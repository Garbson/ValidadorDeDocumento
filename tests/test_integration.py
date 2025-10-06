import unittest
import tempfile
import os
import pandas as pd
from pathlib import Path

from src.layout_parser import LayoutParser
from src.file_validator import ValidadorArquivo
from src.report_generator import GeradorRelatorio
from src.models import TipoCampo


class TestIntegration(unittest.TestCase):

    def setUp(self):
        """Cria arquivos temporários para teste"""
        self.temp_dir = tempfile.mkdtemp()

        # Criar Excel de layout de teste
        layout_data = {
            'Campo': ['NOME', 'IDADE', 'DATA_NASC'],
            'Posicao_Inicio': [1, 21, 31],
            'Tamanho': [20, 10, 8],
            'Tipo': ['TEXTO', 'NUMERO', 'DATA'],
            'Obrigatorio': ['S', 'S', 'N'],
            'Formato': ['', '', 'YYYYMMDD']
        }

        self.layout_file = os.path.join(self.temp_dir, 'layout_teste.xlsx')
        df = pd.DataFrame(layout_data)
        df.to_excel(self.layout_file, index=False)

        # Criar arquivo TXT de teste
        self.arquivo_valido = os.path.join(self.temp_dir, 'dados_validos.txt')
        with open(self.arquivo_valido, 'w') as f:
            f.write("JOAO SILVA          0000000030        \n")  # Sem data (opcional)
            f.write("MARIA SANTOS        0000000025        \n")

        self.arquivo_com_erros = os.path.join(self.temp_dir, 'dados_erros.txt')
        with open(self.arquivo_com_erros, 'w') as f:
            f.write("                    ABC       20231301\n")  # Nome vazio, idade inválida, data inválida
            f.write("PEDRO               0000000040        \n")  # Válido

    def tearDown(self):
        """Remove arquivos temporários"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_fluxo_completo_arquivo_valido(self):
        """Testa fluxo completo com arquivo válido"""
        # Parse do layout
        parser = LayoutParser()
        layout = parser.parse_excel(self.layout_file)

        self.assertEqual(len(layout.campos), 3)
        self.assertEqual(layout.campos[0].nome, 'NOME')
        self.assertEqual(layout.campos[0].tipo, TipoCampo.TEXTO)

        # Validação do arquivo
        validador = ValidadorArquivo(layout)
        resultado = validador.validar_arquivo(self.arquivo_valido)

        self.assertEqual(resultado.total_linhas, 2)
        self.assertEqual(resultado.linhas_validas, 2)
        self.assertEqual(resultado.linhas_com_erro, 0)
        self.assertEqual(resultado.taxa_sucesso, 100.0)

    def test_fluxo_completo_arquivo_com_erros(self):
        """Testa fluxo completo com arquivo com erros"""
        # Parse do layout
        parser = LayoutParser()
        layout = parser.parse_excel(self.layout_file)

        # Validação do arquivo
        validador = ValidadorArquivo(layout)
        resultado = validador.validar_arquivo(self.arquivo_com_erros)

        self.assertEqual(resultado.total_linhas, 2)
        self.assertEqual(resultado.linhas_validas, 1)  # Só a segunda linha é válida
        self.assertEqual(resultado.linhas_com_erro, 1)
        self.assertGreater(len(resultado.erros), 0)  # Deve ter erros

        # Verificar tipos de erro específicos
        tipos_erro = [erro.erro_tipo for erro in resultado.erros]
        self.assertIn('CAMPO_OBRIGATORIO', tipos_erro)  # Nome vazio
        self.assertIn('TIPO_INVALIDO', tipos_erro)      # Idade com letras

    def test_relatorio_generation(self):
        """Testa geração de relatórios"""
        # Parse e validação
        parser = LayoutParser()
        layout = parser.parse_excel(self.layout_file)
        validador = ValidadorArquivo(layout)
        resultado = validador.validar_arquivo(self.arquivo_com_erros)

        # Geração de relatório
        gerador = GeradorRelatorio(resultado, layout)

        # Testar relatório em texto
        resumo_texto = gerador.gerar_resumo_texto()
        self.assertIn("RELATÓRIO DE VALIDAÇÃO", resumo_texto)
        self.assertIn("Total de linhas: 2", resumo_texto)

        # Testar relatório Excel
        excel_path = os.path.join(self.temp_dir, 'relatorio_teste.xlsx')
        gerador.gerar_detalhes_excel(excel_path)
        self.assertTrue(Path(excel_path).exists())

        # Testar relatório CSV
        csv_path = os.path.join(self.temp_dir, 'relatorio_teste.csv')
        gerador.gerar_relatorio_csv(csv_path)
        self.assertTrue(Path(csv_path).exists())

    def test_layout_invalid_excel(self):
        """Testa comportamento com Excel inválido"""
        # Criar Excel com estrutura errada
        invalid_layout = os.path.join(self.temp_dir, 'layout_invalido.xlsx')
        invalid_data = {
            'CampoErrado': ['TESTE'],
            'OutroErrado': [1]
        }
        df = pd.DataFrame(invalid_data)
        df.to_excel(invalid_layout, index=False)

        parser = LayoutParser()
        with self.assertRaises(ValueError):
            parser.parse_excel(invalid_layout)

    def test_arquivo_inexistente(self):
        """Testa comportamento com arquivo inexistente"""
        parser = LayoutParser()
        with self.assertRaises(FileNotFoundError):
            parser.parse_excel('/caminho/inexistente.xlsx')

        layout = LayoutParser().parse_excel(self.layout_file)
        validador = ValidadorArquivo(layout)
        with self.assertRaises(FileNotFoundError):
            validador.validar_arquivo('/caminho/inexistente.txt')


if __name__ == '__main__':
    unittest.main()