#!/usr/bin/env python3
"""
Robot Discovery Troubleshooting Tool
====================================
Systematically tests each component of robot discovery to identify issues.
"""

import socket
import subprocess
import sys
import time
import json
import os
from typing import List, Dict, Optional

# Import discovery functions
try:
    from controller_xbox import (
        discover_robots_on_network,
        query_robot_directly,
        ROBOT_PORT,
        get_all_local_networks
    )
except ImportError:
    # If running from controller directory
    sys.path.insert(0, os.path.dirname(__file__))
    from controller_xbox import (
        discover_robots_on_network,
        query_robot_directly,
        ROBOT_PORT,
        get_all_local_networks
    )


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(name: str, status: str, details: str = ""):
    """Print a test result."""
    status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_symbol} {name}: {status}")
    if details:
        print(f"   {details}")


def test_network_interfaces() -> bool:
    """Test 1: Check network interface detection."""
    print_section("Test 1: Network Interface Detection")
    
    try:
        networks = get_all_local_networks()
        print_test("Network Detection", "PASS" if networks else "WARN", 
                   f"Found {len(networks)} network(s): {networks}")
        
        # Get primary IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
            print_test("Primary IP Detection", "PASS", f"Primary IP: {primary_ip}")
        except Exception as e:
            print_test("Primary IP Detection", "FAIL", f"Error: {e}")
            return False
        
        return True
    except Exception as e:
        print_test("Network Detection", "FAIL", f"Error: {e}")
        return False


def test_socket_creation() -> Optional[socket.socket]:
    """Test 2: Test socket creation and binding."""
    print_section("Test 2: Socket Creation and Binding")
    
    sock = None
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print_test("Socket Creation", "PASS", "UDP socket created")
        
        # Set broadcast option
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print_test("Broadcast Option", "PASS", "SO_BROADCAST enabled")
        
        # Set reuse address
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print_test("Reuse Address", "PASS", "SO_REUSEADDR enabled")
        
        # Get primary IP for binding
        primary_ip = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
        except:
            pass
        
        # Try binding
        bound = False
        bind_addresses = []
        if primary_ip:
            bind_addresses.append((primary_ip, 0))
        bind_addresses.append(('0.0.0.0', 0))
        
        for bind_addr, _ in bind_addresses:
            for port in [8766, 8767, 8768, 8769, 0]:
                try:
                    sock.bind((bind_addr, port))
                    actual_port = sock.getsockname()[1]
                    print_test("Socket Binding", "PASS", 
                              f"Bound to {bind_addr}:{actual_port}")
                    bound = True
                    break
                except OSError as e:
                    continue
            if bound:
                break
        
        if not bound:
            print_test("Socket Binding", "FAIL", "Could not bind socket to any address/port")
            sock.close()
            return None
        
        return sock
        
    except Exception as e:
        print_test("Socket Creation", "FAIL", f"Error: {e}")
        if sock:
            try:
                sock.close()
            except:
                pass
        return None


def test_broadcast_sending(sock: socket.socket) -> bool:
    """Test 3: Test sending UDP broadcasts."""
    print_section("Test 3: UDP Broadcast Sending")
    
    try:
        networks = get_all_local_networks()
        if not networks:
            networks = ['192.168.1', '192.168.0', '10.0.0']
        
        discovery_msg = json.dumps({"cmd": "discover", "seq": 0}).encode()
        broadcasts_sent = 0
        
        for network_prefix in networks[:3]:  # Test first 3 networks
            broadcast_addr = f"{network_prefix}.255"
            try:
                sock.sendto(discovery_msg, (broadcast_addr, ROBOT_PORT))
                broadcasts_sent += 1
                print_test(f"Send to {broadcast_addr}", "PASS", 
                          f"Sent {len(discovery_msg)} bytes")
            except OSError as e:
                print_test(f"Send to {broadcast_addr}", "FAIL", f"Error: {e}")
            except Exception as e:
                print_test(f"Send to {broadcast_addr}", "FAIL", f"Error: {e}")
        
        # Test global broadcast
        try:
            sock.sendto(discovery_msg, ('255.255.255.255', ROBOT_PORT))
            broadcasts_sent += 1
            print_test("Send to 255.255.255.255", "PASS", "Global broadcast sent")
        except Exception as e:
            print_test("Send to 255.255.255.255", "WARN", f"Error: {e} (may be normal)")
        
        if broadcasts_sent == 0:
            print_test("Broadcast Sending", "FAIL", "No broadcasts sent successfully")
            return False
        
        print_test("Broadcast Sending", "PASS", f"Successfully sent {broadcasts_sent} broadcast(s)")
        return True
        
    except Exception as e:
        print_test("Broadcast Sending", "FAIL", f"Error: {e}")
        return False


