"""
Enhanced Analyzer - Análise V2 Expandida

Responsabilidades:
- Gerar 20-50 sugestões de melhoria (vs 5-15 da V2)
- Categorização detalhada (Segurança, Economia, Eficiência, Usabilidade)
- Rastreabilidade completa (sugestão → evidência do playbook)
- Estimativa de esforço e custo por sugestão

Fase de Implementação: FASE 1 (4-6 dias)
Status: ✅ Implementado
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict

# Import core components
from ..core.llm_client import LLMClient
from ..core.logger import logger

# Import V3 components
from .impact_scorer import ImpactScorer, ImpactScores
from ..cost_control import CostEstimator, CostEstimate

# Import prompt template
from config.prompts.enhanced_analysis_prompt import (
    ENHANCED_ANALYSIS_PROMPT_TEMPLATE,
    ENHANCED_OUTPUT_SCHEMA_JSON
)

# Import memory QA (simple markdown-based memory)
from ..feedback.memory_qa import MemoryQA
from ..feedback.memory_engine import MemoryEngine

# Import alert rules and suggestion validator (Wave 4.1 - Intelligence improvements)
from .alert_rules import (
    get_alert_rules_for_prompt,
    get_alert_examples_for_prompt,
    ALERT_IMPLEMENTATION_RULES
)
from ..validators.suggestion_validator import (
    SuggestionValidator,
    filter_suggestions_before_presentation
)


@dataclass
class Suggestion:
    """
    Representa uma sugestão de melhoria expandida.

    Attributes:
        id: Identificador único da sugestão
        category: Categoria (seguranca, economia, eficiencia, usabilidade)
        priority: Prioridade (alta, media, baixa)
        title: Título da sugestão
        description: Descrição detalhada
        rationale: Justificativa clínica
        impact_scores: Scores por categoria
        evidence: Link para evidência no playbook
        implementation_effort: Estimativa de esforço
        auto_apply_cost_estimate: Custo estimado para aplicar
        specific_location: Localização específica no protocolo
    """
    id: str
    category: str
    priority: str
    title: str
    description: str
    rationale: str
    impact_scores: Dict[str, Union[int, str]]  # seguranca: int, economia/eficiencia: str, usabilidade: int
    evidence: Dict[str, str]
    implementation_effort: Dict[str, str]
    auto_apply_cost_estimate: Dict[str, float]
    specific_location: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict:
        """Convert suggestion to dictionary."""
        return asdict(self)


@dataclass
class ExpandedAnalysisResult:
    """
    Resultado da análise expandida.

    Attributes:
        structural_analysis: Análise estrutural do protocolo
        clinical_extraction: Extração clínica
        improvement_suggestions: 20-50 sugestões priorizadas
        impact_scores: Scores agregados
        evidence_mapping: Mapeamento sugestão → evidência
        cost_estimation: Estimativa de custo total
    """
    structural_analysis: Dict
    clinical_extraction: Dict
    improvement_suggestions: List[Suggestion]
    impact_scores: Dict[str, float]
    evidence_mapping: Dict[str, str]
    cost_estimation: Dict[str, float]


class EnhancedAnalyzer:
    """
    Análise expandida de protocolos clínicos.

    Este analisador estende a funcionalidade da V2 para gerar relatórios
    mais sofisticados e acionáveis, com 20-50 sugestões detalhadas.

    Melhorias sobre V2:
    - Mais sugestões (20-50 vs 5-15)
    - Categorização detalhada
    - Scores de impacto por categoria
    - Rastreabilidade completa
    - Estimativa de esforço

    Example:
        >>> analyzer = EnhancedAnalyzer(model="google/gemini-2.5-flash-preview-09-2025")
        >>> result = analyzer.analyze_comprehensive(
        ...     protocol_json=protocol,
        ...     playbook_content=playbook
        ... )
        >>> print(f"Sugestões geradas: {len(result.improvement_suggestions)}")
    """

    def __init__(
        self,
        model: str = "google/gemini-2.5-flash-lite"
    ):
        """
        Inicializa o analisador expandido.

        Args:
            model: Modelo LLM a ser utilizado (default: Gemini 2.5 Flash Lite - barato e estável)
        """
        self.model = model
        self.llm_client = LLMClient(model=model)
        self.impact_scorer = ImpactScorer()
        self.cost_estimator = CostEstimator()
        self.memory_qa = MemoryQA()  # Sistema simples de memória via markdown
        logger.info(f"EnhancedAnalyzer initialized with model: {model}")

    def analyze_comprehensive(
        self,
        protocol_json: Dict,
        playbook_content: str,
        model: Optional[str] = None,
        protocol_path: Optional[str] = None
    ) -> ExpandedAnalysisResult:
        """
        Análise abrangente com sugestões expandidas.

        Este método realiza uma análise completa do protocolo contra o playbook,
        gerando 20-50 sugestões de melhoria com rastreabilidade completa.

        Args:
            protocol_json: Protocolo clínico (dict)
            playbook_content: Conteúdo do playbook (string)
            model: Modelo LLM (override do padrão)
            protocol_path: Caminho do protocolo (para logging)

        Returns:
            ExpandedAnalysisResult contendo:
            - structural_analysis: Análise estrutural
            - clinical_extraction: Extração clínica
            - improvement_suggestions: 20-50 sugestões priorizadas
            - impact_scores: Scores por categoria
            - evidence_mapping: Sugestão → Evidência playbook
            - cost_estimation: Custo estimado para aplicar cada sugestão

        Raises:
            ValueError: Se protocolo ou playbook inválido
            Exception: Se chamada ao LLM falhar
        """
        logger.info("=" * 60)
        logger.info("Enhanced Analyzer - Starting Comprehensive Analysis")
        logger.info("=" * 60)
        
        # Override model if provided
        if model:
            self.model = model
            self.llm_client = LLMClient(model=model)
        
        # Step 1: Estimate cost (informative only, no authorization required)
        logger.info("Step 1: Estimating cost...")
        protocol_size = len(json.dumps(protocol_json, ensure_ascii=False))
        playbook_size = len(playbook_content)
        
        cost_estimate = self.cost_estimator.estimate_analysis_cost(
            protocol_size=protocol_size,
            playbook_size=playbook_size,
            model=self.model
        )
        
        # Exibir estimativa informativa (sem solicitar autorização)
        self._display_cost_estimate(cost_estimate, "Enhanced Analysis (20-50 suggestions)")
        
        logger.info("Step 1: Cost estimated, proceeding with analysis...")
        
        # Step 2: Build enhanced prompt
        logger.info("Step 2: Building enhanced analysis prompt...")
        # Base analysis vazio (V2 integration opcional para MVP)
        base_analysis = {}
        prompt_structure = self._build_enhanced_prompt(
            protocol_json=protocol_json,
            playbook_content=playbook_content,
            base_analysis=base_analysis
        )
        
        # Step 3: Call LLM for enhanced analysis
        logger.info("Step 3: Calling LLM for enhanced analysis (5-50 suggestions, prioritizing medium/high/critical)...")
        try:
            llm_result = self.llm_client.analyze(prompt_structure)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise
        
        # Step 4: Extract and process suggestions
        logger.info("Step 4: Extracting and processing suggestions...")
        suggestions = self._extract_suggestions(llm_result)

        # Step 4.5: Apply post-generation filters (NEW - Phase 2.2)
        if hasattr(self, '_active_filters') and self._active_filters:
            logger.info("Step 4.5: Applying post-generation filters...")
            pre_filter_count = len(suggestions)
            suggestions = self._apply_post_filters(suggestions, self._active_filters)
            post_filter_count = len(suggestions)

            if pre_filter_count != post_filter_count:
                logger.info(
                    f"Post-filtering: {pre_filter_count} → {post_filter_count} suggestions "
                    f"({pre_filter_count - post_filter_count} removed)"
                )

        # Step 4.6: Validate playbook references (CRITICAL - prevent hallucinations)
        logger.info("Step 4.6: Validating playbook references...")
        pre_validation_count = len(suggestions)
        suggestions = self._validate_playbook_references(suggestions, playbook_content)
        post_validation_count = len(suggestions)

        if pre_validation_count != post_validation_count:
            logger.warning(
                f"Playbook validation: {pre_validation_count} → {post_validation_count} suggestions "
                f"({pre_validation_count - post_validation_count} removed - NO VALID PLAYBOOK REFERENCE)"
            )

        # Step 4.6b: Strict reference verification (Wave 2 - fuzzy matching)
        logger.info("Step 4.6b: Strict reference verification (Wave 2)...")
        try:
            from ..validators.reference_validator import validate_suggestions_references
            
            # Convert Suggestion objects to dicts for validator
            suggestion_dicts = [
                {
                    'id': s.id,
                    'title': s.title,
                    'playbook_reference': s.evidence.get('playbook_reference', '')
                }
                for s in suggestions
            ]
            
            valid_dicts, invalid_dicts = validate_suggestions_references(
                suggestion_dicts,
                playbook_content
            )
            
            # Keep only suggestions that passed
            valid_ids = {d['id'] for d in valid_dicts}
            pre_strict_count = len(suggestions)
            suggestions = [s for s in suggestions if s.id in valid_ids]
            post_strict_count = len(suggestions)
            
            if pre_strict_count != post_strict_count:
                logger.warning(
                    f"🔍 Strict reference check: {pre_strict_count} → {post_strict_count} "
                    f"({pre_strict_count - post_strict_count} failed verification)"
                )
        except ImportError as e:
            logger.warning(f"Reference validator not available: {e}")
        except Exception as e:
            logger.warning(f"Reference validation error (continuing): {e}")


        # Step 4.7: Apply memory-based filtering (Memory Engine V2)
        logger.info("Step 4.7: Applying memory-based filtering...")
        memory_engine = MemoryEngine()
        memory_engine.load_memory()
        pre_memory_count = len(suggestions)
        suggestions, memory_debug = memory_engine.filter_suggestions(suggestions)
        post_memory_count = len(suggestions)

        if pre_memory_count != post_memory_count:
            logger.info(
                f"Memory filtering: {pre_memory_count} → {post_memory_count} suggestions "
                f"({pre_memory_count - post_memory_count} filtered by memory rules)"
            )

        # Step 4.8: Apply hard rules engine (CRITICAL - Wave 2)
        logger.info("Step 4.8: Applying hard rules engine...")
        try:
            from ..learning.rules_engine import RulesEngine
            
            rules_engine = RulesEngine()
            pre_rules_count = len(suggestions)
            
            # Convert Suggestion objects to dicts for rules engine
            suggestion_dicts = [
                {
                    'id': s.id,
                    'title': s.title,
                    'description': s.description,
                    'category': s.category,
                    'playbook_reference': s.evidence.get('playbook_reference', ''),
                    'priority': s.priority,
                    'impact_scores': s.impact_scores
                }
                for s in suggestions
            ]
            
            valid_dicts = rules_engine.validate_batch(suggestion_dicts)
            valid_ids = {d['id'] for d in valid_dicts}
            
            # Keep only suggestions that passed rules
            suggestions = [s for s in suggestions if s.id in valid_ids]
            post_rules_count = len(suggestions)
            
            if pre_rules_count != post_rules_count:
                logger.info(
                    f"🛡️ Rules engine: {pre_rules_count} → {post_rules_count} suggestions "
                    f"({pre_rules_count - post_rules_count} blocked by hard rules)"
                )
        except ImportError as e:
            logger.warning(f"Rules engine not available: {e}")
        except Exception as e:
            logger.warning(f"Rules engine error (continuing): {e}")

        # Step 5: Validate suggestions with SuggestionValidator (Wave 4.1)
        logger.info("Step 5: Validating suggestions for antipatterns and duplicates...")
        try:
            validator = SuggestionValidator(strict_mode=False)
            suggestions_dicts = [s.to_dict() for s in suggestions]
            valid_dicts, rejected_dicts = validator.validate_and_filter(suggestions_dicts)
            
            # Log validation stats
            stats = validator.get_stats()
            if stats['failed_antipattern'] > 0 or stats['duplicates_removed'] > 0:
                logger.info(
                    f"🛡️ Suggestion validation: {stats['passed']} passed, "
                    f"{stats['failed_antipattern']} antipatterns blocked, "
                    f"{stats['duplicates_removed']} duplicates removed"
                )
            
            # Rebuild Suggestion objects from validated dicts
            suggestions = [
                Suggestion(
                    id=d.get('id', ''),
                    category=d.get('category', 'usabilidade'),
                    priority=d.get('priority', 'baixa'),
                    title=d.get('title', ''),
                    description=d.get('description', ''),
                    rationale=d.get('rationale', ''),
                    evidence=d.get('evidence', {}),
                    implementation_effort=d.get('implementation_effort', {}),
                    auto_apply_cost_estimate=d.get('auto_apply_cost_estimate', {}),
                    specific_location=d.get('specific_location')
                )
                for d in valid_dicts
            ]
        except Exception as e:
            logger.warning(f"Suggestion validation error (continuing): {e}")
        
        # Step 6: Categorize and prioritize
        logger.info("Step 6: Categorizing and prioritizing suggestions...")
        categorized = self._categorize_suggestions(suggestions)
        prioritized = self._prioritize_suggestions(categorized)
        
        # Step 7: Build result
        logger.info("Step 7: Building expanded analysis result...")
        
        # Calculate aggregate impact scores
        impact_scores = self._calculate_aggregate_scores(prioritized)
        
        # Build evidence mapping
        evidence_mapping = {
            sug.id: sug.evidence.get("playbook_reference", "")
            for sug in prioritized
        }
        
        # Include memory filter debug info in evidence mapping (for transparency)
        # Store memory debug info as a special entry
        if memory_debug.get("filtered_count", 0) > 0:
            evidence_mapping["_memory_filters"] = {
                "filtered_count": memory_debug.get("filtered_count", 0),
                "exact_matches": len(memory_debug.get("exact_matches", [])),
                "semantic_matches": len(memory_debug.get("semantic_matches", [])),
                "reinforced_by_memory": len(memory_debug.get("reinforced_by_memory", []))
            }
        
        # Estimate total cost
        cost_estimation = {
            "analysis_cost_usd": 0.0,  # Will be calculated by CostEstimator
            "suggestions_count": len(prioritized),
            "auto_apply_estimated_cost_usd": sum(
                sug.auto_apply_cost_estimate.get("estimated_cost_usd", 0.0)
                for sug in prioritized
            )
        }
        
        result = ExpandedAnalysisResult(
            structural_analysis=llm_result.get("structural_analysis", {}),
            clinical_extraction=llm_result.get("clinical_extraction", {}),
            improvement_suggestions=prioritized,
            impact_scores=impact_scores,
            evidence_mapping=evidence_mapping,
            cost_estimation=cost_estimation
        )
        
        logger.info("=" * 60)
        logger.info(f"Enhanced Analyzer - Analysis Complete: {len(prioritized)} suggestions generated")
        logger.info("=" * 60)
        
        return result
    
    def _display_cost_estimate(
        self,
        cost_estimate: CostEstimate,
        operation_description: str = "Operação LLM"
    ) -> None:
        """
        Exibe estimativa de custo de forma informativa (sem solicitar autorização).
        
        Args:
            cost_estimate: Estimativa de custo
            operation_description: Descrição da operação
        """
        total_cost = cost_estimate.estimated_cost_usd["total"]
        input_tokens = cost_estimate.estimated_tokens["input"]
        output_tokens = cost_estimate.estimated_tokens["output"]
        total_tokens = input_tokens + output_tokens
        
        # Estilo moderno e compacto
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich import box
            
            console = Console()
            
            # CRITICAL FIX: Print blank line BEFORE panel to properly separate from any active spinner
            # This ensures the spinner line is cleared before the panel is rendered
            console.print("")  # Clear spinner line
            
            content = f"""[bold cyan]{cost_estimate.model}[/bold cyan]

