"""
Task Manager - Gerenciamento de Tasks Visíveis

Responsabilidades:
- Criar e gerenciar tasks visíveis ao usuário
- Atualizar status de tasks em tempo real
- Exibir lista de tasks (pending, in_progress, completed)

Status: ✅ IMPLEMENTADO
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Table = None
    box = None


class TaskStatus(Enum):
    """Status de uma task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """
    Representa uma task visível ao usuário.

    Attributes:
        id: ID único da task
        description: Descrição da task
        status: Status atual
        progress: Progresso 0.0-1.0 (opcional)
        estimated_duration: Duração estimada (opcional)
        created_at: Timestamp de criação
        completed_at: Timestamp de conclusão (opcional)
        error_message: Mensagem de erro se falhou (opcional)
    """
    id: str
    description: str
    status: TaskStatus
    progress: float = 0.0
    estimated_duration: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class TaskManager:
    """
    Gerencia tasks visíveis ao usuário.

    As tasks são exibidas em tempo real durante a execução,
    dando transparência total sobre o que está acontecendo.

    Example:
        >>> manager = TaskManager()
        >>> manager.add_task("load_protocol", "Carregar protocolo JSON", "5s")
        >>> manager.update_status("load_protocol", TaskStatus.IN_PROGRESS)
        >>> manager.mark_completed("load_protocol")
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Inicializa o gerenciador de tasks.

        Args:
            console: Console rich (opcional, para renderização)
        """
        self.tasks: List[Task] = []
        self.console = console

    def add_task(
        self,
        task_id: str,
        description: str,
        estimated_duration: Optional[str] = None
    ) -> None:
        """
        Adiciona uma nova task.

        Args:
            task_id: ID único da task
            description: Descrição da task
            estimated_duration: Duração estimada (ex: "30s", "2min")
        """
        # Verificar se task já existe
        existing = self.get_task(task_id)
        if existing:
            raise ValueError(f"Task '{task_id}' já existe")

        task = Task(
            id=task_id,
            description=description,
            status=TaskStatus.PENDING,
            estimated_duration=estimated_duration
        )
        self.tasks.append(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Obtém uma task por ID.

        Args:
            task_id: ID da task

        Returns:
            Task ou None se não encontrada
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update_status(
        self,
        task_id: str,
        status: TaskStatus
    ) -> None:
        """
        Atualiza status de uma task.

        Args:
            task_id: ID da task
            status: Novo status
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' não encontrada")

        task.status = status

        # Atualizar completed_at se concluída
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.progress = 1.0
        elif status == TaskStatus.FAILED:
            task.completed_at = datetime.now()

    def update_progress(
        self,
        task_id: str,
        progress: float
    ) -> None:
        """
        Atualiza progresso de uma task.

        Args:
            task_id: ID da task
            progress: Progresso 0.0-1.0
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' não encontrada")

        # Garantir que progress está entre 0.0 e 1.0
        task.progress = max(0.0, min(1.0, progress))

        # Se progresso chegou a 1.0, marcar como in_progress se ainda estiver pending
        if task.progress >= 1.0 and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.IN_PROGRESS

    def mark_completed(self, task_id: str) -> None:
        """
        Marca uma task como concluída.

        Args:
            task_id: ID da task
        """
        self.update_status(task_id, TaskStatus.COMPLETED)

    def mark_failed(self, task_id: str, error_message: str) -> None:
        """
        Marca uma task como falhada.

        Args:
            task_id: ID da task
            error_message: Mensagem de erro
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' não encontrada")

        task.status = TaskStatus.FAILED
        task.error_message = error_message
        task.completed_at = datetime.now()

    def render_tasks(self, display_manager=None) -> None:
        """
        Renderiza lista de tasks.

        Args:
            display_manager: DisplayManager opcional para renderização rica
        """
        if not self.tasks:
            return

        if display_manager and RICH_AVAILABLE:
            # Renderizar com rich table
            table = Table(
                box=box.SIMPLE,
                show_header=False,
                padding=(0, 1)
            )
            table.add_column("Status", width=3)
            table.add_column("Description", width=60)
            table.add_column("Progress", width=20)

            for task in self.tasks:
                # Ícone baseado no status
                if task.status == TaskStatus.COMPLETED:
                    icon = "[green]✓[/green]"
                    status_text = ""
                elif task.status == TaskStatus.FAILED:
                    icon = "[red]✗[/red]"
                    status_text = f"[red]{task.error_message or 'Falhou'}[/red]"
                elif task.status == TaskStatus.IN_PROGRESS:
                    icon = "[yellow]⚙[/yellow]"
                    progress_pct = int(task.progress * 100)
                    status_text = f"[yellow]{progress_pct}%[/yellow]"
                else:  # PENDING
                    icon = "[dim]⏳[/dim]"
                    status_text = "[dim]Aguardando...[/dim]"

                # Descrição com duração estimada
                description = task.description
                if task.estimated_duration and task.status != TaskStatus.COMPLETED:
                    description += f" [dim](~{task.estimated_duration})[/dim]"

                # Progress bar simples (se in_progress)
                if task.status == TaskStatus.IN_PROGRESS and task.progress > 0:
                    progress_bar = f"[{'█' * int(task.progress * 10)}{'░' * (10 - int(task.progress * 10))}]"
                else:
                    progress_bar = ""

                table.add_row(icon, description, status_text or progress_bar)

            if self.console:
                self.console.print(table)
            elif display_manager and hasattr(display_manager, 'console'):
                display_manager.console.print(table)
        else:
            # Fallback simples
            print("\nTASKS:")
            for task in self.tasks:
                if task.status == TaskStatus.COMPLETED:
                    icon = "✓"
                elif task.status == TaskStatus.FAILED:
                    icon = "✗"
                elif task.status == TaskStatus.IN_PROGRESS:
                    icon = "⚙"
                else:
                    icon = "⏳"

                duration = f" (~{task.estimated_duration})" if task.estimated_duration else ""
                progress = f" [{int(task.progress * 100)}%]" if task.progress > 0 else ""
                error = f" - {task.error_message}" if task.error_message else ""

                print(f"{icon} {task.description}{duration}{progress}{error}")

    def clear_tasks(self) -> None:
        """Limpa todas as tasks."""
        self.tasks.clear()

    def get_pending_tasks(self) -> List[Task]:
        """Retorna lista de tasks pendentes."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def get_in_progress_tasks(self) -> List[Task]:
        """Retorna lista de tasks em progresso."""
        return [t for t in self.tasks if t.status == TaskStatus.IN_PROGRESS]

    def get_completed_tasks(self) -> List[Task]:
        """Retorna lista de tasks concluídas."""
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED]

    def get_failed_tasks(self) -> List[Task]:
        """Retorna lista de tasks falhadas."""
        return [t for t in self.tasks if t.status == TaskStatus.FAILED]

    def has_failed_tasks(self) -> bool:
        """Verifica se há tasks falhadas."""
        return len(self.get_failed_tasks()) > 0

    def all_completed(self) -> bool:
        """Verifica se todas as tasks foram concluídas."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            for t in self.tasks
        )

