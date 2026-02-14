---
title: Hardware Foundations
sidebar_label: Introduction
---

# Hardware Foundations

Physical AI is not only software.

It requires real hardware.

Humanoid robotics sits at the intersection of:

- AI
- Sensors
- Actuators
- Embedded systems

---

## 🧠 The AI Brain

### NVIDIA Jetson Orin Nano / NX

Role:

- Runs ROS 2 nodes
- Executes perception models
- Handles navigation
- Processes camera input

This is the robot's **edge brain**.

---

## 👀 Vision Sensors

### Intel RealSense D435i

Provides:

- RGB camera
- Depth camera
- IMU (inertial measurement)

Used for:

- SLAM
- Obstacle detection
- Object recognition

Depth perception is critical for humanoids.

---

## 📡 LiDAR

LiDAR provides:

- 360° distance scanning
- Mapping capability
- Localization data

Used heavily in navigation systems.

---

## 🧭 IMU (Inertial Measurement Unit)

Provides:

- Orientation
- Acceleration
- Rotation data

Essential for:

- Balance
- Walking stability
- Fall detection

Humanoid robots rely heavily on IMUs.

---

## ⚙ Actuators

Actuators are motors that move the robot.

Types:

- Servo motors
- BLDC motors
- Linear actuators

They control:

- Arms
- Legs
- Head
- Fingers

---

## 🔋 Power System

Robots require:

- High-current batteries
- Power regulation
- Safe shutdown systems

Humanoids consume significant power during walking.

---

## 🧩 Robot Lab Setup

Basic student lab:

- RTX Workstation
- Jetson Orin Nano
- RealSense Camera
- USB Microphone
- Test robot (Unitree Go2 or small humanoid)

Simulation first.
Physical deployment second.

---

## 🎯 Learning Outcomes

After this lesson you can:

- Identify required robotics hardware
- Explain edge computing role
- Understand sensor importance
- Describe actuator function
- Design a basic Physical AI lab

---
