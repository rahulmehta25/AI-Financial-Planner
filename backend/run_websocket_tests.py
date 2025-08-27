#!/usr/bin/env python3
"""
WebSocket Test Runner
====================

Simple script to run WebSocket tests with different configurations
and check server availability.
"""

import subprocess
import sys
import time
import socket
import json
import logging
from urllib.parse import urlparse
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_server_availability(url: str) -> bool:
    """Check if the WebSocket server is available"""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or 'localhost'
        port = parsed.port or 8000
        
        logger.info(f"Checking server availability at {host}:{port}...")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            logger.info("✓ Server is available")
            return True
        else:
            logger.warning(f"✗ Server is not available (connection failed)")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error checking server: {e}")
        return False

def start_demo_server():
    """Start the demo server if it's not running"""
    logger.info("Starting demo server...")
    
    try:
        # Try to start the working demo
        process = subprocess.Popen(
            [sys.executable, "working_demo.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give the server time to start
        time.sleep(5)
        
        # Check if it's running
        if process.poll() is None:  # Process is still running
            logger.info("✓ Demo server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(f"✗ Demo server failed to start")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        logger.error(f"✗ Failed to start demo server: {e}")
        return None

def run_websocket_test(test_type: str = "comprehensive", url: str = "ws://localhost:8000/ws") -> Dict[str, Any]:
    """Run WebSocket test and return results"""
    logger.info(f"Running {test_type} WebSocket test...")
    
    try:
        cmd = [sys.executable, "websocket_test_client.py", "--url", url]
        
        if test_type == "ping":
            cmd.append("--ping-only")
        elif test_type == "stress":
            cmd.append("--stress")
        elif test_type == "quick":
            cmd.append("--quick")
        
        # Run the test
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Test timed out after 5 minutes")
        return {
            "success": False,
            "error": "Test timed out",
            "stdout": "",
            "stderr": ""
        }
    except Exception as e:
        logger.error(f"Failed to run test: {e}")
        return {
            "success": False,
            "error": str(e),
            "stdout": "",
            "stderr": ""
        }

def main():
    """Main test runner"""
    print("=" * 60)
    print("WEBSOCKET TEST RUNNER")
    print("=" * 60)
    
    url = "ws://localhost:8000/ws"
    
    # Check if server is available
    server_available = check_server_availability(url)
    demo_process = None
    
    if not server_available:
        print("\nServer not available. Attempting to start demo server...")
        demo_process = start_demo_server()
        
        if demo_process:
            # Recheck server availability
            time.sleep(3)
            server_available = check_server_availability(url)
        
        if not server_available:
            print("\n✗ Unable to connect to WebSocket server")
            print("Please ensure the server is running at:", url)
            print("\nTo start the server manually, run:")
            print("  python working_demo.py")
            print("  # or")
            print("  python minimal_working_demo.py")
            return 1
    
    try:
        print(f"\n✓ WebSocket server is available at {url}")
        print("\nRunning test scenarios...")
        
        # Test scenarios to run
        test_scenarios = [
            ("ping", "Ping/Pong Latency Test"),
            ("comprehensive", "Comprehensive Test Suite")
        ]
        
        results = {}
        
        for test_type, description in test_scenarios:
            print(f"\n{'='*40}")
            print(f"RUNNING: {description}")
            print(f"{'='*40}")
            
            result = run_websocket_test(test_type, url)
            results[test_type] = result
            
            if result["success"]:
                print(f"✓ {description} completed successfully")
                if result["stdout"]:
                    print("\nTest Output:")
                    print(result["stdout"])
            else:
                print(f"✗ {description} failed")
                if result.get("error"):
                    print(f"Error: {result['error']}")
                if result["stderr"]:
                    print(f"Error Output: {result['stderr']}")
        
        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = sum(1 for r in results.values() if r["success"])
        total = len(results)
        
        print(f"Tests Passed: {passed}/{total}")
        
        for test_type, result in results.items():
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"  {test_type:15} {status}")
        
        if passed == total:
            print("\n🎉 All tests passed! WebSocket implementation is working correctly.")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
            return 1
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        return 1
    
    finally:
        # Clean up demo server if we started it
        if demo_process:
            print("\nStopping demo server...")
            try:
                demo_process.terminate()
                demo_process.wait(timeout=10)
                print("✓ Demo server stopped")
            except subprocess.TimeoutExpired:
                demo_process.kill()
                print("✓ Demo server killed")
            except Exception as e:
                print(f"Warning: Failed to stop demo server: {e}")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)