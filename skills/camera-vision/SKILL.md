---
name: camera-vision
description: Camera calibration, computer vision, and depth processing for robotics including OpenCV, intrinsic/extrinsic calibration, hand-eye calibration, object detection, tracking, and RGB-D pipelines. Use when working with cameras, depth sensors, or visual perception.
category: perception
tags: [camera, vision, opencv, calibration, depth, detection, tracking]
version: "1.0.0"
---

# Camera Vision

Camera-based perception is fundamental to robotics. This skill covers camera calibration, OpenCV-based image processing, depth sensor handling, and integration with robotic systems.

## When to Use

- Calibrating cameras (intrinsic, extrinsic, hand-eye)
- Setting up RGB or RGB-D cameras (RealSense, ZED, OAK-D)
- Implementing object detection and tracking
- Processing depth images and point clouds
- Configuring camera streaming and synchronization
- Debugging perception pipeline issues
- Converting between 2D pixels and 3D world coordinates

## Quick Start

```bash
# Install dependencies
pip install opencv-python opencv-contrib-python numpy

# For RealSense
pip install pyrealsense2
sudo apt install ros-humble-realsense2-camera

# For ZED
pip install pyzed
```

```python
import cv2
import numpy as np

# Open camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Capture frame
ret, frame = cap.read()
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Display
cv2.imshow('Camera', frame)
cv2.waitKey(0)
cap.release()
```

## Core Concepts

### Sensor and device reference

| Sensor type | Output | Rate | Best for |
|-------------|--------|------|----------|
| RGB camera | (H,W,3) uint8 | 30–120 Hz | Detection, tracking, visual servoing |
| Stereo | (H,W,3)×2 | 30–90 Hz | Dense depth (passive) |
| Structured light / ToF | (H,W) float + RGB | 30 Hz | Indoor, short–medium range |
| Event camera | Events (x,y,t,p) | µs | High-speed, HDR |

| Device | SDK/Driver | ROS2 package |
|--------|------------|--------------|
| Intel RealSense | pyrealsense2 | realsense2_camera |
| Stereolabs ZED | pyzed | zed_wrapper |
| Luxonis OAK-D | depthai | depthai_ros |
| USB webcam | OpenCV VideoCapture | usb_cam / v4l2_camera |

### 1. Camera Calibration

**Pinhole Camera Model:**
```
Projection: [u, v, 1]^T = K @ [R | t] @ [X, Y, Z, 1]^T

K = [ fx   0   cx ]      fx, fy = focal lengths (pixels)
    [  0  fy   cy ]      cx, cy = principal point
    [  0   0    1 ]
```

**Intrinsic Calibration:**
```python
import cv2
import numpy as np

class IntrinsicCalibrator:
    def __init__(self, board_size=(9, 6), square_size_m=0.025):
        self.board_size = board_size
        self.square_size = square_size_m
        self.objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[
            0:board_size[0], 0:board_size[1]
        ].T.reshape(-1, 2) * square_size_m

    def calibrate(self, images):
        obj_points = []
        img_points = []
        
        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(
                gray, self.board_size,
                cv2.CALIB_CB_ADAPTIVE_THRESH |
                cv2.CALIB_CB_NORMALIZE_IMAGE
            )
            
            if found:
                corners = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1),
                    (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                obj_points.append(self.objp)
                img_points.append(corners)
        
        ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, gray.shape[::-1], None, None)
        
        return K, dist, ret

# Usage
calibrator = IntrinsicCalibrator()
K, dist, error = calibrator.calibrate(calibration_images)
print(f"Calibration RMS error: {error:.3f} px")
print(f"Camera matrix:\n{K}")
```

**Hand-Eye Calibration:**
```python
def calibrate_hand_eye(R_gripper2base, t_gripper2base, 
                       R_target2cam, t_target2cam):
    """Calibrate camera-to-robot transform."""
    R, t = cv2.calibrateHandEye(
        R_gripper2base, t_gripper2base,
        R_target2cam, t_target2cam,
        method=cv2.CALIB_HAND_EYE_TSAI
    )
    T_cam2gripper = np.eye(4)
    T_cam2gripper[:3, :3] = R
    T_cam2gripper[:3, 3] = t.flatten()
    return T_cam2gripper
```

