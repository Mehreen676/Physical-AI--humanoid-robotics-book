# Hugging Face Spaces Deployment Guide

## For User: amehreen699

Complete step-by-step guide to deploy RAG Chatbot Backend on Hugging Face Spaces.

---

## Step 1: Create Hugging Face Space

1. Go to: https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in the form:
   - **Owner**: amehreen699 (your username)
   - **Space name**: `rag-chatbot-backend` (or your preferred name)
   - **License**: Select appropriate license
   - **Space SDK**: **Docker** ⚠️ IMPORTANT
   - **Visibility**: **Private** (recommended for now)
   - Click **Create Space**

4. You'll be redirected to your new space. Note the URL:
   ```
   https://huggingface.co/spaces/amehreen699/rag-chatbot-backend
   ```

---

## Step 2: Add Environment Secrets

1. In your Space, click **Settings** (gear icon)
2. Scroll to **Repository Secrets**
3. Add these secrets (get values from your .env file):

   | Secret Name | Example Value | Required |
   |-------------|---------------|----------|
   | `QDRANT_URL` | `https://your-qdrant-url.com` | ✅ Yes |
   | `QDRANT_API_KEY` | `your-api-key` | ✅ Yes |
   | `DATABASE_URL` | `postgresql://user:pass@host/db` | ✅ Yes |
   | `OPENAI_API_KEY` | `sk-proj-...` | ✅ Yes |
   | `SECRET_KEY` | `your-secret-key-min-32-chars` | ✅ Yes |

4. Click **Save** for each secret

---

## Step 3: Push Code to Hugging Face

Run these commands from your local repository:

```bash
# Navigate to your project
cd /path/to/Spec-Driven-Development-Hackathons-main/Hackathon_I

# Add Hugging Face as remote (replace with your space name)
git remote add huggingface https://huggingface.co/spaces/amehreen699/rag-chatbot-backend.git

# Push the rag-backend directory to the Spaces repo
git subtree push --prefix rag-backend huggingface main
```

**Note**: If `subtree push` fails, try:
```bash
git clone https://huggingface.co/spaces/amehreen699/rag-chatbot-backend hf-space
cp -r rag-backend/* hf-space/
cd hf-space
git add .
git commit -m "Deploy RAG Chatbot Backend"
git push
cd ..
```

---

## Step 4: Monitor Build

1. Go back to your Space: https://huggingface.co/spaces/amehreen699/rag-chatbot-backend
2. Click **App** tab
3. Watch the build logs in real-time
4. Wait for: **"Running on local URL"** message
5. ⚠️ **First build takes 5-10 minutes** - be patient!

---

## Step 5: Test Your Deployment

Once the app is running, test the endpoints:

### Health Check
```bash
curl https://amehreen699-rag-chatbot-backend.hf.space/health
```

### API Documentation
```
https://amehreen699-rag-chatbot-backend.hf.space/docs
```

### Query Endpoint
```bash
curl -X POST https://amehreen699-rag-chatbot-backend.hf.space/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "mode": "full_book"
  }'
```

---

## Configuration Summary

| Component | Location | Status |
|-----------|----------|--------|
| **Docker Image** | rag-backend/Dockerfile | ✅ Ready |
| **Entry Point** | rag-backend/main.py | ✅ Ready |
| **FastAPI App** | rag-backend/src/api.py | ✅ Ready |
| **Enterprise App** | rag-backend/src/main.py | ✅ Ready (with slowapi) |
| **Requirements** | rag-backend/requirements.txt | ✅ Ready |
| **Path Config** | All Python files | ✅ Fixed |
| **.dockerignore** | rag-backend/.dockerignore | ✅ Ready |

---

## Common Issues & Solutions

### Issue: "Build failed"
**Solution:** Check build logs in App tab. Usually due to:
- Missing environment variables (add in Settings → Secrets)
- Network timeout (wait and retry)
- Port conflict (should be fine on HF)

### Issue: "ModuleNotFoundError: No module named 'src'"
**Solution:** ✅ Already fixed in latest commit
- Path configuration added to all entry points
- PYTHONPATH set in Dockerfile
- Automatic path discovery enabled

