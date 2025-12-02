"""
Agente Daktus QA - Standard Analysis Pipeline

Standard analysis mode: generates 5-15 improvement suggestions.
This is the basic analysis pipeline for protocol validation.
"""

import json
from typing import Dict, Optional
from pathlib import Path

# CRITICAL: Load .env FIRST, before any other imports
from dotenv import load_dotenv

# Calculate project root: src/agent/analysis/standard.py -> project root
project_root = Path(__file__).resolve().parent.parent.parent.parent
env_file = project_root / ".env"

# Load .env from project root
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    # Fallback: try current working directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)
    else:
        load_dotenv(override=True)

from ..core.protocol_loader import load_protocol, load_playbook
from ..core.prompt_builder import PromptBuilder
from ..core.llm_client import LLMClient
from ..core.validator import ResponseValidator
from ..core.logger import logger


def analyze(protocol_path: str, playbook_path: Optional[str] = None, model: Optional[str] = None) -> Dict:
    """
    Main analysis function - Standard mode.
    
    This is the standard analysis pipeline for protocol validation.
    Generates 5-15 improvement suggestions.
    
    Args:
        protocol_path: Path to protocol JSON file
        playbook_path: Optional path to playbook file (markdown/PDF)
        model: Optional LLM model identifier (default: from environment)
        
    Returns:
        Complete analysis result as dictionary:
        {
            "protocol_analysis": {...},
            "improvement_suggestions": [...],
            "metadata": {...}
        }
        
    Raises:
        FileNotFoundError: If protocol or playbook file not found
        ValueError: If LLM analysis fails
    """
    logger.info("=" * 60)
    logger.info("Agente Daktus QA - Standard Analysis Pipeline")
    logger.info("=" * 60)
    
    # Step 1: Load protocol
    logger.info(f"Step 1: Loading protocol from {protocol_path}")
    try:
        protocol_json = load_protocol(protocol_path)
    except Exception as e:
        logger.error(f"Failed to load protocol: {e}")
        raise
    
    # Step 2: Load playbook (if provided)
    playbook_content = ""
    if playbook_path:
        logger.info(f"Step 2: Loading playbook from {playbook_path}")
        try:
            playbook_content = load_playbook(playbook_path)
        except Exception as e:
            logger.error(f"Failed to load playbook: {e}")
            raise
    else:
        logger.info("Step 2: No playbook provided - structural analysis only")
    
    # Step 3: Build prompt (with caching support)
    logger.info("Step 3: Building analysis prompt")
    try:
        builder = PromptBuilder()
        # Use caching if playbook is provided and substantial (>1000 chars)
        use_cache = bool(playbook_path and len(playbook_content) > 1000)
        prompt_structure = builder.build_analysis_prompt(playbook_content, protocol_json, use_cache=use_cache)
    except Exception as e:
        logger.error(f"Failed to build prompt: {e}")
        raise
    
    # Step 4: LLM analysis
    logger.info("Step 4: Calling LLM for analysis")
    try:
        client = LLMClient(model=model)
        # Pass prompt structure (dict) or string depending on caching
        llm_result = client.analyze(prompt_structure)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        raise
    
    # Step 5: Validate response
    logger.info("Step 5: Validating LLM response")
    try:
        validator = ResponseValidator()
        is_valid, errors = validator.validate(llm_result)
        if not is_valid:
            error_msg = f"LLM response validation failed: {errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    except Exception as e:
        logger.error(f"Response validation failed: {e}")
        raise
    
    # Step 6: Format final output
    logger.info("Step 6: Formatting final output")
    
    # Extract components from LLM result
    clinical_extraction = llm_result.get("clinical_extraction", {})
    structural_analysis = llm_result.get("structural_analysis", {})
    recommendations = llm_result.get("recommendations", [])
    quality_scores = llm_result.get("quality_scores", {})
    
    # Build unified output format
    result = {
        "protocol_analysis": {
            "structural": structural_analysis,
            "clinical_extraction": clinical_extraction
        },
        "improvement_suggestions": recommendations,
        "metadata": {
            "protocol_path": str(protocol_path),
            "playbook_path": str(playbook_path) if playbook_path else None,
            "model_used": client.model,
            "timestamp": llm_result.get("metadata", {}).get("timestamp", ""),
            "processing_time_ms": llm_result.get("metadata", {}).get("processing_time_ms", 0),
            "quality_scores": quality_scores
        }
    }
    
    logger.info("=" * 60)
    logger.info("Agente Daktus QA - Standard Analysis Complete")
    logger.info("=" * 60)
    
    return result

