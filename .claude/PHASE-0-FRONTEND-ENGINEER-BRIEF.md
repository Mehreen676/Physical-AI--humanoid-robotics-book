# PHASE 0 TASK BRIEF - @FrontendEngineer

**Project**: Physical AI & Humanoid Robotics Interactive Textbook
**Phase**: 0 (Foundation & Setup)
**Duration**: 2-3 days (parallel with backend)
**Owner**: @FrontendEngineer
**Status**: READY FOR EXECUTION

---

## Overview

You're building the **custom Docusaurus theme foundation** from scratch—no default theme. This enables full control over design, responsive behavior, and integration with interactive features (difficulty toggle, language switch, RAG chatbot widget).

Your work **doesn't block** content writing, so it can happen in parallel with @BackendEngineer's database setup.

---

## BLOCK 1: Docusaurus Custom Theme Foundation (Days 1-2)

### Task 0.3.1: Disable Docusaurus Defaults & Set Up Custom Theme

**Objective**: Remove all default Docusaurus styling and prepare custom theme structure.

**Steps**:

1. **Verify Docusaurus Installation**
   ```bash
   cd docusaurus-site
   npm install
   npm run build
   # Should build successfully (even if styling looks default)
   ```

2. **Disable Defaults in `docusaurus.config.js`**
   ```javascript
   // docusaurus.config.js

   // Find the section with themes and presets
   module.exports = {
     title: 'Physical AI & Humanoid Robotics',
     tagline: 'Interactive AI-Native Textbook',
     url: 'https://github.com',
     baseUrl: '/physical-ai-humanoid-robotics-book/',

     // KEY: Disable default theme
     themes: [],  // EMPTY - no default theme

     presets: [
       [
         'classic',
         {
           docs: false,  // Disable default docs
           blog: false,  // Disable default blog
           pages: false,  // Disable default pages
           theme: {
             customCss: require.resolve('./src/css/tailwind.css'),
           },
         },
       ],
     ],

     // Theming config
     themeConfig: {
       // This is for Docusaurus UI (search, etc), not our custom theme
       colorMode: {
         defaultMode: 'dark',
         respectPrefersColorScheme: true,
       },
     },
   };
   ```

3. **Create Custom Theme Directory Structure**
   ```bash
   mkdir -p src/theme/Layout
   mkdir -p src/components
   mkdir -p src/css
   ```

4. **Create `src/theme/Layout/index.tsx`** (Main Layout Component)
   ```typescript
   // src/theme/Layout/index.tsx
   import React from 'react';
   import Navbar from '@site/src/components/Navbar';
   import Sidebar from '@site/src/components/Sidebar';
   import Footer from '@site/src/components/Footer';

   export default function Layout({ children }) {
     return (
       <div className="flex flex-col min-h-screen bg-white dark:bg-neutral-900">
         <Navbar />
         <div className="flex flex-1">
           <Sidebar />
           <main className="flex-1 overflow-auto">
             {children}
           </main>
         </div>
         <Footer />
       </div>
     );
   }
   ```

5. **Verify No Default Styles**
   ```bash
   npm run build
   npm run start
   # Visit http://localhost:3000
   # Should look blank/unstyled (no Docusaurus default CSS)
   # Check DevTools: no Docusaurus CSS classes
   ```

**Acceptance Criteria**:
- [ ] `docusaurus.config.js` has `themes: []`
- [ ] Custom Layout component created at `src/theme/Layout/index.tsx`
- [ ] `npm run build` succeeds with no errors
- [ ] No Docusaurus default styles visible (inspect CSS)
- [ ] Page loads (even if unstyled)

**Estimated Time**: 1 hour

---

### Task 0.3.2: Set Up Tailwind CSS & Design System

**Objective**: Configure Tailwind CSS with custom colors, fonts, and dark mode.

**Steps**:

