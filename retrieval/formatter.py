"""
retrieval/formatter.py

Fixes:
- Missing ResultFormatter methods: format_results, validate_metadata_integrity
- Prevents crashes on bad/partial metadata
- Always returns a DICT (never a string), so downstream .get() calls work.

Expected output shape:
{
  "context": str,
  "chunks": [ { "text": str, "metadata": dict, "score": float, "id": str } ],
  "citations": { "<id>": { ... } }
}
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


@dataclass
class FormattedChunk:
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]


class ResultFormatter:
    """
    Formats Qdrant search results into:
    - context text (joined chunks)
    - chunks list with clean metadata
    - citations map (id -> metadata)
    """

    def __init__(self, max_context_chars: int = 12000):
        self.max_context_chars = max_context_chars

    def validate_metadata_integrity(self, metadata: Any) -> Dict[str, Any]:
        """
        Ensures metadata is a dict and has safe chunk_index/total_chunks.
        If values are missing/invalid, we normalize instead of throwing.
        """
        md = _as_dict(metadata)

        chunk_index = md.get("chunk_index", 0)
        total_chunks = md.get("total_chunks", 1)

        try:
            chunk_index = int(chunk_index)
        except Exception:
            chunk_index = 0

        try:
            total_chunks = int(total_chunks)
        except Exception:
            total_chunks = 1

        if chunk_index < 0:
            chunk_index = 0
        if total_chunks < 1:
            total_chunks = 1

        # If chunk_index is out of range, normalize total_chunks rather than error
        if chunk_index >= total_chunks:
            total_chunks = chunk_index + 1

        md["chunk_index"] = chunk_index
        md["total_chunks"] = total_chunks

        # Common fields (safe defaults)
        md.setdefault("chapter", md.get("doc_title") or md.get("chapter_title") or "")
        md.setdefault("section", md.get("section_title") or md.get("section") or "")
        md.setdefault("source", md.get("file_path") or md.get("source") or "")

        return md

    def format_results(self, results: Any) -> Dict[str, Any]:
        """
        Takes raw Qdrant hits (objects or dicts) and returns a stable dict.
        Downstream code should NEVER get a plain string from here.
        """
        formatted: List[FormattedChunk] = []

        if results is None:
            results = []

        for r in results:
            payload = _get_attr(r, "payload", {})
            payload = _as_dict(payload)

            # text field might be stored as: payload["text"] or payload["content"]
            text = payload.get("text") or payload.get("content") or ""
            if not isinstance(text, str):
                text = str(text)

            metadata = payload.get("metadata", payload.get("meta", {}))
            md = self.validate_metadata_integrity(metadata)

            rid = _get_attr(r, "id", "") or payload.get("id", "")
            rid = str(rid)

            score = _get_attr(r, "score", 0.0)
            try:
                score = float(score)
            except Exception:
                score = 0.0

            formatted.append(
                FormattedChunk(
                    id=rid,
                    score=score,
                    text=text,
                    metadata=md,
                )
            )

        # Build context (respect max length)
        parts: List[str] = []
        total = 0
        for fc in formatted:
            t = fc.text.strip()
            if not t:
                continue
            # +2 for spacing
            if total + len(t) + 2 > self.max_context_chars:
                remaining = self.max_context_chars - total
                if remaining > 50:
                    parts.append(t[:remaining])
                break
            parts.append(t)
            total += len(t) + 2

        context = "\n\n".join(parts).strip()

        chunks_out: List[Dict[str, Any]] = []
        citations: Dict[str, Dict[str, Any]] = {}

        for fc in formatted:
            chunks_out.append(
                {
                    "id": fc.id,
                    "score": fc.score,
                    "text": fc.text,
                    "metadata": fc.metadata,
                }
            )
            citations[fc.id] = {
                "score": fc.score,
                "chapter": fc.metadata.get("chapter", ""),
                "section": fc.metadata.get("section", ""),
                "source": fc.metadata.get("source", ""),
                "chunk_index": fc.metadata.get("chunk_index", 0),
                "total_chunks": fc.metadata.get("total_chunks", 1),
            }

        return {
            "context": context,
            "chunks": chunks_out,
            "citations": citations,
        }
