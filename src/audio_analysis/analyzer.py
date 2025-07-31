import os
import json
import librosa
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path
import hashlib

class AudioAnalyzer:
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Camelot Wheel mapping
        self.camelot_wheel = {
            'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B', 'E': '12B', 'B': '1B',
            'F#': '2B', 'C#': '3B', 'G#': '4B', 'D#': '5B', 'A#': '6B', 'F': '7B',
            'Am': '8A', 'Em': '9A', 'Bm': '10A', 'F#m': '11A', 'C#m': '12A', 'G#m': '1A',
            'D#m': '2A', 'A#m': '3A', 'Fm': '4A', 'Cm': '5A', 'Gm': '6A', 'Dm': '7A'
        }
    
    def get_cache_path(self, file_path: str) -> Path:
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.json"
    
    def load_cached_analysis(self, file_path: str) -> Optional[Dict]:
        cache_path = self.get_cache_path(file_path)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def save_analysis_cache(self, file_path: str, analysis: Dict):
        cache_path = self.get_cache_path(file_path)
        try:
            with open(cache_path, 'w') as f:
                json.dump(analysis, f, indent=2)
        except IOError:
            pass
    
    def estimate_key(self, y: np.ndarray, sr: int) -> Tuple[str, str]:
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Key templates (Krumhansl-Schmuckler)
        major_template = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_template = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        major_correlations = []
        minor_correlations = []
        
        for i in range(12):
            major_shifted = np.roll(major_template, i)
            minor_shifted = np.roll(minor_template, i)
            
            major_corr = np.corrcoef(chroma_mean, major_shifted)[0, 1]
            minor_corr = np.corrcoef(chroma_mean, minor_shifted)[0, 1]
            
            major_correlations.append(major_corr)
            minor_correlations.append(minor_corr)
        
        max_major_idx = np.argmax(major_correlations)
        max_minor_idx = np.argmax(minor_correlations)
        
        if major_correlations[max_major_idx] > minor_correlations[max_minor_idx]:
            key = key_names[max_major_idx]
            mode = 'major'
        else:
            key = key_names[max_minor_idx] + 'm'
            mode = 'minor'
        
        camelot = self.camelot_wheel.get(key, 'Unknown')
        return key, camelot
    
    def estimate_energy(self, y: np.ndarray) -> float:
        rms = librosa.feature.rms(y=y)
        return float(np.mean(rms))
    
    def estimate_brightness(self, y: np.ndarray, sr: int) -> float:
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        return float(np.mean(spectral_centroids))
    
    def estimate_mood(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        # Simplified mood estimation based on audio features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
        
        # Calculate mood indicators
        energy = self.estimate_energy(y)
        brightness = self.estimate_brightness(y, sr)
        
        # Normalize values to 0-1 range
        energy_norm = min(energy * 1000, 1.0)
        brightness_norm = min(brightness / 5000, 1.0)
        zcr_norm = min(np.mean(zero_crossing_rate) * 100, 1.0)
        
        # Mood mapping
        euphoric = (energy_norm + brightness_norm) / 2
        dark = 1 - brightness_norm
        driving = energy_norm * zcr_norm
        experimental = np.std(mfccs) / 50  # High variance indicates experimental
        
        return {
            'euphoric': float(euphoric),
            'dark': float(dark),
            'driving': float(driving),
            'experimental': float(min(experimental, 1.0))
        }
    
    def analyze_track(self, file_path: str, progress_callback=None) -> Dict:
        # Check cache first
        cached = self.load_cached_analysis(file_path)
        if cached:
            return cached
        
        try:
            if progress_callback:
                progress_callback(f"Loading {os.path.basename(file_path)}...")
            
            # Load audio file
            y, sr = librosa.load(file_path, duration=120)  # Analyze first 2 minutes
            
            if progress_callback:
                progress_callback("Analyzing tempo...")
            
            # Tempo estimation
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            if progress_callback:
                progress_callback("Analyzing key...")
            
            # Key estimation
            key, camelot = self.estimate_key(y, sr)
            
            if progress_callback:
                progress_callback("Analyzing audio features...")
            
            # Audio features
            energy = self.estimate_energy(y)
            brightness = self.estimate_brightness(y, sr)
            mood = self.estimate_mood(y, sr)
            
            # File metadata
            file_stats = os.stat(file_path)
            
            analysis = {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'file_size': file_stats.st_size,
                'duration': len(y) / sr,
                'bpm': float(tempo),
                'key': key,
                'camelot': camelot,
                'energy': energy,
                'brightness': brightness,
                'mood': mood,
                'analyzed_at': file_stats.st_mtime
            }
            
            # Cache the results
            self.save_analysis_cache(file_path, analysis)
            
            return analysis
            
        except Exception as e:
            return {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'error': str(e),
                'analyzed_at': None
            }
    
    def analyze_directory(self, directory: str, progress_callback=None) -> list:
        audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac'}
        results = []
        
        audio_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in audio_extensions:
                    audio_files.append(os.path.join(root, file))
        
        total_files = len(audio_files)
        
        for i, file_path in enumerate(audio_files):
            if progress_callback:
                progress_callback(f"Processing {i+1}/{total_files}: {os.path.basename(file_path)}")
            
            result = self.analyze_track(file_path)
            results.append(result)
        
        return results