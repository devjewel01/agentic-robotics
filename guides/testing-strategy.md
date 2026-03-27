# Guide: Robotics Testing Strategy

This guide walks through implementing a complete testing pyramid for robot software — from fast unit tests that run without hardware, through simulation-based CI, to hardware-in-the-loop validation and field testing.

## Goal

Build a test suite that catches bugs at the cheapest layer possible: unit tests catch logic errors in milliseconds, integration tests catch ROS 2 wiring issues in seconds, simulation tests catch behavioral regressions in CI, and HIL tests catch hardware-specific issues before field deployment.

## Prerequisites

- **Skills needed:** `ros2_testing`, `robotics_testing`, `gazebo`, `sim_to_real`, `safety_systems`
- **Hardware:** Robot with USB sensors (for HIL), a development machine for unit/integration/sim tests
- **Software:** ROS 2 Jazzy, pytest, colcon, Gazebo Sim (Harmonic), GitHub Actions (for CI)
- **Assumed:** Python-based ROS 2 packages following the project's Clean Architecture conventions

## Estimated Time

2-4 hours to set up the full pyramid from scratch (1-2 hours for individual layers)

---

## Step 1: Testing Pyramid Overview

The testing pyramid defines where you invest testing effort. Each layer is cheaper to run but catches less:

```
         /\
        /  \
       / E2E\          Field tests — real robot, real environment
      /------\
     /  HIL   \        Hardware-in-the-loop — real hardware, mock scenarios
    /----------\
   /  Sim Tests \      Gazebo CI — headless simulation, scenario-based
  /--------------\
 / ROS2 Integration\   launch_testing — nodes wired together, no hardware
/------------------\
|    Unit Tests     |  pytest / GTest — pure logic, no ROS 2 required
\__________________/
```

**Rule of thumb:**
- Unit tests: run on every commit, must pass in < 30 seconds total
- Integration tests: run on every PR, must pass in < 5 minutes
- Simulation tests: run nightly or on merge to `main`, 10-30 minutes
- HIL tests: run before every production deploy, requires robot
- Field tests: run on milestone releases

**Skill reference:** See `skills/ros2_testing` and `skills/robotics_testing` for detailed patterns.

---

## Step 2: Unit Tests — Pure Python/C++ Without ROS 2

Unit tests must run without a ROS 2 context. They test domain logic: kinematics, protocol parsers, state machines, safety logic.

### 2.1 Project Structure

```
src/orbibot_hardware/
├── orbibot_hardware/
│   ├── __init__.py
│   ├── hardware_node.py          # ROS 2 node (not unit-tested directly)
│   ├── rosmaster_driver.py       # Serial protocol — testable
│   └── mecanum_kinematics.py     # Pure math — fully unit-testable
└── test/
    ├── unit/
    │   ├── test_mecanum_kinematics.py
    │   └── test_rosmaster_driver.py
    └── integration/
        └── test_hardware_node.py
```

### 2.2 Unit Test: Mecanum Kinematics

