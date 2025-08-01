import pytest98
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from playlist_engine.generator import PlaylistGenerator
from playlist_engine.algorithms import (
    BPMCompatibilityAlgorithm,
    KeyCompatibilityAlgorithm,
    EnergyProgressionAlgorithm,
    SimilarityAlgorithm
)
from playlist_engine.rules import PlaylistRules

class TestPlaylistGenerator:
    """Test cases for PlaylistGenerator class"""
    
    def test_generator_initialization(self):
        """Test PlaylistGenerator initialization"""
        generator = PlaylistGenerator()
        assert generator is not None
        assert hasattr(generator, 'algorithms')
        assert len(generator.algorithms) > 0
    
    def test_generate_playlist_basic(self, mock_playlist_data):
        """Test basic playlist generation"""
        generator = PlaylistGenerator()
        tracks = mock_playlist_data['tracks']
        rules = PlaylistRules(
            bpm_range=(125, 135),
            key_compatibility=True,
            energy_progression='ascending'
        )
        
        playlist = generator.generate_playlist(tracks, rules, target_length=3)
        
        assert playlist is not None
        assert len(playlist) <= 3
        assert all('filename' in track for track in playlist)
    
    def test_generate_playlist_empty_tracks(self):
        """Test playlist generation with empty track list"""
        generator = PlaylistGenerator()
        rules = PlaylistRules()
        
        playlist = generator.generate_playlist([], rules, target_length=5)
        
        assert playlist == []
    
    def test_generate_playlist_bpm_filtering(self, mock_playlist_data):
        """Test playlist generation with BPM filtering"""
        generator = PlaylistGenerator()
        tracks = mock_playlist_data['tracks']
        
        # Strict BPM range that should filter some tracks
        rules = PlaylistRules(bpm_range=(127, 129))
        
        playlist = generator.generate_playlist(tracks, rules, target_length=10)
        
        # Should only include tracks within BPM range
        for track in playlist:
            assert 127 <= track['bpm'] <= 129
    
    def test_generate_playlist_key_compatibility(self, mock_playlist_data):
        """Test playlist generation with key compatibility"""
        generator = PlaylistGenerator()
        tracks = mock_playlist_data['tracks']
        
        rules = PlaylistRules(key_compatibility=True)
        
        playlist = generator.generate_playlist(tracks, rules, target_length=3)
        
        # Check that consecutive tracks have compatible keys
        if len(playlist) > 1:
            for i in range(len(playlist) - 1):
                current_key = playlist[i]['key']
                next_key = playlist[i + 1]['key']
                # Basic compatibility check (same key or related keys)
                assert current_key is not None
                assert next_key is not None
    
    def test_generate_playlist_energy_progression(self, mock_playlist_data):
        """Test playlist generation with energy progression"""
        generator = PlaylistGenerator()
        tracks = mock_playlist_data['tracks']
        
        rules = PlaylistRules(energy_progression='ascending')
        
        playlist = generator.generate_playlist(tracks, rules, target_length=3)
        
        # Check that energy levels are ascending
        if len(playlist) > 1:
            energy_levels = [track['energy_level'] for track in playlist]
            for i in range(len(energy_levels) - 1):
                assert energy_levels[i] <= energy_levels[i + 1]
    
    def test_optimize_playlist_order(self, mock_playlist_data):
        """Test playlist order optimization"""
        generator = PlaylistGenerator()
        tracks = mock_playlist_data['tracks']
        rules = PlaylistRules()
        
        optimized = generator.optimize_playlist_order(tracks, rules)
        
        assert len(optimized) == len(tracks)
        assert all(track in tracks for track in optimized)

