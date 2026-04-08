"""
Módulo para identificação de cenários em faturas.

Identifica cenários como ICMS, ISS, Cobilling, Débito Automático, Retenção, etc.
baseado nos tipos de registro presentes em cada fatura do arquivo TXT.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional


# Mapeamento de tipos de registro para cenários
CENARIO_MAP = {
    '10': 'ICMS (Modelo 22)',
    '40': 'ICMS (Modelo 62)',
    '20': 'ISS',
    '15': 'Cobilling',
    '30': 'Recibo',
    '80': 'Recibo',
}

# Posição do flag de débito automático no registro tipo 01 (campo 01.17, pos 266)
FLAG_DEBITO_AUTO_POS = 265  # 0-indexed

# Posições do campo "Valor Isentos" nos registros fiscais (0-indexed)
# Registro 48 (Modelo 62): campo 48.11, posição 59-72
# Registro 12 (Modelo 22): campo 12.11, posição 59-72
ISENCAO_POS_DE = 58   # 0-indexed (pos 59 no layout)
ISENCAO_POS_ATE = 72  # 0-indexed exclusive

# Posições do campo "Alíquota ICMS" nos registros fiscais (0-indexed)
# Registro 48 (Modelo 62): campo 48.07, posição 38-42 (formato 9(03)V99)
# Registro 12 (Modelo 22): campo 12.07, posição 38-42 (formato 9(03)V99)
ALIQUOTA_POS_DE = 37   # 0-indexed (pos 38 no layout)
ALIQUOTA_POS_ATE = 42  # 0-indexed exclusive

# Regexes para extrair retenção do registro 88
# Tipo 1: "RETENCAO CFE LEI 9430/960 -  9,45%  R$    9.210,44"
RETENCAO_LEI_REGEX = re.compile(
    r'RETENCAO\s+CFE\s+LEI\s+[\d/]+\s*-\s*([\d,]+)%\s+R\$\s*([\d.,]+)',
    re.IGNORECASE
)
# Tipo 2: "Retencao 4,8% - conf. RBF n.1234/2012 R$      106,36"
RETENCAO_RBF_REGEX = re.compile(
    r'Retencao\s+([\d,]+)%\s*-\s*conf\.\s*RBF\s+.*?R\$\s*([\d.,]+)',
    re.IGNORECASE
)
# Tipo 3: "Retencao conf. Art30 Lei 10.833/2003: PIS(0,65%) R$ 170,48  CSSL(1,00%) R$ 262,28 COFINS(3,00%) R$ 786,83"
RETENCAO_PCC_REGEX = re.compile(
    r'Retencao\s+conf\.\s*Art\d+\s+Lei\s+[\d./]+:\s*PIS\(([\d,]+)%\)\s*R\$\s*([\d.,]+)\s+CSSL\(([\d,]+)%\)\s*R\$\s*([\d.,]+)\s+COFINS\(([\d,]+)%\)\s*R\$\s*([\d.,]+)',
    re.IGNORECASE
)


def parse_retencao(linha: str) -> 'Optional[RetencaoInfo]':
    """Tenta extrair informações de retenção de uma linha de registro 88."""
    msg_texto = linha[2:].strip()

    # Tipo 1: Retenção CFE LEI (9,45%)
    match = RETENCAO_LEI_REGEX.search(linha)
    if match:
        return RetencaoInfo(
            percentual=match.group(1) + '%',
            valor='R$ ' + match.group(2),
            tipo='CFE LEI',
            detalhes=None,
            texto_original=msg_texto,
        )

    # Tipo 2: Retenção RBF (4,8%)
    match = RETENCAO_RBF_REGEX.search(linha)
    if match:
        return RetencaoInfo(
            percentual=match.group(1) + '%',
            valor='R$ ' + match.group(2),
            tipo='RBF',
            detalhes=None,
            texto_original=msg_texto,
        )

    # Tipo 3: Retenção PIS/CSSL/COFINS (4,65%)
    match = RETENCAO_PCC_REGEX.search(linha)
    if match:
        pis_pct, pis_val = match.group(1), match.group(2)
        cssl_pct, cssl_val = match.group(3), match.group(4)
        cofins_pct, cofins_val = match.group(5), match.group(6)

        # Calcular percentual total (ex: 0,65 + 1,00 + 3,00 = 4,65)
        try:
            total_pct = (
                float(pis_pct.replace(',', '.')) +
                float(cssl_pct.replace(',', '.')) +
                float(cofins_pct.replace(',', '.'))
            )
            total_pct_str = str(total_pct).replace('.', ',') + '%'
        except ValueError:
            total_pct_str = f'{pis_pct}+{cssl_pct}+{cofins_pct}%'

        # Calcular valor total
        try:
            total_val = (
                float(pis_val.replace('.', '').replace(',', '.')) +
                float(cssl_val.replace('.', '').replace(',', '.')) +
                float(cofins_val.replace('.', '').replace(',', '.'))
            )
            total_val_str = f'R$ {total_val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        except ValueError:
            total_val_str = f'R$ {pis_val} + {cssl_val} + {cofins_val}'

        return RetencaoInfo(
            percentual=total_pct_str,
            valor=total_val_str,
            tipo='PIS/CSSL/COFINS',
            detalhes={
                'PIS': {'percentual': pis_pct + '%', 'valor': 'R$ ' + pis_val},
                'CSSL': {'percentual': cssl_pct + '%', 'valor': 'R$ ' + cssl_val},
                'COFINS': {'percentual': cofins_pct + '%', 'valor': 'R$ ' + cofins_val},
            },
            texto_original=msg_texto,
        )

    return None


@dataclass
class RetencaoInfo:
    percentual: str      # Ex: "9,45%", "4,8%", "4,65%"
    valor: str           # Ex: "R$ 9.210,44"
    tipo: str            # "CFE LEI", "RBF", "PIS/CSSL/COFINS"
    detalhes: Optional[Dict] = None  # Para PIS/CSSL/COFINS: breakdown individual
    texto_original: str = ""  # Linha completa do registro 88


@dataclass
class ServicoFatura:
    sigla: str               # Ex: "INN", "VPE", "SCE"
    descricao: str           # Ex: "INTERNET", "VOIP", "SERVICO COMUNICACAO"
    valor: Optional[str] = None  # Ex: "R$ 1.234,56" (do registro 02)


@dataclass
class FaturaCenario:
    conta_cliente: str
    cps_fatura: str
    cenarios: List[str]
    tipos_registro: List[str]
    linha_inicio: int
    total_linhas: int
    debito_automatico: bool = False
    isencao: bool = False
    aliquota_icms: Optional[str] = None       # Ex: "18,00%", "0,00%"
    valor_isentos: Optional[str] = None       # Ex: "R$ 4.082,60"
    retencao: Optional[RetencaoInfo] = None
    mensagens: List[str] = field(default_factory=list)
    quantidade_sites: int = 0                 # Qtd de sites (faturas) do mesmo cliente
    servicos: List[ServicoFatura] = field(default_factory=list)  # Serviços cobrados


@dataclass
class ResultadoCenarios:
    cenarios_encontrados: List[str]
    contagem_por_cenario: Dict[str, int]
    faturas: List[FaturaCenario]
    total_faturas: int = 0


def identificar_cenarios(file_path: str) -> ResultadoCenarios:
    """
    Lê um arquivo TXT e identifica os cenários de cada fatura.

    Agrupa linhas por fatura (tipo 01 inicia nova fatura) e identifica
    cenários pela presença de tipos de registro específicos.
    """
    faturas: List[FaturaCenario] = []

    # Estado da fatura atual
    conta_atual = ""
    cps_atual = ""
    tipos_atual: Set[str] = set()
    linha_inicio_atual = 0
    total_linhas_atual = 0
    debito_auto_atual = False
    isencao_atual = False
    aliquota_icms_atual: Optional[str] = None
    valor_isentos_atual: Optional[str] = None
    retencao_atual: Optional[RetencaoInfo] = None
    mensagens_atual: List[str] = []
    servicos_atual: Dict[str, ServicoFatura] = {}  # sigla -> ServicoFatura

    def formatar_valor_brl(valor_raw: str) -> str:
        """Formata valor numérico bruto (sem vírgula, 2 decimais implícitas) para R$."""
        try:
            valor_num = int(valor_raw) / 100
            formatted = f"{valor_num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"R$ {formatted}"
        except (ValueError, TypeError):
            return "R$ 0,00"

    def formatar_aliquota(aliq_raw: str) -> str:
        """Formata alíquota bruta (3 dígitos + 2 decimais implícitas) para percentual."""
        try:
            aliq_num = int(aliq_raw) / 100
            return f"{aliq_num:.2f}".replace('.', ',') + '%'
        except (ValueError, TypeError):
            return "0,00%"

    def finalizar_fatura():
        """Salva a fatura atual na lista."""
        nonlocal retencao_atual, mensagens_atual, isencao_atual
        nonlocal aliquota_icms_atual, valor_isentos_atual, servicos_atual
        if not conta_atual and not cps_atual:
            return

        cenarios = []
        for tipo_reg, cenario in CENARIO_MAP.items():
            if tipo_reg in tipos_atual:
                # Evitar duplicar "Recibo" (tipos 30 e 80)
                if cenario not in cenarios:
                    cenarios.append(cenario)

        # Dupla Convivência: quando tem Modelo 22 (reg 10) E Modelo 62 (reg 40)
        if '10' in tipos_atual and '40' in tipos_atual:
            cenarios.append('Dupla Convivência')

        if debito_auto_atual:
            cenarios.append('Débito Automático')

        if isencao_atual:
            cenarios.append('Isenção')

        if retencao_atual:
            cenarios.append(f'Retenção {retencao_atual.percentual}')

        faturas.append(FaturaCenario(
            conta_cliente=conta_atual,
            cps_fatura=cps_atual,
            cenarios=cenarios,
            tipos_registro=sorted(tipos_atual),
            linha_inicio=linha_inicio_atual,
            total_linhas=total_linhas_atual,
            debito_automatico=debito_auto_atual,
            isencao=isencao_atual,
            aliquota_icms=aliquota_icms_atual,
            valor_isentos=valor_isentos_atual,
            retencao=retencao_atual,
            mensagens=mensagens_atual,
            servicos=list(servicos_atual.values()),
        ))
        retencao_atual = None
        mensagens_atual = []
        isencao_atual = False
        aliquota_icms_atual = None
        valor_isentos_atual = None
        servicos_atual = {}

    # Ler arquivo linha por linha
    encodings = ['utf-8', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for num_linha, linha in enumerate(f, 1):
                    linha = linha.rstrip('\n').rstrip('\r')
                    if len(linha) < 2:
                        continue

                    tipo_registro = linha[:2].strip()

                    if tipo_registro == '01':
                        # Finalizar fatura anterior
                        finalizar_fatura()

                        # Iniciar nova fatura
                        conta_atual = linha[2:17].strip() if len(linha) >= 17 else ""
                        cps_atual = linha[17:30].strip() if len(linha) >= 30 else ""
                        tipos_atual = {'01'}
                        linha_inicio_atual = num_linha
                        total_linhas_atual = 1
                        mensagens_atual = []
                        retencao_atual = None
                        isencao_atual = False
                        aliquota_icms_atual = None
                        valor_isentos_atual = None
                        servicos_atual = {}

                        # Flag débito automático (pos 266, 0-indexed = 265)
                        debito_auto_atual = (
                            len(linha) > FLAG_DEBITO_AUTO_POS and
                            linha[FLAG_DEBITO_AUTO_POS].upper() == 'S'
                        )
                    elif tipo_registro in ('00', '99'):
                        # Header e trailer não pertencem a nenhuma fatura
                        continue
                    else:
                        tipos_atual.add(tipo_registro)
                        total_linhas_atual += 1

                        # Extrair dados fiscais dos registros 48 (M62) ou 12 (M22)
                        if tipo_registro in ('48', '12'):
                            # Alíquota ICMS (campo 48.07/12.07, pos 38-42)
                            if len(linha) >= ALIQUOTA_POS_ATE:
                                aliq_raw = linha[ALIQUOTA_POS_DE:ALIQUOTA_POS_ATE].strip()
                                if aliq_raw:
                                    aliquota_icms_atual = formatar_aliquota(aliq_raw)

                            # Valor Isentos (campo 48.11/12.11, pos 59-72)
                            if len(linha) >= ISENCAO_POS_ATE:
                                vi_raw = linha[ISENCAO_POS_DE:ISENCAO_POS_ATE].strip()
                                if vi_raw and not all(c in '0 ' for c in vi_raw):
                                    isencao_atual = True
                                    valor_isentos_atual = formatar_valor_brl(vi_raw)

                        # Extrair serviços do registro 02 (Resumo Serviços)
                        if tipo_registro == '02' and len(linha) >= 57:
                            sigla = linha[2:7].strip()   # pos 3-7 (0-indexed: 2-7)
                            descricao = linha[7:57].strip()  # pos 8-57 (0-indexed: 7-57)
                            valor_servico = None
                            if len(linha) >= 72:
                                val_raw = linha[58:72].strip()  # pos 59-72
                                if val_raw and not all(c in '0 ' for c in val_raw):
                                    valor_servico = formatar_valor_brl(val_raw)
                            if sigla and sigla not in servicos_atual:
                                servicos_atual[sigla] = ServicoFatura(
                                    sigla=sigla,
                                    descricao=descricao,
                                    valor=valor_servico,
                                )

                        # Capturar mensagens dos registros 85, 86, 87, 88
                        if tipo_registro in ('85', '86', '87', '88'):
                            msg_texto = linha[2:].strip()
                            if msg_texto:
                                mensagens_atual.append(msg_texto)

                            # Verificar retenção no registro 88
                            if tipo_registro == '88':
                                ret = parse_retencao(linha)
                                if ret:
                                    retencao_atual = ret
            break  # Encoding funcionou
        except UnicodeDecodeError:
            if encoding == encodings[-1]:
                raise
            continue

    # Finalizar última fatura
    finalizar_fatura()

    # Calcular quantidade de sites por cliente (faturas do mesmo conta_cliente)
    sites_por_cliente: Dict[str, int] = {}
    for fatura in faturas:
        cliente = fatura.conta_cliente
        sites_por_cliente[cliente] = sites_por_cliente.get(cliente, 0) + 1

    # Atribuir quantidade de sites a cada fatura
    for fatura in faturas:
        fatura.quantidade_sites = sites_por_cliente.get(fatura.conta_cliente, 1)

    # Calcular contagens
    contagem: Dict[str, int] = {}
    cenarios_set: Set[str] = set()
    for fatura in faturas:
        for cenario in fatura.cenarios:
            cenarios_set.add(cenario)
            contagem[cenario] = contagem.get(cenario, 0) + 1

    return ResultadoCenarios(
        cenarios_encontrados=sorted(cenarios_set),
        contagem_por_cenario=contagem,
        faturas=faturas,
        total_faturas=len(faturas),
    )


def buscar_faturas_por_campo(file_path: str, tipo_registro: str,
                              posicao_de: int, posicao_ate: int,
                              valor_busca: str) -> list:
    """
    Busca faturas onde um campo específico contém o valor informado.

    Args:
        file_path: Caminho do arquivo TXT
        tipo_registro: Tipo de registro do campo (ex: "01", "10", "20")
        posicao_de: Posição inicial do campo (1-indexed)
        posicao_ate: Posição final do campo (1-indexed)
        valor_busca: Valor a buscar (busca parcial, case-insensitive)

    Returns:
        Lista de dicts com info das faturas que correspondem
    """
    faturas_match = []
    valor_busca_lower = valor_busca.strip().lower()

    # Estado da fatura atual
    conta_atual = ""
    cps_atual = ""
    linha_inicio_atual = 0
    total_linhas_atual = 0
    match_encontrado = False
    valor_campo_encontrado = ""
    tipos_atual = set()
    debito_auto_atual = False
    isencao_atual = False
    aliquota_icms_atual: Optional[str] = None
    valor_isentos_atual: Optional[str] = None
    retencao_atual: Optional[RetencaoInfo] = None
    servicos_atual: Dict[str, ServicoFatura] = {}

    def formatar_valor_brl2(valor_raw: str) -> str:
        try:
            valor_num = int(valor_raw) / 100
            formatted = f"{valor_num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return f"R$ {formatted}"
        except (ValueError, TypeError):
            return "R$ 0,00"

    def formatar_aliquota2(aliq_raw: str) -> str:
        try:
            aliq_num = int(aliq_raw) / 100
            return f"{aliq_num:.2f}".replace('.', ',') + '%'
        except (ValueError, TypeError):
            return "0,00%"

    def finalizar_fatura():
        nonlocal match_encontrado, valor_campo_encontrado, retencao_atual, isencao_atual
        nonlocal aliquota_icms_atual, valor_isentos_atual, servicos_atual
        if not conta_atual and not cps_atual:
            return
        if match_encontrado:
            cenarios = []
            for tipo_reg, cenario in CENARIO_MAP.items():
                if tipo_reg in tipos_atual and cenario not in cenarios:
                    cenarios.append(cenario)
            if '10' in tipos_atual and '40' in tipos_atual:
                cenarios.append('Dupla Convivência')
            if debito_auto_atual:
                cenarios.append('Débito Automático')
            if isencao_atual:
                cenarios.append('Isenção')
            if retencao_atual:
                cenarios.append(f'Retenção {retencao_atual.percentual}')

            retencao_dict = None
            if retencao_atual:
                retencao_dict = {
                    'percentual': retencao_atual.percentual,
                    'valor': retencao_atual.valor,
                    'tipo': retencao_atual.tipo,
                    'detalhes': retencao_atual.detalhes,
                    'texto_original': retencao_atual.texto_original,
                }

            faturas_match.append({
                'conta_cliente': conta_atual,
                'cps_fatura': cps_atual,
                'valor_campo': valor_campo_encontrado.strip(),
                'cenarios': cenarios,
                'tipos_registro': sorted(tipos_atual),
                'linha_inicio': linha_inicio_atual,
                'total_linhas': total_linhas_atual,
                'debito_automatico': debito_auto_atual,
                'isencao': isencao_atual,
                'aliquota_icms': aliquota_icms_atual,
                'valor_isentos': valor_isentos_atual,
                'retencao': retencao_dict,
                'servicos': [
                    {'sigla': s.sigla, 'descricao': s.descricao, 'valor': s.valor}
                    for s in servicos_atual.values()
                ],
            })
        match_encontrado = False
        valor_campo_encontrado = ""
        retencao_atual = None
        isencao_atual = False
        aliquota_icms_atual = None
        valor_isentos_atual = None
        servicos_atual = {}

    encodings = ['utf-8', 'latin-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                for num_linha, linha in enumerate(f, 1):
                    linha = linha.rstrip('\n').rstrip('\r')
                    if len(linha) < 2:
                        continue

                    tipo_reg = linha[:2].strip()

                    if tipo_reg == '01':
                        finalizar_fatura()
                        conta_atual = linha[2:17].strip() if len(linha) >= 17 else ""
                        cps_atual = linha[17:30].strip() if len(linha) >= 30 else ""
                        tipos_atual = {'01'}
                        linha_inicio_atual = num_linha
                        total_linhas_atual = 1
                        match_encontrado = False
                        valor_campo_encontrado = ""
                        retencao_atual = None
                        isencao_atual = False
                        aliquota_icms_atual = None
                        valor_isentos_atual = None
                        servicos_atual = {}
                        debito_auto_atual = (
                            len(linha) > FLAG_DEBITO_AUTO_POS and
                            linha[FLAG_DEBITO_AUTO_POS].upper() == 'S'
                        )
                    elif tipo_reg in ('00', '99'):
                        continue
                    else:
                        tipos_atual.add(tipo_reg)
                        total_linhas_atual += 1

                        # Extrair dados fiscais dos registros 48 (M62) ou 12 (M22)
                        if tipo_reg in ('48', '12'):
                            if len(linha) >= ALIQUOTA_POS_ATE:
                                aliq_raw = linha[ALIQUOTA_POS_DE:ALIQUOTA_POS_ATE].strip()
                                if aliq_raw:
                                    aliquota_icms_atual = formatar_aliquota2(aliq_raw)
                            if len(linha) >= ISENCAO_POS_ATE:
                                vi_raw = linha[ISENCAO_POS_DE:ISENCAO_POS_ATE].strip()
                                if vi_raw and not all(c in '0 ' for c in vi_raw):
                                    isencao_atual = True
                                    valor_isentos_atual = formatar_valor_brl2(vi_raw)

                        # Extrair serviços do registro 02 (Resumo Serviços)
                        if tipo_reg == '02' and len(linha) >= 57:
                            sigla = linha[2:7].strip()
                            descricao = linha[7:57].strip()
                            valor_servico = None
                            if len(linha) >= 72:
                                val_raw = linha[58:72].strip()
                                if val_raw and not all(c in '0 ' for c in val_raw):
                                    valor_servico = formatar_valor_brl2(val_raw)
                            if sigla and sigla not in servicos_atual:
                                servicos_atual[sigla] = ServicoFatura(
                                    sigla=sigla,
                                    descricao=descricao,
                                    valor=valor_servico,
                                )

                        # Capturar retenção do registro 88
                        if tipo_reg == '88':
                            ret = parse_retencao(linha)
                            if ret:
                                retencao_atual = ret

                    # Verificar se este tipo de registro é o que buscamos
                    if tipo_reg == tipo_registro:
                        # Extrair valor do campo (posições 1-indexed)
                        if len(linha) >= posicao_ate:
                            valor_extraido = linha[posicao_de - 1:posicao_ate]
                            if valor_busca_lower in valor_extraido.lower():
                                match_encontrado = True
                                valor_campo_encontrado = valor_extraido
            break
        except UnicodeDecodeError:
            if encoding == encodings[-1]:
                raise
            continue

    finalizar_fatura()

    # Calcular quantidade de sites por cliente nos resultados da busca
    sites_por_cliente: Dict[str, int] = {}
    for f in faturas_match:
        cliente = f['conta_cliente']
        sites_por_cliente[cliente] = sites_por_cliente.get(cliente, 0) + 1
    for f in faturas_match:
        f['quantidade_sites'] = sites_por_cliente.get(f['conta_cliente'], 1)

    return faturas_match
