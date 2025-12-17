# WAVE 2: Frontend Deployment - Docusaurus to GitHub Pages

**Phase 8 WAVE 2**: Frontend Deployment
**Duration**: 1 day | **Team**: Frontend Engineer

---

## Quick Start

```bash
# 1. GitHub Pages Settings
# Repository → Settings → Pages
# Source: GitHub Actions

# 2. Deploy workflow already configured
# File: .github/workflows/deploy.yml

# 3. Push to main
git push origin main

# 4. Verify
# Actions → deploy workflow → wait for completion
# Site available at: https://mehreen676.github.io/rag-chatbot
```

---

## Task 2.1: Configure GitHub Pages

```bash
# Repository Settings → Pages:
├── Source: GitHub Actions
├── Branch: gh-pages (auto-created by workflow)
├── Custom domain: (optional) your-domain.com
└── HTTPS: Enabled (automatic)

# Workflow deploys to gh-pages automatically
# See: .github/workflows/deploy.yml
```

**Status**: Site accessible at GitHub Pages URL

---

## Task 2.2: Update Frontend Configuration

```bash
# File: docusaurus_textbook/src/components/RagChatbot/config.js

export const API_URL = process.env.NODE_ENV === 'production'
  ? 'https://rag-chatbot-api.onrender.com'  # Backend URL from WAVE 1
  : 'http://localhost:8000';

export const API_KEY = process.env.REACT_APP_API_KEY || 'default-key';
```

**Test locally**:
```bash
cd docusaurus_textbook
npm run start
# Visit http://localhost:3000
# Chat widget should load
```

---

## Task 2.3: Test Frontend-Backend Integration

```bash
# 1. Verify backend is running
curl https://rag-chatbot-api.onrender.com/health

# 2. Start frontend (local testing)
cd docusaurus_textbook
npm run start

# 3. Test chat widget
# - Load chat
# - Send query
# - Verify response with sources
# - Check browser console for errors

# 4. Production test
# - Visit https://mehreen676.github.io
# - Repeat tests
```

**Expected**: Chat widget communicates with production backend

---

## Task 2.4: Set Up Analytics

```bash
# Google Analytics setup:
# 1. Create GA4 property: https://analytics.google.com
# 2. Get Measurement ID: G-XXXXXX
# 3. Add to docusaurus.config.js:

googleAnalytics: {
  trackingID: 'G-XXXXXX',
  anonymizeIP: true,
}

# 4. Rebuild and deploy
npm run build
git add .
git commit -m "Add analytics"
git push origin main
```

**Verification**: Analytics dashboard shows real-time visitors

---

## WAVE 2 Completion Checklist

```
✅ GitHub Pages enabled
✅ Deployment workflow configured
✅ Frontend deployed (en + ur locales)
✅ Site accessible and loading
✅ API endpoint configured
✅ Chat widget functional
✅ Frontend-backend integration working
✅ Analytics tracking active
✅ HTTPS enabled
✅ Performance: <3s load time

WAVE 2 STATUS: ✅ COMPLETE
```

---

## Troubleshooting

```bash
# Site not deploying?
# → Check Actions tab for workflow errors
# → Verify deploy.yml exists
# → Check branch is main

# Chat widget not loading?
# → Verify API_URL points to production backend
# → Check backend is running and healthy
# → Check CORS configuration

# Performance slow?
# → Check CDN caching
# → Minimize bundle size
# → Use lazy loading
```

---

**WAVE 2 Complete!** → Next: **WAVE 3 - Monitoring & Observability**

Generated: 2025-12-17 | Version: 1.0
