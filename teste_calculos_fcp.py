import sys
sys.path.append('src')
from enhanced_validator import EnhancedValidator
from models import Layout, CampoLayout, TipoCampo

print("=== TESTE: CÁLCULOS FCP NO ENHANCED VALIDATOR ===\n")

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

layout_teste = Layout("teste_fcp", campos_teste, 540)

# Criar arquivo de teste com erro de cálculo FCP
import tempfile
import os

# Criar linha correta baseada nas posições do layout:
# Registro 22: posições específicas para cada campo
linha_22 = " " * 540  # Linha em branco de 540 chars
linha_22_list = list(linha_22)

# Preencher campos na linha 22
linha_22_list[0:2] = "22"  # Tipo registro

# NFE22-ICM00-VLR-BC nas posições 49-64 (16 chars) = 17693 (176,93)
valor_bc = "000000000017693 ".ljust(16)
linha_22_list[48:64] = valor_bc

# NFE22-ICM00-ALIQ nas posições 65-70 (6 chars) = 65 (0,65%)
valor_aliq = "000065"
linha_22_list[64:70] = valor_aliq

# NFE22-ICM00-VLR nas posições 71-86 (16 chars) = 115 (1,15) - valor correto
valor_icms = "000000000000115 ".ljust(16)
linha_22_list[70:86] = valor_icms

# NFE22-ICM00-ALIQ-FCP nas posições 87-92 (6 chars) = 65 (0,65%)
valor_aliq_fcp = "000065"
linha_22_list[86:92] = valor_aliq_fcp

# NFE22-ICM00-VLR-FCP nas posições 93-108 (16 chars) = 120 (1,20) - ERRO! deveria ser 115
valor_fcp_errado = "000000000000120 ".ljust(16)
linha_22_list[92:108] = valor_fcp_errado

linha_22_final = ''.join(linha_22_list)

teste_content = f"""01000000123456           001000000789{' ' * (540-33)}
{linha_22_final}
56000000123456           001000000789             000000000011500000000000120000000000017693{' ' * (540-81)}
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

        print("\n4. Detalhes dos erros de cálculo:")
        for erro in resultado.erros:
            if 'CALCULO_ERRO' in erro.erro_tipo:
                print(f"   Linha {erro.linha}: {erro.erro_tipo}")
                print(f"      Campo: {erro.campo}")
                print(f"      Descrição: {erro.descricao}")
                print()

    print("✅ Teste de cálculos FCP concluído!")

except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Limpar arquivo temporário
    os.unlink(temp_file_path)