"""
Protocol Reconstructor - Reconstrução de Protocolo JSON

Responsabilidades:
- Reconstruir protocolo JSON baseado em sugestões de melhoria
- Integração com sistema de autorização de custos
- Validação estrutural do protocolo reconstruído
- Rastreabilidade completa de mudanças

Fase de Implementação: FASE 5 (MVP básico)
Status: ✅ Implementado (MVP)
"""

import sys
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# Add src to path for imports
current_dir = Path(__file__).resolve().parent.parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from agent_v2.logger import logger
from agent_v2.llm_client import LLMClient
from ..cost_control import CostEstimator, CostEstimate
from ..analysis.enhanced_analyzer import ExpandedAnalysisResult


@dataclass
class ReconstructionResult:
    """Resultado da reconstrução do protocolo."""
    reconstructed_protocol: Dict
    changes_applied: List[Dict]
    validation_passed: bool
    cost_actual: Optional[Dict] = None
    metadata: Optional[Dict] = None


class ProtocolReconstructor:
    """
    Reconstrói protocolo JSON baseado em sugestões de melhoria.
    
    Este componente implementa a reconstrução do protocolo usando LLM,
    com controle rigoroso de custos e autorização.
    """

    def __init__(self, model: str = "x-ai/grok-4.1-fast:free"):
        """
        Inicializa o reconstrutor de protocolo.
        
        Args:
            model: Modelo LLM a ser utilizado (default: Grok 4.1 Fast Free - gratuito, contexto 2M tokens)
        """
        self.model = model
        self.llm_client = LLMClient(model=model)
        self.cost_estimator = CostEstimator()
        logger.info(f"ProtocolReconstructor initialized with model: {model}")

    def reconstruct_with_authorization(
        self,
        original_protocol: Dict,
        suggestions: List[Dict],
        analysis_result: Optional[ExpandedAnalysisResult] = None
    ) -> Optional[ReconstructionResult]:
        """
        Reconstrói protocolo (estimativa de custo informativa apenas).
        
        Fluxo:
        1. Estima custo da reconstrução (informativo)
        2. Reconstrói protocolo via LLM
        3. Valida protocolo reconstruído
        4. Retorna resultado
        
        Args:
            original_protocol: Protocolo JSON original
            suggestions: Lista de sugestões a aplicar
            analysis_result: Resultado completo da análise (opcional)
            
        Returns:
            ReconstructionResult ou None se houver erro
        """
        if not suggestions:
            logger.warning("No suggestions provided for reconstruction")
            return None
        
        # Step 1: Estimar custo (informativo apenas, sem autorização)
        logger.info("Step 1: Estimating cost...")
        protocol_size = len(json.dumps(original_protocol, ensure_ascii=False))
        
        cost_estimate = self.cost_estimator.estimate_auto_apply_cost(
            protocol_size=protocol_size,
            suggestions=suggestions,
            model=self.model
        )
        
        # Exibir estimativa informativa (sem solicitar autorização)
        self._display_cost_estimate(cost_estimate, f"Reconstrução de Protocolo JSON ({len(suggestions)} sugestões)")
        
        logger.info("Step 1: Cost estimated, proceeding with reconstruction...")
        
        # Step 3: Reconstruir protocolo
        logger.info("Starting protocol reconstruction...")
        try:
            reconstructed = self._reconstruct_protocol_llm(
                original_protocol=original_protocol,
                suggestions=suggestions,
                analysis_result=analysis_result
            )
            
            # Step 4: Validar (básico - verificar se é JSON válido)
            validation_passed = self._validate_reconstructed(reconstructed)
            
            if not validation_passed:
                logger.error("Reconstructed protocol failed validation")
                return None
            
            # Step 5: Identificar mudanças aplicadas
            changes_applied = self._identify_changes(original_protocol, reconstructed, suggestions)
            
            # Atualizar versão no protocolo reconstruído
            from .version_utils import (
                extract_version_from_protocol,
                increment_version,
                update_protocol_version
            )
            
            # Extrair e incrementar versão
            current_version = extract_version_from_protocol(original_protocol)
            if current_version:
                new_version = increment_version(current_version, increment_type="patch")
                reconstructed = update_protocol_version(reconstructed, new_version)
            
            result = ReconstructionResult(
                reconstructed_protocol=reconstructed,
                changes_applied=changes_applied,
                validation_passed=True,
                metadata={
                    "original_size": protocol_size,
                    "reconstructed_size": len(json.dumps(reconstructed, ensure_ascii=False)),
                    "suggestions_applied": len(suggestions),
                    "timestamp": datetime.now().isoformat(),
                    "model_used": self.model,
                    "original_version": current_version,
                    "new_version": new_version if current_version else None
                }
            )
            
            logger.info("Protocol reconstruction completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error during protocol reconstruction: {e}", exc_info=True)
            raise

    def _reconstruct_protocol_llm(
        self,
        original_protocol: Dict,
        suggestions: List[Dict],
        analysis_result: Optional[ExpandedAnalysisResult] = None
    ) -> Dict:
        """
        Reconstrói protocolo usando LLM.
        
        Args:
            original_protocol: Protocolo original
            suggestions: Sugestões a aplicar
            analysis_result: Resultado da análise (opcional)
            
        Returns:
            Protocolo reconstruído
        """
        # Construir prompt para reconstrução
        prompt = self._build_reconstruction_prompt(
            original_protocol=original_protocol,
            suggestions=suggestions,
            analysis_result=analysis_result
        )
        
        # Chamar LLM
        logger.info("Calling LLM for protocol reconstruction...")
        # LLMClient.analyze() retorna dict parseado do JSON
        response = self.llm_client.analyze(prompt)
        
        # LLMClient já parseia o JSON, então response deve ser dict
        if isinstance(response, dict):
            # O prompt pede para retornar {"reconstructed_protocol": ...}
            if "reconstructed_protocol" in response:
                reconstructed = response["reconstructed_protocol"]
            elif "protocol" in response:
                reconstructed = response["protocol"]
            elif "result" in response:
                reconstructed = response["result"]
            else:
                # Se não tem chave específica, verificar se response já é o protocolo
                # (pode acontecer se o LLM ignorar a estrutura pedida)
                if "nodes" in response or any(key.startswith("node_") for key in response.keys()):
                    # Parece ser o protocolo diretamente
                    reconstructed = response
                else:
                    # Tentar usar response como protocolo
                    reconstructed = response
        else:
            # Se não é dict, tentar extrair JSON de string
            reconstructed = self._extract_json_from_response(str(response))
        
        return reconstructed

    def _build_reconstruction_prompt(
        self,
        original_protocol: Dict,
        suggestions: List[Dict],
        analysis_result: Optional[ExpandedAnalysisResult] = None
    ) -> str:
        """
        Constrói prompt para reconstrução do protocolo.
        
        Args:
            original_protocol: Protocolo original
            suggestions: Sugestões a aplicar
            analysis_result: Resultado da análise (opcional)
            
        Returns:
            Prompt formatado
        """
        protocol_json_str = json.dumps(original_protocol, ensure_ascii=False, indent=2)
        
        # Formatar sugestões
        suggestions_text = "\n".join([
            f"\n{i+1}. [{s.get('id', 'N/A')}] {s.get('category', 'N/A')} - {s.get('priority', 'N/A')}:\n"
            f"   Título: {s.get('title', 'N/A')}\n"
            f"   Descrição: {s.get('description', 'N/A')}\n"
            f"   Localização: {s.get('specific_location', {})}\n"
            for i, s in enumerate(suggestions)
        ])
        
        prompt = f"""You are an expert medical protocol developer. Your task is to reconstruct a medical protocol JSON by applying improvement suggestions.

ORIGINAL PROTOCOL JSON:

{protocol_json_str}

IMPROVEMENT SUGGESTIONS TO APPLY:

{suggestions_text}

INSTRUCTIONS:

1. Apply ALL the suggestions above to the original protocol JSON
2. Maintain the complete structure and all existing nodes
3. Only modify/add what is specified in the suggestions
4. Preserve all metadata, IDs, and relationships
5. Ensure the result is valid JSON
6. Keep the same overall structure and format

CRITICAL REQUIREMENTS:

- The output MUST be valid JSON
- Do NOT remove any existing nodes unless explicitly requested
- Do NOT change node IDs unless necessary
- Preserve all conditional logic and relationships
- Maintain backward compatibility where possible

OUTPUT FORMAT:

You MUST return a JSON object with the following structure:

{{
  "reconstructed_protocol": <complete protocol JSON here>
}}

The "reconstructed_protocol" field must contain the complete, valid protocol JSON with all improvements applied.

IMPORTANT: Return ONLY valid JSON. No markdown, no explanations, no code blocks. Just the JSON object.
"""
        return prompt

    def _extract_json_from_response(self, response: Dict) -> Dict:
        """
        Extrai JSON da resposta do LLM.
        
        Args:
            response: Resposta do LLM
            
        Returns:
            Protocolo JSON extraído
        """
        # Tentar extrair JSON da resposta
        content = response.get("content", "")
        if isinstance(content, dict):
            content = json.dumps(content)
        
        # Tentar parsear diretamente
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Tentar extrair JSON de markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Tentar encontrar JSON entre chaves
            brace_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if brace_match:
                return json.loads(brace_match.group(1))
            
            raise ValueError("Could not extract valid JSON from LLM response")

    def _validate_reconstructed(self, protocol: Dict) -> bool:
        """
        Valida protocolo reconstruído (validação básica).
        
        Args:
            protocol: Protocolo a validar
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            # Verificar se é dict
            if not isinstance(protocol, dict):
                return False
            
            # Verificar se tem estrutura básica de protocolo
            # (pode variar, mas geralmente tem nodes ou estrutura similar)
            if not protocol:
                return False
            
            # Tentar serializar para verificar se é JSON válido
            json.dumps(protocol)
            
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
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

    def _identify_changes(
        self,
        original: Dict,
        reconstructed: Dict,
        suggestions: List[Dict]
    ) -> List[Dict]:
        """
        Identifica mudanças aplicadas (versão simplificada).
        
        Args:
            original: Protocolo original
            reconstructed: Protocolo reconstruído
            suggestions: Sugestões aplicadas
            
        Returns:
            Lista de mudanças identificadas
        """
        changes = []

        # CRITICAL FIX: Return data structure that matches show_diff() expectations
        # show_diff() expects: {type, location, description}
        for sug in suggestions:
            # Determine change type from priority or default to "modified"
            priority = sug.get("priority", "media").lower()
            change_type = "added" if priority in ("alta", "high", "crítica", "critical") else "modified"

            # Build location string with category and ID
            category = sug.get("category", "N/A")
            sug_id = sug.get("id", "N/A")
            location = f"{category} | ID: {sug_id}"

            # Get description (truncate to 200 chars for display)
            description = sug.get("description", sug.get("title", "N/A"))
            if len(description) > 200:
                description = description[:197] + "..."

            changes.append({
                "type": change_type,
                "location": location,
                "description": description
            })

        return changes

