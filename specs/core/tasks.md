# Physical AI & Humanoid Robotics Textbook - Tasks (TASKS)

**Document**: Task Breakdown (TASKS)
**Status**: Ready for Execution
**Last Updated**: 2025-12-24
**Owner**: @SpecArchitect
**Governance**: Spec-Kit Plus + Constitution v1.0.0

---

## Overview

This document breaks the PLAN into **atomic, testable, independently-executable tasks**. Each task:
- Has a clear **acceptance criterion** (how to verify completion)
- Lists **dependencies** (what must be done first)
- Is assigned to a **specific subagent**
- References **deliverables** (files, endpoints, components)
- Includes **estimated effort** (for tracking, not promises)

**Total Tasks**: 120+ across 6 phases
**Critical Path**: 60+ blocking tasks
**Parallelizable**: 80+ independent tasks

---

## PHASE 0: Foundation & Setup (Week 1)

### Block 0.1: Repository & Project Structure

#### Task 0.1.1: Initialize Git & GitHub Repository
**Assigned**: @SpecArchitect
**Effort**: 0.5 days
**Dependencies**: None
**Deliverables**: `.gitignore`, `.github/` directory structure

**Description**:
Initialize Git repository with proper structure for Spec-Kit Plus workflow.

**Acceptance Criteria**:
- [ ] Repository initialized with `.git/`
- [ ] `.gitignore` configured (exclude `.env.local`, `node_modules/`, `venv/`, `*.pyc`, dist, build)
- [ ] `.github/` directory created
- [ ] `README.md` drafted (project overview, setup instructions)
- [ ] Project structure documented (directories and purpose)

**Deliverables**:
- `.gitignore` file
- `.github/` directory
- `README.md`
- Directory structure in place

---

#### Task 0.1.2: Create Docusaurus Project Structure
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.1.1
**Deliverables**: `docusaurus-site/` directory with Docusaurus 3.x scaffold

**Description**:
Initialize Docusaurus 3.x project with custom theme setup (NO defaults).

**Acceptance Criteria**:
- [ ] `docusaurus-site/` directory created
- [ ] Docusaurus 3.x installed (`npm init docusaurus@latest`)
- [ ] `docusaurus.config.js` configured with:
  - Custom theme (no Docusaurus default)
  - Title, tagline, URL, repository
  - plugins, presets, stylesheets
- [ ] `src/` directory structure (components, pages, css, data)
- [ ] `static/` directory for assets
- [ ] Tailwind CSS initialized (`tailwind.config.js`, `tailwind.css`)
- [ ] `package.json` configured (scripts: build, start, lint)
- [ ] `npm run build` produces no errors
- [ ] `npm run start` runs locally on http://localhost:3000

**Deliverables**:
- `docusaurus-site/docusaurus.config.js`
- `docusaurus-site/src/`
- `docusaurus-site/static/`
- `docusaurus-site/tailwind.config.js`
- `docusaurus-site/package.json`

---

#### Task 0.1.3: Create FastAPI Backend Project Structure
**Assigned**: @BackendEngineer
**Effort**: 0.5 days
**Dependencies**: Task 0.1.1
**Deliverables**: `backend/fastapi-app/` directory with FastAPI scaffold

**Description**:
Initialize FastAPI project with standard structure.

**Acceptance Criteria**:
- [ ] `backend/fastapi-app/` directory created
- [ ] `main.py` with FastAPI app initialization
- [ ] `api/` directory (routes)
- [ ] `services/` directory (business logic)
- [ ] `models/` directory (Pydantic models, SQLAlchemy ORM)
- [ ] `config.py` (configuration, environment variables)
- [ ] `requirements.txt` with dependencies (fastapi, uvicorn, sqlalchemy, pydantic, httpx, etc.)
- [ ] `uvicorn` configured (port 8000)
- [ ] `uvicorn main:app --reload` runs without errors
- [ ] `GET /health` returns `{"status": "ok"}`

**Deliverables**:
- `backend/fastapi-app/main.py`
- `backend/fastapi-app/api/`
- `backend/fastapi-app/services/`
- `backend/fastapi-app/models/`
- `backend/fastapi-app/requirements.txt`

---

#### Task 0.1.4: Set Up GitHub Actions CI/CD Pipeline
**Assigned**: @FrontendEngineer, @BackendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.1.1
**Deliverables**: `.github/workflows/` YML files

**Description**:
Create GitHub Actions workflows for continuous integration (testing, linting) and deployment.

**Acceptance Criteria**:
- [ ] `.github/workflows/docusaurus-build.yml` created
  - Trigger: push to main, pull request
  - Steps: install, lint, test, build
  - Deploy to GitHub Pages (on push to main)
- [ ] `.github/workflows/backend-test.yml` created
  - Trigger: push to main, pull request
  - Steps: install, lint, type-check, pytest
  - Fail on test failure or coverage < 80%
- [ ] Workflows tested (manual trigger or push)
- [ ] No secrets hardcoded (use GitHub Secrets)

**Deliverables**:
- `.github/workflows/docusaurus-build.yml`
- `.github/workflows/backend-test.yml`

---

#### Task 0.1.5: Create specs/, history/, and .claude/ Directory Structure
**Assigned**: @SpecArchitect
**Effort**: 0.5 days
**Dependencies**: Task 0.1.1
**Deliverables**: Directory structure for Spec-Kit Plus artifacts

**Description**:
Create Spec-Kit Plus directory hierarchy.

