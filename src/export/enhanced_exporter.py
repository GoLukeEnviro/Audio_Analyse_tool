"""Enhanced Playlist Exporter - Erweiterte Export-Engine für DJ-Software-Integration"""

import json
import xml.etree.ElementTree as ET
import csv
import logging
import base64
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import hashlib
import zipfile
import tempfile

logger = logging.getLogger(__name__)

@dataclass
class ExportConfig:
    """Konfiguration für Playlist-Export"""
    format: str = 'rekordbox'  # rekordbox, serato, traktor, m3u8, json, csv
    include_metadata: bool = True
    include_analysis: bool = True
    include_energy_curve: bool = True
    include_cue_points: bool = False
    relative_paths: bool = True
    backup_original: bool = True
    compression: bool = False
    encoding: str = 'utf-8'
    
class EnhancedPlaylistExporter:
    """Erweiterte Export-Engine für verschiedene DJ-Software-Formate"""
    
    def __init__(self):
        # Unterstützte Formate
        self.supported_formats = {
            'rekordbox': self._export_rekordbox,
            'serato': self._export_serato,
            'traktor': self._export_traktor,
            'virtual_dj': self._export_virtual_dj,
            'djay_pro': self._export_djay_pro,
            'm3u8': self._export_m3u8,
            'json': self._export_json,
            'csv': self._export_csv,
            'xml': self._export_xml,
            'cue_sheet': self._export_cue_sheet
        }
        
        # Format-spezifische Metadaten
        self.format_metadata = {
            'rekordbox': {
                'extension': '.xml',
                'description': 'Rekordbox XML Collection',
                'supports_cues': True,
                'supports_analysis': True,
                'supports_energy': False
            },
            'serato': {
                'extension': '.crate',
                'description': 'Serato Crate File',
                'supports_cues': True,
                'supports_analysis': True,
                'supports_energy': False
            },
            'traktor': {
                'extension': '.nml',
                'description': 'Traktor Collection',
                'supports_cues': True,
                'supports_analysis': True,
                'supports_energy': False
            },
            'm3u8': {
                'extension': '.m3u8',
                'description': 'Extended M3U Playlist',
                'supports_cues': False,
                'supports_analysis': False,
                'supports_energy': False
            },
            'json': {
                'extension': '.json',
                'description': 'JSON Playlist with Full Metadata',
                'supports_cues': True,
                'supports_analysis': True,
                'supports_energy': True
            }
        }
        
        # Export-Statistiken
        self.export_stats = {
            'total_exports': 0,
            'successful_exports': 0,
            'failed_exports': 0,
            'formats_used': {},
            'avg_export_time': 0.0
        }
        
        logger.info("EnhancedPlaylistExporter initialisiert")
    
    def export_playlist(self, 
                       playlist_data: Dict[str, Any],
                       output_path: str,
                       config: Optional[ExportConfig] = None) -> Dict[str, Any]:
        """Exportiert Playlist in gewähltem Format"""
        import time
        start_time = time.time()
        
        config = config or ExportConfig()
        
        try:
            # Validierung
            if config.format not in self.supported_formats:
                raise ValueError(f"Unsupported format: {config.format}")
            
            # Backup erstellen falls gewünscht
            if config.backup_original and Path(output_path).exists():
                self._create_backup(output_path)
            
            # Export durchführen
            export_func = self.supported_formats[config.format]
            result = export_func(playlist_data, output_path, config)
            
            # Statistiken aktualisieren
            export_time = time.time() - start_time
            self._update_export_stats(config.format, export_time, True)
            
            return {
                'success': True,
                'output_path': output_path,
                'format': config.format,
                'export_time': export_time,
                'tracks_exported': len(playlist_data.get('playlist', [])),
                'metadata': result
            }
            
        except Exception as e:
            export_time = time.time() - start_time
            self._update_export_stats(config.format, export_time, False)
            
            logger.error(f"Export failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': config.format,
                'export_time': export_time
            }
    
    def _export_rekordbox(self, playlist_data: Dict[str, Any], 
                         output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert für Rekordbox XML Format"""
        root = ET.Element('DJ_PLAYLISTS')
        root.set('Version', '1.0.0')
        
        # Product Info
        product = ET.SubElement(root, 'PRODUCT')
        product.set('Name', 'Audio Analysis Tool')
        product.set('Version', '1.0')
        product.set('Company', 'DJ Tools')
        
        # Collection
        collection = ET.SubElement(root, 'COLLECTION')
        collection.set('Entries', str(len(playlist_data.get('playlist', []))))
        
        # Tracks
        for i, track in enumerate(playlist_data.get('playlist', [])):
            track_elem = ET.SubElement(collection, 'TRACK')
            
            # Basic Info
            track_elem.set('TrackID', str(i + 1))
            track_elem.set('Name', track.get('title', 'Unknown'))
            track_elem.set('Artist', track.get('artist', 'Unknown'))
            track_elem.set('Album', track.get('album', ''))
            track_elem.set('Genre', track.get('genre', ''))
            track_elem.set('Kind', 'MP3 File')
            track_elem.set('Size', str(track.get('file_size', 0)))
            track_elem.set('TotalTime', str(int(track.get('duration', 0))))
            track_elem.set('SampleRate', str(track.get('sample_rate', 44100)))
            track_elem.set('BitRate', str(track.get('bitrate', 320)))
            
            # File Location
            file_path = track.get('file_path', '')
            if config.relative_paths:
                file_path = str(Path(file_path).name)
            track_elem.set('Location', f'file://localhost/{file_path}')
            
            # DJ Analysis
            if config.include_analysis:
                # BPM
                if 'bpm' in track:
                    track_elem.set('AverageBpm', f"{track['bpm']:.2f}")
                
                # Key
                if 'key' in track:
                    key_mapping = self._get_rekordbox_key_mapping()
                    rb_key = key_mapping.get(track['key'], '1d')
                    track_elem.set('Tonality', rb_key)
                
                # Energy (als Comment)
                if 'energy_score' in track:
                    track_elem.set('Comments', f"Energy: {track['energy_score']:.1f}")
            
            # Cue Points
            if config.include_cue_points and 'cue_points' in track:
                for j, cue in enumerate(track['cue_points']):
                    cue_elem = ET.SubElement(track_elem, 'POSITION_MARK')
                    cue_elem.set('Name', cue.get('name', f'Cue {j+1}'))
                    cue_elem.set('Type', '0')  # Cue
                    cue_elem.set('Start', str(cue.get('position', 0)))
                    cue_elem.set('Num', str(j))
        
        # Playlists
        playlists = ET.SubElement(root, 'PLAYLISTS')
        
        # Main Playlist
        playlist_node = ET.SubElement(playlists, 'NODE')
        playlist_node.set('Type', '1')  # Playlist
        playlist_node.set('Name', playlist_data.get('name', 'Generated Playlist'))
        playlist_node.set('Entries', str(len(playlist_data.get('playlist', []))))
        
        # Playlist Tracks
        for i, track in enumerate(playlist_data.get('playlist', [])):
            track_ref = ET.SubElement(playlist_node, 'TRACK')
            track_ref.set('Key', str(i + 1))
        
        # Write XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_path, encoding=config.encoding, xml_declaration=True)
        
        return {
            'tracks_exported': len(playlist_data.get('playlist', [])),
            'format_version': '1.0.0',
            'includes_analysis': config.include_analysis
        }
    
    def _export_serato(self, playlist_data: Dict[str, Any], 
                      output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert für Serato Crate Format"""
        # Serato verwendet ein proprietäres Binärformat
        # Hier implementieren wir eine vereinfachte Version
        
        crate_data = {
            'version': '1.0',
            'name': playlist_data.get('name', 'Generated Playlist'),
            'tracks': []
        }
        
        for track in playlist_data.get('playlist', []):
            track_entry = {
                'file_path': track.get('file_path', ''),
                'title': track.get('title', 'Unknown'),
                'artist': track.get('artist', 'Unknown'),
                'album': track.get('album', ''),
                'genre': track.get('genre', ''),
                'bpm': track.get('bpm', 0),
                'key': track.get('key', ''),
                'duration': track.get('duration', 0)
            }
            
            if config.include_analysis:
                track_entry.update({
                    'energy_score': track.get('energy_score', 5.0),
                    'mood': track.get('mood', {}),
                    'spectral_features': track.get('spectral_features', {})
                })
            
            crate_data['tracks'].append(track_entry)
        
        # Speichere als JSON (vereinfacht)
        with open(output_path, 'w', encoding=config.encoding) as f:
            json.dump(crate_data, f, indent=2)
        
        return {
            'tracks_exported': len(crate_data['tracks']),
            'format': 'serato_simplified'
        }
    
    def _export_traktor(self, playlist_data: Dict[str, Any], 
                       output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert für Traktor NML Format"""
        root = ET.Element('NML')
        root.set('VERSION', '19')
        
        # Head
        head = ET.SubElement(root, 'HEAD')
        head.set('COMPANY', 'Native Instruments')
        head.set('PROGRAM', 'Traktor')
        
        # Collection
        collection = ET.SubElement(root, 'COLLECTION')
        collection.set('ENTRIES', str(len(playlist_data.get('playlist', []))))
        
        # Tracks
        for track in playlist_data.get('playlist', [])):
            entry = ET.SubElement(collection, 'ENTRY')
            
            # Basic Info
            entry.set('TITLE', track.get('title', 'Unknown'))
            entry.set('ARTIST', track.get('artist', 'Unknown'))
            entry.set('ALBUM', track.get('album', ''))
            entry.set('GENRE', track.get('genre', ''))
            
            # File Location
            location = ET.SubElement(entry, 'LOCATION')
            file_path = track.get('file_path', '')
            if config.relative_paths:
                file_path = str(Path(file_path).name)
            location.set('DIR', str(Path(file_path).parent))
            location.set('FILE', str(Path(file_path).name))
            location.set('VOLUME', '')
            location.set('VOLUMEID', '')
            
            # Audio Info
            info = ET.SubElement(entry, 'INFO')
            info.set('BITRATE', str(track.get('bitrate', 320)))
            info.set('GENRE', track.get('genre', ''))
            info.set('PLAYTIME', str(int(track.get('duration', 0))))
            info.set('SAMPLERATE', str(track.get('sample_rate', 44100)))
            
            # Analysis
            if config.include_analysis:
                # BPM
                if 'bpm' in track:
                    tempo = ET.SubElement(entry, 'TEMPO')
                    tempo.set('BPM', f"{track['bpm']:.2f}")
                    tempo.set('BPM_QUALITY', '100')
                
                # Key
                if 'key' in track:
                    musical_key = ET.SubElement(entry, 'MUSICAL_KEY')
                    key_mapping = self._get_traktor_key_mapping()
                    traktor_key = key_mapping.get(track['key'], '1d')
                    musical_key.set('VALUE', traktor_key)
        
        # Playlists
        playlists = ET.SubElement(root, 'PLAYLISTS')
        playlist_node = ET.SubElement(playlists, 'NODE')
        playlist_node.set('TYPE', 'PLAYLIST')
        playlist_node.set('NAME', playlist_data.get('name', 'Generated Playlist'))
        
        # Playlist Entries
        for i, track in enumerate(playlist_data.get('playlist', [])):
            playlist_entry = ET.SubElement(playlist_node, 'PLAYLIST')
            playlist_entry.set('ENTRIES', '1')
            
            entry_ref = ET.SubElement(playlist_entry, 'ENTRY')
            entry_ref.set('TITLE', track.get('title', 'Unknown'))
            entry_ref.set('ARTIST', track.get('artist', 'Unknown'))
        
        # Write XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_path, encoding=config.encoding, xml_declaration=True)
        
        return {
            'tracks_exported': len(playlist_data.get('playlist', [])),
            'format_version': '19'
        }
    
    def _export_virtual_dj(self, playlist_data: Dict[str, Any], 
                          output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert für Virtual DJ Format"""
        vdj_data = []
        
        for track in playlist_data.get('playlist', []):
            file_path = track.get('file_path', '')
            if config.relative_paths:
                file_path = str(Path(file_path).name)
            
            # Virtual DJ verwendet ein einfaches Format
            track_line = file_path
            
            # Füge Metadaten als Kommentar hinzu
            if config.include_metadata:
                metadata = []
                if 'bpm' in track:
                    metadata.append(f"BPM:{track['bpm']:.1f}")
                if 'key' in track:
                    metadata.append(f"Key:{track['key']}")
                if 'energy_score' in track:
                    metadata.append(f"Energy:{track['energy_score']:.1f}")
                
                if metadata:
                    track_line += f" # {', '.join(metadata)}"
            
            vdj_data.append(track_line)
        
        # Schreibe Playlist
        with open(output_path, 'w', encoding=config.encoding) as f:
            f.write('\n'.join(vdj_data))
        
        return {
            'tracks_exported': len(vdj_data),
            'format': 'virtual_dj'
        }
    
    def _export_djay_pro(self, playlist_data: Dict[str, Any], 
                        output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert für djay Pro Format"""
        # djay Pro verwendet JSON-ähnliches Format
        djay_data = {
            'playlist': {
                'name': playlist_data.get('name', 'Generated Playlist'),
                'created': datetime.now().isoformat(),
                'tracks': []
            }
        }
        
        for track in playlist_data.get('playlist', []):
            track_entry = {
                'file_path': track.get('file_path', ''),
                'metadata': {
                    'title': track.get('title', 'Unknown'),
                    'artist': track.get('artist', 'Unknown'),
                    'album': track.get('album', ''),
                    'genre': track.get('genre', ''),
                    'duration': track.get('duration', 0)
                }
            }
            
            if config.include_analysis:
                track_entry['analysis'] = {
                    'bpm': track.get('bpm', 0),
                    'key': track.get('key', ''),
                    'energy_score': track.get('energy_score', 5.0)
                }
            
            djay_data['playlist']['tracks'].append(track_entry)
        
        # Speichere als JSON
        with open(output_path, 'w', encoding=config.encoding) as f:
            json.dump(djay_data, f, indent=2)
        
        return {
            'tracks_exported': len(djay_data['playlist']['tracks']),
            'format': 'djay_pro'
        }
    
    def _export_m3u8(self, playlist_data: Dict[str, Any], 
                    output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert als Extended M3U8 Playlist"""
        m3u_lines = ['#EXTM3U']
        
        for track in playlist_data.get('playlist', []):
            # Extended Info
            duration = int(track.get('duration', 0))
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            
            extinf_line = f"#EXTINF:{duration},{artist} - {title}"
            
            # Zusätzliche Metadaten
            if config.include_metadata:
                metadata = []
                if 'bpm' in track:
                    metadata.append(f"BPM={track['bpm']:.1f}")
                if 'key' in track:
                    metadata.append(f"KEY={track['key']}")
                if 'energy_score' in track:
                    metadata.append(f"ENERGY={track['energy_score']:.1f}")
                
                if metadata:
                    extinf_line += f" ({', '.join(metadata)})"
            
            m3u_lines.append(extinf_line)
            
            # File Path
            file_path = track.get('file_path', '')
            if config.relative_paths:
                file_path = str(Path(file_path).name)
            m3u_lines.append(file_path)
        
        # Schreibe M3U8
        with open(output_path, 'w', encoding=config.encoding) as f:
            f.write('\n'.join(m3u_lines))
        
        return {
            'tracks_exported': len(playlist_data.get('playlist', [])),
            'format': 'm3u8_extended'
        }
    
    def _export_json(self, playlist_data: Dict[str, Any], 
                    output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert als vollständiges JSON mit allen Metadaten"""
        export_data = {
            'playlist_info': {
                'name': playlist_data.get('name', 'Generated Playlist'),
                'created': datetime.now().isoformat(),
                'generator': 'Audio Analysis Tool',
                'version': '1.0',
                'total_tracks': len(playlist_data.get('playlist', [])),
                'total_duration': sum(t.get('duration', 0) for t in playlist_data.get('playlist', []))
            },
            'tracks': []
        }
        
        # Energie-Kurve hinzufügen
        if config.include_energy_curve and 'energy_curve' in playlist_data:
            export_data['energy_curve'] = [
                {
                    'position': point.position,
                    'energy': point.energy,
                    'weight': point.weight,
                    'tolerance': point.tolerance
                }
                for point in playlist_data['energy_curve']
            ]
        
        # Qualitäts-Metriken
        if 'quality_metrics' in playlist_data:
            export_data['quality_metrics'] = playlist_data['quality_metrics']
        
        # Tracks
        for i, track in enumerate(playlist_data.get('playlist', [])):
            track_data = {
                'position': i + 1,
                'file_path': track.get('file_path', ''),
                'metadata': {
                    'title': track.get('title', 'Unknown'),
                    'artist': track.get('artist', 'Unknown'),
                    'album': track.get('album', ''),
                    'genre': track.get('genre', ''),
                    'year': track.get('year', 0),
                    'duration': track.get('duration', 0),
                    'file_size': track.get('file_size', 0),
                    'bitrate': track.get('bitrate', 0),
                    'sample_rate': track.get('sample_rate', 0)
                }
            }
            
            if config.include_analysis:
                track_data['analysis'] = {
                    'bpm': track.get('bpm', 0),
                    'key': track.get('key', ''),
                    'energy_score': track.get('energy_score', 5.0),
                    'mood': track.get('mood', {}),
                    'spectral_features': track.get('spectral_features', {}),
                    'harmonic_features': track.get('harmonic_features', {})
                }
            
            if config.include_cue_points and 'cue_points' in track:
                track_data['cue_points'] = track['cue_points']
            
            export_data['tracks'].append(track_data)
        
        # Kompression
        if config.compression:
            # Komprimiere und speichere als ZIP
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(export_data, temp_file, indent=2)
                temp_path = temp_file.name
            
            with zipfile.ZipFile(output_path + '.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_path, Path(output_path).name)
            
            Path(temp_path).unlink()
            output_path += '.zip'
        else:
            # Normale JSON-Datei
            with open(output_path, 'w', encoding=config.encoding) as f:
                json.dump(export_data, f, indent=2)
        
        return {
            'tracks_exported': len(export_data['tracks']),
            'includes_energy_curve': config.include_energy_curve,
            'includes_analysis': config.include_analysis,
            'compressed': config.compression,
            'file_size': Path(output_path).stat().st_size if Path(output_path).exists() else 0
        }
    
    def _export_csv(self, playlist_data: Dict[str, Any], 
                   output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert als CSV-Datei"""
        fieldnames = [
            'position', 'file_path', 'title', 'artist', 'album', 'genre', 
            'duration', 'bpm', 'key', 'energy_score'
        ]
        
        if config.include_analysis:
            fieldnames.extend([
                'mood_euphoric', 'mood_dark', 'mood_driving', 'mood_experimental',
                'spectral_centroid', 'spectral_rolloff', 'spectral_bandwidth'
            ])
        
        with open(output_path, 'w', newline='', encoding=config.encoding) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, track in enumerate(playlist_data.get('playlist', [])):
                row = {
                    'position': i + 1,
                    'file_path': track.get('file_path', ''),
                    'title': track.get('title', 'Unknown'),
                    'artist': track.get('artist', 'Unknown'),
                    'album': track.get('album', ''),
                    'genre': track.get('genre', ''),
                    'duration': track.get('duration', 0),
                    'bpm': track.get('bpm', 0),
                    'key': track.get('key', ''),
                    'energy_score': track.get('energy_score', 5.0)
                }
                
                if config.include_analysis:
                    mood = track.get('mood', {})
                    spectral = track.get('spectral_features', {})
                    
                    row.update({
                        'mood_euphoric': mood.get('euphoric', 0),
                        'mood_dark': mood.get('dark', 0),
                        'mood_driving': mood.get('driving', 0),
                        'mood_experimental': mood.get('experimental', 0),
                        'spectral_centroid': spectral.get('centroid', 0),
                        'spectral_rolloff': spectral.get('rolloff', 0),
                        'spectral_bandwidth': spectral.get('bandwidth', 0)
                    })
                
                writer.writerow(row)
        
        return {
            'tracks_exported': len(playlist_data.get('playlist', [])),
            'format': 'csv',
            'columns': len(fieldnames)
        }
    
    def _export_xml(self, playlist_data: Dict[str, Any], 
                   output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert als generisches XML"""
        root = ET.Element('playlist')
        root.set('name', playlist_data.get('name', 'Generated Playlist'))
        root.set('created', datetime.now().isoformat())
        root.set('generator', 'Audio Analysis Tool')
        
        # Tracks
        tracks_elem = ET.SubElement(root, 'tracks')
        tracks_elem.set('count', str(len(playlist_data.get('playlist', []))))
        
        for i, track in enumerate(playlist_data.get('playlist', [])):
            track_elem = ET.SubElement(tracks_elem, 'track')
            track_elem.set('position', str(i + 1))
            
            # Basic Metadata
            for field in ['title', 'artist', 'album', 'genre']:
                if field in track:
                    elem = ET.SubElement(track_elem, field)
                    elem.text = str(track[field])
            
            # File Info
            file_elem = ET.SubElement(track_elem, 'file')
            file_elem.set('path', track.get('file_path', ''))
            file_elem.set('duration', str(track.get('duration', 0)))
            file_elem.set('size', str(track.get('file_size', 0)))
            
            # Analysis
            if config.include_analysis:
                analysis_elem = ET.SubElement(track_elem, 'analysis')
                
                if 'bpm' in track:
                    bpm_elem = ET.SubElement(analysis_elem, 'bpm')
                    bpm_elem.text = str(track['bpm'])
                
                if 'key' in track:
                    key_elem = ET.SubElement(analysis_elem, 'key')
                    key_elem.text = track['key']
                
                if 'energy_score' in track:
                    energy_elem = ET.SubElement(analysis_elem, 'energy')
                    energy_elem.text = str(track['energy_score'])
                
                # Mood
                if 'mood' in track:
                    mood_elem = ET.SubElement(analysis_elem, 'mood')
                    for mood_type, value in track['mood'].items():
                        mood_type_elem = ET.SubElement(mood_elem, mood_type)
                        mood_type_elem.text = str(value)
        
        # Energy Curve
        if config.include_energy_curve and 'energy_curve' in playlist_data:
            curve_elem = ET.SubElement(root, 'energy_curve')
            for point in playlist_data['energy_curve']:
                point_elem = ET.SubElement(curve_elem, 'point')
                point_elem.set('position', str(point.position))
                point_elem.set('energy', str(point.energy))
                point_elem.set('weight', str(point.weight))
                point_elem.set('tolerance', str(point.tolerance))
        
        # Write XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_path, encoding=config.encoding, xml_declaration=True)
        
        return {
            'tracks_exported': len(playlist_data.get('playlist', [])),
            'includes_energy_curve': config.include_energy_curve
        }
    
    def _export_cue_sheet(self, playlist_data: Dict[str, Any], 
                         output_path: str, config: ExportConfig) -> Dict[str, Any]:
        """Exportiert als CUE Sheet für CD-Brennen"""
        cue_lines = []
        
        # Header
        cue_lines.append(f'TITLE "{playlist_data.get("name", "Generated Playlist")}"')
        cue_lines.append('FILE "playlist.mp3" MP3')
        
        current_time = 0
        
        for i, track in enumerate(playlist_data.get('playlist', [])):
            track_num = i + 1
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            duration = track.get('duration', 180)  # Default 3 minutes
            
            # Track Info
            cue_lines.append(f'  TRACK {track_num:02d} AUDIO')
            cue_lines.append(f'    TITLE "{title}"')
            cue_lines.append(f'    PERFORMER "{artist}"')
            
            # Index (Start Time)
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            frames = int((current_time % 1) * 75)  # 75 frames per second
            cue_lines.append(f'    INDEX 01 {minutes:02d}:{seconds:02d}:{frames:02d}')
            
            current_time += duration
        
        # Write CUE
        with open(output_path, 'w', encoding=config.encoding) as f:
            f.write('\n'.join(cue_lines))
        
        return {
            'tracks_exported': len(playlist_data.get('playlist', [])),
            'total_duration': current_time,
            'format': 'cue_sheet'
        }
    
    def _get_rekordbox_key_mapping(self) -> Dict[str, str]:
        """Mapping für Rekordbox Key-Notation"""
        return {
            'C major': '8B', 'A minor': '8A',
            'G major': '9B', 'E minor': '9A',
            'D major': '10B', 'B minor': '10A',
            'A major': '11B', 'F# minor': '11A',
            'E major': '12B', 'C# minor': '12A',
            'B major': '1B', 'G# minor': '1A',
            'F# major': '2B', 'D# minor': '2A',
            'C# major': '3B', 'A# minor': '3A',
            'F major': '7B', 'D minor': '7A',
            'Bb major': '6B', 'G minor': '6A',
            'Eb major': '5B', 'C minor': '5A',
            'Ab major': '4B', 'F minor': '4A'
        }
    
    def _get_traktor_key_mapping(self) -> Dict[str, str]:
        """Mapping für Traktor Key-Notation"""
        return {
            'C major': '1d', 'A minor': '1m',
            'G major': '2d', 'E minor': '2m',
            'D major': '3d', 'B minor': '3m',
            'A major': '4d', 'F# minor': '4m',
            'E major': '5d', 'C# minor': '5m',
            'B major': '6d', 'G# minor': '6m',
            'F# major': '7d', 'D# minor': '7m',
            'C# major': '8d', 'A# minor': '8m',
            'F major': '9d', 'D minor': '9m',
            'Bb major': '10d', 'G minor': '10m',
            'Eb major': '11d', 'C minor': '11m',
            'Ab major': '12d', 'F minor': '12m'
        }
    
    def _create_backup(self, file_path: str):
        """Erstellt Backup einer existierenden Datei"""
        original_path = Path(file_path)
        if original_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = original_path.with_suffix(f'.backup_{timestamp}{original_path.suffix}')
            original_path.rename(backup_path)
            logger.info(f"Backup erstellt: {backup_path}")
    
    def _update_export_stats(self, format_name: str, export_time: float, success: bool):
        """Aktualisiert Export-Statistiken"""
        self.export_stats['total_exports'] += 1
        
        if success:
            self.export_stats['successful_exports'] += 1
        else:
            self.export_stats['failed_exports'] += 1
        
        # Format-Statistiken
        if format_name not in self.export_stats['formats_used']:
            self.export_stats['formats_used'][format_name] = 0
        self.export_stats['formats_used'][format_name] += 1
        
        # Durchschnittliche Export-Zeit
        total = self.export_stats['total_exports']
        current_avg = self.export_stats['avg_export_time']
        self.export_stats['avg_export_time'] = (
            (current_avg * (total - 1) + export_time) / total
        )
    
    def get_supported_formats(self) -> Dict[str, Dict[str, Any]]:
        """Gibt unterstützte Formate zurück"""
        return self.format_metadata.copy()
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Gibt Export-Statistiken zurück"""
        stats = self.export_stats.copy()
        
        # Erfolgsrate
        if stats['total_exports'] > 0:
            stats['success_rate'] = stats['successful_exports'] / stats['total_exports']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def validate_playlist_data(self, playlist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validiert Playlist-Daten vor Export"""
        issues = []
        warnings = []
        
        # Grundlegende Struktur
        if 'playlist' not in playlist_data:
            issues.append("Missing 'playlist' key in data")
        elif not isinstance(playlist_data['playlist'], list):
            issues.append("'playlist' must be a list")
        elif len(playlist_data['playlist']) == 0:
            warnings.append("Playlist is empty")
        
        # Track-Validierung
        if 'playlist' in playlist_data:
            for i, track in enumerate(playlist_data['playlist']):
                if not isinstance(track, dict):
                    issues.append(f"Track {i+1} is not a dictionary")
                    continue
                
                # Erforderliche Felder
                required_fields = ['file_path']
                for field in required_fields:
                    if field not in track:
                        issues.append(f"Track {i+1} missing required field: {field}")
                
                # File-Existenz (optional)
                file_path = track.get('file_path', '')
                if file_path and not Path(file_path).exists():
                    warnings.append(f"Track {i+1} file not found: {file_path}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'track_count': len(playlist_data.get('playlist', [])),
            'has_metadata': any('title' in track for track in playlist_data.get('playlist', [])),
            'has_analysis': any('bpm' in track for track in playlist_data.get('playlist', []))
        }
    
    def batch_export(self, playlist_data: Dict[str, Any], 
                    output_dir: str, formats: List[str],
                    base_filename: str = 'playlist') -> Dict[str, Any]:
        """Exportiert Playlist in mehrere Formate gleichzeitig"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for format_name in formats:
            if format_name not in self.supported_formats:
                results[format_name] = {
                    'success': False,
                    'error': f'Unsupported format: {format_name}'
                }
                continue
            
            # Bestimme Dateiendung
            extension = self.format_metadata.get(format_name, {}).get('extension', '.txt')
            output_path = output_dir / f"{base_filename}_{format_name}{extension}"
            
            # Export
            config = ExportConfig(format=format_name)
            result = self.export_playlist(playlist_data, str(output_path), config)
            results[format_name] = result
        
        return {
            'total_formats': len(formats),
            'successful_exports': sum(1 for r in results.values() if r.get('success', False)),
            'failed_exports': sum(1 for r in results.values() if not r.get('success', False)),
            'results': results,
            'output_directory': str(output_dir)
        }