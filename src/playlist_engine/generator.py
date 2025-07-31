"""Playlist Generator - Hauptlogik für intelligente Playlist-Generierung"""

from typing import Dict, List, Any, Optional, Tuple
import json
import os
import random
from datetime import datetime

from .rule_engine import RuleEngine
from .sorting_algorithms import SortingAlgorithms
from .camelot_wheel import CamelotWheel


class PlaylistGenerator:
    """Hauptklasse für die Generierung intelligenter Playlists"""
    
    def __init__(self, config_dir: str = None):
        self.rule_engine = RuleEngine()
        self.sorting_algorithms = SortingAlgorithms()
        self.camelot_wheel = CamelotWheel()
        
        self.config_dir = config_dir or os.path.join(os.getcwd(), 'config')
        self.presets_file = os.path.join(self.config_dir, 'playlist_presets.json')
        
        self.presets = {}
        self.load_presets()
        
        # Standard-Presets
        self.setup_default_presets()
    
    def setup_default_presets(self):
        """Erstellt Standard-Presets für verschiedene DJ-Stile"""
        default_presets = {
            'Progressive House': {
                'bpm_range': [120, 130],
                'energy_range': [0.6, 0.9],
                'moods': ['Driving', 'Euphoric'],
                'key_compatibility': 'camelot_compatible',
                'sorting_algorithm': 'energy_curve',
                'curve_type': 'buildup',
                'duration_min': 300,  # 5 Minuten
                'description': 'Progressive House Set mit kontinuierlichem Energie-Aufbau'
            },
            'Dark Techno': {
                'bpm_range': [125, 135],
                'energy_range': [0.7, 1.0],
                'moods': ['Dark', 'Experimental'],
                'key_compatibility': 'adjacent',
                'sorting_algorithm': 'harmonic_mixing',
                'duration_min': 360,  # 6 Minuten
                'description': 'Dunkler Techno mit harmonischen Übergängen'
            },
            'Peak Time': {
                'bpm_range': [128, 138],
                'energy_range': [0.8, 1.0],
                'moods': ['Euphoric', 'Driving'],
                'key_compatibility': 'camelot_compatible',
                'sorting_algorithm': 'intelligent',
                'peak_position': 0.6,
                'description': 'Hochenergetisches Peak-Time Set'
            },
            'Warm Up': {
                'bpm_range': [115, 125],
                'energy_range': [0.3, 0.7],
                'moods': ['Driving'],
                'key_compatibility': 'extended',
                'sorting_algorithm': 'energy_curve',
                'curve_type': 'buildup',
                'description': 'Sanfter Einstieg mit kontinuierlichem Aufbau'
            },
            'Cool Down': {
                'bpm_range': [110, 120],
                'energy_range': [0.2, 0.6],
                'moods': ['Dark', 'Experimental'],
                'key_compatibility': 'harmonic',
                'sorting_algorithm': 'energy_curve',
                'curve_type': 'breakdown',
                'description': 'Entspannter Ausklang mit Energie-Abbau'
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
        score += bmp_score * 0.4
        
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
            bpm_diffs.append(abs(bpm_curr - bmp_prev))
        
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