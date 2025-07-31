"""Heuristic Mood Classifier - Regelbasierte Stimmungsklassifikation"""

import logging
from typing import Dict, List, Tuple, Any

from .mood_rules import MoodRules

logger = logging.getLogger(__name__)

class HeuristicClassifier:
    """Regelbasierter Mood-Classifier"""
    
    def __init__(self):
        self.mood_rules = MoodRules()
        
    def classify(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Klassifiziert Stimmung basierend auf Heuristik-Regeln"""
        try:
            mood_scores = {}
            applied_rules = []
            
            # Alle Regeln durchgehen
            for mood_category in self.mood_rules.get_mood_categories():
                rules = self.mood_rules.get_rules_for_mood(mood_category)
                score = 0.0
                category_rules = []
                
                for rule in rules:
                    rule_score = self._evaluate_rule(rule, features)
                    if rule_score > 0:
                        score += rule_score
                        category_rules.append({
                            "rule": rule["name"],
                            "score": rule_score,
                            "description": rule["description"]
                        })
                
                mood_scores[mood_category] = min(score, 1.0)  # Cap bei 1.0
                if category_rules:
                    applied_rules.extend(category_rules)
            
            # Beste Stimmung ermitteln
            if not mood_scores or max(mood_scores.values()) == 0:
                best_mood = "unknown"
                confidence = 0.0
            else:
                best_mood = max(mood_scores, key=mood_scores.get)
                confidence = mood_scores[best_mood]
            
            return {
                "mood": best_mood,
                "confidence": confidence,
                "scores": mood_scores,
                "applied_rules": applied_rules
            }
            
        except Exception as e:
            logger.error(f"Fehler bei heuristischer Klassifikation: {e}")
            return {
                "mood": "unknown",
                "confidence": 0.0,
                "scores": {},
                "applied_rules": []
            }
    
    def _evaluate_rule(self, rule: Dict[str, Any], features: Dict[str, float]) -> float:
        """Evaluiert eine einzelne Regel"""
        try:
            conditions = rule["conditions"]
            weight = rule.get("weight", 1.0)
            
            # Alle Bedingungen prüfen
            condition_scores = []
            for condition in conditions:
                score = self._evaluate_condition(condition, features)
                condition_scores.append(score)
            
            # Regel-Score berechnen (alle Bedingungen müssen erfüllt sein)
            if not condition_scores:
                return 0.0
            
            # Minimum aller Bedingungen (AND-Verknüpfung)
            rule_score = min(condition_scores) * weight
            return max(0.0, rule_score)
            
        except Exception as e:
            logger.warning(f"Fehler bei Regel-Evaluation: {e}")
            return 0.0
    
    def _evaluate_condition(self, condition: Dict[str, Any], features: Dict[str, float]) -> float:
        """Evaluiert eine einzelne Bedingung"""
        feature_name = condition["feature"]
        operator = condition["operator"]
        threshold = condition["value"]
        
        if feature_name not in features:
            return 0.0
        
        feature_value = features[feature_name]
        
        # Verschiedene Operatoren
        if operator == ">":
            return 1.0 if feature_value > threshold else 0.0
        elif operator == "<":
            return 1.0 if feature_value < threshold else 0.0
        elif operator == ">=":
            return 1.0 if feature_value >= threshold else 0.0
        elif operator == "<=":
            return 1.0 if feature_value <= threshold else 0.0
        elif operator == "==":
            return 1.0 if abs(feature_value - threshold) < 0.01 else 0.0
        elif operator == "range":
            # Threshold ist [min, max]
            min_val, max_val = threshold
            return 1.0 if min_val <= feature_value <= max_val else 0.0
        elif operator == "fuzzy_high":
            # Fuzzy-Logik für "hoch"
            return self._fuzzy_high(feature_value, threshold)
        elif operator == "fuzzy_low":
            # Fuzzy-Logik für "niedrig"
            return self._fuzzy_low(feature_value, threshold)
        elif operator == "fuzzy_medium":
            # Fuzzy-Logik für "mittel"
            return self._fuzzy_medium(feature_value, threshold)
        else:
            logger.warning(f"Unbekannter Operator: {operator}")
            return 0.0
    
    def _fuzzy_high(self, value: float, threshold: float) -> float:
        """Fuzzy-Logik für 'hoch' (S-förmige Kurve)"""
        if value >= threshold:
            return 1.0
        elif value >= threshold * 0.7:
            # Graduelle Zunahme
            return (value - threshold * 0.7) / (threshold * 0.3)
        else:
            return 0.0
    
    def _fuzzy_low(self, value: float, threshold: float) -> float:
        """Fuzzy-Logik für 'niedrig' (umgekehrte S-Kurve)"""
        if value <= threshold:
            return 1.0
        elif value <= threshold * 1.3:
            # Graduelle Abnahme
            return 1.0 - (value - threshold) / (threshold * 0.3)
        else:
            return 0.0
    
    def _fuzzy_medium(self, value: float, threshold: float) -> float:
        """Fuzzy-Logik für 'mittel' (Dreieck-Funktion)"""
        center = threshold
        width = threshold * 0.2  # 20% Breite
        
        if abs(value - center) <= width:
            return 1.0 - abs(value - center) / width
        else:
            return 0.0
    
    def explain_classification(self, features: Dict[str, float], mood: str) -> Dict[str, Any]:
        """Erklärt die Klassifikation für eine bestimmte Stimmung"""
        explanation = {
            "mood": mood,
            "applied_rules": [],
            "feature_analysis": {},
            "rule_scores": {}
        }
        
        rules = self.mood_rules.get_rules_for_mood(mood)
        
        for rule in rules:
            rule_score = self._evaluate_rule(rule, features)
            
            rule_info = {
                "name": rule["name"],
                "description": rule["description"],
                "score": rule_score,
                "weight": rule.get("weight", 1.0),
                "conditions": []
            }
            
            # Bedingungen analysieren
            for condition in rule["conditions"]:
                condition_score = self._evaluate_condition(condition, features)
                feature_name = condition["feature"]
                
                condition_info = {
                    "feature": feature_name,
                    "operator": condition["operator"],
                    "threshold": condition["value"],
                    "actual_value": features.get(feature_name, 0.0),
                    "score": condition_score,
                    "satisfied": condition_score > 0.5
                }
                
                rule_info["conditions"].append(condition_info)
            
            explanation["applied_rules"].append(rule_info)
            explanation["rule_scores"][rule["name"]] = rule_score
        
        # Feature-Analyse
        for feature_name, value in features.items():
            explanation["feature_analysis"][feature_name] = {
                "value": value,
                "normalized": min(max(value, 0.0), 1.0),
                "interpretation": self._interpret_feature_value(feature_name, value)
            }
        
        return explanation
    
    def _interpret_feature_value(self, feature_name: str, value: float) -> str:
        """Interpretiert einen Feature-Wert"""
        interpretations = {
            "energy": {
                (0.0, 0.3): "niedrig",
                (0.3, 0.7): "mittel", 
                (0.7, 1.0): "hoch"
            },
            "valence": {
                (0.0, 0.3): "negativ",
                (0.3, 0.7): "neutral",
                (0.7, 1.0): "positiv"
            },
            "tempo": {
                (0.0, 0.4): "langsam",
                (0.4, 0.7): "mittel",
                (0.7, 1.0): "schnell"
            },
            "danceability": {
                (0.0, 0.4): "wenig tanzbar",
                (0.4, 0.7): "mäßig tanzbar",
                (0.7, 1.0): "sehr tanzbar"
            }
        }
        
        if feature_name not in interpretations:
            return f"Wert: {value:.2f}"
        
        for (min_val, max_val), interpretation in interpretations[feature_name].items():
            if min_val <= value < max_val:
                return interpretation
        
        return f"Wert: {value:.2f}"
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Regeln zurück"""
        stats = {
            "total_rules": 0,
            "rules_per_mood": {},
            "feature_usage": {},
            "operator_usage": {}
        }
        
        for mood in self.mood_rules.get_mood_categories():
            rules = self.mood_rules.get_rules_for_mood(mood)
            stats["rules_per_mood"][mood] = len(rules)
            stats["total_rules"] += len(rules)
            
            # Feature-Nutzung analysieren
            for rule in rules:
                for condition in rule["conditions"]:
                    feature = condition["feature"]
                    operator = condition["operator"]
                    
                    stats["feature_usage"][feature] = stats["feature_usage"].get(feature, 0) + 1
                    stats["operator_usage"][operator] = stats["operator_usage"].get(operator, 0) + 1
        
        return stats