1. **Install Tailwind CSS**
   ```bash
   cd docusaurus-site
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

2. **Configure `tailwind.config.js`**
   ```javascript
   // tailwind.config.js
   module.exports = {
     content: [
       "./src/**/*.{js,jsx,ts,tsx}",
     ],
     darkMode: 'class',  // Dark mode enabled
     theme: {
       extend: {
         colors: {
           primary: {
             50: '#f0f7ff',
             500: '#4A90E2',  // Main blue
             900: '#1e3a8a',
           },
           accent: {
             500: '#7ED321',  // Green
           },
           neutral: {
             50: '#f9fafb',
             100: '#f3f4f6',
             800: '#1f2937',
             900: '#0F1419',  // Dark background
           },
         },
         fontFamily: {
           sans: ['Inter', 'system-ui', 'sans-serif'],
           mono: ['Fira Code', 'monospace'],
         },
         fontSize: {
           xs: '0.75rem',
           sm: '0.875rem',
           base: '1rem',
           lg: '1.125rem',
           xl: '1.25rem',
           '2xl': '1.5rem',
           '3xl': '1.875rem',
           '4xl': '2.25rem',
         },
         spacing: {
           0: '0',
           px: '1px',
           0.5: '0.125rem',
           1: '0.25rem',
           2: '0.5rem',
           3: '0.75rem',
           4: '1rem',
           6: '1.5rem',
           8: '2rem',
           12: '3rem',
           16: '4rem',
         },
       },
     },
     plugins: [],
   };
   ```

3. **Create `src/css/tailwind.css`**
   ```css
   /* src/css/tailwind.css */
   @tailwind base;
   @tailwind components;
   @tailwind utilities;

   /* Custom base styles */
   @layer base {
     body {
       @apply bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white;
       transition: background-color 0.3s ease;
     }

     h1 {
       @apply text-4xl font-bold mb-4;
     }
     h2 {
       @apply text-3xl font-bold mb-3;
     }
     h3 {
       @apply text-2xl font-bold mb-2;
     }

     a {
       @apply text-primary-500 hover:text-primary-700 dark:hover:text-primary-300 transition;
     }
   }

   /* Utility classes */
   @layer components {
     .btn-primary {
       @apply px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-700 transition;
     }
     .btn-secondary {
       @apply px-4 py-2 border border-primary-500 text-primary-500 rounded-lg hover:bg-primary-50 transition;
     }
   }
   ```

4. **Update `docusaurus.config.js`** to import Tailwind:
   ```javascript
   theme: {
     customCss: require.resolve('./src/css/tailwind.css'),
   },
   ```

5. **Test Tailwind**
   ```bash
   npm run build
   npm run start
   # Check DevTools: Tailwind utility classes should be present
   # Dark mode should work (add `dark:` classes)
   ```

**Acceptance Criteria**:
- [ ] `tailwind.config.js` configured with custom colors, fonts, dark mode
- [ ] `src/css/tailwind.css` created with Tailwind directives
- [ ] Dark mode toggle works (add `dark` class to HTML element)
- [ ] Custom color palette available (primary blue, accent green, neutrals)
- [ ] Typography configured (Inter font for body, Fira Code for code)
- [ ] Tailwind CSS compiles without errors

**Estimated Time**: 1 hour

---

### Task 0.3.3: Build Navbar Component

**Objective**: Create responsive navbar with logo, dropdowns, search, user menu, theme toggle.

**Steps**:

1. **Create `src/components/Navbar/Navbar.tsx`**
   ```typescript
   // src/components/Navbar/Navbar.tsx
   import React, { useState } from 'react';

   export default function Navbar() {
     const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
     const [moduleDropdown, setModuleDropdown] = useState(false);
     const [isDark, setIsDark] = useState(true);

     const toggleTheme = () => {
       setIsDark(!isDark);
       // Update HTML class
       if (isDark) {
         document.documentElement.classList.remove('dark');
       } else {
         document.documentElement.classList.add('dark');
       }
     };

     return (
       <nav className="bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 sticky top-0 z-50">
         <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
           {/* Logo */}
           <div className="flex items-center gap-2">
             <div className="text-2xl font-bold text-primary-500">📖</div>
             <div>
               <h1 className="text-lg font-bold">Physical AI</h1>
               <p className="text-xs text-neutral-600 dark:text-neutral-400">Humanoid Robotics</p>
             </div>
           </div>

           {/* Desktop Menu */}
           <div className="hidden md:flex items-center gap-6">
             {/* Module Dropdown */}
             <div className="relative">
               <button
                 onClick={() => setModuleDropdown(!moduleDropdown)}
                 className="text-neutral-700 dark:text-neutral-300 hover:text-primary-500 transition"
               >
                 Modules ▼
               </button>
               {moduleDropdown && (
                 <div className="absolute top-full left-0 mt-2 bg-white dark:bg-neutral-800 rounded-lg shadow-lg p-2 min-w-max">
                   <a href="#" className="block px-4 py-2 hover:bg-primary-50 dark:hover:bg-neutral-700 rounded">Module 1: ROS 2</a>
                   <a href="#" className="block px-4 py-2 hover:bg-primary-50 dark:hover:bg-neutral-700 rounded">Module 2: Gazebo</a>
                   <a href="#" className="block px-4 py-2 hover:bg-primary-50 dark:hover:bg-neutral-700 rounded">Module 3: Isaac Sim</a>
                   <a href="#" className="block px-4 py-2 hover:bg-primary-50 dark:hover:bg-neutral-700 rounded">Module 4: VLA</a>
                 </div>
               )}
             </div>

             {/* Search */}
             <input
               type="text"
               placeholder="Search chapters..."
               className="px-3 py-2 rounded-lg bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white placeholder-neutral-500 dark:placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500"
             />

             {/* User Menu */}
             <a href="/login" className="text-neutral-700 dark:text-neutral-300 hover:text-primary-500">
               Login
             </a>

             {/* Theme Toggle */}
             <button
               onClick={toggleTheme}
               className="p-2 rounded-lg hover:bg-neutral-100 dark:hover:bg-neutral-800 transition"
               title="Toggle theme"
             >
               {isDark ? '☀️' : '🌙'}
             </button>
           </div>

           {/* Mobile Menu Button */}
           <button
             onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
             className="md:hidden p-2"
           >
             ☰
           </button>
         </div>

         {/* Mobile Menu */}
         {mobileMenuOpen && (
           <div className="md:hidden bg-white dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-800 p-4">
             <a href="#" className="block py-2 text-neutral-700 dark:text-neutral-300">Module 1: ROS 2</a>
             <a href="#" className="block py-2 text-neutral-700 dark:text-neutral-300">Module 2: Gazebo</a>
             <a href="#" className="block py-2 text-neutral-700 dark:text-neutral-300">Module 3: Isaac Sim</a>
             <a href="#" className="block py-2 text-neutral-700 dark:text-neutral-300">Module 4: VLA</a>
             <a href="/login" className="block py-2 text-primary-500 font-semibold">Login</a>
           </div>
         )}
       </nav>
     );
   }
   ```

2. **Update `src/theme/Layout/index.tsx`** to include Navbar:
   ```typescript
   import Navbar from '@site/src/components/Navbar';

   export default function Layout({ children }) {
     return (
       <div className="flex flex-col min-h-screen bg-white dark:bg-neutral-900">
         <Navbar />
         {/* ... rest of layout ... */}
       </div>
     );
   }
   ```

3. **Test**
   ```bash
   npm run start
   # Check navbar renders, dropdown works, theme toggle works
   ```

**Acceptance Criteria**:
- [ ] Navbar renders without errors
- [ ] Logo and branding visible
- [ ] Module dropdown shows 4 modules
- [ ] Search input visible (functional later)
- [ ] Login link present
- [ ] Theme toggle switches dark mode
- [ ] Responsive on mobile (hamburger menu)
- [ ] Dark mode styling applied

**Estimated Time**: 1.5 hours

---

### Task 0.3.4: Build Sidebar Component

**Objective**: Create hierarchical, collapsible sidebar for chapter navigation.

**Steps**:

1. **Create `src/components/Sidebar/Sidebar.tsx`**
   ```typescript
   // src/components/Sidebar/Sidebar.tsx
   import React, { useState } from 'react';

   export default function Sidebar() {
     const [expandedModules, setExpandedModules] = useState([1, 2, 3, 4]);

     const modules = [
       {
         id: 1,
         title: 'ROS 2 Fundamentals',
         chapters: [
           { id: '1-1', title: 'Introduction to ROS 2' },
           { id: '1-2', title: 'Installation & Setup' },
           { id: '1-3', title: 'Nodes, Topics, Services' },
           { id: '1-4', title: 'ROS 2 CLI Tools' },
           { id: '1-5', title: 'Packages & Workspaces' },
         ],
       },
       {
         id: 2,
         title: 'Simulation Environments',
         chapters: [
           { id: '2-1', title: 'Gazebo Fundamentals' },
           { id: '2-2', title: 'URDF & Robot Modeling' },
           { id: '2-3', title: 'Gazebo Plugins & Sensors' },
           { id: '2-4', title: 'Unity Robotics Integration' },
           { id: '2-5', title: 'Advanced Simulation' },
         ],
       },
       // ... modules 3 and 4
     ];

     const toggleModule = (id) => {
       setExpandedModules(prev =>
         prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
       );
     };

     return (
       <aside className="hidden md:flex md:w-64 lg:w-72 bg-neutral-50 dark:bg-neutral-800 border-r border-neutral-200 dark:border-neutral-700 overflow-y-auto flex-col">
         <div className="p-4 border-b border-neutral-200 dark:border-neutral-700">
           <h2 className="text-lg font-bold text-neutral-900 dark:text-white">Course Outline</h2>
         </div>

         <nav className="flex-1 p-4 space-y-2">
           {modules.map(module => (
             <div key={module.id}>
               <button
                 onClick={() => toggleModule(module.id)}
                 className="w-full text-left px-3 py-2 rounded-lg font-semibold text-neutral-900 dark:text-white hover:bg-neutral-200 dark:hover:bg-neutral-700 transition"
               >
                 {expandedModules.includes(module.id) ? '▼' : '▶'} Module {module.id}: {module.title}
               </button>

               {expandedModules.includes(module.id) && (
                 <div className="ml-4 space-y-1 mt-2">
                   {module.chapters.map(chapter => (
                     <a
                       key={chapter.id}
                       href={`/chapters/${chapter.id}`}
                       className="block px-3 py-2 rounded-lg text-neutral-700 dark:text-neutral-300 hover:bg-primary-50 dark:hover:bg-neutral-700 hover:text-primary-500 transition text-sm"
                     >
                       {chapter.title}
                       <span className="ml-2 text-xs text-neutral-500">0%</span>
                     </a>
                   ))}
                 </div>
               )}
             </div>
           ))}
         </nav>
       </aside>
     );
   }
   ```

2. **Update `src/theme/Layout/index.tsx`**:
   ```typescript
   import Sidebar from '@site/src/components/Sidebar';

   export default function Layout({ children }) {
     return (
       <div className="flex flex-col min-h-screen bg-white dark:bg-neutral-900">
         <Navbar />
         <div className="flex flex-1">
           <Sidebar />
           <main className="flex-1 overflow-auto">
             {children}
           </main>
         </div>
         <Footer />
       </div>
     );
   }
   ```

3. **Test**
   ```bash
   npm run start
   # Check sidebar renders, collapsible modules work, chapters show
   ```

**Acceptance Criteria**:
- [ ] Sidebar renders on desktop (hidden on mobile)
- [ ] Modules collapsible/expandable
- [ ] Chapters listed under each module
- [ ] Progress indicators visible (placeholder: 0%)
- [ ] Links functional (navigate to chapters)
- [ ] Styled with Tailwind, dark mode works

**Estimated Time**: 1.5 hours

---

### Task 0.3.5: Build Footer Component

**Objective**: Create footer with links, copyright, social (optional).

**Steps**:

1. **Create `src/components/Footer/Footer.tsx`**
   ```typescript
   // src/components/Footer/Footer.tsx
   import React from 'react';

   export default function Footer() {
     const currentYear = new Date().getFullYear();

     return (
       <footer className="bg-neutral-100 dark:bg-neutral-800 border-t border-neutral-200 dark:border-neutral-700 mt-16">
         <div className="max-w-7xl mx-auto px-4 py-8">
           <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
             {/* About */}
             <div>
               <h3 className="font-semibold text-neutral-900 dark:text-white mb-4">About</h3>
               <p className="text-sm text-neutral-700 dark:text-neutral-400">
                 An interactive textbook for Physical AI & Humanoid Robotics using Docusaurus, RAG chatbot, and personalization.
               </p>
             </div>

             {/* Resources */}
             <div>
               <h3 className="font-semibold text-neutral-900 dark:text-white mb-4">Resources</h3>
               <ul className="space-y-2 text-sm">
                 <li><a href="#" className="text-primary-500 hover:text-primary-700">ROS 2 Documentation</a></li>
                 <li><a href="#" className="text-primary-500 hover:text-primary-700">Gazebo Tutorials</a></li>
                 <li><a href="#" className="text-primary-500 hover:text-primary-700">NVIDIA Isaac Docs</a></li>
                 <li><a href="#" className="text-primary-500 hover:text-primary-700">GitHub Repository</a></li>
               </ul>
             </div>

             {/* Contact */}
             <div>
               <h3 className="font-semibold text-neutral-900 dark:text-white mb-4">Contact</h3>
               <ul className="space-y-2 text-sm">
                 <li><a href="#" className="text-primary-500 hover:text-primary-700">Issues & Feedback</a></li>
                 <li><a href="#" className="text-primary-500 hover:text-primary-700">Contribute</a></li>
                 <li><a href="#" className="text-primary-500 hover:text-primary-700">Discord Community</a></li>
               </ul>
             </div>
           </div>

           <div className="border-t border-neutral-200 dark:border-neutral-700 pt-8 flex flex-col md:flex-row justify-between items-center">
             <p className="text-sm text-neutral-700 dark:text-neutral-400">
               © {currentYear} Panaversity Hackathon I. All rights reserved.
             </p>
             <div className="flex gap-4 mt-4 md:mt-0">
               <a href="#" title="GitHub" className="text-neutral-700 dark:text-neutral-400 hover:text-primary-500">
                 GitHub
               </a>
               <a href="#" title="LinkedIn" className="text-neutral-700 dark:text-neutral-400 hover:text-primary-500">
                 LinkedIn
               </a>
             </div>
           </div>
         </div>
       </footer>
     );
   }
   ```

2. **Update `src/theme/Layout/index.tsx`**:
   ```typescript
   import Footer from '@site/src/components/Footer';

   export default function Layout({ children }) {
     return (
       <div className="flex flex-col min-h-screen bg-white dark:bg-neutral-900">
         <Navbar />
         <div className="flex flex-1">
           <Sidebar />
           <main className="flex-1 overflow-auto">
             {children}
           </main>
         </div>
         <Footer />
       </div>
     );
   }
   ```

3. **Test**
   ```bash
   npm run start
   # Check footer renders, links present, layout looks good
   ```

**Acceptance Criteria**:
- [ ] Footer renders at bottom of page
- [ ] About section present
- [ ] Links to resources and contact
- [ ] Copyright year correct
- [ ] Responsive layout (stacks on mobile)
- [ ] Dark mode styling applied

**Estimated Time**: 45 minutes

---

## FINAL VERIFICATION (Day 2-3)

### Build & Verify

```bash
cd docusaurus-site
npm run build
npm run start

