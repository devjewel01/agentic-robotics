---
name: ros2-web-bridge
description: >
  Integrate ROS2 with the web: rosbridge_suite for quick prototyping and Foxglove, or custom
  FastAPI/Flask bridges for production (REST, WebSocket, auth, rate limiting). Use when building
  web dashboards, streaming camera to browser, or exposing ROS2 services as REST APIs.
category: middleware
tags: [ros2, web, rosbridge, fastapi, websocket, rest]
version: "1.0.0"
---

# ROS2 Web Bridge

This skill covers integrating ROS2 with web technologies: **rosbridge_suite** for quick demos and Foxglove/Webviz, and **custom bridges** (FastAPI or Flask) for production dashboards, REST APIs, and controlled WebSocket streaming with authentication and rate limiting.

## When to Use

- Building a web dashboard to monitor or control a robot
- Streaming camera feeds (MJPEG, WebSocket) to a browser
- Exposing ROS2 services or actions as REST endpoints
- Setting up rosbridge for Foxglove, Webviz, or quick prototyping
- Writing a custom bridge with auth, rate limiting, or CORS
- Publishing teleop (e.g. cmd_vel) from a browser
- Running a web server (uvicorn) alongside the rclpy executor without deadlocks

## Quick Start

```bash
# rosbridge (quick prototype; no auth)
sudo apt install ros-${ROS_DISTRO}-rosbridge-suite
ros2 launch rosbridge_server rosbridge_websocket_launch.xml

# Connect from browser: ws://robot-ip:9090
# Use roslibjs or Foxglove to subscribe/publish.
```

## Core Concepts

### rosbridge vs Custom Bridge

| | rosbridge_suite | Custom FastAPI/Flask |
|--|-----------------|----------------------|
| Latency | ~5–15 ms (WebSocket) | ~2–5 ms (WebSocket), ~10–30 ms (REST) |
| Auth | Basic (rosauth) | Full (JWT, API keys) |
| Topic filtering | Exposes full graph | Expose only chosen topics/services |
| Production | Not recommended (full graph exposed) | Yes, with rate limiting and CORS |
| When to use | Prototyping, Foxglove, demos | Production APIs, dashboards, video control |

Use **rosbridge** when you need a working bridge in minutes and the client is Foxglove or another rosbridge-aware tool. Use a **custom bridge** when you need auth, selected topics only, REST, or production deployment.

## Common Patterns

### rosbridge_suite: Install and Launch

```bash
sudo apt install ros-${ROS_DISTRO}-rosbridge-suite
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
# Custom port / SSL:
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9091 ssl:=true \
  certfile:=/path/to/cert.pem keyfile:=/path/to/key.pem
```

### roslibjs: Connect and Publish cmd_vel

```javascript
const ros = new ROSLIB.Ros({ url: 'ws://robot-host:9090' });
const cmdVel = new ROSLIB.Topic({
  ros, name: '/cmd_vel', messageType: 'geometry_msgs/msg/Twist'
});
function send(linearX, angularZ) {
  cmdVel.publish(new ROSLIB.Message({
    linear: { x: linearX, y: 0, z: 0 },
    angular: { x: 0, y: 0, z: angularZ }
  }));
}
// Send zero on release to stop the robot
send(0, 0);
```

### Custom Bridge: ROS2 Node with Shared State

Keep a single rclpy node that subscribes to topics and keeps the latest message in thread-safe state; FastAPI reads from this state and publishes cmd_vel or calls services.

```python
# ros_node.py (simplified)
import threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import CompressedImage
from geometry_msgs.msg import Twist

class RobotBridgeNode(Node):
    def __init__(self):
        super().__init__('web_bridge_node')
        self._lock = threading.Lock()
        self._latest_image = None
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST, depth=1)
        self.create_subscription(
            CompressedImage, '/camera/image/compressed', self._image_cb, sensor_qos)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

    def _image_cb(self, msg):
        with self._lock:
            self._latest_image = bytes(msg.data)

    def get_latest_image(self):
        with self._lock:
            return self._latest_image

    def publish_cmd_vel(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self.cmd_vel_pub.publish(msg)
```

### Custom Bridge: FastAPI + rclpy in One Process

Run rclpy in a background thread and uvicorn in the main thread; coordinate shutdown so both exit cleanly.

