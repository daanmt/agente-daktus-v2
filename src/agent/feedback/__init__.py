"""
Feedback Module - Human-in-the-Loop System

Este módulo implementa o sistema de feedback e fine-tuning de prompts,
o diferencial do modo Enhanced.

Componentes:
- FeedbackCollector: Coleta feedback interativo do usuário
- FeedbackStorage: Persistência de feedback estruturado
- PromptRefiner: Refinamento automático de prompts baseado em feedback
"""

from .feedback_collector import FeedbackCollector, FeedbackSession, SuggestionFeedback
from .feedback_storage import FeedbackStorage
from .prompt_refiner import PromptRefiner, FeedbackPattern, PromptAdjustment

__all__ = [
    "FeedbackCollector",
    "FeedbackSession",
    "SuggestionFeedback",
    "FeedbackStorage",
    "PromptRefiner",
    "FeedbackPattern",
    "PromptAdjustment"
]
