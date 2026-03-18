---
name: robot-bringup
description: >
  Bring up a complete ROS2 robot stack on the onboard computer: systemd services, layered launch
  files, ordered startup, udev rules, watchdog, and production monitoring. Use when configuring
  robot startup on boot, systemd for ROS2, launch composition, udev for cameras/serial, or debugging
  boot-time failures.
category: devops
tags: [ros2, systemd, launch, udev, bringup, production]
version: "1.0.0"
---

# Robot Bringup

This skill covers bringing up a full ROS2-based robot stack on the onboard computer: systemd services, layered launch files, udev rules for deterministic device naming, ordered startup with health checks, and production monitoring. For a first power-on checklist see [guides/robot-bringup.md](../../guides/robot-bringup.md).

## When to Use

- Configuring the robot to start its full ROS2 stack on boot via systemd
- Writing systemd unit files that source ROS2 workspaces and set DDS environment
- Composing layered launch files (hardware, drivers, perception, application) into one bringup
- Setting up ordered startup with health checks to avoid race conditions
- Writing udev rules for deterministic device naming (cameras, LiDARs, serial)
- Configuring CycloneDDS or FastDDS for multi-machine ROS2 discovery
- Implementing watchdog and heartbeat monitoring for production
- Setting up log rotation and graceful shutdown for long-running deployments
- Debugging boot-time failures, service ordering, or device enumeration races

## Quick Start

```bash
# 1. Create environment file (systemd does not load .bashrc)
sudo mkdir -p /etc/robot
echo 'ROS_DISTRO=humble
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_DOMAIN_ID=0' | sudo tee /etc/robot/ros2.env

# 2. Create systemd service
sudo tee /etc/systemd/system/robot-bringup.service << 'EOF'
[Unit]
Description=Robot ROS2 Bringup
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=robot
Group=robot
EnvironmentFile=/etc/robot/ros2.env
ExecStart=/bin/bash -c 'source /opt/ros/${ROS_DISTRO}/setup.bash && source /home/robot/ros2_ws/install/setup.bash && exec ros2 launch my_robot_bringup bringup.launch.py'
Restart=on-failure
RestartSec=5
KillSignal=SIGINT
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# 3. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable robot-bringup.service
sudo systemctl start robot-bringup.service
sudo systemctl status robot-bringup.service
```

## Core Concepts

### The Robot Bringup Stack

Startup flows from hardware through drivers, perception, and application. Each layer depends on the one below.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                             │
│  Navigation, manipulation, mission planning                          │
├─────────────────────────────────────────────────────────────────────┤
│                        PERCEPTION LAYER                              │
│  SLAM, detection, sensor fusion                                     │
├─────────────────────────────────────────────────────────────────────┤
│                         DRIVER LAYER                                 │
│  Camera, LiDAR, IMU, motor drivers                                  │
├─────────────────────────────────────────────────────────────────────┤
│                        HARDWARE LAYER                                │
│  udev rules, device enumeration, firmware check                     │
├─────────────────────────────────────────────────────────────────────┤
│                      ROS2 ENVIRONMENT                               │
│  Source workspace, RMW, ROS_DOMAIN_ID, DDS config                  │
├─────────────────────────────────────────────────────────────────────┤
│                    SYSTEMD TARGETS & SERVICES                       │
│  network-online.target → robot-bringup.target                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Launch Layer Architecture

Organize launch files to mirror the stack so each layer can be tested in isolation.

```
bringup.launch.py
├── hardware.launch.py     (udev checks, device readiness)
├── drivers.launch.py      (camera, LiDAR, IMU, motors)
├── perception.launch.py   (SLAM, detection)
└── application.launch.py (navigation, mission)
```

## Common Patterns

### systemd Service Unit with Watchdog

Place in `/etc/systemd/system/`. Use `EnvironmentFile` for ROS2; do not rely on `.bashrc`.

```ini
[Unit]
Description=Robot ROS2 Bringup Stack
After=network-online.target robot-hw.target
Wants=network-online.target
Requires=robot-hw.target

[Service]
Type=notify
User=robot
Group=robot
WorkingDirectory=/home/robot
EnvironmentFile=/etc/robot/ros2.env

ExecStartPre=/usr/local/bin/robot-device-check.sh
ExecStart=/bin/bash -c '\
  source /opt/ros/${ROS_DISTRO}/setup.bash && \
  source /home/robot/ros2_ws/install/setup.bash && \
  exec ros2 launch my_robot_bringup bringup.launch.py'

ExecStop=/bin/kill -INT $MAINPID
TimeoutStopSec=30
Restart=on-failure
RestartSec=5
StartLimitIntervalSec=120
StartLimitBurst=5
WatchdogSec=30
KillMode=mixed
KillSignal=SIGINT
StandardOutput=journal
SyslogIdentifier=robot-bringup

[Install]
WantedBy=multi-user.target
```

### ROS2 Environment File

Store in `/etc/robot/ros2.env` and load via `EnvironmentFile` in the unit.

```bash
ROS_DISTRO=humble
RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_DOMAIN_ID=42
CYCLONEDDS_URI=file:///etc/robot/cyclonedds.xml
ROS_LOCALHOST_ONLY=0
ROS_LOG_DIR=/var/log/ros2
RCUTILS_LOGGING_USE_STDOUT=0
ROBOT_NAME=my_robot_01
```

### Layered systemd Services

Split drivers, perception, and application into separate services with explicit ordering.

```ini
# robot-drivers.service
[Unit]
After=network-online.target robot-hw.target
Requires=robot-hw.target
[Install]
WantedBy=robot-bringup.target

# robot-perception.service
[Unit]
After=robot-drivers.service
Requires=robot-drivers.service
[Install]
WantedBy=robot-bringup.target

# robot-application.service
[Unit]
After=robot-perception.service
Requires=robot-perception.service
[Install]
WantedBy=robot-bringup.target
```

