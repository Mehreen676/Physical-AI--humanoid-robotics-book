---
title: Module 1 — The Robotic Nervous System (ROS 2)
sidebar_label: Module 1 Overview
---

# Module 1 — The Robotic Nervous System (ROS 2)

## 🎯 Focus

ROS 2 is the middleware that acts as the nervous system of a robot.

It allows different robot components (sensors, controllers, AI models) to communicate with each other in real time.

---

## 🧠 Why ROS 2 Matters

Without ROS 2:

- Sensors cannot talk to controllers
- AI models cannot send commands
- Simulation cannot connect to hardware

With ROS 2:

- Everything communicates using nodes and topics
- Real-time robotics becomes possible
- Simulation-to-real workflows are easier

---

## 🔹 Core Concepts

### 1️⃣ Nodes
A node is a small executable program.
Each robot component runs as a node.

Example:
- Camera node
- Motor controller node
- AI planning node

---

### 2️⃣ Topics
Nodes communicate through topics.

Example:
Camera node → publishes images  
AI node → subscribes to images  

---

### 3️⃣ Services
Used for request/response communication.

Example:
“Reset robot position”

---

### 4️⃣ Actions
Used for long-running tasks.

Example:
“Walk to location (x,y)”

---

## 🔧 Python Integration (rclpy)

ROS 2 supports Python using `rclpy`.

AI agents written in Python can directly control robots using ROS topics and actions.

---

## 🤖 URDF for Humanoids

URDF (Unified Robot Description Format) describes:

- Robot links (body parts)
- Joints
- Sensors
- Physical properties

This allows simulation engines like Gazebo to understand the robot structure.

---

## 📚 Learning Outcome

After this module you will:

- Understand ROS 2 architecture
- Know how nodes communicate
- Understand topics vs services vs actions
- Know how AI integrates with robots

---

➡ Next: Move to **Core Concepts Deep Dive**
