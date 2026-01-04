# Embedded Chat Interface - Decisions and Testing

Documentation of key architectural decisions and comprehensive testing strategy.

---

## Decision 1: Chat Widget Placement

### The Question
Where should the chat interface be located in the book UI?

### Options Considered

**Option A: Floating Widget (Bottom-Right)**
- Pros:
  - Always visible, never obstructs content
  - Familiar UX pattern (common in support chat)
  - Minimal CSS to implement
  - Works on all page layouts
  - Easy to toggle open/close
- Cons:
  - Takes fixed screen real estate
  - May conflict with other floating elements
  - Harder to see on mobile (small screen)

**Option B: Sidebar (Left or Right)**
- Pros:
  - More screen space for conversation
  - Integrates with existing sidebar layout
  - Desktop-friendly
- Cons:
  - Requires modifying Docusaurus theme
  - Only visible when sidebar expanded
  - Not available on pages without sidebar
  - Complex responsive behavior

**Option C: Top Banner**
- Pros:
  - Highly visible
  - Full-width conversation area
- Cons:
  - Pushes content down when open
  - Not persistent across page navigation
  - Obstructs reading flow

**Option D: Modal/Overlay**
- Pros:
  - Full-screen conversation
  - No layout conflicts
- Cons:
  - Blocks entire page when open
  - Poor UX for quick questions
  - Requires backdrop/overlay code

### Decision: **Option A - Floating Widget (Bottom-Right)**

**Rationale**:
1. **Universal availability**: Works on all book pages regardless of layout
2. **Non-intrusive**: Doesn't block content when closed
3. **Familiar UX**: Users expect chat in bottom-right (industry standard)
4. **Simple implementation**: Minimal CSS, no theme modifications
5. **Mobile-friendly**: Can be resized/repositioned for small screens

**Implementation Details**:
```css
.chatButton {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  z-index: 999;
}

.chatPanel {
  position: fixed;
  bottom: 96px;  /* Above button */
  right: 24px;
  width: 400px;
  height: 600px;
  z-index: 998;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .chatPanel {
    width: calc(100vw - 32px);
    height: calc(100vh - 120px);
  }
}
```

**Trade-offs Accepted**:
- Fixed 56px space always reserved for button
- May overlap with Docusaurus "scroll to top" button (solution: adjust z-index)
- On very small screens (<360px width), may need further adjustment

---

## Decision 2: Method for Capturing Selected Text

### The Question
How should we detect and capture text that users highlight on the page?

### Options Considered

**Option A: `selectionchange` Event (Browser-Native)**
- Pros:
  - Browser-native, no libraries needed
  - Fires automatically on any selection
  - Works with mouse, keyboard, touch
  - Global event (listens once, works everywhere)
- Cons:
  - May fire frequently (performance concern)
  - Captures selections from UI elements (need filtering)

**Option B: `mouseup` Event on Document**
- Pros:
  - Only fires on mouse release
  - Less frequent than selectionchange
  - Simple to implement
- Cons:
  - Doesn't work with keyboard selection
  - Doesn't work with touch devices
  - Misses programmatic selections

**Option C: Context Menu (Right-Click)**
- Pros:
  - Explicit user action
  - Less accidental captures
- Cons:
  - Requires overriding browser context menu
  - Not touch-friendly
  - Extra click required
  - Poor UX (users expect native menu)

**Option D: Button Overlay on Selection**
- Pros:
  - Very explicit
  - No accidental captures
- Cons:
  - Complex implementation (position overlay)
  - Requires selection detection anyway
  - Obstructs selected text
  - Not mobile-friendly

### Decision: **Option A - `selectionchange` Event**

**Rationale**:
1. **Browser-native**: No external dependencies
2. **Comprehensive coverage**: Works with all input methods (mouse, keyboard, touch)
3. **Automatic**: No extra user actions required
4. **Global**: Single event listener for entire page
5. **Standard**: Widely supported across modern browsers

**Implementation**:
```typescript
useEffect(() => {
  if (typeof window === 'undefined') return;

  const handleSelectionChange = () => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();

    // Validation: 10-2000 characters
    if (text && text.length > 10 && text.length <= 2000) {
      setState((prev) => ({ ...prev, selectedText: text }));
    } else if (!text || text.length <= 10) {
      setState((prev) => ({ ...prev, selectedText: null }));
    }
  };

  document.addEventListener('selectionchange', handleSelectionChange);
  return () => document.removeEventListener('selectionchange', handleSelectionChange);
}, []);
```

