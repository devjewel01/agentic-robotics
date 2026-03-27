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

---

## Extended Core Concepts

### Layer Caching Strategy

Docker builds cache each layer. The goal is to put slow, rarely-changing steps early and fast, frequently-changing steps late. For ROS2 workspaces:

1. **System packages** — `apt-get install` (changes only when you add a new dep)
2. **rosdep dependencies** — copy only `package.xml` files, run `rosdep install` (changes only when a package.xml changes)
3. **Source build** — copy `src/`, run `colcon build` (rebuilds on any source change)
4. **Runtime copy** — `COPY --from=build /ros2_ws/install /ros2_ws/install`

When you copy `src/` before step 2, any edit to any source file invalidates the `rosdep` layer and re-downloads all apt packages — a 5–20 minute penalty per CI run.

```dockerfile
ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base AS deps

# Install build tools first — rarely changes
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

# Copy ONLY package.xml files — preserves cache when .cpp/.py files change
COPY src/orbibot_hardware/package.xml        src/orbibot_hardware/package.xml
COPY src/orbibot_sensors/package.xml         src/orbibot_sensors/package.xml
COPY src/orbibot_navigation/package.xml      src/orbibot_navigation/package.xml
COPY src/orbibot_msgs/package.xml            src/orbibot_msgs/package.xml

# rosdep layer — only rebuilds when package.xml files change
RUN rosdep update && \
    . /opt/ros/${ROS_DISTRO}/setup.sh && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*

# Now copy source — only this layer rebuilds on source changes
FROM deps AS build
COPY src/ src/
RUN . /opt/ros/${ROS_DISTRO}/setup.sh && \
    colcon build \
      --cmake-args -DCMAKE_BUILD_TYPE=Release \
      --event-handlers console_direct+ \
      --parallel-workers 4
```

**Tip:** Use a `find`-based COPY helper script or `.dockerignore` to auto-copy only `package.xml` files if your project grows beyond a handful of packages:

```bash
# scripts/copy_package_xmls.sh — run before docker build to stage package.xml files
find src -name "package.xml" | while read f; do
  mkdir -p "docker_context/$(dirname $f)"
  cp "$f" "docker_context/$f"
done
```

### Non-Root User Setup

Running ROS2 nodes as root inside a container is unnecessary and increases risk. Create a dedicated user in the runtime stage only (not in the build stage, which often needs root for apt).

```dockerfile
FROM ros:${ROS_DISTRO}-ros-core AS runtime
ARG ROS_DISTRO=jazzy
ARG UID=1000
ARG GID=1000

# Install minimal runtime deps as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    python3-yaml \
    && rm -rf /var/lib/apt/lists/*

# Create group and user matching the host UID/GID (avoids bind-mount permission issues)
RUN groupadd -g ${GID} rosuser && \
    useradd -u ${UID} -g ${GID} -m -s /bin/bash rosuser && \
    mkdir -p /ros2_ws && \
    chown -R rosuser:rosuser /ros2_ws

# Copy workspace install from build stage
COPY --from=build --chown=rosuser:rosuser /ros2_ws/install /ros2_ws/install

# Copy entrypoint as root, then switch user
COPY ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh

USER rosuser
WORKDIR /ros2_ws

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["ros2", "launch", "my_pkg", "bringup.launch.py"]
```

Build with matching host UID to avoid bind-mount ownership issues:

```bash
docker build \
  --build-arg UID=$(id -u) \
  --build-arg GID=$(id -g) \
  --build-arg ROS_DISTRO=jazzy \
  -t my_robot:latest .
```

### DDS Network Modes in Docker

Docker offers three relevant network modes for ROS2. Choose based on isolation vs. discovery needs.

| Mode | Multicast | Isolation | When to Use |
|------|-----------|-----------|-------------|
| `host` | Works natively | None — shares host network | Single robot, dev containers, simplest setup |
| `bridge` (default) | Blocked | Containers isolated | Multi-container on one host; requires peer list |
| Custom overlay | Configurable | Swarm-wide | Multi-host Docker Swarm; advanced |

**Host mode** — simplest, no DDS config needed:
```yaml
services:
  driver:
    network_mode: host
    environment:
      ROS_DOMAIN_ID: "42"
```

