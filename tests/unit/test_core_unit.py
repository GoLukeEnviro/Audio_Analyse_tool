"""
Unit test cases for core engine components
"""

import pytest
import asyncio
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import numpy as np

# Import core engine components

from backend.core_engine.audio_analysis.analyzer import AudioAnalyzer
from backend.core_engine.playlist_engine.playlist_engine import PlaylistEngine
from backend.core_engine.mood_classifier.mood_classifier import MoodClassifier
from backend.core_engine.data_management.cache_manager import CacheManager
from backend.core_engine.export.playlist_exporter import PlaylistExporter


class TestAudioAnalyzer:
    """Test AudioAnalyzer core functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create AudioAnalyzer instance for testing"""
        return AudioAnalyzer(enable_multiprocessing=False)
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer is not None
        assert hasattr(analyzer, 'cache_manager')
        assert hasattr(analyzer, 'supported_formats')
    
    def test_get_supported_formats(self, analyzer):
        """Test getting supported audio formats"""
        formats = analyzer.get_supported_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert '.mp3' in formats or '.wav' in formats
    
    @patch('librosa.load')
    @patch('librosa.feature.spectral_centroid')
    @patch('librosa.feature.zero_crossing_rate')
    @patch('librosa.beat.tempo')
    def test_analyze_track_success(self, mock_tempo, mock_zcr, mock_centroid, mock_load, analyzer, mock_audio_file):
        """Test successful track analysis"""
        # Mock librosa functions
        mock_load.return_value = (np.random.rand(44100), 44100)
        mock_centroid.return_value = np.array([[2000.0]])
        mock_zcr.return_value = np.array([[0.1]])
        mock_tempo.return_value = np.array([128.0])
        
        with patch.object(analyzer, '_extract_key_and_camelot', return_value=('C', 'major', '8B', 0.9)):
            result = analyzer.analyze_track(mock_audio_file)
            
            assert result is not None
            assert result['status'] == 'completed'
            assert 'features' in result
            assert 'metadata' in result
            assert 'camelot' in result
    
    def test_analyze_track_file_not_found(self, analyzer):
        """Test analysis with non-existent file"""
        result = analyzer.analyze_track('/nonexistent/file.mp3')
        
        assert result is not None
        assert result['status'] == 'error'
        assert len(result['errors']) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_batch_async(self, analyzer, mock_audio_file):
        """Test batch analysis"""
        file_paths = [mock_audio_file]
        
        with patch.object(analyzer, 'analyze_track') as mock_analyze:
            mock_analyze.return_value = {
                'status': 'completed',
                'file_path': mock_audio_file,
                'features': {'bpm': 128.0}
            }
            
            # Mock progress callback
            progress_callback = AsyncMock()
            
            results = await analyzer.analyze_batch_async(file_paths, progress_callback)
            
            assert len(results) == 1
            assert mock_audio_file in results
            progress_callback.assert_called()
    
    def test_get_analysis_stats(self, analyzer):
        """Test getting analysis statistics"""
        stats = analyzer.get_analysis_stats()
        
        assert isinstance(stats, dict)
        assert 'total_analyzed' in stats
        assert 'cache_hit_rate' in stats


