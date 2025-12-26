# Physical AI & Humanoid Robotics Interactive Textbook - Specification

**Document**: Specification (SPEC)
**Status**: Draft → Ready for Clarification
**Last Updated**: 2025-12-24
**Author**: Lead AI Architect (Spec-Kit Plus)
**Governance**: Follows Constitution v1.0.0

---

## 1. Project Vision & Scope

### 1.1 Vision
Create an AI-native, interactive, web-based textbook ("Physical AI & Humanoid Robotics") that serves as a comprehensive educational resource for learning robotics fundamentals, AI integration, simulation environments, and vision-language models. The textbook leverages modern web technologies (Docusaurus, React, MDX, Tailwind) with a custom, professional design—**no default themes**—and includes an embedded RAG chatbot for personalized learning support.

### 1.2 Success Criteria
✅ **MVP (Must-Have)**
- Docusaurus site with custom theme (React + Tailwind, dark mode, responsive)
- 4 Core Modules (ROS 2, Gazebo/Unity, NVIDIA Isaac, VLA) with progressive chapters
- Embedded RAG chatbot answering questions on course content
- GitHub Pages deployment with CI/CD pipeline
- Markdown/MDX chapter files with standardized structure
- Basic user authentication (Better-Auth)

✅ **Bonus Goals (Maximize Points)**
- Reusable Claude Code subagents + custom skills
- User personalization (background collection, content adaptation)
- Per-chapter buttons: difficulty toggle, Urdu translation
- Comprehensive Prompt History Records (PHRs) throughout
- Architecture Decision Records (ADRs) for major decisions

### 1.3 Out of Scope
- Mobile native apps (web-responsive only)
- Advanced ML model training (use pre-trained OpenAI models)
- Proprietary robot simulation (focus on open-source: ROS 2, Gazebo, Isaac Sim)
- Payment systems or licensing (educational, open content)

---

## 2. Project Structure & Architecture Overview

### 2.1 Directory Structure (Planned)
```
physical-ai-humanoid-robotics-book/
├── .claude/
│   ├── skills/
│   │   ├── chapter-writer.skill.md
│   │   ├── custom-ui-component.skill.md
│   │   ├── personalization-engine.skill.md
│   │   ├── urdu-translator.skill.md
│   │   └── bonus-validator.skill.md
│   └── commands/
│       └── sp.*.md (Spec-Kit Plus commands)
├── .specify/
│   ├── memory/
│   │   └── constitution.md
│   ├── templates/
│   │   ├── spec-template.md
│   │   ├── plan-template.md
│   │   ├── phr-template.prompt.md
│   │   └── adr-template.md
│   └── scripts/
├── specs/
│   ├── core/
│   │   ├── spec.md (this file)
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── rag-chatbot/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   └── personalization/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── history/
│   ├── prompts/ (PHRs)
│   │   ├── constitution/
│   │   ├── core/
│   │   ├── rag-chatbot/
│   │   ├── personalization/
│   │   └── general/
│   └── adr/ (ADRs)
├── docusaurus-site/
│   ├── docusaurus.config.js
│   ├── src/
│   │   ├── components/ (custom React components)
│   │   │   ├── CustomTheme/ (navbar, sidebar, layout)
│   │   │   ├── RagChatbot/ (embedded chatbot UI)
│   │   │   ├── PersonalizationPanel/ (user preferences)
│   │   │   └── shared/ (buttons, cards, modals)
│   │   ├── pages/ (MDX chapter pages)
│   │   │   ├── module-1/ (ROS 2)
│   │   │   ├── module-2/ (Gazebo/Unity)
│   │   │   ├── module-3/ (NVIDIA Isaac)
│   │   │   ├── module-4/ (VLA)
│   │   │   └── appendix/
│   │   ├── css/
│   │   │   ├── tailwind.css
│   │   │   └── custom.css
│   │   └── data/ (metadata, course outline)
│   ├── static/ (diagrams, images)
│   ├── package.json
│   └── .env.local (dev secrets, not in git)
├── backend/
│   ├── fastapi-app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── auth.py (Better-Auth integration)
│   │   │   ├── chatbot.py (RAG endpoints)
│   │   │   └── personalization.py (user preferences)
│   │   ├── services/
│   │   │   ├── rag_engine.py (Qdrant + embeddings)
│   │   │   ├── openai_client.py
│   │   │   └── user_service.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── chat_history.py
│   │   │   └── document.py
│   │   ├── requirements.txt
│   │   └── .env (prod secrets via GitHub Secrets)
│   └── docker/
│       └── Dockerfile
├── .github/
│   ├── workflows/
│   │   ├── docusaurus-build.yml
│   │   ├── backend-deploy.yml
│   │   └── tests.yml
│   └── ISSUE_TEMPLATE/
├── tests/
│   ├── unit/
│   │   ├── components/ (React component tests)
│   │   ├── services/ (backend unit tests)
│   │   └── utils/
│   └── integration/
│       ├── rag_pipeline.test.py
│       ├── auth_flow.test.ts
│       └── personalization.test.ts
├── docs/ (documentation for developers)
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── API.md
│   └── DEPLOYMENT.md
├── CLAUDE.md (project instructions)
├── CONTRIBUTING.md
└── README.md
```

