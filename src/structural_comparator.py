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

    def extrair_campos_linha(self, linha: str, tipo_registro: Optional[str] = None) -> Dict[str, str]:
        """Extrai os campos de uma linha baseado no layout, filtrado por tipo de registro se especificado"""
        campos_extraidos = {}

        # Filtrar campos pelo tipo de registro se especificado
        campos_para_extrair = self.layout.campos
        if tipo_registro:
            campos_para_extrair = [
                campo for campo in self.layout.campos
                if self._campo_pertence_ao_tipo(campo.nome, tipo_registro)
            ]

        for campo in campos_para_extrair:
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

    def _campo_pertence_ao_tipo(self, nome_campo: str, tipo_registro: str) -> bool:
        """Verifica se um campo pertence a um tipo de registro específico"""
        # Padrão: NFE{tipo}-CAMPO ou apenas campos sem prefixo NFE
        if f"NFE{tipo_registro}-" in nome_campo:
            return True

        # Para layouts simples sem prefixo NFE, considera todos os campos
        if not nome_campo.startswith("NFE"):
            return True

        return False

    def detectar_tipo_registro(self, linha: str) -> str:
        """Detecta o tipo de registro baseado nos primeiros 2 caracteres da linha"""
        if not linha or len(linha) < 2:
            return "LINHA_VAZIA"

        # Sempre usar os primeiros 2 caracteres como tipo de registro
        tipo = linha[:2]
        return tipo

    def comparar_campos_linha(self, linha_base: str, linha_validado: str, numero_linha: int, tipo_registro: str) -> List[DiferencaEstruturalCampo]:
        """Compara os campos de duas linhas e retorna as diferenças encontradas, filtrado por tipo de registro"""
        diferencas = []

        # Extrair campos filtrados pelo tipo de registro
        campos_base = self.extrair_campos_linha(linha_base, tipo_registro)
        campos_validado = self.extrair_campos_linha(linha_validado, tipo_registro)

        # Obter apenas os campos deste tipo de registro
        campos_do_tipo = [
            campo for campo in self.layout.campos
            if self._campo_pertence_ao_tipo(campo.nome, tipo_registro)
        ]

        for sequencia, campo in enumerate(campos_do_tipo, 1):
            valor_base = campos_base.get(campo.nome, '')
            valor_validado = campos_validado.get(campo.nome, '')

            # Analisar diferenças estruturais (formato, obrigatoriedade, tamanho)
            tipo_diferenca, descricao = self._analisar_tipo_diferenca(
                campo, valor_base, valor_validado
            )

            # Só adicionar se houver problema estrutural real
            if tipo_diferenca and descricao:
                diferenca = DiferencaEstruturalCampo(
                    nome_campo=campo.nome,
                    posicao_inicio=campo.posicao_inicio,
                    posicao_fim=campo.posicao_fim,
                    valor_base=valor_base,
                    valor_validado=valor_validado,
                    tipo_diferenca=tipo_diferenca,
                    descricao=descricao,
                    sequencia_campo=sequencia
                )
                diferencas.append(diferenca)

        return diferencas

    def _analisar_tipo_diferenca(self, campo, valor_base: str, valor_validado: str) -> Tuple[str, str]:
        """Analisa diferenças estruturais (formato, obrigatoriedade, tamanho) entre campos"""

        # Considerar vazio apenas se for string vazia ou só espaços
        base_eh_vazio = not valor_base or valor_base.isspace()
        validado_eh_vazio = not valor_validado or valor_validado.isspace()

        # 1. VERIFICAR OBRIGATORIEDADE
        if campo.obrigatorio and validado_eh_vazio:
            return "CAMPO_OBRIGATORIO", f"Campo obrigatório '{campo.nome}' está vazio no arquivo validado"

        # 2. VERIFICAR TAMANHO (apenas se ambos não estiverem vazios)
        if not base_eh_vazio and not validado_eh_vazio:
            if len(valor_base) != len(valor_validado):
                return "TAMANHO", f"Campo '{campo.nome}' tem tamanho diferente: base={len(valor_base)} chars, validado={len(valor_validado)} chars"

        # 3. VERIFICAR FORMATO (apenas se o campo validado não estiver vazio)
        if not validado_eh_vazio:
            if campo.tipo == TipoCampo.NUMERO:
                # Campo numérico deve conter apenas dígitos (pode ter espaços à esquerda/direita)
                valor_limpo = valor_validado.strip()
                if valor_limpo and not valor_limpo.isdigit():
                    return "FORMATO_NUMERO", f"Campo numérico '{campo.nome}' contém caracteres não numéricos: '{valor_validado}'"

            elif campo.tipo == TipoCampo.DATA:
                # Campo data deve estar em formato válido
                if not self._validar_formato_data(valor_validado, campo.formato):
                    return "FORMATO_DATA", f"Campo data '{campo.nome}' não está no formato correto: '{valor_validado}'"

            elif campo.tipo == TipoCampo.DECIMAL:
                # Campo decimal deve conter apenas dígitos
                valor_limpo = valor_validado.strip()
                if valor_limpo and not valor_limpo.isdigit():
                    return "FORMATO_DECIMAL", f"Campo decimal '{campo.nome}' contém caracteres não numéricos: '{valor_validado}'"

        # 4. VALIDAÇÕES ESPECÍFICAS POR CAMPO
        if campo.nome == 'NFE06-IE-EMIT' and not validado_eh_vazio:
            valor_limpo = valor_validado.strip().upper()
            if valor_limpo == 'ISENTO':
                return "VALOR_PROIBIDO", f"Campo '{campo.nome}' não pode ter o valor 'ISENTO': '{valor_validado}'"

        # Se chegou até aqui, não há diferenças estruturais relevantes
        return None, None

    def _validar_formato_data(self, valor: str, formato: Optional[str]) -> bool:
        """Valida se o valor está em formato de data válido"""
        if not valor.strip():
            return True  # Campo vazio é considerado válido

        # Verificar se contém apenas dígitos (formato básico YYYYMMDD)
        valor_limpo = valor.strip()
        if formato and 'YYYYMMDD' in formato:
            return len(valor_limpo) == 8 and valor_limpo.isdigit()

        return valor_limpo.isdigit()

    def agrupar_registros_por_tipo(self, caminho_arquivo: str) -> Dict[str, List[Tuple[int, str]]]:
        """Agrupa registros por tipo, ignorando tipos 00 e 99"""
        registros_por_tipo = {}

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                for numero_linha, linha in enumerate(arquivo, 1):
                    linha = linha.rstrip('\n\r')

                    if len(linha) < 2:
                        continue

                    tipo_registro = self.detectar_tipo_registro(linha)

                    # Ignorar tipos 00 e 99 (header e trailer)
                    if tipo_registro in ['00', '99']:
                        continue

                    # Padding para completar tamanho esperado
                    if len(linha) < self.layout.tamanho_linha:
                        linha = linha.ljust(self.layout.tamanho_linha)

                    if tipo_registro not in registros_por_tipo:
                        registros_por_tipo[tipo_registro] = []

                    registros_por_tipo[tipo_registro].append((numero_linha, linha))

        except UnicodeDecodeError:
            # Tentar com encoding latin-1
            with open(caminho_arquivo, 'r', encoding='latin-1') as arquivo:
                for numero_linha, linha in enumerate(arquivo, 1):
                    linha = linha.rstrip('\n\r')

                    if len(linha) < 2:
                        continue

                    tipo_registro = self.detectar_tipo_registro(linha)

                    # Ignorar tipos 00 e 99 (header e trailer)
                    if tipo_registro in ['00', '99']:
                        continue

                    # Padding para completar tamanho esperado
                    if len(linha) < self.layout.tamanho_linha:
                        linha = linha.ljust(self.layout.tamanho_linha)

                    if tipo_registro not in registros_por_tipo:
                        registros_por_tipo[tipo_registro] = []

                    registros_por_tipo[tipo_registro].append((numero_linha, linha))

        return registros_por_tipo

    def gerar_representacao_visual_com_contagem(self, linha_base: str, linha_validado: str, diferencas: List[DiferencaEstruturalCampo], tipo_registro: str) -> str:
        """Gera representação visual das diferenças usando separador | de forma compacta"""

        # Separação por campos usando | (filtrado por tipo)
        campos_base = self.extrair_campos_linha(linha_base, tipo_registro)
        campos_validado = self.extrair_campos_linha(linha_validado, tipo_registro)

        # Obter apenas os campos deste tipo de registro
        campos_do_tipo = [
            campo for campo in self.layout.campos
            if self._campo_pertence_ao_tipo(campo.nome, tipo_registro)
        ]

        linha_base_separada = []
        linha_validado_separada = []

        for campo in campos_do_tipo:
            valor_base = campos_base.get(campo.nome, '')
            valor_validado = campos_validado.get(campo.nome, '')
            linha_base_separada.append(valor_base)
            linha_validado_separada.append(valor_validado)

        # Formatação com barras (uma linha cada, sem quebrar)
        linha_base_formatada = "|".join(linha_base_separada) + "|"
        linha_validado_formatada = "|".join(linha_validado_separada) + "|"

        representacao = []
        representacao.append("BASE:      " + linha_base_formatada)
        representacao.append("VALIDADO:  " + linha_validado_formatada)

        # Problemas estruturais (resumido)
        if diferencas:
            representacao.append("")
            representacao.append(f"Problemas estruturais encontrados: {len(diferencas)}")
            for diff in diferencas:
                representacao.append(f"  - {diff.descricao}")

        return "\n".join(representacao)

    def _gerar_linha_com_barras(self, linha: str, tipo_registro: str) -> str:
        """Gera representação da linha com campos separados por barras, preservando espaços"""
        # Filtrar apenas os campos que pertencem ao tipo de registro
        campos_do_tipo = [
            campo for campo in self.layout.campos
            if self._campo_pertence_ao_tipo(campo.nome, tipo_registro)
        ]

        valores_campos = []
        for campo in campos_do_tipo:
            # Extrair valor diretamente da linha preservando espaços exatos
            inicio = campo.posicao_inicio - 1  # Converter para 0-indexed
            fim = campo.posicao_fim

            # Extrair valor (cuidando com linhas muito curtas)
            if inicio < len(linha):
                valor = linha[inicio:fim] if fim <= len(linha) else linha[inicio:]
                # Garantir que o campo tem o tamanho exato (pad com espaços se necessário)
                tamanho_esperado = campo.posicao_fim - campo.posicao_inicio + 1
                valor = valor.ljust(tamanho_esperado)
            else:
                # Se a linha é muito curta, preencher com espaços
                tamanho_esperado = campo.posicao_fim - campo.posicao_inicio + 1
                valor = ' ' * tamanho_esperado

            valores_campos.append(valor)

        # Retornar com barras separadoras (incluindo no início e fim)
        return "|".join(valores_campos) + "|"

    def _gerar_linha_com_barras_e_numeracao(self, linha: str, tipo_registro: str) -> Tuple[str, str]:
        """Gera representação da linha com campos separados por barras e linha de numeração"""
        # Filtrar apenas os campos que pertencem ao tipo de registro
        campos_do_tipo = [
            campo for campo in self.layout.campos
            if self._campo_pertence_ao_tipo(campo.nome, tipo_registro)
        ]

        valores_campos = []
        numeros_campos = []

        for sequencia, campo in enumerate(campos_do_tipo, 1):
            # Extrair valor diretamente da linha preservando espaços exatos
            inicio = campo.posicao_inicio - 1  # Converter para 0-indexed
            fim = campo.posicao_fim

            # Extrair valor (cuidando com linhas muito curtas)
            if inicio < len(linha):
                valor = linha[inicio:fim] if fim <= len(linha) else linha[inicio:]
                # Garantir que o campo tem o tamanho exato (pad com espaços se necessário)
                tamanho_esperado = campo.posicao_fim - campo.posicao_inicio + 1
                valor = valor.ljust(tamanho_esperado)
            else:
                # Se a linha é muito curta, preencher com espaços
                tamanho_esperado = campo.posicao_fim - campo.posicao_inicio + 1
                valor = ' ' * tamanho_esperado

            valores_campos.append(valor)

            # Criar numeração centralizada no campo
            numero_str = str(sequencia).zfill(2)  # 01, 02, 03, etc.
            tamanho_campo = len(valor)
            # Centralizar o número no tamanho do campo
            numero_formatado = numero_str.center(tamanho_campo)
            numeros_campos.append(numero_formatado)

        # Retornar linha com dados e linha com numeração
        linha_dados = "|".join(valores_campos) + "|"
        linha_numeracao = "|".join(numeros_campos) + "|"

        return linha_dados, linha_numeracao

    def gerar_representacao_visual(self, linha_base: str, linha_validado: str, diferencas: List[DiferencaEstruturalCampo]) -> str:
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
                status = "[ERROR]"
                linha_base_separada.append(f"{valor_base}")
                linha_validado_separada.append(f"{valor_validado}")
                status_campos.append(f"{status} {campo.nome}")
            else:
                status = "[OK]"
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

    def agrupar_registros_por_nota_fiscal(self, caminho_arquivo: str) -> List[List[Tuple[int, str, str]]]:
        """Agrupa registros em notas fiscais completas"""
        registros_todos = []

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                for numero_linha, linha in enumerate(arquivo, 1):
                    linha = linha.rstrip('\n\r')

                    if len(linha) < 2:
                        continue

                    tipo_registro = self.detectar_tipo_registro(linha)

                    # Ignorar tipos 00 e 99 (header e trailer)
                    if tipo_registro in ['00', '99']:
                        continue

                    # Padding para completar tamanho esperado
                    if len(linha) < self.layout.tamanho_linha:
                        linha = linha.ljust(self.layout.tamanho_linha)

                    # Adicionar todos os registros
                    registros_todos.append((numero_linha, linha, tipo_registro))

        except UnicodeDecodeError:
            # Tentar com encoding latin-1
            with open(caminho_arquivo, 'r', encoding='latin-1') as arquivo:
                for numero_linha, linha in enumerate(arquivo, 1):
                    linha = linha.rstrip('\n\r')

                    if len(linha) < 2:
                        continue

                    tipo_registro = self.detectar_tipo_registro(linha)

                    # Ignorar tipos 00 e 99 (header e trailer)
                    if tipo_registro in ['00', '99']:
                        continue

                    # Padding para completar tamanho esperado
                    if len(linha) < self.layout.tamanho_linha:
                        linha = linha.ljust(self.layout.tamanho_linha)

                    # Adicionar todos os registros
                    registros_todos.append((numero_linha, linha, tipo_registro))

        # Por enquanto, considerar tudo como uma única nota fiscal
        # No futuro, podemos implementar lógica mais sofisticada para separar múltiplas notas
        return [registros_todos] if registros_todos else []

    def comparar_arquivos_por_tipo_generator(self, caminho_base: str, caminho_validado: str) -> Generator[DiferencaEstruturalLinha, None, None]:
        """Generator que compara arquivos agrupados por nota fiscal completa"""

        if not Path(caminho_base).exists():
            raise FileNotFoundError(f"Arquivo base não encontrado: {caminho_base}")

        if not Path(caminho_validado).exists():
            raise FileNotFoundError(f"Arquivo a ser validado não encontrado: {caminho_validado}")

        # Agrupar registros por nota fiscal completa
        notas_base = self.agrupar_registros_por_nota_fiscal(caminho_base)
        notas_validado = self.agrupar_registros_por_nota_fiscal(caminho_validado)

        # Usar a primeira nota fiscal da base como padrão
        if len(notas_base) == 0:
            return

        nota_base_padrao = notas_base[0]  # Primeira nota fiscal como padrão

        # Comparar cada nota fiscal do validado com o padrão
        for idx_nota, nota_validado in enumerate(notas_validado, 1):
            # Criar registros agrupados por tipo para facilitar comparação
            registros_base_por_tipo = {}
            registros_validado_por_tipo = {}

            # Agrupar registros da nota base padrão por tipo
            for numero_linha, linha, tipo_registro in nota_base_padrao:
                if tipo_registro not in registros_base_por_tipo:
                    registros_base_por_tipo[tipo_registro] = []
                registros_base_por_tipo[tipo_registro].append((numero_linha, linha))

            # Agrupar registros da nota validado por tipo
            for numero_linha, linha, tipo_registro in nota_validado:
                if tipo_registro not in registros_validado_por_tipo:
                    registros_validado_por_tipo[tipo_registro] = []
                registros_validado_por_tipo[tipo_registro].append((numero_linha, linha))

            # Obter todos os tipos únicos
            todos_tipos = set(registros_base_por_tipo.keys()) | set(registros_validado_por_tipo.keys())

            for tipo_registro in sorted(todos_tipos):
                linhas_base = registros_base_por_tipo.get(tipo_registro, [])
                linhas_validado = registros_validado_por_tipo.get(tipo_registro, [])

                # Comparação tipo por tipo dentro da nota fiscal
                if len(linhas_base) > 0 and len(linhas_validado) > 0:
                    # Usar a primeira linha base como referência (padrão)
                    numero_linha_base, linha_base = linhas_base[0]
                    numero_linha_validado, linha_validado = linhas_validado[0]

                    # Usar número da linha validado + info da nota
                    numero_linha = numero_linha_validado

                    # Comparar campos da linha
                    diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha, tipo_registro)

                    # Gerar representação visual
                    linha_base_formatada, linha_numeracao = self._gerar_linha_com_barras_e_numeracao(linha_base, tipo_registro)
                    linha_validado_formatada, _ = self._gerar_linha_com_barras_e_numeracao(linha_validado, tipo_registro)

                    # Criar resultado da linha
                    diferenca_linha = DiferencaEstruturalLinha(
                        numero_linha=numero_linha,
                        tipo_registro=tipo_registro,
                        arquivo_base_linha=linha_base_formatada,
                        arquivo_validado_linha=linha_validado_formatada,
                        diferencas_campos=diferencas_campos,
                        total_diferencas=len(diferencas_campos),
                        linha_numeracao=linha_numeracao
                    )

                    yield diferenca_linha

                elif len(linhas_base) > 0:
                    # Só existe base, sem validado para este tipo
                    numero_linha_base, linha_base = linhas_base[0]
                    linha_validado = " " * self.layout.tamanho_linha

                    # Comparar campos da linha
                    diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha_base, tipo_registro)

                    # Gerar representação visual
                    linha_base_formatada, linha_numeracao = self._gerar_linha_com_barras_e_numeracao(linha_base, tipo_registro)
                    linha_validado_formatada, _ = self._gerar_linha_com_barras_e_numeracao(linha_validado, tipo_registro)

                    # Criar resultado da linha
                    diferenca_linha = DiferencaEstruturalLinha(
                        numero_linha=numero_linha_base,
                        tipo_registro=tipo_registro,
                        arquivo_base_linha=linha_base_formatada,
                        arquivo_validado_linha=linha_validado_formatada,
                        diferencas_campos=diferencas_campos,
                        total_diferencas=len(diferencas_campos),
                        linha_numeracao=linha_numeracao
                    )

                    yield diferenca_linha

                elif len(linhas_validado) > 0:
                    # Só existe validado, sem base para este tipo
                    numero_linha_validado, linha_validado = linhas_validado[0]
                    linha_base = " " * self.layout.tamanho_linha

                    # Comparar campos da linha
                    diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha_validado, tipo_registro)

                    # Gerar representação visual com barras separadoras e numeração
                    linha_base_formatada, linha_numeracao = self._gerar_linha_com_barras_e_numeracao(linha_base, tipo_registro)
                    linha_validado_formatada, _ = self._gerar_linha_com_barras_e_numeracao(linha_validado, tipo_registro)

                    # Criar resultado da linha
                    diferenca_linha = DiferencaEstruturalLinha(
                        numero_linha=numero_linha_validado,
                        tipo_registro=tipo_registro,
                        arquivo_base_linha=linha_base_formatada,
                        arquivo_validado_linha=linha_validado_formatada,
                        diferencas_campos=diferencas_campos,
                        total_diferencas=len(diferencas_campos),
                        linha_numeracao=linha_numeracao
                    )

                    yield diferenca_linha


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
                    diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha, tipo_registro)

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
                        diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha, tipo_registro)

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
        """Compara dois arquivos estruturalmente agrupados por tipo de registro"""

        total_linhas = 0
        linhas_com_diferencas = 0
        todas_diferencas = []

        for diferenca_linha in self.comparar_arquivos_por_tipo_generator(caminho_base, caminho_validado):
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
        relatorio.append("[REPORT] RELATÓRIO DE COMPARAÇÃO ESTRUTURAL DE ARQUIVOS")
        relatorio.append("=" * 80)
        relatorio.append("")

        # Estatísticas gerais
        relatorio.append(f"[STATS] ESTATÍSTICAS GERAIS:")
        relatorio.append(f"   Total de linhas comparadas: {resultado.total_linhas_comparadas}")
        relatorio.append(f"   Linhas idênticas: {resultado.linhas_identicas}")
        relatorio.append(f"   Linhas com diferenças: {resultado.linhas_com_diferencas}")
        relatorio.append(f"   Taxa de identidade: {resultado.taxa_identidade:.2f}%")
        relatorio.append("")

        if resultado.linhas_com_diferencas == 0:
            relatorio.append("[OK] ARQUIVOS ESTRUTURALMENTE IDÊNTICOS!")
            relatorio.append("   Todos os campos coincidem perfeitamente.")
        else:
            relatorio.append(f"[ERROR] ENCONTRADAS {resultado.linhas_com_diferencas} LINHAS COM DIFERENÇAS:")
            relatorio.append("")

            # Agrupar diferenças por tipo de registro
            diferencas_por_tipo = {}
            for diferenca_linha in resultado.diferencas_por_linha:
                tipo = diferenca_linha.tipo_registro
                if tipo not in diferencas_por_tipo:
                    diferencas_por_tipo[tipo] = []
                diferencas_por_tipo[tipo].append(diferenca_linha)

            # Mostrar até 3 exemplos por tipo de registro
            for tipo_registro, diferencias_tipo in sorted(diferencas_por_tipo.items()):
                relatorio.append(f"[TYPE] TIPO DE REGISTRO: {tipo_registro}")
                relatorio.append(f"   Total de linhas com diferenças: {len(diferencias_tipo)}")
                relatorio.append("")

                # Mostrar até 3 exemplos deste tipo
                for i, diferenca_linha in enumerate(diferencias_tipo[:3]):
                    relatorio.append(f"[EXEMPLO] EXEMPLO {i+1} - LINHA {diferenca_linha.numero_linha}")
                    relatorio.append(f"   Total de diferenças: {diferenca_linha.total_diferencas}")

                    # Mostrar representação visual com contagem
                    representacao_visual = self.gerar_representacao_visual_com_contagem(
                        diferenca_linha.arquivo_base_linha,
                        diferenca_linha.arquivo_validado_linha,
                        diferenca_linha.diferencas_campos,
                        tipo_registro
                    )
                    relatorio.append(representacao_visual)
                    relatorio.append("")

                if len(diferencias_tipo) > 3:
                    relatorio.append(f"   ... e mais {len(diferencias_tipo) - 3} linhas com diferenças do tipo {tipo_registro}")
                    relatorio.append("")

        return "\n".join(relatorio)