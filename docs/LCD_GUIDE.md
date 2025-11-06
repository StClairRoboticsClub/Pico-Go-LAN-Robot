# 📺 LCD Display Guide

## Overview

The Pico-Go Robot features a **240×240 ST7789 LCD display** that shows real-time robot status with **color-coded connection indicators**.

### Connection Status Colors

| Color | Status | Description |
|-------|--------|-------------|
| 🔴 **RED** | Disconnected | No controller connection or timeout (>200ms) |
| 🟡 **YELLOW** | Intermittent | Connection lag detected (100-200ms) |
| 🟢 **GREEN** | Connected | Good connection (<100ms between packets) |

---

## Quick Setup

### 1. Install ST7789 Driver

```bash
# Run the automated installation script
./install_lcd_driver.sh

# OR manually install:
mpremote connect /dev/ttyACM0 mip install st7789
mpremote connect /dev/ttyACM0 cp firmware/lcd_status.py :
mpremote connect /dev/ttyACM0 reset
```

### 2. Verify Installation

After reset, the LCD should display:
1. **Blue screen**: "PICO-GO ROBOT Booting..."
2. **Yellow screen**: "NETWORK CONNECTED" with IP address
3. **Green screen**: "CONTROLLER CONNECTED READY" (when controller connects)

---

## Display States

### 1. 🔵 BOOT (Blue Background)

**Shown:** During startup  
**Duration:** 2-5 seconds

```
    PICO-GO
     ROBOT
   Booting...
```

---

### 2. 🟡 NETWORK UP (Yellow Background)

**Shown:** After Wi-Fi connects, waiting for controller  
**Displays:**
- Network status
- **IP Address** (most important!)
- RSSI signal strength
- Waiting message

```
   NETWORK
  CONNECTED
  
IP:
10.42.0.123

RSSI: -45 dBm

 Waiting for
 controller...
```

**Why Yellow?** Not fully operational yet - waiting for controller.

---

### 3. 🟢 CONTROLLER CONNECTED (Green Background)

**Shown:** When controller first connects  
**Duration:** Brief transition state

```
 CONTROLLER
  CONNECTED
  
    READY
```

---

### 4. 🟢 DRIVING (Green/Yellow/Red Background)

**Shown:** During active control  
**Background Color:** Changes based on connection quality

**Green Version (Good Connection):**
```
    DRIVING
10.42.0.123

THR:  +0.65
[=====>    ]

STR:  -0.20
[  <=======]

PKT: 1234      LAT: 15ms
RSSI: -45
```

**Displays:**
- **Background**: Connection status (Red/Yellow/Green)
- **IP Address**: Top-left corner (small)
- **Throttle**: Value + bar graph
- **Steering**: Value + bar graph
- **PKT**: Total packets received
- **RSSI**: Wi-Fi signal strength
- **LAT**: Latency in milliseconds

**Bar Graph Key:**
- Center line = neutral (0.0)
- Right fill = positive values
- Left fill = negative values
- Bar length = magnitude

---

### 5. 🔴 CONNECTION LOST (Red Background)

**Shown:** When watchdog timeout occurs (>200ms no packets)

```
 CONNECTION
    LOST!
    
 Motors Stopped
 
Last THR: +0.45
Last STR: -0.10
10.42.0.123
```

**Action:** Robot stops automatically. Screen stays red until connection resumes.

---

### 6. 🔴 EMERGENCY STOP (Red Background)

**Shown:** When E-Stop command received

```
  EMERGENCY
    STOP!
    
 Reset Required
```

**Action:** Requires manual reset to recover.

---

## Debug Metrics Explained

### RSSI (Received Signal Strength Indicator)

**Range:** -30 dBm (excellent) to -80 dBm (poor)

| RSSI Value | Quality | Notes |
|------------|---------|-------|
| -30 to -50 | Excellent | Full speed operation |
| -50 to -60 | Good | Normal operation |
| -60 to -70 | Fair | May experience lag |
| -70 to -80 | Poor | Connection issues likely |
| Below -80 | Very Poor | Disconnects imminent |

### Latency (LAT)

**Target:** <20ms typical, <50ms acceptable

| Latency | Quality | Notes |
|---------|---------|-------|
| 0-20ms | Excellent | Real-time control |
| 20-50ms | Good | Slight delay noticeable |
| 50-100ms | Fair | Noticeable lag |
| 100-200ms | Poor | Difficult to control |
| >200ms | Timeout | Connection lost (red screen) |

### Packet Count (PKT)

- Increments with each received control packet
- Should increase smoothly at 30 Hz (30 per second)
- Useful for verifying data flow

---

## Troubleshooting

### LCD Stays Black

**Possible Causes:**
1. ST7789 driver not installed
2. Incorrect wiring
3. Backlight not powered

**Solutions:**
```bash
# Check driver installation
mpremote connect /dev/ttyACM0 fs ls :lib/
# Should show st7789.py or similar

# Reinstall driver
./install_lcd_driver.sh

# Check serial output for errors
mpremote connect /dev/ttyACM0
```

