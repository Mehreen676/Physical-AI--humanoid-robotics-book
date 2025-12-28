---
id: 9
title: Phase 6 Task Generation and Planning
stage: green
date: 2025-12-28
surface: agent
model: claude-haiku-4-5-20251001
feature: 005-rag-agent-openai
branch: 005-rag-agent-openai
user: User
command: /sp.tasks continue phase 6
labels: ["phase6", "tasks", "p2-optional", "openai-synthesis"]
links:
  spec: specs/005-rag-agent-openai/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-rag-agent-openai/tasks.md
  - backend/agent.py
tests:
  - Phase 6 independent test criteria (T029): 5+ queries through OpenAI synthesis
  - Validation: Response coherence, source citation, question addressing
---

## Prompt

**User Request:** `/sp.tasks continue phase 6`

**Context:**
- Spec 005 implementation in progress on branch `005-rag-agent-openai`
- MVP scope (Phases 1-5, P1 priority) fully complete with 100% success rate
- Phase 6 (User Story 4 - P2 Optional) is an enhancement for natural language response synthesis
- User wants to continue with Phase 6 task planning and definition

**Goal:**
1. Generate detailed, actionable tasks for Phase 6 (T026-T030)
2. Map User Story 4 requirements to specific implementation tasks
3. Define independent test criteria for Phase 6 completion
4. Ensure tasks are granular enough for LLM execution
5. Clarify P2 priority and MVP scope boundaries

## Response snapshot

**Phase 6 Task Generation Complete:**

### 1. Context Analysis ✓

**User Story 4 Requirements (from spec.md):**
- Generate natural language responses incorporating retrieved context
- Synthesize responses that cite sources explicitly
- Provide coherent, grammatical answers
- Directly address user questions
- Respect context (no hallucination beyond retrieved chunks)

**Technical Foundation (from plan.md):**
- OpenAI SDK available (optional, ready for integration)
- Qdrant collection populated and tested (Phases 1-5)
- Cohere embeddings functional (Phases 1-5)
- run_query() function proven with 100% success rate (Phase 5)

**MVP vs Enhancement:**
- MVP (Phases 1-5): Retrieval + raw context extraction ✓ COMPLETE
- Enhancement (Phase 6): Natural language synthesis (P2 optional)
- Judges can evaluate raw retrieval results independently
- Synthesis adds sophistication but not blocking

### 2. Task Breakdown (T026-T030) ✓

**T026: Retrieval Tool Wrapper (Implementation)**
- Create function `retrieve_from_textbook(query: str, k: int)` in backend/agent.py
- Wraps existing `run_query()` for OpenAI agent tool invocation
- Returns structured JSON for agent consumption
- File: backend/agent.py (add after run_query function)

**T027: Response Synthesis Prompt Design (Architecture)**
- Design system prompt guiding OpenAI agent behavior
- Key elements:
  - Context-aware synthesis (use provided chunks only)
  - Explicit source citation (URLs or section references)
  - Conversational tone (friendly, accessible to judges)
  - Fallback behavior (if no good chunks, say so honestly)
- File: backend/agent.py (add as constant/configuration)

**T028: OpenAI Agent Client Creation (Integration)**
- Initialize OpenAI Agents SDK client
- Register `retrieve_from_textbook` as tool
- Load system prompt from T027
- Handle API key from .env (OPENAI_API_KEY)
- File: backend/agent.py (add new function `create_openai_agent()`)

**T029: Response Quality Validation (Testing)**
- Execute 5+ test queries through OpenAI synthesis
- Validation criteria:
  - Responses grammatically correct
  - Sources explicitly cited (URLs in response)
  - Questions directly addressed
  - No hallucination (synthesis stays within retrieved chunks)
- Log results to: backend/synthesis_validation_results.log (JSON format)
- File: backend/agent.py (add `validate_synthesis()` or use CLI flag)

**T030: Synthesis vs Retrieval Comparison (Documentation)**
- Side-by-side comparison of Phase 3 (raw retrieval) vs Phase 6 (synthesis)
- Document with 3-5 example queries:
  - Query text
  - Raw retrieval response (chunks)
  - Synthesized response (OpenAI)
  - Quality comparison notes
- File: backend/SYNTHESIS_COMPARISON.md (new file)

### 3. Independent Test Criteria ✓

**Phase 6 Completion Validation (T029):**

**Input**: 5+ diverse test queries covering:
- Fundamentals: "What is humanoid robotics?"
- Software: "How does ROS 2 work?"
- Hardware: "Explain bipedal walking control"
- Perception: "What sensors do humanoid robots use?"
- AI/ML: "How does sim-to-real transfer work?"

