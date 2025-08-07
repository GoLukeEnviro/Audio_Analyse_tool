# DJ Analysis Studio

A comprehensive audio analysis and playlist creation tool combining FastAPI backend with React frontend.

## Quick Start

### Voraussetzungen
Stelle sicher, dass folgende Software installiert ist:
- Python 3.8+ mit pip
- Node.js 16+ mit npm
- Python Virtual Environment (venv) im Projekt eingerichtet

### Abhängigkeiten installieren
Falls noch nicht geschehen:
1. Backend: `pip install -r requirements.txt` im `backend/`-Ordner ausführen
2. Frontend: `npm install` im `src/`-Ordner ausführen

### Anwendung starten
Im Projekt-Hauptverzeichnis:
- **Windows:** `start-dev.bat` ausführen
- **Linux/macOS:** `./start-dev.sh` ausführen

Die Anwendung startet automatisch:
- Backend (FastAPI): http://localhost:8000
- Frontend (React): http://localhost:3000

## Projekt-Struktur

```
├── backend/           # FastAPI Backend
│   ├── api/           # API Endpoints
│   ├── core_engine/   # Audio Analysis Engine
│   └── main.py        # FastAPI Hauptdatei
├── src/               # React Frontend
│   ├── components/    # React Components
│   ├── pages/         # App Pages
│   └── hooks/         # React Hooks
├── start-dev.bat      # Windows Start Script
├── start-dev.sh       # Linux/macOS Start Script
└── package.json       # Monorepo Configuration
```

## Entwicklung

- **Backend nur:** `npm run start:backend`
- **Frontend nur:** `npm run start:frontend`
- **Beide zusammen:** `npm run monorepo:dev`
