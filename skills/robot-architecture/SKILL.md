---
name: robot-architecture
description: Robot software architecture with behavior trees, FSMs, component design, state estimation, and multi-robot coordination.
category: architecture
tags: [robot-architecture, behavior-trees, fsm, state-estimation, multi-robot, components]
version: "1.0.0"
---

# Robot Architecture

Software architecture patterns for robust robot systems. This skill covers behavior trees, FSMs, state estimation, and distributed systems.

## When to Use

- Designing robot behavior hierarchies
- Implementing fault-tolerant state machines
- Architecting multi-robot systems
- Designing component-based software
- Implementing state estimation pipelines
- Creating reusable robot behaviors

## Quick Start

```bash
# Install behavior tree libraries
sudo apt install ros-humble-behaviortree-cpp-v3

# For state estimation
sudo apt install ros-humble-robot-localization
```

## Core Concepts

### 1. Behavior Trees

Hierarchical task decomposition for robot behaviors.

```xml
<!-- behavior_tree.xml -->
<root main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <Sequence>
      <!-- Initialization -->
      <Action ID="InitializeRobot"/>
      
      <!-- Main loop -->
      <ReactiveSequence>
        <!-- Check preconditions -->
        <Condition ID="BatteryOK"/>
        <Condition ID="EmergencyStopClear"/>
        
        <!-- Execute mission -->
        <Selector>
          <Sequence>
            <Condition ID="GoalReached"/>
            <Action ID="CelebrateSuccess"/>
          </Sequence>
          <Sequence>
            <Action ID="ComputePath"/>
            <Action ID="FollowPath"/>
          </Sequence>
        </Selector>
      </ReactiveSequence>
    </Sequence>
  </BehaviorTree>
</root>
```

**C++ Behavior Tree implementation:**
```cpp
#include <behaviortree_cpp_v3/bt_factory.h>

class ComputePath : public BT::SyncActionNode {
public:
    ComputePath(const std::string& name, const BT::NodeConfiguration& config)
        : BT::SyncActionNode(name, config) {}
    
    static BT::PortsList providedPorts() {
        return {BT::InputPort<geometry_msgs::Pose>("goal"),
                BT::OutputPort<nav_msgs::Path>("path")};
    }
    
    BT::NodeStatus tick() override {
        auto goal = getInput<geometry_msgs::Pose>("goal");
        if (!goal) {
            throw BT::RuntimeError("missing required input [goal]");
        }
        
        // Compute path
        nav_msgs::Path path = planner_->plan(goal.value());
        
        setOutput("path", path);
        return BT::NodeStatus::SUCCESS;
    }
    
private:
    std::shared_ptr<PathPlanner> planner_;
};

// Register and use
BT::BehaviorTreeFactory factory;
factory.registerNodeType<ComputePath>("ComputePath");

auto tree = factory.createTreeFromFile("behavior_tree.xml");
tree.tickRoot();
```

### 2. Finite State Machines

Explicit state management for robot modes.

```python
from transitions import Machine

class RobotStateMachine:
    states = ['idle', 'initializing', 'ready', 'executing', 'paused', 'error']
    
    def __init__(self):
        self.machine = Machine(
            model=self,
            states=RobotStateMachine.states,
            initial='idle'
        )
        
        # Transitions
        self.machine.add_transition('initialize', 'idle', 'initializing')
        self.machine.add_transition('init_complete', 'initializing', 'ready')
        self.machine.add_transition('start_mission', 'ready', 'executing')
        self.machine.add_transition('pause', 'executing', 'paused')
        self.machine.add_transition('resume', 'paused', 'executing')
        self.machine.add_transition('complete', 'executing', 'ready')
        self.machine.add_transition('fault', '*', 'error')
        self.machine.add_transition('reset', 'error', 'idle')
        
        # Callbacks
        self.machine.on_enter_executing('on_start_execution')
        self.machine.on_enter_error('on_enter_error')
    
    def on_start_execution(self):
        print("Starting mission execution")
        self.mission_start_time = time.time()
    
    def on_enter_error(self):
        print("Entering error state!")
        self.estop_trigger()
```

### 3. State Estimation

Kalman filters for sensor fusion.

```python
import numpy as np
from filterpy.kalman import KalmanFilter

class RobotStateEstimator:
    def __init__(self):
        # State: [x, y, theta, vx, vy, omega]
        self.kf = KalmanFilter(dim_x=6, dim_z=3)
        
        # State transition (constant velocity model)
        dt = 0.02  # 50 Hz
        self.kf.F = np.array([
            [1, 0, 0, dt, 0, 0],
            [0, 1, 0, 0, dt, 0],
            [0, 0, 1, 0, 0, dt],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])
        
        # Measurement: [x, y, theta] from localization
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ])
        
        # Covariances
        self.kf.R *= 0.1  # Measurement noise
        self.kf.Q *= 0.01  # Process noise
        self.kf.P *= 10   # Initial uncertainty
    
    def predict(self):
        self.kf.predict()
    
    def update_with_odometry(self, x, y, theta):
        z = np.array([x, y, theta])
        self.kf.update(z)
    
    def update_with_imu(self, vx, vy, omega):
        # Velocity measurement
        H_vel = np.array([
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])
        z_vel = np.array([vx, vy, omega])
        self.kf.update(z_vel, H_vel)
    
    def get_state(self):
        return {
            'position': self.kf.x[:3],
            'velocity': self.kf.x[3:],
            'covariance': self.kf.P
        }
```

### 4. Multi-Robot Coordination

Distributed coordination patterns.

```python
import rclpy
from rclpy.node import Node

class FleetCoordinator(Node):
    def __init__(self):
        super().__init__('fleet_coordinator')
        
        self.robots = {}  # robot_id -> status
        
        # Auction-based task allocation
        self.task_queue = []
        self.auction_in_progress = False
        
        self.create_subscription(RobotStatus, '/fleet/status', self.status_callback)
        self.create_publisher(TaskAssignment, '/fleet/assignments', 10)
    
    def allocate_task(self, task):
        """Auction-based task allocation."""
        if not self.robots:
            self.task_queue.append(task)
            return
        
        # Request bids
        bids = {}
        for robot_id, status in self.robots.items():
            if status['available']:
                bid = self.compute_bid(robot_id, task)
                bids[robot_id] = bid
        
        # Winner takes task
        if bids:
            winner = min(bids, key=bids.get)
            self.assign_task(winner, task)
    
    def compute_bid(self, robot_id, task):
        """Compute cost for robot to execute task."""
        robot_pos = self.robots[robot_id]['position']
        task_pos = task['position']
        
        distance = np.linalg.norm(robot_pos - task_pos)
        battery_factor = 1.0 / self.robots[robot_id]['battery']
        
        return distance * battery_factor
```

## Configuration Reference

| Pattern | Use Case | Complexity | Flexibility |
|---------|----------|------------|-------------|
| Behavior Trees | Task sequences | Medium | High |
| FSM | Mode management | Low | Low |
| State Machine | Complex logic | Medium | Medium |
| Multi-agent | Fleet coordination | High | High |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| BT tick fails | Missing blackboard entry | Check port connections |
| State explosion | Too many FSM states | Use hierarchical FSM |
| Estimation drift | Poor sensor fusion | Tune Q/R matrices |

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering behavior trees, FSM, state estimation, multi-robot