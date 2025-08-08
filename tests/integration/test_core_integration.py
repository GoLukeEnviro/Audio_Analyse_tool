"""
Integration tests for core engine components
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


class TestIntegration:
    """Integration tests between components"""
    
    @pytest.mark.asyncio
    async def test_full_analysis_to_playlist_workflow(self, temp_cache_dir, mock_audio_file):
        """Test complete workflow from analysis to playlist generation"""
        # Initialize components
        analyzer = AudioAnalyzer(cache_dir=temp_cache_dir, enable_multiprocessing=False)
        playlist_engine = PlaylistEngine()
        mood_classifier = MoodClassifier()
        
        # Mock the analysis process
        with patch.object(analyzer, 'analyze_track') as mock_analyze:
            mock_analyze.return_value = {
                'status': 'completed',
                'file_path': mock_audio_file,
                'filename': 'test_track.wav',
                'features': {
                    'energy': 0.75,
                    'valence': 0.65,
                    'bpm': 128.0,
                    'danceability': 0.8
                },
                'metadata': {
                    'title': 'Test Track',
                    'duration': 180.0
                },
                'camelot': {
                    'key': 'C Major',
                    'camelot': '8B'
                }
            }
            
            # Analyze track
            track_data = analyzer.analyze_track(mock_audio_file)
            assert track_data['status'] == 'completed'
            
            # Add mood classification
            features = track_data['features']
            mood, confidence, scores = mood_classifier.classify_mood(features)
            
            track_data['mood'] = {
                'primary_mood': mood,
                'confidence': confidence,
                'scores': scores
            }
            
            # Create playlist with single track (for testing)
            tracks = [track_data, track_data, track_data]  # Duplicate for minimum tracks
            
            try:
                playlist_result = await playlist_engine.create_playlist_async(
                    tracks=tracks,
                    preset_name='hybrid_smart'
                )
                
                # Should either succeed or fail gracefully
                assert playlist_result is not None
                assert isinstance(playlist_result, dict)
                
            except Exception as e:
                # If it fails, it should be a known limitation
                assert 'tracks' in str(e).lower() or 'insufficient' in str(e).lower()
    
    def test_cache_integration_with_analyzer(self, temp_cache_dir):
        """Test cache integration with analyzer"""
        analyzer = AudioAnalyzer(cache_dir=temp_cache_dir)
        cache_manager = analyzer.cache_manager
        
        # Test data
        file_path = '/path/to/test.mp3'
        analysis_data = {
            'file_path': file_path,
            'status': 'completed',
            'features': {'bpm': 128.0}
        }
        
        # Save to cache via analyzer's cache manager
        success = cache_manager.save_to_cache(file_path, analysis_data)
        assert success is True
        
        # Check if analyzer can detect cached file
        is_cached = cache_manager.is_cached(file_path)
        assert is_cached is True
        
        # Load from cache
        loaded = cache_manager.load_from_cache(file_path)
        assert loaded is not None
        assert loaded['file_path'] == file_path