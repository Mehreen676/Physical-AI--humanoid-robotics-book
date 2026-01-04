# Embedded Chat Interface - Section Structure

Detailed implementation sections for embedding the agentic RAG chatbot in Docusaurus.

---

## Section 1: Chat Widget Component Design

**Objective**: Create React components for floating chat interface

**Duration**: 60 minutes

**Deliverables**:
- ChatWidget.tsx (main component)
- ChatButton.tsx (floating button)
- ChatPanel.tsx (collapsible panel)
- MessageList.tsx (conversation display)
- MessageInput.tsx (user input field)
- types.ts (TypeScript definitions)

### 1.1 Component Hierarchy

```typescript
// types.ts - Type Definitions
export interface Message {
  id: string;                  // Unique identifier
  role: 'user' | 'assistant';  // Message sender
  content: string;             // Message text
  timestamp: Date;             // When sent
  citations?: Citation[];      // Source references (assistant only)
  isRefusal?: boolean;         // Whether agent refused to answer
}

export interface Citation {
  chapter: string;             // Chapter name
  section: string;             // Section name
  text_snippet: string;        // Excerpt from source
  score: number;               // Relevance score (0-1)
}

export interface ChatRequest {
  session_id?: string;         // Optional on first request
  question: string;            // User's question
  retrieval_mode: 'normal' | 'selected_text';
  selected_text?: string;      // Required if mode = selected_text
}

export interface ChatResponse {
  session_id: string;          // Session identifier
  answer: string;              // AI-generated answer
  citations: Citation[];       // Source citations
  retrieval_mode: string;      // Mode used
  grounded: boolean;           // Answer is grounded
  metadata: {
    latency_ms: number;        // Processing time
    num_chunks: number;        // Chunks retrieved
    is_refusal: boolean;       // Agent refused
  };
}

export interface ChatWidgetState {
  isOpen: boolean;             // Panel open/closed
  messages: Message[];         // Conversation history
  isLoading: boolean;          // Waiting for response
  error: string | null;        // Error message
  selectedText: string | null; // Highlighted text
  sessionId: string | null;    // Session ID
}
```

### 1.2 Main Widget Component

```typescript
// ChatWidget.tsx - Main Component
import React, { useState, useEffect } from 'react';
import ChatButton from './ChatButton';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import SelectedTextBadge from './SelectedTextBadge';
import { sendChatMessage } from './apiClient';
import type { Message, ChatWidgetState } from './types';

const SESSION_STORAGE_KEY = 'chat-widget-session';
const OPEN_STATE_KEY = 'chat-widget-open';

function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export default function ChatWidget(): JSX.Element {
  const [state, setState] = useState<ChatWidgetState>({
    isOpen: sessionStorage.getItem(OPEN_STATE_KEY) === 'true',
    messages: [],
    isLoading: false,
    error: null,
    selectedText: null,
    sessionId: sessionStorage.getItem(SESSION_STORAGE_KEY),
  });

  // Selection detection (Section 2 - detailed below)
  useEffect(() => {
    const handleSelectionChange = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();
      if (text && text.length > 10 && text.length <= 2000) {
        setState((prev) => ({ ...prev, selectedText: text }));
      } else if (!text || text.length <= 10) {
        setState((prev) => ({ ...prev, selectedText: null }));
      }
    };

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, []);

  // Persist open state
  useEffect(() => {
    sessionStorage.setItem(OPEN_STATE_KEY, state.isOpen.toString());
  }, [state.isOpen]);

  const toggleChat = () => {
    setState((prev) => ({ ...prev, isOpen: !prev.isOpen }));
  };

  const clearSelection = () => {
    setState((prev) => ({ ...prev, selectedText: null }));
    window.getSelection()?.removeAllRanges();
  };

  const sendMessage = async (content: string) => {
    // Implementation in Section 3
  };

  const retryLastMessage = () => {
    const lastUserMessage = [...state.messages]
      .reverse()
      .find((m) => m.role === 'user');
    if (lastUserMessage) {
      sendMessage(lastUserMessage.content);
    }
  };

  if (!state.isOpen) {
    return <ChatButton onClick={toggleChat} />;
  }

  return (
    <>
      <ChatButton onClick={toggleChat} />
      <div className={styles.chatPanel}>
        <div className={styles.chatHeader}>
          <h3>Book Assistant</h3>
          <button onClick={toggleChat} aria-label="Close chat">×</button>
        </div>

        <div className={styles.chatBody}>
          {state.selectedText && (
            <SelectedTextBadge text={state.selectedText} onClear={clearSelection} />
          )}

          <MessageList messages={state.messages} isLoading={state.isLoading} />

          {state.error && (
            <div className={styles.errorMessage}>
              <p>{state.error}</p>
              <button onClick={retryLastMessage}>Retry</button>
            </div>
          )}
        </div>

        <div className={styles.chatFooter}>
          <MessageInput
            onSend={sendMessage}
            disabled={state.isLoading}
            placeholder={
              state.selectedText
                ? 'Ask about the selected text...'
                : 'Ask a question about this book...'
            }
          />
        </div>
      </div>
    </>
  );
}
```