class TestPlaylistEngine:
    """Test PlaylistEngine core functionality"""
    
    @pytest.fixture
    def playlist_engine(self, temp_cache_dir):
        """Create PlaylistEngine instance for testing"""
        # Use a temporary directory for presets to avoid NoneType error
        return PlaylistEngine(presets_dir=temp_cache_dir)
    
    def test_engine_initialization(self, playlist_engine):
        """Test playlist engine initialization"""
        assert playlist_engine is not None
        assert hasattr(playlist_engine, 'presets')
        assert hasattr(playlist_engine, 'algorithms')
    
    def test_get_all_presets(self, playlist_engine):
        """Test getting all presets"""
        presets = playlist_engine.get_all_presets()
        
        assert isinstance(presets, list)
        assert len(presets) > 0
        
        # Check preset structure
        preset = presets[0]
        assert 'name' in preset
        assert 'description' in preset
        assert 'algorithm' in preset
    
    def test_get_preset_details(self, playlist_engine):
        """Test getting preset details"""
        presets = playlist_engine.get_all_presets()
        if presets:
            preset_name = presets[0]['name']
            details = playlist_engine.get_preset_details(preset_name)
            
            assert details is not None
            assert details['name'] == preset_name
            assert 'rules' in details
    
    def test_get_preset_details_not_found(self, playlist_engine):
        """Test getting non-existent preset details"""
        details = playlist_engine.get_preset_details('nonexistent_preset')
        assert details is None
    
    def test_get_algorithm_info(self, playlist_engine):
        """Test getting algorithm information"""
        algorithms = playlist_engine.get_algorithm_info()
        
        assert isinstance(algorithms, list)
        assert len(algorithms) > 0
        
        # Check algorithm structure
        algorithm = algorithms[0]
        assert 'name' in algorithm
        assert 'description' in algorithm
    
    @pytest.mark.asyncio
    async def test_create_playlist_async(self, playlist_engine, sample_playlist_data):
        """Test async playlist creation"""
        tracks = sample_playlist_data['tracks']
        
        # Mock progress callback
        progress_callback = AsyncMock()
        
        result = await playlist_engine.create_playlist_async(
            tracks=tracks,
            preset_name='hybrid_smart',
            progress_callback=progress_callback
        )
        
        assert result is not None
        assert 'tracks' in result or 'error' in result
    
    def test_create_playlist_insufficient_tracks(self, playlist_engine):
        """Test playlist creation with insufficient tracks"""
        tracks = [{'file_path': 'track1.mp3'}]  # Only one track
        
        # This should handle gracefully (implementation dependent)
        try:
            result = playlist_engine.create_playlist(tracks)
            # If it returns a result, check for error indication
            if isinstance(result, dict) and 'error' in result:
                assert 'insufficient' in result['error'].lower()
        except ValueError as e:
            assert 'tracks' in str(e).lower()


class TestMoodClassifier:
    """Test MoodClassifier core functionality"""
    
    @pytest.fixture
    def mood_classifier(self):
        """Create MoodClassifier instance for testing"""
        return MoodClassifier()
    
    def test_classifier_initialization(self, mood_classifier):
        """Test mood classifier initialization"""
        assert mood_classifier is not None
        assert hasattr(MoodClassifier, 'MOOD_CATEGORIES')
    
    def test_get_mood_categories(self, mood_classifier):
        """Test getting mood categories"""
        categories = mood_classifier.get_mood_categories()
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert 'euphoric' in categories
        assert 'chill' in categories
    
    def test_classify_mood(self, mood_classifier):
        """Test mood classification with sample features"""
        features = {
            'energy': 0.8,
            'valence': 0.7,
            'danceability': 0.9,
            'bpm': 128.0,
            'loudness': -8.0
        }
        
        mood, confidence, scores = mood_classifier.classify_mood(features)
        
        assert mood is not None
        assert isinstance(mood, str)
        assert 0.0 <= confidence <= 1.0
        assert isinstance(scores, dict)
        assert len(scores) > 0
    
    def test_classify_mood_empty_features(self, mood_classifier):
        """Test mood classification with empty features"""
        features = {}
        
        mood, confidence, scores = mood_classifier.classify_mood(features)
        
        # Should handle gracefully, likely return neutral or default mood
        assert mood is not None
        assert confidence >= 0.0


