#!/bin/bash
# Firewall Fix Script for Robot Discovery
# This script helps fix firewall issues preventing robot discovery

echo "=========================================="
echo "Robot Discovery Firewall Fix"
echo "=========================================="
echo ""
echo "This script will help configure your firewall to allow robot discovery."
echo "Robot discovery uses UDP port 8765 for communication."
echo ""

# Detect which firewall system is in use
if command -v ufw &> /dev/null; then
    echo "Detected: UFW (Uncomplicated Firewall)"
    echo ""
    echo "To allow robot discovery, run:"
    echo "  sudo ufw allow 8765/udp"
    echo ""
    read -p "Would you like to run this command now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw allow 8765/udp
        echo "✅ UFW rule added"
        echo ""
        echo "Current UFW status:"
        sudo ufw status | grep 8765 || echo "  (Rule may need to be verified)"
    fi
elif command -v firewall-cmd &> /dev/null; then
    echo "Detected: firewalld"
    echo ""
    echo "To allow robot discovery, run:"
    echo "  sudo firewall-cmd --permanent --add-port=8765/udp"
    echo "  sudo firewall-cmd --reload"
    echo ""
    read -p "Would you like to run these commands now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo firewall-cmd --permanent --add-port=8765/udp
        sudo firewall-cmd --reload
        echo "✅ firewalld rule added"
        echo ""
        echo "Current firewalld rules:"
        sudo firewall-cmd --list-ports | grep 8765 || echo "  (Rule may need to be verified)"
    fi
elif command -v iptables &> /dev/null; then
    echo "Detected: iptables"
    echo ""
    echo "To allow robot discovery, run:"
    echo "  sudo iptables -I INPUT -p udp --dport 8765 -j ACCEPT"
    echo ""
    echo "⚠️  Note: This is a temporary rule. To make it permanent, you need to"
    echo "    save your iptables rules (method depends on your distribution)."
    echo ""
    read -p "Would you like to add this rule now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo iptables -I INPUT -p udp --dport 8765 -j ACCEPT
        echo "✅ iptables rule added (temporary)"
        echo ""
        echo "To make it permanent on Ubuntu/Debian:"
        echo "  sudo apt-get install iptables-persistent"
        echo "  sudo netfilter-persistent save"
    fi
else
    echo "⚠️  No standard firewall tool detected."
    echo ""
    echo "Your system may be using:"
    echo "  - A different firewall (check system settings)"
    echo "  - No firewall (unlikely on modern Linux)"
    echo "  - A firewall managed by a desktop environment"
    echo ""
    echo "Manual steps:"
    echo "1. Open your system's firewall settings"
    echo "2. Allow UDP port 8765 (incoming and outgoing)"
    echo "3. Ensure UDP broadcasts are not blocked"
fi

echo ""
echo "=========================================="
echo "Testing Robot Discovery"
echo "=========================================="
echo ""
echo "After fixing the firewall, test discovery with:"
echo "  cd controller && python3 troubleshoot_discovery.py"
echo ""
echo "Or run the GUI and click 'Scan for Robots'"
echo ""