```python
# test/unit/test_mecanum_kinematics.py
import pytest
from orbibot_hardware.mecanum_kinematics import MecanumKinematics

# Constants from robot spec
WHEEL_RADIUS = 0.05
WHEEL_SEP_X  = 0.26
WHEEL_SEP_Y  = 0.36


class TestMecanumKinematics:
    """Unit tests for mecanum inverse/forward kinematics."""

    def setup_method(self):
        self.kin = MecanumKinematics(
            wheel_radius=WHEEL_RADIUS,
            wheel_sep_x=WHEEL_SEP_X,
            wheel_sep_y=WHEEL_SEP_Y,
        )

    def test_pure_forward(self):
        """Forward motion: all wheels should spin at same rate."""
        fl, fr, bl, br = self.kin.inverse(vx=1.0, vy=0.0, wz=0.0)
        assert abs(fl - fr) < 1e-9
        assert abs(bl - br) < 1e-9
        assert fl > 0.0

    def test_pure_lateral(self):
        """Lateral (strafing) motion: diagonal pairs opposite sign."""
        fl, fr, bl, br = self.kin.inverse(vx=0.0, vy=1.0, wz=0.0)
        # FL and BR should be negative, FR and BL positive (or vice versa)
        assert fl * br > 0  # same sign
        assert fr * bl > 0  # same sign
        assert fl * fr < 0  # opposite sign between pairs

    def test_pure_rotation(self):
        """Rotation: left side negative, right side positive (CCW)."""
        fl, fr, bl, br = self.kin.inverse(vx=0.0, vy=0.0, wz=1.0)
        assert fl < 0
        assert bl < 0
        assert fr > 0
        assert br > 0

    def test_zero_velocity(self):
        """Zero command should produce zero wheel speeds."""
        fl, fr, bl, br = self.kin.inverse(vx=0.0, vy=0.0, wz=0.0)
        assert fl == pytest.approx(0.0)
        assert fr == pytest.approx(0.0)

    def test_forward_inverse_roundtrip(self):
        """Forward kinematics should invert inverse kinematics."""
        vx_in, vy_in, wz_in = 0.3, 0.1, 0.5
        wheels = self.kin.inverse(vx_in, vy_in, wz_in)
        vx_out, vy_out, wz_out = self.kin.forward(*wheels)
        assert vx_out == pytest.approx(vx_in, abs=1e-6)
        assert vy_out == pytest.approx(vy_in, abs=1e-6)
        assert wz_out == pytest.approx(wz_in, abs=1e-6)
```

### 2.3 Unit Test: Serial Protocol Parser

```python
# test/unit/test_rosmaster_driver.py
import pytest
from unittest.mock import MagicMock, patch
from orbibot_hardware.rosmaster_driver import RosmasterDriver, SYNC_BYTE

class TestRosmasterDriver:
    """Unit tests for firmware serial protocol parsing."""

    def setup_method(self):
        # Instantiate with a mock serial port — no hardware needed
        self._mock_serial = MagicMock()
        with patch('orbibot_hardware.rosmaster_driver.serial.Serial',
                   return_value=self._mock_serial):
            self.driver = RosmasterDriver(port='/dev/null', baud=115200)

    def test_checksum_valid_packet(self):
        """Valid packet with correct checksum should parse without error."""
        # Build a minimal valid packet: [SYNC, LEN, CMD, data..., CKSUM]
        packet = bytes([SYNC_BYTE, 0x06, 0x01, 0x00, 0x00, 0x00])
        checksum = (~sum(packet[1:-1]) + 1) & 0xFF
        packet = packet[:-1] + bytes([checksum])
        result = self.driver._parse_packet(packet)
        assert result is not None

    def test_checksum_invalid_packet(self):
        """Packet with wrong checksum must be rejected."""
        packet = bytes([SYNC_BYTE, 0x06, 0x01, 0x00, 0x00, 0xFF])  # bad checksum
        result = self.driver._parse_packet(packet)
        assert result is None

    def test_encoder_values_decoded(self):
        """Encoder packet should decode to four int32 wheel counts."""
        raw_counts = [100, -200, 300, -400]
        packet = self.driver._build_encoder_packet(raw_counts)
        decoded = self.driver._parse_packet(packet)
        assert decoded['encoders'] == raw_counts

    def test_velocity_command_encoded(self):
        """Velocity command should encode vx, vy, wz to correct bytes."""
        cmd_bytes = self.driver._build_velocity_command(vx=0.5, vy=0.0, wz=0.0)
        assert len(cmd_bytes) > 4
        assert cmd_bytes[0] == SYNC_BYTE
```

### 2.4 Run Unit Tests

```bash
cd ~/orbibot_ws

# Run only unit tests (fast — no ROS 2 needed)
pytest src/orbibot_hardware/test/unit/ -v

# Run with coverage
pytest src/orbibot_hardware/test/unit/ \
  --cov=orbibot_hardware \
  --cov-report=term-missing \
  --cov-report=html:htmlcov/

# Expected output:
# test/unit/test_mecanum_kinematics.py::TestMecanumKinematics::test_pure_forward PASSED
# test/unit/test_mecanum_kinematics.py::TestMecanumKinematics::test_pure_lateral PASSED
# ...
# Coverage: 85%+
```

---

