---
name: sensor-fusion-slam
description: Multi-sensor fusion and SLAM including ORB-SLAM3, RTAB-Map, Cartographer, LIO-SAM, EKF/UKF state estimation with robot_localization. Use when implementing localization, mapping, or sensor fusion.
category: perception
tags: [slam, sensor-fusion, localization, ekf, ukf, orb-slam3, rtabmap, cartographer]
version: "1.0.0"
---

# Sensor Fusion & SLAM

Simultaneous Localization and Mapping (SLAM) and multi-sensor fusion are fundamental for robot autonomy. This skill covers visual SLAM (ORB-SLAM3, RTAB-Map), LiDAR SLAM (Cartographer, LIO-SAM), and state estimation using Kalman filtering.

## When to Use

- Implementing robot localization with SLAM
- Configuring multi-sensor fusion (IMU, GPS, odometry, visual)
- Setting up ORB-SLAM3 for visual-inertial navigation
- Configuring RTAB-Map for RGB-D or LiDAR SLAM
- Deploying Cartographer for 2D/3D mapping
- Implementing LIO-SAM for LiDAR-inertial SLAM
- Tuning EKF/UKF parameters for state estimation
- Fusing GPS with local odometry for outdoor navigation

## Quick Start

```bash
# Install SLAM packages
sudo apt install ros-$ROS_DISTRO-robot-localization
sudo apt install ros-$ROS_DISTRO-rtabmap-ros
sudo apt install ros-$ROS_DISTRO-cartographer-ros
sudo apt install ros-$ROS_DISTRO-slam-toolbox

# Launch EKF with robot_localization
ros2 launch robot_localization ekf.launch.py

# Launch RTAB-Map
ros2 launch rtabmap_launch rtabmap.launch.py \
  args:="-d" \
  rgb_topic:=/camera/color/image_raw \
  depth_topic:=/camera/depth/image_rect_raw \
  camera_info_topic:=/camera/color/camera_info

# Launch Cartographer
ros2 launch cartographer_ros cartographer.launch.py
```

## Core Concepts

### 1. SLAM Taxonomy

| SLAM Type | Sensors | Algorithms | Best For |
|-----------|---------|------------|----------|
| Visual | Monocular, Stereo, RGB-D | ORB-SLAM3, RTAB-Map | Indoor, feature-rich |
| LiDAR | 2D/3D LiDAR | Cartographer, LOAM, LIO-SAM | Indoor/outdoor, structure |
| Visual-Inertial | Camera + IMU | ORB-SLAM3 VI, VINS-Fusion | High-dynamics, GPS-denied |
| LiDAR-Inertial | LiDAR + IMU | LIO-SAM, Fast-LIO | Fast motion, outdoor |
| Multi-sensor | All above | RTAB-Map, custom fusion | Robust long-term |

### 2. robot_localization (EKF/UKF)

The `robot_localization` package fuses multiple sensor sources into a unified state estimate.

**Single EKF Configuration:**
```yaml
# config/ekf.yaml
ekf_filter_node:
  ros__parameters:
    frequency: 50.0
    sensor_timeout: 0.1
    two_d_mode: false
    
    # Frames
    map_frame: map
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom
    
    # Transform settings
    publish_tf: true
    transform_time_offset: 0.0
    transform_timeout: 0.0
    
    # Odometry source (wheel encoders)
    odom0: /wheel_odom
    odom0_config: [true,  true,  false,   # x, y, z position
                   false, false, true,    # roll, pitch, yaw
                   true,  true,  false,   # vx, vy, vz
                   false, false, true,    # vroll, vpitch, vyaw
                   false, false, false]   # ax, ay, az
    odom0_differential: false
    odom0_relative: false
    odom0_queue_size: 10
    
    # IMU source
    imu0: /imu/data
    imu0_config: [false, false, false,    # x, y, z position
                  true,  true,  true,     # roll, pitch, yaw
                  false, false, false,    # vx, vy, vz
                  true,  true,  true,     # vroll, vpitch, vyaw
                  true,  true,  true]     # ax, ay, az
    imu0_differential: false
    imu0_relative: false
    imu0_queue_size: 10
    imu0_remove_gravitational_acceleration: true
    
    # Process noise (tune based on sensor quality)
    process_noise_covariance: [
      0.05, 0.05, 0.06,    # x, y, z
      0.03, 0.03, 0.06,    # roll, pitch, yaw
      0.025, 0.025, 0.04,  # vx, vy, vz
      0.01, 0.01, 0.02,    # vroll, vpitch, vyaw
      0.01, 0.01, 0.015    # ax, ay, az
    ]
    
    # Initial covariance
    initial_estimate_covariance: [
      1e-9, 1e-9, 1e-9,
      1e-9, 1e-9, 1e-9,
      1e-9, 1e-9, 1e-9,
      1e-9, 1e-9, 1e-9,
      1e-9, 1e-9, 1e-9
    ]
```

