# Essentia Setup Guide

## Überblick

Essentia ist eine erweiterte Audio-Analyse-Bibliothek, die zusätzliche Features für die Musikanalyse bietet. Das DJ Audio-Analyse-Tool kann sowohl mit als auch ohne Essentia betrieben werden.

## Installation

### Linux/macOS (Empfohlen)

```bash
pip install essentia
```

### Windows

Essentia kann unter Windows Kompilierungsprobleme verursachen. Alternativen:

1. **Conda verwenden:**
   ```bash
   conda install -c mtg essentia
   ```

2. **Docker verwenden:**
   ```bash
   docker run -it mtgupf/essentia
   ```

3. **WSL (Windows Subsystem for Linux):**
   ```bash
   # In WSL Ubuntu/Debian
   sudo apt-get install essentia-extractor
   pip install essentia
   ```

## Features mit Essentia

Wenn Essentia verfügbar ist, werden folgende erweiterte Features aktiviert:

- **Erweiterte BPM-Erkennung:** Präzisere Tempo-Analyse
- **Harmonische Analyse:** Verbesserte Tonart-Erkennung
- **Spektrale Features:** Zusätzliche Audio-Deskriptoren
- **Mood Classification:** Erweiterte Stimmungs-Analyse
- **Music Extractor:** Umfassende Feature-Extraktion

## Fallback-Verhalten

Ohne Essentia nutzt das Tool:

- **Librosa:** Für BPM und grundlegende Audio-Analyse
- **Scipy:** Für spektrale Berechnungen
- **NumPy:** Für mathematische Operationen

## Überprüfung der Installation

Das Tool zeigt beim Start an, welche Bibliothek verwendet wird:

```
✓ Essentia verfügbar - erweiterte Features aktiviert
```

oder

```
⚠ Essentia nicht verfügbar - verwende nur librosa
```

## Troubleshooting

### Kompilierungsfehler

1. **Build Tools installieren:**
   - Windows: Visual Studio Build Tools
   - Linux: `build-essential`
   - macOS: Xcode Command Line Tools

2. **Alternative Installationsmethoden probieren:**
   - Conda statt pip
   - Vorkompilierte Wheels
   - Docker Container

### Performance-Unterschiede

- **Mit Essentia:** ~2-3x schnellere Analyse
- **Ohne Essentia:** Vollständig funktional, etwas langsamer

## Fazit

Essentia ist optional aber empfohlen für:
- Professionelle DJ-Anwendungen
- Große Musikbibliotheken
- Präzise harmonische Analyse

Das Tool funktioniert vollständig ohne Essentia und bietet automatisches Fallback-Verhalten.