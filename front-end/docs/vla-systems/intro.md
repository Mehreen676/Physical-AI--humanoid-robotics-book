---
title: Vision-Language-Action (VLA)
sidebar_label: Introduction
---

# Vision-Language-Action (VLA)

This module represents the convergence of:

- Vision (Perception)
- Language (LLMs)
- Action (Robot Control)

VLA is the foundation of modern Physical AI.

---

# 🧠 What is VLA?

Traditional robotics:

Sensor → Controller → Motor

Modern Physical AI:

Vision → LLM → Planner → ROS 2 Actions → Motors

The robot understands natural language and converts it into physical behavior.

---

# 🎤 Voice to Action

Example:

User says:
> “Clean the room.”

System flow:

1. Whisper → Converts speech to text  
2. LLM → Breaks task into steps  
3. Planner → Generates ROS 2 actions  
4. Robot → Executes physically  

---

# 🔍 Vision Component

Robots use:

- RGB Cameras
- Depth Cameras
- LiDAR
- SLAM

Vision allows:

- Object detection
- Obstacle avoidance
- Scene understanding
- Human tracking

Without vision, robots are blind.

---

# 🗣 Language Component

LLMs enable:

- Task understanding
- Reasoning
- Multi-step planning
- Tool selection
- Safety constraints

Example:

“Bring me the red bottle from the kitchen.”

LLM breaks into:

1. Navigate to kitchen  
2. Detect red bottle  
3. Grasp bottle  
4. Navigate back  
5. Deliver  

---

# ⚙ Action Component

Execution uses:

- ROS 2 Actions
- Nav2 stack
- Motion planning
- Manipulation control

Actions provide:

- Feedback
- Cancellation
- Status updates

---

# 🏗 VLA Architecture

User  
↓  
Speech Model (Whisper)  
↓  
LLM Planner  
↓  
ROS 2 Action Server  
↓  
Robot Hardware  

---

# 🚀 Why VLA Matters

Future humanoids will:

- Work in homes
- Assist elderly
- Perform warehouse tasks
- Collaborate with humans

All require language understanding + perception + control.

---

# 🎯 Learning Outcomes

After this module you can:

- Explain VLA pipeline
- Connect LLM planning to ROS 2
- Understand voice-to-action workflow
- Design autonomous task execution

---

➡ Next: Capstone Project