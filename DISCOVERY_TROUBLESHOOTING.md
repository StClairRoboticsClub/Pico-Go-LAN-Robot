# Robot Discovery Troubleshooting Guide

## Problem: Robot Discovery Not Working on Laptop

### Symptoms
- Discovery sends broadcasts successfully
- No robots found via broadcast discovery
- Direct queries to known robot IPs work fine
- Same network settings as desktop (where it works)

### Root Cause
**Firewall blocking incoming UDP packets on port 8765**

The laptop can send UDP broadcasts, but cannot receive the robot responses because the firewall is blocking incoming UDP traffic on port 8765.

### Diagnosis

Run the troubleshooting tool:
```bash
cd controller
python3 troubleshoot_discovery.py
```

This will systematically test:
1. Network interface detection
2. Socket creation and binding
3. UDP broadcast sending
4. UDP receive capability
5. Firewall status
6. Full discovery test
7. Direct robot query test

### Solution

#### Option 1: Use the Firewall Fix Script (Recommended)
```bash
cd controller
./fix_firewall.sh
```

This script will:
- Detect your firewall system (UFW, firewalld, or iptables)
- Guide you through adding the necessary rules
- Test the configuration

#### Option 2: Manual Firewall Configuration

**For UFW (Ubuntu/Debian):**
```bash
sudo ufw allow 8765/udp
```

**For firewalld (Fedora/RHEL/CentOS):**
```bash
sudo firewall-cmd --permanent --add-port=8765/udp
sudo firewall-cmd --reload
```

**For iptables:**
```bash
sudo iptables -I INPUT -p udp --dport 8765 -j ACCEPT
```

To make iptables rules permanent on Ubuntu/Debian:
```bash
sudo apt-get install iptables-persistent
sudo netfilter-persistent save
```

#### Option 3: Workaround - Use Direct Queries

If you can't modify firewall settings, you can still use robots by:
1. Getting the robot IP from the robot's LCD screen
2. Using "Add Robot" in the GUI to manually add the IP
3. The direct query mechanism will work even if broadcast discovery doesn't

### Verification

After fixing the firewall, test discovery:
```bash
cd controller
python3 troubleshoot_discovery.py
```

Or run the GUI and click "Scan for Robots".

### Technical Details

**How Discovery Works:**
1. Application sends UDP broadcast packets to port 8765 on all local networks
2. Robots receive the broadcast and respond with their information
3. Application receives responses on the same socket
4. Robots are displayed in the GUI

**Why It Fails:**
- Outgoing UDP (sending broadcasts): ✅ Works
- Incoming UDP (receiving responses): ❌ Blocked by firewall

**Why Direct Queries Work:**
- Direct queries use a different mechanism that may not be blocked
- Or the firewall allows responses to established connections

### Additional Notes

- The discovery code has been improved to:
  - Bind to all interfaces (0.0.0.0) first for better broadcast reception
  - Provide clearer error messages when firewall is detected
  - Fall back to direct queries automatically for saved robots

- Port 8765 is used for robot communication
- Ports 8766-8769 are used for the discovery socket binding (local only)

