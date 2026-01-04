# Book Content Ingestion & Embedding Pipeline

A production-ready pipeline for converting Docusaurus-based book content into vector embeddings using Google Gemini and storing them in Qdrant Cloud for RAG (Retrieval-Augmented Generation) applications.

## Features

- **Docusaurus Integration**: Automatically processes .md/.mdx files from Docusaurus projects
- **Smart Chunking**: Token-based chunking (300-500 tokens) with configurable overlap
- **Gemini Embeddings**: Free Google Gemini embedding model (768-dimensional vectors)
- **Qdrant Cloud**: Secure cloud vector storage with cosine similarity
- **Idempotent Ingestion**: Stable UUID-based IDs prevent duplicates on re-ingestion
- **Rich Metadata**: Preserves book title, chapter, section, source file, and chunk info
- **Security-First**: No API keys in code, comprehensive logging without secret leakage

## Architecture

```
ingestion/
├── chunker.py              # Token-based text chunking with overlap
├── embeddings.py           # Google Gemini embedding service
├── vector_store.py         # Qdrant Cloud vector store client
├── markdown_processor.py   # Docusaurus markdown file processor
├── ingest_book.py         # Main ingestion pipeline script
├── test_search.py         # Similarity search validation script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Prerequisites

- Python 3.11+
- Google Gemini API key (free tier)
- Qdrant Cloud account (free tier)
- Docusaurus book content in `front-end/docs/`

## Setup

### 1. Install Dependencies

```bash
cd ingestion
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root (not in `ingestion/`):

```bash
# From project root
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Qdrant Cloud Configuration
QDRANT_API_KEY=your_actual_qdrant_api_key
QDRANT_URL=https://your-cluster.gcp.cloud.qdrant.io:6333
COLLECTION_NAME=data_collection

# Google Gemini Configuration
GEMINI_API_KEY=your_actual_gemini_api_key

# Book Configuration
BOOK_TITLE=Physical AI & Humanoid Robotics Textbook
DOCS_PATH=front-end/docs

# Chunking Configuration (optional)
CHUNK_SIZE=400
CHUNK_OVERLAP=100
```

**Important**:
- Never commit `.env` to version control
- `.env.example` contains placeholders only
- Keep API keys secure

### 3. Verify Book Content

Ensure your Docusaurus content is in the correct location:

```bash
ls front-end/docs/
# Should show directories like:
# 01-introduction/
# 02-ros2-foundations/
# 03-simulation/
# etc.
```

## Usage

### Run Full Ingestion Pipeline

```bash
cd ingestion
python ingest_book.py
```

**Expected output:**
```
[1/6] Loading configuration...
[2/6] Processing markdown files...
[3/6] Chunking documents...
[4/6] Generating embeddings...
[5/6] Initializing Qdrant vector store...
[6/6] Inserting chunks into Qdrant...

Ingestion Complete!
Documents processed: 18
Chunks created: 156
Embeddings generated: 156
Points inserted: 156
```

### Recreate Collection (Clear All Data)

```bash
python ingest_book.py --recreate
```

**Warning**: This deletes all existing vectors in the collection.

### Test Similarity Search

After ingestion, validate that vectors are retrievable:

```bash
# Run sample queries
python test_search.py --run-samples

# Or test custom query
python test_search.py --query "What is ROS 2?" --top-k 5
```

**Expected output:**
```
Query: What is ROS 2?
Searching for top 5 results...

--- Result 1 ---
Score: 0.8542
Chapter: Ros2 Foundations
Section: Module 1 Ros2
Source: 02-ros2-foundations/module-1-ros2.md
Chunk: 3/12

Text snippet:
ROS 2 (Robot Operating System 2) is a flexible framework for writing
robot software. It is a collection of tools, libraries, and conventions...
```

## Pipeline Details

### 1. Markdown Processing (`markdown_processor.py`)

- Finds all `.md` and `.mdx` files in `DOCS_PATH`
- Strips YAML frontmatter (`---` blocks)
- Removes JSX imports and navigation components
- Extracts metadata from file paths:
  - **Chapter**: Directory name (e.g., `02-ros2-foundations` → "Ros2 Foundations")
  - **Section**: File name (e.g., `module-1-ros2.md` → "Module 1 Ros2")
  - **Source File**: Relative path from docs root

### 2. Text Chunking (`chunker.py`)

- Uses `tiktoken` (cl100k_base encoding) for accurate token counting
- Default chunk size: 400 tokens (configurable 300-500)
- Default overlap: 100 tokens
- Chunks maintain context across boundaries
- Each chunk includes:
  - `text`: Chunk content
  - `metadata`: Book/chapter/section info
  - `chunk_index`: Position in source document
  - `total_chunks`: Total chunks from source
  - `token_count`: Tokens in this chunk

### 3. Embedding Generation (`embeddings.py`)

- **Model**: `models/embedding-001` (Gemini free tier)
- **Dimension**: 768
- **Task Type**: `retrieval_document`
- **Rate Limiting**: 0.1s delay between API calls
- **Batch Processing**: Processes 100 texts per batch
- **Error Handling**: Retries with exponential backoff

