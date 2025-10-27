#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar a aplicação web completa (backend + frontend em desenvolvimento)
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path
import shutil


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


def check_node():
    """Verifica se Node.js está instalado"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} encontrado")
            return True
    except FileNotFoundError:
        pass

    print("❌ Node.js não encontrado")
    print("Instale o Node.js para rodar o frontend")
    return False


def check_frontend_deps():
    """Verifica se as dependências do frontend estão instaladas"""
    frontend_path = Path("frontend")
    if not frontend_path.exists():
        print("❌ Diretório frontend não encontrado")
        return False

    node_modules = frontend_path / "node_modules"
    if node_modules.exists():
        print("✅ Dependências do frontend OK")
        return True
    else:
        print("📦 Instalando dependências do frontend...")
        return install_frontend_deps()


def install_frontend_deps():
    """Instala as dependências do frontend"""
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd="frontend",
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Dependências do frontend instaladas")
            return True
        else:
            print(f"❌ Erro ao instalar dependências: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False


def start_backend():
    """Inicia o backend FastAPI"""
    print("🚀 Iniciando backend (FastAPI)...")

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

        return process
    except Exception as e:
        print(f"❌ Erro ao iniciar backend: {e}")
        return None


def start_frontend():
    """Inicia o servidor de desenvolvimento do frontend"""
    print("🎨 Iniciando frontend (Vue.js dev server)...")

    try:
        # Tentar executar npm; em Windows pode ser necessário npm.cmd
        commands_to_try = [
            ["npm", "run", "dev"],
            ["npm.cmd", "run", "dev"],
            ["npx", "vite"],
            ["pnpm", "run", "dev"]
        ]

        last_exc = None
        for cmd in commands_to_try:
            # verificar se o executável existe no PATH antes de tentar
            exe = cmd[0]
            if shutil.which(exe) is None:
                # pular tentativa se não existir
                continue
            try:
                process = subprocess.Popen(
                    cmd,
                    cwd="frontend",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                print(f"✅ Frontend iniciado com: {' '.join(cmd)}")
                return process
            except FileNotFoundError as fe:
                last_exc = fe
                # tentar próximo
                continue

        # Se chegou aqui, nenhum comando funcionou
        err_msg = (
            "Não foi possível iniciar o frontend: nenhum executor (npm/npx/pnpm) encontrado no PATH "
            "ou falha ao invocar o comando. Tente executar manualmente:\n  cd frontend && npm run dev"
        )
        print(f"❌ {err_msg}")
        if last_exc:
            print(f"Detalhe do último erro: {last_exc}")
        return None
    except Exception as e:
        print(f"❌ Erro ao iniciar frontend: {e}")
        return None


def monitor_process(process, name):
    """Monitora um processo e mostra seus logs"""
    try:
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                print(f"[{name}] {line.strip()}")
    except Exception as e:
        print(f"❌ Erro ao monitorar {name}: {e}")


def cleanup_processes(*processes):
    """Finaliza todos os processos fornecidos"""
    for process in processes:
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main():
    """Função principal"""
    print("🌐 Iniciando Validador de Documentos Sequenciais - Web")
    print("=" * 50)

    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)

    # Verificar Node.js
    if not check_node():
        sys.exit(1)

    # Verificar dependências do frontend
    if not check_frontend_deps():
        sys.exit(1)

    # Criar diretórios necessários
    Path("temp_uploads").mkdir(exist_ok=True)
    Path("relatorios_web").mkdir(exist_ok=True)

    print("\n🚀 Iniciando serviços...")

    # Iniciar backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Falha ao iniciar backend")
        sys.exit(1)

    # Iniciar frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Falha ao iniciar frontend")
        cleanup_processes(backend_process)
        sys.exit(1)

    # Aguardar que os serviços iniciem
    print("\n⏳ Aguardando serviços iniciarem...")
    time.sleep(3)

    # Iniciar threads para monitorar os processos
    backend_thread = threading.Thread(target=monitor_process, args=(backend_process, "BACKEND"), daemon=True)
    frontend_thread = threading.Thread(target=monitor_process, args=(frontend_process, "FRONTEND"), daemon=True)

    backend_thread.start()
    frontend_thread.start()

    # Aguardar um pouco para capturar mensagens de inicialização
    time.sleep(5)

    try:
        print("\n" + "=" * 60)
        print("🎉 Aplicação iniciada com sucesso!")
        print("📍 URLs disponíveis:")
        print("   🎨 Frontend (Vue.js): http://localhost:3000")
        print("   🔗 Backend (FastAPI): http://localhost:8000")
        print("   📚 Documentação API: http://localhost:8000/docs")
        print("\n💡 Dicas:")
        print("  • Use Ctrl+C para parar todos os serviços")
        print("  • O frontend roda em modo de desenvolvimento com hot-reload")
        print("  • A API aceita uploads de até 100MB")
        print("  • Relatórios são salvos em 'relatorios_web/'")
        print("=" * 60)

        # Aguardar que algum processo termine ou interrupção
        while True:
            if backend_process.poll() is not None:
                print("\n❌ Backend parou inesperadamente")
                break
            if frontend_process.poll() is not None:
                print("\n❌ Frontend parou inesperadamente")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Parando serviços...")

    finally:
        cleanup_processes(backend_process, frontend_process)
        print("✅ Todos os serviços foram parados!")


if __name__ == "__main__":
    main()