### Issue: "Connection refused" / "Health check failed"
**Solution:**
- Wait 30+ seconds for app to fully start
- Check logs for actual error
- Verify secrets are set correctly

### Issue: "Slow to respond"
**Reason:** Free tier limitations
**Solution:**
- First request takes longer (~30s) as container warms up
- Subsequent requests are faster
- Consider upgrading to Pro tier for production

### Issue: "Rate limit exceeded"
**Solution:** Use Enterprise version (src/main.py) with slowapi
- Or upgrade HF Space tier
- Or implement custom rate limiting

---

## Deployment Checklist

Before pushing, verify:

- ✅ All code committed (`git status` shows clean)
- ✅ Dockerfile exists and is valid
- ✅ requirements.txt has all dependencies
- ✅ .dockerignore file present
- ✅ main.py can be imported
- ✅ Environment variables planned
- ✅ Hugging Face Space created (Private recommended)
- ✅ Secrets added in Space Settings

---

## After Deployment

### Accessing Your API

**Base URL:**
```
https://amehreen699-rag-chatbot-backend.hf.space
```

**Swagger UI (Interactive):**
```
https://amehreen699-rag-chatbot-backend.hf.space/docs
```

**ReDoc (Documentation):**
```
https://amehreen699-rag-chatbot-backend.hf.space/redoc
```

### Making Requests

**Example with Python:**
```python
import requests

url = "https://amehreen699-rag-chatbot-backend.hf.space/query"
data = {
    "query": "What is RAG?",
    "mode": "full_book"
}

response = requests.post(url, json=data)
print(response.json())
```

**Example with JavaScript:**
```javascript
const url = "https://amehreen699-rag-chatbot-backend.hf.space/query";
const data = {
  query: "What is RAG?",
  mode: "full_book"
};

fetch(url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data)
})
.then(r => r.json())
.then(data => console.log(data));
```

---

## Advanced: Using src/main.py Instead

If you want the full-featured version with rate limiting:

1. Update `rag-backend/main.py`:
   ```python
   from src.main import app  # Instead of src.api
   ```

2. Commit: `git add rag-backend/main.py && git commit -m "Use enterprise app version"`

3. Push to HF: `git subtree push --prefix rag-backend huggingface main`

This gives you:
- ✅ Rate limiting (slowapi)
- ✅ Enterprise authentication (MFA, OAuth, JWT)
- ✅ RBAC (Role-Based Access Control)
- ✅ API key management
- ✅ Analytics

---

## Support & Monitoring

### View Logs
1. Go to Space
2. Click **App** tab
3. Scroll down to see real-time logs

### Monitor Resource Usage
1. Settings → Logs
2. Check CPU, Memory, Disk usage

### Health Check (automated)
- Runs every 30 seconds
- Queries `/health` endpoint
- Restarts if unhealthy

---

## Next Steps

After successful deployment:

1. **Test all endpoints** via Swagger UI
2. **Integrate with frontend** (CORS enabled)
3. **Monitor performance** (check logs regularly)
4. **Scale if needed** (upgrade HF tier)
5. **Set up monitoring** (optional - use external service)

---

## Quick Command Reference

```bash
# Check if code is ready
git status

# View recent commits
git log --oneline -5

# See all branches
git branch -a

# Push to Hugging Face (from project root)
git subtree push --prefix rag-backend huggingface main

# Force push if needed (use with caution)
git push huggingface main --force

# View deployment URL
# https://huggingface.co/spaces/amehreen699/rag-chatbot-backend
```

---

## Your Deployment Status

| Item | Status |
|------|--------|
| Code Ready | ✅ Yes |
| Docker Config | ✅ Yes |
| Dependencies | ✅ Complete |
| Path Fixes | ✅ Applied |
| slowapi | ✅ Added |
| Enterprise Features | ✅ Available |
| Documentation | ✅ Complete |

**Ready to deploy!** 🚀

---

**Need help?** Check HF Space logs or the [Hugging Face Spaces Documentation](https://huggingface.co/docs/hub/spaces)