### 2.2 Tech Stack (Detailed)

| Layer | Tech | Version | Purpose |
|-------|------|---------|---------|
| **Frontend Framework** | Docusaurus | 3.x | Static site generator, MDX support |
| **UI Library** | React | 18+ | Component system |
| **Styling** | Tailwind CSS | 3.x | Custom theme, utility-first CSS |
| **Animation** | Framer Motion | 11+ | Smooth transitions, interactions |
| **Markup Format** | MDX | 2.x | Markdown + React components |
| **Package Manager** | npm/pnpm | latest | Dependency management |
| **Backend Framework** | FastAPI | 0.104+ | REST API for RAG, auth, personalization |
| **Database (Relational)** | Neon Postgres | latest | User data, chat history, content metadata |
| **Vector DB** | Qdrant | 1.7+ | Embeddings storage for RAG |
| **LLM/Embeddings** | OpenAI API | GPT-4 + text-embedding-3-small | Chatbot responses, vector embeddings |
| **Auth** | Better-Auth | latest | User signup/signin, session management |
| **Deployment (Static)** | GitHub Pages | N/A | Host Docusaurus build |
| **Deployment (Backend)** | Railway/Vercel | N/A | Host FastAPI backend |
| **CI/CD** | GitHub Actions | N/A | Automated build, test, deploy |
| **Language (Frontend)** | TypeScript | 5.x | Type-safe React code |
| **Language (Backend)** | Python | 3.11+ | FastAPI, data science libs |
| **Testing Framework** | Vitest + Jest | latest | Frontend unit tests |
| **Testing Framework** | Pytest | latest | Backend unit & integration tests |

