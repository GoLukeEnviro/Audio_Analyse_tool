# DJ Audio-Analyse-Tool Pro Backend - Dokumentation

Willkommen zur umfassenden Dokumentation des DJ Audio-Analyse-Tools Pro Backend API v2.0 - **Project Phoenix**.

**🚀 Neue Architektur**: Dieses Tool wurde vollständig von einer monolithischen Desktop-Anwendung zu einem modernen headless FastAPI Backend transformiert.

## 📚 Dokumentations-Übersicht

### API-Dokumentation
- [FastAPI Reference](api/README.md) - Vollständige REST API-Dokumentation
- [Quick Start Guide](quick-start.md) - API-Schnelleinstieg für neue Entwickler
- [Installation Guide](installation.md) - Backend Setup und Deployment
- [Authentication](api/authentication.md) - API-Authentifizierung
- [Rate Limiting](api/rate-limiting.md) - API-Limits und Quotas

### Backend-Architektur
- [System Architecture](architecture.md) - Microservice-Design und Komponenten
- [Audio Analysis Engine](technical/audio-analysis.md) - librosa + Essentia Integration
- [Background Tasks](technical/background-tasks.md) - Asynchrone Verarbeitung
- [Cache Management](technical/cache-management.md) - Intelligente Zwischenspeicherung
- [Database Schema](technical/database.md) - Datenmodelle und Persistierung

### Entwickler-Guides
- [Developer Guide](developer-guide.md) - Backend-Entwicklung Best Practices
- [Testing Guide](testing.md) - API Tests und Mocking
- [Deployment Guide](deployment.md) - Docker, Kubernetes, Cloud
- [Contributing](contributing.md) - Beitragsrichtlinien für Backend-Entwicklung

### Features & Komponenten
- [Playlist Engine API](technical/playlist-engine-api.md) - Intelligente Playlist-Generierung
- [Mood Classification](technical/mood-classification.md) - Heuristik + ML-basierte Stimmungsanalyse  
- [Export Formats](technical/export-formats.md) - Rekordbox, M3U, JSON, CSV Export
- [Camelot Wheel](technical/camelot-wheel.md) - Harmonische Kompatibilität
- [Batch Processing](technical/batch-processing.md) - Parallele Audio-Verarbeitung

## 🚀 API-Schnellstart

Für einen schnellen Einstieg in die Backend-API empfehlen wir:

1. **Backend starten**: `uvicorn backend.main:app --reload`
2. **API-Dokumentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
3. **Erste Audio-Analyse**: [Quick Start Guide](quick-start.md)
4. **Entwickler**: Lesen Sie den [Developer Guide](developer-guide.md)
5. **Probleme**: Schauen Sie in [Troubleshooting](troubleshooting.md)

### Wichtige API-Endpunkte

```bash
# Server-Status prüfen
GET /api/health

# Audio-Analyse starten
POST /api/analysis/start
{
  "directories": ["/path/to/music"]
}

# Playlist generieren
POST /api/playlists/generate
{
  "preset": "progressive_house",
  "target_duration": 3600
}

# Tracks abrufen
GET /api/tracks?limit=50&bpm_min=120&bpm_max=130
```

## 🏗️ Architektur-Highlights

- **FastAPI**: Moderne Python Web-Framework mit automatischer OpenAPI-Dokumentation
- **Asynchrone Verarbeitung**: Background Tasks für lange Audio-Analysen
- **Intelligente Cache**: JSON-basierte Persistierung mit MD5-Hashing
- **Modulare Engine**: Separate Komponenten für Analyse, Playlist, Export
- **Docker-Ready**: Containerisierte Deployment-Optionen
- **Essentia + librosa**: Professionelle Audio-Feature-Extraktion
- **RESTful Design**: Saubere API-Endpunkte für alle Funktionen

## 📖 Über diese Dokumentation

Diese Dokumentation beschreibt die neue headless Backend-Architektur (Project Phoenix). Bei Fragen oder Verbesserungsvorschlägen erstellen Sie bitte ein Issue im Repository.

**Version**: 2.0 (Phoenix Backend)  
**Architektur**: FastAPI REST Backend  
**Letzte Aktualisierung**: Januar 2025  
**Sprache**: Deutsch

---

*DJ Audio-Analyse-Tool Pro Backend - Headless Audio Analysis API for DJs*