**Acceptance Criteria:**
1. ✓ All 5+ queries successfully synthesized (no errors)
2. ✓ Responses grammatically correct (readable by judges)
3. ✓ Each response cites at least 1 source (URL or section)
4. ✓ Responses address the user's question (relevance)
5. ✓ No hallucination (synthesis within retrieved context)

**Deliverable**: synthesis_validation_results.log with:
- Query text
- Synthesized response
- Citation(s) used
- Quality check (PASS/FAIL)
- Timestamp and execution time

### 4. MVP Boundary Clarification ✓

**Phase 1-5 (MVP) = COMPLETE:**
- Agent retrieves context from textbook ✓
- Raw chunks returned with similarity scores ✓
- Full batch test with 12 queries passed ✓
- Judges can evaluate retrieval quality independently ✓

**Phase 6 (Enhancement) = OPTIONAL:**
- Adds natural language synthesis layer
- Enhances user experience (conversational)
- Not required for MVP demonstration
- Can be added if time permits (~2-3 hours estimated)

**Why P2 Priority:**
- MVP already demonstrates RAG core (retrieval)
- Natural language synthesis is enhancement, not requirement
- Judges can evaluate raw retrieval results directly
- Synthesis can be added post-hackathon

### 5. Task Execution Order (P2) ✓

**Sequential Dependency:**
1. T026 (Create tool wrapper) → Prerequisites for T028
2. T027 (Design prompt) → Input for T028
3. T028 (Create agent client) → Uses T026 + T027
4. T029 (Validate synthesis) → Tests T028 output
5. T030 (Document comparison) → Final documentation

**Estimated Effort:**
- T026: 30 min (wrapper function)
- T027: 30 min (prompt engineering)
- T028: 45 min (agent integration)
- T029: 30 min (validation testing)
- T030: 20 min (documentation)
- **Total: ~2.5 hours** (can be done in parallel with other work)

### 6. Implementation Guidance ✓

**File Structure:**
- All Phase 6 code goes in `backend/agent.py` (single-file constraint)
- No new imports beyond what's in requirements.txt (openai SDK only)
- Maintain existing code organization (add functions after Phase 5 functions)

**Key Functions to Add:**
```python
# T026: Retrieval tool wrapper
def retrieve_from_textbook(query: str, k: int = 5) -> Dict:
    """Wrapper for OpenAI agent tool use"""
    # Call existing run_query() and format for agent

# T027: System prompt (as module constant)
SYNTHESIS_SYSTEM_PROMPT = """You are an assistant..."""

# T028: OpenAI agent creation
def create_openai_agent() -> Agent:
    """Initialize OpenAI Agents SDK with retrieval tool"""
    # Create client, register tool, return agent

# T029: Validation (CLI mode)
# Add --synthesis flag to main() CLI interface
```

**Testing Approach:**
- Use existing test_queries.json (12 queries)
- Select 5+ for synthesis validation
- Log results to JSON for judge review
- Compare raw retrieval vs synthesis output

## Outcome

- ✅ Impact: Phase 6 tasks fully defined and actionable. Each task (T026-T030) is specific enough for implementation without further clarification. MVP boundary clear - Phase 6 is optional enhancement.
- 🧪 Tests: Independent test criteria defined (T029) with 5+ validation queries and explicit acceptance criteria (coherence, citations, relevance)
- 📁 Files: Tasks updated in specs/005-rag-agent-openai/tasks.md with detailed descriptions, implementation guidance provided for each task
- 🔁 Next prompts: User can now execute `/sp.implement` for Phase 6 if desired, or proceed directly to submission with MVP (Phases 1-5) complete.
- 🧠 Reflection: Phase 6 properly scoped as P2 optional enhancement. MVP (retrieval only) is complete and production-ready. Phase 6 adds conversational UX but not required for core RAG functionality. ~2.5 hours estimated to implement if user chooses to proceed.

## Evaluation notes (flywheel)

- Failure modes observed: None blocking. Phase 6 optional status means failure doesn't impact MVP submission.
- Graders run and results (PASS/FAIL):
  - Phase 6 Task Definition: PASS (5 tasks clearly specified)
  - Independent Test Criteria: PASS (measurable validation checklist defined)
  - MVP Boundary Clarity: PASS (P2 optional clearly documented)
  - File Structure: PASS (single-file constraint maintained)
- Prompt variant (if applicable): None - single task generation path
- Next experiment (smallest change to try): If user has extra time, implement T026 first (30-min wrapper) to enable T028. Low-risk way to start Phase 6 without full commitment.
