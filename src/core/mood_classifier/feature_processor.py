"""Feature Processor - Aufbereitung von Audio-Features für Mood-Klassifikation"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class FeatureProcessor:
    """Verarbeitet und normalisiert Audio-Features für Mood-Klassifikation"""
    
    def __init__(self):
        # Feature-Normalisierungsbereiche (basierend auf typischen Audio-Werten)
        self.feature_ranges = {
            "energy": (0.0, 1.0),
            "valence": (0.0, 1.0),
            "tempo": (60.0, 200.0),  # BPM
            "danceability": (0.0, 1.0),
            "loudness": (-60.0, 0.0),  # dB
            "spectral_centroid": (0.0, 8000.0),  # Hz
            "mfcc_variance": (0.0, 100.0),
            "key": (0, 11),  # Chromatic scale
            "mode": (0, 1),  # Major/Minor
            "acousticness": (0.0, 1.0),
            "instrumentalness": (0.0, 1.0),
            "liveness": (0.0, 1.0),
            "speechiness": (0.0, 1.0)
        }
        
        # Feature-Gewichtungen für verschiedene Mood-Aspekte
        self.mood_feature_weights = {
            "energy_related": {
                "energy": 1.0,
                "loudness": 0.8,
                "tempo": 0.9
            },
            "emotional_related": {
                "valence": 1.0,
                "mode": 0.7,
                "acousticness": 0.6
            },
            "rhythmic_related": {
                "danceability": 1.0,
                "tempo": 0.8,
                "energy": 0.7
            },
            "timbral_related": {
                "spectral_centroid": 1.0,
                "mfcc_variance": 0.9,
                "instrumentalness": 0.6
            }
        }
    
    def process_features(self, raw_features: Dict[str, Any]) -> Dict[str, float]:
        """Verarbeitet und normalisiert rohe Audio-Features"""
        try:
            processed = {}
            
            # Basis-Features normalisieren
            for feature_name, value in raw_features.items():
                if feature_name in self.feature_ranges:
                    normalized_value = self._normalize_feature(feature_name, value)
                    processed[feature_name] = normalized_value
            
            # Abgeleitete Features berechnen
            derived_features = self._calculate_derived_features(processed)
            processed.update(derived_features)
            
            # Feature-Validierung
            processed = self._validate_features(processed)
            
            return processed
            
        except Exception as e:
            logger.error(f"Fehler bei Feature-Verarbeitung: {e}")
            return self._get_default_features()
    
    def _normalize_feature(self, feature_name: str, value: Any) -> float:
        """Normalisiert einen einzelnen Feature-Wert"""
        try:
            # Wert zu float konvertieren
            if isinstance(value, (list, np.ndarray)):
                value = float(np.mean(value))
            else:
                value = float(value)
            
            # Normalisierungsbereich abrufen
            min_val, max_val = self.feature_ranges[feature_name]
            
            # Normalisierung
            if max_val == min_val:
                return 0.5  # Fallback für konstante Bereiche
            
            normalized = (value - min_val) / (max_val - min_val)
            
            # Auf [0, 1] begrenzen
            return max(0.0, min(1.0, normalized))
            
        except Exception as e:
            logger.warning(f"Fehler bei Normalisierung von {feature_name}: {e}")
            return 0.5  # Fallback-Wert
    
    def _calculate_derived_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Berechnet abgeleitete Features"""
        derived = {}
        
        try:
            # Energie-Dynamik (Kombination aus Energy und Loudness)
            if "energy" in features and "loudness" in features:
                derived["energy_dynamics"] = (features["energy"] * 0.7 + features["loudness"] * 0.3)
            
            # Emotionale Intensität (Valence + Energy)
            if "valence" in features and "energy" in features:
                derived["emotional_intensity"] = abs(features["valence"] - 0.5) * features["energy"]
            
            # Rhythmische Komplexität
            if "danceability" in features and "tempo" in features:
                tempo_factor = 1.0 - abs(features["tempo"] - 0.6)  # Optimal bei ~120 BPM
                derived["rhythmic_complexity"] = features["danceability"] * tempo_factor
            
            # Harmonische Spannung (basierend auf Mode und Key)
            if "mode" in features:
                # Minor = höhere Spannung
                derived["harmonic_tension"] = 1.0 - features["mode"]
            
            # Klangfarben-Helligkeit
            if "spectral_centroid" in features and "mfcc_variance" in features:
                derived["timbral_brightness"] = (features["spectral_centroid"] * 0.8 + 
                                                (1.0 - features["mfcc_variance"]) * 0.2)
            
            # Aggressivität (Energy + Loudness + Spectral Centroid)
            if all(f in features for f in ["energy", "loudness", "spectral_centroid"]):
                derived["aggressiveness"] = (features["energy"] * 0.4 + 
                                            features["loudness"] * 0.3 + 
                                            features["spectral_centroid"] * 0.3)
            
            # Entspannung (umgekehrt zu Energy und Tempo)
            if "energy" in features and "tempo" in features:
                derived["relaxation"] = 1.0 - (features["energy"] * 0.6 + features["tempo"] * 0.4)
            
        except Exception as e:
            logger.warning(f"Fehler bei Berechnung abgeleiteter Features: {e}")
        
        return derived
    
    def _validate_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Validiert und bereinigt Features"""
        validated = {}
        
        for feature_name, value in features.items():
            # NaN und Inf prüfen
            if np.isnan(value) or np.isinf(value):
                logger.warning(f"Ungültiger Wert für {feature_name}: {value}")
                value = 0.5  # Fallback
            
            # Bereich prüfen
            if not (0.0 <= value <= 1.0):
                logger.warning(f"Wert außerhalb des Bereichs für {feature_name}: {value}")
                value = max(0.0, min(1.0, value))
            
            validated[feature_name] = value
        
        return validated
    
    def _get_default_features(self) -> Dict[str, float]:
        """Gibt Standard-Features zurück (Fallback)"""
        return {
            "energy": 0.5,
            "valence": 0.5,
            "tempo": 0.5,
            "danceability": 0.5,
            "loudness": 0.5,
            "spectral_centroid": 0.5,
            "mfcc_variance": 0.5
        }
    
    def extract_mood_specific_features(self, features: Dict[str, float], 
                                     mood_aspect: str) -> Dict[str, float]:
        """Extrahiert Features für einen spezifischen Mood-Aspekt"""
        if mood_aspect not in self.mood_feature_weights:
            return features
        
        weights = self.mood_feature_weights[mood_aspect]
        mood_features = {}
        
        for feature_name, weight in weights.items():
            if feature_name in features:
                mood_features[feature_name] = features[feature_name] * weight
        
        return mood_features
    
    def calculate_feature_similarity(self, features1: Dict[str, float], 
                                   features2: Dict[str, float]) -> float:
        """Berechnet Ähnlichkeit zwischen zwei Feature-Sets"""
        try:
            common_features = set(features1.keys()) & set(features2.keys())
            
            if not common_features:
                return 0.0
            
            similarities = []
            for feature in common_features:
                # Euklidische Distanz normalisiert
                diff = abs(features1[feature] - features2[feature])
                similarity = 1.0 - diff  # Je kleiner der Unterschied, desto höher die Ähnlichkeit
                similarities.append(similarity)
            
            return np.mean(similarities)
            
        except Exception as e:
            logger.error(f"Fehler bei Ähnlichkeitsberechnung: {e}")
            return 0.0
    
    def get_feature_statistics(self, feature_sets: List[Dict[str, float]]) -> Dict[str, Any]:
        """Berechnet Statistiken über mehrere Feature-Sets"""
        if not feature_sets:
            return {}
        
        stats = {}
        
        # Alle verfügbaren Features sammeln
        all_features = set()
        for fs in feature_sets:
            all_features.update(fs.keys())
        
        for feature in all_features:
            values = [fs.get(feature, 0.0) for fs in feature_sets]
            
            stats[feature] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values)
            }
        
        return stats
    
    def create_feature_vector(self, features: Dict[str, float], 
                            feature_order: Optional[List[str]] = None) -> np.ndarray:
        """Erstellt einen Feature-Vektor in definierter Reihenfolge"""
        if feature_order is None:
            feature_order = [
                "energy", "valence", "tempo", "danceability",
                "loudness", "spectral_centroid", "mfcc_variance"
            ]
        
        vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0.5)  # Fallback auf Mittelwert
            vector.append(value)
        
        return np.array(vector)
    
    def analyze_feature_distribution(self, feature_sets: List[Dict[str, float]], 
                                   mood_labels: List[str]) -> Dict[str, Any]:
        """Analysiert Feature-Verteilung pro Mood"""
        analysis = {}
        
        # Nach Moods gruppieren
        mood_groups = {}
        for features, mood in zip(feature_sets, mood_labels):
            if mood not in mood_groups:
                mood_groups[mood] = []
            mood_groups[mood].append(features)
        
        # Statistiken pro Mood berechnen
        for mood, mood_features in mood_groups.items():
            mood_stats = self.get_feature_statistics(mood_features)
            analysis[mood] = {
                "count": len(mood_features),
                "feature_stats": mood_stats
            }
        
        # Feature-Wichtigkeit pro Mood
        feature_importance = self._calculate_mood_feature_importance(mood_groups)
        analysis["feature_importance"] = feature_importance
        
        return analysis
    
    def _calculate_mood_feature_importance(self, mood_groups: Dict[str, List[Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
        """Berechnet Feature-Wichtigkeit für jede Stimmung"""
        importance = {}
        
        # Alle Features sammeln
        all_features = set()
        for mood_features in mood_groups.values():
            for features in mood_features:
                all_features.update(features.keys())
        
        for mood in mood_groups.keys():
            importance[mood] = {}
            mood_features = mood_groups[mood]
            
            if not mood_features:
                continue
            
            # Durchschnittswerte für diese Stimmung
            mood_means = {}
            for feature in all_features:
                values = [fs.get(feature, 0.5) for fs in mood_features]
                mood_means[feature] = np.mean(values)
            
            # Vergleich mit Gesamtdurchschnitt
            all_features_flat = []
            for mood_features_list in mood_groups.values():
                all_features_flat.extend(mood_features_list)
            
            global_means = {}
            for feature in all_features:
                values = [fs.get(feature, 0.5) for fs in all_features_flat]
                global_means[feature] = np.mean(values)
            
            # Wichtigkeit als Abweichung vom Gesamtdurchschnitt
            for feature in all_features:
                diff = abs(mood_means[feature] - global_means[feature])
                importance[mood][feature] = diff
        
        return importance
    
    def get_processing_info(self) -> Dict[str, Any]:
        """Gibt Informationen über den Feature-Processor zurück"""
        return {
            "supported_features": list(self.feature_ranges.keys()),
            "feature_ranges": self.feature_ranges,
            "mood_aspects": list(self.mood_feature_weights.keys()),
            "derived_features": [
                "energy_dynamics", "emotional_intensity", "rhythmic_complexity",
                "harmonic_tension", "timbral_brightness", "aggressiveness", "relaxation"
            ]
        }