# Contributing to Robotics Agent Skills

Thank you for your interest in contributing! This guide will help you add new skills or improve existing ones.

## How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/your-skill-name`)
3. **Add or modify skills** following the format below
4. **Validate your skill** using the validator script
5. **Submit a pull request** with a clear description

## Skill Format

Every skill must follow this format exactly:

```yaml
---
name: skill-name
description: >
  One-line description used by AI tools for skill discovery.
  Be specific about when to use this skill.
category: middleware|simulation|perception|navigation|manipulation|control|hardware|embedded|ai|architecture|devops
tags: [ros2, navigation, planning]
version: "1.0.0"
---
```

### Required Sections

```markdown
# Skill Name

## When to Use
Explicit trigger conditions. When should an AI load this skill?
List scenarios, keywords, and user intent patterns.

Example:
- "Setting up a new ROS2 workspace"
- "Debugging QoS mismatches"
- "Configuring lifecycle nodes"

## Quick Start
Installation commands and a minimal working example.
Get something running in under 2 minutes.

## Core Concepts
The essential mental model. What does an engineer need to understand?
Each concept gets a working code example (not pseudocode).

## Common Patterns
Practical code patterns engineers use daily.
Each pattern is a complete, copy-paste-ready example.

## Anti-Patterns
What NOT to do, why it breaks, and what happens when it does.
Pair each anti-pattern with the correct approach.

Example:
### ❌ Creating nodes in a loop
Creating a new publisher inside a callback causes memory leaks and DDS discovery overhead.

### ✅ Reuse publishers
Create publishers once in __init__, reuse them in callbacks.

## Configuration Reference
Parameter tables for key config files.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| use_sim_time | bool | false | Use simulation clock |

## Troubleshooting
Symptom -> Cause -> Solution tables for common failures.

| Symptom | Cause | Solution |
|---------|-------|----------|
| Topics not connecting | QoS mismatch | Check reliability settings |

## Workflow Integration
How this skill connects to other skills and where it fits
in the robot development lifecycle.

Example:
- After calibrating cameras (`camera-vision`), use this skill for navigation setup
- Before deployment, review `safety-systems` for hardening
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

## Quality Standards

### Per-Skill Requirements

- [ ] YAML frontmatter validates against schema
- [ ] All required sections present
- [ ] Every code block is syntactically valid (tested)
- [ ] At least 3 anti-patterns documented
- [ ] Troubleshooting table has 5+ entries
- [ ] Size is within 500-3000 lines
- [ ] Cross-references to related skills are correct

### Size Guidelines

- **Under 500 lines**: Too thin, consolidate with related skills
- **500-1500 lines**: Good for focused topics
- **1500-3000 lines**: Good for comprehensive domains
- **Over 3000 lines**: Consider splitting

## Validation

Run the validator before submitting:

```bash
python scripts/validate-skills.py skills/your-skill/
```

This checks:
- YAML frontmatter format
- Required sections present
- No broken internal links
- Size within limits

## Style Guide

### Code Examples

- Use **working, tested code** — no pseudocode
- Include **comments** explaining non-obvious parts
- Show **imports** at the top of each example
- Use **realistic variable names** (not `foo`, `bar`)

### Writing Style

- **Be direct**: "Do X" not "You might want to consider doing X"
- **Be specific**: Include concrete numbers, thresholds, units
- **Show before tell**: Code example first, explanation after
- **Use tables** for configuration parameters and troubleshooting

### Formatting

- Use `backticks` for code, file names, and ROS2 topic names
- Use **bold** for emphasis on critical warnings
- Use > blockquotes for important notes

## Skill Categories

Use these exact category values in the YAML frontmatter:

| Category | Topics |
|----------|--------|
| `middleware` | ROS2, DDS, communication, web bridges |
| `simulation` | Gazebo, Isaac Sim, MuJoCo, sim-to-real |
| `perception` | Cameras, LiDAR, vision, point clouds, SLAM |
| `navigation` | Path planning, Nav2, costmaps, waypoints |
| `manipulation` | MoveIt2, grasping, force control |
| `control` | Control theory, motor control, real-time |
| `hardware` | Serial, CAN, EtherCAT, GPIO, drivers |
| `embedded` | MCUs, RTOS, micro-ROS, firmware |
| `ai` | Machine learning, RL, imitation learning |
| `architecture` | Design patterns, state estimation, multi-robot |
| `devops` | Docker, CI/CD, testing, deployment, safety |

## Submitting Changes

### Pull Request Template

```markdown
## Description
Brief description of what this PR adds or changes.

## Type of Change
- [ ] New skill
- [ ] Skill improvement
- [ ] Bug fix
- [ ] Documentation update

## Checklist
- [ ] Skill validates with `validate-skills.py`
- [ ] All code examples tested
- [ ] Anti-patterns documented
- [ ] Size within 500-3000 lines
- [ ] Related skills cross-referenced

## Testing
How did you test these changes?
```

### Review Process

1. **Automated checks** must pass (validation script)
2. **Maintainer review** for content accuracy
3. **Community feedback** welcome for 48 hours
4. **Merge** when approved

## Questions?

- Open an issue for discussion before major changes
- Join our [Discord/Slack] for real-time chat
- Check existing skills for examples

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.