```python
# main.py
import threading
import rclpy
from rclpy.executors import MultiThreadedExecutor
import uvicorn
from .ros_node import RobotBridgeNode
from .web_app import create_app

def main():
    rclpy.init()
    node = RobotBridgeNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    thread = threading.Thread(target=executor.spin, daemon=True)
    thread.start()
    app = create_app(node)
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
```

### REST Endpoints Wrapping ROS2

Expose only what the dashboard needs; validate input (e.g. clamp cmd_vel).

```python
# In FastAPI app
@app.get("/api/robot/status")
async def get_status():
    odom = app.state.ros_node.get_latest_odom()
    if odom is None:
        raise HTTPException(503, "No odometry yet")
    return {"status": "active", "odometry": odom}

@app.post("/api/robot/cmd_vel")
async def post_cmd_vel(cmd: CmdVelRequest):
    # Clamp in Pydantic model: ge=-1, le=1 for linear_x
    app.state.ros_node.publish_cmd_vel(cmd.linear_x, cmd.angular_z)
    return {"status": "ok"}
```

## Anti-Patterns

### Using rosbridge in production without auth

rosbridge exposes the full topic graph; any client can publish to `/cmd_vel`. Use only on trusted networks or behind a custom gateway that restricts and authenticates.

### Blocking the async event loop with rclpy

Do not call `rclpy.spin()` in the same thread as uvicorn. Run rclpy in a separate thread (executor.spin()) and share state via thread-safe attributes.

### Sending raw high-rate topics to the browser

Throttle or sample (e.g. 10 Hz) and use compressed images; otherwise latency and bandwidth overwhelm the client.

### Forgetting to send zero velocity on disconnect

When the user releases the joystick or closes the page, send cmd_vel (0, 0) so the robot stops.

## Configuration Reference

| Parameter | Description |
|-----------|-------------|
| rosbridge port | Default 9090; set via launch port:=9091 |
| rosbridge ssl | certfile, keyfile for wss:// |
| CORS allow_origins | Restrict to your dashboard origin in production |
| WebSocket max_fps | Throttle camera stream per client (e.g. 10–15) |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Browser cannot connect to rosbridge | Firewall or CORS | Open port 9090; for REST/WS from browser, set CORS on your server |
| "Connection refused" to ROS2 from web server | rclpy not spinning | Run executor in a daemon thread so callbacks run |
| High latency on camera stream | No throttling or huge frames | Throttle (e.g. 10 Hz), use compressed topic, reduce resolution |
| Robot keeps moving after closing dashboard | No zero on disconnect | On WebSocket close or page unload, send cmd_vel (0, 0) |

## Workflow Integration

- For ROS2 nodes and QoS see `skills/ros2/SKILL.md`; for production deployment and security see `safety-systems` and `robot-bringup`.
- For a WebSocket CLI that talks to rosbridge (e.g. from scripts), see the `references/ros-skill` reference; this skill focuses on web dashboards and production bridges.

---

## Extended Core Concepts

### rosbridge WebSocket Protocol

rosbridge_suite implements a JSON-over-WebSocket protocol. Every message is a JSON object with an `op` field that describes the operation. Understanding the wire format helps debug issues that roslibjs abstracts away.

**Key operations:**

| `op` | Direction | Purpose |
|------|-----------|---------|
| `advertise` | Client → Server | Declare that the client will publish to a topic |
| `publish` | Client → Server | Send a message to a topic |
| `subscribe` | Client → Server | Request messages from a topic |
| `unsubscribe` | Client → Server | Cancel a subscription |
| `call_service` | Client → Server | Call a ROS2 service |
| `advertise_service` | Client → Server | Expose a client-side service to ROS |
| `publish` | Server → Client | Deliver a subscribed topic message |
| `service_response` | Server → Client | Return service call result |

**Wire format examples:**

```json
// Subscribe to /scan
{ "op": "subscribe", "topic": "/scan", "type": "sensor_msgs/msg/LaserScan", "throttle_rate": 200 }

// Publish cmd_vel
{
  "op": "publish",
  "topic": "/cmd_vel",
  "msg": { "linear": {"x": 0.3, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.5} }
}

// Call a service
{ "op": "call_service", "service": "/orbibot/reset_odometry", "args": {}, "id": "req_001" }

// Service response from server
{ "op": "service_response", "service": "/orbibot/reset_odometry", "values": {"success": true}, "id": "req_001" }
```

**Throttle and compression options in subscribe:**

