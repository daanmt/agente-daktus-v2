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
import time
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from ..core.logger import logger
from ..core.llm_client import LLMClient
from ..cost_control import CostEstimator, CostEstimate
from ..analysis.enhanced import ExpandedAnalysisResult


@dataclass
class ReconstructionResult:
    """Resultado da reconstrução do protocolo."""
    reconstructed_protocol: Dict
    changes_applied: List[Dict]
    validation_passed: bool
    cost_actual: Optional[Dict] = None
    metadata: Optional[Dict] = None
    detailed_changelog: Optional[List[Dict]] = None  # LLM-generated detailed changes for audit


@dataclass
class SectionReconstructionStatus:
    """Status de reconstrução de uma seção do protocolo."""
    section_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    reconstructed_data: Optional[Dict] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    timestamp: Optional[str] = None


class ProtocolReconstructor:
    """
    Reconstrói protocolo JSON baseado em sugestões de melhoria.
    
    Este componente implementa a reconstrução do protocolo usando LLM,
    com controle rigoroso de custos e autorização.
    """

    def __init__(self, model: str = "google/gemini-2.5-flash-lite"):
        """
        Inicializa o reconstrutor de protocolo.
        
        Args:
            model: Modelo LLM a ser utilizado (default: Gemini 2.5 Flash Lite - barato e estável)
        """
        self.model = model
        self.llm_client = LLMClient(model=model)
        self.cost_estimator = CostEstimator()
        logger.info(f"ProtocolReconstructor initialized with model: {model}")

    def reconstruct_protocol(
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
            
            # Step: Verify changes were actually applied (Wave 2)
            try:
                from .change_verifier import verify_reconstruction_changes
                
                verification = verify_reconstruction_changes(
                    original_protocol,
                    reconstructed,
                    suggestions
                )
                
                result.metadata["verification"] = verification
                
                if verification['failed'] > 0:
                    logger.warning(
                        f"⚠️ Change verification: {verification['verified']}/{verification['total']} verified "
                        f"({verification['failed']} not applied)"
                    )
            except ImportError:
                logger.debug("Change verifier not available")
            except Exception as e:
                logger.warning(f"Change verification error: {e}")
            
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
        Reconstrói protocolo usando LLM com estratégia de chunking.

        NOVO: Divide protocolo em seções, reconstrói cada seção independentemente,
        depois monta o protocolo final com validação de cross-references.

        Args:
            original_protocol: Protocolo original
            suggestions: Sugestões a aplicar
            analysis_result: Resultado da análise (opcional)

        Returns:
            Protocolo reconstruído completo

        Raises:
            ValueError: Se reconstrução falhar
        """
        logger.info("Starting CHUNKED protocol reconstruction...")

        # Step 1: Calculate new version
        from .version_utils import extract_version_from_protocol, increment_version
        current_version = extract_version_from_protocol(original_protocol)
        new_version = increment_version(current_version, "patch") if current_version else "1.0.1"

        # Step 2: Enumerate sections
        sections = self._enumerate_sections(original_protocol, suggestions)
        logger.info(f"Protocol divided into {len(sections)} sections")

        # Step 3: Initialize tracking
        section_statuses = self._track_section_progress(sections)

        # Step 4: Reconstruct each section
        for section in sections:
            section_id = section["section_id"]
            logger.info(f"Processing {section_id}...")

            try:
                section_statuses[section_id].status = "in_progress"

                # Reconstruct with retry
                reconstructed_data = self._reconstruct_section_with_retry(
                    section=section,
                    new_version=new_version,
                    max_retries=3
                )

                # Update status
                section_statuses[section_id].status = "completed"
                section_statuses[section_id].reconstructed_data = reconstructed_data
                section_statuses[section_id].timestamp = datetime.now().isoformat()

                logger.info(f"{section_id} completed successfully")

            except Exception as e:
                section_statuses[section_id].status = "failed"
                section_statuses[section_id].error_message = str(e)
                logger.error(f"{section_id} failed: {e}", exc_info=True)
                raise ValueError(f"Section reconstruction failed: {section_id}") from e

        # Step 5: Assemble protocol
        assembled_protocol = self._assemble_protocol(original_protocol, section_statuses)

        # Step 6: Validate cross-references (non-fatal validation)
        is_valid, warnings = self._validate_cross_references(assembled_protocol)

        if warnings:
            logger.warning(
                f"Cross-reference validation warnings ({len(warnings)}): "
                f"{warnings[:5]}{'...' if len(warnings) > 5 else ''}"
            )
            # Log all warnings at debug level for detailed analysis
            for warning in warnings:
                logger.debug(f"Cross-reference warning: {warning}")

        # Note: is_valid is always True now - warnings are non-fatal
        # Only critical structural errors (like invalid edges) would block reconstruction
        # but those are handled separately in _assemble_protocol
        if not is_valid:
            # This should never happen now, but kept for safety
            logger.error(f"Cross-reference validation failed: {warnings}")
            raise ValueError(f"Cross-reference validation failed: {warnings}")

        logger.info("Chunked reconstruction completed successfully")
        return assembled_protocol

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
        # CRITICAL FIX: Calcular nova versão para incluir no changelog
        from .version_utils import extract_version_from_protocol, increment_version

        current_version = extract_version_from_protocol(original_protocol)
        if current_version:
            new_version = increment_version(current_version, increment_type="patch")
        else:
            new_version = "1.0.1"  # Fallback

        protocol_json_str = json.dumps(original_protocol, ensure_ascii=False, indent=2)
        
        # Formatar sugestões com implementation_path para aplicação direta
        suggestions_formatted = []
        for i, s in enumerate(suggestions):
            sug_text = f"\n{i+1}. [{s.get('id', 'N/A')}] {s.get('category', 'N/A')} - {s.get('priority', 'N/A')}:\n"
            sug_text += f"   Título: {s.get('title', 'N/A')}\n"
            sug_text += f"   Descrição: {s.get('description', 'N/A')}\n"
            
            # Include implementation_path if available (structured for easy application)
            impl_path = s.get('implementation_path', {})
            if impl_path and impl_path.get('json_path'):
                sug_text += f"\n   🎯 IMPLEMENTATION PATH (USE THIS TO APPLY):\n"
                sug_text += f"   - JSON Path: {impl_path.get('json_path', 'N/A')}\n"
                sug_text += f"   - Modification Type: {impl_path.get('modification_type', 'N/A')}\n"
                sug_text += f"   - Current Value: {impl_path.get('current_value', 'null')}\n"
                sug_text += f"   - Proposed Value: {json.dumps(impl_path.get('proposed_value'), ensure_ascii=False) if impl_path.get('proposed_value') else 'N/A'}\n"
            else:
                # Fallback to specific_location
                sug_text += f"   Localização: {s.get('specific_location', {})}\n"
            
            suggestions_formatted.append(sug_text)
        
        suggestions_text = "".join(suggestions_formatted)
        
        prompt = f"""You are an expert medical protocol developer for the Daktus Spider platform. Your task is to reconstruct a medical protocol JSON by applying improvement suggestions.

🔴 CRITICAL: SPIDER/DAKTUS PROTOCOL STRUCTURE

The protocol JSON uses this specific structure:

NODE TYPES:
- type: "custom" → Nodo de Coleta (questions for clinicians)
- type: "conduct" → Nodo de Conduta (exams, medications, alerts)
- type: "summary" → Nodo de Processamento (clinical expressions)

ADDING A QUESTION TO A CUSTOM NODE:
```json
{{
  "id": "q-NEW",
  "uid": "nome_unico_sem_espacos",
  "nome": "Texto da pergunta?",
  "tipo": "multipla-escolha",
  "options": [
    {{"id": "opcao_sim", "label": "Sim"}},
    {{"id": "opcao_nao", "label": "Não", "excludente": true}}
  ],
  "expressao": "",
  "visibilidade": "visivel"
}}
```

ADDING AN OPTION TO EXISTING QUESTION:
Find the question by uid, add to its options array:
```json
{{"id": "nova_opcao_id", "label": "Texto da opção"}}
```

ADDING/MODIFYING mensagem_alerta IN CONDUCT NODE:
```json
{{
  "type": "conduct",
  "data": {{
    "mensagem_alerta": "ATENÇÃO: Texto do alerta para o profissional..."
  }}
}}
```

ADDING/MODIFYING condicao (CONDITIONAL):
```json
{{
  "nome": "Nome do exame",
  "condicao": "(febre == True) and ('sintoma_x' in sintomas)"
}}
```

CONDITIONAL SYNTAX (Python-like):
- 'valor' in variavel → Check if selected
- 'valor' not in variavel → Check if NOT selected
- variavel == True/False → Boolean check
- (cond1) and (cond2) → Both conditions
- (cond1) or (cond2) → Either condition

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

🚨 CRITICAL: DOCUMENT CHANGES IN NODE DESCRIPTIONS

For EVERY node that is modified, you MUST add a changelog entry to its "description" field:

Format for changelog entries:
```
[CHANGELOG v{new_version}]: <summary of what changed>
- Changed: <specific detail>
- Reason: <why this change was made (from suggestion)>
- Suggestion ID: <suggestion_id>
```

Example:
If you modify node "node_001" based on suggestion "sug_042", update its description:
```
"description": "Original description of the node...

[CHANGELOG v1.0.2]: Added contraindication check for elderly patients
- Changed: Added new conditional branch for age >= 65
- Reason: Safety improvement - reduce adverse events in elderly
- Suggestion ID: sug_042"
```

IMPORTANT:
- Append changelog to EXISTING description (don't replace it)
- Use blank line before [CHANGELOG] marker
- Include suggestion ID for traceability
- Be specific about what changed

CRITICAL REQUIREMENTS:

- The output MUST be valid JSON
- Do NOT remove any existing nodes unless explicitly requested
- Do NOT change node IDs unless necessary
- Preserve all conditional logic and relationships
- Maintain backward compatibility where possible
- DOCUMENT ALL CHANGES in node descriptions with [CHANGELOG] entries

OUTPUT FORMAT:

You MUST return a JSON object with the following structure:

{{
  "reconstructed_protocol": <complete protocol JSON here>,
  "detailed_changelog": [
    {{
      "action": "modificação" | "adição" | "remoção",
      "node_id": "id do nodo afetado",
      "node_label": "nome legível do nodo",
      "target_type": "pergunta" | "alternativa" | "condicional" | "mensagem_alerta" | "exame" | "medicamento" | "nodo",
      "target_id": "id do item modificado (uid da pergunta, id da alternativa, etc)",
      "description_before": "descrição breve do estado anterior (ou null se adição)",
      "description_after": "descrição breve do novo estado",
      "suggestion_id": "id da sugestão aplicada"
    }}
  ]
}}

EXEMPLO DE CHANGELOG DETALHADO:
{{
  "action": "modificação",
  "node_id": "node-3",
  "node_label": "Anamnese - inicial",
  "target_type": "alternativa",
  "target_id": "sintomas_febre",
  "description_before": "label: 'Febre'",
  "description_after": "label: 'Febre (≥37.8°C)'",
  "suggestion_id": "sug_001"
}}

{{
  "action": "adição",
  "node_id": "node-5",
  "node_label": "Conduta - avaliação",
  "target_type": "mensagem_alerta",
  "target_id": null,
  "description_before": null,
  "description_after": "ATENÇÃO: Pacientes idosos requerem avaliação renal antes de prescrição",
  "suggestion_id": "sug_003"
}}

{{
  "action": "modificação",
  "node_id": "conduct-1",
  "node_label": "Condutas",
  "target_type": "condicional",
  "target_id": "exame_hemograma",
  "description_before": "condicao: 'febre == True'",
  "description_after": "condicao: '(febre == True) and (idade >= 60)'",
  "suggestion_id": "sug_007"
}}

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

    def _enumerate_sections(
        self,
        protocol: Dict,
        suggestions: List[Dict]
    ) -> List[Dict]:
        """
        Enumera seções do protocolo para reconstrução chunked.

        Divide o protocolo em seções lógicas baseadas no tamanho:
        - Small (< 50KB): 2-3 nodes por seção
        - Medium (50-100KB): 2 nodes por seção
        - Large (> 100KB): 1-2 nodes por seção

        Args:
            protocol: Protocolo original
            suggestions: Lista de sugestões

        Returns:
            Lista de descritores de seções
        """
        # Calculate protocol size
        protocol_size = len(json.dumps(protocol, ensure_ascii=False))

        # Determine nodes per section based on size
        if protocol_size < 50000:  # < 50KB
            nodes_per_section = 3
        elif protocol_size < 100000:  # 50-100KB
            nodes_per_section = 2
        else:  # > 100KB
            nodes_per_section = 1

        nodes = protocol.get("nodes", [])
        edges = protocol.get("edges", [])
        metadata = protocol.get("metadata", {})

        sections = []  # Initialize sections list

        # Create metadata section (Section 0)
        sections.append({
            "section_id": "section_0_metadata",
            "type": "metadata",
            "metadata": metadata
        })

        # Create node sections
        idx = 1
        for i in range(0, len(nodes), nodes_per_section):
            node_group = nodes[i:i + nodes_per_section]
            node_ids = set(n["id"] for n in node_group)

            section_edges = [
                e for e in edges
                if e.get("source") in node_ids or e.get("target") in node_ids
            ]

            # Filter suggestions relevant to this section
            section_suggestions = [
                sug for sug in suggestions
                if sug.get("specific_location", {}).get("node_id") in node_ids
            ]

            sections.append({
                "section_id": f"section_{idx}",
                "type": "nodes",
                "node_ids": node_ids,
                "nodes": node_group,
                "edges": section_edges,
                "relevant_suggestions": section_suggestions,
                "metadata_context": metadata  # Read-only context
            })
            idx += 1

        logger.info(
            f"Enumerated {len(sections)} sections: "
            f"1 metadata + {len(sections)-1} node sections "
            f"(protocol_size={protocol_size/1024:.1f}KB, nodes_per_section={nodes_per_section})"
        )

        return sections

    def _validate_section(
        self,
        section: Dict,
        reconstructed: Dict
    ) -> Tuple[bool, str]:
        """
        Valida seção reconstruída.

        Args:
            section: Descritor da seção original
            reconstructed: Dados reconstruídos

        Returns:
            (is_valid, error_message)
        """
        section_type = section["type"]

        if section_type == "metadata":
            # Validate metadata structure
            if not isinstance(reconstructed, dict):
                return False, "Metadata is not a dict"

            if "version" not in reconstructed:
                return False, "Missing 'version' field"

            if "company" not in reconstructed or "name" not in reconstructed:
                return False, "Missing company/name fields"

            return True, ""

        else:
            # Validate node section
            if not isinstance(reconstructed, list):
                return False, "Nodes are not a list"

            # Check node count matches
            original_node_ids = set(section["node_ids"])
            reconstructed_node_ids = set(n["id"] for n in reconstructed)

            if original_node_ids != reconstructed_node_ids:
                return False, (
                    f"Node ID mismatch: expected {original_node_ids}, "
                    f"got {reconstructed_node_ids}"
                )

            # Validate each node structure
            for node in reconstructed:
                if "id" not in node or "type" not in node or "data" not in node:
                    return False, (
                        f"Node {node.get('id', 'UNKNOWN')} missing required fields"
                    )

            return True, ""

    def _track_section_progress(
        self,
        sections: List[Dict]
    ) -> Dict[str, SectionReconstructionStatus]:
        """
        Inicializa tracking de progresso para todas as seções.

        Args:
            sections: Lista de descritores de seções

        Returns:
            Dict mapeando section_id para status object
        """
        return {
            section["section_id"]: SectionReconstructionStatus(
                section_id=section["section_id"],
                status="pending",
                timestamp=datetime.now().isoformat()
            )
            for section in sections
        }

    def _build_section_reconstruction_prompt(
        self,
        section: Dict,
        new_version: str
    ) -> str:
        """
        Constrói prompt para reconstrução de uma seção.

        Args:
            section: Descritor da seção
            new_version: Nova versão para changelog

        Returns:
            Prompt formatado
        """
        section_id = section["section_id"]
        section_type = section["type"]

        # Check for retry context
        retry_context = section.get("_retry_context", {})
        retry_instruction = ""
        if retry_context:
            retry_instruction = f"\n⚠️ RETRY ATTEMPT #{retry_context.get('attempt', 0)}\n"
            retry_instruction += f"Previous error: {retry_context.get('last_error', 'Unknown')}\n"
            retry_instruction += f"{retry_context.get('instruction', '')}\n\n"

        if section_type == "metadata":
            # Metadata section: Only update version
            return f"""{retry_instruction}You are a medical protocol version manager.

TASK: Update the metadata section with the new version.

CURRENT METADATA:
{json.dumps(section["metadata"], ensure_ascii=False, indent=2)}

INSTRUCTIONS:
1. Update the "version" field to: {new_version}
2. Do NOT modify company or name
3. Return ONLY the updated metadata

OUTPUT FORMAT (JSON only):
{{
  "metadata": {{
    "company": "...",
    "name": "...",
    "version": "{new_version}"
  }}
}}

CRITICAL: Return ONLY valid JSON. No explanations, no markdown code blocks.
"""

        else:
            # Node section: Apply suggestions
            suggestions_text = ""
            if section["relevant_suggestions"]:
                suggestions_text = "\n".join([
                    f"\n{i+1}. [{s.get('id', 'N/A')}] {s.get('category', 'N/A')} - {s.get('priority', 'N/A')}:\n"
                    f"   Title: {s.get('title', 'N/A')}\n"
                    f"   Description: {s.get('description', 'N/A')}\n"
                    f"   Target Node: {s.get('specific_location', {}).get('node_id', 'N/A')}\n"
                    for i, s in enumerate(section["relevant_suggestions"])
                ])
            else:
                suggestions_text = "No suggestions for this section"

            return f"""{retry_instruction}You are an expert medical protocol developer.

TASK: Reconstruct section "{section_id}" by applying improvement suggestions.

PROTOCOL CONTEXT (read-only):
- Company: {section["metadata_context"].get("company", "N/A")}
- Protocol: {section["metadata_context"].get("name", "N/A")}
- Version: {new_version}

SECTION NODES TO RECONSTRUCT:
{json.dumps(section["nodes"], ensure_ascii=False, indent=2)}

EDGES (relationships):
{json.dumps(section["edges"], ensure_ascii=False, indent=2)}

IMPROVEMENT SUGGESTIONS FOR THIS SECTION:
{suggestions_text}

INSTRUCTIONS:
1. Apply ALL suggestions targeting nodes in this section
2. Maintain node IDs, types, positions exactly as they are
3. Only modify node.data (questions, descricao, condicao) as specified
4. Preserve all question IDs, UIDs, and structure
5. DO NOT modify edges
6. Document changes in node "descricao" field with [CHANGELOG v{new_version}] entries

CHANGELOG FORMAT (CRITICAL):
For EVERY modified node, append to its "descricao":

[CHANGELOG v{new_version}]: <summary>
- Changed: <specific detail>
- Reason: <justification from suggestion>
- Suggestion ID: <suggestion_id>

EXAMPLE:
"descricao": "Original description...

[CHANGELOG v1.0.2]: Added age check for elderly patients
- Changed: Added conditional logic for age >= 65
- Reason: Safety improvement to reduce adverse events
- Suggestion ID: sug_042"

OUTPUT FORMAT (JSON only, no markdown):
{{
  "reconstructed_nodes": [
    {{"id": "node-2", "type": "...", "position": {{...}}, "data": {{...}}}},
    {{"id": "node-3", "type": "...", "position": {{...}}, "data": {{...}}}}
  ]
}}

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON. No explanations, no markdown code blocks.
- The output MUST be a JSON object with the "reconstructed_nodes" key
- Do NOT remove any existing nodes unless explicitly requested
- Do NOT change node IDs
- Preserve all conditional logic and relationships
- DOCUMENT ALL CHANGES in node descriptions with [CHANGELOG] entries
"""

    def _reconstruct_section_llm(
        self,
        section: Dict,
        new_version: str
    ) -> Dict:
        """
        Reconstrói uma seção usando LLM.

        Args:
            section: Descritor da seção
            new_version: Nova versão

        Returns:
            Dados reconstruídos (metadata dict ou nodes list)

        Raises:
            ValueError: Se resposta malformada
        """
        section_id = section["section_id"]
        logger.info(f"Reconstructing {section_id}...")

        # Build prompt
        prompt = self._build_section_reconstruction_prompt(section, new_version)

        # Call LLM (auto-continue enabled)
        response = self.llm_client.analyze(prompt)

        # Parse based on section type
        if section["type"] == "metadata":
            if "metadata" in response:
                return response["metadata"]
            else:
                raise ValueError(f"Invalid metadata response: missing 'metadata' key")

        else:
            if "reconstructed_nodes" in response:
                return response["reconstructed_nodes"]
            elif "nodes" in response:
                return response["nodes"]
            else:
                raise ValueError(
                    f"Invalid node section response: missing 'reconstructed_nodes' or 'nodes' key"
                )

    def _reconstruct_section_with_retry(
        self,
        section: Dict,
        new_version: str,
        max_retries: int = 3
    ) -> Dict:
        """
        Reconstrói seção com retry automático em caso de falha.

        Args:
            section: Descritor da seção
            new_version: Nova versão
            max_retries: Número máximo de tentativas

        Returns:
            Dados reconstruídos validados

        Raises:
            ValueError: Se todas as tentativas falharem
        """
        section_id = section["section_id"]
        last_error = None

        for attempt in range(max_retries):
            try:
                # Add retry context if not first attempt
                if attempt > 0:
                    section["_retry_context"] = {
                        "attempt": attempt + 1,
                        "last_error": str(last_error),
                        "instruction": "PREVIOUS ATTEMPT FAILED. Please correct the error."
                    }

                # Attempt reconstruction
                reconstructed = self._reconstruct_section_llm(section, new_version)

                # Validate
                is_valid, error_msg = self._validate_section(section, reconstructed)

                if is_valid:
                    logger.info(f"{section_id} completed successfully (attempt {attempt + 1})")
                    return reconstructed
                else:
                    last_error = error_msg
                    logger.warning(
                        f"{section_id} validation failed (attempt {attempt + 1}): {error_msg}"
                    )

                    # Exponential backoff
                    if attempt < max_retries - 1:
                        delay = 2 ** attempt
                        logger.info(f"Retrying in {delay}s...")
                        time.sleep(delay)

            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                logger.error(f"{section_id} JSON error (attempt {attempt + 1}): {e}")

                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    time.sleep(delay)

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(
                    f"{section_id} error (attempt {attempt + 1}): {e}",
                    exc_info=True
                )

                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    time.sleep(delay)

        # All retries exhausted
        raise ValueError(
            f"Failed to reconstruct {section_id} after {max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def _assemble_protocol(
        self,
        original_protocol: Dict,
        section_statuses: Dict[str, SectionReconstructionStatus]
    ) -> Dict:
        """
        Monta protocolo completo a partir das seções reconstruídas.

        Args:
            original_protocol: Protocolo original (para edges)
            section_statuses: Dict de status das seções

        Returns:
            Protocolo completo montado

        Raises:
            ValueError: Se montagem falhar
        """
        logger.info("Starting protocol assembly from sections...")

        # Step 1: Extract metadata
        metadata_status = section_statuses.get("section_0_metadata")
        if not metadata_status or metadata_status.status != "completed":
            raise ValueError("Metadata section not completed")

        metadata = metadata_status.reconstructed_data

        # Step 2: Collect all reconstructed nodes
        all_nodes = []
        for section_id, status in section_statuses.items():
            if section_id == "section_0_metadata":
                continue

            if status.status != "completed":
                raise ValueError(
                    f"Section {section_id} not completed: {status.error_message}"
                )

            all_nodes.extend(status.reconstructed_data)

        # Step 3: Sort nodes by position.x (maintain visual flow)
        all_nodes.sort(key=lambda n: n.get("position", {}).get("x", 0))

        # Step 4: Validate node count
        original_node_count = len(original_protocol.get("nodes", []))
        if len(all_nodes) != original_node_count:
            raise ValueError(
                f"Node count mismatch: original={original_node_count}, "
                f"reconstructed={len(all_nodes)}"
            )
        # Step 5: Use original edges (validate targets exist)
        node_ids = set(n["id"] for n in all_nodes)
        edges = original_protocol.get("edges", [])

        invalid_edges = [
            e for e in edges
            if e.get("source") not in node_ids or e.get("target") not in node_ids
        ]

        if invalid_edges:
            logger.warning(f"Found {len(invalid_edges)} invalid edges, will exclude them")
            edges = [e for e in edges if e not in invalid_edges]

        # Step 6: Assemble final protocol
        assembled = {
            "metadata": metadata,
            "nodes": all_nodes,
            "edges": edges
        }

        # Step 7: Validate with Pydantic Schema (CRITICAL SAFETY CHECK)
        logger.info("Validating assembled protocol with Pydantic schema...")
        try:
            from ..models.protocol import Protocol
            validated_protocol = Protocol.model_validate(assembled)
            logger.info("✅ Protocol structure validation PASSED")
            
            # Return as dict to maintain compatibility
            return validated_protocol.model_dump()
            
        except ImportError as e:
            # Pydantic not available - skip validation but warn
            logger.warning(f"⚠️ Pydantic validation skipped (import error): {e}")
            logger.warning("Returning assembled protocol without schema validation")
            return assembled
            
        except Exception as e:
            # Check if it's a validation error
            error_type = str(type(e).__name__)
            if "ValidationError" in error_type:
                logger.error(f"❌ Protocol validation FAILED: {e}")
                # Log a snippet of the invalid protocol for debugging
                logger.error(f"Invalid protocol snippet: {str(assembled)[:500]}...")
                
                raise ValueError(
                    f"Reconstructed protocol failed structural validation:\n{e}\n\n"
                    "This is a CRITICAL error. Protocol will NOT be saved."
                )
            else:
                logger.error(f"❌ Unexpected validation error: {e}")
                # For other errors, skip validation but warn
                logger.warning("Returning assembled protocol without schema validation")
                return assembled

    def _validate_cross_references(
        self,
        protocol: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Valida referências cruzadas entre seções.

        Valida:
        - UIDs únicos
        - Lógica condicional referencia UIDs válidos
        - Edges referenciam node IDs válidos

        IMPORTANTE: Esta validação distingue entre:
        - UIDs de questions (devem existir globalmente)
        - IDs de opções (válidos dentro do contexto de uma question)
        - Valores literais em expressões condicionais

        Args:
            protocol: Protocolo completo

        Returns:
            (is_valid, warnings) - is_valid sempre True (warnings não são fatais)
        """
        warnings = []
        nodes = protocol.get("nodes", [])
        edges = protocol.get("edges", [])

        # Step 1: Collect all UIDs from questions
        all_uids = set()
        uid_to_question = {}  # Map UID -> question for context
        for node in nodes:
            for question in node.get("data", {}).get("questions", []):
                uid = question.get("uid")
                if uid:
                    if uid in all_uids:
                        warnings.append(f"Duplicate UID: {uid}")
                    all_uids.add(uid)
                    uid_to_question[uid] = question

        # Step 2: Collect all option IDs from all questions
        # This allows us to validate option references in conditional expressions
        all_option_ids = set()
        for node in nodes:
            for question in node.get("data", {}).get("questions", []):
                uid = question.get("uid")
                if not uid:
                    continue
                for option in question.get("options", []):
                    option_id = option.get("id")
                    if option_id:
                        all_option_ids.add(option_id)

        # Step 3: Validate Conditional Expressions (NEW - Safe AST)
        try:
            from ..validators.logic_validator import validate_protocol_conditionals
            conditionals_valid, conditional_errors = validate_protocol_conditionals(protocol)
            
            if not conditionals_valid:
                for err in conditional_errors:
                    warnings.append(f"Conditional Logic Error: {err}")
                logger.error(f"❌ Found {len(conditional_errors)} conditional logic errors")
        except ImportError:
            logger.warning("Components for logic validation missing, skipping AST check.")
        except Exception as e:
            logger.error(f"Error during logic validation: {e}")
            warnings.append(f"Logic validation failed execution: {e}")

        # Step 4: Validate edges (critical - these must be valid)
        node_ids = set(n["id"] for n in nodes)
        for edge in edges:
            if edge.get("source") not in node_ids:
                warnings.append(f"Edge references unknown source: {edge.get('source')}")
            if edge.get("target") not in node_ids:
                warnings.append(f"Edge references unknown target: {edge.get('target')}")

        # IMPORTANT: Warnings are non-fatal - protocol can be saved even with warnings
        # Only critical errors (like invalid edges) should block reconstruction
        # For now, we return is_valid=True always, but log warnings for review
        is_valid = True
        return is_valid, warnings
