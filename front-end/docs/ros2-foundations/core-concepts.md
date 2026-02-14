---
title: ROS 2 Core Concepts
sidebar_label: Core Concepts
---

# ROS 2 Core Concepts

ROS 2 is the middleware layer that connects perception, planning, and control inside a robot.

It acts as the **nervous system** of a humanoid robot.

---

## 🧠 Nodes

A **Node** is a small executable program inside ROS 2.

Each node performs one focused task.

Examples:

- Camera node (publishes images)
- IMU node (publishes orientation data)
- Navigation node (computes path)
- Motor controller node (controls joints)

Good robotics design = many small nodes working together.

---

## 📡 Topics

Nodes communicate using **Topics**.

A Topic follows a Publish / Subscribe model.

Example topics:

/camera/image_raw
/imu/data
/cmd_vel


Nodes do NOT talk directly to each other.  
They communicate through topics.

This makes the system modular and scalable.

---

## 🔁 Services vs Actions

### Services

Used for short, instant tasks:

- Reset robot
- Get battery level
- Change parameter

Service = Request → Response (one-time interaction)

---

### Actions

Used for long-running tasks:

- Walk to target
- Pick object
- Navigate room

Actions provide:

- Continuous feedback
- Final result
- Cancellation support

Humanoid robots heavily rely on Actions.

---

## 🧠 Real-World Example (Humanoid Flow)

User says:

> “Go to the kitchen”

System flow:

Voice → Whisper  
LLM → Plan steps  
ROS 2 Action → Navigate  
Motor controller → Execute  

This entire pipeline runs through ROS 2.

---

## ⚙️ DDS (Data Distribution Service)

ROS 2 uses **DDS** as its communication layer.

DDS allows:

- Real-time communication
- Reliable message delivery
- Multi-robot scalability
- No central master (unlike ROS 1)

This is critical for industrial-grade robotics systems.

---

## 🔄 Node Lifecycle

Advanced ROS 2 nodes can have lifecycle states:

- Unconfigured
- Inactive
- Active
- Finalized

This allows safer startup/shutdown behavior in humanoid robots.

---

## 🏗 Why This Matters for Physical AI

Physical AI requires:

- Low latency communication
- Reliable execution
- Modular architecture
- Sensor integration
- Real-time feedback loops

ROS 2 provides the nervous system for all of this.

Without ROS 2, a humanoid robot cannot coordinate perception, planning, and motion.

---

## 🎯 Learning Outcomes

After this lesson you can:

- Explain DDS
- Explain Node lifecycle
- Differentiate Topics, Services, and Actions
- Understand humanoid robot communication flow
- Describe how ROS 2 connects AI to physical motion

---