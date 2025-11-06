# Troubleshooting Guide - Pico-Go LAN Robot

## 🔍 Quick Diagnostic Checklist

Before diving into specific issues, run through this checklist:

- [ ] Battery charged and connected properly
- [ ] Pico W properly seated in headers
- [ ] Ubuntu hotspot active: `./setup_hotspot.sh status`
- [ ] Xbox controller connected and recognized
- [ ] Firmware uploaded to Pico W
- [ ] Serial output visible: `mpremote connect /dev/ttyACM0`
- [ ] Robot IP address known (from LCD or serial)

---

## 🚨 Common Issues & Solutions

### 1. No Power / No LED

**Symptom**: Nothing happens when power is applied

**Possible Causes**:
- Dead battery
- Loose connection
- Blown fuse
- Faulty regulator

**Solutions**:
1. Check battery voltage with multimeter (should be 7.0-8.4V for 2S)
2. Verify all power connections tight
3. Test 5V regulator output (should be 4.9-5.1V)
4. Connect via USB to isolate power vs. MCU issue
5. Replace fuse if installed

**Test**:
```bash
# Connect via USB
mpremote connect /dev/ttyACM0
# If REPL appears, MCU is fine - power circuit issue
```

---

### 2. LCD Shows Nothing or White Screen

**Symptom**: LCD backlight on but no display, or completely white

**Possible Causes**:
- SPI not initialized
- Wrong driver
- Loose connection
- Incorrect pin configuration

**Solutions**:
1. **Check physical connection**:
   - Reseat LCD connector
   - Verify no bent pins

2. **Test backlight independently**:
   ```python
   from machine import Pin
   bl = Pin(21, Pin.OUT)
   bl.value(1)  # Should see backlight
   ```

3. **Verify SPI communication**:
   ```python
   from machine import Pin, SPI
   spi = SPI(0, baudrate=40000000, sck=Pin(18), mosi=Pin(19))
   spi.write(b'\x00\xFF')  # Send test data
   ```

4. **Check pin mappings** in `config.py`:
   ```python
   PIN_LCD_SCK = 18
   PIN_LCD_MOSI = 19
   PIN_LCD_DC = 16
   PIN_LCD_RST = 20
   PIN_LCD_CS = 17
   PIN_LCD_BL = 21
   ```

5. **Install ST7789 driver** if missing:
   ```bash
   mpremote mip install st7789
   ```

---

### 3. Motors Don't Move

**Symptom**: Power on, no motor movement even with commands

**Possible Causes**:
- STBY pin not enabled
- Incorrect wiring
- Faulty motor driver
- Motors not receiving PWM

**Diagnostic Steps**:

1. **Check STBY pin**:
   ```python
   from machine import Pin
   stby = Pin(6, Pin.OUT)
   stby.value(1)  # Must be HIGH to enable
   print(f"STBY: {stby.value()}")  # Should print 1
   ```

2. **Test motor driver directly**:
   ```python
   from machine import Pin, PWM
   
   # Enable driver
   stby = Pin(6, Pin.OUT)
   stby.value(1)
   
   # Test Motor A
   pwm = PWM(Pin(0))
   pwm.freq(20000)
   in1 = Pin(1, Pin.OUT)
   in2 = Pin(2, Pin.OUT)
   
   # Forward
   in1.value(1)
   in2.value(0)
   pwm.duty_u16(32768)  # 50% duty
   
   # Wait 2 seconds
   import time
   time.sleep(2)
   
   # Stop
   pwm.duty_u16(0)
   ```

3. **Check motor connections**:
   - Verify motor wires connected to terminal block
   - Test motors with external power source (6-7V)

4. **Verify power to motor driver**:
   - VM pin should have 7.4V (battery voltage)
   - VCC pin should have 5V (logic voltage)

---

### 4. Wi-Fi Won't Connect

**Symptom**: Robot stuck at "BOOT" state, never shows "NET UP"

**Diagnostic Steps**:

1. **Verify hotspot is running**:
   ```bash
   ./setup_hotspot.sh status
   # Should show "Hotspot is ACTIVE"
   ```

2. **Check SSID/password in config**:
   ```python
   # In firmware/config.py
   WIFI_SSID = "PicoLAN"  # Must match hotspot SSID exactly
   WIFI_PASSWORD = "pico1234"  # Case-sensitive!
   ```

3. **Test Wi-Fi manually**:
   ```python
   # In MicroPython REPL
   import network
   
   wlan = network.WLAN(network.STA_IF)
   wlan.active(True)
   
   # Scan for networks
   networks = wlan.scan()
   for net in networks:
       print(net[0].decode())  # Should see "PicoLAN"
   
   # Try connecting
   wlan.connect("PicoLAN", "pico1234")
   
   # Wait and check
   import time
   time.sleep(5)
   print(wlan.isconnected())  # Should be True
   print(wlan.ifconfig())  # Should show IP
   ```

