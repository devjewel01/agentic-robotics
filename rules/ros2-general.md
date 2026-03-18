---
description: ROS2 general conventions — package naming, file structure, launch, params, logging.
---

# ROS2 General Conventions

Use when creating or modifying ROS2 packages. For full reference see `skills/ros2/SKILL.md`.

## Package Naming

- Use **snake_case**: lowercase letters and underscores only.
- Prefer descriptive names: `robot_navigation_core`, `robot_perception_msgs`, `robot_control_interfaces`.
- Avoid abbreviations unless widely known (e.g. `cmd_vel` is fine).

## File Structure

```
package_name/
├── package.xml              # Package manifest
├── setup.py                 # Python package (or CMakeLists.txt for C++)
├── setup.cfg                # Python config
├── resource/
│   └── package_name         # Marker file
├── package_name/            # Python source
│   ├── __init__.py
│   └── node_file.py
├── src/                     # C++ source (if C++)
├── include/                 # C++ headers (if C++)
├── launch/
│   └── node_launch.py
├── config/
│   └── params.yaml
└── test/
    └── test_node.py
```

## Launch Files

- Declare launch arguments (e.g. `use_sim_time`) and pass them into node parameters.
- Use `LaunchConfiguration` for arguments so they can be overridden from CLI.

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='false')
    my_node = Node(
        package='package_name',
        executable='node_name',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )
    return LaunchDescription([use_sim_time, my_node])
```

## Parameter Files (YAML)

```yaml
/**:
  ros__parameters:
    update_rate: 10.0
    sensor:
      frame_id: "base_link"
      range_min: 0.1
      range_max: 10.0
```

## Logging

- Use appropriate levels: `debug`, `info`, `warn`, `error`, `fatal`.
- For high-frequency logs use `throttle_duration_sec` or `once=True` to avoid log flood.

## Workspace Layout

```
ros2_ws/
├── src/
│   ├── robot_core/
│   ├── robot_interfaces/
│   ├── robot_bringup/
│   └── third_party/
├── build/
├── install/
└── log/
```
