---
name: docker-ros2-ci
description: >
  Docker-based ROS2 development and CI: multi-stage Dockerfiles, docker-compose for robot stacks,
  DDS discovery across containers, GPU and USB passthrough, and CI builds/tests. Use when
  containerizing ROS2 workspaces, setting up CI with colcon build/test, or running multi-container
  robot systems.
category: devops
tags: [ros2, docker, docker-compose, ci, colcon, dds]
version: "1.0.0"
---

# Docker and CI for ROS2

This skill covers Docker-based ROS2 development and CI: image choice, multi-stage Dockerfiles, docker-compose for multi-container systems, DDS configuration in containers, and using the same images for local dev and CI (e.g. GitHub Actions).

## When to Use

- Writing Dockerfiles for ROS2 workspaces with colcon builds
- Setting up docker-compose for multi-container robot systems (drivers, perception, navigation)
- Debugging DDS discovery between containers (CycloneDDS, FastDDS)
- Configuring GPU passthrough for perception nodes
- Managing USB passthrough for cameras and serial devices
- Building CI/CD pipelines that run `colcon build` and `colcon test` in Docker
- Choosing the right OSRF base image and optimizing layer caching

## Quick Start

```bash
# Build workspace in Docker (from repo root with src/ and Dockerfile)
docker build --target build -t my_robot:build .
docker run --rm -v $(pwd)/src:/ros2_ws/src my_robot:build \
  bash -c "source /opt/ros/humble/setup.bash && colcon build"

# Run a launch file in a minimal runtime image
docker build --target runtime -t my_robot:latest .
docker run --rm --network host -e ROS_DOMAIN_ID=0 my_robot:latest
```

## Core Concepts

### ROS2 Docker Image Hierarchy

Use the smallest OSRF image that has what you need.

| Image | Size | Contents | Use case |
|-------|------|----------|----------|
| ros:humble-ros-core | ~700 MB | rclcpp, rclpy, launch | Minimal runtime |
| ros:humble-ros-base | ~1.1 GB | + common_interfaces, rosbag2 | Production |
| ros:humble-perception | ~2.2 GB | + image_transport, cv_bridge, PCL | Perception |
| ros:humble-desktop | ~2.8 GB | + rviz2, rqt | Development with GUI |

### Multi-Stage Builds

- **deps:** Copy only `package.xml` files, run `rosdep install` — maximizes cache when source changes.
- **build:** Copy `src/`, run `colcon build`.
- **runtime:** Copy only `install/` from build; no compilers or source. Use for production and CI test runs.

### DDS in Containers

- With **bridge networking**, multicast often does not work. Use CycloneDDS or FastDDS with **explicit peer lists** (service names in compose, or IPs).
- Share **/dev/shm** (or `shm_size`) for shared-memory transport when multiple containers need high-throughput topics.
- **network_mode: host** gives native multicast but less isolation.

## Common Patterns

### Multi-Stage Dockerfile

```dockerfile
ARG ROS_DISTRO=humble
FROM ros:${ROS_DISTRO}-ros-base AS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions python3-rosdep && rm -rf /var/lib/apt/lists/*
WORKDIR /ros2_ws
COPY src/my_pkg/package.xml src/my_pkg/package.xml
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    apt-get update && rosdep install --from-paths src --ignore-src -r -y && rm -rf /var/lib/apt/lists/*

FROM deps AS build
COPY src/ src/
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release --event-handlers console_direct+

FROM ros:${ROS_DISTRO}-ros-core AS runtime
ARG ROS_DISTRO
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-yaml ros-${ROS_DISTRO}-rmw-cyclonedds-cpp && rm -rf /var/lib/apt/lists/*
COPY --from=build /ros2_ws/install /ros2_ws/install
RUN groupadd -r rosuser && useradd -r -g rosuser -m rosuser
USER rosuser
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
COPY ros_entrypoint.sh /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["ros2", "launch", "my_pkg", "bringup.launch.py"]
```

### Entrypoint Script

```bash
#!/bin/bash
set -e
. /opt/ros/${ROS_DISTRO}/setup.bash
[ -f /ros2_ws/install/setup.bash ] && . /ros2_ws/install/setup.bash
exec "$@"
```

