# Post-Deployment Checklist - RAG Backend on Render.com

## Immediately After Deployment (First 30 minutes)

### ✓ Service Running
- [ ] Render dashboard shows "Live" status
- [ ] No error messages in deployment logs
- [ ] Deployment timestamp is recent
- [ ] URL is: `https://rag-chatbot-backend.onrender.com`

### ✓ Basic Connectivity
```bash
# Run these commands
curl https://rag-chatbot-backend.onrender.com/health

# Expected: 200 OK with {"status": "healthy", ...}
```

- [ ] Health endpoint responds with 200 OK
- [ ] Response includes `"status": "healthy"`
- [ ] Response includes timestamp
- [ ] Response includes version

### ✓ API Documentation
```
https://rag-chatbot-backend.onrender.com/docs
```

- [ ] Opens Swagger UI
- [ ] Shows all endpoints
- [ ] Shows request/response schemas
- [ ] No 404 errors

### ✓ Endpoint Availability
```bash
# Check each endpoint
curl -X GET https://rag-chatbot-backend.onrender.com/health
curl -X GET https://rag-chatbot-backend.onrender.com/docs
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "mode": "full_book"}'
```

- [ ] `/health` returns 200
- [ ] `/docs` returns 200
- [ ] `/query` accepts POST requests
- [ ] `/ingest` accepts POST requests (may return 401 without auth)

### ✓ Environment Variables
- [ ] Render dashboard → Settings → Environment shows all vars
- [ ] No placeholders like `<YOUR_KEY>` visible
- [ ] All sensitive vars are masked (show as `***`)
- [ ] ENVIRONMENT is set to `production`
- [ ] DEBUG is set to `false`

### ✓ Logs Clean
1. Open Render dashboard → Logs tab
2. Scroll through recent logs
   - [ ] No ERROR level logs
   - [ ] No repeated warning patterns
   - [ ] No connection timeouts
   - [ ] No authentication failures
   - [ ] No database connection errors

---

## First Hour Checks

### ✓ Run Verification Script
```bash
# Linux/Mac
bash DEPLOY_VERIFICATION.sh https://rag-chatbot-backend.onrender.com

# Windows
DEPLOY_VERIFICATION.bat https://rag-chatbot-backend.onrender.com
```

- [ ] All 6 verification steps pass
- [ ] Health check OK
- [ ] API docs accessible
- [ ] Query endpoint working
- [ ] Ingest endpoint accessible
- [ ] Response time acceptable

### ✓ Test Query Endpoint
```bash
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is ROS 2?",
    "mode": "full_book"
  }'
```

- [ ] Returns 200 OK
- [ ] Contains "answer" field
- [ ] Contains "retrieved_chunks" field
- [ ] Contains "model" and "tokens" information
- [ ] Response time < 10 seconds

### ✓ Database Connectivity
- [ ] Query endpoint successfully retrieves data
- [ ] No "database connection failed" errors in logs
- [ ] Neon PostgreSQL dashboard shows active connection

### ✓ Vector Store Connectivity
- [ ] Query endpoint retrieves chunks from Qdrant
- [ ] Retrieved chunks have similarity scores
- [ ] No "Qdrant connection failed" errors in logs

### ✓ LLM Service Connectivity
- [ ] Query responses include generated text
- [ ] No "API key invalid" errors in logs
- [ ] Response time reasonable for LLM generation

---

## First Day Checks

### ✓ Monitor Performance Metrics
In Render dashboard → Metrics tab:
- [ ] CPU usage is low (<20%)
- [ ] Memory usage is reasonable (<200MB)
- [ ] Network I/O is normal
- [ ] No spike in restart count

### ✓ Monitor Costs
- [ ] Go to OpenAI dashboard → Billing
- [ ] Verify API key is active and working
- [ ] Check usage shows some tokens consumed
- [ ] Cost is within expected range (<$1 for first day)

### ✓ Monitor Database
- [ ] Go to Neon dashboard → Databases
- [ ] Verify database is active
- [ ] Check storage usage (<100MB)
- [ ] View active connections

### ✓ Monitor Vector Store
- [ ] Go to Qdrant Cloud dashboard
- [ ] Verify collection `aibook_chunk` exists
- [ ] Check vector count (should match data ingested)
- [ ] View API usage

### ✓ Review All Error Logs
1. Render dashboard → Logs tab
2. Filter for ERROR level
   - [ ] No critical errors
   - [ ] Any warnings are non-blocking
   - [ ] No repeated failure patterns

