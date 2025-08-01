import pytest
import numpy as np
import os
import tempfile
import json
from unittest.mock import Mock, patch
from pathlib import Path

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
def mock_track_metadata():
    """Mock track metadata for testing"""
    return {
        'filename': 'test_track.mp3',
        'title': 'Test Track',
        'artist': 'Test Artist',
        'bpm': 128.0,
        'key': 'C',
        'camelot_key': '8B',
        'energy_level': 0.75,
        'mood': 'energetic',
        'duration': 180.0,
        'spectral_centroid': 2000.0,
        'spectral_rolloff': 4000.0,
        'zero_crossing_rate': 0.1,
        'mfcc': np.random.rand(13).tolist(),
        'chroma': np.random.rand(12).tolist(),
        'tempo_confidence': 0.95
    }

@pytest.fixture
def temp_audio_file(mock_audio_data):
    """Create a temporary audio file for testing"""
    audio_data, sample_rate = mock_audio_data
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        # Mock file creation - in real scenario would use soundfile
        temp_file.write(b'RIFF')
        temp_file.write((36 + len(audio_data) * 2).to_bytes(4, 'little'))
        temp_file.write(b'WAVE')
        
        yield temp_file.name
        
    # Cleanup
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass

@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing"""
    cache_manager = Mock()
    cache_manager.get_cached_analysis.return_value = None
    cache_manager.cache_analysis.return_value = True
    cache_manager.is_cached.return_value = False
    cache_manager.clear_cache.return_value = True
    return cache_manager

@pytest.fixture
def mock_playlist_data():
    """Mock playlist data for testing"""
    return {
        'name': 'Test Playlist',
        'tracks': [
            {
                'filename': 'track1.mp3',
                'bpm': 128.0,
                'key': 'C',
                'energy_level': 0.7
            },
            {
                'filename': 'track2.mp3', 
                'bpm': 130.0,
                'key': 'G',
                'energy_level': 0.8
            },
            {
                'filename': 'track3.mp3',
                'bpm': 132.0,
                'key': 'D',
                'energy_level': 0.9
            }
        ],
        'rules': {
            'bpm_range': [125, 135],
            'key_compatibility': True,
            'energy_progression': 'ascending'
        }
    }

@pytest.fixture
def mock_essentia():
    """Mock Essentia algorithms for testing"""
    essentia_mock = Mock()
    
    # Mock BeatTracker
    beat_tracker = Mock()
    beat_tracker.return_value = ([1.0, 2.0, 3.0], [128.0])  # beats, bpm
    essentia_mock.BeatTrackerMultiFeature = Mock(return_value=beat_tracker)
    
    # Mock KeyExtractor
    key_extractor = Mock()
    key_extractor.return_value = ('C', 'major', 0.9)  # key, scale, strength
    essentia_mock.KeyExtractor = Mock(return_value=key_extractor)
    
    # Mock MusicExtractor
    music_extractor = Mock()
    music_extractor.return_value = (Mock(), Mock())  # features, features_frames
    essentia_mock.MusicExtractor = Mock(return_value=music_extractor)
    
    return essentia_mock

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        'audio': {
            'sample_rate': 44100,
            'hop_length': 512,
            'n_fft': 2048
        },
        'analysis': {
            'bpm_range': [60, 200],
            'key_profiles': ['krumhansl', 'temperley'],
            'energy_window_size': 2048
        },
        'playlist': {
            'max_bpm_difference': 10,
            'key_compatibility_strict': False,
            'energy_smoothing': True
        }
    }

@pytest.fixture
def mock_gui_components():
    """Mock GUI components for testing"""
    from unittest.mock import Mock
    
    mock_app = Mock()
    mock_window = Mock()
    mock_widget = Mock()
    
    return {
        'app': mock_app,
        'window': mock_window,
        'widget': mock_widget
    }

@pytest.fixture(scope="session")
def test_data_dir():
    """Directory for test data files"""
    test_dir = Path(__file__).parent / 'data'
    test_dir.mkdir(exist_ok=True)
    return test_dir

@pytest.fixture
def mock_export_formats():
    """Mock export format configurations"""
    return {
        'm3u': {
            'extension': '.m3u',
            'supports_metadata': False,
            'encoding': 'utf-8'
        },
        'rekordbox_xml': {
            'extension': '.xml',
            'supports_metadata': True,
            'encoding': 'utf-8'
        },
        'csv': {
            'extension': '.csv',
            'supports_metadata': True,
            'encoding': 'utf-8'
        }
    }