# Enhanced Playlist Engine 🎵

Eine erweiterte Playlist-Engine für das Audio-Analyse-Tool mit intelligenten Algorithmen, intuitivem Wizard-Flow und professionellen Export-Funktionen.

## 🚀 Neue Features

### 1. **EnergyScore-Algorithmus**
- **Intelligente Energie-Bewertung** von 1-10 basierend auf:
  - RMS-Lautstärke
  - Spektralzentroid
  - Onset-Dichte
- **Adaptive Normalisierung** für konsistente Bewertungen
- **Batch-Verarbeitung** für große Musikbibliotheken

### 2. **4-Schritt Playlist Wizard**
- **Schritt 1**: Mood-Preset Auswahl mit visuellen Karten
- **Schritt 2**: Interaktive Energie-Kurven-Bearbeitung
- **Schritt 3**: Camelot Wheel für harmonische Übergänge
- **Schritt 4**: Export-Optionen und Feintuning

### 3. **Smart Suggestions Engine**
- **k-NN-basierte Ähnlichkeitssuche** (< 50ms Antwortzeit)
- **Surprise-Me-Engine** für kreative Entdeckungen
- **Kompatibilitäts-Scoring** basierend auf:
  - Tonart-Harmonie (Camelot Wheel)
  - BPM-Matching
  - Energie-Progression
  - Stimmungs-Kohärenz

### 4. **Interaktive Timeline**
- **Drag & Drop** Track-Bearbeitung
- **Live Energy-Graph** Visualisierung
- **Zoom-Funktionen** für präzise Bearbeitung
- **Playlist-Statistiken** in Echtzeit

### 5. **Erweiterte Export-Funktionen**
- **Rekordbox XML** mit Cue Points und Beat Grid
- **M3U Playlists** für universelle Kompatibilität
- **JSON Metadata** mit detaillierter Analyse
- **Batch-Export** für mehrere Playlists

## 📁 Projektstruktur

```
src/
├── audio_analysis/
│   ├── energy_score_extractor.py      # EnergyScore-Algorithmus
│   ├── mood_classifier_enhanced.py    # Erweiterte Stimmungsklassifikation
│   └── ...
├── playlist_engine/
│   ├── generator.py                   # Erweiterte Playlist-Generierung
│   └── similarity_engine.py           # k-NN Ähnlichkeits-Engine
├── gui/
│   ├── playlist_wizard.py             # 4-Schritt Wizard UI
│   ├── interactive_timeline.py        # Interaktive Timeline
│   └── ...
├── export/
│   └── rekordbox_exporter.py          # Erweiterte Export-Funktionen
└── ...
```

## 🎯 Verwendung

### Demo ausführen
```bash
python demo_enhanced_playlist.py
```

### Hauptanwendung starten
```bash
python src/main.py
```

### Programmatische Verwendung

```python
from playlist_engine.generator import PlaylistGenerator
from export.rekordbox_exporter import EnhancedExportManager

# Playlist Generator initialisieren
generator = PlaylistGenerator()

# Wizard-Flow starten
wizard_state = generator.start_wizard()

# Mood Preset wählen
wizard_state = generator.wizard_step_2("Progressive Journey")

# Energy Curve konfigurieren
energy_settings = {
    'duration': 60,
    'curve_type': 'progressive',
    'custom_points': [(0, 5), (30, 8), (60, 7)]
}
wizard_state = generator.wizard_step_3(energy_settings)

# Playlist generieren
playlist_result = generator.generate_from_wizard(wizard_state, tracks)

# Exportieren
export_manager = EnhancedExportManager()
export_results = export_manager.export_playlist(
    playlist_result, 
    "output/", 
    formats=['rekordbox', 'm3u', 'json']
)
```

## 🎨 UI-Komponenten

### Playlist Wizard
- **MoodPresetCard**: Visuelle Preset-Auswahl mit Emojis und Beschreibungen
- **EnergyCanvas**: Interaktive Energie-Kurven-Bearbeitung
- **CamelotWheel**: Tonart-Auswahl mit harmonischen Beziehungen

### Interactive Timeline
- **TrackBlock**: Drag & Drop Track-Elemente
- **EnergyGraph**: Live Energie-Verlauf
- **TimelineRuler**: Präzise Zeitnavigation

## 🔧 Algorithmen

### EnergyScore-Berechnung
```python
# Gewichtete Kombination von Audio-Features
energy_score = (
    rms_energy * 0.4 +           # Lautstärke
    spectral_centroid * 0.3 +    # Helligkeit
    onset_density * 0.3          # Rhythmische Aktivität
) * normalization_factor
```

### Similarity-Matching
```python
# k-NN basierte Ähnlichkeitssuche
feature_vector = [
    bpm_normalized,
    key_encoded,
    energy_score,
    mood_vector,
    spectral_features
]

similarity_score = cosine_similarity(track1_features, track2_features)
```

### Kompatibilitäts-Scoring
```python
compatibility = (
    key_compatibility * 0.3 +     # Camelot Wheel
    bpm_compatibility * 0.25 +    # BPM-Matching
    energy_compatibility * 0.25 + # Energie-Progression
    mood_compatibility * 0.2      # Stimmungs-Kohärenz
)
```