**Acceptance Criteria**:
- [ ] `specs/core/` created (spec.md, plan.md, tasks.md)
- [ ] `specs/rag-chatbot/` created
- [ ] `specs/personalization/` created
- [ ] `history/prompts/` created (constitution/, core/, rag-chatbot/, personalization/, general/)
- [ ] `history/adr/` created (architecture decision records)
- [ ] `.claude/agents/` created (subagent definitions)
- [ ] `.claude/skills/` created (reusable skills)
- [ ] `.claude/commands/` created (custom commands)
- [ ] All directories have `.gitkeep` files (so empty dirs are tracked)

**Deliverables**:
- Directory structure (visible in git)
- `.gitkeep` files in each directory

---

### Block 0.2: Database Setup

#### Task 0.2.1: Create Neon Postgres Database
**Assigned**: @BackendEngineer
**Effort**: 0.5 days
**Dependencies**: None (external service)
**Deliverables**: Neon database connection string

**Description**:
Set up managed Postgres database on Neon (serverless).

**Acceptance Criteria**:
- [ ] Neon account created (neon.tech)
- [ ] Project created
- [ ] Database created (default "neondb")
- [ ] Connection string obtained (DATABASE_URL format)
- [ ] Connection tested locally (psql, or Python psycopg2)
- [ ] Connection string stored in `.env.local` (NOT in git)

**Deliverables**:
- Neon database URL
- `.env.local` template (documented, secrets excluded)

---

#### Task 0.2.2: Design & Create Database Schema
**Assigned**: @BackendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 0.2.1
**Deliverables**: SQL schema file, Alembic migrations

**Description**:
Design relational schema for users, chat, chapters, progress, preferences.

**Acceptance Criteria**:
- [ ] `backend/fastapi-app/models/` SQLAlchemy models defined:
  - `User` (id, email, password_hash, background_software, background_hardware, learning_goal, created_at)
  - `UserPreferences` (user_id, dark_mode, preferred_language, show_advanced, auto_translate)
  - `ChatSession` (id, user_id, created_at, updated_at)
  - `ChatMessage` (id, session_id, role, content, timestamp, feedback)
  - `Chapter` (id, module, chapter, title, content_type)
  - `UserProgress` (id, user_id, chapter_id, completion_pct, quiz_score, time_spent_sec, bookmarked)
- [ ] Relationships defined (foreign keys, constraints)
- [ ] Indexes created (email, user_id, chapter_id for fast lookups)
- [ ] Alembic migrations created (`alembic init`)
- [ ] Migrations tested locally (apply, rollback)
- [ ] Schema documented (ER diagram, field descriptions)

**Deliverables**:
- `backend/fastapi-app/models/` Python ORM definitions
- `backend/fastapi-app/alembic/` migration files
- Schema diagram (or documented in comments)

---

#### Task 0.2.3: Initialize Qdrant Vector Database
**Assigned**: @BackendEngineer
**Effort**: 0.5 days
**Dependencies**: None (external service)
**Deliverables**: Qdrant collection, connection details

**Description**:
Set up Qdrant vector database (cloud or self-hosted).

**Acceptance Criteria**:
- [ ] Qdrant account/instance created (qdrant.io or self-hosted Docker)
- [ ] Connection URL obtained
- [ ] API key/credentials obtained (if cloud)
- [ ] Collection "chapters" created
  - Vector size: 1536 (OpenAI `text-embedding-3-small`)
  - Distance metric: Cosine
  - Payload: module (int), chapter (int), section (string), content_type (string)
- [ ] Connection tested (create, retrieve, delete operations)
- [ ] Credentials stored in `.env.local`

**Deliverables**:
- Qdrant collection "chapters" created
- Connection details in `.env.local`

---

#### Task 0.2.4: Set Up Database Connection & ORM in FastAPI
**Assigned**: @BackendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.2.2, Task 0.2.3
**Deliverables**: Database client, ORM configuration

**Description**:
Configure SQLAlchemy and Qdrant clients in FastAPI app.

**Acceptance Criteria**:
- [ ] `backend/fastapi-app/database.py` created
  - Engine creation (Neon connection)
  - Session factory setup
  - Base class for models
- [ ] `backend/fastapi-app/qdrant_client.py` created
  - Qdrant client initialization
  - Helper functions: search, upsert, delete
- [ ] Dependency injection in FastAPI (`Depends(get_db)`)
- [ ] Connection pool configured (echo=False for production)
- [ ] Test: create table, insert row, query, delete
- [ ] Logging configured (connection events)

**Deliverables**:
- `backend/fastapi-app/database.py`
- `backend/fastapi-app/qdrant_client.py`
- Integration test (test_database_connection.py)

---

### Block 0.3: Docusaurus Custom Theme Foundation

#### Task 0.3.1: Disable Docusaurus Default Theme
**Assigned**: @FrontendEngineer
**Effort**: 0.5 days
**Dependencies**: Task 0.1.2
**Deliverables**: Updated `docusaurus.config.js`

**Description**:
Remove Docusaurus default styling completely.

**Acceptance Criteria**:
- [ ] `docusaurus.config.js` configured:
  - `themes: []` (no default themes)
  - Custom `Layout` component path specified
  - No Docusaurus CSS imported
- [ ] Create `src/theme/Layout/index.tsx` (custom Layout)
- [ ] Verify no default Docusaurus styles loaded (inspect CSS)
- [ ] Site builds without warnings

**Deliverables**:
- Updated `docusaurus.config.js`
- `src/theme/Layout/index.tsx`

---

#### Task 0.3.2: Set Up Tailwind CSS & Design System
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.1.2
**Deliverables**: Tailwind config, design tokens

**Description**:
Configure Tailwind CSS with custom design system.

**Acceptance Criteria**:
- [ ] `tailwind.config.js` created with:
  - Custom colors (primary blue, accent green, neutral grays)
  - Custom fonts (Inter)
  - Dark mode enabled
  - Responsive breakpoints defined
