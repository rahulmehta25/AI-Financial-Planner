#!/usr/bin/env python3
"""
Comprehensive Monitoring Setup Script
Sets up the entire monitoring infrastructure for the Financial Planning Data Platform
"""

import os
import sys
import json
import yaml
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringSetup:
    """Setup and configure the complete monitoring infrastructure"""
    
    def __init__(self, config_path: str = "monitoring_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.base_dir = Path(__file__).parent
        
    def load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            sys.exit(1)
    
    def setup_directories(self):
        """Create necessary directories for monitoring"""
        directories = [
            "prometheus/rules",
            "grafana/dashboards",
            "grafana/datasources",
            "grafana/plugins",
            "alertmanager",
            "blackbox",
            "snmp",
            "nginx",
            "loki",
            "promtail",
            "exporters/financial-metrics"
        ]
        
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
    
    def setup_prometheus_config(self):
        """Setup Prometheus configuration"""
        logger.info("Setting up Prometheus configuration...")
        
        # Prometheus config is already created, just validate
        prometheus_config_path = self.base_dir / "prometheus" / "prometheus.yml"
        if prometheus_config_path.exists():
            logger.info("Prometheus configuration already exists")
        else:
            logger.error("Prometheus configuration not found!")
            return False
        
        # Setup alerting rules
        rules_path = self.base_dir / "prometheus" / "rules" / "alerting_rules.yml"
        if rules_path.exists():
            logger.info("Alerting rules already exist")
        else:
            logger.error("Alerting rules not found!")
            return False
        
        return True
    
    def setup_grafana_config(self):
        """Setup Grafana configuration"""
        logger.info("Setting up Grafana configuration...")
        
        # Create datasource configuration
        datasources_config = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": "http://prometheus:9090",
                    "isDefault": True,
                    "editable": True
                },
                {
                    "name": "Loki",
                    "type": "loki",
                    "access": "proxy",
                    "url": "http://loki:3100",
                    "editable": True
                },
                {
                    "name": "Jaeger",
                    "type": "jaeger",
                    "access": "proxy",
                    "url": "http://jaeger:16686",
                    "editable": True
                }
            ]
        }
        
        datasources_path = self.base_dir / "grafana" / "datasources" / "datasources.yml"
        with open(datasources_path, 'w') as f:
            yaml.dump(datasources_config, f)
        
        # Create dashboard provisioning configuration
        dashboard_config = {
            "apiVersion": 1,
            "providers": [
                {
                    "name": "default",
                    "orgId": 1,
                    "folder": "",
                    "type": "file",
                    "disableDeletion": False,
                    "editable": True,
                    "updateIntervalSeconds": 10,
                    "allowUiUpdates": True,
                    "options": {
                        "path": "/etc/grafana/provisioning/dashboards"
                    }
                }
            ]
        }
        
        dashboard_provisioning_path = self.base_dir / "grafana" / "dashboards" / "dashboards.yml"
        with open(dashboard_provisioning_path, 'w') as f:
            yaml.dump(dashboard_config, f)
        
        logger.info("Grafana configuration created")
        return True
    
    def setup_alertmanager_config(self):
        """Setup AlertManager configuration"""
        logger.info("Setting up AlertManager configuration...")
        
        email_config = self.config.get('alerting', {}).get('email', {})
        slack_config = self.config.get('alerting', {}).get('slack', {})
        pagerduty_config = self.config.get('alerting', {}).get('pagerduty', {})
        
        alertmanager_config = {
            "global": {
                "smtp_smarthost": f"{email_config.get('smtp_server', 'localhost')}:{email_config.get('smtp_port', 587)}",
                "smtp_from": email_config.get('from_address', 'alerts@company.com'),
                "smtp_auth_username": email_config.get('username', ''),
                "smtp_auth_password": email_config.get('password', ''),
                "smtp_require_tls": email_config.get('use_tls', True)
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "default",
                "routes": [
                    {
                        "match": {"severity": "critical"},
                        "receiver": "critical-alerts"
                    },
                    {
                        "match": {"severity": "warning"},
                        "receiver": "warning-alerts"
                    }
                ]
            },
            "receivers": [
                {
                    "name": "default",
                    "email_configs": [
                        {
                            "to": email_config.get('to_addresses', ['admin@company.com'])[0],
                            "subject": "Alert: {{ .GroupLabels.alertname }}",
                            "body": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                        }
                    ]
                },
                {
                    "name": "critical-alerts",
                    "email_configs": [
                        {
                            "to": ', '.join(email_config.get('to_addresses', ['admin@company.com'])),
                            "subject": "CRITICAL: {{ .GroupLabels.alertname }}",
                            "body": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                        }
                    ]
                },
                {
                    "name": "warning-alerts",
                    "email_configs": [
                        {
                            "to": email_config.get('to_addresses', ['admin@company.com'])[0],
                            "subject": "WARNING: {{ .GroupLabels.alertname }}",
                            "body": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                        }
                    ]
                }
            ]
        }
        
        # Add Slack configuration if available
        if slack_config.get('enabled') and slack_config.get('bot_token'):
            for receiver in alertmanager_config['receivers']:
                receiver['slack_configs'] = [
                    {
                        "api_url": f"https://hooks.slack.com/services/{slack_config['bot_token']}",
                        "channel": slack_config.get('channels', {}).get('critical', '#alerts'),
                        "title": "{{ .GroupLabels.alertname }}",
                        "text": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                    }
                ]
        
        # Add PagerDuty configuration if available
        if pagerduty_config.get('enabled') and pagerduty_config.get('api_key'):
            for receiver in alertmanager_config['receivers']:
                if receiver['name'] == 'critical-alerts':
                    receiver['pagerduty_configs'] = [
                        {
                            "service_key": pagerduty_config['api_key'],
                            "description": "{{ .GroupLabels.alertname }}"
                        }
                    ]
        
        alertmanager_path = self.base_dir / "alertmanager" / "alertmanager.yml"
        with open(alertmanager_path, 'w') as f:
            yaml.dump(alertmanager_config, f)
        
        logger.info("AlertManager configuration created")
        return True
    
    def setup_blackbox_config(self):
        """Setup Blackbox Exporter configuration"""
        logger.info("Setting up Blackbox Exporter configuration...")
        
        blackbox_config = {
            "modules": {
                "http_2xx": {
                    "prober": "http",
                    "timeout": "5s",
                    "http": {
                        "valid_http_versions": ["HTTP/1.1", "HTTP/2.0"],
                        "valid_status_codes": [],
                        "method": "GET",
                        "follow_redirects": True,
                        "fail_if_ssl": False,
                        "fail_if_not_ssl": False
                    }
                },
                "http_post_2xx": {
                    "prober": "http",
                    "timeout": "5s",
                    "http": {
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": "{}"
                    }
                },
                "tcp_connect": {
                    "prober": "tcp",
                    "timeout": "5s"
                },
                "icmp": {
                    "prober": "icmp",
                    "timeout": "5s",
                    "icmp": {
                        "preferred_ip_protocol": "ip4"
                    }
                },
                "ssl_expire": {
                    "prober": "tcp",
                    "timeout": "5s",
                    "tcp": {
                        "query_response": [
                            {
                                "expect": "^SSH-2.0-"
                            }
                        ],
                        "tls": True,
                        "tls_config": {
                            "insecure_skip_verify": False
                        }
                    }
                }
            }
        }
        
        blackbox_path = self.base_dir / "blackbox" / "blackbox.yml"
        with open(blackbox_path, 'w') as f:
            yaml.dump(blackbox_config, f)
        
        logger.info("Blackbox Exporter configuration created")
        return True
    
    def setup_loki_config(self):
        """Setup Loki configuration"""
        logger.info("Setting up Loki configuration...")
        
        loki_config = {
            "auth_enabled": False,
            "server": {
                "http_listen_port": 3100
            },
            "ingester": {
                "lifecycler": {
                    "address": "127.0.0.1",
                    "ring": {
                        "kvstore": {
                            "store": "inmemory"
                        },
                        "replication_factor": 1
                    }
                }
            },
            "schema_config": {
                "configs": [
                    {
                        "from": "2020-10-24",
                        "store": "boltdb-shipper",
                        "object_store": "filesystem",
                        "schema": "v11",
                        "index": {
                            "prefix": "index_",
                            "period": "24h"
                        }
                    }
                ]
            },
            "storage_config": {
                "boltdb_shipper": {
                    "active_index_directory": "/tmp/loki/boltdb-shipper-active",
                    "cache_location": "/tmp/loki/boltdb-shipper-cache",
                    "shared_store": "filesystem"
                },
                "filesystem": {
                    "directory": "/tmp/loki/chunks"
                }
            },
            "limits_config": {
                "reject_old_samples": True,
                "reject_old_samples_max_age": "168h"
            },
            "chunk_store_config": {
                "max_look_back_period": "0s"
            },
            "table_manager": {
                "retention_deletes_enabled": False,
                "retention_period": "0s"
            }
        }
        
        loki_path = self.base_dir / "loki" / "loki-config.yml"
        with open(loki_path, 'w') as f:
            yaml.dump(loki_config, f)
        
        logger.info("Loki configuration created")
        return True
    
    def setup_promtail_config(self):
        """Setup Promtail configuration"""
        logger.info("Setting up Promtail configuration...")
        
        promtail_config = {
            "server": {
                "http_listen_port": 9080,
                "grpc_listen_port": 0
            },
            "positions": {
                "filename": "/tmp/positions.yaml"
            },
            "clients": [
                {
                    "url": "http://loki:3100/loki/api/v1/push"
                }
            ],
            "scrape_configs": [
                {
                    "job_name": "containers",
                    "static_configs": [
                        {
                            "targets": ["localhost"],
                            "labels": {
                                "job": "containerlogs",
                                "__path__": "/var/lib/docker/containers/*/*log"
                            }
                        }
                    ],
                    "pipeline_stages": [
                        {
                            "json": {
                                "expressions": {
                                    "output": "log",
                                    "stream": "stream",
                                    "attrs": ""
                                }
                            }
                        },
                        {
                            "json": {
                                "expressions": {
                                    "tag": "attrs.tag"
                                },
                                "source": "attrs"
                            }
                        },
                        {
                            "regex": {
                                "expression": "^k8s_(?P<container>[^_]+)_(?P<pod>[^_]+)_(?P<namespace>[^_]+)",
                                "source": "tag"
                            }
                        },
                        {
                            "timestamp": {
                                "source": "time",
                                "format": "RFC3339Nano"
                            }
                        },
                        {
                            "labels": {
                                "stream": "",
                                "container": "",
                                "pod": "",
                                "namespace": ""
                            }
                        },
                        {
                            "output": {
                                "source": "output"
                            }
                        }
                    ]
                },
                {
                    "job_name": "system",
                    "static_configs": [
                        {
                            "targets": ["localhost"],
                            "labels": {
                                "job": "varlogs",
                                "__path__": "/var/log/*log"
                            }
                        }
                    ]
                }
            ]
        }
        
        promtail_path = self.base_dir / "promtail" / "promtail-config.yml"
        with open(promtail_path, 'w') as f:
            yaml.dump(promtail_config, f)
        
        logger.info("Promtail configuration created")
        return True
    
    def setup_custom_exporter(self):
        """Setup custom financial metrics exporter"""
        logger.info("Setting up custom financial metrics exporter...")
        
        exporter_dir = self.base_dir / "exporters" / "financial-metrics"
        exporter_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Dockerfile for the custom exporter
        dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9200