---

### Display Shows Garbled Text

**Possible Causes:**
1. Wrong rotation setting
2. SPI timing issue
3. Power supply problem

**Solutions:**
1. Check `LCD_ROTATION` in `firmware/config.py`
2. Try reducing SPI baudrate (in lcd_status.py)
3. Verify 3.3V supply is stable

---

### Colors Don't Change

**Possible Causes:**
1. Connection status not updating
2. Watchdog not running

**Check:**
```python
# In firmware/main.py
# Ensure watchdog task is running
asyncio.create_task(self._watchdog_task())
```

---

### Text Too Small/Large

**Modify:** `scale` parameter in `lcd_status.py`

```python
# Example: Make text larger
self._draw_text("DRIVING", 10, 10, COLOR_WHITE, scale=3)  # Larger
```

---

### IP Address Not Showing

**Possible Causes:**
1. Wi-Fi not connecting
2. IP not passed to LCD

**Check:**
```bash
# Monitor serial output
mpremote connect /dev/ttyACM0

# Look for:
# "LCD: NET_UP - IP: 10.42.0.xxx"
```

---

## Pin Configuration

**Default Waveshare Pico-Go v2 Pins:**

| Function | Pin | GPIO |
|----------|-----|------|
| SCK (Clock) | 24 | GP18 |
| MOSI (Data) | 25 | GP19 |
| DC (Data/Command) | 21 | GP16 |
| RST (Reset) | 26 | GP20 |
| CS (Chip Select) | 22 | GP17 |
| BL (Backlight) | 27 | GP21 |

**Configuration:** `firmware/config.py`

---

## Advanced Customization

### Change Colors

Edit `firmware/lcd_status.py`:

```python
# Custom color definitions (RGB565)
COLOR_MY_RED = 0xF800
COLOR_MY_GREEN = 0x07E0
COLOR_MY_BLUE = 0x001F

# Use in display methods
self.clear(COLOR_MY_BLUE)
```

### Add New Metrics

```python
# In LCDStatus class
def _show_driving(self, throttle, steer):
    # ... existing code ...
    
    # Add battery voltage display
    if self.battery_voltage:
        self._draw_text(f"BAT: {self.battery_voltage:.1f}V", 
                       140, 195, text_color, scale=1)
```

### Custom Screens

```python
def _show_custom_screen(self):
    """Your custom display screen."""
    self.clear(COLOR_CYAN)
    self._draw_text_centered("CUSTOM", 100, COLOR_WHITE, scale=3)
    # Add your content here
```

---

## Performance Notes

### Update Rate

- **Boot/Network screens:** Static (updated on state change)
- **Driving screen:** Updates with each packet (30 Hz)
- **Connection color:** Updates dynamically based on timing

### Memory Usage

- ST7789 driver: ~15KB
- Display buffer: Minimal (uses direct SPI writes)
- Text rendering: Built-in framebuffer

### CPU Impact

- Negligible during static screens
- ~5-10% during active driving display updates
- Does not affect control loop timing

---

## Feature Roadmap

### Completed ✅
- [x] Color-coded connection status
- [x] IP address display
- [x] Real-time throttle/steer
- [x] RSSI monitoring
- [x] Packet counter
- [x] Latency display
- [x] Bar graph visualizations

### Planned 🎯
- [ ] Battery voltage display
- [ ] Uptime counter
- [ ] Signal strength indicator (graphical)
- [ ] Animation effects on state changes
- [ ] Custom boot logo support
- [ ] Touch input (if hardware supports)

---

## Quick Reference Card

**What Each Color Means:**

```
┌─────────────────────────────────┐
│  🔴 RED = DISCONNECTED          │
│     No packets > 200ms          │
│     Motors automatically stop   │
├─────────────────────────────────┤
│  🟡 YELLOW = INTERMITTENT       │
│     Lag detected (100-200ms)    │
│     Connection unstable         │
├─────────────────────────────────┤
│  🟢 GREEN = CONNECTED           │
│     Good connection (<100ms)    │
│     Normal operation            │
└─────────────────────────────────┘
```

**During Operation:**

1. Check **background color** first → connection status
2. Check **IP address** if lost connection
3. Check **RSSI** if experiencing lag
4. Check **LAT** for network performance
5. Check **PKT** to verify data flow

---

## Support

### Test LCD Without Controller

```python
# Run on Pico W (serial connection)
import lcd_status

lcd = lcd_status.initialize()
lcd.test_display()  # Cycles through all screens
```

### Reset LCD

```python
# If display gets stuck
lcd = lcd_status.get_display()
lcd.clear(lcd_status.COLOR_BLACK)
lcd._show_boot()
```

### Enable Debug Output

```python
# In firmware/config.py
DEBUG_MODE = True  # Shows all LCD state changes in serial
```

---

**Remember:** The LCD is your robot's "face" - it tells you everything you need to know at a glance! 🤖✨
