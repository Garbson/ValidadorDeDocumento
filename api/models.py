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


class ValidacaoCompleta(BaseModel):
    layout: LayoutResponse
    resultado: ResultadoValidacaoResponse
    estatisticas: EstatisticasResponse
    timestamp: str


class StatusResponse(BaseModel):
    status: str
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: str