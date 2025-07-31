import json
import os
import math
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class SortingAlgorithm(Enum):
    """Verfügbare Sortieralgorithmen"""
    HARMONIC = "harmonic"  # Harmonische Kompatibilität (Camelot Wheel)
    ENERGY_FLOW = "energy_flow"  # Energie-Verlauf
    MOOD_PROGRESSION = "mood_progression"  # Stimmungs-Progression
    BPM_TRANSITION = "bpm_transition"  # BPM-Übergänge
    KEY_PROGRESSION = "key_progression"  # Tonart-Progression
    HYBRID_SMART = "hybrid_smart"  # Intelligente Kombination
    CUSTOM = "custom"  # Benutzerdefiniert

class MoodCategory(Enum):
    """Stimmungskategorien"""
    ENERGETIC = "energetic"
    HAPPY = "happy"
    CALM = "calm"
    MELANCHOLIC = "melancholic"
    AGGRESSIVE = "aggressive"
    ROMANTIC = "romantic"
    MYSTERIOUS = "mysterious"
    UPLIFTING = "uplifting"

@dataclass
class PlaylistRule:
    """Regel für Playlist-Generierung"""
    name: str
    description: str
    weight: float  # Gewichtung 0.0 - 1.0
    enabled: bool = True
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}

@dataclass
class PlaylistPreset:
    """Preset für Playlist-Konfiguration"""
    name: str
    description: str
    algorithm: SortingAlgorithm
    rules: List[PlaylistRule]
    target_duration_minutes: Optional[int] = None
    energy_curve: str = "gradual_build"  # gradual_build, peak_valley, steady, custom
    mood_flow: str = "coherent"  # coherent, contrasting, mixed
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

