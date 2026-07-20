"""
Load Testing Configuration

Defines performance benchmarks, SLAs, and test parameters
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class LoadProfile(Enum):
    """Load test profile types"""
    SMOKE = "smoke"  # Quick validation test
    LOAD = "load"  # Standard load test
    STRESS = "stress"  # Push to breaking point
    SPIKE = "spike"  # Sudden load increase
    SOAK = "soak"  # Extended duration test
    BREAKPOINT = "breakpoint"  # Find system limits


@dataclass
class PerformanceSLA:
    """Service Level Agreement for performance metrics"""
    
    # Response time SLAs (milliseconds)
    api_response_p50: int = 200  # 50th percentile
    api_response_p95: int = 500  # 95th percentile
    api_response_p99: int = 1000  # 99th percentile
    
    # Specific endpoint SLAs
    monte_carlo_p95: int = 30000  # 30 seconds for simulation
    pdf_generation_p95: int = 60000  # 60 seconds for PDF
    market_data_p95: int = 300  # Real-time data
    websocket_latency_p95: int = 100  # WebSocket messages
    
    # Throughput SLAs
    min_requests_per_second: float = 100
    min_concurrent_users: int = 500
    min_websocket_connections: int = 1000
    
    # Error rate SLAs
    max_error_rate: float = 0.01  # 1% error rate
    max_timeout_rate: float = 0.005  # 0.5% timeout rate
    
    # Database SLAs
    db_query_p95: int = 50  # Database query time
    db_connection_pool_utilization: float = 0.8  # Max 80% utilization
    
    # Resource SLAs
    max_cpu_utilization: float = 0.75  # 75% CPU
    max_memory_utilization: float = 0.85  # 85% memory
    max_disk_io_wait: float = 0.1  # 10% I/O wait


@dataclass
class LoadTestConfig:
    """Load test configuration"""
    
    # Environment
    base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    environment: str = "test"
    
    # Load profile
    profile: LoadProfile = LoadProfile.LOAD
    
    # User configuration
    num_users: int = 100
    spawn_rate: int = 10  # Users per second
    test_duration: int = 300  # Seconds
    
    # Test data
    use_real_data: bool = False
    data_seed: int = 42
    num_test_accounts: int = 1000
    
    # Scenario weights (percentage)
    scenario_weights: Dict[str, int] = field(default_factory=lambda: {
        'user_onboarding': 5,
        'portfolio_view': 25,
        'monte_carlo_simulation': 15,
        'goal_management': 15,
        'market_data_streaming': 10,
        'investment_rebalancing': 10,
        'transaction_sync': 10,
        'report_generation': 5,
        'websocket_sessions': 5
    })
    
    # Performance SLAs
    sla: PerformanceSLA = field(default_factory=PerformanceSLA)
    
    # Monitoring
    enable_monitoring: bool = True
    metrics_interval: int = 10  # Seconds
    grafana_url: str = "http://localhost:3000"
    prometheus_url: str = "http://localhost:9090"
    
    # Reporting
    generate_html_report: bool = True
    generate_json_report: bool = True
    send_slack_notifications: bool = False
    slack_webhook_url: Optional[str] = None
    
    # Advanced options
    connection_timeout: int = 30  # Seconds
    request_timeout: int = 60  # Seconds
    max_retries: int = 3
    retry_delay: int = 1  # Seconds
    
    # WebSocket configuration
    websocket_ping_interval: int = 30  # Seconds
    websocket_reconnect_attempts: int = 5
    
    # Database connection pooling simulation
    db_connection_pool_size: int = 100
    db_max_overflow: int = 50


@dataclass
class LoadProfile:
    """Defines load test profile stages"""
    
    name: str
    stages: List[Dict[str, int]]  # List of {duration, target_users}
    description: str
    
    @classmethod
    def smoke_test(cls):
        """Quick validation test"""
        return cls(
            name="Smoke Test",
            stages=[
                {"duration": 60, "target": 5},  # Ramp up to 5 users
                {"duration": 120, "target": 5},  # Stay at 5 users
                {"duration": 30, "target": 0},  # Ramp down
            ],
            description="Quick validation of basic functionality"
        )
    
    @classmethod
    def load_test(cls):
        """Standard load test"""
        return cls(
            name="Load Test",
            stages=[
                {"duration": 120, "target": 100},  # Ramp up to 100 users
                {"duration": 600, "target": 100},  # Stay at 100 users for 10 min
                {"duration": 120, "target": 200},  # Increase to 200 users
                {"duration": 300, "target": 200},  # Stay at 200 users for 5 min
                {"duration": 60, "target": 0},  # Ramp down
            ],
            description="Standard load test with gradual ramp-up"
        )
    
    @classmethod
    def stress_test(cls):
        """Push system to limits"""
        return cls(
            name="Stress Test",
            stages=[
                {"duration": 120, "target": 100},  # Warm up
                {"duration": 120, "target": 500},  # Rapid increase
                {"duration": 300, "target": 500},  # Sustain high load
                {"duration": 120, "target": 1000},  # Push to limit
                {"duration": 180, "target": 1000},  # Sustain peak
                {"duration": 120, "target": 0},  # Recovery
            ],
            description="Stress test to find breaking point"
        )
    
    @classmethod
    def spike_test(cls):
        """Sudden load increase"""
        return cls(
            name="Spike Test",
            stages=[
                {"duration": 60, "target": 50},  # Normal load
                {"duration": 300, "target": 50},  # Steady state
                {"duration": 10, "target": 500},  # Sudden spike
                {"duration": 120, "target": 500},  # Sustain spike
                {"duration": 10, "target": 50},  # Drop back
                {"duration": 300, "target": 50},  # Recovery period
                {"duration": 60, "target": 0},  # Ramp down
            ],
            description="Test system response to sudden traffic spikes"
        )
    
    @classmethod
    def soak_test(cls):
        """Extended duration test"""
        return cls(
            name="Soak Test",
            stages=[
                {"duration": 300, "target": 200},  # Ramp up
                {"duration": 14400, "target": 200},  # 4 hours sustained
                {"duration": 300, "target": 0},  # Ramp down
            ],
            description="Extended test to detect memory leaks and degradation"
        )


# Endpoint-specific configurations
ENDPOINT_CONFIGS = {
    "/api/v1/auth/login": {
        "timeout": 5000,
        "max_retries": 3,
        "expected_status": [200, 201],
        "sla_p95": 500
    },
    "/api/v1/simulations/monte-carlo": {
        "timeout": 60000,
        "max_retries": 1,
        "expected_status": [200],
        "sla_p95": 30000
    },
    "/api/v1/market-data/stream": {
        "timeout": 1000,
        "max_retries": 5,
        "expected_status": [200],
        "sla_p95": 100
    },
    "/api/v1/reports/generate": {
        "timeout": 120000,
        "max_retries": 2,
        "expected_status": [200, 202],
        "sla_p95": 60000
    },
    "/api/v1/banking/sync": {
        "timeout": 30000,
        "max_retries": 3,
        "expected_status": [200],
        "sla_p95": 15000
    }
}


# Test data configuration
TEST_DATA_CONFIG = {
    "user_profiles": {
        "young_professional": {
            "age_range": (25, 35),
            "income_range": (50000, 150000),
            "investment_experience": ["beginner", "intermediate"],
            "risk_tolerance": ["conservative", "moderate"],
            "goals": ["emergency_fund", "house", "retirement"]
        },
        "family_planner": {
            "age_range": (35, 50),
            "income_range": (75000, 250000),
            "investment_experience": ["intermediate", "advanced"],
            "risk_tolerance": ["moderate", "aggressive"],
            "goals": ["education", "retirement", "estate_planning"]
        },
        "pre_retiree": {
            "age_range": (50, 65),
            "income_range": (100000, 500000),
            "investment_experience": ["advanced"],
            "risk_tolerance": ["conservative", "moderate"],
            "goals": ["retirement", "estate_planning", "healthcare"]
        },
        "high_net_worth": {
            "age_range": (40, 70),
            "income_range": (500000, 5000000),
            "investment_experience": ["advanced"],
            "risk_tolerance": ["moderate", "aggressive"],
            "goals": ["wealth_preservation", "tax_optimization", "philanthropy"]
        }
    },
    "market_scenarios": {
        "bull_market": {
            "annual_return": (0.08, 0.15),
            "volatility": (0.10, 0.15)
        },
        "bear_market": {
            "annual_return": (-0.20, -0.05),
            "volatility": (0.20, 0.35)
        },
        "sideways_market": {
            "annual_return": (-0.02, 0.05),
            "volatility": (0.08, 0.12)
        },
        "high_volatility": {
            "annual_return": (-0.10, 0.20),
            "volatility": (0.25, 0.40)
        }
    },
    "portfolio_templates": {
        "conservative": {
            "stocks": 30,
            "bonds": 60,
            "cash": 10
        },
        "moderate": {
            "stocks": 60,
            "bonds": 30,
            "cash": 10
        },
        "aggressive": {
            "stocks": 80,
            "bonds": 15,
            "cash": 5
        }
    }
}