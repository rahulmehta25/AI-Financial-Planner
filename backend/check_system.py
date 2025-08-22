#!/usr/bin/env python3
"""
Financial Planning System - System Diagnostic Script

This script automatically diagnoses common system issues and provides
recommendations for fixing them.

Usage:
    python3 check_system.py                    # Basic checks
    python3 check_system.py --verbose          # Detailed output
    python3 check_system.py --fix              # Attempt auto-fixes
    python3 check_system.py --export-report    # Generate report file
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import socket
import psutil
import shutil


class Colors:
    """Terminal color codes for output formatting"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class SystemDiagnostic:
    """Main system diagnostic class"""
    
    def __init__(self, verbose: bool = False, auto_fix: bool = False):
        self.verbose = verbose
        self.auto_fix = auto_fix
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {},
            'checks': [],
            'issues': [],
            'recommendations': [],
            'performance': {}
        }
        self.issues_found = 0
        self.fixes_applied = 0
        
    def log(self, message: str, level: str = "INFO", color: str = Colors.NC):
        """Log message with color and level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "WARNING": Colors.YELLOW,
            "ERROR": Colors.RED,
            "DEBUG": Colors.PURPLE
        }
        
        if level == "DEBUG" and not self.verbose:
            return
            
        level_color = level_colors.get(level, Colors.NC)
        print(f"{Colors.CYAN}[{timestamp}]{Colors.NC} {level_color}{level:<8}{Colors.NC} {color}{message}{Colors.NC}")
    
    def run_command(self, command: str, capture_output: bool = True, timeout: int = 30) -> Tuple[int, str, str]:
        """Run system command and return exit code, stdout, stderr"""
        try:
            if isinstance(command, str):
                command = command.split()
            
            result = subprocess.run(
                command, 
                capture_output=capture_output, 
                text=True, 
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except FileNotFoundError:
            return -1, "", f"Command not found: {command[0]}"
        except Exception as e:
            return -1, "", str(e)
    
    def check_system_info(self):
        """Gather basic system information"""
        self.log("Gathering system information...")
        
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': sys.version,
            'python_executable': sys.executable,
            'working_directory': os.getcwd(),
            'user': os.getenv('USER', 'unknown'),
            'home': os.path.expanduser('~')
        }
        
        # Memory information
        memory = psutil.virtual_memory()
        system_info['memory'] = {
            'total': memory.total,
            'available': memory.available,
            'percent_used': memory.percent,
            'total_gb': round(memory.total / (1024**3), 1),
            'available_gb': round(memory.available / (1024**3), 1)
        }
        
        # Disk information
        disk = psutil.disk_usage('.')
        system_info['disk'] = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent_used': round((disk.used / disk.total) * 100, 1),
            'total_gb': round(disk.total / (1024**3), 1),
            'free_gb': round(disk.free / (1024**3), 1)
        }
        
        # CPU information
        system_info['cpu'] = {
            'count': psutil.cpu_count(),
            'count_physical': psutil.cpu_count(logical=False),
            'percent_used': psutil.cpu_percent(interval=1)
        }
        
        self.results['system_info'] = system_info
        
        self.log(f"System: {system_info['platform']} {system_info['platform_release']}", "SUCCESS")
        self.log(f"Python: {system_info['python_version'].split()[0]}", "SUCCESS")
        self.log(f"Memory: {system_info['memory']['available_gb']:.1f}GB available of {system_info['memory']['total_gb']:.1f}GB", "SUCCESS")
        self.log(f"Disk: {system_info['disk']['free_gb']:.1f}GB free of {system_info['disk']['total_gb']:.1f}GB", "SUCCESS")
    
    def check_python_dependencies(self):
        """Check Python dependencies and versions"""
        self.log("Checking Python dependencies...")
        
        # Core requirements
        core_packages = {
            'fastapi': '0.68.0',
            'uvicorn': '0.15.0',
            'numpy': '1.21.0',
            'pydantic': '1.8.0',
            'sqlalchemy': '1.4.0',
            'psycopg2-binary': '2.9.0'
        }
        
        # Optional packages
        optional_packages = {
            'scipy': '1.7.0',
            'matplotlib': '3.4.0',
            'numba': '0.54.0',
            'reportlab': '3.6.0',
            'redis': '3.5.0',
            'celery': '5.2.0'
        }
        
        missing_core = []
        missing_optional = []
        
        for package, min_version in core_packages.items():
            try:
                __import__(package)
                self.log(f"✓ {package} available", "SUCCESS", Colors.GREEN)
            except ImportError:
                missing_core.append(package)
                self.log(f"✗ {package} missing (required)", "ERROR", Colors.RED)
                self.issues_found += 1
        
        for package, min_version in optional_packages.items():
            try:
                __import__(package)
                self.log(f"✓ {package} available (optional)", "SUCCESS", Colors.GREEN)
            except ImportError:
                missing_optional.append(package)
                self.log(f"⚠ {package} missing (optional)", "WARNING", Colors.YELLOW)
        
        # Record check results
        check_result = {
            'name': 'python_dependencies',
            'status': 'PASS' if not missing_core else 'FAIL',
            'missing_core': missing_core,
            'missing_optional': missing_optional,
            'details': f"Core: {len(core_packages) - len(missing_core)}/{len(core_packages)}, Optional: {len(optional_packages) - len(missing_optional)}/{len(optional_packages)}"
        }
        self.results['checks'].append(check_result)
        
        # Auto-fix if requested
        if missing_core and self.auto_fix:
            self.log("Attempting to install missing core packages...", "INFO")
            for package in missing_core:
                self.log(f"Installing {package}...", "INFO")
                exit_code, stdout, stderr = self.run_command([sys.executable, '-m', 'pip', 'install', package])
                if exit_code == 0:
                    self.log(f"Successfully installed {package}", "SUCCESS")
                    self.fixes_applied += 1
                else:
                    self.log(f"Failed to install {package}: {stderr}", "ERROR")
        
        return len(missing_core) == 0
    
    def check_port_availability(self):
        """Check if required ports are available"""
        self.log("Checking port availability...")
        
        required_ports = {
            8000: 'API Server',
            3000: 'Frontend/Grafana',
            5432: 'PostgreSQL',
            6379: 'Redis',
            9090: 'Prometheus',
            5050: 'pgAdmin'
        }
        
        port_issues = []
        
        for port, service in required_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                # Port is in use
                self.log(f"✗ Port {port} ({service}) is in use", "WARNING", Colors.YELLOW)
                port_issues.append({'port': port, 'service': service})
                
                # Try to identify what's using the port
                try:
                    for conn in psutil.net_connections():
                        if conn.laddr.port == port:
                            try:
                                process = psutil.Process(conn.pid)
                                self.log(f"  └─ Used by: {process.name()} (PID: {conn.pid})", "DEBUG")
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                self.log(f"  └─ Used by PID: {conn.pid}", "DEBUG")
                            break
                except Exception as e:
                    self.log(f"  └─ Could not identify process: {e}", "DEBUG")
                    
            else:
                self.log(f"✓ Port {port} ({service}) is available", "SUCCESS", Colors.GREEN)
        
        # Record check results
        check_result = {
            'name': 'port_availability',
            'status': 'WARNING' if port_issues else 'PASS',
            'port_conflicts': port_issues,
            'details': f"{len(port_issues)} ports in use out of {len(required_ports)} checked"
        }
        self.results['checks'].append(check_result)
        
        return len(port_issues) == 0
    
    def check_docker_status(self):
        """Check Docker installation and status"""
        self.log("Checking Docker status...")
        
        # Check Docker installation
        docker_installed = False
        docker_running = False
        compose_available = False
        
        exit_code, stdout, stderr = self.run_command(['docker', '--version'])
        if exit_code == 0:
            docker_installed = True
            version = stdout.strip()
            self.log(f"✓ {version}", "SUCCESS", Colors.GREEN)
            
            # Check if Docker daemon is running
            exit_code, stdout, stderr = self.run_command(['docker', 'info'])
            if exit_code == 0:
                docker_running = True
                self.log("✓ Docker daemon is running", "SUCCESS", Colors.GREEN)
            else:
                self.log("✗ Docker daemon is not running", "ERROR", Colors.RED)
                self.issues_found += 1
        else:
            self.log("✗ Docker is not installed", "ERROR", Colors.RED)
            self.issues_found += 1
        
        # Check Docker Compose
        exit_code, stdout, stderr = self.run_command(['docker-compose', '--version'])
        if exit_code == 0:
            compose_available = True
            version = stdout.strip()
            self.log(f"✓ {version}", "SUCCESS", Colors.GREEN)
        else:
            # Try docker compose (newer syntax)
            exit_code, stdout, stderr = self.run_command(['docker', 'compose', 'version'])
            if exit_code == 0:
                compose_available = True
                version = stdout.strip()
                self.log(f"✓ Docker Compose (integrated): {version}", "SUCCESS", Colors.GREEN)
            else:
                self.log("✗ Docker Compose is not available", "ERROR", Colors.RED)
                self.issues_found += 1
        
        # Record check results
        check_result = {
            'name': 'docker_status',
            'status': 'PASS' if (docker_installed and docker_running and compose_available) else 'FAIL',
            'docker_installed': docker_installed,
            'docker_running': docker_running,
            'compose_available': compose_available
        }
        self.results['checks'].append(check_result)
        
        return docker_installed and docker_running and compose_available
    
    def check_database_connectivity(self):
        """Check database connectivity and status"""
        self.log("Checking database connectivity...")
        
        # Check if database files exist
        db_files = [
            'demo_data/financial_data.db',
            '.env',
            'docker-compose.yml'
        ]
        
        missing_files = []
        for file in db_files:
            if not os.path.exists(file):
                missing_files.append(file)
                self.log(f"✗ Missing: {file}", "WARNING", Colors.YELLOW)
            else:
                self.log(f"✓ Found: {file}", "SUCCESS", Colors.GREEN)
        
        # Test database connection if Docker is available
        db_connection = False
        try:
            exit_code, stdout, stderr = self.run_command([
                'docker-compose', 'exec', '-T', 'postgres', 
                'pg_isready', '-U', 'financial_planning'
            ], timeout=10)
            
            if exit_code == 0:
                db_connection = True
                self.log("✓ Database connection successful", "SUCCESS", Colors.GREEN)
            else:
                self.log(f"✗ Database connection failed: {stderr}", "WARNING", Colors.YELLOW)
        except Exception as e:
            self.log(f"⚠ Could not test database connection: {e}", "DEBUG")
        
        # Record check results
        check_result = {
            'name': 'database_connectivity',
            'status': 'PASS' if not missing_files else 'WARNING',
            'missing_files': missing_files,
            'db_connection': db_connection
        }
        self.results['checks'].append(check_result)
        
        return len(missing_files) == 0
    
    def check_performance_indicators(self):
        """Check system performance indicators"""
        self.log("Checking performance indicators...")
        
        performance = {}
        
        # Memory check
        memory = psutil.virtual_memory()
        if memory.available < 1 * 1024**3:  # Less than 1GB
            self.log("⚠ Low memory: Less than 1GB available", "WARNING", Colors.YELLOW)
            performance['memory_warning'] = True
        else:
            self.log(f"✓ Memory OK: {memory.available / 1024**3:.1f}GB available", "SUCCESS", Colors.GREEN)
            performance['memory_warning'] = False
        
        # Disk space check
        disk = psutil.disk_usage('.')
        free_gb = disk.free / 1024**3
        if free_gb < 2:  # Less than 2GB
            self.log(f"⚠ Low disk space: {free_gb:.1f}GB free", "WARNING", Colors.YELLOW)
            performance['disk_warning'] = True
        else:
            self.log(f"✓ Disk space OK: {free_gb:.1f}GB free", "SUCCESS", Colors.GREEN)
            performance['disk_warning'] = False
        
        # CPU load check
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            self.log(f"⚠ High CPU usage: {cpu_percent:.1f}%", "WARNING", Colors.YELLOW)
            performance['cpu_warning'] = True
        else:
            self.log(f"✓ CPU usage OK: {cpu_percent:.1f}%", "SUCCESS", Colors.GREEN)
            performance['cpu_warning'] = False
        
        # Test numpy performance
        try:
            import numpy as np
            start_time = time.time()
            
            # Simple matrix multiplication benchmark
            size = 1000
            a = np.random.random((size, size))
            b = np.random.random((size, size))
            c = np.dot(a, b)
            
            elapsed = time.time() - start_time
            performance['numpy_benchmark'] = elapsed
            
            if elapsed < 2.0:
                self.log(f"✓ NumPy performance good: {elapsed:.2f}s", "SUCCESS", Colors.GREEN)
            else:
                self.log(f"⚠ NumPy performance slow: {elapsed:.2f}s", "WARNING", Colors.YELLOW)
        except ImportError:
            self.log("⚠ NumPy not available for performance test", "WARNING", Colors.YELLOW)
            performance['numpy_benchmark'] = None
        
        self.results['performance'] = performance
        
        # Record check results
        check_result = {
            'name': 'performance_indicators',
            'status': 'PASS' if not any([
                performance.get('memory_warning', False),
                performance.get('disk_warning', False),
                performance.get('cpu_warning', False)
            ]) else 'WARNING',
            'details': performance
        }
        self.results['checks'].append(check_result)
    
    def check_file_permissions(self):
        """Check file and directory permissions"""
        self.log("Checking file permissions...")
        
        important_paths = [
            '.',  # Current directory
            'app',
            'scripts',
            'logs',
            'exports',
            'tmp'
        ]
        
        permission_issues = []
        
        for path in important_paths:
            if os.path.exists(path):
                try:
                    # Test read access
                    os.listdir(path) if os.path.isdir(path) else open(path, 'r').close()
                    
                    # Test write access for directories
                    if os.path.isdir(path):
                        test_file = os.path.join(path, '.write_test')
                        try:
                            with open(test_file, 'w') as f:
                                f.write('test')
                            os.remove(test_file)
                            self.log(f"✓ {path} - Read/Write OK", "SUCCESS", Colors.GREEN)
                        except PermissionError:
                            self.log(f"✗ {path} - Write permission denied", "ERROR", Colors.RED)
                            permission_issues.append(path)
                            self.issues_found += 1
                    else:
                        self.log(f"✓ {path} - Read OK", "SUCCESS", Colors.GREEN)
                        
                except PermissionError:
                    self.log(f"✗ {path} - Read permission denied", "ERROR", Colors.RED)
                    permission_issues.append(path)
                    self.issues_found += 1
            else:
                if path in ['logs', 'exports', 'tmp']:
                    # Create missing directories if auto-fix is enabled
                    if self.auto_fix:
                        try:
                            os.makedirs(path, exist_ok=True)
                            self.log(f"✓ Created missing directory: {path}", "SUCCESS", Colors.GREEN)
                            self.fixes_applied += 1
                        except PermissionError:
                            self.log(f"✗ Could not create directory: {path}", "ERROR", Colors.RED)
                            permission_issues.append(path)
                            self.issues_found += 1
                    else:
                        self.log(f"⚠ Missing directory: {path}", "WARNING", Colors.YELLOW)
                else:
                    self.log(f"⚠ Path not found: {path}", "WARNING", Colors.YELLOW)
        
        # Record check results
        check_result = {
            'name': 'file_permissions',
            'status': 'PASS' if not permission_issues else 'FAIL',
            'permission_issues': permission_issues
        }
        self.results['checks'].append(check_result)
        
        return len(permission_issues) == 0
    
    def check_environment_configuration(self):
        """Check environment configuration"""
        self.log("Checking environment configuration...")
        
        # Check for .env file
        env_file_exists = os.path.exists('.env')
        env_template_exists = os.path.exists('env.template')
        
        if env_file_exists:
            self.log("✓ .env file found", "SUCCESS", Colors.GREEN)
        elif env_template_exists:
            self.log("⚠ .env file missing but template available", "WARNING", Colors.YELLOW)
            if self.auto_fix:
                try:
                    shutil.copy('env.template', '.env')
                    self.log("✓ Created .env file from template", "SUCCESS", Colors.GREEN)
                    self.fixes_applied += 1
                    env_file_exists = True
                except Exception as e:
                    self.log(f"✗ Could not create .env file: {e}", "ERROR", Colors.RED)
                    self.issues_found += 1
        else:
            self.log("✗ Neither .env nor env.template found", "ERROR", Colors.RED)
            self.issues_found += 1
        
        # Check environment variables
        important_env_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL'
        ]
        
        missing_env_vars = []
        if env_file_exists:
            try:
                with open('.env', 'r') as f:
                    env_content = f.read()
                    
                for var in important_env_vars:
                    if f"{var}=" in env_content:
                        self.log(f"✓ {var} configured", "SUCCESS", Colors.GREEN)
                    else:
                        self.log(f"⚠ {var} not configured", "WARNING", Colors.YELLOW)
                        missing_env_vars.append(var)
            except Exception as e:
                self.log(f"✗ Could not read .env file: {e}", "ERROR", Colors.RED)
                self.issues_found += 1
        
        # Record check results
        check_result = {
            'name': 'environment_configuration',
            'status': 'PASS' if env_file_exists and not missing_env_vars else 'WARNING',
            'env_file_exists': env_file_exists,
            'missing_env_vars': missing_env_vars
        }
        self.results['checks'].append(check_result)
    
    def generate_recommendations(self):
        """Generate recommendations based on check results"""
        self.log("Generating recommendations...")
        
        recommendations = []
        
        # Check each test result and generate recommendations
        for check in self.results['checks']:
            if check['status'] == 'FAIL' or check['status'] == 'WARNING':
                if check['name'] == 'python_dependencies':
                    if check.get('missing_core'):
                        recommendations.append({
                            'category': 'Dependencies',
                            'priority': 'HIGH',
                            'issue': 'Missing core Python packages',
                            'solution': f"Install missing packages: pip install {' '.join(check['missing_core'])}",
                            'command': f"pip install {' '.join(check['missing_core'])}"
                        })
                
                elif check['name'] == 'port_availability':
                    for port_issue in check.get('port_conflicts', []):
                        recommendations.append({
                            'category': 'Network',
                            'priority': 'MEDIUM',
                            'issue': f"Port {port_issue['port']} ({port_issue['service']}) is in use",
                            'solution': f"Kill process using port {port_issue['port']} or change application port",
                            'command': f"lsof -ti:{port_issue['port']} | xargs kill -9"
                        })
                
                elif check['name'] == 'docker_status':
                    if not check.get('docker_installed'):
                        recommendations.append({
                            'category': 'Infrastructure',
                            'priority': 'HIGH',
                            'issue': 'Docker is not installed',
                            'solution': 'Install Docker Desktop from https://docker.com',
                            'command': None
                        })
                    elif not check.get('docker_running'):
                        recommendations.append({
                            'category': 'Infrastructure',
                            'priority': 'HIGH',
                            'issue': 'Docker daemon is not running',
                            'solution': 'Start Docker Desktop or Docker daemon',
                            'command': 'sudo systemctl start docker  # Linux'
                        })
                
                elif check['name'] == 'file_permissions':
                    for path in check.get('permission_issues', []):
                        recommendations.append({
                            'category': 'Permissions',
                            'priority': 'HIGH',
                            'issue': f'Permission denied for {path}',
                            'solution': f'Fix permissions for {path}',
                            'command': f'chmod 755 {path}'
                        })
                
                elif check['name'] == 'environment_configuration':
                    if not check.get('env_file_exists'):
                        recommendations.append({
                            'category': 'Configuration',
                            'priority': 'HIGH',
                            'issue': 'Missing .env configuration file',
                            'solution': 'Create .env file from template',
                            'command': 'cp env.template .env'
                        })
        
        # Performance recommendations
        perf = self.results.get('performance', {})
        if perf.get('memory_warning'):
            recommendations.append({
                'category': 'Performance',
                'priority': 'MEDIUM',
                'issue': 'Low available memory',
                'solution': 'Close unnecessary applications or upgrade system memory',
                'command': None
            })
        
        if perf.get('disk_warning'):
            recommendations.append({
                'category': 'Performance',
                'priority': 'MEDIUM',
                'issue': 'Low disk space',
                'solution': 'Free up disk space or clean temporary files',
                'command': 'docker system prune -f'
            })
        
        # Specific demo recommendations
        recommendations.extend([
            {
                'category': 'Demo Setup',
                'priority': 'LOW',
                'issue': 'Optimize demo performance',
                'solution': 'Install optional performance packages',
                'command': 'pip install scipy matplotlib numba'
            },
            {
                'category': 'Demo Setup',
                'priority': 'LOW',
                'issue': 'Enable caching for better performance',
                'solution': 'Install and configure Redis',
                'command': 'docker-compose up -d redis'
            }
        ])
        
        self.results['recommendations'] = recommendations
        
        # Display recommendations
        if recommendations:
            self.log(f"\nGenerated {len(recommendations)} recommendations:", "INFO", Colors.BOLD)
            for i, rec in enumerate(recommendations, 1):
                priority_color = {
                    'HIGH': Colors.RED,
                    'MEDIUM': Colors.YELLOW,
                    'LOW': Colors.GREEN
                }.get(rec['priority'], Colors.NC)
                
                self.log(f"\n{i}. [{rec['category']}] {rec['issue']}", "INFO", priority_color)
                self.log(f"   Priority: {rec['priority']}", "INFO")
                self.log(f"   Solution: {rec['solution']}", "INFO")
                if rec['command']:
                    self.log(f"   Command: {rec['command']}", "INFO", Colors.CYAN)
    
    def export_report(self, filename: str = None):
        """Export diagnostic report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_diagnostic_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            self.log(f"✓ Diagnostic report exported to: {filename}", "SUCCESS", Colors.GREEN)
            return filename
        except Exception as e:
            self.log(f"✗ Failed to export report: {e}", "ERROR", Colors.RED)
            return None
    
    def print_summary(self):
        """Print diagnostic summary"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.NC}")
        print(f"{Colors.BOLD}DIAGNOSTIC SUMMARY{Colors.NC}")
        print(f"{Colors.BOLD}{'='*60}{Colors.NC}")
        
        # System info summary
        sys_info = self.results['system_info']
        print(f"\n{Colors.CYAN}System Information:{Colors.NC}")
        print(f"  Platform: {sys_info['platform']} {sys_info['platform_release']}")
        print(f"  Python: {sys_info['python_version'].split()[0]}")
        print(f"  Memory: {sys_info['memory']['available_gb']:.1f}GB / {sys_info['memory']['total_gb']:.1f}GB")
        print(f"  Disk: {sys_info['disk']['free_gb']:.1f}GB free")
        
        # Check results summary
        print(f"\n{Colors.CYAN}Check Results:{Colors.NC}")
        passed = sum(1 for check in self.results['checks'] if check['status'] == 'PASS')
        warnings = sum(1 for check in self.results['checks'] if check['status'] == 'WARNING')
        failed = sum(1 for check in self.results['checks'] if check['status'] == 'FAIL')
        
        total_checks = len(self.results['checks'])
        print(f"  ✓ Passed: {passed}/{total_checks}")
        if warnings > 0:
            print(f"  ⚠ Warnings: {warnings}/{total_checks}")
        if failed > 0:
            print(f"  ✗ Failed: {failed}/{total_checks}")
        
        # Issues and fixes
        if self.issues_found > 0:
            print(f"\n{Colors.RED}Issues Found: {self.issues_found}{Colors.NC}")
        
        if self.fixes_applied > 0:
            print(f"{Colors.GREEN}Fixes Applied: {self.fixes_applied}{Colors.NC}")
        
        # Overall status
        print(f"\n{Colors.CYAN}Overall Status:{Colors.NC}")
        if failed == 0 and self.issues_found == 0:
            print(f"  {Colors.GREEN}✓ SYSTEM READY - All checks passed{Colors.NC}")
        elif failed == 0:
            print(f"  {Colors.YELLOW}⚠ SYSTEM READY WITH WARNINGS{Colors.NC}")
        else:
            print(f"  {Colors.RED}✗ ISSUES DETECTED - See recommendations{Colors.NC}")
        
        # Quick start recommendation
        print(f"\n{Colors.CYAN}Quick Start:{Colors.NC}")
        if failed == 0:
            print(f"  Run: {Colors.GREEN}python3 working_demo.py{Colors.NC}")
            print(f"  Or:  {Colors.GREEN}./start_demo.sh{Colors.NC}")
        else:
            print(f"  Fix issues first, then run: {Colors.GREEN}python3 check_system.py --fix{Colors.NC}")
        
        print(f"\n{Colors.BOLD}{'='*60}{Colors.NC}")
    
    def run_all_checks(self):
        """Run all diagnostic checks"""
        start_time = time.time()
        
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("="*70)
        print("  FINANCIAL PLANNING SYSTEM - DIAGNOSTIC TOOL")
        print("="*70)
        print(f"{Colors.NC}")
        
        # Run all checks
        self.check_system_info()
        print()
        
        self.check_python_dependencies()
        print()
        
        self.check_port_availability()
        print()
        
        self.check_docker_status()
        print()
        
        self.check_database_connectivity()
        print()
        
        self.check_file_permissions()
        print()
        
        self.check_environment_configuration()
        print()
        
        self.check_performance_indicators()
        print()
        
        self.generate_recommendations()
        
        elapsed_time = time.time() - start_time
        self.results['diagnostic_time'] = elapsed_time
        
        self.log(f"Diagnostic completed in {elapsed_time:.2f} seconds", "SUCCESS", Colors.GREEN)
        
        self.print_summary()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Financial Planning System Diagnostic Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 check_system.py                    # Basic diagnostic
  python3 check_system.py --verbose          # Detailed output
  python3 check_system.py --fix              # Auto-fix issues
  python3 check_system.py --export-report    # Generate JSON report
  python3 check_system.py --fix --export-report  # Fix and report
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose output')
    parser.add_argument('--fix', '-f', action='store_true',
                      help='Attempt to automatically fix detected issues')
    parser.add_argument('--export-report', '-e', action='store_true',
                      help='Export diagnostic report to JSON file')
    parser.add_argument('--report-file', '-o', type=str,
                      help='Specify output file for report')
    
    args = parser.parse_args()
    
    # Create diagnostic instance
    diagnostic = SystemDiagnostic(
        verbose=args.verbose,
        auto_fix=args.fix
    )
    
    try:
        # Run all checks
        diagnostic.run_all_checks()
        
        # Export report if requested
        if args.export_report:
            report_file = diagnostic.export_report(args.report_file)
            if report_file:
                print(f"\n{Colors.GREEN}Report saved to: {report_file}{Colors.NC}")
        
        # Return appropriate exit code
        failed_checks = sum(1 for check in diagnostic.results['checks'] if check['status'] == 'FAIL')
        exit_code = 1 if failed_checks > 0 else 0
        
        if exit_code == 0:
            print(f"\n{Colors.GREEN}✓ Diagnostic completed successfully{Colors.NC}")
        else:
            print(f"\n{Colors.RED}✗ Diagnostic completed with {failed_checks} failed check(s){Colors.NC}")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Diagnostic interrupted by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Diagnostic failed with error: {e}{Colors.NC}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()