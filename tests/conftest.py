"""
Pytest configuration and fixtures for FastAPI backend testing
"""

import pytest
import asyncio
import tempfile
import os
import json
import sqlite3
from pathlib import Path
from typing import Generator, Dict, List
from unittest.mock import Mock, AsyncMock
import numpy as np

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import backend components
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import backend components (conditional for testing)
try:
    from backend.main import app
    from backend.config.settings import settings
except ImportError:
    # For isolated testing without full backend setup
    app = None
    settings = {}


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """FastAPI test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client():
    """Async FastAPI test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def test_data_dir():
    """Directory for test data files"""
    test_dir = Path(__file__).parent / 'data'
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def temp_cache_dir():
    """Temporary cache directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "cache"
        cache_dir.mkdir()
        yield str(cache_dir)


@pytest.fixture
def temp_export_dir():
    """Temporary export directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        export_dir = Path(temp_dir) / "exports"
        export_dir.mkdir()
        yield str(export_dir)


@pytest.fixture
def test_database():
    """In-memory SQLite database for testing"""
    # Create an in-memory database
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    
    # Create test schema
    cursor = connection.cursor()
    
    # Tracks table
    cursor.execute("""
        CREATE TABLE tracks (
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
            created_at REAL DEFAULT (datetime('now')),
            updated_at REAL DEFAULT (datetime('now'))
        )
    """)
    
    # Global features table
    cursor.execute("""
        CREATE TABLE global_features (
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
            analyzed_at REAL DEFAULT (datetime('now')),
            FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
        )
    """)
    
    # Time series features table (NEW)
    cursor.execute("""
        CREATE TABLE time_series_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            timestamp REAL NOT NULL,  -- Time offset in seconds
            energy_value REAL,
            brightness_value REAL,
            spectral_rolloff REAL,
            rms_energy REAL,
            created_at REAL DEFAULT (datetime('now')),
            FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
        )
    """)
    
    # Analysis tasks table (for background job tracking)
    cursor.execute("""
        CREATE TABLE analysis_tasks (
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
    
    connection.commit()
    
    yield connection
    
    connection.close()


@pytest.fixture
def test_database_file():
    """Temporary SQLite database file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        db_path = temp_db.name
    
    # Create test database
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    
    # Create test schema (same as above)
    cursor = connection.cursor()
    
    cursor.execute("""
        CREATE TABLE tracks (
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
            created_at REAL DEFAULT (datetime('now')),
            updated_at REAL DEFAULT (datetime('now'))
        )
    """)
    
    cursor.execute("""
        CREATE TABLE global_features (
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
            analyzed_at REAL DEFAULT (datetime('now')),
            FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE time_series_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            energy_value REAL,
            brightness_value REAL,
            spectral_rolloff REAL,
            rms_energy REAL,
            created_at REAL DEFAULT (datetime('now')),
            FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE analysis_tasks (
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
    
    connection.commit()
    connection.close()
    
    yield db_path
    
    # Cleanup - ensure all connections are closed first
    try:
        # Small delay to allow connection cleanup
        import time
        time.sleep(0.1)
        os.unlink(db_path)
    except PermissionError:
        # On Windows, sometimes file handles are still open
        # Try again after a short delay
        time.sleep(0.5)
        try:
            os.unlink(db_path)
        except PermissionError:
            # If still failing, log warning but don't fail test
            import logging
            logging.warning(f"Could not cleanup test database file: {db_path}")


@pytest.fixture
def mock_audio_data():
    """Generate mock audio data for testing"""
    sample_rate = 44100
    duration = 3.0  # 3 seconds
    samples = int(sample_rate * duration)
    
    # Generate a simple sine wave
    t = np.linspace(0, duration, samples, False)
    frequency = 440.0  # A4 note
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    return audio_data, sample_rate


@pytest.fixture
def mock_audio_file(mock_audio_data, test_data_dir):
    """Create a mock audio file for testing"""
    audio_data, sample_rate = mock_audio_data
    
    # Create a simple WAV file mock
    audio_file = test_data_dir / "test_track.wav"
    
    # Create mock WAV file (simplified)
    with open(audio_file, 'wb') as f:
        # Write basic WAV header
        f.write(b'RIFF')
        f.write((36 + len(audio_data) * 2).to_bytes(4, 'little'))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write((16).to_bytes(4, 'little'))
        f.write((1).to_bytes(2, 'little'))  # PCM
        f.write((1).to_bytes(2, 'little'))  # Mono
        f.write(sample_rate.to_bytes(4, 'little'))
        f.write((sample_rate * 2).to_bytes(4, 'little'))
        f.write((2).to_bytes(2, 'little'))
        f.write((16).to_bytes(2, 'little'))
        f.write(b'data')
        f.write((len(audio_data) * 2).to_bytes(4, 'little'))
        
        # Write audio data as 16-bit PCM
        for sample in audio_data:
            sample_int = int(sample * 32767)
            f.write(sample_int.to_bytes(2, 'little', signed=True))
    
    yield str(audio_file)
    
    # Cleanup
    if audio_file.exists():
        audio_file.unlink()


@pytest.fixture
def sample_track_analysis():
    """Sample track analysis data"""
    return {
        "file_path": "/path/to/test_track.mp3",
        "filename": "test_track.mp3",
        "features": {
            "energy": 0.75,
            "valence": 0.65,
            "danceability": 0.8,
            "bpm": 128.0,
            "key_numeric": 5.0,
            "mode": "major",
            "loudness": -10.5,
            "spectral_centroid": 2000.0,
            "zero_crossing_rate": 0.1,
            "mfcc_variance": 15.2
        },
        "metadata": {
            "title": "Test Track",
            "artist": "Test Artist",
            "album": "Test Album",
            "genre": "Electronic",
            "year": "2024",
            "duration": 180.0,
            "file_size": 5242880,
            "file_path": "/path/to/test_track.mp3",
            "filename": "test_track.mp3",
            "extension": ".mp3",
            "analyzed_at": 1704067200.0
        },
        "camelot": {
            "key": "C Major",
            "camelot": "8B",
            "key_confidence": 0.95,
            "compatible_keys": ["8A", "9B", "7B"]
        },
        "derived_metrics": {
            "energy_level": "high",
            "bmp_category": "medium",
            "estimated_mood": "euphoric",
            "danceability_level": "high"
        },
        "mood": {
            "primary_mood": "euphoric",
            "confidence": 0.85,
            "scores": {
                "euphoric": 0.85,
                "driving": 0.7,
                "uplifting": 0.6,
                "chill": 0.2,
                "dark": 0.1
            },
            "explanation": "Classified as euphoric with 85% confidence"
        },
        "errors": [],
        "status": "completed",
        "version": "2.0"
    }


@pytest.fixture
def sample_playlist_data(sample_track_analysis):
    """Sample playlist data with multiple tracks"""
    tracks = []
    for i in range(3):
        track = sample_track_analysis.copy()
        track["file_path"] = f"/path/to/track_{i+1}.mp3"
        track["filename"] = f"track_{i+1}.mp3"
        track["metadata"]["title"] = f"Test Track {i+1}"
        track["features"]["bpm"] = 128.0 + i * 2  # Varying BPMs
        tracks.append(track)
    
    return {
        "tracks": tracks,
        "metadata": {
            "total_tracks": 3,
            "total_duration_seconds": 540.0,
            "total_duration_minutes": 9.0,
            "average_energy": 0.75,
            "average_valence": 0.65,
            "average_danceability": 0.8,
            "bpm_stats": {"min": 128.0, "max": 132.0, "avg": 130.0},
            "key_distribution": {"8B": 3},
            "mood_distribution": {"euphoric": 3},
            "energy_progression": [0.75, 0.75, 0.75],
            "preset_name": "hybrid_smart",
            "energy_curve": "gradual_build",
            "mood_flow": "coherent"
        },
        "preset_used": "hybrid_smart",
        "algorithm": "hybrid_smart",
        "rules_applied": [{"harmonic_compatibility": 0.8}],
        "created_at": "2024-01-01T12:00:00",
        "status": "completed"
    }


@pytest.fixture
def mock_analyzer():
    """Mock AudioAnalyzer for testing"""
    analyzer = Mock()
    analyzer.analyze_track = AsyncMock()
    analyzer.analyze_batch_async = AsyncMock()
    analyzer.get_supported_formats.return_value = [".mp3", ".wav", ".flac"]
    analyzer.get_analysis_stats.return_value = {
        "total_analyzed": 10,
        "average_processing_time": 2.5,
        "cache_hit_rate": 0.8
    }
    return analyzer


@pytest.fixture
def mock_playlist_engine():
    """Mock PlaylistEngine for testing"""
    engine = Mock()
    engine.create_playlist_async = AsyncMock()
    engine.get_all_presets.return_value = [
        {
            "name": "hybrid_smart",
            "description": "Intelligent hybrid algorithm",
            "algorithm": "hybrid_smart",
            "energy_curve": "gradual_build",
            "mood_flow": "coherent",
            "target_duration_minutes": 60,
            "is_default": True,
            "created_at": "2024-01-01T00:00:00"
        }
    ]
    engine.get_preset_details.return_value = {
        "name": "hybrid_smart",
        "description": "Intelligent hybrid algorithm",
        "algorithm": "hybrid_smart",
        "rules": [],
        "energy_curve": "gradual_build",
        "mood_flow": "coherent",
        "target_duration_minutes": 60,
        "is_default": True,
        "created_at": "2024-01-01T00:00:00"
    }
    engine.get_algorithm_info.return_value = [
        {
            "name": "hybrid_smart",
            "description": "Intelligent hybrid algorithm",
            "features": ["harmonic", "energy", "mood"]
        }
    ]
    return engine


@pytest.fixture
def mock_cache_manager():
    """Mock CacheManager for testing"""
    cache_manager = Mock()
    cache_manager.is_cached.return_value = False
    cache_manager.load_from_cache.return_value = None
    cache_manager.save_to_cache = Mock()
    cache_manager.get_cache_stats.return_value = {
        "total_files": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0.0,
        "cache_directory": "/tmp/cache",
        "created": 1704067200.0,
        "last_cleanup": 1704067200.0,
        "oldest_file": 1704067200.0,
        "newest_file": 1704067200.0
    }
    cache_manager.get_cached_files.return_value = []
    cache_manager.cleanup_cache.return_value = {
        "removed_files": 0,
        "freed_mb": 0.0
    }
    cache_manager.clear_cache.return_value = 0
    cache_manager.optimize_cache.return_value = {
        "removed_entries": 0,
        "freed_mb": 0.0
    }
    return cache_manager


@pytest.fixture
def mock_mood_classifier():
    """Mock MoodClassifier for testing"""
    classifier = Mock()
    classifier.classify_mood.return_value = ("euphoric", 0.85, {
        "euphoric": 0.85,
        "driving": 0.7,
        "uplifting": 0.6,
        "chill": 0.2,
        "dark": 0.1
    })
    classifier.get_mood_categories.return_value = [
        "euphoric", "driving", "dark", "chill", "melancholic", 
        "aggressive", "uplifting", "mysterious", "neutral"
    ]
    return classifier


@pytest.fixture
def mock_playlist_exporter():
    """Mock PlaylistExporter for testing"""
    exporter = Mock()
    exporter.export_playlist.return_value = {
        "success": True,
        "output_path": "/tmp/test_playlist.m3u",
        "filename": "test_playlist.m3u",
        "track_count": 3,
        "file_size_bytes": 1024
    }
    exporter.get_supported_formats.return_value = ["m3u", "json", "csv", "rekordbox"]
    exporter.list_exports.return_value = []
    exporter.delete_export.return_value = True
    exporter.validate_tracks.return_value = {
        "valid": True,
        "issues": [],
        "track_count": 3
    }
    return exporter


@pytest.fixture
def analysis_request_data():
    """Sample analysis request data"""
    return {
        "directories": ["/path/to/music"],
        "recursive": True,
        "overwrite_cache": False,
        "include_patterns": None,
        "exclude_patterns": None
    }


@pytest.fixture  
def playlist_generation_request_data():
    """Sample playlist generation request data"""
    return {
        "track_file_paths": [
            "/path/to/track1.mp3",
            "/path/to/track2.mp3", 
            "/path/to/track3.mp3"
        ],
        "preset_name": "hybrid_smart",
        "custom_rules": None,
        "target_duration_minutes": 60
    }


@pytest.fixture
def playlist_export_request_data(sample_playlist_data):
    """Sample playlist export request data"""
    return {
        "playlist_data": sample_playlist_data,
        "format_type": "m3u",
        "filename": "test_playlist",
        "include_metadata": True
    }


# Test utilities
class TestUtils:
    """Test utility functions"""
    
    @staticmethod
    def create_mock_track_file(file_path: str, duration: float = 180.0):
        """Create a mock track file for testing"""
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(f"# Mock audio file - duration: {duration}s")
    
    @staticmethod
    def cleanup_mock_files(file_paths: List[str]):
        """Clean up mock files after testing"""
        for file_path in file_paths:
            try:
                Path(file_path).unlink()
            except FileNotFoundError:
                pass


@pytest.fixture
def test_utils():
    """Test utility functions"""
    return TestUtils