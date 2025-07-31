# DJ Audio-Analyse-Tool Pro v2.0

Professionelle Audio-Analyse-Software für DJs mit erweiterten Features für intelligente Playlist-Erstellung und harmonische Mixing-Unterstützung.

## 🎵 Features

### Kern-Features
- **Erweiterte Audio-Analyse** mit Essentia und librosa
- **Hybrid Mood-Classifier** kombiniert heuristische Regeln mit Machine Learning
- **Intelligente Playlist-Engine** mit verschiedenen Sortieralgorithmen
- **Interaktive Camelot Wheel** für harmonische Kompatibilität
- **Rekordbox-Integration** für nahtlosen Workflow
- **Cache-Management** für schnelle Wiederverwendung von Analysen

### Audio-Analyse
- BPM-Erkennung mit hoher Genauigkeit
- Tonart-Erkennung und Camelot Wheel Mapping
- Energie- und Stimmungsanalyse
- Spektrale Features (MFCC, Chroma, Spectral Centroid)
- Rhythmus- und Takt-Analyse

### Playlist-Erstellung
- **Harmonische Kompatibilität**: Basierend auf Camelot Wheel
- **Energie-Verlauf**: Gradueller Aufbau, Peak & Valley, konstant
- **Stimmungs-Progression**: Kohärent, kontrastreich, aufbauend
- **BPM-Übergänge**: Intelligente Tempo-Anpassung
- **Benutzerdefinierte Presets**: Speichern und teilen von Playlist-Regeln

### Export-Optionen
- M3U Playlist-Format
- Rekordbox XML für DJ-Software Integration
- JSON-Export für Datenanalyse
- Detaillierte Analyse-Reports

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher
- Windows 10/11 (andere Betriebssysteme experimentell)
- Mindestens 4 GB RAM
- 2 GB freier Festplattenspeicher

### Schnellstart

1. **Repository klonen oder herunterladen**
   ```bash
   git clone <repository-url>
   cd Audio_Analyse_tool
   ```

2. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

3. **Anwendung starten**
   - **Windows**: Doppelklick auf `start.bat`
   - **Kommandozeile**: `python main.py`

### Manuelle Installation

