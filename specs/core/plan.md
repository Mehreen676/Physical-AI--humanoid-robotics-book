# Physical AI & Humanoid Robotics Interactive Textbook - Implementation Plan

**Document**: Plan (PLAN)
**Status**: Draft → Ready for Review
**Last Updated**: 2025-12-24
**Owner**: Lead Architect (@SpecArchitect)
**Governance**: Spec-Kit Plus methodology, Constitution v1.0.0

---

## 1. Executive Summary

This implementation plan details the phased approach to building the "Physical AI & Humanoid Robotics" interactive textbook using Docusaurus, RAG chatbot, and bonus features. The plan optimizes for:

✅ **Parallelization**: Multiple subagents working simultaneously on independent work streams
✅ **Iterative Delivery**: Core MVP (Phase 1-2) ready early; bonus features (Phase 3-4) incrementally
✅ **Risk Mitigation**: Identify critical paths and blockers early
✅ **Quality Gates**: Testing and validation integrated at each phase
✅ **Bonus Maximization**: Reusable skills and Spec-Kit Plus artifacts prioritized throughout

---

## 2. Project Phases Overview

| Phase | Name | Duration | Focus | Key Subagents |
|-------|------|----------|-------|---|
| **0** | Foundation & Setup | Parallel | Project infrastructure, tool setup, database schema | @SpecArchitect, @BackendEngineer, @FrontendEngineer |
| **1** | Core MVP | Parallel | Custom Docusaurus theme, 12 chapters, basic RAG chatbot | @FrontendEngineer, @Educator, @BackendEngineer |
| **2** | User Authentication & Personalization | Parallel | Better-Auth integration, user profiles, difficulty toggle | @AuthPersonalizer, @FrontendEngineer, @Educator |
| **3** | Urdu Translation & Localization | Sequential (after Phase 1) | Full Urdu translation, glossary, per-chapter toggle | @Translator, @Educator, @FrontendEngineer |
| **4** | Advanced Features & Polish | Parallel | Adaptive learning, recommendation engine, analytics | @AuthPersonalizer, @BackendEngineer, @FrontendEngineer |
| **5** | Testing & QA | Parallel (starts mid-Phase 1) | Unit, integration, E2E, accessibility, performance | @Reviewer |
| **6** | Deployment & Launch | Sequential (final) | CI/CD setup, GitHub Pages, backend hosting, monitoring | @BackendEngineer, @FrontendEngineer |

---

## 3. Detailed Phase Breakdown

### PHASE 0: Foundation & Setup (Week 1)

**Objective**: Establish project infrastructure, databases, and development environment.

**Parallel Workstreams**:

#### 0.1 Repository & Project Structure
**Assigned**: @SpecArchitect (orchestrator), @FrontendEngineer, @BackendEngineer
**Deliverables**:
- [ ] Initialize Docusaurus 3.x project (no defaults)
- [ ] Set up FastAPI project structure
- [ ] Create `.github/workflows/` for CI/CD
- [ ] Establish `.env.local` template (no secrets in git)
- [ ] Create directory structure: `specs/`, `history/`, `.claude/`, `docusaurus-site/`, `backend/`, `tests/`

**Acceptance Criteria**:
- Git repo initialized, `.gitignore` configured (secrets excluded)
- Docusaurus builds without errors
- FastAPI server runs locally (port 8000)
- All directories follow Spec-Kit Plus structure

#### 0.2 Database Setup
**Assigned**: @BackendEngineer
**Deliverables**:
- [ ] Create Neon Postgres database (managed serverless)
- [ ] Write database schema (users, chat_sessions, chapters, progress, preferences)
- [ ] Create Alembic migrations
- [ ] Initialize Qdrant vector DB (cloud or self-hosted)
- [ ] Write seed data (chapters metadata)

**Acceptance Criteria**:
- Neon DB accessible via connection string
- All tables created with indexes
- Migrations run successfully
- Qdrant collection created and ready for vectors

#### 0.3 Docusaurus Custom Theme Foundation
**Assigned**: @FrontendEngineer
**Deliverables**:
- [ ] Disable Docusaurus default theme in `docusaurus.config.js`
- [ ] Create custom `<Layout>` component (React)
- [ ] Set up Tailwind CSS (config, init, custom colors)
- [ ] Create design system (colors, typography, spacing)
- [ ] Build navbar skeleton (logo, placeholder menu, theme toggle)
- [ ] Build sidebar skeleton (hierarchical, collapsible)
- [ ] Build footer skeleton

**Acceptance Criteria**:
- Custom theme renders (no default Docusaurus styling)
- Tailwind CSS working
- Dark mode toggle works
- Responsive layout (desktop/tablet/mobile breakpoints)
- No console errors or warnings

#### 0.4 FastAPI Backend Skeleton
**Assigned**: @BackendEngineer
**Deliverables**:
- [ ] Initialize FastAPI project with project structure (main.py, routes/, services/)
- [ ] Create Pydantic models for requests/responses
- [ ] Set up logging (structured JSON logging)
- [ ] Create error handling middleware
- [ ] Add CORS configuration
- [ ] Create database connection pool (SQLAlchemy + Neon)
- [ ] Create Qdrant client initialization

**Acceptance Criteria**:
- FastAPI server starts on port 8000
- `GET /health` returns 200 (health check)
- Logging configured (JSON format)
- Database connection tested
- CORS allows localhost and GitHub Pages origin

#### 0.5 Better-Auth Configuration
**Assigned**: @AuthPersonalizer
**Deliverables**:
- [ ] Set up Better-Auth (signup, signin flows)
- [ ] Configure email provider (for verification)
- [ ] Create user table integration
- [ ] Set up JWT token generation
- [ ] Create session management

**Acceptance Criteria**:
- Better-Auth endpoints functional
- Email verification flow works
- JWT tokens generated and validated
- Sessions persist to database

**Critical Dependencies**:
- Phase 0 must complete before Phase 1 begins
- Database schema must be finalized before content indexing (Phase 1.3)
- Docusaurus theme foundation must be solid (performance base for Phase 1)

