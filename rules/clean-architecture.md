---
description: Clean Architecture for ROS2 — domain, application, infrastructure; no ROS in domain.
---

# Clean Architecture for ROS2

Optional structure for larger or long-lived robot projects. Skills stay in `skills/`; this rule is a short checklist.

## Layer Rules

1. **Domain** — Entities, value objects, domain interfaces. **No ROS2 or hardware imports.**
2. **Application** — Use cases and application services. Depends only on domain.
3. **Infrastructure** — ROS2 nodes, publishers, subscribers, hardware adapters. Implements domain interfaces.
4. **Presentation** — CLI, GUI, API. Depends on application only.

Dependencies point **inward**: infrastructure and application depend on domain; domain depends on nothing.

## Do Not

- Import `rclpy` / `rclcpp` or any ROS message type in domain or application code.
- Put business rules (e.g. “battery must be > 20% to move”) inside ROS adapters; put them in use cases or domain.
- Let domain entities hold a reference to a ROS node.

## Do

- Define interfaces (ports) in domain; implement them in infrastructure (e.g. `MotionController` interface, `ROS2MotionController` implementation).
- Keep nodes thin: subscribe/publish, convert messages to/from domain types, call use cases.

For full templates and directory layout see reference `references/ros2-claude-code-template/.claude/skills/`.
