---
name: robot-modeling
description: Robot description using URDF and Xacro including kinematics, inertials, transmissions, and TF2 coordinate frame management. Use when creating robot models, defining joint structures, or managing coordinate transformations.
category: middleware
tags: [urdf, xacro, tf2, kinematics, robot-description]
version: "1.0.0"
---

# Robot Modeling

Robot modeling is the foundation of robotics software. Before any robot moves, it must be described—its links, joints, mass properties, and coordinate frames. This skill covers URDF/Xacro for robot description and TF2 for coordinate frame management.

## When to Use

- Creating URDF/Xacro robot descriptions
- Defining joint types, limits, and dynamics
- Specifying mass, inertia, and collision geometry
- Setting up coordinate frame hierarchies with TF2
- Configuring robot_state_publisher
- Debugging TF tree issues or frame mismatches
- Converting from CAD to URDF
- Creating simplified collision meshes

## Quick Start

```bash
# Create a minimal URDF
cat > robot.urdf << 'EOF'
<?xml version="1.0"?>
<robot name="my_robot">
  <link name="base_link">
    <visual>
      <geometry><box size="0.5 0.3 0.1"/></geometry>
    </visual>
    <collision>
      <geometry><box size="0.5 0.3 0.1"/></geometry>
    </collision>
    <inertial>
      <mass value="10"/>
      <inertia ixx="0.1" ixy="0" ixz="0" iyy="0.1" iyz="0" izz="0.1"/>
    </inertial>
  </link>
</robot>
EOF

# View in RViz
ros2 run robot_state_publisher robot_state_publisher robot.urdf
ros2 run rviz2 rviz2
```

## Core Concepts

### 1. URDF Structure

URDF (Unified Robot Description Format) is an XML format describing robot kinematics and dynamics.

```xml
<?xml version="1.0"?>
<robot name="manipulator">
  
  <!-- Base link -->
  <link name="base_link">
    <visual>
      <origin xyz="0 0 0.05" rpy="0 0 0"/>
      <geometry>
        <box size="0.4 0.4 0.1"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
    <collision>
      <origin xyz="0 0 0.05" rpy="0 0 0"/>
      <geometry>
        <box size="0.4 0.4 0.1"/>
      </geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 0.05" rpy="0 0 0"/>
      <mass value="10.0"/>
      <inertia ixx="0.084" ixy="0" ixz="0" 
               iyy="0.084" iyz="0" 
               izz="0.134"/>
    </inertial>
  </link>

  <!-- Joint connecting base to link1 -->
  <joint name="joint1" type="revolute">
    <parent link="base_link"/>
    <child link="link1"/>
    <origin xyz="0 0 0.1" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="100" velocity="2.0"/>
    <dynamics damping="1.0" friction="0.1"/>
  </joint>

  <!-- Link 1 -->
  <link name="link1">
    <visual>
      <origin xyz="0 0 0.25" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="0.05" length="0.5"/>
      </geometry>
    </visual>
    <collision>
      <origin xyz="0 0 0.25" rpy="0 0 0"/>
      <geometry>
        <cylinder radius="0.05" length="0.5"/>
      </geometry>
    </collision>
    <inertial>
      <origin xyz="0 0 0.25" rpy="0 0 0"/>
      <mass value="5.0"/>
      <inertia ixx="0.105" ixy="0" ixz="0"
               iyy="0.105" iyz="0"
               izz="0.00625"/>
    </inertial>
  </link>

</robot>
```

### 2. Joint Types

| Type | Description | Use Case |
|------|-------------|----------|
| `revolute` | Rotates around axis with limits | Robot arm joints |
| `continuous` | Rotates without limits | Wheels, continuous rotation |
| `prismatic` | Translates along axis with limits | Linear actuators |
| `fixed` | No motion, rigid connection | Sensor mounts, static links |
| `floating` | 6 DOF (x,y,z,roll,pitch,yaw) | Mobile base, humanoid torso |
| `planar` | 3 DOF (x,y,yaw) | Mobile robot on flat ground |

### 3. Xacro for Modularity