[dim]Tokens:[/dim] {total_tokens:,} ({input_tokens:,} in + {output_tokens:,} out)
[bold]Custo:[/bold] ${total_cost:.4f} USD [dim]({cost_estimate.confidence.upper()})[/dim]"""
            
            panel = Panel(
                content,
                box=box.ROUNDED,
                title="💰 Estimativa de Custo",
                title_align="left",
                border_style="cyan",
                padding=(1, 2)
            )
            console.print(panel)
            console.print()  # Quebra de linha explícita após o painel
        except ImportError:
            # Fallback simples
            print(f"\n💰 Estimativa de Custo: {cost_estimate.model}")
            print(f"Tokens: {total_tokens:,} | Custo: ${total_cost:.4f} USD ({cost_estimate.confidence.upper()})")

    def _build_enhanced_prompt(
        self,
        protocol_json: Dict,
        playbook_content: str,
        base_analysis: Dict
    ) -> Union[str, Dict]:
        """
        Constrói prompt expandido para análise com suporte a caching.

        Args:
            protocol_json: Protocolo clínico
            playbook_content: Playbook médico
            base_analysis: Análise base da V2 (opcional)

        Returns:
            Prompt structure (string ou dict com caching)
        """
        # Format protocol as JSON
        try:
            protocol_formatted = json.dumps(
                protocol_json,
                indent=2,
                ensure_ascii=False,
                sort_keys=False
            )
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to format protocol JSON: {e}")
            protocol_formatted = str(protocol_json)
        
        # Format base analysis as JSON
        base_analysis_formatted = json.dumps(base_analysis, indent=2, ensure_ascii=False) if base_analysis else "{}"
        
        # Carregar memória QA (memory_qa.md) - ANTES da análise
        memory_qa_content = self.memory_qa.get_memory_content(max_length=3000)

        # Carregar filtros ativos baseados em padrões de feedback (NEW - Phase 2.2)
        # CRITICAL FIX: Lower threshold from 3 to 1 so patterns activate immediately
        active_filters = self.memory_qa.get_active_filters(min_frequency=1)
        
        # Carregar regras do Memory Engine para contexto adicional
        memory_engine = MemoryEngine()
        memory_engine.load_memory()
        memory_rules_context = self._build_memory_rules_context(memory_engine)
        
        filter_instructions = self._build_filter_instructions(active_filters, memory_rules_context)

        # Armazenar filtros para pós-processamento
        self._active_filters = active_filters

        # Build prompt with template
        # CRITICAL FIX: Always include filter_instructions (was missing in non-cached path)
        prompt_text = ENHANCED_ANALYSIS_PROMPT_TEMPLATE.format(
            agent_memory=memory_qa_content,
            playbook_content=playbook_content,
            protocol_json=protocol_formatted,
            base_analysis=base_analysis_formatted,
            filter_instructions=filter_instructions,
            output_schema=ENHANCED_OUTPUT_SCHEMA_JSON
        )
        
        # Use caching if playbook is substantial (>1000 chars)
        use_cache = len(playbook_content) > 1000
        
        if use_cache:
            # Structure for prompt caching: playbook in system, protocol in messages
            # Carregar memória QA (memory_qa.md)
            memory_qa_content = self.memory_qa.get_memory_content(max_length=3000)
            
            base_instructions = f"""You are an expert medical protocol quality analyst conducting DEEP, COMPREHENSIVE analysis.

