# Guide: Hardware Integration

End-to-end workflow for integrating robot hardware from wiring to first ROS2 topic.

## Goal

Get robot hardware communicating with ROS2: sensors publishing data, actuators responding to commands, and the full stack validated.

## Prerequisites

- **Skills needed:** `ros2`, `ros2-control`, `robot-modeling`, `serial-can-protocols`, `microcontrollers`, `realtime-motor-control`
- **Hardware:** Robot platform, sensors, actuators, wiring, power supply
- **Software:** Ubuntu 22.04, ROS2 Humble, development tools

## Estimated Time

4-8 hours for a simple differential drive robot with encoders and LiDAR.

---

## Step 1: Hardware Inventory and Planning

Before touching wires, document your hardware.

### 1.1 Create Hardware Manifest

```yaml
# robot_hardware.yaml
robot:
  name: "my_robot"
  type: "differential_drive"
  
  compute:
    main: "Jetson Orin Nano"
    mcus:
      - name: "left_motor"
        type: "STM32F407"
        interfaces: ["CAN", "UART"]
      - name: "right_motor"
        type: "STM32F407"
        interfaces: ["CAN", "UART"]
  
  sensors:
    - name: "lidar"
      type: "RPLIDAR A1"
      interface: "USB"
      rate: 10  # Hz
    - name: "imu"
      type: "MPU9250"
      interface: "I2C"
      rate: 100  # Hz
    - name: "encoders"
      type: "quadrature"
      resolution: 2000  # CPR
      gear_ratio: 10
  
  actuators:
    - name: "left_wheel"
      type: "BLDC"
      driver: "ODrive"
      max_current: 50  # A
      max_velocity: 10  # rad/s
    - name: "right_wheel"
      type: "BLDC"
      driver: "ODrive"
      max_current: 50  # A
      max_velocity: 10  # rad/s
  
  power:
    battery:
      type: "LiPo"
      voltage: 14.8  # 4S
      capacity: 5000  # mAh
    regulators:
      - output: 12V
        current: 10  # A
        for: ["Jetson", "motors"]
      - output: 5V
        current: 5  # A
        for: ["sensors", "MCUs"]
```

### 1.2 Wiring Diagram

Create a connection diagram showing:

- Power distribution (battery → regulators → components)
- Communication buses (CAN, I2C, UART, USB)
- Signal grounds (single-point ground reference)
- Emergency stops and safety circuits

> **Safety Note:** Include fuses on all power rails. Size fuses at 125% of expected load.

---

## Step 2: Power System Setup

### 2.1 Power Budget

Calculate total power consumption:

| Component | Voltage | Current | Power |
|-----------|---------|---------|-------|
| Jetson Orin Nano | 12V | 3A | 36W |
| 2x Motors (max) | 12V | 20A | 240W |
| LiDAR | 5V | 1A | 5W |
| IMU + MCUs | 5V | 0.5A | 2.5W |
| **Total** | - | - | **283W** |
| **With 20% margin** | - | - | **340W** |

Battery runtime: 5000mAh / (283W / 14.8V) ≈ 15 minutes at full load

### 2.2 Power-Up Sequence

```bash
# Step-by-step power verification
1. Disconnect all loads from battery
2. Verify battery voltage (should be ~16.8V charged)
3. Connect 12V regulator, verify output (12.0V ± 5%)
4. Connect 5V regulator, verify output (5.0V ± 5%)
5. Connect Jetson, verify boots
6. Connect MCUs one at a time
7. Finally connect motors (with current limit set low)
```

> **Anti-Pattern:** Don't connect everything at once. A short in one component can damage everything.

---

## Step 3: Microcontroller Firmware

> **Skill reference:** See `skills/microcontrollers/SKILL.md` -> "Core Concepts"

### 3.1 Basic Firmware Template

```c
// Core system initialization
void SystemInit(void) {
    HAL_Init();
    SystemClock_Config();  // 168 MHz
    GPIO_Init();
    UART_Init(115200);
    CAN_Init(500000);
    TIM2_Init();  // 1 kHz control loop
    Encoder_Init();
    ADC_Init();   // Current sensing
    
    printf("Robot MCU v1.0 starting...\n");
}

// Main control loop (1 kHz)
void TIM2_IRQHandler(void) {
    if (__HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE)) {
        __HAL_TIM_CLEAR_IT(&htim2, TIM_IT_UPDATE);
        
        // Read sensors
        int32_t encoder = Encoder_Read();
        float current = ADC_ReadCurrent();
        
        // Run control
        float pwm = Control_Update(encoder, current);
        
        // Output
        PWM_Set(pwm);
        
        // Safety checks
        if (current > MAX_CURRENT) {
            Fault_Set(OVERCURRENT);
        }
    }
}
```

### 3.2 Communication Protocol

Implement a simple binary protocol:

