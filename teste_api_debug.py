#!/usr/bin/env python3
"""
Script para testar a API e ver exatamente quais dados estão sendo retornados
"""
import requests
import json
from pathlib import Path

# Verificar se existem arquivos de exemplo
exemplos_dir = Path("exemplos")

print("🔍 Procurando arquivos de exemplo...")

# Usar arquivos específicos que sabemos que existem
layout_file = Path("exemplos/layout_teste.xlsx")
dados_file = Path("exemplos/L2508200 (3).txt")

if not layout_file.exists():
    # Tentar outro layout
    layout_file = Path("exemplos/layoutOfficial (6).xlsx")

if not layout_file.exists():
    print("❌ Nenhum layout encontrado")
    exit(1)

if not dados_file.exists():
    # Tentar outro arquivo de dados
    dados_file = Path("exemplos/660.txt")

if not dados_file.exists():
    print("❌ Nenhum arquivo de dados encontrado")
    exit(1)

print(f"✅ Layout encontrado: {layout_file}")
print(f"✅ Arquivo de dados encontrado: {dados_file}")

print(f"\n🧪 Testando API com:")
print(f"   Layout: {layout_file}")
print(f"   Dados: {dados_file}")

# Testar a API
try:
    with open(layout_file, 'rb') as lf, open(dados_file, 'rb') as df:
        files = {
            'layout_file': lf,
            'data_file': df
        }
        data = {
            'max_erros': '10'  # Limitar para facilitar debug
        }

        print("\n📡 Enviando requisição para API...")
        response = requests.post(
            'http://localhost:8000/api/validar-arquivo',
            files=files,
            data=data,
            timeout=60
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n📊 RESULTADO DA API:")
            print(f"Timestamp: {result.get('timestamp', 'N/A')}")

            # Informações básicas do resultado
            resultado = result.get('resultado', {})
            print(f"\n📈 ESTATÍSTICAS:")
            print(f"  Total de linhas: {resultado.get('total_linhas', 'N/A')}")
            print(f"  Linhas válidas: {resultado.get('linhas_validas', 'N/A')}")
            print(f"  Linhas com erro: {resultado.get('linhas_com_erro', 'N/A')}")
            print(f"  Taxa de sucesso: {resultado.get('taxa_sucesso', 'N/A')}%")

            # Analisar erros
            erros = resultado.get('erros', [])
            print(f"\n❌ ERROS ENCONTRADOS: {len(erros)} erros")

            if erros:
                print(f"\n🔍 PRIMEIROS 5 ERROS:")
                for i, erro in enumerate(erros[:5]):
                    print(f"  {i+1}. Linha {erro.get('linha', 'N/A')} - Campo: {erro.get('campo', 'N/A')}")
                    print(f"     Tipo: {erro.get('erro_tipo', 'N/A')}")
                    print(f"     Descrição: {erro.get('descricao', 'N/A')}")
                    print(f"     Valor: {erro.get('valor_encontrado', 'N/A')}")
                    print("")

                # Analisar tipos de erro
                tipos_erro = {}
                for erro in erros:
                    tipo = erro.get('erro_tipo', 'DESCONHECIDO')
                    tipos_erro[tipo] = tipos_erro.get(tipo, 0) + 1

                print(f"📊 TIPOS DE ERRO:")
                for tipo, qtd in tipos_erro.items():
                    print(f"  {tipo}: {qtd}")
            else:
                print("✅ Nenhum erro encontrado nos dados retornados!")

            # Verificar se há dados de estatísticas
            estatisticas = result.get('estatisticas', {})
            print(f"\n📊 ESTATÍSTICAS EXTRAS:")
            print(f"  Tipos de erro: {len(estatisticas.get('tipos_erro', {}))}")
            print(f"  Campos com erro: {len(estatisticas.get('campos_com_erro', {}))}")

        else:
            print(f"❌ Erro na API: {response.status_code}")
            print(f"Resposta: {response.text}")

except Exception as e:
    print(f"❌ Erro ao testar API: {e}")