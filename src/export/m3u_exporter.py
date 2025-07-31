"""M3U Exporter - Export von Playlists im M3U/M3U8 Format"""

import os
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from pathlib import Path


class M3UExporter:
    """Exportiert Playlists im M3U/M3U8 Format"""
    
    def __init__(self):
        self.supported_formats = ['.m3u', '.m3u8']
        self.encoding = 'utf-8'
    
    def export_playlist(self, tracks: List[Dict[str, Any]], 
                       output_path: str, 
                       playlist_name: str = '',
                       use_relative_paths: bool = False,
                       include_metadata: bool = True) -> bool:
        """Exportiert eine Playlist als M3U-Datei"""
        
        if not tracks:
            print("Keine Tracks zum Exportieren")
            return False
        
        try:
            # Stelle sicher, dass das Ausgabeverzeichnis existiert
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding=self.encoding) as f:
                # M3U Header
                f.write('#EXTM3U\n')
                
                # Playlist-Name (falls angegeben)
                if playlist_name:
                    f.write(f'#PLAYLIST:{playlist_name}\n')
                
                # Tracks
                for track in tracks:
                    if include_metadata:
                        self._write_track_with_metadata(f, track, use_relative_paths, output_path)
                    else:
                        self._write_track_simple(f, track, use_relative_paths, output_path)
            
            print(f"Playlist erfolgreich exportiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Exportieren der Playlist: {e}")
            return False
    
    def export_multiple_playlists(self, playlists: Dict[str, List[Dict[str, Any]]], 
                                 output_directory: str,
                                 use_relative_paths: bool = False) -> Dict[str, bool]:
        """Exportiert mehrere Playlists"""
        
        results = {}
        
        for playlist_name, tracks in playlists.items():
            # Bereinige Playlist-Namen für Dateinamen
            safe_name = self._sanitize_filename(playlist_name)
            output_path = os.path.join(output_directory, f"{safe_name}.m3u")
            
            success = self.export_playlist(
                tracks, output_path, playlist_name, use_relative_paths
            )
            results[playlist_name] = success
        
        return results
    
    def validate_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validiert Tracks und gibt Probleme zurück"""
        
        issues = []
        
        for i, track in enumerate(tracks):
            track_issues = []
            
            # Prüfe Dateipfad
            file_path = track.get('file_path')
            if not file_path:
                track_issues.append('Kein Dateipfad angegeben')
            elif not os.path.exists(file_path):
                track_issues.append(f'Datei nicht gefunden: {file_path}')
            
            # Prüfe Metadaten
            if not track.get('title'):
                track_issues.append('Kein Titel angegeben')
            if not track.get('artist'):
                track_issues.append('Kein Künstler angegeben')
            
            if track_issues:
                issues.append({
                    'track_index': i,
                    'track_title': track.get('title', 'Unknown'),
                    'issues': track_issues
                })
        
        return issues
    
    def create_extended_m3u(self, tracks: List[Dict[str, Any]], 
                           output_path: str,
                           playlist_name: str = '') -> bool:
        """Erstellt eine erweiterte M3U mit zusätzlichen Metadaten"""
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding=self.encoding) as f:
                # Extended M3U Header
                f.write('#EXTM3U\n')
                
                # Playlist-Informationen
                if playlist_name:
                    f.write(f'#PLAYLIST:{playlist_name}\n')
                
                # Zusätzliche Playlist-Metadaten
                f.write(f'#EXTENC:{self.encoding}\n')
                f.write(f'#EXTGENRE:Electronic\n')
                
                # Tracks mit erweiterten Metadaten
                for track in tracks:
                    self._write_extended_track_info(f, track, output_path)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Erstellen der erweiterten M3U: {e}")
            return False
    
    def _write_track_with_metadata(self, file_handle, track: Dict[str, Any], 
                                  use_relative_paths: bool, output_path: str):
        """Schreibt Track mit Metadaten"""
        
        # Dauer in Sekunden
        duration = int(track.get('duration', -1))
        
        # Künstler und Titel
        artist = track.get('artist', 'Unknown Artist')
        title = track.get('title', 'Unknown Title')
        
        # EXTINF-Zeile
        file_handle.write(f'#EXTINF:{duration},{artist} - {title}\n')
        
        # Zusätzliche Metadaten (falls verfügbar)
        if track.get('bpm'):
            file_handle.write(f'#EXTBPM:{track["bpm"]}\n')
        
        if track.get('key'):
            file_handle.write(f'#EXTKEY:{track["key"]}\n')
        
        if track.get('energy'):
            energy_percent = int(track['energy'] * 100)
            file_handle.write(f'#EXTENERGY:{energy_percent}\n')
        
        # Dateipfad
        file_path = self._get_file_path(track, use_relative_paths, output_path)
        file_handle.write(f'{file_path}\n')
    
    def _write_track_simple(self, file_handle, track: Dict[str, Any], 
                           use_relative_paths: bool, output_path: str):
        """Schreibt Track ohne erweiterte Metadaten"""
        
        duration = int(track.get('duration', -1))
        artist = track.get('artist', 'Unknown Artist')
        title = track.get('title', 'Unknown Title')
        
        file_handle.write(f'#EXTINF:{duration},{artist} - {title}\n')
        
        file_path = self._get_file_path(track, use_relative_paths, output_path)
        file_handle.write(f'{file_path}\n')
    
    def _write_extended_track_info(self, file_handle, track: Dict[str, Any], output_path: str):
        """Schreibt erweiterte Track-Informationen"""
        
        # Standard EXTINF
        duration = int(track.get('duration', -1))
        artist = track.get('artist', 'Unknown Artist')
        title = track.get('title', 'Unknown Title')
        
        file_handle.write(f'#EXTINF:{duration},{artist} - {title}\n')
        
        # Erweiterte Metadaten
        if track.get('album'):
            file_handle.write(f'#EXTALBUM:{track["album"]}\n')
        
        if track.get('genre'):
            file_handle.write(f'#EXTGENRE:{track["genre"]}\n')
        
        if track.get('year'):
            file_handle.write(f'#EXTYEAR:{track["year"]}\n')
        
        if track.get('bpm'):
            file_handle.write(f'#EXTBPM:{track["bpm"]}\n')
        
        if track.get('key'):
            file_handle.write(f'#EXTKEY:{track["key"]}\n')
        
        if track.get('energy'):
            energy_percent = int(track['energy'] * 100)
            file_handle.write(f'#EXTENERGY:{energy_percent}\n')
        
        if track.get('mood'):
            file_handle.write(f'#EXTMOOD:{track["mood"]}\n')
        
        # Dateipfad
        file_path = track.get('file_path', '')
        file_handle.write(f'{file_path}\n')
    
    def _get_file_path(self, track: Dict[str, Any], use_relative_paths: bool, output_path: str) -> str:
        """Gibt den Dateipfad für die M3U zurück"""
        
        file_path = track.get('file_path', '')
        
        if not file_path:
            return ''
        
        if use_relative_paths:
            try:
                # Berechne relativen Pfad zur M3U-Datei
                output_dir = os.path.dirname(os.path.abspath(output_path))
                rel_path = os.path.relpath(file_path, output_dir)
                return rel_path.replace('\\', '/')
            except ValueError:
                # Fallback auf absoluten Pfad wenn relative Berechnung fehlschlägt
                return file_path
        else:
            return file_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """Bereinigt Dateinamen von ungültigen Zeichen"""
        
        # Entferne/ersetze ungültige Zeichen
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Entferne führende/nachfolgende Leerzeichen und Punkte
        filename = filename.strip(' .')
        
        # Begrenze Länge
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    def read_m3u_playlist(self, file_path: str) -> List[Dict[str, Any]]:
        """Liest eine M3U-Playlist und gibt Track-Informationen zurück"""
        
        tracks = []
        
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                lines = f.readlines()
            
            current_track = {}
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('#EXTINF:'):
                    # Parse EXTINF-Zeile
                    parts = line[8:].split(',', 1)
                    if len(parts) == 2:
                        duration_str, title_info = parts
                        
                        try:
                            current_track['duration'] = int(duration_str)
                        except ValueError:
                            current_track['duration'] = 0
                        
                        # Parse Künstler - Titel
                        if ' - ' in title_info:
                            artist, title = title_info.split(' - ', 1)
                            current_track['artist'] = artist.strip()
                            current_track['title'] = title.strip()
                        else:
                            current_track['title'] = title_info.strip()
                            current_track['artist'] = 'Unknown Artist'
                
                elif line.startswith('#EXTBPM:'):
                    try:
                        current_track['bpm'] = float(line[8:])
                    except ValueError:
                        pass
                
                elif line.startswith('#EXTKEY:'):
                    current_track['key'] = line[8:].strip()
                
                elif line.startswith('#EXTENERGY:'):
                    try:
                        energy_percent = int(line[11:])
                        current_track['energy'] = energy_percent / 100.0
                    except ValueError:
                        pass
                
                elif line and not line.startswith('#'):
                    # Dateipfad
                    current_track['file_path'] = line
                    
                    # Track zur Liste hinzufügen
                    if current_track:
                        tracks.append(current_track.copy())
                        current_track = {}
            
            print(f"M3U-Playlist gelesen: {len(tracks)} Tracks")
            return tracks
            
        except Exception as e:
            print(f"Fehler beim Lesen der M3U-Playlist: {e}")
            return []
    
    def get_playlist_info(self, file_path: str) -> Dict[str, Any]:
        """Gibt Informationen über eine M3U-Playlist zurück"""
        
        info = {
            'file_path': file_path,
            'playlist_name': '',
            'track_count': 0,
            'total_duration': 0,
            'is_extended': False,
            'encoding': 'unknown'
        }
        
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                lines = f.readlines()
            
            track_count = 0
            total_duration = 0
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('#EXTM3U'):
                    info['is_extended'] = True
                
                elif line.startswith('#PLAYLIST:'):
                    info['playlist_name'] = line[10:].strip()
                
                elif line.startswith('#EXTENC:'):
                    info['encoding'] = line[8:].strip()
                
                elif line.startswith('#EXTINF:'):
                    # Parse Dauer
                    parts = line[8:].split(',', 1)
                    if len(parts) >= 1:
                        try:
                            duration = int(parts[0])
                            if duration > 0:
                                total_duration += duration
                        except ValueError:
                            pass
                
                elif line and not line.startswith('#'):
                    # Dateipfad = neuer Track
                    track_count += 1
            
            info['track_count'] = track_count
            info['total_duration'] = total_duration
            
            # Playlist-Name aus Dateiname ableiten falls nicht gesetzt
            if not info['playlist_name']:
                info['playlist_name'] = os.path.splitext(os.path.basename(file_path))[0]
            
        except Exception as e:
            print(f"Fehler beim Lesen der Playlist-Informationen: {e}")
        
        return info