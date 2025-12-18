# API Client Examples - RAG Backend

Quick reference for integrating with the RAG Backend API.

## Python Client

```python
import requests
import json

class RAGBackendClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def health_check(self) -> dict:
        """Check backend health"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()

    def query(self, query: str, mode: str = "full_book", session_id: str = None) -> dict:
        """Execute a RAG query"""
        payload = {
            "query": query,
            "mode": mode,
            "session_id": session_id
        }
        response = self.session.post(
            f"{self.base_url}/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def ingest(self, chapter: str, content: str, section: str = "Introduction") -> dict:
        """Ingest new content"""
        payload = {
            "chapter": chapter,
            "section": section,
            "content": content,
            "book_version": "v1.0"
        }
        response = self.session.post(
            f"{self.base_url}/ingest",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage
client = RAGBackendClient("https://rag-chatbot-backend.onrender.com")

# Health check
health = client.health_check()
print(f"Status: {health['status']}")

# Query
result = client.query("What is ROS 2?")
print(f"Answer: {result['answer']}")
print(f"Sources: {result['retrieved_chunks']}")

# Ingest
ingest_result = client.ingest(
    chapter="Module 1",
    section="Introduction",
    content="ROS 2 is a robotics middleware..."
)
print(f"Ingested: {ingest_result['ingested']} chunks")
```

## JavaScript/Node.js Client