## Step 3: ROS 2 Integration Tests with launch_testing

Integration tests start real ROS 2 nodes and verify that they communicate correctly. No hardware is required — use mock publishers and subscribers.

### 3.1 Basic Integration Test: Hardware Node

```python
# test/integration/test_hardware_node.py
import pytest
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.markers


@launch_testing.markers.keep_alive
def generate_test_description():
    """Launch the hardware node with a mock serial port (via param override)."""
    hardware_node = launch_ros.actions.Node(
        package='orbibot_hardware',
        executable='hardware_node',
        name='hardware_node',
        parameters=[{
            'serial_port': '/dev/null',   # Won't connect — tests topic structure
            'use_sim_time': True,
        }],
        output='screen',
    )
    return (
        launch.LaunchDescription([
            hardware_node,
            launch_testing.actions.ReadyToTest(),
        ]),
        {'hardware_node': hardware_node},
    )


class TestHardwareNodeTopics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('test_node')

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_odom_topic_exists(self):
        """hardware_node must publish /odom."""
        topics = dict(self.node.get_topic_names_and_types())
        assert '/odom' in topics
        assert 'nav_msgs/msg/Odometry' in topics['/odom']

    def test_imu_topic_exists(self):
        """hardware_node must publish /imu/data_raw."""
        topics = dict(self.node.get_topic_names_and_types())
        assert '/imu/data_raw' in topics

    def test_cmd_vel_subscribed(self):
        """hardware_node must subscribe to /cmd_vel."""
        subs = dict(self.node.get_subscriber_names_and_types_by_node(
            'hardware_node', '/'))
        assert '/cmd_vel' in subs
```

### 3.2 Integration Test: Verify Odometry Response to Velocity

```python
# test/integration/test_odometry_response.py
import threading
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class OdomCollector(Node):
    def __init__(self):
        super().__init__('odom_collector')
        self.messages = []
        self._sub = self.create_subscription(
            Odometry, '/odometry/filtered',
            lambda msg: self.messages.append(msg), 10
        )
        self._pub = self.create_publisher(Twist, '/cmd_vel', 10)

    def send_velocity(self, vx, vy, wz):
        msg = Twist()
        msg.linear.x = vx
        msg.linear.y = vy
        msg.angular.z = wz
        self._pub.publish(msg)


def test_ekf_publishes_at_20hz():
    """EKF output must publish at ~20 Hz for 2 seconds."""
    rclpy.init()
    node = OdomCollector()

    executor = rclpy.executors.SingleThreadedExecutor()
    executor.add_node(node)

    # Spin for 2 seconds
    deadline = time.time() + 2.0
    while time.time() < deadline:
        executor.spin_once(timeout_sec=0.05)

    node.destroy_node()
    rclpy.shutdown()

    # Should have received ~40 messages in 2 seconds
    assert len(node.messages) >= 35, \
        f"Expected ~40 messages, got {len(node.messages)}"
```

### 3.3 Run Integration Tests with colcon

```bash
cd ~/orbibot_ws

# Build first
colcon build --packages-select orbibot_hardware --symlink-install

# Run all tests for the package (unit + integration)
colcon test --packages-select orbibot_hardware

# View results
colcon test-result --verbose

# Run a specific test file directly (faster during development)
source install/setup.bash
python3 -m pytest src/orbibot_hardware/test/integration/ -v -s
```

---

## Step 4: Simulation Tests in Gazebo (Headless CI)

Simulation tests run the full robot stack in Gazebo without a display. They catch behavioral regressions: does the robot still navigate correctly? Does SLAM build a reasonable map?

### 4.1 Launch Gazebo Headless

```bash
# Set headless display for CI environments
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &

# Or use the offscreen renderer (no X11 needed)
export MESA_GL_VERSION_OVERRIDE=3.3
export LIBGL_ALWAYS_SOFTWARE=1

# Launch simulation
ros2 launch orbibot_bringup sim.launch.py \
  headless:=true \
  use_sim_time:=true \
  world:=src/orbibot_description/worlds/test_arena.world
```

### 4.2 Scenario Test: Navigate to a Goal

