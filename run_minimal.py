#!/usr/bin/env python3
"""Run the minimal API on a free port"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minimal_api import run_server

if __name__ == '__main__':
    # Try port 8080 instead
    run_server(port=8080)