#!/usr/bin/env python3
"""Web-Demo für die erweiterte Playlist-Engine"""

import sys
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import json

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from playlist_engine.generator import PlaylistGenerator
    from export.rekordbox_exporter import EnhancedExportManager
except ImportError as e:
    print(f"Import-Fehler: {e}")
    print("Fallback auf Mock-Implementierung")
    
    class PlaylistGenerator:
        def start_wizard(self):
            return {'current_step': 1, 'total_steps': 4}
        
        def get_mood_presets(self):
            return {
                "Progressive Journey": {
                    "emoji": "🚀",
                    "description": "Eine progressive Reise durch verschiedene Energy-Level",
                    "energy_curve": "progressive"
                },
                "Chill Vibes": {
                    "emoji": "😌",
                    "description": "Entspannte Atmosphäre für ruhige Momente",
                    "energy_curve": "low"
                },
                "Peak Time": {
                    "emoji": "🔥",
                    "description": "Hochenergetische Tracks für die Tanzfläche",
                    "energy_curve": "high"
                }
            }
        
        def generate_from_wizard(self, wizard_state, tracks):
            return {
                'playlist': tracks[:3],
                'metadata': {'preset_name': 'Demo_Playlist'}
            }
        
        def get_smart_suggestions(self, base_track, tracks, count=3):
            suggestions = []
            for track in tracks[:count]:
                if track['id'] != base_track['id']:
                    suggestions.append({
                        'track': track,
                        'similarity_score': 0.85,
                        'reasons': ['BPM Match', 'Key Compatibility']
                    })
            return suggestions
    
    class EnhancedExportManager:
        def export_playlist(self, playlist_data, output_dir, formats):
            return {fmt: f"{output_dir}/demo.{fmt}" for fmt in formats}

app = Flask(__name__)

# Demo-Daten
DEMO_TRACKS = [
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
        'mood_label': 'Dark'
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
        'mood_label': 'Euphoric'
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
        'mood_label': 'Chill'
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
        'mood_label': 'Driving'
    }
]

# Initialisiere Komponenten
generator = PlaylistGenerator()
export_manager = EnhancedExportManager()

@app.route('/')
def index():
    """Hauptseite"""
    return render_template('index.html')

@app.route('/api/mood-presets')
def get_mood_presets():
    """API: Hole Mood Presets"""
    try:
        presets = generator.get_mood_presets()
        return jsonify({'success': True, 'presets': presets})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/tracks')
def get_tracks():
    """API: Hole alle Tracks"""
    return jsonify({'success': True, 'tracks': DEMO_TRACKS})

