"""
Agent V3 - CLI Module

CLI interativa inspirada no Claude Code com UX excepcional.

Módulos:
    - interactive_cli: Motor principal da CLI
    - task_manager: Gerenciamento de tasks visíveis
    - display_manager: Renderização de conteúdo rico
"""

from .interactive_cli import InteractiveCLI, SessionState
from .task_manager import TaskManager, Task
from .display_manager import DisplayManager

__all__ = [
    "InteractiveCLI",
    "SessionState",
    "TaskManager",
    "Task",
    "DisplayManager"
]
