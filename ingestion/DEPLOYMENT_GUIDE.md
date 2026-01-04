# Deployment & Verification Guide

## Pipeline Test Results

### Test Run: 2026-01-03

**Status**: ✅ Partial Success (Rate Limit Encountered)

**Results**:
- ✅ Configuration loaded successfully
- ✅ 17 documents processed from Docusaurus
- ✅ 87 chunks created (300-500 tokens each with overlap)
- ❌ Embedding generation hit Gemini API rate limit (Free tier quota exceeded)

**Logs**:
```
[1/6] Loading configuration... ✓
[2/6] Processing markdown files... ✓ (17 documents)
[3/6] Chunking documents... ✓ (87 chunks)
[4/6] Generating embeddings... ✗ (Quota exceeded)
```

## Gemini API Rate Limits

### Free Tier Quotas

The Gemini embedding API has strict rate limits on the free tier:

- **Per Minute**: 15 requests
- **Per Day**: 1,500 requests
- **Model**: `embedding-001`

### Quota Exceeded Error

If you see this error:
```
429 You exceeded your current quota, please check your plan and billing details.
Quota exceeded for metric: generativelanguage.googleapis.com/embed_content_free_tier_requests
```

**Solutions**:

1. **Wait and Retry**:
   ```bash
   # Wait 60 seconds then retry
   sleep 60
   python ingest_book.py
   ```

2. **Reduce Rate Limit Delay** (if under daily limit):
   - Edit `.env`: `RATE_LIMIT_DELAY=1.0`
   - This slows embedding generation to ~60 requests/minute

3. **Increase Chunk Size** (reduce total chunks):
   - Edit `.env`: `CHUNK_SIZE=500`
   - Fewer chunks = fewer API calls

4. **Enable Billing** (if needed):
   - Visit https://ai.google.dev/gemini-api/docs/rate-limits
   - Enable billing to increase quotas
   - Paid tier: 1,500 requests/minute, 1M requests/day

5. **Use Alternative Embedding Service**:
   - Modify `embeddings.py` to use OpenAI, Cohere, or Voyage AI
   - Update `requirements.txt` with new SDK

## Successful Pipeline Components

The following components were **verified working**:

### 1. Markdown Processing ✅

- **Files Found**: 18 markdown files
- **Files Processed**: 17 (1 empty file skipped)
- **Chapters Extracted**: 7 chapters
- **Metadata Preserved**: book_title, chapter, section, source_file

**Sample Output**:
```
Processed intro.md: chapter=Introduction, section=Intro
Processed module-1-ros2.md: chapter=Ros2 Foundations, section=Module 1 Ros2
Processed digital-twins.md: chapter=Simulation, section=Digital Twins
```

### 2. Text Chunking ✅

- **Total Chunks**: 87
- **Chunk Size**: 300-500 tokens (avg ~400)
- **Overlap**: 100 tokens
- **Token Counting**: tiktoken (cl100k_base)

**Sample Chunks**:
```
Created 1 chunks from 01-introduction\intro.md
Created 2 chunks from 02-ros2-foundations\module-1-ros2.md
Created 1 chunks from 02-ros2-foundations\ros2-hands-on.md
Created 1 chunks from 03-simulation\digital-twins.md
Created 1 chunks from 03-simulation\gazebo-unity.md
```

### 3. Configuration Management ✅

- **Environment Variables**: Loaded from `.env`
- **API Keys**: Redacted in logs (secure)
- **Paths**: Relative paths work correctly

## Next Steps

### Option 1: Wait for Quota Reset

The Gemini free tier quota resets:
- **Per Minute**: Every 60 seconds
- **Per Day**: At midnight UTC

**Action**:
```bash
# Wait 2 minutes then retry
sleep 120
cd ingestion
python ingest_book.py
```

### Option 2: Reduce Request Rate

Add rate limiting to `.env`:

```bash
# Edit .env
echo "RATE_LIMIT_DELAY=2.0" >> ../.env
```

Then retry:
```bash
python ingest_book.py
```

### Option 3: Use Cached Embeddings (For Testing)

For development/testing, you can mock embeddings:

