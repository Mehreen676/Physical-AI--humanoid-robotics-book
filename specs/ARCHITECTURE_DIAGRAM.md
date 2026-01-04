# Book Content Ingestion & Embedding Pipeline - Architecture Diagrams

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE ARCHITECTURE                │
└───────────────────────────────────────────────────────────────────────┘

                              INPUT LAYER
┌───────────────────────────────────────────────────────────────────────┐
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │         Docusaurus Book Content (GitHub Pages)               │   │
│   │                                                                │   │
│   │  front-end/docs/                                              │   │
│   │  ├── 01-introduction/       (1 file)                          │   │
│   │  ├── 02-ros2-foundations/   (2 files)                         │   │
│   │  ├── 03-simulation/         (3 files)                         │   │
│   │  ├── 04-hardware-basics/    (1 file)                          │   │
│   │  ├── 05-vla-systems/        (5 files)                         │   │
│   │  ├── 06-advanced-ai-control/ (1 file)                         │   │
│   │  ├── 07-humanoid-design/    (1 file)                          │   │
│   │  └── appendix/              (3 files, 1 empty)                │   │
│   │                                                                │   │
│   │  Total: 18 files (.md/.mdx)                                   │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
                         PROCESSING LAYER
┌───────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  STAGE 1: Markdown Processing (markdown_processor.py)          │ │
│  │                                                                 │ │
│  │  Input:  18 .md/.mdx files                                     │ │
│  │  Output: 17 clean documents                                    │ │
│  │                                                                 │ │
│  │  Operations:                                                    │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │ 1. Find Files       │ Recursive glob: **/*.md, **/*.mdx  │ │ │
│  │  ├──────────────────────────────────────────────────────────┤ │ │
│  │  │ 2. Strip Frontmatter│ Remove YAML blocks (---)           │ │ │
│  │  ├──────────────────────────────────────────────────────────┤ │ │
│  │  │ 3. Clean Content    │ Remove JSX imports, HTML comments  │ │ │
│  │  ├──────────────────────────────────────────────────────────┤ │ │
│  │  │ 4. Extract Metadata │ Chapter from dir, section from file│ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  Metadata Schema:                                               │ │
│  │  {                                                              │ │
│  │    'book_title': 'Physical AI & Humanoid Robotics',            │ │
│  │    'chapter': 'Ros2 Foundations',  # From directory name       │ │
│  │    'section': 'Module 1 Ros2',     # From filename             │ │
│  │    'source_file': '02-ros2-foundations/module-1-ros2.md'       │ │
│  │  }                                                              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                 │                                     │
│                                 ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  STAGE 2: Text Chunking (chunker.py)                           │ │
│  │                                                                 │ │
│  │  Input:  17 documents (clean text)                             │ │
│  │  Output: 87 chunks (token-based)                               │ │
│  │                                                                 │ │
│  │  Algorithm: Sliding Window with Overlap                        │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │                 Document (2000 tokens)                    │ │ │
│  │  │  ┌─────────────────────────────────────────────────────┐ │ │ │
│  │  │  │ Chunk 1 (400 tokens)          │                     │ │ │ │
│  │  │  └────────────────┬────────────────────────────────────┘ │ │ │
│  │  │                   │ Overlap (100 tokens)                  │ │ │
│  │  │         ┌─────────┴──────────────────────────────────┐   │ │ │
│  │  │         │ Chunk 2 (400 tokens)       │               │   │ │ │
│  │  │         └──────────────┬───────────────────────────────  │ │ │
│  │  │                        │ Overlap (100 tokens)             │ │ │
│  │  │              ┌─────────┴───────────────────────────┐     │ │ │
│  │  │              │ Chunk 3 (400 tokens)    │           │     │ │ │
│  │  │              └───────────────────────────────────────     │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  Chunking Strategy:                                             │ │
│  │  • Encoding: tiktoken (cl100k_base)                            │ │
│  │  • Size: 400 tokens (300-500 range)                            │ │
│  │  • Overlap: 100 tokens (25%)                                   │ │
│  │  • Deterministic: Same input → same chunks                     │ │
│  │                                                                 │ │
│  │  Enhanced Metadata:                                             │ │
│  │  {                                                              │ │
│  │    ...original_metadata,                                        │ │
│  │    'chunk_index': 2,        # 0-indexed position               │ │
│  │    'total_chunks': 12,      # Total from source doc            │ │
│  │    'token_count': 387,      # Actual tokens in chunk           │ │
│  │    'start_token': 200,      # Start position                   │ │
│  │    'end_token': 587         # End position                     │ │
│  │  }                                                              │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                 │                                     │
│                                 ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  STAGE 3: Embedding Generation (embeddings.py)                 │ │
│  │                                                                 │ │
│  │  Input:  87 text chunks                                        │ │
│  │  Output: 87 embeddings (768-dimensional vectors)               │ │
│  │                                                                 │ │
│  │  Service: Google Gemini API                                    │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Model: models/embedding-001                             │ │ │
│  │  │  Dimension: 768                                           │ │ │
│  │  │  Task Type: retrieval_document                            │ │ │
│  │  │  Rate Limit: 15 requests/min, 1,500/day (free tier)      │ │ │
│  │  │  Cost: $0 (free tier)                                     │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  Batch Processing Flow:                                         │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  For each chunk (with rate limiting):                    │ │ │
│  │  │    1. Send text to Gemini API                            │ │ │
│  │  │    2. Receive 768-float embedding                        │ │ │
│  │  │    3. Sleep 0.1s (rate limit control)                    │ │ │
│  │  │    4. Retry on error (exponential backoff)               │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  Status: ⚠️ Rate-limited (1/87 embeddings generated)           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                        │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
                           STORAGE LAYER
