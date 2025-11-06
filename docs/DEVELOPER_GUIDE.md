# Pico-Go LAN Robot — Context File

**Repository**: StClairRoboticsClub/Pico-Go-LAN-Robot  
**Branch**: main  
**Last Updated**: 2025-11-06  
**Lead Engineer**: Jeremy Dueck  
**Organization**: St. Clair College Robotics Club

---

## 1. Project Snapshot

**What This Is**: A real-time LAN-controlled teleoperated robot platform built on Waveshare Pico-Go v2 with Raspberry Pi Pico W. Designed for robotics education, competitions (sumo/line-following), and R&D prototyping.

**Core Value Proposition**: Fully local Wi-Fi control (no internet required) with industrial-grade safety systems, sub-20ms latency, and automatic fail-safe motor cutoff.

**Current Status**: **85% Complete, Operational** ✅
- Robot drives reliably via Xbox controller at 30 Hz
- All safety systems functional (200ms watchdog timeout)
- TCP communication stable (10-15ms latency typical)
- LCD display fully operational with color-coded connection status
- Network infrastructure proven (Ubuntu hotspot + Pico W client)

**Critical Gap**: None—system is production-ready

**Primary Use Cases**:
1. **Education**: STEM labs, robotics clubs, microcontroller programming
2. **Competition**: Sumo robots, line-following, obstacle courses
3. **R&D**: Platform for sensor integration, autonomous navigation, ML experiments

---

## 2. Tech Stack & Services

### Firmware Layer (Raspberry Pi Pico W)
- **Runtime**: MicroPython 1.22+ on RP2040 (dual-core Cortex-M0+)
- **Wi-Fi**: CYW43439 (2.4 GHz, 802.11n)
- **Framework**: `uasyncio` for cooperative multitasking
- **Protocol**: TCP/JSON on port 8765 (not WebSocket—design improvement)
- **Libraries**: Built-in only (`machine`, `network`, `json`, `time`)
- **LCD Driver**: ST7789 (240×240 SPI display)

### Controller Layer (Ubuntu Laptop)
- **Runtime**: Python 3.11+
- **Input**: pygame 2.5+ (Xbox controller via SDL)
- **Networking**: asyncio + native sockets
- **Platform**: Ubuntu 22.04+ with NetworkManager

### Network Infrastructure
- **Topology**: Ubuntu hotspot → Pico W client (LAN-only, air-gapped)
- **SSID**: Configurable (default: `Pixel_6625`)
- **IP Scheme**: 10.42.0.x/24 (laptop: 10.42.0.1, robot: DHCP-assigned)
- **Security**: WPA2-PSK

### Hardware
- **MCU**: Raspberry Pi Pico W ($6)
- **Platform**: Waveshare Pico-Go v2 ($25)
- **Motor Driver**: TB6612FNG dual H-bridge (on-board)
- **Motors**: 2× TT gear motors (6V DC, 1:48 ratio)
- **Display**: ST7789 1.3" SPI LCD 240×240 (on-board)
- **Power**: 7.4V 2S Li-ion → 5V buck regulator
- **Controller**: Xbox controller (USB/Bluetooth)

---

## 3. Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROLLER (Ubuntu)                       │
│  ┌──────────────┐    ┌───────────────┐   ┌──────────────┐  │
│  │ Xbox Input   │───▶│ Python Client │──▶│ Wi-Fi (AP)   │  │
│  │ (pygame/SDL) │    │ 30 Hz @ 8765  │   │ 10.42.0.1    │  │
│  └──────────────┘    └───────────────┘   └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │ TCP/JSON
                              │ {cmd, throttle, steer, seq}
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     ROBOT (Pico W)                          │
│  ┌──────────────┐    ┌───────────────┐   ┌──────────────┐  │
│  │ Wi-Fi Client │───▶│ TCP Server    │──▶│ Motor Ctrl   │  │
│  │ 10.42.0.x    │    │ uasyncio      │   │ TB6612FNG    │  │
│  └──────────────┘    └───────────────┘   └──────────────┘  │
│                            │                      │          │
│                            ▼                      ▼          │
│                    ┌──────────────┐      ┌──────────────┐  │
│                    │ Watchdog     │      │ Motors (TT)  │  │
│                    │ 200ms safety │      │ PWM 1kHz     │  │
│                    └──────────────┘      └──────────────┘  │
│                            │                                │
│                            ▼                                │
│                    ┌──────────────┐                        │
│                    │ LCD Status   │                        │
│                    │ ST7789 SPI   │                        │
│                    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

**Control Flow**:
1. Xbox controller → pygame reads axes/buttons
2. Python client → formats JSON, sends TCP @ 30 Hz
3. Pico W TCP server → parses JSON, extracts throttle/steer
4. Motor controller → differential drive: `left = throttle + steer`, `right = throttle - steer`
5. PWM output → TB6612FNG → motors spin
6. Watchdog → monitors packet timing, auto-stops if >200ms timeout
7. LCD → displays state, connection quality (red/yellow/green), telemetry

