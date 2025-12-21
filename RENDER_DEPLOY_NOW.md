# QUICK RENDER DEPLOYMENT

## For: RAG Chatbot Backend

### 10-Minute Setup

---

## STEP 1: Push Code to GitHub (1 minute)

Make sure your code is on GitHub on a branch (e.g., `main` or `feature/rag-backend`):

```bash
cd /path/to/Hackathon_I
git add rag-backend/
git commit -m "Deploy RAG Chatbot Backend to Render"
git push origin <your-branch>
```

✅ Code is on GitHub

---

## STEP 2: Connect GitHub to Render (2 minutes)

1. Go to: https://render.com
2. Click **"Sign up"** or **"Log in"**
3. Select **"GitHub"** authentication
4. Click **"Authorize render"** to give Render access to your repositories

✅ GitHub is connected

---

## STEP 3: Create Web Service (2 minutes)

1. Click **"Dashboard"** → **"New +"** → **"Web Service"**
2. **Search for repository**: Select your GitHub repo
3. Click **"Connect"**
4. **Select branch**: Choose the branch with your code (e.g., `main`)

✅ Repository is connected

---

## STEP 4: Configure Service (2 minutes)

Fill in these settings:

| Field | Value |
|-------|-------|
| **Name** | `rag-chatbot-backend` |
| **Runtime** | `Python 3` |
| **Region** | Closest to you |
| **Build Command** | `cd rag-backend && pip install -r requirements.txt` |
| **Start Command** | `cd rag-backend && uvicorn src.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |
| **Auto-deploy** | Toggle **ON** |

✅ Service is configured

---

## STEP 5: Add Environment Variables (2 minutes)

In the service settings, go to **"Environment"** and add these variables:

### Public Variables (copy-paste):

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
ALLOWED_ORIGINS_STR=https://yourdomain.com,https://rag-chatbot-backend.onrender.com,http://localhost:3000
```

### Secret Variables (get from your `.env` or create them):

| Key | Value | Get From |
|-----|-------|----------|
| `DATABASE_URL` | Your PostgreSQL connection string | Neon.tech |
| `QDRANT_URL` | Your Qdrant cluster URL | cloud.qdrant.io |
| `QDRANT_API_KEY` | Your Qdrant API key | cloud.qdrant.io |
| `OPENAI_API_KEY` | Your OpenAI API key | platform.openai.com |
| `SECRET_KEY` | Run: `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Generate locally |

✅ All variables are added

---

## STEP 6: Deploy! (1 minute)

1. Click **"Create Web Service"** button
2. Render will start building and deploying
3. Go to **"Deployments"** tab to watch progress

**Expected time**: 3-5 minutes

Watch for: ✅ **"Live"** status

---

## STEP 7: Test Your API (1 minute)

Once deployment says **"Live"**, test the health endpoint:

```bash
curl https://rag-chatbot-backend.onrender.com/health
```

Or visit in browser:
```
https://rag-chatbot-backend.onrender.com/docs
```

You should see Swagger UI with all endpoints!

---

## URL Format

Your API will be available at:
```
https://rag-chatbot-backend.onrender.com
```

**API Endpoints:**
- Health: `/health`
- Docs: `/docs`
- Query: `/query` (POST)
- Ingest: `/ingest` (POST)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Build failing** | Check build logs in Deployments tab |
| **ModuleNotFoundError** | Already fixed in code ✅ |
| **Can't access API** | Wait 3-5 more minutes (deployment in progress) |
| **Runtime error** | Check Environment variables are set correctly |
| **Database connection failed** | Verify DATABASE_URL is correct |
| **Qdrant not found** | Verify QDRANT_URL and QDRANT_API_KEY |

---

## Free Tier Limits

⚠️ **Important Notes:**
- Free tier spins down after 15 minutes of inactivity
- Next request takes 30-60 seconds to start (cold start)
- Upgrade to **Pro** ($7/month) for always-on service

---

## You're All Set!

Your RAG Chatbot Backend is ready to deploy to Render! 🚀

**Summary:**
1. ✅ Code is on GitHub
2. ✅ Service is configured on Render
3. ✅ Environment variables are added
4. ✅ Deployment is live
5. ✅ API is accessible

**Next Step:** Visit your API at `/docs` and start using it!

Questions? Check: **RENDER_DEPLOYMENT_GUIDE.md**
