"""
WiFi Diagnostic Test Script
Run this on the Pico to diagnose WiFi connection issues
"""

import network
import time

# Your credentials
SSID = "DevNet-2.4G"
PASSWORD = "DevPass**99"

def scan_networks():
    """Scan for available WiFi networks"""
    print("\n=== Scanning for WiFi Networks ===")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    networks = wlan.scan()
    print(f"Found {len(networks)} networks:")
    
    target_found = False
    for ssid, bssid, channel, rssi, security, hidden in networks:
        ssid_str = ssid.decode('utf-8')
        print(f"  {ssid_str:32s} | Channel {channel:2d} | RSSI {rssi:3d} dBm | Security {security}")
        if ssid_str == SSID:
            target_found = True
            print(f"  ^^^ TARGET NETWORK FOUND! ^^^")
    
    if not target_found:
        print(f"\n⚠️  WARNING: Target network '{SSID}' NOT FOUND!")
        print("   Check if:")
        print("   1. The SSID is spelled correctly (case-sensitive)")
        print("   2. The router is in range")
        print("   3. The 2.4GHz band is enabled on your router")
    
    return target_found

def test_connection():
    """Test WiFi connection"""
    print(f"\n=== Testing Connection to '{SSID}' ===")
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print(f"Connecting with password: {'*' * len(PASSWORD)}")
    wlan.connect(SSID, PASSWORD)
    
    # Wait for connection (max 20 seconds)
    timeout = 20
    print(f"Waiting up to {timeout} seconds...")
    
    for i in range(timeout * 2):
        if wlan.isconnected():
            print("\n✓ Connected successfully!")
            status = wlan.ifconfig()
            print(f"  IP Address:  {status[0]}")
            print(f"  Subnet Mask: {status[1]}")
            print(f"  Gateway:     {status[2]}")
            print(f"  DNS Server:  {status[3]}")
            
            # Get signal strength
            try:
                rssi = wlan.status('rssi')
                print(f"  Signal:      {rssi} dBm")
            except:
                print(f"  Signal:      Unknown")
            
            return True
        
        # Progress indicator
        if i % 2 == 0:
            print(".", end="")
        time.sleep(0.5)
    
    print("\n✗ Connection failed!")
    
    # Get status code
    status = wlan.status()
    status_messages = {
        0: "STAT_IDLE - No connection and no activity",
        1: "STAT_CONNECTING - Connecting in progress",
        2: "STAT_WRONG_PASSWORD - Failed due to incorrect password",
        3: "STAT_NO_AP_FOUND - Failed because no access point replied",
        4: "STAT_CONNECT_FAIL - Failed due to other problems",
        5: "STAT_GOT_IP - Connection successful"
    }
    
    msg = status_messages.get(status, f"Unknown status: {status}")
    print(f"  Status Code: {msg}")
    
    return False

def main():
    """Run all diagnostic tests"""
    print("=" * 60)
    print("WiFi Diagnostic Test")
    print("=" * 60)
    
    # Step 1: Scan for networks
    found = scan_networks()
    
    # Step 2: Test connection
    test_connection()
    
    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
