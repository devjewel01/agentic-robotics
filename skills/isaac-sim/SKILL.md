---
name: isaac-sim
description: NVIDIA Isaac Sim photorealistic simulation, USD assets, synthetic data generation, domain randomization, and GPU-accelerated robotics simulation.
category: simulation
tags: [isaac-sim, nvidia, simulation, synthetic-data, domain-randomization, usd, photorealistic, gpu]
version: "1.0.0"
---

# Isaac Sim

NVIDIA Isaac Sim provides GPU-accelerated photorealistic simulation for robotics. This skill covers USD-based workflows, synthetic data generation, and sim-to-real transfer.

## When to Use

- Building photorealistic simulation environments for robot training
- Generating synthetic datasets for perception model training
- Implementing domain randomization for sim-to-real transfer
- Testing robots in physically accurate simulations
- Creating digital twins of real environments
- Benchmarking algorithms in reproducible scenarios
- Training reinforcement learning agents
- Validating manipulation and navigation pipelines

## Quick Start

```bash
# Install Isaac Sim (requires NVIDIA GPU with 8GB+ VRAM)
# Download from https://developer.nvidia.com/isaac-sim

# Launch Isaac Sim
./isaac-sim.sh

# Or headless mode for training
./isaac-sim.sh --headless --enable_livestream=0

# Install Isaac ROS (optional)
sudo apt install ros-humble-isaac-ros-visual-slam
```

## Core Concepts

### 1. USD (Universal Scene Description)

USD is the foundation of Isaac Sim's scene representation.

**USD file structure:**
```
robot_scene.usd
├── /World
│   ├── /ground_plane
│   ├── /lighting
│   │   ├── /default_light
│   │   └── /hdr_sky
│   └── /robot
│       ├── /chassis
│       ├── /wheel_left
│       ├── /wheel_right
│       └── /sensors
│           ├── /camera
│           └── /lidar
└── /Render
    └── /Settings
```

**Creating USD stages programmatically:**

```python
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid, GroundPlane
from omni.isaac.core.prims import XFormPrim
from pxr import Usd, UsdGeom, Gf

# Create world
world = World(stage_units_in_meters=1.0)

# Add ground plane
world.scene.add(GroundPlane(prim_path="/World/groundPlane", 
                           size=50, color=np.array([0.5, 0.5, 0.5])))

# Add objects
cube = world.scene.add(
    DynamicCuboid(
        prim_path="/World/cube",
        name="cube",
        position=np.array([1.0, 0.0, 0.5]),
        scale=np.array([0.5, 0.5, 0.5]),
        color=np.array([1.0, 0.0, 0.0])
    )
)

# Add lighting
import omni.isaac.core.utils.prims as prim_utils
from pxr import UsdLux

stage = omni.usd.get_context().get_stage()
distant_light = UsdLux.DistantLight.Define(stage, "/World/DistantLight")
distant_light.CreateIntensityAttr(5000)
distant_light.CreateColorAttr(Gf.Vec3f(1.0, 1.0, 1.0))
```

**USD layer composition:**
```python
# Layer 1: Base environment (warehouse_layout.usd)
# Layer 2: Robot instance (robot_franka.usd)
# Layer 3: Task-specific objects (pick_place_setup.usd)
# Layer 4: Randomization overrides

from pxr import Sdf

# Open base stage
stage = Usd.Stage.Open("warehouse_layout.usd")

# Add robot as reference
robot_prim = stage.DefinePrim("/World/robot")
robot_prim.GetReferences().AddReference("robot_franka.usd")

# Add task layer as sublayer
root_layer = stage.GetRootLayer()
task_layer = Sdf.Layer.FindOrOpen("pick_place_setup.usd")
root_layer.subLayerPaths.append(task_layer.identifier)
```

### 2. Robot Import (URDF to USD)

Importing robots from URDF/SDF to Isaac Sim's USD format.

