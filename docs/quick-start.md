# Backend API Quick Start Guide

Ein schneller Einstieg in das DJ Audio-Analyse-Tool Pro Backend API v2.0 (Project Phoenix) - von der Installation bis zur ersten API-basierten Playlist in 10 Minuten.

## 🚀 In 5 Schritten zur ersten API-Playlist

### Schritt 1: Backend Installation (3 Minuten)

```bash
# Repository klonen
git clone <repository-url>
cd Audio_Analyse_tool

# Python-Dependencies installieren
pip install -r requirements.txt

# Backend starten
uvicorn backend.main:app --reload --port 8000
```

**✅ Erfolgreich wenn**: Server läuft und `http://localhost:8000/health` antwortet mit "healthy".

### Schritt 2: API-Konfiguration (1 Minute)

1. **API-Dokumentation öffnen**:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Check: [http://localhost:8000/health](http://localhost:8000/health)

2. **Basis-Einstellungen prüfen**:
   ```bash
   # Settings abrufen
   curl http://localhost:8000/api/config/settings
   
   # Musikbibliothek-Pfad setzen (falls nötig)
   # Wird automatisch aus MUSIC_LIBRARY_PATH Environment Variable gelesen
   ```

### Schritt 3: Musik-Verzeichnis validieren (1 Minute)

**API-Endpunkt zum Verzeichnis prüfen**:
```bash
# Verzeichnis validieren
curl "http://localhost:8000/api/analysis/validate/directory?directory=/path/to/music&recursive=true"
```

**Response zeigt**:
- Anzahl gefundener Audio-Dateien
- Geschätzte Analysezeit
- Bereits gecachte Tracks
- Empfehlungen für optimale Performance

**Unterstützte Formate**: MP3, WAV, FLAC, AAC, OGG, M4A, AIFF, AU, WMA, OPUS

### Schritt 4: Audio-Analyse via API starten (3-5 Minuten)

1. **Background-Analyse starten**:
   ```bash
   curl -X POST "http://localhost:8000/api/analysis/start" \
        -H "Content-Type: application/json" \
        -d '{"directories": ["/path/to/music"], "recursive": true}'
   ```

2. **Task-Status verfolgen**:
   ```bash
   # Status abfragen (task_id aus vorheriger Response)
   curl "http://localhost:8000/api/analysis/{task_id}/status"
   ```

3. **Analyse-Ergebnisse**:
   - BPM wird automatisch erkannt (librosa + optional Essentia)
   - Tonart (Key) wird bestimmt mit Camelot Wheel
   - Energie-Level wird berechnet (RMS + Spectral Features)
   - Stimmung wird klassifiziert (8 Kategorien)
   - JSON-Cache für schnelle Wiederverwendung

**💡 Tipp**: Analyse läuft asynchron - Sie können parallel andere API-Endpunkte nutzen.

### Schritt 5: Erste API-Playlist erstellen (1 Minute)

1. **Analysierte Tracks abrufen**:
   ```bash
   # Alle Tracks mit Filter anzeigen
   curl "http://localhost:8000/api/tracks?limit=20&bpm_min=120&bpm_max=130"
   ```

2. **Intelligente Playlist generieren**:
   ```bash
   curl -X POST "http://localhost:8000/api/playlists/generate" \
        -H "Content-Type: application/json" \
        -d '{
          "preset": "progressive_house",
          "target_duration": 3600,
          "options": {
            "bpm_range": [120, 130],
            "energy_curve": "gradual_buildup",
            "harmony_strictness": 0.8
          }
        }'
   ```

3. **Playlist exportieren**:
   ```bash
   # Export in M3U-Format
   curl -X POST "http://localhost:8000/api/playlists/{playlist_id}/export" \
        -H "Content-Type: application/json" \
        -d '{"format": "m3u", "options": {"relative_paths": true}}'
   ```

4. **Weitere Export-Optionen**:
   - `m3u`: Standard-Format für alle DJ-Software
   - `rekordbox_xml`: Rekordbox-Integration mit Cue-Points
   - `json`: Für eigene Anwendungen
   - `csv`: Für Spreadsheet-Analyse

## 🎯 API Quick Start Checkliste

- [ ] ✅ Backend-Server erfolgreich gestartet (`uvicorn backend.main:app --reload`)
- [ ] 📡 API Health-Check antwortet (`GET /health`)
- [ ] 📁 Musikverzeichnis validiert (`GET /api/analysis/validate/directory`)
- [ ] 🎵 Audio-Analyse gestartet und abgeschlossen (`POST /api/analysis/start`)
- [ ] 📅 Track-Daten über API abrufbar (`GET /api/tracks`)
- [ ] 🎼 Erste Playlist generiert (`POST /api/playlists/generate`)
- [ ] 💾 Playlist erfolgreich exportiert (`POST /api/playlists/{id}/export`)

## 🎨 API Interface im Überblick

### Wichtige API-Endpunkte

```
Backend API (http://localhost:8000)
│
├── /health                     # Server-Status
├── /docs                       # Swagger UI
├── /redoc                      # ReDoc Documentation
│
├── /api/analysis/
│   ├── POST /start            # Analyse starten
│   ├── GET /{task_id}/status  # Status prüfen
│   ├── GET /cache/stats       # Cache-Statistiken
│   └── GET /formats           # Unterstützte Formate
│
├── /api/tracks/
│   ├── GET /                  # Alle Tracks abrufen
│   ├── GET /{track_id}        # Track-Details
│   └── GET /similar/{track_id} # Ähnliche Tracks
│
├── /api/playlists/
│   ├── POST /generate         # Playlist generieren
│   ├── GET /{playlist_id}     # Playlist abrufen
│   └── POST /{id}/export      # Playlist exportieren
│
└── /api/config/
    ├── GET /presets           # Verfügbare Presets
    └── GET /settings          # Aktuelle Einstellungen
```

### Wichtige HTTP-Endpunkte

| HTTP Method | Endpunkt | Funktion | Beispiel |
|-------------|----------|----------|----------|
| GET | `/health` | Server-Status prüfen | `curl http://localhost:8000/health` |
| POST | `/api/analysis/start` | Audio-Analyse starten | `curl -X POST ... -d '{"directories":[...]}' ` |
| GET | `/api/analysis/{task_id}/status` | Analyse-Status prüfen | `curl http://localhost:8000/api/analysis/task_123/status` |
| GET | `/api/tracks` | Tracks mit Filter abrufen | `curl "http://localhost:8000/api/tracks?bpm_min=120"` |
| POST | `/api/playlists/generate` | Intelligente Playlist generieren | `curl -X POST ... -d '{"preset":"progressive_house"}' ` |
| POST | `/api/playlists/{id}/export` | Playlist exportieren | `curl -X POST ... -d '{"format":"m3u"}' ` |
| GET | `/docs` | Swagger UI öffnen | Browser: `http://localhost:8000/docs` |

## 🎼 API-Beispiel-Workflow: Progressive House Set

### Szenario
Sie möchten ein 1-stündiges Progressive House Set via API für einen Club-Auftritt erstellen.

### API-Schritt-für-Schritt

1. **Musikverzeichnis scannen**:
   ```bash
   curl -X POST "http://localhost:8000/api/analysis/start" \
        -H "Content-Type: application/json" \
        -d '{
          "directories": ["/music/progressive_house"],
          "recursive": true,
          "overwrite_cache": false
        }'
   ```

2. **Analyse-Status verfolgen**:
   ```bash
   # Wiederholt prüfen bis status = "completed"
   curl "http://localhost:8000/api/analysis/task_20250107_103000_0/status"
   ```

3. **Tracks für Progressive House abrufen**:
   ```bash
   curl "http://localhost:8000/api/tracks?bpm_min=120&bpm_max=130&limit=50"
   ```

4. **Intelligente Playlist generieren**:
   ```bash
   curl -X POST "http://localhost:8000/api/playlists/generate" \
        -H "Content-Type: application/json" \
        -d '{
          "preset": "progressive_house",
          "target_duration": 3600,
          "options": {
            "bpm_range": [120, 130],
            "energy_curve": "gradual_buildup",
            "harmony_strictness": 0.8,
            "mood_consistency": 0.7
          }
        }'
   ```

5. **Playlist für Rekordbox exportieren**:
   ```bash
   curl -X POST "http://localhost:8000/api/playlists/playlist_20250107_103500/export" \
        -H "Content-Type: application/json" \
        -d '{
          "format": "rekordbox_xml",
          "options": {
            "relative_paths": true,
            "include_cues": true,
            "include_beatgrid": true
          }
        }'
   ```

### API-Response Beispiele

**Track-Daten**:
```json
{
  "file_path": "/music/track.mp3",
  "features": {
    "bpm": 125.3,
    "energy": 0.78,
    "valence": 0.72
  },
  "camelot": {
    "key": "Am",
    "camelot": "8A",
    "compatible_keys": ["7A", "8A", "9A", "8B"]
  },
  "mood": {
    "primary_mood": "driving",
    "confidence": 0.87
  }
}
```

**Playlist-Metadata**:
```json
{
  "playlist_id": "playlist_20250107_103500",
  "metadata": {
    "total_tracks": 18,
    "total_duration": 3847,
    "average_bpm": 125.3,
    "energy_progression": "gradual_buildup",
    "mood_consistency": 0.84
  }
}
```

## 🔧 API-Konfiguration & Optimierung

### Backend-Performance optimieren

**Environment Variables (.env)**:
```bash
# Audio-Analyse-Performance
MAX_WORKERS=4
ENABLE_MULTIPROCESSING=true
MAX_FILE_SIZE_MB=500

# Cache-Optimierung
AUDIO_CACHE_DIR=./data/cache
CACHE_CLEANUP_DAYS=30
CACHE_MAX_SIZE_GB=2

# Server-Performance
WORKER_TIMEOUT=300
ENABLE_UVLOOP=true
DEBUG=false
```

### Audio-Qualität konfigurieren

**GET /api/config/settings** Response:
```json
{
  "audio_analysis": {
    "cache_dir": "./data/cache",
    "enable_multiprocessing": true,
    "max_workers": 4,
    "supported_formats": [".mp3", ".wav", ".flac", ".aac"]
  },
  "playlist_engine": {
    "default_algorithm": "harmonic",
    "camelot_wheel_enabled": true,
    "energy_analysis_enabled": true
  }
}
```

### Server-Performance überwachen

```bash
# System-Statistiken
curl "http://localhost:8000/api/analysis/stats"

# Cache-Performance
curl "http://localhost:8000/api/analysis/cache/stats"

# Aktive Background-Tasks
curl "http://localhost:8000/api/tasks/active"
```

## 🎯 API Next Steps

Nach dem erfolgreichen API Quick Start:

1. **API-Features vertiefen**:
   - [FastAPI Documentation](api/README.md) - Vollständige Endpunkt-Referenz
   - [Background Task Monitoring](technical/background-tasks.md)
   - [Cache Management](technical/cache-management.md)

2. **Client-Integration entwickeln**:
   - Python SDK mit `requests` oder `httpx`
   - JavaScript/Node.js Client mit `fetch` oder `axios`
   - Frontend-Integration (React, Vue, Angular)

3. **Production Deployment**:
   - [Docker Deployment](deployment.md#docker)
   - [Kubernetes Scaling](deployment.md#kubernetes)
   - [API Rate Limiting & Authentication](api/authentication.md)

4. **Erweiterte Features**:
   - Custom Playlist-Algorithmen entwickeln
   - Mood-Classifier-Modelle trainieren
   - Export-Formate erweitern

## ❓ Häufige API-Fragen

**Q: Wie lange dauert die API-Analyse?**
A: ~2-4 Sekunden pro Track (mit librosa), ~1-2 Sekunden (cached). Mit Essentia eventuell länger aber genauer.

**Q: Welche Audio-Formate unterstützt die API?**
A: MP3, WAV, FLAC, AAC, OGG, M4A, AIFF, AU, WMA, OPUS - über `GET /api/analysis/formats` abrufbar.

**Q: Ist die API thread-safe für parallele Requests?**
A: Ja, FastAPI ist async und unterstützt concurrent requests. Background Tasks laufen isoliert.

**Q: Wie genau ist die BPM-Erkennung via API?**
A: librosa: ±0.5 BPM, Essentia (falls verfügbar): ±0.1 BPM. Konfidenz-Scores in Response enthalten.

**Q: Kann die API offline betrieben werden?**
A: Ja, vollständig offline. Keine externen API-Calls oder Internet-Verbindung erforderlich.

**Q: Wie überwache ich API-Performance?**
A: Health-Endpoint (`/health`), Metrics (`/api/analysis/stats`) und Background-Task-Monitoring (`/api/tasks/active`).

**Q: Gibt es Rate-Limiting?**
A: Standardmäßig nein, kann aber für Production konfiguriert werden. Background Tasks sind inherent begrenzt.

**Q: Wie skaliere ich das Backend?**
A: Horizontal mit Docker/Kubernetes, vertikal mit `MAX_WORKERS` Environment Variable.

## 🆘 API Troubleshooting

**Problem**: Backend startet nicht
**Lösung**: 
```bash
# Dependencies prüfen
pip install -r requirements.txt

# Direkt starten für Fehlermeldungen
uvicorn backend.main:app --reload --port 8000
```

**Problem**: `/health` antwortet nicht
**Lösung**: Port-Konflikte prüfen, anderen Port verwenden (`--port 8001`)

**Problem**: Audio-Analyse hängt
**Lösung**: 
```bash
# Task-Status prüfen
curl "http://localhost:8000/api/analysis/{task_id}/status"

# Ggf. abbrechen
curl -X POST "http://localhost:8000/api/analysis/{task_id}/cancel"
```

**Problem**: Keine Tracks gefunden
**Lösung**: 
```bash
# Verzeichnis validieren
curl "http://localhost:8000/api/analysis/validate/directory?directory=/path/to/music"

# Unterstützte Formate prüfen
curl "http://localhost:8000/api/analysis/formats"
```

**Problem**: Playlist-Generierung schlägt fehl
**Lösung**: 
- BPM-Bereich erweitern (`bpm_range: [60, 200]`)
- Harmony-Strictness reduzieren (`harmony_strictness: 0.5`)
- Mehr Tracks analysieren lassen

---

**🎉 Herzlichen Glückwunsch!** Sie haben erfolgreich Ihre erste API-basierte Playlist erstellt. Erkunden Sie nun die erweiterten API-Features für professionelle DJ-Software-Integration.

**API Weiter zu**: [FastAPI Docs](api/README.md) | [Swagger UI](http://localhost:8000/docs) | [Development Guide](developer-guide.md)