import React from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import styles from "./index.module.css";

type ModuleCard = {
  title: string;
  desc: string;
  to: string;
  icon: string;
};

const modules: ModuleCard[] = [
  {
    title: "ROS 2 Foundations",
    desc: "Learn ROS 2 — nodes, topics, services, actions, and real robot workflows.",
    to: "/docs/ros2-foundations/intro",
    icon: "📡",
  },
  {
    title: "Simulation & Digital Twins",
    desc: "Master Gazebo, Unity, and Isaac Sim for safe, high-fidelity virtual environments.",
    to: "/docs/simulation/intro",
    icon: "🧊",
  },
  {
    title: "Hardware Foundations",
    desc: "Sensors, actuators, embedded systems — everything real humanoids need.",
    to: "/docs/hardware-basics/intro",
    icon: "💾",
  },
  {
    title: "VLA — Vision, Language, Action",
    desc: "Perception models, LLM-driven command systems, action planners.",
    to: "/docs/vla-systems/intro",
    icon: "👁️",
  },
  {
    title: "Advanced AI & Motion Control",
    desc: "Reinforcement learning, MPC, trajectory optimization, and intelligent control.",
    to: "/docs/advanced-ai-control/intro",
    icon: "🧠",
  },
  {
    title: "Designing Humanoid Robots",
    desc: "Mechanical design, kinematics, balance, morphology, full-stack thinking.",
    to: "/docs/humanoid-design/intro",
    icon: "🦾",
  },
  {
    title: "Appendix",
    desc: "Glossary, research papers, external resources, and further reading.",
    to: "/docs/appendix/intro",
    icon: "📘",
  },
];

export default function Home() {
  return (
    <Layout title="Home" description="Physical AI & Humanoid Robotics Textbook">
      <main className={styles.pageWrapper}>
        {/* HERO */}
        <section className={styles.hero}>
          <div className={styles.heroContent}>
            <h1>Unlock the Future: Physical AI & Humanoid Robotics Textbook</h1>
            <p className={styles.subtitle}>
              A complete learning system for next-generation intelligent machines.
            </p>

            <div className={styles.heroButtons}>
              {/* FIX: Start Reading should go to book intro */}
              <Link className={styles.primaryBtn} to={useBaseUrl("/docs/intro")}>
                Start Reading
              </Link>

              <a
                className={styles.secondaryBtn}
                href="https://github.com/mehreen676/Physical-AI--humanoid-robotics-book"
                target="_blank"
                rel="noreferrer"
              >
                View on GitHub
              </a>
            </div>
          </div>
        </section>

        {/* MODULES */}
        <section className={styles.modules}>
          <h2>Explore All Modules</h2>

          <div className={styles.grid}>
            {modules.map((m) => (
              <div key={m.title} className={styles.card}>
                <div className={styles.cardIcon}>{m.icon}</div>
                <h3>{m.title}</h3>
                <p>{m.desc}</p>

                <Link to={useBaseUrl(m.to)}>Open Module →</Link>
              </div>
            ))}
          </div>
        </section>

        {/* WHY SECTION */}
        <section className={styles.whySection}>
          <h2 className={styles.whyTitle}>
            Why This Textbook is AI-Native & Future-Focused
          </h2>

          <div className={styles.whyGrid}>
            <div className={styles.whyCard}>
              <h3>AI-Driven Design</h3>
              <p>
                Built fully around modern robotics workflows, from LLM agents to
                VLA systems and intelligent controllers.
              </p>
            </div>

            <div className={styles.whyCard}>
              <h3>Hands-On Learning</h3>
              <p>
                Every module includes practical steps, code examples,
                simulations, and real robot applications.
              </p>
            </div>

            <div className={styles.whyCard}>
              <h3>Industry-Inspired Curriculum</h3>
              <p>
                The content reflects what Tesla Bots, Figure AI, Apptronik, and
                Sanctuary AI use in real humanoid robotics pipelines.
              </p>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className={styles.cta}>
          <h2>Begin Your Robotics Journey</h2>
          <p>
            Learn ROS 2, Simulation, Isaac, VLA, and build embodied intelligence
            step-by-step.
          </p>

          {/* FIX: CTA also goes to book intro */}
          <Link className={styles.primaryBtnLarge} to={useBaseUrl("/docs/intro")}>
            Start Reading →
          </Link>
        </section>
      </main>
    </Layout>
  );
}
