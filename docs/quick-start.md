# Quick Start Guide

Ein schneller Einstieg in das DJ Audio-Analyse-Tool Pro v2.0 - von der Installation bis zur ersten Playlist in 10 Minuten.

## 🚀 In 5 Schritten zur ersten Playlist

### Schritt 1: Installation (2 Minuten)

```bash
# Repository klonen
git clone <repository-url>
cd Audio_Analyse_tool

# Automatische Installation
start.bat  # Doppelklick oder im Terminal
```

**✅ Erfolgreich wenn**: Die Anwendung startet und der Onboarding-Wizard erscheint.

### Schritt 2: Erste Konfiguration (1 Minute)

1. **Onboarding-Wizard durchlaufen**:
   - Musikbibliothek-Pfad auswählen (z.B. `C:\Users\[Name]\Music`)
   - Audio-Qualität wählen (Standard: "Hoch")
   - Export-Verzeichnis festlegen
   - Rekordbox-Integration aktivieren (optional)

2. **Wizard abschließen** → Hauptfenster öffnet sich

### Schritt 3: Musik hinzufügen (1 Minute)

**Option A: Ordner hinzufügen**
- Klick auf "Ordner hinzufügen" 📁
- Musikordner auswählen
- "Ordner analysieren" bestätigen

**Option B: Einzelne Dateien**
- Klick auf "Dateien hinzufügen" 🎵
- MP3/WAV/FLAC-Dateien auswählen
- "Öffnen" klicken

**Unterstützte Formate**: MP3, WAV, FLAC, AAC, OGG, M4A, AIFF

### Schritt 4: Audio-Analyse starten (3-5 Minuten)

1. **Analyse starten**:
   - Klick auf "Analyse starten" ▶️
   - Fortschrittsbalken beobachten
   - Bei 10 Tracks: ~30 Sekunden
   - Bei 100 Tracks: ~3-5 Minuten

2. **Analyse-Ergebnisse**:
   - BPM wird automatisch erkannt
   - Tonart (Key) wird bestimmt
   - Energie-Level wird berechnet
   - Stimmung wird klassifiziert

**💡 Tipp**: Während der Analyse können Sie bereits die Benutzeroberfläche erkunden.

### Schritt 5: Erste Playlist erstellen (1 Minute)

1. **Playlist-Generator öffnen**:
   - Tab "Playlist" anklicken
   - Preset auswählen (z.B. "Progressive House")

2. **Parameter anpassen** (optional):
   - BPM-Bereich: 120-130 BPM
   - Energie-Verlauf: "Gradueller Aufbau"
   - Stimmung: "Energetisch"

3. **Playlist generieren**:
   - Klick auf "Playlist erstellen" 🎯
   - Automatische Sortierung nach Harmonie
   - Vorschau der generierten Playlist

4. **Export**:
   - Format wählen (M3U für universelle Kompatibilität)
   - "Exportieren" klicken 💾
   - Datei wird im Export-Verzeichnis gespeichert

## 🎯 Erste Schritte Checkliste

- [ ] ✅ Anwendung erfolgreich gestartet
- [ ] 🎵 Mindestens 5 Audio-Dateien hinzugefügt
- [ ] 🔍 Audio-Analyse abgeschlossen
- [ ] 📊 Track-Daten in der Tabelle sichtbar
- [ ] 🎼 Erste Playlist erstellt
- [ ] 💾 Playlist erfolgreich exportiert

## 🎨 Benutzeroberfläche im Überblick

