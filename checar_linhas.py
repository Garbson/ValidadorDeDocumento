# Script para checar tamanho das linhas de um arquivo TXT
# Salve como checar_linhas.py e execute: python checar_linhas.py

ARQUIVO = r'C:\Users\Filipe O brabo\Downloads\L2509200\L2509200.txt'  # Caminho completo do arquivo
TAMANHO_ESPERADO = 540      # Troque pelo tamanho esperado da linha (soma dos campos do layout)

with open(ARQUIVO, encoding='utf-8') as f:
    for i, linha in enumerate(f, 1):
        tamanho = len(linha.rstrip('\r\n'))
        status = '[OK]' if tamanho == TAMANHO_ESPERADO else '[ERRO]'
        print(f"Linha {i}: {tamanho} caracteres {status}")
        if tamanho != TAMANHO_ESPERADO:
            print(f"  Conteúdo: {linha.rstrip()}")
