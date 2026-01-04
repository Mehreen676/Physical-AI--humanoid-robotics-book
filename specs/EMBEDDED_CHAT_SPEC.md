# Embedded Chat Interface - Specification

## Overview

**Target Audience**: Hackathon judges and frontend/backend engineers evaluating end-to-end integration of the RAG chatbot within a published book.

**Focus**: Embed the completed agentic RAG chatbot directly into the Docusaurus-based book, enabling readers to ask questions about the full book or selected text without leaving the documentation site.

---

## Success Criteria

- [x] Chatbot accessible from all book pages
- [x] Users can ask questions about the entire book
- [x] Users can select text and ask questions scoped to selection
- [x] Chat UI communicates successfully with FastAPI backend
- [x] No API keys or secrets exposed to frontend
- [x] Chatbot works on deployed GitHub Pages site

---

## Constraints

| Constraint | Value | Notes |
|------------|-------|-------|
| Frontend Framework | Docusaurus (React) | Existing book framework |
| Backend | FastAPI RAG service | Already implemented (backend_v3) |
| Deployment | GitHub Pages (book) + Cloud (backend) | Separate deployments |
| Network Communication | Read-only (frontend → backend) | No client-side processing |
| Security | No secrets in frontend | Backend URL only |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EMBEDDED CHAT FLOW                        │
└─────────────────────────────────────────────────────────────┘

Book Page (Docusaurus)
    ↓
┌─────────────────────┐
│  Chat Widget        │  React Component
│  (ChatWidget.tsx)   │  - Floating button
│  - Toggle open/close│  - Chat interface
│  - Input field      │  - Message display
│  - Send button      │  - Loading states
└─────────────────────┘
    │
    │ User types question
    │ (Optional: selects text first)
    │
    ▼
┌─────────────────────┐
│  API Client         │  Fetch API
│  (apiClient.ts)     │  - POST /chat
└─────────────────────┘  - Error handling
    │
    │ HTTPS Request
    │ {question, selected_text, session_id}
    │
    ▼
┌─────────────────────┐
│  FastAPI Backend    │  Deployed on Railway/Render
│  (backend_v3)       │  - Agentic RAG
└─────────────────────┘  - OpenAI ChatKit
    │                    - Strict grounding
    ▼
  Response
  {answer, citations, grounded}
    │
    ▼
┌─────────────────────┐
│  Chat Widget        │  Display answer
│  - Format markdown  │  - Show citations
│  - Display sources  │  - Error states
└─────────────────────┘
```

---

## Component Architecture

```
src/components/ChatWidget/
├── ChatWidget.tsx           Main chat component
├── ChatButton.tsx           Floating chat button
├── ChatPanel.tsx            Chat interface panel
├── MessageList.tsx          Message history display
├── MessageInput.tsx         Input field + send
├── SelectedTextBadge.tsx    Shows selected text
├── CitationList.tsx         Source citations
├── LoadingIndicator.tsx     Loading state
├── ErrorMessage.tsx         Error display
└── types.ts                 TypeScript types

src/services/
└── apiClient.ts             Backend API client

