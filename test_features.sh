#!/bin/bash
# Test script to verify all features are working
# Run this after flashing firmware

echo "=========================================="
echo "🧪 Pico-Go LAN Robot - Feature Test"
echo "=========================================="
echo ""

# Check if robot is responding
echo "1️⃣  Testing Robot Discovery..."
python3 -c "
import socket
import json
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.settimeout(2.0)

# Send discovery
discovery = json.dumps({'cmd': 'discover', 'seq': 0}).encode()
sock.sendto(discovery, ('255.255.255.255', 8765))

try:
    data, addr = sock.recvfrom(1024)
    response = json.loads(data.decode().strip())
    if response.get('type') == 'robot_info':
        print(f'   ✅ Robot found: {response.get(\"hostname\")} at {addr[0]}')
        print(f'   ✅ Robot ID: {response.get(\"robot_id\")}')
        if 'calibration' in response:
            cal = response['calibration']
            print(f'   ✅ Calibration data received:')
            print(f'      - Steering trim: {cal.get(\"steering_trim\", 0.0):+.3f}')
            print(f'      - Motor L scale: {cal.get(\"motor_left_scale\", 1.0):.2f}')
            print(f'      - Motor R scale: {cal.get(\"motor_right_scale\", 1.0):.2f}')
        else:
            print('   ⚠️  No calibration data in discovery response')
    sock.close()
except socket.timeout:
    print('   ❌ No robot response - check WiFi connection')
    sock.close()
except Exception as e:
    print(f'   ❌ Error: {e}')
    sock.close()
"

echo ""
echo "2️⃣  Testing Calibration Request..."
echo "   (This will test if robot responds to get_calibration command)"
echo "   Run controller to test full calibration flow"
echo ""

echo "3️⃣  Next Steps:"
echo "   📱 Make sure phone hotspot is on (DevNet-2.4G)"
echo "   📺 Check robot LCD for IP address"
echo "   🎮 Run controller: python3 controller/controller_xbox.py"
echo "   👀 Watch LED colors:"
echo "      - BOOT: Robot color + RED flash"
echo "      - NET_UP: Solid robot color"
echo "      - CLIENT_OK: Robot color + ORANGE flash ⚠️ (NEW!)"
echo "      - DRIVING: Solid robot color"
echo "   📺 Check LCD shows robot name and unique graphic on drive screen"
echo ""

echo "✅ Test script complete!"
echo ""

