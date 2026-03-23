import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter
import io
import base64
import math

try:
    from .models import ResultadoValidacao, ErroValidacao, Layout
except ImportError:
    from models import ResultadoValidacao, ErroValidacao, Layout

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Wedge, Line
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics import renderPDF
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class GeradorRelatorio:
    """Gerador de relatórios de validação"""

    def __init__(self, resultado: ResultadoValidacao, layout: Layout):
        self.resultado = resultado
        self.layout = layout

    def gerar_resumo_texto(self) -> str:
        """Gera resumo em texto"""
        resumo = f"""
=== RELATÓRIO DE VALIDAÇÃO ===
Layout: {self.layout.nome}
Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

=== ESTATÍSTICAS ===
Total de linhas: {self.resultado.total_linhas:,}
Linhas válidas: {self.resultado.linhas_validas:,}
Linhas com erro: {self.resultado.linhas_com_erro:,}
Taxa de sucesso: {self.resultado.taxa_sucesso:.2f}%

=== TIPOS DE ERROS ===
"""

        # Contar tipos de erro
        contador_tipos = Counter(erro.erro_tipo for erro in self.resultado.erros)
        for tipo, quantidade in contador_tipos.most_common():
            resumo += f"{tipo}: {quantidade:,} ocorrências\n"

        # Contar erros por campo
        resumo += "\n=== ERROS POR CAMPO ===\n"
        contador_campos = Counter(erro.campo for erro in self.resultado.erros)
        for campo, quantidade in contador_campos.most_common(10):  # Top 10
            resumo += f"{campo}: {quantidade:,} erros\n"

        return resumo

    def gerar_detalhes_excel(self, caminho_saida: str) -> str:
        """Gera relatório detalhado em Excel"""
        if not self.resultado.erros:
            # Se não há erros, criar arquivo simples
            df_resumo = pd.DataFrame([{
                'Status': 'SUCESSO',
                'Total_Linhas': self.resultado.total_linhas,
                'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%",
                'Observacao': 'Nenhum erro encontrado'
            }])

            with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)

            return caminho_saida

        # Preparar dados dos erros
        dados_erros = []
        for erro in self.resultado.erros:
            dados_erros.append({
                'Linha': erro.linha,
                'Campo': erro.campo,
                'Tipo_Erro': erro.erro_tipo,
                'Valor_Encontrado': erro.valor_encontrado,
                'Descrição': erro.descricao,
                'Valor_Esperado': erro.valor_esperado or ''
            })

        df_erros = pd.DataFrame(dados_erros)

        # Preparar resumo
        contador_tipos = Counter(erro.erro_tipo for erro in self.resultado.erros)
        dados_resumo = []
        for tipo, quantidade in contador_tipos.items():
            dados_resumo.append({
                'Tipo_Erro': tipo,
                'Quantidade': quantidade,
                'Percentual': f"{(quantidade / len(self.resultado.erros) * 100):.2f}%"
            })

        df_resumo = pd.DataFrame(dados_resumo)

        # Estatísticas gerais
        df_estatisticas = pd.DataFrame([{
            'Total_Linhas': self.resultado.total_linhas,
            'Linhas_Validas': self.resultado.linhas_validas,
            'Linhas_Com_Erro': self.resultado.linhas_com_erro,
            'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%",
            'Total_Erros': len(self.resultado.erros)
        }])

        # Erros por campo
        contador_campos = Counter(erro.campo for erro in self.resultado.erros)
        dados_campos = []
        for campo, quantidade in contador_campos.most_common():
            dados_campos.append({
                'Campo': campo,
                'Quantidade_Erros': quantidade,
                'Percentual': f"{(quantidade / len(self.resultado.erros) * 100):.2f}%"
            })

        df_campos = pd.DataFrame(dados_campos)

        # Salvar Excel com múltiplas abas
        with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
            df_estatisticas.to_excel(writer, sheet_name='Estatísticas', index=False)
            df_resumo.to_excel(writer, sheet_name='Resumo_Tipos', index=False)
            df_campos.to_excel(writer, sheet_name='Erros_Por_Campo', index=False)
            df_erros.to_excel(writer, sheet_name='Detalhes_Erros', index=False)

        return caminho_saida

    def gerar_relatorio_completo(self, diretorio_saida: str) -> Dict[str, str]:
        """Gera relatório completo (texto + Excel)"""
        Path(diretorio_saida).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_base = f"relatorio_validacao_{self.layout.nome}_{timestamp}"

        # Gerar arquivo texto
        caminho_txt = Path(diretorio_saida) / f"{nome_base}.txt"
        with open(caminho_txt, 'w', encoding='utf-8') as arquivo:
            arquivo.write(self.gerar_resumo_texto())

        # Gerar arquivo Excel
        caminho_excel = Path(diretorio_saida) / f"{nome_base}.xlsx"
        self.gerar_detalhes_excel(str(caminho_excel))

        # Gerar também o relatório resumo de erros
        caminho_resumo = Path(diretorio_saida) / f"{nome_base}_resumo_erros.xlsx"
        self.gerar_relatorio_resumo_erros(str(caminho_resumo))

        return {
            'texto': str(caminho_txt),
            'excel': str(caminho_excel),
            'resumo_erros': str(caminho_resumo),
            'resumo': self.gerar_resumo_texto()
        }

    def gerar_relatorio_csv(self, caminho_saida: str) -> str:
        """Gera relatório simples em CSV"""
        if not self.resultado.erros:
            # CSV vazio se não há erros
            df = pd.DataFrame([{
                'Status': 'SUCESSO - Nenhum erro encontrado',
                'Total_Linhas': self.resultado.total_linhas,
                'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%"
            }])
        else:
            dados = []
            for erro in self.resultado.erros:
                dados.append({
                    'Linha': erro.linha,
                    'Campo': erro.campo,
                    'Tipo_Erro': erro.erro_tipo,
                    'Valor_Encontrado': erro.valor_encontrado,
                    'Descrição': erro.descricao
                })
            df = pd.DataFrame(dados)

        df.to_csv(caminho_saida, index=False, encoding='utf-8-sig')  # utf-8-sig para Excel
        return caminho_saida

    def gerar_dados_relatorio(self) -> Dict[str, Any]:
        """Gera dados do relatório em memória para localStorage"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Dados básicos
        dados_relatorio = {
            'timestamp': timestamp,
            'layout_nome': self.layout.nome,
            'data_geracao': datetime.now().isoformat(),
            'resumo_texto': self.gerar_resumo_texto(),
            'estatisticas': {
                'total_linhas': self.resultado.total_linhas,
                'linhas_validas': self.resultado.linhas_validas,
                'linhas_com_erro': self.resultado.linhas_com_erro,
                'taxa_sucesso': self.resultado.taxa_sucesso,
                'total_erros': len(self.resultado.erros)
            }
        }

        # Dados dos erros para download
        if self.resultado.erros:
            dados_relatorio['erros'] = []
            for erro in self.resultado.erros:
                dados_relatorio['erros'].append({
                    'linha': erro.linha,
                    'campo': erro.campo,
                    'tipo_erro': erro.erro_tipo,
                    'valor_encontrado': erro.valor_encontrado,
                    'descricao': erro.descricao,
                    'valor_esperado': erro.valor_esperado or ''
                })

        # Contadores para análise
        if self.resultado.erros:
            contador_tipos = Counter(erro.erro_tipo for erro in self.resultado.erros)
            contador_campos = Counter(erro.campo for erro in self.resultado.erros)

            dados_relatorio['analise'] = {
                'tipos_erro': dict(contador_tipos.most_common()),
                'campos_com_erro': dict(contador_campos.most_common(10))
            }

            # Adicionar dados do relatório resumo de erros para o frontend
            dados_relatorio['resumo_erros_excel'] = self.gerar_excel_resumo_erros_blob()

        # Gerar PDF bonito
        try:
            dados_relatorio['pdf_blob'] = self.gerar_pdf_blob()
        except (ImportError, Exception):
            pass  # PDF não disponível se reportlab não estiver instalado

        return dados_relatorio

    def gerar_excel_resumo_erros_blob(self) -> str:
        """Gera relatório resumo de erros em memória e retorna como base64"""
        buffer = io.BytesIO()

        if not self.resultado.erros:
            # Se não há erros, criar arquivo simples
            df_sucesso = pd.DataFrame([{
                'Status': 'SUCESSO - Nenhum erro encontrado',
                'Total_Registros': self.resultado.total_linhas,
                'Data_Validacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }])

            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_sucesso.to_excel(writer, sheet_name='Resumo_Erros', index=False)
        else:
            # Usar a mesma lógica do método principal, mas salvando em buffer
            # (código simplificado - o método já existe, só muda o destino)
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                self.gerar_relatorio_resumo_erros(temp_file.name)

                # Ler o arquivo temporário para o buffer
                with open(temp_file.name, 'rb') as f:
                    buffer.write(f.read())

                # Remover arquivo temporário
                os.unlink(temp_file.name)

        buffer.seek(0)
        excel_bytes = buffer.getvalue()
        return base64.b64encode(excel_bytes).decode('utf-8')

    def gerar_excel_blob(self) -> str:
        """Gera arquivo Excel em memória e retorna como base64"""
        buffer = io.BytesIO()

        if not self.resultado.erros:
            # Se não há erros, criar arquivo simples
            df_resumo = pd.DataFrame([{
                'Status': 'SUCESSO',
                'Total_Linhas': self.resultado.total_linhas,
                'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%",
                'Observacao': 'Nenhum erro encontrado'
            }])

            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
        else:
            # Preparar dados dos erros
            dados_erros = []
            for erro in self.resultado.erros:
                dados_erros.append({
                    'Linha': erro.linha,
                    'Campo': erro.campo,
                    'Tipo_Erro': erro.erro_tipo,
                    'Valor_Encontrado': erro.valor_encontrado,
                    'Descrição': erro.descricao,
                    'Valor_Esperado': erro.valor_esperado or ''
                })

            df_erros = pd.DataFrame(dados_erros)

            # Preparar resumo
            contador_tipos = Counter(erro.erro_tipo for erro in self.resultado.erros)
            dados_resumo = []
            for tipo, quantidade in contador_tipos.items():
                dados_resumo.append({
                    'Tipo_Erro': tipo,
                    'Quantidade': quantidade,
                    'Percentual': f"{(quantidade / len(self.resultado.erros) * 100):.2f}%"
                })

            df_resumo = pd.DataFrame(dados_resumo)

            # Estatísticas gerais
            df_estatisticas = pd.DataFrame([{
                'Total_Linhas': self.resultado.total_linhas,
                'Linhas_Validas': self.resultado.linhas_validas,
                'Linhas_Com_Erro': self.resultado.linhas_com_erro,
                'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%",
                'Total_Erros': len(self.resultado.erros)
            }])

            # Erros por campo
            contador_campos = Counter(erro.campo for erro in self.resultado.erros)
            dados_campos = []
            for campo, quantidade in contador_campos.most_common():
                dados_campos.append({
                    'Campo': campo,
                    'Quantidade_Erros': quantidade,
                    'Percentual': f"{(quantidade / len(self.resultado.erros) * 100):.2f}%"
                })

            df_campos = pd.DataFrame(dados_campos)

            # Salvar Excel com múltiplas abas
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_estatisticas.to_excel(writer, sheet_name='Estatísticas', index=False)
                df_resumo.to_excel(writer, sheet_name='Resumo_Tipos', index=False)
                df_campos.to_excel(writer, sheet_name='Erros_Por_Campo', index=False)
                df_erros.to_excel(writer, sheet_name='Detalhes_Erros', index=False)

        buffer.seek(0)
        excel_bytes = buffer.getvalue()
        return base64.b64encode(excel_bytes).decode('utf-8')

    def gerar_csv_data(self) -> str:
        """Gera dados CSV em memória como string"""
        buffer = io.StringIO()

        if not self.resultado.erros:
            df = pd.DataFrame([{
                'Status': 'SUCESSO - Nenhum erro encontrado',
                'Total_Linhas': self.resultado.total_linhas,
                'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%"
            }])
        else:
            dados = []
            for erro in self.resultado.erros:
                dados.append({
                    'Linha': erro.linha,
                    'Campo': erro.campo,
                    'Tipo_Erro': erro.erro_tipo,
                    'Valor_Encontrado': erro.valor_encontrado,
                    'Descrição': erro.descricao
                })
            df = pd.DataFrame(dados)

        df.to_csv(buffer, index=False, encoding='utf-8')
        return buffer.getvalue()

    def gerar_relatorio_sefaz(self, caminho_saida: str) -> str:
        """Gera relatório focado em erros críticos para envio à SEFAZ"""
        if not self.resultado.erros:
            # Se não há erros, criar relatório de sucesso
            dados = [{
                'Status': 'APROVADO',
                'Observacao': 'Arquivo válido para envio à SEFAZ',
                'Total_Registros': self.resultado.total_linhas,
                'Data_Validacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }]
            df = pd.DataFrame(dados)
            df.to_excel(caminho_saida, sheet_name='Status_SEFAZ', index=False)
            return caminho_saida

        # Agrupar erros por linha/registro para análise crítica
        erros_por_linha = {}
        for erro in self.resultado.erros:
            linha = erro.linha
            if linha not in erros_por_linha:
                erros_por_linha[linha] = []
            erros_por_linha[linha].append(erro)

        # Categorizar erros por criticidade para SEFAZ
        erros_criticos = []
        erros_advertencia = []

        # Tipos de erro críticos que impedem envio à SEFAZ
        tipos_criticos = {
            'CALCULO_ERRO_ICMS', 'CALCULO_ERRO_PIS', 'CALCULO_ERRO_COFINS',
            'CALCULO_ERRO_FUST', 'CALCULO_ERRO_FUNTEL', 'CALCULO_ERRO_FCP',
            'TOTAL_ICMS', 'TOTAL_PIS', 'TOTAL_COFINS', 'TOTAL_FUST',
            'TOTAL_FUNTEL', 'TOTAL_FCP', 'TOTAL_BC',
            'CAMPO_OBRIGATORIO', 'FORMATO_INVALIDO', 'TIPO_REGISTRO_NAO_RECONHECIDO'
        }

        for linha, erros_linha in erros_por_linha.items():
            # Determinar tipo do registro pela linha
            tipo_registro = 'DESCONHECIDO'
            if self.resultado.erros:
                primeiro_erro = erros_linha[0]
                # Extrair tipo do registro do nome do campo se possível
                if hasattr(primeiro_erro, 'campo') and 'NFE' in primeiro_erro.campo:
                    try:
                        tipo_registro = primeiro_erro.campo.split('-')[0].replace('NFE', '')
                    except:
                        pass

            # Classificar criticidade dos erros desta linha
            tem_erro_critico = any(
                any(tipo_crit in erro.erro_tipo for tipo_crit in tipos_criticos)
                for erro in erros_linha
            )

            # Criar entrada para o relatório
            entrada_relatorio = {
                'Linha': linha,
                'Tipo_Registro': tipo_registro,
                'Status_SEFAZ': 'CRÍTICO' if tem_erro_critico else 'ADVERTÊNCIA',
                'Quantidade_Erros': len(erros_linha),
                'Principais_Erros': '; '.join([
                    f"{erro.campo}: {erro.erro_tipo}"
                    for erro in erros_linha[:3]  # Primeiros 3 erros
                ]),
                'Detalhes_Completos': '; '.join([
                    f"{erro.campo}={erro.valor_encontrado} ({erro.descricao})"
                    for erro in erros_linha
                ])
            }

            if tem_erro_critico:
                erros_criticos.append(entrada_relatorio)
            else:
                erros_advertencia.append(entrada_relatorio)

        # Preparar dados para Excel
        with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
            # Aba 1: Resumo para SEFAZ
            total_criticos = len(erros_criticos)
            total_advertencias = len(erros_advertencia)

            resumo_sefaz = [{
                'Status_Arquivo': 'REPROVADO' if total_criticos > 0 else 'APROVADO_COM_RESSALVAS',
                'Apto_Envio_SEFAZ': 'NÃO' if total_criticos > 0 else 'SIM',
                'Total_Registros': self.resultado.total_linhas,
                'Registros_Com_Erro_Critico': total_criticos,
                'Registros_Com_Advertencia': total_advertencias,
                'Taxa_Aprovacao': f"{((self.resultado.total_linhas - total_criticos) / self.resultado.total_linhas * 100):.2f}%",
                'Data_Validacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'Observacoes': 'Corrigir erros críticos antes do envio' if total_criticos > 0 else 'Arquivo apto para envio com advertências'
            }]

            df_resumo = pd.DataFrame(resumo_sefaz)
            df_resumo.to_excel(writer, sheet_name='Status_SEFAZ', index=False)

            # Aba 2: Erros Críticos (impedem envio)
            if erros_criticos:
                df_criticos = pd.DataFrame(erros_criticos)
                df_criticos.to_excel(writer, sheet_name='Erros_Críticos', index=False)

            # Aba 3: Advertências (não impedem envio)
            if erros_advertencia:
                df_advertencias = pd.DataFrame(erros_advertencia)
                df_advertencias.to_excel(writer, sheet_name='Advertências', index=False)

            # Aba 4: Estatísticas por tipo de registro
            stats_por_tipo = {}
            for linha, erros_linha in erros_por_linha.items():
                tipo = erros_linha[0].campo.split('-')[0].replace('NFE', '') if 'NFE' in erros_linha[0].campo else 'GERAL'
                if tipo not in stats_por_tipo:
                    stats_por_tipo[tipo] = {'total_linhas': 0, 'linhas_com_erro': 0, 'total_erros': 0}

                stats_por_tipo[tipo]['linhas_com_erro'] += 1
                stats_por_tipo[tipo]['total_erros'] += len(erros_linha)

            # Adicionar contagem total de linhas por tipo (aproximação)
            for tipo in stats_por_tipo:
                stats_por_tipo[tipo]['total_linhas'] = stats_por_tipo[tipo]['linhas_com_erro']  # Simplificado

            dados_stats = []
            for tipo, stats in stats_por_tipo.items():
                dados_stats.append({
                    'Tipo_Registro': tipo,
                    'Total_Linhas': stats['total_linhas'],
                    'Linhas_Com_Erro': stats['linhas_com_erro'],
                    'Total_Erros': stats['total_erros'],
                    'Taxa_Erro': f"{(stats['linhas_com_erro'] / stats['total_linhas'] * 100):.2f}%" if stats['total_linhas'] > 0 else '0%'
                })

            if dados_stats:
                df_stats = pd.DataFrame(dados_stats)
                df_stats.to_excel(writer, sheet_name='Stats_Por_Tipo', index=False)

        return caminho_saida

    def gerar_relatorio_detalhado_registro(self, caminho_saida: str) -> str:
        """Gera relatório detalhado mostrando cada registro com erro"""
        if not self.resultado.erros:
            # Se não há erros
            dados = [{
                'Resultado': 'SUCESSO - Nenhum erro encontrado',
                'Total_Registros': self.resultado.total_linhas,
                'Data_Validacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }]
            df = pd.DataFrame(dados)
            df.to_excel(caminho_saida, sheet_name='Resultado', index=False)
            return caminho_saida

        # Agrupar erros por linha/registro
        registros_com_erro = {}
        for erro in self.resultado.erros:
            linha = erro.linha
            if linha not in registros_com_erro:
                registros_com_erro[linha] = {
                    'linha': linha,
                    'erros': [],
                    'tipo_registro': 'DESCONHECIDO',
                    'num_nf': 'N/A'
                }

            registros_com_erro[linha]['erros'].append(erro)

            # Tentar extrair tipo do registro
            if 'NFE' in erro.campo:
                try:
                    tipo = erro.campo.split('-')[0].replace('NFE', '')
                    registros_com_erro[linha]['tipo_registro'] = tipo
                except:
                    pass

        # Preparar dados para relatório detalhado
        dados_detalhados = []
        for linha, dados_linha in sorted(registros_com_erro.items()):
            # Agrupar erros por tipo para esta linha
            erros_por_tipo = {}
            for erro in dados_linha['erros']:
                tipo_erro = erro.erro_tipo
                if tipo_erro not in erros_por_tipo:
                    erros_por_tipo[tipo_erro] = []
                erros_por_tipo[tipo_erro].append(erro)

            # Criar uma entrada para cada tipo de erro nesta linha
            for tipo_erro, erros_tipo in erros_por_tipo.items():
                dados_detalhados.append({
                    'Linha': linha,
                    'Tipo_Registro': dados_linha['tipo_registro'],
                    'Tipo_Erro': tipo_erro,
                    'Quantidade': len(erros_tipo),
                    'Campos_Afetados': ', '.join([erro.campo for erro in erros_tipo]),
                    'Valores_Encontrados': '; '.join([
                        f"{erro.campo}='{erro.valor_encontrado}'"
                        for erro in erros_tipo[:3]  # Primeiros 3 para não ficar muito longo
                    ]),
                    'Descrição_Detalhada': '; '.join([erro.descricao for erro in erros_tipo[:2]]),  # Primeiras 2 descrições
                    'Ação_Requerida': self._get_acao_requerida(tipo_erro)
                })

        # Criar relatório Excel
        with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
            # Aba 1: Visão Geral
            resumo_geral = [{
                'Total_Registros_Arquivo': self.resultado.total_linhas,
                'Registros_Com_Erro': len(registros_com_erro),
                'Registros_Válidos': self.resultado.linhas_validas,
                'Total_Erros_Encontrados': len(self.resultado.erros),
                'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%",
                'Status_Arquivo': 'APROVADO' if len(registros_com_erro) == 0 else 'REQUER_CORREÇÃO',
                'Data_Validacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }]

            df_resumo = pd.DataFrame(resumo_geral)
            df_resumo.to_excel(writer, sheet_name='Resumo_Geral', index=False)

            # Aba 2: Detalhes dos Erros por Registro
            if dados_detalhados:
                df_detalhes = pd.DataFrame(dados_detalhados)
                df_detalhes.to_excel(writer, sheet_name='Erros_Por_Registro', index=False)

            # Aba 3: Lista de Registros com Problemas
            dados_registros_problemas = []
            for linha, dados_linha in sorted(registros_com_erro.items()):
                total_erros = len(dados_linha['erros'])
                tipos_erro = list(set(erro.erro_tipo for erro in dados_linha['erros']))

                dados_registros_problemas.append({
                    'Linha': linha,
                    'Tipo_Registro': dados_linha['tipo_registro'],
                    'Total_Erros': total_erros,
                    'Tipos_Erro': ', '.join(tipos_erro),
                    'Gravidade': 'CRÍTICO' if any('CALCULO_ERRO' in tipo or 'TOTAL_' in tipo for tipo in tipos_erro) else 'MODERADO',
                    'Primeira_Descrição': dados_linha['erros'][0].descricao if dados_linha['erros'] else ''
                })

            if dados_registros_problemas:
                df_registros = pd.DataFrame(dados_registros_problemas)
                df_registros.to_excel(writer, sheet_name='Lista_Registros_Erro', index=False)

        return caminho_saida

    def _get_acao_requerida(self, tipo_erro: str) -> str:
        """Retorna ação requerida baseada no tipo de erro"""
        acoes = {
            'CALCULO_ERRO_ICMS': 'Revisar cálculo: Base × Alíquota = Valor ICMS',
            'CALCULO_ERRO_PIS': 'Revisar cálculo: Base × Alíquota = Valor PIS',
            'CALCULO_ERRO_COFINS': 'Revisar cálculo: Base × Alíquota = Valor COFINS',
            'CALCULO_ERRO_FUST': 'Revisar cálculo: Base × Alíquota = Valor FUST',
            'CALCULO_ERRO_FUNTEL': 'Revisar cálculo: Base × Alíquota = Valor FUNTEL',
            'CALCULO_ERRO_FCP': 'Revisar cálculo: Base × Alíquota FCP = Valor FCP',
            'TOTAL_ICMS': 'Verificar soma dos valores de ICMS nos registros',
            'TOTAL_PIS': 'Verificar soma dos valores de PIS nos registros',
            'TOTAL_COFINS': 'Verificar soma dos valores de COFINS nos registros',
            'TOTAL_FUST': 'Verificar soma dos valores de FUST nos registros',
            'TOTAL_FUNTEL': 'Verificar soma dos valores de FUNTEL nos registros',
            'TOTAL_BC': 'Verificar soma das bases de cálculo',
            'CAMPO_OBRIGATORIO': 'Preencher campo obrigatório',
            'FORMATO_INVALIDO': 'Corrigir formato do campo',
            'TIPO_REGISTRO_NAO_RECONHECIDO': 'Verificar tipo de registro válido'
        }

        return acoes.get(tipo_erro, 'Verificar dados do campo')

    def gerar_relatorio_resumo_erros(self, caminho_saida: str) -> str:
        """Gera relatório resumido focado em identificação rápida: Fatura + NF + Erro"""
        if not self.resultado.erros:
            # Se não há erros, criar relatório de sucesso
            dados = [{
                'Status': 'SUCESSO - Nenhum erro encontrado',
                'Total_Registros': self.resultado.total_linhas,
                'Data_Validacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }]
            df = pd.DataFrame(dados)

            with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Resumo_Erros', index=False)

            return caminho_saida

        # Função para extrair informações de identificação da linha
        def _extrair_identificacao(linha_numero: int, linha_conteudo: str = None) -> Dict[str, str]:
            """Extrai número de fatura e nota fiscal baseado no conteúdo da linha"""
            identificacao = {
                'num_fatura': 'N/A',
                'serie_nf': 'N/A',
                'num_nf': 'N/A',
                'tipo_registro': 'N/A'
            }

            # Se temos conteúdo da linha, extrair informações das posições conhecidas
            if linha_conteudo and len(linha_conteudo) >= 32:
                # Posições baseadas no layout identificado:
                # NUM-FATURA: posições 3-15 (13 chars)
                # SERIE-NF: posições 21-23 (3 chars)
                # NUM-NF: posições 24-32 (9 chars)
                # TIPO-REG: posições 1-2 (2 chars)

                try:
                    identificacao['tipo_registro'] = linha_conteudo[0:2].strip()
                    identificacao['num_fatura'] = linha_conteudo[2:15].strip() or 'N/A'
                    identificacao['serie_nf'] = linha_conteudo[20:23].strip() or 'N/A'
                    identificacao['num_nf'] = linha_conteudo[23:32].strip() or 'N/A'

                    # Remover zeros à esquerda dos números
                    if identificacao['num_fatura'] != 'N/A':
                        identificacao['num_fatura'] = identificacao['num_fatura'].lstrip('0') or '0'
                    if identificacao['num_nf'] != 'N/A':
                        identificacao['num_nf'] = identificacao['num_nf'].lstrip('0') or '0'

                except Exception:
                    pass  # Manter valores padrão em caso de erro

            return identificacao

        # Agrupar erros por linha e extrair identificação
        erros_agrupados = []
        linhas_processadas = set()

        for erro in self.resultado.erros:
            if erro.linha in linhas_processadas:
                continue

            linhas_processadas.add(erro.linha)

            # Pegar todos os erros desta linha
            erros_da_linha = [e for e in self.resultado.erros if e.linha == erro.linha]

            # Extrair identificação (tentaremos deduzir do nome dos campos)
            identificacao = _extrair_identificacao(erro.linha)

            # Tentar extrair fatura e NF dos próprios campos de erro se possível
            for erro_linha in erros_da_linha:
                campo_nome = erro_linha.campo

                # Se o erro é em campo de fatura ou NF, usar o valor encontrado
                if 'NUM-FATURA' in campo_nome and erro_linha.valor_encontrado:
                    valor = erro_linha.valor_encontrado.strip("'() ")
                    if valor and valor != 'N/A':
                        identificacao['num_fatura'] = valor.lstrip('0') or '0'

                elif 'NUM-NF' in campo_nome and erro_linha.valor_encontrado:
                    valor = erro_linha.valor_encontrado.strip("'() ")
                    if valor and valor != 'N/A':
                        identificacao['num_nf'] = valor.lstrip('0') or '0'

                elif 'SERIE-NF' in campo_nome and erro_linha.valor_encontrado:
                    valor = erro_linha.valor_encontrado.strip("'() ")
                    if valor and valor != 'N/A':
                        identificacao['serie_nf'] = valor

                # Extrair tipo de registro do nome do campo
                if 'NFE' in campo_nome:
                    try:
                        tipo_reg = campo_nome.split('-')[0].replace('NFE', '')
                        if tipo_reg.isdigit():
                            identificacao['tipo_registro'] = tipo_reg
                    except:
                        pass

            # Categorizar criticidade
            tipos_erro = [e.erro_tipo for e in erros_da_linha]
            tem_erro_critico = any(
                any(critico in tipo for critico in [
                    'CALCULO_ERRO', 'TOTAL_', 'CAMPO_OBRIGATORIO',
                    'TIPO_REGISTRO_NAO_RECONHECIDO'
                ])
                for tipo in tipos_erro
            )

            criticidade = 'CRÍTICO' if tem_erro_critico else 'MODERADO'

            # Resumir erros desta linha
            resumo_erros = []
            for erro_linha in erros_da_linha[:3]:  # Primeiros 3 erros
                resumo_erros.append(f"{erro_linha.campo}: {erro_linha.erro_tipo}")

            mais_erros = len(erros_da_linha) - 3
            resumo_texto = '; '.join(resumo_erros)
            if mais_erros > 0:
                resumo_texto += f" (+ {mais_erros} outros)"

            # Criar entrada resumida
            entrada = {
                'Linha': erro.linha,
                'Fatura': identificacao['num_fatura'],
                'Série_NF': identificacao['serie_nf'],
                'Número_NF': identificacao['num_nf'],
                'Tipo_Registro': identificacao['tipo_registro'],
                'Criticidade': criticidade,
                'Qtd_Erros': len(erros_da_linha),
                'Principais_Erros': resumo_texto,
                'Primeiro_Erro_Detalhado': erros_da_linha[0].descricao[:100] + '...' if len(erros_da_linha[0].descricao) > 100 else erros_da_linha[0].descricao
            }

            erros_agrupados.append(entrada)

        # Ordenar por criticidade (críticos primeiro) e depois por linha
        erros_agrupados.sort(key=lambda x: (x['Criticidade'] != 'CRÍTICO', x['Linha']))

        # Criar relatório Excel
        with pd.ExcelWriter(caminho_saida, engine='openpyxl') as writer:
            # Aba principal: Resumo de Erros
            df_resumo = pd.DataFrame(erros_agrupados)
            df_resumo.to_excel(writer, sheet_name='Resumo_Erros', index=False)

            # Aba de estatísticas gerais
            resumo_geral = [{
                'Total_Registros': self.resultado.total_linhas,
                'Registros_Com_Erro': len(erros_agrupados),
                'Erros_Críticos': len([e for e in erros_agrupados if e['Criticidade'] == 'CRÍTICO']),
                'Erros_Moderados': len([e for e in erros_agrupados if e['Criticidade'] == 'MODERADO']),
                'Total_Erros_Individuais': len(self.resultado.erros),
                'Taxa_Sucesso': f"{self.resultado.taxa_sucesso:.2f}%",
                'Status_Geral': 'REQUER_CORREÇÃO' if erros_agrupados else 'APROVADO',
                'Data_Validacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }]

            df_geral = pd.DataFrame(resumo_geral)
            df_geral.to_excel(writer, sheet_name='Estatísticas', index=False)

            # Aba de erros por tipo de registro
            stats_por_tipo = {}
            for entrada in erros_agrupados:
                tipo = entrada['Tipo_Registro']
                if tipo not in stats_por_tipo:
                    stats_por_tipo[tipo] = {
                        'registros_com_erro': 0,
                        'total_erros': 0,
                        'erros_criticos': 0
                    }

                stats_por_tipo[tipo]['registros_com_erro'] += 1
                stats_por_tipo[tipo]['total_erros'] += entrada['Qtd_Erros']
                if entrada['Criticidade'] == 'CRÍTICO':
                    stats_por_tipo[tipo]['erros_criticos'] += 1

            dados_stats = []
            for tipo, stats in stats_por_tipo.items():
                dados_stats.append({
                    'Tipo_Registro': tipo,
                    'Registros_Com_Erro': stats['registros_com_erro'],
                    'Total_Erros': stats['total_erros'],
                    'Erros_Críticos': stats['erros_criticos'],
                    'Erros_Moderados': stats['registros_com_erro'] - stats['erros_criticos']
                })

            if dados_stats:
                df_stats = pd.DataFrame(dados_stats)
                df_stats.to_excel(writer, sheet_name='Erros_Por_Tipo', index=False)

        return caminho_saida

    # ===================== PDF REPORT =====================

    def _cor_taxa(self, taxa: float):
        """Retorna cor baseada na taxa de sucesso"""
        if taxa >= 90:
            return colors.HexColor('#16a34a')
        elif taxa >= 70:
            return colors.HexColor('#d97706')
        else:
            return colors.HexColor('#dc2626')

    def _criar_card_estatistica(self, titulo: str, valor: str, cor: colors.Color, largura=120, altura=70):
        """Cria um card visual de estatística como Drawing"""
        d = Drawing(largura, altura)
        r = Rect(0, 0, largura, altura, rx=8, ry=8)
        r.fillColor = cor
        r.strokeColor = colors.HexColor('#e5e7eb')
        r.strokeWidth = 0.5
        d.add(r)
        s_valor = String(largura / 2, altura - 28, valor, textAnchor='middle')
        s_valor.fontSize = 22
        s_valor.fontName = 'Helvetica-Bold'
        s_valor.fillColor = colors.white
        d.add(s_valor)
        s_titulo = String(largura / 2, 18, titulo, textAnchor='middle')
        s_titulo.fontSize = 9
        s_titulo.fontName = 'Helvetica'
        s_titulo.fillColor = colors.HexColor('#f0f0f0')
        d.add(s_titulo)
        return d

    def _criar_grafico_pizza(self, dados: dict, largura=480, altura=180):
        """Cria gráfico de pizza para distribuição de erros"""
        d = Drawing(largura, altura)

        if not dados:
            s = String(largura / 2, altura / 2, 'Sem dados', textAnchor='middle')
            s.fontSize = 12
            s.fillColor = colors.gray
            d.add(s)
            return d

        pie = Pie()
        pie.x = 30
        pie.y = 20
        pie.width = 120
        pie.height = 120
        pie.data = list(dados.values())
        pie.labels = None

        cores_pie = [
            colors.HexColor('#3b82f6'), colors.HexColor('#ef4444'),
            colors.HexColor('#f59e0b'), colors.HexColor('#10b981'),
            colors.HexColor('#8b5cf6'), colors.HexColor('#ec4899'),
            colors.HexColor('#06b6d4'), colors.HexColor('#84cc16'),
        ]

        for i in range(len(dados)):
            pie.slices[i].fillColor = cores_pie[i % len(cores_pie)]
            pie.slices[i].strokeColor = colors.white
            pie.slices[i].strokeWidth = 1.5

        d.add(pie)

        total = sum(dados.values())
        y_legenda = altura - 20
        for i, (label, valor) in enumerate(dados.items()):
            if i >= 8:
                break
            cor = cores_pie[i % len(cores_pie)]
            x_leg = 190
            rect = Rect(x_leg, y_legenda - 4, 10, 10)
            rect.fillColor = cor
            rect.strokeColor = None
            d.add(rect)
            pct = (valor / total * 100) if total > 0 else 0
            texto = f'{label[:22]} ({pct:.0f}%)'
            s = String(x_leg + 14, y_legenda, texto, textAnchor='start')
            s.fontSize = 8
            s.fontName = 'Helvetica'
            s.fillColor = colors.HexColor('#374151')
            d.add(s)
            y_legenda -= 18

        return d

    def _criar_barra_progresso(self, taxa: float, largura=460, altura=30):
        """Cria barra de progresso visual"""
        d = Drawing(largura, altura)
        bg = Rect(0, 5, largura, 18, rx=9, ry=9)
        bg.fillColor = colors.HexColor('#e5e7eb')
        bg.strokeColor = None
        d.add(bg)
        w_barra = max(0, min(largura, largura * taxa / 100))
        if w_barra > 0:
            barra = Rect(0, 5, w_barra, 18, rx=9, ry=9)
            barra.fillColor = self._cor_taxa(taxa)
            barra.strokeColor = None
            d.add(barra)
        texto = String(largura / 2, 10, f'{taxa:.1f}% de sucesso', textAnchor='middle')
        texto.fontSize = 10
        texto.fontName = 'Helvetica-Bold'
        texto.fillColor = colors.white if taxa > 40 else colors.HexColor('#374151')
        d.add(texto)
        return d

    def gerar_pdf_blob(self) -> str:
        """Gera relatório PDF bonito em memória e retorna como base64"""
        if not HAS_REPORTLAB:
            raise ImportError(
                "reportlab não está instalado. Execute: pip install reportlab"
            )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=2 * cm,
            title=f'Relatório de Validação - {self.layout.nome}',
            author='Validador de Documentos'
        )

        styles = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            'TituloPDF', parent=styles['Title'],
            fontSize=22, textColor=colors.HexColor('#1e3a5f'),
            spaceAfter=4 * mm, fontName='Helvetica-Bold', alignment=TA_CENTER,
        )
        estilo_subtitulo = ParagraphStyle(
            'SubtituloPDF', parent=styles['Heading2'],
            fontSize=14, textColor=colors.HexColor('#1e3a5f'),
            spaceBefore=8 * mm, spaceAfter=4 * mm, fontName='Helvetica-Bold',
        )
        estilo_info = ParagraphStyle(
            'InfoPDF', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER, spaceAfter=2 * mm,
        )
        estilo_normal = ParagraphStyle(
            'NormalPDF', parent=styles['Normal'],
            fontSize=9, textColor=colors.HexColor('#374151'), spaceAfter=2 * mm,
        )
        estilo_status = ParagraphStyle(
            'StatusPDF', parent=styles['Normal'],
            fontSize=14, alignment=TA_CENTER,
            spaceAfter=4 * mm, fontName='Helvetica-Bold',
        )

        elementos = []

        # ========== CABEÇALHO ==========
        elementos.append(Paragraph('Relatório de Validação', estilo_titulo))
        elementos.append(Paragraph(f'Layout: <b>{self.layout.nome}</b>', estilo_info))
        elementos.append(Paragraph(
            f'Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}', estilo_info
        ))
        elementos.append(Spacer(1, 4 * mm))
        elementos.append(HRFlowable(
            width='100%', thickness=2, color=colors.HexColor('#3b82f6'),
            spaceAfter=6 * mm, spaceBefore=2 * mm
        ))

        # ========== STATUS GERAL ==========
        taxa = self.resultado.taxa_sucesso
        if taxa == 100:
            status_texto, status_cor = 'APROVADO — Nenhum erro encontrado', '#16a34a'
        elif taxa >= 90:
            status_texto, status_cor = 'APROVADO COM RESSALVAS', '#d97706'
        else:
            status_texto, status_cor = 'REQUER CORREÇÃO', '#dc2626'

        estilo_status.textColor = colors.HexColor(status_cor)
        elementos.append(Paragraph(f'Status: {status_texto}', estilo_status))
        elementos.append(Spacer(1, 2 * mm))

        # ========== BARRA DE PROGRESSO ==========
        elementos.append(self._criar_barra_progresso(taxa))
        elementos.append(Spacer(1, 6 * mm))

        # ========== CARDS DE ESTATÍSTICAS ==========
        cards = Table(
            [[
                self._criar_card_estatistica('Total de Linhas',
                    f'{self.resultado.total_linhas:,}'.replace(',', '.'),
                    colors.HexColor('#3b82f6')),
                self._criar_card_estatistica('Linhas Válidas',
                    f'{self.resultado.linhas_validas:,}'.replace(',', '.'),
                    colors.HexColor('#16a34a')),
                self._criar_card_estatistica('Linhas com Erro',
                    f'{self.resultado.linhas_com_erro:,}'.replace(',', '.'),
                    colors.HexColor('#dc2626') if self.resultado.linhas_com_erro > 0 else colors.HexColor('#6b7280')),
                self._criar_card_estatistica('Taxa de Sucesso',
                    f'{taxa:.1f}%', self._cor_taxa(taxa)),
            ]],
            colWidths=[120, 120, 120, 120],
        )
        cards.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(cards)
        elementos.append(Spacer(1, 8 * mm))

        if not self.resultado.erros:
            elementos.append(Paragraph(
                'Parabéns! O arquivo foi validado com sucesso. Todos os registros '
                'estão em conformidade com o layout definido.',
                ParagraphStyle('Sucesso', parent=estilo_normal, fontSize=12,
                    alignment=TA_CENTER, textColor=colors.HexColor('#16a34a'),
                    spaceBefore=10 * mm)
            ))
            doc.build(elementos, onFirstPage=self._rodape_pdf, onLaterPages=self._rodape_pdf)
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

        # ========== DISTRIBUIÇÃO DE ERROS POR TIPO ==========
        elementos.append(Paragraph('Distribuição de Erros por Tipo', estilo_subtitulo))
        elementos.append(HRFlowable(width='100%', thickness=1,
            color=colors.HexColor('#e5e7eb'), spaceAfter=4 * mm))

        contador_tipos = Counter(erro.erro_tipo for erro in self.resultado.erros)
        elementos.append(self._criar_grafico_pizza(dict(contador_tipos.most_common(8)), altura=160))
        elementos.append(Spacer(1, 3 * mm))

        total_erros = len(self.resultado.erros)
        dados_tipo_tabela = [['Tipo de Erro', 'Quantidade', 'Percentual']]
        for tipo, qtd in contador_tipos.most_common():
            pct = (qtd / total_erros * 100) if total_erros > 0 else 0
            dados_tipo_tabela.append([tipo, f'{qtd:,}'.replace(',', '.'), f'{pct:.1f}%'])

        elementos.append(self._criar_tabela_estilizada(dados_tipo_tabela, [250, 100, 100]))
        elementos.append(Spacer(1, 4 * mm))

        # ========== TOP 10 CAMPOS COM MAIS ERROS ==========
        elementos.append(Paragraph('Campos com Mais Erros', estilo_subtitulo))
        elementos.append(HRFlowable(width='100%', thickness=1,
            color=colors.HexColor('#e5e7eb'), spaceAfter=4 * mm))

        contador_campos = Counter(erro.campo for erro in self.resultado.erros)
        dados_campo_tabela = [['Campo', 'Quantidade', 'Percentual']]
        for campo, qtd in contador_campos.most_common(10):
            pct = (qtd / total_erros * 100) if total_erros > 0 else 0
            dados_campo_tabela.append([campo, f'{qtd:,}'.replace(',', '.'), f'{pct:.1f}%'])

        elementos.append(self._criar_tabela_estilizada(dados_campo_tabela, [250, 120, 80]))
        elementos.append(Spacer(1, 4 * mm))

        # ========== DETALHES DOS ERROS ==========
        elementos.append(Paragraph('Detalhes dos Erros', estilo_subtitulo))
        elementos.append(HRFlowable(width='100%', thickness=1,
            color=colors.HexColor('#e5e7eb'), spaceAfter=4 * mm))

        max_erros_detalhe = min(len(self.resultado.erros), 200)
        if len(self.resultado.erros) > max_erros_detalhe:
            elementos.append(Paragraph(
                f'Exibindo os primeiros {max_erros_detalhe} de {len(self.resultado.erros):,} erros.',
                ParagraphStyle('Aviso', parent=estilo_normal,
                    textColor=colors.HexColor('#d97706'), fontSize=9)
            ))
            elementos.append(Spacer(1, 3 * mm))

        estilo_celula = ParagraphStyle(
            'Celula', parent=estilo_normal,
            fontSize=7, leading=9, spaceAfter=0, spaceBefore=0,
        )

        bloco_tamanho = 40
        erros_detalhe = self.resultado.erros[:max_erros_detalhe]

        for i in range(0, len(erros_detalhe), bloco_tamanho):
            bloco = erros_detalhe[i:i + bloco_tamanho]
            dados_detalhe = [['Linha', 'Campo', 'Tipo', 'Valor Encontrado', 'Descrição']]

            for erro in bloco:
                valor = erro.valor_encontrado[:30] + '...' if len(erro.valor_encontrado) > 30 else erro.valor_encontrado
                desc = erro.descricao[:60] + '...' if len(erro.descricao) > 60 else erro.descricao
                dados_detalhe.append([
                    str(erro.linha),
                    Paragraph(erro.campo, estilo_celula),
                    erro.erro_tipo,
                    Paragraph(valor, estilo_celula),
                    Paragraph(desc, estilo_celula),
                ])

            tabela_detalhe = Table(dados_detalhe, colWidths=[40, 100, 80, 90, 150], repeatRows=1)
            tabela_detalhe.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d1d5db')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            elementos.append(tabela_detalhe)
            if i + bloco_tamanho < len(erros_detalhe):
                elementos.append(PageBreak())

        # Rodapé final
        elementos.append(Spacer(1, 10 * mm))
        elementos.append(HRFlowable(width='100%', thickness=1,
            color=colors.HexColor('#e5e7eb'), spaceAfter=3 * mm))
        elementos.append(Paragraph(
            'Relatório gerado automaticamente pelo Validador de Documentos',
            ParagraphStyle('Rodape', parent=estilo_info, fontSize=8)
        ))

        doc.build(elementos, onFirstPage=self._rodape_pdf, onLaterPages=self._rodape_pdf)
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def _rodape_pdf(self, canvas, doc):
        """Desenha rodapé com numeração de páginas"""
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(colors.HexColor('#9ca3af'))
        canvas.drawString(1.5 * cm, 1 * cm, f'Validador de Documentos — {self.layout.nome}')
        canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f'Página {canvas.getPageNumber()}')
        canvas.setStrokeColor(colors.HexColor('#e5e7eb'))
        canvas.setLineWidth(0.5)
        canvas.line(1.5 * cm, 1.3 * cm, A4[0] - 1.5 * cm, 1.3 * cm)
        canvas.restoreState()

    def _criar_tabela_estilizada(self, dados, col_widths):
        """Cria tabela com estilo padrão do relatório"""
        tabela = Table(dados, colWidths=col_widths)
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        return tabela