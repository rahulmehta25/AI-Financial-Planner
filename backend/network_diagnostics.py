#!/usr/bin/env python3
"""
Network Diagnostics for WebSocket Testing
=========================================

Network diagnostic tools to troubleshoot WebSocket connectivity issues.
"""

import subprocess
import socket
import time
import json
import requests
from urllib.parse import urlparse
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkDiagnostics:
    """Network diagnostic utilities"""
    
    def __init__(self, target_url: str = "ws://localhost:8000/ws"):
        self.target_url = target_url
        parsed = urlparse(target_url)
        self.host = parsed.hostname or 'localhost'
        self.port = parsed.port or 8000
        self.http_url = f"http://{self.host}:{self.port}"
    
    def test_basic_connectivity(self) -> Dict[str, Any]:
        """Test basic TCP connectivity"""
        logger.info(f"Testing TCP connectivity to {self.host}:{self.port}")
        
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            result = sock.connect_ex((self.host, self.port))
            connect_time = (time.time() - start_time) * 1000
            sock.close()
            
            if result == 0:
                return {
                    "success": True,
                    "message": f"TCP connection successful",
                    "connect_time_ms": connect_time
                }
            else:
                return {
                    "success": False,
                    "message": f"TCP connection failed (error {result})",
                    "connect_time_ms": connect_time
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}"
            }
    
    def test_http_endpoint(self) -> Dict[str, Any]:
        """Test HTTP endpoint availability"""
        logger.info(f"Testing HTTP endpoint at {self.http_url}")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.http_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "headers": dict(response.headers),
                "message": f"HTTP {response.status_code} - {response.reason}"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "HTTP connection refused - server may not be running"
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "HTTP request timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"HTTP error: {str(e)}"
            }
    
    def test_websocket_handshake(self) -> Dict[str, Any]:
        """Test WebSocket handshake"""
        logger.info("Testing WebSocket handshake")
        
        try:
            # Manual WebSocket handshake test
            import base64
            import hashlib
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            start_time = time.time()
            sock.connect((self.host, self.port))
            
            # Generate WebSocket key
            key = base64.b64encode(b"test_key_1234567890").decode()
            
            # Send WebSocket handshake request
            request = (
                f"GET /ws HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                f"Upgrade: websocket\r\n"
                f"Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                f"Sec-WebSocket-Version: 13\r\n"
                f"\r\n"
            ).encode()
            
            sock.send(request)
            
            # Read response
            response = sock.recv(1024).decode()
            handshake_time = (time.time() - start_time) * 1000
            
            sock.close()
            
            if "101 Switching Protocols" in response:
                return {
                    "success": True,
                    "message": "WebSocket handshake successful",
                    "handshake_time_ms": handshake_time,
                    "response_headers": response
                }
            else:
                return {
                    "success": False,
                    "message": "WebSocket handshake failed",
                    "response": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"WebSocket handshake error: {str(e)}"
            }
    
    def ping_test(self, count: int = 4) -> Dict[str, Any]:
        """Ping test to check network latency"""
        if self.host == "localhost" or self.host == "127.0.0.1":
            return {
                "success": True,
                "message": "Skipping ping for localhost",
                "avg_latency_ms": 0.1
            }
        
        logger.info(f"Pinging {self.host}")
        
        try:
            # Run ping command
            cmd = ["ping", "-c", str(count), self.host]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse ping results
                lines = result.stdout.split('\n')
                for line in lines:
                    if "avg" in line and "ms" in line:
                        # Extract average latency
                        parts = line.split('/')
                        if len(parts) >= 4:
                            avg_latency = float(parts[4])
                            return {
                                "success": True,
                                "message": f"Ping successful, avg latency: {avg_latency}ms",
                                "avg_latency_ms": avg_latency,
                                "output": result.stdout
                            }
                
                return {
                    "success": True,
                    "message": "Ping successful",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "message": "Ping failed",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Ping timed out"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ping error: {str(e)}"
            }
    
    def port_scan(self) -> Dict[str, Any]:
        """Scan common ports around the target port"""
        logger.info(f"Scanning ports around {self.port}")
        
        ports_to_check = [
            self.port - 1,
            self.port,
            self.port + 1,
            8000, 8080, 8888, 3000, 5000  # Common development ports
        ]
        
        open_ports = []
        closed_ports = []
        
        for port in set(ports_to_check):  # Remove duplicates
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                result = sock.connect_ex((self.host, port))
                sock.close()
                
                if result == 0:
                    open_ports.append(port)
                else:
                    closed_ports.append(port)
                    
            except Exception:
                closed_ports.append(port)
        
        return {
            "success": len(open_ports) > 0,
            "open_ports": sorted(open_ports),
            "closed_ports": sorted(closed_ports),
            "message": f"Found {len(open_ports)} open ports: {open_ports}"
        }
    
    def dns_lookup(self) -> Dict[str, Any]:
        """DNS lookup for hostname"""
        if self.host in ["localhost", "127.0.0.1"]:
            return {
                "success": True,
                "message": "Localhost - no DNS lookup needed",
                "ip_address": "127.0.0.1"
            }
        
        logger.info(f"DNS lookup for {self.host}")
        
        try:
            ip_address = socket.gethostbyname(self.host)
            return {
                "success": True,
                "message": f"DNS lookup successful",
                "hostname": self.host,
                "ip_address": ip_address
            }
        except socket.gaierror as e:
            return {
                "success": False,
                "message": f"DNS lookup failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"DNS error: {str(e)}"
            }
    
    def run_all_diagnostics(self) -> Dict[str, Any]:
        """Run all diagnostic tests"""
        logger.info("Running complete network diagnostics...")
        
        results = {
            "target_url": self.target_url,
            "host": self.host,
            "port": self.port,
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Run all tests
        test_functions = [
            ("dns_lookup", self.dns_lookup),
            ("ping_test", self.ping_test),
            ("tcp_connectivity", self.test_basic_connectivity),
            ("http_endpoint", self.test_http_endpoint),
            ("websocket_handshake", self.test_websocket_handshake),
            ("port_scan", self.port_scan)
        ]
        
        for test_name, test_func in test_functions:
            logger.info(f"Running {test_name}...")
            try:
                results["tests"][test_name] = test_func()
            except Exception as e:
                results["tests"][test_name] = {
                    "success": False,
                    "message": f"Test failed with exception: {str(e)}"
                }
        
        # Calculate summary
        total_tests = len(results["tests"])
        passed_tests = sum(1 for result in results["tests"].values() if result.get("success", False))
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        return results
    
    def print_diagnostic_report(self, results: Dict[str, Any]):
        """Print formatted diagnostic report"""
        print("\n" + "=" * 70)
        print("NETWORK DIAGNOSTIC REPORT")
        print("=" * 70)
        
        print(f"\nTarget: {results['target_url']}")
        print(f"Host:   {results['host']}")
        print(f"Port:   {results['port']}")
        
        print(f"\nSUMMARY:")
        summary = results["summary"]
        print(f"  Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\nTEST RESULTS:")
        for test_name, result in results["tests"].items():
            status = "✓ PASS" if result.get("success", False) else "✗ FAIL"
            message = result.get("message", "No message")
            print(f"  {test_name:20} {status:8} {message}")
        
        print(f"\nDETAILED RESULTS:")
        for test_name, result in results["tests"].items():
            print(f"\n{test_name.upper()}:")
            for key, value in result.items():
                if key != "message":
                    print(f"  {key}: {value}")
        
        print(f"\nRECOMMENDATIONS:")
        failed_tests = [name for name, result in results["tests"].items() if not result.get("success", False)]
        
        if not failed_tests:
            print("  ✓ All diagnostics passed. Network connectivity is good.")
        else:
            print(f"  ! {len(failed_tests)} test(s) failed:")
            for test_name in failed_tests:
                print(f"    - {test_name}: {results['tests'][test_name].get('message', 'Failed')}")
            
            # Specific recommendations
            if "tcp_connectivity" in failed_tests:
                print("  → Check if the server is running and accepting connections")
            if "dns_lookup" in failed_tests:
                print("  → Verify the hostname is correct")
            if "websocket_handshake" in failed_tests:
                print("  → Check WebSocket endpoint configuration")
            if "http_endpoint" in failed_tests:
                print("  → Verify HTTP server is running on the expected port")
        
        print("\n" + "=" * 70)

def main():
    """Main function"""
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8000/ws"
    
    diagnostics = NetworkDiagnostics(url)
    results = diagnostics.run_all_diagnostics()
    diagnostics.print_diagnostic_report(results)
    
    # Save results to file
    filename = f"network_diagnostics_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {filename}")
    
    # Return appropriate exit code
    return 0 if results["summary"]["success_rate"] >= 80 else 1

if __name__ == "__main__":
    exit(main())