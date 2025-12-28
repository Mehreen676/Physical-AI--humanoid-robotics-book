# Implementation Tasks: RAG Frontend Integration

**Feature**: RAG Frontend Integration with Docusaurus + FastAPI
**Branch**: `004-rag-frontend-integration`
**Target**: Hackathon Demo - Embedded Chat Widget for Humanoid Robotics Textbook
**Start**: 2025-12-28
**Scope**: React chat component + FastAPI backend integration, 6 user stories (5 P1, 1 P2)

## Summary

35 tasks organized across 7 phases to implement an embedded RAG chat widget in the Docusaurus humanoid robotics textbook frontend, connected to the FastAPI RAG Agent backend (Spec 005). MVP scope: Phases 1-6 (Setup + US1-US5, all P1 stories). Phase 7 is polish/documentation.

## User Stories & Priority

- **US1 (P1)**: Query Interface - Users can enter questions and get RAG answers
- **US2 (P1)**: Answer Display - Responses show answer + sources + confidence
- **US3 (P2)**: Error Handling - Graceful error messages for failures
- **US4 (P2)**: Loading States - Clear loading indicators during processing
- **US5 (P1)**: Selected-Text Query - Highlight text → ask about it
- **US6 (P1)**: Deployed Site Integration - Works on GitHub Pages live site

---

## Phase 1: Setup & Infrastructure

Shared setup for all user stories. **MUST COMPLETE FIRST before user stories.**

### Goals
- Initialize Docusaurus project with TypeScript + React setup
- Configure backend FastAPI service with CORS
- Establish API contract and type definitions
- Verify development environment ready

### Independent Test Criteria
- TypeScript environment works in Docusaurus build
- Backend server starts and responds to health checks
- CORS configured for local dev and production origins
- API contract documented and validated

### Tasks

