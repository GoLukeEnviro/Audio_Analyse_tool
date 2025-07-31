#!/usr/bin/env python3
"""Demo-Anwendung für die erweiterte Playlist-Engine"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from playlist_engine.generator import PlaylistGenerator
from audio_analysis.energy_score_extractor import EnergyScoreExtractor
from audio_analysis.mood_classifier_enhanced import EnhancedMoodClassifier
from playlist_engine.similarity_engine import SimilarityEngine
from export.rekordbox_exporter import EnhancedExportManager


class PlaylistEngineDemo:
    """Demo-Klasse für die erweiterte Playlist-Engine"""
    
    def __init__(self):
        self.generator = PlaylistGenerator()
        self.export_manager = EnhancedExportManager()
        
        # Demo-Tracks erstellen
        self.demo_tracks = self.create_demo_tracks()
        
        print("🎵 Enhanced Playlist Engine Demo")
        print("=" * 50)
    
    def create_demo_tracks(self) -> List[Dict[str, Any]]:
        """Erstellt Demo-Tracks für die Demonstration"""
        demo_tracks = [
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
                'year': 2023,
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
                'year': 2023,
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
                'year': 2023,
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
                'year': 2023,
                'spectral_centroid': 2800,
                'onset_density': 1.5,
                'harmonic_ratio': 0.6
            },
            {
                'id': 5,
                'title': 'Sunset Vibes',
                'artist': 'Chill Producer',
                'album': 'Golden Hour',
                'genre': 'Chillout',
                'bpm': 95,
                'key': 'G major',
                'duration': 280,
                'energy_score': 4.2,
                'mood_label': 'Uplifting',
                'file_path': '/music/chill/sunset_vibes.mp3',
                'year': 2023,
                'spectral_centroid': 2100,
                'onset_density': 0.5,
                'harmonic_ratio': 0.85
            }
        ]
        
        return demo_tracks
    
    def demo_wizard_flow(self):
        """Demonstriert den Wizard-Flow"""
        print("\n🧙‍♂️ Playlist Wizard Demo")
        print("-" * 30)
        
        # Schritt 1: Wizard starten
        wizard_state = self.generator.start_wizard()
        print(f"✅ Wizard gestartet: Schritt {wizard_state['current_step']}")
        
        # Schritt 2: Mood Presets anzeigen
        mood_presets = self.generator.get_mood_presets()
        print(f"\n📋 Verfügbare Mood Presets: {len(mood_presets)}")
        
        for preset_name, preset_data in list(mood_presets.items())[:3]:
            print(f"  {preset_data.get('emoji', '🎵')} {preset_name}: {preset_data.get('description', '')}")
        
        # Wähle "Progressive Journey" Preset
        selected_preset = "Progressive Journey"
        wizard_state = self.generator.wizard_step_2(selected_preset)
        print(f"\n✅ Preset gewählt: {selected_preset}")
        
        # Schritt 3: Energy Curve anpassen
        energy_settings = {
            'duration': 60,  # 60 Minuten
            'curve_type': 'progressive',
            'custom_points': [(0, 5), (30, 8), (45, 9), (60, 7)]
        }
        
        wizard_state = self.generator.wizard_step_3(energy_settings)
        print(f"✅ Energy Curve konfiguriert: {energy_settings['curve_type']}")
        
        # Schritt 4: Key Preferences
        key_preferences = {
            'preferred_keys': ['A minor', 'E minor', 'F# minor'],
            'transition_style': 'harmonic',
            'allow_key_jumps': False
        }
        
        wizard_state = self.generator.wizard_step_4(key_preferences)
        print(f"✅ Key Preferences gesetzt: {len(key_preferences['preferred_keys'])} bevorzugte Tonarten")
        
        return wizard_state
    
    def demo_playlist_generation(self, wizard_state: Dict[str, Any]):
        """Demonstriert die Playlist-Generierung"""
        print("\n🎼 Playlist Generierung")
        print("-" * 25)
        
        # Generiere Playlist aus Wizard-State
        playlist_result = self.generator.generate_from_wizard(
            wizard_state, 
            self.demo_tracks
        )
        
        if playlist_result:
            playlist = playlist_result['playlist']
            metadata = playlist_result['metadata']
            
            print(f"✅ Playlist generiert: {len(playlist)} Tracks")
            print(f"📊 Preset: {metadata.get('preset_name', 'Unknown')}")
            print(f"⏱️  Gesamtdauer: {sum(t.get('duration', 0) for t in playlist) / 60:.1f} Minuten")
            
            # Zeige Playlist-Details
            print("\n🎵 Playlist Tracks:")
            for i, track in enumerate(playlist, 1):
                energy = track.get('energy_score', 0)
                bpm = track.get('bpm', 0)
                key = track.get('key', 'Unknown')
                
                print(f"  {i:2d}. {track['artist']} - {track['title']}")
                print(f"      🔥 Energy: {energy:.1f} | 🥁 BPM: {bpm} | 🎹 Key: {key}")
                
                # Transition-Info
                if 'transition_to_next' in track:
                    transition = track['transition_to_next']
                    compatibility = transition.get('compatibility_score', 0)
                    print(f"      🔄 Transition Score: {compatibility:.2f}")
            
            return playlist_result
        else:
            print("❌ Playlist-Generierung fehlgeschlagen")
            return None
    
    def demo_smart_suggestions(self):
        """Demonstriert Smart Suggestions"""
        print("\n🤖 Smart Suggestions Demo")
        print("-" * 28)
        
        # Wähle einen Track als Basis
        base_track = self.demo_tracks[1]  # "Electric Euphoria"
        print(f"🎯 Basis-Track: {base_track['artist']} - {base_track['title']}")
        print(f"   Energy: {base_track['energy_score']:.1f} | BPM: {base_track['bpm']} | Key: {base_track['key']}")
        
        # Smart Suggestions
        smart_suggestions = self.generator.get_smart_suggestions(
            base_track, 
            self.demo_tracks, 
            count=3
        )
        
        print(f"\n💡 Smart Suggestions ({len(smart_suggestions)} gefunden):")
        for i, suggestion in enumerate(smart_suggestions, 1):
            track = suggestion['track']
            score = suggestion['similarity_score']
            reasons = suggestion['reasons']
            
            print(f"  {i}. {track['artist']} - {track['title']} (Score: {score:.2f})")
            print(f"     Gründe: {', '.join(reasons)}")
        
        # Surprise Suggestions
        surprise_suggestions = self.generator.get_surprise_suggestions(
            base_track, 
            self.demo_tracks, 
            count=2
        )
        
        print(f"\n🎲 Surprise Suggestions ({len(surprise_suggestions)} gefunden):")
        for i, suggestion in enumerate(surprise_suggestions, 1):
            track = suggestion['track']
            surprise_factor = suggestion['surprise_factor']
            
            print(f"  {i}. {track['artist']} - {track['title']} (Surprise: {surprise_factor:.2f})")
    
    def demo_export_functionality(self, playlist_data: Dict[str, Any]):
        """Demonstriert Export-Funktionalität"""
        print("\n📤 Export Demo")
        print("-" * 15)
        
        # Erstelle Ausgabe-Verzeichnis
        output_dir = Path("demo_exports")
        output_dir.mkdir(exist_ok=True)
        
        # Exportiere in verschiedenen Formaten
        export_results = self.export_manager.export_playlist(
            playlist_data,
            str(output_dir),
            formats=['rekordbox', 'm3u', 'json']
        )
        
        print("✅ Export-Ergebnisse:")
        for format_name, file_path in export_results.items():
            if file_path:
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                print(f"  📁 {format_name.upper()}: {file_path} ({file_size} bytes)")
            else:
                print(f"  ❌ {format_name.upper()}: Export fehlgeschlagen")
        
        return export_results
    
    def demo_energy_analysis(self):
        """Demonstriert Energy Score Analyse"""
        print("\n⚡ Energy Score Analyse")
        print("-" * 25)
        
        # Analysiere Energy Scores der Demo-Tracks
        energy_scores = [track['energy_score'] for track in self.demo_tracks]
        
        print(f"📊 Energy Score Verteilung:")
        print(f"   Min: {min(energy_scores):.1f}")
        print(f"   Max: {max(energy_scores):.1f}")
        print(f"   Durchschnitt: {sum(energy_scores)/len(energy_scores):.1f}")
        
        # Kategorisiere Tracks nach Energy
        low_energy = [t for t in self.demo_tracks if t['energy_score'] < 4]
        mid_energy = [t for t in self.demo_tracks if 4 <= t['energy_score'] < 7]
        high_energy = [t for t in self.demo_tracks if t['energy_score'] >= 7]
        
        print(f"\n🔥 Energy Kategorien:")
        print(f"   🟢 Low Energy (< 4): {len(low_energy)} Tracks")
        print(f"   🟡 Mid Energy (4-7): {len(mid_energy)} Tracks")
        print(f"   🔴 High Energy (≥ 7): {len(high_energy)} Tracks")
    
    def demo_camelot_wheel(self):
        """Demonstriert Camelot Wheel Funktionalität"""
        print("\n🎹 Camelot Wheel Demo")
        print("-" * 22)
        
        # Hole Camelot Wheel Daten
        camelot_data = self.generator.get_camelot_wheel_data()
        
        print(f"🎼 Camelot Wheel Struktur:")
        print(f"   Verfügbare Positionen: {len(camelot_data['positions'])}")
        
        # Zeige einige Beispiel-Positionen
        example_positions = list(camelot_data['positions'].items())[:6]
        for position, key_info in example_positions:
            major_key = key_info['major']
            minor_key = key_info['minor']
            print(f"   {position}: {major_key} / {minor_key}")
        
        # Demonstriere kompatible Übergänge
        print(f"\n🔄 Kompatible Übergänge (Beispiel für 8A):")
        compatible = camelot_data['compatibility_rules']['8A']
        print(f"   Von 8A kompatibel zu: {', '.join(compatible)}")
    
    def run_full_demo(self):
        """Führt die komplette Demo aus"""
        try:
            # 1. Energy Analyse
            self.demo_energy_analysis()
            
            # 2. Camelot Wheel
            self.demo_camelot_wheel()
            
            # 3. Wizard Flow
            wizard_state = self.demo_wizard_flow()
            
            # 4. Playlist Generierung
            playlist_data = self.demo_playlist_generation(wizard_state)
            
            if playlist_data:
                # 5. Smart Suggestions
                self.demo_smart_suggestions()
                
                # 6. Export
                self.demo_export_functionality(playlist_data)
            
            print("\n🎉 Demo erfolgreich abgeschlossen!")
            print("\n📁 Generierte Dateien finden Sie im 'demo_exports' Verzeichnis.")
            
        except Exception as e:
            print(f"\n❌ Demo-Fehler: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Hauptfunktion"""
    print("Starte Enhanced Playlist Engine Demo...\n")
    
    demo = PlaylistEngineDemo()
    demo.run_full_demo()
    
    print("\n" + "=" * 50)
    print("Demo beendet. Vielen Dank!")


if __name__ == "__main__":
    main()