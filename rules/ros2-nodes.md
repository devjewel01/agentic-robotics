---
description: ROS2 node design — parameters first, publishers before subscribers, QoS, services, lifecycle.
---

# ROS2 Node Standards

Apply when writing or reviewing ROS2 nodes. Full patterns in `skills/ros2/SKILL.md`.

## Initialization Order

1. **Declare and read parameters first** — before creating any pub/sub/service.
2. **Create publishers** — so they exist before any subscriber callback can run.
3. **Create subscribers** — last, so callbacks do not fire before the node is ready.
4. **Create timers** — for periodic work.
5. **Optional:** Add parameter change callback with `add_on_set_parameters_callback`.

## Base Node Pattern (Python)

```python
import rclpy
from rclpy.node import Node

class BaseRobotNode(Node):
    def __init__(self, node_name: str, **kwargs):
        super().__init__(node_name, **kwargs)
        self.declare_parameter('update_rate', 10.0)
        self.declare_parameter('use_sim_time', False)
        self._update_rate = self.get_parameter('update_rate').value
        self.get_logger().info(f'{node_name} initialized')

    def create_rate_timer(self, callback):
        period = 1.0 / self._update_rate
        return self.create_timer(period, callback)
```

## QoS by Use Case

- **Sensor data (LiDAR, camera):** `BEST_EFFORT`, `VOLATILE`, depth 1–5.
- **Commands (cmd_vel, goals):** `RELIABLE`, `VOLATILE`, depth 10.
- **State / config (robot_description, map):** `RELIABLE`, `TRANSIENT_LOCAL`, depth 1.

Do not create publishers or subscribers inside callbacks — create them once in `__init__` and reuse.

## Callback Groups

- Use `MutuallyExclusiveCallbackGroup` when callbacks must not run in parallel (e.g. shared state).
- Use `ReentrantCallbackGroup` when callbacks are independent.
- For heavy or blocking callbacks, consider `MultiThreadedExecutor` and assign callback groups to avoid blocking other callbacks.

## Services and Actions

- Keep service/action callbacks short; delegate heavy work to a timer or thread and signal completion.
- Return quickly from the callback; do not block the executor.

## Lifecycle Nodes

- For managed (lifecycle) nodes: implement `on_configure`, `on_activate`, `on_deactivate`, `on_cleanup`.
- Create publishers in `on_configure`; start timers/subscriptions in `on_activate`; stop them in `on_deactivate`.
