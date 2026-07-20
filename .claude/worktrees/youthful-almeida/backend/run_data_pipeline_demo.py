#!/usr/bin/env python3
"""
Data Pipeline Demo Runner

Simple script to execute the comprehensive data pipeline demonstration.
"""

import sys
import os
import subprocess
import asyncio
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    
    required_packages = ['pandas', 'numpy', 'rich', 'plotly', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Installing dependencies...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("Failed to install dependencies. Please install manually:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("🚀 Financial Data Pipeline Demonstration")
    print("=" * 80)
    print()
    
    # Check current directory
    current_dir = Path.cwd()
    demo_file = current_dir / "data_pipeline_demo.py"
    
    if not demo_file.exists():
        # Try to find the demo file
        possible_paths = [
            current_dir / "backend" / "data_pipeline_demo.py",
            Path(__file__).parent / "data_pipeline_demo.py",
        ]
        
        demo_file = None
        for path in possible_paths:
            if path.exists():
                demo_file = path
                break
        
        if not demo_file:
            print("❌ Could not find data_pipeline_demo.py")
            print("Please ensure you're running this from the correct directory.")
            return 1
    
    print(f"📁 Found demo file: {demo_file}")
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    print("✅ All dependencies are available")
    print()
    print("🎬 Starting data pipeline demonstration...")
    print("   This will showcase ETL, streaming, quality checks, and analytics")
    print()
    
    try:
        # Import and run the demo
        sys.path.insert(0, str(demo_file.parent))
        from data_pipeline_demo import main as run_demo
        
        # Run the async demo
        asyncio.run(run_demo())
        
        print()
        print("🎉 Demo completed successfully!")
        print("📊 Check the demo_data/exports directory for results")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        print("Check the logs for more details")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)