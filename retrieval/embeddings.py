"""
Embedding service with support for Gemini and Mock embeddings.
Uses direct REST call for embeddings (stable).

Model: models/gemini-embedding-001
Endpoint: v1beta/models/{model}:embedContent
"""

import os
import time
import hashlib
import numpy as np
from abc import ABC, abstractmethod
from typing import List
import requests


class EmbeddingService(ABC):
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass


def _normalize_model(name: str) -> str:
    n = (name or "").strip()
    if not n:
        n = "models/gemini-embedding-001"
    if not (n.startswith("models/") or n.startswith("tunedModels/")):
        n = "models/" + n
    return n


class GeminiEmbeddings(EmbeddingService):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")

        self.api_key = api_key

        # ✅ Force correct model (env optional)
        self.model = _normalize_model(os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"))

        # free tier safety
        self._min_request_interval = 4.0
        self._last_request_time = 0.0

        # most common dim
        self._dimension = int(os.getenv("EMBEDDING_DIM", "768"))

        model_id = self.model.split("/", 1)[1]  # remove "models/"
        self._url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:embedContent"

    def _enforce_rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def embed_query(self, text: str) -> List[float]:
        self._enforce_rate_limit()

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        payload = {
            "model": self.model,
            "content": {"parts": [{"text": text}]},
            "output_dimensionality": self._dimension,
        }

        r = requests.post(self._url, headers=headers, json=payload, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"embedContent failed ({r.status_code}): {r.text}")

        data = r.json()

        # Expected: {"embedding":{"values":[...]}}
        emb = None
        if isinstance(data, dict):
            e = data.get("embedding")
            if isinstance(e, dict):
                emb = e.get("values")

        if not emb:
            raise RuntimeError(f"Unexpected embedding response: {data}")

        return emb

    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbeddings(EmbeddingService):
    def __init__(self, dimension: int = 768):
        self._dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        hash_obj = hashlib.md5(text.encode("utf-8"))
        seed = int(hash_obj.hexdigest(), 16) % (2**32)
        rng = np.random.RandomState(seed)
        v = rng.randn(self._dimension)
        n = np.linalg.norm(v)
        if n > 0:
            v = v / n
        return v.tolist()

    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_service(use_mock: bool = False, api_key: str = "") -> EmbeddingService:
    if use_mock:
        return MockEmbeddings()
    return GeminiEmbeddings(api_key)
