@echo off
REM ==============================================================================
REM Financial Planning System - Windows Demo Launcher
REM ==============================================================================
REM 
REM Professional batch script launcher for Windows systems
REM Provides easy access to all demos with dependency checking and error handling
REM
REM Usage:
REM   launch_demo.bat                    Interactive mode
REM   launch_demo.bat backend-full       Direct launch
REM   launch_demo.bat --list             List all demos
REM   launch_demo.bat --help             Show help
REM
REM Features:
REM   - Automatic Python and dependency detection
REM   - System requirements validation
REM   - Professional progress indicators
REM   - Error handling and cleanup
REM   - Windows-specific optimizations
REM ==============================================================================

setlocal EnableDelayedExpansion

REM Configuration
set "SCRIPT_DIR=%~dp0"
set "LAUNCHER_SCRIPT=demo_launcher.py"
set "MIN_PYTHON_VERSION=3.8"

REM Colors for Windows (if supported)
REM Note: Windows 10 version 1511 and later support ANSI escape codes
for /F "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
if "%VERSION%" geq "10.0" (
    set "RED=[91m"
    set "GREEN=[92m"
    set "YELLOW=[93m"
    set "BLUE=[94m"
    set "MAGENTA=[95m"
    set "CYAN=[96m"
    set "WHITE=[97m"
    set "BOLD=[1m"
    set "RESET=[0m"
) else (
    set "RED="
    set "GREEN="
    set "YELLOW="
    set "BLUE="
    set "MAGENTA="
    set "CYAN="
    set "WHITE="
    set "BOLD="
    set "RESET="
)

REM ASCII Banner
:print_banner
echo %CYAN%%BOLD%
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                    🏦 FINANCIAL PLANNING SYSTEM 🏦                         ║
echo ║                        Windows Demo Launcher                                ║
echo ║                                                                              ║
echo ║    💰 Advanced Monte Carlo Simulations                                      ║
echo ║    📊 Real-time Portfolio Analytics                                         ║
echo ║    🤖 AI-Powered Recommendations                                            ║
echo ║    📱 Multi-Platform Support                                                ║
echo ║    🔒 Enterprise Security                                                   ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo %RESET%
goto :eof

REM Logging functions
:log_info
echo %BLUE%[INFO]%RESET% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%RESET% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%RESET% %~1
goto :eof

:log_error
echo %RED%[ERROR]%RESET% %~1
goto :eof

:log_step
echo %CYAN%%BOLD%=^> %~1%RESET%
goto :eof

REM Error handling
:error_exit
call :log_error "%~1"
call :log_error "Demo launcher failed. Please check the error message above."
pause
exit /b 1

REM Check if running as administrator (not recommended)
:check_admin
net session >nul 2>&1
if %errorLevel% == 0 (
    call :log_warning "Running as administrator is not recommended for demos"
    set /p "continue=Continue anyway? (y/N): "
    if /i not "!continue!" == "y" exit /b 1
)
goto :eof

REM Detect Windows version and architecture
:detect_system
call :log_step "Detecting System Information"

REM Get Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set "WIN_VERSION=%%i.%%j"
for /f "skip=1 delims=" %%i in ('wmic os get caption') do (
    set "WIN_CAPTION=%%i"
    goto :got_caption
)
:got_caption

REM Get architecture
if "%PROCESSOR_ARCHITECTURE%" == "AMD64" (
    set "ARCH=64-bit"
) else if "%PROCESSOR_ARCHITECTURE%" == "ARM64" (
    set "ARCH=ARM64"
) else (
    set "ARCH=32-bit"
)

call :log_success "Detected: %WIN_CAPTION% (%ARCH%)"
goto :eof

REM Check Python installation
:check_python
call :log_step "Checking Python Installation"

set "PYTHON_CMD="

REM Try different Python commands
for %%p in (python python3 py) do (
    %%p --version >nul 2>&1
    if !errorlevel! == 0 (
        for /f "tokens=2" %%v in ('%%p --version 2^>^&1') do (
            set "version=%%v"
            REM Extract major.minor version
            for /f "tokens=1,2 delims=." %%a in ("!version!") do (
                set "major=%%a"
                set "minor=%%b"
            )
            
            REM Check if version is >= 3.8
            if !major! gtr 3 (
                set "PYTHON_CMD=%%p"
                goto :python_found
            ) else if !major! equ 3 (
                if !minor! geq 8 (
                    set "PYTHON_CMD=%%p"
                    goto :python_found
                )
            )
        )
    )
)

