# Robotics Agent Skills

> A curated skill library for AI assistants helping robotics engineers.
> Works with Cursor, Claude Code, Windsurf, or any tool that consumes markdown skill files.

## Design Principles

1. **Flat and discoverable** -- Two-level hierarchy max (`skills/<name>/SKILL.md`). No deep nesting.
2. **Consolidated skills** -- Each skill is a substantial, self-contained reference (~500-3000 lines). No single-page stubs.
3. **Tool-agnostic** -- SKILL.md is plain markdown with YAML frontmatter. Any AI tool can consume it.
4. **Real-world focus** -- Anti-patterns and failure modes alongside happy paths. Working code over pseudocode.
5. **Progressive disclosure** -- Quick Start at the top, deep reference at the bottom. Experts skip ahead; beginners follow through.

---

## Folder Structure

```
robotics-agent-skills/
├── README.md                       # Project overview, installation, quick start
├── CONTRIBUTING.md                 # How to add/improve skills
├── LICENSE                         # Apache 2.0
├── .gitignore
│
├── skills/                         # All SKILL.md files live here (flat)
│   ├── ros2/SKILL.md
│   ├── ros2-control/SKILL.md
│   ├── ros2-web-bridge/SKILL.md
│   ├── robot-modeling/SKILL.md
│   ├── gazebo/SKILL.md
│   ├── isaac-sim/SKILL.md
│   ├── mujoco/SKILL.md
│   ├── sim-to-real/SKILL.md
│   ├── camera-vision/SKILL.md
│   ├── lidar-pointcloud/SKILL.md
│   ├── sensor-fusion-slam/SKILL.md
│   ├── nav2/SKILL.md
│   ├── path-planning/SKILL.md
│   ├── moveit2/SKILL.md
│   ├── grasping-force-control/SKILL.md
│   ├── control-systems/SKILL.md
│   ├── realtime-motor-control/SKILL.md
│   ├── serial-can-protocols/SKILL.md
│   ├── gpio-i2c-spi/SKILL.md
│   ├── sensor-actuator-drivers/SKILL.md
│   ├── microcontrollers/SKILL.md
│   ├── rtos-micro-ros/SKILL.md
│   ├── learning-robotics/SKILL.md
│   ├── edge-ml-deployment/SKILL.md
│   ├── robot-architecture/SKILL.md
│   ├── safety-systems/SKILL.md
│   ├── docker-ros2-ci/SKILL.md
│   └── deployment-fleet/SKILL.md
│
├── guides/                         # Multi-skill workflow guides
│   ├── robot-bringup.md            # First power-on checklist
│   ├── sensor-calibration.md       # End-to-end calibration workflow
│   ├── hardware-integration.md     # Wiring to first ROS2 topic
│   ├── sim-to-real-pipeline.md     # Full sim-to-real transfer workflow
│   ├── production-deployment.md    # Pre-deployment checklist
│   └── testing-strategy.md         # Unit -> integration -> field testing
│
├── templates/                      # Reusable starter files
│   ├── ros2-pkg-python/            # Python ROS2 package template
│   ├── ros2-pkg-cpp/               # C++ ROS2 package template
│   ├── launch-file/                # Launch file templates
│   ├── urdf-robot/                 # Basic URDF/Xacro template
│   └── docker-ros2/                # Dockerfile + compose template
│
├── scripts/                        # Repo maintenance
│   ├── validate-skills.py          # Validate SKILL.md format
│   └── generate-index.py           # Build skills index for README
│
└── references/                     # Background material (not loaded by agents)
    ├── standards.md                # ISO, IEC safety standards
    ├── glossary.md                 # Robotics terminology
    └── bibliography.md             # Books, papers, courses
```

### What changed from the original plan and why

| Original | Redesign | Rationale |
|----------|----------|-----------|
| `skills/core-middleware/ros2/` (3 levels) | `skills/ros2/` (2 levels) | Flat is faster to navigate, easier for tools to glob |
| 68 skills | 28 skills | Consolidated overlapping domains; each skill is now substantial |
| `agents/` folder (12 persona files) | Removed | No AI tool consumes standalone persona files. Domain expertise lives in each SKILL.md's intro and patterns |
| `processes/` folder (6 workflow files) | `guides/` folder | Renamed for clarity; guides reference skills instead of duplicating content |
| `examples/` (5 full robot projects) | `templates/` (starter scaffolding) | Starter templates are actionable; full example projects are a separate repo |
| YAML frontmatter with `compatibility`, `requires`, `related-skills` | Simplified frontmatter | Removed fields that no tool actually reads; kept what matters |