src/config/
└── environment.ts           Backend URL config
```

---

## Functional Requirements

### 1. Chat Widget Visibility
- Floating button in bottom-right corner
- Available on all book pages
- Toggle open/close state
- Minimize to button when closed
- Persist open/close state in sessionStorage

### 2. User Input Handling
- Text input field for questions
- Enter key to send (Shift+Enter for newline)
- Send button
- Clear input after send
- Disable input while loading
- Max length: 1000 characters

### 3. Selected Text Detection
- Detect when user selects text on page
- Show selected text in chat UI
- Include "Ask about this" prompt
- Send selected text with question
- Clear selection after send
- Limit selected text: 2000 characters

### 4. Backend Communication
- POST request to `/api/v1/chat`
- Include: question, selected_text, session_id
- Handle CORS properly
- Retry on network errors (1 attempt)
- Timeout after 10 seconds
- Graceful error handling

### 5. Response Display
- Show user message immediately
- Show loading indicator for agent response
- Display agent answer with markdown support
- Show citations as expandable list
- Indicate if answer is a refusal
- Show grounding status (grounded: true/false)

### 6. Session Management
- Generate session_id on first interaction
- Store session_id in sessionStorage
- Include session_id in all requests
- Maintain conversation history in UI
- Clear session on page refresh (optional)

### 7. State Management
- Loading state (waiting for response)
- Error state (network/backend error)
- Empty state (no messages yet)
- Disabled state (backend unavailable)

---

## Non-Functional Requirements

### 1. Performance
- Widget bundle size <50KB (gzipped)
- Initial render <100ms
- No impact on page load time
- Lazy load if possible
- Minimize re-renders

### 2. Responsive Design
- Desktop: 400px width panel
- Mobile: Full-width overlay
- Breakpoint: 768px
- Touch-friendly buttons (min 44px)
- Readable text on all screens

### 3. Accessibility
- Keyboard navigation support
- ARIA labels for screen readers
- Focus management
- Contrast ratio ≥4.5:1
- Skip to chat button

### 4. Error Handling
- Network errors: "Unable to connect to chatbot"
- Backend errors: "Something went wrong"
- Timeout: "Request timed out"
- Invalid input: "Please enter a question"
- Display retry button

### 5. Security
- **No API keys in frontend code**
- Backend URL in environment variable
- HTTPS only for production
- Sanitize user input
- Escape markdown output
- CORS headers on backend

---

## NOT Building

- ❌ User authentication or accounts
- ❌ Advanced UI theming or animations
- ❌ Client-side vector search or embeddings
- ❌ Analytics, tracking, or personalization
- ❌ Multi-language support (English only)
- ❌ Voice input or speech-to-text
- ❌ File uploads or attachments
- ❌ Conversation export/download

---

## Deliverables

### 1. React Chat Widget
**File**: `src/components/ChatWidget/ChatWidget.tsx`

**Features**:
- Floating chat button
- Expandable chat panel
- Message input and display
- Selected text handling
- Backend API integration

### 2. API Client
**File**: `src/services/apiClient.ts`

**Features**:
- POST /chat endpoint
- Error handling
- Timeout management
- Type-safe responses

### 3. Environment Configuration
**File**: `docusaurus.config.js` (updated)

**Configuration**:
```javascript
customFields: {
  chatbotBackendUrl: process.env.CHATBOT_BACKEND_URL || 'http://localhost:8000'
}
```

### 4. Integration Instructions
**File**: `CHAT_WIDGET_INTEGRATION.md`

**Contents**:
- Installation steps
- Docusaurus integration
- Environment setup
- Testing guide
- Deployment checklist

### 5. Documentation
**File**: `CHAT_WIDGET_USAGE.md`

**Contents**:
- User guide (how to use chat)
- Full-book questions
- Selected-text questions
- Citation interpretation
- Troubleshooting

---

## Completion Criteria

### Chat Widget Functionality ✅
1. Widget appears on all book pages
2. Floating button toggles chat panel
3. User can type and send questions
4. Selected text is detected and sent
5. Responses display correctly
6. Citations are shown
7. Loading and error states work

### Backend Integration ✅
1. API client sends correct request format
2. CORS headers configured on backend
3. Responses parsed correctly
4. Session continuity works
5. Error handling graceful

### Security ✅
1. No API keys in frontend code
2. Backend URL from environment variable
3. HTTPS in production
4. Input sanitization
5. Output escaping

### Deployment ✅
1. Widget works on GitHub Pages
2. Backend accessible from deployed site
3. CORS allows GitHub Pages origin
4. No console errors
5. Performance acceptable

---

## Technical Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| UI Framework | React (via Docusaurus) | Existing |
| Styling | CSS Modules / Styled Components | Lightweight |
| State Management | React hooks (useState, useEffect) | No Redux needed |
| API Client | Fetch API | Native browser API |
| TypeScript | Yes | Type safety |
| Build Tool | Docusaurus (Webpack) | Existing |

---

## Environment Variables

### Frontend (Docusaurus)
```bash
# .env
CHATBOT_BACKEND_URL=https://your-backend.railway.app

