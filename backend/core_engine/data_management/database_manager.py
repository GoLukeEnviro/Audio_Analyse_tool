"""
DatabaseManager - Ersetzt den CacheManager mit SQLite-basierter Persistierung
"""

import os
import json
import sqlite3
import logging
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def get_conn(db_path: str):
    """Thread-sichere DB-Connection für einzelne Operationen"""
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
    try:
        yield conn
    finally:
        conn.close()


@dataclass
class TrackRecord:
    """Data class for track records"""
    id: int
    file_path: str
    filename: str
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    genre: Optional[str]
    year: Optional[str]
    duration: float
    file_size: int
    extension: str
    created_at: float
    updated_at: float


@dataclass
class GlobalFeaturesRecord:
    """Data class for global features records"""
    id: int
    track_id: int
    bpm: float
    key_name: Optional[str]
    camelot: Optional[str]
    key_confidence: Optional[float]
    energy: float
    valence: float
    danceability: float
    loudness: Optional[float]
    spectral_centroid: Optional[float]
    zero_crossing_rate: Optional[float]
    mfcc_variance: Optional[float]
    primary_mood: Optional[str]
    mood_confidence: Optional[float]
    mood_scores: Optional[str]  # JSON string
    energy_level: Optional[str]
    bpm_category: Optional[str]
    analyzed_at: float


@dataclass
class TimeSeriesRecord:
    """Data class for time series records"""
    id: int
    track_id: int
    timestamp: float
    energy_value: Optional[float]
    brightness_value: Optional[float]
    spectral_rolloff: Optional[float]
    rms_energy: Optional[float]
    created_at: float


