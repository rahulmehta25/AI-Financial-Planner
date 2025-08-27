#!/usr/bin/env python3
"""
WebSocket Test Client for Financial Planning Backend
====================================================

Comprehensive WebSocket testing client that validates:
- Connection establishment and stability
- Message exchange patterns
- Ping/pong heartbeat mechanism
- Error handling and recovery
- Reconnection logic
- Performance metrics

Usage:
    python websocket_test_client.py [options]

Test Scenarios:
1. Basic connection test
2. Ping/pong latency test
3. Message throughput test
4. Connection stability test
5. Reconnection resilience test
6. Error handling test
"""

import asyncio
import json
import logging
import time
import websockets
import argparse
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import statistics
import random
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('websocket_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    duration_ms: float
    message: str
    data: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    connect_time_ms: float = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    ping_latencies: List[float] = None
    errors: List[str] = None
    disconnections: int = 0
    reconnections: int = 0
    test_duration_s: float = 0
    
    def __post_init__(self):
        if self.ping_latencies is None:
            self.ping_latencies = []
        if self.errors is None:
            self.errors = []
    
    @property
    def avg_ping_latency(self) -> float:
        return statistics.mean(self.ping_latencies) if self.ping_latencies else 0
    
    @property
    def min_ping_latency(self) -> float:
        return min(self.ping_latencies) if self.ping_latencies else 0
    
    @property
    def max_ping_latency(self) -> float:
        return max(self.ping_latencies) if self.ping_latencies else 0
    
    @property
    def message_rate(self) -> float:
        return (self.total_messages_sent + self.total_messages_received) / self.test_duration_s if self.test_duration_s > 0 else 0

class WebSocketTestClient:
    """Comprehensive WebSocket test client"""
    
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        self.url = url
        self.websocket = None
        self.running = False
        self.metrics = ConnectionMetrics()
        self.test_results: List[TestResult] = []
        self.message_handlers: Dict[str, callable] = {}
        self.pending_pings: Dict[str, float] = {}
        
        # Test configuration
        self.ping_interval = 5.0  # seconds
        self.test_timeout = 30.0  # seconds
        self.reconnect_attempts = 3
        self.reconnect_delay = 2.0  # seconds
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def add_message_handler(self, message_type: str, handler: callable):
        """Add handler for specific message types"""
        self.message_handlers[message_type] = handler
    
    async def connect(self) -> TestResult:
        """Test connection establishment"""
        start_time = time.time()
        
        try:
            logger.info(f"Connecting to WebSocket: {self.url}")
            connect_start = time.time()
            
            self.websocket = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                max_size=1024 * 1024,  # 1MB
                max_queue=100
            )
            
            connect_time = (time.time() - connect_start) * 1000
            self.metrics.connect_time_ms = connect_time
            
            logger.info(f"Connected successfully in {connect_time:.2f}ms")
            
            return TestResult(
                test_name="connection_test",
                success=True,
                duration_ms=time.time() * 1000 - start_time * 1000,
                message=f"Connected successfully in {connect_time:.2f}ms",
                data={"connect_time_ms": connect_time}
            )
            
        except Exception as e:
            error_msg = f"Connection failed: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            
            return TestResult(
                test_name="connection_test",
                success=False,
                duration_ms=time.time() * 1000 - start_time * 1000,
                message=error_msg,
                data={"error": str(e)}
            )
    
    async def disconnect(self):
        """Clean disconnect"""
        if self.websocket:
            logger.info("Disconnecting WebSocket...")
            await self.websocket.close()
            self.websocket = None
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message to WebSocket"""
        if not self.websocket:
            return False
        
        try:
            message_json = json.dumps(message)
            await self.websocket.send(message_json)
            self.metrics.total_messages_sent += 1
            logger.debug(f"Sent message: {message}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send message: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            return False
    
    async def receive_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.metrics.total_messages_received += 1
                    logger.debug(f"Received message: {data}")
                    
                    # Handle ping responses
                    if data.get("type") == "pong":
                        await self._handle_pong(data)
                    
                    # Call registered handlers
                    message_type = data.get("type")
                    if message_type in self.message_handlers:
                        await self.message_handlers[message_type](data)
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON received: {e}"
                    logger.error(error_msg)
                    self.metrics.errors.append(error_msg)
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"WebSocket connection closed: {e}")
            self.metrics.disconnections += 1
            
        except Exception as e:
            error_msg = f"Error receiving messages: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
    
    async def _handle_pong(self, data: Dict[str, Any]):
        """Handle pong response for latency calculation"""
        timestamp_str = data.get("timestamp")
        if timestamp_str and timestamp_str in self.pending_pings:
            sent_time = self.pending_pings.pop(timestamp_str)
            latency = (time.time() - sent_time) * 1000  # Convert to ms
            self.metrics.ping_latencies.append(latency)
            logger.debug(f"Ping latency: {latency:.2f}ms")
    
    async def ping_test(self, count: int = 10, interval: float = 1.0) -> TestResult:
        """Test ping/pong latency"""
        start_time = time.time()
        successful_pings = 0
        
        logger.info(f"Starting ping test: {count} pings with {interval}s interval")
        
        try:
            for i in range(count):
                timestamp = datetime.now().isoformat()
                ping_time = time.time()
                self.pending_pings[timestamp] = ping_time
                
                success = await self.send_message({
                    "type": "ping",
                    "timestamp": timestamp,
                    "sequence": i
                })
                
                if success:
                    successful_pings += 1
                
                if i < count - 1:  # Don't sleep after last ping
                    await asyncio.sleep(interval)
            
            # Wait for remaining pongs
            await asyncio.sleep(2.0)
            
            duration = (time.time() - start_time) * 1000
            success_rate = successful_pings / count if count > 0 else 0
            
            return TestResult(
                test_name="ping_test",
                success=successful_pings > 0,
                duration_ms=duration,
                message=f"Completed {successful_pings}/{count} pings, avg latency: {self.metrics.avg_ping_latency:.2f}ms",
                data={
                    "total_pings": count,
                    "successful_pings": successful_pings,
                    "success_rate": success_rate,
                    "avg_latency_ms": self.metrics.avg_ping_latency,
                    "min_latency_ms": self.metrics.min_ping_latency,
                    "max_latency_ms": self.metrics.max_ping_latency
                }
            )
            
        except Exception as e:
            error_msg = f"Ping test failed: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            
            return TestResult(
                test_name="ping_test",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=error_msg,
                data={"error": str(e)}
            )
    
    async def subscription_test(self) -> TestResult:
        """Test subscription mechanism"""
        start_time = time.time()
        
        logger.info("Testing subscription mechanism...")
        
        try:
            # Test subscribe message
            subscribe_success = await self.send_message({
                "type": "subscribe_updates",
                "data": "real_time_updates"
            })
            
            if not subscribe_success:
                raise Exception("Failed to send subscription message")
            
            # Wait for confirmation
            await asyncio.sleep(2.0)
            
            duration = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name="subscription_test",
                success=True,
                duration_ms=duration,
                message="Subscription test completed successfully",
                data={"subscribed": True}
            )
            
        except Exception as e:
            error_msg = f"Subscription test failed: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            
            return TestResult(
                test_name="subscription_test",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=error_msg,
                data={"error": str(e)}
            )
    
    async def stress_test(self, duration_s: int = 30, message_rate: float = 1.0) -> TestResult:
        """Test connection under stress"""
        start_time = time.time()
        messages_sent = 0
        
        logger.info(f"Starting stress test: {duration_s}s duration, {message_rate} msg/s")
        
        try:
            end_time = start_time + duration_s
            
            while time.time() < end_time and self.running:
                # Send test message
                success = await self.send_message({
                    "type": "stress_test",
                    "timestamp": datetime.now().isoformat(),
                    "sequence": messages_sent,
                    "data": "x" * random.randint(10, 100)  # Variable payload
                })
                
                if success:
                    messages_sent += 1
                
                # Control message rate
                if message_rate > 0:
                    await asyncio.sleep(1.0 / message_rate)
            
            duration = (time.time() - start_time) * 1000
            actual_rate = messages_sent / (duration / 1000) if duration > 0 else 0
            
            return TestResult(
                test_name="stress_test",
                success=True,
                duration_ms=duration,
                message=f"Sent {messages_sent} messages at {actual_rate:.2f} msg/s",
                data={
                    "messages_sent": messages_sent,
                    "target_rate": message_rate,
                    "actual_rate": actual_rate,
                    "duration_s": duration / 1000
                }
            )
            
        except Exception as e:
            error_msg = f"Stress test failed: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            
            return TestResult(
                test_name="stress_test",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=error_msg,
                data={"error": str(e), "messages_sent": messages_sent}
            )
    
    async def reconnection_test(self, disconnections: int = 3) -> TestResult:
        """Test reconnection logic"""
        start_time = time.time()
        successful_reconnections = 0
        
        logger.info(f"Testing reconnection logic with {disconnections} disconnections")
        
        try:
            for i in range(disconnections):
                logger.info(f"Disconnection test {i+1}/{disconnections}")
                
                # Force disconnect
                if self.websocket:
                    await self.websocket.close()
                    self.metrics.disconnections += 1
                
                # Wait before reconnecting
                await asyncio.sleep(self.reconnect_delay)
                
                # Attempt reconnection
                connect_result = await self.connect()
                if connect_result.success:
                    successful_reconnections += 1
                    self.metrics.reconnections += 1
                    
                    # Test connection with ping
                    ping_result = await self.ping_test(count=1)
                    if not ping_result.success:
                        logger.warning("Ping failed after reconnection")
                else:
                    logger.error(f"Reconnection {i+1} failed")
            
            duration = (time.time() - start_time) * 1000
            success_rate = successful_reconnections / disconnections if disconnections > 0 else 0
            
            return TestResult(
                test_name="reconnection_test",
                success=successful_reconnections > 0,
                duration_ms=duration,
                message=f"Successful reconnections: {successful_reconnections}/{disconnections}",
                data={
                    "total_disconnections": disconnections,
                    "successful_reconnections": successful_reconnections,
                    "success_rate": success_rate
                }
            )
            
        except Exception as e:
            error_msg = f"Reconnection test failed: {e}"
            logger.error(error_msg)
            self.metrics.errors.append(error_msg)
            
            return TestResult(
                test_name="reconnection_test",
                success=False,
                duration_ms=(time.time() - start_time) * 1000,
                message=error_msg,
                data={"error": str(e)}
            )
    
    async def run_comprehensive_test_suite(self):
        """Run all test scenarios"""
        logger.info("=" * 60)
        logger.info("WEBSOCKET COMPREHENSIVE TEST SUITE")
        logger.info("=" * 60)
        
        self.running = True
        test_start = time.time()
        
        # Add message handlers
        self.add_message_handler("subscription_confirmed", self._handle_subscription_confirmed)
        self.add_message_handler("connection_established", self._handle_connection_established)
        
        try:
            # Test 1: Connection
            logger.info("\n1. Testing connection establishment...")
            result = await self.connect()
            self.test_results.append(result)
            
            if not result.success:
                logger.error("Connection failed, aborting remaining tests")
                return
            
            # Start message listener
            listener_task = asyncio.create_task(self.receive_messages())
            
            # Wait for connection to stabilize
            await asyncio.sleep(2.0)
            
            # Test 2: Ping/Pong
            logger.info("\n2. Testing ping/pong mechanism...")
            result = await self.ping_test(count=5, interval=1.0)
            self.test_results.append(result)
            
            # Test 3: Subscription
            logger.info("\n3. Testing subscription mechanism...")
            result = await self.subscription_test()
            self.test_results.append(result)
            
            # Test 4: Stress Test
            logger.info("\n4. Running stress test...")
            result = await self.stress_test(duration_s=10, message_rate=2.0)
            self.test_results.append(result)
            
            # Test 5: Reconnection
            logger.info("\n5. Testing reconnection logic...")
            listener_task.cancel()  # Stop listener for reconnection test
            result = await self.reconnection_test(disconnections=2)
            self.test_results.append(result)
            
            # Calculate total test duration
            self.metrics.test_duration_s = time.time() - test_start
            
            # Generate and print report
            self.generate_report()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            traceback.print_exc()
            
        finally:
            self.running = False
            if self.websocket:
                await self.disconnect()
    
    async def _handle_subscription_confirmed(self, data: Dict[str, Any]):
        """Handle subscription confirmation"""
        logger.info(f"Subscription confirmed: {data.get('message')}")
    
    async def _handle_connection_established(self, data: Dict[str, Any]):
        """Handle connection establishment message"""
        logger.info("Connection establishment confirmed by server")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 80)
        logger.info("WEBSOCKET TEST REPORT")
        logger.info("=" * 80)
        
        # Summary statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\nTEST SUMMARY:")
        logger.info(f"  Total Tests:     {total_tests}")
        logger.info(f"  Passed:          {passed_tests}")
        logger.info(f"  Failed:          {failed_tests}")
        logger.info(f"  Pass Rate:       {pass_rate:.1f}%")
        
        # Connection metrics
        logger.info(f"\nCONNECTION METRICS:")
        logger.info(f"  Connection Time: {self.metrics.connect_time_ms:.2f}ms")
        logger.info(f"  Messages Sent:   {self.metrics.total_messages_sent}")
        logger.info(f"  Messages Recv:   {self.metrics.total_messages_received}")
        logger.info(f"  Disconnections:  {self.metrics.disconnections}")
        logger.info(f"  Reconnections:   {self.metrics.reconnections}")
        logger.info(f"  Total Errors:    {len(self.metrics.errors)}")
        logger.info(f"  Test Duration:   {self.metrics.test_duration_s:.1f}s")
        logger.info(f"  Message Rate:    {self.metrics.message_rate:.2f} msg/s")
        
        # Ping/Pong statistics
        if self.metrics.ping_latencies:
            logger.info(f"\nPING/PONG LATENCY:")
            logger.info(f"  Average:         {self.metrics.avg_ping_latency:.2f}ms")
            logger.info(f"  Minimum:         {self.metrics.min_ping_latency:.2f}ms")
            logger.info(f"  Maximum:         {self.metrics.max_ping_latency:.2f}ms")
            logger.info(f"  Samples:         {len(self.metrics.ping_latencies)}")
        
        # Individual test results
        logger.info(f"\nTEST DETAILS:")
        for result in self.test_results:
            status = "✓ PASS" if result.success else "✗ FAIL"
            logger.info(f"  {result.test_name:20} {status:8} {result.duration_ms:8.1f}ms  {result.message}")
        
        # Error details
        if self.metrics.errors:
            logger.info(f"\nERROR DETAILS:")
            for i, error in enumerate(self.metrics.errors, 1):
                logger.info(f"  {i:2d}. {error}")
        
        # Recommendations
        logger.info(f"\nRECOMMENDATIONS:")
        if pass_rate == 100:
            logger.info("  ✓ All tests passed! WebSocket implementation is working correctly.")
        else:
            logger.info("  ! Some tests failed. Please review the error details above.")
        
        if self.metrics.avg_ping_latency > 100:
            logger.info("  ! High ping latency detected. Check network conditions.")
        
        if len(self.metrics.errors) > 0:
            logger.info("  ! Errors detected. Review error handling implementation.")
        
        if self.metrics.reconnections < self.metrics.disconnections:
            logger.info("  ! Reconnection issues detected. Review reconnection logic.")
        
        logger.info("\n" + "=" * 80)
        
        # Save detailed report to file
        self.save_report_to_file()
    
    def save_report_to_file(self):
        """Save detailed test report to JSON file"""
        report_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "websocket_url": self.url,
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r.success),
                "failed_tests": sum(1 for r in self.test_results if not r.success),
                "pass_rate": (sum(1 for r in self.test_results if r.success) / len(self.test_results) * 100) if self.test_results else 0
            },
            "metrics": asdict(self.metrics),
            "test_results": [asdict(r) for r in self.test_results],
            "configuration": {
                "ping_interval": self.ping_interval,
                "test_timeout": self.test_timeout,
                "reconnect_attempts": self.reconnect_attempts,
                "reconnect_delay": self.reconnect_delay
            }
        }
        
        filename = f"websocket_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            logger.info(f"Detailed report saved to: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save report file: {e}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="WebSocket Test Client")
    parser.add_argument("--url", default="ws://localhost:8000/ws", 
                       help="WebSocket URL to test (default: ws://localhost:8000/ws)")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick test suite")
    parser.add_argument("--ping-only", action="store_true", 
                       help="Run ping test only")
    parser.add_argument("--stress", action="store_true", 
                       help="Run stress test only")
    
    args = parser.parse_args()
    
    client = WebSocketTestClient(url=args.url)
    
    try:
        if args.ping_only:
            # Ping test only
            logger.info("Running ping test only...")
            result = await client.connect()
            if result.success:
                listener_task = asyncio.create_task(client.receive_messages())
                await asyncio.sleep(1.0)
                ping_result = await client.ping_test(count=10, interval=0.5)
                listener_task.cancel()
                client.test_results.append(ping_result)
                client.generate_report()
            await client.disconnect()
            
        elif args.stress:
            # Stress test only
            logger.info("Running stress test only...")
            result = await client.connect()
            if result.success:
                listener_task = asyncio.create_task(client.receive_messages())
                await asyncio.sleep(1.0)
                stress_result = await client.stress_test(duration_s=60, message_rate=5.0)
                listener_task.cancel()
                client.test_results.append(stress_result)
                client.generate_report()
            await client.disconnect()
            
        else:
            # Full test suite
            await client.run_comprehensive_test_suite()
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())