**Dual EKF Setup (Odom + Map Frames):**
```yaml
# Dual EKF for continuous odometry and global localization
ekf_filter_node_odom:
  ros__parameters:
    frequency: 50.0
    world_frame: odom
    
    # Fuse IMU + wheel odometry for smooth local odometry
    imu0: /imu/data
    imu0_config: [false, false, false,
                  true,  true,  true,
                  false, false, false,
                  true,  true,  true,
                  true,  true,  true]
    imu0_remove_gravitational_acceleration: true
    
    odom0: /wheel_odom
    odom0_config: [true,  true,  false,
                   false, false, true,
                   true,  true,  false,
                   false, false, true,
                   false, false, false]

ekf_filter_node_map:
  ros__parameters:
    frequency: 50.0
    world_frame: map
    
    # Fuse odometry + GPS for global localization
    odom0: /odometry/filtered
    odom0_config: [true,  true,  true,
                   true,  true,  true,
                   true,  true,  true,
                   true,  true,  true,
                   true,  true,  true]
    
    odom1: /gps/odom
    odom1_config: [true,  true,  true,
                   false, false, false,
                   false, false, false,
                   false, false, false,
                   false, false, false]

navsat_transform_node:
  ros__parameters:
    frequency: 50.0
    magnetic_declination_radians: 0.0
    yaw_offset: 0.0
    zero_altitude: true
    broadcast_utm_transform: true
    publish_filtered_gps: true
    use_odometry_yaw: false
```

**Sensor Configuration Matrix:**

| Sensor | Position (x,y,z) | Orientation (r,p,y) | Velocity (vx,vy,vz) | Angular Vel | Acceleration |
|--------|------------------|---------------------|---------------------|-------------|--------------|
| Wheel odometry | ✓ | ✓ | ✓ | ✗ | ✗ |
| Visual odometry | ✓ | ✓ | ✓ | ✗ | ✗ |
| GPS | ✓ | ✗ | ✗ | ✗ | ✗ |
| IMU | ✗ | ✓ | ✗ | ✓ | ✓ |
| Pose (Vicon, etc) | ✓ | ✓ | ✗ | ✗ | ✗ |

### 3. ORB-SLAM3

ORB-SLAM3 is a versatile visual SLAM system supporting monocular, stereo, RGB-D, and visual-inertial configurations.

**Installation:**
```bash
cd ~/ros2_ws/src
git clone https://github.com/zang09/ORB_SLAM3_ROS2.git
cd ~/ros2_ws
colcon build --packages-select orbslam3
```

**Monocular Configuration:**
```yaml
# orb_slam3_mono.yaml
%YAML:1.0

Camera.type: "PinHole"
Camera.fx: 458.654
Camera.fy: 457.296
Camera.cx: 367.215
Camera.cy: 248.375
Camera.k1: -0.28340811
Camera.k2: 0.07395907
Camera.p1: 0.00019359
Camera.p2: 1.76187114e-05

Camera.width: 752
Camera.height: 480
Camera.fps: 20.0

# Color order: 0 BGR, 1 RGB
Camera.RGB: 1

ORBextractor.nFeatures: 1200
ORBextractor.scaleFactor: 1.2
ORBextractor.nLevels: 8
ORBextractor.iniThFAST: 20
ORBextractor.minThFAST: 7

Viewer.KeyFrameSize: 0.05
Viewer.KeyFrameLineWidth: 1
Viewer.GraphLineWidth: 0.9
Viewer.PointSize: 2
```

