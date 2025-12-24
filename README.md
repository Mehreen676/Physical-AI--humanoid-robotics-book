# Physical AI & Humanoid Robotics: An Interactive AI-Native Textbook

**Panaversity Hackathon I Project** | **Status**: Phase 0 (In Progress) | **Last Updated**: 2025-12-24

An open-source, interactive textbook on Physical AI and Humanoid Robotics. Designed for learners worldwide with:

- 📚 **12 comprehensive chapters** covering ROS 2, Gazebo/Unity, NVIDIA Isaac, and Vision Language Models (VLA)
- 🤖 **Embedded RAG chatbot** for question answering with sources cited from course material
- 🎯 **Personalized learning** - adaptive difficulty, language (Urdu + English), background-specific examples
- 🎨 **Custom interactive UI** - built with React, Tailwind CSS, and Docusaurus 3
- 🔐 **User authentication** - signup, email verification, personalized profiles
- 💾 **Modern tech stack** - FastAPI, Neon Postgres, Qdrant vector DB, OpenAI GPT-4

## Quick Links

- 📖 **Live Site** (Coming Week 2): https://physical-ai-humanoid-robotics-book.pages.dev
- 📋 **Specification**: [specs/core/spec.md](specs/core/spec.md)
- 📅 **Implementation Plan**: [specs/core/plan.md](specs/core/plan.md)
- ✅ **Task List**: [specs/core/tasks.md](specs/core/tasks.md)
- 🏗️ **Project Constitution**: [.specify/memory/constitution.md](.specify/memory/constitution.md)
- 🏛️ **Architecture Decisions**: [history/adr/](history/adr/)

## Directory Structure

```
physical-ai-humanoid-robotics-book/
├── docusaurus-site/           # Frontend: Docusaurus 3 + custom theme
│   ├── src/
│   │   ├── theme/             # Custom React theme (no defaults)
│   │   ├── components/        # Reusable UI components (20+)
│   │   └── css/               # Tailwind + custom styles
│   ├── docs/                  # 12 MDX chapters
│   ├── docusaurus.config.js   # Docusaurus configuration
│   └── package.json
├── backend/                   # Backend: FastAPI + RAG chatbot
│   ├── app/
│   │   ├── api/               # API endpoints (auth, chatbot, content, progress)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── services/          # Business logic (RAG, personalization)
│   │   └── core/              # Configuration, utilities
│   ├── main.py                # FastAPI app entry
│   ├── requirements.txt        # Python dependencies
│   └── pyproject.toml
├── specs/                     # Specification artifacts
│   └── core/
│       ├── spec.md            # Full technical specification
│       ├── plan.md            # Implementation plan (6 phases)
│       └── tasks.md           # 120+ atomic work items
├── history/                   # Audit trail
│   ├── adr/                   # Architecture Decision Records
│   └── prompts/               # Prompt History Records (PHRs)
├── .claude/                   # Claude Code configuration
│   ├── agents/                # 8 specialized subagents
│   ├── skills/                # 7 reusable AI skills
│   └── PHASE-0-*-BRIEF.md     # Phase 0 task briefs
├── .specify/                  # Spec-Kit Plus templates & scripts
├── CLAUDE.md                  # Claude Code rules & guidelines
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

## Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Docusaurus | 3.x | Static site generator with custom theme |
| | React | 18.x | UI framework |
| | TypeScript | 5.x | Type-safe JavaScript |
| | Tailwind CSS | 3.x | Utility-first styling |
| | Framer Motion | Latest | Animations & interactions |
| **Backend** | FastAPI | 0.104+ | Modern Python web framework |
| | Python | 3.10+ | Runtime |
| **Database** | Neon Postgres | Latest | Serverless relational DB |
| | Qdrant | 1.7+ | Vector DB for RAG |
| **AI/ML** | OpenAI API | Latest | GPT-4 (generation), embeddings |
| **Auth** | Better-Auth | Latest | Modern authentication |
| **Deployment** | GitHub Pages | - | Frontend hosting |
| | Railway/Vercel | - | Backend hosting |
| | GitHub Actions | - | CI/CD pipeline |

## Getting Started

### Prerequisites

- Node.js 18+ & npm/yarn
- Python 3.10+
- Git

### Phase 0 Setup (3 Days)

#### 1. Clone and Configure

```bash
git clone <repo-url>
cd physical-ai-humanoid-robotics-book

# Copy environment template
cp .env.example .env.local
# Edit .env.local with your API keys (OpenAI, Neon, Qdrant, SendGrid)
```

#### 2. Backend Setup (Day 1-2)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Note: Database setup requires Neon Postgres account & connection string
# See PHASE-0-BACKEND-ENGINEER-BRIEF.md for details
```

#### 3. Frontend Setup (Day 1-2)

```bash
cd docusaurus-site

# Install Node dependencies
npm install

# Start development server
npm run start

# Visit http://localhost:3000
```

### Running the Full Stack

```bash
# Terminal 1: Backend (from project root)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend (from project root)
cd docusaurus-site
npm run start

# Terminal 3: Monitor (optional)
cd .claude
# Monitor tasks in specs/core/tasks.md
```

## Phases & Timeline

**Phase 0** (Week 1, Days 1-3): Repository & infrastructure setup
- ✅ Initialize Docusaurus custom theme
- ✅ Set up FastAPI backend skeleton
- ✅ Configure Neon Postgres & Qdrant
- ✅ Implement Better-Auth signup/signin/logout

**Phase 1** (Weeks 2-5): MVP Development
- Write 12 chapters (3/week)
- Build RAG chatbot (embedding → retrieval → generation)
- Implement authentication with email verification
- Create custom UI components & responsive design

**Phase 2** (Weeks 4-6): Personalization
- User profiling system (background, learning goal, experience)
- Content adaptation (difficulty level, language, examples)
- Progress tracking and learning analytics

