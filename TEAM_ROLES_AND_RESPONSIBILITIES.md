# Team Roles & Responsibilities - Deployment Day

**Deployment Window**: [FILL IN DATE & TIME]
**Duration**: 90-115 minutes
**Communication Channel**: [Slack/Discord/Teams]

---

## Role Assignments

### 🎯 **Team Lead (Deployment Commander)**
**Primary Responsibility**: Orchestrate deployment, manage timing, communicate status
**Experience Level**: Senior (has deployed systems before)
**Time Commitment**: 90-115 minutes continuous

#### Before Deployment (Day Before)
- [ ] Schedule 2-hour deployment window
- [ ] Notify all team members
- [ ] Confirm availability of all roles
- [ ] Set up communication channel
- [ ] Schedule post-deployment review meeting

#### During Deployment
**Timeline Milestones**:
- T-30 min: Send "Starting in 30 minutes" message
- T-0: Start timer, begin Phase 1
- Every 15 min: Update team on progress
- Phase completions: Send phase completion updates
- T+90: Deployment should be complete
- T+115: Absolute deadline, if not complete escalate

#### Status Updates (Send to #deployment or team channel):
```
T-30: "Starting RAG backend deployment in 30 minutes. All team members please be ready."

T-0: "Starting deployment - Phase 1: Credential Rotation begins now"

T+15: "✅ Phase 1 complete: Credentials rotated"
T+25: "✅ Phase 2 complete: Pre-deployment validation passed"
T+35: "✅ Phase 3 complete: Web service configured on Render"
T+45: "✅ Phase 4 complete: Environment variables added"
T+50: "✅ Phase 5 complete: Service deployed - Render shows LIVE"
T+55: "✅ Phase 6 complete: Health endpoint verified"
T+60: "✅ Phase 7 complete: All verification checks passed"
T+75: "✅ Phase 8 complete: Monitoring configured"
T+90: "✅ Phase 9 complete: Post-deployment checklist done"
T+95: "✅ Phase 10 complete: Frontend configured"
T+100: "✅ Phase 11 complete: Documentation updated"

T+100: "🎉 DEPLOYMENT COMPLETE - Backend is LIVE in production"
```

#### Decision Authority
You have authority to:
- [ ] STOP deployment if critical issues found
- [ ] ROLLBACK if problems unresolvable in 15 minutes
- [ ] ESCALATE to CTO if stuck
- [ ] EXTEND timeline if needed (notify stakeholders)

#### Failure Procedures
**If deployment fails before Phase 5 (deployment)**:
- Stop at current phase
- Notify team
- Review error with responsible role
- Fix issue
- Continue from failure point

**If deployment fails after Phase 5 (live in production)**:
- PAUSE further changes
- Assemble troubleshooting team
- Investigate for 15 minutes
- If unresolved: ROLLBACK to previous version

---

### 🔐 **Security Lead**
**Primary Responsibility**: Credential rotation, security validation
**Experience Level**: Senior (understands secrets management)
**Time Commitment**: 45 minutes + 5 minutes for follow-up

#### Phase 1: Credential Rotation (T+0 to T+45)
**Location**: Service provider dashboards (OpenAI, Neon, Qdrant, Groq, etc.)
**Parallel**: Can work independently while others prepare

**Tasks** (See DEPLOYMENT_DAY_RUNBOOK.md Phase 1):
- [ ] OpenAI API key rotation (5 min)
- [ ] Neon PostgreSQL password rotation (5 min)
- [ ] Qdrant API key rotation (5 min)
- [ ] Groq API key rotation (5 min)
- [ ] Additional services (Cohere, Gemini, Render) (10 min)
- [ ] Document all rotated keys in secure location (5 min)

#### Before Deployment Preparation (Day Before)
- [ ] Verify access to all service provider dashboards
- [ ] Test credential rotation process manually
- [ ] Prepare password manager for storing new keys
- [ ] Have old key deactivation schedule ready

