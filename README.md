# DJ Analysis Studio 🎵

Ein modernes Tool zur Audioanalyse und Playlist-Generierung mit einem FastAPI-Backend und React-Frontend.

## 🚀 Quick Start

### Voraussetzungen
- **Node.js** (v14 oder höher)
- **Python** (3.8 oder höher)
- **npm** oder **yarn**

### Installation

1. **Repository klonen**
   ```bash
   git clone [repository-url]
   cd Audio_Analyse_tool
   ```

2. **Entwicklungsumgebung starten (Windows)**
   ```bash
   start-dev.bat
   ```

3. **Entwicklungsumgebung starten (Linux/Mac)**
   ```bash
   chmod +x start-dev.sh
   ./start-dev.sh
   ```

4. **Manueller Start** (falls gewünscht)
   ```bash
   # Root-Abhängigkeiten installieren
   npm install
   
   # Frontend-Abhängigkeiten installieren
   cd src && npm install && cd ..
   
   # Backend-Abhängigkeiten installieren
   pip install -r requirements.txt
   
   # Services starten
   npm run monorepo:dev
   ```

## 📁 Projektstruktur

```
Audio_Analyse_tool/
├── backend/                 # FastAPI Backend
│   ├── main.py             # Hauptanwendung
│   ├── models/             # Datenmodelle
│   ├── services/           # Geschäftslogik
│   └── utils/              # Hilfsfunktionen
├── src/                    # React Frontend
│   ├── package.json        # Frontend-Abhängigkeiten
│   ├── src/                # React-Komponenten
│   └── public/             # Statische Dateien
├── tests/                  # Test-Suite
│   ├── unit/              # Unit-Tests
│   ├── integration/        # Integration-Tests
│   └── api/               # API-Tests
├── config/                 # Konfigurationsdateien
├── data/                   # Datenverzeichnis
├── .env.example           # Beispiel-Umgebungsvariablen
├── package.json            # Root-Monorepo-Setup
├── requirements.txt        # Python-Abhängigkeiten
└── start-dev.bat          # Windows-Startskript
```

## 🌐 Zugriff

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API-Dokumentation**: http://localhost:8000/docs

## 🔧 Konfiguration

### Umgebungsvariablen

Kopiere `.env.example` zu `.env` und passe die Werte an:

```bash
cp .env.example .env
```

Wichtige Einstellungen:
- `DEBUG=true` - Debug-Modus aktivieren
- `PORT=8000` - Backend-Port
- `REACT_APP_API_URL=http://localhost:8000` - API-URL für Frontend
- `MAX_FILE_SIZE_MB=500` - Maximale Dateigröße für Uploads

### Essentia Audioanalyse

> ⚠️ **Wichtig**: Essentia kann unter Windows schwer zu installieren sein.

**Option 1: Librosa Fallback (Standard)**
- Keine zusätzliche Installation erforderlich
- Verwendet Librosa als Fallback
- Funktioniert sofort nach Setup

**Option 2: Essentia installieren (optional)**
```bash
# Versuch 1: Standard-Installation
pip install essentia

# Versuch 2: TensorFlow-Variante
pip install essentia-tensorflow

# Versuch 3: Kompilieren aus Quellcode
# Siehe: https://essentia.upf.edu/installing.html
```

**Essentia aktivieren:**
In `.env` setzen:
```
ESSENTIA_ENABLED=true
```

## 🧪 Tests

### Alle Tests ausführen
```bash
# Backend-Tests
pytest tests/ -v

# Frontend-Tests
cd src && npm test

# Integration-Tests
npm run test:integration
```

### Test-Setup prüfen
```bash
# Grundlegende Setup-Validierung
python tests/unit/test_basic_setup.py
```

## 🛠️ Verfügbare Skripte

| Skript | Beschreibung |
|--------|--------------|
| `npm run monorepo:dev` | Startet Backend und Frontend |
| `npm run start:backend` | Startet nur das Backend |
| `npm run start:frontend` | Startet nur das Frontend |
| `npm run build` | Build für beide Services |
| `npm run test` | Führt alle Tests aus |
| `npm run lint` | Code-Qualität prüfen |
| `npm run clean` | Temporäre Dateien löschen |

## 🐛 Bekannte Probleme & Lösungen

### 1. Essentia-Installation fehlschlägt
- **Problem**: `pip install essentia` schlägt fehl
- **Lösung**: Verwende Librosa-Fallback (funktioniert automatisch)
- **Alternative**: Siehe Essentia-Dokumentation für manuelle Installation

### 2. Ports bereits belegt
- **Problem**: Port 8000 oder 3000 bereits in Verwendung
- **Lösung**: Ports in `.env` ändern
  ```
  PORT=8001
  PORT=3001
  ```

### 3. ImportError: No module named 'backend'
- **Problem**: Python-Pfad nicht korrekt
- **Lösung**: Im Root-Verzeichnis ausführen, PYTHONPATH ist korrekt konfiguriert

### 4. Frontend startet nicht
- **Problem**: `npm run monorepo:dev` fehlschlägt
- **Lösung**: 
  1. `npm install` im Root-Verzeichnis
  2. `npm install` im `src/` Verzeichnis
  3. Erneut versuchen

## 📊 Features

- **Audio-Analyse**: BPM, Key, Mood, Energy, etc.
- **Playlist-Generierung**: Automatische Playlists basierend auf Analyse
- **Visualisierung**: Wellenformen, Spektrogramme, BPM-Graphen
- **Export**: Playlists als CSV, M3U, JSON
- **Caching**: Schnelle wiederholte Analysen
- **Multi-Format**: Unterstützt MP3, WAV, FLAC, M4A, AAC, AIFF

## 🎯 Entwicklung

### Code-Style
- **Backend**: PEP 8 (Python)
- **Frontend**: ESLint + Prettier (JavaScript/React)

### Debugging
- **Backend**: `DEBUG=true` in `.env`
- **Frontend**: Browser DevTools
- **Logs**: `./data/logs/` Verzeichnis

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei.

## 🤝 Beitrag

1. Fork erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Commits erstellen (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📞 Support

Bei Problemen:
1. Prüfe die [bekannten Probleme](#-bekannte-probleme--lösungen)
2. Starte mit `start-dev.bat` (Windows) oder `start-dev.sh` (Linux/Mac)
3. Prüfe die Logs im Terminal
4. Erstelle ein Issue mit System-Informationen
