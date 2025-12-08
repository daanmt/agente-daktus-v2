"""
Rules Engine - Hard constraints that BLOCK invalid suggestions.

Wave 2 Implementation - TASK 2.1

Unlike memory_qa.md (soft guidance), these rules ENFORCE blocking of suggestions
that don't meet quality standards. Rules are derived from:
1. Domain knowledge (default rules)
2. User feedback patterns (learned rules)

A suggestion must pass ALL rules to be included in the report.
"""

import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Set, Dict, Callable, Optional, Any
from enum import Enum
from pathlib import Path

from ..core.logger import logger


class RuleType(Enum):
    """Types of rules the engine can enforce."""
    BLOCK_CATEGORY = "block_category"      # Block entire category (e.g., "economia")
    BLOCK_KEYWORD = "block_keyword"        # Block if contains keyword
    REQUIRE_FIELD = "require_field"        # Require specific field present
    REQUIRE_SPECIFICITY = "require_specificity"  # Reference must be specific
    REQUIRE_IMPLEMENTATION = "require_implementation"  # Must have implementation_strategy
    CUSTOM = "custom"                      # Custom validation function


@dataclass
class HardRule:
    """
    A rule that BLOCKS suggestions when violated.
    
    Unlike soft filters in memory_qa, these are ENFORCED.
    A violation means the suggestion is removed from the report.
    """
    rule_id: str
    rule_type: RuleType
    description: str
    error_message: str
    learned_from: str  # Source: "domain_knowledge" or "feedback_session_YYYY-MM-DD"
    enabled: bool = True
    
    # For keyword/category rules
    keywords: List[str] = field(default_factory=list)
    blocked_categories: List[str] = field(default_factory=list)
    
    # For require_field rules
    required_field: Optional[str] = None
    min_field_length: int = 0
    
    def check(self, suggestion: Dict) -> bool:
        """
        Check if suggestion passes this rule.
        
        Returns:
            True if suggestion is VALID (passes rule)
            False if suggestion is BLOCKED (violates rule)
        """
        if not self.enabled:
            return True  # Disabled rules always pass
        
        if self.rule_type == RuleType.BLOCK_CATEGORY:
            return self._check_category(suggestion)
        elif self.rule_type == RuleType.BLOCK_KEYWORD:
            return self._check_keywords(suggestion)
        elif self.rule_type == RuleType.REQUIRE_FIELD:
            return self._check_required_field(suggestion)
        elif self.rule_type == RuleType.REQUIRE_SPECIFICITY:
            return self._check_specificity(suggestion)
        elif self.rule_type == RuleType.REQUIRE_IMPLEMENTATION:
            return self._check_implementation_strategy(suggestion)
        else:
            return True  # Unknown rule type passes
    
    def _check_category(self, suggestion: Dict) -> bool:
        """Block if category is in blocked list."""
        category = suggestion.get('category', '')
        return category not in self.blocked_categories
    
    def _check_keywords(self, suggestion: Dict) -> bool:
        """Block if any keyword found in title/description."""
        title = suggestion.get('title', '').lower()
        desc = suggestion.get('description', '').lower()
        text = f"{title} {desc}"
        
        for keyword in self.keywords:
            if keyword.lower() in text:
                return False  # Keyword found = BLOCKED
        return True
    
    def _check_required_field(self, suggestion: Dict) -> bool:
        """Require specific field with minimum length."""
        if not self.required_field:
            return True
        
        value = suggestion.get(self.required_field, '')
        if isinstance(value, dict):
            value = json.dumps(value)
        
        return len(str(value)) >= self.min_field_length
    
    def _check_specificity(self, suggestion: Dict) -> bool:
        """Check that playbook_reference is specific, not generic."""
        ref = suggestion.get('playbook_reference', '').lower()
        
        # Generic phrases that indicate hallucination
        generic_phrases = [
            "based on medical best practices",
            "according to clinical guidelines",
            "standard practice in medicine",
            "commonly accepted",
            "medical literature suggests",
            "evidências científicas",
            "prática clínica comum",
            "diretrizes médicas",
            "consenso médico",
            "boas práticas médicas",
            "de acordo com evidências",
            "segundo a literatura"
        ]
        
        for phrase in generic_phrases:
            if phrase in ref:
                return False  # Generic reference = BLOCKED
        
        # Also check minimum length
        if len(ref.strip()) < 30:
            return False  # Too short = BLOCKED
        
        return True
    
    def _check_implementation_strategy(self, suggestion: Dict) -> bool:
        """
        Check that suggestion has valid implementation_strategy.
        
        Wave 2 requirement: Every actionable suggestion must explain HOW.
        """
        impl = suggestion.get('implementation_strategy')
        
        # If no implementation_strategy at all
        if not impl:
            return False
        
        # If it's a dict, check required fields
        if isinstance(impl, dict):
            target_field = impl.get('target_field', '')
            modification_type = impl.get('modification_type', '')
            instructions = impl.get('instructions', '')
            
            # All three required fields must be present and non-empty
            if not target_field or len(target_field) < 3:
                return False
            
            if modification_type not in ['add', 'update', 'remove', 'conditional']:
                return False
            
            if not instructions or len(instructions) < 30:
                return False
            
            return True
        
        # If it's a string (fallback), must be substantial
        if isinstance(impl, str):
            return len(impl) >= 50
        
        return False
    
    def to_dict(self) -> Dict:
        """Serialize rule to dict for persistence."""
        return {
            'rule_id': self.rule_id,
            'rule_type': self.rule_type.value,
            'description': self.description,
            'error_message': self.error_message,
            'learned_from': self.learned_from,
            'enabled': self.enabled,
            'keywords': self.keywords,
            'blocked_categories': self.blocked_categories,
            'required_field': self.required_field,
            'min_field_length': self.min_field_length
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HardRule':
        """Deserialize rule from dict."""
        return cls(
            rule_id=data['rule_id'],
            rule_type=RuleType(data['rule_type']),
            description=data['description'],
            error_message=data['error_message'],
            learned_from=data['learned_from'],
            enabled=data.get('enabled', True),
            keywords=data.get('keywords', []),
            blocked_categories=data.get('blocked_categories', []),
            required_field=data.get('required_field'),
            min_field_length=data.get('min_field_length', 0)
        )


class RulesEngine:
    """
    Engine that enforces hard rules on suggestions.
    
    Usage:
        engine = RulesEngine()
        valid_suggestions = engine.validate_batch(raw_suggestions)
        # valid_suggestions contains only those that passed ALL rules
    
    Rules are:
    1. Loaded from persisted rules file
    2. Default rules added if no persisted rules
    3. New rules can be added (and persisted) from feedback
    """
    
    def __init__(self, rules_file: Optional[Path] = None):
        """
        Initialize rules engine.
        
        Args:
            rules_file: Path to JSON file storing rules. Defaults to project root.
        """
        if rules_file is None:
            # Default to project root
            rules_file = Path(__file__).parent.parent.parent.parent / "rules_engine_config.json"
        
        self.rules_file = rules_file
        self.rules: List[HardRule] = []
        
        self._load_rules()
        
        # If no rules loaded, add defaults
        if not self.rules:
            self._add_default_rules()
            self._persist_rules()
        
        logger.info(f"RulesEngine initialized with {len(self.rules)} rules")
    
    def add_rule(self, rule: HardRule):
        """Add new rule and persist."""
        self.rules.append(rule)
        self._persist_rules()
        logger.info(f"Added new rule: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str):
        """Remove rule by ID."""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        self._persist_rules()
        logger.info(f"Removed rule: {rule_id}")
    
    def disable_rule(self, rule_id: str):
        """Disable rule without removing."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                break
        self._persist_rules()
        logger.info(f"Disabled rule: {rule_id}")
    
    def enable_rule(self, rule_id: str):
        """Re-enable previously disabled rule."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                break
        self._persist_rules()
        logger.info(f"Enabled rule: {rule_id}")
    
    def validate_suggestion(self, suggestion: Dict) -> tuple:
        """
        Validate single suggestion against all rules.
        
        Returns:
            (is_valid, violations) where violations is list of error messages
        """
        violations = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if not rule.check(suggestion):
                violations.append(f"[{rule.rule_id}] {rule.error_message}")
        
        return len(violations) == 0, violations
    
    def validate_batch(self, suggestions: List[Dict]) -> List[Dict]:
        """
        Filter list of suggestions, removing those that fail rules.
        
        Returns:
            List of valid suggestions only
        """
        valid_suggestions = []
        blocked_count = 0
        
        for sug in suggestions:
            is_valid, violations = self.validate_suggestion(sug)
            
            if is_valid:
                valid_suggestions.append(sug)
            else:
                blocked_count += 1
                sug_id = sug.get('id', 'unknown')
                logger.warning(
                    f"❌ Suggestion {sug_id} BLOCKED by rules engine:\n" +
                    "\n".join(f"   - {v}" for v in violations[:3])
                )
        
        if blocked_count > 0:
            logger.info(
                f"🛡️ Rules engine: {len(suggestions)} → {len(valid_suggestions)} "
                f"({blocked_count} blocked)"
            )
        
        return valid_suggestions
    
    def get_rules_summary(self) -> str:
        """Get human-readable summary of active rules."""
        lines = ["Active Rules:"]
        for rule in self.rules:
            status = "✓" if rule.enabled else "✗"
            lines.append(f"  {status} [{rule.rule_id}] {rule.description}")
        return "\n".join(lines)
    
    def _load_rules(self):
        """Load rules from persisted file."""
        if not self.rules_file.exists():
            return
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.rules = [HardRule.from_dict(r) for r in data.get('rules', [])]
            logger.debug(f"Loaded {len(self.rules)} rules from {self.rules_file}")
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
    
    def _persist_rules(self):
        """Save rules to file."""
        try:
            data = {
                'version': '1.0',
                'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'rules': [r.to_dict() for r in self.rules]
            }
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Persisted {len(self.rules)} rules to {self.rules_file}")
        except Exception as e:
            logger.error(f"Failed to persist rules: {e}")
    
    def _add_default_rules(self):
        """Add default domain knowledge rules."""
        
        # Rule 1: Require specific playbook reference
        self.rules.append(HardRule(
            rule_id="req_specific_reference",
            rule_type=RuleType.REQUIRE_SPECIFICITY,
            description="Referência do playbook deve ser específica, não genérica",
            error_message="Playbook reference is too generic or too short (min 30 chars, no generic phrases)",
            learned_from="domain_knowledge"
        ))
        
        # Rule 2: Block suggestions about "alerts" without specifying field
        self.rules.append(HardRule(
            rule_id="alert_requires_field",
            rule_type=RuleType.BLOCK_KEYWORD,
            description="Sugestões sobre 'alertas' que não especificam campo são bloqueadas",
            error_message="Alert suggestion blocked: must mention 'mensagem_alerta' or specific field in description",
            learned_from="domain_knowledge",
            keywords=["alerta genérico", "generic alert", "adicionar alerta simples"]
        ))
        
        # Rule 3: Block suggestions that suggest structural changes
        self.rules.append(HardRule(
            rule_id="no_structural_changes",
            rule_type=RuleType.BLOCK_KEYWORD,
            description="Bloqueia sugestões de mudanças estruturais (tooltips, funcionalidade do sistema)",
            error_message="Structural change suggestion blocked: cannot modify system functionality",
            learned_from="domain_knowledge",
            keywords=["adicionar tooltip", "implementar funcionalidade", "mudar interface", "sistema deve"]
        ))
        
        # Rule 4: Block suggestions that invade medical autonomy
        self.rules.append(HardRule(
            rule_id="no_autonomy_invasion",
            rule_type=RuleType.BLOCK_KEYWORD,
            description="Bloqueia sugestões que invadem autonomia médica",
            error_message="Suggestion blocked: invades medical professional autonomy",
            learned_from="domain_knowledge",
            keywords=["médico deve sempre", "obrigar prescrição", "forçar conduta", "impedir escolha"]
        ))
        
        # Rule 5: Require implementation_strategy (Wave 2)
        # NOTE: Disabled by default initially to allow transition period
        # Enable once LLM is consistently generating implementation_strategy
        self.rules.append(HardRule(
            rule_id="req_implementation_strategy",
            rule_type=RuleType.REQUIRE_IMPLEMENTATION,
            description="Sugestões devem ter implementation_strategy específica",
            error_message="Missing or invalid implementation_strategy (must have target_field, modification_type, instructions >= 30 chars)",
            learned_from="wave2_domain_knowledge",
            enabled=False  # Start disabled, enable after testing
        ))
        
        # Rule 6: Spider/Daktus-specific - Block UI/system change suggestions
        # Based on Spider Playbook: suggestions must target modifiable protocol fields only
        self.rules.append(HardRule(
            rule_id="spider_no_ui_changes",
            rule_type=RuleType.BLOCK_KEYWORD,
            description="Bloqueia sugestões de mudanças de UI/sistema (Spider não suporta)",
            error_message="Suggestion targets UI/system features not configurable in Spider protocol JSON",
            learned_from="spider_playbook",
            keywords=[
                "criar nova tela", "adicionar botão", "mudar layout", "redesenhar",
                "nova funcionalidade", "implementar feature", "criar módulo",
                "interface do usuário", "user interface", "frontend", "backend"
            ]
        ))
        
        # Rule 7: Spider-specific - Block suggestions about flow/node creation
        # Based on Spider Playbook: agent should not suggest structural changes
        self.rules.append(HardRule(
            rule_id="spider_no_flow_changes",
            rule_type=RuleType.BLOCK_KEYWORD,
            description="Bloqueia sugestões de alteração de fluxo/criação de nodos (mudança estrutural)",
            error_message="Suggestion requires flow/node changes - outside automated reconstruction scope",
            learned_from="spider_playbook",
            keywords=[
                "criar novo nodo", "adicionar nodo", "remover nodo",
                "mudar fluxo", "reorganizar fluxo", "nova etapa",
                "break point", "dividir nodo", "unir nodos"
            ]
        ))
        
        logger.info(f"Added {len(self.rules)} default rules")


def create_rule_from_feedback(
    rejected_suggestions: List[Dict],
    pattern_name: str,
    pattern_keywords: List[str]
) -> Optional[HardRule]:
    """
    Create a new rule from feedback patterns.
    
    Called by FeedbackLearner when it detects a pattern of rejections.
    
    Args:
        rejected_suggestions: List of suggestions that were rejected for similar reasons
        pattern_name: Human-readable name for the pattern
        pattern_keywords: Keywords that identify this pattern
    
    Returns:
        New HardRule or None if insufficient data
    """
    if len(rejected_suggestions) < 3:
        return None  # Need at least 3 examples
    
    rule_id = f"learned_{pattern_name.lower().replace(' ', '_')}_{int(time.time())}"
    
    return HardRule(
        rule_id=rule_id,
        rule_type=RuleType.BLOCK_KEYWORD,
        description=f"Learned from feedback: {pattern_name}",
        error_message=f"Suggestion blocked due to learned pattern: {pattern_name}",
        learned_from=f"feedback_pattern_{time.strftime('%Y-%m-%d')}",
        keywords=pattern_keywords
    )
