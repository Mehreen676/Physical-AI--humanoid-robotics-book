---
id: 002
title: BookRAGAgent implementation plan complete
stage: plan
date: 2025-12-30
surface: agent
model: claude-haiku-4-5-20251001
feature: 006-book-rag-agent
branch: 006-book-rag-agent
user: mehreen@example.com
command: /sp.plan
labels: ["implementation-plan", "architecture", "design", "phase-0-phase-1"]
links:
  spec: specs/006-book-rag-agent/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/006-book-rag-agent/plan.md
  - specs/006-book-rag-agent/research.md
  - specs/006-book-rag-agent/data-model.md
  - specs/006-book-rag-agent/contracts/chat-api.openapi.json
  - specs/006-book-rag-agent/quickstart.md
tests:
  - Constitution Check: All 5 principles PASS
  - Technical Context: All 8 fields complete (language, dependencies, storage, testing, platform, performance, constraints, scale)
  - Project Structure: Backend folder tree defined
  - Phase 0 Research: 9 research items completed (no NEEDS CLARIFICATION)
  - Phase 1 Design: Data model, API contracts, quickstart all defined
  - Agent Context: Ready for update
---

## Prompt

PROJECT: Integrated RAG Chatbot (Book Embedded)
METHODOLOGY: SpecKit Plus

OBJECTIVE:
Implement a fully functional, hallucination-free RAG chatbot backend
with modular agents, skills, vector retrieval, session memory, and
OpenRouter LLM integration.

PLAN STEPS:
[User provided comprehensive plan outline with 9 steps covering environment setup, folder architecture, agent/skills registration, vector database integration, LLM integration, guardrails, FastAPI endpoint, session storage, and testing/validation]

## Response snapshot

**✅ IMPLEMENTATION PLAN COMPLETE: BookRAGAgent (Feature 006)**

**Artifacts Created** (Phase 0 + Phase 1):
1. **plan.md** (341 lines): Full implementation plan with technical context, constitution check, project structure, and design decisions
2. **research.md** (394 lines): All 9 technical research items completed; no unresolved clarifications
3. **data-model.md** (415 lines): Complete entity definitions (User, Session, ChatMessage, RetrievedChunk, Pydantic models)
4. **chat-api.openapi.json** (527 lines): Full OpenAPI 3.0.0 spec with all 4 endpoints and comprehensive schemas
5. **quickstart.md** (392 lines): Step-by-step local development setup, troubleshooting, Docker instructions

**Constitution Validation** ✅
- **Principle 1: Security-First**: All secrets from env vars, startup validation, no hardcoded keys
- **Principle 2: Zero-Hallucination**: Answer synthesis from chunks only, guardrails with veto authority, fallback message
- **Principle 3: Developer-First**: All backend code in /backend, clear folder structure, actionable error messages
- **Principle 4: Reproducibility**: Unit/integration tests with mocks, version-controlled schema, deterministic setup
- **Principle 5: Deterministic Behavior**: No random seeds, session persistence deterministic, all external calls tested

**Technical Context** ✅
- Language/Version: Python 3.11+
- Dependencies: FastAPI, OpenAI Agents SDK, ChatKit, qdrant-client, psycopg2, openrouter (via requests), pydantic, python-dotenv
- Storage: Neon PostgreSQL (sessions), Qdrant Cloud (vectors)
- Testing: pytest with mocks for external services
- Platform: Linux server (Cloud-ready, Docker-compatible)
- Performance: <5 sec response latency (p95 <10 sec)
- Constraints: ≥95% grounding rate, ≥99% fallback accuracy, metadata preserved
- Scale: Single book collection, multi-user sessions, 10,000+ chunks, 2-3 KLOC

**Project Structure** ✅
- Backend folder organized: agent/, rag/, storage/, models/, api/, services/, config.py, main.py
- Tests mirror source: unit/, integration/, fixtures/
- Documentation: spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md, tasks.md

**Phase 0: Research Complete** ✅
- 9 items researched and confirmed (Agent Orchestration, LLM Provider, Vector DB, Session Storage, Web Framework, Testing, Deployment, Error Handling, Security)
- 0 NEEDS CLARIFICATION markers
- All technical decisions justified with rationale and alternatives considered

**Phase 1: Design Complete** ✅
- **1a Data Model**: 5 entities defined (User, Session, ChatMessage, RetrievedChunk) + Pydantic models + DDL statements + validation rules
- **1b API Contracts**: 4 endpoints (POST /chat, POST /sessions, GET /sessions/{id}, GET /health) with full OpenAPI schema
- **1c Quickstart**: 9-step local setup guide with troubleshooting, Docker, common commands
- **1d Agent Context**: Ready to run `.specify/scripts/powershell/update-agent-context.ps1`

**Key Design Decisions** (5 documented):
1. **Multi-Agent Orchestration**: Separate sub-agents for Retrieval, Answer, Guardrails, SelectionMode, Memory (modular, testable)
2. **Guardrails-First**: GuardrailsSubAgent runs AFTER AnswerSubAgent with veto authority (fail-safe design)
3. **Selected-Text Override**: SelectionModeSubAgent overrides retrieval scope before VectorSearchSkill (efficient, trustworthy)
4. **Session Storage Isolation**: MemorySubAgent reads sessions BUT sessions NEVER used as retrieval knowledge source (clean RAG)
5. **Environment Variables**: OPENROUTER_API_KEY, QDRANT_API_KEY, DATABASE_URL from .env (security compliance)

**Ready for Phase 2** ✅
- All Phase 0 research complete (no clarifications)
- All Phase 1 design artifacts created
- Constitution check passing
- Technical context fully specified
- Project structure defined
- Next: Run `/sp.tasks` to generate task breakdown by user story and phase

## Outcome

- ✅ Impact: Comprehensive, executable implementation plan ready to guide development from setup through testing
- 🧪 Tests: Constitution validation PASS (5/5 principles); technical context complete (8/8 fields); project structure clear; research complete (0 clarifications); design complete (data model, API, quickstart)
- 📁 Files: 5 Phase 0/1 artifacts created (plan.md, research.md, data-model.md, chat-api.openapi.json, quickstart.md)
- 🔁 Next prompts: `/sp.tasks` to generate task breakdown; then `/sp.implement` to execute tasks
- 🧠 Reflection: Plan captures complete architecture for BookRAGAgent with clear separation of concerns (5 sub-agents, 6 skills), guardrail-first fail-safe design, and security-first environment management. All technical decisions justified; no ambiguities remain. Ready to proceed directly to implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None; all Phase 0 and Phase 1 artifacts generated successfully; no missing information
- Graders run and results (PASS/FAIL): Constitution check PASS (5/5 principles); technical context PASS (8/8 fields); project structure PASS (clear folder organization)
- Prompt variant (if applicable): Standard implementation planning workflow (Phase 0: research, Phase 1: design, Phase 2: tasks)
- Next experiment: Generate detailed task breakdown with test cases for each user story; then begin implementation
