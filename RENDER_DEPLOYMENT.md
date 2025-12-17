# Deploy to Render - Updated Guide

## Status: ✅ Code Fixed & Pushed to GitHub

The build and start commands have been corrected in `render.yaml`:
- Build Command: `cd rag-backend && pip install -r requirements.txt`
- Start Command: `cd rag-backend && uvicorn src.main:app --host 0.0.0.0 --port $PORT`

## Quick Deploy (If Already Connected to Render)

**1. Open Render Dashboard**
```
https://dashboard.render.com/
```

**2. Find your service**
- Look for `rag-chatbot-backend` in your services list

**3. Click "Deploy" button**
- Located in the top-right of the service page
- This will redeploy using the latest code from GitHub

**4. Watch deployment progress**
- Go to "Deployments" tab
- You'll see live build logs
- Wait for ✅ "Deploy successful" (takes 2-5 minutes)

---

## If Not Yet Connected to Render

**1. Go to Render**
```
https://render.com
```

**2. Sign up with GitHub** (if not already done)

**3. Create New Web Service**
- Click "New +"
- Select "Web Service"
- Select repo: `Physical-AI--humanoid-robotics-book`
- Branch: `feature/2-rag-chatbot-integration`

**4. Configure Service**

Fill in these fields:
```
Name: rag-chatbot-backend
Runtime: Python
Root Directory: (leave empty)
Build Command: cd rag-backend && pip install -r requirements.txt
Start Command: cd rag-backend && uvicorn src.main:app --host 0.0.0.0 --port $PORT
Plan: Free
```

**5. Add Environment Variables**

Click "Advanced" → "Add Environment Variable" for each:

| Key | Value |
|-----|-------|
| ENVIRONMENT | production |
| DEBUG | False |
| DATABASE_URL | (from rag-backend/.env) |
| GROQ_API_KEY | (from rag-backend/.env) |
| QDRANT_URL | (from rag-backend/.env) |
| QDRANT_API_KEY | (from rag-backend/.env) |
| HUGGINGFACE_API_TOKEN | (optional - only if using HuggingFace) |
| ALLOWED_ORIGINS_STR | `http://localhost:3000,http://localhost:8000,http://localhost:3001` |

**6. Click "Create Web Service"**
- Deployment starts automatically
- Monitor in "Deployments" tab

---

## Test Your Deployment

Once deployed, test the health endpoint:

```bash
curl https://[your-service-name].onrender.com/health
```

Expected response:
```json
{"status": "ok"}
```

---

## Architecture in Cloud

- **Embeddings:** HuggingFace API (free tier)
- **LLM:** Groq (free, fast inference)
- **Vector DB:** Qdrant Cloud
- **Database:** Neon PostgreSQL
- **Frontend:** Docusaurus (localhost:3000)

Everything works automatically! ✅
