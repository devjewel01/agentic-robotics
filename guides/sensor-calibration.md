# Sensor Calibration Guide

End-to-end calibration workflow for cameras, LiDAR, and IMU sensors on mobile robots.

## Goal

Calibrate all sensors on a robot to ensure accurate perception, localization, and navigation.

## Prerequisites

- **Hardware:** Robot with camera(s), LiDAR, and IMU mounted
- **Software:** ROS2 Humble with calibration packages installed
- **Skills needed:** `camera-vision`, `lidar-pointcloud`, `sensor-fusion-slam`

## Estimated Time

2-4 hours for complete calibration

---

## Phase 1: Camera Calibration (45-90 min)

### Step 1.1: Intrinsic Calibration

**Objective:** Determine camera matrix and distortion coefficients.

> **Skill reference:** See `skills/camera-vision/SKILL.md` -> "Camera Calibration"

**Prepare calibration target:**
- Print checkerboard pattern (A4 or larger)
- Square size: 20mm recommended (measure exactly)
- Attach to rigid, flat surface

**Record calibration data:**
```bash
# Start camera driver
ros2 launch <camera_pkg> camera.launch.py

# Start calibration node
ros2 run camera_calibration cameracalibrator \
  --size 8x6 \
  --square 0.020 \
  image:=/camera/color/image_raw \
  camera:=/camera

# Move checkerboard in front of camera:
# - X: left/right
# - Y: up/down
# - Z: towards/away
# - Roll, Pitch, Yaw: tilt in all directions
# - Skew: extreme angles
```

**Capture guidelines:**
- Fill entire field of view
- At least 50 samples
- Good: X, Y, Size, Skew bars green
- "CALIBRATE" button becomes active

**Save calibration:**
```bash
# Click "CALIBRATE" (takes ~30 seconds)
# Click "SAVE"
# Calibration saved to /tmp/calibrationdata.tar.gz

# Extract and use
tar -xzf /tmp/calibrationdata.tar.gz
# Move ost.yaml to your config directory
```

**Checkpoint:**
- [ ] Reprojection error < 0.5 pixels
- [ ] Calibration file saved
- [ ] Distortion coefficients reasonable (k1, k2 typically -0.1 to 0.1)

### Step 1.2: Verify Intrinsic Calibration

**Test undistortion:**
```python
import cv2
import yaml
import numpy as np

# Load calibration
with open('ost.yaml') as f:
    calib = yaml.safe_load(f)

camera_matrix = np.array(calib['camera_matrix']['data']).reshape(3, 3)
dist_coeffs = np.array(calib['distortion_coefficients']['data'])

# Test on image
img = cv2.imread('test_image.jpg')
h, w = img.shape[:2]

# Undistort
undistorted = cv2.undistort(img, camera_matrix, dist_coeffs)

# Compare
cv2.imshow('Original', img)
cv2.imshow('Undistorted', undistorted)
cv2.waitKey(0)
```

**Checkpoint:**
- [ ] Straight lines appear straight in undistorted image
- [ ] No artifacts at image edges

---

## Phase 2: Camera-LiDAR Calibration (60-120 min)

### Step 2.1: Setup Calibration Target

**Objective:** Find rigid transform between camera and LiDAR.

**Target requirements:**
- Checkerboard with known dimensions
- Large enough to be seen by both sensors
- High contrast for camera, reflective for LiDAR

### Step 2.2: Record Calibration Bag

```bash
# Start all sensors
ros2 launch my_robot_bringup sensors.launch.py

# Record calibration data
ros2 bag record \
  /camera/color/image_raw \
  /camera/color/camera_info \
  /lidar/points \
  -o calibration_bag

# Move checkerboard to various poses
# - Different distances (1m to 5m)
# - Different angles
# - Cover camera FOV and LiDAR FOV overlap
```

**Collect 20-30 different poses**

### Step 2.3: Run Calibration

**Option 1: lidar_camera_calibration (ROS2)**

```bash
# Install
sudo apt install ros-$ROS_DISTRO-lidar-camera-calibration

# Run calibration
ros2 launch lidar_camera_calibration calibration.launch.py \
  camera_topic:=/camera/color/image_raw \
  lidar_topic:=/lidar/points \
  bag_file:=./calibration_bag/calibration_bag_0.db3
```

**Option 2: Manual PnP with known correspondences**

```python
import cv2
import numpy as np
import open3d as o3d

def calibrate_camera_lidar(camera_points_2d, lidar_points_3d, 
                          camera_matrix, dist_coeffs):
    """
    Calibrate camera-LiDAR extrinsics using PnP.
    
    camera_points_2d: Nx2 array of image coordinates
    lidar_points_3d: Nx3 array of LiDAR coordinates
    """
    # Solve PnP
    success, rvec, tvec, inliers = cv2.solvePnPRansac(
        lidar_points_3d,
        camera_points_2d,
        camera_matrix,
        dist_coeffs,
        iterationsCount=1000,
        reprojectionError=3.0,
        confidence=0.99
    )
    
    if not success:
        raise RuntimeError("PnP failed")
    
    # Convert to transformation matrix
    R, _ = cv2.Rodrigues(rvec)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = tvec.flatten()
    
    return T
```

### Step 2.4: Verify Calibration

**Project LiDAR points to image:**
```python
def project_lidar_to_image(lidar_points, T_cam_lidar, camera_matrix):
    """Project LiDAR points to camera image."""
    # Transform to camera frame
    points_cam = (T_cam_lidar[:3, :3] @ lidar_points.T).T + T_cam_lidar[:3, 3]
    
    # Project to image
    points_2d = (camera_matrix @ points_cam.T).T
    points_2d = points_2d[:, :2] / points_2d[:, 2:3]
    
    return points_2d

# Visualize
import matplotlib.pyplot as plt

img = cv2.imread('test_image.jpg')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

points_2d = project_lidar_to_image(lidar_points, T_cam_lidar, camera_matrix)

plt.imshow(img_rgb)
plt.scatter(points_2d[:, 0], points_2d[:, 1], c='r', s=1)
plt.show()
```

