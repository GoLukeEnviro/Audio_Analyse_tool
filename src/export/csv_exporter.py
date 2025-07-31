"""CSV Exporter - Export von Track-Daten und Playlists im CSV Format"""

import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime


class CSVExporter:
    """Exportiert Track-Daten und Playlists im CSV Format"""
    
    def __init__(self):
        self.encoding = 'utf-8-sig'  # UTF-8 mit BOM für Excel-Kompatibilität
        self.delimiter = ','
        self.quotechar = '"'
        self.quoting = csv.QUOTE_MINIMAL
    
    def export_tracks_csv(self, tracks: List[Dict[str, Any]], 
                         output_path: str,
                         include_analysis: bool = True) -> bool:
        """Exportiert Track-Daten als CSV"""
        
        try:
            # Erstelle Ausgabeverzeichnis
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if not tracks:
                print("Keine Tracks zum Exportieren vorhanden")
                return False
            
            # Bestimme Spalten basierend auf verfügbaren Daten
            fieldnames = self._get_track_fieldnames(tracks, include_analysis)
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(
                    csvfile, 
                    fieldnames=fieldnames,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                    quoting=self.quoting
                )
                
                # Schreibe Header
                writer.writeheader()
                
                # Schreibe Track-Daten
                for track in tracks:
                    row_data = self._prepare_track_row(track, fieldnames)
                    writer.writerow(row_data)
            
            print(f"CSV erfolgreich exportiert: {output_path}")
            print(f"Exportierte Tracks: {len(tracks)}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Exportieren der CSV: {e}")
            return False
    
    def export_playlists_csv(self, playlists: Dict[str, List[Dict[str, Any]]], 
                            output_path: str,
                            separate_files: bool = False) -> bool:
        """Exportiert Playlists als CSV"""
        
        try:
            if separate_files:
                # Erstelle separate CSV-Datei für jede Playlist
                return self._export_separate_playlist_files(playlists, output_path)
            else:
                # Erstelle eine CSV-Datei mit allen Playlists
                return self._export_combined_playlists_csv(playlists, output_path)
                
        except Exception as e:
            print(f"Fehler beim Exportieren der Playlist-CSVs: {e}")
            return False
    
    def export_analysis_summary_csv(self, tracks: List[Dict[str, Any]], 
                                   output_path: str) -> bool:
        """Exportiert eine Analyse-Zusammenfassung als CSV"""
        
        try:
            # Erstelle Ausgabeverzeichnis
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if not tracks:
                return False
            
            # Berechne Statistiken
            stats = self._calculate_track_statistics(tracks)
            
            # Definiere Felder für Zusammenfassung
            fieldnames = [
                'Metrik', 'Wert', 'Einheit', 'Beschreibung'
            ]
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                    quoting=self.quoting
                )
                
                writer.writeheader()
                
                # Schreibe Statistiken
                for stat in stats:
                    writer.writerow(stat)
            
            print(f"Analyse-Zusammenfassung exportiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Exportieren der Analyse-Zusammenfassung: {e}")
            return False
    
    def export_bpm_distribution_csv(self, tracks: List[Dict[str, Any]], 
                                   output_path: str,
                                   bin_size: int = 5) -> bool:
        """Exportiert BPM-Verteilung als CSV"""
        
        try:
            # Erstelle Ausgabeverzeichnis
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Sammle BPM-Werte
            bpm_values = []
            for track in tracks:
                bpm = track.get('bpm')
                if bpm and isinstance(bpm, (int, float)):
                    bpm_values.append(float(bpm))
            
            if not bpm_values:
                print("Keine BPM-Daten zum Exportieren vorhanden")
                return False
            
            # Erstelle BPM-Bins
            min_bpm = int(min(bpm_values))
            max_bpm = int(max(bpm_values))
            
            bins = {}
            for bpm in range(min_bpm, max_bpm + bin_size, bin_size):
                bin_range = f"{bpm}-{bpm + bin_size - 1}"
                bins[bin_range] = 0
            
            # Zähle Tracks pro Bin
            for bpm in bpm_values:
                bin_start = int(bpm // bin_size) * bin_size
                bin_range = f"{bin_start}-{bin_start + bin_size - 1}"
                if bin_range in bins:
                    bins[bin_range] += 1
            
            # Schreibe CSV
            fieldnames = ['BPM_Bereich', 'Anzahl_Tracks', 'Prozent']
            total_tracks = len(bpm_values)
            
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                    quoting=self.quoting
                )
                
                writer.writeheader()
                
                for bin_range, count in bins.items():
                    if count > 0:
                        percentage = (count / total_tracks) * 100
                        writer.writerow({
                            'BPM_Bereich': bin_range,
                            'Anzahl_Tracks': count,
                            'Prozent': f"{percentage:.1f}%"
                        })
            
            print(f"BPM-Verteilung exportiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Exportieren der BPM-Verteilung: {e}")
            return False
    
    def _get_track_fieldnames(self, tracks: List[Dict[str, Any]], 
                             include_analysis: bool) -> List[str]:
        """Bestimmt die Spaltennamen basierend auf verfügbaren Track-Daten"""
        
        # Basis-Felder
        base_fields = [
            'title', 'artist', 'album', 'genre', 'year',
            'duration', 'file_path', 'file_size', 'bitrate'
        ]
        
        # Analyse-Felder
        analysis_fields = [
            'bpm', 'key', 'energy', 'danceability', 'valence',
            'acousticness', 'instrumentalness', 'liveness',
            'speechiness', 'tempo_stability', 'dynamic_range',
            'spectral_centroid', 'spectral_rolloff', 'zero_crossing_rate',
            'mfcc_mean', 'chroma_mean', 'tonnetz_mean'
        ]
        
        # Sammle alle verfügbaren Felder aus den Tracks
        available_fields = set()
        for track in tracks[:10]:  # Prüfe nur erste 10 Tracks für Performance
            available_fields.update(track.keys())
        
        # Filtere und sortiere Felder
        fieldnames = []
        
        # Füge Basis-Felder hinzu (falls vorhanden)
        for field in base_fields:
            if field in available_fields:
                fieldnames.append(field)
        
        # Füge Analyse-Felder hinzu (falls gewünscht und vorhanden)
        if include_analysis:
            for field in analysis_fields:
                if field in available_fields:
                    fieldnames.append(field)
        
        # Füge zusätzliche Felder hinzu
        for field in sorted(available_fields):
            if field not in fieldnames:
                fieldnames.append(field)
        
        return fieldnames
    
    def _prepare_track_row(self, track: Dict[str, Any], 
                          fieldnames: List[str]) -> Dict[str, str]:
        """Bereitet eine Track-Zeile für CSV-Export vor"""
        
        row_data = {}
        
        for field in fieldnames:
            value = track.get(field, '')
            
            # Formatiere verschiedene Datentypen
            if value is None:
                row_data[field] = ''
            elif isinstance(value, bool):
                row_data[field] = 'Ja' if value else 'Nein'
            elif isinstance(value, (int, float)):
                # Formatiere Zahlen
                if field == 'duration':
                    # Konvertiere Sekunden zu MM:SS Format
                    minutes = int(value // 60)
                    seconds = int(value % 60)
                    row_data[field] = f"{minutes:02d}:{seconds:02d}"
                elif field in ['energy', 'danceability', 'valence', 'acousticness', 
                              'instrumentalness', 'liveness', 'speechiness']:
                    # Prozentuale Werte
                    row_data[field] = f"{value * 100:.1f}%"
                elif field == 'bpm':
                    row_data[field] = f"{value:.1f}"
                elif field == 'file_size':
                    # Konvertiere Bytes zu MB
                    mb_size = value / (1024 * 1024)
                    row_data[field] = f"{mb_size:.1f} MB"
                else:
                    row_data[field] = str(value)
            elif isinstance(value, list):
                # Listen als kommagetrennte Werte
                row_data[field] = ', '.join(str(v) for v in value)
            else:
                row_data[field] = str(value)
        
        return row_data
    
    def _export_separate_playlist_files(self, playlists: Dict[str, List[Dict[str, Any]]], 
                                       base_output_path: str) -> bool:
        """Exportiert jede Playlist in eine separate CSV-Datei"""
        
        base_dir = os.path.dirname(base_output_path)
        base_name = os.path.splitext(os.path.basename(base_output_path))[0]
        
        success_count = 0
        
        for playlist_name, tracks in playlists.items():
            # Erstelle sicheren Dateinamen
            safe_name = self._make_safe_filename(playlist_name)
            output_file = os.path.join(base_dir, f"{base_name}_{safe_name}.csv")
            
            if self.export_tracks_csv(tracks, output_file):
                success_count += 1
                print(f"Playlist '{playlist_name}' exportiert: {output_file}")
        
        print(f"Erfolgreich exportierte Playlists: {success_count}/{len(playlists)}")
        return success_count == len(playlists)
    
    def _export_combined_playlists_csv(self, playlists: Dict[str, List[Dict[str, Any]]], 
                                      output_path: str) -> bool:
        """Exportiert alle Playlists in eine CSV-Datei mit Playlist-Spalte"""
        
        # Erstelle Ausgabeverzeichnis
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Sammle alle Tracks mit Playlist-Information
        all_tracks = []
        for playlist_name, tracks in playlists.items():
            for track in tracks:
                track_copy = track.copy()
                track_copy['playlist'] = playlist_name
                all_tracks.append(track_copy)
        
        if not all_tracks:
            print("Keine Tracks in Playlists zum Exportieren vorhanden")
            return False
        
        # Exportiere als normale Track-CSV
        return self.export_tracks_csv(all_tracks, output_path)
    
    def _calculate_track_statistics(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Berechnet Statistiken für Track-Sammlung"""
        
        stats = []
        
        # Basis-Statistiken
        stats.append({
            'Metrik': 'Gesamtanzahl Tracks',
            'Wert': str(len(tracks)),
            'Einheit': 'Tracks',
            'Beschreibung': 'Anzahl der analysierten Audio-Dateien'
        })
        
        # Gesamtdauer
        total_duration = sum(track.get('duration', 0) for track in tracks)
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        stats.append({
            'Metrik': 'Gesamtdauer',
            'Wert': f"{hours}h {minutes}m",
            'Einheit': 'Zeit',
            'Beschreibung': 'Gesamte Spielzeit aller Tracks'
        })
        
        # BPM-Statistiken
        bpm_values = [track.get('bpm') for track in tracks if track.get('bpm')]
        if bpm_values:
            avg_bpm = sum(bpm_values) / len(bpm_values)
            min_bpm = min(bpm_values)
            max_bpm = max(bpm_values)
            
            stats.extend([
                {
                    'Metrik': 'Durchschnittliche BPM',
                    'Wert': f"{avg_bpm:.1f}",
                    'Einheit': 'BPM',
                    'Beschreibung': 'Mittleres Tempo aller Tracks'
                },
                {
                    'Metrik': 'BPM Bereich',
                    'Wert': f"{min_bpm:.0f} - {max_bpm:.0f}",
                    'Einheit': 'BPM',
                    'Beschreibung': 'Tempo-Spanne von langsamsten zu schnellsten Track'
                }
            ])
        
        # Energie-Statistiken
        energy_values = [track.get('energy') for track in tracks if track.get('energy')]
        if energy_values:
            avg_energy = sum(energy_values) / len(energy_values)
            stats.append({
                'Metrik': 'Durchschnittliche Energie',
                'Wert': f"{avg_energy * 100:.1f}%",
                'Einheit': 'Prozent',
                'Beschreibung': 'Mittlere Energie-Level aller Tracks'
            })
        
        # Genre-Verteilung
        genres = {}
        for track in tracks:
            genre = track.get('genre', 'Unbekannt')
            genres[genre] = genres.get(genre, 0) + 1
        
        if genres:
            most_common_genre = max(genres, key=genres.get)
            stats.append({
                'Metrik': 'Häufigstes Genre',
                'Wert': most_common_genre,
                'Einheit': f"({genres[most_common_genre]} Tracks)",
                'Beschreibung': 'Am häufigsten vorkommendes Musik-Genre'
            })
        
        # Dateigröße
        file_sizes = [track.get('file_size', 0) for track in tracks]
        if file_sizes:
            total_size_mb = sum(file_sizes) / (1024 * 1024)
            avg_size_mb = total_size_mb / len(tracks)
            
            stats.extend([
                {
                    'Metrik': 'Gesamtgröße',
                    'Wert': f"{total_size_mb:.1f}",
                    'Einheit': 'MB',
                    'Beschreibung': 'Gesamter Speicherplatz aller Audio-Dateien'
                },
                {
                    'Metrik': 'Durchschnittliche Dateigröße',
                    'Wert': f"{avg_size_mb:.1f}",
                    'Einheit': 'MB',
                    'Beschreibung': 'Mittlere Dateigröße pro Track'
                }
            ])
        
        return stats
    
    def _make_safe_filename(self, filename: str) -> str:
        """Erstellt einen sicheren Dateinamen"""
        
        # Entferne/ersetze problematische Zeichen
        invalid_chars = '<>:"/\\|?*'
        safe_name = filename
        
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Entferne führende/nachfolgende Leerzeichen und Punkte
        safe_name = safe_name.strip(' .')
        
        # Begrenze Länge
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        
        return safe_name or 'playlist'
    
    def read_csv_tracks(self, file_path: str) -> List[Dict[str, Any]]:
        """Liest Track-Daten aus CSV-Datei"""
        
        tracks = []
        
        try:
            with open(file_path, 'r', encoding=self.encoding) as csvfile:
                # Versuche automatische Delimiter-Erkennung
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(
                    csvfile,
                    delimiter=delimiter,
                    quotechar=self.quotechar
                )
                
                for row in reader:
                    # Konvertiere String-Werte zurück zu passenden Datentypen
                    track = self._parse_csv_row(row)
                    tracks.append(track)
            
            print(f"CSV erfolgreich gelesen: {len(tracks)} Tracks aus {file_path}")
            
        except Exception as e:
            print(f"Fehler beim Lesen der CSV: {e}")
        
        return tracks
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Konvertiert CSV-Zeile zurück zu Track-Daten"""
        
        track = {}
        
        for key, value in row.items():
            if not value or value.strip() == '':
                track[key] = None
                continue
            
            # Versuche Datentyp-Konvertierung
            if key in ['duration', 'year', 'bitrate', 'file_size']:
                try:
                    if key == 'duration' and ':' in value:
                        # MM:SS Format zurück zu Sekunden
                        parts = value.split(':')
                        track[key] = int(parts[0]) * 60 + int(parts[1])
                    elif key == 'file_size' and 'MB' in value:
                        # MB zurück zu Bytes
                        mb_value = float(value.replace(' MB', ''))
                        track[key] = int(mb_value * 1024 * 1024)
                    else:
                        track[key] = int(value)
                except ValueError:
                    track[key] = value
            
            elif key in ['bpm', 'energy', 'danceability', 'valence', 
                        'acousticness', 'instrumentalness', 'liveness', 'speechiness']:
                try:
                    if '%' in value:
                        # Prozent zurück zu Dezimal
                        track[key] = float(value.replace('%', '')) / 100
                    else:
                        track[key] = float(value)
                except ValueError:
                    track[key] = value
            
            elif value in ['Ja', 'Nein']:
                track[key] = value == 'Ja'
            
            else:
                track[key] = value
        
        return track
    
    def get_supported_formats(self) -> List[str]:
        """Gibt unterstützte Export-Formate zurück"""
        return ['.csv']