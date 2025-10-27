from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Dict, Any, Optional, List

# Adicionar src ao path
src_path = str(Path(__file__).parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.layout_parser import LayoutParser
from src.layout_normalizer import (
    map_layout_file, normalize_dataframe, suggest_mapping, analyze_mapping,
    CANONICAL_COLUMNS, headers_signature, get_cached_mapping, save_cached_mapping,
    list_excel_sheets, find_header_row
)
from src.file_validator import ValidadorArquivo
from src.multi_record_validator import MultiRecordValidator
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
            tipo=campo.tipo.value,
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
async def validar_layout(
    layout_file: UploadFile = File(...),
    sheet_name: Optional[int] = Form(None)
):
    """Valida e retorna informações de um arquivo de layout Excel (suporte multi-registro)

    Args:
        layout_file: Arquivo Excel
        sheet_name: Índice da aba (0=primeira, 1=segunda, etc.). Se None, usa aba 1 (layout detalhado).
    """
    if not layout_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")

    temp_layout = None
    try:
        # Salvar arquivo temporário
        temp_layout = UPLOAD_DIR / f"layout_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{layout_file.filename}"
        with open(temp_layout, "wb") as buffer:
            content = await layout_file.read()
            buffer.write(content)

        # Tentar carregar como multi-registro primeiro
        try:
            sheet_index = sheet_name if sheet_name is not None else 1  # Default para aba 1
            multi_validator = MultiRecordValidator(str(temp_layout), sheet_index)

            # Criar layout combinado com TODOS os campos de TODOS os tipos
            todos_campos = []
            for tipo, layout in sorted(multi_validator.layouts_por_tipo.items()):
                todos_campos.extend(layout.campos)

            # Criar layout combinado
            layout_combinado = Layout(
                nome=f"Layout Multi-Registro ({len(multi_validator.layouts_por_tipo)} tipos)",
                campos=todos_campos,
                tamanho_linha=540  # Tamanho padrão
            )

            return converter_layout_para_response(layout_combinado)

        except Exception as multi_error:
            # Fallback para método antigo se multi-registro falhar
            print(f"Multi-registro falhou: {multi_error}, tentando método antigo...")
            parser = LayoutParser()
            sheet_index = sheet_name if sheet_name is not None else 0
            layout = parser.parse_excel(str(temp_layout), sheet_name=sheet_index)
            return converter_layout_para_response(layout)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar layout: {str(e)}")
    finally:
        # Limpar arquivo temporário
        if temp_layout and temp_layout.exists():
            os.remove(temp_layout)


@app.post("/api/listar-abas-excel")
async def listar_abas_excel(layout_file: UploadFile = File(...)):
    """Lista todas as abas disponíveis em um arquivo Excel"""
    if not layout_file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")

    temp_layout = UPLOAD_DIR / f"sheets_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{layout_file.filename}"
    try:
        content = await layout_file.read()
        with open(temp_layout, "wb") as buffer:
            buffer.write(content)

        result = list_excel_sheets(str(temp_layout))

        return {
            "sheets": result.sheets,
            "default_sheet": result.default_sheet,
            "total_sheets": len(result.sheets)
        }
    except Exception as e:
        import traceback
        error_detail = f"Erro ao listar abas do Excel: {str(e)}"
        print(f"Erro ao listar abas: {error_detail}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=error_detail)
    finally:
        if temp_layout.exists():
            os.remove(temp_layout)


@app.post("/api/mapear-layout")
async def mapear_layout(
    layout_file: UploadFile = File(...),
    sheet_name: Optional[int] = Form(None)
):
    """Realiza mapeamento automático das colunas de um layout Excel sem validar estrutura completa.
    Retorna cache se já existir para a assinatura de cabeçalhos.

    Args:
        layout_file: Arquivo Excel
        sheet_name: Índice da aba (0=primeira, 1=segunda, etc.). Se None, usa primeira aba.
    """
    if not layout_file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Arquivo deve ser Excel (.xlsx ou .xls)")
    temp_layout = UPLOAD_DIR / f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{layout_file.filename}"
    try:
        content = await layout_file.read()
        with open(temp_layout, "wb") as buffer:
            buffer.write(content)
        import pandas as pd

        # Usar sheet_name para ler cabeçalhos
        sheet_index = sheet_name if sheet_name is not None else 0

        # Detectar linha de cabeçalho automaticamente
        header_row = find_header_row(str(temp_layout), sheet_index)
        df_head = pd.read_excel(temp_layout, nrows=0, sheet_name=sheet_index, header=header_row)
        signature = headers_signature(list(df_head.columns))
        cached = get_cached_mapping(signature)

        # Se cache não tem normalized_rows ou original_samples, regenerar
        needs_regen = cached and (not cached.get("normalized_rows") or not cached.get("original_samples"))

        result = map_layout_file(str(temp_layout), sheet_name=sheet_index) if (not cached or needs_regen) else None
        
        # Se cached não possui novos campos manter compatibilidade
        response = {
            "signature": signature,
            "cached": cached is not None and not needs_regen,
            "mapping": cached["mapping"] if (cached and not needs_regen) else result.mapping,
            "analysis": cached["analysis"] if (cached and not needs_regen) else result.analysis,
            "warnings": cached.get("warnings", []) if (cached and not needs_regen) else result.warnings,
            "sample": cached.get("sample", []) if (cached and not needs_regen) else result.sample,
            "canonical_columns": CANONICAL_COLUMNS,
            "original_samples": cached.get("original_samples", {}) if (cached and not needs_regen) else result.original_samples,
            "normalized_rows": cached.get("normalized_rows", []) if (cached and not needs_regen) else result.normalized_rows,
            "original_headers": list(df_head.columns),
            "sheet_name": sheet_index,
            "selected_sheet": sheet_index
        }
        return response
    except Exception as e:
        import traceback
        error_detail = f"Erro ao mapear layout: {str(e)}"
        print(f"Erro no mapeamento de layout: {error_detail}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=error_detail)
    finally:
        if temp_layout.exists():
            os.remove(temp_layout)


class SaveMappingRequest(BaseModel):  # type: ignore
    signature: str
    mapping: Dict[str, Optional[str]]
    analysis: Dict[str, Any]
    sample: List[Dict[str, Any]] = []
    warnings: List[str] = []
    original_samples: Dict[str, List[str]] = {}
    normalized_rows: List[Dict[str, Any]] = []


@app.post("/api/layout-mappings")
async def salvar_mapping(data: SaveMappingRequest):
    """Salva mapeamento customizado no cache."""
    save_cached_mapping(data.signature, data.dict())
    return {"saved": True}


class CustomCampo(BaseModel):  # type: ignore
    nome: str
    posicao_inicio: int
    tamanho: int
    tipo: str
    obrigatorio: bool = False
    formato: Optional[str] = None


class ExportLayoutRequest(BaseModel):  # type: ignore
    nome: str
    campos: List[CustomCampo]
    signature: Optional[str] = None


LAYOUT_EXPORT_DIR = Path("data/layouts")
LAYOUT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(nome: str) -> str:
    import re, unicodedata
    nome_norm = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii')
    nome_norm = re.sub(r'[^A-Za-z0-9]+', '-', nome_norm).strip('-').lower()
    return nome_norm or 'layout'


@app.post("/api/layout-export")
async def exportar_layout(req: ExportLayoutRequest):
    """Gera arquivo Excel do layout customizado e retorna URL de download."""
    try:
        if not req.campos:
            raise HTTPException(status_code=400, detail="Lista de campos vazia")
        # Reusar lógica de layout_custom para validar
        from types import SimpleNamespace
        campos_objs = []
        tamanho_linha = 0
        for c in req.campos:
            pos_fim = c.posicao_inicio + c.tamanho - 1
            tamanho_linha = max(tamanho_linha, pos_fim)
            campos_objs.append(SimpleNamespace(
                nome=c.nome,
                posicao_inicio=c.posicao_inicio,
                posicao_fim=pos_fim,
                tamanho=c.tamanho,
                tipo=SimpleNamespace(value=c.tipo.upper()),
                obrigatorio=c.obrigatorio,
                formato=c.formato
            ))
        layout_fake = SimpleNamespace(nome=req.nome, campos=campos_objs, tamanho_linha=tamanho_linha)
        layout_response = converter_layout_para_response(layout_fake)

        # Construir DataFrame canônico
        import pandas as pd
        rows = []
        for c in layout_response.campos:
            rows.append({
                'Campo': c.nome,
                'Posicao_Inicio': c.posicao_inicio,
                'Tamanho': c.tamanho,
                'Tipo': c.tipo,
                'Obrigatorio': 'S' if c.obrigatorio else 'N',
                'Formato': c.formato or ''
            })
        df = pd.DataFrame(rows, columns=['Campo','Posicao_Inicio','Tamanho','Tipo','Obrigatorio','Formato'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        slug = _slugify(req.nome)
        signature_part = f"_{req.signature}" if req.signature else ''
        filename = f"layout_normalizado_{slug}{signature_part}_{timestamp}.xlsx"
        file_path = LAYOUT_EXPORT_DIR / filename
        df.to_excel(file_path, index=False)
        return {
            'saved': True,
            'filename': filename,
            'download_url': f"/api/layout-export/download/{filename}",
            'layout': layout_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao exportar layout: {str(e)}")


@app.get("/api/layout-export/download/{filename}")
async def baixar_layout_exportado(filename: str):
    file_path = LAYOUT_EXPORT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(str(file_path), filename=filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.get("/api/layout-mappings/{signature}")
async def obter_mapping(signature: str):
    cached = get_cached_mapping(signature)
    if not cached:
        raise HTTPException(status_code=404, detail="Mapping não encontrado")
    return cached


class CustomLayoutRequest(BaseModel):  # type: ignore
    nome: str
    campos: List[CustomCampo]


@app.post("/api/layout-custom")
async def layout_custom(data: CustomLayoutRequest):
    """Recebe layout customizado (após usuário editar colunas) e retorna LayoutResponse compatível."""
    try:
        # Validar campos básicos
        if not data.campos:
            raise HTTPException(status_code=400, detail="Lista de campos vazia")
        # Construir objeto fake similar ao LayoutParser
        from types import SimpleNamespace
        campos_objs = []
        tamanho_linha = 0
        for c in data.campos:
            if c.posicao_inicio <= 0 or c.tamanho <= 0:
                raise HTTPException(status_code=400, detail=f"Campo {c.nome}: posição e tamanho devem ser > 0")
            pos_fim = c.posicao_inicio + c.tamanho - 1
            tamanho_linha = max(tamanho_linha, pos_fim)
            tipo_upper = c.tipo.upper()
            if tipo_upper not in [t.value for t in TipoCampo]:
                raise HTTPException(status_code=400, detail=f"Tipo inválido: {c.tipo}")
            campos_objs.append(SimpleNamespace(
                nome=c.nome,
                posicao_inicio=c.posicao_inicio,
                posicao_fim=pos_fim,
                tamanho=c.tamanho,
                tipo=SimpleNamespace(value=tipo_upper),
                obrigatorio=c.obrigatorio,
                formato=c.formato
            ))
        layout_fake = SimpleNamespace(nome=data.nome, campos=campos_objs, tamanho_linha=tamanho_linha)
        return converter_layout_para_response(layout_fake)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar layout customizado: {str(e)}")


@app.post("/api/validar-arquivo")
async def validar_arquivo_completo(
    layout_file: UploadFile = File(...),
    data_file: UploadFile = File(...),
    max_erros: int = Form(default=None),
    sheet_name: Optional[int] = Form(None)
):
    """Valida arquivo completo e retorna resultados detalhados

    Args:
        layout_file: Arquivo Excel com layout
        data_file: Arquivo TXT com dados
        max_erros: Máximo de erros antes de parar validação
        sheet_name: Índice da aba (0=primeira, 1=segunda, etc.). Se None, usa primeira aba.
    """
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

        # Usar MultiRecordValidator para suportar todos os tipos de registro
        sheet_index = sheet_name if sheet_name is not None else 1  # Default para aba 1 (layout detalhado)
        validador = MultiRecordValidator(str(temp_layout), sheet_index)
        resultado = validador.validar_arquivo(str(temp_data), max_erros)

        # Para compatibilidade, criar um layout fictício baseado no primeiro tipo disponível
        if validador.layouts_por_tipo:
            primeiro_tipo = sorted(validador.layouts_por_tipo.keys())[0]
            layout = validador.layouts_por_tipo[primeiro_tipo]
        else:
            # Fallback para o método antigo se não conseguir carregar tipos
            parser = LayoutParser()
            layout = parser.parse_excel(str(temp_layout), sheet_name=sheet_index)

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