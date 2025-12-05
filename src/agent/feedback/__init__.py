"""
Feedback Module - Human-in-the-Loop System

Este módulo implementa o sistema de feedback e melhoria contínua de análises.

Componentes:
- FeedbackCollector: Coleta feedback interativo do usuário
- FeedbackStorage: Persistência de feedback estruturado (backup opcional)
- MemoryQA: Sistema simples de memória via markdown (memory_qa.md)
- PromptRefiner: [DEPRECATED] Mantido para referência, não usar no fluxo principal
- MemoryManager: [DEPRECATED] Mantido para referência, não usar no fluxo principal
"""

from .feedback_collector import FeedbackCollector, FeedbackSession, SuggestionFeedback
from .feedback_storage import FeedbackStorage
from .memory_qa import MemoryQA, FeedbackPattern

# Componentes deprecated (mantidos para referência)
from .prompt_refiner import PromptRefiner, PromptAdjustment
from .memory_manager import MemoryManager, MemoryEntry

__all__ = [
    "FeedbackCollector",
    "FeedbackSession",
    "SuggestionFeedback",
    "FeedbackStorage",
    "MemoryQA",
    "FeedbackPattern",
    # Deprecated (mantidos para referência)
    "PromptRefiner",
    "PromptAdjustment",
    "MemoryManager",
    "MemoryEntry"
]