```c
// Protocol frame: [START][LEN][CMD][DATA...][CRC]
#define FRAME_START 0xAA

typedef enum {
    CMD_HEARTBEAT = 0x01,
    CMD_GET_STATUS = 0x02,
    CMD_SET_VELOCITY = 0x10,
    CMD_GET_ENCODER = 0x11,
    CMD_GET_CURRENT = 0x12,
    CMD_SET_PWM = 0x20,
    CMD_FAULT_CLEAR = 0x30
} CommandType;

void Protocol_Process(uint8_t byte) {
    static ProtocolState state = STATE_WAIT_START;
    static uint8_t buffer[32];
    static uint8_t idx = 0;
    
    switch (state) {
        case STATE_WAIT_START:
            if (byte == FRAME_START) state = STATE_LEN;
            break;
        case STATE_LEN:
            if (byte <= 32) {
                buffer[0] = byte;
                idx = 1;
                state = STATE_DATA;
            } else {
                state = STATE_WAIT_START;
            }
            break;
        case STATE_DATA:
            buffer[idx++] = byte;
            if (idx >= buffer[0] + 2) {  // +2 for CRC
                if (VerifyCRC(buffer, idx - 2)) {
                    ExecuteCommand(buffer[1], &buffer[2], buffer[0] - 1);
                }
                state = STATE_WAIT_START;
            }
            break;
    }
}
```

### 3.3 Flash and Verify

```bash
# Build firmware
make clean && make

# Flash via ST-Link
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
  -c "program build/firmware.elf verify reset exit"

# Or via UART bootloader
stm32flash -w build/firmware.bin -v -g 0x0 /dev/ttyUSB0

# Verify with serial console
screen /dev/ttyUSB0 115200
# Should see: "Robot MCU v1.0 starting..."
```

---

## Step 4: Sensor Integration

### 4.1 I2C Sensor (IMU Example)

> **Skill reference:** See `skills/gpio-i2c-spi/SKILL.md`

```python
#!/usr/bin/env python3
import smbus2
import time

MPU9250_ADDR = 0x68

class MPU9250:
    def __init__(self, bus=1):
        self.bus = smbus2.SMBus(bus)
        self.init()
    
    def init(self):
        # Wake up
        self.bus.write_byte_data(MPU9250_ADDR, 0x6B, 0x00)
        time.sleep(0.1)
        # Set gyro range to ±250 deg/s
        self.bus.write_byte_data(MPU9250_ADDR, 0x1B, 0x00)
        # Set accel range to ±2g
        self.bus.write_byte_data(MPU9250_ADDR, 0x1C, 0x00)
    
    def read_accel(self):
        data = self.bus.read_i2c_block_data(MPU9250_ADDR, 0x3B, 6)
        x = (data[0] << 8) | data[1]
        y = (data[2] << 8) | data[3]
        z = (data[4] << 8) | data[5]
        # Convert to g (±2g range, 16-bit)
        return x / 16384.0, y / 16384.0, z / 16384.0
    
    def read_gyro(self):
        data = self.bus.read_i2c_block_data(MPU9250_ADDR, 0x43, 6)
        x = (data[0] << 8) | data[1]
        y = (data[2] << 8) | data[3]
        z = (data[4] << 8) | data[5]
        # Convert to deg/s (±250 deg/s range)
        return x / 131.0, y / 131.0, z / 131.0

# Test
imu = MPU9250()
while True:
    ax, ay, az = imu.read_accel()
    print(f"Accel: {ax:.2f}, {ay:.2f}, {az:.2f} g")
    time.sleep(0.1)
```

### 4.2 Verify Sensor Data

```bash
# Check I2C bus detection
i2cdetect -y 1
# Should show device at 0x68

# Test with ROS2 driver
ros2 run mpu9250_driver mpu9250_node --ros-args -p bus:=1

# Verify topic publishing
ros2 topic hz /imu/data_raw
# Should show ~100 Hz
```

---

## Step 5: Actuator Integration

> **Skill reference:** See `skills/realtime-motor-control/SKILL.md` -> "Core Concepts"

### 5.1 Motor Controller Setup

