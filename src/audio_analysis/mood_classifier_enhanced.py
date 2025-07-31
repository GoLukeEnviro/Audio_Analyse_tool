"""Enhanced Mood Classifier - LightGBM-basierte Stimmungsklassifikation"""

import json
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

# Versuche Bibliotheken zu importieren
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("LightGBM nicht verfügbar - verwende heuristische Klassifikation")
from .feature_extractor import FeatureExtractor
from .energy_score_extractor import EnergyScoreExtractor


class EnhancedMoodClassifier:
    """Erweiterte Stimmungsklassifikation mit LightGBM und erweiterbarem Training"""
    
    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or os.path.join(os.getcwd(), 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.feature_extractor = FeatureExtractor()
        self.energy_extractor = EnergyScoreExtractor()
        
        # Mood-Kategorien für DJ-Workflows
        self.mood_categories = [
            'Dark',
            'Euphoric', 
            'Driving',
            'Experimental',
            'Progressive',
            'Peak-Time'
        ]
        
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(self.mood_categories)
        
        self.model = None
        self.feature_names = []
        
        # Heuristik-Regeln für Fallback
        self.heuristic_rules = {
            'Dark': {
                'energy_score': (1.0, 6.0),
                'spectral_centroid': (500, 3000),
                'bpm': (120, 140),
                'key_minor_weight': 0.7
            },
            'Euphoric': {
                'energy_score': (7.0, 10.0),
                'spectral_centroid': (2000, 8000),
                'bpm': (125, 135),
                'key_major_weight': 0.8
            },
            'Driving': {
                'energy_score': (6.0, 9.0),
                'spectral_centroid': (1500, 5000),
                'bpm': (120, 135),
                'onset_density': (3.0, 8.0)
            },
            'Experimental': {
                'energy_score': (2.0, 8.0),
                'spectral_centroid': (1000, 6000),
                'bpm': (80, 150),
                'irregularity_weight': 0.6
            },
            'Progressive': {
                'energy_score': (5.0, 8.0),
                'spectral_centroid': (1500, 4000),
                'bpm': (120, 130),
                'buildup_weight': 0.7
            },
            'Peak-Time': {
                'energy_score': (8.0, 10.0),
                'spectral_centroid': (2500, 7000),
                'bpm': (128, 138),
                'intensity_weight': 0.9
            }
        }
        
        # Lade existierendes Model falls vorhanden
        self.load_model()
    
    def extract_mood_features(self, audio_file: str, track_metadata: Dict[str, Any] = None) -> np.ndarray:
        """Extrahiert Feature-Vektor für Mood-Klassifikation"""
        try:
            # Audio-Features
            basic_features = self.feature_extractor.extract_features(audio_file)
            energy_features = self.energy_extractor.extract_energy_score(audio_file)
            
            # Kombiniere Features
            features = []
            
            # Energy-Features
            features.append(energy_features.get('energy_score', 5.0))
            features.append(energy_features.get('rms_loudness', -30.0))
            features.append(energy_features.get('spectral_centroid', 2000.0))
            features.append(energy_features.get('onset_density', 2.0))
            
            # Basic Audio Features
            features.append(basic_features.get('bpm', 120.0))
            features.append(basic_features.get('tempo_stability', 0.5))
            
            # Key-Features (numerisch kodiert)
            key = basic_features.get('key', 'C major')
            key_numeric = self._encode_key_numeric(key)
            features.append(key_numeric)
            
            # Ist Minor Key?
            is_minor = 1.0 if 'minor' in key.lower() or 'moll' in key.lower() else 0.0
            features.append(is_minor)
            
            # Spectral Features
            features.append(basic_features.get('spectral_rolloff', 5000.0))
            features.append(basic_features.get('zero_crossing_rate', 0.1))
            features.append(basic_features.get('mfcc_mean', 0.0))
            
            # Rhythmic Features
            features.append(basic_features.get('beat_strength', 0.5))
            features.append(basic_features.get('rhythm_regularity', 0.5))
            
            # Harmonic Features
            features.append(basic_features.get('harmonic_ratio', 0.5))
            features.append(basic_features.get('dissonance', 0.3))
            
            # Metadata-Features (falls verfügbar)
            if track_metadata:
                features.append(track_metadata.get('duration', 300.0) / 60.0)  # Minuten
                features.append(track_metadata.get('year', 2020) / 2020.0)  # Normalisiert
            else:
                features.extend([5.0, 1.0])  # Default-Werte
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            print(f"Fehler bei Mood-Feature-Extraktion für {audio_file}: {e}")
            # Fallback: Default-Features
            return np.array([5.0] * 16, dtype=np.float32)
    
    def _encode_key_numeric(self, key: str) -> float:
        """Kodiert Tonart numerisch für ML-Features"""
        key_mapping = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
            'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'H': 11
        }
        
        for key_name, value in key_mapping.items():
            if key_name in key:
                return float(value) / 11.0  # Normalisiert 0-1
        
        return 0.0  # Default C
    
    def classify_mood_heuristic(self, features: np.ndarray) -> Tuple[str, float]:
        """Heuristik-basierte Mood-Klassifikation als Fallback"""
        if len(features) < 8:
            return 'Driving', 0.5
        
        energy_score = features[0]
        spectral_centroid = features[2]
        bpm = features[4] if len(features) > 4 else 120.0
        is_minor = features[7] if len(features) > 7 else 0.0
        
        mood_scores = {}
        
        for mood, rules in self.heuristic_rules.items():
            score = 0.0
            
            # Energy Score Check
            if 'energy_score' in rules:
                min_e, max_e = rules['energy_score']
                if min_e <= energy_score <= max_e:
                    score += 0.3
            
            # Spectral Centroid Check
            if 'spectral_centroid' in rules:
                min_sc, max_sc = rules['spectral_centroid']
                if min_sc <= spectral_centroid <= max_sc:
                    score += 0.3
            
            # BPM Check
            if 'bpm' in rules:
                min_bpm, max_bpm = rules['bpm']
                if min_bpm <= bpm <= max_bpm:
                    score += 0.2
            
            # Key-spezifische Gewichtung
            if 'key_minor_weight' in rules and is_minor > 0.5:
                score += rules['key_minor_weight'] * 0.2
            elif 'key_major_weight' in rules and is_minor < 0.5:
                score += rules['key_major_weight'] * 0.2
            
            mood_scores[mood] = score
        
        # Beste Stimmung
        best_mood = max(mood_scores, key=mood_scores.get)
        confidence = mood_scores[best_mood]
        
        return best_mood, confidence
    
    def classify_mood(self, audio_file: str, track_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Klassifiziert Stimmung eines Tracks"""
        features = self.extract_mood_features(audio_file, track_metadata)
        
        if self.model is not None:
            try:
                # ML-Prediction
                prediction_proba = self.model.predict(features.reshape(1, -1))
                predicted_class = np.argmax(prediction_proba)
                confidence = float(np.max(prediction_proba))
                
                mood_label = self.label_encoder.inverse_transform([predicted_class])[0]
                
                return {
                    'mood_label': mood_label,
                    'mood_confidence': confidence,
                    'method': 'lightgbm',
                    'all_probabilities': {
                        mood: float(prob) for mood, prob in 
                        zip(self.mood_categories, prediction_proba[0])
                    }
                }
            except Exception as e:
                print(f"ML-Klassifikation fehlgeschlagen: {e}")
        
        # Fallback: Heuristik
        mood_label, confidence = self.classify_mood_heuristic(features)
        
        return {
            'mood_label': mood_label,
            'mood_confidence': confidence,
            'method': 'heuristic',
            'all_probabilities': {mood_label: confidence}
        }
    
    def train_model(self, training_data_file: str):
        """Trainiert LightGBM-Model mit Trainingsdata (falls verfügbar)"""
        if not LIGHTGBM_AVAILABLE:
            print("LightGBM nicht verfügbar - verwende heuristische Klassifikation")
            return False
            
        try:
            with open(training_data_file, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            features_list = []
            labels_list = []
            
            for entry in training_data:
                audio_file = entry['audio_file']
                mood_label = entry['mood_label']
                metadata = entry.get('metadata', {})
                
                if os.path.exists(audio_file) and mood_label in self.mood_categories:
                    features = self.extract_mood_features(audio_file, metadata)
                    features_list.append(features)
                    labels_list.append(mood_label)
            
            if len(features_list) < 10:
                print("Zu wenig Trainingsdata für ML-Training")
                return False
            
            X = np.array(features_list)
            y = self.label_encoder.transform(labels_list)
            
            # Train-Test Split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # LightGBM Training
            train_data = lgb.Dataset(X_train, label=y_train)
            valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
            
            params = {
                'objective': 'multiclass',
                'num_class': len(self.mood_categories),
                'metric': 'multi_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': 0
            }
            
            self.model = lgb.train(
                params,
                train_data,
                valid_sets=[valid_data],
                num_boost_round=100,
                callbacks=[lgb.early_stopping(10)]
            )
            
            # Evaluation
            y_pred = np.argmax(self.model.predict(X_test), axis=1)
            accuracy = accuracy_score(y_test, y_pred)
            
            print(f"Model-Accuracy: {accuracy:.3f}")
            print("Classification Report:")
            print(classification_report(y_test, y_pred, target_names=self.mood_categories))
            
            # Speichere Model
            self.save_model()
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Model-Training: {e}")
            return False
    
    def save_model(self):
        """Speichert trainiertes Model"""
        if self.model is not None and LIGHTGBM_AVAILABLE:
            model_path = os.path.join(self.model_dir, 'mood_classifier.txt')
            self.model.save_model(model_path)
            
            # Speichere Label Encoder
            encoder_path = os.path.join(self.model_dir, 'label_encoder.json')
            encoder_data = {
                'classes': self.label_encoder.classes_.tolist()
            }
            with open(encoder_path, 'w', encoding='utf-8') as f:
                json.dump(encoder_data, f, indent=2)
    
    def load_model(self):
        """Lädt gespeichertes Model"""
        if not LIGHTGBM_AVAILABLE:
            return False
            
        try:
            model_path = os.path.join(self.model_dir, 'mood_classifier.txt')
            encoder_path = os.path.join(self.model_dir, 'label_encoder.json')
            
            if os.path.exists(model_path) and os.path.exists(encoder_path):
                self.model = lgb.Booster(model_file=model_path)
                
                with open(encoder_path, 'r', encoding='utf-8') as f:
                    encoder_data = json.load(f)
                
                self.label_encoder = LabelEncoder()
                self.label_encoder.classes_ = np.array(encoder_data['classes'])
                
                print("Mood-Classifier-Model erfolgreich geladen")
                return True
        except Exception as e:
            print(f"Fehler beim Model-Laden: {e}")
        
        return False
    
    def create_training_template(self, output_file: str):
        """Erstellt Template für Trainingsdata"""
        template = [
            {
                "audio_file": "/path/to/dark_track.mp3",
                "mood_label": "Dark",
                "metadata": {
                    "duration": 360,
                    "year": 2023,
                    "genre": "Techno"
                }
            },
            {
                "audio_file": "/path/to/euphoric_track.mp3",
                "mood_label": "Euphoric",
                "metadata": {
                    "duration": 420,
                    "year": 2022,
                    "genre": "Trance"
                }
            }
        ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"Training-Template erstellt: {output_file}")