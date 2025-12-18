# Production Monitoring Setup for RAG Backend

## Overview

This guide covers monitoring your RAG backend after deployment to Render.com.

---

## 1. Render.com Built-in Monitoring

### Health Checks
Render automatically monitors your service. Monitor the dashboard:

1. Go to https://dashboard.render.com
2. Select your service: `rag-chatbot-backend`
3. View:
   - **Deployments** tab - Deployment history
   - **Logs** tab - Real-time logs
   - **Metrics** tab - CPU, memory, network usage
   - **Events** tab - Service events

### Check Service Status
```bash
# Health endpoint (200 = OK)
curl https://rag-chatbot-backend.onrender.com/health

# Response should show:
{
  "status": "healthy",
  "timestamp": "2025-12-18T...",
  "version": "1.0.0",
  "environment": "production"
}
```

---

## 2. Log Monitoring

### View Real-time Logs
1. Render Dashboard → Logs tab
2. Filter by level:
   - **INFO** - Normal operation
   - **WARNING** - Potential issues
   - **ERROR** - Problems
   - **CRITICAL** - Service down

### Important Log Patterns to Watch
```
ERROR - Database connection failed     → Check DATABASE_URL
ERROR - Qdrant connection timeout      → Check QDRANT_URL
ERROR - Invalid API key                → Check credentials
ERROR - Rate limit exceeded            → Monitor usage
WARNING - Slow query response          → Check performance
```

---

## 3. Error Tracking with Sentry (Optional)

### Setup Sentry
1. Go to https://sentry.io → Sign up
2. Create new project: Select "FastAPI"
3. Copy DSN (looks like: `https://xxx@yyy.ingest.sentry.io/zzz`)
4. Add to Render environment variables:
   ```
   SENTRY_DSN=<your-dsn>
   SENTRY_ENVIRONMENT=production
   ```

### In Backend Code (already configured)
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
    integrations=[FastApiIntegration()]
)
```

### Monitor Errors
- Go to https://sentry.io/organizations/your-org/issues/
- View all errors by time, frequency, stack trace
- Get notifications for critical errors
- Track error trends

---

## 4. Performance Monitoring

### Key Metrics to Track

#### A. Response Time
```bash
# Measure response time
time curl https://rag-chatbot-backend.onrender.com/health

