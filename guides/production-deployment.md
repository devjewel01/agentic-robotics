# Guide: Production Deployment

This guide walks through taking a robot from development to production: pre-deployment validation, staged rollout, monitoring setup, and rollback procedures.

## Goal

Take a ROS 2 robot that works in development and deploy it reliably to a production or field environment — with proper validation, automated deployment, health monitoring, and a clear rollback plan.

## Prerequisites

- **Skills needed:** `robot_bringup`, `docker_ros2_development`, `ros2_diagnostics`, `safety_systems`
- **Hardware:** Target robot with SSH access, matching a staging robot for pre-deploy testing
- **Software:** Docker, Ansible (or SSH access), a container registry (GHCR, Docker Hub, or self-hosted), Grafana + Loki (optional but recommended)
- **Assumed:** Robot nodes start via systemd using a `ros2 launch` command wrapped in a service unit

## Estimated Time

3-6 hours for first production deployment (experienced: 1-2 hours for subsequent deploys)

---

## Step 1: Pre-Deployment Validation Checklist

Before touching production, every deployment must pass a local or staging gate. This step defines the gate.

### 1.1 Safety Gate

**Objective:** Verify that safety-critical systems are functioning and configured correctly.

```bash
# Verify emergency stop hardware is wired and responsive
ros2 service call /orbibot/set_motor_enable orbibot_msgs/srv/SetMotorEnable '{enable: false}'
# Expected: motors disengage within 50ms

# Confirm watchdog is active (firmware sends heartbeat every 100ms)
ros2 topic echo /orbibot/system_status --once | grep watchdog_ok
# Expected: watchdog_ok: true

# Check safety velocity limits in config
grep -E "max_vel|cmd_timeout" src/orbibot_hardware/config/hardware_params.yaml
# Expected: max_vel_x ≤ 1.0 m/s, cmd_timeout ≤ 0.5 s

# Test command timeout: send a velocity, then stop publishing
ros2 topic pub --once /cmd_vel geometry_msgs/Twist '{linear: {x: 0.3}}'
# Wait 600ms — robot must stop on its own
```

**Checkpoint:**
- [ ] E-stop physically tested and confirmed
- [ ] Watchdog heartbeat present
- [ ] Velocity limits within spec
- [ ] Command timeout causes motor stop

### 1.2 Sensor Gate

**Objective:** All sensors must publish at expected rates with no stale data.

```bash
# LiDAR
ros2 topic hz /scan --window 10
# Expected: ~10 Hz ± 1 Hz

# IMU
ros2 topic hz /imu/data_raw --window 20
# Expected: ~50 Hz ± 5 Hz

# EKF output
ros2 topic hz /odometry/filtered --window 10
# Expected: ~20 Hz ± 2 Hz

# Camera (if used)
ros2 topic hz /camera/color/image_raw --window 5
# Expected: ~15 Hz ± 2 Hz

# Check for stale timestamps (all should be < 1 second old)
ros2 topic echo /scan --once | grep stamp
ros2 topic echo /imu/data_raw --once | grep stamp
```

**Common failure: LiDAR shows 0 Hz** — check `/dev/lidar` symlink, udev rule, or driver crash.

**Checkpoint:**
- [ ] All sensors at expected rate
- [ ] No "Connection timeout" in driver logs
- [ ] Timestamps are current (not replayed bag data)

### 1.3 Communication Gate

**Objective:** Verify all ROS 2 topics, services, and the DDS network are healthy.

```bash
# List all expected topics — none should be missing
ros2 topic list | sort > /tmp/topic_list_actual.txt
diff /tmp/topic_list_expected.txt /tmp/topic_list_actual.txt
# Expected: no diff

# Verify TF tree is complete
ros2 run tf2_tools view_frames
# Check generated frames.pdf: map → odom → base_footprint → base_link → sensors

# Check no transform timeouts
ros2 run tf2_ros tf2_echo odom base_footprint
# Expected: continuous output with no "Lookup would require extrapolation" errors

# Verify AI agent HTTP endpoint (if deployed)
curl -s http://localhost:8082/api/providers | python3 -m json.tool
# Expected: JSON list with at least one provider
```

**Checkpoint:**
- [ ] All expected topics present
- [ ] TF tree connected end-to-end
- [ ] No TF extrapolation errors at runtime
- [ ] HTTP API responds (if applicable)

### 1.4 Resource Usage Gate

**Objective:** CPU, RAM, and temperature must be within production limits before deploying.