### 2.3 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser / Client                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Docusaurus Site (GitHub Pages)                  │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ Custom Theme (React + Tailwind)                │    │   │
│  │  │ - Responsive navbar, sidebar, layout           │    │   │
│  │  │ - Dark/light mode toggle                       │    │   │
│  │  │ - Course navigation, progress tracking         │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ Chapter Pages (MDX)                            │    │   │
│  │  │ - Module 1: ROS 2, Module 2: Gazebo/Unity     │    │   │
│  │  │ - Module 3: NVIDIA Isaac, Module 4: VLA       │    │   │
│  │  │ - Quizzes, code examples, diagrams            │    │   │
│  │  │ - Per-chapter: Difficulty toggle, Urdu btn    │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ Embedded RAG Chatbot Component                 │    │   │
│  │  │ - Widget (bottom-right or sidebar)             │    │   │
│  │  │ - Text selection → direct query                │    │   │
│  │  │ - Context-aware responses                      │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ Personalization Panel                          │    │   │
│  │  │ - User login/signup (Better-Auth)              │    │   │
│  │  │ - Background: software/hardware level          │    │   │
│  │  │ - Content adaptation, bookmarks                │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↕ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                           │
│  Hosted on: Railway / Vercel / Self-Hosted                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ / Endpoints                                              │   │
│  │ - POST /api/auth/signup, /api/auth/signin               │   │
│  │ - GET /api/user/profile, PUT /api/user/preferences      │   │
│  │ - POST /api/chatbot/query, GET /api/chatbot/history     │   │
│  │ - GET /api/content/chapters, /api/content/metadata      │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Services                                                 │   │
│  │ - RAG Engine: query Qdrant, call OpenAI, format answer  │   │
│  │ - User Service: fetch/update profile, preferences       │   │
│  │ - OpenAI Client: embeddings, chat completions           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ↕ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                     Databases & Services                         │
│                                                                  │
│  ┌──────────────────────────┐     ┌──────────────────────────┐  │
│  │ Neon Postgres            │     │ Qdrant Vector DB         │  │
│  │ - Users & profiles       │     │ - Embeddings             │  │
│  │ - Chat history           │     │ - Chunked content        │  │
│  │ - Content metadata       │     │ - Indexed for fast query │  │
│  │ - Personalization prefs  │     │                          │  │
│  └──────────────────────────┘     └──────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────┐     ┌──────────────────────────┐  │
│  │ OpenAI API               │     │ GitHub Pages             │  │
│  │ - Chat completions       │     │ - Static site hosting    │  │
│  │ - Embeddings generation  │     │ - CI/CD via Actions      │  │
│  └──────────────────────────┘     └──────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Modules & Course Structure

### 3.1 Module Breakdown (Weekly Schedule)

#### **Module 1: ROS 2 Fundamentals** (Weeks 1-3)
- **Chapter 1.1**: Introduction to ROS 2
  - History, ROS 1 vs. ROS 2, use cases
  - Learning outcome: Understand ROS 2 motivation, DDS middleware
- **Chapter 1.2**: ROS 2 Installation & Setup
  - Desktop installation, environment setup, first node
  - Learning outcome: Run talker/listener demo
- **Chapter 1.3**: Nodes, Topics, Services, Actions
  - Publisher/subscriber pattern, request/reply, long-running tasks
  - Learning outcome: Create custom node with topic communication
- **Chapter 1.4**: ROS 2 CLI Tools & Debugging
  - `ros2 topic`, `ros2 service`, `ros2 action`, rqt tools
  - Learning outcome: Inspect running system, debug communication
- **Chapter 1.5**: ROS 2 Packages & Workspaces
  - Package structure, ament build system, colcon
  - Learning outcome: Create and build custom package

#### **Module 2: Simulation Environments** (Weeks 4-6)
- **Chapter 2.1**: Gazebo Simulation Fundamentals
  - Physics engine, visual rendering, plugin architecture
  - Learning outcome: Launch Gazebo, load robot model
- **Chapter 2.2**: URDF & Robot Modeling
  - Unified Robot Description Format, links, joints, sensors
  - Learning outcome: Create simple robot URDF, visualize in Gazebo
- **Chapter 2.3**: Gazebo Plugins & Sensors
  - Camera, lidar, IMU simulation, actuator plugins
  - Learning outcome: Simulate robot with sensors in Gazebo
- **Chapter 2.4**: Unity Robotics Integration (Optional Alt)
  - ROS Sharp, robot simulation in Unity
  - Learning outcome: Run robot in Unity + ROS 2 bridge
- **Chapter 2.5**: Advanced Simulation & Scenario Testing
  - World files, physics tuning, spawning models dynamically
  - Learning outcome: Create multi-robot scenario with terrain

#### **Module 3: NVIDIA Isaac Sim** (Weeks 7-9)
- **Chapter 3.1**: NVIDIA Isaac Sim Basics
  - Omniverse platform, Isaac Sim features, PhysX engine
  - Learning outcome: Launch Isaac Sim, load robot