CONTEXT: You will analyze a medical protocol (JSON decision tree) against its corresponding clinical playbook to identify improvements, gaps, and optimization opportunities.

🚨 CRITICAL CONSTRAINT - PLAYBOOK IS THE SINGLE SOURCE OF TRUTH:

THE PLAYBOOK IS THE ONLY VALID SOURCE FOR ALL SUGGESTIONS. You MUST:

1. ✅ ONLY suggest exams, treatments, medications, procedures that are EXPLICITLY mentioned in the playbook
2. ✅ ONLY reference clinical guidelines, protocols, or recommendations that appear in the playbook
3. ✅ EVERY suggestion MUST have a direct, explicit reference to specific playbook content
4. ❌ NEVER add content from external sources, medical literature, or general medical knowledge
5. ❌ NEVER suggest "introducing" or "adding" treatments/exams not in the playbook
6. ❌ NEVER assume standard medical practices - only what the playbook explicitly states

WHY THIS MATTERS:
- The playbook is customized for THIS specific health operator's reality
- It reflects their available resources, contracts, and operational constraints
- Adding external content violates the operator's operational model

VALIDATION: Before including ANY suggestion, ask yourself:
- "Is this exam/treatment/medication explicitly mentioned in the playbook?" → If NO, REJECT
- "Can I quote the exact playbook text supporting this?" → If NO, REJECT
- "Am I assuming this should exist based on medical knowledge?" → If YES, REJECT

IMPORTANT: Review the feedback history below (memory_qa.md) to understand:
- Which types of suggestions were rejected and why (learn from IRRELEVANT patterns)
- Which types of suggestions were accepted and why (learn from RELEVANT patterns)
- What patterns indicate recurring problems vs valuable suggestions

FEEDBACK HISTORY (memory_qa.md):
{memory_qa_content}

INPUT MATERIALS:

1. CLINICAL PLAYBOOK (Medical Guidelines):

