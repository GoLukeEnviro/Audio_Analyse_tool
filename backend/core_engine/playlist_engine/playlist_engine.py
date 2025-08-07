"""Playlist Engine - Intelligente Playlist-Generierung für Backend"""

import json
import os
import math
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime
import numpy as np
import asyncio

logger = logging.getLogger(__name__)


class SortingAlgorithm(Enum):
    """Verfügbare Sortieralgorithmen"""
    HARMONIC = "harmonic"  # Harmonische Kompatibilität (Camelot Wheel)
    ENERGY_FLOW = "energy_flow"  # Energie-Verlauf
    MOOD_PROGRESSION = "mood_progression"  # Stimmungs-Progression
    BPM_TRANSITION = "bpm_transition"  # BPM-Übergänge
    KEY_PROGRESSION = "key_progression"  # Tonart-Progression
    HYBRID_SMART = "hybrid_smart"  # Intelligente Kombination
    CUSTOM = "custom"  # Benutzerdefiniert


class MoodCategory(Enum):
    """Stimmungskategorien"""
    ENERGETIC = "energetic"
    HAPPY = "happy"
    CALM = "calm"
    MELANCHOLIC = "melancholic"
    AGGRESSIVE = "aggressive"
    ROMANTIC = "romantic"
    MYSTERIOUS = "mysterious"
    UPLIFTING = "uplifting"


