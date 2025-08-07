# DJ Audio-Analyse-Tool Pro - Backend Setup

## 🚀 Quick Start

### Windows
```bash
# Einfacher Start
./run_backend.bat

# Development-Modus mit Auto-Reload
./run_backend_dev.bat
```

### Linux/macOS
```bash
# Einfacher Start
./run_backend.sh

# Development-Modus mit Auto-Reload
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## 📋 Voraussetzungen

- **Python 3.8+** (empfohlen: Python 3.11)
- **FFmpeg** (für erweiterte Audio-Verarbeitung)
- **8 GB RAM** (empfohlen für größere Libraries)

## 🔧 Installation

### 1. Virtual Environment erstellen
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS  
source venv/bin/activate
```

### 2. Dependencies installieren
```bash
# Production
pip install -r requirements.txt

# Development (mit zusätzlichen Tools)
pip install -r requirements-dev.txt
```

### 3. Verzeichnisse erstellen
```bash
mkdir -p data/cache data/exports data/presets logs
```

## 🌐 Server starten

### Produktions-Modus
```bash
cd backend
python main.py
```

### Development-Modus
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Mit Docker
```bash
# Build
docker build -t audio-analysis-backend .

# Run
docker run -p 8000:8000 -v ./data:/app/data audio-analysis-backend
```

## 📚 API-Dokumentation

Nach dem Start verfügbar unter:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Status**: http://localhost:8000/api/status

## 🛠 API-Endpunkte

Die API bietet folgende Endpunkte zur Interaktion mit dem Backend:

### Tracks (`/api/tracks`)
- `GET /api/tracks` - Ruft eine paginierte Liste aller analysierten Tracks ab. Unterstützt Filterung nach BPM, Tonart, Stimmung, Künstler, Genre und Volltextsuche.
- `GET /api/tracks/{track_id}` - Ruft detaillierte Informationen zu einem spezifischen Track ab. `track_id` ist der URL-kodierte Dateipfad.
- `GET /api/tracks/search/similar` - Findet ähnliche Tracks basierend auf Audio-Features (BPM, Energie, Camelot Wheel, Stimmung).
- `GET /api/tracks/stats/overview` - Bietet aggregierte Statistiken über alle analysierten Tracks (z.B. BPM-Verteilung, Stimmungs-Verteilung).

### Playlists (`/api/playlists`)
- `GET /api/playlists/presets` - Listet alle verfügbaren Playlist-Presets auf (Standard und benutzerdefiniert).
- `GET /api/playlists/presets/{preset_name}` - Ruft detaillierte Informationen zu einem spezifischen Preset ab.
- `POST /api/playlists/presets` - Erstellt ein neues benutzerdefiniertes Playlist-Preset.
- `DELETE /api/playlists/presets/{preset_name}` - Löscht ein benutzerdefiniertes Preset.
- `POST /api/playlists/generate` - Startet die Playlist-Generierung als asynchrone Hintergrundaufgabe. Nimmt Parameter wie Track-Pfade, Preset-Namen und benutzerdefinierte Regeln entgegen. Gibt eine Task-ID zurück, um den Fortschritt abzufragen und das Ergebnis abzurufen.
- `GET /api/playlists/generate/{task_id}/status` - Ruft den aktuellen Status einer laufenden oder abgeschlossenen Playlist-Generierungsaufgabe ab.
- `GET /api/playlists/generate/{task_id}/result` - Ruft das Ergebnis einer abgeschlossenen Playlist-Generierungsaufgabe ab.
- `POST /api/playlists/export` - Exportiert eine generierte Playlist in verschiedene Formate (M3U, JSON, CSV, Rekordbox XML).
- `GET /api/playlists/{playlist_id}/export` - Exportiert eine zuvor generierte Playlist nach ihrer Task-ID in das gewünschte Format (M3U, JSON, CSV, Rekordbox XML).
- `GET /api/playlists/exports` - Listet alle zuvor exportierten Playlists auf.
- `DELETE /api/playlists/exports/{filename}` - Löscht eine exportierte Playlist-Datei.
- `GET /api/playlists/algorithms` - Listet Informationen über alle verfügbaren Playlist-Algorithmen auf.
- `POST /api/playlists/validate` - Validiert Tracks für die Playlist-Generierung (prüft Verfügbarkeit im Cache und Datenqualität).
- `GET /api/playlists/stats/generation` - Bietet Statistiken über Playlist-Generierungsaufgaben.

### Analysis (`/api/analysis`)
- `POST /api/analysis/start` - Startet den Scan und die Analyse von Audio-Dateien als asynchrone Hintergrundaufgabe. Unterstützt Verzeichnisse, spezifische Dateien, rekursives Scannen und Cache-Überschreibung. Gibt eine Task-ID zurück, um den Fortschritt abzufragen.
- `GET /api/analysis/{task_id}/status` - Ruft den aktuellen Fortschritt und Status einer laufenden Audio-Analyse-Aufgabe ab.
- `POST /api/analysis/{task_id}/cancel` - Bricht eine laufende Audio-Analyse-Aufgabe ab.
- `GET /api/analysis/cache/stats` - Ruft detaillierte Statistiken über den Audio-Analyse-Cache ab.
- `POST /api/analysis/cache/cleanup` - Bereinigt den Analyse-Cache basierend auf Alter und Größe.
- `POST /api/analysis/cache/clear` - Löscht den gesamten Analyse-Cache.
- `POST /api/analysis/cache/optimize` - Optimiert den Cache durch Entfernung ungültiger Einträge.
- `GET /api/analysis/formats` - Listet alle unterstützten Audio-Formate für die Analyse auf.
- `GET /api/analysis/stats` - Bietet aggregierte Statistiken über Audio-Analysen und Cache-Nutzung.
- `GET /api/analysis/validate/directory` - Validiert ein Verzeichnis für die Audio-Analyse (prüft Existenz, Zugriffsrechte und Anzahl der Audio-Dateien).