**Phase 3** (Weeks 6-8): Urdu Localization
- Translate all 12 chapters to Urdu
- Translate UI (navbar, sidebar, buttons, messages)
- Create Urdu-specific examples and code samples

**Phase 4** (Weeks 8-10): Advanced Features
- BM25 hybrid search for RAG
- Text selection queries (select text → ask about it)
- Code execution environment (run ROS commands safely)
- Performance optimization & tuning

**Phase 5** (Weeks 2-10): Continuous Testing
- Unit tests (API endpoints, services)
- Integration tests (database, Qdrant, OpenAI)
- E2E tests (user flows, chatbot interactions)
- Accessibility testing (WCAG 2.1 AA)
- Performance testing & benchmarking
- Security testing

**Phase 6** (Week 11): Deployment & Polish
- Deploy frontend to GitHub Pages
- Deploy backend to Railway/Vercel
- Final bug fixes and performance tuning
- Launch & communication

## Success Metrics

### MVP (Core Features)
- ✅ Docusaurus site with custom theme deployed
- ✅ 12 chapters published (all modules complete)
- ✅ RAG chatbot functional (30+ test queries)
- ✅ User authentication working (signup, login, logout)
- ✅ Responsive design (tested on mobile, tablet, desktop)
- ✅ <2s page load time, <5s chatbot response time

### Bonus Goals
- ✅ Personalization system functional (3+ difficulty levels)
- ✅ Urdu translation complete (all content + UI)
- ✅ Code execution environment (safe ROS command execution)
- ✅ Advanced RAG features (BM25 hybrid, text selection)
- ✅ Comprehensive test coverage (>80% code coverage)
- ✅ Security audit passed (no OWASP Top 10 vulnerabilities)
- ✅ Accessibility audit passed (WCAG 2.1 AA)
- ✅ Full documentation (API docs, architecture, deployment guide)
- ✅ ADRs created for all major decisions
- ✅ PHRs recorded for all phases

## Key Decisions

All major architecture decisions are documented as ADRs (Architecture Decision Records):

1. **ADR 001**: Custom Docusaurus theme (React + Tailwind, no defaults)
2. **ADR 002**: RAG chatbot architecture (Qdrant + GPT-4 + OpenAI embeddings)
3. **ADR 003**: Database separation (Neon Postgres + Qdrant)
4. **ADR 004**: Better-Auth for authentication (modern, open-source)

See [history/adr/](history/adr/) for full details.

## Subagents & Skills

**Subagents** (8 specialized roles):
- @SpecArchitect - Specification & architecture
- @RoboticsExpert - Domain expertise (ROS 2, Gazebo, Isaac, VLA)
- @Educator - Learning design & pedagogy
- @FrontendEngineer - UI/UX, Docusaurus, React
- @BackendEngineer - FastAPI, databases, RAG chatbot
- @AuthPersonalizer - Authentication & personalization
- @Translator - Urdu technical translation
- @Reviewer - QA & testing

**Skills** (7 reusable AI capabilities):
- ChapterWriter - Generate complete MDX chapters
- UrduTranslator - Translate to Urdu
- ContentPersonalizer - Adapt per user profile
- QuizGenerator - Create MCQ quizzes
- DiagramDescriber - Generate Mermaid diagrams
- CodeExampleGenerator - Generate tested code
- BonusValidator - Validate bonus criteria

See [.claude/README.md](.claude/README.md) for more details.

## Development Workflow

This project follows **Spec-Driven Development (SDD)** with the Spec-Kit Plus methodology:

1. **Specify** - Create SPEC.md with requirements
2. **Clarify** - Ask targeted questions
3. **Plan** - Create PLAN.md with phases & timeline
4. **Tasks** - Break into TASKS.md (atomic units)
5. **Implement** - Execute tasks with continuous testing
6. **Document** - Create PHRs & ADRs

All artifacts are version-controlled in Git and reviewed at phase gates.

## Environment Variables

Create `.env.local` from `.env.example`:

```bash
# Database
DATABASE_URL=postgresql://user:password@<neon-host>/database

# Vector DB
QDRANT_URL=https://<qdrant-cloud-url>
QDRANT_API_KEY=<your-api-key>

# AI/LLM
OPENAI_API_KEY=<your-openai-key>
OPENAI_MODEL=gpt-4

# Email
SENDGRID_API_KEY=<your-sendgrid-key>
SENDGRID_FROM_EMAIL=no-reply@textbook.example.com

# Auth
JWT_SECRET=<generate-random-secret>
BETTER_AUTH_SECRET=<generate-random-secret>

# Server
ENVIRONMENT=development
SERVER_PORT=8000
FRONTEND_URL=http://localhost:3000
```

## Contributing

This is a hackathon project with clear subagent roles. See [.claude/README.md](.claude/README.md) for how to delegate work.

## License

MIT License - See LICENSE file (TBD)

## Support

- 📧 Email: team@panaversity.ai
- 🐦 Twitter: @panaversity
- 💬 Discord: [Join our server](https://discord.gg/panaversity) (TBD)
- 📚 Documentation: https://physical-ai-humanoid-robotics-book.pages.dev/docs/

## Authors

**Project Lead**: Lead AI Architect (Panaversity)

**Contributors**:
- @SpecArchitect - Specification & planning
- @RoboticsExpert - Domain expertise
- @Educator - Learning design
- @FrontendEngineer - UI development
- @BackendEngineer - Backend & RAG
- @AuthPersonalizer - Authentication
- @Translator - Urdu localization
- @Reviewer - QA & testing

---

**Last Updated**: 2025-12-24 | **Version**: 0.1.0 (Phase 0) | **Status**: Docusaurus initialization in progress
