---
name: gazebo
description: Gazebo Classic and Gazebo Sim (Ignition) simulation including SDF worlds, physics configuration, sensor models, ROS2 integration, and custom plugins. Use when setting up simulation environments, testing robot behavior, or generating synthetic data.
category: simulation
tags: [gazebo, simulation, sdf, physics, sensors, ros2]
version: "1.0.0"
---

# Gazebo Simulation

Gazebo is the standard open-source robot simulator. This skill covers both Gazebo Classic (11) and Gazebo Sim (Ignition/Harmonic/Ionic) for creating simulation environments, configuring physics, and integrating with ROS2.

## When to Use

- Creating SDF world files with terrain and environments
- Configuring physics engines (ODE, Bullet, DART)
- Setting up sensor models (camera, LiDAR, IMU, depth)
- Integrating ROS2 with Gazebo via bridges
- Testing robot behavior in simulation before hardware
- Generating synthetic training data for ML
- Debugging physics or sensor issues
- Creating custom Gazebo plugins

## Quick Start

```bash
# Install Gazebo Sim (Harmonic) with ROS2
sudo apt install ros-humble-ros-gz

# Launch empty world
ros2 launch ros_gz_sim gz_sim.launch.py

# Launch with robot
ros2 launch ros_gz_sim gz_sim.launch.py gz_args:="-r warehouse.sdf"

# Spawn robot from URDF
ros2 run ros_gz_sim create -topic /robot_description -name my_robot
```

## Core Concepts

### 1. SDF World Structure

SDF (Simulation Description Format) defines worlds, models, and sensors.

```xml
<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="robot_world">
    
    <!-- Physics Configuration -->
    <physics name="default_physics" type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
      <ode>
        <solver>
          <type>quick</type>
          <iters>50</iters>
          <sor>1.3</sor>
        </solver>
        <constraints>
          <cfm>0.0</cfm>
          <erp>0.2</erp>
          <contact_max_correcting_vel>100.0</contact_max_correcting_vel>
          <contact_surface_layer>0.001</contact_surface_layer>
        </constraints>
      </ode>
    </physics>

    <!-- Lighting -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <!-- Ground Plane -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
          <surface>
            <friction>
              <ode>
                <mu>100</mu>
                <mu2>50</mu2>
              </ode>
            </friction>
          </surface>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
          <material>
            <ambient>0.8 0.8 0.8 1</ambient>
            <diffuse>0.8 0.8 0.8 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Include Robot Model -->
    <include>
      <uri>model://my_robot</uri>
      <name>robot1</name>
      <pose>0 0 0.1 0 0 0</pose>
    </include>

    <!-- Required Plugins -->
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>

  </world>
</sdf>
```

### 2. Physics Engine Selection

| Engine | Best For | Characteristics |
|--------|----------|-----------------|
| **ODE** | General robotics | Fast, stable, default |
| **Bullet** | Complex collisions | Better contact handling |
| **DART** | Articulated robots | Accurate joint constraints |
| **Simbody** | Biomechanics | High accuracy, slower |

```xml
<!-- ODE (default) -->
<physics name="ode_physics" type="ode">
  <max_step_size>0.001</max_step_size>
  <real_time_factor>1.0</real_time_factor>
  <ode>
    <solver>
      <type>quick</type>
      <iters>50</iters>
      <sor>1.3</sor>
    </solver>
  </ode>
</physics>

<!-- DART for articulated robots -->
<physics name="dart_physics" type="dart">
  <max_step_size>0.001</max_step_size>
  <dart>
    <collision_detector>fcl</collision_detector>
    <solver>
      <solver_type>pgs</solver_type>
    </solver>
  </dart>
</physics>
```

### 3. Sensor Configuration

**Camera:**
```xml
<sensor name="camera" type="camera">
  <always_on>true</always_on>
  <update_rate>30</update_rate>
  <camera>
    <horizontal_fov>1.3962634</horizontal_fov>
    <image>
      <width>640</width>
      <height>480</height>
      <format>R8G8B8</format>
    </image>
    <clip>
      <near>0.1</near>
      <far>100</far>
    </clip>
    <noise>
      <type>gaussian</type>
      <mean>0</mean>
      <stddev>0.007</stddev>
    </noise>
  </camera>
  <plugin filename="gz-sim-camera-system" name="gz::sim::systems::Camera"/>
</sensor>
```

**Depth Camera:**
```xml
<sensor name="depth_camera" type="depth_camera">
  <always_on>true</always_on>
  <update_rate>15</update_rate>
  <camera>
    <horizontal_fov>1.047</horizontal_fov>
    <image>
      <width>640</width>
      <height>480</height>
    </image>
    <clip>
      <near>0.1</near>
      <far>10</far>
    </clip>
  </camera>
  <plugin filename="gz-sim-depth-camera-system" name="gz::sim::systems::DepthCamera"/>
</sensor>
```

