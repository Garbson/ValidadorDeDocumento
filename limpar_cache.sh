#!/bin/bash
# Script para limpar cache de mapeamentos e layouts exportados

echo "🧹 Limpando cache do sistema de mapeamento..."

# Remover cache de mapeamentos
if [ -f "data/layout_mappings.json" ]; then
    rm data/layout_mappings.json
    echo "✅ Cache de mapeamentos removido: data/layout_mappings.json"
else
    echo "ℹ️  Nenhum cache de mapeamentos encontrado"
fi

# Remover layouts exportados (opcional)
if [ -d "data/layouts" ]; then
    count=$(ls -1 data/layouts/*.xlsx 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
        rm data/layouts/*.xlsx
        echo "✅ $count layout(s) exportado(s) removido(s)"
    else
        echo "ℹ️  Nenhum layout exportado encontrado"
    fi
else
    echo "ℹ️  Diretório data/layouts não existe"
fi

echo ""
echo "✨ Limpeza concluída!"
echo ""
echo "💡 Próximos passos:"
echo "   1. Recarregue a página do mapeamento no navegador"
echo "   2. Faça upload do arquivo Excel novamente"
echo "   3. O mapeamento será recriado com todos os campos atualizados"