CMD ["python", "exporter.py"]
"""
        
        with open(exporter_dir / "Dockerfile", 'w') as f:
            f.write(dockerfile_content)
        
        # Create requirements.txt
        requirements_content = """
prometheus_client==0.15.0
psycopg2-binary==2.9.5
redis==4.5.1
pyyaml==6.0
sqlalchemy==1.4.46
pandas==1.5.2
"""
        
        with open(exporter_dir / "requirements.txt", 'w') as f:
            f.write(requirements_content)
        
        # Create basic exporter configuration
        exporter_config = {
            "metrics": {
                "business_active_users": {
                    "query": "SELECT COUNT(DISTINCT user_id) FROM user_sessions WHERE last_activity >= NOW() - INTERVAL '30 days'",
                    "type": "gauge",
                    "description": "Number of active users in the last 30 days"
                },
                "business_daily_transactions": {
                    "query": "SELECT COUNT(*) FROM transactions WHERE date = CURRENT_DATE",
                    "type": "gauge",
                    "description": "Number of transactions today"
                },
                "business_portfolio_value": {
                    "query": "SELECT SUM(current_value) FROM portfolios WHERE is_active = true",
                    "type": "gauge",
                    "description": "Total portfolio value"
                }
            }
        }
        
        with open(exporter_dir / "config.yml", 'w') as f:
            yaml.dump(exporter_config, f)
        
        logger.info("Custom financial metrics exporter setup completed")
        return True
    
    def setup_nginx_config(self):
        """Setup Nginx reverse proxy configuration"""
        logger.info("Setting up Nginx configuration...")
        
        nginx_config = """