Xacro (XML Macros) enables reusable, parameterized robot descriptions.

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="robot">

  <!-- Property definitions -->
  <xacro:property name="pi" value="3.14159"/>
  <xacro:property name="base_length" value="0.5"/>
  <xacro:property name="base_width" value="0.3"/>
  
  <!-- Macro for a simple link -->
  <xacro:macro name="simple_link" params="name length radius mass">
    <link name="${name}">
      <visual>
        <geometry>
          <cylinder radius="${radius}" length="${length}"/>
        </geometry>
      </visual>
      <collision>
        <geometry>
          <cylinder radius="${radius}" length="${length}"/>
        </geometry>
      </collision>
      <inertial>
        <mass value="${mass}"/>
        <inertia ixx="${mass*length*length/12}" ixy="0" ixz="0"
                 iyy="${mass*length*length/12}" iyz="0"
                 izz="${mass*radius*radius/2}"/>
      </inertial>
    </link>
  </xacro:macro>

  <!-- Use the macro -->
  <xacro:simple_link name="link1" length="0.5" radius="0.05" mass="2.0"/>
  <xacro:simple_link name="link2" length="0.4" radius="0.04" mass="1.5"/>

  <!-- Include external xacro -->
  <xacro:include filename="$(find my_pkg)/urdf/gripper.xacro"/>
  <xacro:gripper prefix="left_"/>
  <xacro:gripper prefix="right_"/>

</robot>
```

**Process Xacro to URDF:**
```bash
xacro robot.xacro > robot.urdf
xacro robot.xacro robot_name:=my_robot > robot.urdf
```

### 4. Inertia Calculation

Correct inertia is critical for simulation accuracy and controller stability.

**For common shapes:**
```xml
<!-- Box: mass m, dimensions a x b x c -->
<inertia ixx="${m*(b*b+c*c)/12}" ixy="0" ixz="0"
         iyy="${m*(a*a+c*c)/12}" iyz="0"
         izz="${m*(a*a+b*b)/12}"/>

<!-- Cylinder: mass m, radius r, length h -->
<inertia ixx="${m*(3*r*r+h*h)/12}" ixy="0" ixz="0"
         iyy="${m*(3*r*r+h*h)/12}" iyz="0"
         izz="${m*r*r/2}"/>

<!-- Sphere: mass m, radius r -->
<inertia ixx="${2*m*r*r/5}" ixy="0" ixz="0"
         iyy="${2*m*r*r/5}" iyz="0"
         izz="${2*m*r*r/5}"/>
```

**Using mesh inertia (approximate):**
```python
import trimesh

mesh = trimesh.load('link.stl')
mass = 1.0  # kg
mesh.density = mass / mesh.volume

inertia = mesh.moment_inertia
# Convert to URDF format
```

### 5. TF2 Coordinate Frames

TF2 manages coordinate frame transformations over time.

**Static transforms (fixed relationships):**
```python
from tf2_ros import StaticTransformBroadcaster
from geometry_msgs.msg import TransformStamped
import tf_transformations

class TFPublisher(Node):
    def __init__(self):
        super().__init__('tf_publisher')
        self.static_broadcaster = StaticTransformBroadcaster(self)
        
        # Camera mount (fixed relative to base)
        static_transform = TransformStamped()
        static_transform.header.stamp = self.get_clock().now().to_msg()
        static_transform.header.frame_id = 'base_link'
        static_transform.child_frame_id = 'camera_link'
        static_transform.transform.translation.x = 0.25
        static_transform.transform.translation.y = 0.0
        static_transform.transform.translation.z = 0.15
        
        quat = tf_transformations.quaternion_from_euler(0, 0.1, 0)
        static_transform.transform.rotation.x = quat[0]
        static_transform.transform.rotation.y = quat[1]
        static_transform.transform.rotation.z = quat[2]
        static_transform.transform.rotation.w = quat[3]
        
        self.static_broadcaster.sendTransform(static_transform)
```

**Dynamic transforms (changing over time):**
```python
from tf2_ros import TransformBroadcaster
from nav_msgs.msg import Odometry

class OdomPublisher(Node):
    def __init__(self):
        super().__init__('odom_publisher')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_sub = self.create_subscription(
            Odometry, 'odom', self.odom_callback, 10)

    def odom_callback(self, msg):
        transform = TransformStamped()
        transform.header = msg.header
        transform.child_frame_id = msg.child_frame_id
        transform.transform.translation.x = msg.pose.pose.position.x
        transform.transform.translation.y = msg.pose.pose.position.y
        transform.transform.translation.z = 0.0
        transform.transform.rotation = msg.pose.pose.orientation
        
        self.tf_broadcaster.sendTransform(transform)
```

**Looking up transforms:**
```python
from tf2_ros import Buffer, TransformListener

