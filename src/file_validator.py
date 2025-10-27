from typing import List, Generator, Tuple
from pathlib import Path

try:
    from .models import Layout, ErroValidacao, ResultadoValidacao
    from .validators import ValidadorCampo
except ImportError:
    from models import Layout, ErroValidacao, ResultadoValidacao
    from validators import ValidadorCampo


class ValidadorArquivo:
    """Validador principal para arquivos sequenciais"""

    def __init__(self, layout: Layout):
        self.layout = layout
        self.validador_campo = ValidadorCampo()

    def extrair_campos_linha(self, linha: str) -> dict:
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

    def validar_linha(self, numero_linha: int, linha: str) -> List[ErroValidacao]:
        """Valida uma linha individual"""
        erros = []

        # Verificar se a linha começa com espaços (problema de formatação)
        if linha.startswith(' '):
            erro = ErroValidacao(
                linha=numero_linha,
                campo='FORMATO_LINHA',
                valor_encontrado=f"Linha começa com espaços: [{linha[:20]}...]",
                erro_tipo='FORMATO_LINHA_INVALIDO',
                descricao=f"Linha não deve começar com espaços. Deve começar com tipo de registro ou código do cliente",
                valor_esperado="Linha deve começar com caracteres válidos (números/letras)"
            )
            erros.append(erro)

        # Verificar tamanho mínimo da linha
        tamanho_esperado = self.layout.tamanho_linha
        if len(linha) < tamanho_esperado:
            # Mostrar quebra visual da linha
            linha_formatada = self._formatar_linha_para_debug(linha)
            erro = ErroValidacao(
                linha=numero_linha,
                campo='LINHA_COMPLETA',
                valor_encontrado=f"Tamanho: {len(linha)} chars | Linha: [{linha_formatada}]",
                erro_tipo='TAMANHO_LINHA',
                descricao=f"Linha muito curta. Encontrado: {len(linha)} caracteres, esperado: {tamanho_esperado} caracteres",
                valor_esperado=f"{tamanho_esperado} caracteres"
            )
            erros.append(erro)
            # Continuar validação mesmo com linha curta para mostrar outros problemas

        # Extrair campos
        campos_extraidos = self.extrair_campos_linha(linha)

        # Validar cada campo (limitando para evitar loops infinitos)
        contador_erros = 0
        for campo in self.layout.campos:
            if contador_erros >= 10:  # Limitar erros por linha
                break

            valor = campos_extraidos.get(campo.nome, '')
            erros_campo = self.validador_campo.validar_campo(valor, campo)

            for descricao_erro in erros_campo:
                if contador_erros >= 10:
                    break

                # Determinar tipo de erro
                if 'obrigatório' in descricao_erro.lower():
                    tipo_erro = 'CAMPO_OBRIGATORIO'
                elif 'tamanho' in descricao_erro.lower():
                    tipo_erro = 'TAMANHO_CAMPO'
                elif 'formato' in descricao_erro.lower() or 'deve estar no formato' in descricao_erro.lower():
                    tipo_erro = 'FORMATO_INVALIDO'
                elif 'deve conter apenas' in descricao_erro.lower() or 'deve ser um' in descricao_erro.lower():
                    tipo_erro = 'TIPO_INVALIDO'
                else:
                    tipo_erro = 'ERRO_GENERICO'

                # Criar descrição mais simples para evitar loops
                descricao_detalhada = f"Campo: {campo.nome} | Posição: {campo.posicao_inicio}-{campo.posicao_fim} | {descricao_erro}"

                erro = ErroValidacao(
                    linha=numero_linha,
                    campo=campo.nome,
                    valor_encontrado=f"'{valor}' (pos {campo.posicao_inicio}-{campo.posicao_fim})",
                    erro_tipo=tipo_erro,
                    descricao=descricao_detalhada,
                    valor_esperado=self._obter_valor_esperado(campo, tipo_erro)
                )
                erros.append(erro)
                contador_erros += 1

        return erros

    def _formatar_linha_para_debug(self, linha: str) -> str:
        """Formata linha para debug mostrando caracteres especiais"""
        linha_formatada = linha.replace(' ', '·').replace('\t', '→')
        if len(linha_formatada) > 50:
            return linha_formatada[:47] + "..."
        return linha_formatada

    def _criar_quebra_visual_linha(self, linha: str, campos_extraidos: dict) -> str:
        """Cria representação visual da linha quebrada por campos"""
        try:
            quebra = "\n📍 Quebra da linha por campos:\n"
            for campo in self.layout.campos[:5]:  # Limitar a 5 campos para evitar loops
                valor = campos_extraidos.get(campo.nome, '')
                valor_visual = valor.replace(' ', '·')[:20] if valor else '(vazio)'  # Limitar tamanho
                status = "✅" if valor.strip() else "❌"
                quebra += f"   {status} {campo.nome}: [{valor_visual}]\n"
            if len(self.layout.campos) > 5:
                quebra += f"   ... e mais {len(self.layout.campos) - 5} campos\n"
            return quebra
        except Exception:
            return "\n📍 Erro ao gerar quebra visual\n"

    def _criar_descricao_detalhada(self, campo, valor, erro_original, quebra_visual):
        """Cria descrição mais detalhada do erro"""
        try:
            descricao = f"🔍 CAMPO: {campo.nome}\n"
            descricao += f"📍 POSIÇÃO: {campo.posicao_inicio}-{campo.posicao_fim} (tamanho {campo.tamanho})\n"
            descricao += f"📝 TIPO ESPERADO: {campo.tipo.value}\n"
            descricao += f"❌ PROBLEMA: {erro_original}\n"
            descricao += f"💡 VALOR ENCONTRADO: '{valor}' (length: {len(valor)})\n"

            if campo.obrigatorio:
                descricao += f"⚠️ CAMPO OBRIGATÓRIO\n"

            if campo.formato:
                descricao += f"📋 FORMATO ESPERADO: {campo.formato}\n"

            # Não incluir quebra visual por enquanto para evitar loops
            return descricao
        except Exception:
            return f"Erro no campo {campo.nome}: {erro_original}"

    def _obter_valor_esperado(self, campo, tipo_erro):
        """Obtém descrição do valor esperado baseado no tipo de erro"""
        if tipo_erro == 'CAMPO_OBRIGATORIO':
            return f"Qualquer valor válido do tipo {campo.tipo.value}"
        elif tipo_erro == 'TAMANHO_CAMPO':
            return f"Exatamente {campo.tamanho} caracteres"
        elif tipo_erro == 'TIPO_INVALIDO':
            if campo.tipo.value == 'NUMERO':
                return "Apenas dígitos (0-9)"
            elif campo.tipo.value == 'DATA':
                return f"Data no formato {campo.formato or 'YYYYMMDD'}"
            elif campo.tipo.value == 'DECIMAL':
                return "Apenas dígitos para valor decimal"
            else:
                return f"Valor do tipo {campo.tipo.value}"
        elif tipo_erro == 'FORMATO_INVALIDO':
            return f"Data válida no formato {campo.formato}"
        else:
            return f"Valor válido do tipo {campo.tipo.value}"

    def _reconstruir_registros_sequenciais(self, caminho_arquivo: str, encoding: str = 'utf-8') -> Generator[str, None, None]:
        """Reconstrói registros sequenciais a partir de arquivo com quebras incorretas"""
        with open(caminho_arquivo, 'r', encoding=encoding) as arquivo:
            buffer = ""

            for linha in arquivo:
                linha = linha.rstrip('\n\r')
                buffer += linha

                # Quando o buffer atingir o tamanho esperado da linha, extrair registros
                while len(buffer) >= self.layout.tamanho_linha:
                    registro = buffer[:self.layout.tamanho_linha]
                    buffer = buffer[self.layout.tamanho_linha:]
                    yield registro

            # Se sobrou algo no buffer, é um registro incompleto
            if buffer.strip():
                yield buffer

    def validar_arquivo_generator(self, caminho_arquivo: str) -> Generator[Tuple[int, List[ErroValidacao]], None, None]:
        """Generator que valida arquivo linha por linha (para arquivos grandes)"""
        if not Path(caminho_arquivo).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                for numero_linha, linha in enumerate(arquivo, 1):
                    # Remover quebra de linha
                    linha = linha.rstrip('\n\r')

                    # Adicionar padding de espaços para completar o tamanho esperado
                    if len(linha) < self.layout.tamanho_linha:
                        linha = linha.ljust(self.layout.tamanho_linha)

                    erros_linha = self.validar_linha(numero_linha, linha)
                    yield numero_linha, erros_linha

        except UnicodeDecodeError:
            # Tentar com encoding latin-1 se UTF-8 falhar
            try:
                with open(caminho_arquivo, 'r', encoding='latin-1') as arquivo:
                    for numero_linha, linha in enumerate(arquivo, 1):
                        linha = linha.rstrip('\n\r')

                        # Adicionar padding de espaços para completar o tamanho esperado
                        if len(linha) < self.layout.tamanho_linha:
                            linha = linha.ljust(self.layout.tamanho_linha)

                        erros_linha = self.validar_linha(numero_linha, linha)
                        yield numero_linha, erros_linha
            except Exception as e:
                raise ValueError(f"Erro ao ler arquivo: {str(e)}")

    def validar_arquivo(self, caminho_arquivo: str, max_erros: int = None) -> ResultadoValidacao:
        """Valida arquivo completo"""
        total_linhas = 0
        linhas_com_erro = 0
        todos_erros = []

        for numero_linha, erros_linha in self.validar_arquivo_generator(caminho_arquivo):
            total_linhas += 1

            if erros_linha:
                linhas_com_erro += 1
                todos_erros.extend(erros_linha)

                # Limitar número de erros se especificado
                if max_erros and len(todos_erros) >= max_erros:
                    break

        linhas_validas = total_linhas - linhas_com_erro

        return ResultadoValidacao(
            total_linhas=total_linhas,
            linhas_validas=linhas_validas,
            linhas_com_erro=linhas_com_erro,
            erros=todos_erros,
            taxa_sucesso=0.0  # Será calculado no __post_init__
        )