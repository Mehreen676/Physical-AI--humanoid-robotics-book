# Implementation Plan: RAG Frontend Integration

**Branch**: `004-rag-frontend-integration` | **Date**: 2025-12-28 | **Spec**: [specs/004-rag-frontend-integration/spec.md](spec.md)

**Input**: Feature specification from `/specs/004-rag-frontend-integration/spec.md`

## Summary

Integrate the existing FastAPI RAG Agent backend (from Spec 005) with the Docusaurus frontend to create an embedded chat widget that allows users to ask questions about the humanoid robotics textbook. The integration enables:

1. **Embedded Chat Widget** in Docusaurus (floating widget or sidebar)
2. **Backend API Communication** via FastAPI with CORS enabled
3. **Real-time Query Processing** using Qdrant vector search + Cohere embeddings
4. **Selected-Text Support** to query highlighted textbook content
5. **Deployed Site Functionality** on GitHub Pages with backend on accessible URL

The architecture is lightweight and hackathon-friendly: single React component, existing FastAPI backend, no authentication, free-tier compatible.

---

## Technical Context

**Language/Version**: TypeScript 4.9+ (React frontend), Python 3.11+ (FastAPI backend - existing)

**Primary Dependencies**:
- **Frontend**: React 18, Docusaurus 2 (default theme), axios or fetch API for HTTP
- **Backend**: FastAPI (existing from Spec 005), Cohere SDK, Qdrant Client, OpenAI SDK (optional)
- **Storage**: Qdrant vector database (existing from Specs 002-005)
- **Testing**: Jest/React Testing Library (frontend), pytest (backend - existing)

**Target Platform**: Web browsers (no mobile optimization), GitHub Pages (frontend), accessible URL for FastAPI backend

**Project Type**: Web application with separated frontend (Docusaurus) and backend (FastAPI)

**Performance Goals**:
- Chat query response: < 5 seconds (target, may exceed for complex queries)
- UI interaction response: < 500ms
- Widget load time: < 2 seconds on page load
- Chat interface instantiation: < 1 second

**Constraints**:
- No authentication required (hackathon demo)
- CORS must allow requests from `https://mehreen676.github.io` (and local dev origins)
- Simple React component (no heavy dependencies)
- Docusaurus default theme (minimal styling customization)
- Free-tier compatible (no paid services)
- Selected-text feature must work across all textbook pages

**Scale/Scope**:
- Single chat widget instance per page
- Support ~50 concurrent users during hackathon
- 100+ textbook pages with embedded widget

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md`:

### Code Quality & Architecture
- ✅ **Single responsibility**: Chat widget component focused on UI/UX only
- ✅ **Minimal dependencies**: Reuse existing FastAPI backend, no new services
- ✅ **Testable**: Each component (query submission, response display, error handling) independently testable
- ✅ **No premature optimization**: Straightforward React component, no caching layer added

### Integration Pattern
- ✅ **Standard REST API**: FastAPI endpoint with clear request/response schema
- ✅ **Error handling**: User-friendly messages, graceful degradation
- ✅ **CORS configuration**: Standard best practices, origin-restricted

### Security & Privacy
- ✅ **No secrets in code**: API keys in environment variables only
- ✅ **No authentication needed**: Intentional design choice for hackathon
- ✅ **Input validation**: Backend already validates queries (from Spec 005)
- ✅ **No data collection**: Queries not logged beyond debug purposes

### Documentation & Clarity
- ✅ **Clear API contract**: Documented in `/contracts/chat-api.json`
- ✅ **Component documentation**: JSDoc comments for all functions
- ✅ **Integration guide**: Included in `quickstart.md`

**Gate Status**: ✅ **PASS** - No violations. Architecture is sound and aligned with principles.

---

## Project Structure

### Documentation (this feature)

```text
specs/004-rag-frontend-integration/
├── spec.md                     # Feature specification
├── plan.md                     # This file (architecture & design)
├── research.md                 # Phase 0: Research findings (TBD)
├── data-model.md               # Phase 1: Data entities & contracts (TBD)
├── quickstart.md               # Phase 1: Integration guide (TBD)
├── contracts/
│   ├── chat-api.json          # Phase 1: OpenAPI schema
│   └── message-types.ts       # Phase 1: TypeScript interfaces
└── checklists/
    └── requirements.md        # Validation checklist (COMPLETED)
