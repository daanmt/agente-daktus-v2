"""
Impact Scorer - Scoring de Impacto Detalhado

Responsabilidades:
- Calcular scores de impacto para cada sugestão
- Categorias: Segurança (0-10), Economia (L/M/A), Eficiência (L/M/A), Usabilidade (0-10)
- Priorização automática baseada em scores

Fase de Implementação: FASE 1 (4-6 dias)
Status: ✅ Implementado
"""

import sys
from pathlib import Path
from typing import Dict, Union
from dataclasses import dataclass

# Add src to path for imports
current_dir = Path(__file__).resolve().parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from agent_v2.logger import logger


@dataclass
class ImpactScores:
    """
    Scores de impacto para uma sugestão.

    Attributes:
        seguranca: Score 0-10 (impacto na segurança do paciente)
        economia: L/M/A (impacto econômico)
        eficiencia: L/M/A (impacto na eficiência)
        usabilidade: Score 0-10 (impacto na usabilidade)
    """
    seguranca: int  # 0-10
    economia: str   # L/M/A
    eficiencia: str  # L/M/A
    usabilidade: int  # 0-10


class ImpactScorer:
    """
    Calcula scores de impacto para sugestões de melhoria.

    Este componente avalia o impacto potencial de cada sugestão
    em múltiplas dimensões: segurança, economia, eficiência e usabilidade.

    Algoritmo de Priorização:
    - Alta: Segurança ≥8 OU (Economia=A E Segurança≥5)
    - Média: Segurança 5-7 OU Economia M/A
    - Baixa: Demais casos

    Example:
        >>> scorer = ImpactScorer()
        >>> scores = scorer.calculate_impact_scores(suggestion)
        >>> priority = scorer.calculate_priority(scores)
        >>> print(f"Prioridade: {priority}")
    """

    def __init__(self):
        """Inicializa o scorer de impacto."""
        # Thresholds para priorização
        self.safety_high_threshold = 8
        self.safety_medium_threshold = 5
        self.economic_high_threshold = "A"
        self.efficiency_high_threshold = "A"
        
        logger.debug("ImpactScorer initialized")

    def calculate_impact_scores(
        self,
        suggestion: Dict
    ) -> ImpactScores:
        """
        Calcula scores de impacto para uma sugestão.

        Args:
            suggestion: Sugestão de melhoria (dict ou Suggestion object)

        Returns:
            ImpactScores com scores calculados
        """
        # Extract scores if already present
        if isinstance(suggestion, dict):
            impact_scores = suggestion.get("impact_scores", {})
            seguranca = impact_scores.get("seguranca", 0)
            economia = impact_scores.get("economia", "L")
            eficiencia = impact_scores.get("eficiencia", "L")
            usabilidade = impact_scores.get("usabilidade", 0)
        else:
            # Assume it's a Suggestion object
            seguranca = suggestion.impact_scores.get("seguranca", 0)
            economia = suggestion.impact_scores.get("economia", "L")
            eficiencia = suggestion.impact_scores.get("eficiencia", "L")
            usabilidade = suggestion.impact_scores.get("usabilidade", 0)
        
        # If scores are missing or zero, try to calculate from content
        if seguranca == 0 and isinstance(suggestion, dict):
            seguranca = self.score_safety_impact(suggestion)
        if usabilidade == 0 and isinstance(suggestion, dict):
            usabilidade = self.score_usability_impact(suggestion)
        if economia == "L" and isinstance(suggestion, dict):
            economia = self.score_economic_impact(suggestion)
        if eficiencia == "L" and isinstance(suggestion, dict):
            eficiencia = self.score_efficiency_impact(suggestion)
        
        return ImpactScores(
            seguranca=seguranca,
            economia=economia,
            eficiencia=eficiencia,
            usabilidade=usabilidade
        )

    def calculate_priority(
        self,
        scores: ImpactScores
    ) -> str:
        """
        Calcula prioridade baseada em scores.

        Algoritmo:
        - Alta: Segurança ≥8 OU (Economia=A E Segurança≥5)
        - Média: Segurança 5-7 OU Economia M/A OU Eficiência A
        - Baixa: Demais casos

        Args:
            scores: Scores de impacto

        Returns:
            Prioridade: "alta", "media", "baixa"
        """
        if scores.seguranca >= self.safety_high_threshold:
            return "alta"
        
        if scores.economia == "A" and scores.seguranca >= self.safety_medium_threshold:
            return "alta"
        
        if (self.safety_medium_threshold <= scores.seguranca < self.safety_high_threshold):
            return "media"
        
        if scores.economia in ("M", "A"):
            return "media"
        
        if scores.eficiencia == "A":
            return "media"
        
        return "baixa"

    def score_safety_impact(
        self,
        suggestion: Dict
    ) -> int:
        """
        Calcula score de impacto em segurança (0-10).

        Args:
            suggestion: Sugestão de melhoria

        Returns:
            Score 0-10
        """
        description = suggestion.get("description", "").lower()
        title = suggestion.get("title", "").lower()
        category = suggestion.get("category", "").lower()
        rationale = suggestion.get("rationale", "").lower()
        
        text = f"{title} {description} {rationale}"
        
        # High safety impact keywords
        high_safety_keywords = [
            "red flag", "contraindication", "allergy", "adverse", "side effect",
            "emergency", "urgent", "critical", "life-threatening", "safety",
            "segurança", "contraindicação", "alergia", "emergência", "urgente",
            "crítico", "risco", "perigo", "adverso", "efeito colateral"
        ]
        
        # Medium safety impact keywords
        medium_safety_keywords = [
            "warning", "caution", "monitor", "follow-up", "precaution",
            "aviso", "cuidado", "monitorar", "acompanhamento", "precaução"
        ]
        
        # Count matches
        high_count = sum(1 for keyword in high_safety_keywords if keyword in text)
        medium_count = sum(1 for keyword in medium_safety_keywords if keyword in text)
        
        # Calculate score
        if category == "seguranca":
            base_score = 7
        else:
            base_score = 0
        
        if high_count > 0:
            return min(10, base_score + high_count * 2)
        elif medium_count > 0:
            return min(7, base_score + medium_count)
        else:
            return max(0, base_score - 2)

    def score_economic_impact(
        self,
        suggestion: Dict
    ) -> str:
        """
        Calcula score de impacto econômico (L/M/A).

        Args:
            suggestion: Sugestão de melhoria

        Returns:
            "L" (baixo), "M" (médio), "A" (alto)
        """
        description = suggestion.get("description", "").lower()
        title = suggestion.get("title", "").lower()
        category = suggestion.get("category", "").lower()
        
        text = f"{title} {description}"
        
        # High economic impact keywords
        high_economic_keywords = [
            "cost", "custo", "economy", "economia", "save", "economizar",
            "reduce cost", "reduzir custo", "expensive", "caro", "budget",
            "orçamento", "resource", "recurso", "waste", "desperdício"
        ]
        
        # Medium economic impact keywords
        medium_economic_keywords = [
            "optimize", "otimizar", "efficient", "eficiente", "streamline"
        ]
        
        if category == "economia":
            # Check for high impact indicators
            if any(keyword in text for keyword in high_economic_keywords):
                return "A"
            elif any(keyword in text for keyword in medium_economic_keywords):
                return "M"
            else:
                return "M"  # Default to medium for economia category
        else:
            # Low economic impact for non-economia categories
            return "L"

    def score_efficiency_impact(
        self,
        suggestion: Dict
    ) -> str:
        """
        Calcula score de impacto em eficiência (L/M/A).

        Args:
            suggestion: Sugestão de melhoria

        Returns:
            "L" (baixo), "M" (médio), "A" (alto)
        """
        description = suggestion.get("description", "").lower()
        title = suggestion.get("title", "").lower()
        category = suggestion.get("category", "").lower()
        
        text = f"{title} {description}"
        
        # High efficiency impact keywords
        high_efficiency_keywords = [
            "automate", "automatizar", "reduce steps", "reduzir etapas",
            "faster", "mais rápido", "speed up", "acelerar", "streamline",
            "simplify", "simplificar", "workflow", "fluxo", "bottleneck",
            "gargalo", "optimize", "otimizar"
        ]
        
        # Medium efficiency impact keywords
        medium_efficiency_keywords = [
            "improve", "melhorar", "enhance", "aperfeiçoar", "refine", "refinar"
        ]
        
        if category == "eficiencia":
            # Check for high impact indicators
            if any(keyword in text for keyword in high_efficiency_keywords):
                return "A"
            elif any(keyword in text for keyword in medium_efficiency_keywords):
                return "M"
            else:
                return "M"  # Default to medium for eficiencia category
        else:
            # Low efficiency impact for non-eficiencia categories
            return "L"

    def score_usability_impact(
        self,
        suggestion: Dict
    ) -> int:
        """
        Calcula score de impacto em usabilidade (0-10).

        Args:
            suggestion: Sugestão de melhoria

        Returns:
            Score 0-10
        """
        description = suggestion.get("description", "").lower()
        title = suggestion.get("title", "").lower()
        category = suggestion.get("category", "").lower()
        
        text = f"{title} {description}"
        
        # High usability impact keywords
        high_usability_keywords = [
            "user experience", "experiência do usuário", "ux", "interface",
            "clarity", "clareza", "clear", "intuitive", "intuitivo",
            "easy to use", "fácil de usar", "user-friendly", "amigável",
            "simplify", "simplificar", "understand", "entender"
        ]
        
        # Medium usability impact keywords
        medium_usability_keywords = [
            "improve", "melhorar", "enhance", "aperfeiçoar", "better", "melhor",
            "readable", "legível", "format", "formato"
        ]
        
        # Count matches
        high_count = sum(1 for keyword in high_usability_keywords if keyword in text)
        medium_count = sum(1 for keyword in medium_usability_keywords if keyword in text)
        
        # Calculate score
        if category == "usabilidade":
            base_score = 6
        else:
            base_score = 0
        
        if high_count > 0:
            return min(10, base_score + high_count * 2)
        elif medium_count > 0:
            return min(8, base_score + medium_count)
        else:
            return max(0, base_score - 1)