**Optimizations**:
1. **Minimum length**: 10 characters (prevents accidental selections)
2. **Maximum length**: 2000 characters (backend constraint)
3. **Trim whitespace**: Remove leading/trailing spaces
4. **Debouncing**: Not needed (state update is cheap, render is conditional)

**Trade-offs Accepted**:
- Event fires on ALL selections (even UI elements) - acceptable, filter by length
- May capture selections user didn't intend for questions - mitigated by 10-char minimum and clear button

---

## Decision 3: API Contract Between Frontend and Backend

### The Question
What should the request/response format be for chat communication?

### Options Considered

**Option A: Minimal (Question-Only)**
```json
POST /api/v1/chat
{ "question": "What is ROS 2?" }

Response:
{ "answer": "ROS 2 is..." }
```
- Pros: Simple, minimal payload
- Cons: No session tracking, no metadata, no citations

**Option B: Rich (Full Metadata)**
```json
POST /api/v1/chat
{
  "session_id": "session-123",
  "question": "What is ROS 2?",
  "retrieval_mode": "normal",
  "selected_text": null
}

Response:
{
  "session_id": "session-123",
  "answer": "ROS 2 is...",
  "citations": [...],
  "grounded": true,
  "metadata": {...}
}
```
- Pros: Session continuity, citations, grounding validation
- Cons: Larger payloads, more fields to handle

**Option C: Streaming (SSE/WebSocket)**
- Pros: Real-time response streaming
- Cons: Complex implementation, no benefit for our use case

### Decision: **Option B - Rich Metadata**

**Rationale**:
1. **Session continuity**: Conversation context maintained across requests
2. **Citation support**: Users can verify sources
3. **Grounding validation**: Frontend knows if answer is grounded
4. **Dual modes**: Supports both normal and selected-text retrieval
5. **Debugging**: Metadata helps diagnose issues

**Request Schema**:
```typescript
interface ChatRequest {
  session_id?: string;         // Optional on first request
  question: string;            // Required, max 1000 chars
  retrieval_mode: 'normal' | 'selected_text';
  selected_text?: string;      // Required if mode = selected_text
}
```

**Response Schema**:
```typescript
interface ChatResponse {
  session_id: string;          // Same or new
  answer: string;              // AI-generated answer
  citations: Citation[];       // Source references
  retrieval_mode: string;      // Mode used
  grounded: boolean;           // Answer is grounded
  metadata: {
    latency_ms: number;        // Processing time
    num_chunks: number;        // Chunks retrieved
    is_refusal: boolean;       // Agent refused
  };
}
```

**Trade-offs Accepted**:
- Larger payloads (~1.5KB vs ~200 bytes) - acceptable for broadband
- More fields to validate - mitigated with Pydantic/TypeScript
- Backend must maintain session state - already implemented in backend_v3

---

## Decision 4: Handling Backend Downtime or Slow Responses

### The Question
How should the frontend handle backend unavailability or timeouts?

### Options Considered

**Option A: Fail Fast (No Retry)**
- Show error immediately
- User manually retries
- Pros: Simple, user in control
- Cons: Poor UX for transient errors

**Option B: Automatic Retry (3 attempts)**
- Retry failed requests 2-3 times
- Exponential backoff
- Pros: Handles transient errors
- Cons: Can cause long delays, multiple API calls

**Option C: Timeout + Manual Retry**
- 30-second timeout
- Show error with retry button
- User decides whether to retry
- Pros: Fast feedback, user control
- Cons: Requires user action

**Option D: Offline Mode (Cache Responses)**
- Store previous responses
- Show cached answers when offline
- Pros: Works offline
- Cons: Stale data, complex implementation

### Decision: **Option C - Timeout + Manual Retry**

**Rationale**:
1. **Fast feedback**: 30-second timeout ensures users aren't waiting forever
2. **User control**: Retry button gives users agency
3. **Simple implementation**: No complex retry logic
4. **Clear errors**: Users understand what went wrong
5. **No wasted API calls**: Only retry when user explicitly requests