## 📊 Mood Presets

| Preset | Emoji | Beschreibung | Energy Curve |
|--------|-------|--------------|---------------|
| **Progressive Journey** | 🚀 | Sanfter Anstieg zu epischen Höhepunkten | 5→8→9→7 |
| **Deep Focus** | 🧘 | Konstante, beruhigende Energie | 3→4→3→3 |
| **Peak Time Energy** | 🔥 | Maximale Energie für Prime Time | 8→9→10→9 |
| **Sunset Chill** | 🌅 | Entspannter Ausklang | 6→4→3→2 |
| **Warm Up** | 🌱 | Allmählicher Energie-Aufbau | 4→5→6→7 |

## 🎹 Camelot Wheel Integration

### Harmonische Übergänge
- **Perfekte Matches**: Gleiche Position (z.B. 8A → 8A)
- **Energie-Wechsel**: A ↔ B (z.B. 8A → 8B)
- **Harmonische Schritte**: ±1 Position (z.B. 8A → 7A, 9A)
- **Dominante Wechsel**: +7 Positionen (z.B. 8A → 3A)

### Kompatibilitäts-Matrix
```
Von 8A kompatibel zu:
- 8A (100%) - Gleiche Tonart
- 8B (95%)  - Energie-Wechsel
- 7A (90%)  - Harmonischer Schritt
- 9A (90%)  - Harmonischer Schritt
- 3A (85%)  - Dominante
```

## 📤 Export-Formate

### Rekordbox XML
- **Vollständige Metadaten**: Title, Artist, BPM, Key, Genre
- **Cue Points**: Automatisch generiert basierend auf Track-Struktur
- **Beat Grid**: Präzise Beat-Positionen
- **Custom Tags**: Energy Score und Mood als Comments
- **Color Coding**: Similarity-basierte Farbkodierung

### M3U Playlist
- **Standard-Format** für universelle Player
- **Extended Info** mit Dauer und Metadaten
- **Relative/Absolute** Pfade unterstützt

### JSON Metadata
- **Detaillierte Analyse**: BPM/Energy/Key-Progressionen
- **Playlist-Statistiken**: Verteilungen und Trends
- **Export-Info**: Zeitstempel und Versionierung

## 🚀 Performance

### Optimierungen
- **k-NN Index Caching**: Schnelle Similarity-Suche (< 50ms)
- **Feature Vector Normalisierung**: Konsistente Ergebnisse
- **Batch Processing**: Effiziente Verarbeitung großer Libraries
- **Memory Management**: Optimierte Speichernutzung

### Benchmarks
- **Similarity Search**: < 50ms für 10.000 Tracks
- **Playlist Generation**: < 2s für 20-Track Playlist
- **Export Processing**: < 1s für Rekordbox XML

## 🔮 Zukünftige Erweiterungen

### Geplante Features
- **AI-basierte Mood Detection** mit Deep Learning
- **Crowd-sourced Tagging** für Community-Feedback
- **Live Performance Mode** mit Echtzeit-Anpassungen
- **Streaming Integration** (Spotify, Apple Music)
- **Advanced Waveform Analysis** für präzise Cue Points

### API-Erweiterungen
- **REST API** für externe Integrationen
- **Plugin System** für Custom Algorithmen
- **Cloud Sync** für Playlist-Sharing

## 🛠️ Entwicklung

### Setup
```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Tests ausführen
python -m pytest tests/

# Demo starten
python demo_enhanced_playlist.py
```

### Architektur-Prinzipien
- **Modulare Komponenten**: Lose gekoppelte Module
- **Performance-First**: Optimiert für große Musikbibliotheken
- **Extensible Design**: Einfache Erweiterung neuer Features
- **User-Centric**: Intuitive Benutzeroberfläche

## 📝 Changelog

### Version 2.0.0 (Aktuell)
- ✨ **Neu**: 4-Schritt Playlist Wizard
- ✨ **Neu**: EnergyScore-Algorithmus
- ✨ **Neu**: Smart Suggestions Engine
- ✨ **Neu**: Interaktive Timeline
- ✨ **Neu**: Erweiterte Rekordbox-Integration
- 🔧 **Verbessert**: Performance-Optimierungen
- 🔧 **Verbessert**: UI/UX-Überarbeitung

### Version 1.0.0
- 🎵 Basis Playlist-Generierung
- 📊 Grundlegende Audio-Analyse
- 📤 Standard-Export-Funktionen

## 🤝 Beitragen

Beiträge sind willkommen! Bitte beachten Sie:

1. **Code Style**: Folgen Sie PEP 8
2. **Tests**: Fügen Sie Tests für neue Features hinzu
3. **Dokumentation**: Aktualisieren Sie die Dokumentation
4. **Performance**: Beachten Sie Performance-Auswirkungen

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe LICENSE-Datei für Details.

## 🙏 Danksagungen

- **Essentia**: Audio-Analyse-Framework
- **Librosa**: Audio-Processing-Library
- **PySide6**: GUI-Framework
- **scikit-learn**: Machine Learning-Tools
- **Community**: Feedback und Beiträge

---

**Enhanced Playlist Engine** - Intelligente Playlist-Generierung für DJs und Musikproduzenten 🎵