import json
import random
from typing import List, Dict, Optional, Callable
from pathlib import Path
import numpy as np

class PlaylistGenerator:
    def __init__(self):
        # Camelot Wheel compatibility mapping
        self.camelot_compatibility = {
            '1A': ['1A', '1B', '2A', '12A'],
            '2A': ['2A', '2B', '3A', '1A'],
            '3A': ['3A', '3B', '4A', '2A'],
            '4A': ['4A', '4B', '5A', '3A'],
            '5A': ['5A', '5B', '6A', '4A'],
            '6A': ['6A', '6B', '7A', '5A'],
            '7A': ['7A', '7B', '8A', '6A'],
            '8A': ['8A', '8B', '9A', '7A'],
            '9A': ['9A', '9B', '10A', '8A'],
            '10A': ['10A', '10B', '11A', '9A'],
            '11A': ['11A', '11B', '12A', '10A'],
            '12A': ['12A', '12B', '1A', '11A'],
            '1B': ['1B', '1A', '2B', '12B'],
            '2B': ['2B', '2A', '3B', '1B'],
            '3B': ['3B', '3A', '4B', '2B'],
            '4B': ['4B', '4A', '5B', '3B'],
            '5B': ['5B', '5A', '6B', '4B'],
            '6B': ['6B', '6A', '7B', '5B'],
            '7B': ['7B', '7A', '8B', '6B'],
            '8B': ['8B', '8A', '9B', '7B'],
            '9B': ['9B', '9A', '10B', '8B'],
            '10B': ['10B', '10A', '11B', '9B'],
            '11B': ['11B', '11A', '12B', '10B'],
            '12B': ['12B', '12A', '1B', '11B']
        }
        
        # Preset configurations
        self.presets = {
            'push_push': {
                'name': 'Push-Push',
                'bpm_range': (128, 135),
                'energy_min': 0.6,
                'mood_weights': {'driving': 0.8, 'euphoric': 0.6, 'dark': 0.2, 'experimental': 0.3},
                'sort_by': 'energy_ascending'
            },
            'dark': {
                'name': 'Dark',
                'bpm_range': (120, 130),
                'energy_min': 0.4,
                'mood_weights': {'dark': 0.9, 'driving': 0.5, 'euphoric': 0.1, 'experimental': 0.7},
                'sort_by': 'mood_dark'
            },
            'euphoric': {
                'name': 'Euphoric',
                'bpm_range': (130, 140),
                'energy_min': 0.7,
                'mood_weights': {'euphoric': 0.9, 'driving': 0.6, 'dark': 0.1, 'experimental': 0.2},
                'sort_by': 'energy_ascending'
            },
            'experimental': {
                'name': 'Experimental',
                'bpm_range': (110, 150),
                'energy_min': 0.3,
                'mood_weights': {'experimental': 0.9, 'dark': 0.6, 'driving': 0.4, 'euphoric': 0.3},
                'sort_by': 'experimental'
            },
            'driving': {
                'name': 'Driving',
                'bpm_range': (125, 135),
                'energy_min': 0.6,
                'mood_weights': {'driving': 0.9, 'energy': 0.8, 'euphoric': 0.5, 'dark': 0.3},
                'sort_by': 'bpm_ascending'
            }
        }
    
    def filter_tracks_by_rules(self, tracks: List[Dict], rules: Dict) -> List[Dict]:
        filtered = []
        
        for track in tracks:
            if 'error' in track:
                continue
            
            # BPM filter
            bpm_min = rules.get('bpm_min', 0)
            bpm_max = rules.get('bpm_max', 200)
            if not (bpm_min <= track.get('bpm', 0) <= bpm_max):
                continue
            
            # Energy filter
            energy_min = rules.get('energy_min', 0)
            if track.get('energy', 0) < energy_min:
                continue
            
            # Key compatibility filter
            if 'required_keys' in rules:
                track_camelot = track.get('camelot', '')
                if track_camelot not in rules['required_keys']:
                    continue
            
            # Mood filter
            if 'mood_weights' in rules:
                mood_score = self.calculate_mood_score(track, rules['mood_weights'])
                mood_threshold = rules.get('mood_threshold', 0.5)
                if mood_score < mood_threshold:
                    continue
            
            filtered.append(track)
        
        return filtered
    
    def calculate_mood_score(self, track: Dict, mood_weights: Dict) -> float:
        track_mood = track.get('mood', {})
        score = 0.0
        total_weight = 0.0
        
        for mood_type, weight in mood_weights.items():
            if mood_type in track_mood:
                score += track_mood[mood_type] * weight
                total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def get_compatible_keys(self, start_key: str) -> List[str]:
        return self.camelot_compatibility.get(start_key, [start_key])
    
    def sort_tracks(self, tracks: List[Dict], sort_method: str) -> List[Dict]:
        if sort_method == 'bpm_ascending':
            return sorted(tracks, key=lambda x: x.get('bpm', 0))
        elif sort_method == 'bpm_descending':
            return sorted(tracks, key=lambda x: x.get('bpm', 0), reverse=True)
        elif sort_method == 'energy_ascending':
            return sorted(tracks, key=lambda x: x.get('energy', 0))
        elif sort_method == 'energy_descending':
            return sorted(tracks, key=lambda x: x.get('energy', 0), reverse=True)
        elif sort_method == 'mood_dark':
            return sorted(tracks, key=lambda x: x.get('mood', {}).get('dark', 0), reverse=True)
        elif sort_method == 'mood_euphoric':
            return sorted(tracks, key=lambda x: x.get('mood', {}).get('euphoric', 0), reverse=True)
        elif sort_method == 'experimental':
            return sorted(tracks, key=lambda x: x.get('mood', {}).get('experimental', 0), reverse=True)
        elif sort_method == 'harmonic_flow':
            return self.sort_by_harmonic_flow(tracks)
        else:
            return tracks
    
    def sort_by_harmonic_flow(self, tracks: List[Dict]) -> List[Dict]:
        if not tracks:
            return tracks
        
        sorted_tracks = [tracks[0]]
        remaining_tracks = tracks[1:]
        
        while remaining_tracks:
            current_key = sorted_tracks[-1].get('camelot', '')
            compatible_keys = self.get_compatible_keys(current_key)
            
            # Find best next track
            best_track = None
            best_score = -1
            
            for track in remaining_tracks:
                track_key = track.get('camelot', '')
                score = 0
                
                # Key compatibility score
                if track_key in compatible_keys:
                    score += 10
                
                # BPM compatibility score (prefer gradual changes)
                current_bpm = sorted_tracks[-1].get('bpm', 120)
                track_bpm = track.get('bpm', 120)
                bpm_diff = abs(current_bpm - track_bpm)
                if bpm_diff <= 5:
                    score += 5
                elif bpm_diff <= 10:
                    score += 2
                
                # Energy flow score
                current_energy = sorted_tracks[-1].get('energy', 0.5)
                track_energy = track.get('energy', 0.5)
                energy_diff = abs(current_energy - track_energy)
                if energy_diff <= 0.1:
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_track = track
            
            if best_track:
                sorted_tracks.append(best_track)
                remaining_tracks.remove(best_track)
            else:
                # If no good match found, add random track
                sorted_tracks.append(remaining_tracks.pop(0))
        
        return sorted_tracks
    
    def generate_playlist(self, tracks: List[Dict], rules: Dict, max_tracks: Optional[int] = None) -> Dict:
        # Filter tracks based on rules
        filtered_tracks = self.filter_tracks_by_rules(tracks, rules)
        
        if not filtered_tracks:
            return {
                'tracks': [],
                'total_duration': 0,
                'avg_bpm': 0,
                'key_distribution': {},
                'mood_profile': {},
                'error': 'No tracks match the specified criteria'
            }
        
        # Sort tracks
        sort_method = rules.get('sort_by', 'bpm_ascending')
        sorted_tracks = self.sort_tracks(filtered_tracks, sort_method)
        
        # Limit number of tracks if specified
        if max_tracks and len(sorted_tracks) > max_tracks:
            sorted_tracks = sorted_tracks[:max_tracks]
        
        # Calculate playlist statistics
        total_duration = sum(track.get('duration', 0) for track in sorted_tracks)
        avg_bpm = np.mean([track.get('bpm', 0) for track in sorted_tracks]) if sorted_tracks else 0
        
        # Key distribution
        key_distribution = {}
        for track in sorted_tracks:
            key = track.get('key', 'Unknown')
            key_distribution[key] = key_distribution.get(key, 0) + 1
        
        # Mood profile
        mood_profile = {'euphoric': 0, 'dark': 0, 'driving': 0, 'experimental': 0}
        for track in sorted_tracks:
            track_mood = track.get('mood', {})
            for mood_type in mood_profile:
                mood_profile[mood_type] += track_mood.get(mood_type, 0)
        
        # Average mood scores
        if sorted_tracks:
            for mood_type in mood_profile:
                mood_profile[mood_type] /= len(sorted_tracks)
        
        return {
            'tracks': sorted_tracks,
            'total_tracks': len(sorted_tracks),
            'total_duration': total_duration,
            'avg_bpm': float(avg_bpm),
            'key_distribution': key_distribution,
            'mood_profile': mood_profile,
            'rules_applied': rules
        }
    
    def generate_from_preset(self, tracks: List[Dict], preset_name: str, max_tracks: Optional[int] = None) -> Dict:
        if preset_name not in self.presets:
            return {'error': f'Preset "{preset_name}" not found'}
        
        preset = self.presets[preset_name]
        
        rules = {
            'bpm_min': preset['bpm_range'][0],
            'bpm_max': preset['bpm_range'][1],
            'energy_min': preset['energy_min'],
            'mood_weights': preset['mood_weights'],
            'mood_threshold': 0.5,
            'sort_by': preset['sort_by']
        }
        
        return self.generate_playlist(tracks, rules, max_tracks)
    
    def suggest_next_tracks(self, current_track: Dict, available_tracks: List[Dict], count: int = 5) -> List[Dict]:
        current_key = current_track.get('camelot', '')
        current_bpm = current_track.get('bpm', 120)
        current_energy = current_track.get('energy', 0.5)
        
        compatible_keys = self.get_compatible_keys(current_key)
        
        scored_tracks = []
        
        for track in available_tracks:
            if track == current_track:
                continue
            
            score = 0
            
            # Key compatibility
            if track.get('camelot', '') in compatible_keys:
                score += 10
            
            # BPM compatibility
            bpm_diff = abs(track.get('bpm', 120) - current_bpm)
            if bpm_diff <= 3:
                score += 8
            elif bpm_diff <= 6:
                score += 5
            elif bpm_diff <= 10:
                score += 2
            
            # Energy flow
            energy_diff = abs(track.get('energy', 0.5) - current_energy)
            if energy_diff <= 0.1:
                score += 5
            elif energy_diff <= 0.2:
                score += 3
            
            scored_tracks.append((track, score))
        
        # Sort by score and return top suggestions
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        return [track for track, score in scored_tracks[:count]]
    
    def save_preset(self, name: str, rules: Dict, file_path: str = "config/custom_presets.json"):
        preset_file = Path(file_path)
        preset_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if preset_file.exists():
                with open(preset_file, 'r') as f:
                    presets = json.load(f)
            else:
                presets = {}
            
            presets[name] = rules
            
            with open(preset_file, 'w') as f:
                json.dump(presets, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def load_custom_presets(self, file_path: str = "config/custom_presets.json") -> Dict:
        preset_file = Path(file_path)
        if preset_file.exists():
            try:
                with open(preset_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}