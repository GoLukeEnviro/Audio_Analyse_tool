"""Rule Engine - Verarbeitung und Anwendung von Playlist-Regeln"""

from typing import Dict, List, Any, Optional, Callable
import json
import os


class RuleEngine:
    """Engine für die Verarbeitung von Playlist-Regeln"""
    
    def __init__(self):
        self.rules = {}
        self.filters = {}
        self.validators = {}
        self.setup_default_rules()
        
    def setup_default_rules(self):
        """Setup der Standard-Regeln und Filter"""
        
        # BPM-Filter
        self.add_filter('bpm_range', self._filter_bpm_range)
        self.add_filter('bpm_tolerance', self._filter_bpm_tolerance)
        
        # Energie-Filter
        self.add_filter('energy_min', self._filter_energy_min)
        self.add_filter('energy_max', self._filter_energy_max)
        self.add_filter('energy_range', self._filter_energy_range)
        
        # Stimmungs-Filter
        self.add_filter('moods', self._filter_moods)
        self.add_filter('mood_compatibility', self._filter_mood_compatibility)
        
        # Tonart-Filter
        self.add_filter('key_compatibility', self._filter_key_compatibility)
        self.add_filter('camelot_compatible', self._filter_camelot_compatible)
        
        # Dauer-Filter
        self.add_filter('duration_min', self._filter_duration_min)
        self.add_filter('duration_max', self._filter_duration_max)
        
        # Qualitäts-Filter
        self.add_filter('min_quality', self._filter_min_quality)
        
        # Validators
        self.add_validator('bpm_range', self._validate_bpm_range)
        self.add_validator('energy_range', self._validate_energy_range)
        self.add_validator('moods', self._validate_moods)
        
    def add_filter(self, name: str, filter_func: Callable):
        """Fügt einen neuen Filter hinzu"""
        self.filters[name] = filter_func
        
    def add_validator(self, name: str, validator_func: Callable):
        """Fügt einen neuen Validator hinzu"""
        self.validators[name] = validator_func
        
    def validate_rules(self, rules: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validiert Regel-Parameter"""
        errors = {}
        
        for rule_name, rule_value in rules.items():
            if rule_name in self.validators:
                try:
                    validation_errors = self.validators[rule_name](rule_value)
                    if validation_errors:
                        errors[rule_name] = validation_errors
                except Exception as e:
                    errors[rule_name] = [f"Validation error: {str(e)}"]
        
        return errors
        
    def apply_rules(self, tracks: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Wendet Regeln auf eine Track-Liste an"""
        # Validiere Regeln
        validation_errors = self.validate_rules(rules)
        if validation_errors:
            print(f"Rule validation errors: {validation_errors}")
            # Verwende nur gültige Regeln
            rules = {k: v for k, v in rules.items() if k not in validation_errors}
        
        filtered_tracks = tracks.copy()
        
        # Wende jeden Filter an
        for rule_name, rule_value in rules.items():
            if rule_name in self.filters and rule_value is not None:
                try:
                    filtered_tracks = self.filters[rule_name](filtered_tracks, rule_value, rules)
                except Exception as e:
                    print(f"Error applying filter {rule_name}: {e}")
                    continue
        
        return filtered_tracks
    
    def get_matching_count(self, tracks: List[Dict[str, Any]], rules: Dict[str, Any]) -> int:
        """Gibt die Anzahl der Tracks zurück, die den Regeln entsprechen"""
        return len(self.apply_rules(tracks, rules))
    
    # Filter-Implementierungen
    
    def _filter_bpm_range(self, tracks: List[Dict[str, Any]], bpm_range: List[float], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach BPM-Bereich"""
        if not isinstance(bpm_range, (list, tuple)) or len(bpm_range) != 2:
            return tracks
        
        min_bpm, max_bpm = bpm_range
        return [track for track in tracks 
                if min_bpm <= track.get('bpm', 0) <= max_bpm]
    
    def _filter_bpm_tolerance(self, tracks: List[Dict[str, Any]], tolerance: float, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach BPM-Toleranz um einen Ziel-BPM"""
        target_bpm = rules.get('target_bpm')
        if target_bpm is None:
            return tracks
        
        return [track for track in tracks 
                if abs(track.get('bpm', 0) - target_bpm) <= tolerance]
    
    def _filter_energy_min(self, tracks: List[Dict[str, Any]], min_energy: float, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Mindest-Energie"""
        return [track for track in tracks 
                if track.get('energy', 0) >= min_energy]
    
    def _filter_energy_max(self, tracks: List[Dict[str, Any]], max_energy: float, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Maximal-Energie"""
        return [track for track in tracks 
                if track.get('energy', 1) <= max_energy]
    
    def _filter_energy_range(self, tracks: List[Dict[str, Any]], energy_range: List[float], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Energie-Bereich"""
        if not isinstance(energy_range, (list, tuple)) or len(energy_range) != 2:
            return tracks
        
        min_energy, max_energy = energy_range
        return [track for track in tracks 
                if min_energy <= track.get('energy', 0) <= max_energy]
    
    def _filter_moods(self, tracks: List[Dict[str, Any]], allowed_moods: List[str], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach erlaubten Stimmungen"""
        if not allowed_moods:
            return tracks
        
        return [track for track in tracks 
                if track.get('mood') in allowed_moods]
    
    def _filter_mood_compatibility(self, tracks: List[Dict[str, Any]], compatibility_level: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Stimmungs-Kompatibilität"""
        target_mood = rules.get('target_mood')
        if not target_mood:
            return tracks
        
        if compatibility_level == 'exact':
            return [track for track in tracks if track.get('mood') == target_mood]
        elif compatibility_level == 'similar':
            # Definiere ähnliche Stimmungen
            mood_groups = {
                'Euphoric': ['Euphoric', 'Driving'],
                'Dark': ['Dark', 'Experimental'],
                'Driving': ['Driving', 'Euphoric'],
                'Experimental': ['Experimental', 'Dark']
            }
            
            compatible_moods = mood_groups.get(target_mood, [target_mood])
            return [track for track in tracks if track.get('mood') in compatible_moods]
        
        return tracks
    
    def _filter_key_compatibility(self, tracks: List[Dict[str, Any]], compatibility_type: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Tonart-Kompatibilität"""
        if compatibility_type == 'any':
            return tracks
        
        target_key = rules.get('target_key') or rules.get('start_key')
        if not target_key or target_key == 'Auto':
            return tracks
        
        if compatibility_type == 'same':
            return [track for track in tracks if track.get('key') == target_key]
        elif compatibility_type == 'camelot_compatible':
            return self._filter_camelot_compatible(tracks, target_key, rules)
        
        return tracks
    
    def _filter_camelot_compatible(self, tracks: List[Dict[str, Any]], target_key: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Camelot Wheel-Kompatibilität"""
        from .camelot_wheel import CamelotWheel
        
        camelot = CamelotWheel()
        target_camelot = camelot.key_to_camelot(target_key)
        
        if not target_camelot:
            return tracks
        
        compatible_tracks = []
        for track in tracks:
            track_key = track.get('key')
            if not track_key:
                continue
            
            track_camelot = camelot.key_to_camelot(track_key)
            if track_camelot and camelot.are_compatible(target_camelot, track_camelot):
                compatible_tracks.append(track)
        
        return compatible_tracks
    
    def _filter_duration_min(self, tracks: List[Dict[str, Any]], min_duration: float, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Mindest-Dauer"""
        return [track for track in tracks 
                if track.get('duration', 0) >= min_duration]
    
    def _filter_duration_max(self, tracks: List[Dict[str, Any]], max_duration: float, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Maximal-Dauer"""
        return [track for track in tracks 
                if track.get('duration', float('inf')) <= max_duration]
    
    def _filter_min_quality(self, tracks: List[Dict[str, Any]], min_quality: float, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filtert Tracks nach Mindest-Qualität"""
        return [track for track in tracks 
                if track.get('quality_score', 1.0) >= min_quality]
    
    # Validator-Implementierungen
    
    def _validate_bpm_range(self, bpm_range: Any) -> List[str]:
        """Validiert BPM-Bereich"""
        errors = []
        
        if not isinstance(bpm_range, (list, tuple)):
            errors.append("BPM range must be a list or tuple")
            return errors
        
        if len(bpm_range) != 2:
            errors.append("BPM range must contain exactly 2 values")
            return errors
        
        min_bpm, max_bpm = bpm_range
        
        if not isinstance(min_bpm, (int, float)) or not isinstance(max_bpm, (int, float)):
            errors.append("BPM values must be numbers")
        
        if min_bpm < 60 or max_bpm > 200:
            errors.append("BPM values must be between 60 and 200")
        
        if min_bpm >= max_bpm:
            errors.append("Min BPM must be less than Max BPM")
        
        return errors
    
    def _validate_energy_range(self, energy_range: Any) -> List[str]:
        """Validiert Energie-Bereich"""
        errors = []
        
        if not isinstance(energy_range, (list, tuple)):
            errors.append("Energy range must be a list or tuple")
            return errors
        
        if len(energy_range) != 2:
            errors.append("Energy range must contain exactly 2 values")
            return errors
        
        min_energy, max_energy = energy_range
        
        if not isinstance(min_energy, (int, float)) or not isinstance(max_energy, (int, float)):
            errors.append("Energy values must be numbers")
        
        if min_energy < 0.0 or max_energy > 1.0:
            errors.append("Energy values must be between 0.0 and 1.0")
        
        if min_energy >= max_energy:
            errors.append("Min energy must be less than Max energy")
        
        return errors
    
    def _validate_moods(self, moods: Any) -> List[str]:
        """Validiert Stimmungs-Liste"""
        errors = []
        
        if not isinstance(moods, list):
            errors.append("Moods must be a list")
            return errors
        
        valid_moods = ['Euphoric', 'Dark', 'Driving', 'Experimental']
        
        for mood in moods:
            if mood not in valid_moods:
                errors.append(f"Invalid mood '{mood}'. Valid moods: {valid_moods}")
        
        return errors
    
    def create_rule_set(self, name: str, rules: Dict[str, Any]) -> bool:
        """Erstellt ein neues Regel-Set"""
        validation_errors = self.validate_rules(rules)
        if validation_errors:
            print(f"Cannot create rule set '{name}': {validation_errors}")
            return False
        
        self.rules[name] = rules.copy()
        return True
    
    def get_rule_set(self, name: str) -> Optional[Dict[str, Any]]:
        """Gibt ein Regel-Set zurück"""
        return self.rules.get(name, {}).copy()
    
    def list_rule_sets(self) -> List[str]:
        """Gibt eine Liste aller Regel-Sets zurück"""
        return list(self.rules.keys())
    
    def save_rule_sets(self, file_path: str) -> bool:
        """Speichert alle Regel-Sets in eine Datei"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving rule sets: {e}")
            return False
    
    def load_rule_sets(self, file_path: str) -> bool:
        """Lädt Regel-Sets aus einer Datei"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_rules = json.load(f)
                
                # Validiere alle geladenen Regel-Sets
                for name, rules in loaded_rules.items():
                    validation_errors = self.validate_rules(rules)
                    if not validation_errors:
                        self.rules[name] = rules
                    else:
                        print(f"Skipping invalid rule set '{name}': {validation_errors}")
                
                return True
        except Exception as e:
            print(f"Error loading rule sets: {e}")
        
        return False
    
    def get_filter_info(self) -> Dict[str, str]:
        """Gibt Informationen über verfügbare Filter zurück"""
        return {
            'bpm_range': 'Filter tracks by BPM range [min, max]',
            'bpm_tolerance': 'Filter tracks within BPM tolerance of target',
            'energy_min': 'Filter tracks with minimum energy level',
            'energy_max': 'Filter tracks with maximum energy level',
            'energy_range': 'Filter tracks by energy range [min, max]',
            'moods': 'Filter tracks by allowed moods list',
            'mood_compatibility': 'Filter tracks by mood compatibility level',
            'key_compatibility': 'Filter tracks by key compatibility type',
            'camelot_compatible': 'Filter tracks compatible with Camelot Wheel',
            'duration_min': 'Filter tracks with minimum duration',
            'duration_max': 'Filter tracks with maximum duration',
            'min_quality': 'Filter tracks with minimum quality score'
        }