---

## Skill Catalog (28 skills)

### Core Middleware

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 1 | `ros2` | ROS2 development | Nodes, topics, services, actions, launch files, QoS, lifecycle, DDS, parameters, packages |
| 2 | `ros2-control` | ros2_control framework | Hardware interfaces, controllers, transmissions, controller manager, real-time loops |
| 3 | `ros2-web-bridge` | Web integration | rosbridge, FastAPI, WebSocket streaming, REST APIs, web visualization |
| 4 | `robot-modeling` | Robot description | URDF, Xacro, TF2 transforms, robot state publisher, joint types, inertials, collision geometry |

### Simulation

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 5 | `gazebo` | Gazebo Classic & Sim | SDF worlds, plugins, physics config, sensor models, multi-robot sim |
| 6 | `isaac-sim` | NVIDIA Isaac Sim | USD format, photorealistic rendering, domain randomization, synthetic data generation |
| 7 | `mujoco` | MuJoCo physics | Contact modeling, MJCF format, optimal control, DeepMind integration |
| 8 | `sim-to-real` | Domain transfer | Reality gap analysis, domain adaptation, transfer learning, validation methodology |

### Perception

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 9 | `camera-vision` | Camera + CV | Intrinsic/extrinsic calibration, hand-eye calibration, OpenCV, detection, tracking, depth pipelines, RGB-D |
| 10 | `lidar-pointcloud` | LiDAR + 3D | PCL, Open3D, filtering, registration, ICP, segmentation, scan matching, obstacle detection |
| 11 | `sensor-fusion-slam` | Fusion + SLAM | Multi-sensor fusion, time sync, EKF/UKF, ORB-SLAM3, RTAB-Map, Cartographer, GMapping, localization |

### Navigation

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 12 | `nav2` | Nav2 stack | Behavior trees, planners (NavFn, Smac, ThetaStar), controllers (DWB, RPP, MPPI), recovery behaviors |
| 13 | `path-planning` | Planning + costmaps | A*, Dijkstra, RRT/RRT*, costmap layers, inflation, voxel grids, waypoint following, coverage planning |

### Manipulation

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 14 | `moveit2` | MoveIt2 | Motion planning, collision checking, trajectory execution, OMPL, STOMP, planning scene |
| 15 | `grasping-force-control` | Grasping + force | Grasp synthesis, quality metrics, F/T sensing, impedance/admittance control, pick-and-place pipelines |

### Control

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 16 | `control-systems` | Control theory | PID, LQR, MPC, state-space, system identification, trajectory generation, splines, optimization |
| 17 | `realtime-motor-control` | Motors + RT | Motor drivers, PID tuning, current/velocity/position loops, PREEMPT_RT, determinism, jitter |

### Hardware Interfaces

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 18 | `serial-can-protocols` | Serial + CAN + EtherCAT | UART, RS232, RS485, CAN 2.0, CAN FD, CANopen, J1939, EtherCAT, PDO/SDO, protocol framing |
| 19 | `gpio-i2c-spi` | Low-level digital I/O | GPIO, PWM, interrupts, pull-ups, level shifting, I2C, SPI, device addressing, timing |
| 20 | `sensor-actuator-drivers` | Driver development | Custom sensor drivers, datasheet interpretation, motor/servo/stepper drivers, calibration routines |

### Embedded Systems

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 21 | `microcontrollers` | MCU development | STM32, ESP32, Arduino, Nordic, bare-metal firmware, HAL patterns, interrupt handling, timers |
| 22 | `rtos-micro-ros` | RTOS + micro-ROS | FreeRTOS, Zephyr, real-time scheduling, micro-ROS on MCUs, resource-constrained ROS2 |

### AI & Learning

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 23 | `learning-robotics` | Robot learning | Imitation learning, behavior cloning, DAgger, RL for robotics, reward shaping, VLA models |
| 24 | `edge-ml-deployment` | Edge inference | TensorRT, ONNX, quantization, Jetson deployment, RLDS, LeRobot, data pipelines, Zarr |