┌───────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  STAGE 4: Vector Storage (vector_store.py)                     │ │
│  │                                                                 │ │
│  │  Database: Qdrant Cloud (Free Tier)                            │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Collection: data_collection                             │ │ │
│  │  │  Distance: COSINE                                         │ │ │
│  │  │  Index: HNSW (Hierarchical Navigable Small World)        │ │ │
│  │  │  Storage: 1 GB free (enough for ~250K chunks)            │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  Point Structure:                                               │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  {                                                        │ │ │
│  │  │    id: "3f2504e0-4f89-11d3-9a0c-0305e82c3301",  (UUID)  │ │ │
│  │  │    vector: [0.123, -0.456, ...],  (768 floats)          │ │ │
│  │  │    payload: {                                            │ │ │
│  │  │      text: "ROS 2 is a flexible framework...",          │ │ │
│  │  │      book_title: "Physical AI & Humanoid Robotics",     │ │ │
│  │  │      chapter: "Ros2 Foundations",                        │ │ │
│  │  │      section: "Module 1 Ros2",                           │ │ │
│  │  │      source_file: "02-ros2-foundations/module-1.md",    │ │ │
│  │  │      chunk_index: 2,                                     │ │ │
│  │  │      total_chunks: 12,                                   │ │ │
│  │  │      token_count: 387                                    │ │ │
│  │  │    }                                                      │ │ │
│  │  │  }                                                        │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  UUID Generation (Idempotent):                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  source_file + chunk_index → MD5 → UUID                  │ │ │
│  │  │  "02-ros2-foundations/module-1.md::2" → hash → UUID      │ │ │
│  │  │                                                           │ │ │
│  │  │  Benefit: Re-running ingestion updates (not duplicates)  │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  Status: ⏸️ Pending embeddings                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                        │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
                        VALIDATION LAYER
