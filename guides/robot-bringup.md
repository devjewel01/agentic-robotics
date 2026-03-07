# Robot Bringup Guide

This guide walks through the complete process of bringing up a new robot from unboxing to first autonomous operation.

## Goal

Take a newly assembled robot from power-on to successfully navigating autonomously in a mapped environment.

## Prerequisites

- **Hardware:** Fully assembled robot with all sensors mounted
- **Software:** ROS2 Humble installed on robot computer
- **Skills needed:** `ros2`, `robot-modeling`, `ros2-control`, `nav2`

## Estimated Time

4-8 hours for first bringup (experienced: 2-3 hours)

---

## Phase 1: Hardware Verification (30-60 min)

### Step 1.1: Power System Check

**Objective:** Verify power distribution and battery safety.

```bash
# Check battery voltage (should be 12V, 24V, or 48V nominal)
multimeter on battery terminals

# Verify voltage under load (motors moving)
# Should not drop more than 10% from nominal

# Check all power rails
# 5V for sensors, 12V for motors, etc.
```

**Checkpoint:**
- [ ] Battery voltage nominal ±5%
- [ ] No voltage drops under light load
- [ ] All fuses intact
- [ ] Emergency stop button works

### Step 1.2: Motor and Encoder Check

**Objective:** Verify motors rotate and encoders report correctly.

```bash
# Manual test: apply low voltage to each motor
# Should rotate smoothly in both directions

# Check encoder counts
ros2 topic echo /wheel_encoders  # Or your encoder topic

# Rotate wheel by hand, verify counts change
# Verify direction: forward = positive counts
```

**Skill reference:** See `skills/ros2-control/SKILL.md` -> "Hardware Interfaces"

**Checkpoint:**
- [ ] All motors rotate smoothly
- [ ] No abnormal noise or vibration
- [ ] Encoders report counts
- [ ] Direction is correct (positive = forward)

### Step 1.3: Sensor Verification

**Objective:** Verify all sensors publish data.

**LiDAR:**
```bash
# Start LiDAR driver
ros2 launch <lidar_pkg> driver.launch.py

# Check data
ros2 topic hz /scan
ros2 topic echo /scan --once

# Verify in RViz
ros2 run rviz2 rviz2
# Add LaserScan display, set topic to /scan
```

**Camera:**
```bash
# Start camera driver
ros2 launch <camera_pkg> driver.launch.py

# Check data
ros2 topic hz /camera/color/image_raw

# Verify in RViz
# Add Image display
```

**IMU:**
```bash
# Start IMU driver
ros2 launch <imu_pkg> driver.launch.py

# Check data
ros2 topic echo /imu/data --once
# Verify all fields: orientation, angular_velocity, linear_acceleration
```

**Checkpoint:**
- [ ] All sensors publishing at expected rate
- [ ] No errors in driver logs
- [ ] Data looks reasonable in RViz
- [ ] Frame IDs are correct

---

## Phase 2: Software Setup (45-90 min)

### Step 2.1: Create Robot Description

**Objective:** Create URDF/Xacro for the robot.

```bash
# Create package
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake my_robot_description

# Create URDF directory
mkdir -p my_robot_description/urdf
mkdir -p my_robot_description/launch
mkdir -p my_robot_description/config
```

**Create URDF:**

> **Skill reference:** See `skills/robot-modeling/SKILL.md` -> "URDF Structure"

Key elements needed:
- Links with collision geometry
- Joints with limits
- Gazebo plugins (if simulating)
- Sensor links with correct transforms

**Test URDF:**
```bash
# View in RViz
ros2 launch my_robot_description view_robot.launch.py

# Check TF tree
ros2 run tf2_tools view_frames
```

**Checkpoint:**
- [ ] URDF loads without errors
- [ ] All links visible in RViz
- [ ] TF tree is connected (no broken frames)
- [ ] Joint limits are reasonable

### Step 2.2: Configure ros2_control

**Objective:** Set up hardware interfaces.

> **Skill reference:** See `skills/ros2-control/SKILL.md` -> "Hardware Interfaces"

Create controller configuration:
```yaml
# config/controllers.yaml
controller_manager:
  ros__parameters:
    update_rate: 100

    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster

    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController
      left_wheel_names: ["left_wheel_joint"]
      right_wheel_names: ["right_wheel_joint"]
      wheel_separation: 0.3
      wheel_radius: 0.05
```

**Checkpoint:**
- [ ] Controller manager starts
- [ ] Hardware interfaces load
- [ ] Joint states published
- [ ] No errors in controller logs

---

## Phase 3: Teleoperation (30-45 min)

### Step 3.1: Test Manual Control

**Objective:** Drive robot manually to verify basic mobility.

```bash
# Launch robot base
ros2 launch my_robot_bringup robot.launch.py

# In another terminal, teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Test checklist:**
- [ ] Forward/backward movement
- [ ] Left/right turning
- [ ] Smooth acceleration
- [ ] Emergency stop works

### Step 3.2: Verify Odometry

**Objective:** Confirm odometry is reasonable.

```bash
# Monitor odometry
ros2 topic echo /odom --once

