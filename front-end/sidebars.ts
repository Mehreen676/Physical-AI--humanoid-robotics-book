import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    // ✅ BOOK LANDING PAGE (NOT ROS2)
    { type: 'doc', id: 'intro', label: 'Physical AI & Humanoid Robotics Textbook' },

    {
      type: 'category',
      label: 'ROS 2 Foundations',
      link: { type: 'doc', id: 'ros2-foundations/intro' },
      collapsed: false,
      items: [
        'ros2-foundations/intro',
        'ros2-foundations/core-concepts',
        'ros2-foundations/urdf-basics',
        'ros2-foundations/ros2-hands-on',
      ],
    },

    {
      type: 'category',
      label: 'Simulation & Digital Twins',
      link: { type: 'doc', id: 'simulation/intro' },
      collapsed: false,
      items: [
        'simulation/intro',
        'simulation/gazebo-setup',
        'simulation/sensors',
        'simulation/unity-isaac',
        'simulation/urdf-sdf',
      ],
    },

    {
      type: 'category',
      label: 'Hardware Foundations',
      link: { type: 'doc', id: 'hardware-basics/intro' },
      collapsed: false,
      items: [
        'hardware-basics/intro',
        'hardware-basics/requirements',
      ],
    },

    {
      type: 'category',
      label: 'Vision-Language-Action (VLA)',
      link: { type: 'doc', id: 'vla-systems/intro' },
      collapsed: false,
      items: [
        'vla-systems/intro',
        'vla-systems/capstone',
      ],
    },

    {
      type: 'category',
      label: 'Advanced AI & Motion Control',
      link: { type: 'doc', id: 'advanced-ai-control/intro' },
      collapsed: false,
      items: [
        'advanced-ai-control/intro',
        'advanced-ai-control/sim-to-real',
      ],
    },

    {
      type: 'category',
      label: 'Designing Humanoid Robots',
      link: { type: 'doc', id: 'humanoid-design/intro' },
      collapsed: false,
      items: [
        'humanoid-design/intro',
        'humanoid-design/locomotion',
      ],
    },

    {
      type: 'category',
      label: 'Appendix',
      link: { type: 'doc', id: 'appendix/intro' },
      collapsed: false,
      items: [
        'appendix/intro',
        'appendix/glossary',
      ],
    },

    {
      type: 'category',
      label: 'Glossary',
      link: { type: 'doc', id: 'glossary/intro' },
      collapsed: false,
      items: ['glossary/intro'],
    },
  ],
};

export default sidebars;