- [ ] `src/css/tailwind.css` created (Tailwind directives)
- [ ] Design system documented (colors, spacing, typography)
- [ ] Tailwind utility classes working
- [ ] Dark mode toggle works

**Deliverables**:
- `tailwind.config.js`
- `src/css/tailwind.css`
- Design system documentation

---

#### Task 0.3.3: Build Custom Navbar Component
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.3.2
**Deliverables**: Navbar React component

**Description**:
Create custom navbar with logo, module dropdown, search, user menu, theme toggle.

**Acceptance Criteria**:
- [ ] Component renders (no errors)
- [ ] Logo displayed
- [ ] Module dropdown (1-4)
- [ ] Search input
- [ ] User menu (Login/Logout)
- [ ] Theme toggle (dark/light)
- [ ] Responsive (desktop: full, mobile: hamburger menu)
- [ ] Accessible (semantic HTML, focus indicators)
- [ ] Styled with Tailwind (no inline styles)

**Deliverables**:
- `src/components/Navbar/Navbar.tsx`
- Unit tests (Navbar.test.tsx)

---

#### Task 0.3.4: Build Custom Sidebar Component
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.3.2
**Deliverables**: Sidebar React component

**Description**:
Create hierarchical, collapsible sidebar for chapter navigation.

**Acceptance Criteria**:
- [ ] Component renders without errors
- [ ] Displays Module 1-4 (collapsible sections)
- [ ] Each module shows chapters (3-5 per module)
- [ ] Active indicator for current page
- [ ] Progress % displayed per chapter
- [ ] Responsive (desktop: full width, mobile: drawer)
- [ ] Accessible (keyboard nav, aria labels)
- [ ] Styled with Tailwind

**Deliverables**:
- `src/components/Sidebar/Sidebar.tsx`
- Unit tests

---

#### Task 0.3.5: Build Custom Footer Component
**Assigned**: @FrontendEngineer
**Effort**: 0.5 days
**Dependencies**: Task 0.3.2
**Deliverables**: Footer React component

**Description**:
Create footer with links, copyright, social.

**Acceptance Criteria**:
- [ ] Component renders
- [ ] Links section (docs, GitHub, issues)
- [ ] Copyright notice
- [ ] Social links (optional)
- [ ] Responsive
- [ ] Styled with Tailwind

**Deliverables**:
- `src/components/Footer/Footer.tsx`

---

### Block 0.4: FastAPI Backend Skeleton

#### Task 0.4.1: Create FastAPI App with Error Handling & Logging
**Assigned**: @BackendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.1.3, Task 0.2.4
**Deliverables**: Updated `main.py`, error handling middleware

**Description**:
Set up FastAPI with logging, error handling, CORS.

**Acceptance Criteria**:
- [ ] `backend/fastapi-app/main.py` updated:
  - FastAPI app instance created
  - CORS configured (allow frontend origin)
  - Error handling middleware
  - Logging configured (JSON format)
- [ ] `/health` endpoint returns `{"status": "ok"}`
- [ ] Error responses properly formatted (error message, status code)
- [ ] Logging shows request/response info
- [ ] No console errors/warnings

**Deliverables**:
- Updated `main.py`
- `backend/fastapi-app/middleware/` for custom middleware

---

#### Task 0.4.2: Create Pydantic Models for Requests/Responses
**Assigned**: @BackendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.4.1
**Deliverables**: Pydantic model files

**Description**:
Define request/response models for all API endpoints.

**Acceptance Criteria**:
- [ ] `models/` directory organized:
  - `auth.py` (LoginRequest, SignupRequest, TokenResponse)
  - `user.py` (UserProfile, UserPreferences)
  - `chatbot.py` (ChatQuery, ChatResponse, ChatMessage)
  - `content.py` (ChapterMetadata, ChapterContent)
  - `progress.py` (ProgressUpdate, ProgressResponse)
- [ ] All models have field validation (required, min/max length, regex)
- [ ] JSON schema generated properly
- [ ] Type hints throughout

**Deliverables**:
- `backend/fastapi-app/models/` with all Pydantic models

---

#### Task 0.4.3: Set Up Authentication Middleware
**Assigned**: @AuthPersonalizer
**Effort**: 1.5 days
**Dependencies**: Task 0.4.1
**Deliverables**: JWT auth middleware, utilities

**Description**:
Implement JWT token validation middleware for protected routes.

**Acceptance Criteria**:
- [ ] JWT configuration (secret, algorithm, expiry)
- [ ] Token generation function (for login)
- [ ] Token validation function (for protected routes)
- [ ] Dependency injection: `Depends(get_current_user)`
- [ ] Protected route returns 401 if not authenticated
- [ ] Token refresh logic (if needed)
- [ ] Test: valid token passes, invalid token rejected

**Deliverables**:
- `backend/fastapi-app/auth/` with JWT utilities
- Middleware integration in main.py

---

#### Task 0.4.4: Create Health Check & Basic Endpoints
**Assigned**: @BackendEngineer
**Effort**: 0.5 days
**Dependencies**: Task 0.4.1
**Deliverables**: Initial API routes

**Description**:
Create placeholder endpoints for testing.

**Acceptance Criteria**:
- [ ] `GET /health` returns 200, `{"status": "ok"}`
- [ ] `GET /api/health` returns database + Qdrant connection status
- [ ] All endpoints return proper status codes
- [ ] Error responses formatted correctly
- [ ] Logging shows all requests

**Deliverables**:
- `backend/fastapi-app/api/health.py`

---

### Block 0.5: Better-Auth Setup