class DatabaseManager:
    """
    Professsioneller Datenbank-Manager für Project Phoenix
    Ersetzt das JSON-basierte Caching mit SQLite für bessere Performance und Skalierbarkeit.
    """
    
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # THREADING FIX: Thread-lokale Speicherung für Connections
        self._local = threading.local()
        self._init_database()
        
        logger.info(f"DatabaseManager initialized with database: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-lokale database connection"""
        # Prüfe ob bereits eine Connection für diesen Thread existiert
        if not hasattr(self._local, 'connection') or self._is_connection_broken():
            # Schließe alte Connection falls vorhanden
            if hasattr(self._local, 'connection') and self._local.connection:
                try:
                    self._local.connection.close()
                except:
                    pass
            
            # Erstelle neue thread-lokale Connection
            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                isolation_level='DEFERRED',  # Bessere Concurrency
                check_same_thread=False  # Erlaubt Connection-Sharing innerhalb des Threads
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection.execute("PRAGMA busy_timeout = 30000")  # 30s timeout
            
            logger.debug(f"Created new thread-local DB connection for thread {threading.current_thread().ident}")
            
        return self._local.connection
    
    def _is_connection_broken(self) -> bool:
        """Check if thread-local connection is broken"""
        try:
            if hasattr(self._local, 'connection') and self._local.connection:
                self._local.connection.execute("SELECT 1")
                return False
            return True
        except:
            return True
    
    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tracks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                title TEXT,
                artist TEXT,
                album TEXT,
                genre TEXT,
                year TEXT,
                duration REAL NOT NULL,
                file_size INTEGER NOT NULL,
                extension TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        
        # Global features table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                bpm REAL NOT NULL,
                key_name TEXT,
                camelot TEXT,
                key_confidence REAL,
                energy REAL NOT NULL,
                valence REAL NOT NULL,
                danceability REAL NOT NULL,
                loudness REAL,
                spectral_centroid REAL,
                zero_crossing_rate REAL,
                mfcc_variance REAL,
                primary_mood TEXT,
                mood_confidence REAL,
                mood_scores TEXT,  -- JSON string
                energy_level TEXT,
                bpm_category TEXT,
                analyzed_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
            )
        """)
        
        # Time series features table - NEW for Phase 2
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_series_features (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,  -- Time offset in seconds
                energy_value REAL,
                brightness_value REAL,
                spectral_rolloff REAL,
                rms_energy REAL,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
            )
        """)
        
        # Analysis tasks table (for background job tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_tasks (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                progress REAL DEFAULT 0,
                message TEXT,
                started_at REAL,
                completed_at REAL,
                error_message TEXT,
                total_files INTEGER DEFAULT 0,
                processed_files INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracks_file_path ON tracks(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_features_track_id ON global_features(track_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_features_bpm ON global_features(bpm)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_features_energy ON global_features(energy)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_global_features_mood ON global_features(primary_mood)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_series_track_id ON time_series_features(track_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_series_timestamp ON time_series_features(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_tasks_status ON analysis_tasks(status)")
        
        conn.commit()
        logger.info("Database schema initialized successfully")
    
    def add_track(self, file_path: str, metadata: Dict[str, Any]) -> int:
        """
        Add a new track to the database
        Returns the track ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO tracks (
                    file_path, filename, title, artist, album, genre, year,
                    duration, file_size, extension
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                metadata.get('filename', os.path.basename(file_path)),
                metadata.get('title'),
                metadata.get('artist'),
                metadata.get('album'),
                metadata.get('genre'),
                metadata.get('year'),
                metadata.get('duration', 0.0),
                metadata.get('file_size', 0),
                metadata.get('extension', Path(file_path).suffix.lower())
            ))
            
            track_id = cursor.lastrowid
            conn.commit()
            
            logger.debug(f"Added track to database: {file_path} (ID: {track_id})")
            return track_id
            
        except sqlite3.IntegrityError as e:
            logger.warning(f"Track already exists in database: {file_path}")
            # Get existing track ID
            cursor.execute("SELECT id FROM tracks WHERE file_path = ?", (file_path,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error adding track to database: {e}")
            raise
    
    def get_track_by_path(self, file_path: str) -> Optional[TrackRecord]:
        """Get track by file path"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tracks WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        
        if row:
            return TrackRecord(**dict(row))
        return None
    
    def get_track_by_id(self, track_id: int) -> Optional[TrackRecord]:
        """Get track by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
        row = cursor.fetchone()
        
        if row:
            return TrackRecord(**dict(row))
        return None
    
    def update_global_features(self, track_id: int, features: Dict[str, Any]) -> bool:
        """Update/Insert global features for a track"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Prepare mood_scores as JSON string
            mood_scores_json = None
            if 'mood' in features and 'scores' in features['mood']:
                mood_scores_json = json.dumps(features['mood']['scores'])
            
            # Extract values from nested dictionaries
            mood_data = features.get('mood', {})
            
            # Handle both direct mood data and nested mood analysis
            if 'primary_mood' not in mood_data and isinstance(mood_data, dict):
                # If mood_data is empty, but features has direct mood keys
                if 'primary_mood' in features:
                    mood_data = features
            camelot_data = features.get('camelot', {})
            derived_metrics = features.get('derived_metrics', {})
            
            cursor.execute("""
                INSERT OR REPLACE INTO global_features (
                    track_id, bpm, key_name, camelot, key_confidence,
                    energy, valence, danceability, loudness, spectral_centroid,
                    zero_crossing_rate, mfcc_variance, primary_mood, mood_confidence,
                    mood_scores, energy_level, bpm_category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                track_id,
                features.get('bpm', 0.0),
                camelot_data.get('key'),
                camelot_data.get('camelot'),
                camelot_data.get('key_confidence'),
                features.get('energy', 0.0),
                features.get('valence', 0.0),
                features.get('danceability', 0.0),
                features.get('loudness'),
                features.get('spectral_centroid'),
                features.get('zero_crossing_rate'),
                features.get('mfcc_variance'),
                mood_data.get('primary_mood'),
                mood_data.get('confidence'),
                mood_scores_json,
                derived_metrics.get('energy_level'),
                derived_metrics.get('bpm_category')
            ))
            
            conn.commit()
            logger.debug(f"Updated global features for track ID: {track_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating global features: {e}")
            return False
    
    def add_time_series_data(self, track_id: int, time_series_data: List[Dict[str, Any]]) -> bool:
        """Add time series feature data for a track"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete existing time series data for this track
            cursor.execute("DELETE FROM time_series_features WHERE track_id = ?", (track_id,))
            
            # Insert new time series data
            for data_point in time_series_data:
                cursor.execute("""
                    INSERT INTO time_series_features (
                        track_id, timestamp, energy_value, brightness_value,
                        spectral_rolloff, rms_energy
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    track_id,
                    data_point.get('timestamp', 0.0),
                    data_point.get('energy_value'),
                    data_point.get('brightness_value'),
                    data_point.get('spectral_rolloff'),
                    data_point.get('rms_energy')
                ))
            
            conn.commit()
            logger.debug(f"Added {len(time_series_data)} time series data points for track ID: {track_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding time series data: {e}")
            return False
    
    def get_time_series_data(self, track_id: int) -> List[TimeSeriesRecord]:
        """Get time series data for a track"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM time_series_features 
            WHERE track_id = ? 
            ORDER BY timestamp ASC
        """, (track_id,))
        
        return [TimeSeriesRecord(**dict(row)) for row in cursor.fetchall()]
    
    def is_cached(self, file_path: str) -> bool:
        """Check if track is already analyzed (replaces CacheManager.is_cached)"""
        try:
            with get_conn(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT t.id FROM tracks t
                    JOIN global_features gf ON t.id = gf.track_id
                    WHERE t.file_path = ?
                """, (file_path,))
                
                return cursor.fetchone() is not None
                
        except Exception as e:
            logger.error(f"Error checking cache: {e}")
            return False
    
    def save_to_cache(self, file_path: str, analysis_result: Dict[str, Any]) -> bool:
        """Save analysis results (replaces CacheManager.save_to_cache)"""
        # Use context manager for thread-safe database operations
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
                
                # Add or get track
                try:
                    cursor.execute("""
                        INSERT INTO tracks (
                            file_path, filename, title, artist, album, genre, year,
                            duration, file_size, extension
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        file_path,
                        analysis_result.get('metadata', {}).get('filename', os.path.basename(file_path)),
                        analysis_result.get('metadata', {}).get('title'),
                        analysis_result.get('metadata', {}).get('artist'),
                        analysis_result.get('metadata', {}).get('album'),
                        analysis_result.get('metadata', {}).get('genre'),
                        analysis_result.get('metadata', {}).get('year'),
                        analysis_result.get('metadata', {}).get('duration', 0.0),
                        analysis_result.get('metadata', {}).get('file_size', 0),
                        analysis_result.get('metadata', {}).get('extension', Path(file_path).suffix.lower())
                    ))
                    track_id = cursor.lastrowid
                except sqlite3.IntegrityError:
                    # Track already exists, get ID
                    cursor.execute("SELECT id FROM tracks WHERE file_path = ?", (file_path,))
                    result = cursor.fetchone()
                    track_id = result[0] if result else None
                
                if not track_id:
                    return False
                
                # Update global features
                features = analysis_result.get('features', {})
                mood_data = features.get('mood', {})
                camelot_data = features.get('camelot', {}) or analysis_result.get('camelot', {})
                derived_metrics = features.get('derived_metrics', {}) or analysis_result.get('derived_metrics', {})
                
                mood_scores_json = None
                if 'mood' in features:
                    if isinstance(features['mood'], dict) and 'scores' in features['mood']:
                        mood_scores_json = json.dumps(features['mood']['scores'])
                    elif isinstance(features['mood'], dict):
                        mood_scores_json = json.dumps(features['mood'])
                
                cursor.execute("""
                    INSERT OR REPLACE INTO global_features (
                        track_id, bpm, key_name, camelot, key_confidence,
                        energy, valence, danceability, loudness, spectral_centroid,
                        zero_crossing_rate, mfcc_variance, primary_mood, mood_confidence,
                        mood_scores, energy_level, bpm_category
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    track_id,
                    features.get('bpm', 0.0),
                    camelot_data.get('key'),
                    camelot_data.get('camelot'),
                    camelot_data.get('key_confidence'),
                    features.get('energy', 0.0),
                    features.get('valence', 0.0),
                    features.get('danceability', 0.0),
                    features.get('loudness'),
                    features.get('spectral_centroid'),
                    features.get('zero_crossing_rate'),
                    features.get('mfcc_variance'),
                    mood_data.get('primary_mood') if isinstance(mood_data, dict) else None,
                    mood_data.get('confidence') if isinstance(mood_data, dict) else None,
                    mood_scores_json,
                    derived_metrics.get('energy_level') if isinstance(derived_metrics, dict) else None,
                    derived_metrics.get('bpm_category') if isinstance(derived_metrics, dict) else None
                ))
                
                # Add time series data if present
                if 'time_series_features' in analysis_result:
                    time_series_data = analysis_result['time_series_features']
                    # Delete existing time series data for this track
                    cursor.execute("DELETE FROM time_series_features WHERE track_id = ?", (track_id,))
                    
                    # Insert new time series data
                    for data_point in time_series_data:
                        cursor.execute("""
                            INSERT INTO time_series_features (
                                track_id, timestamp, energy_value, brightness_value,
                                spectral_rolloff, rms_energy
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            track_id,
                            data_point.get('timestamp', 0.0),
                            data_point.get('energy_value'),
                            data_point.get('brightness_value'),
                            data_point.get('spectral_rolloff'),
                            data_point.get('rms_energy')
                        ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            if conn:
                conn.rollback()
            return False
    
    def load_from_cache(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load analysis results (replaces CacheManager.load_from_cache)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            conn.row_factory = sqlite3.Row
            
            # Get track with global features
            cursor.execute("""
                SELECT t.*, gf.*
                FROM tracks t
                JOIN global_features gf ON t.id = gf.track_id
                WHERE t.file_path = ?
            """, (file_path,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Reconstruct analysis result format with robust null handling
            result = {
                'file_path': str(row['file_path']) if row['file_path'] else file_path,
                'filename': str(row['filename']) if row['filename'] else os.path.basename(file_path),
                'features': {
                    'bpm': float(row['bpm']) if row['bpm'] is not None else 0.0,
                    'energy': float(row['energy']) if row['energy'] is not None else 0.0,
                    'valence': float(row['valence']) if row['valence'] is not None else 0.0,
                    'danceability': float(row['danceability']) if row['danceability'] is not None else 0.0,
                    'loudness': float(row['loudness']) if row['loudness'] is not None else 0.0,
                    'spectral_centroid': float(row['spectral_centroid']) if row['spectral_centroid'] is not None else 0.0,
                    'zero_crossing_rate': float(row['zero_crossing_rate']) if row['zero_crossing_rate'] is not None else 0.0,
                    'mfcc_variance': float(row['mfcc_variance']) if row['mfcc_variance'] is not None else 0.0,
                },
                'metadata': {
                    'title': str(row['title']) if row['title'] else '',
                    'artist': str(row['artist']) if row['artist'] else '',
                    'album': str(row['album']) if row['album'] else '',
                    'genre': str(row['genre']) if row['genre'] else '',
                    'year': str(row['year']) if row['year'] else '',
                    'duration': float(row['duration']) if row['duration'] is not None else 0.0,
                    'file_size': int(row['file_size']) if row['file_size'] is not None else 0,
                    'filename': str(row['filename']) if row['filename'] else os.path.basename(file_path),
                    'file_path': str(row['file_path']) if row['file_path'] else file_path,
                    'extension': str(row['extension']) if row['extension'] else '',
                    'analyzed_at': str(row['updated_at']) if row['updated_at'] else str(time.time())
                },
                'camelot': {
                    'key': str(row['key_name']) if row['key_name'] else '',
                    'camelot': str(row['camelot']) if row['camelot'] else '',
                    'key_confidence': float(row['key_confidence']) if row['key_confidence'] is not None else 0.0
                },
                'mood': {
                    'primary_mood': str(row['primary_mood']) if row['primary_mood'] else '',
                    'confidence': float(row['mood_confidence']) if row['mood_confidence'] is not None else 0.0,
                    'scores': json.loads(row['mood_scores']) if row['mood_scores'] else {}
                },
                'derived_metrics': {
                    'energy_level': str(row['energy_level']) if row['energy_level'] else '',
                    'bpm_category': str(row['bpm_category']) if row['bpm_category'] else ''
                },
                'status': 'completed',
                'version': '2.0',
                'errors': []
            }
            
            # Add time series data if requested
            cursor.execute("""
                SELECT timestamp, energy_value, brightness_value, spectral_rolloff, rms_energy
                FROM time_series_features
                WHERE track_id = ?
                ORDER BY timestamp
            """, (row['id'],))
            
            time_series_data = cursor.fetchall()
            if time_series_data:
                result['time_series_features'] = [
                    {
                        'timestamp': ts['timestamp'],
                        'energy_value': ts['energy_value'],
                        'brightness_value': ts['brightness_value'],
                        'spectral_rolloff': ts['spectral_rolloff'],
                        'rms_energy': ts['rms_energy']
                    }
                    for ts in time_series_data
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            return None
    
    def get_all_tracks(self, 
                       limit: int = 100, 
                       offset: int = 0,
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all tracks with optional filtering"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build query
        base_query = """
            SELECT t.*, gf.*
            FROM tracks t
            LEFT JOIN global_features gf ON t.id = gf.track_id
        """
        
        where_clauses = []
        params = []
        
        if filters:
            if 'artist' in filters:
                where_clauses.append("t.artist LIKE ?")
                params.append(f"%{filters['artist']}%")
            
            if 'genre' in filters:
                where_clauses.append("t.genre LIKE ?")
                params.append(f"%{filters['genre']}%")
            
            if 'min_bpm' in filters:
                where_clauses.append("gf.bpm >= ?")
                params.append(filters['min_bpm'])
            
            if 'max_bmp' in filters:
                where_clauses.append("gf.bpm <= ?")
                params.append(filters['max_bpm'])
            
            if 'min_energy' in filters:
                where_clauses.append("gf.energy >= ?")
                params.append(filters['min_energy'])
            
            if 'max_energy' in filters:
                where_clauses.append("gf.energy <= ?")
                params.append(filters['max_energy'])
            
            if 'mood' in filters:
                where_clauses.append("gf.primary_mood = ?")
                params.append(filters['mood'])
        
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        base_query += " ORDER BY t.artist, t.title LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(base_query, params)
        
        tracks = []
        for row in cursor.fetchall():
            if row['id']:  # Only include tracks that have been analyzed
                track_data = {
                    'file_path': row['file_path'],
                    'filename': row['filename'],
                    'title': row['title'],
                    'artist': row['artist'],
                    'duration': row['duration'],
                    'bpm': row['bpm'],
                    'key': row['key_name'],
                    'camelot': row['camelot'],
                    'energy': row['energy'],
                    'mood': row['primary_mood'],
                    'analyzed_at': row['analyzed_at']
                }
                tracks.append(track_data)
        
        return tracks
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get database statistics (replaces CacheManager.get_cache_stats)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Count total tracks
            cursor.execute("SELECT COUNT(*) FROM tracks")
            total_tracks = cursor.fetchone()[0]
            
            # Count analyzed tracks
            cursor.execute("""
                SELECT COUNT(*) FROM tracks t
                JOIN global_features gf ON t.id = gf.track_id
            """)
            analyzed_tracks = cursor.fetchone()[0]
            
            # Get database file size
            db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            # Get oldest and newest analysis
            cursor.execute("SELECT MIN(analyzed_at), MAX(analyzed_at) FROM global_features")
            result = cursor.fetchone()
            oldest_analysis = result[0] if result[0] else time.time()
            newest_analysis = result[1] if result[1] else time.time()
            
            return {
                'total_tracks': total_tracks,
                'analyzed_tracks': analyzed_tracks,
                'total_size_bytes': db_size_bytes,
                'total_size_mb': db_size_mb,
                'database_path': str(self.db_path),
                'created': oldest_analysis,
                'last_cleanup': time.time(),
                'oldest_file': oldest_analysis,
                'newest_file': newest_analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {
                'total_tracks': 0,
                'analyzed_tracks': 0,
                'total_size_bytes': 0,
                'total_size_mb': 0.0,
                'database_path': str(self.db_path),
                'created': time.time(),
                'last_cleanup': time.time(),
                'oldest_file': time.time(),
                'newest_file': time.time()
            }
    
    def clear_cache(self) -> int:
        """Clear all cached data (replaces CacheManager.clear_cache)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get count before clearing
            cursor.execute("SELECT COUNT(*) FROM tracks")
            count = cursor.fetchone()[0]
            
            # Clear all tables (cascading deletes will handle related data)
            cursor.execute("DELETE FROM tracks")
            cursor.execute("DELETE FROM analysis_tasks")
            
            conn.commit()
            
            # Vacuum to reclaim space (must be outside transaction)
            conn.isolation_level = None  # autocommit mode
            cursor.execute("VACUUM")
            conn.isolation_level = ""  # back to transaction mode
            
            logger.info(f"Cleared {count} tracks from database")
            return count
            
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return 0
    
    def cleanup_cache(self, max_age_days: int = 30, max_size_mb: int = 1000) -> Dict[str, Any]:
        """Cleanup old cache entries (replaces CacheManager.cleanup_cache)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            
            # Count entries to be removed
            cursor.execute("""
                SELECT COUNT(*) FROM global_features 
                WHERE analyzed_at < ?
            """, (cutoff_time,))
            old_entries = cursor.fetchone()[0]
            
            if old_entries > 0:
                # Remove old analyzed tracks
                cursor.execute("""
                    DELETE FROM tracks WHERE id IN (
                        SELECT t.id FROM tracks t
                        JOIN global_features gf ON t.id = gf.track_id
                        WHERE gf.analyzed_at < ?
                    )
                """, (cutoff_time,))
                
                conn.commit()
            
            conn.commit()
            
            # Vacuum to reclaim space (must be outside transaction)
            conn.isolation_level = None  # autocommit mode
            cursor.execute("VACUUM")
            conn.isolation_level = ""  # back to transaction mode
            
            # Get size after cleanup
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            
            return {
                'removed_files': old_entries,
                'freed_mb': 0.0,  # Difficult to calculate exactly
                'current_size_mb': db_size_mb
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {'removed_files': 0, 'freed_mb': 0.0}
    
    def close_thread_connection(self):
        """Close thread-local database connection"""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
                self._local.connection = None
                logger.debug(f"Thread-local DB connection closed for thread {threading.current_thread().ident}")
            except Exception as e:
                logger.warning(f"Error closing thread-local connection: {e}")
    
    def close(self):
        """Close database connection (legacy method for compatibility)"""
        self.close_thread_connection()
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.close_thread_connection()
        except:
            pass