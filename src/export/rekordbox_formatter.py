"""Rekordbox Formatter - Formatierung und Konvertierung für Rekordbox-kompatible Daten"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from urllib.parse import quote, unquote


class RekordboxFormatter:
    """Formatiert Track-Daten für Rekordbox-Kompatibilität"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.wav', '.aiff', '.flac', '.m4a']
        self.key_mapping = self._init_key_mapping()
        self.genre_mapping = self._init_genre_mapping()
    
    def format_track_for_rekordbox(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Formatiert einen Track für Rekordbox-Export"""
        
        formatted_track = {
            'TrackID': track.get('id', 0),
            'Name': self._clean_string(track.get('title', 'Unknown Title')),
            'Artist': self._clean_string(track.get('artist', 'Unknown Artist')),
            'Album': self._clean_string(track.get('album', '')),
            'Genre': self._format_genre(track.get('genre', '')),
            'Kind': self._get_file_kind(track.get('file_path', '')),
            'Size': track.get('file_size', 0),
            'TotalTime': self._format_duration(track.get('duration', 0)),
            'Year': self._format_year(track.get('year')),
            'AverageBpm': self._format_bpm(track.get('bpm')),
            'DateAdded': self._format_date_added(track.get('date_added')),
            'BitRate': track.get('bitrate', 0),
            'SampleRate': track.get('sample_rate', 44100),
            'Comments': self._format_comments(track),
            'PlayCount': track.get('play_count', 0),
            'Rating': self._format_rating(track.get('rating')),
            'Location': self._format_file_location(track.get('file_path', '')),
            'Remixer': self._clean_string(track.get('remixer', '')),
            'Tonality': self._format_key(track.get('key')),
            'Label': self._clean_string(track.get('label', '')),
            'Mix': self._clean_string(track.get('mix', ''))
        }
        
        # Füge Rekordbox-spezifische Analyse-Daten hinzu
        if track.get('energy'):
            formatted_track['Energy'] = self._format_energy(track['energy'])
        
        if track.get('danceability'):
            formatted_track['Danceability'] = self._format_energy(track['danceability'])
        
        # Entferne leere Werte
        return {k: v for k, v in formatted_track.items() if v not in [None, '', 0]}
    
    def format_playlist_for_rekordbox(self, playlist_name: str, 
                                     tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Formatiert eine Playlist für Rekordbox-Export"""
        
        return {
            'Name': self._clean_string(playlist_name),
            'Type': '1',  # Playlist Type
            'KeyType': '0',
            'Entries': str(len(tracks)),
            'Tracks': [self.format_track_for_rekordbox(track) for track in tracks]
        }
    
    def convert_camelot_to_rekordbox_key(self, camelot_key: str) -> int:
        """Konvertiert Camelot-Notation zu Rekordbox-Schlüssel"""
        
        # Camelot zu Rekordbox Mapping
        camelot_to_rb = {
            '1A': 21, '1B': 16, '2A': 22, '2B': 17, '3A': 23, '3B': 18,
            '4A': 24, '4B': 19, '5A': 13, '5B': 20, '6A': 14, '6B': 15,
            '7A': 15, '7B': 22, '8A': 16, '8B': 23, '9A': 17, '9B': 24,
            '10A': 18, '10B': 13, '11A': 19, '11B': 14, '12A': 20, '12B': 21
        }
        
        return camelot_to_rb.get(camelot_key.upper(), 0)
    
    def convert_standard_key_to_rekordbox(self, key: str) -> int:
        """Konvertiert Standard-Tonart zu Rekordbox-Schlüssel"""
        
        if not key:
            return 0
        
        # Normalisiere Eingabe
        key = key.strip().replace('♭', 'b').replace('♯', '#')
        
        return self.key_mapping.get(key, 0)
    
    def format_file_path_for_rekordbox(self, file_path: str) -> str:
        """Formatiert Dateipfad für Rekordbox"""
        
        if not file_path or not os.path.exists(file_path):
            return ''
        
        # Konvertiere zu absoluten Pfad
        abs_path = os.path.abspath(file_path)
        
        # Konvertiere Backslashes zu Forward Slashes
        unix_path = abs_path.replace('\\', '/')
        
        # URL-Encode spezielle Zeichen
        encoded_path = quote(unix_path, safe='/:@')
        
        # Füge file:// Protokoll hinzu
        return f'file://localhost/{encoded_path}'
    
    def validate_rekordbox_compatibility(self, track: Dict[str, Any]) -> Dict[str, Any]:
        """Validiert Track auf Rekordbox-Kompatibilität"""
        
        validation_result = {
            'is_compatible': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Prüfe Dateiformat
        file_path = track.get('file_path', '')
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_formats:
                validation_result['warnings'].append(
                    f'Dateiformat {file_ext} wird möglicherweise nicht von Rekordbox unterstützt'
                )
        
        # Prüfe Dateipfad
        if not file_path or not os.path.exists(file_path):
            validation_result['errors'].append('Datei nicht gefunden oder Pfad ungültig')
            validation_result['is_compatible'] = False
        
        # Prüfe BPM-Bereich
        bpm = track.get('bpm')
        if bpm and (bpm < 50 or bpm > 200):
            validation_result['warnings'].append(
                f'BPM {bpm} liegt außerhalb des typischen Bereichs (50-200)'
            )
        
        # Prüfe Metadaten
        if not track.get('title'):
            validation_result['suggestions'].append('Titel fehlt - wird als "Unknown Title" exportiert')
        
        if not track.get('artist'):
            validation_result['suggestions'].append('Künstler fehlt - wird als "Unknown Artist" exportiert')
        
        # Prüfe Sonderzeichen in Metadaten
        for field in ['title', 'artist', 'album']:
            value = track.get(field, '')
            if value and self._has_problematic_chars(value):
                validation_result['warnings'].append(
                    f'Sonderzeichen in {field} könnten Probleme verursachen'
                )
        
        return validation_result
    
    def create_rekordbox_cue_points(self, track: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Erstellt Rekordbox-kompatible Cue Points"""
        
        cue_points = []
        duration = track.get('duration', 0)
        
        if duration <= 0:
            return cue_points
        
        # Standard Cue Points basierend auf Track-Struktur
        
        # Memory Cue (Anfang)
        cue_points.append({
            'Name': 'Memory',
            'Type': '0',  # Memory Cue
            'Start': '0.000',
            'Num': '0'
        })
        
        # Intro End (geschätzt bei 16 Takten)
        bpm = track.get('bpm', 120)
        if bpm > 0:
            beats_per_second = bpm / 60
            intro_end = min(16 / beats_per_second, duration * 0.2)
            
            cue_points.append({
                'Name': 'Intro End',
                'Type': '1',  # Hot Cue
                'Start': f'{intro_end:.3f}',
                'Num': '1'
            })
        
        # Outro Start (geschätzt bei 85% der Track-Länge)
        outro_start = duration * 0.85
        cue_points.append({
            'Name': 'Outro Start',
            'Type': '1',  # Hot Cue
            'Start': f'{outro_start:.3f}',
            'Num': '2'
        })
        
        return cue_points
    
    def _init_key_mapping(self) -> Dict[str, int]:
        """Initialisiert Key-Mapping für Rekordbox"""
        
        return {
            # Major Keys
            'C major': 1, 'C': 1,
            'Db major': 2, 'C# major': 2, 'Db': 2, 'C#': 2,
            'D major': 3, 'D': 3,
            'Eb major': 4, 'D# major': 4, 'Eb': 4, 'D#': 4,
            'E major': 5, 'E': 5,
            'F major': 6, 'F': 6,
            'F# major': 7, 'Gb major': 7, 'F#': 7, 'Gb': 7,
            'G major': 8, 'G': 8,
            'Ab major': 9, 'G# major': 9, 'Ab': 9, 'G#': 9,
            'A major': 10, 'A': 10,
            'Bb major': 11, 'A# major': 11, 'Bb': 11, 'A#': 11,
            'B major': 12, 'B': 12,
            
            # Minor Keys
            'A minor': 13, 'Am': 13,
            'Bb minor': 14, 'A# minor': 14, 'Bbm': 14, 'A#m': 14,
            'B minor': 15, 'Bm': 15,
            'C minor': 16, 'Cm': 16,
            'C# minor': 17, 'Db minor': 17, 'C#m': 17, 'Dbm': 17,
            'D minor': 18, 'Dm': 18,
            'D# minor': 19, 'Eb minor': 19, 'D#m': 19, 'Ebm': 19,
            'E minor': 20, 'Em': 20,
            'F minor': 21, 'Fm': 21,
            'F# minor': 22, 'Gb minor': 22, 'F#m': 22, 'Gbm': 22,
            'G minor': 23, 'Gm': 23,
            'G# minor': 24, 'Ab minor': 24, 'G#m': 24, 'Abm': 24
        }
    
    def _init_genre_mapping(self) -> Dict[str, str]:
        """Initialisiert Genre-Mapping für Rekordbox"""
        
        return {
            'electronic': 'Electronic',
            'house': 'House',
            'techno': 'Techno',
            'trance': 'Trance',
            'drum and bass': 'Drum & Bass',
            'dubstep': 'Dubstep',
            'ambient': 'Ambient',
            'breakbeat': 'Breakbeat',
            'garage': 'Garage',
            'hardcore': 'Hardcore',
            'jungle': 'Jungle',
            'minimal': 'Minimal',
            'progressive': 'Progressive',
            'psytrance': 'Psytrance',
            'trip hop': 'Trip Hop'
        }
    
    def _clean_string(self, text: str) -> str:
        """Bereinigt String für Rekordbox-Kompatibilität"""
        
        if not text:
            return ''
        
        # Entferne/ersetze problematische Zeichen
        cleaned = text.strip()
        
        # Ersetze XML-problematische Zeichen
        cleaned = cleaned.replace('&', '&amp;')
        cleaned = cleaned.replace('<', '&lt;')
        cleaned = cleaned.replace('>', '&gt;')
        cleaned = cleaned.replace('"', '&quot;')
        cleaned = cleaned.replace("'", '&apos;')
        
        return cleaned
    
    def _format_duration(self, duration: float) -> int:
        """Formatiert Dauer für Rekordbox (in Sekunden)"""
        return int(duration) if duration else 0
    
    def _format_bpm(self, bpm: float) -> int:
        """Formatiert BPM für Rekordbox (BPM * 100)"""
        if not bpm:
            return 0
        return int(float(bpm) * 100)
    
    def _format_year(self, year) -> int:
        """Formatiert Jahr für Rekordbox"""
        if not year:
            return 0
        
        try:
            return int(year)
        except (ValueError, TypeError):
            return 0
    
    def _format_date_added(self, date_added) -> str:
        """Formatiert Hinzufügungsdatum für Rekordbox"""
        
        if not date_added:
            return datetime.now().strftime('%Y-%m-%d')
        
        if isinstance(date_added, str):
            return date_added
        
        if hasattr(date_added, 'strftime'):
            return date_added.strftime('%Y-%m-%d')
        
        return str(date_added)
    
    def _format_comments(self, track: Dict[str, Any]) -> str:
        """Formatiert Kommentare mit zusätzlichen Analyse-Daten"""
        
        comments = []
        
        # Bestehende Kommentare
        if track.get('comments'):
            comments.append(track['comments'])
        
        # Energie-Information
        if track.get('energy'):
            energy_percent = int(track['energy'] * 100)
            comments.append(f'Energy: {energy_percent}%')
        
        # Danceability
        if track.get('danceability'):
            dance_percent = int(track['danceability'] * 100)
            comments.append(f'Danceability: {dance_percent}%')
        
        # Valence (Stimmung)
        if track.get('valence'):
            valence_percent = int(track['valence'] * 100)
            comments.append(f'Valence: {valence_percent}%')
        
        return ' | '.join(comments)
    
    def _format_rating(self, rating) -> int:
        """Formatiert Bewertung für Rekordbox (0-5 Sterne)"""
        
        if not rating:
            return 0
        
        try:
            rating_val = float(rating)
            # Konvertiere zu 0-5 Skala
            if rating_val <= 1.0:
                return int(rating_val * 5)
            else:
                return min(int(rating_val), 5)
        except (ValueError, TypeError):
            return 0
    
    def _format_file_location(self, file_path: str) -> str:
        """Formatiert Dateipfad für Rekordbox Location"""
        return self.format_file_path_for_rekordbox(file_path)
    
    def _format_key(self, key: str) -> int:
        """Formatiert Tonart für Rekordbox"""
        
        if not key:
            return 0
        
        # Versuche zuerst Standard-Key-Konvertierung
        rb_key = self.convert_standard_key_to_rekordbox(key)
        
        # Falls nicht gefunden, versuche Camelot-Konvertierung
        if rb_key == 0 and re.match(r'^\d{1,2}[AB]$', key.upper()):
            rb_key = self.convert_camelot_to_rekordbox_key(key)
        
        return rb_key
    
    def _format_energy(self, energy: float) -> int:
        """Formatiert Energie-Wert für Rekordbox (0-100)"""
        if not energy:
            return 0
        return int(energy * 100)
    
    def _get_file_kind(self, file_path: str) -> str:
        """Bestimmt Dateityp für Rekordbox"""
        
        if not file_path:
            return 'MP3 File'
        
        ext = os.path.splitext(file_path)[1].lower()
        
        kind_mapping = {
            '.mp3': 'MP3 File',
            '.wav': 'WAV File',
            '.aiff': 'AIFF File',
            '.flac': 'FLAC File',
            '.m4a': 'M4A File',
            '.aac': 'AAC File'
        }
        
        return kind_mapping.get(ext, 'Audio File')
    
    def _has_problematic_chars(self, text: str) -> bool:
        """Prüft auf problematische Zeichen"""
        
        problematic_chars = ['<', '>', '&', '"', "'", '\x00', '\x01', '\x02']
        return any(char in text for char in problematic_chars)
    
    def get_rekordbox_version_info(self) -> Dict[str, str]:
        """Gibt Rekordbox-Versionsinformationen zurück"""
        
        return {
            'version': '6.0',
            'company': 'Pioneer DJ',
            'format_version': '1.0.0',
            'supported_formats': ', '.join(self.supported_formats),
            'max_tracks': '10000',
            'max_playlists': '1000'
        }