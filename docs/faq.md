# Häufig gestellte Fragen (FAQ)

Antworten auf die häufigsten Fragen zum DJ Audio-Analyse-Tool Pro v2.0.

## 📋 Inhaltsverzeichnis

1. [Installation und Setup](#installation-und-setup)
2. [Audio-Analyse](#audio-analyse)
3. [Playlist-Erstellung](#playlist-erstellung)
4. [Export und Integration](#export-und-integration)
5. [Performance und Optimierung](#performance-und-optimierung)
6. [Fehlerbehebung](#fehlerbehebung)
7. [Erweiterte Features](#erweiterte-features)
8. [Kompatibilität](#kompatibilität)

## 🚀 Installation und Setup

### Q: Welche Python-Version wird benötigt?
**A**: Python 3.8 oder höher wird empfohlen. Das Tool wurde mit Python 3.9-3.11 getestet. Python 3.12 wird experimentell unterstützt.

### Q: Warum schlägt die Installation von Essentia fehl?
**A**: Essentia kann auf Windows problematisch sein. Versuchen Sie:

1. **Conda-Installation**:
   ```bash
   conda install -c mtg essentia
   ```

2. **Alternative ohne TensorFlow**:
   ```bash
   pip install essentia
   ```

3. **Fallback**: Das Tool funktioniert auch nur mit librosa, wenn Essentia nicht verfügbar ist.

### Q: Kann ich das Tool ohne Administrator-Rechte installieren?
**A**: Ja, verwenden Sie eine virtuelle Umgebung:
```bash
python -m venv dj_tool_env
dj_tool_env\Scripts\activate
pip install -r requirements.txt
```

### Q: Wie viel Speicherplatz wird benötigt?
**A**: 
- **Basis-Installation**: ~500 MB
- **Mit allen Abhängigkeiten**: ~1.5 GB
- **Cache für 1000 Tracks**: ~100 MB
- **Empfohlen**: 5 GB freier Speicherplatz

### Q: Funktioniert das Tool auf Mac/Linux?
**A**: Experimentell ja, aber primär für Windows entwickelt. Bekannte Einschränkungen:
- GUI-Layout kann abweichen
- Einige Shortcuts funktionieren anders
- Rekordbox-Integration nur auf Windows

## 🎵 Audio-Analyse

### Q: Welche Dateiformate werden unterstützt?
**A**: 
- **Vollständig unterstützt**: MP3, WAV, FLAC, AAC, M4A, OGG, AIFF
- **Experimentell**: WMA, APE
- **Nicht unterstützt**: DRM-geschützte Dateien, beschädigte Dateien

### Q: Wie genau ist die BPM-Erkennung?
**A**: 
- **Standard-Qualität**: ±0.5 BPM (95% Genauigkeit)
- **Hohe Qualität**: ±0.1 BPM (98% Genauigkeit)
- **Problematisch**: Live-Aufnahmen, variable BPM, sehr langsame/schnelle Tracks

### Q: Warum wird die falsche Tonart erkannt?
**A**: Häufige Ursachen:
- **Atonal/Noise-Tracks**: Keine klare Tonart
- **Modulationen**: Tonart wechselt im Track
- **Niedrige Qualität**: Komprimierte/verzerrte Dateien
- **Lösung**: Manuelle Korrektur oder höhere Analyse-Qualität

### Q: Wie lange dauert die Analyse?
**A**: 
- **Pro Track**: 2-5 Sekunden (abhängig von Qualität und Hardware)
- **100 Tracks**: 3-8 Minuten
- **1000 Tracks**: 30-60 Minuten
- **Tipp**: Über Nacht laufen lassen für große Bibliotheken

### Q: Was bedeuten die Konfidenz-Werte?
**A**: 
- **>90%**: Sehr zuverlässig, keine Korrektur nötig
- **70-90%**: Meist korrekt, gelegentliche Überprüfung
- **50-70%**: Unsicher, manuelle Überprüfung empfohlen
- **<50%**: Wahrscheinlich falsch, manuelle Korrektur nötig

### Q: Kann ich die Analyse-Parameter anpassen?
**A**: Ja, in `config/settings.json`:
```json
{
  "audio_analysis": {
    "bpm_range": [80, 180],
    "key_confidence_threshold": 0.8,
    "energy_smoothing": 0.1
  }
}
```

### Q: Warum ist die Energie-Berechnung ungenau?
**A**: Energie basiert auf mehreren Faktoren:
- **RMS Energy**: Durchschnittliche Lautstärke
- **Spectral Centroid**: Helligkeit
- **Onset Density**: Beat-Dichte

Bei stark komprimierten Tracks kann die Berechnung ungenau sein.

## 🎼 Playlist-Erstellung

### Q: Wie funktioniert das Camelot Wheel?
**A**: Das Camelot Wheel ordnet Tonarten in einem Kreis an:
- **Identische Zahlen**: Perfekte Harmonie (8A → 8A)
- **±1 Position**: Gute Übergänge (8A → 7A oder 9A)
- **A ↔ B**: Relative Dur/Moll (8A ↔ 8B)
- **Gegenüber**: Vermeiden (8A → 2A)

### Q: Warum sind meine Playlists zu kurz/lang?
**A**: 
- **Zu kurz**: BPM-Bereich zu eng, zu strenge Harmonie-Regeln
- **Zu lang**: Zu viele verfügbare Tracks, lockere Regeln
- **Lösung**: Parameter in Presets anpassen

### Q: Kann ich eigene Presets erstellen?
**A**: Ja, über die GUI oder manuell:
```json
{
  "name": "Mein Preset",
  "bpm_range": [120, 130],
  "energy_curve": "gradual_buildup",
  "harmony_strictness": 0.8,
  "rules": {
    "max_bpm_jump": 3,
    "avoid_back_to_back_same_artist": true
  }
}
```

### Q: Was ist der "Surprise Me" Modus?
**A**: Kontrolliert die Vorhersagbarkeit:
- **0%**: Perfekte harmonische Übergänge
- **50%**: Ausgewogen zwischen Harmonie und Überraschung
- **100%**: Völlig chaotische, unvorhersagbare Kombinationen

### Q: Warum ignoriert die Playlist meine Filter?
**A**: Mögliche Ursachen:
- **Zu wenige Tracks**: Nicht genug Tracks erfüllen die Kriterien
- **Widersprüchliche Regeln**: Unmögliche Kombinationen
- **Cache-Problem**: Veraltete Daten
- **Lösung**: Filter lockern oder mehr Tracks hinzufügen

### Q: Kann ich Playlists manuell bearbeiten?
**A**: Ja:
- **Drag & Drop**: Tracks in der Timeline verschieben
- **Entfernen**: Tracks aus der Playlist löschen
- **Hinzufügen**: Neue Tracks einfügen
- **Speichern**: Als neues Preset speichern

## 💾 Export und Integration

### Q: Welche Export-Formate werden unterstützt?
**A**: 
- **Playlists**: M3U, M3U8, PLS, XSPF
- **DJ-Software**: Rekordbox XML, Serato Crates, Traktor NML
- **Daten**: JSON, CSV, TXT
- **Reports**: HTML, PDF (geplant)

### Q: Funktioniert die Rekordbox-Integration?
**A**: Ja, aber mit Einschränkungen:
- **Unterstützt**: Rekordbox 5.x und 6.x
- **Features**: Playlists, BPM, Key, Cue-Points
- **Nicht unterstützt**: Waveform-Daten, Hot Cues
- **Wichtig**: Backup der collection.xml wird automatisch erstellt

### Q: Warum funktioniert der Rekordbox-Export nicht?
**A**: Häufige Probleme:
- **Rekordbox läuft**: Schließen Sie Rekordbox vor dem Export
- **Falsche Pfade**: Überprüfen Sie die Rekordbox-Installation
- **Berechtigungen**: Administratorrechte erforderlich
- **Korrupte XML**: Backup wiederherstellen

### Q: Kann ich relative Pfade verwenden?
**A**: Ja, empfohlen für portable Playlists:
```json
{
  "export": {
    "relative_paths": true,
    "base_path": "./Music"
  }
}
```

### Q: Wie exportiere ich nur bestimmte Metadaten?
**A**: Konfigurieren Sie den Export:
```json
{
  "export_fields": [
    "title", "artist", "bpm", "key", "file_path"
  ],
  "include_analysis": false
}
```

## ⚡ Performance und Optimierung

### Q: Das Tool ist sehr langsam. Was kann ich tun?
**A**: Optimierungsschritte:

1. **Hardware-Upgrade**:
   - Mehr RAM (8 GB+)
   - SSD statt HDD
   - Bessere CPU

2. **Software-Optimierung**:
   ```json
   {
     "performance": {
       "max_workers": 4,
       "batch_size": 5,
       "quality": "medium"
     }
   }
   ```

3. **Cache aktivieren**:
   ```json
   {
     "cache": {
       "enabled": true,
       "max_size_gb": 2
     }
   }
   ```

### Q: Wie viel RAM wird benötigt?
**A**: 
- **Minimum**: 4 GB (für kleine Bibliotheken)
- **Empfohlen**: 8 GB (für 1000+ Tracks)
- **Optimal**: 16 GB+ (für große Bibliotheken und Batch-Processing)

### Q: Kann ich die Analyse im Hintergrund laufen lassen?
**A**: Ja:
- **Automatisch**: Neue Tracks werden automatisch analysiert
- **Batch-Modus**: Große Mengen über Nacht
- **Priorität**: Niedrige CPU-Priorität für Hintergrund-Analyse

### Q: Wie groß wird der Cache?
**A**: 
- **Pro Track**: ~100 KB Cache-Daten
- **1000 Tracks**: ~100 MB
- **10000 Tracks**: ~1 GB
- **Bereinigung**: Automatisch nach 30 Tagen

## 🐛 Fehlerbehebung

### Q: Die Anwendung startet nicht. Was tun?
**A**: Debugging-Schritte:

1. **Terminal-Start**:
   ```bash
   python main.py
   ```
   Fehlermeldungen beachten

2. **Abhängigkeiten prüfen**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Log-Dateien prüfen**:
   ```
   logs/dj_tool.log
   logs/error.log
   ```

4. **Neuinstallation**:
   ```bash
   pip uninstall -r requirements.txt
   pip install -r requirements.txt
   ```

### Q: "ModuleNotFoundError" beim Start
**A**: 
- **Ursache**: Fehlende Python-Pakete
- **Lösung**: `pip install [paket_name]`
- **Vollständig**: `pip install -r requirements.txt`

### Q: GUI zeigt nur schwarzen Bildschirm
**A**: 
- **Windows**: Grafiktreiber aktualisieren
- **Skalierung**: Windows-Skalierung auf 100% setzen
- **Alternative**: `python main.py --no-gpu`

### Q: Audio-Dateien werden nicht erkannt
**A**: 
- **Pfad prüfen**: Keine Sonderzeichen, keine Leerzeichen am Ende
- **Berechtigungen**: Lesezugriff auf Dateien
- **Format**: Unterstützte Dateiformate verwenden
- **Größe**: Dateien nicht größer als 100 MB

### Q: Analyse bleibt bei bestimmten Tracks hängen
**A**: 
- **Korrupte Dateien**: Track überspringen oder reparieren
- **Timeout**: Längere Timeout-Werte setzen
- **Einzelanalyse**: Track einzeln analysieren
- **Format-Konvertierung**: In anderes Format konvertieren

### Q: Export schlägt fehl
**A**: 
- **Berechtigungen**: Schreibzugriff auf Zielordner
- **Speicherplatz**: Genügend freier Speicher
- **Pfadlänge**: Windows-Pfadlängen-Limit (260 Zeichen)
- **Sonderzeichen**: Keine problematischen Zeichen in Dateinamen

## 🔧 Erweiterte Features

### Q: Wie funktioniert der Machine Learning Mood Classifier?
**A**: 
- **Hybrid-Ansatz**: Kombiniert Regeln und ML
- **Training**: Auf 10.000+ gelabelten Tracks trainiert
- **Features**: MFCC, Chroma, Spectral Features
- **Aktualisierung**: Modell wird regelmäßig verbessert

### Q: Kann ich eigene Stimmungs-Kategorien definieren?
**A**: Ja, in `src/core/mood_classifier/mood_rules.py`:
```python
CUSTOM_MOODS = {
    'chill': {
        'energy_range': [0, 40],
        'bpm_range': [60, 100],
        'mode': 'minor'
    }
}
```

### Q: Was ist Beam Search?
**A**: 
- **Algorithmus**: Sucht optimale Playlist-Pfade
- **Beam Width**: Anzahl paralleler Pfade (Standard: 5)
- **Lookahead**: Vorausschau-Tiefe (Standard: 3)
- **Vorteil**: Bessere Übergänge als greedy Algorithmen

### Q: Wie funktioniert die k-NN Similarity Engine?
**A**: 
- **Features**: 8-dimensionaler Feature-Vektor
- **Distanz**: Euklidische Distanz (konfigurierbar)
- **k-Wert**: Anzahl ähnlicher Tracks (Standard: 5)
- **Gewichtung**: Features können gewichtet werden

### Q: Kann ich das Tool über die Kommandozeile verwenden?
**A**: Ja, CLI-Interface verfügbar:
```bash
# Einzelne Datei analysieren
python -m src.cli analyze track.mp3

# Playlist erstellen
python -m src.cli playlist --preset progressive --output playlist.m3u

# Batch-Export
python -m src.cli export --format rekordbox --input tracks.json
```

## 🔄 Kompatibilität

### Q: Welche DJ-Software wird unterstützt?
**A**: 
- **Vollständig**: Rekordbox 5.x/6.x
- **Experimentell**: Serato DJ, Traktor Pro
- **Basis**: Alle Software mit M3U-Support
- **Geplant**: Virtual DJ, djay Pro

### Q: Funktioniert das Tool mit Streaming-Diensten?
**A**: Nein, nur lokale Dateien werden unterstützt. Streaming-APIs sind nicht integriert.

### Q: Kann ich das Tool mit anderen Audio-Tools kombinieren?
**A**: Ja:
- **Mixed In Key**: Import von Key-Daten
- **Beatport**: Metadaten-Import
- **MusicBrainz**: Automatische Metadaten-Ergänzung
- **Last.fm**: Scrobbling-Integration (geplant)

### Q: Gibt es eine mobile Version?
**A**: Nein, das Tool ist für Desktop-Nutzung optimiert. Mobile Version ist nicht geplant.

### Q: Kann ich das Tool auf einem Server betreiben?
**A**: Experimentell möglich:
- **Headless-Modus**: Ohne GUI
- **Web-Interface**: Über Browser bedienbar
- **API**: REST-API für externe Integration
- **Docker**: Container-Deployment möglich

## 📊 Daten und Backup

### Q: Wo werden meine Daten gespeichert?
**A**: 
- **Cache**: `cache/tracks_cache.json`
- **Einstellungen**: `config/settings.json`
- **Presets**: `presets/*.json`
- **Logs**: `logs/*.log`
- **Exports**: `exports/` (konfigurierbar)

### Q: Wie erstelle ich ein Backup?
**A**: 
1. **Manuell**: Kopieren Sie die Ordner `cache`, `config`, `presets`
2. **Automatisch**: Tools → Backup erstellen
3. **Export**: Alle Daten als JSON exportieren

### Q: Kann ich Daten zwischen Computern synchronisieren?
**A**: 
- **Cache**: Übertragbar, aber pfadabhängig
- **Presets**: Vollständig übertragbar
- **Einstellungen**: Meist übertragbar
- **Tipp**: Relative Pfade verwenden

### Q: Wie importiere ich Daten aus anderen Tools?
**A**: 
- **Mixed In Key**: CSV-Import
- **Rekordbox**: XML-Import
- **iTunes**: XML-Playlist-Import
- **Serato**: Crate-Import (experimentell)

## 🆘 Support und Community

### Q: Wo finde ich weitere Hilfe?
**A**: 
1. **Dokumentation**: Vollständige Docs im `docs/` Ordner
2. **GitHub Issues**: Bug-Reports und Feature-Requests
3. **Community**: Discord-Server (Link im Repository)
4. **Email-Support**: support@dj-audio-tool.com

### Q: Wie melde ich Bugs?
**A**: 
1. **GitHub Issue** erstellen
2. **Log-Dateien** anhängen
3. **Schritte zur Reproduktion** beschreiben
4. **System-Informationen** angeben

### Q: Kann ich Features vorschlagen?
**A**: Ja:
- **GitHub Issues**: Feature-Request-Template verwenden
- **Community-Voting**: Beliebte Features werden priorisiert
- **Pull Requests**: Eigene Implementierungen willkommen

### Q: Gibt es Tutorials oder Videos?
**A**: 
- **YouTube-Kanal**: DJ Audio Tool Tutorials
- **Wiki**: Detaillierte Anleitungen
- **Blog**: Best Practices und Tipps
- **Webinare**: Monatliche Live-Sessions

### Q: Ist das Tool kostenlos?
**A**: 
- **Open Source**: Vollständig kostenlos
- **MIT-Lizenz**: Kommerzielle Nutzung erlaubt
- **Spenden**: Freiwillige Unterstützung willkommen
- **Pro-Features**: Alle Features kostenlos verfügbar

---

**💡 Tipp**: Wenn Ihre Frage hier nicht beantwortet wird, schauen Sie in die [Troubleshooting-Anleitung](troubleshooting.md) oder erstellen Sie ein Issue im GitHub-Repository.

**📚 Weitere Ressourcen**:
- [User Guide](user-guide.md) - Detaillierte Bedienungsanleitung
- [Installation Guide](installation.md) - Schritt-für-Schritt Installation
- [API Reference](api/README.md) - Entwickler-Dokumentation
- [Troubleshooting](troubleshooting.md) - Erweiterte Fehlerbehebung