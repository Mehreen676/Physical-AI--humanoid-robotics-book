# Deployment Quick Start

**For hackathon judges and quick setup**

## 5-Minute Setup

### 1. Get Backend URL

Deploy the FastAPI backend to one of these services:
- **Railway** (easiest): https://railway.app
- **Heroku**: https://heroku.com
- **Your own server**: Any URL accessible from HTTPS

Example deployed URL: `https://robotics-rag.up.railway.app`

### 2. Update Frontend Configuration

Edit `front-end/.env.production`:
```bash
REACT_APP_BACKEND_URL=https://robotics-rag.up.railway.app
```

### 3. Build and Deploy

```bash
cd front-end
npm install          # Install dependencies
npm run build        # Build production bundle
npm run deploy       # Deploy to GitHub Pages
```

**Done!** Your site is live at: `https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/`

---

## Verify It Works

1. Visit your GitHub Pages URL
2. Type a question in the chat widget
3. Check browser DevTools (F12) → Network tab
4. Verify `/chat` request succeeds (200 status)
5. Response should appear in chat

---

## If Backend Deployment Needed

### Railway (Recommended)

1. Go to https://railway.app
2. Connect GitHub repo
3. Set environment variables from `backend/.env`
4. Deploy
5. Copy service URL
6. Update `front-end/.env.production` with that URL
7. Rebuild and redeploy frontend

### Health Check Command

```bash
curl https://your-backend-url.com/health
```

Should return:
```json
{"status": "healthy", "message": "RAG Chat Service is running"}
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| "Failed to fetch" | Backend URL wrong or backend down |
| CORS error | Backend CORS needs your GitHub Pages URL |
| Chat widget not visible | TypeScript compile error, check `npm run build` |
| No response from backend | Backend `/health` endpoint should work |

---

## Environment Variables

### Frontend (.env.production)
```
REACT_APP_BACKEND_URL=<your-backend-url>
REACT_APP_API_TIMEOUT=15000
REACT_APP_DEBUG=false
REACT_APP_ENABLE_SELECTED_TEXT=true
REACT_APP_ENABLE_SYNTHESIS=true
```

### Backend (.env)
```
QDRANT_URL=<your-qdrant-url>
QDRANT_API_KEY=<your-api-key>
OPENAI_API_KEY=<your-key>
OPENROUTER_API_KEY=<your-key>
# ... and others from backend/.env
```

---

## Deploy Commands

```bash
# Frontend
cd front-end
npm install
npm run build
npm run deploy

# Backend (Railway)
- Connect GitHub → Railway
- Set env vars
- Deploy (automatic)
```

---

**For detailed guide, see: DEPLOYMENT_GUIDE.md**
