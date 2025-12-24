# .env Configuration Quick Reference

Copy these into your `.env.local` file. Get each credential from the links below.

---

## 1️⃣ NEON POSTGRES (Database)

**Get it from**: https://console.neon.tech

1. Sign in to Neon
2. Click your project
3. Go to "Connection strings"
4. Copy the **Pooled connection string**
5. Paste below

```bash
DATABASE_URL=postgresql://[user]:[password]@[host]/[dbname]?sslmode=require
```

**Example**:
```bash
DATABASE_URL=postgresql://neon_user:abc123xyz@ep-small-region.neon.tech/physical_ai_textbook?sslmode=require
```

⚠️ **Important**: Use **Pooled** connection string, not direct connection

---

## 2️⃣ QDRANT VECTOR DATABASE

### Option A: Qdrant Cloud (Recommended)

**Get it from**: https://cloud.qdrant.io

1. Sign in to Qdrant Cloud
2. Click your cluster
3. Copy **API Key** and **URL**
4. Paste below

```bash
QDRANT_URL=https://[cluster-id].region.aws.qdrant.io
QDRANT_API_KEY=your-api-key-here
```

**Example**:
```bash
QDRANT_URL=https://12345678-abcd-efgh.eu-west-1-0.aws.qdrant.io
QDRANT_API_KEY=aBcDeFgHiJkLmNoPqRsTuVwXyZ
```

### Option B: Local Qdrant (Docker)

```bash
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Leave empty for local
```

---

## 3️⃣ OPENAI API (GPT-4 & Embeddings)

**Get it from**: https://platform.openai.com/api-keys

