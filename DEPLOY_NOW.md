# QUICK DEPLOYMENT INSTRUCTIONS

## For: amehreen699

### 5-Minute Setup

---

## STEP 1: Create Space (2 minutes)

Go to: https://huggingface.co/spaces

**Create New Space:**
- Name: `rag-chatbot-backend`
- SDK: **Docker**
- Visibility: **Private**

✅ Click Create

---

## STEP 2: Add Secrets (2 minutes)

In your new Space → Settings → Repository Secrets

Add these 5 secrets:

| Name | Value | Example |
|------|-------|---------|
| `QDRANT_URL` | Your Qdrant URL | `https://xxx.qdrant.io` |
| `QDRANT_API_KEY` | Your API key | `ey...` |
| `DATABASE_URL` | Your DB URL | `postgresql://...` |
| `OPENAI_API_KEY` | Your OpenAI key | `sk-proj-...` |
| `SECRET_KEY` | Random string | `your-secret-key-123` |

✅ Click Save

---

## STEP 3: Deploy Code (1 minute)

Run these commands from your terminal:

```bash
cd /path/to/Hackathon_I

git remote add huggingface https://huggingface.co/spaces/amehreen699/rag-chatbot-backend.git

git subtree push --prefix rag-backend huggingface main
```

✅ Wait for "Done" message

---

## STEP 4: Wait for Build (5-10 minutes)

Go to your Space and click **App** tab

Watch the logs. You'll see:
```
INFO: Application startup complete
Running on http://0.0.0.0:8000
```

When you see this → **DEPLOYMENT COMPLETE** ✅

---

## STEP 5: Test It!

Visit your API:
```
https://amehreen699-rag-chatbot-backend.hf.space/docs
```

Try the `/query` endpoint from Swagger UI!

---

## URL Format

Replace `rag-chatbot-backend` with your space name if different:

```
https://amehreen699-rag-chatbot-backend.hf.space
```

---

## Troubleshooting

**Build failing?**
→ Check Settings → Repository Secrets (all 5 must be set)

**Can't access API?**
→ Wait 5 more minutes (cold start)

**ModuleNotFoundError?**
→ Already fixed! ✅

**Port error?**
→ Restart space from settings

---

## You're All Set!

Your RAG Chatbot Backend is ready to deploy! 🚀

All the code, Docker config, and fixes are ready. Just follow the 5 steps above.

Questions? Check: HUGGING_FACE_SPACES_DEPLOYMENT.md