#### Credential Tracking Spreadsheet (CONFIDENTIAL)
Create a tracker with:
- Service Name | Old Key | New Key | Rotation Date | Verified | Deactivated
- Keep in secure location (password manager, vault)
- Do NOT commit to git
- Do NOT share in chat

#### After Rotation
- [ ] Confirm Team Lead that Phase 1 complete
- [ ] Monitor for credential-related errors during deployment
- [ ] Document any issues for post-mortems
- [ ] Schedule credential cleanup (old key deactivation)

#### Credential Deactivation Schedule (Post-Deployment)
After deployment is live and verified:
- [ ] Day 1: Verify new credentials working in production
- [ ] Day 3: Deactivate old OpenAI key
- [ ] Day 3: Deactivate old Neon password
- [ ] Day 3: Deactivate old Qdrant key
- [ ] Day 3: Deactivate old Groq key
- [ ] Week 1: Final cleanup of all old credentials

**Security Validation**:
- [ ] Verify no credentials in git history: `git log --all --oneline | grep -i "key\|password\|secret"`
- [ ] Verify .env not tracked: `git ls-files | grep .env`
- [ ] Verify .gitignore includes .env
- [ ] Confirm old credentials disabled

---

### ⚙️ **DevOps Engineer**
**Primary Responsibility**: Execute deployment phases, manage Render, verify system
**Experience Level**: Mid-level (has used Render or similar PaaS before)
**Time Commitment**: 75 minutes continuous + 15 minutes monitoring

#### Phases Owned:
- Phase 2: Pre-deployment validation (10 min)
- Phase 3: Web service creation (10 min)
- Phase 4: Environment variables (10 min)
- Phase 5: Deploy service (5 min)
- Phase 6: Immediate verification (5 min)
- Phase 7: Verification script (5 min)
- Phase 8: Monitoring setup (15 min)

#### Pre-Deployment Prep (Day Before)
- [ ] Test all scripts locally
- [ ] Verify Render.com account access
- [ ] Verify GitHub account access
- [ ] Ensure internet connection stable
- [ ] Have all documentation open and ready

#### Phase 2: Pre-Deployment Validation (T+45-55)
```bash
cd /path/to/project
bash deploy-to-render.sh
```
**Expected**: All checks pass
**If fails**: Fix issues before proceeding

#### Phase 3-5: Render Deployment (T+55-65)
```bash
1. Open https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Select repository and branch
4. Configure service (name, commands, etc.)
5. Open environment variables section (DO NOT SUBMIT YET)
```

#### Phase 4: Add Environment Variables (T+65-75)
**Critical Actions**:
- [ ] Use NEW rotated keys from Security Lead (Phase 1)
- [ ] Do NOT use old keys
- [ ] Copy-paste from RENDER_ENV_VARS_QUICK_REFERENCE.txt
- [ ] Verify each variable before moving to next
- [ ] Final count: 25+ variables

**Required Variables** (from Phase 1):
- ENVIRONMENT=production
- DEBUG=false
- DATABASE_URL=[NEW from Neon]
- QDRANT_API_KEY=[NEW from Qdrant]
- OPENAI_API_KEY=[NEW from OpenAI]
- GROQ_API_KEY=[NEW from Groq]
- SECRET_KEY=[Generated]
- ALLOWED_ORIGINS_STR=[Frontend URLs]
- Plus 15+ more (see reference file)

#### Phase 5: Deploy (T+75-80)
```bash
1. Final review of all settings
2. Click "Create Web Service"
3. Watch deployment progress
4. Expected: ~4-5 minutes to "Live" status
```

**Monitoring**:
- [ ] Watch for "Building..." status
- [ ] Watch log entries appear
- [ ] Alert if any ERROR logs
- [ ] Confirm "Live" status (green checkmark)

#### Phase 6: Immediate Verification (T+80-85)
```bash
# Test 1: Health check
curl https://rag-chatbot-backend.onrender.com/health

# Test 2: API docs
Open: https://rag-chatbot-backend.onrender.com/docs

# Test 3: Query endpoint
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "mode": "full_book"}'

# Test 4: Review logs
Check Render dashboard → Logs (no ERROR messages)
```