REM Python not found or version too old
call :log_error "Python %MIN_PYTHON_VERSION% or higher is required but not found"
echo.
echo Install Python from:
echo   - https://python.org/downloads/
echo   - Microsoft Store (search for Python)
echo   - Chocolatey: choco install python
echo   - Scoop: scoop install python
echo.
exit /b 1

:python_found
for /f "tokens=2" %%v in ('%PYTHON_CMD% --version 2^>^&1') do set "PY_VERSION=%%v"
call :log_success "Found Python %PY_VERSION% at:"
where %PYTHON_CMD%
goto :eof

REM Check system dependencies
:check_system_deps
call :log_step "Checking System Dependencies"

set "missing_deps="
set "optional_missing="

REM Check essential tools
for %%t in (git curl) do (
    where %%t >nul 2>&1
    if !errorlevel! neq 0 (
        set "missing_deps=!missing_deps! %%t"
    ) else (
        call :log_success "%%t: Found"
    )
)

REM Check optional tools
for %%t in (docker node npm) do (
    where %%t >nul 2>&1
    if !errorlevel! neq 0 (
        set "optional_missing=!optional_missing! %%t"
    ) else (
        for /f "delims=" %%v in ('%%t --version 2^>nul') do (
            call :log_success "%%t: %%v"
        )
    )
)

if not "%missing_deps%" == "" (
    call :log_warning "Missing essential dependencies:%missing_deps%"
    echo.
    echo Install missing tools:
    echo   - Git: https://git-scm.com/download/win
    echo   - curl: Usually included with Windows 10+
    echo   - Or use Chocolatey: choco install git curl
    echo   - Or use Scoop: scoop install git curl
    echo.
    set /p "continue=Continue without these tools? (y/N): "
    if /i not "!continue!" == "y" exit /b 1
)

if not "%optional_missing%" == "" (
    call :log_warning "Optional tools not found:%optional_missing%"
    echo Some demos may not be available without these tools.
)

goto :eof

REM Check if demo launcher exists
:check_launcher
call :log_step "Checking Demo Launcher"

if not exist "%SCRIPT_DIR%%LAUNCHER_SCRIPT%" (
    call :error_exit "Demo launcher script not found: %LAUNCHER_SCRIPT%"
)

call :log_success "Demo launcher found: %LAUNCHER_SCRIPT%"
goto :eof

REM Install Python dependencies if needed
:install_python_deps
call :log_step "Checking Python Dependencies"

REM Check if pip is available
%PYTHON_CMD% -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    call :log_warning "pip not found, attempting to install..."
    %PYTHON_CMD% -m ensurepip --upgrade >nul 2>&1
    if !errorlevel! neq 0 (
        call :error_exit "Could not install pip. Please install pip manually."
    )
)

REM Check for essential Python packages
set "required_packages=fastapi uvicorn numpy pydantic"
set "missing_packages="

for %%p in (%required_packages%) do (
    %PYTHON_CMD% -c "import %%p" >nul 2>&1
    if !errorlevel! neq 0 (
        set "missing_packages=!missing_packages! %%p"
    )
)

if not "%missing_packages%" == "" (
    call :log_warning "Missing Python packages:%missing_packages%"
    
    set /p "install=Install missing packages now? (Y/n): "
    if /i not "!install!" == "n" (
        call :log_info "Installing Python packages..."
        
        REM Upgrade pip first
        %PYTHON_CMD% -m pip install --user --upgrade pip
        
        REM Install missing packages
        %PYTHON_CMD% -m pip install --user%missing_packages%
        
        if !errorlevel! neq 0 (
            call :error_exit "Failed to install Python packages"
        )
        
        call :log_success "Python packages installed successfully"
    )
) else (
    call :log_success "All essential Python packages are available"
)

goto :eof

REM Check disk space
:check_disk_space
set "required_space_mb=2048"

REM Get available space for current drive
for /f "tokens=3" %%a in ('dir /-c "%SCRIPT_DIR%" 2^>nul ^| find "bytes free"') do (
    set "available_bytes=%%a"
    REM Remove commas
    set "available_bytes=!available_bytes:,=!"
)

