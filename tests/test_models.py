import unittest
from src.models import CampoLayout, TipoCampo, ErroValidacao, ResultadoValidacao, Layout


class TestModels(unittest.TestCase):

    def test_campo_layout_posicao_fim(self):
        """Testa cálculo automático da posição final"""
        campo = CampoLayout(
            nome="TESTE",
            posicao_inicio=10,
            tamanho=5,
            tipo=TipoCampo.TEXTO,
            obrigatorio=True
        )
        self.assertEqual(campo.posicao_fim, 14)

    def test_campo_layout_posicao_fim_customizada(self):
        """Testa posição final customizada"""
        campo = CampoLayout(
            nome="TESTE",
            posicao_inicio=10,
            tamanho=5,
            tipo=TipoCampo.TEXTO,
            obrigatorio=True,
            posicao_fim=20
        )
        self.assertEqual(campo.posicao_fim, 20)

    def test_resultado_validacao_taxa_sucesso(self):
        """Testa cálculo da taxa de sucesso"""
        resultado = ResultadoValidacao(
            total_linhas=100,
            linhas_validas=80,
            linhas_com_erro=20,
            erros=[]
        )
        self.assertEqual(resultado.taxa_sucesso, 80.0)

    def test_resultado_validacao_taxa_sucesso_zero_linhas(self):
        """Testa taxa de sucesso com zero linhas"""
        resultado = ResultadoValidacao(
            total_linhas=0,
            linhas_validas=0,
            linhas_com_erro=0,
            erros=[]
        )
        self.assertEqual(resultado.taxa_sucesso, 0.0)

    def test_layout_get_campo(self):
        """Testa busca de campo por nome"""
        campo1 = CampoLayout("CAMPO1", 1, 10, TipoCampo.TEXTO, True)
        campo2 = CampoLayout("CAMPO2", 11, 5, TipoCampo.NUMERO, False)

        layout = Layout("TEST", [campo1, campo2], 15)

        self.assertEqual(layout.get_campo("CAMPO1"), campo1)
        self.assertEqual(layout.get_campo("CAMPO2"), campo2)
        self.assertIsNone(layout.get_campo("INEXISTENTE"))


if __name__ == '__main__':
    unittest.main()