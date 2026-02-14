
Publishes:

/camera/depth/image_raw


Used for:

- Distance estimation
- Obstacle avoidance
- 3D mapping

---

## 📡 LiDAR

Publishes:

/scan


Used for:

- SLAM (Simultaneous Localization and Mapping)
- Navigation
- Mapping rooms

LiDAR creates a 2D or 3D representation of surroundings.

---

## 🎯 IMU (Inertial Measurement Unit)

Publishes:

/imu/data


Provides:

- Orientation
- Acceleration
- Angular velocity

Humanoid robots depend heavily on IMU for balance.

---

## 🧠 Sensor → AI → Action Flow

Example:

LiDAR → Detect obstacle  
AI → Plan alternate path  
Nav2 → Publish `/cmd_vel`  
Controller → Move robot  

This is real embodied intelligence.

---

## 🏗 Why Sensor Simulation Matters

Before using real hardware:

- Test perception pipelines
- Validate SLAM
- Tune navigation parameters
- Debug sensor fusion

Simulation saves hardware damage.

---

## 🔁 Multi-Sensor Fusion

Advanced humanoids combine:

- Camera
- LiDAR
- IMU

To create:

- Robust localization
- Stable walking
- Accurate manipulation

This is called sensor fusion.

---

## 🎯 Learning Outcomes

After this lesson you can:

- Explain RGB vs Depth
- Explain LiDAR role
- Explain IMU importance
- Understand sensor fusion
- Describe perception-to-action loop

---