```javascript
class RAGBackendClient {
  constructor(baseUrl, apiKey = null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  async query(query, mode = "full_book", sessionId = null) {
    const response = await fetch(`${this.baseUrl}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey && { "Authorization": `Bearer ${this.apiKey}` })
      },
      body: JSON.stringify({
        query,
        mode,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }

    return response.json();
  }

  async ingest(chapter, content, section = "Introduction") {
    const response = await fetch(`${this.baseUrl}/ingest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey && { "Authorization": `Bearer ${this.apiKey}` })
      },
      body: JSON.stringify({
        chapter,
        section,
        content,
        book_version: "v1.0"
      })
    });

    if (!response.ok) {
      throw new Error(`Ingest failed: ${response.statusText}`);
    }

    return response.json();
  }
}

// Usage
const client = new RAGBackendClient("https://rag-chatbot-backend.onrender.com");

// Health check
const health = await client.healthCheck();
console.log(`Status: ${health.status}`);

// Query
const result = await client.query("What is ROS 2?");
console.log(`Answer: ${result.answer}`);
console.log(`Chunks: ${result.retrieved_chunks.length}`);

// Ingest
const ingestResult = await client.ingest("Module 1", "ROS 2 content...");
console.log(`Ingested: ${ingestResult.ingested} chunks`);
```

## React Integration

```javascript
import { useState, useEffect } from 'react';

function RAGChatbot() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [health, setHealth] = useState(null);

  const API_URL = process.env.REACT_APP_API_URL ||
    "https://rag-chatbot-backend.onrender.com";

  useEffect(() => {
    // Check health on mount
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_URL}/health`);
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.error("Health check failed:", error);
    }
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          mode: "full_book"
        })
      });

      const data = await response.json();

      setMessages([
        ...messages,
        { type: "user", text: input },
        {
          type: "assistant",
          text: data.answer,
          chunks: data.retrieved_chunks,
          metadata: {
            tokens: data.tokens.total,
            latency: data.latency.total_ms
          }
        }
      ]);

      setInput("");
    } catch (error) {
      console.error("Query failed:", error);
      setMessages([...messages, {
        type: "error",
        text: "Failed to query backend"
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot">
      <div className="status">
        Status: {health?.status || "Checking..."}
      </div>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.type}`}>
            <p>{msg.text}</p>
            {msg.chunks && (
              <div className="sources">
                <h4>Sources:</h4>
                {msg.chunks.map((chunk, j) => (
                  <div key={j} className="chunk">
                    <strong>{chunk.chapter}</strong>
                    <p>{chunk.content.substring(0, 100)}...</p>
                  </div>
                ))}
              </div>
            )}
            {msg.metadata && (
              <small>
                Tokens: {msg.metadata.tokens} |
                Time: {msg.metadata.latency}ms
              </small>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleQuery}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Asking..." : "Ask"}
        </button>
      </form>
    </div>
  );
}

export default RAGChatbot;
```

## cURL Examples

### Health Check
```bash
curl https://rag-chatbot-backend.onrender.com/health
```

### Query Endpoint
```bash
curl -X POST https://rag-chatbot-backend.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is ROS 2?",
    "mode": "full_book"
  }'
```

### Ingest Content
```bash
curl -X POST https://rag-chatbot-backend.onrender.com/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "chapter": "Module 1: ROS 2 Basics",
    "section": "Introduction",
    "content": "ROS 2 is a robotics middleware that provides tools and libraries for building robot applications.",
    "book_version": "v1.0"
  }'
```

### With Authentication
```bash
# If using JWT token
curl -X GET https://rag-chatbot-backend.onrender.com/user/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# If using API key (if implemented)
curl -X GET https://rag-chatbot-backend.onrender.com/user/profile \
  -H "X-API-Key: YOUR_API_KEY"
```

## Error Handling

```python
import requests
from typing import Optional, Dict, Any

def query_with_retry(
    url: str,
    query: str,
    max_retries: int = 3,
    timeout: int = 30
) -> Optional[Dict[str, Any]]:
    """Query with retry logic"""

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{url}/query",
                json={"query": query, "mode": "full_book"},
                timeout=timeout
            )

            if response.status_code == 200:
                return response.json()

            elif response.status_code == 429:
                # Rate limited - wait and retry
                print(f"Rate limited, waiting... (attempt {attempt + 1})")
                time.sleep(2 ** attempt)
                continue

            elif response.status_code >= 500:
                # Server error - retry
                print(f"Server error {response.status_code}, retrying...")
                time.sleep(1)
                continue

            else:
                # Client error - don't retry
                print(f"Error {response.status_code}: {response.text}")
                return None

        except requests.Timeout:
            print(f"Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except requests.ConnectionError:
            print(f"Connection error on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return None

# Usage
result = query_with_retry(
    "https://rag-chatbot-backend.onrender.com",
    "What is ROS 2?"
)

if result:
    print(f"Success: {result['answer']}")
else:
    print("Failed after retries")
```

## Batch Processing

```python
import asyncio
from typing import List

async def batch_query(
    base_url: str,
    queries: List[str]
) -> List[dict]:
    """Process multiple queries concurrently"""

    async def query_async(query: str):
        # Use aiohttp for async requests
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/query",
                json={"query": query, "mode": "full_book"}
            ) as response:
                return await response.json()

    # Run all queries concurrently
    results = await asyncio.gather(*[
        query_async(q) for q in queries
    ])

    return results

# Usage
queries = [
    "What is ROS 2?",
    "How do I install ROS 2?",
    "What are ROS 2 nodes?"
]

results = asyncio.run(batch_query(
    "https://rag-chatbot-backend.onrender.com",
    queries
))

for query, result in zip(queries, results):
    print(f"Q: {query}")
    print(f"A: {result['answer']}\n")
```

## Caching Strategy

```python
from functools import lru_cache
from datetime import datetime, timedelta
import json

class CachedRAGClient:
    def __init__(self, base_url: str, cache_ttl_minutes: int = 60):
        self.base_url = base_url
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache = {}

    def query(self, query: str, use_cache: bool = True) -> dict:
        # Check cache
        if use_cache and query in self.cache:
            cached_result, timestamp = self.cache[query]
            if datetime.now() - timestamp < self.cache_ttl:
                print(f"Cache hit for: {query}")
                return cached_result

        # Query backend
        import requests
        response = requests.post(
            f"{self.base_url}/query",
            json={"query": query, "mode": "full_book"}
        )
        result = response.json()

        # Cache result
        self.cache[query] = (result, datetime.now())

        return result

    def clear_cache(self):
        self.cache.clear()

# Usage
client = CachedRAGClient("https://rag-chatbot-backend.onrender.com")

# First call - queries backend
result1 = client.query("What is ROS 2?")

# Second call - uses cache
result2 = client.query("What is ROS 2?")  # Cache hit!

# Clear cache when needed
client.clear_cache()
```

## Monitoring & Metrics

```python
import time
from typing import Callable, Any

def time_query(func: Callable) -> Callable:
    """Decorator to measure query time"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        print(f"Query took {elapsed:.2f}s")
        print(f"Tokens: {result['tokens']['total']}")
        print(f"Latency: {result['latency']['total_ms']:.0f}ms")

        return result

    return wrapper

@time_query
def query_backend(base_url: str, query: str):
    import requests
    response = requests.post(
        f"{base_url}/query",
        json={"query": query, "mode": "full_book"}
    )
    return response.json()

# Usage
result = query_backend(
    "https://rag-chatbot-backend.onrender.com",
    "What is ROS 2?"
)
```

## Integration Checklist

When integrating with the RAG Backend:

- [ ] Add error handling for network failures
- [ ] Implement retry logic with exponential backoff
- [ ] Add request timeouts
- [ ] Implement caching for repeated queries
- [ ] Monitor response times and costs
- [ ] Log all API calls for debugging
- [ ] Add rate limiting on client side
- [ ] Handle authentication tokens properly
- [ ] Validate API responses before using
- [ ] Add telemetry/metrics collection
- [ ] Test with production endpoints
- [ ] Document API integration for team
- [ ] Set up monitoring alerts
- [ ] Plan for API version upgrades

---

**API Endpoint:** https://rag-chatbot-backend.onrender.com
**API Docs:** https://rag-chatbot-backend.onrender.com/docs
**Status:** Ready for integration