```json
{
  "op": "subscribe",
  "topic": "/camera/image_raw/compressed",
  "type": "sensor_msgs/msg/CompressedImage",
  "throttle_rate": 100,
  "queue_length": 1,
  "compression": "png"
}
```

- `throttle_rate` (ms): minimum time between messages delivered to the client
- `queue_length`: how many messages to buffer; `1` means always get the latest
- `compression`: `"png"` or `"cbor"` for binary encoding (reduces JSON overhead ~40%)

### roslibjs Client Patterns

roslibjs is the official JavaScript client for rosbridge. It wraps the wire protocol into an event-driven API.

**Connection lifecycle and error handling:**

```javascript
const ros = new ROSLIB.Ros({
  url: 'ws://robot-host:9090'
});

ros.on('connection', () => {
  console.log('Connected to rosbridge');
  startSubscriptions();
});

ros.on('error', (error) => {
  console.error('rosbridge error:', error);
});

ros.on('close', () => {
  console.warn('rosbridge connection closed — attempting reconnect in 3s');
  setTimeout(() => ros.connect('ws://robot-host:9090'), 3000);
});
```

**Topic subscriber with throttling:**

```javascript
const odomSub = new ROSLIB.Topic({
  ros: ros,
  name: '/odometry/filtered',
  messageType: 'nav_msgs/msg/Odometry',
  throttle_rate: 100,    // max 10 Hz to browser
  queue_length: 1        // always latest
});

odomSub.subscribe((msg) => {
  const { x, y } = msg.pose.pose.position;
  updateRobotMarker(x, y);
});

// Unsubscribe when component unmounts
odomSub.unsubscribe();
```

**Service call from JavaScript:**

```javascript
const resetOdom = new ROSLIB.Service({
  ros: ros,
  name: '/orbibot/reset_odometry',
  serviceType: 'orbibot_msgs/srv/ResetOdometry'
});

resetOdom.callService(new ROSLIB.ServiceRequest({}), (result) => {
  console.log('Odometry reset:', result);
}, (error) => {
  console.error('Service call failed:', error);
});
```

**Parameter read/write:**

```javascript
const batteryParam = new ROSLIB.Param({
  ros: ros,
  name: '/orbibot/battery_warning_voltage'
});

batteryParam.get((value) => {
  console.log('Warning voltage:', value);
});

batteryParam.set(11.2, (result) => {
  console.log('Parameter updated:', result);
});
```

### FastAPI/Flask REST Bridge

A custom bridge exposes only the endpoints your dashboard needs, adds authentication, validates input, and keeps the ROS2 node completely isolated in a background thread.

**Architecture:**

```
Browser ─── HTTP/WS ──→ FastAPI (uvicorn, main thread)
                              │
                         thread-safe state (dict / dataclass)
                              │
                    rclpy node (MultiThreadedExecutor, daemon thread)
                              │
                         ROS2 middleware (DDS)
```

**Shared state pattern using a dataclass:**

```python
# bridge/state.py
import threading
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RobotState:
    """Thread-safe shared state between rclpy node and FastAPI handlers."""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    battery_voltage: float = 0.0
    odom_x: float = 0.0
    odom_y: float = 0.0
    odom_yaw: float = 0.0
    latest_scan_ranges: list = field(default_factory=list)
    is_emergency_stop: bool = False

    def update_odom(self, x: float, y: float, yaw: float) -> None:
        with self._lock:
            self.odom_x = x
            self.odom_y = y
            self.odom_yaw = yaw

    def get_odom_snapshot(self) -> dict:
        with self._lock:
            return {"x": self.odom_x, "y": self.odom_y, "yaw": self.odom_yaw}
```

**ROS2 node writing to shared state:**