**Checkpoint:**
- [ ] LiDAR points align with image edges
- [ ] Reprojection error < 5 pixels
- [ ] Transformation physically reasonable

---

## Phase 3: IMU Calibration (30-60 min)

### Step 3.1: IMU Intrinsic Calibration

**Objective:** Determine accelerometer and gyroscope biases and scale factors.

**Static calibration (biases):**
```bash
# Record IMU data while stationary
ros2 topic echo /imu/data > static_imu.txt

# Let it run for 60 seconds
```

**Calculate biases:**
```python
import numpy as np

# Parse IMU data (simplified)
acc_data = []  # Extract accelerometer readings
gyro_data = []  # Extract gyroscope readings

# Calculate mean (bias)
acc_bias = np.mean(acc_data, axis=0)
gyro_bias = np.mean(gyro_data, axis=0)

print(f"Accelerometer bias: {acc_bias}")
print(f"Gyroscope bias: {gyro_bias}")

# Expected: acc_bias ≈ [0, 0, 9.81] (gravity in Z)
# Expected: gyro_bias ≈ [0, 0, 0]
```

### Step 3.2: IMU-Camera Calibration (if using visual-inertial SLAM)

**Use Kalibr or similar:**

```bash
# Install Kalibr
# https://github.com/ethz-asl/kalibr

# Record calibration data with IMU and camera
kalibr_bagcreater --folder dataset/ --output-bag calibration.bag

# Run calibration
kalibr_calibrate_imu_camera \
  --target checkerboard.yaml \
  --cam camchain.yaml \
  --imu imu.yaml \
  --bag calibration.bag
```

**Checkpoint:**
- [ ] IMU biases within expected range
- [ ] Noise characteristics known
- [ ] Time synchronization verified

---

## Phase 4: Wheel Odometry Calibration (30-45 min)

### Step 4.1: Wheel Radius Calibration

**Objective:** Calibrate wheel radius for accurate odometry.

**Method: Drive known distance**
```bash
# Mark start position on floor
# Drive robot exactly 2 meters forward (measure with tape)

# Check odometry
ros2 topic echo /odom --once
# Record position.x

# Calculate correction factor
actual_distance = 2.0
measured_distance = <from_odom>
correction_factor = actual_distance / measured_distance

# Update wheel radius in controller config
new_radius = old_radius * correction_factor
```

### Step 4.2: Wheel Separation Calibration

**Objective:** Calibrate wheel separation for accurate rotation.

**Method: Rotate 360 degrees**
```bash
# Place robot with clear marker pointing forward
# Command rotation

ros2 topic pub /cmd_vel geometry_msgs/Twist \
  '{linear: {x: 0.0}, angular: {z: 0.5}}'

# Rotate for exactly 2π / 0.5 = 12.56 seconds
# Stop

# Check if marker returned to original orientation
# If not, adjust wheel separation

# Correction:
# If over-rotated: increase wheel separation
# If under-rotated: decrease wheel separation
```

---

## Phase 5: Multi-Sensor Validation (30-45 min)

### Step 5.1: TF Tree Verification

```bash
# Visualize TF tree
ros2 run tf2_tools view_frames

# Check all frames are connected
# Verify timestamps (no future dated transforms)
```

### Step 5.2: Sensor Fusion Test

**Launch robot_localization:**
```yaml
# config/ekf.yaml
ekf_filter_node:
  ros__parameters:
    frequency: 50.0
    
    odom0: /wheel_odom
    odom0_config: [true, true, false, false, false, true,
                   true, false, false, false, false, true,
                   false, false, false]
    
    imu0: /imu/data
    imu0_config: [false, false, false, true, true, true,
                  false, false, false, true, true, true,
                  true, true, true]
```

```bash
ros2 launch robot_localization ekf.launch.py
```

### Step 5.3: End-to-End Validation

**Test 1: Square path**
- Drive 1m forward, turn 90°, repeat 4 times
- Check final position matches start

**Test 2: Return to origin**
- Navigate to goal 5m away
- Navigate back to origin
- Check position error < 10cm

---

## Calibration Summary

### Files to Save

| Calibration | File | Location |
|-------------|------|----------|
| Camera intrinsic | ost.yaml | `config/camera/` |
| Camera-LiDAR extrinsic | T_cam_lidar.npy | `config/calibration/` |
| IMU biases | imu_biases.yaml | `config/imu/` |
| Odometry params | odometry.yaml | `config/control/` |

### Validation Checklist

- [ ] Camera intrinsics: reprojection error < 0.5 px
- [ ] Camera-LiDAR: alignment verified visually
- [ ] IMU: biases within spec, noise characterized
- [ ] Odometry: < 2% distance error, < 2° rotation error
- [ ] Sensor fusion: smooth combined output
- [ ] End-to-end: returns to origin within 10cm

---

## Troubleshooting

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| High reprojection error | Poor calibration data | Collect more varied poses |
| LiDAR-camera misalignment | Wrong correspondences | Check target visibility in both sensors |
| IMU drift | Temperature changes | Calibrate at operating temperature |
| Odometry error varies | Wheel slip | Calibrate on same surface type |
| TF errors | Time sync issues | Check NTP/chrony, use message_filters |

---

## Resources

- Related skills: `camera-vision`, `lidar-pointcloud`, `sensor-fusion-slam`
- Tools: Kalibr, OpenCV, camera_calibration package
- Phase 2 deliverables complete