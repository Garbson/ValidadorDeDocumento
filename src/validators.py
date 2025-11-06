import re
from datetime import datetime
from typing import List, Optional, Any
from decimal import Decimal, InvalidOperation

try:
    from .models import CampoLayout, TipoCampo, ErroValidacao
except ImportError:
    from models import CampoLayout, TipoCampo, ErroValidacao


class ValidadorCampo:
    """Classe para validar valores de campos individuais"""

    @staticmethod
    def validar_obrigatorio(valor: str, campo: CampoLayout) -> Optional[str]:
        """Valida se campo obrigatório não está vazio"""
        if campo.obrigatorio and (not valor or valor.strip() == ''):
            return f"Campo obrigatório '{campo.nome}' está vazio"
        return None

    @staticmethod
    def validar_tamanho(valor: str, campo: CampoLayout) -> Optional[str]:
        """Valida o tamanho do campo"""
        if len(valor) != campo.tamanho:
            # Manter palavra-chave 'tamanho' para compatibilidade com testes
            return f"Tamanho do campo incorreto: encontrado {len(valor)} caracteres, esperado exatamente {campo.tamanho} caracteres"
        return None

    @staticmethod
    def validar_tipo_texto(valor: str, campo: CampoLayout) -> Optional[str]:
        """Valida campo tipo TEXTO"""
        # Para texto, qualquer caractere é válido
        return None

    @staticmethod
    def validar_tipo_numero(valor: str, campo: CampoLayout) -> Optional[str]:
        """Valida campo tipo NUMERO"""
        valor_limpo = valor.strip()
        if valor_limpo and not valor_limpo.isdigit():
            # Identificar caracteres inválidos
            caracteres_invalidos = [c for c in valor_limpo if not c.isdigit()]
            if caracteres_invalidos:
                chars_str = ', '.join(f"'{c}'" for c in set(caracteres_invalidos))
                # Incluir palavra 'números' para satisfazer expectativa dos testes
                return f"Contém caracteres não numéricos: {chars_str}. Apenas números/dígitos (0-9) são permitidos"
            else:
                return f"Deve conter apenas números, encontrado '{valor}'"
        return None

    @staticmethod
    def validar_tipo_decimal(valor: str, campo: CampoLayout) -> Optional[str]:
        """Valida campo tipo DECIMAL"""
        valor_limpo = valor.strip()
        if valor_limpo:
            try:
                # Verificar se contém apenas dígitos
                if not valor_limpo.isdigit():
                    caracteres_invalidos = [c for c in valor_limpo if not c.isdigit()]
                    chars_str = ', '.join(f"'{c}'" for c in set(caracteres_invalidos))
                    return f"Valor decimal inválido. Contém caracteres não numéricos: {chars_str}"

                # Remove zeros à esquerda e verifica se é um número válido
                valor_sem_zeros = valor_limpo.lstrip('0') or '0'
                if campo.formato:
                    # Se tem formato específico (ex: 2 casas decimais implícitas)
                    casas_decimais = int(campo.formato) if campo.formato.isdigit() else 2
                    decimal_value = Decimal(valor_sem_zeros) / (10 ** casas_decimais)
                    return None  # Valor válido
                else:
                    decimal_value = Decimal(valor_sem_zeros)
                    return None  # Valor válido
            except (InvalidOperation, ValueError):
                return f"Formato decimal inválido. Esperado apenas dígitos, encontrado '{valor}'"
        return None

    @staticmethod
    def validar_tipo_data(valor: str, campo: CampoLayout) -> Optional[str]:
        """Valida campo tipo DATA"""
        valor_limpo = valor.strip()
        if valor_limpo:
            formato = campo.formato or 'YYYYMMDD'

            # Verificar se tem o tamanho correto para data
            if formato == 'YYYYMMDD' and len(valor_limpo) != 8:
                return f"Data deve ter 8 dígitos (YYYYMMDD), encontrado {len(valor_limpo)} dígitos: '{valor}'"

            # Verificar se contém apenas números
            if not valor_limpo.isdigit():
                return f"Data deve conter apenas números, encontrado '{valor}'"

            # Mapear formato para strptime
            formato_python = formato.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d')

            try:
                data_parsed = datetime.strptime(valor_limpo, formato_python)

                # Validações específicas de data
                if formato == 'YYYYMMDD':
                    ano = int(valor_limpo[:4])
                    mes = int(valor_limpo[4:6])
                    dia = int(valor_limpo[6:8])

                    if ano < 1900 or ano > 2100:
                        return f"Ano inválido: {ano}. Deve estar entre 1900 e 2100"
                    if mes < 1 or mes > 12:
                        return f"Mês inválido: {mes}. Deve estar entre 01 e 12"
                    if dia < 1 or dia > 31:
                        return f"Dia inválido: {dia}. Deve estar entre 01 e 31"

                return None  # Data válida

            except ValueError as e:
                # Tentar dar erro mais específico
                if 'day must be in' in str(e):
                    dia = valor_limpo[6:8] if len(valor_limpo) >= 8 else 'XX'
                    mes = valor_limpo[4:6] if len(valor_limpo) >= 6 else 'XX'
                    return f"Dia {dia} é inválido para o mês {mes}"
                elif 'month must be in' in str(e):
                    mes = valor_limpo[4:6] if len(valor_limpo) >= 6 else 'XX'
                    return f"Mês inválido: {mes}. Deve estar entre 01 e 12"
                else:
                    return f"Data inválida no formato {formato}: '{valor}'. Erro: {str(e)}"
        return None

    @classmethod
    def validar_campo(cls, valor: str, campo: CampoLayout) -> List[str]:
        """Valida um campo completo"""
        erros = []

        # Validar obrigatório
        erro_obrigatorio = cls.validar_obrigatorio(valor, campo)
        if erro_obrigatorio:
            erros.append(erro_obrigatorio)
            return erros  # Se é obrigatório e vazio, não faz outras validações

        # Se não é obrigatório e está vazio, pula outras validações
        if not campo.obrigatorio and (not valor or valor.strip() == ''):
            return erros

        # Validar tamanho
        erro_tamanho = cls.validar_tamanho(valor, campo)
        if erro_tamanho:
            erros.append(erro_tamanho)

        # Validar tipo
        if campo.tipo == TipoCampo.TEXTO:
            erro_tipo = cls.validar_tipo_texto(valor, campo)
        elif campo.tipo == TipoCampo.NUMERO:
            erro_tipo = cls.validar_tipo_numero(valor, campo)
        elif campo.tipo == TipoCampo.DECIMAL:
            erro_tipo = cls.validar_tipo_decimal(valor, campo)
        elif campo.tipo == TipoCampo.DATA:
            erro_tipo = cls.validar_tipo_data(valor, campo)
        else:
            erro_tipo = f"Tipo de campo '{campo.tipo}' não implementado"

        if erro_tipo:
            erros.append(erro_tipo)

        return erros