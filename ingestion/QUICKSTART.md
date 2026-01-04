# Quick Start Guide

## Installation (30 seconds)

```bash
# 1. Navigate to ingestion directory
cd ingestion

# 2. Install dependencies
pip install -r requirements.txt
```

## Configuration (1 minute)

```bash
# 1. Copy environment template (from project root)
cp .env.example .env

# 2. Edit .env with your credentials
# - QDRANT_API_KEY (from Qdrant Cloud dashboard)
# - QDRANT_URL (from Qdrant Cloud cluster details)
# - GEMINI_API_KEY (from https://ai.google.dev/)
```

## Run Ingestion (5-10 minutes)

```bash
# From ingestion/ directory
python ingest_book.py
```

**Expected Output**:
```
[1/6] Loading configuration... ✓
[2/6] Processing markdown files... ✓
[3/6] Chunking documents... ✓
[4/6] Generating embeddings... ✓
[5/6] Initializing Qdrant vector store... ✓
[6/6] Inserting chunks into Qdrant... ✓

Ingestion Complete!
Documents processed: 17
Chunks created: 87
Points inserted: 87
```

## Test Search

```bash
# Run sample queries
python test_search.py --run-samples

# Or test custom query
python test_search.py --query "What is ROS 2?" --top-k 5
```

## Troubleshooting

### Rate Limit Error

If you see `429 Quota exceeded`:

**Solution 1**: Wait 60 seconds, retry
```bash
sleep 60 && python ingest_book.py
```

**Solution 2**: Add rate limiting to `.env`
```bash
echo "RATE_LIMIT_DELAY=2.0" >> ../.env
python ingest_book.py
```

### Path Error

If you see `Docs path does not exist`:

**Fix**: Ensure `.env` has correct path relative to ingestion/
```bash
# From ingestion/ directory
DOCS_PATH=../front-end/docs  # ✓ Correct
DOCS_PATH=front-end/docs     # ✗ Wrong
```

### Import Errors

If you see `ModuleNotFoundError`:

**Fix**: Install requirements
```bash
pip install -r requirements.txt
```

## Verification

1. **Check Qdrant Dashboard**:
   - Login to https://cloud.qdrant.io/
   - Navigate to `data_collection`
   - Verify 87 points stored

2. **Run Test Search**:
   - Should return relevant results
   - Scores should be > 0.3
   - Metadata should include chapter, section

## Next Steps

1. ✅ Ingestion complete
2. → Implement RAG agent (OpenAI Agents SDK)
3. → Connect to chat UI
4. → Deploy to production

## Need Help?

- **Logs**: Check `ingestion.log` for errors
- **Docs**: See `README.md` for detailed guide
- **Schema**: See `QDRANT_SCHEMA.md` for vector structure
- **Deployment**: See `DEPLOYMENT_GUIDE.md` for prod steps

---

**Estimated Time to Production**:
- Setup: 2 minutes
- Ingestion: 5-10 minutes
- Testing: 2 minutes
- **Total**: ~15 minutes (if no quota issues)
