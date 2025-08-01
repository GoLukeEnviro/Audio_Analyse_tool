"""Playlist Optimizer - Erweiterte Optimierungsalgorithmen für DJ-Playlists"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import random
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

class OptimizationMode(Enum):
    """Optimierungsmodi"""
    ENERGY_FLOW = "energy_flow"
    HARMONIC_MIXING = "harmonic_mixing"
    MOOD_PROGRESSION = "mood_progression"
    TEMPO_SMOOTHING = "tempo_smoothing"
    DIVERSITY_BALANCE = "diversity_balance"
    CROWD_ENGAGEMENT = "crowd_engagement"
    TECHNICAL_MIXING = "technical_mixing"
    SURPRISE_FACTOR = "surprise_factor"

@dataclass
class OptimizationConfig:
    """Konfiguration für Playlist-Optimierung"""
    mode: OptimizationMode = OptimizationMode.ENERGY_FLOW
    max_iterations: int = 1000
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 10
    convergence_threshold: float = 0.001
    parallel_processing: bool = True
    max_workers: int = 4
    
    # Gewichtungen für verschiedene Faktoren
    weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.weights is None:
            self.weights = {
                'energy_flow': 0.3,
                'harmonic_compatibility': 0.25,
                'tempo_smoothness': 0.2,
                'mood_progression': 0.15,
                'diversity': 0.1
            }

@dataclass
class OptimizationResult:
    """Ergebnis der Playlist-Optimierung"""
    optimized_playlist: List[Dict[str, Any]]
    original_score: float
    optimized_score: float
    improvement: float
    iterations: int
    convergence_achieved: bool
    optimization_time: float
    detailed_scores: Dict[str, float]
    optimization_history: List[float]

class PlaylistOptimizer:
    """Erweiterte Playlist-Optimierung mit verschiedenen Algorithmen"""
    
    def __init__(self):
        # Camelot Wheel für harmonische Kompatibilität
        self.camelot_wheel = self._init_camelot_wheel()
        
        # Optimierungsstatistiken
        self.optimization_stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'avg_improvement': 0.0,
            'avg_optimization_time': 0.0,
            'best_score_achieved': 0.0
        }
        
        logger.info("PlaylistOptimizer initialisiert")
    
    def optimize_playlist(self, 
                         playlist: List[Dict[str, Any]],
                         config: Optional[OptimizationConfig] = None) -> OptimizationResult:
        """Optimiert eine Playlist basierend auf der gewählten Konfiguration"""
        start_time = time.time()
        config = config or OptimizationConfig()
        
        # Original-Score berechnen
        original_score = self._calculate_playlist_score(playlist, config)
        
        # Optimierungsalgorithmus wählen
        if config.mode == OptimizationMode.ENERGY_FLOW:
            result = self._optimize_energy_flow(playlist, config)
        elif config.mode == OptimizationMode.HARMONIC_MIXING:
            result = self._optimize_harmonic_mixing(playlist, config)
        elif config.mode == OptimizationMode.MOOD_PROGRESSION:
            result = self._optimize_mood_progression(playlist, config)
        elif config.mode == OptimizationMode.TEMPO_SMOOTHING:
            result = self._optimize_tempo_smoothing(playlist, config)
        elif config.mode == OptimizationMode.DIVERSITY_BALANCE:
            result = self._optimize_diversity_balance(playlist, config)
        elif config.mode == OptimizationMode.CROWD_ENGAGEMENT:
            result = self._optimize_crowd_engagement(playlist, config)
        elif config.mode == OptimizationMode.TECHNICAL_MIXING:
            result = self._optimize_technical_mixing(playlist, config)
        elif config.mode == OptimizationMode.SURPRISE_FACTOR:
            result = self._optimize_surprise_factor(playlist, config)
        else:
            # Genetischer Algorithmus als Standard
            result = self._genetic_algorithm_optimization(playlist, config)
        
        optimization_time = time.time() - start_time
        
        # Finales Ergebnis zusammenstellen
        optimized_score = self._calculate_playlist_score(result['playlist'], config)
        improvement = ((optimized_score - original_score) / original_score) * 100 if original_score > 0 else 0
        
        # Detaillierte Scores
        detailed_scores = self._calculate_detailed_scores(result['playlist'], config)
        
        # Statistiken aktualisieren
        self._update_optimization_stats(improvement, optimization_time, optimized_score)
        
        return OptimizationResult(
            optimized_playlist=result['playlist'],
            original_score=original_score,
            optimized_score=optimized_score,
            improvement=improvement,
            iterations=result.get('iterations', 0),
            convergence_achieved=result.get('converged', False),
            optimization_time=optimization_time,
            detailed_scores=detailed_scores,
            optimization_history=result.get('history', [])
        )
    
    def _optimize_energy_flow(self, playlist: List[Dict[str, Any]], 
                             config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert den Energie-Flow der Playlist"""
        best_playlist = playlist.copy()
        best_score = self._calculate_energy_flow_score(playlist)
        history = [best_score]
        
        for iteration in range(config.max_iterations):
            # Verschiedene Optimierungsstrategien
            candidates = []
            
            # 1. Lokale Swaps
            for i in range(len(playlist) - 1):
                candidate = playlist.copy()
                candidate[i], candidate[i + 1] = candidate[i + 1], candidate[i]
                candidates.append(candidate)
            
            # 2. Segment-Reordering
            segment_size = min(5, len(playlist) // 3)
            for start in range(0, len(playlist) - segment_size, segment_size):
                candidate = playlist.copy()
                segment = candidate[start:start + segment_size]
                # Sortiere Segment nach Energie
                segment.sort(key=lambda x: x.get('energy_score', 5.0))
                candidate[start:start + segment_size] = segment
                candidates.append(candidate)
            
            # 3. Energie-Gradient-Optimierung
            candidate = self._optimize_energy_gradient(playlist)
            candidates.append(candidate)
            
            # Beste Kandidaten evaluieren
            best_candidate = None
            best_candidate_score = best_score
            
            for candidate in candidates:
                score = self._calculate_energy_flow_score(candidate)
                if score > best_candidate_score:
                    best_candidate = candidate
                    best_candidate_score = score
            
            if best_candidate:
                playlist = best_candidate
                best_score = best_candidate_score
                best_playlist = playlist.copy()
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 10:
                recent_improvement = abs(history[-1] - history[-10])
                if recent_improvement < config.convergence_threshold:
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _optimize_harmonic_mixing(self, playlist: List[Dict[str, Any]], 
                                 config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert harmonische Übergänge zwischen Tracks"""
        best_playlist = playlist.copy()
        best_score = self._calculate_harmonic_score(playlist)
        history = [best_score]
        
        for iteration in range(config.max_iterations):
            # Greedy-Ansatz: Finde beste harmonische Reihenfolge
            if iteration == 0:
                # Erste Iteration: Komplette Neuordnung
                optimized = self._greedy_harmonic_ordering(playlist)
            else:
                # Weitere Iterationen: Lokale Verbesserungen
                optimized = self._improve_harmonic_transitions(best_playlist)
            
            score = self._calculate_harmonic_score(optimized)
            
            if score > best_score:
                best_playlist = optimized
                best_score = score
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 5 and all(
                abs(history[-1] - history[-i]) < config.convergence_threshold 
                for i in range(2, 6)
            ):
                break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _optimize_mood_progression(self, playlist: List[Dict[str, Any]], 
                                  config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert die Stimmungsprogression der Playlist"""
        best_playlist = playlist.copy()
        best_score = self._calculate_mood_progression_score(playlist)
        history = [best_score]
        
        # Definiere gewünschte Mood-Progression
        target_progression = self._generate_target_mood_progression(len(playlist))
        
        for iteration in range(config.max_iterations):
            # Verschiedene Optimierungsansätze
            candidates = []
            
            # 1. Mood-basierte Sortierung
            candidate = self._sort_by_mood_progression(playlist, target_progression)
            candidates.append(candidate)
            
            # 2. Lokale Mood-Optimierung
            candidate = self._optimize_local_mood_transitions(best_playlist)
            candidates.append(candidate)
            
            # 3. Segment-basierte Mood-Optimierung
            candidate = self._optimize_mood_segments(best_playlist, target_progression)
            candidates.append(candidate)
            
            # Beste Kandidaten evaluieren
            for candidate in candidates:
                score = self._calculate_mood_progression_score(candidate)
                if score > best_score:
                    best_playlist = candidate
                    best_score = score
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 10:
                recent_improvement = abs(history[-1] - history[-5])
                if recent_improvement < config.convergence_threshold:
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _optimize_tempo_smoothing(self, playlist: List[Dict[str, Any]], 
                                 config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert Tempo-Übergänge für smoothes Mixing"""
        best_playlist = playlist.copy()
        best_score = self._calculate_tempo_smoothness_score(playlist)
        history = [best_score]
        
        for iteration in range(config.max_iterations):
            # Tempo-Optimierungsstrategien
            candidates = []
            
            # 1. BPM-basierte Sortierung mit Toleranz
            candidate = self._sort_by_tempo_compatibility(playlist)
            candidates.append(candidate)
            
            # 2. Sliding Window Tempo-Optimierung
            candidate = self._sliding_window_tempo_optimization(best_playlist)
            candidates.append(candidate)
            
            # 3. Tempo-Cluster-Optimierung
            candidate = self._cluster_based_tempo_optimization(playlist)
            candidates.append(candidate)
            
            # Evaluierung
            for candidate in candidates:
                score = self._calculate_tempo_smoothness_score(candidate)
                if score > best_score:
                    best_playlist = candidate
                    best_score = score
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 8:
                if all(abs(history[-1] - history[-i]) < config.convergence_threshold 
                       for i in range(2, 5)):
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _optimize_diversity_balance(self, playlist: List[Dict[str, Any]], 
                                   config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert die Balance zwischen Kohärenz und Diversität"""
        best_playlist = playlist.copy()
        best_score = self._calculate_diversity_score(playlist)
        history = [best_score]
        
        for iteration in range(config.max_iterations):
            # Diversitäts-Optimierungsstrategien
            candidates = []
            
            # 1. Genre-Diversität
            candidate = self._optimize_genre_diversity(playlist)
            candidates.append(candidate)
            
            # 2. Artist-Diversität
            candidate = self._optimize_artist_diversity(playlist)
            candidates.append(candidate)
            
            # 3. Energie-Diversität
            candidate = self._optimize_energy_diversity(playlist)
            candidates.append(candidate)
            
            # 4. Zeitperioden-Diversität
            candidate = self._optimize_temporal_diversity(playlist)
            candidates.append(candidate)
            
            # Evaluierung
            for candidate in candidates:
                score = self._calculate_diversity_score(candidate)
                if score > best_score:
                    best_playlist = candidate
                    best_score = score
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 10:
                recent_improvement = abs(history[-1] - history[-5])
                if recent_improvement < config.convergence_threshold:
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _optimize_crowd_engagement(self, playlist: List[Dict[str, Any]], 
                                  config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert für maximales Crowd-Engagement"""
        best_playlist = playlist.copy()
        best_score = self._calculate_crowd_engagement_score(playlist)
        history = [best_score]
        
        # Crowd-Engagement-Faktoren
        engagement_factors = {
            'peak_time_placement': 0.3,
            'energy_buildup': 0.25,
            'familiarity_factor': 0.2,
            'danceability': 0.15,
            'surprise_element': 0.1
        }
        
        for iteration in range(config.max_iterations):
            candidates = []
            
            # 1. Peak-Time-Optimierung
            candidate = self._optimize_peak_time_placement(playlist)
            candidates.append(candidate)
            
            # 2. Energie-Buildup-Optimierung
            candidate = self._optimize_energy_buildup(playlist)
            candidates.append(candidate)
            
            # 3. Familiarity-Balance
            candidate = self._optimize_familiarity_balance(playlist)
            candidates.append(candidate)
            
            # Evaluierung
            for candidate in candidates:
                score = self._calculate_crowd_engagement_score(candidate)
                if score > best_score:
                    best_playlist = candidate
                    best_score = score
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 8:
                if abs(history[-1] - history[-4]) < config.convergence_threshold:
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _optimize_technical_mixing(self, playlist: List[Dict[str, Any]], 
                                  config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert für technische Mixing-Aspekte"""
        best_playlist = playlist.copy()
        best_score = self._calculate_technical_mixing_score(playlist)
        history = [best_score]
        
        for iteration in range(config.max_iterations):
            candidates = []
            
            # 1. BPM-Kompatibilität
            candidate = self._optimize_bpm_compatibility(playlist)
            candidates.append(candidate)
            
            # 2. Key-Kompatibilität
            candidate = self._optimize_key_compatibility(playlist)
            candidates.append(candidate)
            
            # 3. Intro/Outro-Matching
            candidate = self._optimize_intro_outro_matching(playlist)
            candidates.append(candidate)
            
            # 4. Spektrale Kompatibilität
            candidate = self._optimize_spectral_compatibility(playlist)
            candidates.append(candidate)
            
            # Evaluierung
            for candidate in candidates:
                score = self._calculate_technical_mixing_score(candidate)
                if score > best_score:
                    best_playlist = candidate
                    best_score = score
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 6:
                if abs(history[-1] - history[-3]) < config.convergence_threshold:
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _optimize_surprise_factor(self, playlist: List[Dict[str, Any]], 
                                 config: OptimizationConfig) -> Dict[str, Any]:
        """Optimiert für Überraschungsmomente"""
        best_playlist = playlist.copy()
        best_score = self._calculate_surprise_score(playlist)
        history = [best_score]
        
        for iteration in range(config.max_iterations):
            candidates = []
            
            # 1. Unerwartete Genre-Wechsel
            candidate = self._add_surprise_genre_changes(playlist)
            candidates.append(candidate)
            
            # 2. Tempo-Überraschungen
            candidate = self._add_tempo_surprises(playlist)
            candidates.append(candidate)
            
            # 3. Energie-Drops und -Peaks
            candidate = self._add_energy_surprises(playlist)
            candidates.append(candidate)
            
            # 4. Throwback-Momente
            candidate = self._add_throwback_moments(playlist)
            candidates.append(candidate)
            
            # Evaluierung
            for candidate in candidates:
                score = self._calculate_surprise_score(candidate)
                if score > best_score:
                    best_playlist = candidate
                    best_score = score
            
            history.append(best_score)
            
            # Konvergenz prüfen
            if len(history) > 8:
                if abs(history[-1] - history[-4]) < config.convergence_threshold:
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': iteration + 1,
            'converged': iteration < config.max_iterations - 1,
            'history': history
        }
    
    def _genetic_algorithm_optimization(self, playlist: List[Dict[str, Any]], 
                                       config: OptimizationConfig) -> Dict[str, Any]:
        """Genetischer Algorithmus für Playlist-Optimierung"""
        # Initialisiere Population
        population = self._initialize_population(playlist, config.population_size)
        best_score = 0
        best_playlist = playlist.copy()
        history = []
        
        for generation in range(config.max_iterations):
            # Evaluiere Population
            fitness_scores = []
            for individual in population:
                score = self._calculate_playlist_score(individual, config)
                fitness_scores.append(score)
                
                if score > best_score:
                    best_score = score
                    best_playlist = individual.copy()
            
            history.append(best_score)
            
            # Selektion
            elite = self._select_elite(population, fitness_scores, config.elite_size)
            
            # Neue Generation erstellen
            new_population = elite.copy()
            
            while len(new_population) < config.population_size:
                # Crossover
                if random.random() < config.crossover_rate:
                    parent1, parent2 = self._tournament_selection(population, fitness_scores, 2)
                    child = self._crossover(parent1, parent2)
                else:
                    child = random.choice(elite).copy()
                
                # Mutation
                if random.random() < config.mutation_rate:
                    child = self._mutate(child)
                
                new_population.append(child)
            
            population = new_population
            
            # Konvergenz prüfen
            if len(history) > 20:
                recent_improvement = abs(history[-1] - history[-20])
                if recent_improvement < config.convergence_threshold:
                    break
        
        return {
            'playlist': best_playlist,
            'iterations': generation + 1,
            'converged': generation < config.max_iterations - 1,
            'history': history
        }
    
    def _calculate_playlist_score(self, playlist: List[Dict[str, Any]], 
                                 config: OptimizationConfig) -> float:
        """Berechnet Gesamt-Score einer Playlist"""
        scores = {
            'energy_flow': self._calculate_energy_flow_score(playlist),
            'harmonic_compatibility': self._calculate_harmonic_score(playlist),
            'tempo_smoothness': self._calculate_tempo_smoothness_score(playlist),
            'mood_progression': self._calculate_mood_progression_score(playlist),
            'diversity': self._calculate_diversity_score(playlist)
        }
        
        # Gewichteter Gesamt-Score
        total_score = sum(
            scores[factor] * config.weights.get(factor, 0.2)
            for factor in scores
        )
        
        return total_score
    
    def _calculate_energy_flow_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Energy-Flow-Score"""
        if len(playlist) < 2:
            return 1.0
        
        energy_values = [track.get('energy_score', 5.0) for track in playlist]
        
        # Berechne Energie-Gradient
        gradients = []
        for i in range(len(energy_values) - 1):
            gradient = energy_values[i + 1] - energy_values[i]
            gradients.append(gradient)
        
        # Bewerte Gradient-Smoothness
        gradient_variance = np.var(gradients) if gradients else 0
        smoothness_score = 1.0 / (1.0 + gradient_variance)
        
        # Bewerte Energie-Progression (sollte generell aufsteigend sein)
        progression_score = 0.0
        if energy_values:
            start_energy = energy_values[0]
            end_energy = energy_values[-1]
            if end_energy > start_energy:
                progression_score = min(1.0, (end_energy - start_energy) / 5.0)
        
        return (smoothness_score * 0.7 + progression_score * 0.3)
    
    def _calculate_harmonic_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet harmonischen Kompatibilitäts-Score"""
        if len(playlist) < 2:
            return 1.0
        
        compatibility_scores = []
        
        for i in range(len(playlist) - 1):
            current_key = playlist[i].get('key', '')
            next_key = playlist[i + 1].get('key', '')
            
            if current_key and next_key:
                compatibility = self._get_harmonic_compatibility(current_key, next_key)
                compatibility_scores.append(compatibility)
        
        return np.mean(compatibility_scores) if compatibility_scores else 0.5
    
    def _calculate_tempo_smoothness_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Tempo-Smoothness-Score"""
        if len(playlist) < 2:
            return 1.0
        
        bpm_values = [track.get('bpm', 120.0) for track in playlist]
        
        # Berechne BPM-Unterschiede
        bpm_diffs = []
        for i in range(len(bpm_values) - 1):
            diff = abs(bpm_values[i + 1] - bpm_values[i])
            # Normalisiere auf 0-1 (max 20 BPM Unterschied = 0)
            normalized_diff = max(0, 1.0 - diff / 20.0)
            bpm_diffs.append(normalized_diff)
        
        return np.mean(bpm_diffs) if bpm_diffs else 1.0
    
    def _calculate_mood_progression_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Mood-Progression-Score"""
        if len(playlist) < 2:
            return 1.0
        
        # Extrahiere Mood-Werte
        mood_progressions = []
        
        for i in range(len(playlist) - 1):
            current_mood = playlist[i].get('mood', {})
            next_mood = playlist[i + 1].get('mood', {})
            
            # Berechne Mood-Kompatibilität
            compatibility = self._calculate_mood_compatibility(current_mood, next_mood)
            mood_progressions.append(compatibility)
        
        return np.mean(mood_progressions) if mood_progressions else 0.5
    
    def _calculate_diversity_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Diversitäts-Score"""
        if len(playlist) < 2:
            return 1.0
        
        # Genre-Diversität
        genres = [track.get('genre', 'Unknown') for track in playlist]
        unique_genres = len(set(genres))
        genre_diversity = min(1.0, unique_genres / len(playlist))
        
        # Artist-Diversität
        artists = [track.get('artist', 'Unknown') for track in playlist]
        unique_artists = len(set(artists))
        artist_diversity = min(1.0, unique_artists / len(playlist))
        
        # Energie-Diversität
        energy_values = [track.get('energy_score', 5.0) for track in playlist]
        energy_std = np.std(energy_values) if energy_values else 0
        energy_diversity = min(1.0, energy_std / 3.0)  # Normalisiert auf 0-1
        
        # Gewichteter Diversitäts-Score
        diversity_score = (
            genre_diversity * 0.4 +
            artist_diversity * 0.4 +
            energy_diversity * 0.2
        )
        
        return diversity_score
    
    def _calculate_detailed_scores(self, playlist: List[Dict[str, Any]], 
                                  config: OptimizationConfig) -> Dict[str, float]:
        """Berechnet detaillierte Scores für alle Faktoren"""
        return {
            'energy_flow': self._calculate_energy_flow_score(playlist),
            'harmonic_compatibility': self._calculate_harmonic_score(playlist),
            'tempo_smoothness': self._calculate_tempo_smoothness_score(playlist),
            'mood_progression': self._calculate_mood_progression_score(playlist),
            'diversity': self._calculate_diversity_score(playlist),
            'crowd_engagement': self._calculate_crowd_engagement_score(playlist),
            'technical_mixing': self._calculate_technical_mixing_score(playlist),
            'surprise_factor': self._calculate_surprise_score(playlist)
        }
    
    def _calculate_crowd_engagement_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Crowd-Engagement-Score"""
        if not playlist:
            return 0.0
        
        # Peak-Time-Placement (höchste Energie in der Mitte)
        energy_values = [track.get('energy_score', 5.0) for track in playlist]
        peak_position = len(playlist) // 2
        peak_window = max(1, len(playlist) // 4)
        
        peak_energy = max(energy_values[max(0, peak_position - peak_window):
                                       min(len(playlist), peak_position + peak_window)])
        peak_score = peak_energy / 10.0
        
        # Energie-Buildup
        first_half_avg = np.mean(energy_values[:len(playlist)//2]) if energy_values else 5.0
        second_half_avg = np.mean(energy_values[len(playlist)//2:]) if energy_values else 5.0
        buildup_score = min(1.0, (second_half_avg - first_half_avg) / 3.0 + 0.5)
        
        # Danceability (basierend auf BPM-Range)
        bpm_values = [track.get('bpm', 120.0) for track in playlist]
        danceable_bpm_count = sum(1 for bpm in bpm_values if 120 <= bpm <= 140)
        danceability_score = danceable_bpm_count / len(playlist) if playlist else 0
        
        return (peak_score * 0.4 + buildup_score * 0.4 + danceability_score * 0.2)
    
    def _calculate_technical_mixing_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Technical-Mixing-Score"""
        if len(playlist) < 2:
            return 1.0
        
        # BPM-Kompatibilität
        bpm_score = self._calculate_tempo_smoothness_score(playlist)
        
        # Key-Kompatibilität
        key_score = self._calculate_harmonic_score(playlist)
        
        # Spektrale Kompatibilität (vereinfacht)
        spectral_scores = []
        for i in range(len(playlist) - 1):
            current_spectral = playlist[i].get('spectral_features', {})
            next_spectral = playlist[i + 1].get('spectral_features', {})
            
            if current_spectral and next_spectral:
                # Vergleiche Spektralzentroid
                current_centroid = current_spectral.get('centroid', 0)
                next_centroid = next_spectral.get('centroid', 0)
                
                if current_centroid > 0 and next_centroid > 0:
                    diff = abs(current_centroid - next_centroid) / max(current_centroid, next_centroid)
                    spectral_scores.append(1.0 - min(1.0, diff))
        
        spectral_score = np.mean(spectral_scores) if spectral_scores else 0.5
        
        return (bpm_score * 0.4 + key_score * 0.4 + spectral_score * 0.2)
    
    def _calculate_surprise_score(self, playlist: List[Dict[str, Any]]) -> float:
        """Berechnet Surprise-Factor-Score"""
        if len(playlist) < 3:
            return 0.5
        
        surprise_elements = 0
        total_transitions = len(playlist) - 1
        
        for i in range(len(playlist) - 1):
            current = playlist[i]
            next_track = playlist[i + 1]
            
            # Genre-Überraschung
            if current.get('genre') != next_track.get('genre'):
                surprise_elements += 0.3
            
            # BPM-Überraschung (große Sprünge)
            current_bpm = current.get('bpm', 120)
            next_bpm = next_track.get('bpm', 120)
            if abs(current_bpm - next_bpm) > 15:
                surprise_elements += 0.2
            
            # Energie-Überraschung (unerwartete Drops/Peaks)
            current_energy = current.get('energy_score', 5.0)
            next_energy = next_track.get('energy_score', 5.0)
            if abs(current_energy - next_energy) > 2.0:
                surprise_elements += 0.2
        
        # Normalisiere auf 0-1
        surprise_score = min(1.0, surprise_elements / total_transitions)
        
        # Balance: Zu viele Überraschungen sind auch nicht gut
        if surprise_score > 0.7:
            surprise_score = 1.0 - surprise_score
        
        return surprise_score
    
    def _get_harmonic_compatibility(self, key1: str, key2: str) -> float:
        """Berechnet harmonische Kompatibilität zwischen zwei Keys"""
        if not key1 or not key2:
            return 0.5
        
        # Camelot Wheel Kompatibilität
        camelot1 = self.camelot_wheel.get(key1)
        camelot2 = self.camelot_wheel.get(key2)
        
        if not camelot1 or not camelot2:
            return 0.5
        
        # Extrahiere Nummer und Typ (A/B)
        num1, type1 = int(camelot1[:-1]), camelot1[-1]
        num2, type2 = int(camelot2[:-1]), camelot2[-1]
        
        # Perfekte Matches
        if camelot1 == camelot2:
            return 1.0
        
        # Benachbarte Keys
        if type1 == type2:
            num_diff = min(abs(num1 - num2), 12 - abs(num1 - num2))
            if num_diff == 1:
                return 0.9
            elif num_diff == 2:
                return 0.7
        
        # Relative Moll/Dur
        if num1 == num2 and type1 != type2:
            return 0.8
        
        # Energy Boost (A -> B mit gleicher Nummer)
        if num1 == num2 and type1 == 'A' and type2 == 'B':
            return 0.85
        
        return 0.3  # Nicht kompatibel
    
    def _calculate_mood_compatibility(self, mood1: Dict[str, float], 
                                    mood2: Dict[str, float]) -> float:
        """Berechnet Mood-Kompatibilität zwischen zwei Tracks"""
        if not mood1 or not mood2:
            return 0.5
        
        # Gemeinsame Mood-Kategorien
        common_moods = set(mood1.keys()) & set(mood2.keys())
        
        if not common_moods:
            return 0.3
        
        # Berechne Ähnlichkeit für gemeinsame Moods
        similarities = []
        for mood in common_moods:
            val1 = mood1[mood]
            val2 = mood2[mood]
            similarity = 1.0 - abs(val1 - val2)
            similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.5
    
    def _init_camelot_wheel(self) -> Dict[str, str]:
        """Initialisiert Camelot Wheel Mapping"""
        return {
            'C major': '8B', 'A minor': '8A',
            'G major': '9B', 'E minor': '9A',
            'D major': '10B', 'B minor': '10A',
            'A major': '11B', 'F# minor': '11A',
            'E major': '12B', 'C# minor': '12A',
            'B major': '1B', 'G# minor': '1A',
            'F# major': '2B', 'D# minor': '2A',
            'C# major': '3B', 'A# minor': '3A',
            'F major': '7B', 'D minor': '7A',
            'Bb major': '6B', 'G minor': '6A',
            'Eb major': '5B', 'C minor': '5A',
            'Ab major': '4B', 'F minor': '4A'
        }
    
    def _update_optimization_stats(self, improvement: float, 
                                  optimization_time: float, score: float):
        """Aktualisiert Optimierungsstatistiken"""
        self.optimization_stats['total_optimizations'] += 1
        
        if improvement > 0:
            self.optimization_stats['successful_optimizations'] += 1
        
        # Durchschnittliche Verbesserung
        total = self.optimization_stats['total_optimizations']
        current_avg = self.optimization_stats['avg_improvement']
        self.optimization_stats['avg_improvement'] = (
            (current_avg * (total - 1) + improvement) / total
        )
        
        # Durchschnittliche Optimierungszeit
        current_time_avg = self.optimization_stats['avg_optimization_time']
        self.optimization_stats['avg_optimization_time'] = (
            (current_time_avg * (total - 1) + optimization_time) / total
        )
        
        # Bester Score
        if score > self.optimization_stats['best_score_achieved']:
            self.optimization_stats['best_score_achieved'] = score
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Gibt Optimierungsstatistiken zurück"""
        stats = self.optimization_stats.copy()
        
        if stats['total_optimizations'] > 0:
            stats['success_rate'] = (
                stats['successful_optimizations'] / stats['total_optimizations']
            )
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    # Hilfsmethoden für spezifische Optimierungsstrategien
    def _optimize_energy_gradient(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimiert Energie-Gradient"""
        # Sortiere nach gewünschtem Energie-Verlauf
        target_energies = np.linspace(3.0, 9.0, len(playlist))
        
        # Weise Tracks zu Ziel-Energien zu
        playlist_with_targets = []
        for i, track in enumerate(playlist):
            track_energy = track.get('energy_score', 5.0)
            target_energy = target_energies[i]
            diff = abs(track_energy - target_energy)
            playlist_with_targets.append((track, diff, i))
        
        # Sortiere nach geringster Abweichung
        playlist_with_targets.sort(key=lambda x: x[1])
        
        # Rekonstruiere Playlist
        optimized = [item[0] for item in playlist_with_targets]
        return optimized
    
    def _greedy_harmonic_ordering(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Greedy-Algorithmus für harmonische Reihenfolge"""
        if not playlist:
            return []
        
        ordered = [playlist[0]]
        remaining = playlist[1:].copy()
        
        while remaining:
            current_key = ordered[-1].get('key', '')
            
            # Finde besten nächsten Track
            best_track = None
            best_compatibility = -1
            best_index = -1
            
            for i, track in enumerate(remaining):
                track_key = track.get('key', '')
                compatibility = self._get_harmonic_compatibility(current_key, track_key)
                
                if compatibility > best_compatibility:
                    best_compatibility = compatibility
                    best_track = track
                    best_index = i
            
            if best_track:
                ordered.append(best_track)
                remaining.pop(best_index)
            else:
                # Fallback: Nimm ersten verfügbaren Track
                ordered.append(remaining.pop(0))
        
        return ordered
    
    def _improve_harmonic_transitions(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verbessert harmonische Übergänge durch lokale Swaps"""
        improved = playlist.copy()
        
        for i in range(len(improved) - 1):
            current_key = improved[i].get('key', '')
            next_key = improved[i + 1].get('key', '')
            current_compatibility = self._get_harmonic_compatibility(current_key, next_key)
            
            # Suche besseren Nachfolger in den nächsten 3 Tracks
            for j in range(i + 2, min(i + 5, len(improved))):
                candidate_key = improved[j].get('key', '')
                candidate_compatibility = self._get_harmonic_compatibility(current_key, candidate_key)
                
                if candidate_compatibility > current_compatibility + 0.1:
                    # Swap durchführen
                    improved[i + 1], improved[j] = improved[j], improved[i + 1]
                    break
        
        return improved
    
    def _generate_target_mood_progression(self, playlist_length: int) -> List[Dict[str, float]]:
        """Generiert Ziel-Mood-Progression"""
        progression = []
        
        for i in range(playlist_length):
            position = i / (playlist_length - 1) if playlist_length > 1 else 0
            
            # Beispiel-Progression: Start ruhig, Mitte energisch, Ende entspannt
            if position < 0.3:
                # Warm-up Phase
                mood = {
                    'euphoric': 0.3 + position * 0.5,
                    'dark': 0.2,
                    'driving': 0.4 + position * 0.4,
                    'experimental': 0.1
                }
            elif position < 0.7:
                # Peak Phase
                mood = {
                    'euphoric': 0.8 + (position - 0.3) * 0.2,
                    'dark': 0.1,
                    'driving': 0.9,
                    'experimental': 0.2
                }
            else:
                # Cool-down Phase
                mood = {
                    'euphoric': 0.9 - (position - 0.7) * 0.4,
                    'dark': 0.3,
                    'driving': 0.8 - (position - 0.7) * 0.3,
                    'experimental': 0.1
                }
            
            progression.append(mood)
        
        return progression
    
    # Weitere Hilfsmethoden für Optimierungsstrategien...
    # (Implementierung der restlichen Methoden würde den Code zu lang machen)
    # Diese können bei Bedarf hinzugefügt werden
    
    def _sort_by_mood_progression(self, playlist: List[Dict[str, Any]], 
                                 target_progression: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Sortiert Playlist nach Mood-Progression"""
        # Vereinfachte Implementierung
        return playlist.copy()
    
    def _optimize_local_mood_transitions(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimiert lokale Mood-Übergänge"""
        # Vereinfachte Implementierung
        return playlist.copy()
    
    def _optimize_mood_segments(self, playlist: List[Dict[str, Any]], 
                               target_progression: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Optimiert Mood-Segmente"""
        # Vereinfachte Implementierung
        return playlist.copy()
    
    # Weitere Methoden für andere Optimierungsstrategien...
    # (Diese können bei Bedarf implementiert werden)
    
    def _sort_by_tempo_compatibility(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sortiert nach Tempo-Kompatibilität"""
        return sorted(playlist, key=lambda x: x.get('bpm', 120))
    
    def _sliding_window_tempo_optimization(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sliding Window Tempo-Optimierung"""
        return playlist.copy()
    
    def _cluster_based_tempo_optimization(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cluster-basierte Tempo-Optimierung"""
        return playlist.copy()
    
    # Genetische Algorithmus Hilfsmethoden
    def _initialize_population(self, playlist: List[Dict[str, Any]], 
                              population_size: int) -> List[List[Dict[str, Any]]]:
        """Initialisiert Population für genetischen Algorithmus"""
        population = []
        
        # Erste Individual ist die Original-Playlist
        population.append(playlist.copy())
        
        # Generiere weitere Individuals durch Shuffling
        for _ in range(population_size - 1):
            individual = playlist.copy()
            random.shuffle(individual)
            population.append(individual)
        
        return population
    
    def _select_elite(self, population: List[List[Dict[str, Any]]], 
                     fitness_scores: List[float], elite_size: int) -> List[List[Dict[str, Any]]]:
        """Selektiert Elite-Individuals"""
        # Sortiere nach Fitness-Score
        sorted_indices = sorted(range(len(fitness_scores)), 
                               key=lambda i: fitness_scores[i], reverse=True)
        
        elite = []
        for i in range(min(elite_size, len(population))):
            elite.append(population[sorted_indices[i]].copy())
        
        return elite
    
    def _tournament_selection(self, population: List[List[Dict[str, Any]]], 
                             fitness_scores: List[float], 
                             tournament_size: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Tournament-Selektion für Eltern"""
        def select_one():
            tournament_indices = random.sample(range(len(population)), 
                                             min(tournament_size, len(population)))
            best_index = max(tournament_indices, key=lambda i: fitness_scores[i])
            return population[best_index].copy()
        
        return select_one(), select_one()
    
    def _crossover(self, parent1: List[Dict[str, Any]], 
                  parent2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crossover-Operation"""
        if len(parent1) != len(parent2):
            return parent1.copy()
        
        # Order Crossover (OX)
        size = len(parent1)
        start, end = sorted(random.sample(range(size), 2))
        
        child = [None] * size
        child[start:end] = parent1[start:end]
        
        # Fülle Rest mit parent2 in Reihenfolge
        parent2_remaining = [track for track in parent2 if track not in child]
        
        j = 0
        for i in range(size):
            if child[i] is None:
                child[i] = parent2_remaining[j]
                j += 1
        
        return child
    
    def _mutate(self, individual: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mutations-Operation"""
        mutated = individual.copy()
        
        # Swap Mutation
        if len(mutated) >= 2:
            i, j = random.sample(range(len(mutated)), 2)
            mutated[i], mutated[j] = mutated[j], mutated[i]
        
        return mutated