# Production Operations Manual - RAG Backend

## Table of Contents
1. Daily Operations
2. Incident Response
3. Performance Optimization
4. Backup & Disaster Recovery
5. Scaling Procedures
6. Maintenance Tasks
7. Cost Optimization
8. Security Operations

---

## 1. Daily Operations

### Morning Checklist (5 minutes)

```bash
# 1. Check service status
curl https://rag-chatbot-backend.onrender.com/health

# 2. Review overnight logs
# Go to Render dashboard → Logs tab
# Look for ERROR level messages

# 3. Check uptime
# Go to UptimeRobot dashboard
# Verify 100% uptime overnight

# 4. Monitor costs
# Go to OpenAI dashboard → Usage
# Verify costs are within daily budget
```

### Afternoon Check (2 minutes)

```bash
# Quick health check
curl -s https://rag-chatbot-backend.onrender.com/health | jq '.status'

# Should return: "healthy"
```

### Evening Review (10 minutes)

```bash
# Full diagnostic
1. Render dashboard → Metrics tab
   - Check CPU usage (should be <20%)
   - Check memory usage (should be <200MB)
   - Check network I/O (normal levels)

2. Database health
   - Go to Neon dashboard
   - Verify active connections
   - Check query performance

3. Vector store health
   - Go to Qdrant dashboard
   - Verify collection accessible
   - Check vector count

4. API performance
   - Check average response time
   - Review error rate
   - Look for slow queries
```

---

## 2. Incident Response

### Service Down (Status Red)

**Response Time: < 5 minutes**

```bash
# Step 1: Verify the issue
curl -v https://rag-chatbot-backend.onrender.com/health
# If no response or timeout → service is down

# Step 2: Check status pages
- Render status: https://status.render.com
- Neon status: https://status.neon.tech
- Qdrant status: https://status.qdrant.io
- OpenAI status: https://status.openai.com

# Step 3: Check Render logs
Render Dashboard → Logs → Look for crash/error

# Step 4: If external service is down
- Wait for recovery (typically 5-30 minutes)
- Update status page with message
- Notify users if needed

# Step 5: If our service crashed
- Render auto-restarts, check if recovered
- If not, manual redeploy needed
```

**If Manual Redeployment Needed:**
```bash
# Render Dashboard → Deployments → Click latest
# Click "Redeploy" button
# Monitor deployment logs
# Test health endpoint after deployment
```

### High Error Rate (>5% of requests)

**Response Time: < 10 minutes**

```bash
# Step 1: Identify the error type
Render Dashboard → Logs → Filter by ERROR level
# Common patterns:
# - "Database connection failed"
# - "Invalid API key"
# - "Rate limit exceeded"
# - "Timeout"

# Step 2: For database errors
Go to Neon dashboard → Check database status
Verify DATABASE_URL in Render env vars
Check connection pool settings

# Step 3: For API key errors
Verify credentials in Render environment
Check API service status pages
Consider credential rotation

# Step 4: For rate limiting
Check usage patterns
Monitor request frequency
Consider spreading load over time

# Step 5: Monitor recovery
Watch error rate decrease
Verify queries are succeeding again
```

### Slow Responses (Response time > 5s)

**Response Time: < 15 minutes investigation**

```bash
# Step 1: Measure current performance
time curl https://rag-chatbot-backend.onrender.com/query \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query":"test","mode":"full_book"}'

# Step 2: Check resource usage
Render Dashboard → Metrics
- Is CPU usage high (>50%)?
- Is memory usage high (>300MB)?
- Is network I/O high?

# Step 3: Check database performance
Neon Dashboard → Insights
- Query performance
- Slow queries
- Connection count

# Step 4: Check vector store performance
Qdrant Dashboard → Metrics
- Query latency
- Search time
- Vector count

# Step 5: Optimize if needed
- Consider adding caching
- Optimize vector search parameters
- Check for N+1 queries
- Monitor external API response times
```

### Cost Spike (Unexpected High Bills)

**Response Time: < 1 hour**

```bash
# Step 1: Identify source
OpenAI Dashboard → Usage
- What's using tokens?
- Is it embeddings or generation?
- Unusual spike pattern?

# Step 2: Analyze queries
Render Logs → Search for high token usage
Identify which queries are expensive

# Step 3: Take action
- Implement caching for repeated queries
- Batch embeddings requests
- Use Groq (free) instead of OpenAI for generation
- Consider rate limiting to reduce queries

# Step 4: Set budget alerts
OpenAI → Billing → Set hard limit
Configure email alerts at 50%, 80%, 100%
```

