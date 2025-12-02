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

# Add src to path for imports
current_dir = Path(__file__).resolve().parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import V2 components
from agent_v2.llm_client import LLMClient
from agent_v2.logger import logger

# Import V3 components
from .impact_scorer import ImpactScorer, ImpactScores
from ..cost_control import CostEstimator, CostEstimate

# Import prompt template
from config.prompts.enhanced_analysis_prompt import (
    ENHANCED_ANALYSIS_PROMPT_TEMPLATE,
    ENHANCED_OUTPUT_SCHEMA_JSON
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
        model: str = "x-ai/grok-4.1-fast:free"
    ):
        """
        Inicializa o analisador expandido.

        Args:
            model: Modelo LLM a ser utilizado (default: Grok 4.1 Fast Free - gratuito, contexto 2M tokens)
        """
        self.model = model
        self.llm_client = LLMClient(model=model)
        self.impact_scorer = ImpactScorer()
        self.cost_estimator = CostEstimator()
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
        logger.info("Step 3: Calling LLM for enhanced analysis (20-50 suggestions)...")
        try:
            llm_result = self.llm_client.analyze(prompt_structure)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise
        
        # Step 4: Extract and process suggestions
        logger.info("Step 4: Extracting and processing suggestions...")
        suggestions = self._extract_suggestions(llm_result)
        
        # Step 5: Categorize and prioritize
        logger.info("Step 5: Categorizing and prioritizing suggestions...")
        categorized = self._categorize_suggestions(suggestions)
        prioritized = self._prioritize_suggestions(categorized)
        
        # Step 6: Build result
        logger.info("Step 6: Building expanded analysis result...")
        
        # Calculate aggregate impact scores
        impact_scores = self._calculate_aggregate_scores(prioritized)
        
        # Build evidence mapping
        evidence_mapping = {
            sug.id: sug.evidence.get("playbook_reference", "")
            for sug in prioritized
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
        input_cost = cost_estimate.estimated_cost_usd["input"]
        output_cost = cost_estimate.estimated_cost_usd["output"]
        input_tokens = cost_estimate.estimated_tokens["input"]
        output_tokens = cost_estimate.estimated_tokens["output"]
        
        print("\n" + "=" * 60)
        print("ESTIMATIVA DE CUSTO")
        print("=" * 60)
        print(f"\nOperação: {operation_description}")
        print(f"Modelo: {cost_estimate.model}")
        print(f"\nTokens Estimados:")
        print(f"  Input:  {input_tokens:,} tokens (${input_cost:.4f})")
        print(f"  Output: {output_tokens:,} tokens (${output_cost:.4f})")
        print(f"  Total:  {input_tokens + output_tokens:,} tokens")
        print(f"\nCusto Total Estimado: ${total_cost:.4f} USD")
        print(f"Confiança: {cost_estimate.confidence.upper()}")
        print("=" * 60)

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
        
        # Build prompt with template
        prompt_text = ENHANCED_ANALYSIS_PROMPT_TEMPLATE.format(
            playbook_content=playbook_content,
            protocol_json=protocol_formatted,
            base_analysis=base_analysis_formatted,
            output_schema=ENHANCED_OUTPUT_SCHEMA_JSON
        )
        
        # Use caching if playbook is substantial (>1000 chars)
        use_cache = len(playbook_content) > 1000
        
        if use_cache:
            # Structure for prompt caching: playbook in system, protocol in messages
            base_instructions = """You are an expert medical protocol quality analyst conducting DEEP, COMPREHENSIVE analysis.

CONTEXT: You will analyze a medical protocol (JSON decision tree) against its corresponding clinical playbook to identify ALL possible improvements, gaps, and optimization opportunities.

INPUT MATERIALS:

1. CLINICAL PLAYBOOK (Medical Guidelines):

"""
            
            protocol_instructions_template = """
2. PROTOCOL JSON (Decision Tree):

{protocol_json}

3. BASE ANALYSIS (from V2):

{base_analysis}

---

YOUR EXPANDED ANALYSIS MUST GENERATE 20-50 DETAILED IMPROVEMENT SUGGESTIONS:

CRITICAL REQUIREMENTS:

1. QUANTITY: Generate 20-50 suggestions (not 5-15). Be exhaustive and thorough.
   - Structural improvements (5-10 suggestions)
   - Clinical coverage gaps (5-15 suggestions)
   - Safety enhancements (3-8 suggestions)
   - Efficiency optimizations (3-8 suggestions)
   - Usability improvements (2-6 suggestions)
   - Workflow enhancements (2-5 suggestions)

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

5. EVIDENCE TRACEABILITY: For EACH suggestion, provide:
   - playbook_reference: Exact quote or section from playbook that supports this suggestion
   - context: Additional context explaining why this improvement is needed
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
- Generate 20-50 suggestions (minimum 20, target 30-40, maximum 50)
- Every suggestion MUST have ALL required fields
"""
            
            protocol_instructions = protocol_instructions_template.format(
                protocol_json=protocol_formatted,
                base_analysis=base_analysis_formatted,
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

    def _extract_suggestions(
        self,
        llm_result: Dict
    ) -> List[Suggestion]:
        """
        Extrai sugestões estruturadas da resposta do LLM.

        Args:
            llm_result: Resposta do LLM (já parseada como dict)

        Returns:
            Lista de sugestões estruturadas
        """
        suggestions = []
        suggestions_data = llm_result.get("improvement_suggestions", [])
        
        if not suggestions_data:
            logger.warning("No suggestions found in LLM response")
            return suggestions
        
        logger.info(f"Extracting {len(suggestions_data)} suggestions from LLM response...")
        
        for idx, sug_data in enumerate(suggestions_data):
            try:
                # Generate ID if missing
                sug_id = sug_data.get("id", f"sug_{idx+1:03d}")
                
                # Extract impact scores
                impact_scores_raw = sug_data.get("impact_scores", {})
                impact_scores = {
                    "seguranca": impact_scores_raw.get("seguranca", 0),
                    "economia": impact_scores_raw.get("economia", "L"),
                    "eficiencia": impact_scores_raw.get("eficiencia", "L"),
                    "usabilidade": impact_scores_raw.get("usabilidade", 0)
                }
                
                # Extract evidence
                evidence = sug_data.get("evidence", {})
                if not isinstance(evidence, dict):
                    evidence = {
                        "playbook_reference": str(evidence) if evidence else "",
                        "context": "",
                        "clinical_rationale": ""
                    }
                
                # Extract implementation effort
                impl_effort = sug_data.get("implementation_effort", {})
                if not isinstance(impl_effort, dict):
                    impl_effort = {
                        "effort": "medio",
                        "estimated_time": "1h",
                        "complexity": "moderada"
                    }
                
                # Extract cost estimate (default to 0 if not provided)
                cost_estimate = sug_data.get("auto_apply_cost_estimate", {
                    "estimated_tokens": 0,
                    "estimated_cost_usd": 0.0
                })
                
                # Extract specific location
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
                logger.warning(f"Failed to extract suggestion {idx+1}: {e}. Skipping.")
                continue
        
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
            seguranca = sug.impact_scores.get("seguranca", 0)
            economia = sug.impact_scores.get("economia", "L")
            eficiencia = sug.impact_scores.get("eficiencia", "L")
            
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
            key=lambda s: (priority_order.get(s.priority, 3), s.impact_scores.get("seguranca", 0)),
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
        
        seguranca_scores = [s.impact_scores.get("seguranca", 0) for s in suggestions]
        usabilidade_scores = [s.impact_scores.get("usabilidade", 0) for s in suggestions]
        economia_high = sum(1 for s in suggestions if s.impact_scores.get("economia") == "A")
        eficiencia_high = sum(1 for s in suggestions if s.impact_scores.get("eficiencia") == "A")
        
        return {
            "seguranca_avg": sum(seguranca_scores) / len(seguranca_scores) if seguranca_scores else 0.0,
            "usabilidade_avg": sum(usabilidade_scores) / len(usabilidade_scores) if usabilidade_scores else 0.0,
            "economia_high_count": economia_high,
            "eficiencia_high_count": eficiencia_high,
            "total_suggestions": len(suggestions)
        }
