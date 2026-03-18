---
name: lidar-pointcloud
description: LiDAR and 3D point cloud processing using PCL and Open3D including filtering, segmentation, registration (ICP, NDT), feature extraction, and obstacle detection. Use when processing LiDAR data or 3D perception.
category: perception
tags: [lidar, pointcloud, pcl, open3d, filtering, segmentation, icp, registration]
version: "1.0.0"
---

# LiDAR & Point Cloud Processing

Point clouds are the fundamental 3D representation in robotics. This skill covers LiDAR data processing, point cloud filtering, segmentation, registration, and feature extraction using PCL (Point Cloud Library) and Open3D.

## When to Use

- Processing LiDAR scans for obstacle detection
- Filtering and downsampling point clouds
- Segmenting ground planes and objects
- Registering point clouds (ICP, NDT, GICP)
- Extracting features from 3D data
- Creating 3D maps from LiDAR data
- Implementing obstacle detection for navigation
- Fusing LiDAR with camera data

## Quick Start

```bash
# Install PCL and ROS2 packages
sudo apt install ros-$ROS_DISTRO-pcl-ros
sudo apt install ros-$ROS_DISTRO-pcl-conversions
sudo apt install python3-open3d

# View point cloud
ros2 run rviz2 rviz2  # Add PointCloud2 display

# Convert bag to PCD
ros2 run pcl_ros bag_to_pcd input.bag /lidar/points output/
```

**Python with Open3D:**
```python
import open3d as o3d
import numpy as np

# Load point cloud
pcd = o3d.io.read_point_cloud("scan.pcd")

# Visualize
o3d.visualization.draw_geometries([pcd])

# Downsample
downsampled = pcd.voxel_down_sample(voxel_size=0.05)

# Save
o3d.io.write_point_cloud("downsampled.pcd", downsampled)
```

## Core Concepts

### LiDAR and depth device reference

| Device | Type | SDK/Driver | ROS2 package |
|--------|------|------------|--------------|
| Velodyne | Spinning LiDAR | velodyne_driver | velodyne |
| Ouster | Spinning LiDAR | ouster-sdk | ros2_ouster |
| Livox | Solid-state LiDAR | livox_sdk | livox_ros2_driver |
| Intel RealSense | Structured light / ToF | pyrealsense2 | realsense2_camera (depth) |
| Stereolabs ZED | Stereo + IMU | pyzed | zed_wrapper |

Spinning LiDAR: 0.5–200 m, 10–20 Hz. Solid-state: 0.5–200 m, 10–30 Hz. Use sensor QoS (best-effort, depth 1–5) for LiDAR topics.

### 1. Point Cloud Representation

**ROS2 Message (sensor_msgs/PointCloud2):**
```python
from sensor_msgs.msg import PointCloud2, PointField
import numpy as np
import struct

def create_pointcloud2(points, stamp, frame_id='lidar'):
    """Create PointCloud2 from numpy array."""
    header = std_msgs.msg.Header()
    header.stamp = stamp
    header.frame_id = frame_id
    
    fields = [
        PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
        PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
        PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
    ]
    
    # Convert to bytes
    buffer = []
    for point in points:
        buffer.append(struct.pack('fff', point[0], point[1], point[2]))
    
    return PointCloud2(
        header=header,
        height=1,
        width=len(points),
        fields=fields,
        is_bigendian=False,
        point_step=12,
        row_step=12 * len(points),
        data=b''.join(buffer),
        is_dense=True
    )
```

**PCL Point Types:**
```cpp
// Common PCL point types
pcl::PointXYZ          // x, y, z
pcl::PointXYZI         // x, y, z, intensity
pcl::PointXYZRGB       // x, y, z, rgb
pcl::PointXYZRGBA      // x, y, z, rgba
pcl::PointNormal       // x, y, z, normal_x, normal_y, normal_z, curvature
pcl::PointXYZRGBNormal // Combined color + normal
```

### 2. Filtering

**Voxel Grid Downsampling:**
```python
import open3d as o3d

def voxel_downsample(pcd, voxel_size=0.05):
    """Downsample point cloud using voxel grid."""
    return pcd.voxel_down_sample(voxel_size)

# With PCL (C++)
# pcl::VoxelGrid<pcl::PointXYZ> voxel_filter;
# voxel_filter.setInputCloud(cloud);
# voxel_filter.setLeafSize(0.05f, 0.05f, 0.05f);
# voxel_filter.filter(*cloud_filtered);
```

