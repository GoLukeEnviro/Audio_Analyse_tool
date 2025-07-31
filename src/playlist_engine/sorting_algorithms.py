"""Sorting Algorithms - Algorithmen für die Playlist-Sortierung"""

from typing import Dict, List, Any, Optional, Callable, Tuple
import random
import math
from .camelot_wheel import CamelotWheel


class SortingAlgorithms:
    """Sammlung von Sortier-Algorithmen für Playlists"""
    
    def __init__(self):
        self.camelot_wheel = CamelotWheel()
        self.algorithms = {
            'bpm_ascending': self.sort_by_bpm_ascending,
            'bpm_descending': self.sort_by_bpm_descending,
            'energy_ascending': self.sort_by_energy_ascending,
            'energy_descending': self.sort_by_energy_descending,
            'harmonic_mixing': self.sort_by_harmonic_mixing,
            'energy_curve': self.sort_by_energy_curve,
            'random': self.sort_random,
            'alphabetical': self.sort_alphabetical,
            'duration': self.sort_by_duration,
            'key_progression': self.sort_by_key_progression,
            'mood_flow': self.sort_by_mood_flow,
            'intelligent': self.sort_intelligent
        }
    
    def get_available_algorithms(self) -> Dict[str, str]:
        """Gibt verfügbare Sortier-Algorithmen zurück"""
        return {
            'bpm_ascending': 'BPM aufsteigend',
            'bpm_descending': 'BPM absteigend',
            'energy_ascending': 'Energie aufsteigend',
            'energy_descending': 'Energie absteigend',
            'harmonic_mixing': 'Harmonisches Mixing',
            'energy_curve': 'Energie-Kurve',
            'random': 'Zufällig',
            'alphabetical': 'Alphabetisch',
            'duration': 'Nach Dauer',
            'key_progression': 'Tonart-Progression',
            'mood_flow': 'Stimmungs-Verlauf',
            'intelligent': 'Intelligente Sortierung'
        }
    
    def sort_tracks(self, tracks: List[Dict[str, Any]], algorithm: str, **kwargs) -> List[Dict[str, Any]]:
        """Sortiert Tracks mit dem angegebenen Algorithmus"""
        if not tracks:
            return []
        
        if algorithm not in self.algorithms:
            print(f"Unknown sorting algorithm: {algorithm}")
            return tracks
        
        try:
            return self.algorithms[algorithm](tracks, **kwargs)
        except Exception as e:
            print(f"Error in sorting algorithm {algorithm}: {e}")
            return tracks
    
    # Basis-Sortierungen
    
    def sort_by_bpm_ascending(self, tracks: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach BPM aufsteigend"""
        return sorted(tracks, key=lambda x: x.get('bpm', 0))
    
    def sort_by_bpm_descending(self, tracks: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach BPM absteigend"""
        return sorted(tracks, key=lambda x: x.get('bpm', 0), reverse=True)
    
    def sort_by_energy_ascending(self, tracks: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach Energie aufsteigend"""
        return sorted(tracks, key=lambda x: x.get('energy', 0))
    
    def sort_by_energy_descending(self, tracks: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach Energie absteigend"""
        return sorted(tracks, key=lambda x: x.get('energy', 0), reverse=True)
    
    def sort_alphabetical(self, tracks: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Sortiert alphabetisch nach Titel"""
        return sorted(tracks, key=lambda x: x.get('title', '').lower())
    
    def sort_by_duration(self, tracks: List[Dict[str, Any]], ascending: bool = True, **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach Dauer"""
        return sorted(tracks, key=lambda x: x.get('duration', 0), reverse=not ascending)
    
    def sort_random(self, tracks: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """Zufällige Sortierung"""
        shuffled = tracks.copy()
        random.shuffle(shuffled)
        return shuffled
    
    # Erweiterte Sortierungen
    
    def sort_by_harmonic_mixing(self, tracks: List[Dict[str, Any]], start_key: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Sortiert für optimales harmonisches Mixing"""
        if len(tracks) <= 1:
            return tracks
        
        # Konvertiere alle Tonarten zu Camelot
        camelot_tracks = []
        for track in tracks:
            key = track.get('key')
            camelot = self.camelot_wheel.key_to_camelot(key) if key else None
            camelot_tracks.append((track, camelot))
        
        # Tracks ohne Tonart ans Ende
        tracks_with_key = [(t, c) for t, c in camelot_tracks if c]
        tracks_without_key = [t for t, c in camelot_tracks if not c]
        
        if not tracks_with_key:
            return tracks
        
        # Bestimme Start-Tonart
        if start_key:
            start_camelot = self.camelot_wheel.key_to_camelot(start_key)
        else:
            # Verwende die häufigste Tonart oder die erste
            start_camelot = tracks_with_key[0][1]
        
        # Greedy-Algorithmus für harmonische Reihenfolge
        sorted_tracks = []
        remaining_tracks = tracks_with_key.copy()
        
        # Finde besten Starttrack
        if start_camelot:
            best_start = min(remaining_tracks, 
                           key=lambda x: self.camelot_wheel.calculate_distance(start_camelot, x[1]))
            current_track, current_camelot = best_start
            sorted_tracks.append(current_track)
            remaining_tracks.remove(best_start)
        else:
            current_track, current_camelot = remaining_tracks.pop(0)
            sorted_tracks.append(current_track)
        
        # Baue Kette auf
        while remaining_tracks:
            # Finde nächsten besten Track
            best_next = min(remaining_tracks,
                          key=lambda x: self.camelot_wheel.calculate_distance(current_camelot, x[1]))
            
            current_track, current_camelot = best_next
            sorted_tracks.append(current_track)
            remaining_tracks.remove(best_next)
        
        # Füge Tracks ohne Tonart hinzu
        sorted_tracks.extend(tracks_without_key)
        
        return sorted_tracks
    
    def sort_by_energy_curve(self, tracks: List[Dict[str, Any]], curve_type: str = 'buildup', **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach Energie-Kurve"""
        if len(tracks) <= 1:
            return tracks
        
        # Sortiere zunächst nach Energie
        energy_sorted = sorted(tracks, key=lambda x: x.get('energy', 0))
        
        if curve_type == 'buildup':
            # Kontinuierlicher Aufbau
            return energy_sorted
        
        elif curve_type == 'breakdown':
            # Kontinuierlicher Abbau
            return energy_sorted[::-1]
        
        elif curve_type == 'wave':
            # Wellenförmig: niedrig -> hoch -> niedrig
            low_energy = energy_sorted[:len(energy_sorted)//3]
            high_energy = energy_sorted[len(energy_sorted)//3:2*len(energy_sorted)//3]
            mid_energy = energy_sorted[2*len(energy_sorted)//3:]
            
            return low_energy + high_energy + mid_energy
        
        elif curve_type == 'peak':
            # Aufbau zum Höhepunkt in der Mitte
            mid_point = len(energy_sorted) // 2
            first_half = energy_sorted[:mid_point]
            second_half = energy_sorted[mid_point:][::-1]
            
            return first_half + second_half
        
        return energy_sorted
    
    def sort_by_key_progression(self, tracks: List[Dict[str, Any]], progression_type: str = 'circle_of_fifths', **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach Tonart-Progression"""
        if len(tracks) <= 1:
            return tracks
        
        # Gruppiere nach Tonarten
        key_groups = {}
        tracks_without_key = []
        
        for track in tracks:
            key = track.get('key')
            if key:
                camelot = self.camelot_wheel.key_to_camelot(key)
                if camelot:
                    if camelot not in key_groups:
                        key_groups[camelot] = []
                    key_groups[camelot].append(track)
                else:
                    tracks_without_key.append(track)
            else:
                tracks_without_key.append(track)
        
        if not key_groups:
            return tracks
        
        sorted_tracks = []
        
        if progression_type == 'circle_of_fifths':
            # Quintenkreis-Reihenfolge
            fifth_order = ['1A', '8A', '3A', '10A', '5A', '12A', '7A', '2A', '9A', '4A', '11A', '6A',
                          '1B', '8B', '3B', '10B', '5B', '12B', '7B', '2B', '9B', '4B', '11B', '6B']
            
            for camelot in fifth_order:
                if camelot in key_groups:
                    sorted_tracks.extend(key_groups[camelot])
        
        elif progression_type == 'chromatic':
            # Chromatische Reihenfolge
            chromatic_order = [f"{i}A" for i in range(1, 13)] + [f"{i}B" for i in range(1, 13)]
            
            for camelot in chromatic_order:
                if camelot in key_groups:
                    sorted_tracks.extend(key_groups[camelot])
        
        elif progression_type == 'relative_pairs':
            # Relative Dur/Moll-Paare
            for i in range(1, 13):
                minor_key = f"{i}A"
                major_key = f"{i}B"
                
                if minor_key in key_groups:
                    sorted_tracks.extend(key_groups[minor_key])
                if major_key in key_groups:
                    sorted_tracks.extend(key_groups[major_key])
        
        # Füge Tracks ohne Tonart hinzu
        sorted_tracks.extend(tracks_without_key)
        
        return sorted_tracks
    
    def sort_by_mood_flow(self, tracks: List[Dict[str, Any]], flow_type: str = 'emotional_journey', **kwargs) -> List[Dict[str, Any]]:
        """Sortiert nach Stimmungs-Verlauf"""
        if len(tracks) <= 1:
            return tracks
        
        # Definiere Stimmungs-Reihenfolgen
        mood_orders = {
            'emotional_journey': ['Dark', 'Experimental', 'Driving', 'Euphoric'],
            'energy_buildup': ['Experimental', 'Dark', 'Driving', 'Euphoric'],
            'chill_to_peak': ['Dark', 'Driving', 'Experimental', 'Euphoric'],
            'peak_to_chill': ['Euphoric', 'Driving', 'Experimental', 'Dark']
        }
        
        mood_order = mood_orders.get(flow_type, mood_orders['emotional_journey'])
        
        # Gruppiere nach Stimmungen
        mood_groups = {mood: [] for mood in mood_order}
        tracks_without_mood = []
        
        for track in tracks:
            mood = track.get('mood')
            if mood and mood in mood_groups:
                mood_groups[mood].append(track)
            else:
                tracks_without_mood.append(track)
        
        # Baue sortierte Liste auf
        sorted_tracks = []
        for mood in mood_order:
            sorted_tracks.extend(mood_groups[mood])
        
        sorted_tracks.extend(tracks_without_mood)
        
        return sorted_tracks
    
    def sort_intelligent(self, tracks: List[Dict[str, Any]], 
                        start_energy: float = 0.3, 
                        peak_position: float = 0.7,
                        end_energy: float = 0.4,
                        harmonic_weight: float = 0.3,
                        energy_weight: float = 0.4,
                        bpm_weight: float = 0.3,
                        **kwargs) -> List[Dict[str, Any]]:
        """Intelligente Sortierung mit mehreren Faktoren"""
        if len(tracks) <= 2:
            return tracks
        
        # Berechne Ziel-Energie-Kurve
        target_energies = self._calculate_energy_curve(len(tracks), start_energy, peak_position, end_energy)
        
        # Initialisiere mit zufälliger Reihenfolge
        current_order = tracks.copy()
        random.shuffle(current_order)
        
        # Simulated Annealing für Optimierung
        best_order = current_order.copy()
        best_score = self._calculate_playlist_score(best_order, target_energies, 
                                                   harmonic_weight, energy_weight, bpm_weight)
        
        temperature = 1000.0
        cooling_rate = 0.95
        min_temperature = 1.0
        
        while temperature > min_temperature:
            # Erstelle neue Reihenfolge durch Swap
            new_order = current_order.copy()
            i, j = random.sample(range(len(new_order)), 2)
            new_order[i], new_order[j] = new_order[j], new_order[i]
            
            # Berechne Score
            new_score = self._calculate_playlist_score(new_order, target_energies,
                                                     harmonic_weight, energy_weight, bpm_weight)
            
            # Akzeptiere bessere Lösungen oder schlechtere mit Wahrscheinlichkeit
            if new_score > best_score or random.random() < math.exp((new_score - best_score) / temperature):
                current_order = new_order
                if new_score > best_score:
                    best_order = new_order.copy()
                    best_score = new_score
            
            temperature *= cooling_rate
        
        return best_order
    
    def _calculate_energy_curve(self, length: int, start: float, peak_pos: float, end: float) -> List[float]:
        """Berechnet Ziel-Energie-Kurve"""
        if length <= 1:
            return [start]
        
        energies = []
        peak_index = int(length * peak_pos)
        
        for i in range(length):
            if i <= peak_index:
                # Aufbau zur Spitze
                progress = i / peak_index if peak_index > 0 else 0
                energy = start + (1.0 - start) * progress
            else:
                # Abbau von der Spitze
                progress = (i - peak_index) / (length - peak_index - 1) if length > peak_index + 1 else 0
                energy = 1.0 + (end - 1.0) * progress
            
            energies.append(max(0.0, min(1.0, energy)))
        
        return energies
    
    def _calculate_playlist_score(self, tracks: List[Dict[str, Any]], target_energies: List[float],
                                harmonic_weight: float, energy_weight: float, bpm_weight: float) -> float:
        """Berechnet Qualitäts-Score einer Playlist"""
        if not tracks or len(tracks) != len(target_energies):
            return 0.0
        
        total_score = 0.0
        
        for i, track in enumerate(tracks):
            # Energie-Score
            track_energy = track.get('energy', 0.5)
            target_energy = target_energies[i]
            energy_score = 1.0 - abs(track_energy - target_energy)
            
            # Harmonischer Score (mit vorherigem Track)
            harmonic_score = 1.0
            if i > 0:
                prev_key = tracks[i-1].get('key')
                curr_key = track.get('key')
                if prev_key and curr_key:
                    prev_camelot = self.camelot_wheel.key_to_camelot(prev_key)
                    curr_camelot = self.camelot_wheel.key_to_camelot(curr_key)
                    if prev_camelot and curr_camelot:
                        distance = self.camelot_wheel.calculate_distance(prev_camelot, curr_camelot)
                        harmonic_score = max(0.0, 1.0 - distance / 6.0)  # Normalisiere auf 0-1
            
            # BPM-Score (Übergänge)
            bpm_score = 1.0
            if i > 0:
                prev_bpm = tracks[i-1].get('bpm', 120)
                curr_bpm = track.get('bpm', 120)
                bpm_diff = abs(curr_bpm - prev_bpm)
                bpm_score = max(0.0, 1.0 - bpm_diff / 50.0)  # Normalisiere auf 0-1
            
            # Gewichteter Gesamt-Score
            track_score = (energy_weight * energy_score + 
                          harmonic_weight * harmonic_score + 
                          bpm_weight * bpm_score)
            
            total_score += track_score
        
        return total_score / len(tracks) if tracks else 0.0
    
    def analyze_playlist_flow(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analysiert den Verlauf einer Playlist"""
        if not tracks:
            return {}
        
        analysis = {
            'track_count': len(tracks),
            'total_duration': sum(track.get('duration', 0) for track in tracks),
            'bpm_range': [0, 0],
            'energy_curve': [],
            'key_transitions': [],
            'mood_distribution': {},
            'harmonic_quality': 0.0,
            'energy_flow_quality': 0.0
        }
        
        # BPM-Analyse
        bpms = [track.get('bpm', 0) for track in tracks if track.get('bpm')]
        if bpms:
            analysis['bpm_range'] = [min(bpms), max(bpms)]
        
        # Energie-Kurve
        analysis['energy_curve'] = [track.get('energy', 0) for track in tracks]
        
        # Tonart-Übergänge
        for i in range(1, len(tracks)):
            prev_key = tracks[i-1].get('key')
            curr_key = tracks[i].get('key')
            
            if prev_key and curr_key:
                prev_camelot = self.camelot_wheel.key_to_camelot(prev_key)
                curr_camelot = self.camelot_wheel.key_to_camelot(curr_key)
                
                if prev_camelot and curr_camelot:
                    quality = self.camelot_wheel.get_transition_quality(prev_camelot, curr_camelot)
                    analysis['key_transitions'].append({
                        'from': prev_key,
                        'to': curr_key,
                        'quality': quality
                    })
        
        # Stimmungs-Verteilung
        for track in tracks:
            mood = track.get('mood', 'Unknown')
            analysis['mood_distribution'][mood] = analysis['mood_distribution'].get(mood, 0) + 1
        
        # Harmonische Qualität
        if analysis['key_transitions']:
            quality_scores = {'Perfect': 1.0, 'Excellent': 0.9, 'Good': 0.7, 'Fair': 0.5, 'Poor': 0.3, 'Bad': 0.1}
            total_quality = sum(quality_scores.get(t['quality'], 0.5) for t in analysis['key_transitions'])
            analysis['harmonic_quality'] = total_quality / len(analysis['key_transitions'])
        
        # Energie-Verlauf-Qualität
        if len(analysis['energy_curve']) > 1:
            # Berechne Varianz und Trends
            energies = analysis['energy_curve']
            variance = sum((e - sum(energies)/len(energies))**2 for e in energies) / len(energies)
            analysis['energy_flow_quality'] = min(1.0, variance * 2)  # Normalisiere
        
        return analysis