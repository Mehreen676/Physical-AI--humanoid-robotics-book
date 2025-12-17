# Phase 8 Deployment Simulation - Complete Walkthrough

**Purpose**: Show exactly what happens during production deployment
**Status**: Ready for real team execution with actual credentials
**Credentials Required**: See checklist below

---

## Prerequisites Checklist

Before you can deploy, gather these credentials:

```
REQUIRED CREDENTIALS:
☐ Render.com Account
  - URL: https://render.com
  - Create account with GitHub OAuth
  - Get API key for automation

☐ Neon PostgreSQL
  - URL: https://neon.tech
  - Create account
  - Get database connection string
  - Format: postgresql://user:pass@host/db

☐ Qdrant Cloud
  - URL: https://cloud.qdrant.io
  - Create account
  - Get cluster URL: https://cluster-id.qdrant.io:6333
  - Get API key

☐ OpenAI API
  - URL: https://platform.openai.com/api-keys
  - Create secret key
  - Format: sk-proj-...

☐ GitHub Repository
  - Ensure you have push access to main branch
  - Verify GitHub Actions enabled

☐ Domain (Optional)
  - For custom domain (e.g., rag-chatbot.example.com)
  - DNS configured

☐ PagerDuty Account (for WAVE 3)
  - URL: https://pagerduty.com
  - Create service
  - Get integration key

☐ Grafana/Prometheus (for WAVE 3)
  - Server with Docker installed, or cloud hosting
```

---

## WAVE 1 Deployment Simulation - Backend to Render.com

### Step 1.1: Create Render.com Web Service

```bash
# Login to https://render.com dashboard

# Click "New +" → "Web Service"

# Configuration to enter:
Service Name:           rag-chatbot-api
Repository:             Spec-Driven-Development-Hackathons-main
Branch:                 main
Root Directory:         rag-backend
Runtime:                Python 3.13
Build Command:          pip install -r requirements.txt
Start Command:          uvicorn src.main:app --host 0.0.0.0 --port 8080
Plan:                   Standard (auto-scales 2-4)
Region:                 Oregon (us-west)
Health Check Path:      /health
Health Check Interval:  30 seconds

# Click "Create Web Service"

# ✅ EXPECTED OUTPUT:
# [SUCCESS] Service created
# Service ID: srv-xxxxx
# Service URL: https://rag-chatbot-api.onrender.com
# Status: Building (this takes 5-10 minutes)
```

### Step 1.2: Set Environment Variables

```bash
# In Render Dashboard → Settings → Environment

# Add each variable:

# Database
DATABASE_URL=postgresql://user:password@ep-xxxxx.neon.tech/rag_chatbot

# Vector Store
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=ey...

# LLM API
OPENAI_API_KEY=sk-proj-...

# App Config
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Security
SECRET_KEY=your-generated-secret-key-here
ALLOWED_ORIGINS_STR=https://mehreen676.github.io

# Rate Limiting
RATE_LIMIT_QUERIES_PER_MINUTE=10
RATE_LIMIT_QUERIES_PER_DAY=1000

# Timeouts
QUERY_TIMEOUT_SECONDS=30
DATABASE_POOL_SIZE=20
SESSION_TIMEOUT_HOURS=24

# Click "Save" after each

# ✅ EXPECTED OUTPUT:
# Environment variables saved successfully
# Service will restart with new config
```

### Step 1.3: Verify Service Health

```bash
# Wait for build to complete (5-10 minutes)
# Then test:

curl https://rag-chatbot-api.onrender.com/health -v

# ✅ EXPECTED OUTPUT (HTTP 200):
# {
#   "status": "healthy",
#   "timestamp": "2025-12-17T...",
#   "version": "1.0.0"
# }

# ✅ In Render Dashboard, status should show "RUNNING" (green)
```

### Step 1.4: Test API Endpoints

```bash
# Test health check
curl https://rag-chatbot-api.onrender.com/health

# Test query endpoint (requires API key)
curl -X POST https://rag-chatbot-api.onrender.com/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: default-key" \
  -d '{
    "query": "What is RAG?",
    "session_id": "test-123"
  }' -v

# ✅ EXPECTED OUTPUT:
# HTTP 200
# {
#   "answer": "RAG stands for Retrieval-Augmented Generation...",
#   "sources": [...],
#   "latency_ms": 5800
# }

# Check metrics
curl https://rag-chatbot-api.onrender.com/metrics

# ✅ EXPECTED OUTPUT:
# Prometheus format metrics showing queries, latency, errors
```

---

## WAVE 2 Deployment Simulation - Frontend to GitHub Pages

### Step 2.1: Enable GitHub Pages