## 📁 Verzeichnisstruktur

```
backend/
├── main.py                 # FastAPI Hauptanwendung
├── config/
│   └── settings.py        # Konfiguration
├── api/
│   ├── models.py          # Pydantic Modelle
│   └── endpoints/
│       ├── tracks.py      # Track-Management
│       ├── playlists.py   # Playlist-Generation
│       └── analysis.py    # Audio-Analyse
└── core_engine/           # Kern-Logic (migriert von src/)
    ├── audio_analysis/
    ├── playlist_engine/
    ├── mood_classifier/
    └── export/
```

## ⚙️ Konfiguration

Die Hauptkonfiguration des Backends wird in `backend/config/settings.py` definiert. Diese Datei enthält Standardwerte für alle Einstellungen, einschließlich Server-Parameter, Musikbibliothek-Pfade, Audio-Analyse-Optionen, Playlist-Engine-Verhalten, Cache-Management und Logging.

**Benutzerdefinierte Einstellungen:**
Für benutzerdefinierte Anpassungen, die über die Standardwerte hinausgehen, können Sie eine Datei namens `backend_config.json` im `data/`-Verzeichnis erstellen. Diese JSON-Datei wird beim Start des Backends automatisch geladen und ihre Einstellungen werden mit den Standardeinstellungen zusammengeführt (Deep Merge). Dies ermöglicht es Ihnen, spezifische Werte zu überschreiben, ohne die `settings.py`-Datei direkt ändern zu müssen.

**Beispiel für `data/backend_config.json`:**
```json
{
  "server": {
    "port": 8001,
    "cors_origins": ["http://localhost:3000", "http://192.168.1.100"]
  },
  "music_library": {
    "scan_path": "/path/to/your/music",
    "auto_scan_on_startup": true
  },
  "audio_analysis": {
    "enable_multiprocessing": false,
    "max_file_size_mb": 1024
  }
}
```

**Umgebungsvariablen:**
Einige wichtige Einstellungen können auch über Umgebungsvariablen überschrieben werden, was besonders nützlich für Docker-Container oder CI/CD-Pipelines ist. Beispiele hierfür sind `HOST`, `PORT`, `MUSIC_LIBRARY_PATH`, `CACHE_DIR`, `PRESETS_DIR`, `EXPORT_DIR`, `MAX_WORKERS` und `DEBUG`.

**Wichtige Konfigurationspfade:**
- `music_library.scan_path`: Standardpfad, der beim Scannen der Musikbibliothek verwendet wird.
- `audio_analysis.cache_dir`: Verzeichnis für Analyse-Cache-Dateien.
- `playlist_engine.presets_dir`: Verzeichnis für Playlist-Presets.
- `export.output_dir`: Verzeichnis für exportierte Playlists.


## 🐳 Docker Deployment

```bash
# Lokaler Build
docker build -t audio-analysis-backend .

# Mit Volume für persistente Daten
docker run -d \
  -p 8000:8000 \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  --name audio-backend \
  audio-analysis-backend
```

## 🧪 Testing

```bash
# Tests ausführen
pytest

# Mit Coverage
pytest --cov=backend

# Nur API-Tests
pytest tests/api/
```

## 📈 Performance & Monitoring

### Health Checks
- `/health` - Komponenten-Status
- `/api/status` - Detaillierte System-Info

### Logging
- Logs in `logs/backend.log`
- Konfigurierbare Log-Level
- Strukturierte Logs mit Timestamps

### Caching
- Intelligenter Audio-Analyse-Cache
- Automatische Cache-Bereinigung
- Cache-Optimierung verfügbar

## 🚨 Troubleshooting

### Häufige Probleme

**Port bereits belegt:**
```bash
# Ändere Port in data/backend_config.json oder setze Umgebungsvariable PORT
# Beispiel: PORT=8001
```

**Audio-Dependencies fehlen:**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libsndfile1

# macOS
brew install ffmpeg libsndfile

# Windows: FFmpeg von https://ffmpeg.org/download.html
```

**Virtual Environment Probleme:**
```bash
# Lösche und erstelle neu
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug-Modus

```bash
# Environment Variable setzen
export DEBUG=true
export ENVIRONMENT=development

# Oder in backend/main.py Debug aktivieren
uvicorn backend.main:app --reload --log-level debug
```

## 🔒 Sicherheit

### Produktions-Deployment
- CORS auf spezifische Origins begrenzen
- TrustedHostMiddleware aktiviert
- Keine Debug-Informationen in Responses
- HTTPS empfohlen

### API-Rate-Limiting
```bash
# Optional: nginx als Reverse Proxy
# Mit Rate-Limiting konfigurieren
```

## 📞 Support

Bei Problemen:
1. Logs in `logs/backend.log` prüfen
2. Health Check `/health` aufrufen
3. API Status `/api/status` prüfen
4. GitHub Issues für Bugs/Features

---

**Entwickelt für Project Phoenix 🔥**  
*Transforming monolithic desktop app to modern headless API*