┌───────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  STAGE 5: Similarity Search (test_search.py)                   │ │
│  │                                                                 │ │
│  │  Query: "What is ROS 2?"                                        │ │
│  │     ↓                                                           │ │
│  │  Generate embedding (768-dim)                                   │ │
│  │     ↓                                                           │ │
│  │  Search Qdrant (cosine similarity)                              │ │
│  │     ↓                                                           │ │
│  │  Return top 5 results:                                          │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Result 1: Score 0.85 - "ROS 2 is a flexible framework..."│ │ │
│  │  │  Result 2: Score 0.78 - "ROS 2 provides tools for..."    │ │ │
│  │  │  Result 3: Score 0.72 - "Robot Operating System 2..."    │ │ │
│  │  │  ...                                                      │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │                                                                 │ │
│  │  Validation Criteria:                                           │ │
│  │  ✅ Results returned (count > 0)                                │ │
│  │  ✅ Scores > threshold (0.3)                                    │ │
│  │  ✅ Metadata present (chapter, section)                         │ │
│  │  ✅ Text snippets relevant                                      │ │
│  │                                                                 │ │
│  │  Status: ⏸️ Pending vectors                                     │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                     COMPONENT INTERACTIONS                           │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  ingest_book.py  │  (Main Orchestrator)
│   (6.7 KB)       │
└────────┬─────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ markdown_        │  │    chunker.py    │
│ processor.py     │  │    (3.5 KB)      │
│    (5.7 KB)      │  │                  │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         │ depends on          │ depends on
         │                     │
         ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│  pathlib         │  │    tiktoken      │
│  (stdlib)        │  │   (external)     │
└──────────────────┘  └──────────────────┘

         │
         ├─────────────────────────────┐
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  embeddings.py   │          │ vector_store.py  │
│    (4.7 KB)      │          │    (8.9 KB)      │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         │ depends on                  │ depends on
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│ google.          │          │ qdrant_client    │
│ generativeai     │          │   (external)     │
│   (external)     │          │                  │
└──────────────────┘          └──────────────────┘
         │                             │
         │ API call                    │ API call
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  Gemini API      │          │  Qdrant Cloud    │
│  (Free Tier)     │          │  (Free Tier)     │
│                  │          │                  │
│  • 15 req/min    │          │  • 1 GB storage  │
│  • 1,500 req/day │          │  • HNSW index    │
│  • 768-dim embeds│          │  • Cosine metric │
└──────────────────┘          └──────────────────┘

┌──────────────────┐
│ test_search.py   │  (Validation)
│   (5.4 KB)       │
└────────┬─────────┘
         │ uses
         │
         ├─────────────────┬─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