class TFListener(Node):
    def __init__(self):
        super().__init__('tf_listener')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def get_transform(self):
        try:
            transform = self.tf_buffer.lookup_transform(
                'base_link',      # target frame
                'camera_link',    # source frame
                rclpy.time.Time(), # latest available
                timeout=rclpy.duration.Duration(seconds=1.0)
            )
            return transform
        except Exception as e:
            self.get_logger().warn(f'TF lookup failed: {e}')
            return None

    def transform_pose(self, pose_stamped, target_frame):
        """Transform a pose to a different frame."""
        try:
            transform = self.tf_buffer.lookup_transform(
                target_frame,
                pose_stamped.header.frame_id,
                pose_stamped.header.stamp,
                timeout=rclpy.duration.Duration(seconds=1.0)
            )
            from tf2_geometry_msgs import do_transform_pose
            return do_transform_pose(pose_stamped, transform)
        except Exception as e:
            self.get_logger().warn(f'Transform failed: {e}')
            return None
```

## Common Patterns

### Pattern 1: Mobile Robot with Wheels

```xml
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="mobile_robot">

  <!-- Base -->
  <link name="base_link">
    <visual>
      <geometry><box size="0.5 0.3 0.1"/></geometry>
    </visual>
    <collision>
      <geometry><box size="0.5 0.3 0.1"/></geometry>
    </collision>
    <inertial>
      <mass value="10"/>
      <inertia ixx="0.1" ixy="0" ixz="0" iyy="0.1" iyz="0" izz="0.1"/>
    </inertial>
  </link>

  <!-- Wheel macro -->
  <xacro:macro name="wheel" params="side reflect">
    <link name="${side}_wheel">
      <visual>
        <geometry><cylinder radius="0.05" length="0.03"/></geometry>
      </visual>
      <collision>
        <geometry><cylinder radius="0.05" length="0.03"/></geometry>
      </collision>
      <inertial>
        <mass value="0.5"/>
        <inertia ixx="0.0003" ixy="0" ixz="0" 
                 iyy="0.0003" iyz="0" 
                 izz="0.0006"/>
      </inertial>
    </link>
    
    <joint name="${side}_wheel_joint" type="continuous">
      <parent link="base_link"/>
      <child link="${side}_wheel"/>
      <origin xyz="0 ${reflect*0.15} 0" rpy="${pi/2} 0 0"/>
      <axis xyz="0 0 1"/>
    </joint>
  </xacro:macro>

  <xacro:wheel side="left" reflect="1"/>
  <xacro:wheel side="right" reflect="-1"/>

  <!-- Caster wheel -->
  <link name="caster">
    <visual>
      <geometry><sphere radius="0.025"/></geometry>
    </visual>
  </link>
  
  <joint name="caster_joint" type="fixed">
    <parent link="base_link"/>
    <child link="caster"/>
    <origin xyz="-0.15 0 -0.025"/>
  </joint>

</robot>
```

### Pattern 2: Robot with Gazebo Plugins

```xml
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="robot">

  <!-- ... links and joints ... -->

  <!-- Gazebo differential drive plugin -->
  <gazebo>
    <plugin filename="libgazebo_ros_diff_drive.so" name="diff_drive">
      <ros>
        <namespace>/robot</namespace>
      </ros>
      <update_rate>50</update_rate>
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>0.3</wheel_separation>
      <wheel_diameter>0.1</wheel_diameter>
      <max_wheel_torque>20</max_wheel_torque>
      <max_wheel_acceleration>1.0</max_wheel_acceleration>
      <publish_odom>true</publish_odom>
      <publish_odom_tf>true</publish_odom_tf>
      <odometry_frame>odom</odometry_frame>
      <robot_base_frame>base_link</robot_base_frame>
    </plugin>
  </gazebo>

  <!-- Camera sensor -->
  <link name="camera_link">
    <visual>
      <geometry><box size="0.05 0.05 0.05"/></geometry>
    </visual>
  </link>
  
  <joint name="camera_joint" type="fixed">
    <parent link="base_link"/>
    <child link="camera_link"/>
    <origin xyz="0.2 0 0.1"/>
  </joint>

  <gazebo reference="camera_link">
    <sensor name="camera" type="camera">
      <camera>
        <horizontal_fov>1.047</horizontal_fov>
        <image>
          <width>640</width>
          <height>480</height>
        </image>
      </camera>
      <plugin filename="libgazebo_ros_camera.so" name="camera_plugin">
        <frame_name>camera_link</frame_name>
      </plugin>
    </sensor>
  </gazebo>