4. **Common fixes**:
   - Restart hotspot: `sudo ./setup_hotspot.sh restart`
   - Verify using Pico **W** not regular Pico
   - Re-flash MicroPython firmware
   - Try different Wi-Fi channel in setup script

---

### 5. Controller Can't Connect to Robot

**Symptom**: "Connection failed" in controller app

**Diagnostic Steps**:

1. **Verify robot IP**:
   - Check LCD display
   - Or use serial: `mpremote connect /dev/ttyACM0`

2. **Test network connectivity**:
   ```bash
   # Ping robot
   ping -c 5 10.42.0.123
   # Should get responses with <20ms latency
   ```

3. **Test TCP port**:
   ```bash
   # Check if port 8765 is open
   nc -zv 10.42.0.123 8765
   # Should say "succeeded!"
   ```

4. **Check firewall**:
   ```bash
   sudo ufw status
   # If active and blocking:
   sudo ufw allow 8765
   ```

5. **Verify controller configuration**:
   ```python
   # In controller_xbox.py
   DEFAULT_ROBOT_IP = "10.42.0.123"  # Update to actual IP
   ROBOT_PORT = 8765
   ```

6. **Test with telnet**:
   ```bash
   telnet 10.42.0.123 8765
   # Should connect
   # Try sending: {"cmd":"ping","seq":1}
   ```

---

### 6. No Xbox Controller Detected

**Symptom**: "No controller detected!" message

**Solutions**:

1. **Verify controller connected**:
   ```bash
   ls /dev/input/js*
   # Should show /dev/input/js0
   ```

2. **Test with jstest**:
   ```bash
   sudo apt install joystick
   jstest /dev/input/js0
   # Should show button/axis values
   ```

3. **Check pygame detection**:
   ```python
   import pygame
   pygame.init()
   pygame.joystick.init()
   print(f"Controllers: {pygame.joystick.get_count()}")
   # Should be > 0
   ```

4. **Bluetooth issues** (if using wireless):
   ```bash
   # Check Bluetooth status
   bluetoothctl
   > devices
   > connect [MAC_ADDRESS]
   ```

5. **Install dependencies**:
   ```bash
   sudo apt install python3-pygame
   pip install pygame --upgrade
   ```

---

### 7. Laggy or Jerky Control

**Symptom**: Delayed response, stuttering movement

**Possible Causes**:
- High network latency
- Weak Wi-Fi signal
- Interference
- Low packet rate

**Diagnostic Steps**:

1. **Measure latency**:
   ```bash
   ping -c 100 10.42.0.123 | grep avg
   # Should be <20ms average
   ```

2. **Check signal strength**:
   ```bash
   sudo iw dev wlan0 station dump | grep signal
   # Should be >-60 dBm
   ```

3. **Monitor packet rate**:
   Controller prints rate every second:
   ```
   📊 Packets: 300 | Rate: 30.1 Hz | T: +0.75 | S: -0.20
   ```
   Should consistently show ~30 Hz

**Solutions**:

1. **Reduce distance** - keep laptop <10m from robot
2. **Eliminate interference**:
   ```bash
   # Turn off Bluetooth temporarily
   sudo rfkill block bluetooth
   ```
3. **Change Wi-Fi channel**:
   ```bash
   # Edit setup_hotspot.sh
   CHANNEL="6"  # Try 1, 6, or 11
   ```
4. **Disable power saving**:
   ```bash
   sudo iw dev wlan0 set power_save off
   ```

---

### 8. Watchdog Timeout / Link Lost

**Symptom**: LCD shows "LINK LOST", motors stop frequently

**Possible Causes**:
- Network packet loss
- Controller app crashed
- Wi-Fi dropouts

**Diagnostic Steps**:

1. **Check controller is running**:
   - Should see status messages every second
   - If frozen, restart controller app

2. **Monitor packet loss**:
   ```bash
   ping -c 1000 10.42.0.123 | grep loss
   # Should be 0% loss
   ```

3. **Check watchdog timeout setting**:
   ```python
   # In firmware/config.py
   WATCHDOG_TIMEOUT_MS = 200  # Milliseconds
   ```
   - Too short: False alarms
   - Too long: Slow safety response

**Solutions**:

1. **Increase timeout if network unstable**:
   ```python
   WATCHDOG_TIMEOUT_MS = 500  # More lenient
   ```

