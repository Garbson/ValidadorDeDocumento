from typing import List, Generator, Tuple, Optional, Dict
from pathlib import Path

try:
    from .models import (
        Layout, DiferencaEstruturalCampo, DiferencaEstruturalLinha,
        ResultadoComparacaoEstrutural, TipoCampo
    )
except ImportError:
    from models import (
        Layout, DiferencaEstruturalCampo, DiferencaEstruturalLinha,
        ResultadoComparacaoEstrutural, TipoCampo
    )


class ComparadorEstruturalArquivos:
    """Comparador estrutural que analisa diferenças entre arquivo base e arquivo a ser validado"""

    def __init__(self, layout: Layout):
        self.layout = layout

    def extrair_campos_linha(self, linha: str) -> Dict[str, str]:
        """Extrai os campos de uma linha baseado no layout"""
        campos_extraidos = {}

        for campo in self.layout.campos:
            # Ajustar índices (layout usa 1-indexed, Python usa 0-indexed)
            inicio = campo.posicao_inicio - 1
            fim = campo.posicao_fim

            # Extrair valor (cuidando com linhas muito curtas)
            if inicio < len(linha):
                valor = linha[inicio:fim] if fim <= len(linha) else linha[inicio:]
            else:
                valor = ''

            campos_extraidos[campo.nome] = valor

        return campos_extraidos

    def detectar_tipo_registro(self, linha: str) -> str:
        """Detecta o tipo de registro baseado nos primeiros caracteres da linha"""
        if not linha:
            return "LINHA_VAZIA"

        # Verificar se existe um campo específico para tipo de registro
        for campo in self.layout.campos:
            if 'tipo' in campo.nome.lower() or 'registro' in campo.nome.lower():
                inicio = campo.posicao_inicio - 1
                fim = campo.posicao_fim
                tipo_valor = linha[inicio:fim] if fim <= len(linha) else linha[inicio:]
                return f"TIPO_{tipo_valor.strip()}"

        # Fallback: usar os primeiros 2-3 caracteres
        return f"TIPO_{linha[:3].strip()}"

    def comparar_campos_linha(self, linha_base: str, linha_validado: str, numero_linha: int) -> List[DiferencaEstruturalCampo]:
        """Compara os campos de duas linhas e retorna as diferenças encontradas"""
        diferencas = []

        campos_base = self.extrair_campos_linha(linha_base)
        campos_validado = self.extrair_campos_linha(linha_validado)

        for campo in self.layout.campos:
            valor_base = campos_base.get(campo.nome, '')
            valor_validado = campos_validado.get(campo.nome, '')

            # Verificar se os valores são diferentes
            if valor_base != valor_validado:
                tipo_diferenca, descricao = self._analisar_tipo_diferenca(
                    campo, valor_base, valor_validado
                )

                diferenca = DiferencaEstruturalCampo(
                    nome_campo=campo.nome,
                    posicao_inicio=campo.posicao_inicio,
                    posicao_fim=campo.posicao_fim,
                    valor_base=valor_base,
                    valor_validado=valor_validado,
                    tipo_diferenca=tipo_diferenca,
                    descricao=descricao
                )
                diferencas.append(diferenca)

        return diferencas

    def _analisar_tipo_diferenca(self, campo, valor_base: str, valor_validado: str) -> Tuple[str, str]:
        """Analisa o tipo de diferença entre dois valores de campo"""

        # Verificar campo vazio que deveria ter conteúdo
        if valor_base.strip() and not valor_validado.strip():
            return "CAMPO_VAZIO", f"Campo '{campo.nome}' está vazio no arquivo validado mas contém '{valor_base.strip()}' no arquivo base"

        # Verificar campo com conteúdo que deveria estar vazio
        if not valor_base.strip() and valor_validado.strip():
            return "CAMPO_EXTRA", f"Campo '{campo.nome}' contém '{valor_validado.strip()}' no arquivo validado mas está vazio no arquivo base"

        # Verificar diferença de tamanho
        if len(valor_base) != len(valor_validado):
            return "TAMANHO", f"Campo '{campo.nome}' tem tamanho diferente: base={len(valor_base)} chars, validado={len(valor_validado)} chars"

        # Verificar formato baseado no tipo do campo
        if campo.tipo == TipoCampo.NUMERO:
            if valor_base.isdigit() != valor_validado.isdigit():
                return "FORMATO", f"Campo '{campo.nome}' tem formato numérico diferente: base='{valor_base}', validado='{valor_validado}'"

        elif campo.tipo == TipoCampo.DATA:
            if self._validar_formato_data(valor_base, campo.formato) != self._validar_formato_data(valor_validado, campo.formato):
                return "FORMATO", f"Campo '{campo.nome}' tem formato de data diferente: base='{valor_base}', validado='{valor_validado}'"

        # Diferença de conteúdo geral
        return "CONTEUDO", f"Campo '{campo.nome}' tem conteúdo diferente: base='{valor_base}', validado='{valor_validado}'"

    def _validar_formato_data(self, valor: str, formato: Optional[str]) -> bool:
        """Valida se o valor está em formato de data válido"""
        if not valor.strip():
            return True  # Campo vazio é considerado válido

        # Verificar se contém apenas dígitos (formato básico YYYYMMDD)
        valor_limpo = valor.strip()
        if formato and 'YYYYMMDD' in formato:
            return len(valor_limpo) == 8 and valor_limpo.isdigit()

        return valor_limpo.isdigit()

    def gerar_representacao_visual(self, linha_base: str, linha_validado: str, diferencas: List[DiferencaEstruturalCampo]) -> str:
        """Gera representação visual das diferenças usando separador |"""

        representacao = []
        representacao.append("=" * 80)
        representacao.append("COMPARAÇÃO ESTRUTURAL CAMPO POR CAMPO")
        representacao.append("=" * 80)

        # Cabeçalho
        representacao.append("ARQUIVO BASE:          " + linha_base)
        representacao.append("ARQUIVO A SER VALIDADO: " + linha_validado)
        representacao.append("-" * 80)

        # Separação por campos usando |
        campos_base = self.extrair_campos_linha(linha_base)
        campos_validado = self.extrair_campos_linha(linha_validado)

        linha_base_separada = []
        linha_validado_separada = []
        status_campos = []

        for campo in self.layout.campos:
            valor_base = campos_base.get(campo.nome, '')
            valor_validado = campos_validado.get(campo.nome, '')

            # Determinar status do campo
            diferenca_encontrada = None
            for diff in diferencas:
                if diff.nome_campo == campo.nome:
                    diferenca_encontrada = diff
                    break

            if diferenca_encontrada:
                status = "❌"
                linha_base_separada.append(f"{valor_base}")
                linha_validado_separada.append(f"{valor_validado}")
                status_campos.append(f"{status} {campo.nome}")
            else:
                status = "✅"
                linha_base_separada.append(f"{valor_base}")
                linha_validado_separada.append(f"{valor_validado}")
                status_campos.append(f"{status} {campo.nome}")

        # Mostrar separação visual
        representacao.append("CAMPOS SEPARADOS POR |:")
        representacao.append("BASE:      " + " | ".join(linha_base_separada))
        representacao.append("VALIDADO:  " + " | ".join(linha_validado_separada))
        representacao.append("")

        # Status dos campos
        representacao.append("STATUS DOS CAMPOS:")
        for status in status_campos:
            representacao.append(f"  {status}")

        # Detalhes das diferenças
        if diferencas:
            representacao.append("")
            representacao.append("DIFERENÇAS ENCONTRADAS:")
            for i, diff in enumerate(diferencas, 1):
                representacao.append(f"  {i}. {diff.descricao}")

        representacao.append("=" * 80)

        return "\n".join(representacao)

    def comparar_arquivos_generator(self, caminho_base: str, caminho_validado: str) -> Generator[DiferencaEstruturalLinha, None, None]:
        """Generator que compara arquivos linha por linha"""

        if not Path(caminho_base).exists():
            raise FileNotFoundError(f"Arquivo base não encontrado: {caminho_base}")

        if not Path(caminho_validado).exists():
            raise FileNotFoundError(f"Arquivo a ser validado não encontrado: {caminho_validado}")

        try:
            with open(caminho_base, 'r', encoding='utf-8') as arquivo_base, \
                 open(caminho_validado, 'r', encoding='utf-8') as arquivo_validado:

                for numero_linha, (linha_base, linha_validado) in enumerate(zip(arquivo_base, arquivo_validado), 1):
                    # Remover quebras de linha
                    linha_base = linha_base.rstrip('\n\r')
                    linha_validado = linha_validado.rstrip('\n\r')

                    # Padding para completar tamanho esperado
                    if len(linha_base) < self.layout.tamanho_linha:
                        linha_base = linha_base.ljust(self.layout.tamanho_linha)

                    if len(linha_validado) < self.layout.tamanho_linha:
                        linha_validado = linha_validado.ljust(self.layout.tamanho_linha)

                    # Detectar tipo de registro
                    tipo_registro = self.detectar_tipo_registro(linha_base)

                    # Comparar campos da linha
                    diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha)

                    # Criar resultado da linha
                    diferenca_linha = DiferencaEstruturalLinha(
                        numero_linha=numero_linha,
                        tipo_registro=tipo_registro,
                        arquivo_base_linha=linha_base,
                        arquivo_validado_linha=linha_validado,
                        diferencas_campos=diferencas_campos,
                        total_diferencas=len(diferencas_campos)
                    )

                    yield diferenca_linha

        except UnicodeDecodeError:
            # Tentar com encoding latin-1
            try:
                with open(caminho_base, 'r', encoding='latin-1') as arquivo_base, \
                     open(caminho_validado, 'r', encoding='latin-1') as arquivo_validado:

                    for numero_linha, (linha_base, linha_validado) in enumerate(zip(arquivo_base, arquivo_validado), 1):
                        linha_base = linha_base.rstrip('\n\r')
                        linha_validado = linha_validado.rstrip('\n\r')

                        if len(linha_base) < self.layout.tamanho_linha:
                            linha_base = linha_base.ljust(self.layout.tamanho_linha)

                        if len(linha_validado) < self.layout.tamanho_linha:
                            linha_validado = linha_validado.ljust(self.layout.tamanho_linha)

                        tipo_registro = self.detectar_tipo_registro(linha_base)
                        diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha)

                        diferenca_linha = DiferencaEstruturalLinha(
                            numero_linha=numero_linha,
                            tipo_registro=tipo_registro,
                            arquivo_base_linha=linha_base,
                            arquivo_validado_linha=linha_validado,
                            diferencas_campos=diferencas_campos,
                            total_diferencas=len(diferencas_campos)
                        )

                        yield diferenca_linha

            except Exception as e:
                raise ValueError(f"Erro ao ler arquivos: {str(e)}")

    def comparar_arquivos(self, caminho_base: str, caminho_validado: str) -> ResultadoComparacaoEstrutural:
        """Compara dois arquivos estruturalmente e retorna resultado completo"""

        total_linhas = 0
        linhas_com_diferencas = 0
        todas_diferencas = []

        for diferenca_linha in self.comparar_arquivos_generator(caminho_base, caminho_validado):
            total_linhas += 1

            if diferenca_linha.total_diferencas > 0:
                linhas_com_diferencas += 1
                todas_diferencas.append(diferenca_linha)

        linhas_identicas = total_linhas - linhas_com_diferencas

        return ResultadoComparacaoEstrutural(
            total_linhas_comparadas=total_linhas,
            linhas_com_diferencas=linhas_com_diferencas,
            linhas_identicas=linhas_identicas,
            diferencas_por_linha=todas_diferencas,
            taxa_identidade=0.0  # Será calculado no __post_init__
        )

    def gerar_relatorio_completo(self, resultado: ResultadoComparacaoEstrutural) -> str:
        """Gera relatório completo da comparação estrutural"""

        relatorio = []
        relatorio.append("🔍 RELATÓRIO DE COMPARAÇÃO ESTRUTURAL DE ARQUIVOS")
        relatorio.append("=" * 80)
        relatorio.append("")

        # Estatísticas gerais
        relatorio.append(f"📊 ESTATÍSTICAS GERAIS:")
        relatorio.append(f"   Total de linhas comparadas: {resultado.total_linhas_comparadas}")
        relatorio.append(f"   Linhas idênticas: {resultado.linhas_identicas}")
        relatorio.append(f"   Linhas com diferenças: {resultado.linhas_com_diferencas}")
        relatorio.append(f"   Taxa de identidade: {resultado.taxa_identidade:.2f}%")
        relatorio.append("")

        if resultado.linhas_com_diferencas == 0:
            relatorio.append("✅ ARQUIVOS ESTRUTURALMENTE IDÊNTICOS!")
            relatorio.append("   Todos os campos coincidem perfeitamente.")
        else:
            relatorio.append(f"❌ ENCONTRADAS {resultado.linhas_com_diferencas} LINHAS COM DIFERENÇAS:")
            relatorio.append("")

            for diferenca_linha in resultado.diferencas_por_linha[:10]:  # Limitar a 10 linhas para não ficar muito longo
                relatorio.append(f"📍 LINHA {diferenca_linha.numero_linha} - {diferenca_linha.tipo_registro}")
                relatorio.append(f"   Total de diferenças: {diferenca_linha.total_diferencas}")

                # Mostrar representação visual
                representacao_visual = self.gerar_representacao_visual(
                    diferenca_linha.arquivo_base_linha,
                    diferenca_linha.arquivo_validado_linha,
                    diferenca_linha.diferencas_campos
                )
                relatorio.append(representacao_visual)
                relatorio.append("")

            if len(resultado.diferencas_por_linha) > 10:
                relatorio.append(f"... e mais {len(resultado.diferencas_por_linha) - 10} linhas com diferenças.")

        return "\n".join(relatorio)