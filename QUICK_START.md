# 🚀 Quick Start Guide - CORS Fixed!

## ✅ CORS Issue Fixed!

Main issue: `allow_credentials=True` with `allow_origins=["*"]` conflict tha.
**Solution:** `allow_credentials=False` set kiya.

---

## 🎯 Start Karo (2 Steps):

### Step 1: Backend Start (Terminal 1)

```bash
python start_backend.py
```

**Expected Output:**
```
============================================================
Starting Agentic RAG Backend v3.0.0
============================================================
[OK] Retrieval layer initialized
[OK] Gemini agent initialized (model: gemini-1.5-flash)
[OK] Agentic RAG Backend ready
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status":"healthy","components":{"qdrant":true,"embeddings":true,"agent":true,"database":true},"version":"3.0.0"}
```

---

### Step 2: Frontend Start (Terminal 2)

```bash
cd front-end
npm start
```

**Browser automatically open hoga:** `http://localhost:3000`

---

## 🧪 Test Chat Widget:

1. **Click chat button** (bottom-right corner, 💬 icon)
2. **Type question:** "What is ROS 2?"
3. **Press Enter**
4. **See response** with citations! ✨

---

## 🔧 Agar Error Aaye:

### 1. "Unable to connect to chatbot"
**Solution:**
- Backend running hai? Check: `curl http://localhost:8000/api/v1/health`
- Agar nahi: `python start_backend.py`

### 2. CORS Error (Console mein)
**Solution:**
- Backend restart karo (CORS fix ho gaya hai)
- Frontend restart karo: Ctrl+C then `npm start`

### 3. Backend Start Nahi Ho Raha
**Solution:**
```bash
# Dependencies install karo
cd backend_v3
pip install -r requirements.txt

# Phir start karo
cd ..
python start_backend.py
```

### 4. Frontend Compile Error
**Solution:**
```bash
cd front-end
npm install
npm start
```

---

## ✅ What's Fixed:

1. ✅ **CORS Configuration** - Now works with all origins
2. ✅ **OPTIONS Handler** - Preflight requests handled
3. ✅ **Free APIs** - All Gemini (no paid services)
4. ✅ **Simple Startup** - One command: `python start_backend.py`

---

## 📊 Current Setup:

```
Frontend (localhost:3000)
    ↓
    Sends request to
    ↓
Backend (localhost:8000)
    ↓
    Uses FREE APIs:
    ├─ Gemini AI (Agent) ✅ FREE
    ├─ Gemini Embeddings ✅ FREE
    ├─ Qdrant (Vector DB) ✅ FREE
    └─ SQLite (Database) ✅ FREE
```

---

## 🎉 Ready!

**2 Commands. That's it!**

```bash
# Terminal 1
python start_backend.py

# Terminal 2
cd front-end && npm start
```

**Everything is FREE! No cost! 🎉**