### 2. Image Undistortion

```python
class ImageUndistorter:
    def __init__(self, K, dist, image_size, alpha=0.0):
        self.new_K, self.roi = cv2.getOptimalNewCameraMatrix(
            K, dist, image_size, alpha, image_size)
        self.map1, self.map2 = cv2.initUndistortRectifyMap(
            K, dist, None, self.new_K, image_size, cv2.CV_16SC2)

    def undistort(self, image):
        return cv2.remap(image, self.map1, self.map2, 
                        interpolation=cv2.INTER_LINEAR)
```

### 3. Depth Processing

```python
class DepthProcessor:
    def __init__(self, depth_scale=0.001, min_depth=0.1, max_depth=3.0):
        self.depth_scale = depth_scale
        self.min_depth = min_depth
        self.max_depth = max_depth

    def process(self, raw_depth):
        depth = raw_depth.astype(np.float32) * self.depth_scale
        
        # Range filtering
        depth[(depth < self.min_depth) | (depth > self.max_depth)] = 0
        
        # Remove flying pixels at edges
        depth = self._remove_flying_pixels(depth)
        
        # Fill small holes
        depth = self._fill_holes(depth)
        
        return depth

    def _remove_flying_pixels(self, depth, threshold=0.05):
        dx = np.abs(np.diff(depth, axis=1, prepend=0))
        dy = np.abs(np.diff(depth, axis=0, prepend=0))
        gradient = np.sqrt(dx**2 + dy**2)
        depth[gradient > threshold] = 0
        return depth

    def _fill_holes(self, depth, max_hole_size=10):
        mask = (depth == 0).astype(np.uint8)
        kernel = np.ones((max_hole_size, max_hole_size), np.uint8)
        small_holes = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        small_holes = small_holes & mask
        
        if small_holes.any():
            d_norm = (depth * 1000).astype(np.uint16)
            filled = cv2.inpaint(d_norm, small_holes, max_hole_size, cv2.INPAINT_NS)
            depth = np.where(small_holes, filled.astype(np.float32) / 1000, depth)
        return depth
```

### 4. 2D to 3D Backprojection

```python
def backproject_pixel(pixel, depth, K):
    """Convert 2D pixel + depth to 3D point."""
    u, v = pixel
    fx, fy = K[0, 0], K[1, 1]
    cx, cy = K[0, 2], K[1, 2]
    
    Z = depth
    X = (u - cx) * Z / fx
    Y = (v - cy) * Z / fy
    
    return np.array([X, Y, Z])

# Sample depth in patch for robustness
def get_depth_at_point(depth_image, center, patch_size=5):
    cy, cx = int(center[1]), int(center[0])
    h, w = depth_image.shape
    cy = np.clip(cy, patch_size, h - patch_size - 1)
    cx = np.clip(cx, patch_size, w - patch_size - 1)
    
    patch = depth_image[cy-patch_size:cy+patch_size+1, 
                        cx-patch_size:cx+patch_size+1]
    valid = patch[patch > 0]
    return np.median(valid) if len(valid) > 0 else None
```

## Common Patterns

### Pattern 1: Object Detection with Depth

```python
class RobotObjectDetector:
    def __init__(self, model, K, workspace_bounds=None, min_confidence=0.5):
        self.model = model
        self.K = K
        self.workspace_bounds = workspace_bounds
        self.min_confidence = min_confidence

    def detect(self, rgb, depth=None):
        detections = self.model(rgb)
        results = []
        
        for det in detections:
            if det.confidence < self.min_confidence:
                continue
            
            if depth is not None:
                # Get 3D position from depth
                z = get_depth_at_point(depth, det.center)
                if z is not None:
                    det.position_3d = backproject_pixel(det.center, z, self.K)
                    
                    # Filter by workspace
                    if self.workspace_bounds:
                        if not self.workspace_bounds.contains(det.position_3d):
                            continue
            
            results.append(det)
        
        return results
```

