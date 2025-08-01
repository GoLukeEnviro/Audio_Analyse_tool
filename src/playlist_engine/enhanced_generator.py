"""Enhanced Playlist Generator - Erweiterte Playlist-Engine mit Energie-Kurven und Smart Suggestions"""

import numpy as np
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
from collections import deque
import heapq
import time

from .generator import PlaylistGenerator
from .camelot_wheel import CamelotWheel
from .rule_engine import RuleEngine
from .validator import PlaylistValidator, ValidationConfig
from ..audio_analysis.energy_score_extractor import EnergyScoreExtractor
from ..audio_analysis.smart_suggestions import SmartSuggestionsEngine
from ..audio_analysis.mood_classifier_enhanced import EnhancedMoodClassifier

logger = logging.getLogger(__name__)

@dataclass
class EnergyPoint:
    """Repräsentiert einen Punkt auf der Energie-Kurve"""
    position: float  # 0.0 - 1.0 (Position in der Playlist)
    energy: float    # 1.0 - 10.0 (Energie-Level)
    weight: float = 1.0  # Gewichtung für Curve-Matching
    tolerance: float = 0.5  # Toleranz für Abweichungen

@dataclass
class PlaylistSegment:
    """Segment einer Playlist mit spezifischen Eigenschaften"""
    start_position: float
    end_position: float
    target_energy_range: Tuple[float, float]
    mood_preference: Optional[str] = None
    key_preference: Optional[str] = None
    bpm_range: Optional[Tuple[float, float]] = None

