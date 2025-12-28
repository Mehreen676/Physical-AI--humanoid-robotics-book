# Implementation Plan: RAG Agent with OpenAI Integration

**Branch**: `005-rag-agent-openai` | **Date**: 2025-12-28 | **Spec**: [specs/005-rag-agent-openai/spec.md](spec.md)
**Input**: Feature specification from `specs/005-rag-agent-openai/spec.md`

**Note**: This plan defines the architecture for a single-file agent.py implementation using OpenAI Agents SDK with Qdrant retrieval.

## Summary

Build an intelligent conversational agent using OpenAI's Agent framework that retrieves context from the humanoid robotics textbook via Qdrant vector database (populated by Spec 001) and Cohere embeddings (from Spec 002). The agent will answer user queries with accurate, contextual responses grounded in textbook content. Implementation constrained to single agent.py file for MVP clarity and hackathon demo purposes.

## Technical Context

**Language/Version**: Python 3.8+ (matches existing backend stack from Specs 001-002)
**Primary Dependencies**:
  - OpenAI SDK (agents framework)
  - Cohere (embeddings: 1024-dim via embed-english-v3.0)
  - Qdrant-client (vector search)
  - python-dotenv (environment configuration)

**Storage**: Qdrant Cloud collection "rag_embedding" (read-only access, pre-populated by Spec 001)
**Testing**: Manual validation with test_queries.json (from Spec 002); 5+ diverse queries covering all 8 textbook modules
**Target Platform**: Backend Python service, runs locally or deployed to cloud (Linux/Windows compatible)
**Project Type**: Single agent.py file (simplicity for MVP)
**Performance Goals**:
  - Query response time: < 5 seconds (95th percentile)
  - Retrieval latency: < 3 seconds including Cohere embedding + Qdrant search

**Constraints**:
  - Single agent.py file (no multi-file architecture)
  - No persistent conversation history (stateless per query)
  - No advanced tool chaining (single retrieval tool only)
  - Must work with existing Qdrant collection (read-only)

**Scale/Scope**:
  - 5+ concurrent user queries supported
  - 24 indexed chunks (from Spec 001 ingestion of 18/19 pages)
  - Designed for hackathon demo (not production)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle 1: Technical Accuracy and Source Verification** ✅
- Agent responses will cite retrieved textbook content directly (no hallucination)
- All responses are grounded in existing Spec 001 vectors populated from official Docusaurus content
- No generation of unverified technical claims

**Principle 2: Clarity for Target Audience** ✅
- Single agent.py file ensures transparency and clarity for judges
- Natural language responses designed for robotics engineers/AI students
- Code will be well-documented with clear function purposes

**Principle 3: Reproducibility** ✅
- Agent uses existing Qdrant collection and Cohere API (both reproducible, spec-driven)
- Implementation fully contained in single file for easy review and testing
- Will include setup instructions and validation steps in README

**Principle 4: Theory-Practice Integration** ✅
- Agent demonstrates RAG retrieval workflow in practice (from Specs 001-002)
- Responses are tied to textbook content with proper attribution

**Principle 5: Standardized Citations** ✅
- Retrieved chunks include source URLs (APA-compatible)
- Agent will cite textbook sections explicitly in responses

**Technology Stack Compliance** ✅
- Uses OpenAI Agents SDK (specified in constitution)
- Integrates with Qdrant (vector database as per tech stack)
- Leverages Cohere embeddings (from Spec 001)

**Gate Status**: ✅ PASS - All principles aligned with constitution. Agent focuses on retrieval and response synthesis, not content generation. All dependencies verified.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── agent.py              # Single-file agent implementation (NEW - this feature)
├── main.py               # Embedding pipeline (Spec 001)
├── retrieve.py           # Retrieval testing (Spec 002)
├── .env                  # Configuration (credentials, URLs, API keys)
├── test_queries.json     # Test queries for validation
├── requirements.txt      # Python dependencies
└── README.md             # Updated with agent usage instructions

