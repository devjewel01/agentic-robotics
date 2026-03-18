---
description: ROS2 communication — topic naming, QoS profiles, when to use reliable vs best-effort.
---

# ROS2 Communication Standards

Use when defining topics, services, actions and QoS. See `skills/ros2/SKILL.md` for full detail.

## Topic Naming

- **Format:** `/<namespace>/<category>/<specific>` when using namespaces (e.g. multi-robot).
- Use **lowercase** and **underscores**; avoid abbreviations.
- Examples: `/robot/sensors/lidar/scan`, `/robot/control/cmd_vel`, `/robot/state/odometry`.

| Rule              | Example                |
| ----------------- | ---------------------- |
| Lowercase         | `/robot/cmd_vel`       |
| Underscores       | `/joint_states`        |
| Descriptive       | `/laser_scan` not `/ls`|
| Namespace per bot | `/robot1/cmd_vel`      |

## QoS Selection

| Data type          | Reliability | Durability      | Depth | Use for              |
| ------------------ | ----------- | --------------- | ----- | -------------------- |
| Sensor (high freq) | BEST_EFFORT | VOLATILE        | 1–5   | LiDAR, camera, IMU   |
| Commands           | RELIABLE    | VOLATILE        | 10    | cmd_vel, goals       |
| State / config     | RELIABLE    | TRANSIENT_LOCAL | 1     | robot_description, map |
| Transforms         | RELIABLE    | VOLATILE        | 100   | tf                   |

**Mismatch rule:** Publisher and subscriber QoS must be compatible (e.g. both RELIABLE, or one BEST_EFFORT with compatible depth); otherwise messages may not be received.

## Message / Service / Action Packages

- Keep interfaces in a dedicated package (e.g. `robot_interfaces`).
- Use `std_msgs/Header` in messages for timestamp and `frame_id`.
- Prefer explicit request/response and feedback in services and actions; document units (e.g. metres, radians).

## TF2

- Publish static transforms with `StaticTransformBroadcaster`; dynamic with `TransformBroadcaster`.
- Keep frame names consistent with URDF and config (e.g. `base_link`, `odom`, `map`). See `skills/robot-modeling/SKILL.md`.