**Blockers to Watch**:
- Neon Postgres account setup (delay: request creation, might take 1-2 days)
- Qdrant cloud setup (delay: account creation)
- GitHub Actions secrets configuration (API keys, DB credentials)

---

### PHASE 1: Core MVP (Weeks 2-5)

**Objective**: Build functional textbook with custom theme, 12 chapters, and basic RAG chatbot. This phase enables core learning experience.

**Work Streams** (Parallel):

#### 1.1 Custom Docusaurus Components & Styling
**Assigned**: @FrontendEngineer
**Duration**: Weeks 2-3
**Deliverables**:
- [ ] Complete navbar (logo, Module 1-4 dropdown, search input, user menu, theme toggle)
- [ ] Complete sidebar (Chapter tree, collapsible, active indicator, progress %)
- [ ] Complete footer (links, copyright, social)
- [ ] Chapter page template (MDX layout with standard sections)
- [ ] Reusable component library:
  - Buttons (primary, secondary, link)
  - Cards (chapter preview, feature)
  - Alerts (success, warning, error, info)
  - Code blocks (syntax highlighting, copy button)
  - Typography (Heading, Paragraph, Link)
  - Form inputs (TextInput, Select, Checkbox)
  - Loading spinner, toast notifications, modal

**Acceptance Criteria**:
- All components render correctly
- Responsive on desktop (1200px), tablet (768px), mobile (375px)
- Dark mode works for all components
- Accessibility: WCAG 2.1 AA (focus indicators, color contrast, semantic HTML)
- Code quality: TypeScript strict mode, ESLint passing
- Lighthouse score: 80+ (desktop), 75+ (mobile)

#### 1.2 Chapter Content Writing
**Assigned**: @Educator (primary), @RoboticsExpert (review), @CodeExampleGenerator, @DiagramDescriber (supplementary)
**Duration**: Weeks 2-5 (parallel, 3 chapters/week)
**Deliverables**:
- [ ] Module 1: ROS 2 Fundamentals (5 chapters)
  - 1.1: Introduction to ROS 2
  - 1.2: Installation & Setup
  - 1.3: Nodes, Topics, Services, Actions
  - 1.4: ROS 2 CLI Tools & Debugging
  - 1.5: Packages & Workspaces
- [ ] Module 2: Simulation Environments (5 chapters)
  - 2.1: Gazebo Fundamentals
  - 2.2: URDF & Robot Modeling
  - 2.3: Gazebo Plugins & Sensors
  - 2.4: Unity Robotics Integration (optional alternative)
  - 2.5: Advanced Simulation & Scenarios
- [ ] Module 3: NVIDIA Isaac Sim (5 chapters)
  - 3.1: Isaac Sim Basics
  - 3.2: Robot Import & Configuration
  - 3.3: ROS 2 Integration in Isaac
  - 3.4: Physics-Based Manipulation
  - 3.5: Perception & Computer Vision
- [ ] Module 4: Vision-Language Models (5 chapters)
  - 4.1: VLM Foundations
  - 4.2: VLMs with Robotic Perception
  - 4.3: Prompt Engineering for Robotics
  - 4.4: LLMs for Robot Planning
  - 4.5: Multimodal Learning & Future Directions

**Each Chapter Includes**:
- Learning outcomes (3-5, specific, measurable)
- Clear explanations with analogies
- 2-3 code examples (Python, tested, copy-paste ready)
- Diagrams/visuals (Mermaid or ASCII descriptions)
- Hands-on exercise (step-by-step)
- Quiz (5 MCQs, misconception-aligned distractors)
- Key takeaways
- Further reading (links to ROS 2 docs, research papers)

**Acceptance Criteria**:
- 12 chapters written, all sections complete
- Learning outcomes aligned to Bloom's levels
- Code examples tested and runnable
- Diagrams generated (Mermaid/ASCII)
- Quizzes created (5 questions/chapter, reviewed by @Educator)
- No spelling/grammar errors
- @RoboticsExpert review: ✅ scientifically accurate
- Content follows Chapter Template (standard structure)
- All in MDX format (valid syntax)

**Parallelization Strategy**:
- Week 2: Chapters 1.1-1.3, 2.1-2.2
- Week 3: Chapters 1.4-1.5, 2.3-2.5
- Week 4: Chapters 3.1-3.3, 4.1-4.2
- Week 5: Chapters 3.4-3.5, 4.3-4.5

#### 1.3 RAG Chatbot Content Indexing & Pipeline
**Assigned**: @BackendEngineer
**Duration**: Weeks 2-5 (concurrent with content writing, initial setup Week 2, then incremental)
**Deliverables**:
- [ ] Chapter ingestion pipeline (read .mdx files)
- [ ] Chunking logic (split chapters into 300-500 token chunks, overlap=100)
- [ ] Embedding generation (OpenAI `text-embedding-3-small`)
- [ ] Qdrant indexing (upsert vectors with metadata: module, chapter, section)
- [ ] Retrieval pipeline (semantic search, top-5 results)
- [ ] Ranking/filtering (confidence scoring, grounding validation)
- [ ] Generation endpoint (GPT-4 with system prompt + context)
- [ ] Chat history storage (Neon Postgres)
- [ ] Cost optimization (cache embeddings, batch requests)

**API Endpoints**:
```
POST /api/chatbot/query
  Request: { message, selected_text?, user_id?, context? }
  Response: { response, sources, confidence, session_id }

GET /api/chatbot/history?session_id=...
  Response: [{ role, content, timestamp }, ...]
```

**Acceptance Criteria**:
- All chapters indexed (vectors in Qdrant)
- Query latency: < 5 seconds (p95)
- Responses grounded in course content
- Confidence scores computed
- Chat history persists
- Rate limiting: 10 req/min per user
- Error handling: 400 (bad input), 429 (rate limit), 500 (error)
- Logging: all queries and responses logged

**Critical Dependency**: Chapter content must be finalized before indexing (ready Week 5)

#### 1.4 Authentication Integration
**Assigned**: @AuthPersonalizer
**Duration**: Weeks 2-3
**Deliverables**:
- [ ] Signup form (email, password, verification)
- [ ] Signin form (email, password, remember me)
- [ ] Logout (clear session)
- [ ] Password reset flow
- [ ] Session persistence (JWT in secure storage)
- [ ] Protected API routes (auth middleware)

