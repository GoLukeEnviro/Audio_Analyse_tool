"""Hybrid Mood Classifier - Kombiniert Heuristik-Regeln mit LightGBM-Modell"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .heuristic_classifier import HeuristicClassifier
from .ml_classifier import MLClassifier
from .mood_rules import MoodRules
from .feature_processor import FeatureProcessor

logger = logging.getLogger(__name__)

class HybridClassifier:
    """Hybrid Mood Classifier mit Heuristik + ML"""
    
    MOOD_CATEGORIES = [
        "euphoric",     # Hochenergetisch, positiv
        "driving",      # Energetisch, fokussiert
        "dark",         # Düster, intensiv
        "chill",        # Entspannt, ruhig
        "melancholic",  # Melancholisch, emotional
        "aggressive",   # Aggressiv, hart
        "uplifting",    # Erhebend, motivierend
        "mysterious"    # Mysteriös, atmosphärisch
    ]
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("data/mood_classifier_config.json")
        self.heuristic_classifier = HeuristicClassifier()
        self.ml_classifier = MLClassifier()
        self.mood_rules = MoodRules()
        self.feature_processor = FeatureProcessor()
        
        self.config = self._load_config()
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Lädt Konfiguration für Hybrid-Classifier"""
        default_config = {
            "heuristic_weight": 0.4,
            "ml_weight": 0.6,
            "confidence_threshold": 0.7,
            "fallback_to_heuristic": True,
            "feature_weights": {
                "energy": 1.0,
                "valence": 1.0,
                "tempo": 0.8,
                "danceability": 0.9,
                "loudness": 0.7,
                "spectral_centroid": 0.6,
                "mfcc_variance": 0.5
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Konfiguration: {e}")
                
        return default_config
    
    def save_config(self):
        """Speichert aktuelle Konfiguration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def classify_mood(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        """Klassifiziert Stimmung mit Hybrid-Ansatz"""
        try:
            # Feature-Preprocessing
            processed_features = self.feature_processor.process_features(features)
            
            # Heuristik-Klassifikation
            heuristic_result = self.heuristic_classifier.classify(processed_features)
            heuristic_mood = heuristic_result["mood"]
            heuristic_confidence = heuristic_result["confidence"]
            heuristic_scores = heuristic_result["scores"]
            
            # ML-Klassifikation (falls Modell trainiert)
            ml_mood = None
            ml_confidence = 0.0
            ml_scores = {mood: 0.0 for mood in self.MOOD_CATEGORIES}
            
            if self.is_trained:
                try:
                    ml_result = self.ml_classifier.predict(processed_features)
                    ml_mood = ml_result["mood"]
                    ml_confidence = ml_result["confidence"]
                    ml_scores = ml_result["scores"]
                except Exception as e:
                    logger.warning(f"ML-Klassifikation fehlgeschlagen: {e}")
            
            # Hybrid-Kombination
            final_mood, final_confidence, combined_scores = self._combine_predictions(
                heuristic_mood, heuristic_confidence, heuristic_scores,
                ml_mood, ml_confidence, ml_scores
            )
            
            return final_mood, final_confidence, combined_scores
            
        except Exception as e:
            logger.error(f"Fehler bei Mood-Klassifikation: {e}")
            return "unknown", 0.0, {mood: 0.0 for mood in self.MOOD_CATEGORIES}
    
    def _combine_predictions(self, 
                           heuristic_mood: str, heuristic_confidence: float, heuristic_scores: Dict[str, float],
                           ml_mood: Optional[str], ml_confidence: float, ml_scores: Dict[str, float]
                           ) -> Tuple[str, float, Dict[str, float]]:
        """Kombiniert Heuristik- und ML-Vorhersagen"""
        
        if not self.is_trained or ml_mood is None:
            # Fallback auf Heuristik
            return heuristic_mood, heuristic_confidence, heuristic_scores
        
        # Gewichtete Kombination der Scores
        combined_scores = {}
        heuristic_weight = self.config["heuristic_weight"]
        ml_weight = self.config["ml_weight"]
        
        for mood in self.MOOD_CATEGORIES:
            h_score = heuristic_scores.get(mood, 0.0)
            m_score = ml_scores.get(mood, 0.0)
            combined_scores[mood] = (h_score * heuristic_weight) + (m_score * ml_weight)
        
        # Beste Stimmung ermitteln
        final_mood = max(combined_scores, key=combined_scores.get)
        final_confidence = combined_scores[final_mood]
        
        # Confidence-Threshold prüfen
        if final_confidence < self.config["confidence_threshold"]:
            if self.config["fallback_to_heuristic"]:
                return heuristic_mood, heuristic_confidence, heuristic_scores
        
        return final_mood, final_confidence, combined_scores
    
    def train_ml_model(self, training_data: List[Dict[str, Any]], 
                      validation_split: float = 0.2) -> Dict[str, float]:
        """Trainiert das ML-Modell mit gelabelten Daten"""
        try:
            if len(training_data) < 10:
                raise ValueError("Mindestens 10 Trainingssamples erforderlich")
            
            # Daten vorbereiten
            features_list = []
            labels = []
            
            for sample in training_data:
                processed_features = self.feature_processor.process_features(sample["features"])
                feature_vector = self._features_to_vector(processed_features)
                features_list.append(feature_vector)
                labels.append(sample["mood"])
            
            X = np.array(features_list)
            y = np.array(labels)
            
            # Feature-Skalierung
            X_scaled = self.scaler.fit_transform(X)
            
            # ML-Modell trainieren
            metrics = self.ml_classifier.train(X_scaled, y, validation_split)
            self.is_trained = True
            
            logger.info(f"ML-Modell erfolgreich trainiert. Accuracy: {metrics.get('accuracy', 0):.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Fehler beim Training des ML-Modells: {e}")
            return {"error": str(e)}
    
    def _features_to_vector(self, features: Dict[str, float]) -> np.ndarray:
        """Konvertiert Feature-Dict zu Vektor für ML-Modell"""
        feature_order = [
            "energy", "valence", "tempo", "danceability", 
            "loudness", "spectral_centroid", "mfcc_variance"
        ]
        
        vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0.0)
            weight = self.config["feature_weights"].get(feature_name, 1.0)
            vector.append(value * weight)
        
        return np.array(vector)
    
    def get_mood_explanation(self, features: Dict[str, float], mood: str) -> Dict[str, Any]:
        """Erklärt die Mood-Klassifikation"""
        explanation = {
            "mood": mood,
            "key_features": {},
            "heuristic_rules": [],
            "confidence_factors": {}
        }
        
        # Heuristik-Erklärung
        heuristic_explanation = self.heuristic_classifier.explain_classification(features, mood)
        explanation["heuristic_rules"] = heuristic_explanation.get("applied_rules", [])
        
        # Feature-Wichtigkeit
        for feature, value in features.items():
            if feature in self.config["feature_weights"]:
                weight = self.config["feature_weights"][feature]
                explanation["key_features"][feature] = {
                    "value": value,
                    "weight": weight,
                    "contribution": value * weight
                }
        
        return explanation
    
    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über den Classifier zurück"""
        stats = {
            "is_trained": self.is_trained,
            "mood_categories": self.MOOD_CATEGORIES,
            "config": self.config.copy(),
            "heuristic_rules_count": len(self.mood_rules.get_all_rules()),
            "ml_model_info": self.ml_classifier.get_model_info() if self.is_trained else None
        }
        
        return stats
    
    def update_weights(self, heuristic_weight: float, ml_weight: float):
        """Aktualisiert Gewichtung zwischen Heuristik und ML"""
        total = heuristic_weight + ml_weight
        if total <= 0:
            raise ValueError("Gewichtungen müssen positiv sein")
        
        self.config["heuristic_weight"] = heuristic_weight / total
        self.config["ml_weight"] = ml_weight / total
        self.save_config()
    
    def reset_ml_model(self):
        """Setzt das ML-Modell zurück"""
        self.ml_classifier.reset()
        self.is_trained = False
        logger.info("ML-Modell wurde zurückgesetzt")