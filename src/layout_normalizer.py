import unicodedata
import difflib
import json
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd

CANONICAL_COLUMNS = [
    'Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio', 'Formato'
]

SYNONYMS = {
    'Campo': [
        'campo','nome_campo','nome','field','coluna','campo_nome','CAMPO','campo_mobile',
        'atributo','atributo_fct','nome_campo_netsms','campo_netsms','descricao_atributo'
    ],
    'Posicao_Inicio': [
        'posicao_inicio','inicio','start','pos_ini','posicao','inicio_pos','start_pos',
        'coluna_inicio','inicio_coluna','indice','index','idx'
    ],
    'Tamanho': [
        'tamanho','tam','length','len','qtd_caracteres','caracteres','tamanho_campo','TAMANHO',
        'tam_campo'
    ],
    'Tipo': [
        'tipo','type','categoria','formato_tipo','tipo_campo','TIPO'
    ],
    'Obrigatorio': [
        'obrigatorio','obrig','required','req','mandatory','obg','necessario','OBRIGATORIO','preench','preenchimento'
    ],
    'Formato': [
        'formato','pattern','mascara','mask','regex','dominio'
    ]
}

TIPO_NORMALIZATION = {
    'TXT': 'TEXTO', 'TEXT': 'TEXTO', 'STRING': 'TEXTO', 'CHAR': 'TEXTO',
    'VARCHAR': 'TEXTO', 'VARCHAR2': 'TEXTO', 'NVARCHAR': 'TEXTO',
    'NUM': 'NUMERO', 'INT': 'NUMERO', 'INTEGER': 'NUMERO', 'NUMBER': 'NUMERO',
    'BIGINT': 'NUMERO', 'SMALLINT': 'NUMERO',
    'DEC': 'DECIMAL', 'FLOAT': 'DECIMAL', 'DOUBLE': 'DECIMAL', 'VALOR': 'DECIMAL',
    'REAL': 'DECIMAL', 'NUMERIC': 'DECIMAL',
    'DATE': 'DATA', 'DATETIME': 'DATA', 'TIMESTAMP': 'DATA', 'DT': 'DATA'
}

OBRIGATORIO_TRUE = {'S', 'SIM', 'Y', 'YES', '1', 'TRUE'}
OBRIGATORIO_FALSE = {'N', 'NAO', 'NA', 'NO', '0', 'FALSE'}


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    for ch in [' ', '.', '/', '-', '\\']:
        s = s.replace(ch, '_')
    return s


def suggest_mapping(headers: List[str]) -> Dict[str, Optional[str]]:
    """Sugere mapeamento de cabeçalhos para colunas canônicas"""
    normalized = {h: _norm(h) for h in headers}
    mapping: Dict[str, Optional[str]] = {c: None for c in CANONICAL_COLUMNS}

    # Passo 1: sinônimos diretos
    for canon in CANONICAL_COLUMNS:
        syns = {_norm(x) for x in SYNONYMS.get(canon, [])} | {_norm(canon)}
        for orig, normed in normalized.items():
            if normed in syns and mapping[canon] is None:
                mapping[canon] = orig
                break

    # Heurística adicional: se não existir Campo mas existir algo com 'campo' dentro
    if mapping['Campo'] is None:
        for orig in headers:
            normed = _norm(orig)
            if 'campo' in normed and not any(x in normed for x in ['obrig','tamanho','tipo']):
                mapping['Campo'] = orig
                break

    # Heurística: Tamanho pode vir como TAM puro
    if mapping['Tamanho'] is None:
        for orig in headers:
            if _norm(orig) in {'tam'}:
                mapping['Tamanho'] = orig
                break

    # Heurística: Obrigatorio pode vir como PREENCH / PREENCHIMENTO
    if mapping['Obrigatorio'] is None:
        for orig in headers:
            if _norm(orig) in {'preench','preenchimento'}:
                mapping['Obrigatorio'] = orig
                break

    # Passo 2: fuzzy para não mapeados
    for canon in CANONICAL_COLUMNS:
        if mapping[canon] is None:
            candidates = []
            for orig, normed in normalized.items():
                score = difflib.SequenceMatcher(None, normed, _norm(canon)).ratio()
                if score >= 0.75:
                    candidates.append((score, orig))
            if candidates:
                candidates.sort(reverse=True)
                mapping[canon] = candidates[0][1]

    return mapping


def headers_signature(headers: List[str]) -> str:
    """Gera assinatura estável dos cabeçalhos (normalizados e ordenados)."""
    normed = sorted(_norm(h) for h in headers)
    digest = hashlib.sha256(('|'.join(normed)).encode('utf-8')).hexdigest()[:16]
    return digest


_CACHE_PATH = Path('data/layout_mappings.json')


