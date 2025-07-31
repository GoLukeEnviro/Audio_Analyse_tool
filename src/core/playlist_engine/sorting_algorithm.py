"""Sorting Algorithm - Sortieralgorithmen für Playlists"""

import logging
from typing import Dict, List, Any, Callable

logger = logging.getLogger(__name__)

class SortingAlgorithm:
    """Sortieralgorithmus für Playlists"""
    
    def __init__(self, name: str, sort_function: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]):
        self.name = name
        self.sort_function = sort_function
        
    def sort(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sortiert die Track-Liste"""
        try:
            return self.sort_function(tracks)
        except Exception as e:
            logger.error(f"Fehler beim Sortieren: {e}")
            return tracks.copy()
    
    def get_name(self) -> str:
        """Gibt den Namen des Algorithmus zurück"""
        return self.name
    
    @staticmethod
    def sort_by_bpm(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sortiert Tracks nach BPM"""
        return sorted(tracks, key=lambda x: x.get('bpm', 0))
    
    @staticmethod
    def sort_by_energy(tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sortiert Tracks nach Energie"""
        return sorted(tracks, key=lambda x: x.get('energy', 0), reverse=True)