# Deployment Day Runbook - RAG Backend to Render.com

**Deployment Date**: [FILL IN DATE]
**Estimated Duration**: 90-115 minutes
**Status**: Ready to Execute
**Risk Level**: Low (all tests passing, infrastructure verified)

---

## Pre-Deployment (Day Before)

### Team Lead
- [ ] Schedule 2-hour deployment window
- [ ] Notify all teams of deployment time
- [ ] Ensure all team members available
- [ ] Set up communication channel (Slack/Discord)
- [ ] Verify backup runbook is accessible

### DevOps Engineer
- [ ] Verify all 9 commits are in GitHub
- [ ] Confirm branch is `feature/2-rag-chatbot-integration`
- [ ] Test deployment scripts locally (`bash deploy-to-render.sh`)
- [ ] Verify Render.com account access
- [ ] Confirm all service provider accounts accessible:
  - OpenAI API dashboard
  - Neon PostgreSQL dashboard
  - Qdrant Cloud dashboard
  - GitHub account
  - Render.com account

### Security Lead
- [ ] Review credential rotation checklist
- [ ] Verify no credentials in recent commits
- [ ] Confirm all credentials ready for rotation
- [ ] Document old credential deactivation schedule

---

## **T-30 MINUTES: Final Preparation**

### DevOps Engineer
**Checklist**:
- [ ] Open Render.com dashboard
- [ ] Open GitHub repository
- [ ] Have RENDER_ENV_VARS_QUICK_REFERENCE.txt open
- [ ] Have RENDER_DEPLOYMENT_GUIDE.md ready
- [ ] Test internet connection & VPN if needed
- [ ] Close unrelated applications
- [ ] Set up dual monitors if available

### Security Lead
**Checklist**:
- [ ] Have new API keys generated/ready
- [ ] Have SECRET_KEY generation command ready
- [ ] Have credential rotation checklist open
- [ ] Verify credential vaults/password managers accessible

### Team Lead
**Communication**:
- [ ] Send Slack message: "Deployment starts in 30 minutes"
- [ ] Confirm all team members are ready
- [ ] Set 90-minute timer
- [ ] Enable deployment notification alerts

---

## **T-0: DEPLOYMENT STARTS** ⏱️

### Phase 1: Credential Rotation (30-45 minutes)

**Owner**: Security Lead
**Location**: Render dashboard + service provider dashboards
**Critical**: DO NOT SKIP - Old credentials must be rotated

#### Step 1: OpenAI API Key Rotation (5 min)
```bash
1. Go to: https://platform.openai.com/api-keys
2. Find current key (starts with sk-proj-)
3. Click "Delete key"
4. Confirm deletion
5. Click "Create new secret key"
6. Copy new key
7. SAVE in password manager with label "Production OpenAI Key [DATE]"
```
**Verification**: New key starts with `sk-` or `sk-proj-`

#### Step 2: Neon PostgreSQL Password Rotation (5 min)
```bash
1. Go to: https://neon.tech/console/projects
2. Select your project
3. Go to "Connection details"
4. Click "Reset password" for role "neondb_owner"
5. Copy new connection string
6. SAVE in password manager
7. Format: postgresql://user:password@host/database
```
**Verification**: Connection string includes new password

#### Step 3: Qdrant API Key Rotation (5 min)
```bash
1. Go to: https://cloud.qdrant.io/dashboards
2. Select your cluster
3. Go to "API keys" or "Security"
4. Click "Regenerate key"
5. Confirm regeneration
6. Copy new API key
7. SAVE in password manager
```
**Verification**: New key is JWT format or alphanumeric string

#### Step 4: Groq API Key Rotation (5 min)
```bash
1. Go to: https://console.groq.com/keys
2. Find current key
3. Delete or revoke current key
4. Create new API key
5. Copy new key
6. SAVE in password manager
```
**Verification**: New key starts with `gsk_` or similar format