events {
    worker_connections 1024;
}

http {
    upstream prometheus {
        server prometheus:9090;
    }

    upstream grafana {
        server grafana:3000;
    }

    upstream alertmanager {
        server alertmanager:9093;
    }

    server {
        listen 80;
        server_name monitoring.financial-planning.local;

        location /prometheus/ {
            proxy_pass http://prometheus/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location / {
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /alertmanager/ {
            proxy_pass http://alertmanager/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
"""
        
        nginx_path = self.base_dir / "nginx" / "nginx.conf"
        with open(nginx_path, 'w') as f:
            f.write(nginx_config)
        
        logger.info("Nginx configuration created")
        return True
    
    def validate_docker_compose(self):
        """Validate Docker Compose configuration"""
        logger.info("Validating Docker Compose configuration...")
        
        compose_file = self.base_dir / "docker-compose.monitoring.yml"
        if not compose_file.exists():
            logger.error("Docker Compose file not found!")
            return False
        
        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "config"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Docker Compose configuration is valid")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker Compose validation failed: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("Docker Compose command not found. Please install Docker Compose.")
            return False
    
    def deploy_monitoring_stack(self, environment: str = "development"):
        """Deploy the monitoring stack"""
        logger.info(f"Deploying monitoring stack for {environment} environment...")
        
        compose_file = self.base_dir / "docker-compose.monitoring.yml"
        env_file = self.base_dir / f".env.{environment}"
        
        # Create environment file if it doesn't exist
        if not env_file.exists():
            self.create_env_file(env_file, environment)
        
        try:
            # Pull images
            logger.info("Pulling Docker images...")
            subprocess.run(
                ["docker-compose", "-f", str(compose_file), "pull"],
                check=True
            )
            
            # Start services
            logger.info("Starting monitoring services...")
            subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d"],
                check=True
            )
            
            logger.info("Monitoring stack deployed successfully!")
            
            # Wait for services to be ready
            self.wait_for_services()
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to deploy monitoring stack: {e}")
            return False
    
    def create_env_file(self, env_file: Path, environment: str):
        """Create environment file with default values"""
        env_content = f"""
# Environment: {environment}
GRAFANA_ADMIN_PASSWORD=admin123
POSTGRES_USER=financial_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=financial_planning
REDIS_PASSWORD=redis_password
ES_USERNAME=elastic
ES_PASSWORD=elastic_password
EMAIL_USERNAME=alerts@company.com
EMAIL_PASSWORD=email_password
SLACK_BOT_TOKEN=xoxb-your-slack-token
PAGERDUTY_API_KEY=your-pagerduty-key
PAGERDUTY_SERVICE_ID=your-service-id
PAGERDUTY_ESCALATION_POLICY_ID=your-escalation-policy
WEBHOOK_URL=https://your-webhook-url.com
WEBHOOK_TOKEN=your-webhook-token
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_FROM_NUMBER=+1234567890
ADMIN_PHONE_NUMBER=+1234567890
GRAFANA_API_KEY=your-grafana-api-key
MARKET_DATA_API_KEY=your-market-data-key
BANKING_API_KEY=your-banking-api-key
AIRFLOW_USERNAME=airflow
AIRFLOW_PASSWORD=airflow_password
AIRFLOW_DB_PASSWORD=airflow_db_password
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Created environment file: {env_file}")
        logger.warning("Please update the environment file with your actual credentials!")
    
    def wait_for_services(self):
        """Wait for monitoring services to be ready"""
        services = [
            ("Prometheus", "http://localhost:9090/-/ready", 30),
            ("Grafana", "http://localhost:3000/api/health", 60),
            ("AlertManager", "http://localhost:9093/-/ready", 30)
        ]
        
        for service_name, url, timeout in services:
            logger.info(f"Waiting for {service_name} to be ready...")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    import requests
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"{service_name} is ready!")
                        break
                except Exception:
                    time.sleep(2)
            else:
                logger.warning(f"{service_name} may not be ready within {timeout} seconds")
    
    def setup_all(self, environment: str = "development"):
        """Setup the complete monitoring infrastructure"""
        logger.info("Starting complete monitoring setup...")
        
        steps = [
            ("Creating directories", self.setup_directories),
            ("Setting up Prometheus", self.setup_prometheus_config),
            ("Setting up Grafana", self.setup_grafana_config),
            ("Setting up AlertManager", self.setup_alertmanager_config),
            ("Setting up Blackbox Exporter", self.setup_blackbox_config),
            ("Setting up Loki", self.setup_loki_config),
            ("Setting up Promtail", self.setup_promtail_config),
            ("Setting up custom exporter", self.setup_custom_exporter),
            ("Setting up Nginx", self.setup_nginx_config),
            ("Validating Docker Compose", self.validate_docker_compose)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Executing: {step_name}")
            if not step_func():
                logger.error(f"Failed: {step_name}")
                return False
            logger.info(f"Completed: {step_name}")
        
        # Deploy if requested
        if environment:
            if not self.deploy_monitoring_stack(environment):
                logger.error("Failed to deploy monitoring stack")
                return False
        
        logger.info("Monitoring setup completed successfully!")
        self.print_access_info()
        return True
    
    def print_access_info(self):
        """Print access information for monitoring services"""
        print("\n" + "="*60)
        print("MONITORING SERVICES ACCESS INFORMATION")
        print("="*60)
        print("Grafana Dashboard:     http://localhost:3000")
        print("  - Username: admin")
        print("  - Password: admin123 (change in .env file)")
        print()
        print("Prometheus:            http://localhost:9090")
        print("AlertManager:          http://localhost:9093")
        print("Jaeger Tracing:        http://localhost:16686")
        print()
        print("Service Health Checks:")
        print("  - Node Exporter:     http://localhost:9100/metrics")
        print("  - Postgres Exporter: http://localhost:9187/metrics")
        print("  - Redis Exporter:    http://localhost:9121/metrics")
        print("  - Custom Exporter:   http://localhost:9200/metrics")
        print()
        print("Note: Make sure to update credentials in the .env file!")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Setup Financial Planning Monitoring Infrastructure")
    parser.add_argument("--config", default="monitoring_config.yaml", help="Configuration file path")
    parser.add_argument("--environment", default="development", help="Environment to deploy")
    parser.add_argument("--no-deploy", action="store_true", help="Skip deployment")
    
    args = parser.parse_args()
    
    setup = MonitoringSetup(args.config)
    
    environment = None if args.no_deploy else args.environment
    success = setup.setup_all(environment)
    
    if success:
        logger.info("Monitoring setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("Monitoring setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()