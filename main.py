#!/usr/bin/env python3
"""
Audio Analysis Tool - DJ Playlist Generator
Main entry point for the desktop application
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from src.gui.main_window import main
except ImportError as e:
    print(f"Error importing GUI module: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    print("Audio Analysis Tool - DJ Playlist Generator")
    print("Starting application...")
    main()