```bash
# Go to Repository Settings → Pages

# Configuration:
Source:                 GitHub Actions
Branch:                 gh-pages (will be auto-created)
Enforce HTTPS:          Enabled

# Click "Save"

# ✅ EXPECTED OUTPUT:
# Your site is live at: https://mehreen676.github.io/rag-chatbot
```

### Step 2.2: Update Frontend Config

```bash
# Edit: docusaurus_textbook/src/components/RagChatbot/config.js

# Change API_URL to production:
export const API_URL = 'https://rag-chatbot-api.onrender.com'

# Commit and push:
git add docusaurus_textbook/src/components/RagChatbot/config.js
git commit -m "Update: Production API endpoint"
git push origin main

# ✅ EXPECTED OUTPUT:
# GitHub Actions triggers deploy workflow
# Build starts automatically
# Wait 2-3 minutes
```

### Step 2.3: Verify Frontend

```bash
# Test frontend deployment
curl https://mehreen676.github.io/rag-chatbot -I

# ✅ EXPECTED OUTPUT (HTTP 200):
# HTTP/2 200
# Content-Type: text/html
# Cache-Control: public

# Visit in browser: https://mehreen676.github.io/rag-chatbot
# ✅ EXPECTED: Site loads, chat widget visible
```

---

## WAVE 3 Deployment Simulation - Monitoring Infrastructure

### Step 3.1: Start Prometheus

```bash
# Create prometheus.yml configuration (see templates below)
# Then run:

docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  --name prometheus \
  prom/prometheus

# ✅ EXPECTED OUTPUT:
# Container ID: abc123...
# Access at: http://localhost:9090

# Test metrics collection:
curl http://localhost:9090/api/v1/targets

# ✅ EXPECTED OUTPUT:
# {
#   "status": "success",
#   "data": {
#     "activeTargets": [{
#       "labels": {"job": "rag-backend"},
#       "lastScrapeTime": "...",
#       "health": "up"
#     }]
#   }
# }
```

### Step 3.2: Start Grafana

```bash
docker run -d -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  --name grafana \
  grafana/grafana

# ✅ EXPECTED OUTPUT:
# Container ID: def456...
# Access at: http://localhost:3000 (admin/admin)

# Add Prometheus datasource:
# Dashboard → Configuration → Data Sources → Add
# URL: http://prometheus:9090
# Click "Save & Test"

# ✅ EXPECTED OUTPUT:
# "Data source is working"
```

### Step 3.3: Configure Alerts

```bash
# Create alertmanager.yml
# Start AlertManager:

docker run -d -p 9093:9093 \
  -v $(pwd)/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  --name alertmanager \
  prom/alertmanager

# ✅ EXPECTED OUTPUT:
# Container ID: ghi789...
# Access at: http://localhost:9093
```

---

## WAVE 4 Deployment Simulation - Operations Readiness

### Step 4.1: Test Runbooks

```bash
# Simulate high error rate scenario:

# 1. Generate test errors:
for i in {1..100}; do
  curl -X POST https://rag-chatbot-api.onrender.com/query \
    -H "Content-Type: application/json" \
    -d '{"query":"test","invalid_field":"x"}' &
done

# 2. Check dashboards:
# Grafana → Error Rate panel should spike
# PagerDuty should trigger alert

# 3. Follow runbook procedure:
# - Check error logs
# - Identify issue
# - Implement fix
# - Rollback if needed

# ✅ EXPECTED: Error rate returns to <1%
```

### Step 4.2: Test Rollback

```bash
# Simulate a bad deployment:

# 1. Make a bad commit (intentionally)
git commit -m "test: intentional breaking change"
git push origin main

# 2. Watch deployment fail:
# - GitHub Actions fails tests
# - Deployment stops (doesn't reach production)

# 3. Fix the issue:
git revert HEAD
git push origin main

# 4. Verify rollback:
curl https://rag-chatbot-api.onrender.com/health

# ✅ EXPECTED: Returns to healthy state
```

### Step 4.3: Team Training

```bash
# Run incident simulation drill:

# 1. Page on-call engineer (simulated)
# 2. Investigate mock incident
# 3. Execute runbook procedure
# 4. Resolve simulated issue
# 5. Document in post-incident review

# ✅ EXPECTED: All team members understand procedures
```

---

## Configuration Templates

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'rag-chatbot'

scrape_configs:
  - job_name: 'rag-backend'
    scheme: 'https'
    static_configs:
      - targets: ['rag-chatbot-api.onrender.com:443']
    metrics_path: '/metrics'

rule_files:
  - 'alert_rules.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

### alert_rules.yml

