from dataclasses import dataclass
from typing import List, Optional, Any
from enum import Enum


class TipoCampo(Enum):
    TEXTO = "TEXTO"
    NUMERO = "NUMERO"
    DATA = "DATA"
    DECIMAL = "DECIMAL"


@dataclass
class CampoLayout:
    """Representa um campo do layout"""
    nome: str
    posicao_inicio: int
    tamanho: int
    tipo: TipoCampo
    obrigatorio: bool
    formato: Optional[str] = None
    posicao_fim: Optional[int] = None

    def __post_init__(self):
        """Calcula posição final baseada no início e tamanho"""
        if self.posicao_fim is None:
            self.posicao_fim = self.posicao_inicio + self.tamanho - 1


@dataclass
class ErroValidacao:
    """Representa um erro encontrado na validação"""
    linha: int
    campo: str
    valor_encontrado: str
    erro_tipo: str
    descricao: str
    valor_esperado: Optional[str] = None


@dataclass
class ResultadoValidacao:
    """Resultado completo da validação"""
    total_linhas: int
    linhas_validas: int
    linhas_com_erro: int
    erros: List[ErroValidacao]
    taxa_sucesso: float

    def __post_init__(self):
        """Calcula taxa de sucesso"""
        if self.total_linhas > 0:
            self.taxa_sucesso = (self.linhas_validas / self.total_linhas) * 100
        else:
            self.taxa_sucesso = 0.0


@dataclass
class Layout:
    """Representa o layout completo"""
    nome: str
    campos: List[CampoLayout]
    tamanho_linha: int

    def get_campo(self, nome: str) -> Optional[CampoLayout]:
        """Busca um campo pelo nome"""
        for campo in self.campos:
            if campo.nome == nome:
                return campo
        return None