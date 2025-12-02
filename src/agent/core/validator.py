"""
Response Validator - Validate LLM Output Schema

Responsibility: Validate LLM response matches expected schema before returning.
NO medical interpretation - just schema validation.
"""

import logging
from typing import Dict, List, Tuple, Any

# Logger - usar logger do core
from .logger import logger


class ValidationError(Exception):
    """Raised when LLM response validation fails."""
    pass


class ResponseValidator:
    """
    Validates LLM response structure and completeness.
    
    Principle: Simple schema validation only.
    NO medical interpretation, NO clinical validation.
    """
    
    def __init__(self):
        """Initialize validator with expected schema."""
        self.required_keys = [
            "clinical_extraction",
            "structural_analysis",
            "recommendations",
            "quality_scores",
            "metadata"
        ]
        
        self.required_clinical_keys = [
            "syndromes",
            "exams",
            "treatments",
            "red_flags"
        ]
        
        logger.debug("ResponseValidator initialized")
    
    def validate(self, response: Dict) -> Tuple[bool, List[str]]:
        """
        Validate LLM response against expected schema.
        
        Args:
            response: LLM response dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
            
        Raises:
            ValidationError: If response is invalid with specific error details
            
        Example:
            >>> validator = ResponseValidator()
            >>> is_valid, errors = validator.validate(response)
            >>> if not is_valid:
            >>>     raise ValidationError(f"Validation failed: {errors}")
        """
        errors = []
        
        # Check top-level keys
        for key in self.required_keys:
            if key not in response:
                errors.append(f"Missing required key: {key}")
        
        if errors:
            error_msg = f"Missing required keys in LLM response: {', '.join(errors)}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Validate clinical_extraction structure
        clinical = response.get("clinical_extraction", {})
        clinical_errors = self._validate_clinical_extraction(clinical)
        errors.extend(clinical_errors)
        
        # Validate quality_scores structure
        quality = response.get("quality_scores", {})
        quality_errors = self._validate_quality_scores(quality)
        errors.extend(quality_errors)
        
        # Log validation result
        if errors:
            logger.warning(f"LLM response validation found {len(errors)} issues: {errors}")
        else:
            logger.debug("LLM response validation passed")
        
        return len(errors) == 0, errors
    
    def _validate_clinical_extraction(self, clinical: Dict) -> List[str]:
        """Validate clinical_extraction structure."""
        errors = []
        
        if not isinstance(clinical, dict):
            errors.append("clinical_extraction must be a dictionary")
            return errors
        
        # Check that required fields exist (they should be lists)
        for key in self.required_clinical_keys:
            if key not in clinical:
                errors.append(f"clinical_extraction missing key: {key}")
            elif not isinstance(clinical[key], list):
                errors.append(f"clinical_extraction.{key} must be a list")
        
        return errors
    
    def _validate_quality_scores(self, quality: Dict) -> List[str]:
        """Validate quality_scores structure."""
        errors = []
        
        if not isinstance(quality, dict):
            errors.append("quality_scores must be a dictionary")
            return errors
        
        # Check required quality scores exist
        required_scores = [
            "clinical_coverage",
            "structural_quality",
            "safety_implementation",
            "overall_quality"
        ]
        
        for score_key in required_scores:
            if score_key not in quality:
                errors.append(f"quality_scores missing key: {score_key}")
            else:
                score_value = quality[score_key]
                if not isinstance(score_value, (int, float)):
                    errors.append(f"quality_scores.{score_key} must be numeric")
                elif not (0 <= score_value <= 100):
                    errors.append(f"quality_scores.{score_key} out of range (0-100): {score_value}")
        
        return errors
    
    def validate_completeness(self, response: Dict, playbook_size: int = 0) -> Tuple[bool, List[str]]:
        """
        Validate clinical completeness (non-empty extraction for non-trivial playbooks).
        
        This is a content check, not schema validation.
        """
        warnings = []
        
        clinical = response.get("clinical_extraction", {})
        
        # Check if extraction is empty for non-trivial playbook
        if playbook_size > 100:  # Non-trivial playbook
            syndromes = len(clinical.get("syndromes", []))
            exams = len(clinical.get("exams", []))
            treatments = len(clinical.get("treatments", []))
            
            total_extracted = syndromes + exams + treatments
            
            if total_extracted == 0:
                warnings.append(
                    f"No clinical elements extracted from playbook ({playbook_size} chars). "
                    f"Playbook may lack clinical content or extraction failed."
                )
        
        return len(warnings) == 0, warnings

