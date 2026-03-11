#!/usr/bin/env bash
# Script de build para o Render
set -o errexit

# 1. Instalar dependencias Python
pip install -r requirements.txt

# 2. Instalar Node.js e buildar frontend
cd frontend
npm install
npm run build
cd ..

# 3. Criar diretorio de uploads temporarios
mkdir -p temp_uploads
