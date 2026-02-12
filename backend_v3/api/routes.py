from __future__ import annotations

import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend_v3.db import SQLiteDB

router = APIRouter()

_AGENT: Any = None
_RETRIEVER: Any = None

_DB = SQLiteDB(os.getenv("SQLITE_DB_PATH", "chatbot.db"))


def set_agent(agent: Any) -> None:
    global _AGENT
    _AGENT = agent


def set_retriever(retriever: Any) -> None:
    global _RETRIEVER
    _RETRIEVER = retriever


def get_agent() -> Any:
    return _AGENT


def get_retriever() -> Any:
    return _RETRIEVER


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    retrieval_mode: str = Field("normal")  # "normal" | "selected_text"
    selected_text: Optional[str] = None
    session_id: Optional[str] = None


class Citation(BaseModel):
    chapter: str = "Unknown"
    section: str = "Unknown"
    text_snippet: str = ""
    score: float = 0.0


class ChatMetadata(BaseModel):
    latency_ms: float = 0.0
    num_chunks: int = 0
    is_refusal: bool = False
    context_length: int = 0
    shortcut: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation]
    retrieval_mode: str
    grounded: bool
    metadata: ChatMetadata


def _normalize_chunks(retrieved_raw: Any) -> List[Dict[str, Any]]:
    """
    Accept many shapes from retriever:
      - list[dict]
      - dict with list under chunks/results/documents/data
    """
    if retrieved_raw is None:
        return []

    if isinstance(retrieved_raw, list):
        return [c for c in retrieved_raw if isinstance(c, dict)]

    if isinstance(retrieved_raw, dict):
        for key in ("chunks", "results", "documents", "data"):
            val = retrieved_raw.get(key)
            if isinstance(val, list):
                return [c for c in val if isinstance(c, dict)]

    return []


def _chunk_text(c: Dict[str, Any]) -> str:
    t = c.get("text") or c.get("content") or ""
    return t if isinstance(t, str) else ""


def _chunk_meta(c: Dict[str, Any]) -> Dict[str, Any]:
    md = c.get("metadata") or {}
    return md if isinstance(md, dict) else {}


def _build_context_and_citations(
    chunks: List[Dict[str, Any]], max_citations: int = 3
) -> Tuple[str, List[Citation]]:
    parts: List[str] = []
    citations: List[Citation] = []

    for c in chunks:
        text = _chunk_text(c).strip()
        if text:
            parts.append(text)

    for c in chunks[:max_citations]:
        md = _chunk_meta(c)
        text = _chunk_text(c).strip()
        citations.append(
            Citation(
                chapter=str(md.get("chapter", "Unknown")),
                section=str(md.get("section", "Unknown")),
                text_snippet=(text[:150] + "...") if len(text) > 150 else text,
                score=float(c.get("score", 0.0) or 0.0),
            )
        )

    context = "\n\n---\n\n".join(parts)
    return context, citations


def _safe_retrieve(question: str, mode: str, selected_text: Optional[str]) -> Any:
    """
    Compatibility layer: some retrievers use query=..., some use question=...
    """
    r = get_retriever()
    if r is None:
        return []

    # try "question" kw first
    try:
        return r.retrieve(
            question=question,
            retrieval_mode=mode,
            selected_text=selected_text if mode == "selected_text" else None,
        )
    except TypeError:
        # fallback to "query"
        return r.retrieve(
            query=question,
            retrieval_mode=mode,
            selected_text=selected_text if mode == "selected_text" else None,
        )


def _is_refusal_text(answer: str) -> bool:
    return "i cannot answer this question based on the provided context." in (answer or "").lower()


