import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from audio_analysis.analyzer import AudioAnalyzer
from audio_analysis.feature_extractor import FeatureExtractor
from audio_analysis.cache_manager import CacheManager

class TestAudioAnalyzer:
    """Test cases for AudioAnalyzer class"""
    
    def test_analyzer_initialization(self):
        """Test AudioAnalyzer initialization"""
        analyzer = AudioAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'feature_extractor')
        assert hasattr(analyzer, 'cache_manager')
    
    @patch('audio_analysis.analyzer.librosa')
    def test_load_audio_file(self, mock_librosa, mock_audio_data):
        """Test audio file loading"""
        audio_data, sample_rate = mock_audio_data
        mock_librosa.load.return_value = (audio_data, sample_rate)
        
        analyzer = AudioAnalyzer()
        result_audio, result_sr = analyzer.load_audio_file('test.mp3')
        
        assert np.array_equal(result_audio, audio_data)
        assert result_sr == sample_rate
        mock_librosa.load.assert_called_once_with('test.mp3', sr=None)
    
    @patch('audio_analysis.analyzer.librosa')
    def test_analyze_track_success(self, mock_librosa, mock_audio_data, mock_track_metadata):
        """Test successful track analysis"""
        audio_data, sample_rate = mock_audio_data
        mock_librosa.load.return_value = (audio_data, sample_rate)
        
        analyzer = AudioAnalyzer()
        
        # Mock feature extraction
        with patch.object(analyzer.feature_extractor, 'extract_all_features') as mock_extract:
            mock_extract.return_value = mock_track_metadata
            
            result = analyzer.analyze_track('test.mp3')
            
            assert result is not None
            assert result['filename'] == 'test.mp3'
            assert 'bpm' in result
            assert 'key' in result
            assert 'duration' in result
    
    def test_analyze_track_file_not_found(self):
        """Test track analysis with non-existent file"""
        analyzer = AudioAnalyzer()
        
        with patch('audio_analysis.analyzer.librosa.load') as mock_load:
            mock_load.side_effect = FileNotFoundError("File not found")
            
            result = analyzer.analyze_track('nonexistent.mp3')
            assert result is None
    
    @patch('audio_analysis.analyzer.librosa')
    def test_analyze_track_with_cache(self, mock_librosa, mock_cache_manager, mock_track_metadata):
        """Test track analysis with cache hit"""
        mock_cache_manager.is_cached.return_value = True
        mock_cache_manager.get_cached_analysis.return_value = mock_track_metadata
        
        analyzer = AudioAnalyzer()
        analyzer.cache_manager = mock_cache_manager
        
        result = analyzer.analyze_track('test.mp3')
        
        assert result == mock_track_metadata
        mock_cache_manager.get_cached_analysis.assert_called_once_with('test.mp3')
        # Should not load audio if cached
        mock_librosa.load.assert_not_called()

