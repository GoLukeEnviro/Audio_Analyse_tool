"""
Unit tests for DatabaseManager
"""

import pytest
import tempfile
import os
import sqlite3
import json
from unittest.mock import Mock, patch
from pathlib import Path

from backend.core_engine.data_management.database_manager import (
    DatabaseManager, TrackRecord, GlobalFeaturesRecord, TimeSeriesRecord
)


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseManager:
    """Test DatabaseManager functionality"""
    
    def test_database_initialization(self, test_database_file):
        """Test that database is initialized correctly"""
        db_manager = DatabaseManager(test_database_file)
        
        # Test connection
        conn = db_manager._get_connection()
        assert conn is not None
        
        # Test that tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['tracks', 'global_features', 'time_series_features', 'analysis_tasks']
        for table in expected_tables:
            assert table in tables
        
        db_manager.close()
    
    def test_add_track(self, test_database_file):
        """Test adding a track to the database"""
        db_manager = DatabaseManager(test_database_file)
        
        metadata = {
            'filename': 'test.mp3',
            'title': 'Test Track',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'genre': 'Electronic',
            'year': '2024',
            'duration': 180.0,
            'file_size': 5242880,
            'extension': '.mp3'
        }
        
        track_id = db_manager.add_track('/test/path/test.mp3', metadata)
        
        assert track_id is not None
        assert isinstance(track_id, int)
        assert track_id > 0
        
        # Verify track was added
        track = db_manager.get_track_by_id(track_id)
        assert track is not None
        assert track.file_path == '/test/path/test.mp3'
        assert track.title == 'Test Track'
        assert track.artist == 'Test Artist'
        
        db_manager.close()
    
    def test_duplicate_track_handling(self, test_database_file):
        """Test handling of duplicate tracks"""
        db_manager = DatabaseManager(test_database_file)
        
        metadata = {
            'filename': 'test.mp3',
            'title': 'Test Track',
            'artist': 'Test Artist',
            'duration': 180.0,
            'file_size': 5242880,
            'extension': '.mp3'
        }
        
        # Add track first time
        track_id1 = db_manager.add_track('/test/path/test.mp3', metadata)
        
        # Add same track again
        track_id2 = db_manager.add_track('/test/path/test.mp3', metadata)
        
        # Should return the same ID
        assert track_id1 == track_id2
        
        db_manager.close()
    
    def test_update_global_features(self, test_database_file):
        """Test updating global features for a track"""
        db_manager = DatabaseManager(test_database_file)
        
        # Add track first
        metadata = {'filename': 'test.mp3', 'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'}
        track_id = db_manager.add_track('/test/path/test.mp3', metadata)
        
        # Update features
        features = {
            'bpm': 128.0,
            'energy': 0.75,
            'valence': 0.65,
            'danceability': 0.8,
            'loudness': -10.5,
            'camelot': {
                'key': 'C Major',
                'camelot': '8B',
                'key_confidence': 0.95
            },
            'mood': {
                'primary_mood': 'euphoric',
                'confidence': 0.85,
                'scores': {'euphoric': 0.85, 'driving': 0.7}
            },
            'derived_metrics': {
                'energy_level': 'high',
                'bpm_category': 'medium'
            }
        }
        
        db_manager.update_global_features(track_id, features)
        
        # Verify features were saved
        conn = db_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM global_features WHERE track_id = ?", (track_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row['bpm'] == 128.0
        assert row['energy'] == 0.75
        assert row['camelot'] == '8B'
        assert row['primary_mood'] == 'euphoric'
        
        # Test mood scores JSON parsing
        mood_scores = json.loads(row['mood_scores'])
        assert mood_scores['euphoric'] == 0.85
        
        db_manager.close()
    
    def test_add_time_series_data(self, test_database_file):
        """Test adding time series data"""
        db_manager = DatabaseManager(test_database_file)
        
        # Add track first
        metadata = {'filename': 'test.mp3', 'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'}
        track_id = db_manager.add_track('/test/path/test.mp3', metadata)
        
        # Add time series data
        time_series_data = [
            {'timestamp': 0.0, 'energy_value': 0.6, 'brightness_value': 0.5, 'spectral_rolloff': 2000.0},
            {'timestamp': 5.0, 'energy_value': 0.7, 'brightness_value': 0.6, 'spectral_rolloff': 2100.0},
            {'timestamp': 10.0, 'energy_value': 0.8, 'brightness_value': 0.7, 'spectral_rolloff': 2200.0}
        ]
        
        db_manager.add_time_series_data(track_id, time_series_data)
        
        # Retrieve and verify data
        time_series_records = db_manager.get_time_series_data(track_id)
        assert len(time_series_records) == 3
        
        assert time_series_records[0].timestamp == 0.0
        assert time_series_records[0].energy_value == 0.6
        assert time_series_records[1].timestamp == 5.0
        assert time_series_records[2].timestamp == 10.0
        
        db_manager.close()
    
    def test_is_cached(self, test_database_file):
        """Test caching check functionality"""
        db_manager = DatabaseManager(test_database_file)
        
        # Initially not cached
        assert db_manager.is_cached('/test/path/test.mp3') is False
        
        # Add track but no features - still not cached
        metadata = {'filename': 'test.mp3', 'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'}
        track_id = db_manager.add_track('/test/path/test.mp3', metadata)
        assert db_manager.is_cached('/test/path/test.mp3') is False
        
        # Add features - now cached
        features = {'bpm': 128.0, 'energy': 0.75, 'valence': 0.65, 'danceability': 0.8}
        db_manager.update_global_features(track_id, features)
        assert db_manager.is_cached('/test/path/test.mp3') is True
        
        db_manager.close()
    
    def test_save_to_cache_compatibility(self, test_database_file):
        """Test save_to_cache interface compatibility with old CacheManager"""
        db_manager = DatabaseManager(test_database_file)
        
        # Add track first to ensure it exists
        metadata = {
            'filename': 'test.mp3',
            'title': 'Test Track',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'genre': 'Electronic',
            'year': '2024',
            'duration': 200.0,
            'file_size': 6242880,
            'extension': '.mp3'
        }
        db_manager.add_track('/test/path/test.mp3', metadata)
        
        analysis_result = {
            'file_path': '/test/path/test.mp3',
            'filename': 'test.mp3',
            'features': {
                'bpm': 130.0,
                'energy': 0.85,
                'valence': 0.7,
                'danceability': 0.9,
                'loudness': -10.5,
                'spectral_centroid': 2500.0,
                'zero_crossing_rate': 0.05,
                'mfcc_variance': 0.02,
                'mood': {
                    'primary_mood': 'uplifting',
                    'confidence': 0.8,
                    'scores': {'uplifting': 0.8, 'euphoric': 0.6}
                },
                'camelot': {
                    'key': 'D Major',
                    'camelot': '10B',
                    'key_confidence': 0.9
                },
                'derived_metrics': {
                    'energy_level': 'high',
                    'bpm_category': 'medium'
                }
            },
            'metadata': metadata,
            'time_series_features': [
                {'timestamp': 0.0, 'energy_value': 0.7, 'brightness_value': 0.6},
                {'timestamp': 5.0, 'energy_value': 0.8, 'brightness_value': 0.7}
            ]
        }
        
        # Ensure track exists before saving to cache
        db_manager.add_track('/test/path/test.mp3', metadata)
        
        result = db_manager.save_to_cache('/test/path/test.mp3', analysis_result)
        assert result is True, f"save_to_cache should return True on success, got {result}"
        
        # Verify data was saved by checking database directly
        conn = db_manager._get_connection()
        cursor = conn.cursor()
        
        # Check if track exists
        cursor.execute("SELECT id FROM tracks WHERE file_path = ?", ('/test/path/test.mp3',))
        track_row = cursor.fetchone()
        assert track_row is not None, "Track should exist in database after save"
        
        # Check if global features exist
        cursor.execute("SELECT * FROM global_features WHERE track_id = ?", (track_row[0],))
        features_row = cursor.fetchone()
        assert features_row is not None, "Global features should exist in database"
        
        # Verify is_cached works
        assert db_manager.is_cached('/test/path/test.mp3') is True
        
        # Test load_from_cache returns valid data
        loaded_data = db_manager.load_from_cache('/test/path/test.mp3')
        assert loaded_data is not None, "load_from_cache should return data, not None"
        assert loaded_data['file_path'] == '/test/path/test.mp3'
        assert loaded_data['features']['bpm'] == 130.0
        assert loaded_data['metadata']['title'] == 'Test Track'
        assert loaded_data['features']['mood']['primary_mood'] == 'uplifting'
        assert len(loaded_data.get('time_series_features', [])) == 2
        
        db_manager.close()
    
    def test_load_from_cache_compatibility(self, test_database_file):
        """Test load_from_cache interface compatibility"""
        db_manager = DatabaseManager(test_database_file)
        
        # Non-existent track
        assert db_manager.load_from_cache('/nonexistent/path.mp3') is None
        
        # Add and retrieve track
        analysis_result = {
            'file_path': '/test/path/test.mp3',
            'filename': 'test.mp3',
            'features': {'bpm': 128.0, 'energy': 0.75},
            'metadata': {
                'filename': 'test.mp3', 'title': 'Test Track', 
                'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'
            },
            'camelot': {'key': 'C Major', 'camelot': '8B'},
            'mood': {'primary_mood': 'euphoric', 'confidence': 0.8, 'scores': {}}
        }
        
        db_manager.save_to_cache('/test/path/test.mp3', analysis_result)
        loaded_data = db_manager.load_from_cache('/test/path/test.mp3')
        
        # Verify format compatibility
        assert 'file_path' in loaded_data
        assert 'filename' in loaded_data
        assert 'features' in loaded_data
        assert 'metadata' in loaded_data
        assert 'camelot' in loaded_data
        assert 'mood' in loaded_data
        assert 'status' in loaded_data
        assert 'version' in loaded_data
        assert 'errors' in loaded_data
        
        assert loaded_data['status'] == 'completed'
        assert loaded_data['version'] == '2.0'
        
        db_manager.close()
    
    def test_get_all_tracks_with_filters(self, test_database_file):
        """Test getting tracks with filters"""
        db_manager = DatabaseManager(test_database_file)
        
        # Add multiple test tracks
        test_tracks = [
            {
                'path': '/test/track1.mp3',
                'metadata': {'filename': 'track1.mp3', 'artist': 'Artist A', 'genre': 'Electronic', 'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'},
                'features': {'bpm': 120.0, 'energy': 0.6}
            },
            {
                'path': '/test/track2.mp3', 
                'metadata': {'filename': 'track2.mp3', 'artist': 'Artist B', 'genre': 'House', 'duration': 200.0, 'file_size': 2048, 'extension': '.mp3'},
                'features': {'bpm': 128.0, 'energy': 0.8}
            },
            {
                'path': '/test/track3.mp3',
                'metadata': {'filename': 'track3.mp3', 'artist': 'Artist A', 'genre': 'Techno', 'duration': 220.0, 'file_size': 3072, 'extension': '.mp3'},
                'features': {'bpm': 135.0, 'energy': 0.9}
            }
        ]
        
        for track in test_tracks:
            track_id = db_manager.add_track(track['path'], track['metadata'])
            db_manager.update_global_features(track_id, track['features'])
        
        # Test filtering by artist
        artist_a_tracks = db_manager.get_all_tracks(filters={'artist': 'Artist A'})
        assert len(artist_a_tracks) == 2
        
        # Test filtering by BPM range
        high_bpm_tracks = db_manager.get_all_tracks(filters={'min_bpm': 125.0})
        assert len(high_bpm_tracks) == 2
        
        # Test filtering by energy range
        high_energy_tracks = db_manager.get_all_tracks(filters={'min_energy': 0.8})
        assert len(high_energy_tracks) == 2
        
        # Test pagination
        page1 = db_manager.get_all_tracks(limit=2, offset=0)
        assert len(page1) <= 2
        
        page2 = db_manager.get_all_tracks(limit=2, offset=2) 
        assert len(page2) <= 2
        
        db_manager.close()
    
    def test_get_cache_stats(self, test_database_file):
        """Test database statistics"""
        db_manager = DatabaseManager(test_database_file)
        
        stats = db_manager.get_cache_stats()
        
        # Check stats structure
        required_keys = ['total_tracks', 'analyzed_tracks', 'total_size_bytes', 'total_size_mb', 'database_path']
        for key in required_keys:
            assert key in stats
        
        # Initially empty
        assert stats['total_tracks'] == 0
        assert stats['analyzed_tracks'] == 0
        
        # Add a track
        metadata = {'filename': 'test.mp3', 'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'}
        track_id = db_manager.add_track('/test/path/test.mp3', metadata)
        
        stats = db_manager.get_cache_stats()
        assert stats['total_tracks'] == 1
        assert stats['analyzed_tracks'] == 0  # No features yet
        
        # Add features
        features = {'bpm': 128.0, 'energy': 0.75, 'valence': 0.65, 'danceability': 0.8}
        db_manager.update_global_features(track_id, features)
        
        stats = db_manager.get_cache_stats()
        assert stats['total_tracks'] == 1
        assert stats['analyzed_tracks'] == 1
        
        db_manager.close()
    
    def test_clear_cache(self, test_database_file):
        """Test clearing the database"""
        db_manager = DatabaseManager(test_database_file)
        
        # Add some data
        metadata = {'filename': 'test.mp3', 'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'}
        track_id = db_manager.add_track('/test/path/test.mp3', metadata)
        features = {'bpm': 128.0, 'energy': 0.75, 'valence': 0.65, 'danceability': 0.8}
        db_manager.update_global_features(track_id, features)
        
        # Verify data exists
        stats = db_manager.get_cache_stats()
        assert stats['total_tracks'] > 0
        
        # Clear cache
        cleared_count = db_manager.clear_cache()
        assert cleared_count > 0
        
        # Verify database is empty
        stats = db_manager.get_cache_stats()
        assert stats['total_tracks'] == 0
        assert stats['analyzed_tracks'] == 0
        
        db_manager.close()
    
    @pytest.mark.unit
    def test_connection_management(self, test_database_file):
        """Test connection management and cleanup"""
        db_manager = DatabaseManager(test_database_file)
        
        # Test connection is established
        conn1 = db_manager._get_connection()
        assert conn1 is not None
        
        # Test same connection is reused
        conn2 = db_manager._get_connection()
        assert conn1 is conn2
        
        # Test close
        db_manager.close()
        assert db_manager._connection is None
        
        # Test connection can be re-established
        conn3 = db_manager._get_connection()
        assert conn3 is not None
        
        db_manager.close()


