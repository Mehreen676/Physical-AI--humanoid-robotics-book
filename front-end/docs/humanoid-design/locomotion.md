---
title: Locomotion Basics
sidebar_label: Locomotion Basics
---

# 🚶 Locomotion Basics

Walking is one of the hardest problems in robotics.

Humans walk effortlessly.

Humanoid robots do not.

---

# 🧠 Why Walking is Hard

Unlike wheeled robots:

- Humanoids are always falling forward
- They must constantly rebalance
- Each step is controlled instability

Walking = controlled falling.

---

# ⚖ Center of Mass (CoM)

The robot’s balance depends on:

- Mass distribution
- Joint angles
- Body orientation

If the Center of Mass moves outside the support polygon:

→ The robot falls.

---

# 📐 Zero Moment Point (ZMP)

ZMP is the point where:

All dynamic forces balance during walking.

Stable walking requires:

ZMP must remain inside the foot support area.

Modern humanoids compute ZMP in real-time.

---

# 🦵 Gait Planning

Walking involves:

1. Lift leg
2. Shift weight
3. Swing leg forward
4. Place foot
5. Rebalance

This sequence is called a **gait cycle**.

---

# 🤖 Control Methods

Humanoids use:

### 1️⃣ Inverse Kinematics
Calculate joint angles from desired foot position.

### 2️⃣ Model Predictive Control (MPC)
Predict future movement and adjust in advance.

### 3️⃣ Reinforcement Learning
Train walking policies in simulation.

---

# 🧪 Sim-to-Real Training

Walking is usually trained in:

- Isaac Sim
- Gazebo
- MuJoCo

Then transferred to:

- Jetson edge device
- Real humanoid robot

This prevents damage during testing.

---

# 🔁 Feedback Loop

Humanoid walking uses sensors:

- IMU (balance)
- Force sensors (feet pressure)
- Joint encoders
- Vision

Loop:

Sense → Compute → Correct → Repeat (100+ times per second)

---

# 🏁 Real-World Example

User command:

> “Walk to the table”

System flow:

Voice → LLM → Plan  
Planner → Nav2  
Nav2 → Gait controller  
Controller → Motor drivers  

Walking begins.

---

# 🎯 Learning Outcomes

After this lesson you can:

- Explain why humanoid walking is complex
- Define Center of Mass and ZMP
- Describe gait planning
- Understand walking control systems
- Explain sim-to-real walking workflow

---


