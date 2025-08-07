# FastAPI Backend Reference - DJ Audio-Analyse-Tool Pro

Vollständige REST API-Dokumentation für das headless Backend (Project Phoenix).

## 📚 Übersicht

Das Backend ist als FastAPI-Service implementiert und bietet RESTful Zugriff auf alle Kernfunktionen:

- **Analysis API**: Audio-Verarbeitung und Feature-Extraktion via Background Tasks
- **Tracks API**: Track-Verwaltung und Metadaten-Abfrage
- **Playlists API**: Intelligente Playlist-Generierung mit verschiedenen Algorithmen
- **Export API**: Verschiedene Export-Formate (M3U, Rekordbox XML, JSON)
- **Cache Management**: Effiziente Datenverwaltung mit automatischer Bereinigung
- **Health Monitoring**: System-Status und Performance-Metriken

## 🏗️ Backend-Architektur

```
backend/
├── main.py                    # FastAPI App Entry Point
├── api/
│   ├── endpoints/
│   │   ├── analysis.py         # Audio-Analyse Endpunkte
│   │   ├── tracks.py           # Track-Management API  
│   │   └── playlists.py        # Playlist-Generierung API
│   └── models.py               # Pydantic Request/Response Models
├── core_engine/
│   ├── audio_analysis/
│   │   ├── analyzer.py         # Haupt-Audio-Analyzer
│   │   └── feature_extractor.py # Modulare Feature-Extraktion
│   ├── data_management/
│   │   └── cache_manager.py    # JSON-basierter Cache
│   ├── playlist_engine/
│   │   └── playlist_engine.py  # Intelligente Playlist-Algorithmen
│   ├── mood_classifier/
│   │   └── mood_classifier.py  # Heuristik-basierte Stimmungsanalyse
│   └── export/
│       └── playlist_exporter.py # Multi-Format Export
└── config/
    └── settings.py             # Konfiguration
```

## 🔌 REST API Endpunkte

### Base URL
```
http://localhost:8000/api
```

### Health & Status

#### GET /health

