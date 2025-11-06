import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from .models import Layout, CampoLayout, TipoCampo
except ImportError:
    from models import Layout, CampoLayout, TipoCampo


class LayoutParser:
    """Parser para arquivos Excel de layout"""

    def __init__(self):
        self.colunas_obrigatorias = [
            'Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio'
        ]
        self.tipos_validos = {tipo.value for tipo in TipoCampo}

    def validar_excel(self, df: pd.DataFrame) -> List[str]:
        """Valida se o Excel tem a estrutura correta"""
        erros = []

        # Verificar colunas obrigatórias
        colunas_faltantes = set(self.colunas_obrigatorias) - set(df.columns)
        if colunas_faltantes:
            erros.append(f"Colunas obrigatórias faltantes: {', '.join(colunas_faltantes)}")

        # Verificar se há dados
        if df.empty:
            erros.append("Arquivo Excel está vazio")

        return erros

    def validar_linha_layout(self, linha: pd.Series, numero_linha: int) -> List[str]:
        """Valida uma linha específica do layout"""
        erros = []

        # Campo obrigatório
        if pd.isna(linha.get('Campo')) or str(linha.get('Campo')).strip() == '':
            erros.append(f"Linha {numero_linha}: Campo 'Campo' é obrigatório")

        # Posição início deve ser número positivo
        try:
            pos_inicio = int(linha.get('Posicao_Inicio', 0))
            if pos_inicio <= 0:
                erros.append(f"Linha {numero_linha}: Posicao_Inicio deve ser maior que 0")
        except (ValueError, TypeError):
            erros.append(f"Linha {numero_linha}: Posicao_Inicio deve ser um número")

        # Tamanho deve ser número positivo
        try:
            tamanho = int(linha.get('Tamanho', 0))
            if tamanho <= 0:
                erros.append(f"Linha {numero_linha}: Tamanho deve ser maior que 0")
        except (ValueError, TypeError):
            erros.append(f"Linha {numero_linha}: Tamanho deve ser um número")

        # Tipo deve ser válido
        tipo = str(linha.get('Tipo', '')).upper().strip()
        if tipo not in self.tipos_validos:
            erros.append(f"Linha {numero_linha}: Tipo '{tipo}' inválido. Use: {', '.join(self.tipos_validos)}")

        # Obrigatório deve ser S ou N
        obrigatorio = str(linha.get('Obrigatorio', '')).upper().strip()
        if obrigatorio not in ['S', 'N']:
            erros.append(f"Linha {numero_linha}: Obrigatorio deve ser 'S' ou 'N'")

        return erros

    def parse_excel(self, caminho_excel: str, sheet_name: Optional[int] = None) -> Layout:
        """Converte Excel para objeto Layout

        Args:
            caminho_excel: Caminho para o arquivo Excel
            sheet_name: Índice da aba (None = primeira aba, 0 = primeira, 1 = segunda, etc.)
        """
        if not Path(caminho_excel).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_excel}")

        try:
            # Importar função de detecção de cabeçalho
            try:
                from .layout_normalizer import find_header_row
            except ImportError:
                from layout_normalizer import find_header_row

            # Ler Excel com seleção de aba e detecção automática de cabeçalho
            sheet_index = sheet_name if sheet_name is not None else 0

            # Detectar linha de cabeçalho
            header_row = find_header_row(caminho_excel, sheet_index)

            # Ler Excel usando a linha de cabeçalho detectada
            df = pd.read_excel(caminho_excel, sheet_name=sheet_index, header=header_row)

            # Filtrar linhas de títulos de seção (como "01 - Identificação da NFCom")
            if not df.empty:
                first_col = df.iloc[:, 0].astype(str)
                section_titles_mask = first_col.str.match(r'^\d+\s*-\s*', na=False)

                if section_titles_mask.any():
                    df = df[~section_titles_mask]
                    df = df.reset_index(drop=True)

            # Validar estrutura
            erros_estrutura = self.validar_excel(df)
            if erros_estrutura:
                raise ValueError("Erros na estrutura do Excel:\n" + "\n".join(erros_estrutura))

            # Validar cada linha
            erros_linhas = []
            for idx, linha in df.iterrows():
                erros_linha = self.validar_linha_layout(linha, idx + 2)  # +2 porque Excel começa linha 1 e tem header
                erros_linhas.extend(erros_linha)

            if erros_linhas:
                raise ValueError("Erros nas linhas do layout:\n" + "\n".join(erros_linhas))

            # Converter para objetos CampoLayout
            campos = []
            for _, linha in df.iterrows():
                campo = CampoLayout(
                    nome=str(linha['Campo']).strip(),
                    posicao_inicio=int(linha['Posicao_Inicio']),
                    tamanho=int(linha['Tamanho']),
                    tipo=TipoCampo(str(linha['Tipo']).upper().strip()),
                    obrigatorio=str(linha['Obrigatorio']).upper().strip() == 'S',
                    formato=str(linha.get('Formato', '')).strip() if pd.notna(linha.get('Formato')) else None
                )
                campos.append(campo)

            # Validar sobreposições de campos
            self._validar_sobreposicoes(campos)

            # Calcular tamanho total da linha
            tamanho_linha = max(campo.posicao_fim for campo in campos) if campos else 0

            nome_layout = Path(caminho_excel).stem
            return Layout(nome=nome_layout, campos=campos, tamanho_linha=tamanho_linha)

        except Exception as e:
            raise ValueError(f"Erro ao processar Excel: {str(e)}")

    def parse_dataframe(self, df: pd.DataFrame, nome_layout: str = "Layout") -> Layout:
        """Converte um DataFrame já carregado (com colunas canônicas) em um objeto Layout.

        Espera as colunas: 'Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio' e opcional 'Formato'.
        """
        try:
            # Validar estrutura básica
            erros_estrutura = self.validar_excel(df)
            if erros_estrutura:
                raise ValueError("Erros na estrutura do DataFrame:\n" + "\n".join(erros_estrutura))

            # Validar cada linha
            erros_linhas = []
            for idx, linha in df.iterrows():
                erros_linha = self.validar_linha_layout(linha, idx + 2)
                erros_linhas.extend(erros_linha)

            if erros_linhas:
                raise ValueError("Erros nas linhas do layout:\n" + "\n".join(erros_linhas))

            # Converter linhas em CampoLayout
            campos: List[CampoLayout] = []
            for _, row in df.iterrows():
                nome = str(row['Campo']).strip()
                pos_ini = int(row['Posicao_Inicio'])
                tam = int(row['Tamanho'])
                tipo_str = str(row['Tipo']).upper().strip()

                # Garantir que o tipo é um TipoCampo válido
                try:
                    tipo_campo = TipoCampo(tipo_str)
                except ValueError:
                    # Fallback para TEXTO se vier algo não mapeado
                    tipo_campo = TipoCampo.TEXTO

                obrig = str(row['Obrigatorio']).upper().strip() in ['S', 'SIM', 'Y', 'YES', '1', 'TRUE', 'OBRIG', 'OBRIGATORIO']
                formato = str(row.get('Formato', '')).strip() if pd.notna(row.get('Formato', None)) else None

                campos.append(CampoLayout(
                    nome=nome,
                    posicao_inicio=pos_ini,
                    tamanho=tam,
                    tipo=tipo_campo,
                    obrigatorio=obrig,
                    formato=formato
                ))

            # Validar sobreposições e calcular tamanho total
            self._validar_sobreposicoes(campos)
            tamanho_linha = max((c.posicao_fim for c in campos), default=0)

            return Layout(nome=nome_layout, campos=campos, tamanho_linha=tamanho_linha)
        except Exception as e:
            raise ValueError(f"Erro ao processar DataFrame: {str(e)}")

    def _validar_sobreposicoes(self, campos: List[CampoLayout]) -> None:
        """Valida se há sobreposições entre campos

        Para arquivos multiregistro (campos com padrão NFE[XX]-), verifica sobreposições
        apenas dentro do mesmo tipo de registro, pois cada tipo representa linhas separadas.
        """
        import re

        # Detectar se é arquivo multiregistro
        is_multirecord = any(re.match(r'NFE\d+-', campo.nome) for campo in campos)

        if is_multirecord:
            # Para multiregistro: agrupar campos por tipo de registro
            campos_por_tipo = {}
            for campo in campos:
                match = re.match(r'NFE(\d+)-', campo.nome)
                if match:
                    tipo_registro = match.group(1)
                    if tipo_registro not in campos_por_tipo:
                        campos_por_tipo[tipo_registro] = []
                    campos_por_tipo[tipo_registro].append(campo)
                else:
                    # Campos sem padrão NFE[XX]- são tratados como tipo "00" por padrão
                    if "00" not in campos_por_tipo:
                        campos_por_tipo["00"] = []
                    campos_por_tipo["00"].append(campo)

            # Validar sobreposições dentro de cada tipo de registro
            for tipo_registro, campos_do_tipo in campos_por_tipo.items():
                self._validar_sobreposicoes_simples(campos_do_tipo, f"tipo {tipo_registro}")
        else:
            # Para arquivo normal: validar sobreposições globalmente
            self._validar_sobreposicoes_simples(campos)

    def _validar_sobreposicoes_simples(self, campos: List[CampoLayout], contexto: str = "") -> None:
        """Valida sobreposições em uma lista de campos"""
        campos_ordenados = sorted(campos, key=lambda c: c.posicao_inicio)

        for i in range(len(campos_ordenados) - 1):
            campo_atual = campos_ordenados[i]
            campo_proximo = campos_ordenados[i + 1]

            if campo_atual.posicao_fim >= campo_proximo.posicao_inicio:
                contexto_msg = f" ({contexto})" if contexto else ""
                raise ValueError(
                    f"Sobreposição detectada entre campos '{campo_atual.nome}' "
                    f"(posições {campo_atual.posicao_inicio}-{campo_atual.posicao_fim}) e "
                    f"'{campo_proximo.nome}' (posições {campo_proximo.posicao_inicio}-{campo_proximo.posicao_fim}){contexto_msg}"
                )