# Embedded Chat Interface - Task Breakdown

Detailed task list for implementing the embedded chat widget in Docusaurus.

---

## Overview

**Total Estimated Duration**: 210 minutes (3.5 hours)

**Phases**:
1. UI Setup (60 min)
2. Selection Capture (30 min)
3. Backend Communication (45 min)
4. Rendering & Polish (30 min)
5. Configuration & Deployment (30 min)
6. Testing & Validation (45 min)

---

## Phase 1: UI Setup (60 minutes)

### Task 1.1: Create TypeScript Type Definitions
**Duration**: 10 minutes

**Files**:
- `front-end/src/components/ChatWidget/types.ts`

**Checklist**:
- [ ] Define `Message` interface (id, role, content, timestamp, citations, isRefusal)
- [ ] Define `Citation` interface (chapter, section, text_snippet, score)
- [ ] Define `ChatRequest` interface (session_id, question, retrieval_mode, selected_text)
- [ ] Define `ChatResponse` interface (session_id, answer, citations, grounded, metadata)
- [ ] Define `ChatWidgetState` interface (isOpen, messages, isLoading, error, selectedText, sessionId)
- [ ] Export all types

**Validation**:
- TypeScript compiles without errors
- All interfaces have required fields
- Optional fields marked with `?`

---

### Task 1.2: Create Floating Chat Button Component
**Duration**: 15 minutes

**Files**:
- `front-end/src/components/ChatWidget/ChatButton.tsx`
- `front-end/src/components/ChatWidget/ChatWidget.module.css`

**Checklist**:
- [ ] Create ChatButton component with onClick prop
- [ ] Add SVG chat icon (24x24)
- [ ] Add optional hasUnread badge
- [ ] Add ARIA label: "Open chat assistant"
- [ ] Style: 56px circle, fixed bottom-right, z-index 999
- [ ] Add hover effect (scale 1.05)
- [ ] Add active effect (scale 0.95)
- [ ] Add box-shadow for depth

**Validation**:
- Button renders at bottom-right
- Icon visible and centered
- Hover/active animations smooth
- Accessible via keyboard (Tab + Enter)

---

### Task 1.3: Create Message Input Component
**Duration**: 15 minutes

**Files**:
- `front-end/src/components/ChatWidget/MessageInput.tsx`

**Checklist**:
- [ ] Create MessageInput component with onSend, disabled, placeholder props
- [ ] Add textarea with auto-resize (max 120px height)
- [ ] Handle Enter to send (Shift+Enter for newline)
- [ ] Add maxLength: 1000 characters
- [ ] Add send button with SVG icon
- [ ] Disable send button when input empty or disabled
- [ ] Clear input after send
- [ ] Add input change handler for auto-resize

**Validation**:
- Enter sends message
- Shift+Enter adds newline
- Textarea auto-resizes
- Send button disabled when empty
- Max length enforced

---

### Task 1.4: Create Message List Component
**Duration**: 20 minutes

**Files**:
- `front-end/src/components/ChatWidget/MessageList.tsx`

**Checklist**:
- [ ] Create MessageList component with messages, isLoading props
- [ ] Render user messages (blue, right-aligned)
- [ ] Render assistant messages (gray, left-aligned)
- [ ] Integrate ReactMarkdown for assistant messages
- [ ] Add expandable citations (details/summary)
- [ ] Add timestamps for each message
- [ ] Add empty state UI (when no messages)
- [ ] Add loading indicator (3 animated dots)
- [ ] Auto-scroll to newest message (useEffect + ref)

**Validation**:
- Messages display correctly
- Markdown renders in assistant messages
- Citations expandable
- Timestamps formatted (HH:MM)
- Empty state shows
- Auto-scroll works

---

## Phase 2: Selection Capture (30 minutes)

### Task 2.1: Implement Text Selection Detection
**Duration**: 15 minutes

**Files**:
- `front-end/src/components/ChatWidget/ChatWidget.tsx` (main component)

**Checklist**:
- [ ] Add useEffect for selectionchange event listener
- [ ] Get selection using window.getSelection()
- [ ] Validate selection length (10-2000 chars)
- [ ] Update selectedText state when valid
- [ ] Clear selectedText when invalid (<10 chars)
- [ ] Handle SSR (check typeof window !== 'undefined')
- [ ] Clean up event listener on unmount

**Validation**:
- Selection detected when >10 chars highlighted
- Selection cleared when <10 chars
- Selection limited to 2000 chars
- No errors in SSR/build

---

### Task 2.2: Create Selected Text Badge Component
**Duration**: 15 minutes

**Files**:
- `front-end/src/components/ChatWidget/SelectedTextBadge.tsx`

