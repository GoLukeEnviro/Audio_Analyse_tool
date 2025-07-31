"""Playlist Generator - Hauptlogik für intelligente Playlist-Generierung"""

from typing import Dict, List, Any, Optional, Tuple
import json
import os
import random
import numpy as np
from datetime import datetime

from .rule_engine import RuleEngine
from .sorting_algorithms import SortingAlgorithms
from .camelot_wheel import CamelotWheel

try:
    from .similarity_engine import SimilarityEngine
    from ..audio_analysis.energy_score_extractor import EnergyScoreExtractor
    from ..audio_analysis.mood_classifier_enhanced import EnhancedMoodClassifier
except ImportError:
    # Fallback für direkte Ausführung
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from playlist_engine.similarity_engine import SimilarityEngine
    from audio_analysis.energy_score_extractor import EnergyScoreExtractor
    from audio_analysis.mood_classifier_enhanced import EnhancedMoodClassifier


class PlaylistGenerator:
    """Hauptklasse für die Generierung intelligenter Playlists"""
    
    def __init__(self, config_dir: str = None):
        self.rule_engine = RuleEngine()
        self.sorting_algorithms = SortingAlgorithms()
        self.camelot_wheel = CamelotWheel()
        self.similarity_engine = SimilarityEngine(config_dir)
        self.energy_extractor = EnergyScoreExtractor()
        self.mood_classifier = EnhancedMoodClassifier()
        
        self.config_dir = config_dir or os.path.join(os.getcwd(), 'config')
        self.presets_file = os.path.join(self.config_dir, 'playlist_presets.json')
        
        self.presets = {}
        self.load_presets()
        
        # Standard-Presets
        self.setup_default_presets()
        
        # Wizard-State
        self.wizard_state = {
            'step': 1,
            'mood_preset': None,
            'energy_curve': None,
            'key_preferences': [],
            'duration_minutes': 60,
            'transition_style': 'smooth'
        }
    
    def setup_default_presets(self):
        """Erstellt erweiterte Mood-Presets für Wizard"""
        default_presets = {
            'Warm Up': {
                'bpm_range': [100, 130],
                'energy_range': [0.3, 0.7],
                'moods': ['Chill', 'Progressive', 'Driving'],
                'key_compatibility': 'camelot_compatible',
                'sorting_algorithm': 'energy_curve',
                'curve_type': 'buildup',
                'duration_min': 45,
                'description': 'Sanfter Einstieg mit steigender Energie',
                'emoji': '🌅',
                'energy_curve': [3, 4, 5, 6, 7],
                'mood_progression': ['Chill', 'Progressive', 'Driving'],
                'bpm_progression': [(100, 115), (115, 125), (125, 130)],
                'key_suggestions': ['8A', '9A', '10A', '11A', '12A']
            },
            'Peak Time': {
                'bpm_range': [125, 135],
                'energy_range': [0.7, 1.0],
                'moods': ['Driving', 'Euphoric'],
                'key_compatibility': 'camelot_compatible',
                'sorting_algorithm': 'intelligent',
                'peak_position': 0.6,
                'duration_min': 60,
                'description': 'Hochenergetische Tracks für Prime Time',
                'emoji': '🔥',
                'energy_curve': [8, 9, 10, 9, 8],
                'mood_progression': ['Driving', 'Euphoric', 'Euphoric'],
                'bpm_progression': [(128, 132), (132, 135), (130, 134)],
                'key_suggestions': ['1A', '2A', '3A', '1B', '2B', '3B']
            },
            'Cool Down': {
                'bpm_range': [105, 120],
                'energy_range': [0.2, 0.6],
                'moods': ['Progressive', 'Chill', 'Ambient'],
                'key_compatibility': 'harmonic',
                'sorting_algorithm': 'energy_curve',
                'curve_type': 'breakdown',
                'duration_min': 30,
                'description': 'Entspannter Ausklang',
                'emoji': '🌙',
                'energy_curve': [6, 5, 4, 3, 2],
                'mood_progression': ['Progressive', 'Chill', 'Ambient'],
                'bpm_progression': [(120, 115), (115, 110), (110, 105)],
                'key_suggestions': ['6A', '7A', '8A', '9A']
            },
            'Dark Techno': {
                'bpm_range': [130, 145],
                'energy_range': [0.6, 0.9],
                'moods': ['Dark', 'Experimental'],
                'key_compatibility': 'adjacent',
                'sorting_algorithm': 'harmonic_mixing',
                'duration_min': 75,
                'description': 'Düstere, treibende Techno-Journey',
                'emoji': '🖤',
                'energy_curve': [6, 7, 8, 9, 8],
                'mood_progression': ['Dark', 'Dark', 'Experimental'],
                'bmp_progression': [(130, 135), (135, 140), (138, 142)],
                'key_suggestions': ['6A', '7A', '8A', '6B', '7B']
            },
            'Progressive House': {
                'bpm_range': [120, 132],
                'energy_range': [0.5, 0.8],
                'moods': ['Progressive', 'Euphoric'],
                'key_compatibility': 'camelot_compatible',
                'sorting_algorithm': 'energy_curve',
                'curve_type': 'buildup',
                'duration_min': 90,
                'description': 'Melodische Progressive-Reise',
                'emoji': '🌊',
                'energy_curve': [5, 6, 7, 8, 7],
                'mood_progression': ['Progressive', 'Euphoric', 'Progressive'],
                'bpm_progression': [(120, 125), (125, 128), (126, 130)],
                'key_suggestions': ['9A', '10A', '11A', '12A', '1A']
            }
        }
        
        for name, preset in default_presets.items():
            if name not in self.presets:
                self.presets[name] = preset
    
    def generate_playlist(self, tracks: List[Dict[str, Any]], rules: Dict[str, Any], 
                         target_duration: Optional[int] = None, 
                         max_tracks: Optional[int] = None) -> Dict[str, Any]:
        """Generiert eine Playlist basierend auf Regeln"""
        
        if not tracks:
            return self._create_empty_playlist_result("Keine Tracks verfügbar")
        
        # Validiere und bereinige Regeln
        validation_errors = self.rule_engine.validate_rules(rules)
        if validation_errors:
            print(f"Regel-Validierungsfehler: {validation_errors}")
            # Entferne ungültige Regeln
            rules = {k: v for k, v in rules.items() if k not in validation_errors}
        
        # Wende Regeln an
        filtered_tracks = self.rule_engine.apply_rules(tracks, rules)
        
        if not filtered_tracks:
            return self._create_empty_playlist_result("Keine Tracks entsprechen den Regeln")
        
        # Begrenze Tracks nach Dauer oder Anzahl
        selected_tracks = self._select_tracks_by_constraints(
            filtered_tracks, target_duration, max_tracks
        )
        
        # Sortiere Tracks
        sorting_algorithm = rules.get('sorting_algorithm', 'intelligent')
        sorted_tracks = self.sorting_algorithms.sort_tracks(
            selected_tracks, sorting_algorithm, **rules
        )
        
        # Erstelle Playlist-Ergebnis
        result = self._create_playlist_result(sorted_tracks, rules, tracks)
        
        return result
    
    def generate_from_preset(self, tracks: List[Dict[str, Any]], preset_name: str, 
                           **overrides) -> Dict[str, Any]:
        """Generiert Playlist aus einem Preset"""
        
        if preset_name not in self.presets:
            return self._create_empty_playlist_result(f"Preset '{preset_name}' nicht gefunden")
        
        # Lade Preset und überschreibe mit gegebenen Parametern
        rules = self.presets[preset_name].copy()
        rules.update(overrides)
        
        return self.generate_playlist(tracks, rules)
    
    def suggest_next_tracks(self, current_track: Dict[str, Any], 
                          available_tracks: List[Dict[str, Any]], 
                          count: int = 5, 
                          compatibility_level: str = 'adjacent') -> List[Dict[str, Any]]:
        """Schlägt nächste Tracks basierend auf dem aktuellen Track vor"""
        
        if not current_track or not available_tracks:
            return []
        
        current_key = current_track.get('key')
        current_bpm = current_track.get('bpm', 120)
        current_energy = current_track.get('energy', 0.5)
        current_mood = current_track.get('mood')
        
        # Score jeden verfügbaren Track
        scored_tracks = []
        
        for track in available_tracks:
            if track.get('file_path') == current_track.get('file_path'):
                continue  # Überspringe den aktuellen Track
            
            score = self._calculate_compatibility_score(
                current_track, track, compatibility_level
            )
            
            scored_tracks.append((track, score))
        
        # Sortiere nach Score und gib Top-Ergebnisse zurück
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        
        return [track for track, score in scored_tracks[:count]]
    
    def analyze_playlist_quality(self, playlist_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysiert die Qualität einer Playlist"""
        
        if not playlist_tracks:
            return {'quality_score': 0.0, 'issues': ['Playlist ist leer']}
        
        analysis = self.sorting_algorithms.analyze_playlist_flow(playlist_tracks)
        
        # Berechne Gesamt-Qualitätsscore
        quality_factors = {
            'harmonic_quality': analysis.get('harmonic_quality', 0.5),
            'energy_flow': analysis.get('energy_flow_quality', 0.5),
            'bpm_consistency': self._analyze_bpm_consistency(playlist_tracks),
            'duration_balance': self._analyze_duration_balance(playlist_tracks)
        }
        
        # Gewichteter Durchschnitt
        weights = {'harmonic_quality': 0.3, 'energy_flow': 0.3, 'bpm_consistency': 0.2, 'duration_balance': 0.2}
        quality_score = sum(quality_factors[factor] * weights[factor] for factor in weights)
        
        # Identifiziere Probleme
        issues = []
        if quality_factors['harmonic_quality'] < 0.6:
            issues.append('Schwache harmonische Übergänge')
        if quality_factors['energy_flow'] < 0.5:
            issues.append('Ungleichmäßiger Energie-Verlauf')
        if quality_factors['bpm_consistency'] < 0.7:
            issues.append('Große BPM-Sprünge')
        if quality_factors['duration_balance'] < 0.6:
            issues.append('Unausgewogene Track-Längen')
        
        analysis.update({
            'quality_score': quality_score,
            'quality_factors': quality_factors,
            'issues': issues,
            'recommendations': self._generate_recommendations(quality_factors)
        })
        
        return analysis
    
    def optimize_playlist(self, playlist_tracks: List[Dict[str, Any]], 
                         optimization_target: str = 'overall') -> List[Dict[str, Any]]:
        """Optimiert eine bestehende Playlist"""
        
        if len(playlist_tracks) <= 2:
            return playlist_tracks
        
        if optimization_target == 'harmonic':
            return self.sorting_algorithms.sort_tracks(playlist_tracks, 'harmonic_mixing')
        elif optimization_target == 'energy':
            return self.sorting_algorithms.sort_tracks(playlist_tracks, 'energy_curve')
        elif optimization_target == 'bpm':
            return self.sorting_algorithms.sort_tracks(playlist_tracks, 'bpm_ascending')
        else:  # overall
            return self.sorting_algorithms.sort_tracks(playlist_tracks, 'intelligent')
    
    def create_mix_transition(self, track_a: Dict[str, Any], track_b: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiert und bewertet einen Übergang zwischen zwei Tracks"""
        
        transition = {
            'from_track': track_a.get('title', 'Unknown'),
            'to_track': track_b.get('title', 'Unknown'),
            'compatibility_score': 0.0,
            'transition_quality': 'Poor',
            'recommendations': []
        }
        
        # BPM-Kompatibilität
        bpm_a = track_a.get('bpm', 120)
        bpm_b = track_b.get('bpm', 120)
        bpm_diff = abs(bpm_a - bpm_b)
        bpm_score = max(0.0, 1.0 - bpm_diff / 20.0)  # 20 BPM = 0 Score
        
        # Tonart-Kompatibilität
        key_a = track_a.get('key')
        key_b = track_b.get('key')
        key_score = 0.5  # Default
        
        if key_a and key_b:
            camelot_a = self.camelot_wheel.key_to_camelot(key_a)
            camelot_b = self.camelot_wheel.key_to_camelot(key_b)
            
            if camelot_a and camelot_b:
                distance = self.camelot_wheel.calculate_distance(camelot_a, camelot_b)
                key_score = max(0.0, 1.0 - distance / 6.0)
                transition['key_transition'] = self.camelot_wheel.get_transition_quality(camelot_a, camelot_b)
        
        # Energie-Kompatibilität
        energy_a = track_a.get('energy', 0.5)
        energy_b = track_b.get('energy', 0.5)
        energy_diff = abs(energy_a - energy_b)
        energy_score = max(0.0, 1.0 - energy_diff)
        
        # Gesamt-Score
        compatibility_score = (bpm_score * 0.4 + key_score * 0.4 + energy_score * 0.2)
        
        # Qualitätsbewertung
        if compatibility_score >= 0.8:
            quality = 'Excellent'
        elif compatibility_score >= 0.6:
            quality = 'Good'
        elif compatibility_score >= 0.4:
            quality = 'Fair'
        else:
            quality = 'Poor'
        
        # Empfehlungen
        recommendations = []
        if bpm_diff > 10:
            recommendations.append(f'BPM-Unterschied von {bpm_diff:.1f} ist groß')
        if energy_diff > 0.3:
            recommendations.append(f'Energie-Sprung von {energy_diff:.2f} ist deutlich')
        if key_score < 0.5:
            recommendations.append('Tonarten sind nicht harmonisch kompatibel')
        
        transition.update({
            'compatibility_score': compatibility_score,
            'transition_quality': quality,
            'bpm_difference': bpm_diff,
            'energy_difference': energy_diff,
            'recommendations': recommendations
        })
        
        return transition
    
    # Preset-Management
    
    def save_preset(self, name: str, rules: Dict[str, Any], description: str = '') -> bool:
        """Speichert ein neues Preset"""
        preset = rules.copy()
        preset['description'] = description
        preset['created_at'] = datetime.now().isoformat()
        
        self.presets[name] = preset
        return self.save_presets()
    
    def delete_preset(self, name: str) -> bool:
        """Löscht ein Preset"""
        if name in self.presets:
            del self.presets[name]
            return self.save_presets()
        return False
    
    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Gibt ein Preset zurück"""
        return self.presets.get(name, {}).copy()
    
    def list_presets(self) -> List[str]:
        """Gibt eine Liste aller Preset-Namen zurück"""
        return list(self.presets.keys())
    
    def save_presets(self) -> bool:
        """Speichert alle Presets in eine Datei"""
        try:
            os.makedirs(os.path.dirname(self.presets_file), exist_ok=True)
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Presets: {e}")
            return False
    
    def load_presets(self) -> bool:
        """Lädt Presets aus einer Datei"""
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    loaded_presets = json.load(f)
                self.presets.update(loaded_presets)
                return True
        except Exception as e:
            print(f"Fehler beim Laden der Presets: {e}")
        return False
    
    # Private Hilfsmethoden
    
    def _select_tracks_by_constraints(self, tracks: List[Dict[str, Any]], 
                                    target_duration: Optional[int], 
                                    max_tracks: Optional[int]) -> List[Dict[str, Any]]:
        """Wählt Tracks basierend auf Dauer- oder Anzahl-Beschränkungen"""
        
        if not target_duration and not max_tracks:
            return tracks
        
        selected = []
        total_duration = 0
        
        # Mische Tracks für Abwechslung
        shuffled_tracks = tracks.copy()
        random.shuffle(shuffled_tracks)
        
        for track in shuffled_tracks:
            track_duration = track.get('duration', 0)
            
            # Prüfe Anzahl-Limit
            if max_tracks and len(selected) >= max_tracks:
                break
            
            # Prüfe Dauer-Limit
            if target_duration and (total_duration + track_duration) > target_duration:
                # Versuche einen kürzeren Track zu finden
                remaining_time = target_duration - total_duration
                shorter_tracks = [t for t in shuffled_tracks[shuffled_tracks.index(track):] 
                                if t.get('duration', 0) <= remaining_time]
                
                if shorter_tracks:
                    track = shorter_tracks[0]
                    track_duration = track.get('duration', 0)
                else:
                    break
            
            selected.append(track)
            total_duration += track_duration
        
        return selected
    
    def _calculate_compatibility_score(self, track_a: Dict[str, Any], 
                                     track_b: Dict[str, Any], 
                                     compatibility_level: str) -> float:
        """Berechnet Kompatibilitäts-Score zwischen zwei Tracks"""
        
        score = 0.0
        
        # BPM-Kompatibilität (40% Gewichtung)
        bpm_a = track_a.get('bpm', 120)
        bpm_b = track_b.get('bpm', 120)
        bpm_diff = abs(bpm_a - bpm_b)
        bpm_score = max(0.0, 1.0 - bpm_diff / 20.0)
        score += bpm_score * 0.4
        
        # Tonart-Kompatibilität (35% Gewichtung)
        key_a = track_a.get('key')
        key_b = track_b.get('key')
        
        if key_a and key_b:
            camelot_a = self.camelot_wheel.key_to_camelot(key_a)
            camelot_b = self.camelot_wheel.key_to_camelot(key_b)
            
            if camelot_a and camelot_b:
                if self.camelot_wheel.are_compatible(camelot_a, camelot_b, compatibility_level):
                    distance = self.camelot_wheel.calculate_distance(camelot_a, camelot_b)
                    key_score = max(0.0, 1.0 - distance / 6.0)
                else:
                    key_score = 0.2  # Minimaler Score für inkompatible Tonarten
            else:
                key_score = 0.5  # Neutral wenn Tonart nicht erkannt
        else:
            key_score = 0.5  # Neutral wenn Tonart fehlt
        
        score += key_score * 0.35
        
        # Energie-Kompatibilität (15% Gewichtung)
        energy_a = track_a.get('energy', 0.5)
        energy_b = track_b.get('energy', 0.5)
        energy_diff = abs(energy_a - energy_b)
        energy_score = max(0.0, 1.0 - energy_diff)
        score += energy_score * 0.15
        
        # Stimmungs-Kompatibilität (10% Gewichtung)
        mood_a = track_a.get('mood')
        mood_b = track_b.get('mood')
        
        if mood_a and mood_b:
            if mood_a == mood_b:
                mood_score = 1.0
            else:
                # Ähnliche Stimmungen
                compatible_moods = {
                    'Euphoric': ['Driving'],
                    'Driving': ['Euphoric', 'Dark'],
                    'Dark': ['Driving', 'Experimental'],
                    'Experimental': ['Dark']
                }
                
                if mood_b in compatible_moods.get(mood_a, []):
                    mood_score = 0.7
                else:
                    mood_score = 0.3
        else:
            mood_score = 0.5  # Neutral wenn Stimmung fehlt
        
        score += mood_score * 0.1
        
        return min(1.0, max(0.0, score))
    
    def _analyze_bpm_consistency(self, tracks: List[Dict[str, Any]]) -> float:
        """Analysiert BPM-Konsistenz einer Playlist"""
        if len(tracks) <= 1:
            return 1.0
        
        bpm_diffs = []
        for i in range(1, len(tracks)):
            bpm_prev = tracks[i-1].get('bpm', 120)
            bpm_curr = tracks[i].get('bpm', 120)
            bpm_diffs.append(abs(bpm_curr - bpm_prev))
        
        avg_diff = sum(bpm_diffs) / len(bpm_diffs)
        return max(0.0, 1.0 - avg_diff / 15.0)  # 15 BPM Durchschnitt = 0 Score
    
    def _analyze_duration_balance(self, tracks: List[Dict[str, Any]]) -> float:
        """Analysiert Ausgewogenheit der Track-Längen"""
        if not tracks:
            return 1.0
        
        durations = [track.get('duration', 0) for track in tracks]
        if not durations or max(durations) == 0:
            return 1.0
        
        avg_duration = sum(durations) / len(durations)
        variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
        std_dev = variance ** 0.5
        
        # Normalisiere Standardabweichung (60 Sekunden = 0 Score)
        balance_score = max(0.0, 1.0 - std_dev / 60.0)
        return balance_score
    
    def _generate_recommendations(self, quality_factors: Dict[str, float]) -> List[str]:
        """Generiert Empfehlungen basierend auf Qualitätsfaktoren"""
        recommendations = []
        
        if quality_factors['harmonic_quality'] < 0.6:
            recommendations.append('Verwende harmonische Sortierung für bessere Tonart-Übergänge')
        
        if quality_factors['energy_flow'] < 0.5:
            recommendations.append('Sortiere nach Energie-Kurve für gleichmäßigeren Verlauf')
        
        if quality_factors['bpm_consistency'] < 0.7:
            recommendations.append('Reduziere BPM-Bereich oder verwende BPM-Sortierung')
        
        if quality_factors['duration_balance'] < 0.6:
            recommendations.append('Wähle Tracks mit ähnlicheren Längen')
        
        return recommendations
    
    def _create_playlist_result(self, tracks: List[Dict[str, Any]], 
                              rules: Dict[str, Any], 
                              original_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Erstellt ein vollständiges Playlist-Ergebnis"""
        
        total_duration = sum(track.get('duration', 0) for track in tracks)
        
        result = {
            'tracks': tracks,
            'metadata': {
                'track_count': len(tracks),
                'total_duration': total_duration,
                'total_duration_formatted': self._format_duration(total_duration),
                'rules_applied': rules,
                'generated_at': datetime.now().isoformat(),
                'source_track_count': len(original_tracks)
            },
            'analysis': self.analyze_playlist_quality(tracks),
            'success': True,
            'message': f'Playlist mit {len(tracks)} Tracks erfolgreich generiert'
        }
        
        return result
    
    def _create_empty_playlist_result(self, message: str) -> Dict[str, Any]:
        """Erstellt ein leeres Playlist-Ergebnis mit Fehlermeldung"""
        return {
            'tracks': [],
            'metadata': {
                'track_count': 0,
                'total_duration': 0,
                'total_duration_formatted': '00:00:00',
                'generated_at': datetime.now().isoformat()
            },
            'analysis': {'quality_score': 0.0, 'issues': [message]},
            'success': False,
            'message': message
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Formatiert Dauer in HH:MM:SS Format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # === WIZARD-FLOW METHODS ===
    
    def start_wizard(self) -> Dict[str, Any]:
        """Startet den Playlist-Wizard"""
        self.wizard_state = {
            'step': 1,
            'mood_preset': None,
            'energy_curve': None,
            'key_preferences': [],
            'duration_minutes': 60,
            'transition_style': 'smooth'
        }
        
        return {
            'step': 1,
            'title': 'Mood & Vibe auswählen',
            'description': 'Wähle den Grundcharakter deiner Playlist',
            'presets': self.get_mood_presets(),
            'wizard_state': self.wizard_state.copy()
        }
    
    def get_mood_presets(self) -> List[Dict[str, Any]]:
        """Gibt Mood-Presets für Wizard zurück"""
        presets = []
        for key, preset in self.presets.items():
            presets.append({
                'id': key,
                'name': preset.get('name', key),
                'description': preset.get('description', ''),
                'emoji': preset.get('emoji', '🎵'),
                'duration_minutes': preset.get('duration_min', 60),
                'energy_curve': preset.get('energy_curve', [5, 6, 7, 6, 5]),
                'mood_progression': preset.get('mood_progression', ['Driving']),
                'bpm_range': preset.get('bpm_range', [120, 130])
            })
        return presets
    
    def wizard_step_2(self, mood_preset_id: str) -> Dict[str, Any]:
        """Wizard Schritt 2: Energy Curve anpassen"""
        if mood_preset_id not in self.presets:
            raise ValueError(f"Unbekanntes Preset: {mood_preset_id}")
        
        self.wizard_state['step'] = 2
        self.wizard_state['mood_preset'] = mood_preset_id
        
        preset = self.presets[mood_preset_id]
        default_curve = preset.get('energy_curve', [5, 6, 7, 6, 5])
        
        return {
            'step': 2,
            'title': 'Energy-Kurve anpassen',
            'description': 'Gestalte den Energieverlauf deiner Playlist',
            'preset_name': preset.get('name', mood_preset_id),
            'default_curve': default_curve,
            'duration_minutes': preset.get('duration_min', 60),
            'curve_templates': self.get_curve_templates(),
            'wizard_state': self.wizard_state.copy()
        }
    
    def get_curve_templates(self) -> List[Dict[str, Any]]:
        """Gibt vordefinierte Energy-Kurven-Templates zurück"""
        return [
            {
                'name': 'Steady Build',
                'description': 'Kontinuierlicher Aufbau',
                'curve': [3, 4, 5, 6, 7, 8, 9],
                'emoji': '📈'
            },
            {
                'name': 'Peak & Valley',
                'description': 'Höhen und Tiefen',
                'curve': [5, 7, 5, 8, 6, 9, 7],
                'emoji': '🏔️'
            },
            {
                'name': 'Plateau',
                'description': 'Konstante Energie',
                'curve': [7, 7, 8, 8, 7, 7, 7],
                'emoji': '🏞️'
            },
            {
                'name': 'Breakdown',
                'description': 'Sanfter Abbau',
                'curve': [8, 7, 6, 5, 4, 3, 2],
                'emoji': '📉'
            }
        ]
    
    def wizard_step_3(self, energy_curve: List[float], duration_minutes: int = 60) -> Dict[str, Any]:
        """Wizard Schritt 3: Key-Präferenzen und Feintuning"""
        self.wizard_state['step'] = 3
        self.wizard_state['energy_curve'] = energy_curve
        self.wizard_state['duration_minutes'] = duration_minutes
        
        preset = self.presets[self.wizard_state['mood_preset']]
        
        return {
            'step': 3,
            'title': 'Tonarten & Feintuning',
            'description': 'Wähle bevorzugte Tonarten und Übergangsstil',
            'key_suggestions': preset.get('key_suggestions', ['1A', '2A', '3A']),
            'camelot_wheel': self.get_camelot_wheel_data(),
            'transition_styles': [
                {'id': 'smooth', 'name': 'Smooth', 'description': 'Sanfte Übergänge'},
                {'id': 'energetic', 'name': 'Energetic', 'description': 'Dynamische Sprünge'},
                {'id': 'harmonic', 'name': 'Harmonic', 'description': 'Harmonische Progression'}
            ],
            'wizard_state': self.wizard_state.copy()
        }
    
    def get_camelot_wheel_data(self) -> Dict[str, Any]:
        """Gibt Camelot Wheel-Daten für UI zurück"""
        wheel_data = []
        
        for number in range(1, 13):
            for key_type in ['A', 'B']:
                camelot = f"{number}{key_type}"
                key_name = self.camelot_wheel.camelot_to_key.get(camelot, 'Unknown')
                
                wheel_data.append({
                    'camelot': camelot,
                    'key': key_name,
                    'number': number,
                    'type': key_type,
                    'position': {
                        'angle': (number - 1) * 30,  # 360° / 12 = 30°
                        'radius': 100 if key_type == 'B' else 70
                    }
                })
        
        return {
            'keys': wheel_data,
            'compatible_rules': {
                'same': 'Gleiche Tonart',
                'adjacent': '±1 Position',
                'relative': 'A ↔ B (gleiche Zahl)',
                'dominant': '+7 Positionen',
                'subdominant': '-7 Positionen'
            }
        }
    
    def wizard_step_4(self, key_preferences: List[str], transition_style: str = 'smooth') -> Dict[str, Any]:
        """Wizard Schritt 4: Vorschau und Export"""
        self.wizard_state['step'] = 4
        self.wizard_state['key_preferences'] = key_preferences
        self.wizard_state['transition_style'] = transition_style
        
        return {
            'step': 4,
            'title': 'Vorschau & Export',
            'description': 'Playlist-Vorschau und Export-Optionen',
            'wizard_state': self.wizard_state.copy(),
            'ready_to_generate': True
        }
    
    def generate_from_wizard(self, available_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generiert Playlist basierend auf Wizard-Einstellungen"""
        if self.wizard_state['step'] != 4:
            raise ValueError("Wizard nicht vollständig durchlaufen")
        
        # Baue Similarity-Index auf
        self.similarity_engine.build_similarity_index(available_tracks)
        
        # Konvertiere Wizard-State zu Preset-Format
        wizard_preset = self._wizard_state_to_preset()
        
        # Generiere Playlist mit erweiterten Algorithmen
        result = self.generate_playlist_advanced(
            available_tracks,
            wizard_preset,
            use_smart_suggestions=True
        )
        
        return result
    
    def _wizard_state_to_preset(self) -> Dict[str, Any]:
        """Konvertiert Wizard-State zu Preset-Format"""
        base_preset = self.presets[self.wizard_state['mood_preset']].copy()
        
        # Überschreibe mit Wizard-Einstellungen
        base_preset['energy_curve'] = self.wizard_state['energy_curve']
        base_preset['duration_min'] = self.wizard_state['duration_minutes']
        base_preset['key_preferences'] = self.wizard_state['key_preferences']
        base_preset['transition_style'] = self.wizard_state['transition_style']
        
        return base_preset
    
    # === SMART SUGGESTIONS ===
    
    def generate_playlist_advanced(self, available_tracks: List[Dict[str, Any]], 
                                 preset: Dict[str, Any],
                                 use_smart_suggestions: bool = True) -> Dict[str, Any]:
        """Erweiterte Playlist-Generierung mit Smart Suggestions"""
        import time
        start_time = time.time()
        
        # Filtere Tracks nach Preset-Regeln
        filtered_tracks = self.rule_engine.apply_rules(available_tracks, preset)
        
        if len(filtered_tracks) < 3:
            return {
                'error': 'Nicht genügend passende Tracks gefunden',
                'available_tracks': len(available_tracks),
                'filtered_tracks': len(filtered_tracks)
            }
        
        # Erweitere Tracks mit Energy Score und Mood
        enhanced_tracks = self._enhance_tracks_with_analysis(filtered_tracks)
        
        # Generiere Playlist mit Smart Suggestions
        if use_smart_suggestions:
            playlist = self._generate_with_smart_suggestions(enhanced_tracks, preset)
        else:
            playlist = self._generate_traditional(enhanced_tracks, preset)
        
        # Optimiere Übergänge
        optimized_playlist = self._optimize_transitions(playlist, preset)
        
        return {
            'playlist': optimized_playlist,
            'metadata': {
                'preset_name': preset.get('name', 'Custom'),
                'total_tracks': len(optimized_playlist),
                'total_duration': sum(track.get('duration', 0) for track in optimized_playlist),
                'avg_bpm': sum(track.get('bpm', 0) for track in optimized_playlist) / len(optimized_playlist) if optimized_playlist else 0,
                'energy_progression': [track.get('energy_score', 5) for track in optimized_playlist],
                'generation_time': time.time() - start_time,
                'algorithm': 'smart_suggestions' if use_smart_suggestions else 'traditional'
            }
        }
    
    def _enhance_tracks_with_analysis(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Erweitert Tracks mit Energy Score und Mood-Analyse"""
        enhanced = []
        
        for track in tracks:
            enhanced_track = track.copy()
            
            # Energy Score (falls nicht vorhanden)
            if 'energy_score' not in enhanced_track:
                # Fallback basierend auf vorhandenen Daten
                bpm = enhanced_track.get('bpm', 120)
                energy_estimate = min(10, max(1, (bpm - 100) / 10 + 3))
                enhanced_track['energy_score'] = energy_estimate
            
            # Mood Label (falls nicht vorhanden)
            if 'mood_label' not in enhanced_track:
                # Heuristische Mood-Zuweisung
                energy = enhanced_track.get('energy_score', 5)
                if energy >= 8:
                    enhanced_track['mood_label'] = 'Euphoric'
                elif energy >= 6:
                    enhanced_track['mood_label'] = 'Driving'
                elif energy >= 4:
                    enhanced_track['mood_label'] = 'Progressive'
                else:
                    enhanced_track['mood_label'] = 'Chill'
                
                enhanced_track['mood_confidence'] = 0.6  # Heuristische Confidence
            
            enhanced.append(enhanced_track)
        
        return enhanced
    
    def _generate_with_smart_suggestions(self, tracks: List[Dict[str, Any]], 
                                       preset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generiert Playlist mit k-NN Smart Suggestions"""
        playlist = []
        remaining_tracks = tracks.copy()
        target_duration = preset.get('duration_min', 60) * 60  # Sekunden
        energy_curve = preset.get('energy_curve', [5, 6, 7, 6, 5])
        
        # Wähle Starter-Track
        starter_track = self._select_starter_track(remaining_tracks, energy_curve[0])
        if not starter_track:
            return []
        
        playlist.append(starter_track)
        remaining_tracks.remove(starter_track)
        
        current_duration = starter_track.get('duration', 240)
        curve_position = 0
        
        # Füge Tracks basierend auf Similarity hinzu
        while current_duration < target_duration and remaining_tracks and curve_position < len(energy_curve) - 1:
            curve_position += 1
            target_energy = energy_curve[curve_position]
            
            # Finde ähnliche Tracks mit passender Energy
            current_track = playlist[-1]
            
            # k-NN Suggestions
            similar_tracks = self.similarity_engine.find_similar_tracks(
                current_track,
                exclude_tracks=[t.get('file_path', '') for t in playlist],
                count=5,
                min_compatibility=0.6
            )
            
            # Filtere nach Energy-Target
            energy_filtered = [
                track for track in similar_tracks
                if abs(track.get('energy_score', 5) - target_energy) <= 1.5
            ]
            
            if energy_filtered:
                next_track = energy_filtered[0]  # Bester Match
            else:
                # Fallback: Surprise-Track oder bester verfügbarer
                surprise_tracks = self.similarity_engine.get_surprise_tracks(
                    current_track, remaining_tracks, count=1
                )
                
                if surprise_tracks:
                    next_track = surprise_tracks[0]
                else:
                    # Letzter Fallback
                    next_track = self._find_best_energy_match(remaining_tracks, target_energy)
            
            if next_track and next_track in remaining_tracks:
                playlist.append(next_track)
                remaining_tracks.remove(next_track)
                current_duration += next_track.get('duration', 240)
        
        return playlist
    
    def _generate_traditional(self, tracks: List[Dict[str, Any]], 
                            preset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Traditionelle Playlist-Generierung ohne Smart Suggestions"""
        # Verwende bestehende Sortieralgorithmen
        sorting_algorithm = preset.get('sorting_algorithm', 'intelligent')
        return self.sorting_algorithms.sort_tracks(tracks, sorting_algorithm, **preset)
    
    def _select_starter_track(self, tracks: List[Dict[str, Any]], target_energy: float) -> Optional[Dict[str, Any]]:
        """Wählt optimalen Starter-Track"""
        # Sortiere nach Energy-Nähe zum Target
        energy_sorted = sorted(
            tracks,
            key=lambda t: abs(t.get('energy_score', 5) - target_energy)
        )
        
        return energy_sorted[0] if energy_sorted else None
    
    def _find_best_energy_match(self, tracks: List[Dict[str, Any]], target_energy: float) -> Optional[Dict[str, Any]]:
        """Findet Track mit bester Energy-Übereinstimmung"""
        if not tracks:
            return None
        
        best_track = min(
            tracks,
            key=lambda t: abs(t.get('energy_score', 5) - target_energy)
        )
        
        return best_track
    
    def _optimize_transitions(self, playlist: List[Dict[str, Any]], 
                            preset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimiert Übergänge zwischen Tracks"""
        if len(playlist) <= 1:
            return playlist
        
        transition_style = preset.get('transition_style', 'smooth')
        
        # Füge Transition-Metadaten hinzu
        for i in range(len(playlist) - 1):
            current_track = playlist[i]
            next_track = playlist[i + 1]
            
            # Berechne Transition-Score
            transition_score = self.similarity_engine.calculate_compatibility_score(
                current_track, next_track
            )
            
            # Füge Transition-Daten hinzu
            current_track['transition_to_next'] = {
                'compatibility_score': transition_score,
                'style': transition_style,
                'bmp_change': next_track.get('bpm', 120) - current_track.get('bpm', 120),
                'energy_change': next_track.get('energy_score', 5) - current_track.get('energy_score', 5),
                'key_change': self._analyze_key_change(current_track, next_track)
            }
        
        return playlist
    
    def _analyze_key_change(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> Dict[str, str]:
        """Analysiert Tonart-Wechsel zwischen Tracks"""
        key1 = track1.get('key', '')
        key2 = track2.get('key', '')
        
        if not key1 or not key2:
            return {'type': 'unknown', 'description': 'Tonart unbekannt'}
        
        camelot1 = self.camelot_wheel.key_to_camelot(key1)
        camelot2 = self.camelot_wheel.key_to_camelot(key2)
        
        if not camelot1 or not camelot2:
            return {'type': 'unknown', 'description': 'Camelot-Konvertierung fehlgeschlagen'}
        
        if camelot1 == camelot2:
            return {'type': 'same', 'description': 'Gleiche Tonart'}
        
        compatible_keys = self.camelot_wheel.get_compatible_keys(camelot1, 'extended')
        
        if camelot2 in compatible_keys:
            return {'type': 'compatible', 'description': 'Harmonisch kompatibel'}
        else:
            return {'type': 'clash', 'description': 'Harmonischer Konflikt'}
    
    def get_smart_suggestions(self, current_track: Dict[str, Any], 
                            available_tracks: List[Dict[str, Any]],
                            count: int = 5) -> List[Dict[str, Any]]:
        """Gibt Smart Suggestions für nächsten Track zurück"""
        if not hasattr(self, 'similarity_engine') or self.similarity_engine.feature_matrix is None:
            # Baue Index auf falls nicht vorhanden
            self.similarity_engine.build_similarity_index(available_tracks)
        
        suggestions = self.similarity_engine.find_similar_tracks(
            current_track,
            exclude_tracks=[current_track.get('file_path', '')],
            count=count,
            min_compatibility=0.5
        )
        
        return suggestions
    
    def get_surprise_suggestions(self, current_track: Dict[str, Any],
                               available_tracks: List[Dict[str, Any]],
                               count: int = 2) -> List[Dict[str, Any]]:
        """Gibt Surprise-Me Suggestions zurück"""
        return self.similarity_engine.get_surprise_tracks(
            current_track, available_tracks, count
        )