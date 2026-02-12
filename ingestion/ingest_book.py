# ingestion/ingest_book.py
import os
import uuid
import time
import logging
from typing import Any, Dict, List, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from ingestion.markdown_processor import MarkdownProcessor
from ingestion.chunker import TextChunker
from ingestion.embeddings import get_embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------
# Helpers
# -----------------------------
def env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    return str(v).strip()


def env_int(name: str, default: int) -> int:
    v = env(name)
    if v is None:
        return default
    try:
        return int(v)
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    v = env(name)
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    v = env(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "y", "on")


def load_config() -> Dict[str, Any]:
    cfg = {
        "qdrant_url": env("QDRANT_URL"),
        "qdrant_api_key": env("QDRANT_API_KEY"),
        "collection_name": env("COLLECTION_NAME", "data_collection"),
        "docs_path": env("DOCS_PATH", "front-end/docs"),
        "book_title": env("BOOK_TITLE", "Physical AI & Humanoid Robotics Textbook"),
        "chunk_size": env_int("CHUNK_SIZE", 400),
        "chunk_overlap": env_int("CHUNK_OVERLAP", 100),
        "rate_limit_delay": env_float("RATE_LIMIT_DELAY", 0.1),
        "batch_size": env_int("BATCH_SIZE", 32),
        "use_mock_embeddings": env_bool("USE_MOCK_EMBEDDINGS", False),
    }

    # hard checks
    if not cfg["qdrant_url"]:
        raise RuntimeError("QDRANT_URL missing")
    if not cfg["qdrant_api_key"]:
        raise RuntimeError("QDRANT_API_KEY missing")

    return cfg


def init_markdown_processor(book_title: str, docs_path: str) -> MarkdownProcessor:
    """
    Tumhare project me MarkdownProcessor ka signature change hota raha.
    Is liye hum safe init kar rahe hain:
      - pehle (docs_path, book_title)
      - agar fail ho to (book_title, docs_path)
      - agar fail ho to (docs_path) + set book_title later
    """
    try:
        p = MarkdownProcessor(docs_path, book_title)  # preferred (docs_path, book_title)
        logger.info(f"✅ MarkdownProcessor init mode: docs_book args=({docs_path!r}, {book_title!r})")
        return p
    except TypeError:
        pass

    try:
        p = MarkdownProcessor(book_title, docs_path)  # alternate (book_title, docs_path)
        logger.info(f"✅ MarkdownProcessor init mode: book_docs args=({book_title!r}, {docs_path!r})")
        return p
    except TypeError:
        pass

    p = MarkdownProcessor(docs_path)  # fallback
    logger.info(f"✅ MarkdownProcessor init mode: docs_only args=({docs_path!r})")
    # if processor has book_title attribute
    if hasattr(p, "book_title"):
        try:
            setattr(p, "book_title", book_title)
        except Exception:
            pass
    return p


def process_markdown(processor: MarkdownProcessor) -> List[Dict[str, Any]]:
    """
    MarkdownProcessor me method name `process_all_files` hai.
    """
    if hasattr(processor, "process_all_files"):
        docs = processor.process_all_files()
        return docs

    # fallback: manual find + process_file
    files = processor.find_markdown_files()
    out = []
    for fp in files:
        doc = processor.process_file(fp)
        if doc:
            out.append(doc)
    return out


def init_chunker(chunk_size: int, chunk_overlap: int) -> TextChunker:
    """
    TextChunker signature variation handle:
      - (chunk_size=?, chunk_overlap=?)
      - else (chunk_size=?, overlap=?)
    """
    try:
        c = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        logger.info(f"✅ TextChunker init kwargs={{'chunk_size': {chunk_size}, 'chunk_overlap': {chunk_overlap}}}")
        return c
    except TypeError:
        c = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)
        logger.info(f"✅ TextChunker init kwargs={{'chunk_size': {chunk_size}, 'overlap': {chunk_overlap}}}")
        return c


def normalize_doc(doc: Dict[str, Any], fallback_book_title: str) -> Tuple[str, Dict[str, Any]]:
    """
    Processor ka doc format different ho sakta hai.
    We normalize into:
      text: str
      metadata: dict {book_title, chapter, section, source_file}
    """
    text = doc.get("content") or doc.get("text") or ""
    meta = doc.get("metadata") or {}

    # try keys
    book_title = meta.get("book_title") or doc.get("book_title") or fallback_book_title
    chapter = meta.get("chapter") or doc.get("chapter")
    section = meta.get("section") or doc.get("section")

    # source file keys
    source_file = (
        meta.get("source_file")
        or meta.get("path")
        or doc.get("source_file")
        or doc.get("path")
        or doc.get("source")
    )

    metadata = {
        "book_title": book_title,
        "chapter": chapter,
        "section": section,
        "source_file": source_file,
    }

    return text, metadata


