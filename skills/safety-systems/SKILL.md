---
name: safety-systems
description: Robot safety and security with functional safety (ISO 10218), SROS2, DDS security, E-stops, watchdogs, and risk assessment.
category: architecture
tags: [safety, security, sros2, functional-safety, iso10218, estop, watchdog, risk-assessment]
version: "1.0.0"
---

# Safety Systems

Safety and security for robotic systems. This skill covers functional safety standards, SROS2, E-stops, and risk assessment.

## Security: robot attack surface

Cyber vulnerabilities on robots become physical risks (unauthorized motion, sensor spoofing). Key vectors:

| Vector | Impact |
|--------|--------|
| Unauthenticated `/cmd_vel` | Robot moves unexpectedly — injury or damage |
| Sensor spoofing (`/scan`, `/camera/image`) | Wrong decisions, collisions |
| Open DDS discovery | Full topic graph visible to anyone on the network |
| USB/serial physical access | Root shell, firmware flash |
| Unsigned firmware OTA | Persistent backdoor in motor controllers |

SROS2 adds DDS authentication, encryption, and access control. Use it for production and multi-tenant networks.

## When to Use

- Designing emergency stop systems
- Implementing safety-rated monitored stops
- Configuring SROS2 and DDS security
- Performing risk assessments per ISO 10218
- Implementing safety controllers
- Securing robot communication
- Adding watchdogs and safety monitors

## Quick Start

```bash
# Install SROS2
sudo apt install ros-humble-sros2

# Generate security artifacts
ros2 security create_keystore ~/sros2_keystore
ros2 security create_enclave ~/sros2_keystore /robot/navigation
```

Create one enclave per fully-qualified node name. Set `ROS_SECURITY_KEYSTORE` and `ROS_SECURITY_STRATEGY=Enforce` when launching nodes. Use governance XML to require encryption and authentication; use permissions XML to allow only specific topics/services per enclave.

## Core Concepts

### 1. Emergency Stop Systems

Hardware and software E-stop implementation.

```cpp
// Safety controller with E-stop
class SafetyController {
public:
    enum class SafetyState {
        NORMAL,      // Normal operation
        PROTECTIVE,  // Protective stop (recoverable)
        EMERGENCY    // Emergency stop (requires reset)
    };
    
    SafetyController() : state_(SafetyState::NORMAL) {
        // Configure GPIO for E-stop input
        gpio_export(E_STOP_PIN);
        gpio_set_direction(E_STOP_PIN, "in");
        gpio_set_edge(E_STOP_PIN, "falling");
        
        // Safety-rated output
        gpio_export(SAFETY_OUT_PIN);
        gpio_set_direction(SAFETY_OUT_PIN, "out");
        gpio_set_value(SAFETY_OUT_PIN, 1);  // Enable motion
    }
    
    void update() {
        // Read E-stop (dual channel for safety rating)
        bool estop_ch1 = gpio_get_value(E_STOP_PIN_1);
        bool estop_ch2 = gpio_get_value(E_STOP_PIN_2);
        
        // Both channels must agree
        if (estop_ch1 == 0 && estop_ch2 == 0) {
            trigger_emergency_stop("E-stop pressed");
        } else if (estop_ch1 != estop_ch2) {
            // Fault - channels disagree
            trigger_emergency_stop("E-stop fault");
        }
        
        // Check other safety inputs
        check_joint_limits();
        check_collision_detected();
        check_safety_zone_violation();
        
        // Update safety output
        if (state_ == SafetyState::NORMAL) {
            gpio_set_value(SAFETY_OUT_PIN, 1);
        } else {
            gpio_set_value(SAFETY_OUT_PIN, 0);
            stop_all_motion();
        }
    }
    
    void trigger_emergency_stop(const std::string& reason) {
        if (state_ != SafetyState::EMERGENCY) {
            state_ = SafetyState::EMERGENCY;
            RCLCPP_ERROR(logger_, "EMERGENCY STOP: %s", reason.c_str());
            
            // Immediate hardware stop
            halt_all_actuators();
            
            // Software stop
            publish_safety_state();
        }
    }
    
    bool reset_emergency_stop() {
        // Require manual reset with verification
        if (gpio_get_value(RESET_PIN) == 0) {
            // Check all safety conditions cleared
            if (is_safe_to_reset()) {
                state_ = SafetyState::NORMAL;
                return true;
            }
        }
        return false;
    }

private:
    SafetyState state_;
    rclcpp::Logger logger_ = rclcpp::get_logger("SafetyController");
};
```

### 2. SROS2 Security

Secure ROS2 communication.

```bash
# Create security keystore
ros2 security create_keystore ~/sros2_keystore

# Create keys for nodes
ros2 security create_key ~/sros2_keystore /robot/vision
ros2 security create_key ~/sros2_keystore /robot/navigation
ros2 security create_key ~/sros2_keystore /robot/manipulation

# List keys
ros2 security list_keys ~/sros2_keystore

# Launch with security
ROS_SECURITY_KEYSTORE=~/sros2_keystore \
ROS_SECURITY_ENABLE=true \
ROS_SECURITY_STRATEGY=Enforce \
ros2 launch robot_bringup secure_launch.py
```