**Frontend Components**:
- LoginForm (email, password input, validation)
- SignupForm (email, password, confirm, terms)
- LogoutButton

**Backend Routes**:
```
POST /api/auth/signup
POST /api/auth/signin
POST /api/auth/logout
PUT /api/auth/reset-password
```

**Acceptance Criteria**:
- Signup works (email verification required)
- Signin works (JWT issued, stored securely)
- Protected routes return 401 if not authenticated
- Session persists across page reloads
- Logout clears session
- Password hashed (bcrypt), never plaintext

#### 1.5 Frontend-Backend Integration
**Assigned**: @FrontendEngineer, @BackendEngineer
**Duration**: Weeks 3-5
**Deliverables**:
- [ ] Fetch chapter content from API (GET /api/content/chapter/{id})
- [ ] Display chapters in custom theme
- [ ] Login/logout UI integration
- [ ] API error handling (display user-friendly messages)
- [ ] Loading states (spinners while fetching)
- [ ] CORS configuration (allow frontend → backend)

**Acceptance Criteria**:
- Chapters render with proper styling
- API calls succeed (200 status)
- Errors handled gracefully
- No console errors
- Network requests logged (for debugging)

**Dependencies**:
- Phase 0 (infrastructure) ✅ prerequisite
- Database schema (Phase 0.2) ✅ prerequisite
- Chapter content (Phase 1.2) ✅ prerequisite

**Blockers to Watch**:
- OpenAI API rate limits (handle gracefully)
- Qdrant indexing latency (might spike with 12 chapters)
- Content writing delays (Educator bottleneck) → parallelize aggressively

---

### PHASE 2: User Authentication & Personalization (Weeks 4-6, parallel with Phase 1.2-1.5)

**Objective**: Enable user profiles, content personalization (difficulty toggle, bookmarking, progress tracking), and preference persistence.

**Work Streams**:

#### 2.1 User Profiling & Onboarding
**Assigned**: @AuthPersonalizer, @FrontendEngineer
**Duration**: Week 4
**Deliverables**:
- [ ] Onboarding form (software level, hardware level, learning goal)
- [ ] Profile storage (Neon: software_level, hardware_level, learning_goal)
- [ ] Profile update endpoint (PUT /api/user/profile)
- [ ] Profile fetch endpoint (GET /api/user/profile)

**Frontend Components**:
- OnboardingForm (3-step form with radio buttons)
- ProfilePage (view/edit profile)

**Backend Routes**:
```
GET /api/user/profile
PUT /api/user/profile
  Request: { software_level, hardware_level, learning_goal }
```

**Acceptance Criteria**:
- Onboarding flows after signup
- Profile data saved to database
- Profile editable at any time
- User can see their profile

#### 2.2 Content Personalization Engine
**Assigned**: @AuthPersonalizer, @BackendEngineer
**Duration**: Weeks 4-5
**Deliverables**:
- [ ] Personalization service (adapts chapter based on user profile)
- [ ] Difficulty selector logic (basic vs. advanced)
- [ ] Content filtering (hide/show sections per profile)
- [ ] Code example filtering (Python for beginners, C++ for advanced)
- [ ] Endpoint: GET /api/content/chapter/{id}/personalized

**Backend Service**:
```python
def personalize_chapter(chapter_mdx, user_profile):
    # Remove <AdvancedOnly> if beginner
    # Remove <BeginnerOnly> if advanced
    # Filter code examples per language preference
    # Simplify explanations per software level
    # Add hardware context if hardware experience exists
    # Return personalized MDX
```

**Acceptance Criteria**:
- Chapter content changes based on user profile
- Personalized content still valid MDX
- Performance: < 500ms personalization overhead
- Default (unauthenticated) users see basic version

#### 2.3 Chapter-Level Personalization Buttons
**Assigned**: @FrontendEngineer
**Duration**: Week 5
**Deliverables**:
- [ ] Difficulty Toggle Button (Basic ↔ Advanced)
- [ ] Bookmark Button (save/unsave chapter)
- [ ] Progress Indicator (% completion)
- [ ] Responsive button layout (mobile-friendly)

**Components**:
```typescript
<DifficultyToggle currentLevel={userProfile.level} />
<BookmarkButton chapter_id={...} />
<ProgressIndicator completion_pct={...} />
```

**Acceptance Criteria**:
- Buttons render on chapter pages
- Difficulty toggle switches content (calls personalization API)
- Bookmark saves to database, persists
- Progress indicator updates on quiz completion
- Mobile responsive (touch-friendly)

#### 2.4 Progress Tracking
**Assigned**: @BackendEngineer
**Duration**: Weeks 5-6
**Deliverables**:
- [ ] Progress table (Neon: user_progress)
- [ ] Completion tracking (% per chapter)
- [ ] Quiz score tracking
- [ ] Time spent tracking
- [ ] Endpoints:
  - GET /api/user/progress/{chapter_id}
  - PUT /api/user/progress/{chapter_id}
  - GET /api/user/progress (all chapters)

**Acceptance Criteria**:
- Progress saved to database
- Fetched and displayed on user dashboard
- Updated when chapter section completed
- Updated when quiz submitted
- Persists across sessions

#### 2.5 Preference Persistence
**Assigned**: @AuthPersonalizer
**Duration**: Week 5
**Deliverables**:
- [ ] User preferences table (Neon: user_preferences)
- [ ] Preferences: dark_mode, preferred_language, show_advanced, auto_translate
- [ ] Endpoint: PUT /api/user/preferences
- [ ] Frontend: sync preferences to backend on change

**Acceptance Criteria**:
- Theme preference (dark/light) persists
- Language preference (en/ur) persists
- Show advanced toggle persists
- Auto-translate option persists
- Settings accessible from navbar menu

**Dependencies**:
- Phase 0 (infrastructure) ✅
- Phase 1 (chapters, auth) ✅ prerequisite
- Database schema (Phase 0.2) ✅

**Blockers to Watch**:
- Personalization logic complexity (test thoroughly)
- Database query performance (index user_progress table)

---

### PHASE 3: Urdu Translation & Localization (Weeks 6-8, sequential after Phase 1)