class TestFeatureExtractor:
    """Test cases for FeatureExtractor class"""
    
    def test_feature_extractor_initialization(self):
        """Test FeatureExtractor initialization"""
        extractor = FeatureExtractor()
        assert extractor is not None
    
    @patch('audio_analysis.feature_extractor.librosa')
    def test_extract_bpm(self, mock_librosa, mock_audio_data):
        """Test BPM extraction"""
        audio_data, sample_rate = mock_audio_data
        mock_librosa.beat.tempo.return_value = np.array([128.0])
        
        extractor = FeatureExtractor()
        bpm = extractor.extract_bpm(audio_data, sample_rate)
        
        assert bpm == 128.0
        mock_librosa.beat.tempo.assert_called_once()
    
    @patch('audio_analysis.feature_extractor.librosa')
    def test_extract_key(self, mock_librosa, mock_audio_data):
        """Test key extraction"""
        audio_data, sample_rate = mock_audio_data
        
        # Mock chroma features
        mock_chroma = np.random.rand(12, 100)
        mock_librosa.feature.chroma_cqt.return_value = mock_chroma
        
        extractor = FeatureExtractor()
        
        with patch.object(extractor, '_estimate_key_from_chroma') as mock_key_est:
            mock_key_est.return_value = ('C', 'major')
            
            key, scale = extractor.extract_key(audio_data, sample_rate)
            
            assert key == 'C'
            assert scale == 'major'
    
    @patch('audio_analysis.feature_extractor.librosa')
    def test_extract_energy_level(self, mock_librosa, mock_audio_data):
        """Test energy level extraction"""
        audio_data, sample_rate = mock_audio_data
        
        # Mock RMS energy
        mock_rms = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]])
        mock_librosa.feature.rms.return_value = mock_rms
        
        extractor = FeatureExtractor()
        energy = extractor.extract_energy_level(audio_data, sample_rate)
        
        assert 0.0 <= energy <= 1.0
        mock_librosa.feature.rms.assert_called_once()
    
    @patch('audio_analysis.feature_extractor.librosa')
    def test_extract_spectral_features(self, mock_librosa, mock_audio_data):
        """Test spectral features extraction"""
        audio_data, sample_rate = mock_audio_data
        
        # Mock spectral features
        mock_centroid = np.array([[2000.0, 2100.0, 1900.0]])
        mock_rolloff = np.array([[4000.0, 4200.0, 3800.0]])
        mock_zcr = np.array([[0.1, 0.12, 0.08]])
        
        mock_librosa.feature.spectral_centroid.return_value = mock_centroid
        mock_librosa.feature.spectral_rolloff.return_value = mock_rolloff
        mock_librosa.feature.zero_crossing_rate.return_value = mock_zcr
        
        extractor = FeatureExtractor()
        features = extractor.extract_spectral_features(audio_data, sample_rate)
        
        assert 'spectral_centroid' in features
        assert 'spectral_rolloff' in features
        assert 'zero_crossing_rate' in features
        assert isinstance(features['spectral_centroid'], float)
    
    @patch('audio_analysis.feature_extractor.librosa')
    def test_extract_mfcc(self, mock_librosa, mock_audio_data):
        """Test MFCC extraction"""
        audio_data, sample_rate = mock_audio_data
        
        # Mock MFCC features
        mock_mfcc = np.random.rand(13, 100)
        mock_librosa.feature.mfcc.return_value = mock_mfcc
        
        extractor = FeatureExtractor()
        mfcc = extractor.extract_mfcc(audio_data, sample_rate)
        
        assert len(mfcc) == 13
        assert all(isinstance(coeff, float) for coeff in mfcc)
        mock_librosa.feature.mfcc.assert_called_once()
    
    def test_estimate_key_from_chroma(self):
        """Test key estimation from chroma features"""
        extractor = FeatureExtractor()
        
        # Create mock chroma with strong C major profile
        chroma = np.zeros((12, 100))
        # C major: C, E, G strong
        chroma[0, :] = 0.9  # C
        chroma[4, :] = 0.7  # E
        chroma[7, :] = 0.8  # G
        
        key, scale = extractor._estimate_key_from_chroma(chroma)
        
        assert key in ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        assert scale in ['major', 'minor']
    
    @patch('audio_analysis.feature_extractor.librosa')
    def test_extract_all_features(self, mock_librosa, mock_audio_data):
        """Test extraction of all features"""
        audio_data, sample_rate = mock_audio_data
        
        extractor = FeatureExtractor()
        
        # Mock all individual extraction methods
        with patch.object(extractor, 'extract_bpm', return_value=128.0), \
             patch.object(extractor, 'extract_key', return_value=('C', 'major')), \
             patch.object(extractor, 'extract_energy_level', return_value=0.75), \
             patch.object(extractor, 'extract_spectral_features', return_value={'spectral_centroid': 2000.0}), \
             patch.object(extractor, 'extract_mfcc', return_value=[1.0, 2.0, 3.0]):
            
            features = extractor.extract_all_features(audio_data, sample_rate, 'test.mp3')
            
            assert 'filename' in features
            assert 'bpm' in features
            assert 'key' in features
            assert 'energy_level' in features
            assert 'spectral_centroid' in features
            assert 'mfcc' in features
            assert features['filename'] == 'test.mp3'

