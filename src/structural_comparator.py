from typing import List, Generator, Tuple, Optional, Dict, Any
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

    def __init__(self, layout: Layout, show_all_lines: bool = True):
        """Inicializa o comparador.

        Args:
            layout: Layout a ser utilizado para extração/validação estrutural.
            show_all_lines: Quando True, inclui também linhas sem diferenças (idênticas)
                no resultado e no relatório; quando False, mantém o comportamento antigo
                mostrando apenas linhas com diferenças.
        """
        self.layout = layout
        self.show_all_lines = show_all_lines

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
        # Padrão: NFE{tipo}-CAMPO ou NFCOM{tipo}-CAMPO; ou campos sem prefixo específico
        if f"NFE{tipo_registro}-" in nome_campo or f"NFCOM{tipo_registro}-" in nome_campo:
            return True

        # Para layouts simples sem prefixo, considera todos os campos
        if not (nome_campo.startswith("NFE") or nome_campo.startswith("NFCOM")):
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
        # Se já vierem formatadas com barras, reutilizar diretamente
        if '|' in linha_base and '|' in linha_validado:
            linha_base_formatada = linha_base
            linha_validado_formatada = linha_validado
        else:
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

    # Nota: método gerar_representacao_visual removido (substituído por gerar_representacao_visual_com_contagem)

    def comparar_arquivos_por_tipo_generator(self, caminho_base: str, caminho_validado: str) -> Generator[DiferencaEstruturalLinha, None, None]:
        """Percorre o arquivo validado NA ORDEM e compara cada linha com a primeira ocorrência do mesmo tipo no arquivo base."""

        if not Path(caminho_base).exists():
            raise FileNotFoundError(f"Arquivo base não encontrado: {caminho_base}")

        if not Path(caminho_validado).exists():
            raise FileNotFoundError(f"Arquivo a ser validado não encontrado: {caminho_validado}")

        # 1) Construir referência por tipo a partir do arquivo base (primeira ocorrência)
        referencias_base: Dict[str, Tuple[int, str]] = {}

        def add_ref(numero_linha: int, linha: str):
            if len(linha) < 2:
                return
            tipo = self.detectar_tipo_registro(linha)
            if tipo in ['00', '99']:
                return
            if len(linha) < self.layout.tamanho_linha:
                linha_padded = linha.ljust(self.layout.tamanho_linha)
            else:
                linha_padded = linha
            if tipo not in referencias_base:
                referencias_base[tipo] = (numero_linha, linha_padded)

        try:
            with open(caminho_base, 'r', encoding='utf-8') as fbase:
                for n, linha in enumerate(fbase, 1):
                    add_ref(n, linha.rstrip('\n\r'))
        except UnicodeDecodeError:
            with open(caminho_base, 'r', encoding='latin-1') as fbase:
                for n, linha in enumerate(fbase, 1):
                    add_ref(n, linha.rstrip('\n\r'))

        # 2) Percorrer o arquivo validado NA ORDEM e comparar com a referência do mesmo tipo
        #    Além disso, acumular totais por fatura (entre registros '01' e próximo '01')
        #    e validar no registro 56 os totais calculados.

        def _only_digits_to_int(s: str) -> int:
            try:
                digits = ''.join(ch for ch in (s or '') if ch.isdigit())
                return int(digits) if digits else 0
            except Exception:
                return 0

        # Mapeamento: campo total do 56 -> lista de fontes (tipo, campo origem)
        totals_map = {
            'NFE56-TOT-VLR-PIS':        [{'tipo': '38', 'campo': 'NFE38-PIS-VLR'}],
            'NFE56-TOT-VLR-COFINS':     [{'tipo': '40', 'campo': 'NFE40-COFINS-VLR'}],
            'NFE56-TOT-VLR-FUST':       [{'tipo': '42', 'campo': 'NFE42-FUST-VLR'}],
            'NFE56-TOT-VLR-FUNTEL':     [{'tipo': '44', 'campo': 'NFE44-FUNTEL-VLR'}],
            'NFE56-TOT-VLR-ICMS':       [{'tipo': '30', 'campo': 'NFE30-ICM90-VLR'}],
            'NFE56-TOT-VLR-BC':         [{'tipo': '30', 'campo': 'NFE30-ICM90-VLR-BC'}],
        }

        # Mapeamento para validação de cálculos individuais: BC × Alíquota = Valor
        calculation_validations = {
            '38': {  # PIS
                'bc_field': 'NFE38-PIS-VLR-BC',
                'aliq_field': 'NFE38-PIS-ALIQ',
                'valor_field': 'NFE38-PIS-VLR',
                'nome_imposto': 'PIS'
            },
            '40': {  # COFINS
                'bc_field': 'NFE40-COFINS-VLR-BC',
                'aliq_field': 'NFE40-COFINS-ALIQ',
                'valor_field': 'NFE40-COFINS-VLR',
                'nome_imposto': 'COFINS'
            },
            '42': {  # FUST
                'bc_field': 'NFE42-FUST-VLR-BC',
                'aliq_field': 'NFE42-FUST-ALIQ',
                'valor_field': 'NFE42-FUST-VLR',
                'nome_imposto': 'FUST'
            },
            '44': {  # FUNTEL
                'bc_field': 'NFE44-FUNTEL-VLR-BC',
                'aliq_field': 'NFE44-FUNTEL-ALIQ',
                'valor_field': 'NFE44-FUNTEL-VLR',
                'nome_imposto': 'FUNTEL'
            },
            '30': {  # ICMS (tipo 90)
                'bc_field': 'NFE30-ICM90-VLR-BC',
                'aliq_field': 'NFE30-ICM90-ALIQ',
                'valor_field': 'NFE30-ICM90-VLR',
                'nome_imposto': 'ICMS'
            }
        }

        # Índice por tipo para somar rapidamente
        sources_by_tipo: Dict[str, List[Tuple[str, str]]] = {}
        for target, fontes in totals_map.items():
            for f in fontes:
                sources_by_tipo.setdefault(f['tipo'], []).append((target, f['campo']))

        # Acumuladores por fatura
        accum_totals: Dict[str, int] = {k: 0 for k in totals_map.keys()}
        # Componentes: lista de contribuições por total (para depuração/relatório)
        components: Dict[str, List[Dict[str, Any]]] = {k: [] for k in totals_map.keys()}

        def reset_accumulators():
            for k in accum_totals.keys():
                accum_totals[k] = 0
            for k in components.keys():
                components[k].clear()

        def _validar_calculo_imposto(tipo_registro: str, campos_extraidos: Dict[str, str], diferencas_campos: List, linha_completa: str = '', numero_linha: int = 0) -> None:
            """Valida se o cálculo do imposto está correto: BC × Alíquota = Valor"""
            if tipo_registro not in calculation_validations:
                return

            config = calculation_validations[tipo_registro]

            # Extrair NUM-NF da linha (posições 3-15)
            num_nf = ''
            if linha_completa and len(linha_completa) >= 15:
                num_nf = linha_completa[2:15].strip().lstrip('0') or '0'

            # Extrair valores dos campos
            bc_str = campos_extraidos.get(config['bc_field'], '').strip()
            aliq_str = campos_extraidos.get(config['aliq_field'], '').strip()
            valor_str = campos_extraidos.get(config['valor_field'], '').strip()

            # Se algum campo estiver vazio, não validar
            if not bc_str or not aliq_str or not valor_str:
                return

            try:
                # Converter valores decimais para números (removendo pontos e tratando como centésimos)
                def _parse_decimal_value(s: str) -> int:
                    """Converte valor decimal para inteiro com 2 casas decimais implícitas"""
                    try:
                        # Remover espaços e zeros à esquerda
                        clean_s = s.strip().lstrip('0') or '0'

                        # Se contém ponto decimal, processar
                        if '.' in clean_s:
                            parts = clean_s.split('.')
                            inteiro = int(parts[0]) if parts[0] else 0
                            decimal = parts[1][:2].ljust(2, '0')  # Pegar até 2 casas e completar com zeros
                            return inteiro * 100 + int(decimal)
                        else:
                            # Se não tem ponto, considerar como inteiro com 2 casas implícitas
                            return _only_digits_to_int(clean_s)
                    except Exception:
                        return 0

                bc_val = _parse_decimal_value(bc_str)
                aliq_val = _parse_decimal_value(aliq_str)
                valor_declarado = _parse_decimal_value(valor_str)

                # Se todos os valores são zero, não validar
                if bc_val == 0 and aliq_val == 0 and valor_declarado == 0:
                    return

                # Calcular valor esperado: BC × Alíquota / 10000 (alíquota em percentual)
                # Exemplo: BC=17693 (176,93), Alíquota=65 (0,65%), Resultado=115 (1,15)
                # Usar truncamento (divisão inteira) ao invés de arredondamento
                valor_calculado = (bc_val * aliq_val) // 10000

                # Sempre mostrar o cálculo (tanto correto quanto incorreto)
                # Determinar se é correto ou incorreto
                calculo_correto = valor_declarado == valor_calculado
                tipo_calculo = "CORRETO" if calculo_correto else "ERRO"

                # Formatar valores para exibição com 2 casas decimais
                bc_fmt = f"{bc_val/100:.2f}".replace('.', ',')
                aliq_fmt = f"{aliq_val/100:.2f}".replace('.', ',')
                valor_decl_fmt = f"{valor_declarado/100:.2f}".replace('.', ',')
                valor_calc_fmt = f"{valor_calculado/100:.2f}".replace('.', ',')

                # Obter metadados do campo valor
                campo_meta = self.layout.get_campo(config['valor_field'])
                pos_ini = campo_meta.posicao_inicio if campo_meta else 1
                pos_fim = campo_meta.posicao_fim if campo_meta else len(valor_str)

                # Sequência do campo dentro do tipo
                seq = 0
                try:
                    campos_do_tipo = [c for c in self.layout.campos if self._campo_pertence_ao_tipo(c.nome, tipo_registro)]
                    for i, c in enumerate(campos_do_tipo, 1):
                        if c.nome == config['valor_field']:
                            seq = i
                            break
                except Exception:
                    seq = 0

                # Incluir NUM-NF na descrição para facilitar identificação
                identificacao = f"NUM-NF: {num_nf}" if num_nf else f"Linha: {numero_linha}"

                # Criar descrição baseada no resultado
                if calculo_correto:
                    descricao = f"{config['nome_imposto']} ({identificacao}): BC={bc_fmt} × Alíquota={aliq_fmt}% = {valor_calc_fmt} ✅ CORRETO"
                    tipo_diff = f"CALCULO_OK_{config['nome_imposto']}"
                else:
                    diferenca_fmt = f"{(valor_declarado - valor_calculado)/100:.2f}".replace('.', ',')
                    descricao = f"{config['nome_imposto']} ({identificacao}): BC={bc_fmt} × Alíquota={aliq_fmt}% = Calculado={valor_calc_fmt} | Declarado={valor_decl_fmt} | Diferença={diferenca_fmt}"
                    tipo_diff = f"CALCULO_ERRO_{config['nome_imposto']}"

                diferencas_campos.append(
                    DiferencaEstruturalCampo(
                        nome_campo=config['valor_field'],
                        posicao_inicio=pos_ini,
                        posicao_fim=pos_fim,
                        valor_base='',  # Não há base para comparação de cálculo
                        valor_validado=valor_str,
                        tipo_diferenca=tipo_diff,
                        descricao=descricao,
                        sequencia_campo=seq
                    )
                )

            except Exception:
                # Se houver erro na validação, não adicionar diferença
                pass

        try:
            with open(caminho_validado, 'r', encoding='utf-8') as fval:
                for numero_linha_validado, linha_validado in enumerate(fval, 1):
                    linha_validado = linha_validado.rstrip('\n\r')
                    if len(linha_validado) < 2:
                        continue
                    tipo_registro = self.detectar_tipo_registro(linha_validado)
                    if tipo_registro in ['00', '99']:
                        continue
                    # Nova fatura: reset acumuladores
                    if tipo_registro == '01':
                        reset_accumulators()
                    if len(linha_validado) < self.layout.tamanho_linha:
                        linha_validado = linha_validado.ljust(self.layout.tamanho_linha)

                    # Buscar linha base de referência para este tipo
                    linha_base = referencias_base.get(tipo_registro, (0, ' ' * self.layout.tamanho_linha))[1]

                    # Comparar campos filtrando por tipo
                    diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha_validado, tipo_registro)

                    # Acúmulo/validação de totais por fatura
                    try:
                        # Extrair campos para validações
                        campos_tipo = self.extrair_campos_linha(linha_validado, tipo_registro)

                        # Validar cálculos individuais de impostos (BC × Alíquota = Valor)
                        _validar_calculo_imposto(tipo_registro, campos_tipo, diferencas_campos, linha_validado, numero_linha_validado)

                        # Acumular fontes do tipo atual
                        if tipo_registro in sources_by_tipo:
                            for target, campo_src in sources_by_tipo[tipo_registro]:
                                val = _only_digits_to_int(campos_tipo.get(campo_src, ''))
                                accum_totals[target] += val
                                if val:
                                    components[target].append({
                                        'tipo': tipo_registro,
                                        'campo': campo_src,
                                        'valor': val,
                                        'linha': numero_linha_validado
                                    })

                        # Validar no totalizador 56
                        if tipo_registro == '56':
                            campos_56 = self.extrair_campos_linha(linha_validado, '56')
                            for target_field in totals_map.keys():
                                tot_str = campos_56.get(target_field, '')
                                tot_val = _only_digits_to_int(tot_str)
                                if tot_val != accum_totals.get(target_field, 0):
                                    # Formatar valores considerando as duas últimas casas como decimais
                                    tot_val_fmt = (f"{tot_val/100:.2f}").replace('.', ',')
                                    calc_val = accum_totals.get(target_field, 0)
                                    calc_val_fmt = (f"{calc_val/100:.2f}").replace('.', ',')
                                    # Metadados do campo 56
                                    campo_meta = self.layout.get_campo(target_field)
                                    pos_ini = campo_meta.posicao_inicio if campo_meta else 1
                                    pos_fim = campo_meta.posicao_fim if campo_meta else len(tot_str)
                                    # Sequência do campo dentro do tipo 56
                                    seq = 0
                                    try:
                                        campos_do_tipo = [c for c in self.layout.campos if self._campo_pertence_ao_tipo(c.nome, '56')]
                                        for i, c in enumerate(campos_do_tipo, 1):
                                            if c.nome == target_field:
                                                seq = i
                                                break
                                    except Exception:
                                        seq = 0
                                    tipo_diff_label = f"TOTAL_{target_field.replace('NFE56-TOT-VLR-','')}"
                                    diferencas_campos.append(
                                        DiferencaEstruturalCampo(
                                            nome_campo=target_field,
                                            posicao_inicio=pos_ini,
                                            posicao_fim=pos_fim,
                                            valor_base=linha_base[pos_ini-1:pos_fim] if 0 < pos_ini <= len(linha_base) else '',
                                            valor_validado=tot_str,
                                            tipo_diferenca=tipo_diff_label,
                                            descricao=f"{target_field}='{tot_val_fmt}' difere da soma calculada='{calc_val_fmt}' na fatura",
                                            sequencia_campo=seq
                                        )
                                    )
                    except Exception:
                        pass

                    # Geração visual com barras e numeração
                    linha_base_formatada, linha_numeracao = self._gerar_linha_com_barras_e_numeracao(linha_base, tipo_registro)
                    linha_validado_formatada, _ = self._gerar_linha_com_barras_e_numeracao(linha_validado, tipo_registro)

                    yield DiferencaEstruturalLinha(
                        numero_linha=numero_linha_validado,
                        tipo_registro=tipo_registro,
                        arquivo_base_linha=linha_base_formatada,
                        arquivo_validado_linha=linha_validado_formatada,
                        diferencas_campos=diferencas_campos,
                        total_diferencas=len(diferencas_campos),
                        linha_numeracao=linha_numeracao,
                        totais_acumulados=(accum_totals.copy() if tipo_registro == '56' else None),
                        componentes_totais=([{'total': k, 'componentes': components[k].copy()} for k in components.keys()] if tipo_registro == '56' else None)
                    )
        except UnicodeDecodeError:
            with open(caminho_validado, 'r', encoding='latin-1') as fval:
                for numero_linha_validado, linha_validado in enumerate(fval, 1):
                    linha_validado = linha_validado.rstrip('\n\r')
                    if len(linha_validado) < 2:
                        continue
                    tipo_registro = self.detectar_tipo_registro(linha_validado)
                    if tipo_registro in ['00', '99']:
                        continue
                    if tipo_registro == '01':
                        reset_accumulators()
                    if len(linha_validado) < self.layout.tamanho_linha:
                        linha_validado = linha_validado.ljust(self.layout.tamanho_linha)
                    linha_base = referencias_base.get(tipo_registro, (0, ' ' * self.layout.tamanho_linha))[1]
                    diferencas_campos = self.comparar_campos_linha(linha_base, linha_validado, numero_linha_validado, tipo_registro)
                    try:
                        # Extrair campos para validações
                        campos_tipo = self.extrair_campos_linha(linha_validado, tipo_registro)

                        # Validar cálculos individuais de impostos (BC × Alíquota = Valor)
                        _validar_calculo_imposto(tipo_registro, campos_tipo, diferencas_campos, linha_validado, numero_linha_validado)

                        if tipo_registro in sources_by_tipo:
                            for target, campo_src in sources_by_tipo[tipo_registro]:
                                val = _only_digits_to_int(campos_tipo.get(campo_src, ''))
                                accum_totals[target] += val
                                if val:
                                    components[target].append({
                                        'tipo': tipo_registro,
                                        'campo': campo_src,
                                        'valor': val,
                                        'linha': numero_linha_validado
                                    })
                        if tipo_registro == '56':
                            campos_56 = self.extrair_campos_linha(linha_validado, '56')
                            for target_field in totals_map.keys():
                                tot_str = campos_56.get(target_field, '')
                                tot_val = _only_digits_to_int(tot_str)
                                if tot_val != accum_totals.get(target_field, 0):
                                    # Formatar valores considerando as duas últimas casas como decimais
                                    tot_val_fmt = (f"{tot_val/100:.2f}").replace('.', ',')
                                    calc_val = accum_totals.get(target_field, 0)
                                    calc_val_fmt = (f"{calc_val/100:.2f}").replace('.', ',')
                                    campo_meta = self.layout.get_campo(target_field)
                                    pos_ini = campo_meta.posicao_inicio if campo_meta else 1
                                    pos_fim = campo_meta.posicao_fim if campo_meta else len(tot_str)
                                    seq = 0
                                    try:
                                        campos_do_tipo = [c for c in self.layout.campos if self._campo_pertence_ao_tipo(c.nome, '56')]
                                        for i, c in enumerate(campos_do_tipo, 1):
                                            if c.nome == target_field:
                                                seq = i
                                                break
                                    except Exception:
                                        seq = 0
                                    tipo_diff_label = f"TOTAL_{target_field.replace('NFE56-TOT-VLR-','')}"
                                    diferencas_campos.append(
                                        DiferencaEstruturalCampo(
                                            nome_campo=target_field,
                                            posicao_inicio=pos_ini,
                                            posicao_fim=pos_fim,
                                            valor_base=linha_base[pos_ini-1:pos_fim] if 0 < pos_ini <= len(linha_base) else '',
                                            valor_validado=tot_str,
                                            tipo_diferenca=tipo_diff_label,
                                            descricao=f"{target_field}='{tot_val_fmt}' difere da soma calculada='{calc_val_fmt}' na fatura",
                                            sequencia_campo=seq
                                        )
                                    )
                    except Exception:
                        pass
                    linha_base_formatada, linha_numeracao = self._gerar_linha_com_barras_e_numeracao(linha_base, tipo_registro)
                    linha_validado_formatada, _ = self._gerar_linha_com_barras_e_numeracao(linha_validado, tipo_registro)
                    yield DiferencaEstruturalLinha(
                        numero_linha=numero_linha_validado,
                        tipo_registro=tipo_registro,
                        arquivo_base_linha=linha_base_formatada,
                        arquivo_validado_linha=linha_validado_formatada,
                        diferencas_campos=diferencas_campos,
                        total_diferencas=len(diferencas_campos),
                        linha_numeracao=linha_numeracao,
                        totais_acumulados=(accum_totals.copy() if tipo_registro == '56' else None),
                        componentes_totais=([{'total': k, 'componentes': components[k].copy()} for k in components.keys()] if tipo_registro == '56' else None)
                    )


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

            # Incluir sempre quando show_all_lines=True; caso contrário, apenas quando houver diferenças
            if diferenca_linha.total_diferencas > 0:
                linhas_com_diferencas += 1
                todas_diferencas.append(diferenca_linha)
            elif self.show_all_lines:
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

        # Agrupar por tipo e mostrar exemplos (mesmo quando não há diferenças)
        relatorio.append("")
        relatorio.append("📁 DETALHES POR TIPO DE REGISTRO:")
        relatorio.append("")

        diferencas_por_tipo = {}
        for diferenca_linha in resultado.diferencas_por_linha:
            tipo = diferenca_linha.tipo_registro
            if tipo not in diferencas_por_tipo:
                diferencas_por_tipo[tipo] = []
            diferencas_por_tipo[tipo].append(diferenca_linha)

        for tipo_registro, linhas_tipo in sorted(diferencas_por_tipo.items()):
            total_tipo = len(linhas_tipo)
            com_diff = sum(1 for d in linhas_tipo if d.total_diferencas > 0)
            identicas = total_tipo - com_diff
            relatorio.append(f"🔸 TIPO DE REGISTRO: {tipo_registro}")
            relatorio.append(f"   Linhas (comparadas): {total_tipo} | Com diferenças: {com_diff} | Idênticas: {identicas}")
            relatorio.append("")

            # Mostrar até 3 exemplos deste tipo (inclui idênticas se existirem)
            for i, diferenca_linha in enumerate(linhas_tipo[:3]):
                relatorio.append(f"📍 EXEMPLO {i+1} - LINHA {diferenca_linha.numero_linha}")
                relatorio.append(f"   Total de diferenças: {diferenca_linha.total_diferencas}")

                representacao_visual = self.gerar_representacao_visual_com_contagem(
                    diferenca_linha.arquivo_base_linha,
                    diferenca_linha.arquivo_validado_linha,
                    diferenca_linha.diferencas_campos,
                    tipo_registro
                )
                relatorio.append(representacao_visual)
                relatorio.append("")

            if len(linhas_tipo) > 3:
                relatorio.append(f"   ... e mais {len(linhas_tipo) - 3} linhas do tipo {tipo_registro}")
                relatorio.append("")

        return "\n".join(relatorio)