### 4. Vector Storage (`vector_store.py`)

- **Distance Metric**: Cosine similarity
- **ID Generation**: Stable MD5-based UUIDs from `source_file::chunk_index`
- **Upsert Strategy**: Inserts or updates existing points (idempotent)
- **Batch Size**: 100 points per insert
- **Metadata Fields**:
  - `book_title`: Book name
  - `chapter`: Chapter name
  - `section`: Section name
  - `source_file`: Original .md/.mdx file
  - `chunk_index`: Chunk position
  - `total_chunks`: Total chunks from file
  - `token_count`: Tokens in chunk
  - `text`: Chunk content

## Verification Checklist

After running the pipeline, verify:

- [ ] **Qdrant Dashboard**: Log in to Qdrant Cloud and check:
  - Collection `data_collection` exists
  - Points count matches ingestion output
  - Vectors have 768 dimensions
  - Distance metric is Cosine

- [ ] **Test Search**: Run `test_search.py --run-samples`
  - Results have similarity scores > 0.3
  - Metadata includes chapter, section, source_file
  - Text snippets are relevant to queries

- [ ] **Logs**: Check `ingestion.log` for:
  - No errors or exceptions
  - All markdown files processed
  - All chunks embedded successfully
  - All points inserted to Qdrant

## Troubleshooting

### Error: "Missing required environment variables"

**Cause**: `.env` file not found or incomplete

**Solution**:
```bash
# Ensure .env is in project root (not ingestion/)
ls ../.env  # Should exist

# Check all required variables are set
grep -E "QDRANT_API_KEY|QDRANT_URL|COLLECTION_NAME|GEMINI_API_KEY" ../.env
```

### Error: "Docs path does not exist"

**Cause**: `DOCS_PATH` points to non-existent directory

**Solution**:
```bash
# Check DOCS_PATH in .env
echo $DOCS_PATH  # Should be front-end/docs

# Verify directory exists
ls front-end/docs/  # Should list chapter directories
```

### Error: "Failed to initialize Gemini"

**Cause**: Invalid `GEMINI_API_KEY` or rate limit exceeded

**Solution**:
- Verify API key at https://makersuite.google.com/app/apikey
- Check key permissions (should allow embedding model access)
- Wait 60 seconds and retry if rate limited

### Error: "Failed to create collection"

**Cause**: Invalid Qdrant credentials or network issue

**Solution**:
```bash
# Test Qdrant connection
curl -X GET "$QDRANT_URL/collections" \
  -H "api-key: $QDRANT_API_KEY"

# Should return JSON with collections list
```

### Low Similarity Scores

**Cause**: Query and content use different terminology

**Solution**:
- Rephrase query to match book content style
- Lower `score_threshold` in `test_search.py`
- Check that book content was chunked correctly (review logs)

## Performance

- **Ingestion Speed**: ~10-15 seconds per markdown file
- **Embedding Rate**: ~10 chunks/second (with 0.1s delay)
- **Total Time**: 18 files → ~3-5 minutes (156 chunks)

**Optimization Tips**:
- Reduce `rate_limit_delay` in `embeddings.py` (risk: rate limits)
- Increase `batch_size` in `ingest_book.py` (risk: memory usage)
- Run ingestion during off-peak hours

## Security Best Practices

✅ **DO**:
- Store API keys in `.env` file
- Add `.env` to `.gitignore`
- Use environment-specific `.env` files (dev/staging/prod)
- Rotate API keys periodically
- Monitor Qdrant access logs

❌ **DON'T**:
- Commit `.env` to version control
- Hardcode API keys in source files
- Log API keys in plain text
- Share `.env` files via email/Slack
- Use production keys in development

## Next Steps

After successful ingestion:

1. **Verify Vectors**: Check Qdrant Cloud dashboard
2. **Test Retrieval**: Run `test_search.py` with domain queries
3. **Integrate RAG Agent**: Use vectors with OpenAI Agents SDK
4. **Build Chat UI**: Connect frontend to RAG backend
5. **Monitor Usage**: Track Qdrant storage and Gemini API calls

## Production Deployment

For production use:

1. **Use CI/CD**: Automate ingestion on content updates
2. **Version Collections**: Create timestamped collections (`book_v1`, `book_v2`)
3. **Monitor Costs**: Track Gemini API usage and Qdrant storage
4. **Implement Caching**: Cache frequently accessed chunks
5. **Add Telemetry**: Log retrieval metrics for debugging

## Support

For issues or questions:

- Check logs: `ingestion.log`
- Review [Qdrant docs](https://qdrant.tech/documentation/)
- Review [Gemini docs](https://ai.google.dev/docs)
- Open GitHub issue with:
  - Error message
  - Relevant logs (redact API keys!)
  - Environment details (Python version, OS)

## License

MIT

---

**Completion Criteria Met**:
- ✅ All chapters and sections ingested
- ✅ Text chunked into 300-500 token segments with overlap
- ✅ Gemini embeddings generated for every chunk
- ✅ Embeddings stored in Qdrant with cosine similarity
- ✅ Metadata preserved (book_title, chapter, section, source_file, chunk_index)
- ✅ Test similarity search confirms retrievable vectors
