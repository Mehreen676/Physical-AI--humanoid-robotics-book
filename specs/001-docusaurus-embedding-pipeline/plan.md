# Implementation Plan: Docusaurus Embedding Pipeline

**Feature**: Docusaurus Embedding Pipeline
**Created**: 2025-12-10
**Updated**: 2025-12-28
**Status**: Ready for Implementation
**Branch**: 001-docusaurus-embedding-pipeline
**Spec**: [specs/001-docusaurus-embedding-pipeline/spec.md](spec.md)

## Summary

This plan describes the implementation of a complete RAG embedding pipeline that extracts text from the deployed Docusaurus textbook (https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/), generates vector embeddings using Cohere, and stores them in Qdrant Cloud for RAG-based retrieval. The implementation follows a single-file main.py approach with clearly defined functions orchestrated by a main() controller, enabling end-to-end document ingestion, embedding generation, and vector storage in Qdrant's free-tier cloud service.

## Technical Context

### System Overview
This system extracts text from the deployed Docusaurus textbook, generates embeddings using Cohere, and stores them in Qdrant Cloud for RAG-based retrieval. The implementation is contained in a **single main.py file** with the following core functions:

**Core Functions**:
- `get_urls()` - Fetch all content URLs from deployed book
- `extract_text()` - Extract and clean text from each URL
- `chunk_text()` - Split content into sized chunks with overlap
- `embed_chunks()` - Generate Cohere embeddings for chunks
- `store_in_qdrant()` - Upsert embeddings to Qdrant collection
- `main()` - Orchestrate the complete pipeline

**Execution Flow**:
```
Deployed Book URLs → Extract Text → Chunk Content → Generate Embeddings → Store in Qdrant
```

### Architecture
- **Backend**: Python 3.9+ application using UV for project initialization and dependency management
- **Project Initialization**: `uv init backend && uv venv && uv add requests beautifulsoup4 cohere qdrant-client`
- **Embedding Service**: Cohere API (`embed-english-light-v3.0` model, 1024 dimensions)
- **Vector Database**: Qdrant Cloud (free tier), collection: "rag_embedding"
- **Target Site**: https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/ (GitHub Pages deployment)
- **Collection Configuration**: Cosine similarity metric, 1024-dimension vectors, metadata retention

### Technology Stack
- **Language**: Python 3.9+
- **Package Manager**: UV (for project initialization, venv, dependency management)
- **Dependencies**:
  - `requests` - HTTP requests for URL fetching
  - `beautifulsoup4` - HTML parsing and text extraction
  - `cohere` - Embedding generation SDK
  - `qdrant-client` - Vector database client
- **Embedding Model**: Cohere `embed-english-light-v3.0` (1024 dimensions, lightweight)
- **Vector Database**: Qdrant Cloud (remote, free tier)

### Dependencies & Integration Points
- **Cohere API**: Requires `COHERE_API_KEY` in `.env`
- **Qdrant Cloud**: Requires `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
- **Web Scraping**: requests + BeautifulSoup for HTML parsing
- **Environment Variables**: `.env` file for API credentials
- **Python Version**: 3.9+ (UV compatible)

### Known Configurations (from .env)
- **Qdrant URL**: `https://890f051f-d398-4dd0-abdc-01c3dfd41cb1.europe-west3-0.gcp.cloud.qdrant.io:6333`
- **Qdrant API Key**: Configured in `.env`
- **Cohere API Key**: Configured in `.env`
- **Collection Name**: "rag_embedding"
- **Vector Dimensions**: 1024
- **Embedding Model**: embed-english-light-v3.0

## Constitution Check

### Alignment with Core Principles
- **Interdisciplinary Collaboration**: This system integrates web scraping, NLP, and vector databases across different domains
- **Ethical AI Development**: System will handle public content only, respecting robots.txt and rate limits
- **Robustness & Safety Engineering**: Implementation will include proper error handling and fallback mechanisms
- **Continuous Learning & Adaptation**: Design allows for parameter tuning and future enhancement

### Potential Violations
- **Ethical AI Development**: Must ensure compliance with website terms of service and robots.txt when scraping

## Phase 0: Research & Resolution (COMPLETED)

### Research Findings

#### 1. UV Package Manager Best Practices ✅
- **Decision**: Use `uv init backend` to create new Python project with UV
- **Rationale**: UV provides fast, deterministic dependency management with virtual environment support
- **Implementation**:
  ```bash
  uv init backend        # Initialize new project in backend/ directory
  uv venv                # Create virtual environment
  uv add requests beautifulsoup4 cohere qdrant-client  # Add required dependencies
  ```
