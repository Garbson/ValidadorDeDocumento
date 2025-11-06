from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import os
import sys
import io
import base64
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
from src.enhanced_validator import EnhancedValidator
from src.multi_record_validator import MultiRecordValidator
from src.structural_comparator import ComparadorEstruturalArquivos
from src.report_generator import GeradorRelatorio
from src.models import TipoCampo, Layout

from .models import (
    LayoutResponse, CampoLayoutResponse, TipoCampoAPI,
    ResultadoValidacaoResponse, ErroValidacaoResponse,
    EstatisticasResponse, ValidacaoCompleta,
    StatusResponse, ErrorResponse, RegistroPreviewResponse,
    DiferencaEstruturalCampoResponse, DiferencaEstruturalLinhaResponse,
    ResultadoComparacaoEstruturalResponse, ComparacaoEstruturalCompleta,
    ResultadoCalculosResponse, TotaisCalculadosResponse, EstatisticasFaturasResponse
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


def _extrair_linhas_completas(caminho: str) -> Dict[int, str]:
    """Lê arquivo e mapeia numero_linha -> conteúdo bruto (com padding original)."""
    linhas: Dict[int, str] = {}
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            for i, linha in enumerate(f, 1):
                linhas[i] = linha.rstrip('\n\r')
    except UnicodeDecodeError:
        with open(caminho, 'r', encoding='latin-1') as f:
            for i, linha in enumerate(f, 1):
                linhas[i] = linha.rstrip('\n\r')
    return linhas


def _gerar_estatisticas_faturas_do_enhanced(ev: EnhancedValidator) -> EstatisticasFaturasResponse:
    stats = ev._gerar_estatisticas_faturas()
    # Calcular métricas de NF usando os grupos e erros presentes
    total_nfs = stats.get('total_notas_fiscais', 0)
    nfs_com_erro = set()
    # Mapear linhas com erro por NF via grupos
    linhas_com_erro = set()
    # Tentar obter erros do último resultado produzido: não está diretamente disponível aqui;
    # então inferimos por presença de divergências de total (56) no agrupamento não é possível aqui.
    # Alternativa robusta: considerar NF válida se houve registro 56 e nenhum erro TOTAL_* associado a esse grupo.
    # Como não temos os erros aqui, aproximamos: todas as NF presentes são consideradas "validadas" por padrão.
    total_validas = total_nfs - len(nfs_com_erro)
    taxa_sucesso = (total_validas / total_nfs * 100) if total_nfs > 0 else 0.0

    # Converter duplicatas para o modelo de resposta
    from .models import DuplicataNFResponse
    duplicatas_response = []
    for dup in stats.get('duplicatas_detalhes', []):
        duplicatas_response.append(DuplicataNFResponse(
            linha=dup['linha'],
            fatura=dup['fatura'],
            nf=dup['nf'],
            combinacao=dup['combinacao']
        ))

    return EstatisticasFaturasResponse(
        total_faturas=stats.get('total_faturas', 0),
        total_notas_fiscais=total_nfs,
        total_combinacoes_unicas=stats.get('total_combinacoes_unicas', 0),
        total_duplicatas=stats.get('total_duplicatas', 0),
        faturas_detalhes=stats.get('faturas_detalhes', {}),
        duplicatas_detalhes=duplicatas_response if duplicatas_response else [],
        total_nfs_validas=total_validas,
        total_nfs_com_erro=len(nfs_com_erro),
        taxa_sucesso_nf=taxa_sucesso
    )


@app.post("/api/validar-calculos")
async def validar_calculos(
    layout_file: UploadFile = File(...),
    data_file: UploadFile = File(...),
    sheet_name: Optional[int] = Form(None)
):
    """Valida cálculos e totalizadores (sem arquivo base), retornando erros e a linha completa de cada ocorrência."""
    if not layout_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Layout deve ser Excel (.xlsx ou .xls)")
    if not data_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Arquivo de dados deve ser TXT")

    temp_layout = None
    temp_data = None
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Salvar uploads
        temp_layout = UPLOAD_DIR / f"layout_{timestamp}_{layout_file.filename}"
        with open(temp_layout, "wb") as buffer:
            buffer.write(await layout_file.read())

        temp_data = UPLOAD_DIR / f"data_{timestamp}_{data_file.filename}"
        with open(temp_data, "wb") as buffer:
            buffer.write(await data_file.read())

        # Carregar layout (aba definida ou 0)
        parser = LayoutParser()
        sheet_index = sheet_name if sheet_name is not None else 0
        layout = parser.parse_excel(str(temp_layout), sheet_name=sheet_index)

        # Rodar EnhancedValidator sem limite de erros
        ev = EnhancedValidator(layout)
        resultado = ev.validar_arquivo(str(temp_data))

        # Converter resultados básicos
        resultado_response = converter_resultado_para_response(resultado)

        # Linhas completas: capturar apenas as com erro
        linhas_raw = _extrair_linhas_completas(str(temp_data))
        linhas_com_erro: Dict[int, str] = {}
        for erro in resultado.erros:
            if erro.linha not in linhas_com_erro and erro.linha in linhas_raw:
                # Pad para tamanho de linha do layout para coerência visual
                linha = linhas_raw[erro.linha]
                if len(linha) < layout.tamanho_linha:
                    linha = linha.ljust(layout.tamanho_linha)
                linhas_com_erro[erro.linha] = linha

        # Preparar extras: totais
        totais_resp = TotaisCalculadosResponse(valores=dict(ev.totais_acumulados))

        # Converter grupos por NF para resposta serializável (inclui conteúdo das linhas do grupo)
        grupos_resp: Dict[str, Any] = {}
        for (fatura, nf), dados in ev.grupos_nf.items():
            key = f"{fatura}|{nf}"
            # Mapear conteúdo bruto das linhas do grupo (com padding)
            linhas_conteudo: Dict[int, str] = {}
            for ln in dados.get('linhas', []):
                if ln in linhas_raw:
                    linha = linhas_raw[ln]
                    if len(linha) < layout.tamanho_linha:
                        linha = linha.ljust(layout.tamanho_linha)
                    linhas_conteudo[ln] = linha
            grupos_resp[key] = {
                'linhas': dados.get('linhas', []),
                'contribuintes_por_total': dados.get('contribuintes_por_total', {}),
                'linhas_conteudo': linhas_conteudo
            }

        # Estatísticas por NF - usar contador igual SEFAZ (por linha processada = registros 01)
        total_nfs = ev.total_registros_01  # Cada registro 01 = 1 NFCOM processada
        nfs_com_erro: set[str] = set()

        def extrair_grupo_key_descricao(desc: str) -> Optional[str]:
            if not desc:
                return None
            import re as _re
            m = _re.search(r"Fatura\s+(\S+)\s*\|\s*NF\s+(\S+)", desc)
            if m:
                return f"{m.group(1)}|{m.group(2)}"
            return None

        # Mapear rapidamente linha->grupo
        linha_para_grupo: Dict[int, str] = {}
        for gk, gdata in grupos_resp.items():
            for ln in gdata.get('linhas', []):
                linha_para_grupo[ln] = gk

        for erro in resultado.erros:
            gk = extrair_grupo_key_descricao(getattr(erro, 'descricao', ''))
            if not gk:
                gk = linha_para_grupo.get(getattr(erro, 'linha', -1))
            if gk:
                nfs_com_erro.add(gk)

        total_nfs_com_erro = len(nfs_com_erro)

        # TODO: Integrar dados reais da SEFAZ quando disponível
        # SEFAZ real: 148 aprovadas + 363 rejeitadas = 511 total
        # Arquivo TXT: 502 registros 01
        # Por enquanto, usar contagem do arquivo TXT
        total_nfs_validas = max(0, total_nfs - total_nfs_com_erro)
        taxa_sucesso_nf = (total_nfs_validas / total_nfs * 100) if total_nfs > 0 else 0.0

        stats_resp = EstatisticasFaturasResponse(
            total_faturas=len(ev.notas_fiscais_por_fatura),
            total_notas_fiscais=total_nfs,
            total_combinacoes_unicas=len(ev.combinacoes_fatura_nf),  # 343 combinações únicas
            total_duplicatas=len(ev.duplicatas_fatura_nf),  # Duplicatas encontradas
            faturas_detalhes=ev._gerar_estatisticas_faturas().get('faturas_detalhes', {}),
            duplicatas_detalhes=ev.duplicatas_fatura_nf,  # Lista das duplicatas
            total_nfs_validas=total_nfs_validas,
            total_nfs_com_erro=total_nfs_com_erro,
            taxa_sucesso_nf=taxa_sucesso_nf
        )

        return ResultadoCalculosResponse(
            resultado_basico=resultado_response,
            totais=totais_resp,
            estatisticas_faturas=stats_resp,
            linhas_completas_com_erro=linhas_com_erro,
            grupos_por_nf=grupos_resp,
            layout=converter_layout_para_response(layout)
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro durante validação de cálculos: {str(e)}")
    finally:
        if temp_layout and temp_layout.exists():
            os.remove(temp_layout)
        if temp_data and temp_data.exists():
            os.remove(temp_data)


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


def converter_resultado_comparacao_para_response(resultado) -> ResultadoComparacaoEstruturalResponse:
    """Converte resultado de comparação estrutural para response da API"""
    diferencas_response = []

    for diferenca_linha in resultado.diferencas_por_linha:
        campos_response = []
        for campo_diff in diferenca_linha.diferencas_campos:
            campos_response.append(DiferencaEstruturalCampoResponse(
                nome_campo=campo_diff.nome_campo,
                posicao_inicio=campo_diff.posicao_inicio,
                posicao_fim=campo_diff.posicao_fim,
                valor_base=campo_diff.valor_base,
                valor_validado=campo_diff.valor_validado,
                tipo_diferenca=campo_diff.tipo_diferenca,
                descricao=campo_diff.descricao
            ))

        diferencas_response.append(DiferencaEstruturalLinhaResponse(
            numero_linha=diferenca_linha.numero_linha,
            tipo_registro=diferenca_linha.tipo_registro,
            arquivo_base_linha=diferenca_linha.arquivo_base_linha,
            arquivo_validado_linha=diferenca_linha.arquivo_validado_linha,
            diferencas_campos=campos_response,
            total_diferencas=diferenca_linha.total_diferencas
        ))

    return ResultadoComparacaoEstruturalResponse(
        total_linhas_comparadas=resultado.total_linhas_comparadas,
        linhas_com_diferencas=resultado.linhas_com_diferencas,
        linhas_identicas=resultado.linhas_identicas,
        diferencas_por_linha=diferencas_response,
        taxa_identidade=resultado.taxa_identidade
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
            sheet_index = sheet_name if sheet_name is not None else 0  # Default para aba 0 (primeira aba)
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
        # Gerar Excel em memória
        df = pd.DataFrame(rows, columns=['Campo','Posicao_Inicio','Tamanho','Tipo','Obrigatorio','Formato'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        slug = _slugify(req.nome)
        signature_part = f"_{req.signature}" if req.signature else ''
        filename = f"layout_normalizado_{slug}{signature_part}_{timestamp}.xlsx"

        # Converter Excel para base64
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        excel_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            'saved': True,
            'filename': filename,
            'excel_data': excel_base64,  # Dados para localStorage
            'layout': layout_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao exportar layout: {str(e)}")




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

        # Detectar se é layout normalizado ou multi-registro
        sheet_index = sheet_name if sheet_name is not None else 0  # Default para aba 0 (primeira aba)
        
        # Variáveis para preview de registros
        preview_registros_data = []
        tipos_encontrados = []

        def is_normalized_layout(filename):
            """Detecta se é um layout normalizado pelo nome do arquivo"""
            return 'layout_normalizado' in filename.lower()

        def is_multi_record_layout(layout_path, sheet_idx):
            """Detecta se é um layout multi-registro"""
            try:
                import pandas as pd
                df = pd.read_excel(layout_path, sheet_name=sheet_idx, header=1)
                df_clean = df[df['Campo'].notna() & (df['Campo'] != 'Campo')].copy()

                # Verificar se há campos com padrão NFE##-
                tipos_encontrados = set()
                for _, row in df_clean.iterrows():
                    campo_nome = str(row['Campo'])
                    if 'NFE' in campo_nome and '-' in campo_nome:
                        tipo = campo_nome.split('-')[0].replace('NFE', '')
                        if tipo.isdigit():
                            tipos_encontrados.add(tipo)

                return len(tipos_encontrados) > 1
            except:
                return False

        def detect_data_file_structure(data_path):
            """Detecta se o arquivo de dados tem estrutura multi-registro (linha por linha)"""
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    tipos_encontrados = set()
                    for i, linha in enumerate(f):
                        if i >= 20:  # Verificar apenas primeiras 20 linhas
                            break
                        linha = linha.strip()
                        if len(linha) >= 2:
                            tipo = linha[:2]
                            if tipo.isdigit():
                                tipos_encontrados.add(tipo)
                    return len(tipos_encontrados) > 1
            except:
                return False

        # LÓGICA CORRIGIDA: Detectar estrutura do arquivo de dados primeiro
        data_is_multi_record = detect_data_file_structure(str(temp_data))
        layout_is_normalized = is_normalized_layout(layout_file.filename)
        layout_is_multi_record = is_multi_record_layout(str(temp_layout), sheet_index)

        if data_is_multi_record:
            # Arquivo de dados tem múltiplos tipos - SEMPRE usar MultiRecordValidator
            if layout_is_normalized:
                # Layout normalizado + arquivo multi-registro = ERRO DE CONCEITO!
                # Precisa usar o layout original multi-registro
                raise HTTPException(
                    status_code=400,
                    detail="ERRO: Layout normalizado não pode ser usado com arquivo multi-registro. Use o layout Excel original."
                )
            else:
                # Usar MultiRecordValidator com layout original
                validador = MultiRecordValidator(str(temp_layout), sheet_index)
                resultado = validador.validar_arquivo(str(temp_data), max_erros)
                
                # Gerar preview de registros parseados
                preview_registros_data, tipos_encontrados = validador.parsear_linhas_preview(str(temp_data), max_linhas=20)

                # Criar layout combinado com TODOS os campos de TODOS os tipos para preview
                if validador.layouts_por_tipo:
                    # Combinar todos os campos de todos os tipos
                    from src.models import CampoLayout
                    todos_campos = []

                    for tipo in sorted(validador.layouts_por_tipo.keys()):
                        layout_tipo = validador.layouts_por_tipo[tipo]
                        for campo in layout_tipo.campos:
                            # Prefixar com tipo para identificação no preview
                            campo_preview = CampoLayout(
                                nome=f"[Tipo {tipo}] {campo.nome}",
                                posicao_inicio=campo.posicao_inicio,
                                tamanho=campo.tamanho,
                                tipo=campo.tipo,
                                obrigatorio=campo.obrigatorio,
                                formato=campo.formato
                            )
                            todos_campos.append(campo_preview)

                    # Criar layout combinado para preview
                    layout = Layout(
                        nome=f"Multi-Registro ({len(validador.layouts_por_tipo)} tipos)",
                        campos=todos_campos,
                        tamanho_linha=540
                    )
                else:
                    # Fallback para o método antigo se não conseguir carregar tipos
                    parser = LayoutParser()
                    layout = parser.parse_excel(str(temp_layout), sheet_name=sheet_index)
        else:
            # Arquivo tem estrutura simples/concatenada
            if layout_is_normalized:
                # Layout normalizado + arquivo simples = OK
                parser = LayoutParser()
                layout = parser.parse_excel(str(temp_layout), sheet_name=0)  # Layouts normalizados usam aba 0
                validador = ValidadorArquivo(layout)
                resultado = validador.validar_arquivo(str(temp_data), max_erros)
            else:
                # Layout original + arquivo simples = usar validador padrão
                parser = LayoutParser()
                layout = parser.parse_excel(str(temp_layout), sheet_name=sheet_index)
                validador = ValidadorArquivo(layout)
                resultado = validador.validar_arquivo(str(temp_data), max_erros)

        # Converter para responses
        layout_response = converter_layout_para_response(layout)
        resultado_response = converter_resultado_para_response(resultado)
        estatisticas_response = gerar_estatisticas(resultado)

        # Gerar dados do relatório em memória
        gerador = GeradorRelatorio(resultado, layout)
        dados_relatorio = gerador.gerar_dados_relatorio()

        # Preparar dados de preview de registros se for multi-registro
        preview_registros = None
        tipos_registro = None
        
        if data_is_multi_record and not layout_is_normalized:
            # Converter preview para response
            preview_registros = [
                RegistroPreviewResponse(
                    linha=reg['linha'],
                    tipo_registro=reg['tipo_registro'],
                    campos=reg['campos']
                )
                for reg in preview_registros_data
            ]
            tipos_registro = tipos_encontrados

        validacao_completa = ValidacaoCompleta(
            layout=layout_response,
            resultado=resultado_response,
            estatisticas=estatisticas_response,
            timestamp=timestamp,
            dados_relatorio=dados_relatorio,
            preview_registros=preview_registros,
            tipos_registro_encontrados=tipos_registro
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








@app.post("/api/comparar-estrutural")
async def comparar_arquivos_estrutural(
    layout_file: UploadFile = File(...),
    arquivo_base: UploadFile = File(...),
    arquivo_validado: UploadFile = File(...),
    sheet_name: Optional[int] = Form(None)
):
    """Realiza comparação estrutural entre dois arquivos baseado em um layout

    Args:
        layout_file: Arquivo Excel com layout
        arquivo_base: Arquivo TXT de referência (base)
        arquivo_validado: Arquivo TXT a ser comparado
        sheet_name: Índice da aba (0=primeira, 1=segunda, etc.). Se None, usa primeira aba.
    """
    if not layout_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Layout deve ser Excel (.xlsx ou .xls)")

    if not arquivo_base.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Arquivo base deve ser TXT")

    if not arquivo_validado.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Arquivo a ser validado deve ser TXT")

    temp_layout = None
    temp_base = None
    temp_validado = None

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Salvar arquivos temporários
        temp_layout = UPLOAD_DIR / f"layout_{timestamp}_{layout_file.filename}"
        with open(temp_layout, "wb") as buffer:
            content = await layout_file.read()
            buffer.write(content)

        temp_base = UPLOAD_DIR / f"base_{timestamp}_{arquivo_base.filename}"
        with open(temp_base, "wb") as buffer:
            content = await arquivo_base.read()
            buffer.write(content)

        temp_validado = UPLOAD_DIR / f"validado_{timestamp}_{arquivo_validado.filename}"
        with open(temp_validado, "wb") as buffer:
            content = await arquivo_validado.read()
            buffer.write(content)

        # Carregar layout
        sheet_index = sheet_name if sheet_name is not None else 0

        # Verificar se é layout multi-registro (não suportado para comparação estrutural)
        def is_multi_record_layout(layout_path, sheet_idx):
            try:
                import pandas as pd
                df = pd.read_excel(layout_path, sheet_name=sheet_idx, header=1)
                df_clean = df[df['Campo'].notna() & (df['Campo'] != 'Campo')].copy()

                tipos_encontrados = set()
                for _, row in df_clean.iterrows():
                    campo_nome = str(row['Campo'])
                    if 'NFE' in campo_nome and '-' in campo_nome:
                        tipo = campo_nome.split('-')[0].replace('NFE', '')
                        if tipo.isdigit():
                            tipos_encontrados.add(tipo)

                return len(tipos_encontrados) > 1
            except:
                return False

        if is_multi_record_layout(str(temp_layout), sheet_index):
            raise HTTPException(
                status_code=400,
                detail="Comparação estrutural não suportada para layouts multi-registro. Use layouts normalizados."
            )

        # Carregar layout usando parser padrão
        parser = LayoutParser()
        layout = parser.parse_excel(str(temp_layout), sheet_name=sheet_index)

        # Executar comparação estrutural
        comparador = ComparadorEstruturalArquivos(layout)
        resultado_comparacao = comparador.comparar_arquivos(str(temp_base), str(temp_validado))

        # Gerar relatório textual
        relatorio_texto = comparador.gerar_relatorio_completo(resultado_comparacao)

        # Preparar dados para localStorage
        dados_comparacao = {
            'timestamp': timestamp,
            'data_comparacao': datetime.now().isoformat(),
            'relatorio_texto': relatorio_texto,
            'layout_nome': layout.nome
        }

        # Converter para responses
        layout_response = converter_layout_para_response(layout)
        resultado_response = converter_resultado_comparacao_para_response(resultado_comparacao)

        return ComparacaoEstruturalCompleta(
            layout=layout_response,
            resultado_comparacao=resultado_response,
            relatorio_texto=relatorio_texto,
            timestamp=timestamp,
            dados_comparacao=dados_comparacao
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro durante comparação estrutural: {str(e)}")

    finally:
        # Limpar arquivos temporários
        for temp_file in [temp_layout, temp_base, temp_validado]:
            if temp_file and temp_file.exists():
                os.remove(temp_file)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)