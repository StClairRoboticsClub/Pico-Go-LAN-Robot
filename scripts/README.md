# Scripts Directory

This directory contains utility scripts for system setup and maintenance.

## Available Scripts

### `setup_hotspot.sh`

**Purpose**: Create and manage Ubuntu Wi-Fi hotspot for robot communication.

**Usage**:
```bash
# Start hotspot
sudo ./setup_hotspot.sh start

# Stop hotspot
sudo ./setup_hotspot.sh stop

# Check status
./setup_hotspot.sh status

# Scan for connected devices
sudo ./setup_hotspot.sh scan

# Restart hotspot
sudo ./setup_hotspot.sh restart
```

**Configuration**:
Edit the script to change:
- `SSID` - Hotspot network name (must match `firmware/config.py`)
- `PASSWORD` - WPA2 password (must match `firmware/config.py`)
- `INTERFACE` - Wi-Fi interface (check with `ip link show`)
- `BAND` - 2.4 GHz (bg) or 5 GHz (a)
- `CHANNEL` - Wi-Fi channel (leave empty for auto)

**Requirements**:
- Ubuntu 22.04+ with NetworkManager
- Sudo privileges
- Wi-Fi adapter that supports AP mode

---

### `install_lcd_driver.sh`

**Purpose**: Install ST7789 LCD driver on Raspberry Pi Pico W.

**Usage**:
```bash
# Run script (requires Pico W connected via USB)
./install_lcd_driver.sh
```

**What it does**:
1. Checks for `mpremote` installation
2. Connects to Pico W on `/dev/ttyACM0`
3. Installs ST7789 driver via `mip` (MicroPython package manager)
4. Verifies installation
5. Resets Pico W

**Manual Installation** (if script fails):
```bash
mpremote connect /dev/ttyACM0 mip install st7789
mpremote connect /dev/ttyACM0 ls :lib/
mpremote reset
```

**Note**: The ST7789 driver may already be pre-installed on Waveshare Pico-Go boards.

---

## Adding New Scripts

When adding utility scripts:

1. **Use descriptive names**: `verb_noun.sh` (e.g., `backup_firmware.sh`)
2. **Add shebang**: `#!/bin/bash` at the top
3. **Make executable**: `chmod +x script_name.sh`
4. **Document in this README**: Add usage and description
5. **Add error handling**: Use `set -e` and check for dependencies
6. **Use colors for output**: See `setup_hotspot.sh` for examples

---

## Troubleshooting

### Permission Denied
```bash
chmod +x scripts/script_name.sh
```

### Hotspot Won't Start
1. Check interface name: `ip link show`
2. Update `INTERFACE` in `setup_hotspot.sh`
3. Ensure NetworkManager is running: `systemctl status NetworkManager`

### LCD Driver Install Fails
1. Verify Pico W connected: `ls /dev/ttyACM*`
2. Check `mpremote` installed: `pip install mpremote`
3. Try manual installation (see above)

---

For more information, see `/docs/QUICKSTART.md` and `/docs/NETWORKING.md`.
