# Deployment Guide: RAG Chatbot Backend

This guide covers deploying the RAG Chatbot FastAPI backend to production.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Build & Run](#docker-build--run)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Migrations](#database-migrations)
6. [Health Checks & Monitoring](#health-checks--monitoring)
7. [Scaling & Performance Tuning](#scaling--performance-tuning)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)
10. [Disaster Recovery](#disaster-recovery)

---

## Local Development

### Prerequisites

- Python 3.13+
- PostgreSQL 15+
- Docker & Docker Compose (for containerized setup)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/rag-chatbot.git
   cd rag-chatbot/rag-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database URL
   ```

5. **Run locally**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access API**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health: http://localhost:8000/health

---

## Docker Build & Run

### Build Docker Image

```bash
cd rag-backend
docker build -t rag-chatbot-backend:latest .
```

### Run Container Locally

```bash
docker run -d \
  --name rag-chatbot-backend \
  -p 8000:8000 \
  --env-file .env \
  rag-chatbot-backend:latest
```

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f rag-backend

# Run tests
docker-compose exec rag-backend pytest tests/ -v

# Stop services
docker-compose down
```

### Docker Compose Environment Variables

Create `.env` file in project root:

```
OPENAI_API_KEY=sk-...
QDRANT_URL=https://...
QDRANT_API_KEY=...
DATABASE_URL=postgresql://user:password@postgres:5432/rag_chatbot
```

---

## Production Deployment

### Option 1: Render.com (Recommended for Free Tier)

1. **Create Render account** at https://render.com

2. **Create new Web Service**
   - Repository: Your GitHub repo
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn src.main:app --host 0.0.0.0 --port 8080`

3. **Set environment variables**
   - Go to Environment tab
   - Add all variables from `.env`

4. **Configure health check**
   - Health Check Path: `/health`
   - Health Check Interval: 30s

5. **Deploy**
   - Render automatically deploys on push to main

### Option 2: Railway.app

1. **Create Railway account** at https://railway.app

2. **Connect GitHub repository**

3. **Create PostgreSQL plugin** (or use Neon)

4. **Deploy**
   ```bash
   railway up
   ```

### Option 3: AWS/GCP (Enterprise)

1. **Push Docker image to ECR/GCR**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker tag rag-chatbot-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/rag-chatbot-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/rag-chatbot-backend:latest
   ```

2. **Deploy to ECS/GKE**
   - Configure task/pod definitions
   - Set up load balancer
   - Enable auto-scaling

---

## Environment Configuration

### Required Variables

```bash
# FastAPI
DEBUG=false                    # false in production
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# OpenAI
OPENAI_API_KEY=sk-...         # Required for generation
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4o
OPENAI_LLM_FALLBACK_MODEL=gpt-3.5-turbo

# Qdrant
QDRANT_URL=https://...        # Cloud URL
QDRANT_API_KEY=...            # API key

# Database
DATABASE_URL=postgresql://user:password@host:5432/db

# Logging
LOG_LEVEL=INFO                # INFO in production, DEBUG in development
```

### Optional Variables

```bash
# Rate Limiting
RATE_LIMIT_QUERIES_PER_MINUTE=10
RATE_LIMIT_QUERIES_PER_DAY_PER_IP=1000

# Session Management
SESSION_TIMEOUT_HOURS=24

# CORS
ALLOWED_ORIGINS_STR=https://book.example.com,https://api.example.com
```

---

## Database Migrations

### Using Alembic

1. **Initialize Alembic** (one-time setup)
   ```bash
   alembic init alembic
   ```

2. **Create migration**
   ```bash
   alembic revision --autogenerate -m "Add new column"
   ```

3. **Apply migration**
   ```bash
   alembic upgrade head
   ```

4. **Rollback migration**
   ```bash
   alembic downgrade -1
   ```

### Manual Schema Update

If using SQLAlchemy directly:

```python
from src.database import Base, engine

# Create all tables
Base.metadata.create_all(bind=engine)
```

---

## Health Checks & Monitoring

### Health Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy"}
```

### Monitoring Endpoints

Add to your monitoring system:

```
GET /health - Application health
POST /query - Query endpoint (logs latency)
GET /sessions/{session_id} - Session retrieval
```

### Structured Logging

All requests are logged with:
- Request ID for tracing
- Latency measurements
- Error details (sanitized)
- User/session ID (if available)

### Prometheus Metrics

Metrics exposed at `/metrics`:
- `http_requests_total` - Total requests
- `http_request_duration_seconds` - Request latency
- `embedding_generation_duration_seconds` - Embedding latency
- `query_errors_total` - Error count

---

## Scaling & Performance Tuning

### Horizontal Scaling

```bash
# Run multiple instances behind load balancer
docker-compose up -d --scale rag-backend=4
```

### Vertical Scaling

Increase resources per instance:
```bash
docker run -d \
  --cpus="2" \
  --memory="4g" \
  rag-chatbot-backend:latest
```

### Database Connection Pooling

Configure in `config.py`:
```python
# Pool size for connections
pool_size = 20
max_overflow = 40
pool_pre_ping = True  # Verify connections are alive
```

### Caching Optimization

- Redis layer (optional): Cache frequently asked questions
- Database row-level caching: Store query results
- TTL: 24 hours by default

---

## Troubleshooting

### Container won't start

1. Check logs: `docker logs rag-chatbot-backend`
2. Verify environment variables: `docker inspect rag-chatbot-backend`
3. Check port conflicts: `netstat -tulpn | grep 8000`

### Database connection errors

```bash
# Test connection
psql postgresql://user:password@host:5432/db

# Check connection string in logs
# Format: postgresql://[user[:password]@][netloc][:port][/dbname]
```

### API timeout errors

1. Check OpenAI API status
2. Verify Qdrant connectivity
3. Monitor database query performance
4. Increase timeout in config

### Memory leaks

```bash
# Monitor memory usage
docker stats rag-chatbot-backend

# Restart if memory usage > 80%
docker restart rag-chatbot-backend
```

---

## Rollback Procedures

### Rollback to Previous Version

```bash
# View deployment history
docker image ls | grep rag-chatbot

# Rollback to previous image
docker stop rag-chatbot-backend
docker run -d \
  --name rag-chatbot-backend \
  -p 8000:8000 \
  --env-file .env \
  rag-chatbot-backend:previous-tag
```

### Rollback Database Migrations

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade abc123def456
```

### Emergency Rollback (< 5 minutes)

1. Stop current container: `docker stop rag-chatbot-backend`
2. Start previous container: `docker start <previous-container-id>`
3. Verify health: `curl http://localhost:8000/health`
4. Notify team on Slack

---

## Disaster Recovery

### Data Backup

```bash
# Backup PostgreSQL database
pg_dump postgresql://user:password@host:5432/db > backup.sql

# Backup to AWS S3
pg_dump postgresql://user:password@host:5432/db | \
  aws s3 cp - s3://backup-bucket/rag-chatbot-$(date +%Y%m%d).sql

# Schedule daily backups
0 2 * * * pg_dump ... | aws s3 cp - s3://backup-bucket/daily/$(date +%Y%m%d).sql
```

### Data Restore

```bash
# Restore from backup
psql postgresql://user:password@host:5432/db < backup.sql

# Restore from S3
aws s3 cp s3://backup-bucket/rag-chatbot-20240101.sql - | \
  psql postgresql://user:password@host:5432/db
```

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective):** < 1 hour
2. **RPO (Recovery Point Objective):** < 1 day
3. **Backup Frequency:** Daily at 02:00 UTC
4. **Backup Location:** AWS S3 (separate region)
5. **Restore Test:** Weekly restore test

### Testing Recovery

```bash
# Monthly disaster recovery drill
# 1. Restore from backup to staging database
# 2. Run integration tests
# 3. Verify data integrity
# 4. Document time taken
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| Error Rate | > 1% | Page on-call engineer |
| Latency p95 | > 8s | Investigate bottleneck |
| CPU Usage | > 80% | Scale horizontally |
| Memory Usage | > 85% | Restart instance |
| Database Connections | > 90% of pool | Increase pool size |

### Setup Alerts

```bash
# Using Datadog
dd-agent -c /etc/dd-agent/datadog.conf
```

### Slack Integration

Notifications sent to #rag-chatbot-alerts on:
- Deployment success/failure
- Health check failures
- Error rate spikes
- Performance degradation

---

## Maintenance Windows

- **Backup Window:** 02:00-02:30 UTC daily
- **Deployment Window:** Friday 14:00 UTC
- **Database Maintenance:** Sunday 03:00 UTC

## Support

For issues or questions:
1. Check logs: `docker logs -f rag-chatbot-backend`
2. Review troubleshooting section above
3. Open issue on GitHub
4. Contact: support@example.com