@pytest.mark.unit
def test_data_classes():
    """Test data classes for type safety"""
    
    # Test TrackRecord
    track = TrackRecord(
        id=1, file_path='/test.mp3', filename='test.mp3',
        title='Test', artist='Artist', album='Album',
        genre='Electronic', year='2024', duration=180.0,
        file_size=1024, extension='.mp3',
        created_at=1234567890, updated_at=1234567890
    )
    
    assert track.id == 1
    assert track.file_path == '/test.mp3'
    assert track.duration == 180.0
    
    # Test GlobalFeaturesRecord
    features = GlobalFeaturesRecord(
        id=1, track_id=1, bpm=128.0, key_name='C Major',
        camelot='8B', key_confidence=0.95,
        energy=0.75, valence=0.65, danceability=0.8,
        loudness=-10.5, spectral_centroid=2000.0,
        zero_crossing_rate=0.1, mfcc_variance=15.2,
        primary_mood='euphoric', mood_confidence=0.85,
        mood_scores='{}', energy_level='high',
        bpm_category='medium', analyzed_at=1234567890
    )
    
    assert features.bpm == 128.0
    assert features.primary_mood == 'euphoric'
    
    # Test TimeSeriesRecord
    time_series = TimeSeriesRecord(
        id=1, track_id=1, timestamp=5.0,
        energy_value=0.75, brightness_value=0.6,
        spectral_rolloff=2000.0, rms_energy=0.5,
        created_at=1234567890
    )
    
    assert time_series.timestamp == 5.0
    assert time_series.energy_value == 0.75