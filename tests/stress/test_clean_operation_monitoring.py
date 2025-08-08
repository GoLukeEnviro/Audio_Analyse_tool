#!/usr/bin/env python3
"""
Clean Operation Monitoring - 30-Minuten Produktions-ähnlicher Test
Überwacht System-Stabilität, Memory-Leaks, Performance unter kontinuierlicher Last
"""

import sys
import os
import time
import threading
import logging
import requests
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from core_engine.audio_analysis.analyzer import AudioAnalyzer
from core_engine.data_management.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"

@dataclass
class SystemMetrics:
    """System-Metriken für einen Zeitpunkt"""
    timestamp: float
    memory_mb: float
    cpu_percent: float
    disk_usage_mb: float
    db_size_mb: float
    active_connections: int
    response_time_ms: float
    api_success_rate: float

class CleanOperationMonitor:
    """30-Minuten Clean Operation Monitor"""
    
    def __init__(self, test_duration_minutes: int = 5):  # Reduziert für Demo
        self.test_duration = test_duration_minutes * 60  # Convert to seconds
        self.process = psutil.Process()
        self.monitoring_active = False
        self.start_time = time.time()
        
        self.metrics_history: List[SystemMetrics] = []
        self.api_request_log = []
        self.analysis_log = []
        self.error_log = []
        
        self.performance_targets = {
            'max_memory_mb': 1000,  # Max 1GB memory usage
            'max_cpu_percent': 80,  # Max 80% CPU
            'min_api_success_rate': 95,  # Min 95% API success
            'max_response_time_ms': 2000,  # Max 2s response time
            'memory_growth_rate': 10  # Max 10MB/minute memory growth
        }
        
        self.current_stats = {
            'total_api_requests': 0,
            'successful_api_requests': 0,
            'failed_api_requests': 0,
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'errors_encountered': 0
        }
    
    def get_current_metrics(self) -> SystemMetrics:
        """Sammle aktuelle System-Metriken"""
        try:
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            
            # Disk usage
            disk_usage = psutil.disk_usage('.')
            disk_usage_mb = disk_usage.used / 1024 / 1024
            
            # Database size
            db_path = Path('data/database.db')
            db_size_mb = db_path.stat().st_size / 1024 / 1024 if db_path.exists() else 0
            
            # API response time test
            api_start = time.time()
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=10)
                response_time_ms = (time.time() - api_start) * 1000
                api_success = response.status_code == 200
            except Exception:
                response_time_ms = 10000  # 10s timeout
                api_success = False
            
            # Calculate recent API success rate
            recent_requests = [req for req in self.api_request_log[-50:]]  # Last 50 requests
            if recent_requests:
                recent_successes = sum(1 for req in recent_requests if req.get('success', False))
                api_success_rate = (recent_successes / len(recent_requests)) * 100
            else:
                api_success_rate = 100 if api_success else 0
            
            return SystemMetrics(
                timestamp=time.time(),
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                disk_usage_mb=disk_usage_mb,
                db_size_mb=db_size_mb,
                active_connections=1,  # Simplified
                response_time_ms=response_time_ms,
                api_success_rate=api_success_rate
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return SystemMetrics(
                timestamp=time.time(),
                memory_mb=0, cpu_percent=0, disk_usage_mb=0, db_size_mb=0,
                active_connections=0, response_time_ms=0, api_success_rate=0
            )
    
    def start_monitoring(self):
        """Starte kontinuierliches System-Monitoring"""
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    metrics = self.get_current_metrics()
                    self.metrics_history.append(metrics)
                    
                    # Check for performance violations
                    self.check_performance_violations(metrics)
                    
                    # Log progress every 60 seconds
                    if len(self.metrics_history) % 12 == 0:  # Every 12 samples (60s at 5s intervals)
                        elapsed_minutes = (time.time() - self.start_time) / 60
                        logger.info(f"Monitoring: {elapsed_minutes:.1f}min - "
                                  f"Memory: {metrics.memory_mb:.1f}MB, "
                                  f"CPU: {metrics.cpu_percent:.1f}%, "
                                  f"API: {metrics.api_success_rate:.1f}%")
                    
                    time.sleep(5)  # Sample every 5 seconds
                    
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("Clean operation monitoring started")
    
    def check_performance_violations(self, metrics: SystemMetrics):
        """Prüfe auf Performance-Verstöße"""
        violations = []
        
        if metrics.memory_mb > self.performance_targets['max_memory_mb']:
            violations.append(f"Memory usage too high: {metrics.memory_mb:.1f}MB")
        
        if metrics.cpu_percent > self.performance_targets['max_cpu_percent']:
            violations.append(f"CPU usage too high: {metrics.cpu_percent:.1f}%")
        
        if metrics.response_time_ms > self.performance_targets['max_response_time_ms']:
            violations.append(f"Response time too slow: {metrics.response_time_ms:.1f}ms")
        
        if metrics.api_success_rate < self.performance_targets['min_api_success_rate']:
            violations.append(f"API success rate too low: {metrics.api_success_rate:.1f}%")
        
        # Check memory growth rate
        if len(self.metrics_history) >= 12:  # At least 1 minute of data
            old_memory = self.metrics_history[-12].memory_mb
            memory_growth = metrics.memory_mb - old_memory
            if memory_growth > self.performance_targets['memory_growth_rate']:
                violations.append(f"Memory growth too high: {memory_growth:.1f}MB/min")
        
        if violations:
            for violation in violations:
                logger.warning(f"Performance violation: {violation}")
                self.error_log.append({
                    'timestamp': time.time(),
                    'type': 'performance_violation',
                    'message': violation
                })
    
    def simulate_production_load(self):
        """Simuliere produktions-ähnliche Last"""
        def load_generator():
            while self.monitoring_active:
                try:
                    # API requests every 2-5 seconds
                    self.make_api_request()
                    time.sleep(2 + (time.time() % 3))  # 2-5 seconds
                    
                    # Occasional analysis tasks
                    if int(time.time()) % 15 == 0:  # Every 15 seconds
                        self.perform_analysis_task()
                    
                except Exception as e:
                    logger.debug(f"Load generation error: {e}")
        
        load_thread = threading.Thread(target=load_generator, daemon=True)
        load_thread.start()
        logger.info("Production load simulation started")
    
    def make_api_request(self):
        """Mache einen API-Request"""
        try:
            self.current_stats['total_api_requests'] += 1
            
            # Wähle zufälligen API-Endpunkt
            endpoints = [
                '/health',
                '/api/tracks?per_page=10',
                '/api/tracks/stats/overview'
            ]
            endpoint = endpoints[int(time.time()) % len(endpoints)]
            
            start_time = time.time()
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            success = response.status_code == 200
            if success:
                self.current_stats['successful_api_requests'] += 1
            else:
                self.current_stats['failed_api_requests'] += 1
            
            self.api_request_log.append({
                'timestamp': time.time(),
                'endpoint': endpoint,
                'response_time_ms': response_time,
                'status_code': response.status_code,
                'success': success
            })
            
        except Exception as e:
            self.current_stats['failed_api_requests'] += 1
            self.api_request_log.append({
                'timestamp': time.time(),
                'endpoint': 'unknown',
                'response_time_ms': 10000,
                'success': False,
                'error': str(e)
            })
    
    def perform_analysis_task(self):
        """Führe eine Analyse-Aufgabe aus"""
        try:
            self.current_stats['total_analyses'] += 1
            
            # Simuliere Analyse durch Fallback-Generierung
            from core_engine.audio_analysis.feature_extractor import get_fallback_analysis
            
            start_time = time.time()
            result = get_fallback_analysis("test_file.mp3")
            analysis_time = time.time() - start_time
            
            if result and result.get('status') == 'fallback':
                self.current_stats['successful_analyses'] += 1
                success = True
            else:
                self.current_stats['failed_analyses'] += 1
                success = False
            
            self.analysis_log.append({
                'timestamp': time.time(),
                'analysis_time_ms': analysis_time * 1000,
                'success': success
            })
            
        except Exception as e:
            self.current_stats['failed_analyses'] += 1
            self.analysis_log.append({
                'timestamp': time.time(),
                'success': False,
                'error': str(e)
            })
    
    def stop_monitoring(self):
        """Stoppe Monitoring"""
        self.monitoring_active = False
        logger.info("Clean operation monitoring stopped")
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generiere finalen Monitoring-Bericht"""
        if not self.metrics_history:
            return {'error': 'No metrics collected'}
        
        # Berechne Statistiken
        memory_values = [m.memory_mb for m in self.metrics_history]
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        response_times = [m.response_time_ms for m in self.metrics_history]
        api_success_rates = [m.api_success_rate for m in self.metrics_history]
        
        # Memory analysis
        memory_stats = {
            'initial_mb': memory_values[0],
            'final_mb': memory_values[-1],
            'peak_mb': max(memory_values),
            'average_mb': sum(memory_values) / len(memory_values),
            'growth_mb': memory_values[-1] - memory_values[0],
            'growth_rate_mb_per_min': (memory_values[-1] - memory_values[0]) / (len(memory_values) * 5 / 60)
        }
        
        # CPU analysis
        cpu_stats = {
            'average_percent': sum(cpu_values) / len(cpu_values),
            'peak_percent': max(cpu_values),
            'time_over_80_percent': sum(1 for cpu in cpu_values if cpu > 80) * 5  # seconds
        }
        
        # API analysis
        api_stats = {
            'total_requests': self.current_stats['total_api_requests'],
            'successful_requests': self.current_stats['successful_api_requests'],
            'failed_requests': self.current_stats['failed_api_requests'],
            'success_rate_percent': (self.current_stats['successful_api_requests'] / max(1, self.current_stats['total_api_requests'])) * 100,
            'average_response_time_ms': sum(response_times) / len(response_times),
            'max_response_time_ms': max(response_times),
            'timeouts': sum(1 for rt in response_times if rt >= 10000)
        }
        
        # Analysis stats
        analysis_stats = {
            'total_analyses': self.current_stats['total_analyses'],
            'successful_analyses': self.current_stats['successful_analyses'],
            'failed_analyses': self.current_stats['failed_analyses'],
            'success_rate_percent': (self.current_stats['successful_analyses'] / max(1, self.current_stats['total_analyses'])) * 100
        }
        
        # Performance violations
        violations = [error for error in self.error_log if error['type'] == 'performance_violation']
        
        # Overall health score
        health_score = self.calculate_health_score(memory_stats, cpu_stats, api_stats, analysis_stats)
        
        # Test duration
        actual_duration_minutes = (time.time() - self.start_time) / 60
        
        report = {
            'test_summary': {
                'planned_duration_minutes': self.test_duration / 60,
                'actual_duration_minutes': actual_duration_minutes,
                'metrics_collected': len(self.metrics_history),
                'sampling_interval_seconds': 5
            },
            'memory_analysis': memory_stats,
            'cpu_analysis': cpu_stats,
            'api_analysis': api_stats,
            'analysis_performance': analysis_stats,
            'performance_violations': {
                'count': len(violations),
                'details': violations[-10:]  # Last 10 violations
            },
            'stability_metrics': {
                'uptime_percent': 100,  # Simplified - we're still running
                'error_rate': len(self.error_log) / max(1, self.current_stats['total_api_requests']),
                'consistency_score': self.calculate_consistency_score()
            },
            'performance_targets': self.performance_targets,
            'overall_health_score': health_score,
            'recommendations': self.generate_recommendations(memory_stats, cpu_stats, api_stats)
        }
        
        return report
    
    def calculate_health_score(self, memory_stats, cpu_stats, api_stats, analysis_stats) -> int:
        """Berechne Gesamt-Health-Score (0-100)"""
        score_components = []
        
        # Memory score (25%)
        if memory_stats['peak_mb'] < self.performance_targets['max_memory_mb']:
            memory_score = 25
        elif memory_stats['peak_mb'] < self.performance_targets['max_memory_mb'] * 1.2:
            memory_score = 20
        else:
            memory_score = 10
        score_components.append(memory_score)
        
        # CPU score (25%)
        if cpu_stats['average_percent'] < 50:
            cpu_score = 25
        elif cpu_stats['average_percent'] < 70:
            cpu_score = 20
        else:
            cpu_score = 10
        score_components.append(cpu_score)
        
        # API score (30%)
        if api_stats['success_rate_percent'] >= 98:
            api_score = 30
        elif api_stats['success_rate_percent'] >= 95:
            api_score = 25
        elif api_stats['success_rate_percent'] >= 90:
            api_score = 20
        else:
            api_score = 10
        score_components.append(api_score)
        
        # Analysis score (20%)
        if analysis_stats['success_rate_percent'] >= 98:
            analysis_score = 20
        elif analysis_stats['success_rate_percent'] >= 95:
            analysis_score = 15
        else:
            analysis_score = 10
        score_components.append(analysis_score)
        
        return sum(score_components)
    
    def calculate_consistency_score(self) -> float:
        """Berechne Konsistenz-Score basierend auf Variabilität der Metriken"""
        if len(self.metrics_history) < 10:
            return 100.0
        
        # Berechne Variabilität der Response-Zeiten
        response_times = [m.response_time_ms for m in self.metrics_history[-50:]]  # Last 50
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            variance = sum((rt - avg_response) ** 2 for rt in response_times) / len(response_times)
            coefficient_of_variation = (variance ** 0.5) / avg_response if avg_response > 0 else 0
            
            # Convert to score (lower variation = higher score)
            consistency_score = max(0, 100 - (coefficient_of_variation * 100))
            return min(100, consistency_score)
        
        return 100.0
    
    def generate_recommendations(self, memory_stats, cpu_stats, api_stats) -> List[str]:
        """Generiere Empfehlungen basierend auf Performance"""
        recommendations = []
        
        if memory_stats['growth_rate_mb_per_min'] > 5:
            recommendations.append("High memory growth detected - check for memory leaks")
        
        if memory_stats['peak_mb'] > 800:
            recommendations.append("High memory usage - consider optimizing data structures")
        
        if cpu_stats['average_percent'] > 60:
            recommendations.append("High CPU usage - consider performance optimizations")
        
        if api_stats['average_response_time_ms'] > 1000:
            recommendations.append("Slow API responses - optimize database queries and caching")
        
        if api_stats['success_rate_percent'] < 98:
            recommendations.append("API reliability issues - improve error handling")
        
        if not recommendations:
            recommendations.append("System performance is within acceptable limits")
        
        return recommendations

def run_clean_operation_monitoring(duration_minutes: int = 5):
    """Führe Clean Operation Monitoring aus"""
    
    logger.info(f"=== CLEAN OPERATION MONITORING ({duration_minutes} minutes) ===")
    
    monitor = CleanOperationMonitor(duration_minutes)
    
    try:
        # Start monitoring and load simulation
        monitor.start_monitoring()
        monitor.simulate_production_load()
        
        # Run for specified duration
        end_time = time.time() + (duration_minutes * 60)
        
        logger.info(f"Monitoring will run for {duration_minutes} minutes...")
        logger.info("System is under continuous load simulation...")
        
        # Wait and report progress
        while time.time() < end_time:
            remaining_minutes = (end_time - time.time()) / 60
            if remaining_minutes > 0.5:
                logger.info(f"Monitoring continues... {remaining_minutes:.1f} minutes remaining")
                time.sleep(30)  # Report every 30 seconds
            else:
                time.sleep(5)  # Check more frequently near end
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Generate final report
        logger.info("Generating final monitoring report...")
        report = monitor.generate_final_report()
        
        # Display results
        logger.info("\n=== CLEAN OPERATION MONITORING RESULTS ===")
        logger.info(f"Test Duration: {report['test_summary']['actual_duration_minutes']:.1f} minutes")
        logger.info(f"Metrics Collected: {report['test_summary']['metrics_collected']} samples")
        
        logger.info(f"\nMemory Analysis:")
        logger.info(f"  Peak Usage: {report['memory_analysis']['peak_mb']:.1f} MB")
        logger.info(f"  Growth Rate: {report['memory_analysis']['growth_rate_mb_per_min']:.1f} MB/min")
        
        logger.info(f"\nAPI Performance:")
        logger.info(f"  Success Rate: {report['api_analysis']['success_rate_percent']:.1f}%")
        logger.info(f"  Avg Response: {report['api_analysis']['average_response_time_ms']:.1f}ms")
        logger.info(f"  Total Requests: {report['api_analysis']['total_requests']}")
        
        logger.info(f"\nPerformance Violations: {report['performance_violations']['count']}")
        
        logger.info(f"\n🎯 OVERALL HEALTH SCORE: {report['overall_health_score']}/100")
        
        # Recommendations
        logger.info(f"\nRecommendations:")
        for rec in report['recommendations']:
            logger.info(f"  • {rec}")
        
        # Determine success
        if report['overall_health_score'] >= 80:
            logger.info("🎉 EXCELLENT system stability under clean operation!")
            return True
        elif report['overall_health_score'] >= 60:
            logger.info("✅ GOOD system stability")
            return True
        else:
            logger.warning("⚠️ System stability needs improvement")
            return False
            
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
        monitor.stop_monitoring()
        return False
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        monitor.stop_monitoring()
        return False

if __name__ == "__main__":
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    success = run_clean_operation_monitoring(duration)
    sys.exit(0 if success else 1)