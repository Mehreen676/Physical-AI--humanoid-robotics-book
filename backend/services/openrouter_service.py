"""
OpenRouter LLM service integration.

Provides OpenRouterClient for calling LLM models via OpenRouter API.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for interacting with OpenRouter LLM API."""

    def __init__(self, api_key: str, model_name: str, base_url: str = None):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            model_name: Model name (e.g., 'claude-3-5-sonnet')
            base_url: Optional base URL override
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url or settings.openrouter_url
        self.timeout = 30.0

    async def call(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call OpenRouter LLM API.

        Args:
            prompt: The prompt/message to send
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters

        Returns:
            Dictionary with 'content' and 'usage' keys

        Raises:
            Exception: If API call fails
        """
        try:
            # Validate API key
            if not self.api_key or self.api_key.startswith("sk-or-v1-") is False:
                error_msg = f"Invalid OpenRouter API key format. Expected sk-or-v1-* format"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Validate model name
            if not self.model_name:
                error_msg = "Model name is not configured"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Calling OpenRouter API with model: {self.model_name}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://huggingface.co",
                "X-Title": "BookRAGAgent"
            }

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            logger.debug(f"Request payload: model={self.model_name}, temp={temperature}, max_tokens={max_tokens}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )

            logger.info(f"OpenRouter API response status: {response.status_code}")

            if response.status_code != 200:
                error_text = response.text[:500]  # Truncate for logging
                error_msg = f"OpenRouter API error: {response.status_code} - {error_text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            try:
                data = response.json()
            except Exception as e:
                error_msg = f"Failed to parse OpenRouter response as JSON: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Validate response structure
            if "choices" not in data or not data["choices"]:
                error_msg = f"Invalid OpenRouter response: no choices in response"
                logger.error(f"Response: {data}")
                raise Exception(error_msg)

            try:
                answer_content = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                error_msg = f"Failed to extract answer from OpenRouter response: {e}"
                logger.error(f"Response structure: {data}")
                raise Exception(error_msg)

            # Extract response content and usage (with defaults)
            usage = data.get("usage", {})
            result = {
                "content": answer_content,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
            }

            logger.info(f"LLM call succeeded. Model: {self.model_name}, Tokens: {result['usage']['total_tokens']}")
            return result

        except httpx.TimeoutException as e:
            error_msg = f"OpenRouter API timeout after {self.timeout}s"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except httpx.HTTPError as e:
            error_msg = f"OpenRouter API HTTP error: {str(e)[:200]}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except (ValueError, Exception) as e:
            error_msg = f"OpenRouter API call failed: {str(e)[:200]}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    async def health_check(self) -> Dict[str, str]:
        """
        Check OpenRouter API health.

        Returns:
            Dictionary with 'status' key ('ok' or 'error')
        """
        try:
            result = await self.call(
                prompt="Test",
                max_tokens=10,
                temperature=0.5
            )
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"OpenRouter health check failed: {e}")
            return {"status": "error", "message": str(e)}