```python
# bridge/ros_node.py
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from .state import RobotState

class BridgeNode(Node):
    def __init__(self, state: RobotState):
        super().__init__('web_bridge_node')
        self._state = state

        self.create_subscription(Odometry, '/odometry/filtered',
                                  self._odom_cb, 10)
        self.create_subscription(LaserScan, '/scan',
                                  self._scan_cb, qos_profile_sensor_data)

        self._cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self._safety_timer = self.create_timer(0.5, self._safety_watchdog)
        self._last_cmd_time = self.get_clock().now()

    def _odom_cb(self, msg: Odometry) -> None:
        # Extract yaw from quaternion
        q = msg.pose.pose.orientation
        yaw = math.atan2(2*(q.w*q.z + q.x*q.y), 1 - 2*(q.y**2 + q.z**2))
        self._state.update_odom(
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            yaw
        )

    def _scan_cb(self, msg: LaserScan) -> None:
        # Sample every 10th range to reduce state size
        with self._state._lock:
            self._state.latest_scan_ranges = msg.ranges[::10]

    def publish_cmd_vel(self, linear_x: float, angular_z: float) -> None:
        """Publish velocity command and record time for watchdog."""
        msg = Twist()
        msg.linear.x = max(-0.5, min(0.5, float(linear_x)))   # Safety clamp
        msg.angular.z = max(-1.9, min(1.9, float(angular_z)))
        self._cmd_vel_pub.publish(msg)
        self._last_cmd_time = self.get_clock().now()

    def _safety_watchdog(self) -> None:
        """Stop robot if no cmd_vel received for 1 second."""
        elapsed = (self.get_clock().now() - self._last_cmd_time).nanoseconds / 1e9
        if elapsed > 1.0 and not self._state.is_emergency_stop:
            stop = Twist()
            self._cmd_vel_pub.publish(stop)
```

### MJPEG Camera Streaming

MJPEG streams a sequence of JPEG frames in a single HTTP response using `multipart/x-mixed-replace`. It works in any `<img>` tag without JavaScript libraries.

```python
# bridge/camera_stream.py
import asyncio
from fastapi import Response
from fastapi.responses import StreamingResponse
from sensor_msgs.msg import CompressedImage
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
import threading

class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_bridge')
        self._lock = threading.Lock()
        self._latest_jpeg: bytes = b''
        self.create_subscription(
            CompressedImage,
            '/camera/color/image_raw/compressed',
            self._image_cb,
            qos_profile_sensor_data
        )

    def _image_cb(self, msg: CompressedImage) -> None:
        with self._lock:
            self._latest_jpeg = bytes(msg.data)

    def get_frame(self) -> bytes:
        with self._lock:
            return self._latest_jpeg

# In FastAPI app
async def mjpeg_generator(camera_node: CameraNode):
    """Async generator yielding MJPEG frames."""
    while True:
        frame = camera_node.get_frame()
        if frame:
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                frame +
                b'\r\n'
            )
        await asyncio.sleep(1 / 15)  # 15 fps cap

# Route
@app.get("/video/mjpeg")
async def mjpeg_stream():
    camera_node = app.state.camera_node
    return StreamingResponse(
        mjpeg_generator(camera_node),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )
```

HTML usage — no JavaScript needed:
```html
<img src="/video/mjpeg" width="640" height="480" alt="Robot camera" />
```

### ROS2 Service and Action Proxying to HTTP

Wrap ROS2 service calls in FastAPI endpoints. Use `asyncio.get_event_loop().run_in_executor` to call synchronous rclpy service calls without blocking the async event loop.

```python
# bridge/service_proxy.py
import asyncio
import concurrent.futures
from fastapi import HTTPException
from pydantic import BaseModel
from orbibot_msgs.srv import SetMotorEnable, ResetOdometry

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

class MotorEnableRequest(BaseModel):
    enable: bool

@app.post("/api/motors/enable")
async def set_motor_enable(req: MotorEnableRequest):
    """Proxy HTTP POST → ROS2 service call."""
    loop = asyncio.get_event_loop()

    def _call_service():
        node = app.state.ros_node
        client = node.create_client(SetMotorEnable, '/orbibot/set_motor_enable')
        if not client.wait_for_service(timeout_sec=2.0):
            return None
        request = SetMotorEnable.Request()
        request.enable = req.enable
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)
        return future.result()

    result = await loop.run_in_executor(_executor, _call_service)
    if result is None:
        raise HTTPException(503, "Service /orbibot/set_motor_enable unavailable")
    return {"success": result.success, "message": result.message}

@app.post("/api/odometry/reset")
async def reset_odometry():
    loop = asyncio.get_event_loop()

    def _call():
        node = app.state.ros_node
        client = node.create_client(ResetOdometry, '/orbibot/reset_odometry')
        if not client.wait_for_service(timeout_sec=2.0):
            return None
        future = client.call_async(ResetOdometry.Request())
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)
        return future.result()

    result = await loop.run_in_executor(_executor, _call)
    if result is None:
        raise HTTPException(503, "Service unavailable")
    return {"success": True}
```