```python
#!/usr/bin/env python3
import serial
import struct

class MotorController:
    def __init__(self, port='/dev/ttyACM0', baud=115200):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.ser.reset_input_buffer()
    
    def send_command(self, cmd, data=b''):
        frame = bytes([0xAA, len(data) + 1, cmd]) + data
        crc = sum(frame) & 0xFF
        frame += bytes([crc])
        self.ser.write(frame)
    
    def set_velocity(self, vel_rad_s):
        # Send velocity in milli-rad/s
        vel_mrad = int(vel_rad_s * 1000)
        data = struct.pack('<h', vel_mrad)  # int16
        self.send_command(0x10, data)
    
    def get_encoder(self):
        self.send_command(0x11)
        resp = self.ser.read(6)  # [START][LEN][CMD][DATA][DATA][CRC]
        if len(resp) == 6 and resp[0] == 0xAA:
            return struct.unpack('<i', resp[3:7])[0]  # int32
        return None
    
    def get_status(self):
        self.send_command(0x02)
        resp = self.ser.read(8)
        if len(resp) == 8:
            return {
                'state': resp[3],
                'fault': resp[4],
                'voltage': resp[5] / 10.0,
                'current': struct.unpack('<h', resp[6:8])[0] / 100.0
            }
        return None

# Test motion
motor = MotorController()

# Check status
print(motor.get_status())

# Small velocity test
motor.set_velocity(1.0)  # 1 rad/s
time.sleep(1.0)
motor.set_velocity(0.0)

# Verify encoder changed
print(f"Encoder: {motor.get_encoder()}")
```

### 5.2 Characterize Motor Response

```python
import matplotlib.pyplot as plt

# Step response test
velocities = []
times = []
target = 5.0  # rad/s

motor.set_velocity(target)
start = time.time()

for _ in range(100):
    v = motor.get_velocity()
    velocities.append(v)
    times.append(time.time() - start)
    time.sleep(0.01)

motor.set_velocity(0)

plt.plot(times, velocities)
plt.axhline(y=target, color='r', linestyle='--', label='Target')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (rad/s)')
plt.legend()
plt.savefig('step_response.png')

# Measure rise time (10% to 90%)
v10 = target * 0.1
v90 = target * 0.9
t10 = next(t for t, v in zip(times, velocities) if v >= v10)
t90 = next(t for t, v in zip(times, velocities) if v >= v90)
print(f"Rise time: {t90 - t10:.3f} s")
```

---

## Step 6: ROS2 Control Integration

> **Skill reference:** See `skills/ros2-control/SKILL.md` -> "Hardware Interface"

### 6.1 Hardware Interface Package

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake robot_hardware --dependencies hardware_interface pluginlib rclcpp
```

```cpp
// include/robot_hardware/robot_hardware.hpp
#ifndef ROBOT_HARDWARE__ROBOT_HARDWARE_HPP_
#define ROBOT_HARDWARE__ROBOT_HARDWARE_HPP_

#include "hardware_interface/system_interface.hpp"
#include "rclcpp/rclcpp.hpp"

namespace robot_hardware {
class RobotHardware : public hardware_interface::SystemInterface {
public:
    hardware_interface::CallbackReturn on_init(
        const hardware_interface::HardwareInfo& info) override;
    
    hardware_interface::CallbackReturn on_configure(
        const rclcpp_lifecycle::State& previous_state) override;
    
    std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
    std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;
    
    hardware_interface::return_type read(
        const rclcpp::Time& time, const rclcpp::Duration& period) override;
    
    hardware_interface::return_type write(
        const rclcpp::Time& time, const rclcpp::Duration& period) override;

private:
    // Motor controllers
    std::unique_ptr<MotorController> left_motor_;
    std::unique_ptr<MotorController> right_motor_;
    
    // State
    double left_pos_, left_vel_, left_eff_;
    double right_pos_, right_vel_, right_eff_;
    
    // Commands
    double left_cmd_, right_cmd_;
};

}  // namespace robot_hardware

#endif
```

```cpp
// src/robot_hardware.cpp
#include "robot_hardware/robot_hardware.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