**Visual-Inertial Configuration:**
```yaml
# orb_slam3_stereo_inertial.yaml
%YAML:1.0

# Camera parameters (stereo)
Camera.type: "PinHole"
Camera.fx: 435.2046959714599
Camera.fy: 435.2046959714599
Camera.cx: 367.4517211914062
Camera.cy: 252.2008514404297

Camera.k1: 0.0
Camera.k2: 0.0
Camera.p1: 0.0
Camera.p2: 0.0

Camera.width: 752
Camera.height: 480
Camera.fps: 20.0

# Stereo baseline times fx
Camera.bf: 47.90639384423901

# Camera-IMU transformation
Tbc: !!opencv-matrix
  rows: 4
  cols: 4
  dt: f
  data: [0.0148655429818, -0.999880929698, 0.00414029679422, -0.0216401454975,
         0.999557249008, 0.0149672133247, 0.025715529948, -0.064676986768,
        -0.0257744366974, 0.00375618835797, 0.999660727178, 0.00981073058949,
         0.0, 0.0, 0.0, 1.0]

# IMU noise parameters
IMU.NoiseGyro: 1.7e-4
IMU.NoiseAcc: 2.0e-3
IMU.GyroWalk: 1.9e-5
IMU.AccWalk: 3.0e-3
IMU.Frequency: 200

ORBextractor.nFeatures: 1200
ORBextractor.scaleFactor: 1.2
ORBextractor.nLevels: 8
ORBextractor.iniThFAST: 20
ORBextractor.minThFAST: 7
```

**Launch ORB-SLAM3:**
```bash
# Monocular
ros2 run orbslam3 mono \
  /path/to/ORBvoc.txt \
  /path/to/mono_config.yaml \
  /camera/image_raw

# Stereo-Inertial
ros2 run orbslam3 stereo_inertial \
  /path/to/ORBvoc.txt \
  /path/to/stereo_inertial_config.yaml \
  /camera/left/image_raw \
  /camera/right/image_raw \
  /imu/data
```

### 4. RTAB-Map

RTAB-Map is a RGB-D, stereo, and LiDAR graph-based SLAM approach with real-time appearance-based loop closure.

**Configuration:**
```yaml
# rtabmap_params.yaml
rtabmap:
  ros__parameters:
    # Database
    database_path: ""
    frame_id: base_link
    
    # Detection
    Rtabmap/DetectionRate: "1.0"
    Rtabmap/TimeThr: "700"  # ms
    
    # Memory
    Mem/IncrementalMemory: "true"
    Mem/STMSize: "30"
    Mem/RehearsalSimilarity: "0.6"
    Mem/NotLinkedNodesKept: "false"
    
    # Visual Features
    Vis/FeatureType: "6"  # 6=ORB, 11=SuperPoint
    Vis/MaxFeatures: "500"
    Vis/MinInliers: "20"
    Vis/InlierDistance: "0.1"
    
    # Loop Closure
    RGBD/LoopClosureReextractFeatures: "true"
    RGBD/OptimizeFromGraphEnd: "false"
    RGBD/ProximityBySpace: "true"
    RGBD/ProximityPathMaxNeighbors: "10"
    
    # ICP for LiDAR
    Reg/Strategy: "1"  # 0=Vis, 1=ICP, 2=Vis+ICP
    Icp/PointToPlane: "true"
    Icp/Iterations: "30"
    Icp/VoxelSize: "0.05"
    Icp/MaxCorrespondenceDistance: "0.1"
    
    # Graph Optimization
    Optimizer/Strategy: "1"  # 1=g2o, 2=gtsam
    Optimizer/Iterations: "20"
    
    # Mapping
    Grid/CellSize: "0.05"
    Grid/RangeMax: "5.0"
    Grid/RayTracing: "true"
    Grid/3D: "true"
    Grid/FromDepth: "true"

rgbd_odometry:
  ros__parameters:
    frame_id: base_link
    odom_frame_id: odom
    publish_tf: true
    
    Odom/Strategy: "0"  # 0=Frame-to-Map, 1=Frame-to-Frame
    OdomF2M/MaxSize: "3000"
    Vis/CorType: "0"  # 0=Features matching, 1=Optical flow
```

