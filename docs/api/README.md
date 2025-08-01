# API Reference - DJ Audio-Analyse-Tool Pro

Vollständige API-Dokumentation für Entwickler und erweiterte Benutzer.

## 📚 Übersicht

Die API des DJ Audio-Analyse-Tools ist modular aufgebaut und bietet Zugriff auf alle Kernfunktionen:

- **Audio Analysis Engine**: Audio-Verarbeitung und Feature-Extraktion
- **Playlist Engine**: Intelligente Playlist-Generierung
- **Export Engine**: Verschiedene Export-Formate
- **Cache Manager**: Effiziente Datenverwaltung
- **GUI Components**: Benutzeroberflächen-Komponenten

## 🏗️ Architektur-Übersicht

```
src/
├── audio_analysis/          # Audio-Analyse-Module
│   ├── analyzer.py          # Haupt-Analyzer
│   ├── feature_extractor.py # Feature-Extraktion
│   ├── essentia_integration.py # Essentia-Integration
│   └── cache_manager.py     # Cache-Verwaltung
├── playlist_engine/         # Playlist-Generierung
│   ├── generator.py         # Playlist-Generator
│   ├── camelot_wheel.py     # Harmonische Analyse
│   ├── similarity_engine.py # Ähnlichkeits-Berechnung
│   └── optimizer.py         # Playlist-Optimierung
├── export/                  # Export-Funktionen
│   ├── playlist_exporter.py # Playlist-Export
│   ├── rekordbox_exporter.py # Rekordbox-Integration
│   └── csv_exporter.py      # CSV-Export
└── gui/                     # GUI-Komponenten
    ├── main_window.py       # Hauptfenster
    ├── track_browser.py     # Track-Browser
    └── playlist_dashboard.py # Playlist-Dashboard
```

## 📖 Module-Dokumentation

### Audio Analysis Engine

#### AudioAnalyzer

**Klasse**: `src.audio_analysis.analyzer.AudioAnalyzer`

**Beschreibung**: Haupt-Klasse für Audio-Analyse mit Unterstützung für verschiedene Algorithmen.

**Initialisierung**:
```python
from src.audio_analysis.analyzer import AudioAnalyzer

analyzer = AudioAnalyzer(
    use_essentia=True,
    use_librosa=True,
    cache_enabled=True,
    quality='high'
)
```

**Parameter**:
- `use_essentia` (bool): Essentia für erweiterte Analyse verwenden
- `use_librosa` (bool): librosa für Basis-Analyse verwenden
- `cache_enabled` (bool): Cache-System aktivieren
- `quality` (str): Analyse-Qualität ('low', 'medium', 'high', 'ultra')

**Methoden**:

##### `analyze_file(file_path: str) -> Dict[str, Any]`

Analysiert eine einzelne Audio-Datei.

**Parameter**:
- `file_path` (str): Pfad zur Audio-Datei

**Rückgabe**:
```python
{
    'bpm': 128.0,
    'key': 'Am',
    'camelot': '8A',
    'energy': 75.5,
    'mood': 'energetic',
    'duration': 245.3,
    'confidence': {
        'bpm': 0.95,
        'key': 0.87,
        'energy': 0.92,
        'mood': 0.78
    },
    'features': {
        'mfcc': [...],
        'chroma': [...],
        'spectral_centroid': 1500.2,
        'rms_energy': 0.15
    }
}
```

**Beispiel**:
```python
result = analyzer.analyze_file('path/to/track.mp3')
print(f"BPM: {result['bpm']}, Key: {result['key']}")
```

##### `batch_analyze(file_paths: List[str], callback=None) -> List[Dict[str, Any]]`

Analysiert mehrere Audio-Dateien parallel.

**Parameter**:
- `file_paths` (List[str]): Liste von Dateipfaden
- `callback` (callable, optional): Fortschritts-Callback

**Callback-Signatur**:
```python
def progress_callback(current: int, total: int, file_path: str):
    print(f"Fortschritt: {current}/{total} - {file_path}")
```

**Beispiel**:
```python
files = ['track1.mp3', 'track2.mp3', 'track3.mp3']
results = analyzer.batch_analyze(files, callback=progress_callback)
```

#### FeatureExtractor

**Klasse**: `src.audio_analysis.feature_extractor.FeatureExtractor`

**Beschreibung**: Spezialisierte Klasse für Audio-Feature-Extraktion.

**Methoden**:

##### `extract_bpm(audio_data: np.ndarray, sr: int) -> Tuple[float, float]`

Extrahiert BPM aus Audio-Daten.