```python
# test/sim/test_navigation_scenario.py
"""
Scenario: Robot starts at origin, navigates to (2.0, 1.0), must arrive within 30s.
Requires: Gazebo running with map loaded, Nav2 active.
"""
import time
import pytest
import rclpy
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped


@pytest.fixture(scope='module')
def ros_context():
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture
def nav_client(ros_context):
    node = rclpy.create_node('test_nav_client')
    client = ActionClient(node, NavigateToPose, 'navigate_to_pose')
    assert client.wait_for_server(timeout_sec=10.0), \
        "NavigateToPose action server not available"
    yield node, client
    node.destroy_node()


def test_navigate_to_goal(nav_client):
    """Robot must reach (2.0, 1.0) within 30 seconds."""
    node, client = nav_client

    goal = NavigateToPose.Goal()
    goal.pose = PoseStamped()
    goal.pose.header.frame_id = 'map'
    goal.pose.pose.position.x = 2.0
    goal.pose.pose.position.y = 1.0
    goal.pose.pose.orientation.w = 1.0

    future = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)

    goal_handle = future.result()
    assert goal_handle.accepted, "Navigation goal was rejected"

    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=30.0)

    assert result_future.done(), "Navigation did not complete within 30s"
    result = result_future.result()
    assert result.status == 4, \
        f"Navigation failed with status {result.status}"  # 4 = SUCCEEDED
```

### 4.3 Scenario Test: SLAM Builds a Map

```python
# test/sim/test_slam_mapping.py
"""
Scenario: Drive robot around test arena for 60s, verify /map is published
and has non-trivial content (at least 10% of cells are known).
"""
import time
import rclpy
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import Twist


def test_slam_produces_map():
    """SLAM must produce a map with > 10% known cells after 60 seconds of driving."""
    rclpy.init()
    node = rclpy.create_node('test_slam')
    received_map = []

    sub = node.create_subscription(
        OccupancyGrid, '/map',
        lambda m: received_map.append(m), 1
    )
    pub = node.create_publisher(Twist, '/cmd_vel', 10)

    # Drive in a square for 60 seconds
    start = time.time()
    directions = [(0.2, 0.0), (0.0, 0.5), (-0.2, 0.0), (0.0, -0.5)]
    while time.time() - start < 60.0:
        idx = int((time.time() - start) / 15.0) % 4
        vx, wz = directions[idx]
        cmd = Twist()
        cmd.linear.x = vx
        cmd.angular.z = wz
        pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=0.1)

    # Stop
    pub.publish(Twist())

    node.destroy_node()
    rclpy.shutdown()

    assert len(received_map) > 0, "No map was published by SLAM"
    grid = received_map[-1]
    total_cells = len(grid.data)
    known_cells = sum(1 for c in grid.data if c >= 0)  # -1 = unknown
    known_ratio = known_cells / total_cells if total_cells > 0 else 0.0

    assert known_ratio > 0.10, \
        f"Map only {known_ratio:.1%} known — SLAM may not be running"
```

---

## Step 5: Hardware-in-the-Loop (HIL) Tests

HIL tests run on real hardware with real sensors, but use controlled scenarios rather than full field conditions.

### 5.1 Prepare the Robot for HIL

```bash
# On the robot: start the full stack
ros2 launch orbibot_bringup robot.launch.py &
sleep 10

# Verify stack is healthy before running HIL tests
ros2 topic hz /scan --window 5
ros2 topic hz /odometry/filtered --window 5
```

### 5.2 HIL Test: Encoder Symmetry