**LiDAR:**
```xml
<sensor name="lidar" type="gpu_lidar">
  <always_on>true</always_on>
  <update_rate>10</update_rate>
  <lidar>
    <scan>
      <horizontal>
        <samples>640</samples>
        <resolution>1</resolution>
        <min_angle>-3.14159</min_angle>
        <max_angle>3.14159</max_angle>
      </horizontal>
      <vertical>
        <samples>16</samples>
        <resolution>1</resolution>
        <min_angle>-0.26</min_angle>
        <max_angle>0.26</max_angle>
      </vertical>
    </scan>
    <range>
      <min>0.3</min>
      <max>100</max>
      <resolution>0.01</resolution>
    </range>
    <noise>
      <type>gaussian</type>
      <mean>0</mean>
      <stddev>0.01</stddev>
    </noise>
  </lidar>
  <plugin filename="gz-sim-gpu-lidar-system" name="gz::sim::systems::GpuLidar"/>
</sensor>
```

**IMU:**
```xml
<sensor name="imu" type="imu">
  <always_on>true</always_on>
  <update_rate>200</update_rate>
  <imu>
    <angular_velocity>
      <x>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.0002</stddev>
        </noise>
      </x>
    </angular_velocity>
    <linear_acceleration>
      <x>
        <noise type="gaussian">
          <mean>0.0</mean>
          <stddev>0.017</stddev>
        </noise>
      </x>
    </linear_acceleration>
  </imu>
  <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
</sensor>
```

### 4. ROS2-Gazebo Bridge

```xml
<!-- In SDF world file -->
<plugin filename="gz-sim-ros-gz-bridge" name="ros_gz_bridge::RosGzBridge">
  <ros>
    <namespace>/robot</namespace>
  </ros>

  <!-- Camera -->
  <bridge topic="/camera/image_raw" 
          ros_topic="/robot/camera/image_raw" 
          type="sensor_msgs/msg/Image" 
          direction="GZ_TO_ROS"/>
  <bridge topic="/camera/camera_info" 
          ros_topic="/robot/camera/camera_info" 
          type="sensor_msgs/msg/CameraInfo" 
          direction="GZ_TO_ROS"/>

  <!-- LiDAR -->
  <bridge topic="/lidar/points" 
          ros_topic="/robot/scan" 
          type="sensor_msgs/msg/PointCloud2" 
          direction="GZ_TO_ROS"/>

  <!-- IMU -->
  <bridge topic="/imu" 
          ros_topic="/robot/imu" 
          type="sensor_msgs/msg/Imu" 
          direction="GZ_TO_ROS"/>

  <!-- Command -->
  <bridge topic="/cmd_vel" 
          ros_topic="/robot/cmd_vel" 
          type="geometry_msgs/msg/Twist" 
          direction="ROS_TO_GZ"/>

  <!-- Odometry -->
  <bridge topic="/odom" 
          ros_topic="/robot/odom" 
          type="nav_msgs/msg/Odometry" 
          direction="GZ_TO_ROS"/>
</plugin>
```

## Common Patterns

### Pattern 1: Complete Robot Launch

```python
# launch/simulation.launch.py
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_share = FindPackageShare('my_robot_gazebo')

    # Gazebo with world
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('ros_gz_sim'), '/launch/gz_sim.launch.py'
        ]),
        launch_arguments={
            'gz_args': ['-r ', PathJoinSubstitution([pkg_share, 'worlds', 'warehouse.sdf'])],
            'on_exit_shutdown': 'true'
        }.items()
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': PathJoinSubstitution([
                pkg_share, 'urdf', 'robot.xacro'
            ])
        }]
    )

    # Spawn robot
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'my_robot',
            '-topic', '/robot_description',
            '-x', '0', '-y', '0', '-z', '0.1'
        ],
        output='screen'
    )

    # Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge
    ])
```

### Pattern 2: Differential Drive Robot Plugin

```xml
<!-- In robot URDF/SDF -->
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
```

### Pattern 3: Custom World with Obstacles