**Checklist**:
- [ ] Create SelectedTextBadge component with text, onClear props
- [ ] Display text preview (max 100 chars with ellipsis)
- [ ] Add book icon SVG
- [ ] Add clear button (X icon)
- [ ] Add hint text: "Your question will be answered based on this selection only."
- [ ] Style: blue background, rounded, padding
- [ ] Add badge header with icon + label + clear button

**Validation**:
- Badge displays selected text
- Text truncated at 100 chars
- Clear button works
- Hint text visible
- Styled with blue theme

---

## Phase 3: Backend Communication (45 minutes)

### Task 3.1: Create API Client
**Duration**: 20 minutes

**Files**:
- `front-end/src/components/ChatWidget/apiClient.ts`

**Checklist**:
- [ ] Create getBackendUrl() function (reads from Docusaurus config)
- [ ] Define BACKEND_URL constant
- [ ] Define CHAT_ENDPOINT: `/api/v1/chat`
- [ ] Define TIMEOUT_MS: 30000 (30 seconds)
- [ ] Implement sendChatMessage(request) function
- [ ] Add AbortController for timeout
- [ ] Add fetch with POST, JSON headers, body
- [ ] Handle timeout error (AbortError)
- [ ] Handle network error (TypeError)
- [ ] Handle HTTP errors (4xx, 5xx)
- [ ] Parse and return ChatResponse
- [ ] Implement checkBackendHealth() function (optional)

**Validation**:
- API client sends correct request format
- Timeout after 30 seconds
- Network errors caught with friendly message
- HTTP errors display response.statusText
- Response parsed as JSON

---

### Task 3.2: Implement Send Message Logic
**Duration**: 25 minutes

**Files**:
- `front-end/src/components/ChatWidget/ChatWidget.tsx`

**Checklist**:
- [ ] Implement sendMessage(content) function
- [ ] Create user message object
- [ ] Update state: add user message, set isLoading=true, clear error
- [ ] Generate or retrieve session ID
- [ ] Store session ID in sessionStorage
- [ ] Call sendChatMessage() with ChatRequest
- [ ] Handle response: create assistant message
- [ ] Update state: add assistant message, set isLoading=false, clear selectedText
- [ ] Clear window selection
- [ ] Handle errors: update state with error message
- [ ] Implement retryLastMessage() function

**Validation**:
- User message appears immediately
- Loading indicator shows
- Assistant message appears after response
- Session ID persisted in sessionStorage
- Errors display with retry button
- Retry button resends last question

---

## Phase 4: Rendering & Polish (30 minutes)

### Task 4.1: Create Main Chat Widget Component
**Duration**: 20 minutes

**Files**:
- `front-end/src/components/ChatWidget/ChatWidget.tsx`

**Checklist**:
- [ ] Define SESSION_STORAGE_KEY and OPEN_STATE_KEY constants
- [ ] Implement generateSessionId() helper
- [ ] Initialize state with ChatWidgetState
- [ ] Load isOpen from sessionStorage
- [ ] Load sessionId from sessionStorage
- [ ] Add useEffect to persist isOpen state
- [ ] Implement toggleChat() function
- [ ] Implement clearSelection() function
- [ ] Render ChatButton when closed
- [ ] Render ChatPanel when open (with header, body, footer)
- [ ] Conditionally render SelectedTextBadge
- [ ] Render MessageList with messages and isLoading
- [ ] Conditionally render error message with retry button
- [ ] Render MessageInput in footer

**Validation**:
- Widget toggles open/closed
- State persists in sessionStorage
- All sub-components render correctly
- Error UI shows when error occurs
- Retry button functional

---

### Task 4.2: Add Responsive Styles
**Duration**: 10 minutes

**Files**:
- `front-end/src/components/ChatWidget/ChatWidget.module.css`

**Checklist**:
- [ ] Add desktop styles: 400px width, 600px height
- [ ] Add mobile breakpoint: @media (max-width: 768px)
- [ ] Mobile: full-width panel, calc(100vh - 120px) height
- [ ] Style chat header (primary color, white text)
- [ ] Style message bubbles (user: blue right, assistant: gray left)
- [ ] Style citations (details/summary)
- [ ] Style loading indicator (3 dots animation)
- [ ] Style error message (red background)
- [ ] Style selected text badge (blue background)
- [ ] Add animations (bounce for loading, scale for button)

**Validation**:
- Desktop: 400px panel width
- Mobile: full-width panel
- All components styled consistently
- Animations smooth
- Readable on all screen sizes

---

## Phase 5: Configuration & Deployment (30 minutes)

### Task 5.1: Update Package Dependencies
**Duration**: 5 minutes

**Files**:
- `front-end/package.json`

**Checklist**:
- [ ] Add `react-markdown@^9.0.0` to dependencies
- [ ] Run `npm install` to install