**Objective**: Translate 75%+ of chapters to Urdu while preserving technical terms, code, and formatting. Implement per-chapter language toggle.

**Work Streams**:

#### 3.1 Technical Glossary Development
**Assigned**: @Translator, @RoboticsExpert, @Educator
**Duration**: Week 6
**Deliverables**:
- [ ] Build comprehensive technical glossary (English ↔ Urdu)
- [ ] Include 100+ robotics/AI terms
- [ ] Document translation rationale
- [ ] Establish consistency rules (ROS 2 stays "ROS 2", not translated)
- [ ] Share with team before translation

**Format**:
```
English | Urdu | Example Sentence | Notes
ROS 2 | ROS 2 | "ROS 2 ایک middleware ہے" | Proper noun, keep as-is
Topic | موضوع | "Topic پر messages بھیجیں" | Core concept
Publisher | اشاعت کنندہ | "Publisher node messages بھیجتا ہے" | [Context]
...
```

**Acceptance Criteria**:
- 100+ terms translated consistently
- Clear, natural Urdu equivalents
- Example sentences provided
- Shared document accessible to all

#### 3.2 Chapter Translation
**Assigned**: @Translator
**Duration**: Weeks 6-8 (3 chapters/week, 9 chapters = 3 weeks)
**Deliverables**:
- [ ] Translate 9-10 chapters (75% coverage):
  - Module 1: All 5 chapters (ROS 2)
  - Module 2: 2-3 chapters (Gazebo/Unity)
  - Module 3: 2 chapters (Isaac Sim)
  - Module 4: 1-2 chapters (VLA)
- [ ] Each translated chapter:
  - Full Urdu text (اردو میں متن)
  - Technical terms kept in English
  - Code blocks UNCHANGED
  - MDX components UNCHANGED
  - All links functional
  - Formatting preserved

**Acceptance Criteria**:
- Urdu text is grammatically correct (native speaker verified)
- Technical accuracy maintained
- MDX syntax valid
- 100% code preservation
- All links functional
- Glossary terms applied consistently

**Parallelization Strategy**:
- Translator can work on 3 chapters/week
- @RoboticsExpert reviews for technical accuracy
- @Educator reviews for clarity and tone

#### 3.3 Language Toggle Implementation
**Assigned**: @FrontendEngineer, @BackendEngineer
**Duration**: Weeks 7-8
**Deliverables**:
- [ ] Language toggle button (English | اردو)
- [ ] Store language preference (Neon)
- [ ] Fetch correct language version (API endpoint)
- [ ] Persist preference across sessions
- [ ] Mobile responsive

**Frontend Component**:
```typescript
<LanguageToggle
  currentLanguage={userProfile.preferred_language}
  onToggle={(lang) => updateLanguagePreference(lang)}
/>
```

**Backend Endpoint**:
```
GET /api/content/chapter/{id}?language=en|ur
  Response: Chapter content in selected language
```

**Acceptance Criteria**:
- Toggle switches between English and Urdu versions
- Correct chapter version loads
- Language preference persists
- Mobile responsive
- No console errors

#### 3.4 Quality Assurance & Review
**Assigned**: @Reviewer, @RoboticsExpert, @Translator
**Duration**: Week 8
**Deliverables**:
- [ ] Proofread all Urdu translations
- [ ] Verify technical accuracy
- [ ] Check MDX/code integrity
- [ ] Test language toggle functionality
- [ ] Ensure glossary consistency

**Acceptance Criteria**:
- 0 breaking MDX errors
- 100% code block preservation
- Zero inconsistent terminology
- Native speaker QA passed
- All links functional

**Dependencies**:
- Phase 1 (English chapters) ✅ prerequisite
- Technical glossary (Phase 3.1) ✅ prerequisite

**Blockers to Watch**:
- Translation delays (single @Translator bottleneck)
- Quality variance (mitigate with glossary + @RoboticsExpert review)

---

### PHASE 4: Advanced Features & Polish (Weeks 8-10, parallel with Phase 3)

**Objective**: Implement adaptive learning, recommendation engine, analytics, and final polish.

**Work Streams**:

#### 4.1 Adaptive Learning Engine
**Assigned**: @AuthPersonalizer, @BackendEngineer
**Duration**: Weeks 8-9
**Deliverables**:
- [ ] Quiz difficulty adjustment (based on performance)
- [ ] Section unlock progression (require 80%+ to unlock advanced)
- [ ] Learning path recommendations (based on profile + progress)
- [ ] Suggested next chapters (algorithm)
- [ ] Peer statistics (optional: avg quiz score per chapter)

**Backend Logic**:
```python
def recommend_next_chapters(user_id):
    user_progress = get_user_progress(user_id)
    completed = [ch for ch in user_progress if completion_pct >= 100]

    # Recommend chapters in sequence
    next_modules = [ch for ch in all_chapters if module > completed[-1].module]
    return next_modules[:3]
```

**Acceptance Criteria**:
- Recommendations display on homepage
- Rationale provided (e.g., "Next: ROS 2 Services")
- Quiz difficulty adjusts based on performance
- Advanced content hidden until prerequisites mastered

#### 4.2 RAG Chatbot Enhancements
**Assigned**: @BackendEngineer
**Duration**: Weeks 8-9
**Deliverables**:
- [ ] Improve retrieval (BM25 hybrid search, not just semantic)
- [ ] Better ranking (relevance scoring, chunk importance)
- [ ] Selected text → direct query (text selection detection on frontend)
- [ ] Answer feedback (thumbs up/down, drives improvement)
- [ ] Conversation context (remember multi-turn context)

**Frontend Enhancement**:
```typescript
// Text selection → chatbot popup
document.addEventListener('mouseup', () => {
  const selectedText = getSelectedText();
  if (selectedText.length > 0) {
    showChatbotWithQuery(selectedText);
  }
});
```

**Acceptance Criteria**:
- Retrieval accuracy improved (user feedback >4/5)
- Selected text query works (popup appears)
- Feedback mechanism captures user thumbs
- Multi-turn conversations work smoothly

