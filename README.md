🚀 Physical AI & Humanoid Robotics Textbook — Agentic RAG Backend

Production-ready Agentic RAG (Retrieval-Augmented Generation) backend powering the interactive Physical AI & Humanoid Robotics textbook.

This backend drives the embedded AI chat widget inside the Docusaurus textbook and provides strictly grounded answers using vector retrieval from book content.

🧠 Architecture Overview

This backend implements a modern Agentic RAG pipeline:

User question received

Gemini Embedding (3072-dim)

Qdrant Cloud vector similarity search

Context grounding

OpenAI response generation

Structured API response to frontend

⚡ Core Features

✅ Agentic RAG architecture

✅ Qdrant Cloud vector database

✅ 3072-dimension Gemini embeddings

✅ OpenAI LLM answer generation

✅ Selected-text constrained answering

✅ Multi-turn session support

✅ SQLite (local) development

✅ Neon PostgreSQL (production ready)

✅ Dockerized deployment

✅ Hugging Face Spaces production deployment

🌐 Production Deployment
Hosted on:

Hugging Face Spaces (Docker runtime)

Runtime Configuration:

Port: 7860

Bind: 0.0.0.0

Health Endpoint: /api/v1/health

Chat Endpoint: /api/v1/chat

Frontend environment variable:

CHATBOT_BACKEND_URL=https://mehreenasghar5-physical-ai-rag-backend.hf.space

🗂 Project Structure
physical-ai-rag-backend/
│
├── main.py
├── config.py
├── requirements.txt
├── Dockerfile
│
├── api/
├── agent/
├── retrieval/
├── storage/
├── models/
└── utils/

🔐 Required Environment Variables

Configure inside:

Hugging Face → Space → Settings → Variables

Variable	Required
OPENAI_API_KEY	Yes
GEMINI_API_KEY	Yes
GEMINI_EMBEDDING_MODEL	Yes
QDRANT_URL	Yes
QDRANT_API_KEY	Yes
COLLECTION_NAME	Yes
DATABASE_URL	Optional
Current Production Setup

Embedding Model: models/gemini-embedding-001

Embedding Dimension: 3072

Active Collection: data_collection_3072_v3

⚠ Never commit .env files.

🧪 Local Development

Install dependencies:

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


Request Body:

{
  "session_id": "optional",
  "question": "What is ROS 2?",
  "retrieval_mode": "normal",
  "selected_text": null
}

🔎 Retrieval Modes
Mode	Description
normal	Full-book retrieval
selected_text	Constrained search within highlighted text
🛡 CORS Configuration

Allowed frontend origin:

https://mehreen676.github.io


Modify in config.py if deploying elsewhere.

🐳 Docker Configuration

Hugging Face Docker requirements:

App must bind to 0.0.0.0

Must run on port 7860

Dockerfile preconfigured accordingly

📊 Production Stack

FastAPI

Qdrant Cloud (Vector DB)

Gemini Embeddings (3072-dim)

OpenAI LLM

Neon PostgreSQL (optional)

Docker

Hugging Face Spaces

📜 License

MIT

🎯 Judge Notes

This backend demonstrates:

Modern Agentic RAG implementation

Cloud vector database integration

Production container deployment

Secure environment variable management

Multi-model AI integration

Scalable architecture for educational AI systems

Agar chaho to main tumhe:

🔥 “Judge Optimized” version bhi bana du

📊 Architecture diagram section add kar du

🧠 System flow diagram add kar du

🏆 Hackathon presentation ready version bana du

Bas bolo.