def _extractive_fallback_answer(question: str, chunks: List[Dict[str, Any]]) -> Optional[Tuple[str, Citation]]:
    """
    If Gemini refuses or quota fail, we still answer using retrieved book text ONLY.
    We pick the best chunk and extract 1-2 lines/sentences.
    """
    if not chunks:
        return None

    q = (question or "").strip()
    ql = q.lower()

    # try to infer term for glossary-style questions
    term = q
    term = re.sub(r"^\s*(what is|who is|define|explain)\s+", "", term, flags=re.I).strip()
    term = re.sub(r"[?!.]+$", "", term).strip()

    # choose chunk:
    best = None
    best_score = -1.0

    for c in chunks:
        text = _chunk_text(c)
        if not text:
            continue
        tl = text.lower()

        score = float(c.get("score", 0.0) or 0.0)

        # boost if contains term
        if term and term.lower() in tl:
            score += 2.0
        # boost if contains any key words from question
        for w in re.findall(r"[a-z0-9_]+", ql):
            if len(w) >= 3 and w in tl:
                score += 0.1

        if score > best_score:
            best_score = score
            best = c

    if best is None:
        best = chunks[0]

    md = _chunk_meta(best)
    chapter = str(md.get("chapter", "Unknown"))
    section = str(md.get("section", "Unknown"))

    text = _chunk_text(best).strip()
    if not text:
        return None

    # extract small snippet: first bullet/line or first 1-2 sentences
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    snippet = ""
    if lines:
        # if glossary bullet exists, prefer it
        # e.g. "- **ROS 2**: Robot Operating System 2, middleware for robotics."
        for ln in lines[:20]:
            if term and term.lower() in ln.lower():
                snippet = ln
                break
        if not snippet:
            snippet = lines[0]
            if len(lines) > 1 and len(snippet) < 120:
                snippet = snippet + " " + lines[1]

    # final clamp
    snippet = re.sub(r"\s+", " ", snippet).strip()
    snippet = snippet[:420]

    answer = f"From the book context related to your query:\n{snippet}\n[Chapter: {chapter}, Section: {section}]"
    citation = Citation(
        chapter=chapter,
        section=section,
        text_snippet=snippet[:150] + ("..." if len(snippet) > 150 else ""),
        score=float(best.get("score", 0.0) or 0.0),
    )
    return answer, citation


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    agent = get_agent()
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    if req.retrieval_mode not in ("normal", "selected_text"):
        raise HTTPException(status_code=422, detail="retrieval_mode must be 'normal' or 'selected_text'")

    if req.retrieval_mode == "selected_text" and (not req.selected_text or not req.selected_text.strip()):
        raise HTTPException(status_code=422, detail="selected_text is required when retrieval_mode='selected_text'")

    session_id = req.session_id or str(uuid.uuid4())

    # history (safe)
    history = _DB.get_history(session_id=session_id, limit=6)

    # retrieve
    retrieved_raw = _safe_retrieve(req.question, req.retrieval_mode, req.selected_text)
    chunks = _normalize_chunks(retrieved_raw)

    # context/citations
    context, citations = _build_context_and_citations(chunks, max_citations=3)

    shortcut = None

    # selected_text direct context if needed
    if req.retrieval_mode == "selected_text" and not context.strip():
        context = req.selected_text.strip()
        citations = [Citation(chapter="Unknown", section="Unknown", text_snippet=context[:150], score=1.0)]
        shortcut = "selected_text_direct"

    # ask agent
    try:
        answer = agent.create_chat_completion(
            question=req.question,
            context=context,
            conversation_history=history,
        )
    except Exception as e:
        # if agent crashes, we fallback extractively
        fallback = _extractive_fallback_answer(req.question, chunks)
        if fallback:
            answer, cit = fallback
            citations = [cit]
            shortcut = "extractive_fallback_agent_error"
        else:
            raise HTTPException(status_code=500, detail=f"Internal error: {e}")

    # if agent refused but we do have chunks => extractive fallback (THIS FIXES YOUR ISSUE)
    if _is_refusal_text(answer) and chunks:
        fallback = _extractive_fallback_answer(req.question, chunks)
        if fallback:
            answer, cit = fallback
            citations = [cit]
            shortcut = "extractive_fallback_refusal"

    is_refusal = _is_refusal_text(answer)

    # save turn (never crash API)
    try:
        _DB.save_turn(session_id=session_id, question=req.question, answer=answer)
    except Exception:
        pass

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        citations=citations if not is_refusal else [],
        retrieval_mode=req.retrieval_mode,
        grounded=True,
        metadata=ChatMetadata(
            latency_ms=0.0,
            num_chunks=len(chunks),
            is_refusal=is_refusal,
            context_length=len(context or ""),
            shortcut=shortcut,
        ),
    )
