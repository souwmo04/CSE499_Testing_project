"""
VLM Client for Ollama Integration with LLaVA
============================================

This module provides the core Vision-Language Model client that connects to
Ollama's local server and uses LLaVA for visual reasoning on dashboard snapshots.

Algorithm: Visual-Time-Series Reasoning Pipeline
------------------------------------------------
1. Input: User question + latest dashboard snapshot image
2. Image Processing: Resize, normalize, prepare for VLM
3. Prompt Construction: Combine question + visual context + reasoning instructions
4. VLM Execution: Send to Ollama/LLaVA, receive structured response
5. Post-Processing: Extract insights (trends, correlations, volatility)
6. Response: Return human-readable answer

NO MOCK DATA - This is a real integration with Ollama.
"""

import base64
import logging
import os
# Prefer 'requests' if available, otherwise provide a minimal shim using urllib
try:
    import requests  # type: ignore
except Exception:
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error
    import socket
    import json as _json

    class _RequestsShim:
        class exceptions:
            class ConnectionError(Exception):
                pass
            class Timeout(Exception):
                pass

        def get(self, url, timeout=5):
            req = _urllib_request.Request(url, method="GET", headers={"Accept": "application/json"})
            try:
                with _urllib_request.urlopen(req, timeout=timeout) as resp:
                    status = resp.getcode()
                    text = resp.read().decode("utf-8")
                    return _ResponseShim(status, text)
            except _urllib_error.HTTPError as e:
                return _ResponseShim(e.code, e.read().decode("utf-8"))
            except _urllib_error.URLError as e:
                if isinstance(e.reason, socket.timeout):
                    raise self.exceptions.Timeout(e)
                raise self.exceptions.ConnectionError(e)

        def post(self, url, json=None, timeout=None):
            data = None
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if json is not None:
                data = _json.dumps(json).encode("utf-8")
            req = _urllib_request.Request(url, data=data, headers=headers, method="POST")
            try:
                with _urllib_request.urlopen(req, timeout=timeout) as resp:
                    status = resp.getcode()
                    text = resp.read().decode("utf-8")
                    return _ResponseShim(status, text)
            except _urllib_error.HTTPError as e:
                return _ResponseShim(e.code, e.read().decode("utf-8"))
            except _urllib_error.URLError as e:
                if isinstance(e.reason, socket.timeout):
                    raise self.exceptions.Timeout(e)
                raise self.exceptions.ConnectionError(e)

    class _ResponseShim:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self._text = text

        def json(self):
            return _json.loads(self._text)

    requests = _RequestsShim()
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class OllamaVLMClient:
    """
    Client for interacting with Ollama's Vision-Language Models (LLaVA).

    This client handles:
    - Connection to local Ollama server
    - Image encoding and transmission
    - Prompt construction for financial analysis
    - Response parsing and error handling
    """

    # Default Ollama configuration
    DEFAULT_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "llava"
    DEFAULT_TIMEOUT = 120  # seconds

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the Ollama VLM client.

        Args:
            host: Ollama server URL (default: http://localhost:11434)
            model: VLM model name (default: llava)
            timeout: Request timeout in seconds
        """
        self.host = host or os.environ.get("OLLAMA_HOST", self.DEFAULT_HOST)
        self.model = model or os.environ.get("OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.timeout = timeout
        self.api_generate = f"{self.host}/api/generate"
        self.api_tags = f"{self.host}/api/tags"

    def is_available(self) -> Tuple[bool, str]:
        """
        Check if Ollama server is running and the model is available.

        Returns:
            Tuple of (is_available, status_message)
        """
        try:
            response = requests.get(self.api_tags, timeout=5)
            if response.status_code != 200:
                return False, f"Ollama server returned status {response.status_code}"

            data = response.json()
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            model_names = [m.get("name", "") for m in data.get("models", [])]

            if (self.model not in models
                    and f"{self.model}:latest" not in model_names):
                # Check if any variant of the model exists
                model_base = self.model.split(":")[0]
                if not any(model_base in m for m in models):
                    return False, f"Model '{self.model}' not found. Available: {models}"

            return True, "Ollama is running and model is available"

        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama. Is it running? Start with: ollama serve"
        except requests.exceptions.Timeout:
            return False, "Ollama server timeout"
        except Exception as e:
            return False, f"Error checking Ollama: {str(e)}"

    def encode_image(self, image_path: str) -> Optional[str]:
        """
        Encode an image file to base64 for transmission to Ollama.

        Args:
            image_path: Path to the image file

        Returns:
            Base64-encoded image string or None if failed
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"Image not found: {image_path}")
                return None

            with open(path, "rb") as f:
                image_data = f.read()

            return base64.b64encode(image_data).decode("utf-8")

        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            return None

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an image and prompt to LLaVA for visual analysis.

        This is the core method that implements the VLM execution step
        of the Visual-Time-Series Reasoning Pipeline.

        Args:
            image_path: Path to the dashboard snapshot image
            prompt: The user's question or analysis request
            system_prompt: Optional system context for the model

        Returns:
            Dict with 'success', 'response', and 'error' keys
        """
        # Check availability first
        available, status = self.is_available()
        if not available:
            return {
                "success": False,
                "response": None,
                "error": status
            }

        # Encode the image
        image_b64 = self.encode_image(image_path)
        if not image_b64:
            return {
                "success": False,
                "response": None,
                "error": f"Failed to load image: {image_path}"
            }

        # Construct the full prompt with system context
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Build the request payload for Ollama
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "images": [image_b64],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1024
            }
        }

        try:
            logger.info(f"Sending request to Ollama ({self.model})...")
            response = requests.post(
                self.api_generate,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                error_msg = f"Ollama returned status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except Exception:
                    pass
                return {
                    "success": False,
                    "response": None,
                    "error": error_msg
                }

            result = response.json()
            ai_response = result.get("response", "")

            if not ai_response:
                return {
                    "success": False,
                    "response": None,
                    "error": "Empty response from Ollama"
                }

            logger.info("Successfully received VLM response")
            return {
                "success": True,
                "response": ai_response.strip(),
                "error": None,
                "model": self.model,
                "eval_count": result.get("eval_count", 0),
                "total_duration": result.get("total_duration", 0)
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": None,
                "error": f"Request timed out after {self.timeout}s. Try a simpler question."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": None,
                "error": "Lost connection to Ollama. Is it still running?"
            }
        except Exception as e:
            logger.exception("Unexpected error during VLM analysis")
            return {
                "success": False,
                "response": None,
                "error": f"Unexpected error: {str(e)}"
            }

    def chat(
        self,
        question: str,
        image_path: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        High-level chat interface for the AI Dashboard Assistant.

        This method wraps analyze_image with financial-specific prompting
        and context handling.

        Args:
            question: User's question about the dashboard
            image_path: Path to the latest dashboard snapshot
            context: Optional additional context (e.g., CSV metadata)

        Returns:
            Dict with the AI response or error information
        """
        from .prompt_templates import PromptTemplates

        # Build the analysis prompt
        prompt = PromptTemplates.build_chat_prompt(question, context)
        system_prompt = PromptTemplates.FINANCIAL_ANALYST_SYSTEM

        # Execute VLM analysis
        result = self.analyze_image(image_path, prompt, system_prompt)

        return result

    def generate_snapshot_summary(self, image_path: str) -> Dict[str, Any]:
        """
        Generate an automatic summary description of a dashboard snapshot.

        This is used to populate the ai_summary field when a snapshot is saved.

        Args:
            image_path: Path to the snapshot image

        Returns:
            Dict with the generated summary or error
        """
        from .prompt_templates import PromptTemplates

        prompt = PromptTemplates.SNAPSHOT_SUMMARY_PROMPT
        system_prompt = PromptTemplates.FINANCIAL_ANALYST_SYSTEM

        return self.analyze_image(image_path, prompt, system_prompt)


# Singleton instance for easy access
_default_client: Optional[OllamaVLMClient] = None


def get_vlm_client() -> OllamaVLMClient:
    """Get or create the default VLM client instance."""
    global _default_client
    if _default_client is None:
        _default_client = OllamaVLMClient()
    return _default_client
