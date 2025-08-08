"""Audio Analyzer - Erweiterte Audioanalyse mit Essentia + librosa für Backend"""

import os
import json
import logging
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import asyncio

try:
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
    print("[INFO] Essentia-Modul erfolgreich geladen.")
except ImportError:
    ESSENTIA_AVAILABLE = False
    print("[WARNUNG] Essentia-Modul nicht gefunden. Analyse läuft im librosa-Fallback-Modus.")

try:
    import librosa
    LIBROSA_AVAILABLE = True
    print("[INFO] Librosa module loaded successfully.")
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[WARNING] Could not import librosa. Some audio analysis features will be limited.")
    raise ImportError("The librosa package is required for audio analysis. Please install it using 'pip install librosa'")
import numpy as np
from mutagen import File as MutagenFile
from ..data_management.database_manager import DatabaseManager, get_conn
from .feature_extractor import FeatureExtractor
from ..mood_classifier.mood_classifier import MoodClassifier # Neuer Import

logger = logging.getLogger(__name__)

DB_PATH = 'data/database.db'

def db_insert_result(result: dict) -> None:
    """Thread-sichere DB-Insertion für Analyse-Ergebnisse"""
    if result.get('status') != 'success':
        return
    f = result.get('features', {})
    c = result.get('camelot', {})
    try:
        with get_conn(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO tracks (file_path, bpm, musical_key, energy, mood, camelot)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                  bpm=excluded.bpm,
                  musical_key=excluded.musical_key,
                  energy=excluded.energy,
                  mood=excluded.mood,
                  camelot=excluded.camelot,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (
                    result.get('file_path'),
                    f.get('bpm', 0.0),
                    c.get('key', ''),
                    f.get('energy', 0.0),
                    result.get('mood', {}).get('primary_mood', ''),
                    c.get('camelot', '')
                )
            )
            conn.commit()
    except Exception as e:
        logger.error(f"DB insert failed: {e}")


