import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import Counter

try:
    from .models import ResultadoValidacao, ErroValidacao, Layout
except ImportError:
    from models import ResultadoValidacao, ErroValidacao, Layout


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

        return {
            'texto': str(caminho_txt),
            'excel': str(caminho_excel),
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