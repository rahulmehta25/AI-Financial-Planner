#!/usr/bin/env python3
"""
Unified Demo Launcher for Financial Planning System
==================================================

A comprehensive launcher that provides a single entry point for all demos
in the Financial Planning System. Supports interactive menu selection,
dependency management, system validation, and batch launching.

Features:
- Interactive menu with demo categories
- Automatic dependency detection and installation
- System requirements validation
- Port availability checking
- Multiple platform support (Windows, macOS, Linux)
- Batch launching capabilities
- Professional progress indicators
- Comprehensive error handling
- Link to documentation

Usage:
    python demo_launcher.py                    # Interactive mode
    python demo_launcher.py --demo backend     # Direct launch
    python demo_launcher.py --list             # List all demos
    python demo_launcher.py --batch backend frontend  # Batch launch
"""

import os
import sys
import json
import time
import shutil
import socket
import platform
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import threading
import signal
from contextlib import contextmanager

# ASCII Art Banner
BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🏦 FINANCIAL PLANNING SYSTEM 🏦                         ║
║                         Unified Demo Launcher                               ║
║                                                                              ║
║    💰 Advanced Monte Carlo Simulations                                      ║
║    📊 Real-time Portfolio Analytics                                         ║
║    🤖 AI-Powered Recommendations                                            ║
║    📱 Multi-Platform Support                                                ║
║    🔒 Enterprise Security                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

class DemoCategory(Enum):
    BACKEND = "Backend Services"
    FRONTEND = "Frontend Applications"
    MOBILE = "Mobile Applications"
    INFRASTRUCTURE = "Infrastructure & DevOps"
    SECURITY = "Security Demonstrations"
    DATA = "Data Pipeline & Analytics"
    ML = "Machine Learning & AI"
    INTEGRATION = "End-to-End Integration"

@dataclass
class SystemRequirement:
    name: str
    command: str
    version_flag: str = "--version"
    min_version: Optional[str] = None
    install_url: str = ""
    required: bool = True

@dataclass
class Demo:
    name: str
    category: DemoCategory
    description: str
    path: str
    script: str
    requirements: List[SystemRequirement] = field(default_factory=list)
    ports: List[int] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    estimated_time: str = "2-5 minutes"
    documentation: str = ""
    prerequisites: List[str] = field(default_factory=list)

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ProgressIndicator:
    """Professional progress indicator with spinner"""
    def __init__(self, message: str):
        self.message = message
        self.running = False
        self.thread = None
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.current_char = 0

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, success: bool = True, final_message: str = ""):
        self.running = False
        if self.thread:
            self.thread.join()
        
        symbol = "✅" if success else "❌"
        message = final_message or self.message
        print(f"\r{symbol} {message}")

    def _spin(self):
        while self.running:
            char = self.spinner_chars[self.current_char]
            print(f"\r{char} {self.message}", end="", flush=True)
            self.current_char = (self.current_char + 1) % len(self.spinner_chars)
            time.sleep(0.1)

