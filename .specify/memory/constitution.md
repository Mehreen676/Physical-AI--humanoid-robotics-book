<!-- SYNC IMPACT REPORT
Version change: 1.0.0 -> 2.0.0 (MAJOR)
Rationale: Project refocused from "Physical AI textbook" to "RAG chatbot backend system". Redefined architecture principles (book-centric → backend/API-centric), changed tech stack (OpenRouter instead of OpenAI, Cohere embeddings, ChatKit SDK), elevated security-first to primary principle.
Modified principles:
  - Added: Security-First Foundation (new primary principle)
  - Renamed: "Technical Accuracy" → "Zero-Hallucination Grounding" (RAG-specific)
  - Renamed: "Clarity for Target Audience" → "Developer-First Implementation" (backend focus)
  - Removed: "Standardized Citations" (not applicable to RAG agent)
  - Removed: robotics-specific context (ROS 2, Gazebo, Isaac, VLA)
Added sections:
  - Backend Architecture Rules (folder structure, /backend mandatory)
  - API Security & Environment Management
  - RAG-Specific Requirements (book-only answers, selected-text mode, metadata preservation)
Removed sections:
  - Theory-Practice Integration (robotics-centric)
  - Content format/Docusaurus references
  - Citation format standards
Templates requiring updates:
  - .specify/templates/plan-template.md (backend/agent paths, environment vars)
  - .specify/templates/spec-template.md (RAG-specific user stories, security reqs)
  - .specify/templates/tasks-template.md (backend structure, .env handling)
  - .specify/templates/commands/*.md (backend path conventions)
Follow-up TODOs: Update all 4 templates to reflect backend-only architecture and RAG requirements
-->

# Integrated RAG Chatbot Backend — Spec-Driven Development Constitution

## Core Principles

### 1. Security-First Foundation
All development MUST prioritize security from the start. Secrets (API keys, tokens, credentials) MUST be read exclusively from environment variables defined in `.env` files, never hardcoded. No secrets shall be logged or echoed in responses. Environment variable names MUST use clear, descriptive placeholders (e.g., `OPENROUTER_API_KEY`, `QDRANT_API_KEY`). Every external service integration MUST validate credentials at application startup.

**Rationale**: Backend API systems are security perimeters. Hardcoded secrets represent unacceptable risk.

### 2. Zero-Hallucination Grounding
The RAG system MUST answer user questions exclusively from book content. When a question cannot be answered from the provided text, the system MUST gracefully decline and surface the limitation. All responses MUST be traceable to source chunks (preserve chunk IDs, URLs, section metadata). No inferred, synthesized, or external knowledge is permitted in answer generation.

**Rationale**: The product promise is "answers from this book only." Hallucinations destroy user trust.

### 3. Developer-First Implementation
Code and systems MUST be designed for clarity and debuggability by backend engineers. File and folder organization MUST follow strict conventions: all backend code in `/backend`, each logical unit in its own folder, configuration management via environment variables. Error messages MUST be actionable and include context. Logging MUST capture both user interactions and system state for production support.

**Rationale**: Maintainable code reduces bugs and accelerates feature delivery.

### 4. Reproducibility and Testability
All code MUST be executable and testable in isolation. Database schemas, API contracts, and environment configurations MUST be version-controlled and documented. Every code change MUST include appropriate unit and integration tests. Setup instructions MUST be clear and deterministic.

**Rationale**: Production reliability depends on code that can be tested, deployed, and debugged repeatably.

### 5. Deterministic Behavior
The system MUST be debuggable. Non-determinism (random seeds, timing dependencies, flaky tests) MUST be minimized. All external service calls (LLM, vector DB, chat storage) MUST be explicitly tested with mocks or fixtures. Errors MUST be captured and logged with sufficient detail for investigation.

**Rationale**: Debugging production systems requires predictable, auditable behavior.

## Backend Architecture Rules

### Mandatory Structure
- **All backend code**: `/backend` directory (no exceptions)
- **Logical units**: Each service/component in its own folder (e.g., `/backend/agent`, `/backend/rag`, `/backend/storage`)
- **Python files only**: All code files MUST be `.py`
- **Agent implementation**: `/backend/agent/agent.py` is the entry point for agent orchestration logic
- **Configuration**: All settings loaded from `.env` via environment variables
- **No frontend code**: This repository contains backend-only implementation unless explicitly requested

### Folder Organization Template
```
/backend
├── agent/
│   ├── __init__.py
│   └── agent.py          # OpenAI Agents SDK + ChatKit orchestration
├── rag/
│   ├── __init__.py
│   ├── retrieval.py      # Qdrant vector DB queries
│   └── grounding.py      # Zero-hallucination validation
├── storage/
│   ├── __init__.py
│   └── sessions.py       # Neon PostgreSQL chat sessions
├── models/
│   ├── __init__.py
│   └── schemas.py        # Pydantic models for API contracts
├── api/
│   ├── __init__.py
│   └── routes.py         # FastAPI endpoints
├── services/
│   ├── __init__.py
│   └── embeddings.py     # Cohere or compatible embeddings service
├── main.py               # FastAPI application entry point
├── config.py             # Environment variable loading
└── pyproject.toml        # Python dependencies (uv or pip)

/tests
├── unit/                 # Unit tests for services
├── integration/          # Integration tests with mocked external services
└── contract/             # API contract tests
```

## RAG-Specific Requirements

### Answer Grounding
- Answers MUST cite source chunks with metadata: chunk ID, book section/URL, original text excerpt
- Selected-text mode: When user enables "answer only from this passage," the system MUST restrict retrieval to that passage only
- Fallback response: If no relevant chunks found, respond with "I couldn't find an answer to that question in the book" + suggestion to rephrase
- Never apologize or explain limitations; state facts clearly

### Metadata Preservation
- Every vector chunk ingested from the book MUST include: source URL, section name, chunk sequence ID, original text hash
- Metadata MUST be queryable and returned with every RAG response
- Version tracking: If book content updates, old chunks MUST be invalidated, new chunks ingested, version MUST be tracked

### Chat Session Management
- User sessions stored in Neon PostgreSQL with: user_id, session_id, timestamp, message history, metadata
- Sessions MUST support conversation context (recent N messages) for multi-turn RAG
- Sessions MUST be queryable by user and date for analytics/debugging

## API Security & Environment Management

### Environment Variables (Mandatory)
All external service credentials MUST be defined as environment variables:
```
OPENROUTER_API_KEY=<your-key>
QDRANT_API_KEY=<your-key>
QDRANT_URL=https://your-instance.qdrant.io
NEON_DATABASE_URL=postgresql://user:pass@host/dbname
COHERE_API_KEY=<your-key>          # if using Cohere embeddings
OPENAI_API_KEY=<optional-for-sdk>  # if using OpenAI SDK (typically not for OpenRouter)
```

### No Hardcoded Secrets
- Hardcoding any credential in code is a security violation and MUST be caught in code review
- `.env` files MUST be in `.gitignore`
- `.env.example` (with placeholder values) MUST be version-controlled for team reference

### Startup Validation
- Application MUST fail loudly if required environment variables are missing
- Error message format: `Missing required environment variable: <VAR_NAME>`
- Never log the actual secret value

## Development Workflow

The project follows Spec-Driven Development (SDD) methodology:
- All implementations MUST reference the specification (in `/specs/<feature-name>/spec.md`)
- Changes to specifications require formal update (via `/sp.specify` command)
- All code changes MUST include appropriate unit and integration tests
- All significant architectural decisions MUST be documented in Architecture Decision Records (`/history/adr/`)
- Prompt History Records MUST be created for all development sessions (`/history/prompts/`)

## Governance

This constitution establishes the foundational principles governing the Integrated RAG Chatbot Backend project. All development activities, code changes, and architectural decisions MUST comply with these principles.

**Amendment Procedure:**
1. Proposed amendment MUST be documented in a GitHub issue with clear rationale
2. Amendment MUST include version bump rationale (MAJOR/MINOR/PATCH per semantic versioning)
3. Changes MUST be reviewed and approved before merging to `main`
4. Once merged, affected artifacts (specs, plans, tasks, templates) MUST be updated within 1 sprint

**Compliance Verification:**
- All PRs MUST include a checklist confirming adherence to core principles
- Architecture reviews MUST explicitly test against Security-First, Zero-Hallucination, and Reproducibility principles
- Quarterly compliance audits MUST be conducted on production code and deployment procedures

**Version**: 2.0.0 | **Ratified**: 2025-12-13 | **Last Amended**: 2025-12-30
