#!/bin/bash
# Flash firmware to Pico W
# Usage: ./flash_firmware.sh [device]
# Example: ./flash_firmware.sh /dev/ttyACM0

DEVICE="${1:-/dev/ttyACM0}"

echo "=========================================="
echo "🤖 Pico-Go LAN Robot - Firmware Flash"
echo "=========================================="
echo ""
echo "Device: $DEVICE"
echo ""

# Check if device exists
if [ ! -e "$DEVICE" ]; then
    echo "❌ Error: Device $DEVICE not found"
    echo "   Please connect the Pico W via USB"
    exit 1
fi

echo "📦 Uploading firmware files..."
echo ""

cd firmware

# Upload all Python files
mpremote connect "$DEVICE" cp \
    calibration.py \
    charging_mode.py \
    config.py \
    events.py \
    lcd_status.py \
    main.py \
    motor.py \
    underglow.py \
    utils.py \
    watchdog.py \
    wifi.py \
    ws_server.py \
    :

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Firmware uploaded successfully!"
    echo ""
    echo "🔄 Resetting robot..."
    mpremote connect "$DEVICE" reset
    echo ""
    echo "✅ Robot reset - check LCD for boot sequence"
    echo ""
    echo "Expected sequence:"
    echo "  1. BOOT (purple LED flash)"
    echo "  2. NET_UP (blue LED, shows IP on LCD)"
    echo "  3. CLIENT_OK (robot color + orange LED flash when controller connects)"
    echo "  4. DRIVING (solid robot color LED, drive screen on LCD)"
else
    echo ""
    echo "❌ Upload failed - check connection and try again"
    exit 1
fi

