# 🤖 Agentic Robotics

> A curated skill library for AI assistants helping robotics engineers.
> Works with Cursor, Claude Code, Windsurf, or any tool that consumes markdown skill files.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/agentic-robotics.git
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

- **28 consolidated skills** — Each skill is substantial (500-3000 lines), covering a complete domain
- **Tool-agnostic** — Plain markdown with YAML frontmatter, consumable by any AI tool
- **Real-world focus** — Anti-patterns and failure modes alongside working code
- **Progressive disclosure** — Quick start at top, deep reference below

## Project Status

This project is actively being developed. Below is the current status:

### ✅ Completed (Phase 1-4)
- **Phase 1** (Foundation): ros2, robot-modeling, gazebo, camera-vision, ros2-control ✓
- **Phase 2** (Navigation): nav2, sensor-fusion-slam, path-planning, lidar-pointcloud, control-systems ✓
- **Phase 3** (Manipulation & Hardware): moveit2, grasping-force-control, serial-can-protocols, microcontrollers, realtime-motor-control ✓
- **Phase 4** (AI & Advanced): isaac-sim, mujoco, sim-to-real, learning-robotics, edge-ml-deployment, robot-architecture, safety-systems ✓

### 🚧 Remaining (Phase 5)
- **Skills**: ros2-web-bridge, gpio-i2c-spi, sensor-actuator-drivers, rtos-micro-ros, docker-ros2-ci, deployment-fleet
- **Guides**: production-deployment.md, testing-strategy.md
- **Templates**: Starter templates for ROS2 packages, URDF, Docker

See [plan.md](plan.md) for full roadmap details.

## Skill Catalog

### Core Middleware
| Skill | Description | Status |
|-------|-------------|--------|
| [ros2](skills/ros2/SKILL.md) | ROS2 development: nodes, topics, services, actions, launch files, QoS, lifecycle, DDS | ✅ |
| [ros2-control](skills/ros2-control/SKILL.md) | ros2_control framework: hardware interfaces, controllers, transmissions | ✅ |
| ros2-web-bridge | Web integration: rosbridge, FastAPI, WebSocket streaming, REST APIs | 🚧 |
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
| gpio-i2c-spi | GPIO, PWM, interrupts, I2C, SPI protocols | 🚧 |
| sensor-actuator-drivers | Custom driver development, motor/servo/stepper drivers | 🚧 |

### Embedded Systems
| Skill | Description | Status |
|-------|-------------|--------|
| [microcontrollers](skills/microcontrollers/SKILL.md) | STM32, ESP32, Arduino, bare-metal firmware, HAL patterns | ✅ |
| rtos-micro-ros | FreeRTOS, Zephyr, real-time scheduling, micro-ROS | 🚧 |

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
| docker-ros2-ci | Docker builds, pytest, launch_testing, GitHub Actions | 🚧 |
| deployment-fleet | OTA updates, fleet management, logging, diagnostics | 🚧 |

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
| Production Deployment | Pre-deployment checklist | 🚧 |
| Testing Strategy | Unit → integration → field testing | 🚧 |

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