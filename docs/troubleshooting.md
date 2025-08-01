# 🔧 Troubleshooting Guide

## 🚨 Häufige Probleme

### Installation & Setup

#### ❌ Python-Version nicht unterstützt

**Problem**: `Python 3.7 is not supported`

**Lösung**:
```bash
# Python-Version prüfen
python --version

# Python 3.8+ installieren
# Windows: https://python.org/downloads/
# Oder Conda verwenden:
conda install python=3.9
```

#### ❌ Abhängigkeiten können nicht installiert werden

**Problem**: `ERROR: Could not install packages`

**Lösung**:
```bash
# 1. Pip upgraden
python -m pip install --upgrade pip

# 2. Virtual Environment verwenden
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Bei Problemen mit Essentia:
pip install essentia-tensorflow  # Statt essentia
```

#### ❌ FFmpeg nicht gefunden

**Problem**: `FFmpeg not found`

**Lösung**:
```bash
# Windows (mit Chocolatey):
choco install ffmpeg

# Oder manuell:
# 1. FFmpeg von https://ffmpeg.org/download.html herunterladen
# 2. Zu PATH hinzufügen
# 3. Neustart
```

### Audio-Analyse

#### ❌ Dateien werden nicht erkannt

**Problem**: `Unsupported audio format`

**Lösung**:
```python
# Unterstützte Formate prüfen
from src.audio_analysis.analyzer import AudioAnalyzer
analyzer = AudioAnalyzer()
print(analyzer.supported_formats)

# Datei konvertieren (falls nötig):
# ffmpeg -i input.m4a output.mp3
```

#### ❌ BPM-Erkennung ungenau

**Problem**: BPM-Werte sind falsch oder inkonsistent

**Lösung**:
1. **Audio-Qualität prüfen**: Mindestens 44.1kHz, 16-bit
2. **Algorithmus anpassen**:
   ```python
   # In config/audio_config.json
   {
     "bpm_detection": {
       "method": "essentia",  # oder "librosa"
       "hop_length": 512,
       "tempo_range": [60, 200]
     }
   }
   ```
3. **Manuelle Korrektur**: BPM-Werte in der GUI editieren

#### ❌ Tonart-Erkennung fehlerhaft

**Problem**: Falsche Key-Detection

**Lösung**:
```python
# Erweiterte Key-Detection aktivieren
{
  "key_detection": {
    "algorithm": "krumhansl",  # oder "temperley"
    "use_harmonic_analysis": true,
    "confidence_threshold": 0.7
  }
}
```

### Performance

#### ❌ Langsame Analyse

**Problem**: Audio-Analyse dauert sehr lange

**Lösung**:
1. **Multi-Threading aktivieren**:
   ```python
   # In config/performance.json
   {
     "max_workers": 4,  # CPU-Kerne
     "batch_size": 10,
     "use_gpu": false  # Experimentell
   }
   ```

2. **Cache optimieren**:
   ```bash
   # Cache leeren
   python -c "from src.core.cache_manager import CacheManager; CacheManager().clear_cache()"
   
   # Cache-Größe erhöhen
   # config/cache_config.json: "max_size_mb": 1024
   ```

3. **Audio-Qualität reduzieren** (für Tests):
   ```python
   {
     "analysis": {
       "sample_rate": 22050,  # Statt 44100
       "duration_limit": 60   # Nur erste 60s analysieren
     }
   }
   ```

#### ❌ Hoher Speicherverbrauch

**Problem**: RAM-Verbrauch zu hoch

**Lösung**:
```python
# Memory Management optimieren
{
  "memory": {
    "max_tracks_in_memory": 50,
    "clear_cache_interval": 100,
    "use_memory_mapping": true
  }
}
```

### GUI-Probleme

#### ❌ Interface reagiert nicht

**Problem**: GUI friert ein

**Lösung**:
1. **Task Manager**: Prozess beenden und neu starten
2. **Safe Mode**: `python main.py --safe-mode`
3. **GUI-Reset**: Einstellungen zurücksetzen
   ```bash
   del config/gui_settings.json
   ```

#### ❌ Waveform wird nicht angezeigt

**Problem**: Leere Waveform-Anzeige

**Lösung**:
```python
# OpenGL-Probleme beheben
# In main.py vor GUI-Start:
import os
os.environ['QT_OPENGL'] = 'software'  # Software-Rendering

# Oder Waveform-Engine wechseln:
# config/gui_config.json
{
  "waveform": {
    "renderer": "matplotlib",  # Statt "opengl"
    "resolution": 1024
  }
}
```

### Export-Probleme

#### ❌ Rekordbox XML fehlerhaft

**Problem**: XML wird nicht importiert

**Lösung**:
1. **Rekordbox-Version prüfen**: Unterstützt v5.8.5+
2. **XML validieren**:
   ```bash
   python -c "from src.export.rekordbox_exporter import validate_xml; validate_xml('playlist.xml')"
   ```
3. **Backup erstellen**: Vor Import Collection.xml sichern

#### ❌ M3U-Pfade falsch

**Problem**: Tracks werden nicht gefunden

**Lösung**:
```python
# Pfad-Format anpassen
{
  "export": {
    "m3u_format": "relative",  # oder "absolute"
    "path_separator": "/",     # oder "\\"
    "encoding": "utf-8"
  }
}
```

## 🔍 Debug-Modus

### Erweiterte Logs aktivieren

```bash
# Debug-Modus starten
python main.py --debug --log-level DEBUG

# Oder in config/logging.json:
{
  "level": "DEBUG",
  "handlers": {
    "file": {
      "filename": "logs/debug.log",
      "max_size_mb": 50
    }
  }
}
```

### Performance-Profiling

```python
# Performance-Analyse
python -m cProfile -o profile.stats main.py

# Ergebnisse anzeigen:
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

### Memory-Profiling

```bash
# Memory-Leaks finden
pip install memory-profiler
python -m memory_profiler main.py
```

## 🆘 Support kontaktieren

### Informationen sammeln

Vor Support-Anfrage diese Informationen sammeln:

```bash
# System-Info
python --version
pip list | grep -E "(librosa|essentia|PyQt|numpy)"

# Log-Dateien
# logs/app.log (letzte 50 Zeilen)
# logs/error.log (alle Fehler)

# Konfiguration
# config/ Verzeichnis (ohne Passwörter)
```

### Bug-Report Template

```markdown
## Bug Report

**Beschreibung**: [Kurze Beschreibung des Problems]

**Schritte zur Reproduktion**:
1. [Schritt 1]
2. [Schritt 2]
3. [Schritt 3]

**Erwartetes Verhalten**: [Was sollte passieren]

**Tatsächliches Verhalten**: [Was passiert wirklich]

**System-Info**:
- OS: Windows 10/11
- Python: 3.x.x
- Tool Version: v2.0.x

**Log-Ausgabe**:
```
[Relevante Log-Zeilen hier einfügen]
```

**Screenshots**: [Falls relevant]
```

### Kontakt-Kanäle

| Priorität | Kanal | Antwortzeit |
|-----------|-------|-------------|
| 🚨 **Kritisch** | support@dj-audio-tool.com | 4h |
| 🐛 **Bug** | [GitHub Issues](https://github.com/username/repo/issues) | 24h |
| ❓ **Frage** | [Discord #support](https://discord.gg/dj-tools) | 2-8h |
| 💡 **Feature** | [GitHub Discussions](https://github.com/username/repo/discussions) | 1 Woche |

---

> 💡 **Tipp**: Die meisten Probleme lassen sich durch einen Neustart oder Cache-Reset lösen!