# Implementation Plan: RAG Frontend Integration (Spec 4)

**Branch**: `004-rag-frontend-integration` | **Date**: 2025-12-28 | **Spec**: [specs/004-rag-frontend-integration/spec.md](spec.md)
**Input**: Feature specification from `/specs/004-rag-frontend-integration/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Integrate FastAPI RAG backend with Docusaurus frontend to create an embedded chat widget for answering questions about the humanoid robotics textbook. The widget will send user queries to the backend, display responses with sources and confidence scores, and support selected-text queries. Implementation uses React for the frontend component and FastAPI for backend integration, with CORS enabled for GitHub Pages deployment.

**Key Architecture Decisions**:
- Single ChatWidget React component (floating or sidebar) for chat interface
- Fetch-based HTTP communication (no external dependencies)
- Real-time response display with loading indicators
- Selected-text detection using browser Selection API
- Configurable backend endpoint for local dev and production
- CORS-enabled FastAPI /chat endpoint for cross-origin requests

## Technical Context

**Language/Version**:
- Frontend: JavaScript/TypeScript 5.0+ (React 18.x in Docusaurus 3.x)
- Backend: Python 3.11+ (FastAPI 0.110+)

**Primary Dependencies**:
- Frontend: React 18, TypeScript, Docusaurus 3, CSS Modules
- Backend: FastAPI 0.110+, Qdrant client, OpenAI SDK, pydantic

**Storage**: Qdrant vector database (external service) - N/A for frontend

**Testing**:
- Frontend: Jest, React Testing Library
- Backend: pytest, FastAPI TestClient

**Target Platform**:
- Frontend: Web browsers (Chrome, Firefox, Safari, Edge) on desktop and mobile
- Backend: Linux servers (local dev, Railway/Heroku production)

**Project Type**: Web application (Frontend + Backend)

**Performance Goals**:
- Query response time: < 5 seconds (SC-009)
- Widget load time: < 2 seconds
- Backend call success rate: 95% (SC-001)

**Constraints**:
- No authentication required (hackathon demo)
- Free-tier compatible deployment
- CORS must allow GitHub Pages origin (https://mehreen676.github.io)
- Simple React component (Docusaurus default theme)
- Single /chat endpoint

**Scale/Scope**:
- Single embedded widget (not multi-page)
- Conversation history in memory (50 messages max)
- 6 user stories covering query, display, error handling, loading, selected-text, deployed site

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Validation

| Principle | Status | Notes |
|-----------|--------|-------|
| **Technical Accuracy** | ✅ PASS | Spec references FastAPI, Qdrant, OpenAI as per constitution |
| **Clarity for Audience** | ✅ PASS | Hackathon judges can understand without deep tech knowledge |
| **Reproducibility** | ✅ PASS | DEMO_SCRIPT.md, QUICKSTART.md, DEPLOYMENT_GUIDE.md provided |
| **Theory-Practice Integration** | ✅ PASS | RAG integration demonstrates vector search + LLM synthesis |
| **Standardized Citations** | ✅ PASS | Documentation references official APIs (OpenAI, Qdrant, FastAPI) |
| **Technology Stack Alignment** | ✅ PASS | Uses Docusaurus, FastAPI, Qdrant as required |
| **Spec-Driven Development** | ✅ PASS | Full spec.md completed before planning |

**Gate Result**: ✅ **PASS** - All principles satisfied. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-rag-frontend-integration/
├── spec.md              # Feature specification (COMPLETED)
├── plan.md              # This file (/sp.plan output)
├── research.md          # Phase 0 research findings (TO BE GENERATED)
├── data-model.md        # Phase 1 data entities (TO BE GENERATED)
├── quickstart.md        # Phase 1 developer guide (COMPLETED)
├── contracts/           # Phase 1 API contracts (TO BE GENERATED)
├── checklists/
│   └── requirements.md  # Spec quality checklist (PASS)
├── README.md            # Architecture overview (500+ lines)
├── DEMO_SCRIPT.md       # 6-minute demo guide
├── DEPLOYMENT_GUIDE.md  # Deployment instructions (2000+ lines)
└── tasks.md             # Phase 2 output (/sp.tasks - COMPLETED with 136 tasks)
```

### Source Code (Web Application - Frontend + Backend)

```text
frontend/ (Docusaurus React application)
├── src/
│   ├── components/
│   │   ├── ChatWidget.tsx          # Main chat interface component
│   │   ├── ChatInput.tsx            # User query input form
│   │   ├── ChatMessage.tsx          # Individual message display
│   │   ├── SourcesList.tsx          # Source attribution component
│   │   └── MatchedChunks.tsx        # Retrieved text snippets display
│   ├── hooks/
│   │   ├── useMessageHistory.ts     # Chat history state management
│   │   ├── useLoadingState.ts       # Loading progress tracking
│   │   └── useSelectedText.ts       # Text selection detection
│   ├── services/
│   │   ├── chatApi.ts              # HTTP client for backend
│   │   ├── errorHandler.ts         # Error processing and messages
│   │   ├── selectedText.ts         # Text extraction utilities
│   │   └── __mocks__/
│   │       └── chatApi.ts          # Mock for testing
│   ├── types/
│   │   └── chat.ts                 # TypeScript interfaces (Query, Response, Message)
│   ├── styles/
│   │   ├── ChatWidget.module.css
│   │   ├── ChatInput.module.css
│   │   ├── ChatMessage.module.css
│   │   ├── SourcesList.module.css
│   │   └── MatchedChunks.module.css
│   └── pages/
│       └── [chat page or floating widget integration]
└── tests/
    ├── unit/              # Component and hook tests
    ├── integration/       # End-to-end tests
    └── contract/         # API contract tests

backend/ (FastAPI application)
├── main.py              # Application entry point
├── app.py               # FastAPI app setup with CORS
├── chat_router.py       # POST /chat endpoint
├── agent.py             # RAG Agent integration (external)
├── models.py            # Pydantic request/response models
└── tests/
    ├── test_chat_api.py # Endpoint tests
    └── test_cors.py     # CORS configuration tests
```