```python
import omni.isaac.urdf as urdf_utils
from omni.isaac.core.utils.extensions import enable_extension

# Enable URDF extension
enable_extension("omni.importer.urdf")

# Import URDF
import_config = urdf_utils.ImportConfig()
import_config.merge_fixed_joints = False
import_config.convex_decomp = False
import_config.import_inertia_tensor = True
import_config.fix_base = False
import_config.make_default_prim = True

urdf_path = "/path/to/robot.urdf"
usd_path = "/path/to/robot.usd"

urdf_utils.import_urdf(urdf_path, usd_path, import_config)
```

**Articulation configuration:**
```python
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.nucleus import get_assets_root_path

# Load robot
assets_root_path = get_assets_root_path()
franka_path = assets_root_path + "/Isaac/Robots/Franka/franka_alt_fingers.usd"

robot = Articulation(prim_path="/World/franka", 
                    name="franka",
                    usd_path=franka_path)

# Get joint information
joint_names = robot.dof_names
print(f"DOFs: {len(joint_names)}")
print(f"Joints: {joint_names}")

# Set joint positions
robot.set_joint_positions(np.array([0.0, -0.5, 0.0, -1.8, 0.0, 1.8, 0.0, 0.04, 0.04]))

# Get state
position, orientation = robot.get_world_pose()
joint_pos = robot.get_joint_positions()
joint_vel = robot.get_joint_velocities()
```

### 3. Sensors and Cameras

Configuring sensors for perception tasks.

```python
from omni.isaac.sensor import Camera, LidarRtx, IMUSensor
import omni.replicator.core as rep

# RGB Camera
camera = Camera(
    prim_path="/World/robot/camera",
    frequency=30,
    resolution=(640, 480),
    position=np.array([0.5, 0.0, 0.5]),
    orientation=rot_utils.euler_angles_to_quats(np.array([0, 0, 0]))
)

camera.initialize()
camera.add_distance_to_image_plane_to_frame()
camera.add_semantic_segmentation_to_frame()

# Access data
rgb_image = camera.get_rgba()
depth_image = camera.get_depth()
semantic_seg = camera.get_semantic_segmentation()

# RTX Lidar
lidar = LidarRtx(
    prim_path="/World/robot/lidar",
    name="lidar",
    frequency=20,
    config_file="Example_Rotary",
    position=np.array([0.0, 0.0, 0.5])
)

lidar.initialize()
pointcloud = lidar.get_point_cloud_data()

# IMU
imu = IMUSensor(
    prim_path="/World/robot/imu",
    name="imu",
    frequency=100,
    translation=np.array([0.0, 0.0, 0.1])
)

imu.initialize()
linear_acc = imu.get_linear_acceleration()
angular_vel = imu.get_angular_velocity()
```

**Camera intrinsic matrix:**
```python
def get_camera_intrinsics(camera):
    """Get 3x3 intrinsic matrix from Isaac Sim camera."""
    resolution = camera.get_resolution()
    width, height = resolution[0], resolution[1]
    
    # Get horizontal/vertical FOV
    focal_length = camera.get_focal_length()
    horizontal_aperture = camera.get_horizontal_aperture()
    
    fx = width * focal_length / horizontal_aperture
    fy = height * focal_length / horizontal_aperture
    
    cx = width / 2.0
    cy = height / 2.0
    
    K = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0, 0, 1]
    ])
    
    return K
```

### 4. Synthetic Data Generation (Replicator)

Replicator generates annotated training data at scale.

