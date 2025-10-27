# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos Essenciais

### Inicializar Aplicação Web
```bash
# Opção 1: Script Python (recomendado)
python start_web.py

# Opção 2: Script Bash (desenvolvimento)
./iniciar.sh
```

### Interface CLI
```bash
# Validação básica
python main.py -l layout.xlsx -a dados.txt

# Com limite de erros
python main.py -l layout.xlsx -a dados.txt --max-erros 100

# Informações do layout apenas
python main.py -l layout.xlsx --info-layout
```

### Testes
```bash
# Executar todos os testes
python run_tests.py

# Ou usando pytest
pytest tests/
```

### Frontend (desenvolvimento)
```bash
cd frontend
npm install        # Instalar dependências
npm run dev         # Servidor de desenvolvimento
npm run build       # Build para produção
```

### Backend API
```bash
# Iniciar apenas a API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Arquitetura do Sistema

Este é um validador de documentos sequenciais (arquivos TXT) baseado em layouts Excel, com três interfaces principais:

### Core Python (src/)
- **layout_parser.py**: Parsing de arquivos Excel para definição de layouts
- **layout_normalizer.py**: Normalização e mapeamento inteligente de layouts com estruturas variadas
- **file_validator.py**: Validação linha por linha de arquivos TXT
- **validators.py**: Validadores específicos por tipo de campo (TEXTO, NUMERO, DATA, DECIMAL)
- **report_generator.py**: Geração de relatórios em Excel, CSV e texto
- **models.py**: Modelos de dados e enums

### API REST (api/)
- **main.py**: Aplicação FastAPI com endpoints para validação, mapeamento e exportação
- **models.py**: Modelos Pydantic para API
- Endpoints principais: `/api/validar-arquivo`, `/api/mapear-layout`, `/api/layout-export`

### Frontend Vue.js (frontend/)
- **App.vue**: Componente principal com navegação
- **views/**: Páginas principais (Dashboard, Validador, Mapeamento)
- **components/**: Componentes reutilizáveis (FileUpload, ResultsDisplay, etc.)
- **services/**: Cliente HTTP para comunicação com API
- **stores/**: Estado global com Pinia

## Fluxo de Dados Principal

1. **Upload de Layout Excel**: Arquivo é processado pelo `LayoutParser`
2. **Mapeamento Inteligente**: `layout_normalizer` mapeia colunas com nomes variados para padrão canônico
3. **Validação de Arquivo**: `ValidadorArquivo` processa linha por linha usando validadores específicos
4. **Geração de Relatório**: `GeradorRelatorio` cria relatórios detalhados com estatísticas

## Recursos Avançados

### Mapeamento Automático de Layouts
- Sistema de cache por assinatura de cabeçalhos
- Sugestões automáticas para colunas não reconhecidas
- Normalização de tipos (NUM → NUMERO, TXT → TEXTO)
- Geração automática de posições quando ausentes

### Sistema de Validação
- Suporte a 4 tipos: TEXTO, NUMERO, DATA, DECIMAL
- Validação de obrigatoriedade por campo
- Formatos específicos para datas (YYYYMMDD, etc.)
- Limite configurável de erros por validação

### Interface Web
- Dashboard com gráficos de estatísticas
- Upload via drag-and-drop
- Visualização de erros em tempo real
- Download de relatórios em múltiplos formatos
- Design responsivo com Tailwind CSS

## Estrutura de Arquivos

- `main.py`: Interface CLI principal
- `start_web.py`: Inicializador da aplicação web
- `iniciar.sh`: Script de desenvolvimento (backend + frontend)
- `requirements.txt`: Dependências Python
- `temp_uploads/`: Uploads temporários
- `relatorios_web/`: Relatórios gerados pela interface web
- `exemplos/`: Arquivos de exemplo para testes

## URLs da Aplicação
- Frontend: http://localhost:8000 (quando servido pelo backend)
- API: http://localhost:8000/api
- Documentação API: http://localhost:8000/docs
- Frontend dev: http://localhost:3000 (apenas em desenvolvimento)