```

### Source Code (repository root)

```text
# Frontend (Docusaurus)
docs/                          # Textbook pages (existing)
└── [pages already have content]

src/                           # NEW: Frontend code (in Docusaurus src/)
├── components/
│   └── ChatWidget.tsx         # Main chat widget component
│   └── ChatMessage.tsx        # Individual message display
│   └── ChatInput.tsx          # Query input form
│   └── LoadingIndicator.tsx   # Loading state display
├── services/
│   └── chatApi.ts             # Backend API client
│   └── selectedText.ts        # Selected-text extraction utility
├── styles/
│   └── ChatWidget.module.css  # Widget styling
└── types/
    └── chat.ts                # TypeScript interfaces

tests/
├── components/
│   └── ChatWidget.test.tsx    # Widget integration tests
├── services/
│   └── chatApi.test.ts        # API client tests
└── integration/
    └── end-to-end.test.ts     # E2E tests on live URL

# Backend (FastAPI - Existing, Enhanced)
backend/
├── main.py                    # FastAPI app (existing from Spec 005)
├── agent.py                   # RAG agent with synthesis (Spec 005 Phase 6)
├── chat_router.py             # NEW: Chat API endpoint
└── [existing files from Specs 002-005]
```

**Structure Decision**: Web application with separated concerns - Docusaurus/React frontend handles UI/UX, FastAPI backend handles RAG processing. This separation allows independent deployment and evolution.

---

## Architecture Overview

### High-Level Integration Flow

```
┌─────────────────────────────────────┐
│  Docusaurus Frontend (GitHub Pages) │
│                                     │
│  1. User highlights text or types   │
│  2. ChatWidget component processes  │
│  3. Sends query via HTTP to backend │
│                                     │
└────────────┬────────────────────────┘
             │ HTTP POST /chat
             │ { query, selected_text }
             ↓
┌─────────────────────────────────────┐
│  FastAPI Backend (Deployed URL)     │
│                                     │
│  1. Receive query from frontend     │
│  2. Pass to Agent (Spec 005)        │
│  3. Agent retrieves from Qdrant     │
│  4. Agent returns synthesized resp  │
│  5. Return JSON response to frontend│
│                                     │
└────────────┬────────────────────────┘
             │ HTTP 200 { response, sources, confidence }
             ↓
┌─────────────────────────────────────┐
│  Frontend Display                   │
│                                     │
│  1. Parse response JSON             │
│  2. Render answer with sources      │
│  3. Show confidence score           │
│  4. Display matched chunks          │
│                                     │
└─────────────────────────────────────┘
```

### Component Architecture

**Frontend Components**:
- **ChatWidget.tsx** (parent): Manages state, handles API calls, orchestrates layout
- **ChatMessage.tsx**: Renders individual messages (user query, assistant response)
- **ChatInput.tsx**: Input form for new queries, supports pre-filling from selected text
- **LoadingIndicator.tsx**: Shows progress during API requests
- **Selected-Text Service**: Extracts highlighted text, provides to ChatInput

**Backend Endpoints**:
- **POST /chat**: Accept query, return response
  - Request: `{ query: string, selected_text?: string, k?: number }`
  - Response: `{ query, response, sources, confidence, execution_time_ms, status }`
- Uses existing `run_query()` from agent.py (Spec 005)

### Data Flow

1. **User Action**: Highlight text in book OR type in chat input
2. **Frontend Processing**:
   - Extract selected text (if any)
   - Combine with user-typed query
   - Show loading indicator
3. **API Call**: POST to `/chat` endpoint with structured request
4. **Backend Processing**:
   - Receive query from frontend
   - Pass to `agent.run_query()` (existing, from Spec 005)
   - Get back: response text + sources + confidence
   - Return JSON response
5. **Frontend Display**:
   - Parse response
   - Render message with sources
   - Hide loading indicator
   - Scroll to latest message

### Error Handling

**Frontend Error Cases**:
- Network error (timeout, no connection) → "Unable to connect to backend. Please try again."
- API error (4xx, 5xx) → Display backend error message or generic "An error occurred"
- Malformed response → "Unexpected response format. Please try again."
- Empty result → "No relevant content found in the textbook for your query."

**Backend Error Cases** (handled by existing agent.py):
- Cohere API rate limit → Exponential backoff, retry
- Qdrant connection error → Return error response to frontend
- Invalid query → Return validation error message

### CORS Configuration

**FastAPI Backend** must configure CORS to allow:
- **Origin**: `https://mehreen676.github.io` (production)
- **Origin**: `http://localhost:3000`, `http://localhost:8000` (development)
- **Methods**: GET, POST, OPTIONS
- **Headers**: Content-Type, Authorization (optional)
- **Credentials**: False (no authentication)

