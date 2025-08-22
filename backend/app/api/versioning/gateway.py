"""
API Gateway Configuration for Version Routing
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import yaml
import json

from .models import APIVersion, ABTestConfig
from .manager import VersionManager

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies for version routing"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    PER_VERSION = "per_version"
    PER_CLIENT = "per_client" 
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


@dataclass
class ServiceUpstream:
    """Service upstream configuration"""
    name: str
    host: str
    port: int
    weight: int = 100
    max_fails: int = 3
    fail_timeout: str = "30s"
    health_check: bool = True
    health_check_path: str = "/health"
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class VersionRoute:
    """Version-specific routing configuration"""
    version: str
    path_prefix: str
    upstreams: List[ServiceUpstream]
    load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    rate_limits: Dict[str, int] = None
    timeout: str = "30s"
    retries: int = 3
    circuit_breaker: bool = True
    cache_enabled: bool = False
    cache_ttl: str = "5m"
    
    def __post_init__(self):
        if self.rate_limits is None:
            self.rate_limits = {
                "requests_per_minute": 1000,
                "requests_per_hour": 10000
            }


@dataclass
class ABTestRoute:
    """A/B testing route configuration"""
    test_name: str
    control_version: str
    treatment_version: str
    traffic_split: float  # 0.0 to 1.0
    user_segments: List[str] = None
    header_based_routing: bool = True
    sticky_sessions: bool = True
    
    def __post_init__(self):
        if self.user_segments is None:
            self.user_segments = []


class GatewayConfigGenerator:
    """Generate API Gateway configurations for different platforms"""
    
    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
    
    def generate_nginx_config(
        self,
        routes: List[VersionRoute],
        ab_tests: List[ABTestRoute] = None
    ) -> str:
        """Generate NGINX configuration for version routing"""
        
        config_parts = [
            "# API Gateway Configuration - Generated",
            "# Version routing for Financial Planning API",
            "",
            "upstream financial_api_v1 {",
        ]
        
        # Generate upstreams for each version
        for route in routes:
            config_parts.extend([
                f"upstream financial_api_{route.version.replace('.', '_')} {{",
                f"    {route.load_balancing.value};",
            ])
            
            for upstream in route.upstreams:
                config_parts.append(
                    f"    server {upstream.host}:{upstream.port} "
                    f"weight={upstream.weight} "
                    f"max_fails={upstream.max_fails} "
                    f"fail_timeout={upstream.fail_timeout};"
                )
            
            config_parts.extend([
                "    ",
                f"    # Health checks",
                f"    health_check uri={upstream.health_check_path} interval=10s;",
                "}",
                ""
            ])
        
        # Main server configuration
        config_parts.extend([
            "server {",
            "    listen 80;",
            "    server_name api.financial-planning.com;",
            "",
            "    # Rate limiting zones",
            "    limit_req_zone $binary_remote_addr zone=api_rate:10m rate=100r/m;",
            "    limit_req_zone $http_x_api_version zone=version_rate:10m rate=1000r/m;",
            "",
            "    # Logging",
            "    access_log /var/log/nginx/api_access.log combined;",
            "    error_log /var/log/nginx/api_error.log warn;",
            "",
            "    # Default headers",
            "    add_header X-Gateway-Version '1.0' always;",
            "    add_header X-Content-Type-Options nosniff always;",
            "",
        ])
        
        # Add version routing
        for route in routes:
            version_major = route.version.split('.')[0]
            config_parts.extend([
                f"    # Route for API version {route.version}",
                f"    location {route.path_prefix} {{",
                f"        # Rate limiting",
                f"        limit_req zone=version_rate burst=50 nodelay;",
                "",
                f"        # Proxy settings", 
                f"        proxy_pass http://financial_api_{route.version.replace('.', '_')};",
                f"        proxy_set_header Host $host;",
                f"        proxy_set_header X-Real-IP $remote_addr;",
                f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                f"        proxy_set_header X-Forwarded-Proto $scheme;",
                f"        proxy_set_header X-API-Version '{route.version}';",
                "",
                f"        # Timeouts",
                f"        proxy_connect_timeout {route.timeout};",
                f"        proxy_send_timeout {route.timeout};",
                f"        proxy_read_timeout {route.timeout};",
                "",
                f"        # Retries",
                f"        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;",
                f"        proxy_next_upstream_tries {route.retries};",
                "",
            ])
            
            # Add caching if enabled
            if route.cache_enabled:
                config_parts.extend([
                    f"        # Caching",
                    f"        proxy_cache api_cache;",
                    f"        proxy_cache_valid 200 {route.cache_ttl};",
                    f"        proxy_cache_key $scheme$proxy_host$request_uri$http_x_api_version;",
                    "",
                ])
            
            config_parts.extend([
                "    }",
                ""
            ])
        
        # Add A/B testing routes
        if ab_tests:
            config_parts.extend([
                "    # A/B Testing Routes",
                ""
            ])
            
            for test in ab_tests:
                config_parts.extend([
                    f"    # A/B Test: {test.test_name}",
                    f"    location @ab_test_{test.test_name} {{",
                    f"        # Route based on user segment",
                    f"        if ($http_x_user_segment ~ \"{test.user_segments[0] if test.user_segments else 'all'}\") {{",
                    f"            set $ab_version '{test.treatment_version}';",
                    f"        }}",
                    f"        ",
                    f"        # Default to control version",
                    f"        set $ab_version '{test.control_version}';",
                    f"        ",
                    f"        proxy_pass http://financial_api_${{ab_version}};",
                    f"    }}",
                    ""
                ])
        
        config_parts.extend([
            "    # Health check endpoint",
            "    location /health {",
            "        access_log off;",
            "        return 200 'Gateway Healthy';",
            "        add_header Content-Type text/plain;",
            "    }",
            "",
            "    # Default route (latest version)",
            "    location / {",
            "        return 301 /api/v2$request_uri;",
            "    }",
            "}",
        ])
        
        return "\n".join(config_parts)
    
    def generate_kong_config(
        self,
        routes: List[VersionRoute],
        ab_tests: List[ABTestRoute] = None
    ) -> Dict[str, Any]:
        """Generate Kong Gateway configuration"""
        
        config = {
            "_format_version": "3.0",
            "services": [],
            "routes": [],
            "plugins": []
        }
        
        # Generate services for each version
        for route in routes:
            service_name = f"financial-api-{route.version.replace('.', '-')}"
            
            # Create service
            service = {
                "name": service_name,
                "protocol": "http",
                "host": route.upstreams[0].host,  # Use first upstream as primary
                "port": route.upstreams[0].port,
                "path": "/",
                "connect_timeout": 5000,
                "read_timeout": 30000,
                "write_timeout": 30000,
                "retries": route.retries
            }
            config["services"].append(service)
            
            # Create route
            route_config = {
                "name": f"api-{route.version.replace('.', '-')}",
                "service": {"name": service_name},
                "paths": [route.path_prefix],
                "strip_path": False,
                "preserve_host": True
            }
            config["routes"].append(route_config)
            
            # Add rate limiting plugin
            rate_limit_plugin = {
                "name": "rate-limiting",
                "service": {"name": service_name},
                "config": {
                    "minute": route.rate_limits.get("requests_per_minute", 1000),
                    "hour": route.rate_limits.get("requests_per_hour", 10000),
                    "policy": "redis",
                    "fault_tolerant": True,
                    "hide_client_headers": False
                }
            }
            config["plugins"].append(rate_limit_plugin)
            
            # Add request transformer for version headers
            transformer_plugin = {
                "name": "request-transformer",
                "service": {"name": service_name},
                "config": {
                    "add": {
                        "headers": [f"X-API-Version:{route.version}"]
                    }
                }
            }
            config["plugins"].append(transformer_plugin)
            
            # Add response transformer for deprecation warnings
            version_obj = self.version_manager.get_version(route.version)
            if version_obj and version_obj.is_deprecated:
                response_transformer = {
                    "name": "response-transformer",
                    "service": {"name": service_name},
                    "config": {
                        "add": {
                            "headers": [
                                "X-API-Deprecated:true",
                                f"X-API-Deprecation-Date:{version_obj.deprecation_date.isoformat() if version_obj.deprecation_date else ''}",
                                f"X-API-Retirement-Date:{version_obj.retirement_date.isoformat() if version_obj.retirement_date else ''}"
                            ]
                        }
                    }
                }
                config["plugins"].append(response_transformer)
        
        # Add global plugins
        global_plugins = [
            {
                "name": "cors",
                "config": {
                    "origins": ["*"],
                    "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
                    "headers": ["Accept", "Accept-Version", "Content-Length", "Content-MD5", "Content-Type", "Date", "X-Auth-Token", "X-API-Version"],
                    "exposed_headers": ["X-Auth-Token", "X-API-Version", "X-API-Deprecated", "X-API-Retirement-Date"],
                    "credentials": True,
                    "max_age": 3600
                }
            },
            {
                "name": "prometheus",
                "config": {
                    "per_consumer": True,
                    "status_code_metrics": True,
                    "latency_metrics": True,
                    "bandwidth_metrics": True,
                    "upstream_health_metrics": True
                }
            }
        ]
        
        config["plugins"].extend(global_plugins)
        
        return config
    
    def generate_envoy_config(self, routes: List[VersionRoute]) -> Dict[str, Any]:
        """Generate Envoy Proxy configuration"""
        
        clusters = []
        virtual_hosts = []
        
        # Generate clusters for each version
        for route in routes:
            cluster_name = f"financial_api_{route.version.replace('.', '_')}"
            
            # Create cluster endpoints
            endpoints = []
            for upstream in route.upstreams:
                endpoints.append({
                    "endpoint": {
                        "address": {
                            "socket_address": {
                                "address": upstream.host,
                                "port_value": upstream.port
                            }
                        }
                    },
                    "load_balancing_weight": upstream.weight
                })
            
            cluster = {
                "name": cluster_name,
                "type": "STRICT_DNS",
                "lb_policy": route.load_balancing.value.upper(),
                "load_assignment": {
                    "cluster_name": cluster_name,
                    "endpoints": [{"lb_endpoints": endpoints}]
                },
                "health_checks": [
                    {
                        "timeout": "5s",
                        "interval": "10s",
                        "unhealthy_threshold": upstream.max_fails,
                        "healthy_threshold": 2,
                        "http_health_check": {
                            "path": upstream.health_check_path,
                            "expected_statuses": [{"start": 200, "end": 299}]
                        }
                    }
                ] if route.upstreams[0].health_check else []
            }
            clusters.append(cluster)
            
            # Create virtual host route
            route_config = {
                "match": {"prefix": route.path_prefix},
                "route": {
                    "cluster": cluster_name,
                    "timeout": route.timeout,
                    "retry_policy": {
                        "retry_on": "5xx,reset,connect-failure,refused-stream",
                        "num_retries": route.retries
                    }
                },
                "request_headers_to_add": [
                    {
                        "header": {"key": "x-api-version", "value": route.version},
                        "append": False
                    }
                ]
            }
            
            virtual_hosts.append({
                "name": f"api_v{route.version.split('.')[0]}",
                "domains": ["*"],
                "routes": [route_config]
            })
        
        config = {
            "static_resources": {
                "clusters": clusters,
                "listeners": [
                    {
                        "name": "api_listener",
                        "address": {
                            "socket_address": {
                                "address": "0.0.0.0",
                                "port_value": 8080
                            }
                        },
                        "filter_chains": [
                            {
                                "filters": [
                                    {
                                        "name": "envoy.filters.network.http_connection_manager",
                                        "typed_config": {
                                            "@type": "type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager",
                                            "stat_prefix": "api_gateway",
                                            "codec_type": "AUTO",
                                            "route_config": {
                                                "name": "api_routes",
                                                "virtual_hosts": virtual_hosts
                                            },
                                            "http_filters": [
                                                {
                                                    "name": "envoy.filters.http.ratelimit",
                                                    "typed_config": {
                                                        "@type": "type.googleapis.com/envoy.extensions.filters.http.ratelimit.v3.RateLimit",
                                                        "domain": "api_gateway",
                                                        "stage": 0,
                                                        "timeout": "0.25s"
                                                    }
                                                },
                                                {
                                                    "name": "envoy.filters.http.router"
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        return config
    
    def generate_kubernetes_ingress(self, routes: List[VersionRoute]) -> Dict[str, Any]:
        """Generate Kubernetes Ingress configuration"""
        
        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "financial-api-versioned",
                "namespace": "financial-planning",
                "annotations": {
                    "nginx.ingress.kubernetes.io/rewrite-target": "/$2",
                    "nginx.ingress.kubernetes.io/use-regex": "true",
                    "nginx.ingress.kubernetes.io/rate-limit": "100",
                    "nginx.ingress.kubernetes.io/rate-limit-window": "1m",
                    "nginx.ingress.kubernetes.io/configuration-snippet": """
                        more_set_headers "X-API-Gateway: kubernetes-ingress";
                        more_set_headers "X-Content-Type-Options: nosniff";
                    """
                }
            },
            "spec": {
                "ingressClassName": "nginx",
                "rules": [
                    {
                        "host": "api.financial-planning.com",
                        "http": {
                            "paths": []
                        }
                    }
                ]
            }
        }
        
        # Add paths for each version
        for route in routes:
            version_major = route.version.split('.')[0]
            service_name = f"financial-api-v{version_major}"
            
            path_config = {
                "path": f"{route.path_prefix}(/|$)(.*)",
                "pathType": "Prefix",
                "backend": {
                    "service": {
                        "name": service_name,
                        "port": {
                            "number": 80
                        }
                    }
                }
            }
            
            ingress["spec"]["rules"][0]["http"]["paths"].append(path_config)
        
        return ingress
    
    def generate_istio_virtual_service(self, routes: List[VersionRoute], ab_tests: List[ABTestRoute] = None) -> Dict[str, Any]:
        """Generate Istio VirtualService configuration"""
        
        virtual_service = {
            "apiVersion": "networking.istio.io/v1beta1",
            "kind": "VirtualService",
            "metadata": {
                "name": "financial-api-versioned",
                "namespace": "financial-planning"
            },
            "spec": {
                "hosts": ["api.financial-planning.com"],
                "gateways": ["financial-api-gateway"],
                "http": []
            }
        }
        
        # Add A/B testing routes first (higher priority)
        if ab_tests:
            for test in ab_tests:
                ab_route = {
                    "match": [
                        {
                            "uri": {"prefix": "/api/"},
                            "headers": {
                                "x-user-segment": {
                                    "regex": "|".join(test.user_segments) if test.user_segments else ".*"
                                }
                            }
                        }
                    ],
                    "route": [
                        {
                            "destination": {
                                "host": f"financial-api-v{test.control_version.split('.')[0]}",
                                "subset": test.control_version
                            },
                            "weight": int((1 - test.traffic_split) * 100)
                        },
                        {
                            "destination": {
                                "host": f"financial-api-v{test.treatment_version.split('.')[0]}",
                                "subset": test.treatment_version
                            },
                            "weight": int(test.traffic_split * 100)
                        }
                    ],
                    "headers": {
                        "request": {
                            "add": {
                                "x-ab-test": test.test_name,
                                "x-ab-variant": "{% if weight <= " + str(int(test.traffic_split * 100)) + " %}treatment{% else %}control{% endif %}"
                            }
                        }
                    }
                }
                virtual_service["spec"]["http"].append(ab_route)
        
        # Add regular version routes
        for route in routes:
            version_major = route.version.split('.')[0]
            
            route_config = {
                "match": [{"uri": {"prefix": route.path_prefix}}],
                "route": [{
                    "destination": {
                        "host": f"financial-api-v{version_major}",
                        "subset": route.version
                    }
                }],
                "headers": {
                    "request": {
                        "add": {
                            "x-api-version": route.version,
                            "x-gateway": "istio"
                        }
                    }
                },
                "fault": {
                    "delay": {
                        "percentage": {"value": 0.1},
                        "fixedDelay": "1s"
                    }
                } if route.circuit_breaker else None,
                "retries": {
                    "attempts": route.retries,
                    "perTryTimeout": route.timeout,
                    "retryOn": "5xx,reset,connect-failure,refused-stream"
                }
            }
            
            # Remove None values
            route_config = {k: v for k, v in route_config.items() if v is not None}
            virtual_service["spec"]["http"].append(route_config)
        
        return virtual_service
    
    def export_all_configs(self, output_dir: str = "config/gateway") -> Dict[str, str]:
        """Export all gateway configurations to files"""
        import os
        
        # Get current version routes
        supported_versions = self.version_manager.get_supported_versions()
        routes = []
        
        for version_obj in supported_versions:
            version_major = version_obj.version.split('.')[0]
            route = VersionRoute(
                version=version_obj.version,
                path_prefix=f"/api/v{version_major}",
                upstreams=[
                    ServiceUpstream(
                        name=f"financial-api-v{version_major}",
                        host=f"financial-api-v{version_major}-service",
                        port=8000
                    )
                ]
            )
            routes.append(route)
        
        # Get A/B tests
        ab_tests = []
        for test_config in self.version_manager.get_active_ab_tests():
            ab_test = ABTestRoute(
                test_name=test_config.test_name,
                control_version=test_config.from_version,
                treatment_version=test_config.to_version,
                traffic_split=test_config.traffic_percentage / 100.0
            )
            ab_tests.append(ab_test)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = {}
        
        # Generate configurations
        configs = {
            "nginx.conf": self.generate_nginx_config(routes, ab_tests),
            "kong.yaml": yaml.dump(self.generate_kong_config(routes, ab_tests), default_flow_style=False),
            "envoy.yaml": yaml.dump(self.generate_envoy_config(routes), default_flow_style=False),
            "k8s-ingress.yaml": yaml.dump(self.generate_kubernetes_ingress(routes), default_flow_style=False),
            "istio-virtualservice.yaml": yaml.dump(self.generate_istio_virtual_service(routes, ab_tests), default_flow_style=False)
        }
        
        # Write files
        for filename, content in configs.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            generated_files[filename] = filepath
            logger.info(f"Generated {filename} at {filepath}")
        
        return generated_files