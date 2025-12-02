"""
Agent V3 - Analysis Module

Este módulo contém componentes para análise expandida de protocolos clínicos.

Módulos:
    - enhanced_analyzer: Análise V2 expandida com 20-50 sugestões
    - impact_scorer: Scoring detalhado de impacto por categoria
"""

from .enhanced_analyzer import EnhancedAnalyzer
from .impact_scorer import ImpactScorer

__all__ = ["EnhancedAnalyzer", "ImpactScorer"]