```bash
# Run full stack for 5 minutes, then sample
ros2 launch orbibot_bringup robot.launch.py &
sleep 300

# CPU usage (should be < 70% sustained on RPi 5)
ros2 topic echo /orbibot/system_status --once | grep cpu_percent
# Expected: cpu_percent < 70.0

# RAM usage (should be < 80% of total)
ros2 topic echo /orbibot/system_status --once | grep memory_percent
# Expected: memory_percent < 80.0

# CPU temperature (RPi 5 throttles at 85°C)
ros2 topic echo /orbibot/system_status --once | grep cpu_temp
# Expected: cpu_temp < 75.0

# Check for memory leaks: run longer and compare
ps aux --sort=-%mem | head -10
```

**Checkpoint:**
- [ ] CPU < 70% sustained
- [ ] RAM < 80% used
- [ ] Temperature < 75°C under load
- [ ] No growing memory usage over 5 minutes

---

## Step 2: Staging Environment Setup

Never deploy directly to a production robot. Use a staging robot (or a Docker-based staging node on a development machine) that mirrors production.

### 2.1 Mirror Production Configuration

```bash
# Clone production robot config to staging
rsync -av orbibot@production-robot:/home/orbibot/orbibot_ws/src/orbibot_hardware/config/ \
          orbibot@staging-robot:/home/orbibot/orbibot_ws/src/orbibot_hardware/config/

rsync -av orbibot@production-robot:/home/orbibot/maps/ \
          orbibot@staging-robot:/home/orbibot/maps/

# Verify versions match
ssh orbibot@staging-robot "cat /etc/orbibot_version"
ssh orbibot@production-robot "cat /etc/orbibot_version"
# Expected: same base OS and ROS 2 version
```

### 2.2 Staging Smoke Test

Run the full validation checklist (Step 1) on the staging robot before proceeding.

```bash
# SSH to staging robot and run automated check script
ssh orbibot@staging-robot "bash ~/orbibot_ws/scripts/pre_deploy_check.sh"
# Expected: "All checks PASSED" printed to stdout, exit code 0
```

A minimal `pre_deploy_check.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/jazzy/setup.bash
source ~/orbibot_ws/install/setup.bash

FAILURES=0

check() {
    local name="$1"; local cmd="$2"; local expect="$3"
    result=$(eval "$cmd" 2>&1) || true
    if echo "$result" | grep -q "$expect"; then
        echo "  PASS: $name"
    else
        echo "  FAIL: $name (got: $result)"
        FAILURES=$((FAILURES + 1))
    fi
}

check "scan topic"    "ros2 topic info /scan"           "sensor_msgs/msg/LaserScan"
check "odom topic"    "ros2 topic info /odom"           "nav_msgs/msg/Odometry"
check "filtered odom" "ros2 topic info /odometry/filtered" "nav_msgs/msg/Odometry"

[ $FAILURES -eq 0 ] && echo "All checks PASSED" || { echo "$FAILURES checks FAILED"; exit 1; }
```

---

## Step 3: Docker Image Build and Push Pipeline

### 3.1 Build the Production Image

```dockerfile
# Dockerfile.production
FROM ros:jazzy-ros-base AS builder

WORKDIR /orbibot_ws
COPY src/ src/

RUN . /opt/ros/jazzy/setup.sh && \
    apt-get update && \
    rosdep install --from-paths src --ignore-src -r -y && \
    colcon build \
      --cmake-args -DCMAKE_BUILD_TYPE=Release \
      --packages-skip orbibot_rosmaster_firmware && \
    rm -rf build/ log/

# Runtime stage — smaller image
FROM ros:jazzy-ros-base AS runtime

COPY --from=builder /orbibot_ws/install /orbibot_ws/install
COPY --from=builder /orbibot_ws/src/orbibot_bringup/config /orbibot_ws/config

RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc && \
    echo "source /orbibot_ws/install/setup.bash" >> ~/.bashrc

ENTRYPOINT ["/bin/bash", "-lc", \
  "source /opt/ros/jazzy/setup.bash && \
   source /orbibot_ws/install/setup.bash && \
   ros2 launch orbibot_bringup robot.launch.py"]
```

```bash
# Build and tag with git SHA for traceability
GIT_SHA=$(git rev-parse --short HEAD)
docker build \
  -f Dockerfile.production \
  -t ghcr.io/your-org/orbibot:${GIT_SHA} \
  -t ghcr.io/your-org/orbibot:latest \
  .

# Push to registry
docker push ghcr.io/your-org/orbibot:${GIT_SHA}
docker push ghcr.io/your-org/orbibot:latest
```

