"""
Test cases for FastAPI endpoints
"""

import pytest
import json
from unittest.mock import patch, Mock
from fastapi import status


class TestHealthEndpoints:
    """Test health check and status endpoints"""
    
    def test_health_check(self, client):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data
    
    def test_api_status(self, client):
        """Test /api/status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["api_version"] == "2.0.0"
        assert data["status"] == "operational"
        assert "cache_statistics" in data
        assert "system_info" in data
    
    def test_root_endpoint(self, client):
        """Test root / endpoint"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "features" in data


class TestTracksEndpoints:
    """Test tracks API endpoints"""
    
    @patch('backend.api.endpoints.tracks.get_cached_tracks')
    def test_list_tracks_empty(self, mock_get_cached, client):
        """Test listing tracks when no tracks are cached"""
        mock_get_cached.return_value = []
        
        response = client.get("/api/tracks")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["tracks"] == []
        assert data["total_count"] == 0
        assert data["page"] == 1
    
    @patch('backend.api.endpoints.tracks.get_cached_tracks')
    def test_list_tracks_with_data(self, mock_get_cached, client, sample_track_analysis):
        """Test listing tracks with sample data"""
        mock_get_cached.return_value = [sample_track_analysis]
        
        response = client.get("/api/tracks")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data["tracks"]) == 1
        assert data["total_count"] == 1
        assert data["tracks"][0]["filename"] == "test_track.mp3"
    
    @patch('backend.api.endpoints.tracks.get_cached_tracks')
    def test_list_tracks_with_filters(self, mock_get_cached, client, sample_track_analysis):
        """Test listing tracks with filters"""
        mock_get_cached.return_value = [sample_track_analysis]
        
        # Test BPM filter
        response = client.get("/api/tracks?min_bpm=120&max_bmp=140")
        assert response.status_code == status.HTTP_200_OK
        
        # Test mood filter
        response = client.get("/api/tracks?mood=euphoric")
        assert response.status_code == status.HTTP_200_OK
        
        # Test search
        response = client.get("/api/tracks?search=test")
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_tracks_pagination(self, client):
        """Test tracks pagination"""
        response = client.get("/api/tracks?page=1&per_page=10")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    @patch('backend.api.endpoints.tracks.get_cache_manager')
    def test_get_track_details_not_found(self, mock_get_cache_manager, client):
        """Test getting track details for non-existent track"""
        mock_cache_manager = Mock()
        mock_cache_manager.load_from_cache.return_value = None
        mock_get_cache_manager.return_value = mock_cache_manager
        
        with patch('os.path.exists', return_value=False):
            response = client.get("/api/tracks/nonexistent.mp3")
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('backend.api.endpoints.tracks.get_cache_manager')
    def test_find_similar_tracks_empty(self, mock_get_cache_manager, client):
        """Test finding similar tracks with no reference"""
        mock_cache_manager = Mock()
        mock_cache_manager.load_from_cache.return_value = None
        mock_get_cache_manager.return_value = mock_cache_manager
        
        response = client.get("/api/tracks/search/similar?track_path=/path/to/track.mp3")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('backend.api.endpoints.tracks.get_cached_tracks')
    def test_get_tracks_statistics(self, mock_get_cached, client, sample_track_analysis):
        """Test getting track statistics"""
        mock_get_cached.return_value = [sample_track_analysis]
        
        response = client.get("/api/tracks/stats/overview")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_tracks" in data
        assert "statistics" in data
        assert "distributions" in data


