# Robot Calibration System

## Overview

The Pico-Go robots now have a comprehensive calibration system that compensates for hardware variations between different units. Calibration data is **stored on the robot** and automatically loaded when connecting from any controller machine.

## Calibration Parameters

Each robot stores three calibration values:

1. **Steering Trim** (`steering_trim`): -0.5 to +0.5
   - Compensates for drift when driving straight
   - Positive = adds right steering, Negative = adds left steering
   
2. **Left Motor Balance** (`motor_left_scale`): 0.5 to 1.0
   - Reduces left motor power if it's stronger than the right
   
3. **Right Motor Balance** (`motor_right_scale`): 0.5 to 1.0
   - Reduces right motor power if it's stronger than the left

## Quick Start

### 1. Initial Calibration

```bash
# Connect to robot and run calibration tool
python3 controller/calibrate.py 192.168.8.230
```

### 2. Calibrate Steering Trim

1. Drive forward at medium speed
2. Observe drift direction:
   - **Drifts LEFT** → Press D-Pad UP to increase trim
   - **Drifts RIGHT** → Press D-Pad DOWN to decrease trim
3. Test again and fine-tune
4. Press **A button** to save

### 3. Calibrate Motor Balance

If the robot still drifts after steering trim:

1. **Left motor too strong** (robot veers left):
   - Press D-Pad LEFT to reduce left motor power
   
2. **Right motor too strong** (robot veers right):
   - Press LB (Left Bumper) to reduce right motor power

3. Press **A button** to save

### 4. Normal Operation

```bash
# Run normal controller - calibration auto-loads!
python3 controller/controller_xbox.py 192.168.8.230
```

The controller will automatically fetch and display the robot's calibration on connect.

## Calibration Tool Controls

| Control | Function |
|---------|----------|
| Right Trigger | Drive forward (for testing) |
| Left Stick X | Steering |
| D-Pad ↑ | Increase steering trim (+right) |
| D-Pad ↓ | Decrease steering trim (+left) |
| D-Pad ← | Decrease left motor power |
| D-Pad → | Increase left motor power |
| LB (Button 4) | Decrease right motor power |
| RB (Button 5) | Increase right motor power |
| A Button | **SAVE** calibration to robot |
| B Button | Reset to defaults |
| START | Exit (warns if unsaved) |

## How It Works

### Storage Location

Calibration is stored in `/calibration.json` on the robot's filesystem (Pico W flash memory). This persists across reboots and firmware updates.

### Calibration Flow

```
[Controller Connects] 
    ↓
[Requests calibration via UDP]
    ↓
[Robot sends calibration.json data]
    ↓
[Controller displays calibration]
    ↓
[Normal driving with calibration applied on robot]
```

### Where Calibration is Applied

- **Steering Trim**: Applied in `firmware/ws_server.py` when processing drive commands
- **Motor Balance**: Applied in `firmware/motor.py` before sending PWM signals

This ensures calibration works regardless of which machine runs the controller.

## Firmware Integration

To enable calibration on a robot, the firmware must initialize the calibration manager:

```python
# In firmware/main.py
import calibration

# Initialize with unique robot ID
cal_mgr = calibration.initialize(robot_id="picogo1")

# Pass to WebSocket server
ws_server = ws_server.initialize(motor, safety, lcd, cal_mgr)

# Apply motor balance on startup
motor.set_motor_balance(
    cal_mgr.get("motor_left_scale", 1.0),
    cal_mgr.get("motor_right_scale", 1.0)
)
```

## Troubleshooting

### Robot still drifts after trim calibration

Try motor balance calibration instead. Steering trim compensates for slight imbalances, but if one motor is significantly stronger, use motor balance.

### Calibration not saving

- Check that the robot filesystem has write permissions
- Verify `/calibration.json` exists after saving
- Check robot debug output for save errors

### Calibration not loading on controller

- Ensure robot firmware includes calibration module
- Check that WebSocket server is passing calibration_manager
- Verify robot responds to `get_calibration` command

### Different calibration needed for different speeds

This is normal - calibration is a compromise. If drift is speed-dependent:
1. Calibrate at the most commonly used speed
2. Consider adjusting `SPEED_STEERING_REDUCTION` in controller config

## Advanced: Manual Calibration Edit

You can also manually edit calibration on the robot:

```bash
# Connect via mpremote
mpremote connect /dev/ttyACM0

# Edit calibration file
mpremote edit /calibration.json
```

Example `/calibration.json`:
```json
{
  "robot_id": "picogo1",
  "steering_trim": 0.08,
  "motor_left_scale": 0.95,
  "motor_right_scale": 1.0,
  "version": 1
}
```

## Multiple Robots

Each robot maintains its own calibration. When you connect to a different robot, the controller automatically fetches that robot's specific calibration.

**Example workflow:**
```bash
# Calibrate robot 1
python3 controller/calibrate.py 192.168.8.230  # Save trim: +0.08
python3 controller/controller_xbox.py 192.168.8.230  # Uses trim: +0.08

# Calibrate robot 2
python3 controller/calibrate.py 192.168.8.231  # Save trim: -0.05
python3 controller/controller_xbox.py 192.168.8.231  # Uses trim: -0.05

# Switch back to robot 1
python3 controller/controller_xbox.py 192.168.8.230  # Uses trim: +0.08 ✓
```

No need to reconfigure - each robot remembers its own calibration!

## Files

- `firmware/calibration.py` - Calibration storage module
- `firmware/ws_server.py` - Calibration protocol handlers
- `firmware/motor.py` - Motor balance application
- `controller/calibrate.py` - Interactive calibration tool
- `controller/controller_xbox.py` - Auto-loading on connect
