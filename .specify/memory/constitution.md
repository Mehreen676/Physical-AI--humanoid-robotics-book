# Physical AI & Humanoid Robotics Textbook Constitution

## Core Principles

### I. Educational Excellence
Content must be scientifically accurate, progressively structured, and engaging. Each chapter includes clear learning outcomes, explanatory text, code examples, simulation descriptions/diagrams, and quizzes. Content serves learners from fundamentals to advanced applications.

### II. Scientific Accuracy & Rigor
All robotics, AI, and technical concepts are verified against current research and industry standards. References to foundational papers, ROS 2 documentation, Gazebo/Unity simulation specs, NVIDIA Isaac frameworks, and vision-language model (VLA) architectures are mandatory where applicable.

### III. Interactivity & Engagement
MDX-based interactive elements throughout the textbook. Embedded RAG chatbot (trained on full course content) enables learners to ask questions and receive context-aware answers. Selected text allows direct chatbot queries for targeted learning.

### IV. Modularity & Reusability
Chapters are independent MDX files with standardized structure. React components (custom Tailwind-based) are reusable across chapters. Code examples are copy-pasteable and tested. Agent skills for chapter writing, UI components, and personalization are centralized and versioned.

### V. Custom Design & No Default Themes
Zero use of Docusaurus default theme. Custom theme built entirely with React + Tailwind CSS. Features: responsive modern design, dark mode, custom navbar/sidebar with course navigation, smooth animations, accessible typography, consistent branding.

### VI. Personalization & Accessibility
User authentication (Better-Auth) collects background (software/hardware experience). Content adapts based on user profile. Per-chapter buttons enable:
- Content difficulty/depth toggle (basic ↔ advanced)
- Urdu language translation (technical terminology preserved)
- Bookmark/progress tracking per user

### VII. Tech Stack Specificity
- **Frontend**: Docusaurus 3.x (custom theme), React 18+, MDX, Tailwind CSS, animations (Framer Motion)
- **Backend**: FastAPI, Neon Postgres (vector storage + relational data), Qdrant (vector DB for RAG), OpenAI API (embeddings + agent calls)
- **Auth & Personalization**: Better-Auth, JWT sessions, user preference storage
- **Deployment**: GitHub Pages (static site), GitHub Actions CI/CD
- **Agent Orchestration**: Claude Code subagents for specialized tasks, skills in `.claude/skills/`

### VIII. Bonus Maximization
Reusable Claude Code subagents and skills prioritized throughout. Prompt History Records (PHRs) and Architecture Decision Records (ADRs) document all significant decisions. User personalization and Urdu translation are production-ready, not stub implementations.

## Development Workflow

- **Spec-Kit Plus**: Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement
- **Artifacts as First-Class**: Specs, plans, tasks, PHRs, ADRs treated as deliverables, not throwaway.
- **Delegation**: Use @SpecArchitect, @FrontendEngineer, @BackendEngineer, @Translator, @Reviewer subagents for domain-specific work.
- **Smallest Viable Change**: No scope creep; code only what's specified.
- **AI-Driven Collaboration**: Leverage Claude Code agents for content generation, code scaffolding, and validation.

## Tech Stack & Constraints

- **No Default Docusaurus Theme**: Custom React/Tailwind required; use `docusaurus.config.js` to disable all defaults.
- **Neon + Qdrant**: Single source of truth for user data; vector embeddings versioned with content.
- **RAG Quality**: Chatbot trained on full textbook content + external references (ROS 2 docs, Gazebo tutorials, NVIDIA Isaac docs). Accuracy measured by learner feedback.
- **Deployment**: GitHub Pages only; no external servers for static assets. FastAPI backend on serverless (Vercel/Railway) or self-hosted.
- **Security**: No hardcoded secrets; `.env.local` for development, GitHub Secrets for CI/CD.

## Quality Gates

- **Content Review**: RoboticsExpert + Educator approval before chapters go live.
- **Code Quality**: TypeScript strict mode, ESLint/Prettier, Tailwind class validation.
- **Testing**: Unit tests for components, integration tests for RAG pipeline, manual QA for all interactive features.
- **Accessibility**: WCAG 2.1 AA compliance, semantic HTML, keyboard navigation, alt text for all diagrams.

## Governance

Constitution supersedes all other documents. Amendments require documented justification, team agreement, and migration plan. All PRs must verify compliance with principles. Use `.specify/` templates and this constitution as reference during development.

**Version**: 1.0.0 | **Ratified**: 2025-12-24 | **Last Amended**: 2025-12-24

