# Task Routing Guide

## Overview

This document provides a comprehensive mapping of task types, feature categories, bug classifications, and task patterns to their appropriate agent assignments. Use this guide to quickly determine which agent(s) should handle a given task.

---

## Feature Request Routing

### Firmware & Hardware Features

**Route to: Firmware Agent**

#### Motor Control Features
- Motor speed control improvements
- PWM frequency optimization
- Motor acceleration/deceleration curves
- Motor direction control
- Motor braking mechanisms
- Motor calibration procedures

**Keywords**: `motor`, `PWM`, `servo`, `actuator`, `drive`, `movement`

#### Sensor Integration
- New sensor support (ultrasonic, IR, IMU, etc.)
- Sensor calibration routines
- Sensor data filtering
- Sensor fusion algorithms
- Sensor reading optimization

**Keywords**: `sensor`, `ultrasonic`, `IR`, `IMU`, `gyro`, `accelerometer`, `calibration`

#### Watchdog & Safety
- Watchdog timer improvements
- Fail-safe mechanisms
- Emergency stop functionality
- Safety timeout handling
- Recovery procedures

**Keywords**: `watchdog`, `fail-safe`, `safety`, `emergency`, `timeout`, `recovery`

#### Hardware Interfaces
- GPIO pin management
- I2C/SPI communication
- ADC reading optimization
- Hardware abstraction layers
- Component initialization

**Keywords**: `GPIO`, `I2C`, `SPI`, `ADC`, `hardware`, `interface`, `pin`

#### Boot & Configuration
- Boot sequence optimization
- Configuration file handling
- Startup procedures
- Initialization order
- Error handling during boot

**Keywords**: `boot`, `startup`, `init`, `configuration`, `config`, `setup`

#### WiFi & Network (Firmware Side)
- WiFi connection management
- WebSocket server implementation
- Network error handling
- Connection stability
- Firmware-side protocol handling

**Keywords**: `wifi`, `websocket server`, `firmware network`, `connection`

---

### Controller & Network Features

**Route to: Controller Agent**

#### Input Handling
- Input device support (Xbox, keyboard, gamepad)
- Input mapping and remapping
- Dead-zone configuration
- Input scaling and curves
- Button/trigger mapping
- Input validation

**Keywords**: `input`, `xbox`, `gamepad`, `controller`, `joystick`, `dead-zone`, `mapping`

#### WebSocket Client
- WebSocket client implementation
- Connection management
- Reconnection logic
- Error handling
- Message queuing
- Connection status monitoring

**Keywords**: `websocket client`, `connection`, `reconnect`, `client`

#### Network Configuration
- Ubuntu hotspot setup
- DHCP configuration
- IP addressing
- Network troubleshooting
- Network diagnostics
- Connection testing

**Keywords**: `network`, `hotspot`, `DHCP`, `IP`, `LAN`, `connection setup`

#### Protocol & Communication
- JSON packet structure design
- Command encoding/decoding
- Protocol versioning
- Message validation
- Error reporting
- Status updates

**Keywords**: `protocol`, `packet`, `JSON`, `message`, `command`, `communication`

#### Performance Optimization (Controller Side)
- Input processing speed
- WebSocket overhead reduction
- Network latency optimization
- Reconnection time improvement
- Packet size optimization

**Keywords**: `controller performance`, `input speed`, `network latency`, `optimization`

---

### Documentation Features

**Route to: Documentation Agent**

#### Documentation Creation
- New documentation pages
- Quick-start guides
- Tutorial creation
- API documentation
- Architecture diagrams
- User manuals

**Keywords**: `documentation`, `guide`, `tutorial`, `manual`, `docs`, `README`

#### Performance Reporting
- Performance test execution
- Benchmark results compilation
- Performance graphs creation
- Trend analysis
- Performance summaries

**Keywords**: `performance report`, `benchmark`, `metrics`, `testing`, `results`

#### Reproducibility
- Build procedure documentation
- Setup instructions
- Dependency documentation
- Troubleshooting guides
- Known issues documentation

**Keywords**: `reproducibility`, `setup`, `build`, `install`, `troubleshooting`

#### Visual Documentation
- Architecture diagrams
- Data flow diagrams
- Hardware schematics (documentation)
- Sequence diagrams
- State diagrams

**Keywords**: `diagram`, `architecture`, `schematic`, `visual`, `flow`

---

### Cross-Agent Features

**Route to: Director (coordinates multiple agents)**

#### Protocol Changes
- New communication protocol
- Protocol version updates
- Protocol encryption
- Protocol optimization

**Coordination**: Firmware Agent + Controller Agent + Documentation Agent

