#!/usr/bin/env python3
"""
Database Cleanup Script - Bereinigt NULL-Werte und korrigiert inkonsistente Daten
"""

import sqlite3
import logging
import os
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core_engine.data_management.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_database(db_path: str = "data/database.db"):
    """Bereinigt die Datenbank von NULL-Werten und inkonsistenten Daten"""
    
    db_full_path = Path(db_path)
    if not db_full_path.exists():
        logger.error(f"Database not found: {db_full_path}")
        return False
    
    logger.info(f"Starting database cleanup: {db_full_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Tracks-Tabelle bereinigen
        logger.info("Cleaning tracks table...")
        
        # Setze Default-Werte für NULL-Felder
        cursor.execute("""
            UPDATE tracks 
            SET title = COALESCE(title, filename)
            WHERE title IS NULL OR title = ''
        """)
        
        cursor.execute("""
            UPDATE tracks 
            SET artist = COALESCE(artist, 'Unknown Artist')
            WHERE artist IS NULL OR artist = ''
        """)
        
        cursor.execute("""
            UPDATE tracks 
            SET genre = COALESCE(genre, 'Unknown')
            WHERE genre IS NULL OR genre = ''
        """)
        
        # 2. Global Features bereinigen
        logger.info("Cleaning global_features table...")
        
        cursor.execute("""
            UPDATE global_features 
            SET key_name = COALESCE(key_name, 'Unknown')
            WHERE key_name IS NULL OR key_name = ''
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET camelot = COALESCE(camelot, '1A')
            WHERE camelot IS NULL OR camelot = ''
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET key_confidence = COALESCE(key_confidence, 0.0)
            WHERE key_confidence IS NULL
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET primary_mood = COALESCE(primary_mood, 'neutral')
            WHERE primary_mood IS NULL OR primary_mood = ''
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET mood_confidence = COALESCE(mood_confidence, 0.0)
            WHERE mood_confidence IS NULL
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET energy_level = COALESCE(energy_level, 'medium')
            WHERE energy_level IS NULL OR energy_level = ''
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET bpm_category = COALESCE(bpm_category, 'medium')
            WHERE bpm_category IS NULL OR bpm_category = ''
        """)
        
        # 3. Bereiche für Zahlen-Felder begrenzen
        logger.info("Normalizing numeric ranges...")
        
        cursor.execute("""
            UPDATE global_features 
            SET bpm = CASE 
                WHEN bpm < 60 THEN 60
                WHEN bpm > 200 THEN 200
                ELSE bpm
            END
            WHERE bpm IS NOT NULL
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET energy = CASE 
                WHEN energy < 0 THEN 0
                WHEN energy > 1 THEN 1
                ELSE energy
            END
            WHERE energy IS NOT NULL
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET valence = CASE 
                WHEN valence < 0 THEN 0
                WHEN valence > 1 THEN 1
                ELSE valence
            END
            WHERE valence IS NOT NULL
        """)
        
        cursor.execute("""
            UPDATE global_features 
            SET danceability = CASE 
                WHEN danceability < 0 THEN 0
                WHEN danceability > 1 THEN 1
                ELSE danceability
            END
            WHERE danceability IS NOT NULL
        """)
        
        # 4. Lösche kaputte/verwaiste Einträge
        logger.info("Removing orphaned and invalid entries...")
        
        # Lösche Tracks ohne existierende Dateien
        cursor.execute("""
            DELETE FROM tracks 
            WHERE file_path IS NULL 
               OR file_path = ''
               OR LENGTH(file_path) < 3
        """)
        
        # Lösche alte, fehlgeschlagene Analyse-Tasks
        cursor.execute("""
            DELETE FROM analysis_tasks 
            WHERE status = 'error' 
              AND (started_at IS NULL OR started_at < strftime('%s', 'now', '-7 days'))
        """)
        
        # 5. Konsistenz-Checks
        logger.info("Running consistency checks...")
        
        # Zähle bereinigte Einträge
        cursor.execute("SELECT COUNT(*) FROM tracks")
        tracks_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM global_features")
        features_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM time_series_features")
        timeseries_count = cursor.fetchone()[0]
        
        # Commit alle Änderungen
        conn.commit()
        logger.info("Database cleanup completed successfully!")
        logger.info(f"Statistics: {tracks_count} tracks, {features_count} feature sets, {timeseries_count} time series entries")
        
        # Optimiere Datenbank
        logger.info("Optimizing database...")
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        
        return True
        
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_database_integrity(db_path: str = "data/database.db"):
    """Überprüft die Datenbank-Integrität nach der Bereinigung"""
    
    logger.info("Verifying database integrity...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check für NULL-Werte in kritischen Feldern
        checks = [
            ("tracks", "title", "Tracks without title"),
            ("tracks", "file_path", "Tracks without file_path"), 
            ("global_features", "key_name", "Features without key_name"),
            ("global_features", "camelot", "Features without camelot"),
            ("global_features", "primary_mood", "Features without primary_mood")
        ]
        
        issues_found = 0
        for table, field, description in checks:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {field} IS NULL OR {field} = ''")
            count = cursor.fetchone()[0]
            if count > 0:
                logger.warning(f"{description}: {count} entries")
                issues_found += 1
            else:
                logger.info(f"✓ {description}: OK")
        
        # Check für ungültige Camelot-Werte (vereinfacht ohne REGEXP)
        cursor.execute("""
            SELECT COUNT(*) FROM global_features 
            WHERE camelot IS NULL OR camelot = '' OR LENGTH(camelot) < 2
        """)
        invalid_camelot = cursor.fetchone()[0]
        if invalid_camelot > 0:
            logger.warning(f"Invalid Camelot values: {invalid_camelot}")
            issues_found += 1
        
        # Check für ungültige BPM-Werte
        cursor.execute("""
            SELECT COUNT(*) FROM global_features 
            WHERE bpm IS NULL OR bpm < 60 OR bpm > 200
        """)
        invalid_bpm = cursor.fetchone()[0]
        if invalid_bpm > 0:
            logger.warning(f"Invalid BPM values: {invalid_bpm}")
            issues_found += 1
        
        if issues_found == 0:
            logger.info("✓ Database integrity check passed!")
            return True
        else:
            logger.warning(f"Database integrity check found {issues_found} issues")
            return False
            
    except Exception as e:
        logger.error(f"Database integrity check failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/database.db"
    
    print("=== Database Cleanup Script ===")
    print(f"Target database: {db_path}")
    
    # Backup erstellen
    backup_path = f"{db_path}.backup"
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
    
    # Cleanup durchführen
    if cleanup_database(db_path):
        # Integrität überprüfen
        if verify_database_integrity(db_path):
            logger.info("Database cleanup completed successfully!")
        else:
            logger.warning("Database cleanup completed with warnings")
    else:
        logger.error("Database cleanup failed!")
        sys.exit(1)