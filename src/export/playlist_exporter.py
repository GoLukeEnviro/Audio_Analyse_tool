"""Playlist Exporter - Export von Playlists in verschiedene Formate"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PlaylistExporter:
    """Exportiert Playlists in verschiedene Formate"""
    
    def __init__(self):
        self.supported_formats = ['m3u', 'json', 'csv']
        
    def export_m3u(self, tracks: List[Dict[str, Any]], output_path: str) -> bool:
        """Exportiert Playlist als M3U-Datei"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for track in tracks:
                    file_path = track.get('file_path', '')
                    title = track.get('title', 'Unknown')
                    artist = track.get('artist', 'Unknown')
                    duration = int(track.get('duration', 0))
                    
                    f.write(f'#EXTINF:{duration},{artist} - {title}\n')
                    f.write(f'{file_path}\n')
            
            logger.info(f"M3U-Playlist exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim M3U-Export: {e}")
            return False
    
    def export_json(self, tracks: List[Dict[str, Any]], output_path: str) -> bool:
        """Exportiert Playlist als JSON-Datei"""
        try:
            playlist_data = {
                'version': '1.0',
                'created': str(Path().cwd()),
                'tracks': tracks
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON-Playlist exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim JSON-Export: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Export-Formate zurück"""
        return self.supported_formats.copy()