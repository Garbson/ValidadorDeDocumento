#!/usr/bin/env python3
"""
Validador de Documentos Sequenciais
Ferramenta para validar arquivos TXT baseado em layouts Excel
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.text import Text

from src.layout_parser import LayoutParser
from src.file_validator import ValidadorArquivo
from src.report_generator import GeradorRelatorio


console = Console()


def mostrar_banner():
    """Mostra banner da aplicação"""
    banner = Text.from_markup("""
[bold blue]╔═══════════════════════════════════════╗[/bold blue]
[bold blue]║[/bold blue] [bold white]Validador de Documentos Sequenciais[/bold white] [bold blue]║[/bold blue]
[bold blue]║[/bold blue] [dim]Claro/Embratel - Análise de Arquivos[/dim]  [bold blue]║[/bold blue]
[bold blue]╚═══════════════════════════════════════╝[/bold blue]
""")
    console.print(banner)


def validar_arquivos_existem(layout_path: str, arquivo_path: str) -> bool:
    """Valida se os arquivos existem"""
    erros = []

    if not Path(layout_path).exists():
        erros.append(f"❌ Arquivo de layout não encontrado: {layout_path}")

    if not Path(arquivo_path).exists():
        erros.append(f"❌ Arquivo de dados não encontrado: {arquivo_path}")

    if erros:
        console.print("\n[bold red]Erros encontrados:[/bold red]")
        for erro in erros:
            console.print(f"  {erro}")
        return False

    return True


def mostrar_info_layout(layout):
    """Mostra informações do layout carregado"""
    table = Table(title="📋 Informações do Layout")
    table.add_column("Campo", style="cyan")
    table.add_column("Posição", style="magenta")
    table.add_column("Tamanho", style="green")
    table.add_column("Tipo", style="yellow")
    table.add_column("Obrigatório", style="red")
    table.add_column("Formato", style="blue")

    for campo in layout.campos:
        obrigatorio = "✅ Sim" if campo.obrigatorio else "❌ Não"
        formato = campo.formato or "-"
        table.add_row(
            campo.nome,
            f"{campo.posicao_inicio}-{campo.posicao_fim}",
            str(campo.tamanho),
            campo.tipo.value,
            obrigatorio,
            formato
        )

    console.print(table)
    console.print(f"\n[bold]Total de campos:[/bold] {len(layout.campos)}")
    console.print(f"[bold]Tamanho da linha:[/bold] {layout.tamanho_linha} caracteres\n")


def mostrar_resultado_validacao(resultado):
    """Mostra resultado da validação"""
    # Painel de estatísticas
    stats_text = f"""
