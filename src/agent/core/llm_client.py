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
        # Force reload .env to ensure we have the latest key
        if env_file.exists():
            load_dotenv(env_file, override=True)
        else:
            cwd_env = Path.cwd() / ".env"
            if cwd_env.exists():
                load_dotenv(cwd_env, override=True)
            else:
                load_dotenv(override=True)
        
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        
        # Log API key status (without exposing the full key)
        if self.api_key:
            key_preview = self.api_key[:20] + "..." if len(self.api_key) > 20 else self.api_key
            logger.debug(f"API key loaded: {key_preview} (length: {len(self.api_key)})")
        else:
            logger.warning("API key not found in environment")
        
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
                    model_id = "google/gemini-2.5-flash-lite"  # Default: Gemini 2.5 Flash Lite - barato e estável
        
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
        
        self.base_url = "https://openrouter.ai/api/v1"
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
            "google/gemini-2.5-flash-lite",
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

    def _run_with_auto_continue(self, prompt: Union[str, Dict], max_tokens: int = 20000) -> str:
        """
        Universal auto-continue wrapper for LLM completions.

        Automatically continues generation when the model stops with finish_reason == "length".
        Ensures complete outputs regardless of model or output size.

        Args:
            prompt: String prompt OR structured dict with system/messages
            max_tokens: Maximum tokens per call (default: 20000)

        Returns:
            Complete output as string (concatenated if continued)
        """
        full_output = ""
        current_prompt = prompt
        continuation_count = 0
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        while True:
            # Call low-level API
            call_start = time.time()
            content, finish_reason, usage = self._call_api(current_prompt, attempt=0, max_tokens=max_tokens)
            call_latency = int((time.time() - call_start) * 1000)
            
            # Track usage (Wave 3)
            try:
                from ..cost_control.cost_tracker import get_cost_tracker
                tracker = get_cost_tracker()
                tracker.record_usage("llm_call", usage, call_latency, self.model)
            except Exception:
                pass  # Cost tracking is optional
            
            # Accumulate usage
            total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            total_usage["total_tokens"] += usage.get("total_tokens", 0)

            # Append chunk to full output
            full_output += content

            # Check if truncated
            if finish_reason == "length":
                continuation_count += 1
                logger.info(
                    f"Response truncated (continuation #{continuation_count}), "
                    f"continuing... (current length: {len(full_output)} chars)"
                )

                # Build continuation prompt
                if isinstance(current_prompt, dict) and "messages" in current_prompt:
                    # Structured prompt: append assistant response and "continue" user message
                    messages = list(current_prompt.get("messages", []))
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": "continue"})
                    current_prompt = dict(current_prompt)
                    current_prompt["messages"] = messages
                else:
                    # String prompt: convert to message format for continuation
                    original_content = prompt if isinstance(prompt, str) else str(prompt)
                    current_prompt = {
                        "messages": [
                            {"role": "user", "content": original_content},
                            {"role": "assistant", "content": content},
                            {"role": "user", "content": "continue"}
                        ]
                    }

                continue

            # Not truncated, done
            break

        if continuation_count > 0:
            logger.info(
                f"Auto-continue completed: {continuation_count} continuation(s), "
                f"total length={len(full_output)} chars"
            )

        return full_output

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
                # Call LLM API with auto-continue (handles truncation automatically)
                response_text = self._run_with_auto_continue(prompt, max_tokens=20000)

                # Extract and parse JSON from response
                analysis_result = self._extract_json_from_response(response_text)
                
                # Calculate latency
                latency_ms = int((time.time() - start_time) * 1000)

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
                # Verificar se a exceção tem o atributo response e se não é None
                if hasattr(e, 'response') and e.response is not None:
                    if e.response.status_code == 429:
                        logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            wait_time = 5 * (attempt + 1)
                            time.sleep(wait_time)
                        else:
                            raise Exception(f"Rate limited after {max_retries} attempts")
                    elif e.response.status_code == 402:
                        # Erro 402 (Payment Required) - não fazer retry, apenas relançar
                        logger.error(f"Payment required (402) - insufficient credits. Error: {e}")
                        raise
                    elif e.response.status_code == 403:
                        # Erro 403 (Forbidden) - modelo não disponível ou quota excedida
                        logger.error(
                            f"Access forbidden (403) - model may be unavailable or quota exceeded. "
                            f"Try a different model (e.g., gemini-2.5-flash-lite). Error: {e}"
                        )
                        raise Exception(
                            f"403 Forbidden: O modelo selecionado pode estar indisponível ou quota excedida. "
                            f"Tente usar outro modelo (ex: Gemini 2.5 Flash Lite). Erro original: {e}"
                        )
                    else:
                        logger.error(f"LLM API error: {e}")
                        raise
                else:
                    # Exceção HTTPError sem response - relançar como está
                    logger.error(f"LLM API error (no response object): {e}")
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
    
    def _call_api(self, prompt: Union[str, Dict], attempt: int = 0, max_tokens: int = 20000) -> Tuple[str, str, Dict]:
        """
        Make API call to OpenRouter with support for prompt caching.

        Simple HTTP request - NO medical processing, NO legacy dependencies.

        Args:
            prompt: String prompt OR structured dict with system/messages for caching
            attempt: Retry attempt number (used to increase max_tokens on retry)
            max_tokens: Maximum tokens for completion (default: 20000)

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
            # Converter system array para formato que a API aceita
            system_content = prompt["system"]
            if isinstance(system_content, list):
                # Se system é array, converter para string ou formato de mensagens
                system_parts = []
                for item in system_content:
                    if isinstance(item, dict):
                        if "text" in item:
                            system_parts.append(item["text"])
                        elif "type" in item and item["type"] == "text" and "text" in item:
                            system_parts.append(item["text"])
                    elif isinstance(item, str):
                        system_parts.append(item)
                # Combinar todas as partes do system em uma string
                system_str = "\n\n".join(system_parts)
            else:
                system_str = system_content if isinstance(system_content, str) else str(system_content)
            
            # Converter messages para formato correto
            messages = []
            for msg in prompt["messages"]:
                if isinstance(msg, dict):
                    if "role" in msg and "content" in msg:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                    elif "content" in msg:
                        messages.append({"role": "user", "content": msg["content"]})
                elif isinstance(msg, str):
                    messages.append({"role": "user", "content": msg})
            
            # Verificar se é modelo Claude (pode não suportar response_format ou system separado)
            is_claude = "claude" in self.model.lower() or "anthropic" in self.model.lower()
            
            # Para Claude, usar formato de mensagens (system como role="system")
            if is_claude:
                # Claude usa system como mensagem com role="system"
                if system_str:
                    messages.insert(0, {"role": "system", "content": system_str})
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1
                    # Claude não suporta response_format={"type": "json_object"}
                }
            else:
                # Outros modelos podem usar system separado e response_format
                payload = {
                    "model": self.model,
                    "system": system_str,
                    "messages": messages,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
            # Adicionar max_tokens apenas se não for modelo gratuito E não for Grok
            # Grok (free ou pago) não deve ter max_tokens para evitar truncamento
            if not is_free_model and not is_grok_model:
                payload["max_tokens"] = max_tokens
            logger.debug(f"Using structured prompt with caching support (attempt {attempt + 1}, free_model={is_free_model}, grok={is_grok_model}, max_tokens={max_tokens if not is_grok_model else 'N/A'})")
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
            elif isinstance(prompt, dict) and "messages" in prompt:
                # CRITICAL FIX: Handle dict with 'messages' but without 'system' (continuation case)
                # Extract content from messages and combine into prompt_str
                messages_parts = []
                for msg in prompt.get("messages", []):
                    if isinstance(msg, dict) and "content" in msg:
                        messages_parts.append(str(msg["content"]))
                    elif isinstance(msg, str):
                        messages_parts.append(msg)
                prompt_str = "\n\n".join(messages_parts) if messages_parts else ""
                if not prompt_str:
                    logger.error("Empty messages array in prompt dict!")
                logger.debug(f"Extracted prompt from messages dict (continuation mode)")
            else:
                prompt_str = prompt if isinstance(prompt, str) else prompt.get("prompt", "")
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt_str}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}  # Request JSON if supported
            }
            # NUNCA adicionar max_tokens para modelos Grok (free ou pago)
            # Grok tem comportamento diferente e max_tokens pode causar truncamento
            if not is_free_model and not is_grok_model:
                payload["max_tokens"] = max_tokens
            logger.debug(f"Using string prompt (no caching, attempt {attempt + 1}, free_model={is_free_model}, grok={is_grok_model}, max_tokens={'N/A' if is_grok_model else payload.get('max_tokens', 'N/A')})")
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120  # Increased timeout for large responses
        )
        
        # Tratamento de erro 402 (Payment Required)
        if response.status_code == 402:
            try:
                error_detail = response.json()
                error_message = error_detail.get('error', {}).get('message', 'Unknown error')
                logger.error(f"API 402 Error (Payment Required): {error_message}")
                logger.error(f"Full error details: {json.dumps(error_detail, indent=2)}")
                
                # Log API key status (without exposing the full key)
                key_preview = self.api_key[:20] + "..." if len(self.api_key) > 20 else self.api_key
                logger.error(f"API key being used: {key_preview} (length: {len(self.api_key)})")
                logger.error("This error usually means:")
                logger.error("  1. The API key has no credits or has expired")
                logger.error("  2. The API key is invalid or incorrect")
                logger.error("  3. Check your OpenRouter account balance at https://openrouter.ai/keys")
                logger.error("  4. Verify the API key in your .env file matches the one in OpenRouter")
            except Exception as e:
                logger.error(f"API 402 Error Response: {response.text[:500]}")
            # Criar exceção HTTPError corretamente com a resposta
            http_error = requests.exceptions.HTTPError(
                f"402 Payment Required: Your OpenRouter API key has no credits or is invalid. "
                f"Please check your account balance at https://openrouter.ai/keys and verify your API key in .env"
            )
            http_error.response = response
            raise http_error
        
        # Melhor tratamento de erro 400
        if response.status_code == 400:
            try:
                error_detail = response.json()
                error_message = error_detail.get('error', {}).get('message', 'Unknown error')
                logger.error(f"API 400 Error: {error_message}")
                logger.error(f"Full error details: {json.dumps(error_detail, indent=2)}")
                
                # Log payload summary (without exposing full content)
                payload_summary = {
                    "model": payload.get("model"),
                    "message_count": len(payload.get("messages", [])),
                    "has_system": "system" in payload,
                    "temperature": payload.get("temperature"),
                    "max_tokens": payload.get("max_tokens", "N/A"),
                    "has_response_format": "response_format" in payload
                }
                logger.error(f"Payload summary: {json.dumps(payload_summary, indent=2)}")
                
                # If it's a content length issue, log that
                total_content_length = sum(
                    len(str(m.get("content", ""))) 
                    for m in payload.get("messages", [])
                )
                logger.error(f"Total message content length: {total_content_length} chars")
            except Exception as e:
                logger.error(f"API 400 Error Response: {response.text[:500]}")
        
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
        # Clean response first - remove any leading/trailing whitespace and invisible characters
        response = response.strip()
        
        # Remove BOM and other invisible characters that can break JSON parsing
        response = response.lstrip('\ufeff\u200b\u200c\u200d\ufffe')
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.debug(f"Direct JSON parse failed: {e}")
        
        # Strategy 1.5: Try with .encode().decode() to normalize encoding
        try:
            normalized = response.encode('utf-8', errors='ignore').decode('utf-8')
            return json.loads(normalized)
        except json.JSONDecodeError as e:
            logger.debug(f"Normalized JSON parse failed: {e}")
        
        # Strategy 1.6: Try fixing common escape issues in nested strings
        # JSON with nested escaped strings like \" inside \" can fail
        try:
            # Replace double-escaped backslashes that might cause issues
            fixed = response.replace('\\\\\\\"', '\\\\u0022')  # Escaped quotes
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            logger.debug(f"Fixed escapes JSON parse failed: {e}")
        
        # Strategy 1.7: For responses that look like complete JSON, try direct slice
        if response.strip().startswith('{') and response.strip().endswith('}'):
            try:
                # Try parsing after removing any invisible control chars
                clean = ''.join(c for c in response if ord(c) >= 32 or c in '\n\r\t')
                return json.loads(clean)
            except json.JSONDecodeError as e:
                logger.debug(f"Clean control chars JSON parse failed: {e}")
        
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
        
        # Strategy 5: Most aggressive - just take everything between first { and last }
        first_brace_idx = response.find('{')
        last_brace_idx = response.rfind('}')
        if first_brace_idx != -1 and last_brace_idx != -1 and last_brace_idx > first_brace_idx:
            try:
                json_str = response[first_brace_idx:last_brace_idx + 1]
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.debug(f"Strategy 5 (simple slice) failed: {e}")
        
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
        i = start_pos
        
        while i < len(text):
            char = text[i]
            
            # Handle escape sequences inside strings
            if in_string and char == '\\' and i + 1 < len(text):
                # Skip the next character (escaped)
                i += 2
                continue
            
            if char == '"':
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found matching closing brace
                        return text[start_pos:i+1]
            
            i += 1
        
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
    
    def _find_last_complete_structure(self, json_text: str) -> Tuple[Optional[str], Optional[Dict], int]:
        """
        Encontra o último ponto válido no JSON truncado.
        
        Args:
            json_text: JSON truncado como string
            
        Returns:
            Tuple de (json_completo_até_aqui, contexto_para_continuação, índice_do_último_nó)
            - json_completo_até_aqui: JSON válido até o último nó completo (None se não encontrar)
            - contexto_para_continuação: Dict com informações para continuação (None se não encontrar)
            - índice_do_último_nó: Índice do último nó completo no array (ou -1 se não encontrar)
        """
        # Tentar extrair JSON válido até onde conseguir
        json_str = self._extract_json_by_braces(json_text)
        if not json_str:
            return None, None, -1
        
        try:
            partial_json = json.loads(json_str)
        except json.JSONDecodeError:
            return None, None, -1
        
        # Procurar por estrutura "reconstructed_protocol" -> "nodes" (caso de reconstrução)
        if "reconstructed_protocol" in partial_json:
            protocol = partial_json["reconstructed_protocol"]
        elif "protocol" in partial_json:
            protocol = partial_json["protocol"]
        else:
            protocol = partial_json
        
        # Se tem array "nodes", encontrar último nó completo
        if isinstance(protocol, dict) and "nodes" in protocol:
            nodes = protocol["nodes"]
            if isinstance(nodes, list) and len(nodes) > 0:
                # Último nó do array (assumindo que está completo)
                last_node_idx = len(nodes) - 1
                last_node = nodes[last_node_idx]
                
                # Contexto para continuação
                context = {
                    "last_complete_node_index": last_node_idx,
                    "last_complete_node_id": last_node.get("id", f"node_{last_node_idx}") if isinstance(last_node, dict) else None,
                    "total_nodes_processed": len(nodes),
                    "structure_type": "protocol_with_nodes"
                }
                
                return json_str, context, last_node_idx
        
        # Se não tem estrutura conhecida, retornar o que temos
        context = {
            "structure_type": "unknown",
            "partial_json_keys": list(partial_json.keys()) if isinstance(partial_json, dict) else []
        }
        
        return json_str, context, -1
    
    def _continue_truncated_json(
        self,
        truncated_response: str,
        original_prompt: Union[str, Dict],
        continuation_level: int = 0,
        max_continuation_levels: int = 3
    ) -> Optional[Dict]:
        """
        Continua geração de JSON truncado fazendo nova chamada ao LLM.
        
        Args:
            truncated_response: Resposta truncada do LLM
            original_prompt: Prompt original usado na chamada
            continuation_level: Nível atual de continuação (0 = primeira continuação)
            max_continuation_levels: Máximo de níveis de continuação permitidos
            
        Returns:
            JSON completo (juntado) ou None se falhar
        """
        if continuation_level >= max_continuation_levels:
            logger.error(f"Maximum continuation levels ({max_continuation_levels}) reached")
            return None
        
        # Encontrar último ponto válido
        complete_json_str, context, last_node_idx = self._find_last_complete_structure(truncated_response)
        
        if not complete_json_str or not context:
            logger.warning("Could not find valid structure in truncated JSON for continuation")
            return None
        
        logger.info(
            f"Continuing truncated JSON (level {continuation_level + 1}/{max_continuation_levels}). "
            f"Last complete node index: {last_node_idx}, Context: {context.get('structure_type', 'unknown')}"
        )
        
        # Construir prompt de continuação
        continuation_prompt = self._build_continuation_prompt(
            original_prompt=original_prompt,
            complete_part=complete_json_str,
            context=context
        )
        
        # Fazer chamada de continuação
        try:
            continuation_response_text, continuation_finish_reason, _ = self._call_api(
                continuation_prompt,
                attempt=0  # Não aumentar max_tokens na continuação
            )
            
            # Se continuação também truncou, fazer nova continuação
            if continuation_finish_reason == "length":
                logger.warning(f"Continuation also truncated (level {continuation_level + 1})")
                continued_part = self._continue_truncated_json(
                    truncated_response=continuation_response_text,
                    original_prompt=original_prompt,
                    continuation_level=continuation_level + 1,
                    max_continuation_levels=max_continuation_levels
                )
                if not continued_part:
                    return None
                # Juntar: parte original (parseada) + continuação da continuação
                try:
                    first_part_dict = json.loads(complete_json_str)
                except json.JSONDecodeError:
                    logger.error("Failed to parse complete_json_str for merge")
                    return None
                return self._merge_json_parts(first_part_dict, continued_part)
            
            # Extrair JSON da continuação
            continuation_json = self._extract_json_from_response(continuation_response_text)
            
            # Parsear primeira parte para dict
            try:
                first_part_dict = json.loads(complete_json_str)
            except json.JSONDecodeError:
                logger.error("Failed to parse complete_json_str for merge")
                return None
            
            # Juntar partes
            merged_result = self._merge_json_parts(first_part_dict, continuation_json)
            
            return merged_result
            
        except Exception as e:
            logger.error(f"Error during JSON continuation: {e}", exc_info=True)
            return None
    
    def _build_continuation_prompt(
        self,
        original_prompt: Union[str, Dict],
        complete_part: str,
        context: Dict
    ) -> str:
        """
        Constrói prompt para continuação do JSON truncado.
        
        Args:
            original_prompt: Prompt original
            complete_part: JSON completo até o último ponto válido
            context: Contexto com informações sobre onde parou
            
        Returns:
            Prompt formatado para continuação
        """
        # Extrair informações do contexto
        structure_type = context.get("structure_type", "unknown")
        last_node_idx = context.get("last_complete_node_index", -1)
        total_processed = context.get("total_nodes_processed", 0)
        last_node_id = context.get("last_complete_node_id", None)
        
        # Tentar extrair informações do prompt original
        original_prompt_str = ""
        if isinstance(original_prompt, dict):
            # Converter prompt estruturado para string
            if "system" in original_prompt:
                system_parts = []
                for item in original_prompt.get("system", []):
                    if isinstance(item, dict) and "text" in item:
                        system_parts.append(item["text"])
                    elif isinstance(item, str):
                        system_parts.append(item)
                original_prompt_str += "\n\n".join(system_parts) + "\n\n"
            
            if "messages" in original_prompt:
                for msg in original_prompt.get("messages", []):
                    if isinstance(msg, dict) and "content" in msg:
                        original_prompt_str += msg["content"] + "\n\n"
                    elif isinstance(msg, str):
                        original_prompt_str += msg + "\n\n"
        else:
            original_prompt_str = str(original_prompt)
        
        # Construir prompt de continuação
        if structure_type == "protocol_with_nodes":
            continuation_prompt = f"""O JSON anterior foi truncado. Continue a partir do último nó completo.