**Implementation**:
```typescript
// apiClient.ts
const TIMEOUT_MS = 30000; // 30 seconds

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(CHAT_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Unable to connect to chatbot. Please check your connection.');
    }

    throw error;
  }
}
```

**Error UI**:
```typescript
{state.error && (
  <div className={styles.errorMessage}>
    <p>{state.error}</p>
    <button onClick={retryLastMessage}>Retry</button>
  </div>
)}
```

**Trade-offs Accepted**:
- User must manually retry (not automatic) - acceptable, gives control
- No offline mode - acceptable, chatbot requires backend
- 30-second wait before timeout - acceptable for AI processing

---

## Decision 5: Environment-Based Backend URL Configuration

### The Question
How should the frontend know which backend URL to use?

### Options Considered

**Option A: Hardcoded in Source**
```typescript
const BACKEND_URL = 'https://my-backend.railway.app';
```
- Pros: Simple, no configuration needed
- Cons: Can't change without rebuilding, no local dev support

**Option B: Environment Variable (Build-Time)**
```typescript
const BACKEND_URL = process.env.CHATBOT_BACKEND_URL;
```
- Pros: Different URLs for dev/prod
- Cons: Requires rebuild to change, not runtime-configurable

**Option C: Docusaurus Custom Fields**
```javascript
// docusaurus.config.js
customFields: {
  chatbotBackendUrl: process.env.CHATBOT_BACKEND_URL || 'http://localhost:8000',
}
```
- Pros: Integrated with Docusaurus, environment-based, fallback support
- Cons: Requires Docusaurus rebuild to change

**Option D: Runtime Configuration (Fetch from Server)**
- Fetch config.json at runtime
- Pros: Runtime-configurable
- Cons: Extra network request, complex setup

### Decision: **Option C - Docusaurus Custom Fields**

**Rationale**:
1. **Docusaurus-native**: Uses built-in customFields feature
2. **Environment-based**: Different URLs for dev/prod
3. **Fallback support**: Defaults to localhost for dev
4. **Type-safe**: TypeScript can access via window.docusaurus
5. **No extra requests**: No runtime fetching needed

**Implementation**:

**Docusaurus config**:
```javascript
// docusaurus.config.js
const config = {
  // ... existing config ...
  customFields: {
    chatbotBackendUrl: process.env.CHATBOT_BACKEND_URL || 'http://localhost:8000',
  },
};
```

**Frontend access**:
```typescript
// apiClient.ts
const getBackendUrl = (): string => {
  // @ts-ignore - Docusaurus global
  if (typeof window !== 'undefined' && window.docusaurus?.siteConfig?.customFields?.chatbotBackendUrl) {
    // @ts-ignore
    return window.docusaurus.siteConfig.customFields.chatbotBackendUrl;
  }
  return process.env.CHATBOT_BACKEND_URL || 'http://localhost:8000';
};

const BACKEND_URL = getBackendUrl();
```

**Environment setup**:
```bash
# Local development (.env)
CHATBOT_BACKEND_URL=http://localhost:8000

# Production (GitHub Secrets)
CHATBOT_BACKEND_URL=https://your-backend.railway.app
```

**Trade-offs Accepted**:
- Requires rebuild to change URL - acceptable for static deployment
- Not runtime-configurable - acceptable, URL rarely changes
- TypeScript @ts-ignore needed - acceptable, Docusaurus types not complete

---

## Testing Strategy

### Phase 1: Component Unit Testing

**Objective**: Verify individual components render and behave correctly

**Tests**:
```typescript
// ChatButton.test.tsx
test('renders chat button', () => {
  render(<ChatButton onClick={() => {}} />);
  expect(screen.getByLabelText('Open chat assistant')).toBeInTheDocument();
});

test('calls onClick when clicked', () => {
  const handleClick = jest.fn();
  render(<ChatButton onClick={handleClick} />);
  fireEvent.click(screen.getByLabelText('Open chat assistant'));
  expect(handleClick).toHaveBeenCalledTimes(1);
});

// MessageInput.test.tsx
test('sends message on Enter key', () => {
  const handleSend = jest.fn();
  render(<MessageInput onSend={handleSend} />);
  const input = screen.getByPlaceholderText('Ask a question...');

  fireEvent.change(input, { target: { value: 'What is ROS 2?' } });
  fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });

  expect(handleSend).toHaveBeenCalledWith('What is ROS 2?');
});

test('does not send on Shift+Enter', () => {
  const handleSend = jest.fn();
  render(<MessageInput onSend={handleSend} />);
  const input = screen.getByPlaceholderText('Ask a question...');

  fireEvent.change(input, { target: { value: 'Line 1' } });
  fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });

  expect(handleSend).not.toHaveBeenCalled();
});
```

