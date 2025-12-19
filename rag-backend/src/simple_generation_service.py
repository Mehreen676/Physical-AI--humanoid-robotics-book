"""
Simple Content Generation Service for RAG pipeline
"""

import logging
from typing import Dict, Optional
from src.config import get_settings

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    logger.warning("OpenAI not installed; install with: pip install openai")


def generate_response_with_context(question: str, context: str) -> str:
    """
    Generate response using LLM with RAG context.

    Args:
        question: User question
        context: Retrieved context from vector store

    Returns:
        Generated response string
    """
    try:
        settings = get_settings()

        # Check if OpenAI API key is available
        if not settings.openai_api_key or settings.openai_api_key == "sk-proj-default":
            # Return a response based on the context without calling OpenAI
            logger.warning("⚠️ OpenAI API key not configured, generating response from context only")
            return f"Based on the provided context: {context}\n\nQuestion: {question}\n\n[Note: OpenAI API key not configured - this is a context-based response without LLM generation]"

        # Use OpenAI API with the key from environment variables
        client = OpenAI(api_key=settings.openai_api_key)

        prompt = f"""You are a helpful educational assistant. Answer the question based on the provided context.

Context information:
{context}

Question: {question}

Provide a comprehensive, accurate answer based on the context provided."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful educational assistant. Answer questions based on the provided context. Be concise but comprehensive."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"❌ Generation failed: {e}", exc_info=True)
        return "Sorry, I couldn't generate a response at this time. Please try again later."