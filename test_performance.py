#!/usr/bin/env python3
"""
Teste de performance da validação
"""
import time
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.layout_parser import LayoutParser
from src.file_validator import ValidadorArquivo

def test_validation_performance():
    print("=== TESTE DE PERFORMANCE DA VALIDAÇÃO ===")

    # Arquivos de teste
    layout_file = "exemplos/layout_exemplo.xlsx"
    data_file = "exemplos/dados_exemplo.txt"

    if not Path(layout_file).exists():
        print(f"[ERROR] Arquivo de layout não encontrado: {layout_file}")
        return

    if not Path(data_file).exists():
        print(f"[ERROR] Arquivo de dados não encontrado: {data_file}")
        return

    try:
        print(f"[INFO] Carregando layout: {layout_file}")
        start_time = time.time()

        # Carregar layout
        parser = LayoutParser()
        layout = parser.parse_excel(layout_file)
        layout_time = time.time() - start_time

        print(f"[OK] Layout carregado em {layout_time:.3f}s")
        print(f"   - Nome: {layout.nome}")
        print(f"   - Campos: {len(layout.campos)}")
        print(f"   - Tamanho linha: {layout.tamanho_linha}")

        print(f"\n[INFO] Validando arquivo: {data_file}")
        start_time = time.time()

        # Validar arquivo
        validador = ValidadorArquivo(layout)
        resultado = validador.validar_arquivo(data_file, max_erros=50)
        validation_time = time.time() - start_time

        print(f"[OK] Validação concluída em {validation_time:.3f}s")
        print(f"   - Total de linhas: {resultado.total_linhas}")
        print(f"   - Linhas válidas: {resultado.linhas_validas}")
        print(f"   - Linhas com erro: {resultado.linhas_com_erro}")
        print(f"   - Total de erros: {len(resultado.erros)}")
        print(f"   - Taxa de sucesso: {resultado.taxa_sucesso:.2f}%")

        print(f"\n[TIME] TEMPO TOTAL: {layout_time + validation_time:.3f}s")

        # Mostrar alguns erros como exemplo
        if resultado.erros:
            print(f"\n[LIST] Primeiros 5 erros encontrados:")
            for i, erro in enumerate(resultado.erros[:5]):
                print(f"   {i+1}. Linha {erro.linha} - Campo '{erro.campo}': {erro.descricao}")

        return True

    except Exception as e:
        print(f"[ERROR] Erro durante validação: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_validation_performance()