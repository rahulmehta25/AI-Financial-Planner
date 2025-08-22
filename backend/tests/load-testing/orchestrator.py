"""
Load Testing Orchestrator

Main entry point for running comprehensive load tests with monitoring and reporting
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from locust import events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
from locust.runners import LocalRunner, MasterRunner, WorkerRunner
import gevent

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import LoadTestConfig, PerformanceSLA, LoadProfile
from data.test_data_generator import TestDataGenerator
from scenarios.comprehensive_scenarios import (
    FinancialPlanningUser,
    NewUserFlow
)
from monitoring.performance_monitor import (
    PrometheusMetricsCollector,
    SystemResourceMonitor,
    DatabaseMetricsCollector,
    PerformanceRegressionDetector,
    AlertingService,
    MonitoringDashboard,
    PerformanceMetrics
)


@dataclass
class LoadTestReport:
    """Comprehensive load test report"""
    test_id: str
    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Configuration
    target_users: int
    spawn_rate: int
    host: str
    profile: str
    
    # Results
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    
    # Response times (milliseconds)
    min_response_time: float
    max_response_time: float
    mean_response_time: float
    median_response_time: float
    p50_response_time: float
    p75_response_time: float
    p90_response_time: float
    p95_response_time: float
    p99_response_time: float
    
    # Throughput
    avg_rps: float
    peak_rps: float
    total_data_transferred_mb: float
    
    # Resource usage
    peak_cpu_percent: float
    avg_cpu_percent: float
    peak_memory_mb: float
    avg_memory_mb: float
    peak_db_connections: int
    
    # SLA validation
    sla_passed: bool
    sla_violations: List[Dict[str, Any]]
    
    # Errors
    error_breakdown: Dict[str, int]
    slowest_endpoints: List[Dict[str, float]]
    
    # Recommendations
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    def save_to_file(self, filepath: str):
        """Save report to file"""
        with open(filepath, 'w') as f:
            f.write(self.to_json())


class LoadTestOrchestrator:
    """Orchestrate load testing with monitoring and reporting"""
    
    def __init__(self, config: LoadTestConfig):
        """
        Initialize load test orchestrator
        
        Args:
            config: Load test configuration
        """
        self.config = config
        self.test_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.environment = None
        self.runner = None
        
        # Monitoring components
        self.prometheus_collector = PrometheusMetricsCollector(
            push_gateway_url=config.prometheus_url.replace("http://", "")
        ) if config.enable_monitoring else None
        
        self.resource_monitor = SystemResourceMonitor(interval=5)
        self.db_metrics_collector = DatabaseMetricsCollector(
            db_url=os.getenv("DATABASE_URL", "postgresql://localhost/financial_planning")
        )
        
        self.dashboard = MonitoringDashboard()
        self.alerting_service = AlertingService({
            "slack_webhook_url": config.slack_webhook_url
        }) if config.send_slack_notifications else None
        
        # Results storage
        self.results = []
        self.metrics_history = []
        
        # Create output directories
        self.output_dir = Path(f"./reports/{self.test_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_test_data(self):
        """Generate test data if needed"""
        print("Preparing test data...")
        
        test_data_dir = Path("./test_data")
        credentials_file = test_data_dir / "test_credentials.json"
        
        if not credentials_file.exists() or self.config.use_real_data:
            print(f"Generating test data for {self.config.num_test_accounts} users...")
            generator = TestDataGenerator(seed=self.config.data_seed)
            files = generator.generate_complete_dataset(
                num_users=self.config.num_test_accounts,
                output_dir=str(test_data_dir)
            )
            print(f"Test data generated: {files}")
        else:
            print(f"Using existing test data from {test_data_dir}")
    
    def setup_environment(self):
        """Setup Locust environment"""
        print("Setting up test environment...")
        
        # Setup Locust environment
        self.environment = Environment(
            user_classes=[FinancialPlanningUser],
            host=self.config.base_url,
            events=events
        )
        
        # Setup logging
        setup_logging("INFO")
        
        # Create runner based on configuration
        if os.getenv("LOCUST_MODE") == "master":
            self.runner = MasterRunner(self.environment)
        elif os.getenv("LOCUST_MODE") == "worker":
            self.runner = WorkerRunner(self.environment)
        else:
            self.runner = LocalRunner(self.environment)
        
        # Register event handlers
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register Locust event handlers for monitoring"""
        
        @self.environment.events.request.add_listener
        def on_request(request_type, name, response_time, response_length, exception, **kwargs):
            """Handle request events"""
            if self.prometheus_collector:
                status = 0 if exception else kwargs.get("response", {}).get("status_code", 200)
                self.prometheus_collector.record_request(
                    method=request_type,
                    endpoint=name,
                    status=status,
                    response_time=response_time / 1000.0,  # Convert to seconds
                    error=str(exception) if exception else None
                )
        
        @self.environment.events.test_start.add_listener
        def on_test_start(environment, **kwargs):
            """Handle test start"""
            print(f"\n{'='*60}")
            print(f"Load Test Started: {self.test_id}")
            print(f"Target: {environment.host}")
            print(f"Users: {self.config.num_users}")
            print(f"Spawn Rate: {self.config.spawn_rate}/sec")
            print(f"Duration: {self.config.test_duration}s")
            print(f"Profile: {self.config.profile}")
            print(f"{'='*60}\n")
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring()
        
        @self.environment.events.test_stop.add_listener
        def on_test_stop(environment, **kwargs):
            """Handle test stop"""
            print("\nLoad test completed, generating report...")
            
            # Stop resource monitoring
            self.resource_monitor.stop_monitoring()
            
            # Generate and save report
            report = self._generate_report()
            self._save_report(report)
            self._print_summary(report)
            
            # Check for regressions
            if self.config.enable_monitoring:
                self._check_regressions(report)
            
            # Send alerts if needed
            if self.alerting_service and not report.sla_passed:
                self._send_alerts(report)
    
    def run_test(self) -> LoadTestReport:
        """
        Run the load test
        
        Returns:
            Load test report
        """
        # Prepare test data
        self.prepare_test_data()
        
        # Setup environment
        self.setup_environment()
        
        # Start test
        print(f"\nStarting load test with {self.config.num_users} users...")
        self.runner.start(
            user_count=self.config.num_users,
            spawn_rate=self.config.spawn_rate
        )
        
        # Monitor test progress
        start_time = datetime.now()
        self._monitor_test_progress()
        
        # Run for specified duration
        gevent.spawn_later(self.config.test_duration, lambda: self.runner.quit())
        
        # Wait for test to complete
        self.runner.greenlet.join()
        end_time = datetime.now()
        
        # Generate final report
        report = self._generate_report()
        report.start_time = start_time
        report.end_time = end_time
        report.duration_seconds = (end_time - start_time).total_seconds()
        
        return report
    
    def _monitor_test_progress(self):
        """Monitor test progress and collect metrics"""
        def monitor_loop():
            while self.runner.state != "stopped":
                # Collect current metrics
                stats = self.environment.stats
                
                # Get system metrics
                system_metrics = self.resource_monitor.get_metrics()
                
                # Get database metrics
                db_metrics = self.db_metrics_collector.collect_metrics()
                
                # Create performance metrics snapshot
                metrics = PerformanceMetrics(
                    timestamp=datetime.now(),
                    response_time_p50=stats.total.get_response_time_percentile(0.50) or 0,
                    response_time_p95=stats.total.get_response_time_percentile(0.95) or 0,
                    response_time_p99=stats.total.get_response_time_percentile(0.99) or 0,
                    response_time_max=stats.total.max_response_time or 0,
                    requests_per_second=stats.total.current_rps or 0,
                    successful_requests=stats.total.num_requests - stats.total.num_failures,
                    failed_requests=stats.total.num_failures,
                    error_rate=stats.total.fail_ratio,
                    cpu_usage=system_metrics[-1]["cpu_percent"] if system_metrics else 0,
                    memory_usage=system_metrics[-1]["memory_used"] if system_metrics else 0,
                    memory_available=system_metrics[-1]["memory_available"] if system_metrics else 0,
                    disk_io_read=system_metrics[-1]["disk_read_rate"] if system_metrics else 0,
                    disk_io_write=system_metrics[-1]["disk_write_rate"] if system_metrics else 0,
                    network_rx=system_metrics[-1]["network_rx_rate"] if system_metrics else 0,
                    network_tx=system_metrics[-1]["network_tx_rate"] if system_metrics else 0,
                    db_connections_active=db_metrics.get("connections_active", 0),
                    db_connections_idle=db_metrics.get("connections_idle", 0),
                    db_query_time_avg=db_metrics.get("avg_query_time_ms", 0),
                    db_slow_queries=db_metrics.get("slow_queries", 0),
                    active_users=self.runner.user_count,
                    websocket_connections=0,  # Would be tracked separately
                    cache_hit_rate=db_metrics.get("cache_hit_ratio", 0),
                    queue_size=0  # Would be tracked separately
                )
                
                # Update dashboard
                self.dashboard.update_metrics(metrics)
                
                # Push to Prometheus
                if self.prometheus_collector:
                    self.prometheus_collector.update_system_metrics(metrics)
                    self.prometheus_collector.push_metrics(job_name=f"load_test_{self.test_id}")
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Print progress
                self._print_progress(metrics)
                
                time.sleep(self.config.metrics_interval)
        
        gevent.spawn(monitor_loop)
    
    def _print_progress(self, metrics: PerformanceMetrics):
        """Print test progress"""
        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
              f"Users: {metrics.active_users} | "
              f"RPS: {metrics.requests_per_second:.1f} | "
              f"P95: {metrics.response_time_p95:.0f}ms | "
              f"Errors: {metrics.error_rate*100:.2f}% | "
              f"CPU: {metrics.cpu_usage:.1f}%", end="")
    
    def _generate_report(self) -> LoadTestReport:
        """Generate comprehensive test report"""
        stats = self.environment.stats
        
        # Calculate resource usage statistics
        if self.metrics_history:
            cpu_values = [m.cpu_usage for m in self.metrics_history]
            memory_values = [m.memory_usage for m in self.metrics_history]
            db_connections = [m.db_connections_active for m in self.metrics_history]
            
            peak_cpu = max(cpu_values)
            avg_cpu = sum(cpu_values) / len(cpu_values)
            peak_memory = max(memory_values) / (1024 ** 2)  # Convert to MB
            avg_memory = sum(memory_values) / len(memory_values) / (1024 ** 2)
            peak_db_connections = max(db_connections)
        else:
            peak_cpu = avg_cpu = peak_memory = avg_memory = peak_db_connections = 0
        
        # Get error breakdown
        error_breakdown = {}
        for stat_name, stat in stats.entries.items():
            if stat.num_failures > 0:
                error_breakdown[stat_name] = stat.num_failures
        
        # Get slowest endpoints
        slowest_endpoints = []
        for stat_name, stat in stats.entries.items():
            if stat.num_requests > 0:
                slowest_endpoints.append({
                    "endpoint": stat_name,
                    "p95_ms": stat.get_response_time_percentile(0.95) or 0,
                    "requests": stat.num_requests
                })
        slowest_endpoints.sort(key=lambda x: x["p95_ms"], reverse=True)
        slowest_endpoints = slowest_endpoints[:10]  # Top 10 slowest
        
        # Check SLA violations
        sla_violations = self._check_sla_violations(stats)
        sla_passed = len(sla_violations) == 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(stats, sla_violations)
        
        return LoadTestReport(
            test_id=self.test_id,
            test_name=f"Load Test - {self.config.profile}",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration_seconds=self.config.test_duration,
            target_users=self.config.num_users,
            spawn_rate=self.config.spawn_rate,
            host=self.config.base_url,
            profile=str(self.config.profile),
            total_requests=stats.total.num_requests,
            successful_requests=stats.total.num_requests - stats.total.num_failures,
            failed_requests=stats.total.num_failures,
            error_rate=stats.total.fail_ratio,
            min_response_time=stats.total.min_response_time or 0,
            max_response_time=stats.total.max_response_time or 0,
            mean_response_time=stats.total.avg_response_time or 0,
            median_response_time=stats.total.median_response_time or 0,
            p50_response_time=stats.total.get_response_time_percentile(0.50) or 0,
            p75_response_time=stats.total.get_response_time_percentile(0.75) or 0,
            p90_response_time=stats.total.get_response_time_percentile(0.90) or 0,
            p95_response_time=stats.total.get_response_time_percentile(0.95) or 0,
            p99_response_time=stats.total.get_response_time_percentile(0.99) or 0,
            avg_rps=stats.total.total_rps or 0,
            peak_rps=max([m.requests_per_second for m in self.metrics_history]) if self.metrics_history else 0,
            total_data_transferred_mb=stats.total.total_content_length / (1024 ** 2) if stats.total.total_content_length else 0,
            peak_cpu_percent=peak_cpu,
            avg_cpu_percent=avg_cpu,
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            peak_db_connections=peak_db_connections,
            sla_passed=sla_passed,
            sla_violations=sla_violations,
            error_breakdown=error_breakdown,
            slowest_endpoints=slowest_endpoints,
            recommendations=recommendations
        )
    
    def _check_sla_violations(self, stats) -> List[Dict[str, Any]]:
        """Check for SLA violations"""
        violations = []
        sla = self.config.sla
        
        # Check response time SLAs
        p95 = stats.total.get_response_time_percentile(0.95) or 0
        if p95 > sla.api_response_p95:
            violations.append({
                "metric": "API Response P95",
                "threshold": sla.api_response_p95,
                "actual": p95,
                "violation_percent": ((p95 - sla.api_response_p95) / sla.api_response_p95) * 100
            })
        
        p99 = stats.total.get_response_time_percentile(0.99) or 0
        if p99 > sla.api_response_p99:
            violations.append({
                "metric": "API Response P99",
                "threshold": sla.api_response_p99,
                "actual": p99,
                "violation_percent": ((p99 - sla.api_response_p99) / sla.api_response_p99) * 100
            })
        
        # Check error rate SLA
        if stats.total.fail_ratio > sla.max_error_rate:
            violations.append({
                "metric": "Error Rate",
                "threshold": sla.max_error_rate * 100,
                "actual": stats.total.fail_ratio * 100,
                "violation_percent": ((stats.total.fail_ratio - sla.max_error_rate) / sla.max_error_rate) * 100
            })
        
        # Check throughput SLA
        if stats.total.current_rps < sla.min_requests_per_second:
            violations.append({
                "metric": "Throughput",
                "threshold": sla.min_requests_per_second,
                "actual": stats.total.current_rps,
                "violation_percent": ((sla.min_requests_per_second - stats.total.current_rps) / sla.min_requests_per_second) * 100
            })
        
        return violations
    
    def _generate_recommendations(self, stats, violations: List[Dict]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Based on SLA violations
        for violation in violations:
            metric = violation["metric"]
            
            if "Response" in metric:
                recommendations.append(
                    f"Optimize slow endpoints to improve {metric}. "
                    f"Consider caching, query optimization, or horizontal scaling."
                )
            elif metric == "Error Rate":
                recommendations.append(
                    "Investigate and fix errors. Check application logs for patterns. "
                    "Consider implementing circuit breakers and retry mechanisms."
                )
            elif metric == "Throughput":
                recommendations.append(
                    "Increase system capacity. Consider load balancing, "
                    "connection pooling, and asynchronous processing."
                )
        
        # Based on resource usage
        if self.metrics_history:
            avg_cpu = sum(m.cpu_usage for m in self.metrics_history) / len(self.metrics_history)
            if avg_cpu > 70:
                recommendations.append(
                    "High CPU usage detected. Profile CPU-intensive operations "
                    "and optimize algorithms or scale horizontally."
                )
            
            avg_memory = sum(m.memory_usage for m in self.metrics_history) / len(self.metrics_history)
            if avg_memory > 0.85 * psutil.virtual_memory().total:
                recommendations.append(
                    "High memory usage detected. Check for memory leaks "
                    "and optimize data structures."
                )
        
        # Based on specific endpoint performance
        for stat_name, stat in stats.entries.items():
            if "monte-carlo" in stat_name.lower():
                p95 = stat.get_response_time_percentile(0.95) or 0
                if p95 > 30000:  # 30 seconds
                    recommendations.append(
                        "Monte Carlo simulations exceeding target time. "
                        "Consider GPU acceleration or distributed computing."
                    )
            elif "report" in stat_name.lower():
                p95 = stat.get_response_time_percentile(0.95) or 0
                if p95 > 60000:  # 60 seconds
                    recommendations.append(
                        "Report generation exceeding target time. "
                        "Implement async generation with progress tracking."
                    )
        
        return list(set(recommendations))  # Remove duplicates
    
    def _save_report(self, report: LoadTestReport):
        """Save report to file"""
        # Save JSON report
        json_file = self.output_dir / f"report_{self.test_id}.json"
        report.save_to_file(str(json_file))
        print(f"\nReport saved to: {json_file}")
        
        # Save HTML report if configured
        if self.config.generate_html_report:
            html_file = self.output_dir / f"report_{self.test_id}.html"
            self._generate_html_report(report, str(html_file))
            print(f"HTML report saved to: {html_file}")
        
        # Save metrics history
        metrics_file = self.output_dir / f"metrics_{self.test_id}.json"
        with open(metrics_file, 'w') as f:
            json.dump(
                [m.to_dict() for m in self.metrics_history],
                f,
                indent=2,
                default=str
            )
        print(f"Metrics history saved to: {metrics_file}")
    
    def _generate_html_report(self, report: LoadTestReport, filepath: str):
        """Generate HTML report"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Load Test Report - {test_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; }}
        .metric-value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .metric-label {{ color: #777; font-size: 14px; margin-top: 5px; }}
        .pass {{ color: #4CAF50; }}
        .fail {{ color: #f44336; }}
        .warning {{ color: #ff9800; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .recommendation {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .violation {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .chart {{ margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #777; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Load Test Performance Report</h1>
        <p><strong>Test ID:</strong> {test_id} | <strong>Duration:</strong> {duration}s | <strong>Profile:</strong> {profile}</p>
        
        <h2>Executive Summary</h2>
        <div class="summary">
            <div class="metric-card">
                <div class="metric-value {status_class}">{status}</div>
                <div class="metric-label">Overall Status</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_requests:,}</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{success_rate:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_rps:.1f}</div>
                <div class="metric-label">Avg Requests/sec</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{p95:.0f}ms</div>
                <div class="metric-label">P95 Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{p99:.0f}ms</div>
                <div class="metric-label">P99 Response Time</div>
            </div>
        </div>
        
        <h2>Response Time Distribution</h2>
        <table>
            <tr>
                <th>Percentile</th>
                <th>Response Time (ms)</th>
                <th>Target SLA (ms)</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Minimum</td>
                <td>{min_rt:.0f}</td>
                <td>-</td>
                <td class="pass">✓</td>
            </tr>
            <tr>
                <td>Median (P50)</td>
                <td>{p50:.0f}</td>
                <td>200</td>
                <td class="{p50_status}">{{p50_icon}}</td>
            </tr>
            <tr>
                <td>P75</td>
                <td>{p75:.0f}</td>
                <td>350</td>
                <td class="{p75_status}">{{p75_icon}}</td>
            </tr>
            <tr>
                <td>P90</td>
                <td>{p90:.0f}</td>
                <td>450</td>
                <td class="{p90_status}">{{p90_icon}}</td>
            </tr>
            <tr>
                <td>P95</td>
                <td>{p95:.0f}</td>
                <td>500</td>
                <td class="{p95_status}">{{p95_icon}}</td>
            </tr>
            <tr>
                <td>P99</td>
                <td>{p99:.0f}</td>
                <td>1000</td>
                <td class="{p99_status}">{{p99_icon}}</td>
            </tr>
            <tr>
                <td>Maximum</td>
                <td>{max_rt:.0f}</td>
                <td>-</td>
                <td>-</td>
            </tr>
        </table>
        
        {violations_section}
        
        <h2>Slowest Endpoints</h2>
        <table>
            <tr>
                <th>Endpoint</th>
                <th>P95 Response Time (ms)</th>
                <th>Request Count</th>
            </tr>
            {slowest_endpoints_rows}
        </table>
        
        <h2>Resource Usage</h2>
        <div class="summary">
            <div class="metric-card">
                <div class="metric-value">{avg_cpu:.1f}%</div>
                <div class="metric-label">Avg CPU Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{peak_cpu:.1f}%</div>
                <div class="metric-label">Peak CPU Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_memory:.1f} MB</div>
                <div class="metric-label">Avg Memory</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{peak_memory:.1f} MB</div>
                <div class="metric-label">Peak Memory</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{peak_db_conn}</div>
                <div class="metric-label">Peak DB Connections</div>
            </div>
        </div>
        
        {recommendations_section}
        
        <div class="footer">
            <p>Generated: {generated_time} | Financial Planning Load Test Suite v1.0</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Prepare template variables
        status = "PASS" if report.sla_passed else "FAIL"
        status_class = "pass" if report.sla_passed else "fail"
        success_rate = (1 - report.error_rate) * 100
        
        # Response time status checks
        p50_status = "pass" if report.p50_response_time < 200 else "fail"
        p75_status = "pass" if report.p75_response_time < 350 else "fail"
        p90_status = "pass" if report.p90_response_time < 450 else "fail"
        p95_status = "pass" if report.p95_response_time < 500 else "fail"
        p99_status = "pass" if report.p99_response_time < 1000 else "fail"
        
        # Icons
        p50_icon = "✓" if p50_status == "pass" else "✗"
        p75_icon = "✓" if p75_status == "pass" else "✗"
        p90_icon = "✓" if p90_status == "pass" else "✗"
        p95_icon = "✓" if p95_status == "pass" else "✗"
        p99_icon = "✓" if p99_status == "pass" else "✗"
        
        # Violations section
        if report.sla_violations:
            violations_html = "<h2>SLA Violations</h2>"
            for violation in report.sla_violations:
                violations_html += f'''
                <div class="violation">
                    <strong>{violation['metric']}:</strong> 
                    Threshold: {violation['threshold']:.2f}, 
                    Actual: {violation['actual']:.2f} 
                    ({violation['violation_percent']:.1f}% violation)
                </div>
                '''
            violations_section = violations_html
        else:
            violations_section = "<h2>SLA Compliance</h2><p class='pass'>✓ All SLAs met successfully</p>"
        
        # Slowest endpoints
        slowest_endpoints_rows = ""
        for endpoint in report.slowest_endpoints[:10]:
            slowest_endpoints_rows += f'''
            <tr>
                <td>{endpoint['endpoint']}</td>
                <td>{endpoint['p95_ms']:.0f}</td>
                <td>{endpoint['requests']}</td>
            </tr>
            '''
        
        # Recommendations section
        if report.recommendations:
            recommendations_html = "<h2>Performance Recommendations</h2>"
            for rec in report.recommendations:
                recommendations_html += f'<div class="recommendation">{rec}</div>'
            recommendations_section = recommendations_html
        else:
            recommendations_section = ""
        
        # Generate HTML
        html_content = html_template.format(
            test_id=report.test_id,
            duration=report.duration_seconds,
            profile=report.profile,
            status=status,
            status_class=status_class,
            total_requests=report.total_requests,
            success_rate=success_rate,
            avg_rps=report.avg_rps,
            p95=report.p95_response_time,
            p99=report.p99_response_time,
            min_rt=report.min_response_time,
            p50=report.p50_response_time,
            p75=report.p75_response_time,
            p90=report.p90_response_time,
            max_rt=report.max_response_time,
            p50_status=p50_status,
            p75_status=p75_status,
            p90_status=p90_status,
            p95_status=p95_status,
            p99_status=p99_status,
            p50_icon=p50_icon,
            p75_icon=p75_icon,
            p90_icon=p90_icon,
            p95_icon=p95_icon,
            p99_icon=p99_icon,
            violations_section=violations_section,
            slowest_endpoints_rows=slowest_endpoints_rows,
            avg_cpu=report.avg_cpu_percent,
            peak_cpu=report.peak_cpu_percent,
            avg_memory=report.avg_memory_mb,
            peak_memory=report.peak_memory_mb,
            peak_db_conn=report.peak_db_connections,
            recommendations_section=recommendations_section,
            generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Save to file
        with open(filepath, 'w') as f:
            f.write(html_content)
    
    def _print_summary(self, report: LoadTestReport):
        """Print test summary to console"""
        print(f"\n{'='*60}")
        print(f"LOAD TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Test ID: {report.test_id}")
        print(f"Duration: {report.duration_seconds:.1f}s")
        print(f"Status: {'PASS' if report.sla_passed else 'FAIL'}")
        print(f"\nPERFORMANCE METRICS:")
        print(f"  Total Requests: {report.total_requests:,}")
        print(f"  Success Rate: {(1 - report.error_rate) * 100:.2f}%")
        print(f"  Avg RPS: {report.avg_rps:.1f}")
        print(f"  Peak RPS: {report.peak_rps:.1f}")
        print(f"\nRESPONSE TIMES:")
        print(f"  P50: {report.p50_response_time:.0f}ms")
        print(f"  P95: {report.p95_response_time:.0f}ms")
        print(f"  P99: {report.p99_response_time:.0f}ms")
        print(f"\nRESOURCE USAGE:")
        print(f"  Avg CPU: {report.avg_cpu_percent:.1f}%")
        print(f"  Peak CPU: {report.peak_cpu_percent:.1f}%")
        print(f"  Avg Memory: {report.avg_memory_mb:.1f}MB")
        print(f"  Peak Memory: {report.peak_memory_mb:.1f}MB")
        
        if report.sla_violations:
            print(f"\nSLA VIOLATIONS ({len(report.sla_violations)}):")
            for violation in report.sla_violations:
                print(f"  - {violation['metric']}: {violation['actual']:.2f} > {violation['threshold']:.2f}")
        
        if report.recommendations:
            print(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(report.recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        print(f"{'='*60}\n")
    
    def _check_regressions(self, report: LoadTestReport):
        """Check for performance regressions"""
        # Load baseline if exists
        baseline_file = Path("./baseline/baseline_metrics.json")
        if baseline_file.exists():
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
            
            detector = PerformanceRegressionDetector(baseline)
            current_metrics = {
                "response_time_p95": report.p95_response_time,
                "response_time_p99": report.p99_response_time,
                "error_rate": report.error_rate,
                "throughput": report.avg_rps,
                "cpu_usage": report.avg_cpu_percent,
                "memory_usage": report.avg_memory_mb
            }
            
            regressions = detector.check_regression(current_metrics)
            if regressions:
                print("\nPERFORMANCE REGRESSIONS DETECTED:")
                for reg in regressions:
                    print(f"  - {reg['metric']}: {reg['change_percent']:.1f}% regression")
    
    def _send_alerts(self, report: LoadTestReport):
        """Send alerts for failed tests"""
        if self.alerting_service:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "type": "load_test_failure",
                "severity": "high" if report.error_rate > 0.05 else "medium",
                "summary": f"Load test {report.test_id} failed SLA validation",
                "violations": report.sla_violations,
                "recommendations": report.recommendations[:3]
            }
            self.alerting_service.send_alert(alert)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Financial Planning Load Testing Suite")
    
    # Test configuration
    parser.add_argument("--host", default="http://localhost:8000", help="Target host URL")
    parser.add_argument("--users", type=int, default=100, help="Number of concurrent users")
    parser.add_argument("--spawn-rate", type=int, default=10, help="User spawn rate per second")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--profile", choices=["smoke", "load", "stress", "spike", "soak"], 
                       default="load", help="Load test profile")
    
    # Test data
    parser.add_argument("--generate-data", action="store_true", help="Generate new test data")
    parser.add_argument("--test-accounts", type=int, default=1000, help="Number of test accounts")
    
    # Monitoring
    parser.add_argument("--prometheus", default="localhost:9091", help="Prometheus push gateway")
    parser.add_argument("--grafana", default="localhost:3000", help="Grafana URL")
    parser.add_argument("--no-monitoring", action="store_true", help="Disable monitoring")
    
    # Reporting
    parser.add_argument("--slack-webhook", help="Slack webhook URL for alerts")
    parser.add_argument("--html-report", action="store_true", default=True, help="Generate HTML report")
    parser.add_argument("--json-report", action="store_true", default=True, help="Generate JSON report")
    
    args = parser.parse_args()
    
    # Create configuration
    config = LoadTestConfig(
        base_url=args.host,
        num_users=args.users,
        spawn_rate=args.spawn_rate,
        test_duration=args.duration,
        profile=LoadProfile[args.profile.upper()],
        use_real_data=args.generate_data,
        num_test_accounts=args.test_accounts,
        enable_monitoring=not args.no_monitoring,
        prometheus_url=args.prometheus,
        grafana_url=args.grafana,
        slack_webhook_url=args.slack_webhook,
        generate_html_report=args.html_report,
        generate_json_report=args.json_report
    )
    
    # Run test
    orchestrator = LoadTestOrchestrator(config)
    report = orchestrator.run_test()
    
    # Exit with appropriate code
    sys.exit(0 if report.sla_passed else 1)


if __name__ == "__main__":
    main()