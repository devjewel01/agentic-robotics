---
name: ros2
description: ROS2 development including nodes, topics, services, actions, launch files, DDS, QoS, lifecycle nodes, and debugging. Use when building ROS2 packages or configuring robot software stacks.
category: middleware
tags: [ros2, robotics, middleware, dds, colcon, launch]
version: "1.0.0"
---

# ROS2

ROS2 is the de facto standard middleware for robotics. This skill covers the complete development workflow from workspace setup to production deployment.

## When to Use

- Building ROS2 packages, nodes, or component containers
- Setting up colcon workspaces, ament_cmake, or ament_python packages
- Writing CMakeLists.txt, package.xml, or setup.py for ROS2
- Defining custom messages, services, or actions
- Configuring DDS middleware and QoS profiles
- Implementing lifecycle (managed) nodes for production
- Debugging DDS discovery, QoS mismatches, or build failures
- Working with Nav2, MoveIt2, or other ROS2 frameworks
- Deploying ROS2 to production or embedded systems (micro-ROS)

## Quick Start

```bash
# Install ROS2 (Ubuntu 22.04 / ROS2 Humble)
sudo apt update && sudo apt install curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install ros-humble-desktop ros-dev-tools

# Source ROS2
source /opt/ros/humble/setup.bash

# Create workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws

# Create package
cd src
ros2 pkg create --build-type ament_python my_pkg --dependencies rclpy std_msgs

# Build
cd ~/ros2_ws
colcon build --packages-select my_pkg

# Source workspace
source install/setup.bash

# Run
ros2 run my_pkg my_node
```

## Core Concepts

### 1. Node Architecture

A ROS2 node is the fundamental unit of computation. Each node should have a single responsibility.

**Python Node (rclpy):**
```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String

class MinimalNode(Node):
    def __init__(self):
        super().__init__('minimal_node')
        
        # Declare parameters with validation
        self.declare_parameter('rate_hz', 10.0)
        self.declare_parameter('message', 'Hello ROS2')
        
        # Get parameters
        rate_hz = self.get_parameter('rate_hz').value
        self.message = self.get_parameter('message').value
        
        # Setup QoS
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Create publisher and subscriber
        self.pub = self.create_publisher(String, 'chatter', qos)
        self.sub = self.create_subscription(
            String, 'chatter', self.chatter_callback, qos)
        
        # Create timer
        self.timer = self.create_timer(1.0 / rate_hz, self.timer_callback)
        
        self.get_logger().info(f'Node started, publishing at {rate_hz}Hz')

    def timer_callback(self):
        msg = String()
        msg.data = self.message
        self.pub.publish(msg)
        self.get_logger().debug(f'Published: {msg.data}')

    def chatter_callback(self, msg):
        self.get_logger().info(f'Received: {msg.data}')

def main(args=None):
    rclpy.init(args=args)
    node = MinimalNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**C++ Node (rclcpp):**
```cpp
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

class MinimalNode : public rclcpp::Node {
public:
    MinimalNode() : Node("minimal_node") {
        // Declare parameters
        this->declare_parameter("rate_hz", 10.0);
        this->declare_parameter("message", "Hello ROS2");
        
        double rate_hz = this->get_parameter("rate_hz").as_double();
        message_ = this->get_parameter("message").as_string();
        
        // Setup QoS
        auto qos = rclcpp::QoS(10).reliable();
        
        // Create publisher and subscription
        pub_ = this->create_publisher<std_msgs::msg::String>("chatter", qos);
        sub_ = this->create_subscription<std_msgs::msg::String>(
            "chatter", qos,
            std::bind(&MinimalNode::chatterCallback, this, std::placeholders::_1));
        
        // Create timer
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(static_cast<int>(1000.0 / rate_hz)),
            std::bind(&MinimalNode::timerCallback, this));
        
        RCLCPP_INFO(this->get_logger(), "Node started, publishing at %.1fHz", rate_hz);
    }

