import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Optional
from pathlib import Path
from urllib.parse import quote
import datetime

class PlaylistExporter:
    def __init__(self):
        self.supported_formats = ['m3u', 'm3u8', 'xml', 'rekordbox_xml']
    
    def export_m3u(self, playlist: Dict, output_path: str, extended: bool = True) -> bool:
        try:
            tracks = playlist.get('tracks', [])
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if extended:
                    f.write('#EXTM3U\n')
                
                for track in tracks:
                    if 'error' in track:
                        continue
                    
                    file_path = track.get('file_path', '')
                    if not file_path:
                        continue
                    
                    if extended:
                        duration = int(track.get('duration', 0))
                        artist = track.get('artist', 'Unknown Artist')
                        title = track.get('title', track.get('filename', 'Unknown Title'))
                        
                        # Remove file extension from title if it's just the filename
                        if title == track.get('filename', ''):
                            title = os.path.splitext(title)[0]
                        
                        f.write(f'#EXTINF:{duration},{artist} - {title}\n')
                        
                        # Add custom tags for DJ software
                        bpm = track.get('bpm', 0)
                        key = track.get('key', '')
                        if bpm or key:
                            f.write(f'#EXTBPM:{bpm:.1f}\n')
                            f.write(f'#EXTKEY:{key}\n')
                    
                    # Convert to relative path if possible
                    rel_path = self._get_relative_path(file_path, output_path)
                    f.write(f'{rel_path}\n')
            
            return True
            
        except Exception as e:
            print(f"Error exporting M3U: {e}")
            return False
    
    def export_rekordbox_xml(self, playlist: Dict, output_path: str, collection_name: str = "Audio Analysis Tool") -> bool:
        try:
            tracks = playlist.get('tracks', [])
            
            # Create root element
            dj_playlists = ET.Element('DJ_PLAYLISTS', Version="1.0.0")
            
            # Create PRODUCT element
            product = ET.SubElement(dj_playlists, 'PRODUCT', 
                                  Name="rekordbox", 
                                  Version="6.0.0", 
                                  Company="Pioneer DJ")
            
            # Create COLLECTION element
            collection = ET.SubElement(dj_playlists, 'COLLECTION', Entries=str(len(tracks)))
            
            # Add tracks to collection
            track_ids = {}
            for i, track in enumerate(tracks):
                if 'error' in track:
                    continue
                
                track_id = str(i + 1)
                track_ids[track.get('file_path', '')] = track_id
                
                track_elem = ET.SubElement(collection, 'TRACK')
                track_elem.set('TrackID', track_id)
                track_elem.set('Name', self._get_track_title(track))
                track_elem.set('Artist', track.get('artist', 'Unknown Artist'))
                track_elem.set('Album', track.get('album', ''))
                track_elem.set('Genre', track.get('genre', ''))
                track_elem.set('Kind', 'MP3 File')
                track_elem.set('Size', str(track.get('file_size', 0)))
                track_elem.set('TotalTime', str(int(track.get('duration', 0))))
                track_elem.set('DiscNumber', '0')
                track_elem.set('TrackNumber', '0')
                track_elem.set('Year', '0')
                track_elem.set('AverageBpm', f"{track.get('bpm', 0):.2f}")
                track_elem.set('DateCreated', self._get_date_string())
                track_elem.set('DateAdded', self._get_date_string())
                track_elem.set('BitRate', '320')
                track_elem.set('SampleRate', '44100')
                track_elem.set('Comments', '')
                track_elem.set('PlayCount', '0')
                track_elem.set('Rating', '0')
                track_elem.set('Location', f"file://localhost/{quote(track.get('file_path', '').replace(os.sep, '/'), safe='/:')}")
                track_elem.set('Remixer', '')
                track_elem.set('Tonality', self._convert_key_to_rekordbox(track.get('key', '')))
                track_elem.set('Label', '')
                track_elem.set('Mix', '')
                
                # Add tempo information
                tempo_elem = ET.SubElement(track_elem, 'TEMPO')
                tempo_elem.set('Inizio', '0.000')
                tempo_elem.set('Bpm', f"{track.get('bpm', 0):.2f}")
                tempo_elem.set('Metro', '4/4')
                tempo_elem.set('Battito', '1')
            
            # Create PLAYLISTS element
            playlists = ET.SubElement(dj_playlists, 'PLAYLISTS')
            
            # Create root node
            root_node = ET.SubElement(playlists, 'NODE', Type="0", Name="ROOT", Count="1")
            
            # Create playlist node
            playlist_node = ET.SubElement(root_node, 'NODE', 
                                        Type="1", 
                                        Name=playlist.get('name', 'Generated Playlist'),
                                        KeyType="0",
                                        Entries=str(len([t for t in tracks if 'error' not in t])))
            
            # Add tracks to playlist
            for track in tracks:
                if 'error' in track:
                    continue
                
                file_path = track.get('file_path', '')
                if file_path in track_ids:
                    track_elem = ET.SubElement(playlist_node, 'TRACK', Key=track_ids[file_path])
            
            # Write to file with proper formatting
            rough_string = ET.tostring(dj_playlists, 'unicode')
            reparsed = minidom.parseString(rough_string)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(reparsed.documentElement.toprettyxml(indent="  ")[23:])  # Remove extra XML declaration
            
            return True
            
        except Exception as e:
            print(f"Error exporting Rekordbox XML: {e}")
            return False
    
    def export_playlist(self, playlist: Dict, output_path: str, format_type: str = 'm3u', **kwargs) -> bool:
        format_type = format_type.lower()
        
        if format_type not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format_type}. Supported: {self.supported_formats}")
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format_type in ['m3u', 'm3u8']:
            return self.export_m3u(playlist, output_path, extended=True)
        elif format_type in ['xml', 'rekordbox_xml']:
            return self.export_rekordbox_xml(playlist, output_path, **kwargs)
        
        return False
    
    def batch_export(self, playlists: List[Dict], output_directory: str, format_type: str = 'm3u') -> Dict[str, bool]:
        results = {}
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for playlist in playlists:
            playlist_name = playlist.get('name', 'Unnamed Playlist')
            safe_name = self._sanitize_filename(playlist_name)
            
            if format_type.lower() in ['m3u', 'm3u8']:
                output_path = output_dir / f"{safe_name}.m3u"
            elif format_type.lower() in ['xml', 'rekordbox_xml']:
                output_path = output_dir / f"{safe_name}.xml"
            else:
                results[playlist_name] = False
                continue
            
            success = self.export_playlist(playlist, str(output_path), format_type)
            results[playlist_name] = success
        
        return results
    
    def _get_relative_path(self, file_path: str, playlist_path: str) -> str:
        try:
            file_abs = Path(file_path).resolve()
            playlist_abs = Path(playlist_path).resolve().parent
            return str(file_abs.relative_to(playlist_abs))
        except ValueError:
            # If relative path can't be computed, return absolute path
            return file_path
    
    def _get_track_title(self, track: Dict) -> str:
        title = track.get('title', '')
        if not title:
            filename = track.get('filename', 'Unknown')
            title = os.path.splitext(filename)[0]
        return title
    
    def _get_date_string(self) -> str:
        return datetime.datetime.now().strftime('%Y-%m-%d')
    
    def _convert_key_to_rekordbox(self, key: str) -> str:
        # Convert our key format to Rekordbox format
        key_mapping = {
            'C': '1d', 'C#': '8d', 'D': '3d', 'D#': '10d', 'E': '5d', 'F': '12d',
            'F#': '7d', 'G': '2d', 'G#': '9d', 'A': '4d', 'A#': '11d', 'B': '6d',
            'Cm': '1m', 'C#m': '8m', 'Dm': '3m', 'D#m': '10m', 'Em': '5m', 'Fm': '12m',
            'F#m': '7m', 'Gm': '2m', 'G#m': '9m', 'Am': '4m', 'A#m': '11m', 'Bm': '6m'
        }
        return key_mapping.get(key, '')
    
    def _sanitize_filename(self, filename: str) -> str:
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    
    def get_export_info(self, playlist: Dict) -> Dict:
        tracks = playlist.get('tracks', [])
        valid_tracks = [t for t in tracks if 'error' not in t]
        
        total_duration = sum(track.get('duration', 0) for track in valid_tracks)
        total_size = sum(track.get('file_size', 0) for track in valid_tracks)
        
        return {
            'total_tracks': len(valid_tracks),
            'total_duration': total_duration,
            'total_duration_formatted': self._format_duration(total_duration),
            'total_size': total_size,
            'total_size_formatted': self._format_file_size(total_size),
            'avg_bpm': playlist.get('avg_bpm', 0),
            'key_distribution': playlist.get('key_distribution', {}),
            'mood_profile': playlist.get('mood_profile', {})
        }
    
    def _format_duration(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def _format_file_size(self, bytes_size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"