---

## Extended Common Patterns

### rosbridge_server Full Setup with Parameters

```bash
# Install
sudo apt install ros-${ROS_DISTRO}-rosbridge-suite

# Launch with common options
ros2 launch rosbridge_server rosbridge_websocket_launch.xml \
  port:=9090 \
  address:=0.0.0.0 \
  retry_startup_delay:=5.0 \
  unregister_timeout:=10.0 \
  max_message_size:=10000000
```

As a ROS2 launch file with parameters:

```python
# launch/rosbridge.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            parameters=[{
                'port': 9090,
                'address': '0.0.0.0',
                'retry_startup_delay': 5.0,
                'unregister_timeout': 10.0,
                'max_message_size': 10_000_000,   # 10 MB for image messages
                'send_action_goals_in_new_thread': True,
                'topics_glob': '[*]',             # Allow all topics (restrict in production)
                'services_glob': '[*]',
                'params_glob': '[*]',
            }],
            output='screen'
        )
    ])
```

### roslibjs Subscriber and Publisher — Complete Example

```javascript
// robot_control.js — complete pattern with reconnection and cleanup
class RobotBridge {
  constructor(url) {
    this.url = url;
    this.ros = null;
    this.subscriptions = new Map();
    this.publishers = new Map();
    this._connect();
  }

  _connect() {
    this.ros = new ROSLIB.Ros({ url: this.url });

    this.ros.on('connection', () => {
      console.log('Connected');
      this._setupTopics();
    });

    this.ros.on('close', () => {
      console.warn('Disconnected — reconnecting in 3s');
      setTimeout(() => this._connect(), 3000);
    });
  }

  _setupTopics() {
    // Subscribe to odometry
    const odom = new ROSLIB.Topic({
      ros: this.ros,
      name: '/odometry/filtered',
      messageType: 'nav_msgs/msg/Odometry',
      throttle_rate: 100,
      queue_length: 1
    });
    odom.subscribe(this._onOdom.bind(this));
    this.subscriptions.set('odom', odom);

    // Subscribe to battery status
    const battery = new ROSLIB.Topic({
      ros: this.ros,
      name: '/orbibot/system_status',
      messageType: 'orbibot_msgs/msg/SystemStatus',
      throttle_rate: 2000   // 0.5 Hz — no need for high rate
    });
    battery.subscribe(this._onStatus.bind(this));
    this.subscriptions.set('battery', battery);

    // Set up cmd_vel publisher
    const cmdVel = new ROSLIB.Topic({
      ros: this.ros,
      name: '/cmd_vel',
      messageType: 'geometry_msgs/msg/Twist'
    });
    cmdVel.advertise();
    this.publishers.set('cmd_vel', cmdVel);
  }

  _onOdom(msg) {
    const pos = msg.pose.pose.position;
    document.getElementById('pos-x').textContent = pos.x.toFixed(3);
    document.getElementById('pos-y').textContent = pos.y.toFixed(3);
  }

  _onStatus(msg) {
    document.getElementById('battery').textContent =
      msg.battery_voltage.toFixed(1) + ' V';
  }

  sendVelocity(linearX, angularZ) {
    const pub = this.publishers.get('cmd_vel');
    if (!pub) return;
    pub.publish(new ROSLIB.Message({
      linear:  { x: linearX, y: 0, z: 0 },
      angular: { x: 0, y: 0, z: angularZ }
    }));
  }

  stop() {
    this.sendVelocity(0, 0);
  }

  destroy() {
    this.stop();
    this.subscriptions.forEach(sub => sub.unsubscribe());
    this.publishers.forEach(pub => pub.unadvertise());
    this.ros.close();
  }
}

// Usage
const bridge = new RobotBridge('ws://robot-host:9090');

// Gamepad integration
window.addEventListener('gamepadconnected', () => {
  setInterval(() => {
    const gp = navigator.getGamepads()[0];
    if (gp) {
      bridge.sendVelocity(-gp.axes[1] * 0.5, -gp.axes[0] * 1.9);
    }
  }, 100);  // 10 Hz
});

// Stop on page close
window.addEventListener('beforeunload', () => bridge.stop());
```

### FastAPI Endpoint Calling a ROS2 Service

Full working example with Pydantic input validation, timeout handling, and structured errors:

