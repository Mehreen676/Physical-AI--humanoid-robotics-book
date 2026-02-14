sidebar_label: Gazebo Setup
---

# Gazebo Simulation Setup

Gazebo is the core physics engine used with ROS 2.

It simulates:

- Gravity
- Collisions
- Joint physics
- Sensors
- Robot movement

---

## 🧠 Architecture Overview

Gazebo works with:

- ROS 2 nodes
- URDF robot description
- Sensor plugins
- Controller plugins

Flow:

URDF → Gazebo loads robot  
Plugins → Connect to ROS 2  
Topics → Publish sensor data  

---

## 🏗 URDF in Gazebo

URDF describes:

- Links
- Joints
- Mass
- Inertia
- Collision shapes

Gazebo reads URDF and simulates:

- Rigid body physics
- Torque
- Contact forces

Without URDF, no robot exists in simulation.

---

## 📡 Sensor Simulation

Gazebo supports:

- RGB Camera
- Depth Camera
- LiDAR
- IMU
- GPS

Example simulated topics:

- `/camera/image_raw`
- `/scan`
- `/imu/data`
- `/odom`

These behave like real robot hardware.

---

## 🔁 Controller Integration

Gazebo integrates with:

- ros2_control
- Joint controllers
- Velocity controllers

Example:

Navigation stack publishes `/cmd_vel`  
Controller converts it into wheel/joint motion  

This simulates real robot movement.

---

## ⚠ Why Simulation First?

Testing on real humanoids can:

- Break motors
- Damage joints
- Cause instability

Simulation allows:

- Safe debugging
- AI model testing
- Motion tuning

Before real-world deployment.

---

## 🏗 Digital Twin Loop

1. Sensor publishes data  
2. AI processes input  
3. Planner generates command  
4. Controller executes motion  
5. Gazebo updates physics  

This loop runs continuously.

---

## 🎯 Learning Outcomes

After this lesson you can:

- Explain Gazebo architecture
- Understand URDF role
- Understand sensor simulation
- Understand controller integration
- Explain simulation feedback loop

---