### 3.2 Verify the Image

```bash
# Run locally to confirm the image starts without errors
docker run --rm \
  --network host \
  --device /dev/motordriver \
  --device /dev/lidar \
  ghcr.io/your-org/orbibot:${GIT_SHA}

# Expected: no Python tracebacks, topics visible within 5 seconds
# In another terminal:
docker exec $(docker ps -q) ros2 topic list
```

---

## Step 4: Ansible Deployment to Robot Fleet

### 4.1 Inventory File

```ini
# inventory/robots.ini
[production]
orbibot-01 ansible_host=192.168.1.10 ansible_user=orbibot
orbibot-02 ansible_host=192.168.1.11 ansible_user=orbibot

[staging]
orbibot-staging ansible_host=192.168.1.20 ansible_user=orbibot

[all:vars]
ansible_ssh_private_key_file=~/.ssh/orbibot_deploy
registry=ghcr.io/your-org/orbibot
```

### 4.2 Deployment Playbook

```yaml
# deploy.yml
---
- name: Deploy OrbiBot to robot fleet
  hosts: "{{ target_group | default('staging') }}"
  become: false
  vars:
    image_tag: "{{ git_sha | default('latest') }}"
    orbibot_home: /home/orbibot

  tasks:
    - name: Pull new Docker image
      community.docker.docker_image:
        name: "{{ registry }}:{{ image_tag }}"
        source: pull
        force_source: true

    - name: Stop existing orbibot service
      ansible.builtin.systemd:
        name: orbibot
        state: stopped
      ignore_errors: true

    - name: Record rollback point
      ansible.builtin.copy:
        content: "{{ previous_tag | default('latest') }}"
        dest: "{{ orbibot_home }}/.rollback_tag"
        mode: '0644'

    - name: Update image tag in systemd override
      ansible.builtin.template:
        src: templates/orbibot.service.j2
        dest: /etc/systemd/system/orbibot.service
      become: true
      notify: Reload systemd

    - name: Start orbibot service
      ansible.builtin.systemd:
        name: orbibot
        state: started
        enabled: true
      become: true

    - name: Wait for robot nodes to initialize
      ansible.builtin.wait_for:
        timeout: 30

    - name: Run post-deploy health check
      ansible.builtin.command: "bash {{ orbibot_home }}/orbibot_ws/scripts/pre_deploy_check.sh"
      register: health_result
      failed_when: health_result.rc != 0

    - name: Report deployment result
      ansible.builtin.debug:
        msg: "Deployed {{ image_tag }} to {{ inventory_hostname }} — OK"

  handlers:
    - name: Reload systemd
      ansible.builtin.systemd:
        daemon_reload: true
      become: true
```

### 4.3 Systemd Service Template

```ini
# templates/orbibot.service.j2
[Unit]
Description=OrbiBot ROS 2 Stack
After=network.target docker.service
Requires=docker.service

[Service]
User=orbibot
Restart=on-failure
RestartSec=10
ExecStartPre=-/usr/bin/docker rm -f orbibot_runtime
ExecStart=/usr/bin/docker run --rm \
  --name orbibot_runtime \
  --network host \
  --device /dev/motordriver \
  --device /dev/lidar \
  -e ANTHROPIC_API_KEY={{ anthropic_api_key | default('') }} \
  {{ registry }}:{{ image_tag }}
ExecStop=/usr/bin/docker stop orbibot_runtime

[Install]
WantedBy=multi-user.target
```

### 4.4 Run the Deployment

```bash
# Deploy to staging first
ansible-playbook deploy.yml \
  -i inventory/robots.ini \
  -e target_group=staging \
  -e git_sha=${GIT_SHA}

# If staging passes, deploy to production
ansible-playbook deploy.yml \
  -i inventory/robots.ini \
  -e target_group=production \
  -e git_sha=${GIT_SHA} \
  -e previous_tag=$(ssh orbibot@orbibot-01 cat ~/.rollback_tag)
```

---

## Step 5: Health Check Verification Post-Deploy

### 5.1 Automated Post-Deploy Checks

```bash
# From deployment machine — run against each robot after deploy
for robot in orbibot-01 orbibot-02; do
  echo "=== Checking $robot ==="
  ssh orbibot@${robot} "bash ~/orbibot_ws/scripts/pre_deploy_check.sh"
done
```