**Statistical Outlier Removal:**
```python
def remove_outliers(pcd, nb_neighbors=20, std_ratio=2.0):
    """Remove statistical outliers."""
    cl, ind = pcd.remove_statistical_outlier(
        nb_neighbors=nb_neighbors,
        std_ratio=std_ratio
    )
    return pcd.select_by_index(ind)

# PCL equivalent
# pcl::StatisticalOutlierRemoval<pcl::PointXYZ> sor;
# sor.setInputCloud(cloud);
# sor.setMeanK(50);
# sor.setStddevMulThresh(1.0);
# sor.filter(*cloud_filtered);
```

**PassThrough Filter (ROI extraction):**
```python
def passthrough_filter(pcd, axis='z', min_val=0.0, max_val=2.0):
    """Filter points within axis range."""
    points = np.asarray(pcd.points)
    
    if axis == 'x':
        mask = (points[:, 0] >= min_val) & (points[:, 0] <= max_val)
    elif axis == 'y':
        mask = (points[:, 1] >= min_val) & (points[:, 1] <= max_val)
    else:  # z
        mask = (points[:, 2] >= min_val) & (points[:, 2] <= max_val)
    
    filtered = o3d.geometry.PointCloud()
    filtered.points = o3d.utility.Vector3dVector(points[mask])
    return filtered
```

**Radius Outlier Removal:**
```python
def radius_outlier_removal(pcd, nb_points=16, radius=0.05):
    """Remove points with few neighbors within radius."""
    cl, ind = pcd.remove_radius_outlier(
        nb_points=nb_points,
        radius=radius
    )
    return pcd.select_by_index(ind)
```

### 3. Segmentation

**Ground Plane Segmentation (RANSAC):**
```python
def segment_ground(pcd, distance_threshold=0.01, ransac_n=3, num_iterations=1000):
    """Segment ground plane using RANSAC."""
    plane_model, inliers = pcd.segment_plane(
        distance_threshold=distance_threshold,
        ransac_n=ransac_n,
        num_iterations=num_iterations
    )
    
    [a, b, c, d] = plane_model
    print(f"Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")
    
    ground_cloud = pcd.select_by_index(inliers)
    obstacle_cloud = pcd.select_by_index(inliers, invert=True)
    
    return ground_cloud, obstacle_cloud, plane_model

# PCL equivalent
# pcl::SACSegmentation<pcl::PointXYZ> seg;
# seg.setOptimizeCoefficients(true);
# seg.setModelType(pcl::SACMODEL_PLANE);
# seg.setMethodType(pcl::SAC_RANSAC);
# seg.setDistanceThreshold(0.01);
# seg.segment(*inliers, *coefficients);
```

**Euclidean Cluster Extraction:**
```python
def cluster_objects(pcd, eps=0.05, min_points=10):
    """Cluster points using DBSCAN."""
    labels = np.array(pcd.cluster_dbscan(eps=eps, min_points=min_points))
    
    max_label = labels.max()
    print(f"Found {max_label + 1} clusters")
    
    colors = plt.get_cmap("tab20")(labels / (max_label if max_label > 0 else 1))
    colors[labels < 0] = 0  # Noise points in black
    pcd.colors = o3d.utility.Vector3dVector(colors[:, :3])
    
    return pcd, labels

# With PCL (C++)
# pcl::EuclideanClusterExtraction<pcl::PointXYZ> ec;
# ec.setClusterTolerance(0.02); // 2cm
# ec.setMinClusterSize(100);
# ec.setMaxClusterSize(25000);
# ec.setSearchMethod(tree);
# ec.setInputCloud(cloud);
# ec.extract(cluster_indices);
```

