"""FastAPI routes for Agentic RAG."""

import time
import sys
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from fastapi import APIRouter, HTTPException

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend_v3.models import (
    ChatRequest,
    ChatResponse,
    SessionCreate,
    SessionResponse,
    SessionHistory,
    HealthResponse
)
from backend_v3.agent import (
    GeminiAgent,
    ContextFormatter,
    SelectedTextHandler,
    AnswerGenerator
)
from backend_v3.storage import get_database
from backend_v3.utils import StructuredLogger
from retrieval import SemanticRetriever

router = APIRouter()

_agent: GeminiAgent = None
_retriever: SemanticRetriever = None

REFUSAL_PHRASE = "I cannot answer this question based on the provided context."


# -------------------------
# Dependency setters
# -------------------------
def set_agent(agent: GeminiAgent):
    global _agent
    _agent = agent


def set_retriever(retriever: SemanticRetriever):
    global _retriever
    _retriever = retriever


def get_agent() -> GeminiAgent:
    if _agent is None:
        raise RuntimeError("Agent not initialized")
    return _agent


def get_retriever() -> SemanticRetriever:
    if _retriever is None:
        raise RuntimeError("Retriever not initialized")
    return _retriever


# -------------------------
# Helpers
# -------------------------
def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def _extract_term_from_question(q: str) -> Optional[str]:
    q = (q or "").strip()

    # Allow: "ros 2" (keyword), "ROS2", "simulation"
    # If it's short and not a sentence, treat as term.
    if len(q) <= 40 and not re.search(r"[?.!]", q) and len(q.split()) <= 4:
        return q.strip().strip('"').strip("'")

    m = re.match(r"^(what is|define|explain)\s+(.+?)\s*[\?\.\!]*$", q, flags=re.IGNORECASE)
    if not m:
        return None

    raw = (m.group(2) or "").strip().strip('"').strip("'").strip()

    raw = re.split(
        r"\b(according to|in the glossary|from the glossary|as per|based on)\b",
        raw,
        flags=re.IGNORECASE
    )[0].strip()

    raw = re.sub(r"\b(the|glossary)\b\s*$", "", raw, flags=re.IGNORECASE).strip()

    if not raw or len(raw) > 80:
        return None
    return raw


def _chunk_text(c: Dict[str, Any]) -> str:
    for k in ("text", "content", "text_snippet", "snippet"):
        v = c.get(k)
        if isinstance(v, str) and v.strip():
            return v
    payload = c.get("payload")
    if isinstance(payload, dict):
        v = payload.get("text")
        if isinstance(v, str) and v.strip():
            return v
    return ""


def _chunk_meta(c: Dict[str, Any]) -> Tuple[str, str]:
    ch = c.get("chapter")
    sec = c.get("section")
    if isinstance(ch, str) and ch.strip() and isinstance(sec, str) and sec.strip():
        return ch.strip(), sec.strip()

    meta = c.get("metadata")
    if isinstance(meta, dict):
        ch2 = meta.get("chapter")
        sec2 = meta.get("section")
        if isinstance(ch2, str) and ch2.strip() and isinstance(sec2, str) and sec2.strip():
            return ch2.strip(), sec2.strip()

    payload = c.get("payload")
    if isinstance(payload, dict):
        ch3 = payload.get("chapter")
        sec3 = payload.get("section")
        if isinstance(ch3, str) and ch3.strip() and isinstance(sec3, str) and sec3.strip():
            return ch3.strip(), sec3.strip()

    return "Unknown", "Unknown"


def _is_glossary_chunk(c: Dict[str, Any]) -> bool:
    ch, sec = _chunk_meta(c)
    s = _normalize(f"{ch} {sec}")
    return ("glossary" in s) or (ch.strip().lower() == "appendix" and "glossary" in sec.strip().lower())


def _make_citation_from_chunk(chunk: Dict[str, Any], score: float = 1.0) -> Dict[str, Any]:
    ch, sec = _chunk_meta(chunk)
    snippet = (_chunk_text(chunk) or "").strip()
    if len(snippet) > 500:
        snippet = snippet[:500] + "..."
    return {"chapter": ch, "section": sec, "text_snippet": snippet, "score": float(score)}


