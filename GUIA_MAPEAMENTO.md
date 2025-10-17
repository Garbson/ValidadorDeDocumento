# Guia de Uso: Mapeamento e Exportação de Layout

## Visão Geral

O sistema de mapeamento permite transformar arquivos Excel com estruturas variadas em layouts padronizados que podem ser usados pelo validador.

## Fluxo Completo

### 1. Preparação do Arquivo Excel

Seu arquivo Excel pode ter colunas com nomes variados, como:
- `CAMPO`, `CAMPO MOBILE`, `ATRIBUTO FCT`
- `TAM`, `TAMANHO`
- `TIPO`, `TIPO DE DADOS`
- `PREENCH`, `PREENCHIMENTO`, `OBRIGATORIO`
- `POSICAO`, `POS`, `POSICAO INICIAL`

**Nota:** A coluna `Posicao_Inicio` é opcional! Se não existir, o sistema irá gerá-la automaticamente com base no tamanho cumulativo dos campos.

### 2. Upload e Mapeamento Automático

1. Acesse a página **Mapeamento** no menu
2. Faça upload do arquivo Excel
3. Clique em **Mapear**
4. O sistema irá:
   - Analisar os cabeçalhos
   - Sugerir mapeamentos baseados em sinônimos e similaridade
   - Gerar posições iniciais se ausentes
   - Mostrar exemplos das colunas originais

### 3. Revisão e Ajuste

Na tela de mapeamento você pode:
- Ver sugestões automáticas de cada coluna
- Alterar mapeamentos usando os dropdowns
- Ver exemplos dos dados originais de cada coluna
- Criar colunas manualmente (opção "Nova Coluna Manual")
- Verificar warnings e completude dos campos obrigatórios

### 4. Confirmação e Exportação

Ao clicar em **Confirmar Mapeamento**:

1. O sistema salva o mapeamento no cache (pela assinatura dos cabeçalhos)
2. Gera um arquivo Excel padronizado com colunas:
   - `Campo`: nome do campo
   - `Posicao_Inicio`: posição inicial (gerada automaticamente se necessário)
   - `Tamanho`: tamanho do campo
   - `Tipo`: tipo normalizado (TEXTO, NUMERO, DATA, DECIMAL)
   - `Obrigatorio`: S ou N
   - `Formato`: formato opcional
3. Retorna um layout JSON com metadados completos

### 5. Usando o Layout Exportado

Você tem **3 opções**:

#### Opção A: Download Manual
1. Clique em **Download Layout Excel**
2. Salve o arquivo `.xlsx` gerado
3. Use este arquivo na página **Validador**

#### Opção B: Usar Direto no Validador (Recomendado)
1. Clique em **Usar no Validador**
2. Você será redirecionado automaticamente
3. O layout já estará carregado

#### Opção C: API Direta
```bash
# O endpoint retorna JSON com URL de download
POST /api/layout-export
{
  "nome": "Meu Layout",
  "campos": [...],
  "signature": "abc123"
}

# Resposta
{
  "saved": true,
  "filename": "layout_normalizado_meu-layout_abc123_20251008_195351.xlsx",
  "download_url": "/api/layout-export/download/layout_normalizado_meu-layout_abc123_20251008_195351.xlsx",
  "layout": { ... }
}
```

## Tipos de Campo Válidos

O sistema suporta os seguintes tipos (normalizados automaticamente):

| Tipo Final | Sinônimos Aceitos |
|-----------|------------------|
| `TEXTO` | TXT, TEXT, STRING, CHAR |
| `NUMERO` | NUM, INT, INTEGER, NUMBER |
| `DECIMAL` | DEC, FLOAT, DOUBLE, VALOR |
| `DATA` | DATE, DT |

**Importante:** Qualquer tipo não reconhecido será convertido para `TEXTO` automaticamente.

## Cache de Mapeamentos

O sistema mantém um cache inteligente:
- Cada conjunto único de cabeçalhos gera uma assinatura SHA-256
- Mapeamentos são salvos em `data/layout_mappings.json`
- Na próxima vez que você carregar um arquivo com os **mesmos cabeçalhos**, o mapeamento anterior será recuperado
- Você pode ajustar e re-salvar conforme necessário

## Arquivos Gerados

Todos os layouts exportados são salvos em:
```
data/layouts/layout_normalizado_{slug}_{signature}_{timestamp}.xlsx
```

Exemplo:
```
data/layouts/layout_normalizado_layout-teste_test123_20251008_195351.xlsx
```

## Debugging

Se algo não funcionar:

1. **Verifique o console do navegador** - logs detalhados são exibidos
2. **Verifique os tipos** - devem ser TEXTO, NUMERO, DATA ou DECIMAL
3. **Verifique campos obrigatórios** - Campo, Posicao_Inicio, Tamanho, Tipo e Obrigatorio devem estar mapeados
4. **Teste o endpoint diretamente**:
   ```bash
   python3 test_export_endpoint.py
   ```

## Exemplo Completo

**Arquivo Original:**
```
CAMPO MOBILE | TAM | TIPO DE DADOS | PREENCH | DOMINIO
CODIGO       | 10  | NUM           | S       | -
NOME         | 50  | TXT           | S       | -
VALOR        | 15  | DEC           | N       | -
```

**Após Mapeamento:**
```
Campo  | Posicao_Inicio | Tamanho | Tipo    | Obrigatorio | Formato
CODIGO | 1              | 10      | NUMERO  | S           |
NOME   | 11             | 50      | TEXTO   | S           |
VALOR  | 61             | 15      | DECIMAL | N           |
```

## Próximos Passos

Depois de gerar o layout:
1. Vá para a página **Validador**
2. Carregue o layout Excel exportado (ou clique em "Usar no Validador")
3. Carregue seu arquivo de dados `.txt`
4. Execute a validação
5. Visualize erros e baixe relatórios

## Troubleshooting

### "Exportação falhou"
- Verifique se todos os campos obrigatórios foram mapeados
- Verifique se os tipos são válidos
- Veja mensagem de erro detalhada no console

### "Nenhum campo válido para exportação"
- Certifique-se de que as linhas normalizadas contêm Campo, Posicao_Inicio e Tamanho
- Verifique warnings do mapeamento

### Backend não está respondendo
- Certifique-se de que o servidor está rodando em `http://localhost:8000`
- Execute: `python3 run_dev.py`

## Suporte

Para problemas ou dúvidas, verifique:
- Logs do backend (terminal onde rodou `run_dev.py`)
- Console do navegador (F12 → Console)
- Arquivo de teste: `test_export_endpoint.py`
