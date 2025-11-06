# 🎯 Action Plan: Complete Spec Compliance

**Goal:** Close the gap between current implementation (85%) and full spec compliance (100%)

**Timeline:** 1-2 days of focused work

---

## 🔴 CRITICAL: LCD Integration (Priority 1)

**Estimated Time:** 2-3 hours  
**Status:** ❌ Not started  
**Impact:** HIGH - Most visible missing feature

### Step-by-Step Implementation

#### 1. Install ST7789 Driver (15 min)

```bash
# Connect Pico W via USB
cd /home/jeremy/Workspaces/Robotics_Club/SumoBotProject/Pico-Go-LAN-Robot

# Install driver
mpremote connect /dev/ttyACM0 mip install st7789

# Verify installation
mpremote connect /dev/ttyACM0 ls :lib/
```

**Expected output:** Should show `st7789.py` or similar

---

#### 2. Create LCD Driver Wrapper (1 hour)

**File:** `firmware/lcd_status.py`

**Replace TODO sections with:**

```python
# At top of file, add:
try:
    import st7789
    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False
    print("Warning: ST7789 driver not found")

# In __init__ method, replace TODO:
if LCD_AVAILABLE:
    self.display = st7789.ST7789(
        self.spi,
        LCD_WIDTH,
        LCD_HEIGHT,
        reset=self.rst,
        dc=self.dc,
        cs=self.cs,
        rotation=LCD_ROTATION
    )
    self.display.init()
    self.clear(COLOR_BLACK)
else:
    self.display = None

# Implement clear() method:
def clear(self, color=COLOR_BLACK):
    if self.display:
        self.display.fill(color)

# Implement draw_text() method:
def draw_text(self, text, x, y, color=COLOR_WHITE, size=2):
    if self.display:
        # Use st7789's text rendering
        self.display.text(text, x, y, color)
```

---

#### 3. Implement State Display Methods (1 hour)

**File:** `firmware/lcd_status.py`

Update `set_state()` method to actually draw on screen:

```python
def set_state(self, state, **kwargs):
    """Update display with current state."""
    if not self.display:
        return
    
    self.current_state = state
    self.clear(COLOR_BLACK)
    
    if state == STATE_BOOT:
        self._draw_boot_screen()
    
    elif state == STATE_NET_UP:
        self.ip_address = kwargs.get('ip', 'Unknown')
        self.rssi = kwargs.get('rssi', 0)
        self._draw_network_screen()
    
    elif state == STATE_CLIENT_OK:
        self._draw_connected_screen()
    
    elif state == STATE_DRIVING:
        throttle = kwargs.get('throttle', 0)
        steer = kwargs.get('steer', 0)
        self._draw_driving_screen(throttle, steer)
    
    elif state == STATE_LINK_LOST:
        self._draw_link_lost_screen()
    
    elif state == STATE_E_STOP:
        self._draw_estop_screen()

# Implement each screen:
def _draw_boot_screen(self):
    self.draw_text("PICO-GO", 60, 80, COLOR_CYAN, 3)
    self.draw_text("BOOTING...", 60, 140, COLOR_WHITE, 2)

def _draw_network_screen(self):
    self.draw_text("NETWORK", 70, 40, COLOR_GREEN, 2)
    self.draw_text(f"IP: {self.ip_address}", 10, 100, COLOR_WHITE, 1)
    self.draw_text(f"RSSI: {self.rssi} dBm", 10, 130, COLOR_YELLOW, 1)
    self.draw_text("Waiting for", 50, 180, COLOR_WHITE, 2)
    self.draw_text("Controller...", 40, 210, COLOR_WHITE, 2)

def _draw_driving_screen(self, throttle, steer):
    self.draw_text("DRIVING", 60, 20, COLOR_GREEN, 2)
    self.draw_text(f"Throttle: {throttle:.2f}", 20, 100, COLOR_WHITE, 2)
    self.draw_text(f"Steer: {steer:.2f}", 20, 140, COLOR_WHITE, 2)
    # Optional: Draw bars for visual feedback

def _draw_link_lost_screen(self):
    self.clear(COLOR_RED)
    self.draw_text("CONNECTION", 40, 80, COLOR_WHITE, 2)
    self.draw_text("LOST!", 80, 120, COLOR_WHITE, 3)
    self.draw_text("Motors Stopped", 30, 180, COLOR_YELLOW, 1)
```

---

#### 4. Test LCD Integration (30 min)

```bash
# Upload updated lcd_status.py
mpremote cp firmware/lcd_status.py :

# Reset Pico
mpremote reset

# Watch serial output
mpremote connect /dev/ttyACM0
```

**Test checklist:**
- [ ] LCD shows "BOOTING..." on startup
- [ ] IP address displays after Wi-Fi connects
- [ ] "DRIVING" screen shows throttle/steer values
- [ ] "CONNECTION LOST" appears on timeout
- [ ] Text is readable and properly positioned

---

## 🟡 MEDIUM: Telemetry Improvements (Priority 2)

**Estimated Time:** 1 hour  
**Status:** ⚠️ Partial  
**Impact:** MEDIUM - Improves operational feedback