**Create `ingestion/mock_embeddings.py`**:
```python
import numpy as np

class MockEmbeddings:
    def __init__(self, *args, **kwargs):
        self.embedding_dim = 768

    def embed_text(self, text):
        # Deterministic mock embedding from text hash
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(768).tolist()

    def embed_batch(self, texts, **kwargs):
        return [self.embed_text(t) for t in texts]

    def get_embedding_dimension(self):
        return self.embedding_dim
```

**Modify `ingest_book.py` line 130**:
```python
# For testing only
from mock_embeddings import MockEmbeddings
embedder = MockEmbeddings()
# embedder = GeminiEmbeddings(api_key=config['gemini_api_key'])
```

## Production Deployment Checklist

When quota is available:

- [ ] **Pre-Deployment**:
  - [ ] Verify Gemini API key is valid
  - [ ] Check Gemini API quota: https://ai.dev/usage
  - [ ] Verify Qdrant Cloud connection
  - [ ] Test with small doc set first (1-2 files)

- [ ] **Deployment**:
  - [ ] Run ingestion: `python ingest_book.py`
  - [ ] Monitor logs: `tail -f ingestion.log`
  - [ ] Check Qdrant dashboard for points

- [ ] **Verification**:
  - [ ] Run test search: `python test_search.py --run-samples`
  - [ ] Check similarity scores > 0.3
  - [ ] Verify metadata correctness
  - [ ] Test filtered search by chapter

- [ ] **Post-Deployment**:
  - [ ] Document collection stats
  - [ ] Export sample queries and results
  - [ ] Update RAG agent configuration

## Troubleshooting

### Issue: Quota Exceeded (Current)

**Error**: `429 You exceeded your current quota`

**Root Cause**: Gemini free tier limits hit

**Fix**:
1. Wait 60+ seconds for per-minute quota
2. Wait until next day for daily quota
3. Add `RATE_LIMIT_DELAY=2.0` to `.env`
4. Enable billing on Gemini API

### Issue: Empty Collection

**Symptom**: Qdrant shows 0 points after ingestion

**Fix**:
1. Check logs for errors: `cat ingestion.log`
2. Verify Qdrant credentials in `.env`
3. Test Qdrant connection:
   ```bash
   curl -X GET "$QDRANT_URL/collections" \
     -H "api-key: $QDRANT_API_KEY"
   ```

### Issue: Low Search Quality

**Symptom**: Similarity search returns irrelevant results

**Fix**:
1. Increase `score_threshold` in `test_search.py`
2. Use metadata filters: `filter_dict={"chapter": "Ros2 Foundations"}`
3. Review chunking strategy (size/overlap)
4. Re-ingest with different chunk size

## Monitoring

### Check Gemini API Usage

Visit: https://ai.dev/usage?tab=rate-limit

- View requests per minute/day
- Check quota limits
- Monitor billing (if enabled)

### Check Qdrant Cloud

Visit: https://cloud.qdrant.io/

- Collection: `data_collection`
- Expected points: 87 (if ingestion completes)
- Vector dimension: 768
- Distance metric: Cosine

## Cost Estimates

### Free Tier (Current Setup)

- **Gemini API**: $0 (1,500 requests/day free)
- **Qdrant Cloud**: $0 (1 GB storage free)
- **Total**: $0/month

**Limitations**:
- Gemini: 15 requests/minute
- Qdrant: 1 GB storage (~250K chunks)

### Paid Tier (If Needed)

- **Gemini API**: $0.00025 per embedding (87 chunks = $0.02)
- **Qdrant Cloud**: $25/month (Starter plan, 2 GB)
- **Total**: ~$25/month + $0.02 one-time ingestion

## Success Criteria (To Be Verified)

After successful ingestion:

- [ ] All 17 documents ingested
- [ ] 87 chunks created (300-500 tokens)
- [ ] 87 embeddings generated (768-dim)
- [ ] 87 points stored in Qdrant
- [ ] Metadata preserved for all chunks
- [ ] Similarity search returns relevant results
- [ ] Score threshold filtering works
- [ ] Chapter/section filters work

## Contact & Support

For issues:

1. Check logs: `ingestion.log`
2. Review Gemini docs: https://ai.google.dev/gemini-api/docs
3. Review Qdrant docs: https://qdrant.tech/documentation/
4. Open GitHub issue with redacted logs

---

**Last Updated**: 2026-01-03 04:51 UTC

**Status**: Pipeline tested, awaiting quota reset for full ingestion
