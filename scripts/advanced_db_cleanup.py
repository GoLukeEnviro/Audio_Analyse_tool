#!/usr/bin/env python3
"""
Advanced Database Cleanup Script - Erweiterte Bereinigung und Konsistenz-Checks
"""

import sqlite3
import logging
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core_engine.data_management.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedDatabaseCleaner:
    """Erweiterte Datenbank-Bereinigung mit Konsistenz-Checks"""
    
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = Path(db_path)
        self.backup_path = f"{db_path}.advanced_backup_{int(time.time())}"
        self.stats = {
            'cleaned_records': 0,
            'fixed_nulls': 0,
            'removed_orphans': 0,
            'normalized_values': 0
        }
    
    def create_backup(self) -> bool:
        """Erstelle erweiterte Backup"""
        try:
            if self.db_path.exists():
                import shutil
                shutil.copy2(self.db_path, self.backup_path)
                logger.info(f"Advanced backup created: {self.backup_path}")
                return True
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
        return True
    
    def advanced_cleanup(self) -> Dict[str, Any]:
        """Führe erweiterte Bereinigung durch"""
        
        if not self.create_backup():
            return {'success': False, 'error': 'Backup failed'}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.info("=== Phase 1: Advanced NULL cleanup ===")
            self._fix_advanced_nulls(cursor)
            
            logger.info("=== Phase 2: Data normalization ===")
            self._normalize_data_ranges(cursor)
            
            logger.info("=== Phase 3: Orphan removal ===")
            self._remove_orphaned_records(cursor)
            
            logger.info("=== Phase 4: Consistency enforcement ===")
            self._enforce_consistency(cursor)
            
            logger.info("=== Phase 5: Performance optimization ===")
            self._optimize_performance(cursor, conn)
            
            conn.commit()
            
            logger.info("=== Phase 6: Integrity verification ===")
            integrity_results = self._verify_integrity(cursor)
            
            conn.close()
            
            return {
                'success': True,
                'stats': self.stats,
                'integrity': integrity_results,
                'backup': self.backup_path
            }
            
        except Exception as e:
            logger.error(f"Advanced cleanup failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _fix_advanced_nulls(self, cursor: sqlite3.Cursor):
        """Erweiterte NULL-Werte Bereinigung"""
        
        # Fix tracks table with advanced patterns
        null_fixes = [
            ("UPDATE tracks SET title = filename WHERE title IS NULL OR title = '' OR title = 'None'", "track titles"),
            ("UPDATE tracks SET artist = 'Unknown Artist' WHERE artist IS NULL OR artist = '' OR artist = 'None'", "track artists"),
            ("UPDATE tracks SET album = 'Unknown Album' WHERE album IS NULL OR album = '' OR album = 'None'", "track albums"),
            ("UPDATE tracks SET genre = 'Unknown' WHERE genre IS NULL OR genre = '' OR genre = 'None'", "track genres"),
            ("UPDATE tracks SET year = '0' WHERE year IS NULL OR year = '' OR year = 'None'", "track years"),
        ]
        
        for query, description in null_fixes:
            cursor.execute(query)
            affected = cursor.rowcount
            if affected > 0:
                logger.info(f"Fixed {affected} {description}")
                self.stats['fixed_nulls'] += affected
        
        # Fix global_features with comprehensive patterns
        features_fixes = [
            ("UPDATE global_features SET key_name = 'Unknown' WHERE key_name IS NULL OR key_name = '' OR key_name = 'None'", "key names"),
            ("UPDATE global_features SET camelot = '1A' WHERE camelot IS NULL OR camelot = '' OR camelot = 'None' OR LENGTH(camelot) < 2", "camelot values"),
            ("UPDATE global_features SET key_confidence = 0.0 WHERE key_confidence IS NULL OR key_confidence < 0 OR key_confidence > 1", "key confidence"),
            ("UPDATE global_features SET primary_mood = 'neutral' WHERE primary_mood IS NULL OR primary_mood = '' OR primary_mood = 'None'", "primary moods"),
            ("UPDATE global_features SET mood_confidence = 0.0 WHERE mood_confidence IS NULL OR mood_confidence < 0 OR mood_confidence > 1", "mood confidence"),
            ("UPDATE global_features SET energy_level = 'medium' WHERE energy_level IS NULL OR energy_level = '' OR energy_level = 'None'", "energy levels"),
            ("UPDATE global_features SET bpm_category = 'medium' WHERE bpm_category IS NULL OR bpm_category = '' OR bmp_category = 'None'", "bpm categories")
        ]
        
        for query, description in features_fixes:
            try:
                cursor.execute(query)
                affected = cursor.rowcount
                if affected > 0:
                    logger.info(f"Fixed {affected} {description}")
                    self.stats['fixed_nulls'] += affected
            except Exception as e:
                logger.warning(f"Failed to fix {description}: {e}")
    
    def _normalize_data_ranges(self, cursor: sqlite3.Cursor):
        """Normalisiere Datenbereich-Werte"""
        
        range_normalizations = [
            # BPM normalization (60-200)
            ("UPDATE global_features SET bpm = 60 WHERE bpm IS NOT NULL AND bpm < 60", "low BPM values"),
            ("UPDATE global_features SET bpm = 200 WHERE bpm IS NOT NULL AND bpm > 200", "high BPM values"),
            ("UPDATE global_features SET bpm = 120 WHERE bpm IS NULL OR bpm = 0", "null BPM values"),
            
            # Energy normalization (0-1)
            ("UPDATE global_features SET energy = 0.0 WHERE energy IS NOT NULL AND energy < 0", "negative energy"),
            ("UPDATE global_features SET energy = 1.0 WHERE energy IS NOT NULL AND energy > 1", "high energy"),
            ("UPDATE global_features SET energy = 0.5 WHERE energy IS NULL", "null energy"),
            
            # Valence normalization (0-1)  
            ("UPDATE global_features SET valence = 0.0 WHERE valence IS NOT NULL AND valence < 0", "negative valence"),
            ("UPDATE global_features SET valence = 1.0 WHERE valence IS NOT NULL AND valence > 1", "high valence"),
            ("UPDATE global_features SET valence = 0.5 WHERE valence IS NULL", "null valence"),
            
            # Danceability normalization (0-1)
            ("UPDATE global_features SET danceability = 0.0 WHERE danceability IS NOT NULL AND danceability < 0", "negative danceability"),
            ("UPDATE global_features SET danceability = 1.0 WHERE danceability IS NOT NULL AND danceability > 1", "high danceability"),
            ("UPDATE global_features SET danceability = 0.5 WHERE danceability IS NULL", "null danceability"),
        ]
        
        for query, description in range_normalizations:
            cursor.execute(query)
            affected = cursor.rowcount
            if affected > 0:
                logger.info(f"Normalized {affected} {description}")
                self.stats['normalized_values'] += affected
    
    def _remove_orphaned_records(self, cursor: sqlite3.Cursor):
        """Entferne verwaiste und ungültige Einträge"""
        
        # Remove broken tracks
        orphan_removals = [
            ("DELETE FROM tracks WHERE file_path IS NULL OR file_path = '' OR LENGTH(file_path) < 3", "invalid file paths"),
            ("DELETE FROM tracks WHERE filename IS NULL OR filename = '' OR LENGTH(filename) < 1", "invalid filenames"),
            ("DELETE FROM tracks WHERE duration IS NULL OR duration <= 0", "invalid durations"),
            
            # Remove features without tracks
            ("""DELETE FROM global_features WHERE track_id NOT IN (SELECT id FROM tracks)""", "orphaned features"),
            
            # Remove time series without tracks
            ("""DELETE FROM time_series_features WHERE track_id NOT IN (SELECT id FROM tracks)""", "orphaned time series"),
            
            # Remove old failed analysis tasks
            ("""DELETE FROM analysis_tasks WHERE status = 'error' AND (started_at IS NULL OR started_at < strftime('%s', 'now', '-30 days'))""", "old failed tasks"),
        ]
        
        for query, description in orphan_removals:
            cursor.execute(query)
            affected = cursor.rowcount
            if affected > 0:
                logger.info(f"Removed {affected} {description}")
                self.stats['removed_orphans'] += affected
    
    def _enforce_consistency(self, cursor: sqlite3.Cursor):
        """Erzwinge Datenbank-Konsistenz"""
        
        # Ensure all tracks have corresponding features
        cursor.execute("""
            INSERT INTO global_features (
                track_id, bpm, energy, valence, danceability, 
                key_name, camelot, key_confidence, primary_mood, mood_confidence
            )
            SELECT 
                t.id, 120.0, 0.5, 0.5, 0.5, 
                'Unknown', '1A', 0.0, 'neutral', 0.0
            FROM tracks t 
            WHERE t.id NOT IN (SELECT track_id FROM global_features)
        """)
        
        missing_features = cursor.rowcount
        if missing_features > 0:
            logger.info(f"Created features for {missing_features} tracks without features")
            self.stats['cleaned_records'] += missing_features
        
        # Update analysis timestamps
        cursor.execute("""
            UPDATE global_features 
            SET analyzed_at = strftime('%s', 'now') 
            WHERE analyzed_at IS NULL OR analyzed_at = 0
        """)
        
        # Ensure mood_scores JSON validity
        cursor.execute("""
            UPDATE global_features 
            SET mood_scores = '{"neutral": 1.0}' 
            WHERE mood_scores IS NULL OR mood_scores = '' OR mood_scores = 'None'
        """)
    
    def _optimize_performance(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
        """Optimiere Datenbank-Performance"""
        
        # Update statistics
        cursor.execute("ANALYZE")
        
        # Rebuild indexes if needed
        indexes_to_rebuild = [
            "idx_tracks_file_path",
            "idx_tracks_artist", 
            "idx_global_features_bpm",
            "idx_global_features_energy",
            "idx_global_features_mood"
        ]
        
        for index_name in indexes_to_rebuild:
            try:
                cursor.execute(f"REINDEX {index_name}")
                logger.debug(f"Rebuilt index: {index_name}")
            except Exception as e:
                logger.warning(f"Could not rebuild index {index_name}: {e}")
        
        # Commit before VACUUM
        conn.commit()
        
        # Vacuum for space reclamation (outside transaction)
        conn.isolation_level = None  # autocommit mode
        cursor.execute("VACUUM")
        conn.isolation_level = ''  # back to normal
        logger.info("Database vacuumed and optimized")
    
    def _verify_integrity(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        """Überprüfe Datenbank-Integrität"""
        
        integrity_results = {}
        
        # Count records
        cursor.execute("SELECT COUNT(*) FROM tracks")
        integrity_results['total_tracks'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM global_features")
        integrity_results['total_features'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM time_series_features")
        integrity_results['total_time_series'] = cursor.fetchone()[0]
        
        # Check for remaining issues
        issue_checks = [
            ("SELECT COUNT(*) FROM tracks WHERE title IS NULL OR title = ''", "tracks_without_title"),
            ("SELECT COUNT(*) FROM tracks WHERE artist IS NULL OR artist = ''", "tracks_without_artist"),
            ("SELECT COUNT(*) FROM global_features WHERE key_name IS NULL OR key_name = ''", "features_without_key"),
            ("SELECT COUNT(*) FROM global_features WHERE camelot IS NULL OR camelot = ''", "features_without_camelot"),
            ("SELECT COUNT(*) FROM global_features WHERE primary_mood IS NULL OR primary_mood = ''", "features_without_mood"),
            ("SELECT COUNT(*) FROM global_features WHERE bpm IS NULL OR bpm < 60 OR bpm > 200", "invalid_bpm_values"),
            ("SELECT COUNT(*) FROM global_features WHERE energy IS NULL OR energy < 0 OR energy > 1", "invalid_energy_values"),
        ]
        
        issues_found = 0
        for query, check_name in issue_checks:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            integrity_results[check_name] = count
            if count > 0:
                issues_found += 1
                logger.warning(f"{check_name}: {count} issues remain")
            else:
                logger.info(f"✓ {check_name}: OK")
        
        integrity_results['issues_found'] = issues_found
        integrity_results['integrity_score'] = max(0, 100 - (issues_found * 10))
        
        return integrity_results

def run_advanced_cleanup(db_path: str = "data/database.db"):
    """Führe erweiterte Bereinigung aus"""
    
    logger.info("=== Advanced Database Cleanup Started ===")
    
    cleaner = AdvancedDatabaseCleaner(db_path)
    results = cleaner.advanced_cleanup()
    
    if results['success']:
        logger.info("=== Advanced Cleanup Results ===")
        logger.info(f"Statistics: {results['stats']}")
        logger.info(f"Integrity Score: {results['integrity']['integrity_score']}/100")
        logger.info(f"Total Tracks: {results['integrity']['total_tracks']}")
        logger.info(f"Total Features: {results['integrity']['total_features']}")
        
        if results['integrity']['issues_found'] == 0:
            logger.info("🎉 Perfect database integrity achieved!")
        else:
            logger.warning(f"⚠️ {results['integrity']['issues_found']} integrity issues remain")
        
        return True
    else:
        logger.error(f"Advanced cleanup failed: {results['error']}")
        return False

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/database.db"
    success = run_advanced_cleanup(db_path)
    sys.exit(0 if success else 1)