private:
    void timerCallback() {
        auto msg = std_msgs::msg::String();
        msg.data = message_;
        pub_->publish(msg);
    }
    
    void chatterCallback(const std_msgs::msg::String::SharedPtr msg) {
        RCLCPP_INFO(this->get_logger(), "Received: %s", msg.data.c_str());
    }
    
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_;
    rclcpp::TimerBase::SharedPtr timer_;
    std::string message_;
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MinimalNode>());
    rclcpp::shutdown();
    return 0;
}
```

### 2. QoS (Quality of Service)

QoS mismatches are the #1 source of silent failures in ROS2.

**Compatibility Matrix:**
| Publisher | Subscriber | Result |
|-----------|------------|--------|
| RELIABLE | RELIABLE | ✅ Works |
| RELIABLE | BEST_EFFORT | ✅ Works |
| BEST_EFFORT | BEST_EFFORT | ✅ Works |
| BEST_EFFORT | RELIABLE | ❌ Silent failure |

**Standard QoS Profiles:**
```python
from rclpy.qos import (
    QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy,
    QoSDurabilityPolicy
)

# Sensor data (cameras, LiDAR) - tolerate drops, want latest
SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
    durability=QoSDurabilityPolicy.VOLATILE
)

# Commands (velocity, joint) - never miss
COMMAND_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10,
    durability=QoSDurabilityPolicy.VOLATILE
)

# Map/static data - late joiners get it
MAP_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL  # Latching
)

# State/parameters
STATE_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10
)
```

### 3. Lifecycle Nodes

Use lifecycle nodes for production systems requiring deterministic startup/shutdown.

**State Machine:** `Unconfigured → Inactive → Active → Finalized`

```python
from rclpy.lifecycle import Node as LifecycleNode
from rclpy.lifecycle import State, TransitionCallbackReturn

class ManagedNode(LifecycleNode):
    def __init__(self):
        super().__init__('managed_node')
        self.get_logger().info('Created (unconfigured)')

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        """Allocate resources, setup pubs/subs (don't activate yet)"""
        try:
            self.declare_parameter('model_path', '')
            self.model = load_model(self.get_parameter('model_path').value)
            
            self.pub = self.create_lifecycle_publisher(
                DetectionArray, 'detections', 10)
            
            self.get_logger().info('Configured')
            return TransitionCallbackReturn.SUCCESS
        except Exception as e:
            self.get_logger().error(f'Config failed: {e}')
            return TransitionCallbackReturn.FAILURE

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        """Start processing - subscriptions go live here"""
        self.sub = self.create_subscription(
            Image, 'camera/image', self.image_callback, 1)
        self.get_logger().info('Activated')
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        """Pause processing - safe to reconfigure after this"""
        self.destroy_subscription(self.sub)
        self.get_logger().info('Deactivated')
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        """Release resources, return to unconfigured"""
        del self.model
        self.get_logger().info('Cleaned up')
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        """Final cleanup before destruction"""
        self.get_logger().info('Shutting down')
        return TransitionCallbackReturn.SUCCESS

    def on_error(self, state: State) -> TransitionCallbackReturn:
        """Handle errors - recover or fail gracefully"""
        self.get_logger().error(f'Error in state {state.label}')
        return TransitionCallbackReturn.SUCCESS
```

### 4. Launch Files

ROS2 uses Python for launch files, enabling powerful conditional logic.

```python
# launch/robot.launch.py
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription,
    GroupAction, OpaqueFunction
)
from launch.conditions import IfCondition
from launch.substitutions import (
    LaunchConfiguration, PathJoinSubstitution
)
from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='false')
    robot_name_arg = DeclareLaunchArgument(
        'robot_name', default_value='robot')
    
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    
    # Load params from YAML
    config_file = PathJoinSubstitution([
        FindPackageShare('my_pkg'), 'config', 'robot.yaml'
    ])
    
    # Standard node
    perception_node = Node(
        package='my_pkg',
        executable='perception_node',
        name='perception',
        namespace=robot_name,
        parameters=[config_file, {'use_sim_time': use_sim_time}],
        remappings=[
            ('camera/image', 'realsense/color/image_raw'),
            ('detections', 'perception/detections'),
        ],
        output='screen'
    )
    
    # Composable nodes (zero-copy, same process)
    container = ComposableNodeContainer(
        name='perception_container',
        namespace=robot_name,
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=[
            ComposableNode(
                package='my_pkg',
                plugin='my_pkg::PerceptionComponent',
                name='perception',
                parameters=[config_file],
            ),
            ComposableNode(
                package='my_pkg',
                plugin='my_pkg::TrackerComponent',
                name='tracker',
            ),
        ],
        output='screen'
    )
    
    return LaunchDescription([
        use_sim_time_arg,
        robot_name_arg,
        perception_node,
        container,
    ])
```

## Common Patterns

### Pattern 1: Component Composition

Zero-copy intra-process communication for high-performance pipelines.

```cpp
// src/perception_component.cpp
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_components/register_node_macro.hpp>
#include <sensor_msgs/msg/image.hpp>