# Production
CHATBOT_BACKEND_URL=https://your-backend.railway.app
```

### Backend (FastAPI)
```bash
# Update CORS_ORIGINS to allow GitHub Pages
CORS_ORIGINS=https://yourusername.github.io,http://localhost:3000
```

---

## Implementation Phases

### Phase 1: UI Components (60 min)
- Create ChatButton component (floating button)
- Create ChatPanel component (chat interface)
- Create MessageList component (message display)
- Create MessageInput component (input field)
- Create basic styling (responsive)

### Phase 2: Selected Text Detection (30 min)
- Implement text selection listener
- Create SelectedTextBadge component
- Handle selection clear
- Test selection edge cases

### Phase 3: Backend Integration (45 min)
- Create apiClient.ts
- Implement POST /chat
- Add error handling
- Add timeout logic
- Test with real backend

### Phase 4: State Management (30 min)
- Session ID generation
- Message history state
- Loading state
- Error state
- SessionStorage persistence

### Phase 5: Docusaurus Integration (30 min)
- Add widget to theme
- Configure environment variables
- Update CORS on backend
- Test on localhost
- Build and deploy

### Phase 6: Polish & Testing (30 min)
- Markdown rendering for answers
- Citation display
- Loading animations
- Error messages
- Mobile responsiveness
- Accessibility audit

**Total**: ~3.5 hours

---

## User Flows

### Flow 1: Full-Book Question

```
1. User opens book page
2. Clicks floating chat button
3. Chat panel opens
4. User types: "What is ROS 2?"
5. Clicks Send (or presses Enter)
6. Message appears in chat
7. Loading indicator shows
8. Backend processes question
9. Response appears with answer
10. Citations shown below answer
11. User can ask follow-up
```

### Flow 2: Selected-Text Question

```
1. User reads book page
2. User highlights text: "DDS is used for communication"
3. Selection detected by widget
4. Badge appears: "Ask about selected text"
5. User opens chat panel
6. Selected text shown in input area
7. User types: "Explain this concept"
8. Clicks Send
9. Backend receives question + selected_text
10. Response constrained to selection
11. Answer displayed with citations
12. Selection cleared
```

### Flow 3: Error Handling

```
1. User asks question
2. Network error occurs
3. Error message: "Unable to connect to chatbot"
4. Retry button appears
5. User clicks Retry
6. Request sent again
7. Success or persistent error
```

---

## UI Mockup (Text-based)

### Closed State
```
┌─────────────────────────────────────┐
│  Book Content Here                  │
│                                     │
│  ... documentation text ...         │
│                                     │
│                             ┌────┐  │
│                             │💬 │  │  ← Floating button
│                             └────┘  │
└─────────────────────────────────────┘
```

### Open State (Desktop)
```
┌─────────────────────────────────────┐
│  Book Content Here                  │
│                                     │
│  ... documentation ...      ┌───────────────────┐
│                             │ Chat Assistant    │
│                             ├───────────────────┤
│                             │ 🧑 What is ROS 2? │
│                             │                   │
│                             │ 🤖 ROS 2 is the   │
│                             │    next generation│
│                             │    [Chapter 1]    │
│                             │                   │
│                             ├───────────────────┤
│                             │ [Your question]   │
│                             │ [Send]            │
│                             └───────────────────┘
└─────────────────────────────────────┘
```

### Selected Text State
```
┌───────────────────────────────────────┐
│ Chat Assistant                        │
├───────────────────────────────────────┤
│ 📌 Selected: "DDS is used for..."     │
│                                       │
│ Type your question about this text:   │
│ ┌─────────────────────────────────┐   │
│ │ Explain this concept            │   │
│ └─────────────────────────────────┘   │
│                            [Send]     │
└───────────────────────────────────────┘
```

---

## API Request/Response Format

### Request (Frontend → Backend)
```json
POST /api/v1/chat

