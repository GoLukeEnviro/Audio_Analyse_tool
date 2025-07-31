#!/usr/bin/env python3
"""
DJ Audio-Analyse-Tool Pro v2.0
Hauptanwendung

Professionelle Audio-Analyse für DJs mit erweiterten Features:
- Hybrid Mood-Classifier
- Intelligente Playlist-Engine
- Interaktive Camelot Wheel
- Rekordbox-Integration
"""

import sys
import os
import logging
from pathlib import Path

# Füge src-Verzeichnis zum Python-Pfad hinzu
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dj_tool_pro.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_dependencies():
    """Überprüft ob alle erforderlichen Abhängigkeiten installiert sind"""
    required_packages = [
        'PySide6',
        'librosa',
        'numpy',
        'scipy',
        'soundfile',
        'mutagen',
        'pandas',
        'lightgbm'
    ]
    
    optional_packages = ['essentia']  # Essentia ist optional
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"[OK] {package} ist verfügbar")
        except ImportError:
            logger.error(f"[FEHLER] {package} ist nicht installiert")
            missing_packages.append(package)
    
    # Prüfe optionale Pakete
    for package in optional_packages:
        try:
            __import__(package)
            logger.info(f"[OK] {package} ist verfügbar (optional)")
        except ImportError:
            logger.warning(f"[WARNUNG] {package} ist nicht installiert (optional)")
    
    if missing_packages:
        logger.error(f"Fehlende Pakete: {', '.join(missing_packages)}")
        logger.error("Bitte installieren Sie die fehlenden Pakete mit: pip install -r requirements.txt")
        return False
    
    return True

def setup_environment():
    """Richtet die Anwendungsumgebung ein"""
    # Erstelle notwendige Verzeichnisse
    directories = [
        'cache',
        'exports',
        'presets',
        'logs',
        'temp'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Verzeichnis erstellt: {directory}")
    
    # Setze Umgebungsvariablen für bessere Performance
    os.environ['OMP_NUM_THREADS'] = '4'  # Begrenzt OpenMP Threads
    os.environ['NUMBA_NUM_THREADS'] = '4'  # Begrenzt Numba Threads
    
    logger.info("Anwendungsumgebung eingerichtet")

def main():
    """Hauptfunktion der Anwendung"""
    logger.info("DJ Audio-Analyse-Tool Pro v2.0 wird gestartet...")
    
    # Überprüfe Abhängigkeiten
    if not check_dependencies():
        sys.exit(1)
    
    # Richte Umgebung ein
    setup_environment()
    
    try:
        # Importiere und starte GUI
        from gui.main_window import main as gui_main
        
        logger.info("GUI wird gestartet...")
        gui_main()
        
    except ImportError as e:
        logger.error(f"Fehler beim Importieren der GUI: {e}")
        print("Fehler: GUI-Module konnten nicht geladen werden.")
        print("Stellen Sie sicher, dass alle Abhängigkeiten installiert sind.")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        sys.exit(1)
    
    logger.info("Anwendung beendet")

if __name__ == "__main__":
    main()