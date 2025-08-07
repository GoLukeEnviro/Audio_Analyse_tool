"""Audio Analyzer - Erweiterte Audioanalyse mit Essentia + librosa für Backend"""

import os
import json
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import asyncio

import librosa
import numpy as np
from mutagen import File as MutagenFile
from .cache_manager import CacheManager

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
    """Erweiterte Audio-Analyse-Engine mit Essentia + librosa für headless Backend"""
    
    def __init__(self, cache_dir: str = "data/cache", enable_multiprocessing: bool = True):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache Manager
        self.cache_manager = CacheManager(str(self.cache_dir))
        
        # Multiprocessing-Konfiguration
        self.enable_multiprocessing = enable_multiprocessing
        self.max_workers = min(mp.cpu_count(), 8)
        
        # Erweiterte unterstützte Audioformate
        self.supported_formats = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.aiff', '.aif', '.au',
            '.wma', '.mp4', '.3gp', '.amr', '.opus', '.webm', '.mkv'
        }
        
        # Import-Konfiguration
        self.import_config = {
            'max_file_size_mb': 500,
            'sample_rate': 44100,
            'mono': True,
            'normalize': True,
            'trim_silence': True
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
            self.use_essentia = False
    
    def get_cache_path(self, file_path: str) -> Path:
        """Gibt Cache-Pfad für Datei zurück"""
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.json"
    
    def load_cached_analysis(self, file_path: str) -> Optional[Dict]:
        """Lädt gecachte Analyse-Ergebnisse"""
        cached = self.cache_manager.load_from_cache(file_path)
        if cached:
            self.analysis_stats['cache_hits'] += 1
            return cached
        return None
    
    def save_analysis_cache(self, file_path: str, analysis: Dict):
        """Speichert Analyse-Ergebnisse im Cache"""
        success = self.cache_manager.save_to_cache(file_path, analysis)
        if not success:
            logger.warning(f"Cache konnte nicht gespeichert werden für: {file_path}")
    
    def is_cached(self, file_path: str) -> bool:
        """Prüft ob eine Datei bereits analysiert und gecacht ist"""
        return self.cache_manager.is_cached(file_path)
    
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
            
            major_corr = np.corrcoef(chroma_mean, major_shifted)[0, 1]
            minor_corr = np.corrcoef(chroma_mean, minor_shifted)[0, 1]
            
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
    
    def validate_audio_file(self, file_path: str) -> bool:
        """Validiert Audio-Datei vor der Analyse"""
        try:
            # Prüfe Dateigröße
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.import_config['max_file_size_mb']:
                logger.warning(f"Datei zu groß: {file_size_mb:.1f}MB > {self.import_config['max_file_size_mb']}MB")
                return False
            
            # Prüfe Dateiformat
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.warning(f"Nicht unterstütztes Format: {file_ext}")
                return False
            
            # Prüfe ob Datei lesbar ist
            try:
                y, sr = librosa.load(file_path, sr=None, duration=1.0)
                if len(y) == 0:
                    logger.warning(f"Leere Audio-Datei: {file_path}")
                    return False
            except Exception as e:
                logger.warning(f"Kann Audio-Datei nicht laden: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Datei-Validierung: {e}")
            return False
    
    def _extract_librosa_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert Audio-Features mit librosa"""
        features = {}
        
        try:
            # BPM und Beat-Tracking
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features['bpm'] = float(tempo)
            features['beat_count'] = len(beats)
            
            # Spectral Features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid'] = float(np.mean(spectral_centroids))
            
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
            
            # Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zero_crossing_rate'] = float(np.mean(zcr))
            
            # MFCC Features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_variance'] = float(np.var(mfccs))
            
            # Chroma Features für Harmonie
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            features['chroma_mean'] = float(np.mean(chroma))
            
            # RMS Energy
            rms = librosa.feature.rms(y=y)[0]
            features['energy'] = float(np.mean(rms))
            
            # Loudness (approximiert)
            features['loudness'] = float(librosa.amplitude_to_db(np.mean(rms)))
            
            # Tonart-Features
            chroma_mean = np.mean(chroma, axis=1)
            key_index = np.argmax(chroma_mean)
            features['key_numeric'] = key_index
            features['key_confidence'] = float(chroma_mean[key_index])
            
            # Mode (Dur/Moll) - vereinfachte Heuristik
            major_profile = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1])
            minor_profile = np.array([1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0])
            
            major_corr = np.corrcoef(chroma_mean, major_profile)[0, 1]
            minor_corr = np.corrcoef(chroma_mean, minor_profile)[0, 1]
            
            features['mode'] = 'major' if major_corr > minor_corr else 'minor'
            
            # Valence (vereinfacht)
            features['valence'] = float((major_corr + features['energy']) / 2)
            
            # Danceability (Heuristik)
            beat_strength = len(beats) / (len(y) / sr) / 4.0
            features['danceability'] = min(1.0, beat_strength * features['energy'])
            
        except Exception as e:
            logger.error(f"Fehler bei librosa Feature-Extraktion: {e}")
        
        return features
    
    def _extract_essentia_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert erweiterte Audio-Features mit Essentia"""
        features = {}
        
        if not self.use_essentia:
            return features
        
        try:
            # Convert to Essentia format
            audio_mono = essentia.array(y)
            
            # Rhythm Features
            bpm, beats, beat_confidence, _, estimates = self.rhythm_extractor(audio_mono)
            features['essentia_bpm'] = float(bpm)
            features['beat_confidence'] = float(beat_confidence)
            
            # Onset Rate
            onset_rate = self.onset_rate(audio_mono)
            features['onset_rate'] = float(onset_rate)
            
            # Key Detection
            key, scale, strength = self.key_extractor(audio_mono)
            features['key_essentia'] = key
            features['scale_essentia'] = scale
            features['key_strength'] = float(strength)
            
            # Spectral Analysis
            windowing = essentia.standard.Windowing(type='hann')
            fft = essentia.standard.FFT()
            spectrum = essentia.standard.Spectrum()
            
            # Process frames for spectral analysis
            frame_size = 2048
            hop_size = 1024
            frames = []
            
            for i in range(0, len(audio_mono) - frame_size, hop_size):
                frame = audio_mono[i:i+frame_size]
                windowed_frame = windowing(essentia.array(frame))
                fft_frame = fft(windowed_frame)
                spectrum_frame = spectrum(fft_frame)
                frames.append(spectrum_frame)
            
            if len(frames) > 0:
                # Spectral features
                avg_spectrum = np.mean(frames, axis=0)
                features['spectral_centroid_essentia'] = float(self.spectral_centroid(avg_spectrum))
                features['spectral_rolloff_essentia'] = float(self.spectral_rolloff(avg_spectrum))
                
                # MFCC (Essentia version)
                bands, mfcc_coeffs = self.mfcc(avg_spectrum)
                features['mfcc_essentia_mean'] = float(np.mean(mfcc_coeffs))
            
            # Loudness (professional EBU R128)
            try:
                loudness = self.loudness_ebu128(audio_mono)
                features['loudness_ebu128'] = float(loudness)
            except:
                pass
            
            # Dynamic Complexity
            try:
                dynamic_complexity = self.dynamic_complexity(audio_mono)
                features['dynamic_complexity'] = float(dynamic_complexity)
            except:
                pass
                
            # Danceability (Essentia version)
            try:
                danceability, dfa = self.danceability(audio_mono)
                features['danceability_essentia'] = float(danceability)
                features['dfa'] = float(dfa)
            except:
                pass
            
        except Exception as e:
            logger.error(f"Fehler bei Essentia Feature-Extraktion: {e}")
        
        return features

    def _extract_fass_features(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Extrahiert FASS-spezifische Audio-Features"""
        features = {}
        # TODO: Implement FASS feature extraction logic here
        return features
    
    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrahiert Metadaten aus Audio-Datei"""
        metadata = {}
        
        try:
            # Mutagen für ID3-Tags
            audio_file = MutagenFile(file_path)
            if audio_file is not None:
                metadata.update({
                    'title': str(audio_file.get('TIT2', [''])[0]) if audio_file.get('TIT2') else os.path.splitext(os.path.basename(file_path))[0],
                    'artist': str(audio_file.get('TPE1', [''])[0]) if audio_file.get('TPE1') else 'Unknown',
                    'album': str(audio_file.get('TALB', [''])[0]) if audio_file.get('TALB') else 'Unknown',
                    'genre': str(audio_file.get('TCON', [''])[0]) if audio_file.get('TCON') else 'Unknown',
                    'year': str(audio_file.get('TDRC', [''])[0]) if audio_file.get('TDRC') else None,
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
    
    def analyze_track(self, file_path: str) -> Dict[str, Any]:
        """Analysiert einen Audio-Track komplett"""
        # Check cache first
        cached = self.load_cached_analysis(file_path)
        if cached:
            return cached
        
        result = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'features': {},
            'metadata': {},
            'camelot': {},
            'errors': [],
            'status': 'analyzing',
            'version': '2.0'
        }
        
        try:
            # Validierung
            if not self.validate_audio_file(file_path):
                result['errors'].append(f"Datei-Validierung fehlgeschlagen")
                result['status'] = 'error'
                return result
            
            # Audio laden
            y, sr = librosa.load(file_path, sr=self.import_config['sample_rate'])
            
            if len(y) == 0:
                result['errors'].append("Leere Audio-Datei")
                result['status'] = 'error'
                return result
            
            # Audio preprocessing
            if self.import_config['trim_silence']:
                y, _ = librosa.effects.trim(y, top_db=20)
            
            if self.import_config['normalize']:
                y = librosa.util.normalize(y)
            
            # Features extrahieren
            librosa_features = self._extract_librosa_features(y, sr)
            result['features'].update(librosa_features)
            
            # Erweiterte Essentia-Features (falls verfügbar)
            if self.use_essentia:
                essentia_features = self._extract_essentia_features(y, sr)
                result['features'].update(essentia_features)
                
                # Use better Essentia BPM if available
                if 'essentia_bpm' in essentia_features and essentia_features.get('beat_confidence', 0) > 0.5:
                    result['features']['bpm'] = essentia_features['essentia_bpm']
            
            # Metadaten extrahieren
            metadata = self._extract_metadata(file_path)
            metadata['duration'] = len(y) / sr
            result['metadata'] = metadata
            
            # Fassaden-Analyse (FASS)
            fass_features = self._extract_fass_features(y, sr)
            result['features'].update(fass_features)

            # Camelot Wheel Info
            key, camelot = self.estimate_key(y, sr)
            result['camelot'] = {
                'key': key,
                'camelot': camelot,
                'key_confidence': result['features'].get('key_confidence', 0.0),
                'compatible_keys': self._get_compatible_keys(camelot)
            }
            
            result['status'] = 'completed'
            self.analysis_stats['total_analyzed'] += 1
            
            # Cache speichern
            self.save_analysis_cache(file_path, result)
            
        except Exception as e:
            error_msg = f"Fehler bei der Analyse von {file_path}: {str(e)}"
            result['errors'].append(error_msg)
            result['status'] = 'error'
            logger.error(error_msg)
            self.analysis_stats['errors'] += 1
        
        return result
    
    def _get_compatible_keys(self, camelot: str) -> List[str]:
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
    
    async def analyze_batch_async(self, file_paths: List[str], 
                                 progress_callback: Optional[Callable] = None) -> Dict[str, Dict]:
        """Analysiert mehrere Dateien asynchron"""
        results = {}
        
        if not self.enable_multiprocessing or len(file_paths) < 2:
            # Sequenzielle Verarbeitung
            for i, file_path in enumerate(file_paths):
                try:
                    results[file_path] = self.analyze_track(file_path)
                    if progress_callback:
                        await progress_callback(i + 1, len(file_paths), file_path)
                except Exception as e:
                    logger.error(f"Fehler bei {file_path}: {e}")
                    results[file_path] = {
                        'file_path': file_path,
                        'status': 'error',
                        'errors': [str(e)]
                    }
        else:
            # Parallele Verarbeitung
            loop = asyncio.get_event_loop()
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # Starte alle Tasks
                future_to_file = {
                    loop.run_in_executor(executor, self.analyze_track, file_path): file_path
                    for file_path in file_paths
                }
                
                # Sammle Ergebnisse
                completed = 0
                for future in asyncio.as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = await future
                        results[file_path] = result
                        completed += 1
                        if progress_callback:
                            await progress_callback(completed, len(file_paths), file_path)
                    except Exception as e:
                        logger.error(f"Fehler bei {file_path}: {e}")
                        results[file_path] = {
                            'file_path': file_path,
                            'status': 'error',
                            'errors': [str(e)]
                        }
        
        return results
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Gibt Analyse-Statistiken zurück"""
        return self.analysis_stats.copy()
    
    def clear_cache(self) -> int:
        """Leert den Analyse-Cache"""
        return self.cache_manager.clear_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Cache-Statistiken zurück"""
        return self.cache_manager.get_cache_stats()
    
    def cleanup_cache(self, max_age_days: int = 30, max_size_mb: int = 1000) -> Dict[str, Any]:
        """Bereinigt den Cache"""
        return self.cache_manager.cleanup_cache(max_age_days, max_size_mb)
    
    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Audio-Formate zurück"""
        return list(self.supported_formats)