---

## Key Design Decisions

### 1. Single Chat Widget Component
**Decision**: One React component handles all chat UI
- **Rationale**: Simplicity, easy to embed in any Docusaurus page, minimal dependency footprint
- **Alternatives**: Complex chat library (react-chat-ui, Rasa), full chat application
- **Impact**: Faster development, easier testing, lighter build

### 2. Backend API: Single `/chat` Endpoint
**Decision**: One POST endpoint handles all query processing
- **Rationale**: Clear separation of concerns, easy to understand, aligns with existing agent.py
- **Alternatives**: Multiple endpoints (/query, /synthesis, /retrieved-chunks)
- **Impact**: Simpler deployment, easier CORS configuration, all logic in one place

### 3. Selected-Text Support via Context Parameter
**Decision**: Pass `selected_text` as optional parameter to backend
- **Rationale**: Backend (Spec 005) already supports query encoding, can incorporate context
- **Alternatives**: Modify query string to include selected text
- **Impact**: Cleaner API, better for future multi-turn conversations

### 4. No Authentication / No User Sessions
**Decision**: Hackathon demo without auth
- **Rationale**: Fastest to implement, judges don't need to log in
- **Alternatives**: OAuth2, JWT tokens, API keys
- **Impact**: Reduces complexity, enables anonymous queries, works on GitHub Pages

### 5. Floating Widget as Default
**Decision**: Floating chat widget (not full-page chat)
- **Rationale**: Less intrusive, works on all pages without redesign
- **Alternatives**: Full-page chat route, embedded in sidebar
- **Impact**: Easier integration, better UX for judges, widget-like affordance

### 6. Docusaurus Theme Integration
**Decision**: Use Docusaurus default theme, minimal custom styling
- **Rationale**: No theme customization needed, works out-of-box
- **Alternatives**: Custom theme, Tailwind CSS styling
- **Impact**: Faster implementation, consistent with book design

---

## Phase 0: Research (To Be Completed)

Research tasks to resolve during implementation:

1. **React/TypeScript setup in Docusaurus** - How to add custom components to Docusaurus default theme
2. **Selected-text extraction** - Best practices for capturing highlighted text across different browsers
3. **CORS configuration in FastAPI** - Specific configuration for production origin
4. **HTTP client choice** - Fetch API vs. axios for simple requests (recommend: Fetch API - no dependency)
5. **Error handling patterns** - Best practices for network errors in React apps
6. **Keyboard shortcuts** - Should chat widget support keyboard access? (Ctrl+K to focus input?)

**Output**: `research.md` with findings and decisions

---

## Phase 1: Design & Contracts (To Be Completed)

### 1.1 Data Model
**File**: `data-model.md`

**Entities**:
- **ChatMessage**: `{ id, role (user|assistant), content, timestamp, sources?, confidence? }`
- **QueryRequest**: `{ query, selected_text?, k }`
- **QueryResponse**: `{ query, response, sources, confidence, execution_time_ms, status }`

### 1.2 API Contracts
**File**: `contracts/chat-api.json` (OpenAPI schema)

**Endpoint**: `POST /chat`
- **Request Body**:
  ```json
  {
    "query": "What is humanoid robotics?",
    "selected_text": "optional highlighted text",
    "k": 5
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "query": "What is humanoid robotics?",
    "response": "Based on the textbook, here's what I found:\n...",
    "sources": [
      {
        "url": "https://example.com/intro",
        "snippet": "Welcome to the Physical AI & Humanoid Robotics textbook..."
      }
    ],
    "confidence": 0.578,
    "execution_time_ms": 4500,
    "status": "success"
  }
  ```

### 1.3 TypeScript Interfaces
**File**: `contracts/message-types.ts`