[bold]Total de linhas:[/bold] {resultado.total_linhas:,}
[bold green]Linhas válidas:[/bold green] {resultado.linhas_validas:,}
[bold red]Linhas com erro:[/bold red] {resultado.linhas_com_erro:,}
[bold blue]Taxa de sucesso:[/bold blue] {resultado.taxa_sucesso:.2f}%
[bold yellow]Total de erros:[/bold yellow] {len(resultado.erros):,}
"""

    if resultado.taxa_sucesso >= 95:
        cor_painel = "green"
        icone = "✅"
    elif resultado.taxa_sucesso >= 80:
        cor_painel = "yellow"
        icone = "⚠️"
    else:
        cor_painel = "red"
        icone = "❌"

    console.print(Panel(stats_text, title=f"{icone} Resultado da Validação", border_style=cor_painel))

    # Mostrar resumo de erros se houver
    if resultado.erros:
        from collections import Counter

        console.print("\n[bold]📊 Resumo de Erros:[/bold]")

        # Top 5 tipos de erro
        tipos_erro = Counter(erro.erro_tipo for erro in resultado.erros)
        table_tipos = Table(title="Tipos de Erro Mais Comuns")
        table_tipos.add_column("Tipo", style="red")
        table_tipos.add_column("Quantidade", style="yellow")
        table_tipos.add_column("Percentual", style="blue")

        for tipo, qtd in tipos_erro.most_common(5):
            percentual = (qtd / len(resultado.erros)) * 100
            table_tipos.add_row(tipo, f"{qtd:,}", f"{percentual:.1f}%")

        console.print(table_tipos)

        # Top 5 campos com erro
        campos_erro = Counter(erro.campo for erro in resultado.erros)
        table_campos = Table(title="Campos com Mais Erros")
        table_campos.add_column("Campo", style="red")
        table_campos.add_column("Quantidade", style="yellow")
        table_campos.add_column("Percentual", style="blue")

        for campo, qtd in campos_erro.most_common(5):
            percentual = (qtd / len(resultado.erros)) * 100
            table_campos.add_row(campo, f"{qtd:,}", f"{percentual:.1f}%")

        console.print(table_campos)

        # Primeiros 10 erros detalhados
        if len(resultado.erros) > 0:
            console.print("\n[bold]🔍 Primeiros Erros Detalhados:[/bold]")
            table_detalhes = Table()
            table_detalhes.add_column("Linha", style="cyan")
            table_detalhes.add_column("Campo", style="magenta")
            table_detalhes.add_column("Erro", style="red")
            table_detalhes.add_column("Valor", style="yellow")

            for erro in resultado.erros[:10]:  # Primeiros 10
                table_detalhes.add_row(
                    str(erro.linha),
                    erro.campo,
                    erro.erro_tipo,
                    erro.valor_encontrado[:30] + "..." if len(erro.valor_encontrado) > 30 else erro.valor_encontrado
                )

            console.print(table_detalhes)

            if len(resultado.erros) > 10:
                console.print(f"\n[dim]... e mais {len(resultado.erros) - 10} erros. Veja o relatório completo para detalhes.[/dim]")


@click.command()
@click.option('--layout', '-l', required=True, help='Caminho para o arquivo Excel com o layout')
@click.option('--arquivo', '-a', required=True, help='Caminho para o arquivo TXT a ser validado')
@click.option('--relatorio', '-r', default='relatorios', help='Diretório para salvar relatórios (padrão: relatorios)')
@click.option('--max-erros', '-m', type=int, help='Limite máximo de erros a processar')
@click.option('--silencioso', '-s', is_flag=True, help='Modo silencioso (apenas resultado final)')
@click.option('--info-layout', is_flag=True, help='Mostrar apenas informações do layout')
def main(layout, arquivo, relatorio, max_erros, silencioso, info_layout):
    """
    Validador de Documentos Sequenciais

    Valida arquivos TXT baseado em layouts definidos em Excel.

    Exemplo de uso:
    python main.py -l layout.xlsx -a dados.txt
    """

    if not silencioso:
        mostrar_banner()

    try:
        # Validar se arquivos existem
        if not info_layout and not validar_arquivos_existem(layout, arquivo):
            sys.exit(1)
        elif info_layout and not Path(layout).exists():
            console.print(f"[bold red]❌ Arquivo de layout não encontrado: {layout}[/bold red]")
            sys.exit(1)

        # Carregar layout
        if not silencioso:
            console.print("📖 Carregando layout...")

        parser = LayoutParser()
        layout_obj = parser.parse_excel(layout)

        if not silencioso:
            console.print(f"[bold green]✅ Layout '{layout_obj.nome}' carregado com sucesso![/bold green]")

        # Se só quer info do layout, mostrar e sair
        if info_layout:
            mostrar_info_layout(layout_obj)
            return

        if not silencioso:
            mostrar_info_layout(layout_obj)

        # Validar arquivo
        validador = ValidadorArquivo(layout_obj)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console if not silencioso else Console(file=open('/dev/null', 'w'))
        ) as progress:

            task = progress.add_task("🔍 Validando arquivo...", total=None)

            resultado = validador.validar_arquivo(arquivo, max_erros)

            progress.update(task, completed=True)

        # Mostrar resultado
        if not silencioso:
            mostrar_resultado_validacao(resultado)

        # Gerar relatórios
        if not silencioso:
            console.print("\n📊 Gerando relatórios...")

        gerador = GeradorRelatorio(resultado, layout_obj)
        arquivos_relatorio = gerador.gerar_relatorio_completo(relatorio)

        # Mostrar caminhos dos relatórios
        console.print(f"\n[bold green]✅ Validação concluída![/bold green]")
        console.print(f"[bold]Relatórios salvos em:[/bold]")
        console.print(f"  📄 Texto: {arquivos_relatorio['texto']}")
        console.print(f"  📊 Excel: {arquivos_relatorio['excel']}")

        # Mostrar resumo final
        if resultado.taxa_sucesso >= 95:
            console.print(f"\n[bold green]🎉 Excelente! Taxa de sucesso: {resultado.taxa_sucesso:.2f}%[/bold green]")
        elif resultado.taxa_sucesso >= 80:
            console.print(f"\n[bold yellow]⚠️  Atenção! Taxa de sucesso: {resultado.taxa_sucesso:.2f}%[/bold yellow]")
        else:
            console.print(f"\n[bold red]❌ Muitos erros! Taxa de sucesso: {resultado.taxa_sucesso:.2f}%[/bold red]")

        # Código de saída baseado na taxa de sucesso
        if resultado.taxa_sucesso < 80:
            sys.exit(2)  # Muitos erros
        elif resultado.taxa_sucesso < 95:
            sys.exit(1)  # Alguns erros
        else:
            sys.exit(0)  # Sucesso

    except Exception as e:
        console.print(f"\n[bold red]❌ Erro durante a execução:[/bold red]")
        console.print(f"[red]{str(e)}[/red]")
        sys.exit(3)


if __name__ == '__main__':
    main()