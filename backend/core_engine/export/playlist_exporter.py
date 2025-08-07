"""Playlist Exporter - Export von Playlists in verschiedene Formate für Backend"""

import logging
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class PlaylistExporter:
    """Exportiert Playlists in verschiedene Formate für headless Backend"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.supported_formats = ['m3u', 'json', 'csv', 'rekordbox']
        
    def export_playlist(self, tracks: List[Dict[str, Any]], 
                       format_type: str, 
                       output_filename: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Exportiert Playlist in gewünschtes Format"""
        
        if format_type not in self.supported_formats:
            return {
                'success': False,
                'error': f'Format {format_type} nicht unterstützt',
                'supported_formats': self.supported_formats
            }
        
        if not tracks:
            return {
                'success': False,
                'error': 'Keine Tracks zum Exportieren'
            }
        
        # Generate filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            preset_name = metadata.get('preset_name', 'playlist') if metadata else 'playlist'
            output_filename = f"{preset_name}_{timestamp}.{format_type}"
        
        output_path = self.output_dir / output_filename
        
        try:
            if format_type == 'm3u':
                success = self._export_m3u(tracks, output_path, metadata)
            elif format_type == 'json':
                success = self._export_json(tracks, output_path, metadata)
            elif format_type == 'csv':
                success = self._export_csv(tracks, output_path, metadata)
            elif format_type == 'rekordbox':
                success = self._export_rekordbox(tracks, output_path, metadata)
            else:
                success = False
            
            if success:
                return {
                    'success': True,
                    'output_path': str(output_path),
                    'filename': output_filename,
                    'format': format_type,
                    'track_count': len(tracks),
                    'file_size_bytes': output_path.stat().st_size if output_path.exists() else 0
                }
            else:
                return {
                    'success': False,
                    'error': f'Export nach {format_type} fehlgeschlagen'
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Export: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _export_m3u(self, tracks: List[Dict[str, Any]], output_path: Path, 
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Exportiert Playlist als M3U-Datei"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                
                # Füge Playlist-Metadaten als Kommentar hinzu
                if metadata:
                    f.write(f'# Playlist: {metadata.get("preset_name", "Unknown")}\n')
                    f.write(f'# Created: {datetime.now().isoformat()}\n')
                    f.write(f'# Total Duration: {metadata.get("total_duration_minutes", 0):.1f} minutes\n')
                    f.write(f'# Track Count: {metadata.get("total_tracks", len(tracks))}\n')
                    f.write('#\n')
                
                for track in tracks:
                    # Extrahiere Metadaten
                    metadata_info = track.get('metadata', {})
                    file_path = track.get('file_path', metadata_info.get('file_path', ''))
                    
                    title = metadata_info.get('title', track.get('filename', 'Unknown'))
                    artist = metadata_info.get('artist', 'Unknown')
                    duration = int(metadata_info.get('duration', 0))
                    
                    # Schreibe EXTINF-Zeile
                    f.write(f'#EXTINF:{duration},{artist} - {title}\n')
                    f.write(f'{file_path}\n')
            
            logger.info(f"M3U-Playlist exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim M3U-Export: {e}")
            return False
    
    def _export_json(self, tracks: List[Dict[str, Any]], output_path: Path, 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Exportiert Playlist als JSON-Datei"""
        try:
            playlist_data = {
                'version': '2.0',
                'format': 'DJ Audio Analysis Tool Playlist',
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {},
                'track_count': len(tracks),
                'tracks': []
            }
            
            # Bereite Tracks für Export vor
            for i, track in enumerate(tracks):
                track_data = {
                    'index': i + 1,
                    'file_path': track.get('file_path', ''),
                    'filename': track.get('filename', ''),
                    'metadata': track.get('metadata', {}),
                    'features': track.get('features', {}),
                    'camelot': track.get('camelot', {}),
                    'mood': track.get('mood', {}),
                    'derived_metrics': track.get('derived_metrics', {})
                }
                playlist_data['tracks'].append(track_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON-Playlist exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim JSON-Export: {e}")
            return False
    
    def _export_csv(self, tracks: List[Dict[str, Any]], output_path: Path, 
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Exportiert Playlist als CSV-Datei"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                # Definiere CSV-Spalten
                fieldnames = [
                    'index', 'filename', 'file_path', 'title', 'artist', 'album',
                    'duration_seconds', 'bpm', 'key', 'camelot', 'energy', 
                    'valence', 'danceability', 'mood', 'energy_level'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for i, track in enumerate(tracks):
                    metadata_info = track.get('metadata', {})
                    features = track.get('features', {})
                    camelot_info = track.get('camelot', {})
                    derived_metrics = track.get('derived_metrics', {})
                    
                    row_data = {
                        'index': i + 1,
                        'filename': track.get('filename', ''),
                        'file_path': track.get('file_path', ''),
                        'title': metadata_info.get('title', ''),
                        'artist': metadata_info.get('artist', ''),
                        'album': metadata_info.get('album', ''),
                        'duration_seconds': metadata_info.get('duration', 0),
                        'bpm': features.get('bpm', 0),
                        'key': camelot_info.get('key', ''),
                        'camelot': camelot_info.get('camelot', ''),
                        'energy': round(features.get('energy', 0), 3),
                        'valence': round(features.get('valence', 0), 3),
                        'danceability': round(features.get('danceability', 0), 3),
                        'mood': derived_metrics.get('estimated_mood', ''),
                        'energy_level': derived_metrics.get('energy_level', '')
                    }
                    
                    writer.writerow(row_data)
            
            logger.info(f"CSV-Playlist exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim CSV-Export: {e}")
            return False
    
    def _export_rekordbox(self, tracks: List[Dict[str, Any]], output_path: Path, 
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Exportiert Playlist als Rekordbox XML"""
        try:
            # Erstelle XML-Struktur für Rekordbox
            root = ET.Element("DJ_PLAYLISTS", Version="1.0.0")
            
            # Product Info
            product = ET.SubElement(root, "PRODUCT", Name="DJ Audio Analysis Tool", Version="2.0")
            
            # Collection (required for Rekordbox)
            collection = ET.SubElement(root, "COLLECTION", Entries=str(len(tracks)))
            
            # Tracks in Collection
            for i, track in enumerate(tracks):
                metadata_info = track.get('metadata', {})
                features = track.get('features', {})
                camelot_info = track.get('camelot', {})
                
                track_elem = ET.SubElement(collection, "TRACK",
                    TrackID=str(i + 1),
                    Name=metadata_info.get('title', track.get('filename', '')),
                    Artist=metadata_info.get('artist', ''),
                    Album=metadata_info.get('album', ''),
                    Kind="MP3 File",  # Default
                    Size=str(metadata_info.get('file_size', 0)),
                    TotalTime=str(int(metadata_info.get('duration', 0))),
                    DiscNumber="1",
                    TrackNumber="1",
                    Year="",
                    AverageBpm=f"{features.get('bpm', 120):.2f}",
                    DateCreated=datetime.now().strftime("%Y-%m-%d"),
                    BitRate="320",  # Default
                    SampleRate="44100",  # Default
                    Comments=f"Energy: {features.get('energy', 0):.2f}, Valence: {features.get('valence', 0):.2f}",
                    PlayCount="0",
                    Rating="0",
                    Location=f"file://localhost/{track.get('file_path', '').replace(chr(92), '/')}"
                )
                
                # Tonart-Information falls verfügbar
                if camelot_info.get('key'):
                    track_elem.set("Tonality", camelot_info['key'])
            
            # Playlists
            playlists = ET.SubElement(root, "PLAYLISTS")
            root_node = ET.SubElement(playlists, "NODE", Type="0", Name="ROOT", Count="1")
            
            # Hauptplaylist
            playlist_name = metadata.get('preset_name', 'Generated Playlist') if metadata else 'Generated Playlist'
            playlist_node = ET.SubElement(root_node, "NODE", 
                Type="1", 
                Name=playlist_name,
                Entries=str(len(tracks)),
                KeyType="0",
                Keys=""
            )
            
            # Tracks in Playlist
            for i, track in enumerate(tracks):
                ET.SubElement(playlist_node, "TRACK", Key=str(i + 1))
            
            # Schreibe XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            logger.info(f"Rekordbox XML exportiert: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Rekordbox-Export: {e}")
            return False
    
    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Export-Formate zurück"""
        return self.supported_formats.copy()
    
    def validate_tracks(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validiert Track-Daten für Export"""
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'track_count': len(tracks),
            'missing_metadata_count': 0,
            'missing_features_count': 0
        }
        
        if not tracks:
            validation_result['valid'] = False
            validation_result['errors'].append('Keine Tracks vorhanden')
            return validation_result
        
        for i, track in enumerate(tracks):
            track_id = f"Track {i + 1}"
            
            # Prüfe file_path
            if not track.get('file_path'):
                validation_result['errors'].append(f"{track_id}: Kein file_path")
            
            # Prüfe Metadaten
            metadata = track.get('metadata', {})
            if not metadata:
                validation_result['missing_metadata_count'] += 1
                validation_result['warnings'].append(f"{track_id}: Keine Metadaten")
            
            # Prüfe Features
            features = track.get('features', {})
            if not features:
                validation_result['missing_features_count'] += 1
                validation_result['warnings'].append(f"{track_id}: Keine Features")
        
        # Gesamtbewertung
        if validation_result['errors']:
            validation_result['valid'] = False
        
        return validation_result
    
    def get_export_info(self, format_type: str) -> Dict[str, Any]:
        """Gibt Informationen über ein Export-Format zurück"""
        format_info = {
            'm3u': {
                'name': 'M3U Playlist',
                'description': 'Standard Multimedia Playlist Format',
                'extension': '.m3u',
                'supports_metadata': False,
                'supports_features': False,
                'compatible_with': ['VLC', 'Winamp', 'iTunes', 'Most Media Players']
            },
            'json': {
                'name': 'JSON Export',
                'description': 'Complete track data in JSON format',
                'extension': '.json',
                'supports_metadata': True,
                'supports_features': True,
                'compatible_with': ['DJ Audio Analysis Tool', 'Custom Applications']
            },
            'csv': {
                'name': 'CSV Export',
                'description': 'Comma-separated values for data analysis',
                'extension': '.csv',
                'supports_metadata': True,
                'supports_features': True,
                'compatible_with': ['Excel', 'LibreOffice', 'Data Analysis Tools']
            },
            'rekordbox': {
                'name': 'Rekordbox XML',
                'description': 'Pioneer Rekordbox compatible XML format',
                'extension': '.xml',
                'supports_metadata': True,
                'supports_features': False,
                'compatible_with': ['Rekordbox', 'Pioneer CDJs', 'Pioneer Mixers']
            }
        }
        
        return format_info.get(format_type, {
            'name': 'Unknown Format',
            'description': 'Format not supported',
            'extension': '',
            'supports_metadata': False,
            'supports_features': False,
            'compatible_with': []
        })
    
    def list_exports(self) -> List[Dict[str, Any]]:
        """Listet alle exportierten Playlists auf"""
        exports = []
        
        try:
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file() and file_path.suffix[1:] in self.supported_formats:
                    stat = file_path.stat()
                    exports.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'format': file_path.suffix[1:],
                        'size_bytes': stat.st_size,
                        'created_at': stat.st_mtime,
                        'modified_at': stat.st_mtime
                    })
            
            # Sortiere nach Erstellungsdatum (neueste zuerst)
            exports.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Exports: {e}")
        
        return exports
    
    def delete_export(self, filename: str) -> bool:
        """Löscht eine exportierte Playlist"""
        try:
            file_path = self.output_dir / filename
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"Export gelöscht: {filename}")
                return True
            else:
                logger.warning(f"Export nicht gefunden: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Exports {filename}: {e}")
            return False