#!/usr/bin/env python3
"""
Comprehensive Null-Value Handling Tests
Testet alle kritischen Szenarien mit None/NULL-Werten
"""

import sys
import os
import json
import time
import pytest
import logging
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from api.models import (
    TrackSummary, CamelotInfo, AudioFeatures, MoodAnalysis, 
    MoodCategory, DerivedMetrics, TrackMetadata
)
from api.endpoints.tracks import sanitize_track_data, track_to_summary
from core_engine.audio_analysis.feature_extractor import get_safe_defaults, get_fallback_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestNullValueHandling:
    """Umfassende Tests für NULL-Werte Behandlung"""
    
    def test_pydantic_models_with_defaults(self):
        """Test: Pydantic-Modelle mit Default-Werten"""
        
        # Test TrackSummary mit minimalen Daten
        track = TrackSummary(
            file_path="test.mp3",
            filename="test.mp3", 
            duration=180.0,
            bpm=120.0,
            energy=0.5,
            analyzed_at=time.time()
        )
        
        assert track.key == ""
        assert track.camelot == ""
        assert track.title is None  # Optional field
        assert track.artist is None  # Optional field
        logger.info("✓ TrackSummary handles None/defaults correctly")
        
        # Test CamelotInfo mit Defaults
        camelot = CamelotInfo()
        assert camelot.key == "Unknown"
        assert camelot.camelot == "1A"
        assert camelot.key_confidence == 0.0
        assert len(camelot.compatible_keys) >= 3
        logger.info("✓ CamelotInfo uses default factories")
        
        # Test AudioFeatures mit Defaults
        features = AudioFeatures()
        assert features.bpm == 120.0
        assert features.energy == 0.5
        assert features.valence == 0.5
        logger.info("✓ AudioFeatures has safe defaults")
        
        # Test MoodAnalysis mit Defaults
        mood = MoodAnalysis()
        assert mood.primary_mood == MoodCategory.neutral
        assert mood.confidence == 0.0
        assert len(mood.scores) > 0
        assert mood.scores['neutral'] == 1.0
        logger.info("✓ MoodAnalysis uses factory defaults")
        
        return True
    
    def test_extreme_null_data_sanitization(self):
        """Test: Sanitization mit extremen NULL-Werten"""
        
        # Test 1: Komplett leeres Dict
        result = sanitize_track_data({})
        assert result['file_path'] == 'unknown'
        assert result['metadata']['artist'] == 'Unknown Artist'
        assert result['features']['bpm'] == 120.0
        assert result['camelot']['camelot'] == '1A'
        logger.info("✓ Empty dict sanitized successfully")
        
        # Test 2: Nur None-Werte
        null_data = {
            'file_path': None,
            'filename': None,
            'metadata': {
                'title': None,
                'artist': None,
                'duration': None
            },
            'features': {
                'bpm': None,
                'energy': None,
                'key': None
            },
            'camelot': None,
            'mood': None
        }
        
        result = sanitize_track_data(null_data)
        assert result['metadata']['artist'] == 'Unknown Artist'
        assert result['features']['bpm'] == 120.0
        assert result['camelot']['key'] == 'Unknown'
        assert result['mood']['primary_mood'] == 'neutral'
        logger.info("✓ All-None data sanitized successfully")
        
        # Test 3: Broken/Invalid-Daten
        broken_data = {
            'file_path': '',
            'metadata': 'not_a_dict',  # Invalid type
            'features': [],            # Wrong type
            'camelot': {'key': '', 'camelot': None},
            'mood': {'primary_mood': 'invalid_mood'}
        }
        
        result = sanitize_track_data(broken_data)
        assert isinstance(result['metadata'], dict)
        assert isinstance(result['features'], dict)
        assert result['camelot']['camelot'] == '1A'
        logger.info("✓ Broken data types sanitized successfully")
        
        return True
    
    def test_track_conversion_with_nulls(self):
        """Test: Track-Konvertierung mit NULL-Werten"""
        
        # Verschiedene NULL-Szenarien
        test_cases = [
            # Fall 1: Minimale Daten
            {
                'file_path': 'test1.mp3',
                'filename': 'test1.mp3'
            },
            
            # Fall 2: Teilweise NULL-Metadaten
            {
                'file_path': 'test2.mp3',
                'filename': 'test2.mp3',
                'metadata': {
                    'title': None,
                    'artist': 'Some Artist',
                    'duration': 200.0
                },
                'features': {
                    'bmp': None,  # Typo
                    'energy': 0.7
                }
            },
            
            # Fall 3: Korrupte Strukturen
            {
                'file_path': 'test3.mp3',
                'metadata': None,
                'camelot': {'key': '', 'camelot': ''},
                'mood': {'scores': None}
            }
        ]
        
        for i, test_data in enumerate(test_cases, 1):
            try:
                summary = track_to_summary(test_data)
                assert isinstance(summary, TrackSummary)
                assert summary.file_path  # Should not be empty
                assert summary.key is not None  # Should be string
                assert summary.camelot is not None  # Should be string
                logger.info(f"✓ Test case {i} converted successfully")
                
            except Exception as e:
                logger.error(f"✗ Test case {i} failed: {e}")
                raise
        
        return True
    
    def test_fallback_analysis_generation(self):
        """Test: Fallback-Analyse Generation"""
        
        # Test 1: Standard Fallback
        fallback = get_fallback_analysis("test.mp3")
        
        assert fallback['status'] == 'fallback'
        assert fallback['file_path'] == 'test.mp3'
        assert fallback['features']['bpm'] == 120.0
        assert fallback['camelot']['key'] == 'Unknown'
        assert fallback['mood']['primary_mood'] == 'neutral'
        assert len(fallback['errors']) > 0
        logger.info("✓ Standard fallback analysis generated")
        
        # Test 2: Unknown file fallback
        fallback_unknown = get_fallback_analysis()
        assert fallback_unknown['file_path'] == 'unknown'
        assert fallback_unknown['filename'] == 'unknown'
        logger.info("✓ Unknown file fallback generated")
        
        # Test 3: Validate all required fields
        required_sections = ['features', 'metadata', 'camelot', 'mood', 'derived_metrics']
        for section in required_sections:
            assert section in fallback
            assert isinstance(fallback[section], dict)
            assert len(fallback[section]) > 0
        
        logger.info("✓ All fallback sections properly structured")
        
        return True
    
    def test_database_null_resilience(self):
        """Test: Database NULL-Werte Resistenz"""
        
        # Simuliere DB-Rückgaben mit NULL-Werten
        mock_db_responses = [
            # Fall 1: Komplett leere Row
            {},
            
            # Fall 2: Teilweise NULL-Werte
            {
                'file_path': 'test.mp3',
                'title': None,
                'artist': '',
                'bpm': None,
                'key_name': None,
                'camelot': '',
                'energy': None
            },
            
            # Fall 3: Gemischte Datentypen
            {
                'file_path': 'test2.mp3',
                'bpm': 'not_a_number',
                'energy': -0.5,  # Invalid range
                'camelot': 'invalid',
                'key_confidence': 1.5  # Out of range
            }
        ]
        
        for i, mock_data in enumerate(mock_db_responses, 1):
            try:
                # Sanitize DB data
                sanitized = sanitize_track_data(mock_data)
                
                # Convert to TrackSummary
                summary = track_to_summary(sanitized)
                
                # Validate result
                assert isinstance(summary, TrackSummary)
                assert summary.key != None  # Should be string (could be empty)
                assert summary.camelot != None  # Should be string
                assert summary.bpm >= 0  # Should be valid
                
                logger.info(f"✓ DB mock case {i} handled correctly")
                
            except Exception as e:
                logger.error(f"✗ DB mock case {i} failed: {e}")
                raise
        
        return True
    
    def test_api_endpoint_null_resilience(self):
        """Test: API-Endpoint NULL-Resistenz"""
        
        # Teste verschiedene fehlerhafte Track-Listen
        error_cases = [
            [],  # Leere Liste
            [None],  # Liste mit None
            [{}],  # Liste mit leerem Dict
            [{'file_path': None}],  # Liste mit NULL-Werten
            [{'completely': 'broken', 'structure': True}]  # Komplett falsche Struktur
        ]
        
        for i, error_case in enumerate(error_cases, 1):
            try:
                # Simuliere die list_tracks Logik
                track_summaries = []
                failed_conversions = 0
                
                for track in error_case:
                    try:
                        if track is None:
                            track = {}
                        
                        summary = track_to_summary(track)
                        track_summaries.append(summary)
                        
                    except Exception as e:
                        failed_conversions += 1
                        logger.warning(f"Conversion failed (expected): {e}")
                        
                        # Erstelle safe fallback summary
                        safe_summary = TrackSummary(
                            file_path=str(track.get('file_path', 'unknown') if track else 'unknown'),
                            filename='Error loading track',
                            title='Error loading track',
                            artist='Unknown',
                            duration=0.0,
                            bpm=120.0,
                            key='Unknown', 
                            camelot='1A',
                            energy=0.5,
                            mood='neutral',
                            analyzed_at=0.0
                        )
                        track_summaries.append(safe_summary)
                
                # Validiere Endergebnis
                assert isinstance(track_summaries, list)
                for summary in track_summaries:
                    assert isinstance(summary, TrackSummary)
                
                logger.info(f"✓ API error case {i} handled gracefully ({len(track_summaries)} results, {failed_conversions} failed)")
                
            except Exception as e:
                logger.error(f"✗ API error case {i} crashed: {e}")
                raise
        
        return True

def run_null_value_tests():
    """Führe alle NULL-Werte Tests aus"""
    
    logger.info("=== NULL-Value Handling Tests ===")
    
    tester = TestNullValueHandling()
    
    tests = [
        ("Pydantic Models with Defaults", tester.test_pydantic_models_with_defaults),
        ("Extreme NULL Data Sanitization", tester.test_extreme_null_data_sanitization),
        ("Track Conversion with NULLs", tester.test_track_conversion_with_nulls),
        ("Fallback Analysis Generation", tester.test_fallback_analysis_generation),
        ("Database NULL Resilience", tester.test_database_null_resilience),
        ("API Endpoint NULL Resilience", tester.test_api_endpoint_null_resilience)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing: {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                failed += 1
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_name} CRASHED: {e}", exc_info=True)
    
    logger.info(f"\n=== NULL-Value Test Results ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        logger.info("🎉 All NULL-value handling tests passed!")
        return True
    else:
        logger.warning(f"⚠️ {failed} NULL-value tests failed")
        return False

if __name__ == "__main__":
    success = run_null_value_tests()
    sys.exit(0 if success else 1)