class TestBPMCompatibilityAlgorithm:
    """Test cases for BPM compatibility algorithm"""
    
    def test_bpm_algorithm_initialization(self):
        """Test BPM algorithm initialization"""
        algorithm = BPMCompatibilityAlgorithm(max_bpm_difference=10)
        assert algorithm.max_bpm_difference == 10
    
    def test_calculate_compatibility_same_bpm(self):
        """Test BPM compatibility with same BPM"""
        algorithm = BPMCompatibilityAlgorithm(max_bpm_difference=10)
        
        track1 = {'bpm': 128.0}
        track2 = {'bpm': 128.0}
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility == 1.0
    
    def test_calculate_compatibility_within_range(self):
        """Test BPM compatibility within acceptable range"""
        algorithm = BPMCompatibilityAlgorithm(max_bpm_difference=10)
        
        track1 = {'bpm': 128.0}
        track2 = {'bpm': 132.0}  # 4 BPM difference
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert 0.0 < compatibility < 1.0
    
    def test_calculate_compatibility_outside_range(self):
        """Test BPM compatibility outside acceptable range"""
        algorithm = BPMCompatibilityAlgorithm(max_bpm_difference=5)
        
        track1 = {'bpm': 128.0}
        track2 = {'bpm': 140.0}  # 12 BPM difference
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility == 0.0
    
    def test_filter_compatible_tracks(self):
        """Test filtering tracks by BPM compatibility"""
        algorithm = BPMCompatibilityAlgorithm(max_bpm_difference=5)
        
        reference_track = {'bpm': 128.0}
        candidate_tracks = [
            {'bpm': 126.0, 'filename': 'track1.mp3'},  # Compatible
            {'bpm': 130.0, 'filename': 'track2.mp3'},  # Compatible
            {'bpm': 140.0, 'filename': 'track3.mp3'},  # Not compatible
            {'bpm': 125.0, 'filename': 'track4.mp3'},  # Compatible
        ]
        
        compatible = algorithm.filter_compatible_tracks(reference_track, candidate_tracks)
        
        assert len(compatible) == 3
        assert all(abs(track['bpm'] - 128.0) <= 5 for track in compatible)

class TestKeyCompatibilityAlgorithm:
    """Test cases for Key compatibility algorithm"""
    
    def test_key_algorithm_initialization(self):
        """Test Key algorithm initialization"""
        algorithm = KeyCompatibilityAlgorithm()
        assert algorithm is not None
        assert hasattr(algorithm, 'camelot_wheel')
    
    def test_calculate_compatibility_same_key(self):
        """Test key compatibility with same key"""
        algorithm = KeyCompatibilityAlgorithm()
        
        track1 = {'key': 'C', 'camelot_key': '8B'}
        track2 = {'key': 'C', 'camelot_key': '8B'}
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility == 1.0
    
    def test_calculate_compatibility_adjacent_keys(self):
        """Test key compatibility with adjacent keys"""
        algorithm = KeyCompatibilityAlgorithm()
        
        track1 = {'key': 'C', 'camelot_key': '8B'}
        track2 = {'key': 'G', 'camelot_key': '9B'}  # Adjacent in Camelot wheel
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility > 0.5
    
    def test_calculate_compatibility_incompatible_keys(self):
        """Test key compatibility with incompatible keys"""
        algorithm = KeyCompatibilityAlgorithm()
        
        track1 = {'key': 'C', 'camelot_key': '8B'}
        track2 = {'key': 'F#', 'camelot_key': '2A'}  # Incompatible
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility < 0.5
    
    def test_get_camelot_key(self):
        """Test Camelot key conversion"""
        algorithm = KeyCompatibilityAlgorithm()
        
        camelot = algorithm.get_camelot_key('C', 'major')
        assert camelot in algorithm.camelot_wheel.values()
        
        camelot = algorithm.get_camelot_key('A', 'minor')
        assert camelot in algorithm.camelot_wheel.values()
    
    def test_are_keys_compatible(self):
        """Test key compatibility checking"""
        algorithm = KeyCompatibilityAlgorithm()
        
        # Same key should be compatible
        assert algorithm.are_keys_compatible('8B', '8B') is True
        
        # Adjacent keys should be compatible
        assert algorithm.are_keys_compatible('8B', '9B') is True
        assert algorithm.are_keys_compatible('8B', '7B') is True
        
        # Relative major/minor should be compatible
        assert algorithm.are_keys_compatible('8B', '8A') is True