def test_receive_capability(sock: socket.socket) -> bool:
    """Test 4: Test receiving UDP packets."""
    print_section("Test 4: UDP Receive Capability")
    
    try:
        # Set a short timeout
        sock.settimeout(2.0)
        
        print("   Listening for responses (2 seconds)...")
        print("   (This will timeout if no robots respond, which is expected)")
        
        start_time = time.time()
        received_any = False
        
        while time.time() - start_time < 2.0:
            try:
                data, addr = sock.recvfrom(1024)
                received_any = True
                print_test(f"Received from {addr[0]}", "PASS", 
                          f"{len(data)} bytes received")
                
                # Try to decode
                try:
                    response = json.loads(data.decode('utf-8'))
                    print_test("Response Decode", "PASS", 
                              f"Type: {response.get('type', 'unknown')}")
                except:
                    print_test("Response Decode", "WARN", 
                              "Could not decode as JSON (may be normal)")
                    
            except socket.timeout:
                # Expected if no robots
                break
            except Exception as e:
                print_test("Receive Error", "WARN", f"Error: {e}")
                break
        
        if received_any:
            print_test("UDP Receive", "PASS", "Successfully received UDP packets")
        else:
            print_test("UDP Receive", "WARN", 
                      "No packets received (may indicate firewall blocking or no robots)")
        
        return True
        
    except Exception as e:
        print_test("UDP Receive", "FAIL", f"Error: {e}")
        return False


