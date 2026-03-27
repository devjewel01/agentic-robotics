# 🤖 Agentic Robotics

> A curated skill library for AI assistants helping robotics engineers.
> Works with Cursor, Claude Code, Windsurf, or any tool that consumes markdown skill files.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Quick Start

```bash
# Clone the repository
https://github.com/devjewel01/Agentic-Robotics
cd agentic-robotics

# Use with Cursor IDE
# In Cursor settings, add skill paths:
# /path/to/agentic-robotics/skills/ros2/SKILL.md
# /path/to/agentic-robotics/skills/nav2/SKILL.md

# Use with Claude Code
# Reference in your project's CLAUDE.md:
# When working on ROS2, read /path/to/agentic-robotics/skills/ros2/SKILL.md
```

## What is This?

A comprehensive skill library covering the full robotics engineering stack:

- **29 consolidated skills** — Each skill is substantial (500-3000 lines), covering a complete domain
- **Tool-agnostic** — Plain markdown with YAML frontmatter, consumable by any AI tool
- **Real-world focus** — Anti-patterns and failure modes alongside working code
- **Progressive disclosure** — Quick start at top, deep reference below

## Project Status

This project is actively being developed. Below is the current status:

### ✅ Completed (Phase 1-5)
- **Phase 1** (Foundation): ros2, robot-modeling, gazebo, camera-vision, ros2-control ✓
- **Phase 2** (Navigation): nav2, sensor-fusion-slam, path-planning, lidar-pointcloud, control-systems ✓
- **Phase 3** (Manipulation & Hardware): moveit2, grasping-force-control, serial-can-protocols, microcontrollers, realtime-motor-control ✓
- **Phase 4** (AI & Advanced): isaac-sim, mujoco, sim-to-real, learning-robotics, edge-ml-deployment, robot-architecture, safety-systems ✓
- **Phase 5** (Embedded, DevOps & Production): gpio-i2c-spi, sensor-actuator-drivers, rtos-micro-ros, deployment-fleet, robot-bringup, ros2-web-bridge, docker-ros2-ci ✓
- **Phase 5 Guides**: production-deployment.md, testing-strategy.md ✓

### 🚧 Remaining
- **Templates**: Starter templates for ROS2 packages, URDF, Docker

## Skill Catalog

### Core Middleware
| Skill | Description | Status |
|-------|-------------|--------|
| [ros2](skills/ros2/SKILL.md) | ROS2 development: nodes, topics, services, actions, launch files, QoS, lifecycle, DDS | ✅ |
| [ros2-control](skills/ros2-control/SKILL.md) | ros2_control framework: hardware interfaces, controllers, transmissions | ✅ |
| [ros2-web-bridge](skills/ros2-web-bridge/SKILL.md) | Web integration: rosbridge, FastAPI, WebSocket streaming, REST APIs | ✅ |
| [robot-modeling](skills/robot-modeling/SKILL.md) | URDF, Xacro, TF2 transforms, robot state publisher | ✅ |

### Simulation
| Skill | Description | Status |
|-------|-------------|--------|
| [gazebo](skills/gazebo/SKILL.md) | Gazebo Classic & Sim: SDF worlds, plugins, physics, sensor models | ✅ |
| [isaac-sim](skills/isaac-sim/SKILL.md) | NVIDIA Isaac Sim: USD format, photorealistic rendering, synthetic data | ✅ |
| [mujoco](skills/mujoco/SKILL.md) | MuJoCo physics: contact modeling, MJCF, optimal control | ✅ |
| [sim-to-real](skills/sim-to-real/SKILL.md) | Domain transfer: reality gap, domain adaptation, validation | ✅ |

### Perception
| Skill | Description | Status |
|-------|-------------|--------|
| [camera-vision](skills/camera-vision/SKILL.md) | Camera calibration, OpenCV, detection, tracking, depth pipelines | ✅ |
| [lidar-pointcloud](skills/lidar-pointcloud/SKILL.md) | PCL, Open3D, filtering, registration, ICP, segmentation | ✅ |
| [sensor-fusion-slam](skills/sensor-fusion-slam/SKILL.md) | Multi-sensor fusion, EKF, ORB-SLAM3, RTAB-Map, Cartographer | ✅ |

### Navigation
| Skill | Description | Status |
|-------|-------------|--------|
| [nav2](skills/nav2/SKILL.md) | Nav2 stack: behavior trees, planners, controllers, recovery | ✅ |
| [path-planning](skills/path-planning/SKILL.md) | A*, RRT, costmaps, waypoint following, coverage planning | ✅ |

### Manipulation
| Skill | Description | Status |
|-------|-------------|--------|
| [moveit2](skills/moveit2/SKILL.md) | Motion planning, collision checking, trajectory execution | ✅ |
| [grasping-force-control](skills/grasping-force-control/SKILL.md) | Grasp synthesis, F/T sensing, impedance control, pick-and-place | ✅ |

### Control
| Skill | Description | Status |
|-------|-------------|--------|
| [control-systems](skills/control-systems/SKILL.md) | PID, LQR, MPC, state-space, system identification, trajectories | ✅ |
| [realtime-motor-control](skills/realtime-motor-control/SKILL.md) | Motor drivers, PID tuning, loops, PREEMPT_RT, determinism | ✅ |

### Hardware Interfaces
| Skill | Description | Status |
|-------|-------------|--------|
| [serial-can-protocols](skills/serial-can-protocols/SKILL.md) | UART, RS485, CAN 2.0, CANopen, J1939, EtherCAT | ✅ |
| [gpio-i2c-spi](skills/gpio-i2c-spi/SKILL.md) | GPIO, PWM, interrupts, I2C, SPI protocols on Linux/RPi | ✅ |
| [sensor-actuator-drivers](skills/sensor-actuator-drivers/SKILL.md) | Custom ROS2 driver development: IMU, encoder, motor, servo | ✅ |

