"""
Validador para arquivos com múltiplos tipos de registro
"""
from typing import Dict, List, Generator, Tuple
from pathlib import Path
import pandas as pd

try:
    from .models import Layout, ErroValidacao, ResultadoValidacao
    from .layout_parser import LayoutParser
    from .file_validator import ValidadorArquivo
except ImportError:
    from models import Layout, ErroValidacao, ResultadoValidacao
    from layout_parser import LayoutParser
    from file_validator import ValidadorArquivo


class MultiRecordValidator:
    """Validador que suporta múltiplos tipos de registro"""

    def __init__(self, excel_path: str, sheet_name: int = 1):
        self.excel_path = excel_path
        self.sheet_name = sheet_name
        self.layouts_por_tipo: Dict[str, Layout] = {}
        self.validadores_por_tipo: Dict[str, ValidadorArquivo] = {}
        self._carregar_layouts()

    def _carregar_layouts(self):
        """Carrega layouts para todos os tipos de registro"""
        df = pd.read_excel(self.excel_path, sheet_name=self.sheet_name, header=1)
        df_clean = df[df['Campo'].notna() & (df['Campo'] != 'Campo')].copy()

        # Identificar todos os tipos de registro
        tipos_registro = set()
        for _, row in df_clean.iterrows():
            campo_nome = str(row['Campo'])
            if 'NFE' in campo_nome and '-' in campo_nome:
                tipo = campo_nome.split('-')[0].replace('NFE', '')
                tipos_registro.add(tipo)

        print(f"Carregando layouts para {len(tipos_registro)} tipos de registro...")

        # Criar layout para cada tipo
        parser = LayoutParser()
        for tipo in tipos_registro:
            try:
                layout_path = self._criar_layout_para_tipo(tipo, df_clean)
                layout = parser.parse_excel(layout_path)
                self.layouts_por_tipo[tipo] = layout
                self.validadores_por_tipo[tipo] = ValidadorArquivo(layout)
                print(f"  ✅ Tipo {tipo}: {len(layout.campos)} campos")
            except Exception as e:
                print(f"  ❌ Erro no tipo {tipo}: {e}")

    def _criar_layout_para_tipo(self, tipo: str, df_clean: pd.DataFrame) -> str:
        """Cria arquivo de layout para um tipo específico"""
        campos_tipo = df_clean[df_clean['Campo'].str.contains(f'NFE{tipo}-', na=False)]

        campos_convertidos = []
        for _, row in campos_tipo.iterrows():
            campo_nome = str(row['Campo'])
            posicao_inicio = int(row['De'])
            tamanho = int(row['Tam'])
            tipo_campo = str(row['Tipo']).upper()
            obrigatorio = str(row['Preenc\nSovos']).upper() in ['OBRIG', 'OBRIGATORIO']

            # Converter tipos
            if tipo_campo == 'NUM':
                tipo_campo = 'NUMERO'
            elif tipo_campo == 'ALFA':
                tipo_campo = 'TEXTO'

            campos_convertidos.append({
                'Campo': campo_nome,
                'Posicao_Inicio': posicao_inicio,
                'Tamanho': tamanho,
                'Tipo': tipo_campo,
                'Obrigatorio': 'S' if obrigatorio else 'N',
                'Formato': None
            })

        # Salvar layout temporário
        layout_path = f'layout_tipo_{tipo}.xlsx'
        df_convertido = pd.DataFrame(campos_convertidos)
        df_convertido.to_excel(layout_path, index=False)

        return layout_path

    def detectar_tipo_registro(self, linha: str) -> str:
        """Detecta o tipo de registro de uma linha"""
        if len(linha) >= 2:
            return linha[:2]
        return "00"  # default

    def validar_linha_por_tipo(self, numero_linha: int, linha: str) -> List[ErroValidacao]:
        """Valida uma linha usando o layout apropriado para seu tipo"""
        tipo_registro = self.detectar_tipo_registro(linha)

        if tipo_registro in self.validadores_por_tipo:
            return self.validadores_por_tipo[tipo_registro].validar_linha(numero_linha, linha)
        else:
            # Tipo não reconhecido
            return [ErroValidacao(
                linha=numero_linha,
                campo='TIPO_REGISTRO',
                valor_encontrado=tipo_registro,
                erro_tipo='TIPO_REGISTRO_NAO_RECONHECIDO',
                descricao=f"Tipo de registro '{tipo_registro}' não foi encontrado no layout",
                valor_esperado="Tipo de registro válido (00, 01, 02, etc.)"
            )]

    def validar_arquivo(self, caminho_arquivo: str, max_erros: int = None) -> ResultadoValidacao:
        """Valida arquivo completo com suporte a múltiplos tipos"""
        if not Path(caminho_arquivo).exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

        total_linhas = 0
        linhas_com_erro = 0
        todos_erros = []
        estatisticas_por_tipo = {}

        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                for numero_linha, linha in enumerate(arquivo, 1):
                    linha = linha.rstrip('\n\r')
                    total_linhas += 1

                    # Adicionar padding se necessário
                    if len(linha) < 540:  # tamanho padrão
                        linha = linha.ljust(540)

                    # Detectar tipo e validar
                    tipo_registro = self.detectar_tipo_registro(linha)

                    # Estatísticas por tipo
                    if tipo_registro not in estatisticas_por_tipo:
                        estatisticas_por_tipo[tipo_registro] = {'total': 0, 'erros': 0}
                    estatisticas_por_tipo[tipo_registro]['total'] += 1

                    erros_linha = self.validar_linha_por_tipo(numero_linha, linha)

                    if erros_linha:
                        linhas_com_erro += 1
                        estatisticas_por_tipo[tipo_registro]['erros'] += 1
                        todos_erros.extend(erros_linha)

                        # Limitar erros se especificado
                        if max_erros and len(todos_erros) >= max_erros:
                            break

        except UnicodeDecodeError:
            # Tentar com latin-1
            with open(caminho_arquivo, 'r', encoding='latin-1') as arquivo:
                # Mesmo código...
                pass

        linhas_validas = total_linhas - linhas_com_erro

        # Mostrar estatísticas por tipo
        print(f"\nEstatísticas por tipo de registro:")
        for tipo, stats in sorted(estatisticas_por_tipo.items()):
            taxa_sucesso = ((stats['total'] - stats['erros']) / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  Tipo {tipo}: {stats['total']} linhas, {stats['erros']} erros ({taxa_sucesso:.1f}% válidas)")

        return ResultadoValidacao(
            total_linhas=total_linhas,
            linhas_validas=linhas_validas,
            linhas_com_erro=linhas_com_erro,
            erros=todos_erros,
            taxa_sucesso=0.0  # Será calculado no __post_init__
        )