```python
import omni.replicator.core as rep

# Define randomizers
def randomize_lighting():
    lights = rep.create.light(
        light_type="distant",
        temperature=rep.distribution.uniform(4000, 8000),
        intensity=rep.distribution.uniform(1000, 5000),
        rotation=rep.distribution.uniform((0, 0, 0), (360, 360, 360))
    )
    return lights.node

def randomize_objects():
    cubes = rep.create.cube(
        position=rep.distribution.uniform((-1, -1, 0), (1, 1, 0.5)),
        scale=rep.distribution.uniform(0.1, 0.3),
        rotation=rep.distribution.uniform((0, 0, 0), (360, 360, 360))
    )
    with cubes:
        rep.randomizer.color(colors=rep.distribution.uniform((0, 0, 0), (1, 1, 1)))
    return cubes.node

# Set up camera
camera = rep.create.camera(position=(2, 2, 2), look_at=(0, 0, 0))
render_product = rep.create.render_product(camera, (640, 480))

# Set up writers
writer = rep.WriterRegistry.get("BasicWriter")
writer.initialize(
    output_dir="/path/to/output",
    rgb=True,
    depth=True,
    semantic_segmentation=True,
    instance_segmentation=True,
    bounding_box_2d_tight=True,
    bounding_box_3d=True,
    camera_params=True
)
writer.attach([render_product])

# Register randomizers
rep.randomizer.register(randomize_lighting)
rep.randomizer.register(randomize_objects)

# Trigger on frame
with rep.trigger.on_frame(num_frames=1000):
    rep.randomizer.randomize_lighting()
    rep.randomizer.randomize_objects()

# Run
rep.orchestrator.run()
```

**Domain randomization parameters:**
```python
def full_domain_randomization():
    """Comprehensive domain randomization for sim-to-real."""
    
    # Lighting
    with rep.trigger.on_frame():
        lights = rep.get.prims(path_pattern="/World/Lights")
        with lights:
            rep.modify.attribute("inputs:intensity", 
                rep.distribution.uniform(500, 5000))
            rep.modify.attribute("inputs:colorTemperature",
                rep.distribution.uniform(3000, 8000))
            rep.modify.attribute("inputs:angle",
                rep.distribution.uniform(0.5, 5.0))
    
    # Materials
    with rep.trigger.on_frame():
        mats = rep.get.materials()
        with mats:
            rep.modify.attribute("inputs:diffuse_tint",
                rep.distribution.uniform((0.1, 0.1, 0.1), (1.0, 1.0, 1.0)))
            rep.modify.attribute("inputs:roughness",
                rep.distribution.uniform(0.1, 0.9))
            rep.modify.attribute("inputs:metallic",
                rep.distribution.uniform(0.0, 1.0))
    
    # Camera pose
    with rep.trigger.on_frame():
        camera = rep.get.camera("/World/Camera")
        with camera:
            rep.modify.pose(
                position=rep.distribution.uniform((1.5, -0.5, 1.0), (2.5, 0.5, 2.0)),
                rotation=rep.distribution.uniform((-10, -10, -10), (10, 10, 10))
            )
    
    # Object placement
    with rep.trigger.on_frame():
        objects = rep.get.prims(path_pattern="/World/Objects/.*")
        with objects:
            rep.modify.pose(
                position=rep.distribution.uniform((-0.5, -0.5, 0), (0.5, 0.5, 0.5)),
                rotation=rep.distribution.uniform((0, 0, 0), (360, 360, 360)),
                scale=rep.distribution.uniform(0.8, 1.2)
            )
```

### 5. Physics and Simulation

PhysX configuration for accurate dynamics.

```python
from omni.isaac.core.physics_context import PhysicsContext
from omni.physx import get_physx_scene_query_interface

# Configure physics
physics_context = PhysicsContext(
    physics_dt=1.0 / 60.0,  # 60 Hz physics
    stage_units_in_meters=1.0
)

# Enable GPU dynamics
physics_context.enable_gpu_dynamics(True)
physics_context.enable_stablization(True)

# Set solver settings
physics_context.set_solver_position_iteration_count(32)
physics_context.set_solver_velocity_iteration_count(4)

# Get physics simulation interface
from omni.physx import get_physx_interface
physx_interface = get_physx_interface()

# Raycasting
def raycast(origin, direction, distance=100.0):
    result = get_physx_scene_query_interface().raycast_closest(
        origin, direction, distance
    )
    return result

# Collision callbacks
def on_collision(contact_headers, contact_data):
    for header in contact_headers:
        print(f"Collision: {header.actor0} - {header.actor1}")

physx_interface.subscribe_contact_report_events(on_collision)
```

## Common Patterns

### Pattern 1: ROS2 Bridge

