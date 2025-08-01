"""Feature Extractor - Extraktion von Audio-Features mit librosa"""

import librosa
import numpy as np
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')
try:
    from .essentia_integration import get_essentia_integration, is_essentia_available
except ImportError:
    def get_essentia_integration():
        return None
    def is_essentia_available():
        return False


class FeatureExtractor:
    """Klasse für die Extraktion von Audio-Features"""
    
    def __init__(self, sample_rate: int = 22050, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.essentia = get_essentia_integration()
        
        # Configure Essentia algorithms if available
        if is_essentia_available():
            self.essentia.configure_algorithms({
                'beat_tracker': {
                    'maxTempo': 200,
                    'minTempo': 60
                },
                'key_extractor': {
                    'profileType': 'temperley'
                }
            })
    
    def extract_bpm(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Extract BPM from audio data using Essentia with librosa fallback"""
        try:
            # Try Essentia first if available
            if is_essentia_available():
                bpm = self.essentia.extract_bpm(audio_data, sample_rate)
                if bpm is not None:
                    return bpm
            
            # Fallback to librosa
            tempo = librosa.beat.tempo(y=audio_data, sr=sample_rate)
            return float(tempo[0]) if len(tempo) > 0 else 120.0
        except Exception as e:
            print(f"Error extracting BPM: {e}")
            return 120.0
    
    def extract_key(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Extract musical key from audio data using Essentia with librosa fallback"""
        try:
            # Try Essentia first if available
            if is_essentia_available():
                key, scale, strength = self.essentia.extract_key(audio_data, sample_rate)
                if key and scale:
                    return f"{key} {scale}"
            
            # Fallback to librosa
            # Extract chroma features
            chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sample_rate)
            
            # Calculate mean chroma
            chroma_mean = np.mean(chroma, axis=1)
            
            # Key templates (simplified)
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            # Find the key with maximum correlation
            key_idx = np.argmax(chroma_mean)
            
            # Simple major/minor detection (placeholder)
            scale = 'major' if chroma_mean[key_idx] > np.mean(chroma_mean) else 'minor'
            
            return f"{key_names[key_idx]} {scale}"
        except Exception as e:
            print(f"Error extracting key: {e}")
            return "C major"
    
    def extract_energy_level(self, audio_data: np.ndarray) -> float:
        """Extract energy level from audio data"""
        try:
            rms = librosa.feature.rms(y=audio_data)[0]
            return float(np.mean(rms))
        except Exception as e:
            print(f"Error extracting energy level: {e}")
            return 0.5
    
    def extract_spectral_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Extract spectral features from audio data"""
        try:
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)
            
            return {
                'spectral_centroid': float(np.mean(spectral_centroid)),
                'spectral_rolloff': float(np.mean(spectral_rolloff)),
                'spectral_bandwidth': float(np.mean(spectral_bandwidth))
            }
        except Exception as e:
            print(f"Error extracting spectral features: {e}")
            return {
                'spectral_centroid': 2000.0,
                'spectral_rolloff': 4000.0,
                'spectral_bandwidth': 1000.0
            }
    
    def extract_mfcc_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Extract MFCC features from audio data"""
        try:
            mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
            return {
                'mfcc': np.mean(mfcc, axis=1).tolist()
            }
        except Exception as e:
            print(f"Error extracting MFCC features: {e}")
            return {
                'mfcc': [0.0] * 13
            }
        
    def extract_all_features(self, audio_path: str, duration: Optional[float] = None) -> Dict[str, Any]:
        """Extrahiert alle verfügbaren Features aus einer Audio-Datei"""
        try:
            # Audio laden
            y, sr = librosa.load(audio_path, sr=self.sample_rate, duration=duration)
            
            if len(y) == 0:
                raise ValueError("Audio file is empty or corrupted")
            
            features = {}
            
            # Basis-Features
            features.update(self.extract_basic_features(y, sr))
            
            # Rhythmus-Features
            features.update(self.extract_rhythm_features(y, sr))
            
            # Harmonische Features
            features.update(self.extract_harmonic_features(y, sr))
            
            # Spektrale Features
            features.update(self.extract_spectral_features(y, sr))
            
            # Timbre-Features
            features.update(self.extract_timbre_features(y, sr))
            
            return features
            
        except Exception as e:
            print(f"Error extracting features from {audio_path}: {e}")
            return {}
    
    def extract_basic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert grundlegende Audio-Features"""
        features = {}
        
        try:
            # Dauer
            features['duration'] = len(y) / sr
            
            # RMS Energy
            rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
            features['rms_mean'] = float(np.mean(rms))
            features['rms_std'] = float(np.std(rms))
            features['energy'] = features['rms_mean']  # Alias für Kompatibilität
            
            # Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(y, hop_length=self.hop_length)[0]
            features['zcr_mean'] = float(np.mean(zcr))
            features['zcr_std'] = float(np.std(zcr))
            
        except Exception as e:
            print(f"Error extracting basic features: {e}")
            
        return features
    
    def extract_rhythm_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert rhythmische Features"""
        features = {}
        
        try:
            # Tempo/BPM - Try Essentia first if available
            if is_essentia_available():
                essentia_bpm = self.essentia.extract_bpm(y, sr)
                if essentia_bpm is not None:
                    features['bpm'] = float(essentia_bpm)
                    # Still get beats for other calculations
                    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
                else:
                    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
                    features['bpm'] = float(tempo)
            else:
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
                features['bpm'] = float(tempo)
            features['beat_count'] = len(beats)
            
            # Onset Detection
            onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=self.hop_length)
            features['onset_count'] = len(onset_frames)
            features['onset_rate'] = len(onset_frames) / (len(y) / sr)  # Onsets pro Sekunde
            
            # Rhythmic Regularity
            if len(beats) > 1:
                beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=self.hop_length)
                beat_intervals = np.diff(beat_times)
                features['beat_regularity'] = float(1.0 / (np.std(beat_intervals) + 1e-6))
            else:
                features['beat_regularity'] = 0.0
                
        except Exception as e:
            print(f"Error extracting rhythm features: {e}")
            features.update({
                'bpm': 120.0,  # Default BPM
                'beat_count': 0,
                'onset_count': 0,
                'onset_rate': 0.0,
                'beat_regularity': 0.0
            })
            
        return features
    
    def extract_harmonic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert harmonische Features"""
        features = {}
        
        try:
            # Try Essentia key extraction first
            if is_essentia_available():
                key, scale, strength = self.essentia.extract_key(y, sr)
                if key and scale:
                    features['detected_key'] = f"{key} {scale}"
                    features['key_strength'] = float(strength) if strength else 0.0
            
            # Chroma Features für Tonart-Erkennung
            chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=self.hop_length)
            features['chroma_mean'] = chroma.mean(axis=1).tolist()
            features['chroma_std'] = chroma.std(axis=1).tolist()
            
            # Harmonic-Percussive Separation
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            # Harmonic Ratio
            harmonic_energy = np.sum(y_harmonic ** 2)
            total_energy = np.sum(y ** 2)
            features['harmonic_ratio'] = float(harmonic_energy / (total_energy + 1e-6))
            
            # Percussive Ratio
            percussive_energy = np.sum(y_percussive ** 2)
            features['percussive_ratio'] = float(percussive_energy / (total_energy + 1e-6))
            
        except Exception as e:
            print(f"Error extracting harmonic features: {e}")
            features.update({
                'chroma_mean': [0.0] * 12,
                'chroma_std': [0.0] * 12,
                'harmonic_ratio': 0.5,
                'percussive_ratio': 0.5
            })
            
        return features
    
    def extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert spektrale Features"""
        features = {}
        
        try:
            # Spectral Centroid (Helligkeit)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=self.hop_length)[0]
            features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
            features['spectral_centroid_std'] = float(np.std(spectral_centroids))
            features['brightness'] = features['spectral_centroid_mean'] / (sr / 2)  # Normalisiert
            
            # Spectral Rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=self.hop_length)[0]
            features['spectral_rolloff_mean'] = float(np.mean(spectral_rolloff))
            features['spectral_rolloff_std'] = float(np.std(spectral_rolloff))
            
            # Spectral Bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=self.hop_length)[0]
            features['spectral_bandwidth_mean'] = float(np.mean(spectral_bandwidth))
            features['spectral_bandwidth_std'] = float(np.std(spectral_bandwidth))
            
            # Spectral Contrast
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=self.hop_length)
            features['spectral_contrast_mean'] = spectral_contrast.mean(axis=1).tolist()
            features['spectral_contrast_std'] = spectral_contrast.std(axis=1).tolist()
            
        except Exception as e:
            print(f"Error extracting spectral features: {e}")
            features.update({
                'spectral_centroid_mean': 2000.0,
                'spectral_centroid_std': 500.0,
                'brightness': 0.5,
                'spectral_rolloff_mean': 4000.0,
                'spectral_rolloff_std': 1000.0,
                'spectral_bandwidth_mean': 2000.0,
                'spectral_bandwidth_std': 500.0,
                'spectral_contrast_mean': [0.5] * 7,
                'spectral_contrast_std': [0.1] * 7
            })
            
        return features
    
    def extract_timbre_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert Timbre-Features (MFCCs)"""
        features = {}
        
        try:
            # MFCCs (Mel-frequency cepstral coefficients)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=self.hop_length)
            
            # Statistiken für jeden MFCC
            features['mfcc_mean'] = mfccs.mean(axis=1).tolist()
            features['mfcc_std'] = mfccs.std(axis=1).tolist()
            
            # Delta MFCCs (erste Ableitung)
            mfcc_delta = librosa.feature.delta(mfccs)
            features['mfcc_delta_mean'] = mfcc_delta.mean(axis=1).tolist()
            features['mfcc_delta_std'] = mfcc_delta.std(axis=1).tolist()
            
            # Delta-Delta MFCCs (zweite Ableitung)
            mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
            features['mfcc_delta2_mean'] = mfcc_delta2.mean(axis=1).tolist()
            features['mfcc_delta2_std'] = mfcc_delta2.std(axis=1).tolist()
            
        except Exception as e:
            print(f"Error extracting timbre features: {e}")
            features.update({
                'mfcc_mean': [0.0] * 13,
                'mfcc_std': [0.0] * 13,
                'mfcc_delta_mean': [0.0] * 13,
                'mfcc_delta_std': [0.0] * 13,
                'mfcc_delta2_mean': [0.0] * 13,
                'mfcc_delta2_std': [0.0] * 13
            })
            
        return features
    
    def extract_key_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert Features speziell für Tonart-Erkennung"""
        features = {}
        
        try:
            # Chroma Features mit höherer Auflösung
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=self.hop_length)
            
            # Durchschnittliches Chroma-Profil
            chroma_profile = np.mean(chroma, axis=1)
            features['chroma_profile'] = chroma_profile.tolist()
            
            # Chroma-Energie pro Tonklasse
            features['chroma_energy'] = {
                'C': float(chroma_profile[0]),
                'C#': float(chroma_profile[1]),
                'D': float(chroma_profile[2]),
                'D#': float(chroma_profile[3]),
                'E': float(chroma_profile[4]),
                'F': float(chroma_profile[5]),
                'F#': float(chroma_profile[6]),
                'G': float(chroma_profile[7]),
                'G#': float(chroma_profile[8]),
                'A': float(chroma_profile[9]),
                'A#': float(chroma_profile[10]),
                'B': float(chroma_profile[11])
            }
            
            # Dominante Tonklasse
            dominant_pitch_class = np.argmax(chroma_profile)
            pitch_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            features['dominant_pitch_class'] = pitch_names[dominant_pitch_class]
            
        except Exception as e:
            print(f"Error extracting key features: {e}")
            features.update({
                'chroma_profile': [0.0] * 12,
                'chroma_energy': {note: 0.0 for note in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']},
                'dominant_pitch_class': 'C'
            })
            
        return features
    
    def extract_mood_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extrahiert Features für Stimmungs-Analyse"""
        features = {}
        
        try:
            # Dynamik-Features
            rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
            features['dynamic_range'] = float(np.max(rms) - np.min(rms))
            features['dynamic_variance'] = float(np.var(rms))
            
            # Spektrale Features für Stimmung
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=self.hop_length)[0]
            features['brightness_variance'] = float(np.var(spectral_centroids))
            
            # Harmonicity
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            harmonic_energy = np.sum(y_harmonic ** 2)
            total_energy = np.sum(y ** 2)
            features['harmonicity'] = float(harmonic_energy / (total_energy + 1e-6))
            
            # Roughness (basierend auf spektraler Irregularität)
            stft = librosa.stft(y, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            spectral_irregularity = np.mean(np.diff(magnitude, axis=0) ** 2)
            features['roughness'] = float(spectral_irregularity)
            
        except Exception as e:
            print(f"Error extracting mood features: {e}")
            features.update({
                'dynamic_range': 0.5,
                'dynamic_variance': 0.1,
                'brightness_variance': 1000.0,
                'harmonicity': 0.5,
                'roughness': 0.1
            })
            
        return features
    
    def get_feature_summary(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt eine Zusammenfassung der wichtigsten Features"""
        summary = {}
        
        # Basis-Informationen
        summary['duration'] = features.get('duration', 0.0)
        summary['bpm'] = features.get('bpm', 120.0)
        summary['energy'] = features.get('energy', 0.5)
        summary['brightness'] = features.get('brightness', 0.5)
        
        # Harmonische Informationen
        summary['harmonic_ratio'] = features.get('harmonic_ratio', 0.5)
        summary['dominant_pitch_class'] = features.get('dominant_pitch_class', 'C')
        
        # Rhythmische Informationen
        summary['beat_regularity'] = features.get('beat_regularity', 0.0)
        summary['onset_rate'] = features.get('onset_rate', 0.0)
        
        # Stimmungs-relevante Features
        summary['dynamic_range'] = features.get('dynamic_range', 0.5)
        summary['harmonicity'] = features.get('harmonicity', 0.5)
        summary['roughness'] = features.get('roughness', 0.1)
        
        return summary