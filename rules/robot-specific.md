---
description: Robot-specific conventions — URDF/xacro, TF tree, Nav2 params, sensor/motor patterns.
---

# Robot-Specific Standards

Use when defining robot geometry, frames, navigation, and hardware integration. Full content in `skills/robot-modeling/SKILL.md`, `skills/nav2/SKILL.md`, and related skills.

## TF2 Frame Tree

Keep a consistent tree; typical mobile base:

```
map → odom → base_footprint → base_link
                                 ├── lidar_link
                                 ├── camera_link → camera_optical_frame
                                 ├── imu_link
                                 └── wheel links
```

- Publish `odom → base_link` from odometry; `map → odom` from localization (e.g. AMCL).
- Use `base_footprint` for ground projection if needed by Nav2.

## URDF / Xacro

- Use xacro properties and macros for repeated parts (e.g. wheels, identical arms).
- Every link should have `<inertial>` for simulation and dynamics; use `<collision>` matching `<visual>` where possible.
- Prefer `continuous` joints for wheels; `revolute` with limits for arms.

## Navigation (Nav2)

- Set `global_frame`, `robot_base_frame`, `odom_topic` consistently with your TF tree.
- Tune `controller_frequency`, `max_vel_x`, `max_vel_theta` and planner tolerance to the robot and environment.

## Sensor and Motor Nodes

- Publish sensor data with **sensor QoS** (best-effort, volatile, depth 1–5).
- Subscribe to `cmd_vel` (or equivalent) with reliable QoS; convert to motor commands in one place; avoid multiple nodes writing to the same actuator without a single controller.

Customize this file per project (frame names, topic names, safety limits) and keep a copy in the robot repo.
