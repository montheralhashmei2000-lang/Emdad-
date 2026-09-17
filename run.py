#!/usr/bin/env python3
"""Launch entry point for the نظام الإمداد والتموين application."""
import sys
import os

# Ensure this directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import run

if __name__ == '__main__':
    run()
