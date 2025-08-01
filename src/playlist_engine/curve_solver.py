"""Curve Matching Solver - Beam-Search-Algorithmus für optimale Playlist-Generierung"""

import numpy as np
import heapq
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

@dataclass
class SolverState:
    """Zustand des Curve-Matching-Solvers"""
    playlist: List[Dict[str, Any]] = field(default_factory=list)
    used_tracks: Set[str] = field(default_factory=set)
    current_score: float = 0.0
    position: int = 0
    energy_deviation: float = 0.0
    harmonic_score: float = 0.0
    flow_score: float = 0.0
    
    def __lt__(self, other):
        return self.current_score > other.current_score  # Für Max-Heap

@dataclass
class SolverConfig:
    """Konfiguration für den Curve-Matching-Solver"""
    beam_width: int = 5
    max_iterations: int = 100
    energy_weight: float = 0.4
    harmonic_weight: float = 0.3
    flow_weight: float = 0.2
    diversity_weight: float = 0.1
    early_stopping_threshold: float = 0.95
    parallel_processing: bool = True
    max_workers: int = 4
    cache_enabled: bool = True
    pruning_enabled: bool = True
    pruning_threshold: float = 0.1

class CurveMatchingSolver:
    """Erweiterte Beam-Search-Engine für optimale Playlist-Generierung"""
    
    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
        
        # Performance-Caches
        self._transition_cache = {}
        self._energy_cache = {}
        self._similarity_cache = {}
        self._max_cache_size = 10000
        
        # Statistiken
        self.solver_stats = {
            'total_solves': 0,
            'avg_solve_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'pruned_states': 0,
            'best_scores': []
        }
        
        # Thread-Safety
        self._cache_lock = threading.Lock()
        
        logger.info(f"CurveMatchingSolver initialisiert mit Beam-Width: {self.config.beam_width}")
    
    def solve_optimal_playlist(self, 
                             track_pool: List[Dict[str, Any]],
                             energy_curve: List[Any],
                             target_length: int,
                             constraints: Optional[Dict[str, Any]] = None,
                             seed_tracks: Optional[List[str]] = None) -> Dict[str, Any]:
        """Löst optimale Playlist mit Beam-Search-Algorithmus"""
        start_time = time.time()
        
        # Validierung
        if not track_pool or target_length <= 0:
            return {'playlist': [], 'score': 0.0, 'metadata': {}}
        
        # Initialisierung
        constraints = constraints or {}
        initial_states = self._initialize_beam(track_pool, energy_curve, seed_tracks)
        
        # Beam-Search Hauptschleife
        best_solution = self._beam_search_loop(
            initial_states=initial_states,
            track_pool=track_pool,
            energy_curve=energy_curve,
            target_length=target_length,
            constraints=constraints
        )
        
        # Ergebnis-Verarbeitung
        solve_time = time.time() - start_time
        self._update_solver_stats(solve_time, best_solution.current_score)
        
        return {
            'playlist': best_solution.playlist,
            'score': best_solution.current_score,
            'metadata': {
                'solve_time': solve_time,
                'energy_deviation': best_solution.energy_deviation,
                'harmonic_score': best_solution.harmonic_score,
                'flow_score': best_solution.flow_score,
                'iterations': min(target_length, self.config.max_iterations),
                'beam_width_used': self.config.beam_width
            }
        }
    
    def _initialize_beam(self, 
                        track_pool: List[Dict[str, Any]], 
                        energy_curve: List[Any],
                        seed_tracks: Optional[List[str]] = None) -> List[SolverState]:
        """Initialisiert Beam mit besten Start-Zuständen"""
        initial_states = []
        
        if seed_tracks:
            # Verwende Seed-Tracks als Startpunkte
            for track_id in seed_tracks[:self.config.beam_width]:
                track = self._find_track_by_id(track_pool, track_id)
                if track:
                    state = SolverState(
                        playlist=[track],
                        used_tracks={track['id']},
                        current_score=self._calculate_initial_score(track, energy_curve),
                        position=1
                    )
                    initial_states.append(state)
        else:
            # Finde beste Start-Tracks basierend auf Energie-Kurve
            start_candidates = self._find_start_candidates(track_pool, energy_curve)
            
            for i, (track, score) in enumerate(start_candidates[:self.config.beam_width]):
                state = SolverState(
                    playlist=[track],
                    used_tracks={track['id']},
                    current_score=score,
                    position=1
                )
                initial_states.append(state)
        
        # Fülle Beam auf falls nötig
        while len(initial_states) < self.config.beam_width and len(initial_states) < len(track_pool):
            remaining_tracks = [
                t for t in track_pool 
                if t['id'] not in {s.used_tracks for s in initial_states for s in [s]}
            ]
            if remaining_tracks:
                track = remaining_tracks[0]
                state = SolverState(
                    playlist=[track],
                    used_tracks={track['id']},
                    current_score=0.5,
                    position=1
                )
                initial_states.append(state)
            else:
                break
        
        return initial_states
    
    def _beam_search_loop(self, 
                         initial_states: List[SolverState],
                         track_pool: List[Dict[str, Any]],
                         energy_curve: List[Any],
                         target_length: int,
                         constraints: Dict[str, Any]) -> SolverState:
        """Hauptschleife des Beam-Search-Algorithmus"""
        current_beam = initial_states
        best_solution = max(current_beam, key=lambda s: s.current_score) if current_beam else SolverState()
        
        for iteration in range(target_length - 1):  # -1 weil wir bereits einen Track haben
            if not current_beam:
                break
            
            # Generiere nächste Zustände
            next_beam = self._expand_beam(
                current_beam=current_beam,
                track_pool=track_pool,
                energy_curve=energy_curve,
                target_position=iteration + 1,
                target_length=target_length,
                constraints=constraints
            )
            
            # Pruning und Selektion
            if self.config.pruning_enabled:
                next_beam = self._prune_beam(next_beam)
            
            current_beam = self._select_best_states(next_beam, self.config.beam_width)
            
            # Update beste Lösung
            if current_beam:
                current_best = max(current_beam, key=lambda s: s.current_score)
                if current_best.current_score > best_solution.current_score:
                    best_solution = current_best
            
            # Early Stopping
            if (best_solution.current_score >= self.config.early_stopping_threshold and 
                len(best_solution.playlist) >= target_length * 0.8):
                logger.info(f"Early stopping bei Iteration {iteration}, Score: {best_solution.current_score:.3f}")
                break
        
        return best_solution
    
    def _expand_beam(self, 
                    current_beam: List[SolverState],
                    track_pool: List[Dict[str, Any]],
                    energy_curve: List[Any],
                    target_position: int,
                    target_length: int,
                    constraints: Dict[str, Any]) -> List[SolverState]:
        """Erweitert Beam um nächste mögliche Zustände"""
        next_states = []
        
        if self.config.parallel_processing and len(current_beam) > 2:
            # Parallele Verarbeitung
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                
                for state in current_beam:
                    future = executor.submit(
                        self._expand_single_state,
                        state, track_pool, energy_curve, target_position, target_length, constraints
                    )
                    futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        state_expansions = future.result()
                        next_states.extend(state_expansions)
                    except Exception as e:
                        logger.error(f"Fehler bei paralleler Beam-Expansion: {e}")
        else:
            # Sequenzielle Verarbeitung
            for state in current_beam:
                state_expansions = self._expand_single_state(
                    state, track_pool, energy_curve, target_position, target_length, constraints
                )
                next_states.extend(state_expansions)
        
        return next_states
    
    def _expand_single_state(self, 
                           state: SolverState,
                           track_pool: List[Dict[str, Any]],
                           energy_curve: List[Any],
                           target_position: int,
                           target_length: int,
                           constraints: Dict[str, Any]) -> List[SolverState]:
        """Erweitert einzelnen Zustand um mögliche nächste Tracks"""
        if len(state.playlist) >= target_length:
            return [state]
        
        expansions = []
        last_track = state.playlist[-1] if state.playlist else None
        
        # Finde Kandidaten für nächsten Track
        candidates = self._find_next_candidates(
            current_state=state,
            track_pool=track_pool,
            energy_curve=energy_curve,
            target_position=target_position,
            constraints=constraints
        )
        
        # Erstelle neue Zustände
        for candidate, candidate_score in candidates[:5]:  # Top 5 pro Zustand
            if candidate['id'] not in state.used_tracks:
                new_state = self._create_new_state(
                    parent_state=state,
                    new_track=candidate,
                    energy_curve=energy_curve,
                    target_position=target_position
                )
                expansions.append(new_state)
        
        return expansions
    
    def _find_next_candidates(self, 
                            current_state: SolverState,
                            track_pool: List[Dict[str, Any]],
                            energy_curve: List[Any],
                            target_position: int,
                            constraints: Dict[str, Any]) -> List[Tuple[Dict[str, Any], float]]:
        """Findet beste Kandidaten für nächsten Track"""
        if not current_state.playlist:
            return [(track, 0.5) for track in track_pool[:10]]
        
        last_track = current_state.playlist[-1]
        target_energy = self._get_target_energy_at_position(energy_curve, target_position, len(energy_curve))
        
        candidates = []
        
        for track in track_pool:
            if track['id'] in current_state.used_tracks:
                continue
            
            # Berechne Kandidaten-Score
            candidate_score = self._calculate_candidate_score(
                last_track=last_track,
                candidate_track=track,
                target_energy=target_energy,
                current_state=current_state,
                constraints=constraints
            )
            
            candidates.append((track, candidate_score))
        
        # Sortiere nach Score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return candidates
    
    def _calculate_candidate_score(self, 
                                 last_track: Dict[str, Any],
                                 candidate_track: Dict[str, Any],
                                 target_energy: float,
                                 current_state: SolverState,
                                 constraints: Dict[str, Any]) -> float:
        """Berechnet Score für Kandidaten-Track"""
        # Cache-Key für Performance
        cache_key = (
            last_track['id'], 
            candidate_track['id'], 
            round(target_energy, 1)
        )
        
        if self.config.cache_enabled:
            with self._cache_lock:
                if cache_key in self._transition_cache:
                    self.solver_stats['cache_hits'] += 1
                    return self._transition_cache[cache_key]
                else:
                    self.solver_stats['cache_misses'] += 1
        
        # Energie-Kompatibilität
        candidate_energy = candidate_track.get('energy_score', 5.0)
        energy_diff = abs(candidate_energy - target_energy)
        energy_score = max(0, 1.0 - energy_diff / 5.0)
        
        # Harmonische Kompatibilität
        harmonic_score = self._calculate_harmonic_compatibility(
            last_track, candidate_track
        )
        
        # Flow-Kompatibilität
        flow_score = self._calculate_flow_compatibility(
            last_track, candidate_track, current_state
        )
        
        # Diversitäts-Score
        diversity_score = self._calculate_diversity_impact(
            candidate_track, current_state.playlist
        )
        
        # Constraint-Kompatibilität
        constraint_score = self._check_constraints(
            candidate_track, constraints
        )
        
        # Gewichtete Kombination
        total_score = (
            energy_score * self.config.energy_weight +
            harmonic_score * self.config.harmonic_weight +
            flow_score * self.config.flow_weight +
            diversity_score * self.config.diversity_weight
        ) * constraint_score
        
        # Cache-Update
        if self.config.cache_enabled:
            with self._cache_lock:
                if len(self._transition_cache) < self._max_cache_size:
                    self._transition_cache[cache_key] = total_score
        
        return total_score
    
    def _calculate_harmonic_compatibility(self, 
                                        track1: Dict[str, Any], 
                                        track2: Dict[str, Any]) -> float:
        """Berechnet harmonische Kompatibilität zwischen zwei Tracks"""
        # Camelot-Kompatibilität
        key1 = track1.get('key', 'C major')
        key2 = track2.get('key', 'C major')
        
        # Vereinfachte Camelot-Bewertung (sollte durch echte CamelotWheel ersetzt werden)
        if key1 == key2:
            camelot_score = 1.0
        elif self._are_compatible_keys(key1, key2):
            camelot_score = 0.8
        else:
            camelot_score = 0.3
        
        # BPM-Kompatibilität
        bpm1 = track1.get('bpm', 120)
        bpm2 = track2.get('bpm', 120)
        bpm_diff = abs(bpm1 - bpm2)
        bpm_score = max(0, 1.0 - bpm_diff / 30.0)  # Toleranz: 30 BPM
        
        return (camelot_score + bpm_score) / 2.0
    
    def _calculate_flow_compatibility(self, 
                                    last_track: Dict[str, Any],
                                    candidate_track: Dict[str, Any],
                                    current_state: SolverState) -> float:
        """Berechnet Flow-Kompatibilität"""
        # Energie-Übergang
        last_energy = last_track.get('energy_score', 5.0)
        candidate_energy = candidate_track.get('energy_score', 5.0)
        energy_transition = abs(candidate_energy - last_energy)
        
        # Sanfte Übergänge bevorzugen
        transition_score = max(0, 1.0 - energy_transition / 4.0)
        
        # Mood-Kontinuität
        mood_score = self._calculate_mood_continuity(last_track, candidate_track)
        
        # Tempo-Flow
        tempo_score = self._calculate_tempo_flow(last_track, candidate_track)
        
        return (transition_score + mood_score + tempo_score) / 3.0
    
    def _calculate_diversity_impact(self, 
                                  candidate_track: Dict[str, Any],
                                  current_playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Diversitäts-Impact des Kandidaten"""
        if not current_playlist:
            return 0.5
        
        # Energie-Diversität
        candidate_energy = candidate_track.get('energy_score', 5.0)
        playlist_energies = [t.get('energy_score', 5.0) for t in current_playlist]
        
        energy_variance_before = np.var(playlist_energies)
        energy_variance_after = np.var(playlist_energies + [candidate_energy])
        energy_diversity = min(1.0, energy_variance_after / max(energy_variance_before, 0.1))
        
        # Key-Diversität
        candidate_key = candidate_track.get('key', 'C major')
        playlist_keys = [t.get('key', 'C major') for t in current_playlist]
        key_diversity = 0.8 if candidate_key not in playlist_keys else 0.3
        
        return (energy_diversity + key_diversity) / 2.0
    
    def _check_constraints(self, track: Dict[str, Any], constraints: Dict[str, Any]) -> float:
        """Überprüft Constraint-Kompatibilität"""
        if not constraints:
            return 1.0
        
        score = 1.0
        
        # BPM-Constraints
        if 'bpm_range' in constraints:
            bpm = track.get('bpm', 120)
            min_bpm, max_bpm = constraints['bpm_range']
            if not (min_bpm <= bpm <= max_bpm):
                score *= 0.5
        
        # Energie-Constraints
        if 'energy_range' in constraints:
            energy = track.get('energy_score', 5.0)
            min_energy, max_energy = constraints['energy_range']
            if not (min_energy <= energy <= max_energy):
                score *= 0.5
        
        # Mood-Constraints
        if 'required_moods' in constraints:
            track_moods = track.get('mood', {})
            required_moods = constraints['required_moods']
            
            mood_match = any(
                track_moods.get(mood, 0) > 0.5 
                for mood in required_moods
            )
            
            if not mood_match:
                score *= 0.3
        
        # Blacklist
        if 'blacklisted_tracks' in constraints:
            if track['id'] in constraints['blacklisted_tracks']:
                score = 0.0
        
        return score
    
    def _create_new_state(self, 
                         parent_state: SolverState,
                         new_track: Dict[str, Any],
                         energy_curve: List[Any],
                         target_position: int) -> SolverState:
        """Erstellt neuen Zustand durch Hinzufügen eines Tracks"""
        new_playlist = parent_state.playlist + [new_track]
        new_used_tracks = parent_state.used_tracks | {new_track['id']}
        
        # Berechne neuen Score
        new_score = self._calculate_state_score(
            playlist=new_playlist,
            energy_curve=energy_curve,
            target_position=target_position
        )
        
        # Berechne Metriken
        energy_deviation = self._calculate_energy_deviation(new_playlist, energy_curve)
        harmonic_score = self._calculate_harmonic_score(new_playlist)
        flow_score = self._calculate_flow_score(new_playlist)
        
        return SolverState(
            playlist=new_playlist,
            used_tracks=new_used_tracks,
            current_score=new_score,
            position=target_position,
            energy_deviation=energy_deviation,
            harmonic_score=harmonic_score,
            flow_score=flow_score
        )
    
    def _calculate_state_score(self, 
                             playlist: List[Dict[str, Any]],
                             energy_curve: List[Any],
                             target_position: int) -> float:
        """Berechnet Gesamt-Score für Zustand"""
        if not playlist:
            return 0.0
        
        # Energie-Kurven-Matching
        curve_score = self._calculate_curve_matching_score(playlist, energy_curve)
        
        # Harmonische Qualität
        harmonic_score = self._calculate_harmonic_score(playlist)
        
        # Flow-Qualität
        flow_score = self._calculate_flow_score(playlist)
        
        # Diversität
        diversity_score = self._calculate_playlist_diversity(playlist)
        
        # Gewichtete Kombination
        total_score = (
            curve_score * self.config.energy_weight +
            harmonic_score * self.config.harmonic_weight +
            flow_score * self.config.flow_weight +
            diversity_score * self.config.diversity_weight
        )
        
        return total_score
    
    def _prune_beam(self, beam: List[SolverState]) -> List[SolverState]:
        """Entfernt schwache Zustände aus dem Beam"""
        if not beam:
            return beam
        
        # Sortiere nach Score
        beam.sort(key=lambda s: s.current_score, reverse=True)
        
        # Berechne Pruning-Schwellwert
        best_score = beam[0].current_score
        threshold = best_score * self.config.pruning_threshold
        
        # Filtere schwache Zustände
        pruned_beam = [state for state in beam if state.current_score >= threshold]
        
        # Update Statistiken
        pruned_count = len(beam) - len(pruned_beam)
        self.solver_stats['pruned_states'] += pruned_count
        
        return pruned_beam
    
    def _select_best_states(self, states: List[SolverState], beam_width: int) -> List[SolverState]:
        """Wählt beste Zustände für nächste Iteration"""
        if len(states) <= beam_width:
            return states
        
        # Sortiere nach Score
        states.sort(key=lambda s: s.current_score, reverse=True)
        
        return states[:beam_width]
    
    # Hilfsmethoden
    def _find_track_by_id(self, track_pool: List[Dict[str, Any]], track_id: str) -> Optional[Dict[str, Any]]:
        """Findet Track anhand der ID"""
        for track in track_pool:
            if track.get('id') == track_id:
                return track
        return None
    
    def _find_start_candidates(self, track_pool: List[Dict[str, Any]], 
                             energy_curve: List[Any]) -> List[Tuple[Dict[str, Any], float]]:
        """Findet beste Start-Kandidaten"""
        if not energy_curve:
            return [(track, 0.5) for track in track_pool[:10]]
        
        target_energy = energy_curve[0].energy if hasattr(energy_curve[0], 'energy') else 5.0
        candidates = []
        
        for track in track_pool:
            energy_score = track.get('energy_score', 5.0)
            energy_diff = abs(energy_score - target_energy)
            score = max(0, 1.0 - energy_diff / 5.0)
            candidates.append((track, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates
    
    def _calculate_initial_score(self, track: Dict[str, Any], energy_curve: List[Any]) -> float:
        """Berechnet initialen Score für Start-Track"""
        if not energy_curve:
            return 0.5
        
        target_energy = energy_curve[0].energy if hasattr(energy_curve[0], 'energy') else 5.0
        track_energy = track.get('energy_score', 5.0)
        energy_diff = abs(track_energy - target_energy)
        
        return max(0, 1.0 - energy_diff / 5.0)
    
    def _get_target_energy_at_position(self, energy_curve: List[Any], position: int, total_length: int) -> float:
        """Berechnet Ziel-Energie an gegebener Position"""
        if not energy_curve or total_length == 0:
            return 5.0
        
        normalized_position = position / max(total_length - 1, 1)
        
        # Finde umgebende Punkte in der Kurve
        for i in range(len(energy_curve) - 1):
            p1 = energy_curve[i]
            p2 = energy_curve[i + 1]
            
            pos1 = p1.position if hasattr(p1, 'position') else i / len(energy_curve)
            pos2 = p2.position if hasattr(p2, 'position') else (i + 1) / len(energy_curve)
            
            if pos1 <= normalized_position <= pos2:
                # Lineare Interpolation
                energy1 = p1.energy if hasattr(p1, 'energy') else 5.0
                energy2 = p2.energy if hasattr(p2, 'energy') else 5.0
                
                ratio = (normalized_position - pos1) / max(pos2 - pos1, 0.001)
                return energy1 + ratio * (energy2 - energy1)
        
        # Fallback: letzter Punkt
        last_point = energy_curve[-1]
        return last_point.energy if hasattr(last_point, 'energy') else 5.0
    
    def _are_compatible_keys(self, key1: str, key2: str) -> bool:
        """Vereinfachte Key-Kompatibilitätsprüfung"""
        # Vereinfachte Implementierung - sollte durch echte Camelot-Logik ersetzt werden
        compatible_pairs = [
            ('C major', 'A minor'),
            ('G major', 'E minor'),
            ('D major', 'B minor'),
            ('A major', 'F# minor'),
            ('E major', 'C# minor'),
            ('B major', 'G# minor'),
            ('F# major', 'D# minor'),
            ('C# major', 'A# minor'),
            ('F major', 'D minor'),
            ('Bb major', 'G minor'),
            ('Eb major', 'C minor'),
            ('Ab major', 'F minor')
        ]
        
        return (key1, key2) in compatible_pairs or (key2, key1) in compatible_pairs
    
    def _calculate_mood_continuity(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """Berechnet Mood-Kontinuität zwischen Tracks"""
        mood1 = track1.get('mood', {})
        mood2 = track2.get('mood', {})
        
        if not mood1 or not mood2:
            return 0.5
        
        # Berechne Ähnlichkeit der Mood-Vektoren
        mood_keys = ['euphoric', 'dark', 'driving', 'experimental']
        similarities = []
        
        for key in mood_keys:
            val1 = mood1.get(key, 0.5)
            val2 = mood2.get(key, 0.5)
            similarity = 1.0 - abs(val1 - val2)
            similarities.append(similarity)
        
        return np.mean(similarities)
    
    def _calculate_tempo_flow(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """Berechnet Tempo-Flow zwischen Tracks"""
        bpm1 = track1.get('bpm', 120)
        bpm2 = track2.get('bpm', 120)
        
        bpm_diff = abs(bpm1 - bpm2)
        return max(0, 1.0 - bpm_diff / 25.0)  # Toleranz: 25 BPM
    
    def _calculate_curve_matching_score(self, playlist: List[Dict[str, Any]], energy_curve: List[Any]) -> float:
        """Berechnet Kurven-Matching-Score"""
        if not playlist or not energy_curve:
            return 0.0
        
        deviations = []
        
        for i, track in enumerate(playlist):
            target_energy = self._get_target_energy_at_position(energy_curve, i, len(playlist))
            actual_energy = track.get('energy_score', 5.0)
            deviation = abs(actual_energy - target_energy)
            deviations.append(deviation)
        
        avg_deviation = np.mean(deviations)
        return max(0, 1.0 - avg_deviation / 5.0)
    
    def _calculate_harmonic_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet harmonischen Score der Playlist"""
        if len(playlist) < 2:
            return 0.5
        
        harmonic_scores = []
        
        for i in range(len(playlist) - 1):
            score = self._calculate_harmonic_compatibility(playlist[i], playlist[i + 1])
            harmonic_scores.append(score)
        
        return np.mean(harmonic_scores)
    
    def _calculate_flow_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Flow-Score der Playlist"""
        if len(playlist) < 2:
            return 0.5
        
        flow_scores = []
        
        for i in range(len(playlist) - 1):
            # Vereinfachte Flow-Berechnung
            energy1 = playlist[i].get('energy_score', 5.0)
            energy2 = playlist[i + 1].get('energy_score', 5.0)
            energy_transition = abs(energy2 - energy1)
            flow_score = max(0, 1.0 - energy_transition / 4.0)
            flow_scores.append(flow_score)
        
        return np.mean(flow_scores)
    
    def _calculate_playlist_diversity(self, playlist: List[Dict[str, Any]]) -> float:
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
        
        return (energy_diversity + key_diversity) / 2.0
    
    def _calculate_energy_deviation(self, playlist: List[Dict[str, Any]], energy_curve: List[Any]) -> float:
        """Berechnet durchschnittliche Energie-Abweichung"""
        if not playlist or not energy_curve:
            return 0.0
        
        deviations = []
        
        for i, track in enumerate(playlist):
            target_energy = self._get_target_energy_at_position(energy_curve, i, len(playlist))
            actual_energy = track.get('energy_score', 5.0)
            deviation = abs(actual_energy - target_energy)
            deviations.append(deviation)
        
        return np.mean(deviations)
    
    def _update_solver_stats(self, solve_time: float, final_score: float):
        """Aktualisiert Solver-Statistiken"""
        self.solver_stats['total_solves'] += 1
        
        # Durchschnittliche Solve-Zeit
        total = self.solver_stats['total_solves']
        current_avg = self.solver_stats['avg_solve_time']
        self.solver_stats['avg_solve_time'] = (
            (current_avg * (total - 1) + solve_time) / total
        )
        
        # Beste Scores
        self.solver_stats['best_scores'].append(final_score)
        if len(self.solver_stats['best_scores']) > 100:
            self.solver_stats['best_scores'] = self.solver_stats['best_scores'][-100:]
    
    def get_solver_stats(self) -> Dict[str, Any]:
        """Gibt Solver-Statistiken zurück"""
        stats = self.solver_stats.copy()
        
        # Cache-Hit-Rate
        total_requests = stats['cache_hits'] + stats['cache_misses']
        if total_requests > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / total_requests
        else:
            stats['cache_hit_rate'] = 0.0
        
        # Durchschnittlicher Score
        if stats['best_scores']:
            stats['avg_score'] = np.mean(stats['best_scores'])
            stats['best_score'] = max(stats['best_scores'])
        else:
            stats['avg_score'] = 0.0
            stats['best_score'] = 0.0
        
        return stats
    
    def clear_cache(self):
        """Löscht alle Caches"""
        with self._cache_lock:
            self._transition_cache.clear()
            self._energy_cache.clear()
            self._similarity_cache.clear()
        
        logger.info("CurveMatchingSolver Cache geleert")
    
    def update_config(self, new_config: SolverConfig):
        """Aktualisiert Solver-Konfiguration"""
        self.config = new_config
        logger.info(f"Solver-Konfiguration aktualisiert: Beam-Width={new_config.beam_width}")