### docker-compose with Shared DDS Config

```yaml
x-ros-common: &ros-common
  environment:
    ROS_DOMAIN_ID: 0
    RMW_IMPLEMENTATION: rmw_cyclonedds_cpp
    CYCLONEDDS_URI: file:///cyclonedds.xml
  volumes:
    - ./config/cyclonedds.xml:/cyclonedds.xml:ro
    - /dev/shm:/dev/shm
  network_mode: host

services:
  driver:
    <<: *ros-common
    image: my_robot_driver:latest
    command: ros2 launch my_robot_driver driver.launch.py
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    group_add: [dialout]

  perception:
    <<: *ros-common
    image: my_robot_perception:latest
    command: ros2 launch my_robot_perception perception.launch.py
    deploy:
      resources:
        reservations:
          devices: [{ driver: nvidia, count: 1, capabilities: [gpu] }]
```

### CycloneDDS Peer List (for bridge networking)

When not using `network_mode: host`, list peers by service name or IP.

```xml
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain>
    <General><AllowMulticast>false</AllowMulticast></General>
    <Discovery>
      <Peers>
        <Peer address="driver"/>
        <Peer address="perception"/>
        <Peer address="navigation"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

### CI: Build and Test in Docker

Use the same Dockerfile; run tests in the build or a test stage.

```yaml
# .github/workflows/ci.yml (example)
- name: Build and test
  run: |
    docker build --target build -t my_robot:test .
    docker run --rm my_robot:test bash -c "\
      source /opt/ros/humble/setup.bash && \
      source /ros2_ws/install/setup.bash && \
      colcon test --event-handlers console_direct+ && \
      colcon test-result --all"
```

## Anti-Patterns

### Copying entire repo before rosdep

Copy only `package.xml` (or per-package `package.xml`) first, run `rosdep install`, then copy `src/`. Otherwise any source change invalidates the dependency layer and reinstalls packages.

### Using desktop image for production

Use `ros-base` or `ros-core` for runtime to reduce image size and attack surface.

### Forgetting /dev/shm for multi-container DDS

Large topics (images, point clouds) use shared memory when enabled. Give containers enough `shm_size` or mount `/dev/shm` and enable shared memory in CycloneDDS config.

### Running as root in container

Create a non-root user in the runtime stage and set `USER` so the process does not run as root.

### Relying on multicast in bridge network

With default bridge networking, DDS multicast often fails. Use explicit peer lists and set `AllowMulticast` to false in CycloneDDS.

## Configuration Reference

| Variable / option | Description |
|-------------------|-------------|
| ROS_DISTRO | humble, iron, jazzy — must match base image |
| RMW_IMPLEMENTATION | rmw_cyclonedds_cpp, rmw_fastrtps_cpp |
| CYCLONEDDS_URI | file:///path/to/cyclonedds.xml |
| ROS_DOMAIN_ID | Same across containers that should discover each other |
| network_mode: host | Use host network; DDS multicast works, less isolation |
| shm_size | Increase for image/point cloud topics (e.g. 512m) |

## Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| Containers do not see each other's topics | DDS discovery (multicast/peers) | Use peer list in CycloneDDS/FastDDS; or network_mode: host |
| "No space left on device" during build | Full disk or small /dev/shm | Increase disk/shm; clean images and build cache |
| colcon test fails in CI only | Timing, resources, or env | Run with --event-handlers console_direct+; ensure enough memory/CPU in runner |
| GPU not available in container | Missing NVIDIA Container Toolkit | Install nvidia-container-toolkit; use deploy.reservations.devices (gpu) in compose |
| USB device not visible | Permissions or not passed | Use devices: and group_add: dialout (or video) as needed |

## Workflow Integration

- Use `robot-bringup` for production startup on the robot (systemd, launch layers); use this skill for containerized builds and optional containerized deployment.
- For testing patterns (pytest, launch_testing) see `rules/robotics-testing.md` and `skills/ros2/SKILL.md`.
- For web interfaces to ROS2 see `ros2-web-bridge`.