**State Machine**:
```
BOOT → NET_UP → CLIENT_OK → DRIVING ←→ LINK_LOST
                                  ↓
                              E_STOP (latched)
```

---

## 4. Code Map (Curated File Tree)

```
Pico-Go-LAN-Robot/
├── init.md                        ← YOU ARE HERE (unified context)
├── README.md                       ← Public-facing quick start
├── LICENSE                         ← MIT License
├── .gitignore                      ← Python, MicroPython, IDE, logs
│
├── firmware/                       ← MicroPython code (Pico W)
│   ├── main.py                    ← Entry point, orchestrator
│   ├── config.py                  ← Pin defs, SSID, timeouts, constants
│   ├── wifi.py                    ← Wi-Fi connection manager (STA mode)
│   ├── motor.py                   ← Motor class, differential drive, PWM
│   ├── lcd_status.py              ← ST7789 driver, state display
│   ├── watchdog.py                ← Safety timer (200ms timeout)
│   ├── ws_server.py               ← TCP server (JSON packet handler)
│   ├── utils.py                   ← Clamping, debug_print helpers
│   ├── requirements.txt           ← MicroPython deps (mostly built-in)
│   └── (test_*.py, lcd_*.py)      ← Development artifacts
│
├── controller/                     ← Python controller app (laptop)
│   ├── controller_xbox.py         ← Main controller (pygame, asyncio)
│   └── requirements.txt           ← pygame>=2.5, asyncio-compat
│
├── scripts/                        ← Utility scripts
│   ├── setup_hotspot.sh           ← Ubuntu hotspot automation
│   ├── install_lcd_driver.sh      ← ST7789 driver installer
│   └── README.md                  ← Script documentation
│
├── docs/                           ← Documentation suite
│   ├── QUICKSTART.md              ← 5-minute setup guide
│   ├── HARDWARE.md                ← BOM, wiring, pin assignments
│   ├── NETWORKING.md              ← LAN setup, diagnostics, performance
│   ├── TROUBLESHOOTING.md         ← Problem-solving guide
│   └── LCD_GUIDE.md               ← Display states, color codes
│
├── schematics/                     ← Hardware diagrams
│   └── README.md                  ← Placeholder (diagrams TBD)
│
├── examples/                       ← Reference code from Waveshare
│   ├── PicoGo_Code_V2/            ← Original Waveshare examples
│   └── README.md                  ← Example code documentation
│
└── docs/deprecated/                ← Superseded files (historical)
    ├── README.md                  ← Explains consolidation
    ├── PROJECT_SUMMARY.md         ← Merged into init.md
    ├── QUICK_SUMMARY.md           ← Merged into init.md
    ├── ACTION_PLAN.md             ← Completed (LCD now working)
    ├── IMPLEMENTATION_STATUS.md   ← Obsolete (project operational)
    ├── oringinal_project_specs.md ← Historical (see EngineeringReference)
    ├── PicoGo-LAN-Robot_EngineeringReference_v2.md ← Verbose original spec
    └── LCD_WORKING.md             ← Superseded by LCD_GUIDE.md
```

**Key Modules Explained**:

- **`main.py`**: Initializes subsystems (Wi-Fi, LCD, motors, watchdog), starts TCP server, runs main loop. Handles graceful shutdown.
- **`config.py`**: Single source of truth for pins, network credentials, timing constants. Modify here to change SSID, PWM frequency, safety timeouts.
- **`motor.py`**: `Motor` class controls individual motor (PWM + direction pins). `DifferentialDrive` converts throttle/steer → left/right speeds.
- **`watchdog.py`**: Tracks last packet timestamp. If `time.ticks_ms() - last_packet > 200ms`, stops motors and sets `LINK_LOST` state.
- **`lcd_status.py`**: Manages ST7789 display via SPI. Shows boot screen, IP address, connection quality (red/yellow/green background), throttle/steer bars, RSSI, latency.
- **`ws_server.py`**: TCP server on port 8765. Accepts connections, parses JSON commands, calls motor controller, feeds watchdog, sends ACKs.
- **`controller_xbox.py`**: Reads Xbox controller via pygame, applies dead zone (0.08), sends JSON packets at 30 Hz, handles reconnection.

---

## 5. Configuration & Environments

### Environment Variables
None required—configuration is file-based.

### Key Config Files

#### `firmware/config.py` (Robot)
```python
# Network (CHANGE THESE)
WIFI_SSID = "Pixel_6625"        # Match your hotspot SSID
WIFI_PASSWORD = "Test123)("     # Match your hotspot password
WEBSOCKET_PORT = 8765           # TCP port for control

# Safety
WATCHDOG_TIMEOUT_MS = 200       # Fail-safe timeout
DEAD_ZONE = 0.08                # Joystick dead zone (±8%)

# Motor Pins (Waveshare Pico-Go v2)
PIN_MOTOR_A_PWM = 16            # Left motor PWM
PIN_MOTOR_A_IN1 = 18            # Left direction 1
PIN_MOTOR_A_IN2 = 17            # Left direction 2
PIN_MOTOR_B_PWM = 21            # Right motor PWM
PIN_MOTOR_B_IN1 = 19            # Right direction 1
PIN_MOTOR_B_IN2 = 20            # Right direction 2
PIN_MOTOR_STBY = None           # Not used on Waveshare

# LCD Pins
PIN_LCD_SCK = 18, PIN_LCD_MOSI = 19, PIN_LCD_DC = 16
PIN_LCD_RST = 20, PIN_LCD_CS = 17, PIN_LCD_BL = 21
```