### 1.3 Floating Button Component

```typescript
// ChatButton.tsx - Floating Button
import React from 'react';

interface ChatButtonProps {
  onClick: () => void;
  hasUnread?: boolean;
}

export default function ChatButton({ onClick, hasUnread = false }: ChatButtonProps): JSX.Element {
  return (
    <button
      className={styles.chatButton}
      onClick={onClick}
      aria-label="Open chat assistant"
      title="Ask questions about this book"
    >
      {/* SVG chat icon */}
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
        <path d="M7 9H17M7 13H13" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      </svg>
      {hasUnread && <span className={styles.unreadBadge} />}
    </button>
  );
}
```

**CSS for floating button**:
```css
.chatButton {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--ifm-color-primary);
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  z-index: 999;
}

.chatButton:hover {
  transform: scale(1.05);
}
```

### 1.4 Message Display Component

```typescript
// MessageList.tsx - Message Display
import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import type { Message } from './types';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
}

export default function MessageList({ messages, isLoading = false }: MessageListProps): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className={styles.emptyState}>
        <svg width="48" height="48" viewBox="0 0 24 24">
          <path d="M20 2H4C2.9 2 2 2.9 2 4V22L6 18H20C21.1 18 22 17.1 22 16V4C22 2.9 21.1 2 20 2Z" fill="currentColor" opacity="0.3"/>
        </svg>
        <h3>Ask me anything about this book</h3>
        <p>Select text for focused questions or ask about the entire book.</p>
      </div>
    );
  }

  return (
    <div className={styles.messageList}>
      {messages.map((message) => (
        <div
          key={message.id}
          className={message.role === 'user' ? styles.userMessage : styles.assistantMessage}
        >
          <div className={styles.messageContent}>
            {message.role === 'assistant' ? (
              <>
                <ReactMarkdown>{message.content}</ReactMarkdown>
                {message.citations && message.citations.length > 0 && (
                  <div className={styles.citations}>
                    <details>
                      <summary>Sources ({message.citations.length})</summary>
                      <ul>
                        {message.citations.map((citation, idx) => (
                          <li key={idx}>
                            <strong>{citation.chapter}</strong> - {citation.section}<br/>
                            <small>{citation.text_snippet.substring(0, 100)}...</small><br/>
                            <span className={styles.score}>Relevance: {(citation.score * 100).toFixed(0)}%</span>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </div>
                )}
              </>
            ) : (
              <p>{message.content}</p>
            )}
          </div>
          <time>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
        </div>
      ))}

      {isLoading && (
        <div className={styles.loadingIndicator}>
          <span></span><span></span><span></span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
```

### 1.5 Input Component

```typescript
// MessageInput.tsx - User Input
import React, { useState, useRef, KeyboardEvent } from 'react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function MessageInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about this book...',
}: MessageInputProps): JSX.Element {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = input.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div className={styles.inputContainer}>
      <textarea
        ref={textareaRef}
        value={input}
        onChange={handleInput}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        maxLength={1000}
        rows={1}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        aria-label="Send message"
      >
        {/* Send icon SVG */}
        <svg width="20" height="20" viewBox="0 0 20 20">
          <path d="M2 10L18 2L10 18L8 11L2 10Z" fill="currentColor"/>
        </svg>
      </button>
    </div>
  );
}
```

