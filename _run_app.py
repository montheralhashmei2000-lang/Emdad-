#!/usr/bin/env python3
"""Unified launcher - best practice entry point."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import run

if __name__ == '__main__':
    run()