**Success Criteria**: All 4 tests pass

#### Phase 7: Verification Script (T+85-90)
```bash
# Run automated verification
bash DEPLOY_VERIFICATION.sh https://rag-chatbot-backend.onrender.com

# Expected: All 6 checks pass (green checkmarks)
```

#### Phase 8: Monitoring Setup (T+90-105, parallel)
```bash
1. UptimeRobot: Create health check monitor
2. Slack: Configure deployment notifications (optional)
3. Verify monitoring shows "UP"
```

#### Post-Deployment (Day 1 - 1 hour)
- [ ] Monitor Render dashboard for 60 minutes
- [ ] Watch for any error spikes
- [ ] Monitor resource usage (CPU, memory)
- [ ] Verify uptime in UptimeRobot
- [ ] Be available for troubleshooting

#### If Issues Arise
- [ ] Check Render logs immediately
- [ ] Verify environment variables
- [ ] Check external service status (Qdrant, Neon, OpenAI)
- [ ] Contact service providers if needed
- [ ] Report to Team Lead

---

### 📊 **Operations Lead**
**Primary Responsibility**: Post-deployment verification, monitoring setup, operations handoff
**Experience Level**: Mid-level (understands monitoring and ops procedures)
**Time Commitment**: 30 minutes during deployment + 60 minutes Day 1

#### Phase 8-9: Monitoring & Checklist (T+90-120, parallel with DevOps)

#### Phase 8: Monitoring Setup (T+90-105, parallel)
**Render-Built-in Monitoring**:
- [ ] Enable deploy notifications
- [ ] Configure resource alerts
- [ ] Set up log viewing

**External Monitoring (UptimeRobot)**:
- [ ] Create health check monitor
- [ ] Set frequency to 5 minutes
- [ ] Configure email alerts
- [ ] Test alerts (optional)

**Alerting Setup**:
- [ ] Set alert on service DOWN
- [ ] Set alert on service UP
- [ ] Set alert recipients (email/Slack)
- [ ] Test alert system

#### Phase 9: Post-Deployment Checklist (T+105-120)
Execute all items from POST_DEPLOYMENT_CHECKLIST.md "First Hour Checks":
- [ ] Run verification script
- [ ] Test query endpoint (5 different queries)
- [ ] Check database connectivity
- [ ] Check vector store connectivity
- [ ] Review all logs (no errors)
- [ ] Monitor performance metrics

#### Day 1: Production Monitoring (9 AM - 5 PM)

**Morning (9-12 PM)**:
- [ ] Verify "Live" status
- [ ] Check UptimeRobot uptime (should be ~100%)
- [ ] Review Render logs (no errors)
- [ ] Test health endpoint: `curl https://rag-chatbot-backend.onrender.com/health`
- [ ] Verify frontend → backend connection works

**Afternoon (12-5 PM)**:
- [ ] Monitor performance metrics hourly
- [ ] Check for error patterns
- [ ] Monitor API costs (OpenAI dashboard)
- [ ] Monitor database storage
- [ ] Monitor Qdrant usage
- [ ] Be available for support

**Actions if Issues**:
- [ ] Document issue in incident log
- [ ] Notify Team Lead
- [ ] Escalate to DevOps Engineer if needed
- [ ] Follow OPERATIONS_MANUAL.md incident procedures

#### Week 1: Operations Handoff
- [ ] Schedule daily standup for operations team
- [ ] Review OPERATIONS_MANUAL.md daily procedures
- [ ] Set up weekly performance review meetings
- [ ] Document any issues for lessons learned

---

### 💻 **Frontend Developer**
**Primary Responsibility**: Update frontend configuration, verify integration
**Experience Level**: Any (only requires code edit + testing)
**Time Commitment**: 10 minutes during deployment + 15 minutes integration testing