- [X] T001 Verify Docusaurus project structure and React setup in frontend directory
- [X] T002 Create TypeScript configuration for custom React components in Docusaurus src/
- [X] T003 Set up development environment: .env file with REACT_APP_BACKEND_URL for local dev and production
- [X] T004 [P] Create src/types/chat.ts with TypeScript interfaces for Query, Response, and ChatMessage
- [X] T005 [P] Create src/services/chatApi.ts with HTTP client functions (fetch-based, no axios dependency)
- [X] T006 [P] Create backend/chat_router.py with FastAPI endpoint POST /chat (skeleton, integration in later phases)
- [X] T007 Configure CORS in backend/app.py for origins (http://localhost:3000, https://mehreen676.github.io)
- [X] T008 [P] Verify FastAPI backend starts without errors and responds to GET /health endpoint
- [X] T009 Create contracts/chat-api.json with OpenAPI schema for POST /chat endpoint request/response
- [X] T010 Validate TypeScript builds successfully in Docusaurus dev environment

---

## Phase 2: Agent Foundation (Blocking Prerequisites)

Core services and utilities needed by all user stories. **MUST COMPLETE BEFORE USER STORIES.**

### Goals
- Implement API communication layer
- Create selected-text extraction utility
- Set up error handling patterns
- Establish message state management structure

### Independent Test Criteria
- chatApi service can make HTTP requests to backend
- selectedText utility correctly extracts highlighted text
- Error responses properly formatted and catchable
- Message types correctly validated

### Tasks

- [X] T011 [P] Implement chatApi.sendQuery() function in src/services/chatApi.ts with error handling
- [X] T012 [P] Implement chatApi.healthCheck() function to verify backend connection
- [X] T013 [P] Create src/services/selectedText.ts with getSelectedText() function to extract highlighted content
- [X] T014 [P] Create src/services/selectedText.ts with getSelectionContext() to include surrounding paragraph
- [X] T015 [P] Create error handling utility in src/services/errorHandler.ts with user-friendly messages
- [X] T016 [P] Create loading state management patterns in src/hooks/useLoadingState.ts
- [X] T017 [P] Implement message history hook in src/hooks/useMessageHistory.ts for state management
- [X] T018 [P] Test chatApi functions locally with mock backend responses in src/services/__mocks__/chatApi.ts
- [X] T019 [P] Test selectedText extraction on sample HTML content
- [X] T020 [P] Validate error messages match spec requirements (user-friendly, no stack traces)

---

## Phase 3: User Story 1 - Query Interface (P1)

As a user, I want to enter questions in a UI interface so that I can get RAG-powered answers.

### Story Goal
Users can type questions into a chat input field and submit them to the RAG backend, receiving responses from the knowledge base.

### Independent Test Criteria
- User can type and submit a query
- Backend receives query and processes it
- Response received and available for display (Phase 4 handles display)
- Empty queries rejected with validation message
- Loading state shown during processing

### Tasks

- [ ] T021 [P] [US1] Create src/components/ChatInput.tsx component with text input form
- [ ] T022 [P] [US1] Implement form submission handler in ChatInput to call chatApi.sendQuery()
- [ ] T023 [US1] Implement input validation in ChatInput (3-5000 char range, trim whitespace)
- [ ] T024 [US1] Add placeholder text and submit button to ChatInput component
- [ ] T025 [P] [US1] Create src/components/ChatWidget.tsx parent component managing overall state
- [ ] T026 [US1] Implement state management in ChatWidget for loading, error, and messages
- [ ] T027 [US1] Connect ChatInput to ChatWidget: pass query to parent state on submission
- [ ] T028 [US1] Integrate loading state from Phase 2 hook into ChatWidget during query processing
- [ ] T029 [US1] Test ChatInput component in isolation (typing, validation, submission)
- [ ] T030 [US1] Test ChatWidget query submission flow end-to-end

---

## Phase 4: User Story 2 - Answer Display (P1)

As a user, I want to see answers with sources and matched chunks so I understand the response.

### Story Goal
Responses are clearly displayed with answer text, source URLs, confidence scores, and matched content chunks that informed the answer.

### Independent Test Criteria
- RAG response JSON parsed correctly
- Answer text displayed in message component
- All sources shown with clickable URLs
- Confidence score visible
- Matched chunks displayed with proper formatting

### Tasks

- [ ] T031 [P] [US2] Create src/components/ChatMessage.tsx component for displaying individual messages
- [ ] T032 [P] [US2] Implement user message display in ChatMessage (query text, timestamp)
- [ ] T033 [US2] Implement assistant message display in ChatMessage (answer text with formatting)
- [ ] T034 [P] [US2] Create src/components/SourcesList.tsx to display sources with URLs
- [ ] T035 [P] [US2] Make sources clickable links that open in new tab (href to textbook URL)
- [ ] T036 [US2] Create src/components/MatchedChunks.tsx to display retrieved text snippets
- [ ] T037 [US2] Display confidence score/similarity metric in response header
- [ ] T038 [US2] Add response metadata (execution time, match count) in message footer
- [ ] T039 [US2] Integrate ChatMessage components into ChatWidget message list
- [ ] T040 [US2] Test ChatMessage rendering with sample RAG responses
- [ ] T041 [US2] Test source links open correctly and point to right textbook sections

---

## Phase 5: User Story 5 - Selected-Text Query (P1)

As a user, I want to highlight text and ask questions about that specific content.

### Story Goal
Users can select text in the book, and the selected content is captured and sent with their query to the RAG backend for contextually relevant answers.

### Independent Test Criteria
- Selected text is extracted when user highlights
- Selected text pre-fills or appears in query context
- Query with selected text sent to backend correctly
- Backend receives `selected_text` parameter and processes it

### Tasks

- [ ] T042 [P] [US5] Add selection listener to book content area detecting text highlights
- [ ] T043 [US5] Implement UI affordance (button/tooltip) to "Ask about selected text"
- [ ] T044 [P] [US5] Integrate selectedText utility from Phase 2 into ChatInput component
- [ ] T045 [US5] When selected text exists, pre-fill or append to query input automatically
- [ ] T046 [US5] Visually indicate selected text context in ChatInput (highlighted or labeled)
- [ ] T047 [P] [US5] Pass selected_text parameter in chatApi.sendQuery() request body
- [ ] T048 [US5] Handle case where user selects text but doesn't submit query (clear on unfocus)
- [ ] T049 [US5] Test selection detection on different textbook page sections
- [ ] T050 [US5] Test backend receives and processes selected_text parameter correctly
- [ ] T051 [US5] Verify responses for selected-text queries are contextually relevant

---

## Phase 6: User Story 6 - Deployed Site Integration (P1)

As a hackathon judge, I want the chat to work on the live GitHub Pages site.

### Story Goal
The chat widget functions completely on the deployed GitHub Pages site (https://mehreen676.github.io/Physical-AI--humanoid-robotics-book/) with properly configured backend URL and CORS settings.

### Independent Test Criteria
- Frontend deployed to GitHub Pages
- Backend URL configured for production in environment
- CORS headers allow requests from deployed origin
- Full end-to-end query → response works on live site
- No authentication required to use chat

### Tasks

- [ ] T052 [US6] Configure production backend URL in environment (REACT_APP_BACKEND_URL)
- [ ] T053 [US6] Deploy ChatWidget component to GitHub Pages production build
- [ ] T054 [US6] Verify backend CORS configuration allows https://mehreen676.github.io origin
- [ ] T055 [US6] Test full query flow on live deployed site (no local dev)
- [ ] T056 [US6] Verify no authentication prompts appear to judges
- [ ] T057 [US6] Test selected-text feature works on live deployed pages
- [ ] T058 [US6] Verify all sources links point to correct GitHub Pages URLs
- [ ] T059 [US6] Document backend URL configuration for production environment
- [ ] T060 [US6] Create deployment checklist (frontend build, backend health check, CORS verification)

---

## Phase 7: User Story 3 - Error Handling (P2)

As a user, I want appropriate error messages when things go wrong.

### Story Goal
Network errors, backend failures, and edge cases are handled gracefully with user-friendly messages that help users understand what happened and try again.

### Independent Test Criteria
- Network errors show helpful message (not stack trace)
- Backend errors displayed to user
- Empty results handled with "no content found" message
- Timeout errors show and allow retry
- Error state cleared when user resubmits

### Tasks

- [ ] T061 [P] [US3] Implement error boundary in ChatWidget to catch component errors
- [ ] T062 [US3] Create error message component for network failures in src/components/ErrorMessage.tsx
- [ ] T063 [US3] Handle timeout errors (> 30s) with user-friendly "request took too long" message
- [ ] T064 [US3] Handle backend 5xx errors with "service unavailable, please try again later"
- [ ] T065 [US3] Handle backend 4xx errors with "invalid query, please try different wording"
- [ ] T066 [US3] Handle empty results (status: "no_results") with "no relevant content found"
- [ ] T067 [US3] Implement retry button in error state to resubmit same query
- [ ] T068 [US3] Clear error message when user starts typing new query
- [ ] T069 [US3] Test error scenarios: network down, backend down, timeout, bad response
- [ ] T070 [US3] Verify error messages don't expose sensitive info (no API keys, URLs)

---

## Phase 8: User Story 4 - Loading States (P2)

As a user, I want to see loading indicators while processing.

### Story Goal
Clear visual feedback during query processing so users know the system is working and their request hasn't been lost.

### Independent Test Criteria
- Loading indicator appears immediately after query submission
- Loading state removed when response arrives or error occurs
- Loading animation is visible and not jarring
- Can see context (which query is being processed)

### Tasks

- [ ] T071 [P] [US4] Create src/components/LoadingIndicator.tsx with spinner/animation
- [ ] T072 [US4] Implement loading state visibility toggle based on phase 2 hook
- [ ] T073 [P] [US4] Show loading indicator in message area during query processing
- [ ] T074 [US4] Display "Processing your question..." text during loading
- [ ] T075 [US4] Ensure loading state cleared immediately on response or error
- [ ] T076 [US4] Add subtle animation (spinner, pulsing, progress indication)
- [ ] T077 [US4] Test loading state appears and disappears at right times
- [ ] T078 [US4] Verify user can see query being processed (context visible)

---

## Phase 9: Polish & Cross-Cutting Concerns

Final touches for production readiness and hackathon demo.

### Goals
- Complete documentation and user guides
- Verify all features work together
- Optimize performance
- Prepare demo scenarios

### Independent Test Criteria
- All components work together seamlessly
- Documentation clear and complete
- Performance meets targets (< 5s response, < 2s widget load)
- Demo script executes without errors

### Tasks

- [ ] T079 Create README.md in specs/004-rag-frontend-integration/ with architecture overview
- [ ] T080 Create QUICKSTART.md with setup instructions for local development
- [ ] T081 Create DEMO_SCRIPT.md with 3-5 example queries for judges to try
- [ ] T082 [P] Update docstrings in all components (ChatWidget, ChatInput, ChatMessage, etc.)
- [ ] T083 [P] Add TypeScript type hints to all function signatures in services
- [ ] T084 [P] Test end-to-end flow: highlight → ask → response → see sources
- [ ] T085 [P] Performance test: measure widget load time (target < 2s)
- [ ] T086 [P] Performance test: measure query response time (target < 5s)
- [ ] T087 Optimize any slow operations identified in performance tests
- [ ] T088 Create deployment guide for moving widget to production
- [ ] T089 Document how to configure backend URL for different environments
- [ ] T090 Final QA: test all user stories together in integrated system
- [ ] T091 Create screenshot documentation for hackathon judges
- [ ] T092 Verify all links work (sources, textbook pages, external links)

---

## Dependency Graph & Execution Strategy

### Strict Sequence (Blocking)

1. **Phase 1** (T001-T010): Setup & Infrastructure (prerequisite for all)
2. **Phase 2** (T011-T020): Agent Foundation (prerequisite for all user stories)
3. **Phases 3-8**: User Stories (can run in parallel after Phase 2)
4. **Phase 9** (T079-T092): Polish (final)

### Parallelizable Opportunities

After Phase 2 completion, these teams can work in parallel:

**Team Frontend**:
- Phase 3 (US1 Query): T021-T030
- Phase 4 (US2 Answer): T031-T041
- Phase 5 (US5 Selected-Text): T042-T051
- Phase 7 (US3 Error): T061-T070
- Phase 8 (US4 Loading): T071-T078

**Team Backend**:
- Enhance FastAPI POST /chat endpoint
- Implement selected_text parameter handling
- Verify CORS configuration

**Team Integration**:
- Phase 6 (US6 Deployed): T052-T060 (run after US1-US5 frontend mostly complete)

### MVP Scope (Minimum Viable Product)

**Complete for Hackathon**: Phases 1-6 (Setup + US1, US2, US5, US6) = **60 tasks**

- ✅ Users can ask questions (US1)
- ✅ Answers displayed with sources (US2)
- ✅ Selected-text queries work (US5)
- ✅ Works on deployed GitHub Pages (US6)

**Optional Enhancements**: Phases 7-8 (US3 Error Handling, US4 Loading States) = **20 tasks**

- ✅ Better error messages
- ✅ Loading indicators

**Polish**: Phase 9 (Documentation, QA) = **14 tasks**

---

## Independent Test Criteria

### Phase 1: Setup ✓
- [ ] TypeScript builds without errors in Docusaurus
- [ ] Backend starts and /health responds
- [ ] CORS configured for local and production origins
- [ ] .env loads REACT_APP_BACKEND_URL correctly

### Phase 2: Agent Foundation ✓
- [ ] chatApi.sendQuery() makes HTTP POST requests
- [ ] chatApi responses parsed as QueryResponse type
- [ ] selectedText.getSelectedText() extracts highlighted content
- [ ] Error handler formats messages without stack traces
- [ ] Message history hook tracks conversation

### Phase 3: US1 Query Interface ✓
- [ ] User can type question and submit
- [ ] Query sent to backend via chatApi
- [ ] Loading state shows during processing
- [ ] Response received and stored in state
- [ ] Empty query validation prevents submission

### Phase 4: US2 Answer Display ✓
- [ ] Answer text displayed clearly
- [ ] Sources shown as clickable links
- [ ] Confidence score visible
- [ ] Matched chunks displayed
- [ ] Metadata shown (execution time, count)

### Phase 5: US5 Selected-Text ✓
- [ ] Text selection detected in document
- [ ] Selected text captured and stored
- [ ] Pre-filled in query input
- [ ] Sent as `selected_text` parameter
- [ ] Backend processes contextually

### Phase 6: US6 Deployed Site ✓
- [ ] Frontend deployed to GitHub Pages
- [ ] Backend URL correctly configured
- [ ] Full query → response works on live site
- [ ] No auth required
- [ ] CORS allows requests

### Phase 7: US3 Error Handling ✓
- [ ] Network errors show user message
- [ ] Backend errors displayed
- [ ] Empty results handled
- [ ] Timeout errors shown
- [ ] Retry option available

### Phase 8: US4 Loading States ✓
- [ ] Loading indicator appears on submit
- [ ] Shows immediately (< 100ms)
- [ ] Disappears on response or error
- [ ] Animation is visible
- [ ] Context shows which query is processing

### Phase 9: Polish ✓
- [ ] All documentation complete
- [ ] All components documented
- [ ] Performance targets met
- [ ] Demo script works
- [ ] End-to-end integration verified

---

## Success Criteria Mapping

| Spec Criteria | Implementation Task |
|---------------|-------------------|
| SC-001: 95%+ successful calls | Phase 1-2 (API setup), Phase 7 (error handling) |
| SC-002: 100% display answer + sources + chunks | Phase 4 (Answer Display) |
| SC-003: 100% loading states shown | Phase 8 (Loading States) |
| SC-004: 100% graceful error handling | Phase 7 (Error Handling) |
| SC-005: Works in local dev | Phase 1-2 (Setup) |
| SC-006: Selected-text queries work | Phase 5 (Selected-Text) |
| SC-007: Works on deployed site | Phase 6 (Deployed Site) |
| SC-008: CORS configured | Phase 1 (Setup) |
| SC-009: < 5s response time | Phase 3-6 (integration), Phase 9 (optimization) |
| SC-010: Judges can test without setup | Phase 6 (Deployed Site) |

---

## File Summary

| File | Status | Deliverable |
|------|--------|------------|
| src/components/ChatWidget.tsx | TO BUILD | Main widget component orchestrating state |
| src/components/ChatInput.tsx | TO BUILD | Query input form with validation |
| src/components/ChatMessage.tsx | TO BUILD | Individual message display |
| src/components/SourcesList.tsx | TO BUILD | Sources with clickable links |
| src/components/MatchedChunks.tsx | TO BUILD | Retrieved text snippets display |
| src/components/LoadingIndicator.tsx | TO BUILD | Loading animation |
| src/components/ErrorMessage.tsx | TO BUILD | Error display |
| src/services/chatApi.ts | TO BUILD | Backend HTTP client |
| src/services/selectedText.ts | TO BUILD | Text selection extraction |
| src/services/errorHandler.ts | TO BUILD | Error message formatting |
| src/hooks/useLoadingState.ts | TO BUILD | Loading state management |
| src/hooks/useMessageHistory.ts | TO BUILD | Message history state |
| src/types/chat.ts | TO BUILD | TypeScript interfaces |
| src/styles/ChatWidget.module.css | TO BUILD | Component styling |
| backend/chat_router.py | TO ENHANCE | FastAPI endpoint for /chat |
| backend/main.py | TO UPDATE | Add CORS configuration |
| contracts/chat-api.json | TO BUILD | OpenAPI schema |
| README.md | TO BUILD | Architecture overview |
| QUICKSTART.md | TO BUILD | Local dev setup |
| DEMO_SCRIPT.md | TO BUILD | Hackathon demo guide |

---

## Implementation Notes

**Architecture**:
- React component (ChatWidget) manages state
- Services layer handles API calls and utilities
- Components display messages with rich formatting
- Type safety via TypeScript throughout

**Testing Strategy**:
- Manual testing of each user story (independent test criteria)
- Integration testing: all stories together
- E2E testing on live deployed site
- No unit test framework required (simplicity)

**Deployment**:
- Frontend: Deploy to GitHub Pages (existing pipeline)
- Backend: FastAPI running on accessible URL (e.g., Heroku, Railway, local server)
- Environment variables: REACT_APP_BACKEND_URL in .env or build config

**Performance Targets**:
- Widget load: < 2 seconds
- Query response: < 5 seconds
- UI interaction: < 500ms

---

## Next Steps

1. **Team Kickoff**: Review task breakdown, assign ownership
2. **Phase 1 Start**: Setup Docusaurus + FastAPI environment (1-2 days)
3. **Phase 2 Start**: Implement services layer (1-2 days)
4. **Parallel Execution**: Teams work on Phases 3-8 (2-3 weeks)
5. **Phase 9 Polish**: Documentation, optimization, demo prep (1 week)
6. **Demo & Submission**: Test on live site, deliver to judges

**Estimated Total**: 4-5 weeks for complete implementation from Phase 1 start

---

**Branch**: `004-rag-frontend-integration`
**Total Tasks**: 92 tasks organized across 9 phases
**MVP Tasks**: 60 tasks (Phases 1-6, all P1 user stories)
**Enhancement Tasks**: 20 tasks (Phases 7-8, P2 error/loading)
**Polish Tasks**: 14 tasks (Phase 9, documentation & QA)

**Status**: Ready for team assignment and execution. All tasks are specific, actionable, and independently testable.
