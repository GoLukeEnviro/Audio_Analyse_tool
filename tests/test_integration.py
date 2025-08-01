import pytest
import os
import tempfile
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestFullWorkflowIntegration:
    """Integration tests for the complete DJ Audio Analysis workflow"""
    
    @pytest.fixture
    def temp_audio_files(self, tmp_path):
        """Create temporary audio files for testing"""
        audio_files = []
        for i in range(3):
            audio_file = tmp_path / f"test_track_{i}.mp3"
            # Create dummy audio file
            audio_file.write_bytes(b'dummy audio data')
            audio_files.append(str(audio_file))
        return audio_files
    
    @patch('audio_analysis.analyzer.librosa.load')
    @patch('audio_analysis.analyzer.librosa.beat.tempo')
    @patch('audio_analysis.analyzer.librosa.feature.chroma_cqt')
    def test_complete_analysis_to_export_workflow(self, mock_chroma, mock_tempo, mock_load, 
                                                 temp_audio_files, tmp_path):
        """Test complete workflow from audio analysis to playlist export"""
        from audio_analysis.analyzer import AudioAnalyzer
        from playlist_engine.generator import PlaylistGenerator
        from playlist_engine.rules import PlaylistRules
        from export_engine.exporter import PlaylistExporter
        
        # Mock audio analysis
        mock_load.return_value = (np.random.rand(44100 * 3), 44100)  # 3 seconds of audio
        mock_tempo.return_value = np.array([128.0, 130.0, 132.0])
        mock_chroma.return_value = np.random.rand(12, 100)
        
        # Step 1: Analyze audio files
        analyzer = AudioAnalyzer()
        analyzed_tracks = []
        
        for audio_file in temp_audio_files:
            track_data = analyzer.analyze_track(audio_file)
            if track_data:
                analyzed_tracks.append(track_data)
        
        assert len(analyzed_tracks) == len(temp_audio_files)
        assert all('bpm' in track for track in analyzed_tracks)
        assert all('key' in track for track in analyzed_tracks)
        
        # Step 2: Generate playlist
        generator = PlaylistGenerator()
        rules = PlaylistRules(
            bpm_range=(125, 135),
            key_compatibility=True,
            energy_progression='ascending'
        )
        
        playlist = generator.generate_playlist(analyzed_tracks, rules, target_length=3)
        
        assert len(playlist) <= 3
        assert all('filename' in track for track in playlist)
        
        # Step 3: Export playlist
        exporter = PlaylistExporter()
        output_file = tmp_path / "integration_test.m3u"
        
        export_result = exporter.export_playlist(playlist, str(output_file), 'm3u')
        
        assert export_result is True
        assert output_file.exists()
        
        # Verify export content
        content = output_file.read_text(encoding='utf-8')
        assert '#EXTM3U' in content
        assert any(track['filename'] in content for track in playlist)
    
    @patch('audio_analysis.analyzer.librosa.load')
    def test_batch_analysis_workflow(self, mock_load, temp_audio_files, tmp_path):
        """Test batch analysis of multiple audio files"""
        from audio_analysis.analyzer import AudioAnalyzer
        
        # Mock audio loading
        mock_load.return_value = (np.random.rand(44100 * 3), 44100)
        
        analyzer = AudioAnalyzer()
        
        # Batch analyze all files
        results = []
        for audio_file in temp_audio_files:
            result = analyzer.analyze_track(audio_file)
            if result:
                results.append(result)
        
        assert len(results) == len(temp_audio_files)
        
        # Verify all results have required fields
        required_fields = ['filename', 'bpm', 'key', 'energy_level', 'duration']
        for result in results:
            for field in required_fields:
                assert field in result
    
    def test_cache_integration(self, temp_audio_files, tmp_path):
        """Test cache integration across analysis sessions"""
        from audio_analysis.analyzer import AudioAnalyzer
        from audio_analysis.cache_manager import CacheManager
        
        cache_file = tmp_path / "test_cache.json"
        cache_manager = CacheManager(str(cache_file))
        
        # Mock analysis result
        mock_result = {
            'filename': temp_audio_files[0],
            'bpm': 128.0,
            'key': 'C',
            'energy_level': 0.75,
            'duration': 180.0
        }
        
        # Cache the result
        cache_manager.cache_analysis(temp_audio_files[0], mock_result)
        
        # Verify caching
        assert cache_manager.is_cached(temp_audio_files[0])
        cached_result = cache_manager.get_cached_analysis(temp_audio_files[0])
        assert cached_result == mock_result
        
        # Test cache persistence
        new_cache_manager = CacheManager(str(cache_file))
        assert new_cache_manager.is_cached(temp_audio_files[0])
    
    def test_playlist_generation_with_different_rules(self, mock_playlist_data):
        """Test playlist generation with various rule combinations"""
        from playlist_engine.generator import PlaylistGenerator
        from playlist_engine.rules import PlaylistRules
        
        generator = PlaylistGenerator()
        tracks = mock_playlist_data['tracks']
        
        # Test different rule combinations
        rule_sets = [
            PlaylistRules(bpm_range=(125, 135)),
            PlaylistRules(key_compatibility=True),
            PlaylistRules(energy_progression='ascending'),
            PlaylistRules(
                bpm_range=(120, 140),
                key_compatibility=True,
                energy_progression='stable'
            )
        ]
        
        for rules in rule_sets:
            playlist = generator.generate_playlist(tracks, rules, target_length=5)
            
            assert isinstance(playlist, list)
            assert len(playlist) <= 5
            assert all('filename' in track for track in playlist)
    
    def test_export_format_compatibility(self, mock_playlist_data, tmp_path):
        """Test export compatibility across different formats"""
        from export_engine.exporter import PlaylistExporter
        
        exporter = PlaylistExporter()
        tracks = mock_playlist_data['tracks']
        
        formats = ['m3u', 'csv', 'json']
        
        for format_type in formats:
            output_file = tmp_path / f"test_playlist.{format_type}"
            
            result = exporter.export_playlist(tracks, str(output_file), format_type)
            
            assert result is True
            assert output_file.exists()
            assert output_file.stat().st_size > 0
    
    @patch('audio_analysis.analyzer.librosa.load')
    def test_error_handling_integration(self, mock_load, tmp_path):
        """Test error handling across the complete workflow"""
        from audio_analysis.analyzer import AudioAnalyzer
        from playlist_engine.generator import PlaylistGenerator
        from playlist_engine.rules import PlaylistRules
        from export_engine.exporter import PlaylistExporter
        
        # Test with file that causes analysis error
        mock_load.side_effect = Exception("Audio loading failed")
        
        analyzer = AudioAnalyzer()
        result = analyzer.analyze_track("nonexistent.mp3")
        
        # Should handle error gracefully
        assert result is None
        
        # Test playlist generation with empty tracks
        generator = PlaylistGenerator()
        rules = PlaylistRules()
        
        empty_playlist = generator.generate_playlist([], rules, target_length=5)
        assert empty_playlist == []
        
        # Test export with empty playlist
        exporter = PlaylistExporter()
        output_file = tmp_path / "empty.m3u"
        
        export_result = exporter.export_playlist([], str(output_file), 'm3u')
        assert export_result is True

