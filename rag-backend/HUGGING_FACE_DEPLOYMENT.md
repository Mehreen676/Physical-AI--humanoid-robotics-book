# Hugging Face Spaces Deployment Guide

## Overview
This guide explains how to deploy the RAG Chatbot Backend on Hugging Face Spaces.

## Prerequisites
- Hugging Face account with Spaces enabled
- Docker knowledge (optional - Spaces can auto-build from Dockerfile)
- Required environment variables configured

## Step 1: Prepare Repository

Ensure these files exist in your repo root (`rag-backend/`):
```
✓ Dockerfile
✓ .dockerignore
✓ requirements.txt
✓ main.py
✓ src/
✓ .env.example
```

## Step 2: Environment Variables

On Hugging Face Spaces, add these secrets in the Space settings:

```env
QDRANT_URL=https://your-qdrant-cloud-url
QDRANT_API_KEY=your-qdrant-api-key
DATABASE_URL=postgresql://user:pass@host/dbname
OPENAI_API_KEY=your-openai-api-key
SECRET_KEY=your-secret-key-for-jwt
```

## Step 3: Create Space

1. Go to https://huggingface.co/new-space
2. Select "Docker" as the Space SDK
3. Choose a name: `rag-chatbot-backend`
4. Set visibility to "Private" (recommended)

## Step 4: Push Code

```bash
git push huggingface main
```

Or manually upload the repository files.

## Step 5: Monitor Deployment

- Spaces will automatically build the Docker image
- Check the logs for any build errors
- Once deployed, your API will be available at:
  ```
  https://huggingface.co/spaces/[username]/rag-chatbot-backend
  ```

## Troubleshooting

### Error: "/src": not found
**Cause:** Docker build context doesn't include the src directory.

**Solution:** Ensure these files are in the repo:
- `.dockerignore` (properly formatted)
- `Dockerfile` (uses correct COPY paths)
- `src/` directory at root level

**Check:**
```bash
ls -la rag-backend/
# Should show: src/, main.py, Dockerfile, .dockerignore, requirements.txt
```

### Error: "ModuleNotFoundError: No module named 'src'"
**Cause:** PYTHONPATH not set correctly.

**Solution:** Dockerfile sets `PYTHONPATH=/app:$PYTHONPATH` which allows imports from root.

### Error: "Health check failed"
**Cause:** App not starting within 15 seconds.

**Solution:** Check app logs:
```bash
docker logs <container-id>
```

Increase start-period in HEALTHCHECK if needed.

### Memory/CPU Issues
Hugging Face Spaces free tier is limited. If app crashes:
1. Reduce workers: Change `--workers 1` (already set)
2. Optimize dependencies: Remove unused packages
3. Use smaller models if applicable
4. Upgrade to Pro tier for more resources

## API Endpoints

Once deployed, access your API:

```bash
# Health check
curl https://[username].hf.space/health

# Query endpoint
curl -X POST https://[username].hf.space/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RAG?"}'

# API documentation
https://[username].hf.space/docs
```

## Performance Tuning

For Hugging Face Spaces:
- **Workers:** Set to 1 (free tier memory limitation)
- **Timeout:** Increase if getting timeouts
- **Start-period:** Set to 15-30s for slow startups
- **Cache:** Use COPY requirements optimization

## File Structure

```
rag-backend/
├── Dockerfile              # Multi-stage build
├── .dockerignore          # Exclude unnecessary files
├── requirements.txt       # Python dependencies
├── main.py               # FastAPI entry point
├── src/
│   ├── api.py           # FastAPI app definition
│   ├── agent.py         # OpenAI Agent SDK
│   ├── config.py        # Configuration
│   ├── embeddings.py    # Embedding generation
│   ├── retrieval_service.py
│   ├── generation_service.py
│   └── ... (other modules)
└── .env.example         # Example environment variables
```

## Important Notes

1. **Build Cache:** Hugging Face Spaces caches Docker layers, so push `.dockerignore` first
2. **Cold Start:** First request after deployment is slower (~30-60s)
3. **Secrets:** Use Hugging Face Spaces secrets panel, NOT `.env` file
4. **Logs:** Access logs via Spaces interface for debugging
5. **Pricing:** Free tier has limitations; check HF Spaces pricing for production

## Next Steps

After successful deployment:
1. Test all endpoints via Swagger UI (`/docs`)
2. Set up monitoring/alerts
3. Configure CI/CD for auto-deployment
4. Add API authentication (JWT tokens included)
5. Monitor resource usage in Spaces settings