---

## Section 2: Selected-Text Capture Logic

**Objective**: Detect user text selection from book pages

**Duration**: 30 minutes

**Deliverables**:
- Selection detection logic
- SelectedTextBadge component
- Clear selection handler

### 2.1 Selection Detection

```typescript
// In ChatWidget.tsx - useEffect for selection
useEffect(() => {
  if (typeof window === 'undefined') return;

  const handleSelectionChange = () => {
    const selection = window.getSelection();
    const text = selection?.toString().trim();

    // Validation rules
    if (text && text.length > 10 && text.length <= 2000) {
      setState((prev) => ({ ...prev, selectedText: text }));
    } else if (!text || text.length <= 10) {
      // Clear if selection too short or empty
      setState((prev) => ({ ...prev, selectedText: null }));
    }
  };

  // Listen to selectionchange event
  document.addEventListener('selectionchange', handleSelectionChange);

  return () => {
    document.removeEventListener('selectionchange', handleSelectionChange);
  };
}, []);
```

**Why `selectionchange`**:
- Fires whenever text selection changes on page
- Global event (not per-element)
- Browser-native, no external libraries needed
- Works with mouse, keyboard, touch selection

**Validation Rules**:
1. **Minimum**: 10 characters (prevent accidental selections)
2. **Maximum**: 2000 characters (backend constraint)
3. **Trim whitespace**: Remove leading/trailing spaces
4. **Plain text only**: No HTML or formatting

### 2.2 Selected Text Badge

```typescript
// SelectedTextBadge.tsx - Display selected text
import React from 'react';

interface SelectedTextBadgeProps {
  text: string;
  onClear: () => void;
}

export default function SelectedTextBadge({ text, onClear }: SelectedTextBadgeProps): JSX.Element {
  const displayText = text.length > 100 ? `${text.substring(0, 100)}...` : text;

  return (
    <div className={styles.selectedTextBadge}>
      <div className={styles.badgeHeader}>
        <svg width="16" height="16">{/* Book icon */}</svg>
        <span>Selected text:</span>
        <button onClick={onClear} aria-label="Clear selection">×</button>
      </div>
      <div className={styles.badgeContent}>{displayText}</div>
      <p className={styles.badgeHint}>Your question will be answered based on this selection only.</p>
    </div>
  );
}
```

**CSS styling**:
```css
.selectedTextBadge {
  margin: 12px 16px 0 16px;
  padding: 12px;
  background: var(--ifm-color-info-contrast-background);
  border: 1px solid var(--ifm-color-info);
  border-radius: 8px;
}

.badgeContent {
  padding: 8px;
  background: white;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
}
```

### 2.3 Clear Selection Handler

```typescript
// In ChatWidget.tsx
const clearSelection = () => {
  setState((prev) => ({ ...prev, selectedText: null }));

  if (typeof window !== 'undefined') {
    window.getSelection()?.removeAllRanges();
  }
};

// Auto-clear after sending
const sendMessage = async (content: string) => {
  // ... send logic ...

  // Clear selection after sending
  setState((prev) => ({ ...prev, selectedText: null }));
  window.getSelection()?.removeAllRanges();
};
```

---

## Section 3: Request/Response Handling with Backend

**Objective**: Communicate with FastAPI backend

**Duration**: 45 minutes

**Deliverables**:
- apiClient.ts (Fetch API wrapper)
- Error handling
- Timeout management
- Type-safe requests/responses

### 3.1 API Client

