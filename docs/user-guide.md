# User Guide - DJ Audio-Analyse-Tool Pro

Umfassende Bedienungsanleitung für alle Funktionen des DJ Audio-Analyse-Tools Pro v2.0.

## 📖 Inhaltsverzeichnis

1. [Benutzeroberfläche](#benutzeroberfläche)
2. [Audio-Import und -Verwaltung](#audio-import-und--verwaltung)
3. [Audio-Analyse](#audio-analyse)
4. [Playlist-Erstellung](#playlist-erstellung)
5. [Track-Browser](#track-browser)
6. [Export-Funktionen](#export-funktionen)
7. [Einstellungen und Konfiguration](#einstellungen-und-konfiguration)
8. [Erweiterte Features](#erweiterte-features)
9. [Workflow-Tipps](#workflow-tipps)

## 🖥️ Benutzeroberfläche

### Hauptfenster-Layout

Das Hauptfenster ist in mehrere Bereiche unterteilt:

```
┌─────────────────────────────────────────────────────────┐
│ Menüleiste: [Datei] [Bearbeiten] [Tools] [Hilfe]       │
├─────────────────────────────────────────────────────────┤
│ Toolbar: [📁] [🎵] [▶️] [🎯] [💾] [⚙️]                │
├─────────────────────────────────────────────────────────┤
│ Tab-Leiste: [Tracks] [Playlist] [Browser] [Export]     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                 Hauptarbeitsbereich                    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Statusleiste: [Status] [Cache] [Preview] [Progress]    │
└─────────────────────────────────────────────────────────┘
```

### Menüleiste

#### Datei-Menü
- **Dateien hinzufügen** (Ctrl+F): Einzelne Audio-Dateien importieren
- **Ordner hinzufügen** (Ctrl+O): Komplette Verzeichnisse scannen
- **Projekt speichern** (Ctrl+S): Aktuellen Zustand speichern
- **Projekt laden** (Ctrl+L): Gespeicherten Zustand laden
- **Beenden** (Alt+F4): Anwendung schließen

#### Bearbeiten-Menü
- **Rückgängig** (Ctrl+Z): Letzte Aktion rückgängig machen
- **Wiederholen** (Ctrl+Y): Aktion wiederholen
- **Alle auswählen** (Ctrl+A): Alle Tracks auswählen
- **Auswahl umkehren** (Ctrl+I): Auswahl invertieren
- **Löschen** (Del): Ausgewählte Tracks entfernen

#### Tools-Menü
- **Analyse starten** (F5): Audio-Analyse für alle Tracks
- **Cache verwalten**: Cache-Verwaltung öffnen
- **Batch-Export**: Mehrere Playlists exportieren
- **Einstellungen** (F12): Konfigurationsdialog öffnen

### Toolbar-Buttons

| Icon | Funktion | Beschreibung |
|------|----------|-------------|
| 📁 | Ordner hinzufügen | Musikverzeichnis scannen |
| 🎵 | Dateien hinzufügen | Einzelne Dateien importieren |
| ▶️ | Analyse starten | Audio-Analyse durchführen |
| 🎯 | Playlist erstellen | Intelligente Playlist generieren |
| 💾 | Export | Playlist/Daten exportieren |
| ⚙️ | Einstellungen | Konfiguration öffnen |

## 🎵 Audio-Import und -Verwaltung

### Unterstützte Dateiformate

| Format | Erweiterung | Qualität | Metadaten |
|--------|-------------|----------|----------|
| MP3 | .mp3 | Verlustbehaftet | ID3v1/v2 |
| WAV | .wav | Verlustfrei | Begrenzt |
| FLAC | .flac | Verlustfrei | Vorbis Comments |
| AAC | .aac, .m4a | Verlustbehaftet | iTunes Tags |
| OGG | .ogg | Verlustbehaftet | Vorbis Comments |
| AIFF | .aiff, .aif | Verlustfrei | ID3v2 |

### Import-Methoden

#### Einzelne Dateien hinzufügen

1. **Über Toolbar**: Klick auf 🎵 "Dateien hinzufügen"
2. **Über Menü**: Datei → Dateien hinzufügen
3. **Tastenkürzel**: Ctrl+F
4. **Drag & Drop**: Dateien direkt ins Hauptfenster ziehen

**Mehrfachauswahl**: Ctrl+Klick oder Shift+Klick für mehrere Dateien

#### Ordner hinzufügen

1. **Rekursive Suche**: Alle Unterordner werden durchsucht
2. **Filter-Optionen**: Nur bestimmte Dateiformate
3. **Duplikat-Erkennung**: Automatische Erkennung bereits importierter Dateien

```
Beispiel-Ordnerstruktur:
C:\Music\
├── House\
│   ├── Deep House\
│   └── Progressive House\
├── Techno\
└── Ambient\

→ Alle Unterordner werden automatisch gescannt
```

#### Batch-Import-Einstellungen

```json
{
  "import": {
    "recursive_scan": true,
    "skip_duplicates": true,
    "auto_analyze": false,
    "supported_formats": ["mp3", "wav", "flac", "aac", "ogg", "aiff"],
    "max_file_size_mb": 100,
    "min_duration_seconds": 30
  }
}
```

### Track-Verwaltung

#### Track-Informationen

Jeder importierte Track zeigt folgende Informationen:

| Feld | Beschreibung | Quelle |
|------|--------------|--------|
| Titel | Song-Titel | Metadaten/Dateiname |
| Künstler | Interpret | Metadaten |
| Album | Album-Name | Metadaten |
| Dauer | Track-Länge | Audio-Analyse |
| Dateigröße | Größe in MB | Dateisystem |
| Format | Audio-Format | Datei-Header |
| Bitrate | Qualität in kbps | Audio-Stream |
| Sample Rate | Abtastrate in Hz | Audio-Stream |

#### Track-Status

- 🔄 **Importiert**: Track wurde hinzugefügt, aber noch nicht analysiert
- ⚡ **Analysiert**: Audio-Analyse abgeschlossen
- ❌ **Fehler**: Analyse fehlgeschlagen
- 🔒 **Gesperrt**: Datei ist schreibgeschützt oder in Verwendung
- ✅ **Bereit**: Track ist für Playlist-Erstellung verfügbar

## 🔍 Audio-Analyse

### Analyse-Parameter

#### BPM-Erkennung (Beats Per Minute)

**Algorithmus**: Essentia BeatTrackerMultiFeature + librosa beat_track

**Genauigkeit**:
- Standard: ±0.5 BPM
- Hoch: ±0.1 BPM
- Sehr hoch: ±0.05 BPM (langsamer)

**Besonderheiten**:
- Automatische Erkennung von halben/doppelten BPM
- Unterstützung für variable BPM (Tempo-Änderungen)
- Manuelle Korrektur möglich

#### Key-Erkennung (Tonart)

**Algorithmus**: Essentia KeyExtractor + Camelot Wheel Mapping

**Ausgabeformate**:
- **Musikalisch**: C, C#, D, D#, E, F, F#, G, G#, A, A#, B
- **Camelot**: 1A-12A (Moll), 1B-12B (Dur)
- **Open Key**: 1m-12m (Moll), 1d-12d (Dur)

**Konfidenz-Level**:
- Hoch (>0.8): Sehr zuverlässig
- Mittel (0.5-0.8): Meist korrekt
- Niedrig (<0.5): Manuelle Überprüfung empfohlen

#### Energie-Analyse

**Komponenten**:
1. **RMS Energy**: Durchschnittliche Lautstärke
2. **Spectral Centroid**: Helligkeit/Brillanz
3. **Onset Density**: Anzahl der Beats/Ereignisse
4. **Dynamic Range**: Lautstärke-Variation

**Energie-Skala**: 0-100%
- 0-30%: Ruhig, Ambient
- 30-60%: Moderat, Lounge
- 60-80%: Energetisch, Dance
- 80-100%: Sehr energetisch, Peak Time

#### Stimmungs-Klassifikation

**Hybrid-Ansatz**: Heuristische Regeln + Machine Learning

**Stimmungs-Kategorien**:
- **Düster**: Moll-Tonarten, niedrige Energie
- **Melancholisch**: Langsame BPM, Moll-Tonarten
- **Neutral**: Ausgewogene Parameter
- **Fröhlich**: Dur-Tonarten, mittlere Energie
- **Energetisch**: Hohe BPM, hohe Energie
- **Euphorisch**: Sehr hohe Energie, Dur-Tonarten
- **Treibend**: Hohe Onset Density, konstante BPM

### Analyse-Prozess

#### Automatische Analyse

1. **Batch-Verarbeitung**: Alle Tracks werden parallel analysiert
2. **Fortschrittsanzeige**: Real-time Updates in der Statusleiste
3. **Fehlerbehandlung**: Defekte Dateien werden übersprungen
4. **Cache-System**: Ergebnisse werden für schnelle Wiederverwendung gespeichert

#### Manuelle Analyse

**Einzeltrack-Analyse**:
- Rechtsklick auf Track → "Erneut analysieren"
- Für Tracks mit niedrigem Konfidenz-Level
- Nach manueller Korrektur von Metadaten

**Parameter-Anpassung**:
```json
{
  "analysis": {
    "bpm_range": [60, 200],
    "key_confidence_threshold": 0.7,
    "energy_smoothing": 0.1,
    "mood_weights": {
      "valence": 0.4,
      "energy": 0.3,
      "tempo": 0.2,
      "mode": 0.1
    }
  }
}
```

### Cache-System

#### Cache-Struktur

```json
{
  "file_path": "/path/to/track.mp3",
  "file_hash": "sha256_hash",
  "analysis_version": "2.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "results": {
    "bpm": 128.0,
    "key": "Am",
    "camelot": "8A",
    "energy": 75.5,
    "mood": "energetic",
    "confidence": {
      "bpm": 0.95,
      "key": 0.87,
      "energy": 0.92,
      "mood": 0.78
    }
  }
}
```

#### Cache-Verwaltung

**Automatische Bereinigung**:
- Alte Einträge (>30 Tage) werden entfernt
- Ungültige Dateipfade werden bereinigt
- Cache-Größe wird überwacht (Standard: 1 GB)

**Manuelle Verwaltung**:
- Tools → Cache verwalten
- Cache leeren, Statistiken anzeigen
- Einzelne Einträge löschen

## 🎼 Playlist-Erstellung

### Playlist-Engine

#### Algorithmen-Übersicht

1. **Harmonische Kompatibilität**: Basiert auf Camelot Wheel
2. **Energie-Verlauf**: Verschiedene Kurven-Typen
3. **BPM-Progression**: Intelligente Tempo-Übergänge
4. **Stimmungs-Kohärenz**: Konsistente emotionale Entwicklung

#### Preset-System

**Vordefinierte Presets**:

| Preset | BPM-Bereich | Energie-Verlauf | Harmonie | Beschreibung |
|--------|-------------|-----------------|----------|-------------|
| Progressive House | 120-130 | Graduell aufbauend | Strikt | Klassischer Progressive Build-up |
| Peak Time | 128-135 | Konstant hoch | Moderat | Energie für Prime Time |
| Warm-Up | 110-125 | Langsam aufbauend | Strikt | Sanfter Einstieg |
| Cool-Down | 100-120 | Abfallend | Locker | Entspannter Ausklang |
| Experimental | 80-160 | Chaotisch | Locker | Überraschende Kombinationen |
| Deep House | 115-125 | Wellenförmig | Strikt | Tiefe, hypnotische Grooves |
| Techno Drive | 125-140 | Konstant | Moderat | Treibende Techno-Energie |

#### Custom Presets erstellen

1. **Basis-Parameter**:
   ```json
   {
     "name": "Mein Custom Preset",
     "description": "Beschreibung des Presets",
     "bpm_range": [120, 130],
     "energy_curve": "gradual_buildup",
     "harmony_strictness": 0.8,
     "mood_consistency": 0.7
   }
   ```

2. **Erweiterte Regeln**:
   ```json
   {
     "rules": {
       "max_bpm_jump": 3,
       "key_compatibility": "camelot_wheel",
       "energy_smoothing": 0.2,
       "avoid_back_to_back_same_artist": true,
       "min_track_duration": 180,
       "max_track_duration": 480
     }
   }
   ```

### Camelot Wheel Integration

#### Harmonische Kompatibilität

**Perfekte Matches**:
- Identische Keys (z.B. 8A → 8A)
- Relative Major/Minor (z.B. 8A → 8B)

**Gute Matches**:
- ±1 Semitone (z.B. 8A → 7A oder 9A)
- Dominante Beziehungen (z.B. 8A → 3A)

**Kompatibilitäts-Matrix**:
```
    1A  2A  3A  4A  5A  6A  7A  8A  9A 10A 11A 12A
1A  ✓   ○   ○   ○   ○   ○   ○   ○   ○   ○   ○   ✓
2A  ✓   ✓   ○   ○   ○   ○   ○   ○   ○   ○   ○   ○
...

✓ = Perfekt, ○ = Gut, ✗ = Vermeiden
```

#### Interaktive Camelot Wheel

**Funktionen**:
- Klick auf Key → Kompatible Tracks hervorheben
- Hover → Kompatibilitäts-Info anzeigen
- Drag & Drop → Tracks zu Keys zuordnen
- Filter → Nur bestimmte Keys anzeigen

### Energie-Kurven

#### Kurven-Typen

1. **Gradueller Aufbau**:
   ```
   Energie
   100% ┤                    ╭─
    80% ┤                ╭───╯
    60% ┤            ╭───╯
    40% ┤        ╭───╯
    20% ┤    ╭───╯
     0% ┤╭───╯
        └┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─ Zeit
   ```

2. **Peak & Valley**:
   ```
   Energie
   100% ┤    ╭─╮        ╭─╮
    80% ┤   ╱   ╲      ╱   ╲
    60% ┤  ╱     ╲    ╱     ╲
    40% ┤ ╱       ╲  ╱       ╲
    20% ┤╱         ╲╱         ╲
     0% ┤                     ╲
        └┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─ Zeit
   ```

3. **Konstant**:
   ```
   Energie
   100% ┤
    80% ┤─────────────────────
    60% ┤
    40% ┤
    20% ┤
     0% ┤
        └┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─ Zeit
   ```

#### Benutzerdefinierte Kurven

**Bezier-Kurven-Editor**:
- Drag & Drop Kontrollpunkte
- Real-time Vorschau
- Speichern als Preset
- Import/Export von Kurven

### Playlist-Optimierung

#### Beam Search Algorithmus

**Parameter**:
- Beam Width: Anzahl paralleler Pfade (Standard: 5)
- Lookahead: Vorausschau-Tiefe (Standard: 3)
- Scoring Function: Bewertungsfunktion für Übergänge

**Scoring-Faktoren**:
```python
score = (
    harmony_score * 0.4 +
    energy_score * 0.3 +
    bpm_score * 0.2 +
    mood_score * 0.1
)
```

#### k-NN Similarity Engine

**Feature-Vektor**:
```python
features = [
    bpm_normalized,
    energy_level,
    valence,
    danceability,
    acousticness,
    instrumentalness,
    key_numeric,
    mode_numeric
]
```

**Distanz-Metriken**:
- Euklidische Distanz (Standard)
- Manhattan Distanz
- Cosinus-Ähnlichkeit
- Gewichtete Distanz

## 🔍 Track-Browser

### Detailansicht

#### Track-Informationen

**Metadaten-Panel**:
```
┌─────────────────────────────────────┐
│ 🎵 Track: "Example Song"            │
│ 👤 Artist: "Example Artist"         │
│ 💿 Album: "Example Album"           │
│ 📅 Jahr: 2023                       │
│ ⏱️ Dauer: 4:32                      │
│ 📁 Datei: example.mp3               │
│ 💾 Größe: 8.5 MB                    │
│ 🎚️ Bitrate: 320 kbps               │
└─────────────────────────────────────┘
```

**Analyse-Ergebnisse**:
```
┌─────────────────────────────────────┐
│ 🥁 BPM: 128.0 (Konfidenz: 95%)     │
│ 🎹 Key: Am / 8A (Konfidenz: 87%)   │
│ ⚡ Energie: 75% (Hoch)              │
│ 😊 Stimmung: Energetisch            │
│ 🎯 Tanzbarkeit: 85%                 │
│ 🎼 Instrumentalness: 15%            │
└─────────────────────────────────────┘
```

#### Waveform-Anzeige

**Features**:
- Zoom-Funktion (1x bis 100x)
- Cue-Point-Markierungen
- Beat-Grid-Overlay
- Energie-Verlauf-Overlay
- Spektrogramm-Ansicht

**Interaktion**:
- Klick → Playback-Position setzen
- Drag → Bereich auswählen
- Doppelklick → Cue-Point setzen
- Rechtsklick → Kontextmenü

### Filter-System

#### Basis-Filter

| Filter | Typ | Optionen |
|--------|-----|----------|
| BPM | Range-Slider | 60-200 BPM |
| Key | Multi-Select | Alle 24 Keys |
| Energie | Range-Slider | 0-100% |
| Stimmung | Dropdown | 7 Kategorien |
| Dauer | Range-Slider | 0-20 Minuten |
| Format | Checkboxes | MP3, WAV, FLAC, etc. |

#### Erweiterte Filter

**Kombinierte Filter**:
```json
{
  "filter_name": "Peak Time Tracks",
  "conditions": {
    "bpm": {"min": 128, "max": 135},
    "energy": {"min": 80, "max": 100},
    "mood": ["energetic", "euphoric"],
    "key_compatibility": "8A",
    "duration": {"min": 300, "max": 420}
  }
}
```

**Smart Filter**:
- "Ähnlich zu diesem Track": k-NN basierte Suche
- "Harmonisch kompatibel": Camelot Wheel Filter
- "Energie-passend": ±10% Energie-Bereich
- "BPM-kompatibel": ±5 BPM Bereich

### Sortierung

#### Standard-Sortierungen

| Kriterium | Aufsteigend | Absteigend |
|-----------|-------------|------------|
| Titel | A-Z | Z-A |
| Künstler | A-Z | Z-A |
| BPM | Langsam → Schnell | Schnell → Langsam |
| Energie | Ruhig → Energetisch | Energetisch → Ruhig |
| Dauer | Kurz → Lang | Lang → Kurz |
| Hinzugefügt | Alt → Neu | Neu → Alt |

#### Intelligente Sortierung

**Playlist-optimiert**:
- Harmonische Reihenfolge (Camelot Wheel)
- Energie-Verlauf optimiert
- BPM-Progression
- Stimmungs-Kohärenz

**Multi-Kriterien-Sortierung**:
1. Primär: BPM (aufsteigend)
2. Sekundär: Energie (aufsteigend)
3. Tertiär: Key (harmonisch)

## 💾 Export-Funktionen

### Unterstützte Formate

#### Playlist-Formate

| Format | Erweiterung | Kompatibilität | Features |
|--------|-------------|----------------|----------|
| M3U | .m3u | Universal | Basis-Playlist |
| M3U8 | .m3u8 | Universal + UTF-8 | Unicode-Support |
| PLS | .pls | Winamp, VLC | Erweiterte Metadaten |
| XSPF | .xspf | XML-basiert | Vollständige Metadaten |
| Rekordbox XML | .xml | Rekordbox | Native Integration |
| Serato | .crate | Serato DJ | Cue-Points, Loops |
| Traktor | .nml | Traktor Pro | Beatgrids, Cues |

#### Daten-Export

| Format | Erweiterung | Verwendung |
|--------|-------------|------------|
| JSON | .json | Datenanalyse, Backup |
| CSV | .csv | Excel, Statistiken |
| XML | .xml | Strukturierte Daten |
| TXT | .txt | Einfache Listen |

### Rekordbox-Integration

#### XML-Export

**Features**:
- Native Rekordbox-Kompatibilität
- Automatische Pfad-Konvertierung
- Cue-Point-Export
- Beatgrid-Information
- Hot Cue-Markierungen

**Export-Optionen**:
```json
{
  "rekordbox_export": {
    "include_analysis": true,
    "include_cues": true,
    "include_beatgrid": true,
    "path_format": "relative",
    "backup_original": true,
    "merge_with_existing": true
  }
}
```

#### Collection.xml Integration

**Sicherheitsfeatures**:
- Automatisches Backup vor Änderungen
- Validierung der XML-Struktur
- Rollback-Funktion bei Fehlern
- Duplikat-Erkennung

**Merge-Strategien**:
- **Überschreiben**: Neue Daten ersetzen alte
- **Ergänzen**: Nur neue Tracks hinzufügen
- **Intelligent**: Bessere Analyse-Daten bevorzugen

### Batch-Export

#### Multi-Playlist-Export

**Workflow**:
1. Mehrere Playlists auswählen
2. Export-Format wählen
3. Zielverzeichnis festlegen
4. Batch-Export starten

**Naming-Conventions**:
```
Playlist_Name_YYYYMMDD_HHMMSS.format

Beispiel:
Progressive_House_20250115_143022.m3u
Peak_Time_20250115_143023.xml
```

#### Export-Templates

**Vordefinierte Templates**:
- **DJ Set**: M3U + Cue-Sheet
- **Radio Show**: M3U8 + Timing-Info
- **Rekordbox**: XML + Backup
- **Analyse-Report**: JSON + CSV
- **Backup**: Alle Formate

## ⚙️ Einstellungen und Konfiguration

### Audio-Einstellungen

#### Analyse-Parameter

```json
{
  "audio_analysis": {
    "quality_preset": "high",
    "use_essentia": true,
    "use_librosa": true,
    "bpm_detection": {
      "algorithm": "multifeature",
      "range": [60, 200],
      "accuracy": 0.1,
      "confidence_threshold": 0.8
    },
    "key_detection": {
      "algorithm": "krumhansl",
      "confidence_threshold": 0.7,
      "use_harmonic_analysis": true
    },
    "energy_analysis": {
      "window_size": 2048,
      "hop_length": 512,
      "smoothing_factor": 0.1
    }
  }
}
```

#### Performance-Einstellungen

```json
{
  "performance": {
    "max_workers": 4,
    "batch_size": 10,
    "memory_limit_gb": 4,
    "cache_enabled": true,
    "parallel_analysis": true,
    "gpu_acceleration": false
  }
}
```

### GUI-Einstellungen

#### Theme-Konfiguration

```json
{
  "ui": {
    "theme": "dark",
    "accent_color": "#0066cc",
    "font_family": "Segoe UI",
    "font_size": 12,
    "show_tooltips": true,
    "animation_enabled": true,
    "auto_save_layout": true
  }
}
```

#### Layout-Optionen

- **Compact**: Platzsparende Ansicht
- **Standard**: Ausgewogenes Layout
- **Expanded**: Maximale Information
- **Custom**: Benutzerdefiniert

### Pfad-Verwaltung

#### Standard-Verzeichnisse

```json
{
  "paths": {
    "music_library": "C:\\Users\\[User]\\Music",
    "export_directory": "./exports",
    "cache_directory": "./cache",
    "presets_directory": "./presets",
    "logs_directory": "./logs",
    "temp_directory": "%TEMP%\\dj_tool"
  }
}
```

#### Rekordbox-Pfade

```json
{
  "rekordbox": {
    "installation_path": "C:\\Program Files\\Pioneer\\rekordbox",
    "collection_xml": "%APPDATA%\\Pioneer\\rekordbox\\collection.xml",
    "analysis_folder": "%APPDATA%\\Pioneer\\rekordbox\\share",
    "auto_detect": true
  }
}
```

## 🚀 Erweiterte Features

### Smart Suggestions

#### Kontext-basierte Vorschläge

**Algorithmus**: Kombiniert mehrere Faktoren für intelligente Empfehlungen

**Faktoren**:
1. **Harmonische Kompatibilität** (40%)
2. **Energie-Verlauf** (30%)
3. **BPM-Kompatibilität** (20%)
4. **Stimmungs-Kohärenz** (10%)

**Anwendungsfälle**:
- "Was passt nach diesem Track?"
- "Finde ähnliche Tracks"
- "Vervollständige diese Playlist"
- "Übergangs-Vorschläge"

#### Machine Learning Integration

**LightGBM Mood Classifier**:
- Training auf 10.000+ gelabelten Tracks
- Feature-Engineering mit librosa
- Cross-Validation für Robustheit
- Kontinuierliches Learning

**Feature-Importance**:
```
Spectral Centroid:     25%
MFCC Features:         20%
Chroma Features:       15%
Tempo:                 15%
RMS Energy:            10%
Zero Crossing Rate:    10%
Spectral Rolloff:       5%
```

### Surprise-Me Engine

#### Chaos-Parameter

**Slider-Einstellungen**:
- **0% (Strikt)**: Perfekte harmonische Übergänge
- **25% (Konservativ)**: Kleine Abweichungen erlaubt
- **50% (Ausgewogen)**: Mix aus Vorhersagbar und Überraschend
- **75% (Experimentell)**: Größere Sprünge möglich
- **100% (Chaotisch)**: Völlig unvorhersagbare Kombinationen

**Algorithmus**:
```python
def surprise_factor(chaos_level):
    harmony_weight = 1.0 - (chaos_level * 0.6)
    random_weight = chaos_level * 0.8
    
    return {
        'harmony': harmony_weight,
        'energy_jump': chaos_level * 0.4,
        'bpm_jump': chaos_level * 0.3,
        'mood_switch': chaos_level * 0.5,
        'randomness': random_weight
    }
```

### Multi-Format Support

#### Erweiterte Codecs

**Lossless Formate**:
- FLAC: Free Lossless Audio Codec
- ALAC: Apple Lossless Audio Codec
- WAV: Uncompressed PCM
- AIFF: Audio Interchange File Format

**Lossy Formate**:
- MP3: MPEG-1 Audio Layer III
- AAC: Advanced Audio Coding
- OGG: Ogg Vorbis
- WMA: Windows Media Audio (experimentell)

**Metadaten-Support**:
- ID3v1/v2 (MP3)
- Vorbis Comments (FLAC, OGG)
- iTunes Tags (AAC, M4A)
- BWF (Broadcast Wave Format)

## 💡 Workflow-Tipps

### Effiziente Arbeitsabläufe

#### Batch-Processing Optimierung

1. **Große Bibliotheken**:
   ```
   Schritt 1: Ordner-Import (rekursiv)
   Schritt 2: Batch-Analyse (über Nacht)
   Schritt 3: Cache-Validierung
   Schritt 4: Manuelle Korrekturen
   ```

2. **Neue Tracks**:
   ```
   Schritt 1: Einzelne Dateien hinzufügen
   Schritt 2: Sofortige Analyse
   Schritt 3: In bestehende Playlists integrieren
   ```

#### Playlist-Erstellung Best Practices

1. **Vorbereitung**:
   - Zielgruppe definieren
   - Set-Länge festlegen
   - Energie-Verlauf planen
   - Key-Präferenzen bestimmen

2. **Erstellung**:
   - Mit Preset beginnen
   - Parameter anpassen
   - Vorschau testen
   - Feintuning durchführen

3. **Nachbearbeitung**:
   - Übergänge prüfen
   - Cue-Points setzen
   - Export vorbereiten
   - Backup erstellen

### Keyboard Shortcuts

#### Globale Shortcuts

| Shortcut | Funktion |
|----------|----------|
| Ctrl+N | Neues Projekt |
| Ctrl+O | Ordner hinzufügen |
| Ctrl+F | Dateien hinzufügen |
| Ctrl+S | Projekt speichern |
| Ctrl+P | Playlist erstellen |
| Ctrl+E | Export |
| F5 | Analyse starten |
| F12 | Einstellungen |
| Esc | Aktion abbrechen |

#### Player-Shortcuts

| Shortcut | Funktion |
|----------|----------|
| Leertaste | Play/Pause |
| Ctrl+← | Vorheriger Track |
| Ctrl+→ | Nächster Track |
| Ctrl+↑ | Lautstärke + |
| Ctrl+↓ | Lautstärke - |
| Home | Zum Anfang |
| End | Zum Ende |

#### Bearbeitung-Shortcuts

| Shortcut | Funktion |
|----------|----------|
| Ctrl+A | Alle auswählen |
| Ctrl+I | Auswahl umkehren |
| Del | Löschen |
| Ctrl+Z | Rückgängig |
| Ctrl+Y | Wiederholen |
| Ctrl+C | Kopieren |
| Ctrl+V | Einfügen |

### Performance-Optimierung

#### Hardware-Empfehlungen

**Minimum**:
- CPU: Dual-Core 2.5 GHz
- RAM: 4 GB
- Storage: 2 GB frei
- Audio: Integrierte Soundkarte

**Empfohlen**:
- CPU: Quad-Core 3.0 GHz+
- RAM: 8 GB+
- Storage: SSD mit 10 GB+ frei
- Audio: Professionelles Audio-Interface

**Optimal**:
- CPU: 8-Core 3.5 GHz+
- RAM: 16 GB+
- Storage: NVMe SSD
- Audio: High-End DJ-Controller

#### Software-Optimierung

```json
{
  "optimization": {
    "cpu_priority": "high",
    "memory_management": "aggressive",
    "disk_cache": "enabled",
    "background_analysis": true,
    "gpu_acceleration": false,
    "multiprocessing": {
      "enabled": true,
      "max_workers": "auto",
      "chunk_size": 10
    }
  }
}
```

---

**📚 Weitere Ressourcen**:
- [API Reference](api/README.md)
- [Developer Guide](developer-guide.md)
- [FAQ](faq.md)
- [Troubleshooting](troubleshooting.md)

**🆘 Support**: Bei Fragen oder Problemen erstellen Sie ein Issue im Repository oder konsultieren Sie die FAQ-Sektion.