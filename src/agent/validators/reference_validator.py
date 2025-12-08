"""
Reference Validator - Strict verification of playbook references.

Wave 2 Implementation - TASK 2.3

Zero tolerance policy for:
- Generic/fabricated references ("based on medical best practices")
- Paraphrases that can't be verified
- References to content not in playbook

Every suggestion's playbook_reference must be VERIFIABLE.
"""

import re
from typing import Tuple, List, Dict, Set
from ..core.logger import logger


class ReferenceValidator:
    """
    Validates playbook references with fuzzy matching.
    
    A reference is valid if:
    1. Not generic (doesn't contain blacklisted phrases)
    2. Minimum length (30+ chars)
    3. Actually exists in playbook (fuzzy match)
    """
    
    # Generic phrases that indicate hallucination - immediate block
    GENERIC_BLACKLIST = [
        # English
        "based on medical best practices",
        "according to clinical guidelines",
        "standard practice in medicine",
        "commonly accepted in healthcare",
        "medical literature suggests",
        "evidence-based medicine recommends",
        "as per standard protocols",
        "following best practices",
        # Portuguese
        "baseado em boas práticas médicas",
        "de acordo com diretrizes clínicas",
        "prática padrão na medicina",
        "comumente aceito",
        "literatura médica sugere",
        "evidências científicas indicam",
        "conforme protocolos padrão",
        "seguindo melhores práticas",
        "segundo a literatura",
        "práticas médicas recomendadas",
        "consenso médico indica",
        "de acordo com evidências",
        "conforme recomendações gerais"
    ]
    
    # Minimum lengths
    MIN_REFERENCE_LENGTH = 30
    MIN_MATCH_WORDS = 3  # At least 3 words must match
    
    # Stopwords to ignore in matching
    STOPWORDS = {
        'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos',
        'e', 'em', 'no', 'na', 'nos', 'nas', 'para', 'por',
        'com', 'que', 'um', 'uma', 'uns', 'umas', 'se', 'é',
        'ao', 'aos', 'às', 'à', 'ou', 'como', 'mais', 'muito',
        'the', 'a', 'an', 'is', 'are', 'of', 'in', 'to', 'and',
        'for', 'with', 'on', 'at', 'by', 'from', 'or', 'as'
    }
    
    def __init__(self, playbook_content: str):
        """
        Initialize with playbook content.
        
        Args:
            playbook_content: Full text of the playbook
        """
        self.playbook_content = playbook_content
        self.playbook_lower = playbook_content.lower()
        
        # Pre-process playbook into sentences and word sets
        self.playbook_sentences = self._split_into_sentences(playbook_content)
        self.playbook_words = self._tokenize(playbook_content)
        
        logger.debug(f"ReferenceValidator initialized with {len(self.playbook_sentences)} sentences")
    
    def validate_reference(
        self, 
        reference: str, 
        suggestion_title: str = ""
    ) -> Tuple[bool, str]:
        """
        Validate a single playbook reference.
        
        Args:
            reference: The playbook_reference string from suggestion
            suggestion_title: Title of suggestion (for logging)
        
        Returns:
            (is_valid, reason) - reason explains why invalid if is_valid=False
        """
        if not reference:
            return False, "Empty reference"
        
        reference = reference.strip()
        
        # Check 1: Not too short
        if len(reference) < self.MIN_REFERENCE_LENGTH:
            return False, f"Reference too short ({len(reference)} chars, min {self.MIN_REFERENCE_LENGTH})"
        
        # Check 2: Not generic (blacklist check)
        ref_lower = reference.lower()
        for phrase in self.GENERIC_BLACKLIST:
            if phrase in ref_lower:
                return False, f"Generic/fabricated reference detected: '{phrase}'"
        
        # Check 3: Verify against playbook content (fuzzy match)
        is_verifiable, match_details = self._verify_in_playbook(reference)
        if not is_verifiable:
            return False, f"Reference not found in playbook: {match_details}"
        
        return True, "OK"
    
    def _verify_in_playbook(self, reference: str) -> Tuple[bool, str]:
        """
        Verify reference exists in playbook using fuzzy matching.
        
        Strategies:
        1. Exact substring (best)
        2. Sentence overlap (good)
        3. Word overlap (acceptable)
        """
        ref_lower = reference.lower()
        
        # Strategy 1: Exact or near-exact substring
        if ref_lower in self.playbook_lower:
            return True, "exact_match"
        
        # Strategy 2: Significant word overlap with at least one sentence
        ref_words = self._tokenize(reference)
        if len(ref_words) < 3:
            return False, "reference_too_short_for_matching"
        
        best_overlap = 0
        best_sentence = ""
        
        for sentence in self.playbook_sentences:
            sent_words = self._tokenize(sentence)
            if not sent_words:
                continue
            
            # Count overlapping words
            overlap = len(ref_words & sent_words)
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_sentence = sentence[:100]
        
        # Need at least MIN_MATCH_WORDS or 40% of reference words
        min_required = max(self.MIN_MATCH_WORDS, len(ref_words) * 0.4)
        
        if best_overlap >= min_required:
            return True, f"word_overlap_{best_overlap}"
        
        # Strategy 3: Check for key medical terms match
        # (More lenient - if rare medical terms appear in both, likely valid)
        rare_words = {w for w in ref_words if len(w) > 6 and w not in self.STOPWORDS}
        if rare_words:
            rare_in_playbook = sum(1 for w in rare_words if w in self.playbook_lower)
            if rare_in_playbook >= 2 or (len(rare_words) == 1 and rare_in_playbook == 1):
                return True, f"rare_term_match_{rare_in_playbook}"
        
        return False, f"best_overlap_{best_overlap}_of_{len(ref_words)}"
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!?]+\s*', text)
        # Filter short/empty
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into set of meaningful words."""
        # Remove punctuation and lowercase
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text_clean.split()
        # Filter stopwords and short words
        return {w for w in words if w not in self.STOPWORDS and len(w) > 2}


def validate_suggestions_references(
    suggestions: List[Dict],
    playbook_content: str
) -> Tuple[List[Dict], List[Dict]]:
    """
    Batch validate references for all suggestions.
    
    Args:
        suggestions: List of suggestion dicts
        playbook_content: Full playbook text
    
    Returns:
        (valid_suggestions, invalid_suggestions)
    """
    if not playbook_content or not playbook_content.strip():
        logger.warning("Empty playbook content, skipping reference validation")
        return suggestions, []
    
    validator = ReferenceValidator(playbook_content)
    
    valid = []
    invalid = []
    
    for sug in suggestions:
        reference = sug.get('playbook_reference', '')
        title = sug.get('title', sug.get('id', 'unknown'))
        
        is_valid, reason = validator.validate_reference(reference, title)
        
        if is_valid:
            valid.append(sug)
        else:
            logger.warning(
                f"❌ Reference validation failed for '{title}': {reason}\n"
                f"   Reference: {reference[:80]}..."
            )
            invalid.append({
                **sug,
                '_validation_error': f"Invalid reference: {reason}"
            })
    
    if invalid:
        logger.info(
            f"📋 Reference validation: {len(suggestions)} → {len(valid)} "
            f"({len(invalid)} invalid references)"
        )
    
    return valid, invalid