# Acceptable ranges:
# - Health check: <200ms
# - Query endpoint: <5000ms
# - Cold start: 30-60s (free tier)
```

#### B. Throughput
Monitor successful queries per minute:
```bash
# In logs, count successful responses
# Pattern: "Query endpoint returned 200"
```

#### C. Error Rate
Monitor failed requests:
```bash
# Pattern: "Query endpoint failed with 500"
# Target: <1% error rate
```

#### D. Database Performance
Monitor database queries:
```bash
# Check logs for slow queries
# Pattern: "Database query took XXXms"
```

---

## 5. Cost Monitoring

### OpenAI API Costs
1. Go to https://platform.openai.com/account/billing/overview
2. Set up usage alerts:
   - Hard limit: $10/month (to prevent surprise bills)
   - Email alert at 80% usage
3. Monitor tokens used:
   - Embedding: ~1000-5000/day (cheapest)
   - Generation: Free (using Groq)

### Render Costs
1. Go to https://dashboard.render.com/account/billing
2. View current month usage
3. Upgrade plan if needed (after free tier spin-downs)

### Database Costs
1. Go to https://neon.tech/app/projects
2. Check storage usage
3. Monitor connection count

### Total Monthly Cost
```
Render:    $0 (free tier)
OpenAI:    $2-5 (embeddings only)
Neon DB:   $0 (free tier)
Qdrant:    $0 (free tier)
─────────────────────
Total:     $2-5 USD
```

---

## 6. Uptime Monitoring

### UptimeRobot (Free)
1. Go to https://uptimerobot.com → Sign up
2. Create new monitor:
   - Type: HTTP(s)
   - URL: https://rag-chatbot-backend.onrender.com/health
   - Check interval: Every 5 minutes
   - Alert emails: Your email

### What It Monitors
- Service availability
- Response time
- SSL certificate status
- Downtime alerts

### Expected Uptime
- Render free tier: 99.9% (accepts brief spin-downs)
- Production tier: 99.99%

---

## 7. Alert Configuration

### Set Up Alerts

#### Email Alerts (Render)
1. Dashboard → Settings → Alerts
2. Enable email notifications for:
   - Deployment failures
   - Service crashes
   - High CPU/memory usage

#### Slack Integration (Optional)
1. Create Slack webhook: https://api.slack.com/messaging/webhooks
2. Add to monitoring tools
3. Get real-time alerts in Slack channel

#### Email Alerts (UptimeRobot)
- Configure in UptimeRobot dashboard
- Get alerted if service goes down

---

## 8. Daily Monitoring Checklist

### Daily (Every Morning)
```
☐ Check health endpoint: curl .../health
☐ Review Render logs for errors
☐ Check UptimeRobot status
☐ Verify no spike in error rate
☐ Monitor response times
```

### Weekly (Every Friday)
```
☐ Review past week's logs
☐ Check OpenAI API usage costs
☐ Monitor database storage
☐ Verify Qdrant vector count
☐ Check rate limiting stats
```

### Monthly (1st of month)
```
☐ Review total costs
☐ Analyze performance trends
☐ Check for slow queries
☐ Review security logs
☐ Plan optimizations
☐ Update documentation
```

---

## 9. Common Issues & Solutions

### Issue: Service Slow (>3s response time)
**Causes**:
- Cold start (free tier) - Normal, accept 30-60s
- High database load - Check query performance
- Qdrant timeout - Check vector store
- LLM API slow - Check OpenAI/Groq status

**Solutions**:
1. Check logs for specific error
2. Monitor database performance
3. Upgrade instance type if needed
4. Use caching for frequent queries

### Issue: High Error Rate (>5%)
**Causes**:
- Invalid credentials - Verify env vars
- Database down - Check Neon status
- Rate limiting hit - Check usage
- Code bug - Review recent changes

**Solutions**:
1. Check Render logs for specific errors
2. Verify all credentials are valid
3. Check external service status
4. Roll back if recent deployment

### Issue: High Costs
**Causes**:
- Excessive API calls - Check query volume
- Large batch requests - Monitor ingestion
- Inefficient embeddings - Check chunking

**Solutions**:
1. Review query patterns
2. Optimize chunking strategy
3. Implement caching
4. Use free tier models where possible

### Issue: Database Connection Failed
**Causes**:
- Invalid DATABASE_URL - Typo in env var
- Neon database down - Check Neon status
- Connection limit exceeded - Too many queries
- Network issue - Firewall/IP blocking

**Solutions**:
1. Verify DATABASE_URL format
2. Check Neon dashboard status
3. Review connection pool settings
4. Contact Neon support if needed

---

## 10. Post-Deployment Monitoring Dashboard

### What to Monitor (Priority Order)

| Metric | Target | Check Frequency | Alert if |
|--------|--------|-----------------|----------|
| Health Check | 200 OK | Every 5 min | Fails for 15 min |
| Error Rate | <1% | Hourly | >5% for 1 hour |
| Response Time | <1s | Hourly | >5s average |
| Uptime | 99.9% | Daily | <95% monthly |
| Cost | $5/month | Daily | >$20/month |
| Database Size | <1GB | Weekly | >10GB |
| Vector Count | >1000 | Weekly | Decreasing |

---

## 11. Production Runbook

### If Service is Down
1. Check Render dashboard status
2. View real-time logs for errors
3. Check external services (OpenAI, Neon, Qdrant)
4. Manually trigger redeployment if needed
5. Contact Render support if persists

### If Response is Slow
1. Check Render metrics (CPU, memory)
2. Review recent database queries
3. Check OpenAI/Groq API status
4. Look for spike in error rate
5. Consider upgrading instance

### If Getting Rate Limited
1. Check rate limiting configuration
2. Review query patterns
3. Implement caching if possible
4. Distribute queries across time
5. Upgrade if persistent

---

## 12. Optimization Tips

### Reduce Costs
- Use Groq (free) instead of OpenAI for generation
- Implement query result caching
- Batch embedding requests
- Monitor and optimize database queries

### Improve Performance
- Add query result caching (Redis)
- Optimize vector search parameters
- Use database connection pooling
- Compress response payloads

### Increase Reliability
- Implement circuit breakers for external APIs
- Add retry logic with exponential backoff
- Set up automated failover
- Regular backup verification

---

## Resources

- **Render Docs**: https://render.com/docs
- **Sentry Docs**: https://docs.sentry.io
- **UptimeRobot**: https://uptimerobot.com
- **FastAPI Monitoring**: https://fastapi.tiangolo.com/deployment/concepts/monitoring/

---

## Next Steps

1. ✓ Deploy to Render
2. ✓ Set up Render log monitoring
3. Set up UptimeRobot for health checks
4. (Optional) Set up Sentry for error tracking
5. (Optional) Set up Slack alerts
6. Create monitoring schedule
7. Document incident response procedures

---

**Your backend is production-ready and monitored!** 🚀