```python
from omni.isaac.ros2_bridge import Ros2Bridge
import rclpy
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Twist

class IsaacSimROS2Bridge:
    def __init__(self):
        rclpy.init()
        self.node = rclpy.create_node('isaac_sim_bridge')
        
        # Publishers
        self.rgb_pub = self.node.create_publisher(Image, '/camera/color/image_raw', 10)
        self.depth_pub = self.node.create_publisher(Image, '/camera/depth/image_raw', 10)
        self.info_pub = self.node.create_publisher(CameraInfo, '/camera/color/camera_info', 10)
        
        # Subscribers
        self.cmd_vel_sub = self.node.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        self.bridge = Ros2Bridge()
        
    def publish_camera(self, camera):
        rgb = camera.get_rgba()
        depth = camera.get_depth()
        
        # Convert to ROS messages
        rgb_msg = self.bridge.cv2_to_imgmsg(rgb[:,:,:3], encoding='rgb8')
        rgb_msg.header.stamp = self.node.get_clock().now().to_msg()
        rgb_msg.header.frame_id = 'camera_link'
        
        self.rgb_pub.publish(rgb_msg)
        
    def cmd_vel_callback(self, msg):
        # Convert Twist to Isaac Sim commands
        linear = msg.linear.x
        angular = msg.angular.z
        
        # Apply to robot
        self.robot.apply_wheel_commands(linear, angular)
    
    def spin(self):
        while rclpy.ok():
            self.publish_camera(self.camera)
            rclpy.spin_once(self.node, timeout_sec=0.001)
```

### Pattern 2: RL Environment

```python
from omni.isaac.gym.vec_env import VecEnvBase
import torch

class RobotTaskEnv(VecEnvBase):
    def __init__(self, headless=True):
        super().__init__(headless=headless)
        
        self._create_scene()
        self._setup_rewards()
        
    def _create_scene(self):
        self.world = World()
        
        # Add robot
        self.robot = self.world.scene.add(
            Robot(prim_path="/World/robot", name="robot")
        )
        
        # Add target
        self.target = self.world.scene.add(
            VisualCuboid(prim_path="/World/target", name="target")
        )
        
    def reset(self):
        # Randomize target position
        target_pos = np.random.uniform(-1, 1, 3)
        target_pos[2] = 0.5
        self.target.set_world_pose(target_pos)
        
        # Reset robot
        self.robot.set_joint_positions(self.default_joint_pos)
        
        return self.get_observations()
    
    def step(self, actions):
        # Apply actions
        self.robot.set_joint_position_targets(actions)
        
        # Step physics
        self.world.step(render=not self.headless)
        
        # Get observations
        obs = self.get_observations()
        
        # Compute reward
        reward = self.compute_reward()
        
        # Check termination
        done = self.check_termination()
        
        return obs, reward, done, {}
    
    def get_observations(self):
        joint_pos = self.robot.get_joint_positions()
        joint_vel = self.robot.get_joint_velocities()
        target_pos, _ = self.target.get_world_pose()
        
        return np.concatenate([joint_pos, joint_vel, target_pos])
    
    def compute_reward(self):
        ee_pos, _ = self.robot.end_effector.get_world_pose()
        target_pos, _ = self.target.get_world_pose()
        distance = np.linalg.norm(ee_pos - target_pos)
        return -distance  # Negative distance as reward
```

### Pattern 3: Digital Twin

```python
class DigitalTwin:
    def __init__(self, real_robot_ip):
        self.sim_world = World()
        self.real_robot = RealRobotInterface(real_robot_ip)
        
        # Create simulated twin
        self.sim_robot = self.sim_world.scene.add(
            Robot(prim_path="/World/twin", name="twin")
        )
        
        # Sync loop
        self.running = True
        
    def sync_real_to_sim(self):
        """Update simulation from real robot state."""
        real_joint_pos = self.real_robot.get_joint_positions()
        real_joint_vel = self.real_robot.get_joint_velocities()
        
        self.sim_robot.set_joint_positions(real_joint_pos)
        self.sim_robot.set_joint_velocities(real_joint_vel)
        
    def sync_sim_to_real(self):
        """Send simulation commands to real robot."""
        sim_commands = self.sim_robot.get_joint_commands()
        self.real_robot.set_joint_targets(sim_commands)
        
    def run_twin(self):
        while self.running:
            self.sync_real_to_sim()
            self.sim_world.step()
            
            # Visualize difference
            sim_pos = self.sim_robot.get_joint_positions()
            real_pos = self.real_robot.get_joint_positions()
            error = np.abs(sim_pos - real_pos)
            
            if np.max(error) > 0.1:
                print(f"Warning: High sim-to-real error: {np.max(error)}")
            
            time.sleep(0.016)  # ~60 Hz
```

