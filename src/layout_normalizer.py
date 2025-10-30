import unicodedata
import difflib
import json
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd

CANONICAL_COLUMNS = [
    'Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio', 'Formato'
]

SYNONYMS = {
    'Campo': [
        'campo','nome_campo','nome','field','coluna','campo_nome','CAMPO','campo_mobile',
        'atributo','atributo_fct','nome_campo_netsms','campo_netsms','descricao_atributo'
    ],
    'Posicao_Inicio': [
        'posicao_inicio','inicio','start','pos_ini','posicao','inicio_pos','start_pos',
        'coluna_inicio','inicio_coluna','indice','index','idx'
    ],
    'Tamanho': [
        'tamanho','tam','length','len','qtd_caracteres','caracteres','tamanho_campo','TAMANHO',
        'tam_campo'
    ],
    'Tipo': [
        'tipo','type','categoria','formato_tipo','tipo_campo','TIPO'
    ],
    'Obrigatorio': [
        'obrigatorio','obrig','required','req','mandatory','obg','necessario','OBRIGATORIO','preench','preenchimento',
        'facult','facultativo','opcional'
    ],
    'Formato': [
        'formato','pattern','mascara','mask','regex','dominio'
    ]
}

TIPO_NORMALIZATION = {
    'TXT': 'TEXTO', 'TEXT': 'TEXTO', 'STRING': 'TEXTO', 'CHAR': 'TEXTO',
    'VARCHAR': 'TEXTO', 'VARCHAR2': 'TEXTO', 'NVARCHAR': 'TEXTO',
    'NUM': 'NUMERO', 'INT': 'NUMERO', 'INTEGER': 'NUMERO', 'NUMBER': 'NUMERO',
    'BIGINT': 'NUMERO', 'SMALLINT': 'NUMERO',
    'DEC': 'DECIMAL', 'FLOAT': 'DECIMAL', 'DOUBLE': 'DECIMAL', 'VALOR': 'DECIMAL',
    'REAL': 'DECIMAL', 'NUMERIC': 'DECIMAL',
    'DATE': 'DATA', 'DATETIME': 'DATA', 'TIMESTAMP': 'DATA', 'DT': 'DATA'
}

OBRIGATORIO_TRUE = {'S', 'SIM', 'Y', 'YES', '1', 'TRUE', 'OBRIG', 'OBRIGATORIO'}
OBRIGATORIO_FALSE = {'N', 'NAO', 'NA', 'NO', '0', 'FALSE', 'FACULT', 'FACULTATIVO'}


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    for ch in [' ', '.', '/', '-', '\\']:
        s = s.replace(ch, '_')
    return s


def suggest_mapping(headers: List[str]) -> Dict[str, Optional[str]]:
    """Sugere mapeamento de cabeçalhos para colunas canônicas"""
    normalized = {h: _norm(h) for h in headers}
    mapping: Dict[str, Optional[str]] = {c: None for c in CANONICAL_COLUMNS}

    # Passo 1: sinônimos diretos - priorizar cabeçalhos mais específicos
    for canon in CANONICAL_COLUMNS:
        syns = {_norm(x) for x in SYNONYMS.get(canon, [])} | {_norm(canon)}

        # Priorizar correspondências exatas primeiro
        for orig, normed in normalized.items():
            if normed == _norm(canon) and mapping[canon] is None:
                mapping[canon] = orig
                break

        # Se não encontrou exato, usar sinônimos
        if mapping[canon] is None:
            for orig, normed in normalized.items():
                if normed in syns and mapping[canon] is None:
                    mapping[canon] = orig
                    break

    # Heurística adicional: se não existir Campo mas existir algo com 'campo' dentro
    if mapping['Campo'] is None:
        for orig in headers:
            normed = _norm(orig)
            if 'campo' in normed and not any(x in normed for x in ['obrig','tamanho','tipo']):
                mapping['Campo'] = orig
                break

    # Heurística: Tamanho pode vir como TAM puro
    if mapping['Tamanho'] is None:
        for orig in headers:
            if _norm(orig) in {'tam'}:
                mapping['Tamanho'] = orig
                break

    # Heurística: Obrigatorio pode vir como PREENCH / PREENCHIMENTO
    if mapping['Obrigatorio'] is None:
        for orig in headers:
            if _norm(orig) in {'preench','preenchimento'}:
                mapping['Obrigatorio'] = orig
                break

    # Passo 2: fuzzy para não mapeados
    for canon in CANONICAL_COLUMNS:
        if mapping[canon] is None:
            candidates = []
            for orig, normed in normalized.items():
                score = difflib.SequenceMatcher(None, normed, _norm(canon)).ratio()
                if score >= 0.75:
                    candidates.append((score, orig))
            if candidates:
                candidates.sort(reverse=True)
                mapping[canon] = candidates[0][1]

    return mapping


