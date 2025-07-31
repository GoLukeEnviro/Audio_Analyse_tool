#!/usr/bin/env python3
"""Test-Anwendung für die erweiterte Playlist-Engine"""

import sys
import os
from pathlib import Path

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit
    from PySide6.QtCore import Qt
    
    from playlist_engine.generator import PlaylistGenerator
    from export.rekordbox_exporter import EnhancedExportManager
    
    class EnhancedPlaylistTestApp(QMainWindow):
        """Test-Anwendung für die erweiterte Playlist-Engine"""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Enhanced Playlist Engine - Test")
            self.setGeometry(100, 100, 800, 600)
            
            # Initialisiere Komponenten
            self.generator = PlaylistGenerator()
            self.export_manager = EnhancedExportManager()
            
            self.setup_ui()
            self.create_demo_data()
        
        def setup_ui(self):
            """Erstellt die Benutzeroberfläche"""
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # Titel
            title = QLabel("🎵 Enhanced Playlist Engine Test")
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
            layout.addWidget(title)
            
            # Info-Text
            info = QLabel("Diese Test-Anwendung demonstriert die erweiterte Playlist-Engine mit:\n" +
                         "• EnergyScore-Algorithmus\n" +
                         "• Smart Suggestions Engine\n" +
                         "• Camelot Wheel Integration\n" +
                         "• Erweiterte Export-Funktionen")
            info.setAlignment(Qt.AlignCenter)
            info.setStyleSheet("margin: 10px; padding: 20px; background-color: #f0f0f0; border-radius: 10px;")
            layout.addWidget(info)
            
            # Test-Buttons
            self.test_wizard_btn = QPushButton("🧙‍♂️ Teste Playlist Wizard")
            self.test_wizard_btn.clicked.connect(self.test_wizard)
            layout.addWidget(self.test_wizard_btn)
            
            self.test_suggestions_btn = QPushButton("🤖 Teste Smart Suggestions")
            self.test_suggestions_btn.clicked.connect(self.test_suggestions)
            layout.addWidget(self.test_suggestions_btn)
            
            self.test_export_btn = QPushButton("📤 Teste Export-Funktionen")
            self.test_export_btn.clicked.connect(self.test_export)
            layout.addWidget(self.test_export_btn)
            
            # Ausgabe-Bereich
            self.output = QTextEdit()
            self.output.setReadOnly(True)
            self.output.setStyleSheet("font-family: monospace; background-color: #2b2b2b; color: #ffffff;")
            layout.addWidget(self.output)
            
            # Status
            self.log("✅ Enhanced Playlist Engine erfolgreich initialisiert!")
        
        def create_demo_data(self):
            """Erstellt Demo-Daten"""
            self.demo_tracks = [
                {
                    'id': 1,
                    'title': 'Midnight Drive',
                    'artist': 'Synthwave Artist',
                    'album': 'Neon Dreams',
                    'genre': 'Synthwave',
                    'bpm': 128,
                    'key': 'A minor',
                    'duration': 240,
                    'energy_score': 7.5,
                    'mood_label': 'Dark',
                    'file_path': '/music/synthwave/midnight_drive.mp3',
                    'spectral_centroid': 2500,
                    'onset_density': 0.8,
                    'harmonic_ratio': 0.7
                },
                {
                    'id': 2,
                    'title': 'Electric Euphoria',
                    'artist': 'EDM Producer',
                    'album': 'Festival Anthems',
                    'genre': 'Progressive House',
                    'bpm': 132,
                    'key': 'E minor',
                    'duration': 360,
                    'energy_score': 9.2,
                    'mood_label': 'Euphoric',
                    'file_path': '/music/edm/electric_euphoria.mp3',
                    'spectral_centroid': 3200,
                    'onset_density': 1.2,
                    'harmonic_ratio': 0.8
                },
                {
                    'id': 3,
                    'title': 'Deep Reflection',
                    'artist': 'Ambient Collective',
                    'album': 'Mindscapes',
                    'genre': 'Ambient',
                    'bpm': 85,
                    'key': 'C major',
                    'duration': 420,
                    'energy_score': 2.8,
                    'mood_label': 'Chill',
                    'file_path': '/music/ambient/deep_reflection.mp3',
                    'spectral_centroid': 1800,
                    'onset_density': 0.3,
                    'harmonic_ratio': 0.9
                },
                {
                    'id': 4,
                    'title': 'Driving Force',
                    'artist': 'Techno Master',
                    'album': 'Underground Sessions',
                    'genre': 'Techno',
                    'bpm': 140,
                    'key': 'F# minor',
                    'duration': 300,
                    'energy_score': 8.7,
                    'mood_label': 'Driving',
                    'file_path': '/music/techno/driving_force.mp3',
                    'spectral_centroid': 2800,
                    'onset_density': 1.5,
                    'harmonic_ratio': 0.6
                }
            ]
            
            self.log(f"📊 Demo-Daten erstellt: {len(self.demo_tracks)} Tracks")
        
        def test_wizard(self):
            """Testet den Playlist Wizard"""
            self.log("\n🧙‍♂️ Teste Playlist Wizard...")
            
            try:
                # Starte Wizard
                wizard_state = self.generator.start_wizard()
                self.log(f"✅ Wizard gestartet: Schritt {wizard_state['current_step']}")
                
                # Hole Mood Presets
                mood_presets = self.generator.get_mood_presets()
                self.log(f"📋 Verfügbare Mood Presets: {len(mood_presets)}")
                
                # Zeige erste 3 Presets
                for i, (name, data) in enumerate(list(mood_presets.items())[:3]):
                    emoji = data.get('emoji', '🎵')
                    desc = data.get('description', '')[:50] + '...' if len(data.get('description', '')) > 50 else data.get('description', '')
                    self.log(f"  {emoji} {name}: {desc}")
                
                # Wähle Preset
                selected_preset = "Progressive Journey"
                wizard_state = self.generator.wizard_step_2(selected_preset)
                self.log(f"✅ Preset gewählt: {selected_preset}")
                
                # Konfiguriere Energy Curve
                energy_settings = {
                    'duration': 60,
                    'curve_type': 'progressive',
                    'custom_points': [(0, 5), (30, 8), (45, 9), (60, 7)]
                }
                wizard_state = self.generator.wizard_step_3(energy_settings)
                self.log(f"✅ Energy Curve konfiguriert: {energy_settings['curve_type']}")
                
                # Generiere Playlist
                playlist_result = self.generator.generate_from_wizard(wizard_state, self.demo_tracks)
                
                if playlist_result:
                    playlist = playlist_result['playlist']
                    self.log(f"🎼 Playlist generiert: {len(playlist)} Tracks")
                    
                    for i, track in enumerate(playlist, 1):
                        energy = track.get('energy_score', 0)
                        bpm = track.get('bpm', 0)
                        self.log(f"  {i}. {track['artist']} - {track['title']} (Energy: {energy:.1f}, BPM: {bpm})")
                else:
                    self.log("❌ Playlist-Generierung fehlgeschlagen")
                
            except Exception as e:
                self.log(f"❌ Wizard-Test Fehler: {e}")
        
        def test_suggestions(self):
            """Testet Smart Suggestions"""
            self.log("\n🤖 Teste Smart Suggestions...")
            
            try:
                # Wähle Basis-Track
                base_track = self.demo_tracks[1]  # "Electric Euphoria"
                self.log(f"🎯 Basis-Track: {base_track['artist']} - {base_track['title']}")
                self.log(f"   Energy: {base_track['energy_score']:.1f} | BPM: {base_track['bpm']} | Key: {base_track['key']}")
                
                # Smart Suggestions
                smart_suggestions = self.generator.get_smart_suggestions(
                    base_track, 
                    self.demo_tracks, 
                    count=2
                )
                
                self.log(f"\n💡 Smart Suggestions ({len(smart_suggestions)} gefunden):")
                for i, suggestion in enumerate(smart_suggestions, 1):
                    track = suggestion['track']
                    score = suggestion['similarity_score']
                    reasons = suggestion['reasons']
                    
                    self.log(f"  {i}. {track['artist']} - {track['title']} (Score: {score:.2f})")
                    self.log(f"     Gründe: {', '.join(reasons)}")
                
                # Surprise Suggestions
                surprise_suggestions = self.generator.get_surprise_suggestions(
                    base_track, 
                    self.demo_tracks, 
                    count=1
                )
                
                self.log(f"\n🎲 Surprise Suggestions ({len(surprise_suggestions)} gefunden):")
                for i, suggestion in enumerate(surprise_suggestions, 1):
                    track = suggestion['track']
                    surprise_factor = suggestion['surprise_factor']
                    
                    self.log(f"  {i}. {track['artist']} - {track['title']} (Surprise: {surprise_factor:.2f})")
                
            except Exception as e:
                self.log(f"❌ Suggestions-Test Fehler: {e}")
        
        def test_export(self):
            """Testet Export-Funktionen"""
            self.log("\n📤 Teste Export-Funktionen...")
            
            try:
                # Erstelle Test-Playlist
                playlist_data = {
                    'playlist': self.demo_tracks[:3],
                    'metadata': {
                        'preset_name': 'Test_Playlist',
                        'created_at': '2025-01-31',
                        'total_duration': sum(t.get('duration', 0) for t in self.demo_tracks[:3])
                    }
                }
                
                # Erstelle Ausgabe-Verzeichnis
                output_dir = Path("test_exports")
                output_dir.mkdir(exist_ok=True)
                
                # Exportiere
                export_results = self.export_manager.export_playlist(
                    playlist_data,
                    str(output_dir),
                    formats=['rekordbox', 'm3u', 'json']
                )
                
                self.log("✅ Export-Ergebnisse:")
                for format_name, file_path in export_results.items():
                    if file_path and os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        self.log(f"  📁 {format_name.upper()}: {file_path} ({file_size} bytes)")
                    else:
                        self.log(f"  ❌ {format_name.upper()}: Export fehlgeschlagen")
                
            except Exception as e:
                self.log(f"❌ Export-Test Fehler: {e}")
        
        def log(self, message):
            """Fügt Nachricht zur Ausgabe hinzu"""
            self.output.append(message)
            self.output.ensureCursorVisible()
    
    def main():
        """Hauptfunktion"""
        app = QApplication(sys.argv)
        
        # Setze Anwendungs-Stil
        app.setStyle('Fusion')
        
        window = EnhancedPlaylistTestApp()
        window.show()
        
        sys.exit(app.exec())
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import-Fehler: {e}")
    print("Bitte stellen Sie sicher, dass alle Abhängigkeiten installiert sind.")
    print("Führen Sie 'pip install -r requirements.txt' aus.")
except Exception as e:
    print(f"Unerwarteter Fehler: {e}")
    import traceback
    traceback.print_exc()