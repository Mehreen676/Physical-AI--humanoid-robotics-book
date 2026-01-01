"""
Google Gemini LLM Service for RAG chatbot backend.

Handles text generation and validation using Google Gemini API.
"""

import google.generativeai as genai
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google Gemini API key
            model_name: Model name (default: gemini-1.5-flash)
        """
        self.api_key = api_key
        self.model_name = model_name

        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_name)

        logger.info(f"Gemini client initialized with model: {model_name}")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using Gemini.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)

        Returns:
            Generated text
        """
        try:
            response = self.client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

            if response.text:
                logger.debug(f"Gemini generated response: {response.text[:100]}...")
                return response.text
            else:
                logger.warning("Gemini returned empty response")
                return ""

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise

    def validate_answer(
        self,
        question: str,
        answer: str,
        context: str,
        temperature: float = 0.3,
    ) -> dict:
        """
        Validate if answer is grounded in context.

        Args:
            question: Original question
            answer: Generated answer
            context: Retrieved context chunks
            temperature: Lower temperature for validation

        Returns:
            Validation result with is_grounded flag
        """
        validation_prompt = f"""You are a fact-checking assistant. Analyze if the following answer is grounded in the provided context.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
{answer}

Respond with ONLY valid JSON (no markdown, no code blocks):
{{"is_grounded": boolean, "reasoning": "brief explanation"}}

If the answer is supported by the context, set is_grounded to true. Otherwise, set it to false."""

        try:
            response = self.client.generate_content(
                validation_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=256,
                    temperature=temperature,
                ),
            )

            import json

            # Parse JSON response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)
            logger.debug(f"Validation result: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation response as JSON: {e}")
            return {"is_grounded": False, "reasoning": "Validation response invalid"}
        except Exception as e:
            logger.error(f"Answer validation failed: {e}")
            return {"is_grounded": False, "reasoning": str(e)}

    def health_check(self) -> dict:
        """
        Check Gemini API connection and status.

        Returns:
            Health check result
        """
        try:
            # Try a simple generation to verify API works
            response = self.client.generate_content(
                "Say 'ok'",
                generation_config=genai.types.GenerationConfig(max_output_tokens=10),
            )

            if response.text:
                logger.info("Gemini API health check passed")
                return {
                    "status": "ok",
                    "service": "gemini",
                    "model": self.model_name,
                }
            else:
                logger.warning("Gemini API returned empty response")
                return {
                    "status": "error",
                    "service": "gemini",
                    "error": "Empty response",
                }

        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}")
            return {
                "status": "error",
                "service": "gemini",
                "error": str(e),
            }