1. **Python-Umgebung einrichten**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # oder
   source venv/bin/activate  # Linux/Mac
   ```

2. **Kern-Abhängigkeiten installieren**
   ```bash
   pip install PySide6 librosa numpy scipy soundfile mutagen pandas
   ```

3. **Erweiterte Abhängigkeiten installieren**
   ```bash
   pip install lightgbm essentia-tensorflow
   ```

## 📖 Nutzung

### Erste Schritte

1. **Dateien hinzufügen**
   - Klicken Sie auf "Dateien hinzufügen" oder "Ordner hinzufügen"
   - Unterstützte Formate: MP3, WAV, FLAC, AAC, OGG, M4A

2. **Analyse starten**
   - Klicken Sie auf "Analyse starten"
   - Der Fortschritt wird in der Statusleiste angezeigt
   - Analysierte Tracks erscheinen in der Tracks-Tabelle

3. **Playlist erstellen**
   - Wählen Sie ein Preset aus der Dropdown-Liste
   - Klicken Sie auf "Playlist erstellen"
   - Die generierte Playlist erscheint im Playlist-Tab

4. **Export**
   - Wählen Sie das gewünschte Export-Format
   - Speichern Sie die Playlist oder Analyse-Daten

### Erweiterte Features

#### Camelot Wheel
- Klicken Sie auf einen Key im Camelot Wheel
- Kompatible Tracks werden in der Tabelle hervorgehoben
- Nutzen Sie dies für harmonisches Mixing

#### Preset-Erstellung
- Klicken Sie auf "Neues Preset"
- Konfigurieren Sie Algorithmus, Energie-Verlauf und Regeln
- Speichern Sie das Preset für wiederholte Nutzung

#### Cache-Management
- Analysierte Tracks werden automatisch gecacht
- Verwalten Sie den Cache über Tools → Cache verwalten
- Löschen Sie alte Einträge bei Bedarf

## 🎛️ Playlist-Algorithmen

### Harmonische Kompatibilität
Basiert auf dem Camelot Wheel System:
- Identische Keys (perfekte Harmonie)
- Benachbarte Keys (±1 Semitone)
- Relative Major/Minor Keys

### Energie-Verläufe
- **Gradueller Aufbau**: Langsamer Energie-Anstieg
- **Peak & Valley**: Wechsel zwischen hoher und niedriger Energie
- **Konstant**: Gleichmäßige Energie-Level
- **Benutzerdefiniert**: Eigene Energie-Kurven

### Stimmungs-Progressionen
- **Kohärent**: Ähnliche Stimmungen
- **Kontrastreich**: Abwechselnde Stimmungen
- **Aufbauend**: Von ruhig zu energetisch
- **Gemischt**: Ausgewogene Mischung

## 🔧 Konfiguration

### Mood-Classifier Einstellungen
Die Hybrid-Klassifikation kann angepasst werden:
- Heuristische Regeln in `src/core/mood_classifier/mood_rules.py`
- ML-Modell Parameter in `src/core/mood_classifier/ml_classifier.py`
- Feature-Gewichtungen in `src/core/mood_classifier/feature_processor.py`

### Cache-Einstellungen
- Standard-Cache-Größe: 1 GB
- Automatische Bereinigung nach 30 Tagen
- Konfigurierbar in `src/core/cache_manager.py`

### Performance-Optimierung
- Multiprocessing für Batch-Analysen
- Essentia für erweiterte Audio-Features
- LightGBM für schnelle ML-Klassifikation

## 📁 Projektstruktur

```
Audio_Analyse_tool/
├── main.py                 # Hauptanwendung
├── start.bat              # Windows-Startskript
├── requirements.txt       # Python-Abhängigkeiten
├── README.md             # Diese Datei
├── src/
│   ├── core/             # Kern-Module
│   │   ├── mood_classifier/  # Stimmungsklassifikation
│   │   ├── cache_manager.py  # Cache-Verwaltung
│   │   └── playlist_engine.py # Playlist-Erstellung
│   ├── audio_analysis/   # Audio-Analyse
│   │   └── analyzer.py   # Haupt-Analyzer
│   ├── export/          # Export-Module
│   │   └── playlist_exporter.py
│   └── gui/             # Benutzeroberfläche
│       └── main_window.py
├── cache/               # Cache-Verzeichnis
├── exports/            # Export-Verzeichnis
├── presets/           # Gespeicherte Presets
└── logs/              # Log-Dateien
```

## 🐛 Fehlerbehebung

### Häufige Probleme

**"Essentia nicht gefunden"**
```bash
pip install essentia-tensorflow
# oder für CPU-only:
pip install essentia
```

**"LightGBM Installation fehlgeschlagen"**
```bash
# Windows:
pip install lightgbm
# Bei Problemen:
conda install lightgbm
```

**"Audio-Datei kann nicht geladen werden"**
- Überprüfen Sie das Dateiformat
- Stellen Sie sicher, dass die Datei nicht beschädigt ist
- Installieren Sie zusätzliche Codecs falls nötig

**Performance-Probleme**
- Reduzieren Sie die Anzahl paralleler Threads
- Leeren Sie den Cache regelmäßig
- Schließen Sie andere ressourcenintensive Programme

### Log-Dateien
Log-Dateien finden Sie in:
- `dj_tool_pro.log` (Hauptanwendung)
- `logs/` Verzeichnis (detaillierte Logs)

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:
1. Forken Sie das Repository
2. Erstellen Sie einen Feature-Branch
3. Committen Sie Ihre Änderungen
4. Erstellen Sie einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe LICENSE-Datei für Details.

## 🙏 Danksagungen

- **Essentia** für erweiterte Audio-Analyse
- **librosa** für Audio-Processing
- **LightGBM** für Machine Learning
- **PySide6** für die moderne GUI
- **Camelot Wheel** System für harmonische Mixing-Theorie

## 📞 Support

Bei Fragen oder Problemen:
1. Überprüfen Sie die Fehlerbehebung oben
2. Schauen Sie in die Log-Dateien
3. Erstellen Sie ein Issue im Repository
4. Kontaktieren Sie den Support

---

**DJ Audio-Analyse-Tool Pro v2.0** - Professionelle Audio-Analyse für DJs