### Enhance ACK Processing

**File:** `controller/controller_xbox.py`

Add background task to read robot acknowledgments:

```python
class RobotConnection:
    # ... existing code ...
    
    async def read_ack_loop(self):
        """Background task to read robot ACKs."""
        while self.connected:
            try:
                # Read line from robot
                data = await asyncio.wait_for(
                    self.reader.readline(),
                    timeout=1.0
                )
                
                if data:
                    ack = json.loads(data.decode())
                    
                    # Extract telemetry
                    state = ack.get('state', 'UNKNOWN')
                    rssi = ack.get('rssi', None)
                    
                    # Display (optional)
                    if rssi:
                        print(f"  Robot RSSI: {rssi} dBm", end='\r')
                    
            except asyncio.TimeoutError:
                pass  # Normal - no ACK yet
            except Exception as e:
                print(f"ACK read error: {e}")
                break
```

Then in main controller loop, start the task:

```python
# In main():
asyncio.create_task(robot.read_ack_loop())
```

---

## 🟢 LOW: Documentation & Polish (Priority 3)

**Estimated Time:** 2-3 hours  
**Status:** 🟡 Good but can improve  
**Impact:** LOW - Helpful but not critical

### Create Wiring Diagram

**Tool:** Fritzing (free) or hand-drawn

**Content to include:**
1. Pico W pinout
2. TB6612FNG motor driver connections
3. ST7789 LCD SPI wiring
4. Power distribution (7.4V → 5V regulator)
5. Motor connections
6. Battery input with protection

**Save to:** `schematics/wiring_diagram.png`

---

### Update README with LCD Status

**File:** `README.md`

Add section about LCD states:

```markdown
## 📺 LCD Status Display

The robot displays its current state on the built-in ST7789 LCD:

| State | Color | Display |
|-------|-------|---------|
| BOOT | Cyan | "BOOTING..." |
| NET_UP | Green | IP address + RSSI |
| CLIENT_OK | Green | "Controller Connected" |
| DRIVING | Green | Throttle & Steer values |
| LINK_LOST | Red | "CONNECTION LOST!" |
| E_STOP | Red | "EMERGENCY STOP" |

The display automatically updates in real-time during operation.
```

---

## 📅 Suggested Timeline

### Day 1 - LCD Integration
- **Morning (2 hours):** Install driver, update lcd_status.py
- **Afternoon (1 hour):** Test and debug display
- **Evening (30 min):** Verify all states display correctly

### Day 2 - Polish & Testing
- **Morning (1 hour):** Add ACK processing improvements
- **Afternoon (2 hours):** Create wiring diagram
- **Evening (1 hour):** Update documentation, final testing

---

## ✅ Success Criteria

You'll know you're done when:

1. ✅ LCD shows all 6 states correctly
2. ✅ IP address is visible on robot without serial connection
3. ✅ Throttle/steer values update in real-time on LCD
4. ✅ "LINK LOST" appears when controller disconnects
5. ✅ Controller displays robot RSSI
6. ✅ Wiring diagram exists in schematics/
7. ✅ README documents LCD states

**Result:** 100% spec compliance, production-ready robot! 🎉

---

## 🚀 Quick Start Command

Run this to begin LCD integration:

```bash
cd /home/jeremy/Workspaces/Robotics_Club/SumoBotProject/Pico-Go-LAN-Robot

# Install driver
mpremote connect /dev/ttyACM0 mip install st7789

# Edit lcd_status.py
code firmware/lcd_status.py

# Upload and test
mpremote cp firmware/lcd_status.py :
mpremote reset
mpremote connect /dev/ttyACM0  # Monitor output
```

---

## 💡 Pro Tips

1. **Test incrementally** - Get basic text rendering working before complex screens
2. **Use serial debug** - Keep `mpremote` connection open to see errors
3. **Start simple** - Just show "BOOT" first, then add other states
4. **Check examples** - Look at st7789 library examples for syntax
5. **Font sizes** - Start with size=2 for readability

---

## 🆘 If You Get Stuck

### LCD Not Displaying Anything
- Check SPI connections (SCK, MOSI, CS, DC, RST pins)
- Verify backlight is on (`bl.value(1)`)
- Try basic st7789 example code first
- Check 3.3V power to LCD

### Driver Import Fails
- Verify installation: `mpremote ls :lib/`
- Try manual download from Waveshare GitHub
- Check MicroPython version compatibility

### Text Not Visible
- Try different colors (white on black)
- Increase font size
- Check LCD rotation setting
- Verify coordinates are within 240×240

---

## 📊 Progress Tracking

Mark off as you complete:

- [ ] ST7789 driver installed
- [ ] lcd_status.py updated with driver integration
- [ ] BOOT state displays
- [ ] NET_UP state shows IP and RSSI
- [ ] DRIVING state shows throttle/steer
- [ ] LINK_LOST state appears on timeout
- [ ] E_STOP state displays
- [ ] ACK processing improved
- [ ] Wiring diagram created
- [ ] Documentation updated
- [ ] Full system test passed

---

**Once complete, your robot will match 100% of the original specifications! 🎯**
