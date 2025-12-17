# WAVE 1: Backend Deployment - Complete Implementation Guide

**Phase 8 WAVE 1**: Backend Deployment to Production
**Duration**: 3-4 days | **Team**: DevOps + Backend Engineer

---

## Quick Start

```bash
# 1. Render.com Web Service
# Dashboard: New Web Service → Select repo → Configure

# 2. Environment Variables (Render Dashboard)
DATABASE_URL=postgresql://user:pass@neon.tech/rag_chatbot
QDRANT_URL=https://cluster.qdrant.io:6333
QDRANT_API_KEY=ey...
OPENAI_API_KEY=sk-proj-...
ENVIRONMENT=production
LOG_LEVEL=INFO

# 3. Deploy
git push origin main  # GitHub Actions auto-triggers

# 4. Verify
curl https://rag-chatbot-api.onrender.com/health
# {"status": "healthy"}
```

---

## Task 1.1: Render.com Account & GitHub Integration

```bash
# 1. Sign up: https://render.com (GitHub OAuth)
# 2. Dashboard → GitHub → Connect repository
# 3. Grant webhook permissions
# 4. Settings → Billing → Add payment method
# Time: 15 minutes
```

---

## Task 1.2: Create Web Service

```yaml
# Render Dashboard → New Web Service:
Name: rag-chatbot-api
Repository: Spec-Driven-Development-Hackathons-main
Branch: main
Root Directory: rag-backend
Runtime: Python 3.13
Build Command: pip install -r requirements.txt
Start Command: uvicorn src.main:app --host 0.0.0.0 --port 8080
Plan: Standard (auto-scale 2-4)
Region: Oregon
Health Check: /health (30s interval)
```

**Status**: Service URL assigned (e.g., rag-chatbot-api.onrender.com)

---

## Task 1.3: Environment Variables

```bash
# Render Dashboard → Settings → Environment

# Critical Variables
DATABASE_URL=postgresql://user:password@ep-xxxxx.neon.tech/rag_chatbot
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=ey...
OPENAI_API_KEY=sk-proj-...

# App Config
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS_STR=https://mehreen676.github.io

# Rate Limiting
RATE_LIMIT_QUERIES_PER_MINUTE=10
RATE_LIMIT_QUERIES_PER_DAY=1000

# Timeouts
QUERY_TIMEOUT_SECONDS=30
DATABASE_POOL_SIZE=20
SESSION_TIMEOUT_HOURS=24
```

**⚠️ Never commit secrets to git**

---

## Task 1.4: Health Checks

```bash
# Render Settings → Health Check:
Path: /health
Protocol: HTTP
Interval: 30 seconds
Timeout: 10 seconds
Grace Period: 60 seconds
Auto-restart: Enabled

# Test:
curl https://rag-chatbot-api.onrender.com/health
# Expected: {"status": "healthy"}
```

---

## Task 1.5: Neon PostgreSQL

```bash
# 1. https://neon.tech → Sign up
# 2. Create Project → Database: rag_chatbot
# 3. Copy connection string: postgresql://user:pass@host/db

# Test connection:
psql postgresql://user:pass@ep-xxxxx.neon.tech/rag_chatbot -c "SELECT 1"

# Configure:
# - Pooling: Transaction mode, max 20 connections
# - Backups: Daily, 30-day retention
# - PITR: Enabled (7 days)
```

**Time**: 30 minutes

---

## Task 1.6: Database Migrations

```bash
cd rag-backend
export DATABASE_URL="postgresql://..."

# Run migrations
alembic upgrade head

# Verify tables
psql $DATABASE_URL -c "\dt"
# Should show: chat_sessions, messages, documents, api_keys, users
```

**Status**: All tables created successfully

---

## Task 1.7: Qdrant Cloud

```bash
# 1. https://cloud.qdrant.io → Sign up
# 2. Create Cluster (Free tier 1GB)
# 3. Create Collection: rag_chatbot
#    - Vector size: 1536
#    - Distance: Cosine
#    - Index: HNSW

# Test:
curl -X GET "https://cluster.qdrant.io:6333/collections/rag_chatbot" \
  -H "api-key: YOUR_KEY"
```

**Time**: 20 minutes

---

## Task 1.8: OpenAI API

```bash
# 1. https://platform.openai.com/api-keys → Create secret key
# 2. Name: rag-chatbot-production
# 3. Billing → Set monthly limit: $50

# Test:
python -c "
import openai
openai.api_key = 'sk-proj-...'
response = openai.Embedding.create(
    input='test', model='text-embedding-3-small'
)
print('OK' if response['data'] else 'FAIL')
"
```

**Time**: 15 minutes

---

## Task 1.9: Test Deployment Pipeline

```bash
# 1. Push to main
git commit -m "Test deployment"
git push origin main

# 2. Monitor GitHub Actions
# Repository → Actions → ci-cd workflow
# Should complete: lint → test → build → deploy

# 3. Check Render Dashboard
# Service should transition to "Running"

# 4. Test API
curl -X POST https://rag-chatbot-api.onrender.com/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"query":"What is RAG?","session_id":"test"}'
```

**Time**: 30 minutes

---

## Task 1.10: Automated Backups

```bash
# Neon Dashboard → Backups:
# - Frequency: Daily at 2 AM UTC
# - Retention: 30 days
# - Point-in-time recovery: 7 days

# Test restore procedure:
# 1. Create test database
# 2. Verify connectivity
# 3. Document in runbook
```

**Time**: 20 minutes

---

## WAVE 1 Completion Checklist

```
✅ Render.com account created & GitHub connected
✅ Web service deployed (rag-chatbot-api)
✅ Service running (green status)
✅ Environment variables configured
✅ Health checks passing
✅ Neon PostgreSQL configured
✅ Database migrations applied
✅ Qdrant collection created
✅ OpenAI API configured
✅ Deployment pipeline working
✅ API endpoints responding
✅ Automated backups enabled
✅ Monitoring ready for WAVE 3

WAVE 1 STATUS: ✅ COMPLETE
```

---

## Troubleshooting

```bash
# Service won't start?
# → Check logs: Render Dashboard → Logs
# → Verify environment variables set
# → Test locally: uvicorn src.main:app

# Health check failing?
# → curl https://rag-chatbot-api.onrender.com/health
# → Wait 1-2 minutes for service startup
# → Check database connectivity

# Database connection error?
# → Verify connection string format
# → Check Neon password
# → Test locally: psql $DATABASE_URL -c "SELECT 1"
```

---

**WAVE 1 Complete!** → Next: **WAVE 2 - Frontend Deployment**

Generated: 2025-12-17 | Version: 1.0