namespace my_pkg {

class PerceptionComponent : public rclcpp::Node {
public:
    explicit PerceptionComponent(const rclcpp::NodeOptions& options)
        : Node("perception", options)
    {
        // Enable intra-process for zero-copy
        auto sub_options = rclcpp::SubscriptionOptions();
        sub_options.use_intra_process_comm = 
            rclcpp::IntraProcessSetting::Enable;
        
        sub_ = this->create_subscription<sensor_msgs::msg::Image>(
            "camera/image",
            rclcpp::SensorDataQoS(),
            std::bind(&PerceptionComponent::callback, this, 
                      std::placeholders::_1),
            sub_options);
        
        pub_ = this->create_publisher<DetectionArray>(
            "detections", 10);
    }

private:
    void callback(sensor_msgs::msg::Image::UniquePtr msg) {
        // UniquePtr = zero-copy when using intra-process
        auto detections = process(std::move(msg));
        pub_->publish(std::move(detections));
    }
    
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_;
    rclcpp::Publisher<DetectionArray>::SharedPtr pub_;
};

}  // namespace my_pkg

RCLCPP_COMPONENTS_REGISTER_NODE(my_pkg::PerceptionComponent)
```

### Pattern 2: Actions for Long-Running Tasks

```python
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from my_interfaces.action import Navigate

class NavigationServer(Node):
    def __init__(self):
        super().__init__('navigation_server')
        self._action_server = ActionServer(
            self, Navigate, 'navigate',
            execute_callback=self.execute_cb,
            goal_callback=self.goal_cb,
            cancel_callback=self.cancel_cb,
        )

    def goal_cb(self, goal_request):
        self.get_logger().info(f'Goal: {goal_request.target_pose}')
        return GoalResponse.ACCEPT

    def cancel_cb(self, goal_handle):
        return CancelResponse.ACCEPT

    async def execute_cb(self, goal_handle):
        feedback = Navigate.Feedback()
        
        for i, waypoint in enumerate(self.plan(goal_handle.request)):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                return Navigate.Result(success=False)
            
            # Execute waypoint
            self.move_to(waypoint)
            feedback.progress = float(i) / len(self.waypoints)
            goal_handle.publish_feedback(feedback)
        
        goal_handle.succeed()
        return Navigate.Result(success=True)
```

### Pattern 3: Custom Messages

```
# msg/Detection.msg
std_msgs/Header header
string class_name
float32 confidence
geometry_msgs/Pose pose
float32[4] bbox  # [x_min, y_min, x_max, y_max]
```

```
# srv/GetPose.srv
string object_name
---
bool success
geometry_msgs/PoseStamped pose
string error_message
```

```
# action/PickPlace.action
# Goal
geometry_msgs/Pose target_pose
string object_class
---
# Result
bool success
string error_message
---
# Feedback
float32 progress
string current_phase
```

**CMakeLists.txt for custom messages:**
```cmake
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Detection.msg"
  "srv/GetPose.srv"
  "action/PickPlace.action"
  DEPENDENCIES geometry_msgs std_msgs
)
```

### Pattern 4: Runtime parameter updates (parameter callback)

Use `add_on_set_parameters_callback` to react to dynamic reconfigure–style updates without restarting the node.

```python
from rcl_interfaces.msg import SetParametersResult
from rclpy.parameter import Parameter

def __init__(self):
    super().__init__('my_node')
    self.declare_parameter('confidence_threshold', 0.7)
    self.threshold = self.get_parameter('confidence_threshold').value
    self.add_on_set_parameters_callback(self._param_callback)

def _param_callback(self, params):
    for p in params:
        if p.name == 'confidence_threshold':
            self.threshold = p.value
            self.get_logger().info(f'Threshold updated to {p.value}')
    return SetParametersResult(successful=True)
```

For parameter descriptors (ranges, descriptions) use `declare_parameter` with `ParameterDescriptor` and optional `FloatingPointRange` / `IntegerRange` so tools and UIs can show constraints.

## Anti-Patterns

### ❌ Creating publishers/subscribers in callbacks
Creating a new publisher inside a timer callback causes DDS discovery overhead and memory leaks.

**What happens:** Node slows down over time, DDS discovery traffic floods network, memory usage grows.

### ✅ Create once, reuse
```python
def __init__(self):
    # Create publishers in __init__
    self.pub = self.create_publisher(String, 'topic', 10)
    
    # Reuse in callback
    self.timer = self.create_timer(1.0, self.callback)