</robot>
```

### Pattern 3: Robot State Publisher Setup

```python
# launch/robot_state_publisher.launch.py
from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    
    # Process Xacro
    robot_description = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        PathJoinSubstitution([
            FindPackageShare('my_robot_pkg'),
            'urdf',
            'robot.xacro'
        ]),
    ])

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': False,
                'publish_frequency': 50.0,
                'frame_prefix': '',  # Use for multi-robot: 'robot1/'
            }]
        ),
    ])
```

## Anti-Patterns

### ❌ Incorrect inertia origin
Placing inertia origin at link visual center instead of COM causes unstable simulation.

**What happens:** Robot oscillates, falls over, or explodes in simulation.

### ✅ Place inertia at center of mass
```xml
<link name="link1">
  <visual>
    <!-- Visual at origin -->
    <geometry><cylinder radius="0.05" length="0.5"/></geometry>
  </visual>
  <inertial>
    <!-- Inertia at COM (center of cylinder) -->
    <origin xyz="0 0 0.25" rpy="0 0 0"/>
    <mass value="2.0"/>
    <inertia .../>
  </inertial>
</link>
```

### ❌ Missing collision geometry
Using detailed meshes for collision causes slow simulation and contact instability.

**What happens:** Gazebo runs at 0.1x real-time, robots jitter on contact.

### ✅ Use simplified collision shapes
```xml
<collision>
  <!-- Approximate complex shape with primitives -->
  <geometry>
    <box size="0.1 0.1 0.2"/>
  </geometry>
</collision>
```

### ❌ Cyclic TF tree
Creating a loop in the transform tree breaks TF lookups.

**What happens:** `tf2` throws `ConnectivityException`, nodes can't transform poses.

### ✅ Maintain tree structure
```
base_link → link1 → link2 → end_effector
         ↘ camera_link
         ↘ laser_link
```
No cycles, single parent per frame.

## Configuration Reference

### Joint Limit Parameters

| Parameter | Unit | Description |
|-----------|------|-------------|
| `lower` | rad or m | Minimum joint position |
| `upper` | rad or m | Maximum joint position |
| `effort` | N or N·m | Maximum joint effort |
| `velocity` | rad/s or m/s | Maximum joint velocity |

### Inertia Tensor

```
I = [ ixx  ixy  ixz ]
    [ ixy  iyy  iyz ]
    [ ixz  iyz  izz ]

Must be symmetric positive definite.
```

### TF2 Frame Conventions

| Frame | Convention |
|-------|------------|
| `base_link` | Robot centroid, z up |
| `odom` | Odometry origin, z up |
| `map` | Global map origin |
| `tool0`, `ee_link` | End-effector tip |
| `camera_link` | Optical center |
| `laser`, `lidar_link` | Scan origin |

**ROS REP-105:** `map` → `odom` → `base_link` → `{sensors, limbs}`

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Robot drifts in Gazebo | Incorrect inertia | Recalculate inertia at COM |
| Joints oscillate | High gains + low damping | Add `<dynamics damping="1.0"/>` |
| TF tree broken | Cyclic or missing transforms | Check `ros2 run tf2_tools view_frames` |
| Robot explodes on spawn | Massive mass ratio | Keep link masses within 100x |
| Visual/collision mismatch | Different origins | Align `<origin>` tags |
| Controller fails | Joint limits too tight | Widen limits or reduce effort |
| Robot slides on ground | No friction | Add `<mu>` to ground plane |
| Camera image black | Missing optical frame | Add `camera_optical_frame` with RPY rotation |

## Workflow Integration

- **Before this:** Define robot mechanical design and joint specifications
- **After this:** Use `ros2` for node development, `ros2-control` for controllers
- **Parallel with:** Use `gazebo` for simulation testing
- **Before deployment:** Validate collision geometry with `safety-systems`

## Further Reading

- [URDF Specification](http://wiki.ros.org/urdf/XML)
- [Xacro Tutorial](http://wiki.ros.org/xacro)
- [TF2 Documentation](http://wiki.ros.org/tf2)
- [ROS REP-103](https://www.ros.org/reps/rep-0103.html) - Standard Units and Coordinate Conventions
- [ROS REP-105](https://www.ros.org/reps/rep-0105.html) - Coordinate Frames for Mobile Platforms

## Changelog

### v1.0.0 (2026-03-07)
- Initial release
- Covers URDF, Xacro, TF2, robot_state_publisher