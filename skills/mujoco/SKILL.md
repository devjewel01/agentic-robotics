---
name: mujoco
description: MuJoCo physics simulation, contact modeling, MJCF format, optimal control, and DeepMind integration for robotics research.
category: simulation
tags: [mujoco, physics, simulation, mjcf, contact, optimal-control, deepmind, robotics]
version: "1.0.0"
---

# MuJoCo

MuJoCo (Multi-Joint dynamics with Contact) is a high-performance physics engine for robotics. This skill covers MJCF modeling, contact dynamics, and optimal control.

## When to Use

- Research-grade physics simulation with accurate contact modeling
- Model Predictive Control (MPC) and trajectory optimization
- Reinforcement learning with fast simulation (1000+ FPS)
- Biomechanics and humanoid robotics
- Sim-to-real transfer requiring precise dynamics
- Optimal control and state estimation research

## Quick Start

```bash
# Install MuJoCo
pip install mujoco

# Download models
git clone https://github.com/deepmind/mujoco_menagerie.git

# Basic usage
python -c "import mujoco; print(mujoco.__version__)"
```

## Core Concepts

### 1. MJCF (Model XML Format)

MuJoCo's native modeling format.

```xml
<mujoco model="robot">
  <compiler angle="radian" meshdir="meshes/"/>
  
  <asset>
    <texture name="grid" type="2d" builtin="checker" width="512" height="512"/>
    <material name="grid" texture="grid" texrepeat="8 8" reflectance="0.1"/>
    <mesh name="chassis" file="chassis.stl" scale="0.001 0.001 0.001"/>
  </asset>
  
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    <geom name="floor" size="100 100 0.1" type="plane" material="grid"/>
    
    <body name="robot" pos="0 0 0.5">
      <freejoint/>
      <geom name="chassis_geom" type="mesh" mesh="chassis" mass="10"/>
      
      <body name="wheel_left" pos="-0.2 0.3 0">
        <joint name="wheel_left_joint" type="hinge" axis="0 1 0"/>
        <geom name="wheel_left_geom" type="cylinder" size="0.1 0.05" mass="1"/>
      </body>
      
      <body name="wheel_right" pos="-0.2 -0.3 0">
        <joint name="wheel_right_joint" type="hinge" axis="0 1 0"/>
        <geom name="wheel_right_geom" type="cylinder" size="0.1 0.05" mass="1"/>
      </body>
    </body>
  </worldbody>
  
  <actuator>
    <motor name="left_motor" joint="wheel_left_joint" gear="1" ctrlrange="-100 100"/>
    <motor name="right_motor" joint="wheel_right_joint" gear="1" ctrlrange="-100 100"/>
  </actuator>
  
  <sensor>
    <accelerometer name="imu_accel" site="imu_site"/>
    <gyro name="imu_gyro" site="imu_site"/>
    <jointpos name="wheel_left_pos" joint="wheel_left_joint"/>
    <jointvel name="wheel_left_vel" joint="wheel_left_joint"/>
  </sensor>
</mujoco>
```

**Python loading and basic simulation:**
```python
import mujoco
import numpy as np

# Load model
model = mujoco.MjModel.from_xml_path("robot.xml")
data = mujoco.MjData(model)

# Simulation loop
duration = 10.0  # seconds
while data.time < duration:
    # Set control inputs
    data.ctrl[0] = 10.0   # Left wheel torque
    data.ctrl[1] = 10.0   # Right wheel torque
    
    # Step simulation
    mujoco.mj_step(model, data)
    
    # Access state
    position = data.qpos  # Joint positions
    velocity = data.qvel  # Joint velocities
    sensor_data = data.sensordata
```

### 2. Contact Modeling

MuJoCo's soft contact model prevents penetration while remaining differentiable.

```python
# Contact parameters in MJCF
"""
<geom name="foot" size="0.05" friction="1.0 0.005 0.0001"
      solimp="0.9 0.95 0.001" solref="0.02 1"/>
"""

# solimp: impedance parameters (dmin, dmax, width)
# solref: reference parameters (timeconst, dampratio)

# Access contact data
def print_contacts(model, data):
    for i in range(data.ncon):
        contact = data.contact[i]
        print(f"Contact {i}: {contact.geom1} - {contact.geom2}")
        print(f"  Position: {contact.pos}")
        print(f"  Normal force: {data.cfrc_ext[contact.geom2]}")
```