### Embedded Systems
| Skill | Description | Status |
|-------|-------------|--------|
| [microcontrollers](skills/microcontrollers/SKILL.md) | STM32, ESP32, Arduino, bare-metal firmware, HAL patterns | ✅ |
| [rtos-micro-ros](skills/rtos-micro-ros/SKILL.md) | FreeRTOS task scheduling, micro-ROS on STM32/ESP32, real-time patterns | ✅ |

### AI & Learning
| Skill | Description | Status |
|-------|-------------|--------|
| [learning-robotics](skills/learning-robotics/SKILL.md) | Imitation learning, RL for robotics, VLA models | ✅ |
| [edge-ml-deployment](skills/edge-ml-deployment/SKILL.md) | TensorRT, ONNX, quantization, Jetson, data pipelines | ✅ |

### Architecture & Safety
| Skill | Description | Status |
|-------|-------------|--------|
| [robot-architecture](skills/robot-architecture/SKILL.md) | Design patterns, BT/FSM, state estimation, multi-robot | ✅ |
| [safety-systems](skills/safety-systems/SKILL.md) | Watchdogs, SROS2, functional safety (ISO 10218, IEC 61508) | ✅ |

### DevOps & Production
| Skill | Description | Status |
|-------|-------------|--------|
| [robot-bringup](skills/robot-bringup/SKILL.md) | systemd, layered launch, udev, watchdog, production bringup | ✅ |
| [docker-ros2-ci](skills/docker-ros2-ci/SKILL.md) | Docker builds, docker-compose, DDS in containers, CI with colcon | ✅ |
| [deployment-fleet](skills/deployment-fleet/SKILL.md) | OTA updates, fleet management, centralized logging, diagnostics | ✅ |

## Commands

Quick CLI reference for daily use and AI-assisted workflows:

| File | Description |
|------|-------------|
| [commands/ros2.md](commands/ros2.md) | colcon build/test, `ros2 node/topic/service/action/param`, rqt, tf2_tools, ros2 doctor |

## Rules

Project-wide conventions and always-on rules for ROS2 and robotics projects. Use in Cursor rules, Claude project instructions, or as team standards:

| File | Description |
|------|-------------|
| [rules/ros2-general.md](rules/ros2-general.md) | Package naming, file structure, launch, params, logging |
| [rules/ros2-nodes.md](rules/ros2-nodes.md) | Node design: parameters first, pub/sub order, QoS, lifecycle |
| [rules/ros2-communication.md](rules/ros2-communication.md) | Topic naming, QoS selection, message/service packages, TF2 |
| [rules/robotics-testing.md](rules/robotics-testing.md) | Unit, integration, launch tests; pytest, launch_testing |
| [rules/clean-architecture.md](rules/clean-architecture.md) | Optional: domain / application / infrastructure layers |
| [rules/robot-specific.md](rules/robot-specific.md) | Optional: URDF, TF tree, Nav2, sensor/motor patterns |

## Usage

### With Cursor IDE

Add skills in Cursor settings or create `.cursor/rules/robotics.md`:

```markdown
When working on ROS2 navigation, reference:
- /path/to/agentic-robotics/skills/ros2/SKILL.md
- /path/to/agentic-robotics/skills/nav2/SKILL.md
```

### With Claude Code

Reference skills in your project's `CLAUDE.md`:

```markdown
## ROS2 Development Guidelines

When the user asks about ROS2, read and follow:
- /path/to/agentic-robotics/skills/ros2/SKILL.md

When working on robot perception:
- /path/to/agentic-robotics/skills/camera-vision/SKILL.md
- /path/to/agentic-robotics/skills/sensor-fusion-slam/SKILL.md
```

### With Any AI Tool

Skills are plain markdown. Copy the content into your context, or configure your tool to read the file when relevant topics come up.

### Manual Reference

Skills are well-structured documentation. Engineers can read them directly.

## Guides

Multi-skill workflow guides:

| Guide | Description | Status |
|-------|-------------|--------|
| [Robot Bringup](guides/robot-bringup.md) | First power-on checklist | ✅ |
| [Sensor Calibration](guides/sensor-calibration.md) | End-to-end calibration workflow | ✅ |
| [Hardware Integration](guides/hardware-integration.md) | Wiring to first ROS2 topic | ✅ |
| [Sim-to-Real Pipeline](guides/sim-to-real-pipeline.md) | Full sim-to-real transfer | ✅ |
| [Production Deployment](guides/production-deployment.md) | Pre-deployment checklist, staging, rollback | ✅ |
| [Testing Strategy](guides/testing-strategy.md) | Unit → integration → sim → HIL → field testing | ✅ |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Skill format specification
- How to add a new skill
- Code review process
- Style guide

## Design Principles

1. **Flat and discoverable** — Two-level hierarchy (`skills/<name>/SKILL.md`)
2. **Consolidated skills** — Substantial references (~500-3000 lines), no thin stubs
3. **Tool-agnostic** — Plain markdown with YAML frontmatter
4. **Real-world focus** — Anti-patterns and failure modes documented
5. **Progressive disclosure** — Quick start at top, deep reference below

## License

Apache 2.0 — See [LICENSE](LICENSE)

## References

- [ROS2](https://github.com/ros2)
- [MoveIt2](https://moveit.ros.org)
- [Nav2](https://ros-planning.github.io/navigation2)
- [OpenCV](https://opencv.org)
- [PCL](https://pointclouds.org)
- [Gazebo](https://gazebosim.org)