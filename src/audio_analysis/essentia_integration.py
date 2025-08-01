import importlib.util
import importlib
import numpy as np
import logging
from typing import Optional, Tuple, Dict, List, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EssentiaIntegration:
    """Integration class for Essentia audio analysis with fallback to librosa"""
    
    def __init__(self):
        self.essentia = None
        self.essentia_streaming = None
        self.is_available = False
        self.streaming_available = False
        self.algorithm_config = {}
        
        self._initialize_essentia()
    
    def _initialize_essentia(self):
        """Initialize Essentia if available, otherwise set up fallback"""
        try:
            # Check if Essentia is available
            essentia_spec = importlib.util.find_spec('essentia')
            if essentia_spec is None:
                logger.warning("Essentia not found. Using librosa fallback.")
                self.is_available = False
                return
            
            # Import Essentia standard algorithms
            self.essentia = importlib.import_module('essentia.standard')
            
            # Try to import streaming algorithms
            try:
                self.essentia_streaming = importlib.import_module('essentia.streaming')
                self.streaming_available = True
                logger.info("Essentia streaming mode available")
            except ImportError:
                logger.warning("Essentia streaming mode not available")
                self.streaming_available = False
            
            self.is_available = True
            logger.info("Essentia successfully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Essentia: {e}")
            self.is_available = False
            self.essentia = None
            self.essentia_streaming = None
    
    def configure_algorithms(self, config: Dict[str, Any]):
        """Configure Essentia algorithm parameters"""
        self.algorithm_config = config
        logger.info(f"Algorithm configuration updated: {config}")
    
    def extract_bpm(self, audio_data: np.ndarray, sample_rate: int) -> Optional[float]:
        """Extract BPM using Essentia with fallback to librosa"""
        if not self.is_available:
            return self._extract_bpm_fallback(audio_data, sample_rate)
        
        try:
            return self._extract_bpm_essentia(audio_data, sample_rate)
        except Exception as e:
            logger.warning(f"Essentia BPM extraction failed: {e}. Falling back to librosa.")
            return self._extract_bpm_fallback(audio_data, sample_rate)
    
    def _extract_bpm_essentia(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Extract BPM using Essentia BeatTracker"""
        # Get algorithm configuration
        beat_config = self.algorithm_config.get('beat_tracker', {})
        
        # Initialize BeatTracker with configuration
        beat_tracker = self.essentia.BeatTrackerMultiFeature(
            maxTempo=beat_config.get('maxTempo', 200),
            minTempo=beat_config.get('minTempo', 60)
        )
        
        # Extract beats and BPM
        beats, bpm = beat_tracker(audio_data)
        
        # Return the most confident BPM
        if len(bpm) > 0:
            return float(bpm[0])
        else:
            raise ValueError("No BPM detected")
    
    def _extract_bpm_fallback(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Fallback BPM extraction using librosa"""
        try:
            import librosa
            tempo = librosa.beat.tempo(y=audio_data, sr=sample_rate)
            return float(tempo[0]) if len(tempo) > 0 else 120.0
        except ImportError:
            logger.error("Neither Essentia nor librosa available for BPM extraction")
            return 120.0  # Default BPM
        except Exception as e:
            logger.error(f"Librosa BPM extraction failed: {e}")
            return 120.0
    
    def extract_key(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[str, str, float]:
        """Extract key using Essentia with fallback to librosa"""
        if not self.is_available:
            return self._extract_key_fallback(audio_data, sample_rate)
        
        try:
            return self._extract_key_essentia(audio_data, sample_rate)
        except Exception as e:
            logger.warning(f"Essentia key extraction failed: {e}. Falling back to librosa.")
            return self._extract_key_fallback(audio_data, sample_rate)
    
    def _extract_key_essentia(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[str, str, float]:
        """Extract key using Essentia KeyExtractor"""
        # Get algorithm configuration
        key_config = self.algorithm_config.get('key_extractor', {})
        
        # Initialize KeyExtractor with configuration
        key_extractor = self.essentia.KeyExtractor(
            profileType=key_config.get('profileType', 'temperley')
        )
        
        # Extract key, scale, and strength
        key, scale, strength = key_extractor(audio_data)
        
        return key, scale, float(strength)
    
    def _extract_key_fallback(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[str, str, float]:
        """Fallback key extraction using librosa"""
        try:
            import librosa
            
            # Extract chroma features
            chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sample_rate)
            
            # Simple key estimation based on chroma
            chroma_mean = np.mean(chroma, axis=1)
            
            # Key templates (simplified)
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            # Find the key with maximum correlation
            key_idx = np.argmax(chroma_mean)
            key = key_names[key_idx]
            
            # Simple major/minor detection (placeholder)
            scale = 'major' if chroma_mean[key_idx] > np.mean(chroma_mean) else 'minor'
            confidence = float(chroma_mean[key_idx] / np.sum(chroma_mean))
            
            return key, scale, confidence
            
        except ImportError:
            logger.error("Neither Essentia nor librosa available for key extraction")
            return 'C', 'major', 0.0
        except Exception as e:
            logger.error(f"Librosa key extraction failed: {e}")
            return 'C', 'major', 0.0
    
    def extract_all_features(self, audio_file: str) -> Optional[Dict[str, Any]]:
        """Extract comprehensive features using Essentia MusicExtractor"""
        if not self.is_available:
            return self._extract_all_features_fallback(audio_file)
        
        try:
            return self._extract_all_features_essentia(audio_file)
        except Exception as e:
            logger.warning(f"Essentia feature extraction failed: {e}. Falling back to librosa.")
            return self._extract_all_features_fallback(audio_file)
    
    def _extract_all_features_essentia(self, audio_file: str) -> Dict[str, Any]:
        """Extract all features using Essentia MusicExtractor"""
        # Initialize MusicExtractor
        music_extractor = self.essentia.MusicExtractor(
            lowlevelStats=['mean', 'stdev'],
            rhythmStats=['mean', 'stdev'],
            tonalStats=['mean', 'stdev']
        )
        
        # Extract features
        features, features_frames = music_extractor(audio_file)
        
        # Convert to our standard format
        result = {
            'filename': audio_file,
            'bpm': float(features.get('rhythm.bpm', 120.0)),
            'key': features.get('tonal.key_key', 'C'),
            'scale': features.get('tonal.key_scale', 'major'),
            'key_strength': float(features.get('tonal.key_strength', 0.0)),
            'spectral_centroid': float(features.get('lowlevel.spectral_centroid.mean', 2000.0)),
            'spectral_rolloff': float(features.get('lowlevel.spectral_rolloff.mean', 4000.0)),
            'zero_crossing_rate': float(features.get('lowlevel.zerocrossingrate.mean', 0.1)),
            'energy_level': float(features.get('rhythm.beats_loudness.mean', 0.5)),
            'mfcc': features.get('lowlevel.mfcc.mean', [0.0] * 13),
            'chroma': features.get('tonal.chroma.mean', [0.0] * 12),
            'tempo_confidence': float(features.get('rhythm.bpm_confidence', 0.0)),
            'danceability': float(features.get('rhythm.danceability', 0.5)),
            'valence': float(features.get('mood.happy', 0.5)),
            'arousal': float(features.get('mood.aggressive', 0.5))
        }
        
        return result
    
    def _extract_all_features_fallback(self, audio_file: str) -> Dict[str, Any]:
        """Fallback feature extraction using librosa"""
        try:
            import librosa
            import soundfile as sf
            
            # Load audio file
            audio_data, sample_rate = librosa.load(audio_file, sr=None)
            
            # Extract basic features using librosa
            tempo = librosa.beat.tempo(y=audio_data, sr=sample_rate)
            chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sample_rate)
            mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)
            zcr = librosa.feature.zero_crossing_rate(audio_data)
            rms = librosa.feature.rms(y=audio_data)
            
            # Simple key estimation
            chroma_mean = np.mean(chroma, axis=1)
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key_idx = np.argmax(chroma_mean)
            key = key_names[key_idx]
            scale = 'major' if chroma_mean[key_idx] > np.mean(chroma_mean) else 'minor'
            
            result = {
                'filename': audio_file,
                'bpm': float(tempo[0]) if len(tempo) > 0 else 120.0,
                'key': key,
                'scale': scale,
                'key_strength': float(chroma_mean[key_idx] / np.sum(chroma_mean)),
                'spectral_centroid': float(np.mean(spectral_centroid)),
                'spectral_rolloff': float(np.mean(spectral_rolloff)),
                'zero_crossing_rate': float(np.mean(zcr)),
                'energy_level': float(np.mean(rms)),
                'mfcc': np.mean(mfcc, axis=1).tolist(),
                'chroma': chroma_mean.tolist(),
                'tempo_confidence': 0.8,  # Placeholder
                'danceability': float(np.mean(rms) * 2),  # Simple approximation
                'valence': 0.5,  # Placeholder
                'arousal': float(np.mean(spectral_centroid) / 4000.0)  # Simple approximation
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Fallback feature extraction failed: {e}")
            return None
    
    def batch_extract_features(self, audio_files: List[str]) -> List[Dict[str, Any]]:
        """Extract features from multiple audio files"""
        results = []
        
        for audio_file in audio_files:
            try:
                features = self.extract_all_features(audio_file)
                if features:
                    results.append(features)
                else:
                    logger.warning(f"Failed to extract features from {audio_file}")
            except Exception as e:
                logger.error(f"Error processing {audio_file}: {e}")
        
        return results
    
    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get information about available algorithms"""
        info = {
            'essentia_available': self.is_available,
            'streaming_available': self.streaming_available,
            'fallback_method': 'librosa'
        }
        
        if self.is_available:
            try:
                # Get Essentia version if available
                essentia_info = importlib.import_module('essentia')
                info['essentia_version'] = getattr(essentia_info, '__version__', 'unknown')
            except:
                info['essentia_version'] = 'unknown'
        
        return info
    
    def benchmark_performance(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Benchmark performance of different analysis methods"""
        import time
        
        results = {}
        
        # Benchmark Essentia if available
        if self.is_available:
            try:
                start_time = time.time()
                self._extract_bpm_essentia(audio_data, sample_rate)
                results['essentia_bpm_time'] = time.time() - start_time
                
                start_time = time.time()
                self._extract_key_essentia(audio_data, sample_rate)
                results['essentia_key_time'] = time.time() - start_time
            except Exception as e:
                logger.warning(f"Essentia benchmark failed: {e}")
                results['essentia_bpm_time'] = float('inf')
                results['essentia_key_time'] = float('inf')
        
        # Benchmark librosa fallback
        try:
            start_time = time.time()
            self._extract_bpm_fallback(audio_data, sample_rate)
            results['librosa_bpm_time'] = time.time() - start_time
            
            start_time = time.time()
            self._extract_key_fallback(audio_data, sample_rate)
            results['librosa_key_time'] = time.time() - start_time
        except Exception as e:
            logger.warning(f"Librosa benchmark failed: {e}")
            results['librosa_bpm_time'] = float('inf')
            results['librosa_key_time'] = float('inf')
        
        return results

# Global instance for easy access
_essentia_integration = None

def get_essentia_integration() -> EssentiaIntegration:
    """Get global Essentia integration instance"""
    global _essentia_integration
    if _essentia_integration is None:
        _essentia_integration = EssentiaIntegration()
    return _essentia_integration

# Convenience functions
def is_essentia_available() -> bool:
    """Check if Essentia is available"""
    return get_essentia_integration().is_available

def extract_bpm_with_essentia(audio_data: np.ndarray, sample_rate: int) -> Optional[float]:
    """Extract BPM using Essentia with fallback"""
    return get_essentia_integration().extract_bpm(audio_data, sample_rate)

def extract_key_with_essentia(audio_data: np.ndarray, sample_rate: int) -> Tuple[str, str, float]:
    """Extract key using Essentia with fallback"""
    return get_essentia_integration().extract_key(audio_data, sample_rate)