## Anti-Patterns

### ❌ Single large USD file
Monolithic scenes are hard to version and slow to load.

**What happens:** Long load times, merge conflicts, inflexible scenes.

### ✅ Layer composition
```python
# Base environment
# Robot reference
# Task-specific objects
# Randomization overrides
```

### ❌ Ignoring physics determinism
Non-deterministic physics causes unreproducible training.

**What happens:** Different results on each run, hard to debug.

### ✅ Fixed seeds and determinism
```python
np.random.seed(42)
torch.manual_seed(42)
world.reset()
physics_context.enable_gpu_dynamics(False)  # CPU for determinism
```

### ❌ Rendering every frame
Full rendering slows training significantly.

**What happens:** 5 FPS instead of 1000+ FPS for RL.

### ✅ Headless with specific rendering
```python
# Only render when needed for data collection
if step % 10 == 0:
    world.step(render=True)
else:
    world.step(render=False)
```

## Configuration Reference

### GPU Requirements

| Feature | Minimum VRAM | Recommended |
|---------|-------------|-------------|
| Basic simulation | 8 GB | 12 GB |
| Ray tracing | 16 GB | 24 GB |
| Large scenes (1000+ objects) | 24 GB | 48 GB |
| Multi-GPU | 2x 16 GB | 2x 24 GB |

### Performance Settings

```python
# Quality vs Speed trade-offs
from omni.isaac.core.utils.extensions import enable_extension

# Disable unnecessary features for training
def optimize_for_training():
    # Disable ray tracing
    carb.settings.get_settings().set("/rtx/rtxEnabled", False)
    
    # Reduce texture quality
    carb.settings.get_settings().set("/rtx/textures/textureMipBias", 2)
    
    # Disable reflections
    carb.settings.get_settings().set("/rtx/reflections/enabled", False)
    
    # Reduce shadow quality
    carb.settings.get_settings().set("/rtx/shadows/enabled", False)
```

### Replicator Output Formats

| Format | Use Case | Size |
|--------|----------|------|
| PNG | Visualization | Large |
| JPEG | Training (fast load) | Medium |
| EXR | HDR, depth | Very large |
| NPY | Direct numpy | Small |
| COCO | Object detection | Metadata |
| KITTI | Autonomous driving | Metadata |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Low FPS | GPU memory full | Reduce texture quality, close other apps |
| Black screen | Missing lighting | Add dome light or HDR sky |
| Robot falls through floor | Missing collision | Enable collision on ground plane |
| Jerky motion | Physics timestep too large | Reduce physics_dt to 1/60 |
| Memory leak | Circular references | Call `world.clear()` between episodes |
| Texture errors | Missing assets | Check Nucleus connection |
| ROS2 not connecting | Wrong domain ID | Set `ROS_DOMAIN_ID` |

## Workflow Integration

- **Before this:** Use `gazebo` for rapid prototyping
- **With this:** Use `sim-to-real` for domain transfer strategies
- **After this:** Use `learning-robotics` for RL training
- **Related:** Use `camera-vision` for perception pipeline design

## Further Reading

- [Isaac Sim Documentation](https://docs.omniverse.nvidia.com/isaacsim/latest/)
- [NVIDIA Deep Learning Institute](https://www.nvidia.com/dli)
- Related skills: `gazebo`, `sim-to-real`, `learning-robotics`

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering USD, Replicator, sensors, ROS2 bridge
- Includes RL environment and digital twin patterns