```python
# test/hil/test_encoder_symmetry.py
"""
HIL test: Drive forward at 0.3 m/s for 2 seconds.
All four encoders should accumulate similar tick counts.
A 10%+ asymmetry indicates a motor/encoder hardware problem.
"""
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from geometry_msgs.msg import Twist


def test_encoder_symmetry_forward():
    """All four wheel encoders must accumulate within 10% of each other."""
    rclpy.init()
    node = rclpy.create_node('hil_encoder_test')
    encoder_snapshots = []

    sub = node.create_subscription(
        Int32MultiArray, '/orbibot/encoders',
        lambda m: encoder_snapshots.append(list(m.data)), 10
    )
    pub = node.create_publisher(Twist, '/cmd_vel', 10)

    # Drive forward for 2 seconds
    start = time.time()
    while time.time() - start < 2.0:
        cmd = Twist()
        cmd.linear.x = 0.3
        pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=0.05)

    # Stop
    pub.publish(Twist())
    rclpy.spin_once(node, timeout_sec=0.2)

    node.destroy_node()
    rclpy.shutdown()

    assert len(encoder_snapshots) > 10, "Too few encoder messages received"

    first = encoder_snapshots[0]
    last  = encoder_snapshots[-1]
    deltas = [abs(last[i] - first[i]) for i in range(4)]
    max_delta = max(deltas)
    min_delta = min(deltas)

    asymmetry = (max_delta - min_delta) / max_delta if max_delta > 0 else 0.0
    assert asymmetry < 0.10, \
        f"Encoder asymmetry {asymmetry:.1%} exceeds 10% — check motors FL={deltas[0]}, BL={deltas[1]}, FR={deltas[2]}, BR={deltas[3]}"
```

### 5.3 HIL Test: Safety Stop on Command Timeout

```python
# test/hil/test_safety_timeout.py
"""
HIL test: Send velocity command, then stop publishing.
Hardware node must stop the robot within 0.6 seconds (cmd_timeout = 0.5s + 100ms margin).
"""
import time
import rclpy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist


def test_command_timeout_stops_robot():
    """Robot must stop within 600ms of last velocity command."""
    rclpy.init()
    node = rclpy.create_node('hil_safety_test')
    odom_msgs = []

    sub = node.create_subscription(
        Odometry, '/odom',
        lambda m: odom_msgs.append(m), 10
    )
    pub = node.create_publisher(Twist, '/cmd_vel', 10)

    # Start moving
    cmd = Twist()
    cmd.linear.x = 0.2
    for _ in range(5):
        pub.publish(cmd)
        rclpy.spin_once(node, timeout_sec=0.05)

    # Stop publishing (simulate lost connection)
    stop_time = time.time()

    # Wait 800ms and sample velocity
    while time.time() - stop_time < 0.8:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.destroy_node()
    rclpy.shutdown()

    # The last odom messages should show ~0 velocity
    assert len(odom_msgs) > 0
    last_vel = odom_msgs[-1].twist.twist.linear.x
    assert abs(last_vel) < 0.05, \
        f"Robot still moving at {last_vel:.3f} m/s after command timeout"
```

### 5.4 Run HIL Tests

```bash
# Run HIL tests on the robot (requires live ROS 2 stack)
ssh orbibot@orbibot-01

source /opt/ros/jazzy/setup.bash
source ~/orbibot_ws/install/setup.bash

# Run HIL suite — requires robot.launch.py already running
pytest ~/orbibot_ws/src/orbibot_hardware/test/hil/ -v --timeout=60

# Expected:
# test/hil/test_encoder_symmetry.py::test_encoder_symmetry_forward PASSED
# test/hil/test_safety_timeout.py::test_command_timeout_stops_robot PASSED
```

---

## Step 6: Field Testing Protocol

Field tests run the robot in its actual operating environment with full instrumentation. The goal is to collect metrics, not just pass/fail.

### 6.1 Instrumented Run Setup

```bash
# Before every field test: start bag recording for full analysis
mkdir -p ~/field_tests/$(date +%Y-%m-%d)
TESTDIR=~/field_tests/$(date +%Y-%m-%d)

ros2 bag record \
  /scan \
  /odom \
  /odometry/filtered \
  /imu/data_raw \
  /imu/data_filtered \
  /cmd_vel \
  /map \
  /orbibot/system_status \
  /orbibot/encoders \
  -o ${TESTDIR}/field_run_$(date +%H%M)

# Run in parallel with normal operations — no performance impact
```

### 6.2 Field Test Scenarios

**Scenario A: 10m Straight Line**
```bash
# Drive forward 10 meters, measure odometry error
# Expected: position error < 5% (< 50cm over 10m)
ros2 topic echo /odometry/filtered --once | grep position
# Drive manually, stop, check again
```

