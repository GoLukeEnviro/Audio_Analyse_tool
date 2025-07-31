"""Playlist Rule - Regeln für Playlist-Erstellung"""

import logging
from typing import Dict, List, Any, Callable

logger = logging.getLogger(__name__)

class PlaylistRule:
    """Playlist-Regel Klasse"""
    
    def __init__(self, name: str, condition: Callable[[Dict[str, Any]], bool]):
        self.name = name
        self.condition = condition
        
    def evaluate(self, track: Dict[str, Any]) -> bool:
        """Evaluiert die Regel für einen Track"""
        try:
            return self.condition(track)
        except Exception as e:
            logger.error(f"Fehler bei Regel-Evaluation: {e}")
            return False
    
    def get_name(self) -> str:
        """Gibt den Namen der Regel zurück"""
        return self.name