#### End-to-End Features
- Complete feature requiring firmware and controller
- System-wide optimizations
- Major architectural changes
- Integration features

**Coordination**: All relevant agents

#### Performance Optimization (System-Wide)
- End-to-end latency reduction
- Overall system optimization
- Cross-layer performance improvements

**Coordination**: Firmware Agent + Controller Agent + Documentation Agent

---

## Bug Report Routing

### Firmware Bugs

**Route to: Firmware Agent**

#### Motor Control Bugs
- Motor not responding
- Motor stuttering or jittering
- PWM instability
- Motor direction incorrect
- Motor speed inconsistent
- Motor overheating

**Keywords**: `motor not working`, `PWM`, `motor stutter`, `motor jitter`, `motor direction`

#### Sensor Bugs
- Sensor readings incorrect
- Sensor not detected
- Sensor calibration failure
- Sensor data noise
- Sensor timeout

**Keywords**: `sensor error`, `sensor reading`, `sensor not working`, `sensor calibration`

#### Watchdog Bugs
- Watchdog timeout too short/long
- Watchdog not triggering
- Fail-safe not working
- Recovery failure
- System lockup

**Keywords**: `watchdog`, `fail-safe`, `timeout`, `lockup`, `freeze`

#### Hardware Interface Bugs
- GPIO not working
- I2C/SPI communication failure
- ADC reading incorrect
- Pin configuration error
- Hardware initialization failure

**Keywords**: `GPIO`, `I2C`, `SPI`, `ADC`, `hardware error`, `pin`

#### Boot & Startup Bugs
- Boot failure
- Startup sequence error
- Configuration loading failure
- Initialization error
- Boot loop

**Keywords**: `boot`, `startup`, `init error`, `boot failure`, `boot loop`

#### WiFi & Network (Firmware Side) Bugs
- WiFi connection failure
- WebSocket server not starting
- Connection drops
- Network timeout
- Protocol handling error

**Keywords**: `wifi`, `websocket server`, `connection`, `network error`

---

### Controller Bugs

**Route to: Controller Agent**

#### Input Bugs
- Input not responding
- Input mapping incorrect
- Dead-zone not working
- Button not detected
- Input lag

**Keywords**: `input not working`, `input mapping`, `dead-zone`, `button`, `input lag`

#### WebSocket Client Bugs
- Connection failure
- Reconnection not working
- Message not sending
- Message not receiving
- Connection drops frequently

**Keywords**: `websocket client`, `connection`, `reconnect`, `message`, `disconnect`

#### Network Configuration Bugs
- Hotspot not working
- DHCP failure
- IP address conflict
- Network not accessible
- Connection timeout

**Keywords**: `hotspot`, `DHCP`, `IP`, `network`, `connection`

#### Protocol Bugs
- Packet parsing error
- Protocol mismatch
- Message format error
- Command not recognized
- Status update failure

**Keywords**: `protocol`, `packet`, `message`, `command`, `parsing`

---

### Documentation Bugs

**Route to: Documentation Agent**

#### Documentation Accuracy Bugs
- Documentation outdated
- Instructions don't match code
- Missing information
- Incorrect examples
- Wrong file paths

**Keywords**: `documentation outdated`, `instructions wrong`, `missing info`, `incorrect`

#### Reproducibility Bugs
- Build procedure doesn't work
- Setup instructions incomplete
- Dependencies missing
- Steps don't work as written
- Configuration examples wrong

**Keywords**: `build`, `setup`, `procedure`, `instructions`, `reproducibility`

#### Performance Report Bugs
- Performance metrics incorrect
- Test results outdated
- Benchmarks wrong
- Graphs missing or incorrect

**Keywords**: `performance`, `metrics`, `benchmark`, `test results`

---

### Integration Bugs

**Route to: Director (coordinates resolution)**

#### Protocol Mismatch Bugs
- Firmware and controller protocol incompatible
- Version mismatch
- Packet format mismatch
- Command not understood

**Coordination**: Firmware Agent + Controller Agent

#### Cross-Layer Bugs
- End-to-end communication failure
- Latency issues across layers
- Integration test failures
- Compatibility issues

**Coordination**: All relevant agents

#### Architecture Bugs
- Design violation
- Architectural inconsistency
- Integration point failure

**Coordination**: Director analyzes, assigns to appropriate agents

---

## Performance Task Routing

### Firmware Performance

**Route to: Firmware Agent**

- Control latency optimization (target: ≤20ms)
- Watchdog timing optimization (target: <200ms)
- PWM frequency optimization
- Boot time reduction
- Sensor reading speed
- Motor response time

**Metrics**: Control latency, watchdog timeout, PWM stability, boot time

---

### Controller Performance

