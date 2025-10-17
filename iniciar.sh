#!/bin/bash

echo "🚀 Inicializando Validador de Documentos..."
echo "=========================================="

# Função para limpar processos ao sair
cleanup() {
    echo ""
    echo "🛑 Encerrando serviços..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Serviços encerrados!"
    exit 0
}

# Capturar Ctrl+C
trap cleanup SIGINT

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale o Python3 primeiro."
    exit 1
fi

# Verificar se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Instale o Node.js primeiro."
    exit 1
fi

echo "📦 Verificando dependências do backend..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ Arquivo requirements.txt não encontrado!"
    exit 1
fi

# Instalar dependências Python se necessário
echo "🔧 Instalando dependências Python..."
pip3 install -r requirements.txt > /dev/null 2>&1

echo "📦 Verificando dependências do frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "🔧 Instalando dependências Node.js..."
    npm install
fi

echo ""
echo "🌐 Iniciando Backend (FastAPI)..."
cd ..
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "🎨 Iniciando Frontend (Vue.js)..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Serviços iniciados com sucesso!"
echo "📍 URLs disponíveis:"
echo "   🔗 Frontend: http://localhost:3000"
echo "   🔗 Backend:  http://localhost:8000"
echo "   📖 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Para parar os serviços, pressione Ctrl+C"
echo ""

# Aguardar processos
wait $BACKEND_PID $FRONTEND_PID