**Scenario B: Return to Origin**
```bash
# Drive a known loop (4x right turns × 90°), check final position
# Expected: return within 20cm and 5° of origin
```

**Scenario C: Obstacle Avoidance**
```bash
# Navigate to a goal with a static obstacle in the path
# Expected: path replanned, goal reached, no collision
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 5.0, y: 0.0}, orientation: {w: 1.0}}}}'
```

### 6.3 Post-Run Analysis

```bash
# Analyze recorded bag — check odometry drift
ros2 bag info ${TESTDIR}/field_run_1200/

# Plot odometry vs ideal path
python3 scripts/analyze_odom_drift.py \
  --bag ${TESTDIR}/field_run_1200/ \
  --output ${TESTDIR}/drift_report.png

# Check system health during run
ros2 bag play ${TESTDIR}/field_run_1200/ --topics /orbibot/system_status &
ros2 topic echo /orbibot/system_status | grep -E "cpu|memory|temp"
```

**Field test acceptance criteria:**

| Metric | Pass Threshold |
|--------|---------------|
| Odometry error (10m straight) | < 5% (50 cm) |
| Angular drift (360° turn) | < 5° |
| Navigation success rate | ≥ 90% of goals reached |
| Sensor dropout events | 0 during test |
| CPU temperature peak | < 80°C |
| Battery duration | > 45 min normal operation |

---

## Step 7: CI/CD Integration with GitHub Actions

### 7.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: ROS 2 Test Suite

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

env:
  ROS_DISTRO: jazzy

