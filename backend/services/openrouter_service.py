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
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
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

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )

            if response.status_code != 200:
                error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)

            data = response.json()

            # Extract response content and usage
            result = {
                "content": data["choices"][0]["message"]["content"],
                "usage": {
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                    "total_tokens": data["usage"]["total_tokens"]
                }
            }

            logger.debug(f"LLM call succeeded. Tokens used: {result['usage']['total_tokens']}")
            return result

        except httpx.TimeoutException:
            error_msg = f"OpenRouter API timeout after {self.timeout}s"
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.HTTPError as e:
            error_msg = f"OpenRouter API HTTP error: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except KeyError as e:
            error_msg = f"Invalid OpenRouter response format: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error calling OpenRouter API: {e}")
            raise

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
