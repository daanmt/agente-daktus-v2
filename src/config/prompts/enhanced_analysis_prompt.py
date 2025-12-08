"""
Enhanced Analysis Prompt Template - V3 Expanded Analysis

This prompt extends V2 analysis to generate 20-50 detailed improvement suggestions
with complete traceability, impact scores, and evidence mapping.

CRITICAL: This prompt must work for ALL medical specialties without modification.

Version: 1.0.0
"""

__version__ = "1.0.1"

ENHANCED_ANALYSIS_PROMPT_TEMPLATE = """You are an expert medical protocol quality analyst conducting DEEP, COMPREHENSIVE analysis.

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
{agent_memory}

INPUT MATERIALS:

1. CLINICAL PLAYBOOK (Medical Guidelines):

{playbook_content}

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
- PRIORIZE generating MEDIUM, HIGH and CRITICAL priority suggestions over LOW priority ones
- LOW priority suggestions should ONLY be included if they are truly valuable, non-redundant, and add significant value
- Focus computational resources on suggestions that have significant impact:
  * Safety score >= 7 (high/critical safety issues)
  * Medium/High efficiency or economy impact
  * Medium/High usability improvements that significantly enhance workflow
- DO NOT force low-impact suggestions just to reach a target count
- Quality over quantity: Better to generate 5-10 high-quality, high-priority suggestions than 20-30 mixed-quality suggestions with many low-impact ones
- If there are fewer than 5 high/medium priority suggestions available, generate only what is truly valuable (minimum 5, but quality is paramount)

CRITICAL REQUIREMENTS:

1. QUANTITY: Generate 5-50 suggestions, prioritizing MEDIUM/HIGH/CRITICAL priority.
   Focus on quality and impact, not quantity:
   - Safety enhancements (prioritize: safety score >= 7) - 2-8 suggestions
   - Clinical coverage gaps (prioritize: high impact) - 3-12 suggestions
   - Efficiency optimizations (prioritize: medium/high impact) - 2-8 suggestions
   - Structural improvements (prioritize: significant issues) - 2-8 suggestions
   - Usability improvements (prioritize: medium/high impact) - 1-6 suggestions
   - Workflow enhancements (prioritize: medium/high impact) - 1-5 suggestions
   
   IMPORTANT: If you cannot find enough high/medium priority suggestions, generate fewer but higher quality suggestions. Do NOT pad with low-priority suggestions.

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

6. IMPLEMENTATION PATH (IMPORTANT FOR AUTO-APPLY):
   For EACH suggestion, provide:
   - json_path: Exact JSON path (e.g., "nodes[3].data.questions[0].options")
   - modification_type: "add_option", "modify_option", "add_question", "modify_condition", "add_alert", "modify_text"
   - proposed_value: The new value to apply (as string)

7. IMPLEMENTATION EFFORT: For EACH suggestion, estimate:
   - effort: "baixo" (low), "medio" (medium), "alto" (high implementation effort)
   - estimated_time: Estimated time to implement (e.g., "30min", "2h", "1dia")
   - complexity: "simples" (simple), "moderada" (moderate), "complexa" (complex)

8. SPECIFICITY: Each suggestion must be:
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
- Generate 5-50 suggestions (minimum 5, target 15-30 high/medium priority, maximum 50)
- Prioritize MEDIUM/HIGH/CRITICAL priority suggestions
- Only include LOW priority if truly valuable and non-redundant
- Every suggestion MUST have ALL required fields
"""

ENHANCED_OUTPUT_SCHEMA_JSON = """{
    "structural_analysis": {
        "json_valid": true,
        "logic_issues": [
            {
                "node_id": "string",
                "issue": "string",
                "severity": "string",
                "description": "string"
            }
        ],
        "unreachable_nodes": ["string"],
        "dead_end_paths": [
            {
                "path": ["string"],
                "reason": "string"
            }
        ]
    },
    "clinical_extraction": {
        "syndromes": [
            {
                "name": "string",
                "description": "string",
                "symptoms": ["string"]
            }
        ],
        "exams": [
            {
                "name": "string",
                "type": "string",
                "indication": "string"
            }
        ],
        "treatments": [
            {
                "name": "string",
                "type": "string",
                "indication": "string"
            }
        ],
        "red_flags": [
            {
                "flag": "string",
                "urgency": "string",
                "action": "string"
            }
        ]
    },
    "improvement_suggestions": [
        {
            "id": "string (unique identifier, e.g., 'sug_001')",
            "category": "string (seguranca|economia|eficiencia|usabilidade)",
            "priority": "string (alta|media|baixa)",
            "title": "string (short descriptive title)",
            "description": "string (detailed description of the improvement)",
            "rationale": "string (clinical/technical justification)",
            "impact_scores": {
                "seguranca": 0,
                "economia": "string (L|M|A)",
                "eficiencia": "string (L|M|A)",
                "usabilidade": 0
            },
            "evidence": {
                "playbook_reference": "string (exact quote or section)",
                "context": "string (additional context)",
                "clinical_rationale": "string (medical justification)"
            },
            "implementation_effort": {
                "effort": "string (baixo|medio|alto)",
                "estimated_time": "string (e.g., '30min', '2h', '1dia')",
                "complexity": "string (simples|moderada|complexa)"
            },
            "specific_location": {
                "node_id": "string (if applicable)",
                "field": "string (if applicable)",
                "path": "string (JSON path if applicable)"
            },
            "implementation_path": {
                "json_path": "string (e.g., 'nodes[3].data.questions[0].options')",
                "modification_type": "string (add_option|modify_option|add_question|modify_condition|add_alert|modify_text)",
                "proposed_value": "string (the new value to apply)"
            },
            "auto_apply_cost_estimate": {
                "estimated_tokens": 0,
                "estimated_cost_usd": 0.0
            }
        }
    ],
    "quality_scores": {
        "clinical_coverage": 0.0,
        "structural_quality": 0.0,
        "safety_implementation": 0.0,
        "overall_quality": 0.0
    },
    "metadata": {
        "analysis_timestamp": "string",
        "model_used": "string",
        "suggestions_count": 0,
        "confidence_scores": {}
    }
}"""

