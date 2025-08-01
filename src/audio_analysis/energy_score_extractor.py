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
    """Erweiterte EnergyScore-Extraktion mit verbesserter Algorithmus und Performance"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        
        # Erweiterte Gewichtungen für EnergyScore-Berechnung
        self.weights = {
            'rms_loudness': 0.25,
            'spectral_centroid': 0.20,
            'onset_density': 0.20,
            'spectral_rolloff': 0.15,
            'zero_crossing_rate': 0.10,
            'tempo_stability': 0.10
        }
        
        # Adaptive Normalisierungs-Parameter
        self.normalization_params = {
            'rms_loudness': {'min': -60.0, 'max': -5.0, 'adaptive': True},
            'spectral_centroid': {'min': 300.0, 'max': 12000.0, 'adaptive': True},
            'onset_density': {'min': 0.0, 'max': 15.0, 'adaptive': True},
            'spectral_rolloff': {'min': 1000.0, 'max': 15000.0, 'adaptive': True},
            'zero_crossing_rate': {'min': 0.0, 'max': 0.5, 'adaptive': True},
            'tempo_stability': {'min': 0.0, 'max': 1.0, 'adaptive': False}
        }
        
        # Performance-Cache für wiederholte Berechnungen
        self._feature_cache = {}
        self._cache_max_size = 100
    
    def extract_energy_features(self, audio_file: str) -> Dict[str, float]:
        """Extrahiert erweiterte Features für EnergyScore mit Caching"""
        # Prüfe Cache
        cache_key = self._get_cache_key(audio_file)
        if cache_key in self._feature_cache:
            return self._feature_cache[cache_key]
        
        # Extrahiere Features
        if ESSENTIA_AVAILABLE:
            try:
                features = self._extract_features_essentia_enhanced(audio_file)
            except Exception as e:
                print(f"Fehler bei Feature-Extraktion mit Essentia: {e}")
                features = self._extract_features_librosa_enhanced(audio_file)
        else:
            features = self._extract_features_librosa_enhanced(audio_file)
        
        # Cache Management
        self._manage_cache(cache_key, features)
        
        return features
    
    def _get_cache_key(self, audio_file: str) -> str:
        """Generiert Cache-Schlüssel für Audio-Datei"""
        import hashlib
        import os
        
        # Verwende Dateipfad + Modifikationszeit für Cache-Key
        try:
            mtime = os.path.getmtime(audio_file)
            cache_string = f"{audio_file}_{mtime}"
            return hashlib.md5(cache_string.encode()).hexdigest()
        except:
            return hashlib.md5(audio_file.encode()).hexdigest()
    
    def _manage_cache(self, cache_key: str, features: Dict[str, float]):
        """Verwaltet Feature-Cache mit LRU-Strategie"""
        # Entferne älteste Einträge wenn Cache voll
        if len(self._feature_cache) >= self._cache_max_size:
            # Entferne ersten Eintrag (FIFO)
            oldest_key = next(iter(self._feature_cache))
            del self._feature_cache[oldest_key]
        
        self._feature_cache[cache_key] = features
    
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
        
        return {}
    
    def _extract_features_essentia_enhanced(self, audio_file: str) -> Dict[str, float]:
        """Erweiterte Feature-Extraktion mit Essentia"""
        # Lade Audio
        loader = es.MonoLoader(filename=audio_file)
        audio = loader()
        
        if len(audio) == 0:
            raise ValueError(f"Leere Audio-Datei: {audio_file}")
        
        features = {}
        
        # Frame-Parameter
        frame_size = 2048
        hop_size = 1024
        
        # RMS Loudness (in dB)
        rms = es.RMS()
        rms_values = []
        
        # Spectral Features
        spectrum = es.Spectrum()
        spectral_centroid = es.SpectralCentroidTime()
        spectral_rolloff = es.SpectralRollOff()
        
        centroid_values = []
        rolloff_values = []
        
        # Zero Crossing Rate
        zcr = es.ZeroCrossingRate()
        zcr_values = []
        
        # Frame-basierte Analyse
        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            # RMS
            rms_frame = rms(frame)
            if rms_frame > 0:
                rms_values.append(20 * np.log10(rms_frame))
            
            # Spectral Features
            spec = spectrum(frame)
            centroid_values.append(spectral_centroid(spec))
            rolloff_values.append(spectral_rolloff(spec))
            
            # ZCR
            zcr_values.append(zcr(frame))
        
        # Onset Detection
        onset_detection = es.OnsetDetection(method='hfc')
        onsets = es.Onsets()
        onset_times = onsets(audio)
        
        # Tempo Estimation
        rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
        bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)
        
        # Berechne Features
        duration = len(audio) / 44100.0
        
        features['rms_loudness'] = float(np.mean(rms_values)) if rms_values else -60.0
        features['spectral_centroid'] = float(np.mean(centroid_values)) if centroid_values else 1000.0
        features['spectral_rolloff'] = float(np.mean(rolloff_values)) if rolloff_values else 5000.0
        features['zero_crossing_rate'] = float(np.mean(zcr_values)) if zcr_values else 0.1
        features['onset_density'] = len(onset_times) / duration if duration > 0 else 0.0
        
        # Tempo Stability
        if len(beats_intervals) > 1:
            tempo_stability = 1.0 / (np.std(beats_intervals) + 1e-6)
            features['tempo_stability'] = min(1.0, tempo_stability / 10.0)
        else:
            features['tempo_stability'] = 0.0
        
        return features
    
    def _extract_features_librosa_enhanced(self, audio_file: str) -> Dict[str, float]:
        """Erweiterte Feature-Extraktion mit librosa"""
        try:
            if not LIBROSA_AVAILABLE:
                return self._get_default_features()
            
            # Lade Audio
            audio, sr = librosa.load(audio_file, sr=44100)
            
            if len(audio) == 0:
                raise ValueError(f"Leere Audio-Datei: {audio_file}")
            
            features = {}
            
            # RMS Loudness (in dB)
            rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=1024)[0]
            rms_db = 20 * np.log10(rms + 1e-8)
            features['rms_loudness'] = float(np.mean(rms_db))
            
            # Spectral Features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            features['spectral_centroid'] = float(np.mean(spectral_centroid))
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
            
            # Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            features['zero_crossing_rate'] = float(np.mean(zcr))
            
            # Onset Density
            onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='frames')
            duration = len(audio) / sr
            features['onset_density'] = len(onset_frames) / duration if duration > 0 else 0.0
            
            # Tempo und Beat-Tracking für Stability
            try:
                tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
                if len(beats) > 1:
                    beat_times = librosa.frames_to_time(beats, sr=sr)
                    beat_intervals = np.diff(beat_times)
                    tempo_stability = 1.0 / (np.std(beat_intervals) + 1e-6)
                    features['tempo_stability'] = min(1.0, tempo_stability / 10.0)
                else:
                    features['tempo_stability'] = 0.0
            except:
                features['tempo_stability'] = 0.0
            
            return features
            
        except Exception as e:
            print(f"Fehler bei erweiterter Feature-Extraktion für {audio_file}: {e}")
            return self._get_default_features()
    
    def _get_default_features(self) -> Dict[str, float]:
        """Gibt Standard-Features zurück bei Fehlern"""
        return {
            'rms_loudness': -30.0,
            'spectral_centroid': 2000.0,
            'spectral_rolloff': 5000.0,
            'zero_crossing_rate': 0.1,
            'onset_density': 2.0,
            'tempo_stability': 0.5
        }
    
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