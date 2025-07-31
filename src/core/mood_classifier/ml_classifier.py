"""ML Mood Classifier - LightGBM-basierte Stimmungsklassifikation"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb

logger = logging.getLogger(__name__)

class MLClassifier:
    """LightGBM-basierter Mood-Classifier"""
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or Path("data/models/mood_classifier.pkl")
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.is_trained = False
        self.training_history = []
        
        # LightGBM Parameter
        self.lgb_params = {
            'objective': 'multiclass',
            'metric': 'multi_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        self._load_model()
    
    def _load_model(self):
        """Lädt ein trainiertes Modell"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.model = model_data['model']
                self.label_encoder = model_data['label_encoder']
                self.feature_names = model_data['feature_names']
                self.training_history = model_data.get('training_history', [])
                self.is_trained = True
                
                logger.info(f"Modell geladen: {self.model_path}")
                
            except Exception as e:
                logger.warning(f"Fehler beim Laden des Modells: {e}")
    
    def save_model(self):
        """Speichert das trainierte Modell"""
        if not self.is_trained:
            logger.warning("Kein trainiertes Modell zum Speichern vorhanden")
            return
        
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'label_encoder': self.label_encoder,
                'feature_names': self.feature_names,
                'training_history': self.training_history
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Modell gespeichert: {self.model_path}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Modells: {e}")
    
    def train(self, X: np.ndarray, y: np.ndarray, validation_split: float = 0.2) -> Dict[str, float]:
        """Trainiert das LightGBM-Modell"""
        try:
            if len(X) < 10:
                raise ValueError("Mindestens 10 Trainingssamples erforderlich")
            
            # Labels encodieren
            y_encoded = self.label_encoder.fit_transform(y)
            num_classes = len(self.label_encoder.classes_)
            
            # Feature-Namen setzen
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]
            
            # Train-Validation Split
            X_train, X_val, y_train, y_val = train_test_split(
                X, y_encoded, test_size=validation_split, 
                random_state=42, stratify=y_encoded
            )
            
            # LightGBM Datasets
            train_data = lgb.Dataset(X_train, label=y_train, feature_name=self.feature_names)
            val_data = lgb.Dataset(X_val, label=y_val, feature_name=self.feature_names, reference=train_data)
            
            # Parameter für Multiclass anpassen
            params = self.lgb_params.copy()
            params['num_class'] = num_classes
            
            # Training mit Early Stopping
            self.model = lgb.train(
                params,
                train_data,
                valid_sets=[train_data, val_data],
                valid_names=['train', 'eval'],
                num_boost_round=1000,
                callbacks=[
                    lgb.early_stopping(stopping_rounds=50),
                    lgb.log_evaluation(period=0)  # Keine Ausgabe während Training
                ]
            )
            
            # Validierung
            y_pred = self.model.predict(X_val, num_iteration=self.model.best_iteration)
            y_pred_classes = np.argmax(y_pred, axis=1)
            
            accuracy = accuracy_score(y_val, y_pred_classes)
            
            # Cross-Validation
            cv_scores = self._cross_validate(X, y_encoded, cv_folds=5)
            
            # Metriken berechnen
            metrics = {
                'accuracy': accuracy,
                'cv_mean': np.mean(cv_scores),
                'cv_std': np.std(cv_scores),
                'num_samples': len(X),
                'num_features': X.shape[1],
                'num_classes': num_classes,
                'best_iteration': self.model.best_iteration
            }
            
            # Training History aktualisieren
            self.training_history.append({
                'timestamp': pd.Timestamp.now().isoformat(),
                'metrics': metrics,
                'classes': self.label_encoder.classes_.tolist()
            })
            
            self.is_trained = True
            self.save_model()
            
            logger.info(f"Modell trainiert - Accuracy: {accuracy:.3f}, CV: {np.mean(cv_scores):.3f}±{np.std(cv_scores):.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Fehler beim Training: {e}")
            return {'error': str(e)}
    
    def _cross_validate(self, X: np.ndarray, y: np.ndarray, cv_folds: int = 5) -> np.ndarray:
        """Führt Cross-Validation durch"""
        try:
            # Temporäres Modell für CV
            temp_model = lgb.LGBMClassifier(**self.lgb_params, n_estimators=100)
            scores = cross_val_score(temp_model, X, y, cv=cv_folds, scoring='accuracy')
            return scores
        except Exception as e:
            logger.warning(f"Cross-Validation fehlgeschlagen: {e}")
            return np.array([0.0])
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Vorhersage für einzelne Features"""
        if not self.is_trained:
            raise ValueError("Modell ist nicht trainiert")
        
        try:
            # Features zu Array konvertieren
            feature_vector = self._features_to_vector(features)
            feature_array = np.array([feature_vector])
            
            # Vorhersage
            probabilities = self.model.predict(feature_array, num_iteration=self.model.best_iteration)[0]
            
            # Klassen-Wahrscheinlichkeiten
            class_probs = {}
            for i, class_name in enumerate(self.label_encoder.classes_):
                class_probs[class_name] = float(probabilities[i])
            
            # Beste Klasse
            best_class_idx = np.argmax(probabilities)
            best_class = self.label_encoder.classes_[best_class_idx]
            confidence = float(probabilities[best_class_idx])
            
            return {
                'mood': best_class,
                'confidence': confidence,
                'scores': class_probs
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Vorhersage: {e}")
            return {
                'mood': 'unknown',
                'confidence': 0.0,
                'scores': {}
            }
    
    def predict_batch(self, features_list: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Batch-Vorhersage für mehrere Feature-Sets"""
        if not self.is_trained:
            raise ValueError("Modell ist nicht trainiert")
        
        try:
            # Features zu Array konvertieren
            feature_vectors = [self._features_to_vector(features) for features in features_list]
            feature_array = np.array(feature_vectors)
            
            # Batch-Vorhersage
            probabilities = self.model.predict(feature_array, num_iteration=self.model.best_iteration)
            
            results = []
            for i, probs in enumerate(probabilities):
                # Klassen-Wahrscheinlichkeiten
                class_probs = {}
                for j, class_name in enumerate(self.label_encoder.classes_):
                    class_probs[class_name] = float(probs[j])
                
                # Beste Klasse
                best_class_idx = np.argmax(probs)
                best_class = self.label_encoder.classes_[best_class_idx]
                confidence = float(probs[best_class_idx])
                
                results.append({
                    'mood': best_class,
                    'confidence': confidence,
                    'scores': class_probs
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Fehler bei Batch-Vorhersage: {e}")
            return [{'mood': 'unknown', 'confidence': 0.0, 'scores': {}} for _ in features_list]
    
    def _features_to_vector(self, features: Dict[str, float]) -> np.ndarray:
        """Konvertiert Feature-Dict zu Vektor"""
        # Standard-Feature-Reihenfolge
        feature_order = [
            "energy", "valence", "tempo", "danceability",
            "loudness", "spectral_centroid", "mfcc_variance"
        ]
        
        vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0.0)
            vector.append(value)
        
        return np.array(vector)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Gibt Feature-Wichtigkeit zurück"""
        if not self.is_trained:
            return {}
        
        try:
            importance = self.model.feature_importance(importance_type='gain')
            feature_importance = {}
            
            for i, imp in enumerate(importance):
                if i < len(self.feature_names):
                    feature_importance[self.feature_names[i]] = float(imp)
            
            return feature_importance
            
        except Exception as e:
            logger.error(f"Fehler bei Feature-Wichtigkeit: {e}")
            return {}
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Evaluiert das Modell auf Testdaten"""
        if not self.is_trained:
            raise ValueError("Modell ist nicht trainiert")
        
        try:
            # Labels encodieren
            y_test_encoded = self.label_encoder.transform(y_test)
            
            # Vorhersagen
            y_pred_probs = self.model.predict(X_test, num_iteration=self.model.best_iteration)
            y_pred = np.argmax(y_pred_probs, axis=1)
            
            # Metriken
            accuracy = accuracy_score(y_test_encoded, y_pred)
            
            # Classification Report
            class_names = self.label_encoder.classes_
            report = classification_report(y_test_encoded, y_pred, 
                                         target_names=class_names, 
                                         output_dict=True)
            
            # Confusion Matrix
            cm = confusion_matrix(y_test_encoded, y_pred)
            
            return {
                'accuracy': accuracy,
                'classification_report': report,
                'confusion_matrix': cm.tolist(),
                'class_names': class_names.tolist()
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Modell-Evaluation: {e}")
            return {'error': str(e)}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Gibt Informationen über das Modell zurück"""
        if not self.is_trained:
            return {'is_trained': False}
        
        info = {
            'is_trained': True,
            'num_classes': len(self.label_encoder.classes_),
            'classes': self.label_encoder.classes_.tolist(),
            'num_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'best_iteration': getattr(self.model, 'best_iteration', None),
            'training_history': self.training_history,
            'feature_importance': self.get_feature_importance()
        }
        
        return info
    
    def reset(self):
        """Setzt das Modell zurück"""
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.is_trained = False
        self.training_history = []
        
        # Modell-Datei löschen
        if self.model_path.exists():
            try:
                self.model_path.unlink()
                logger.info("Modell-Datei gelöscht")
            except Exception as e:
                logger.warning(f"Fehler beim Löschen der Modell-Datei: {e}")
    
    def update_parameters(self, new_params: Dict[str, Any]):
        """Aktualisiert LightGBM-Parameter"""
        self.lgb_params.update(new_params)
        logger.info(f"Parameter aktualisiert: {new_params}")
    
    def export_training_data_template(self) -> Dict[str, Any]:
        """Exportiert eine Vorlage für Trainingsdaten"""
        template = {
            "training_data": [
                {
                    "features": {
                        "energy": 0.8,
                        "valence": 0.7,
                        "tempo": 0.6,
                        "danceability": 0.9,
                        "loudness": 0.5,
                        "spectral_centroid": 0.6,
                        "mfcc_variance": 0.4
                    },
                    "mood": "euphoric"
                }
            ],
            "available_moods": [
                "euphoric", "driving", "dark", "chill",
                "melancholic", "aggressive", "uplifting", "mysterious"
            ],
            "required_features": [
                "energy", "valence", "tempo", "danceability",
                "loudness", "spectral_centroid", "mfcc_variance"
            ]
        }
        
        return template