# Hardware Guide - Pico-Go LAN Robot

## 📋 Bill of Materials (BOM)

| Component | Part Number/Model | Quantity | Estimated Cost |
|-----------|-------------------|----------|----------------|
| Raspberry Pi Pico W | RP2040 + CYW43439 | 1 | $6 USD |
| Waveshare Pico-Go Platform | Pico-Go v2 | 1 | $25 USD |
| TT Gear Motors (included) | 6V DC | 2 | Included |
| ST7789 LCD (included) | 240×240, 1.3" | 1 | Included |
| TB6612FNG Motor Driver (included) | Dual H-bridge | 1 | Included |
| Li-ion Battery | 7.4V 2S 1000mAh+ | 1 | $15 USD |
| Xbox Controller | Wired or Bluetooth | 1 | $30-60 USD |
| Ubuntu Laptop | 22.04+ with Wi-Fi | 1 | Existing |

**Total Estimated Cost**: ~$75-100 USD (excluding laptop)

---

## 🔌 Electrical Connections

### Motor Driver (TB6612FNG) → Pico W

| TB6612FNG Pin | Pico W GPIO | Function |
|---------------|-------------|----------|
| PWMA | GP0 | Motor A PWM speed |
| AIN1 | GP1 | Motor A direction 1 |
| AIN2 | GP2 | Motor A direction 2 |
| PWMB | GP3 | Motor B PWM speed |
| BIN1 | GP4 | Motor B direction 1 |
| BIN2 | GP5 | Motor B direction 2 |
| STBY | GP6 | Standby (HIGH = enabled) |
| VM | 7.4V Battery | Motor voltage |
| VCC | 5V | Logic voltage |
| GND | GND | Common ground |

### LCD (ST7789) → Pico W

| LCD Pin | Pico W GPIO | Function |
|---------|-------------|----------|
| SCK | GP18 | SPI Clock |
| MOSI | GP19 | SPI Data Out |
| DC | GP16 | Data/Command select |
| RST | GP20 | Reset |
| CS | GP17 | Chip Select |
| BL | GP21 | Backlight control |
| VCC | 3.3V | Power |
| GND | GND | Ground |

### Power Distribution

```
7.4V Li-ion Battery
    │
    ├─► 5V Regulator (LM2596 or similar, ≥2A)
    │       │
    │       ├─► Pico W VSYS (5V)
    │       ├─► Motor Driver VCC (5V logic)
    │       └─► 3.3V Regulator → LCD (optional, Pico provides 3.3V)
    │
    └─► Motor Driver VM (7.4V direct)
            │
            └─► Motors (M1, M2)
```

---

## ⚡ Power Specifications

### Current Draw Budget

| Component | Idle | Typical | Peak |
|-----------|------|---------|------|
| Pico W MCU | 50 mA | 100 mA | 300 mA (Wi-Fi TX) |
| LCD Backlight | 5 mA | 25 mA | 50 mA |
| Motor Driver Logic | 5 mA | 20 mA | 50 mA |
| Motor A | 0 mA | 300 mA | 1.5 A (stall) |
| Motor B | 0 mA | 300 mA | 1.5 A (stall) |
| **Total System** | **60 mA** | **745 mA** | **3.4 A** |

### Battery Sizing

- **Minimum**: 1000 mAh @ 7.4V (30-45 min runtime)
- **Recommended**: 2000 mAh @ 7.4V (60-90 min runtime)
- **Chemistry**: Li-ion 2S with protection circuit

### Voltage Requirements

- **Motors**: 6-7.4V nominal (VM on TB6612FNG)
- **Logic**: 5V for Pico W and motor driver
- **LCD**: 3.3V (provided by Pico W 3V3 pin)

---

## 🔧 Assembly Instructions

### Step 1: Install Pico W on Waveshare Platform

1. Align Pico W with 40-pin header on Pico-Go board
2. Press firmly to seat all pins
3. Verify no pins are bent or misaligned

### Step 2: Connect Motors

Motors should be pre-wired on Waveshare Pico-Go platform.

- **Motor A (Left)**: Connected to TB6612FNG output A
- **Motor B (Right)**: Connected to TB6612FNG output B

**Polarity Check**: Run test sequence to verify forward direction. If motors run backward, swap motor wires at terminal block.

### Step 3: LCD Installation

LCD should be pre-installed on Waveshare Pico-Go.

- Verify SPI connections match pinout above
- Check for proper seating in connector

### Step 4: Power Wiring

1. **DO NOT connect battery yet**
2. Install 5V regulator (if not included):
   - Input: 7.4V battery terminals
   - Output: 5V rail on board
   - Add 470 µF capacitor across 5V output
3. Add 100 nF ceramic capacitor near each motor terminal (noise suppression)

### Step 5: Safety Checks

Before powering on:

- [ ] Verify no shorts between VCC and GND
- [ ] Check polarity of battery connection
- [ ] Ensure all GPIO pins properly seated
- [ ] Confirm no loose wires
- [ ] Test with USB power before battery

