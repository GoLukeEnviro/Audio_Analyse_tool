import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import importlib.util

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestEssentiaIntegration:
    """Test cases for Essentia integration with fallback mechanisms"""
    
    def test_essentia_availability_check(self):
        """Test checking if Essentia is available"""
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        # Should handle both available and unavailable cases
        assert hasattr(integration, 'is_available')
        assert isinstance(integration.is_available, bool)
    
    @patch('importlib.util.find_spec')
    def test_essentia_not_available_fallback(self, mock_find_spec):
        """Test fallback behavior when Essentia is not available"""
        mock_find_spec.return_value = None
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        assert integration.is_available is False
        assert integration.essentia is None
    
    @patch('importlib.util.find_spec')
    @patch('importlib.import_module')
    def test_essentia_available_initialization(self, mock_import, mock_find_spec):
        """Test initialization when Essentia is available"""
        # Mock Essentia module
        mock_essentia = Mock()
        mock_essentia.standard = Mock()
        mock_essentia.streaming = Mock()
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        assert integration.is_available is True
        assert integration.essentia is not None
        mock_import.assert_called_with('essentia.standard')
    
    @patch('importlib.util.find_spec')
    @patch('importlib.import_module')
    def test_essentia_bpm_extraction(self, mock_import, mock_find_spec):
        """Test BPM extraction using Essentia"""
        # Mock Essentia module and algorithms
        mock_essentia = Mock()
        mock_beat_tracker = Mock()
        mock_beat_tracker.return_value = ([1.0, 2.0, 3.0], [128.5])
        mock_essentia.BeatTrackerMultiFeature = Mock(return_value=mock_beat_tracker)
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        # Test BPM extraction
        audio_data = np.random.rand(44100 * 3).astype(np.float32)
        sample_rate = 44100
        
        bpm = integration.extract_bpm(audio_data, sample_rate)
        
        assert bpm == 128.5
        mock_essentia.BeatTrackerMultiFeature.assert_called_once()
    
    @patch('importlib.util.find_spec')
    @patch('importlib.import_module')
    def test_essentia_key_extraction(self, mock_import, mock_find_spec):
        """Test key extraction using Essentia"""
        # Mock Essentia module and algorithms
        mock_essentia = Mock()
        mock_key_extractor = Mock()
        mock_key_extractor.return_value = ('A', 'minor', 0.95)
        mock_essentia.KeyExtractor = Mock(return_value=mock_key_extractor)
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        # Test key extraction
        audio_data = np.random.rand(44100 * 3).astype(np.float32)
        sample_rate = 44100
        
        key, scale, confidence = integration.extract_key(audio_data, sample_rate)
        
        assert key == 'A'
        assert scale == 'minor'
        assert confidence == 0.95
        mock_essentia.KeyExtractor.assert_called_once()
    
    @patch('importlib.util.find_spec')
    @patch('importlib.import_module')
    def test_essentia_music_extractor(self, mock_import, mock_find_spec):
        """Test comprehensive music feature extraction using Essentia"""
        # Mock Essentia module and MusicExtractor
        mock_essentia = Mock()
        
        # Mock features dictionary
        mock_features = {
            'rhythm.bpm': 128.0,
            'tonal.key_key': 'C',
            'tonal.key_scale': 'major',
            'lowlevel.spectral_centroid.mean': 2000.0,
            'lowlevel.spectral_rolloff.mean': 4000.0,
            'lowlevel.mfcc.mean': np.random.rand(13).tolist(),
            'rhythm.beats_loudness.mean': 0.75
        }
        
        mock_music_extractor = Mock()
        mock_music_extractor.return_value = (mock_features, None)
        mock_essentia.MusicExtractor = Mock(return_value=mock_music_extractor)
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        # Test comprehensive feature extraction
        audio_file = 'test_track.mp3'
        features = integration.extract_all_features(audio_file)
        
        assert features is not None
        assert 'bpm' in features
        assert 'key' in features
        assert 'spectral_centroid' in features
        assert features['bpm'] == 128.0
        assert features['key'] == 'C'
    
    def test_essentia_fallback_to_librosa(self):
        """Test fallback to librosa when Essentia fails"""
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        # Create integration without Essentia
        integration = EssentiaIntegration()
        integration.is_available = False
        integration.essentia = None
        
        audio_data = np.random.rand(44100 * 3).astype(np.float32)
        sample_rate = 44100
        
        with patch('audio_analysis.essentia_integration.librosa') as mock_librosa:
            mock_librosa.beat.tempo.return_value = np.array([130.0])
            
            bpm = integration.extract_bpm_fallback(audio_data, sample_rate)
            
            assert bpm == 130.0
            mock_librosa.beat.tempo.assert_called_once()
    
    @patch('importlib.util.find_spec')
    @patch('importlib.import_module')
    def test_essentia_error_handling(self, mock_import, mock_find_spec):
        """Test error handling in Essentia operations"""
        # Mock Essentia module that raises errors
        mock_essentia = Mock()
        mock_beat_tracker = Mock()
        mock_beat_tracker.side_effect = Exception("Essentia processing error")
        mock_essentia.BeatTrackerMultiFeature = Mock(return_value=mock_beat_tracker)
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        audio_data = np.random.rand(44100 * 3).astype(np.float32)
        sample_rate = 44100
        
        # Should handle error gracefully and return None or fallback
        with patch.object(integration, 'extract_bpm_fallback', return_value=128.0) as mock_fallback:
            bpm = integration.extract_bpm(audio_data, sample_rate)
            
            # Should fallback to librosa
            mock_fallback.assert_called_once()
            assert bpm == 128.0
    
    @patch('importlib.util.find_spec')
    @patch('importlib.import_module')
    def test_essentia_streaming_mode(self, mock_import, mock_find_spec):
        """Test Essentia streaming mode for real-time processing"""
        # Mock Essentia streaming module
        mock_essentia_streaming = Mock()
        mock_essentia_standard = Mock()
        
        def mock_import_side_effect(module_name):
            if module_name == 'essentia.standard':
                return mock_essentia_standard
            elif module_name == 'essentia.streaming':
                return mock_essentia_streaming
            return Mock()
        
        mock_find_spec.return_value = True
        mock_import.side_effect = mock_import_side_effect
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        # Test streaming mode availability
        assert hasattr(integration, 'streaming_available')
    
    def test_essentia_algorithm_configuration(self):
        """Test configuration of Essentia algorithms"""
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        # Test algorithm parameter configuration
        config = {
            'beat_tracker': {
                'maxTempo': 200,
                'minTempo': 60
            },
            'key_extractor': {
                'profileType': 'temperley'
            }
        }
        
        integration.configure_algorithms(config)
        
        assert integration.algorithm_config == config
    
    @patch('importlib.util.find_spec')
    @patch('importlib.import_module')
    def test_essentia_batch_processing(self, mock_import, mock_find_spec):
        """Test batch processing with Essentia"""
        # Mock Essentia module
        mock_essentia = Mock()
        mock_music_extractor = Mock()
        
        # Mock different results for different files
        def mock_extract_side_effect(filename):
            if 'track1' in filename:
                return ({'rhythm.bpm': 128.0, 'tonal.key_key': 'C'}, None)
            elif 'track2' in filename:
                return ({'rhythm.bpm': 130.0, 'tonal.key_key': 'G'}, None)
            else:
                return ({'rhythm.bpm': 132.0, 'tonal.key_key': 'D'}, None)
        
        mock_music_extractor.side_effect = mock_extract_side_effect
        mock_essentia.MusicExtractor = Mock(return_value=mock_music_extractor)
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        # Test batch processing
        audio_files = ['track1.mp3', 'track2.mp3', 'track3.mp3']
        results = integration.batch_extract_features(audio_files)
        
        assert len(results) == 3
        assert results[0]['bpm'] == 128.0
        assert results[1]['bpm'] == 130.0
        assert results[2]['bpm'] == 132.0
    
    def test_essentia_performance_comparison(self):
        """Test performance comparison between Essentia and librosa"""
        import time
        
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        integration = EssentiaIntegration()
        
        audio_data = np.random.rand(44100 * 10).astype(np.float32)  # 10 seconds
        sample_rate = 44100
        
        # Time Essentia processing (if available)
        if integration.is_available:
            start_time = time.time()
            try:
                bpm_essentia = integration.extract_bpm(audio_data, sample_rate)
                essentia_time = time.time() - start_time
            except:
                essentia_time = float('inf')
        else:
            essentia_time = float('inf')
        
        # Time librosa processing
        start_time = time.time()
        bpm_librosa = integration.extract_bpm_fallback(audio_data, sample_rate)
        librosa_time = time.time() - start_time
        
        # Record performance metrics
        performance_metrics = {
            'essentia_time': essentia_time,
            'librosa_time': librosa_time,
            'essentia_available': integration.is_available
        }
        
        assert isinstance(performance_metrics, dict)
        assert 'essentia_time' in performance_metrics
        assert 'librosa_time' in performance_metrics

