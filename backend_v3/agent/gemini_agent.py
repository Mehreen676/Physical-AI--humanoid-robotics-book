"""
Gemini Agent using Google's Generative AI API.

Supports:
1) New Google GenAI SDK (recommended): from google import genai
2) Legacy SDK fallback: import google.generativeai as genai_legacy

IMPORTANT:
- Strict grounding (book context only).
- Sanitizes model output to remove "(Relevance: x.xx)" / "(Score: x.xx)".
- Handles quota/rate-limit gracefully (no noisy prints).
- Robust conversation_history handling (avoids "'str' object has no attribute 'get'").
"""

from __future__ import annotations

import re
import time
from typing import List, Dict, Optional, Any, Tuple


REFUSAL_PHRASE = "I cannot answer this question based on the provided context."


class GeminiAgent:
    """Agent using Google Gemini API for grounded chat completion."""

    _MODEL_FALLBACKS = [
        # prefer newer models first (availability depends on your API/quota)
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = (api_key or "").strip()
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
        self._model_candidates: List[str] = [self.model_name] + [
            m for m in self._MODEL_FALLBACKS if m != self.model_name
        ]

        # output sanitizer
        self._strip_metrics_pat = re.compile(
            r"\s*\((?:relevance|score)\s*:\s*[-+]?\d*\.?\d+\)\s*",
            re.IGNORECASE,
        )

        # Try new SDK first (google-genai)
        try:
            from google import genai  # type: ignore

            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
                self._use_new_sdk = True
            else:
                self._use_new_sdk = False
        except Exception:
            self._use_new_sdk = False

        # Legacy fallback (google-generativeai)
        if not self._use_new_sdk:
            try:
                import google.generativeai as genai_legacy  # type: ignore

                self._genai_legacy = genai_legacy
                if self.api_key:
                    genai_legacy.configure(api_key=self.api_key)
                self._select_working_model_legacy()
            except Exception:
                # If nothing works, we still keep agent alive (it will refuse)
                self._legacy_model = None

    # -------------------------
    # Helpers
    # -------------------------
    def _sanitize_output(self, text: str) -> str:
        if not text:
            return text
        cleaned = re.sub(self._strip_metrics_pat, " ", text)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
        return cleaned

    def _is_rate_limit(self, err: Exception) -> bool:
        msg = str(err).lower()
        return ("429" in msg) or ("quota" in msg) or ("rate limit" in msg) or ("exceeded" in msg)

    def _is_model_missing(self, err: Exception) -> bool:
        msg = str(err).lower()
        return ("not found" in msg) or ("is not supported" in msg) or ("404" in msg)

    def _safe_turn_to_qa(self, turn: Any) -> Tuple[str, str]:
        """
        DB history sometimes returns dicts, sometimes strings, sometimes tuples.
        This prevents: "'str' object has no attribute 'get'".
        """
        # dict-like
        if isinstance(turn, dict):
            q = str(turn.get("question", "") or "")
            a = str(turn.get("answer", "") or "")
            return q, a

        # tuple/list like: (question, answer, ...)
        if isinstance(turn, (list, tuple)) and len(turn) >= 2:
            return str(turn[0] or ""), str(turn[1] or "")

        # string fallback
        if isinstance(turn, str):
            # treat as raw transcript
            return "", turn

        return "", ""

    def _build_prompt(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Any]] = None,
    ) -> str:
        prompt_parts = [self.system_instruction, "\n\n"]

        if conversation_history:
            prompt_parts.append("Previous conversation:\n")
            for turn in conversation_history[-3:]:
                q, a = self._safe_turn_to_qa(turn)
                if q:
                    prompt_parts.append(f"User: {q}\n")
                if a:
                    prompt_parts.append(f"Assistant: {a}\n")
            prompt_parts.append("\n")

        prompt_parts.append(f"Context from book:\n{context}\n\n")
        prompt_parts.append(f"User question: {question}\n\n")
        prompt_parts.append("Answer (cite sources using ONLY [Chapter: ..., Section: ...]):")

        return "".join(prompt_parts)

    # -------------------------
    # Legacy model selection
    # -------------------------
    def _select_working_model_legacy(self) -> None:
        last_err: Optional[Exception] = None
        for m in self._model_candidates:
            try:
                self._legacy_model = self._genai_legacy.GenerativeModel(m)
                self.model_name = m
                return
            except Exception as e:
                last_err = e

        self._legacy_model = None
        self._last_model_error = last_err

    # -------------------------
    # Main call
    # -------------------------
    def create_chat_completion(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Any]] = None,
    ) -> str:
        # hard refusal if no context
        if not context or not str(context).strip():
            return REFUSAL_PHRASE

        # if API key missing, never call external
        if not self.api_key:
            return REFUSAL_PHRASE

        prompt = self._build_prompt(question, context, conversation_history)

        # New SDK path
        if self._use_new_sdk and self._client is not None:
            try:
                from google.genai import types  # type: ignore

                for m in self._model_candidates:
                    for attempt in range(2):
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
                            if self._is_model_missing(inner):
                                break
                            if self._is_rate_limit(inner) and attempt == 0:
                                time.sleep(1.2)
                                continue
                            return REFUSAL_PHRASE

                return REFUSAL_PHRASE
            except Exception:
                return REFUSAL_PHRASE

        # Legacy SDK path
        try:
            if self._legacy_model is None:
                self._select_working_model_legacy()

            for m in self._model_candidates:
                for attempt in range(2):
                    try:
                        if self._legacy_model is None or self.model_name != m:
                            self._legacy_model = self._genai_legacy.GenerativeModel(m)
                            self.model_name = m

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
                            return self._sanitize_output(str(text).strip())
                        break
                    except Exception as inner:
                        if self._is_model_missing(inner):
                            break
                        if self._is_rate_limit(inner) and attempt == 0:
                            time.sleep(1.2)
                            continue
                        return REFUSAL_PHRASE

            return REFUSAL_PHRASE
        except Exception:
            return REFUSAL_PHRASE

    def __repr__(self) -> str:
        return f"GeminiAgent(model={self.model_name}, sdk={'new' if self._use_new_sdk else 'legacy'})"
