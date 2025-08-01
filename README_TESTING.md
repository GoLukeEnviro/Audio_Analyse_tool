# DJ Audio Analysis Tool - Testing Environment

## Übersicht

Dieses Dokument beschreibt die umfassende Testumgebung für das DJ Audio Analysis Tool, einschließlich der Essentia-Integration mit Fallback-Mechanismen.

## 🧪 Testumgebung Setup

### Installierte Test-Dependencies

```bash
pip install pytest pytest-mock pytest-cov
```

### Projektstruktur

```
Audio_Analyse_tool/
├── src/
│   ├── audio_analysis/
│   │   ├── essentia_integration.py    # Essentia-Integration mit Fallback
│   │   ├── feature_extractor.py       # Erweiterte Feature-Extraktion
│   │   ├── cache_manager.py           # Cache-Management
│   │   └── analyzer.py               # Haupt-Analyzer
│   ├── playlist_engine/
│   ├── gui/
│   └── export_engine/
├── tests/
│   ├── conftest.py                   # Pytest-Fixtures
│   ├── test_audio_analysis.py        # Audio-Analyse Tests
│   ├── test_playlist_engine.py       # Playlist-Engine Tests
│   ├── test_gui_components.py        # GUI-Tests
│   ├── test_export_engine.py         # Export-Tests
│   ├── test_integration.py           # Integrationstests
│   └── test_essentia_integration.py  # Essentia-spezifische Tests
├── pytest.ini                       # Pytest-Konfiguration
└── test_runner.py                   # Einfacher Test-Runner
```

## 🎵 Essentia-Integration

### Funktionalität

Die Essentia-Integration bietet erweiterte Audio-Analyse-Funktionen mit automatischem Fallback zu librosa:

#### Verfügbare Features:
- **BPM-Extraktion**: Präzise Tempo-Erkennung
- **Tonart-Erkennung**: Musikalische Tonart und Modus
- **Umfassende Feature-Extraktion**: Spektrale, rhythmische und harmonische Features
- **Streaming-Modus**: Für große Audio-Dateien (falls verfügbar)
- **Performance-Benchmarking**: Vergleich verschiedener Algorithmen

#### Fallback-Mechanismus:
```python
from audio_analysis.essentia_integration import EssentiaIntegration

# Automatische Initialisierung mit Fallback
ei = EssentiaIntegration()

if ei.is_available:
    print("Essentia verfügbar - verwende erweiterte Algorithmen")
else:
    print("Essentia nicht verfügbar - verwende librosa Fallback")

# BPM-Extraktion (automatischer Fallback)
bpm = ei.extract_bpm(audio_data, sample_rate)

# Tonart-Extraktion (automatischer Fallback)
key, scale, strength = ei.extract_key(audio_data, sample_rate)
```

### Konfiguration

```python
# Algorithmus-Konfiguration
ei.configure_algorithms({
    'beat_tracker': {
        'maxTempo': 200,
        'minTempo': 60
    },
    'key_extractor': {
        'profileType': 'temperley'
    }
})
```

## 🔧 Test-Kategorien

### 1. Unit Tests

#### Audio Analysis Tests (`test_audio_analysis.py`)
- AudioAnalyzer-Initialisierung
- Feature-Extraktion (BPM, Key, Spektral, MFCC)
- Cache-Integration
- Fehlerbehandlung

#### Playlist Engine Tests (`test_playlist_engine.py`)
- Playlist-Generierung
- Kompatibilitäts-Algorithmen
- Regel-basierte Filterung
- Ähnlichkeits-Berechnung

#### GUI Tests (`test_gui_components.py`)
- Widget-Initialisierung
- Event-Handling
- Drag & Drop Funktionalität
- Audio-Preview

#### Export Tests (`test_export_engine.py`)
- Format-spezifische Exporter
- Metadaten-Behandlung
- Fehlerbehandlung
- Unicode-Support

### 2. Integration Tests (`test_integration.py`)
- End-to-End Workflows
- Batch-Verarbeitung
- Performance-Tests
- Datenintegrität

### 3. Essentia-spezifische Tests (`test_essentia_integration.py`)
- Verfügbarkeitsprüfung
- Fallback-Verhalten
- Algorithm-Konfiguration
- Performance-Vergleiche