class TestCacheManager:
    """Test CacheManager core functionality"""
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create CacheManager instance for testing"""
        return CacheManager(temp_cache_dir)
    
    def test_cache_manager_initialization(self, cache_manager):
        """Test cache manager initialization"""
        assert cache_manager is not None
        assert hasattr(cache_manager, 'cache_dir')
    
    def test_is_cached(self, cache_manager):
        """Test checking if file is cached"""
        result = cache_manager.is_cached('/path/to/nonexistent.mp3')
        assert result is False
    
    def test_save_and_load_cache(self, cache_manager, sample_track_analysis):
        """Test saving and loading from cache"""
        file_path = '/path/to/test_track.mp3'
        
        # Save to cache
        success = cache_manager.save_to_cache(file_path, sample_track_analysis)
        assert success is True
        
        # Check if cached
        is_cached = cache_manager.is_cached(file_path)
        assert is_cached is True
        
        # Load from cache
        loaded_data = cache_manager.load_from_cache(file_path)
        assert loaded_data is not None
        assert loaded_data['file_path'] == file_path
    
    def test_get_cache_stats(self, cache_manager):
        """Test getting cache statistics"""
        stats = cache_manager.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert 'total_files' in stats
        assert 'total_size_bytes' in stats
        assert 'cache_directory' in stats
    
    def test_get_cached_files(self, cache_manager):
        """Test getting list of cached files"""
        files = cache_manager.get_cached_files()
        assert isinstance(files, list)
    
    def test_cleanup_cache(self, cache_manager):
        """Test cache cleanup"""
        result = cache_manager.cleanup_cache(max_age_days=30, max_size_mb=1000)
        
        assert isinstance(result, dict)
        assert 'removed_files' in result
        assert 'freed_mb' in result
    
    def test_clear_cache(self, cache_manager):
        """Test clearing entire cache"""
        count = cache_manager.clear_cache()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_optimize_cache(self, cache_manager):
        """Test cache optimization"""
        result = cache_manager.optimize_cache()
        
        assert isinstance(result, dict)
        assert 'removed_entries' in result
        assert 'freed_mb' in result
    
    def test_optimize_cache(self, cache_manager):
        """Test cache optimization"""
        result = cache_manager.optimize_cache()
        
        assert isinstance(result, dict)
        assert 'removed_entries' in result
        assert 'freed_mb' in result


class TestPlaylistExporter:
    """Test PlaylistExporter core functionality"""
    
    @pytest.fixture
    def playlist_exporter(self, temp_export_dir):
        """Create PlaylistExporter instance for testing"""
        return PlaylistExporter(temp_export_dir)
    
    def test_exporter_initialization(self, playlist_exporter):
        """Test playlist exporter initialization"""
        assert playlist_exporter is not None
        assert hasattr(playlist_exporter, 'output_dir')
    
    def test_get_supported_formats(self, playlist_exporter):
        """Test getting supported export formats"""
        formats = playlist_exporter.get_supported_formats()
        
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'm3u' in formats
        assert 'json' in formats
    
    def test_export_playlist_m3u(self, playlist_exporter, sample_playlist_data):
        """Test exporting playlist as M3U"""
        tracks = sample_playlist_data['tracks']
        
        result = playlist_exporter.export_playlist(
            tracks=tracks,
            format_type='m3u',
            output_filename='test_playlist'
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert 'output_path' in result
            assert 'filename' in result
            assert 'track_count' in result
    
    def test_export_playlist_json(self, playlist_exporter, sample_playlist_data):
        """Test exporting playlist as JSON"""
        tracks = sample_playlist_data['tracks']
        
        result = playlist_exporter.export_playlist(
            tracks=tracks,
            format_type='json',
            output_filename='test_playlist',
            metadata=sample_playlist_data['metadata']
        )
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'success' in result
    
    def test_validate_tracks(self, playlist_exporter, sample_playlist_data):
        """Test track validation"""
        tracks = sample_playlist_data['tracks']
        
        result = playlist_exporter.validate_tracks(tracks)
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'track_count' in result
    
    def test_list_exports(self, playlist_exporter):
        """Test listing exported playlists"""
        exports = playlist_exporter.list_exports()
        assert isinstance(exports, list)
    
    def test_delete_export(self, playlist_exporter):
        """Test deleting export file"""
        # Test with non-existent file
        result = playlist_exporter.delete_export('nonexistent.m3u')
        assert result is False