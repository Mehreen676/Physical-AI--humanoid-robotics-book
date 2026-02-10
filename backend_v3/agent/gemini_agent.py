"""
Gemini Agent using Google's Generative AI API.

Supports:
1) New Google GenAI SDK (recommended): from google import genai
2) Legacy SDK fallback: import google.generativeai as genai_legacy

IMPORTANT:
- Strict grounding (book context only).
- Sanitizes model output to remove "(Relevance: x.xx)" / "(Score: x.xx)".
- Handles quota/rate-limit gracefully (no noisy prints).
"""

from __future__ import annotations

import re
import time
from typing import List, Dict, Optional, Any


class GeminiAgent:
    """Agent using Google Gemini API for grounded chat completion."""

    _MODEL_FALLBACKS = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model

        self.system_instruction = """You are a helpful AI assistant for a Physical AI & Humanoid Robotics textbook.

CRITICAL RULES:
1) Answer ONLY using the provided context from the book.
2) If the answer is not in the context, respond exactly:
   "I cannot answer this question based on the provided context."
3) Always cite sources using ONLY this format:
   [Chapter: <chapter>, Section: <section>]
4) Do NOT include any scores or relevance values (e.g., do not write "(Relevance: 0.04)" or "(Score: 0.12)").
5) Be concise and accurate. Do not add extra info beyond context.
Temperature is 0 for deterministic responses.
"""

        self._use_new_sdk = False
        self._client = None
        self._legacy_model = None

        try:
            from google import genai  # type: ignore
            self._genai = genai
            self._client = genai.Client(api_key=self.api_key)
            self._use_new_sdk = True
        except Exception:
            import google.generativeai as genai_legacy  # type: ignore
            self._genai_legacy = genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            self._use_new_sdk = False

        self._select_working_model()

        self._strip_metrics_pat = re.compile(
            r"\s*\((?:relevance|score)\s*:\s*[-+]?\d*\.?\d+\)\s*",
            re.IGNORECASE,
        )

    def _select_working_model(self) -> None:
        candidates = [self.model_name] + [m for m in self._MODEL_FALLBACKS if m != self.model_name]

        if self._use_new_sdk:
            self._model_candidates = candidates
            return

        last_err: Optional[Exception] = None
        for m in candidates:
            try:
                self._legacy_model = self._genai_legacy.GenerativeModel(m)
                self.model_name = m
                self._model_candidates = candidates
                return
            except Exception as e:
                last_err = e

        self._legacy_model = None
        self._model_candidates = candidates
        self._last_model_error = last_err

    def _build_prompt(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        prompt_parts = [self.system_instruction, "\n\n"]

        if conversation_history:
            prompt_parts.append("Previous conversation:\n")
            for turn in conversation_history[-3:]:
                prompt_parts.append(f"User: {turn.get('question', '')}\n")
                prompt_parts.append(f"Assistant: {turn.get('answer', '')}\n")
            prompt_parts.append("\n")

        prompt_parts.append(f"Context from book:\n{context}\n\n")
        prompt_parts.append(f"User question: {question}\n\n")
        prompt_parts.append("Answer (cite sources using ONLY [Chapter: ..., Section: ...]):")

        return "".join(prompt_parts)

    def _sanitize_output(self, text: str) -> str:
        if not text:
            return text
        cleaned = re.sub(self._strip_metrics_pat, " ", text)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
        return cleaned

    def _is_rate_limit(self, err: Exception) -> bool:
        msg = str(err).lower()
        return ("429" in msg) or ("quota" in msg) or ("rate limit" in msg) or ("exceeded" in msg)

    def create_chat_completion(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        if not context or not context.strip():
            return "I cannot answer this question based on the provided context."

        prompt = self._build_prompt(question, context, conversation_history)

        # New SDK
        if self._use_new_sdk:
            try:
                from google.genai import types  # type: ignore

                # small backoff loop only for 429
                for m in getattr(self, "_model_candidates", [self.model_name]):
                    for attempt in range(2):  # 2 tries per model
                        try:
                            resp = self._client.models.generate_content(
                                model=m,
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    temperature=0.0,
                                    top_p=0.95,
                                    top_k=40,
                                    max_output_tokens=768,
                                ),
                            )
                            text = getattr(resp, "text", None)
                            if text and str(text).strip():
                                self.model_name = m
                                return self._sanitize_output(str(text).strip())
                            break
                        except Exception as inner:
                            msg = str(inner).lower()

                            # model not found → try next
                            if ("not found" in msg) or ("is not supported" in msg) or ("404" in msg):
                                break

                            # 429/quota → brief backoff then continue attempt
                            if self._is_rate_limit(inner) and attempt == 0:
                                time.sleep(1.2)
                                continue

                            # other errors
                            return "I cannot answer this question based on the provided context."

                return "I cannot answer this question based on the provided context."

            except Exception:
                return "I cannot answer this question based on the provided context."

        # Legacy SDK
        try:
            if self._legacy_model is None:
                self._select_working_model()

            for m in getattr(self, "_model_candidates", [self.model_name]):
                for attempt in range(2):
                    try:
                        if self._legacy_model is None or self.model_name != m:
                            self._legacy_model = self._genai_legacy.GenerativeModel(m)

                        response = self._legacy_model.generate_content(
                            prompt,
                            generation_config=self._genai_legacy.GenerationConfig(
                                temperature=0.0,
                                top_p=0.95,
                                top_k=40,
                                max_output_tokens=768,
                            ),
                        )
                        text = getattr(response, "text", None)
                        if text and str(text).strip():
                            self.model_name = m
                            return self._sanitize_output(str(text).strip())
                        break

                    except Exception as inner:
                        msg = str(inner).lower()
                        if ("not found" in msg) or ("is not supported" in msg) or ("404" in msg):
                            break

                        if self._is_rate_limit(inner) and attempt == 0:
                            time.sleep(1.2)
                            continue

                        return "I cannot answer this question based on the provided context."

            return "I cannot answer this question based on the provided context."

        except Exception:
            return "I cannot answer this question based on the provided context."

    def __repr__(self) -> str:
        return f"GeminiAgent(model={self.model_name}, sdk={'new' if self._use_new_sdk else 'legacy'})"