- **Chapter 3.2**: Robot Import & Configuration
  - URDF/USD import, articulation setup, sensor configuration
  - Learning outcome: Configure humanoid robot in Isaac Sim
- **Chapter 3.3**: ROS 2 Integration in Isaac Sim
  - ROS 2 bridge, topic publishing, Omniverse APIs
  - Learning outcome: Control robot via ROS 2 from Isaac Sim
- **Chapter 3.4**: Physics-Based Manipulation
  - Grasping, contact dynamics, trajectory planning in sim
  - Learning outcome: Simulate pick-and-place task
- **Chapter 3.5**: Perception & Computer Vision in Sim
  - Synthetic data generation, segmentation, depth sensing
  - Learning outcome: Generate labeled dataset for vision tasks

#### **Module 4: Vision-Language Models & AI Integration** (Weeks 10-12)
- **Chapter 4.1**: Foundations of Vision-Language Models
  - VLM architecture (CLIP, GPT-4V), multimodal embeddings
  - Learning outcome: Understand VLM internals, use GPT-4V API
- **Chapter 4.2**: Integrating VLMs with Robotic Perception
  - Robot image → VLM → semantic understanding
  - Learning outcome: Classify objects, answer "what do you see?"
- **Chapter 4.3**: Prompt Engineering for Robotics
  - Crafting prompts for task description, object recognition
  - Learning outcome: Generate robot task plans from natural language
- **Chapter 4.4**: Large Language Models for Robot Planning
  - Using LLMs (GPT-4, Claude) for motion planning, task decomposition
  - Learning outcome: Generate robot behavior from text instructions
- **Chapter 4.5**: Multimodal Learning & Future Directions
  - End-to-end visuomotor learning, real-world deployment
  - Learning outcome: Design AI-driven robot behavior

### 3.2 Chapter Template & Standards

Each chapter `.mdx` file includes:
```mdx
---
id: module-X-chapter-Y
title: Chapter Title
sidebar_label: Short Title
sidebar_position: Y
---

import { Quiz, CodeBlock, Diagram, Video, Callout } from '@site/src/components';

## Learning Outcomes
- [ ] Outcome 1
- [ ] Outcome 2
- [ ] Outcome 3

## Introduction
[Contextual introduction, motivation]

## Core Concepts
### Concept 1
[Explanation with diagrams/images]

### Concept 2
[Explanation, code examples]

## Hands-On Exercise
[Step-by-step walkthrough, copy-paste code]

<CodeBlock language="python" title="example.py">
{`# Runnable code example
...
`}</CodeBlock>

## Quiz
<Quiz
  questions={[
    { q: "Question 1?", options: [...], answer: 0 },
    ...
  ]}
/>

## Further Reading
- [External reference 1](url)
- [ROS 2 docs](https://docs.ros.org/)

## Summary
[Key takeaways]
```

---

## 4. RAG Chatbot Specification

### 4.1 Overview
An embedded, context-aware chatbot trained on the full textbook content. Users can:
- Ask questions in natural language
- Select text and query the chatbot directly
- Receive answers grounded in course materials
- View chat history (if authenticated)

### 4.2 Architecture

**Frontend (React Component)**:
- Floating widget or sidebar chat interface
- Input field for text questions
- Chat history display (scrollable, with timestamps)
- "Copy" and "Ask" buttons for selected text
- Typing indicators, error handling

**Backend (FastAPI)**:
```
POST /api/chatbot/query
{
  "message": "What is ROS 2?",
  "selected_text": "...",  // optional
  "user_id": "uuid",        // optional, for history
  "context": {              // optional session context
    "current_chapter": "module-1-chapter-1",
    "language": "en"  // or "ur" for Urdu
  }
}
→ Response:
{
  "response": "ROS 2 is a middleware...",
  "sources": ["module-1-chapter-1", "module-1-chapter-2"],
  "confidence": 0.92,
  "session_id": "..."
}
```

