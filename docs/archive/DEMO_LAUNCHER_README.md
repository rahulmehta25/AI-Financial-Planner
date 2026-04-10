# 🚀 Unified Demo Launcher for Financial Planning System

A comprehensive, professional demo launcher that provides a single entry point for all demonstrations in the Financial Planning System. Features interactive menu selection, automatic dependency management, system validation, and cross-platform support.

## ✨ Features

- **🎯 Interactive Menu System**: Beautiful categorized menu with professional styling
- **🔍 Auto-Discovery**: Automatically detects all available demos across the project
- **📦 Dependency Management**: Checks and installs missing dependencies automatically
- **🖥️ Cross-Platform**: Full support for Windows, macOS, and Linux
- **🛡️ System Validation**: Comprehensive system requirements checking
- **🔌 Port Checking**: Validates port availability before launching demos
- **📊 Progress Indicators**: Professional spinners and progress feedback
- **🧹 Cleanup Handling**: Graceful shutdown and cleanup on interruption
- **📚 Built-in Documentation**: Links to relevant documentation and guides

## 🎮 Quick Start

### Interactive Mode (Recommended)
```bash
# Unix/Linux/macOS
./launch_demo.sh

# Windows
launch_demo.bat

# Python directly
python demo_launcher.py
```

### Direct Launch
```bash
# Launch specific demo
./launch_demo.sh backend-full
python demo_launcher.py --demo backend-full

# List all available demos
./launch_demo.sh --list
python demo_launcher.py --list
```

### Batch Launch
```bash
# Launch multiple demos
python demo_launcher.py --batch backend-full frontend mobile-demo
```

## 📋 Available Demo Categories

### 🏗️ Backend Services
- **Full Backend Demo** - Complete FastAPI backend with Monte Carlo simulations, PDF generation, and WebSocket updates
- **Minimal Backend Demo** - Lightweight backend with core functionality and minimal dependencies
- **CLI Demo** - Command-line interface showcasing financial calculations
- **Performance Demo** - High-performance computing with GPU acceleration

### 🌐 Frontend Applications
- **Next.js Frontend** - Modern React/Next.js frontend with interactive dashboards
- **Frontend Demo Mode** - Showcase mode with mock data and demo features

### 📱 Mobile Applications
- **React Native Demo** - Complete mobile app with biometric auth and offline support

### 🏢 Infrastructure & DevOps
- **Full Docker Stack** - Complete containerized deployment with monitoring
- **Kubernetes Demo** - K8s deployment with auto-scaling and service mesh

### 🔒 Security Demonstrations
- **Security Demo** - Authentication, authorization, and data protection features

### 📊 Data Pipeline & Analytics
- **Data Pipeline Demo** - ETL pipeline with real-time processing
- **ML Simulation Demo** - Advanced ML with portfolio optimization

### 🤖 Machine Learning & AI
- **ML Recommendation Engine** - AI-powered financial recommendations
- **Portfolio Optimization** - Modern Portfolio Theory implementations

### 🔄 End-to-End Integration
- **Integration Tests** - Complete system validation and testing

## 🛠️ System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 4GB recommended (2GB minimum)
- **Disk Space**: 2GB free space
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+ (or equivalent)

### Essential Tools
- **Git** - Version control (required for most demos)
- **curl** - HTTP client for testing APIs

### Optional Tools (for specific demos)
- **Docker Desktop** - For infrastructure demos
- **Node.js 18+** - For frontend and mobile demos
- **kubectl** - For Kubernetes demos

## 🎯 Demo Details

### Backend Demos

#### Full Backend Demo
- **Ports**: 8000
- **Time**: 3-5 minutes
- **Features**: Monte Carlo simulations, PDF reports, WebSocket updates
- **Documentation**: http://localhost:8000/docs
- **Dependencies**: FastAPI, NumPy, SciPy, Matplotlib, ReportLab

#### Minimal Backend Demo
- **Ports**: 8000
- **Time**: 1-2 minutes
- **Features**: Core financial planning API
- **Documentation**: http://localhost:8000/docs
- **Dependencies**: FastAPI, NumPy, Pydantic

### Frontend Demos

#### Next.js Frontend
- **Ports**: 3000
- **Time**: 2-3 minutes
- **Features**: Interactive dashboards, real-time charts
- **Documentation**: http://localhost:3000
- **Dependencies**: Node.js, npm

### Infrastructure Demos

#### Full Docker Stack
- **Ports**: 80, 3000, 8000, 5432, 6379, 9090, 3001
- **Time**: 5-10 minutes
- **Features**: Complete deployment with monitoring
- **Documentation**: http://localhost
- **Dependencies**: Docker Desktop, 4GB+ RAM

## 🔧 Installation & Setup

### Automatic Installation
The launcher will automatically:
1. Check system requirements
2. Detect missing dependencies
3. Offer to install missing packages
4. Validate port availability
5. Set up the demo environment

### Manual Installation

#### Python Dependencies
```bash
pip install fastapi uvicorn numpy scipy matplotlib reportlab numba pandas pydantic
```

