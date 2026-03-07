---
name: learning-robotics
description: Robot learning with imitation learning, behavior cloning, DAgger, reinforcement learning, reward shaping, and VLA models.
category: ai
tags: [robot-learning, imitation-learning, rl, reinforcement-learning, behavior-cloning, vla, dagger]
version: "1.0.0"
---

# Learning for Robotics

Robot learning enables adaptive behaviors through demonstration and experience. This skill covers imitation learning, RL, and vision-language-action models.

## When to Use

- Teaching robots through human demonstration
- Training policies via reinforcement learning
- Implementing behavior cloning from expert data
- Using DAgger for iterative improvement
- Deploying VLA models for instruction following
- Reward engineering for complex tasks

## Quick Start

```bash
# Install robot learning libraries
pip install stable-baselines3 gymnasium-robotics

# For imitation learning
pip install imitation lerobot

# For VLA models
pip install transformers torch
```

## Core Concepts

### 1. Imitation Learning (Behavior Cloning)

Learn policies from expert demonstrations.

```python
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class DemonstrationDataset(Dataset):
    def __init__(self, trajectories):
        """
        trajectories: list of {'obs': [...], 'action': [...]}
        """
        self.data = []
        for traj in trajectories:
            for obs, act in zip(traj['obs'], traj['action']):
                self.data.append((obs, act))
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        obs, act = self.data[idx]
        return torch.FloatTensor(obs), torch.FloatTensor(act)

class BCModel(nn.Module):
    def __init__(self, obs_dim, action_dim, hidden_dim=256):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh()  # For normalized actions
        )
    
    def forward(self, obs):
        return self.network(obs)

def train_behavior_cloning(model, dataset, epochs=100):
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-4)
    criterion = nn.MSELoss()
    
    for epoch in range(epochs):
        total_loss = 0
        for obs, action in dataloader:
            pred_action = model(obs)
            loss = criterion(pred_action, action)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"Epoch {epoch}: Loss = {total_loss/len(dataloader):.4f}")
```

### 2. DAgger (Dataset Aggregation)

Iteratively improve policy by collecting data from student.

```python
class DAgger:
    def __init__(self, model, expert_policy):
        self.model = model
        self.expert = expert_policy
        self.dataset = []
    
    def run_iteration(self, env, num_episodes=10):
        """Collect data using current policy with expert corrections."""
        for episode in range(num_episodes):
            obs, _ = env.reset()
            done = False
            
            while not done:
                # Student action
                with torch.no_grad():
                    student_action = self.model(
                        torch.FloatTensor(obs)
                    ).numpy()
                
                # Query expert for "correct" action
                expert_action = self.expert.predict(obs)
                
                # Store (obs, expert_action) pair
                self.dataset.append((obs, expert_action))
                
                # Execute student action (with noise)
                action = student_action + np.random.normal(0, 0.1)
                obs, _, done, _, _ = env.step(action)
        
        # Retrain on aggregated data
        self._retrain()
    
    def _retrain(self):
        """Retrain model on all collected data."""
        dataset = DemonstrationDataset([
            {'obs': [d[0] for d in self.dataset],
             'action': [d[1] for d in self.dataset]}
        ])
        train_behavior_cloning(self.model, dataset, epochs=50)
```

### 3. Reinforcement Learning

Train policies through trial and error.

```python
from stable_baselines3 import PPO, SAC
from stable_baselines3.common.env_util import make_vec_env

# Create vectorized environment
env = make_vec_env("Pendulum-v1", n_envs=8)

# PPO for discrete or continuous actions
model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    verbose=1
)

# Train
model.learn(total_timesteps=1_000_000)

# Save
model.save("ppo_robot")

# Load and deploy
model = PPO.load("ppo_robot")
```

