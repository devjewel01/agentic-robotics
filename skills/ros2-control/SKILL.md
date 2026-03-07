---
name: ros2-control
description: ros2_control framework for hardware abstraction, controller management, and real-time robot control including hardware interfaces, controllers, transmissions, and joint limits. Use when interfacing with robot hardware or setting up control systems.
category: middleware
tags: [ros2-control, hardware-interface, controller, real-time, transmission]
version: "1.0.0"
---

# ROS2 Control

ros2_control is the hardware abstraction framework for ROS2. It provides a standardized interface between robot hardware (motors, sensors) and high-level controllers (trajectory following, navigation).

## When to Use

- Interfacing with robot hardware (motors, encoders, sensors)
- Setting up joint position/velocity/effort controllers
- Configuring differential drive or Ackermann steering
- Implementing custom hardware interfaces
- Managing controller lifecycle (load, configure, activate)
- Setting up joint limits and safety constraints
- Integrating with MoveIt2 for trajectory execution
- Configuring transmissions for complex mechanisms

## Quick Start

```bash
# Install ros2_control
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers

# Hardware interface + controller manager launch
ros2 launch my_robot_bringup robot.launch.py
```

```xml
<!-- URDF with ros2_control -->
<ros2_control name="RobotSystem" type="system">
  <hardware>
    <plugin>robot_hardware/RobotHardware</plugin>
    <param name="port">/dev/ttyUSB0</param>
  </hardware>
  
  <joint name="joint1">
    <command_interface name="position"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
</ros2_control>
```

## Core Concepts

### 1. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Controller Manager                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Controller  │  │ Controller  │  │ Controller  │ │
│  │ (position)  │  │ (velocity)  │  │  (effort)   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
└─────────┼────────────────┼────────────────┼────────┘
          │                │                │
┌─────────┴────────────────┴────────────────┴────────┐
│              Hardware Interface                      │
│         (ResourceManager)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Joint 1     │  │ Joint 2     │  │ Sensor 1    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
└─────────┼────────────────┼────────────────┼────────┘
          │                │                │
    ┌─────┴─────┐    ┌─────┴─────┐    ┌─────┴─────┐
    │  Motor    │    │  Motor    │    │  Encoder  │
    │  Driver   │    │  Driver   │    │  / Sensor │
    └───────────┘    └───────────┘    └───────────┘
```

### 2. Hardware Interface Types

| Type | Description | Example |
|------|-------------|---------|
| `System` | Complete robot with multiple joints | Manipulator, mobile base |
| `Sensor` | Read-only sensor interface | IMU, force/torque sensor |
| `Actuator` | Single actuator with command/state | Linear actuator |

**System Hardware Interface:**
```cpp
// include/robot_hardware/robot_system.hpp
#ifndef ROBOT_HARDWARE__ROBOT_SYSTEM_HPP_
#define ROBOT_HARDWARE__ROBOT_SYSTEM_HPP_

#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "rclcpp/rclcpp.hpp"

namespace robot_hardware
{

class RobotSystem : public hardware_interface::SystemInterface
{
public:
  RobotSystem() = default;

  // Lifecycle methods
  hardware_interface::CallbackReturn on_init(
    const hardware_interface::HardwareInfo & info) override;

  hardware_interface::CallbackReturn on_configure(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_activate(
    const rclcpp_lifecycle::State & previous_state) override;

  hardware_interface::CallbackReturn on_deactivate(
    const rclcpp_lifecycle::State & previous_state) override;

  // Read current state from hardware
  hardware_interface::return_type read(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

  // Write commands to hardware
  hardware_interface::return_type write(
    const rclcpp::Time & time,
    const rclcpp::Duration & period) override;

private:
  // Joint states
  std::vector<double> hw_positions_;
  std::vector<double> hw_velocities_;
  
  // Joint commands
  std::vector<double> hw_position_commands_;
  
  // Serial communication
  std::string port_;
  int baud_rate_;
  
  // Hardware connection
  std::unique_ptr<SerialConnection> serial_conn_;
};

}  // namespace robot_hardware

#endif  // ROBOT_HARDWARE__ROBOT_SYSTEM_HPP_
```

**Implementation:**
```cpp
// src/robot_system.cpp
#include "robot_hardware/robot_system.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

namespace robot_hardware
{

hardware_interface::CallbackReturn RobotSystem::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) !=
      hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  // Parse parameters from URDF
  port_ = info.hardware_parameters.at("port");
  baud_rate_ = std::stoi(info.hardware_parameters.at("baud_rate"));

