"""Parser especializado para layouts PrintCenter no formato COBOL Picture."""

import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    from .models import Layout, CampoLayout, TipoCampo
except ImportError:
    from models import Layout, CampoLayout, TipoCampo


def parse_picture(picture: str) -> Tuple[TipoCampo, int, Optional[str]]:
    """Converte COBOL Picture clause para tipo e tamanho.

    Exemplos:
        9(02) -> NUMERO, 2
        X(20) -> TEXTO, 20
        9(12)V99 -> DECIMAL, 14, formato "12.2"
        9(12)V9(02) -> DECIMAL, 14, formato "12.2"
        9(05)V9(04) -> DECIMAL, 9, formato "5.4"
    """
    if not picture or not isinstance(picture, str):
        return TipoCampo.TEXTO, 1, None

    picture = picture.strip()

    # Decimal: 9(N)V9(M) ou 9(N)V99 etc
    match_decimal = re.match(r'9\((\d+)\)V9\((\d+)\)', picture)
    if match_decimal:
        inteiro = int(match_decimal.group(1))
        decimal = int(match_decimal.group(2))
        return TipoCampo.DECIMAL, inteiro + decimal, f"{inteiro}.{decimal}"

    match_decimal2 = re.match(r'9\((\d+)\)V(9+)', picture)
    if match_decimal2:
        inteiro = int(match_decimal2.group(1))
        decimal = len(match_decimal2.group(2))
        return TipoCampo.DECIMAL, inteiro + decimal, f"{inteiro}.{decimal}"

    # Numérico: 9(N)
    match_num = re.match(r'9\((\d+)\)', picture)
    if match_num:
        return TipoCampo.NUMERO, int(match_num.group(1)), None

    # Alfanumérico: X(N)
    match_alpha = re.match(r'X\((\d+)\)', picture)
    if match_alpha:
        return TipoCampo.TEXTO, int(match_alpha.group(1)), None

    # Fallback
    return TipoCampo.TEXTO, 1, None


def parse_printcenter_layout(excel_path: str, sheet_name=0) -> Layout:
    """Lê layout PrintCenter do Excel e converte para Layout padrão.

    O layout tem colunas: Campo, Posicao De, Posicao Ate, Picture, Conteudo
    O campo tem formato TT.NN onde TT é o tipo de registro.
    """
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de layout não encontrado: {excel_path}")

    # Ler Excel - tentar encontrar a linha de cabeçalho
    df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    # Procurar linha com "Campo" e "Posicao/Posição De"
    def _normalize(s):
        return s.strip().lower().replace('ã', 'a').replace('á', 'a').replace('ç', 'c').replace('é', 'e').replace('ú', 'u').replace('ó', 'o')

    header_row = None
    for idx, row in df_raw.iterrows():
        row_values = [_normalize(str(v)) for v in row.values if pd.notna(v)]
        if 'campo' in row_values and any('posic' in v for v in row_values):
            header_row = idx
            break

    if header_row is None:
        raise ValueError("Não foi possível encontrar cabeçalho do layout (esperado: Campo, Posicao De, Posicao Ate, Picture, Conteudo)")

    # Reler com cabeçalho correto
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row)

    # Normalizar nomes das colunas (aceita com/sem acento)
    col_map = {}
    for col in df.columns:
        col_lower = str(col).strip().lower()
        # Normalizar removendo acentos comuns
        col_norm = col_lower.replace('ã', 'a').replace('á', 'a').replace('ç', 'c').replace('é', 'e').replace('ú', 'u')
        if col_norm == 'campo':
            col_map[col] = 'Campo'
        elif 'posic' in col_norm and 'de' in col_norm:
            col_map[col] = 'Posicao_De'
        elif 'posic' in col_norm and 'ate' in col_norm:
            col_map[col] = 'Posicao_Ate'
        elif col_norm == 'picture':
            col_map[col] = 'Picture'
        elif 'conteudo' in col_norm or 'descri' in col_norm:
            col_map[col] = 'Conteudo'

    df = df.rename(columns=col_map)

    required = ['Campo', 'Posicao_De', 'Posicao_Ate', 'Picture']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória não encontrada: {col}. Colunas disponíveis: {list(df.columns)}")

    # Filtrar linhas válidas (Campo deve ter formato TT.NN)
    campos_layout = []
    campo_pattern = re.compile(r'^(\d{2})\.(\d{2,3})$')

    for _, row in df.iterrows():
        campo_val = str(row['Campo']).strip() if pd.notna(row['Campo']) else ''
        match = campo_pattern.match(campo_val)
        if not match:
            continue  # Pular linhas de título/separador

        tipo_registro = match.group(1)
        seq = match.group(2)

        # Obter posições
        try:
            pos_de = int(float(row['Posicao_De']))
            pos_ate = int(float(row['Posicao_Ate']))
        except (ValueError, TypeError):
            continue

        if pos_de <= 0 or pos_ate <= 0 or pos_ate < pos_de:
            continue

        tamanho = pos_ate - pos_de + 1

        # Obter tipo do Picture
        picture = str(row['Picture']).strip() if pd.notna(row['Picture']) else 'X(1)'
        tipo_campo, _, formato = parse_picture(picture)

        # Nome do campo: NFCOM{tipo}-{conteudo} para compatibilidade com comparador
        conteudo = str(row.get('Conteudo', '')).strip() if pd.notna(row.get('Conteudo', '')) else f'Campo_{seq}'
        # Limpar conteúdo para usar como nome (pegar só a primeira parte)
        nome_limpo = conteudo.split('\n')[0].split('(')[0].strip()
        if len(nome_limpo) > 60:
            nome_limpo = nome_limpo[:60]

        nome_campo = f"NFCOM{tipo_registro}-{nome_limpo}"

        campo = CampoLayout(
            nome=nome_campo,
            posicao_inicio=pos_de,
            tamanho=tamanho,
            tipo=tipo_campo,
            obrigatorio=False,  # Layout PrintCenter não tem coluna obrigatório
            formato=formato,
            posicao_fim=pos_ate
        )
        campos_layout.append(campo)

    if not campos_layout:
        raise ValueError("Nenhum campo válido encontrado no layout PrintCenter")

    # Tamanho da linha = maior posicao_ate
    tamanho_linha = max(c.posicao_fim for c in campos_layout)

    return Layout(
        nome=path.stem,
        campos=campos_layout,
        tamanho_linha=tamanho_linha
    )