def headers_signature(headers: List[str]) -> str:
    """Gera assinatura estável dos cabeçalhos (normalizados e ordenados)."""
    normed = sorted(_norm(h) for h in headers)
    digest = hashlib.sha256(('|'.join(normed)).encode('utf-8')).hexdigest()[:16]
    return digest


_CACHE_PATH = Path('data/layout_mappings.json')


def _load_cache() -> Dict[str, Any]:
    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: Dict[str, Any]):
    _CACHE_PATH.parent.mkdir(exist_ok=True, parents=True)
    with open(_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_cached_mapping(signature: str) -> Optional[Dict[str, Any]]:
    cache = _load_cache()
    return cache.get(signature)


def save_cached_mapping(signature: str, mapping: Dict[str, Any]):
    cache = _load_cache()
    cache[signature] = mapping
    _save_cache(cache)


def analyze_mapping(mapping: Dict[str, Optional[str]]) -> Dict[str, Any]:
    missing = [k for k, v in mapping.items() if v is None and k in ['Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio']]
    optional_missing = [k for k, v in mapping.items() if v is None and k not in missing]
    completeness = 1 - (len(missing) / 5)
    return {
        'missing_required': missing,
        'missing_optional': optional_missing,
        'completeness': completeness
    }


def normalize_dataframe(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> Tuple[pd.DataFrame, List[str]]:
    """Produz dataframe com colunas canônicas a partir do mapeamento.
    Retorna df_normalizado, warnings"""
    warnings = []
    data: Dict[str, Any] = {}

    # Determinar o índice baseado no DataFrame original
    index = df.index if not df.empty else range(0)

    for canon in CANONICAL_COLUMNS:
        orig = mapping.get(canon)
        if orig and orig in df.columns:
            data[canon] = df[orig]
        else:
            # Criar uma série com valores None do mesmo tamanho que o DataFrame original
            data[canon] = pd.Series([None] * len(df), index=index)
            if canon in ['Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio']:
                warnings.append(f'Coluna obrigatória ausente: {canon}')

    norm_df = pd.DataFrame(data, index=index)

    # Limpeza e normalização de tipos
    if 'Obrigatorio' in norm_df:
        norm_df['Obrigatorio'] = norm_df['Obrigatorio'].astype(str).str.upper().str.strip().apply(
            lambda x: 'S' if x in OBRIGATORIO_TRUE else ('N' if x in OBRIGATORIO_FALSE else 'N')
        )

    if 'Tipo' in norm_df:
        def normalizar_tipo(x):
            x_upper = str(x).upper().strip()
            # Primeiro tenta normalização direta
            normalized = TIPO_NORMALIZATION.get(x_upper, None)
            if normalized:
                return normalized
            # Se não encontrou, verifica se é um dos tipos válidos
            if x_upper in ['TEXTO', 'NUMERO', 'DATA', 'DECIMAL']:
                return x_upper
            # Fallback para TEXTO para tipos desconhecidos
            return 'TEXTO'
        
        norm_df['Tipo'] = norm_df['Tipo'].apply(normalizar_tipo)

    # Converter numéricos
    for col in ['Posicao_Inicio', 'Tamanho']:
        if col in norm_df:
            norm_df[col] = pd.to_numeric(norm_df[col], errors='coerce')

    # Se não houver Posicao_Inicio válido mas houver Tamanho, gerar cumulativo
    if 'Posicao_Inicio' in norm_df and 'Tamanho' in norm_df:
        if norm_df['Posicao_Inicio'].isna().all() or (norm_df['Posicao_Inicio'] <= 0).all():
            # Detectar se é arquivo multiregistro (campos com NFE[XX]-)
            is_multirecord = False
            if 'Campo' in norm_df:
                multirecord_pattern = norm_df['Campo'].astype(str).str.contains(r'NFE\d+-', na=False)
                is_multirecord = multirecord_pattern.any()

            if is_multirecord:
                # Para multiregistro: resetar posições por tipo de registro
                posicoes = []
                tipos_processados = {}

                for idx, row in norm_df.iterrows():
                    campo_nome = str(row.get('Campo', ''))
                    try:
                        tam = int(row['Tamanho']) if pd.notna(row['Tamanho']) else None
                    except (ValueError, TypeError):
                        tam = None

                    if tam is None or tam <= 0:
                        posicoes.append(None)
                        continue

                    # Extrair tipo de registro (ex: NFE01- -> tipo 01)
                    import re
                    match = re.match(r'NFE(\d+)-', campo_nome)
                    if match:
                        tipo_registro = match.group(1)

                        # Se é o primeiro campo deste tipo, resetar posição para 1
                        if tipo_registro not in tipos_processados:
                            tipos_processados[tipo_registro] = 1

                        posicoes.append(tipos_processados[tipo_registro])
                        tipos_processados[tipo_registro] += tam
                    else:
                        # Campo sem padrão NFE[XX]-, usar posição sequencial global
                        posicoes.append(1)

                warnings.append('Posicao_Inicio gerada para arquivo multiregistro (posições resetadas por tipo).')
            else:
                # Para arquivo normal: usar cumulativo simples
                start = 1
                posicoes = []
                for tam in norm_df['Tamanho']:
                    try:
                        t = int(tam) if pd.notna(tam) else None
                    except (ValueError, TypeError):
                        t = None
                    if t is None or t <= 0:
                        posicoes.append(None)
                    else:
                        posicoes.append(start)
                        start += t

                warnings.append('Posicao_Inicio gerada automaticamente pelo cumulativo de Tamanho.')

            # Criar Series com o mesmo índice do DataFrame
            norm_df['Posicao_Inicio'] = pd.Series(posicoes, index=norm_df.index)

    # Remover linhas vazias
    if 'Campo' in norm_df:
        norm_df = norm_df[~norm_df['Campo'].astype(str).str.strip().eq('')]

    norm_df = norm_df.reset_index(drop=True)
    return norm_df, warnings


@dataclass
class LayoutMappingResult:
    mapping: Dict[str, Optional[str]]
    analysis: Dict[str, Any]
    sample: List[Dict[str, Any]]  # primeiras linhas normalizadas
    warnings: List[str]
    original_samples: Dict[str, List[str]]  # amostras por coluna original
    normalized_rows: List[Dict[str, Any]]  # todas as linhas normalizadas (layout base)


@dataclass
class ExcelSheetsResult:
    sheets: List[str]  # nomes das abas
    default_sheet: int  # índice da aba padrão (0)


def find_header_row(temp_path: str, sheet_name: int = 0) -> int:
    """Encontra a linha que contém os cabeçalhos reais (procura por 'Campo', 'Tipo', etc.)"""
    import pandas as pd

    # Palavras-chave que indicam uma linha de cabeçalho válida
    header_keywords = ['campo', 'tipo', 'tamanho', 'tam', 'posicao', 'inicio', 'obrigatorio', 'preenc', 'facult', 'obrig']

    try:
        # Ler as primeiras 10 linhas para analisar
        df_preview = pd.read_excel(temp_path, sheet_name=sheet_name, nrows=10, header=None)

        for row_idx in range(len(df_preview)):
            row_values = df_preview.iloc[row_idx].astype(str).str.lower().str.strip()

            # Contar quantas palavras-chave encontramos nesta linha
            keyword_count = sum(1 for val in row_values if any(keyword in str(val) for keyword in header_keywords))

            # Se encontramos pelo menos 3 palavras-chave, provavelmente é uma linha de cabeçalho
            if keyword_count >= 3:
                return row_idx

        # Se não encontrou, usar linha 0 como fallback
        return 0

    except Exception as e:
        print(f"Erro ao detectar linha de cabeçalho: {e}")
        return 0


def list_excel_sheets(temp_path: str) -> ExcelSheetsResult:
    """Lista todas as abas de um arquivo Excel"""
    import pandas as pd
    try:
        # Usar ExcelFile para obter todas as abas sem carregar dados
        excel_file = pd.ExcelFile(temp_path)
        sheets = excel_file.sheet_names
        excel_file.close()

        return ExcelSheetsResult(
            sheets=sheets,
            default_sheet=0
        )
    except Exception as e:
        raise ValueError(f"Erro ao ler abas do Excel: {str(e)}")


def suggest_mapping_with_data(headers: List[str], df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Sugere mapeamento analisando também os dados das colunas"""
    mapping = suggest_mapping(headers)

    # Melhorar mapeamento analisando o conteúdo das colunas
    if not df.empty:
        # Para coluna Obrigatorio, procurar coluna que contém 'obrig'/'facult' nos dados
        if mapping['Obrigatorio'] is None or True:  # Sempre verificar para melhorar
            for col in headers:
                try:
                    # Analisar os primeiros valores não nulos da coluna
                    sample_values = df[col].dropna().astype(str).str.lower().str.strip()
                    if len(sample_values) > 0:
                        obrig_count = sum(val in ['obrig', 'obrigatorio'] for val in sample_values)
                        facult_count = sum(val in ['facult', 'facultativo'] for val in sample_values)

                        # Se encontrou valores de obrigatoriedade, usar esta coluna
                        if obrig_count + facult_count > 0:
                            print(f"Detectada coluna de obrigatoriedade: {col} (obrig: {obrig_count}, facult: {facult_count})")
                            mapping['Obrigatorio'] = col
                            break
                except Exception:
                    continue

    return mapping


def map_layout_file(temp_path: str, sheet_name: Optional[int] = None) -> LayoutMappingResult:
    """Mapeia layout de arquivo Excel com suporte a seleção de aba

    Args:
        temp_path: Caminho para o arquivo Excel
        sheet_name: Índice da aba (None = primeira aba, 0 = primeira, 1 = segunda, etc.)
    """
    import pandas as pd

    # Se sheet_name não especificado, usar primeira aba (comportamento original)
    if sheet_name is None:
        sheet_name = 0

    try:
        # Detectar automaticamente a linha de cabeçalho
        header_row = find_header_row(temp_path, sheet_name)
        print(f"Detectada linha de cabeçalho: {header_row}")

        # Ler Excel usando a linha de cabeçalho detectada
        df = pd.read_excel(temp_path, sheet_name=sheet_name, header=header_row)

        # Filtrar apenas linhas que não são títulos de seção
        # (linhas que começam com números seguidos de ' - ' são títulos de seção)
        if not df.empty:
            # Verificar se a primeira coluna contém títulos de seção
            first_col = df.iloc[:, 0].astype(str)
            section_titles_mask = first_col.str.match(r'^\d+\s*-\s*', na=False)

            if section_titles_mask.any():
                # Remover linhas de títulos de seção
                df = df[~section_titles_mask]
                df = df.reset_index(drop=True)

    except Exception as e:
        raise ValueError(f"Erro ao ler aba {sheet_name} do Excel: {str(e)}")

    headers = list(df.columns)
    mapping = suggest_mapping_with_data(headers, df)
    analysis = analyze_mapping(mapping)
    norm_df, warnings = normalize_dataframe(df, mapping)
    sample = norm_df.head(5).fillna('').to_dict(orient='records')

    # Amostras originais: primeiros 3 valores não nulos por coluna
    original_samples: Dict[str, List[str]] = {}
    for col in headers:
        serie = df[col].astype(str).fillna('').tolist()
        original_samples[col] = [v for v in serie if v.strip()][:3]

    normalized_rows = norm_df.fillna('').to_dict(orient='records')
    return LayoutMappingResult(
        mapping=mapping,
        analysis=analysis,
        sample=sample,
        warnings=warnings,
        original_samples=original_samples,
        normalized_rows=normalized_rows
    )