**Route to: Controller Agent**

- Network latency optimization (target: <50ms end-to-end)
- WebSocket overhead reduction
- Input processing speed
- Reconnection time (target: <5s)
- Packet processing speed
- Connection stability

**Metrics**: Network latency, reconnection time, packet delivery rate, input lag

---

### System Performance

**Route to: Director (coordinates optimization)**

- End-to-end latency (firmware + network)
- Overall system responsiveness
- Cross-layer optimization
- System-wide performance tuning

**Coordination**: Firmware Agent + Controller Agent + Documentation Agent

**Metrics**: End-to-end latency, system reliability, user experience

---

## Task Type Patterns

### Quick Reference Table

| Task Pattern | Agent | Coordination |
|-------------|-------|--------------|
| `motor`, `PWM`, `servo` | Firmware | None |
| `sensor`, `ultrasonic`, `IMU` | Firmware | None |
| `watchdog`, `fail-safe` | Firmware | None |
| `GPIO`, `I2C`, `SPI` | Firmware | None |
| `boot`, `startup`, `init` | Firmware | None |
| `input`, `xbox`, `gamepad` | Controller | None |
| `websocket client` | Controller | None |
| `hotspot`, `DHCP`, `network` | Controller | None |
| `protocol`, `packet`, `JSON` | Controller/Firmware | If cross-agent |
| `documentation`, `guide`, `README` | Documentation | None |
| `performance report`, `benchmark` | Documentation | None |
| `end-to-end`, `system-wide` | Director | All agents |
| `architecture`, `design` | Director | All agents |
| `integration`, `compatibility` | Director | Multiple agents |

---

## Dependency Mapping

### Common Dependencies

#### Firmware → Controller
- **Trigger**: Protocol changes, new commands
- **Action**: Controller Agent updates client to match

#### Controller → Firmware
- **Trigger**: New controller features needing firmware support
- **Action**: Firmware Agent implements required functionality

#### Any Code Change → Documentation
- **Trigger**: Any firmware or controller change
- **Action**: Documentation Agent updates relevant docs

#### Performance Task → All Agents
- **Trigger**: System-wide performance optimization
- **Action**: Director coordinates optimization across layers

---

## Routing Decision Tree

```
START: Receive Task

Is it a documentation-only task?
  YES → Route to Documentation Agent
  NO → Continue

Does it affect firmware/hardware?
  YES → Does it also affect controller?
    YES → Route to Director (coordinate)
    NO → Route to Firmware Agent
  NO → Continue

Does it affect controller/network?
  YES → Does it also affect firmware?
    YES → Route to Director (coordinate)
    NO → Route to Controller Agent
  NO → Continue

Does it affect multiple components?
  YES → Route to Director (coordinate)
  NO → Route to Documentation Agent (if docs) or Director (if unclear)

END: Task Routed
```

---

## Special Cases

### Ambiguous Tasks

If a task is unclear or could belong to multiple agents:
1. Route to Director for analysis
2. Director classifies and delegates
3. Director coordinates if needed

### Emergency/Critical Tasks

For critical bugs or urgent features:
1. Route immediately to appropriate agent
2. Set high priority
3. Director monitors closely
4. Expedited integration if safe

### Research Tasks

For tasks requiring investigation:
1. Route to Director for initial analysis
2. Director may assign to multiple agents for research
3. Director synthesizes findings
4. Director creates implementation plan

---

## Examples

### Example 1: Simple Feature
```
Task: "Add support for ultrasonic sensor"
Routing: Firmware Agent
Reason: Hardware integration, sensor-specific
Coordination: None
```

### Example 2: Simple Bug
```
Task: "Motor stutters at low speeds"
Routing: Firmware Agent
Reason: Motor control issue, PWM-related
Coordination: None
```

### Example 3: Cross-Agent Feature
```
Task: "Implement encrypted communication"
Routing: Director
Reason: Requires firmware and controller changes
Coordination: 
  - Firmware Agent: Encryption in WebSocket server
  - Controller Agent: Encryption in WebSocket client
  - Documentation Agent: Update protocol docs
```

### Example 4: Performance Task
```
Task: "Reduce end-to-end latency to 30ms"
Routing: Director
Reason: System-wide optimization
Coordination:
  - Firmware Agent: Optimize control loop
  - Controller Agent: Optimize network communication
  - Documentation Agent: Update performance benchmarks
```

### Example 5: Documentation Task
```
Task: "Create quick-start guide for new developers"
Routing: Documentation Agent
Reason: Documentation creation
Coordination: None (but may need info from other agents)
```

---

This routing guide ensures tasks are assigned to the most appropriate agent(s) while maintaining clear boundaries and coordination when needed.

