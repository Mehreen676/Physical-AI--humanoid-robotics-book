# Claude Code Configuration for Physical AI & Humanoid Robotics

This directory contains all configuration, skills, and agents for the Panaversity Hackathon I project.

## Directory Structure

```
.claude/
├── agents/              # 8 specialized subagents
│   ├── SpecArchitect.claude_agent
│   ├── RoboticsExpert.claude_agent
│   ├── Educator.claude_agent
│   ├── FrontendEngineer.claude_agent
│   ├── BackendEngineer.claude_agent
│   ├── AuthPersonalizer.claude_agent
│   ├── Translator.claude_agent
│   └── Reviewer.claude_agent
├── skills/              # 7 reusable skills
│   ├── ChapterWriter.claude_skill
│   ├── UrduTranslator.claude_skill
│   ├── ContentPersonalizer.claude_skill
│   ├── QuizGenerator.claude_skill
│   ├── DiagramDescriber.claude_skill
│   ├── CodeExampleGenerator.claude_skill
│   └── BonusValidator.claude_skill
├── commands/            # Custom commands (reserved)
├── PHASE-0-BACKEND-ENGINEER-BRIEF.md    # Phase 0 backend tasks
├── PHASE-0-FRONTEND-ENGINEER-BRIEF.md   # Phase 0 frontend tasks
├── .clauderc.json       # Project configuration
├── settings.local.json  # Local settings
└── README.md            # This file
```

## Phases

All development follows the Spec-Driven Development (SDD) workflow with 6 phases:

1. **Phase 0** (Week 1, Days 1-3): Repository initialization, Docusaurus setup, database configuration, FastAPI skeleton
2. **Phase 1** (Weeks 2-5): MVP development - 12 chapters, RAG chatbot, authentication, custom theme
3. **Phase 2** (Weeks 4-6): Personalization system - user profiling, difficulty levels, background detection
4. **Phase 3** (Weeks 6-8): Urdu localization - translation of all content
5. **Phase 4** (Weeks 8-10): Advanced features - BM25 hybrid search, code execution environment
6. **Phase 5** (Weeks 2-10): Continuous testing - unit, integration, E2E, accessibility, performance
7. **Phase 6** (Week 11): Deployment and polish - final bug fixes, performance optimization

## Key Files

- **Constitution** (.specify/memory/constitution.md): Project principles and governance
- **Specification** (specs/core/spec.md): Full technical requirements (13 sections)
- **Plan** (specs/core/plan.md): Implementation strategy with phases and dependencies
- **Tasks** (specs/core/tasks.md): Atomic work items (120+)
- **ADRs** (history/adr/): Architecture Decision Records for significant decisions

## How to Use

### Running Phase 0 (Backend)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
# Follow PHASE-0-BACKEND-ENGINEER-BRIEF.md for tasks
```

### Running Phase 0 (Frontend)

```bash
cd docusaurus-site
npm install
npm run start
# Follow PHASE-0-FRONTEND-ENGINEER-BRIEF.md for tasks
```

## Environment Variables

Create a `.env.local` file in the project root using `.env.example` as template. Required variables:

- `DATABASE_URL`: Neon Postgres connection string
- `QDRANT_URL` & `QDRANT_API_KEY`: Vector database credentials
- `OPENAI_API_KEY`: OpenAI API key (GPT-4, embeddings)
- `JWT_SECRET`: For JWT token signing

## Subagents

Each subagent has a specialized role:

- **@SpecArchitect**: Specification, architecture, ADR management
- **@RoboticsExpert**: Domain expertise (ROS 2, Gazebo, Isaac, VLA, humanoid robotics)
- **@Educator**: Pedagogy, learning design, chapter structure
- **@FrontendEngineer**: Custom Docusaurus theme, React components, Tailwind CSS
- **@BackendEngineer**: FastAPI, RAG chatbot, database design, API endpoints
- **@AuthPersonalizer**: Authentication system, user profiling, personalization logic
- **@Translator**: Urdu technical translation, terminology management
- **@Reviewer**: QA testing, accessibility, bonus criteria validation

## Skills

Reusable skills for content generation:

- **ChapterWriter**: Generate complete MDX chapters (2000-6000 words)
- **UrduTranslator**: Translate chapters to Urdu (preserve code, terminology)
- **ContentPersonalizer**: Adapt content per user background (difficulty, language, examples)
- **QuizGenerator**: Create 5-MCQ quizzes with distractors
- **DiagramDescriber**: Generate Mermaid/ASCII diagrams
- **CodeExampleGenerator**: Generate tested, runnable code examples
- **BonusValidator**: Validate bonus criteria (skills, personalization, translation)

## Success Criteria

**MVP (Core features)**:
- Docusaurus site running with custom theme (no defaults)
- 12 chapters written and published
- RAG chatbot functional (question answering with sources)
- User authentication (signup, signin, logout, email verification)
- Responsive design (desktop & mobile)

**Bonus goals**:
- User personalization system (difficulty, language, background)
- Urdu translation (all content + UI)
- Code execution environment
- Advanced RAG features (BM25 hybrid search, text selection queries)
- Comprehensive testing (unit, integration, E2E, accessibility, security)
- Detailed documentation and ADRs

## Getting Help

- **Architecture questions**: Consult ADRs (history/adr/)
- **Specification questions**: Check specs/core/spec.md
- **Task assignments**: See specs/core/tasks.md and phase briefs
- **Code standards**: See .specify/memory/constitution.md

## Quick Commands

```bash
# Initialize Phase 0
npm run setup:phase0

# Run tests
npm run test
npm run test:e2e

# Build for deployment
npm run build
cd backend && python -m pytest

# Check code quality
npm run lint
npm run type-check
```

---

**Last Updated**: 2025-12-24
**Version**: 0.1.0 (Phase 0)
**Status**: In Progress (Docusaurus initialization, backend setup)
