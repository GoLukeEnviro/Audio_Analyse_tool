import pytest
import os
import tempfile
import xml.etree.ElementTree as ET
import csv
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from export_engine.exporter import PlaylistExporter
from export_engine.formats.m3u_exporter import M3UExporter
from export_engine.formats.rekordbox_exporter import RekordboxExporter
from export_engine.formats.csv_exporter import CSVExporter
from export_engine.formats.json_exporter import JSONExporter

class TestPlaylistExporter:
    """Test cases for PlaylistExporter class"""
    
    def test_exporter_initialization(self):
        """Test PlaylistExporter initialization"""
        exporter = PlaylistExporter()
        assert exporter is not None
        assert hasattr(exporter, 'supported_formats')
        assert len(exporter.supported_formats) > 0
    
    def test_get_supported_formats(self):
        """Test getting supported export formats"""
        exporter = PlaylistExporter()
        formats = exporter.get_supported_formats()
        
        assert isinstance(formats, list)
        assert 'm3u' in formats
        assert 'csv' in formats
        assert 'json' in formats
    
    def test_export_playlist_m3u(self, tmp_path, mock_playlist_data):
        """Test exporting playlist to M3U format"""
        exporter = PlaylistExporter()
        output_file = tmp_path / "test_playlist.m3u"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export_playlist(tracks, str(output_file), 'm3u')
        
        assert result is True
        assert output_file.exists()
        
        # Verify file content
        content = output_file.read_text(encoding='utf-8')
        assert '#EXTM3U' in content
        assert 'track1.mp3' in content
    
    def test_export_playlist_csv(self, tmp_path, mock_playlist_data):
        """Test exporting playlist to CSV format"""
        exporter = PlaylistExporter()
        output_file = tmp_path / "test_playlist.csv"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export_playlist(tracks, str(output_file), 'csv')
        
        assert result is True
        assert output_file.exists()
        
        # Verify CSV content
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == len(tracks)
            assert 'filename' in rows[0]
            assert 'bpm' in rows[0]
    
    def test_export_playlist_json(self, tmp_path, mock_playlist_data):
        """Test exporting playlist to JSON format"""
        exporter = PlaylistExporter()
        output_file = tmp_path / "test_playlist.json"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export_playlist(tracks, str(output_file), 'json')
        
        assert result is True
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert 'playlist' in data
            assert 'tracks' in data['playlist']
            assert len(data['playlist']['tracks']) == len(tracks)
    
    def test_export_playlist_unsupported_format(self, tmp_path, mock_playlist_data):
        """Test exporting playlist with unsupported format"""
        exporter = PlaylistExporter()
        output_file = tmp_path / "test_playlist.xyz"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export_playlist(tracks, str(output_file), 'xyz')
        
        assert result is False
    
    def test_export_empty_playlist(self, tmp_path):
        """Test exporting empty playlist"""
        exporter = PlaylistExporter()
        output_file = tmp_path / "empty_playlist.m3u"
        
        result = exporter.export_playlist([], str(output_file), 'm3u')
        
        assert result is True
        assert output_file.exists()
        
        # Verify file content
        content = output_file.read_text(encoding='utf-8')
        assert '#EXTM3U' in content
    
    def test_validate_tracks(self, mock_playlist_data):
        """Test track validation before export"""
        exporter = PlaylistExporter()
        
        # Valid tracks
        valid_tracks = mock_playlist_data['tracks']
        assert exporter.validate_tracks(valid_tracks) is True
        
        # Invalid tracks (missing filename)
        invalid_tracks = [{'bpm': 128.0, 'key': 'C'}]
        assert exporter.validate_tracks(invalid_tracks) is False
        
        # Empty tracks
        assert exporter.validate_tracks([]) is True

class TestM3UExporter:
    """Test cases for M3U format exporter"""
    
    def test_m3u_exporter_initialization(self):
        """Test M3UExporter initialization"""
        exporter = M3UExporter()
        assert exporter is not None
    
    def test_export_basic_m3u(self, tmp_path, mock_playlist_data):
        """Test basic M3U export"""
        exporter = M3UExporter()
        output_file = tmp_path / "test.m3u"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify M3U format
        lines = output_file.read_text(encoding='utf-8').strip().split('\n')
        assert lines[0] == '#EXTM3U'
        
        # Check track entries
        track_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        assert len(track_lines) == len(tracks)
    
    def test_export_extended_m3u(self, tmp_path, mock_playlist_data):
        """Test extended M3U export with metadata"""
        exporter = M3UExporter()
        output_file = tmp_path / "test_extended.m3u"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file), extended=True)
        
        assert result is True
        assert output_file.exists()
        
        # Verify extended M3U format
        content = output_file.read_text(encoding='utf-8')
        assert '#EXTM3U' in content
        assert '#EXTINF:' in content  # Extended info tags
    
    def test_export_with_relative_paths(self, tmp_path, mock_playlist_data):
        """Test M3U export with relative paths"""
        exporter = M3UExporter()
        output_file = tmp_path / "test_relative.m3u"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file), use_relative_paths=True)
        
        assert result is True
        assert output_file.exists()
        
        # Verify relative paths
        content = output_file.read_text(encoding='utf-8')
        # Should not contain absolute paths
        assert 'C:\\' not in content and '/home/' not in content
    
    def test_export_with_unicode_filenames(self, tmp_path):
        """Test M3U export with unicode filenames"""
        exporter = M3UExporter()
        output_file = tmp_path / "test_unicode.m3u"
        
        tracks = [
            {'filename': 'track_ñoño.mp3', 'bpm': 128.0},
            {'filename': 'track_中文.mp3', 'bpm': 130.0},
            {'filename': 'track_العربية.mp3', 'bpm': 132.0}
        ]
        
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify unicode handling
        content = output_file.read_text(encoding='utf-8')
        assert 'track_ñoño.mp3' in content
        assert 'track_中文.mp3' in content
        assert 'track_العربية.mp3' in content