class TestPerformanceIntegration:
    """Integration tests for performance and scalability"""
    
    @patch('audio_analysis.analyzer.librosa.load')
    def test_large_batch_analysis_performance(self, mock_load):
        """Test performance with large batch of files"""
        from audio_analysis.analyzer import AudioAnalyzer
        import time
        
        # Mock audio loading
        mock_load.return_value = (np.random.rand(44100 * 3), 44100)
        
        analyzer = AudioAnalyzer()
        
        # Simulate large batch
        file_count = 50
        test_files = [f"test_track_{i}.mp3" for i in range(file_count)]
        
        start_time = time.time()
        
        results = []
        for file_path in test_files:
            result = analyzer.analyze_track(file_path)
            if result:
                results.append(result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert len(results) == file_count
        assert processing_time < 30.0  # Should complete within 30 seconds
        
        # Average processing time per file
        avg_time_per_file = processing_time / file_count
        assert avg_time_per_file < 1.0  # Less than 1 second per file
    
    def test_large_playlist_generation_performance(self):
        """Test performance with large track collections"""
        from playlist_engine.generator import PlaylistGenerator
        from playlist_engine.rules import PlaylistRules
        import time
        
        # Generate large track collection
        track_count = 1000
        large_track_collection = []
        
        for i in range(track_count):
            track = {
                'filename': f'track_{i}.mp3',
                'bpm': 120 + (i % 40),  # BPM range 120-160
                'key': ['C', 'D', 'E', 'F', 'G', 'A', 'B'][i % 7],
                'energy_level': (i % 100) / 100.0
            }
            large_track_collection.append(track)
        
        generator = PlaylistGenerator()
        rules = PlaylistRules(
            bpm_range=(125, 135),
            key_compatibility=True,
            energy_progression='ascending'
        )
        
        start_time = time.time()
        
        playlist = generator.generate_playlist(
            large_track_collection, 
            rules, 
            target_length=50
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert len(playlist) <= 50
        assert processing_time < 10.0  # Should complete within 10 seconds
    
    def test_memory_usage_integration(self, tmp_path):
        """Test memory usage during intensive operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Simulate memory-intensive operations
        from audio_analysis.analyzer import AudioAnalyzer
        from playlist_engine.generator import PlaylistGenerator
        
        analyzer = AudioAnalyzer()
        generator = PlaylistGenerator()
        
        # Create large data structures
        large_data = []
        for i in range(100):
            mock_track = {
                'filename': f'track_{i}.mp3',
                'bpm': 128.0,
                'key': 'C',
                'energy_level': 0.5,
                'mfcc': np.random.rand(13).tolist(),
                'chroma': np.random.rand(12).tolist(),
                'spectral_features': np.random.rand(100).tolist()
            }
            large_data.append(mock_track)
        
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory
        
        # Memory usage should be reasonable (less than 500MB increase)
        assert memory_increase < 500 * 1024 * 1024  # 500MB

class TestConcurrencyIntegration:
    """Integration tests for concurrent operations"""
    
    @patch('audio_analysis.analyzer.librosa.load')
    def test_concurrent_analysis(self, mock_load):
        """Test concurrent audio analysis"""
        import threading
        import time
        
        from audio_analysis.analyzer import AudioAnalyzer
        
        # Mock audio loading
        mock_load.return_value = (np.random.rand(44100 * 3), 44100)
        
        analyzer = AudioAnalyzer()
        results = []
        results_lock = threading.Lock()
        
        def analyze_worker(file_path):
            result = analyzer.analyze_track(file_path)
            with results_lock:
                results.append(result)
        
        # Start multiple analysis threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=analyze_worker, 
                args=(f'test_track_{i}.mp3',)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all analyses completed
        assert len(results) == 5
        assert all(result is not None for result in results)
    
    def test_concurrent_export(self, mock_playlist_data, tmp_path):
        """Test concurrent playlist export"""
        import threading
        
        from export_engine.exporter import PlaylistExporter
        
        exporter = PlaylistExporter()
        tracks = mock_playlist_data['tracks']
        export_results = []
        results_lock = threading.Lock()
        
        def export_worker(format_type, file_suffix):
            output_file = tmp_path / f"concurrent_{file_suffix}.{format_type}"
            result = exporter.export_playlist(tracks, str(output_file), format_type)
            with results_lock:
                export_results.append(result)
        
        # Start multiple export threads
        threads = []
        formats = ['m3u', 'csv', 'json']
        
        for i, format_type in enumerate(formats):
            thread = threading.Thread(
                target=export_worker, 
                args=(format_type, i)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all exports completed successfully
        assert len(export_results) == len(formats)
        assert all(result is True for result in export_results)

class TestDataIntegrityIntegration:
    """Integration tests for data integrity across the workflow"""
    
    @patch('audio_analysis.analyzer.librosa.load')
    @patch('audio_analysis.analyzer.librosa.beat.tempo')
    def test_data_consistency_through_workflow(self, mock_tempo, mock_load, tmp_path):
        """Test data consistency from analysis to export"""
        from audio_analysis.analyzer import AudioAnalyzer
        from playlist_engine.generator import PlaylistGenerator
        from playlist_engine.rules import PlaylistRules
        from export_engine.exporter import PlaylistExporter
        import json
        
        # Mock consistent analysis results
        mock_load.return_value = (np.random.rand(44100 * 3), 44100)
        mock_tempo.return_value = np.array([128.5])
        
        # Step 1: Analyze
        analyzer = AudioAnalyzer()
        original_track = analyzer.analyze_track('test.mp3')
        
        assert original_track is not None
        original_bpm = original_track['bpm']
        original_filename = original_track['filename']
        
        # Step 2: Generate playlist
        generator = PlaylistGenerator()
        rules = PlaylistRules()
        
        playlist = generator.generate_playlist([original_track], rules, target_length=1)
        
        assert len(playlist) == 1
        playlist_track = playlist[0]
        
        # Verify data consistency
        assert playlist_track['bpm'] == original_bpm
        assert playlist_track['filename'] == original_filename
        
        # Step 3: Export to JSON for detailed verification
        exporter = PlaylistExporter()
        output_file = tmp_path / "consistency_test.json"
        
        export_result = exporter.export_playlist(playlist, str(output_file), 'json')
        assert export_result is True
        
        # Step 4: Verify exported data
        with open(output_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        exported_track = exported_data['playlist']['tracks'][0]
        
        # Verify all data matches
        assert exported_track['bpm'] == original_bpm
        assert exported_track['filename'] == original_filename
    
    def test_unicode_handling_integration(self, tmp_path):
        """Test Unicode handling across the complete workflow"""
        from export_engine.exporter import PlaylistExporter
        
        # Create tracks with Unicode characters
        unicode_tracks = [
            {
                'filename': 'track_ñoño.mp3',
                'title': 'Canción Española',
                'artist': 'Artista Español',
                'bpm': 128.0,
                'key': 'C'
            },
            {
                'filename': 'track_中文.mp3',
                'title': '中文歌曲',
                'artist': '中文艺术家',
                'bpm': 130.0,
                'key': 'G'
            },
            {
                'filename': 'track_العربية.mp3',
                'title': 'أغنية عربية',
                'artist': 'فنان عربي',
                'bpm': 132.0,
                'key': 'D'
            }
        ]
        
        exporter = PlaylistExporter()
        
        # Test Unicode handling in different formats
        formats = ['m3u', 'csv', 'json']
        
        for format_type in formats:
            output_file = tmp_path / f"unicode_test.{format_type}"
            
            result = exporter.export_playlist(unicode_tracks, str(output_file), format_type)
            assert result is True
            assert output_file.exists()
            
            # Verify Unicode content is preserved
            content = output_file.read_text(encoding='utf-8')
            assert 'ñoño' in content
            assert '中文' in content
            assert 'العربية' in content
    
    def test_numerical_precision_integration(self, tmp_path):
        """Test numerical precision across the workflow"""
        from export_engine.exporter import PlaylistExporter
        import json
        
        # Create tracks with precise numerical values
        precise_tracks = [
            {
                'filename': 'precise_track.mp3',
                'bpm': 128.123456789,
                'energy_level': 0.123456789,
                'spectral_centroid': 2000.987654321,
                'tempo_confidence': 0.999999999
            }
        ]
        
        exporter = PlaylistExporter()
        output_file = tmp_path / "precision_test.json"
        
        result = exporter.export_playlist(precise_tracks, str(output_file), 'json')
        assert result is True
        
        # Verify numerical precision is maintained
        with open(output_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        exported_track = exported_data['playlist']['tracks'][0]
        
        # Check that precision is reasonably maintained
        assert abs(exported_track['bpm'] - 128.123456789) < 0.000001
        assert abs(exported_track['energy_level'] - 0.123456789) < 0.000001