Prüft Server-Status und -Verfügbarkeit.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-07T10:30:00Z",
  "version": "2.0.0",
  "components": {
    "cache": "healthy",
    "analyzer": "healthy",
    "essentia": true
  }
}
```

### Audio Analysis API

#### POST /analysis/start

Startet die Audio-Analyse als Background Task.

**Request**:
```json
{
  "directories": ["/path/to/music"],
  "file_paths": null,
  "recursive": true,
  "overwrite_cache": false,
  "include_patterns": null,
  "exclude_patterns": null
}
```

**Response**:
```json
{
  "task_id": "analysis_20250107_103000_0",
  "status": "started",
  "message": "Audio analysis started",
  "total_files": 127,
  "invalid_files": 0,
  "directories_scanned": 1,
  "status_url": "/api/analysis/analysis_20250107_103000_0/status",
  "overwrite_cache": false
}
```

#### GET /analysis/{task_id}/status

Abfrage des aktuellen Analyse-Status.

**Response**:
```json
{
  "status": "running",
  "progress": 42.5,
  "current_file": "track_042.mp3",
  "processed_files": 54,
  "total_files": 127,
  "errors": [],
  "started_at": "2025-01-07T10:30:00Z",
  "estimated_completion": "2025-01-07T10:35:30Z"
}
```

#### POST /analysis/{task_id}/cancel

Bricht eine laufende Analyse ab.

#### GET /analysis/cache/stats

Cache-Statistiken abrufen.

### Tracks API

#### GET /tracks

Alle analysierten Tracks mit Filter-Optionen abrufen.

**Query Parameter**:
- `limit` (int): Maximale Anzahl Tracks (default: 50)
- `offset` (int): Skip-Anzahl für Pagination (default: 0)
- `bpm_min` (float): Minimale BPM
- `bpm_max` (float): Maximale BPM  
- `key` (str): Specific Key (z.B. "Am", "8A")
- `mood` (str): Gewünschte Stimmung
- `search` (str): Volltext-Suche in Titel/Artist

**Response**:
```json
{
  "tracks": [
    {
      "file_path": "/music/track.mp3",
      "filename": "track.mp3",
      "features": {
        "bpm": 128.0,
        "energy": 0.75,
        "valence": 0.68,
        "danceability": 0.82
      },
      "metadata": {
        "title": "Example Track",
        "artist": "Example Artist",
        "duration": 245.3
      },
      "camelot": {
        "key": "Am",
        "camelot": "8A",
        "compatible_keys": ["7A", "8A", "9A", "8B"]
      },
      "mood": {
        "primary_mood": "driving",
        "confidence": 0.85,
        "scores": {
          "driving": 0.85,
          "euphoric": 0.23,
          "chill": 0.12
        }
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### GET /tracks/{track_id}

Einzelnen Track mit allen Details abrufen.

#### GET /tracks/similar/{track_id}

Ähnliche Tracks basierend auf Audio-Features finden.

**Query Parameter**:
- `limit` (int): Anzahl ähnlicher Tracks (default: 10)
- `algorithm` (str): Similarity-Algorithmus (default: "cosine")

### Playlists API

#### POST /playlists/generate

Intelligente Playlist-Generierung.

**Request**:
```json
{
  "preset": "progressive_house",
  "target_duration": 3600,
  "start_track_id": null,
  "options": {
    "bpm_range": [120, 130],
    "energy_curve": "gradual_buildup",
    "harmony_strictness": 0.8,
    "avoid_repetition": true
  }
}
```

**Response**:
```json
{
  "playlist_id": "playlist_20250107_103500",
  "tracks": [
    {
      "track_id": "track_001",
      "position": 0,
      "transition_score": 0.92,
      "reason": "harmonic_compatibility"
    }
  ],
  "metadata": {
    "total_tracks": 18,
    "total_duration": 3847,
    "average_bpm": 125.3,
    "energy_progression": "gradual_buildup",
    "mood_consistency": 0.84
  }
}
```

#### GET /playlists

Alle gespeicherten Playlists abrufen.

#### GET /playlists/{playlist_id}

Einzelne Playlist mit allen Tracks abrufen.

#### DELETE /playlists/{playlist_id}

Playlist löschen.

### Export API

#### POST /playlists/{playlist_id}/export

Playlist in verschiedene Formate exportieren.

**Request**:
```json
{
  "format": "m3u",
  "options": {
    "relative_paths": true,
    "include_metadata": true,
    "path_prefix": "/Music"
  }
}
```

**Supported Formats**:
- `m3u`: Standard M3U Playlist
- `m3u8`: Extended M3U with metadata
- `rekordbox_xml`: Rekordbox-kompatibles XML
- `json`: JSON-Format für APIs
- `csv`: CSV für Spreadsheets

### Configuration API

#### GET /config/presets

Alle verfügbaren Playlist-Presets abrufen.

#### GET /config/settings

Aktuelle System-Einstellungen abrufen.

#### PUT /config/settings

System-Einstellungen aktualisieren.

## 📊 Response Models

### Standard-Response-Format

Alle API-Responses folgen einem einheitlichen Format:

#### Success Response
```json
{
  "status": "success",
  "data": { /* Response data */ },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-07T10:30:00Z"
}
```

#### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "bpm_range",
      "issue": "Minimum BPM cannot be greater than maximum BPM"
    }
  },
  "timestamp": "2025-01-07T10:30:00Z"
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully  
- `202 Accepted`: Request accepted (async processing)
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## 🔐 Authentication & Security

### API Key Authentication (Optional)

Wenn aktiviert, wird ein API-Key für alle Requests benötigt:

```bash
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/api/tracks
```

### CORS Configuration

FastAPI ist für Cross-Origin-Requests konfiguriert:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔧 Konfiguration

### Environment Variables

```bash
# Server Configuration
HOST=localhost
PORT=8000
DEBUG=true

# Audio Analysis
AUDIO_CACHE_DIR=./data/cache
MAX_FILE_SIZE_MB=500
ENABLE_MULTIPROCESSING=true
MAX_WORKERS=4

# Music Library
MUSIC_LIBRARY_PATH=/path/to/music
SCAN_RECURSIVE=true
MIN_FILE_SIZE_KB=100

# Performance
ENABLE_UVLOOP=true
WORKER_TIMEOUT=300
```

### Backend Settings

```json
{
  "audio_analysis": {
    "cache_dir": "./data/cache",
    "enable_multiprocessing": true,
    "max_workers": 4,
    "supported_formats": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"]
  },
  "music_library": {
    "scan_path": "/path/to/music",
    "max_depth": 10,
    "min_file_size_kb": 100,
    "exclude_patterns": ["*/.git/*", "*/temp/*"]
  },
  "playlist_engine": {
    "default_algorithm": "harmonic",
    "camelot_wheel_enabled": true,
    "energy_analysis_enabled": true
  }
}
```

## 📊 Performance & Monitoring

### Health Check Endpoint

```bash
# Basic health check
GET /health

# Detailed system info
GET /health/detailed
```

### Metrics & Statistics

```bash
# Analysis statistics
GET /api/analysis/stats

# Cache statistics  
GET /api/analysis/cache/stats

# System performance
GET /api/system/stats
```

### Background Task Monitoring

```bash
# Active background tasks
GET /api/tasks/active

# Task history
GET /api/tasks/history
```

## 🧠 Testing & Development

### API Testing mit curl

```bash
# Server starten
uvicorn backend.main:app --reload --port 8000

# Health check
curl http://localhost:8000/health

# Analyse starten
curl -X POST "http://localhost:8000/api/analysis/start" \
     -H "Content-Type: application/json" \
     -d '{"directories": ["/path/to/music"]}'

# Status prüfen
curl "http://localhost:8000/api/analysis/task_id/status"

# Tracks abrufen
curl "http://localhost:8000/api/tracks?limit=10&bpm_min=120"
```

### Automated Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# API integration tests
pytest tests/test_api_endpoints.py -v
```

### Interactive API Documentation

```bash
# Swagger UI
http://localhost:8000/docs

# ReDoc  
http://localhost:8000/redoc

# OpenAPI JSON
http://localhost:8000/openapi.json
```

### Development Server

```bash
# Development with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY data/ ./data/

# Non-root user for security
RUN useradd -m -u 1001 djapi
USER djapi

EXPOSE 8000

# Use uvicorn for production
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  dj-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - /path/to/music:/music:ro
    environment:
      - MUSIC_LIBRARY_PATH=/music
      - DEBUG=false
      - MAX_WORKERS=4
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - dj-api
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dj-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dj-api
  template:
    metadata:
      labels:
        app: dj-api
    spec:
      containers:
      - name: dj-api
        image: dj-audio-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: MAX_WORKERS
          value: "2"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## 🔗 Weitere Ressourcen

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Swagger UI](http://localhost:8000/docs) (wenn Server läuft)
- [ReDoc API Docs](http://localhost:8000/redoc)
- [GitHub Repository](https://github.com/your-repo/audio-analysis-tool)

## 📞 Support & Community

Für Backend-API-spezifische Fragen:

1. **Interactive Docs**: Swagger UI unter `/docs`
2. **API Testing**: ReDoc unter `/redoc`
3. **GitHub Issues**: Bug-Reports und Feature-Requests
4. **Tests**: API-Integration-Tests in `tests/`
5. **Examples**: API-Usage-Examples in `examples/api/`

## 🚀 Next Steps

1. **Development**: Lokalen Server starten mit `uvicorn backend.main:app --reload`
2. **Testing**: API mit Swagger UI testen unter `http://localhost:8000/docs`
3. **Integration**: Client-SDKs in verschiedenen Sprachen entwickeln
4. **Deployment**: Docker-Container für Production-Environment

---

**Version**: 2.0 (Phoenix Backend)  
**Architecture**: FastAPI REST API  
**Letzte Aktualisierung**: Januar 2025  
**Kompatibilität**: Python 3.9+