#### `scripts/setup_hotspot.sh` (Laptop)
```bash
SSID="PicoLAN"                  # Hotspot name (match firmware config)
PASSWORD="pico1234"             # WPA2 password (match firmware)
INTERFACE="wlp112s0"            # Wi-Fi interface (check: ip link show)
BAND="bg"                       # 2.4 GHz (bg) or 5 GHz (a)
```

#### `controller/controller_xbox.py` (Laptop)
```python
DEFAULT_ROBOT_IP = "10.42.0.123"  # Update to match robot's actual IP
ROBOT_PORT = 8765
CONTROL_RATE_HZ = 30              # Packet transmission rate
DEAD_ZONE = 0.08                  # Match firmware dead zone
```

### Configuration Checklist
- [ ] Update `WIFI_SSID` and `WIFI_PASSWORD` in `firmware/config.py`
- [ ] Update `SSID` and `PASSWORD` in `scripts/setup_hotspot.sh`
- [ ] Verify `INTERFACE` in `scripts/setup_hotspot.sh` (run `ip link show`)
- [ ] Update `DEFAULT_ROBOT_IP` in `controller_xbox.py` after first boot
- [ ] Ensure pin mappings match your Waveshare Pico-Go version

### Deployment Targets
- **Development**: USB-powered, serial monitor attached, `DEBUG_MODE = True`
- **Testing**: Battery-powered, LCD feedback, controller on laptop
- **Competition**: Battery-powered, autonomous start, pre-tested network config

---

## 6. Build, Run, Test

### Prerequisites
**Hardware**:
- Waveshare Pico-Go v2 with Raspberry Pi Pico W installed
- Charged 7.4V Li-ion battery (2S, ≥1000mAh)
- Xbox controller (wired or Bluetooth)
- Ubuntu 22.04+ laptop with Wi-Fi

**Software**:
- MicroPython 1.22+ flashed to Pico W
- Python 3.11+ on laptop
- `mpremote` for firmware upload
- Git for cloning repo

---

### Quick Start (5 Minutes)

#### 1. Clone Repository
```bash
git clone https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot.git
cd Pico-Go-LAN-Robot
```

#### 2. Setup Laptop
```bash
# Install Python dependencies
pip install -r controller/requirements.txt

# Start hotspot (requires sudo)
sudo ./scripts/setup_hotspot.sh start

# Verify hotspot
./scripts/setup_hotspot.sh status
# Should show: "Hotspot is ACTIVE" and IP 10.42.0.1
```

#### 3. Flash Firmware
```bash
# Install mpremote if not already installed
pip install mpremote

# Connect Pico W via USB
# Upload all firmware files
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :

# Reset Pico
mpremote reset

# Monitor serial output (optional)
mpremote connect /dev/ttyACM0
# Watch for: "Connected! IP: 10.42.0.xxx"
# Note the IP address from serial or LCD
```

#### 4. Run Controller
```bash
# Connect Xbox controller to laptop (USB or Bluetooth)

# Run controller with robot IP from step 3
cd ../controller
python3 controller_xbox.py 10.42.0.123

# Expected output:
# ✅ Controller connected: Xbox Wireless Controller
# 🔌 Connecting to robot at 10.42.0.123:8765...
# ✅ Connected to robot!
# 📊 Packets: 30 | Rate: 30.1 Hz | T: +0.00 | S: +0.00
```

#### 5. Drive!
- **Left Stick Y-axis**: Forward/Reverse throttle
- **Left Stick X-axis**: Steering
- **START Button**: Exit controller app

---

### Development Workflow

#### Firmware Development
```bash
# Edit firmware files
code firmware/motor.py

# Upload changed file
mpremote connect /dev/ttyACM0 cp firmware/motor.py :

# Reset or soft-reset Pico
mpremote reset
# OR in REPL: Ctrl+D

# Monitor output
mpremote connect /dev/ttyACM0

# Quick test in REPL
mpremote connect /dev/ttyACM0 exec "import motor; m = motor.initialize(); m.test_sequence()"
```

#### Controller Development
```bash
# Edit controller
code controller/controller_xbox.py

# Run directly (auto-reload with nodemon equivalent not needed for Python)
python3 controller/controller_xbox.py 10.42.0.123

# Test without robot (will retry connection)
python3 controller/controller_xbox.py 10.42.0.1
```

