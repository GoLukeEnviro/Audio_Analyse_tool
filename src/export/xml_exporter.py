"""XML Exporter - Export von Playlists im Rekordbox XML Format"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote


class XMLExporter:
    """Exportiert Playlists im Rekordbox XML Format"""
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.version = '1.0.0'
    
    def export_rekordbox_xml(self, playlists: Dict[str, List[Dict[str, Any]]], 
                            output_path: str,
                            collection_name: str = 'Audio Analysis Collection') -> bool:
        """Exportiert Playlists als Rekordbox XML"""
        
        try:
            # Erstelle Root-Element
            root = ET.Element('DJ_PLAYLISTS')
            root.set('Version', self.version)
            
            # Sammle alle einzigartigen Tracks
            all_tracks = {}
            track_id = 1
            
            for playlist_name, tracks in playlists.items():
                for track in tracks:
                    file_path = track.get('file_path', '')
                    if file_path and file_path not in all_tracks:
                        track_data = track.copy()
                        track_data['TrackID'] = track_id
                        all_tracks[file_path] = track_data
                        track_id += 1
            
            # COLLECTION Element
            collection = ET.SubElement(root, 'COLLECTION')
            collection.set('Entries', str(len(all_tracks)))
            
            # Füge alle Tracks zur Collection hinzu
            for file_path, track in all_tracks.items():
                self._add_track_to_collection(collection, track)
            
            # PLAYLISTS Element
            playlists_elem = ET.SubElement(root, 'PLAYLISTS')
            
            # Root Playlist Node
            root_node = ET.SubElement(playlists_elem, 'NODE')
            root_node.set('Type', '0')
            root_node.set('Name', collection_name)
            root_node.set('Count', str(len(playlists)))
            
            # Füge jede Playlist hinzu
            for playlist_name, tracks in playlists.items():
                self._add_playlist_node(root_node, playlist_name, tracks, all_tracks)
            
            # Schreibe XML-Datei
            self._write_xml_file(root, output_path)
            
            print(f"Rekordbox XML erfolgreich exportiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Exportieren der Rekordbox XML: {e}")
            return False
    
    def export_single_playlist_xml(self, tracks: List[Dict[str, Any]], 
                                  output_path: str,
                                  playlist_name: str = 'Exported Playlist') -> bool:
        """Exportiert eine einzelne Playlist als XML"""
        
        playlists = {playlist_name: tracks}
        return self.export_rekordbox_xml(playlists, output_path)
    
    def create_traktor_nml(self, playlists: Dict[str, List[Dict[str, Any]]], 
                          output_path: str) -> bool:
        """Erstellt eine Traktor NML-Datei"""
        
        try:
            # NML Root
            root = ET.Element('NML')
            root.set('VERSION', '19')
            
            # HEAD
            head = ET.SubElement(root, 'HEAD')
            head.set('COMPANY', 'Audio Analysis Tool')
            head.set('PROGRAM', 'Audio Analysis Tool')
            head.set('VERSION', self.version)
            
            # MUSICFOLDERS
            musicfolders = ET.SubElement(root, 'MUSICFOLDERS')
            
            # COLLECTION
            collection = ET.SubElement(root, 'COLLECTION')
            collection.set('ENTRIES', str(sum(len(tracks) for tracks in playlists.values())))
            
            # Sammle alle Tracks
            all_tracks = {}
            for playlist_tracks in playlists.values():
                for track in playlist_tracks:
                    file_path = track.get('file_path', '')
                    if file_path:
                        all_tracks[file_path] = track
            
            # Füge Tracks zur Collection hinzu
            for track in all_tracks.values():
                self._add_traktor_entry(collection, track)
            
            # PLAYLISTS
            playlists_elem = ET.SubElement(root, 'PLAYLISTS')
            
            # Füge Playlists hinzu
            for playlist_name, tracks in playlists.items():
                self._add_traktor_playlist(playlists_elem, playlist_name, tracks)
            
            # Schreibe NML-Datei
            self._write_xml_file(root, output_path)
            
            print(f"Traktor NML erfolgreich exportiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Exportieren der Traktor NML: {e}")
            return False
    
    def _add_track_to_collection(self, collection: ET.Element, track: Dict[str, Any]):
        """Fügt einen Track zur Rekordbox Collection hinzu"""
        
        track_elem = ET.SubElement(collection, 'TRACK')
        
        # Basis-Attribute
        track_elem.set('TrackID', str(track.get('TrackID', 0)))
        track_elem.set('Name', track.get('title', 'Unknown Title'))
        track_elem.set('Artist', track.get('artist', 'Unknown Artist'))
        track_elem.set('Album', track.get('album', ''))
        track_elem.set('Genre', track.get('genre', ''))
        track_elem.set('Kind', 'MP3 File')
        
        # Dateipfad
        file_path = track.get('file_path', '')
        if file_path:
            # Konvertiere zu file:// URL
            file_url = 'file://localhost/' + file_path.replace('\\', '/').replace(':', '%3A')
            track_elem.set('Location', file_url)
        
        # Audio-Eigenschaften
        if track.get('duration'):
            track_elem.set('TotalTime', str(int(track['duration'])))
        
        if track.get('bpm'):
            # Rekordbox speichert BPM * 100
            bpm_value = int(float(track['bpm']) * 100)
            track_elem.set('AverageBpm', str(bpm_value))
        
        if track.get('key'):
            # Konvertiere Tonart zu Rekordbox-Format
            key_value = self._convert_key_to_rekordbox(track['key'])
            track_elem.set('Tonality', str(key_value))
        
        # Zusätzliche Metadaten
        if track.get('year'):
            track_elem.set('Year', str(track['year']))
        
        if track.get('bitrate'):
            track_elem.set('BitRate', str(track['bitrate']))
        
        # Energie als Comment
        if track.get('energy'):
            energy_percent = int(track['energy'] * 100)
            track_elem.set('Comments', f'Energy: {energy_percent}%')
        
        # Datei-Informationen
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            track_elem.set('Size', str(file_size))
            
            # Modification Date
            mod_time = os.path.getmtime(file_path)
            mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
            track_elem.set('DateAdded', mod_date)
    
    def _add_playlist_node(self, parent: ET.Element, playlist_name: str, 
                          tracks: List[Dict[str, Any]], all_tracks: Dict[str, Dict[str, Any]]):
        """Fügt einen Playlist-Node hinzu"""
        
        node = ET.SubElement(parent, 'NODE')
        node.set('Type', '1')  # Playlist Type
        node.set('Name', playlist_name)
        node.set('KeyType', '0')
        node.set('Entries', str(len(tracks)))
        
        # Füge Tracks hinzu
        for track in tracks:
            file_path = track.get('file_path', '')
            if file_path in all_tracks:
                track_data = all_tracks[file_path]
                track_elem = ET.SubElement(node, 'TRACK')
                track_elem.set('Key', str(track_data.get('TrackID', 0)))
    
    def _add_traktor_entry(self, collection: ET.Element, track: Dict[str, Any]):
        """Fügt einen Track zur Traktor Collection hinzu"""
        
        entry = ET.SubElement(collection, 'ENTRY')
        
        # Location
        location = ET.SubElement(entry, 'LOCATION')
        file_path = track.get('file_path', '')
        if file_path:
            location.set('DIR', os.path.dirname(file_path) + '/')
            location.set('FILE', os.path.basename(file_path))
            location.set('VOLUME', os.path.splitdrive(file_path)[0])
            location.set('VOLUMEID', 'C:')
        
        # Album
        if track.get('album'):
            album = ET.SubElement(entry, 'ALBUM')
            album.set('TITLE', track['album'])
        
        # Modification Info
        modification_info = ET.SubElement(entry, 'MODIFICATION_INFO')
        modification_info.set('AUTHOR_TYPE', 'user')
        
        # Info
        info = ET.SubElement(entry, 'INFO')
        if track.get('bitrate'):
            info.set('BITRATE', str(track['bitrate']))
        if track.get('genre'):
            info.set('GENRE', track['genre'])
        if track.get('title'):
            info.set('TITLE', track['title'])
        if track.get('artist'):
            info.set('ARTIST', track['artist'])
        
        # Tempo
        if track.get('bpm'):
            tempo = ET.SubElement(entry, 'TEMPO')
            tempo.set('BPM', str(track['bpm']))
            tempo.set('BPM_QUALITY', '100')
        
        # Musical Key
        if track.get('key'):
            musical_key = ET.SubElement(entry, 'MUSICAL_KEY')
            musical_key.set('VALUE', str(self._convert_key_to_traktor(track['key'])))
    
    def _add_traktor_playlist(self, playlists_elem: ET.Element, 
                             playlist_name: str, tracks: List[Dict[str, Any]]):
        """Fügt eine Traktor Playlist hinzu"""
        
        node = ET.SubElement(playlists_elem, 'NODE')
        node.set('TYPE', 'PLAYLIST')
        node.set('NAME', playlist_name)
        
        playlist = ET.SubElement(node, 'PLAYLIST')
        playlist.set('ENTRIES', str(len(tracks)))
        playlist.set('TYPE', 'LIST')
        playlist.set('UUID', self._generate_uuid())
        
        # Füge Tracks hinzu
        for track in tracks:
            entry = ET.SubElement(playlist, 'ENTRY')
            
            primarykey = ET.SubElement(entry, 'PRIMARYKEY')
            primarykey.set('TYPE', 'TRACK')
            primarykey.set('KEY', track.get('file_path', ''))
    
    def _convert_key_to_rekordbox(self, key: str) -> int:
        """Konvertiert Tonart zu Rekordbox-Zahlenwert"""
        
        # Rekordbox Key Mapping
        key_mapping = {
            'C major': 1, 'Db major': 2, 'D major': 3, 'Eb major': 4,
            'E major': 5, 'F major': 6, 'F# major': 7, 'G major': 8,
            'Ab major': 9, 'A major': 10, 'Bb major': 11, 'B major': 12,
            'A minor': 13, 'Bb minor': 14, 'B minor': 15, 'C minor': 16,
            'C# minor': 17, 'D minor': 18, 'D# minor': 19, 'E minor': 20,
            'F minor': 21, 'F# minor': 22, 'G minor': 23, 'G# minor': 24
        }
        
        return key_mapping.get(key, 0)
    
    def _convert_key_to_traktor(self, key: str) -> int:
        """Konvertiert Tonart zu Traktor-Zahlenwert"""
        
        # Traktor Key Mapping (0-23)
        key_mapping = {
            'C major': 0, 'C# major': 1, 'D major': 2, 'D# major': 3,
            'E major': 4, 'F major': 5, 'F# major': 6, 'G major': 7,
            'G# major': 8, 'A major': 9, 'A# major': 10, 'B major': 11,
            'C minor': 12, 'C# minor': 13, 'D minor': 14, 'D# minor': 15,
            'E minor': 16, 'F minor': 17, 'F# minor': 18, 'G minor': 19,
            'G# minor': 20, 'A minor': 21, 'A# minor': 22, 'B minor': 23
        }
        
        return key_mapping.get(key, 0)
    
    def _generate_uuid(self) -> str:
        """Generiert eine einfache UUID für Traktor"""
        import uuid
        return str(uuid.uuid4()).upper()
    
    def _write_xml_file(self, root: ET.Element, output_path: str):
        """Schreibt XML-Element in Datei mit schöner Formatierung"""
        
        # Erstelle Ausgabeverzeichnis
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Konvertiere zu String mit schöner Formatierung
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent='  ', encoding=None)
        
        # Entferne leere Zeilen
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        formatted_xml = '\n'.join(lines)
        
        # Schreibe Datei
        with open(output_path, 'w', encoding=self.encoding) as f:
            f.write(formatted_xml)
    
    def validate_xml_export(self, file_path: str) -> Dict[str, Any]:
        """Validiert eine exportierte XML-Datei"""
        
        validation_result = {
            'is_valid': False,
            'track_count': 0,
            'playlist_count': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Prüfe Root-Element
            if root.tag not in ['DJ_PLAYLISTS', 'NML']:
                validation_result['errors'].append(f'Unbekanntes Root-Element: {root.tag}')
                return validation_result
            
            # Zähle Tracks und Playlists
            if root.tag == 'DJ_PLAYLISTS':
                # Rekordbox Format
                collection = root.find('COLLECTION')
                if collection is not None:
                    tracks = collection.findall('TRACK')
                    validation_result['track_count'] = len(tracks)
                
                playlists_elem = root.find('PLAYLISTS')
                if playlists_elem is not None:
                    playlists = playlists_elem.findall('.//NODE[@Type="1"]')
                    validation_result['playlist_count'] = len(playlists)
            
            elif root.tag == 'NML':
                # Traktor Format
                collection = root.find('COLLECTION')
                if collection is not None:
                    entries = collection.findall('ENTRY')
                    validation_result['track_count'] = len(entries)
                
                playlists_elem = root.find('PLAYLISTS')
                if playlists_elem is not None:
                    playlists = playlists_elem.findall('.//NODE[@TYPE="PLAYLIST"]')
                    validation_result['playlist_count'] = len(playlists)
            
            # Prüfe auf fehlende Dateipfade
            missing_files = 0
            if root.tag == 'DJ_PLAYLISTS':
                for track in root.findall('.//TRACK'):
                    location = track.get('Location', '')
                    if location.startswith('file://localhost/'):
                        file_path = location[17:].replace('%3A', ':').replace('/', '\\')
                        if not os.path.exists(file_path):
                            missing_files += 1
            
            if missing_files > 0:
                validation_result['warnings'].append(f'{missing_files} Dateien nicht gefunden')
            
            validation_result['is_valid'] = True
            
        except ET.ParseError as e:
            validation_result['errors'].append(f'XML Parse Error: {e}')
        except Exception as e:
            validation_result['errors'].append(f'Validation Error: {e}')
        
        return validation_result
    
    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Export-Formate zurück"""
        return ['.xml', '.nml']