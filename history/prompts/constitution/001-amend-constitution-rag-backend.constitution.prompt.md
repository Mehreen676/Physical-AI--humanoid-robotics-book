---
id: 001
title: Amend constitution to RAG backend system
stage: constitution
date: 2025-12-30
surface: agent
model: claude-haiku-4-5-20251001
feature: none
branch: 004-rag-frontend-integration
user: mehreen@example.com
command: /sp.constitution
labels: ["constitution", "rag-backend", "security", "architecture"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - No unresolved placeholders
  - Version bump from 1.0.0 to 2.0.0 (MAJOR)
  - All principles testable and non-vague
  - Sync Impact Report complete
---

## Prompt

You are an expert AI system architect and backend engineer.

You MUST follow SpecKit Plus methodology strictly.

CORE PRINCIPLES:
1. Security-first: NEVER hardcode API keys or secrets.
2. Backend-only implementation using Python.
3. Clear folder-based architecture.
4. Deterministic, debuggable, production-ready code.
5. Zero hallucination: if data is missing, say so.

PROJECT GOAL:
Build an Integrated Retrieval-Augmented Generation (RAG) chatbot embedded in a published book website.

TECH STACK (MANDATORY):
- Python 3.11+
- FastAPI (backend API)
- OpenAI Agents SDK + ChatKit SDK (agent orchestration)
- OpenRouter (LLM provider, NOT OpenAI API)
- Qdrant Cloud (vector database, free tier)
- Neon Serverless PostgreSQL (chat/session storage)
- Cohere embeddings OR compatible embedding model
- Environment variables via .env

FUNCTIONAL REQUIREMENTS:
1. Answer user questions using book content only.
2. Support "answer only from selected text" mode.
3. Preserve metadata (URL, section, chunk id).
4. No hallucinated answers.
5. Graceful fallback if answer not found.

ARCHITECTURE RULES:
- All backend code must live inside `/backend`
- Every logical unit must be in its own folder
- All Python files must be `.py`
- Agent logic must be inside `/backend/agent/agent.py`
- No frontend code unless explicitly requested

SECURITY RULES:
- Use placeholders like ENV_VAR_NAME
- Read secrets only from environment variables
- Never log secrets
- Never echo keys in responses

OUTPUT FORMAT RULES:
- Step-by-step
- Folder tree first
- Then code per file
- Then run instructions
- Then testing checklist

If anything is ambiguous, make a reasonable engineering assumption and document it.

## Response snapshot

**Updated constitution v2.0.0 (MAJOR bump)** reflecting project refocus from "Physical AI textbook" to "RAG chatbot backend system."

**Key changes:**
- Added Security-First Foundation as primary principle (env vars, no hardcoding)
- Refocused principles for backend/API-centric system (Zero-Hallucination Grounding, Developer-First Implementation)
- Removed robotics/citation context (theory-practice, citations, Docusaurus)
- Added Backend Architecture Rules section with mandatory `/backend` structure and folder organization template
- Added RAG-Specific Requirements section (answer grounding, metadata preservation, session management)
- Added API Security & Environment Management section with explicit env var list and startup validation
- Elevated Development Workflow to SDD methodology with PHR/ADR requirements
- Enhanced Governance with amendment procedure, compliance verification, quarterly audits

**Sync Impact Report generated:**
- 4 templates flagged for update (plan-template.md, spec-template.md, tasks-template.md, commands/*.md)
- Version change rationale: MAJOR (architecture & principles redefinition)
- Deferred follow-ups: Update templates to reflect backend-only architecture

**Validation passed:**
- No unresolved bracket tokens
- Version 2.0.0 matches report
- Dates in ISO format
- All principles declarative and testable (no vague "should" language)
- File at expected path: `.specify/memory/constitution.md`

## Outcome

- ✅ Impact: Constitution refocused for RAG backend; all downstream templates identified for update; governance strengthened with compliance checklist
- 🧪 Tests: All validation checks passed; Sync Impact Report complete; no placeholder tokens remain
- 📁 Files: `.specify/memory/constitution.md` (1 file updated)
- 🔁 Next prompts: Run `/sp.specify` to create feature spec for RAG chatbot backend; update 4 dependent templates (plan, spec, tasks, commands)
- 🧠 Reflection: Constitution now serves as authoritative governance doc for backend-only RAG system. Security-First elevation and Zero-Hallucination principles directly address product risks. Backend Architecture Rules provide clear structural guardrails for all future development.

## Evaluation notes (flywheel)

- Failure modes observed: None; shell script create-phr.sh not present (fallback to agent-native PHR creation used successfully)
- Graders run and results (PASS/FAIL): Manual validation PASS (no unresolved tokens, version coherent, governance complete)
- Prompt variant (if applicable): Standard constitution amendment workflow
- Next experiment: Update all dependent templates to align with new backend architecture and RAG requirements before next feature spec
