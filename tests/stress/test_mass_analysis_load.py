#!/usr/bin/env python3
"""
Mass Analysis Load Test - Testet System mit 1000+ Dateien
Performance-, Memory- und Stabilität-Test für große Datenmengen
"""

import sys
import os
import time
import threading
import logging
import tempfile
import requests
import psutil
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core_engine.audio_analysis.analyzer import AudioAnalyzer
from core_engine.data_management.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

class MassAnalysisLoadTester:
    """Load-Test mit vielen simulierten Audio-Dateien"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="mass_analysis_test_"))
        self.process = psutil.Process()
        self.test_results = {
            'total_files': 0,
            'successful_analysis': 0,
            'fallback_analysis': 0,
            'failed_analysis': 0,
            'api_requests': 0,
            'api_successes': 0,
            'memory_usage': [],
            'cpu_usage': [],
            'processing_times': []
        }
        self.monitoring_active = False
        
    def create_test_files(self, count: int = 1000) -> List[Path]:
        """Erstelle viele Test-Dateien verschiedener Arten"""
        
        logger.info(f"Creating {count} test files...")
        
        test_files = []
        
        for i in range(count):
            file_path = self.temp_dir / f"test_audio_{i:04d}.wav"
            
            # Verschiedene Arten von Test-Dateien erstellen
            if i % 100 == 0:
                # Minimale gültige WAV-Datei alle 100 Dateien
                wav_data = self._create_minimal_wav()
                file_path.write_bytes(wav_data)
            elif i % 50 == 0:
                # Leere Dateien alle 50 Dateien
                file_path.write_bytes(b"")
            elif i % 25 == 0:
                # JSON-Fake alle 25 Dateien
                file_path.write_text(f'{{"test_file": {i}, "fake": true}}')
            elif i % 10 == 0:
                # Kleine kaputte Audio-Dateien alle 10 Dateien
                file_path.write_bytes(b"RIFF\x00\x00\x00\x00WAVE" + bytes([i % 256] * (i % 100 + 10)))
            else:
                # Normale kaputte/fake Dateien
                file_path.write_bytes(b"GARBAGE_DATA_" + bytes([i % 256] * (i % 50 + 1)))
            
            test_files.append(file_path)
            
            # Progress alle 200 Dateien
            if (i + 1) % 200 == 0:
                logger.info(f"Created {i + 1}/{count} test files...")
        
        logger.info(f"Created {len(test_files)} test files in {self.temp_dir}")
        return test_files
    
    def _create_minimal_wav(self) -> bytes:
        """Erstelle minimale gültige WAV-Datei"""
        import struct
        
        # Minimale WAV-Header für 1 Sekunde 16-bit mono 8kHz
        sample_rate = 8000
        num_samples = sample_rate  # 1 Sekunde
        
        # WAV Header
        header = b'RIFF'
        file_size = 36 + num_samples * 2  # 36 für Header + Daten
        header += struct.pack('<I', file_size)
        header += b'WAVE'
        header += b'fmt '
        header += struct.pack('<I', 16)  # Subchunk1Size
        header += struct.pack('<H', 1)   # AudioFormat (PCM)
        header += struct.pack('<H', 1)   # NumChannels (mono)
        header += struct.pack('<I', sample_rate)
        header += struct.pack('<I', sample_rate * 2)  # ByteRate
        header += struct.pack('<H', 2)   # BlockAlign
        header += struct.pack('<H', 16)  # BitsPerSample
        header += b'data'
        header += struct.pack('<I', num_samples * 2)
        
        # Dummy audio data (silence)
        audio_data = b'\x00\x00' * num_samples
        
        return header + audio_data
    
    def start_system_monitoring(self):
        """Starte System-Monitoring"""
        self.monitoring_active = True
        
        def monitor():
            while self.monitoring_active:
                try:
                    # Memory usage
                    memory_info = self.process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    self.test_results['memory_usage'].append(memory_mb)
                    
                    # CPU usage
                    cpu_percent = self.process.cpu_percent()
                    self.test_results['cpu_usage'].append(cpu_percent)
                    
                    time.sleep(1)
                except Exception as e:
                    logger.debug(f"Monitoring error: {e}")
        
        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()
        logger.info("System monitoring started")
    
    def stop_system_monitoring(self):
        """Stoppe System-Monitoring"""
        self.monitoring_active = False
        logger.info("System monitoring stopped")
    
    def test_sequential_analysis(self, test_files: List[Path], limit: int = 500) -> Dict[str, Any]:
        """Teste sequenzielle Analyse vieler Dateien"""
        
        logger.info(f"=== Sequential Analysis Test ({limit} files) ===")
        
        # Limitiere für praktischen Test
        files_to_test = test_files[:limit]
        
        analyzer = AudioAnalyzer(enable_multiprocessing=False)
        
        results = {
            'processed': 0,
            'successful': 0,
            'fallbacks': 0,
            'errors': 0,
            'total_time': 0,
            'avg_time_per_file': 0
        }
        
        start_time = time.time()
        
        for i, file_path in enumerate(files_to_test):
            file_start = time.time()
            
            try:
                result = analyzer.analyze_track(str(file_path))
                
                if result:
                    results['processed'] += 1
                    
                    if result.get('status') in ['fallback', 'error_fallback']:
                        results['fallbacks'] += 1
                    elif result.get('status') == 'completed':
                        results['successful'] += 1
                    elif result.get('status') == 'error':
                        results['errors'] += 1
                else:
                    results['errors'] += 1
                
            except Exception as e:
                results['errors'] += 1
                if i < 10:  # Log nur erste 10 Errors
                    logger.debug(f"Analysis error for {file_path.name}: {e}")
            
            file_time = time.time() - file_start
            self.test_results['processing_times'].append(file_time)
            
            # Progress alle 50 Dateien
            if (i + 1) % 50 == 0:
                logger.info(f"Processed {i + 1}/{len(files_to_test)} files...")
        
        results['total_time'] = time.time() - start_time
        results['avg_time_per_file'] = results['total_time'] / len(files_to_test)
        
        logger.info(f"Sequential analysis completed in {results['total_time']:.1f}s")
        logger.info(f"Success rate: {(results['processed'] / len(files_to_test)) * 100:.1f}%")
        
        return results
    
    def test_concurrent_analysis(self, test_files: List[Path], limit: int = 200, workers: int = 4) -> Dict[str, Any]:
        """Teste parallele Analyse mit ThreadPool"""
        
        logger.info(f"=== Concurrent Analysis Test ({limit} files, {workers} workers) ===")
        
        files_to_test = test_files[:limit]
        
        results = {
            'processed': 0,
            'successful': 0,
            'fallbacks': 0,
            'errors': 0,
            'total_time': 0,
            'worker_errors': 0
        }
        
        def analyze_file(file_path: Path) -> Dict[str, Any]:
            try:
                analyzer = AudioAnalyzer(enable_multiprocessing=False)
                result = analyzer.analyze_track(str(file_path))
                return {'file': file_path, 'result': result, 'error': None}
            except Exception as e:
                return {'file': file_path, 'result': None, 'error': str(e)}
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit alle Tasks
            futures = [executor.submit(analyze_file, file_path) for file_path in files_to_test]
            
            # Collect results
            for i, future in enumerate(futures):
                try:
                    analysis_result = future.result(timeout=30)
                    
                    if analysis_result['error']:
                        results['worker_errors'] += 1
                    elif analysis_result['result']:
                        results['processed'] += 1
                        
                        status = analysis_result['result'].get('status')
                        if status in ['fallback', 'error_fallback']:
                            results['fallbacks'] += 1
                        elif status == 'completed':
                            results['successful'] += 1
                        else:
                            results['errors'] += 1
                    else:
                        results['errors'] += 1
                    
                    # Progress
                    if (i + 1) % 25 == 0:
                        logger.info(f"Completed {i + 1}/{len(files_to_test)} concurrent analyses...")
                        
                except Exception as e:
                    results['worker_errors'] += 1
                    logger.debug(f"Worker future error: {e}")
        
        results['total_time'] = time.time() - start_time
        
        logger.info(f"Concurrent analysis completed in {results['total_time']:.1f}s")
        logger.info(f"Processing rate: {len(files_to_test) / results['total_time']:.1f} files/sec")
        
        return results
    
    def test_api_mass_load(self, count: int = 100) -> Dict[str, Any]:
        """Teste API unter Last mit vielen Requests"""
        
        logger.info(f"=== API Mass Load Test ({count} requests) ===")
        
        results = {
            'total_requests': count,
            'successful_requests': 0,
            'failed_requests': 0,
            'timeout_requests': 0,
            'avg_response_time': 0,
            'response_times': []
        }
        
        def make_request(request_id: int) -> Dict[str, Any]:
            try:
                start_time = time.time()
                
                # Verschiedene API-Calls testen
                if request_id % 4 == 0:
                    response = requests.get(f"{BASE_URL}/health", timeout=10)
                elif request_id % 4 == 1:
                    response = requests.get(f"{BASE_URL}/api/tracks?per_page=10", timeout=10)
                elif request_id % 4 == 2:
                    response = requests.get(f"{BASE_URL}/api/tracks/stats/overview", timeout=10)
                else:
                    response = requests.get(f"{BASE_URL}/health", timeout=10)
                
                response_time = time.time() - start_time
                
                return {
                    'success': response.status_code == 200,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'timeout': False
                }
                
            except requests.exceptions.Timeout:
                return {'success': False, 'timeout': True, 'response_time': 10.0}
            except Exception as e:
                return {'success': False, 'error': str(e), 'response_time': 0}
        
        # Sequenzielle API-Requests (um Server nicht zu überlasten)
        for i in range(count):
            request_result = make_request(i)
            
            if request_result.get('success'):
                results['successful_requests'] += 1
            elif request_result.get('timeout'):
                results['timeout_requests'] += 1
            else:
                results['failed_requests'] += 1
            
            results['response_times'].append(request_result.get('response_time', 0))
            
            # Progress
            if (i + 1) % 20 == 0:
                logger.info(f"Completed {i + 1}/{count} API requests...")
            
            # Kleine Pause um Server zu schonen
            time.sleep(0.1)
        
        if results['response_times']:
            results['avg_response_time'] = sum(results['response_times']) / len(results['response_times'])
        
        success_rate = (results['successful_requests'] / count) * 100
        logger.info(f"API success rate: {success_rate:.1f}%")
        
        return results
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generiere Performance-Bericht"""
        
        report = {
            'test_timestamp': time.time(),
            'test_duration': time.time(),
            'files_created': self.test_results['total_files'],
            'memory_stats': {},
            'cpu_stats': {},
            'processing_stats': {},
            'overall_score': 0
        }
        
        # Memory statistics
        if self.test_results['memory_usage']:
            memory_usage = self.test_results['memory_usage']
            report['memory_stats'] = {
                'peak_memory_mb': max(memory_usage),
                'avg_memory_mb': sum(memory_usage) / len(memory_usage),
                'min_memory_mb': min(memory_usage),
                'memory_growth': max(memory_usage) - min(memory_usage)
            }
        
        # CPU statistics
        if self.test_results['cpu_usage']:
            cpu_usage = self.test_results['cpu_usage']
            report['cpu_stats'] = {
                'peak_cpu_percent': max(cpu_usage),
                'avg_cpu_percent': sum(cpu_usage) / len(cpu_usage),
                'min_cpu_percent': min(cpu_usage)
            }
        
        # Processing statistics
        if self.test_results['processing_times']:
            processing_times = self.test_results['processing_times']
            report['processing_stats'] = {
                'total_processed': len(processing_times),
                'avg_processing_time': sum(processing_times) / len(processing_times),
                'max_processing_time': max(processing_times),
                'min_processing_time': min(processing_times),
                'files_per_second': len(processing_times) / sum(processing_times) if sum(processing_times) > 0 else 0
            }
        
        # Overall score calculation
        score_components = []
        
        # Memory efficiency (lower is better)
        if report['memory_stats'].get('peak_memory_mb', 0) < 500:
            score_components.append(25)  # Excellent memory usage
        elif report['memory_stats'].get('peak_memory_mb', 0) < 1000:
            score_components.append(20)  # Good memory usage
        else:
            score_components.append(10)  # High memory usage
        
        # Processing speed
        files_per_sec = report['processing_stats'].get('files_per_second', 0)
        if files_per_sec > 100:
            score_components.append(30)  # Very fast
        elif files_per_sec > 50:
            score_components.append(25)  # Fast
        elif files_per_sec > 10:
            score_components.append(20)  # Moderate
        else:
            score_components.append(10)  # Slow
        
        # API performance
        api_success_rate = (self.test_results.get('api_successes', 0) / max(1, self.test_results.get('api_requests', 1))) * 100
        if api_success_rate >= 95:
            score_components.append(25)
        elif api_success_rate >= 85:
            score_components.append(20)
        else:
            score_components.append(10)
        
        # Error handling
        total_analysis = self.test_results.get('successful_analysis', 0) + self.test_results.get('fallback_analysis', 0)
        total_files = max(1, self.test_results.get('total_files', 1))
        handling_rate = (total_analysis / total_files) * 100
        
        if handling_rate >= 95:
            score_components.append(20)  # Excellent error handling
        elif handling_rate >= 85:
            score_components.append(15)  # Good error handling
        else:
            score_components.append(5)   # Poor error handling
        
        report['overall_score'] = sum(score_components)
        
        return report
    
    def cleanup(self):
        """Cleanup test files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up test directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

def run_mass_analysis_load_test(file_count: int = 1000):
    """Führe Mass-Analysis Load Test aus"""
    
    logger.info("=== MASS ANALYSIS LOAD TEST ===")
    logger.info(f"Testing with {file_count} files")
    
    tester = MassAnalysisLoadTester()
    
    try:
        # Start monitoring
        tester.start_system_monitoring()
        
        # Phase 1: Create test files
        logger.info("Phase 1: Creating test files...")
        test_files = tester.create_test_files(file_count)
        tester.test_results['total_files'] = len(test_files)
        
        # Phase 2: Sequential analysis test
        logger.info("Phase 2: Sequential analysis test...")
        sequential_results = tester.test_sequential_analysis(test_files, limit=min(500, file_count))
        tester.test_results['successful_analysis'] += sequential_results['successful']
        tester.test_results['fallback_analysis'] += sequential_results['fallbacks']
        tester.test_results['failed_analysis'] += sequential_results['errors']
        
        # Phase 3: Concurrent analysis test
        logger.info("Phase 3: Concurrent analysis test...")
        concurrent_results = tester.test_concurrent_analysis(test_files, limit=min(200, file_count))
        
        # Phase 4: API load test
        logger.info("Phase 4: API load test...")
        api_results = tester.test_api_mass_load(100)
        tester.test_results['api_requests'] = api_results['total_requests']
        tester.test_results['api_successes'] = api_results['successful_requests']
        
        # Stop monitoring
        tester.stop_system_monitoring()
        
        # Generate report
        logger.info("Generating performance report...")
        performance_report = tester.generate_performance_report()
        
        # Results summary
        logger.info("\n=== MASS LOAD TEST RESULTS ===")
        logger.info(f"Files Created: {tester.test_results['total_files']}")
        logger.info(f"Sequential Processing: {sequential_results['processed']}/{min(500, file_count)} files")
        logger.info(f"Sequential Time: {sequential_results['total_time']:.1f}s")
        logger.info(f"Concurrent Processing: {concurrent_results['processed']}/{min(200, file_count)} files") 
        logger.info(f"Concurrent Time: {concurrent_results['total_time']:.1f}s")
        logger.info(f"API Success Rate: {(api_results['successful_requests']/api_results['total_requests']*100):.1f}%")
        
        if performance_report['memory_stats']:
            logger.info(f"Peak Memory Usage: {performance_report['memory_stats']['peak_memory_mb']:.1f} MB")
        
        if performance_report['processing_stats']:
            logger.info(f"Processing Speed: {performance_report['processing_stats']['files_per_second']:.1f} files/sec")
        
        logger.info(f"\n🎯 OVERALL PERFORMANCE SCORE: {performance_report['overall_score']}/100")
        
        if performance_report['overall_score'] >= 80:
            logger.info("🎉 EXCELLENT performance under mass load!")
            return True
        elif performance_report['overall_score'] >= 60:
            logger.info("✅ GOOD performance under mass load")
            return True
        else:
            logger.warning("⚠️ Performance could be improved under mass load")
            return False
            
    finally:
        tester.cleanup()

if __name__ == "__main__":
    file_count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    success = run_mass_analysis_load_test(file_count)
    sys.exit(0 if success else 1)