### Architecture & Safety

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 25 | `robot-architecture` | Software design | Behavior trees, FSMs, subsumption, component architecture, state estimation, Kalman/EKF, multi-robot coordination |
| 26 | `safety-systems` | Safety + security | Watchdogs, E-stops, SROS2, DDS security, functional safety (ISO 10218, IEC 61508, ISO 26262), risk assessment |

### DevOps

| # | Skill | Covers | Key Topics |
|---|-------|--------|------------|
| 27 | `docker-ros2-ci` | Containers + CI | Docker multi-stage builds, GPU passthrough, pytest, launch_testing, GitHub Actions, GitLab CI |
| 28 | `deployment-fleet` | Production ops | OTA updates, fleet management, logging, ros2 doctor, tracing, bag files, diagnostics, monitoring |

### Coverage check against the original 68 skills

Every topic from the original plan is covered. Here's the mapping:

| Original skill | Now lives in |
|----------------|-------------|
| `ros1/` | `ros2` (legacy section) |
| `ros2/` | `ros2` |
| `ros2-web-integration/` | `ros2-web-bridge` |
| `ros2-control/` | `ros2-control` |
| `urdf-xacro/` | `robot-modeling` |
| `tf2-transforms/` | `robot-modeling` |
| `robot-state-publisher/` | `robot-modeling` |
| `gazebo/` | `gazebo` |
| `isaac-sim/` | `isaac-sim` |
| `mujoco/` | `mujoco` |
| `webots/` | `gazebo` (alt simulators section) |
| `sim-to-real/` | `sim-to-real` |
| `synthetic-data/` | `isaac-sim` + `sim-to-real` |
| `camera-calibration/` | `camera-vision` |
| `computer-vision/` | `camera-vision` |
| `point-clouds/` | `lidar-pointcloud` |
| `sensor-fusion/` | `sensor-fusion-slam` |
| `lidar-processing/` | `lidar-pointcloud` |
| `visual-slam/` | `sensor-fusion-slam` |
| `depth-processing/` | `camera-vision` |
| `nav2/` | `nav2` |
| `slam/` | `sensor-fusion-slam` |
| `path-planning/` | `path-planning` |
| `costmaps/` | `path-planning` |
| `waypoint-following/` | `path-planning` |
| `moveit2/` | `moveit2` |
| `grasp-planning/` | `grasping-force-control` |
| `kinematics/` | `moveit2` + `control-systems` |
| `force-control/` | `grasping-force-control` |
| `pick-and-place/` | `grasping-force-control` |
| `control-theory/` | `control-systems` |
| `trajectory-generation/` | `control-systems` |
| `motor-control/` | `realtime-motor-control` |
| `real-time-control/` | `realtime-motor-control` |
| `serial-communication/` | `serial-can-protocols` |
| `can-bus/` | `serial-can-protocols` |
| `ethercat/` | `serial-can-protocols` |
| `gpio-interfacing/` | `gpio-i2c-spi` |
| `i2c-spi/` | `gpio-i2c-spi` |
| `sensor-drivers/` | `sensor-actuator-drivers` |
| `actuator-drivers/` | `sensor-actuator-drivers` |
| `microcontrollers/` | `microcontrollers` |
| `rtos/` | `rtos-micro-ros` |
| `embedded-ros/` | `rtos-micro-ros` |
| `firmware-development/` | `microcontrollers` |
| `hardware-abstraction/` | `microcontrollers` |
| `imitation-learning/` | `learning-robotics` |
| `reinforcement-learning/` | `learning-robotics` |
| `vla-models/` | `learning-robotics` |
| `edge-deployment/` | `edge-ml-deployment` |
| `data-pipelines/` | `edge-ml-deployment` |
| `design-patterns/` | `robot-architecture` |
| `safety-systems/` | `safety-systems` |
| `multi-robot/` | `robot-architecture` |
| `state-estimation/` | `robot-architecture` |
| `docker-ros2/` | `docker-ros2-ci` |
| `testing/` | `docker-ros2-ci` |
| `ci-cd/` | `docker-ros2-ci` |
| `logging-diagnostics/` | `deployment-fleet` |
| `deployment/` | `deployment-fleet` |
| `sros2/` | `safety-systems` |
| `network-security/` | `safety-systems` |
| `functional-safety/` | `safety-systems` |

---

## SKILL.md Format

