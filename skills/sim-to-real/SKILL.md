---
name: sim-to-real
description: Domain transfer from simulation to reality, reality gap analysis, domain adaptation, system identification, and validation methodology.
category: simulation
tags: [sim-to-real, domain-transfer, reality-gap, domain-adaptation, system-identification, validation]
version: "1.0.0"
---

# Sim-to-Real Transfer

Sim-to-real transfer bridges the gap between simulation and physical robots. This skill covers domain adaptation, system identification, and validation strategies.

## When to Use

- Transferring policies from simulation to physical robots
- Identifying real system parameters for simulation tuning
- Implementing domain randomization for robust policies
- Adapting simulators to match real-world dynamics
- Validating simulation accuracy against physical measurements
- Dealing with sensor and actuator discrepancies

## Quick Start

```bash
# Install system identification tools
pip install control sippy

# Install domain adaptation libraries
pip install gymnasium-robotics

# For ROS2 bridge
sudo apt install ros-humble-ros-gz-bridge
```

## Core Concepts

### 1. Reality Gap Analysis

Understanding discrepancies between sim and real.

```python
import numpy as np
import matplotlib.pyplot as plt

class RealityGapAnalyzer:
    def __init__(self):
        self.sim_data = []
        self.real_data = []
    
    def collect_step_response(self, sim_env, real_robot, amplitude=1.0):
        """Collect step response from both systems."""
        # Simulation
        sim_env.reset()
        sim_response = []
        for _ in range(100):
            obs, _, _, _, _ = sim_env.step(np.array([amplitude]))
            sim_response.append(obs[0])  # Position
        
        # Real robot
        real_response = real_robot.execute_step(amplitude, duration=5.0)
        
        self.sim_data = np.array(sim_response)
        self.real_data = np.array(real_response)
        
        return self.sim_data, self.real_data
    
    def compute_metrics(self):
        """Compute reality gap metrics."""
        # Steady-state error
        sim_ss = self.sim_data[-10:].mean()
        real_ss = self.real_data[-10:].mean()
        ss_error = abs(sim_ss - real_ss) / abs(real_ss) * 100
        
        # Rise time difference
        sim_rise = self._rise_time(self.sim_data)
        real_rise = self._rise_time(self.real_data)
        rise_error = abs(sim_rise - real_rise) / real_rise * 100
        
        # Overshoot
        sim_os = self._overshoot(self.sim_data)
        real_os = self._overshoot(self.real_data)
        
        return {
            'steady_state_error_pct': ss_error,
            'rise_time_error_pct': rise_error,
            'sim_overshoot': sim_os,
            'real_overshoot': real_os
        }
    
    def _rise_time(self, data, threshold=0.9):
        target = data[-1]
        idx = np.where(data >= threshold * target)[0]
        return idx[0] if len(idx) > 0 else len(data)
    
    def _overshoot(self, data):
        final = data[-1]
        peak = np.max(data)
        return (peak - final) / final * 100 if final != 0 else 0
```

### 2. System Identification

Identify real system parameters to improve simulation accuracy.

```python
import control as ctrl
from scipy.optimize import minimize

class SystemIdentifier:
    def __init__(self):
        self.params = {'J': 0.1, 'b': 0.01, 'K': 0.5, 'R': 1.0, 'L': 0.01}
    
    def motor_model(self, params, t, u):
        """DC motor model: J*ddq + b*dq = K*i, L*di + R*i = u - K*dq"""
        J, b, K, R, L = params['J'], params['b'], params['K'], params['R'], params['L']
        
        # State-space: [position, velocity, current]
        A = [[0, 1, 0],
             [0, -b/J, K/J],
             [0, -K/L, -R/L]]
        B = [[0], [0], [1/L]]
        C = [[1, 0, 0]]
        D = [[0]]
        
        sys = ctrl.ss(A, B, C, D)
        t_out, y, _ = ctrl.forced_response(sys, T=t, U=u)
        return y
    
    def identify(self, t_data, u_data, y_data):
        """Identify parameters from measured data."""
        def cost_function(params_list):
            params = dict(zip(self.params.keys(), params_list))
            y_sim = self.motor_model(params, t_data, u_data)
            return np.sum((y_sim - y_data) ** 2)
        
        # Optimize
        x0 = list(self.params.values())
        bounds = [(0.001, 10.0)] * len(x0)
        
        result = minimize(cost_function, x0, bounds=bounds, method='L-BFGS-B')
        
        self.params = dict(zip(self.params.keys(), result.x))
        return self.params
    
    def update_simulation(self, sim_env):
        """Update simulation with identified parameters."""
        sim_env.set_parameters(self.params)
```

### 3. Domain Randomization

Randomize simulation parameters to train robust policies.