# Drive forward 1 meter
# Check that position.x increased by ~1.0

# Rotate 360 degrees
# Check that orientation.z returns to start
```

> **Skill reference:** See `skills/robot-modeling/SKILL.md` -> "TF2 Coordinate Frames"

**Common issues:**
- Odometry diverges → Check encoder counts/direction
- Robot rotates wrong way → Swap left/right in controller config
- Distance wrong → Calibrate wheel radius

---

## Phase 4: SLAM Setup (45-90 min)

### Step 4.1: Launch SLAM

**Objective:** Create first map of environment.

> **Skill reference:** See `skills/sensor-fusion-slam/SKILL.md`

```bash
# Option 1: Cartographer (2D LiDAR)
ros2 launch cartographer_ros cartographer.launch.py

# Option 2: RTAB-Map (RGB-D or LiDAR)
ros2 launch rtabmap_launch rtabmap.launch.py

# Option 3: SLAM Toolbox (2D LiDAR)
ros2 launch slam_toolbox online_async_launch.py
```

### Step 4.2: Map the Environment

**Procedure:**
1. Start SLAM node
2. Open RViz with map display
3. Teleop robot slowly around environment
4. Ensure loop closure (return to start)
5. Save the map

```bash
# Save Cartographer map
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
  "{filename: '/path/to/map.pbstream'}"

# Save RTAB-Map
ros2 service call /rtabmap/save_map std_srvs/srv/Empty "{data: '/path/to/map.db'}"

# Save SLAM Toolbox / Nav2 map
ros2 run nav2_map_server map_saver_cli -f my_map
```

**Checkpoint:**
- [ ] Map looks correct (walls, obstacles)
- [ ] No drift or deformation
- [ ] Robot relocalizes at start position
- [ ] Map file saved successfully

---

## Phase 5: Navigation Setup (60-120 min)

### Step 5.1: Configure Nav2

> **Skill reference:** See `skills/nav2/SKILL.md` -> "Complete Nav2 Configuration"

Create Nav2 parameters file:
```yaml
# config/nav2_params.yaml
amcl:
  ros__parameters:
    use_sim_time: False
    # ... AMCL parameters

controller_server:
  ros__parameters:
    controller_plugins: ["FollowPath"]
    FollowPath:
      plugin: "dwb_core::DWBLocalPlanner"
      # ... DWB parameters tuned for your robot

local_costmap:
  ros__parameters:
    # Match your robot footprint
    robot_radius: 0.22
    # ... costmap parameters
```

### Step 5.2: Launch Navigation

```bash
# Launch navigation with saved map
ros2 launch nav2_bringup navigation_launch.py \
  map:=/path/to/my_map.yaml \
  params_file:=/path/to/nav2_params.yaml
```

### Step 5.3: Test Autonomous Navigation

**Set initial pose:**
```bash
ros2 topic pub /initialpose geometry_msgs/PoseWithCovarianceStamped \
  '{header: {frame_id: "map"}, pose: {pose: {position: {x: 0.0, y: 0.0}, orientation: {w: 1.0}}}}'
```

**Send navigation goal:**
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 2.0, y: 1.0}, orientation: {w: 1.0}}}}'
```

**Test checklist:**
- [ ] Robot localizes correctly
- [ ] Path is computed
- [ ] Robot follows path
- [ ] Avoids obstacles
- [ ] Reaches goal
- [ ] Recovery behaviors work (test by blocking path)

---

## Validation Checklist

### Hardware
- [ ] All sensors working
- [ ] Motors respond correctly
- [ ] Emergency stop functional
- [ ] Battery lasts expected duration

### Software
- [ ] All nodes start without errors
- [ ] TF tree complete
- [ ] Topics publishing at correct rates
- [ ] Parameters loaded correctly

### Navigation
- [ ] Accurate localization
- [ ] Successful navigation to multiple goals
- [ ] Obstacle avoidance working
- [ ] Recovery behaviors tested

---

## Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| TF errors | Missing transforms | Check URDF, run robot_state_publisher |
| Controllers fail | Wrong interface names | Match URDF joint names with controller config |
| AMCL diverges | Bad initial pose | Set initial pose in RViz |
| Planner fails | Goal in obstacle | Increase tolerance or clear costmap |
| Robot doesn't move | Controller not active | `ros2 control switch_controllers --start diff_drive_controller` |
| Sensors not visible | Wrong topic names | Check remappings in launch files |

---

## Next Steps

After successful bringup:

1. **Tune controllers** - See `skills/control-systems/SKILL.md`
2. **Calibrate sensors** - See `guides/sensor-calibration.md`
3. **Add safety systems** - See `skills/safety-systems/SKILL.md`
4. **Deploy to fleet** - See `skills/deployment-fleet/SKILL.md`

---

## Resources

- Related skills: `ros2`, `robot-modeling`, `ros2-control`, `nav2`, `sensor-fusion-slam`
- Phase 2 deliverables complete