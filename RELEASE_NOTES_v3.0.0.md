# Release Notes - v3.0.0-prerelease

**Release Date**: 2025-01-10  
**Status**: Pre-release (Ready for Testing)

---

## 🎉 Major Features

### 8 Configurable Robot Profiles
- **THUNDER** (Orange) - High energy racing
- **BLITZ** (Cyan) - Fast and striking
- **NITRO** (Red) - Speed boost
- **TURBO** (Green) - Cool performance
- **SPEED** (Yellow) - Deep racing
- **BOLT** (Purple) - Electric energy
- **FLASH** (Pink) - Quick and bright
- **STORM** (Blue) - Powerful presence

Each profile includes unique name, color, and LCD graphics.

### Enhanced Controller UI
- **Modern pygame window** with visual feedback bars
- **Real-time throttle bar** (green forward, red reverse)
- **Real-time steering bar** (blue, centered)
- **Clean, professional design** with dark theme
- **No terminal display issues** - all visual feedback in window

### Calibration System
- **Fully restored** calibration.py (was empty/corrupt)
- **Integrated** into motor control (steering trim, motor balance)
- **Controller requests** calibration during connection
- **Discovery includes** calibration data
- **Calibration tool** available (calibrate.py)

### Event-Driven Architecture
- **New events.py** module for inter-module communication
- **Decoupled components** for better maintainability
- **Replaced global variables** with event system

---

## 🔧 Improvements

### Performance
- **Faster discovery** (1.5s timeout, broadcast-only)
- **Optimized UDP** communication
- **Reduced verbosity** in terminal output
- **Efficient connection** process

### Code Quality
- **Consolidated duplicate** packet handling code
- **Thread-safe** display updates
- **Better error handling** patterns
- **Improved code organization**

### User Experience
- **Suppressed pygame** community message
- **Concise terminal** output
- **Visual feedback** in pygame window
- **Better connection** status messages

---

## 🐛 Fixes

### Critical
- ✅ **Restored calibration.py** (was empty/corrupt file)
- ✅ **Fixed LED color** - CLIENT_OK now shows ORANGE (not GREEN)
- ✅ **Fixed TUI display** issues (reverted to pygame window)

### Minor
- ✅ Fixed discovery response to include calibration data
- ✅ Fixed motor calibration integration
- ✅ Fixed event system integration
- ✅ Improved terminal output formatting

---

## 📦 Files Changed

### New Files
- `firmware/calibration.py` - Calibration data management
- `firmware/events.py` - Event-driven architecture
- `controller/configure_robot.py` - Robot profile configuration tool

### Modified Files
- `firmware/config.py` - Added 8 robot profiles
- `firmware/ws_server.py` - Optimized, added calibration commands
- `firmware/motor.py` - Integrated calibration
- `firmware/underglow.py` - Fixed ORANGE color for CLIENT_OK
- `firmware/main.py` - Event system integration
- `controller/controller_xbox.py` - Enhanced pygame UI

---

## 🚀 Installation

### Firmware
```bash
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :
mpremote reset
```

### Controller
```bash
pip install -r controller/requirements.txt
python3 controller/controller_xbox.py
```

### Configure Robot Profile
```bash
python3 controller/configure_robot.py [robot_id] [robot_ip]
```

---

## ⚠️ Breaking Changes

None - This is a feature release with backward compatibility.

---

## 📝 Testing Checklist

- [x] Robot discovery works
- [x] Calibration system functional
- [x] LED colors correct (ORANGE for CLIENT_OK)
- [x] Controller UI displays correctly
- [x] Motor control with calibration
- [x] All 8 robot profiles configurable
- [x] UDP communication stable

---

## 🔜 Next Steps

1. Test with multiple robots (different profiles)
2. Verify calibration persistence
3. Test profile configuration tool
4. Performance testing under load

---

**Repository**: https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot  
**Tag**: v3.0.0  
**Author**: Jeremy Dueck  
**Organization**: St. Clair College Robotics Club