**Launch RTAB-Map:**
```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # RGB-D Odometry
        Node(
            package='rtabmap_odom',
            executable='rgbd_odometry',
            output='screen',
            parameters=[{
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'publish_tf': True,
                'subscribe_rgbd': True,
                'approx_sync': True,
            }],
            remappings=[
                ('rgbd_image', '/camera/rgbd'),
            ]
        ),
        
        # RTAB-Map SLAM
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            output='screen',
            parameters=[{
                'subscribe_rgbd': True,
                'subscribe_scan': True,
                'approx_sync': True,
                'frame_id': 'base_link',
                'map_frame_id': 'map',
                'odom_frame_id': 'odom',
            }],
            remappings=[
                ('rgbd_image', '/camera/rgbd'),
                ('scan', '/lidar/scan'),
            ]
        ),
        
        # Visualization
        Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            output='screen',
            parameters=[{
                'subscribe_rgbd': True,
                'subscribe_scan': True,
            }],
        )
    ])
```

### 5. Cartographer

Google Cartographer is a system that provides real-time simultaneous localization and mapping in 2D and 3D.

**2D Configuration (Lua):**
```lua
-- cartographer_2d.lua
include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "base_link",
  odom_frame = "odom",
  provide_odom_frame = true,
  publish_frame_projected_to_2d = false,
  use_odometry = false,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER_2D.min_range = 0.3
TRAJECTORY_BUILDER_2D.max_range = 30.
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 1.
TRAJECTORY_BUILDER_2D.use_imu_data = false
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(0.1)

POSE_GRAPH.constraint_builder.min_score = 0.65
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.7
```

**3D Configuration (LiDAR + IMU):**
```lua
-- cartographer_3d.lua
include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "imu_link",
  published_frame = "base_link",
  odom_frame = "odom",
  provide_odom_frame = true,
  use_odometry = false,
  num_laser_scans = 0,
  num_point_clouds = 1,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
}

MAP_BUILDER.use_trajectory_builder_3d = true
MAP_BUILDER.num_background_threads = 4

TRAJECTORY_BUILDER_3D.num_accumulated_range_data = 1
TRAJECTORY_BUILDER_3D.min_range = 1.
TRAJECTORY_BUILDER_3D.max_range = 100.
TRAJECTORY_BUILDER_3D.voxel_filter_size = 0.15

POSE_GRAPH.optimization_problem.huber_scale = 5e2
POSE_GRAPH.optimize_every_n_nodes = 90
POSE_GRAPH.constraint_builder.sampling_ratio = 0.03
POSE_GRAPH.constraint_builder.min_score = 0.62
```

### 6. LIO-SAM

LIO-SAM (LiDAR Inertial Odometry via Smoothing and Mapping) tightly couples LiDAR and IMU data for robust localization.

**Configuration:**
```yaml
# lio_sam_params.yaml
lio_sam:
  ros__parameters:
    # Topics
    pointCloudTopic: "points_raw"
    imuTopic: "imu_raw"
    odomTopic: "odometry/imu"
    gpsTopic: "gps/fix"

    # Frames
    lidarFrame: "base_link"
    baselinkFrame: "base_link"
    odometryFrame: "odom"
    mapFrame: "map"

    # Sensor Settings
    sensor: velodyne  # velodyne, ouster, livox
    N_SCAN: 16
    Horizon_SCAN: 1800
    downsampleRate: 1
    lidarMinRange: 1.0
    lidarMaxRange: 100.0

    # IMU Settings (tune for your IMU)
    imuAccNoise: 3.9939570888238808e-03
    imuGyrNoise: 1.5636343949698187e-03
    imuAccBiasN: 6.4356659353532566e-05
    imuGyrBiasN: 3.5640318696367613e-05
    imuGravity: 9.80511
    imuRPYWeight: 0.01

    # Extrinsics (LiDAR -> IMU)
    extrinsicTrans: [0.0, 0.0, 0.0]
    extrinsicRot: [-1, 0, 0,
                    0, 1, 0,
                    0, 0, -1]

    # LOAM feature extraction
    edgeThreshold: 1.0
    surfThreshold: 0.1
    edgeFeatureMinValidNum: 10
    surfFeatureMinValidNum: 100

    # Voxel filter
    odometrySurfLeafSize: 0.4
    mappingCornerLeafSize: 0.2
    mappingSurfLeafSize: 0.4

    # Loop closure
    loopClosureEnableFlag: true
    loopClosureFrequency: 1.0
    surroundingKeyframeSize: 50
    historyKeyframeSearchRadius: 15.0
    historyKeyframeSearchTimeDiff: 30.0
    historyKeyframeFitnessScore: 0.3

    # Optimization
    numberOfCores: 4
    mappingProcessInterval: 0.15
```

