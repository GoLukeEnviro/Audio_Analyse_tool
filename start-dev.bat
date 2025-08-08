@echo off
chcp 65001 > nul
title DJ Analysis Studio - DEV MODE
color 0A
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    DJ Analysis Studio                         ║
echo ║                  Development Environment                      ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM === System Checks ===
echo [INFO] Ueberpruefe Systemvoraussetzungen...

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js ist nicht installiert!
    echo Installiere von: https://nodejs.org/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('node --version') do echo [OK] Node.js: %%a
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python ist nicht installiert!
    echo Installiere Python 3.8+ von: https://python.org/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('python --version') do echo [OK] Python: %%a
)

REM Check pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip ist nicht verfuegbar!
    echo Installiere pip: python -m ensurepip --upgrade
    echo.
    pause
    exit /b 1
)

echo.
echo [INSTALL] Installiere Root-Abhaengigkeiten...
npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install fehlgeschlagen!
    echo Versuche: npm cache clean --force
    echo.
    pause
    exit /b 1
)

echo.
echo [INSTALL] Installiere Frontend-Abhaengigkeiten...
cd src
npm install
if %errorlevel% neq 0 (
    echo [ERROR] Frontend npm install fehlgeschlagen!
    echo.
    pause
    exit /b 1
)
cd ..

echo.
echo [CHECK] Pruefe Python-Abhaengigkeiten...
python -c "import numpy; print('[OK] NumPy:', __import__('numpy').__version__)" 2>nul || echo [WARNING] NumPy fehlt
python -c "import librosa; print('[OK] Librosa:', __import__('librosa').__version__)" 2>nul || echo [WARNING] Librosa fehlt
python -c "import essentia; print('[OK] Essentia: installiert')" 2>nul || echo [INFO] Essentia nicht gefunden - verwende Librosa-Fallback

REM Check requirements
python -c "import sys; import os; sys.path.insert(0, '.'); from backend.main import app; print('[OK] Backend imports erfolgreich')" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [INSTALL] Installiere Python-Abhaengigkeiten...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Python requirements installation fehlgeschlagen!
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [START] Starte Entwicklungsumgebung...
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    API-Docs: http://localhost:8000/docs
echo.
echo [INFO] Druecke STRG+C zum Beenden aller Services
echo.

REM Starte beide Services
npm run monorepo:dev

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fehler beim Starten der Entwicklungsumgebung!
    echo Prüfe die Ports 8000 und 3000 sind frei
    echo Alternative: Ports in .env anpassen
    echo.
    pause
)

echo.
echo [DONE] Entwicklungsumgebung wurde beendet.
pause