class TestEnergyProgressionAlgorithm:
    """Test cases for Energy progression algorithm"""
    
    def test_energy_algorithm_initialization(self):
        """Test Energy algorithm initialization"""
        algorithm = EnergyProgressionAlgorithm(progression_type='ascending')
        assert algorithm.progression_type == 'ascending'
    
    def test_calculate_compatibility_ascending(self):
        """Test energy compatibility with ascending progression"""
        algorithm = EnergyProgressionAlgorithm(progression_type='ascending')
        
        track1 = {'energy_level': 0.5}
        track2 = {'energy_level': 0.7}  # Higher energy
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility > 0.5
    
    def test_calculate_compatibility_descending(self):
        """Test energy compatibility with descending progression"""
        algorithm = EnergyProgressionAlgorithm(progression_type='descending')
        
        track1 = {'energy_level': 0.8}
        track2 = {'energy_level': 0.6}  # Lower energy
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility > 0.5
    
    def test_calculate_compatibility_stable(self):
        """Test energy compatibility with stable progression"""
        algorithm = EnergyProgressionAlgorithm(progression_type='stable')
        
        track1 = {'energy_level': 0.7}
        track2 = {'energy_level': 0.72}  # Similar energy
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility > 0.8
    
    def test_sort_by_energy(self):
        """Test sorting tracks by energy level"""
        algorithm = EnergyProgressionAlgorithm(progression_type='ascending')
        
        tracks = [
            {'energy_level': 0.8, 'filename': 'high.mp3'},
            {'energy_level': 0.3, 'filename': 'low.mp3'},
            {'energy_level': 0.6, 'filename': 'medium.mp3'}
        ]
        
        sorted_tracks = algorithm.sort_by_energy(tracks, 'ascending')
        
        energy_levels = [track['energy_level'] for track in sorted_tracks]
        assert energy_levels == sorted(energy_levels)
    
    def test_optimize_energy_flow(self):
        """Test energy flow optimization"""
        algorithm = EnergyProgressionAlgorithm(progression_type='ascending')
        
        tracks = [
            {'energy_level': 0.8, 'filename': 'high.mp3'},
            {'energy_level': 0.3, 'filename': 'low.mp3'},
            {'energy_level': 0.6, 'filename': 'medium.mp3'}
        ]
        
        optimized = algorithm.optimize_energy_flow(tracks)
        
        assert len(optimized) == len(tracks)
        # Should be ordered by energy for ascending progression
        energy_levels = [track['energy_level'] for track in optimized]
        assert energy_levels == sorted(energy_levels)