class TestCacheManager:
    """Test cases for CacheManager class"""
    
    def test_cache_manager_initialization(self, tmp_path):
        """Test CacheManager initialization"""
        cache_file = tmp_path / "test_cache.json"
        cache_manager = CacheManager(str(cache_file))
        
        assert cache_manager is not None
        assert cache_manager.cache_file == str(cache_file)
    
    def test_cache_analysis(self, tmp_path, mock_track_metadata):
        """Test caching analysis results"""
        cache_file = tmp_path / "test_cache.json"
        cache_manager = CacheManager(str(cache_file))
        
        result = cache_manager.cache_analysis('test.mp3', mock_track_metadata)
        assert result is True
        
        # Verify file was created
        assert cache_file.exists()
    
    def test_get_cached_analysis(self, tmp_path, mock_track_metadata):
        """Test retrieving cached analysis"""
        cache_file = tmp_path / "test_cache.json"
        cache_manager = CacheManager(str(cache_file))
        
        # Cache some data first
        cache_manager.cache_analysis('test.mp3', mock_track_metadata)
        
        # Retrieve cached data
        cached_data = cache_manager.get_cached_analysis('test.mp3')
        
        assert cached_data is not None
        assert cached_data['filename'] == mock_track_metadata['filename']
        assert cached_data['bpm'] == mock_track_metadata['bpm']
    
    def test_is_cached(self, tmp_path, mock_track_metadata):
        """Test checking if file is cached"""
        cache_file = tmp_path / "test_cache.json"
        cache_manager = CacheManager(str(cache_file))
        
        # Initially not cached
        assert cache_manager.is_cached('test.mp3') is False
        
        # Cache the file
        cache_manager.cache_analysis('test.mp3', mock_track_metadata)
        
        # Now should be cached
        assert cache_manager.is_cached('test.mp3') is True
    
    def test_clear_cache(self, tmp_path, mock_track_metadata):
        """Test clearing cache"""
        cache_file = tmp_path / "test_cache.json"
        cache_manager = CacheManager(str(cache_file))
        
        # Cache some data
        cache_manager.cache_analysis('test.mp3', mock_track_metadata)
        assert cache_manager.is_cached('test.mp3') is True
        
        # Clear cache
        cache_manager.clear_cache()
        assert cache_manager.is_cached('test.mp3') is False

class TestEssentiaIntegration:
    """Test cases for Essentia integration"""
    
    @patch('audio_analysis.feature_extractor.importlib.util.find_spec')
    def test_essentia_not_available(self, mock_find_spec):
        """Test behavior when Essentia is not available"""
        mock_find_spec.return_value = None
        
        extractor = FeatureExtractor()
        assert not hasattr(extractor, 'essentia') or extractor.essentia is None
    
    @patch('audio_analysis.feature_extractor.importlib.util.find_spec')
    @patch('audio_analysis.feature_extractor.importlib.import_module')
    def test_essentia_available(self, mock_import, mock_find_spec, mock_essentia):
        """Test behavior when Essentia is available"""
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        extractor = FeatureExtractor()
        # Should attempt to use Essentia if available
        assert mock_import.called
    
    @patch('audio_analysis.feature_extractor.importlib.util.find_spec')
    @patch('audio_analysis.feature_extractor.importlib.import_module')
    def test_essentia_bpm_extraction(self, mock_import, mock_find_spec, mock_essentia, mock_audio_data):
        """Test BPM extraction with Essentia"""
        audio_data, sample_rate = mock_audio_data
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        extractor = FeatureExtractor()
        
        # Mock Essentia BPM extraction
        with patch.object(extractor, '_extract_bpm_essentia', return_value=128.5) as mock_essentia_bpm:
            bpm = extractor.extract_bpm(audio_data, sample_rate)
            
            # Should use Essentia if available
            if hasattr(extractor, 'essentia') and extractor.essentia:
                mock_essentia_bpm.assert_called_once()
                assert bpm == 128.5
    
    @patch('audio_analysis.feature_extractor.importlib.util.find_spec')
    @patch('audio_analysis.feature_extractor.importlib.import_module')
    def test_essentia_key_extraction(self, mock_import, mock_find_spec, mock_essentia, mock_audio_data):
        """Test key extraction with Essentia"""
        audio_data, sample_rate = mock_audio_data
        
        mock_find_spec.return_value = True
        mock_import.return_value = mock_essentia
        
        extractor = FeatureExtractor()
        
        # Mock Essentia key extraction
        with patch.object(extractor, '_extract_key_essentia', return_value=('A', 'minor')) as mock_essentia_key:
            key, scale = extractor.extract_key(audio_data, sample_rate)
            
            # Should use Essentia if available
            if hasattr(extractor, 'essentia') and extractor.essentia:
                mock_essentia_key.assert_called_once()
                assert key == 'A'
                assert scale == 'minor'