### 5.2 Manual Spot Checks

```bash
# SSH to one production robot and verify live topics
ssh orbibot@orbibot-01

# Verify all expected topics are live
ros2 topic list | wc -l
# Expected: at least 15 topics for full bringup

ros2 topic hz /scan --window 5
# Expected: ~10 Hz

ros2 topic hz /odometry/filtered --window 5
# Expected: ~20 Hz

# Verify no ERROR or FATAL in recent logs (last 2 minutes)
journalctl -u orbibot --since "2 minutes ago" | grep -E "ERROR|FATAL"
# Expected: empty output
```

**Checkpoint:**
- [ ] All topics publishing at expected rates
- [ ] No ERROR/FATAL in systemd journal
- [ ] Health check script exits 0 on all robots
- [ ] TF tree complete on production robot

---

## Step 6: Setting Up Grafana and Log Monitoring

### 6.1 Log Forwarding with Promtail

Install Promtail on the robot to ship systemd logs to a central Loki instance:

```yaml
# /etc/promtail/promtail-config.yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://grafana-server:3100/loki/api/v1/push

scrape_configs:
  - job_name: orbibot_systemd
    journal:
      max_age: 12h
      labels:
        job: orbibot
        host: __HOSTNAME__
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: unit
      - source_labels: ['__journal_priority_keyword']
        target_label: level
```

```bash
# Start Promtail
sudo systemctl enable promtail
sudo systemctl start promtail
```

### 6.2 Metrics with a ROS 2 Diagnostics Exporter

Export `/diagnostics` to Prometheus using a bridge node:

```bash
# On robot: publish system status metrics
ros2 topic echo /orbibot/system_status_enriched --once
# This topic has cpu_percent, memory_percent, cpu_temp — export these

# Simple Prometheus push (add to robot startup)
# See skills/ros2_diagnostics for full diagnostics_to_prometheus bridge
```

### 6.3 Grafana Dashboard Setup

```bash
# On monitoring server — start Grafana + Loki + Prometheus
cat > docker-compose.monitoring.yml << 'EOF'
version: '3.8'
services:
  loki:
    image: grafana/loki:2.9.0
    ports: ["3100:3100"]

  grafana:
    image: grafana/grafana:10.2.0
    ports: ["3000:3000"]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: your_password
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
EOF

docker compose -f docker-compose.monitoring.yml up -d
```

**Key dashboards to create in Grafana:**

1. **Robot Health** — CPU%, RAM%, temperature per robot, over time
2. **ROS 2 Topic Rates** — `/scan`, `/odom`, `/odometry/filtered` Hz
3. **Error Log Stream** — Loki log panel filtered to `level=error`
4. **Deploy History** — Annotate graph with each deployment timestamp

```bash
# Add a Grafana annotation at deploy time (from CI/CD or Ansible)
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  http://grafana-server:3000/api/annotations \
  -d "{\"text\": \"Deploy ${GIT_SHA}\", \"tags\": [\"deployment\"]}"
```

---

## Step 7: Rollback Procedure

### 7.1 When to Roll Back

Roll back immediately if any of the following occur within 15 minutes of a deploy:

- Health check script fails on any production robot
- `ERROR` or `FATAL` in logs that were not present before deploy
- Any sensor stops publishing (topic Hz drops to 0)
- Robot fails to respond to manual drive commands
- CPU temperature rises above 80°C under normal operation

### 7.2 Rollback Execution

```bash
# Read the saved rollback tag from the robot
ROLLBACK_TAG=$(ssh orbibot@orbibot-01 cat ~/.rollback_tag)
echo "Rolling back to: ${ROLLBACK_TAG}"

# Re-run deployment playbook with previous tag
ansible-playbook deploy.yml \
  -i inventory/robots.ini \
  -e target_group=production \
  -e git_sha=${ROLLBACK_TAG}
```

**Manual rollback (single robot, no Ansible):**

```bash
ssh orbibot@orbibot-01

# Stop current service
sudo systemctl stop orbibot

# Read rollback tag
ROLLBACK_TAG=$(cat ~/.rollback_tag)

# Update service to use rollback image
sudo sed -i "s|orbibot:.*|orbibot:${ROLLBACK_TAG}|" /etc/systemd/system/orbibot.service
sudo systemctl daemon-reload
sudo systemctl start orbibot

# Verify
journalctl -u orbibot -f --since now
```