```typescript
// apiClient.ts - Backend Communication
import type { ChatRequest, ChatResponse } from './types';

// Get backend URL from Docusaurus config
const getBackendUrl = (): string => {
  // @ts-ignore - Docusaurus global
  if (typeof window !== 'undefined' && window.docusaurus?.siteConfig?.customFields?.chatbotBackendUrl) {
    // @ts-ignore
    return window.docusaurus.siteConfig.customFields.chatbotBackendUrl;
  }
  return process.env.CHATBOT_BACKEND_URL || 'http://localhost:8000';
};

const BACKEND_URL = getBackendUrl();
const CHAT_ENDPOINT = `${BACKEND_URL}/api/v1/chat`;
const TIMEOUT_MS = 30000; // 30 seconds

/**
 * Send chat request to backend
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(CHAT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error) {
    clearTimeout(timeoutId);

    // Handle timeout
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Unable to connect to chatbot. Please check your connection.');
    }

    // Re-throw other errors
    throw error;
  }
}

/**
 * Check backend health
 */
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}
```

### 3.2 Send Message Implementation

```typescript
// In ChatWidget.tsx - sendMessage function
const sendMessage = async (content: string) => {
  // Create user message
  const userMessage: Message = {
    id: `user-${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date(),
  };

  // Update state: add user message, show loading
  setState((prev) => ({
    ...prev,
    messages: [...prev.messages, userMessage],
    isLoading: true,
    error: null,
  }));

  try {
    // Generate or retrieve session ID
    const sessionId = state.sessionId || generateSessionId();
    if (!state.sessionId) {
      sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
      setState((prev) => ({ ...prev, sessionId }));
    }

    // Send request to backend
    const response = await sendChatMessage({
      session_id: sessionId,
      question: content,
      retrieval_mode: state.selectedText ? 'selected_text' : 'normal',
      selected_text: state.selectedText || undefined,
    });

    // Create assistant message
    const assistantMessage: Message = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: response.answer,
      timestamp: new Date(),
      citations: response.citations,
      isRefusal: response.metadata.is_refusal,
    };

    // Update state: add assistant message, hide loading, clear selection
    setState((prev) => ({
      ...prev,
      messages: [...prev.messages, assistantMessage],
      isLoading: false,
      selectedText: null, // Clear selection after sending
    }));

    // Clear text selection
    if (typeof window !== 'undefined') {
      window.getSelection()?.removeAllRanges();
    }
  } catch (error) {
    // Update state: show error, hide loading
    setState((prev) => ({
      ...prev,
      isLoading: false,
      error: error instanceof Error ? error.message : 'An error occurred',
    }));
  }
};
```

### 3.3 Error Handling

```typescript
// Error states in ChatWidget
{state.error && (
  <div className={styles.errorMessage}>
    <p>{state.error}</p>
    <button onClick={retryLastMessage} className={styles.retryButton}>
      Retry
    </button>
  </div>
)}

// Retry handler
const retryLastMessage = () => {
  const lastUserMessage = [...state.messages]
    .reverse()
    .find((m) => m.role === 'user');

  if (lastUserMessage) {
    sendMessage(lastUserMessage.content);
  }
};
```

---

## Section 4: UI States (Loading, Error, Response)

**Objective**: Handle all UI states gracefully

**Duration**: 30 minutes

**Deliverables**:
- Loading indicators
- Error displays
- Empty states
- Success states

### 4.1 Loading State

```typescript
// Loading indicator component
{isLoading && (
  <div className={styles.loadingIndicator}>
    <span></span>
    <span></span>
    <span></span>
  </div>
)}
```

**CSS animation**:
```css
.loadingIndicator {
  display: flex;
  gap: 6px;
  padding: 16px;
}

