"""EnergyScore Extractor - Berechnet gewichteten Energy-Score aus Audio-Features"""

import numpy as np
from typing import Dict, Any, Optional
from .feature_extractor import FeatureExtractor

# Versuche Essentia zu importieren, falls verfügbar
try:
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    print("Essentia nicht verfügbar - verwende nur librosa")

# Fallback zu librosa wenn Essentia nicht verfügbar
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


class EnergyScoreExtractor:
    """Extrahiert EnergyScore (1-10) basierend auf RMS-Loudness, Spectral Centroid, Onset-Density"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        
        # Gewichtungen für EnergyScore-Berechnung
        self.weights = {
            'rms_loudness': 0.4,
            'spectral_centroid': 0.3,
            'onset_density': 0.3
        }
        
        # Normalisierungs-Parameter (werden aus Trainingsdata bestimmt)
        self.normalization_params = {
            'rms_loudness': {'min': -60.0, 'max': -10.0},  # dB
            'spectral_centroid': {'min': 500.0, 'max': 8000.0},  # Hz
            'onset_density': {'min': 0.0, 'max': 10.0}  # onsets/sec
        }
    
    def extract_energy_features(self, audio_file: str) -> Dict[str, float]:
        """Extrahiert die drei Kern-Features für EnergyScore"""
        if ESSENTIA_AVAILABLE:
            try:
                return self._extract_features_essentia(audio_file)
            except Exception as e:
                print(f"Fehler bei Feature-Extraktion mit Essentia: {e}")
                # Fallback zu librosa
                return self._extract_features_librosa(audio_file)
        else:
            return self._extract_features_librosa(audio_file)
    
    def _extract_features_essentia(self, audio_file: str) -> Dict[str, float]:
        """Extrahiert Features mit Essentia"""
        # Lade Audio
        loader = es.MonoLoader(filename=audio_file)
        audio = loader()
        
        if len(audio) == 0:
            raise ValueError(f"Leere Audio-Datei: {audio_file}")
        
        # RMS Loudness (in dB)
        rms = es.RMS()
        rms_values = []
        
        # Frame-basierte Analyse
        frame_size = 2048
        hop_size = 1024
        
        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            rms_frame = rms(frame)
            if rms_frame > 0:
                rms_values.append(20 * np.log10(rms_frame))
        
        rms_loudness = np.mean(rms_values) if rms_values else -60.0
        
        # Spectral Centroid
        spectrum = es.Spectrum()
        spectral_centroid = es.SpectralCentroidTime()
        centroid_values = []
        
        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            spec = spectrum(frame)
            centroid = spectral_centroid(spec)
            centroid_values.append(centroid)
        
        avg_spectral_centroid = np.mean(centroid_values) if centroid_values else 1000.0
        
        # Onset Density
        onset_detection = es.OnsetDetection(method='hfc')
        onsets = es.Onsets()
        
        onset_times = onsets(audio)
        duration = len(audio) / 44100.0  # Annahme: 44.1kHz
        onset_density = len(onset_times) / duration if duration > 0 else 0.0
        
        return {
            'rms_loudness': float(rms_loudness),
            'spectral_centroid': float(avg_spectral_centroid),
            'onset_density': float(onset_density)
        }
    
    def _extract_features_librosa(self, audio_file: str) -> Dict[str, float]:
        """Extrahiert Features mit librosa als Fallback"""
        try:
            if not LIBROSA_AVAILABLE:
                print("Weder Essentia noch librosa verfügbar - verwende Standardwerte")
                return {
                    'rms_loudness': -30.0,
                    'spectral_centroid': 2000.0,
                    'onset_density': 2.0
                }
            
            # Lade Audio mit librosa
            audio, sr = librosa.load(audio_file, sr=44100)
            
            if len(audio) == 0:
                raise ValueError(f"Leere Audio-Datei: {audio_file}")
            
            # RMS Loudness (in dB)
            rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=1024)[0]
            rms_db = 20 * np.log10(rms + 1e-8)  # Vermeide log(0)
            rms_loudness = np.mean(rms_db)
            
            # Spectral Centroid
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            avg_spectral_centroid = np.mean(spectral_centroid)
            
            # Onset Density
            onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='frames')
            duration = len(audio) / sr
            onset_density = len(onset_frames) / duration if duration > 0 else 0.0
            
            return {
                'rms_loudness': float(rms_loudness),
                'spectral_centroid': float(avg_spectral_centroid),
                'onset_density': float(onset_density)
            }
            
        except Exception as e:
            print(f"Fehler bei Feature-Extraktion mit librosa für {audio_file}: {e}")
            return {
                'rms_loudness': -30.0,
                'spectral_centroid': 2000.0,
                'onset_density': 2.0
            }
    
    def normalize_feature(self, value: float, feature_name: str) -> float:
        """Normalisiert Feature-Wert auf 0-1 Bereich"""
        params = self.normalization_params.get(feature_name, {'min': 0, 'max': 1})
        min_val = params['min']
        max_val = params['max']
        
        # Clamp und normalisiere
        clamped = max(min_val, min(max_val, value))
        normalized = (clamped - min_val) / (max_val - min_val)
        
        return normalized
    
    def calculate_energy_score(self, features: Dict[str, float]) -> float:
        """Berechnet gewichteten EnergyScore (1-10)"""
        # Normalisiere Features
        normalized_features = {}
        for feature_name, value in features.items():
            if feature_name in self.weights:
                normalized_features[feature_name] = self.normalize_feature(value, feature_name)
        
        # Gewichtete Summe
        energy_score = 0.0
        for feature_name, weight in self.weights.items():
            if feature_name in normalized_features:
                energy_score += weight * normalized_features[feature_name]
        
        # Skaliere auf 1-10
        energy_score = (energy_score * 9) + 1
        
        # Clamp auf gültigen Bereich
        return max(1.0, min(10.0, energy_score))
    
    def extract_energy_score(self, audio_file: str) -> Dict[str, Any]:
        """Hauptmethode: Extrahiert EnergyScore und alle relevanten Features"""
        # Extrahiere Energy-Features
        energy_features = self.extract_energy_features(audio_file)
        
        # Berechne EnergyScore
        energy_score = self.calculate_energy_score(energy_features)
        
        return {
            'energy_score': round(energy_score, 2),
            'rms_loudness': energy_features['rms_loudness'],
            'spectral_centroid': energy_features['spectral_centroid'],
            'onset_density': energy_features['onset_density']
        }
    
    def update_normalization_params(self, training_data: Dict[str, Dict[str, float]]):
        """Aktualisiert Normalisierungs-Parameter basierend auf Trainingsdata"""
        for feature_name in self.weights.keys():
            if feature_name in training_data:
                values = list(training_data[feature_name].values())
                if values:
                    # Verwende 5. und 95. Perzentil für robuste Normalisierung
                    min_val = np.percentile(values, 5)
                    max_val = np.percentile(values, 95)
                    
                    self.normalization_params[feature_name] = {
                        'min': float(min_val),
                        'max': float(max_val)
                    }
    
    def batch_extract_energy_scores(self, audio_files: list) -> Dict[str, Dict[str, Any]]:
        """Batch-Extraktion für mehrere Audio-Dateien"""
        results = {}
        
        for audio_file in audio_files:
            try:
                results[audio_file] = self.extract_energy_score(audio_file)
            except Exception as e:
                print(f"Fehler bei {audio_file}: {e}")
                results[audio_file] = {
                    'energy_score': 5.0,
                    'rms_loudness': -30.0,
                    'spectral_centroid': 2000.0,
                    'onset_density': 2.0
                }
        
        return results