**Validation**:
- [x] ChatButton renders
- [x] ChatButton onClick fires
- [x] MessageInput sends on Enter
- [x] MessageInput adds newline on Shift+Enter
- [x] MessageList displays messages
- [x] SelectedTextBadge shows text
- [x] SelectedTextBadge clear button works

### Phase 2: Integration Testing (Frontend)

**Objective**: Verify component interactions and state management

**Tests**:
```typescript
// ChatWidget.integration.test.tsx
test('opens and closes chat panel', () => {
  render(<ChatWidget />);

  // Initially closed
  expect(screen.queryByText('Book Assistant')).not.toBeInTheDocument();

  // Open chat
  fireEvent.click(screen.getByLabelText('Open chat assistant'));
  expect(screen.getByText('Book Assistant')).toBeInTheDocument();

  // Close chat
  fireEvent.click(screen.getByLabelText('Close chat'));
  expect(screen.queryByText('Book Assistant')).not.toBeInTheDocument();
});

test('detects and displays selected text', async () => {
  render(<ChatWidget />);

  // Simulate text selection
  const selection = {
    toString: () => 'ROS 2 is a middleware',
    removeAllRanges: jest.fn(),
  };
  window.getSelection = jest.fn(() => selection);

  // Trigger selectionchange
  document.dispatchEvent(new Event('selectionchange'));

  // Open chat
  fireEvent.click(screen.getByLabelText('Open chat assistant'));

  // Verify badge appears
  await screen.findByText(/Selected text:/);
  expect(screen.getByText(/ROS 2 is a middleware/)).toBeInTheDocument();
});

test('sends message and displays response', async () => {
  // Mock fetch
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        session_id: 'session-123',
        answer: 'ROS 2 is the next generation...',
        citations: [],
        grounded: true,
        metadata: { is_refusal: false },
      }),
    })
  );

  render(<ChatWidget />);
  fireEvent.click(screen.getByLabelText('Open chat assistant'));

  // Type and send question
  const input = screen.getByPlaceholderText(/Ask a question/);
  fireEvent.change(input, { target: { value: 'What is ROS 2?' } });
  fireEvent.keyDown(input, { key: 'Enter' });

  // Verify user message
  expect(await screen.findByText('What is ROS 2?')).toBeInTheDocument();

  // Verify assistant response
  expect(await screen.findByText(/ROS 2 is the next generation/)).toBeInTheDocument();
});
```

**Validation**:
- [x] Chat panel opens/closes
- [x] Selected text detected
- [x] Badge displays selected text
- [x] Badge clears on clear button
- [x] Message sent on Enter
- [x] Loading indicator shows
- [x] Response displayed
- [x] Session ID persisted

### Phase 3: End-to-End Testing (Full Flow)

**Objective**: Test complete user flows with real backend

**Test Environment**:
```bash
# Terminal 1: Start backend
cd backend_v3
python main.py

# Terminal 2: Start frontend
cd front-end
npm start

# Terminal 3: Run E2E tests
npm run test:e2e
```

**Test Cases**:

**Test 3.1: Full-Book Question Flow**
```
1. Open http://localhost:3000/docs/introduction/intro
2. Click chat button (bottom-right)
3. Verify chat panel opens
4. Type question: "What is ROS 2?"
5. Press Enter
6. Verify loading indicator appears
7. Wait for response (max 10 seconds)
8. Verify answer appears
9. Verify citations expandable
10. Verify sources listed
11. ✅ PASS if answer contains "ROS 2"
```

