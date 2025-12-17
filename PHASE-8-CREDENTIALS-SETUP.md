# Phase 8: Credentials & Secrets Setup Guide

**Purpose**: Gather and configure all credentials needed for production deployment
**Status**: Ready for execution
**Duration**: 2-3 hours

---

## ⚠️ Security Rules

**CRITICAL RULES**:
1. ❌ NEVER commit `.env` file with real credentials
2. ❌ NEVER share credentials in messages, emails, or chat
3. ❌ NEVER hardcode secrets in code
4. ✅ ALWAYS use environment variables (Render.com dashboard)
5. ✅ ALWAYS rotate credentials if accidentally exposed
6. ✅ ALWAYS use `.env.example` as template only

**If Credentials Are Exposed**:
- Immediately revoke the key in the service dashboard
- Generate a new key
- Update all deployment environments
- Document the incident

---

## 1️⃣ Neon PostgreSQL Setup

### Step 1: Create Neon Account
- Go to https://neon.tech
- Sign up (free tier available)
- Create new project: `rag-chatbot`

### Step 2: Create Database
```bash
# In Neon console:
1. Project → Create database
   Name: rag_chatbot

2. Branches → main
   → Connection string (copy full URL)
```

### Step 3: Get Connection String
```
Format: postgresql://user:password@host/database?sslmode=require

Example:
postgresql://neondb_owner:secret123@ep-xxxxx.us-east-1.aws.neon.tech/rag_chatbot?sslmode=require
```

**Save as**: `DATABASE_URL` environment variable

### Step 4: Verify Connection
```bash
# Test locally (replace with your actual URL):
psql "postgresql://user:password@host/rag_chatbot?sslmode=require" -c "SELECT 1;"
```

---

## 2️⃣ Qdrant Cloud Setup

### Step 1: Create Qdrant Account
- Go to https://cloud.qdrant.io
- Sign up (free tier: 1 cluster, 1GB storage)
- Create new cluster: `rag-chatbot`

### Step 2: Cluster Configuration
```
Cluster Size: Free (1GB storage)
Region: us-east-1 (closest to your deployment)
```

### Step 3: Get Credentials
```bash
# In Qdrant console:
1. Cluster → API Keys
   Generate new key

2. Copy API key (JWT token format)

3. Cluster URL: https://your-cluster-id.qdrant.io:6333
```

**Save as**:
- `QDRANT_URL`: `https://your-cluster-id.qdrant.io:6333`
- `QDRANT_API_KEY`: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### Step 4: Verify Connection
```bash
# Test API connectivity:
curl -H "api-key: $QDRANT_API_KEY" \
  https://$QDRANT_CLUSTER_ID.qdrant.io:6333/health

# Expected response: {"status":"ok"}
```

---

## 3️⃣ OpenAI API Setup

### Step 1: Create OpenAI Account
- Go to https://platform.openai.com
- Sign up or log in
- Create paid plan (free trial credits expire)

### Step 2: Set Billing
```bash
# CRITICAL: Set spending limits
1. Account → Billing → Overview
2. Set monthly budget: $50 (recommended)
3. Enable email alerts
4. Set usage limits to prevent overages
```

### Step 3: Generate API Key
```bash
# In OpenAI console:
1. Account → API keys
2. Create new API key
3. Copy key: sk-proj-...
4. Save securely (cannot be retrieved later)
```

**Save as**: `OPENAI_API_KEY`

### Step 4: Verify API Key
```bash
# Test embeddings API:
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer sk-proj-..." \
  -H "Content-Type: application/json" \
  -d '{"input":"test","model":"text-embedding-3-small"}'

# Expected: 200 OK with embedding vector
```

### Step 5: Enable Required Models
- ✅ `text-embedding-3-small` (embeddings)
- ✅ `gpt-4o` (primary LLM)
- ✅ `gpt-3.5-turbo` (fallback LLM)

All should be enabled by default on paid plan.

---

## 4️⃣ GitHub Repository Access

### Step 1: Verify GitHub Access
```bash
# Current repository:
Spec-Driven-Development-Hackathons-main
```

### Step 2: Check Permissions
```bash
# Required permissions:
- [x] Push to main branch
- [x] Create releases
- [x] GitHub Actions enabled
- [x] Workflow files executable
```

### Step 3: Generate Personal Access Token (if needed)
```bash
# For Render.com GitHub integration:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Create new token
3. Scopes: repo, read:user, workflow
4. Save token: ghp_...
```

---

## 5️⃣ Render.com Setup

### Step 1: Create Account
- Go to https://render.com
- Sign up with GitHub OAuth (recommended)
- Authorize access to your repositories

### Step 2: Connect GitHub
```bash
# In Render dashboard:
1. Settings → Integrations
2. Connect GitHub repository
3. Grant access to Spec-Driven-Development-Hackathons-main
```

### Step 3: Get API Key (optional, for automation)
```bash
# In Render dashboard:
1. Account → API tokens
2. Create new token
3. Save: rnd_...
```

---

## 6️⃣ PagerDuty Setup (Optional - for WAVE 3)