#### Task 0.5.1: Initialize Better-Auth Configuration
**Assigned**: @AuthPersonalizer
**Effort**: 1 day
**Dependencies**: Task 0.2.2, Task 0.4.3
**Deliverables**: Better-Auth configuration, database integration

**Description**:
Set up Better-Auth for signup/signin flows.

**Acceptance Criteria**:
- [ ] Better-Auth package installed
- [ ] Database configured (Neon Postgres)
- [ ] User table integration (use existing User model)
- [ ] Email provider configured (for verification emails)
- [ ] JWT configuration (secret, expiry)
- [ ] Password hashing configured (bcrypt)
- [ ] Session storage configured (database)

**Deliverables**:
- Better-Auth config in FastAPI
- Integration with User model

---

#### Task 0.5.2: Create Signup & Signin Endpoints
**Assigned**: @AuthPersonalizer
**Effort**: 1 day
**Dependencies**: Task 0.5.1
**Deliverables**: Auth API routes

**Description**:
Implement signup and signin routes.

**Acceptance Criteria**:
- [ ] `POST /api/auth/signup` works:
  - Request: { email, password }
  - Response: { user_id, token }
  - Email verification sent
  - User created in database
- [ ] `POST /api/auth/signin` works:
  - Request: { email, password }
  - Response: { user_id, token }
  - Validates credentials
  - Returns 401 if invalid
- [ ] Passwords hashed (never plaintext)
- [ ] Email verification required before login
- [ ] Test: signup → verify email → signin

**Deliverables**:
- `backend/fastapi-app/api/auth.py`
- Integration tests

---

#### Task 0.5.3: Create Logout Endpoint & Session Management
**Assigned**: @AuthPersonalizer
**Effort**: 0.5 days
**Dependencies**: Task 0.5.2
**Deliverables**: Logout route, session cleanup

**Description**:
Implement logout and session management.

**Acceptance Criteria**:
- [ ] `POST /api/auth/logout` works:
  - Clears session/token
  - Returns 200
- [ ] Session persists across requests (not lost on page reload)
- [ ] Token expires after time limit
- [ ] Refresh token logic (if applicable)

**Deliverables**:
- Logout endpoint in auth.py

---

### Phase 0 Completion Criteria
- [ ] Git repo initialized, CI/CD pipelines created
- [ ] Docusaurus project created, custom theme foundation built
- [ ] FastAPI server running, database connected
- [ ] Neon Postgres & Qdrant initialized
- [ ] Better-Auth configured
- [ ] Health checks passing
- [ ] No critical errors or warnings
- [ ] All Phase 0 tasks merged to main branch

---

---

## PHASE 1: Core MVP (Weeks 2-5)

### Block 1.1: Custom Docusaurus Components & Styling

#### Task 1.1.1: Build Chapter Page Template & MDX Components
**Assigned**: @FrontendEngineer
**Effort**: 2 days
**Dependencies**: Task 0.3.5
**Deliverables**: MDX layout component, custom chapter components

**Description**:
Create reusable layout for chapter pages with custom components.

**Acceptance Criteria**:
- [ ] `src/theme/DocItem/Layout.tsx` created (MDX page layout)
- [ ] Custom MDX components created:
  - `CodeBlock` (syntax highlighting, copy button)
  - `Quiz` (MCQ, scoring, feedback)
  - `Diagram` (Mermaid/ASCII rendering)
  - `Callout` (Note, Warning, Tip, Success colors)
  - `Video` (responsive embed)
- [ ] Components styled with Tailwind
- [ ] Dark mode works for all components
- [ ] Responsive (mobile-first)
- [ ] Accessible (semantic HTML, ARIA labels)

**Deliverables**:
- `src/theme/DocItem/Layout.tsx`
- `src/components/MDXComponents/` with all components
- Unit tests

---

#### Task 1.1.2: Build Component Library (20+ Base Components)
**Assigned**: @FrontendEngineer
**Effort**: 3 days
**Dependencies**: Task 0.3.2
**Deliverables**: Reusable component library

**Description**:
Create base components for buttons, cards, forms, modals, etc.

**Acceptance Criteria**:
- [ ] Button variants (primary, secondary, link, icon)
- [ ] Card component (chapter preview, feature)
- [ ] Alert/Callout component (success, warning, error, info)
- [ ] Form inputs (TextInput, Select, Checkbox, Radio)
- [ ] Modal dialog
- [ ] Toast notification
- [ ] Loading spinner, skeleton, progress bar
- [ ] Breadcrumbs, pagination, tabs, accordion
- [ ] All components:
  - Styled with Tailwind
  - Dark mode support
  - Responsive
  - Accessible (ARIA, keyboard nav)
  - Tested (unit tests)
- [ ] Storybook or component documentation (optional)

**Deliverables**:
- `src/components/` organized by type
- Unit tests for each component
- Component library documentation

---

#### Task 1.1.3: Complete Navbar Styling & Interactions
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 0.3.3, Task 1.1.2
**Deliverables**: Fully styled navbar

**Description**:
Polish navbar with complete styling and interactions.

**Acceptance Criteria**:
- [ ] Logo and branding polished
- [ ] Module dropdown functional (shows chapters on hover/click)
- [ ] Search input styled (focus states, placeholder)
- [ ] User menu (Login/Signup dropdown, profile dropdown when logged in)
- [ ] Theme toggle smooth (transitions between light/dark)
- [ ] Mobile menu (hamburger icon, drawer animation)
- [ ] Hover states, focus indicators, transitions smooth
- [ ] Responsive at all breakpoints
- [ ] No layout shift or flickering

**Deliverables**:
- Updated Navbar component with styling

---