"""
            
            protocol_instructions_template = """
2. PROTOCOL JSON (Decision Tree):

{protocol_json}

3. BASE ANALYSIS (from V2):

{base_analysis}

---

ACTIVE FILTERS (Based on User Feedback Patterns):

{filter_instructions}

---

YOUR EXPANDED ANALYSIS MUST GENERATE 5-50 DETAILED IMPROVEMENT SUGGESTIONS:

CRITICAL PRIORITY FOCUS: 
- PRIORIZE generating suggestions in this order:
  1. SEGURANÇA (safety score >= 7) - HIGHEST PRIORITY
  2. EFICIÊNCIA (medium/high impact) - HIGH PRIORITY
  3. ECONOMIA (medium/high impact) - MEDIUM PRIORITY
  4. USABILIDADE (only if significantly enhances workflow) - LOWER PRIORITY
- LOW priority suggestions should ONLY be included if they are truly valuable, non-redundant, and add significant value
- Focus computational resources on suggestions that have significant impact:
  * Safety score >= 7 (high/critical safety issues) - PRIORITIZE THESE
  * Medium/High efficiency impact - PRIORITIZE THESE
  * Medium/High economy impact
  * Medium/High usability improvements that significantly enhance workflow
- DO NOT force low-impact suggestions just to reach a target count
- Quality over quantity: Better to generate 5-10 high-quality, high-priority suggestions than 20-30 mixed-quality suggestions with many low-impact ones
- If there are fewer than 5 high/medium priority suggestions available, generate only what is truly valuable (minimum 5, but quality is paramount)

CRITICAL REQUIREMENTS:

1. QUANTITY: Generate 5-50 suggestions, prioritizing in this order:
   - Safety enhancements (PRIORITY 1: safety score >= 7) - 3-10 suggestions
   - Efficiency optimizations (PRIORITY 2: medium/high impact) - 3-10 suggestions
   - Economy optimizations (PRIORITY 3: medium/high impact) - 2-8 suggestions
   - Usability improvements (PRIORITY 4: only if significantly enhances workflow) - 1-5 suggestions
   
   IMPORTANT: Focus on SEGURANÇA and EFICIÊNCIA first. If you cannot find enough high/medium priority suggestions, generate fewer but higher quality suggestions. Do NOT pad with low-priority suggestions.

2. CATEGORIZATION: Each suggestion MUST be categorized as ONE of:
   - "seguranca" (patient safety, red flags, contraindications)
   - "economia" (cost reduction, resource optimization)
   - "eficiencia" (workflow speed, reduced steps, automation)
   - "usabilidade" (user experience, clarity, simplicity)

3. IMPACT SCORING: For EACH suggestion, provide impact scores:
   - seguranca: 0-10 (0=no safety impact, 10=critical safety issue)
   - economia: "L" (low), "M" (medium), "A" (high economic impact)
   - eficiencia: "L" (low), "M" (medium), "A" (high efficiency gain)
   - usabilidade: 0-10 (0=no UX impact, 10=major UX improvement)

4. PRIORITIZATION: Assign priority based on impact scores:
   - "alta": Segurança ≥8 OR (Economia="A" AND Segurança≥5)
   - "media": Segurança 5-7 OR Economia="M"/"A" OR Eficiência="A"
   - "baixa": All other cases

5. EVIDENCE TRACEABILITY (🚨 MANDATORY - NO EXCEPTIONS):
   For EACH suggestion, you MUST provide:
   - playbook_reference: EXACT QUOTE from the playbook (copy-paste actual text)
     → This is MANDATORY. If you cannot provide an exact quote, DO NOT include the suggestion
     → The quote must be verifiable in the playbook content provided above
     → Generic references like "based on medical best practices" are INVALID
   - context: Why the protocol is missing/misimplementing this playbook recommendation
   - clinical_rationale: Justification using ONLY information from the playbook

   🚨 CRITICAL: If a suggestion does NOT have an explicit playbook quote, it is INVALID and must be REMOVED
   - clinical_rationale: Medical/clinical justification

6. IMPLEMENTATION DETAILS: For EACH suggestion, estimate:
   - effort: "baixo" (low), "medio" (medium), "alto" (high implementation effort)
   - estimated_time: Estimated time to implement (e.g., "30min", "2h", "1dia")
   - complexity: "simples" (simple), "moderada" (moderate), "complexa" (complex)

7. SPECIFICITY: Each suggestion must be:
   - Actionable: Clear what needs to be changed
   - Specific: Exact location in protocol (node_id, field, etc.)
   - Measurable: How to verify the improvement
   - Evidence-based: Linked to playbook content

8. ALERT IMPLEMENTATION RULES (🚨 CRITICAL - NO GENERIC ALERTS):

   When suggesting alerts or warnings, you MUST specify one of these types:
   
   A. MENSAGEM AO MÉDICO (condutaDataNode.mensagem)
      - Use for critical information the doctor needs to SEE
      - Include complete JSON with id, nome, condicional, condicao, conteudo
   
   B. ORIENTAÇÃO AO PACIENTE (condutaDataNode.orientacao)
      - Use for educational information for the patient
      - Include complete HTML content in conteudo field
   
   C. ALERTA EM MEDICAMENTO (medicamentos[id].mensagem)
      - Use for prescription/contraindication warnings
      - Specify exact medication and condition
   
   ❌ NEVER USE GENERIC TERMS WITHOUT SPECIFICATION:
   - "adicionar alerta visual"
   - "criar bloqueio de conduta"
   - "implementar aviso crítico"
   - "alerta de alta prioridade"
   
   ✅ ALWAYS INCLUDE FOR ALERT SUGGESTIONS:
   - specific_location: {{ node_id, field, path }}
   - implementation_path: {{ json_path, modification_type, proposed_value }}
   - proposed_value MUST include complete HTML content for alerts

ANALYSIS DEPTH:

- Review EVERY node in the protocol
- Compare EVERY playbook recommendation against protocol implementation
- Identify ALL missing safety checks
- Find ALL efficiency bottlenecks
- Spot ALL usability issues
- Consider ALL edge cases

OUTPUT FORMAT:

Respond with ONLY valid JSON matching this exact schema:

{output_schema}

CRITICAL OUTPUT REQUIREMENTS:

