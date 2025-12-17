# API Reference: RAG Chatbot Backend

Complete API documentation for the RAG Chatbot REST endpoints.

## Base URL

```
Development:  http://localhost:8000
Staging:      https://staging-api.example.com
Production:   https://api.example.com
```

## Authentication

### API Key Authentication

For admin endpoints, include API key in header:

```bash
curl -H "X-API-Key: rk_prod_your_key_here" \
     https://api.example.com/ingest
```

### Bearer Token (JWT)

For user endpoints:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://api.example.com/sessions
```

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Query Endpoint (Full Book)

**POST** `/query`

Search the entire textbook and generate an answer.

**Request Body:**
```json
{
  "query": "What is ROS 2?",
  "session_id": "session-123",
  "mode": "full_book"
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | User question (max 500 chars) |
| `session_id` | string | No | Session ID for history tracking |
| `mode` | string | No | Query mode: "full_book" or "selected_text" (default: "full_book") |

**Response:**
```json
{
  "answer": "ROS 2 is a middleware that provides...",
  "sources": [
    {
      "chapter": "Chapter 2: Introduction to ROS",
      "section": "2.1 ROS 1 vs ROS 2",
      "content": "ROS 2 is the next generation of ROS...",
      "relevance_score": 0.92
    },
    {
      "chapter": "Chapter 3: ROS Architecture",
      "section": "3.2 ROS 2 Improvements",
      "content": "ROS 2 improves upon ROS 1 by...",
      "relevance_score": 0.87
    }
  ],
  "session_id": "session-123",
  "latency_ms": 3245,
  "tokens_used": {
    "embedding": 45,
    "generation": 156
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Generated answer to the query |
| `sources` | array | Relevant passages from textbook |
| `session_id` | string | Session ID for follow-up queries |
| `latency_ms` | number | Time taken to generate response (milliseconds) |
| `tokens_used` | object | Token usage for billing |

**Error Responses:**

```json
// Invalid query (too long)
{
  "detail": "Query exceeds maximum length of 500 characters"
}

// Rate limit exceeded
{
  "detail": "Rate limit exceeded: 10 queries per minute"
}

// Service unavailable
{
  "detail": "OpenAI API temporarily unavailable"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is humanoid locomotion?",
    "session_id": "session-123"
  }'
```

---

### 3. Query with Selected Text

**POST** `/query-selected-text`

Answer a question using ONLY the provided text.

**Request Body:**
```json
{
  "query": "What are the challenges mentioned?",
  "selected_text": "Humanoid robots must balance bipedal locomotion with upper-body manipulation tasks.",
  "session_id": "session-123"
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | User question (max 500 chars) |
| `selected_text` | string | Yes | User-selected passage (max 10,000 chars) |
| `session_id` | string | No | Session ID for history tracking |

**Response:**
```json
{
  "answer": "The selected text mentions the challenge of...",
  "mode": "selected_text",
  "used_selected_text": true,
  "session_id": "session-123",
  "latency_ms": 2145
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/query-selected-text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does this explain?",
    "selected_text": "ROS 2 uses a distributed middleware architecture..."
  }'
```

---

### 4. Content Ingestion

**POST** `/ingest`

Add new content to the knowledge base (admin only).

**Authentication:** Requires X-API-Key header

**Request Body:**
```json
{
  "chapter": "Chapter 5: Advanced Robotics",
  "content": "This chapter covers advanced topics including...",
  "section": "5.1 Computer Vision",
  "metadata": {
    "version": "1.0",
    "author": "Dr. Smith"
  }
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chapter` | string | Yes | Chapter name |
| `content` | string | Yes | Content to ingest (auto-chunked) |
| `section` | string | No | Section name |
| `metadata` | object | No | Custom metadata |

**Response:**
```json
{
  "chunks_created": 12,
  "documents_created": 1,
  "vectors_stored": 12,
  "total_tokens": 2345,
  "estimated_cost": 0.002
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: rk_prod_your_key_here" \
  -d '{
    "chapter": "Chapter 5",
    "content": "Your content here...",
    "section": "5.1"
  }'
```

---

### 5. Get Chat Session

**GET** `/sessions/{session_id}`

Retrieve chat history for a session.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session identifier |

**Response:**
```json
{
  "session_id": "session-123",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:45:00Z",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "What is ROS 2?",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "ROS 2 is...",
      "timestamp": "2024-01-15T10:30:05Z",
      "sources": [...]
    }
  ],
  "message_count": 2
}
```

**Example Request:**
```bash
curl http://localhost:8000/sessions/session-123
```

---

### 6. List Sessions

**GET** `/sessions`

Get list of all sessions for current user.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Max sessions to return |
| `offset` | integer | 0 | Pagination offset |

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "session-123",
      "created_at": "2024-01-15T10:30:00Z",
      "message_count": 5,
      "first_message": "What is ROS 2?"
    }
  ],
  "total": 15,
  "limit": 10,
  "offset": 0
}
```

**Example Request:**
```bash
curl "http://localhost:8000/sessions?limit=20"
```

---

### 7. Delete Session

**DELETE** `/sessions/{session_id}`

Delete a chat session.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session to delete |

**Response:**
```json
{
  "status": "deleted",
  "session_id": "session-123"
}
```

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/sessions/session-123
```