### Pattern 2: Fiducial Marker Detection

```python
class FiducialDetector:
    def __init__(self, K, dist, marker_size_m=0.05):
        self.K = K
        self.dist = dist
        self.marker_size = marker_size_m
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(
            cv2.aruco.DICT_APRILTAG_36h11)
        self.detector = cv2.aruco.ArucoDetector(
            self.aruco_dict, cv2.aruco.DetectorParameters())

    def detect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
        results = []
        if ids is not None:
            for i, marker_id in enumerate(ids.flatten()):
                rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                    corners[i:i+1], self.marker_size, self.K, self.dist)
                
                R, _ = cv2.Rodrigues(rvecs[0])
                T = np.eye(4)
                T[:3, :3] = R
                T[:3, 3] = tvecs[0].flatten()
                
                results.append({
                    'marker_id': int(marker_id),
                    'pose': T,
                    'distance': np.linalg.norm(tvecs[0])
                })
        return results
```

### Pattern 3: Camera Streaming with Threading

```python
import threading
from collections import deque

class CameraStream:
    def __init__(self, camera, buffer_size=2, name="camera"):
        self.camera = camera
        self.name = name
        self._buffer = deque(maxlen=buffer_size)
        self._lock = threading.Lock()
        self._running = False

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        while self._running:
            frame = self.camera.capture()
            timestamp = time.time()
            
            with self._lock:
                self._buffer.append({
                    'data': frame,
                    'timestamp': timestamp
                })

    def get_latest(self):
        with self._lock:
            return self._buffer[-1] if self._buffer else None

    def stop(self):
        self._running = False
        self._thread.join(timeout=2.0)
```

## Anti-Patterns

### ❌ Not validating calibration
Using nominal intrinsics or assuming cameras are calibrated causes systematic errors.

**What happens:** 3D positions are wrong, hand-eye calibration fails, robot misses targets.

### ✅ Always calibrate and validate
```python
# Load actual calibration from file
K, dist = load_calibration('camera_calib.yaml')
# Verify with known object before use
```

### ❌ Single-pixel depth sampling
Using a single depth pixel is noisy and may hit a hole.

**What happens:** Erratic 3D positions, detection jitter.

### ✅ Sample neighborhood with median
```python
patch = depth[cy-2:cy+3, cx-2:cx+3]
valid = patch[patch > 0]
z = np.median(valid) if len(valid) > 0 else None
```

### ❌ Ignoring timestamp synchronization
Using capture time instead of sensor timestamp causes fusion errors.

**What happens:** Camera and LiDAR data don't align, bad multi-sensor fusion.

### ✅ Timestamp at capture
```python
frame = camera.capture()
timestamp = time.monotonic()  # Or better: sensor timestamp
```

## Configuration Reference

### Calibration Quality Metrics

| Metric | Target | Acceptable |
|--------|--------|------------|
| Intrinsic RMS | < 0.3 px | < 0.5 px |
| Stereo RMS | < 0.5 px | < 1.0 px |
| Hand-eye error | < 5 mm | < 10 mm |

### Common Camera Specs

| Camera | Resolution | FOV | Depth Range |
|--------|-----------|-----|-------------|
| RealSense D435 | 1280x720 | 87° | 0.3-3m |
| RealSense D455 | 1280x720 | 87° | 0.6-6m |
| ZED 2i | 1920x1080 | 110° | 0.3-20m |
| OAK-D | 1920x1080 | 81° | 0.7-10m |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Undistorted image has black borders | Alpha parameter too low | Increase alpha in getOptimalNewCameraMatrix |
| Depth has holes | Object too close/far, reflective surface | Check min/max depth, avoid specular surfaces |
| Detection flickers | No temporal filtering | Add tracking or filter across frames |
| High reprojection error | Bad calibration coverage | Recalibrate with better coverage |
| Hand-eye calibration fails | Insufficient pose diversity | Use more poses with rotation variation |

## Workflow Integration

- **Before this:** Use `robot-modeling` to define camera mounting frames
- **After this:** Use `sensor-fusion-slam` for multi-sensor integration
- **Parallel with:** Use `gazebo` for simulation-based testing
- **Before deployment:** Validate with `safety-systems` checks

