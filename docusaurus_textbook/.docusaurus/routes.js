import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/Physical-AI--humanoid-robotics-book/docs',
    component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs', '48d'),
    routes: [
      {
        path: '/Physical-AI--humanoid-robotics-book/docs',
        component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs', '009'),
        routes: [
          {
            path: '/Physical-AI--humanoid-robotics-book/docs',
            component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs', 'af9'),
            routes: [
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/advanced-ai-control/module-5-advanced-ai',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/advanced-ai-control/module-5-advanced-ai', '03f'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/appendix/glossary',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/appendix/glossary', '2b5'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/appendix/rag-chatbot-integration',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/appendix/rag-chatbot-integration', '32c'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/appendix/references',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/appendix/references', '84c'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/appendix/resources',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/appendix/resources', '1d8'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/hardware-basics/module-3-hardware',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/hardware-basics/module-3-hardware', '11b'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/humanoid-design/module-6-humanoid-design',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/humanoid-design/module-6-humanoid-design', 'b08'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/intro',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/intro', '1e8'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/introduction/intro',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/introduction/intro', 'f9c'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/ros2-foundations/module-1-ros2',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/ros2-foundations/module-1-ros2', '4ff'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/ros2-foundations/ros2-hands-on',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/ros2-foundations/ros2-hands-on', '73d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/simulation/digital-twins',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/simulation/digital-twins', '08b'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/simulation/gazebo-unity',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/simulation/gazebo-unity', '872'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/simulation/module-2-simulation',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/simulation/module-2-simulation', '6ba'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/vla-systems/module-4-vla-foundations',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/vla-systems/module-4-vla-foundations', '944'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-action',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-action', '5a8'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-hands-on-basic',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-hands-on-basic', 'ec3'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-language',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-language', 'df1'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-vision',
                component: ComponentCreator('/Physical-AI--humanoid-robotics-book/docs/vla-systems/vla-vision', 'b8b'),
                exact: true,
                sidebar: "tutorialSidebar"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '/Physical-AI--humanoid-robotics-book/',
    component: ComponentCreator('/Physical-AI--humanoid-robotics-book/', '112'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