{
  "session_id": "abc-123-def-456",
  "question": "What is ROS 2?",
  "retrieval_mode": "normal",
  "selected_text": null
}
```

### Response (Backend → Frontend)
```json
{
  "session_id": "abc-123-def-456",
  "answer": "ROS 2 is the next generation of the Robot Operating System... [Chapter 1, Section 1.2]",
  "citations": [
    {
      "chapter": "Chapter 1",
      "section": "Section 1.2",
      "text_snippet": "ROS 2 is the next generation...",
      "score": 0.85
    }
  ],
  "retrieval_mode": "normal",
  "grounded": true,
  "metadata": {
    "latency_ms": 2345.67,
    "num_chunks": 5,
    "is_refusal": false
  }
}
```

---

## Error Scenarios

| Error | Cause | Message | Action |
|-------|-------|---------|--------|
| Network Error | No internet | "Unable to connect to chatbot" | Retry button |
| Backend Error | 500 response | "Something went wrong. Please try again." | Retry button |
| Timeout | >10s | "Request timed out" | Retry button |
| Invalid Input | Empty question | "Please enter a question" | None (disable send) |
| CORS Error | Wrong origin | "Configuration error" | Contact admin |

---

## Security Checklist

- [ ] No OPENAI_API_KEY in frontend
- [ ] No QDRANT_API_KEY in frontend
- [ ] Backend URL from environment variable
- [ ] HTTPS in production
- [ ] Input sanitization (escape HTML)
- [ ] Output sanitization (markdown XSS prevention)
- [ ] CORS headers on backend
- [ ] No sensitive data in network logs
- [ ] Session ID non-guessable (UUID)
- [ ] Rate limiting on backend (optional)

---

## Deployment Checklist

### Frontend (GitHub Pages)
- [ ] Set CHATBOT_BACKEND_URL in GitHub Secrets
- [ ] Build Docusaurus with env variable
- [ ] Deploy to GitHub Pages
- [ ] Test widget appears
- [ ] Test backend connectivity

### Backend (Railway/Render)
- [ ] Add GitHub Pages URL to CORS_ORIGINS
- [ ] Set OPENAI_API_KEY
- [ ] Deploy backend
- [ ] Test /api/v1/health endpoint
- [ ] Test /api/v1/chat endpoint

### Integration Testing
- [ ] Open book on GitHub Pages
- [ ] Click chat button
- [ ] Send question
- [ ] Verify response
- [ ] Test selected-text mode
- [ ] Check no console errors
- [ ] Check network tab (no secrets)

---

## Success Metrics

- [ ] Widget loads on all book pages
- [ ] Questions return answers within 5 seconds
- [ ] Selected-text mode works correctly
- [ ] Citations displayed properly
- [ ] No API keys in browser source
- [ ] Mobile responsive
- [ ] Accessible (keyboard navigation)
- [ ] Graceful error handling

---

## Comparison to Existing Implementation

### Current (No Frontend)
- Backend only
- API accessible via curl/Postman
- No user-facing UI
- Manual testing

### New (Embedded Chat)
- Full-stack integration
- Embedded in book pages
- User-friendly interface
- Real-world usage

### Benefits
- **Ease of Use**: Readers ask questions without leaving book
- **Context**: Selected-text questions for specific passages
- **Engagement**: Interactive learning experience
- **Validation**: End-to-end system demonstration

---

## Next Steps After Implementation

1. **User Feedback**: Collect usage data, iterate on UX
2. **Analytics**: Track question types, popular topics
3. **Enhancements**: Conversation export, better citations
4. **Scaling**: CDN for frontend, load balancing for backend
5. **Localization**: Multi-language support (future)

---

**Status**: 📋 Specification complete, ready for implementation

**Estimated Duration**: 3.5 hours

**Dependencies**: backend_v3 (Agentic RAG) ✅, Docusaurus book ✅

**Deployment**: GitHub Pages (frontend) + Railway/Render (backend)