**Structure Decision**: Web application with separate frontend (Docusaurus in React) and backend (FastAPI). Frontend is embedded as custom React component in Docusaurus; backend is deployed independently. This matches existing project layout where frontend/ contains Docusaurus app and backend/ contains FastAPI service.

## Complexity Tracking

> **No violations detected** - All constraints satisfied with simple architecture. Complexity justified below.

| Decision | Why Needed | Simpler Alternative Rejected Because |
|----------|-----------|---------------------------------------|
| Separate frontend/backend | Frontend deployed to GitHub Pages, backend to Railway/Heroku | Single process insufficient for different hosting requirements |
| React component architecture | Docusaurus is React-based; natural fit for component library | Direct JS would lose type safety and reusability benefits |
| Fetch API (no axios) | Lighter dependencies for embedded widget | HTTP library adds unnecessary complexity for simple endpoint |

---

## Phase 0: Outline & Research

**Goal**: Resolve unknowns and validate technology choices

### Research Tasks

Based on the architecture decisions provided, no critical unknowns remain. However, the following areas will be researched to ensure best practices:

1. **Browser Selection API for text extraction**
   - Compatibility across browsers (Chrome, Firefox, Safari, Edge)
   - Performance implications of selection listeners
   - Mobile device support for selected-text feature

2. **CORS configuration patterns**
   - Best practices for FastAPI CORS middleware
   - GitHub Pages origin configuration
   - Security considerations for public endpoints

3. **Real-time response handling**
   - Streaming responses vs. fetch completion
   - Loading state patterns in React
   - Network timeout handling

4. **TypeScript in Docusaurus**
   - Custom component compilation
   - Type safety with React 18
   - Testing strategy for components

### Research Deliverables

Create `research.md` documenting:
- Browser Selection API findings (Chrome 63+, Firefox 53+, Safari 11+, Edge 79+ all supported)
- CORS best practices (FastAPI documentation, GitHub Pages origin handling)
- Real-time patterns for RAG responses (streaming via fetch EventSource vs. standard response)
- TypeScript compilation in Docusaurus (works with tsconfig.json in src/)

**Output**: `specs/004-rag-frontend-integration/research.md`

---

## Phase 1: Design & Contracts

**Prerequisites**: Constitution Check PASS ✅, Research completed

### 1.1 Data Model

**Entity: Query Request**
- Fields: query (string, 3-5000 chars), selected_text (optional string), k (number, 1-20, default 5)
- Validation: Query length enforced by frontend, backend echoes validation

**Entity: RAG Response**
- Fields: response (string), sources (Source[]), confidence (0-1), execution_time_ms (number)
- Validation: All fields required from backend

**Entity: Source**
- Fields: url (string), snippet (string, first 200 chars), similarity_score (0-1), chunk_position (optional)

**Entity: ChatMessage**
- Fields: id (string), role ('user' | 'assistant'), content (string), timestamp (Date), sources?, confidence?, execution_time_ms?
- Relationships: Messages form conversation history (max 50)

**Output**: `specs/004-rag-frontend-integration/data-model.md`

### 1.2 API Contracts

**Endpoint: POST /chat**

Request:
```json
{
  "query": "What is humanoid robotics?",
  "selected_text": "optional context text",
  "k": 5
}
```

Response (200):
```json
{
  "response": "Generated answer from RAG agent",
  "sources": [
    {
      "url": "https://example.com/page",
      "snippet": "Relevant text chunk...",
      "similarity_score": 0.92
    }
  ],
  "confidence": 0.85,
  "execution_time_ms": 1234
}
```

Error Response (400, 500):
```json
{
  "detail": "Error message describing the issue"
}
```

**Output**: `specs/004-rag-frontend-integration/contracts/chat-api.json` (OpenAPI 3.0)

### 1.3 Developer Quickstart

Update `quickstart.md` to include:
- Dependency installation (frontend: npm, backend: pip)
- Environment configuration (.env files)
- Running backend with FastAPI (uvicorn)
- Running frontend with Docusaurus (npm start)
- Testing with curl/Postman
- Deployment steps (GitHub Pages, Railway/Heroku)

**Output**: `specs/004-rag-frontend-integration/quickstart.md` (already exists, reference in tasks)

### 1.4 Agent Context Update

Run update-agent-context script to add discovered technologies and patterns to agent memory.

---

## Phase 2: Task Breakdown (Next Step)

The following phase generates `tasks.md` via `/sp.tasks` command with:
- 7 implementation phases (Setup, Foundation, User Stories 1-6)
- 92 tasks total with prioritization (P1/P2)
- Dependency ordering and parallel execution markers
- Test-driven development approach

**Output**: `specs/004-rag-frontend-integration/tasks.md` (already generated)