## 🚀 Test-Ausführung

### Alle Tests ausführen
```bash
pytest tests/ -v
```

### Spezifische Test-Kategorien
```bash
# Nur Audio-Analyse Tests
pytest tests/test_audio_analysis.py -v

# Nur Essentia-Tests
pytest tests/test_essentia_integration.py -v

# Mit Coverage-Report
pytest tests/ --cov=src --cov-report=html
```

### Einfacher Test-Runner
```bash
python test_runner.py
```

### Test-Marker verwenden
```bash
# Nur schnelle Tests
pytest -m "not slow" -v

# Nur Unit Tests
pytest -m "unit" -v

# Nur Integration Tests
pytest -m "integration" -v
```

## 📊 Test-Fixtures

Die `conftest.py` stellt umfassende Fixtures bereit:

### Audio-Daten
- `mock_audio_data`: Synthetische Audio-Daten
- `sample_track_metadata`: Beispiel-Metadaten
- `temp_audio_file`: Temporäre Audio-Dateien

### System-Komponenten
- `cache_manager`: Konfigurierter Cache-Manager
- `feature_extractor`: Feature-Extractor mit Essentia
- `playlist_generator`: Playlist-Generator

### Test-Konfiguration
- `test_config`: Test-spezifische Einstellungen
- `mock_essentia_algorithms`: Mock Essentia-Algorithmen

## 🔍 Best Practices

### 1. Mock-Objekte verwenden
```python
@pytest.fixture
def mock_audio_file(mocker):
    mock_file = mocker.Mock()
    mock_file.load.return_value = (np.random.randn(44100), 44100)
    return mock_file
```

### 2. Parametrisierte Tests
```python
@pytest.mark.parametrize("audio_format", [".mp3", ".wav", ".flac", ".aiff"])
def test_audio_format_support(audio_format):
    # Test verschiedene Audio-Formate
    pass
```

### 3. Fehlerbehandlung testen
```python
def test_invalid_audio_file():
    with pytest.raises(FileNotFoundError):
        analyzer.analyze_track("nonexistent.mp3")
```

### 4. Performance-Tests
```python
@pytest.mark.slow
def test_large_batch_processing():
    # Test mit großen Datenmengen
    pass
```

## 📈 Coverage-Ziele

- **Audio Analysis**: > 90%
- **Playlist Engine**: > 85%
- **Export Engine**: > 90%
- **GUI Components**: > 70%
- **Integration**: > 80%

## 🐛 Debugging

### Logging aktivieren
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Pytest-Debugging
```bash
# Stoppe bei erstem Fehler
pytest -x

# Zeige lokale Variablen bei Fehlern
pytest --tb=long

# Interaktiver Debugger
pytest --pdb
```

## 🔄 Continuous Integration

Die Tests sind CI/CD-ready und können in GitHub Actions, Jenkins oder anderen CI-Systemen verwendet werden:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: pytest tests/ --cov=src
```

## 📝 Ergebnisse

### Aktuelle Test-Ergebnisse
```
📊 TEST SUMMARY
✅ Import Tests: PASSED
✅ Essentia Integration: PASSED  
✅ Feature Extractor: PASSED
✅ Cache Manager: PASSED

Overall: 4/4 tests passed
🎉 All tests passed! The system is ready for use.
```

### Essentia-Status
- **Verfügbarkeit**: Nicht installiert (Windows-Kompatibilitätsprobleme)
- **Fallback**: Librosa wird erfolgreich verwendet
- **Funktionalität**: Alle Features funktionieren mit Fallback
- **Performance**: Librosa-Fallback zeigt gute Performance

## 🚀 Nächste Schritte

1. **Essentia-Installation**: Für Linux/macOS Systeme Essentia installieren
2. **Performance-Optimierung**: Weitere Optimierungen für große Dateien
3. **Erweiterte Tests**: Mehr Edge-Cases und Stress-Tests
4. **GUI-Tests**: Erweiterte UI-Tests mit Qt Test Framework
5. **Dokumentation**: API-Dokumentation mit Sphinx

## 📚 Ressourcen

- [Pytest Documentation](https://docs.pytest.org/)
- [Essentia Documentation](https://essentia.upf.edu/)
- [Librosa Documentation](https://librosa.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)