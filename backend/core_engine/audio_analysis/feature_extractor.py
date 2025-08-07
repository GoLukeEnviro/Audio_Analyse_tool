"""Feature Extractor - Modulare Audio-Feature-Extraktion"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import librosa
from mutagen import File as MutagenFile
import os
from pathlib import Path

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
        
        # Camelot Wheel mapping
        self.camelot_wheel = {
            'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 'B': '1B',
            'F#': '2B', 'C#': '3B', 'G#': '4B', 'D#': '5B', 'A#': '6B', 'F': '7B',
            'Am': '8A', 'Em': '9A', 'Bm': '10A', 'F#m': '11A', 'C#m': '12A', 'G#m': '1A',
            'D#m': '2A', 'A#m': '3A', 'Fm': '4A', 'Cm': '5A', 'Gm': '6A', 'Dm': '7A'
        }
    
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
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            
            major_corr = np.corrcoef(chroma_mean, major_profile) if len(chroma_mean) == 12 else 0
            minor_corr = np.corrcoef(chroma_mean, minor_profile) if len(chroma_mean) == 12 else 0
            
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
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            features['spectral_centroid'] = float(np.mean(spectral_centroids))
            features['spectral_centroid_variance'] = float(np.var(spectral_centroids))
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)
            features['zero_crossing_rate'] = float(np.mean(zcr))
            
            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            features['spectral_bandwidth'] = float(np.mean(spectral_bandwidth))
            
            # Spectral flatness
            spectral_flatness = librosa.feature.spectral_flatness(y=y)
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
            rms = librosa.feature.rms(y=y)
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
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            major_corr = np.corrcoef(chroma_mean, major_profile) if len(chroma_mean) == 12 else 0.5
            
            # RMS for energy component
            rms = librosa.feature.rms(y=y)
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

    def estimate_key(self, y: np.ndarray, sr: int) -> Tuple[str, str]:
        """Schätzt Tonart mit Krumhansl-Schmuckler Algorithmus"""
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Key templates (Krumhansl-Schmuckler)
        major_template = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_template = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        major_correlations = []
        minor_correlations = []
        
        for i in range(12):
            major_shifted = np.roll(major_template, i)
            minor_shifted = np.roll(minor_template, i)
            
            major_corr = np.corrcoef(chroma_mean, major_shifted)
            minor_corr = np.corrcoef(chroma_mean, minor_shifted)
            
            major_correlations.append(major_corr)
            minor_correlations.append(minor_corr)
        
        max_major_idx = np.argmax(major_correlations)
        max_minor_idx = np.argmax(minor_correlations)
        
        if major_correlations[max_major_idx] > minor_correlations[max_minor_idx]:
            key = key_names[max_major_idx]
        else:
            key = key_names[max_minor_idx] + 'm'
        
        camelot = self.camelot_wheel.get(key, 'Unknown')
        return key, camelot
    
    def estimate_energy(self, y: np.ndarray) -> float:
        """Schätzt Energie des Tracks"""
        rms = librosa.feature.rms(y=y)
        return float(np.mean(rms))
    
    def estimate_brightness(self, y: np.ndarray, sr: int) -> float:
        """Schätzt Helligkeit/Spektrum des Tracks"""
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        return float(np.mean(spectral_centroids))

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrahiert Metadaten aus Audio-Datei"""
        metadata = {}
        
        try:
            # Mutagen für ID3-Tags
            audio_file = MutagenFile(file_path)
            if audio_file is not None:
                metadata.update({
                    'title': str(audio_file.get('TIT2', [''])) if audio_file.get('TIT2') else os.path.splitext(os.path.basename(file_path)),
                    'artist': str(audio_file.get('TPE1', [''])) if audio_file.get('TPE1') else 'Unknown',
                    'album': str(audio_file.get('TALB', [''])) if audio_file.get('TALB') else 'Unknown',
                    'genre': str(audio_file.get('TCON', [''])) if audio_file.get('TCON') else 'Unknown',
                    'year': str(audio_file.get('TDRC', [''])) if audio_file.get('TDRC') else None,
                })
            
            # Datei-Informationen
            file_stats = os.stat(file_path)
            metadata.update({
                'file_size': file_stats.st_size,
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'extension': Path(file_path).suffix.lower(),
                'analyzed_at': file_stats.st_mtime
            })
            
        except Exception as e:
            logger.error(f"Fehler bei Metadaten-Extraktion: {e}")
        
        return metadata
    
    def get_compatible_keys(self, camelot: str) -> List[str]:
        """Gibt harmonisch kompatible Keys zurück"""
        if not camelot or len(camelot) < 2:
            return []
        
        try:
            number = int(camelot[:-1])
            letter = camelot[-1]
        except (ValueError, IndexError):
            return []
        
        compatible = []
        
        # Gleiche Nummer, andere Modalität (relative Dur/Moll)
        if letter == 'A':
            compatible.append(f"{number}B")
        else:
            compatible.append(f"{number}A")
        
        # +1 und -1 (Quintenzirkel)
        next_num = (number % 12) + 1
        prev_num = ((number - 2) % 12) + 1
        
        compatible.extend([f"{next_num}{letter}", f"{prev_num}{letter}"])
        
        return compatible