│  embeddings.py   │ │vector_store.py│ │  .env config │
└──────────────────┘ └──────────────┘ └──────────────┘
```

## Data Transformation Pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DATA TRANSFORMATION FLOW                          │
└──────────────────────────────────────────────────────────────────────┘

Raw Markdown File
┌───────────────────────────────────────────────────────────────────┐
│ ---                                                                │
│ title: "ROS 2 Foundations"                                         │
│ ---                                                                │
│                                                                    │
│ import React from 'react';                                         │
│ import TOC from '@theme/TOC';                                      │
│                                                                    │
│ # ROS 2 Foundations                                                │
│                                                                    │
│ ROS 2 (Robot Operating System 2) is a flexible framework for      │
│ writing robot software. It is a collection of tools, libraries,   │
│ and conventions...                                                 │
│                                                                    │
│ <!-- Navigation buttons -->                                        │
│ <NavigationButtons prev="intro" next="simulation" />              │
└───────────────────────────────────────────────────────────────────┘
         │
         │ [markdown_processor.py]
         │ • Strip frontmatter
         │ • Remove imports
         │ • Remove JSX components
         │ • Extract metadata
         ▼
Clean Document
┌───────────────────────────────────────────────────────────────────┐
│ content: "# ROS 2 Foundations\n\nROS 2 (Robot Operating System   │
│           2) is a flexible framework for writing robot            │
│           software. It is a collection of tools..."               │
│                                                                    │
│ metadata: {                                                        │
│   book_title: "Physical AI & Humanoid Robotics Textbook",         │
│   chapter: "Ros2 Foundations",                                     │
│   section: "Module 1 Ros2",                                        │
│   source_file: "02-ros2-foundations/module-1-ros2.md"             │
│ }                                                                  │
└───────────────────────────────────────────────────────────────────┘
         │
         │ [chunker.py]
         │ • Tokenize (tiktoken)
         │ • Split into 400-token chunks
         │ • Apply 100-token overlap
         │ • Add chunk metadata
         ▼
Text Chunks (87 total)
┌───────────────────────────────────────────────────────────────────┐
│ Chunk 1:                                                           │
│ {                                                                  │
│   text: "# ROS 2 Foundations\n\nROS 2 (Robot Operating System 2) │
│          is a flexible framework for writing robot software...",  │
│   metadata: {                                                      │
│     ...original_metadata,                                          │
│     chunk_index: 0,                                                │
│     total_chunks: 2,                                               │
│     token_count: 387                                               │
│   }                                                                │
│ }                                                                  │
│                                                                    │
│ Chunk 2:                                                           │
│ {                                                                  │
│   text: "...framework for writing robot software. It is a         │
│          collection of tools, libraries, and conventions that...",│
│   metadata: {                                                      │
│     ...original_metadata,                                          │
│     chunk_index: 1,                                                │
│     total_chunks: 2,                                               │
│     token_count: 412                                               │
│   }                                                                │
│ }                                                                  │
└───────────────────────────────────────────────────────────────────┘
         │
         │ [embeddings.py]
         │ • Call Gemini API
         │ • Generate 768-dim vectors
         │ • Rate limit: 0.1s delay
         ▼
Embeddings (768-dimensional)
┌───────────────────────────────────────────────────────────────────┐
│ Chunk 1 embedding: [0.0234, -0.0123, 0.0456, ..., 0.0891]        │
│ Chunk 2 embedding: [0.0198, -0.0087, 0.0521, ..., 0.0734]        │
│ ...                                                                │
│ Chunk 87 embedding: [0.0312, -0.0234, 0.0678, ..., 0.0923]       │
└───────────────────────────────────────────────────────────────────┘
         │
         │ [vector_store.py]
         │ • Generate UUID (MD5-based)
         │ • Create PointStruct
         │ • Upsert to Qdrant
         ▼
Vector Points in Qdrant
┌───────────────────────────────────────────────────────────────────┐
│ Point 1:                                                           │
│ {                                                                  │
│   id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",                     │
│   vector: [0.0234, -0.0123, 0.0456, ..., 0.0891],                │
│   payload: {                                                       │
│     text: "# ROS 2 Foundations...",                               │
│     book_title: "Physical AI & Humanoid Robotics Textbook",       │
│     chapter: "Ros2 Foundations",                                   │
│     section: "Module 1 Ros2",                                      │
│     source_file: "02-ros2-foundations/module-1-ros2.md",          │
│     chunk_index: 0,                                                │
│     total_chunks: 2,                                               │
│     token_count: 387                                               │
│   }                                                                │
│ }                                                                  │
│                                                                    │
│ ... (87 total points)                                              │
└───────────────────────────────────────────────────────────────────┘
```

## Error Handling & Resilience