### 3. Optimal Control with mocap

Model Predictive Control using MuJoCo's optimal control solvers.

```python
import mujoco
from mujoco import minimize

# Define trajectory optimization problem
def make_trajectory_problem(model, data, horizon=100):
    # State: [qpos, qvel]
    # Control: joint torques
    
    def cost(state, control):
        # Target state cost
        target_pos = np.array([1.0, 0.0, 0.5])
        pos_cost = np.sum((state[:3] - target_pos) ** 2)
        
        # Control cost
        ctrl_cost = 0.01 * np.sum(control ** 2)
        
        return pos_cost + ctrl_cost
    
    def dynamics(state, control):
        # Set state and control
        data.qpos[:] = state[:model.nq]
        data.qvel[:] = state[model.nq:]
        data.ctrl[:] = control
        
        # Step physics
        mujoco.mj_step(model, data)
        
        # Return next state
        return np.concatenate([data.qpos, data.qvel])
    
    return cost, dynamics

# Solve with iterative LQR (iLQR)
from scipy.optimize import minimize

def ilqr_solve(model, data, x0, horizon=100):
    # Initialize trajectory
    states = [x0 for _ in range(horizon + 1)]
    controls = [np.zeros(model.nu) for _ in range(horizon)]
    
    for iteration in range(100):
        # Forward pass
        for t in range(horizon):
            states[t+1] = dynamics(states[t], controls[t])
        
        # Backward pass (compute gradients)
        # ... (implement LQR backward pass)
        
        # Update controls
        # ...
    
    return states, controls
```

### 4. Reinforcement Learning Integration

Fast simulation for RL training.

```python
import gymnasium as gym
from gymnasium import spaces

class MuJoCoRobotEnv(gym.Env):
    def __init__(self, xml_path, frame_skip=5):
        super().__init__()
        
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        self.frame_skip = frame_skip
        
        # Action space: joint torques
        self.action_space = spaces.Box(
            low=self.model.actuator_ctrlrange[:, 0],
            high=self.model.actuator_ctrlrange[:, 1],
            dtype=np.float32
        )
        
        # Observation space: joint positions, velocities, sensor data
        obs_dim = self.model.nq + self.model.nv + self.model.nsensordata
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
    
    def reset(self, seed=None):
        super().reset(seed=seed)
        
        # Reset to keyframe or default
        mujoco.mj_resetData(self.model, self.data)
        
        # Randomize initial state
        self.data.qpos[:] += np.random.randn(self.model.nq) * 0.01
        
        return self._get_obs(), {}
    
    def step(self, action):
        # Apply action
        self.data.ctrl[:] = action
        
        # Simulate with frame skip
        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)
        
        # Compute reward
        reward = self._compute_reward()
        
        # Check termination
        terminated = self._check_termination()
        
        return self._get_obs(), reward, terminated, False, {}
    
    def _get_obs(self):
        return np.concatenate([
            self.data.qpos,
            self.data.qvel,
            self.data.sensordata
        ])
    
    def _compute_reward(self):
        # Example: reward for forward velocity
        return self.data.qvel[0]  # x-direction velocity
    
    def _check_termination(self):
        # Terminate if robot falls
        return self.data.qpos[2] < 0.3  # z-position check
```

## Configuration Reference

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| timestep | Simulation timestep | 0.002 s |
| integrator | Integration method | Euler, RK4, implicit |
| iterations | Solver iterations | 50-100 |
| solver | Constraint solver | Newton, CG |
| cone | Friction cone | pyramidal, elliptic |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Unstable simulation | Large timestep | Reduce timestep, increase iterations |
| Slow simulation | Complex mesh collisions | Use primitive geom approximations |
| Contact jitter | Too stiff contacts | Increase solimp width |
| Joint oscillation | High gains | Reduce controller gains |

## Workflow Integration

- **With:** Use `isaac-sim` for photorealistic rendering of MuJoCo trajectories
- **Before:** Use `control-systems` for MPC theory
- **After:** Use `sim-to-real` for transferring policies

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering MJCF, contact modeling, optimal control, RL