  // Initialize vectors based on number of joints
  hw_positions_.resize(info.joints.size(), 0.0);
  hw_velocities_.resize(info.joints.size(), 0.0);
  hw_position_commands_.resize(info.joints.size(), 0.0);

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotSystem::on_configure(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  // Initialize serial connection
  try {
    serial_conn_ = std::make_unique<SerialConnection>(port_, baud_rate_);
    serial_conn_->connect();
  } catch (const std::exception & e) {
    RCLCPP_FATAL(rclcpp::get_logger("RobotSystem"),
                 "Failed to connect to hardware: %s", e.what());
    return hardware_interface::CallbackReturn::ERROR;
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type RobotSystem::read(
  const rclcpp::Time & /*time*/,
  const rclcpp::Duration & /*period*/)
{
  // Read actual joint positions from hardware
  for (size_t i = 0; i < hw_positions_.size(); ++i) {
    hw_positions_[i] = serial_conn_->read_joint_position(i);
    hw_velocities_[i] = serial_conn_->read_joint_velocity(i);
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type RobotSystem::write(
  const rclcpp::Time & /*time*/,
  const rclcpp::Duration & /*period*/)
{
  // Send commands to hardware
  for (size_t i = 0; i < hw_position_commands_.size(); ++i) {
    serial_conn_->write_joint_command(i, hw_position_commands_[i]);
  }

  return hardware_interface::return_type::OK;
}

}  // namespace robot_hardware

// Export plugin
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  robot_hardware::RobotSystem,
  hardware_interface::SystemInterface)
```

### 3. URDF Configuration

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="robot">

  <!-- Regular URDF links and joints -->
  <link name="base_link">...</link>
  <joint name="joint1" type="revolute">...</joint>
  <joint name="joint2" type="revolute">...</joint>

  <!-- ros2_control system -->
  <ros2_control name="RobotSystem" type="system">
    <hardware>
      <plugin>robot_hardware/RobotSystem</plugin>
      <param name="port">/dev/ttyUSB0</param>
      <param name="baud_rate">115200</param>
    </hardware>
    
    <joint name="joint1">
      <command_interface name="position">
        <param name="min">-3.14</param>
        <param name="max">3.14</param>
      </command_interface>
      <command_interface name="velocity">
        <param name="min">-2.0</param>
        <param name="max">2.0</param>
      </command_interface>
      <state_interface name="position"/>
      <state_interface name="velocity"/>
    </joint>
    
    <joint name="joint2">
      <command_interface name="position"/>
      <state_interface name="position"/>
      <state_interface name="velocity"/>
    </joint>
  </ros2_control>

  <!-- Transmissions (for Gazebo simulation) -->
  <transmission name="joint1_trans">
    <type>transmission_interface/SimpleTransmission</type>
    <joint name="joint1">
      <hardwareInterface>hardware_interface/EffortJointInterface</hardwareInterface>
    </joint>
    <actuator name="joint1_motor">
      <mechanicalReduction>1</mechanicalReduction>
    </actuator>
  </transmission>

</robot>
```

### 4. Controller Configuration

```yaml
# config/controllers.yaml
controller_manager:
  ros__parameters:
    update_rate: 100  # Hz
    
    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster
    
    joint_trajectory_controller:
      type: joint_trajectory_controller/JointTrajectoryController
    
    forward_velocity_controller:
      type: velocity_controllers/JointGroupVelocityController
    
    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController

joint_trajectory_controller:
  ros__parameters:
    joints:
      - joint1
      - joint2
    command_interfaces:
      - position
    state_interfaces:
      - position
      - velocity
    gains:
      joint1: {p: 100.0, i: 0.0, d: 10.0}
      joint2: {p: 100.0, i: 0.0, d: 10.0}

diff_drive_controller:
  ros__parameters:
    left_wheel_names: ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]
    wheel_separation: 0.3
    wheel_radius: 0.05
    cmd_vel_timeout: 0.5
    publish_rate: 50.0
    base_frame_id: base_link
    odom_frame_id: odom
    enable_odom_tf: true
```

### 5. Controller Lifecycle Management

```python
# Launch file with controller loading
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit

def generate_launch_description():
    
    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}]
    )
    
    # Controller manager (hardware interface + controller manager)
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controller_config],
        output='screen'
    )
    
    # Spawn joint state broadcaster (always first)
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster',
                   '--controller-manager', '/controller_manager']
    )
    
    # Spawn trajectory controller
    trajectory_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_trajectory_controller',
                   '--controller-manager', '/controller_manager']
    )
    
    # Delay trajectory controller until joint state broadcaster is ready
    delay_trajectory = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[trajectory_controller_spawner]
        )
    )
    
    return LaunchDescription([
        robot_state_publisher,
        controller_manager,
        joint_state_broadcaster_spawner,
        delay_trajectory
    ])
```

## Common Patterns

### Pattern 1: Differential Drive Mobile Robot

```xml
<!-- URDF snippet -->
<ros2_control name="DiffDriveSystem" type="system">
  <hardware>
    <plugin>diff_drive_hardware/DiffDriveHardware</plugin>
    <param name="left_wheel_port">/dev/ttyUSB0</param>
    <param name="right_wheel_port">/dev/ttyUSB1</param>
  </hardware>
  
  <joint name="left_wheel_joint">
    <command_interface name="velocity"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
  
  <joint name="right_wheel_joint">
    <command_interface name="velocity"/>
    <state_interface name="position"/>
    <state_interface name="velocity"/>
  </joint>
</ros2_control>
```

```yaml
# Controller config
diff_drive_controller:
  ros__parameters:
    left_wheel_names: ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]
    wheel_separation: 0.3
    wheels_per_side: 1
    wheel_radius: 0.05
    
    # Odometry
    odom_frame_id: odom
    base_frame_id: base_link
    pose_covariance_diagonal: [0.001, 0.001, 0.001, 0.001, 0.001, 0.01]
    twist_covariance_diagonal: [0.001, 0.001, 0.001, 0.001, 0.001, 0.01]
    
    # TF
    enable_odom_tf: true
    
    # Limits
    linear.x.has_velocity_limits: true
    linear.x.max_velocity: 1.0
    linear.x.has_acceleration_limits: true
    linear.x.max_acceleration: 2.0
    
    angular.z.has_velocity_limits: true
    angular.z.max_velocity: 2.0
```

### Pattern 2: Joint Trajectory Controller with MoveIt2

```xml
<!-- URDF for manipulator -->
<ros2_control name="ArmSystem" type="system">
  <hardware>
    <plugin>mock_components/GenericSystem</plugin>
  </hardware>
  
  <joint name="shoulder_pan_joint">
    <command_interface name="position"/>
    <state_interface name="position"/>
  </joint>
  <!-- More joints... -->
</ros2_control>
```

```yaml
# Trajectory controller for MoveIt2
joint_trajectory_controller:
  ros__parameters:
    joints:
      - shoulder_pan_joint
      - shoulder_lift_joint
      - elbow_joint
      - wrist_1_joint
      - wrist_2_joint
      - wrist_3_joint
    
    command_interfaces:
      - position
    
    state_interfaces:
      - position
      - velocity
    
    gains:
      shoulder_pan_joint: {p: 100.0, i: 0.0, d: 10.0}
      shoulder_lift_joint: {p: 100.0, i: 0.0, d: 10.0}
      elbow_joint: {p: 100.0, i: 0.0, d: 10.0}
      wrist_1_joint: {p: 50.0, i: 0.0, d: 5.0}
      wrist_2_joint: {p: 50.0, i: 0.0, d: 5.0}
      wrist_3_joint: {p: 50.0, i: 0.0, d: 5.0}
    
    constraints:
      stopped_velocity_tolerance: 0.01
      goal_time: 0.5
```

## Anti-Patterns

### ❌ Not implementing lifecycle properly
Skipping on_configure/on_activate or not handling errors causes crashes.

**What happens:** Controller manager can't load hardware, cryptic errors, system unstable.

### ✅ Implement all lifecycle methods
```cpp
CallbackReturn on_configure(const rclcpp_lifecycle::State &) override {
  // Initialize hardware connection
  // Return ERROR if hardware not available
}

CallbackReturn on_activate(const rclcpp_lifecycle::State &) override {
  // Start control loops, enable motors
}

CallbackReturn on_deactivate(const rclcpp_lifecycle::State &) override {
  // Disable motors, stop control loops
}
```

### ❌ Ignoring command limits
Sending commands outside joint limits can damage hardware.

**What happens:** Mechanical damage, joint overrun, safety violations.

### ✅ Enforce limits in hardware interface
```cpp
hardware_interface::return_type write(const rclcpp::Time &, const rclcpp::Duration &) {
  for (size_t i = 0; i < joints_.size(); ++i) {
    // Clamp commands to limits
    cmd = std::clamp(commands_[i], joint_limits_[i].min, joint_limits_[i].max);
    hardware_->write(i, cmd);
  }
}
```

### ❌ Blocking in read/write
Blocking operations in read/write stall the control loop.

**What happens:** Jitter, missed deadlines, unstable control.

### ✅ Use async I/O or timeouts
```cpp
// Set serial timeout
serial_conn_->set_timeout(10ms);

// Non-blocking read with timeout
if (serial_conn_->read_available()) {
  data = serial_conn_->read();
}
```

## Configuration Reference

### Command Interfaces

| Type | Description | Use Case |
|------|-------------|----------|
| `position` | Target joint position | Position control |
| `velocity` | Target joint velocity | Velocity control |
| `effort` | Target joint effort/torque | Force control |
| `acceleration` | Target joint acceleration | Advanced control |

### Available Controllers

| Controller | Purpose |
|------------|---------|
| `joint_state_broadcaster` | Publish joint states to /joint_states |
| `joint_trajectory_controller` | Execute joint trajectories (MoveIt2) |
| `forward_position_controller` | Direct position command forwarding |
| `forward_velocity_controller` | Direct velocity command forwarding |
| `diff_drive_controller` | Mobile robot differential drive |
| `gripper_action_controller` | Parallel gripper control |

### CLI Commands

```bash
# List controllers
ros2 control list_controllers

# List hardware interfaces
ros2 control list_hardware_interfaces

# Load controller
ros2 control load_controller joint_trajectory_controller

# Configure controller
ros2 control set_controller_state joint_trajectory_controller configure

# Activate controller
ros2 control switch_controllers --activate joint_trajectory_controller

# Deactivate
ros2 control switch_controllers --deactivate joint_trajectory_controller

# View controller state
ros2 control view_controller_state
```

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Controller fails to load | Plugin not found | Check CMakeLists.txt exports, source workspace |
| Hardware interface error | Port not accessible | Check permissions, dialout group |
| Joint not responding | Wrong command interface | Verify URDF command_interface matches controller |
| No /joint_states | Broadcaster not loaded | Start joint_state_broadcaster |
| MoveIt2 fails | Trajectory controller not active | Check controller state, activate manually |
| High latency | Control loop rate too low | Increase update_rate in controller_manager |

## Workflow Integration

- **Before this:** Use `robot-modeling` to create URDF with joints and transmissions
- **After this:** Use `moveit2` for motion planning with trajectory controller
- **Parallel with:** Use `nav2` which uses diff_drive_controller for mobile bases
- **For real-time:** Review `realtime-motor-control` for PREEMPT_RT setup

## Further Reading

- [ros2_control Documentation](https://control.ros.org/)
- [Writing a Hardware Interface](https://control.ros.org/master/doc/ros2_control/hardware_interface/doc/writing_new_hardware_interface.html)
- [Available Controllers](https://control.ros.org/master/doc/ros2_controllers/doc/controllers_index.html)
- Related skills: `robot-modeling`, `moveit2`, `realtime-motor-control`, `nav2`

## Changelog

### v1.0.0 (2026-03-07)
- Initial release
- Covers hardware interfaces, controllers, transmissions, lifecycle