---

## 🧪 Hardware Testing

### Test 1: Power-On Self Test

```python
# Connect via USB, run in REPL
import machine
import time

# Test LED (on Pico W)
led = machine.Pin("LED", machine.Pin.OUT)
for _ in range(5):
    led.toggle()
    time.sleep(0.5)

print("LED test passed!")
```

### Test 2: Motor Driver Test

```python
from machine import Pin, PWM

# Enable motor driver
stby = Pin(6, Pin.OUT)
stby.value(1)

# Test Motor A
pwm_a = PWM(Pin(0))
pwm_a.freq(20000)
in1 = Pin(1, Pin.OUT)
in2 = Pin(2, Pin.OUT)

# Forward at 50%
in1.value(1)
in2.value(0)
pwm_a.duty_u16(32768)

# Wait 1 second
time.sleep(1)

# Stop
pwm_a.duty_u16(0)
stby.value(0)

print("Motor test complete!")
```

### Test 3: LCD Test

```python
from machine import Pin, SPI

# Initialize SPI
spi = SPI(0, baudrate=40000000, sck=Pin(18), mosi=Pin(19))

# Toggle backlight
bl = Pin(21, Pin.OUT)
for _ in range(5):
    bl.toggle()
    time.sleep(0.5)

print("LCD backlight test passed!")
```

---

## 🛡️ Safety Considerations

### Electrical Safety

1. **Reverse Polarity Protection**: Add diode (1N5819) in series with battery positive
2. **Fuse**: 2A fast-blow fuse on battery positive lead
3. **Capacitors**: 
   - 470 µF electrolytic across 5V rail
   - 100 nF ceramic at motor terminals
   - 10 µF ceramic near Pico W VCC

### Mechanical Safety

1. **Secure all connections** with heat shrink or tape
2. **Mount battery** securely to prevent shifting
3. **Cable management** - prevent wires from contacting wheels
4. **Emergency access** - ensure easy battery disconnect

### Operational Safety

1. **Test on blocks** before ground testing
2. **Power switch** easily accessible
3. **Physical E-stop** optional but recommended
4. **Eye protection** during motor testing

---

## 🔍 Troubleshooting Hardware Issues

| Symptom | Possible Cause | Solution |
|---------|----------------|----------|
| No power LED | No 5V supply | Check regulator, battery voltage |
| Pico boots but no LCD | Loose SPI connection | Reseat LCD connector, check wiring |
| Motors don't spin | STBY pin low | Ensure GP6 set HIGH in code |
| Motors twitch | Insufficient current | Check regulator rating (≥2A) |
| Intermittent resets | Voltage drop | Add bulk capacitor (470 µF) |
| Wi-Fi not working | Wrong Pico model | Verify using Pico **W** not regular Pico |
| LCD stays white | No initialization | Flash correct st7789 driver |

---

## 🔧 Modifications & Upgrades

### Optional Sensors

**Ultrasonic Distance Sensor (HC-SR04)**
- Trig: GP10
- Echo: GP11
- VCC: 5V, GND: GND

**Line Following Sensors**
- Analog: GP26 (ADC0), GP27 (ADC1), GP28 (ADC2)

**IMU (MPU6050)**
- I2C: GP4 (SDA), GP5 (SCL)
- Note: Conflicts with motor pins - reassign motors if using I2C

### Power Upgrades

**Higher Capacity Battery**
- Use 2200-3000 mAh for extended runtime
- Ensure C-rating adequate for motor draw (≥10C)

**Buck-Boost Regulator**
- Maintains 5V even as battery voltage drops
- Recommended: Pololu D24V10F5 or similar

---

## 📐 Mechanical Specifications

| Parameter | Value |
|-----------|-------|
| Chassis Dimensions | ~100 × 80 × 40 mm |
| Wheel Diameter | ~42 mm |
| Wheelbase | ~70 mm |
| Ground Clearance | ~5 mm |
| Weight (no battery) | ~80 g |
| Weight (with battery) | ~130 g |

---

## 📦 Maintenance

### Regular Checks

- **Weekly**: Check battery charge, verify all connections tight
- **Monthly**: Clean motor commutators, inspect wheels for wear
- **Quarterly**: Re-flash firmware with updates, recalibrate sensors

### Battery Care

- Store at 3.7V per cell (storage charge) when not in use
- Never discharge below 3.0V per cell
- Use proper Li-ion charger with cell balancing
- Inspect for physical damage before each use

---

## 🔗 Resources

- [TB6612FNG Datasheet](https://www.sparkfun.com/datasheets/Robotics/TB6612FNG.pdf)
- [Pico W Pinout](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
- [ST7789 Datasheet](https://www.waveshare.com/w/upload/a/ae/ST7789_Datasheet.pdf)
- [Li-ion Safety Guide](https://www.sparkfun.com/tutorials/241)
