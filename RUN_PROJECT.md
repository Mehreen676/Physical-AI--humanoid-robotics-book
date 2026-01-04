# 🚀 How to Run the Project (100% FREE)

## ✅ All FREE APIs Configured:

- ✅ **Gemini AI** (Agent) - FREE - `AIzaSyCTvAp39zQgXO7mFSQR92x5SGcN4ykqgh4`
- ✅ **Gemini Embeddings** - FREE - Same key
- ✅ **Qdrant** - FREE tier - Configured
- ✅ **SQLite Database** - FREE (local)

---

## 🖥️ Start Backend (Terminal 1)

### Option 1: Using Simple Script (Recommended)
```bash
python start_backend.py
```

### Option 2: Direct Python Module
```bash
python -m backend_v3.main
```

### Expected Output:
```
============================================================
Starting Agentic RAG Backend v3.0.0
============================================================
[OK] Retrieval layer initialized
[OK] Gemini agent initialized (model: gemini-1.5-flash)
[OK] SQLite database: chatbot.db
============================================================
[OK] Agentic RAG Backend ready
============================================================
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test Backend:
```bash
# New terminal
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status":"healthy","components":{"qdrant":true,"embeddings":true,"agent":true,"database":true},"version":"3.0.0"}
```

---

## 🌐 Start Frontend (Terminal 2)

```bash
cd front-end
npm start
```

### Expected Output:
```
Compiled successfully!

You can now view physical-ai-robotics-book in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

---

## 🧪 Test Chat Widget

1. **Open browser:** `http://localhost:3000`
2. **Look for chat button** in bottom-right corner (💬 icon)
3. **Click to open** chat panel
4. **Type a question:** "What is ROS 2?"
5. **Press Enter** or click Send
6. **See Gemini respond** with citations! 🎉

---

## 🔧 Troubleshooting

### CORS Error (Fixed ✅)
If you see CORS error, it's already fixed in `backend_v3/main.py`:
```python
allow_origins=["http://localhost:3000", "*"]
```

### Backend Won't Start
**Solution:** Use the startup script:
```bash
python start_backend.py
```

### Frontend Errors
**Solution:** Restart frontend server:
```bash
cd front-end
# Press Ctrl+C to stop
npm start
```

### "Module not found" Error
**Solution:** Install dependencies:
```bash
# Backend
cd backend_v3
pip install -r requirements.txt

# Frontend
cd front-end
npm install
```

---

## 📊 FREE API Usage Limits

All APIs have generous free tiers:

| API | Free Limit | Current Usage |
|-----|-----------|---------------|
| **Gemini AI** | 60 requests/min | ✅ Plenty for dev |
| **Gemini Embeddings** | 1500 requests/day | ✅ Enough |
| **Qdrant** | 1GB storage | ✅ More than enough |
| **SQLite** | Unlimited | ✅ Local file |

---

## 🎯 Quick Commands

### Start Everything:
```bash
# Terminal 1 - Backend
python start_backend.py

# Terminal 2 - Frontend
cd front-end && npm start
```

### Stop Everything:
```bash
# In each terminal: Ctrl+C
```

### Check Backend Status:
```bash
curl http://localhost:8000/api/v1/health
```

### Test Chat API:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is ROS 2?\", \"retrieval_mode\": \"normal\"}"
```

---

## ✅ Everything is FREE!

- 🟢 Backend: Google Gemini (FREE)
- 🟢 Database: SQLite (FREE)
- 🟢 Embeddings: Gemini (FREE)
- 🟢 Vector DB: Qdrant Free Tier (FREE)
- 🟢 Frontend: React/Docusaurus (FREE)

**Total Cost: $0.00** 🎉

---

## 📝 Summary

1. **Backend:** `python start_backend.py`
2. **Frontend:** `cd front-end && npm start`
3. **Test:** Open `http://localhost:3000` and use chat widget
4. **All FREE APIs configured!** ✅

Enjoy your **100% FREE** RAG chatbot! 🚀
