"""
LLM Contract Validator - Garante que respostas LLM seguem schema esperado.

Detecta model drift (mudanças de formato) antes de processar dados.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Literal

class ImpactScores(BaseModel):
    """Scores de impacto de uma sugestão."""
    seguranca: int = Field(..., ge=0, le=10, description="0-10: Impacto em segurança")
    economia: Literal["baixa", "b", "media", "m", "alta", "a", "N/A", "n/a", "L", "M", "A"] # Expanded to be robust
    eficiencia: str  # Mais flexível
    usabilidade: int = Field(..., ge=0, le=10)
    
    @field_validator('economia', mode='before')
    @classmethod
    def normalize_economy(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if v in ['b', 'l', 'low']: return 'baixa'
            if v in ['m', 'medium']: return 'media'
            if v in ['a', 'high']: return 'alta'
        return v

class SpecificLocation(BaseModel):
    """Localização específica da sugestão no protocolo."""
    node_id: Optional[str] = Field(None, pattern=r'^node-\d+$')
    question_id: Optional[str] = None
    section: Optional[str] = None


class ImplementationStrategy(BaseModel):
    """
    Estratégia específica de implementação - OBRIGATÓRIA para sugestões acionáveis.
    
    Wave 2 Addition: Every suggestion must explain HOW to implement it.
    """
    target_field: str = Field(
        ..., 
        min_length=3,
        description="Campo do protocolo a modificar (e.g., 'mensagem_alerta', 'descricao', 'condicao')"
    )
    modification_type: Literal["add", "update", "remove", "conditional"] = Field(
        ...,
        description="Tipo de modificação: add (novo), update (alterar), remove, conditional (lógica)"
    )
    instructions: str = Field(
        ..., 
        min_length=30,
        description="Instruções específicas de como implementar (min 30 chars)"
    )
    example_value: Optional[str] = Field(
        None,
        description="Exemplo do valor a adicionar/atualizar"
    )
    
    @field_validator('target_field')
    @classmethod
    def validate_target_field_not_generic(cls, v):
        """Garante que target_field é específico."""
        # Common valid fields in Daktus protocols
        valid_fields = {
            'mensagem_alerta', 'descricao', 'condicao', 'expressao',
            'titulo', 'options', 'label', 'value', 'tooltip',
            'visibilidade', 'obrigatorio', 'default_value'
        }
        
        v_lower = v.lower().strip()
        
        # Accept if it's a known field or follows a pattern
        if v_lower in valid_fields:
            return v
        
        # Accept if it's a path like "data.questions[0].mensagem_alerta"
        if '.' in v or '[' in v:
            return v
        
        # Accept any non-empty value for flexibility
        return v


class ImprovementSuggestion(BaseModel):
    """Schema de uma sugestão de melhoria."""
    id: str = Field(..., pattern=r'^sug_\d+')
    category: Literal["seguranca", "economia", "eficiencia", "usabilidade", "outro"]
    priority: Literal["baixa", "media", "alta", "critical"]
    title: str = Field(..., min_length=5, max_length=200) # Min length relaxed slightly
    description: str = Field(..., min_length=20) # Min length relaxed
    impact_scores: ImpactScores
    # specific_location can be dict or flattened in some prompts, keeping robust
    specific_location: Optional[SpecificLocation] = None 
    playbook_reference: str = Field(..., min_length=10, description="Snippet do playbook")
    rationale: Optional[str] = None # Often present
    
    # Wave 2: Implementation strategy (optional for backward compat, but encouraged)
    implementation_strategy: Optional[ImplementationStrategy] = Field(
        None,
        description="RECOMENDADO: Estratégia específica de como implementar esta sugestão"
    )
    
    @field_validator('playbook_reference')
    @classmethod
    def validate_playbook_reference_not_generic(cls, v):
        """Garante que referência não é genérica."""
        generic_phrases = [
            "não especificado no playbook",
            "not in playbook"
        ]
        
        v_lower = v.lower()
        for phrase in generic_phrases:
            if phrase in v_lower:
                raise ValueError(
                    f"Playbook reference is invalid/generic: '{phrase}'. "
                    "Must cite specific playbook content."
                )
        
        return v

class AnalysisMetadata(BaseModel):
    """Metadados da análise."""
    protocol_path: Optional[str] = None
    playbook_path: Optional[str] = None
    model_used: Optional[str] = None
    timestamp: Optional[str] = None
    version: Optional[str] = None
    suggestions_count: Optional[int] = None

class EnhancedAnalysisResponse(BaseModel):
    """
    Schema completo da resposta do Enhanced Analyzer.
    
    CRITICAL: Se LLM mudar formato, ValidationError será levantado.
    """
    improvement_suggestions: List[ImprovementSuggestion] = Field(..., min_length=1)
    metadata: Optional[AnalysisMetadata] = None
    
    @field_validator('improvement_suggestions')
    @classmethod
    def validate_suggestions_count_in_range(cls, v):
        """Valida que número de sugestões está no range esperado."""
        count = len(v)
        if count < 1: # Strict < 5 might block valid small optimizations
            raise ValueError(f"Too few suggestions: {count}")
        if count > 60:
            raise ValueError(f"Too many suggestions: {count}")
        return v
