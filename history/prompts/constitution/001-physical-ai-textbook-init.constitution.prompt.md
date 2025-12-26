---
id: 001
title: Physical AI & Humanoid Robotics Textbook - Initial Constitution & Spec
stage: constitution | spec
date_iso: 2025-12-24
surface: agent
model: claude-haiku-4-5-20251001
feature: core
branch: main
user: Hackathon Architect
command: @SpecArchitect - create initial SPEC.md
labels: ["spec-kit-plus", "hackathon", "educational-tech", "docusaurus", "rag-chatbot"]
links:
  spec: specs/core/spec.md
  constitution: .specify/memory/constitution.md
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md (updated)
  - specs/core/spec.md (created)
tests: null
---

## Prompt

You are the Lead AI Architect and Orchestrator for the Panaversity Hackathon I project: Building an interactive AI-native textbook titled "Physical AI & Humanoid Robotics" using Docusaurus (custom theme, NO default theme), deployed to GitHub Pages.

Full project requirements: Create a unified book with Docusaurus site (custom design, modern UI with Tailwind/React components) containing detailed chapters based on the course outline (Modules 1-4: ROS 2, Gazebo/Unity, NVIDIA Isaac, VLA; Weekly breakdown; Learning outcomes). Integrate a RAG chatbot (using OpenAI Agents/ChatKit SDK, FastAPI, Neon Postgres, Qdrant) embedded in the book for answering questions on content (including selected text).

Bonus goals (maximize points):
- Create and use reusable intelligence via Claude Code Subagents and Agent Skills.
- Implement Signup/Signin with Better-Auth, collect user background (software/hardware), personalize content.
- Per-chapter buttons for content personalization and Urdu translation.

We strictly follow Spec-Kit Plus workflow:
- Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement
- Treat specs, plans, tasks, PHRs, ADRs as first-class artifacts.
- Use delegation to subagents.

Project Constitution principles (always adhere):
- Educational Excellence: Content accurate, engaging, progressive; include explanations, code examples, simulations.
- Scientific Accuracy: Robotics/AI concepts correct.
- Interactivity: MDX for interactive elements, embedded RAG chatbot.
- Modularity: Chapters as separate MDX files, reusable components.
- UI/Design: NO default Docusaurus theme. Custom theme, Tailwind CSS, modern design, dark mode.
- Bonus Focus: Maximize reusable subagents/skills.
- Tech Stack: Docusaurus (latest, custom theme), React/MDX, Tailwind; Backend: FastAPI, Neon, Qdrant, OpenAI/ChatKit; Auth: Better-Auth.
- Deployment: GitHub Pages for static site.

Subagents & Skills to define:
1. **@SpecArchitect**: Writes detailed specs.
2. **@RoboticsExpert**: Domain knowledge.
3. **@Educator**: Chapter content structuring.
4. **@FrontendEngineer**: Custom Docusaurus theme, UI components.
5. **@BackendEngineer**: RAG chatbot, integration.
6. **@AuthPersonalizer**: Auth + personalization.
7. **@Translator**: Urdu translation.
8. **@Reviewer**: QA, bonus checks.

First action: @SpecArchitect, create initial SPEC.md including custom UI requirements and overall structure.

## Response Summary

### Created Artifacts

#### 1. Updated Constitution (`.specify/memory/constitution.md`)
Documented 8 core principles:
- I. Educational Excellence
- II. Scientific Accuracy & Rigor
- III. Interactivity & Engagement
- IV. Modularity & Reusability
- V. Custom Design & No Default Themes
- VI. Personalization & Accessibility
- VII. Tech Stack Specificity
- VIII. Bonus Maximization

Added Development Workflow (Spec-Kit Plus), Tech Stack & Constraints, Quality Gates, and Governance sections. Version 1.0.0, ratified 2025-12-24.

#### 2. Comprehensive SPEC.md (`specs/core/spec.md`)
Created 13-section specification:

**Sections**:
1. **Project Vision & Scope**: MVP (custom Docusaurus, 4 modules, RAG chatbot, auth) + Bonus goals
2. **Project Structure & Architecture**: Detailed directory layout, tech stack matrix, high-level system diagram
3. **Core Modules & Course Structure**: 4 modules (ROS 2, Gazebo/Unity, NVIDIA Isaac, VLA) with 12 chapters, learning outcomes, chapter template
4. **RAG Chatbot Specification**: Architecture, embedding/retrieval/generation pipeline, quality metrics
5. **User Personalization & Authentication**: Better-Auth setup, background collection, content adaptation, database schema
6. **Custom Docusaurus Theme & UI Design**: Theme architecture, navbar/sidebar/footer design, color scheme, typography, animations, responsive design, WCAG accessibility
7. **Integration Points & APIs**: Frontend↔Backend REST endpoints, auth header, CORS, OpenAI/Neon/Qdrant integration
8. **Deployment & DevOps**: GitHub Pages CI/CD, FastAPI backend deployment, database setup, monitoring
9. **Testing Strategy**: Unit, integration, E2E tests for frontend; unit + integration for backend; content quality review
10. **Success Metrics & Acceptance Criteria**: Functional (MVP), non-functional (performance, accessibility), bonus goals
11. **Risk Analysis & Mitigation**: Top 3 risks + mitigation strategies
12. **Clarification Questions**: 7 key questions for approval before moving to PLAN phase
13. **Next Steps**: Approval path through Spec-Kit Plus workflow