**Custom robot environment:**
```python
import gymnasium as gym
from gymnasium import spaces

class PickPlaceEnv(gym.Env):
    def __init__(self):
        super().__init__()
        
        # Observation: [gripper_pos(3), gripper_open(1), object_pos(3), target_pos(3)]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )
        
        # Action: [dx, dy, dz, gripper]
        self.action_space = spaces.Box(
            low=-1, high=1, shape=(4,), dtype=np.float32
        )
    
    def reset(self, seed=None):
        # Initialize scene
        self.gripper_pos = np.array([0.5, 0.0, 0.5])
        self.object_pos = np.random.uniform([0.3, -0.2, 0.1], [0.7, 0.2, 0.1])
        self.target_pos = np.random.uniform([0.3, -0.2, 0.0], [0.7, 0.2, 0.0])
        
        return self._get_obs(), {}
    
    def step(self, action):
        # Execute action
        self.gripper_pos += action[:3] * 0.01  # 1cm per step
        gripper_open = action[3] > 0
        
        # Check grasp
        distance_to_object = np.linalg.norm(self.gripper_pos - self.object_pos)
        
        # Compute reward (shaped)
        reward = self._compute_shaped_reward(distance_to_object, gripper_open)
        
        # Check success
        success = distance_to_object < 0.02 and not gripper_open
        
        return self._get_obs(), reward, success, False, {}
    
    def _compute_shaped_reward(self, dist, gripper_open):
        # Distance reward
        dist_reward = -dist
        
        # Grasp reward when close
        grasp_reward = 0
        if dist < 0.05 and not gripper_open:
            grasp_reward = 10
        
        # Placement reward
        place_reward = 0
        if not gripper_open:  # Holding object
            dist_to_target = np.linalg.norm(self.object_pos - self.target_pos)
            place_reward = -dist_to_target
        
        return dist_reward + grasp_reward + place_reward
```

### 4. Reward Shaping

Guide learning with intermediate rewards.

```python
class RewardShaper:
    def __init__(self):
        self.prev_distance = None
    
    def potential_based_shaping(self, state, action, next_state, base_reward):
        """Potential-based reward shaping preserves optimal policy."""
        # Define potential function
        def potential(s):
            # Distance to goal
            return -np.linalg.norm(s['robot'] - s['goal'])
        
        # Shaped reward
        phi_s = potential(state)
        phi_s_next = potential(next_state)
        
        shaped_reward = base_reward + 0.99 * phi_s_next - phi_s
        return shaped_reward
    
    def dense_rewards(self, env_state):
        """Multiple dense reward components."""
        rewards = {
            'distance_to_goal': -env_state['distance'],
            'heading_alignment': np.cos(env_state['heading_error']),
            'velocity_towards_goal': env_state['forward_vel'] * np.cos(env_state['heading_error']),
            'action_smoothness': -np.linalg.norm(env_state['action'] - env_state['prev_action']),
            'energy_penalty': -0.01 * np.sum(env_state['torque'] ** 2)
        }
        
        # Weighted sum
        weights = {'distance_to_goal': 1.0, 'heading_alignment': 0.5, 
                  'velocity_towards_goal': 1.0, 'action_smoothness': 0.1,
                  'energy_penalty': 0.01}
        
        return sum(rewards[k] * weights[k] for k in rewards)
```

## Anti-Patterns

### ❌ Sparse rewards without shaping
Only rewarding final success makes learning extremely slow.

**What happens:** No learning signal, random exploration fails.

### ✅ Dense, shaped rewards
```python
reward = -distance + alignment_bonus + progress_bonus - action_penalty
```

### ❌ Distribution mismatch in BC
Training on expert data only, testing on student distribution.

**What happens:** Compounding errors, policy diverges.

### ✅ Use DAgger or noise injection
```python
# Add noise to expert actions during collection
action = expert_action + np.random.normal(0, noise_std)
```

## Configuration Reference

| Algorithm | Data Needed | Sample Efficiency | Best For |
|-----------|-------------|-------------------|----------|
| Behavior Cloning | Expert demos only | High (offline) | Simple tasks |
| DAgger | Expert queries | Medium | Distribution shift |
| PPO | None | Low (online) | Complex dynamics |
| SAC | None | Medium (online) | Continuous control |
| VLA | Internet + robot data | High (pretrained) | Language instruction |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| BC policy fails | Distribution shift | Use DAgger, add noise |
| RL not learning | Poor reward shaping | Add dense rewards |
| Unstable training | Learning rate too high | Reduce LR, use LR schedule |
| Poor generalization | Overfitting to demos | Data augmentation |

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering BC, DAgger, RL, reward shaping