#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar a aplicação web completa
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path


def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    try:
        import uvicorn
        import fastapi
        print("✅ Dependências Python OK")
        return True
    except ImportError:
        print("❌ Dependências Python não encontradas")
        print("Execute: pip install -r requirements.txt")
        return False


def check_frontend():
    """Verifica se o frontend foi buildado"""
    frontend_dist = Path("frontend/dist")
    if frontend_dist.exists():
        print("✅ Frontend buildado encontrado")
        return True
    else:
        print("⚠️ Frontend não buildado")
        print("O backend será iniciado sem interface web")
        return False


def start_api():
    """Inicia a API FastAPI"""
    print("🚀 Iniciando API backend...")

    # Definir variáveis de ambiente
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path.cwd())

    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        # Mostrar logs em tempo real
        for line in iter(process.stdout.readline, ''):
            print(f"[API] {line.strip()}")
            if "Uvicorn running on" in line:
                print("\n✅ API iniciada com sucesso!")
                print("📊 Acesse: http://localhost:8000")
                print("📚 Documentação: http://localhost:8000/docs")
                break

        return process
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")
        return None


def build_frontend():
    """Constrói o frontend se necessário"""
    if not Path("frontend/package.json").exists():
        print("⚠️ Frontend não encontrado")
        return False

    print("🔨 Construindo frontend...")

    # Verificar se node_modules existe
    if not Path("frontend/node_modules").exists():
        print("📦 Instalando dependências do frontend...")
        result = subprocess.run(
            ["npm", "install"],
            cwd="frontend",
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ Erro ao instalar dependências: {result.stderr}")
            return False

    # Build do frontend
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd="frontend",
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ Frontend construído com sucesso!")
        return True
    else:
        print(f"❌ Erro ao construir frontend: {result.stderr}")
        return False


def main():
    """Função principal"""
    print("🌐 Iniciando Validador de Documentos Sequenciais - Web")
    print("=" * 50)

    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)

    # Tentar construir frontend se não existir
    if not check_frontend():
        if Path("frontend/package.json").exists():
            print("🔨 Tentando construir frontend automaticamente...")
            if not build_frontend():
                print("⚠️ Continuando apenas com backend...")
        else:
            print("⚠️ Continuando apenas com backend...")

    # Criar diretórios necessários
    Path("temp_uploads").mkdir(exist_ok=True)
    Path("relatorios_web").mkdir(exist_ok=True)

    print("\n🚀 Iniciando serviços...")

    # Iniciar API
    api_process = start_api()

    if api_process:
        try:
            print("\n" + "=" * 50)
            print("🎉 Aplicação iniciada com sucesso!")
            print(f"🌐 Interface Web: http://localhost:8000")
            print(f"📊 API Backend: http://localhost:8000/api")
            print(f"📚 Documentação: http://localhost:8000/docs")
            print("\n💡 Dicas:")
            print("  • Use Ctrl+C para parar os serviços")
            print("  • A API aceita uploads de até 100MB")
            print("  • Relatórios são salvos em 'relatorios_web/'")
            print("=" * 50)

            # Aguardar interrupção
            api_process.wait()

        except KeyboardInterrupt:
            print("\n\n🛑 Parando serviços...")
            api_process.terminate()
            api_process.wait()
            print("✅ Serviços parados com sucesso!")
    else:
        print("❌ Falha ao iniciar a aplicação")
        sys.exit(1)


if __name__ == "__main__":
    main()