def chunk_documents(chunker: TextChunker, docs: List[Dict[str, Any]], book_title: str) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []

    for doc in docs:
        text, metadata = normalize_doc(doc, book_title)

        if not isinstance(text, str) or not text.strip():
            continue

        # TextChunker.chunk_text requires (text, metadata) in your latest run
        pieces = chunker.chunk_text(text, metadata)

        # expected: list[dict] with keys: text, chunk_index, total_chunks, token_count, ...
        # we normalize output
        for idx, piece in enumerate(pieces):
            chunk_text = piece.get("text") if isinstance(piece, dict) else str(piece)
            chunk_meta = piece.get("chunk_meta") if isinstance(piece, dict) else {}

            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": metadata,   # ✅ always correct metadata
                    "chunk_index": piece.get("chunk_index", idx) if isinstance(piece, dict) else idx,
                    "chunk_meta": chunk_meta,
                }
            )

    return chunks


def ensure_collection(client: QdrantClient, collection_name: str, dim: int) -> None:
    # if exists -> just log
    cols = client.get_collections().collections
    names = {c.name for c in cols}
    if collection_name in names:
        info = client.get_collection(collection_name)
        current_dim = info.config.params.vectors.size
        logger.info(f"Collection already exists: {collection_name} (dim={current_dim})")
        return

    logger.info(f"Creating collection: {collection_name} (dim={dim})")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    logger.info("✅ Collection created")


def upsert_batches(
    client: QdrantClient,
    collection_name: str,
    embedder,
    chunks: List[Dict[str, Any]],
    batch_size: int,
    delay: float,
) -> int:
    total = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]

        vectors = []
        for ch in batch:
            vectors.append(embedder.embed_text(ch["text"]))
            if delay > 0:
                time.sleep(delay)

        points: List[PointStruct] = []
        for ch, vec in zip(batch, vectors):
            payload = {
                "text": ch["text"],
                "metadata": ch["metadata"],     # ✅ nested metadata (book_title/chapter/section/source_file)
                "chunk_index": ch["chunk_index"],
                "chunk_meta": ch.get("chunk_meta") or {},
            }
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload=payload,
                )
            )

        client.upsert(collection_name=collection_name, points=points, wait=True)
        total += len(points)
        logger.info(f"Upserted {total}/{len(chunks)}")

    return total


# -----------------------------
# Main
# -----------------------------
def main():
    logger.info("============================================================")
    logger.info("Starting Book Content Ingestion Pipeline")
    logger.info("============================================================")

    cfg = load_config()

    logger.info("Configuration loaded:")
    for k, v in cfg.items():
        if "key" in k.lower():
            logger.info(f"  {k}: [REDACTED]")
        else:
            logger.info(f"  {k}: {v}")

    logger.info("\n[1/5] Processing markdown files...")
    processor = init_markdown_processor(cfg["book_title"], cfg["docs_path"])
    documents = process_markdown(processor)
    logger.info(f"Processed {len(documents)} documents")

    logger.info("\n[2/5] Chunking documents...")
    chunker = init_chunker(cfg["chunk_size"], cfg["chunk_overlap"])
    chunks = chunk_documents(chunker, documents, cfg["book_title"])
    logger.info(f"Created {len(chunks)} chunks")

    logger.info("\n[3/5] Initializing embeddings provider...")
    embedder = get_embedder()

    # detect actual embedding dim
    sample_vec = embedder.embed_query("dimension check")
    dim = len(sample_vec)
    logger.info(f"Detected embedding dim = {dim}")

    logger.info("\n[4/5] Initializing Qdrant...")
    client = QdrantClient(url=cfg["qdrant_url"], api_key=cfg["qdrant_api_key"], timeout=60)
    ensure_collection(client, cfg["collection_name"], dim)

    logger.info("\n[5/5] Embedding + upserting to Qdrant...")
    total = upsert_batches(
        client=client,
        collection_name=cfg["collection_name"],
        embedder=embedder,
        chunks=chunks,
        batch_size=cfg["batch_size"],
        delay=cfg["rate_limit_delay"],
    )

    logger.info(f"✅ Done. Total upserted: {total}")


if __name__ == "__main__":
    main()