**Bridge mode with CycloneDDS peer list** — containers discover each other by service name:
```xml
<!-- config/cyclonedds_bridge.xml -->
<CycloneDDS xmlns="https://cdds.io/config">
  <Domain>
    <General>
      <AllowMulticast>false</AllowMulticast>
      <MaxMessageSize>65500B</MaxMessageSize>
    </General>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <Peers>
        <Peer address="driver"/>
        <Peer address="perception"/>
        <Peer address="navigation"/>
        <Peer address="webgui"/>
      </Peers>
    </Discovery>
    <Internal>
      <Watermarks>
        <WhcHigh>500kB</WhcHigh>
      </Watermarks>
    </Internal>
  </Domain>
</CycloneDDS>
```

**FastDDS with XML peer list** (alternative to CycloneDDS):
```xml
<!-- config/fastdds_bridge.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<dds xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles">
  <profiles>
    <participant profile_name="bridge_profile" is_default_profile="true">
      <rtps>
        <builtin>
          <metatrafficUnicastLocatorList>
            <locator/>
          </metatrafficUnicastLocatorList>
          <initialPeersList>
            <locator>
              <udpv4><address>driver</address></udpv4>
            </locator>
            <locator>
              <udpv4><address>perception</address></udpv4>
            </locator>
          </initialPeersList>
        </builtin>
      </rtps>
    </participant>
  </profiles>
</dds>
```

Set in environment:
```yaml
environment:
  RMW_IMPLEMENTATION: rmw_fastrtps_cpp
  FASTRTPS_DEFAULT_PROFILES_FILE: /config/fastdds_bridge.xml
```

---

## Extended Common Patterns

### Dev Container with Volume Mounts

A dev container builds once but recompiles inside the container, with your source tree mounted as a bind mount. This gives instant file-sync without rebuilding the image on every change.

```dockerfile
# Dockerfile.dev — dev image only; not for production
ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base AS dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    vim \
    gdb \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*

# Pre-install deps so bind-mount workspace builds quickly
WORKDIR /ros2_ws
COPY src/*/package.xml /tmp/pkg_xmls/
# Use a helper to restore directory structure for rosdep
RUN mkdir -p src && find /tmp/pkg_xmls -name "package.xml" -exec bash -c \
    'pkg=$(basename $(dirname $1)); mkdir -p src/$pkg; cp $1 src/$pkg/' _ {} \; && \
    rosdep update && \
    . /opt/ros/${ROS_DISTRO}/setup.sh && \
    rosdep install --from-paths src --ignore-src -r -y && \
    rm -rf /var/lib/apt/lists/*

# Entrypoint sources ROS and workspace if installed
COPY ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh
ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
```

```yaml
# docker-compose.dev.yaml
services:
  dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    image: my_robot:dev
    network_mode: host
    environment:
      ROS_DOMAIN_ID: "0"
      RMW_IMPLEMENTATION: rmw_cyclonedds_cpp
    volumes:
      # Bind-mount source — edits reflect instantly without rebuild
      - ./src:/ros2_ws/src:rw
      # Persist colcon build cache across container restarts
      - colcon_build:/ros2_ws/build
      - colcon_install:/ros2_ws/install
      - colcon_log:/ros2_ws/log
      # Host X11 for RViz (Linux)
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      # Device access
      - /dev/motordriver:/dev/motordriver
    devices:
      - /dev/motordriver:/dev/motordriver
    privileged: false
    environment:
      DISPLAY: "${DISPLAY}"
    group_add:
      - dialout

volumes:
  colcon_build:
  colcon_install:
  colcon_log:
```

Usage:
```bash
# Start dev container
docker compose -f docker-compose.dev.yaml up -d dev

# Build inside container
docker compose -f docker-compose.dev.yaml exec dev bash -c \
  "source /opt/ros/jazzy/setup.bash && colcon build --symlink-install"

# Run launch file inside container
docker compose -f docker-compose.dev.yaml exec dev bash -c \
  "source /opt/ros/jazzy/setup.bash && \
   source /ros2_ws/install/setup.bash && \
   ros2 launch orbibot_bringup robot.launch.py"
```

### CI/CD Pipeline with colcon build and test

A complete GitHub Actions workflow using Docker layer caching via the GitHub Actions cache backend.