**Parameter**:
- `audio_data` (np.ndarray): Audio-Signal
- `sr` (int): Sample-Rate

**Rückgabe**:
- Tuple[float, float]: (BPM, Konfidenz)

**Beispiel**:
```python
import librosa
from src.audio_analysis.feature_extractor import FeatureExtractor

audio, sr = librosa.load('track.mp3')
extractor = FeatureExtractor()
bpm, confidence = extractor.extract_bpm(audio, sr)
```

##### `extract_key(audio_data: np.ndarray, sr: int) -> Tuple[str, str, float]`

Extrahiert Tonart aus Audio-Daten.

**Rückgabe**:
- Tuple[str, str, float]: (Key, Camelot, Konfidenz)

##### `extract_energy(audio_data: np.ndarray, sr: int) -> float`

Berechnet Energie-Level des Tracks.

**Rückgabe**:
- float: Energie-Level (0-100)

#### EssentiaIntegration

**Klasse**: `src.audio_analysis.essentia_integration.EssentiaIntegration`

**Beschreibung**: Integration von Essentia für erweiterte Audio-Analyse.

**Methoden**:

##### `analyze_with_essentia(file_path: str) -> Dict[str, Any]`

Vollständige Essentia-Analyse.

**Beispiel**:
```python
from src.audio_analysis.essentia_integration import EssentiaIntegration

essentia = EssentiaIntegration()
result = essentia.analyze_with_essentia('track.mp3')
```

### Playlist Engine

#### PlaylistGenerator

**Klasse**: `src.playlist_engine.generator.PlaylistGenerator`

**Beschreibung**: Intelligente Playlist-Generierung mit verschiedenen Algorithmen.

**Initialisierung**:
```python
from src.playlist_engine.generator import PlaylistGenerator

generator = PlaylistGenerator(
    algorithm='beam_search',
    beam_width=5,
    lookahead=3
)
```

**Methoden**:

##### `generate_playlist(tracks: List[Dict], preset: Dict, target_duration: int = None) -> List[Dict]`

Generiert eine optimierte Playlist.

**Parameter**:
- `tracks` (List[Dict]): Verfügbare Tracks
- `preset` (Dict): Playlist-Preset-Konfiguration
- `target_duration` (int, optional): Ziel-Dauer in Sekunden

**Preset-Format**:
```python
preset = {
    'name': 'Progressive House',
    'bpm_range': [120, 130],
    'energy_curve': 'gradual_buildup',
    'harmony_strictness': 0.8,
    'mood_consistency': 0.7,
    'rules': {
        'max_bpm_jump': 3,
        'key_compatibility': 'camelot_wheel',
        'avoid_back_to_back_same_artist': True
    }
}
```

**Beispiel**:
```python
tracks = [...]  # Liste von analysierten Tracks
playlist = generator.generate_playlist(tracks, preset, target_duration=3600)
```

#### CamelotWheel

**Klasse**: `src.playlist_engine.camelot_wheel.CamelotWheel`

**Beschreibung**: Harmonische Kompatibilitäts-Analyse basierend auf dem Camelot Wheel.

**Methoden**:

##### `get_compatible_keys(key: str) -> List[str]`

Gibt kompatible Keys für harmonische Übergänge zurück.

**Parameter**:
- `key` (str): Ausgangs-Key (z.B. '8A', 'Am', 'C')

**Rückgabe**:
- List[str]: Liste kompatibler Keys

**Beispiel**:
```python
from src.playlist_engine.camelot_wheel import CamelotWheel

wheel = CamelotWheel()
compatible = wheel.get_compatible_keys('8A')
print(compatible)  # ['7A', '8A', '9A', '8B']
```

##### `calculate_compatibility(key1: str, key2: str) -> float`

Berechnet Kompatibilitäts-Score zwischen zwei Keys.

**Rückgabe**:
- float: Kompatibilitäts-Score (0.0-1.0)

#### SimilarityEngine

**Klasse**: `src.playlist_engine.similarity_engine.SimilarityEngine`

**Beschreibung**: k-NN basierte Ähnlichkeits-Berechnung für Tracks.

**Methoden**:

##### `find_similar_tracks(target_track: Dict, tracks: List[Dict], k: int = 5) -> List[Tuple[Dict, float]]`

Findet ähnliche Tracks basierend auf Audio-Features.

**Parameter**:
- `target_track` (Dict): Ziel-Track
- `tracks` (List[Dict]): Verfügbare Tracks
- `k` (int): Anzahl ähnlicher Tracks

**Rückgabe**:
- List[Tuple[Dict, float]]: Liste von (Track, Ähnlichkeits-Score)