```yaml
---
name: skill-name
description: >
  One-line description. Used by AI tools for skill discovery and activation.
category: core | simulation | perception | navigation | manipulation | control | hardware | embedded | ai | architecture | devops
tags: [ros2, navigation, planning]
version: "1.0.0"
---
```

### Required Sections

```markdown
# Skill Name

## When to Use
Explicit trigger conditions -- when should an AI load this skill?
List scenarios, keywords, and user intent patterns.

## Quick Start
Installation commands and a minimal working example.
Get something running in under 2 minutes.

## Core Concepts
The essential mental model. What does an engineer need to understand?
Each concept gets a working code example.

## Common Patterns
Practical code patterns engineers use daily.
Each pattern is a complete, copy-paste-ready example.

## Anti-Patterns
What NOT to do, why it breaks, and what happens when it does.
Pair each anti-pattern with the correct approach.

## Configuration Reference
Parameter tables for key config files.

## Troubleshooting
Symptom -> Cause -> Solution tables for common failures.

## Workflow Integration
How this skill connects to other skills and where it fits
in the robot development lifecycle.
```

### Optional Sections

```markdown
## Advanced Topics
Deep dives for experienced engineers.

## Platform-Specific Notes
Differences across ROS2 distributions, OS versions, hardware.

## Migration Guide
Upgrading from older versions or migrating from related tools.
```

### Format Rules

- **No persona instructions** inside SKILL.md. The skill is a knowledge reference, not a system prompt. An AI tool adds its own persona wrapper.
- **Working code only.** Every code block must be syntactically correct and tested. No pseudocode.
- **Anti-patterns are mandatory.** Real engineering value comes from knowing what fails.
- **Size target:** 500-3000 lines per skill. Under 500 is too thin to be useful. Over 3000 is too large for context windows.

---

## Guides (replacing processes/ and agents/)

Guides are lightweight workflow documents that orchestrate multiple skills for a specific engineering task. They don't duplicate skill content -- they reference it.

### Guide Format

```markdown
# Guide: Workflow Name

## Goal
What this workflow achieves.

## Prerequisites
- Skills needed: `ros2`, `robot-modeling`, `gazebo`
- Hardware / software requirements

## Steps

### Step 1: Title
Brief description.
> **Skill reference:** See `skills/ros2/SKILL.md` -> "Core Concepts" -> "Launch Files"

Commands and config specific to this workflow step.

### Step 2: Title
...

## Validation Checklist
- [ ] Checkpoint 1
- [ ] Checkpoint 2

## Common Issues
Link to relevant skill troubleshooting sections.
```

### Why agents/ was removed

The original plan had 12 "agent persona" files like `ros-expert.md` and `navigation-engineer.md`. These were role descriptions ("You are an expert in...") with no mechanism for any AI tool to load them.

In practice:
- **Cursor** uses `.cursor/rules/` files that activate based on glob patterns
- **Claude Code** uses `CLAUDE.md` files at the project root
- **Other tools** use their own configuration formats

Domain expertise belongs **inside each SKILL.md**, not in a separate persona file. When an AI loads `skills/nav2/SKILL.md`, it inherently becomes a Nav2 expert for that conversation. A separate `navigation-engineer.md` persona is redundant.

If users want Cursor rules, they can create `.cursor/rules/` files that point to specific skills. That's a tool-specific integration concern, not part of the skill library itself.

---

## How to Use This Repository

### With Cursor IDE

Add skills as Cursor agent skills in your project's settings or `~/.cursor/skills-cursor/`:

```
# In your Cursor skill configuration, point to:
/path/to/robotics-agent-skills/skills/ros2/SKILL.md
```

Or create a `.cursor/rules/robotics.md` in your project that references relevant skills.

### With Claude Code

Reference skills in your `CLAUDE.md`:

```markdown
When working on ROS2 code, read and follow:
- /path/to/robotics-agent-skills/skills/ros2/SKILL.md
- /path/to/robotics-agent-skills/skills/ros2-control/SKILL.md
```

### With Any AI Tool

Copy the SKILL.md content into your system prompt or context, or configure your tool to read the file when relevant topics come up.

### Manual Reference

Skills are well-structured markdown. Engineers can read them directly as documentation.

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)

The minimum viable set for any ROS2 robotics work.

