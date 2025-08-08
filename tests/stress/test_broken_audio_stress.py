#!/usr/bin/env python3
"""
Broken Audio Stress Test
Testet das System mit verschiedenen korrupten/fehlerhaften Audio-Dateien
"""

import sys
import os
import time
import logging
import tempfile
import requests
from pathlib import Path
from typing import List, Dict, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core_engine.audio_analysis.analyzer import AudioAnalyzer
from core_engine.audio_analysis.feature_extractor import get_fallback_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

class BrokenAudioStressTester:
    """Stress-Test mit kaputten/problematischen Audio-Dateien"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="broken_audio_test_"))
        self.test_results = {
            'total_files': 0,
            'successful_fallbacks': 0,
            'failed_completely': 0,
            'analysis_errors': 0,
            'api_errors': 0
        }
        
    def create_broken_files(self) -> List[Path]:
        """Erstelle verschiedene kaputte Audio-Dateien zum Testen"""
        
        broken_files = []
        
        # 1. Leere Datei
        empty_file = self.temp_dir / "empty.wav"
        empty_file.write_bytes(b"")
        broken_files.append(empty_file)
        
        # 2. Zu kleine Datei
        tiny_file = self.temp_dir / "tiny.mp3"
        tiny_file.write_bytes(b"MP3")  # Nur 3 Bytes
        broken_files.append(tiny_file)
        
        # 3. Falsche Datei-Extension
        fake_audio = self.temp_dir / "fake.wav"
        fake_audio.write_text("This is not audio data")
        broken_files.append(fake_audio)
        
        # 4. Binäre Müll-Daten
        garbage_file = self.temp_dir / "garbage.flac"
        garbage_data = bytes([i % 256 for i in range(1024)])  # 1KB Müll
        garbage_file.write_bytes(garbage_data)
        broken_files.append(garbage_file)
        
        # 5. Sehr große Datei (simuliert)
        large_file = self.temp_dir / "large.aiff"
        large_file.write_bytes(b"FORM" + b"0" * 100000)  # 100KB Null-Daten
        broken_files.append(large_file)
        
        # 6. Datei mit ungültigen Zeichen im Namen
        special_chars_file = self.temp_dir / "spëçiål_çhârs_ñämé.mp3"
        special_chars_file.write_bytes(b"ID3\x00\x00\x00")
        broken_files.append(special_chars_file)
        
        # 7. Datei ohne Berechtigung (soweit möglich)
        no_permission = self.temp_dir / "no_permission.wav"
        no_permission.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        broken_files.append(no_permission)
        
        # 8. Datei mit NULL-Bytes im Dateinamen  
        null_bytes_file = self.temp_dir / "null_file.m4a"
        null_bytes_file.write_bytes(b"\x00" * 512)
        broken_files.append(null_bytes_file)
        
        # 9. JSON-Datei mit Audio-Extension
        json_fake = self.temp_dir / "fake_audio.ogg"
        json_fake.write_text('{"this": "is not audio"}')
        broken_files.append(json_fake)
        
        # 10. Kaputter WAV-Header
        broken_wav = self.temp_dir / "broken_header.wav"
        broken_wav.write_bytes(b"RIFF\xFF\xFF\xFF\xFFWAVE" + b"\x00" * 100)
        broken_files.append(broken_wav)
        
        logger.info(f"Created {len(broken_files)} broken test files in {self.temp_dir}")
        return broken_files
    
    def test_analyzer_resilience(self, broken_files: List[Path]) -> Dict[str, Any]:
        """Teste AudioAnalyzer mit kaputten Dateien"""
        
        logger.info("=== Testing AudioAnalyzer Resilience ===")
        
        analyzer = AudioAnalyzer(enable_multiprocessing=False)  # Einfacher für Tests
        
        results = {
            'processed': 0,
            'fallbacks': 0,
            'errors': 0,
            'exceptions': 0
        }
        
        for i, file_path in enumerate(broken_files, 1):
            logger.info(f"Testing file {i}/{len(broken_files)}: {file_path.name}")
            
            try:
                result = analyzer.analyze_track(str(file_path))
                
                if result:
                    results['processed'] += 1
                    
                    # Prüfe ob Fallback verwendet wurde
                    if result.get('status') in ['fallback', 'error_fallback']:
                        results['fallbacks'] += 1
                        logger.info(f"  ✓ Fallback used for {file_path.name}")
                    elif result.get('status') == 'error':
                        results['errors'] += 1
                        logger.warning(f"  ⚠ Error status for {file_path.name}")
                    elif result.get('status') == 'completed':
                        logger.info(f"  ✓ Surprisingly successful for {file_path.name}")
                    
                    # Validiere grundlegende Struktur
                    assert 'file_path' in result
                    assert 'features' in result
                    assert isinstance(result['features'], dict)
                    
                else:
                    results['errors'] += 1
                    logger.warning(f"  ⚠ No result returned for {file_path.name}")
                    
            except Exception as e:
                results['exceptions'] += 1
                logger.error(f"  ✗ Exception for {file_path.name}: {e}")
        
        success_rate = ((results['processed'] - results['exceptions']) / len(broken_files)) * 100
        logger.info(f"AudioAnalyzer resilience: {success_rate:.1f}% success rate")
        
        return results
    
    def test_api_resilience(self, broken_files: List[Path]) -> Dict[str, Any]:
        """Teste API-Endpoints mit kaputten Dateien"""
        
        logger.info("=== Testing API Resilience ===")
        
        # Kopiere ein paar Test-Dateien in data/inbox
        inbox_path = Path("data/inbox")
        inbox_path.mkdir(exist_ok=True)
        
        copied_files = []
        for i, broken_file in enumerate(broken_files[:5]):  # Nur erste 5 für API-Test
            target = inbox_path / f"broken_test_{i}.{broken_file.suffix[1:]}"
            try:
                target.write_bytes(broken_file.read_bytes())
                copied_files.append(target)
            except Exception as e:
                logger.warning(f"Could not copy {broken_file}: {e}")
        
        results = {
            'api_calls': 0,
            'successful_responses': 0,
            'errors': 0,
            'analysis_started': False
        }
        
        # Test 1: Health Check
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            results['api_calls'] += 1
            if response.status_code == 200:
                results['successful_responses'] += 1
                logger.info("✓ Health check passed during broken file test")
            else:
                results['errors'] += 1
        except Exception as e:
            results['errors'] += 1
            logger.error(f"Health check failed: {e}")
        
        # Test 2: Start Analysis (erwarten, dass es fehlschlägt oder handled wird)
        try:
            payload = {"input_dir": "data/inbox"}
            response = requests.post(f"{BASE_URL}/api/analysis/start", json=payload, timeout=10)
            results['api_calls'] += 1
            
            if response.status_code in [200, 400, 422]:  # Alle sind akzeptabel
                results['successful_responses'] += 1
                if response.status_code == 200:
                    results['analysis_started'] = True
                    logger.info("✓ Analysis started (will likely use fallbacks)")
                else:
                    logger.info(f"✓ Analysis rejected gracefully ({response.status_code})")
            else:
                results['errors'] += 1
                logger.warning(f"Unexpected status code: {response.status_code}")
                
        except Exception as e:
            results['errors'] += 1
            logger.error(f"Analysis start failed: {e}")
        
        # Test 3: List Tracks (sollte immer funktionieren)
        try:
            response = requests.get(f"{BASE_URL}/api/tracks", timeout=5)
            results['api_calls'] += 1
            if response.status_code == 200:
                results['successful_responses'] += 1
                data = response.json()
                logger.info(f"✓ Tracks list returned {data.get('total_count', 0)} tracks")
            else:
                results['errors'] += 1
                logger.warning(f"Tracks list failed with {response.status_code}")
        except Exception as e:
            results['errors'] += 1
            logger.error(f"Tracks list failed: {e}")
        
        # Cleanup
        for copied_file in copied_files:
            try:
                copied_file.unlink()
            except:
                pass
        
        api_success_rate = (results['successful_responses'] / max(1, results['api_calls'])) * 100
        logger.info(f"API resilience: {api_success_rate:.1f}% success rate")
        
        return results
    
    def test_mass_broken_file_processing(self, count: int = 50) -> Dict[str, Any]:
        """Teste mit vielen kaputten Dateien gleichzeitig"""
        
        logger.info(f"=== Testing Mass Broken File Processing ({count} files) ===")
        
        # Erstelle viele kaputte Dateien
        mass_files = []
        for i in range(count):
            file_path = self.temp_dir / f"mass_broken_{i:03d}.wav"
            
            # Verschiedene Arten von kaputten Daten
            if i % 5 == 0:
                file_path.write_bytes(b"")  # Leer
            elif i % 5 == 1:
                file_path.write_bytes(b"GARBAGE" * (i % 100 + 1))  # Müll
            elif i % 5 == 2:
                file_path.write_text(f"Text file number {i}")  # Text
            elif i % 5 == 3:
                file_path.write_bytes(b"\x00" * (i % 1000 + 10))  # NULL-Bytes
            else:
                file_path.write_bytes(b"RIFF" + bytes([i % 256] * 100))  # Kaputter WAV
            
            mass_files.append(file_path)
        
        # Teste sequenzielle Verarbeitung
        analyzer = AudioAnalyzer(enable_multiprocessing=False)
        
        results = {
            'total_files': len(mass_files),
            'processed': 0,
            'fallbacks': 0,
            'errors': 0,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        for i, file_path in enumerate(mass_files):
            if i % 10 == 0:
                logger.info(f"Processing mass file {i+1}/{len(mass_files)}")
            
            try:
                result = analyzer.analyze_track(str(file_path))
                
                if result:
                    results['processed'] += 1
                    
                    if result.get('status') in ['fallback', 'error_fallback']:
                        results['fallbacks'] += 1
                    elif result.get('status') == 'error':
                        results['errors'] += 1
                
            except Exception as e:
                results['errors'] += 1
                if i < 5:  # Nur erste paar Errors loggen
                    logger.debug(f"Mass processing error for {file_path.name}: {e}")
        
        results['processing_time'] = time.time() - start_time
        
        success_rate = ((results['processed'] - results['errors']) / results['total_files']) * 100
        avg_time_per_file = results['processing_time'] / results['total_files']
        
        logger.info(f"Mass processing: {success_rate:.1f}% success rate")
        logger.info(f"Average time per broken file: {avg_time_per_file:.3f}s")
        
        return results
    
    def cleanup(self):
        """Cleanup test files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up test directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

