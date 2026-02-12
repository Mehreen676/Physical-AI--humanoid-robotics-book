from __future__ import annotations

import os
import time
import hashlib
from dataclasses import dataclass
from typing import List, Optional, Any, Dict

import requests

try:
    import numpy as np
except Exception:
    np = None


def _normalize_model(name: str) -> str:
    n = (name or "").strip()
    if not n:
        n = "models/gemini-embedding-001"
    if not (n.startswith("models/") or n.startswith("tunedModels/")):
        n = "models/" + n
    return n


def _env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


@dataclass
class EmbeddingConfig:
    api_key: str
    model: str
    dimension: int = 3072
    timeout_s: int = 30
    max_retries: int = 6
    base_backoff_s: float = 0.8
    max_backoff_s: float = 8.0


class GeminiEmbeddingService:
    """
    Backend retrieval embedding service.
    Must expose:
      - embed_query(text) -> List[float]
      - (optional) embed_text / embed aliases
      - dimension
    """

    def __init__(self, cfg: EmbeddingConfig):
        self.api_key = cfg.api_key
        self.model = cfg.model
        self.dimension = cfg.dimension
        self.timeout_s = cfg.timeout_s
        self.max_retries = cfg.max_retries
        self.base_backoff_s = cfg.base_backoff_s
        self.max_backoff_s = cfg.max_backoff_s

        model_id = self.model.split("/", 1)[1]
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:embedContent"

    def _should_retry(self, status: int) -> bool:
        return status in (429, 500, 502, 503, 504)

    def embed_query(self, text: str) -> List[float]:
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        payload: Dict[str, Any] = {
            "model": self.model,
            "content": {"parts": [{"text": text}]},
            "output_dimensionality": self.dimension,
        }

        last_err: Optional[str] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                r = requests.post(self.url, headers=headers, json=payload, timeout=self.timeout_s)

                if r.status_code >= 400:
                    # retryable?
                    if self._should_retry(r.status_code):
                        last_err = f"embedContent failed ({r.status_code}): {r.text}"
                        backoff = min(self.max_backoff_s, self.base_backoff_s * (2 ** (attempt - 1)))
                        time.sleep(backoff)
                        continue

                    raise RuntimeError(f"embedContent failed ({r.status_code}): {r.text}")

                data = r.json()
                if not isinstance(data, dict) or "embedding" not in data:
                    raise RuntimeError(f"Unexpected embedding response: {data}")

                emb = data["embedding"]
                if not isinstance(emb, dict) or "values" not in emb:
                    raise RuntimeError(f"Unexpected embedding response: {data}")

                values = emb["values"]
                if not isinstance(values, list) or not values:
                    raise RuntimeError(f"Unexpected embedding response: {data}")

                return values

            except requests.RequestException as e:
                last_err = f"Request error: {e}"
                backoff = min(self.max_backoff_s, self.base_backoff_s * (2 ** (attempt - 1)))
                time.sleep(backoff)

        raise RuntimeError(last_err or "embedContent failed after retries")

    # aliases (some code calls these)
    def embed_text(self, text: str) -> List[float]:
        return self.embed_query(text)

    def embed(self, text: str) -> List[float]:
        return self.embed_query(text)


class MockEmbeddingService:
    def __init__(self, dimension: int = 3072):
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        # deterministic vector for same text
        if np is None:
            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            seed = int(h[:8], 16)
            return [((seed + i) % 1000) / 1000.0 for i in range(self.dimension)]

        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        seed = int(h[:8], 16)
        rng = np.random.RandomState(seed)
        v = rng.randn(self.dimension)
        n = float(np.linalg.norm(v))
        if n > 0:
            v = v / n
        return v.astype(float).tolist()

    def embed_text(self, text: str) -> List[float]:
        return self.embed_query(text)

    def embed(self, text: str) -> List[float]:
        return self.embed_query(text)


def get_embedding_service(
    use_mock: bool = False,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    expected_dim: Optional[int] = None,
):
    """
    Signature MUST match retriever.py call:
      get_embedding_service(use_mock=..., api_key=...)
    """
    dim = int(expected_dim or os.getenv("EXPECTED_EMBEDDING_DIM", "3072"))

    # allow forcing mock via env too
    if use_mock or _env_bool("USE_MOCK_EMBEDDINGS", False):
        return MockEmbeddingService(dim)

    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")

    m = _normalize_model(model or os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"))

    cfg = EmbeddingConfig(
        api_key=key,
        model=m,
        dimension=dim,
        timeout_s=int(os.getenv("GEMINI_EMBED_TIMEOUT_S", "30")),
        max_retries=int(os.getenv("GEMINI_EMBED_MAX_RETRIES", "6")),
        base_backoff_s=float(os.getenv("GEMINI_EMBED_BASE_BACKOFF_S", "0.8")),
        max_backoff_s=float(os.getenv("GEMINI_EMBED_MAX_BACKOFF_S", "8.0")),
    )
    return GeminiEmbeddingService(cfg)
