import sys
sys.path.append('src')
from enhanced_validator import EnhancedValidator
from models import Layout, CampoLayout, TipoCampo

print("=== DEBUG: EXTRAÇÃO FCP ===\n")

# Linha de teste: registro 22
linha = "22                                                000000000017693006500000000011500650000000000120"
print(f"Linha completa: '{linha}'")
print(f"Tamanho da linha: {len(linha)}")
print(f"Posições: {' '.join([str(i%10) for i in range(len(linha))])}")
print(f"Dezenas:  {' '.join([str(i//10) for i in range(len(linha))])}")

# Analisando a linha manualmente:
# Posições:  22000000000000000000000000000000000000000000000000000000000017693006500000000011500650000000000120
# Campos parecem estar assim:
# BC: posições 49-64 (pos 73-88)  = '000000000017693'
# ALIQ: posições após BC           = '0065'
# VLR: posições após ALIQ          = '0000000000115'
# ALIQ-FCP: após VLR               = '0065'
# VLR-FCP: após ALIQ-FCP           = '0000000000120'

print("\nAnálise posição por posição da linha:")
for i, char in enumerate(linha):
    if i >= 45:  # A partir de onde começam os dados importantes
        print(f"pos {i+1:2d}: '{char}'")

# Vamos tentar identificar visualmente onde estão os valores
print(f"\nVisualmente na linha:")
print(f"22 + 46 espaços + campos")
dados = linha[48:]  # Pulando tipo registro + espaços
print(f"Dados: '{dados}'")
print(f"Esperamos: BC(000000000017693) + ALIQ(0065) + VLR(0000000000115) + ALIQ-FCP(0065) + VLR-FCP(0000000000120)")

# Campos FCP baseado na análise visual
campos = [
    ("NFE22-ICM00-VLR-BC", 49, 15),     # 000000000017693
    ("NFE22-ICM00-ALIQ", 64, 4),       # 0065
    ("NFE22-ICM00-VLR", 68, 13),       # 0000000000115
    ("NFE22-ICM00-ALIQ-FCP", 81, 4),   # 0065
    ("NFE22-ICM00-VLR-FCP", 85, 13),   # 0000000000120
]

print("\nExtração de campos:")
for nome, inicio, tamanho in campos:
    fim = inicio + tamanho - 1
    valor = linha[inicio-1:inicio-1+tamanho]
    print(f"{nome}: pos {inicio}-{fim} = '{valor}' (len={len(valor)})")

print("\nTeste de parsing:")
def _parse_decimal_value(s: str) -> int:
    def _only_digits_to_int(s):
        digits = ''.join(ch for ch in s if ch.isdigit())
        return int(digits) if digits else 0

    try:
        # Remover espaços e zeros à esquerda
        clean_s = s.strip().lstrip('0') or '0'
        print(f"  clean_s: '{clean_s}'")

        # Se contém ponto decimal, processar
        if '.' in clean_s:
            parts = clean_s.split('.')
            inteiro = int(parts[0]) if parts[0] else 0
            decimal = parts[1][:2].ljust(2, '0')
            result = inteiro * 100 + int(decimal)
            print(f"  com ponto: inteiro={inteiro}, decimal='{decimal}', result={result}")
            return result
        else:
            # Se não tem ponto, considerar como inteiro com 2 casas implícitas
            result = _only_digits_to_int(clean_s)
            print(f"  sem ponto: digits='{clean_s}', result={result}")
            return result
    except Exception as e:
        print(f"  erro: {e}")
        return 0

# Testar parsing dos valores
bc_str = "000000000017693"      # BC = 176,93 = 17693
aliq_str = "000065"             # Alíquota = 0,65% = 65
valor_str = "0000000000115"     # Valor = 1,15 = 115
aliq_fcp_str = "000065"         # Alíquota FCP = 0,65% = 65
valor_fcp_str = "0000000000120" # Valor FCP = 1,20 = 120 (ERRO! deveria ser 115)

print(f"\nBC: '{bc_str}'")
bc_val = _parse_decimal_value(bc_str)
print(f"BC parsed: {bc_val} (esperado: 17693)")

print(f"\nAlíquota: '{aliq_str}'")
aliq_val = _parse_decimal_value(aliq_str)
print(f"Alíquota parsed: {aliq_val} (esperado: 65)")

print(f"\nValor: '{valor_str}'")
valor_val = _parse_decimal_value(valor_str)
print(f"Valor parsed: {valor_val} (esperado: 115)")

print(f"\nAlíquota FCP: '{aliq_fcp_str}'")
aliq_fcp_val = _parse_decimal_value(aliq_fcp_str)
print(f"Alíquota FCP parsed: {aliq_fcp_val} (esperado: 65)")

print(f"\nValor FCP: '{valor_fcp_str}'")
valor_fcp_val = _parse_decimal_value(valor_fcp_str)
print(f"Valor FCP parsed: {valor_fcp_val} (esperado: 120)")

# Teste do cálculo
print(f"\nCálculo FCP:")
print(f"BC × Alíquota FCP / 10000 = {bc_val} × {aliq_fcp_val} / 10000 = {(bc_val * aliq_fcp_val) // 10000}")
print(f"Valor declarado: {valor_fcp_val}")
print(f"Diferença: {valor_fcp_val - ((bc_val * aliq_fcp_val) // 10000)}")