@app.route('/api/suggestions/<int:track_id>')
def get_suggestions(track_id):
    """API: Hole Smart Suggestions für einen Track"""
    try:
        base_track = next((t for t in DEMO_TRACKS if t['id'] == track_id), None)
        if not base_track:
            return jsonify({'success': False, 'error': 'Track nicht gefunden'})
        
        suggestions = generator.get_smart_suggestions(base_track, DEMO_TRACKS, count=2)
        return jsonify({'success': True, 'suggestions': suggestions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-playlist', methods=['POST'])
def generate_playlist():
    """API: Generiere Playlist"""
    try:
        data = request.json
        preset_name = data.get('preset', 'Progressive Journey')
        
        # Simuliere Wizard-Prozess
        wizard_state = generator.start_wizard()
        
        # Generiere Playlist
        result = generator.generate_from_wizard(wizard_state, DEMO_TRACKS)
        
        return jsonify({
            'success': True, 
            'playlist': result['playlist'],
            'metadata': result['metadata']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Erstelle Templates-Verzeichnis
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Erstelle HTML-Template
    html_content = '''
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Playlist Engine - Web Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .demo-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .demo-section h2 {
            color: #4a5568;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .feature-card {
            background: #f7fafc;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }
        
        .feature-card h3 {
            color: #2d3748;
            margin-bottom: 10px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .track-list {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .track-item {
            background: white;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 8px;
            border-left: 3px solid #667eea;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .track-info {
            flex-grow: 1;
        }
        
        .track-meta {
            font-size: 0.9em;
            color: #666;
            margin-top: 4px;
        }
        
        .energy-bar {
            width: 60px;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin-left: 15px;
        }
        
        .energy-fill {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #ed8936, #e53e3e);
            transition: width 0.3s;
        }
        
        .preset-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .preset-card {
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .preset-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        .preset-card.selected {
            border-color: #667eea;
            background: #f0f4ff;
        }
        
        .preset-emoji {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .error {
            background: #fed7d7;
            color: #c53030;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .success {
            background: #c6f6d5;
            color: #2f855a;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Enhanced Playlist Engine</h1>
            <p>Intelligente Playlist-Generierung mit KI-gestützten Algorithmen</p>
        </div>
        
        <div class="demo-section">
            <h2>🚀 Features</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>🧙‍♂️ 4-Schritt Playlist Wizard</h3>
                    <p>Intuitiver Wizard für die Erstellung perfekter Playlists mit Mood Presets und Energy Curves.</p>
                </div>
                <div class="feature-card">
                    <h3>🤖 Smart Suggestions Engine</h3>
                    <p>KI-basierte Vorschläge basierend auf Audio-Features, BPM-Matching und harmonischer Kompatibilität.</p>
                </div>
                <div class="feature-card">
                    <h3>📊 EnergyScore Algorithmus</h3>
                    <p>Fortschrittliche Analyse von Spektral-Features zur Bestimmung der Track-Energie.</p>
                </div>
                <div class="feature-card">
                    <h3>🎯 Camelot Wheel Integration</h3>
                    <p>Harmonisches Mixing mit dem Camelot Wheel System für nahtlose Übergänge.</p>
                </div>
            </div>
        </div>
        
        <div class="demo-section">
            <h2>🎼 Mood Presets</h2>
            <div id="presets-container" class="loading">Lade Mood Presets...</div>
        </div>
        
        <div class="demo-section">
            <h2>🎵 Demo Tracks</h2>
            <div id="tracks-container" class="loading">Lade Tracks...</div>
        </div>
        
        <div class="demo-section">
            <h2>🤖 Smart Suggestions Demo</h2>
            <p>Klicken Sie auf einen Track oben, um Smart Suggestions zu sehen.</p>
            <div id="suggestions-container"></div>
        </div>
        
        <div class="demo-section">
            <h2>🎼 Playlist Generator</h2>
            <button class="btn" onclick="generatePlaylist()">🚀 Generiere Demo Playlist</button>
            <div id="playlist-container"></div>
        </div>
    </div>
    
    <script>
        let selectedPreset = 'Progressive Journey';
        let tracks = [];
        
        // Lade Mood Presets
        async function loadPresets() {
            try {
                const response = await fetch('/api/mood-presets');
                const data = await response.json();
                
                if (data.success) {
                    displayPresets(data.presets);
                } else {
                    document.getElementById('presets-container').innerHTML = 
                        `<div class="error">Fehler beim Laden der Presets: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('presets-container').innerHTML = 
                    `<div class="error">Netzwerk-Fehler: ${error.message}</div>`;
            }
        }
        
        function displayPresets(presets) {
            const container = document.getElementById('presets-container');
            const presetCards = Object.entries(presets).map(([name, data]) => `
                <div class="preset-card ${name === selectedPreset ? 'selected' : ''}" 
                     onclick="selectPreset('${name}')">
                    <div class="preset-emoji">${data.emoji}</div>
                    <h4>${name}</h4>
                    <p>${data.description}</p>
                </div>
            `).join('');
            
            container.innerHTML = `<div class="preset-grid">${presetCards}</div>`;
        }
        
        function selectPreset(name) {
            selectedPreset = name;
            loadPresets(); // Refresh to show selection
        }
        
        // Lade Tracks
        async function loadTracks() {
            try {
                const response = await fetch('/api/tracks');
                const data = await response.json();
                
                if (data.success) {
                    tracks = data.tracks;
                    displayTracks(tracks);
                } else {
                    document.getElementById('tracks-container').innerHTML = 
                        `<div class="error">Fehler beim Laden der Tracks: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('tracks-container').innerHTML = 
                    `<div class="error">Netzwerk-Fehler: ${error.message}</div>`;
            }
        }
        
        function displayTracks(trackList) {
            const container = document.getElementById('tracks-container');
            const trackItems = trackList.map(track => `
                <div class="track-item" onclick="showSuggestions(${track.id})" style="cursor: pointer;">
                    <div class="track-info">
                        <strong>${track.artist} - ${track.title}</strong>
                        <div class="track-meta">
                            ${track.genre} | ${track.bpm} BPM | ${track.key} | ${track.mood_label}
                        </div>
                    </div>
                    <div class="energy-bar">
                        <div class="energy-fill" style="width: ${(track.energy_score / 10) * 100}%"></div>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = `<div class="track-list">${trackItems}</div>`;
        }
        
        // Smart Suggestions
        async function showSuggestions(trackId) {
            const container = document.getElementById('suggestions-container');
            container.innerHTML = '<div class="loading">Lade Suggestions...</div>';
            
            try {
                const response = await fetch(`/api/suggestions/${trackId}`);
                const data = await response.json();
                
                if (data.success) {
                    displaySuggestions(data.suggestions, trackId);
                } else {
                    container.innerHTML = `<div class="error">Fehler: ${data.error}</div>`;
                }
            } catch (error) {
                container.innerHTML = `<div class="error">Netzwerk-Fehler: ${error.message}</div>`;
            }
        }
        
        function displaySuggestions(suggestions, baseTrackId) {
            const container = document.getElementById('suggestions-container');
            const baseTrack = tracks.find(t => t.id === baseTrackId);
            
            let html = `
                <div class="success">
                    <strong>Basis-Track:</strong> ${baseTrack.artist} - ${baseTrack.title}
                </div>
                <div class="track-list">
            `;
            
            suggestions.forEach(suggestion => {
                const track = suggestion.track;
                html += `
                    <div class="track-item">
                        <div class="track-info">
                            <strong>${track.artist} - ${track.title}</strong>
                            <div class="track-meta">
                                Score: ${suggestion.similarity_score.toFixed(2)} | 
                                Gründe: ${suggestion.reasons.join(', ')}
                            </div>
                        </div>
                        <div class="energy-bar">
                            <div class="energy-fill" style="width: ${(track.energy_score / 10) * 100}%"></div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        // Playlist Generator
        async function generatePlaylist() {
            const container = document.getElementById('playlist-container');
            container.innerHTML = '<div class="loading">Generiere Playlist...</div>';
            
            try {
                const response = await fetch('/api/generate-playlist', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        preset: selectedPreset
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayPlaylist(data.playlist, data.metadata);
                } else {
                    container.innerHTML = `<div class="error">Fehler: ${data.error}</div>`;
                }
            } catch (error) {
                container.innerHTML = `<div class="error">Netzwerk-Fehler: ${error.message}</div>`;
            }
        }
        
        function displayPlaylist(playlist, metadata) {
            const container = document.getElementById('playlist-container');
            
            let html = `
                <div class="success">
                    <strong>Playlist generiert!</strong> Preset: ${selectedPreset}
                </div>
                <div class="track-list">
            `;
            
            playlist.forEach((track, index) => {
                html += `
                    <div class="track-item">
                        <div class="track-info">
                            <strong>${index + 1}. ${track.artist} - ${track.title}</strong>
                            <div class="track-meta">
                                ${track.genre} | ${track.bpm} BPM | Energy: ${track.energy_score.toFixed(1)}
                            </div>
                        </div>
                        <div class="energy-bar">
                            <div class="energy-fill" style="width: ${(track.energy_score / 10) * 100}%"></div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        // Initialisierung
        document.addEventListener('DOMContentLoaded', function() {
            loadPresets();
            loadTracks();
        });
    </script>
</body>
</html>
    '''
    
    with open(templates_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("🚀 Enhanced Playlist Engine Web Demo")
    print("📊 Starte Server auf http://localhost:5000")
    print("\nFeatures:")
    print("• 🧙‍♂️ 4-Schritt Playlist Wizard")
    print("• 🤖 Smart Suggestions Engine")
    print("• 📊 EnergyScore Algorithmus")
    print("• 🎯 Camelot Wheel Integration")
    print("• 📤 Erweiterte Export-Funktionen")
    
    app.run(host='0.0.0.0', port=5000, debug=True)