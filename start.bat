@echo off
echo DJ Audio-Analyse-Tool Pro v2.0
echo ================================
echo.

REM Überprüfe ob Python verfügbar ist
python --version >nul 2>&1
if errorlevel 1 (
    echo Fehler: Python ist nicht installiert oder nicht im PATH verfügbar.
    echo Bitte installieren Sie Python 3.8 oder höher.
    pause
    exit /b 1
)

REM Überprüfe ob pip verfügbar ist
pip --version >nul 2>&1
if errorlevel 1 (
    echo Fehler: pip ist nicht verfügbar.
    echo Bitte stellen Sie sicher, dass pip installiert ist.
    pause
    exit /b 1
)

REM Installiere Abhängigkeiten falls requirements.txt existiert
if exist requirements.txt (
    echo Überprüfe und installiere Abhängigkeiten...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Warnung: Einige Abhängigkeiten konnten nicht installiert werden.
        echo Die Anwendung wird trotzdem gestartet...
        echo.
    )
)

REM Starte die Anwendung
echo Starte DJ Audio-Analyse-Tool Pro...
echo.
python main.py

REM Warte auf Benutzereingabe falls Fehler aufgetreten sind
if errorlevel 1 (
    echo.
    echo Die Anwendung wurde mit einem Fehler beendet.
    pause
)