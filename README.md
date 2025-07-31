# 🎵 Audio Analyse Tool

Ein Desktop-Tool für die intelligente Analyse von Musikbibliotheken und automatische Playlist-Generierung. Optimiert für DJs und Musikproduzenten.

## ✨ Features

### 🔍 Audio-Analyse
- **Automatische Musikanalyse** mit essentia und librosa
- **Extraktion von**: Tonart, BPM, Energie, Stimmung, Helligkeit, Harmonik
- **JSON-Caching** für schnelle Wiederverwendung der Analyseergebnisse
- **Unterstützte Formate**: MP3, WAV, FLAC, M4A, AAC

### 🎛️ Intelligente Playlist-Generierung
- **Regel-basierte Engine** mit benutzerdefinierten Parametern
- **Camelot Wheel Integration** für harmonische Tonart-Übergänge
- **BPM-Flow-Optimierung** und Energie-Verlauf-Steuerung
- **Preset-Stile**: Driving, Dark, Euphoric, Experimental

### 🖥️ Desktop GUI
- **Moderne PyQt5-Oberfläche** mit Dark Theme
- **Track-Browser** mit Sortier- und Filterfunktionen
- **Playlist-Dashboard** für Regel-Konfiguration
- **Spectrogramm-Anzeige** (optional)
- **Einstellungen** speicher- und ladbar

### 📤 Export-Funktionen
- **Rekordbox-kompatible Formate**: M3U, XML
- **Metadata-Integration** für nahtlosen Import
- **Relative Pfade** für portable Playlists

## 🚀 Installation

### Entwicklungsumgebung

```bash
# Repository klonen
git clone <repository-url>
cd Audio_Analyse_tool

# Virtual Environment erstellen
python -m venv venv
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Anwendung starten
python main.py
```

### Standalone .exe erstellen

```bash
# PyInstaller ausführen
pyinstaller build_exe.spec

# .exe findet sich in dist/AudioAnalyseTool.exe
```

## 📁 Projektstruktur

```
Audio_Analyse_tool/
├── main.py                 # Haupteinstiegspunkt
├── requirements.txt        # Python-Dependencies
├── setup.py               # Packaging-Konfiguration
├── build_exe.spec         # PyInstaller-Spezifikation
├── README.md              # Projektdokumentation
├── src/                   # Quellcode
│   ├── audio_analysis/    # Audio-Analyse-Engine
│   ├── gui/              # Desktop-Interface
│   ├── playlist_engine/   # Playlist-Generierung
│   ├── export/           # Export-Funktionen
│   └── utils/            # Hilfsfunktionen
├── config/               # Konfigurationsdateien
├── data/                 # Cache und Datenbank
├── assets/              # Icons und Ressourcen
├── tests/               # Unit Tests
└── docs/                # Dokumentation
```

## ⚙️ Konfiguration

Die Hauptkonfiguration befindet sich in `config/default_config.yaml`:

- **Audio-Analyse-Parameter**: Sample Rate, Hop Length, Feature-Auswahl
- **Playlist-Regeln**: BPM-Toleranz, Camelot-Gewichtung, Preset-Stile
- **Export-Einstellungen**: Format-Präferenzen, Metadata-Optionen
- **Cache-Management**: Größenlimits, Cleanup-Intervalle

## 🎯 Verwendung

1. **Musikbibliothek laden**: Ordner mit MP3-Files auswählen
2. **Analyse starten**: Automatische Feature-Extraktion
3. **Playlist-Regeln definieren**: BPM, Tonart, Stimmung, Energie
4. **Playlist generieren**: Intelligente Sortierung und Optimierung
5. **Export**: M3U oder XML für Rekordbox

## 🛠️ Entwicklung

### Code-Style
- **PEP-8 konform** mit black und flake8
- **Type Hints** für bessere Code-Qualität
- **Modulare Architektur** für einfache Erweiterung

### Testing
```bash
# Unit Tests ausführen
pytest tests/

# Code-Qualität prüfen
flake8 src/
black src/ --check
```

## 📋 Roadmap

- [ ] **Machine Learning**: Automatische Stimmungserkennung
- [ ] **Cloud-Integration**: Spotify/Beatport API
- [ ] **Collaborative Filtering**: Community-basierte Empfehlungen
- [ ] **Live-Mixing**: Real-time BPM-Matching
- [ ] **Mobile App**: Companion für iOS/Android

## 🤝 Contributing

Beiträge sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

## 📄 Lizenz

MIT License - siehe LICENSE-Datei für Details.

---

**Entwickelt für die DJ- und Musikproduktions-Community** 🎧