#### Pre-Deployment Prep (Day Before)
- [ ] Identify where API_URL is configured in code
- [ ] Backup current configuration
- [ ] Prepare code change
- [ ] Test locally with localhost first

#### Phase 10: Frontend Configuration (T+100-105)

**Update API Configuration** (parallel task - can start when backend deploys):
```javascript
// File: docusaurus_textbook/src/config.js (or wherever API_URL is defined)

// Before deployment (current):
const API_URL = "http://localhost:8000";

// After deployment (production):
const API_URL = process.env.NODE_ENV === 'production'
  ? "https://rag-chatbot-backend.onrender.com"
  : "http://localhost:8000";
```

**Steps**:
- [ ] Edit configuration file
- [ ] Replace localhost with `https://rag-chatbot-backend.onrender.com`
- [ ] Commit change (optional, can commit later)
- [ ] Build frontend locally to verify no errors

#### Post-Deployment Testing (T+105-120)

**Local Testing** (before deploying frontend):
- [ ] `npm run build` or `yarn build` (verify no errors)
- [ ] Start dev server: `npm start` or `yarn start`
- [ ] Open frontend in browser
- [ ] Test query functionality
- [ ] Verify responses received from backend
- [ ] Check browser console for errors

**Expected Behavior**:
- [ ] Frontend loads without errors
- [ ] Can input query and submit
- [ ] Backend responds with results
- [ ] Results display correctly
- [ ] No CORS errors in console

#### If CORS Errors Occur
**Common Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**:
- [ ] Check ALLOWED_ORIGINS_STR in Render environment variables
- [ ] Verify it includes frontend URL
- [ ] For Docusaurus frontend: `https://mehreen676.github.io`
- [ ] Contact DevOps to update if needed

#### Day 1: Integration Testing (1 hour)

**Morning**:
- [ ] Test 5 different queries
- [ ] Verify responses match expectations
- [ ] Check sources/citations
- [ ] Verify performance (should be <5s)
- [ ] Check error handling (empty query, invalid input)

**Documentation**:
- [ ] Document API response format
- [ ] Share with team
- [ ] Update frontend README

---

### 📢 **Communications Manager (Optional)**
**Primary Responsibility**: Keep stakeholders informed
**Experience Level**: Any
**Time Commitment**: 15 minutes before + continuous updates

#### Before Deployment
- [ ] Prepare announcement for users/stakeholders
- [ ] Schedule deployment notifications
- [ ] Prepare FAQ for common questions
- [ ] Identify communication channels

#### During Deployment
- [ ] Share Team Lead status updates with stakeholders
- [ ] Monitor support channels for incoming questions
- [ ] Escalate urgent issues to Team Lead
- [ ] Document questions for post-deployment FAQ

#### Templates (Customize as Needed):

**Pre-Deployment Announcement** (24 hours before):
```
Subject: Scheduled System Maintenance - RAG Backend Deployment

Hello team,

We have scheduled a system upgrade for the RAG backend on [DATE] at [TIME] (EST).

Expected downtime: None (zero-downtime deployment)
Duration: Approximately 90 minutes
Impact: No service interruption expected

During this window:
- Backend APIs will remain available
- Query responses may take up to 30 seconds longer
- We recommend avoiding new data uploads

Questions? Contact #support-channel

Thank you for your patience!
```

**Live Announcement**:
```
Subject: RAG Backend Deployment - In Progress

Hello,

We're currently deploying the latest RAG backend improvements. The system will remain available but may experience brief slowdowns.

Status: Live deployment in progress
Estimated completion: [TIME]
Status updates: Available at #deployment-status

Thank you!
```

**Success Announcement**:
```
Subject: RAG Backend Deployment - Complete!

Hello,

The RAG backend deployment is complete! The system is now live with improved performance and new features.

✅ Deployment successful
✅ All systems operational
✅ Zero downtime achieved

New features:
- Improved query response times
- Better vector search accuracy
- Enhanced error handling

Thank you for your patience!
```

---