# In browser, check:
✓ Homepage loads
✓ Navbar renders (logo, modules dropdown, search, theme toggle)
✓ Sidebar renders (modules collapsible, chapters listed)
✓ Footer renders (links, copyright)
✓ Dark mode works (toggle in navbar)
✓ Responsive on mobile (hamburger menu, sidebar hides)
✓ No Docusaurus default styles visible
✓ Tailwind CSS classes applied
✓ No console errors
```

---

## DELIVERABLES CHECKLIST

By end of Phase 0, you should have:

- [ ] Custom Docusaurus theme initialized
  - [ ] `themes: []` in `docusaurus.config.js`
  - [ ] No default Docusaurus styles

- [ ] Tailwind CSS configured
  - [ ] `tailwind.config.js` with custom colors, fonts, dark mode
  - [ ] `src/css/tailwind.css` with base styles
  - [ ] Dark mode toggle working

- [ ] React components built
  - [ ] `src/theme/Layout/index.tsx` (main layout)
  - [ ] `src/components/Navbar/Navbar.tsx`
  - [ ] `src/components/Sidebar/Sidebar.tsx`
  - [ ] `src/components/Footer/Footer.tsx`

- [ ] Styling complete
  - [ ] Responsive layout (desktop, tablet, mobile)
  - [ ] Dark mode works throughout
  - [ ] Hover states, transitions smooth
  - [ ] Accessibility basics (focus indicators, semantic HTML)

- [ ] Testing
  - [ ] `npm run build` succeeds
  - [ ] `npm run start` runs on http://localhost:3000
  - [ ] All components render without errors
  - [ ] No console warnings

---

## REPORT BACK

When complete, provide:

1. **Status**: "Phase 0 Frontend COMPLETE ✓"
2. **Docusaurus**:
   - Custom theme running on http://localhost:3000
   - No default styles visible
3. **Components**:
   - ✓ Navbar (responsive, dark mode)
   - ✓ Sidebar (collapsible, hierarchical)
   - ✓ Footer (responsive, links)
   - ✓ Layout (flex-based, full-height)
4. **Tailwind**:
   - Custom colors working
   - Dark mode toggle functional
   - Responsive breakpoints verified
5. **Any blockers**: List any issues encountered

---

**Start Now!** Your work enables Phase 1 content placement.

