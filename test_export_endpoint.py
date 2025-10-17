#!/usr/bin/env python3
"""
Script de teste para endpoint /api/layout-export
"""
import requests
import json

# Dados de teste
payload = {
    "nome": "Layout Teste",
    "campos": [
        {
            "nome": "CAMPO1",
            "posicao_inicio": 1,
            "tamanho": 10,
            "tipo": "TEXTO",
            "obrigatorio": True,
            "formato": None
        },
        {
            "nome": "CAMPO2",
            "posicao_inicio": 11,
            "tamanho": 5,
            "tipo": "NUMERO",
            "obrigatorio": False,
            "formato": None
        }
    ],
    "signature": "test123"
}

print("Testando endpoint /api/layout-export...")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        "http://localhost:8000/api/layout-export",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        data = response.json()
        if 'download_url' in data:
            print(f"\n✅ Sucesso! Arquivo disponível em: {data['download_url']}")
            print(f"   Filename: {data.get('filename')}")
            
            # Tentar baixar o arquivo
            download_response = requests.get(f"http://localhost:8000{data['download_url']}")
            if download_response.status_code == 200:
                print(f"   ✅ Download OK - {len(download_response.content)} bytes")
            else:
                print(f"   ❌ Falha no download: {download_response.status_code}")
        else:
            print("\n⚠️  Resposta não contém download_url")
    else:
        print(f"\n❌ Erro: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ Erro: Não foi possível conectar ao servidor")
    print("   Certifique-se de que o backend está rodando em http://localhost:8000")
except Exception as e:
    print(f"\n❌ Erro: {e}")
