"""
Feedback Module - Human-in-the-Loop System

Este módulo implementa o sistema de feedback e melhoria contínua de análises.

Componentes:
- FeedbackCollector: Coleta feedback interativo do usuário
- FeedbackStorage: Persistência de feedback estruturado (backup opcional)
- MemoryQA: Sistema simples de memória via markdown (memory_qa.md)
"""

from .feedback_collector import FeedbackCollector, FeedbackSession, SuggestionFeedback
from .feedback_storage import FeedbackStorage
from .memory_qa import MemoryQA, FeedbackPattern

__all__ = [
    "FeedbackCollector",
    "FeedbackSession",
    "SuggestionFeedback",
    "FeedbackStorage",
    "MemoryQA",
    "FeedbackPattern",
]