if defined available_bytes (
    set /a "available_mb=!available_bytes! / 1024 / 1024"
    
    if !available_mb! lss %required_space_mb% (
        call :log_warning "Low disk space: !available_mb!MB available (%required_space_mb%MB recommended)"
        set /p "continue=Continue anyway? (y/N): "
        if /i not "!continue!" == "y" exit /b 1
    ) else (
        call :log_success "Disk space: !available_mb!MB available"
    )
)

goto :eof

REM Check memory
:check_memory
for /f "skip=1" %%p in ('wmic computersystem get TotalPhysicalMemory') do (
    set "total_memory_bytes=%%p"
    if defined total_memory_bytes goto :got_memory
)
:got_memory

if defined total_memory_bytes (
    set /a "total_memory_mb=!total_memory_bytes! / 1024 / 1024"
    
    if !total_memory_mb! lss 4096 (
        call :log_warning "Low memory: !total_memory_mb!MB total (4096MB recommended)"
        echo Some demos may run slowly or fail.
    ) else (
        call :log_success "Memory: !total_memory_mb!MB total"
    )
)

goto :eof

REM Show help
:show_help
call :print_banner
echo %BOLD%Financial Planning System - Windows Demo Launcher%RESET%
echo.
echo Usage:
echo   %~nx0 [DEMO_ID]               Launch specific demo
echo   %~nx0 --list                  List all available demos
echo   %~nx0 --check                 Run system requirements check only
echo   %~nx0 --help                  Show this help message
echo.
echo Examples:
echo   %~nx0                         # Interactive mode
echo   %~nx0 backend-full            # Launch full backend demo
echo   %~nx0 frontend                # Launch frontend demo
echo   %~nx0 --list                  # List all demos
echo.
echo Demo Categories:
echo   • Backend Services         - FastAPI servers with ML simulations
echo   • Frontend Applications    - React/Next.js web applications
echo   • Mobile Applications      - React Native mobile apps
echo   • Infrastructure ^& DevOps  - Docker, Kubernetes deployments
echo   • Security Demonstrations - Authentication, encryption demos
echo   • Data Pipeline ^& Analytics- ETL processes and data analysis
echo   • Machine Learning ^& AI    - ML models and recommendations
echo   • End-to-End Integration   - Complete system tests
echo.
echo System Requirements:
echo   • Python 3.8 or higher
echo   • 4GB+ RAM recommended
echo   • 2GB+ disk space
echo   • Git, curl (essential)
echo   • Docker, Node.js (optional, for some demos)
echo.
echo For more information, visit the documentation or run in interactive mode.
goto :eof

REM Main system check
:run_system_check
call :log_step "System Requirements Check"
echo.

call :detect_system
call :check_python
if !errorlevel! neq 0 exit /b 1

call :check_system_deps
if !errorlevel! neq 0 exit /b 1

call :check_disk_space
if !errorlevel! neq 0 exit /b 1

call :check_memory
call :check_launcher
if !errorlevel! neq 0 exit /b 1

call :install_python_deps
if !errorlevel! neq 0 exit /b 1

echo.
call :log_success "System check completed successfully!"
goto :eof

REM Launch Python demo launcher
:launch_python_launcher
call :log_step "Launching Demo System"

REM Change to script directory
cd /d "%SCRIPT_DIR%"
if !errorlevel! neq 0 (
    call :error_exit "Could not change to script directory"
)

REM Launch the Python launcher with all arguments
%PYTHON_CMD% "%LAUNCHER_SCRIPT%" %*
goto :eof

REM Main entry point
:main
REM Handle command line arguments
if "%~1" == "--help" goto :show_help_and_exit
if "%~1" == "-h" goto :show_help_and_exit
if "%~1" == "/?" goto :show_help_and_exit

if "%~1" == "--check" (
    call :print_banner
    call :run_system_check
    echo.
    pause
    exit /b 0
)

call :print_banner

REM Don't check admin in interactive mode for better UX
if "%~1" == "" call :check_admin

REM Run system check
call :run_system_check
if !errorlevel! neq 0 (
    call :error_exit "System requirements not met"
)

echo.
call :log_step "Starting Demo Launcher"
echo.

REM Launch Python launcher with all arguments
call :launch_python_launcher %*

goto :end

:show_help_and_exit
call :show_help
pause
exit /b 0

:end
REM Keep console open if run by double-clicking
echo %cmdcmdline% | find /i "%~0" >nul
if not errorlevel 1 pause