**RAG Pipeline**:
1. **Embedding**: Convert user query to vector using OpenAI `text-embedding-3-small`
2. **Retrieval**: Query Qdrant for top-K similar chunks (K=5)
3. **Ranking**: Re-rank by relevance, filter low-confidence matches
4. **Augmentation**: Format retrieved chunks as context
5. **Generation**: Call GPT-4 with system prompt + context + user query
6. **Filtering**: Ensure answer is grounded in content, mark out-of-scope questions

### 4.3 Content Indexing
- **Chunking**: Split chapters into ~300-500 token chunks with overlap
- **Metadata**: Tag each chunk with module, chapter, section, content_type (theory/code/quiz)
- **Versioning**: Version content in Qdrant; migrate on major updates
- **External Refs**: Include ROS 2 docs, Gazebo tutorials, NVIDIA Isaac docs as supplementary sources

### 4.4 Quality & Safety
- **Accuracy Metrics**: Track user feedback (thumbs up/down) on answers
- **Guardrails**: System prompt enforces textbook-grounded responses; reject questions outside scope
- **Rate Limiting**: 10 req/min per user (authenticated), 1 req/min (anonymous)
- **Logging**: Log all queries, responses, user feedback for continuous improvement

---

## 5. User Personalization & Authentication

### 5.1 Authentication (Better-Auth)
- **Signup**: Email + password, email verification
- **Signin**: Standard login flow, JWT session tokens
- **Logout**: Clear session
- **Profile**: Store user metadata (name, email, background)

### 5.2 User Background Collection
At signup, collect:
- **Software Experience**: Beginner / Intermediate / Advanced (Python, ROS)
- **Hardware Experience**: No robotics / Assembled robots / Built custom robots
- **Learning Goal**: Fundamentals / Specialization / Research

### 5.3 Content Personalization
Based on background, adapt:
- **Chapter Difficulty**: Show basic OR advanced explanations (toggle button)
- **Code Examples**: Filter to relevant language/framework
- **Recommended Path**: Suggest chapters based on learning goal
- **Progress Tracking**: Bookmark chapters, quiz scores, time spent

### 5.4 Per-Chapter Personalization Buttons

**Difficulty Toggle**:
```
[ Basic ]  [ Advanced ]
```
- **Basic**: Simplified explanations, fundamental concepts only
- **Advanced**: In-depth theory, research references, optimization tricks

**Urdu Translation**:
```
[ English ]  [ اردو ]
```
- Toggles chapter text to Urdu translation (human-translated or AI-assisted)
- Code comments, technical terms preserved in English
- Translations reviewed by native speakers

**Bookmarking & Progress**:
```
[ ★ Bookmark ]  [ Progress: 45% ]
```
- Save chapter for later review
- Quiz score + time-spent tracking

### 5.5 Database Schema (Neon Postgres)

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  created_at TIMESTAMP,
  background_software VARCHAR,  -- beginner|intermediate|advanced
  background_hardware VARCHAR,  -- none|assembled|custom
  learning_goal VARCHAR,         -- fundamentals|specialization|research
  preferred_language VARCHAR DEFAULT 'en'  -- en|ur
);

-- Chat History
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE chat_messages (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES chat_sessions(id),
  role VARCHAR,  -- user|assistant
  content TEXT,
  timestamp TIMESTAMP,
  feedback INT  -- -1 (bad), 0 (neutral), 1 (good)
);

-- Content Metadata
CREATE TABLE chapters (
  id VARCHAR PRIMARY KEY,
  module INT,
  chapter INT,
  title VARCHAR,
  content_type VARCHAR  -- theory|code|quiz
);

