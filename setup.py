#!/usr/bin/env python3
"""
Setup-Skript für Audio Analyse Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# README lesen
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

# Requirements lesen
requirements = []
if (this_directory / "requirements.txt").exists():
    with open(this_directory / "requirements.txt", 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="audio-analyse-tool",
    version="1.0.0",
    author="Audio Analyse Tool Team",
    description="Desktop-Tool für Musikbibliothek-Analyse und intelligente Playlist-Generierung",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "audio-analyse-tool=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="audio analysis music dj playlist rekordbox",
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
    },
)