CONTEXTO (últimos nós já processados):
- Total de nós processados: {total_processed}
- Último nó completo: índice {last_node_idx}"""
            if last_node_id:
                continuation_prompt += f" (ID: {last_node_id})"
            continuation_prompt += f"""

JSON COMPLETO ATÉ AQUI:
{complete_part}

INSTRUÇÕES:
1. Continue o JSON a partir do próximo nó após o último nó completo (índice {last_node_idx + 1})
2. NÃO repita nós já processados
3. Complete todos os nós restantes do protocolo
4. Retorne APENAS a continuação do JSON (sem repetir o início)
5. Formato: {{"reconstructed_protocol": {{"nodes": [<nós_restantes>], ...}}}}

PROMPT ORIGINAL (para referência):
{original_prompt_str[:2000]}..."""
        else:
            # Estrutura desconhecida - pedir continuação genérica
            continuation_prompt = f"""O JSON anterior foi truncado. Continue a partir do último ponto válido.

JSON COMPLETO ATÉ AQUI:
{complete_part}

INSTRUÇÕES:
1. Continue o JSON a partir do último ponto válido
2. NÃO repita conteúdo já processado
3. Complete a estrutura JSON
4. Retorne APENAS a continuação do JSON (sem repetir o início)

PROMPT ORIGINAL (para referência):
{original_prompt_str[:2000]}..."""
        
        return continuation_prompt
    
    def _merge_json_parts(self, first_part: Union[str, Dict], second_part: Union[str, Dict]) -> Optional[Dict]:
        """
        Junta duas partes de JSON de forma inteligente.
        
        Args:
            first_part: Primeira parte do JSON (string ou dict)
            second_part: Segunda parte do JSON (string ou dict)
            
        Returns:
            JSON completo juntado ou None se falhar
        """
        # Converter strings para dict se necessário
        if isinstance(first_part, str):
            try:
                first_dict = json.loads(first_part)
            except json.JSONDecodeError:
                logger.error("Failed to parse first_part as JSON")
                return None
        else:
            first_dict = first_part
        
        if isinstance(second_part, str):
            try:
                second_dict = json.loads(second_part)
            except json.JSONDecodeError:
                logger.error("Failed to parse second_part as JSON")
                return None
        else:
            second_dict = second_part
        
        # Extrair protocolos de ambas as partes
        first_protocol = None
        if "reconstructed_protocol" in first_dict:
            first_protocol = first_dict["reconstructed_protocol"]
        elif "protocol" in first_dict:
            first_protocol = first_dict["protocol"]
        else:
            first_protocol = first_dict
        
        second_protocol = None
        if "reconstructed_protocol" in second_dict:
            second_protocol = second_dict["reconstructed_protocol"]
        elif "protocol" in second_dict:
            second_protocol = second_dict["protocol"]
        else:
            second_protocol = second_dict
        
        # Se ambos têm estrutura "nodes", juntar arrays
        if (isinstance(first_protocol, dict) and "nodes" in first_protocol and
            isinstance(second_protocol, dict) and "nodes" in second_protocol):
            
            first_nodes = first_protocol["nodes"]
            second_nodes = second_protocol["nodes"]
            
            if not isinstance(first_nodes, list):
                first_nodes = []
            if not isinstance(second_nodes, list):
                second_nodes = []
            
            # Remover duplicatas por ID
            first_node_ids = set()
            for node in first_nodes:
                if isinstance(node, dict) and "id" in node:
                    first_node_ids.add(node["id"])
            
            # Adicionar apenas nós não duplicados da segunda parte
            merged_nodes = list(first_nodes)
            for node in second_nodes:
                if isinstance(node, dict) and "id" in node:
                    if node["id"] not in first_node_ids:
                        merged_nodes.append(node)
                        first_node_ids.add(node["id"])
                else:
                    # Nó sem ID - adicionar de qualquer forma (pode ser novo)
                    merged_nodes.append(node)
            
            # Construir resultado final
            merged_protocol = dict(first_protocol)
            merged_protocol["nodes"] = merged_nodes
            
            # Preservar metadados da primeira parte
            result = {"reconstructed_protocol": merged_protocol}
            
            # Validar JSON final
            try:
                json.dumps(result)  # Teste de serialização
                logger.info(f"Successfully merged JSON parts: {len(first_nodes)} + {len(second_nodes)} -> {len(merged_nodes)} nodes")
                return result
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to validate merged JSON: {e}")
                return None
        
        # Se não tem estrutura "nodes", tentar merge genérico
        # Preservar primeira parte e adicionar campos únicos da segunda
        merged = dict(first_dict)
        for key, value in second_dict.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                # Merge recursivo de dicts
                merged[key] = {**merged[key], **value}
            elif isinstance(merged[key], list) and isinstance(value, list):
                # Concatenar arrays (sem duplicatas se possível)
                merged[key] = merged[key] + [v for v in value if v not in merged[key]]
        
        try:
            json.dumps(merged)  # Teste de serialização
            logger.info("Successfully merged JSON parts (generic merge)")
            return merged
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to validate merged JSON: {e}")
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