**Region Growing Segmentation:**
```python
def region_growing_segmentation(pcd):
    """Segment based on normal consistency."""
    pcd.estimate_normals()
    
    # Use PCL for region growing
    # pcl::RegionGrowing<pcl::PointXYZ, pcl::Normal> reg;
    # reg.setMinClusterSize(50);
    # reg.setMaxClusterSize(1000000);
    # reg.setSearchMethod(tree);
    # reg.setNumberOfNeighbours(30);
    # reg.setInputCloud(cloud);
    # reg.setInputNormals(normals);
    # reg.setSmoothnessThreshold(3.0 / 180.0 * M_PI);
    # reg.setCurvatureThreshold(1.0);
```

### 4. Registration

**ICP (Iterative Closest Point):**
```python
def icp_registration(source, target, threshold=0.02, trans_init=np.eye(4)):
    """Register source to target using ICP."""
    reg_p2p = o3d.pipelines.registration.registration_icp(
        source, target, threshold, trans_init,
        o3d.pipelines.registration.TransformationEstimationPointToPoint()
    )
    
    print(f"Fitness: {reg_p2p.fitness:.4f}")
    print(f"Inlier RMSE: {reg_p2p.inlier_rmse:.4f}")
    print(f"Transformation:\n{reg_p2p.transformation}")
    
    return reg_p2p

# Point-to-Plane ICP (better for structured scenes)
def icp_point_to_plane(source, target, threshold=0.02):
    """ICP with point-to-plane metric."""
    # Estimate normals for target
    target.estimate_normals()
    
    reg_p2l = o3d.pipelines.registration.registration_icp(
        source, target, threshold, np.eye(4),
        o3d.pipelines.registration.TransformationEstimationPointToPlane()
    )
    
    return reg_p2l
```

**Generalized ICP (GICP):**
```cpp
// PCL GICP
pcl::GeneralizedIterativeClosestPoint<pcl::PointXYZ, pcl::PointXYZ> gicp;
gicp.setInputSource(source_cloud);
gicp.setInputTarget(target_cloud);
gicp.align(*aligned_cloud);
```

**NDT (Normal Distributions Transform):**
```python
def ndt_registration(source, target, voxel_size=1.0):
    """Register using NDT."""
    # Downsample for faster computation
    source_down = source.voxel_down_sample(voxel_size)
    target_down = target.voxel_down_sample(voxel_size)
    
    # PCL NDT
    # pcl::NormalDistributionsTransform<pcl::PointXYZ, pcl::PointXYZ> ndt;
    # ndt.setTransformationEpsilon(0.01);
    # ndt.setStepSize(0.1);
    # ndt.setResolution(1.0);
    # ndt.setMaximumIterations(35);
    # ndt.setInputSource(source_down);
    # ndt.setInputTarget(target_down);
    # ndt.align(*output_cloud, init_guess);
```

**Fast Global Registration (FPFH-based):**
```python
def fast_global_registration(source, target, voxel_size=0.05):
    """Fast registration using FPFH features."""
    # Downsample
    source_down = source.voxel_down_sample(voxel_size)
    target_down = target.voxel_down_sample(voxel_size)
    
    # Estimate normals
    source_down.estimate_normals()
    target_down.estimate_normals()
    
    # Compute FPFH features
    source_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        source_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 5, max_nn=100)
    )
    target_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        target_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 5, max_nn=100)
    )
    
    # Fast global registration
    result = o3d.pipelines.registration.registration_fast_based_on_feature_matching(
        source_down, target_down, source_fpfh, target_fpfh,
        o3d.pipelines.registration.FastGlobalRegistrationOption(
            maximum_correspondence_distance=voxel_size * 0.3
        )
    )
    
    return result
```

### 5. Feature Extraction

**FPFH (Fast Point Feature Histograms):**
```python
def compute_fpfh(pcd, voxel_size):
    """Compute FPFH features."""
    pcd_down = pcd.voxel_down_sample(voxel_size)
    pcd_down.estimate_normals()
    
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 5, max_nn=100)
    )
    
    return pcd_down, fpfh
```

**Normal Estimation:**
```python
def estimate_normals(pcd, radius=0.1, max_nn=30):
    """Estimate point cloud normals."""
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(
            radius=radius, max_nn=max_nn
        )
    )
    
    # Orient normals consistently
    pcd.orient_normals_consistent_tangent_plane(100)
    
    return pcd
```

## Common Patterns

### Pattern 1: ROS2 Point Cloud Subscriber

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
import numpy as np
import open3d as o3d