### Hauptfenster-Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Datei] [Bearbeiten] [Tools] [Hilfe]                   │
├─────────────────────────────────────────────────────────┤
│ [📁 Ordner] [🎵 Dateien] [▶️ Analyse] [🎯 Playlist]     │
├─────────────────────────────────────────────────────────┤
│ Tracks │ Playlist │ Browser │ Export │ Einstellungen   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Track-Tabelle mit BPM, Key, Energie, Stimmung        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Status: Bereit │ Cache: 45 Tracks │ 🔊 Preview         │
└─────────────────────────────────────────────────────────┘
```

### Wichtige Bedienelemente

| Element | Funktion | Shortcut |
|---------|----------|----------|
| 📁 Ordner hinzufügen | Kompletten Musikordner analysieren | Ctrl+O |
| 🎵 Dateien hinzufügen | Einzelne Audio-Dateien hinzufügen | Ctrl+F |
| ▶️ Analyse starten | Audio-Analyse für alle Tracks | F5 |
| 🎯 Playlist erstellen | Intelligente Playlist generieren | Ctrl+P |
| 💾 Export | Playlist in verschiedene Formate | Ctrl+E |
| 🔊 Preview | Audio-Vorschau abspielen | Leertaste |

## 🎼 Beispiel-Workflow: Progressive House Set

### Szenario
Sie möchten ein 1-stündiges Progressive House Set für einen Club-Auftritt erstellen.

### Schritt-für-Schritt

1. **Musik vorbereiten**:
   ```
   Ordner: "C:\Music\Progressive House"
   Anzahl Tracks: ~50 Tracks
   Durchschnittliche BPM: 120-130
   ```

2. **Analyse-Parameter**:
   - Qualität: "Hoch" (für präzise BPM-Erkennung)
   - Essentia aktiviert (für bessere Key-Detection)
   - Cache aktiviert (für schnelle Re-Analyse)

3. **Playlist-Konfiguration**:
   ```
   Preset: "Progressive House"
   BPM-Bereich: 120-130 BPM
   Energie-Verlauf: "Gradueller Aufbau"
   Harmonie: "Camelot Wheel" aktiviert
   Länge: 60 Minuten
   ```

4. **Feintuning**:
   - Drag & Drop in der Timeline
   - Manuelle Anpassung der Reihenfolge
   - Preview einzelner Übergänge

5. **Export für Rekordbox**:
   ```
   Format: Rekordbox XML
   Pfad-Anpassung: Relativ
   Cue-Points: Automatisch setzen
   ```

### Erwartetes Ergebnis
- 15-20 Tracks für 60 Minuten
- Harmonische Übergänge (±1 Semitone)
- Gradueller BPM-Anstieg (120 → 130)
- Energie-Aufbau von 60% → 90%

## 🔧 Erste Anpassungen

### Audio-Qualität optimieren

```json
// config/settings.json
{
  "audio_analysis": {
    "quality": "high",
    "use_essentia": true,
    "bpm_accuracy": 0.1,
    "key_confidence": 0.8
  }
}
```

### Performance verbessern

```json
{
  "processing": {
    "max_workers": 4,        // Anzahl CPU-Kerne
    "batch_size": 10,        // Tracks pro Batch
    "cache_enabled": true,   // Cache aktivieren
    "parallel_analysis": true
  }
}
```

### GUI-Anpassungen

```json
{
  "ui": {
    "theme": "dark",
    "auto_preview": true,
    "show_waveforms": true,
    "table_columns": ["title", "artist", "bpm", "key", "energy"]
  }
}
```

## 🎯 Nächste Schritte

Nach dem erfolgreichen Quick Start:

1. **Erweiterte Features erkunden**:
   - [Advanced Features Guide](tutorials/advanced-features.md)
   - [Custom Presets erstellen](tutorials/custom-presets.md)

2. **Rekordbox-Integration**:
   - [Rekordbox Integration Guide](tutorials/rekordbox-integration.md)

3. **Workflow optimieren**:
   - [User Guide](user-guide.md) für detaillierte Funktionen
   - [Best Practices](tutorials/best-practices.md)

## ❓ Häufige Fragen beim Einstieg

**Q: Wie lange dauert die Analyse?**
A: ~3-5 Sekunden pro Track bei hoher Qualität, ~1-2 Sekunden bei Standard-Qualität.

**Q: Welche Dateiformate werden unterstützt?**
A: MP3, WAV, FLAC, AAC, OGG, M4A, AIFF - alle gängigen Audio-Formate.

**Q: Kann ich während der Analyse andere Funktionen nutzen?**
A: Ja, die Analyse läuft im Hintergrund. Sie können bereits analysierte Tracks bearbeiten.

**Q: Wie genau ist die BPM-Erkennung?**
A: Bei hoher Qualität: ±0.1 BPM Genauigkeit. Bei komplexen Tracks kann manuelle Korrektur nötig sein.

**Q: Funktioniert das Tool offline?**
A: Ja, komplett offline. Keine Internetverbindung erforderlich.

## 🆘 Schnelle Hilfe

**Problem**: Anwendung startet nicht
**Lösung**: `python main.py` im Terminal ausführen, Fehlermeldung prüfen

**Problem**: Keine Audio-Dateien erkannt
**Lösung**: Dateiformate prüfen, Pfad-Berechtigung überprüfen

**Problem**: Analyse bleibt hängen
**Lösung**: Anwendung neu starten, kleinere Batches verwenden

**Problem**: Playlist ist leer
**Lösung**: BPM-Bereich erweitern, weniger restriktive Filter verwenden

---

**🎉 Herzlichen Glückwunsch!** Sie haben erfolgreich Ihre erste Playlist erstellt. Erkunden Sie nun die erweiterten Features für professionelle DJ-Sets.

**Weiter zu**: [User Guide](user-guide.md) | [Advanced Features](tutorials