namespace robot_hardware {

hardware_interface::CallbackReturn RobotHardware::on_init(
    const hardware_interface::HardwareInfo& info) {
    
    if (hardware_interface::SystemInterface::on_init(info) !=
        hardware_interface::CallbackReturn::SUCCESS) {
        return hardware_interface::CallbackReturn::ERROR;
    }
    
    // Initialize state variables
    left_pos_ = left_vel_ = left_eff_ = 0.0;
    right_pos_ = right_vel_ = right_eff_ = 0.0;
    left_cmd_ = right_cmd_ = 0.0;
    
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RobotHardware::on_configure(
    const rclcpp_lifecycle::State& previous_state) {
    
    RCLCPP_INFO(rclcpp::get_logger("RobotHardware"), "Configuring...");
    
    // Get parameters from URDF
    std::string left_port = info_.hardware_parameters["left_port"];
    std::string right_port = info_.hardware_parameters["right_port"];
    
    try {
        left_motor_ = std::make_unique<MotorController>(left_port);
        right_motor_ = std::make_unique<MotorController>(right_port);
    } catch (const std::exception& e) {
        RCLCPP_ERROR(rclcpp::get_logger("RobotHardware"), 
                    "Failed to connect: %s", e.what());
        return hardware_interface::CallbackReturn::ERROR;
    }
    
    return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> 
RobotHardware::export_state_interfaces() {
    std::vector<hardware_interface::StateInterface> state_interfaces;
    
    state_interfaces.emplace_back("left_wheel_joint", 
        hardware_interface::HW_IF_POSITION, &left_pos_);
    state_interfaces.emplace_back("left_wheel_joint", 
        hardware_interface::HW_IF_VELOCITY, &left_vel_);
    
    state_interfaces.emplace_back("right_wheel_joint", 
        hardware_interface::HW_IF_POSITION, &right_pos_);
    state_interfaces.emplace_back("right_wheel_joint", 
        hardware_interface::HW_IF_VELOCITY, &right_vel_);
    
    return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> 
RobotHardware::export_command_interfaces() {
    std::vector<hardware_interface::CommandInterface> command_interfaces;
    
    command_interfaces.emplace_back("left_wheel_joint", 
        hardware_interface::HW_IF_VELOCITY, &left_cmd_);
    command_interfaces.emplace_back("right_wheel_joint", 
        hardware_interface::HW_IF_VELOCITY, &right_cmd_);
    
    return command_interfaces;
}

hardware_interface::return_type RobotHardware::read(
    const rclcpp::Time& time, const rclcpp::Duration& period) {
    
    // Read encoders and convert to SI units
    int32_t left_enc = left_motor_->get_encoder();
    int32_t right_enc = right_motor_->get_encoder();
    
    // Convert encoder counts to radians
    // CPR = 2000, gear_ratio = 10
    const double cpr = 2000.0 * 10.0 * 4.0;  // Quad encoder
    left_pos_ = 2.0 * M_PI * left_enc / cpr;
    right_pos_ = 2.0 * M_PI * right_enc / cpr;
    
    // Calculate velocity
    static double prev_left = 0, prev_right = 0;
    double dt = period.seconds();
    left_vel_ = (left_pos_ - prev_left) / dt;
    right_vel_ = (right_pos_ - prev_right) / dt;
    prev_left = left_pos_;
    prev_right = right_pos_;
    
    return hardware_interface::return_type::OK;
}

hardware_interface::return_type RobotHardware::write(
    const rclcpp::Time& time, const rclcpp::Duration& period) {
    
    // Send velocity commands to motors
    left_motor_->set_velocity(left_cmd_);
    right_motor_->set_velocity(right_cmd_);
    
    return hardware_interface::return_type::OK;
}

}  // namespace robot_hardware

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(robot_hardware::RobotHardware, 
                      hardware_interface::SystemInterface)
```

### 6.2 Launch and Test

```python
# launch/robot.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    return LaunchDescription([
        # Robot state publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            arguments=['/path/to/robot.urdf']
        ),
        
        # ros2_control node
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[{
                'robot_description': 'path/to/robot.urdf',
                'controllers': ['diff_drive_controller', 'joint_state_broadcaster']
            }]
        ),
        
        # Diff drive controller
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['diff_drive_controller', '--controller-manager', '/controller_manager']
        ),
        
        # Joint state broadcaster
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager']
        ),
    ])
```

```bash
# Build and run
cd ~/ros2_ws
colcon build --packages-select robot_hardware
source install/setup.bash

# Launch
ros2 launch robot_hardware robot.launch.py

# Test with teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Monitor
ros2 topic echo /joint_states
ros2 topic echo /odom
```

---

## Validation Checklist

- [ ] Power system: All voltages correct under load
- [ ] MCU firmware: Boots, responds to commands
- [ ] Sensors: Publishing data at expected rate
- [ ] Motors: Respond to velocity commands smoothly
- [ ] Encoders: Reading correctly, no missed counts
- [ ] ros2_control: Hardware interface loads without errors
- [ ] Teleop: Robot responds to keyboard commands
- [ ] Safety: Emergency stop works, current limits enforced

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Motors don't move | No enable signal, wrong command format | Check wiring, verify protocol |
| Jerky motion | Control loop rate too low, noise | Increase rate, add filtering |
| Position drift | Encoder slip, missed counts | Check coupling, verify CPR |
| ros2_control fails | URDF mismatch, port permissions | Check joint names, add user to dialout |
| High latency | USB vs UART, buffering | Use direct UART, disable buffering |
| Thermal shutdown | Current limits too high | Reduce limits, add cooling |

## Next Steps

- **Calibration:** Run `guides/sensor-calibration.md` for IMU and wheel odometry
- **Navigation:** Proceed to `skills/nav2/SKILL.md` for autonomous navigation
- **Simulation:** Use `skills/gazebo/SKILL.md` to test algorithms safely

## References

- **Hardware Design:** `skills/serial-can-protocols/SKILL.md`
- **Motor Control:** `skills/realtime-motor-control/SKILL.md`
- **ROS2 Control:** `skills/ros2-control/SKILL.md`
- **Robot Modeling:** `skills/robot-modeling/SKILL.md`