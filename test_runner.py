#!/usr/bin/env python3
"""Test runner for DJ Audio Analysis Tool"""

import sys
import os
import logging
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_essentia_integration():
    """Test Essentia integration with fallback"""
    print("\n=== Testing Essentia Integration ===")
    
    try:
        from audio_analysis.essentia_integration import EssentiaIntegration
        
        # Initialize Essentia integration
        ei = EssentiaIntegration()
        
        # Check availability
        print(f"Essentia available: {ei.is_available}")
        print(f"Streaming available: {ei.streaming_available}")
        
        # Get algorithm info
        info = ei.get_algorithm_info()
        print(f"Algorithm info: {info}")
        
        # Test with mock audio data
        sample_rate = 44100
        duration = 5  # 5 seconds
        audio_data = np.random.randn(sample_rate * duration).astype(np.float32)
        
        # Test BPM extraction
        print("\nTesting BPM extraction...")
        bpm = ei.extract_bpm(audio_data, sample_rate)
        print(f"Extracted BPM: {bpm}")
        
        # Test key extraction
        print("\nTesting key extraction...")
        key, scale, strength = ei.extract_key(audio_data, sample_rate)
        print(f"Extracted key: {key} {scale} (strength: {strength:.3f})")
        
        # Test performance benchmark
        print("\nTesting performance benchmark...")
        benchmark = ei.benchmark_performance(audio_data, sample_rate)
        print(f"Performance benchmark: {benchmark}")
        
        print("✅ Essentia integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Essentia integration test failed: {e}")
        return False

def test_feature_extractor():
    """Test feature extractor with Essentia integration"""
    print("\n=== Testing Feature Extractor ===")
    
    try:
        from audio_analysis.feature_extractor import FeatureExtractor
        
        # Initialize feature extractor
        fe = FeatureExtractor()
        
        # Test with mock audio data
        sample_rate = 44100
        duration = 10  # 10 seconds
        audio_data = np.random.randn(sample_rate * duration).astype(np.float32)
        
        # Test individual feature extraction
        print("\nTesting individual features...")
        
        # Test BPM
        bpm = fe.extract_bpm(audio_data, sample_rate)
        print(f"BPM: {bpm}")
        
        # Test key
        key = fe.extract_key(audio_data, sample_rate)
        print(f"Key: {key}")
        
        # Test energy level
        energy = fe.extract_energy_level(audio_data)
        print(f"Energy level: {energy:.3f}")
        
        # Test spectral features
        spectral = fe.extract_spectral_features(audio_data, sample_rate)
        print(f"Spectral features: {list(spectral.keys())}")
        
        # Test MFCC features
        mfcc = fe.extract_mfcc_features(audio_data, sample_rate)
        print(f"MFCC features shape: {np.array(mfcc['mfcc']).shape}")
        
        print("✅ Feature extractor test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Feature extractor test failed: {e}")
        return False

def test_cache_manager():
    """Test cache manager functionality"""
    print("\n=== Testing Cache Manager ===")
    
    try:
        from audio_analysis.cache_manager import CacheManager
        import tempfile
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mp3', delete=False) as temp_file:
            temp_file.write("dummy audio content")
            test_file_path = temp_file.name
        
        # Initialize cache manager
        cache_dir = Path("test_cache")
        cm = CacheManager(cache_dir)
        
        # Test cache operations
        test_data = {
            'bpm': 128.0,
            'key': 'C major',
            'energy_level': 0.75
        }
        
        # Test storing
        print("Testing cache storage...")
        success = cm.save_to_cache(test_file_path, test_data)
        print(f"Stored data for file: {test_file_path} - Success: {success}")
        
        # Test retrieving
        print("Testing cache retrieval...")
        retrieved = cm.load_from_cache(test_file_path)
        print(f"Retrieved data: {retrieved is not None}")
        
        # Test cache hit
        is_cached = cm.is_cached(test_file_path)
        print(f"Is cached: {is_cached}")
        
        # Test cache info
        info = cm.get_cache_info()
        print(f"Cache info: files={info['total_files']}, size={info['total_size_bytes']}")
        
        # Test alias methods
        print("Testing alias methods...")
        alias_success = cm.store(test_file_path, test_data)
        alias_retrieved = cm.get(test_file_path)
        print(f"Alias methods work: store={alias_success}, get={alias_retrieved is not None}")
        
        # Cleanup
        cm.clear_cache()
        os.unlink(test_file_path)  # Remove temp file
        
        # Try to remove cache directory
        try:
            import shutil
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
        except:
            pass  # Ignore cleanup errors
        
        print("✅ Cache manager test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Cache manager test failed: {e}")
        return False

def test_imports():
    """Test all critical imports"""
    print("\n=== Testing Critical Imports ===")
    
    imports_to_test = [
        ('audio_analysis.essentia_integration', 'EssentiaIntegration'),
        ('audio_analysis.feature_extractor', 'FeatureExtractor'),
        ('audio_analysis.cache_manager', 'CacheManager'),
    ]
    
    success_count = 0
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ Successfully imported {class_name} from {module_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to import {class_name} from {module_name}: {e}")
    
    print(f"\nImport test results: {success_count}/{len(imports_to_test)} successful")
    return success_count == len(imports_to_test)

def main():
    """Run all tests"""
    print("🎵 DJ Audio Analysis Tool - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Essentia Integration", test_essentia_integration),
        ("Feature Extractor", test_feature_extractor),
        ("Cache Manager", test_cache_manager),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The system is ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())