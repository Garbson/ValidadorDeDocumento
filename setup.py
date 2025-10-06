#!/usr/bin/env python3
"""
Script de configuração e instalação
"""

import subprocess
import sys
from pathlib import Path


def install_requirements():
    """Instala as dependências"""
    print("🔧 Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências")
        return False


def run_tests():
    """Executa os testes"""
    print("🧪 Executando testes...")
    try:
        subprocess.check_call([sys.executable, "run_tests.py"])
        print("✅ Todos os testes passaram!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Alguns testes falharam")
        return False


def create_sample_files():
    """Cria arquivos de exemplo se não existirem"""
    print("📄 Verificando arquivos de exemplo...")

    # Criar Excel de exemplo com pandas se não existir
    layout_file = Path("exemplos/layout_exemplo.xlsx")
    if not layout_file.exists():
        import pandas as pd

        layout_data = {
            'Campo': ['CODIGO_CLIENTE', 'NOME_CLIENTE', 'CPF', 'DATA_NASCIMENTO', 'TELEFONE', 'EMAIL', 'VALOR_CREDITO', 'STATUS'],
            'Posicao_Inicio': [1, 11, 41, 52, 60, 71, 121, 131],
            'Tamanho': [10, 30, 11, 8, 11, 50, 10, 1],
            'Tipo': ['NUMERO', 'TEXTO', 'NUMERO', 'DATA', 'NUMERO', 'TEXTO', 'DECIMAL', 'TEXTO'],
            'Obrigatorio': ['S', 'S', 'S', 'N', 'N', 'N', 'S', 'S'],
            'Formato': ['', '', '', 'YYYYMMDD', '', '', '2', '']
        }

        df = pd.DataFrame(layout_data)
        df.to_excel(layout_file, index=False)
        print(f"✅ Criado: {layout_file}")

    print("✅ Arquivos de exemplo prontos!")


def main():
    """Função principal de setup"""
    print("🚀 Configurando Validador de Documentos Sequenciais...")

    # Criar diretórios necessários
    Path("exemplos").mkdir(exist_ok=True)
    Path("relatorios").mkdir(exist_ok=True)

    # Instalar dependências
    if not install_requirements():
        sys.exit(1)

    # Criar arquivos de exemplo
    create_sample_files()

    # Executar testes
    if not run_tests():
        print("⚠️ Alguns testes falharam, mas a instalação pode continuar")

    print("\n🎉 Setup concluído!")
    print("\n📖 Como usar:")
    print("python main.py -l exemplos/layout_exemplo.xlsx -a exemplos/dados_exemplo.txt")
    print("\n📚 Para mais informações:")
    print("python main.py --help")


if __name__ == "__main__":
    main()