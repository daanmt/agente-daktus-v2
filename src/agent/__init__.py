"""
Agente Daktus | QA - Sistema Unificado de Validação e Correção de Protocolos Clínicos

Este é o módulo principal unificado que consolida todas as funcionalidades do Agente Daktus QA.
O versionamento é feito via tags/branches Git, não via estrutura de pastas separadas.

Componentes Principais:
- core: Componentes compartilhados (LLM client, logger, loaders, etc.)
- analysis: Análise de protocolos (standard e enhanced)
- applicator: Auto-apply de melhorias
- feedback: Sistema de feedback e fine-tuning
- cost_control: Controle de custos e autorização
- cli: CLI interativa avançada
"""

__version__ = "3.0.0"
__author__ = "Daktus QA Team"

# Core components
from .core import (
    LLMClient,
    logger,
    load_protocol,
    load_playbook,
    PromptBuilder,
    ResponseValidator
)

# Analysis pipelines
from .analysis.standard import analyze as analyze_standard
from .analysis.enhanced import EnhancedAnalyzer

# Applicator
from .applicator import ProtocolReconstructor

# Feedback
from .feedback import FeedbackCollector, MemoryQA

# Cost control
from .cost_control import CostEstimator

# CLI
from .cli import InteractiveCLI, DisplayManager, TaskManager

__all__ = [
    # Core
    "LLMClient",
    "logger",
    "load_protocol",
    "load_playbook",
    "PromptBuilder",
    "ResponseValidator",
    # Analysis
    "analyze_standard",
    "EnhancedAnalyzer",
    # Applicator
    "ProtocolReconstructor",
    # Feedback
    "FeedbackCollector",
    "MemoryQA",
    # Cost control
    "CostEstimator",
    # CLI
    "InteractiveCLI",
    "DisplayManager",
    "TaskManager",
]

