@echo off
REM DJ Audio-Analyse-Tool Pro - Backend Starter (Windows)
REM Startet den FastAPI Uvicorn Server

echo ========================================
echo   DJ Audio-Analyse-Tool Pro Backend
echo   FastAPI Server v2.0.0
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python ist nicht installiert oder nicht im PATH verfuegbar!
    echo Bitte installiere Python 3.8+ und fuege es zum PATH hinzu.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py nicht gefunden!
    echo Bitte stelle sicher, dass du im Projekt-Root-Verzeichnis bist.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [INFO] Erstelle Virtual Environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Virtual Environment konnte nicht erstellt werden!
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Aktiviere Virtual Environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo [INFO] Installiere/Aktualisiere Dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependencies konnten nicht installiert werden!
    echo Versuche: pip install -r requirements.txt --no-deps
    pip install -r requirements.txt --no-deps
)

REM Create necessary directories
echo [INFO] Erstelle notwendige Verzeichnisse...
if not exist "data\" mkdir data
if not exist "data\cache\" mkdir data\cache
if not exist "data\exports\" mkdir data\exports
if not exist "data\presets\" mkdir data\presets
if not exist "logs\" mkdir logs

echo.
echo [INFO] Starte FastAPI Backend Server...
echo [INFO] API-Dokumentation: http://localhost:8000/docs
echo [INFO] Server Status: http://localhost:8000/health
echo [INFO] Zum Beenden: Strg+C
echo.

REM Start the FastAPI server
cd backend
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo [ERROR] Server konnte nicht gestartet werden!
    pause
)