def _extract_module_request(question: str) -> Optional[Dict[str, Any]]:
    q_norm = _normalize(question)
    needs_summary = bool(re.search(r"\b(summarize|summary|overview)\b", q_norm))

    m = re.search(r"\bmodule\s*(\d+)\b\s*[:\-]?\s*([^,\n]+)?", question, flags=re.IGNORECASE)
    if not m:
        return None

    try:
        module_num = int(m.group(1))
    except Exception:
        return None

    title = (m.group(2) or "").strip()
    if title:
        title = re.split(r"\b(from|in)\s+the\s+book\b", title, flags=re.IGNORECASE)[0].strip()
        title = title.strip(" -:")

    return {"module_num": module_num, "module_title": title, "needs_summary": needs_summary}


def _chunk_matches_module(c: Dict[str, Any], module_num: int, module_title: str = "") -> bool:
    ch, sec = _chunk_meta(c)
    meta = _normalize(f"{ch} {sec}")

    if re.search(rf"\bmodule\s*{module_num}\b", meta):
        return True

    if module_title:
        keywords = [k for k in re.split(r"[^\w]+", module_title.lower()) if len(k) >= 4]
        if keywords and any(k in meta for k in keywords):
            return True

    return False


def _heuristic_glossary_definition(question: str, chunks: List[Dict[str, Any]]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    term = _extract_term_from_question(question)
    if not term or not chunks:
        return None, []

    glossary_chunks = [c for c in chunks if _is_glossary_chunk(c)]
    if not glossary_chunks:
        return None, []

    patterns = [
        re.compile(rf"^\s*-\s*\*\*{re.escape(term)}\*\*\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
        re.compile(rf"^\s*-\s*{re.escape(term)}\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
        re.compile(rf"^\s*{re.escape(term)}\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    ]

    for c in glossary_chunks:
        txt = _chunk_text(c)
        if not txt:
            continue
        for pat in patterns:
            m = pat.search(txt)
            if m:
                definition = m.group(1).strip()
                chapter, section = _chunk_meta(c)
                ans = f"{term} is {definition} [Chapter: {chapter}, Section: {section}]"
                return ans, [_make_citation_from_chunk(c, 1.0)]

    return None, []


def _heuristic_module_summary(question: str, chunks: List[Dict[str, Any]]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    req = _extract_module_request(question)
    if not req or not chunks or not req.get("needs_summary"):
        return None, []

    module_num = req["module_num"]
    module_title = req.get("module_title", "") or ""

    module_chunks = [c for c in chunks if _chunk_matches_module(c, module_num, module_title)]
    if not module_chunks:
        return None, []

    points: List[str] = []
    used_chunks: List[Dict[str, Any]] = []

    for c in module_chunks:
        txt = _chunk_text(c)
        if not txt:
            continue
        used_chunks.append(c)

        for line in txt.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith(("-", "•")):
                s2 = s.lstrip("-•").strip()
                if 6 <= len(s2) <= 150:
                    points.append(s2)

        if len(points) >= 8:
            break

    seen = set()
    clean_points = []
    for p in points:
        k = _normalize(p)
        if k in seen:
            continue
        seen.add(k)
        clean_points.append(p)
        if len(clean_points) >= 8:
            break

    if not clean_points:
        return None, []

    title_part = f"Module {module_num}"
    if module_title:
        title_part += f": {module_title}"

    ch, sec = _chunk_meta(used_chunks[0])
    ans = f"{title_part} overview (from the book):\n- " + "\n- ".join(clean_points) + f"\n[Chapter: {ch}, Section: {sec}]"

    cits = [_make_citation_from_chunk(used_chunks[0], 1.0)]
    if len(used_chunks) > 1:
        cits.append(_make_citation_from_chunk(used_chunks[1], 0.95))
    return ans, cits


def _extractive_fallback_from_chunks(question: str, chunks: List[Dict[str, Any]]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    """
    If LLM fails (429), give user something grounded from the top chunk.
    """
    if not chunks:
        return None, []

    top = chunks[0]
    txt = (_chunk_text(top) or "").strip()
    if not txt:
        return None, []

    ch, sec = _chunk_meta(top)

    # Take first 6 useful lines (prefer bullets)
    lines = []
    for raw in txt.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("#"):
            continue
        lines.append(s)
        if len(lines) >= 6:
            break

    snippet = " ".join(lines)
    if len(snippet) > 450:
        snippet = snippet[:450] + "..."

    ans = f"From the book context related to your query:\n{snippet}\n[Chapter: {ch}, Section: {sec}]"
    return ans, [_make_citation_from_chunk(top, 1.0)]


# -------------------------
# CHAT ENDPOINT
# -------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    StructuredLogger.log_event("chat_start", question=request.question)

    try:
        SelectedTextHandler.validate_selected_text(
            request.selected_text,
            request.retrieval_mode
        )

        retriever = get_retriever()
        chunks = retriever.retrieve(
            query=request.question,
            retrieval_mode=request.retrieval_mode,
            selected_text=request.selected_text
        )

        StructuredLogger.log_event("retrieval_complete", num_chunks=len(chunks))

        if request.retrieval_mode == "selected_text":
            context = SelectedTextHandler.prepare_selected_text_context(
                request.question,
                request.selected_text,
                chunks
            )
        else:
            context = ContextFormatter.format_chunks(chunks)

        db = get_database()
        session_id = request.session_id

        if session_id and db.session_exists(session_id):
            history = db.get_conversation_history(session_id)
        else:
            session_id = db.create_session()
            history = []

        # ✅ HEURISTICS FIRST (avoid Gemini quota hits)
        shortcut = None
        forced_citations: Optional[List[Dict[str, Any]]] = None

        h_ans, h_cit = _heuristic_glossary_definition(request.question, chunks)
        if h_ans:
            answer_text = h_ans
            grounded = True
            is_refusal = False
            shortcut = "heuristic_glossary"
            forced_citations = h_cit
        else:
            m_ans, m_cit = _heuristic_module_summary(request.question, chunks)
            if m_ans:
                answer_text = m_ans
                grounded = True
                is_refusal = False
                shortcut = "heuristic_module_summary"
                forced_citations = m_cit
            else:
                # LLM as last resort
                agent = get_agent()
                generator = AnswerGenerator(agent)
                result = generator.generate_answer(
                    question=request.question,
                    context=context,
                    conversation_history=history
                )
                answer_text = (result.get("answer") or "").strip()

                if answer_text == REFUSAL_PHRASE and chunks:
                    # If LLM refused (including 429 behind the scenes), use extractive fallback
                    ex_ans, ex_cit = _extractive_fallback_from_chunks(request.question, chunks)
                    if ex_ans:
                        answer_text = ex_ans
                        grounded = True
                        is_refusal = False
                        shortcut = "extractive_fallback"
                        forced_citations = ex_cit
                    else:
                        grounded = False
                        is_refusal = True
                else:
                    is_refusal = (answer_text == REFUSAL_PHRASE)
                    grounded = not is_refusal

        StructuredLogger.log_event("answer_generated", is_refusal=is_refusal)

        if forced_citations is not None:
            citations = forced_citations
        else:
            # normal citation extraction
            agent = get_agent()
            generator = AnswerGenerator(agent)
            citations = generator.extract_citations(answer_text, chunks)

        # Store turn
        try:
            chunk_ids = [str(i) for i in range(len(chunks))]
            db.add_turn(
                session_id=session_id,
                question=request.question,
                retrieval_mode=request.retrieval_mode,
                context_chunk_ids=chunk_ids,
                answer=answer_text,
                grounded=grounded
            )
        except Exception as e:
            StructuredLogger.log_event("database_error", level="WARNING", error=str(e))

        latency_ms = (time.time() - start_time) * 1000
        StructuredLogger.log_latency("chat_request", latency_ms)

        meta: Dict[str, Any] = {
            "latency_ms": round(latency_ms, 2),
            "num_chunks": len(chunks),
            "is_refusal": is_refusal,
            "context_length": len(context),
        }
        if shortcut:
            meta["shortcut"] = shortcut

        return ChatResponse(
            session_id=session_id,
            answer=answer_text,
            citations=citations,
            retrieval_mode=request.retrieval_mode,
            grounded=grounded,
            metadata=meta
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        StructuredLogger.log_event("chat_error", level="ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# -------------------------
# SESSION ENDPOINTS
# -------------------------
@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    try:
        db = get_database()
        session_id = db.create_session(user_id=request.user_id)
        return SessionResponse(session_id=session_id, created_at=datetime.utcnow())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionHistory)
async def get_session(session_id: str):
    db = get_database()

    if not db.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    history = db.get_conversation_history(session_id)
    created_at = history[0]["created_at"] if history else datetime.utcnow()

    return SessionHistory(session_id=session_id, created_at=created_at, turns=history)


# -------------------------
# HEALTH
# -------------------------
@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        retriever = get_retriever()
        health = retriever.health_check()

        return HealthResponse(
            status="healthy",
            components={
                "qdrant": health["qdrant"],
                "embeddings": health["embedding_service"],
                "agent": True,
                "database": True
            },
            version="3.0.0"
        )
    except Exception:
        return HealthResponse(
            status="unhealthy",
            components={
                "qdrant": False,
                "embeddings": False,
                "agent": False,
                "database": False
            },
            version="3.0.0"
        )