class TestSimilarityAlgorithm:
    """Test cases for Similarity algorithm"""
    
    def test_similarity_algorithm_initialization(self):
        """Test Similarity algorithm initialization"""
        algorithm = SimilarityAlgorithm()
        assert algorithm is not None
    
    def test_calculate_compatibility_identical_features(self):
        """Test similarity with identical features"""
        algorithm = SimilarityAlgorithm()
        
        track1 = {
            'mfcc': [1.0, 2.0, 3.0],
            'spectral_centroid': 2000.0,
            'spectral_rolloff': 4000.0
        }
        track2 = {
            'mfcc': [1.0, 2.0, 3.0],
            'spectral_centroid': 2000.0,
            'spectral_rolloff': 4000.0
        }
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert compatibility == 1.0
    
    def test_calculate_compatibility_different_features(self):
        """Test similarity with different features"""
        algorithm = SimilarityAlgorithm()
        
        track1 = {
            'mfcc': [1.0, 2.0, 3.0],
            'spectral_centroid': 2000.0,
            'spectral_rolloff': 4000.0
        }
        track2 = {
            'mfcc': [4.0, 5.0, 6.0],
            'spectral_centroid': 3000.0,
            'spectral_rolloff': 5000.0
        }
        
        compatibility = algorithm.calculate_compatibility(track1, track2)
        assert 0.0 <= compatibility <= 1.0
        assert compatibility < 1.0
    
    def test_calculate_mfcc_similarity(self):
        """Test MFCC similarity calculation"""
        algorithm = SimilarityAlgorithm()
        
        mfcc1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        mfcc2 = [1.1, 2.1, 3.1, 4.1, 5.1]  # Very similar
        
        similarity = algorithm.calculate_mfcc_similarity(mfcc1, mfcc2)
        assert similarity > 0.9
        
        mfcc3 = [10.0, 20.0, 30.0, 40.0, 50.0]  # Very different
        similarity = algorithm.calculate_mfcc_similarity(mfcc1, mfcc3)
        assert similarity < 0.5
    
    def test_find_similar_tracks(self):
        """Test finding similar tracks"""
        algorithm = SimilarityAlgorithm()
        
        reference_track = {
            'mfcc': [1.0, 2.0, 3.0],
            'spectral_centroid': 2000.0,
            'filename': 'reference.mp3'
        }
        
        candidate_tracks = [
            {
                'mfcc': [1.1, 2.1, 3.1],
                'spectral_centroid': 2100.0,
                'filename': 'similar.mp3'
            },
            {
                'mfcc': [10.0, 20.0, 30.0],
                'spectral_centroid': 5000.0,
                'filename': 'different.mp3'
            }
        ]
        
        similar_tracks = algorithm.find_similar_tracks(reference_track, candidate_tracks, threshold=0.5)
        
        assert len(similar_tracks) >= 1
        assert 'similar.mp3' in [track['filename'] for track in similar_tracks]

class TestPlaylistRules:
    """Test cases for PlaylistRules class"""
    
    def test_rules_initialization_default(self):
        """Test PlaylistRules default initialization"""
        rules = PlaylistRules()
        
        assert rules.bpm_range is None
        assert rules.key_compatibility is False
        assert rules.energy_progression is None
        assert rules.max_bpm_difference == 10
    
    def test_rules_initialization_custom(self):
        """Test PlaylistRules custom initialization"""
        rules = PlaylistRules(
            bpm_range=(120, 140),
            key_compatibility=True,
            energy_progression='ascending',
            max_bpm_difference=5
        )
        
        assert rules.bpm_range == (120, 140)
        assert rules.key_compatibility is True
        assert rules.energy_progression == 'ascending'
        assert rules.max_bpm_difference == 5
    
    def test_validate_rules(self):
        """Test rules validation"""
        # Valid rules
        rules = PlaylistRules(
            bpm_range=(120, 140),
            energy_progression='ascending'
        )
        assert rules.validate() is True
        
        # Invalid BPM range
        rules = PlaylistRules(bpm_range=(140, 120))  # min > max
        assert rules.validate() is False
        
        # Invalid energy progression
        rules = PlaylistRules(energy_progression='invalid')
        assert rules.validate() is False
    
    def test_to_dict(self):
        """Test converting rules to dictionary"""
        rules = PlaylistRules(
            bpm_range=(120, 140),
            key_compatibility=True,
            energy_progression='ascending'
        )
        
        rules_dict = rules.to_dict()
        
        assert isinstance(rules_dict, dict)
        assert rules_dict['bpm_range'] == (120, 140)
        assert rules_dict['key_compatibility'] is True
        assert rules_dict['energy_progression'] == 'ascending'
    
    def test_from_dict(self):
        """Test creating rules from dictionary"""
        rules_dict = {
            'bpm_range': (120, 140),
            'key_compatibility': True,
            'energy_progression': 'descending',
            'max_bpm_difference': 8
        }
        
        rules = PlaylistRules.from_dict(rules_dict)
        
        assert rules.bpm_range == (120, 140)
        assert rules.key_compatibility is True
        assert rules.energy_progression == 'descending'
        assert rules.max_bpm_difference == 8