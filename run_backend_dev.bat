@echo off
REM DJ Audio-Analyse-Tool Pro - Development Backend Starter
REM Startet den FastAPI Server im Development-Modus mit Auto-Reload

echo ========================================
echo   DJ Audio-Analyse-Tool Pro Backend
echo   Development Server v2.0.0
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python ist nicht installiert oder nicht im PATH verfuegbar!
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo [ERROR] backend\main.py nicht gefunden!
    pause
    exit /b 1
)

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Aktiviere Virtual Environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual Environment nicht gefunden, verwende System-Python
)

REM Set development environment
set ENVIRONMENT=development
set DEBUG=true

echo [INFO] Starte Development Server mit Auto-Reload...
echo [INFO] API-Dokumentation: http://localhost:8000/docs
echo [INFO] Server Status: http://localhost:8000/health
echo [INFO] Zum Beenden: Strg+C
echo.

REM Start with uvicorn directly for development
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 --log-level debug

if errorlevel 1 (
    echo.
    echo [ERROR] Development Server konnte nicht gestartet werden!
    pause
)