- NO markdown formatting
- NO explanatory text outside JSON
- NO code blocks or markdown fences
- ONLY the JSON response
- Ensure JSON is valid and parseable
- Generate 5-50 suggestions (minimum 5, target 15-30 high/medium priority, maximum 50)
- Prioritize MEDIUM/HIGH/CRITICAL priority suggestions
- Only include LOW priority if truly valuable and non-redundant
- Every suggestion MUST have ALL required fields
"""
            
            protocol_instructions = protocol_instructions_template.format(
                protocol_json=protocol_formatted,
                base_analysis=base_analysis_formatted,
                filter_instructions=filter_instructions if filter_instructions else "No active filters",
                output_schema=ENHANCED_OUTPUT_SCHEMA_JSON
            )
            
            prompt_structure = {
                "system": [
                    {
                        "type": "text",
                        "text": base_instructions
                    },
                    {
                        "type": "text",
                        "text": playbook_content,
                        "cache_control": {"type": "ephemeral"}  # 5-minute cache
                    }
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": protocol_instructions
                    }
                ]
            }
            
            logger.info(
                f"Built cached enhanced prompt: playbook_size={len(playbook_content)} chars "
                f"(cacheable), protocol_size={len(protocol_formatted)} chars"
            )
            
            return prompt_structure
        else:
            # No caching - return full prompt string
            logger.info(f"Built enhanced prompt (no caching): size={len(prompt_text)} chars")
            return {"prompt": prompt_text}

    def _build_memory_rules_context(self, memory_engine: MemoryEngine) -> str:
        """
        Constrói contexto das regras do Memory Engine para o prompt.
        
        Args:
            memory_engine: Instância do Memory Engine carregada
            
        Returns:
            String com contexto formatado das regras rejeitadas
        """
        if not memory_engine.rules_rejected:
            return ""
        
        context = []
        context.append("\n" + "=" * 60)
        context.append("🧠 MEMORY ENGINE V2 - REJECTED PATTERNS")
        context.append("=" * 60)
        context.append("")
        context.append(f"Total de {len(memory_engine.rules_rejected)} regras rejeitadas aprendidas do histórico.")
        context.append("")
        context.append("PADRÕES CRÍTICOS DE REJEIÇÃO (evitar sugestões similares):")
        context.append("")
        
        # Agrupar por keywords para identificar padrões
        keyword_groups = {}
        for rule in memory_engine.rules_rejected[:20]:  # Limitar a 20 para não sobrecarregar
            keywords = rule.get('keywords', [])
            if not keywords:
                keywords = ['geral']
            
            for keyword in keywords[:2]:  # Pegar até 2 keywords principais
                if keyword not in keyword_groups:
                    keyword_groups[keyword] = []
                keyword_groups[keyword].append(rule)
        
        # Adicionar exemplos por padrão
        for keyword, rules in list(keyword_groups.items())[:10]:  # Top 10 padrões
            context.append(f"• {keyword.upper().replace('_', ' ')}:")
            # Pegar exemplo mais representativo
            example_rule = rules[0]
            example_text = example_rule.get('text', example_rule.get('comment', ''))[:150]
            context.append(f"  Exemplo rejeitado: \"{example_text}...\"")
            context.append("")
        
        context.append("=" * 60)
        context.append("")
        
        return "\n".join(context)
    
    def _build_filter_instructions(self, active_filters: Dict, memory_rules_context: str = "") -> str:
        """
        Constrói instruções LLM a partir dos filtros ativos.

        CRITICAL: Traduz padrões de feedback em instruções CLARAS e ACIONÁVEIS para o LLM.

        Args:
            active_filters: Filtros ativos do memory_qa

        Returns:
            String com instruções formatadas
        """
        instructions = []
        instructions.append("=" * 60)
        instructions.append("⚠️  CRITICAL LEARNING FILTERS (FROM USER FEEDBACK)")
        instructions.append("=" * 60)
        instructions.append("")
        instructions.append("The following rules were derived from EXPLICIT user rejection patterns.")
        instructions.append("VIOLATING these rules will result in suggestion rejection.")
        instructions.append("")
        
        # Adicionar contexto do Memory Engine
        if memory_rules_context:
            instructions.append(memory_rules_context)
            instructions.append("")

        rule_number = 1

        # Filtro de prioridade
        if active_filters.get("priority_threshold", "baixa") != "baixa":
            threshold_map = {"media": "MÉDIA", "alta": "ALTA"}
            threshold_upper = threshold_map.get(active_filters["priority_threshold"], "MÉDIA")
            instructions.append(
                f"{rule_number}. 🎯 PRIORITY FILTER: Generate ONLY {threshold_upper} and ALTA priority suggestions. "
                f"DO NOT generate BAIXA priority suggestions."
            )
            rule_number += 1

        # Filtros de categoria
        blocked_categories = [
            cat for cat, enabled in active_filters.get("category_filters", {}).items()
            if not enabled
        ]
        if blocked_categories:
            cats_str = ", ".join(blocked_categories)
            instructions.append(
                f"{rule_number}. 🚫 CATEGORY FILTER: AVOID suggestions in: {cats_str}"
            )
            rule_number += 1

        # Regras baseadas em padrões (EXPANDIDO)
        pattern_rules = active_filters.get("pattern_rules", [])
        if pattern_rules:
            instructions.append("")
            instructions.append(f"{rule_number}. 📋 LEARNED REJECTION PATTERNS:")
            instructions.append("")
            
            for rule in pattern_rules:
                rule_type = rule.get("rule", "unknown")
                action = rule.get("action", "")
                reason = rule.get("reason", "")
                blocked_phrases = rule.get("blocked_phrases", [])
                
                # Gerar instrução específica por tipo de regra
                if rule_type == "medical_autonomy":
                    instructions.append(
                        "   ❌ AUTONOMIA MÉDICA: NÃO sugerir restrições à decisão clínica do médico."
                    )
                    instructions.append(
                        "      • NÃO usar: 'priorizar X sobre Y', 'condicionar prescrição', 'substituir por'"
                    )
                    instructions.append(
                        "      • O médico deve ter LIBERDADE de escolha entre opções válidas"
                    )
                    instructions.append("")
                    
                elif rule_type == "playbook_strict":
                    instructions.append(
                        "   ❌ PLAYBOOK COMO LIMITE: NÃO sugerir exames/medicamentos/procedimentos fora do playbook."
                    )
                    instructions.append(
                        "      • Se não está explicitamente no playbook, NÃO sugerir"
                    )
                    instructions.append(
                        "      • NÃO usar: 'adicionar exame X', 'incluir medicamento Y'"
                    )
                    instructions.append("")
                    
                elif rule_type == "existing_logic":
                    instructions.append(
                        "   ❌ LÓGICA FUNCIONAL: NÃO sugerir mudanças em lógica que já funciona corretamente."
                    )
                    instructions.append(
                        "      • Condicionais existentes geralmente estão corretas"
                    )
                    instructions.append(
                        "      • 'exclusive' e 'preselected' já funcionam - não otimizar"
                    )
                    instructions.append("")
                    
                elif rule_type == "complexity_filter":
                    instructions.append(
                        "   ❌ COMPLEXIDADE: NÃO adicionar etapas/perguntas que aumentam tempo sem retorno."
                    )
                    instructions.append(
                        "      • Preferir SIMPLICIDADE sobre completude"
                    )
                    instructions.append(
                        "      • Cada pergunta adicional = mais tempo de atendimento"
                    )
                    instructions.append("")
                    
                elif rule_type == "tech_restriction":
                    instructions.append(
                        "   ❌ RESTRIÇÃO TÉCNICA: NÃO sugerir funcionalidades não disponíveis no sistema."
                    )
                    instructions.append(
                        "      • Tooltips, funções customizadas = NÃO DISPONÍVEIS"
                    )
                    instructions.append("")
                    
                elif rule_type == "context_scope":
                    instructions.append(
                        "   ❌ CONTEXTO AMBULATORIAL: Foco nos 99% de casos comuns, não em corner cases."
                    )
                    instructions.append(
                        "      • NÃO sugerir investigação de emergências/neoplasias"
                    )
                    instructions.append(
                        "      • Desfechos raros são tratados pelo especialista"
                    )
                    instructions.append("")
                    
                elif rule_type == "priority_filter":
                    # Já coberto acima
                    pass
                    
                else:
                    # Regra genérica
                    if blocked_phrases:
                        phrases_str = ", ".join(f'"{p}"' for p in blocked_phrases[:3])
                        instructions.append(f"   ❌ {action}: Evitar {phrases_str}")
                        instructions.append(f"      Motivo: {reason}")
                        instructions.append("")

            rule_number += 1

        # Keyword blocklist
        keyword_blocklist = active_filters.get("keyword_blocklist", [])
        if keyword_blocklist:
            keywords = ", ".join(f'"{kw}"' for kw in keyword_blocklist[:8])
            instructions.append(
                f"{rule_number}. 🔍 KEYWORDS TO AVOID: {keywords}"
            )
            rule_number += 1

        # Indicador de força
        if active_filters.get("rule_strength") == "hard":
            instructions.append("")
            instructions.append("=" * 60)
            instructions.append(
                "⚠️  HARD FILTERS ACTIVE: These rules are MANDATORY."
            )
            instructions.append(
                "Suggestions violating these patterns WILL BE REJECTED by the user."
            )
            instructions.append("=" * 60)

        # Se não há regras, ainda assim informar
        if rule_number == 1:
            instructions.append("No active filters from previous feedback.")
            instructions.append("Generate suggestions based on playbook content only.")

        instructions.append("")
        return "\n".join(instructions)

    def _apply_post_filters(
        self,
        suggestions: List[Suggestion],
        active_filters: Dict
    ) -> List[Suggestion]:
        """
        Aplica filtros pós-geração como rede de segurança.

        CRITICAL: Esta função é a última linha de defesa contra sugestões
        que violam os padrões de feedback aprendidos.

        Args:
            suggestions: Lista de sugestões geradas
            active_filters: Filtros ativos do memory_qa

        Returns:
            Lista filtrada de sugestões
        """
        if not active_filters:
            return suggestions

        filtered = []
        removed = []

        # Extrair blocked_phrases de todas as regras de padrão
        all_blocked_phrases = []
        for rule in active_filters.get("pattern_rules", []):
            phrases = rule.get("blocked_phrases", [])
            all_blocked_phrases.extend(phrases)

        for sug in suggestions:
            should_keep = True
            removal_reason = None

            # Texto completo para verificação
            text_to_check = f"{sug.title} {sug.description} {sug.rationale}".lower()

            # Filtro 1: Priority threshold
            if active_filters.get("priority_threshold") == "media":
                if sug.priority.lower() in ("baixa", "low"):
                    should_keep = False
                    removal_reason = f"Priority filter (threshold: media, got: {sug.priority})"

            # Filtro 2: Category filters
            if should_keep and sug.category in active_filters.get("category_filters", {}):
                if not active_filters["category_filters"][sug.category]:
                    should_keep = False
                    removal_reason = f"Category filter (blocked: {sug.category})"

            # Filtro 3: Keyword blocklist
            if should_keep and active_filters.get("keyword_blocklist"):
                for keyword in active_filters["keyword_blocklist"]:
                    if keyword.lower() in text_to_check:
                        should_keep = False
                        removal_reason = f"Keyword filter (blocked: {keyword})"
                        break

            # Filtro 4: Blocked phrases from pattern rules
            if should_keep and all_blocked_phrases:
                for phrase in all_blocked_phrases:
                    if phrase.lower() in text_to_check:
                        should_keep = False
                        removal_reason = f"Pattern rule blocked phrase: '{phrase}'"
                        break

            # Filtro 5: Pattern-based rules específicas
            if should_keep:
                for rule in active_filters.get("pattern_rules", []):
                    rule_type = rule.get("rule")
                    
                    # Context validation
                    if rule_type == "context_validation":
                        min_length = rule.get("min_length", 50)
                        if len(sug.rationale) < min_length:
                            should_keep = False
                            removal_reason = f"Context validation (rationale too short: {len(sug.rationale)} < {min_length})"
                            break
                    
                    # Medical autonomy - detectar restrições à autonomia médica
                    if rule_type == "medical_autonomy" and should_keep:
                        autonomy_patterns = [
                            "priorizar", "deve ser preferido", "substituir por",
                            "ao invés de", "sempre usar", "nunca prescrever",
                            "obrigatoriamente", "condicionar prescrição"
                        ]
                        if any(p in text_to_check for p in autonomy_patterns):
                            should_keep = False
                            removal_reason = f"Medical autonomy: suggestion restricts clinical decision"
                            break
                    
                    # Playbook strict - detectar sugestões fora do playbook
                    if rule_type == "playbook_strict" and should_keep:
                        out_of_playbook_patterns = [
                            "adicionar exame", "incluir medicamento", "novo procedimento",
                            "introduzir", "acrescentar tratamento", "não mencionado no playbook"
                        ]
                        if any(p in text_to_check for p in out_of_playbook_patterns):
                            should_keep = False
                            removal_reason = f"Playbook strict: suggests content outside playbook"
                            break
                    
                    # Existing logic - detectar tentativas de mudar lógica funcional
                    if rule_type == "existing_logic" and should_keep:
                        existing_logic_patterns = [
                            "otimizar condicional", "refinar condição", "ajustar lógica",
                            "modificar exclusive", "alterar preselected"
                        ]
                        if any(p in text_to_check for p in existing_logic_patterns):
                            should_keep = False
                            removal_reason = f"Existing logic: suggests changing working logic"
                            break
                    
                    # Complexity filter - detectar complexidade desnecessária
                    if rule_type == "complexity_filter" and should_keep:
                        complexity_patterns = [
                            "adicionar pergunta", "nova etapa", "verificação adicional",
                            "campo extra", "validação complementar"
                        ]
                        if any(p in text_to_check for p in complexity_patterns):
                            # Apenas bloquear se for baixa prioridade
                            if sug.priority.lower() in ("baixa", "low"):
                                should_keep = False
                                removal_reason = f"Complexity filter: low-priority suggestion adds complexity"
                                break

            # Filtro 6: Semantic pattern matching (padrões detectados automaticamente)
            if should_keep:
                # Pattern: Invasão da Autonomia Médica
                autonomy_invasion_patterns = ["priorizar", "deve ser", "preferir", "em vez de", "substituir por", "ao invés de"]
                if any(pattern in text_to_check for pattern in autonomy_invasion_patterns):
                    restrictive_terms = ["sempre", "obrigatório", "nunca", "proibido", "não pode"]
                    if any(term in text_to_check for term in restrictive_terms):
                        should_keep = False
                        removal_reason = f"Semantic: autonomy_invasion (restrictive medical guidance)"

                # Pattern: Out of scope
                if should_keep:
                    out_of_scope_patterns = ["introduzir", "adicionar medicamento", "incluir novo", "criar opção", "não está no playbook"]
                    if any(pattern in text_to_check for pattern in out_of_scope_patterns):
                        should_keep = False
                        removal_reason = f"Semantic: out_of_scope (content outside playbook)"

                # Pattern: Already implemented
                if should_keep:
                    already_implemented_patterns = ["já existe", "já implementado", "já tem", "já está", "já contempla"]
                    if any(pattern in text_to_check for pattern in already_implemented_patterns):
                        should_keep = False
                        removal_reason = f"Semantic: already_implemented"

            if should_keep:
                filtered.append(sug)
            else:
                removed.append({"suggestion": sug, "reason": removal_reason})
                logger.info(f"Post-filter removed: {sug.id} - {removal_reason}")

        # Safety check: se filtrou demais, relaxar filtros (mas manter os críticos)
        if len(filtered) < 5 and len(suggestions) >= 5:
            logger.warning(
                f"Post-filtering resulted in only {len(filtered)} suggestions (started with {len(suggestions)}). "
                f"Applying relaxed filters..."
            )

            # Relaxar: apenas aplicar filtros CRÍTICOS
            filtered = []
            for sug in suggestions:
                should_keep = True
                text_to_check = f"{sug.title} {sug.description} {sug.rationale}".lower()

                # Manter apenas filtro de playbook strict (crítico)
                out_of_playbook = any(p in text_to_check for p in [
                    "adicionar exame", "incluir medicamento", "novo procedimento",
                    "não mencionado no playbook"
                ])
                if out_of_playbook:
                    should_keep = False

                # Manter filtro de prioridade se strength == "hard"
                if should_keep and active_filters.get("rule_strength") == "hard":
                    if active_filters.get("priority_threshold") == "media":
                        if sug.priority.lower() in ("baixa", "low"):
                            should_keep = False

                if should_keep:
                    filtered.append(sug)

            logger.info(f"Relaxed filtering: {len(suggestions)} → {len(filtered)} suggestions")

            # Se ainda muito agressivo, retornar todas
            if len(filtered) < 5:
                logger.error(
                    f"Even relaxed filters result in <5 suggestions. Disabling filters for this run."
                )
                return suggestions

        if removed:
            logger.warning(
                f"Post-filtering removed {len(removed)} suggestions. "
                f"LLM didn't follow filter instructions completely."
            )
            for item in removed[:5]:
                logger.info(f"  - {item['suggestion'].id}: {item['reason']}")

        return filtered

    def _validate_playbook_references(
        self,
        suggestions: List[Suggestion],
        playbook_content: str
    ) -> List[Suggestion]:
        """
        Valida se sugestões têm referências válidas ao playbook.

        CRITICAL: Previne hallucinations removendo sugestões que não têm
        referência explícita ao conteúdo do playbook.

        Args:
            suggestions: Lista de sugestões geradas
            playbook_content: Conteúdo completo do playbook

        Returns:
            Lista filtrada apenas com sugestões que têm referências válidas
        """
        if not playbook_content or not suggestions:
            return suggestions

        validated = []
        removed = []

        # Normalizar playbook para comparação (case-insensitive, remove espaços extras)
        playbook_normalized = " ".join(playbook_content.lower().split())

        for sug in suggestions:
            should_keep = True
            removal_reason = None

            # Obter referência ao playbook da sugestão
            playbook_ref = None
            if hasattr(sug, 'evidence') and sug.evidence:
                if isinstance(sug.evidence, dict):
                    playbook_ref = sug.evidence.get('playbook_reference', '')
                elif hasattr(sug.evidence, 'playbook_reference'):
                    playbook_ref = sug.evidence.playbook_reference

            # Validação 1: Referência existe e é substancial?
            if not playbook_ref or len(playbook_ref.strip()) < 20:
                should_keep = False
                removal_reason = "NO_PLAYBOOK_REFERENCE (reference missing or too short - minimum 20 chars required)"

            # Validação 2: Referência é genérica/inválida?
            elif should_keep:
                generic_phrases = [
                    "based on medical",
                    "standard practice",
                    "clinical guideline",
                    "best practice",
                    "according to literature",
                    "medical consensus",
                    "não especificado",
                    "conforme literatura",
                    "segundo literatura",
                    "de acordo com",
                    "conforme diretrizes",
                    "baseado em evidências",
                    "evidências científicas",
                    "recomendação geral",
                    "prática clínica",
                    "protocolo padrão",
                    "guidelines gerais"
                ]

                ref_lower = playbook_ref.lower()
                if any(phrase in ref_lower for phrase in generic_phrases):
                    should_keep = False
                    removal_reason = "GENERIC_REFERENCE (not specific to playbook - contains generic medical phrases)"

            # Validação 3: Referência existe no playbook? (CRITICAL - must be verifiable)
            elif should_keep:
                # Extrair trecho relevante da referência
                ref_normalized = " ".join(playbook_ref.lower().split())

                # Pegar snippet de 30+ caracteres consecutivos da referência
                words = ref_normalized.split()
                if len(words) >= 6:
                    # Tentar encontrar snippet de 6 palavras consecutivas no playbook (mais rigoroso)
                    found = False
                    for i in range(len(words) - 5):
                        snippet = " ".join(words[i:i+6])
                        if len(snippet) >= 30 and snippet in playbook_normalized:
                            found = True
                            break
                    
                    # Se não encontrou com 6 palavras, tentar com 5 (mais permissivo, mas ainda válido)
                    if not found and len(words) >= 5:
                        for i in range(len(words) - 4):
                            snippet = " ".join(words[i:i+5])
                            if len(snippet) >= 25 and snippet in playbook_normalized:
                                found = True
                                break

                    if not found:
                        should_keep = False
                        removal_reason = f"REFERENCE_NOT_IN_PLAYBOOK (cannot verify reference in playbook: '{playbook_ref[:80]}...')"
                else:
                    # Referência muito curta para validar adequadamente
                    should_keep = False
                    removal_reason = f"REFERENCE_TOO_SHORT (reference has fewer than 6 words, cannot verify: '{playbook_ref[:60]}...')"

            if should_keep:
                validated.append(sug)
            else:
                removed.append({"suggestion": sug, "reason": removal_reason})
                logger.warning(f"Playbook validation removed: {sug.id} - {removal_reason}")

        # Relatório de remoções
            if removed:
                logger.warning(
                    f"Playbook validation removed {len(removed)} suggestions that lack valid playbook references. "
                    f"This indicates the LLM generated content outside the playbook."
                )
                # Log detalhes das primeiras 5 remoções
                for i, rem in enumerate(removed[:5]):
                    logger.warning(f"  Removed #{i+1}: {rem['suggestion'].id} - {rem['reason']}")
        
        return validated

    def _extract_suggestions(self, llm_response) -> List[Suggestion]:
        """
        Extrai lista de objetos Suggestion da resposta do LLM.
        
        Inclui validação de contrato (Wave 1).
        
        Args:
            llm_response: Either a dict (already parsed) or a JSON string from LLM.
        """
        suggestions = []
        try:
            # 1. Handle both dict and string inputs
            if isinstance(llm_response, dict):
                data = llm_response
            else:
                # Limpar e parsear JSON string
                cleaned_response = llm_response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                
                data = json.loads(cleaned_response.strip())
            
            # 2. Validar Contrato (Wave 1)
            raw_suggestions = []
            try:
                from ..validators.llm_contract import EnhancedAnalysisResponse
                # Validate schema but don't crash analysis if valid data exists
                # We want to catch Drift but be resilient in Wave 1
                validated_response = EnhancedAnalysisResponse(**data)
                
                # Convert back to dicts for processing (to keep logic compatible)
                # In future we can work with objects directly
                raw_suggestions = [s.dict() for s in validated_response.improvement_suggestions]
                logger.info("✅ LLM Output validated against Pydantic Contract")
                
            except Exception as e:
                # Soft block for Wave 1 - allow fallback but log error
                logger.warning(f"⚠️ LLM Output Contract Violation: {e}")
                logger.warning("Proceeding with raw extraction (Best Effort)...")
                
                # Fallback extraction
                raw_suggestions = data.get("improvement_suggestions", [])
                if not raw_suggestions and isinstance(data, list):
                    raw_suggestions = data
            
            # 3. Processar sugestões
            scorer = ImpactScorer()
            for idx, sug_data in enumerate(raw_suggestions):
                try:
                    sug_id = sug_data.get("id", f"sug_{idx+1}")
                    
                    # Extract nested objects safely using ImpactScorer
                    # This is more robust than creating ImpactScores directly from dict
                    try:
                        impact_scores = scorer.calculate_impact_scores(sug_data)
                    except Exception as e:
                        logger.warning(f"Failed to calculate impact_scores for {sug_id}: {e}")
                        # Use default scores
                        impact_scores = ImpactScores(seguranca=0, economia="L", eficiencia="L", usabilidade=0)
                    
                    evidence = sug_data.get("evidence", {})
                    impl_effort = sug_data.get("implementation_effort", {})
                    cost_estimate = sug_data.get("auto_apply_cost_estimate", {})
                    
                    specific_location = sug_data.get("specific_location")
                    
                    suggestion = Suggestion(
                        id=sug_id,
                        category=sug_data.get("category", "eficiencia"),
                        priority=sug_data.get("priority", "media"),
                        title=sug_data.get("title", f"Suggestion {idx+1}"),
                        description=sug_data.get("description", ""),
                        rationale=sug_data.get("rationale", ""),
                        impact_scores=impact_scores,
                        evidence=evidence,
                        implementation_effort=impl_effort,
                        auto_apply_cost_estimate=cost_estimate,
                        specific_location=specific_location
                    )
                    
                    suggestions.append(suggestion)
                except Exception as e:
                     logger.warning(f"Failed to create Suggestion object for {idx}: {e}")
                     continue
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {llm_response[:500]}...")
            
        except Exception as e:
            logger.error(f"Unexpected error extracting suggestions: {e}", exc_info=True)

        logger.info(f"Successfully extracted {len(suggestions)} suggestions")
        return suggestions

    def _categorize_suggestions(
        self,
        suggestions: List[Suggestion]
    ) -> List[Suggestion]:
        """
        Valida e corrige categorias das sugestões.

        Args:
            suggestions: Lista de sugestões

        Returns:
            Sugestões com categorias validadas
        """
        valid_categories = {"seguranca", "economia", "eficiencia", "usabilidade"}
        
        for sug in suggestions:
            if sug.category not in valid_categories:
                # Auto-categorize based on content if invalid
                if "segurança" in sug.description.lower() or "safety" in sug.description.lower() or "red flag" in sug.description.lower():
                    sug.category = "seguranca"
                elif "custo" in sug.description.lower() or "economia" in sug.description.lower() or "economic" in sug.description.lower():
                    sug.category = "economia"
                elif "eficiencia" in sug.description.lower() or "efficiency" in sug.description.lower() or "workflow" in sug.description.lower():
                    sug.category = "eficiencia"
                else:
                    sug.category = "usabilidade"
                
                logger.debug(f"Auto-categorized suggestion {sug.id} as {sug.category}")
        
        return suggestions

    def _prioritize_suggestions(
        self,
        suggestions: List[Suggestion]
    ) -> List[Suggestion]:
        """
        Prioriza sugestões baseado em scores de impacto.

        Algoritmo:
        - Alta: Segurança ≥8 OR (Economia="A" AND Segurança≥5)
        - Média: Segurança 5-7 OR Economia="M"/"A" OR Eficiência="A"
        - Baixa: Demais casos

        Args:
            suggestions: Lista de sugestões

        Returns:
            Sugestões priorizadas (alta, média, baixa)
        """
        for sug in suggestions:
            seguranca = getattr(sug.impact_scores, 'seguranca', 0)
            economia = getattr(sug.impact_scores, 'economia', 'L')
            eficiencia = getattr(sug.impact_scores, 'eficiencia', 'L')
            
            # Calculate priority based on algorithm
            if seguranca >= 8 or (economia == "A" and seguranca >= 5):
                sug.priority = "alta"
            elif seguranca >= 5 or economia in ("M", "A") or eficiencia == "A":
                sug.priority = "media"
            else:
                sug.priority = "baixa"
        
        # Sort by priority: alta > media > baixa
        priority_order = {"alta": 0, "media": 1, "baixa": 2}
        suggestions_sorted = sorted(
            suggestions,
            key=lambda s: (priority_order.get(s.priority, 3), getattr(s.impact_scores, 'seguranca', 0)),
            reverse=True
        )
        
        logger.info(
            f"Prioritized suggestions: "
            f"alta={sum(1 for s in suggestions_sorted if s.priority == 'alta')}, "
            f"media={sum(1 for s in suggestions_sorted if s.priority == 'media')}, "
            f"baixa={sum(1 for s in suggestions_sorted if s.priority == 'baixa')}"
        )
        
        return suggestions_sorted
    
    def _calculate_aggregate_scores(
        self,
        suggestions: List[Suggestion]
    ) -> Dict[str, float]:
        """
        Calcula scores agregados por categoria.

        Args:
            suggestions: Lista de sugestões priorizadas

        Returns:
            Dict com scores agregados
        """
        if not suggestions:
            return {
                "seguranca_avg": 0.0,
                "usabilidade_avg": 0.0,
                "economia_high_count": 0,
                "eficiencia_high_count": 0
            }
        
        seguranca_scores = [getattr(s.impact_scores, 'seguranca', 0) for s in suggestions]
        usabilidade_scores = [getattr(s.impact_scores, 'usabilidade', 0) for s in suggestions]
        economia_high = sum(1 for s in suggestions if getattr(s.impact_scores, 'economia', None) == "A")
        eficiencia_high = sum(1 for s in suggestions if getattr(s.impact_scores, 'eficiencia', None) == "A")
        
        return {
            "seguranca_avg": sum(seguranca_scores) / len(seguranca_scores) if seguranca_scores else 0.0,
            "usabilidade_avg": sum(usabilidade_scores) / len(usabilidade_scores) if usabilidade_scores else 0.0,
            "economia_high_count": economia_high,
            "eficiencia_high_count": eficiencia_high,
            "total_suggestions": len(suggestions)
        }
