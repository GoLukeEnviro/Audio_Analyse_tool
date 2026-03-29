# 📊 GAP-ANALYSE – Visual DJ Analysis Studio
**Erstellt am:** 29. März 2026  
**Analysiert von:** GitHub Copilot Agent  
**Repository:** GoLukeEnviro/Audio_Analyse_tool  
**Branch:** copilot/gaps-analysis-report

---

## 📌 Zusammenfassung (Executive Summary)

Das Projekt ist zu **~65 % fertiggestellt**. Das Backend (FastAPI, Audio-Analyse-Engine, Datenmanagement, Export) ist **gut ausgebaut und funktionsfähig**. Das Frontend (React/TypeScript) ist **strukturell komplett** aber weist mehrere **nicht funktionale UI-Elemente** auf. Kritische Infrastruktur-Dateien (Docker, CI/CD, Lizenz, `.env.example`) fehlen vollständig. Die Vision des „Creator Studios" (Canvas-basierte Energie-Kurve zeichnen) ist nur rudimentär umgesetzt.

---

## ✅ VOLLSTÄNDIG IMPLEMENTIERT

### 🔧 Backend – Core Engine

| Komponente | Datei | Status |
|---|---|---|
| Audio-Analyzer (librosa + Essentia Fallback) | `backend/core_engine/audio_analysis/analyzer.py` | ✅ Vollständig |
| Feature-Extractor (BPM, Key, Energy, Valence, MFCC etc.) | `backend/core_engine/audio_analysis/feature_extractor.py` | ✅ Vollständig |
| Zeitreihen-Extraktion (Energie-/Helligkeitskurve) | `analyzer.py::_extract_time_series_features()` | ✅ Vollständig |
| Mood-Classifier (regelbasierte Heuristik) | `backend/core_engine/mood_classifier/mood_classifier.py` | ✅ Vollständig |
| Playlist-Engine (5 Algorithmen) | `backend/core_engine/playlist_engine/playlist_engine.py` | ✅ Vollständig |
| Playlist-Exporter (M3U, JSON, CSV, Rekordbox XML) | `backend/core_engine/export/playlist_exporter.py` | ✅ Vollständig |
| Database Manager (SQLite, Indexing, Batch-Inserts) | `backend/core_engine/data_management/database_manager.py` | ✅ Vollständig |
| Cache Manager (Multi-Level) | `backend/core_engine/data_management/cache_manager.py` | ✅ Vollständig |
| Camelot Wheel Mapping | `feature_extractor.py::get_compatible_keys()` | ✅ Vollständig |
| Fallback-Analyse (fehlertolerante Verarbeitung) | `feature_extractor.py::get_fallback_analysis()` | ✅ Vollständig |
| Thread-Pool für Batch-Analyse | `analyzer.py::analyze_batch_async()` | ✅ Vollständig |

### 🌐 Backend – API (FastAPI)

| Endpoint-Gruppe | Datei | Status |
|---|---|---|
| Tracks CRUD + Suche + Filterung | `backend/api/endpoints/tracks.py` | ✅ Vollständig |
| Playlist-Generierung + Status + Export | `backend/api/endpoints/playlists.py` | ✅ Vollständig |
| Analyse-Start, -Status, -Abbruch | `backend/api/endpoints/analysis.py` | ✅ Vollständig |
| Konfiguration lesen/schreiben | `backend/api/endpoints/config.py` | ✅ Vollständig |
| CORS Middleware | `backend/main.py` | ✅ Vollständig |
| Global Exception Handler | `backend/main.py` | ✅ Vollständig |
| Health-Check Endpoint | `backend/main.py::health()` | ✅ Vollständig |
| API-Status Endpoint | `backend/main.py::api_status()` | ✅ Vollständig |
| WebSocket Heartbeat | `backend/main.py::websocket_health_endpoint()` | ✅ Vollständig |
| Pydantic Data Models | `backend/api/models.py` | ✅ Vollständig |

### 🎨 Frontend – Seiten & Komponenten