class AudioAnalyzer:
    """Erweiterte Audio-Analyse-Engine mit Essentia + librosa für headless Backend"""
    
    def __init__(self, db_path: str = "data/database.db", enable_multiprocessing: bool = True):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Database Manager (replaces CacheManager)
        self.database_manager = DatabaseManager(str(self.db_path))
        
        # Feature Extractor
        self.feature_extractor = FeatureExtractor(use_essentia=ESSENTIA_AVAILABLE) # Essentia standardmäßig aktivieren
        
        # Mood Classifier
        self.mood_classifier = MoodClassifier() # Instanziierung des MoodClassifiers
        
        # Multiprocessing-Konfiguration
        self.enable_multiprocessing = enable_multiprocessing
        self.max_workers = min(mp.cpu_count() or 1, 8)
        
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
        
        # Analyse-Statistiken
        self.analysis_stats = {
            'total_analyzed': 0,
            'cache_hits': 0,
            'errors': 0,
            'processing_time': 0.0
        }
    
    def load_cached_analysis(self, file_path: str) -> Optional[Dict]:
        """Lädt Analyse-Ergebnisse aus der Datenbank"""
        cached = self.database_manager.load_from_cache(file_path)
        if cached:
            self.analysis_stats['cache_hits'] += 1
            return cached
        return None
    
    def save_analysis_results(self, file_path: str, analysis: Dict):
        """Speichert Analyse-Ergebnisse in der Datenbank"""
        success = self.database_manager.save_to_cache(file_path, analysis)
        if not success:
            logger.warning(f"Analyse-Ergebnisse konnten nicht gespeichert werden für: {file_path}")
    
    def is_cached(self, file_path: str) -> bool:
        """Prüft ob eine Datei bereits analysiert ist"""
        return self.database_manager.is_cached(file_path)
    
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
    
    def analyze_track(self, file_path: str) -> Dict[str, Any]:
        """Analysiert einen Audio-Track komplett - mit ultimativer Fehlerbehandlung"""
        # Check cache first
        cached = self.load_cached_analysis(file_path)
        if cached:
            return cached
        
        # Ultra-safe file validation
        from .feature_extractor import safe_analyze_audio_file, get_fallback_analysis
        
        pre_check = safe_analyze_audio_file(file_path)
        if pre_check and pre_check.get('status') == 'fallback':
            # File validation failed
            logger.warning(f"Pre-check failed for {file_path}, using fallback")
            return pre_check
        
        result = {
            'file_path': file_path,
            'filename': os.path.basename(file_path),
            'features': {},
            'metadata': {},
            'camelot': {},
            'mood': {}, # Hinzugefügt für Mood-Analyse
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
            all_features = self.feature_extractor.extract_all_features(y, sr)
            result['features'].update(all_features)
            
            # NEUE Phase 2 Funktionalität: Zeitreihen-Features extrahieren
            time_series_features = self._extract_time_series_features(y, sr)
            result['time_series_features'] = time_series_features
            
            # Metadaten extrahieren
            metadata = self.feature_extractor.extract_metadata(file_path)
            metadata['duration'] = len(y) / sr
            result['metadata'] = metadata
            
            # Camelot Wheel Info
            key, camelot = self.feature_extractor.estimate_key(y, sr)
            result['camelot'] = {
                'key': key,
                'camelot': camelot,
                'key_confidence': result['features'].get('key_confidence', 0.0),
                'compatible_keys': self.feature_extractor.get_compatible_keys(camelot)
            }
            
            # Mood-Klassifikation
            mood, confidence, scores = self.mood_classifier.classify_mood(result['features'])
            result['mood'] = {
                'primary_mood': mood,
                'confidence': confidence,
                'scores': scores
            }
            
            result['status'] = 'completed'
            self.analysis_stats['total_analyzed'] += 1
            
            # Ergebnisse in Datenbank speichern
            self.save_analysis_results(file_path, result)
            
        except Exception as e:
            error_msg = f"Fehler bei der Analyse von {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.analysis_stats['errors'] += 1
            
            # Return comprehensive fallback instead of broken result
            from .feature_extractor import get_fallback_analysis
            fallback_result = get_fallback_analysis(file_path)
            fallback_result['errors'] = [error_msg]
            fallback_result['status'] = 'error_fallback'
            
            # Still save fallback to avoid reprocessing
            self.save_analysis_results(file_path, fallback_result)
            return fallback_result
        
        return result
    
    def _analyze_track_safe(self, file_path: str) -> Dict[str, Any]:
        """Thread-sichere Track-Analyse ohne SharedDB-Connection"""
        try:
            return self.analyze_track(file_path)
        except Exception as e:
            return {
                'file_path': file_path,
                'status': 'error',
                'errors': [str(e)],
                'features': {},
                'metadata': {},
                'camelot': {},
                'mood': {}
            }
    
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
            # ThreadPool für Thread-sichere DB-Operationen
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self._analyze_track_safe, fp) for fp in file_paths]
                batch_results = []
                
                # Sammle alle Ergebnisse
                for fut in as_completed(futures):
                    batch_results.append(fut.result())
                
                # DB-Schreiben NUR hier im Aufrufer (keine Connection in Threads teilen)  
                for r in batch_results:
                    db_insert_result(r)
                    results[r.get('file_path', 'unknown')] = r
        
        return results
    
    
    def _extract_time_series_features(self, y: np.ndarray, sr: int, 
                                     window_seconds: float = 5.0) -> List[Dict[str, Any]]:
        """
        Extrahiert zeitbasierte Features für grafische Darstellung
        Analysiert alle window_seconds Sekunden Energie, Helligkeit, etc.
        
        Args:
            y: Audio-Signal
            sr: Sample-Rate
            window_seconds: Zeitfenster in Sekunden (Standard: 5 Sekunden)
        
        Returns:
            Liste von Zeitpunkten mit entsprechenden Feature-Werten
        """
        duration = len(y) / sr
        window_samples = int(window_seconds * sr)
        hop_samples = window_samples  # Non-overlapping windows
        
        time_series_data = []
        
        try:
            # Iteriere über das Audio-Signal in Zeitfenstern
            for start_sample in range(0, len(y), hop_samples):
                end_sample = min(start_sample + window_samples, len(y))
                
                if end_sample - start_sample < window_samples // 2:
                    # Skip zu kurze Segmente am Ende
                    break
                
                # Zeitstempel für dieses Segment
                timestamp = start_sample / sr
                
                # Audio-Segment extrahieren
                segment = y[start_sample:end_sample]
                
                if len(segment) == 0:
                    continue
                
                # Features für dieses Zeitfenster berechnen
                time_point_features = {}
                
                # 1. Energie (RMS)
                rms = librosa.feature.rms(y=segment)[0]
                time_point_features['energy_value'] = float(np.mean(rms))
                time_point_features['rms_energy'] = float(np.mean(rms))
                
                # 2. Spektrale Helligkeit (Centroid)
                spectral_centroid = librosa.feature.spectral_centroid(y=segment, sr=sr)[0]
                time_point_features['brightness_value'] = float(np.mean(spectral_centroid))
                
                # 3. Spektrale Rolloff (zusätzliche Information für Klangfarbe)
                spectral_rolloff = librosa.feature.spectral_rolloff(y=segment, sr=sr)[0]
                time_point_features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
                
                # 4. Zeitstempel
                time_point_features['timestamp'] = timestamp
                
                # Optional: Weitere Features für erweiterte Analyse
                try:
                    # Zero Crossing Rate (Indikator für Percussion vs. Tonal)
                    zcr = librosa.feature.zero_crossing_rate(segment)[0]
                    time_point_features['zero_crossing_rate'] = float(np.mean(zcr))
                    
                    # Spectral Bandwidth (Klangbreite)
                    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=segment, sr=sr)[0]
                    time_point_features['spectral_bandwidth'] = float(np.mean(spectral_bandwidth))
                    
                except Exception as e:
                    logger.debug(f"Could not extract additional time series features: {e}")
                
                time_series_data.append(time_point_features)
            
            logger.debug(f"Extracted {len(time_series_data)} time series data points")
            return time_series_data
            
        except Exception as e:
            logger.error(f"Error extracting time series features: {e}")
            return []
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Gibt Analyse-Statistiken zurück"""
        return self.analysis_stats.copy()
    
    def clear_cache(self) -> int:
        """Leert die Analyse-Datenbank"""
        return self.database_manager.clear_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Gibt Datenbank-Statistiken zurück"""
        return self.database_manager.get_cache_stats()
    
    def cleanup_cache(self, max_age_days: int = 30, max_size_mb: int = 1000) -> Dict[str, Any]:
        """Bereinigt die Datenbank"""
        return self.database_manager.cleanup_cache(max_age_days, max_size_mb)
    
    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Audio-Formate zurück"""
        return list(self.supported_formats)