# Agent.py structure (single file):
# - Agent initialization with OpenAI Agents SDK
# - Retrieval tool (Cohere encode → Qdrant search → response format)
# - Response generation (synthesize context from retrieved chunks)
# - Error handling & logging
# - CLI interface for testing (optional)
```

**Structure Decision**: Single agent.py file in backend/ directory. This satisfies the constraint of "single agent.py file for simplicity" while leveraging existing retrieve.py functions where possible. Agent will import retrieve functions (encode_query, search_qdrant) as a library or reimplement them self-contained for independence.

## Phase 0: Research & Exploration

**Status**: ✅ COMPLETE - No significant unknowns; context fully defined by Specs 001-002

**Key Findings**:
- OpenAI Agents SDK: Mature framework with built-in tool use pattern
- Cohere embeddings: Already validated in Spec 002 (encode_query with input_type="search_query")
- Qdrant retrieval: Already tested in Spec 002 (search_qdrant function works correctly)
- Agent pattern: Standard retrieval-augmented generation (RAG) with OpenAI agents

**No NEEDS CLARIFICATION items**: All technical decisions already determined by previous specs and architecture decisions provided by user.

## Phase 1: Design & Contracts

### Data Model

**Query Request**
- `query_text`: str (3-5000 characters)
- `k`: int (default 5, range 1-20)
- `include_context`: bool (default True)

**Retrieved Chunk** (from Qdrant)
- `rank`: int (1 to k)
- `similarity_score`: float (0.0 to 1.0)
- `content`: str (text of chunk)
- `source_url`: str (original document URL)
- `chunk_position`: int (position in original document)
- `created_at`: str (ISO 8601 timestamp)
- `chunk_size`: int (character count)

**Agent Response**
- `query`: str (original user query)
- `response`: str (synthesized natural language answer)
- `sources`: List[{url, snippet}] (cited chunks)
- `confidence`: float (0.0-1.0, based on similarity scores)
- `execution_time_ms`: int (elapsed time)
- `status`: str ("success" or "error")

### API Contract

**Single Query Handler** (CLI interface):
```
Input: python agent.py "What is humanoid robotics?"
Output: JSON with query, response, sources, confidence, execution_time_ms
```

**Batch Query Handler** (for validation):
```
Input: python agent.py --batch test_queries.json --k 5
Output: Aggregated results with statistics
```

### Implementation Phases

**Phase 1A: Agent Initialization** (1-2 days)
- Set up OpenAI Agents SDK
- Configure Cohere embeddings
- Connect to Qdrant collection
- Implement retrieval tool

**Phase 1B: Response Synthesis** (1-2 days)
- Design prompt template for agent
- Implement context injection from retrieved chunks
- Add source attribution

**Phase 1C: Testing & Validation** (1 day)
- Run 5+ test queries (all 8 textbook modules)
- Measure response time and relevance
- Document results for judges

## Implementation Architecture

### Agent Flow

```
User Query
    ↓
[Cohere Embed] - encode_query(query, input_type="search_query")
    ↓
[Qdrant Search] - search_qdrant(embedding, k=5)
    ↓
[Format Context] - Extract content + metadata
    ↓
[OpenAI Agent] - Synthesize response with LLM
    ↓
[Return Response] - JSON with query, response, sources, confidence
```

### Tool Definition for OpenAI Agent

```
Tool Name: retrieve_from_textbook
Description: Search the robotics textbook for relevant information
Input: query text (string)
Output: Top-5 relevant chunks with sources and similarity scores
```

### Error Handling

- Query validation: Reject if < 3 chars or > 5000 chars
- Cohere API errors: Exponential backoff (from Spec 001)
- Qdrant connection errors: Clear error message with diagnostics
- Empty results: Return "No relevant content found" with confidence 0.0
- Timeout: 10-second limit on total response time

### Logging Strategy

- Log all queries with timestamp
- Log retrieval results (chunk count, similarity scores)
- Log response generation (synthesis prompts, LLM output)
- Write to agent_results.log with rotation

## Dependencies & Integration

**Direct Dependencies from Specs 001-002**:
- Qdrant collection "rag_embedding" (read-only)
- Cohere API (via existing COHERE_API_KEY)
- QDRANT_URL and QDRANT_API_KEY from .env

**New Dependencies**:
- OpenAI Python SDK (openai >= 1.0.0)
- Additional pip packages: None (reuses existing)

**Configuration** (.env):
```
OPENAI_API_KEY=sk-...        # Required for agent
COHERE_API_KEY=...           # From Spec 001
QDRANT_URL=...              # From Spec 001
QDRANT_API_KEY=...          # From Spec 001
COLLECTION_NAME=rag_embedding  # From Spec 002
```

## Success Criteria Verification

| Criterion | How to Verify | Status |
|-----------|---------------|--------|
| Agent initializes | Check logs for "Agent ready" message | Design phase |
| Qdrant connection | Agent confirms collection access | Design phase |
| Cohere encoding | Query generates 1024-dim embedding | Design phase |
| Top-k retrieval | Returns 5 chunks with scores | Design phase |
| Response synthesis | LLM generates coherent answer | Design phase |
| All 8 modules covered | Test queries for each module | Design phase |
| < 5s response time | Measure batch of 12 queries | Testing phase |
| Citations included | Each response cites sources | Design phase |
| Error handling | Test invalid inputs, API failures | Testing phase |
| Deployable | Works locally with .env creds | Testing phase |

## Complexity Tracking

No complexity violations. This feature is constrained to single agent.py file and uses proven patterns from Specs 001-002. No additional infrastructure or multi-file architecture introduced.