class DemoLauncher:
    """Main demo launcher class"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.demos = self._discover_demos()
        self.running_processes = []
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n{Colors.WARNING}⚠️  Received shutdown signal. Cleaning up...{Colors.ENDC}")
        self.cleanup()
        sys.exit(0)

    def _discover_demos(self) -> Dict[str, Demo]:
        """Discover all available demos in the project"""
        demos = {}
        
        # Backend Demos
        backend_dir = self.root_dir / "backend"
        if backend_dir.exists():
            demos.update({
                "backend-full": Demo(
                    name="Full Backend Demo",
                    category=DemoCategory.BACKEND,
                    description="Complete FastAPI backend with all features including Monte Carlo simulations, PDF generation, and real-time WebSocket updates",
                    path=str(backend_dir),
                    script="working_demo.py",
                    ports=[8000],
                    dependencies=["fastapi", "uvicorn", "numpy", "scipy", "matplotlib", "reportlab", "numba"],
                    estimated_time="3-5 minutes",
                    documentation="http://localhost:8000/docs",
                    prerequisites=["Python 3.8+"]
                ),
                "backend-minimal": Demo(
                    name="Minimal Backend Demo",
                    category=DemoCategory.BACKEND,
                    description="Lightweight backend demo with core functionality and minimal dependencies",
                    path=str(backend_dir),
                    script="minimal_working_demo.py",
                    ports=[8000],
                    dependencies=["fastapi", "uvicorn", "numpy", "pydantic"],
                    estimated_time="1-2 minutes",
                    documentation="http://localhost:8000/docs",
                    prerequisites=["Python 3.8+"]
                ),
                "backend-cli": Demo(
                    name="CLI Demo",
                    category=DemoCategory.BACKEND,
                    description="Command-line interface demo showcasing financial calculations and portfolio analysis",
                    path=str(backend_dir),
                    script="cli_demo.py",
                    ports=[],
                    dependencies=["numpy", "pandas"],
                    estimated_time="1 minute",
                    prerequisites=["Python 3.8+"]
                ),
                "ml-simulation": Demo(
                    name="ML Simulation Demo",
                    category=DemoCategory.ML,
                    description="Advanced machine learning demonstrations with portfolio optimization and risk analysis",
                    path=str(backend_dir),
                    script="ml_simulation_demo.py",
                    ports=[],
                    dependencies=["numpy", "scipy", "pandas", "scikit-learn"],
                    estimated_time="2-3 minutes",
                    prerequisites=["Python 3.8+"]
                ),
                "data-pipeline": Demo(
                    name="Data Pipeline Demo",
                    category=DemoCategory.DATA,
                    description="ETL pipeline demonstration with real-time data processing and analytics",
                    path=str(backend_dir),
                    script="data_pipeline_demo.py",
                    ports=[],
                    dependencies=["pandas", "numpy", "sqlalchemy"],
                    estimated_time="2-4 minutes",
                    prerequisites=["Python 3.8+"]
                ),
                "security-demo": Demo(
                    name="Security Demo",
                    category=DemoCategory.SECURITY,
                    description="Security features demonstration including authentication, authorization, and data protection",
                    path=str(backend_dir),
                    script="security_demo.py",
                    ports=[8000],
                    dependencies=["fastapi", "uvicorn", "cryptography", "passlib"],
                    estimated_time="2-3 minutes",
                    documentation="http://localhost:8000/docs",
                    prerequisites=["Python 3.8+"]
                ),
                "performance-demo": Demo(
                    name="Performance Demo",
                    category=DemoCategory.BACKEND,
                    description="High-performance computing demonstration with GPU acceleration and optimization",
                    path=str(backend_dir),
                    script="performance_demo.py",
                    ports=[8000],
                    dependencies=["fastapi", "uvicorn", "numpy", "numba"],
                    estimated_time="3-5 minutes",
                    prerequisites=["Python 3.8+"]
                )
            })

        # Frontend Demos
        frontend_dir = self.root_dir / "frontend"
        if frontend_dir.exists():
            demos.update({
                "frontend": Demo(
                    name="Next.js Frontend",
                    category=DemoCategory.FRONTEND,
                    description="Modern React/Next.js frontend with interactive dashboards and real-time charts",
                    path=str(frontend_dir),
                    script="npm run dev",
                    ports=[3000],
                    dependencies=["node", "npm"],
                    estimated_time="2-3 minutes",
                    documentation="http://localhost:3000",
                    prerequisites=["Node.js 18+", "npm"]
                ),
                "frontend-demo": Demo(
                    name="Frontend Demo Mode",
                    category=DemoCategory.FRONTEND,
                    description="Frontend in demo mode with mock data and showcase features",
                    path=str(frontend_dir),
                    script="npm run demo",
                    ports=[3000],
                    dependencies=["node", "npm"],
                    estimated_time="1-2 minutes",
                    documentation="http://localhost:3000/demo",
                    prerequisites=["Node.js 18+", "npm"]
                )
            })

        # Mobile Demos
        mobile_demo_dir = self.root_dir / "mobile" / "demo-app"
        if mobile_demo_dir.exists():
            demos.update({
                "mobile-demo": Demo(
                    name="React Native Mobile Demo",
                    category=DemoCategory.MOBILE,
                    description="Complete mobile application with biometric authentication, offline support, and push notifications",
                    path=str(mobile_demo_dir),
                    script="start-demo.sh",
                    ports=[19000, 19001, 19002],
                    dependencies=["node", "npm", "expo"],
                    estimated_time="3-5 minutes",
                    documentation="Scan QR code with Expo Go app",
                    prerequisites=["Node.js 18+", "Expo CLI", "Expo Go mobile app"]
                )
            })

        # Infrastructure Demos
        if (self.root_dir / "docker-compose.yml").exists():
            demos.update({
                "docker-full": Demo(
                    name="Full Docker Stack",
                    category=DemoCategory.INFRASTRUCTURE,
                    description="Complete containerized deployment with all services, monitoring, and infrastructure",
                    path=str(self.root_dir),
                    script="start_docker_demo.sh",
                    ports=[80, 3000, 8000, 5432, 6379, 9090, 3001],
                    dependencies=["docker", "docker-compose"],
                    estimated_time="5-10 minutes",
                    documentation="http://localhost",
                    prerequisites=["Docker Desktop", "4GB+ RAM"]
                ),
                "kubernetes-demo": Demo(
                    name="Kubernetes Demo",
                    category=DemoCategory.INFRASTRUCTURE,
                    description="Kubernetes deployment with auto-scaling, monitoring, and service mesh",
                    path=str(self.root_dir / "backend" / "k8s"),
                    script="kubectl apply -f .",
                    ports=[80, 443],
                    dependencies=["kubectl", "kubernetes"],
                    estimated_time="10-15 minutes",
                    documentation="http://localhost/docs",
                    prerequisites=["Kubernetes cluster", "kubectl", "8GB+ RAM"]
                )
            })

        # Integration Demos
        demos.update({
            "integration-test": Demo(
                name="End-to-End Integration",
                category=DemoCategory.INTEGRATION,
                description="Complete system integration test with all components working together",
                path=str(self.root_dir),
                script="validate_demo.sh",
                ports=[80, 3000, 8000],
                dependencies=["docker", "docker-compose", "curl"],
                estimated_time="5-8 minutes",
                prerequisites=["Docker Desktop", "All services running"]
            )
        })

        return demos

    def print_banner(self):
        """Print the application banner"""
        print(f"{Colors.CYAN}{BANNER}{Colors.ENDC}")
        print(f"{Colors.BLUE}Version: 2.0.0 | Platform: {platform.system()} | Python: {sys.version.split()[0]}{Colors.ENDC}")
        print()

    def check_system_requirements(self) -> bool:
        """Check basic system requirements"""
        print(f"{Colors.BOLD}🔍 System Requirements Check{Colors.ENDC}")
        print("-" * 50)
        
        checks_passed = 0
        total_checks = 0
        
        # Check Python version
        total_checks += 1
        python_version = sys.version_info
        if python_version >= (3, 8):
            print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
            checks_passed += 1
        else:
            print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)")
        
        # Check essential commands
        essential_commands = [
            ("git", "Git version control"),
            ("curl", "HTTP client for testing"),
        ]
        
        for command, description in essential_commands:
            total_checks += 1
            if shutil.which(command):
                print(f"✅ {command}: {description}")
                checks_passed += 1
            else:
                print(f"⚠️  {command}: {description} (recommended)")
        
        # Check Docker availability
        total_checks += 1
        if shutil.which("docker"):
            try:
                result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"✅ Docker: {version}")
                    checks_passed += 1
                else:
                    print("❌ Docker: Installed but not working")
            except subprocess.TimeoutExpired:
                print("❌ Docker: Timeout checking version")
            except Exception:
                print("❌ Docker: Error checking version")
        else:
            print("⚠️  Docker: Not installed (required for infrastructure demos)")
        
        # Check Node.js availability
        total_checks += 1
        if shutil.which("node"):
            try:
                result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"✅ Node.js: {version}")
                    checks_passed += 1
                else:
                    print("❌ Node.js: Installed but not working")
            except Exception:
                print("❌ Node.js: Error checking version")
        else:
            print("⚠️  Node.js: Not installed (required for frontend/mobile demos)")
        
        print()
        print(f"System Check: {checks_passed}/{total_checks} passed")
        
        if checks_passed < total_checks // 2:
            print(f"{Colors.WARNING}⚠️  Some system requirements are missing. Some demos may not work.{Colors.ENDC}")
            return False
        
        return True

    def check_port_availability(self, ports: List[int]) -> bool:
        """Check if required ports are available"""
        if not ports:
            return True
            
        unavailable_ports = []
        for port in ports:
            if not self._is_port_available(port):
                unavailable_ports.append(port)
        
        if unavailable_ports:
            print(f"{Colors.WARNING}⚠️  Ports {unavailable_ports} are already in use{Colors.ENDC}")
            print("Please stop services using these ports or choose different demos.")
            return False
        
        return True

    def _is_port_available(self, port: int) -> bool:
        """Check if a specific port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return False

    def install_dependencies(self, demo: Demo) -> bool:
        """Install missing dependencies for a demo"""
        if not demo.dependencies:
            return True
        
        print(f"{Colors.BOLD}📦 Checking Dependencies for {demo.name}{Colors.ENDC}")
        print("-" * 50)
        
        missing_deps = []
        
        for dep in demo.dependencies:
            if not self._check_dependency(dep):
                missing_deps.append(dep)
        
        if not missing_deps:
            print("✅ All dependencies are installed")
            return True
        
        print(f"{Colors.WARNING}Missing dependencies: {', '.join(missing_deps)}{Colors.ENDC}")
        
        # Ask user if they want to install
        install = input(f"Install missing dependencies? (y/N): ").lower().strip()
        if install != 'y':
            print("❌ Cannot proceed without required dependencies")
            return False
        
        # Install Python dependencies
        python_deps = [dep for dep in missing_deps if dep in [
            'fastapi', 'uvicorn', 'numpy', 'scipy', 'matplotlib', 'reportlab', 
            'numba', 'pandas', 'scikit-learn', 'pydantic', 'cryptography', 'passlib'
        ]]
        
        if python_deps:
            progress = ProgressIndicator(f"Installing Python packages: {', '.join(python_deps)}")
            progress.start()
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "--upgrade", *python_deps
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    progress.stop(True, f"Successfully installed: {', '.join(python_deps)}")
                else:
                    progress.stop(False, f"Failed to install: {', '.join(python_deps)}")
                    print(f"Error: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                progress.stop(False, "Installation timeout")
                return False
            except Exception as e:
                progress.stop(False, f"Installation error: {e}")
                return False
        
        return True

    def _check_dependency(self, dep: str) -> bool:
        """Check if a dependency is available"""
        try:
            if dep in ['node', 'npm']:
                return shutil.which(dep) is not None
            elif dep in ['docker', 'docker-compose', 'kubectl']:
                return shutil.which(dep) is not None
            else:
                # Python package
                __import__(dep)
                return True
        except ImportError:
            return False

    def list_demos(self, category: Optional[DemoCategory] = None):
        """List all available demos"""
        print(f"{Colors.BOLD}📋 Available Demos{Colors.ENDC}")
        print("=" * 80)
        
        if category:
            demos = {k: v for k, v in self.demos.items() if v.category == category}
            print(f"\n{Colors.BOLD}🏷️  {category.value}{Colors.ENDC}")
        else:
            demos = self.demos
            # Group by category
            categories = {}
            for demo_id, demo in demos.items():
                if demo.category not in categories:
                    categories[demo.category] = []
                categories[demo.category].append((demo_id, demo))
            
            for cat, demo_list in categories.items():
                print(f"\n{Colors.BOLD}🏷️  {cat.value}{Colors.ENDC}")
                print("-" * 40)
                for demo_id, demo in demo_list:
                    self._print_demo_info(demo_id, demo)
            return
        
        print("-" * 40)
        for demo_id, demo in demos.items():
            self._print_demo_info(demo_id, demo)

    def _print_demo_info(self, demo_id: str, demo: Demo):
        """Print information about a single demo"""
        status = "✅" if self._check_demo_requirements(demo) else "⚠️"
        print(f"{status} {Colors.BOLD}{demo_id}{Colors.ENDC}: {demo.name}")
        print(f"    {demo.description}")
        print(f"    📊 Time: {demo.estimated_time} | 🔌 Ports: {demo.ports or 'None'}")
        if demo.documentation:
            print(f"    📚 Docs: {demo.documentation}")
        print()

    def _check_demo_requirements(self, demo: Demo) -> bool:
        """Check if demo requirements are met"""
        if not demo.dependencies:
            return True
        
        for dep in demo.dependencies:
            if not self._check_dependency(dep):
                return False
        
        return True

    def show_interactive_menu(self):
        """Show interactive demo selection menu"""
        while True:
            self.print_banner()
            
            print(f"{Colors.BOLD}🎯 Demo Categories{Colors.ENDC}")
            print("=" * 50)
            
            categories = list(DemoCategory)
            for i, category in enumerate(categories, 1):
                count = len([d for d in self.demos.values() if d.category == category])
                if count > 0:
                    print(f"{i:2d}. {category.value} ({count} demos)")
            
            print(f"\n{Colors.BOLD}🔧 Quick Actions{Colors.ENDC}")
            print("-" * 30)
            print(f"{len(categories) + 1:2d}. 🚀 Launch Full Stack Demo")
            print(f"{len(categories) + 2:2d}. 📋 List All Demos")
            print(f"{len(categories) + 3:2d}. 🔍 System Check")
            print(f"{len(categories) + 4:2d}. 📚 Documentation")
            print(f"{len(categories) + 5:2d}. ❌ Exit")
            
            try:
                choice = input(f"\n{Colors.CYAN}Select option: {Colors.ENDC}").strip()
                
                if choice == str(len(categories) + 5) or choice.lower() == 'exit':
                    break
                elif choice == str(len(categories) + 1):
                    self.launch_full_stack()
                elif choice == str(len(categories) + 2):
                    self.list_demos()
                    input("\nPress Enter to continue...")
                elif choice == str(len(categories) + 3):
                    self.check_system_requirements()
                    input("\nPress Enter to continue...")
                elif choice == str(len(categories) + 4):
                    self.show_documentation()
                    input("\nPress Enter to continue...")
                elif choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(categories):
                        self.show_category_menu(categories[choice_idx])
                    else:
                        print(f"{Colors.FAIL}Invalid choice{Colors.ENDC}")
                        time.sleep(1)
                else:
                    print(f"{Colors.FAIL}Invalid choice{Colors.ENDC}")
                    time.sleep(1)
                    
            except (ValueError, KeyboardInterrupt):
                print(f"\n{Colors.WARNING}Exiting...{Colors.ENDC}")
                break

    def show_category_menu(self, category: DemoCategory):
        """Show demos for a specific category"""
        demos_in_category = {k: v for k, v in self.demos.items() if v.category == category}
        
        if not demos_in_category:
            print(f"{Colors.WARNING}No demos available in this category{Colors.ENDC}")
            time.sleep(2)
            return
        
        while True:
            print(f"\n{Colors.BOLD}🏷️  {category.value}{Colors.ENDC}")
            print("=" * 60)
            
            demo_list = list(demos_in_category.items())
            for i, (demo_id, demo) in enumerate(demo_list, 1):
                status = "✅" if self._check_demo_requirements(demo) else "⚠️"
                print(f"{i:2d}. {status} {demo.name}")
                print(f"      {demo.description[:60]}...")
                print(f"      ⏱️  {demo.estimated_time} | 🔌 {demo.ports or 'No ports'}")
            
            print(f"\n{len(demo_list) + 1:2d}. 🔙 Back to main menu")
            
            try:
                choice = input(f"\n{Colors.CYAN}Select demo: {Colors.ENDC}").strip()
                
                if choice == str(len(demo_list) + 1):
                    break
                elif choice.isdigit():
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(demo_list):
                        demo_id, demo = demo_list[choice_idx]
                        self.launch_demo(demo_id, demo)
                    else:
                        print(f"{Colors.FAIL}Invalid choice{Colors.ENDC}")
                        time.sleep(1)
                else:
                    print(f"{Colors.FAIL}Invalid choice{Colors.ENDC}")
                    time.sleep(1)
                    
            except (ValueError, KeyboardInterrupt):
                break

    def launch_demo(self, demo_id: str, demo: Demo) -> bool:
        """Launch a specific demo"""
        print(f"\n{Colors.BOLD}🚀 Launching: {demo.name}{Colors.ENDC}")
        print("=" * 60)
        print(f"📝 Description: {demo.description}")
        print(f"📂 Path: {demo.path}")
        print(f"📜 Script: {demo.script}")
        print(f"⏱️  Estimated time: {demo.estimated_time}")
        
        if demo.prerequisites:
            print(f"📋 Prerequisites: {', '.join(demo.prerequisites)}")
        
        print()
        
        # Check system requirements
        if not self.check_system_requirements():
            return False
        
        # Check port availability
        if not self.check_port_availability(demo.ports):
            return False
        
        # Install dependencies
        if not self.install_dependencies(demo):
            return False
        
        # Confirm launch
        confirm = input(f"{Colors.CYAN}Launch {demo.name}? (Y/n): {Colors.ENDC}").lower().strip()
        if confirm == 'n':
            print("❌ Launch cancelled")
            return False
        
        print(f"\n{Colors.GREEN}🚀 Starting {demo.name}...{Colors.ENDC}")
        print("-" * 40)
        
        try:
            # Change to demo directory
            original_dir = os.getcwd()
            os.chdir(demo.path)
            
            # Set environment variables
            env = os.environ.copy()
            env.update(demo.env_vars)
            
            # Execute demo script
            if demo.script.endswith('.py'):
                # Python script
                process = subprocess.Popen([sys.executable, demo.script], 
                                         env=env, stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT, text=True)
            elif demo.script.endswith('.sh'):
                # Shell script
                process = subprocess.Popen(['bash', demo.script], 
                                         env=env, stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT, text=True)
            elif demo.script.startswith('npm'):
                # npm command
                process = subprocess.Popen(demo.script.split(), 
                                         env=env, stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT, text=True)
            else:
                # Generic command
                process = subprocess.Popen(demo.script.split(), 
                                         env=env, stdout=subprocess.PIPE, 
                                         stderr=subprocess.STDOUT, text=True)
            
            self.running_processes.append(process)
            
            # Show progress and handle output
            self._handle_demo_process(process, demo)
            
            return True
            
        except Exception as e:
            print(f"{Colors.FAIL}❌ Error launching demo: {e}{Colors.ENDC}")
            return False
        finally:
            os.chdir(original_dir)

    def _handle_demo_process(self, process: subprocess.Popen, demo: Demo):
        """Handle demo process output and interaction"""
        print(f"✅ Demo started successfully!")
        
        if demo.documentation:
            print(f"📚 Documentation: {demo.documentation}")
        
        if demo.ports:
            print("🔌 Services will be available at:")
            for port in demo.ports:
                print(f"   • http://localhost:{port}")
        
        print(f"\n{Colors.BOLD}Demo is running...{Colors.ENDC}")
        print("Press Ctrl+C to stop the demo")
        print("-" * 40)
        
        try:
            # Stream output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.rstrip())
                    
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}⚠️  Stopping demo...{Colors.ENDC}")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ Demo stopped")

    def launch_full_stack(self):
        """Launch the complete full-stack demo"""
        print(f"\n{Colors.BOLD}🚀 Full Stack Demo Launch{Colors.ENDC}")
        print("=" * 60)
        print("This will launch:")
        print("• Backend API server")
        print("• Frontend application") 
        print("• Database services")
        print("• Monitoring dashboard")
        print()
        
        if "docker-full" in self.demos:
            self.launch_demo("docker-full", self.demos["docker-full"])
        else:
            print(f"{Colors.WARNING}Docker full stack demo not available{Colors.ENDC}")
            print("Launching individual components instead...")
            
            # Launch backend and frontend separately
            success_count = 0
            if "backend-full" in self.demos:
                if self.launch_demo("backend-full", self.demos["backend-full"]):
                    success_count += 1
            
            time.sleep(5)  # Give backend time to start
            
            if "frontend" in self.demos:
                if self.launch_demo("frontend", self.demos["frontend"]):
                    success_count += 1
            
            print(f"✅ Launched {success_count} components successfully")

    def show_documentation(self):
        """Show documentation and helpful links"""
        print(f"\n{Colors.BOLD}📚 Documentation & Resources{Colors.ENDC}")
        print("=" * 60)
        
        docs = [
            ("📖 Main README", "README.md"),
            ("🚀 Demo Setup Guide", "DEMO_README.md"),
            ("🏗️  Backend Documentation", "backend/README.md"),
            ("🌐 Frontend Documentation", "frontend/README.md"),
            ("📱 Mobile Documentation", "mobile/README.md"),
            ("🔒 Security Guide", "docs/SECURITY_BEST_PRACTICES.md"),
            ("📊 API Documentation", "http://localhost:8000/docs (when backend running)"),
        ]
        
        for title, path in docs:
            if path.startswith("http"):
                print(f"{title}: {path}")
            else:
                full_path = self.root_dir / path
                if full_path.exists():
                    print(f"✅ {title}: {path}")
                else:
                    print(f"❌ {title}: {path} (not found)")
        
        print(f"\n{Colors.BOLD}🔗 Quick Links{Colors.ENDC}")
        print("-" * 30)
        print("• API Docs: http://localhost:8000/docs")
        print("• Frontend: http://localhost:3000")
        print("• Admin Panel: http://localhost:8000/admin")
        print("• Health Check: http://localhost:8000/health")

    def cleanup(self):
        """Cleanup running processes"""
        if self.running_processes:
            print(f"🧹 Cleaning up {len(self.running_processes)} running processes...")
            for process in self.running_processes:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    try:
                        process.kill()
                    except ProcessLookupError:
                        pass
            self.running_processes.clear()
            print("✅ Cleanup completed")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Unified Demo Launcher for Financial Planning System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_launcher.py                    # Interactive mode
  python demo_launcher.py --demo backend-full  # Launch specific demo
  python demo_launcher.py --list               # List all demos
  python demo_launcher.py --batch backend-full frontend  # Batch launch
  python demo_launcher.py --category backend   # Show backend demos
        """
    )
    
    parser.add_argument(
        '--demo', 
        help='Launch specific demo by ID'
    )
    
    parser.add_argument(
        '--list', 
        action='store_true',
        help='List all available demos'
    )
    
    parser.add_argument(
        '--batch', 
        nargs='+',
        help='Launch multiple demos in batch mode'
    )
    
    parser.add_argument(
        '--category',
        choices=[cat.name.lower() for cat in DemoCategory],
        help='Show demos for specific category'
    )
    
    parser.add_argument(
        '--check', 
        action='store_true',
        help='Run system requirements check'
    )
    
    parser.add_argument(
        '--no-deps', 
        action='store_true',
        help='Skip dependency installation'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    if args.no_color:
        # Disable colors
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')
    
    launcher = DemoLauncher()
    
    try:
        if args.list:
            launcher.list_demos()
        elif args.check:
            launcher.check_system_requirements()
        elif args.category:
            category = DemoCategory[args.category.upper()]
            launcher.list_demos(category)
        elif args.demo:
            if args.demo in launcher.demos:
                demo = launcher.demos[args.demo]
                launcher.launch_demo(args.demo, demo)
            else:
                print(f"{Colors.FAIL}❌ Demo '{args.demo}' not found{Colors.ENDC}")
                print("Available demos:")
                launcher.list_demos()
                sys.exit(1)
        elif args.batch:
            for demo_id in args.batch:
                if demo_id in launcher.demos:
                    print(f"\n{Colors.BOLD}Launching {demo_id}...{Colors.ENDC}")
                    launcher.launch_demo(demo_id, launcher.demos[demo_id])
                    time.sleep(2)  # Brief pause between launches
                else:
                    print(f"{Colors.FAIL}❌ Demo '{demo_id}' not found, skipping{Colors.ENDC}")
        else:
            # Interactive mode
            launcher.show_interactive_menu()
    
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  Demo launcher interrupted{Colors.ENDC}")
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    main()