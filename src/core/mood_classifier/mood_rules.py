"""Mood Rules - Heuristik-Regeln für Stimmungsklassifikation"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class MoodRules:
    """Verwaltet Heuristik-Regeln für Mood-Klassifikation"""
    
    def __init__(self, rules_path: Path = None):
        self.rules_path = rules_path or Path("data/mood_rules.json")
        self.rules = self._load_default_rules()
        self._load_custom_rules()
    
    def _load_default_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Lädt Standard-Heuristik-Regeln"""
        return {
            "euphoric": [
                {
                    "name": "high_energy_positive",
                    "description": "Hohe Energie mit positiver Valenz",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "energy", "operator": "fuzzy_high", "value": 0.7},
                        {"feature": "valence", "operator": "fuzzy_high", "value": 0.6},
                        {"feature": "tempo", "operator": ">", "value": 0.6}
                    ]
                },
                {
                    "name": "uplifting_characteristics",
                    "description": "Erhebende musikalische Eigenschaften",
                    "weight": 0.8,
                    "conditions": [
                        {"feature": "danceability", "operator": "fuzzy_high", "value": 0.7},
                        {"feature": "loudness", "operator": ">", "value": 0.5},
                        {"feature": "spectral_centroid", "operator": "fuzzy_high", "value": 0.6}
                    ]
                }
            ],
            
            "driving": [
                {
                    "name": "steady_high_energy",
                    "description": "Konstante hohe Energie mit mittlerer Valenz",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "energy", "operator": "range", "value": [0.6, 0.9]},
                        {"feature": "tempo", "operator": "fuzzy_high", "value": 0.65},
                        {"feature": "valence", "operator": "range", "value": [0.3, 0.7]}
                    ]
                },
                {
                    "name": "rhythmic_focus",
                    "description": "Starker rhythmischer Fokus",
                    "weight": 0.9,
                    "conditions": [
                        {"feature": "danceability", "operator": "fuzzy_high", "value": 0.6},
                        {"feature": "mfcc_variance", "operator": "<", "value": 0.4}
                    ]
                }
            ],
            
            "dark": [
                {
                    "name": "low_valence_intense",
                    "description": "Niedrige Valenz mit Intensität",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "valence", "operator": "fuzzy_low", "value": 0.4},
                        {"feature": "energy", "operator": ">", "value": 0.4},
                        {"feature": "loudness", "operator": ">", "value": 0.3}
                    ]
                },
                {
                    "name": "minor_key_characteristics",
                    "description": "Moll-Tonart Charakteristiken",
                    "weight": 0.7,
                    "conditions": [
                        {"feature": "spectral_centroid", "operator": "fuzzy_low", "value": 0.5},
                        {"feature": "mfcc_variance", "operator": ">", "value": 0.3}
                    ]
                }
            ],
            
            "chill": [
                {
                    "name": "low_energy_relaxed",
                    "description": "Niedrige Energie, entspannt",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "energy", "operator": "fuzzy_low", "value": 0.4},
                        {"feature": "tempo", "operator": "fuzzy_low", "value": 0.5},
                        {"feature": "loudness", "operator": "<", "value": 0.6}
                    ]
                },
                {
                    "name": "smooth_characteristics",
                    "description": "Sanfte musikalische Eigenschaften",
                    "weight": 0.8,
                    "conditions": [
                        {"feature": "danceability", "operator": "fuzzy_low", "value": 0.6},
                        {"feature": "mfcc_variance", "operator": "fuzzy_low", "value": 0.4}
                    ]
                }
            ],
            
            "melancholic": [
                {
                    "name": "sad_emotional",
                    "description": "Traurig und emotional",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "valence", "operator": "fuzzy_low", "value": 0.3},
                        {"feature": "energy", "operator": "fuzzy_low", "value": 0.5},
                        {"feature": "tempo", "operator": "<", "value": 0.6}
                    ]
                },
                {
                    "name": "introspective_qualities",
                    "description": "Introspektive Qualitäten",
                    "weight": 0.7,
                    "conditions": [
                        {"feature": "loudness", "operator": "fuzzy_low", "value": 0.5},
                        {"feature": "spectral_centroid", "operator": "fuzzy_medium", "value": 0.4}
                    ]
                }
            ],
            
            "aggressive": [
                {
                    "name": "high_intensity_harsh",
                    "description": "Hohe Intensität, hart",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "energy", "operator": "fuzzy_high", "value": 0.8},
                        {"feature": "loudness", "operator": "fuzzy_high", "value": 0.7},
                        {"feature": "spectral_centroid", "operator": "fuzzy_high", "value": 0.7}
                    ]
                },
                {
                    "name": "distorted_characteristics",
                    "description": "Verzerrte Charakteristiken",
                    "weight": 0.8,
                    "conditions": [
                        {"feature": "mfcc_variance", "operator": "fuzzy_high", "value": 0.6},
                        {"feature": "tempo", "operator": ">", "value": 0.5}
                    ]
                }
            ],
            
            "uplifting": [
                {
                    "name": "positive_energetic",
                    "description": "Positiv und energetisch",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "valence", "operator": "fuzzy_high", "value": 0.6},
                        {"feature": "energy", "operator": "range", "value": [0.5, 0.8]},
                        {"feature": "tempo", "operator": ">", "value": 0.4}
                    ]
                },
                {
                    "name": "motivational_elements",
                    "description": "Motivierende Elemente",
                    "weight": 0.8,
                    "conditions": [
                        {"feature": "danceability", "operator": ">", "value": 0.5},
                        {"feature": "loudness", "operator": "range", "value": [0.4, 0.8]}
                    ]
                }
            ],
            
            "mysterious": [
                {
                    "name": "atmospheric_ambient",
                    "description": "Atmosphärisch und ambient",
                    "weight": 1.0,
                    "conditions": [
                        {"feature": "energy", "operator": "fuzzy_medium", "value": 0.4},
                        {"feature": "valence", "operator": "fuzzy_medium", "value": 0.5},
                        {"feature": "spectral_centroid", "operator": "fuzzy_medium", "value": 0.5}
                    ]
                },
                {
                    "name": "complex_textures",
                    "description": "Komplexe Texturen",
                    "weight": 0.7,
                    "conditions": [
                        {"feature": "mfcc_variance", "operator": "fuzzy_high", "value": 0.5},
                        {"feature": "danceability", "operator": "fuzzy_low", "value": 0.6}
                    ]
                }
            ]
        }
    
    def _load_custom_rules(self):
        """Lädt benutzerdefinierte Regeln aus Datei"""
        if self.rules_path.exists():
            try:
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    custom_rules = json.load(f)
                    
                # Merge mit Standard-Regeln
                for mood, rules in custom_rules.items():
                    if mood in self.rules:
                        self.rules[mood].extend(rules)
                    else:
                        self.rules[mood] = rules
                        
                logger.info(f"Benutzerdefinierte Regeln geladen: {self.rules_path}")
                
            except Exception as e:
                logger.warning(f"Fehler beim Laden benutzerdefinierter Regeln: {e}")
    
    def save_custom_rules(self, custom_rules: Dict[str, List[Dict[str, Any]]]):
        """Speichert benutzerdefinierte Regeln"""
        try:
            self.rules_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.rules_path, 'w', encoding='utf-8') as f:
                json.dump(custom_rules, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Benutzerdefinierte Regeln gespeichert: {self.rules_path}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern benutzerdefinierter Regeln: {e}")
    
    def get_mood_categories(self) -> List[str]:
        """Gibt alle verfügbaren Stimmungskategorien zurück"""
        return list(self.rules.keys())
    
    def get_rules_for_mood(self, mood: str) -> List[Dict[str, Any]]:
        """Gibt alle Regeln für eine bestimmte Stimmung zurück"""
        return self.rules.get(mood, [])
    
    def get_all_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Gibt alle Regeln zurück"""
        return self.rules.copy()
    
    def add_rule(self, mood: str, rule: Dict[str, Any]) -> bool:
        """Fügt eine neue Regel hinzu"""
        try:
            # Regel validieren
            if not self._validate_rule(rule):
                return False
            
            if mood not in self.rules:
                self.rules[mood] = []
            
            self.rules[mood].append(rule)
            logger.info(f"Regel '{rule['name']}' für Stimmung '{mood}' hinzugefügt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Regel: {e}")
            return False
    
    def remove_rule(self, mood: str, rule_name: str) -> bool:
        """Entfernt eine Regel"""
        try:
            if mood not in self.rules:
                return False
            
            original_count = len(self.rules[mood])
            self.rules[mood] = [r for r in self.rules[mood] if r.get("name") != rule_name]
            
            if len(self.rules[mood]) < original_count:
                logger.info(f"Regel '{rule_name}' für Stimmung '{mood}' entfernt")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Fehler beim Entfernen der Regel: {e}")
            return False
    
    def _validate_rule(self, rule: Dict[str, Any]) -> bool:
        """Validiert eine Regel"""
        required_fields = ["name", "description", "conditions"]
        
        for field in required_fields:
            if field not in rule:
                logger.error(f"Regel fehlt erforderliches Feld: {field}")
                return False
        
        # Bedingungen validieren
        for condition in rule["conditions"]:
            if not self._validate_condition(condition):
                return False
        
        return True
    
    def _validate_condition(self, condition: Dict[str, Any]) -> bool:
        """Validiert eine Bedingung"""
        required_fields = ["feature", "operator", "value"]
        
        for field in required_fields:
            if field not in condition:
                logger.error(f"Bedingung fehlt erforderliches Feld: {field}")
                return False
        
        # Operator validieren
        valid_operators = [
            ">", "<", ">=", "<=", "==", "range",
            "fuzzy_high", "fuzzy_low", "fuzzy_medium"
        ]
        
        if condition["operator"] not in valid_operators:
            logger.error(f"Ungültiger Operator: {condition['operator']}")
            return False
        
        return True
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Gibt Statistiken über die Regeln zurück"""
        stats = {
            "total_moods": len(self.rules),
            "total_rules": sum(len(rules) for rules in self.rules.values()),
            "rules_per_mood": {},
            "feature_usage": {},
            "operator_usage": {},
            "average_conditions_per_rule": 0
        }
        
        total_conditions = 0
        total_rules = 0
        
        for mood, rules in self.rules.items():
            stats["rules_per_mood"][mood] = len(rules)
            
            for rule in rules:
                total_rules += 1
                conditions = rule.get("conditions", [])
                total_conditions += len(conditions)
                
                for condition in conditions:
                    feature = condition.get("feature", "unknown")
                    operator = condition.get("operator", "unknown")
                    
                    stats["feature_usage"][feature] = stats["feature_usage"].get(feature, 0) + 1
                    stats["operator_usage"][operator] = stats["operator_usage"].get(operator, 0) + 1
        
        if total_rules > 0:
            stats["average_conditions_per_rule"] = total_conditions / total_rules
        
        return stats
    
    def export_rules_template(self) -> Dict[str, Any]:
        """Exportiert eine Regel-Vorlage für Benutzer"""
        template = {
            "mood_name": [
                {
                    "name": "rule_name",
                    "description": "Beschreibung der Regel",
                    "weight": 1.0,
                    "conditions": [
                        {
                            "feature": "energy",
                            "operator": "fuzzy_high",
                            "value": 0.7
                        }
                    ]
                }
            ]
        }
        
        return {
            "template": template,
            "available_features": [
                "energy", "valence", "tempo", "danceability",
                "loudness", "spectral_centroid", "mfcc_variance"
            ],
            "available_operators": [
                ">", "<", ">=", "<=", "==", "range",
                "fuzzy_high", "fuzzy_low", "fuzzy_medium"
            ],
            "mood_categories": self.get_mood_categories()
        }