#### Task 1.1.4: Complete Sidebar Styling & Navigation
**Assigned**: @FrontendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 0.3.4, Task 1.1.2
**Deliverables**: Fully styled sidebar

**Description**:
Polish sidebar with complete styling and chapter navigation.

**Acceptance Criteria**:
- [ ] Module sections collapsible/expandable
- [ ] Chapter links styled (active state highlighted)
- [ ] Progress indicators (% completion shown)
- [ ] Smooth animations on expand/collapse
- [ ] Mobile: drawer (hamburger opens sidebar, overlay closes)
- [ ] Desktop: sticky sidebar (doesn't scroll with content)
- [ ] Search/filter chapters (optional)
- [ ] Responsive at all breakpoints

**Deliverables**:
- Updated Sidebar component with styling

---

#### Task 1.1.5: Implement Responsive Grid Layout for Chapter Content
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 1.1.1
**Deliverables**: Responsive layout with sidebar + content

**Description**:
Create responsive layout that works on all screen sizes.

**Acceptance Criteria**:
- [ ] Desktop (1200px+): navbar + sidebar (20%) + content (80%)
- [ ] Tablet (768-1199px): navbar + collapsible sidebar + content
- [ ] Mobile (<768px): navbar + drawer sidebar + full-width content
- [ ] No horizontal scroll
- [ ] All breakpoints tested
- [ ] Touch-friendly on mobile
- [ ] Dark mode works at all sizes

**Deliverables**:
- Layout CSS/Tailwind classes
- Responsive testing documentation

---

### Block 1.2: Chapter Content Writing

#### Task 1.2.1-1.2.12: Write 12 Chapters (Module 1-4)
**Assigned**: @Educator (primary), @RoboticsExpert (review), @CodeExampleGenerator, @DiagramDescriber
**Effort**: 3 days per chapter (12 chapters = 36 days, parallelized 3/week)
**Dependencies**: Phase 0 complete
**Deliverables**: 12 MDX chapter files

**Description**:
Write all chapters with complete structure (learning outcomes, concepts, exercises, quizzes, further reading).

**Each Chapter Includes**:
- Learning outcomes (3-5, specific, measurable)
- Introduction (motivation, real-world relevance)
- Core concepts sections (2-3, detailed explanations)
- Hands-on exercise (copy-paste ready code)
- Code example(s) (2-3 per chapter, tested)
- Diagrams/visuals (Mermaid or ASCII descriptions)
- Common pitfalls & debugging
- Quiz (5 MCQs, misconception-aligned)
- Key takeaways (3-5 bullets)
- Further reading (links to docs, papers)

**Module 1: ROS 2 Fundamentals** (Weeks 2-3)
- [ ] 1.1: Introduction to ROS 2 (History, motivation, DDS)
- [ ] 1.2: Installation & Setup (Desktop setup, first demo)
- [ ] 1.3: Nodes, Topics, Services (Publisher/Subscriber, request/reply)
- [ ] 1.4: ROS 2 CLI Tools (ros2 topic, service, action, rqt)
- [ ] 1.5: Packages & Workspaces (colcon, ament, package structure)

**Module 2: Simulation Environments** (Weeks 3-4)
- [ ] 2.1: Gazebo Fundamentals (Physics, rendering, plugins)
- [ ] 2.2: URDF & Robot Modeling (Links, joints, coordinate frames)
- [ ] 2.3: Gazebo Plugins & Sensors (Camera, lidar, IMU)
- [ ] 2.4: Unity Robotics Integration (Optional: ROS# bridge)
- [ ] 2.5: Advanced Simulation (World files, spawning, scenarios)

**Module 3: NVIDIA Isaac Sim** (Weeks 4-5)
- [ ] 3.1: Isaac Sim Basics (Omniverse, PhysX, rendering)
- [ ] 3.2: Robot Import & Configuration (URDF/USD, articulation)
- [ ] 3.3: ROS 2 Integration in Isaac (Bridge, publishing)
- [ ] 3.4: Physics-Based Manipulation (Grasping, contact dynamics)
- [ ] 3.5: Perception & Computer Vision (Synthetic data, segmentation)

**Module 4: Vision-Language Models** (Weeks 5)
- [ ] 4.1: VLM Foundations (CLIP, GPT-4V, embeddings)
- [ ] 4.2: VLMs with Robotic Perception (Image → semantic understanding)
- [ ] 4.3: Prompt Engineering for Robotics (Task description, planning)
- [ ] 4.4: LLMs for Robot Planning (Task decomposition, behavior)
- [ ] 4.5: Multimodal Learning & Future Directions (End-to-end visuomotor learning)

**Acceptance Criteria** (per chapter):
- [ ] All sections present (outcomes, concepts, exercise, quiz, takeaways)
- [ ] Learning outcomes aligned to Bloom's levels
- [ ] Code examples tested and runnable
- [ ] Diagrams created (Mermaid or ASCII descriptions)
- [ ] Quiz has 5 questions with clear answers
- [ ] Misconception-aligned distractors
- [ ] No spelling/grammar errors
- [ ] @RoboticsExpert: ✅ scientifically accurate
- [ ] MDX syntax valid
- [ ] ~2000-3000 words per chapter

**Deliverables**:
- 12 MDX files in `docusaurus-site/src/pages/modules/`
- Code example files (Python, C++)
- Diagram descriptions or Mermaid code

---

### Block 1.3: RAG Chatbot Content Indexing & Pipeline

#### Task 1.3.1: Create Chapter Ingestion Pipeline
**Assigned**: @BackendEngineer
**Effort**: 2 days
**Dependencies**: Task 0.2.2, Task 1.2.1+ (chapters exist)
**Deliverables**: Chapter ingestion script

**Description**:
Read MDX chapter files and prepare for embedding.

**Acceptance Criteria**:
- [ ] Script reads all MDX files from `docusaurus-site/src/pages/`
- [ ] Extracts text (removes MDX syntax, code blocks)
- [ ] Preserves metadata (module, chapter, section)
- [ ] Output: structured data (chapter content + metadata)
- [ ] Handles errors gracefully (missing files, malformed MDX)
- [ ] Logging shows progress

**Deliverables**:
- `backend/fastapi-app/services/content_ingestion.py`

---

#### Task 1.3.2: Implement Text Chunking Strategy
**Assigned**: @BackendEngineer
**Effort**: 1 day
**Dependencies**: Task 1.3.1
**Deliverables**: Chunking service

**Description**:
Split chapters into 300-500 token chunks with overlap.

**Acceptance Criteria**:
- [ ] Chunk size: 300-500 tokens (use tiktoken for counting)
- [ ] Overlap: 100 tokens (for context preservation)
- [ ] Metadata preserved: module, chapter, section, content_type
- [ ] All chapters chunked successfully
- [ ] Total chunks: ~100-150 (for 12 chapters)
- [ ] No missing text

**Deliverables**:
- `backend/fastapi-app/services/chunking.py`
- Chunk test data

---

#### Task 1.3.3: Integrate OpenAI Embeddings API
**Assigned**: @BackendEngineer
**Effort**: 1 day
**Dependencies**: Task 1.3.2
**Deliverables**: Embeddings client, batch processor

**Description**:
Generate embeddings for all chunks using OpenAI.

**Acceptance Criteria**:
- [ ] OpenAI API key configured
- [ ] Model: `text-embedding-3-small` (1536 dimensions)
- [ ] Batch embedding (avoid rate limits)
- [ ] Embeddings cached (don't re-embed)
- [ ] Cost tracking (log token usage)
- [ ] All chunks embedded successfully
- [ ] Embeddings verified (dimension 1536)

**Deliverables**:
- `backend/fastapi-app/services/embeddings.py`
- Batch processing script

---

#### Task 1.3.4: Index Embeddings in Qdrant
**Assigned**: @BackendEngineer
**Effort**: 1 day
**Dependencies**: Task 1.3.3, Task 0.2.3
**Deliverables**: Qdrant indexing script

**Description**:
Upsert embeddings and metadata into Qdrant.

**Acceptance Criteria**:
- [ ] Qdrant collection "chapters" populated
- [ ] All chunks indexed with metadata
- [ ] Metadata searchable (filter by module, chapter, content_type)
- [ ] Index tested (search query returns results)
- [ ] Performance acceptable (search latency < 200ms)

**Deliverables**:
- `backend/fastapi-app/services/qdrant_indexing.py`

---

#### Task 1.3.5: Implement Retrieval Pipeline
**Assigned**: @BackendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 1.3.4
**Deliverables**: Retrieval service

**Description**:
Retrieve top-K similar chunks for a user query.

**Acceptance Criteria**:
- [ ] Query embedding generated
- [ ] Qdrant semantic search (top-5 chunks)
- [ ] Results filtered by relevance (confidence > 0.7)
- [ ] Metadata included in results
- [ ] Latency < 500ms (p95)
- [ ] Handles empty results gracefully

**Deliverables**:
- `backend/fastapi-app/services/retrieval.py`

---

#### Task 1.3.6: Implement Ranking & Augmentation
**Assigned**: @BackendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 1.3.5
**Deliverables**: Ranking and prompt augmentation service

**Description**:
Re-rank retrieved chunks and format context for LLM.

**Acceptance Criteria**:
- [ ] Chunks re-ranked by importance (BM25 or heuristic)
- [ ] Low-relevance chunks filtered
- [ ] Context formatted for GPT-4 (markdown, numbered sections)
- [ ] Token count calculated (ensure < 3000 tokens)
- [ ] Sources tracked (which chapters contributed)

**Deliverables**:
- `backend/fastapi-app/services/ranking.py`

---

#### Task 1.3.7: Implement Generation with GPT-4
**Assigned**: @BackendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 1.3.6
**Deliverables**: Chat completion service

**Description**:
Call GPT-4 with system prompt + context + query.

**Acceptance Criteria**:
- [ ] OpenAI GPT-4 API integrated
- [ ] System prompt defined (role, behavior)
- [ ] Context injected into prompt
- [ ] User query added
- [ ] Temperature, max_tokens configured
- [ ] Response parsed and returned
- [ ] Latency acceptable (< 5s p95)
- [ ] Error handling (API errors, timeouts)

**Deliverables**:
- `backend/fastapi-app/services/generation.py`
- Prompt templates

---

#### Task 1.3.8: Create Chat History Storage & API Endpoint
**Assigned**: @BackendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 0.2.2, Task 1.3.7
**Deliverables**: Chat API routes, database storage

**Description**:
Store chat messages and create API endpoints.

**Acceptance Criteria**:
- [ ] POST /api/chatbot/query endpoint:
  - Request: { message, selected_text?, user_id?, context? }
  - Response: { response, sources, confidence, session_id }
  - Authenticated users: save to database
  - Anonymous: don't save
- [ ] GET /api/chatbot/history endpoint:
  - Returns chat history for user
  - Includes timestamps, feedback
- [ ] Chat messages stored in Neon (ChatMessage table)
- [ ] Rate limiting: 10 req/min per user
- [ ] Logging: all queries and responses logged

**Deliverables**:
- `backend/fastapi-app/api/chatbot.py`
- Database models (ChatSession, ChatMessage)

---

### Block 1.4: Authentication Integration

#### Task 1.4.1: Create Frontend Login/Signup Components
**Assigned**: @FrontendEngineer
**Effort**: 2 days
**Dependencies**: Task 1.1.2
**Deliverables**: Login and Signup pages

**Description**:
Build React components for user authentication.

**Acceptance Criteria**:
- [ ] LoginForm component:
  - Email and password inputs
  - "Remember me" checkbox
  - Validation (email format, password length)
  - Error messages
  - Loading state
- [ ] SignupForm component:
  - Email, password, confirm password inputs
  - Terms acceptance checkbox
  - Validation (email format, password strength)
  - CAPTCHA (optional)
  - Email verification flow
- [ ] Both styled with Tailwind
- [ ] Dark mode support
- [ ] Mobile responsive
- [ ] Accessible (ARIA labels, semantic HTML)

**Deliverables**:
- `src/components/Auth/LoginForm.tsx`
- `src/components/Auth/SignupForm.tsx`
- Pages for login and signup

---

#### Task 1.4.2: Implement Frontend Auth State Management
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 1.4.1
**Deliverables**: Auth context, hooks

**Description**:
Manage user authentication state in frontend.

**Acceptance Criteria**:
- [ ] Context API or state management (Redux, Zustand)
- [ ] useAuth hook for accessing user data
- [ ] JWT token stored securely (localStorage or cookie)
- [ ] Token refresh logic
- [ ] Logout clears state
- [ ] Protected routes (redirect if not authenticated)
- [ ] User info (email, profile) available throughout app

**Deliverables**:
- `src/context/AuthContext.tsx` or state management
- `src/hooks/useAuth.ts`
- Protected route wrapper

---

#### Task 1.4.3: Connect Frontend Auth to Backend API
**Assigned**: @FrontendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 1.4.2, Task 0.5.2
**Deliverables**: API client for auth endpoints

**Description**:
Call backend auth endpoints from frontend.

**Acceptance Criteria**:
- [ ] Signup calls POST /api/auth/signup
- [ ] Signin calls POST /api/auth/signin
- [ ] Logout calls POST /api/auth/logout
- [ ] Token stored on successful login
- [ ] Error handling (invalid credentials, server error)
- [ ] Loading states during requests
- [ ] Success notifications (toast)
- [ ] Redirect after successful auth

**Deliverables**:
- `src/services/authService.ts`
- Integration tests

---

### Block 1.5: Frontend-Backend Integration

#### Task 1.5.1: Create API Client & Config
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 1.4.3
**Deliverables**: HTTP client, API configuration

**Description**:
Set up API client for all frontend requests.

**Acceptance Criteria**:
- [ ] HTTP client library (fetch, axios, or similar)
- [ ] Base URL configuration (env-dependent)
- [ ] Request interceptor (add auth token)
- [ ] Response interceptor (handle errors)
- [ ] Error handling (display user-friendly messages)
- [ ] Logging (request/response in dev mode)
- [ ] CORS headers handled

**Deliverables**:
- `src/services/apiClient.ts`
- Configuration (environment variables)

---

#### Task 1.5.2: Create Content Fetching Service
**Assigned**: @FrontendEngineer, @BackendEngineer
**Effort**: 1.5 days
**Dependencies**: Task 1.5.1, Task 1.2.1+
**Deliverables**: Content API endpoints, frontend service

**Description**:
Fetch chapter content from backend to frontend.

**Acceptance Criteria**:
- [ ] Backend endpoints:
  - GET /api/content/chapters (list all chapters)
  - GET /api/content/chapter/{id} (single chapter)
- [ ] Frontend service calls endpoints
- [ ] Chapter content loaded and displayed
- [ ] Chapters render with proper formatting
- [ ] Images/diagrams load correctly
- [ ] Code blocks syntax-highlighted
- [ ] Loading state during fetch

**Deliverables**:
- `backend/fastapi-app/api/content.py`
- `src/services/contentService.ts`

---

#### Task 1.5.3: Add Error Handling & User Feedback
**Assigned**: @FrontendEngineer
**Effort**: 1 day
**Dependencies**: Task 1.5.2
**Deliverables**: Error handling utilities, toast notifications

**Description**:
Display errors and feedback to users.

**Acceptance Criteria**:
- [ ] API errors display toast notifications
- [ ] User-friendly error messages
- [ ] Network errors handled (offline detection)
- [ ] Retry logic for failed requests
- [ ] Loading spinners during requests
- [ ] Success messages on important actions
- [ ] No console errors

**Deliverables**:
- Error handling middleware
- Toast notification component

---

### Phase 1 Completion Criteria
- [ ] All 12 chapters written and published
- [ ] Custom Docusaurus theme complete
- [ ] Components styled and tested
- [ ] RAG chatbot indexed and responding
- [ ] Authentication working (signup, signin, logout)
- [ ] Frontend-backend integration complete
- [ ] All code merged to main
- [ ] Lighthouse score >= 75
- [ ] No critical errors

---

---

## PHASE 2: Personalization (Weeks 4-6)

*[Abbreviated for space; similar structure to above]*

### Block 2.1: User Profiling
- Task 2.1.1: Create onboarding form
- Task 2.1.2: Store profile in database
- Task 2.1.3: Profile update endpoint

### Block 2.2: Content Personalization Engine
- Task 2.2.1: Implement personalization logic
- Task 2.2.2: API endpoint for personalized content
- Task 2.2.3: Test personalization service

### Block 2.3: Chapter Personalization Buttons
- Task 2.3.1: Difficulty toggle component
- Task 2.3.2: Bookmark button component
- Task 2.3.3: Progress indicator

### Block 2.4: Progress Tracking
- Task 2.4.1: Store progress in database
- Task 2.4.2: API endpoints (GET/PUT progress)
- Task 2.4.3: Display progress on dashboard

### Block 2.5: Preference Persistence
- Task 2.5.1: User preferences API
- Task 2.5.2: Frontend preference sync
- Task 2.5.3: Settings page

---

## PHASE 3: Urdu Translation (Weeks 6-8)

*[Abbreviated for space]*

### Block 3.1: Technical Glossary
- Task 3.1.1: Build English-Urdu glossary (100+ terms)
- Task 3.1.2: Share glossary with team

### Block 3.2: Chapter Translation
- Task 3.2.1-3.2.9: Translate 9-10 chapters to Urdu
  - Each chapter: @Translator translates, @RoboticsExpert reviews, @Reviewer QAs
  - 3 chapters/week parallelization

### Block 3.3: Language Toggle
- Task 3.3.1: API endpoint for language selection
- Task 3.3.2: Frontend language toggle button
- Task 3.3.3: Persist language preference

### Block 3.4: QA & Review
- Task 3.4.1: Proofread all Urdu content
- Task 3.4.2: Verify MDX integrity
- Task 3.4.3: Native speaker review

---

## PHASE 4: Advanced Features (Weeks 8-10)

*[Abbreviated for space]*

### Block 4.1: Adaptive Learning
- Task 4.1.1: Quiz difficulty adjustment service
- Task 4.1.2: Learning path recommendation engine
- Task 4.1.3: Display recommendations on homepage

### Block 4.2: Chatbot Enhancements
- Task 4.2.1: Improve retrieval (BM25 hybrid search)
- Task 4.2.2: Text selection → query feature
- Task 4.2.3: Answer feedback mechanism

### Block 4.3: Analytics
- Task 4.3.1: User dashboard service
- Task 4.3.2: Dashboard page
- Task 4.3.3: Chapter analytics

### Block 4.4: Polish & Optimization
- Task 4.4.1: Code splitting & lazy loading
- Task 4.4.2: Image optimization
- Task 4.4.3: Lighthouse audit & improvements

### Block 4.5: Accessibility Audit
- Task 4.5.1: WCAG 2.1 AA audit
- Task 4.5.2: Fix accessibility issues
- Task 4.5.3: Keyboard navigation test

---

## PHASE 5: Testing & QA (Weeks 2-10)

*[Continuous throughout]*

### Block 5.1: Unit Testing
- Task 5.1.1: Frontend component tests (80%+ coverage)
- Task 5.1.2: Backend service tests (80%+ coverage)

### Block 5.2: Integration Testing
- Task 5.2.1: API integration tests
- Task 5.2.2: Database integration tests
- Task 5.2.3: End-to-end workflows

### Block 5.3: Performance Testing
- Task 5.3.1: Lighthouse benchmarking
- Task 5.3.2: API latency testing
- Task 5.3.3: Load testing (concurrent users)

### Block 5.4: Accessibility Testing
- Task 5.4.1: WCAG 2.1 AA audit
- Task 5.4.2: Keyboard navigation test
- Task 5.4.3: Screen reader testing

### Block 5.5: Security Testing
- Task 5.5.1: Input validation testing
- Task 5.5.2: Auth security testing
- Task 5.5.3: Dependency vulnerability scan

### Block 5.6: Content QA
- Task 5.6.1: Spelling & grammar check
- Task 5.6.2: Technical accuracy review
- Task 5.6.3: Code example verification

---

## PHASE 6: Deployment (Week 11)

*[Final phase]*

### Block 6.1: Frontend Deployment
- Task 6.1.1: GitHub Actions CI/CD pipeline
- Task 6.1.2: Build & deploy to GitHub Pages
- Task 6.1.3: Verify deployment

### Block 6.2: Backend Deployment
- Task 6.2.1: Docker image build
- Task 6.2.2: Deploy to Railway/Vercel
- Task 6.2.3: Health checks

### Block 6.3: Database Backups
- Task 6.3.1: Configure Neon backups
- Task 6.3.2: Test backup/restore
- Task 6.3.3: Document recovery procedures

### Block 6.4: Monitoring & Alerting
- Task 6.4.1: Set up error tracking (Sentry)
- Task 6.4.2: Configure alerts (Slack, email)
- Task 6.4.3: Create dashboards

### Block 6.5: Documentation
- Task 6.5.1: Deployment documentation
- Task 6.5.2: Runbooks & procedures
- Task 6.5.3: Team training

---

## Task Summary Statistics

**Total Tasks**: 120+
**Critical Path**: 60+ blocking
**Parallelizable**: 80+ independent

**By Phase**:
- Phase 0: 15 tasks (setup)
- Phase 1: 35 tasks (MVP)
- Phase 2: 15 tasks (personalization)
- Phase 3: 15 tasks (Urdu translation)
- Phase 4: 20 tasks (advanced features)
- Phase 5: 15 tasks (testing, continuous)
- Phase 6: 10 tasks (deployment)

**By Subagent**:
- @FrontendEngineer: 45 tasks (UI/UX, components, styling)
- @BackendEngineer: 35 tasks (APIs, databases, RAG, deployment)
- @Educator: 15 tasks (content writing, pedagogy)
- @RoboticsExpert: 10 tasks (technical review, domain knowledge)
- @AuthPersonalizer: 12 tasks (auth, personalization, preferences)
- @Translator: 12 tasks (Urdu translation, glossary)
- @Reviewer: 15 tasks (testing, QA, validation)
- @SpecArchitect: 5 tasks (orchestration, planning)

---

**Status**: Ready for Task Execution
**Document Version**: 1.0.0
**Last Updated**: 2025-12-24

