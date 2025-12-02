"""
Prompt Builder - Template Assembly Only (No Medical Logic)

Responsibility: Assemble the super prompt by substituting playbook and protocol
content into the template. NO medical interpretation, NO clinical logic.
"""

import json
from typing import Dict

from config.prompts.super_prompt import OUTPUT_SCHEMA_JSON

# Logger - usar logger do core
from .logger import logger


class PromptBuilder:
    """
    Builds comprehensive analysis prompts by assembling template with content.
    
    Principle: Simple template substitution only.
    All medical intelligence is in the template, not in this code.
    """
    
    def __init__(self):
        """Initialize prompt builder."""
        # Note: SUPER_PROMPT_TEMPLATE is no longer used directly
        # Prompt is now built manually to support caching
        logger.debug("PromptBuilder initialized")
    
    def build_analysis_prompt(self, playbook_content: str, protocol_json: Dict, use_cache: bool = True) -> Dict:
        """
        Build comprehensive analysis prompt for LLM with optional prompt caching.
        
        Simple template substitution - NO medical interpretation,
        NO content analysis, NO clinical logic.
        
        Args:
            playbook_content: Raw playbook text content
            protocol_json: Protocol dictionary (will be formatted as JSON)
            use_cache: If True, structure prompt for caching (playbook cacheable, protocol not)
            
        Returns:
            Dictionary with prompt structure:
            {
                "system": [{"type": "text", "text": "...", "cache_control": {...}}],
                "messages": [{"role": "user", "content": "..."}]
            }
            OR if use_cache=False:
            {
                "prompt": "complete prompt string"
            }
            
        Example:
            >>> builder = PromptBuilder()
            >>> playbook = "# Medical Guidelines..."
            >>> protocol = {"nodes": [...]}
            >>> prompt_struct = builder.build_analysis_prompt(playbook, protocol)
            >>> "system" in prompt_struct
            True
        """
        # Format protocol as pretty JSON
        # NO validation, NO medical analysis - just formatting
        try:
            protocol_formatted = json.dumps(
                protocol_json,
                indent=2,
                ensure_ascii=False,
                sort_keys=False
            )
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to format protocol JSON: {e}")
            # Fallback: convert to string representation
            protocol_formatted = str(protocol_json)
        
        # Build base instructions (always cacheable if using cache)
        base_instructions = """You are a senior medical QA specialist conducting comprehensive clinical protocol analysis.

CONTEXT: You will analyze a medical protocol (JSON decision tree) against its corresponding clinical playbook (medical guidelines document) to identify gaps, errors, and improvement opportunities.

INPUT MATERIALS:

1. CLINICAL PLAYBOOK (Medical Guidelines):

"""
        
        # Build protocol-specific instructions (not cacheable, changes per protocol)
        # Use regular string (not f-string) to allow .format() to work
        protocol_instructions_template = """
2. PROTOCOL JSON (Decision Tree):

{protocol_json}

YOUR COMPREHENSIVE ANALYSIS MUST INCLUDE:

PART 1: CLINICAL CONTENT EXTRACTION

Extract ALL clinical elements from the playbook:
- Medical syndromes/conditions mentioned
- Signs and symptoms described  
- Diagnostic exams/tests of any type (laboratory, imaging, functional, diagnostic procedures)
- Therapeutic conducts/treatments
- Medications and dosages
- Clinical indications and contraindications
- Red flags and emergency criteria
- Patient education/orientations
- Referral criteria
- Age restrictions and special population considerations
- Follow-up protocols

IMPORTANT: Extract EVERYTHING regardless of medical specialty. Do not assume specialty type. Analyze the content itself to determine what clinical elements are present.

PART 2: STRUCTURAL PROTOCOL ANALYSIS  

Analyze the protocol JSON structure:
- Validate JSON syntax and schema compliance
- Map decision tree logic and pathways
- Identify unreachable nodes or dead-end paths
- Check variable usage and conditional logic completeness
- Validate metadata completeness
- Check for circular references or infinite loops
- Identify missing required fields
- Validate question structure and answer options

PART 3: CLINICAL-PROTOCOL ALIGNMENT

Compare playbook clinical content with protocol implementation:
- Calculate coverage: What percentage of playbook concepts are implemented in the protocol?
- Identify missing clinical elements from playbook not covered by protocol
- Identify protocol elements not supported by playbook evidence
- Validate clinical indication accuracy (protocol matches playbook recommendations)
- Check implementation of safety measures (red flags, contraindications)
- Assess age restrictions and special population considerations
- Validate exam ordering logic matches playbook guidelines
- Check treatment sequences align with clinical guidelines

PART 4: QUALITY ASSESSMENT

Provide comprehensive scoring:
- Clinical coverage score (0-100%): How much of playbook is covered?
- Structural quality score (0-100%): How well-structured is the protocol?
- Safety implementation score (0-100%): Are safety measures properly implemented?
- Overall protocol quality score (0-100%): Composite quality metric
- Identify critical gaps requiring immediate attention
- Categorize issues by priority (critical/high/medium/low)
- Flag any ambiguous findings for human review

PART 5: IMPROVEMENT RECOMMENDATIONS

Generate specific, actionable recommendations:
- Missing clinical elements to add with specific examples
- Structural improvements needed with rationale
- Safety enhancements required with priority
- Question optimizations for better clinical flow
- Workflow improvements for efficiency
- Priority ranking for implementation
- Estimated impact of each recommendation

ANALYSIS REQUIREMENTS:

- Be thorough and clinically rigorous
- Use medical expertise for all clinical assessments  
- Provide specific, actionable recommendations with clinical rationale
- Include confidence scores for uncertain assessments
- Flag any ambiguous or unclear findings for human review
- Consider patient safety as highest priority
- Maintain objectivity - report what is missing, not what you wish was there
- Extract exact terminology from playbook when possible

OUTPUT FORMAT: 

Respond with ONLY valid JSON matching this exact schema:

{output_schema}

CRITICAL OUTPUT REQUIREMENTS:

- NO markdown formatting
- NO explanatory text outside JSON
- NO code blocks or markdown fences
- ONLY the JSON response
- Ensure JSON is valid and parseable
- Include all required fields from schema
"""
        
        # Format the template with both protocol_json and output_schema
        protocol_instructions = protocol_instructions_template.format(
            protocol_json=protocol_formatted,
            output_schema=OUTPUT_SCHEMA_JSON
        )
        
        if use_cache and playbook_content:
            # Structure for prompt caching: playbook in system with cache_control, protocol in messages
            prompt_structure = {
                "system": [
                    {
                        "type": "text",
                        "text": base_instructions
                    },
                    {
                        "type": "text",
                        "text": playbook_content,
                        "cache_control": {"type": "ephemeral"}  # 5-minute cache (default)
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
                f"Built cached prompt structure: playbook_size={len(playbook_content)} chars "
                f"(cacheable), protocol_size={len(protocol_formatted)} chars, "
                f"protocol_nodes={self._count_protocol_nodes(protocol_json)}"
            )
        else:
            # Fallback: single prompt string (no caching)
            full_prompt = base_instructions + playbook_content + protocol_instructions
            prompt_structure = {"prompt": full_prompt}
            
            prompt_size = len(full_prompt)
            prompt_hash = hash(full_prompt) % 1000000
            
            logger.info(
                f"Built analysis prompt: size={prompt_size} chars, "
                f"hash={prompt_hash}, playbook_size={len(playbook_content)} chars, "
                f"protocol_nodes={self._count_protocol_nodes(protocol_json)}"
            )
        
        return prompt_structure
    
    def _count_protocol_nodes(self, protocol_json: Dict) -> int:
        """
        Count protocol nodes for logging purposes only.
        
        Simple structure traversal - NO medical validation.
        """
        # Try common protocol structures
        if isinstance(protocol_json, dict):
            # Look for nodes in common locations
            if "nodes" in protocol_json:
                return len(protocol_json["nodes"]) if isinstance(protocol_json["nodes"], list) else 0
            if "protocol_tree" in protocol_json:
                tree = protocol_json["protocol_tree"]
                if isinstance(tree, dict) and "nodes" in tree:
                    return len(tree["nodes"]) if isinstance(tree["nodes"], list) else 0
            if "questions" in protocol_json:
                return len(protocol_json["questions"]) if isinstance(protocol_json["questions"], list) else 0
        
        # If structure unknown, return 0 (not an error, just unknown)
        return 0