#### 4.3 Analytics & Insights
**Assigned**: @BackendEngineer, @FrontendEngineer
**Duration**: Week 9
**Deliverables**:
- [ ] User dashboard (progress overview, quiz scores, time spent)
- [ ] Chapter analytics (view count, avg completion time)
- [ ] Chatbot analytics (query count, satisfaction score)
- [ ] Learning path insights (which chapters users complete together)

**Dashboard Endpoint**:
```
GET /api/user/dashboard
  Response: {
    progress: { completed: 3, total: 12, pct: 25 },
    avg_quiz_score: 82,
    total_time_spent: 12.5 (hours),
    learning_path: "fundamentals",
    recommended_next: [...]
  }
```

**Acceptance Criteria**:
- Dashboard displays key metrics
- Data accurate and fresh
- Mobile responsive
- Privacy: only show own data (not others)

#### 4.4 Final Polish & Optimization
**Assigned**: @FrontendEngineer, @BackendEngineer
**Duration**: Week 10
**Deliverables**:
- [ ] Performance optimization (code splitting, lazy loading)
- [ ] Bundle size optimization
- [ ] Image optimization (all diagrams)
- [ ] CSS/JS minification
- [ ] Lighthouse score: 80+
- [ ] Page load: < 3 seconds (p95)