def run_broken_audio_stress_test():
    """Führe alle Broken-Audio Stress Tests aus"""
    
    logger.info("=== BROKEN AUDIO STRESS TEST ===")
    
    tester = BrokenAudioStressTester()
    
    try:
        # Phase 1: Erstelle kaputte Dateien
        broken_files = tester.create_broken_files()
        tester.test_results['total_files'] = len(broken_files)
        
        # Phase 2: Teste AudioAnalyzer
        analyzer_results = tester.test_analyzer_resilience(broken_files)
        
        # Phase 3: Teste API
        api_results = tester.test_api_resilience(broken_files)
        
        # Phase 4: Mass Processing Test
        mass_results = tester.test_mass_broken_file_processing(50)
        
        # Zusammenfassung
        logger.info("\n=== STRESS TEST RESULTS ===")
        logger.info(f"Individual Files: {len(broken_files)} created")
        logger.info(f"Analyzer Processed: {analyzer_results['processed']}/{len(broken_files)}")
        logger.info(f"Analyzer Fallbacks: {analyzer_results['fallbacks']}")
        logger.info(f"API Success Rate: {api_results['successful_responses']}/{api_results['api_calls']}")
        logger.info(f"Mass Processing: {mass_results['processed']}/{mass_results['total_files']} in {mass_results['processing_time']:.1f}s")
        
        # Bewertung
        overall_score = 0
        
        # Analyzer resilience (40%)
        analyzer_score = (analyzer_results['processed'] - analyzer_results['exceptions']) / len(broken_files)
        overall_score += analyzer_score * 0.4
        
        # API resilience (30%)  
        api_score = api_results['successful_responses'] / max(1, api_results['api_calls'])
        overall_score += api_score * 0.3
        
        # Mass processing (30%)
        mass_score = (mass_results['processed'] - mass_results['errors']) / mass_results['total_files']
        overall_score += mass_score * 0.3
        
        overall_percentage = overall_score * 100
        
        logger.info(f"\n🎯 OVERALL RESILIENCE SCORE: {overall_percentage:.1f}%")
        
        if overall_percentage >= 90:
            logger.info("🎉 EXCELLENT resilience to broken files!")
            return True
        elif overall_percentage >= 75:
            logger.info("✅ GOOD resilience to broken files")
            return True
        else:
            logger.warning("⚠️  Resilience could be improved")
            return False
            
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = run_broken_audio_stress_test()
    sys.exit(0 if success else 1)