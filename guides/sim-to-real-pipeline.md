# Guide: Sim-to-Real Pipeline

Complete workflow for transferring policies from simulation to physical robots.

## Goal

Train a policy in simulation and successfully deploy it on a real robot with minimal reality gap.

## Prerequisites

- **Skills needed:** `gazebo` or `isaac-sim`, `sim-to-real`, `learning-robotics`, `ros2-control`, `realtime-motor-control`
- **Hardware:** Robot platform with ROS2 interface
- **Software:** MuJoCo or Isaac Sim, PyTorch, robot learning libraries

## Estimated Time

2-3 days for a simple task (e.g., reaching), 1-2 weeks for complex manipulation.

---

## Step 1: Simulation Setup

### 1.1 Create Accurate Robot Model

> **Skill reference:** See `skills/robot-modeling/SKILL.md`

```bash
# From URDF, create simulation model
# Gazebo
ros2 run gazebo_ros spawn_entity.py -topic robot_description -entity robot

# Or MuJoCo
python -c "
import mujoco
model = mujoco.MjModel.from_xml_path('robot.xml')
"
```

**Verify dynamics match real robot:**
```python
# Collect step response from real robot
real_response = collect_step_response(real_robot, amplitude=1.0)

# Simulate same command in sim
sim_response = simulate_step_response(sim_env, amplitude=1.0)

# Compare
plot_comparison(real_response, sim_response)
```

### 1.2 Add Realistic Actuator Models

> **Skill reference:** See `skills/realtime-motor-control/SKILL.md`

```python
class RealisticActuator:
    """Actuator with delay and bandwidth limits."""
    
    def __init__(self, delay_steps=3, bandwidth=50):
        self.delay_steps = delay_steps
        self.bandwidth = bandwidth
        self.action_history = deque(maxlen=delay_steps + 1)
        
        # Low-pass filter for bandwidth limiting
        self.prev_output = 0.0
        self.alpha = 1.0 / (1.0 + bandwidth * dt)
    
    def apply(self, target_action):
        # Add to history
        self.action_history.append(target_action)
        
        # Apply delay
        if len(self.action_history) < self.delay_steps:
            delayed_action = 0.0
        else:
            delayed_action = self.action_history[0]
        
        # Apply bandwidth limit (low-pass)
        output = self.alpha * delayed_action + (1 - self.alpha) * self.prev_output
        self.prev_output = output
        
        return output
```

---

## Step 2: Domain Randomization Training

> **Skill reference:** See `skills/learning-robotics/SKILL.md`

### 2.1 Set Up Randomized Environment

```python
from sim_to_real import DomainRandomizedEnv

env = DomainRandomizedEnv(
    base_env=GazeboEnv("robot_reach"),
    randomization_config={
        'mass_range': (0.8, 1.2),
        'friction_range': (0.5, 1.2),
        'delay_range': (0, 5),  # steps
        'sensor_noise': (0.001, 0.05),
        'action_noise': (0.0, 0.1)
    }
)
```

### 2.2 Train with Progressive Randomization

```python
from stable_baselines3 import PPO

# Phase 1: No randomization (learn basic task)
env.set_randomization(0.0)
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=500_000)

# Phase 2-5: Gradually increase randomization
for phase in range(2, 6):
    randomization = (phase - 1) * 0.2
    env.set_randomization(randomization)
    print(f"Phase {phase}: Randomization = {randomization}")
    model.learn(total_timesteps=500_000)

model.save("policy_domain_randomized")
```

---

## Step 3: System Identification (Optional but Recommended)

> **Skill reference:** See `skills/sim-to-real/SKILL.md`

If simulation and real dynamics differ significantly:

```python
# Collect real robot data
real_data = collect_trajectory_data(real_robot, num_episodes=50)

# Identify parameters
identifier = SystemIdentifier()
identified_params = identifier.identify(
    t_data=real_data['time'],
    u_data=real_data['commands'],
    y_data=real_data['positions']
)

print("Identified parameters:", identified_params)

# Update simulation
sim_env.set_parameters(identified_params)

# Retrain if needed
model.learn(total_timesteps=200_000)
```

---

## Step 4: Policy Refinement with Real Data

