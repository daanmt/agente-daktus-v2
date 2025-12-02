"""
Cost Estimator - Estimativa de Custos

Responsabilidades:
- Estimar consumo de tokens para cada operação
- Calcular custo em USD baseado no modelo selecionado
- Gerar estimativas pré-execução
- Rastrear custos reais pós-execução

Fase de Implementação: FASE 3 (3-4 dias)
Status: ✅ Implementado
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from ..core.logger import logger


@dataclass
class CostEstimate:
    """Estimativa de custo para uma operação."""
    operation: str
    model: str
    estimated_tokens: Dict[str, int]  # {input: X, output: Y}
    estimated_cost_usd: Dict[str, float]  # {input: X, output: Y, total: Z}
    confidence: str  # low, medium, high


@dataclass
class ActualCost:
    """Custo real de uma operação executada."""
    operation: str
    model: str
    actual_tokens: Dict[str, int]
    actual_cost_usd: Dict[str, float]
    variance_from_estimate: Dict[str, float]


class CostEstimator:
    """
    Estimativa e rastreamento de custos.

    Meta: 90%+ precisão nas estimativas.
    
    Tabela de preços (por milhão de tokens):
    - Input: preço por MTok de input
    - Output: preço por MTok de output
    """
    
    # Tabela de preços (USD por milhão de tokens) - Preços atualizados 2025-12-01
    MODEL_PRICING = {
        # Grok models (default: Grok 4.1 Fast Free)
        "x-ai/grok-4.1-fast:free": {"input": 0.0, "output": 0.0},  # Contexto: 2M tokens
        "x-ai/grok-code-fast-1": {"input": 0.20, "output": 1.50},  # Contexto: 256K tokens
        
        # Gemini models
        "google/gemini-2.5-flash-preview-09-2025": {"input": 0.30, "output": 2.50},  # Contexto: 1.05M tokens
        "google/gemini-2.5-flash": {"input": 0.30, "output": 2.50},  # Contexto: 1.05M tokens
        "google/gemini-2.5-pro": {"input": 1.25, "output": 10.0},  # Contexto: 1.05M tokens
        
        # Claude models
        "anthropic/claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},  # Contexto: 1M tokens
        "anthropic/claude-opus-4-20250514": {"input": 5.0, "output": 25.0},  # Contexto: 200K tokens
        
        # OpenAI models (mantido para compatibilidade)
        "openai/gpt-5-mini": {"input": 0.15, "output": 0.60},
    }
    
    # Fator de conversão: caracteres para tokens (aproximado)
    # 1 token ≈ 4 caracteres (conservador)
    CHARS_TO_TOKENS = 4
    
    def __init__(self):
        """Inicializa o estimador de custos."""
        logger.debug("CostEstimator initialized")
    
    def _get_model_pricing(self, model: str) -> Dict[str, float]:
        """
        Obtém preços do modelo.
        
        Args:
            model: ID do modelo
            
        Returns:
            Dict com preços input/output por MTok
            
        Raises:
            ValueError: Se modelo não encontrado na tabela
        """
        # Tentar match exato primeiro
        if model in self.MODEL_PRICING:
            return self.MODEL_PRICING[model]
        
        # Tentar match parcial (para variações de versão)
        for model_key, pricing in self.MODEL_PRICING.items():
            if model_key.split("/")[-1] in model or model in model_key:
                logger.warning(f"Using approximate pricing for {model} (matched {model_key})")
                return pricing
        
        # Default: usar preço médio (conservador)
        logger.warning(f"Model {model} not found in pricing table, using conservative default")
        return {"input": 2.0, "output": 10.0}  # Preço médio conservador
    
    def _estimate_tokens(self, text_size: int, is_output: bool = False) -> int:
        """
        Estima tokens baseado em tamanho de texto.
        
        Args:
            text_size: Tamanho em caracteres
            is_output: Se é output (tende a ser mais compacto)
            
        Returns:
            Número estimado de tokens
        """
        # Output tende a ser mais compacto (JSON estruturado)
        factor = 3.5 if is_output else self.CHARS_TO_TOKENS
        return int(text_size / factor)

    def estimate_analysis_cost(
        self,
        protocol_size: int,
        playbook_size: int,
        model: str
    ) -> CostEstimate:
        """
        Estima custo da análise V3 expandida (20-50 sugestões).

        Fórmulas:
        - input_tokens ≈ (protocol_size + playbook_size) / 4 (chars to tokens)
        - output_tokens ≈ calculado dinamicamente baseado no tamanho:
          * Protocolos pequenos (<10k chars): ~15k tokens (20-30 sugestões)
          * Protocolos médios (10k-50k chars): ~20k tokens (30-40 sugestões)
          * Protocolos grandes (>50k chars): ~25k tokens (40-50 sugestões)
        
        Args:
            protocol_size: Tamanho do protocolo em caracteres
            playbook_size: Tamanho do playbook em caracteres
            model: Modelo LLM a ser utilizado
            
        Returns:
            CostEstimate com estimativa de custo
        """
        pricing = self._get_model_pricing(model)
        
        # Estimar tokens de input
        total_input_chars = protocol_size + playbook_size
        estimated_input_tokens = self._estimate_tokens(total_input_chars, is_output=False)
        
        # Estimar tokens de output (20-50 sugestões em JSON)
        # Baseado no tamanho do protocolo e playbook:
        # - Protocolos pequenos (<10k chars): ~15k tokens output (20-30 sugestões)
        # - Protocolos médios (10k-50k chars): ~20k tokens output (30-40 sugestões)
        # - Protocolos grandes (>50k chars): ~25k tokens output (40-50 sugestões)
        # Cada sugestão: ~200-500 tokens em JSON detalhado
        if total_input_chars < 10000:
            estimated_output_tokens = 15000  # ~20-30 sugestões
        elif total_input_chars < 50000:
            estimated_output_tokens = 20000  # ~30-40 sugestões
        else:
            estimated_output_tokens = 25000  # ~40-50 sugestões
        
        # Calcular custos
        input_cost = (estimated_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Confidence baseado em tamanho (maior = mais confiável)
        if total_input_chars > 50000:
            confidence = "high"
        elif total_input_chars > 10000:
            confidence = "medium"
        else:
            confidence = "low"
        
        estimate = CostEstimate(
            operation="enhanced_analysis",
            model=model,
            estimated_tokens={
                "input": estimated_input_tokens,
                "output": estimated_output_tokens,
                "total": estimated_input_tokens + estimated_output_tokens
            },
            estimated_cost_usd={
                "input": round(input_cost, 4),
                "output": round(output_cost, 4),
                "total": round(total_cost, 4)
            },
            confidence=confidence
        )
        
        logger.info(
            f"Cost estimate for analysis: ${total_cost:.4f} "
            f"({estimated_input_tokens} input + {estimated_output_tokens} output tokens)"
        )
        
        return estimate

    def estimate_auto_apply_cost(
        self,
        protocol_size: int,
        suggestions: List[Dict],
        model: str
    ) -> CostEstimate:
        """
        Estima custo do auto-apply (aplicar sugestões ao protocolo).

        Fórmulas:
        - input_tokens ≈ protocol_size / 4 + (N * 500) (protocolo + sugestões como contexto)
        - output_tokens ≈ protocol_size / 4 (protocolo corrigido completo)
        
        Args:
            protocol_size: Tamanho do protocolo em caracteres
            suggestions: Lista de sugestões a aplicar
            model: Modelo LLM a ser utilizado
            
        Returns:
            CostEstimate com estimativa de custo
        """
        pricing = self._get_model_pricing(model)
        num_suggestions = len(suggestions)
        
        # Estimar tokens de input
        # Protocolo original + sugestões como contexto (~500 tokens cada)
        protocol_tokens = self._estimate_tokens(protocol_size, is_output=False)
        suggestions_context = num_suggestions * 500  # ~500 tokens por sugestão
        estimated_input_tokens = protocol_tokens + suggestions_context
        
        # Estimar tokens de output (protocolo corrigido completo)
        # Assume que o protocolo pode crescer 10-20% com melhorias
        estimated_output_tokens = int(protocol_tokens * 1.15)  # 15% de crescimento
        
        # Calcular custos
        input_cost = (estimated_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (estimated_output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Confidence baseado em número de sugestões
        if num_suggestions > 30:
            confidence = "high"  # Mais sugestões = padrão mais previsível
        elif num_suggestions > 10:
            confidence = "medium"
        else:
            confidence = "low"
        
        estimate = CostEstimate(
            operation="auto_apply",
            model=model,
            estimated_tokens={
                "input": estimated_input_tokens,
                "output": estimated_output_tokens,
                "total": estimated_input_tokens + estimated_output_tokens
            },
            estimated_cost_usd={
                "input": round(input_cost, 4),
                "output": round(output_cost, 4),
                "total": round(total_cost, 4)
            },
            confidence=confidence
        )
        
        logger.info(
            f"Cost estimate for auto-apply ({num_suggestions} suggestions): ${total_cost:.4f} "
            f"({estimated_input_tokens} input + {estimated_output_tokens} output tokens)"
        )
        
        return estimate

    def track_actual_cost(
        self,
        tokens_used: Dict[str, int],
        model: str,
        estimated_cost: CostEstimate
    ) -> ActualCost:
        """
        Registra custo real e compara com estimativa.

        Args:
            tokens_used: Tokens realmente usados {"input": X, "output": Y}
            model: Modelo utilizado
            estimated_cost: Estimativa original
            
        Returns:
            ActualCost com custo real e variância
        """
        pricing = self._get_model_pricing(model)
        
        input_tokens = tokens_used.get("input", 0)
        output_tokens = tokens_used.get("output", 0)
        total_tokens = input_tokens + output_tokens
        
        # Calcular custos reais
        actual_input_cost = (input_tokens / 1_000_000) * pricing["input"]
        actual_output_cost = (output_tokens / 1_000_000) * pricing["output"]
        actual_total_cost = actual_input_cost + actual_output_cost
        
        # Calcular variância
        estimated_total = estimated_cost.estimated_cost_usd["total"]
        variance_total = actual_total_cost - estimated_total
        variance_percent = (variance_total / estimated_total * 100) if estimated_total > 0 else 0
        
        actual_cost = ActualCost(
            operation=estimated_cost.operation,
            model=model,
            actual_tokens={
                "input": input_tokens,
                "output": output_tokens,
                "total": total_tokens
            },
            actual_cost_usd={
                "input": round(actual_input_cost, 4),
                "output": round(actual_output_cost, 4),
                "total": round(actual_total_cost, 4)
            },
            variance_from_estimate={
                "total_usd": round(variance_total, 4),
                "total_percent": round(variance_percent, 2)
            }
        )
        
        logger.info(
            f"Actual cost: ${actual_total_cost:.4f} "
            f"(estimate: ${estimated_total:.4f}, variance: {variance_percent:+.1f}%)"
        )
        
        return actual_cost
