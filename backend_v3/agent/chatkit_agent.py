"""ChatKit agent using OpenAI Agents SDK with strict grounding."""

from typing import List, Dict, Optional
from openai import OpenAI


class ChatKitAgent:
    """OpenAI Agents SDK wrapper for grounded book Q&A."""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Initialize ChatKit agent.

        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4-turbo-preview, gpt-4o, gpt-4)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = 0.0  # Deterministic responses

    def get_system_instructions(self) -> str:
        """
        Get system instructions enforcing strict grounding.

        Returns:
            System instruction string
        """
        return """You are a helpful assistant that answers questions about a book.

CRITICAL GROUNDING RULES:
1. Use ONLY the provided context to answer questions
2. If the answer is not in the context, respond EXACTLY: "I cannot answer this question based on the book content provided."
3. Do NOT use external knowledge or prior information
4. Do NOT infer, speculate, or extrapolate beyond the context
5. Cite chapter and section when possible using format: [Chapter X, Section Y]
6. Keep answers concise and directly address the question
7. If context is ambiguous, acknowledge uncertainty

CONTEXT FORMAT:
You will receive retrieved book chunks with metadata.
Each chunk includes:
- Chapter name
- Section name
- Text content
- Relevance score

These chunks are your SOLE source of information. Answer only from this context."""

    def create_chat_completion(
        self,
        question: str,
        context: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Generate grounded answer using ChatKit.

        Args:
            question: User question
            context: Formatted context from retrieved chunks
            conversation_history: Optional previous turns

        Returns:
            Generated answer string
        """
        messages = [
            {"role": "system", "content": self.get_system_instructions()},
        ]

        # Add conversation history (last 3 turns for context)
        if conversation_history:
            for turn in conversation_history[-3:]:
                messages.append({"role": "user", "content": turn.get("question", "")})
                messages.append({"role": "assistant", "content": turn.get("answer", "")})

        # Add current context and question
        user_message = f"""CONTEXT FROM BOOK:
{context}

QUESTION: {question}

Answer based ONLY on the context above:"""

        messages.append({"role": "user", "content": user_message})

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=1000
        )

        return response.choices[0].message.content
