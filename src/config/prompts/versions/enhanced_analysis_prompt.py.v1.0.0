"""
Enhanced Analysis Prompt Template - V3 Expanded Analysis

This prompt extends V2 analysis to generate 20-50 detailed improvement suggestions
with complete traceability, impact scores, and evidence mapping.

CRITICAL: This prompt must work for ALL medical specialties without modification.

Version: 1.0.0
"""

__version__ = "1.0.0"

ENHANCED_ANALYSIS_PROMPT_TEMPLATE = """You are an expert medical protocol quality analyst conducting DEEP, COMPREHENSIVE analysis.

CONTEXT: You will analyze a medical protocol (JSON decision tree) against its corresponding clinical playbook to identify ALL possible improvements, gaps, and optimization opportunities.

INPUT MATERIALS:

1. CLINICAL PLAYBOOK (Medical Guidelines):

{playbook_content}

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