class PointCloudProcessor(Node):
    """Process incoming point clouds."""
    
    def __init__(self):
        super().__init__('pointcloud_processor')
        
        self.sub = self.create_subscription(
            PointCloud2,
            '/lidar/points',
            self.pointcloud_callback,
            10
        )
        
        self.pub = self.create_publisher(
            PointCloud2,
            '/processed_points',
            10
        )
        
    def pointcloud_callback(self, msg):
        """Convert ROS message to Open3D point cloud."""
        # Convert to numpy array
        points = point_cloud2.read_points_numpy(
            msg, field_names=("x", "y", "z")
        )
        
        # Create Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Process
        processed = self.process(pcd)
        
        # Convert back and publish
        out_msg = self.o3d_to_ros(processed, msg.header)
        self.pub.publish(out_msg)
    
    def process(self, pcd):
        """Apply processing pipeline."""
        # Voxel downsampling
        pcd = pcd.voxel_down_sample(voxel_size=0.05)
        
        # Remove outliers
        pcd, _ = pcd.remove_statistical_outlier(
            nb_neighbors=20, std_ratio=2.0
        )
        
        # Ground removal
        _, obstacles, _ = self.segment_ground(pcd)
        
        return obstacles
    
    def segment_ground(self, pcd):
        """RANSAC ground segmentation."""
        plane_model, inliers = pcd.segment_plane(
            distance_threshold=0.01,
            ransac_n=3,
            num_iterations=1000
        )
        ground = pcd.select_by_index(inliers)
        obstacles = pcd.select_by_index(inliers, invert=True)
        return ground, obstacles, plane_model
    
    def o3d_to_ros(self, pcd, header):
        """Convert Open3D point cloud to ROS message."""
        points = np.asarray(pcd.points)
        
        msg = PointCloud2()
        msg.header = header
        msg.height = 1
        msg.width = len(points)
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = 12 * len(points)
        msg.is_dense = True
        
        buffer = []
        for point in points:
            buffer.append(struct.pack('fff', point[0], point[1], point[2]))
        msg.data = b''.join(buffer)
        
        return msg
```

### Pattern 2: Obstacle Detection Pipeline

```python
class ObstacleDetector:
    """Detect obstacles from LiDAR data."""
    
    def __init__(self, ground_threshold=0.1, cluster_tolerance=0.3):
        self.ground_threshold = ground_threshold
        self.cluster_tolerance = cluster_tolerance
        
    def detect(self, pcd):
        """Detect obstacles in point cloud."""
        # 1. Preprocess
        pcd = self.preprocess(pcd)
        
        # 2. Ground segmentation
        ground, obstacles, _ = self.segment_ground(pcd)
        
        # 3. Cluster obstacles
        clusters = self.cluster_obstacles(obstacles)
        
        # 4. Compute bounding boxes
        detections = []
        for cluster in clusters:
            bbox = self.compute_bbox(cluster)
            detections.append({
                'points': cluster,
                'bbox': bbox,
                'center': bbox.get_center(),
                'extent': bbox.get_extent()
            })
        
        return detections
    
    def preprocess(self, pcd):
        """Preprocess point cloud."""
        # Downsample
        pcd = pcd.voxel_down_sample(0.05)
        
        # Remove outliers
        pcd, _ = pcd.remove_statistical_outlier(20, 2.0)
        
        # Filter height range
        points = np.asarray(pcd.points)
        mask = (points[:, 2] > -0.5) & (points[:, 2] < 2.0)
        filtered = o3d.geometry.PointCloud()
        filtered.points = o3d.utility.Vector3dVector(points[mask])
        
        return filtered
    
    def cluster_obstacles(self, obstacles):
        """Cluster obstacle points."""
        labels = np.array(obstacles.cluster_dbscan(
            eps=self.cluster_tolerance,
            min_points=10
        ))
        
        clusters = []
        for label in range(labels.max() + 1):
            indices = np.where(labels == label)[0]
            cluster = obstacles.select_by_index(indices)
            clusters.append(cluster)
        
        return clusters
    
    def compute_bbox(self, cluster):
        """Compute oriented bounding box."""
        return cluster.get_oriented_bounding_box()
