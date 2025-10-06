from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Dict, Any

# Adicionar src ao path
src_path = str(Path(__file__).parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.layout_parser import LayoutParser
from src.file_validator import ValidadorArquivo
from src.report_generator import GeradorRelatorio
from src.models import TipoCampo

from .models import (
    LayoutResponse, CampoLayoutResponse, TipoCampoAPI,
    ResultadoValidacaoResponse, ErroValidacaoResponse,
    EstatisticasResponse, ValidacaoCompleta,
    StatusResponse, ErrorResponse
)

app = FastAPI(
    title="Validador de Documentos Sequenciais API",
    description="API para validação de arquivos sequenciais baseado em layouts Excel",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos do frontend
frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_path.exists():
    # Montar assets
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")
    # Montar outros arquivos estáticos
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

# Diretório temporário para uploads
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Diretório para relatórios
REPORTS_DIR = Path("relatorios_web")
REPORTS_DIR.mkdir(exist_ok=True)


def converter_layout_para_response(layout) -> LayoutResponse:
    """Converte layout interno para response da API"""
    campos_response = []
    for campo in layout.campos:
        campos_response.append(CampoLayoutResponse(
            nome=campo.nome,
            posicao_inicio=campo.posicao_inicio,
            posicao_fim=campo.posicao_fim,
            tamanho=campo.tamanho,
            tipo=TipoCampoAPI(campo.tipo.value),
            obrigatorio=campo.obrigatorio,
            formato=campo.formato
        ))

    return LayoutResponse(
        nome=layout.nome,
        campos=campos_response,
        tamanho_linha=layout.tamanho_linha
    )


def converter_resultado_para_response(resultado) -> ResultadoValidacaoResponse:
    """Converte resultado interno para response da API"""
    erros_response = []
    for erro in resultado.erros:
        erros_response.append(ErroValidacaoResponse(
            linha=erro.linha,
            campo=erro.campo,
            valor_encontrado=erro.valor_encontrado,
            erro_tipo=erro.erro_tipo,
            descricao=erro.descricao,
            valor_esperado=erro.valor_esperado
        ))

    return ResultadoValidacaoResponse(
        total_linhas=resultado.total_linhas,
        linhas_validas=resultado.linhas_validas,
        linhas_com_erro=resultado.linhas_com_erro,
        erros=erros_response,
        taxa_sucesso=resultado.taxa_sucesso
    )


def gerar_estatisticas(resultado) -> EstatisticasResponse:
    """Gera estatísticas detalhadas"""
    tipos_erro = Counter(erro.erro_tipo for erro in resultado.erros)
    campos_com_erro = Counter(erro.campo for erro in resultado.erros)

    return EstatisticasResponse(
        total_linhas=resultado.total_linhas,
        linhas_validas=resultado.linhas_validas,
        linhas_com_erro=resultado.linhas_com_erro,
        taxa_sucesso=resultado.taxa_sucesso,
        total_erros=len(resultado.erros),
        tipos_erro=dict(tipos_erro),
        campos_com_erro=dict(campos_com_erro)
    )


@app.get("/")
async def root():
    """Página inicial - redireciona para frontend se disponível"""
    if frontend_path.exists():
        return FileResponse(str(frontend_path / "index.html"))
    return {"message": "Validador de Documentos Sequenciais API"}


@app.get("/vite.svg")
async def vite_svg():
    """Serve vite.svg"""
    from fastapi import Response
    # Criar um SVG simples se não existir
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="iconify iconify--logos" width="31.88" height="32" preserveAspectRatio="xMidYMid meet" viewBox="0 0 256 257"><defs><linearGradient id="IconifyId1813088fe1fbc01fb466" x1="-.828%" x2="57.636%" y1="7.652%" y2="78.411%"><stop offset="0%" stop-color="#41D1FF"></stop><stop offset="100%" stop-color="#BD34FE"></stop></linearGradient><linearGradient id="IconifyId1813088fe1fbc01fb467" x1="43.376%" x2="50.316%" y1="2.242%" y2="89.03%"><stop offset="0%" stop-color="#FFEA83"></stop><stop offset="8.333%" stop-color="#FFDD35"></stop><stop offset="100%" stop-color="#FFA800"></stop></linearGradient></defs><path fill="url(#IconifyId1813088fe1fbc01fb466)" d="M255.153 37.938L134.897 252.976c-2.483 4.44-8.862 4.466-11.382.048L.875 37.958c-2.746-4.814 1.371-10.646 6.827-9.67l120.385 21.517a6.537 6.537 0 0 0 2.322-.004l117.867-21.483c5.438-.991 9.574 4.796 6.877 9.62Z"></path><path fill="url(#IconifyId1813088fe1fbc01fb467)" d="M185.432.063L96.44 17.501a3.268 3.268 0 0 0-2.634 3.014l-5.474 92.456a3.268 3.268 0 0 0 3.997 3.378l24.777-5.718c2.318-.535 4.413 1.507 3.936 3.838l-7.361 36.047c-.495 2.426 1.782 4.5 4.151 3.78l15.304-4.649c2.372-.72 4.652 1.36 4.15 3.788l-11.698 56.621c-.732 3.542 3.979 5.473 5.943 2.437l1.313-2.028l72.516-144.72c1.215-2.423-.88-5.186-3.54-4.672l-25.505 4.922c-2.396.462-4.435-1.77-3.759-4.114l16.646-57.705c.677-2.35-1.37-4.583-3.769-4.113Z"></path></svg>'''
    return Response(content=svg_content, media_type="image/svg+xml")


@app.get("/api/health")
async def health_check():
    """Verificação de saúde da API"""
    return StatusResponse(status="healthy", message="API funcionando corretamente")


@app.post("/api/validar-layout")
async def validar_layout(layout_file: UploadFile = File(...)):
    """Valida e retorna informações de um arquivo de layout Excel"""
    if not layout_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")

    try:
        # Salvar arquivo temporário
        temp_layout = UPLOAD_DIR / f"layout_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{layout_file.filename}"
        with open(temp_layout, "wb") as buffer:
            content = await layout_file.read()
            buffer.write(content)

        # Processar layout
        parser = LayoutParser()
        layout = parser.parse_excel(str(temp_layout))

        # Limpar arquivo temporário
        os.remove(temp_layout)

        return converter_layout_para_response(layout)

    except Exception as e:
        # Limpar arquivo se der erro
        if temp_layout.exists():
            os.remove(temp_layout)
        raise HTTPException(status_code=400, detail=f"Erro ao processar layout: {str(e)}")


@app.post("/api/validar-arquivo")
async def validar_arquivo_completo(
    layout_file: UploadFile = File(...),
    data_file: UploadFile = File(...),
    max_erros: int = Form(default=None)
):
    """Valida arquivo completo e retorna resultados detalhados"""
    if not layout_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Layout deve ser Excel (.xlsx ou .xls)")

    if not data_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Arquivo de dados deve ser TXT")

    temp_layout = None
    temp_data = None

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Salvar arquivos temporários
        temp_layout = UPLOAD_DIR / f"layout_{timestamp}_{layout_file.filename}"
        with open(temp_layout, "wb") as buffer:
            content = await layout_file.read()
            buffer.write(content)

        temp_data = UPLOAD_DIR / f"data_{timestamp}_{data_file.filename}"
        with open(temp_data, "wb") as buffer:
            content = await data_file.read()
            buffer.write(content)

        # Processar layout
        parser = LayoutParser()
        layout = parser.parse_excel(str(temp_layout))

        # Validar arquivo
        validador = ValidadorArquivo(layout)
        resultado = validador.validar_arquivo(str(temp_data), max_erros)

        # Converter para responses
        layout_response = converter_layout_para_response(layout)
        resultado_response = converter_resultado_para_response(resultado)
        estatisticas_response = gerar_estatisticas(resultado)

        # Gerar relatório para download posterior
        gerador = GeradorRelatorio(resultado, layout)
        relatorio_paths = gerador.gerar_relatorio_completo(str(REPORTS_DIR))

        validacao_completa = ValidacaoCompleta(
            layout=layout_response,
            resultado=resultado_response,
            estatisticas=estatisticas_response,
            timestamp=timestamp
        )

        return validacao_completa

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro durante validação: {str(e)}")

    finally:
        # Limpar arquivos temporários
        if temp_layout and temp_layout.exists():
            os.remove(temp_layout)
        if temp_data and temp_data.exists():
            os.remove(temp_data)


@app.get("/api/download-relatorio/{timestamp}")
async def download_relatorio(timestamp: str, formato: str = "excel"):
    """Download de relatório gerado"""
    if formato not in ["excel", "texto", "csv"]:
        raise HTTPException(status_code=400, detail="Formato deve ser: excel, texto ou csv")

    # Buscar arquivo de relatório
    if formato == "excel":
        pattern = f"relatorio_validacao_*_{timestamp}.xlsx"
        extensao = ".xlsx"
    elif formato == "texto":
        pattern = f"relatorio_validacao_*_{timestamp}.txt"
        extensao = ".txt"
    else:  # csv
        pattern = f"relatorio_validacao_*_{timestamp}.csv"
        extensao = ".csv"

    import glob
    arquivos = glob.glob(str(REPORTS_DIR / pattern))

    if not arquivos:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    arquivo_path = arquivos[0]
    filename = f"relatorio_validacao_{timestamp}{extensao}"

    return FileResponse(
        path=arquivo_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@app.get("/api/relatorios")
async def listar_relatorios():
    """Lista relatórios disponíveis"""
    relatorios = []
    for arquivo in REPORTS_DIR.glob("relatorio_validacao_*.xlsx"):
        timestamp = arquivo.stem.split('_')[-1]
        relatorios.append({
            "timestamp": timestamp,
            "arquivo": arquivo.name,
            "data_criacao": datetime.fromtimestamp(arquivo.stat().st_mtime).isoformat()
        })

    return {"relatorios": sorted(relatorios, key=lambda x: x["data_criacao"], reverse=True)}


@app.delete("/api/relatorios/{timestamp}")
async def deletar_relatorio(timestamp: str):
    """Deleta relatórios de um timestamp específico"""
    import glob

    deleted = 0
    for pattern in [f"*_{timestamp}.xlsx", f"*_{timestamp}.txt", f"*_{timestamp}.csv"]:
        arquivos = glob.glob(str(REPORTS_DIR / pattern))
        for arquivo in arquivos:
            os.remove(arquivo)
            deleted += 1

    return {"message": f"{deleted} arquivos deletados"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)