#### Step 5: Additional Service Keys (10 min)
Repeat for:
- [ ] Cohere API key (https://dashboard.cohere.com/api-keys)
- [ ] Gemini API key (https://aistudio.google.com/app/apikey)
- [ ] Render API key (https://dashboard.render.com/account/api-keys)
- [ ] GitHub OAuth keys (if configured)
- [ ] Google OAuth keys (if configured)

**Team Lead Update**: "✅ Phase 1: Credentials rotated"

---

### Phase 2: Pre-Deployment Validation (10 minutes)

**Owner**: DevOps Engineer
**Location**: Terminal/Command line
**Command**: `bash deploy-to-render.sh`

```bash
cd /path/to/project
bash deploy-to-render.sh
```

**Expected Output**:
```
✓ Git repository verified
✓ .env file properly excluded
✓ Required environment variables documented
✓ Test suite passing
✓ Deployment files present
✓ Ready for deployment!
```

**If any checks fail**:
- STOP deployment
- Notify team lead
- Review and fix issue
- Re-run validation
- Continue only when all checks pass

**Team Lead Update**: "✅ Phase 2: Pre-deployment validation complete"

---

### Phase 3: Render.com Web Service Creation (10 minutes)

**Owner**: DevOps Engineer
**Location**: https://render.com/dashboard
**Time Budget**: 10 minutes

#### Step 1: Create New Web Service (2 min)
```
1. Click "New +" button
2. Select "Web Service"
3. Authorize GitHub access if needed
4. Select repository: "Spec-Driven-Development-Hackathons-main"
5. Select branch: "feature/2-rag-chatbot-integration"
6. Click "Next"
```

#### Step 2: Configure Service Settings (3 min)
```
Name:                rag-chatbot-backend
Runtime:             Python 3
Root Directory:      (leave empty)
Build Command:       cd rag-backend && pip install -r requirements.txt
Start Command:       cd rag-backend && uvicorn src.main:app --host 0.0.0.0 --port $PORT
Plan:                Free
Region:              [Choose closest region]
```

#### Step 3: Environment Variables Section - IMPORTANT (5 min)
**Do NOT click "Create Web Service" yet!**

Scroll to "Environment" section:
- [ ] Check "Add Environment Variables"
- [ ] Do NOT close the form
- [ ] Keep this page open for Phase 4

**Team Lead Update**: "✅ Phase 3: Web service configured"

---

### Phase 4: Add Environment Variables (10 minutes)

**Owner**: DevOps Engineer
**Source**: RENDER_ENV_VARS_QUICK_REFERENCE.txt
**Credentials**: Use newly rotated keys from Phase 1
**Critical**: Use correct values - do NOT use old keys

#### Variables to Add (Copy from RENDER_ENV_VARS_QUICK_REFERENCE.txt):

```
# Deployment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database (NEW - from Phase 1 Step 2)
DATABASE_URL=postgresql://[user]:[NEW_PASSWORD]@[host]/[db]

# Qdrant (NEW - from Phase 1 Step 3)
QDRANT_URL=https://[cluster].qdrant.io
QDRANT_API_KEY=[NEW_KEY_FROM_PHASE_1]
QDRANT_COLLECTION_NAME=aibook_chunk

# OpenAI Embeddings (NEW - from Phase 1 Step 1)
OPENAI_API_KEY=[NEW_KEY_FROM_PHASE_1]
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Groq Generation (NEW - from Phase 1 Step 4)
GROQ_API_KEY=[NEW_KEY_FROM_PHASE_1]
GROQ_LLM_MODEL=llama-3.1-70b-versatile

# Additional LLMs
COHERE_API_KEY=[NEW_KEY_FROM_PHASE_1]
COHERE_LLM_MODEL=command
GEMINI_API_KEY=[NEW_KEY_FROM_PHASE_1]

# Fallback
OPENAI_LLM_MODEL=gpt-4o-mini
OPENAI_LLM_FALLBACK_MODEL=gpt-3.5-turbo

# Security (GENERATE NEW - from Phase 1)
SECRET_KEY=[GENERATED_IN_PHASE_1]

# Frontend
ALLOWED_ORIGINS_STR=https://mehreen676.github.io,https://rag-chatbot-backend.onrender.com

# Rate Limiting
RATE_LIMIT_QUERIES_PER_MINUTE=10
RATE_LIMIT_QUERIES_PER_DAY=1000
SESSION_TIMEOUT_HOURS=24
```

#### How to Add Each Variable:
```
For each variable:
1. Click "Add Environment Variable"
2. Enter Key (left field)
3. Enter Value (right field) - USE NEW KEYS!
4. Press Enter or click elsewhere
5. Variable appears in list
```

**Verification Checklist**:
- [ ] All 25+ variables added
- [ ] No variables show `<YOUR_...>` placeholder
- [ ] All sensitive vars masked (show as ***)
- [ ] ENVIRONMENT=production (not development)
- [ ] DEBUG=false (not true)
- [ ] DATABASE_URL contains NEW password
- [ ] QDRANT_API_KEY is NEW key
- [ ] OPENAI_API_KEY is NEW key
- [ ] GROQ_API_KEY is NEW key
- [ ] SECRET_KEY is generated value

**Team Lead Update**: "✅ Phase 4: Environment variables configured"

---

### Phase 5: Deploy Service (5 minutes)

**Owner**: DevOps Engineer
**Location**: Render dashboard
**Action**: Click the button

#### Step 1: Final Review
Before clicking "Create Web Service":
- [ ] Verify all variables are correct
- [ ] Review service name: `rag-chatbot-backend`
- [ ] Review build command includes `cd rag-backend`
- [ ] Review start command uses `$PORT`
- [ ] Region is selected

#### Step 2: Create Service
```
1. Click "Create Web Service" button
2. Watch deployment start
3. Render begins cloning repository
4. Render installs dependencies
5. Render starts uvicorn server
```

**Expected Timeline**:
- 0-30 sec: Repository cloning
- 30 sec-2 min: Python installation
- 2-3 min: Dependency installation
- 3-4 min: Server startup
- **Total: ~4-5 minutes**

#### Step 3: Monitor Deployment
Keep Render dashboard open and watch for:
- [ ] "Building..." status
- [ ] Yellow/orange progress indicators
- [ ] Build log entries appearing
- [ ] No ERROR level logs
- [ ] Status changes to "Live" (green checkmark)

**If deployment fails**:
- [ ] STOP
- [ ] Click "Redeploy"
- [ ] Check logs for error message
- [ ] Report to team lead
- [ ] Do NOT continue until fixed

**Success Indicator**: Green "Live" status on dashboard

**Team Lead Update**: "✅ Phase 5: Service deployed to Render.com"

---

### Phase 6: Immediate Verification (5 minutes)

**Owner**: DevOps Engineer
**Command**: Health check + API docs access

#### Step 1: Health Check (1 min)
```bash
curl https://rag-chatbot-backend.onrender.com/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T...",
  "version": "1.0.0",
  "environment": "production"
}
```

**Acceptable**: 200 status code + "status": "healthy"

#### Step 2: API Documentation (1 min)
```
Open in browser:
https://rag-chatbot-backend.onrender.com/docs
```

**Expected**: Swagger UI loads with all endpoints visible

#### Step 3: Test Query Endpoint (2 min)
```bash
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is ROS?", "mode": "full_book"}'
```

**Expected**: 200 status code with JSON response including "answer" field

#### Step 4: Quick Logs Review (1 min)
In Render dashboard → Logs:
- [ ] No ERROR level messages
- [ ] No repeated warning patterns
- [ ] Startup messages indicate successful boot

**If any check fails**:
- [ ] Check Render logs for error details
- [ ] Verify environment variables
- [ ] Check external services (Qdrant, Neon, OpenAI)
- [ ] Contact service providers if needed

**Team Lead Update**: "✅ Phase 6: Service verified - Backend LIVE"

---

### Phase 7: Detailed Verification Script (5 minutes)

**Owner**: DevOps Engineer
**Command**: Run automated verification

```bash
# Linux/Mac
bash DEPLOY_VERIFICATION.sh https://rag-chatbot-backend.onrender.com

# Windows
DEPLOY_VERIFICATION.bat https://rag-chatbot-backend.onrender.com
```

**Expected Output**: All 6 checks pass (green checkmarks)

```
✓ Health endpoint responding
✓ API documentation accessible
✓ Query endpoint functional
✓ Ingest endpoint accessible
✓ Response time acceptable
✓ All systems operational
```

**If any check fails**:
- [ ] Review error message
- [ ] Check corresponding service
- [ ] Investigate in Render logs
- [ ] Retry check

**Team Lead Update**: "✅ Phase 7: All verification checks passed"

---

### Phase 8: Monitoring Setup (15 minutes)

**Owner**: DevOps Engineer + Operations Lead
**Location**: External monitoring services
**Time**: 15 minutes parallel with other setup

#### UptimeRobot Health Checks (5 min)
```
1. Go to https://uptimerobot.com
2. Create new monitor
3. URL: https://rag-chatbot-backend.onrender.com/health
4. Frequency: Every 5 minutes
5. Name: "RAG Backend Health"
6. Click "Create Monitor"
7. Verify monitor shows "UP"
```

#### Email Alerts Configuration (5 min)
```
1. Settings → Alerts
2. Add email recipients
3. Alert when status changes to "DOWN"
4. Alert when status returns to "UP"
5. Test alert (optional)
```

#### Slack Integration (Optional, 5 min)
```
1. UptimeRobot → Integrations
2. Find Slack
3. Connect Slack workspace
4. Select #deployments channel (or create)
5. Test integration
```

**Team Lead Update**: "✅ Phase 8: Monitoring configured"

---

### Phase 9: Post-Deployment Checklist (30 minutes)

**Owner**: Operations Lead
**Reference**: POST_DEPLOYMENT_CHECKLIST.md
**Parallel**: Can start while devops handles other tasks

Execute all items from "First Hour Checks" section:
- [ ] Run verification script again
- [ ] Test query endpoint manually
- [ ] Check database connectivity
- [ ] Check vector store connectivity
- [ ] Review all logs (no errors)
- [ ] Test 5 different queries

**Expected**: All checks pass, system operating normally

**Team Lead Update**: "✅ Phase 9: Post-deployment checklist complete"

---

### Phase 10: Frontend Update (5 minutes)

**Owner**: Frontend Developer
**File**: `docusaurus_textbook/src/config.js` or API config

```javascript
// Update from:
const API_URL = "http://localhost:8000";

// To:
const API_URL = process.env.NODE_ENV === 'production'
  ? "https://rag-chatbot-backend.onrender.com"
  : "http://localhost:8000";
```

#### Steps:
1. [ ] Edit frontend config file
2. [ ] Update backend URL to: `https://rag-chatbot-backend.onrender.com`
3. [ ] Test frontend in development
4. [ ] Test end-to-end query flow
5. [ ] Verify CORS allows frontend

**Verification**: Frontend can query backend and receive responses

**Team Lead Update**: "✅ Phase 10: Frontend configured"

---

### Phase 11: Documentation & Communication (10 minutes)

**Owner**: Team Lead
**Activities**:

#### Internal Documentation:
- [ ] Document actual deployment time
- [ ] Record any issues encountered
- [ ] Note any deviations from plan
- [ ] Update deployment checklist with lessons learned

#### Team Communication:
- [ ] Announce deployment success in Slack
- [ ] Share production URL: `https://rag-chatbot-backend.onrender.com`
- [ ] Share API docs URL: `https://rag-chatbot-backend.onrender.com/docs`
- [ ] Notify users (if applicable)
- [ ] Update status page (if applicable)

#### Documentation Updates:
- [ ] Update README with production URLs
- [ ] Update team wiki/confluence
- [ ] Share API client examples with frontend team
- [ ] Distribute OPERATIONS_MANUAL.md to ops team

**Team Lead Update**: "✅ Phase 11: Documentation & communication complete"

---

## **DEPLOYMENT COMPLETE** ✅

**Total Time**: 90-115 minutes
**Status**: LIVE IN PRODUCTION
**Next**: Day 1 monitoring and Week 1 optimization

---

## Post-Deployment (Day 1)

### Morning (9 AM)
- [ ] Check Render dashboard - confirm "Live" status
- [ ] Check UptimeRobot - confirm 100% uptime
- [ ] Review Render logs - no errors
- [ ] Test health endpoint manually
- [ ] Verify frontend can query backend

### Afternoon (3 PM)
- [ ] Review performance metrics
- [ ] Check API costs (OpenAI dashboard)
- [ ] Monitor Qdrant vector usage
- [ ] Monitor Neon database storage
- [ ] Check for any error patterns

### End of Day (5 PM)
- [ ] Complete POST_DEPLOYMENT_CHECKLIST.md fully
- [ ] Schedule Week 1 optimization tasks
- [ ] Set calendar reminder for weekly review

---

## Post-Deployment (Week 1)

Follow OPERATIONS_MANUAL.md:
- [ ] Daily health checks
- [ ] Weekly cost review
- [ ] Weekly performance analysis
- [ ] Begin optimization tasks

---

## Rollback Procedure (If Needed)

**If critical issues occur and cannot be resolved within 15 minutes:**

### Step 1: Stop Traffic
- [ ] In Render dashboard, click "Suspend"
- [ ] This stops the service without deleting it

### Step 2: Revert to Previous Version
Option A: Re-deploy main branch
```bash
git checkout main
git push origin main
```

Option B: In Render, select previous deployment:
- [ ] Click "Deployments" tab
- [ ] Find previous successful deployment
- [ ] Click "Redeploy"

### Step 3: Verify
- [ ] Check health endpoint responds
- [ ] Verify frontend works
- [ ] Check logs for errors

### Step 4: Communicate
- [ ] Notify team of rollback
- [ ] Document what went wrong
- [ ] Schedule remediation meeting

---

## Emergency Contacts

**If problems occur:**

- **Render Support**: https://dashboard.render.com/help
- **Neon PostgreSQL**: https://neon.tech/docs/introduction/support
- **Qdrant**: https://qdrant.tech/documentation/
- **OpenAI**: https://help.openai.com/

---

## Sign-Off

**Deployment Executed By**: _______________________
**Date**: _______________________
**Time Started**: _______________________
**Time Completed**: _______________________
**Status**: [ ] SUCCESS  [ ] ROLLBACK  [ ] ISSUES

**Issues Encountered**:
_________________________________________________________________

**Resolution**:
_________________________________________________________________

**Notes for Next Deployment**:
_________________________________________________________________

---

**Deployment Runbook Complete**
