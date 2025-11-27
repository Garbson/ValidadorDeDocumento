"""
Validador aprimorado que inclui:
1. Cálculos de impostos (como na comparação)
2. Validação de estrutura (registros duplicados)
3. Contagem de notas fiscais por fatura
4. Validação de unicidade (fatura + NF)
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import re

try:
    from .models import ResultadoValidacao, ErroValidacao, Layout
    from .file_validator import ValidadorArquivo
    from .structural_comparator import ComparadorEstruturalArquivos
except ImportError:
    from models import ResultadoValidacao, ErroValidacao, Layout
    from file_validator import ValidadorArquivo
    from structural_comparator import ComparadorEstruturalArquivos


class EnhancedValidator:
    """Validador aprimorado com validações estruturais e cálculos de impostos"""

    def __init__(self, layout: Layout):
        self.layout = layout
        self.validador_basico = ValidadorArquivo(layout)

        # Contadores para validações estruturais
        self.notas_fiscais_por_fatura: Dict[str, List[str]] = defaultdict(list)
        self.combinacoes_fatura_nf: Set[Tuple[str, str]] = set()
        self.registros_por_linha: Dict[int, str] = {}
        # Conteúdo bruto das linhas (para exemplos de cálculo em erros de totalizador)
        self.linhas_conteudo: Dict[int, str] = {}

        # Contexto atual de fatura e NF, e agrupamento por NF
        self.current_fatura: Optional[str] = None
        self.current_nf: Optional[str] = None
        # key: (fatura, nf) -> {'linhas': List[int], 'contribuintes_por_total': Dict[str, List[int]], 'transaction_id_claro': Optional[str]}
        self.grupos_nf: Dict[Tuple[str, str], Dict] = {}

        # Declarações encontradas no header 00 (ex.: quantidade de NF)
        self.declaracoes_header: Dict[str, int] = {}

        # Contador de registros 01 (para ficar igual à SEFAZ)
        self.total_registros_01: int = 0

        # Duplicatas para análise
        self.duplicatas_fatura_nf: List[Dict] = []

        # Acumuladores para cálculos de impostos (como na comparação)
        self.totais_acumulados: Dict[str, int] = {
            'NFE56-TOT-VLR-PIS': 0,
            'NFE56-TOT-VLR-COFINS': 0,
            'NFE56-TOT-VLR-FUST': 0,
            'NFE56-TOT-VLR-FUNTEL': 0,
            'NFE56-TOT-VLR-ICMS': 0,
            'NFE56-TOT-VLR-FCP': 0,
            'NFE56-TOT-VLR-BC': 0,
        }

        # Estado estrutural por NF
        self.item_aberto: Optional[Dict] = None  # {'linha_20': int, 'tem_36': bool, 'taxes_seen': Set[str]}
        self.contador_tipos_nf: Counter = Counter()

        # Mapeamento EXATO da comparação estrutural
        self.totals_map = {
            'NFE56-TOT-VLR-PIS':        [{'tipo': '38', 'campo': 'NFE38-PIS-VLR'}],
            'NFE56-TOT-VLR-COFINS':     [{'tipo': '40', 'campo': 'NFE40-COFINS-VLR'}],
            'NFE56-TOT-VLR-FUST':       [{'tipo': '42', 'campo': 'NFE42-FUST-VLR'}],
            'NFE56-TOT-VLR-FUNTEL':     [{'tipo': '44', 'campo': 'NFE44-FUNTEL-VLR'}],
            'NFE56-TOT-VLR-ICMS':       [{'tipo': '22', 'campo': 'NFE22-ICM00-VLR'}],
            'NFE56-TOT-VLR-FCP':        [{'tipo': '22', 'campo': 'NFE22-ICM00-VLR-FCP'}],
            'NFE56-TOT-VLR-BC':         [{'tipo': '22', 'campo': 'NFE22-ICM00-VLR-BC'}],
        }

        # Mapeamento para validação de cálculos individuais EXATO da comparação
        self.calculation_validations = {
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
            },
            '22': {  # ICMS (tipo 00)
                'bc_field': 'NFE22-ICM00-VLR-BC',
                'aliq_field': 'NFE22-ICM00-ALIQ',
                'valor_field': 'NFE22-ICM00-VLR',
                'nome_imposto': 'ICMS',
                'validacoes_adicionais': [
                    {
                        'bc_field': 'NFE22-ICM00-VLR-BC',
                        'aliq_field': 'NFE22-ICM00-ALIQ-FCP',
                        'valor_field': 'NFE22-ICM00-VLR-FCP',
                        'nome_imposto': 'FCP'
                    }
                ]
            }
        }

    def validar_arquivo(self, caminho_arquivo: str, max_erros: int = None) -> ResultadoValidacao:
        """Validação focada nos 4 pontos específicos (sem erros básicos de campo)"""

        # Reset dos contadores
        self._reset_contadores()

        # Fazer APENAS as validações aprimoradas (4 pontos específicos)
        erros_aprimorados = []
        total_linhas = 0

        # Tentar ler com UTF-8, se falhar usar latin-1
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                linhas = arquivo.readlines()
        except UnicodeDecodeError:
            with open(caminho_arquivo, 'r', encoding='latin-1') as arquivo:
                linhas = arquivo.readlines()

        try:
            total_linhas = len([l for l in linhas if l.strip()])

            # Primeira passada: coletar informações e validar estrutura
            for numero_linha, linha_content in enumerate(linhas, 1):
                try:
                    linha_content = linha_content.rstrip('\n\r')
                    # Guardar conteúdo da linha para breakdowns posteriores
                    self.linhas_conteudo[numero_linha] = linha_content

                    if len(linha_content) < 2:
                        continue

                    # Detectar tipo de registro
                    tipo_registro = linha_content[:2]
                    self.registros_por_linha[numero_linha] = tipo_registro
                except Exception as e:
                    # Capturar erro específico da linha e continuar
                    erro_linha = ErroValidacao(
                        linha=numero_linha,
                        campo="LINHA",
                        valor_encontrado=str(e),
                        erro_tipo="ERRO_LEITURA",
                        descricao=f"Erro ao processar linha {numero_linha}: {str(e)}",
                        valor_esperado="Linha válida"
                    )
                    erros_aprimorados.append(erro_linha)
                    continue

                # Header (00): capturar declarações
                if tipo_registro == '00':
                    self._capturar_declaracoes_header_00(numero_linha, linha_content)

                # Validação 1: Estrutura - evitar registros duplicados consecutivos
                erros_estrutura = self._validar_estrutura_consecutiva(numero_linha, tipo_registro)
                erros_aprimorados.extend(erros_estrutura)

                # Validação 2: Coletar dados de fatura e NF (registro 01)
                if tipo_registro == '01':
                    # Primeiro processa o 01 para atualizar o contexto da NF atual
                    erros_unicidade = self._processar_registro_01(numero_linha, linha_content)
                    erros_aprimorados.extend(erros_unicidade)
                    # Agora registre a própria linha 01 no grupo correto (NF atual)
                    self._registrar_linha_no_grupo(numero_linha)
                else:
                    # Para os demais tipos, registra no grupo vigente
                    self._registrar_linha_no_grupo(numero_linha)

                # Validação 3 & 3.5: Validar cálculos E acumular valores corretos
                # IMPORTANTE: Fazer os cálculos primeiro e acumular apenas valores CORRETOS
                erros_calculos_linha = self._validar_calculos_linha(numero_linha, tipo_registro, linha_content)
                erros_aprimorados.extend(erros_calculos_linha)

                # Acumular valores (usando valores corretos se houver erro de cálculo)
                self._acumular_valores_impostos(numero_linha, tipo_registro, linha_content, erros_calculos_linha)

                # Validação 4: Verificar totalizador (registro 56)
                if tipo_registro == '56':
                    erros_totais = self._validar_totalizador_56(numero_linha, linha_content)
                    erros_aprimorados.extend(erros_totais)

                # Capturar TRANSACTION_ID_CLARO dos registros 90 (por NF)
                if tipo_registro == '90':
                    try:
                        # Heurística: procurar padrão 14 dígitos + 6 dígitos + 'FTC' (ex.: 2025083107360004FTC)
                        m = re.search(r"\b\d{10,18}FTC\b", linha_content)
                        if m and self.current_fatura is not None and self.current_nf is not None:
                            key_g = (self.current_fatura, self.current_nf)
                            self.grupos_nf.setdefault(key_g, {
                                'linhas': [],
                                'contribuintes_por_total': {k: [] for k in self.totais_acumulados.keys()}
                            })
                            self.grupos_nf[key_g]['transaction_id_claro'] = m.group(0)
                    except Exception:
                        pass

                # Validação 5: Verificar trailer final (apenas registro 99) - quantidade de notas fiscais
                if tipo_registro == '99':
                    erros_trailer = self._validar_trailer_99(numero_linha, linha_content)
                    erros_aprimorados.extend(erros_trailer)

                # Validação estrutural por NF: regras de sequência
                erros_seq = self._validar_estrutura_nf(numero_linha, tipo_registro)
                erros_aprimorados.extend(erros_seq)

                # Removido limite de erros - queremos ver TODOS os problemas

            # Validações adicionais pós-passada: conferir header 00 vs contagem real de NF
            if self.declaracoes_header:
                    quantidade_real_nf = self.total_registros_01  # Igual SEFAZ: total registros 01
                    for campo_nome, qtd_decl in self.declaracoes_header.items():
                        if 'QTD-NF' in campo_nome or 'TOT-NF' in campo_nome or 'QTD-NOTAS' in campo_nome:
                            if qtd_decl != quantidade_real_nf:
                                erro = ErroValidacao(
                                    linha=1,
                                    campo=campo_nome,
                                    valor_encontrado=str(qtd_decl),
                                    erro_tipo='HEADER_QTD_NF',
                                    descricao=(
                                        f"Quantidade de NF no header ({qtd_decl}) difere da quantidade real encontrada ({quantidade_real_nf})"
                                    ),
                                    valor_esperado=str(quantidade_real_nf)
                                )
                                erros_aprimorados.append(erro)

                # Não precisamos mais da validação 5 aqui, pois já está sendo feita linha por linha

        except Exception as e:
            # Em caso de erro, adicionar como erro de validação
            erro_arquivo = ErroValidacao(
                linha=1,
                campo="ARQUIVO",
                valor_encontrado=str(e),
                erro_tipo="ERRO_LEITURA",
                descricao=f"Erro ao ler arquivo: {str(e)}",
                valor_esperado="Arquivo válido"
            )
            erros_aprimorados.append(erro_arquivo)

        # Sem limite de erros - retornar TODOS os problemas encontrados
        todos_erros = erros_aprimorados

        # Recalcular estatísticas focadas nos 4 pontos
        linhas_com_erro_total = len(set(erro.linha for erro in todos_erros))
        linhas_validas_total = total_linhas - linhas_com_erro_total
        taxa_sucesso_total = (linhas_validas_total / total_linhas * 100) if total_linhas > 0 else 100

        return ResultadoValidacao(
            total_linhas=total_linhas,
            linhas_validas=linhas_validas_total,
            linhas_com_erro=linhas_com_erro_total,
            erros=todos_erros,  # TODOS os erros, sem limite
            taxa_sucesso=taxa_sucesso_total
        )

    def _reset_contadores(self):
        """Reset todos os contadores para nova validação"""
        self.notas_fiscais_por_fatura.clear()
        self.combinacoes_fatura_nf.clear()
        self.registros_por_linha.clear()
        self.linhas_conteudo.clear()
        self.current_fatura = None
        self.current_nf = None
        self.grupos_nf.clear()
        self.declaracoes_header.clear()
        self.item_aberto = None
        self.contador_tipos_nf = Counter()
        self.total_registros_01 = 0
        self.duplicatas_fatura_nf.clear()

        for key in self.totais_acumulados:
            self.totais_acumulados[key] = 0

    def _validar_estrutura_consecutiva(self, numero_linha: int, tipo_registro: str) -> List[ErroValidacao]:
        """Validação 1: Evitar registros duplicados consecutivos"""
        erros = []

        # Verificar se o registro anterior é do mesmo tipo
        linha_anterior = numero_linha - 1
        if linha_anterior in self.registros_por_linha:
            tipo_anterior = self.registros_por_linha[linha_anterior]

            # Exceção para header/trailer (00, 99) e registros de item/impostos (20, 22, 36, 38, 40, 42, 44)
            # que podem se repetir para múltiplos itens
            tipos_permitidos_repetir = ['00', '99', '20', '22', '36', '38', '40', '42', '44']
            
            if tipo_anterior == tipo_registro and tipo_registro not in tipos_permitidos_repetir:
                erro = ErroValidacao(
                    linha=numero_linha,
                    campo=f"NFE{tipo_registro}-TP-REG",
                    valor_encontrado=tipo_registro,
                    erro_tipo="ESTRUTURA_DUPLICADA",
                    descricao=f"Registro tipo {tipo_registro} duplicado consecutivamente (linha anterior: {linha_anterior})",
                    valor_esperado="Tipos de registro diferentes em sequência"
                )
                erros.append(erro)

        return erros

    def _processar_registro_01(self, numero_linha: int, linha_content: str) -> List[ErroValidacao]:
        """Validação 2: Processar registro 01 para fatura/NF e verificar unicidade"""
        erros = []

        try:
            # Contador igual à SEFAZ: cada registro 01 = 1 NF
            self.total_registros_01 += 1

            # Extrair fatura e NF das posições conhecidas (preservando zeros à esquerda)
            # NUM-FATURA: posições 3-15 (índices 2-14)
            # NUM-NF: posições 24-32 (índices 23-31)
            if len(linha_content) >= 32:
                num_fatura = (linha_content[2:15] or '').strip() or '0'
                num_nf = (linha_content[23:32] or '').strip() or '0'

                # Atualizar contexto atual e inicializar agrupamento
                self.current_fatura = num_fatura
                self.current_nf = num_nf

                key = (self.current_fatura, self.current_nf)
                if key not in self.grupos_nf:
                    self.grupos_nf[key] = {
                        'linhas': [],
                        'contribuintes_por_total': {k: [] for k in self.totais_acumulados.keys()}
                    }

                # Validação 3: Contagem de notas fiscais por fatura
                self.notas_fiscais_por_fatura[num_fatura].append(num_nf)

                # Validação 4: Unicidade de combinação fatura + NF
                combinacao = (num_fatura, num_nf)
                if combinacao in self.combinacoes_fatura_nf:
                    # Registrar como duplicata para análise
                    self.duplicatas_fatura_nf.append({
                        'linha': numero_linha,
                        'fatura': num_fatura,
                        'nf': num_nf,
                        'combinacao': f"{num_fatura}|{num_nf}"
                    })

                    erro = ErroValidacao(
                        linha=numero_linha,
                        campo="NFE01-NUM-NF",
                        valor_encontrado=f"Fatura: {num_fatura}, NF: {num_nf}",
                        erro_tipo="COMBINACAO_DUPLICADA",
                        descricao=f"Combinação Fatura {num_fatura} + NF {num_nf} já foi utilizada anteriormente",
                        valor_esperado="Combinação única de fatura + nota fiscal"
                    )
                    erros.append(erro)
                else:
                    self.combinacoes_fatura_nf.add(combinacao)

        except Exception as e:
            erro = ErroValidacao(
                linha=numero_linha,
                campo="NFE01-ESTRUTURA",
                valor_encontrado="Erro de parsing",
                erro_tipo="ERRO_ESTRUTURA",
                descricao=f"Erro ao processar registro 01: {str(e)}",
                valor_esperado="Registro 01 válido"
            )
            erros.append(erro)

        return erros

    def _acumular_valores_impostos(self, numero_linha: int, tipo_registro: str, linha_content: str, erros_calculos: List = None):
        """Validação 3: Acumular valores para cálculos de impostos - usando valores CORRETOS"""

        # CRITICAL: Resetar acumuladores no início de nova fatura (registro 01) IGUAL à comparação
        if tipo_registro == '01':
            for key in self.totais_acumulados:
                self.totais_acumulados[key] = 0
            # Reiniciar estado estrutural para nova NF
            self.item_aberto = None
            self.contador_tipos_nf = Counter()

        # Acumular valores usando a MESMA lógica da comparação
        for total_field, fontes in self.totals_map.items():
            for fonte in fontes:
                if fonte['tipo'] == tipo_registro:
                    # Verificar se há erro de cálculo para este campo
                    valor_a_acumular = None
                    campo_fonte = fonte['campo']

                    # Se há erros de cálculo OU valor zerado, procurar valor correto
                    if erros_calculos:
                        for erro in erros_calculos:
                            if erro.campo == campo_fonte and ('CALCULO_ERRO' in erro.erro_tipo or 'VALOR_ZERADO' in erro.erro_tipo):
                                # Usar valor esperado (correto) em vez do declarado
                                valor_correto_str = erro.valor_esperado.replace(',', '.')
                                try:
                                    valor_a_acumular = int(float(valor_correto_str) * 100)
                                except:
                                    valor_a_acumular = None
                                break

                    # Se não há erro ou não conseguiu extrair valor correto, usar valor declarado
                    if valor_a_acumular is None:
                        valor_str = self._extrair_valor_campo_str(linha_content, campo_fonte)
                        valor_a_acumular = self._only_digits_to_int(valor_str)

                    if valor_a_acumular > 0:
                        self.totais_acumulados[total_field] += valor_a_acumular
                        # Registrar linha contribuinte do total para a NF corrente
                        if self.current_fatura is not None and self.current_nf is not None:
                            key = (self.current_fatura, self.current_nf)
                            if key not in self.grupos_nf:
                                self.grupos_nf[key] = {
                                    'linhas': [],
                                    'contribuintes_por_total': {k: [] for k in self.totais_acumulados.keys()}
                                }
                            self.grupos_nf[key]['contribuintes_por_total'].setdefault(total_field, []).append(numero_linha)

    def _only_digits_to_int(self, s: str) -> int:
        """Função IGUAL à comparação para extrair apenas dígitos"""
        digits = ''.join(ch for ch in s if ch.isdigit())
        return int(digits) if digits else 0

    def _registrar_linha_no_grupo(self, numero_linha: int):
        """Registra a linha atual no agrupamento da NF corrente, se houver contexto."""
        if self.current_fatura is None or self.current_nf is None:
            return
        key = (self.current_fatura, self.current_nf)
        if key not in self.grupos_nf:
            self.grupos_nf[key] = {
                'linhas': [],
                'contribuintes_por_total': {k: [] for k in self.totais_acumulados.keys()}
            }
        self.grupos_nf[key]['linhas'].append(numero_linha)

    def _capturar_declaracoes_header_00(self, numero_linha: int, linha_content: str):
        """Captura declarações relevantes do header 00 (ex.: quantidade de NF)."""
        try:
            possiveis = [
                'NFE00-QTD-NF', 'NFE00-TOT-NF', 'NFE00-QTD-REG', 'NFE00-QTD-NOTAS'
            ]
            for campo_nome in possiveis:
                campo = self.layout.get_campo(campo_nome)
                if campo:
                    valor_str = self._extrair_valor_campo_str(linha_content, campo_nome)
                    if valor_str:
                        self.declaracoes_header[campo_nome] = self._only_digits_to_int(valor_str)
        except Exception:
            pass

    def _extrair_valor_campo(self, linha: str, nome_campo: str) -> int:
        """Extrai valor numérico de um campo específico da linha"""
        try:
            # Encontrar o campo no layout
            campo = self.layout.get_campo(nome_campo)
            if not campo:
                return 0

            # Extrair valor da posição
            if len(linha) >= campo.posicao_fim:
                valor_str = linha[campo.posicao_inicio-1:campo.posicao_fim]
                # Converter para inteiro (removendo pontos decimais)
                digits = ''.join(ch for ch in valor_str if ch.isdigit())
                return int(digits) if digits else 0

        except Exception:
            pass

        return 0

    def _validar_totalizador_56(self, numero_linha: int, linha_content: str) -> List[ErroValidacao]:
        """Validação 4: Verificar se totais do registro 56 batem com valores acumulados"""
        erros = []

        for total_field in self.totals_map.keys():
            try:
                # Extrair valor declarado no registro 56
                valor_declarado = self._extrair_valor_campo(linha_content, total_field)
                valor_calculado = self.totais_acumulados[total_field]

                if valor_declarado != valor_calculado:
                    # Formatar valores para exibição
                    decl_fmt = f"{valor_declarado/100:.2f}".replace('.', ',')
                    calc_fmt = f"{valor_calculado/100:.2f}".replace('.', ',')
                    diff_fmt = f"{(valor_declarado - valor_calculado)/100:.2f}".replace('.', ',')

                    identificacao = None
                    if self.current_fatura is not None and self.current_nf is not None:
                        identificacao = f"Fatura {self.current_fatura} | NF {self.current_nf}"
                    # Tentar montar exemplo de cálculo para alguns itens contribuintes
                    exemplos_calc = self._montar_exemplos_calculo_total(total_field)
                    exemplos_texto = (" | Cálculo: " + exemplos_calc) if exemplos_calc else ""

                    erro = ErroValidacao(
                        linha=numero_linha,
                        campo=total_field,
                        valor_encontrado=decl_fmt,
                        erro_tipo=f"TOTAL_{total_field.split('-')[-1]}",  # Ex: TOTAL_ICMS
                        descricao=(
                            f"Total {total_field.split('-')[-1]} divergente: Declarado={decl_fmt} | "
                            f"Calculado={calc_fmt} | Diferença={diff_fmt}" + (f" | {identificacao}" if identificacao else "") + exemplos_texto
                        ),
                        valor_esperado=calc_fmt
                    )
                    erros.append(erro)

            except Exception as e:
                pass  # Ignorar erros de extração individual

        return erros

    def _montar_exemplos_calculo_total(self, total_field: str, max_itens: int = 3) -> str:
        """Gera uma string com exemplos de cálculo para o total informado, usando algumas linhas contribuintes.
        Para impostos com BC/ALIQ/VALOR, mostra "ln 000123: BC=a × ALIQ=b% → VAL=c".
        Para TOT-VLR-BC, mostra "ln 000123: BC=a". Limita a alguns itens e informa se há mais.
        """
        try:
            if self.current_fatura is None or self.current_nf is None:
                return ""
            key = (self.current_fatura, self.current_nf)
            grupo = self.grupos_nf.get(key)
            if not grupo:
                return ""
            contrib = grupo.get('contribuintes_por_total', {}).get(total_field, []) or []
            if not contrib:
                return ""

            # Mapear total_field para config de cálculo
            def config_por_total(tf: str):
                # Retorna tuplas (bc_field, aliq_field, valor_field, nome_imposto) ou None para apenas BC
                sufixo = tf.split('-')[-1]
                mapa = {
                    'PIS': '38',
                    'COFINS': '40',
                    'FUST': '42',
                    'FUNTEL': '44',
                    'ICM00': '22',
                    'ICMS': '22',
                    'FCP': ('22', 'FCP'),  # adicional em 22
                    'BC': ('22', 'BC'),   # só base de cálculo
                }
                # Normalizar chaves prováveis
                if sufixo == 'ICMS':
                    tipo = '22'
                    cfg = self.calculation_validations.get(tipo)
                    return (cfg['bc_field'], cfg['aliq_field'], cfg['valor_field'], 'ICMS') if cfg else None
                if sufixo == 'FCP':
                    tipo = '22'
                    cfg = self.calculation_validations.get(tipo)
                    if cfg and cfg.get('validacoes_adicionais'):
                        add = cfg['validacoes_adicionais'][0]
                        return (add['bc_field'], add.get('aliq_field'), add['valor_field'], 'FCP')
                    return None
                if sufixo == 'BC':
                    tipo = '22'
                    cfg = self.calculation_validations.get(tipo)
                    if cfg:
                        return (cfg['bc_field'], None, cfg['bc_field'], 'BC')
                    return None
                # Demais: PIS/COFINS/FUST/FUNTEL
                tipo = mapa.get(sufixo)
                if not tipo:
                    return None
                cfg = self.calculation_validations.get(tipo)
                if cfg:
                    return (cfg['bc_field'], cfg.get('aliq_field'), cfg['valor_field'], cfg.get('nome_imposto', sufixo))
                return None

            cfg_tuple = config_por_total(total_field)
            exemplos: List[str] = []

            for ln in contrib[:max_itens]:
                try:
                    linha_str = self.linhas_conteudo.get(ln, '')
                    if not linha_str:
                        continue
                    # Se não houver config (ex.: BC puro), mostre apenas o campo fonte
                    if not cfg_tuple:
                        exemplos.append(f"ln {str(ln).zfill(6)}")
                        continue
                    bc_field, aliq_field, valor_field, nome_imp = cfg_tuple
                    # Obter valores dos campos
                    if bc_field:
                        bc_val_int = self._extrair_valor_campo(linha_str, bc_field)
                        bc_fmt = f"{bc_val_int/100:.2f}".replace('.', ',')
                    else:
                        bc_fmt = ""
                    if aliq_field:
                        aliq_val_int = self._extrair_valor_campo(linha_str, aliq_field)
                        aliq_fmt = f"{aliq_val_int/100:.2f}".replace('.', ',')
                    else:
                        aliq_fmt = None
                    valor_int = self._extrair_valor_campo(linha_str, valor_field)
                    valor_fmt = f"{valor_int/100:.2f}".replace('.', ',')

                    if nome_imp == 'BC' or not aliq_fmt:
                        exemplos.append(f"ln {str(ln).zfill(6)}: BC={bc_fmt}")
                    else:
                        exemplos.append(f"ln {str(ln).zfill(6)}: BC={bc_fmt} × ALIQ={aliq_fmt}% → VAL={valor_fmt}")
                except Exception:
                    # Pular linha problemática
                    continue

            if not exemplos:
                return ""

            resto = len(contrib) - len(exemplos)
            sufixo_rest = f" (+{resto} itens)" if resto > 0 else ""
            return "; ".join(exemplos) + sufixo_rest
        except Exception:
            return ""

    def _validar_calculos_linha(self, numero_linha: int, tipo_registro: str, linha_content: str) -> List[ErroValidacao]:
        """Validação de cálculos individuais IGUAL à comparação estrutural"""
        erros = []

        if tipo_registro not in self.calculation_validations:
            return erros

        config = self.calculation_validations[tipo_registro]

        # Extrair NUM-NF da linha (posições 3-15) como na comparação
        num_nf = ''
        if linha_content and len(linha_content) >= 15:
            num_nf = linha_content[2:15].strip().lstrip('0') or '0'

        def _validar_calculo_especifico(config_calc):
            # Extrair valores dos campos usando mesma lógica da comparação
            bc_str = self._extrair_valor_campo_str(linha_content, config_calc['bc_field'])
            aliq_str = self._extrair_valor_campo_str(linha_content, config_calc['aliq_field'])
            valor_str = self._extrair_valor_campo_str(linha_content, config_calc['valor_field'])

            # CASO ESPECIAL FCP: Se BC e Alíquota preenchidos mas valor vazio/zero, é ERRO!
            bc_val_temp = self._only_digits_to_int(bc_str) if bc_str else 0
            aliq_val_temp = self._only_digits_to_int(aliq_str) if aliq_str else 0
            valor_val_temp = self._only_digits_to_int(valor_str) if valor_str else 0

            # Se BC > 0 e Alíquota > 0 mas Valor = 0, só é erro se o esperado (2 casas) > 0
            if bc_val_temp > 0 and aliq_val_temp > 0 and valor_val_temp == 0:
                valor_calculado_esperado = (bc_val_temp * aliq_val_temp) // 10000
                if valor_calculado_esperado > 0:
                    # Identificação preferindo Fatura|NF quando disponível
                    if self.current_fatura is not None and self.current_nf is not None:
                        identificacao = f"Fatura {self.current_fatura} | NF {self.current_nf}"
                    elif num_nf:
                        identificacao = f"NUM-NF: {num_nf}"
                    else:
                        identificacao = f"Linha: {numero_linha}"
                    bc_fmt = f"{bc_val_temp/100:.2f}".replace('.', ',')
                    aliq_fmt = f"{aliq_val_temp/100:.2f}".replace('.', ',')
                    valor_calc_fmt = f"{valor_calculado_esperado/100:.2f}".replace('.', ',')

                    erro = ErroValidacao(
                        linha=numero_linha,
                        campo=config_calc['valor_field'],
                        valor_encontrado="0,00",
                        erro_tipo=f"VALOR_ZERADO_{config_calc['nome_imposto']}",
                        descricao=f"{config_calc['nome_imposto']} ({identificacao}): BC={bc_fmt} × Alíquota={aliq_fmt}% = Esperado={valor_calc_fmt} | Encontrado=0,00 (VALOR ZERADO INCORRETAMENTE)",
                        valor_esperado=valor_calc_fmt
                    )
                    erros.append(erro)
                return  # Se esperado for 0, não é erro; encerra validação deste imposto

            # Se algum campo estiver vazio, não validar
            if not bc_str or not aliq_str or not valor_str:
                return

            try:
                # Usar EXATAMENTE a mesma função de parsing da comparação
                def _parse_decimal_value(s: str) -> int:
                    """Converte valor decimal para inteiro com 2 casas decimais implícitas - IGUAL à comparação"""
                    def _only_digits_to_int(s):
                        digits = ''.join(ch for ch in s if ch.isdigit())
                        return int(digits) if digits else 0

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

                # EXATAMENTE o mesmo cálculo da comparação: BC × Alíquota / 10000
                valor_calculado = (bc_val * aliq_val) // 10000

                # Só adicionar erros se houver divergência
                if valor_declarado != valor_calculado:
                    # Formatar valores igual à comparação
                    bc_fmt = f"{bc_val/100:.2f}".replace('.', ',')
                    aliq_fmt = f"{aliq_val/100:.2f}".replace('.', ',')
                    valor_decl_fmt = f"{valor_declarado/100:.2f}".replace('.', ',')
                    valor_calc_fmt = f"{valor_calculado/100:.2f}".replace('.', ',')
                    diferenca_fmt = f"{(valor_declarado - valor_calculado)/100:.2f}".replace('.', ',')

                    # Identificação preferindo Fatura|NF quando disponível
                    if self.current_fatura is not None and self.current_nf is not None:
                        identificacao = f"Fatura {self.current_fatura} | NF {self.current_nf}"
                    elif num_nf:
                        identificacao = f"NUM-NF: {num_nf}"
                    else:
                        identificacao = f"Linha: {numero_linha}"
                    descricao = f"{config_calc['nome_imposto']} ({identificacao}): BC={bc_fmt} × Alíquota={aliq_fmt}% = Calculado={valor_calc_fmt} | Declarado={valor_decl_fmt} | Diferença={diferenca_fmt}"

                    erro = ErroValidacao(
                        linha=numero_linha,
                        campo=config_calc['valor_field'],
                        valor_encontrado=valor_decl_fmt,
                        erro_tipo=f"CALCULO_ERRO_{config_calc['nome_imposto']}",
                        descricao=descricao,
                        valor_esperado=valor_calc_fmt
                    )
                    erros.append(erro)

            except Exception:
                # Se houver erro na validação, não adicionar erro
                pass

        # Validar cálculo principal
        _validar_calculo_especifico(config)

        # Validar cálculos adicionais (para registro 22: FCP)
        if 'validacoes_adicionais' in config:
            for validacao_adicional in config['validacoes_adicionais']:
                _validar_calculo_especifico(validacao_adicional)

        return erros

    def _extrair_valor_campo_str(self, linha: str, nome_campo: str) -> str:
        """Extrai valor string de um campo específico da linha"""
        try:
            # Encontrar o campo no layout
            campo = self.layout.get_campo(nome_campo)
            if not campo:
                return ''

            # Extrair valor da posição
            if len(linha) >= campo.posicao_fim:
                valor_str = linha[campo.posicao_inicio-1:campo.posicao_fim]
                return valor_str.strip()

        except Exception:
            pass

        return ''

    def _validar_trailer_99(self, numero_linha: int, linha_content: str) -> List[ErroValidacao]:
        """Validação 5: Verificar trailer (registro 99) - quantidade de notas fiscais"""
        erros = []

        try:
            # Quantidade real de notas fiscais encontrada (igual SEFAZ: total registros 01)
            quantidade_real = self.total_registros_01

            # Procurar campo de quantidade no trailer 99
            # Campo correto: NFE99-QTDE-DOC-NFCOM (quantidade de NFCOMs no arquivo)
            campos_trailer_possiveis = [
                'NFE99-QTDE-DOC-NFCOM'  # Campo oficial do layout NFCOM
            ]

            quantidade_declarada = None
            campo_encontrado = None

            # Tentar encontrar o campo de quantidade no trailer
            for campo_nome in campos_trailer_possiveis:
                campo = self.layout.get_campo(campo_nome)
                if campo:
                    valor_str = self._extrair_valor_campo_str(linha_content, campo_nome)
                    if valor_str:
                        quantidade_declarada = self._only_digits_to_int(valor_str)
                        campo_encontrado = campo_nome
                        break

            # Se encontrou campo de quantidade, validar
            if campo_encontrado and quantidade_declarada is not None:
                if quantidade_declarada != quantidade_real:
                    erro = ErroValidacao(
                        linha=numero_linha,
                        campo=campo_encontrado,
                        valor_encontrado=str(quantidade_declarada),
                        erro_tipo="TRAILER_QTD_NF",
                        descricao=f"Quantidade de notas fiscais no trailer ({quantidade_declarada}) difere da quantidade real encontrada ({quantidade_real})",
                        valor_esperado=str(quantidade_real)
                    )
                    erros.append(erro)
            else:
                # Se não encontrou campo de quantidade no layout, criar aviso informativo
                print(f"[WARN] AVISO: Não foi encontrado campo de quantidade de NF no trailer 99 do layout")
                print(f"    Campos procurados: {campos_trailer_possiveis}")
                print(f"    Quantidade real de NF encontrada: {quantidade_real}")

        except Exception as e:
            # Em caso de erro, criar erro de validação
            erro = ErroValidacao(
                linha=numero_linha,
                campo="NFE99-TRAILER",
                valor_encontrado="Erro de parsing",
                erro_tipo="ERRO_TRAILER",
                descricao=f"Erro ao validar trailer: {str(e)}",
                valor_esperado="Trailer válido"
            )
            erros.append(erro)

        return erros

    def _gerar_estatisticas_faturas(self) -> Dict:
        """Gerar estatísticas sobre faturas e notas fiscais"""

        # DEBUG: Verificar qual contador está sendo usado
        total_registros_debug = sum(1 for linha_tipo in self.registros_por_linha.values() if linha_tipo == '01')

        print(f"[DEBUG] total_registros_01: {self.total_registros_01}")
        print(f"[DEBUG] total_registros_debug: {total_registros_debug}")
        print(f"[DEBUG] combinacoes_fatura_nf: {len(self.combinacoes_fatura_nf)}")

        # Usar sempre o contador igual SEFAZ (por linha processada = registros 01)
        total_nfcoms = self.total_registros_01  # Cada registro 01 = 1 NFCOM processada
        print(f"[DEBUG] Finalizando estatísticas: total_nfcoms={total_nfcoms}")

        stats = {
            'total_faturas': len(self.notas_fiscais_por_fatura),
            'total_notas_fiscais': total_nfcoms,  # Garantir que seja o valor correto
            'total_combinacoes_unicas': len(self.combinacoes_fatura_nf),
            'total_duplicatas': len(self.duplicatas_fatura_nf),
            'faturas_detalhes': {},
            'duplicatas_detalhes': self.duplicatas_fatura_nf
        }

        for fatura, notas in self.notas_fiscais_por_fatura.items():
            stats['faturas_detalhes'][fatura] = {
                'quantidade_notas': len(notas),
                'notas_fiscais': list(set(notas))  # Remove duplicatas
            }

        return stats

    def _validar_estrutura_nf(self, numero_linha: int, tipo_registro: str) -> List[ErroValidacao]:
        """Regras estruturais por NF:
        - Não permitir tipos repetidos consecutivos, exceto o fluxo de item (20 ... impostos ... [20/36]).
        - Um item (20) com impostos deve ter a sequência 22, 38, 40, 42, 44 (ordem exigida) antes de um novo 20 ou 36.
        - Item financeiro (20 seguido de 36) não pode ter impostos entre 20 e 36.
        - Fora do bloco do item, tipos (exceto os do bloco) não podem repetir consecutivamente.
        """
        erros: List[ErroValidacao] = []

        # Só aplica dentro de uma NF aberta
        if self.current_fatura is None or self.current_nf is None:
            return erros

        # Atualizar contador de tipo na NF
        prev_count = self.contador_tipos_nf.get(tipo_registro, 0)
        self.contador_tipos_nf[tipo_registro] += 1

        # Sequência esperada de impostos para item não financeiro
        impostos_ordem = ['22', '38', '40', '42', '44']

        # Abertura de item
        if tipo_registro == '20':
            # Fechar item anterior e validar pendências
            if self.item_aberto is not None:
                # Se item anterior não foi financeiro (sem 36) e não teve todos impostos na ordem
                taxes_seen = self.item_aberto.get('taxes_seen', [])
                tem_36 = self.item_aberto.get('tem_36', False)
                if not tem_36 and any(t not in taxes_seen for t in impostos_ordem):
                    faltantes = [t for t in impostos_ordem if t not in taxes_seen]
                    erros.append(ErroValidacao(
                        linha=numero_linha,
                        campo='NFE20-ITEM',
                        valor_encontrado='|'.join(taxes_seen),
                        erro_tipo='ESTRUTURA_ITEM_IMPOSTOS_INCOMPLETOS',
                        descricao=(f"Fatura {self.current_fatura} | NF {self.current_nf}: Item anterior sem todos impostos: faltam {', '.join(faltantes)}"),
                        valor_esperado=' -> '.join(impostos_ordem)
                    ))
            # Abrir novo item
            self.item_aberto = {'linha_20': numero_linha, 'tem_36': False, 'taxes_seen': []}
            return erros

        # Dentro de um item aberto
        if self.item_aberto is not None:
            taxes_seen: List[str] = self.item_aberto.get('taxes_seen', [])
            tem_36: bool = self.item_aberto.get('tem_36', False)

            # Chegada de 36: marca como financeiro (sem impostos)
            if tipo_registro == '36':
                # Se já houve algum imposto antes de 36, é erro (financeiro não tem impostos)
                if taxes_seen:
                    erros.append(ErroValidacao(
                        linha=numero_linha,
                        campo='NFE36-ITEM-FINANCEIRO',
                        valor_encontrado='com-impostos',
                        erro_tipo='ESTRUTURA_ITEM_FINANCEIRO_COM_IMPOSTO',
                        descricao=(f"Fatura {self.current_fatura} | NF {self.current_nf}: Item financeiro (20->36) não pode ter impostos (encontrado: {', '.join(taxes_seen)})"),
                        valor_esperado='Sem impostos entre 20 e 36'
                    ))
                self.item_aberto['tem_36'] = True
                # Item será fechado quando aparecer novo 20 ou outros blocos
                return erros

            # impostos esperados em ordem
            if tipo_registro in impostos_ordem:
                # NOTA: Quando há múltiplos itens na mesma NF, os impostos aparecem repetidos
                # Exemplo: Item1 -> 22,38,40,42,44 -> Item2 -> 22,38,40,42,44
                # Por isso, NÃO validamos ordem estrita nem repetição consecutiva aqui
                # Apenas registramos que o imposto foi visto para este item
                taxes_seen.append(tipo_registro)
                return erros

            # Qualquer outro tipo aparecendo com item aberto fecha e valida o item atual
            # Fechar e validar se não-financeiro: precisa ter todos impostos
            if not tem_36 and any(t not in taxes_seen for t in impostos_ordem):
                faltantes = [t for t in impostos_ordem if t not in taxes_seen]
                erros.append(ErroValidacao(
                    linha=numero_linha,
                    campo='NFE20-ITEM',
                    valor_encontrado='|'.join(taxes_seen),
                    erro_tipo='ESTRUTURA_ITEM_IMPOSTOS_INCOMPLETOS',
                    descricao=(f"Fatura {self.current_fatura} | NF {self.current_nf}: Item sem todos impostos: faltam {', '.join(faltantes)}"),
                    valor_esperado=' -> '.join(impostos_ordem)
                ))
            # Fechar item
            self.item_aberto = None

        # Regra geral: não permitir tipos repetidos consecutivamente dentro da NF, exceto para o fluxo de item tratado acima
        linha_anterior = numero_linha - 1
        if linha_anterior in self.registros_por_linha:
            tipo_anterior = self.registros_por_linha[linha_anterior]
            if tipo_anterior == tipo_registro and tipo_registro not in ['00', '99']:
                # Já tratamos impostos repetidos acima; evite duplicar erro para esses tipos
                if tipo_registro not in ['22', '38', '40', '42', '44', '20', '36']:
                    erros.append(ErroValidacao(
                        linha=numero_linha,
                        campo=f"NFE{tipo_registro}-TP-REG",
                        valor_encontrado=tipo_registro,
                        erro_tipo='ESTRUTURA_REGISTRO_REPETIDO',
                        descricao=(f"Fatura {self.current_fatura} | NF {self.current_nf}: Tipo {tipo_registro} repetido consecutivamente"),
                        valor_esperado='Tipos diferentes em sequência'
                    ))

        return erros