class TestRekordboxExporter:
    """Test cases for Rekordbox XML format exporter"""
    
    def test_rekordbox_exporter_initialization(self):
        """Test RekordboxExporter initialization"""
        exporter = RekordboxExporter()
        assert exporter is not None
    
    def test_export_rekordbox_xml(self, tmp_path, mock_playlist_data):
        """Test Rekordbox XML export"""
        exporter = RekordboxExporter()
        output_file = tmp_path / "test_rekordbox.xml"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify XML structure
        tree = ET.parse(output_file)
        root = tree.getroot()
        assert root.tag == 'DJ_PLAYLISTS'
        
        # Check for collection and playlists
        collection = root.find('COLLECTION')
        assert collection is not None
        
        playlists = root.find('PLAYLISTS')
        assert playlists is not None
    
    def test_export_with_full_metadata(self, tmp_path, mock_track_metadata):
        """Test Rekordbox export with full track metadata"""
        exporter = RekordboxExporter()
        output_file = tmp_path / "test_full_metadata.xml"
        
        tracks = [mock_track_metadata]
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify metadata in XML
        tree = ET.parse(output_file)
        root = tree.getroot()
        
        track_elem = root.find('.//TRACK')
        assert track_elem is not None
        assert track_elem.get('Name') == mock_track_metadata['title']
        assert track_elem.get('Artist') == mock_track_metadata['artist']
        assert float(track_elem.get('AverageBpm')) == mock_track_metadata['bpm']
    
    def test_export_with_cue_points(self, tmp_path):
        """Test Rekordbox export with cue points"""
        exporter = RekordboxExporter()
        output_file = tmp_path / "test_cue_points.xml"
        
        tracks = [{
            'filename': 'test_track.mp3',
            'title': 'Test Track',
            'artist': 'Test Artist',
            'bpm': 128.0,
            'cue_points': [
                {'position': 0.0, 'type': 'intro'},
                {'position': 30.0, 'type': 'verse'},
                {'position': 60.0, 'type': 'chorus'}
            ]
        }]
        
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify cue points in XML
        tree = ET.parse(output_file)
        root = tree.getroot()
        
        position_marks = root.findall('.//POSITION_MARK')
        assert len(position_marks) == 3

class TestCSVExporter:
    """Test cases for CSV format exporter"""
    
    def test_csv_exporter_initialization(self):
        """Test CSVExporter initialization"""
        exporter = CSVExporter()
        assert exporter is not None
        assert hasattr(exporter, 'default_fields')
    
    def test_export_basic_csv(self, tmp_path, mock_playlist_data):
        """Test basic CSV export"""
        exporter = CSVExporter()
        output_file = tmp_path / "test.csv"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify CSV content
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == len(tracks)
            assert 'filename' in reader.fieldnames
            assert 'bpm' in reader.fieldnames
            assert 'key' in reader.fieldnames
    
    def test_export_custom_fields(self, tmp_path, mock_track_metadata):
        """Test CSV export with custom fields"""
        exporter = CSVExporter()
        output_file = tmp_path / "test_custom.csv"
        
        custom_fields = ['filename', 'bpm', 'energy_level', 'mood']
        tracks = [mock_track_metadata]
        
        result = exporter.export(tracks, str(output_file), fields=custom_fields)
        
        assert result is True
        assert output_file.exists()
        
        # Verify custom fields
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == custom_fields
    
    def test_export_with_missing_fields(self, tmp_path):
        """Test CSV export with missing fields in tracks"""
        exporter = CSVExporter()
        output_file = tmp_path / "test_missing.csv"
        
        tracks = [
            {'filename': 'track1.mp3', 'bpm': 128.0},  # Missing key
            {'filename': 'track2.mp3', 'key': 'G'},     # Missing bpm
        ]
        
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify handling of missing fields
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 2
            # Missing fields should be empty or have default values
            assert rows[0]['key'] in ['', 'N/A', None] or 'key' not in rows[0]
    
    def test_export_with_special_characters(self, tmp_path):
        """Test CSV export with special characters"""
        exporter = CSVExporter()
        output_file = tmp_path / "test_special.csv"
        
        tracks = [{
            'filename': 'track,with,commas.mp3',
            'title': 'Track "with quotes"',
            'artist': 'Artist\nwith\nnewlines',
            'bpm': 128.0
        }]
        
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify proper CSV escaping
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert 'track,with,commas.mp3' in rows[0]['filename']
            assert 'Track "with quotes"' in rows[0]['title']