```python
# bridge/web_app.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
import concurrent.futures

def create_app(ros_node) -> FastAPI:
    app = FastAPI(title="OrbiBot Bridge API", version="1.0.0")

    # Configure CORS — restrict in production to your dashboard origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://dashboard.local"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.state.ros_node = ros_node
    app.state.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    class CmdVelRequest(BaseModel):
        linear_x: float = Field(0.0, ge=-0.5, le=0.5, description="Forward speed m/s")
        linear_y: float = Field(0.0, ge=-0.5, le=0.5, description="Lateral speed m/s (mecanum)")
        angular_z: float = Field(0.0, ge=-1.9, le=1.9, description="Rotation rad/s")

    @app.get("/api/robot/status")
    async def get_status():
        state = app.state.ros_node.get_state_snapshot()
        return {
            "connected": True,
            "position": {"x": state["odom_x"], "y": state["odom_y"]},
            "battery_voltage": state["battery_voltage"],
            "emergency_stop": state["is_emergency_stop"],
        }

    @app.post("/api/robot/cmd_vel")
    async def post_cmd_vel(cmd: CmdVelRequest):
        if app.state.ros_node.state.is_emergency_stop:
            raise HTTPException(403, "Emergency stop active — reset before driving")
        app.state.ros_node.publish_cmd_vel(cmd.linear_x, cmd.angular_z)
        return {"status": "ok"}

    @app.post("/api/robot/stop")
    async def emergency_stop():
        app.state.ros_node.publish_cmd_vel(0.0, 0.0)
        app.state.ros_node.state.is_emergency_stop = True
        return {"status": "stopped"}

    @app.post("/api/robot/resume")
    async def resume():
        app.state.ros_node.state.is_emergency_stop = False
        return {"status": "resumed"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
```

### WebSocket-Based cmd_vel Publisher from Browser Joystick

For low-latency control, use a WebSocket instead of polling REST. FastAPI WebSocket handler with per-connection watchdog:

```python
# bridge/ws_control.py
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/control")
async def ws_control(websocket: WebSocket):
    await websocket.accept()
    ros_node = app.state.ros_node
    last_received = asyncio.get_event_loop().time()

    async def watchdog():
        """Send zero velocity if no message received for 1 second."""
        nonlocal last_received
        while True:
            await asyncio.sleep(0.2)
            if asyncio.get_event_loop().time() - last_received > 1.0:
                ros_node.publish_cmd_vel(0.0, 0.0)

    watchdog_task = asyncio.create_task(watchdog())

    try:
        while True:
            data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            msg = json.loads(data)
            last_received = asyncio.get_event_loop().time()

            if msg.get("type") == "cmd_vel":
                ros_node.publish_cmd_vel(
                    msg.get("linear_x", 0.0),
                    msg.get("angular_z", 0.0)
                )
            elif msg.get("type") == "stop":
                ros_node.publish_cmd_vel(0.0, 0.0)

    except (WebSocketDisconnect, asyncio.TimeoutError):
        ros_node.publish_cmd_vel(0.0, 0.0)   # Safety stop on disconnect
    finally:
        watchdog_task.cancel()
        await websocket.close()
```

Browser-side WebSocket joystick:

```javascript
// ws_joystick.js
class WsJoystick {
  constructor(url) {
    this.ws = new WebSocket(url);
    this.ws.onopen = () => console.log('WS control connected');
    this.ws.onclose = () => {
      console.warn('WS closed');
      setTimeout(() => new WsJoystick(url), 2000);
    };
    // Send zero on page close
    window.addEventListener('beforeunload', () => this.stop());
  }

  send(linearX, angularZ) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'cmd_vel', linear_x: linearX, angular_z: angularZ }));
    }
  }

  stop() {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'stop' }));
    }
  }
}

const joystick = new WsJoystick('ws://robot-host:8000/ws/control');

// Keyboard control
const keys = {};
document.addEventListener('keydown', e => { keys[e.key] = true; });
document.addEventListener('keyup',   e => { keys[e.key] = false; joystick.stop(); });

setInterval(() => {
  const lx = (keys['ArrowUp'] ? 0.3 : 0) - (keys['ArrowDown'] ? 0.3 : 0);
  const az = (keys['ArrowLeft'] ? 1.0 : 0) - (keys['ArrowRight'] ? 1.0 : 0);
  if (lx !== 0 || az !== 0) joystick.send(lx, az);
}, 100);
```

---

## Extended Anti-Patterns