**Validation**:
- react-markdown installed
- No dependency conflicts
- npm install completes successfully

---

### Task 5.2: Configure Docusaurus
**Duration**: 10 minutes

**Files**:
- `front-end/docusaurus.config.js`
- `front-end/.env`

**Checklist**:
- [ ] Add customFields to docusaurus.config.js
- [ ] Set chatbotBackendUrl: process.env.CHATBOT_BACKEND_URL || 'http://localhost:8000'
- [ ] Create .env file with CHATBOT_BACKEND_URL
- [ ] Set local: CHATBOT_BACKEND_URL=http://localhost:8000

**Validation**:
- customFields accessible in frontend
- Backend URL defaults to localhost
- Environment variable loaded

---

### Task 5.3: Integrate with Docusaurus Theme
**Duration**: 5 minutes

**Files**:
- `front-end/src/theme/Root.js`

**Checklist**:
- [ ] Import ChatWidget from '../components/ChatWidget'
- [ ] Render ChatWidget after {children}
- [ ] Verify Root.js wraps all pages

**Validation**:
- Chat widget appears on all book pages
- Widget persists across page navigation
- No layout conflicts

---

### Task 5.4: Configure Backend CORS
**Duration**: 10 minutes

**Files**:
- `backend_v3/config.py` (or `backend/config.py`)
- `backend_v3/main.py` (or `backend/main.py`)

**Checklist**:
- [ ] Update CORS_ORIGINS to include localhost:3000
- [ ] Add GitHub Pages URL: https://mehreen676.github.io
- [ ] Verify CORSMiddleware configured in main.py
- [ ] Set allow_credentials=False
- [ ] Set allow_methods=["GET", "POST"]
- [ ] Set allow_headers=["Content-Type"]

**Validation**:
- CORS allows localhost origin
- CORS allows GitHub Pages origin
- CORS blocks other origins
- No credentials sent

---

## Phase 6: Testing & Validation (45 minutes)

### Task 6.1: Manual UI Testing
**Duration**: 15 minutes

**Checklist**:
- [ ] Start frontend: `npm start`
- [ ] Open http://localhost:3000
- [ ] Verify chat button appears (bottom-right)
- [ ] Click button, verify panel opens
- [ ] Verify empty state shows
- [ ] Type question, verify send button enables
- [ ] Verify textarea auto-resizes
- [ ] Press Enter, verify input clears
- [ ] Close panel, verify state persists
- [ ] Navigate to different page, verify widget persists
- [ ] Test on mobile (375px width)
- [ ] Test keyboard navigation (Tab, Enter, Esc)

**Validation**:
- All UI interactions work
- State persists across pages
- Responsive on mobile
- Keyboard accessible

---

### Task 6.2: Selected Text Testing
**Duration**: 10 minutes

**Checklist**:
- [ ] Highlight text on page (>10 chars)
- [ ] Verify badge appears in chat (if open)
- [ ] Open chat, verify badge shows selected text
- [ ] Verify clear button works
- [ ] Verify text truncated at 100 chars
- [ ] Highlight text <10 chars, verify badge doesn't appear
- [ ] Highlight text >2000 chars, verify badge doesn't appear

**Validation**:
- Selection detected correctly
- Badge displays selected text
- Clear button works
- Length validation works

---

### Task 6.3: End-to-End Testing with Backend
**Duration**: 15 minutes

**Checklist**:
- [ ] Start backend: `cd backend_v3 && python main.py`
- [ ] Verify backend health: http://localhost:8000/api/v1/health
- [ ] Send full-book question: "What is ROS 2?"
- [ ] Verify loading indicator shows
- [ ] Verify response appears (within 10 seconds)
- [ ] Verify citations expandable
- [ ] Highlight text, ask selected-text question
- [ ] Verify constrained answer
- [ ] Stop backend, send question
- [ ] Verify error message: "Unable to connect"
- [ ] Verify retry button appears
- [ ] Start backend, click retry
- [ ] Verify response appears

**Validation**:
- Full-book questions work
- Selected-text questions work
- Responses display correctly
- Citations shown
- Error handling graceful
- Retry mechanism works

---

### Task 6.4: Security Validation
**Duration**: 5 minutes

**Checklist**:
- [ ] Open browser DevTools (F12)
- [ ] Go to Network tab
- [ ] Send question
- [ ] Inspect request headers
- [ ] Verify no Authorization header
- [ ] Inspect request body
- [ ] Verify no API keys in body
- [ ] Verify only backend URL visible
- [ ] View page source
- [ ] Search for "OPENAI_API_KEY"
- [ ] Search for "sk-"
- [ ] Verify no matches found

**Validation**:
- No API keys in frontend
- No secrets in network requests
- Backend URL only public info
- Input/output sanitized

