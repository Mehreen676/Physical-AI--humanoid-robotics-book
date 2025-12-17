# WAVE 4: Operations & Compliance - Production Readiness

**Phase 8 WAVE 4**: Operations & Compliance
**Duration**: 2-3 days | **Team**: DevOps + Engineering Lead + Security

---

## Quick Start

```bash
# 1. Create runbooks
# → Emergency response playbook
# → Database recovery procedure
# → Scaling procedures

# 2. Train operations team
# → Dashboard walkthrough
# → Alert response procedure
# → Incident handling

# 3. Security audit
# → OWASP Top 10 scan
# → Dependency check
# → Secret scanning

# 4. Incident response drill
# → Test alert routing
# → Practice escalation
# → Document procedures
```

---

## Task 4.1: Emergency Response Runbook

### High Error Rate (>1%)

```bash
SYMPTOMS:
- Error rate alert triggered in PagerDuty
- Sentry shows error spike

IMMEDIATE (0-5 min):
1. Check Grafana dashboard for error trend
2. Review latest error logs in Kibana
3. Check Sentry error groups
4. Determine error pattern (new vs existing)

INVESTIGATION (5-15 min):
1. Check recent deployments
2. Review database connection status
3. Check external API status (OpenAI, Qdrant)
4. Review application logs for stack traces

RESOLUTION:
IF recent deployment:
  → git revert HEAD && git push origin main
  → Render auto-redeploys previous version

IF database issue:
  → Check connection pool status
  → Increase pool size if needed
  → Restart service if connections stuck

IF external API down:
  → Implement failover
  → Notify customers of degraded service
  → Wait for API recovery or use fallback

ESCALATION:
- If not resolved in 15 min: Page engineering lead
- If production down: Notify all stakeholders
```

### Database Issues

```bash
SYMPTOMS:
- Database connection timeouts
- Slow queries (>5s)
- Connection pool exhaustion

IMMEDIATE:
1. Check Neon dashboard status
2. Monitor current connections
3. Review slow query logs

RESOLUTION:
1. Restart connection pool
2. Increase pool size if needed
3. Kill long-running queries if safe
4. Restore from backup if data corruption

BACKUP RESTORATION:
1. Go to Neon Dashboard → Backups
2. Select point-in-time to restore
3. Click "Restore"
4. Wait 5-10 minutes
5. Test connectivity
6. Update DATABASE_URL if needed
7. Restart service
```

---

## Task 4.2: Scaling Procedures

```bash
HORIZONTAL SCALING (Add instances):
1. Render Dashboard → Settings → Plan
2. Change from "2 instances" to "3" or "4"
3. Render auto-scales and load balances
4. Monitor metrics for improvement

VERTICAL SCALING (Upgrade instance):
1. Render Dashboard → Settings → Instance Type
2. Upgrade from Standard to Pro
3. Service briefly restarts
4. More CPU/memory available

AUTO-SCALING TRIGGERS:
- CPU > 80% → Add instance (max 4)
- CPU < 20% → Remove instance (min 2)
- Memory > 85% → Alert and log
- Response time > 10s → Investigate

SCALING CHECKLIST:
✅ Monitor metrics during scaling
✅ Load test after scaling
✅ Update capacity planning docs
✅ Notify stakeholders if major change
✅ Document reason for scaling
```

---

## Task 4.3: Rollback Procedures

```bash
ROLLBACK OPTION 1: Git Revert (Fastest)
1. Identify commit to revert
2. Run: git revert HEAD
3. Run: git push origin main
4. GitHub Actions auto-deploys
5. Render pulls new Docker image
6. Service restarts (< 2 min downtime)

ROLLBACK OPTION 2: Docker Tag
1. Render Dashboard → Environment → DOCKER_IMAGE_TAG
2. Change to previous tag (e.g., main-abc123)
3. Service restarts with old image

ROLLBACK OPTION 3: Database Rollback
1. Neon Dashboard → Backups
2. Select pre-deployment backup
3. Click "Restore"
4. Test connectivity
5. Restart service

TESTING ROLLBACK:
- Practice quarterly
- Document time to complete
- Verify zero data loss
- Test from different locations
```

---

## Task 4.4: On-Call Rotation

```bash
PRIMARY ON-CALL SCHEDULE:
Week 1: Engineer A (Mon-Sun)
Week 2: Engineer B (Mon-Sun)
Week 3: Engineer C (Mon-Sun)
Week 4: Engineer D (Mon-Sun)

RESPONSIBILITIES:
- Respond to PagerDuty alerts within 5 minutes
- Investigate and resolve incidents
- Escalate if needed after 15 minutes
- Document incident in postmortem
- Handoff to next on-call engineer

ESCALATION PATHS:
Primary (On-call) → Engineering Lead → VP Engineering

RESPONSE TIMES:
Work hours (9-5): 5 min response, 15 min resolution
Off hours (5-9, weekends): 15 min response, 60 min resolution
```