### udev Rules for Cameras

Stable symlinks so `/dev/video0` is not used directly. Find attributes with `udevadm info --name=/dev/video0 --attribute-walk`.

```bash
# /etc/udev/rules.d/99-robot-cameras.rules
SUBSYSTEM=="video4linux", ATTRS{idVendor}=="1234", ATTRS{idProduct}=="5678", \
  KERNELS=="1-1.2:1.0", ATTR{index}=="0", \
  SYMLINK+="robot/camera_front", MODE="0666", GROUP="video"
```

### udev Rules for Serial Devices

Stable names for IMU, LiDAR, motor controller (e.g. `/dev/robot/imu`, `/dev/robot/lidar`).

```bash
# /etc/udev/rules.d/99-robot-serial.rules
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", \
  ATTRS{serial}=="AB0CDEFG", \
  SYMLINK+="robot/imu", MODE="0666", GROUP="dialout"

SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", \
  ATTRS{serial}=="0001", SYMLINK+="robot/lidar", MODE="0666", GROUP="dialout"
```

Reload: `sudo udevadm control --reload-rules && sudo udevadm trigger`.

### Health Check Script (ExecStartPre)

Block driver startup until devices exist.

```bash
#!/bin/bash
# /usr/local/bin/robot-device-check.sh
set -euo pipefail
REQUIRED_DEVICES=("/dev/robot/camera_front" "/dev/robot/lidar" "/dev/robot/imu")
TIMEOUT=30
for device in "${REQUIRED_DEVICES[@]}"; do
  elapsed=0
  while [ ! -e "$device" ]; do
    [ "$elapsed" -ge "$TIMEOUT" ] && { echo "Missing $device"; exit 1; }
    sleep 1; elapsed=$((elapsed+1))
  done
done
exit 0
```

### DDS Peers for Multi-Machine

In CycloneDDS XML, list peers explicitly when multicast is unavailable.

```xml
<CycloneDDS>
  <Domain>
    <Discovery>
      <Peers>
        <Peer address="10.0.0.10"/>
        <Peer address="10.0.0.20"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

## Anti-Patterns

### Sourcing setup.bash only in .bashrc

systemd does not load `.bashrc`. Service will not see ROS2. Use `EnvironmentFile` and source in `ExecStart`: `source /opt/ros/${ROS_DISTRO}/setup.bash && ...`.

### No startup ordering

All nodes start in parallel; navigation may call a service not yet advertised. Use `After=` and `Requires=` between systemd units (drivers → perception → application).

### Restart=always without rate limiting

Broken service restarts in a tight loop. Use `Restart=on-failure`, `RestartSec=5`, `StartLimitIntervalSec=120`, `StartLimitBurst=5`.

### Using network.target instead of network-online.target

`network.target` does not guarantee connectivity. Use `After=network-online.target` and `Wants=network-online.target`.

### No log rotation

Logs and journal fill the disk. Configure logrotate for `$ROS_LOG_DIR` and set journald `SystemMaxUse=1G` in `/etc/systemd/journald.conf`.

### Hardcoded device paths (/dev/ttyUSB0)

Enumeration order changes on reboot. Use udev rules and stable symlinks (e.g. `/dev/robot/imu`) in node parameters.

### Running the stack as root

Security and permission issues. Create a `robot` user, set `User=robot` and `Group=robot`, and grant device access via udev `GROUP` and `MODE`.

### No graceful shutdown

On stop, actuators keep last commanded velocity. In nodes that command motors, register shutdown handlers to command zero velocity and engage brakes before exit.

## Configuration Reference

| Parameter / setting | Type | Default | Description |
|---------------------|------|---------|-------------|
| ROS_DISTRO | env | - | humble, iron, jazzy |
| RMW_IMPLEMENTATION | env | rmw_fastrps_cpp | rmw_cyclonedds_cpp recommended |
| ROS_DOMAIN_ID | env | 0 | 0–101 for isolation |
| CYCLONEDDS_URI | env | - | Path to CycloneDDS XML |
| WatchdogSec | systemd | - | Interval for sd_notify(WATCHDOG=1) |
| RestartSec | systemd | 5 | Delay before restart |
| StartLimitBurst | systemd | 5 | Max restarts in StartLimitIntervalSec |
| StartLimitIntervalSec | systemd | 120 | Window for rate limit |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| "command not found" for ros2 | Environment not loaded in systemd | Use EnvironmentFile and source in ExecStart |
| Nodes start then crash repeatedly | Missing device or config | Add ExecStartPre health check; check journal with `journalctl -u robot-bringup -f` |
| Topics not visible on another machine | DDS discovery | Set ROS_DOMAIN_ID same on both; use CycloneDDS peer list |
| /dev/ttyUSB0 wrong device after reboot | Enumeration order | Add udev rules and use stable symlinks in params |
| Service never reaches "active" | Dependency not ready | Use network-online.target; add After= for driver service |
| Disk full after days | Unbounded logs | Configure logrotate and journald SystemMaxUse |
| Robot keeps moving on shutdown | No safe state on SIGINT | Implement shutdown handler (zero velocity, brakes) in actuator nodes |

## Workflow Integration

- After hardware is wired and udev rules are in place, use this skill to define systemd and launch layers; see [guides/hardware-integration.md](../../guides/hardware-integration.md) for wiring to first topic.
- Use [guides/robot-bringup.md](../../guides/robot-bringup.md) for the first power-on and verification steps.
- For navigation and perception config, use `nav2` and `sensor-fusion-slam` skills; for security and hardening before deployment use `safety-systems`.