## Common Patterns

### Pattern 1: EKF with Outlier Rejection

```python
import numpy as np
from scipy.linalg import block_diag

class RobustEKF:
    """EKF with Mahalanobis distance-based outlier rejection."""
    
    def __init__(self, n_states=15):
        self.n_states = n_states
        self.x = np.zeros(n_states)
        self.P = np.eye(n_states) * 0.1
        self.Q = np.eye(n_states) * 0.01
        
        # Mahalanobis threshold (chi-squared, 3 DOF, 99% confidence)
        self.mahalanobis_threshold = 11.34
        
    def update_with_rejection(self, z, H, R):
        """Update with outlier rejection."""
        # Innovation
        y = z - H @ self.x
        
        # Innovation covariance
        S = H @ self.P @ H.T + R
        
        # Mahalanobis distance
        mahal_dist = np.sqrt(y.T @ np.linalg.inv(S) @ y)
        
        if mahal_dist < self.mahalanobis_threshold:
            # Standard EKF update
            K = self.P @ H.T @ np.linalg.inv(S)
            self.x = self.x + K @ y
            self.P = (np.eye(self.n_states) - K @ H) @ self.P
            
            return True, mahal_dist
        else:
            self.get_logger().warn(f"Outlier rejected: {mahal_dist:.2f}")
            return False, mahal_dist
```

### Pattern 2: SLAM Accuracy Evaluation

```bash
# Install evo toolkit
pip install evo

# Evaluate trajectory accuracy
evo_ape tum groundtruth.txt estimated.txt -va --plot

# Compute relative pose error
evo_rpe tum groundtruth.txt estimated.txt --delta 1 --delta_unit m -va --plot

# Compare multiple SLAM methods
evo_traj tum groundtruth.txt orb_slam.txt rtabmap.txt --ref groundtruth.txt -p
```

### Pattern 3: Map Saving and Loading

```bash
# RTAB-Map
# Save map
ros2 service call /rtabmap/pause std_srvs/srv/Empty
ros2 service call /rtabmap/save_map std_srvs/srv/Empty "{data: '/path/to/map.db'}"

# Load map for localization
ros2 run rtabmap_slam rtabmap \
  --ros-args -p database_path:=/path/to/map.db \
  -p Mem/IncrementalMemory:=false \
  -p Mem/InitWMWithAllNodes:=true

# Cartographer
# Save state
ros2 service call /write_state cartographer_ros_msgs/srv/WriteState \
  "{filename: '/path/to/map.pbstream'}"

# Load for pure localization
ros2 launch cartographer_ros localization.launch.py \
  load_state_filename:=/path/to/map.pbstream

# Export occupancy grid
ros2 run nav2_map_server map_saver_cli -f /path/to/map
```

## Anti-Patterns

### ❌ Ignoring sensor synchronization
Using unsynchronized sensors causes time misalignment and fusion errors.

**What happens:** Robot jumps, EKF diverges, SLAM fails to close loops.