### ✓ Test Common Scenarios
```bash
# Test different query types
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"query": "ROS installation", "mode": "full_book"}'

curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How to use ROS?", "mode": "full_book"}'

# Test invalid requests
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{}'  # Missing required fields
```

- [ ] Valid queries return proper responses
- [ ] Invalid queries return 422 (validation error)
- [ ] Error messages are helpful
- [ ] No 500 errors for invalid input

---

## First Week Tasks

### ✓ Set Up Monitoring
- [ ] Set up UptimeRobot health check
- [ ] Configure email alerts
- [ ] (Optional) Set up Sentry error tracking
- [ ] (Optional) Set up Slack integration

### ✓ Document Production URLs
- [ ] Update frontend to use: `https://rag-chatbot-backend.onrender.com`
- [ ] Test frontend ↔ backend communication
- [ ] Verify CORS headers allow frontend origin
- [ ] Test end-to-end query flow

### ✓ Security Review
- [ ] Verify no credentials in logs
- [ ] Confirm .env not in git history
- [ ] Check all API keys are rotated
- [ ] Verify rate limiting is enabled
- [ ] Test authentication if implemented

### ✓ Performance Review
- [ ] Analyze response times over past week
- [ ] Check error rate (should be <1%)
- [ ] Review database query performance
- [ ] Monitor CPU/memory trends
- [ ] Identify any slow endpoints

### ✓ Cost Review
- [ ] Check OpenAI API usage and costs
- [ ] Verify costs are within budget
- [ ] Review Render instance type for needs
- [ ] Consider free LLM alternative optimization

### ✓ Documentation Updates
- [ ] Update README with production URLs
- [ ] Document API endpoints and usage
- [ ] Create runbook for common issues
- [ ] Document incident response procedures

---

## Weekly Tasks (Every Monday)

### ✓ Service Health
- [ ] Health check responds normally
- [ ] No unexpected downtime
- [ ] UptimeRobot shows 100% availability
- [ ] All critical logs review clean

### ✓ Performance Analysis
- [ ] Average response time stable
- [ ] Error rate remains <1%
- [ ] No new performance issues
- [ ] Database queries optimized

### ✓ Cost Monitoring
- [ ] OpenAI API costs as expected
- [ ] No unusual spikes
- [ ] Usage patterns normal
- [ ] Budget tracking on track

### ✓ Updates & Patches
- [ ] Python packages up to date
- [ ] Security patches applied if needed
- [ ] Dependencies reviewed
- [ ] Breaking changes checked

### ✓ Backups Verification
- [ ] Database backups running (Neon)
- [ ] Qdrant snapshots available
- [ ] Restore procedures documented
- [ ] Recovery time objective (RTO) acceptable

---

## Monthly Tasks (1st of month)

### ✓ Comprehensive Review
- [ ] Review entire month's performance
- [ ] Analyze trends and patterns
- [ ] Identify optimization opportunities
- [ ] Plan for next month

### ✓ Security Audit
- [ ] Review access logs
- [ ] Verify no unauthorized access attempts
- [ ] Check for suspicious patterns
- [ ] Update security documentation

### ✓ Cost Analysis
- [ ] Calculate total monthly cost
- [ ] Identify cost reduction opportunities
- [ ] Compare to budget
- [ ] Plan for scaling needs

### ✓ Capacity Planning
- [ ] Analyze usage trends
- [ ] Forecast growth
- [ ] Plan for scaling
- [ ] Update capacity management plan

### ✓ Incident Review
- [ ] Review any incidents from past month
- [ ] Document lessons learned
- [ ] Update runbooks
- [ ] Improve monitoring coverage

---

## Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| Service Down | Check Render dashboard status |
| Slow Response | Check database/Qdrant performance |
| High Errors | Review logs for specific error messages |
| High Costs | Check API usage dashboard |
| CORS Errors | Verify ALLOWED_ORIGINS_STR includes frontend |
| Auth Failures | Verify SECRET_KEY and credentials |
| Database Errors | Check Neon dashboard and DATABASE_URL |
| Vector Errors | Check Qdrant Cloud status |

---

## Support Contacts

- **Render Support**: https://dashboard.render.com/help
- **Neon Support**: https://neon.tech/docs/introduction/support
- **Qdrant Support**: https://qdrant.tech/documentation/
- **OpenAI Support**: https://help.openai.com/

---

## Next Review Date
- [ ] Set calendar reminder for 1 week review
- [ ] Set calendar reminder for 1 month review
- [ ] Set calendar reminder for quarterly review

---

## Sign-Off

- Deployment Date: _______________
- Deployed By: _______________
- Verified By: _______________
- Issues Found: _______________

**Status**: ✅ Production Ready