---

### 8. OpenAPI Documentation

**GET** `/docs`

Interactive API documentation (Swagger UI).

Access at: `http://localhost:8000/docs`

**GET** `/redoc`

Alternative API documentation (ReDoc).

Access at: `http://localhost:8000/redoc`

---

## Rate Limits

API rate limits:

```
Per Session:  10 queries per minute
Per IP:       1000 queries per day
```

**Rate Limit Headers:**

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1705320600
```

**When rate limited (HTTP 429):**

```json
{
  "detail": "Rate limit exceeded: 10 queries per minute"
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing/invalid API key) |
| 429 | Too many requests (rate limited) |
| 500 | Server error (unexpected) |

### Error Examples

**Invalid Query:**
```json
{
  "detail": "Query exceeds maximum length of 500 characters"
}
```

**Rate Limited:**
```json
{
  "detail": "Rate limit exceeded: 10 queries per minute"
}
```

**API Key Invalid:**
```json
{
  "detail": "Invalid API key"
}
```

---

## Request/Response Examples

### Example 1: Simple Question

**Request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is ROS 2?"}'
```

**Response:**
```json
{
  "answer": "ROS 2 is the second generation of ROS...",
  "sources": [
    {
      "chapter": "Chapter 2",
      "section": "2.1 ROS 2 Overview",
      "relevance_score": 0.95
    }
  ],
  "latency_ms": 3200
}
```

### Example 2: Multi-turn Conversation

**Query 1:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the advantages of ROS 2?"}'
```

**Query 2 (using session):**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does that compare to ROS 1?",
    "session_id": "session-abc-123"
  }'
```

Bot remembers previous context and provides relevant follow-up answer.

### Example 3: Selected Text Query

**Request:**
```bash
curl -X POST http://localhost:8000/query-selected-text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main concepts here?",
    "selected_text": "ROS 2 introduces distributed middleware, improved real-time performance, and better security."
  }'
```

**Response:**
```json
{
  "answer": "The main concepts mentioned are: 1) Distributed middleware, 2) Improved real-time performance, 3) Better security",
  "mode": "selected_text",
  "used_selected_text": true
}
```

---

## Performance Guidelines

### Typical Latencies

| Operation | Latency | Notes |
|-----------|---------|-------|
| Embedding | 50-100ms | OpenAI API |
| Vector Search | 100-200ms | Qdrant |
| LLM Generation | 2-5s | GPT-4o |
| **Total Query** | **3-6s** | p95 latency |

### Cost Estimates

```
Per Query Cost: $0.001 - $0.005 (roughly)

Components:
- Embedding: ~$0.00002 per 1K tokens
- LLM: ~$0.005 per 1K input, $0.015 per 1K output
- Infrastructure: ~$0.0001 per query
```

---

## SDK Usage

### Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "rk_prod_your_key"

def query_rag(question: str, session_id: str = None):
    """Query the RAG chatbot."""
    response = requests.post(
        f"{BASE_URL}/query",
        json={
            "query": question,
            "session_id": session_id
        }
    )
    return response.json()

def ingest_content(chapter: str, content: str):
    """Add content to knowledge base."""
    response = requests.post(
        f"{BASE_URL}/ingest",
        headers={"X-API-Key": API_KEY},
        json={
            "chapter": chapter,
            "content": content
        }
    )
    return response.json()

# Usage
response = query_rag("What is humanoid robotics?")
print(response["answer"])
```

### JavaScript Client Example

```javascript
const BASE_URL = "http://localhost:8000";

async function queryRAG(question, sessionId = null) {
  const response = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      query: question,
      session_id: sessionId
    })
  });
  return response.json();
}

// Usage
const result = await queryRAG("What is ROS 2?");
console.log(result.answer);
```

---

## Support

- **Documentation**: https://docs.example.com
- **Issues**: https://github.com/your-org/rag-chatbot/issues
- **Email**: support@example.com
- **Status Page**: https://status.example.com

---

**Last Updated:** 2024-01-15
**API Version:** 1.0.0
**Stability:** Stable