```xml
<!-- secure_launch.xml -->
<launch>
  <env name="ROS_SECURITY_KEYSTORE" value="$(env HOME)/sros2_keystore"/>
  <env name="ROS_SECURITY_ENABLE" value="true"/>
  
  <node pkg="vision" exec="camera_node" 
        security="enable"
        enclave="/robot/vision"/>
  
  <node pkg="nav2" exec="navigation_node"
        security="enable"
        enclave="/robot/navigation"/>
</launch>
```

### 3. Watchdogs

Hardware and software watchdogs prevent runaway conditions.

```cpp
#include <linux/watchdog.h>

class WatchdogManager {
public:
    WatchdogManager() {
        // Open hardware watchdog
        fd_ = open("/dev/watchdog", O_RDWR);
        if (fd_ < 0) {
            throw std::runtime_error("Failed to open watchdog");
        }
        
        // Set timeout (seconds)
        int timeout = 5;
        ioctl(fd_, WDIOC_SETTIMEOUT, &timeout);
        
        // Start watchdog thread
        running_ = true;
        watchdog_thread_ = std::thread(&WatchdogManager::watchdog_loop, this);
    }
    
    void pet_watchdog() {
        std::lock_guard<std::mutex> lock(mutex_);
        last_pet_time_ = std::chrono::steady_clock::now();
    }
    
    void register_monitor(const std::string& name, 
                         std::function<bool()> health_check) {
        monitors_[name] = health_check;
    }

private:
    void watchdog_loop() {
        while (running_) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            
            // Check all monitors
            bool all_healthy = true;
            for (const auto& [name, check] : monitors_) {
                if (!check()) {
                    RCLCPP_ERROR(logger_, "Health check failed: %s", name.c_str());
                    all_healthy = false;
                }
            }
            
            // Check timeout
            auto elapsed = std::chrono::steady_clock::now() - last_pet_time_;
            if (elapsed > std::chrono::seconds(3)) {
                RCLCPP_ERROR(logger_, "Watchdog timeout - system will reset");
                // Don't pet - let watchdog trigger
                return;
            }
            
            if (all_healthy) {
                // Pet hardware watchdog
                ioctl(fd_, WDIOC_KEEPALIVE, 0);
            }
        }
    }
    
    int fd_;
    std::atomic<bool> running_;
    std::thread watchdog_thread_;
    std::mutex mutex_;
    std::chrono::steady_clock::time_point last_pet_time_;
    std::map<std::string, std::function<bool()>> monitors_;
    rclcpp::Logger logger_ = rclcpp::get_logger("Watchdog");
};
```

### 4. Risk Assessment

ISO 10218 compliant risk assessment.

```python
class RiskAssessment:
    def __init__(self):
        self.hazards = []
        self.risk_matrix = {
            'severity': {'negligible': 1, 'minor': 2, 'major': 3, 'critical': 4},
            'probability': {'unlikely': 1, 'possible': 2, 'likely': 3, 'frequent': 4}
        }
    
    def identify_hazards(self, robot_system):
        """Identify hazards per ISO 10218."""
        hazards = [
            {
                'id': 'H001',
                'description': 'Unexpected robot motion',
                'source': 'Control system fault',
                'severity': 'critical',
                'probability': 'unlikely',
                'mitigations': ['E-stop', 'Safety limits', 'Redundant sensors']
            },
            {
                'id': 'H002',
                'description': 'Collision with operator',
                'source': 'Presence in workspace',
                'severity': 'major',
                'probability': 'possible',
                'mitigations': ['Safety scanner', 'Light curtain', 'Reduced speed']
            },
            # ... more hazards
        ]
        return hazards
    
    def calculate_risk_level(self, severity, probability):
        """Calculate risk level from severity and probability."""
        s = self.risk_matrix['severity'][severity]
        p = self.risk_matrix['probability'][probability]
        risk = s * p
        
        if risk <= 4:
            return 'low'
        elif risk <= 8:
            return 'medium'
        elif risk <= 12:
            return 'high'
        else:
            return 'unacceptable'
    
    def generate_report(self):
        """Generate risk assessment report."""
        report = {
            'standards': ['ISO 10218-1', 'ISO 10218-2', 'ISO/TS 15066'],
            'hazards': self.hazards,
            'residual_risks': [],
            'mitigation_status': {}
        }
        
        for hazard in self.hazards:
            risk = self.calculate_risk_level(
                hazard['severity'], 
                hazard['probability']
            )
            hazard['risk_level'] = risk
            
            if risk in ['high', 'unacceptable']:
                report['residual_risks'].append(hazard)
        
        return report
```

## Configuration Reference

| Safety Level | Stop Category | Performance Level | Use Case |
|--------------|---------------|-------------------|----------|
| Emergency | 0 (uncontrolled) | PL e | Life-threatening |
| Protective | 1 (controlled) | PL d | Collision risk |
| Operational | 2 (soft) | PL c | Normal limits |

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| False E-stops | EMI on E-stop line | Shield cables, use filtered inputs |
| Watchdog reset | Task taking too long | Increase timeout, optimize code |
| SROS2 fails | Certificate expired | Regenerate keys, check permissions |

## Changelog

### v1.0.0 (2026-03-07)
- Initial release covering E-stops, SROS2, watchdogs, risk assessment