jobs:
  unit-tests:
    name: Unit Tests (no ROS 2)
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pytest-timeout
          pip install -e src/orbibot_hardware/

      - name: Run unit tests
        run: |
          pytest src/orbibot_hardware/test/unit/ \
            src/orbibot_rosmaster_firmware/tests/ \
            -v \
            --timeout=30 \
            --cov=orbibot_hardware \
            --cov-report=xml:coverage.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  integration-tests:
    name: ROS 2 Integration Tests
    runs-on: ubuntu-24.04
    container:
      image: ros:jazzy-ros-base
    steps:
      - uses: actions/checkout@v4

      - name: Install ROS 2 dependencies
        run: |
          apt-get update
          rosdep update
          rosdep install --from-paths src --ignore-src -r -y

      - name: Build
        run: |
          . /opt/ros/jazzy/setup.sh
          colcon build \
            --packages-select orbibot_msgs orbibot_hardware \
            --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo

      - name: Run integration tests
        run: |
          . /opt/ros/jazzy/setup.sh
          . install/setup.sh
          colcon test \
            --packages-select orbibot_hardware \
            --pytest-args --timeout=60
          colcon test-result --verbose

  simulation-tests:
    name: Gazebo Simulation Tests
    runs-on: ubuntu-24.04
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    container:
      image: ros:jazzy-ros-base
    steps:
      - uses: actions/checkout@v4

      - name: Install Gazebo + ROS 2 packages
        run: |
          apt-get update
          apt-get install -y \
            ros-jazzy-gazebo-ros-pkgs \
            ros-jazzy-nav2-bringup \
            ros-jazzy-slam-toolbox \
            xvfb
          rosdep install --from-paths src --ignore-src -r -y

      - name: Build all packages
        run: |
          . /opt/ros/jazzy/setup.sh
          colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

      - name: Start virtual display
        run: Xvfb :99 -screen 0 1024x768x24 &

      - name: Launch simulation
        run: |
          . /opt/ros/jazzy/setup.sh
          . install/setup.sh
          DISPLAY=:99 ros2 launch orbibot_bringup sim.launch.py \
            headless:=true use_sim_time:=true &
          sleep 15  # Wait for Gazebo to initialize

      - name: Run simulation tests
        run: |
          . /opt/ros/jazzy/setup.sh
          . install/setup.sh
          DISPLAY=:99 pytest src/*/test/sim/ \
            -v \
            --timeout=120 \
            -x  # Stop on first failure

      - name: Upload test artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: sim-test-results
          path: |
            log/
            *.png
```

### 7.2 Run CI Locally with act

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run unit tests locally exactly as CI would
act push -j unit-tests

# Run only integration tests
act push -j integration-tests --container-architecture linux/amd64
```

---

## Step 8: Test Coverage Reporting

### 8.1 Python Coverage with pytest-cov

```bash
# Run full test suite with coverage
cd ~/orbibot_ws
source install/setup.bash

pytest src/orbibot_hardware/test/ \
  src/orbibot_agent/test/ \
  --cov=orbibot_hardware \
  --cov=orbibot_agent \
  --cov-report=term-missing \
  --cov-report=html:htmlcov/ \
  --cov-fail-under=70

# Open HTML report
xdg-open htmlcov/index.html
```

### 8.2 Coverage Targets

| Package | Target | Notes |
|---------|--------|-------|
| `orbibot_hardware` (domain logic) | ≥ 80% | Kinematics, protocol parser |
| `orbibot_agent` (tools, safety) | ≥ 75% | Tool registry, safety checks |
| `orbibot_hardware` (node itself) | ≥ 40% | Harder — needs ROS 2 runtime |
| Firmware (`tests/`) | ≥ 70% | Python test scripts against serial |

### 8.3 colcon Test Summary

```bash
# After running colcon test
colcon test-result --all

# Find any failing tests quickly
colcon test-result --all | grep -E "FAIL|ERROR"

# Verbose output for a specific package
colcon test-result --packages-select orbibot_hardware --verbose
```

---

## Validation Checklist

### Unit Tests
- [ ] Unit tests have no ROS 2 imports in test files
- [ ] All domain logic (kinematics, parsers, safety checks) is unit-tested
- [ ] Tests run in < 30 seconds total
- [ ] Coverage ≥ 70% for all tested packages

### Integration Tests
- [ ] `colcon test` passes on a clean build
- [ ] All expected topics and services are verified in tests
- [ ] Tests use `--timeout` to prevent hangs
- [ ] No tests rely on hardware being connected

### Simulation Tests
- [ ] Simulation tests run headless (no display required)
- [ ] Navigation scenario passes with `use_sim_time:=true`
- [ ] Tests clean up (stop nodes) even on failure

### CI/CD
- [ ] GitHub Actions workflow runs on every PR
- [ ] Unit tests are a required check (block merge on failure)
- [ ] Coverage report uploaded on each run
- [ ] Sim tests run on merge to main (not every PR — too slow)

### HIL and Field
- [ ] HIL tests documented with expected pass criteria
- [ ] Bag recording procedure followed for every field test
- [ ] Field test results logged with date, SHA, and pass/fail

---

## Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Unit test imports rclpy | Domain/ROS 2 layers not separated | Move logic to pure Python class, test that |
| Integration test hangs | Node never publishes / no `timeout` | Add `--timeout=30` to pytest, use `wait_for_message` |
| Sim test flaky | Gazebo startup time varies | Increase sleep after launch, retry once |
| `colcon test` skips tests | Missing `pytest` in test deps | Add `pytest` to `test_require` in `setup.py` |
| Coverage too low | Node code not exercised | Add more integration tests, or extract logic |
| HIL test fails on encoder | Wheel slightly slower | Check for debris in wheel, re-grease gearbox |

---

## Next Steps

After implementing the full testing pyramid:

1. **Automate HIL** — See `guides/production-deployment.md` for integrating HIL tests into the deploy gate
2. **Sim-to-real gap analysis** — See `skills/sim_to_real` for domain randomization and reality gap measurement
3. **Mutation testing** — Use `mutmut` to verify your unit tests actually catch bugs
4. **Performance benchmarking** — Add `pytest-benchmark` to track kinematics computation time across commits
5. **Hardware fault injection** — Simulate sensor failures in HIL by unplugging and re-plugging devices mid-test

---

## Resources

- Related skills: `ros2_testing`, `robotics_testing`, `gazebo`, `sim_to_real`, `safety_systems`
- Related guides: `production-deployment.md`, `hardware-integration.md`
- pytest docs: https://docs.pytest.org/
- launch_testing: https://github.com/ros2/launch/tree/rolling/launch_testing
- colcon test: https://colcon.readthedocs.io/en/released/reference/verb/test.html
- act (local CI): https://github.com/nektos/act
