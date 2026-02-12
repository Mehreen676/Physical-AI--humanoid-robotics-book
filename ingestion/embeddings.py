"""
Ingestion embeddings provider (Gemini) — REST based (stable)
Fixes: AttributeError: 'GeminiEmbedder' has no attribute 'embed_query'

Env:
- GEMINI_API_KEY (required)
- GEMINI_EMBEDDING_MODEL (default: models/gemini-embedding-001)
- EXPECTED_EMBEDDING_DIM (default: 3072)
- USE_MOCK_EMBEDDINGS (default: false)
"""

import os
import time
import hashlib
from typing import List
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


class GeminiEmbedder:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY missing")

        self.api_key = api_key
        self.model = _normalize_model(os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"))

        # must match Qdrant collection vector size
        self._dimension = int(os.getenv("EXPECTED_EMBEDDING_DIM", "3072"))

        self._min_request_interval = float(os.getenv("GEMINI_RATE_LIMIT_SECONDS", "0.0"))
        self._last_request_time = 0.0

        model_id = self.model.split("/", 1)[1]
        self._url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:embedContent"

    @property
    def dimension(self) -> int:
        return self._dimension

    def _enforce_rate_limit(self):
        if self._min_request_interval <= 0:
            return
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def embed_text(self, text: str) -> List[float]:
        self._enforce_rate_limit()

        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        payload = {
            "model": self.model,
            "content": {"parts": [{"text": text}]},
            "output_dimensionality": self._dimension,
        }

        r = requests.post(self._url, headers=headers, json=payload, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"embedContent failed ({r.status_code}): {r.text}")

        data = r.json()
        values = None
        if isinstance(data, dict):
            emb = data.get("embedding")
            if isinstance(emb, dict):
                values = emb.get("values")

        if not values:
            raise RuntimeError(f"Unexpected embedding response: {data}")

        return values

    # ✅ ingestion expects this
    def embed_query(self, text: str) -> List[float]:
        return self.embed_text(text)

    def embed(self, text: str) -> List[float]:
        return self.embed_text(text)


class MockEmbedder:
    def __init__(self, dimension: int = 3072):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        if np is None:
            h = hashlib.md5(text.encode("utf-8")).hexdigest()
            seed = int(h[:8], 16)
            return [((seed + i) % 1000) / 1000.0 for i in range(self._dimension)]

        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        seed = int(h[:8], 16)
        rng = np.random.RandomState(seed)
        v = rng.randn(self._dimension)
        n = float(np.linalg.norm(v))
        if n > 0:
            v = v / n
        return v.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_text(text)

    def embed(self, text: str) -> List[float]:
        return self.embed_text(text)


def get_embedder():
    use_mock = os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"
    if use_mock:
        return MockEmbedder(int(os.getenv("EXPECTED_EMBEDDING_DIM", "3072")))
    return GeminiEmbedder()