```yaml
groups:
  - name: rag_chatbot_alerts
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(rag_query_errors_total[5m]) > 0.01
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rag_query_duration_seconds) > 8
        for: 5m
        annotations:
          summary: "High latency p95"

      - alert: ServiceDown
        expr: up{job="rag-backend"} == 0
        for: 1m
        annotations:
          summary: "RAG backend service is down"
```

### alertmanager.yml

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'pagerduty'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

### docker-compose.yml (for local monitoring)

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

  alertmanager:
    image: prom/alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
```

---

## Deployment Timeline

### Pre-Deployment (Day -1)
- [ ] Gather all credentials
- [ ] Read all WAVE guides
- [ ] Team briefing
- [ ] Backup data
- [ ] Notify stakeholders

### Launch Day

```
T-0:30  Final systems check
        ✓ All services running
        ✓ Credentials verified
        ✓ Tests passing

T-0:15  Team standby
        ✓ All team members ready
        ✓ Communication channels active
        ✓ Runbooks reviewed

T+0:00  DEPLOY
        ✓ Push to main branch
        ✓ GitHub Actions triggered
        ✓ Docker build starts
        ✓ Render deployment begins

T+0:10  Build complete
        ✓ Docker image pushed
        ✓ Render pulls image
        ✓ Service starting

T+0:15  Service running
        ✓ Health checks passing
        ✓ APIs responding
        ✓ Databases connected

T+0:30  Smoke tests
        ✓ Query endpoint works
        ✓ Session management works
        ✓ Databases persisting
        ✓ No errors in logs

T+1:00  All clear
        ✓ Performance normal
        ✓ Error rate <1%
        ✓ Latency p95 <6s
        ✓ Ready for normal traffic
```

### Post-Deployment (Days 1-7)

```
Day 1: Continuous monitoring
       - Check dashboards hourly
       - Monitor error logs
       - Respond to any alerts
       - Document any issues

Day 2-3: Performance validation
        - Verify all SLOs met
        - Check cost tracking
        - Review user feedback
        - Optimize if needed

Day 4-7: Stabilization
        - Daily monitoring
        - Weekly review meeting
        - Performance tuning
        - Documentation updates
```

---

## Success Criteria

### ✅ WAVE 1 Success
- [ ] Backend service running on Render.com
- [ ] Health checks passing
- [ ] All environment variables set
- [ ] Databases connected
- [ ] APIs responding
- [ ] Tests passing
- [ ] Monitoring metrics flowing

### ✅ WAVE 2 Success
- [ ] Frontend deployed to GitHub Pages
- [ ] Site loads without errors
- [ ] Chat widget visible and functional
- [ ] Frontend-backend integration working
- [ ] Performance <3s load time
- [ ] Both locales (en/ur) working

### ✅ WAVE 3 Success
- [ ] Prometheus collecting metrics
- [ ] Grafana dashboards showing live data
- [ ] ELK logging ingesting data
- [ ] Sentry capturing errors
- [ ] PagerDuty routing alerts
- [ ] All dashboards accessible

### ✅ WAVE 4 Success
- [ ] Operations team trained
- [ ] Runbooks documented and tested
- [ ] Incident response drill completed
- [ ] Security audit passed
- [ ] Backup/restore tested
- [ ] Go-live approval signed

---

## Troubleshooting Quick Reference

### Service won't start
```
→ Check Render logs
→ Verify environment variables
→ Test locally: uvicorn src.main:app
→ Check database connectivity
```

### Health check failing
```
→ Wait 1-2 minutes for startup
→ Check if database connected
→ Verify all required APIs accessible
→ Check service logs
```

### Database connection error
```
→ Verify connection string format
→ Check Neon password
→ Test locally: psql $DATABASE_URL -c "SELECT 1"
→ Check IP whitelisting
```

### Monitoring not collecting data
```
→ Verify Prometheus config
→ Check target health (http://localhost:9090/targets)
→ Verify metrics endpoint: /metrics
→ Check network connectivity
```

---

## Final Go/No-Go Decision

```
DEPLOYMENT APPROVED?

☐ YES - All checks passed, ready to go live
☐ NO  - Requires fixes: ____________________

Approved by:
- DevOps Lead: _________________ Date: _____
- Engineering Lead: _________________ Date: _____
- Product Manager: _________________ Date: _____
```

---

**This simulation document shows exactly what happens during actual deployment.**

**To execute with real credentials:**
1. Gather credentials from checklist
2. Follow PRODUCTION_DEPLOYMENT_CHECKLIST.md
3. Execute WAVE 1-4 guides
4. Go live! 🚀

Generated: 2025-12-17
