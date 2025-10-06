#!/usr/bin/env python3
"""
Demo script para demonstrar a funcionalidade da aplicação
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def main():
    print("🎯 Demo - Validador de Documentos Sequenciais")
    print("=" * 50)

    # Verificar se a API está rodando
    try:
        import requests
        response = requests.get("http://localhost:8001/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ API já está rodando na porta 8001")
            print("🌐 Abrindo interface web...")
            time.sleep(1)
            webbrowser.open("http://localhost:8001")
            print("\n📋 Instruções para teste:")
            print("1. Clique em 'Validador' no menu")
            print("2. Faça upload de:")
            print("   - Layout: exemplos/layout_exemplo.xlsx")
            print("   - Dados: exemplos/dados_exemplo.txt")
            print("3. Clique em 'Iniciar Validação'")
            print("4. Visualize os resultados e baixe relatórios")
            print("\n💡 Funcionalidades disponíveis:")
            print("  • Dashboard interativo")
            print("  • Gráficos de erros em tempo real")
            print("  • Relatórios em Excel, CSV e TXT")
            print("  • Histórico de validações")
            print("  • Preview de layouts")
            return
    except:
        pass

    print("🚀 Iniciando aplicação...")
    print("Aguarde alguns segundos...")

    # Iniciar API se não estiver rodando
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        # Aguardar inicialização
        for _ in range(30):  # 30 segundos timeout
            try:
                import requests
                response = requests.get("http://localhost:8001/api/health", timeout=1)
                if response.status_code == 200:
                    print("✅ API iniciada com sucesso!")
                    break
            except:
                time.sleep(1)
        else:
            print("❌ Timeout ao iniciar API")
            return

        print("🌐 Abrindo interface web...")
        time.sleep(2)
        webbrowser.open("http://localhost:8001")

        print("\n" + "=" * 50)
        print("🎉 Aplicação rodando com sucesso!")
        print(f"🌐 Interface Web: http://localhost:8001")
        print(f"📊 API Backend: http://localhost:8001/api")
        print(f"📚 Documentação: http://localhost:8001/docs")

        print("\n📋 Para testar:")
        print("1. Use os arquivos em 'exemplos/'")
        print("2. Teste as diferentes funcionalidades")
        print("3. Baixe relatórios")

        print("\n💡 Pressione Ctrl+C para parar")
        print("=" * 50)

        # Manter rodando
        process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Parando aplicação...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("✅ Aplicação parada!")
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())