### Step 1: Create Account
- Go to https://pagerduty.com
- Sign up (free tier available)

### Step 2: Create Service
```bash
# In PagerDuty console:
1. Services → Create new service
   Name: RAG Chatbot Backend
   Escalation Policy: Default (you)

2. Copy Integration Key
   Format: xxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Add to Environment
**Save as**: `PAGERDUTY_INTEGRATION_KEY`

---

## 7️⃣ Production Environment Variables

### Summary Table

| Variable | Source | Example | Required |
|----------|--------|---------|----------|
| `DATABASE_URL` | Neon | `postgresql://...` | ✅ |
| `QDRANT_URL` | Qdrant | `https://...qdrant.io:6333` | ✅ |
| `QDRANT_API_KEY` | Qdrant | `eyJ...` | ✅ |
| `OPENAI_API_KEY` | OpenAI | `sk-proj-...` | ✅ |
| `ENVIRONMENT` | Config | `production` | ✅ |
| `DEBUG` | Config | `False` | ✅ |
| `SECRET_KEY` | Generated | (random string) | ✅ |
| `ALLOWED_ORIGINS_STR` | Config | `https://mehreen676.github.io,...` | ✅ |
| `SENTRY_DSN` | Sentry | `https://...ingest.sentry.io/...` | ❌ |
| `PAGERDUTY_KEY` | PagerDuty | `...` | ❌ |

---

## 8️⃣ Render.com Environment Configuration

### Step 1: Create Web Service
- Follow WAVE-1-DEPLOYMENT-GUIDE.md Step 1.2

### Step 2: Add Environment Variables
```bash
# In Render dashboard → Web Service → Settings → Environment

# Database
DATABASE_URL=postgresql://...

# Vector Store
QDRANT_URL=https://...qdrant.io:6333
QDRANT_API_KEY=eyJ...

# LLM
OPENAI_API_KEY=sk-proj-...

# Configuration
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# Security
ALLOWED_ORIGINS_STR=https://mehreen676.github.io,https://rag-chatbot-api.onrender.com

# Rate Limiting
RATE_LIMIT_QUERIES_PER_MINUTE=10
RATE_LIMIT_QUERIES_PER_DAY=1000

# Optional: Error Tracking
SENTRY_DSN=https://...ingest.sentry.io/...
```

### Step 3: Verify in Dashboard
- All variables should show as set (value hidden)
- No red warning icons
- Service should restart automatically

---

## 9️⃣ Development vs Production Config

### Development (Local `.env`)
```bash
ENVIRONMENT=development
DEBUG=True
ALLOWED_ORIGINS_STR=http://localhost:3000,http://localhost:8000
DATABASE_URL=postgresql://localhost/rag_chatbot  # local test DB
```

### Production (Render.com Environment)
```bash
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS_STR=https://mehreen676.github.io,https://rag-chatbot-api.onrender.com
DATABASE_URL=postgresql://neondb_owner:...@ep-xxxxx.neon.tech/rag_chatbot
```

---

## 🔟 Verification Checklist

Before proceeding to WAVE 1 deployment:

```
✅ Neon PostgreSQL
   □ Account created
   □ Database created
   □ Connection string obtained
   □ Connection tested locally

✅ Qdrant Cloud
   □ Account created
   □ Cluster created
   □ API key generated
   □ Connection tested

✅ OpenAI API
   □ Paid plan activated
   □ Monthly budget set to $50
   □ API key generated
   □ Spending limits configured
   □ Required models enabled

✅ GitHub
   □ Repository access verified
   □ Push permissions confirmed
   □ GitHub Actions enabled

✅ Render.com
   □ Account created
   □ GitHub connected
   □ Ready for web service creation

✅ All Credentials
   □ Stored securely (not shared)
   □ Ready to input into Render.com
   □ .env file not committed
   □ Backup credentials saved in password manager
```

---

## 🔐 Credential Rotation (Emergency)

If credentials are accidentally exposed:

### Neon PostgreSQL
```bash
1. Go to Neon Dashboard
2. Project → Branches → main
3. Reset password (creates new password)
4. Update DATABASE_URL in Render.com
5. Service auto-restarts
```

### Qdrant Cloud
```bash
1. Go to Qdrant Dashboard
2. API Keys → Delete exposed key
3. Generate new key
4. Update QDRANT_API_KEY in Render.com
```

### OpenAI API
```bash
1. Go to https://platform.openai.com/account/api-keys
2. Delete exposed key
3. Create new key
4. Update OPENAI_API_KEY in Render.com
```

### Render.com
```bash
1. Dashboard → Web Service → Settings → Environment
2. Find compromised variable
3. Update with new value
4. Service auto-restarts
```

---

## Next Steps

Once all credentials are gathered:
1. ✅ Follow PRODUCTION_DEPLOYMENT_CHECKLIST.md
2. ✅ Execute WAVE-1-DEPLOYMENT-GUIDE.md
3. ✅ Input credentials into Render.com environment
4. ✅ Verify health checks passing

---

**Status**: 🟢 Ready for Phase 8 WAVE 1 Execution
