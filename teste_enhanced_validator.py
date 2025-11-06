import sys
sys.path.append('src')
from enhanced_validator import EnhancedValidator
from models import Layout, CampoLayout, TipoCampo

print("=== TESTE: ENHANCED VALIDATOR ===\n")

# Criar layout simplificado para teste
campos_teste = [
    CampoLayout("NFE01-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE01-NUM-FATURA", 3, 13, TipoCampo.NUMERO, True),
    CampoLayout("NFE01-NUM-NF", 24, 9, TipoCampo.NUMERO, True),
    CampoLayout("NFE22-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE22-ICM00-VLR-BC", 49, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-ALIQ", 65, 6, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-VLR", 71, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE56-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE56-TOT-VLR-ICMS", 65, 16, TipoCampo.DECIMAL, True),
]

layout_teste = Layout("teste_enhanced", campos_teste, 540)

# Criar arquivo de teste em memória
import tempfile
import os

teste_content = """01000000123456           001000000789
22                                                100000000000000006500000000120000
56000000123456           001000000789             000000000120000
01000000123456           001000000789
22                                                100000000000000006500000000120000
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
    temp_file.write(teste_content)
    temp_file_path = temp_file.name

try:
    print("1. Criando Enhanced Validator...")
    validator = EnhancedValidator(layout_teste)
    print("✅ Enhanced Validator criado com sucesso")

    print("\n2. Executando validação aprimorada...")
    resultado = validator.validar_arquivo(temp_file_path)

    print(f"✅ Validação concluída:")
    print(f"   Total de linhas: {resultado.total_linhas}")
    print(f"   Linhas válidas: {resultado.linhas_validas}")
    print(f"   Linhas com erro: {resultado.linhas_com_erro}")
    print(f"   Taxa de sucesso: {resultado.taxa_sucesso:.2f}%")
    print(f"   Total de erros: {len(resultado.erros)}")

    print("\n3. Tipos de erros encontrados:")
    if resultado.erros:
        tipos_erro = list(set(erro.erro_tipo for erro in resultado.erros))
        for tipo in tipos_erro:
            quantidade = len([e for e in resultado.erros if e.erro_tipo == tipo])
            print(f"   - {tipo}: {quantidade} ocorrências")

        print("\n4. Detalhes dos erros:")
        for erro in resultado.erros[:5]:  # Primeiros 5 erros
            print(f"   Linha {erro.linha}: {erro.erro_tipo}")
            print(f"      Campo: {erro.campo}")
            print(f"      Descrição: {erro.descricao}")
            print()

    # Verificar estatísticas de faturas se disponível
    if hasattr(resultado, 'estatisticas_faturas') and resultado.estatisticas_faturas:
        print("5. Estatísticas de Faturas:")
        stats = resultado.estatisticas_faturas
        print(f"   Total de faturas: {stats['total_faturas']}")
        print(f"   Total de notas fiscais: {stats['total_notas_fiscais']}")

        for fatura, detalhes in stats['faturas_detalhes'].items():
            print(f"   Fatura {fatura}: {detalhes['quantidade_notas']} notas fiscais")

    # Verificar totais acumulados se disponível
    if hasattr(resultado, 'totais_acumulados') and resultado.totais_acumulados:
        print("\n6. Totais Acumulados de Impostos:")
        for campo, valor in resultado.totais_acumulados.items():
            if valor > 0:
                valor_fmt = f"{valor/100:.2f}".replace('.', ',')
                print(f"   {campo}: {valor_fmt}")

    print("\n✅ Teste do Enhanced Validator concluído!")

except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Limpar arquivo temporário
    os.unlink(temp_file_path)