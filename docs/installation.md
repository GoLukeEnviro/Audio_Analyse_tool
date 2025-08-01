# Installation Guide

Diese Anleitung führt Sie durch die Installation des DJ Audio-Analyse-Tools Pro v2.0.

## 📋 Systemanforderungen

### Mindestanforderungen
- **Betriebssystem**: Windows 10 (Version 1903 oder höher) / Windows 11
- **Python**: Version 3.8 oder höher
- **RAM**: Mindestens 4 GB (8 GB empfohlen)
- **Festplattenspeicher**: 2 GB freier Speicherplatz
- **Prozessor**: Dual-Core CPU (Quad-Core empfohlen)

### Empfohlene Konfiguration
- **RAM**: 8 GB oder mehr
- **Prozessor**: Quad-Core CPU oder besser
- **Festplatte**: SSD für bessere Performance
- **Audio-Interface**: Professionelles Audio-Interface für DJ-Anwendungen

## 🚀 Schnellinstallation

### Option 1: Automatische Installation (Empfohlen)

1. **Repository herunterladen**
   ```bash
   git clone <repository-url>
   cd Audio_Analyse_tool
   ```

2. **Automatisches Setup ausführen**
   - Doppelklick auf `start.bat`
   - Das Skript installiert automatisch alle Abhängigkeiten
   - Folgen Sie den Anweisungen auf dem Bildschirm

3. **Anwendung starten**
   - Nach erfolgreicher Installation startet die Anwendung automatisch
   - Beim ersten Start wird der Onboarding-Wizard angezeigt

### Option 2: Manuelle Installation

#### Schritt 1: Python-Umgebung vorbereiten

```bash
# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
venv\Scripts\activate  # Windows
# oder
source venv/bin/activate  # Linux/Mac
```

#### Schritt 2: Basis-Abhängigkeiten installieren

```bash
# Kern-Abhängigkeiten
pip install --upgrade pip
pip install PySide6 librosa numpy scipy soundfile mutagen pandas
```

#### Schritt 3: Audio-Analyse-Bibliotheken

```bash
# Essentia für erweiterte Audio-Analyse
pip install essentia-tensorflow

# Alternative für CPU-only:
# pip install essentia
```

#### Schritt 4: Machine Learning-Komponenten

```bash
# LightGBM für Mood-Klassifikation
pip install lightgbm

# Scikit-learn für zusätzliche ML-Features
pip install scikit-learn
```

#### Schritt 5: Test- und Entwicklungstools

```bash
# Testing-Framework
pip install pytest pytest-mock pytest-cov

# Entwicklungstools (optional)
pip install black flake8 mypy
```

#### Schritt 6: Alle Abhängigkeiten auf einmal

```bash
# Installiere alle Abhängigkeiten aus requirements.txt
pip install -r requirements.txt
```

## 🔧 Erweiterte Installation

### Conda-Installation

Für Benutzer, die Conda bevorzugen:

```bash
# Conda-Umgebung erstellen
conda create -n dj-tool python=3.9
conda activate dj-tool

# Basis-Pakete über Conda
conda install numpy scipy pandas

# Spezielle Pakete über pip
pip install PySide6 librosa essentia-tensorflow lightgbm
```

### Docker-Installation (Experimentell)

```bash
# Docker-Image erstellen
docker build -t dj-audio-tool .

# Container ausführen
docker run -it --rm -v $(pwd):/app dj-audio-tool
```

## ✅ Installation verifizieren

### Schritt 1: Abhängigkeiten testen

```bash
# Test-Suite ausführen
python -m pytest tests/ -v

# Oder spezifische Tests
python test_runner.py
```

### Schritt 2: Anwendung starten

```bash
# Hauptanwendung starten
python main.py

# Oder Demo-Version
python demo_mvp.py
```

### Schritt 3: Funktionalität testen

1. **Audio-Import testen**
   - Laden Sie eine Test-MP3-Datei
   - Überprüfen Sie, ob die Analyse funktioniert

2. **Playlist-Generierung testen**
   - Erstellen Sie eine einfache Playlist
   - Exportieren Sie sie als M3U

3. **GUI-Funktionen testen**
   - Navigieren Sie durch alle Tabs
   - Testen Sie Drag & Drop-Funktionen

## 🐛 Häufige Installationsprobleme

### Problem: "Essentia nicht gefunden"

**Lösung 1**: Alternative Installation
```bash
pip uninstall essentia-tensorflow
pip install essentia
```

**Lösung 2**: Conda-Installation
```bash
conda install -c mtg essentia
```

### Problem: "LightGBM Installation fehlgeschlagen"

**Windows-spezifische Lösung**:
```bash
# Visual Studio Build Tools installieren
# Dann:
pip install lightgbm
```

**Alternative**:
```bash
conda install lightgbm
```

### Problem: "PySide6 Import-Fehler"

**Lösung**:
```bash
pip uninstall PySide6
pip install PySide6==6.4.0
```

### Problem: "Audio-Dateien können nicht geladen werden"

**Lösung**: Zusätzliche Codecs installieren
```bash
pip install pydub
# Für erweiterte Format-Unterstützung
```

### Problem: "Langsame Performance"

**Optimierungen**:
1. **Multiprocessing konfigurieren**:
   ```python
   # In config/settings.json
   {
     "processing": {
       "max_workers": 4,  # Anzahl CPU-Kerne
       "batch_size": 10
     }
   }
   ```

2. **Cache-Einstellungen optimieren**:
   ```python
   {
     "cache": {
       "max_size_gb": 2,
       "cleanup_days": 30
     }
   }
   ```

## 🔄 Updates und Wartung

### Abhängigkeiten aktualisieren

```bash
# Alle Pakete aktualisieren
pip install --upgrade -r requirements.txt

# Spezifische Pakete aktualisieren
pip install --upgrade librosa essentia-tensorflow
```

### Cache bereinigen

```bash
# Cache-Verzeichnis leeren
rmdir /s cache
mkdir cache

# Oder über die Anwendung: Tools → Cache verwalten
```

### Deinstallation

```bash
# Virtuelle Umgebung entfernen
rmdir /s venv

# Anwendungsdaten entfernen
rmdir /s cache
rmdir /s exports
rmdir /s logs
```

## 📞 Support

Bei Installationsproblemen:

1. **Log-Dateien prüfen**: `logs/installation.log`
2. **FAQ konsultieren**: [FAQ](faq.md)
3. **Issue erstellen**: GitHub Repository
4. **Community-Support**: Discord/Forum

## 🔗 Nützliche Links

- [Python Download](https://www.python.org/downloads/)
- [Git für Windows](https://git-scm.com/download/win)
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- [Conda Download](https://docs.conda.io/en/latest/miniconda.html)

---

**Nächste Schritte**: Nach erfolgreicher Installation lesen Sie den [Quick Start Guide](quick-start.md) für den ersten Einstieg.