```yaml
# .github/workflows/ros2_ci.yml
name: ROS2 CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-test:
    runs-on: ubuntu-24.04

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Build deps stage — cached by layer hash of package.xml files
      - name: Build deps stage
        uses: docker/build-push-action@v5
        with:
          context: .
          target: deps
          push: false
          load: true
          tags: ${{ env.IMAGE_NAME }}:deps
          cache-from: type=gha,scope=deps
          cache-to: type=gha,mode=max,scope=deps

      # Build full image
      - name: Build workspace
        uses: docker/build-push-action@v5
        with:
          context: .
          target: build
          push: false
          load: true
          tags: ${{ env.IMAGE_NAME }}:ci
          cache-from: |
            type=gha,scope=deps
            type=gha,scope=build
          cache-to: type=gha,mode=max,scope=build

      # Run colcon test inside the built image
      - name: Run tests
        run: |
          docker run --rm \
            -e ROS_DOMAIN_ID=99 \
            -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
            ${{ env.IMAGE_NAME }}:ci \
            bash -c "
              source /opt/ros/jazzy/setup.bash && \
              source /ros2_ws/install/setup.bash && \
              colcon test \
                --packages-select orbibot_hardware orbibot_msgs \
                --event-handlers console_direct+ && \
              colcon test-result --all --verbose
            "

      # Push runtime image on merge to main
      - name: Build and push runtime image
        if: github.ref == 'refs/heads/main'
        uses: docker/build-push-action@v5
        with:
          context: .
          target: runtime
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha,scope=build
```

### Multi-Arch Builds (AMD64 + ARM64 for Raspberry Pi)

OrbiBot's RPi 5 runs ARM64. Build and push a multi-arch manifest so the same tag works on both the development laptop (AMD64) and the robot.

```yaml
# .github/workflows/multiarch.yml
name: Multi-Arch Build

on:
  push:
    tags: ['v*']

jobs:
  build-multiarch:
    runs-on: ubuntu-24.04

    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU (emulate ARM64 on AMD64 runner)
        uses: docker/setup-qemu-action@v3
        with:
          platforms: arm64

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push multi-arch image
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          target: runtime
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}
          # Separate cache scopes per platform to avoid cross-contamination
          cache-from: |
            type=gha,scope=amd64
            type=gha,scope=arm64
          cache-to: type=gha,mode=max,scope=${{ runner.arch == 'X64' && 'amd64' || 'arm64' }}
```

Local cross-compile test (slow — uses QEMU emulation):
```bash
# Build ARM64 image locally
docker buildx build \
  --platform linux/arm64 \
  --target runtime \
  -t my_robot:arm64-test \
  --load \
  .

# Verify architecture
docker run --rm my_robot:arm64-test uname -m  # Should print: aarch64
```

**ARM64-specific Dockerfile considerations:**

```dockerfile
ARG ROS_DISTRO=jazzy
# OSRF publishes multi-arch images — FROM automatically pulls the right arch
FROM ros:${ROS_DISTRO}-ros-base AS deps

# Some Python packages have no ARM64 wheel; install from apt when possible
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-numpy \
    python3-scipy \
    && rm -rf /var/lib/apt/lists/*
# Avoid: pip install numpy (compiles from source on ARM64, very slow in QEMU)
```

### docker-compose for Multi-Robot Simulation

Run multiple robot instances with isolated `ROS_DOMAIN_ID` values on a single host.

```yaml
# docker-compose.simulation.yaml
x-robot-base: &robot-base
  image: my_robot:latest
  volumes:
    - ./config/cyclonedds.xml:/cyclonedds.xml:ro
    - /dev/shm:/dev/shm

services:
  robot_1:
    <<: *robot-base
    container_name: robot_1
    environment:
      ROS_DOMAIN_ID: "1"
      ROBOT_NAME: "robot_1"
      RMW_IMPLEMENTATION: rmw_cyclonedds_cpp
      CYCLONEDDS_URI: file:///cyclonedds.xml
    networks:
      - sim_net
    command: ros2 launch my_pkg bringup.launch.py robot_name:=robot_1

  robot_2:
    <<: *robot-base
    container_name: robot_2
    environment:
      ROS_DOMAIN_ID: "2"
      ROBOT_NAME: "robot_2"
      RMW_IMPLEMENTATION: rmw_cyclonedds_cpp
      CYCLONEDDS_URI: file:///cyclonedds.xml
    networks:
      - sim_net
    command: ros2 launch my_pkg bringup.launch.py robot_name:=robot_2

  # Fleet coordinator — subscribes to all robots via DDS domain bridge or a REST proxy
  coordinator:
    image: my_robot_coordinator:latest
    environment:
      ROBOT_1_URL: "http://robot_1:8080"
      ROBOT_2_URL: "http://robot_2:8080"
    networks:
      - sim_net
    depends_on:
      - robot_1
      - robot_2

networks:
  sim_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### GPU Passthrough for Gazebo / Perception

NVIDIA GPU passthrough requires the NVIDIA Container Toolkit on the host.

```bash
# Install NVIDIA Container Toolkit (host, one-time)
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