def test_firewall_status() -> bool:
    """Test 5: Check firewall status."""
    print_section("Test 5: Firewall Status Check")
    
    # Check if firewall is active (Linux)
    if sys.platform == "linux":
        try:
            # Check ufw status
            result = subprocess.run(['ufw', 'status'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                status = result.stdout.strip()
                if 'Status: active' in status:
                    print_test("UFW Firewall", "WARN", 
                              "UFW is ACTIVE - may block UDP broadcasts")
                    print("   💡 Try: sudo ufw allow 8765/udp")
                else:
                    print_test("UFW Firewall", "PASS", "UFW is inactive")
            else:
                print_test("UFW Firewall", "INFO", "UFW not installed or not accessible")
        except FileNotFoundError:
            print_test("UFW Firewall", "INFO", "UFW not installed")
        except Exception as e:
            print_test("UFW Firewall", "WARN", f"Could not check: {e}")
        
        # Check iptables (basic check)
        try:
            result = subprocess.run(['iptables', '-L', '-n'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                rules = result.stdout
                if 'REJECT' in rules or 'DROP' in rules:
                    print_test("iptables", "WARN", 
                              "iptables has rules - may block UDP")
                else:
                    print_test("iptables", "PASS", "No blocking rules detected")
        except FileNotFoundError:
            print_test("iptables", "INFO", "iptables not accessible (may need sudo)")
        except Exception as e:
            print_test("iptables", "WARN", f"Could not check: {e}")
    
    return True


def test_full_discovery() -> bool:
    """Test 6: Full discovery test."""
    print_section("Test 6: Full Discovery Test")
    
    try:
        print("   Running full discovery (5 second timeout)...")
        robots = discover_robots_on_network(timeout=5.0, debug=True)
        
        if robots:
            print_test("Robot Discovery", "PASS", 
                      f"Found {len(robots)} robot(s)")
            for robot in robots:
                print(f"   - Robot #{robot['robot_id']} ({robot['hostname']}) at {robot['ip']}")
            return True
        else:
            print_test("Robot Discovery", "FAIL", "No robots found")
            return False
            
    except Exception as e:
        print_test("Robot Discovery", "FAIL", f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_query() -> bool:
    """Test 7: Test direct query to a known IP."""
    print_section("Test 7: Direct Robot Query")
    
    # Try to get saved robots from config
    try:
        from robot_config import RobotConfig
        config = RobotConfig()
        saved_robots = config.get_robots()
        
        if saved_robots:
            print(f"   Found {len(saved_robots)} saved robot(s) in config")
            for robot in saved_robots:
                ip = robot.get('ip')
                if ip:
                    print(f"   Testing direct query to {ip}...")
                    try:
                        robot_info = query_robot_directly(ip, timeout=2.0, debug=True)
                        if robot_info:
                            print_test(f"Direct Query to {ip}", "PASS", 
                                      f"Robot #{robot_info['robot_id']} responded")
                            return True
                        else:
                            print_test(f"Direct Query to {ip}", "FAIL", 
                                      "No response")
                    except Exception as e:
                        print_test(f"Direct Query to {ip}", "FAIL", f"Error: {e}")
        else:
            print("   No saved robots in config to test")
    except ImportError:
        print("   Could not import robot_config (skipping direct query test)")
    except Exception as e:
        print(f"   Error checking saved robots: {e}")
    
    return False


def main():
    """Run all troubleshooting tests."""
    print("\n" + "=" * 70)
    print("  Robot Discovery Troubleshooting Tool")
    print("=" * 70)
    print("\nThis tool will systematically test each component of robot discovery.")
    print("Press Ctrl+C to cancel at any time.\n")
    
    results = {}
    
    # Test 1: Network interfaces
    results['network'] = test_network_interfaces()
    
    # Test 2: Socket creation
    sock = test_socket_creation()
    results['socket'] = sock is not None
    
    if sock:
        # Test 3: Broadcast sending
        results['broadcast'] = test_broadcast_sending(sock)
        
        # Test 4: Receive capability
        results['receive'] = test_receive_capability(sock)
        
        # Clean up
        try:
            sock.close()
        except:
            pass
    else:
        results['broadcast'] = False
        results['receive'] = False
    
    # Test 5: Firewall
    test_firewall_status()
    
    # Test 6: Full discovery
    results['discovery'] = test_full_discovery()
    
    # Test 7: Direct query
    test_direct_query()
    
    # Summary
    print_section("Summary")
    
    all_passed = all(results.values())
    
    print("\nTest Results:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.upper():15} {status}")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✅ All basic tests passed!")
        print("   If robots still not found, check:")
        print("   - Robots are powered on and connected to WiFi")
        print("   - Robots are on the same network as this computer")
        print("   - Robot firmware is running and listening on UDP port 8765")
    else:
        print("❌ Some tests failed. Common fixes:")
        print("\n1. Firewall Issues:")
        print("   - Linux (UFW): sudo ufw allow 8765/udp")
        print("   - Linux (iptables): sudo iptables -I INPUT -p udp --dport 8765 -j ACCEPT")
        print("   - Check system firewall settings")
        print("\n2. Network Issues:")
        print("   - Ensure you're on the same WiFi network as robots")
        print("   - Check network interface is active")
        print("   - Try disabling VPN if active")
        print("\n3. Socket Binding Issues:")
        print("   - Check if port 8766-8769 are in use: netstat -an | grep 876")
        print("   - Try running with sudo (if permission issues)")
        print("\n4. Manual Robot Addition:")
        print("   - Use 'Add Robot' in GUI to manually enter robot IP")
        print("   - Check robot's LCD screen for IP address")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Troubleshooting cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

