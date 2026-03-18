---
description: Robotics testing — unit, integration, launch tests; pytest and launch_testing.
---

# Robotics Testing Standards

Use when writing or reviewing tests for ROS2/robotics packages. See `skills/ros2/SKILL.md` and (if present) `skills/robotics-testing/SKILL.md` for full patterns.

## Test Layout

```
package_name/test/
├── unit/           # Pure logic, no ROS
├── integration/    # Node-level, rclpy/rclcpp
└── e2e/            # Launch-based system tests
```

## Unit Tests

- Test domain logic and utilities **without** ROS; use pytest (Python) or GTest (C++).
- No `rclpy.init()` in unit tests; keep them fast and deterministic.

## Integration Tests (Python)

- Initialize ROS once per module: `rclpy.init()` in a `scope='module'` fixture; `rclpy.shutdown()` in teardown.
- Create a fresh node per test if state matters; destroy it in teardown.
- Use `rclpy.spin_once(node, timeout_sec=...)` to process one callback when testing pub/sub.

```python
@pytest.fixture(scope='module')
def ros2_context():
    rclpy.init()
    yield
    rclpy.shutdown()

@pytest.fixture
def test_node(ros2_context):
    node = Node('test_node')
    yield node
    node.destroy_node()
```

## Launch Tests (E2E)

- Use `launch_testing` with `ReadyToTest()` so tests start after nodes are up.
- Keep launch test descriptions minimal (one launch file under test) for clarity and speed.

## Commands

- `colcon test` — run all package tests.
- `colcon test --packages-select <pkg>` — run tests for one package.
- `colcon test-result --all` — show results after a test run.

One concern per test; avoid flaky timing by using timeouts and explicit synchronization (e.g. wait for first message) instead of fixed sleeps where possible.