### 4.1 Deploy Policy on Real Robot (Conservative)

```python
# Load policy
model = PPO.load("policy_domain_randomized")

# Initial deployment with safety limits
class SafePolicyWrapper:
    def __init__(self, policy, max_vel=0.5, max_acc=1.0):
        self.policy = policy
        self.max_vel = max_vel
        self.max_acc = max_acc
        self.prev_action = np.zeros(action_dim)
    
    def predict(self, obs):
        action, _ = self.policy.predict(obs, deterministic=True)
        
        # Limit velocity
        action = np.clip(action, -self.max_vel, self.max_vel)
        
        # Limit acceleration
        max_delta = self.max_acc * dt
        action = np.clip(action, 
                        self.prev_action - max_delta,
                        self.prev_action + max_delta)
        
        self.prev_action = action
        return action

safe_policy = SafePolicyWrapper(model, max_vel=0.3, max_acc=0.5)
```

### 4.2 Collect Real-World Data for Fine-tuning

```python
# Run policy, collect (obs, action, reward) tuples
real_world_dataset = []

for episode in range(20):
    obs = real_robot.reset()
    done = False
    
    while not done:
        action = safe_policy.predict(obs)
        next_obs, reward, done = real_robot.step(action)
        
        real_world_dataset.append({
            'obs': obs,
            'action': action,
            'reward': reward,
            'next_obs': next_obs
        })
        
        obs = next_obs

# Fine-tune with real data (offline RL or DAgger)
from imitation.algorithms.bc import BC

bc_trainer = BC(
    observation_space=env.observation_space,
    action_space=env.action_space,
    demonstrations=real_world_dataset,
    policy=model.policy
)
bc_trainer.train(n_epochs=10)
```

---

## Step 5: Validation and Iteration

### 5.1 Measure Reality Gap

```python
validator = SimToRealValidator(
    policy=model,
    sim_env=sim_env,
    real_robot=real_robot
)

sim_rewards, real_rewards = validator.validate_policy(num_episodes=10)

# Compute gap
gap = np.mean(sim_rewards) - np.mean(real_rewards)
print(f"Sim-to-Real Gap: {gap:.2f}")

if gap > threshold:
    print("Gap too large - need more domain randomization or system ID")
```

### 5.2 Iterative Improvement

```python
# If performance is poor, try:
# 1. More domain randomization
# 2. Better actuator models
# 3. DAgger with real-world corrections
# 4. Domain adaptation network

from sim_to_real import DAgger

dagger = DAgger(
    student_policy=model,
    expert=human_operator  # or MPC controller
)

# Iteratively improve
for iteration in range(5):
    # Collect data with current policy
    dagger.run_iteration(real_robot, num_episodes=5)
    
    # Retrain
    model = dagger.get_updated_policy()
    
    # Validate
    gap = measure_gap(model, sim_env, real_robot)
    print(f"Iteration {iteration}: Gap = {gap:.2f}")
```

---

## Validation Checklist

- [ ] Simulation matches real robot step response (< 10% error)
- [ ] Policy succeeds in simulation > 90% of time
- [ ] Conservative deployment works on real robot
- [ ] Safety limits prevent dangerous actions
- [ ] Reality gap < 20% after domain randomization
- [ ] Fine-tuned policy succeeds > 80% on real robot
- [ ] Failure modes are graceful and safe

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Policy oscillates | Unmodeled actuator dynamics | Add delay and bandwidth limits |
| Sim policy fails completely | Distribution shift | Increase domain randomization range |
| Works sometimes | Stochastic real world | Add more sensor/action noise in sim |
| Biased behavior | Simulation bias | System identification, domain adaptation |
| Unsafe actions | Poor safety limits | Tighten limits, add more constraints |

## Next Steps

- **Fleet deployment:** Use `skills/deployment-fleet` for multi-robot deployment
- **Continuous improvement:** Set up data collection pipeline for ongoing learning
- **Safety validation:** Review `skills/safety-systems` for production deployment

## References

- **Domain Transfer:** `skills/sim-to-real/SKILL.md`
- **Robot Learning:** `skills/learning-robotics/SKILL.md`
- **Real-time Control:** `skills/realtime-motor-control/SKILL.md`