2. **Improve network stability** (see issue #7)

3. **Verify controller packet rate**:
   ```python
   # In controller_xbox.py
   CONTROL_RATE_HZ = 30  # Should be 20-50 Hz
   ```

---

### 9. Motors Run Backward

**Symptom**: Forward command makes robot go backward

**Solution**: Swap motor wires

1. **Power off robot completely**
2. **Locate motor terminal blocks** on Pico-Go board
3. **Swap the two wires** for the problematic motor
4. **Test again**

Alternatively, fix in software:
```python
# In motor.py, in Motor.set_speed()
# Invert one motor:
if self.name == "Left Motor":
    speed = -speed  # Invert left motor
```

---

### 10. Robot Moves in Circles

**Symptom**: Robot doesn't go straight even with neutral steering

**Possible Causes**:
- Motor speed mismatch
- Mechanical friction difference
- Wheel slippage
- Dead zone too small

**Solutions**:

1. **Adjust motor calibration**:
   ```python
   # In motor.py
   class DifferentialDrive:
       def __init__(self):
           # ...
           self.left_trim = 1.0   # Speed multiplier
           self.right_trim = 0.95  # Slow down right motor
       
       def drive(self, throttle, steer):
           left_speed = clamp(throttle + steer, -1.0, 1.0) * self.left_trim
           right_speed = clamp(throttle - steer, -1.0, 1.0) * self.right_trim
   ```

2. **Increase dead zone**:
   ```python
   # In config.py
   DEAD_ZONE = 0.10  # Increase from 0.08
   ```

3. **Check mechanical issues**:
   - Ensure wheels spin freely
   - Check for debris in gearboxes
   - Verify both motors have same gear ratio

---

## 🔬 Advanced Debugging

### Enable Debug Output

```python
# In firmware/config.py
DEBUG_MODE = True

# Now you'll see detailed logs:
# [12345] WiFi: Attempting connection...
# [12500] Motor: Drive command: T=0.5, S=-0.2
# [12505] Watchdog: Fed at 12505
```

### Serial Monitoring

```bash
# Real-time serial output
mpremote connect /dev/ttyACM0

# Or with screen
screen /dev/ttyACM0 115200

# Exit screen: Ctrl+A, then K
```

### Network Packet Capture

```bash
# Capture packets between laptop and robot
sudo tcpdump -i wlan0 -w robot_packets.pcap host 10.42.0.123

# Analyze with Wireshark
wireshark robot_packets.pcap
```

### MicroPython Memory Debug

```python
# In REPL
import gc
gc.collect()
print(f"Free RAM: {gc.mem_free()} bytes")

# If low memory (<10KB), reduce allocations
```

---

## 🛠️ Recovery Procedures

### Factory Reset Firmware

```bash
# Re-flash MicroPython
# 1. Hold BOOTSEL button on Pico W
# 2. Connect USB (appears as mass storage)
# 3. Copy MicroPython .uf2 file to device
# 4. Re-upload all firmware files

cd firmware
mpremote connect /dev/ttyACM0 cp *.py :
mpremote reset
```

### Reset Network Settings

```bash
# Delete and recreate hotspot
sudo nmcli connection delete PicoLAN
sudo ./setup_hotspot.sh start
```

### Emergency Motor Stop

If robot is running away:

1. **Physical**: Cut power (disconnect battery)
2. **Software**: Press START on controller
3. **Network**: Turn off hotspot - watchdog will stop motors

---

## 📞 Getting Help

### Information to Collect

When asking for help, provide:

1. **Hardware**:
   - Waveshare Pico-Go version
   - MicroPython version: `import sys; print(sys.version)`
   - Battery voltage

2. **Software**:
   - Git commit hash: `git rev-parse --short HEAD`
   - Ubuntu version: `lsb_release -a`
   - Python version: `python3 --version`

3. **Error Details**:
   - Serial output from robot
   - Controller app output
   - Network diagnostics: `ping 10.42.0.123`

4. **Logs**:
   ```bash
   # Capture full session
   mpremote connect /dev/ttyACM0 | tee robot_log.txt
   ```

### Contact

- **GitHub Issues**: [Report a bug](https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot/issues)
- **Email**: robotics@stclaircollege.ca
- **Discord**: St. Clair Robotics Club (link in repo)

---

## 📚 Additional Resources

- [MicroPython Forum](https://forum.micropython.org/)
- [Raspberry Pi Pico W Documentation](https://www.raspberrypi.com/documentation/microcontrollers/)
- [Waveshare Wiki](https://www.waveshare.com/wiki/Pico-Go)
- [pygame Documentation](https://www.pygame.org/docs/)

---

## ✅ Known Limitations

1. **Range**: Wi-Fi limited to ~15-20m in open space
2. **Latency**: Minimum ~10ms due to Wi-Fi + processing
3. **Battery Life**: ~45-60 min with aggressive driving
4. **LCD Update Rate**: Limited to prevent SPI bus contention
5. **Single Client**: Only one controller can connect at a time

These are design constraints, not bugs. Future versions may address some limitations.
