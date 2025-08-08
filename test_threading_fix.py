#!/usr/bin/env python3
"""
Test script für die SQLite Threading-Fix
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Test-Datei (falls vorhanden)
test_files = [
    "M:\\Soundeo 2024\\92.2024\\3\\Richard Cleber - Omnia (Drumsauw Remix).aiff",
    "M:\\Soundeo 2024\\92.2024\\3\\Wehbba - Nitro (Original Mix).aiff",
    "M:\\Soundeo 2024\\92.2024\\3\\Zeltak - Addiction (Original Mix).aiff"
]

def test_single_analysis(file_path):
    """Teste einzelne Datei-Analyse"""
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/analyze/single",
            json={"file_path": file_path},
            timeout=30
        )
        print(f"Thread {threading.current_thread().ident}: {file_path} -> Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Erfolg: {result.get('status', 'unknown')}")
        else:
            print(f"  Fehler: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Thread {threading.current_thread().ident}: Fehler bei {file_path}: {e}")
        return False

def test_concurrent_analysis():
    """Teste gleichzeitige Analyse mehrerer Dateien"""
    print("🧪 Teste gleichzeitige Audio-Analyse...")
    
    # Teste mit ThreadPoolExecutor (simuliert das Threading-Problem)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for file_path in test_files:
            future = executor.submit(test_single_analysis, file_path)
            futures.append(future)
        
        # Warte auf alle Ergebnisse
        results = []
        for future in futures:
            try:
                result = future.result(timeout=60)
                results.append(result)
            except Exception as e:
                print(f"Future failed: {e}")
                results.append(False)
    
    success_count = sum(results)
    print(f"\n✅ Erfolgreich: {success_count}/{len(test_files)}")
    print(f"❌ Fehlgeschlagen: {len(test_files) - success_count}/{len(test_files)}")
    
    return success_count == len(test_files)

def test_database_stats():
    """Teste Datenbank-Statistiken"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/cache/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 DB Stats: {stats.get('analyzed_tracks', 0)} analysierte Tracks")
            return True
        else:
            print(f"❌ Stats-Fehler: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats-Exception: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Teste SQLite Threading-Fix...")
    print("="*50)
    
    # Teste Datenbank-Statistiken
    print("\n1. Teste Datenbank-Verbindung...")
    if test_database_stats():
        print("✅ Datenbank-Verbindung OK")
    else:
        print("❌ Datenbank-Verbindung fehlgeschlagen")
    
    # Teste gleichzeitige Analyse
    print("\n2. Teste gleichzeitige Audio-Analyse...")
    if test_concurrent_analysis():
        print("\n🎉 Alle Tests erfolgreich! Threading-Problem behoben.")
    else:
        print("\n⚠️  Einige Tests fehlgeschlagen. Prüfe die Logs.")
    
    print("\n📋 Prüfe die Backend-Logs für SQLite-Fehler...")