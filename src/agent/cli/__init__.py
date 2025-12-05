"""
Agente Daktus | QA - CLI Module

CLI interativa com UX rica para análise de protocolos clínicos.

Módulos:
    - interactive_cli: Motor principal da CLI
    - task_manager: Gerenciamento de tasks visíveis
    - display_manager: Renderização de conteúdo rico
"""

from .interactive_cli import InteractiveCLI, SessionState
from .task_manager import TaskManager, Task, TaskStatus
from .display_manager import DisplayManager

__all__ = [
    "InteractiveCLI",
    "SessionState",
    "TaskManager",
    "Task",
    "TaskStatus",
    "DisplayManager"
]