- **Alternatives Considered**: pip + poetry (more verbose); setuptools (less convenient)

#### 2. Cohere Embedding Integration ✅
- **Decision**: Use Cohere `embed-english-light-v3.0` model with 1024 dimensions
- **Rationale**: Lightweight, fast, suitable for Docusaurus content; free tier availability; 1024 dims provides good semantic richness
- **Implementation**:
  - API Key: Loaded from `COHERE_API_KEY` environment variable
  - Input type: `default` for documents, `search_query` for retrieval queries
  - Rate limit strategy: Batch requests in groups of 20-50 texts per API call
  - Error handling: Retry with exponential backoff for rate limits
- **Alternatives Considered**: OpenAI embeddings (paid, slower); Local models (requires GPU, slower)

#### 3. Qdrant Cloud Integration ✅
- **Decision**: Use Qdrant Cloud free tier with remote hosted vectors
- **Rationale**: No local setup required; accessible from anywhere; free tier supports 1M+ vectors
- **Implementation**:
  - Connection: `https://[qdrant-url]:6333` with API key authentication
  - Collection: "rag_embedding" with 1024-dimension vectors
  - Distance metric: Cosine similarity (optimal for semantic search)
  - Metadata storage: Include `content`, `url`, `position`, `created_at` with each vector
- **Alternatives Considered**: Self-hosted Qdrant (setup overhead); Weaviate (different API); Pinecone (paid)

#### 4. Web Scraping Approach ✅
- **Decision**: Use requests + BeautifulSoup for static content extraction
- **Rationale**: Docusaurus deployed site is static HTML; no JavaScript rendering needed
- **Implementation**:
  - Fetch sitemap: `https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/sitemap.xml`
  - Extract all `.html` URLs from sitemap
  - Filter out non-content pages (search, admin, etc.)
  - Extract main content using BeautifulSoup CSS selectors targeting Docusaurus content divs
  - Remove navigation, headers, footers using CSS class exclusions
- **Alternatives Considered**: Selenium (overkill for static site); Scrapy (heavy framework); Playwright (async but complex)

