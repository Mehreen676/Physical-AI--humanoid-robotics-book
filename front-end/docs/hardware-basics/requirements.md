---
title: Hardware Requirements
sidebar_label: Requirements
---

# Hardware Requirements

This course is computationally heavy.

It combines:

- Physics Simulation
- Computer Vision
- SLAM
- Generative AI (LLMs)
- Reinforcement Learning

You need serious hardware.

---

# 🖥 1) Digital Twin Workstation (Required)

This is the most critical component.

## Minimum Specs

- GPU: NVIDIA RTX 4070 Ti (12GB VRAM)
- CPU: Intel i7 (13th Gen+) / Ryzen 9
- RAM: 32GB minimum (64GB recommended)
- OS: Ubuntu 22.04 LTS

---

## Why RTX GPU?

NVIDIA Isaac Sim requires:

- Ray tracing
- High VRAM
- Parallel compute

Without RTX, Isaac Sim will struggle or crash.

---

# 🧠 2) Edge AI Kit (Physical AI Brain)

To deploy AI physically:

## Recommended

- NVIDIA Jetson Orin Nano (8GB)
- NVIDIA Jetson Orin NX (16GB)

This runs:

- ROS 2
- Perception models
- Navigation stack
- VLA inference

---

# 👀 3) Sensors

### RealSense D435i

- RGB + Depth
- Built-in IMU
- Ideal for SLAM

### LiDAR (Optional but Recommended)

Used for:

- Mapping
- Navigation
- Obstacle avoidance

---

# 🦾 4) Robot Options

## Budget Option
Unitree Go2 (Quadruped)
- Affordable
- Strong ROS 2 support

## Mini Humanoid
Robotis OP3
Unitree G1 (advanced)

## Premium
Full humanoid with open SDK

---

# ☁ Cloud Alternative (If No RTX)

You can use:

- AWS g5 instances
- Azure GPU instances
- NVIDIA Omniverse Cloud

But:

- Higher cost
- Latency issues
- Not ideal for real-time control

---

# ⚠ Latency Warning

Never control real robots directly from cloud.

Correct workflow:

Train in cloud →  
Download model →  
Deploy on Jetson locally

---

# 💰 Approx Student Kit Cost

Jetson Orin Nano: ~$249  
RealSense D435i: ~$349  
Mic Array: ~$69  
SD Card + Misc: ~$30  

Total: ~$700

---

# 🎯 Learning Outcomes

After this lesson you can:

- Select appropriate GPU
- Design lab architecture
- Compare cloud vs on-premise
- Estimate robotics setup cost

---

➡ Next: Vision-Language-Action (VLA)