```typescript
interface QueryRequest {
  query: string;
  selected_text?: string;
  k?: number;
}

interface Source {
  url: string;
  snippet: string;
}

interface QueryResponse {
  query: string;
  response: string;
  sources: Source[];
  confidence: number;
  execution_time_ms: number;
  status: "success" | "error" | "no_results";
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: Source[];
  confidence?: number;
}
```

### 1.4 Component Interface
**File**: `quickstart.md`

**Integration Steps**:
1. Copy `ChatWidget.tsx` to Docusaurus `src/components/`
2. Import widget in desired pages: `<ChatWidget backendUrl="..." />`
3. Configure backend URL in environment: `REACT_APP_BACKEND_URL`
4. Enable CORS on FastAPI backend
5. Test on local dev, then deploy to GitHub Pages

---

## Phase 2: Implementation (Tasks to Be Defined)

Tasks will be generated by `/sp.tasks` command after plan approval. Expected task groups:

1. **Frontend Setup** (4-5 tasks)
   - Setup TypeScript environment in Docusaurus
   - Create ChatWidget component
   - Create message display components
   - Implement selected-text extraction

2. **API Integration** (3-4 tasks)
   - Create chatApi service (HTTP client)
   - Implement request/response handling
   - Add error handling and retry logic
   - Test API contract

3. **Backend Enhancement** (2-3 tasks)
   - Add `/chat` endpoint to FastAPI
   - Integrate with agent.py
   - Configure CORS for frontend origin
   - Test backend endpoint

4. **Testing & Deployment** (3-4 tasks)
   - Unit tests for components
   - Integration tests for API calls
   - E2E tests on live site
   - Deploy frontend to GitHub Pages, backend to accessible URL

5. **Demo & Documentation** (2-3 tasks)
   - Prepare demo queries
   - Create usage guide
   - Document integration steps

---

## Assumptions & Decisions Documented

1. **FastAPI backend available**: Spec 005 provides complete RAG Agent with Qdrant + Cohere + OpenAI
2. **GitHub Pages deployment**: Docusaurus frontend already deployed to GitHub Pages
3. **Backend URL provided**: Backend (FastAPI) deployed to accessible URL with CORS enabled
4. **No user database**: Queries not stored; stateless API
5. **Selected text is optional**: Query can be submitted with or without highlighted text context
6. **Floating widget is default**: Can be adapted to sidebar or full-page later
7. **Real-time display** (not streaming): Response displayed as complete message, not streamed tokens

---

## Dependencies & Integration Points

### Frontend Dependencies
- **Docusaurus 2**: Already deployed, provides default theme
- **React 18**: Bundled with Docusaurus
- **TypeScript**: Docusaurus supports out-of-box
- **Fetch API**: Built-in, no npm package needed

### Backend Dependencies
- **FastAPI**: Existing from Spec 005
- **Cohere SDK**: Existing from Spec 005
- **Qdrant Client**: Existing from Spec 005
- **OpenAI SDK**: Optional, used in Spec 005 Phase 6

### External Services
- **Cohere API**: Query embeddings (existing key)
- **Qdrant Cloud**: Vector database (existing collection)
- **OpenAI API**: Optional response synthesis (existing key from Phase 6)

---

## Success Metrics

From spec.md, integration is successful when:

1. ✅ Frontend (Docusaurus) connects to FastAPI backend (100% connection success)
2. ✅ Chat interface loads in < 2 seconds
3. ✅ Query processing completes in < 5 seconds (end-to-end)
4. ✅ Sources displayed with responses (100% of responses show sources)
5. ✅ Selected-text queries work (highlight → ask → correct answer)
6. ✅ Works on deployed GitHub Pages site
7. ✅ Error messages user-friendly (no stack traces)
8. ✅ CORS properly configured (requests from deployed origin accepted)
9. ✅ Hackathon demo ready (judges can test without setup)
10. ✅ No authentication required (open access)

---

## Next Phase

After phase 1 design approval, `/sp.tasks` will generate detailed task breakdown for:
- Frontend component implementation (React/TypeScript)
- Backend endpoint integration (FastAPI)
- Testing & deployment workflows
- Demo preparation

**Estimated scope**: 15-20 implementation tasks, 2-3 weeks for full feature

---

**Branch**: `004-rag-frontend-integration`
**Plan Status**: Ready for Phase 0 research and Phase 1 design
**Created**: 2025-12-28
**Next Command**: `/sp.tasks 004-rag-frontend-integration` (after Phase 1 approval)