"""
Small test script to validate Qdrant search.

Run:
  py -m ingestion.test_search
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any, List

from dotenv import load_dotenv

# -------------------------------------------------------------------
# Force-load .env from PROJECT ROOT (parent of /ingestion folder)
# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT / ".env"

# override=True so latest .env values always win
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import AFTER loading env
from ingestion.embeddings import get_embedder
from ingestion.vector_store import QdrantVectorStore


def _get_expected_dim_from_env() -> int | None:
    v = os.environ.get("EXPECTED_EMBEDDING_DIM")
    if not v:
        return None
    try:
        return int(v.strip())
    except ValueError:
        return None


def _embed_text(embedder: Any, text: str) -> List[float]:
    """
    Handles different embedder method names across versions.
    """
    candidates = ["embed_text", "embed", "embed_query", "get_embedding", "encode"]
    for name in candidates:
        fn = getattr(embedder, name, None)
        if callable(fn):
            try:
                out = fn(text)
                if isinstance(out, dict):
                    for k in ("embedding", "vector", "values"):
                        if k in out and isinstance(out[k], list):
                            return out[k]
                if isinstance(out, list):
                    return out
            except TypeError:
                continue

    raise AttributeError(
        "Embedder method not found. Tried: embed_text/embed/embed_query/get_embedding/encode"
    )


def detect_dim() -> int:
    expected = _get_expected_dim_from_env()
    if expected:
        logger.info("Using EXPECTED_EMBEDDING_DIM = %s", expected)
        return expected

    embedder = get_embedder()
    v = _embed_text(embedder, "dim probe")
    dim = len(v)
    logger.info("Detected embedding dim = %s", dim)
    return dim


def main() -> None:
    # Helpful debug
    logger.info("CWD = %s", Path.cwd())
    logger.info("PROJECT_ROOT = %s", PROJECT_ROOT)
    logger.info(".env path = %s (exists=%s)", DOTENV_PATH, DOTENV_PATH.exists())

    if not DOTENV_PATH.exists():
        raise RuntimeError(f".env not found at: {DOTENV_PATH}")

    qdrant_url = os.environ.get("QDRANT_URL")
    qdrant_api_key = os.environ.get("QDRANT_API_KEY")
    collection = os.environ.get("COLLECTION_NAME", "data_collection_3072_v2")

    if not qdrant_url:
        raise RuntimeError("QDRANT_URL missing (check .env content + path)")
    if not qdrant_api_key:
        raise RuntimeError("QDRANT_API_KEY missing (check .env content + path)")

    dim = detect_dim()

    store = QdrantVectorStore(
        qdrant_url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=collection,
        vector_dim=dim,
        timeout=60,
    )

    queries = [
        "What is ROS 2?",
        "What is Gazebo simulation?",
        "Explain vision-language-action systems",
        "How do humanoid robots work?",
        "How to control robotic hardware?",
    ]

    for q in queries:
        logger.info("\nQuery: %s", q)
        results = store.search(q, top_k=3)

        for i, r in enumerate(results, start=1):
            payload = r.get("payload") or {}
            meta = payload.get("metadata", {}) if isinstance(payload, dict) else {}

            chapter = meta.get("chapter")
            section = meta.get("section")
            source = meta.get("source_file") or meta.get("source") or meta.get("path")

            text = payload.get("text") if isinstance(payload, dict) else None
            preview = (text or "").replace("\n", " ")[:180]

            logger.info(
                "[%s] score=%.4f | chapter=%s | section=%s | source=%s",
                i,
                float(r.get("score", 0)),
                chapter,
                section,
                source,
            )
            logger.info("     %s", preview)

    logger.info("Done.")


if __name__ == "__main__":
    main()
