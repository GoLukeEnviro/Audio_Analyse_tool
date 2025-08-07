"""Mood Classifier - Stimmungsklassifikation für Backend"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)


class MoodClassifier:
    """Vereinfachter Mood Classifier für headless Backend mit Heuristik-basierten Regeln"""
    
    MOOD_CATEGORIES = [
        "euphoric",     # Hochenergetisch, positiv
        "driving",      # Energetisch, fokussiert
        "dark",         # Düster, intensiv
        "chill",        # Entspannt, ruhig
        "melancholic",  # Melancholisch, emotional
        "aggressive",   # Aggressiv, hart
        "uplifting",    # Erhebend, motivierend
        "mysterious",   # Mysteriös, atmosphärisch
        "neutral"       # Neutral/unbekannt
    ]
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("data/mood_config.json")
        self.config = self._load_config()
        self.mood_rules = self._create_mood_rules()
        
    def _load_config(self) -> Dict[str, Any]:
        """Lädt Konfiguration für Mood-Klassifikation"""
        default_config = {
            "confidence_threshold": 0.5,
            "feature_weights": {
                "energy": 1.0,
                "valence": 1.0,
                "bpm": 0.8,
                "danceability": 0.9,
                "loudness": 0.7,
                "spectral_centroid": 0.6,
                "mode": 0.5
            },
            "mood_combinations": {
                "euphoric": {"energy": [0.7, 1.0], "valence": [0.6, 1.0], "danceability": [0.6, 1.0]},
                "driving": {"energy": [0.6, 0.9], "valence": [0.3, 0.7], "bpm": [110, 140]},
                "dark": {"valence": [0.0, 0.4], "energy": [0.4, 0.8], "mode": "minor"},
                "chill": {"energy": [0.0, 0.4], "valence": [0.4, 0.8], "bpm": [60, 110]},
                "melancholic": {"valence": [0.0, 0.3], "energy": [0.0, 0.5], "mode": "minor"},
                "aggressive": {"energy": [0.7, 1.0], "valence": [0.0, 0.3], "loudness": [-5, 0]},
                "uplifting": {"valence": [0.7, 1.0], "energy": [0.5, 0.9], "danceability": [0.6, 1.0]},
                "mysterious": {"valence": [0.2, 0.6], "energy": [0.3, 0.7], "spectral_centroid": [0.0, 0.5]}
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Mood-Konfiguration: {e}")
                
        return default_config
    
    def _create_mood_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Erstellt heuristische Regeln für Mood-Klassifikation"""
        rules = {}
        
        for mood, conditions in self.config["mood_combinations"].items():
            rules[mood] = []
            
            # Hauptregel für jede Stimmung
            rule = {
                "name": f"{mood}_main",
                "description": f"Hauptregel für {mood}",
                "weight": 1.0,
                "conditions": []
            }
            
            for feature, criteria in conditions.items():
                if isinstance(criteria, list) and len(criteria) == 2:
                    # Bereichs-Bedingung
                    rule["conditions"].append({
                        "feature": feature,
                        "operator": "range",
                        "value": criteria
                    })
                elif isinstance(criteria, str):
                    # String-Bedingung (z.B. mode)
                    rule["conditions"].append({
                        "feature": feature,
                        "operator": "equals",
                        "value": criteria
                    })
                else:
                    # Einzelwert-Bedingung
                    rule["conditions"].append({
                        "feature": feature,
                        "operator": "fuzzy_high",
                        "value": criteria
                    })
            
            rules[mood].append(rule)
        
        return rules
    
    def classify_mood(self, features: Dict[str, Any]) -> Tuple[str, float, Dict[str, float]]:
        """Klassifiziert Stimmung basierend auf Audio-Features"""
        try:
            # Normalisiere Features
            normalized_features = self._normalize_features(features)
            
            # Berechne Scores für alle Stimmungen
            mood_scores = {}
            
            for mood in self.MOOD_CATEGORIES[:-1]:  # Ohne 'neutral'
                score = self._calculate_mood_score(mood, normalized_features)
                mood_scores[mood] = score
            
            # Beste Stimmung ermitteln
            if not mood_scores or max(mood_scores.values()) < self.config["confidence_threshold"]:
                best_mood = "neutral"
                confidence = 0.0
            else:
                best_mood = max(mood_scores, key=mood_scores.get)
                confidence = mood_scores[best_mood]
            
            # Füge neutral zur Ausgabe hinzu
            mood_scores["neutral"] = 1.0 - max(mood_scores.values()) if mood_scores else 1.0
            
            return best_mood, confidence, mood_scores
            
        except Exception as e:
            logger.error(f"Fehler bei Mood-Klassifikation: {e}")
            return "neutral", 0.0, {mood: 0.0 for mood in self.MOOD_CATEGORIES}
    
    def _normalize_features(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Normalisiert und konvertiert Features für Mood-Analyse"""
        normalized = {}
        
        # Standard-Normalisierungen
        normalized['energy'] = float(features.get('energy', 0.5))
        normalized['valence'] = float(features.get('valence', 0.5))
        normalized['danceability'] = float(features.get('danceability', 0.5))
        
        # BPM behandeln (kann absolute Werte haben)
        bpm = features.get('bpm', 120.0)
        if isinstance(bpm, (int, float)) and bpm > 10:
            # Absolute BPM zu normalisierten Werten
            normalized['bpm'] = min(1.0, max(0.0, (bpm - 60) / 140))  # 60-200 BPM Range
        else:
            normalized['bpm'] = float(bpm)
        
        # Loudness behandeln (meist in dB)
        loudness = features.get('loudness', -10.0)
        if isinstance(loudness, (int, float)) and loudness < 10:
            # dB zu normalisiert (-60dB bis 0dB)
            normalized['loudness'] = min(1.0, max(0.0, (loudness + 60) / 60))
        else:
            normalized['loudness'] = float(loudness)
        
        # Spectral Centroid normalisieren
        spectral_centroid = features.get('spectral_centroid', 0.5)
        if isinstance(spectral_centroid, (int, float)) and spectral_centroid > 10:
            # Absolute Hz zu normalisiert
            normalized['spectral_centroid'] = min(1.0, max(0.0, spectral_centroid / 8000))
        else:
            normalized['spectral_centroid'] = float(spectral_centroid)
        
        # Mode behandeln
        mode = features.get('mode', 'major')
        if isinstance(mode, str):
            normalized['mode'] = mode.lower()
        elif isinstance(mode, (int, float)):
            normalized['mode'] = 'major' if mode > 0.5 else 'minor'
        else:
            normalized['mode'] = 'major'
        
        return normalized
    
    def _calculate_mood_score(self, mood: str, features: Dict[str, float]) -> float:
        """Berechnet Score für eine spezifische Stimmung"""
        if mood not in self.mood_rules:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for rule in self.mood_rules[mood]:
            rule_score = self._evaluate_rule(rule, features)
            rule_weight = rule.get('weight', 1.0)
            
            total_score += rule_score * rule_weight
            total_weight += rule_weight
        
        if total_weight == 0:
            return 0.0
        
        return min(1.0, total_score / total_weight)
    
    def _evaluate_rule(self, rule: Dict[str, Any], features: Dict[str, float]) -> float:
        """Evaluiert eine einzelne Regel"""
        conditions = rule.get('conditions', [])
        if not conditions:
            return 0.0
        
        condition_scores = []
        
        for condition in conditions:
            score = self._evaluate_condition(condition, features)
            condition_scores.append(score)
        
        # AND-Verknüpfung: alle Bedingungen müssen erfüllt sein
        return min(condition_scores) if condition_scores else 0.0
    
    def _evaluate_condition(self, condition: Dict[str, Any], features: Dict[str, float]) -> float:
        """Evaluiert eine einzelne Bedingung"""
        feature_name = condition['feature']
        operator = condition['operator']
        value = condition['value']
        
        if feature_name not in features:
            return 0.0
        
        feature_value = features[feature_name]
        
        if operator == "range":
            # Bereichs-Check mit Fuzzy-Logic
            if isinstance(value, list) and len(value) == 2:
                min_val, max_val = value
                if min_val <= feature_value <= max_val:
                    return 1.0
                elif feature_value < min_val:
                    # Fuzzy falloff unter dem Minimum
                    distance = min_val - feature_value
                    return max(0.0, 1.0 - (distance / 0.2))  # 0.2 = Fuzzy-Bereich
                else:
                    # Fuzzy falloff über dem Maximum
                    distance = feature_value - max_val
                    return max(0.0, 1.0 - (distance / 0.2))
            return 0.0
        
        elif operator == "fuzzy_high":
            # Fuzzy "hoch" - S-förmige Kurve
            threshold = float(value)
            if feature_value >= threshold:
                return 1.0
            elif feature_value >= threshold - 0.2:
                # Linearer Anstieg im Fuzzy-Bereich
                return (feature_value - (threshold - 0.2)) / 0.2
            else:
                return 0.0
        
        elif operator == "fuzzy_low":
            # Fuzzy "niedrig" - umgekehrte S-förmige Kurve
            threshold = float(value)
            if feature_value <= threshold:
                return 1.0
            elif feature_value <= threshold + 0.2:
                # Linearer Abfall im Fuzzy-Bereich
                return 1.0 - ((feature_value - threshold) / 0.2)
            else:
                return 0.0
        
        elif operator == ">":
            return 1.0 if feature_value > float(value) else 0.0
        
        elif operator == "<":
            return 1.0 if feature_value < float(value) else 0.0
        
        elif operator == "equals":
            if isinstance(feature_value, str) and isinstance(value, str):
                return 1.0 if feature_value.lower() == value.lower() else 0.0
            else:
                return 1.0 if abs(feature_value - float(value)) < 0.1 else 0.0
        
        return 0.0
    
    def get_mood_explanation(self, features: Dict[str, Any], mood: str) -> Dict[str, Any]:
        """Erklärt die Mood-Klassifikation"""
        normalized_features = self._normalize_features(features)
        
        explanation = {
            "mood": mood,
            "confidence": 0.0,
            "key_features": {},
            "applied_rules": [],
            "feature_analysis": {}
        }
        
        # Berechne Score für die gegebene Stimmung
        if mood in self.mood_rules:
            score = self._calculate_mood_score(mood, normalized_features)
            explanation["confidence"] = score
            
            # Analysiere welche Regeln angewendet wurden
            for rule in self.mood_rules[mood]:
                rule_score = self._evaluate_rule(rule, normalized_features)
                if rule_score > 0:
                    explanation["applied_rules"].append({
                        "name": rule["name"],
                        "description": rule["description"],
                        "score": rule_score,
                        "weight": rule.get("weight", 1.0)
                    })
        
        # Feature-Analyse
        for feature, value in normalized_features.items():
            weight = self.config["feature_weights"].get(feature, 0.5)
            explanation["feature_analysis"][feature] = {
                "value": value,
                "weight": weight,
                "contribution": value * weight
            }
        
        return explanation
    
    def get_mood_statistics(self, track_features_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysiert Mood-Statistiken für eine Liste von Tracks"""
        mood_distribution = {mood: 0 for mood in self.MOOD_CATEGORIES}
        confidence_scores = []
        
        for features in track_features_list:
            mood, confidence, scores = self.classify_mood(features)
            mood_distribution[mood] += 1
            confidence_scores.append(confidence)
        
        total_tracks = len(track_features_list)
        
        return {
            "total_tracks": total_tracks,
            "mood_distribution": mood_distribution,
            "mood_percentages": {
                mood: (count / total_tracks * 100) if total_tracks > 0 else 0
                for mood, count in mood_distribution.items()
            },
            "average_confidence": np.mean(confidence_scores) if confidence_scores else 0.0,
            "confidence_std": np.std(confidence_scores) if confidence_scores else 0.0,
            "dominant_mood": max(mood_distribution, key=mood_distribution.get) if total_tracks > 0 else "neutral"
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Aktualisiert die Mood-Classifier-Konfiguration"""
        try:
            self.config.update(new_config)
            self.mood_rules = self._create_mood_rules()
            
            # Speichere Konfiguration
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info("Mood-Classifier-Konfiguration aktualisiert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Konfiguration: {e}")
            return False
    
    def get_mood_categories(self) -> List[str]:
        """Gibt alle verfügbaren Mood-Kategorien zurück"""
        return self.MOOD_CATEGORIES.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """Gibt aktuelle Konfiguration zurück"""
        return self.config.copy()
    
    def batch_classify(self, features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Klassifiziert eine Liste von Feature-Sets"""
        results = []
        
        for i, features in enumerate(features_list):
            mood, confidence, scores = self.classify_mood(features)
            
            results.append({
                "index": i,
                "mood": mood,
                "confidence": confidence,
                "scores": scores,
                "features_used": list(features.keys())
            })
        
        return results