"""Playlist Validator - Erweiterte Validierung und Qualitätsprüfung für DJ-Playlists"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import statistics
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validierungslevel"""
    BASIC = "basic"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    EXPERT = "expert"

class IssueType(Enum):
    """Typen von Validierungsproblemen"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"

@dataclass
class ValidationIssue:
    """Einzelnes Validierungsproblem"""
    type: IssueType
    category: str
    message: str
    track_index: Optional[int] = None
    track_title: Optional[str] = None
    severity: float = 1.0  # 0.0 - 1.0
    suggestion: Optional[str] = None
    auto_fixable: bool = False

@dataclass
class ValidationConfig:
    """Konfiguration für Playlist-Validierung"""
    level: ValidationLevel = ValidationLevel.STANDARD
    check_file_existence: bool = True
    check_audio_quality: bool = True
    check_harmonic_flow: bool = True
    check_energy_flow: bool = True
    check_tempo_flow: bool = True
    check_mood_progression: bool = True
    check_diversity: bool = True
    check_technical_mixing: bool = True
    check_crowd_engagement: bool = False
    
    # Toleranzen
    max_bpm_jump: float = 20.0
    max_energy_jump: float = 3.0
    min_track_duration: float = 60.0  # Sekunden
    max_track_duration: float = 600.0  # Sekunden
    min_bitrate: int = 128  # kbps
    max_duplicate_artists: int = 2
    max_same_genre_consecutive: int = 3
    
    # Gewichtungen für Qualitäts-Score
    weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.weights is None:
            self.weights = {
                'harmonic_flow': 0.25,
                'energy_flow': 0.20,
                'tempo_flow': 0.15,
                'mood_progression': 0.15,
                'diversity': 0.10,
                'technical_mixing': 0.10,
                'crowd_engagement': 0.05
            }
        self.adjust_for_level()

    def adjust_for_level(self):
        if self.level == ValidationLevel.BASIC:
            self.check_crowd_engagement = False
            self.check_technical_mixing = False
        elif self.level == ValidationLevel.STANDARD:
            self.check_crowd_engagement = False
        # Für PROFESSIONAL und EXPERT alle Checks aktiv

class PlaylistValidator:
    """Hauptklasse für Playlist-Validierung"""

    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.issues: List[ValidationIssue] = []
        self.quality_score: float = 0.0
        self.detailed_scores: Dict[str, float] = {}

    def validate(self, playlist: List[Dict[str, Any]]) -> Tuple[float, List[ValidationIssue]]:
        """Validierung einer Playlist durchführen"""
        self.issues.clear()
        self.detailed_scores.clear()

        # Einzelne Checks ausführen
        if self.config.check_file_existence:
            self._check_file_existence(playlist)
        if self.config.check_audio_quality:
            self._check_audio_quality(playlist)
        if self.config.check_harmonic_flow:
            self._check_harmonic_flow(playlist)
        if self.config.check_energy_flow:
            self._check_energy_flow(playlist)
        if self.config.check_tempo_flow:
            self._check_tempo_flow(playlist)
        if self.config.check_mood_progression:
            self._check_mood_progression(playlist)
        if self.config.check_diversity:
            self._check_diversity(playlist)
        if self.config.check_technical_mixing:
            self._check_technical_mixing(playlist)
        if self.config.check_crowd_engagement:
            self._check_crowd_engagement(playlist)

        # Qualitäts-Score berechnen
        self._calculate_quality_score()

        return self.quality_score, self.issues

    def _calculate_quality_score(self):
        """Aggregierten Qualitäts-Score berechnen"""
        total_weight = sum(self.config.weights.values())
        self.quality_score = 0.0
        for category, weight in self.config.weights.items():
            category_issues = [i for i in self.issues if i.category == category]
            if category_issues:
                avg_severity = statistics.mean(i.severity for i in category_issues)
                score = 1.0 - avg_severity
            else:
                score = 1.0
            self.detailed_scores[category] = score
            self.quality_score += score * (weight / total_weight)
        self.quality_score = round(self.quality_score * 100, 2)

    # Beispiel für einen Check (weitere implementieren)
    def _check_harmonic_flow(self, playlist: List[Dict[str, Any]]):
        """Harmonischen Fluss prüfen"""
        for i in range(len(playlist) - 1):
            current_key = playlist[i].get('camelot_key')
            next_key = playlist[i+1].get('camelot_key')
            if current_key and next_key:
                if not self._is_harmonic_compatible(current_key, next_key):
                    self.issues.append(ValidationIssue(
                        type=IssueType.WARNING,
                        category='harmonic_flow',
                        message=f'Inkompatible Tonart-Übergang von {current_key} zu {next_key}',
                        track_index=i+1,
                        severity=0.7,
                        suggestion='Track austauschen oder Key-Shift anwenden'
                    ))

    def _is_harmonic_compatible(self, key1: str, key2: str) -> bool:
        """Kompatibilität basierend auf Camelot Wheel prüfen"""
        # Hier Integration mit camelot_wheel.py
        from .camelot_wheel import CamelotWheel
        return CamelotWheel.is_compatible(key1, key2)

    def _check_energy_flow(self, playlist: List[Dict[str, Any]]):
        """Energie-Fluss prüfen"""
        energies = [track.get('energy_score', 0) for track in playlist if 'energy_score' in track]
        if len(energies) < 2:
            return
        jumps = np.diff(energies)
        large_jumps = np.abs(jumps) > self.config.max_energy_jump
        for i, jump in enumerate(large_jumps):
            if jump:
                self.issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category='energy_flow',
                    message=f'Großer Energie-Sprung zwischen Track {i+1} und {i+2}',
                    track_index=i+1,
                    severity=0.6,
                    suggestion='Energie-Kurve anpassen oder Track ersetzen'
                ))

    def _check_tempo_flow(self, playlist: List[Dict[str, Any]]):
        """Tempo-Fluss prüfen"""
        bpms = [track.get('bpm', 0) for track in playlist if 'bpm' in track]
        if len(bpms) < 2:
            return
        jumps = np.diff(bpms)
        large_jumps = np.abs(jumps) > self.config.max_bpm_jump
        for i, jump in enumerate(large_jumps):
            if jump:
                self.issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category='tempo_flow',
                    message=f'Großer BPM-Sprung zwischen Track {i+1} und {i+2}',
                    track_index=i+1,
                    severity=0.5,
                    suggestion='Tempo anpassen oder Track ersetzen',
                    auto_fixable=True
                ))

    def _check_mood_progression(self, playlist: List[Dict[str, Any]]):
        """Stimmungs-Progression prüfen"""
        moods = [track.get('mood_label') for track in playlist if 'mood_label' in track]
        if len(moods) < 3:
            return
        mood_changes = sum(1 for i in range(len(moods)-1) if moods[i] != moods[i+1])
        if mood_changes < len(moods) / 3:
            self.issues.append(ValidationIssue(
                type=IssueType.INFO,
                category='mood_progression',
                message='Wenige Stimmungswechsel - könnte dynamischer sein',
                severity=0.3,
                suggestion='Mehr Mood-Variationen hinzufügen'
            ))

    def _check_diversity(self, playlist: List[Dict[str, Any]]):
        """Vielfalt prüfen"""
        artists = Counter(track.get('artist') for track in playlist if 'artist' in track)
        for artist, count in artists.items():
            if count > self.config.max_duplicate_artists:
                self.issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category='diversity',
                    message=f'Zu viele Tracks vom Artist {artist} ({count})',
                    severity=0.4,
                    suggestion='Einige Tracks entfernen oder ersetzen'
                ))

    def _check_technical_mixing(self, playlist: List[Dict[str, Any]]):
        """Technische Mix-Aspekte prüfen"""
        for i in range(len(playlist) - 1):
            current = playlist[i]
            next_track = playlist[i+1]
            if abs(current.get('bpm', 0) - next_track.get('bpm', 0)) > 5 and not current.get('can_pitch_shift', False):
                self.issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category='technical_mixing',
                    message=f'Beat-Matching schwierig zwischen Track {i+1} und {i+2} aufgrund BPM-Differenz',
                    track_index=i+1,
                    severity=0.6,
                    suggestion='Pitch-Shift aktivieren oder Track ersetzen',
                    auto_fixable=True
                ))

    def _check_crowd_engagement(self, playlist: List[Dict[str, Any]]):
        """Crowd-Engagement potenziell prüfen"""
        energy_peaks = sum(1 for track in playlist if track.get('energy_score', 0) > 8.0)
        if energy_peaks < len(playlist) / 5:
            self.issues.append(ValidationIssue(
                type=IssueType.SUGGESTION,
                category='crowd_engagement',
                message='Wenige Energy-Peaks - könnte Crowd-Engagement verbessern',
                severity=0.2,
                suggestion='Mehr hochenergetische Tracks hinzufügen'
            ))

    def _check_file_existence(self, playlist: List[Dict[str, Any]]):
        """Dateiexistenz prüfen"""
        for i, track in enumerate(playlist):
            if 'file_path' in track and not Path(track['file_path']).exists():
                self.issues.append(ValidationIssue(
                    type=IssueType.ERROR,
                    category='file_existence',
                    message=f'Track-Datei nicht gefunden: {track.get("title")}',
                    track_index=i,
                    severity=1.0
                ))

    def _check_audio_quality(self, playlist: List[Dict[str, Any]]):
        """Audio-Qualität prüfen"""
        for i, track in enumerate(playlist):
            if track.get('bitrate', 0) < self.config.min_bitrate:
                self.issues.append(ValidationIssue(
                    type=IssueType.WARNING,
                    category='audio_quality',
                    message=f'Niedrige Bitrate für Track {track.get("title")}',
                    track_index=i,
                    severity=0.8
                ))

    def apply_auto_fixes(self, playlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Automatische Fixes anwenden"""
        fixable_issues = [i for i in self.issues if i.auto_fixable]
        fixed_playlist = playlist.copy()
        for issue in fixable_issues:
            if issue.category == 'tempo_flow':
                # Beispiel: BPM anpassen
                if issue.track_index is not None and issue.track_index + 1 < len(fixed_playlist):
                    avg_bpm = (fixed_playlist[issue.track_index]['bpm'] + fixed_playlist[issue.track_index + 1]['bpm']) / 2
                    fixed_playlist[issue.track_index + 1]['bpm'] = avg_bpm  # Simulierte Anpassung
            elif issue.category == 'technical_mixing':
                if issue.track_index is not None:
                    fixed_playlist[issue.track_index]['can_pitch_shift'] = True  # Aktiviere Pitch-Shift
        return fixed_playlist

    def generate_report(self) -> str:
        """Detaillierten Validierungsreport generieren"""
        report = f'Playlist Quality Score: {self.quality_score}%\n\nIssues:\n'
        for issue in sorted(self.issues, key=lambda x: x.severity, reverse=True):
            report += f'[{issue.type.value.upper()}] {issue.category}: {issue.message}\n'
            if issue.suggestion:
                report += f'Suggestion: {issue.suggestion}\n'
        return report