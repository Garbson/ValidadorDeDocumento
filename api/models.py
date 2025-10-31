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
    totais_acumulados: Optional[Dict[str, int]] = None
    componentes_totais: Optional[List[Dict[str, Any]]] = None


class ResultadoComparacaoEstruturalResponse(BaseModel):
    total_linhas_comparadas: int
    linhas_com_diferencas: int
    linhas_identicas: int
    diferencas_por_linha: List[DiferencaEstruturalLinhaResponse]
    taxa_identidade: float


class ComparacaoEstruturalCompleta(BaseModel):
    layout: LayoutResponse
    resultado_comparacao: ResultadoComparacaoEstruturalResponse
    relatorio_texto: str
    timestamp: str
    dados_comparacao: Optional[Dict] = None  # Dados para localStorage