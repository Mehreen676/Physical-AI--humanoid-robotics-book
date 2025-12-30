# Book RAG Agent Backend

Hallucination-free RAG chatbot backend for book content.

## Features

- Semantic search over book content using Qdrant vector database
- FastAPI REST API for chat and retrieval
- Multi-turn conversation support with context management
- Selected text mode for focused retrieval
- Graceful error handling and fallbacks

## Setup

```bash
pip install -e .
```

## Running

```bash
python main.py
```

## Development

Install dev dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```
