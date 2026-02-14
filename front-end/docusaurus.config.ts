import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const isProd = process.env.NODE_ENV === "production";

const config: Config = {
  title: "Physical AI & Humanoid Robotics Textbook",
  tagline: "Interactive textbook + Agentic RAG Chatbot",
  favicon: "img/favicon.ico",

  future: { v4: true },

  url: "https://mehreen676.github.io",
  baseUrl: isProd ? "/Physical-AI--humanoid-robotics-book/" : "/",

  organizationName: "mehreen676",
  projectName: "Physical-AI--humanoid-robotics-book",

  onBrokenLinks: "throw",

  markdown: {
    hooks: { onBrokenMarkdownLinks: "warn" },
  },

  i18n: {
    defaultLocale: "en",
    locales: ["en", "ur"],
    localeConfigs: {
      en: { label: "English" },
      ur: { label: "اردو" },
    },
  },

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          routeBasePath: "docs",
          editUrl:
            "https://github.com/mehreen676/Physical-AI--humanoid-robotics-book/tree/main/front-end/",
        },
        blog: false,
        theme: { customCss: "./src/css/custom.css" },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: "img/docusaurus-social-card.jpg",

    colorMode: {
      defaultMode: "dark",
      respectPrefersColorScheme: false,
      disableSwitch: false,
    },

    navbar: {
      title: "Physical AI & Humanoid Robotics Textbook",
      logo: { alt: "Robot Logo", src: "img/robot-logo.svg" },
      items: [
        { to: "/", label: "Home", position: "left" },

        // FIX: Textbook button -> book landing
        { to: "/docs/intro", label: "Textbook", position: "left" },

        {
          href: "https://github.com/mehreen676/Physical-AI--humanoid-robotics-book",
          label: "GitHub",
          position: "right",
        },

        { type: "localeDropdown", position: "right" },
      ],
    },

    footer: {
      style: "dark",
      links: [
        {
          title: "Docs",
          items: [{ label: "Introduction", to: "/docs/intro" }],
        },
        {
          title: "Project",
          items: [
            {
              label: "GitHub Repo",
              href: "https://github.com/mehreen676/Physical-AI--humanoid-robotics-book",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Mehreen676. Built with Docusaurus.`,
    },

    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
