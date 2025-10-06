import unittest
from src.validators import ValidadorCampo
from src.models import CampoLayout, TipoCampo


class TestValidadores(unittest.TestCase):

    def setUp(self):
        self.validador = ValidadorCampo()

    def test_validar_obrigatorio_campo_vazio(self):
        """Testa validação de campo obrigatório vazio"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.TEXTO, obrigatorio=True)
        erro = self.validador.validar_obrigatorio("", campo)
        self.assertIsNotNone(erro)
        self.assertIn("obrigatório", erro)

    def test_validar_obrigatorio_campo_preenchido(self):
        """Testa validação de campo obrigatório preenchido"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.TEXTO, obrigatorio=True)
        erro = self.validador.validar_obrigatorio("VALOR", campo)
        self.assertIsNone(erro)

    def test_validar_obrigatorio_campo_nao_obrigatorio(self):
        """Testa validação de campo não obrigatório vazio"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.TEXTO, obrigatorio=False)
        erro = self.validador.validar_obrigatorio("", campo)
        self.assertIsNone(erro)

    def test_validar_tamanho_correto(self):
        """Testa validação de tamanho correto"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.TEXTO, obrigatorio=True)
        erro = self.validador.validar_tamanho("ABCDE", campo)
        self.assertIsNone(erro)

    def test_validar_tamanho_incorreto(self):
        """Testa validação de tamanho incorreto"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.TEXTO, obrigatorio=True)
        erro = self.validador.validar_tamanho("ABC", campo)
        self.assertIsNotNone(erro)
        self.assertIn("tamanho", erro)

    def test_validar_tipo_numero_valido(self):
        """Testa validação de número válido"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.NUMERO, obrigatorio=True)
        erro = self.validador.validar_tipo_numero("12345", campo)
        self.assertIsNone(erro)

    def test_validar_tipo_numero_invalido(self):
        """Testa validação de número inválido"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.NUMERO, obrigatorio=True)
        erro = self.validador.validar_tipo_numero("ABC12", campo)
        self.assertIsNotNone(erro)
        self.assertIn("números", erro)

    def test_validar_tipo_data_valida(self):
        """Testa validação de data válida"""
        campo = CampoLayout("TESTE", 1, 8, TipoCampo.DATA, obrigatorio=True, formato="YYYYMMDD")
        erro = self.validador.validar_tipo_data("20231201", campo)
        self.assertIsNone(erro)

    def test_validar_tipo_data_invalida(self):
        """Testa validação de data inválida"""
        campo = CampoLayout("TESTE", 1, 8, TipoCampo.DATA, obrigatorio=True, formato="YYYYMMDD")
        erro = self.validador.validar_tipo_data("20231301", campo)  # Mês 13 não existe
        self.assertIsNotNone(erro)
        self.assertIn("formato", erro)

    def test_validar_campo_completo_sucesso(self):
        """Testa validação completa de campo com sucesso"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.TEXTO, obrigatorio=True)
        erros = self.validador.validar_campo("ABCDE", campo)
        self.assertEqual(len(erros), 0)

    def test_validar_campo_completo_multiplos_erros(self):
        """Testa validação completa de campo com múltiplos erros"""
        campo = CampoLayout("TESTE", 1, 5, TipoCampo.NUMERO, obrigatorio=True)
        erros = self.validador.validar_campo("ABC", campo)  # Tamanho e tipo errados
        self.assertGreater(len(erros), 1)


if __name__ == '__main__':
    unittest.main()