---

## Implementation Checklist

### Phase 1: UI Setup ✅
- [ ] Task 1.1: Create TypeScript types (10 min)
- [ ] Task 1.2: Create ChatButton component (15 min)
- [ ] Task 1.3: Create MessageInput component (15 min)
- [ ] Task 1.4: Create MessageList component (20 min)

### Phase 2: Selection Capture ✅
- [ ] Task 2.1: Implement selection detection (15 min)
- [ ] Task 2.2: Create SelectedTextBadge component (15 min)

### Phase 3: Backend Communication ✅
- [ ] Task 3.1: Create API client (20 min)
- [ ] Task 3.2: Implement send message logic (25 min)

### Phase 4: Rendering & Polish ✅
- [ ] Task 4.1: Create main ChatWidget component (20 min)
- [ ] Task 4.2: Add responsive styles (10 min)

### Phase 5: Configuration & Deployment ✅
- [ ] Task 5.1: Update package dependencies (5 min)
- [ ] Task 5.2: Configure Docusaurus (10 min)
- [ ] Task 5.3: Integrate with theme (5 min)
- [ ] Task 5.4: Configure backend CORS (10 min)

### Phase 6: Testing & Validation ✅
- [ ] Task 6.1: Manual UI testing (15 min)
- [ ] Task 6.2: Selected text testing (10 min)
- [ ] Task 6.3: End-to-end testing (15 min)
- [ ] Task 6.4: Security validation (5 min)

---

## File Creation Summary

### New Files (13 total)

**Components** (9 files):
```
front-end/src/components/ChatWidget/
├── index.ts
├── types.ts
├── apiClient.ts
├── ChatWidget.tsx
├── ChatButton.tsx
├── MessageList.tsx
├── MessageInput.tsx
├── SelectedTextBadge.tsx
└── ChatWidget.module.css
```

**Configuration** (3 files):
```
front-end/
├── .env (updated)
├── package.json (updated)
└── docusaurus.config.js (updated)
```

**Integration** (1 file):
```
front-end/src/theme/
└── Root.js (already exists, verify ChatWidget import)
```

**Backend** (2 files updated):
```
backend_v3/
├── config.py (updated CORS)
└── main.py (verify CORSMiddleware)
```

---

## Dependencies

### Required Before Starting
- [ ] Node.js 18+ installed
- [ ] npm or yarn installed
- [ ] Docusaurus 3.0 project exists
- [ ] Backend (backend_v3 or backend) implemented
- [ ] Python 3.11+ installed (for backend)

### Required APIs/Services
- [ ] OpenAI API key (for backend)
- [ ] Qdrant Cloud instance (for backend)
- [ ] Qdrant API key (for backend)
- [ ] Gemini API key (for embeddings) or USE_MOCK_EMBEDDINGS=true

### Optional
- [ ] Neon Postgres database (for production)
- [ ] Railway/Render account (for backend deployment)
- [ ] GitHub repository (for frontend deployment)

---

## Success Criteria

### Functional ✅
- [x] Chat widget appears on all book pages
- [x] Floating button opens/closes chat panel
- [x] Users can type and send questions
- [x] Selected text detected and sent with question
- [x] Responses display with markdown formatting
- [x] Citations shown and expandable
- [x] Loading and error states work correctly

### Non-Functional ✅
- [x] Bundle size <50KB (gzipped)
- [x] Widget initialization <100ms
- [x] No impact on page load time
- [x] Responsive on mobile (375px+)
- [x] Accessible (keyboard navigation)
- [x] Secure (no API keys exposed)

### Integration ✅
- [x] API client communicates with backend
- [x] CORS configured correctly
- [x] Session persistence works
- [x] Error handling graceful
- [x] Retry mechanism functional

---

## Troubleshooting Guide

### Issue: Chat button not appearing
**Solution**:
- Check Root.js imports ChatWidget
- Verify no CSS conflicts (z-index)
- Clear browser cache
- Check console for errors

### Issue: Backend connection fails
**Solution**:
- Verify backend running: http://localhost:8000/api/v1/health
- Check CHATBOT_BACKEND_URL in .env
- Verify CORS_ORIGINS includes frontend URL
- Check browser console for CORS errors

### Issue: Selected text not detected
**Solution**:
- Check selection >10 characters
- Verify selectionchange listener attached
- Check console for errors
- Try selecting plain text (not UI elements)

### Issue: TypeScript errors
**Solution**:
- Run `npm install` to install dependencies
- Check types.ts exports all interfaces
- Verify react-markdown installed
- Run `npm run typecheck`

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-03
**Total Tasks**: 24 tasks across 6 phases
**Estimated Duration**: 210 minutes (3.5 hours)
