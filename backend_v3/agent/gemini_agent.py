"""Gemini Agent using Google's Generative AI API (FREE)."""

import google.generativeai as genai
from typing import List, Dict, Optional


class GeminiAgent:
    """Agent using Google Gemini API for chat completion."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """
        Initialize Gemini agent.

        Args:
            api_key: Google Gemini API key
            model: Model name (default: gemini-1.5-flash - FREE)
        """
        self.api_key = api_key
        self.model_name = model

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

        # System instruction for grounding
        self.system_instruction = """You are a helpful AI assistant for a Physical AI & Humanoid Robotics textbook.

CRITICAL RULES:
1. Answer ONLY using the provided context from the book
2. If the answer is not in the context, respond: "I cannot answer this question based on the provided context."
3. Always cite sources using [Chapter X, Section Y] format
4. Be concise and accurate
5. Do not add any information beyond what's in the context
6. Temperature is 0 for deterministic responses"""

    def create_chat_completion(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate answer using Gemini.

        Args:
            question: User question
            context: Retrieved context from book
            conversation_history: Optional conversation history

        Returns:
            Generated answer
        """
        # Build prompt
        prompt_parts = [self.system_instruction, "\n\n"]

        # Add conversation history if available
        if conversation_history:
            prompt_parts.append("Previous conversation:\n")
            for turn in conversation_history[-3:]:  # Last 3 turns
                prompt_parts.append(f"User: {turn.get('question', '')}\n")
                prompt_parts.append(f"Assistant: {turn.get('answer', '')}\n")
            prompt_parts.append("\n")

        # Add context and question
        prompt_parts.append(f"Context from book:\n{context}\n\n")
        prompt_parts.append(f"User question: {question}\n\n")
        prompt_parts.append("Answer (cite sources using [Chapter X, Section Y]):")

        prompt = "".join(prompt_parts)

        # Generate response
        generation_config = genai.GenerationConfig(
            temperature=0.0,  # Deterministic
            top_p=0.95,
            top_k=40,
            max_output_tokens=1024,
        )

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            if response.text:
                return response.text.strip()
            else:
                return "I cannot answer this question based on the provided context."

        except Exception as e:
            print(f"Gemini API error: {e}")
            return "I cannot answer this question based on the provided context."

    def __repr__(self):
        return f"GeminiAgent(model={self.model_name})"