### Database Connection Issues

**Response Time: < 10 minutes**

```bash
# Step 1: Verify connection string
Render Environment Variables → DATABASE_URL
Format: postgresql://user:password@host/database

# Step 2: Check database status
Neon Dashboard → Your project
Verify database is "Available"

# Step 3: Test connection
Try connecting from local machine:
psql postgresql://user:password@host/database

# Step 4: Check connection limits
Neon free tier: 100 connections
If exceeded, reduce connection pool size

# Step 5: Monitor recovery
Watch error logs decrease
Verify queries completing successfully
```

---

## 3. Performance Optimization

### Response Time Optimization

```bash
# Current baseline
Test endpoint response times:
curl -w "Total: %{time_total}s\n" https://rag-chatbot-backend.onrender.com/query

# Target: < 1 second for health, < 5 seconds for queries

# Optimization strategies:
1. Implement Redis caching
   - Cache frequently asked questions
   - Cache vector search results
   - Cache generated responses

2. Optimize vector search
   - Adjust similarity threshold
   - Reduce number of vectors returned
   - Use approximation algorithms

3. Batch requests
   - Combine embeddings requests
   - Batch multiple queries
   - Use connection pooling

4. Database optimization
   - Add indexes on frequently queried columns
   - Monitor slow query logs
   - Archive old data

5. External API optimization
   - Use faster LLM (Groq instead of OpenAI)
   - Implement fallback chains
   - Cache LLM responses for common queries
```

### Memory Usage Optimization

```bash
# Current usage
Render Dashboard → Metrics → Memory

# Target: < 200MB

# Optimization strategies:
1. Reduce model size
   - Use smaller embedding models
   - Compress stored vectors
   - Archive large datasets

2. Memory pooling
   - Connection pooling (SQL connections)
   - Vector store client pooling
   - API client reuse

3. Stream responses
   - Return results in chunks
   - Don't load entire datasets into memory
   - Use generators instead of lists

4. Cleanup
   - Remove old sessions
   - Clear expired tokens
   - Archive old logs
```

### CPU Usage Optimization

```bash
# Current usage
Render Dashboard → Metrics → CPU

# Target: < 20% average

# Optimization strategies:
1. Async operations
   - Ensure all I/O is async
   - Avoid blocking operations
   - Use connection pooling

2. Background tasks
   - Move heavy processing to background
   - Use job queue for batch processing
   - Schedule optimization tasks off-peak

3. Query optimization
   - Add database indexes
   - Rewrite slow queries
   - Cache expensive operations

4. Load distribution
   - Spread requests across time
   - Implement request queuing
   - Scale horizontally if needed
```

---

## 4. Backup & Disaster Recovery

### Database Backups

```bash
# Neon provides automatic backups
# 7-day retention on free tier
# 30-day on paid tier

# Test restore procedure monthly:
1. Go to Neon Dashboard
2. Select your project
3. Look for "Backups" tab
4. Create test restore point
5. Verify data integrity

# Manual backup (if needed):
pg_dump postgresql://user:pass@host/db > backup.sql

# Restore from manual backup:
psql postgresql://user:pass@host/db < backup.sql
```

### Vector Store Snapshots

```bash
# Qdrant provides snapshots
# Configure automated snapshots:
1. Go to Qdrant Cloud Dashboard
2. Select your cluster
3. Enable scheduled snapshots
4. Set retention policy

# Manual snapshot:
curl -X POST https://your-cluster.qdrant.io:6333/snapshots

# Test restore monthly:
1. Create snapshot
2. Verify it's stored
3. Document process
4. Update disaster recovery plan
```

### Disaster Recovery Plan

```
SCENARIO: Complete data loss

Recovery steps:
1. Identify which data was lost (database, vectors, or both)
2. If database lost:
   - Restore from Neon backup
   - Verify data integrity
   - Monitor for consistency

3. If vectors lost:
   - Restore from Qdrant snapshot
   - Or re-embed from database content
   - Rebuild vector collection

4. If both lost:
   - Restore from Neon backup
   - Re-embed all content
   - Verify system functionality

Recovery time target (RTO): < 2 hours
Recovery point target (RPO): < 1 hour

Regular testing:
- Monthly: Test database restore
- Monthly: Test vector restore
- Quarterly: Full system recovery drill
```