## Advanced Topics

### Multi-Camera Calibration

Calibrating stereo or multi-camera rigs:

```python
class StereoCalibrator:
    def __init__(self, board_size=(9, 6), square_size=0.025):
        self.board_size = board_size
        self.square_size = square_size
        self.objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[
            0:board_size[0], 0:board_size[1]
        ].T.reshape(-1, 2) * square_size

    def calibrate_stereo(self, left_images, right_images, K1, D1, K2, D2):
        obj_points = []
        left_points = []
        right_points = []
        
        for left_img, right_img in zip(left_images, right_images):
            left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
            right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
            
            left_found, left_corners = cv2.findChessboardCorners(
                left_gray, self.board_size, None)
            right_found, right_corners = cv2.findChessboardCorners(
                right_gray, self.board_size, None)
            
            if left_found and right_found:
                obj_points.append(self.objp)
                left_points.append(left_corners)
                right_points.append(right_corners)
        
        # Calibrate stereo pair
        ret, K1, D1, K2, D2, R, T, E, F = cv2.stereoCalibrate(
            obj_points, left_points, right_points,
            K1, D1, K2, D2,
            left_gray.shape[::-1],
            flags=cv2.CALIB_FIX_INTRINSIC
        )
        
        # Compute rectification transforms
        R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
            K1, D1, K2, D2,
            left_gray.shape[::-1],
            R, T
        )
        
        return {
            'R': R, 'T': T,
            'R1': R1, 'R2': R2,
            'P1': P1, 'P2': P2,
            'Q': Q
        }
```

### Image Preprocessing Pipeline

```python
class ImagePreprocessor:
    def __init__(self, target_size=(640, 480)):
        self.target_size = target_size

    def preprocess(self, image):
        # Resize maintaining aspect ratio
        h, w = image.shape[:2]
        scale = min(self.target_size[0] / w, self.target_size[1] / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(image, (new_w, new_h))
        
        # Pad to target size
        padded = np.zeros((*self.target_size[::-1], 3), dtype=np.uint8)
        y_offset = (self.target_size[1] - new_h) // 2
        x_offset = (self.target_size[0] - new_w) // 2
        padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        # Normalize
        normalized = padded.astype(np.float32) / 255.0
        
        # Standard ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        normalized = (normalized - mean) / std
        
        return normalized
```

### Camera-LiDAR Fusion

```python
class CameraLiDARFusion:
    def __init__(self, K, T_cam_lidar, image_size):
        self.K = K
        self.T = T_cam_lidar
        self.image_size = image_size

    def project_lidar_to_image(self, lidar_points):
        """Project 3D LiDAR points to 2D image."""
        # Transform to camera frame
        pts_cam = (self.T @ np.hstack([
            lidar_points, np.ones((len(lidar_points), 1))
        ]).T).T
        
        # Project to image
        valid = pts_cam[:, 2] > 0
        pixels = np.zeros((len(lidar_points), 2))
        
        pixels[valid, 0] = (
            self.K[0, 0] * pts_cam[valid, 0] / pts_cam[valid, 2] + 
            self.K[0, 2]
        )
        pixels[valid, 1] = (
            self.K[1, 1] * pts_cam[valid, 1] / pts_cam[valid, 2] + 
            self.K[1, 2]
        )
        
        # Check bounds
        w, h = self.image_size
        in_bounds = (
            valid & 
            (pixels[:, 0] >= 0) & (pixels[:, 0] < w) &
            (pixels[:, 1] >= 0) & (pixels[:, 1] < h)
        )
        
        return pixels, in_bounds
```

## Further Reading

- [OpenCV Documentation](https://docs.opencv.org/)
- [Camera Calibration Tutorial](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)
- [RealSense ROS2](https://github.com/IntelRealSense/realsense-ros)
- Related skills: `lidar-pointcloud`, `sensor-fusion-slam`, `gazebo`

## Changelog

### v1.0.0 (2026-03-07)
- Initial release
- Covers calibration, OpenCV, depth processing, detection
