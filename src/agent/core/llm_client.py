"""
LLM Client - Simple API Communication (No Clinical Processing)

Responsibility: Communicate with LLM API to send prompts and receive responses.
NO medical validation, NO clinical interpretation, NO content analysis.
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Union, Tuple
from datetime import datetime
import time

# CRITICAL: Load .env FIRST, before any other imports
from dotenv import load_dotenv

# Calculate project root: src/agent/core/llm_client.py -> project root
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

# Add parent directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

# MVP: Direct OpenRouter API - no dependencies on legacy infrastructure

# Logger - usar logger do core
from .logger import logger


class LLMClient:
    """
    Simple LLM communication client - sends prompts and receives responses.
    
    Principle: Pure API communication. NO clinical processing.
    All medical intelligence is in the prompt, not in this code.
    """
    
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize LLM client.
        
        Loads .env file and gets API key from environment.
        
        Args:
            model: LLM model identifier (default: from environment or model catalog)
            api_key: API key (default: from environment)
        """
        # Get API key from parameter first, then environment
        # .env is already loaded at module import time
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        
        # Validate API key with helpful error message
        if not self.api_key:
            error_msg = (
                "OPENROUTER_API_KEY not found.\n"
                f"  Expected .env location: {env_file}\n"
                f"  Current directory .env: {Path.cwd() / '.env'}\n"
                "  Solutions:\n"
                "  1. Create .env file in project root with: OPENROUTER_API_KEY=sk-or-v1-...\n"
                "  2. Set environment variable: $env:OPENROUTER_API_KEY='sk-or-v1-...' (PowerShell)\n"
                "  3. Or: setx OPENROUTER_API_KEY 'sk-or-v1-...' (Windows CMD)"
            )
            try:
                logger.error(error_msg)
            except:
                pass
            raise ValueError(error_msg)
        
        # Get model from parameter, environment, or catalog (preserve existing behavior)
        if model:
            model_id = model
        else:
            model_id = os.getenv("LLM_MODEL")
            if not model_id:
                # Use model catalog default (same as existing system)
                try:
                    from llm.model_catalog import get_default_model
                    default_model = get_default_model()
                    model_id = default_model.id
                except ImportError:
                    model_id = "x-ai/grok-4.1-fast:free"  # Default: Grok 4.1 Fast (Free) - gratuito, contexto 2M tokens
        
        # Validate and get model info from catalog (if available)
        try:
            from llm.model_catalog import get_model_by_id, validate_model
            if validate_model(model_id):
                model_obj = get_model_by_id(model_id)
                if model_obj:
                    self.model = model_obj.id
                    self.model_name = model_obj.name
                else:
                    self.model = model_id
                    self.model_name = model_id
            else:
                self.model = model_id
                self.model_name = model_id
        except ImportError:
            # Catalog not available, use model_id directly
            self.model = model_id
            self.model_name = model_id
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.available = bool(self.api_key)
        
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable not set. "
                "Set it in .env file or environment. "
                "See INSTALACAO.md for setup instructions."
            )
        
        logger.info(f"LLMClient initialized with model: {self.model} ({getattr(self, 'model_name', 'N/A')})")
    
    def _is_free_model(self, model: str) -> bool:
        """
        Verifica se o modelo é gratuito (sem limite de tokens).
        
        Args:
            model: ID do modelo
            
        Returns:
            True se for modelo gratuito, False caso contrário
        """
        free_models = [
            "x-ai/grok-4.1-fast:free",
            "grok-4.1-fast:free",
        ]
        return any(free_model in model for free_model in free_models)
    
    def _is_grok_model(self, model: str) -> bool:
        """
        Verifica se o modelo é Grok (não suporta formato estruturado com cache).
        
        Args:
            model: ID do modelo
            
        Returns:
            True se for modelo Grok, False caso contrário
        """
        grok_models = [
            "x-ai/grok",
            "grok",
        ]
        return any(grok_model in model.lower() for grok_model in grok_models)
    
    def analyze(self, prompt: Union[str, Dict], max_retries: int = 3) -> Dict:
        """
        Send analysis prompt to LLM and return parsed JSON response.
        
        Simple API call and JSON parsing only.
        NO medical validation, NO clinical interpretation.
        
        Args:
            prompt: Complete analysis prompt (string) OR structured prompt dict with:
                {
                    "system": [{"type": "text", "text": "...", "cache_control": {...}}],
                    "messages": [{"role": "user", "content": "..."}]
                }
            max_retries: Maximum retry attempts on failure
            
        Returns:
            Structured analysis as dictionary (parsed from LLM JSON response)
            
        Raises:
            ValueError: If API key not configured
            requests.RequestException: If API call fails
            json.JSONDecodeError: If response cannot be parsed as JSON
            
        Example:
            >>> client = LLMClient()
            >>> prompt = "Analyze this protocol..."
            >>> result = client.analyze(prompt)
            >>> "clinical_extraction" in result
            True
        """
        request_id = f"req_{int(time.time() * 1000)}"
        start_time = time.time()
        
        logger.info(f"LLM analysis started: request_id={request_id}, model={self.model}")
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                # Call LLM API
                response_text, finish_reason, usage = self._call_api(prompt, attempt=attempt)
                
                # Check if response was truncated
                if finish_reason == "length":
                    logger.warning(
                        f"LLM response truncated (attempt {attempt + 1}/{max_retries}). "
                        f"Content length: {len(response_text)} chars. "
                        f"Attempting to repair incomplete JSON..."
                    )
                    
                    # Try to repair truncated JSON
                    repaired_result = self._attempt_truncated_json_repair(response_text)
                    if repaired_result:
                        logger.info(f"Successfully repaired truncated JSON on attempt {attempt + 1}")
                        latency_ms = int((time.time() - start_time) * 1000)
                        logger.info(
                            f"LLM analysis completed: request_id={request_id}, "
                            f"latency_ms={latency_ms}, attempt={attempt + 1}"
                        )
                        return repaired_result
                    
                    # If repair failed and not last attempt, retry with higher max_tokens
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(
                            f"Retrying with increased max_tokens after {wait_time}s "
                            f"(attempt {attempt + 2}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Failed to repair truncated JSON after all retries")
                        raise ValueError(
                            f"LLM response was truncated and could not be repaired. "
                            f"Response length: {len(response_text)} chars. "
                            f"Consider using a model with larger context window or chunking strategy."
                        )
                
                # Extract and parse JSON from response
                analysis_result = self._extract_json_from_response(response_text)
                
                # Calculate latency
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Log cache usage if available
                if usage:
                    cache_read = usage.get("cache_read_input_tokens", 0)
                    cache_creation = usage.get("cache_creation_input_tokens", 0)
                    if cache_read > 0 or cache_creation > 0:
                        logger.info(
                            f"Prompt cache used: read={cache_read} tokens, "
                            f"created={cache_creation} tokens"
                        )
                
                logger.info(
                    f"LLM analysis completed: request_id={request_id}, "
                    f"latency_ms={latency_ms}, attempt={attempt + 1}"
                )
                
                return analysis_result
                
            except requests.exceptions.Timeout as e:
                logger.warning(
                    f"LLM API timeout (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                else:
                    raise Exception(f"LLM API timeout after {max_retries} attempts")
            
            except requests.exceptions.HTTPError as e:
                if hasattr(e, 'response') and e.response.status_code == 429:
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        wait_time = 5 * (attempt + 1)
                        time.sleep(wait_time)
                    else:
                        raise Exception(f"Rate limited after {max_retries} attempts")
                else:
                    logger.error(f"LLM API error: {e}")
                    raise
            
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                # Attempt repair (response_text should be available from _call_api)
                try:
                    # response_text is available from the try block above
                    analysis_result = self._attempt_json_repair(response_text)
                    if analysis_result:
                        logger.info("Successfully repaired malformed JSON")
                        latency_ms = int((time.time() - start_time) * 1000)
                        logger.info(
                            f"LLM analysis completed: request_id={request_id}, "
                            f"latency_ms={latency_ms}, attempt={attempt + 1}"
                        )
                        return analysis_result
                except Exception as repair_error:
                    logger.debug(f"JSON repair attempt failed: {repair_error}")
                
                # If repair fails and this is last attempt, raise with full context
                if attempt == max_retries - 1:
                    error_msg = str(e)
                    if len(response_text) > 2000:
                        preview = f"{response_text[:1000]}...\n[Response truncated, total length: {len(response_text)} chars]"
                    else:
                        preview = response_text
                    raise ValueError(
                        f"Could not parse JSON from LLM response after {max_retries} attempts.\n"
                        f"Error: {error_msg}\n\n"
                        f"Response preview:\n{preview}"
                    )
            
            except Exception as e:
                logger.error(f"Unexpected error in LLM call: {e}", exc_info=True)
                # MVP: Return structured error, no retries
                return {
                    "status": "error",
                    "error_type": "llm_failure",
                    "message": str(e),
                    "partial_result": None
                }
    
    def _call_api(self, prompt: Union[str, Dict], attempt: int = 0) -> Tuple[str, str, Dict]:
        """
        Make API call to OpenRouter with support for prompt caching.
        
        Simple HTTP request - NO medical processing, NO legacy dependencies.
        
        Args:
            prompt: String prompt OR structured dict with system/messages for caching
            attempt: Retry attempt number (used to increase max_tokens on retry)
            
        Returns:
            Tuple of (content, finish_reason, usage_dict)
        """
        if not _REQUESTS_AVAILABLE:
            raise ImportError("requests library not available. Install with: pip install requests")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/daktus-medical",
            "X-Title": "Daktus QA Agent"
        }
        
        # Determinar se é modelo gratuito (sem limite de tokens)
        is_free_model = self._is_free_model(self.model)
        # Determinar se é modelo Grok (não suporta formato estruturado)
        is_grok_model = self._is_grok_model(self.model)
        
        # Build payload based on prompt type
        # Grok models não suportam formato estruturado com cache, usar string prompt
        if isinstance(prompt, dict) and "system" in prompt and not is_grok_model:
            # Structured prompt with caching support (apenas para modelos que suportam)
            payload = {
                "model": self.model,
                "system": prompt["system"],
                "messages": prompt["messages"],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}  # Request JSON if supported
            }
            # Apenas adicionar max_tokens se não for modelo gratuito
            if not is_free_model:
                payload["max_tokens"] = min(32000 + (attempt * 8000), 128000)  # Increase on retry, max 128k
            logger.debug(f"Using structured prompt with caching support (attempt {attempt + 1}, free_model={is_free_model})")
        else:
            # Legacy string prompt (no caching) - usado para Grok ou prompts simples
            if isinstance(prompt, dict) and "system" in prompt:
                # Converter prompt estruturado para string (para Grok)
                system_parts = []
                for item in prompt["system"]:
                    if isinstance(item, dict) and "text" in item:
                        system_parts.append(item["text"])
                    elif isinstance(item, str):
                        system_parts.append(item)
                
                messages_parts = []
                for msg in prompt["messages"]:
                    if isinstance(msg, dict) and "content" in msg:
                        messages_parts.append(msg["content"])
                    elif isinstance(msg, str):
                        messages_parts.append(msg)
                
                # Combinar system e messages em um único prompt string
                prompt_str = "\n\n".join(system_parts + messages_parts)
                logger.debug(f"Converted structured prompt to string for Grok compatibility")
            else:
                prompt_str = prompt if isinstance(prompt, str) else prompt.get("prompt", "")
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt_str}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}  # Request JSON if supported
            }
            # Apenas adicionar max_tokens se não for modelo gratuito
            if not is_free_model:
                payload["max_tokens"] = min(32000 + (attempt * 8000), 128000)  # Increase on retry
            logger.debug(f"Using string prompt (no caching, attempt {attempt + 1}, free_model={is_free_model}, grok={is_grok_model})")
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=120  # Increased timeout for large responses
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Log response metadata for debugging
        choice = result.get("choices", [{}])[0]
        finish_reason = choice.get("finish_reason", "unknown")
        usage = result.get("usage", {})
        
        logger.debug(
            f"LLM API response: finish_reason={finish_reason}, "
            f"prompt_tokens={usage.get('prompt_tokens', 0)}, "
            f"completion_tokens={usage.get('completion_tokens', 0)}, "
            f"total_tokens={usage.get('total_tokens', 0)}, "
            f"max_tokens={payload.get('max_tokens', 'N/A')}"
        )
        
        content = choice.get("message", {}).get("content", "")
        
        return content, finish_reason, usage
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """
        Extract and parse JSON from LLM response.
        
        Simple JSON extraction - NO medical validation.
        Attempts multiple strategies to find JSON in response.
        """
        # Clean response first - remove any leading/trailing whitespace
        response = response.strip()
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract from markdown code blocks
        # Find content after ```json or ``` and extract JSON using brace counting
        # Don't rely on closing markers - just extract from first { to matching }
        code_block_markers = ['```json', '```']
        
        for start_marker in code_block_markers:
            start_idx = response.find(start_marker)
            if start_idx != -1:
                # Find content start (after the marker)
                content_start = start_idx + len(start_marker)
                # Skip leading whitespace/newlines
                while content_start < len(response) and response[content_start] in ['\n', '\r', ' ', '\t']:
                    content_start += 1
                
                # Extract everything from content_start and use brace counting to find complete JSON
                # This works even if there's no closing ``` or if it appears later
                content = response[content_start:]
                json_str = self._extract_json_by_braces(content)
                if json_str:
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.debug(f"Failed to parse JSON extracted from markdown block: {e}")
                        continue
        
        # Strategy 3: Find JSON object by counting braces from first {
        json_str = self._extract_json_by_braces(response)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try removing markdown and parsing
        cleaned = re.sub(r'```(?:json)?\s*', '', response)
        cleaned = re.sub(r'\s*```', '', cleaned)
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # All strategies failed - provide detailed error with diagnostic info
        # Check if JSON appears incomplete (no closing brace found)
        first_brace_idx = response.find('{')
        last_brace_idx = response.rfind('}')
        
        diagnostic = []
        diagnostic.append(f"Response length: {len(response)} chars")
        if first_brace_idx != -1:
            diagnostic.append(f"First '{{' found at position: {first_brace_idx}")
        else:
            diagnostic.append("No '{' found in response")
        
        if last_brace_idx != -1:
            diagnostic.append(f"Last '}}' found at position: {last_brace_idx}")
            # Count braces to see if they match
            brace_count_open = response.count('{')
            brace_count_close = response.count('}')
            brace_diff = brace_count_open - brace_count_close
            if brace_diff != 0:
                diagnostic.append(f"WARNING: Unbalanced braces! '{{' count: {brace_count_open}, '}}' count: {brace_count_close}")
        else:
            diagnostic.append("No '}' found in response - JSON appears incomplete!")
        
        # Check if response ends abruptly
        if not response.strip().endswith('}'):
            diagnostic.append("Response does not end with '}' - may be truncated")
        
        preview_start = response[:500] if len(response) > 500 else response
        preview_end = response[-500:] if len(response) > 500 else response
        
        error_msg = (
            f"Could not extract valid JSON from LLM response.\n\n"
            f"Diagnostics:\n" + "\n".join(f"  - {d}" for d in diagnostic) + "\n\n"
            f"Response start (first 500 chars):\n{preview_start}\n\n"
            f"Response end (last 500 chars):\n{preview_end}\n\n"
            f"Full response saved to error log."
        )
        
        # Log full response for debugging
        logger.error(f"Full LLM response that failed to parse:\n{response}")
        
        raise ValueError(error_msg)
    
    def _extract_json_by_braces(self, text: str) -> Optional[str]:
        """
        Extract JSON object by finding matching braces.
        
        Starts from first { and counts braces to find matching }.
        Handles strings with escaped quotes and braces inside strings.
        """
        first_brace = text.find('{')
        if first_brace == -1:
            return None
        
        brace_count = 0
        start_pos = first_brace
        in_string = False
        escape_next = False
        
        for i in range(start_pos, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found matching closing brace
                        return text[start_pos:i+1]
        
        # No matching closing brace found - JSON may be incomplete
        return None
    
    def _attempt_json_repair(self, response: str) -> Optional[Dict]:
        """
        Attempt to repair malformed JSON (simple fixes only).
        
        Basic repair attempts - NO medical interpretation.
        """
        # Strategy 1: Try extracting JSON by braces (most reliable)
        json_str = self._extract_json_by_braces(response)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Remove markdown code fences and try again
        cleaned = re.sub(r'```(?:json)?\s*', '', response, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```', '', cleaned)
        cleaned = cleaned.strip()
        json_str = self._extract_json_by_braces(cleaned)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Direct parsing after cleaning
        try:
            return json.loads(cleaned)
        except:
            return None
    
    def _attempt_truncated_json_repair(self, response: str) -> Optional[Dict]:
        """
        Attempt to repair truncated JSON by closing open structures.
        
        This is a best-effort repair for responses cut off mid-generation.
        """
        if not response.strip().startswith('{'):
            return None
        
        # Try to extract complete JSON structures first
        json_str = self._extract_json_by_braces(response)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # If extraction failed, try to close incomplete JSON
        # Count open braces and try to close them
        brace_count = response.count('{') - response.count('}')
        
        if brace_count > 0:
            # Try to close open structures
            repaired = response.rstrip()
            
            # Remove trailing comma if present
            if repaired.rstrip().endswith(','):
                repaired = repaired.rstrip()[:-1]
            
            # Close all open braces
            repaired += '\n' + ('}' * brace_count)
            
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass
        
        return None