| Skill | Priority | Est. Size |
|-------|----------|-----------|
| `ros2` | P0 | ~2500 lines |
| `robot-modeling` | P0 | ~1500 lines |
| `gazebo` | P0 | ~2000 lines |
| `camera-vision` | P0 | ~2000 lines |
| `ros2-control` | P0 | ~1500 lines |

Deliverables: 5 skills, README.md, CONTRIBUTING.md, skill validator script.

### Phase 2: Navigation & Perception (Weeks 4-5)

Mobile robot stack.

| Skill | Priority | Est. Size |
|-------|----------|-----------|
| `nav2` | P0 | ~2000 lines |
| `sensor-fusion-slam` | P0 | ~2000 lines |
| `path-planning` | P0 | ~1500 lines |
| `lidar-pointcloud` | P1 | ~1500 lines |
| `control-systems` | P1 | ~1500 lines |

Deliverables: 5 skills, `guides/robot-bringup.md`, `guides/sensor-calibration.md`.

### Phase 3: Manipulation & Hardware (Weeks 6-7)

Arm + embedded stack.

| Skill | Priority | Est. Size |
|-------|----------|-----------|
| `moveit2` | P1 | ~2000 lines |
| `grasping-force-control` | P1 | ~1500 lines |
| `serial-can-protocols` | P1 | ~1500 lines |
| `microcontrollers` | P1 | ~1500 lines |
| `realtime-motor-control` | P1 | ~1500 lines |

Deliverables: 5 skills, `guides/hardware-integration.md`, templates.

### Phase 4: Advanced (Weeks 8-9)

AI, simulation depth, production.

| Skill | Priority | Est. Size |
|-------|----------|-----------|
| `isaac-sim` | P1 | ~1500 lines |
| `mujoco` | P2 | ~1000 lines |
| `sim-to-real` | P1 | ~1200 lines |
| `learning-robotics` | P2 | ~1500 lines |
| `edge-ml-deployment` | P2 | ~1200 lines |
| `robot-architecture` | P1 | ~1500 lines |
| `safety-systems` | P1 | ~1500 lines |

Deliverables: 7 skills, `guides/sim-to-real-pipeline.md`.

### Phase 5: Production & Polish (Week 10)

| Skill | Priority | Est. Size |
|-------|----------|-----------|
| `ros2-web-bridge` | P2 | ~1000 lines |
| `gpio-i2c-spi` | P2 | ~1200 lines |
| `sensor-actuator-drivers` | P2 | ~1200 lines |
| `rtos-micro-ros` | P2 | ~1200 lines |
| `docker-ros2-ci` | P2 | ~1200 lines |
| `deployment-fleet` | P2 | ~1200 lines |

Deliverables: 6 skills, remaining guides, all templates, `generate-index.py`.

---

## Quality Standards

### Per-Skill Requirements

- [ ] YAML frontmatter validates against schema
- [ ] All required sections present
- [ ] Every code block is syntactically valid
- [ ] At least 3 anti-patterns documented
- [ ] Troubleshooting table has 5+ entries
- [ ] Size is within 500-3000 lines
- [ ] Cross-references to related skills are correct

### Repository Requirements

- [ ] `validate-skills.py` passes on all skills
- [ ] README skill index is up to date
- [ ] No broken internal links
- [ ] CONTRIBUTING.md has clear submission process

---

## References

### Standards
- ISO 10218-1/2 -- Industrial robot safety
- ISO/TS 15066 -- Collaborative robots
- IEC 61508 -- Functional safety (electrical systems)
- ISO 26262 -- Automotive functional safety
- IEC 62061 -- Safety of machinery

### Key Texts
- "Probabilistic Robotics" -- Thrun, Burgard, Fox
- "Modern Robotics" -- Lynch & Park
- "Robotics, Vision and Control" -- Peter Corke
- "Springer Handbook of Robotics" -- Siciliano & Khatib

### Open Source
- [ROS2](https://github.com/ros2) | [MoveIt2](https://moveit.ros.org) | [Nav2](https://ros-planning.github.io/navigation2)
- [OpenCV](https://opencv.org) | [PCL](https://pointclouds.org) | [Open3D](http://www.open3d.org)
- [Gazebo](https://gazebosim.org) | [Isaac Sim](https://developer.nvidia.com/isaac-sim) | [MuJoCo](https://mujoco.org)
