import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to be tested

from backend.api.endpoints.analysis import find_audio_files
from config.settings import settings

@pytest.fixture
def mock_settings():
    """Mock settings for find_audio_files tests"""
    original_settings = settings.config.copy()
    settings.config.update({
        "audio_analysis": {
            "supported_formats": [".mp3", ".wav", ".flac"]
        },
        "music_library": {
            "min_file_size_kb": 1,
            "max_depth": 10,
            "exclude_patterns": []
        }
    })
    yield
    settings.config = original_settings # Restore original settings

@pytest.fixture
def create_mock_directory_structure(tmp_path):
    """Helper to create a mock directory structure"""
    def _creator(structure):
        for name, content in structure.items():
            path = tmp_path / name
            if isinstance(content, dict):
                path.mkdir()
                _creator_recursive(path, content)
            else:
                path.write_text(content)
        return tmp_path

    def _creator_recursive(base_path, structure):
        for name, content in structure.items():
            path = base_path / name
            if isinstance(content, dict):
                path.mkdir()
                _creator_recursive(path, content)
            else:
                path.write_text(content)
    return _creator

class TestFindAudioFiles:
    """Tests for the find_audio_files utility function"""

    @pytest.mark.parametrize("file_content, expected_count", [
        ("dummy content", 1),
        ("", 0) # Too small if min_file_size_kb is > 0
    ])
    def test_find_audio_files_basic(self, create_mock_directory_structure, mock_settings, file_content, expected_count):
        """Test basic file finding and size filtering"""
        mock_dir = create_mock_directory_structure({
            "music": {
                "track1.mp3": file_content,
                "track2.flac": "dummy content",
                "text.txt": "not audio"
            }
        })
        
        # Adjust min_file_size_kb for empty file test
        if file_content == "":
            settings.set("music_library.min_file_size_kb", 1)
        else:
            settings.set("music_library.min_file_size_kb", 0)

        found_files = find_audio_files(directories=[str(mock_dir / "music")])
        assert len(found_files) == expected_count + (1 if file_content != "" else 0) # track2.flac is always found if not empty

    def test_find_audio_files_recursive(self, create_mock_directory_structure, mock_settings):
        """Test recursive file finding"""
        mock_dir = create_mock_directory_structure({
            "music": {
                "genre1": {
                    "track1.mp3": "content"
                },
                "genre2": {
                    "subgenre": {
                        "track2.wav": "content"
                    }
                },
                "track3.flac": "content"
            }
        })
        found_files = find_audio_files(directories=[str(mock_dir / "music")], recursive=True)
        assert len(found_files) == 3
        assert any("track1.mp3" in f for f in found_files)
        assert any("track2.wav" in f for f in found_files)
        assert any("track3.flac" in f for f in found_files)

    def test_find_audio_files_non_recursive(self, create_mock_directory_structure, mock_settings):
        """Test non-recursive file finding"""
        mock_dir = create_mock_directory_structure({
            "music": {
                "genre1": {
                    "track1.mp3": "content"
                },
                "track2.wav": "content"
            }
        })
        found_files = find_audio_files(directories=[str(mock_dir / "music")], recursive=False)
        assert len(found_files) == 1
        assert any("track2.wav" in f for f in found_files)
        assert not any("track1.mp3" in f for f in found_files)

    def test_find_audio_files_include_patterns(self, create_mock_directory_structure, mock_settings):
        """Test filtering with include patterns"""
        mock_dir = create_mock_directory_structure({
            "music": {
                "track1.mp3": "content",
                "track2.wav": "content",
                "track3.flac": "content"
            }
        })
        found_files = find_audio_files(directories=[str(mock_dir / "music")], include_patterns=["*mp3"])
        assert len(found_files) == 1
        assert any("track1.mp3" in f for f in found_files)

    def test_find_audio_files_exclude_patterns(self, create_mock_directory_structure, mock_settings):
        """Test filtering with exclude patterns"""
        mock_dir = create_mock_directory_structure({
            "music": {
                "track1.mp3": "content",
                "temp_track.mp3": "content",
                "cache": {
                    "cached_track.mp3": "content"
                }
            }
        })
        settings.set("music_library.exclude_patterns", ["temp*", "cache"])
        found_files = find_audio_files(directories=[str(mock_dir / "music")], recursive=True)
        assert len(found_files) == 1
        assert any("track1.mp3" in f for f in found_files)
        assert not any("temp_track.mp3" in f for f in found_files)
        assert not any("cached_track.mp3" in f for f in found_files)

    def test_find_audio_files_non_existent_directory(self, mock_settings):
        """Test with a non-existent directory"""
        found_files = find_audio_files(directories=["/path/to/nonexistent"])
        assert len(found_files) == 0

    @patch('os.access', return_value=False)
    def test_find_audio_files_permission_denied(self, mock_access, create_mock_directory_structure, mock_settings):
        """Test with permission denied directory"""
        mock_dir = create_mock_directory_structure({
            "restricted_music": {
                "track.mp3": "content"
            }
        })
        # Mock os.walk to simulate PermissionError
        with patch('os.walk', side_effect=PermissionError("Permission denied")):
            found_files = find_audio_files(directories=[str(mock_dir / "restricted_music")])
            assert len(found_files) == 0

    def test_find_audio_files_max_depth(self, create_mock_directory_structure, mock_settings):
        """Test max_depth filtering"""
        mock_dir = create_mock_directory_structure({
            "music": {
                "level1": {
                    "track1.mp3": "content",
                    "level2": {
                        "track2.mp3": "content"
                    }
                }
            }
        })
        settings.set("music_library.max_depth", 1)
        found_files = find_audio_files(directories=[str(mock_dir / "music")], recursive=True)
        assert len(found_files) == 1
        assert any("track1.mp3" in f for f in found_files)
        assert not any("track2.mp3" in f for f in found_files)