### ✅ Synchronize sensors with message_filters
```python
from message_filters import Subscriber, ApproximateTimeSynchronizer

image_sub = Subscriber(self, Image, '/camera/image')
depth_sub = Subscriber(self, Image, '/camera/depth')
imu_sub = Subscriber(self, Imu, '/imu/data')

sync = ApproximateTimeSynchronizer(
    [image_sub, depth_sub, imu_sub],
    queue_size=10,
    slop=0.1  # 100ms tolerance
)
sync.registerCallback(self.fusion_callback)
```

### ❌ Wrong IMU coordinate frame
IMU data in wrong frame causes incorrect orientation estimates.

**What happens:** Robot thinks it's tilted when level, SLAM drifts rapidly.

### ✅ Verify IMU frame matches convention
```yaml
# Check IMU frame in URDF
<joint name="imu_joint" type="fixed">
  <parent link="base_link"/>
  <child link="imu_link"/>
  <origin xyz="0 0 0.1" rpy="0 0 0"/>
</joint>

# In EKF config
imu0_remove_gravitational_acceleration: true  # Critical!
```

### ❌ Overconfident sensor covariance
Setting sensor covariance too small causes filter to trust bad measurements.

**What happens:** Filter diverges, jumps to wrong positions, can't recover.

### ✅ Measure actual sensor noise
```python
# Collect sensor data while stationary
measurements = collect_sensor_data(duration=60)

# Compute covariance
covariance = np.cov(measurements.T)

# Use in EKF config
initial_estimate_covariance: [covariance diagonal]
```

## Configuration Reference

### EKF State Vector (15 states)

```
[x, y, z, roll, pitch, yaw, vx, vy, vz, vroll, vpitch, vyaw, ax, ay, az]
```

### Sensor Fusion Rates

| Sensor | Typical Rate | Latency |
|--------|--------------|---------|
| IMU | 200-1000 Hz | <1 ms |
| Wheel odometry | 50-100 Hz | 5-20 ms |
| Visual odometry | 30-60 Hz | 30-100 ms |
| LiDAR | 10-20 Hz | 50-100 ms |
| GPS | 1-10 Hz | 100-500 ms |

### SLAM Algorithm Selection

| Scenario | Recommended SLAM | Why |
|----------|------------------|-----|
| Indoor, texture-rich | ORB-SLAM3, RTAB-Map | Feature-based, loop closure |
| Indoor, low texture | RTAB-Map with ICP, LIO-SAM | Geometry-based |
| Outdoor, structured | Cartographer, LIO-SAM | Handles large-scale |
| High dynamics | ORB-SLAM3 VI, LIO-SAM | Inertial compensation |
| Long-term autonomy | RTAB-Map | Memory management |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| EKF diverges | Wrong covariance values | Tune process/measurement noise |
| SLAM loses tracking | Motion too fast | Reduce speed or increase camera FPS |
| Loop closure fails | Insufficient features | Add texture to environment |
| Z-drift in 2D SLAM | No height observation | Use 3D SLAM or add height constraint |
| GPS jumps | Multipath/urban canyon | Increase GPS covariance, use RTK |
| IMU bias drift | Temperature/aging | Enable online bias estimation |
| Map deformation | Wrong extrinsics | Calibrate camera-IMU-LiDAR extrinsics |
| Slow SLAM | Too many features | Reduce max_features, increase voxel size |

## Workflow Integration

- **Before this:** Use `robot-modeling` for coordinate frames, `camera-vision` for camera calibration
- **After this:** Use `nav2` for navigation with SLAM output
- **Parallel with:** Use `lidar-pointcloud` for LiDAR processing
- **For production:** Use `safety-systems` for localization monitoring

## Further Reading

- [robot_localization docs](http://docs.ros.org/en/noetic/api/robot_localization/html/index.html)
- [ORB-SLAM3 paper](https://arxiv.org/abs/2007.11898)
- [RTAB-Map wiki](https://wiki.ros.org/rtabmap)
- [Cartographer docs](https://google-cartographer.readthedocs.io/)
- [LIO-SAM paper](https://arxiv.org/abs/2007.00258)
- Related skills: `robot-modeling`, `camera-vision`, `lidar-pointcloud`, `nav2`

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering ORB-SLAM3, RTAB-Map, Cartographer, LIO-SAM
- Includes EKF/UKF sensor fusion with robot_localization