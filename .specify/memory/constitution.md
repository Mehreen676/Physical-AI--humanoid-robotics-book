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

## Phase 1 Module-Specific Principles

### Module 1: The Robotic Nervous System (ROS 2)

#### ROS 2 Foundation & Coverage
Each ROS 2 chapter MUST comprehensively cover:
- **Nodes**: Process isolation, communication patterns, lifecycle management (composition vs. standalone)
- **Topics & Services**: Pub-sub messaging, request-reply semantics, latency implications, best practices
- **Middleware & Executors**: DDS (Data Distribution Service), real-time guarantees, thread models
- **Tools & Debugging**: `ros2 topic`, `ros2 service`, `rqt`, logging infrastructure, best practices for debugging distributed systems
- **Real-World Context**: How concepts apply to humanoid robot control, sensor fusion, and multi-robot coordination

**Rationale**: ROS 2 is the foundation of modern robotics. Learners MUST understand nodes, topics, and services deeply to design robust systems. Skipping these fundamentals leads to runtime failures and poor robot behavior.

#### Simulation-First Validation
All ROS 2 concepts MUST be validated in Gazebo or equivalent simulation BEFORE real-world application sections. Code examples provided MUST be runnable in the simulated environment with clear instructions for setup.

**Rationale**: Simulation provides safe, repeatable learning without hardware costs. Learners gain confidence before deploying to real robots.

#### Integration with Gazebo/Unity (Module 2 Preview)
Chapter conclusions MUST reference how each ROS 2 concept connects to simulation (Gazebo plugin architecture, sensor simulation, physics). Links to Module 2 (Gazebo/Unity) should be embedded where relevant.

**Rationale**: Learning is reinforced when learners see how components interconnect across modules.

#### Personalization & Accessibility
Each chapter MUST include:
- **Difficulty Toggle**: "Beginner" path (setup, basic examples) vs. "Advanced" (internals, optimization, debugging)
- **Code Examples**: Provided in both Python (faster to prototype) and C++ (production-grade). Selection per user preference stored in Better-Auth profile.
- **Urdu Translation**: All learning outcomes, key concepts, and code comments available in Urdu. Technical terminology (node, topic, service, DDS) preserved as-is with English pronunciation guides.
- **Interactive Checkpoints**: Quiz after each major section (5 MCQs, auto-graded). Chatbot available for contextual help.

**Rationale**: Diverse learners benefit from multiple difficulty levels, language options, and paced learning. Personalization increases engagement and retention.

#### Reusable Assets Deployment
Module 1 chapters are generated using:
- **@ChapterWriter skill**: Generates MDX with structure (learning outcomes → concepts → examples → quiz → further reading)
- **@CodeExampleGenerator skill**: Produces tested Python/C++ code with setup instructions
- **@UrduTranslator skill**: Translates content, preserving technical terminology
- **@QuizGenerator skill**: Creates 5-MCQ quizzes with misconception-aligned distractors
- **@DiagramDescriber skill**: Generates Mermaid diagrams for node graphs, message flows, and architecture
- **@ContentPersonalizer skill**: Adapts code examples and explanations per user background

**Rationale**: Reusable skills ensure consistency, scalability, and reduce manual writing burden. Subagents (@RoboticsExpert, @Educator) review and approve all outputs per quality gates.

#### RAG Chatbot Integration
Chapter content is automatically indexed into Qdrant upon publication. Learners can:
- Ask freeform questions (e.g., "How do I create a custom message type?") → chatbot retrieves relevant sections + provides answer with source citations
- Select text and query directly (e.g., highlight "DDS middleware" → ask "explain this in detail")

**Rationale**: RAG chatbot extends learning beyond static text. Contextual answers reduce learner frustration and reinforce key concepts.

#### Chapter Structure Template
All Module 1 chapters follow this MDX structure:

```
# Chapter Title

## Learning Outcomes
- Outcome 1
- Outcome 2
- ...

## Introduction
[Engaging context, real-world relevance]

## Core Concepts
### Concept 1
[Detailed explanation with examples]
### Concept 2
[...]

## Hands-On Exercise
[Step-by-step tutorial with Gazebo simulation]

## Code Examples
### Python Example
[Runnable code with setup instructions]
### C++ Example
[Production-grade equivalent]

## Quiz
[5 auto-graded MCQs]

## Further Reading
[Links to ROS 2 docs, papers, related chapters]

## Difficulty/Language Toggles
[UI buttons for content adaptation]
```

**Rationale**: Consistent structure aids navigation, simplifies maintenance, and enables content reuse across modules.

---

## Governance

Constitution supersedes all other documents. Amendments require documented justification, team agreement, and migration plan. All PRs must verify compliance with principles. Use `.specify/` templates and this constitution as reference during development.

**Amendment Procedure**:
1. Proposed change documented in issue/PR with rationale
2. Review by @SpecArchitect + @RoboticsExpert + @Educator (for module-specific changes)
3. Approval signals minor/major version bump
4. Update constitution, propagate to dependent docs (SPEC, PLAN, TASKS), commit to main

**Versioning**:
- MAJOR: Backward-incompatible principle removals or fundamental redefinitions
- MINOR: New principles, expanded sections, significant clarifications
- PATCH: Wording, clarifications, typo fixes, non-semantic refinements

**Version**: 1.1.0 | **Ratified**: 2025-12-24 | **Last Amended**: 2025-12-24