| Seite / Komponente | Datei | Status |
|---|---|---|
| Dashboard (Stats-Cards, Schnellzugriff) | `src/pages/Dashboard.tsx` | ✅ Vollständig |
| Bibliothek mit Filterung & Pagination | `src/pages/Library.tsx` | ✅ Vollständig |
| Analyse-Center (Start/Stop/Monitor) | `src/pages/AnalysisCenter.tsx` | ✅ Vollständig |
| Creator Studio (Playlist-Generierung) | `src/pages/CreatorStudio.tsx` | ✅ Strukturell vorhanden |
| Track-Detailansicht mit Energie-Chart | `src/pages/TrackDetails.tsx` | ✅ Vollständig |
| Energie-Liniendiagramm (Recharts) | `src/components/charts/EnergyChart.tsx` | ✅ Vollständig |
| Fortschrittsmonitor (Analyse-Liveview) | `src/components/analysis/ProgressMonitor.tsx` | ✅ Vollständig |
| Track-Karte (BPM, Mood, Energy Anzeige) | `src/components/tracks/TrackCard.tsx` | ✅ Vollständig |
| Filter-Panel (Suche, Mood, BPM, Energy, Key) | `src/components/tracks/FilterPanel.tsx` | ✅ Vollständig |
| Track-Selektor (für Creator Studio) | `src/components/tracks/TrackSelector.tsx` | ✅ Vollständig |
| Error Boundary | `src/components/common/ErrorBoundary.tsx` | ✅ Vorhanden |
| Loading Skeleton | `src/components/common/LoadingSkeleton.tsx` | ✅ Vollständig |
| Notification Provider (Toast-System) | `src/components/common/NotificationProvider.tsx` | ✅ Vollständig |
| App-Layout + Navigation-Sidebar | `src/components/layout/AppLayout.tsx` | ✅ Vollständig |
| React Hooks (Tracks, Analysis, Playlist) | `src/hooks/` | ✅ Vollständig |
| TypeScript Interfaces & Enums | `src/types/` | ✅ Vollständig |
| Formatter-Utilities | `src/utils/formatters.ts` | ✅ Vollständig |
| Dark-Theme-Konfiguration | `src/theme/theme.ts` | ✅ Vollständig |

### 🧪 Tests

| Test-Bereich | Datei | Status |
|---|---|---|
| Unit Tests (Basic Setup) | `tests/unit/test_basic_setup.py` | ✅ Vollständig |
| Unit Tests (Core Engine) | `tests/unit/test_core_unit.py` | ✅ Vorhanden |
| Unit Tests (Database Manager) | `tests/unit/test_database_manager.py` | ✅ Vorhanden |
| Unit Tests (Zeitreihen-Analyse) | `tests/unit/test_audio_analyzer_time_series.py` | ✅ Vorhanden |
| Integration Tests | `tests/integration/test_core_integration.py` | ✅ Vorhanden |
| API Tests | `tests/api/test_api_endpoints.py` | ✅ Vorhanden |
| Stress Tests (Broken Audio, Mass Load, Null Values) | `tests/stress/` | ✅ Vorhanden |

### 🏗️ Konfiguration & Infrastruktur

| Element | Datei | Status |
|---|---|---|
| Backend-Einstellungen (YAML + JSON) | `backend/config/settings.py` | ✅ Vollständig |
| Standard-Konfiguration | `config/default_config.yaml` | ✅ Vorhanden |
| Benutzer-Presets | `config/custom_presets.json` | ✅ Vorhanden |
| Monorepo package.json (Start-Skripte) | `package.json` | ✅ Vorhanden |
| Start-Skripte (Windows + Linux) | `start-dev.bat`, `start-dev.sh` | ✅ Vorhanden |
| pytest Konfiguration | `pytest.ini` | ✅ Vorhanden |
| .gitignore | `.gitignore` | ✅ Vorhanden |
| .dockerignore | `.dockerignore` | ✅ Vorhanden |

---

## ⚠️ TEILWEISE IMPLEMENTIERT (Needs Work)

