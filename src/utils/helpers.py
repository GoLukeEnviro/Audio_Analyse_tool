import os
import json
from typing import Dict, List, Optional, Union
from pathlib import Path
import hashlib
import time

class ConfigManager:
    def __init__(self, config_file: str = "config/app_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        default_config = {
            "analysis": {
                "cache_enabled": True,
                "max_duration": 120,
                "sample_rate": 22050,
                "hop_length": 512
            },
            "gui": {
                "theme": "dark",
                "window_size": [1400, 900],
                "auto_save": True
            },
            "export": {
                "default_format": "m3u",
                "include_metadata": True,
                "relative_paths": True
            },
            "playlist": {
                "max_tracks": 100,
                "default_sort": "bpm_ascending",
                "energy_threshold": 0.5
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                return self._merge_configs(default_config, loaded_config)
            except (json.JSONDecodeError, IOError):
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Optional[Dict] = None):
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError:
            pass
    
    def get(self, key_path: str, default=None):
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value):
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

class FileUtils:
    @staticmethod
    def get_audio_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
        if extensions is None:
            extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.aiff', '.aif']
        
        audio_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in extensions:
                    audio_files.append(os.path.join(root, file))
        
        return sorted(audio_files)
    
    @staticmethod
    def get_file_hash(file_path: str) -> str:
        return hashlib.md5(file_path.encode()).hexdigest()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

class CamelotWheel:
    # Complete Camelot Wheel mapping
    WHEEL_MAPPING = {
        # Major keys
        'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 'B': '1B',
        'F#': '2B', 'Gb': '2B', 'C#': '3B', 'Db': '3B', 'G#': '4B', 'Ab': '4B',
        'D#': '5B', 'Eb': '5B', 'A#': '6B', 'Bb': '6B', 'F': '7B',
        
        # Minor keys
        'Am': '8A', 'Em': '9A', 'Bm': '10A', 'F#m': '11A', 'Gbm': '11A',
        'C#m': '12A', 'Dbm': '12A', 'G#m': '1A', 'Abm': '1A', 'D#m': '2A',
        'Ebm': '2A', 'A#m': '3A', 'Bbm': '3A', 'Fm': '4A', 'Cm': '5A',
        'Gm': '6A', 'Dm': '7A'
    }
    
    # Reverse mapping
    REVERSE_MAPPING = {v: k for k, v in WHEEL_MAPPING.items()}
    
    @classmethod
    def get_camelot(cls, key: str) -> str:
        return cls.WHEEL_MAPPING.get(key, 'Unknown')
    
    @classmethod
    def get_key(cls, camelot: str) -> str:
        return cls.REVERSE_MAPPING.get(camelot, 'Unknown')
    
    @classmethod
    def get_compatible_keys(cls, camelot: str) -> List[str]:
        if not camelot or camelot == 'Unknown':
            return []
        
        try:
            number = int(camelot[:-1])
            letter = camelot[-1]
            
            compatible = [camelot]  # Same key
            
            # Adjacent keys (±1)
            next_num = (number % 12) + 1
            prev_num = ((number - 2) % 12) + 1
            
            compatible.extend([
                f"{next_num}{letter}",
                f"{prev_num}{letter}"
            ])
            
            # Relative major/minor
            other_letter = 'A' if letter == 'B' else 'B'
            compatible.append(f"{number}{other_letter}")
            
            return compatible
            
        except (ValueError, IndexError):
            return [camelot]
    
    @classmethod
    def calculate_key_distance(cls, key1: str, key2: str) -> int:
        camelot1 = cls.get_camelot(key1)
        camelot2 = cls.get_camelot(key2)
        
        if camelot1 == 'Unknown' or camelot2 == 'Unknown':
            return 12  # Maximum distance
        
        try:
            num1 = int(camelot1[:-1])
            num2 = int(camelot2[:-1])
            letter1 = camelot1[-1]
            letter2 = camelot2[-1]
            
            # Same key
            if camelot1 == camelot2:
                return 0
            
            # Relative major/minor
            if num1 == num2 and letter1 != letter2:
                return 1
            
            # Adjacent keys
            distance = min(abs(num1 - num2), 12 - abs(num1 - num2))
            
            # Add penalty for different mode (major/minor)
            if letter1 != letter2:
                distance += 1
            
            return distance
            
        except (ValueError, IndexError):
            return 12

class MoodAnalyzer:
    @staticmethod
    def calculate_mood_score(track_mood: Dict[str, float], target_moods: Dict[str, float]) -> float:
        if not track_mood or not target_moods:
            return 0.0
        
        score = 0.0
        total_weight = 0.0
        
        for mood_type, weight in target_moods.items():
            if mood_type in track_mood:
                score += track_mood[mood_type] * weight
                total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def get_dominant_mood(track_mood: Dict[str, float]) -> str:
        if not track_mood:
            return 'Unknown'
        
        return max(track_mood.items(), key=lambda x: x[1])[0]
    
    @staticmethod
    def mood_compatibility(mood1: Dict[str, float], mood2: Dict[str, float]) -> float:
        if not mood1 or not mood2:
            return 0.0
        
        # Calculate cosine similarity between mood vectors
        common_moods = set(mood1.keys()) & set(mood2.keys())
        
        if not common_moods:
            return 0.0
        
        dot_product = sum(mood1[mood] * mood2[mood] for mood in common_moods)
        
        magnitude1 = sum(mood1[mood] ** 2 for mood in common_moods) ** 0.5
        magnitude2 = sum(mood2[mood] ** 2 for mood in common_moods) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)

class Logger:
    def __init__(self, log_file: str = "data/app.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, level: str, message: str):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level.upper()}: {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except IOError:
            pass
        
        # Also print to console
        print(log_entry.strip())
    
    def info(self, message: str):
        self.log('INFO', message)
    
    def warning(self, message: str):
        self.log('WARNING', message)
    
    def error(self, message: str):
        self.log('ERROR', message)
    
    def debug(self, message: str):
        self.log('DEBUG', message)

# Global instances
config_manager = ConfigManager()
logger = Logger()