---

## 5. Scaling Procedures

### When to Scale

```
Signs you need to scale:
- Error rate increasing (>2%)
- Response times increasing (>3s average)
- CPU usage consistently >70%
- Memory usage consistently >300MB
- Rate limiting triggered frequently
- Costs increasing dramatically
```

### Vertical Scaling (Upgrade Instance)

```bash
# Render.com scaling:
1. Dashboard → Your service
2. Click Settings
3. Click "Plan" dropdown
4. Select higher tier
5. Review new cost
6. Confirm upgrade

# No downtime - seamless upgrade
# Cost increase but better performance

Tiers:
- Free: $0, ~5 concurrent connections
- Starter: $7/month, ~25 connections
- Pro: $25/month, ~100 connections
- Business: $115/month, unlimited
```

### Horizontal Scaling (Multiple Instances)

```bash
# For high availability:
1. Deploy multiple instances of backend
2. Use load balancer (Render handles this)
3. Configure auto-scaling rules
4. Set min/max replica count

# For database:
- Neon: Upgrade to paid tier for read replicas
- Enable connection pooling

# For vector store:
- Qdrant: Upgrade to larger plan
- Enable sharding for large datasets
```

### Database Scaling

```bash
# Neon PostgreSQL scaling:
1. Monitor storage usage
2. When approaching limit, upgrade plan
3. Archive old data to separate storage
4. Enable read replicas for scaling reads

# Connection pool sizing:
- Render (1 instance): 20 connections
- Render (3 instances): 60 connections
- Rule: 20 connections per instance

# Query optimization before scaling:
- Add missing indexes
- Optimize slow queries
- Consider materialized views
```

### Vector Store Scaling

```bash
# Qdrant Cloud scaling:
1. Monitor vector count and storage
2. When approaching limit, upgrade
3. Sharding strategy for large datasets
4. Consider partitioning by collection

# Performance optimization before scaling:
- Reduce vector dimensions if possible
- Use appropriate similarity metric
- Optimize search parameters
- Archive old vectors
```

---

## 6. Maintenance Tasks

### Weekly Maintenance

```
Every Monday morning:

□ Review past week performance
  - Error rate trends
  - Response time trends
  - Cost trends

□ Security audit
  - Review access logs
  - Check for suspicious patterns
  - Verify no unauthorized access

□ Database maintenance
  - Check index health
  - Review query performance
  - Archive old data

□ Backup verification
  - Verify automatic backups exist
  - Test one backup restore
  - Document any issues

□ Update documentation
  - Record performance metrics
  - Update runbooks with new procedures
  - Document lessons learned
```

### Monthly Maintenance

```
First day of each month:

□ Comprehensive performance review
  - Analyze full month data
  - Identify trends
  - Plan optimizations

□ Cost analysis
  - Review all service costs
  - Compare to budget
  - Identify optimization opportunities

□ Security audit
  - Review all logs
  - Check for anomalies
  - Update security policies

□ Capacity planning
  - Forecast growth
  - Plan scaling
  - Update budgets

□ Update all credentials
  - Rotate API keys (optional but recommended)
  - Review access permissions
  - Update password policies

□ Disaster recovery test
  - Restore from backup
  - Verify all systems work
  - Document any issues

□ Team training
  - Update runbooks
  - Train team on new procedures
  - Review incident responses
```

### Quarterly Maintenance

```
Every 3 months:

□ Major security audit
  - Full penetration test (if budgeted)
  - Code review for security issues
  - Dependency vulnerability scan
  - Access control audit

□ Performance optimization review
  - Analyze bottlenecks
  - Implement improvements
  - Measure impact

□ Disaster recovery drill
  - Full system failure simulation
  - Time the recovery
  - Document lessons learned
  - Update procedures

□ Architecture review
  - Evaluate current design
  - Identify technical debt
  - Plan improvements
  - Update documentation

□ Budget review
  - Analyze spending
  - Forecast future costs
  - Adjust budgets
  - Plan cost optimizations
```

---

## 7. Cost Optimization

### Monthly Cost Reduction