```
┌──────────────────────────────────────────────────────────────────────┐
│                     ERROR HANDLING ARCHITECTURE                      │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Configuration Errors (.env validation)                             │
├─────────────────────────────────────────────────────────────────────┤
│  Error: Missing GEMINI_API_KEY                                      │
│  Handler: Raise ValueError with clear message                       │
│  Recovery: User sets environment variable                           │
│  Log: "Missing required environment variable: GEMINI_API_KEY"       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  File Processing Errors (markdown_processor.py)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Error: Empty file after cleaning                                   │
│  Handler: Skip file, log warning, continue                          │
│  Recovery: Automatic (skip and continue)                            │
│  Log: "Empty content after cleaning: resources.md"                  │
│                                                                      │
│  Error: File not readable (permissions)                             │
│  Handler: Log error, skip file, continue                            │
│  Recovery: User fixes permissions                                   │
│  Log: "Failed to process file.md: Permission denied"                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  API Rate Limit Errors (embeddings.py)                              │
├─────────────────────────────────────────────────────────────────────┤
│  Error: 429 Quota exceeded (15 req/min, 1,500/day)                 │
│  Handler: Catch RateLimitError, log, provide wait time              │
│  Recovery: User waits or enables billing                            │
│  Log: "Rate limit exceeded. Retry in 31.4s"                         │
│                                                                      │
│  Error: 401 Unauthorized (invalid API key)                          │
│  Handler: Raise exception immediately (unrecoverable)               │
│  Recovery: User updates GEMINI_API_KEY                              │
│  Log: "Gemini API authentication failed. Check API key"             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Vector Storage Errors (vector_store.py)                            │
├─────────────────────────────────────────────────────────────────────┤
│  Error: Qdrant connection timeout                                   │
│  Handler: Retry with exponential backoff (3 attempts)               │
│  Recovery: Automatic retry or user checks network                   │
│  Log: "Qdrant connection timeout. Retry 1/3..."                     │
│                                                                      │
│  Error: Collection already exists (recreate=False)                  │
│  Handler: Skip creation, log info, continue                         │
│  Recovery: Automatic (use existing collection)                      │
│  Log: "Collection data_collection already exists"                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        SECURITY DESIGN                               │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Secrets Management                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  .env file (NOT committed)                                           │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ GEMINI_API_KEY=AIzaSy...                                      │ │
│  │ QDRANT_API_KEY=eyJhbG...                                       │ │
│  └───────────────────────────────────────────────────────────────┘ │
│            │                                                         │
│            │ Loaded by python-dotenv                                │
│            ▼                                                         │
│  Environment Variables (memory only)                                │
│            │                                                         │
│            │ Accessed by code                                       │
│            ▼                                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ config = {'gemini_api_key': os.getenv('GEMINI_API_KEY')}     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│            │                                                         │
│            │ Redacted in logs                                       │
│            ▼                                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ logger.info("GEMINI_API_KEY: [REDACTED]")                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  .gitignore                                                          │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ .env           # ✅ Actual secrets ignored                    │ │
│  │ .env.local     # ✅ All variants ignored                      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  .env.example (Committed)                                            │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ GEMINI_API_KEY=your_api_key_here  # ✅ Placeholders only      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Logging Security                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ✅ SAFE: Redacted API keys                                         │
│  logger.info("GEMINI_API_KEY: [REDACTED]")                          │
│                                                                      │
│  ✅ SAFE: Partial URLs (domain only)                                │
│  logger.info("QDRANT_URL: https://xxx.gcp.cloud.qdrant.io:6333")   │
│                                                                      │
│  ✅ SAFE: Collection names, counts                                  │
│  logger.info("Inserted 87 points to data_collection")               │
│                                                                      │
│  ❌ NEVER: Full API keys, tokens                                    │
│  logger.info(f"Using key: {api_key}")  # WRONG!                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Data Privacy                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Book Content:         Public (GitHub Pages)                         │
│  Embeddings:           Sent to Gemini API (Google)                  │
│  Vectors:              Stored in Qdrant Cloud                       │
│  Metadata:             No PII (only book structure)                 │
│                                                                      │
│  TLS Encryption:       ✅ All API calls (HTTPS)                     │
│  At-Rest Encryption:   ✅ Qdrant Cloud (AES-256)                    │
│  Access Control:       ✅ API keys required                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Diagrams Created**: 2026-01-03

**Purpose**: Visual reference for hackathon demo, code review, and documentation

**Status**: Complete