**Test 3.2: Selected-Text Question Flow**
```
1. Open http://localhost:3000/docs/introduction/intro
2. Highlight text: "DDS is used for inter-node communication"
3. Verify selection detected
4. Click chat button
5. Verify badge shows selected text
6. Type question: "Explain this"
7. Press Enter
8. Verify loading indicator
9. Wait for response
10. Verify answer is constrained to selection
11. Verify selection cleared after send
12. ✅ PASS if answer mentions "DDS"
```

**Test 3.3: Error Handling Flow**
```
1. Open http://localhost:3000/docs/introduction/intro
2. Stop backend (kill process)
3. Click chat button
4. Type question: "What is ROS 2?"
5. Press Enter
6. Verify loading indicator
7. Wait for error (network failure)
8. Verify error message: "Unable to connect to chatbot"
9. Verify retry button appears
10. Start backend again
11. Click retry button
12. Verify response appears
13. ✅ PASS if retry succeeds
```

**Test 3.4: Session Continuity Flow**
```
1. Open http://localhost:3000/docs/introduction/intro
2. Click chat button
3. Send question: "What is ROS 2?"
4. Wait for response
5. Send follow-up: "What are the main improvements?"
6. Verify backend receives same session_id
7. Verify context maintained (answer refers to ROS 2)
8. Navigate to different page
9. Click chat button
10. Verify session persists (messages still visible)
11. ✅ PASS if session_id consistent across pages
```

**Validation**:
- [x] Widget loads on all book pages
- [x] Questions return answers within 5 seconds (P95)
- [x] Selected-text mode works correctly
- [x] Citations displayed properly
- [x] No API keys in browser source
- [x] Mobile responsive (test on 375px, 768px, 1024px)
- [x] Keyboard navigation works (Tab, Enter, Esc)
- [x] Error handling graceful (network, timeout, 4xx, 5xx)

### Phase 4: Security Validation

**Objective**: Ensure no secrets exposed and inputs sanitized

**Tests**:

**Test 4.1: No API Keys in Frontend**
```bash
# 1. Build production bundle
cd front-end
npm run build

# 2. Search for secrets in bundle
grep -r "OPENAI_API_KEY" build/
grep -r "sk-" build/
grep -r "QDRANT_API_KEY" build/

# ✅ PASS if no matches found
```

**Test 4.2: No Secrets in Network Calls**
```
1. Open browser DevTools (F12)
2. Go to Network tab
3. Click chat button
4. Send question: "What is ROS 2?"
5. Inspect request headers
6. Inspect request body
7. Verify no Authorization header
8. Verify no API keys in body
9. ✅ PASS if only backend URL visible
```

**Test 4.3: Input Validation**
```
1. Try sending empty question
   - ✅ Send button disabled
2. Try sending 10001-character question
   - ✅ Textarea truncates at 1000
3. Try selecting 3000-character text
   - ✅ Selection not captured (>2000 limit)
4. Try XSS injection: <script>alert('XSS')</script>
   - ✅ React escapes, no alert
5. Try markdown injection: [Click](javascript:alert('XSS'))
   - ✅ ReactMarkdown sanitizes, no execution
```

**Test 4.4: CORS Validation**
```bash
# 1. Deploy frontend to GitHub Pages
# 2. Attempt to access backend from different origin
curl -X POST https://your-backend.railway.app/api/v1/chat \
  -H "Origin: https://malicious-site.com" \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'

# ✅ PASS if CORS error returned
```

**Validation**:
- [x] No OPENAI_API_KEY in frontend bundle
- [x] No QDRANT_API_KEY in frontend bundle
- [x] Backend URL from environment variable
- [x] HTTPS enforced in production
- [x] Input length limits enforced
- [x] XSS prevented (React + ReactMarkdown)
- [x] CORS restricts origins
- [x] Session ID non-guessable

### Phase 5: Performance Testing

**Objective**: Verify bundle size and response times

**Tests**:

**Test 5.1: Bundle Size**
```bash
cd front-end
npm run build

# Check bundle sizes
du -sh build/assets/*.js | sort -h

# Verify total added by chat widget
# Target: <50KB gzipped

# ✅ PASS if chat widget + react-markdown < 50KB
```

**Test 5.2: Load Time**
```javascript
// Use Lighthouse or Web Vitals
performance.mark('widget-start');
// Chat widget loads
performance.mark('widget-end');
performance.measure('widget-load', 'widget-start', 'widget-end');

// ✅ PASS if <100ms
```

