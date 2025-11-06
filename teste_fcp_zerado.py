import sys
sys.path.append('src')
from enhanced_validator import EnhancedValidator
from models import Layout, CampoLayout, TipoCampo

print("=== TESTE: FCP ZERADO INCORRETAMENTE ===\n")

# Criar layout com campos FCP (registro 22)
campos_teste = [
    CampoLayout("NFE01-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE01-NUM-FATURA", 3, 13, TipoCampo.NUMERO, True),
    CampoLayout("NFE01-NUM-NF", 24, 9, TipoCampo.NUMERO, True),
    CampoLayout("NFE22-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE22-ICM00-VLR-BC", 49, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-ALIQ", 65, 6, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-VLR", 71, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-ALIQ-FCP", 87, 6, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-VLR-FCP", 93, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE56-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE56-TOT-VLR-ICMS", 65, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE56-TOT-VLR-FCP", 81, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE56-TOT-VLR-BC", 97, 16, TipoCampo.DECIMAL, True),
]

layout_teste = Layout("teste_fcp_zerado", campos_teste, 540)

# Criar arquivo de teste com FCP ZERADO INCORRETAMENTE
import tempfile
import os

def criar_linha(tipo_reg, dados_especificos="", tamanho=540):
    """Cria linha preenchida com dados específicos"""
    linha = [' '] * tamanho
    linha[0:2] = tipo_reg
    if dados_especificos:
        for pos, valor in dados_especificos.items():
            linha[pos[0]:pos[1]] = valor.ljust(pos[1] - pos[0])
    return ''.join(linha)

# Cenário problemático: BC preenchida, Alíquota FCP preenchida, mas VALOR FCP = 0
linha_01 = criar_linha("01", {
    (2, 15): "0000000001111",     # NUM-FATURA = 1111
    (23, 32): "000001234"         # NUM-NF = 1234
})

linha_22_problema = criar_linha("22", {
    (48, 64): "000000000050000",   # BC = 500,00
    (64, 70): "001200",           # ALIQ ICMS = 12,00%
    (70, 86): "000000000006000",  # VLR ICMS = 60,00 (500 × 12% = 60,00)
    (86, 92): "000200",           # ALIQ FCP = 2,00% (PREENCHIDO!)
    (92, 108): "000000000000000"  # VLR FCP = 0,00 (ZERADO INCORRETAMENTE!)
    # Deveria ser: 500 × 2% = 10,00
})

linha_56 = criar_linha("56", {
    (64, 80): "000000000006000",  # TOT ICMS = 60,00 (correto)
    (80, 96): "000000000000000",  # TOT FCP = 0,00 (ERRO! deveria ser 10,00)
    (96, 112): "000000000050000", # TOT BC = 500,00 (correto)
})

teste_content = f"""{linha_01}
{linha_22_problema}
{linha_56}
"""

print("Conteúdo do teste:")
print("===================")
print("Linha 1 (Reg 01): Fatura 1111, NF 1234")
print("Linha 2 (Reg 22): BC=500,00 | ALIQ_FCP=2,00% | VLR_FCP=0,00 ❌ (deveria ser 10,00)")
print("Linha 3 (Reg 56): TOT_FCP=0,00 ❌ (deveria ser 10,00)")
print()

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
    temp_file.write(teste_content)
    temp_file_path = temp_file.name

try:
    print("1. Criando Enhanced Validator...")
    validator = EnhancedValidator(layout_teste)
    print("✅ Enhanced Validator criado com sucesso")

    print("\n2. Executando validação para FCP ZERADO...")
    resultado = validator.validar_arquivo(temp_file_path)

    print(f"\n✅ Validação concluída:")
    print(f"   Total de linhas: {resultado.total_linhas}")
    print(f"   Linhas válidas: {resultado.linhas_validas}")
    print(f"   Linhas com erro: {resultado.linhas_com_erro}")
    print(f"   Taxa de sucesso: {resultado.taxa_sucesso:.2f}%")
    print(f"   Total de erros: {len(resultado.erros)}")

    print("\n3. ERROS DETECTADOS:")
    if resultado.erros:
        for i, erro in enumerate(resultado.erros, 1):
            print(f"\n   🔴 ERRO {i}:")
            print(f"      Linha: {erro.linha}")
            print(f"      Campo: {erro.campo}")
            print(f"      Tipo: {erro.erro_tipo}")
            print(f"      Valor encontrado: {erro.valor_encontrado}")
            print(f"      Valor esperado: {erro.valor_esperado}")
            print(f"      📝 Descrição: {erro.descricao}")

    print("\n4. TOTAIS ACUMULADOS:")
    if resultado.totais_acumulados:
        for campo, valor in resultado.totais_acumulados.items():
            valor_fmt = f"{valor/100:.2f}".replace('.', ',')
            imposto = campo.replace('NFE56-TOT-VLR-', '')
            print(f"   💰 {imposto}: R$ {valor_fmt}")

    # Verificar se detectou os erros esperados
    tipos_erro_encontrados = [erro.erro_tipo for erro in resultado.erros]
    erros_esperados = ['VALOR_ZERADO_FCP', 'TOTAL_FCP']

    print("\n5. VERIFICAÇÃO DOS ERROS ESPERADOS:")
    for erro_esperado in erros_esperados:
        if erro_esperado in tipos_erro_encontrados:
            print(f"   ✅ {erro_esperado}: DETECTADO")
        else:
            print(f"   ❌ {erro_esperado}: NÃO DETECTADO")

    print("\n✅ Teste de FCP ZERADO concluído!")

except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Limpar arquivo temporário
    os.unlink(temp_file_path)