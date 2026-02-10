"""
Main semantic retriever orchestrator.
"""

import json
import re
import time
from typing import List, Dict, Optional, Literal
from datetime import datetime

from .config import RetrievalConfig, get_config
from .embeddings import get_embedding_service
from .qdrant_client import QdrantRetriever
from .formatter import ResultFormatter
from .schemas import RetrievalRequest


class SemanticRetriever:
    """
    Main orchestrator for semantic retrieval.

    Supports two modes:
    - Normal: Broad semantic search (k=5, threshold=0.7)
    - Selected Text: Constrained search based on selection (k=3, threshold=0.85)
    """

    def __init__(self, config: Optional[RetrievalConfig] = None):
        """
        Initialize semantic retriever.

        Args:
            config: Optional configuration. If None, loads from environment.
        """
        self.config = config or get_config()

        # Initialize embedding service
        self.embedding_service = get_embedding_service(
            use_mock=self.config.use_mock_embeddings,
            api_key=self.config.gemini_api_key,
        )

        # Initialize Qdrant client
        self.qdrant_client = QdrantRetriever(
            url=self.config.qdrant_url,
            api_key=self.config.qdrant_api_key,
            collection_name=self.config.collection_name,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )

        # Result formatter
        self.formatter = ResultFormatter()

    def retrieve(
        self,
        query: str,
        retrieval_mode: Literal["normal", "selected_text"] = "normal",
        selected_text: Optional[str] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant chunks based on mode.

        Args:
            query: User's question
            retrieval_mode: "normal" or "selected_text"
            selected_text: Text selected by user (required if mode="selected_text")
            top_k: Override default top_k
            score_threshold: Override default threshold

        Returns:
            List of formatted chunk dictionaries with metadata and scores

        Raises:
            ValueError: If validation fails
            Exception: If retrieval fails
        """
        start_time = time.time()

        # Validate request
        request = RetrievalRequest(
            query=query,
            retrieval_mode=retrieval_mode,
            selected_text=selected_text,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        # Log retrieval start
        self._log_event(
            "retrieval_start",
            mode=retrieval_mode,
            query_length=len(query),
            has_selected_text=selected_text is not None,
        )

        try:
            if retrieval_mode == "normal":
                results = self._retrieve_normal(request, top_k, score_threshold)
            else:
                results = self._retrieve_selected_text(request, top_k, score_threshold)

            # Validate metadata integrity (formatter rule)
            self.formatter.validate_metadata_integrity(results)

            # IMPORTANT: strip score/relevance junk from snippets so LLM doesn't copy it
            self._strip_score_from_snippets(results)

            # Log retrieval success
            elapsed_ms = (time.time() - start_time) * 1000
            self._log_event(
                "retrieval_success",
                mode=retrieval_mode,
                num_results=len(results),
                latency_ms=round(elapsed_ms, 2),
            )

            return results

        except Exception as e:
            # Log retrieval failure
            elapsed_ms = (time.time() - start_time) * 1000
            self._log_event(
                "retrieval_failure",
                level="ERROR",
                mode=retrieval_mode,
                error=str(e),
                latency_ms=round(elapsed_ms, 2),
            )
            raise

    def _retrieve_normal(
        self,
        request: RetrievalRequest,
        top_k: Optional[int],
        score_threshold: Optional[float],
    ) -> List[Dict]:
        """
        Perform normal mode retrieval.
        """
        k = top_k if top_k is not None else self.config.retrieval_top_k
        threshold = (
            score_threshold
            if score_threshold is not None
            else self.config.retrieval_score_threshold
        )

        # Generate embedding for query
        embedding_start = time.time()
        query_embedding = self.embedding_service.embed_query(request.query)
        embedding_time_ms = (time.time() - embedding_start) * 1000

        self._log_event(
            "embedding_generated",
            mode="normal",
            embedding_time_ms=round(embedding_time_ms, 2),
        )

        # Search Qdrant
        search_start = time.time()
        scored_points = self.qdrant_client.search(
            query_vector=query_embedding, top_k=k, score_threshold=threshold
        )
        search_time_ms = (time.time() - search_start) * 1000

        self._log_event(
            "qdrant_search_complete",
            mode="normal",
            num_results=len(scored_points),
            search_time_ms=round(search_time_ms, 2),
        )

        return self.formatter.format_results(scored_points)

    def _retrieve_selected_text(
        self,
        request: RetrievalRequest,
        top_k: Optional[int],
        score_threshold: Optional[float],
    ) -> List[Dict]:
        """
        Perform selected text mode retrieval.

        IMPORTANT: Embeds the selected_text (not the query) to constrain context.
        """
        k = top_k if top_k is not None else self.config.selected_text_top_k
        threshold = (
            score_threshold
            if score_threshold is not None
            else self.config.selected_text_score_threshold
        )

        # Generate embedding for selected text
        embedding_start = time.time()
        selection_embedding = self.embedding_service.embed_query(request.selected_text)
        embedding_time_ms = (time.time() - embedding_start) * 1000

        self._log_event(
            "embedding_generated",
            mode="selected_text",
            selection_length=len(request.selected_text),
            embedding_time_ms=round(embedding_time_ms, 2),
        )

        # Search Qdrant
        search_start = time.time()
        scored_points = self.qdrant_client.search(
            query_vector=selection_embedding, top_k=k, score_threshold=threshold
        )
        search_time_ms = (time.time() - search_start) * 1000

        self._log_event(
            "qdrant_search_complete",
            mode="selected_text",
            num_results=len(scored_points),
            search_time_ms=round(search_time_ms, 2),
        )

        return self.formatter.format_results(scored_points)

    def _strip_score_from_snippets(self, results: List[Dict]) -> None:
        """
        Remove "(Relevance: x.xx)" / "(Score: x.xx)" noise from snippets.
        This prevents the LLM from copying these into the final answer.
        """
        if not results:
            return

        # Matches: (Relevance: 0.04) OR (Relevance: 0.04), or (Score: 0.04) etc.
        pat = re.compile(r"\s*\((?:relevance|score)\s*:\s*[-+]?\d*\.?\d+\)\s*", re.IGNORECASE)

        for r in results:
            # Some formatters use "text_snippet", some use "text"
            if isinstance(r, dict):
                if "text_snippet" in r and isinstance(r["text_snippet"], str):
                    r["text_snippet"] = re.sub(pat, " ", r["text_snippet"]).strip()
                if "text" in r and isinstance(r["text"], str):
                    r["text"] = re.sub(pat, " ", r["text"]).strip()

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all components.
        """
        return {
            "qdrant": self.qdrant_client.health_check(),
            "embedding_service": True,
        }

    def get_collection_info(self) -> Dict:
        """
        Get Qdrant collection information.
        """
        return self.qdrant_client.get_collection_info()

    def _log_event(self, event: str, level: str = "INFO", **kwargs):
        """
        Log structured JSON event.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs,
        }
        print(json.dumps(log_entry))