```bash
# Target: Keep costs below $10/month

Strategy 1: Use free LLM services
- OpenAI only for embeddings ($2-3/month)
- Groq for generation (free)
- Cohere for fallback (free tier)
- Result: Save ~$15/month

Strategy 2: Implement caching
- Cache frequent queries
- Cache embedding results
- Cache LLM responses
- Result: Reduce API calls by 30-50%

Strategy 3: Batch requests
- Combine embedding requests
- Group vector searches
- Batch database queries
- Result: Reduce API calls by 20-30%

Strategy 4: Optimize queries
- Add database indexes
- Remove N+1 queries
- Optimize vector search
- Result: Reduce latency and resource usage

Strategy 5: Archive old data
- Move old messages to archive
- Delete old sessions
- Compress logs
- Result: Reduce storage and query time

Estimated savings: $5-10/month
```

### Free Tier Optimization

```bash
# Maximize free tier benefits:

Render.com:
- Use free tier with 750 hrs/month
- Service spins down after 15 min inactivity
- Upgrade only if always-on needed

Neon PostgreSQL:
- 3GB free storage
- Monitor usage monthly
- Archive data to reduce storage

Qdrant Cloud:
- 5GB free vector storage
- Archive old vectors
- Optimize vector size

OpenAI:
- Only use for embeddings (cheapest)
- Use free LLM (Groq) for generation
- Implement caching to reduce calls

Total cost on free tiers: $2-5/month
```

---

## 8. Security Operations

### Daily Security Tasks

```bash
# Check for unauthorized access
Render Logs → Look for 401/403 errors

# Monitor rate limiting
Check for unusual request patterns

# Verify SSL certificate
Check certificate expiration date
```

### Weekly Security Review

```bash
# Access logs audit
Review who accessed the system

# API key usage audit
Check which keys are being used
Verify no leaked keys in logs

# Database audit
Review database access logs
Check for unusual queries

# Update security patches
Check for dependency updates
Apply critical security patches
```

### Monthly Security Audit

```bash
# Full security review:
□ Access control audit
  - Verify proper role assignments
  - Remove unused users
  - Review admin access

□ Credential audit
  - Check API key rotation schedule
  - Verify secrets not in logs
  - Review .env security

□ Encryption audit
  - Verify HTTPS everywhere
  - Check API key encryption
  - Review data encryption

□ Backup security
  - Verify backups are encrypted
  - Test restore with encryption
  - Document backup access

□ Compliance check
  - Review data handling policies
  - Verify GDPR compliance
  - Check data retention policies

□ Incident review
  - Review security incidents from past month
  - Update incident response procedures
  - Train team on lessons learned
```

### Credential Rotation Schedule

```
Recommended rotation:
- API keys: Every 90 days (or if compromised)
- Database password: Every 90 days
- JWT secret: Annually or if compromise suspected
- OAuth secrets: As per provider recommendations

Process:
1. Generate new credential
2. Update in all environments
3. Test thoroughly
4. Document rotation
5. Schedule old credential deletion
6. Verify no usage of old credential
```

---

## Emergency Contacts

**Service Providers:**
- Render Support: https://dashboard.render.com/help
- Neon Support: https://neon.tech/docs/introduction/support
- Qdrant Support: https://qdrant.tech/documentation/
- OpenAI Support: https://help.openai.com/

**Monitoring Tools:**
- UptimeRobot Support: https://uptimerobot.com/contact
- Sentry Support: https://sentry.io/support/

---

## Runbook Templates

### Service Down Runbook
```
Time detected: _________
Root cause: _________
Actions taken: _________
Time resolved: _________
Post-mortem: _________
Preventive measures: _________
```

### Performance Issue Runbook
```
Issue description: _________
Symptoms: _________
Diagnosis: _________
Actions taken: _________
Effectiveness: _________
Long-term solution: _________
```

### Cost Spike Runbook
```
Cost detected: $_________
Compared to: $_________
Likely cause: _________
Investigation results: _________
Actions taken: _________
Expected savings: $_________
```

---

## Success Metrics

Track these metrics daily:

```
✓ Uptime: Target 99.9%
✓ Error Rate: Target <1%
✓ Response Time: Target <1s
✓ Cost: Target <$10/month
✓ CPU Usage: Target <20%
✓ Memory Usage: Target <200MB
✓ Database Connections: Target <30
✓ Active Users: Monitor trends
✓ Query Success Rate: Target >99%
✓ Cache Hit Rate: Target >50%
```

---

**Last Updated:** 2025-12-18
**Version:** 1.0 - Production Ready