```python
import gymnasium as gym

class DomainRandomizedEnv(gym.Wrapper):
    def __init__(self, env, randomization_config):
        super().__init__(env)
        self.config = randomization_config
        self.default_params = self._get_default_params()
    
    def reset(self, **kwargs):
        # Randomize parameters
        self._randomize_dynamics()
        self._randomize_friction()
        self._randomize_mass()
        self._randomize_sensor_noise()
        
        return self.env.reset(**kwargs)
    
    def _randomize_dynamics(self):
        """Randomize inertial parameters."""
        mass_scale = np.random.uniform(0.8, 1.2)
        inertia_noise = np.random.uniform(-0.1, 0.1, 3)
        
        for body in self.env.unwrapped.model.body_names:
            idx = self.env.unwrapped.model.body_names.index(body)
            self.env.unwrapped.model.body_mass[idx] *= mass_scale
            self.env.unwrapped.model.body_inertia[idx] *= (1 + inertia_noise)
    
    def _randomize_friction(self):
        """Randomize contact friction."""
        friction = np.random.uniform(0.5, 1.2)
        self.env.unwrapped.model.geom_friction[:] = [friction, 0.005, 0.0001]
    
    def _randomize_mass(self):
        """Randomize link masses."""
        for i in range(self.env.unwrapped.model.body_mass.shape[0]):
            noise = np.random.uniform(0.9, 1.1)
            self.env.unwrapped.model.body_mass[i] *= noise
    
    def _randomize_sensor_noise(self):
        """Add sensor noise."""
        self.sensor_noise_std = np.random.uniform(0.001, 0.05)
    
    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        
        # Add observation noise
        obs += np.random.normal(0, self.sensor_noise_std, obs.shape)
        
        return obs, reward, terminated, truncated, info
```

### 4. Domain Adaptation

Adapt simulation to match real observations.

```python
import torch
import torch.nn as nn

class DomainAdapter(nn.Module):
    """Learn mapping from sim to real observations."""
    
    def __init__(self, obs_dim):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, obs_dim)
        )
    
    def forward(self, sim_obs):
        """Transform sim observation to match real."""
        return sim_obs + self.encoder(sim_obs)
    
    def train_adapter(self, sim_data, real_data, epochs=100):
        """Train on paired sim-real data."""
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        
        for epoch in range(epochs):
            pred_real = self.forward(sim_data)
            loss = nn.MSELoss()(pred_real, real_data)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

class RandomizedSimulator:
    """Train policy with progressive domain randomization."""
    
    def __init__(self, base_env):
        self.env = base_env
        self.randomization_range = 0.0
    
    def train_policy(self, total_timesteps):
        """Progressively increase randomization."""
        from stable_baselines3 import PPO
        
        model = PPO("MlpPolicy", self.env, verbose=1)
        
        for phase in range(5):
            # Increase randomization each phase
            self.randomization_range = phase * 0.2
            self.env.set_randomization(self.randomization_range)
            
            print(f"Phase {phase}: Randomization = {self.randomization_range}")
            model.learn(total_timesteps=total_timesteps // 5)
        
        return model
```

## Common Patterns

### Pattern 1: Sim-to-Real Validation

```python
class SimToRealValidator:
    def __init__(self, policy, sim_env, real_robot):
        self.policy = policy
        self.sim_env = sim_env
        self.real_robot = real_robot
    
    def validate_policy(self, num_episodes=10):
        """Compare policy performance in sim vs real."""
        sim_rewards = []
        real_rewards = []
        
        for episode in range(num_episodes):
            # Sim evaluation
            sim_reward = self._evaluate_sim()
            sim_rewards.append(sim_reward)
            
            # Real evaluation
            real_reward = self._evaluate_real()
            real_rewards.append(real_reward)
            
            print(f"Episode {episode}: Sim={sim_reward:.2f}, Real={real_reward:.2f}")
        
        # Compute transfer gap
        gap = np.mean(sim_rewards) - np.mean(real_rewards)
        print(f"Sim-to-Real Gap: {gap:.2f}")
        
        return sim_rewards, real_rewards
    
    def _evaluate_sim(self):
        obs, _ = self.sim_env.reset()
        total_reward = 0
        
        for _ in range(100):
            action, _ = self.policy.predict(obs)
            obs, reward, done, _, _ = self.sim_env.step(action)
            total_reward += reward
            if done:
                break
        
        return total_reward
    
    def _evaluate_real(self):
        return self.real_robot.run_policy(self.policy, max_steps=100)
```

## Anti-Patterns

### ❌ Direct policy transfer without validation
Deploying sim-trained policy without real-world testing.

**What happens:** Unexpected failures, potential damage.

### ✅ Gradual deployment with safety checks
```python
# Start with reduced speed/limits
policy.scale_action(0.3)  # 30% max action
safety_monitor.enable()
```

### ❌ Ignoring actuator dynamics
Simulating perfect actuators while real ones have delays.

**What happens:** Oscillations, instability.

### ✅ Model actuator dynamics
```python
# Add delay and bandwidth limits to simulation
action_delayed = np.roll(action_history, delay_steps)
action_limited = lowpass_filter(action_delayed, bandwidth)
```

## Configuration Reference

| Technique | Use Case | Effort | Effectiveness |
|-----------|----------|--------|---------------|
| Domain Randomization | Robust policies | Low | Medium |
| System ID | Accurate sim | Medium | High |
| Domain Adaptation | Transfer learning | High | High |
| Progressive Randomization | Complex tasks | Medium | High |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Policy fails in real | Reality gap too large | Increase randomization, add system ID |
| Unstable on real | Unmodeled dynamics | Add actuator models, delays |
| Poor generalization | Insufficient randomization | Wider parameter ranges |

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering reality gap analysis, system ID, domain adaptation