class TestPlaylistsEndpoints:
    """Test playlists API endpoints"""
    
    @patch('backend.api.endpoints.playlists.get_playlist_engine')
    def test_list_presets(self, mock_get_engine, client, mock_playlist_engine):
        """Test listing playlist presets"""
        mock_get_engine.return_value = mock_playlist_engine
        
        response = client.get("/api/playlists/presets")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "presets" in data
        assert "total_count" in data
        assert len(data["presets"]) > 0
    
    @patch('backend.api.endpoints.playlists.get_playlist_engine')
    def test_get_preset_details(self, mock_get_engine, client, mock_playlist_engine):
        """Test getting preset details"""
        mock_get_engine.return_value = mock_playlist_engine
        
        response = client.get("/api/playlists/presets/hybrid_smart")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "preset" in data
        assert data["preset"]["name"] == "hybrid_smart"
    
    @patch('backend.api.endpoints.playlists.get_playlist_engine')
    def test_get_preset_details_not_found(self, mock_get_engine, client):
        """Test getting non-existent preset details"""
        mock_engine = Mock()
        mock_engine.get_preset_details.return_value = None
        mock_get_engine.return_value = mock_engine
        
        response = client.get("/api/playlists/presets/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('backend.api.endpoints.playlists.get_cache_manager')
    def test_generate_playlist_insufficient_tracks(self, mock_get_cache_manager, client, playlist_generation_request_data):
        """Test playlist generation with insufficient tracks"""
        mock_cache_manager = Mock()
        mock_cache_manager.is_cached.return_value = False
        mock_get_cache_manager.return_value = mock_cache_manager
        
        response = client.post("/api/playlists/generate", json=playlist_generation_request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "Insufficient analyzed tracks" in data["detail"]
    
    @patch('backend.api.endpoints.playlists.get_cache_manager')
    @patch('backend.api.endpoints.playlists.generate_playlist_task')
    def test_generate_playlist_success(self, mock_task, mock_get_cache_manager, client, playlist_generation_request_data):
        """Test successful playlist generation"""
        mock_cache_manager = Mock()
        mock_cache_manager.is_cached.return_value = True
        mock_get_cache_manager.return_value = mock_cache_manager
        
        response = client.post("/api/playlists/generate", json=playlist_generation_request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "started"
        assert "status_url" in data
    
    def test_get_generation_status_not_found(self, client):
        """Test getting status of non-existent generation task"""
        response = client.get("/api/playlists/generate/nonexistent/status")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('backend.api.endpoints.playlists.get_playlist_exporter')
    def test_export_playlist(self, mock_get_exporter, client, mock_playlist_exporter, playlist_export_request_data):
        """Test playlist export"""
        mock_get_exporter.return_value = mock_playlist_exporter
        
        response = client.post("/api/playlists/export", json=playlist_export_request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["success"] is True
        assert "output_path" in data
        assert "filename" in data
    
    @patch('backend.api.endpoints.playlists.get_playlist_engine')
    def test_list_algorithms(self, mock_get_engine, client, mock_playlist_engine):
        """Test listing available algorithms"""
        mock_get_engine.return_value = mock_playlist_engine
        
        response = client.get("/api/playlists/algorithms")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "algorithms" in data
        assert "total_count" in data
    
    @patch('backend.api.endpoints.playlists.get_cache_manager')
    @patch('backend.api.endpoints.playlists.get_playlist_exporter')
    def test_validate_tracks(self, mock_get_exporter, mock_get_cache_manager, client, mock_playlist_exporter):
        """Test track validation for playlist generation"""
        mock_cache_manager = Mock()
        mock_cache_manager.is_cached.return_value = True
        mock_cache_manager.load_from_cache.return_value = {"file_path": "/path/to/track.mp3"}
        mock_get_cache_manager.return_value = mock_cache_manager
        mock_get_exporter.return_value = mock_playlist_exporter
        
        track_paths = ["/path/to/track1.mp3", "/path/to/track2.mp3"]
        response = client.post("/api/playlists/validate", json=track_paths)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_requested" in data
        assert "available_tracks" in data
        assert "ready_for_generation" in data


class TestAnalysisEndpoints:
    """Test analysis API endpoints"""
    
    @patch('backend.api.endpoints.analysis.find_audio_files')
    def test_start_analysis_no_files(self, mock_find_files, client, analysis_request_data):
        """Test starting analysis with no files found"""
        mock_find_files.return_value = []
        
        response = client.post("/api/analysis/start", json=analysis_request_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        data = response.json()
        assert "No audio files found" in data["detail"]
    
    @patch('backend.api.endpoints.analysis.find_audio_files')
    @patch('os.path.exists')
    @patch('backend.api.endpoints.analysis.analyze_files_task')
    def test_start_analysis_success(self, mock_task, mock_exists, mock_find_files, client, analysis_request_data):
        """Test successful analysis start"""
        mock_find_files.return_value = ["/path/to/track1.mp3", "/path/to/track2.mp3"]
        mock_exists.return_value = True
        
        response = client.post("/api/analysis/start", json=analysis_request_data)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "started"
        assert "total_files" in data
        assert "status_url" in data
    
    def test_get_analysis_status_not_found(self, client):
        """Test getting status of non-existent analysis task"""
        response = client.get("/api/analysis/nonexistent/status")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('backend.api.endpoints.analysis.get_cache_manager')
    def test_get_cache_stats(self, mock_get_cache_manager, client, mock_cache_manager):
        """Test getting cache statistics"""
        mock_get_cache_manager.return_value = mock_cache_manager
        
        response = client.get("/api/analysis/cache/stats")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_files" in data
        assert "total_size_mb" in data
        assert "cache_directory" in data
    
    @patch('backend.api.endpoints.analysis.get_cache_manager')
    def test_cleanup_cache(self, mock_get_cache_manager, client, mock_cache_manager):
        """Test cache cleanup"""
        mock_get_cache_manager.return_value = mock_cache_manager
        
        response = client.post("/api/analysis/cache/cleanup?max_age_days=30&max_size_mb=1000")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["success"] is True
        assert "message" in data
    
    @patch('backend.api.endpoints.analysis.get_cache_manager')
    def test_clear_cache(self, mock_get_cache_manager, client, mock_cache_manager):
        """Test clearing entire cache"""
        mock_get_cache_manager.return_value = mock_cache_manager
        
        response = client.post("/api/analysis/cache/clear")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["success"] is True
        assert "deleted_files" in data["data"]
    
    @patch('backend.api.endpoints.analysis.get_analyzer')
    def test_get_supported_formats(self, mock_get_analyzer, client, mock_analyzer):
        """Test getting supported audio formats"""
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/analysis/formats")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "supported_formats" in data
        assert "total_count" in data
        assert "examples" in data
    
    @patch('backend.api.endpoints.analysis.get_analyzer')
    def test_get_analysis_stats(self, mock_get_analyzer, client, mock_analyzer):
        """Test getting analysis statistics"""
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/analysis/stats")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "analyzer_stats" in data
        assert "current_session" in data
    
    @patch('backend.api.endpoints.analysis.find_audio_files')
    @patch('backend.api.endpoints.analysis.get_cache_manager')
    def test_validate_directory(self, mock_get_cache_manager, mock_find_files, client, mock_cache_manager):
        """Test directory validation for analysis"""
        mock_find_files.return_value = ["/path/to/track1.mp3"]
        mock_get_cache_manager.return_value = mock_cache_manager
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True), \
             patch('pathlib.Path.iterdir', return_value=[]):
            
            response = client.get("/api/analysis/validate/directory?directory=/path/to/music")
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert data["valid"] is True
            assert "audio_files_found" in data
            assert "recommendation" in data