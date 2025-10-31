from dataclasses import dataclass
from typing import List, Optional, Any, Dict
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
class DiferencaEstruturalCampo:
    """Representa uma diferença encontrada em um campo específico"""
    nome_campo: str
    posicao_inicio: int
    posicao_fim: int
    valor_base: str
    valor_validado: str
    tipo_diferenca: str  # 'TAMANHO', 'FORMATO', 'CAMPO_VAZIO', 'CONTEUDO'
    descricao: str
    sequencia_campo: int = 0  # Sequência do campo (1, 2, 3, etc.)


@dataclass
class DiferencaEstruturalLinha:
    """Representa as diferenças encontradas em uma linha"""
    numero_linha: int
    tipo_registro: str
    arquivo_base_linha: str
    arquivo_validado_linha: str
    diferencas_campos: List[DiferencaEstruturalCampo]
    total_diferencas: int
    linha_numeracao: str = ""  # Linha com numeração dos campos
    # Totais calculados por fatura (somatórios) e componentes que geraram cada total
    totais_acumulados: Optional[Dict[str, int]] = None  # ex.: { 'NFE56-TOT-VLR-PIS': 1234, ... }
    componentes_totais: Optional[List[Dict[str, Any]]] = None  # lista de componentes somados


@dataclass
class ResultadoComparacaoEstrutural:
    """Resultado completo da comparação estrutural"""
    total_linhas_comparadas: int
    linhas_com_diferencas: int
    linhas_identicas: int
    diferencas_por_linha: List[DiferencaEstruturalLinha]
    taxa_identidade: float

    def __post_init__(self):
        """Calcula taxa de identidade"""
        if self.total_linhas_comparadas > 0:
            self.taxa_identidade = (self.linhas_identicas / self.total_linhas_comparadas) * 100
        else:
            self.taxa_identidade = 0.0


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