def callback(self):
    # Just publish, don't create new publisher
    self.pub.publish(msg)
```

### ❌ Ignoring QoS compatibility
Using mismatched reliability settings causes silent topic failures.

**What happens:** Subscriber shows 0 messages received despite publisher running. No error messages.

### ✅ Explicit QoS with verification
```python
# Both sides use same QoS profile
qos = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=10
)

# Verify with: ros2 topic info /my_topic -v
```

### ❌ Blocking the executor
Running heavy computation in callbacks blocks all other callbacks.

**What happens:** Timer jitter increases, message processing delays, robot becomes unresponsive.

### ✅ Use executors and callbacks properly
```python
# Multi-threaded executor for CPU-heavy work
from rclpy.executors import MultiThreadedExecutor

def main():
    rclpy.init()
    node = MyNode()
    
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
```

### ❌ Not using use_sim_time consistently
Mixing simulated and wall-clock time causes TF lookup failures and synchronization issues.

**What happens:** TF extrapolation errors, sensor data misalignment, navigation failures.

### ✅ Set use_sim_time globally
```python
# In launch file
from launch.actions import SetParameter

def generate_launch_description():
    return LaunchDescription([
        SetParameter(name='use_sim_time', value=True),
        # All nodes inherit this
        Node(...),
        Node(...),
    ])
```

## Configuration Reference

### package.xml

```xml
<?xml version="1.0"?>
<package format="3">
  <name>my_robot_pkg</name>
  <version>0.1.0</version>
  <description>My robot package</description>
  <maintainer email="dev@example.com">Dev Name</maintainer>
  <license>Apache-2.0</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <!-- For pure Python: <buildtool_depend>ament_python</buildtool_depend> -->

  <depend>rclcpp</depend>
  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  <depend>sensor_msgs</depend>
  <depend>geometry_msgs</depend>
  <depend>tf2_ros</depend>

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_cmake_pytest</test_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

### colcon Build Options

| Flag | Description |
|------|-------------|
| `--packages-select pkg` | Build only specific package |
| `--packages-up-to pkg` | Build package + dependencies |
| `--symlink-install` | Symlink Python files (edit without rebuild) |
| `--cmake-args -DCMAKE_BUILD_TYPE=Release` | Release build |
| `--parallel-workers 4` | Limit parallel jobs (RAM constrained) |
| `--event-handlers console_direct+` | Show build output in real-time |

### DDS Configuration

```bash
# Set DDS implementation
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp  # Recommended

# Limit to localhost
export ROS_LOCALHOST_ONLY=1

# Isolate robot groups
export ROS_DOMAIN_ID=42  # Range 0-101

# CycloneDDS config file
export CYCLONEDDS_URI=file:///path/to/cyclonedds.xml
```

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Topics not connecting | QoS mismatch | Check `ros2 topic info /topic -v` for reliability settings |
| Build fails "package not found" | Missing dependency | Run `rosdep install --from-paths src --ignore-src -y` |
| Python changes not reflected | Not using symlink install | Use `colcon build --symlink-install` |
| High CPU usage | Spinning without sleep | Use `create_timer()` not `while True` loops |
| Memory leak | Creating publishers in callbacks | Create publishers in `__init__`, reuse in callbacks |
| TF lookup fails | Missing use_sim_time | Set `use_sim_time` parameter consistently |
| Custom message not found | Not sourced after build | Run `source install/setup.bash` |
| Action server not responding | Goal not accepted | Check `goal_callback` returns `GoalResponse.ACCEPT` |
| Parameter not declared | Using `get_parameter` without `declare_parameter` | Always declare before getting |
| Launch file fails | Syntax error in Python launch | Check with `python3 -m py_compile launch/file.py` |

## Workflow Integration

- **Before this:** Use `robot-modeling` to create URDF/Xacro robot description
- **After this:** Use `ros2-control` for hardware interfaces and controllers
- **Parallel with:** Use `camera-vision` or `sensor-fusion-slam` for perception nodes
- **Before deployment:** Review `safety-systems` for production hardening

## Further Reading

- [ROS2 Documentation](https://docs.ros.org/en/humble/)
- [ros2/design](https://design.ros2.org/) - Architecture articles
- Related skills: `ros2-control`, `nav2`, `robot-modeling`, `safety-systems`

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering ROS2 Humble
- Includes rclpy, rclcpp, QoS, lifecycle nodes, launch files, components