## Team Schedule

### Day Before (Verification)

| Time | Role | Activity |
|------|------|----------|
| 2 PM | All | Final preparation checks |
| 3 PM | Team Lead | Schedule window, notify team |
| 4 PM | DevOps | Test scripts locally |
| 4 PM | Security | Test credential rotation |
| 5 PM | Operations | Review procedures |

### Deployment Day

| Time | Duration | Role | Phase | Activity |
|------|----------|------|-------|----------|
| 8:30 AM | 15 min | All | Setup | Final checks, open dashboards |
| 8:45 AM | 1 min | Team Lead | Kickoff | "Deployment starting now" |
| 9:00 AM | 45 min | Security | 1 | Credential rotation |
| 9:00 AM | 10 min | DevOps | 2 | Pre-flight validation |
| 9:15 AM | 10 min | DevOps | 3 | Web service creation |
| 9:25 AM | 10 min | DevOps | 4 | Environment variables |
| 9:35 AM | 5 min | DevOps | 5 | Deploy service |
| 9:40 AM | 5 min | DevOps | 6 | Immediate verification |
| 9:45 AM | 5 min | DevOps | 7 | Verification script |
| 9:50 AM | 15 min | DevOps + Ops | 8 | Monitoring setup |
| 9:50 AM | 30 min | Operations | 9 | Post-deployment checklist |
| 10:20 AM | 5 min | Frontend | 10 | Frontend update |
| 10:25 AM | 10 min | Team Lead | 11 | Docs & communication |
| 10:35 AM | - | All | Complete | Deployment done! |

### Day 1 (Monitoring)

| Time | Duration | Role | Activity |
|------|----------|------|----------|
| 9 AM | 60 min | Operations | Monitor deployment health |
| 10 AM | 30 min | Frontend | Integration testing |
| 1 PM | 30 min | Team Lead | Mid-day check-in |
| 5 PM | 30 min | All | Daily wrap-up, document issues |

---

## Communication Channels

**During Deployment**:
- **Primary**: #deployment-status (Slack/Discord)
- **Urgent Issues**: @team-lead
- **Technical Help**: #devops-support

**Status Updates**:
- Every 15 minutes or when phase completes
- Format: "[PHASE X] Status - Description"
- Examples:
  - "✅ [Phase 2] Pre-deployment validation passed"
  - "⏳ [Phase 5] Service deploying to Render (~4 min)"
  - "⚠️ [Phase 6] Health check investigating error..."
  - "🎉 [Complete] Deployment successful, backend LIVE"

---

## Escalation Path

**If something goes wrong:**

1. **Immediate Issue (T+0-5 min)**
   - Team Lead pauses deployment
   - Responsible role investigates
   - Escalate to CTO if blocking

2. **Unresolved Issue (T+15 min)**
   - Team Lead decides: Fix or Rollback?
   - If fixable: Continue troubleshooting
   - If not: Execute ROLLBACK procedure

3. **Post-Deployment Issue**
   - Follow OPERATIONS_MANUAL.md incident procedures
   - Document issue for post-mortem
   - Prepare lessons learned presentation

---

## Success Criteria

**Deployment is successful when:**
- [ ] Service shows "Live" in Render dashboard
- [ ] Health endpoint responds with 200 OK
- [ ] API documentation accessible at /docs
- [ ] Query endpoint returns valid responses
- [ ] All verification checks pass
- [ ] No ERROR logs in Render
- [ ] UptimeRobot shows "UP"
- [ ] Frontend successfully queries backend
- [ ] Monitoring alerts configured
- [ ] Team trained on operations

---

## Post-Deployment Review

**Schedule**: Day 1 (5 PM) + Week 1 (Friday)

**Attendees**: Team Lead, DevOps, Operations, Frontend, Security

**Topics**:
- What went well?
- What was challenging?
- What should we improve next time?
- Any incidents or issues?
- Lessons learned?
- Documentation updates needed?

---

**Team Roles & Responsibilities Complete**