#### System Dependencies

**macOS (using Homebrew):**
```bash
brew install python git curl docker node npm
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip git curl docker.io nodejs npm
```

**Windows (using Chocolatey):**
```powershell
choco install python git curl docker-desktop nodejs npm
```

## 💡 Usage Examples

### Interactive Menu Navigation
1. Run the launcher: `./launch_demo.sh`
2. Select a demo category (1-8)
3. Choose a specific demo
4. The launcher will check requirements and launch the demo

### Command Line Options
```bash
# Show all demos
python demo_launcher.py --list

# Show demos by category
python demo_launcher.py --category backend

# Run system check only
python demo_launcher.py --check

# Launch with specific demo
python demo_launcher.py --demo backend-full

# Batch launch multiple demos
python demo_launcher.py --batch backend-full frontend

# Skip dependency installation
python demo_launcher.py --no-deps --demo cli-demo

# Disable colored output
python demo_launcher.py --no-color
```

## 🚦 Demo Status Indicators

- ✅ **Green**: All requirements met, ready to launch
- ⚠️ **Yellow**: Some optional dependencies missing, may have limited functionality
- ❌ **Red**: Critical requirements missing, cannot launch

## 🔍 Troubleshooting

### Common Issues

#### Python Not Found
```bash
# Install Python 3.8+
# macOS: brew install python
# Ubuntu: sudo apt install python3 python3-pip
# Windows: Download from python.org
```

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Stop the process or choose a different demo
```

#### Docker Issues
```bash
# Start Docker Desktop
# Ensure Docker daemon is running
docker info

# For Linux, may need to start Docker service
sudo systemctl start docker
```

#### Permission Issues
```bash
# Don't run as root/administrator
# Use virtual environments for Python packages
python -m venv venv
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows
```

### Getting Help

1. **Interactive Help**: Run launcher and select "Documentation" option
2. **Command Help**: `python demo_launcher.py --help`
3. **System Check**: `python demo_launcher.py --check`
4. **Verbose Mode**: Set environment variable `DEBUG=1`

## 🎨 Customization

### Adding New Demos

1. **Create Demo Script**: Add your demo script to the appropriate directory
2. **Update Discovery**: The launcher auto-discovers demos based on file patterns
3. **Add Configuration**: Modify `_discover_demos()` method if needed

### Environment Variables

```bash
# Skip system checks
export SKIP_CHECKS=true

# Set demo environment
export DEMO_ENV=development

# Auto-install dependencies
export AUTO_INSTALL=true

# Custom Python command
export PYTHON_CMD=python3.11
```

## 📊 Performance Notes

- **Startup Time**: 2-10 seconds depending on system check options
- **Memory Usage**: 50-100MB for the launcher itself
- **Demo Memory**: Varies by demo (see individual demo requirements)
- **Concurrent Demos**: Multiple demos can run simultaneously if ports don't conflict

## 🛡️ Security Considerations

- **No Root Required**: Launcher runs as regular user
- **Local Network Only**: Demos bind to localhost by default
- **Demo Credentials**: Uses non-production demo credentials only
- **Dependency Validation**: Checks package integrity where possible

## 🗂️ File Structure

```
Financial Planning/
├── demo_launcher.py          # Main Python launcher
├── launch_demo.sh           # Unix shell wrapper
├── launch_demo.bat          # Windows batch wrapper
├── DEMO_LAUNCHER_README.md  # This documentation
│
├── backend/                 # Backend demos
│   ├── working_demo.py
│   ├── minimal_working_demo.py
│   ├── cli_demo.py
│   └── ...
│
├── frontend/               # Frontend demos
│   └── ...
│
└── mobile/                # Mobile demos
    └── demo-app/
        └── ...
```

## 🤝 Contributing

### Adding New Demo Categories

1. Add new `DemoCategory` enum value
2. Update demo discovery logic
3. Add appropriate demo configuration
4. Update documentation

### Improving Platform Support

1. Test on target platform
2. Add platform-specific logic
3. Update dependency installation
4. Add platform-specific documentation

## 📝 Changelog

### Version 2.0.0
- Complete rewrite with professional UI
- Added interactive menu system
- Cross-platform shell script wrappers
- Automatic dependency management
- Comprehensive system validation
- Professional progress indicators
- Batch launching capabilities
- Enhanced error handling and cleanup

### Version 1.0.0
- Initial release
- Basic demo launching
- Simple dependency checking

## 📄 License

This demo launcher is part of the Financial Planning System project and follows the same license terms.

---

## 🎉 Ready to Explore?

Choose your adventure:

1. **Quick Start**: `./launch_demo.sh` for interactive experience
2. **Backend Developer**: `python demo_launcher.py --demo backend-full`
3. **Frontend Developer**: `python demo_launcher.py --demo frontend`
4. **Full Stack**: `python demo_launcher.py --demo docker-full`
5. **Mobile Developer**: `python demo_launcher.py --demo mobile-demo`

Happy exploring! 🚀