class TestEssentiaFeatureExtractorIntegration:
    """Test integration of Essentia with the main FeatureExtractor"""
    
    @patch('audio_analysis.feature_extractor.EssentiaIntegration')
    def test_feature_extractor_with_essentia(self, mock_essentia_integration):
        """Test FeatureExtractor using Essentia when available"""
        from audio_analysis.feature_extractor import FeatureExtractor
        
        # Mock Essentia integration
        mock_integration = Mock()
        mock_integration.is_available = True
        mock_integration.extract_bpm.return_value = 128.5
        mock_integration.extract_key.return_value = ('A', 'minor', 0.95)
        mock_essentia_integration.return_value = mock_integration
        
        extractor = FeatureExtractor()
        
        audio_data = np.random.rand(44100 * 3).astype(np.float32)
        sample_rate = 44100
        
        # Test BPM extraction with Essentia
        bpm = extractor.extract_bpm(audio_data, sample_rate)
        assert bpm == 128.5
        
        # Test key extraction with Essentia
        key, scale = extractor.extract_key(audio_data, sample_rate)
        assert key == 'A'
        assert scale == 'minor'
    
    @patch('audio_analysis.feature_extractor.EssentiaIntegration')
    def test_feature_extractor_fallback_to_librosa(self, mock_essentia_integration):
        """Test FeatureExtractor falling back to librosa when Essentia unavailable"""
        from audio_analysis.feature_extractor import FeatureExtractor
        
        # Mock Essentia integration as unavailable
        mock_integration = Mock()
        mock_integration.is_available = False
        mock_essentia_integration.return_value = mock_integration
        
        extractor = FeatureExtractor()
        
        audio_data = np.random.rand(44100 * 3).astype(np.float32)
        sample_rate = 44100
        
        with patch('audio_analysis.feature_extractor.librosa') as mock_librosa:
            mock_librosa.beat.tempo.return_value = np.array([130.0])
            mock_librosa.feature.chroma_cqt.return_value = np.random.rand(12, 100)
            
            # Should use librosa fallback
            bpm = extractor.extract_bpm(audio_data, sample_rate)
            
            mock_librosa.beat.tempo.assert_called_once()
            assert isinstance(bpm, float)
    
    def test_feature_extractor_hybrid_approach(self):
        """Test hybrid approach using both Essentia and librosa"""
        from audio_analysis.feature_extractor import FeatureExtractor
        
        extractor = FeatureExtractor()
        
        # Test that extractor can handle both approaches
        assert hasattr(extractor, 'use_essentia')
        assert hasattr(extractor, 'use_librosa')
        
        # Should be able to switch between methods
        extractor.set_analysis_method('essentia')
        assert extractor.preferred_method == 'essentia'
        
        extractor.set_analysis_method('librosa')
        assert extractor.preferred_method == 'librosa'
        
        extractor.set_analysis_method('hybrid')
        assert extractor.preferred_method == 'hybrid'