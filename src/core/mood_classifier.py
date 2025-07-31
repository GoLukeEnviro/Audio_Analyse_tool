"""Hybrid Mood Classifier - Kombiniert regelbasierte und ML-Ansätze"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Optionales LightGBM-Import
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM nicht verfügbar - verwende nur regelbasierte Klassifikation")

class HybridClassifier:
    """Hybrid Mood-Classifier mit regelbasierten und ML-Komponenten"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.use_ml = False
        
        # Mood-Kategorien
        self.mood_categories = {
            'euphoric': ['happy', 'energetic', 'uplifting', 'euphoric'],
            'dark': ['dark', 'melancholic', 'sad', 'mysterious'],
            'driving': ['driving', 'rhythmic', 'groovy', 'pumping'],
            'experimental': ['experimental', 'ambient', 'abstract', 'weird']
        }
        
        # Feature-Gewichtungen für regelbasierte Klassifikation
        self.feature_weights = {
            'tempo': 0.3,
            'energy': 0.25,
            'spectral_centroid': 0.2,
            'spectral_rolloff': 0.15,
            'zero_crossing_rate': 0.1
        }
        
        # Lade ML-Modell falls verfügbar
        if LIGHTGBM_AVAILABLE and model_path and Path(model_path).exists():
            self._load_model()
    
    def _load_model(self):
        """Lädt das trainierte LightGBM-Modell"""
        try:
            self.model = lgb.Booster(model_file=self.model_path)
            self.use_ml = True
            logger.info(f"ML-Modell geladen: {self.model_path}")
        except Exception as e:
            logger.warning(f"Konnte ML-Modell nicht laden: {e}")
            self.use_ml = False
    
    def classify_mood(self, features: Dict[str, float]) -> Dict[str, any]:
        """Klassifiziert die Stimmung basierend auf Audio-Features"""
        if self.use_ml and self.model:
            return self._ml_classification(features)
        else:
            return self._rule_based_classification(features)
    
    def _rule_based_classification(self, features: Dict[str, float]) -> Dict[str, any]:
        """Regelbasierte Stimmungsklassifikation"""
        # Normalisiere Features
        normalized_features = self._normalize_features(features)
        
        # Berechne Mood-Scores
        mood_scores = {
            'euphoric': self._calculate_euphoric_score(normalized_features),
            'dark': self._calculate_dark_score(normalized_features),
            'driving': self._calculate_driving_score(normalized_features),
            'experimental': self._calculate_experimental_score(normalized_features)
        }
        
        # Finde primäre Stimmung
        primary_mood = max(mood_scores, key=mood_scores.get)
        confidence = mood_scores[primary_mood]
        
        # Zusätzliche Metriken
        energy_level = normalized_features.get('energy', 0.5)
        valence = self._calculate_valence(normalized_features)
        danceability = self._calculate_danceability(normalized_features)
        
        return {
            'primary_mood': primary_mood,
            'confidence': confidence,
            'mood_scores': mood_scores,
            'energy_level': energy_level,
            'valence': valence,
            'danceability': danceability,
            'method': 'rule_based'
        }
    
    def _ml_classification(self, features: Dict[str, float]) -> Dict[str, any]:
        """ML-basierte Stimmungsklassifikation"""
        try:
            # Bereite Features für ML-Modell vor
            feature_vector = self._prepare_feature_vector(features)
            
            # Vorhersage
            prediction = self.model.predict([feature_vector])[0]
            
            # Konvertiere Vorhersage zu Mood-Scores
            mood_scores = self._prediction_to_mood_scores(prediction)
            
            primary_mood = max(mood_scores, key=mood_scores.get)
            confidence = mood_scores[primary_mood]
            
            return {
                'primary_mood': primary_mood,
                'confidence': confidence,
                'mood_scores': mood_scores,
                'energy_level': features.get('energy', 0.5),
                'valence': self._calculate_valence(features),
                'danceability': self._calculate_danceability(features),
                'method': 'ml'
            }
            
        except Exception as e:
            logger.error(f"ML-Klassifikation fehlgeschlagen: {e}")
            # Fallback auf regelbasierte Klassifikation
            return self._rule_based_classification(features)
    
    def _normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Normalisiert Features auf [0,1] Bereich"""
        normalized = {}
        
        # Tempo (bereits normalisiert durch /200)
        normalized['tempo'] = min(max(features.get('tempo', 0.5), 0), 1)
        
        # Energie
        normalized['energy'] = min(max(features.get('energy', 0.5), 0), 1)
        
        # Spectral Features (bereits normalisiert)
        normalized['spectral_centroid'] = min(max(features.get('spectral_centroid', 0.5), 0), 1)
        normalized['spectral_rolloff'] = min(max(features.get('spectral_rolloff', 0.5), 0), 1)
        
        # Zero Crossing Rate
        normalized['zero_crossing_rate'] = min(max(features.get('zero_crossing_rate', 0.5), 0), 1)
        
        return normalized
    
    def _calculate_euphoric_score(self, features: Dict[str, float]) -> float:
        """Berechnet Euphoric-Score"""
        tempo_factor = features.get('tempo', 0.5)
        energy_factor = features.get('energy', 0.5)
        brightness_factor = features.get('spectral_centroid', 0.5)
        
        # Euphoric = hohe Energie + schnelles Tempo + Helligkeit
        score = (tempo_factor * 0.4 + energy_factor * 0.4 + brightness_factor * 0.2)
        return min(score, 1.0)
    
    def _calculate_dark_score(self, features: Dict[str, float]) -> float:
        """Berechnet Dark-Score"""
        energy_factor = features.get('energy', 0.5)
        brightness_factor = features.get('spectral_centroid', 0.5)
        
        # Dark = niedrige Helligkeit + variable Energie
        score = (1 - brightness_factor) * 0.6 + (1 - abs(energy_factor - 0.3)) * 0.4
        return min(score, 1.0)
    
    def _calculate_driving_score(self, features: Dict[str, float]) -> float:
        """Berechnet Driving-Score"""
        tempo_factor = features.get('tempo', 0.5)
        energy_factor = features.get('energy', 0.5)
        zcr_factor = features.get('zero_crossing_rate', 0.5)
        
        # Driving = konstante Energie + mittleres bis hohes Tempo + Rhythmus
        score = (energy_factor * 0.4 + tempo_factor * 0.3 + zcr_factor * 0.3)
        return min(score, 1.0)
    
    def _calculate_experimental_score(self, features: Dict[str, float]) -> float:
        """Berechnet Experimental-Score"""
        # Experimental = hohe Varianz in Features
        feature_values = list(features.values())
        variance = np.var(feature_values) if feature_values else 0
        
        # Normalisiere Varianz
        score = min(variance * 4, 1.0)  # Skalierungsfaktor
        return score
    
    def _calculate_valence(self, features: Dict[str, float]) -> float:
        """Berechnet Valence (Positivität)"""
        tempo_factor = features.get('tempo', 0.5)
        energy_factor = features.get('energy', 0.5)
        brightness_factor = features.get('spectral_centroid', 0.5)
        
        # Valence = Kombination aus Tempo, Energie und Helligkeit
        valence = (tempo_factor * 0.3 + energy_factor * 0.4 + brightness_factor * 0.3)
        return min(valence, 1.0)
    
    def _calculate_danceability(self, features: Dict[str, float]) -> float:
        """Berechnet Danceability"""
        tempo_factor = features.get('tempo', 0.5)
        energy_factor = features.get('energy', 0.5)
        
        # Danceability = Energie + optimales Tempo (120-140 BPM normalisiert)
        optimal_tempo_range = 0.6  # 120 BPM normalisiert
        tempo_score = 1 - abs(tempo_factor - optimal_tempo_range)
        
        danceability = (energy_factor * 0.6 + tempo_score * 0.4)
        return min(danceability, 1.0)
    
    def _prepare_feature_vector(self, features: Dict[str, float]) -> List[float]:
        """Bereitet Feature-Vektor für ML-Modell vor"""
        # Standard-Feature-Reihenfolge für ML-Modell
        feature_order = [
            'tempo', 'energy', 'spectral_centroid', 'spectral_rolloff',
            'zero_crossing_rate', 'mfcc_mean', 'chroma_mean'
        ]
        
        vector = []
        for feature_name in feature_order:
            vector.append(features.get(feature_name, 0.5))
        
        return vector
    
    def _prediction_to_mood_scores(self, prediction: float) -> Dict[str, float]:
        """Konvertiert ML-Vorhersage zu Mood-Scores"""
        # Vereinfachte Konvertierung - in der Praxis würde das Modell
        # direkt Mood-Scores ausgeben
        if prediction > 0.7:
            return {'euphoric': 0.8, 'dark': 0.1, 'driving': 0.6, 'experimental': 0.2}
        elif prediction > 0.4:
            return {'euphoric': 0.3, 'dark': 0.2, 'driving': 0.8, 'experimental': 0.3}
        elif prediction > 0.2:
            return {'euphoric': 0.2, 'dark': 0.7, 'driving': 0.3, 'experimental': 0.4}
        else:
            return {'euphoric': 0.1, 'dark': 0.3, 'driving': 0.2, 'experimental': 0.8}
    
    def get_mood_description(self, mood: str) -> str:
        """Gibt eine Beschreibung für eine Stimmung zurück"""
        descriptions = {
            'euphoric': 'Euphorisch - Energiegeladen und positiv',
            'dark': 'Dunkel - Melancholisch und mysteriös',
            'driving': 'Treibend - Rhythmisch und groovy',
            'experimental': 'Experimentell - Abstrakt und unkonventionell'
        }
        return descriptions.get(mood, 'Unbekannte Stimmung')
    
    def get_compatible_moods(self, mood: str) -> List[str]:
        """Gibt kompatible Stimmungen für Playlist-Erstellung zurück"""
        compatibility_matrix = {
            'euphoric': ['euphoric', 'driving'],
            'dark': ['dark', 'experimental'],
            'driving': ['driving', 'euphoric', 'experimental'],
            'experimental': ['experimental', 'dark', 'driving']
        }
        return compatibility_matrix.get(mood, [mood])