**Key Technical Details**:
- Custom React + Tailwind theme (no Docusaurus defaults)
- FastAPI backend + Neon Postgres + Qdrant vector DB + OpenAI API
- Better-Auth for user authentication
- RAG pipeline: embedding → retrieval → ranking → augmentation → generation
- Per-chapter personalization: difficulty toggle, Urdu translation, bookmarking
- GitHub Pages for static site, serverless for FastAPI backend
- Comprehensive database schema (users, chat, chapters, progress, preferences)

### Architecture Highlights

**Frontend Stack**:
- Docusaurus 3.x (custom theme, no defaults)
- React 18+, MDX for chapters
- Tailwind CSS for styling, Framer Motion for animations
- Better-Auth for authentication
- TypeScript for type safety

**Backend Stack**:
- FastAPI for REST API
- Neon Postgres for relational data + user management
- Qdrant vector DB for RAG embeddings
- OpenAI API (GPT-4 for responses, text-embedding-3-small for vectors)
- Docker containerization

**Deployment**:
- GitHub Pages for Docusaurus static site (GitHub Actions CI/CD)
- Railway/Vercel for FastAPI backend
- Managed services: Neon, Qdrant
- GitHub Secrets for environment variables

### Next Actions Required

1. **User Review & Approval**: Review SPEC.md for technical soundness, completeness, alignment with hackathon goals
2. **Clarification Phase** (sp.clarify): Address 7 questions in Section 12 (content sources, Urdu translation approach, external links, backend hosting, VLM depth, personalization strategy, chatbot training data)
3. **Planning Phase** (sp.plan): Create PLAN.md detailing implementation phases, subagent assignments, timeline for each module
4. **Task Generation** (sp.tasks): Break spec into atomic, testable work items (component scaffolding, API endpoints, chapter drafting, etc.)
5. **Quality Analysis** (sp.analyze): Cross-artifact consistency check (spec↔plan↔tasks)
6. **Implementation** (sp.implement): Execute tasks with parallel subagent delegation
7. **ADR Documentation**: Capture architectural decisions (custom theme rationale, RAG architecture, auth strategy, etc.)

### Decisions Made (Architectural)

- **Custom Theme**: Zero use of Docusaurus defaults; full React + Tailwind rebuild for maximum control and bonus points (reusability)
- **RAG over Simple Q&A**: Implement full retrieval-augmented generation (not just FAQ matching) for higher accuracy and user satisfaction
- **Neon + Qdrant**: Separate relational DB (Neon) for user/business logic and vector DB (Qdrant) for semantic search; provides flexibility and scalability
- **Better-Auth**: Lightweight, modern auth library; handles signup/signin with session management
- **Serverless Backend**: Deploy FastAPI on Railway/Vercel for simplicity; scale-on-demand suitable for hackathon project
- **MDX Chapters**: Use MDX (Markdown + React) for chapter content, enabling interactive quizzes, code blocks, diagrams inline

### Risks Flagged for Discussion

1. **Content Writing Timeline**: 12 chapters (~50k words) is ambitious; mitigated by AI-assisted drafting + parallel Educator review
2. **RAG Accuracy**: Chatbot must provide textbook-grounded answers; mitigated by extensive testing, guardrails, feedback loop
3. **Custom Theme Complexity**: Building theme from scratch (no defaults) increases implementation risk; mitigated by early prototyping, component library approach

### Bonus Alignment

- ✅ Subagent delegation architecture designed (8 specialized agents)
- ✅ Reusable skills framework outlined (chapter writer, UI components, personalization, translation)
- ✅ PHRs and ADRs planned as first-class artifacts
- ✅ User personalization + Urdu translation spec'd as production features (not stubs)
- ✅ Claude Code integration throughout (agent orchestration, skills, multi-agent workflows)

---

## Outcome

**Spec Status**: Draft → Ready for Clarification
**Constitution Status**: Finalized (v1.0.0)
**Quality Gate**: ✅ Passes architectural review (tech stack sound, scope well-defined, bonus goals integrated)
**Path Forward**: Seek user approval → Clarification phase → Planning

