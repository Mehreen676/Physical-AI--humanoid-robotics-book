sidebar_label: URDF Basics
---

# URDF Basics (Unified Robot Description Format)

URDF is the file format used to describe a robot’s physical structure in ROS 2.

It defines:

- Links (robot body parts)
- Joints (how parts connect)
- Geometry (shape & size)
- Sensors
- Collision models

URDF allows simulation engines like Gazebo and Isaac Sim to understand your robot.

---

## 🏗 What is a Link?

A **Link** represents a rigid body part.

Examples:

- Head
- Torso
- Arm
- Leg
- Wheel

Each link has:

- Visual model
- Collision model
- Inertia (mass properties)

---

## 🔩 What is a Joint?

A **Joint** connects two links.

Types of joints:

- Revolute (rotational, like elbow)
- Prismatic (sliding)
- Fixed (no movement)
- Continuous (wheel rotation)

Example:

Upper Arm → Elbow Joint → Forearm

---

## 🧍 Example: Simple Robot Arm

A robot arm might look like this:

Base Link  
→ Shoulder Joint  
→ Upper Arm Link  
→ Elbow Joint  
→ Forearm Link  

URDF defines this structure hierarchically.

---

## 📄 Simple URDF Example

```xml
<robot name="simple_bot">

  <link name="base_link"/>

  <joint name="shoulder_joint" type="revolute">
    <parent link="base_link"/>
    <child link="arm_link"/>
  </joint>

  <link name="arm_link"/>

</robot>

This defines:

    One base

    One arm

    One rotating join
    🧠 Why URDF is Critical for Humanoids

Humanoid robots have:

20+ joints

Complex balance constraints

Dynamic walking control

Multiple sensors

Without URDF:

Simulation cannot run

Controllers cannot attach

Physics cannot calculate motion

URDF is the robot’s skeleton blueprint.

🔍 URDF vs SDF
URDF	SDF
ROS standard	Gazebo standard
Simpler	More detailed physics
Used for robot model	Used for simulation world

In most robotics projects:

URDF → converted to SDF → loaded in Gazebo

🏗 URDF in Physical AI Pipeline

Physical AI Flow:

URDF → Simulation → Sensor Data → AI Model → Action → Joint Control

If URDF is wrong:

Robot falls

Joints break

Simulation crashes

So URDF accuracy is essential.

🎯 Learning Outcomes

After this lesson you can:

Explain what URDF is

Define Links and Joints

Understand robot kinematic structure

Connect URDF to simulation

Understand why humanoids require precise modeling