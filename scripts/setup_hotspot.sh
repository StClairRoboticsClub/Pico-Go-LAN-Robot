#!/bin/bash
################################################################################
# Pico-Go LAN Robot - Ubuntu Hotspot Setup Script
################################################################################
# Creates and configures a Wi-Fi hotspot on Ubuntu for robot communication.
#
# Author: Jeremy Dueck
# Organization: St. Clair College Robotics Club
# License: MIT
#
# Usage:
#   ./setup_hotspot.sh [start|stop|status]
################################################################################

set -e  # Exit on error

# Configuration
SSID="PicoLAN"
PASSWORD="pico1234"
INTERFACE="wlp8s0"  # WiFi interface (was wlp112s0)
BAND="bg"          # 2.4 GHz (bg) or 5 GHz (a)
CHANNEL=""         # Leave empty for auto

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_interface() {
    if ! ip link show "$INTERFACE" &> /dev/null; then
        print_error "Interface $INTERFACE not found"
        print_info "Available interfaces:"
        ip link show | grep -E "^[0-9]+: " | awk -F': ' '{print "  - " $2}'
        exit 1
    fi
}

################################################################################
# Hotspot Management Functions
################################################################################

start_hotspot() {
    print_header "Starting PicoLAN Hotspot"
    
    check_root
    check_interface
    
    # Check if hotspot already exists
    if nmcli connection show "$SSID" &> /dev/null; then
        print_warning "Hotspot '$SSID' already exists. Deleting old connection..."
        nmcli connection delete "$SSID" &> /dev/null || true
    fi
    
    # Create hotspot
    print_info "Creating hotspot: $SSID"
    print_info "Interface: $INTERFACE"
    print_info "Password: $PASSWORD"
    
    if [ -n "$CHANNEL" ]; then
        nmcli dev wifi hotspot ifname "$INTERFACE" ssid "$SSID" password "$PASSWORD" band "$BAND" channel "$CHANNEL"
    else
        nmcli dev wifi hotspot ifname "$INTERFACE" ssid "$SSID" password "$PASSWORD" band "$BAND"
    fi
    
    # Wait a moment for hotspot to initialize
    sleep 2
    
    # Get IP address
    IP_ADDR=$(ip -4 addr show "$INTERFACE" | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    
    if [ -n "$IP_ADDR" ]; then
        print_success "Hotspot started successfully!"
        echo ""
        print_info "Network Information:"
        echo "  SSID:     $SSID"
        echo "  Password: $PASSWORD"
        echo "  IP:       $IP_ADDR"
        echo "  Gateway:  $IP_ADDR"
        echo ""
        print_info "Robot should connect to this network"
        print_info "Expected robot IP range: ${IP_ADDR%.*}.x"
    else
        print_error "Hotspot created but no IP address assigned"
        exit 1
    fi
}

stop_hotspot() {
    print_header "Stopping PicoLAN Hotspot"
    
    check_root
    
    # Check if hotspot exists
    if ! nmcli connection show "$SSID" &> /dev/null; then
        print_warning "Hotspot '$SSID' not found"
        return 0
    fi
    
    # Delete hotspot connection
    print_info "Deleting hotspot connection..."
    nmcli connection delete "$SSID"
    
    print_success "Hotspot stopped"
}

show_status() {
    print_header "PicoLAN Hotspot Status"
    
    # Check if connection exists
    if nmcli connection show "$SSID" &> /dev/null; then
        # Check if it's active
        if nmcli connection show --active | grep -q "$SSID"; then
            print_success "Hotspot is ACTIVE"
            
            # Get details
            IP_ADDR=$(ip -4 addr show "$INTERFACE" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "N/A")
            
            echo ""
            echo "Network Details:"
            echo "  SSID:      $SSID"
            echo "  Interface: $INTERFACE"
            echo "  IP:        $IP_ADDR"
            
            # Show connected clients (if available)
            echo ""
            echo "Connected Devices:"
            if command -v arp-scan &> /dev/null; then
                sudo arp-scan --interface="$INTERFACE" --localnet 2>/dev/null | grep -v "Interface\|packets" || echo "  No devices detected"
            else
                print_info "Install arp-scan for device detection: sudo apt install arp-scan"
                # Alternative: show ARP table
                arp -n | grep "$INTERFACE" || echo "  No devices in ARP table"
            fi
        else
            print_warning "Hotspot exists but is NOT ACTIVE"
        fi
    else
        print_warning "Hotspot does NOT exist"
        echo ""
        print_info "Run './setup_hotspot.sh start' to create it"
    fi
}

scan_network() {
    print_header "Scanning for Robot on Network"
    
    # Get network info
    IP_ADDR=$(ip -4 addr show "$INTERFACE" 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "")
    
    if [ -z "$IP_ADDR" ]; then
        print_error "Hotspot not active or no IP address"
        exit 1
    fi
    
    NETWORK="${IP_ADDR%.*}.0/24"
    
    print_info "Scanning network: $NETWORK"
    print_info "This may take 10-20 seconds..."
    echo ""
    
    # Use nmap if available
    if command -v nmap &> /dev/null; then
        nmap -sn "$NETWORK" | grep -E "Nmap scan|Host is up" || print_warning "No devices found"
    else
        print_warning "nmap not installed. Install with: sudo apt install nmap"
        print_info "Using ping sweep instead (less reliable)..."
        
        for i in {1..254}; do
            IP="${IP_ADDR%.*}.$i"
            if ping -c 1 -W 1 "$IP" &> /dev/null; then
                echo "  ✅ $IP is up"
            fi
        done
    fi
}

################################################################################
# Main Menu
################################################################################

show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start   - Start the PicoLAN hotspot"
    echo "  stop    - Stop the PicoLAN hotspot"
    echo "  status  - Show hotspot status"
    echo "  scan    - Scan network for connected devices"
    echo "  help    - Show this help message"
    echo ""
    echo "Configuration:"
    echo "  SSID:      $SSID"
    echo "  Password:  $PASSWORD"
    echo "  Interface: $INTERFACE"
}

################################################################################
# Main Script
################################################################################

# If no argument provided, show status
if [ $# -eq 0 ]; then
    show_status
    exit 0
fi

# Process command
case "$1" in
    start)
        start_hotspot
        ;;
    stop)
        stop_hotspot
        ;;
    status)
        show_status
        ;;
    scan)
        scan_network
        ;;
    restart)
        stop_hotspot
        sleep 2
        start_hotspot
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