```xml
<?xml version="1.0" ?>
<sdf version="1.8">
  <world name="navigation_world">
    
    <include>
      <uri>model://sun</uri>
    </include>
    
    <include>
      <uri>model://ground_plane</uri>
    </include>

    <!-- Wall obstacle -->
    <model name="wall_1">
      <static>true</static>
      <pose>5 0 1 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry>
            <box>
              <size>0.2 4 2</size>
            </box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box>
              <size>0.2 4 2</size>
            </box>
          </geometry>
          <material>
            <ambient>0.5 0.5 0.5 1</ambient>
            <diffuse>0.5 0.5 0.5 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- Cylinder obstacle -->
    <model name="pillar">
      <static>true</static>
      <pose>2 3 0.5 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry>
            <cylinder>
              <radius>0.3</radius>
              <length>1</length>
            </cylinder>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <cylinder>
              <radius>0.3</radius>
              <length>1</length>
            </cylinder>
          </geometry>
        </visual>
      </link>
    </model>

  </world>
</sdf>
```

## Anti-Patterns

### ❌ Using detailed meshes for collision
Complex meshes for collision slow simulation dramatically.

**What happens:** Simulation runs at 0.1x real-time, robots jitter, contact detection fails.

### ✅ Use simplified collision primitives
```xml
<collision>
  <geometry>
    <box size="0.5 0.3 0.1"/>  <!-- Simple box -->
  </geometry>
</collision>
<visual>
  <geometry>
    <mesh filename="complex_visual.dae"/>  <!-- Detailed visual -->
  </geometry>
</visual>
```

### ❌ Missing sensor noise models
Perfect sensors don't match real-world behavior.

**What happens:** Algorithms work in sim but fail on real hardware (reality gap).

### ✅ Add realistic noise
```xml
<noise>
  <type>gaussian</type>
  <mean>0</mean>
  <stddev>0.01</stddev>  <!-- Match real sensor specs -->
</noise>
```

### ❌ Incorrect physics step size
Step size too large causes instability.

**What happens:** Robot explodes, joints fly apart, simulation crashes.

### ✅ Use appropriate step size
```xml
<max_step_size>0.001</max_step_size>  <!-- 1ms for stability -->
<real_time_update_rate>1000</real_time_update_rate>
```

## Configuration Reference

### Physics Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_step_size` | 0.001 | Simulation step (seconds) |
| `real_time_factor` | 1.0 | Speed multiplier (1.0 = real-time) |
| `iters` | 50 | Solver iterations |
| `sor` | 1.3 | Successive over-relaxation |
| `cfm` | 0.0 | Constraint force mixing |
| `erp` | 0.2 | Error reduction parameter |

### Bridge Message Types

| ROS2 Type | Gazebo Type | Direction |
|-----------|-------------|-----------|
| `geometry_msgs/Twist` | `gz.msgs.Twist` | ROS→GZ |
| `nav_msgs/Odometry` | `gz.msgs.Odometry` | GZ→ROS |
| `sensor_msgs/Image` | `gz.msgs.Image` | GZ→ROS |
| `sensor_msgs/LaserScan` | `gz.msgs.LaserScan` | GZ→ROS |
| `sensor_msgs/PointCloud2` | `gz.msgs.PointCloudPacked` | GZ→ROS |
| `sensor_msgs/Imu` | `gz.msgs.IMU` | GZ→ROS |

### Model Path Resolution

```
model://my_model
  → ~/.gz/models/my_model/
  → /usr/share/gz/gz-sim8/models/my_model/
  → $GZ_SIM_MODEL_PATH/my_model/
```

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Robot explodes on spawn | Massive mass ratio or bad inertia | Check inertia values, keep mass ratios < 100 |
| Simulation slow | Complex collision meshes | Simplify collision geometry |
| Black camera image | Missing render engine | Set `<render_engine>ogre2</render_engine>` |
| Topics not bridging | Wrong message type | Check type mapping in bridge config |
| Robot slides on ground | No friction | Add `<mu>` to ground plane contact |
| Joints oscillate | High gains, low damping | Add damping: `<dynamics damping="1.0"/>` |
| Sensors not publishing | Missing plugin | Include sensor system plugin |
| TF not published | odometry plugin missing | Add diff_drive or odometry plugin |
| Gazebo crashes on start | Corrupted world file | Validate SDF: `gz sdf -k world.sdf` |

## Workflow Integration

- **Before this:** Create robot model with `robot-modeling`
- **Parallel with:** Use `ros2` for node development and testing
- **After this:** Use `sim-to-real` for domain transfer to hardware
- **For ML:** Use `isaac-sim` if photorealistic rendering needed

## Further Reading

- [Gazebo Sim Documentation](https://gazebosim.org/docs)
- [SDF Specification](http://sdformat.org/spec)
- [ROS-Gazebo Integration](https://github.com/gazebosim/ros_gz)
- Related skills: `robot-modeling`, `ros2`, `sim-to-real`, `isaac-sim`

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering Gazebo Sim (Harmonic) and Classic
- Includes SDF worlds, physics, sensors, ROS2 bridge