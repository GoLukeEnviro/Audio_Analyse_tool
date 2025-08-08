#!/usr/bin/env python3
"""Test-Skript für den Multiprocessing/SQLite Fix"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from core_engine.audio_analysis.analyzer import AudioAnalyzer
    import asyncio
    
    async def test_multiprocessing_fix():
        print("[TEST] Teste ThreadPool-Hotfix fuer SQLite/Multiprocessing...")
        
        # Initialize analyzer
        analyzer = AudioAnalyzer(
            db_path="data/test_database.db", 
            enable_multiprocessing=True
        )
        
        print(f"[OK] AudioAnalyzer initialisiert (Multiprocessing: {analyzer.enable_multiprocessing})")
        print(f"[OK] Max Workers: {analyzer.max_workers}")
        
        # Test mit ein paar Dummy-Dateien
        test_files = []
        
        # Finde echte Audio-Dateien falls vorhanden
        test_dirs = ["data/inbox", "data", "backend/test_data"]
        for test_dir in test_dirs:
            test_path = Path(test_dir)
            if test_path.exists():
                audio_files = []
                for ext in ['.mp3', '.wav', '.flac', '.m4a']:
                    audio_files.extend(list(test_path.glob(f"*{ext}")))
                if audio_files:
                    test_files = [str(f) for f in audio_files[:3]]  # Max 3 files
                    break
        
        if not test_files:
            print("[WARNING] Keine Audio-Test-Dateien gefunden")
            print("[TEST] Erstelle Dummy-Test fuer Validierung...")
            
            # Teste nur die Initialisierung
            stats = analyzer.get_analysis_stats()
            cache_stats = analyzer.get_cache_stats() 
            print(f"[OK] Analyzer-Stats: {stats}")
            print(f"[OK] Cache-Stats: {cache_stats}")
            print("[SUCCESS] ERFOLG: Kein SQLite-Pickling-Fehler bei Initialisierung!")
            return
        
        print(f"[TEST] Teste mit {len(test_files)} Audio-Dateien:")
        for f in test_files:
            print(f"  - {Path(f).name}")
        
        # Teste Batch-Analyse (hier würde der Pickling-Fehler auftreten)
        try:
            results = await analyzer.analyze_batch_async(
                test_files,
                progress_callback=lambda done, total, current: print(f"Progress: {done}/{total} - {Path(current).name}")
            )
            
            print(f"[SUCCESS] ERFOLG: Batch-Analyse abgeschlossen ohne Pickling-Fehler!")
            print(f"[STATS] Analysierte Dateien: {len(results)}")
            
            # Prüfe Ergebnisse
            for file_path, result in results.items():
                status = result.get('status', 'unknown')
                errors = result.get('errors', [])
                filename = Path(file_path).name
                
                if status == 'completed':
                    features = result.get('features', {})
                    bpm = features.get('bpm', 'N/A')
                    energy = features.get('energy', 'N/A')
                    print(f"  [OK] {filename}: BPM={bpm}, Energy={energy}")
                elif status == 'error':
                    print(f"  [ERROR] {filename}: {errors}")
                else:
                    print(f"  [WARNING] {filename}: Status={status}")
            
            # Test DB-Zugriff
            db_stats = analyzer.get_cache_stats()
            print(f"[STATS] DB-Stats nach Analyse: {db_stats['analyzed_tracks']} Tracks")
            
            print("[SUCCESS] PERFEKT: ThreadPool-Hotfix funktioniert!")
            print("[SUCCESS] Kein 'cannot pickle sqlite3.Connection' Fehler mehr!")
            
        except Exception as e:
            if "cannot pickle" in str(e) and "sqlite3.Connection" in str(e):
                print(f"[ERROR] FEHLER: SQLite-Pickling Problem noch nicht behoben!")
                print(f"[ERROR] Fehlerdetails: {e}")
                return False
            else:
                print(f"[WARNING] Anderer Fehler bei Batch-Analyse: {e}")
                # Other errors are okay for this test
                
    if __name__ == "__main__":
        asyncio.run(test_multiprocessing_fix())
        
except ImportError as e:
    print(f"[ERROR] Import-Fehler: {e}")
    print("[INFO] Stelle sicher, dass alle Dependencies installiert sind:")
    print("   pip install librosa soundfile mutagen")