**Beispiel**:
```python
from src.playlist_engine.similarity_engine import SimilarityEngine

engine = SimilarityEngine()
similar = engine.find_similar_tracks(target_track, all_tracks, k=10)
```

### Export Engine

#### PlaylistExporter

**Klasse**: `src.export.playlist_exporter.PlaylistExporter`

**Beschreibung**: Export von Playlists in verschiedene Formate.

**Methoden**:

##### `export_m3u(playlist: List[Dict], file_path: str, relative_paths: bool = True) -> bool`

Exportiert Playlist als M3U-Datei.

**Parameter**:
- `playlist` (List[Dict]): Playlist-Daten
- `file_path` (str): Ziel-Dateipfad
- `relative_paths` (bool): Relative Pfade verwenden

**Beispiel**:
```python
from src.export.playlist_exporter import PlaylistExporter

exporter = PlaylistExporter()
success = exporter.export_m3u(playlist, 'my_playlist.m3u')
```

##### `export_rekordbox_xml(playlist: List[Dict], file_path: str, options: Dict = None) -> bool`

Exportiert Playlist als Rekordbox-kompatible XML-Datei.

**Options-Format**:
```python
options = {
    'include_analysis': True,
    'include_cues': True,
    'include_beatgrid': True,
    'path_format': 'relative'
}
```

#### RekordboxExporter

**Klasse**: `src.export.rekordbox_exporter.RekordboxExporter`

**Beschreibung**: Spezialisierter Rekordbox-Export mit erweiterten Features.

**Methoden**:

##### `merge_with_collection(playlist: List[Dict], collection_path: str, backup: bool = True) -> bool`

Integriert Playlist in bestehende Rekordbox-Collection.

**Parameter**:
- `playlist` (List[Dict]): Playlist-Daten
- `collection_path` (str): Pfad zur collection.xml
- `backup` (bool): Backup vor Änderungen erstellen

### Cache Manager

#### CacheManager

**Klasse**: `src.audio_analysis.cache_manager.CacheManager`

**Beschreibung**: Effiziente Verwaltung von Analyse-Ergebnissen.

**Methoden**:

##### `get_cached_analysis(file_path: str) -> Dict[str, Any] | None`

Lädt gecachte Analyse-Ergebnisse.

##### `cache_analysis(file_path: str, analysis_result: Dict[str, Any]) -> bool`

Speichert Analyse-Ergebnisse im Cache.

##### `clear_cache(older_than_days: int = None) -> int`

Bereinigt Cache-Einträge.

**Beispiel**:
```python
from src.audio_analysis.cache_manager import CacheManager

cache = CacheManager()

# Cache prüfen
cached = cache.get_cached_analysis('track.mp3')
if cached is None:
    # Analyse durchführen
    result = analyzer.analyze_file('track.mp3')
    cache.cache_analysis('track.mp3', result)
else:
    result = cached
```

## 🔧 Konfiguration

### Konfigurationsdateien

#### settings.json

**Pfad**: `config/settings.json`

**Struktur**:
```json
{
  "audio_analysis": {
    "quality": "high",
    "use_essentia": true,
    "use_librosa": true,
    "bpm_range": [60, 200],
    "key_confidence_threshold": 0.7
  },
  "playlist_engine": {
    "default_algorithm": "beam_search",
    "beam_width": 5,
    "lookahead": 3,
    "similarity_threshold": 0.8
  },
  "cache": {
    "enabled": true,
    "max_size_gb": 2,
    "cleanup_days": 30,
    "compression": true
  },
  "export": {
    "default_format": "m3u",
    "relative_paths": true,
    "include_metadata": true
  }
}
```

### Umgebungsvariablen

```bash
# Cache-Verzeichnis
DJ_TOOL_CACHE_DIR=/path/to/cache

# Log-Level
DJ_TOOL_LOG_LEVEL=INFO

# Rekordbox-Pfad
DJ_TOOL_REKORDBOX_PATH=/path/to/rekordbox

# Performance-Einstellungen
DJ_TOOL_MAX_WORKERS=4
DJ_TOOL_MEMORY_LIMIT=4096
```

## 🧪 Testing API

### Unit Tests

**Test-Framework**: pytest

**Beispiel-Test**:
```python
import pytest
from src.audio_analysis.analyzer import AudioAnalyzer

def test_audio_analyzer_initialization():
    analyzer = AudioAnalyzer(use_essentia=True)
    assert analyzer.use_essentia is True
    assert analyzer.cache_enabled is True

def test_bpm_detection():
    analyzer = AudioAnalyzer()
    # Mock-Audio-Daten verwenden
    result = analyzer.analyze_file('tests/fixtures/test_track.mp3')
    assert 'bpm' in result
    assert isinstance(result['bpm'], float)
    assert 60 <= result['bpm'] <= 200
```