class EnhancedPlaylistGenerator(PlaylistGenerator):
    """Erweiterte Playlist-Engine mit Energie-Kurven, Smart Suggestions und k-NN"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        super().__init__()
        
        # Erweiterte Komponenten
        self.energy_extractor = EnergyScoreExtractor()
        self.smart_suggestions = SmartSuggestionsEngine(cache_dir)
        self.mood_classifier = EnhancedMoodClassifier()
        
        # Energie-Kurven-System
        self.energy_curves = {
            'buildup': self._create_buildup_curve(),
            'peak_time': self._create_peak_time_curve(),
            'cool_down': self._create_cool_down_curve(),
            'wave': self._create_wave_curve(),
            'progressive': self._create_progressive_curve(),
            'custom': []
        }
        
        # Curve-Matching-Konfiguration
        self.curve_matching_config = {
            'beam_width': 5,
            'max_iterations': 100,
            'energy_weight': 0.4,
            'harmonic_weight': 0.3,
            'flow_weight': 0.2,
            'diversity_weight': 0.1
        }
        
        # Performance-Cache
        self._similarity_cache = {}
        self._energy_cache = {}
        self._max_cache_size = 1000
        
        # Playlist-Generierung-Statistiken
        self.generation_stats = {
            'total_generated': 0,
            'avg_generation_time': 0.0,
            'cache_hit_rate': 0.0,
            'curve_match_accuracy': 0.0
        }
    
    def _create_buildup_curve(self) -> List[EnergyPoint]:
        """Erstellt eine Buildup-Energie-Kurve"""
        return [
            EnergyPoint(0.0, 3.0, 1.0, 0.5),
            EnergyPoint(0.2, 4.5, 1.2, 0.4),
            EnergyPoint(0.5, 6.5, 1.5, 0.3),
            EnergyPoint(0.8, 8.5, 1.8, 0.2),
            EnergyPoint(1.0, 9.5, 2.0, 0.1)
        ]
    
    def _create_peak_time_curve(self) -> List[EnergyPoint]:
        """Erstellt eine Peak-Time-Energie-Kurve"""
        return [
            EnergyPoint(0.0, 8.0, 1.5, 0.3),
            EnergyPoint(0.25, 9.0, 2.0, 0.2),
            EnergyPoint(0.5, 9.5, 2.0, 0.1),
            EnergyPoint(0.75, 9.0, 2.0, 0.2),
            EnergyPoint(1.0, 8.5, 1.5, 0.3)
        ]
    
    def _create_cool_down_curve(self) -> List[EnergyPoint]:
        """Erstellt eine Cool-Down-Energie-Kurve"""
        return [
            EnergyPoint(0.0, 8.0, 1.5, 0.3),
            EnergyPoint(0.3, 6.5, 1.2, 0.4),
            EnergyPoint(0.6, 5.0, 1.0, 0.5),
            EnergyPoint(0.8, 3.5, 0.8, 0.6),
            EnergyPoint(1.0, 2.0, 0.5, 0.8)
        ]
    
    def _create_wave_curve(self) -> List[EnergyPoint]:
        """Erstellt eine Wellen-Energie-Kurve"""
        return [
            EnergyPoint(0.0, 5.0, 1.0, 0.5),
            EnergyPoint(0.15, 7.5, 1.5, 0.3),
            EnergyPoint(0.3, 5.5, 1.0, 0.4),
            EnergyPoint(0.5, 8.0, 1.8, 0.2),
            EnergyPoint(0.7, 6.0, 1.2, 0.4),
            EnergyPoint(0.85, 8.5, 2.0, 0.2),
            EnergyPoint(1.0, 6.5, 1.3, 0.3)
        ]
    
    def _create_progressive_curve(self) -> List[EnergyPoint]:
        """Erstellt eine Progressive-Energie-Kurve"""
        return [
            EnergyPoint(0.0, 4.0, 1.0, 0.4),
            EnergyPoint(0.2, 5.0, 1.1, 0.4),
            EnergyPoint(0.4, 6.0, 1.2, 0.3),
            EnergyPoint(0.6, 7.0, 1.4, 0.3),
            EnergyPoint(0.8, 8.0, 1.6, 0.2),
            EnergyPoint(1.0, 8.5, 1.8, 0.2)
        ]
    
    def generate_playlist_with_curve(self, 
                                   track_pool: List[Dict[str, Any]], 
                                   target_length: int,
                                   curve_type: str = 'progressive',
                                   custom_curve: Optional[List[EnergyPoint]] = None,
                                   constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generiert Playlist basierend auf Energie-Kurve"""
        start_time = time.time()
        
        # Wähle Energie-Kurve
        if custom_curve:
            energy_curve = custom_curve
        else:
            energy_curve = self.energy_curves.get(curve_type, self.energy_curves['progressive'])
        
        # Initialisiere Smart Suggestions mit Track-Pool
        self._populate_smart_suggestions(track_pool)
        
        # Beam-Search für optimale Playlist
        playlist = self._beam_search_playlist(
            track_pool=track_pool,
            target_length=target_length,
            energy_curve=energy_curve,
            constraints=constraints or {}
        )
        
        # Berechne Qualitäts-Metriken
        quality_metrics = self._calculate_playlist_quality(playlist, energy_curve)
        
        # Update Statistiken
        generation_time = time.time() - start_time
        self._update_generation_stats(generation_time, quality_metrics)
        
        # Nach Generierung validieren
        validator = PlaylistValidator(ValidationConfig(level=ValidationLevel.PROFESSIONAL))
        quality_score, issues = validator.validate(playlist)
        fixed_playlist = validator.apply_auto_fixes(playlist)
        # Update Playlist wenn Fixes angewendet
        if fixed_playlist != playlist:
            playlist = fixed_playlist
            quality_metrics = self._calculate_playlist_quality(playlist, energy_curve)
        return {
            'playlist': playlist,
            'curve_type': curve_type,
            'target_curve': energy_curve,
            'quality_metrics': quality_metrics,
            'validation': {
                'score': quality_score,
                'issues': issues,
                'report': validator.generate_report()
            },
            'generation_time': generation_time,
            'metadata': {
                'total_tracks': len(playlist),
                'avg_energy': np.mean([t.get('energy_score', 5) for t in playlist]),
                'energy_variance': np.var([t.get('energy_score', 5) for t in playlist]),
                'harmonic_transitions': self._count_harmonic_transitions(playlist)
            }
        }
    
    def _populate_smart_suggestions(self, track_pool: List[Dict[str, Any]]):
        """Fügt Tracks zur Smart Suggestions Engine hinzu"""
        for track in track_pool:
            track_id = track.get('id', track.get('file_path', str(hash(str(track)))))
            self.smart_suggestions.add_track(
                track_id=track_id,
                features=track,
                metadata=track.get('metadata', {})
            )
        
        # Trainiere Model
        self.smart_suggestions.fit_model()
    
    def _beam_search_playlist(self, 
                            track_pool: List[Dict[str, Any]], 
                            target_length: int,
                            energy_curve: List[EnergyPoint],
                            constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Beam-Search-Algorithmus für optimale Playlist-Generierung"""
        beam_width = self.curve_matching_config['beam_width']
        
        # Initialisiere Beam mit besten Start-Tracks
        initial_candidates = self._find_start_candidates(track_pool, energy_curve[0])
        beam = [([], 0.0, set()) for _ in range(min(beam_width, len(initial_candidates)))]
        
        for i, candidate in enumerate(initial_candidates[:beam_width]):
            beam[i] = ([candidate], self._calculate_track_score(candidate, energy_curve, 0), {candidate['id']})
        
        # Beam-Search Hauptschleife
        for position in range(1, target_length):
            new_beam = []
            
            for current_playlist, current_score, used_tracks in beam:
                if len(current_playlist) >= target_length:
                    new_beam.append((current_playlist, current_score, used_tracks))
                    continue
                
                # Finde nächste Kandidaten
                next_candidates = self._find_next_candidates(
                    current_playlist=current_playlist,
                    track_pool=track_pool,
                    energy_curve=energy_curve,
                    position=position,
                    used_tracks=used_tracks,
                    constraints=constraints
                )
                
                # Erweitere Beam
                for candidate in next_candidates[:3]:  # Top 3 pro Beam-Pfad
                    if candidate['id'] not in used_tracks:
                        new_playlist = current_playlist + [candidate]
                        new_score = self._calculate_playlist_score(new_playlist, energy_curve)
                        new_used = used_tracks | {candidate['id']}
                        new_beam.append((new_playlist, new_score, new_used))
            
            # Behalte beste Kandidaten
            new_beam.sort(key=lambda x: x[1], reverse=True)
            beam = new_beam[:beam_width]
        
        # Wähle beste Playlist
        if beam:
            best_playlist, best_score, _ = max(beam, key=lambda x: x[1])
            return best_playlist
        
        return []
    
    def _find_start_candidates(self, track_pool: List[Dict[str, Any]], 
                             start_point: EnergyPoint) -> List[Dict[str, Any]]:
        """Findet beste Start-Tracks für die Playlist"""
        candidates = []
        
        for track in track_pool:
            energy_score = track.get('energy_score', 5.0)
            energy_diff = abs(energy_score - start_point.energy)
            
            if energy_diff <= start_point.tolerance:
                score = 1.0 - (energy_diff / start_point.tolerance)
                candidates.append((track, score))
        
        # Sortiere nach Score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [track for track, score in candidates[:20]]
    
    def _find_next_candidates(self, 
                            current_playlist: List[Dict[str, Any]],
                            track_pool: List[Dict[str, Any]],
                            energy_curve: List[EnergyPoint],
                            position: int,
                            used_tracks: set,
                            constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Findet beste nächste Tracks basierend auf aktueller Playlist"""
        if not current_playlist:
            return []
        
        last_track = current_playlist[-1]
        target_energy = self._interpolate_energy_at_position(
            energy_curve, position / len(current_playlist)
        )
        
        # Smart Suggestions für harmonische Übergänge
        last_track_id = last_track.get('id', str(hash(str(last_track))))
        smart_suggestions = self.smart_suggestions.get_similar_tracks(
            target_track_id=last_track_id,
            n_suggestions=10,
            mode='harmonic'
        )
        
        # Kombiniere mit Energie-basierten Kandidaten
        energy_candidates = self._find_energy_candidates(
            track_pool, target_energy, used_tracks
        )
        
        # Merge und bewerte Kandidaten
        all_candidates = []
        
        # Smart Suggestions
        for suggestion in smart_suggestions:
            track = self._find_track_by_id(track_pool, suggestion['track_id'])
            if track and track['id'] not in used_tracks:
                score = self._calculate_transition_score(
                    last_track, track, target_energy, constraints
                )
                all_candidates.append((track, score))
        
        # Energie-Kandidaten
        for track in energy_candidates:
            if track['id'] not in used_tracks:
                score = self._calculate_transition_score(
                    last_track, track, target_energy, constraints
                )
                all_candidates.append((track, score))
        
        # Entferne Duplikate und sortiere
        unique_candidates = {}
        for track, score in all_candidates:
            track_id = track['id']
            if track_id not in unique_candidates or score > unique_candidates[track_id][1]:
                unique_candidates[track_id] = (track, score)
        
        sorted_candidates = sorted(unique_candidates.values(), key=lambda x: x[1], reverse=True)
        return [track for track, score in sorted_candidates[:15]]
    
    def _find_energy_candidates(self, track_pool: List[Dict[str, Any]], 
                              target_energy: float, used_tracks: set) -> List[Dict[str, Any]]:
        """Findet Tracks mit passender Energie"""
        candidates = []
        tolerance = 1.5
        
        for track in track_pool:
            if track['id'] in used_tracks:
                continue
            
            energy_score = track.get('energy_score', 5.0)
            energy_diff = abs(energy_score - target_energy)
            
            if energy_diff <= tolerance:
                candidates.append(track)
        
        return candidates
    
    def _find_track_by_id(self, track_pool: List[Dict[str, Any]], track_id: str) -> Optional[Dict[str, Any]]:
        """Findet Track anhand der ID"""
        for track in track_pool:
            if track.get('id') == track_id:
                return track
        return None
    
    def _interpolate_energy_at_position(self, energy_curve: List[EnergyPoint], position: float) -> float:
        """Interpoliert Energie-Wert an gegebener Position"""
        if not energy_curve:
            return 5.0
        
        # Finde umgebende Punkte
        for i in range(len(energy_curve) - 1):
            if energy_curve[i].position <= position <= energy_curve[i + 1].position:
                # Lineare Interpolation
                p1, p2 = energy_curve[i], energy_curve[i + 1]
                ratio = (position - p1.position) / (p2.position - p1.position)
                return p1.energy + ratio * (p2.energy - p1.energy)
        
        # Fallback: nächster Punkt
        closest_point = min(energy_curve, key=lambda p: abs(p.position - position))
        return closest_point.energy
    
    def _calculate_track_score(self, track: Dict[str, Any], 
                             energy_curve: List[EnergyPoint], position: int) -> float:
        """Berechnet Score für einzelnen Track an Position"""
        if not energy_curve:
            return 0.5
        
        # Normalisierte Position
        norm_position = position / max(len(energy_curve) - 1, 1)
        target_energy = self._interpolate_energy_at_position(energy_curve, norm_position)
        
        # Energie-Score
        track_energy = track.get('energy_score', 5.0)
        energy_diff = abs(track_energy - target_energy)
        energy_score = max(0, 1.0 - energy_diff / 5.0)
        
        # Mood-Score
        mood_score = self._calculate_mood_compatibility(track, target_energy)
        
        # Qualitäts-Score
        quality_score = track.get('quality_score', 0.7)
        
        # Gewichtete Kombination
        total_score = (
            energy_score * 0.5 +
            mood_score * 0.3 +
            quality_score * 0.2
        )
        
        return total_score
    
    def _calculate_playlist_score(self, playlist: List[Dict[str, Any]], 
                                energy_curve: List[EnergyPoint]) -> float:
        """Berechnet Gesamt-Score für Playlist"""
        if not playlist:
            return 0.0
        
        scores = []
        
        # Einzelne Track-Scores
        for i, track in enumerate(playlist):
            track_score = self._calculate_track_score(track, energy_curve, i)
            scores.append(track_score)
        
        # Übergangs-Scores
        transition_scores = []
        for i in range(len(playlist) - 1):
            transition_score = self._calculate_transition_quality(
                playlist[i], playlist[i + 1]
            )
            transition_scores.append(transition_score)
        
        # Kurven-Matching-Score
        curve_score = self._calculate_curve_matching_score(playlist, energy_curve)
        
        # Diversitäts-Score
        diversity_score = self._calculate_diversity_score(playlist)
        
        # Gewichtete Kombination
        avg_track_score = np.mean(scores) if scores else 0.0
        avg_transition_score = np.mean(transition_scores) if transition_scores else 0.0
        
        total_score = (
            avg_track_score * self.curve_matching_config['energy_weight'] +
            avg_transition_score * self.curve_matching_config['harmonic_weight'] +
            curve_score * self.curve_matching_config['flow_weight'] +
            diversity_score * self.curve_matching_config['diversity_weight']
        )
        
        return total_score
    
    def _calculate_transition_score(self, track1: Dict[str, Any], track2: Dict[str, Any], 
                                  target_energy: float, constraints: Dict[str, Any]) -> float:
        """Berechnet Score für Übergang zwischen zwei Tracks"""
        # Camelot-Kompatibilität
        key1 = track1.get('key', 'C major')
        key2 = track2.get('key', 'C major')
        camelot_score = self.camelot_wheel.get_compatibility_score(key1, key2)
        
        # BPM-Kompatibilität
        bpm1 = track1.get('bpm', 120)
        bpm2 = track2.get('bpm', 120)
        bpm_diff = abs(bpm1 - bpm2)
        bpm_score = max(0, 1.0 - bpm_diff / 20.0)  # Toleranz: 20 BPM
        
        # Energie-Übergang
        energy1 = track1.get('energy_score', 5.0)
        energy2 = track2.get('energy_score', 5.0)
        energy_transition = abs(energy2 - energy1)
        energy_score = max(0, 1.0 - energy_transition / 3.0)  # Toleranz: 3 Energie-Punkte
        
        # Ziel-Energie-Kompatibilität
        target_diff = abs(energy2 - target_energy)
        target_score = max(0, 1.0 - target_diff / 2.0)
        
        # Mood-Kompatibilität
        mood_score = self._calculate_mood_transition_score(track1, track2)
        
        # Gewichtete Kombination
        total_score = (
            camelot_score * 0.3 +
            bpm_score * 0.2 +
            energy_score * 0.2 +
            target_score * 0.2 +
            mood_score * 0.1
        )
        
        return total_score
    
    def _calculate_transition_quality(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """Berechnet Qualität des Übergangs zwischen zwei Tracks"""
        # Vereinfachte Version der Transition-Score-Berechnung
        key1 = track1.get('key', 'C major')
        key2 = track2.get('key', 'C major')
        camelot_score = self.camelot_wheel.get_compatibility_score(key1, key2)
        
        bpm1 = track1.get('bpm', 120)
        bpm2 = track2.get('bpm', 120)
        bpm_score = max(0, 1.0 - abs(bpm1 - bpm2) / 20.0)
        
        return (camelot_score + bpm_score) / 2.0
    
    def _calculate_curve_matching_score(self, playlist: List[Dict[str, Any]], 
                                      energy_curve: List[EnergyPoint]) -> float:
        """Berechnet wie gut die Playlist der Ziel-Kurve entspricht"""
        if not playlist or not energy_curve:
            return 0.0
        
        deviations = []
        
        for i, track in enumerate(playlist):
            position = i / max(len(playlist) - 1, 1)
            target_energy = self._interpolate_energy_at_position(energy_curve, position)
            actual_energy = track.get('energy_score', 5.0)
            
            deviation = abs(actual_energy - target_energy)
            deviations.append(deviation)
        
        # Berechne Score basierend auf durchschnittlicher Abweichung
        avg_deviation = np.mean(deviations)
        score = max(0, 1.0 - avg_deviation / 5.0)  # Normalisiert auf 0-1
        
        return score
    
    def _calculate_diversity_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Diversitäts-Score der Playlist"""
        if len(playlist) < 2:
            return 0.5
        
        # Energie-Diversität
        energies = [track.get('energy_score', 5.0) for track in playlist]
        energy_variance = np.var(energies)
        energy_diversity = min(1.0, energy_variance / 4.0)
        
        # Key-Diversität
        keys = [track.get('key', 'C major') for track in playlist]
        unique_keys = len(set(keys))
        key_diversity = min(1.0, unique_keys / min(len(playlist), 12))
        
        # BPM-Diversität
        bpms = [track.get('bpm', 120) for track in playlist]
        bpm_variance = np.var(bpms)
        bpm_diversity = min(1.0, bpm_variance / 400.0)
        
        # Kombiniere Diversitäts-Metriken
        total_diversity = (energy_diversity + key_diversity + bpm_diversity) / 3.0
        
        return total_diversity
    
    def _calculate_mood_compatibility(self, track: Dict[str, Any], target_energy: float) -> float:
        """Berechnet Mood-Kompatibilität für Ziel-Energie"""
        mood_features = track.get('mood', {})
        
        if target_energy >= 8.0:
            # Hohe Energie: Euphoric, Peak-Time
            return mood_features.get('euphoric', 0.5)
        elif target_energy >= 6.0:
            # Mittlere Energie: Driving
            return mood_features.get('driving', 0.5)
        elif target_energy >= 4.0:
            # Niedrige Energie: Progressive
            return (mood_features.get('progressive', 0.5) + mood_features.get('driving', 0.5)) / 2.0
        else:
            # Sehr niedrige Energie: Dark, Experimental
            return (mood_features.get('dark', 0.5) + mood_features.get('experimental', 0.5)) / 2.0
    
    def _calculate_mood_transition_score(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """Berechnet Mood-Übergangs-Score"""
        mood1 = track1.get('mood', {})
        mood2 = track2.get('mood', {})
        
        # Berechne Ähnlichkeit der Mood-Vektoren
        mood_keys = ['euphoric', 'dark', 'driving', 'experimental']
        
        similarities = []
        for key in mood_keys:
            val1 = mood1.get(key, 0.5)
            val2 = mood2.get(key, 0.5)
            similarity = 1.0 - abs(val1 - val2)
            similarities.append(similarity)
        
        return np.mean(similarities)
    
    def _calculate_playlist_quality(self, playlist: List[Dict[str, Any]], 
                                  energy_curve: List[EnergyPoint]) -> Dict[str, float]:
        """Berechnet umfassende Qualitäts-Metriken für Playlist"""
        if not playlist:
            return {'overall': 0.0}
        
        # Kurven-Matching
        curve_match = self._calculate_curve_matching_score(playlist, energy_curve)
        
        # Harmonische Übergänge
        harmonic_scores = []
        for i in range(len(playlist) - 1):
            score = self._calculate_transition_quality(playlist[i], playlist[i + 1])
            harmonic_scores.append(score)
        avg_harmonic = np.mean(harmonic_scores) if harmonic_scores else 0.0
        
        # Energie-Flow
        energy_flow = self._calculate_energy_flow_quality(playlist)
        
        # Diversität
        diversity = self._calculate_diversity_score(playlist)
        
        # Gesamt-Qualität
        overall = (
            curve_match * 0.4 +
            avg_harmonic * 0.3 +
            energy_flow * 0.2 +
            diversity * 0.1
        )
        
        return {
            'overall': overall,
            'curve_matching': curve_match,
            'harmonic_transitions': avg_harmonic,
            'energy_flow': energy_flow,
            'diversity': diversity
        }
    
    def _calculate_energy_flow_quality(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Qualität des Energie-Flows"""
        if len(playlist) < 2:
            return 0.5
        
        energies = [track.get('energy_score', 5.0) for track in playlist]
        
        # Berechne Energie-Übergänge
        transitions = []
        for i in range(len(energies) - 1):
            transition = energies[i + 1] - energies[i]
            transitions.append(transition)
        
        # Bewerte Smoothness (keine extremen Sprünge)
        extreme_jumps = sum(1 for t in transitions if abs(t) > 3.0)
        smoothness = 1.0 - (extreme_jumps / len(transitions))
        
        # Bewerte Progression (allgemeine Richtung)
        overall_progression = energies[-1] - energies[0]
        progression_score = min(1.0, abs(overall_progression) / 5.0)
        
        return (smoothness + progression_score) / 2.0
    
    def _count_harmonic_transitions(self, playlist: List[Dict[str, Any]]) -> int:
        """Zählt harmonische Übergänge in der Playlist"""
        harmonic_count = 0
        
        for i in range(len(playlist) - 1):
            key1 = playlist[i].get('key', 'C major')
            key2 = playlist[i + 1].get('key', 'C major')
            
            if self.camelot_wheel.are_compatible(key1, key2):
                harmonic_count += 1
        
        return harmonic_count
    
    def _update_generation_stats(self, generation_time: float, quality_metrics: Dict[str, float]):
        """Aktualisiert Generierungs-Statistiken"""
        self.generation_stats['total_generated'] += 1
        
        # Durchschnittliche Generierungszeit
        total = self.generation_stats['total_generated']
        current_avg = self.generation_stats['avg_generation_time']
        self.generation_stats['avg_generation_time'] = (
            (current_avg * (total - 1) + generation_time) / total
        )
        
        # Kurven-Match-Genauigkeit
        curve_accuracy = quality_metrics.get('curve_matching', 0.0)
        current_curve_avg = self.generation_stats['curve_match_accuracy']
        self.generation_stats['curve_match_accuracy'] = (
            (current_curve_avg * (total - 1) + curve_accuracy) / total
        )
    
    def get_surprise_me_playlist(self, 
                               track_pool: List[Dict[str, Any]], 
                               target_length: int,
                               context_tracks: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generiert überraschende aber passende Playlist"""
        # Initialisiere Smart Suggestions
        self._populate_smart_suggestions(track_pool)
        
        # Hole Surprise-Me-Tracks
        surprise_tracks = self.smart_suggestions.get_surprise_me_tracks(
            playlist_context=context_tracks or [],
            n_suggestions=target_length
        )
        
        # Konvertiere zu Playlist-Format
        playlist = []
        for surprise_track in surprise_tracks:
            track = self._find_track_by_id(track_pool, surprise_track['track_id'])
            if track:
                track['surprise_score'] = surprise_track['surprise_score']
                playlist.append(track)
        
        # Fülle auf falls nötig
        while len(playlist) < target_length and len(playlist) < len(track_pool):
            remaining_tracks = [t for t in track_pool if t['id'] not in [p['id'] for p in playlist]]
            if remaining_tracks:
                playlist.append(remaining_tracks[0])
            else:
                break
        
        return {
            'playlist': playlist[:target_length],
            'type': 'surprise_me',
            'metadata': {
                'avg_surprise_score': np.mean([t.get('surprise_score', 0.5) for t in playlist]),
                'total_tracks': len(playlist)
            }
        }
    
    def create_custom_curve(self, energy_points: List[Tuple[float, float]], 
                          name: str = 'custom') -> List[EnergyPoint]:
        """Erstellt benutzerdefinierte Energie-Kurve"""
        curve = []
        for position, energy in energy_points:
            # Validierung
            position = max(0.0, min(1.0, position))
            energy = max(1.0, min(10.0, energy))
            
            curve.append(EnergyPoint(
                position=position,
                energy=energy,
                weight=1.0,
                tolerance=0.5
            ))
        
        # Sortiere nach Position
        curve.sort(key=lambda p: p.position)
        
        # Speichere Kurve
        self.energy_curves[name] = curve
        
        return curve
    
    def analyze_playlist_segments(self, playlist: List[Dict[str, Any]]) -> List[PlaylistSegment]:
        """Analysiert Playlist und identifiziert Segmente"""
        if len(playlist) < 3:
            return []
        
        segments = []
        energies = [track.get('energy_score', 5.0) for track in playlist]
        
        # Finde Energie-Wendepunkte
        turning_points = [0]
        for i in range(1, len(energies) - 1):
            prev_trend = energies[i] - energies[i-1]
            next_trend = energies[i+1] - energies[i]
            
            # Wendepunkt wenn Trend sich ändert
            if (prev_trend > 0 and next_trend < 0) or (prev_trend < 0 and next_trend > 0):
                turning_points.append(i)
        
        turning_points.append(len(playlist) - 1)
        
        # Erstelle Segmente
        for i in range(len(turning_points) - 1):
            start_idx = turning_points[i]
            end_idx = turning_points[i + 1]
            
            segment_energies = energies[start_idx:end_idx + 1]
            energy_range = (min(segment_energies), max(segment_energies))
            
            segment = PlaylistSegment(
                start_position=start_idx / len(playlist),
                end_position=end_idx / len(playlist),
                target_energy_range=energy_range
            )
            
            segments.append(segment)
        
        return segments
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Gibt Generierungs-Statistiken zurück"""
        return self.generation_stats.copy()
    
    def clear_cache(self):
        """Löscht Performance-Caches"""
        self._similarity_cache.clear()
        self._energy_cache.clear()
        logger.info("Enhanced Playlist Generator Cache geleert")
    
    def export_curve(self, curve_name: str, file_path: str):
        """Exportiert Energie-Kurve als JSON"""
        if curve_name not in self.energy_curves:
            raise ValueError(f"Kurve '{curve_name}' nicht gefunden")
        
        curve = self.energy_curves[curve_name]
        curve_data = {
            'name': curve_name,
            'points': [
                {
                    'position': point.position,
                    'energy': point.energy,
                    'weight': point.weight,
                    'tolerance': point.tolerance
                }
                for point in curve
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(curve_data, f, indent=2)
        
        logger.info(f"Energie-Kurve '{curve_name}' exportiert nach {file_path}")
    
    def import_curve(self, file_path: str) -> str:
        """Importiert Energie-Kurve aus JSON"""
        with open(file_path, 'r') as f:
            curve_data = json.load(f)
        
        curve_name = curve_data['name']
        points = []
        
        for point_data in curve_data['points']:
            point = EnergyPoint(
                position=point_data['position'],
                energy=point_data['energy'],
                weight=point_data.get('weight', 1.0),
                tolerance=point_data.get('tolerance', 0.5)
            )
            points.append(point)
        
        self.energy_curves[curve_name] = points
        logger.info(f"Energie-Kurve '{curve_name}' importiert aus {file_path}")
        
        return curve_name