```yaml
# docker-compose with GPU
services:
  gazebo:
    image: my_robot_sim:latest
    environment:
      DISPLAY: "${DISPLAY}"
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_DRIVER_CAPABILITIES: graphics,compute,utility
      ROS_DOMAIN_ID: "0"
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - /dev/shm:/dev/shm
    network_mode: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: ros2 launch my_pkg gazebo_sim.launch.py
```

For Intel integrated GPU (no NVIDIA toolkit needed):
```yaml
services:
  rviz:
    image: my_robot:desktop
    devices:
      - /dev/dri:/dev/dri
    environment:
      DISPLAY: "${DISPLAY}"
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
```

---

## Extended Anti-Patterns

### Running as root in the container

❌ **Wrong** — default root user in runtime image:
```dockerfile
FROM ros:jazzy-ros-core
COPY --from=build /ros2_ws/install /ros2_ws/install
CMD ["ros2", "launch", "my_pkg", "bringup.launch.py"]
# Container runs as root — any exploit gets full root access
```

✅ **Correct** — create and switch to a non-root user:
```dockerfile
FROM ros:jazzy-ros-core
RUN groupadd -r rosuser && useradd -r -g rosuser -m rosuser && \
    mkdir -p /ros2_ws && chown rosuser:rosuser /ros2_ws
COPY --from=build --chown=rosuser:rosuser /ros2_ws/install /ros2_ws/install
USER rosuser
CMD ["ros2", "launch", "my_pkg", "bringup.launch.py"]
```

### Not pinning the ROS2 distro tag

❌ **Wrong** — unpinned base image breaks builds when OSRF releases a new patch:
```dockerfile
FROM ros:latest         # Could be any distro
FROM ros:humble         # Rolling tag; minor updates may break your deps
```

✅ **Correct** — pin to a specific digest or at minimum a distro + release date tag:
```dockerfile
ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base
# For maximum reproducibility, pin to a digest:
# FROM ros:jazzy-ros-base@sha256:abc123...
```

Automate digest updates with Dependabot or Renovate rather than manually tracking them.

### DDS discovery issues in Docker bridge network

❌ **Wrong** — relying on multicast with bridge networking and no peer config:
```yaml
services:
  driver:
    image: my_robot:latest
    # No network_mode: host, no CYCLONEDDS_URI — topics invisible to other containers
  perception:
    image: my_robot_perc:latest
```

✅ **Correct** — explicit peer list via CycloneDDS config mounted into every container:
```yaml
x-dds: &dds
  environment:
    RMW_IMPLEMENTATION: rmw_cyclonedds_cpp
    CYCLONEDDS_URI: file:///cyclonedds.xml
  volumes:
    - ./config/cyclonedds_bridge.xml:/cyclonedds.xml:ro

services:
  driver:
    <<: *dds
    image: my_robot:latest
  perception:
    <<: *dds
    image: my_robot_perc:latest
```

### No cache busting when apt sources go stale

❌ **Wrong** — no cache busting means `apt-get update` is skipped on cache hit, leading to stale package lists and `404 Not Found` errors for packages:
```dockerfile
RUN apt-get install -y python3-colcon-common-extensions
```