#### Network Diagnostics
```bash
# Check hotspot status
./scripts/setup_hotspot.sh status

# Scan for robot
sudo ./scripts/setup_hotspot.sh scan
# OR
sudo nmap -sn 10.42.0.0/24

# Test connectivity
ping -c 5 10.42.0.123

# Check latency statistics
ping -c 100 10.42.0.123 | grep avg

# Test TCP port
nc -zv 10.42.0.123 8765
```

---

### Testing Strategy

#### Hardware Tests
```python
# In MicroPython REPL (mpremote connect /dev/ttyACM0)

# Test LED
from machine import Pin
led = Pin("LED", Pin.OUT)
for i in range(5): led.toggle(); time.sleep(0.5)

# Test motors (SECURE ROBOT FIRST!)
import motor
m = motor.initialize()
m.enable()
m.test_sequence()  # Forward, back, left, right, stop
m.disable()

# Test LCD
import lcd_status
lcd = lcd_status.initialize()
lcd.set_state("BOOT")
lcd.set_state("NET_UP", ip="10.42.0.123", rssi=-45)
lcd.set_state("DRIVING", throttle=0.5, steer=-0.2)
```

#### Integration Tests
```bash
# 1. Connectivity Test
# Laptop: sudo ./scripts/setup_hotspot.sh start
# Pico: Power on, wait for NET_UP state
# Laptop: ping 10.42.0.123 (should succeed)

# 2. Control Test
# Run controller, verify:
#   - Controller detects Xbox controller
#   - Connects to robot
#   - LCD shows "DRIVING" state
#   - Motors respond to joystick input
#   - LCD background changes color based on connection

# 3. Safety Test
# While driving, disconnect hotspot or turn off Wi-Fi
# Expected: Motors stop within 200ms, LCD shows red "LINK LOST"
# Reconnect hotspot, robot should resume (auto-reconnect)

# 4. Latency Test
ping -c 100 10.42.0.123 | tail -1
# Should show avg <20ms

# 5. Endurance Test
# Run for 30+ minutes
# Check: Battery voltage, motor temperature, no crashes
```

#### Performance Benchmarks
| Metric | Target | Measured | Status |
|--------|--------|----------|--------|
| Control Latency | ≤20ms | 10-15ms | ✅ Pass |
| Packet Rate | 30 Hz | 30.0-30.2 Hz | ✅ Pass |
| Wi-Fi Range | ≥10m | 15-20m | ✅ Pass |
| Fail-safe Response | ≤250ms | 200ms | ✅ Pass |
| Battery Life | ≥30min | 45-60min | ✅ Pass |

---

## 7. API/Interfaces

### TCP Control Protocol (Port 8765)

#### Controller → Robot (Drive Command)
```json
{
  "t_ms": 1730774000000,
  "seq": 42,
  "cmd": "drive",
  "axes": {
    "throttle": 0.6,
    "steer": -0.2
  }
}
```

**Fields**:
- `t_ms` (int): Timestamp in milliseconds (Unix epoch)
- `seq` (int): Sequence number (incrementing, for packet loss detection)
- `cmd` (str): Command type (`"drive"`, `"stop"`, `"estop"`)
- `axes.throttle` (float): Forward/reverse speed [-1.0, +1.0]
- `axes.steer` (float): Left/right steering [-1.0, +1.0]

**Dead Zone Applied**: Values within ±0.08 clamped to 0.0

#### Robot → Controller (Acknowledgment)
```json
{
  "seq_ack": 42,
  "state": "DRIVING",
  "motor_enabled": true,
  "packets_received": 1234
}
```

**Fields**:
- `seq_ack` (int): Echoes received sequence number
- `state` (str): Current robot state (`BOOT`, `NET_UP`, `DRIVING`, `LINK_LOST`, `E_STOP`)
- `motor_enabled` (bool): Motor driver enabled status
- `packets_received` (int): Total packets received since boot

**Note**: ACKs are sent but not currently processed by controller (future enhancement for RSSI display).

---

### Motor Control API

#### Differential Drive Algorithm
```python
def drive(throttle: float, steer: float) -> None:
    """
    Convert throttle/steer to left/right motor speeds.
    
    Args:
        throttle: Forward/reverse [-1.0, +1.0]
        steer: Left/right [-1.0, +1.0]
    
    Output:
        left_speed = throttle + steer
        right_speed = throttle - steer
        (both clamped to [-1.0, +1.0])
    """
```

**Examples**:
- `drive(0.5, 0.0)` → Forward at 50% (left=0.5, right=0.5)
- `drive(0.5, 0.3)` → Forward-right turn (left=0.8, right=0.2)
- `drive(0.0, 1.0)` → Spin right in place (left=1.0, right=-1.0)
- `drive(-0.5, 0.0)` → Reverse at 50% (left=-0.5, right=-0.5)

---

### LCD Display States