class PlaylistEngine:
    """Erweiterte Playlist-Engine mit intelligenten Sortieralgorithmen"""
    
    def __init__(self, presets_dir: str = None):
        self.presets_dir = presets_dir or os.path.join(os.path.expanduser("~"), ".dj_tool_presets")
        self._ensure_presets_dir()
        
        # Standard-Presets
        self.default_presets = self._create_default_presets()
        self.custom_presets = self._load_custom_presets()
        
        # Camelot Wheel Kompatibilitäts-Matrix
        self.camelot_compatibility = self._build_camelot_matrix()
        
        # Mood-Kompatibilitäts-Matrix
        self.mood_compatibility = self._build_mood_matrix()
    
    def _ensure_presets_dir(self):
        """Stellt sicher, dass das Presets-Verzeichnis existiert"""
        os.makedirs(self.presets_dir, exist_ok=True)
    
    def _create_default_presets(self) -> List[PlaylistPreset]:
        """Erstellt Standard-Presets"""
        presets = []
        
        # DJ Set - Harmonic Flow
        presets.append(PlaylistPreset(
            name="DJ Set - Harmonic Flow",
            description="Harmonische Übergänge für professionelle DJ-Sets",
            algorithm=SortingAlgorithm.HARMONIC,
            rules=[
                PlaylistRule("camelot_compatibility", "Bevorzuge harmonisch kompatible Keys", 0.8),
                PlaylistRule("bpm_transition", "Sanfte BPM-Übergänge (±5 BPM)", 0.6),
                PlaylistRule("energy_flow", "Gradueller Energie-Aufbau", 0.4),
                PlaylistRule("key_progression", "Quintenzirkel-Progression", 0.7)
            ],
            energy_curve="gradual_build",
            mood_flow="coherent"
        ))
        
        # Party Mix - Energy Build
        presets.append(PlaylistPreset(
            name="Party Mix - Energy Build",
            description="Energie-aufbauende Playlist für Partys",
            algorithm=SortingAlgorithm.ENERGY_FLOW,
            rules=[
                PlaylistRule("energy_progression", "Kontinuierlicher Energie-Aufbau", 0.9),
                PlaylistRule("danceability_priority", "Bevorzuge tanzbare Tracks", 0.8),
                PlaylistRule("bpm_acceleration", "BPM-Steigerung über Zeit", 0.7),
                PlaylistRule("mood_uplifting", "Positive Stimmung bevorzugen", 0.6)
            ],
            energy_curve="gradual_build",
            mood_flow="uplifting"
        ))
        
        # Chill Session
        presets.append(PlaylistPreset(
            name="Chill Session",
            description="Entspannte Playlist für ruhige Momente",
            algorithm=SortingAlgorithm.MOOD_PROGRESSION,
            rules=[
                PlaylistRule("low_energy_priority", "Bevorzuge ruhige Tracks", 0.8),
                PlaylistRule("mood_coherence", "Stimmungs-Kohärenz", 0.9),
                PlaylistRule("tempo_stability", "Stabile BPM (±3 BPM)", 0.7),
                PlaylistRule("valence_consistency", "Konsistente Valence", 0.6)
            ],
            energy_curve="steady",
            mood_flow="coherent"
        ))
        
        # Peak Time
        presets.append(PlaylistPreset(
            name="Peak Time",
            description="Hochenergetische Playlist für Prime Time",
            algorithm=SortingAlgorithm.HYBRID_SMART,
            rules=[
                PlaylistRule("high_energy_only", "Nur hochenergetische Tracks", 0.9),
                PlaylistRule("peak_bpm_range", "BPM 125-135", 0.8),
                PlaylistRule("crowd_favorites", "Bekannte Tracks bevorzugen", 0.7),
                PlaylistRule("harmonic_mixing", "Harmonische Übergänge", 0.6)
            ],
            energy_curve="peak_valley",
            mood_flow="energetic"
        ))
        
        return presets
    
    def _load_custom_presets(self) -> List[PlaylistPreset]:
        """Lädt benutzerdefinierte Presets"""
        presets = []
        presets_file = os.path.join(self.presets_dir, "custom_presets.json")
        
        try:
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for preset_data in data.get('presets', []):
                    rules = []
                    for rule_data in preset_data.get('rules', []):
                        rules.append(PlaylistRule(**rule_data))
                    
                    preset_data['rules'] = rules
                    preset_data['algorithm'] = SortingAlgorithm(preset_data['algorithm'])
                    presets.append(PlaylistPreset(**preset_data))
                    
        except Exception as e:
            logger.error(f"Fehler beim Laden der Custom Presets: {e}")
        
        return presets
    
    def _save_custom_presets(self):
        """Speichert benutzerdefinierte Presets"""
        presets_file = os.path.join(self.presets_dir, "custom_presets.json")
        
        try:
            data = {
                'version': '2.0',
                'created_at': datetime.now().isoformat(),
                'presets': []
            }
            
            for preset in self.custom_presets:
                preset_dict = asdict(preset)
                preset_dict['algorithm'] = preset.algorithm.value
                data['presets'].append(preset_dict)
            
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Custom Presets: {e}")
    
    def _build_camelot_matrix(self) -> Dict[str, List[str]]:
        """Erstellt Camelot-Kompatibilitäts-Matrix"""
        compatibility = {}
        
        # Alle Camelot-Keys
        for i in range(1, 13):
            for letter in ['A', 'B']:
                key = f"{i}{letter}"
                compatible = []
                
                # Gleiche Nummer, andere Modalität
                other_letter = 'B' if letter == 'A' else 'A'
                compatible.append(f"{i}{other_letter}")
                
                # +1 und -1 (Quintenzirkel)
                next_num = (i % 12) + 1
                prev_num = ((i - 2) % 12) + 1
                compatible.extend([f"{next_num}{letter}", f"{prev_num}{letter}"])
                
                # Erweiterte Kompatibilität (+2, -2)
                next2_num = ((i + 1) % 12) + 1
                prev2_num = ((i - 3) % 12) + 1
                compatible.extend([f"{next2_num}{letter}", f"{prev2_num}{letter}"])
                
                compatibility[key] = compatible
        
        return compatibility
    
    def _build_mood_matrix(self) -> Dict[str, Dict[str, float]]:
        """Erstellt Mood-Kompatibilitäts-Matrix"""
        moods = [mood.value for mood in MoodCategory]
        compatibility = {}
        
        # Kompatibilitäts-Scores zwischen Stimmungen (0.0 - 1.0)
        mood_scores = {
            'energetic': {'energetic': 1.0, 'happy': 0.8, 'uplifting': 0.9, 'aggressive': 0.6, 'calm': 0.2, 'melancholic': 0.1, 'romantic': 0.3, 'mysterious': 0.4},
            'happy': {'happy': 1.0, 'energetic': 0.8, 'uplifting': 0.9, 'romantic': 0.7, 'calm': 0.6, 'aggressive': 0.3, 'melancholic': 0.2, 'mysterious': 0.3},
            'calm': {'calm': 1.0, 'romantic': 0.8, 'melancholic': 0.6, 'mysterious': 0.7, 'happy': 0.6, 'uplifting': 0.4, 'energetic': 0.2, 'aggressive': 0.1},
            'melancholic': {'melancholic': 1.0, 'calm': 0.6, 'mysterious': 0.8, 'romantic': 0.5, 'aggressive': 0.3, 'happy': 0.2, 'energetic': 0.1, 'uplifting': 0.2},
            'aggressive': {'aggressive': 1.0, 'energetic': 0.6, 'mysterious': 0.5, 'melancholic': 0.3, 'uplifting': 0.2, 'happy': 0.3, 'calm': 0.1, 'romantic': 0.1},
            'romantic': {'romantic': 1.0, 'calm': 0.8, 'happy': 0.7, 'melancholic': 0.5, 'mysterious': 0.6, 'uplifting': 0.6, 'energetic': 0.3, 'aggressive': 0.1},
            'mysterious': {'mysterious': 1.0, 'melancholic': 0.8, 'calm': 0.7, 'romantic': 0.6, 'aggressive': 0.5, 'energetic': 0.4, 'happy': 0.3, 'uplifting': 0.3},
            'uplifting': {'uplifting': 1.0, 'happy': 0.9, 'energetic': 0.9, 'romantic': 0.6, 'calm': 0.4, 'mysterious': 0.3, 'melancholic': 0.2, 'aggressive': 0.2}
        }
        
        return mood_scores
    
    def create_playlist(self, tracks: List[Dict], preset_name: str = None, 
                      custom_rules: List[PlaylistRule] = None, 
                      target_duration: int = None) -> Dict:
        """Erstellt eine optimierte Playlist"""
        
        if not tracks:
            return {'error': 'Keine Tracks verfügbar'}
        
        # Preset auswählen
        preset = self._get_preset(preset_name) if preset_name else self.default_presets[0]
        if not preset:
            return {'error': f'Preset "{preset_name}" nicht gefunden'}
        
        # Custom Rules überschreiben Preset-Rules
        rules = custom_rules if custom_rules else preset.rules
        
        # Tracks filtern und vorbereiten
        valid_tracks = self._prepare_tracks(tracks)
        if not valid_tracks:
            return {'error': 'Keine gültigen Tracks gefunden'}
        
        # Sortieralgorithmus anwenden
        sorted_tracks = self._apply_sorting_algorithm(valid_tracks, preset.algorithm, rules)
        
        # Zieldauer berücksichtigen
        if target_duration or preset.target_duration_minutes:
            duration = target_duration or preset.target_duration_minutes
            sorted_tracks = self._trim_to_duration(sorted_tracks, duration * 60)
        
        # Playlist-Metadaten berechnen
        metadata = self._calculate_playlist_metadata(sorted_tracks, preset)
        
        return {
            'tracks': sorted_tracks,
            'metadata': metadata,
            'preset_used': preset.name,
            'algorithm': preset.algorithm.value,
            'created_at': datetime.now().isoformat()
        }
    
    def _get_preset(self, name: str) -> Optional[PlaylistPreset]:
        """Findet ein Preset nach Name"""
        all_presets = self.default_presets + self.custom_presets
        return next((p for p in all_presets if p.name == name), None)
    
    def _prepare_tracks(self, tracks: List[Dict]) -> List[Dict]:
        """Bereitet Tracks für die Sortierung vor"""
        valid_tracks = []
        
        for track in tracks:
            # Prüfe ob notwendige Features vorhanden sind
            features = track.get('features', {})
            if not features:
                continue
            
            # Normalisiere und validiere Features
            normalized_track = track.copy()
            normalized_features = self._normalize_features(features)
            normalized_track['features'] = normalized_features
            
            # Berechne abgeleitete Metriken
            normalized_track['derived_metrics'] = self._calculate_derived_metrics(normalized_features)
            
            valid_tracks.append(normalized_track)
        
        return valid_tracks
    
    def _normalize_features(self, features: Dict) -> Dict:
        """Normalisiert Audio-Features"""
        normalized = features.copy()
        
        # Stelle sicher, dass alle wichtigen Features vorhanden sind
        defaults = {
            'energy': 0.5,
            'valence': 0.5,
            'danceability': 0.5,
            'tempo': 0.5,
            'key': 0.0,
            'mode': 0.0,
            'loudness': 0.5
        }
        
        for key, default_value in defaults.items():
            if key not in normalized:
                normalized[key] = default_value
            else:
                # Stelle sicher, dass Werte im Bereich [0, 1] sind
                normalized[key] = max(0.0, min(1.0, float(normalized[key])))
        
        return normalized
    
    def _calculate_derived_metrics(self, features: Dict) -> Dict:
        """Berechnet abgeleitete Metriken"""
        metrics = {}
        
        # Energie-Level Kategorisierung
        energy = features.get('energy', 0.5)
        if energy < 0.3:
            metrics['energy_level'] = 'low'
        elif energy < 0.7:
            metrics['energy_level'] = 'medium'
        else:
            metrics['energy_level'] = 'high'
        
        # BPM-Kategorie
        tempo_normalized = features.get('tempo', 0.5)
        bpm_estimated = tempo_normalized * 200  # Rückkonvertierung
        
        if bpm_estimated < 90:
            metrics['bpm_category'] = 'slow'
        elif bpm_estimated < 120:
            metrics['bpm_category'] = 'medium'
        elif bpm_estimated < 140:
            metrics['bpm_category'] = 'fast'
        else:
            metrics['bpm_category'] = 'very_fast'
        
        # Mood-Schätzung basierend auf Features
        valence = features.get('valence', 0.5)
        energy = features.get('energy', 0.5)
        
        if energy > 0.7 and valence > 0.6:
            metrics['estimated_mood'] = 'energetic'
        elif energy < 0.4 and valence > 0.6:
            metrics['estimated_mood'] = 'happy'
        elif energy < 0.4 and valence < 0.4:
            metrics['estimated_mood'] = 'melancholic'
        elif energy > 0.6 and valence < 0.4:
            metrics['estimated_mood'] = 'aggressive'
        else:
            metrics['estimated_mood'] = 'neutral'
        
        return metrics
    
    def _apply_sorting_algorithm(self, tracks: List[Dict], algorithm: SortingAlgorithm, 
                               rules: List[PlaylistRule]) -> List[Dict]:
        """Wendet den gewählten Sortieralgorithmus an"""
        
        if algorithm == SortingAlgorithm.HARMONIC:
            return self._sort_harmonic(tracks, rules)
        elif algorithm == SortingAlgorithm.ENERGY_FLOW:
            return self._sort_energy_flow(tracks, rules)
        elif algorithm == SortingAlgorithm.MOOD_PROGRESSION:
            return self._sort_mood_progression(tracks, rules)
        elif algorithm == SortingAlgorithm.BPM_TRANSITION:
            return self._sort_bpm_transition(tracks, rules)
        elif algorithm == SortingAlgorithm.KEY_PROGRESSION:
            return self._sort_key_progression(tracks, rules)
        elif algorithm == SortingAlgorithm.HYBRID_SMART:
            return self._sort_hybrid_smart(tracks, rules)
        else:
            return self._sort_custom(tracks, rules)
    
    def _sort_harmonic(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert nach harmonischer Kompatibilität"""
        if not tracks:
            return []
        
        # Starte mit dem ersten Track
        sorted_tracks = [tracks[0]]
        remaining_tracks = tracks[1:]
        
        while remaining_tracks:
            current_track = sorted_tracks[-1]
            current_camelot = self._get_camelot_from_track(current_track)
            
            # Finde den besten nächsten Track
            best_track = None
            best_score = -1
            
            for track in remaining_tracks:
                track_camelot = self._get_camelot_from_track(track)
                score = self._calculate_harmonic_score(current_camelot, track_camelot, rules)
                
                if score > best_score:
                    best_score = score
                    best_track = track
            
            if best_track:
                sorted_tracks.append(best_track)
                remaining_tracks.remove(best_track)
            else:
                # Fallback: nimm den ersten verfügbaren Track
                sorted_tracks.append(remaining_tracks.pop(0))
        
        return sorted_tracks
    
    def _sort_energy_flow(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert nach Energie-Verlauf"""
        # Sortiere Tracks nach Energie
        energy_rule = next((r for r in rules if 'energy' in r.name.lower()), None)
        
        if energy_rule and 'progression' in energy_rule.name.lower():
            # Aufsteigender Energie-Verlauf
            return sorted(tracks, key=lambda t: t['features'].get('energy', 0.5))
        else:
            # Standard: Energie-optimierte Reihenfolge
            return self._optimize_energy_flow(tracks, rules)
    
    def _optimize_energy_flow(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Optimiert den Energie-Verlauf"""
        if not tracks:
            return []
        
        # Gruppiere Tracks nach Energie-Level
        low_energy = [t for t in tracks if t['features'].get('energy', 0.5) < 0.4]
        med_energy = [t for t in tracks if 0.4 <= t['features'].get('energy', 0.5) < 0.7]
        high_energy = [t for t in tracks if t['features'].get('energy', 0.5) >= 0.7]
        
        # Sortiere jede Gruppe intern
        low_energy.sort(key=lambda t: t['features'].get('energy', 0.5))
        med_energy.sort(key=lambda t: t['features'].get('energy', 0.5))
        high_energy.sort(key=lambda t: t['features'].get('energy', 0.5))
        
        # Kombiniere für graduellen Aufbau
        return low_energy + med_energy + high_energy
    
    def _sort_mood_progression(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert nach Stimmungs-Progression"""
        # Implementierung der Mood-basierten Sortierung
        return self._create_mood_flow(tracks, rules)
    
    def _create_mood_flow(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Erstellt einen kohärenten Stimmungs-Verlauf"""
        if not tracks:
            return []
        
        # Gruppiere nach geschätzter Stimmung
        mood_groups = {}
        for track in tracks:
            mood = track.get('derived_metrics', {}).get('estimated_mood', 'neutral')
            if mood not in mood_groups:
                mood_groups[mood] = []
            mood_groups[mood].append(track)
        
        # Erstelle Stimmungs-Progression
        mood_order = ['calm', 'happy', 'energetic', 'aggressive']  # Beispiel-Progression
        sorted_tracks = []
        
        for mood in mood_order:
            if mood in mood_groups:
                sorted_tracks.extend(mood_groups[mood])
        
        # Füge übrige Stimmungen hinzu
        for mood, tracks_list in mood_groups.items():
            if mood not in mood_order:
                sorted_tracks.extend(tracks_list)
        
        return sorted_tracks
    
    def _sort_bpm_transition(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert für sanfte BPM-Übergänge"""
        if not tracks:
            return []
        
        # Starte mit mittlerem BPM
        tracks_by_bpm = sorted(tracks, key=lambda t: t['features'].get('tempo', 0.5))
        start_index = len(tracks_by_bpm) // 2
        
        sorted_tracks = [tracks_by_bpm[start_index]]
        remaining = tracks_by_bpm[:start_index] + tracks_by_bpm[start_index+1:]
        
        while remaining:
            current_bpm = sorted_tracks[-1]['features'].get('tempo', 0.5)
            
            # Finde Track mit ähnlichstem BPM
            best_track = min(remaining, key=lambda t: abs(t['features'].get('tempo', 0.5) - current_bpm))
            
            sorted_tracks.append(best_track)
            remaining.remove(best_track)
        
        return sorted_tracks
    
    def _sort_key_progression(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert nach Tonart-Progression (Quintenzirkel)"""
        # Ähnlich wie harmonic, aber fokussiert auf Quintenzirkel
        return self._sort_harmonic(tracks, rules)
    
    def _sort_hybrid_smart(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Intelligente Kombination aller Algorithmen"""
        if not tracks:
            return []
        
        # Gewichtete Kombination verschiedener Scores
        scored_tracks = []
        
        for i, track in enumerate(tracks):
            score = 0.0
            
            # Harmonic Score (wenn nicht erster Track)
            if i > 0:
                prev_camelot = self._get_camelot_from_track(tracks[i-1])
                curr_camelot = self._get_camelot_from_track(track)
                harmonic_score = self._calculate_harmonic_score(prev_camelot, curr_camelot, rules)
                score += harmonic_score * 0.3
            
            # Energy Score
            energy = track['features'].get('energy', 0.5)
            energy_score = energy  # Bevorzuge höhere Energie
            score += energy_score * 0.25
            
            # Danceability Score
            danceability = track['features'].get('danceability', 0.5)
            score += danceability * 0.25
            
            # Valence Score
            valence = track['features'].get('valence', 0.5)
            score += valence * 0.2
            
            scored_tracks.append((track, score))
        
        # Sortiere nach Score
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        
        return [track for track, score in scored_tracks]
    
    def _sort_custom(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Benutzerdefinierte Sortierung basierend auf Regeln"""
        # Implementiere benutzerdefinierte Sortierlogik
        return tracks  # Placeholder
    
    def _get_camelot_from_track(self, track: Dict) -> str:
        """Extrahiert Camelot-Key aus Track"""
        camelot_info = track.get('camelot', {})
        if isinstance(camelot_info, dict):
            return camelot_info.get('camelot', '1A')
        return '1A'  # Fallback
    
    def _calculate_harmonic_score(self, camelot1: str, camelot2: str, rules: List[PlaylistRule]) -> float:
        """Berechnet harmonischen Kompatibilitäts-Score"""
        if camelot1 == camelot2:
            return 1.0
        
        compatible_keys = self.camelot_compatibility.get(camelot1, [])
        
        if camelot2 in compatible_keys:
            # Gewichtung basierend auf Kompatibilitäts-Typ
            if camelot2 == f"{camelot1[:-1]}{'B' if camelot1[-1] == 'A' else 'A'}":
                return 0.9  # Relative Dur/Moll
            else:
                return 0.7  # Quintenzirkel
        
        return 0.1  # Nicht kompatibel
    
    def _trim_to_duration(self, tracks: List[Dict], target_seconds: int) -> List[Dict]:
        """Kürzt Playlist auf Zieldauer"""
        total_duration = 0
        trimmed_tracks = []
        
        for track in tracks:
            track_duration = track.get('metadata', {}).get('duration', 180)  # 3min default
            
            if total_duration + track_duration <= target_seconds:
                trimmed_tracks.append(track)
                total_duration += track_duration
            else:
                break
        
        return trimmed_tracks
    
    def _calculate_playlist_metadata(self, tracks: List[Dict], preset: PlaylistPreset) -> Dict:
        """Berechnet Playlist-Metadaten"""
        if not tracks:
            return {}
        
        total_duration = sum(t.get('metadata', {}).get('duration', 180) for t in tracks)
        
        # Durchschnittliche Features
        avg_energy = np.mean([t['features'].get('energy', 0.5) for t in tracks])
        avg_valence = np.mean([t['features'].get('valence', 0.5) for t in tracks])
        avg_danceability = np.mean([t['features'].get('danceability', 0.5) for t in tracks])
        avg_tempo = np.mean([t['features'].get('tempo', 0.5) for t in tracks])
        
        # BPM-Bereich
        bpms = [t['features'].get('tempo', 0.5) * 200 for t in tracks]  # Rückkonvertierung
        min_bpm = min(bpms)
        max_bpm = max(bpms)
        
        # Key-Verteilung
        keys = [self._get_camelot_from_track(t) for t in tracks]
        key_distribution = {}
        for key in keys:
            key_distribution[key] = key_distribution.get(key, 0) + 1
        
        return {
            'total_tracks': len(tracks),
            'total_duration_seconds': total_duration,
            'total_duration_minutes': total_duration / 60,
            'average_energy': float(avg_energy),
            'average_valence': float(avg_valence),
            'average_danceability': float(avg_danceability),
            'average_tempo_normalized': float(avg_tempo),
            'bpm_range': {'min': float(min_bpm), 'max': float(max_bpm)},
            'key_distribution': key_distribution,
            'preset_name': preset.name,
            'energy_curve': preset.energy_curve,
            'mood_flow': preset.mood_flow
        }
    
    def get_all_presets(self) -> List[PlaylistPreset]:
        """Gibt alle verfügbaren Presets zurück"""
        return self.default_presets + self.custom_presets
    
    def save_custom_preset(self, preset: PlaylistPreset) -> bool:
        """Speichert ein benutzerdefiniertes Preset"""
        try:
            # Prüfe ob Preset bereits existiert
            existing = next((p for p in self.custom_presets if p.name == preset.name), None)
            
            if existing:
                # Aktualisiere existierendes Preset
                index = self.custom_presets.index(existing)
                self.custom_presets[index] = preset
            else:
                # Füge neues Preset hinzu
                self.custom_presets.append(preset)
            
            self._save_custom_presets()
            logger.info(f"Preset '{preset.name}' gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Presets: {e}")
            return False
    
    def delete_custom_preset(self, preset_name: str) -> bool:
        """Löscht ein benutzerdefiniertes Preset"""
        try:
            preset = next((p for p in self.custom_presets if p.name == preset_name), None)
            
            if preset:
                self.custom_presets.remove(preset)
                self._save_custom_presets()
                logger.info(f"Preset '{preset_name}' gelöscht")
                return True
            else:
                logger.warning(f"Preset '{preset_name}' nicht gefunden")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Presets: {e}")
            return False
    
    def export_preset(self, preset_name: str, export_path: str) -> bool:
        """Exportiert ein Preset in eine Datei"""
        try:
            preset = self._get_preset(preset_name)
            if not preset:
                return False
            
            export_data = {
                'version': '2.0',
                'exported_at': datetime.now().isoformat(),
                'preset': asdict(preset)
            }
            export_data['preset']['algorithm'] = preset.algorithm.value
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Preset '{preset_name}' nach {export_path} exportiert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Preset-Export: {e}")
            return False
    
    def import_preset(self, import_path: str) -> bool:
        """Importiert ein Preset aus einer Datei"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preset_data = data.get('preset', {})
            if not preset_data:
                return False
            
            # Konvertiere Rules
            rules = []
            for rule_data in preset_data.get('rules', []):
                rules.append(PlaylistRule(**rule_data))
            
            preset_data['rules'] = rules
            preset_data['algorithm'] = SortingAlgorithm(preset_data['algorithm'])
            
            preset = PlaylistPreset(**preset_data)
            
            return self.save_custom_preset(preset)
            
        except Exception as e:
            logger.error(f"Fehler beim Preset-Import: {e}")
            return False