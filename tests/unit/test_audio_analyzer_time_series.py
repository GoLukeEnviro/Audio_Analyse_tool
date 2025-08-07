"""
Unit tests for AudioAnalyzer time series functionality
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile

from backend.core_engine.audio_analysis.analyzer import AudioAnalyzer


@pytest.mark.unit
@pytest.mark.audio
class TestAudioAnalyzerTimeSeries:
    """Test AudioAnalyzer time series feature extraction"""
    
    @pytest.fixture
    def mock_audio_analyzer(self, test_database_file):
        """Create AudioAnalyzer with mocked dependencies"""
        with patch('backend.core_engine.audio_analysis.analyzer.DatabaseManager') as mock_db_manager, \
             patch('backend.core_engine.audio_analysis.analyzer.FeatureExtractor') as mock_feature_extractor, \
             patch('backend.core_engine.audio_analysis.analyzer.MoodClassifier') as mock_mood_classifier:
            
            analyzer = AudioAnalyzer(db_path=test_database_file)
            
            # Setup mocks
            analyzer.database_manager = mock_db_manager.return_value
            analyzer.feature_extractor = mock_feature_extractor.return_value
            analyzer.mood_classifier = mock_mood_classifier.return_value
            
            return analyzer
    
    def test_extract_time_series_features_basic(self, mock_audio_analyzer):
        """Test basic time series feature extraction"""
        # Create mock audio data (30 seconds at 44100 Hz)
        sample_rate = 44100
        duration = 30.0  # 30 seconds
        y = np.random.random(int(sample_rate * duration)).astype(np.float32)
        
        # Extract time series features
        time_series_data = mock_audio_analyzer._extract_time_series_features(y, sample_rate, window_seconds=5.0)
        
        # Should have 6 windows (30 seconds / 5 second windows)
        assert len(time_series_data) == 6
        
        # Check first data point structure
        first_point = time_series_data[0]
        required_keys = ['timestamp', 'energy_value', 'brightness_value', 'spectral_rolloff', 'rms_energy']
        for key in required_keys:
            assert key in first_point
        
        # Check timestamp progression
        assert first_point['timestamp'] == 0.0
        assert time_series_data[1]['timestamp'] == 5.0
        assert time_series_data[2]['timestamp'] == 10.0
        
        # Check values are reasonable
        assert 0 <= first_point['energy_value'] <= 1.0
        assert first_point['brightness_value'] > 0
        assert first_point['spectral_rolloff'] > 0
    
    def test_extract_time_series_features_short_audio(self, mock_audio_analyzer):
        """Test time series extraction with short audio"""
        # Create 3 second audio (shorter than one window)
        sample_rate = 44100
        duration = 3.0
        y = np.random.random(int(sample_rate * duration)).astype(np.float32)
        
        time_series_data = mock_audio_analyzer._extract_time_series_features(y, sample_rate, window_seconds=5.0)
        
        # Should have 0 windows (audio too short)
        assert len(time_series_data) == 0
    
    def test_extract_time_series_features_custom_window(self, mock_audio_analyzer):
        """Test time series extraction with custom window size"""
        # Create 20 second audio
        sample_rate = 44100
        duration = 20.0
        y = np.random.random(int(sample_rate * duration)).astype(np.float32)
        
        # Use 2 second windows
        time_series_data = mock_audio_analyzer._extract_time_series_features(y, sample_rate, window_seconds=2.0)
        
        # Should have 10 windows (20 seconds / 2 second windows)
        assert len(time_series_data) == 10
        
        # Check timestamp progression
        timestamps = [point['timestamp'] for point in time_series_data]
        expected_timestamps = [i * 2.0 for i in range(10)]
        assert timestamps == expected_timestamps
    
    def test_extract_time_series_features_values_range(self, mock_audio_analyzer):
        """Test that extracted values are in reasonable ranges"""
        # Create audio with controlled characteristics
        sample_rate = 44100
        duration = 10.0
        
        # Create a simple sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        frequency = 440.0  # A4 note
        y = np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        time_series_data = mock_audio_analyzer._extract_time_series_features(y, sample_rate, window_seconds=5.0)
        
        assert len(time_series_data) == 2
        
        for point in time_series_data:
            # Energy should be reasonable for sine wave
            assert 0 <= point['energy_value'] <= 1.0
            
            # Brightness (spectral centroid) should be around the frequency
            assert point['brightness_value'] > 0
            
            # Spectral rolloff should be reasonable
            assert point['spectral_rolloff'] > 0
            
            # RMS energy should match energy_value
            assert abs(point['rms_energy'] - point['energy_value']) < 0.01
    
    def test_extract_time_series_features_error_handling(self, mock_audio_analyzer):
        """Test error handling in time series extraction"""
        # Test with empty audio
        empty_audio = np.array([])
        time_series_data = mock_audio_analyzer._extract_time_series_features(empty_audio, 44100)
        assert len(time_series_data) == 0
        
        # Test with invalid sample rate
        y = np.random.random(44100).astype(np.float32)
        time_series_data = mock_audio_analyzer._extract_time_series_features(y, 0)
        # Should handle error gracefully and return empty list
        assert isinstance(time_series_data, list)
    
    def test_extract_time_series_additional_features(self, mock_audio_analyzer):
        """Test extraction of additional time series features"""
        sample_rate = 44100
        duration = 10.0
        y = np.random.random(int(sample_rate * duration)).astype(np.float32)
        
        time_series_data = mock_audio_analyzer._extract_time_series_features(y, sample_rate)
        
        # Check for optional additional features
        first_point = time_series_data[0]
        
        # These features should be present if extraction succeeds
        if 'zero_crossing_rate' in first_point:
            assert 0 <= first_point['zero_crossing_rate'] <= 1.0
        
        if 'spectral_bandwidth' in first_point:
            assert first_point['spectral_bandwidth'] > 0
    
    @patch('backend.core_engine.audio_analysis.analyzer.librosa')
    def test_analyze_track_with_time_series(self, mock_librosa, mock_audio_analyzer):
        """Test that analyze_track includes time series features"""
        # Setup mocks
        sample_rate = 44100
        duration = 10.0
        mock_audio_data = np.random.random(int(sample_rate * duration)).astype(np.float32)
        
        mock_librosa.load.return_value = (mock_audio_data, sample_rate)
        mock_librosa.effects.trim.return_value = (mock_audio_data, None)
        mock_librosa.util.normalize.return_value = mock_audio_data
        
        # Mock feature extractor
        mock_audio_analyzer.feature_extractor.extract_all_features.return_value = {
            'bpm': 128.0,
            'energy': 0.75,
            'valence': 0.65,
            'danceability': 0.8
        }
        
        mock_audio_analyzer.feature_extractor.extract_metadata.return_value = {
            'title': 'Test Track',
            'artist': 'Test Artist',
            'duration': duration,
            'file_size': 1024,
            'filename': 'test.mp3',
            'extension': '.mp3'
        }
        
        mock_audio_analyzer.feature_extractor.estimate_key.return_value = ('C Major', '8B')
        
        # Mock mood classifier
        mock_audio_analyzer.mood_classifier.classify_mood.return_value = ('euphoric', 0.85, {'euphoric': 0.85})
        
        # Mock database operations
        mock_audio_analyzer.database_manager.is_cached.return_value = False
        mock_audio_analyzer.database_manager.save_to_cache.return_value = True
        
        # Analyze track
        with patch('os.path.exists', return_value=True):
            result = mock_audio_analyzer.analyze_track('/test/path/test.mp3')
        
        # Check that result includes time series features
        assert 'time_series_features' in result
        assert isinstance(result['time_series_features'], list)
        assert len(result['time_series_features']) == 2  # 10 seconds / 5 second windows
        
        # Check time series data structure
        first_ts_point = result['time_series_features'][0]
        assert 'timestamp' in first_ts_point
        assert 'energy_value' in first_ts_point
        assert 'brightness_value' in first_ts_point
        assert first_ts_point['timestamp'] == 0.0
    
    def test_time_series_integration_with_database(self, mock_audio_analyzer):
        """Test that time series data is properly integrated with database storage"""
        # Create sample time series data
        time_series_data = [
            {'timestamp': 0.0, 'energy_value': 0.6, 'brightness_value': 0.5},
            {'timestamp': 5.0, 'energy_value': 0.7, 'brightness_value': 0.6},
            {'timestamp': 10.0, 'energy_value': 0.8, 'brightness_value': 0.7}
        ]
        
        # Mock database manager to verify correct calls
        mock_db_manager = mock_audio_analyzer.database_manager
        mock_db_manager.add_track.return_value = 1
        mock_db_manager.update_global_features.return_value = True
        mock_db_manager.add_time_series_data.return_value = True
        
        # Create analysis result with time series data
        analysis_result = {
            'file_path': '/test/path/test.mp3',
            'filename': 'test.mp3',
            'features': {'bpm': 128.0, 'energy': 0.75},
            'metadata': {'filename': 'test.mp3', 'duration': 180.0, 'file_size': 1024, 'extension': '.mp3'},
            'time_series_features': time_series_data
        }
        
        # Call save_analysis_results
        mock_audio_analyzer.save_analysis_results('/test/path/test.mp3', analysis_result)
        
        # Verify database manager was called correctly
        mock_db_manager.save_to_cache.assert_called_once_with('/test/path/test.mp3', analysis_result)
    
    def test_time_series_performance(self, mock_audio_analyzer):
        """Test performance with larger audio files"""
        # Create 5 minute audio file
        sample_rate = 44100
        duration = 300.0  # 5 minutes
        y = np.random.random(int(sample_rate * duration)).astype(np.float32)
        
        import time
        start_time = time.time()
        
        time_series_data = mock_audio_analyzer._extract_time_series_features(y, sample_rate, window_seconds=5.0)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process reasonably quickly (less than 5 seconds for 5 minute audio)
        assert processing_time < 5.0
        
        # Should have correct number of windows
        expected_windows = int(duration // 5.0)
        assert len(time_series_data) == expected_windows
        
        # All timestamps should be valid
        timestamps = [point['timestamp'] for point in time_series_data]
        assert timestamps == sorted(timestamps)  # Should be in ascending order
        assert timestamps[0] == 0.0
        assert timestamps[-1] == (expected_windows - 1) * 5.0