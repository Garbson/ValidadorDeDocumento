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
import pandas as pd

# Adicionar src ao path
# UPDATED: 2024-11-30 - Forçar reload após correção arredondamento
src_path = str(Path(__file__).parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.layout_parser import LayoutParser
from src.layout_normalizer import list_excel_sheets
from src.file_validator import ValidadorArquivo
from src.enhanced_validator import EnhancedValidator
from src.multi_record_validator import MultiRecordValidator
from src.structural_comparator import ComparadorEstruturalArquivos
from src.report_generator import GeradorRelatorio
from src.models import TipoCampo, Layout
from src.printcenter_parser import parse_printcenter_layout
from src.scenario_identifier import identificar_cenarios, buscar_faturas_por_campo

from .models import (
    LayoutResponse, CampoLayoutResponse, TipoCampoAPI,
    ResultadoValidacaoResponse, ErroValidacaoResponse,
    EstatisticasResponse, ValidacaoCompleta,
    StatusResponse, ErrorResponse, RegistroPreviewResponse,
    DiferencaEstruturalCampoResponse, DiferencaEstruturalLinhaResponse,
    ResultadoComparacaoEstruturalResponse, ComparacaoEstruturalCompleta,
    FaturaComparadaResponse,
    ResultadoCalculosResponse, TotaisCalculadosResponse, EstatisticasFaturasResponse,
    FaturaCenarioResponse, CenarioIdentificadoResponse,
    CampoLayoutPrintCenterResponse, LayoutPrintCenterResponse,
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

# Diretório PrintCenter
PRINTCENTER_DIR = Path(__file__).parent.parent / "printcenter"
import json



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

        # PROTEÇÃO: Para arquivos muito grandes, limitar dados retornados
        MAX_ERROS_DETALHES = 1000  # Máximo de erros com detalhes completos
        MAX_LINHAS_CONTEUDO = 5000  # Máximo de linhas de conteúdo
        arquivo_grande = resultado.total_linhas > 10000 or len(resultado.erros) > MAX_ERROS_DETALHES
        
        # Linhas completas: capturar apenas as com erro (limitado para arquivos grandes)
        linhas_raw = _extrair_linhas_completas(str(temp_data))
        linhas_com_erro: Dict[int, str] = {}
        
        if arquivo_grande:
            # Para arquivos grandes, retornar apenas primeiros N erros com detalhes
            erros_limitados = resultado.erros[:MAX_ERROS_DETALHES]
            for erro in erros_limitados:
                if erro.linha not in linhas_com_erro and erro.linha in linhas_raw:
                    linha = linhas_raw[erro.linha]
                    if len(linha) < layout.tamanho_linha:
                        linha = linha.ljust(layout.tamanho_linha)
                    linhas_com_erro[erro.linha] = linha
        else:
            # Para arquivos normais, retornar todos
            for erro in resultado.erros:
                if erro.linha not in linhas_com_erro and erro.linha in linhas_raw:
                    linha = linhas_raw[erro.linha]
                    if len(linha) < layout.tamanho_linha:
                        linha = linha.ljust(layout.tamanho_linha)
                    linhas_com_erro[erro.linha] = linha

        # Preparar extras: totais
        totais_resp = TotaisCalculadosResponse(valores=dict(ev.totais_acumulados))

        # Converter grupos por NF para resposta serializável (inclui conteúdo das linhas do grupo)
        grupos_resp: Dict[str, Any] = {}
        
        if arquivo_grande:
            # Para arquivos grandes, limitar grupos retornados
            grupos_limitados = dict(list(ev.grupos_nf.items())[:100])  # Primeiros 100 grupos
            for (fatura, nf), dados in grupos_limitados.items():
                key = f"{fatura}|{nf}"
                # Não incluir conteúdo das linhas para economizar memória
                grupos_resp[key] = {
                    'linhas': dados.get('linhas', []),
                    'contribuintes_por_total': dados.get('contribuintes_por_total', {}),
                    'linhas_conteudo': {}  # Vazio para arquivos grandes
                }
        else:
            # Para arquivos normais, retornar tudo
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
            # Ignorar erros de totalizador (56, 57, 99) e header (00) pois afetam o arquivo todo, não NFs específicas
            tipo_erro = getattr(erro, 'erro_tipo', '')
            if tipo_erro.startswith('TOTAL_') or tipo_erro.startswith('RT_TOTAL_') or tipo_erro == 'TRAILER_QTD_NF' or tipo_erro == 'HEADER_QTD_NF':
                continue
            
            gk = extrair_grupo_key_descricao(getattr(erro, 'descricao', ''))
            if not gk:
                gk = linha_para_grupo.get(getattr(erro, 'linha', -1))
            if gk:
                nfs_com_erro.add(gk)

        total_nfs_com_erro = len(nfs_com_erro)

        # Calcular NFCOMs válidas e taxa de sucesso
        # Exemplo: 10 NFCOMs totais, 2 com erro = 8 válidas = 80% de taxa de sucesso
        total_nfs_validas = max(0, total_nfs - total_nfs_com_erro)
        taxa_sucesso_nf = (total_nfs_validas / total_nfs * 100) if total_nfs > 0 else 100.0

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


def _converter_linhas_para_response(linhas) -> List[DiferencaEstruturalLinhaResponse]:
    """Converte lista de DiferencaEstruturalLinha para response"""
    response = []
    for diferenca_linha in linhas:
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

        response.append(DiferencaEstruturalLinhaResponse(
            numero_linha=diferenca_linha.numero_linha,
            tipo_registro=diferenca_linha.tipo_registro,
            arquivo_base_linha=diferenca_linha.arquivo_base_linha,
            arquivo_validado_linha=diferenca_linha.arquivo_validado_linha,
            diferencas_campos=campos_response,
            total_diferencas=diferenca_linha.total_diferencas
        ))
    return response


def converter_resultado_comparacao_para_response(resultado) -> ResultadoComparacaoEstruturalResponse:
    """Converte resultado de comparação estrutural para response da API"""
    diferencas_response = _converter_linhas_para_response(resultado.diferencas_por_linha)

    # Converter faturas comparadas
    faturas_response = []
    for fatura in getattr(resultado, 'faturas_comparadas', []):
        faturas_response.append(FaturaComparadaResponse(
            conta_cliente=fatura.conta_cliente,
            cps_fatura=fatura.cps_fatura,
            todas_linhas=_converter_linhas_para_response(fatura.todas_linhas),
            diferencas_por_linha=_converter_linhas_para_response(fatura.diferencas_por_linha),
            total_linhas=fatura.total_linhas,
            linhas_com_diferencas=fatura.linhas_com_diferencas,
            linhas_identicas=fatura.linhas_identicas
        ))

    return ResultadoComparacaoEstruturalResponse(
        total_linhas_comparadas=resultado.total_linhas_comparadas,
        linhas_com_diferencas=resultado.linhas_com_diferencas,
        linhas_identicas=resultado.linhas_identicas,
        diferencas_por_linha=diferencas_response,
        taxa_identidade=resultado.taxa_identidade,
        contas_nao_encontradas=getattr(resultado, 'contas_nao_encontradas', []),
        faturas_comparadas=faturas_response
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




@app.get("/api/printcenter/config")
async def get_printcenter_config():
    """Retorna configuração do PrintCenter com lotes disponíveis"""
    config_path = PRINTCENTER_DIR / "config.json"
    lotes_dir = PRINTCENTER_DIR / "lotes"

    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Configuração do PrintCenter não encontrada")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Auto-detectar arquivos .txt na pasta lotes/ que não estão no config
    lotes_config = {l["arquivo"] for l in config.get("lotes", [])}
    lotes = list(config.get("lotes", []))

    if lotes_dir.exists():
        for arquivo in sorted(lotes_dir.iterdir()):
            if arquivo.is_file() and arquivo.name != ".gitkeep":
                arquivo_rel = f"lotes/{arquivo.name}"
                if arquivo_rel not in lotes_config:
                    lotes.append({
                        "nome": arquivo.name,
                        "arquivo": arquivo_rel
                    })

    # Verificar se layout existe
    layout_file = config.get("layout_file", "")
    layout_exists = (PRINTCENTER_DIR / layout_file).exists() if layout_file else False

    return {
        "layout_file": layout_file,
        "layout_exists": layout_exists,
        "sheet_index": config.get("sheet_index", 0),
        "lotes": lotes
    }


@app.post("/api/printcenter/upload-lote")
async def upload_lote_producao(
    arquivo: UploadFile = File(...)
):
    """Faz upload de um arquivo de produção para a pasta lotes/

    Permite que o usuário envie arquivos de produção grandes separadamente,
    sem precisar fazer upload durante a comparação. O arquivo fica salvo
    no servidor e aparece no dropdown de lotes.
    """
    lotes_dir = PRINTCENTER_DIR / "lotes"
    lotes_dir.mkdir(parents=True, exist_ok=True)

    if not arquivo.filename:
        raise HTTPException(status_code=400, detail="Arquivo é obrigatório")

    destino = lotes_dir / arquivo.filename

    try:
        # Salvar o arquivo em chunks para não sobrecarregar a memória
        chunk_size = 1024 * 1024  # 1MB por chunk
        total_bytes = 0
        with open(destino, "wb") as buffer:
            while True:
                chunk = await arquivo.read(chunk_size)
                if not chunk:
                    break
                buffer.write(chunk)
                total_bytes += len(chunk)

        # Contar linhas e faturas para feedback
        total_linhas = 0
        total_faturas = 0
        with open(destino, 'r', encoding='utf-8', errors='replace') as f:
            for linha in f:
                total_linhas += 1
                if linha.startswith('01'):
                    total_faturas += 1

        tamanho_mb = total_bytes / (1024 * 1024)

        return {
            "sucesso": True,
            "mensagem": f"Arquivo '{arquivo.filename}' salvo com sucesso na pasta lotes/",
            "arquivo": f"lotes/{arquivo.filename}",
            "nome": arquivo.filename,
            "tamanho_mb": round(tamanho_mb, 2),
            "total_linhas": total_linhas,
            "total_faturas": total_faturas
        }
    except Exception as e:
        # Limpar arquivo parcialmente salvo em caso de erro
        if destino.exists():
            os.remove(destino)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")


@app.delete("/api/printcenter/lote/{nome_arquivo:path}")
async def remover_lote(nome_arquivo: str):
    """Remove um arquivo de lote da pasta lotes/"""
    lote_path = PRINTCENTER_DIR / "lotes" / nome_arquivo

    if not lote_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo '{nome_arquivo}' não encontrado")

    if lote_path.name == ".gitkeep":
        raise HTTPException(status_code=400, detail="Não é possível remover o arquivo .gitkeep")

    try:
        os.remove(lote_path)
        return {"sucesso": True, "mensagem": f"Arquivo '{nome_arquivo}' removido com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover arquivo: {str(e)}")


# ============================================================
# CONSTANTES E FUNÇÕES AUXILIARES PARA COMPARAÇÃO PRINTCENTER
# ============================================================

# Mapeamento de tipos DEV modelo62 -> PROD
MAPA_TIPOS_MODELO62 = {'10': '40', '11': '46', '12': '48', '13': '50'}
# Mapeamento inverso: PROD -> DEV modelo62
MAPA_DEV_PARA_PROD = {v: k for k, v in MAPA_TIPOS_MODELO62.items()}
# Tipos DEV que não têm correspondência no PROD (modelo62)
TIPOS_DEV_SEM_CORRESPONDENCIA_M62 = {'42', '85'}
# Tipos PROD que não são comparados (modelo22)
TIPOS_PROD_SEM_COMPARACAO_M22 = {'14'}
# Tipos que identificam modelo 62 no DEV
TIPOS_MODELO_62 = {'40', '42', '44', '46', '48', '50', '52'}
# Tipos de cobilling (iguais em DEV e PROD)
TIPOS_COBILLING = {'15', '16', '17', '18', '19'}

# Campos ignorados por modelo
CAMPOS_IGNORADOS_MODELO62 = {
    'NFCOM01-Número da CPS/Fatura', 'NFCOM01-Data da Emissão', 'NFCOM00-Data da Geração do Arquivo',
    'NFCOM40-Data Emissão da Nota Fiscal', 'NFCOM40-Tipo de Registro = 40', 'NFCOM46-Tipo de Registro = 46',
    'NFCOM48-Tipo de Registro = 48', 'NFCOM50-Tipo de Registro = 50', 'NFCOM50-Filler',
}
CAMPOS_IGNORADOS_MODELO22 = {
    'NFCOM01-Número da CPS/Fatura', 'NFCOM01-Data da Emissão', 'NFCOM00-Data da Geração do Arquivo',
    'NFCOM10-Data Emissão da Nota Fiscal', 'NFCOM10-Número da CPS/Fatura', 'NFCOM15-Data Emissão da Nota Fiscal', 'NFCOM15-Número da CPS/Fatura',
}

# Hash-Code: ignorar se preenchido no DEV, reportar se vazio
CAMPOS_HASH_CODE = {'NFCOM13-Hash-Code editado', 'NFCOM19-Hash-Code operadora', 'NFCOM50-Hash-Code editado'}


def _detectar_modelo(linhas):
    """Detecta se o arquivo DEV é modelo 62 ou modelo 22.
    Modelo 62: arquivo DEV contém tipos 40, 42, 46, 48, 50
    Modelo 22: arquivo DEV contém tipos 10-14 (mesmos que PROD)
    """
    tipos_encontrados = set()
    for linha in linhas:
        if len(linha) >= 2:
            tipos_encontrados.add(linha[:2])
    if tipos_encontrados & TIPOS_MODELO_62:
        return 'modelo62'
    return 'modelo22'


def _ler_linhas_arquivo(caminho: str):
    """Lê todas as linhas de um arquivo, tentando utf-8 e latin-1."""
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return [l.rstrip('\n\r') for l in f]
    except UnicodeDecodeError:
        with open(caminho, 'r', encoding='latin-1') as f:
            return [l.rstrip('\n\r') for l in f]


def _construir_arquivo_alinhado(linhas_dev, linhas_prod, modelo):
    """Constrói arquivo DEV alinhado com o PROD para comparação linha a linha.
    
    Para modelo62: mapeia tipos DEV (40,46,48,50) para tipos PROD (10,11,12,13).
    Para modelo22: sem mapeamento, tipos iguais.
    Cobilling (15-19): sempre tipos iguais.
    
    Usa algoritmo de lookahead para lidar com quantidades diferentes de linhas por tipo.
    """
    resultado_dev = []
    resultado_prod = []
    
    i_dev = 0
    i_prod = 0
    
    while i_dev < len(linhas_dev) and i_prod < len(linhas_prod):
        linha_dev = linhas_dev[i_dev]
        linha_prod = linhas_prod[i_prod]
        
        tipo_dev = linha_dev[:2] if len(linha_dev) >= 2 else '??'
        tipo_prod = linha_prod[:2] if len(linha_prod) >= 2 else '??'
        
        # Determinar tipo esperado no PROD para o tipo DEV atual
        if modelo == 'modelo62' and tipo_dev in MAPA_DEV_PARA_PROD:
            tipo_prod_esperado = MAPA_DEV_PARA_PROD[tipo_dev]
        else:
            tipo_prod_esperado = tipo_dev
        
        # Pular tipos DEV sem correspondência (ex: 42 no modelo62)
        if modelo == 'modelo62' and tipo_dev in TIPOS_DEV_SEM_CORRESPONDENCIA_M62:
            i_dev += 1
            continue
        
        # Se os tipos batem (considerando mapeamento)
        if tipo_prod == tipo_prod_esperado:
            resultado_dev.append(linha_dev)
            resultado_prod.append(linha_prod)
            i_dev += 1
            i_prod += 1
        else:
            # Tipos não batem - usar lookahead para descobrir quem tem linhas extras
            JANELA = 20
            
            # Procurar tipo_prod_esperado à frente no PROD
            encontrou_no_prod = False
            for j in range(1, JANELA):
                if i_prod + j < len(linhas_prod):
                    tipo_futuro = linhas_prod[i_prod + j][:2] if len(linhas_prod[i_prod + j]) >= 2 else '??'
                    if tipo_futuro == tipo_prod_esperado:
                        encontrou_no_prod = True
                        # PROD tem linhas extras antes - adicionar como linhas sem correspondência DEV
                        for k in range(j):
                            resultado_dev.append('')  # Linha vazia no DEV
                            resultado_prod.append(linhas_prod[i_prod + k])
                        i_prod += j
                        break
            
            if not encontrou_no_prod:
                # Procurar se o tipo DEV atual aparece à frente no DEV
                encontrou_no_dev = False
                for j in range(1, JANELA):
                    if i_dev + j < len(linhas_dev):
                        tipo_futuro_dev = linhas_dev[i_dev + j][:2] if len(linhas_dev[i_dev + j]) >= 2 else '??'
                        if modelo == 'modelo62' and tipo_futuro_dev in MAPA_DEV_PARA_PROD:
                            tipo_futuro_mapeado = MAPA_DEV_PARA_PROD[tipo_futuro_dev]
                        else:
                            tipo_futuro_mapeado = tipo_futuro_dev
                        
                        if tipo_futuro_mapeado == tipo_prod:
                            encontrou_no_dev = True
                            # DEV tem linhas extras antes - pular
                            for k in range(j):
                                resultado_dev.append(linhas_dev[i_dev + k])
                                resultado_prod.append('')
                            i_dev += j
                            break
                
                if not encontrou_no_dev:
                    # Nenhum match encontrado, avançar ambos
                    resultado_dev.append(linha_dev)
                    resultado_prod.append(linha_prod)
                    i_dev += 1
                    i_prod += 1
    
    # Linhas restantes
    while i_dev < len(linhas_dev):
        resultado_dev.append(linhas_dev[i_dev])
        resultado_prod.append('')
        i_dev += 1
    
    while i_prod < len(linhas_prod):
        resultado_dev.append('')
        resultado_prod.append(linhas_prod[i_prod])
        i_prod += 1
    
    return resultado_dev, resultado_prod


def _extrair_mapa_faturas(caminho_arquivo: str):
    """Extrai mapa de faturas do arquivo.
    Cada fatura começa com tipo 01 e contém o código do cliente na posição [2:17].
    Retorna lista de dicts com numero_fatura, codigo_cliente, linhaInicio, linhaFim.
    """
    linhas = _ler_linhas_arquivo(caminho_arquivo)
    faturas = []
    fatura_atual = None
    
    for i, linha in enumerate(linhas, 1):
        if len(linha) >= 2:
            tipo = linha[:2]
            if tipo == '01':
                # Fecha fatura anterior
                if fatura_atual:
                    fatura_atual['linhaFim'] = i - 1
                    faturas.append(fatura_atual)
                
                # Nova fatura
                codigo_cliente = linha[2:17].strip() if len(linha) >= 17 else ''
                fatura_atual = {
                    'numero_fatura': len(faturas) + 1,
                    'codigo_cliente': codigo_cliente,
                    'linhaInicio': i,
                    'linhaFim': i
                }
    
    # Fecha última fatura
    if fatura_atual:
        fatura_atual['linhaFim'] = len(linhas)
        faturas.append(fatura_atual)
    
    return faturas
@app.post("/api/printcenter/comparar")
async def printcenter_comparar(
    arquivo_usuario: UploadFile = File(...),
    lote_arquivo: str = Form(default=""),
    arquivo_producao: UploadFile = File(default=None)
):
    """Compara arquivo do usuário com arquivo de produção (lote selecionado ou upload)"""
    config_path = PRINTCENTER_DIR / "config.json"

    if not config_path.exists():
        raise HTTPException(status_code=404, detail="Configuração do PrintCenter não encontrada")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validar layout
    layout_file_rel = config.get("layout_file", "")
    layout_path = PRINTCENTER_DIR / layout_file_rel
    if not layout_path.exists():
        raise HTTPException(status_code=400, detail=f"Arquivo de layout não encontrado: {layout_file_rel}. Coloque o arquivo na pasta printcenter/layout/")

    # Determinar arquivo de produção: upload ou lote
    tem_upload_producao = arquivo_producao is not None and arquivo_producao.filename
    tem_lote = lote_arquivo and lote_arquivo.strip()

    if not tem_upload_producao and not tem_lote:
        raise HTTPException(status_code=400, detail="É necessário selecionar um lote ou fazer upload de um arquivo de produção")

    if not arquivo_usuario.filename:
        raise HTTPException(status_code=400, detail="Arquivo do usuário é obrigatório")

    temp_usuario = None
    temp_producao = None

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_usuario = UPLOAD_DIR / f"printcenter_{timestamp}_{arquivo_usuario.filename}"
        with open(temp_usuario, "wb") as buffer:
            content = await arquivo_usuario.read()
            buffer.write(content)

        if tem_upload_producao:
            temp_producao = UPLOAD_DIR / f"printcenter_prod_{timestamp}_{arquivo_producao.filename}"
            with open(temp_producao, "wb") as buffer:
                content = await arquivo_producao.read()
                buffer.write(content)
            producao_path = str(temp_producao)
        else:
            lote_path = PRINTCENTER_DIR / lote_arquivo
            if not lote_path.exists():
                raise HTTPException(status_code=400, detail=f"Arquivo do lote não encontrado: {lote_arquivo}")
            producao_path = str(lote_path)

        sheet_index = config.get("sheet_index", 0)
        layout = parse_printcenter_layout(str(layout_path), sheet_name=sheet_index)

        # Detecção de modelo lendo apenas as primeiras linhas (economiza memória)
        def _detectar_modelo_streaming(caminho: str, max_linhas=100):
            for enc in ['utf-8', 'latin-1']:
                try:
                    with open(caminho, 'r', encoding=enc) as f:
                        for i, linha in enumerate(f):
                            if i >= max_linhas:
                                break
                            if "Hash-Code" in linha:
                                return "hashcode"
                            if "Fatura" in linha:
                                return "fatura"
                    return "padrao"
                except UnicodeDecodeError:
                    continue
            return "padrao"

        modelo_usuario = _detectar_modelo_streaming(str(temp_usuario))
        modelo_producao = _detectar_modelo_streaming(producao_path)

        # Mapa de faturas lendo em streaming (não carrega arquivo inteiro)
        def _extrair_mapa_faturas_streaming(caminho_arquivo: str):
            mapa = {}
            for enc in ['utf-8', 'latin-1']:
                try:
                    with open(caminho_arquivo, 'r', encoding=enc) as f:
                        for idx, linha in enumerate(f, 1):
                            linha = linha.rstrip('\n\r')
                            if "Fatura" in linha:
                                partes = linha.split()
                                fatura = partes[1] if len(partes) > 1 else ""
                                mapa[fatura] = idx
                    break
                except UnicodeDecodeError:
                    continue
            return mapa

        mapa_faturas_usuario = _extrair_mapa_faturas_streaming(str(temp_usuario))
        mapa_faturas_producao = _extrair_mapa_faturas_streaming(producao_path)

        # Hash-Code conditional comparison
        campos_ignorados = set(getattr(layout, 'campos_ignorados', []))
        campos_ignorar_se_preenchido = getattr(layout, 'campos_ignorar_se_preenchido', [])

        # Campos que sempre serão diferentes entre arquivos
        campos_ignorados.add('NFCOM01-Número da CPS/Fatura')
        campos_ignorados.add('NFCOM01-Data da Emissão')
        campos_ignorados.add('NFCOM00-Data da Geração do Arquivo')
        campos_ignorados.add('NFCOM01-Indicador do tipo de cobrança : Fatura')

        comparador = ComparadorEstruturalArquivos(layout,
            campos_ignorados=campos_ignorados,
            campos_ignorar_se_preenchido=campos_ignorar_se_preenchido
        )
        resultado_comparacao = comparador.comparar_arquivos_por_tipo_registro(
            producao_path,
            str(temp_usuario)
        )

        relatorio_texto = comparador.gerar_relatorio_completo(resultado_comparacao)
        dados_comparacao = {
            'timestamp': timestamp,
            'data_comparacao': datetime.now().isoformat(),
            'relatorio_texto': relatorio_texto,
            'layout_nome': layout.nome,
            'modelo_usuario': modelo_usuario,
            'modelo_producao': modelo_producao,
            'mapa_faturas_usuario': mapa_faturas_usuario,
            'mapa_faturas_producao': mapa_faturas_producao
        }
        layout_response = converter_layout_para_response(layout)
        resultado_response = converter_resultado_comparacao_para_response(resultado_comparacao)
        return ComparacaoEstruturalCompleta(
            layout=layout_response,
            resultado_comparacao=resultado_response,
            relatorio_texto=relatorio_texto,
            timestamp=timestamp,
            dados_comparacao=dados_comparacao
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na comparação PrintCenter: {str(e)}")
    finally:
        if temp_usuario and temp_usuario.exists():
            os.remove(temp_usuario)
        if temp_producao and temp_producao.exists():
            os.remove(temp_producao)


@app.post("/api/identificar-cenarios")
async def identificar_cenarios_endpoint(
    arquivo: UploadFile = File(...),
):
    """Identifica cenários (ICMS, ISS, Cobilling, etc.) nas faturas de um arquivo TXT.

    Não necessita de layout Excel - usa posições fixas para identificar
    tipos de registro e flags.
    """
    if not arquivo.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser TXT")

    temp_arquivo = None
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_arquivo = UPLOAD_DIR / f"cenarios_{timestamp}_{arquivo.filename}"
        with open(temp_arquivo, "wb") as buffer:
            content = await arquivo.read()
            buffer.write(content)

        resultado = identificar_cenarios(str(temp_arquivo))

        return CenarioIdentificadoResponse(
            cenarios_encontrados=resultado.cenarios_encontrados,
            contagem_por_cenario=resultado.contagem_por_cenario,
            faturas=[
                FaturaCenarioResponse(
                    conta_cliente=f.conta_cliente,
                    cps_fatura=f.cps_fatura,
                    cenarios=f.cenarios,
                    tipos_registro=f.tipos_registro,
                    linha_inicio=f.linha_inicio,
                    total_linhas=f.total_linhas,
                    debito_automatico=f.debito_automatico,
                    isencao=f.isencao,
                    aliquota_icms=f.aliquota_icms,
                    valor_isentos=f.valor_isentos,
                    retencao={
                        'percentual': f.retencao.percentual,
                        'valor': f.retencao.valor,
                        'tipo': f.retencao.tipo,
                        'detalhes': f.retencao.detalhes,
                        'texto_original': f.retencao.texto_original,
                    } if f.retencao else None,
                    mensagens=f.mensagens if f.mensagens else None,
                )
                for f in resultado.faturas
            ],
            total_faturas=resultado.total_faturas,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao identificar cenários: {str(e)}")
    finally:
        if temp_arquivo and temp_arquivo.exists():
            os.remove(temp_arquivo)


@app.get("/api/campos-layout")
async def get_campos_layout():
    """Retorna todos os campos do layout PrintCenter com código TT.NN.

    Usa o layout padrão em printcenter/layout/.
    """
    import re

    layout_dir = Path(__file__).parent.parent / "printcenter" / "layout"
    layout_files = list(layout_dir.glob("*.xlsx"))

    if not layout_files:
        raise HTTPException(status_code=404, detail="Nenhum layout PrintCenter encontrado na pasta printcenter/layout/")

    layout_path = layout_files[0]

    try:
        df_raw = pd.read_excel(str(layout_path), sheet_name=0, header=None)

        # Encontrar linha de cabeçalho
        header_row = None
        for idx, row in df_raw.iterrows():
            vals = [str(v).strip().lower().replace('ã', 'a').replace('á', 'a')
                    for v in row.values if pd.notna(v)]
            if 'campo' in vals:
                header_row = idx
                break

        if header_row is None:
            raise ValueError("Cabeçalho não encontrado no layout")

        df = pd.read_excel(str(layout_path), sheet_name=0, header=header_row)

        # Normalizar colunas
        col_map = {}
        for col in df.columns:
            col_norm = str(col).strip().lower().replace('ã', 'a').replace('á', 'a').replace('ç', 'c').replace('é', 'e').replace('ú', 'u')
            if col_norm == 'campo':
                col_map[col] = 'Campo'
            elif 'posic' in col_norm and 'de' in col_norm:
                col_map[col] = 'De'
            elif col_norm == 'de':
                col_map[col] = 'De'
            elif 'posic' in col_norm and 'ate' in col_norm:
                col_map[col] = 'Ate'
            elif col_norm in ('ate', 'ate'):
                col_map[col] = 'Ate'
            elif col_norm == 'picture':
                col_map[col] = 'Picture'
            elif 'conteudo' in col_norm or 'descri' in col_norm:
                col_map[col] = 'Conteudo'
        df = df.rename(columns=col_map)

        campo_pattern = re.compile(r'^(\d{2})\.(\d{2,3})$')
        campos = []
        tipos_registro = set()

        for _, row in df.iterrows():
            campo_val = str(row.get('Campo', '')).strip() if pd.notna(row.get('Campo')) else ''
            match = campo_pattern.match(campo_val)
            if not match:
                continue

            tipo_reg = match.group(1)
            tipos_registro.add(tipo_reg)

            try:
                pos_de = int(float(row['De']))
                pos_ate = int(float(row['Ate']))
            except (ValueError, TypeError):
                continue

            if pos_de <= 0 or pos_ate <= 0 or pos_ate < pos_de:
                continue

            tamanho = pos_ate - pos_de + 1
            picture = str(row.get('Picture', '')).strip() if pd.notna(row.get('Picture')) else ''
            conteudo = str(row.get('Conteudo', '')).strip() if pd.notna(row.get('Conteudo')) else f'Campo {campo_val}'
            nome_limpo = conteudo.split('\n')[0].split('(')[0].strip()
            if len(nome_limpo) > 80:
                nome_limpo = nome_limpo[:80]

            # Determinar tipo pelo picture
            tipo = 'TEXTO'
            if picture.startswith('9') and 'V' in picture:
                tipo = 'DECIMAL'
            elif picture.startswith('9'):
                tipo = 'NUMERO'

            campos.append(CampoLayoutPrintCenterResponse(
                codigo=campo_val,
                nome=nome_limpo,
                posicao_de=pos_de,
                posicao_ate=pos_ate,
                tamanho=tamanho,
                tipo=tipo,
                picture=picture,
                tipo_registro=tipo_reg,
            ))

        return LayoutPrintCenterResponse(
            campos=campos,
            tipos_registro=sorted(tipos_registro),
            total_campos=len(campos),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler layout: {str(e)}")


@app.post("/api/buscar-por-campo")
async def buscar_por_campo_endpoint(
    arquivo: UploadFile = File(...),
    tipo_registro: str = Form(...),
    posicao_de: int = Form(...),
    posicao_ate: int = Form(...),
    valor_busca: str = Form(...),
):
    """Busca faturas onde um campo específico contém o valor informado.

    Args:
        arquivo: Arquivo TXT com faturas
        tipo_registro: Tipo de registro do campo (ex: "01")
        posicao_de: Posição inicial (1-indexed)
        posicao_ate: Posição final (1-indexed)
        valor_busca: Valor a buscar (busca parcial, case-insensitive)
    """
    if not arquivo.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser TXT")

    temp_arquivo = None
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_arquivo = UPLOAD_DIR / f"busca_{timestamp}_{arquivo.filename}"
        with open(temp_arquivo, "wb") as buffer:
            content = await arquivo.read()
            buffer.write(content)

        resultados = buscar_faturas_por_campo(
            str(temp_arquivo), tipo_registro, posicao_de, posicao_ate, valor_busca
        )

        return {
            "total_encontradas": len(resultados),
            "valor_buscado": valor_busca,
            "campo": f"{tipo_registro}.XX (pos {posicao_de}-{posicao_ate})",
            "faturas": resultados,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na busca: {str(e)}")
    finally:
        if temp_arquivo and temp_arquivo.exists():
            os.remove(temp_arquivo)


# Catch-all: qualquer rota que não seja /api/* serve o index.html do frontend (Vue Router)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve o frontend para qualquer rota não-API (suporte ao Vue Router)"""
    if frontend_path.exists():
        # Se o arquivo existe no dist, servir diretamente
        file_path = frontend_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        # Caso contrário, servir index.html (Vue Router cuida do roteamento)
        return FileResponse(str(frontend_path / "index.html"))
    return {"message": "Frontend não encontrado"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)