### Integration Tests

**Beispiel**:
```python
def test_full_workflow():
    # Audio-Analyse
    analyzer = AudioAnalyzer()
    tracks = analyzer.batch_analyze(['track1.mp3', 'track2.mp3'])
    
    # Playlist-Generierung
    generator = PlaylistGenerator()
    preset = load_preset('progressive_house')
    playlist = generator.generate_playlist(tracks, preset)
    
    # Export
    exporter = PlaylistExporter()
    success = exporter.export_m3u(playlist, 'test_playlist.m3u')
    
    assert success is True
    assert len(playlist) > 0
```

### Mock-Objekte

**Audio-Mock**:
```python
import numpy as np
from unittest.mock import Mock

def create_mock_audio(duration=30, sr=22050, bpm=128):
    """Erstellt Mock-Audio-Daten für Tests."""
    samples = int(duration * sr)
    # Einfaches Sinussignal mit Beat-Pattern
    t = np.linspace(0, duration, samples)
    beat_freq = bpm / 60
    audio = np.sin(2 * np.pi * 440 * t) * np.sin(2 * np.pi * beat_freq * t)
    return audio, sr
```

## 🔌 Plugin-System

### Custom Analyzer Plugin

**Interface**:
```python
from abc import ABC, abstractmethod

class AnalyzerPlugin(ABC):
    @abstractmethod
    def analyze(self, audio_data: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analysiert Audio-Daten und gibt Ergebnisse zurück."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Gibt den Plugin-Namen zurück."""
        pass
```

**Beispiel-Plugin**:
```python
class CustomBPMAnalyzer(AnalyzerPlugin):
    def analyze(self, audio_data, sr):
        # Custom BPM-Algorithmus
        bpm = self._detect_bpm(audio_data, sr)
        return {'custom_bpm': bpm}
    
    def get_name(self):
        return "Custom BPM Analyzer"
    
    def _detect_bpm(self, audio_data, sr):
        # Implementierung des BPM-Algorithmus
        pass
```

### Plugin-Registration

```python
from src.audio_analysis.analyzer import AudioAnalyzer

analyzer = AudioAnalyzer()
analyzer.register_plugin(CustomBPMAnalyzer())
```

## 📊 Performance-Monitoring

### Profiling

```python
import cProfile
import pstats
from src.audio_analysis.analyzer import AudioAnalyzer

def profile_analysis():
    analyzer = AudioAnalyzer()
    analyzer.analyze_file('large_track.mp3')

# Profiling ausführen
cProfile.run('profile_analysis()', 'analysis_profile.prof')

# Ergebnisse anzeigen
stats = pstats.Stats('analysis_profile.prof')
stats.sort_stats('cumulative').print_stats(10)
```

### Memory-Monitoring

```python
import tracemalloc
from src.audio_analysis.analyzer import AudioAnalyzer

tracemalloc.start()

analyzer = AudioAnalyzer()
result = analyzer.analyze_file('track.mp3')

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

## 🚀 Deployment

### Standalone-Anwendung

**PyInstaller-Konfiguration**:
```python
# build.spec
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('presets', 'presets'),
        ('templates', 'templates')
    ],
    hiddenimports=[
        'essentia',
        'librosa',
        'PySide6'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)
```

**Build-Befehl**:
```bash
pyinstaller build.spec --onefile --windowed
```

### Docker-Deployment

**Dockerfile**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren
COPY . .

# Benutzer erstellen
RUN useradd -m djuser
USER djuser

EXPOSE 8000

CMD ["python", "main.py"]
```

## 🔗 API-Referenz Links

- [Audio Analysis API](audio-analysis.md)
- [Playlist Engine API](playlist-engine.md)
- [Export Engine API](export-engine.md)
- [GUI Components API](gui-components.md)
- [Cache Manager API](cache-manager.md)
- [Utilities API](utilities.md)

## 📞 Support

Für API-spezifische Fragen:

1. **Dokumentation**: Konsultieren Sie die detaillierten Module-Dokumentationen
2. **Beispiele**: Schauen Sie in das `examples/` Verzeichnis
3. **Tests**: Referenz-Implementierungen in `tests/`
4. **Issues**: GitHub Issues für Bug-Reports und Feature-Requests

---

**Version**: 2.0  
**Letzte Aktualisierung**: Januar 2025  
**Kompatibilität**: Python 3.8+