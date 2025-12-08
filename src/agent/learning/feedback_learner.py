"""
Feedback Learner - Converts user feedback into executable rules.

Wave 2 Implementation - TASK 2.5

Flow:
1. User rejects suggestions with comments
2. System detects patterns in rejections
3. Creates HardRule that blocks similar suggestions
4. Rule is persisted and used in future analyses

This closes the learning loop - the system actually LEARNS from feedback.
"""

import re
import hashlib
from typing import List, Dict, Optional, Tuple
from collections import Counter
from datetime import datetime

from ..core.logger import logger
from .rules_engine import RulesEngine, HardRule, RuleType


class FeedbackLearner:
    """
    Learns from user feedback to generate blocking rules.
    
    Detection Methods:
    1. Keyword frequency - Common words in rejection comments
    2. Category patterns - Same category rejected multiple times
    3. Semantic patterns - Similar reasons across rejections
    """
    
    # Minimum rejections needed to learn a pattern
    MIN_REJECTIONS_FOR_PATTERN = 3
    
    # Common reason patterns and their rule mappings
    REASON_PATTERN_KEYWORDS = {
        'out_of_playbook': [
            'fora do playbook', 'não consta', 'não está no playbook',
            'outside playbook', 'not in playbook', 'hallucination'
        ],
        'autonomy_invasion': [
            'autonomia médica', 'decisão do médico', 'critério médico',
            'medical autonomy', 'doctor decision', 'professional judgment'
        ],
        'already_implemented': [
            'já existe', 'já implementado', 'já tem', 'já ocorre',
            'already exists', 'already implemented', 'already done'
        ],
        'structural_change': [
            'mudança estrutural', 'tooltip', 'funcionalidade',
            'structural change', 'functionality', 'system change'
        ],
        'low_value': [
            'baixo valor', 'não agrega', 'irrelevante', 'desnecessário',
            'low value', 'not useful', 'irrelevant', 'unnecessary'
        ],
        'too_complex': [
            'complexo demais', 'muito trabalho', 'alto esforço',
            'too complex', 'too much work', 'high effort'
        ]
    }
    
    def __init__(self):
        self.rules_engine = RulesEngine()
    
    def learn_from_rejected_suggestions(
        self,
        rejected_suggestions: List[Dict]
    ) -> List[HardRule]:
        """
        Analyze rejected suggestions and generate new rules.
        
        Args:
            rejected_suggestions: List of suggestions with rejection comments
                Each should have:
                - id: suggestion ID
                - title: suggestion title
                - description: suggestion description
                - rejection_comment: user's reason for rejection
                - category: suggestion category
        
        Returns:
            List of new HardRules created (may be empty if no patterns found)
        """
        if len(rejected_suggestions) < self.MIN_REJECTIONS_FOR_PATTERN:
            logger.debug(
                f"Not enough rejections to learn ({len(rejected_suggestions)} < {self.MIN_REJECTIONS_FOR_PATTERN})"
            )
            return []
        
        new_rules = []
        
        # Method 1: Detect reason patterns
        pattern_rules = self._detect_reason_patterns(rejected_suggestions)
        new_rules.extend(pattern_rules)
        
        # Method 2: Detect frequent keywords in rejections
        keyword_rules = self._detect_keyword_patterns(rejected_suggestions)
        new_rules.extend(keyword_rules)
        
        # Method 3: Detect category patterns
        category_rules = self._detect_category_patterns(rejected_suggestions)
        new_rules.extend(category_rules)
        
        # Add rules to engine (if not duplicates)
        added_rules = []
        existing_ids = {r.rule_id for r in self.rules_engine.rules}
        
        for rule in new_rules:
            if rule.rule_id not in existing_ids:
                self.rules_engine.add_rule(rule)
                added_rules.append(rule)
                logger.info(f"🧠 Learned new rule: {rule.rule_id} - {rule.description}")
        
        if added_rules:
            logger.info(f"✅ FeedbackLearner created {len(added_rules)} new rules from feedback")
        
        return added_rules
    
    def _detect_reason_patterns(self, rejected: List[Dict]) -> List[HardRule]:
        """Detect predefined reason patterns in rejection comments."""
        rules = []
        pattern_counts = Counter()
        
        for sug in rejected:
            comment = sug.get('rejection_comment', '').lower()
            
            for pattern_name, keywords in self.REASON_PATTERN_KEYWORDS.items():
                if any(kw in comment for kw in keywords):
                    pattern_counts[pattern_name] += 1
        
        # Create rules for patterns with >= threshold occurrences
        for pattern, count in pattern_counts.items():
            if count >= self.MIN_REJECTIONS_FOR_PATTERN:
                # Check if this pattern already has a rule
                existing_patterns = ['autonomy_invasion', 'structural_change']  # Known defaults
                if pattern not in existing_patterns:
                    rule = self._create_rule_for_pattern(pattern, count)
                    if rule:
                        rules.append(rule)
        
        return rules
    
    def _detect_keyword_patterns(self, rejected: List[Dict]) -> List[HardRule]:
        """Detect frequently occurring keywords in rejection comments."""
        rules = []
        
        # Extract all significant words from comments
        all_words = []
        for sug in rejected:
            comment = sug.get('rejection_comment', '')
            words = self._tokenize(comment)
            all_words.extend(words)
        
        # Find frequent words (appear in >= threshold rejections)
        word_counts = Counter(all_words)
        frequent_words = [
            word for word, count in word_counts.items()
            if count >= self.MIN_REJECTIONS_FOR_PATTERN and len(word) > 5
        ]
        
        if len(frequent_words) >= 2:
            # Create a rule to block suggestions mentioning these words
            rule_id = f"learned_keywords_{self._hash(frequent_words)}"
            
            rules.append(HardRule(
                rule_id=rule_id,
                rule_type=RuleType.BLOCK_KEYWORD,
                description=f"Bloqueia sugestões com palavras frequentemente rejeitadas: {', '.join(frequent_words[:3])}",
                error_message=f"Suggestion contains frequently rejected keywords",
                learned_from=f"feedback_keywords_{datetime.now().strftime('%Y-%m-%d')}",
                keywords=frequent_words[:5]  # Top 5 keywords
            ))
        
        return rules
    
    def _detect_category_patterns(self, rejected: List[Dict]) -> List[HardRule]:
        """Detect if certain categories are frequently rejected."""
        rules = []
        
        category_counts = Counter(sug.get('category', 'unknown') for sug in rejected)
        
        # If a category represents > 50% of rejections and has enough samples
        total = sum(category_counts.values())
        
        for category, count in category_counts.items():
            ratio = count / total if total > 0 else 0
            
            if ratio > 0.5 and count >= self.MIN_REJECTIONS_FOR_PATTERN * 2:
                logger.warning(
                    f"⚠️ Category '{category}' has {int(ratio*100)}% rejection rate ({count}/{total}). "
                    "Consider blocking this category."
                )
                # Don't auto-block categories, but could add as disabled rule
        
        return rules
    
    def _create_rule_for_pattern(self, pattern_name: str, occurrence_count: int) -> Optional[HardRule]:
        """Create a rule for a detected pattern."""
        
        rule_configs = {
            'out_of_playbook': {
                'description': 'Sugestões fora do playbook detectadas como padrão de rejeição',
                'error_message': 'Suggestion appears to be outside playbook scope',
                'keywords': ['fora do playbook', 'não consta no playbook']
            },
            'already_implemented': {
                'description': 'Sugestões para funcionalidades já existentes',
                'error_message': 'Suggestion refers to already implemented feature',
                'keywords': ['já existe', 'já implementado', 'já ocorre']
            },
            'low_value': {
                'description': 'Sugestões de baixo valor identificadas por feedback',
                'error_message': 'Suggestion identified as low value by user feedback',
                'keywords': ['baixo valor', 'irrelevante para', 'não agrega']
            },
            'too_complex': {
                'description': 'Sugestões muito complexas para implementar',
                'error_message': 'Suggestion too complex based on feedback',
                'keywords': ['complexidade alta', 'muito trabalho', 'alto esforço']
            }
        }
        
        config = rule_configs.get(pattern_name)
        if not config:
            return None
        
        return HardRule(
            rule_id=f"learned_{pattern_name}_{int(datetime.now().timestamp())}",
            rule_type=RuleType.BLOCK_KEYWORD,
            description=config['description'],
            error_message=config['error_message'],
            learned_from=f"feedback_pattern_{pattern_name}_{datetime.now().strftime('%Y-%m-%d')}",
            keywords=config['keywords'],
            enabled=True  # New learned rules are enabled immediately
        )
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into meaningful words."""
        # Remove punctuation and lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter stopwords and short words
        stopwords = {
            'o', 'a', 'os', 'as', 'de', 'da', 'do', 'e', 'em', 'no', 'na',
            'para', 'por', 'com', 'que', 'um', 'uma', 'se', 'é', 'ao',
            'the', 'a', 'an', 'is', 'of', 'in', 'to', 'and', 'for', 'with'
        }
        
        return [w for w in words if w not in stopwords and len(w) > 3]
    
    def _hash(self, items: List[str]) -> str:
        """Create short hash from list of items."""
        content = '|'.join(sorted(items))
        return hashlib.md5(content.encode()).hexdigest()[:8]


def learn_from_feedback_session(
    edited_report: Dict
) -> List[HardRule]:
    """
    Convenience function to learn from an edited report.
    
    Args:
        edited_report: The _EDITED.json with rejected_suggestions
    
    Returns:
        List of new rules learned
    """
    rejected = edited_report.get('rejected_suggestions', [])
    
    if not rejected:
        return []
    
    learner = FeedbackLearner()
    return learner.learn_from_rejected_suggestions(rejected)
