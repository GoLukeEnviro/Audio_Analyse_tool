"""Rekordbox Exporter - Erweiterte XML-Export-Funktionalität für Rekordbox"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import urllib.parse


class RekordboxExporter:
    """Erweiterte Rekordbox XML-Export-Funktionalität"""
    
    def __init__(self):
        self.company = "Trae AI Audio Analysis Tool"
        self.program = "Enhanced Playlist Engine"
        self.version = "2.0.0"
    
    def export_playlist(self, playlist_data: Dict[str, Any], 
                       output_path: str,
                       include_cues: bool = True,
                       include_beatgrid: bool = True,
                       include_waveform: bool = False) -> bool:
        """Exportiert Playlist als Rekordbox XML"""
        try:
            # Erstelle XML-Struktur
            root = self.create_xml_root()
            
            # Füge Collection hinzu
            collection = self.create_collection(playlist_data['playlist'])
            root.append(collection)
            
            # Füge Playlists hinzu
            playlists = self.create_playlists(playlist_data)
            root.append(playlists)
            
            # Schreibe XML-Datei
            self.write_xml_file(root, output_path)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Rekordbox-Export: {e}")
            return False
    
    def create_xml_root(self) -> ET.Element:
        """Erstellt XML-Root-Element"""
        root = ET.Element("DJ_PLAYLISTS")
        root.set("Version", "1.0.0")
        
        # Product Info
        product = ET.SubElement(root, "PRODUCT")
        product.set("Name", self.program)
        product.set("Version", self.version)
        product.set("Company", self.company)
        
        return root
    
    def create_collection(self, tracks: List[Dict[str, Any]]) -> ET.Element:
        """Erstellt Collection-Element mit allen Tracks"""
        collection = ET.SubElement(ET.Element("temp"), "COLLECTION")
        collection.set("Entries", str(len(tracks)))
        
        for track in tracks:
            track_element = self.create_track_element(track)
            collection.append(track_element)
        
        return collection
    
    def create_track_element(self, track: Dict[str, Any]) -> ET.Element:
        """Erstellt Track-Element für Rekordbox"""
        track_elem = ET.Element("TRACK")
        
        # Basis-Attribute
        track_elem.set("TrackID", str(self.generate_track_id(track)))
        track_elem.set("Name", track.get('title', 'Unknown'))
        track_elem.set("Artist", track.get('artist', 'Unknown'))
        track_elem.set("Composer", track.get('composer', ''))
        track_elem.set("Album", track.get('album', ''))
        track_elem.set("Grouping", track.get('grouping', ''))
        track_elem.set("Genre", track.get('genre', ''))
        track_elem.set("Kind", track.get('file_type', 'MP3 File'))
        
        # Technische Daten
        track_elem.set("Size", str(track.get('file_size', 0)))
        track_elem.set("TotalTime", str(track.get('duration', 0)))
        track_elem.set("DiscNumber", str(track.get('disc_number', 0)))
        track_elem.set("TrackNumber", str(track.get('track_number', 0)))
        track_elem.set("Year", str(track.get('year', 0)))
        track_elem.set("AverageBpm", f"{track.get('bpm', 0):.2f}")
        
        # DJ-spezifische Daten
        track_elem.set("DateCreated", datetime.now().strftime("%Y-%m-%d"))
        track_elem.set("DateAdded", datetime.now().strftime("%Y-%m-%d"))
        
        # Tonart
        key = track.get('key', '')
        if key:
            camelot_key = self.convert_to_camelot_key(key)
            track_elem.set("Tonality", camelot_key)
        
        # Energy und Mood als Comments
        energy_score = track.get('energy_score', 0)
        mood_label = track.get('mood_label', '')
        
        comments = []
        if energy_score:
            comments.append(f"Energy: {energy_score:.1f}/10")
        if mood_label:
            comments.append(f"Mood: {mood_label}")
        
        if comments:
            track_elem.set("Comments", " | ".join(comments))
        
        # Dateipfad
        file_path = track.get('file_path', '')
        if file_path:
            # Konvertiere zu Rekordbox-Format
            location = self.convert_file_path(file_path)
            track_elem.set("Location", location)
        
        # Erweiterte Metadaten
        self.add_extended_metadata(track_elem, track)
        
        # Cue Points
        self.add_cue_points(track_elem, track)
        
        # Beat Grid
        self.add_beat_grid(track_elem, track)
        
        return track_elem
    
    def add_extended_metadata(self, track_elem: ET.Element, track: Dict[str, Any]):
        """Fügt erweiterte Metadaten hinzu"""
        # Transition-Daten (falls vorhanden)
        transition = track.get('transition_to_next')
        if transition:
            # Speichere als Custom-Tags
            track_elem.set("MixTime", "30")  # Standard Mix-Zeit
            
            compatibility = transition.get('compatibility_score', 0)
            if compatibility > 0.8:
                track_elem.set("Rating", "5")
            elif compatibility > 0.6:
                track_elem.set("Rating", "4")
            elif compatibility > 0.4:
                track_elem.set("Rating", "3")
            else:
                track_elem.set("Rating", "2")
        
        # Similarity-Daten
        similarity_distance = track.get('similarity_distance')
        if similarity_distance is not None:
            # Konvertiere zu Color-Code
            if similarity_distance < 0.3:
                track_elem.set("Colour", "Green")  # Sehr ähnlich
            elif similarity_distance < 0.6:
                track_elem.set("Colour", "Yellow")  # Mäßig ähnlich
            else:
                track_elem.set("Colour", "Red")  # Wenig ähnlich
    
    def add_cue_points(self, track_elem: ET.Element, track: Dict[str, Any]):
        """Fügt Cue Points hinzu"""
        duration = track.get('duration', 240)
        
        # Standard Cue Points basierend auf Track-Struktur
        cue_points = [
            {"name": "Intro", "position": 0, "type": 0},
            {"name": "Verse", "position": duration * 0.25, "type": 0},
            {"name": "Chorus", "position": duration * 0.5, "type": 0},
            {"name": "Breakdown", "position": duration * 0.75, "type": 0},
            {"name": "Outro", "position": duration * 0.9, "type": 0}
        ]
        
        # Erweiterte Cue Points basierend auf Energy
        energy_score = track.get('energy_score', 5)
        
        if energy_score >= 8:  # High Energy
            cue_points.append({
                "name": "Drop", 
                "position": duration * 0.6, 
                "type": 1  # Hot Cue
            })
        
        if energy_score <= 3:  # Low Energy
            cue_points.append({
                "name": "Ambient", 
                "position": duration * 0.3, 
                "type": 1
            })
        
        # Füge Cue Points zum XML hinzu
        for i, cue in enumerate(cue_points[:8]):  # Max 8 Cues
            cue_elem = ET.SubElement(track_elem, "POSITION_MARK")
            cue_elem.set("Name", cue["name"])
            cue_elem.set("Type", str(cue["type"]))
            cue_elem.set("Start", f"{cue['position']:.3f}")
            cue_elem.set("Num", str(i))
    
    def add_beat_grid(self, track_elem: ET.Element, track: Dict[str, Any]):
        """Fügt Beat Grid hinzu"""
        bpm = track.get('bpm', 120)
        duration = track.get('duration', 240)
        
        if bpm > 0:
            # Berechne Beat-Positionen
            beat_interval = 60.0 / bpm  # Sekunden pro Beat
            beats_count = int(duration / beat_interval)
            
            # Erstelle Beat Grid (vereinfacht)
            tempo_elem = ET.SubElement(track_elem, "TEMPO")
            tempo_elem.set("Inizio", "0.000")
            tempo_elem.set("Bpm", f"{bpm:.2f}")
            tempo_elem.set("Metro", "4/4")
            tempo_elem.set("Battito", "1")
    
    def create_playlists(self, playlist_data: Dict[str, Any]) -> ET.Element:
        """Erstellt Playlists-Element"""
        playlists = ET.Element("PLAYLISTS")
        
        # Root Node
        root_node = ET.SubElement(playlists, "NODE")
        root_node.set("Type", "0")
        root_node.set("Name", "ROOT")
        root_node.set("Count", "1")
        
        # Playlist Node
        playlist_node = ET.SubElement(root_node, "NODE")
        playlist_node.set("Name", playlist_data.get('metadata', {}).get('preset_name', 'Generated Playlist'))
        playlist_node.set("Type", "1")
        playlist_node.set("KeyType", "0")
        playlist_node.set("Entries", str(len(playlist_data['playlist'])))
        
        # Track-Referenzen
        for track in playlist_data['playlist']:
            track_ref = ET.SubElement(playlist_node, "TRACK")
            track_ref.set("Key", str(self.generate_track_id(track)))
        
        return playlists
    
    def generate_track_id(self, track: Dict[str, Any]) -> int:
        """Generiert eindeutige Track-ID"""
        # Verwende Dateipfad für konsistente ID
        file_path = track.get('file_path', '')
        if file_path:
            return abs(hash(file_path)) % (10**8)
        else:
            # Fallback: Hash aus Title + Artist
            content = f"{track.get('title', '')}{track.get('artist', '')}"
            return abs(hash(content)) % (10**8)
    
    def convert_file_path(self, file_path: str) -> str:
        """Konvertiert Dateipfad zu Rekordbox-Format"""
        # Konvertiere zu file:// URL
        if os.path.isabs(file_path):
            # Absolute Pfade
            url = urllib.parse.urljoin('file:', urllib.parse.quote(file_path.replace('\\', '/')))
        else:
            # Relative Pfade
            url = urllib.parse.quote(file_path.replace('\\', '/'))
        
        return url
    
    def convert_to_camelot_key(self, key: str) -> str:
        """Konvertiert Tonart zu Camelot-Notation für Rekordbox"""
        # Mapping von Standard-Tonarten zu Camelot
        key_mapping = {
            'C major': '8B', 'A minor': '8A',
            'G major': '9B', 'E minor': '9A',
            'D major': '10B', 'B minor': '10A',
            'A major': '11B', 'F# minor': '11A',
            'E major': '12B', 'C# minor': '12A',
            'B major': '1B', 'G# minor': '1A',
            'F# major': '2B', 'D# minor': '2A',
            'Db major': '3B', 'Bb minor': '3A',
            'Ab major': '4B', 'F minor': '4A',
            'Eb major': '5B', 'C minor': '5A',
            'Bb major': '6B', 'G minor': '6A',
            'F major': '7B', 'D minor': '7A'
        }
        
        return key_mapping.get(key, key)
    
    def write_xml_file(self, root: ET.Element, output_path: str):
        """Schreibt XML-Datei mit Formatierung"""
        # Erstelle String-Repräsentation
        rough_string = ET.tostring(root, 'unicode')
        
        # Formatiere mit minidom
        reparsed = minidom.parseString(rough_string)
        formatted_xml = reparsed.toprettyxml(indent="  ")
        
        # Entferne leere Zeilen
        lines = [line for line in formatted_xml.split('\n') if line.strip()]
        formatted_xml = '\n'.join(lines)
        
        # Schreibe Datei
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)
    
    def export_multiple_playlists(self, playlists: List[Dict[str, Any]], 
                                 output_dir: str) -> List[str]:
        """Exportiert mehrere Playlists"""
        exported_files = []
        
        for i, playlist_data in enumerate(playlists):
            # Generiere Dateinamen
            preset_name = playlist_data.get('metadata', {}).get('preset_name', f'Playlist_{i+1}')
            safe_name = "".join(c for c in preset_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}.xml"
            
            output_path = os.path.join(output_dir, filename)
            
            if self.export_playlist(playlist_data, output_path):
                exported_files.append(output_path)
        
        return exported_files
    
    def create_smart_playlist_xml(self, playlist_data: Dict[str, Any], 
                                smart_rules: Dict[str, Any]) -> ET.Element:
        """Erstellt Smart Playlist mit Regeln"""
        # TODO: Implementiere Smart Playlist-Regeln für Rekordbox
        # Rekordbox unterstützt Smart Playlists mit XML-Regeln
        
        playlist_node = ET.Element("NODE")
        playlist_node.set("Type", "2")  # Smart Playlist
        playlist_node.set("Name", playlist_data.get('metadata', {}).get('preset_name', 'Smart Playlist'))
        
        # Füge Smart-Regeln hinzu
        if smart_rules:
            # BPM-Regel
            if 'bpm_range' in smart_rules:
                bpm_min, bpm_max = smart_rules['bpm_range']
                # TODO: Implementiere BPM-Regel-XML
            
            # Energy-Regel
            if 'energy_range' in smart_rules:
                energy_min, energy_max = smart_rules['energy_range']
                # TODO: Implementiere Energy-Regel-XML
        
        return playlist_node


class M3UExporter:
    """M3U Playlist Exporter"""
    
    def export_playlist(self, playlist_data: Dict[str, Any], output_path: str) -> bool:
        """Exportiert Playlist als M3U-Datei"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                
                for track in playlist_data['playlist']:
                    duration = track.get('duration', 0)
                    title = track.get('title', 'Unknown')
                    artist = track.get('artist', 'Unknown')
                    file_path = track.get('file_path', '')
                    
                    # Extended Info
                    f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                    
                    # Dateipfad
                    if file_path:
                        f.write(f"{file_path}\n")
            
            return True
            
        except Exception as e:
            print(f"Fehler beim M3U-Export: {e}")
            return False


