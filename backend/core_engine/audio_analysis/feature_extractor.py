"""Feature Extractor - Modulare Audio-Feature-Extraktion"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import librosa
from mutagen import File as MutagenFile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def get_safe_defaults() -> Dict[str, Any]:
    """Sichere Default-Werte für Feature-Extraktion"""
    return {
        'bpm': 120.0,
        'key': 'Unknown',
        'camelot': '1A',
        'key_confidence': 0.0,
        'energy': 0.5,
        'valence': 0.5,
        'danceability': 0.5,
        'acousticness': 0.5,
        'instrumentalness': 0.5,
        'loudness': -20.0,
        'spectral_centroid': 2000.0,
        'zero_crossing_rate': 0.1,
        'mfcc_variance': 0.5,
        'tempo_confidence': 0.0,
        'rhythm_strength': 0.5
    }

def get_fallback_analysis(file_path: str = "unknown") -> Dict[str, Any]:
    """Vollständige Fallback-Analyse für fehlgeschlagene Dateien"""
    import time
    return {
        'file_path': file_path,
        'filename': os.path.basename(file_path) if file_path != "unknown" else "unknown",
        'features': get_safe_defaults(),
        'metadata': {
            'title': 'Unknown',
            'artist': 'Unknown Artist',
            'album': 'Unknown',
            'duration': 180.0,
            'file_size': 0,
            'format': 'unknown',
            'analyzed_at': time.time()
        },
        'camelot': {
            'key': 'Unknown',
            'camelot': '1A',
            'key_confidence': 0.0,
            'compatible_keys': ['1A', '12A', '2A']
        },
        'mood': {
            'primary_mood': 'neutral',
            'confidence': 0.0,
            'scores': {
                'energetic': 0.0,
                'happy': 0.0,
                'calm': 0.0,
                'melancholic': 0.0,
                'aggressive': 0.0,
                'neutral': 1.0
            }
        },
        'derived_metrics': {
            'energy_level': 'medium',
            'bpm_category': 'medium',
            'estimated_mood': 'neutral',
            'danceability_level': 'medium'
        },
        'status': 'fallback',
        'errors': ['Analysis failed - using fallback values'],
        'version': '2.0'
    }

def safe_analyze_audio_file(file_path: str) -> Dict[str, Any]:
    """Ultimativ sichere Audio-Analyse mit Fallback"""
    import time
    
    # File validation
    if not Path(file_path).is_file():
        logger.error(f"File not found: {file_path}")
        return get_fallback_analysis(file_path)
    
    # Size check
    try:
        file_size = os.path.getsize(file_path)
        if file_size < 1024:  # Less than 1KB
            logger.error(f"File too small: {file_path} ({file_size} bytes)")
            return get_fallback_analysis(file_path)
    except OSError as e:
        logger.error(f"Cannot access file {file_path}: {e}")
        return get_fallback_analysis(file_path)
    
    # Try full analysis
    try:
        # This will be implemented by AudioAnalyzer.analyze_track()
        logger.debug(f"Starting safe analysis for: {file_path}")
        return None  # Placeholder - will be replaced by caller
    except Exception as e:
        logger.error(f"Safe analysis failed for {file_path}: {e}")
        return get_fallback_analysis(file_path)

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
        """Extrahiert tonale Features (Key, Harmonie, Chroma) mit robustem Array-Handling"""
        features = {}
        
        try:
            # ROBUST CHROMA FEATURES mit Array-Safety
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Sichere Array-Validierung und Aggregation
            if chroma.size == 0:
                logger.warning("Empty chroma array, using fallback values")
                chroma_mean = np.zeros(12)
                features['chroma_mean'] = 0.0
                features['chroma_variance'] = 0.0
            else:
                chroma_mean = np.mean(chroma, axis=1) if chroma.ndim > 1 else chroma
                
                # Sicherstellen, dass chroma_mean 12 Elemente hat, sonst mit Nullen auffüllen
                if chroma_mean.shape[0] != 12:
                    logger.warning(f"Chroma_mean hat {chroma_mean.shape[0]} Elemente, erwartet 12. Fülle mit Nullen auf.")
                    chroma_mean = np.pad(chroma_mean, (0, 12 - chroma_mean.shape[0]), 'constant')
                
                features['chroma_mean'] = float(np.mean(chroma))
                features['chroma_variance'] = float(np.var(chroma))
            
            # Key detection (librosa-based)
            key_index = np.argmax(chroma_mean)
            features['key_numeric'] = key_index
            features['key_confidence'] = float(chroma_mean[key_index])
            
            # Mode detection (major/minor)
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            
            # FIX: corrcoef returns 2D matrix, need [0,1] element
            # Sicherstellen, dass chroma_mean 12 Elemente hat, sonst Korrelation auf 0 setzen
            if chroma_mean.shape[0] == 12:
                major_corr = np.corrcoef(chroma_mean, major_profile)[0, 1]
                minor_corr = np.corrcoef(chroma_mean, minor_profile)[0, 1]
            else:
                major_corr = 0.0
                minor_corr = 0.0
            
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
            # ROBUST SPECTRAL CENTROID mit Array-Safety
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            if spectral_centroids.size > 0:
                features['spectral_centroid'] = float(np.mean(spectral_centroids))
                features['spectral_centroid_variance'] = float(np.var(spectral_centroids))
            else:
                features['spectral_centroid'] = float(sr / 4)  # Fallback: quarter of Nyquist
                features['spectral_centroid_variance'] = 0.0
            
            # ROBUST SPECTRAL ROLLOFF 
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            if spectral_rolloff.size > 0:
                features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
            else:
                features['spectral_rolloff'] = float(sr / 2)  # Fallback: Nyquist frequency
            
            # ROBUST ZERO CROSSING RATE
            zcr = librosa.feature.zero_crossing_rate(y)
            if zcr.size > 0:
                features['zero_crossing_rate'] = float(np.mean(zcr))
            else:
                features['zero_crossing_rate'] = 0.0
            
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
            # ROBUST RMS ENERGY mit Array-Safety  
            rms = librosa.feature.rms(y=y)
            
            if rms.size == 0:
                logger.warning("Empty RMS array, using fallback energy values")
                features['energy'] = 0.0
                features['energy_variance'] = 0.0
                features['loudness'] = -60.0  # Silent fallback
                features['dynamic_range'] = 0.0
            else:
                # Sichere Skalar-Konvertierung
                features['energy'] = float(np.mean(rms))
                features['energy_variance'] = float(np.var(rms))
                
                # Loudness mit Array-Validierung
                rms_mean = np.mean(rms)
                if rms_mean > 0:
                    features['loudness'] = float(librosa.amplitude_to_db(rms_mean))
                else:
                    features['loudness'] = -60.0  # Silent fallback
                
                # Dynamic range mit Min/Max-Safety
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
            # FIX: corrcoef returns 2D matrix, need [0,1] element  
            major_corr = np.corrcoef(chroma_mean, major_profile)[0, 1] if len(chroma_mean) == 12 else 0.5
            
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
        """Extrahiert alle verfügbaren Features mit Fehlerbehandlung"""
        all_features = get_safe_defaults()
        
        try:
            # Extract different feature categories with individual error handling
            try:
                rhythm_features = self.extract_rhythm_features(y, sr)
                all_features.update(rhythm_features)
                logger.debug("Rhythm features extracted successfully")
            except Exception as e:
                logger.warning(f"Rhythm feature extraction failed: {e}")
            
            try:
                tonal_features = self.extract_tonal_features(y, sr)
                all_features.update(tonal_features)
                logger.debug("Tonal features extracted successfully")
            except Exception as e:
                logger.warning(f"Tonal feature extraction failed: {e}")
            
            try:
                spectral_features = self.extract_spectral_features(y, sr)
                all_features.update(spectral_features)
                logger.debug("Spectral features extracted successfully")
            except Exception as e:
                logger.warning(f"Spectral feature extraction failed: {e}")
            
            try:
                energy_features = self.extract_energy_features(y, sr)
                all_features.update(energy_features)
                logger.debug("Energy features extracted successfully")
            except Exception as e:
                logger.warning(f"Energy feature extraction failed: {e}")
            
            try:
                perceptual_features = self.extract_perceptual_features(y, sr)
                all_features.update(perceptual_features)
                logger.debug("Perceptual features extracted successfully")
            except Exception as e:
                logger.warning(f"Perceptual feature extraction failed: {e}")
                
        except Exception as e:
            logger.error(f"Critical error in feature extraction: {e}")
            # Return safe defaults if everything fails
            
        return all_features

    def estimate_key(self, y: np.ndarray, sr: int) -> Tuple[str, str]:
        """Schätzt Tonart mit Krumhansl-Schmuckler Algorithmus - robust gegen Fehler"""
        try:
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1) if chroma.ndim > 1 else chroma
        except Exception as e:
            logger.warning(f"Key estimation failed: {e}")
            return 'Unknown', '1A'
        
        # Sicherstellen, dass chroma_mean 12 Elemente hat, sonst mit Nullen auffüllen
        if chroma_mean.shape[0] != 12:
            logger.warning(f"Chroma_mean in estimate_key hat {chroma_mean.shape[0]} Elemente, erwartet 12. Fülle mit Nullen auf.")
            chroma_mean = np.pad(chroma_mean, (0, 12 - chroma_mean.shape[0]), 'constant')
        
        # Key templates (Krumhansl-Schmuckler)
        major_template = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_template = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        major_correlations = []
        minor_correlations = []
        
        for i in range(12):
            major_shifted = np.roll(major_template, i)
            minor_shifted = np.roll(minor_template, i)
            
            # FIX: corrcoef returns 2D matrix, extract scalar correlation
            # Sicherstellen, dass chroma_mean und shifted_template nicht leer sind
            if chroma_mean.size == 0 or major_shifted.size == 0:
                major_corr = 0.0
            else:
                major_corr = np.corrcoef(chroma_mean, major_shifted)[0, 1]
            
            if chroma_mean.size == 0 or minor_shifted.size == 0:
                minor_corr = 0.0
            else:
                minor_corr = np.corrcoef(chroma_mean, minor_shifted)[0, 1]
            
            major_correlations.append(major_corr)
            minor_correlations.append(minor_corr)
        
        max_major_idx = np.argmax(major_correlations)
        max_minor_idx = np.argmax(minor_correlations)
        
        # NaN-Werte in 0 umwandeln, um Vergleich zu ermöglichen
        major_max_corr = np.nan_to_num(major_correlations[max_major_idx])
        minor_max_corr = np.nan_to_num(minor_correlations[max_minor_idx])

        if major_max_corr > minor_max_corr:
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