| State | Background | Displays |
|-------|-----------|----------|
| `BOOT` | Blue | "PICO-GO ROBOT Booting..." |
| `NET_UP` | Yellow | IP address, RSSI, "Waiting for controller" |
| `CLIENT_OK` | Green | "CONTROLLER CONNECTED READY" |
| `DRIVING` | Red/Yellow/Green* | Throttle bar, Steer bar, PKT, RSSI, LAT |
| `LINK_LOST` | Red | "CONNECTION LOST! Motors Stopped" |
| `E_STOP` | Red | "EMERGENCY STOP!" |

*Background color in `DRIVING` state indicates connection quality:
- **Green**: <100ms between packets (good)
- **Yellow**: 100-200ms (intermittent)
- **Red**: >200ms (timeout, motors stopped)

---

## 8. Conventions & Guardrails

### Code Style

#### Python (Controller)
- Follow PEP 8
- Use type hints: `def drive(throttle: float, steer: float) -> None:`
- Docstrings for all public functions (Google style)
- Constants in UPPER_CASE
- Class names in PascalCase
- Functions/variables in snake_case

#### MicroPython (Firmware)
- Match Python conventions where possible
- Memory-conscious: avoid large allocations in loops
- Use `const()` for compile-time constants
- Comment complex logic (async tasks, timing-critical sections)
- Keep functions small (<50 lines)

