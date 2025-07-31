"""Audio Analyzer Pro - Erweiterte Audioanalyse mit Essentia + librosa"""

import os
import json
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib

import librosa
import numpy as np
from mutagen import File as MutagenFile
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Optionales Essentia-Import
try:
    import essentia
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    logger.warning("Essentia nicht verfügbar - verwende nur librosa")

class AudioAnalyzer:
    """Erweiterte Audio-Analyse-Engine mit Essentia + librosa"""
    
    def __init__(self, cache_dir: str = "data/cache", enable_multiprocessing: bool = True):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Multiprocessing-Konfiguration
        self.enable_multiprocessing = enable_multiprocessing
        self.max_workers = min(mp.cpu_count(), 8)  # Maximal 8 Prozesse
        
        # Unterstützte Audioformate (erweitert)
        self.supported_formats = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.aiff', '.au'
        }
        
        # Essentia-Algorithmen initialisieren
        self._init_essentia_algorithms()
        
        # Analyse-Statistiken
        self.analysis_stats = {
            'total_analyzed': 0,
            'cache_hits': 0,
            'errors': 0,
            'processing_time': 0.0
        }
        
        # Camelot Wheel mapping
        self.camelot_wheel = {
            'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 'B': '1B',
            'F#': '2B', 'C#': '3B', 'G#': '4B', 'D#': '5B', 'A#': '6B', 'F': '7B',
            'Am': '8A', 'Em': '9A', 'Bm': '10A', 'F#m': '11A', 'C#m': '12A', 'G#m': '1A',
            'D#m': '2A', 'A#m': '3A', 'Fm': '4A', 'Cm': '5A', 'Gm': '6A', 'Dm': '7A'
        }
    
    def _init_essentia_algorithms(self):
        """Initialisiert Essentia-Algorithmen"""
        if not ESSENTIA_AVAILABLE:
            logger.info("Essentia nicht verfügbar - verwende nur librosa")
            self.use_essentia = False
            return
            
        try:
            # Rhythm-Algorithmen
            self.rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
            self.onset_rate = es.OnsetRate()
            
            # Tonal-Algorithmen
            self.key_extractor = es.KeyExtractor()
            self.hpcp = es.HPCP()
            self.spectral_peaks = es.SpectralPeaks()
            
            # Spectral-Algorithmen
            self.spectral_centroid = es.SpectralCentroid()
            self.spectral_rolloff = es.SpectralRollOff()
            self.spectral_flux = es.SpectralFlux()
            self.mfcc = es.MFCC(numberCoefficients=13)
            
            # Loudness-Algorithmen
            self.loudness_ebu128 = es.LoudnessEBUR128()
            self.dynamic_complexity = es.DynamicComplexity()
            
            # High-Level-Algorithmen
            self.danceability = es.Danceability()
            
            logger.info("Essentia-Algorithmen erfolgreich initialisiert")
            self.use_essentia = True
            
        except Exception as e:
            logger.error(f"Fehler bei Essentia-Initialisierung: {e}")
            # Fallback: Nur librosa verwenden
            self.use_essentia = False
    
    def get_cache_path(self, file_path: str) -> Path:
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.json"
    
    def load_cached_analysis(self, file_path: str) -> Optional[Dict]:
        cache_path = self.get_cache_path(file_path)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def save_analysis_cache(self, file_path: str, analysis: Dict):
        cache_path = self.get_cache_path(file_path)
        try:
            with open(cache_path, 'w') as f:
                json.dump(analysis, f, indent=2)
        except IOError:
            pass
    
    def estimate_key(self, y: np.ndarray, sr: int) -> Tuple[str, str]:
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
            
            major_corr = np.corrcoef(chroma_mean, major_shifted)[0, 1]
            minor_corr = np.corrcoef(chroma_mean, minor_shifted)[0, 1]
            
            major_correlations.append(major_corr)
            minor_correlations.append(minor_corr)
        
        max_major_idx = np.argmax(major_correlations)
        max_minor_idx = np.argmax(minor_correlations)
        
        if major_correlations[max_major_idx] > minor_correlations[max_minor_idx]:
            key = key_names[max_major_idx]
            mode = 'major'
        else:
            key = key_names[max_minor_idx] + 'm'
            mode = 'minor'
        
        camelot = self.camelot_wheel.get(key, 'Unknown')
        return key, camelot
    
    def estimate_energy(self, y: np.ndarray) -> float:
        rms = librosa.feature.rms(y=y)
        return float(np.mean(rms))
    
    def estimate_brightness(self, y: np.ndarray, sr: int) -> float:
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        return float(np.mean(spectral_centroids))
    
    def estimate_mood(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        # Simplified mood estimation based on audio features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        
        # Calculate mood indicators
        energy = self.estimate_energy(y)
        brightness = self.estimate_brightness(y, sr)
        
        # Normalize values to 0-1 range
        energy_norm = min(energy * 1000, 1.0)
        brightness_norm = min(brightness / 5000, 1.0)
        zcr_norm = min(np.mean(zero_crossing_rate) * 100, 1.0)
        
        # Mood mapping
        euphoric = (energy_norm + brightness_norm) / 2
        dark = 1 - brightness_norm
        driving = energy_norm * zcr_norm
        experimental = np.std(mfccs) / 50  # High variance indicates experimental
        
        return {
            'euphoric': float(euphoric),
            'dark': float(dark),
            'driving': float(driving),
            'experimental': float(min(experimental, 1.0))
        }
    
    def _extract_librosa_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert Audio-Features mit librosa"""
        features = {}
        
        try:
            # Tempo und Beat-Tracking
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo'] = float(tempo) / 200.0  # Normalisiert auf [0,1]
            features['beat_count'] = len(beats)
            
            # Spectral Features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid'] = float(np.mean(spectral_centroids)) / 8000.0  # Normalisiert
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            features['spectral_rolloff'] = float(np.mean(spectral_rolloff)) / 8000.0
            
            # Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zero_crossing_rate'] = float(np.mean(zcr))
            
            # MFCC Variance (für Timbre-Analyse)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_variance'] = float(np.var(mfccs)) / 100.0  # Normalisiert
            
            # Chroma Features für Harmonie
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            features['chroma_mean'] = float(np.mean(chroma))
            
            # RMS Energy
            rms = librosa.feature.rms(y=y)[0]
            features['energy'] = float(np.mean(rms))  # Bereits [0,1]
            
            # Loudness (approximiert)
            features['loudness'] = float(librosa.amplitude_to_db(np.mean(rms))) / -60.0 + 1.0  # Normalisiert
            
            # Tonart-Erkennung
            chroma_mean = np.mean(chroma, axis=1)
            key_index = np.argmax(chroma_mean)
            features['key'] = key_index / 11.0  # Normalisiert [0,1]
            features['key_confidence'] = float(chroma_mean[key_index])
            
            # Mode (Dur/Moll) - vereinfachte Heuristik
            major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
            minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])
            
            major_corr = np.corrcoef(chroma_mean, major_profile)[0, 1]
            minor_corr = np.corrcoef(chroma_mean, minor_profile)[0, 1]
            
            features['mode'] = 1.0 if major_corr > minor_corr else 0.0
            
            # Valence (Positivität) - Heuristik basierend auf Harmonie und Energie
            features['valence'] = (features['mode'] * 0.6 + features['energy'] * 0.4)
            
            # Danceability (Heuristik)
            beat_strength = len(beats) / (len(y) / sr) / 4.0  # Beats pro Sekunde normalisiert
            features['danceability'] = min(1.0, beat_strength * features['energy'])
            
        except Exception as e:
            logger.error(f"Fehler bei librosa Feature-Extraktion: {e}")
        
        return features
    
    def _extract_essentia_features(self, file_path: str) -> Dict[str, float]:
        """Extrahiert erweiterte Features mit Essentia"""
        features = {}
        
        if not self.use_essentia:
            return features
        
        try:
            # Audio laden für Essentia
            loader = es.MonoLoader(filename=file_path)
            audio = loader()
            
            # Rhythm-Features
            bpm, beats, beats_confidence, _, beats_intervals = self.rhythm_extractor(audio)
            features['essentia_bpm'] = float(bpm) / 200.0  # Normalisiert
            features['beat_confidence'] = float(beats_confidence)
            
            # Onset Rate
            onset_rate = self.onset_rate(audio)
            features['onset_rate'] = float(onset_rate) / 10.0  # Normalisiert
            
            # Key Detection
            key, scale, key_strength = self.key_extractor(audio)
            features['key_strength'] = float(key_strength)
            
            # Spectral Features
            windowing = es.Windowing(type='hann')
            spectrum = es.Spectrum()
            
            # Frame-basierte Analyse
            spectral_centroids = []
            spectral_rolloffs = []
            mfcc_values = []
            
            for frame in es.FrameGenerator(audio, frameSize=1024, hopSize=512):
                windowed_frame = windowing(frame)
                spec = spectrum(windowed_frame)
                
                # Spectral Centroid
                sc = self.spectral_centroid(spec)
                spectral_centroids.append(sc)
                
                # Spectral Rolloff
                sr = self.spectral_rolloff(spec)
                spectral_rolloffs.append(sr)
                
                # MFCC
                mfcc_bands, mfcc_coeffs = self.mfcc(spec)
                mfcc_values.append(mfcc_coeffs)
            
            if spectral_centroids:
                features['essentia_spectral_centroid'] = float(np.mean(spectral_centroids)) / 8000.0
                features['essentia_spectral_rolloff'] = float(np.mean(spectral_rolloffs)) / 8000.0
                features['essentia_mfcc_variance'] = float(np.var(mfcc_values)) / 100.0
            
            # Loudness (EBU R128)
            try:
                loudness = self.loudness_ebu128(audio)
                features['ebu_loudness'] = float(loudness) / -60.0 + 1.0  # Normalisiert
            except:
                pass
            
            # Dynamic Complexity
            try:
                dyn_complexity = self.dynamic_complexity(audio)
                features['dynamic_complexity'] = float(dyn_complexity)
            except:
                pass
            
            # Danceability
            try:
                danceability_value, dfa = self.danceability(audio)
                features['essentia_danceability'] = float(danceability_value)
            except:
                pass
            
        except Exception as e:
            logger.error(f"Fehler bei Essentia Feature-Extraktion: {e}")
        
        return features
    
    def _calculate_camelot_info(self, key_numeric: float, mode: float) -> Dict[str, any]:
        """Berechnet Camelot Wheel Informationen"""
        # Konvertiere normalisierte Werte zurück
        key_index = int(key_numeric * 11)
        is_major = mode > 0.5
        
        # Key Namen
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key_name = key_names[key_index]
        
        if is_major:
            key_full = f"{key_name} Major"
        else:
            key_full = f"{key_name} Minor"
        
        # Camelot Wheel Mapping
        camelot_major = ['8B', '3B', '10B', '5B', '12B', '7B', '2B', '9B', '4B', '11B', '6B', '1B']
        camelot_minor = ['5A', '12A', '7A', '2A', '9A', '4A', '11A', '6A', '1A', '8A', '3A', '10A']
        
        if is_major:
            camelot = camelot_major[key_index]
        else:
            camelot = camelot_minor[key_index]
        
        # Harmonisch kompatible Keys
        compatible_keys = self._get_compatible_keys(camelot)
        
        return {
            'key': key_full,
            'camelot': camelot,
            'key_numeric': key_numeric,
            'mode': 'Major' if is_major else 'Minor',
            'compatible_keys': compatible_keys,
            'key_confidence': 0.8  # Placeholder
        }
    
    def _get_compatible_keys(self, camelot: str) -> List[str]:
        """Gibt harmonisch kompatible Keys zurück"""
        if not camelot or len(camelot) < 2:
            return []
        
        number = int(camelot[:-1])
        letter = camelot[-1]
        
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
 
    def analyze_track(self, file_path: str, progress_callback=None) -> Dict:
        """Analysiert einen Audio-Track mit erweiterter Feature-Extraktion"""
        # Check cache first
        cached = self.load_cached_analysis(file_path)
        if cached:
            return cached
        
        result = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'features': {},
            'metadata': {},
            'mood': {},
            'camelot': {},
            'errors': [],
            'version': '2.0'  # Pro-Version
        }
        
        try:
            if progress_callback:
                progress_callback(f"Loading {os.path.basename(file_path)}...")
            
            # Load audio file
            y, sr = librosa.load(file_path, duration=120)  # Analyze first 2 minutes
            
            if progress_callback:
                progress_callback("Extrahiere librosa Features...")
            
            # Librosa Features extrahieren
            librosa_features = self._extract_librosa_features(y, sr)
            result['features'].update(librosa_features)
            
            if progress_callback:
                progress_callback("Extrahiere Essentia Features...")
            
            # Essentia Features extrahieren (falls verfügbar)
            essentia_features = self._extract_essentia_features(file_path)
            result['features'].update(essentia_features)
            
            if progress_callback:
                progress_callback("Analysiere Stimmung...")
            
            # Mood Classification
            mood = self.estimate_mood(y, sr)
            result['mood'] = {
                'primary_mood': 'unknown',
                'confidence': 0.0,
                'secondary_moods': [],
                'explanation': '',
                'energy_level': result['features'].get('energy', 0.0),
                'valence': result['features'].get('valence', 0.5),
                'danceability': result['features'].get('danceability', 0.0),
                'mood_details': mood
            }
            
            if progress_callback:
                progress_callback("Berechne Camelot Wheel...")
            
            # Camelot Wheel Informationen
            key, camelot = self.estimate_key(y, sr)
            result['camelot'] = {
                'key': key,
                'camelot': camelot,
                'key_confidence': result['features'].get('key_confidence', 0.0)
            }
            
            if progress_callback:
                progress_callback("Extrahiere Metadaten...")
            
            # File metadata
            file_stats = os.stat(file_path)
            result['metadata'] = {
                'file_size': file_stats.st_size,
                'duration': len(y) / sr,
                'bpm': float(librosa.beat.beat_track(y=y, sr=sr)[0]),
                'analyzed_at': file_stats.st_mtime
            }
            
            # Cache the results
            self.save_analysis_cache(file_path, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Fehler bei der Analyse von {file_path}: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(error_msg)
            return result
    
    def analyze_directory(self, directory: str, progress_callback=None) -> list:
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac'}
        results = []
        
        audio_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in audio_extensions:
                    audio_files.append(os.path.join(root, file))
        
        total_files = len(audio_files)
        
        for i, file_path in enumerate(audio_files):
            if progress_callback:
                progress_callback(f"Processing {i+1}/{total_files}: {os.path.basename(file_path)}")
            
            result = self.analyze_track(file_path)
            results.append(result)
        
        return results