**Acceptance Criteria**:
- Lighthouse score desktop: 85+
- Lighthouse score mobile: 80+
- Core Web Vitals passing (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- Bundle size < 500KB (gzipped)

#### 4.5 Accessibility Audit
**Assigned**: @Reviewer, @FrontendEngineer
**Duration**: Week 10
**Deliverables**:
- [ ] WCAG 2.1 AA compliance audit
- [ ] Keyboard navigation test (Tab through all pages)
- [ ] Screen reader test (NVDA/VoiceOver)
- [ ] Color contrast check (4.5:1 for text)
- [ ] Alt text review (all images)
- [ ] Focus indicator review
- [ ] Semantic HTML check

**Acceptance Criteria**:
- 0 WCAG 2.1 AA violations
- Keyboard navigation works
- Screen reader compatible
- All images have alt text
- High contrast throughout

**Dependencies**:
- Phase 1 (MVP) ✅
- Phase 2 (personalization) ✅
- Phase 3 (translation) ✅ (parallel with this phase)

**Blockers to Watch**:
- Performance optimization complexity (requires profiling)
- WCAG audit might find unexpected issues (allocate time for fixes)

---

### PHASE 5: Testing & Quality Assurance (Weeks 2-10, continuous)

**Objective**: Comprehensive testing at all levels (unit, integration, E2E), accessibility, performance, security, and bonus validation.

**Parallel Workstream** (starts mid-Phase 1, continues throughout):

#### 5.1 Unit Testing
**Assigned**: @Reviewer
**Duration**: Weeks 2-10 (continuous)
**Deliverables**:
- [ ] Frontend unit tests (React Testing Library + Vitest)
  - Components render correctly
  - Props handling
  - State updates
  - Event handlers
- [ ] Backend unit tests (Pytest)
  - Services functions
  - Database operations
  - Validation logic
  - Utility functions

**Target**: 80%+ code coverage for critical paths

**Acceptance Criteria**:
- All tests pass
- Coverage >= 80% (critical paths)
- No flaky tests (consistent results)

#### 5.2 Integration Testing
**Assigned**: @Reviewer
**Duration**: Weeks 3-10 (as APIs are built)
**Deliverables**:
- [ ] Frontend ↔ Backend integration
  - API calls return correct data
  - Error handling works
  - Authentication flows
- [ ] Backend ↔ Database integration
  - Queries execute correctly
  - Data persists
  - Transactions work
- [ ] Backend ↔ OpenAI integration
  - Embeddings generated correctly
  - Chat completions return responses
  - Cost tracking

**Acceptance Criteria**:
- All integration flows tested
- No regressions
- Error cases handled

#### 5.3 End-to-End Testing
**Assigned**: @Reviewer
**Duration**: Weeks 5-10 (full workflows)
**Deliverables**:
- [ ] User workflows (Playwright or manual)
  - Signup → onboarding → view chapter → answer quiz
  - Login → personalize difficulty → browse chapters → use chatbot
  - Bookmark chapter → return later → resume progress
- [ ] Full feature workflows
  - Language toggle (English ↔ اردو)
  - Theme toggle (dark ↔ light)
  - User preference updates
- [ ] Error scenarios
  - Network timeout
  - API error (500)
  - Invalid input
  - Rate limiting

**Acceptance Criteria**:
- All workflows complete successfully
- No broken flows
- Errors handled gracefully

#### 5.4 Performance Testing
**Assigned**: @Reviewer, @FrontendEngineer
**Duration**: Weeks 5-10 (benchmarking)
**Deliverables**:
- [ ] Frontend performance
  - Lighthouse score (desktop, mobile)
  - Core Web Vitals (LCP, FID, CLS)
  - Page load time (< 3s p95)
  - Time to interactive
- [ ] Backend performance
  - API latency (< 200ms p95 excluding LLM)
  - Database query latency (< 100ms p95)
  - Chatbot response time (< 5s p95)
  - Concurrent request handling (10+ simultaneous)
- [ ] Load testing
  - 100 concurrent users
  - 10 requests/second
  - Resource usage (CPU, memory)

**Tools**: Lighthouse, Chrome DevTools, Locust (load testing)

**Acceptance Criteria**:
- Lighthouse score: 80+ (desktop), 75+ (mobile)
- API latency: < 200ms (p95)
- Page load: < 3s (p95)
- Handle 100+ concurrent users

#### 5.5 Accessibility Testing
**Assigned**: @Reviewer
**Duration**: Weeks 5-10 (continuous)
**Deliverables**:
- [ ] WCAG 2.1 AA compliance audit
- [ ] Keyboard navigation (Tab through all pages)
- [ ] Screen reader testing (NVDA, VoiceOver)
- [ ] Color contrast verification (4.5:1 text)
- [ ] Alt text review (all images)
- [ ] Focus indicator checks
- [ ] Semantic HTML validation

**Tools**: WAVE, axe DevTools, Lighthouse, manual testing

**Acceptance Criteria**:
- 0 WCAG 2.1 AA violations
- Keyboard navigable
- Screen reader compatible
- 4.5:1 contrast for all text

#### 5.6 Security Testing
**Assigned**: @Reviewer, @BackendEngineer
**Duration**: Weeks 5-10 (continuous)
**Deliverables**:
- [ ] Input validation (SQL injection, XSS, command injection)
- [ ] Authentication security (JWT, session expiry, password hashing)
- [ ] Authorization (users can't access others' data)
- [ ] Secrets management (no API keys in code)
- [ ] HTTPS/CORS validation
- [ ] Dependency vulnerability scan (npm, pip)

**Tools**: OWASP ZAP, npm audit, pip check, manual code review

**Acceptance Criteria**:
- 0 critical vulnerabilities
- Secrets not in code/logs
- JWT properly validated
- No unauthorized access possible

#### 5.7 Content Quality Testing
**Assigned**: @Reviewer, @RoboticsExpert, @Educator
**Duration**: Weeks 2-6 (during content writing)
**Deliverables**:
- [ ] Spelling & grammar check (all chapters)
- [ ] Technical accuracy review (@RoboticsExpert)
- [ ] Code example verification (run all code)
- [ ] Link validation (all external links active)
- [ ] Learning outcome alignment (content delivers on outcomes)

**Acceptance Criteria**:
- 0 spelling errors
- 0 grammar errors
- All technical content accurate
- All code examples runnable
- All links active
- Content aligns to learning outcomes

**Continuous Integration**:
- Unit tests run on every commit (GitHub Actions)
- Integration tests run before merge to main
- Performance benchmarks tracked (Lighthouse, API latency)
- Security scan on dependency updates

---

### PHASE 6: Deployment & Launch (Week 11, final)

**Objective**: Deploy Docusaurus site to GitHub Pages, FastAPI backend to serverless, set up monitoring.

**Work Streams**:

#### 6.1 Frontend Deployment (GitHub Pages)
**Assigned**: @FrontendEngineer, @BackendEngineer
**Duration**: Week 11
**Deliverables**:
- [ ] CI/CD pipeline (GitHub Actions)
  - Trigger: push to main branch
  - Steps: install, lint, type-check, test, build, deploy
- [ ] Docusaurus build (static HTML + CSS + JS)
- [ ] GitHub Pages configuration (.github/workflows/deploy.yml)
- [ ] Custom domain (optional)
- [ ] SSL/TLS (automatic via GitHub Pages)

**Workflow Steps**:
```yaml
name: Deploy Docusaurus to GitHub Pages
on: [push to main]
jobs:
  build-deploy:
    - npm install
    - npm run lint
    - npm run type-check
    - npm test
    - npm run build
    - Deploy to GitHub Pages (automatic)
```

**Acceptance Criteria**:
- Site deploys automatically on push
- No build errors
- Site accessible at GitHub Pages URL
- SSL/TLS working
- Performance acceptable

#### 6.2 Backend Deployment (Serverless)
**Assigned**: @BackendEngineer
**Duration**: Week 11
**Deliverables**:
- [ ] Docker image (Dockerfile for FastAPI)
- [ ] Deployment target (Railway or Vercel)
- [ ] Environment variables (GitHub Secrets)
  - OPENAI_API_KEY
  - DATABASE_URL (Neon)
  - QDRANT_URL, QDRANT_KEY
  - JWT_SECRET
- [ ] CI/CD pipeline (GitHub Actions)
  - Build Docker image
  - Push to registry
  - Deploy to hosting platform
- [ ] Health check endpoint (/health)
- [ ] Monitoring & alerting (Sentry, custom logs)

**Workflow Steps**:
```yaml
name: Deploy FastAPI Backend
on: [push to main]
jobs:
  build-deploy:
    - Run tests (pytest)
    - Build Docker image
    - Push to registry
    - Deploy to Railway/Vercel
    - Health check
```

**Acceptance Criteria**:
- Backend accessible at API URL
- All endpoints return 200/expected codes
- Database connected (queries work)
- Qdrant connected (embeddings searchable)
- OpenAI API working (chatbot functional)
- Logging in place
- Health check passing

#### 6.3 Database Migrations & Backups
**Assigned**: @BackendEngineer
**Duration**: Week 11
**Deliverables**:
- [ ] Alembic migrations run on deployment
- [ ] Database backups configured (Neon auto-backups)
- [ ] Backup retention policy (30 days)
- [ ] Disaster recovery plan documented

**Acceptance Criteria**:
- Migrations run successfully
- No data loss
- Backups verified

#### 6.4 Monitoring & Alerting
**Assigned**: @BackendEngineer, @FrontendEngineer
**Duration**: Week 11
**Deliverables**:
- [ ] Error tracking (Sentry)
- [ ] Performance monitoring (API latency, database latency)
- [ ] Uptime monitoring (health check)
- [ ] Alerts configured (Slack, email)
- [ ] Logs aggregation (structured JSON logs)
- [ ] Dashboard (metrics visible)

**Acceptance Criteria**:
- Errors tracked and reported
- Latency metrics captured
- Alerts trigger on critical errors
- Logs searchable
- Dashboard accessible

#### 6.5 Documentation & Runbooks
**Assigned**: @FrontendEngineer, @BackendEngineer
**Duration**: Week 11
**Deliverables**:
- [ ] Deployment documentation (how to deploy)
- [ ] Rollback procedures (how to revert bad deployment)
- [ ] Emergency runbooks (high CPU, database down, API errors)
- [ ] Troubleshooting guide
- [ ] Contact info (on-call engineer)

**Acceptance Criteria**:
- Documentation complete
- Runbooks tested
- Team trained

**Dependencies**:
- Phases 1-5 ✅ (everything must be complete before deployment)

**Blockers to Watch**:
- GitHub Pages DNS propagation (might take 24 hours)
- Railway/Vercel approval (might delay deployment)
- Environment variable misconfiguration (test thoroughly)

---

## 4. Critical Path & Dependencies

```
Phase 0 (Foundation)
├── 0.1 Repo Setup ──┐
├── 0.2 Database ────├── BLOCKING
├── 0.3 Theme ───────┤
├── 0.4 Backend ─────┤
└── 0.5 Auth ────────┘
         │
         ▼
Phase 1 (MVP) [PARALLEL]
├── 1.1 Components ──────────────┐
├── 1.2 Chapters ────────────────├── DELIVER by Week 5
├── 1.3 RAG Chatbot ─────────────┤
├── 1.4 Auth Integration ───────┤
└── 1.5 Frontend-Backend ────────┘
         │
         ├── Phase 2 (Personalization) [PARALLEL, Weeks 4-6]
         │   ├── 2.1 Profiling
         │   ├── 2.2 Personalization
         │   ├── 2.3 Buttons
         │   ├── 2.4 Progress
         │   └── 2.5 Preferences
         │
         ├── Phase 3 (Urdu) [SEQUENTIAL, Weeks 6-8]
         │   ├── 3.1 Glossary ──┐
         │   ├── 3.2 Translation ├── AFTER Phase 1
         │   ├── 3.3 Toggle ────┤
         │   └── 3.4 QA ────────┘
         │
         ├── Phase 4 (Advanced) [PARALLEL, Weeks 8-10]
         │   ├── 4.1 Adaptive Learning
         │   ├── 4.2 Chatbot Enhancements
         │   ├── 4.3 Analytics
         │   ├── 4.4 Polish
         │   └── 4.5 Accessibility
         │
         ├── Phase 5 (Testing) [CONTINUOUS, Weeks 2-10]
         │   ├── 5.1 Unit Testing
         │   ├── 5.2 Integration Testing
         │   ├── 5.3 E2E Testing
         │   ├── 5.4 Performance
         │   ├── 5.5 Accessibility
         │   ├── 5.6 Security
         │   └── 5.7 Content QA
         │
         ▼
Phase 6 (Deployment) [FINAL]
├── 6.1 Frontend Deploy ─┐
├── 6.2 Backend Deploy ──├── LAUNCH
├── 6.3 Backups ────────┤
├── 6.4 Monitoring ─────┤
└── 6.5 Documentation ──┘
```

**Critical Path** (minimum duration):
- Phase 0: 1 week (blocking all others)
- Phase 1: 4 weeks (MVP core)
- Phase 3: 3 weeks (after Phase 1)
- Phase 6: 1 week (final deployment)
- **Total: ~9 weeks minimum** (with aggressive parallelization)

---

## 5. Subagent Assignment Summary

| Phase | Subagent | Role | Duration |
|-------|----------|------|----------|
| **0** | @SpecArchitect, @BackendEngineer, @FrontendEngineer | Setup, infrastructure | Week 1 |
| **1.1** | @FrontendEngineer | Custom theme, components | Weeks 2-3 |
| **1.2** | @Educator, @RoboticsExpert, @CodeExampleGenerator, @DiagramDescriber | Content writing | Weeks 2-5 |
| **1.3** | @BackendEngineer | RAG chatbot indexing | Weeks 2-5 |
| **1.4** | @AuthPersonalizer | Auth integration | Weeks 2-3 |
| **1.5** | @FrontendEngineer, @BackendEngineer | API integration | Weeks 3-5 |
| **2.1** | @AuthPersonalizer, @FrontendEngineer | Profiling & onboarding | Week 4 |
| **2.2** | @AuthPersonalizer, @BackendEngineer | Personalization engine | Weeks 4-5 |
| **2.3** | @FrontendEngineer | Chapter buttons | Week 5 |
| **2.4** | @BackendEngineer | Progress tracking | Weeks 5-6 |
| **2.5** | @AuthPersonalizer | Preferences | Week 5 |
| **3.1** | @Translator, @RoboticsExpert, @Educator | Glossary | Week 6 |
| **3.2** | @Translator | Chapter translation | Weeks 6-8 |
| **3.3** | @FrontendEngineer, @BackendEngineer | Language toggle | Weeks 7-8 |
| **3.4** | @Reviewer, @RoboticsExpert, @Translator | QA review | Week 8 |
| **4.1** | @AuthPersonalizer, @BackendEngineer | Adaptive learning | Weeks 8-9 |
| **4.2** | @BackendEngineer | Chatbot enhancements | Weeks 8-9 |
| **4.3** | @BackendEngineer, @FrontendEngineer | Analytics | Week 9 |
| **4.4** | @FrontendEngineer, @BackendEngineer | Polish & optimization | Week 10 |
| **4.5** | @Reviewer, @FrontendEngineer | Accessibility audit | Week 10 |
| **5** | @Reviewer (orchestrator), all subagents (provide input) | Testing & QA | Weeks 2-10 |
| **6.1** | @FrontendEngineer | GitHub Pages deploy | Week 11 |
| **6.2** | @BackendEngineer | Backend deploy | Week 11 |
| **6.3** | @BackendEngineer | Backups | Week 11 |
| **6.4** | @BackendEngineer, @FrontendEngineer | Monitoring | Week 11 |
| **6.5** | @FrontendEngineer, @BackendEngineer | Documentation | Week 11 |

**Concurrency Strategy**:
- **Weeks 2-3**: Phase 0 completes; Phase 1.1, 1.2 start (no dependencies)
- **Weeks 4-5**: Phase 1 continues; Phase 2, Phase 1.3-1.5 start (parallel streams)
- **Weeks 6-8**: Phase 1 wraps; Phase 2 wraps; Phase 3 starts (Urdu translation)
- **Weeks 8-10**: Phase 3-4 parallel; Phase 5 intensive testing throughout
- **Week 11**: Phase 6 deployment (all code frozen)

---

## 6. Risk Management

### Top Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| **Content writing delays** (@Educator bottleneck) | HIGH | HIGH | Parallelize across 3 chapters/week; use ChapterWriter skill to draft content |
| **RAG chatbot indexing latency** | MEDIUM | MEDIUM | Batch embeddings; use caching; test with smaller subset first |
| **Urdu translation quality** | MEDIUM | MEDIUM | Establish glossary early; @RoboticsExpert reviews; native speaker QA |
| **Database schema changes mid-project** | LOW | HIGH | Finalize schema in Phase 0; use migrations for changes; communicate changes to team |
| **OpenAI API rate limits** | MEDIUM | LOW | Implement rate limiting; cache embeddings; use batching |
| **Docusaurus theme performance** | LOW | MEDIUM | Profile early (Phase 1.1); optimize images/CSS incrementally |
| **Frontend-backend API contract misalignment** | MEDIUM | MEDIUM | Define OpenAPI spec early; mock API endpoints before implementation |
| **Accessibility regressions** | LOW | MEDIUM | Test accessibility continuously (Phase 5); don't leave for final week |
| **GitHub Pages deployment issues** | LOW | LOW | Test CI/CD pipeline early; have rollback plan |

### Blockers & Escalation

**Known Blockers** (requires external approval):
1. Neon Postgres account creation (1-2 days)
2. Qdrant cloud account creation (1-2 days)
3. OpenAI API credits (must request, approve)
4. GitHub org secrets configuration (IT approval)

**Escalation Path**:
- Technical blockers: escalate to @SpecArchitect
- Content blockers: escalate to @Educator
- External dependencies: escalate immediately

---

## 7. Quality Gates & Acceptance

### Phase Completion Criteria

**Phase 0**: ✅ All infrastructure working
- [ ] Git repo configured, CI/CD pipeline functional
- [ ] Docusaurus builds, custom theme loads
- [ ] FastAPI server runs, health check passes
- [ ] Neon Postgres connected, tables created
- [ ] Qdrant initialized, collection created
- [ ] Better-Auth configured
- [ ] Environment variables set (GitHub Secrets)

**Phase 1**: ✅ Core MVP complete
- [ ] All 12 chapters written in MDX
- [ ] Custom Docusaurus theme fully functional
- [ ] RAG chatbot indexed and responding
- [ ] Authentication working (signup, signin, logout)
- [ ] Pages render correctly (no styling errors)
- [ ] API endpoints all functional (200 OK)
- [ ] Code coverage >= 80% (unit tests)
- [ ] Lighthouse score >= 75

**Phase 2**: ✅ Personalization complete
- [ ] User profiles stored (software/hardware/goal)
- [ ] Difficulty toggle switches content
- [ ] Bookmarking saves to database
- [ ] Progress tracking works
- [ ] Preferences persist
- [ ] All features tested (unit + integration)

**Phase 3**: ✅ Urdu translation complete
- [ ] 75%+ chapters translated
- [ ] Glossary established (100+ terms)
- [ ] Language toggle functional
- [ ] MDX syntax valid for all Urdu chapters
- [ ] Code blocks unchanged
- [ ] Links functional
- [ ] Native speaker QA passed

**Phase 4**: ✅ Advanced features complete
- [ ] Adaptive learning engine functional
- [ ] Chatbot enhancements working
- [ ] Analytics dashboard showing metrics
- [ ] Performance optimized (Lighthouse 80+)
- [ ] Accessibility audit passed (WCAG 2.1 AA)

**Phase 5**: ✅ Testing complete
- [ ] Unit test coverage >= 80%
- [ ] Integration tests all pass
- [ ] E2E workflows tested
- [ ] Performance benchmarks met
- [ ] Accessibility verified
- [ ] Security audit passed
- [ ] Content QA approved

**Phase 6**: ✅ Deployment complete
- [ ] Frontend deployed to GitHub Pages
- [ ] Backend deployed to serverless
- [ ] All endpoints accessible
- [ ] Database backups configured
- [ ] Monitoring & alerting active
- [ ] Documentation complete

---

## 8. Success Metrics

### MVP Success (End of Phase 1)
- ✅ 12 chapters written, published
- ✅ Custom Docusaurus theme functional
- ✅ RAG chatbot answers questions
- ✅ User auth working
- ✅ Page load < 3s
- ✅ Lighthouse score 75+

### Project Success (End of Phase 6)
- ✅ Deployed to GitHub Pages
- ✅ 75%+ chapters in Urdu
- ✅ User personalization working (auth + difficulty toggle + bookmarks)
- ✅ RAG chatbot >4/5 user satisfaction
- ✅ Lighthouse score 80+
- ✅ WCAG 2.1 AA compliant
- ✅ Zero critical security vulnerabilities
- ✅ 40+ hours saved via reusable skills

### Bonus Maximization (Hackathon)
- ✅ 7 reusable Claude Code skills (ChapterWriter, UrduTranslator, ContentPersonalizer, QuizGenerator, DiagramDescriber, CodeExampleGenerator, BonusValidator)
- ✅ 8 specialized subagents (orchestration, delegation model)
- ✅ 10+ PHRs (Prompt History Records)
- ✅ 5+ ADRs (Architecture Decision Records)
- ✅ User personalization (auth + background + difficulty + language + bookmarks)
- ✅ 75%+ Urdu translation with glossary
- ✅ Estimated bonus multiplier: **~4.2x** (1.7x skills × 1.4x personalization × 1.5x translation × 1.5x artifacts)

---

## 9. Communication & Handoff

### Weekly Sync Format
Every Friday, 15-min sync:
1. **What was completed** (Phase X milestones)
2. **What's planned next** (Week N+1)
3. **Blockers or risks** (escalate if needed)
4. **Dependencies** (who needs what from whom)

### Phase Handoff Checklist
Before moving to next phase:
- [ ] All acceptance criteria met for current phase
- [ ] Code reviewed and merged
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Stakeholders approved
- [ ] No critical blockers

### Knowledge Transfer
- @Educator documents chapter structure (template)
- @FrontendEngineer documents component library
- @BackendEngineer documents API contracts (OpenAPI spec)
- @Translator documents glossary
- @Reviewer documents test procedures

---

## 10. Next Steps

1. **Approve this PLAN.md** (stakeholder sign-off)
2. **Create TASKS.md** (break into atomic work items with acceptance criteria)
3. **Initiate Phase 0** (immediately after approval)
4. **Kick off subagent assignments** (parallelization begins)
5. **Create ADRs** for major architectural decisions
6. **Record PHRs** for each planning phase

---

**Status**: Ready for Stakeholder Review & Approval
**Document Version**: 1.0.0-draft
**Last Updated**: 2025-12-24
**Owner**: @SpecArchitect (Lead AI Architect)