```

### Pattern 3: Multi-Frame Integration

```python
class PointCloudAccumulator:
    """Accumulate point clouds over time."""
    
    def __init__(self, max_frames=10):
        self.max_frames = max_frames
        self.frames = []
        self.pose_history = []
        
    def add_frame(self, pcd, pose):
        """Add new frame with pose."""
        self.frames.append(pcd)
        self.pose_history.append(pose)
        
        # Keep only recent frames
        if len(self.frames) > self.max_frames:
            self.frames.pop(0)
            self.pose_history.pop(0)
    
    def get_accumulated(self):
        """Get accumulated point cloud in current frame."""
        if not self.frames:
            return None
        
        accumulated = o3d.geometry.PointCloud()
        
        for i, (frame, pose) in enumerate(zip(self.frames, self.pose_history)):
            # Transform to current frame
            relative_pose = np.linalg.inv(self.pose_history[-1]) @ pose
            transformed = frame.transform(relative_pose)
            accumulated += transformed
        
        return accumulated
    
    def voxel_cleanup(self, voxel_size=0.05):
        """Remove duplicate points."""
        accumulated = self.get_accumulated()
        if accumulated:
            return accumulated.voxel_down_sample(voxel_size)
        return None
```

## Anti-Patterns

### ❌ Processing full-resolution point clouds
Processing millions of points causes high latency and dropped frames.

**What happens:** 100ms+ processing delay, robot cannot react in time.

### ✅ Always downsample first
```python
# Downsample early in pipeline
pcd = pcd.voxel_down_sample(voxel_size=0.05)
# Then process...
```

### ❌ Fixed thresholds for segmentation
Using hard-coded thresholds that fail in different environments.

**What happens:** Ground segmentation fails on slopes, misses obstacles.

### ✅ Adaptive thresholds
```python
# Estimate ground plane, then use relative height
_, _, plane_model = segment_ground(pcd)
height_threshold = 0.1  # 10cm above estimated ground
```

### ❌ Ignoring sensor noise
Not filtering outliers causes false obstacles.

**What happens:** Robot stops for noise points, phantom obstacles.

### ✅ Statistical outlier removal
```python
pcd, _ = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)
```

## Configuration Reference

### Common Voxel Sizes

| Application | Voxel Size | Point Density |
|-------------|-----------|---------------|
| Indoor mapping | 0.01-0.02 m | High detail |
| Outdoor navigation | 0.05-0.1 m | Balanced |
| Large-scale SLAM | 0.1-0.5 m | Sparse |

### RANSAC Parameters

| Parameter | Typical Value | Description |
|-----------|---------------|-------------|
| `distance_threshold` | 0.01-0.05 m | Max distance to plane |
| `ransac_n` | 3 | Points to sample |
| `num_iterations` | 100-1000 | Iterations for robustness |

### ICP Thresholds

| Scenario | Threshold | Notes |
|----------|-----------|-------|
| Indoor, precise | 0.01 m | Structured environment |
| Outdoor, noisy | 0.05-0.1 m | Vegetation, uneven ground |
| Initial alignment | 0.5 m | When poses uncertain |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| High processing latency | Too many points | Increase voxel_size |
| Missed small obstacles | Downsampling too aggressive | Reduce voxel_size |
| False obstacles | Sensor noise | Add outlier removal |
| Registration fails | Poor initial guess | Use feature-based first |
| Ground not flat | RANSAC threshold too tight | Increase distance_threshold |
| Slow clustering | Too many points | Pre-filter with ROI |
| Memory overflow | Accumulating frames | Limit buffer size |
| Misaligned clouds | Timestamp issues | Check time synchronization |

## Workflow Integration

- **Before this:** Use `camera-vision` for camera calibration if fusing sensors
- **After this:** Use `nav2` for navigation with processed point clouds
- **Parallel with:** Use `sensor-fusion-slam` for LiDAR-based SLAM
- **For production:** Use `safety-systems` for obstacle monitoring

## Further Reading

- [PCL Documentation](https://pointclouds.org/documentation/)
- [Open3D Documentation](http://www.open3d.org/docs/release/)
- [ROS2 PCL](https://github.com/ros-perception/perception_pcl)
- Related skills: `sensor-fusion-slam`, `nav2`, `camera-vision`

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering PCL/Open3D, filtering, segmentation, registration