✅ **Correct** — always pair `apt-get update` and `apt-get install` in a single `RUN` layer, and use `--no-install-recommends` to keep image small:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*
```

For CI where freshness matters, use `--no-cache` on the build command:
```bash
docker build --no-cache --target deps -t my_robot:deps .
```

### Using `colcon build` without `--symlink-install` in dev containers

❌ **Wrong** — full rebuild required after every Python script change when using bind mounts:
```bash
colcon build  # Copies files into install/; bind-mount source changes ignored
```

✅ **Correct** — use `--symlink-install` in dev containers so Python changes are reflected immediately:
```bash
colcon build --symlink-install
# Python files in install/ are now symlinks to src/; no rebuild needed for .py changes
# C++ still requires rebuild (compiled code cannot be symlinked)
```

---

## Extended Configuration Reference

### Docker Build Arguments

| Build Arg | Default | Description |
|-----------|---------|-------------|
| `ROS_DISTRO` | `humble` | ROS2 distro (`humble`, `iron`, `jazzy`) — must match base image tag |
| `UID` | `1000` | User ID for non-root user — match host UID to avoid bind-mount permission issues |
| `GID` | `1000` | Group ID for non-root user |
| `CMAKE_BUILD_TYPE` | `Release` | `Release`, `Debug`, `RelWithDebInfo` — use `Debug` for dev images |
| `COLCON_PARALLEL_WORKERS` | CPU count | Limit for constrained CI runners (e.g. `--parallel-workers 2`) |

### docker-compose Service Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `network_mode: host` | Share host network namespace — DDS multicast works, no peer config needed | `network_mode: host` |
| `shm_size` | Shared memory for image/pointcloud DDS transport | `shm_size: "512m"` |
| `devices` | Pass host device into container | `- /dev/ttyUSB0:/dev/ttyUSB0` |
| `group_add` | Add container user to host group | `- dialout` (serial), `- video` (camera) |
| `privileged` | Full host device access — avoid unless necessary | `privileged: false` |
| `deploy.resources.reservations.devices` | NVIDIA GPU passthrough (requires NVIDIA Container Toolkit) | `driver: nvidia, count: 1, capabilities: [gpu]` |
| `restart` | Auto-restart policy for production | `restart: unless-stopped` |
| `healthcheck` | Container health probe | `test: ["CMD", "ros2", "topic", "list"]` |
| `depends_on` | Start order and health dependency | `depends_on: driver: condition: service_healthy` |

### CycloneDDS XML Parameters

| Parameter | Description | Recommended Value |
|-----------|-------------|-------------------|
| `AllowMulticast` | Enable/disable multicast discovery | `false` for bridge networks |
| `Peers/Peer address` | Explicit peer by service name or IP | Service name in compose |
| `WhcHigh` | High-water mark for write history cache | `500kB`–`2MB` for image topics |
| `MaxMessageSize` | UDP fragment size | `65500B` (default) |
| `ParticipantIndex` | DDS participant index | `auto` |

### GitHub Actions Cache Configuration

| Option | Description |
|--------|-------------|
| `cache-from: type=gha,scope=deps` | Read from GitHub Actions cache for the `deps` stage |
| `cache-to: type=gha,mode=max,scope=build` | Write all layers to cache (max mode caches intermediate layers) |
| Separate scopes per stage | Prevents a `build` cache miss from also busting the `deps` cache |
| Separate scopes per arch | `scope=amd64` vs `scope=arm64` for multi-arch builds |

---

## Extended Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| `ros2 topic list` empty inside container | DDS discovery failed across bridge network | Add CycloneDDS peer list with service names; or switch to `network_mode: host` |
| Topics visible in one direction only | Asymmetric peer list | Add peers in both directions; check `ROS_DOMAIN_ID` matches in all containers |
| GPU not accessible (`CUDA error: no kernel image`) | NVIDIA Container Toolkit not installed or container not requesting GPU | `sudo apt install nvidia-container-toolkit && sudo systemctl restart docker`; add `deploy.resources.reservations.devices` with `capabilities: [gpu]` |
| ARM64 cross-compile extremely slow in CI | QEMU software emulation for ARM64 | Use `runs-on: ubuntu-24.04-arm64` self-hosted runner, or AWS Graviton runner for native ARM64 builds |
| `colcon test` passes locally but fails in CI | Non-deterministic timing, missing env vars, or resource starvation | Set `ROS_DOMAIN_ID` to an unused value (e.g. 99) in CI; add `--timeout 120`; allocate ≥2 CPU and ≥4 GB RAM to the runner |
| `rosdep install` fails with `404` | Stale apt cache in cached layer | Use `--no-cache` for the `deps` stage in CI; or add `--build-arg CACHE_BUST=$(date +%Y%m%d)` weekly |
| Image bind mount shows wrong UID (permission denied) | Host UID ≠ container user UID | Build with `--build-arg UID=$(id -u) --build-arg GID=$(id -g)` to create a matching user |
| Container exits immediately after launch | Entrypoint not sourcing setup.bash, or CMD not found | Verify entrypoint script has `set -e` and sources both `/opt/ros/.../setup.bash` and `/ros2_ws/install/setup.bash`; check CMD path |
| Large images (>4 GB) in CI | Desktop image used, or build artifacts not cleaned | Use `ros-base` or `ros-core` for runtime; run `colcon build --cmake-clean-cache` and delete `build/` before copying to runtime stage |
| `/dev/shm` too small for point cloud topics | Default 64 MB shm insufficient | Add `shm_size: "512m"` to compose service and enable `<SharedMemory><Enable>true</Enable>` in CycloneDDS XML |