#### 5. Text Chunking Strategy ✅
- **Decision**: Fixed-size chunking with overlap
  - Chunk size: 1000 characters (fits within Cohere's limits)
  - Overlap: 100 characters (preserves context across chunks)
  - Max chunk: 2000 characters (safety limit for Cohere)
- **Rationale**: Provides good semantic units while preserving token limits and context continuity
- **Implementation**:
  ```python
  def chunk_text(text, chunk_size=1000, overlap=100):
      chunks = []
      for i in range(0, len(text), chunk_size - overlap):
          chunks.append(text[i:i + chunk_size])
      return chunks
  ```
- **Alternatives Considered**: Sentence-based (loses semantic units); Paragraph-based (variable quality); NLP tokenization (complexity vs. benefit)

### Known Unknowns Resolved ✅
- ✅ Cohere and Qdrant configuration parameters: Using established defaults from community patterns
- ✅ Target Docusaurus site structure: GitHub Pages deployment of physical-ai book (static HTML)
- ✅ Rate limits: Cohere free tier: ~100 requests/min; Qdrant: 10k+ ops/s (ample for demo)
- ✅ Dynamic content: Not applicable - deployed site is static HTML

## Phase 1: Design & Architecture (COMPLETED)

### Data Model Design

#### Document Chunk Entity (stored in Qdrant)
```python
{
    "id": "UUID4 or deterministic hash",  # Unique identifier
    "content": "text chunk (≤2000 chars)",  # The document text segment
    "url": "source URL",                    # Original document URL
    "position": 0,                          # Chunk order in document (0-indexed)
    "embedding": [1024 floats],             # Cohere embedding vector
    "created_at": "ISO-8601 timestamp",     # Generation timestamp
    "metadata": {                           # Additional fields
        "page_title": "extracted from HTML",
        "section": "optional section info"
    }
}
```

#### Qdrant Collection Schema
- **Collection Name**: `rag_embedding`
- **Vector Size**: 1024 dimensions (from Cohere embed-english-light-v3.0)
- **Distance Metric**: Cosine similarity (optimal for semantic search)
- **Point ID Strategy**: UUID4 for unique, non-deterministic IDs (allows re-indexing)
- **Payload Storage**: All metadata retained for retrieval context

**Payload Field Mapping**:
| Field | Type | Description |
|-------|------|-------------|
| `content` | String | Text chunk (max 2000 chars) |
| `url` | String | Source document URL |
| `position` | Integer | Chunk index in original document |
| `created_at` | String | ISO-8601 timestamp |
| `page_title` | String | Extracted page title |
| `chunk_size` | Integer | Actual chunk character count |

### Function Contracts (main.py)

#### 1. `get_urls(base_url: str = "https://mehreen676.github.io/Physical-AI--humanoid-robotics-book") -> List[str]`
- **Purpose**: Fetch all content URLs from deployed Docusaurus site
- **Input**: Optional base URL (defaults to deployed book)
- **Process**:
  1. Fetch sitemap.xml from base_url
  2. Parse XML and extract all URL locations
  3. Filter to include only article/content pages (exclude /docs, /api, etc. if present)
  4. Return sorted list of unique URLs
- **Output**: List of content URLs
- **Error Handling**:
  - HTTP errors → log and continue with partial results
  - XML parse errors → fallback to manual URL list
  - Empty results → raise ValueError

#### 2. `extract_text(url: str) -> str`
- **Purpose**: Extract clean text from HTML page
- **Input**: Single URL string
- **Process**:
  1. Fetch HTML via requests with timeout (10s)
  2. Parse with BeautifulSoup
  3. Find main content div (Docusaurus: `.markdown`, `.content`, or main tag)
  4. Remove script, style, nav, footer elements
  5. Extract text and normalize whitespace
  6. Return cleaned text
- **Output**: Cleaned text string
- **Error Handling**:
  - Network errors → log and return empty string
  - Parse errors → return raw text content
  - Empty content → log warning and continue

#### 3. `chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]`
- **Purpose**: Split text into overlapping chunks
- **Input**: Text string, chunk_size, overlap amount
- **Process**:
  1. Split into fixed-size chunks with stride = chunk_size - overlap
  2. Validate chunk sizes don't exceed 2000 chars
  3. Skip empty chunks
  4. Return list of chunks
- **Output**: List of text chunks
- **Constraints**: chunk_size > overlap > 0; max_chunk ≤ 2000

#### 4. `embed_chunks(chunks: List[str], model: str = "embed-english-light-v3.0") -> List[List[float]]`
- **Purpose**: Generate Cohere embeddings for text chunks
- **Input**: List of text chunks (up to 100 at a time)
- **Process**:
  1. Batch chunks into groups of 50 (API limit)
  2. Call Cohere API with `input_type="default"`
  3. Implement exponential backoff retry for rate limits
  4. Return embeddings in same order as input
- **Output**: List of embedding vectors (1024 dimensions each)
- **Error Handling**:
  - Rate limit → exponential backoff (max 5 retries)
  - API errors → log and raise Exception
  - Empty chunks → return empty list

#### 5. `store_in_qdrant(chunks: List[str], urls: List[str], embeddings: List[List[float]], positions: List[int]) -> int`
- **Purpose**: Upsert document chunks to Qdrant collection
- **Input**: Parallel lists of chunks, source URLs, embeddings, and positions
- **Process**:
  1. Initialize Qdrant client with `QDRANT_URL` and `QDRANT_API_KEY`
  2. Ensure collection "rag_embedding" exists (create if needed)
  3. Upsert points with:
     - UUID4 point IDs
     - Embedding vectors
     - Metadata: content, url, position, created_at
  4. Return count of successfully stored points
- **Output**: Integer count of upserted points
- **Error Handling**:
  - Connection errors → log and raise
  - Payload errors → skip invalid points, log, continue
  - Collection errors → create collection and retry

#### 6. `main()`
- **Purpose**: Orchestrate the complete pipeline
- **Process**:
  1. Load environment variables (COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY)
  2. Call `get_urls()` → get list of content URLs
  3. For each URL:
     - Extract text: `extract_text(url)`
     - Chunk text: `chunk_text(text)`
     - Generate embeddings: `embed_chunks(chunks)`
     - Store in Qdrant: `store_in_qdrant(...)`
     - Log progress and stats
  4. Print final summary: total URLs, total chunks, total vectors stored
- **Error Handling**: Continue on individual URL failures; report final summary with successes/failures

### System Architecture Diagram
```
┌────────────────────────────────────────────────────────────┐
│                    Backend Ingestion Pipeline               │
└────────────────────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  get_urls()     │
                    │  ├─ Fetch       │
                    │  │  sitemap.xml │
                    │  └─ Parse URLs  │
                    └────────┬────────┘
                             │
                    ┌────────▼──────────────────────┐
                    │  For each URL:                 │
                    │  ├─ extract_text(url)         │
                    │  ├─ chunk_text(text)          │
                    │  ├─ embed_chunks(chunks)      │
                    │  └─ store_in_qdrant(...)      │
                    └────────┬──────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼────┐         ┌─────▼─────┐      ┌──────▼──────┐
    │ Cohere │         │  Qdrant   │      │   Logging   │
    │  API   │         │  Cloud    │      │  & Metrics  │
    │        │         │ Collection│      │             │
    └────────┘         │ "rag_     │      └─────────────┘
                       │embedding" │
                       └───────────┘
```

### Project Structure (backend/)
```
backend/
├── pyproject.toml          # UV project manifest
├── .venv/                  # Virtual environment
├── main.py                 # Main pipeline implementation
├── .env                    # Environment variables (API keys)
├── .env.example            # Template for .env
└── README.md               # Quickstart guide
```

## Phase 2: Implementation Plan

**Next Phase**: Implementation tasks will be generated by `/sp.tasks` command.

### Implementation Overview

**Execution Flow**:
1. Create backend/ directory with UV project structure
2. Implement main.py with 6 core functions (get_urls, extract_text, chunk_text, embed_chunks, store_in_qdrant, main)
3. Add comprehensive error handling, logging, and progress tracking
4. Test end-to-end pipeline on deployed Docusaurus site
5. Verify vectors are stored in Qdrant collection "rag_embedding"

**Key Success Metrics**:
- ✅ All 6 functions implemented per specifications in Phase 1
- ✅ Pipeline successfully processes ≥95% of deployed book pages
- ✅ ≥99% of extracted chunks generate embeddings successfully
- ✅ All embeddings upserted to Qdrant with correct metadata
- ✅ Final stats show: total URLs processed, total chunks created, total vectors stored

### Roles & Responsibilities

**@BackendEngineer**:
- Implement ScrapingSkill: `get_urls()` and `extract_text()` functions
- Implement EmbeddingSkill: `chunk_text()` and `embed_chunks()` functions
- Implement StorageSkill: `store_in_qdrant()` function
- Create main() orchestrator with comprehensive error handling and logging

**@Reviewer**:
- Test end-to-end pipeline execution
- Verify Qdrant collection contains expected vectors and metadata
- Validate embeddings using sample queries to ensure semantic correctness
- Confirm all 6 functions meet specification contracts

## Risk Assessment

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| API Rate Limits | Medium | Medium | Batch requests, exponential backoff, retry logic |
| Cohere Token Limits | Low | Medium | Max chunk size validation (2000 chars), chunking strategy |
| Qdrant Connection | Low | High | Connection pooling, retry on transient failures |
| Scraped Content Empty | Low | Low | Fallback selectors, manual URL list if sitemap fails |
| Large Document Processing | Medium | Low | Stream processing, checkpoint save state |

### Mitigation Strategies
- ✅ Implement exponential backoff retry for rate limits (max 5 retries)
- ✅ Validate chunk sizes don't exceed 2000 chars (Cohere limit)
- ✅ Add robust error handling for network and API failures
- ✅ Implement comprehensive logging for debugging
- ✅ Create checkpoint system to resume from failures

## Expected Outcomes

### After Phase 2 Completion
- **Artifact**: `backend/main.py` (~300-400 lines of production code)
- **Configuration**: `.env` file with Cohere and Qdrant credentials
- **Documentation**: `backend/README.md` with quickstart and usage instructions
- **Deployment**: Runnable end-to-end pipeline: `python backend/main.py`

### Performance Expectations
- Sitemap parsing: ~5 seconds
- Content extraction: ~0.5-1 second per page
- Chunking: ~10ms per page
- Embedding generation: ~2-3 seconds for 50 chunks (batched API calls)
- Qdrant storage: ~100ms for 50 vectors
- **Total for 100 pages**: ~30-40 minutes (rate-limited to respect API quotas)

## Success Criteria (Phase 2)
- ✅ All 6 functions implemented per contracts in Phase 1
- ✅ System successfully processes deployed Docusaurus site
- ✅ Embeddings stored in Qdrant collection "rag_embedding" with complete metadata
- ✅ Proper error handling for all failure modes (network, API, parsing)
- ✅ Comprehensive logging and progress tracking
- ✅ Final summary report shows vectors successfully stored and indexed

## Project Structure

### Source Code Layout (backend/)
```
backend/
├── pyproject.toml                  # UV project manifest with dependencies
├── uv.lock                         # Locked dependency versions
├── .venv/                          # Virtual environment (created by uv venv)
├── .env                            # Environment variables (COHERE_API_KEY, QDRANT_*)
├── .env.example                    # Template for .env configuration
├── main.py                         # Main ingestion pipeline (300-400 lines)
├── README.md                       # Quickstart and usage documentation
└── .gitignore                      # Exclude .env, .venv, __pycache__
```

### Implementation File: backend/main.py
**Size Estimate**: 300-400 lines of Python code

**Structure**:
```python
# Imports and configuration
import os, logging, time
from datetime import datetime
from typing import List
import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from uuid import uuid4

# Configuration
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
BASE_URL = "https://mehreen676.github.io/Physical-AI--humanoid-robotics-book"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function 1: get_urls()          [~50 lines]
# Function 2: extract_text()      [~60 lines]
# Function 3: chunk_text()        [~30 lines]
# Function 4: embed_chunks()      [~50 lines]
# Function 5: store_in_qdrant()   [~60 lines]
# Function 6: main()              [~70 lines, orchestrates 1-5]

if __name__ == "__main__":
    main()
```

## Complexity Tracking

> **Note**: This plan adheres to the Project Constitution requirements. No unJustified complexity introduced.

**Architectural Decisions Rationale**:

| Decision | Rationale | Simpler Alternative Considered |
|----------|-----------|-------------------------------|
| Single main.py file | Clear, focused implementation for single pipeline responsibility; easy to test and debug | Separate modules (would add file overhead without benefit for 6 functions) |
| UV package manager | Fast, deterministic deps; clean venv handling; aligns with project standards | pip + poetry (verbose, slow) |
| Cohere embed-light | Lightweight, fast, suitable for demo; sufficient semantic quality | OpenAI embeddings (cost), Local models (setup) |
| Qdrant Cloud free tier | No local setup; accessible globally; free tier sufficient for hackathon demo | Self-hosted (operational overhead); Pinecone (paid) |
| Fixed-size chunks | Predictable, simple to implement; preserves semantics reasonably well | NLP-based (added complexity, marginal benefit) |

## Constitution Alignment

### ✅ Technical Accuracy and Source Verification
- Architecture decisions backed by official docs (Cohere, Qdrant, Docusaurus)
- All API integration patterns follow published SDK examples
- Performance expectations based on documented API limits and benchmarks

### ✅ Clarity for Target Audience
- Specification written for developers with Python/backend experience
- All function contracts documented with clear input/output types
- Error handling strategies explained in accessible language
- README quickstart guides non-experts through setup

### ✅ Reproducibility of Code and Systems
- Single main.py file with clear function separation
- Step-by-step initialization: `uv init backend && uv venv && uv add ...`
- .env configuration approach allows reproduction across environments
- Comprehensive logging enables debugging and verification

### ✅ Theory-Practice Integration
- Chunking strategy explained with practical rationale
- Embedding model selection grounded in performance/quality tradeoff
- Qdrant collection design based on actual use-case (RAG retrieval)
- Risk mitigation strategies all have practical implementations

### ✅ Standardized Citations
- Cohere API docs: https://docs.cohere.com/docs/embeddings
- Qdrant docs: https://qdrant.tech/documentation/
- BeautifulSoup docs: https://www.crummy.com/software/BeautifulSoup/
- UV docs: https://docs.astral.sh/uv/

---

## Next Steps

**After Phase 1 (This Plan) Approval**:
1. Use `/sp.tasks` command to generate detailed implementation tasks
2. Execute implementation according to task breakdown
3. Create PhR for this plan document with `/sp.phr` command

**Deliverables**:
- ✅ Complete implementation plan (Phases 0-1) with detailed function contracts
- ✅ Data model specifications for Qdrant storage
- ✅ Architecture decisions with rationale and alternatives
- ✅ Risk assessment with mitigation strategies
- ⏳ Implementation tasks (Phase 2, generated by `/sp.tasks`)
- ⏳ Completed implementation code (Phase 3, `/sp.tasks` execution)