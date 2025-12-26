# ADR 001: Custom Docusaurus Theme (No Defaults)

**Status**: Accepted
**Date**: 2025-12-24
**Deciders**: Lead Architect, Frontend Engineer
**Consulted**: RoboticsExpert, Educator
**Informed**: All subagents

---

## Context

The project requires a modern, professional interactive textbook for Physical AI & Humanoid Robotics. Docusaurus is the chosen static site generator, but the decision arose: use Docusaurus's built-in theme, or build a custom theme from scratch?

### Options Considered

#### Option A: Use Docusaurus Default Theme
- **Pros**:
  - Fastest setup (days, not weeks)
  - Proven, stable design
  - Community support & plugins
  - Dark mode built-in
  - Mobile responsive
  - Low maintenance
- **Cons**:
  - Limited customization (can feel "generic")
  - May not match hacjkathon bonus criteria (reusable skills, unique design)
  - Default styling hard to override significantly
  - No "reusable UI component library" benefit
  - Doesn't maximize frontend engineering showcase

#### Option B: Custom Theme (React + Tailwind, 100% Custom)
- **Pros**:
  - Full control over design (modern, unique aesthetic)
  - Reusable component library (bonus: reusable intelligence)
  - Maximizes UI/UX engineering showcase
  - Can integrate interactive elements seamlessly
  - Aligns with hackathon bonus criteria (custom design, skills)
  - Tailwind CSS for rapid iteration
  - Enables custom features (difficulty toggle, language switch, bookmarking UI)
  - Better performance (optimized CSS/JS)
- **Cons**:
  - Longer development time (3-4 weeks vs 1 week)
  - Higher complexity (more code to maintain)
  - Requires frontend expertise
  - Potential accessibility regressions (must verify WCAG 2.1 AA)
  - No built-in integrations (must code navbar, sidebar, footer)
  - More testing required

---

## Decision

**Build a custom Docusaurus theme from scratch using React + Tailwind CSS.**

### Rationale

1. **Hackathon Bonus Alignment**: The project explicitly aims to maximize bonus points via "reusable intelligence" and unique design. A custom theme demonstrates engineering excellence and custom UI component development (reusable across all 12 chapters).

2. **Feature Requirements**: The textbook requires per-chapter buttons (difficulty toggle, Urdu language toggle, bookmarking) that are easier to implement with custom components than fighting Docusaurus default styling.

3. **Modern Aesthetics**: Educational content deserves a polished, modern design. Custom theme allows brand consistency, smooth animations (Framer Motion), and responsive design optimized for learning.

4. **Reusable Component Library**: Building custom React components (20+ buttons, cards, forms, modals, etc.) creates a reusable library that can be leveraged in future projects, aligning with bonus criteria.

5. **Performance**: Custom, optimized CSS and code splitting yield better Lighthouse scores (target 80+) than fighting Docusaurus defaults.

6. **Integration with RAG Chatbot**: Embedding the RAG chatbot widget seamlessly in the page layout is easier with custom React components.

---

## Consequences

### Positive
- ✅ Unique, modern design (differentiates from generic Docusaurus sites)
- ✅ Reusable component library (20+ components = reusable intelligence bonus)
- ✅ Full control over UX (difficulty toggle, bookmarks, progress indicators integrate naturally)
- ✅ Better Lighthouse scores (optimized CSS, code splitting)
- ✅ Accessible design (WCAG 2.1 AA compliance planned)
- ✅ Scalable (components reused across 12 chapters)

### Negative
- ⚠️ **Longer timeline** (Phase 0-1: custom theme foundation, Phase 1: complete styling = 3-4 weeks)
- ⚠️ **Higher complexity** (more code, more testing)
- ⚠️ **Maintenance burden** (custom theme owned by team, not Docusaurus community)
- ⚠️ **Accessibility risk** (must verify WCAG 2.1 AA, can't rely on Docusaurus defaults)
- ⚠️ **Developer skill requirement** (needs strong React/CSS expertise)

### Mitigation Strategies
1. **Timeline**: Parallelize with Phase 1 (while content is being written), don't block content on theme completion
2. **Testing**: Continuous accessibility testing throughout Phase 5 (not left to final week)
3. **Component library**: Use Storybook or documentation to keep components maintainable
4. **Quality gates**: Lighthouse score >= 80 is non-negotiable (Phase 4.4 and Phase 5.4)

---

## Implementation Details

### Architecture
- **Disable defaults**: `docusaurus.config.js` sets `themes: []`
- **Custom Layout**: `src/theme/Layout/index.tsx` (React component)
- **Design system**: Tailwind CSS with custom colors, typography, spacing
- **Component library**: `src/components/` organized by type
- **MDX components**: Custom `<CodeBlock>`, `<Quiz>`, `<Diagram>`, etc.

### Key Components
- Navbar (logo, dropdown, search, user menu, theme toggle)
- Sidebar (hierarchical chapters, collapsible, progress %)
- Footer (links, copyright, social)
- Chapter layout (MDX page template)
- 20+ base components (buttons, cards, forms, modals, etc.)

### Tech Stack
- **Docusaurus 3.x** (static site generator)
- **React 18+** (component framework)
- **Tailwind CSS 3.x** (styling)
- **TypeScript** (type safety)
- **Framer Motion** (animations, optional)

---

## Related Decisions

- **ADR 002**: RAG Chatbot Architecture (influences custom component needs)
- **ADR 003**: Neon + Qdrant (no direct relation, parallel decision)
- **Constitution Principle V**: No default themes; custom design mandatory

---

## Approval

- ✅ **Lead Architect**: Approved (aligns with bonus criteria, realistic timeline with parallelization)
- ✅ **Frontend Engineer**: Approved (realistic effort estimate, clear deliverables)
- ✅ **Project Owner**: Approved (differentiation, bonus multiplier)

---

## References

- Docusaurus Theme Customization: https://docusaurus.io/docs/advanced/swizzling
- Tailwind CSS: https://tailwindcss.com/
- Constitution Principle V (No Default Themes)