class TestJSONExporter:
    """Test cases for JSON format exporter"""
    
    def test_json_exporter_initialization(self):
        """Test JSONExporter initialization"""
        exporter = JSONExporter()
        assert exporter is not None
    
    def test_export_basic_json(self, tmp_path, mock_playlist_data):
        """Test basic JSON export"""
        exporter = JSONExporter()
        output_file = tmp_path / "test.json"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file))
        
        assert result is True
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            assert 'playlist' in data
            assert 'metadata' in data
            assert 'tracks' in data['playlist']
            assert len(data['playlist']['tracks']) == len(tracks)
    
    def test_export_with_metadata(self, tmp_path, mock_playlist_data):
        """Test JSON export with playlist metadata"""
        exporter = JSONExporter()
        output_file = tmp_path / "test_metadata.json"
        
        tracks = mock_playlist_data['tracks']
        metadata = {
            'name': 'Test Playlist',
            'description': 'A test playlist',
            'created_by': 'Test User',
            'genre': 'Electronic'
        }
        
        result = exporter.export(tracks, str(output_file), metadata=metadata)
        
        assert result is True
        assert output_file.exists()
        
        # Verify metadata in JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            assert data['metadata']['name'] == 'Test Playlist'
            assert data['metadata']['description'] == 'A test playlist'
    
    def test_export_pretty_formatted(self, tmp_path, mock_playlist_data):
        """Test JSON export with pretty formatting"""
        exporter = JSONExporter()
        output_file = tmp_path / "test_pretty.json"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file), pretty=True)
        
        assert result is True
        assert output_file.exists()
        
        # Verify pretty formatting (indentation)
        content = output_file.read_text(encoding='utf-8')
        assert '\n' in content  # Should have newlines
        assert '  ' in content  # Should have indentation
    
    def test_export_compact_json(self, tmp_path, mock_playlist_data):
        """Test JSON export in compact format"""
        exporter = JSONExporter()
        output_file = tmp_path / "test_compact.json"
        
        tracks = mock_playlist_data['tracks']
        result = exporter.export(tracks, str(output_file), pretty=False)
        
        assert result is True
        assert output_file.exists()
        
        # Verify compact formatting (no unnecessary whitespace)
        content = output_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        assert len(lines) <= 3  # Should be very few lines

class TestExportValidation:
    """Test cases for export validation and error handling"""
    
    def test_invalid_output_path(self, mock_playlist_data):
        """Test export with invalid output path"""
        exporter = PlaylistExporter()
        
        tracks = mock_playlist_data['tracks']
        # Invalid path (non-existent directory)
        invalid_path = "/non/existent/directory/playlist.m3u"
        
        result = exporter.export_playlist(tracks, invalid_path, 'm3u')
        assert result is False
    
    def test_permission_denied(self, tmp_path, mock_playlist_data):
        """Test export with permission denied"""
        exporter = PlaylistExporter()
        output_file = tmp_path / "readonly.m3u"
        
        # Create file and make it read-only
        output_file.touch()
        output_file.chmod(0o444)  # Read-only
        
        tracks = mock_playlist_data['tracks']
        
        try:
            result = exporter.export_playlist(tracks, str(output_file), 'm3u')
            # On some systems, this might still succeed, so we don't assert False
        except PermissionError:
            # Expected on systems that enforce permissions
            pass
        finally:
            # Restore permissions for cleanup
            output_file.chmod(0o644)
    
    def test_disk_space_simulation(self, tmp_path, mock_playlist_data):
        """Test export behavior when disk space is limited"""
        exporter = PlaylistExporter()
        output_file = tmp_path / "large_playlist.m3u"
        
        # Create a very large track list to simulate disk space issues
        large_track_list = mock_playlist_data['tracks'] * 10000
        
        # This test mainly ensures the export doesn't crash with large data
        try:
            result = exporter.export_playlist(large_track_list, str(output_file), 'm3u')
            # Should either succeed or fail gracefully
            assert isinstance(result, bool)
        except Exception as e:
            # Should not raise unhandled exceptions
            assert False, f"Export raised unhandled exception: {e}"
    
    def test_concurrent_export(self, tmp_path, mock_playlist_data):
        """Test concurrent export operations"""
        import threading
        import time
        
        exporter = PlaylistExporter()
        tracks = mock_playlist_data['tracks']
        results = []
        
        def export_worker(file_suffix):
            output_file = tmp_path / f"concurrent_{file_suffix}.m3u"
            result = exporter.export_playlist(tracks, str(output_file), 'm3u')
            results.append(result)
        
        # Start multiple export threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=export_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All exports should succeed
        assert all(results)
        assert len(results) == 3