def _load_cache() -> Dict[str, Any]:
    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: Dict[str, Any]):
    _CACHE_PATH.parent.mkdir(exist_ok=True, parents=True)
    with open(_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_cached_mapping(signature: str) -> Optional[Dict[str, Any]]:
    cache = _load_cache()
    return cache.get(signature)


def save_cached_mapping(signature: str, mapping: Dict[str, Any]):
    cache = _load_cache()
    cache[signature] = mapping
    _save_cache(cache)


def analyze_mapping(mapping: Dict[str, Optional[str]]) -> Dict[str, Any]:
    missing = [k for k, v in mapping.items() if v is None and k in ['Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio']]
    optional_missing = [k for k, v in mapping.items() if v is None and k not in missing]
    completeness = 1 - (len(missing) / 5)
    return {
        'missing_required': missing,
        'missing_optional': optional_missing,
        'completeness': completeness
    }


def normalize_dataframe(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> Tuple[pd.DataFrame, List[str]]:
    """Produz dataframe com colunas canônicas a partir do mapeamento.
    Retorna df_normalizado, warnings"""
    warnings = []
    data: Dict[str, Any] = {}
    for canon in CANONICAL_COLUMNS:
        orig = mapping.get(canon)
        if orig and orig in df.columns:
            data[canon] = df[orig]
        else:
            data[canon] = None
            if canon in ['Campo', 'Posicao_Inicio', 'Tamanho', 'Tipo', 'Obrigatorio']:
                warnings.append(f'Coluna obrigatória ausente: {canon}')

    norm_df = pd.DataFrame(data)

    # Limpeza e normalização de tipos
    if 'Obrigatorio' in norm_df:
        norm_df['Obrigatorio'] = norm_df['Obrigatorio'].astype(str).str.upper().str.strip().apply(
            lambda x: 'S' if x in OBRIGATORIO_TRUE else ('N' if x in OBRIGATORIO_FALSE else 'N')
        )

    if 'Tipo' in norm_df:
        def normalizar_tipo(x):
            x_upper = str(x).upper().strip()
            # Primeiro tenta normalização direta
            normalized = TIPO_NORMALIZATION.get(x_upper, None)
            if normalized:
                return normalized
            # Se não encontrou, verifica se é um dos tipos válidos
            if x_upper in ['TEXTO', 'NUMERO', 'DATA', 'DECIMAL']:
                return x_upper
            # Fallback para TEXTO para tipos desconhecidos
            return 'TEXTO'
        
        norm_df['Tipo'] = norm_df['Tipo'].apply(normalizar_tipo)

    # Converter numéricos
    for col in ['Posicao_Inicio', 'Tamanho']:
        if col in norm_df:
            norm_df[col] = pd.to_numeric(norm_df[col], errors='coerce')

    # Se não houver Posicao_Inicio válido mas houver Tamanho, gerar cumulativo
    if 'Posicao_Inicio' in norm_df and 'Tamanho' in norm_df:
        if norm_df['Posicao_Inicio'].isna().all() or (norm_df['Posicao_Inicio'] <= 0).all():
            start = 1
            posicoes = []
            for tam in norm_df['Tamanho']:
                try:
                    t = int(tam)
                except Exception:
                    t = None
                if t is None or t <= 0:
                    posicoes.append(None)
                else:
                    posicoes.append(start)
                    start += t
            norm_df['Posicao_Inicio'] = posicoes
            # Aviso de geração automática
            warnings.append('Posicao_Inicio gerada automaticamente pelo cumulativo de Tamanho.')

    # Remover linhas vazias
    if 'Campo' in norm_df:
        norm_df = norm_df[~norm_df['Campo'].astype(str).str.strip().eq('')]

    norm_df = norm_df.reset_index(drop=True)
    return norm_df, warnings


@dataclass
class LayoutMappingResult:
    mapping: Dict[str, Optional[str]]
    analysis: Dict[str, Any]
    sample: List[Dict[str, Any]]  # primeiras linhas normalizadas
    warnings: List[str]
    original_samples: Dict[str, List[str]]  # amostras por coluna original
    normalized_rows: List[Dict[str, Any]]  # todas as linhas normalizadas (layout base)


def map_layout_file(temp_path: str) -> LayoutMappingResult:
    import pandas as pd
    df = pd.read_excel(temp_path)
    headers = list(df.columns)
    mapping = suggest_mapping(headers)
    analysis = analyze_mapping(mapping)
    norm_df, warnings = normalize_dataframe(df, mapping)
    sample = norm_df.head(5).fillna('').to_dict(orient='records')
    # Amostras originais: primeiros 3 valores não nulos por coluna
    original_samples: Dict[str, List[str]] = {}
    for col in headers:
        serie = df[col].astype(str).fillna('').tolist()
        original_samples[col] = [v for v in serie if v.strip()][:3]
    normalized_rows = norm_df.fillna('').to_dict(orient='records')
    return LayoutMappingResult(
        mapping=mapping,
        analysis=analysis,
        sample=sample,
        warnings=warnings,
        original_samples=original_samples,
        normalized_rows=normalized_rows
    )
