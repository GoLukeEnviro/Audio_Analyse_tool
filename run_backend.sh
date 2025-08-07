#!/bin/bash
# DJ Audio-Analyse-Tool Pro - Backend Starter (Linux/macOS)
# Startet den FastAPI Uvicorn Server

set -e  # Exit on any error

echo "========================================"
echo "  DJ Audio-Analyse-Tool Pro Backend"
echo "  FastAPI Server v2.0.0"  
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m' 
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_error "Python ist nicht installiert oder nicht im PATH verfügbar!"
        echo "Bitte installiere Python 3.8+ und füge es zum PATH hinzu."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

print_info "Using Python: $($PYTHON_CMD --version)"

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    print_error "backend/main.py nicht gefunden!"
    echo "Bitte stelle sicher, dass du im Projekt-Root-Verzeichnis bist."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Erstelle Virtual Environment..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        print_error "Virtual Environment konnte nicht erstellt werden!"
        exit 1
    fi
    print_success "Virtual Environment erstellt"
fi

# Activate virtual environment
print_info "Aktiviere Virtual Environment..."
source venv/bin/activate

# Install/upgrade dependencies
print_info "Installiere/Aktualisiere Dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_warning "Einige Dependencies konnten nicht installiert werden, versuche ohne deps..."
    pip install -r requirements.txt --no-deps
fi

# Create necessary directories
print_info "Erstelle notwendige Verzeichnisse..."
mkdir -p data/cache
mkdir -p data/exports  
mkdir -p data/presets
mkdir -p logs

print_success "Setup abgeschlossen"
echo
print_info "Starte FastAPI Backend Server..."
print_info "API-Dokumentation: http://localhost:8000/docs"
print_info "Server Status: http://localhost:8000/health"
print_info "Zum Beenden: Strg+C"
echo

# Start the FastAPI server
cd backend
python main.py

# If we get here, the server exited
if [ $? -ne 0 ]; then
    print_error "Server konnte nicht gestartet werden!"
    exit 1
fi