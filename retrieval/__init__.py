"""
Semantic Retrieval Layer for Book-Based RAG Chatbot

This module provides semantic search capabilities over book content stored in Qdrant.
Supports two retrieval modes:
- Normal: Broad semantic search (k=5, threshold=0.7)
- Selected Text: Constrained search based on user selection (k=3, threshold=0.85)
"""

from .retriever import SemanticRetriever
from .config import RetrievalConfig

__all__ = ["SemanticRetriever", "RetrievalConfig"]
__version__ = "1.0.0"