---

## Task 4.5: Operations Team Training

```bash
DAY 1: SYSTEM OVERVIEW
- Architecture walkthrough
- Key components (backend, database, vector store)
- External dependencies (OpenAI, Qdrant)
- Monitoring tools introduction

DAY 2: OPERATIONAL PROCEDURES
- Dashboard walkthrough
- Alert response procedures
- Runbook review
- Scaling procedures
- Rollback procedures

DAY 3: HANDS-ON LABS
- Trigger test alert
- Respond to simulated incident
- Practice scaling
- Database backup/restore
- Documentation review

CERTIFICATION:
- Pass quiz (80%+ score)
- Complete simulation incident
- Sign-off from engineering lead
```

---

## Task 4.6: Security Audit

```bash
OWASP TOP 10 CHECKS:
□ Injection attacks (SQL, command)
□ Broken authentication
□ Sensitive data exposure
□ XML external entities
□ Broken access control
□ Security misconfiguration
□ XSS attacks
□ Insecure deserialization
□ Using components with vulnerabilities
□ Insufficient logging

DEPENDENCY SCANNING:
```bash
owasp-dependency-check rag-backend/
bandit -r rag-backend/src
safety check -r rag-backend/requirements.txt
```

SECRET SCANNING:
```bash
truffleHog scan --json .
# Should return: No secrets found
```

SSL/TLS VERIFICATION:
```bash
openssl s_client -connect rag-chatbot-api.onrender.com:443
# Verify certificate validity and chain
```

API SECURITY:
- ✅ Rate limiting active
- ✅ API keys required
- ✅ CORS restricted
- ✅ Input validation
- ✅ Output encoding
```

---

## Task 4.7: Incident Response

```bash
INCIDENT SEVERITY LEVELS:

P1 (CRITICAL): Production down, data loss, security breach
- Response: Immediate
- Escalation: All hands
- Communication: Every 15 minutes

P2 (HIGH): Degraded performance (>50% error rate)
- Response: 5 minutes
- Escalation: After 15 minutes
- Communication: Every 30 minutes

P3 (MEDIUM): Partial outage (<50% error rate)
- Response: 30 minutes
- Escalation: After 1 hour
- Communication: Every hour

P4 (LOW): Minor issues, no user impact
- Response: Next business day
- Escalation: Engineering lead
- Communication: Daily summary

INCIDENT PROCESS:
1. Detection (alert triggered)
2. Page on-call engineer (< 1 min)
3. Acknowledge in PagerDuty (< 5 min)
4. Investigate (< 15 min)
5. Mitigate or escalate
6. Resolve
7. Document in postmortem
8. Review and improve
```

---

## Task 4.8: Performance Optimization

```bash
CACHING STRATEGIES:
1. Query result caching (Redis)
   - TTL: 24 hours
   - Invalidation: Manual or event-based

2. Vector similarity caching
   - Common questions pre-computed
   - Fallback to on-demand

DATABASE OPTIMIZATION:
1. Add indexes on frequently searched columns
2. Analyze query plans: EXPLAIN ANALYZE
3. Archive old sessions (>30 days)
4. Vacuum/analyze regularly

CONNECTION POOLING:
1. Max connections: 20 (tuned for concurrency)
2. Min connections: 5 (baseline)
3. Timeout: 30 seconds

MEASUREMENT:
- Latency p95: Target ≤6s
- Error rate: Target <1%
- Cache hit rate: Target >70%
```

---

## WAVE 4 Completion Checklist

```
✅ Emergency response runbook created
✅ Database recovery procedures documented
✅ Scaling procedures documented
✅ Rollback procedures tested
✅ On-call rotation configured
✅ Operations team trained (3 days)
✅ Certification signed off
✅ Security audit completed (OWASP)
✅ Dependency scan passed
✅ Secret scan passed (no secrets found)
✅ SSL/TLS verified
✅ Incident response playbook created
✅ Performance optimization implemented
✅ Monitoring alerts tested
✅ Backup/restore drill completed

WAVE 4 STATUS: ✅ COMPLETE
```

---

## Final Sign-Offs

```
Engineering Lead: _________________ Date: _______
Operations Lead: _________________ Date: _______
Security Lead: ___________________ Date: _______
Product Manager: _________________ Date: _______

PRODUCTION GO/NO-GO DECISION:
☐ GO FOR PRODUCTION
☐ NOT READY (requires fixes: _______________)
```

---

**WAVE 4 Complete!** → **All Phases Ready for Launch!** 🚀

Generated: 2025-12-17 | Version: 1.0