### Blocking ROS2 calls in async web handlers

❌ **Wrong** — calling synchronous rclpy functions in an async FastAPI handler blocks the event loop, freezing all other requests:
```python
@app.post("/api/reset")
async def reset():
    # rclpy.spin_until_future_complete blocks the event loop thread
    future = client.call_async(ResetOdometry.Request())
    rclpy.spin_until_future_complete(node, future)   # BLOCKS — never do this in async
    return {"ok": True}
```

✅ **Correct** — offload blocking rclpy calls to a thread pool executor:
```python
import asyncio
import concurrent.futures

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

@app.post("/api/reset")
async def reset():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, _blocking_reset_call)
    return {"ok": result is not None}

def _blocking_reset_call():
    future = client.call_async(ResetOdometry.Request())
    rclpy.spin_until_future_complete(node, future, timeout_sec=5.0)
    return future.result()
```

### No authentication on rosbridge

❌ **Wrong** — rosbridge open to the internet or an untrusted LAN with no auth:
```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
# Any browser tab or script on the network can now publish to /cmd_vel
```

✅ **Correct** — for production, run rosbridge behind a custom FastAPI gateway that requires a token, or restrict rosbridge to localhost only and proxy through your authenticated API:
```python
# In custom bridge: validate API key before forwarding
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        token = request.headers.get("X-API-Key")
        if token != os.environ["BRIDGE_API_KEY"]:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)
```

If rosbridge must be used directly, bind it to `127.0.0.1` and proxy via nginx with HTTP basic auth:
```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml address:=127.0.0.1
```

### Publishing to cmd_vel from untrusted web clients without safety checks

❌ **Wrong** — accepting raw velocity values from the web and publishing directly:
```python
@app.post("/api/cmd_vel")
async def cmd_vel(linear_x: float, angular_z: float):
    # No validation — attacker can send linear_x=999.0
    node.publish_cmd_vel(linear_x, angular_z)
```

✅ **Correct** — clamp values in the Pydantic model, check emergency stop state, and apply a software watchdog:
```python
class CmdVelRequest(BaseModel):
    linear_x: float = Field(0.0, ge=-0.5, le=0.5)  # Clamped by Pydantic
    angular_z: float = Field(0.0, ge=-1.9, le=1.9)

@app.post("/api/cmd_vel")
async def cmd_vel(cmd: CmdVelRequest):
    if node.state.is_emergency_stop:
        raise HTTPException(403, "E-stop active")
    node.publish_cmd_vel(cmd.linear_x, cmd.angular_z)  # Already clamped by model
    return {"ok": True}
```

### Not handling WebSocket disconnect — robot keeps moving

❌ **Wrong** — WebSocket handler that publishes velocity but has no disconnect cleanup:
```python
@app.websocket("/ws/control")
async def ws_control(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = json.loads(await websocket.receive_text())
        node.publish_cmd_vel(data["lx"], data["az"])
    # If browser closes → WebSocketDisconnect exception → node.publish_cmd_vel never called with 0
    # Robot continues at last commanded velocity indefinitely
```

✅ **Correct** — always send zero velocity in a `finally` block and in the watchdog:
```python
@app.websocket("/ws/control")
async def ws_control(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            node.publish_cmd_vel(data["lx"], data["az"])
    except WebSocketDisconnect:
        pass
    finally:
        node.publish_cmd_vel(0.0, 0.0)   # Always stop on disconnect
```

### Sending uncompressed image topics to the browser at full rate

❌ **Wrong** — subscribing to the raw image topic and forwarding every frame:
```python
# Subscribing to /camera/color/image_raw (uncompressed, ~15 MB/s at 1080p/15Hz)
# then forwarding base64-encoded to a WebSocket client = browser chokes
```

✅ **Correct** — subscribe to the compressed topic, throttle frame rate, and stream as MJPEG:
```python
# Subscribe to /camera/color/image_raw/compressed (JPEG, ~100-400 kB/s at 15Hz)
# Deliver via MJPEG endpoint capped at 15 fps
# If compressed topic not available, add image_transport republish node:
# ros2 run image_transport republish raw --ros-args \
#   -r in:=/camera/color/image_raw -r out/compressed:=/camera/color/image_raw/compressed
```

---

## Extended Configuration Reference