### Git Workflow
- **main**: Production-ready code only
- **dev**: Active development branch (Assumption: not currently used)
- **feature/***: Feature branches (Assumption: merge to dev, then main)
- Commit messages: `Add: feature`, `Fix: bug`, `Docs: update`, `Refactor: improve`

### Safety Conventions
1. **Always test motors on blocks** before ground testing
2. **Verify STBY pin state** before assuming motors disabled
3. **Monitor serial output** during firmware development
4. **Check battery voltage** before each session (>7.0V)
5. **Emergency stop**: Physical power disconnect > software E-stop

### Configuration Guardrails
- **Never commit secrets**: SSID/password in config files are placeholders (change before deployment)
- **Validate pin assignments**: Incorrect pins can damage hardware
- **Test watchdog timeout**: Too short = false alarms, too long = unsafe
- **Verify motor polarity**: Swap wires if forward command goes backward

---

## 9. Testing Strategy

### Test Pyramid

#### Unit Tests (Not Implemented)
**Assumption**: Future enhancement. Would test:
- Motor speed clamping logic
- Dead zone filtering
- JSON parsing
- Differential drive calculations

#### Integration Tests (Manual)
**Procedure**:
1. **Wi-Fi Connection**: Pico connects to hotspot, obtains IP
2. **TCP Server**: Controller connects to robot port 8765
3. **Motor Control**: Joystick input → motors respond correctly
4. **Watchdog**: Disconnect Wi-Fi → motors stop within 200ms
5. **LCD Display**: All states render correctly

#### System Tests (Field Testing)
**Scenarios**:
- **Range Test**: Drive robot to 15m+ distance, verify control maintained
- **Obstacle Course**: Navigate turns, ramps, tight spaces
- **Battery Endurance**: 45+ min continuous operation
- **Latency Stress**: Multiple Wi-Fi devices, microwave interference

### Test Commands

#### Hardware Test
```bash
# Run from mpremote REPL
mpremote connect /dev/ttyACM0 exec "
import motor
m = motor.initialize()
m.enable()
m.drive(0.5, 0.0)  # Forward 50%
import time; time.sleep(2)
m.stop()
m.disable()
print('Motor test complete')
"
```

#### Network Test
```bash
# Latency test
ping -c 100 10.42.0.123 | grep -E "min/avg/max"

# Packet loss test
ping -c 1000 10.42.0.123 | grep "packet loss"

# Signal strength (from laptop)
sudo iw dev wlp112s0 station dump | grep signal
```

#### Controller Test
```bash
# Test without robot (validates controller input)
python3 controller/controller_xbox.py 127.0.0.1
# Press buttons, move sticks, verify console output
```

---

## 10. Known Issues & TODOs

### Known Limitations
1. **Single Controller**: Only one controller can connect at a time (TCP limitation)
2. **No UDP Discovery**: Robot IP must be manually determined from LCD or serial
3. **No OTA Updates**: Firmware updates require USB connection
4. **LCD Update Lag**: Display refresh rate limited to prevent SPI bus contention
5. **2.4 GHz Only**: Wi-Fi restricted to 2.4 GHz band (CYW43439 limitation)

### Active Issues
None—system is operational and stable.

### TODO (Future Enhancements)
- [ ] **UDP Broadcast Discovery**: Robot broadcasts IP on port 5000, controller auto-detects
- [ ] **WebSocket Migration**: Replace TCP with WebSocket for lower latency framing
- [ ] **Telemetry Logging**: CSV export of throttle, steer, RSSI, latency for analysis
- [ ] **Battery Voltage Monitor**: ADC reading on GPIO26, display on LCD, low-battery warning
- [ ] **ACK Processing**: Controller reads robot ACKs, displays RSSI on console
- [ ] **Web Dashboard**: Flask app for real-time telemetry visualization (matplotlib)
- [ ] **Multi-Robot Support**: Unique robot IDs, controller selects target
- [ ] **ROS2 Integration**: Bridge to ROS2 for autonomous navigation stacks
- [ ] **Sensor Integration**: Ultrasonic (HC-SR04), line-following (IR array), IMU (MPU6050)
- [ ] **Unit Tests**: pytest suite for motor logic, JSON parsing, differential drive
- [ ] **CI/CD**: GitHub Actions for automated testing, firmware validation

### Wontfix / Out of Scope
- **Autonomous Navigation**: Platform supports it, but not core objective
- **Camera Streaming**: RP2040 lacks power for video encoding
- **Bluetooth Control**: Wi-Fi provides better range and throughput

---

## 11. Glossary & Abbreviations

| Term | Definition |
|------|------------|
| **ADC** | Analog-to-Digital Converter (e.g., GPIO26-28 on Pico) |
| **AP** | Access Point (laptop acting as Wi-Fi hotspot) |
| **BOM** | Bill of Materials (parts list) |
| **CYW43439** | Wi-Fi/Bluetooth chip on Pico W |
| **DHCP** | Dynamic Host Configuration Protocol (auto-assigns IPs) |
| **E-Stop** | Emergency Stop (immediate motor cutoff) |
| **GPIO** | General Purpose Input/Output (Pico pins) |
| **LCD** | Liquid Crystal Display (ST7789 driver) |
| **LAN** | Local Area Network (Wi-Fi without internet) |
| **mpremote** | MicroPython remote control tool (USB serial) |
| **OTA** | Over-The-Air (wireless firmware updates) |
| **PWM** | Pulse Width Modulation (motor speed control) |
| **REPL** | Read-Eval-Print Loop (interactive Python shell) |
| **RP2040** | Dual-core Cortex-M0+ microcontroller on Pico |
| **RSSI** | Received Signal Strength Indicator (Wi-Fi signal quality, dBm) |
| **RTT** | Round-Trip Time (network latency measurement) |
| **SPI** | Serial Peripheral Interface (LCD communication) |
| **SSID** | Service Set Identifier (Wi-Fi network name) |
| **STA** | Station mode (Wi-Fi client, not AP) |
| **STBY** | Standby pin on TB6612FNG (enable/disable motors) |
| **TB6612FNG** | Dual H-bridge motor driver IC |
| **TCP** | Transmission Control Protocol (reliable, ordered packets) |
| **TT Motor** | Toy Train motor (common DC gearmotor form factor) |
| **UDP** | User Datagram Protocol (fast, unreliable packets) |
| **WPA2-PSK** | Wi-Fi Protected Access 2, Pre-Shared Key (password auth) |

---

## 12. Quick Start Playbooks

### Playbook 1: First-Time Setup (Clean Laptop + New Pico)

**Time**: 15 minutes  
**Prerequisites**: Ubuntu laptop, Pico W, USB cable, Xbox controller

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3-pip python3-pygame network-manager -y

# 2. Clone repo
git clone https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot.git
cd Pico-Go-LAN-Robot

# 3. Install Python tools
pip install mpremote
pip install -r controller/requirements.txt

# 4. Flash MicroPython to Pico W (if not already installed)
# - Download: https://micropython.org/download/RPI_PICO_W/
# - Hold BOOTSEL button, connect USB
# - Drag .uf2 file to RPI-RP2 drive
# - Wait for reboot

# 5. Upload firmware
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :
mpremote reset

# 6. Configure network
# Edit firmware/config.py: Set WIFI_SSID and WIFI_PASSWORD
# Edit scripts/setup_hotspot.sh: Match SSID and PASSWORD

# 7. Start hotspot
cd ..
sudo ./scripts/setup_hotspot.sh start

# 8. Re-upload config and reboot Pico
cd firmware
mpremote connect /dev/ttyACM0 cp config.py :
mpremote reset

# 9. Get robot IP (from LCD or serial)
mpremote connect /dev/ttyACM0
# Note the IP address (e.g., 10.42.0.123)

# 10. Run controller
cd ../controller
python3 controller_xbox.py 10.42.0.123

# 11. Drive!
```

---

### Playbook 2: Daily Operation (System Already Configured)

**Time**: 2 minutes

```bash
# 1. Start hotspot
cd /path/to/Pico-Go-LAN-Robot
sudo ./scripts/setup_hotspot.sh start

# 2. Power on robot (check LCD for IP address)

# 3. Connect Xbox controller to laptop

# 4. Run controller
python3 controller/controller_xbox.py 10.42.0.123

# 5. Drive!

# When done:
# - Press START on controller to exit
# - Power off robot
# - Stop hotspot: sudo ./scripts/setup_hotspot.sh stop
```

---

### Playbook 3: Troubleshooting Network Issues

```bash
# Symptom: Robot won't connect to hotspot

# 1. Verify hotspot is running
./scripts/setup_hotspot.sh status
# Should show "Hotspot is ACTIVE"

# 2. Check robot serial output
mpremote connect /dev/ttyACM0
# Look for: "Wi-Fi connection failed" or "Connected! IP: x.x.x.x"

# 3. Verify SSID/password match
# firmware/config.py: WIFI_SSID and WIFI_PASSWORD
# setup_hotspot.sh: SSID and PASSWORD

# 4. Restart hotspot
sudo ./scripts/setup_hotspot.sh restart

# 5. Power cycle robot

# 6. If still failing, test Wi-Fi manually in REPL
mpremote connect /dev/ttyACM0 exec "
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print(wlan.scan())  # Should list 'PicoLAN' or your SSID
wlan.connect('PicoLAN', 'pico1234')
import time; time.sleep(5)
print(wlan.isconnected())
print(wlan.ifconfig())
"
```

---

### Playbook 4: Updating Firmware

```bash
# Scenario: You modified motor.py and want to test

# 1. Connect Pico via USB
mpremote connect /dev/ttyACM0

# 2. Upload changed file(s)
mpremote cp firmware/motor.py :

# 3. Reset Pico
mpremote exec "import machine; machine.soft_reset()"

# 4. Monitor output
mpremote connect /dev/ttyACM0
# Verify no errors during startup

# 5. Test with controller
python3 controller/controller_xbox.py 10.42.0.123
```

---

### Playbook 5: Competition Deployment

**Checklist**:
- [ ] Battery fully charged (≥8.0V)
- [ ] Firmware tested in practice arena
- [ ] Network credentials match competition Wi-Fi (if applicable)
- [ ] Motor directions verified (forward = forward)
- [ ] Watchdog timeout tested (disconnect = stop)
- [ ] LCD visible and functional
- [ ] Controller batteries fresh (if wireless Xbox controller)
- [ ] Backup Pico with firmware on USB drive

**Pre-Match**:
```bash
# 1. Power on robot 30 seconds before match
# 2. Verify LCD shows green "DRIVING" state
# 3. Test forward, reverse, turn (2 seconds each)
# 4. Park in starting position
# 5. Wait for start signal
```

**Post-Match**:
```bash
# 1. Power off robot immediately
# 2. Check battery voltage (should be >7.2V)
# 3. Inspect motors/gearboxes for damage
# 4. Download telemetry logs (if implemented)
```

---

## 13. Change Risk Areas

### High-Risk Changes (Test Extensively)

#### 1. Safety System Modifications
**Files**: `firmware/watchdog.py`, `firmware/config.py` (WATCHDOG_TIMEOUT_MS)

**Risks**:
- Timeout too short → false positives (motors stop unnecessarily)
- Timeout too long → unsafe (motors don't stop on link loss)
- Watchdog disabled → no fail-safe protection

**Testing**: Disconnect Wi-Fi during operation, verify motors stop within timeout + 50ms margin.

#### 2. Motor Control Logic
**Files**: `firmware/motor.py`, `firmware/config.py` (pin assignments)

**Risks**:
- Incorrect PWM polarity → motors run backward
- Pin conflicts → GPIO collision with LCD or other peripherals
- Speed clamping removed → over-voltage to motors
- STBY pin misconfigured → motors won't enable

**Testing**: Test on blocks. Verify forward/reverse/left/right/stop. Check motor temperature after 5 min operation.

#### 3. Network Configuration
**Files**: `firmware/config.py` (WIFI_SSID, WIFI_PASSWORD), `scripts/setup_hotspot.sh`

**Risks**:
- Typo in SSID/password → robot won't connect
- Wrong network band (5 GHz) → Pico W can't connect (2.4 GHz only)
- IP conflicts → robot unreachable

**Testing**: Power cycle robot, verify LCD shows IP address within 10 seconds. Ping robot from laptop.

---

### Medium-Risk Changes (Test Thoroughly)

#### 4. LCD Display Updates
**Files**: `firmware/lcd_status.py`, `firmware/config.py` (LCD pins)

**Risks**:
- SPI frequency too high → garbled display
- Incorrect pins → no display output
- Excessive refresh rate → CPU/SPI bus contention, control loop lag

**Testing**: Verify all states render correctly. Monitor control latency (should stay <20ms).

#### 5. Control Protocol Changes
**Files**: `firmware/ws_server.py`, `controller/controller_xbox.py`

**Risks**:
- JSON schema mismatch → parse errors
- Packet rate too high → network congestion
- Dead zone changes → drifting or unresponsive robot

**Testing**: Drive for 5+ minutes. Monitor packet loss (should be 0%). Verify dead zone prevents drift.

---

### Low-Risk Changes (Standard Testing)

#### 6. Documentation Updates
**Files**: `*.md`, `docs/*`

**Risks**: None (documentation doesn't affect runtime)

**Testing**: Verify links, spelling, code examples are accurate.

#### 7. Utility Functions
**Files**: `firmware/utils.py`

**Risks**: Low (isolated helper functions)

**Testing**: Unit test if possible, otherwise verify callers work correctly.

---

### Critical Files (DO NOT DELETE)

| File | Purpose | Impact if Deleted |
|------|---------|-------------------|
| `firmware/main.py` | Entry point | Robot won't boot |
| `firmware/config.py` | All settings | Compile errors everywhere |
| `firmware/motor.py` | Motor control | No movement |
| `firmware/watchdog.py` | Safety system | No fail-safe, UNSAFE |
| `controller/controller_xbox.py` | Controller app | Can't control robot |
| `scripts/setup_hotspot.sh` | Network setup | No LAN, can't connect |

---

### Debugging Tips for Risky Changes

**Before Making Changes**:
1. Git commit current working state: `git commit -am "Working state before X change"`
2. Note robot IP and current behavior
3. Take photo/video of LCD states if testing display changes

**After Making Changes**:
1. Upload to robot: `mpremote cp <file> :`
2. Reset: `mpremote exec "import machine; machine.soft_reset()"`
3. Monitor serial: `mpremote connect /dev/ttyACM0`
4. Look for exceptions, infinite loops, or missing output

**If Things Break**:
1. Check serial output for error messages
2. Revert file: `git checkout HEAD -- <file>`
3. Re-upload: `mpremote cp <file> :`
4. Reset: `mpremote reset`

---

## Appendix: Network Topology Diagram

```
                    Internet
                       ❌ (Air-gapped)
                       
                       
    ┌──────────────────────────────────────────┐
    │     Ubuntu Laptop (10.42.0.1)            │
    │  ┌─────────────────────────────────────┐ │
    │  │   NetworkManager Hotspot (AP)       │ │
    │  │   SSID: PicoLAN                     │ │
    │  │   Auth: WPA2-PSK                    │ │
    │  │   Band: 2.4 GHz (802.11n)           │ │
    │  └─────────────────────────────────────┘ │
    │  ┌─────────────────────────────────────┐ │
    │  │   DHCP Server                       │ │
    │  │   Range: 10.42.0.50 - 10.42.0.150   │ │
    │  └─────────────────────────────────────┘ │
    │  ┌─────────────────────────────────────┐ │
    │  │   Python Controller App             │ │
    │  │   TCP Client → 10.42.0.x:8765       │ │
    │  └─────────────────────────────────────┘ │
    └──────────────────────────────────────────┘
                       │
                       │ Wi-Fi (2.4 GHz)
                       │ ~15-20m range
                       │
    ┌──────────────────────────────────────────┐
    │  Raspberry Pi Pico W (10.42.0.123)       │
    │  ┌─────────────────────────────────────┐ │
    │  │   CYW43439 Wi-Fi (STA Mode)         │ │
    │  │   DHCP Client                       │ │
    │  └─────────────────────────────────────┘ │
    │  ┌─────────────────────────────────────┐ │
    │  │   TCP Server (Port 8765)            │ │
    │  │   Receives: JSON drive commands     │ │
    │  │   Sends: JSON acknowledgments       │ │
    │  └─────────────────────────────────────┘ │
    └──────────────────────────────────────────┘
```

---

## Appendix: Packet Flow Sequence

```
Controller                           Robot
    │                                   │
    │  1. TCP SYN (establish)          │
    ├──────────────────────────────────>│
    │                                   │
    │  2. SYN-ACK                       │
    │<──────────────────────────────────┤
    │                                   │
    │  3. ACK (connected)               │
    ├──────────────────────────────────>│
    │                                   │
    │                                   │
    ├─── 30 Hz Control Loop ────────────┤
    │                                   │
    │  4. JSON: {seq:1, throttle:0.5}  │
    ├──────────────────────────────────>│
    │                                   │ → Parse JSON
    │                                   │ → Feed watchdog (reset timer)
    │                                   │ → motor.drive(0.5, 0.0)
    │                                   │ → LCD update (if changed)
    │                                   │
    │  5. JSON: {seq_ack:1, state:...} │
    │<──────────────────────────────────┤
    │                                   │
    │  6. JSON: {seq:2, throttle:0.6}  │
    ├──────────────────────────────────>│
    │                                   │
    │  ... (continues @ 30 Hz) ...      │
    │                                   │
    │                                   │
    ├─── Timeout Scenario ──────────────┤
    │                                   │
    │  (Wi-Fi drops)                    │
    │                                   │ ⏰ Watchdog timer expires (200ms)
    │                                   │ → motor.stop()
    │                                   │ → lcd.set_state("LINK_LOST")
    │                                   │ → Background: Red screen
    │                                   │
    │  (Wi-Fi restores)                 │
    │                                   │
    │  7. JSON: {seq:50, throttle:0.0} │
    ├──────────────────────────────────>│
    │                                   │ → Feed watchdog (resume)
    │                                   │ → lcd.set_state("DRIVING")
    │                                   │ → Background: Green (if <100ms)
    │                                   │
```

---

**End of init.md**  
**For questions, see**: `docs/TROUBLESHOOTING.md` or open GitHub issue  
**For quick start, see**: `docs/QUICKSTART.md`  
**For hardware setup, see**: `docs/HARDWARE.md`
