import pandas as pd
from typing import List, Dict, Any
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

    def parse_excel(self, caminho_excel: str) -> Layout:
        """Converte Excel para objeto Layout"""
        if not Path(caminho_excel).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_excel}")

        try:
            # Ler Excel
            df = pd.read_excel(caminho_excel)

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

    def _validar_sobreposicoes(self, campos: List[CampoLayout]) -> None:
        """Valida se há sobreposições entre campos"""
        campos_ordenados = sorted(campos, key=lambda c: c.posicao_inicio)

        for i in range(len(campos_ordenados) - 1):
            campo_atual = campos_ordenados[i]
            campo_proximo = campos_ordenados[i + 1]

            if campo_atual.posicao_fim >= campo_proximo.posicao_inicio:
                raise ValueError(
                    f"Sobreposição detectada entre campos '{campo_atual.nome}' "
                    f"(posições {campo_atual.posicao_inicio}-{campo_atual.posicao_fim}) e "
                    f"'{campo_proximo.nome}' (posições {campo_proximo.posicao_inicio}-{campo_proximo.posicao_fim})"
                )