### rosbridge_server Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `port` | `9090` | WebSocket listen port |
| `address` | `0.0.0.0` | Bind address — use `127.0.0.1` to restrict to localhost |
| `retry_startup_delay` | `5.0` | Seconds to wait before retrying if ROS graph not ready |
| `unregister_timeout` | `10.0` | Seconds before unregistering an unresponsive client |
| `max_message_size` | `None` | Max WebSocket message bytes — set to `10000000` (10 MB) for image messages |
| `send_action_goals_in_new_thread` | `False` | Prevent action goals from blocking the WebSocket handler |
| `topics_glob` | `[*]` | Glob pattern to allow/deny topics — e.g. `[/odom, /scan, /cmd_vel]` |
| `services_glob` | `[*]` | Glob pattern for services |
| `params_glob` | `[*]` | Glob pattern for parameters |
| `ssl` | `False` | Enable TLS — requires `certfile` and `keyfile` |
| `certfile` | `""` | Path to TLS certificate file for `wss://` |
| `keyfile` | `""` | Path to TLS private key file |

### FastAPI / uvicorn Route Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| `GET /api/robot/status` | Snapshot of robot state — fast, reads shared state | Returns odom, battery, E-stop flag |
| `POST /api/robot/cmd_vel` | Publish velocity — validates with Pydantic, checks E-stop | Body: `{linear_x, angular_z}` |
| `GET /video/mjpeg` | StreamingResponse MJPEG — works in `<img>` tag | `StreamingResponse(generator, media_type='multipart/x-mixed-replace; boundary=frame')` |
| `WS /ws/control` | Low-latency bidirectional control channel | JSON frames: `{type, linear_x, angular_z}` |
| `POST /api/services/{name}` | Generic service proxy — body is service request JSON | Dynamic dispatch via service registry |
| `GET /health` | Liveness probe for Docker/k8s | Returns `{"status": "ok"}` |

### roslibjs Subscribe Options

| Option | Type | Description |
|--------|------|-------------|
| `throttle_rate` | ms | Minimum interval between messages (e.g. `100` = 10 Hz max) |
| `queue_length` | int | Messages to buffer; `1` = always latest, `0` = unlimited |
| `compression` | string | `"none"` (default), `"png"`, `"cbor"` — cbor reduces overhead ~40% |
| `reconnect_on_close` | bool | Auto-resubscribe after reconnect (handled by roslibjs reconnect logic) |

---

## Extended Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| CORS error in browser console (`Access-Control-Allow-Origin`) | FastAPI CORS middleware not configured, or wrong origin | Add `CORSMiddleware` with the exact dashboard origin; for development use `allow_origins=["*"]` but never in production |
| WebSocket connection closes after ~60 seconds with no activity | Reverse proxy (nginx, AWS ALB) idle timeout | Send a WebSocket ping every 30 seconds from the client: `ros.socket.ping()` or add nginx `proxy_read_timeout 3600` |
| rosbridge message type mismatch (`TypeError: Cannot read properties of undefined`) | roslibjs `messageType` does not match actual topic type | Run `ros2 topic info /topic_name` to get the exact type string; use `pkg/msg/Type` format (not `pkg/Type`) in roslibjs |
| High latency on MJPEG stream (>500 ms) | Uncompressed images or missing throttle | Subscribe to `/camera/color/image_raw/compressed`; cap MJPEG generator at 10–15 fps with `asyncio.sleep` |
| `rclpy.spin_until_future_complete` hangs indefinitely in service proxy | Service not running or DDS discovery issue | Add `timeout_sec=5.0`; check `ros2 service list` includes the service; ensure `ROS_DOMAIN_ID` matches between bridge and robot |
| Robot keeps moving after browser tab closes | No zero velocity on WebSocket disconnect | Send `cmd_vel(0, 0)` in `finally` block of the WebSocket handler; add a server-side watchdog timer |
| `uvicorn` and `rclpy` interfere — callbacks not called | Both trying to use same event loop or rclpy not spinning | Run `rclpy` `executor.spin()` in a separate `daemon=True` thread; never call `rclpy.spin()` in the main thread |
| `405 Method Not Allowed` on CORS preflight | FastAPI not handling OPTIONS requests | Add `allow_methods=["*"]` or explicitly include `OPTIONS` in CORSMiddleware |
| Image WebSocket frames too large — browser drops connection | Sending raw uncompressed image bytes | Use MJPEG streaming endpoint instead of WebSocket for video; or compress each frame to JPEG before sending over WebSocket |
