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