-- User Progress
CREATE TABLE user_progress (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  chapter_id VARCHAR REFERENCES chapters(id),
  completion_pct INT,
  quiz_score INT,
  time_spent_sec INT,
  bookmarked BOOLEAN,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Preferences
CREATE TABLE user_preferences (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  dark_mode BOOLEAN DEFAULT TRUE,
  preferred_language VARCHAR DEFAULT 'en',
  show_advanced BOOLEAN DEFAULT FALSE,
  auto_translate BOOLEAN DEFAULT FALSE,
  updated_at TIMESTAMP
);
```

---

## 6. Custom Docusaurus Theme & UI Design

### 6.1 Theme Architecture
- **Disable Defaults**: Set `swizzle: { disableDefaultTheme: true }` in `docusaurus.config.js`
- **Custom Layout**: Build custom `<Layout>` component with navbar, sidebar, footer
- **Component System**: Tailwind-based reusable components (buttons, cards, alerts, modals)

### 6.2 Custom Navbar
- **Logo & Branding**: Project title, custom icon (robot or book icon)
- **Course Navigation**: Dropdown for Module 1-4, chapter links
- **Search**: Algolia or local search integration
- **User Menu**: Login/Signup or User profile (name, settings)
- **Theme Toggle**: Dark/light mode switch (top-right)
- **Responsive**: Hamburger menu on mobile

### 6.3 Custom Sidebar
- **Hierarchical Navigation**: Modules → Chapters → Sections
- **Collapsible**: Expand/collapse module trees
- **Active Indicator**: Highlight current page
- **Progress Indicators**: Visual completion % for each chapter (if authenticated)
- **Floating**: Sticky on desktop, collapsible drawer on mobile

### 6.4 Custom Footer
- **Links**: Documentation, GitHub repo, issue tracker
- **Copyright**: Hackathon project, educational use
- **Social**: Links to team members' GitHub, LinkedIn (optional)

### 6.5 Color Scheme & Typography
- **Primary Colors**:
  - Light: `#FFFFFF` (white), `#F5F7FA` (light gray)
  - Dark: `#0F1419` (dark blue-gray), `#1C1F26` (darker)
  - Accent: `#4A90E2` (blue) for links, buttons, highlights
- **Typography**:
  - Headings: Inter, 700 weight (modern, clear)
  - Body: Inter, 400 weight (readable, accessible)
  - Code: "Courier New" or Fira Code, 12px

### 6.6 Animations
- **Page Transitions**: Fade-in/slide-in effects (Framer Motion)
- **Interactive Elements**: Hover states, button animations, loading states
- **Scroll**: Smooth scrolling, progress indicator

### 6.7 Responsive Design
- **Desktop** (1200px+): Full sidebar, 2-column layout
- **Tablet** (768px–1199px): Collapsible sidebar, single column
- **Mobile** (<768px): Drawer navigation, stacked layout, full-width content

### 6.8 Accessibility (WCAG 2.1 AA)
- Semantic HTML (`<header>`, `<nav>`, `<main>`, `<footer>`)
- Alt text for all diagrams and images
- Keyboard navigation (Tab through navbar, sidebar, buttons)
- Color contrast: 4.5:1 for text, 3:1 for graphics
- Focus indicators: Clear, visible focus outlines

---

## 7. Integration Points & APIs

### 7.1 Frontend ↔ Backend Communication
All communication via HTTPS REST API:
```
API Base URL: https://api.example.com/api
```

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/signup` | POST | Register new user |
| `/auth/signin` | POST | Login |
| `/auth/logout` | POST | Logout |
| `/user/profile` | GET | Fetch user profile |
| `/user/preferences` | GET/PUT | User settings, language preference |
| `/chatbot/query` | POST | Submit chatbot query |
| `/chatbot/history` | GET | Fetch chat history |
| `/content/chapters` | GET | List all chapters + metadata |
| `/content/chapter/{id}` | GET | Fetch chapter content + metadata |
| `/user/progress/{chapter_id}` | GET/PUT | Track completion, quiz scores |

### 7.2 Docusaurus ↔ FastAPI
- **Frontend**: Next.js-style client-side API calls via `fetch()` or Axios
- **Authentication**: JWT in `Authorization: Bearer <token>` header
- **CORS**: Allow requests from `https://pages.github.io` + localhost

### 7.3 OpenAI Integration
- **Models**:
  - `gpt-4` for chatbot responses
  - `text-embedding-3-small` for embeddings
- **API Key**: Store in GitHub Secrets, pass to FastAPI backend via env vars
- **Cost Optimization**: Cache embeddings, reuse vectors where possible

### 7.4 Neon & Qdrant Integration
- **Neon Connection**: `postgresql://user:pass@host/dbname`
- **Qdrant Connection**: `http://qdrant-host:6333` or `https://...`
- **Both**: Credentials in `.env` (never in git)

---

## 8. Deployment & DevOps

### 8.1 Frontend Deployment (GitHub Pages)
- **Trigger**: Push to `main` branch
- **CI/CD**: GitHub Actions workflow (`.github/workflows/docusaurus-build.yml`)
  1. Install dependencies (`npm install`)
  2. Run type check (`tsc --noEmit`)
  3. Run tests (`npm test`)
  4. Build Docusaurus (`npm run build`)
  5. Deploy to GitHub Pages (automatic)
- **URL**: `https://<username>.github.io/physical-ai-humanoid-robotics-book/`

### 8.2 Backend Deployment (FastAPI)
- **Container**: Docker image (Python 3.11 + FastAPI)
- **Registry**: Docker Hub or GitHub Container Registry
- **Hosting**: Railway, Vercel, or self-hosted VPS
- **CI/CD**: GitHub Actions workflow (`.github/workflows/backend-deploy.yml`)
  1. Run linting (`flake8`, `black`)
  2. Run type checks (`mypy`)
  3. Run tests (`pytest`)
  4. Build and push Docker image
  5. Deploy to hosting platform
- **Environment**: GitHub Secrets for API keys, DB credentials

### 8.3 Database Deployment
- **Neon**: Managed Postgres (no setup required, use connection string)
- **Qdrant**: Managed cloud or self-hosted Docker container
- **Backups**: Neon auto-backups; Qdrant snapshots via API

### 8.4 Monitoring & Logging
- **Frontend**: Sentry for error tracking
- **Backend**: FastAPI logging (structured JSON logs), Sentry
- **Database**: Neon monitoring dashboard, Qdrant metrics
- **Alerts**: Email/Slack on critical errors

---

## 9. Testing Strategy

### 9.1 Frontend Testing
- **Unit Tests**: React components (Vitest + React Testing Library)
  - Test: Navbar rendering, theme toggle, button clicks
  - Coverage: 80%+
- **Integration Tests**: User login → chatbot query → response display
  - Mock API calls, test end-to-end flows
- **E2E Tests** (Optional): Playwright or Cypress for full workflows

### 9.2 Backend Testing
- **Unit Tests**: FastAPI routes, service functions (Pytest)
  - Test: Auth endpoints, RAG query logic, user preference updates
  - Coverage: 85%+
- **Integration Tests**: FastAPI + Neon + Qdrant
  - Test: Full RAG pipeline (embedding → retrieval → generation)
  - Test: User signup → profile update → chatbot query
- **Load Tests** (Optional): Locust for API performance

### 9.3 Content Quality
- **Accuracy Review**: RoboticsExpert reviews all chapters
- **Completeness**: Educator checks learning outcomes, quiz correctness
- **Code Examples**: Run and verify all code snippets
- **Links**: Check external references (ROS 2 docs, NVIDIA docs)

---

## 10. Success Metrics & Acceptance Criteria

### 10.1 Functional Requirements (MVP)
- ✅ Docusaurus site builds and deploys to GitHub Pages without errors
- ✅ Custom theme (no defaults) with working navbar, sidebar, footer
- ✅ All 12 chapters present with MDX content, learning outcomes, code examples
- ✅ RAG chatbot responsive to queries, grounded in content
- ✅ User authentication (signup/signin) functional
- ✅ Personalization: difficulty toggle, Urdu translation buttons work

### 10.2 Non-Functional Requirements
- ✅ Page load time <3 seconds (Lighthouse score 80+)
- ✅ Chatbot response time <5 seconds (p95)
- ✅ Mobile responsive (all breakpoints)
- ✅ WCAG 2.1 AA accessibility compliance
- ✅ Dark mode functional across all pages
- ✅ All code examples copy-pasteable and runnable

### 10.3 Bonus Goals (Point Multipliers)
- ⭐ Reusable Claude Code skills for chapter writing, UI components, translation
- ⭐ Prompt History Records (PHRs) for all major development phases
- ⭐ Architecture Decision Records (ADRs) documenting key design choices
- ⭐ User background collection + content adaptation
- ⭐ Urdu translation (human-reviewed or AI-assisted) for all chapters
- ⭐ Advanced personalization: per-user learning paths, recommendations
- ⭐ Quiz/assessment system with score tracking and feedback

---

## 11. Risk Analysis & Mitigation

### 11.1 Top Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| RAG chatbot provides inaccurate answers | High | Medium | Extensive testing, guardrails, feedback loop for continuous improvement |
| Content writing (12 chapters) takes too long | High | High | Use Claude Code agents for content drafting, Educator reviews in parallel |
| Custom Docusaurus theme has bugs/performance issues | Medium | Medium | Early prototyping, component library testing, Lighthouse audits |
| Database scaling issues (many concurrent users) | Medium | Low | Use managed services (Neon, Qdrant), load testing, caching strategies |
| Deployment pipeline failures | Medium | Low | Automated tests, staging environment, rollback procedures |

### 11.2 Mitigation Strategies
- **Content**: Delegate to @Educator + @RoboticsExpert early; use AI-assisted drafting
- **Frontend**: Build theme incrementally, test on multiple devices, focus on core UX first
- **Backend**: Load test RAG pipeline, implement caching, monitor API costs
- **Deployment**: Pre-commit hooks, automated tests gate all PRs, canary deployments

---

## 12. Clarification Questions (To Be Addressed)

Before moving to PLAN phase:

1. **Course Content Source**: Is there an existing syllabus/outline to follow, or should we create from scratch based on best practices?
2. **Urdu Translation**: Human-translated by domain expert, or AI-assisted (ChatGPT) with review?
3. **External Content**: Can we embed/link to external resources (ROS 2 docs, Gazebo tutorials, NVIDIA Isaac docs), or copy content?
4. **Backend Hosting**: Preferred platform for FastAPI backend (Railway, Vercel, self-hosted)?
5. **VLM Module Depth**: Should Module 4 include hands-on coding labs, or conceptual explanations only?
6. **User Personalization**: Should content adaptation be real-time (server-rendered) or client-side (JavaScript)?
7. **Chatbot Training Data**: External sources (ROS 2 docs, research papers) or textbook-only?

---

## 13. Next Steps (Approval Path)

1. ✅ **This SPEC**: Review and approve core architecture, tech stack, module structure
2. 📋 **Clarification** (sp.clarify): Address questions in Section 12
3. 📐 **PLAN** (sp.plan): Detail implementation phases, subagent assignments
4. ✓ **TASKS** (sp.tasks): Break into specific, testable work items
5. 🔍 **ANALYZE** (sp.analyze): Cross-artifact consistency check
6. 🚀 **IMPLEMENT** (sp.implement): Execute tasks in parallel with subagents
7. 📝 **ADRs**: Document major architectural decisions
8. 🎯 **REVIEW**: QA, bonus validation, final checks
9. 🚢 **DEPLOY**: GitHub Pages + backend hosting, production launch

---

**Status**: Ready for user review and clarification
**Owner**: @SpecArchitect
**Version**: 1.0.0-draft
**Last Updated**: 2025-12-24

