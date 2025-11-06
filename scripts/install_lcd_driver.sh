#!/bin/bash
# LCD Driver Installation Script for Pico-Go Robot
# Installs ST7789 display driver on Raspberry Pi Pico W

set -e

echo "======================================"
echo "  Pico-Go Robot - LCD Driver Setup   "
echo "======================================"
echo ""

# Check if mpremote is installed
if ! command -v mpremote &> /dev/null; then
    echo "❌ Error: mpremote not found"
    echo "Install with: pip install mpremote"
    exit 1
fi

echo "✅ mpremote found"
echo ""

# Detect Pico W device
echo "🔍 Looking for Pico W..."
DEVICE=$(ls /dev/ttyACM* 2>/dev/null | head -n 1)

if [ -z "$DEVICE" ]; then
    echo "❌ Error: No Pico W found on /dev/ttyACM*"
    echo "Please connect your Pico W via USB"
    exit 1
fi

echo "✅ Found Pico W at: $DEVICE"
echo ""

# Install ST7789 driver
echo "📦 Installing ST7789 driver..."
mpremote connect $DEVICE mip install st7789

if [ $? -eq 0 ]; then
    echo "✅ ST7789 driver installed successfully!"
else
    echo "⚠️  Driver installation may have failed"
    echo "Trying alternative method..."
    
    # Alternative: install github version
    mpremote connect $DEVICE mip install github:russhughes/st7789py_mpy
fi

echo ""

# Verify installation
echo "🔍 Verifying installation..."
mpremote connect $DEVICE fs ls :lib/ | grep -i st7789

if [ $? -eq 0 ]; then
    echo "✅ Verification successful - driver is installed"
else
    echo "⚠️  Warning: Could not verify driver installation"
fi

echo ""

# Upload updated firmware
echo "📤 Uploading updated firmware files..."
cd "$(dirname "$0")/firmware"

mpremote connect $DEVICE cp lcd_status.py :
echo "  ✓ lcd_status.py"

mpremote connect $DEVICE cp config.py :
echo "  ✓ config.py"

mpremote connect $DEVICE cp main.py :
echo "  ✓ main.py"

echo ""
echo "======================================"
echo "  🎉 Installation Complete!          "
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Reset your Pico W: mpremote connect $DEVICE reset"
echo "2. Monitor output: mpremote connect $DEVICE"
echo "3. The LCD should show boot screen, then IP address"
echo ""
echo "Connection Status Colors:"
echo "  🔴 RED    = Disconnected"
echo "  🟡 YELLOW = Intermittent/Lag"
echo "  🟢 GREEN  = Connected & Good"
echo ""