@dataclass
class PlaylistRule:
    """Regel für Playlist-Generierung"""
    name: str
    description: str
    weight: float  # Gewichtung 0.0 - 1.0
    enabled: bool = True
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class PlaylistPreset:
    """Preset für Playlist-Konfiguration"""
    name: str
    description: str
    algorithm: SortingAlgorithm
    rules: List[PlaylistRule]
    target_duration_minutes: Optional[int] = None
    energy_curve: str = "gradual_build"  # gradual_build, peak_valley, steady, custom
    mood_flow: str = "coherent"  # coherent, contrasting, mixed
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class PlaylistEngine:
    """Erweiterte Playlist-Engine mit intelligenten Sortieralgorithmen für headless Backend"""
    
    def __init__(self, presets_dir: str = "data/presets"):
        self.presets_dir = presets_dir
        self._ensure_presets_dir()
        
        # Standard-Presets
        self.default_presets = self._create_default_presets()
        self.custom_presets = self._load_custom_presets()
        
        # Camelot Wheel Kompatibilitäts-Matrix
        self.camelot_compatibility = self._build_camelot_matrix()
        
        # Mood-Kompatibilitäts-Matrix
        self.mood_compatibility = self._build_mood_matrix()
    
    def _ensure_presets_dir(self):
        """Stellt sicher, dass das Presets-Verzeichnis existiert"""
        os.makedirs(self.presets_dir, exist_ok=True)
    
    def _create_default_presets(self) -> List[PlaylistPreset]:
        """Erstellt Standard-Presets für verschiedene DJ-Szenarien"""
        presets = []
        
        # DJ Set - Harmonic Flow
        presets.append(PlaylistPreset(
            name="DJ Set - Harmonic Flow",
            description="Harmonische Übergänge für professionelle DJ-Sets",
            algorithm=SortingAlgorithm.HARMONIC,
            rules=[
                PlaylistRule("camelot_compatibility", "Bevorzuge harmonisch kompatible Keys", 0.8),
                PlaylistRule("bpm_transition", "Sanfte BPM-Übergänge (±5 BPM)", 0.6),
                PlaylistRule("energy_flow", "Gradueller Energie-Aufbau", 0.4),
                PlaylistRule("key_progression", "Quintenzirkel-Progression", 0.7)
            ],
            energy_curve="gradual_build",
            mood_flow="coherent"
        ))
        
        # Party Mix - Energy Build
        presets.append(PlaylistPreset(
            name="Party Mix - Energy Build",
            description="Energie-aufbauende Playlist für Partys",
            algorithm=SortingAlgorithm.ENERGY_FLOW,
            rules=[
                PlaylistRule("energy_progression", "Kontinuierlicher Energie-Aufbau", 0.9),
                PlaylistRule("danceability_priority", "Bevorzuge tanzbare Tracks", 0.8),
                PlaylistRule("bpm_acceleration", "BPM-Steigerung über Zeit", 0.7),
                PlaylistRule("mood_uplifting", "Positive Stimmung bevorzugen", 0.6)
            ],
            energy_curve="gradual_build",
            mood_flow="uplifting",
            target_duration_minutes=60
        ))
        
        # Chill Session
        presets.append(PlaylistPreset(
            name="Chill Session",
            description="Entspannte Playlist für ruhige Momente",
            algorithm=SortingAlgorithm.MOOD_PROGRESSION,
            rules=[
                PlaylistRule("low_energy_priority", "Bevorzuge ruhige Tracks", 0.8),
                PlaylistRule("mood_coherence", "Stimmungs-Kohärenz", 0.9),
                PlaylistRule("tempo_stability", "Stabile BPM (±3 BPM)", 0.7),
                PlaylistRule("valence_consistency", "Konsistente Valence", 0.6)
            ],
            energy_curve="steady",
            mood_flow="coherent",
            target_duration_minutes=45
        ))
        
        # Peak Time
        presets.append(PlaylistPreset(
            name="Peak Time",
            description="Hochenergetische Playlist für Prime Time",
            algorithm=SortingAlgorithm.HYBRID_SMART,
            rules=[
                PlaylistRule("high_energy_only", "Nur hochenergetische Tracks", 0.9),
                PlaylistRule("peak_bpm_range", "BPM 125-135", 0.8),
                PlaylistRule("crowd_favorites", "Bekannte Tracks bevorzugen", 0.7),
                PlaylistRule("harmonic_mixing", "Harmonische Übergänge", 0.6)
            ],
            energy_curve="peak_valley",
            mood_flow="energetic",
            target_duration_minutes=90
        ))
        
        # Warm-Up Set
        presets.append(PlaylistPreset(
            name="Warm-Up Set",
            description="Sanfter Einstieg für Club-Abende",
            algorithm=SortingAlgorithm.BPM_TRANSITION,
            rules=[
                PlaylistRule("gradual_bpm_increase", "Langsamer BPM-Aufbau", 0.8),
                PlaylistRule("low_to_medium_energy", "Von niedriger zu mittlerer Energie", 0.7),
                PlaylistRule("mood_transition", "Von entspannt zu energetisch", 0.6),
                PlaylistRule("harmonic_stability", "Harmonische Stabilität", 0.5)
            ],
            energy_curve="gradual_build",
            mood_flow="building",
            target_duration_minutes=30
        ))
        
        return presets
    
    def _load_custom_presets(self) -> List[PlaylistPreset]:
        """Lädt benutzerdefinierte Presets aus Datei"""
        presets = []
        presets_file = os.path.join(self.presets_dir, "custom_presets.json")
        
        try:
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for preset_data in data.get('presets', []):
                    rules = []
                    for rule_data in preset_data.get('rules', []):
                        rules.append(PlaylistRule(**rule_data))
                    
                    preset_data['rules'] = rules
                    preset_data['algorithm'] = SortingAlgorithm(preset_data['algorithm'])
                    presets.append(PlaylistPreset(**preset_data))
                    
        except Exception as e:
            logger.error(f"Fehler beim Laden der Custom Presets: {e}")
        
        return presets
    
    def _save_custom_presets(self):
        """Speichert benutzerdefinierte Presets in Datei"""
        presets_file = os.path.join(self.presets_dir, "custom_presets.json")
        
        try:
            data = {
                'version': '2.0',
                'created_at': datetime.now().isoformat(),
                'presets': []
            }
            
            for preset in self.custom_presets:
                preset_dict = asdict(preset)
                preset_dict['algorithm'] = preset.algorithm.value
                data['presets'].append(preset_dict)
            
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Custom Presets: {e}")
    
    def _build_camelot_matrix(self) -> Dict[str, List[str]]:
        """Erstellt Camelot-Kompatibilitäts-Matrix für harmonisches Mixing"""
        compatibility = {}
        
        # Alle Camelot-Keys (1A-12A, 1B-12B)
        for i in range(1, 13):
            for letter in ['A', 'B']:
                key = f"{i}{letter}"
                compatible = []
                
                # Gleiche Nummer, andere Modalität (relative Dur/Moll)
                other_letter = 'B' if letter == 'A' else 'A'
                compatible.append(f"{i}{other_letter}")
                
                # +1 und -1 (Quintenzirkel)
                next_num = (i % 12) + 1
                prev_num = ((i - 2) % 12) + 1
                compatible.extend([f"{next_num}{letter}", f"{prev_num}{letter}"])
                
                # Erweiterte Kompatibilität (+2, -2) für flexibleres Mixing
                next2_num = ((i + 1) % 12) + 1
                prev2_num = ((i - 3) % 12) + 1
                compatible.extend([f"{next2_num}{letter}", f"{prev2_num}{letter}"])
                
                compatibility[key] = compatible
        
        return compatibility
    
    def _build_mood_matrix(self) -> Dict[str, Dict[str, float]]:
        """Erstellt Mood-Kompatibilitäts-Matrix für Stimmungsübergänge"""
        mood_scores = {
            'energetic': {
                'energetic': 1.0, 'happy': 0.8, 'uplifting': 0.9, 
                'aggressive': 0.6, 'calm': 0.2, 'melancholic': 0.1, 
                'romantic': 0.3, 'mysterious': 0.4
            },
            'happy': {
                'happy': 1.0, 'energetic': 0.8, 'uplifting': 0.9, 
                'romantic': 0.7, 'calm': 0.6, 'aggressive': 0.3, 
                'melancholic': 0.2, 'mysterious': 0.3
            },
            'calm': {
                'calm': 1.0, 'romantic': 0.8, 'melancholic': 0.6, 
                'mysterious': 0.7, 'happy': 0.6, 'uplifting': 0.4, 
                'energetic': 0.2, 'aggressive': 0.1
            },
            'melancholic': {
                'melancholic': 1.0, 'calm': 0.6, 'mysterious': 0.8, 
                'romantic': 0.5, 'aggressive': 0.3, 'happy': 0.2, 
                'energetic': 0.1, 'uplifting': 0.2
            },
            'aggressive': {
                'aggressive': 1.0, 'energetic': 0.6, 'mysterious': 0.5, 
                'melancholic': 0.3, 'uplifting': 0.2, 'happy': 0.3, 
                'calm': 0.1, 'romantic': 0.1
            },
            'romantic': {
                'romantic': 1.0, 'calm': 0.8, 'happy': 0.7, 
                'melancholic': 0.5, 'mysterious': 0.6, 'uplifting': 0.6, 
                'energetic': 0.3, 'aggressive': 0.1
            },
            'mysterious': {
                'mysterious': 1.0, 'melancholic': 0.8, 'calm': 0.7, 
                'romantic': 0.6, 'aggressive': 0.5, 'energetic': 0.4, 
                'happy': 0.3, 'uplifting': 0.3
            },
            'uplifting': {
                'uplifting': 1.0, 'happy': 0.9, 'energetic': 0.9, 
                'romantic': 0.6, 'calm': 0.4, 'mysterious': 0.3, 
                'melancholic': 0.2, 'aggressive': 0.2
            }
        }
        
        return mood_scores
    
    async def create_playlist_async(self, tracks: List[Dict], preset_name: str = None, 
                                   custom_rules: List[PlaylistRule] = None, 
                                   target_duration: int = None,
                                   progress_callback: Optional[Callable] = None) -> Dict:
        """Erstellt eine optimierte Playlist asynchron"""
        
        if not tracks:
            return {'error': 'Keine Tracks verfügbar'}
        
        if progress_callback:
            await progress_callback("Initialisiere Playlist-Generierung...")
        
        # Preset auswählen
        preset = self._get_preset(preset_name) if preset_name else self.default_presets[0]
        if not preset:
            return {'error': f'Preset "{preset_name}" nicht gefunden'}
        
        # Custom Rules überschreiben Preset-Rules
        rules = custom_rules if custom_rules else preset.rules
        
        if progress_callback:
            await progress_callback("Bereite Tracks vor...")
        
        # Tracks filtern und vorbereiten
        valid_tracks = self._prepare_tracks(tracks)
        if not valid_tracks:
            return {'error': 'Keine gültigen Tracks gefunden'}
        
        if progress_callback:
            await progress_callback(f"Wende {preset.algorithm.value} Algorithmus an...")
        
        # Sortieralgorithmus anwenden
        sorted_tracks = await self._apply_sorting_algorithm_async(valid_tracks, preset.algorithm, rules, progress_callback)
        
        if progress_callback:
            await progress_callback("Optimiere Playlist-Länge...")
        
        # Zieldauer berücksichtigen
        if target_duration or preset.target_duration_minutes:
            duration = target_duration or preset.target_duration_minutes
            sorted_tracks = self._trim_to_duration(sorted_tracks, duration * 60)
        
        if progress_callback:
            await progress_callback("Berechne Playlist-Metadaten...")
        
        # Playlist-Metadaten berechnen
        metadata = self._calculate_playlist_metadata(sorted_tracks, preset)
        
        if progress_callback:
            await progress_callback("Playlist-Generierung abgeschlossen!")
        
        return {
            'tracks': sorted_tracks,
            'metadata': metadata,
            'preset_used': preset.name,
            'algorithm': preset.algorithm.value,
            'rules_applied': [{'name': r.name, 'weight': r.weight} for r in rules if r.enabled],
            'created_at': datetime.now().isoformat(),
            'status': 'completed'
        }
    
    def create_playlist(self, tracks: List[Dict], preset_name: str = None, 
                       custom_rules: List[PlaylistRule] = None, 
                       target_duration: int = None) -> Dict:
        """Synchrone Version der Playlist-Erstellung"""
        return asyncio.run(self.create_playlist_async(tracks, preset_name, custom_rules, target_duration))
    
    def _get_preset(self, name: str) -> Optional[PlaylistPreset]:
        """Findet ein Preset nach Name"""
        all_presets = self.default_presets + self.custom_presets
        return next((p for p in all_presets if p.name == name), None)
    
    def _prepare_tracks(self, tracks: List[Dict]) -> List[Dict]:
        """Bereitet Tracks für die Sortierung vor und normalisiert Features"""
        valid_tracks = []
        
        for track in tracks:
            # Prüfe ob notwendige Features vorhanden sind
            features = track.get('features', {})
            if not features:
                logger.warning(f"Track {track.get('filename', 'unknown')} hat keine Features")
                continue
            
            # Normalisiere und validiere Features
            normalized_track = track.copy()
            normalized_features = self._normalize_features(features)
            normalized_track['features'] = normalized_features
            
            # Berechne abgeleitete Metriken
            normalized_track['derived_metrics'] = self._calculate_derived_metrics(normalized_features)
            
            valid_tracks.append(normalized_track)
        
        logger.info(f"Vorbereitung abgeschlossen: {len(valid_tracks)} von {len(tracks)} Tracks gültig")
        return valid_tracks
    
    def _normalize_features(self, features: Dict) -> Dict:
        """Normalisiert Audio-Features auf 0-1 Bereich"""
        normalized = features.copy()
        
        # Standard-Werte für fehlende Features
        defaults = {
            'energy': 0.5,
            'valence': 0.5,
            'danceability': 0.5,
            'bpm': 120.0,  # Absolute BPM
            'key_numeric': 0.0,
            'mode': 'major',
            'loudness': -10.0  # dB
        }
        
        for key, default_value in defaults.items():
            if key not in normalized:
                normalized[key] = default_value
            else:
                # Normalisiere verschiedene Feature-Typen
                if key in ['energy', 'valence', 'danceability']:
                    normalized[key] = max(0.0, min(1.0, float(normalized[key])))
                elif key == 'bpm':
                    # BPM bleibt absolut für bessere Verarbeitung
                    normalized[key] = max(60.0, min(200.0, float(normalized[key])))
                elif key == 'loudness':
                    # Loudness in dB
                    normalized[key] = max(-60.0, min(0.0, float(normalized[key])))
        
        return normalized
    
    def _calculate_derived_metrics(self, features: Dict) -> Dict:
        """Berechnet abgeleitete Metriken für bessere Playlist-Optimierung"""
        metrics = {}
        
        # Energie-Level Kategorisierung
        energy = features.get('energy', 0.5)
        if energy < 0.3:
            metrics['energy_level'] = 'low'
        elif energy < 0.7:
            metrics['energy_level'] = 'medium'
        else:
            metrics['energy_level'] = 'high'
        
        # BPM-Kategorie
        bpm = features.get('bpm', 120.0)
        if bpm < 90:
            metrics['bpm_category'] = 'slow'
        elif bpm < 120:
            metrics['bpm_category'] = 'medium'
        elif bpm < 140:
            metrics['bpm_category'] = 'fast'
        else:
            metrics['bpm_category'] = 'very_fast'
        
        # Mood-Schätzung basierend auf Features
        valence = features.get('valence', 0.5)
        energy = features.get('energy', 0.5)
        
        if energy > 0.7 and valence > 0.6:
            metrics['estimated_mood'] = 'energetic'
        elif energy < 0.4 and valence > 0.6:
            metrics['estimated_mood'] = 'happy'
        elif energy < 0.4 and valence < 0.4:
            metrics['estimated_mood'] = 'melancholic'
        elif energy > 0.6 and valence < 0.4:
            metrics['estimated_mood'] = 'aggressive'
        else:
            metrics['estimated_mood'] = 'neutral'
        
        # Danceability-Level
        danceability = features.get('danceability', 0.5)
        if danceability > 0.7:
            metrics['danceability_level'] = 'high'
        elif danceability > 0.4:
            metrics['danceability_level'] = 'medium'
        else:
            metrics['danceability_level'] = 'low'
        
        return metrics
    
    async def _apply_sorting_algorithm_async(self, tracks: List[Dict], algorithm: SortingAlgorithm, 
                                           rules: List[PlaylistRule], 
                                           progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Wendet den gewählten Sortieralgorithmus asynchron an"""
        
        if algorithm == SortingAlgorithm.HARMONIC:
            return await self._sort_harmonic_async(tracks, rules, progress_callback)
        elif algorithm == SortingAlgorithm.ENERGY_FLOW:
            return self._sort_energy_flow(tracks, rules)
        elif algorithm == SortingAlgorithm.MOOD_PROGRESSION:
            return self._sort_mood_progression(tracks, rules)
        elif algorithm == SortingAlgorithm.BPM_TRANSITION:
            return self._sort_bpm_transition(tracks, rules)
        elif algorithm == SortingAlgorithm.KEY_PROGRESSION:
            return await self._sort_harmonic_async(tracks, rules, progress_callback)  # Ähnlich wie harmonic
        elif algorithm == SortingAlgorithm.HYBRID_SMART:
            return await self._sort_hybrid_smart_async(tracks, rules, progress_callback)
        else:
            return self._sort_custom(tracks, rules)
    
    async def _sort_harmonic_async(self, tracks: List[Dict], rules: List[PlaylistRule], 
                                  progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Sortiert nach harmonischer Kompatibilität mit Progress-Updates"""
        if not tracks:
            return []
        
        # Starte mit dem Track mit der besten durchschnittlichen Harmonie
        if progress_callback:
            await progress_callback("Analysiere harmonische Kompatibilität...")
        
        sorted_tracks = [tracks[0]]
        remaining_tracks = tracks[1:]
        total_tracks = len(tracks)
        
        while remaining_tracks:
            current_track = sorted_tracks[-1]
            current_camelot = self._get_camelot_from_track(current_track)
            
            # Finde den besten nächsten Track
            best_track = None
            best_score = -1
            
            for track in remaining_tracks:
                track_camelot = self._get_camelot_from_track(track)
                score = self._calculate_harmonic_score(current_camelot, track_camelot, rules)
                
                if score > best_score:
                    best_score = score
                    best_track = track
            
            if best_track:
                sorted_tracks.append(best_track)
                remaining_tracks.remove(best_track)
            else:
                # Fallback: nimm den ersten verfügbaren Track
                sorted_tracks.append(remaining_tracks.pop(0))
            
            # Progress-Update
            if progress_callback:
                progress = len(sorted_tracks) / total_tracks * 100
                await progress_callback(f"Harmonische Sortierung: {progress:.1f}%")
        
        return sorted_tracks
    
    def _sort_energy_flow(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert nach Energie-Verlauf"""
        energy_rule = next((r for r in rules if 'energy' in r.name.lower()), None)
        
        if energy_rule and 'progression' in energy_rule.name.lower():
            # Aufsteigender Energie-Verlauf
            return sorted(tracks, key=lambda t: t['features'].get('energy', 0.5))
        else:
            # Optimierter Energie-Verlauf
            return self._optimize_energy_flow(tracks, rules)
    
    def _optimize_energy_flow(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Optimiert den Energie-Verlauf für natürliche Progression"""
        if not tracks:
            return []
        
        # Gruppiere Tracks nach Energie-Level
        low_energy = [t for t in tracks if t['features'].get('energy', 0.5) < 0.4]
        med_energy = [t for t in tracks if 0.4 <= t['features'].get('energy', 0.5) < 0.7]
        high_energy = [t for t in tracks if t['features'].get('energy', 0.5) >= 0.7]
        
        # Sortiere jede Gruppe intern nach Energie
        low_energy.sort(key=lambda t: t['features'].get('energy', 0.5))
        med_energy.sort(key=lambda t: t['features'].get('energy', 0.5))
        high_energy.sort(key=lambda t: t['features'].get('energy', 0.5))
        
        # Kombiniere für graduellen Aufbau
        return low_energy + med_energy + high_energy
    
    def _sort_mood_progression(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert nach kohärenter Stimmungs-Progression"""
        return self._create_mood_flow(tracks, rules)
    
    def _create_mood_flow(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Erstellt einen kohärenten Stimmungs-Verlauf"""
        if not tracks:
            return []
        
        # Gruppiere nach geschätzter Stimmung
        mood_groups = {}
        for track in tracks:
            mood = track.get('derived_metrics', {}).get('estimated_mood', 'neutral')
            if mood not in mood_groups:
                mood_groups[mood] = []
            mood_groups[mood].append(track)
        
        # Definiere Stimmungs-Progression für verschiedene Flows
        mood_order = ['calm', 'happy', 'energetic']  # Standard-Progression
        
        # Prüfe Rules für spezielle Mood-Flows
        for rule in rules:
            if 'mood' in rule.name.lower() and 'uplifting' in rule.description.lower():
                mood_order = ['melancholic', 'calm', 'happy', 'uplifting', 'energetic']
            elif 'coherent' in rule.name.lower():
                # Gruppiere ähnliche Stimmungen zusammen
                dominant_mood = max(mood_groups.keys(), key=lambda m: len(mood_groups[m]))
                mood_order = [dominant_mood] + [m for m in mood_groups.keys() if m != dominant_mood]
        
        # Erstelle Stimmungs-Progression
        sorted_tracks = []
        for mood in mood_order:
            if mood in mood_groups:
                sorted_tracks.extend(mood_groups[mood])
        
        # Füge übrige Stimmungen hinzu
        for mood, tracks_list in mood_groups.items():
            if mood not in mood_order:
                sorted_tracks.extend(tracks_list)
        
        return sorted_tracks
    
    def _sort_bpm_transition(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Sortiert für sanfte BPM-Übergänge"""
        if not tracks:
            return []
        
        # Sortiere nach BPM
        tracks_by_bpm = sorted(tracks, key=lambda t: t['features'].get('bpm', 120.0))
        
        # Prüfe Rules für spezielle BPM-Behandlung
        for rule in rules:
            if 'gradual' in rule.name.lower() and 'increase' in rule.name.lower():
                # Gradueller BPM-Anstieg
                return tracks_by_bpm
            elif 'stability' in rule.name.lower():
                # BPM-Stabilität bevorzugen
                return self._optimize_bpm_stability(tracks, rules)
        
        # Standard: Beginne in der Mitte und arbeite graduell
        start_index = len(tracks_by_bpm) // 2
        sorted_tracks = [tracks_by_bpm[start_index]]
        remaining = tracks_by_bpm[:start_index] + tracks_by_bpm[start_index+1:]
        
        while remaining:
            current_bpm = sorted_tracks[-1]['features'].get('bpm', 120.0)
            
            # Finde Track mit ähnlichstem BPM
            best_track = min(remaining, key=lambda t: abs(t['features'].get('bpm', 120.0) - current_bpm))
            
            sorted_tracks.append(best_track)
            remaining.remove(best_track)
        
        return sorted_tracks
    
    def _optimize_bpm_stability(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Optimiert für BPM-Stabilität"""
        # Gruppiere Tracks nach BPM-Bereichen
        bpm_groups = {}
        
        for track in tracks:
            bpm = track['features'].get('bpm', 120.0)
            bpm_range = int(bpm / 10) * 10  # 10er-Bereiche
            
            if bpm_range not in bpm_groups:
                bpm_groups[bpm_range] = []
            bpm_groups[bpm_range].append(track)
        
        # Sortiere Gruppen und kombiniere
        sorted_tracks = []
        for bpm_range in sorted(bpm_groups.keys()):
            group = sorted(bpm_groups[bpm_range], key=lambda t: t['features'].get('bpm', 120.0))
            sorted_tracks.extend(group)
        
        return sorted_tracks
    
    async def _sort_hybrid_smart_async(self, tracks: List[Dict], rules: List[PlaylistRule], 
                                      progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Intelligente Kombination aller Algorithmen mit gewichteten Scores"""
        if not tracks:
            return []
        
        if progress_callback:
            await progress_callback("Berechne Hybrid-Scores...")
        
        # Berechne gewichtete Scores für jeden Track
        scored_tracks = []
        total_tracks = len(tracks)
        
        for i, track in enumerate(tracks):
            score_components = {}
            total_score = 0.0
            
            # Harmonic Score (relativ zu anderen Tracks)
            harmonic_scores = []
            track_camelot = self._get_camelot_from_track(track)
            for other_track in tracks:
                if other_track != track:
                    other_camelot = self._get_camelot_from_track(other_track)
                    harm_score = self._calculate_harmonic_score(track_camelot, other_camelot, rules)
                    harmonic_scores.append(harm_score)
            
            score_components['harmonic'] = np.mean(harmonic_scores) if harmonic_scores else 0.5
            
            # Feature-basierte Scores
            features = track['features']
            score_components['energy'] = features.get('energy', 0.5)
            score_components['danceability'] = features.get('danceability', 0.5)
            score_components['valence'] = features.get('valence', 0.5)
            
            # Gewichtete Kombination basierend auf Rules
            weights = {'harmonic': 0.3, 'energy': 0.25, 'danceability': 0.25, 'valence': 0.2}
            
            # Anpassung der Gewichte basierend auf Rules
            for rule in rules:
                if rule.enabled:
                    if 'harmonic' in rule.name.lower():
                        weights['harmonic'] += rule.weight * 0.1
                    elif 'energy' in rule.name.lower():
                        weights['energy'] += rule.weight * 0.1
                    elif 'danceability' in rule.name.lower():
                        weights['danceability'] += rule.weight * 0.1
            
            # Normalisiere Gewichte
            weight_sum = sum(weights.values())
            weights = {k: v/weight_sum for k, v in weights.items()}
            
            # Berechne finalen Score
            for component, weight in weights.items():
                total_score += score_components[component] * weight
            
            scored_tracks.append((track, total_score, score_components))
            
            if progress_callback and i % 10 == 0:
                progress = (i + 1) / total_tracks * 100
                await progress_callback(f"Score-Berechnung: {progress:.1f}%")
        
        if progress_callback:
            await progress_callback("Sortiere nach Hybrid-Score...")
        
        # Sortiere nach Gesamt-Score (absteigend)
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        
        return [track for track, score, components in scored_tracks]
    
    def _sort_custom(self, tracks: List[Dict], rules: List[PlaylistRule]) -> List[Dict]:
        """Benutzerdefinierte Sortierung basierend auf Rules"""
        # Implementiere flexible Rule-Engine
        sorted_tracks = tracks.copy()
        
        for rule in rules:
            if not rule.enabled:
                continue
                
            if rule.name == "high_energy_filter":
                # Filtere nur hochenergetische Tracks
                min_energy = rule.parameters.get('min_energy', 0.7)
                sorted_tracks = [t for t in sorted_tracks if t['features'].get('energy', 0.5) >= min_energy]
            
            elif rule.name == "bpm_range_filter":
                # Filtere nach BPM-Bereich
                min_bpm = rule.parameters.get('min_bpm', 60)
                max_bpm = rule.parameters.get('max_bpm', 200)
                sorted_tracks = [t for t in sorted_tracks 
                               if min_bpm <= t['features'].get('bpm', 120.0) <= max_bpm]
            
            # Weitere custom Rules können hier hinzugefügt werden
        
        return sorted_tracks
    
    def _get_camelot_from_track(self, track: Dict) -> str:
        """Extrahiert Camelot-Key aus Track-Daten"""
        camelot_info = track.get('camelot', {})
        if isinstance(camelot_info, dict):
            return camelot_info.get('camelot', '1A')
        return '1A'  # Fallback
    
    def _calculate_harmonic_score(self, camelot1: str, camelot2: str, rules: List[PlaylistRule]) -> float:
        """Berechnet harmonischen Kompatibilitäts-Score zwischen zwei Keys"""
        if camelot1 == camelot2:
            return 1.0
        
        compatible_keys = self.camelot_compatibility.get(camelot1, [])
        
        if camelot2 in compatible_keys:
            # Gewichtung basierend auf Kompatibilitäts-Typ
            if len(camelot1) >= 2 and len(camelot2) >= 2:
                # Relative Dur/Moll (gleiche Nummer, andere Modalität)
                if (camelot1[:-1] == camelot2[:-1] and 
                    camelot1[-1] != camelot2[-1]):
                    return 0.9
                else:
                    return 0.7  # Quintenzirkel
            return 0.7
        
        return 0.1  # Nicht kompatibel
    
    def _trim_to_duration(self, tracks: List[Dict], target_seconds: int) -> List[Dict]:
        """Kürzt Playlist auf Zieldauer"""
        total_duration = 0
        trimmed_tracks = []
        
        for track in tracks:
            track_duration = track.get('metadata', {}).get('duration', 180)  # 3min default
            
            if total_duration + track_duration <= target_seconds:
                trimmed_tracks.append(track)
                total_duration += track_duration
            else:
                # Prüfe ob der Track noch reinpasst mit Toleranz
                tolerance = 30  # 30 Sekunden Toleranz
                if total_duration + track_duration <= target_seconds + tolerance:
                    trimmed_tracks.append(track)
                    total_duration += track_duration
                break
        
        logger.info(f"Playlist auf {len(trimmed_tracks)} Tracks gekürzt ({total_duration/60:.1f} Min)")
        return trimmed_tracks
    
    def _calculate_playlist_metadata(self, tracks: List[Dict], preset: PlaylistPreset) -> Dict:
        """Berechnet umfassende Playlist-Metadaten"""
        if not tracks:
            return {}
        
        total_duration = sum(t.get('metadata', {}).get('duration', 180) for t in tracks)
        
        # Durchschnittliche Features
        avg_energy = np.mean([t['features'].get('energy', 0.5) for t in tracks])
        avg_valence = np.mean([t['features'].get('valence', 0.5) for t in tracks])
        avg_danceability = np.mean([t['features'].get('danceability', 0.5) for t in tracks])
        
        # BPM-Statistiken
        bpms = [t['features'].get('bpm', 120.0) for t in tracks]
        min_bpm = min(bpms)
        max_bpm = max(bpms)
        avg_bpm = np.mean(bpms)
        
        # Key-Verteilung
        keys = [self._get_camelot_from_track(t) for t in tracks]
        key_distribution = {}
        for key in keys:
            key_distribution[key] = key_distribution.get(key, 0) + 1
        
        # Stimmungs-Verteilung
        moods = [t.get('derived_metrics', {}).get('estimated_mood', 'neutral') for t in tracks]
        mood_distribution = {}
        for mood in moods:
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
        
        # Energie-Verlauf (für Visualisierung)
        energy_progression = [t['features'].get('energy', 0.5) for t in tracks]
        
        return {
            'total_tracks': len(tracks),
            'total_duration_seconds': total_duration,
            'total_duration_minutes': round(total_duration / 60, 1),
            'average_energy': round(float(avg_energy), 3),
            'average_valence': round(float(avg_valence), 3),
            'average_danceability': round(float(avg_danceability), 3),
            'bpm_stats': {
                'min': round(float(min_bpm), 1),
                'max': round(float(max_bpm), 1),
                'average': round(float(avg_bpm), 1)
            },
            'key_distribution': key_distribution,
            'mood_distribution': mood_distribution,
            'energy_progression': energy_progression,
            'preset_name': preset.name,
            'energy_curve': preset.energy_curve,
            'mood_flow': preset.mood_flow
        }
    
    # Public API Methods
    
    def get_all_presets(self) -> List[Dict]:
        """Gibt alle verfügbaren Presets als Dict zurück (für API)"""
        all_presets = self.default_presets + self.custom_presets
        return [
            {
                'name': preset.name,
                'description': preset.description,
                'algorithm': preset.algorithm.value,
                'energy_curve': preset.energy_curve,
                'mood_flow': preset.mood_flow,
                'target_duration_minutes': preset.target_duration_minutes,
                'is_default': preset in self.default_presets,
                'created_at': preset.created_at
            }
            for preset in all_presets
        ]
    
    def get_preset_details(self, preset_name: str) -> Optional[Dict]:
        """Gibt detaillierte Informationen zu einem Preset zurück"""
        preset = self._get_preset(preset_name)
        if not preset:
            return None
        
        return {
            'name': preset.name,
            'description': preset.description,
            'algorithm': preset.algorithm.value,
            'rules': [
                {
                    'name': rule.name,
                    'description': rule.description,
                    'weight': rule.weight,
                    'enabled': rule.enabled,
                    'parameters': rule.parameters
                }
                for rule in preset.rules
            ],
            'target_duration_minutes': preset.target_duration_minutes,
            'energy_curve': preset.energy_curve,
            'mood_flow': preset.mood_flow,
            'is_default': preset in self.default_presets,
            'created_at': preset.created_at
        }
    
    def save_custom_preset(self, preset_data: Dict) -> bool:
        """Speichert ein benutzerdefiniertes Preset aus Dict"""
        try:
            # Konvertiere Rules
            rules = []
            for rule_data in preset_data.get('rules', []):
                rules.append(PlaylistRule(**rule_data))
            
            # Erstelle Preset
            preset = PlaylistPreset(
                name=preset_data['name'],
                description=preset_data['description'],
                algorithm=SortingAlgorithm(preset_data['algorithm']),
                rules=rules,
                target_duration_minutes=preset_data.get('target_duration_minutes'),
                energy_curve=preset_data.get('energy_curve', 'gradual_build'),
                mood_flow=preset_data.get('mood_flow', 'coherent')
            )
            
            # Prüfe ob Preset bereits existiert
            existing = next((p for p in self.custom_presets if p.name == preset.name), None)
            
            if existing:
                index = self.custom_presets.index(existing)
                self.custom_presets[index] = preset
            else:
                self.custom_presets.append(preset)
            
            self._save_custom_presets()
            logger.info(f"Custom Preset '{preset.name}' gespeichert")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Custom Presets: {e}")
            return False
    
    def delete_custom_preset(self, preset_name: str) -> bool:
        """Löscht ein benutzerdefiniertes Preset"""
        try:
            preset = next((p for p in self.custom_presets if p.name == preset_name), None)
            
            if preset:
                self.custom_presets.remove(preset)
                self._save_custom_presets()
                logger.info(f"Custom Preset '{preset_name}' gelöscht")
                return True
            else:
                logger.warning(f"Custom Preset '{preset_name}' nicht gefunden")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Custom Presets: {e}")
            return False
    
    def get_algorithm_info(self) -> Dict[str, str]:
        """Gibt Informationen über verfügbare Algorithmen zurück"""
        return {
            SortingAlgorithm.HARMONIC.value: "Harmonische Übergänge basierend auf Camelot Wheel",
            SortingAlgorithm.ENERGY_FLOW.value: "Optimierter Energie-Verlauf für natürliche Progression",
            SortingAlgorithm.MOOD_PROGRESSION.value: "Kohärente Stimmungs-Übergänge",
            SortingAlgorithm.BPM_TRANSITION.value: "Sanfte BPM-Übergänge für DJ-Sets",
            SortingAlgorithm.KEY_PROGRESSION.value: "Tonart-basierte Progression (Quintenzirkel)",
            SortingAlgorithm.HYBRID_SMART.value: "Intelligente Kombination aller Algorithmen",
            SortingAlgorithm.CUSTOM.value: "Benutzerdefinierte Regel-basierte Sortierung"
        }