### 1. 🎨 Creator Studio – Energie-Kurven-Zeichnung
**Ist-Zustand:** Ein einfacher MUI `Slider`-Balken mit 5 Punkten  
**Soll-Zustand (Vision):** Interaktives Canvas, auf dem der DJ den Energieverlauf frei zeichnen kann (wie im README beschrieben: „Du zeichnest auf einer leeren Leinwand")  
**Lücke:** Die zentrale Vision des Produkts – die „Leinwand" – fehlt. Kein Canvas-basiertes Drawing-Tool, kein freies Zeichnen der Kurve.  
**Priorität:** 🔴 HOCH

### 2. 🔴 WebSocket – Real-Time Analyse-Progress
**Ist-Zustand:** Nur `/ws/health` Heartbeat-WebSocket implementiert  
**Soll-Zustand:** Analyse-Fortschritt in Echtzeit an das Frontend streamen (welche Datei wird gerade analysiert, wie viele bereits fertig)  
**Lücke:** Das Frontend fragt den Status per Polling (alle 2000ms) ab, anstatt echte WebSocket-Events zu empfangen  
**Priorität:** 🟡 MITTEL

### 3. 🤖 ML-basierter Mood-Classifier
**Ist-Zustand:** Vollständige Infrastruktur für LightGBM-Modell vorhanden (Loading, Feature-Vorbereitung, Prediction)  
**Soll-Zustand:** Trainiertes Modell `data/models/mood_model.txt` vorhanden  
**Lücke:** Kein trainiertes Modell existiert, der ML-Classifier ist deaktiviert; nur heuristische Regeln sind aktiv  
**Priorität:** 🟡 MITTEL (Heuristik funktioniert, ML wäre eine Verbesserung)

### 4. 🎵 Audio-Preview / Waveform-Visualisierung
**Ist-Zustand:** `wavesurfer.js` (v7) als Dependency in `src/package.json` installiert  
**Soll-Zustand:** Audio-Vorschau in der Bibliothek und auf der Track-Detailseite  
**Lücke:** Wavesurfer.js ist installiert aber nirgendwo im Code verwendet  
**Priorität:** 🟡 MITTEL

### 5. ⚙️ Settings-Seite – Teilweise nicht funktionale Buttons
**Ist-Zustand:**  
- „Zurücksetzen": Schaltfläche vorhanden, aber keine Logik (kein Handler)  
- „Cache löschen": Schaltfläche vorhanden, aber keine Logik  
- „Dark Theme Toggle": Switch vorhanden, aber er ändert das Theme nicht  
**Soll-Zustand:** Alle Buttons führen ihre jeweilige Aktion aus  
**Priorität:** 🟡 MITTEL

### 6. 📊 Dashboard – Letzte Aktivitäten
**Ist-Zustand:** Hardcoded Beispieldaten ("Analyse von 15 Tracks abgeschlossen", "vor 2 Stunden")  
**Soll-Zustand:** Echte Aktivitätsdaten aus der Datenbank/API  
**Priorität:** 🟢 NIEDRIG

### 7. 🔁 Error Boundary – Konsistente Anwendung
**Ist-Zustand:** `ErrorBoundary`-Komponente existiert  
**Soll-Zustand:** Alle Hauptseiten sind mit Error Boundaries gewrappt  
**Lücke:** Keine der Seiten nutzt die Error Boundary aktiv  
**Priorität:** 🟡 MITTEL

### 8. 📁 Dupliziertes `src/src/` Verzeichnis
**Ist-Zustand:** Alle Dateien aus `src/` sind auch in `src/src/` vorhanden (mit leichten Abweichungen bei Import-Pfaden, z.B. `.tsx`-Erweiterungen in Imports)  
**Soll-Zustand:** Nur `src/` sollte existieren, `src/src/` ist Redundanz und sollte entfernt werden  
**Lücke:** Technische Schulden / Verwirrungspotenzial  
**Priorität:** 🟡 MITTEL (Aufräum-Aktion nötig)

---

## ❌ NICHT IMPLEMENTIERT (Fehlend)

### 🐳 Deployment & Container

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| `Dockerfile` (Backend) | In Architektur-Docs beschrieben, Datei fehlt | 🔴 HOCH |
| `Dockerfile` (Frontend) | In Architektur-Docs beschrieben, Datei fehlt | 🔴 HOCH |
| `docker-compose.yml` | In Architektur-Docs beschrieben (`services: backend, frontend, nginx`), Datei fehlt | 🔴 HOCH |
| `.env.example` | README beschreibt `cp .env.example .env`, Datei fehlt | 🔴 HOCH |
| `nginx.conf` | Im docker-compose Beispiel referenziert, fehlt | 🟡 MITTEL |

### ⚙️ CI/CD & Automatisierung

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| `.github/workflows/ci.yml` | Kein GitHub Actions Workflow vorhanden | 🔴 HOCH |
| `.github/workflows/test.yml` | Automatische Test-Ausführung bei PR | 🔴 HOCH |
| `.github/workflows/build.yml` | Automatischer Build bei Push auf main | 🟡 MITTEL |
| Pre-commit Hooks | Kein automatisches Linting/Formatting | 🟢 NIEDRIG |

### 📄 Rechtliches & Dokumentation

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| `LICENSE` | README referenziert `[LICENSE](LICENSE)`, Datei fehlt | 🔴 HOCH |
| `CHANGELOG.md` | Keine Versionshistorie | 🟢 NIEDRIG |
| `tests/README.md` | README verlinkt auf `[Testing-Guide](tests/README.md)`, Datei fehlt | 🟡 MITTEL |
| `CONTRIBUTING.md` | Kein Beitragsleitfaden | 🟢 NIEDRIG |

### 🔒 Sicherheit & Authentifizierung

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| Authentifizierung (z.B. JWT) | In Architektur erwähnt (`Auth Middleware`), nicht implementiert | 🟡 MITTEL |
| API Rate Limiting | In Architektur beschrieben, nicht implementiert | 🟡 MITTEL |
| Path-Traversal-Schutz | In Architektur beschrieben für File-System-Level, nicht verifiziert | 🟡 MITTEL |
| API-Key / Token-Validierung | Keine Authentifizierung für API-Endpoints | 🟡 MITTEL |

### 🎵 Track-Management

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| Track löschen (API + UI) | Kein DELETE-Endpoint für Tracks | 🟡 MITTEL |
| Track-Metadaten bearbeiten | Kein Edit-Interface für Titel/Artist | 🟢 NIEDRIG |
| Bulk-Operationen (Mehrfachauswahl löschen) | Nicht vorhanden | 🟢 NIEDRIG |
| Cover-Art Anzeige | Track-Cards zeigen kein Album-Cover | 🟢 NIEDRIG |
| Favoriten / Tagging-System | Keine benutzerdefinierte Kategorisierung | 🟢 NIEDRIG |

### 🔄 Hintergrundprozesse

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| Automatischer Verzeichnis-Watcher | Keine automatische Erkennung neuer Dateien | 🟡 MITTEL |
| Geplante Re-Analyse (Scheduler) | Keine periodische Aktualisierung | 🟢 NIEDRIG |
| Background-Task-Queue | Lange Analysen blockieren ggf. den API-Server | 🟡 MITTEL |

### 🖥️ Frontend – Fehlende Features

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| Frontend-Tests (Jest/React Testing Library) | `src/package.json` hat Test-Skript, aber keine Testdateien | 🔴 HOCH |
| Canvas-Zeichenwerkzeug (Creator Studio) | Die Kern-Vision: Energie-Kurve frei zeichnen | 🔴 HOCH |
| Helligkeits-Chart in TrackDetails | `EnergyChart` zeigt nur Energie, nicht `brightness_value` | 🟡 MITTEL |
| Waveform-Visualisierung (wavesurfer.js) | Dependency installiert, aber nicht integriert | 🟡 MITTEL |
| Responsives Mobile-Design | Erwähnt im README, nicht verifiziert/optimiert | 🟡 MITTEL |
| Playlist-Vorschau (Trackliste nach Generierung) | Nur Anzahl der Tracks, keine vollständige Liste | 🟡 MITTEL |
| Dark/Light Theme Toggle (funktional) | Switch in Settings vorhanden, aber nicht verdrahtet | 🟡 MITTEL |
| Sortierung per Spalten-Header in Bibliothek | Kein interaktiver Spalten-Sort | 🟢 NIEDRIG |
| Drag & Drop (Playlist neu ordnen) | Nicht vorhanden | 🟢 NIEDRIG |
| Keyboard-Shortcuts | Keine definierten Shortcuts | 🟢 NIEDRIG |

### 🗃️ Datenbank & Performance

| Fehlendes Element | Beschreibung | Priorität |
|---|---|---|
| Datenbankmigrationen (Alembic) | Keine Migrationsstrategie beim Schema-Update | 🟡 MITTEL |
| Redis für verteilten Cache | In Architektur beschrieben, nur SQLite/Memory-Cache vorhanden | 🟢 NIEDRIG |
| PostgreSQL-Support | Nur SQLite implementiert | 🟢 NIEDRIG |
| Datenbank-Backup-Mechanismus (automatisch) | Nur manuelle Cleanup-Skripte vorhanden | 🟡 MITTEL |

---

## 📈 GESAMTSTATUS-ÜBERSICHT

```
Gesamt-Implementierungsgrad: ████████████░░░░░░░░  ~65%

Backend Core Engine:      ██████████████████░░  ~90%
Backend API:              ████████████████░░░░  ~80%
Frontend UI:              ████████████░░░░░░░░  ~65%
Frontend Tests:           ████░░░░░░░░░░░░░░░░  ~15%
Deployment/Infra:         ████░░░░░░░░░░░░░░░░  ~20%
Dokumentation:            ████████████████░░░░  ~80%
Sicherheit:               ████░░░░░░░░░░░░░░░░  ~20%
```

---

## 🎯 PRIORISIERTE MASSNAHMEN (Handlungsplan)

### 🔴 Priorität 1 – Kritisch (sofort angehen)

1. **`.env.example` erstellen** – README referenziert diese Datei, sie fehlt  
2. **`LICENSE`-Datei hinzufügen** – MIT-Lizenz laut README  
3. **`Dockerfile` + `docker-compose.yml` erstellen** – Für reproduzierbare Deployments  
4. **GitHub Actions CI/CD Pipeline** – Automatische Tests bei jedem PR  
5. **Frontend-Tests (Jest)** – Zumindest Smoke-Tests für alle 6 Seiten  

### 🟡 Priorität 2 – Wichtig (nächste Iteration)

6. **Canvas-Zeichenwerkzeug für Creator Studio** – Die Kernvision des Produkts  
7. **Wavesurfer.js integrieren** – Audio-Vorschau in Bibliothek & Track-Details  
8. **WebSocket für Analyse-Fortschritt** – Statt Polling echte Events  
9. **Settings-Seite vervollständigen** – Zurücksetzen/Cache löschen/Theme-Toggle  
10. **Error Boundaries auf allen Hauptseiten anwenden**  
11. **`src/src/` Duplikat bereinigen**  
12. **`tests/README.md` erstellen** (README verlinkt dorthin)  
13. **Track-Löschfunktion** (API + UI)  
14. **Authentifizierung** (zumindest API-Key für Produktionsumgebung)  

### 🟢 Priorität 3 – Nice-to-Have (zukünftige Versionen)

15. **ML-Modell für Mood-Classifier trainieren und einbinden**  
16. **Automatischer Verzeichnis-Watcher**  
17. **Playlist-Vorschau (vollständige Trackliste)**  
18. **Cover-Art Anzeige in Track-Cards**  
19. **Redis-Cache für Skalierung**  
20. **Datenbankmigrationen (Alembic)**  
21. **Mobile-Optimierung/Responsive Design verfeinern**  
22. **Helligkeits-Chart** (`brightness_value`) neben dem Energie-Chart  

---

## 🗂️ DATEI-STRUKTUR STATUS

```
Audio_Analyse_tool/
├── ✅ README.md
├── ✅ PROJECT_OVERVIEW.md
├── ✅ ARCHITEKTUR_OVERVIEW.md
├── ✅ SYSTEM_DOKUMENTATION.md
├── ✅ GAP_ANALYSE.md               ← DIESE DATEI (neu)
├── ❌ LICENSE                       ← FEHLT
├── ❌ .env.example                  ← FEHLT (README referenziert es)
├── ❌ Dockerfile                    ← FEHLT (Architektur beschreibt es)
├── ❌ docker-compose.yml            ← FEHLT (Architektur beschreibt es)
├── ❌ nginx.conf                    ← FEHLT
├── ❌ .github/
│   └── ❌ workflows/
│       ├── ❌ ci.yml                ← FEHLT
│       └── ❌ test.yml              ← FEHLT
├── ✅ backend/
│   ├── ✅ main.py
│   ├── ✅ api/
│   │   ├── ✅ models.py
│   │   └── ✅ endpoints/
│   │       ├── ✅ tracks.py
│   │       ├── ✅ playlists.py
│   │       ├── ✅ analysis.py
│   │       └── ✅ config.py
│   ├── ✅ core_engine/
│   │   ├── ✅ audio_analysis/
│   │   │   ├── ✅ analyzer.py
│   │   │   └── ✅ feature_extractor.py
│   │   ├── ✅ mood_classifier/
│   │   │   └── ✅ mood_classifier.py
│   │   ├── ✅ playlist_engine/
│   │   │   └── ✅ playlist_engine.py
│   │   ├── ✅ data_management/
│   │   │   ├── ✅ database_manager.py
│   │   │   └── ✅ cache_manager.py
│   │   └── ✅ export/
│   │       └── ✅ playlist_exporter.py
│   └── ✅ config/
│       └── ✅ settings.py
├── ✅ src/                           ← React Frontend
│   ├── ⚠️ src/                      ← DUPLIKAT (bereinigen!)
│   ├── ✅ pages/ (6 Seiten)
│   ├── ✅ components/ (11 Komponenten)
│   ├── ✅ hooks/ (4 Custom Hooks)
│   ├── ✅ types/ (interfaces.ts, enums.ts)
│   ├── ✅ utils/formatters.ts
│   ├── ✅ theme/theme.ts
│   └── ❌ __tests__/                ← FEHLT (keine Frontend-Tests)
├── ✅ tests/                         ← Backend-Tests
│   ├── ✅ unit/ (5 Testdateien)
│   ├── ✅ integration/
│   ├── ✅ api/
│   ├── ✅ stress/
│   └── ❌ README.md                 ← FEHLT (README verlinkt dorthin)
├── ✅ config/
│   ├── ✅ default_config.yaml
│   ├── ✅ custom_presets.json
│   └── ✅ settings.json
├── ✅ data/                          ← Datenbank (gitignored)
├── ✅ scripts/
│   ├── ✅ db_cleanup.py
│   └── ✅ advanced_db_cleanup.py
├── ✅ requirements.txt
├── ✅ requirements-dev.txt
├── ✅ package.json
├── ✅ pytest.ini
├── ✅ tsconfig.json
├── ✅ start-dev.bat
├── ✅ start-dev.sh
├── ✅ .gitignore
└── ✅ .dockerignore
```

---

## 🔍 TECHNISCHE SCHULDEN

| Problem | Beschreibung | Auswirkung |
|---|---|---|
| `src/src/` Duplikat | Alle Frontend-Dateien doppelt vorhanden | Verwirrung, Wartungsaufwand |
| Hartcodierte `API_BASE_URL` | `http://localhost:8000/api` in allen Hooks | Produktions-Deployment nicht möglich ohne Code-Änderung |
| Fehlende `.env.example` | Umgebungsvariablen nicht dokumentiert | Onboarding für neue Entwickler erschwert |
| Keine API-Versionierung | Aktuell `/api/tracks`, kein `/api/v1/tracks` | Breaking Changes ohne Migrationspfad |
| `data/database.db` im Repo | Wird durch .gitignore ausgeschlossen (korrekt), aber das `data/`-Verzeichnis ist leer eingecheckt | Kein Problem, aber ungewöhnlich |
| Test-Dateien im Root | `test_api_simple.py`, `test_multiprocessing_fix.py` etc. liegen im Root, nicht in `tests/` | Unordnung, sollten in `tests/` verschoben werden |
| Globale Singleton-Instanzen in API | `_analyzer = None`, `_database_manager = None` in Endpoints | Nicht thread-safe bei horizontaler Skalierung |
| Duplizierte Duplikate in `.gitignore` | Mehrere identische Einträge (z.B. `*.log` zweimal) | Kosmetisches Problem |

---

## 💡 QUICK WINS (Sofort umsetzbar, <1h je)

1. **`LICENSE`-Datei** hinzufügen (MIT-Text, 5 Minuten)  
2. **`.env.example`** erstellen mit allen dokumentierten Umgebungsvariablen (15 Minuten)  
3. **`tests/README.md`** erstellen (15 Minuten)  
4. **Root-Testdateien** in `tests/` verschieben (`test_api_simple.py` etc.) (10 Minuten)  
5. **Hardcodierte `API_BASE_URL`** in einen Konfigurations-Parameter auslagern (20 Minuten)  
6. **Nicht-funktionierende Buttons** in Settings mit `// TODO`-Kommentaren versehen oder Placeholder-Handler hinzufügen (20 Minuten)  

---

*GAP-Analyse erstellt am 29.03.2026 durch automatisierte Code-Inspektion aller Quelldateien.*  
*Nächste Überprüfung empfohlen nach Abschluss der Priorität-1-Maßnahmen.*
