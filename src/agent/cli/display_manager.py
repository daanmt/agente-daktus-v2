"""
Display Manager - Renderização de Conteúdo Rico

Responsabilidades:
- Renderizar relatórios formatados
- Exibir tabelas de sugestões
- Mostrar diff visual de mudanças
- Formatação de custos e métricas

Usa biblioteca 'rich' para UI rica no terminal.

Status: ✅ IMPLEMENTADO
"""

from typing import List, Dict, Optional, Any, ContextManager
from datetime import datetime
import json
from contextlib import contextmanager

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.text import Text
    from rich.markdown import Markdown
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Table = None
    Panel = None
    Syntax = None
    Progress = None
    Text = None
    Markdown = None
    box = None


class DisplayManager:
    """
    Gerencia renderização de conteúdo rico no terminal.

    Características:
    - Syntax highlighting para JSON
    - Tabelas formatadas
    - Diff colorido (verde/vermelho)
    - Formatação de valores monetários
    - Progress bars e spinners

    Example:
        >>> display = DisplayManager()
        >>> display.show_suggestions_table(suggestions)
        >>> display.show_cost_estimate(estimate)
    """

    def __init__(self):
        """Inicializa o gerenciador de display."""
        if RICH_AVAILABLE:
            self.console = Console()
            self.rich_available = True
        else:
            self.console = None
            self.rich_available = False

    def show_banner(
        self,
        title: str,
        subtitle: Optional[str] = None,
        style: str = "bold cyan"
    ) -> None:
        """
        Exibe banner de texto formatado.

        Args:
            title: Título principal
            subtitle: Subtítulo opcional
            style: Estilo do texto (rich style string)
        """
        if self.rich_available:
            content = f"[{style}]{title}[/{style}]"
            if subtitle:
                content += f"\n[dim]{subtitle}[/dim]"
            panel = Panel(
                content,
                box=box.ROUNDED,
                padding=(1, 2),
                title="Agente Daktus | QA",
                title_align="center"
            )
            self.console.print(panel)
        else:
            print("=" * 60)
            print(title)
            if subtitle:
                print(subtitle)
            print("=" * 60)

    def show_suggestions_table(
        self,
        suggestions: List[Dict],
        max_rows: int = 20
    ) -> None:
        """
        Exibe tabela formatada de sugestões.

        Colunas:
        - ID
        - Prioridade
        - Categoria
        - Título
        - Impacto (Segurança/Economia)

        Args:
            suggestions: Lista de sugestões (dicts)
            max_rows: Número máximo de linhas a exibir (padrão: 20)
        """
        if not suggestions:
            self.show_info("Nenhuma sugestão disponível.")
            return

        if self.rich_available:
            table = Table(
                title="Sugestões de Melhoria",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
                title_style="bold cyan"
            )

            # Adicionar colunas
            table.add_column("ID", style="cyan", width=6)
            table.add_column("Prioridade", style="yellow", width=10)
            table.add_column("Categoria", style="green", width=12)
            table.add_column("Título", style="white", width=40)
            table.add_column("Segurança", style="red", width=8, justify="center")
            table.add_column("Economia", style="blue", width=8, justify="center")

            # Adicionar linhas (limitado a max_rows)
            display_count = min(len(suggestions), max_rows)
            for i, sug in enumerate(suggestions[:display_count]):
                sug_id = sug.get("id", f"SUG{i+1:02d}")
                priority = sug.get("priority", "N/A")
                category = sug.get("category", "N/A")
                title = sug.get("title", sug.get("description", "N/A"))[:40]
                
                # Impact scores
                impact_scores = sug.get("impact_scores", {})
                safety = impact_scores.get("seguranca", 0)
                economy = impact_scores.get("economia", "N/A")
                
                # Colorir prioridade
                priority_style = {
                    "alta": "bold red",
                    "high": "bold red",
                    "media": "bold yellow",
                    "medium": "bold yellow",
                    "baixa": "dim",
                    "low": "dim"
                }.get(priority.lower(), "")

                table.add_row(
                    sug_id,
                    f"[{priority_style}]{priority.upper()}[/{priority_style}]" if priority_style else priority,
                    category,
                    title,
                    str(safety) if isinstance(safety, (int, float)) else "N/A",
                    str(economy) if economy != "N/A" else "N/A"
                )

            self.console.print(table)

            # Indicar se há mais sugestões
            if len(suggestions) > max_rows:
                remaining = len(suggestions) - max_rows
                self.console.print(
                    f"\n[dim]... e mais {remaining} sugestões (total: {len(suggestions)})[/dim]"
                )
        else:
            # Fallback simples
            print("\nSUGESTÕES DE MELHORIA")
            print("-" * 80)
            for i, sug in enumerate(suggestions[:max_rows]):
                sug_id = sug.get("id", f"SUG{i+1:02d}")
                priority = sug.get("priority", "N/A")
                category = sug.get("category", "N/A")
                title = sug.get("title", sug.get("description", "N/A"))
                print(f"{sug_id} | {priority:10s} | {category:12s} | {title[:40]}")
            if len(suggestions) > max_rows:
                print(f"\n... e mais {len(suggestions) - max_rows} sugestões")

    def show_cost_estimate(
        self,
        estimate: Dict
    ) -> None:
        """
        Exibe estimativa de custo formatada.

        Args:
            estimate: Dict com campos:
                - model: Nome do modelo
                - estimated_tokens: Dict com input/output
                - estimated_cost_usd: Dict com input/output/total
                - confidence: Nível de confiança
        """
        if self.rich_available:
            model = estimate.get("model", "N/A")
            tokens = estimate.get("estimated_tokens", {})
            costs = estimate.get("estimated_cost_usd", {})
            confidence = estimate.get("confidence", "medium")

            input_tokens = tokens.get("input", 0)
            output_tokens = tokens.get("output", 0)
            total_tokens = input_tokens + output_tokens

            input_cost = costs.get("input", 0.0)
            output_cost = costs.get("output", 0.0)
            total_cost = costs.get("total", input_cost + output_cost)

            # Construir conteúdo
            content = f"""
[bold]Modelo:[/bold] {model}

[bold]Tokens Estimados:[/bold]
  Input:  {input_tokens:,} tokens (${input_cost:.4f})
  Output: {output_tokens:,} tokens (${output_cost:.4f})
  Total:  {total_tokens:,} tokens

[bold]Custo Total Estimado:[/bold] ${total_cost:.4f} USD
[bold]Confiança:[/bold] {confidence.upper()}
            """.strip()

            panel = Panel(
                content,
                box=box.ROUNDED,
                title="💰 Estimativa de Custo",
                title_align="left",
                border_style="cyan"
            )
            self.console.print(panel)
        else:
            # Fallback simples
            print("\nESTIMATIVA DE CUSTO")
            print("-" * 60)
            print(f"Modelo: {estimate.get('model', 'N/A')}")
            tokens = estimate.get("estimated_tokens", {})
            costs = estimate.get("estimated_cost_usd", {})
            print(f"Tokens Input: {tokens.get('input', 0):,}")
            print(f"Tokens Output: {tokens.get('output', 0):,}")
            print(f"Custo Total: ${costs.get('total', 0.0):.4f} USD")

    def show_diff(
        self,
        changes: List[Dict]
    ) -> None:
        """
        Exibe diff visual de mudanças.

        Args:
            changes: Lista de mudanças, cada uma com:
                - type: "added", "modified", "removed"
                - location: Onde a mudança ocorreu
                - description: Descrição da mudança
        """
        if not changes:
            self.show_info("Nenhuma mudança aplicada.")
            return

        if self.rich_available:
            content_lines = []
            for change in changes:
                change_type = change.get("type", "modified")
                location = change.get("location", "N/A")
                description = change.get("description", "N/A")

                if change_type == "added":
                    icon = "[green]+[/green]"
                    prefix = "[green]Adicionado:[/green]"
                elif change_type == "removed":
                    icon = "[red]-[/red]"
                    prefix = "[red]Removido:[/red]"
                else:
                    icon = "[yellow]~[/yellow]"
                    prefix = "[yellow]Modificado:[/yellow]"

                content_lines.append(f"{icon} {prefix} {location}")
                content_lines.append(f"    {description}")

            content = "\n".join(content_lines)
            panel = Panel(
                content,
                box=box.ROUNDED,
                title="📝 Mudanças Aplicadas",
                title_align="left",
                border_style="yellow"
            )
            self.console.print(panel)
        else:
            # Fallback simples
            print("\nMUDANÇAS APLICADAS")
            print("-" * 60)
            for change in changes:
                change_type = change.get("type", "modified")
                location = change.get("location", "N/A")
                description = change.get("description", "N/A")
                icon = {"added": "+", "removed": "-", "modified": "~"}.get(change_type, "~")
                print(f"{icon} {change_type.upper()}: {location}")
                print(f"  {description}")

    def show_json_highlighted(
        self,
        json_data: Dict,
        title: Optional[str] = None
    ) -> None:
        """
        Exibe JSON com syntax highlighting.

        Args:
            json_data: Dados JSON (dict)
            title: Título opcional
        """
        if self.rich_available:
            try:
                json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
                
                if title:
                    panel = Panel(
                        syntax,
                        title=title,
                        title_align="left",
                        border_style="blue"
                    )
                    self.console.print(panel)
                else:
                    self.console.print(syntax)
            except Exception as e:
                self.show_error(f"Erro ao formatar JSON: {e}")
                print(json.dumps(json_data, indent=2))
        else:
            # Fallback simples
            if title:
                print(f"\n{title}")
                print("-" * 60)
            print(json.dumps(json_data, indent=2))

    def show_thinking(
        self,
        thought: str,
        duration: Optional[float] = None
    ) -> None:
        """
        Exibe mensagem de "thinking" do sistema.

        Args:
            thought: Mensagem de thinking
            duration: Duração estimada em segundos (opcional)
        """
        if self.rich_available:
            duration_str = f" (~{duration:.0f}s)" if duration else ""
            content = f"💭 [cyan]{thought}[/cyan]{duration_str}"
            self.console.print(content)
        else:
            duration_str = f" (~{duration:.0f}s)" if duration else ""
            print(f"💭 {thought}{duration_str}")

    def show_success(self, message: str) -> None:
        """Exibe mensagem de sucesso."""
        if self.rich_available:
            self.console.print(f"[green]✓[/green] [bold green]{message}[/bold green]")
        else:
            print(f"OK: {message}")

    def show_error(self, message: str) -> None:
        """Exibe mensagem de erro."""
        if self.rich_available:
            self.console.print(f"[red]✗[/red] [bold red]{message}[/bold red]")
        else:
            print(f"ERRO: {message}")

    def show_warning(self, message: str) -> None:
        """Exibe mensagem de aviso."""
        if self.rich_available:
            self.console.print(f"[yellow]⚠[/yellow] [bold yellow]{message}[/bold yellow]")
        else:
            print(f"AVISO: {message}")

    def show_info(self, message: str) -> None:
        """Exibe mensagem informativa."""
        if self.rich_available:
            self.console.print(f"[blue]ℹ[/blue] [cyan]{message}[/cyan]")
        else:
            print(f"INFO: {message}")

    def create_progress_bar(
        self,
        description: str,
        total: int = 100
    ) -> ContextManager[Progress]:
        """
        Cria e retorna um context manager de progress bar.

        Args:
            description: Descrição da operação
            total: Total de itens (padrão: 100)

        Returns:
            Context manager que pode ser usado com 'with'

        Example:
            >>> with display.create_progress_bar("Processando...", 50) as progress:
            ...     task = progress.add_task(description, total=50)
            ...     for i in range(50):
            ...         progress.update(task, advance=1)
        """
        if self.rich_available:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console
            )
            return progress
        else:
            # Fallback: context manager simples que não faz nada
            class SimpleProgress:
                def __init__(self):
                    self.task_id = 0

                def __enter__(self):
                    print(f"Processando: {description}...")
                    return self
                def __exit__(self, *args):
                    print("Concluído!")
                def add_task(self, *args, **kwargs):
                    return self.task_id
                def update(self, task_id=None, advance: int = 0, **kwargs):
                    return None
            return SimpleProgress()

    @contextmanager
    def spinner(self, message: str, transient: bool = True):
        """
        Context manager para exibir spinner durante operações de I/O.

        Args:
            message: Mensagem a exibir
            transient: Se True, remove o spinner ao finalizar
        """
        if self.rich_available:
            progress = Progress(
                SpinnerColumn(),
                TextColumn(f"[progress.description]{message}"),
                transient=transient,
                console=self.console,
            )
            progress.start()
            task_id = progress.add_task(message, total=None)
            try:
                yield
            finally:
                progress.stop()
        else:
            try:
                print(f"{message} ...")
                yield
            finally:
                print("Concluído.")

    def show_summary_panel(
        self,
        title: str,
        items: Dict[str, Any]
    ) -> None:
        """
        Exibe painel de resumo com itens formatados.

        Args:
            title: Título do painel
            items: Dict com chave-valor para exibir
        """
        if self.rich_available:
            content_lines = []
            for key, value in items.items():
                content_lines.append(f"[bold]{key}:[/bold] {value}")
            
            content = "\n".join(content_lines)
            panel = Panel(
                content,
                box=box.ROUNDED,
                title=title,
                title_align="center",
                border_style="cyan"
            )
            self.console.print(panel)
        else:
            print(f"\n{title}")
            print("-" * 60)
            for key, value in items.items():
                print(f"{key}: {value}")

