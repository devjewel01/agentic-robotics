# Robotics Skill Set — Full Refactor Plan

This document extends the earlier redesign plan with: (1) full skill refactor including renames and consolidation, (2) **commands/** and **rules/** folders.

---

## 1. Target folder layout

After refactor, the repo will have:

```
agentic-robotics/
├── commands/          # NEW — Quick CLI reference (colcon, ros2, debug)
├── rules/             # NEW — Always-on rules (naming, nodes, QoS, testing)
├── skills/            # Refactored — Renamed/merged, one SKILL.md per skill
├── guides/            # Unchanged or lightly updated
├── references/        # Unchanged (read-only)
├── scripts/
├── CONTRIBUTING.md
├── README.md
└── ...
```

---

## 2. commands/ folder

**Purpose:** Short, table-style command references so the AI (or user) can quickly suggest the right CLI without opening a full skill.

| File | Content (source idea) |
|------|------------------------|
| `commands/ros2.md` | colcon build/test, source overlay, `ros2 node/topic/service/action/param` list/echo/pub/call, rqt_graph, rqt_console, tf2_tools view_frames, ros2 doctor. Base on `references/ros2-claude-code-template/.claude/commands/ros2.md`. |

- Keep each file to **one markdown file, tables + minimal prose**.
- In README / CONTRIBUTING, mention: “For quick CLI reference see `commands/`.”

---

## 3. rules/ folder

**Purpose:** Project-wide rules that tools (e.g. Cursor rules, Claude project instructions) can “always apply” when working in this repo or in a robot project that uses it. Short, actionable.

| File | Content (source idea) |
|------|------------------------|
| `rules/ros2-general.md` | Package naming (snake_case), standard layout (package.xml, setup.py/CMakeLists.txt, resource/, launch/, config/, test/). Base on reference `ros2_general.md`. |
| `rules/ros2-nodes.md` | Node design: declare parameters first, publishers before subscribers, use callback groups where needed; optional base-node snippet. Base on reference `ros2_nodes.md`. |
| `rules/ros2-communication.md` | QoS defaults (reliable vs best_effort, depth), when to use which; avoid creating pub/sub inside callbacks. From reference `ros2_communication.md`. |
| `rules/robotics-testing.md` | Prefer pytest for Python nodes; use launch_testing for integration; test one concern per test. From reference `testing.md`. |
| `rules/clean-architecture.md` (optional) | Short: domain/application/infrastructure split; ROS in infrastructure only. From reference `clean_architecture.md`. |
| `rules/robot-specific.md` (optional) | Placeholder for project-specific conventions (frame names, naming, safety). From reference `robot_specific.md`. |

- Each rule file: **YAML frontmatter optional** (`description:` one line). Focus on “do this / avoid that” and small code snippets.
- In README: “For project conventions and rules see `rules/`.”

---

## 4. Skills refactor (names + consolidation)

### 4.1 Naming consistency

- Use **lowercase + hyphen** for folder and skill names: `robot-modeling`, `ros2-control`, `sensor-fusion-slam`.
- Align **name** in frontmatter with folder name (e.g. `name: ros2-control` for `skills/ros2-control/SKILL.md`).

Suggested renames (if any current name feels “off”):

| Current | Proposed | Note |
|--------|----------|------|
| `grasping-force-control` | Keep or `manipulation-force-control` | “Grasping” is standard; keep unless you prefer “manipulation”. |
| `realtime-motor-control` | Keep | Clear. |
| `edge-ml-deployment` | Keep or `ml-edge-deployment` | “Edge ML” is common; keep as is. |
| `serial-can-protocols` | Keep | Clear. |

No mandatory renames; only apply where you already feel the name is wrong.

### 4.2 One skill = one folder, one SKILL.md

- Today each skill is already **one folder + one SKILL.md** (no multi-file skills in current tree). So the main rule is: **do not split one skill into multiple files**; keep a single `SKILL.md` per skill.
- If a topic grows too large (>3000 lines), either trim or split into **two skills** (e.g. “nav2-basics” and “nav2-advanced”) with clear boundaries, each with its own folder and single SKILL.md.

### 4.3 Content merges from references (unchanged from earlier plan)

- **ros2:** Merge in ParameterDescriptor, parameter callback, “When to Use” expansion (references).
- **robot-architecture:** Merge robotics-design-patterns (stack diagram, BT/FSM) and robotics-software-principles (why robotics is different, SOLID-style).
- **safety-systems:** Merge robotics-security (SROS2, attack surface, keystore).
- **camera-vision / lidar-pointcloud:** Merge sensor/device tables and calibration notes from robot-perception.
- **New skills:** robot-bringup, docker-ros2-ci, ros2-web-bridge (and optionally robotics-testing, ros1) as single-file skills.

---

## 5. README updates

- **Skill catalog:** Add new skills (robot-bringup, docker-ros2-ci, ros2-web-bridge); mark Phase 5 items done where applicable.
- **New sections:**
  - **Commands:** “Quick CLI reference: see `commands/` (e.g. `commands/ros2.md`).”
  - **Rules:** “Project conventions and always-on rules: see `rules/`.”

---

## 6. Execution order

1. Add **commands/** and **rules/** (new folders and files as in tables above).
2. Refactor **skills:** renames (if any), then content merges and new skills; keep one SKILL.md per skill.
3. Update **README** (catalog + commands + rules).
4. Run **scripts/validate-skills.py** and fix any issues.

---

## Summary

- **commands/:** Quick reference for ROS2 (and optionally Docker) CLI.
- **rules/:** Short, always-applicable rules (general, nodes, communication, testing, optional clean-architecture and robot-specific).
- **skills:** Keep one file per skill; rename only where needed; merge reference content and add new skills as planned.
- No change to **references/** content; only use it as source for creating/updating files under commands/, rules/, and skills/.
