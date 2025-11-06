import sys
sys.path.append('src')
from enhanced_validator import EnhancedValidator
from models import Layout, CampoLayout, TipoCampo

print("=== TESTE COMPLETO: ENHANCED VALIDATOR ===\n")

# Criar layout completo com trailer 99
campos_teste = [
    # Registro 01 - Header da fatura
    CampoLayout("NFE01-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE01-NUM-FATURA", 3, 13, TipoCampo.NUMERO, True),
    CampoLayout("NFE01-NUM-NF", 24, 9, TipoCampo.NUMERO, True),

    # Registro 22 - ICMS
    CampoLayout("NFE22-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE22-ICM00-VLR-BC", 49, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-ALIQ", 65, 6, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-VLR", 71, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-ALIQ-FCP", 87, 6, TipoCampo.DECIMAL, True),
    CampoLayout("NFE22-ICM00-VLR-FCP", 93, 16, TipoCampo.DECIMAL, True),

    # Registro 38 - PIS
    CampoLayout("NFE38-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE38-PIS-VLR-BC", 49, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE38-PIS-ALIQ", 65, 6, TipoCampo.DECIMAL, True),
    CampoLayout("NFE38-PIS-VLR", 71, 16, TipoCampo.DECIMAL, True),

    # Registro 56 - Totalizador
    CampoLayout("NFE56-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE56-TOT-VLR-ICMS", 65, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE56-TOT-VLR-FCP", 81, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE56-TOT-VLR-BC", 97, 16, TipoCampo.DECIMAL, True),
    CampoLayout("NFE56-TOT-VLR-PIS", 113, 16, TipoCampo.DECIMAL, True),

    # Registro 99 - Trailer
    CampoLayout("NFE99-TP-REG", 1, 2, TipoCampo.NUMERO, True),
    CampoLayout("NFE99-QTD-NF", 10, 6, TipoCampo.NUMERO, True),  # Quantidade de notas fiscais
]

layout_teste = Layout("teste_completo", campos_teste, 540)

# Criar arquivo de teste completo
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

# Fatura 1
linha_01_fat1 = criar_linha("01", {
    (2, 15): "0000000001111",     # NUM-FATURA = 1111
    (23, 32): "000001234"         # NUM-NF = 1234
})

linha_22_fat1 = criar_linha("22", {
    (48, 64): "000000000010000",   # BC = 100,00
    (64, 70): "000065",           # ALIQ ICMS = 0,65%
    (70, 86): "000000000000065",  # VLR ICMS = 0,65 (100 × 0.65% = 0.65)
    (86, 92): "000065",           # ALIQ FCP = 0,65%
    (92, 108): "000000000000065"  # VLR FCP = 0,65 (correto)
})

linha_38_fat1 = criar_linha("38", {
    (48, 64): "000000000010000",  # BC = 100,00
    (64, 70): "000165",           # ALIQ PIS = 1,65%
    (70, 86): "000000000000165"   # VLR PIS = 1,65 (100 × 1.65% = 1.65)
})

linha_56_fat1 = criar_linha("56", {
    (64, 80): "000000000000065",  # TOT ICMS = 0,65 (correto)
    (80, 96): "000000000000065",  # TOT FCP = 0,65 (correto)
    (96, 112): "000000000010000", # TOT BC = 100,00 (correto)
    (112, 128): "000000000000165" # TOT PIS = 1,65 (correto)
})

# Fatura 2 - COM ERRO no FCP
linha_01_fat2 = criar_linha("01", {
    (2, 15): "0000000002222",     # NUM-FATURA = 2222
    (23, 32): "000005678"         # NUM-NF = 5678
})

linha_22_fat2 = criar_linha("22", {
    (48, 64): "000000000020000",   # BC = 200,00
    (64, 70): "000065",           # ALIQ ICMS = 0,65%
    (70, 86): "000000000000130",  # VLR ICMS = 1,30 (200 × 0.65% = 1.30)
    (86, 92): "000065",           # ALIQ FCP = 0,65%
    (92, 108): "000000000000150"  # VLR FCP = 1,50 (ERRO! deveria ser 1,30)
})

linha_56_fat2 = criar_linha("56", {
    (64, 80): "000000000000130",  # TOT ICMS = 1,30 (correto)
    (80, 96): "000000000000150",  # TOT FCP = 1,50 (ERRO! deveria ser 1,30)
    (96, 112): "000000000020000", # TOT BC = 200,00 (correto)
    (112, 128): "000000000000000" # TOT PIS = 0,00 (sem PIS nesta fatura)
})

# Trailer com ERRO na quantidade
linha_99 = criar_linha("99", {
    (9, 15): "000005"             # QTD-NF = 5 (ERRO! só temos 2 NFs)
})

teste_content = f"""{linha_01_fat1}
{linha_22_fat1}
{linha_38_fat1}
{linha_56_fat1}
{linha_01_fat2}
{linha_22_fat2}
{linha_56_fat2}
{linha_99}
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
    temp_file.write(teste_content)
    temp_file_path = temp_file.name

try:
    print("1. Criando Enhanced Validator...")
    validator = EnhancedValidator(layout_teste)
    print("✅ Enhanced Validator criado com sucesso")

    print("\n2. Executando validação COMPLETA...")
    resultado = validator.validar_arquivo(temp_file_path)

    print(f"\n✅ Validação concluída:")
    print(f"   Total de linhas: {resultado.total_linhas}")
    print(f"   Linhas válidas: {resultado.linhas_validas}")
    print(f"   Linhas com erro: {resultado.linhas_com_erro}")
    print(f"   Taxa de sucesso: {resultado.taxa_sucesso:.2f}%")
    print(f"   Total de erros: {len(resultado.erros)}")

    print("\n3. ANÁLISE DETALHADA DOS ERROS:")
    if resultado.erros:
        # Agrupar erros por tipo
        erros_por_tipo = {}
        for erro in resultado.erros:
            erros_por_tipo.setdefault(erro.erro_tipo, []).append(erro)

        for tipo, erros_lista in erros_por_tipo.items():
            print(f"\n   🔴 {tipo}: {len(erros_lista)} ocorrências")
            for erro in erros_lista:
                print(f"      Linha {erro.linha}: {erro.campo}")
                print(f"      📝 {erro.descricao}")
                print()

    print("\n4. ESTATÍSTICAS DE FATURAS:")
    if resultado.estatisticas_faturas:
        stats = resultado.estatisticas_faturas
        print(f"   📊 Total de faturas processadas: {stats['total_faturas']}")
        print(f"   📄 Total de notas fiscais: {stats['total_notas_fiscais']}")

        for fatura, detalhes in stats['faturas_detalhes'].items():
            print(f"   📋 Fatura {fatura}: {detalhes['quantidade_notas']} nota(s) fiscal(is)")

    print("\n5. TOTAIS ACUMULADOS POR IMPOSTO:")
    if resultado.totais_acumulados:
        for campo, valor in resultado.totais_acumulados.items():
            if valor > 0:
                valor_fmt = f"{valor/100:.2f}".replace('.', ',')
                imposto = campo.replace('NFE56-TOT-VLR-', '')
                print(f"   💰 {imposto}: R$ {valor_fmt}")

    print("\n✅ Teste COMPLETO finalizado!")

    # Verificar se detectou os erros esperados
    tipos_erro_encontrados = [erro.erro_tipo for erro in resultado.erros]
    erros_esperados = ['CALCULO_ERRO_FCP', 'TOTAL_FCP', 'TRAILER_QTD_NF']

    print("\n6. VERIFICAÇÃO DOS ERROS ESPERADOS:")
    for erro_esperado in erros_esperados:
        if erro_esperado in tipos_erro_encontrados:
            print(f"   ✅ {erro_esperado}: DETECTADO")
        else:
            print(f"   ❌ {erro_esperado}: NÃO DETECTADO")

except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Limpar arquivo temporário
    os.unlink(temp_file_path)