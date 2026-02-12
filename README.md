---
title: Physical AI RAG Backend
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Physical AI & Humanoid Robotics Textbook — RAG Backend

Production-ready Agentic RAG (Retrieval-Augmented Generation) backend for the Physical AI & Humanoid Robotics interactive textbook.

This backend powers the embedded chat widget inside the Docusaurus book and answers questions grounded strictly in book content.

---

## 🚀 Features

- Agentic RAG architecture
- Qdrant vector search integration
- Gemini embeddings
- OpenAI response generation
- Selected-text constrained answering
- Multi-turn session support
- SQLite (local) + Neon Postgres (production)
- Production-ready FastAPI setup
- Hugging Face Docker deployment ready

---

## 🌐 Deployment (Hugging Face Spaces)

This repository is deployed as a **Docker Space**.

- Runtime Port: **7860**
- Health Endpoint: `/api/v1/health`
- Chat Endpoint: `/api/v1/chat`

After deployment succeeds, use your Space URL in frontend:

CHATBOT_BACKEND_URL=https://your-space-name.hf.space


---

## 📁 Project Structure



physical-ai-rag-backend/
├── main.py
├── config.py
├── requirements.txt
├── Dockerfile
├── api/
├── agent/
├── models/
├── storage/
├── utils/
└── retrieval/


---

## 🔑 Required Environment Variables (Set in Space Settings)

You must configure these in:

Hugging Face → Space → Settings → Variables

| Variable | Required |
|----------|----------|
| OPENAI_API_KEY | Yes |
| QDRANT_URL | Yes |
| QDRANT_API_KEY | Yes |
| GEMINI_API_KEY | Yes |
| DATABASE_URL | Optional |

⚠ Do NOT commit `.env` files.

---

## 🧪 Local Development

Install dependencies:

```bash
pip install -r requirements.txt


Run locally:

uvicorn main:app --host 0.0.0.0 --port 8000


Health check:

curl http://localhost:8000/api/v1/health


Chat test:

curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is ROS 2?","retrieval_mode":"normal"}'

📡 API Overview
Health
GET /api/v1/health

Create Session
POST /api/v1/sessions

Chat
POST /api/v1/chat


Body:

{
  "session_id": "optional",
  "question": "What is ROS 2?",
  "retrieval_mode": "normal",
  "selected_text": null
}

🔒 CORS Configuration

Ensure backend allows:

https://mehreen676.github.io


Update allowed origins in config.py if needed.

⚙ Docker Notes

Hugging Face requires:

App to bind on 0.0.0.0

Port 7860

Dockerfile already configured accordingly.

📚 License

MIT