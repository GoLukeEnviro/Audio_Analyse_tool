"""Smart Suggestions Engine - k-NN-basierte Track-Empfehlungen mit Surprise-Me-Funktion"""

import numpy as np
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import logging

logger = logging.getLogger(__name__)

class SmartSuggestionsEngine:
    """Intelligente Track-Empfehlungen mit k-NN und Überraschungs-Algorithmus"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ML-Modelle
        self.knn_model = NearestNeighbors(
            n_neighbors=20,
            metric='euclidean',
            algorithm='auto'
        )
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Behalte 95% der Varianz
        
        # Feature-Gewichtungen für verschiedene Empfehlungs-Modi
        self.feature_weights = {
            'harmonic': {
                'key_numeric': 0.4,
                'camelot_distance': 0.3,
                'energy_score': 0.2,
                'bpm': 0.1
            },
            'energy': {
                'energy_score': 0.4,
                'rms_loudness': 0.2,
                'onset_density': 0.2,
                'spectral_centroid': 0.2
            },
            'mood': {
                'mood_vector': 0.5,
                'energy_score': 0.2,
                'spectral_features': 0.3
            },
            'surprise': {
                'diversity_score': 0.6,
                'novelty_score': 0.4
            }
        }
        
        # Track-Datenbank
        self.track_database = []
        self.feature_matrix = None
        self.is_fitted = False
        
        # Surprise-Me-Parameter
        self.surprise_config = {
            'diversity_threshold': 0.7,
            'novelty_weight': 0.3,
            'serendipity_factor': 0.2
        }
    
    def add_track(self, track_id: str, features: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Fügt Track zur Empfehlungs-Datenbank hinzu"""
        track_entry = {
            'id': track_id,
            'features': features,
            'metadata': metadata or {},
            'feature_vector': self._extract_feature_vector(features)
        }
        
        self.track_database.append(track_entry)
        self.is_fitted = False  # Model muss neu trainiert werden
    
    def _extract_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Extrahiert numerischen Feature-Vektor aus Track-Features"""
        vector = []
        
        # Audio-Features
        vector.append(features.get('energy_score', 5.0))
        vector.append(features.get('bpm', 120.0))
        vector.append(features.get('rms_loudness', -30.0))
        vector.append(features.get('spectral_centroid', 2000.0))
        vector.append(features.get('spectral_rolloff', 5000.0))
        vector.append(features.get('onset_density', 2.0))
        vector.append(features.get('zero_crossing_rate', 0.1))
        vector.append(features.get('tempo_stability', 0.5))
        
        # Key-Features (numerisch kodiert)
        key = features.get('key', 'C major')
        key_numeric = self._encode_key_numeric(key)
        vector.append(key_numeric)
        
        # Camelot-Distanz (relativ zu C major)
        camelot_distance = self._calculate_camelot_distance(key, 'C major')
        vector.append(camelot_distance)
        
        # Mood-Features
        mood_features = features.get('mood', {})
        vector.extend([
            mood_features.get('euphoric', 0.5),
            mood_features.get('dark', 0.5),
            mood_features.get('driving', 0.5),
            mood_features.get('experimental', 0.5)
        ])
        
        # Harmonic-Features
        vector.append(features.get('harmonic_ratio', 0.5))
        vector.append(features.get('percussive_ratio', 0.5))
        
        # Spectral-Features (MFCC-Zusammenfassung)
        mfcc_mean = features.get('mfcc_mean', [0.0] * 13)
        if isinstance(mfcc_mean, list) and len(mfcc_mean) >= 3:
            vector.extend(mfcc_mean[:3])  # Nur erste 3 MFCCs
        else:
            vector.extend([0.0, 0.0, 0.0])
        
        return np.array(vector, dtype=np.float32)
    
    def _encode_key_numeric(self, key: str) -> float:
        """Kodiert Tonart numerisch"""
        key_mapping = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'H': 11
        }
        
        for key_name, value in key_mapping.items():
            if key_name in key:
                return float(value) / 11.0  # Normalisiert 0-1
        
        return 0.0  # Default C
    
    def _calculate_camelot_distance(self, key1: str, key2: str) -> float:
        """Berechnet Camelot-Wheel-Distanz zwischen zwei Tonarten"""
        camelot_wheel = {
            'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 'B': '1B',
            'F#': '2B', 'C#': '3B', 'G#': '4B', 'D#': '5B', 'A#': '6B', 'F': '7B',
            'Am': '8A', 'Em': '9A', 'Bm': '10A', 'F#m': '11A', 'C#m': '12A', 'G#m': '1A',
            'D#m': '2A', 'A#m': '3A', 'Fm': '4A', 'Cm': '5A', 'Gm': '6A', 'Dm': '7A'
        }
        
        camelot1 = camelot_wheel.get(key1, '8B')
        camelot2 = camelot_wheel.get(key2, '8B')
        
        # Extrahiere Zahlen
        num1 = int(camelot1[:-1])
        num2 = int(camelot2[:-1])
        
        # Berechne minimale Distanz auf dem Kreis
        distance = min(abs(num1 - num2), 12 - abs(num1 - num2))
        
        return float(distance) / 6.0  # Normalisiert 0-1
    
    def fit_model(self):
        """Trainiert k-NN-Model mit aktueller Track-Datenbank"""
        if len(self.track_database) < 2:
            logger.warning("Nicht genügend Tracks für Model-Training")
            return
        
        # Erstelle Feature-Matrix
        feature_vectors = [track['feature_vector'] for track in self.track_database]
        self.feature_matrix = np.array(feature_vectors)
        
        # Normalisierung
        self.feature_matrix = self.scaler.fit_transform(self.feature_matrix)
        
        # Dimensionalitätsreduktion (optional)
        if self.feature_matrix.shape[1] > 10:
            self.feature_matrix = self.pca.fit_transform(self.feature_matrix)
        
        # Trainiere k-NN
        self.knn_model.fit(self.feature_matrix)
        self.is_fitted = True
        
        logger.info(f"Smart Suggestions Model trainiert mit {len(self.track_database)} Tracks")
    
    def get_similar_tracks(self, target_track_id: str, n_suggestions: int = 5, 
                          mode: str = 'harmonic') -> List[Dict[str, Any]]:
        """Findet ähnliche Tracks basierend auf k-NN"""
        if not self.is_fitted:
            self.fit_model()
        
        if not self.is_fitted:
            return []
        
        # Finde Target-Track
        target_track = None
        target_index = None
        
        for i, track in enumerate(self.track_database):
            if track['id'] == target_track_id:
                target_track = track
                target_index = i
                break
        
        if target_track is None:
            logger.warning(f"Target-Track {target_track_id} nicht gefunden")
            return []
        
        # k-NN-Suche
        target_vector = self.feature_matrix[target_index].reshape(1, -1)
        distances, indices = self.knn_model.kneighbors(
            target_vector, 
            n_neighbors=min(n_suggestions + 1, len(self.track_database))
        )
        
        # Erstelle Empfehlungen (ohne Target-Track selbst)
        suggestions = []
        for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
            if index != target_index:  # Schließe Target-Track aus
                track = self.track_database[index]
                suggestion = {
                    'track_id': track['id'],
                    'similarity_score': float(1.0 / (1.0 + distance)),  # Konvertiere Distanz zu Ähnlichkeit
                    'distance': float(distance),
                    'features': track['features'],
                    'metadata': track['metadata'],
                    'recommendation_reason': self._get_recommendation_reason(target_track, track, mode)
                }
                suggestions.append(suggestion)
                
                if len(suggestions) >= n_suggestions:
                    break
        
        return suggestions
    
    def get_surprise_me_tracks(self, playlist_context: List[str], n_suggestions: int = 3) -> List[Dict[str, Any]]:
        """Surprise-Me-Algorithmus für unerwartete aber passende Empfehlungen"""
        if not self.is_fitted or len(playlist_context) == 0:
            return self._get_random_diverse_tracks(n_suggestions)
        
        # Analysiere Playlist-Kontext
        context_features = self._analyze_playlist_context(playlist_context)
        
        # Finde diverse Tracks
        diverse_tracks = self._find_diverse_tracks(context_features, n_suggestions * 3)
        
        # Bewerte Überraschungsfaktor
        surprise_tracks = []
        for track in diverse_tracks:
            surprise_score = self._calculate_surprise_score(track, context_features)
            track['surprise_score'] = surprise_score
            surprise_tracks.append(track)
        
        # Sortiere nach Überraschungsfaktor
        surprise_tracks.sort(key=lambda x: x['surprise_score'], reverse=True)
        
        return surprise_tracks[:n_suggestions]
    
    def _analyze_playlist_context(self, playlist_track_ids: List[str]) -> Dict[str, Any]:
        """Analysiert den Kontext einer Playlist"""
        context_tracks = []
        for track_id in playlist_track_ids:
            for track in self.track_database:
                if track['id'] == track_id:
                    context_tracks.append(track)
                    break
        
        if not context_tracks:
            return {}
        
        # Berechne Durchschnitts-Features
        feature_vectors = [track['feature_vector'] for track in context_tracks]
        avg_features = np.mean(feature_vectors, axis=0)
        
        # Berechne Diversität
        diversity = np.std(feature_vectors, axis=0)
        
        return {
            'avg_features': avg_features,
            'diversity': diversity,
            'track_count': len(context_tracks),
            'energy_range': (np.min([t['features'].get('energy_score', 5) for t in context_tracks]),
                           np.max([t['features'].get('energy_score', 5) for t in context_tracks])),
            'bpm_range': (np.min([t['features'].get('bpm', 120) for t in context_tracks]),
                         np.max([t['features'].get('bpm', 120) for t in context_tracks]))
        }
    
    def _find_diverse_tracks(self, context_features: Dict[str, Any], n_candidates: int) -> List[Dict[str, Any]]:
        """Findet diverse Tracks basierend auf Kontext"""
        if not context_features:
            return self._get_random_diverse_tracks(n_candidates)
        
        diverse_tracks = []
        avg_features = context_features['avg_features']
        
        for track in self.track_database:
            # Berechne Distanz zum Durchschnitt
            distance = np.linalg.norm(track['feature_vector'] - avg_features)
            
            # Bewerte Diversität
            diversity_score = min(distance / 10.0, 1.0)  # Normalisiert
            
            track_copy = track.copy()
            track_copy['diversity_score'] = diversity_score
            diverse_tracks.append(track_copy)
        
        # Sortiere nach Diversität
        diverse_tracks.sort(key=lambda x: x['diversity_score'], reverse=True)
        
        return diverse_tracks[:n_candidates]
    
    def _calculate_surprise_score(self, track: Dict[str, Any], context_features: Dict[str, Any]) -> float:
        """Berechnet Überraschungsfaktor eines Tracks"""
        if not context_features:
            return 0.5
        
        # Diversitäts-Score
        diversity_score = track.get('diversity_score', 0.5)
        
        # Novelty-Score (basierend auf seltenen Feature-Kombinationen)
        novelty_score = self._calculate_novelty_score(track)
        
        # Serendipity-Score (unerwartete aber passende Kombinationen)
        serendipity_score = self._calculate_serendipity_score(track, context_features)
        
        # Gewichtete Kombination
        surprise_score = (
            diversity_score * 0.4 +
            novelty_score * 0.3 +
            serendipity_score * 0.3
        )
        
        return min(surprise_score, 1.0)
    
    def _calculate_novelty_score(self, track: Dict[str, Any]) -> float:
        """Berechnet Novelty-Score basierend auf Feature-Seltenheit"""
        features = track['features']
        
        # Sammle Feature-Werte aller Tracks
        all_energy_scores = [t['features'].get('energy_score', 5) for t in self.track_database]
        all_bpms = [t['features'].get('bpm', 120) for t in self.track_database]
        
        # Berechne Seltenheit
        energy_percentile = np.percentile(all_energy_scores, 50)
        bpm_percentile = np.percentile(all_bpms, 50)
        
        energy_novelty = abs(features.get('energy_score', 5) - energy_percentile) / 5.0
        bpm_novelty = abs(features.get('bpm', 120) - bpm_percentile) / 60.0
        
        return min((energy_novelty + bpm_novelty) / 2.0, 1.0)
    
    def _calculate_serendipity_score(self, track: Dict[str, Any], context_features: Dict[str, Any]) -> float:
        """Berechnet Serendipity-Score für unerwartete aber passende Tracks"""
        # Vereinfachte Serendipity-Berechnung
        # Tracks die in einer Dimension sehr unterschiedlich sind, aber in anderen passen
        
        features = track['features']
        
        energy_diff = abs(features.get('energy_score', 5) - np.mean([t['features'].get('energy_score', 5) for t in self.track_database]))
        key_compatibility = 1.0 - self._calculate_camelot_distance(features.get('key', 'C'), 'C')
        
        # Hohe Energie-Differenz aber gute Key-Kompatibilität = Serendipity
        serendipity = (energy_diff / 5.0) * key_compatibility
        
        return min(serendipity, 1.0)
    
    def _get_random_diverse_tracks(self, n_tracks: int) -> List[Dict[str, Any]]:
        """Fallback: Zufällige diverse Tracks"""
        if len(self.track_database) <= n_tracks:
            return [track.copy() for track in self.track_database]
        
        # Einfache zufällige Auswahl
        import random
        selected = random.sample(self.track_database, n_tracks)
        
        for track in selected:
            track['surprise_score'] = 0.5
            track['diversity_score'] = 0.5
        
        return selected
    
    def _get_recommendation_reason(self, target_track: Dict[str, Any], 
                                 recommended_track: Dict[str, Any], mode: str) -> str:
        """Generiert Begründung für Empfehlung"""
        target_features = target_track['features']
        rec_features = recommended_track['features']
        
        if mode == 'harmonic':
            target_key = target_features.get('key', 'Unknown')
            rec_key = rec_features.get('key', 'Unknown')
            return f"Harmonisch kompatibel: {target_key} → {rec_key}"
        
        elif mode == 'energy':
            target_energy = target_features.get('energy_score', 5)
            rec_energy = rec_features.get('energy_score', 5)
            return f"Ähnliche Energie: {target_energy:.1f} → {rec_energy:.1f}"
        
        elif mode == 'mood':
            return "Ähnliche Stimmung und Atmosphäre"
        
        else:
            return "Ähnliche Audio-Charakteristika"
    
    def save_model(self, model_path: str):
        """Speichert trainiertes Model"""
        if not self.is_fitted:
            logger.warning("Model nicht trainiert - kann nicht gespeichert werden")
            return
        
        model_data = {
            'track_database': self.track_database,
            'scaler_mean': self.scaler.mean_.tolist(),
            'scaler_scale': self.scaler.scale_.tolist(),
            'feature_matrix_shape': self.feature_matrix.shape,
            'is_fitted': self.is_fitted
        }
        
        try:
            with open(model_path, 'w') as f:
                json.dump(model_data, f, indent=2)
            logger.info(f"Smart Suggestions Model gespeichert: {model_path}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Models: {e}")
    
    def load_model(self, model_path: str):
        """Lädt gespeichertes Model"""
        try:
            with open(model_path, 'r') as f:
                model_data = json.load(f)
            
            self.track_database = model_data['track_database']
            
            # Rekonstruiere Scaler
            self.scaler.mean_ = np.array(model_data['scaler_mean'])
            self.scaler.scale_ = np.array(model_data['scaler_scale'])
            
            # Re-fit Model
            self.fit_model()
            
            logger.info(f"Smart Suggestions Model geladen: {model_path}")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Models: {e}")