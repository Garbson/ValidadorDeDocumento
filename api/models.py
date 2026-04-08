from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class TipoCampoAPI(str, Enum):
    TEXTO = "TEXTO"
    NUMERO = "NUMERO"
    DATA = "DATA"
    DECIMAL = "DECIMAL"


class CampoLayoutResponse(BaseModel):
    nome: str
    posicao_inicio: int
    posicao_fim: int
    tamanho: int
    tipo: str
    obrigatorio: bool
    formato: Optional[str] = None


class LayoutResponse(BaseModel):
    nome: str
    campos: List[CampoLayoutResponse]
    tamanho_linha: int


class ErroValidacaoResponse(BaseModel):
    linha: int
    campo: str
    valor_encontrado: str
    erro_tipo: str
    descricao: str
    valor_esperado: Optional[str] = None


class ResultadoValidacaoResponse(BaseModel):
    total_linhas: int
    linhas_validas: int
    linhas_com_erro: int
    erros: List[ErroValidacaoResponse]
    taxa_sucesso: float


class TotaisCalculadosResponse(BaseModel):
    """Totais acumulados por campo totalizador no registro 56."""
    valores: Dict[str, int]


class DuplicataNFResponse(BaseModel):
    linha: int
    fatura: str
    nf: str
    combinacao: str

class EstatisticasFaturasResponse(BaseModel):
    total_faturas: int
    total_notas_fiscais: int  # Agora igual à SEFAZ (total de registros 01)
    total_combinacoes_unicas: int = 0  # Combinações únicas (fatura, nf)
    total_duplicatas: int = 0  # Número de duplicatas encontradas
    faturas_detalhes: Dict[str, Any]
    duplicatas_detalhes: List[DuplicataNFResponse] = []  # Lista das duplicatas
    # Novas métricas por NF
    total_nfs_validas: int
    total_nfs_com_erro: int
    taxa_sucesso_nf: float


class ResultadoCalculosResponse(BaseModel):
    """Resultado específico para validação de cálculos/totalizadores."""
    resultado_basico: ResultadoValidacaoResponse
    totais: Optional[TotaisCalculadosResponse] = None
    estatisticas_faturas: Optional[EstatisticasFaturasResponse] = None
    linhas_completas_com_erro: Dict[int, str] = {}
    grupos_por_nf: Optional[Dict[str, Any]] = None  # chave "fatura|nf" -> {linhas:[], contribuintes_por_total:{campo_total:[linhas...]}}
    layout: LayoutResponse


class ValidarCalculosRequest(BaseModel):
    """Request para validação de cálculos: apenas arquivos, sem base."""
    # Mantido vazio pois usaremos UploadFile no endpoint, mas esta classe facilita documentação futura
    pass


class EstatisticasResponse(BaseModel):
    total_linhas: int
    linhas_validas: int
    linhas_com_erro: int
    taxa_sucesso: float
    total_erros: int
    tipos_erro: Dict[str, int]
    campos_com_erro: Dict[str, int]


class RegistroPreviewResponse(BaseModel):
    """Preview de um registro parseado com seus campos"""
    linha: int
    tipo_registro: str
    campos: Dict[str, str]  # nome_campo -> valor


class ValidacaoCompleta(BaseModel):
    layout: LayoutResponse
    resultado: ResultadoValidacaoResponse
    estatisticas: EstatisticasResponse
    timestamp: str
    dados_relatorio: Optional[Dict] = None  # Dados do relatório para localStorage
    preview_registros: Optional[List[RegistroPreviewResponse]] = None  # Preview dos primeiros registros
    tipos_registro_encontrados: Optional[List[str]] = None  # Tipos encontrados no arquivo


class StatusResponse(BaseModel):
    status: str
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: str


class DiferencaEstruturalCampoResponse(BaseModel):
    nome_campo: str
    posicao_inicio: int
    posicao_fim: int
    valor_base: str
    valor_validado: str
    tipo_diferenca: str
    descricao: str


class DiferencaEstruturalLinhaResponse(BaseModel):
    numero_linha: int
    tipo_registro: str
    arquivo_base_linha: str
    arquivo_validado_linha: str
    diferencas_campos: List[DiferencaEstruturalCampoResponse]
    total_diferencas: int


class FaturaComparadaResponse(BaseModel):
    conta_cliente: str
    cps_fatura: str
    todas_linhas: List[DiferencaEstruturalLinhaResponse]
    diferencas_por_linha: List[DiferencaEstruturalLinhaResponse]
    total_linhas: int
    linhas_com_diferencas: int
    linhas_identicas: int


class ResultadoComparacaoEstruturalResponse(BaseModel):
    total_linhas_comparadas: int
    linhas_com_diferencas: int
    linhas_identicas: int
    diferencas_por_linha: List[DiferencaEstruturalLinhaResponse]
    todas_linhas: Optional[List[DiferencaEstruturalLinhaResponse]] = None
    taxa_identidade: float
    contas_nao_encontradas: List[str] = []
    faturas_comparadas: List[FaturaComparadaResponse] = []


class ComparacaoEstruturalCompleta(BaseModel):
    layout: LayoutResponse
    resultado_comparacao: ResultadoComparacaoEstruturalResponse
    relatorio_texto: str
    timestamp: str
    dados_comparacao: Optional[Dict] = None  # Dados para localStorage


class ServicoFaturaResponse(BaseModel):
    sigla: str           # Ex: "INN", "VPE"
    descricao: str       # Ex: "INTERNET", "VOIP"
    valor: Optional[str] = None  # Ex: "R$ 1.234,56"


class RetencaoInfoResponse(BaseModel):
    percentual: str  # Ex: "9,45%", "4,8%", "4,65%"
    valor: str       # Ex: "R$ 9.210,44"
    tipo: str = ""   # "CFE LEI", "RBF", "PIS/CSSL/COFINS"
    detalhes: Optional[Dict] = None  # Para PIS/CSSL/COFINS: breakdown individual
    texto_original: str = ""


class FaturaCenarioResponse(BaseModel):
    conta_cliente: str
    cps_fatura: str
    cenarios: List[str]
    tipos_registro: List[str]
    linha_inicio: int
    total_linhas: int
    debito_automatico: bool
    isencao: bool = False
    aliquota_icms: Optional[str] = None
    valor_isentos: Optional[str] = None
    retencao: Optional[RetencaoInfoResponse] = None
    mensagens: Optional[List[str]] = None
    quantidade_sites: int = 0
    servicos: Optional[List[ServicoFaturaResponse]] = None


class CenarioIdentificadoResponse(BaseModel):
    cenarios_encontrados: List[str]
    contagem_por_cenario: Dict[str, int]
    faturas: List[FaturaCenarioResponse]
    total_faturas: int


class CampoLayoutPrintCenterResponse(BaseModel):
    """Campo do layout PrintCenter com código TT.NN"""
    codigo: str  # Ex: "01.02"
    nome: str  # Ex: "Código de Cliente"
    posicao_de: int
    posicao_ate: int
    tamanho: int
    tipo: str  # TEXTO, NUMERO, DECIMAL
    picture: str  # Ex: "9(15)"
    tipo_registro: str  # Ex: "01"


class LayoutPrintCenterResponse(BaseModel):
    """Lista de campos do layout PrintCenter"""
    campos: List[CampoLayoutPrintCenterResponse]
    tipos_registro: List[str]  # Lista de tipos de registro disponíveis
    total_campos: int