class JSONExporter:
    """JSON Metadata Exporter"""
    
    def export_playlist(self, playlist_data: Dict[str, Any], output_path: str) -> bool:
        """Exportiert Playlist-Metadaten als JSON"""
        try:
            import json
            
            # Erweitere Metadaten
            export_data = {
                'playlist': playlist_data['playlist'],
                'metadata': playlist_data.get('metadata', {}),
                'export_info': {
                    'exported_at': datetime.now().isoformat(),
                    'exporter': 'Enhanced Playlist Engine',
                    'version': '2.0.0'
                },
                'analysis': self.generate_playlist_analysis(playlist_data['playlist'])
            }
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim JSON-Export: {e}")
            return False
    
    def generate_playlist_analysis(self, playlist: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generiert Playlist-Analyse"""
        if not playlist:
            return {}
        
        # BPM-Analyse
        bpms = [track.get('bpm', 0) for track in playlist if track.get('bpm', 0) > 0]
        bpm_analysis = {
            'min': min(bpms) if bpms else 0,
            'max': max(bpms) if bpms else 0,
            'avg': sum(bpms) / len(bpms) if bpms else 0,
            'progression': bpms
        }
        
        # Energy-Analyse
        energies = [track.get('energy_score', 0) for track in playlist]
        energy_analysis = {
            'min': min(energies) if energies else 0,
            'max': max(energies) if energies else 0,
            'avg': sum(energies) / len(energies) if energies else 0,
            'progression': energies
        }
        
        # Key-Analyse
        keys = [track.get('key', '') for track in playlist if track.get('key')]
        key_distribution = {}
        for key in keys:
            key_distribution[key] = key_distribution.get(key, 0) + 1
        
        # Mood-Analyse
        moods = [track.get('mood_label', '') for track in playlist if track.get('mood_label')]
        mood_distribution = {}
        for mood in moods:
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
        
        return {
            'bpm': bpm_analysis,
            'energy': energy_analysis,
            'key_distribution': key_distribution,
            'mood_distribution': mood_distribution,
            'total_tracks': len(playlist),
            'total_duration': sum(track.get('duration', 0) for track in playlist)
        }


class EnhancedExportManager:
    """Erweiterte Export-Manager-Klasse"""
    
    def __init__(self):
        self.rekordbox_exporter = RekordboxExporter()
        self.m3u_exporter = M3UExporter()
        self.json_exporter = JSONExporter()
    
    def export_playlist(self, playlist_data: Dict[str, Any], 
                       output_dir: str,
                       formats: List[str] = None) -> Dict[str, str]:
        """Exportiert Playlist in verschiedenen Formaten"""
        if formats is None:
            formats = ['rekordbox', 'm3u', 'json']
        
        results = {}
        
        # Erstelle Basis-Dateinamen
        preset_name = playlist_data.get('metadata', {}).get('preset_name', 'Generated_Playlist')
        safe_name = "".join(c for c in preset_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        # Rekordbox XML
        if 'rekordbox' in formats:
            xml_path = os.path.join(output_dir, f"{safe_name}.xml")
            if self.rekordbox_exporter.export_playlist(playlist_data, xml_path):
                results['rekordbox'] = xml_path
            else:
                results['rekordbox'] = None
        
        # M3U Playlist
        if 'm3u' in formats:
            m3u_path = os.path.join(output_dir, f"{safe_name}.m3u")
            if self.m3u_exporter.export_playlist(playlist_data, m3u_path):
                results['m3u'] = m3u_path
            else:
                results['m3u'] = None
        
        # JSON Metadata
        if 'json' in formats:
            json_path = os.path.join(output_dir, f"{safe_name}_metadata.json")
            if self.json_exporter.export_playlist(playlist_data, json_path):
                results['json'] = json_path
            else:
                results['json'] = None
        
        return results
    
    def batch_export(self, playlists: List[Dict[str, Any]], 
                    output_dir: str,
                    formats: List[str] = None) -> List[Dict[str, str]]:
        """Batch-Export mehrerer Playlists"""
        results = []
        
        for playlist_data in playlists:
            result = self.export_playlist(playlist_data, output_dir, formats)
            results.append(result)
        
        return results