.loadingIndicator span {
  width: 8px;
  height: 8px;
  background: var(--ifm-color-primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.loadingIndicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.loadingIndicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
```

### 4.2 Error State

```typescript
// Error message display
{state.error && (
  <div className={styles.errorMessage}>
    <p>{state.error}</p>
    <button onClick={retryLastMessage}>Retry</button>
  </div>
)}
```

**CSS styling**:
```css
.errorMessage {
  margin: 0 16px 12px 16px;
  padding: 12px;
  background: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  color: #c33;
}

.retryButton {
  padding: 6px 12px;
  background: #c33;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
```

### 4.3 Empty State

```typescript
// When no messages exist
if (messages.length === 0 && !isLoading) {
  return (
    <div className={styles.emptyState}>
      <svg width="48" height="48">
        {/* Chat icon */}
      </svg>
      <h3>Ask me anything about this book</h3>
      <p>Select text for focused questions or ask about the entire book.</p>
    </div>
  );
}
```

### 4.4 Success State

```typescript
// Rendered message with citations
<div className={styles.assistantMessage}>
  <ReactMarkdown>{message.content}</ReactMarkdown>
  {message.citations && message.citations.length > 0 && (
    <details>
      <summary>Sources ({message.citations.length})</summary>
      <ul>
        {message.citations.map((citation, idx) => (
          <li key={idx}>
            <strong>{citation.chapter}</strong> - {citation.section}
          </li>
        ))}
      </ul>
    </details>
  )}
</div>
```

---

## Section 5: Configuration and Deployment Setup

**Objective**: Configure environment variables and deploy

**Duration**: 30 minutes

**Deliverables**:
- Environment variable configuration
- Docusaurus config update
- Backend CORS setup
- Deployment instructions

### 5.1 Frontend Configuration

```javascript
// docusaurus.config.js - Add customFields
const config = {
  // ... existing config ...

  customFields: {
    chatbotBackendUrl: process.env.CHATBOT_BACKEND_URL || 'http://localhost:8000',
  },
};
```

**Environment file**:
```bash
# .env (frontend root)
CHATBOT_BACKEND_URL=http://localhost:8000
```

**Production (GitHub Secrets)**:
```bash
# GitHub repository settings → Secrets and variables → Actions
CHATBOT_BACKEND_URL=https://your-backend.railway.app
```

### 5.2 Backend CORS Configuration

```python
# backend_v3/config.py or backend/config.py
from typing import List

class Config:
    # ... existing config ...

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",              # Local development
        "https://mehreen676.github.io",       # Production GitHub Pages
    ]
```

**FastAPI app**:
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

### 5.3 Docusaurus Integration

```javascript
// src/theme/Root.js (Docusaurus theme wrapper)
import ChatWidget from '../components/ChatWidget';

export default function Root({ children }) {
  return (
    <>
      {children}
      <ChatWidget />
    </>
  );
}
```

**This makes chat widget available on ALL book pages**.

### 5.4 Deployment Steps

**Frontend (GitHub Pages)**:
```bash
# 1. Set environment variable in GitHub Secrets
# GitHub repo → Settings → Secrets → New repository secret
# Name: CHATBOT_BACKEND_URL
# Value: https://your-backend.railway.app

# 2. Build Docusaurus
npm run build

# 3. Deploy to GitHub Pages
npm run deploy
```

**Backend (Railway/Render)**:
```bash
# 1. Deploy backend_v3 to Railway/Render

# 2. Set environment variables in Railway/Render dashboard:
OPENAI_API_KEY=sk-...
QDRANT_URL=https://...
QDRANT_API_KEY=...
DATABASE_URL=postgresql://...@neon.tech/...

# 3. Verify health endpoint:
curl https://your-backend.railway.app/api/v1/health
```

---

## Integration Approach Summary

### Thin Frontend
- **Only UI components** - No AI, no embeddings, no vector search
- **State management** - React useState, sessionStorage
- **API client** - Fetch API with timeout, error handling
- **Environment-based** - Backend URL from config

### Backend-Driven
- **All AI logic** - ChatKit agent, retrieval, grounding
- **All storage** - Database, sessions, conversation history
- **All processing** - Embeddings, vector search, answer generation
- **Secure** - API keys never exposed to frontend

### Configuration
- **Frontend**: `CHATBOT_BACKEND_URL` environment variable
- **Backend**: CORS origins include GitHub Pages URL
- **Docusaurus**: `customFields.chatbotBackendUrl` in config
- **Deployment**: Separate deployments (GitHub Pages + Railway)

### No Authentication
- **Anonymous users** - No login required
- **Session-based** - UUID session IDs
- **No tracking** - No analytics, no user profiles
- **Privacy-first** - Conversation history in sessionStorage only

---

**Document Version**: 1.0.0
**Last Updated**: 2026-01-03
**Status**: Complete implementation sections
