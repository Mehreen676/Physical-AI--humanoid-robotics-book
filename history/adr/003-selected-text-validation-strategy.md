# ADR-003: Selected-Text Validation Strategy (Hybrid Client+Server)

**Status**: Accepted
**Date**: 2025-12-16
**Feature**: RAG Chatbot Integration (#2)
**Deciders**: Technical Architecture Team
**Consulted**: Security Team, Product Team, QA

---

## Context

The RAG Chatbot supports a "Selected-Text Mode" where users highlight a passage and ask questions that must be answered using ONLY that selected text. This feature is critical for:

1. **Learning Verification**: Students can verify the chatbot understands a specific passage
2. **Scope Control**: Ensures answers are grounded in the selected content, not external knowledge
3. **Trust**: Reassures users that the chatbot isn't hallucinating beyond context
4. **Accuracy**: Prevents spurious answers from multi-source retrieval

The implementation strategy must balance:
- **Security**: Prevent users from tricking the chatbot into answering beyond selected text
- **Performance**: Minimize latency added by validation
- **User Experience**: Provide clear feedback if answer cannot be found in selection
- **Reliability**: Handle edge cases (very long text, code blocks, ambiguous passages)

Three strategies were considered:

1. **Client-Only**: Trust JavaScript to enforce constraint (fast, insecure)
2. **Server-Only**: Validate on backend after generation (secure, slower)
3. **Hybrid**: Client truncates/warns; server validates semantically (balanced)

---

## Decision

**We will implement a Hybrid Client+Server validation strategy:**

### Selected Solution

**Client-Side (JavaScript SDK)**:
- Capture selected text from page
- Truncate to 2000 tokens with user indication
- Display "Ask about this" button
- Send selected text to backend with query
- Show hint if response appears truncated

**Server-Side (FastAPI Backend)**:
- Receive selected text and generated response
- Perform semantic similarity validation
  - Embed response and selected text
  - Compute cosine similarity
  - Compare against threshold (0.7)
  - Extract keywords and check overlap
- If validation fails: Replace response with fallback message: "The selected text does not contain the answer."
- Log validation failures for monitoring

**Fallback Response**:
```
"The selected text does not contain the answer."
```

---

## Rationale

### Why Hybrid Over Pure Client or Server?

**Client-Only Approach (Trust JavaScript)**

```
User Selection → JavaScript Truncates → Send to Backend → Generate Response
```

**Pros**:
- Fast (no server validation latency)
- Simple implementation
- Good UX (immediate feedback)

**Cons**:
- **SECURITY FLAW**: Malicious user can modify JavaScript to send full book as "selected text"
- No enforcement of constraint
- Cannot verify response actually uses only selected text
- Educational integrity compromised

**Verdict**: INSUFFICIENT. Browser-level constraints are not secure.

---

**Server-Only Approach (Full Validation)**

```
User Selection → Send to Backend → Validate Selected Text Size → Generate Response → Validate Response
```

**Pros**:
- Secure: Server enforces all constraints
- No reliance on client behavior
- Complete control

**Cons**:
- **LATENCY**: Additional 200-300ms for semantic validation (embedding + similarity)
- Adds ~20% overhead to generation latency
- More complex error handling
- Slower user feedback on truncation

**Verdict**: FUNCTIONAL but adds unacceptable latency overhead.

---

**Hybrid Approach (Client + Server)**

```
User Selection → JavaScript Truncates (UX) → Send to Backend → Validate Semantically (Security) → Generate Response
```

**Pros**:
- **SECURITY**: Server validates that response is grounded in selected text
- **UX**: Client provides immediate truncation feedback
- **LATENCY**: Minimal overhead; validation runs in parallel with response formatting
- **RELIABILITY**: Catches both accidental (LLM reasoning) and intentional (malicious client) bypasses
- **MONITORING**: Failed validations logged for debugging/improvement

**Cons**:
- More complex implementation
- Requires semantic validation logic (embedding + similarity)
- Two points of validation to maintain

**Verdict**: OPTIMAL. Balances security, performance, and UX.

---

### Trade-off Comparison Matrix

| Aspect | Client-Only | Server-Only | Hybrid |
|--------|-------------|-------------|--------|
| **Security** | ❌ None | ✅ Strong | ✅✅ Strong |
| **Latency Impact** | ✅ 0ms | ⚠️ +200-300ms | ✅ +50-100ms |
| **Implementation Complexity** | ✅ Simple | ⚠️ Moderate | ⚠️ Moderate |
| **UX (Truncation Feedback)** | ✅✅ Fast | ⚠️ Slow | ✅✅ Fast |
| **Error Handling** | ❌ Limited | ✅✅ Comprehensive | ✅✅ Comprehensive |
| **Monitoring/Debugging** | ❌ None | ✅ Full | ✅ Full |
| **Scalability** | ✅ Best | ⚠️ Needs validation service | ✅ Good |
| **Educational Integrity** | ❌❌ Compromised | ✅ Assured | ✅ Assured |

---

## Consequences

### Positive

1. **Security**: Server-side validation ensures response uses only selected text; prevents bypass attempts
2. **Trust**: Users can verify answers are grounded in selections; builds confidence
3. **Learning Integrity**: Students cannot trick chatbot; educational credibility maintained
4. **UX**: Client-side truncation provides instant feedback; users know text was processed
5. **Monitoring**: Failed validations logged; reveals if LLM is reasoning beyond context
6. **Graceful Degradation**: If validation fails, clear fallback message instead of wrong answer

### Negative

1. **Implementation Complexity**: Requires semantic validation logic (2-3 additional components)
2. **Latency Overhead**: ~50-100ms added for semantic validation (acceptable but non-zero)
3. **Token Cost**: Each validation requires embedding the response (adds ~$0.000001 per query)
4. **Edge Cases**: Very long selections, code blocks, tables may have lower semantic similarity
5. **Threshold Tuning**: Similarity threshold (0.7) may need adjustments for domain-specific content

### Risks

- **Risk**: Semantic similarity threshold too strict; false negatives (valid answers rejected)
  - **Mitigation**: Start at 0.7; monitor failures; adjust to 0.6-0.8 based on data
- **Risk**: Semantic similarity threshold too loose; false positives (invalid answers accepted)
  - **Mitigation**: Include keyword overlap check; manual review of edge cases
- **Risk**: Very long selections exceed embedding token limits
  - **Mitigation**: Client truncates to 2000 tokens; server enforces max length

---

## Implementation Details

### Client-Side (JavaScript SDK)

```javascript
// chat-embed.js
class RagChatbot {
  async querySelectedText(query, selectedText) {
    // Step 1: Truncate to 2000 tokens with user indication
    const MAX_TOKENS = 2000;
    const estimatedTokens = selectedText.split(/\s+/).length * 1.3; // Rough estimate

    if (estimatedTokens > MAX_TOKENS) {
      selectedText = this._truncateToTokens(selectedText, MAX_TOKENS);
      this._showNotification(
        "⚠️ Selected text is long; truncated to 2000 tokens.",
        "info"
      );
    }

    // Step 2: Send to backend
    const response = await fetch(this.apiUrl + "/query-selected-text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        selected_text: selectedText,
        session_id: this.sessionId
      })
    });

    const data = await response.json();

    // Step 3: Display response with validation indicator
    if (!data.in_selected_text) {
      this._showMessage(
        data.response,
        "assistant",
        { isOutOfScope: true, confidence: 0 }
      );
    } else {
      this._showMessage(data.response, "assistant");
    }
  }

  _truncateToTokens(text, maxTokens) {
    const words = text.split(/\s+/);
    const truncatedWords = words.slice(0, Math.floor(maxTokens / 1.3));
    return truncatedWords.join(" ");
  }
}
```

### Server-Side (FastAPI Backend)

```python
# rag_service.py
from sentence_transformers import SentenceTransformer, util
import numpy as np

class SelectedTextValidator:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.similarity_threshold = 0.7
        self.keyword_overlap_threshold = 0.5

    def validate_response_in_context(
        self, response: str, selected_text: str
    ) -> bool:
        """
        Validate that generated response is grounded in selected text.

        Uses two methods:
        1. Semantic similarity (cosine similarity between embeddings)
        2. Keyword overlap (check if key terms from response are in text)

        Response is valid if EITHER:
        - Semantic similarity >= threshold, OR
        - Keyword overlap >= threshold
        """

        # Method 1: Semantic Similarity
        response_embedding = self.model.encode(response, convert_to_tensor=True)
        context_embedding = self.model.encode(selected_text, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(response_embedding, context_embedding).item()

        if similarity >= self.similarity_threshold:
            logger.info(f"Response validated via semantic similarity: {similarity:.3f}")
            return True

        # Method 2: Keyword Overlap
        response_keywords = self._extract_keywords(response)
        context_keywords = self._extract_keywords(selected_text)

        if len(response_keywords) == 0:
            return True  # Empty response; pass validation

        overlap = len(set(response_keywords) & set(context_keywords)) / len(
            response_keywords
        )

        if overlap >= self.keyword_overlap_threshold:
            logger.info(f"Response validated via keyword overlap: {overlap:.2%}")
            return True

        # Validation failed
        logger.warn(
            f"Response failed validation: similarity={similarity:.3f}, overlap={overlap:.2%}"
        )
        return False

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key concepts from text (using simple heuristics)."""
        import nltk
        from nltk.corpus import stopwords

        # Simple approach: extract nouns and important terms
        words = text.lower().split()
        stopwords_set = stopwords.words("english")
        keywords = [
            w.strip(".,!?;:") for w in words
            if w not in stopwords_set and len(w) > 3
        ]
        return keywords

@app.post("/query-selected-text")
async def query_selected_text(request: QuerySelectedTextRequest):
    """Process query using ONLY selected text with validation."""

    # Step 1: Validate input
    if not request.query or not request.selected_text:
        raise HTTPException(status_code=400, detail="query and selected_text required")

    # Step 2: Enforce max length
    if len(request.selected_text) > 10000:
        request.selected_text = request.selected_text[:10000]
        truncated_warning = "Selected text truncated to 10,000 characters."
    else:
        truncated_warning = None

    # Step 3: Generate response using ONLY selected text
    try:
        response = generation_agent.generate(
            query=request.query,
            context=request.selected_text,
            selected_text_mode=True
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        response = "The selected text does not contain the answer."
        in_selected_text = False
    else:
        # Step 4: Validate response is grounded in selected text
        validator = SelectedTextValidator()
        in_selected_text = validator.validate_response_in_context(
            response, request.selected_text
        )

        if not in_selected_text:
            response = "The selected text does not contain the answer."

    # Step 5: Store in database
    message = Message(
        session_id=request.session_id,
        user_message=request.query,
        assistant_response=response,
        mode="selected_text",
        selected_text=request.selected_text[:500],  # Store excerpt
        source_chunk_ids=None,
        in_selected_text=in_selected_text
    )
    db.add(message)
    db.commit()

    # Step 6: Return response
    return {
        "response": response,
        "in_selected_text": in_selected_text,
        "sources": [{"type": "selected_text", "excerpt": request.selected_text[:200]}],
        "session_id": request.session_id,
        "truncation_warning": truncated_warning
    }
```

---

## Edge Cases & Handling

### Case 1: Very Long Selected Text

**Handling**:
- Client truncates to 2000 tokens; shows warning
- Server enforces max 10,000 characters
- Validation may fail due to information loss; fallback to "not in text"

### Case 2: Selected Text Contains Code/Tables

**Handling**:
- Preserve markdown/formatting in truncation
- Keyword extraction handles code (extracts variable names, function calls)
- Semantic model trained on diverse text; handles code reasonably

### Case 3: Ambiguous Selection (Multiple Meanings)

**Handling**:
- User query provides disambiguation
- Validation checks if query+response align with selection
- Semantic similarity may be lower but still valid

### Case 4: Selection Spans Multiple Paragraphs

**Handling**:
- Treated as single context block
- Validation uses entire concatenated text
- Works well for related concepts across paragraphs

### Case 5: User Selects Part of Code Block

**Handling**:
- Preserve code structure during truncation
- Keyword extraction works on code (variable names, functions)
- May require manual testing to validate

---

## Monitoring & Metrics

**Track Per Query**:
- `response_similarity_score`: Semantic similarity value (0-1)
- `keyword_overlap_ratio`: Keyword overlap percentage (0-1)
- `validation_passed`: Boolean (response grounded in selected text)
- `latency_validation_ms`: Time to validate response

**Weekly Dashboard**:
- `validation_success_rate`: % of responses that pass validation (target: 95%+)
- `false_negative_rate`: % of valid responses rejected (target: <5%)
- `false_positive_rate`: % of invalid responses accepted (target: <1%)
- `avg_similarity_score`: Average semantic similarity (target: >0.7)

**Monthly Review**:
- Adjust similarity threshold based on false positive/negative rates
- Review edge cases logged in failures
- Evaluate if keyword overlap check needed

---

## Testing Strategy

### Unit Tests

```python
def test_validation_valid_response():
    """Response should pass if grounded in selected text."""
    validator = SelectedTextValidator()
    selected = "ROS 2 supports distributed systems."
    response = "ROS 2 enables distributed systems."
    assert validator.validate_response_in_context(response, selected)

def test_validation_invalid_response():
    """Response should fail if not in selected text."""
    validator = SelectedTextValidator()
    selected = "ROS 2 supports distributed systems."
    response = "Kubernetes provides container orchestration."
    assert not validator.validate_response_in_context(response, selected)

def test_validation_edge_case_code():
    """Code blocks should be handled correctly."""
    selected = "def factorial(n): return 1 if n==0 else n*factorial(n-1)"
    response = "factorial function computes factorial"
    assert validator.validate_response_in_context(response, selected)
```

### Integration Tests

```python
def test_selected_text_endpoint_valid():
    """Valid response through endpoint."""
    response = client.post(
        "/query-selected-text",
        json={
            "query": "What is this?",
            "selected_text": "ROS 2 is a robotics middleware.",
            "session_id": "test-session"
        }
    )
    assert response.json()["in_selected_text"] == True

def test_selected_text_endpoint_invalid():
    """Invalid response (out of scope)."""
    response = client.post(
        "/query-selected-text",
        json={
            "query": "What is AI?",
            "selected_text": "ROS 2 is a robotics middleware.",
            "session_id": "test-session"
        }
    )
    assert "does not contain the answer" in response.json()["response"]
```

---

## Future Improvements

1. **Threshold Tuning**: Fine-tune similarity/overlap thresholds based on real-world data
2. **Domain-Specific Models**: Use domain-specific embeddings (trained on technical textbook data)
3. **Explainability**: Show user why response was rejected (e.g., "Response mentions 'Kubernetes' which isn't in selection")
4. **Interactive Refinement**: Suggest related sections if answer not in selection

---

## References

- Sentence Transformers: https://www.sbert.net/
- Semantic Similarity: https://arxiv.org/abs/1908.10084
- Specification: `specs/2-rag-chatbot-integration/spec.md` (Selected-Text Requirements)
- Textbook: `docusaurus_textbook/docs/08-appendix/rag-chatbot-integration.md` (Selected-Text QA Logic section)