1. Go to API Keys
2. Click "Create new secret key"
3. Copy immediately (won't show again)
4. Paste below

```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

**Example**:
```bash
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

⚠️ **Important**:
- Must have GPT-4 access enabled
- Must have embeddings API access

---

## 4️⃣ SENDGRID EMAIL SERVICE (Phase 1)

**Get it from**: https://sendgrid.com

1. Sign up (free tier: 100 emails/day)
2. Settings → API Keys
3. Create new API key
4. Copy the key
5. Paste below

```bash
SENDGRID_API_KEY=SG.your-key-here
SENDGRID_FROM_EMAIL=no-reply@yourdomain.com
```

**Example**:
```bash
SENDGRID_API_KEY=SG.abc123def456ghi789jkl_mnopqrstuvwxyz
SENDGRID_FROM_EMAIL=no-reply@textbook.example.com
```

⚠️ **Note**: Can use SendGrid's default domain or your own

---

## 5️⃣ JWT & AUTHENTICATION SECRETS

Generate these in terminal:

```bash
# Generate JWT_SECRET (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output → paste as JWT_SECRET

# Generate BETTER_AUTH_SECRET (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output → paste as BETTER_AUTH_SECRET
```

```bash
JWT_SECRET=your-random-secret-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=30

BETTER_AUTH_SECRET=another-random-secret-min-32-chars
```

**Example**:
```bash
JWT_SECRET=AbCdEfGhIjKlMnOpQrStUvWxYz1234567890_abc
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=30

BETTER_AUTH_SECRET=XyZ9876543210_zYxWvUtSrQpOnMlKjIhGfEdCbA
```

---

## 6️⃣ SERVER & ENVIRONMENT

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

FRONTEND_URL=http://localhost:3000
```

---

## Complete .env.local Template

Copy this entire block into your `.env.local`:

```bash
# ===== DATABASE =====
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# ===== QDRANT =====
QDRANT_URL=https://your-cluster.region.aws.qdrant.io
QDRANT_API_KEY=your-api-key

# ===== OPENAI =====
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# ===== SENDGRID =====
SENDGRID_API_KEY=SG.your-key-here
SENDGRID_FROM_EMAIL=no-reply@example.com

# ===== AUTHENTICATION =====
JWT_SECRET=generate-with-python-secrets
JWT_ALGORITHM=HS256
JWT_EXPIRY_DAYS=30

BETTER_AUTH_SECRET=generate-with-python-secrets

# ===== SERVER =====
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# ===== FRONTEND =====
FRONTEND_URL=http://localhost:3000

# ===== OPTIONAL =====
# SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

---

## Credential Checklist

Print this and check off as you get each credential:

```
NEON POSTGRES
- [ ] Go to https://console.neon.tech
- [ ] Sign in
- [ ] Copy pooled connection string
- [ ] Paste into DATABASE_URL

QDRANT
- [ ] Go to https://cloud.qdrant.io (or use Docker local)
- [ ] Copy cluster URL
- [ ] Copy API key
- [ ] Paste QDRANT_URL and QDRANT_API_KEY

OPENAI API
- [ ] Go to https://platform.openai.com/api-keys
- [ ] Create new secret key
- [ ] Copy immediately (won't show again!)
- [ ] Paste into OPENAI_API_KEY

SENDGRID (Optional for Phase 0)
- [ ] Go to https://sendgrid.com
- [ ] Create API key
- [ ] Paste into SENDGRID_API_KEY

JWT SECRETS
- [ ] Generate JWT_SECRET (run python command)
- [ ] Generate BETTER_AUTH_SECRET (run python command)

SERVER CONFIG
- [ ] Set ENVIRONMENT=development
- [ ] Set DEBUG=true
- [ ] Set FRONTEND_URL=http://localhost:3000
```

---

## Validation Commands

After filling .env.local, test each credential:

### Test Postgres
```bash
cd backend
python -c "
from app.core.database import engine
try:
    with engine.connect() as conn:
        conn.execute('SELECT 1')
        print('✓ Postgres OK')
except Exception as e:
    print(f'✗ Postgres error: {e}')
"
```

### Test Qdrant
```bash
python -c "
from qdrant_client import QdrantClient
from app.core.config import settings
try:
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )
    client.get_collections()
    print('✓ Qdrant OK')
except Exception as e:
    print(f'✗ Qdrant error: {e}')
"
```

### Test OpenAI
```bash
python -c "
from openai import OpenAI
from app.core.config import settings
try:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    client.models.list()
    print('✓ OpenAI OK')
except Exception as e:
    print(f'✗ OpenAI error: {e}')
"
```

### Test All at Once
```bash
# Run backend health check
uvicorn app.main:app --reload
# Then in another terminal:
curl http://localhost:8000/api/health
# Should return: {"status": "healthy", "postgres": "ok", "qdrant": "ok"}
```

---

## Order of Operations

1. **Create .env.local** (copy from .env.example)
2. **Get Neon Postgres** → Fill DATABASE_URL
3. **Get Qdrant** → Fill QDRANT_URL + QDRANT_API_KEY
4. **Get OpenAI key** → Fill OPENAI_API_KEY
5. **Generate secrets** → Fill JWT_SECRET + BETTER_AUTH_SECRET
6. **Fill server config** → ENVIRONMENT, DEBUG, etc.
7. **Validate all** → Run test commands
8. **Start backend** → `uvicorn app.main:app --reload`
9. **Start frontend** → `npm run start`

---

## Common Mistakes to Avoid

❌ **Don't**:
- Use direct connection string instead of pooled (Neon)
- Leave JWT_SECRET as placeholder
- Commit .env.local to Git
- Share API keys in messages/screenshots
- Use development secrets in production

✅ **Do**:
- Use pooled connection string
- Generate random secrets
- Keep .env.local local only
- Rotate keys regularly
- Use different secrets per environment

---

## If Something Goes Wrong

| Error | Solution |
|-------|----------|
| `could not connect to server` | Check DATABASE_URL format |
| `SSL error` | Add `?sslmode=require` to DATABASE_URL |
| `Invalid API key` | Re-copy from Neon/Qdrant/OpenAI |
| `connection refused` | Check host/port correct |
| `403 Unauthorized` | API key may be expired/invalid |
| `rate limit` | OpenAI quota exhausted (check billing) |

---

## Quick Links

- Neon Console: https://console.neon.tech
- Qdrant Cloud: https://cloud.qdrant.io
- OpenAI API Keys: https://platform.openai.com/api-keys
- SendGrid: https://sendgrid.com
- FastAPI Docs: http://localhost:8000/api/docs (after setup)

---

## Next Steps After .env.local

1. ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. ```bash
   # Initialize database
   python -c "from app.core.database import init_db; init_db()"
   ```

3. ```bash
   # Start server
   uvicorn app.main:app --reload
   ```

4. Visit http://localhost:8000/api/docs to test endpoints

---

**Estimated time to complete**: ~20 minutes

**Need help?** Check PHASE-0-SETUP-GUIDE.md for detailed steps
