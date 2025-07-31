"""Similarity Engine - k-NN-basierte Track-Ähnlichkeitsberechnung für Smart Suggestions"""

import numpy as np
import time
from typing import Dict, List, Any, Tuple, Optional
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances
import json
import os
from .camelot_wheel import CamelotWheel

try:
    from ..audio_analysis.energy_score_extractor import EnergyScoreExtractor
    from ..audio_analysis.mood_classifier_enhanced import EnhancedMoodClassifier
except ImportError:
    # Fallback für direkte Ausführung
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from audio_analysis.energy_score_extractor import EnergyScoreExtractor
    from audio_analysis.mood_classifier_enhanced import EnhancedMoodClassifier


class SimilarityEngine:
    """k-NN-basierte Ähnlichkeitsberechnung für Track-Suggestions mit <50ms Performance"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.camelot_wheel = CamelotWheel()
        
        # Feature-Dimensionen für k-NN
        self.feature_names = [
            'bpm',
            'key_numeric',
            'energy_score',
            'mood_vector_dark',
            'mood_vector_euphoric',
            'mood_vector_driving',
            'mood_vector_experimental',
            'spectral_centroid',
            'onset_density',
            'harmonic_ratio'
        ]
        
        # Gewichtungen für Feature-Distanz
        self.feature_weights = {
            'bpm': 0.25,
            'key_numeric': 0.20,
            'energy_score': 0.20,
            'mood_vector': 0.15,  # Summe aller Mood-Vektoren
            'spectral_centroid': 0.10,
            'onset_density': 0.05,
            'harmonic_ratio': 0.05
        }
        
        # k-NN Model
        self.knn_model = NearestNeighbors(
            n_neighbors=10,  # Mehr als benötigt für Filtering
            algorithm='ball_tree',
            metric='euclidean',
            n_jobs=-1  # Parallelisierung
        )
        
        self.scaler = StandardScaler()
        self.feature_matrix = None
        self.track_ids = []
        self.track_metadata = {}
        
        # Performance-Cache
        self.similarity_cache = {}
        self.cache_max_size = 1000
    
    def encode_key_numeric(self, key: str) -> float:
        """Kodiert Tonart numerisch für k-NN"""
        camelot = self.camelot_wheel.key_to_camelot(key)
        if not camelot:
            return 0.0
        
        number, key_type = self.camelot_wheel.parse_camelot(camelot)
        if not number:
            return 0.0
        
        # Kodierung: 0-11 für Position, +12 für Minor (A)
        base_value = (number - 1) / 11.0  # 0-1 für Position
        if key_type == 'A':  # Minor
            base_value += 1.0
        
        return base_value / 2.0  # Normalisiert auf 0-1
    
    def encode_mood_vector(self, mood_label: str, mood_confidence: float = 1.0) -> List[float]:
        """Kodiert Mood als One-Hot-Vector mit Confidence"""
        mood_categories = ['Dark', 'Euphoric', 'Driving', 'Experimental']
        vector = [0.0] * len(mood_categories)
        
        if mood_label in mood_categories:
            index = mood_categories.index(mood_label)
            vector[index] = mood_confidence
        
        return vector
    
    def extract_feature_vector(self, track_data: Dict[str, Any]) -> np.ndarray:
        """Extrahiert Feature-Vektor für k-NN"""
        features = []
        
        # BPM (normalisiert)
        bpm = track_data.get('bpm', 120.0)
        features.append(bpm / 200.0)  # Normalisiert auf typischen DJ-Bereich
        
        # Key (numerisch kodiert)
        key = track_data.get('key', 'C major')
        features.append(self.encode_key_numeric(key))
        
        # Energy Score
        energy_score = track_data.get('energy_score', 5.0)
        features.append(energy_score / 10.0)  # Normalisiert 0-1
        
        # Mood Vector
        mood_label = track_data.get('mood_label', 'Driving')
        mood_confidence = track_data.get('mood_confidence', 0.5)
        mood_vector = self.encode_mood_vector(mood_label, mood_confidence)
        features.extend(mood_vector)
        
        # Spectral Features
        spectral_centroid = track_data.get('spectral_centroid', 2000.0)
        features.append(spectral_centroid / 8000.0)  # Normalisiert
        
        onset_density = track_data.get('onset_density', 2.0)
        features.append(onset_density / 10.0)  # Normalisiert
        
        harmonic_ratio = track_data.get('harmonic_ratio', 0.5)
        features.append(harmonic_ratio)
        
        return np.array(features, dtype=np.float32)
    
    def build_similarity_index(self, tracks_data: List[Dict[str, Any]]):
        """Baut k-NN-Index für alle Tracks auf"""
        start_time = time.time()
        
        feature_vectors = []
        track_ids = []
        track_metadata = {}
        
        for track in tracks_data:
            track_id = track.get('file_path', '') or track.get('id', '')
            if not track_id:
                continue
            
            feature_vector = self.extract_feature_vector(track)
            
            feature_vectors.append(feature_vector)
            track_ids.append(track_id)
            track_metadata[track_id] = track
        
        if not feature_vectors:
            print("Keine gültigen Tracks für Similarity-Index")
            return False
        
        # Konvertiere zu NumPy Array
        self.feature_matrix = np.array(feature_vectors)
        self.track_ids = track_ids
        self.track_metadata = track_metadata
        
        # Skaliere Features
        self.feature_matrix = self.scaler.fit_transform(self.feature_matrix)
        
        # Trainiere k-NN Model
        self.knn_model.fit(self.feature_matrix)
        
        build_time = time.time() - start_time
        print(f"Similarity-Index für {len(track_ids)} Tracks in {build_time:.3f}s aufgebaut")
        
        # Cache leeren
        self.similarity_cache.clear()
        
        return True
    
    def calculate_compatibility_score(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> float:
        """Berechnet Kompatibilitäts-Score zwischen zwei Tracks"""
        score = 0.0
        
        # Key-Kompatibilität (Camelot Wheel)
        key1 = track1.get('key', '')
        key2 = track2.get('key', '')
        
        if key1 and key2:
            camelot1 = self.camelot_wheel.key_to_camelot(key1)
            camelot2 = self.camelot_wheel.key_to_camelot(key2)
            
            if camelot1 and camelot2:
                compatible_keys = self.camelot_wheel.get_compatible_keys(camelot1, 'extended')
                if camelot2 in compatible_keys:
                    score += 0.3
                elif camelot1 == camelot2:
                    score += 0.4
        
        # BPM-Kompatibilität
        bpm1 = track1.get('bpm', 120.0)
        bpm2 = track2.get('bpm', 120.0)
        bpm_diff = abs(bpm1 - bpm2)
        
        if bpm_diff <= 2:
            score += 0.3
        elif bpm_diff <= 5:
            score += 0.2
        elif bpm_diff <= 10:
            score += 0.1
        
        # Energy-Kompatibilität
        energy1 = track1.get('energy_score', 5.0)
        energy2 = track2.get('energy_score', 5.0)
        energy_diff = abs(energy1 - energy2)
        
        if energy_diff <= 1.0:
            score += 0.2
        elif energy_diff <= 2.0:
            score += 0.1
        
        # Mood-Kompatibilität
        mood1 = track1.get('mood_label', '')
        mood2 = track2.get('mood_label', '')
        
        if mood1 == mood2:
            score += 0.2
        elif self._are_moods_compatible(mood1, mood2):
            score += 0.1
        
        return min(1.0, score)
    
    def _are_moods_compatible(self, mood1: str, mood2: str) -> bool:
        """Prüft Mood-Kompatibilität"""
        compatible_moods = {
            'Dark': ['Experimental'],
            'Euphoric': ['Driving'],
            'Driving': ['Euphoric', 'Progressive'],
            'Experimental': ['Dark'],
            'Progressive': ['Driving']
        }
        
        return mood2 in compatible_moods.get(mood1, [])
    
    def find_similar_tracks(self, target_track: Dict[str, Any], 
                          exclude_tracks: List[str] = None,
                          count: int = 5,
                          min_compatibility: float = 0.6) -> List[Dict[str, Any]]:
        """Findet ähnliche Tracks mit k-NN (Performance-Target: <50ms)"""
        start_time = time.time()
        
        if self.feature_matrix is None or len(self.track_ids) == 0:
            return []
        
        target_id = target_track.get('file_path', '') or target_track.get('id', '')
        exclude_tracks = exclude_tracks or []
        if target_id:
            exclude_tracks.append(target_id)
        
        # Cache-Check
        cache_key = f"{target_id}_{count}_{min_compatibility}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        try:
            # Extrahiere Feature-Vektor für Target
            target_features = self.extract_feature_vector(target_track)
            target_features_scaled = self.scaler.transform(target_features.reshape(1, -1))
            
            # k-NN Suche
            distances, indices = self.knn_model.kneighbors(
                target_features_scaled, 
                n_neighbors=min(len(self.track_ids), count * 3)  # Mehr für Filtering
            )
            
            similar_tracks = []
            
            for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                if len(similar_tracks) >= count:
                    break
                
                track_id = self.track_ids[index]
                
                # Exclude-Filter
                if track_id in exclude_tracks:
                    continue
                
                track_data = self.track_metadata[track_id].copy()
                
                # Berechne Kompatibilitäts-Score
                compatibility = self.calculate_compatibility_score(target_track, track_data)
                
                if compatibility >= min_compatibility:
                    track_data['similarity_distance'] = float(distance)
                    track_data['compatibility_score'] = compatibility
                    track_data['combined_score'] = compatibility * (1.0 - distance)
                    
                    similar_tracks.append(track_data)
            
            # Sortiere nach Combined Score
            similar_tracks.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # Cache-Update (mit LRU-ähnlicher Logik)
            if len(self.similarity_cache) >= self.cache_max_size:
                # Entferne ältesten Eintrag
                oldest_key = next(iter(self.similarity_cache))
                del self.similarity_cache[oldest_key]
            
            self.similarity_cache[cache_key] = similar_tracks[:count]
            
            elapsed_time = (time.time() - start_time) * 1000  # ms
            
            if elapsed_time > 50:
                print(f"Warning: Similarity-Suche dauerte {elapsed_time:.1f}ms (Target: <50ms)")
            
            return similar_tracks[:count]
            
        except Exception as e:
            print(f"Fehler bei Similarity-Suche: {e}")
            return []
    
    def get_surprise_tracks(self, target_track: Dict[str, Any], 
                          available_tracks: List[Dict[str, Any]],
                          count: int = 2) -> List[Dict[str, Any]]:
        """Surprise-Me-Engine: ±2 Camelot + höhere Energy für Uplift-Momente"""
        target_key = target_track.get('key', '')
        target_energy = target_track.get('energy_score', 5.0)
        target_camelot = self.camelot_wheel.key_to_camelot(target_key)
        
        if not target_camelot:
            return []
        
        surprise_candidates = []
        
        for track in available_tracks:
            track_key = track.get('key', '')
            track_energy = track.get('energy_score', 5.0)
            track_camelot = self.camelot_wheel.key_to_camelot(track_key)
            
            if not track_camelot:
                continue
            
            # ±2 Camelot-Positionen
            target_num, target_type = self.camelot_wheel.parse_camelot(target_camelot)
            track_num, track_type = self.camelot_wheel.parse_camelot(track_camelot)
            
            if target_type == track_type:  # Gleicher Typ (A/B)
                pos_diff = abs(target_num - track_num)
                # Berücksichtige Wrap-around (12 -> 1)
                pos_diff = min(pos_diff, 12 - pos_diff)
                
                if pos_diff == 2:  # Genau ±2 Positionen
                    # Höhere Energy für Uplift
                    if track_energy > target_energy + 0.5:
                        surprise_score = track_energy - target_energy
                        track_copy = track.copy()
                        track_copy['surprise_score'] = surprise_score
                        track_copy['surprise_reason'] = f"±2 Camelot + Energy Uplift ({track_energy:.1f} > {target_energy:.1f})"
                        surprise_candidates.append(track_copy)
        
        # Sortiere nach Surprise-Score
        surprise_candidates.sort(key=lambda x: x['surprise_score'], reverse=True)
        
        return surprise_candidates[:count]
    
    def save_similarity_index(self, filename: str = 'similarity_index.json'):
        """Speichert Similarity-Index für schnelles Laden"""
        if self.feature_matrix is None:
            return False
        
        try:
            index_data = {
                'track_ids': self.track_ids,
                'feature_matrix': self.feature_matrix.tolist(),
                'scaler_mean': self.scaler.mean_.tolist(),
                'scaler_scale': self.scaler.scale_.tolist()
            }
            
            filepath = os.path.join(self.cache_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Fehler beim Speichern des Similarity-Index: {e}")
            return False
    
    def load_similarity_index(self, filename: str = 'similarity_index.json') -> bool:
        """Lädt gespeicherten Similarity-Index"""
        try:
            filepath = os.path.join(self.cache_dir, filename)
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            self.track_ids = index_data['track_ids']
            self.feature_matrix = np.array(index_data['feature_matrix'])
            
            # Rekonstruiere Scaler
            self.scaler.mean_ = np.array(index_data['scaler_mean'])
            self.scaler.scale_ = np.array(index_data['scaler_scale'])
            
            # Trainiere k-NN Model
            self.knn_model.fit(self.feature_matrix)
            
            print(f"Similarity-Index mit {len(self.track_ids)} Tracks geladen")
            return True
            
        except Exception as e:
            print(f"Fehler beim Laden des Similarity-Index: {e}")
            return False