### 7.3 Post-Rollback Analysis

```bash
# Collect logs from the failed deployment window
journalctl -u orbibot \
  --since "$(date -d '30 minutes ago' --iso-8601=seconds)" \
  --until "$(date --iso-8601=seconds)" \
  > /tmp/failed_deploy_logs.txt

# Look for the first ERROR or exception
grep -n "ERROR\|Traceback\|Exception" /tmp/failed_deploy_logs.txt | head -20

# Compare topic lists between working and failed images
docker run --rm ghcr.io/your-org/orbibot:${ROLLBACK_TAG} \
  bash -lc "ros2 topic list" > /tmp/topics_good.txt

docker run --rm ghcr.io/your-org/orbibot:${GIT_SHA} \
  bash -lc "ros2 topic list" > /tmp/topics_bad.txt

diff /tmp/topics_good.txt /tmp/topics_bad.txt
```

---

## Step 8: Go-Live Checklist

Complete this checklist before declaring a deployment "in production."

### Pre-Deploy (done before running Ansible)
- [ ] All Step 1 validation gates passed on staging robot
- [ ] Docker image built from a tagged git commit (not `main` HEAD)
- [ ] Image pushed to registry with git SHA tag
- [ ] Rollback tag recorded from previous production state
- [ ] Monitoring (Grafana/Loki) is operational and showing pre-deploy baseline

### Deploy
- [ ] Deployed to staging first, health checks passed
- [ ] Deployed to one production robot, health checks passed
- [ ] If fleet: rolled out to remaining robots one at a time
- [ ] Grafana deploy annotation added

### Post-Deploy (first 15 minutes)
- [ ] All topic rates stable at expected Hz
- [ ] No ERROR/FATAL in logs
- [ ] CPU/RAM/temperature within normal range
- [ ] Manual robot control verified (teleop test drive)
- [ ] AI agent (if deployed) responds to a test query
- [ ] Grafana shows no anomalies in health dashboard

### Sign-Off
- [ ] Deployment recorded in a deployment log (date, SHA, deployer, robots)
- [ ] Previous image tag archived (not deleted — needed for rollback)
- [ ] On-call contact aware of the deployment window

---

## Validation Checklist

### Environment Parity
- [ ] Staging robot runs same OS version as production
- [ ] Same device symlinks (`/dev/motordriver`, `/dev/lidar`) exist on both
- [ ] Same map files deployed to both

### Deployment Pipeline
- [ ] `pre_deploy_check.sh` exits 0 on staging and production
- [ ] Docker image tagged with git SHA (not floating `latest`)
- [ ] Ansible playbook is idempotent (safe to re-run)
- [ ] Rollback procedure tested at least once end-to-end

### Observability
- [ ] Logs flowing to Loki from all robots
- [ ] Grafana health dashboard accessible
- [ ] Deploy annotations visible on timeline
- [ ] Alert rules configured for CPU > 80%, no scan for > 10s

---

## Common Issues

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Docker image fails to start | Missing device node in container | Add `--device /dev/motordriver` to `docker run` |
| `ros2 topic list` empty in container | DDS can't see host network | Use `--network host` in Docker |
| Ansible SSH fails | Key not in `authorized_keys` | `ssh-copy-id -i ~/.ssh/orbibot_deploy.pub orbibot@robot` |
| Health check times out | Nodes slow to start | Increase `wait_for timeout` in playbook |
| Rollback image not in registry | Old image was pruned | Keep at least 3 previous image tags in registry |
| Grafana shows no logs | Promtail not running | `systemctl status promtail` on robot |

---

## Next Steps

After successful production deployment:

1. **Automate the pipeline** — Add a GitHub Actions workflow that builds, pushes, and deploys on each merge to `main`
2. **Add alerting** — Configure Grafana alerts for critical metrics (no scan, high CPU, temperature)
3. **Expand fleet** — See `skills/deployment-fleet` for multi-robot orchestration at scale
4. **Harden security** — See `skills/robotics_security` for SROS2 and network segmentation
5. **Test recovery** — See `guides/testing-strategy.md` for hardware-in-the-loop and field testing

---

## Resources

- Related skills: `robot_bringup`, `docker_ros2_development`, `ros2_diagnostics`, `safety_systems`
- Related guides: `hardware-integration.md`, `testing-strategy.md`
- Ansible docs: https://docs.ansible.com/
- Grafana Loki: https://grafana.com/docs/loki/
