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
echo 🔍 Überprüfe Systemvoraussetzungen...

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js ist nicht installiert!
    echo Installiere von: https://nodejs.org/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('node --version') do echo ✅ Node.js: %%a
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python ist nicht installiert!
    echo Installiere Python 3.8+ von: https://python.org/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%a in ('python --version') do echo ✅ Python: %%a
)

REM Check pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip ist nicht verfügbar!
    echo Installiere pip: python -m ensurepip --upgrade
    echo.
    pause
    exit /b 1
)

echo.
echo 📦 Installiere Root-Abhängigkeiten...
npm install
if %errorlevel% neq 0 (
    echo ❌ npm install fehlgeschlagen!
    echo Versuche: npm cache clean --force
    echo.
    pause
    exit /b 1
)

echo.
echo 📦 Installiere Frontend-Abhängigkeiten...
cd src
npm install
if %errorlevel% neq 0 (
    echo ❌ Frontend npm install fehlgeschlagen!
    echo.
    pause
    exit /b 1
)
cd ..

echo.
echo 🔧 Prüfe Python-Abhängigkeiten...
python -c "import numpy; print('✅ NumPy:', __import__('numpy').__version__)" 2>nul || echo ⚠️ NumPy fehlt
python -c "import librosa; print('✅ Librosa:', __import__('librosa').__version__)" 2>nul || echo ⚠️ Librosa fehlt
python -c "import essentia; print('✅ Essentia: installiert')" 2>nul || echo ℹ️ Essentia nicht gefunden - verwende Librosa-Fallback

REM Check requirements
python -c "import sys; import os; sys.path.insert(0, '.'); from backend.main import app; print('✅ Backend imports erfolgreich')" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 📋 Installiere Python-Abhängigkeiten...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Python requirements installation fehlgeschlagen!
        echo.
        pause
        exit /b 1
    )
)

echo.
echo 🚀 Starte Entwicklungsumgebung...
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:3000
echo    API-Docs: http://localhost:8000/docs
echo.
echo ℹ️  Drücke STRG+C zum Beenden aller Services
echo.

REM Starte beide Services
npm run monorepo:dev

if %errorlevel% neq 0 (
    echo.
    echo ❌ Fehler beim Starten der Entwicklungsumgebung!
    echo Prüfe die Ports 8000 und 3000 sind frei
    echo Alternative: Ports in .env anpassen
    echo.
    pause
)

echo.
echo ✅ Entwicklungsumgebung wurde beendet.
pause