**Test 5.3: API Latency**
```bash
# Send 10 requests, measure P50, P95, P99
for i in {1..10}; do
  time curl -X POST http://localhost:8000/api/v1/chat \
    -H "Content-Type: application/json" \
    -d '{"question": "What is ROS 2?", "retrieval_mode": "normal"}'
done

# ✅ PASS if P95 < 5 seconds
```

**Test 5.4: Responsive Design**
```
Test on screen sizes:
- 375px (mobile)
- 768px (tablet)
- 1024px (desktop)
- 1920px (large desktop)

Verify:
- Chat button visible on all sizes
- Panel width adjusts (400px desktop, full-width mobile)
- Touch targets ≥44px
- Text readable on all sizes

# ✅ PASS if all breakpoints work
```

**Validation**:
- [x] Bundle size <50KB (gzipped)
- [x] Widget initialization <100ms
- [x] No impact on page load time
- [x] API P95 latency <5 seconds
- [x] Responsive on 375px, 768px, 1024px
- [x] Touch targets ≥44px
- [x] Text contrast ≥4.5:1

---

## Quality Validation Checklist

### Functionality ✅
- [x] Chat widget appears on all book pages
- [x] Floating button clickable
- [x] Chat panel opens/closes
- [x] Selected text detected automatically
- [x] Badge shows selected text
- [x] Messages send on Enter
- [x] Shift+Enter adds newline
- [x] Loading indicator shows
- [x] Responses display with markdown
- [x] Citations expandable
- [x] Error messages appear
- [x] Retry button works
- [x] Session persists across pages

### Backend Integration ✅
- [x] API client sends correct format
- [x] Timeout after 30 seconds
- [x] Network errors caught
- [x] CORS configured
- [x] Responses parsed correctly
- [x] Session ID included in requests
- [x] Normal mode works
- [x] Selected-text mode works

### Security ✅
- [x] No API keys in frontend
- [x] Backend URL from environment
- [x] HTTPS in production
- [x] Input sanitization
- [x] Output escaping (ReactMarkdown)
- [x] CORS origins restricted
- [x] Session ID non-guessable
- [x] No tracking or analytics

### Performance ✅
- [x] Bundle size <50KB
- [x] Load time <100ms
- [x] API latency <5s (P95)
- [x] No page load impact
- [x] Smooth animations
- [x] Auto-scroll works

### Accessibility ✅
- [x] Keyboard navigation (Tab, Enter, Esc)
- [x] ARIA labels present
- [x] Focus indicators visible
- [x] Contrast ratio ≥4.5:1
- [x] Touch targets ≥44px
- [x] Screen reader compatible

### Responsive Design ✅
- [x] Desktop (400px panel)
- [x] Tablet (responsive width)
- [x] Mobile (full-width panel)
- [x] Touch-friendly (44px buttons)
- [x] Readable text on all sizes

### Error Handling ✅
- [x] Network error handled
- [x] Timeout error handled
- [x] HTTP 4xx handled
- [x] HTTP 5xx handled
- [x] Validation error handled
- [x] Empty state shown
- [x] Retry mechanism works

---

## Testing Summary

### Test Coverage

**Unit Tests**: 15 tests
- ChatButton: 2 tests
- MessageInput: 3 tests
- MessageList: 3 tests
- SelectedTextBadge: 2 tests
- ChatWidget: 5 tests

**Integration Tests**: 8 tests
- Component interactions: 3 tests
- State management: 2 tests
- API integration: 3 tests

**E2E Tests**: 4 flows
- Full-book question: 1 flow
- Selected-text question: 1 flow
- Error handling: 1 flow
- Session continuity: 1 flow

**Security Tests**: 4 tests
- No API keys in bundle
- No secrets in network
- Input validation
- CORS validation

**Performance Tests**: 4 tests
- Bundle size
- Load time
- API latency
- Responsive design

**Total**: 35 tests across 5 phases

### Test Execution

```bash
# Run all tests
npm run test                # Unit + Integration
npm run test:e2e            # End-to-end (requires backend)
npm run test:security       # Security validation
npm run test:performance    # Performance benchmarks

# Coverage report
npm run test:coverage

# Target: >80% code coverage
```

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-03
**Status**: Complete decisions and testing strategy
