"""Feature Extractor - Modulare Audio-Feature-Extraktion"""

import logging
import numpy as np
from typing import Dict, Any, Optional
import librosa

logger = logging.getLogger(__name__)

# Optionales Essentia-Import
try:
    import essentia
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False


class FeatureExtractor:
    """Modulare Klasse für Audio-Feature-Extraktion"""
    
    def __init__(self, use_essentia: bool = True):
        self.use_essentia = use_essentia and ESSENTIA_AVAILABLE
        
        if self.use_essentia:
            self._init_essentia_algorithms()
            logger.info("FeatureExtractor mit Essentia initialisiert")
        else:
            logger.info("FeatureExtractor nur mit librosa initialisiert")
    
    def _init_essentia_algorithms(self):
        """Initialisiert Essentia-Algorithmen"""
        try:
            # Rhythm-Algorithmen
            self.rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
            self.onset_rate = es.OnsetRate()
            
            # Tonal-Algorithmen
            self.key_extractor = es.KeyExtractor()
            
            # Spectral-Algorithmen
            self.spectral_centroid = es.SpectralCentroid()
            self.spectral_rolloff = es.SpectralRollOff()
            self.mfcc = es.MFCC(numberCoefficients=13)
            
            # Loudness-Algorithmen
            self.loudness_ebu128 = es.LoudnessEBUR128()
            self.dynamic_complexity = es.DynamicComplexity()
            
            # High-Level-Algorithmen
            self.danceability = es.Danceability()
            
        except Exception as e:
            logger.error(f"Fehler bei Essentia-Initialisierung: {e}")
            self.use_essentia = False
    
    def extract_rhythm_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert Rhythmus-Features (BPM, Beat-Tracking)"""
        features = {}
        
        try:
            # Librosa BPM
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features['bpm'] = float(tempo)
            features['beat_count'] = len(beats)
            
            # Beat strength heuristic
            if len(beats) > 0:
                beat_times = librosa.frames_to_time(beats, sr=sr)
                beat_intervals = np.diff(beat_times)
                features['beat_regularity'] = float(1.0 - np.std(beat_intervals) / np.mean(beat_intervals))
            
            # Essentia rhythm features
            if self.use_essentia:
                try:
                    audio_mono = essentia.array(y)
                    bpm_est, beats_est, confidence, _, _ = self.rhythm_extractor(audio_mono)
                    
                    features['essentia_bpm'] = float(bpm_est)
                    features['beat_confidence'] = float(confidence)
                    
                    # Use Essentia BPM if more confident
                    if confidence > 0.7:
                        features['bpm'] = float(bpm_est)
                        
                    # Onset rate
                    onset_rate = self.onset_rate(audio_mono)
                    features['onset_rate'] = float(onset_rate)
                    
                except Exception as e:
                    logger.debug(f"Essentia rhythm extraction failed: {e}")
            
        except Exception as e:
            logger.error(f"Rhythm feature extraction failed: {e}")
        
        return features
    
    def extract_tonal_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert tonale Features (Key, Harmonie, Chroma)"""
        features = {}
        
        try:
            # Chroma features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            features['chroma_mean'] = float(np.mean(chroma))
            features['chroma_variance'] = float(np.var(chroma))
            
            # Key detection (librosa-based)
            key_index = np.argmax(chroma_mean)
            features['key_numeric'] = key_index
            features['key_confidence'] = float(chroma_mean[key_index])
            
            # Mode detection (major/minor)
            major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
            minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])
            
            major_corr = np.corrcoef(chroma_mean, major_profile)[0, 1] if len(chroma_mean) == 12 else 0
            minor_corr = np.corrcoef(chroma_mean, minor_profile)[0, 1] if len(chroma_mean) == 12 else 0
            
            features['mode'] = 'major' if major_corr > minor_corr else 'minor'
            features['mode_confidence'] = float(abs(major_corr - minor_corr))
            
            # Essentia key detection
            if self.use_essentia:
                try:
                    audio_mono = essentia.array(y)
                    key, scale, strength = self.key_extractor(audio_mono)
                    
                    features['key_essentia'] = key
                    features['scale_essentia'] = scale
                    features['key_strength'] = float(strength)
                    
                    # Use Essentia key if more confident
                    if strength > features.get('key_confidence', 0):
                        features['detected_key'] = key
                        features['detected_scale'] = scale
                        
                except Exception as e:
                    logger.debug(f"Essentia key extraction failed: {e}")
            
        except Exception as e:
            logger.error(f"Tonal feature extraction failed: {e}")
        
        return features
    
    def extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert spektrale Features"""
        features = {}
        
        try:
            # Spectral centroid
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid'] = float(np.mean(spectral_centroids))
            features['spectral_centroid_variance'] = float(np.var(spectral_centroids))
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zero_crossing_rate'] = float(np.mean(zcr))
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            features['spectral_bandwidth'] = float(np.mean(spectral_bandwidth))
            
            # Spectral flatness
            spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
            features['spectral_flatness'] = float(np.mean(spectral_flatness))
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_mean'] = float(np.mean(mfccs))
            features['mfcc_variance'] = float(np.var(mfccs))
            
            # Essentia spectral features
            if self.use_essentia:
                try:
                    # Create simple spectrum for Essentia
                    spectrum = np.abs(np.fft.fft(y[:4096]))
                    
                    features['spectral_centroid_essentia'] = float(self.spectral_centroid(spectrum))
                    features['spectral_rolloff_essentia'] = float(self.spectral_rolloff(spectrum))
                    
                    # MFCC (Essentia)
                    bands, mfcc_coeffs = self.mfcc(spectrum)
                    features['mfcc_essentia_mean'] = float(np.mean(mfcc_coeffs))
                    
                except Exception as e:
                    logger.debug(f"Essentia spectral extraction failed: {e}")
            
        except Exception as e:
            logger.error(f"Spectral feature extraction failed: {e}")
        
        return features
    
    def extract_energy_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert Energie- und Loudness-Features"""
        features = {}
        
        try:
            # RMS Energy
            rms = librosa.feature.rms(y=y)[0]
            features['energy'] = float(np.mean(rms))
            features['energy_variance'] = float(np.var(rms))
            
            # Loudness approximation
            features['loudness'] = float(librosa.amplitude_to_db(np.mean(rms)))
            
            # Dynamic range
            features['dynamic_range'] = float(np.max(rms) - np.min(rms))
            
            # Essentia loudness features
            if self.use_essentia:
                try:
                    audio_mono = essentia.array(y)
                    
                    # EBU R128 Loudness
                    loudness = self.loudness_ebu128(audio_mono)
                    features['loudness_ebu128'] = float(loudness)
                    
                    # Dynamic complexity
                    dynamic_complexity = self.dynamic_complexity(audio_mono)
                    features['dynamic_complexity'] = float(dynamic_complexity)
                    
                except Exception as e:
                    logger.debug(f"Essentia energy extraction failed: {e}")
            
        except Exception as e:
            logger.error(f"Energy feature extraction failed: {e}")
        
        return features
    
    def extract_perceptual_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert perzeptuelle Features (Valence, Danceability, etc.)"""
        features = {}
        
        try:
            # Simple valence estimation (based on spectral and tonal features)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Major/minor correlation for valence
            major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
            major_corr = np.corrcoef(chroma_mean, major_profile)[0, 1] if len(chroma_mean) == 12 else 0.5
            
            # RMS for energy component
            rms = librosa.feature.rms(y=y)[0]
            energy = np.mean(rms)
            
            # Combine for valence estimation
            features['valence'] = float(np.clip((major_corr + energy) / 2, 0, 1))
            
            # Simple danceability heuristic
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            beat_strength = len(beats) / (len(y) / sr) / 4.0
            features['danceability'] = float(np.clip(beat_strength * energy, 0, 1))
            
            # Essentia perceptual features
            if self.use_essentia:
                try:
                    audio_mono = essentia.array(y)
                    
                    # Danceability
                    danceability, dfa = self.danceability(audio_mono)
                    features['danceability_essentia'] = float(danceability)
                    features['dfa'] = float(dfa)
                    
                    # Use Essentia danceability if available
                    if not np.isnan(danceability) and danceability > 0:
                        features['danceability'] = float(danceability)
                    
                except Exception as e:
                    logger.debug(f"Essentia perceptual extraction failed: {e}")
            
        except Exception as e:
            logger.error(f"Perceptual feature extraction failed: {e}")
        
        return features
    
    def extract_all_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert alle verfügbaren Features"""
        all_features = {}
        
        # Extract different feature categories
        rhythm_features = self.extract_rhythm_features(y, sr)
        tonal_features = self.extract_tonal_features(y, sr)
        spectral_features = self.extract_spectral_features(y, sr)
        energy_features = self.extract_energy_features(y, sr)
        perceptual_features = self.extract_perceptual_features(y, sr)
        
        # Combine all features
        all_features.update(rhythm_features)
        all_features.update(tonal_features)
        all_features.update(spectral_features)
        all_features.update(energy_features)
        all_features.update(perceptual_features)
        
        return all_features