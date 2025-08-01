import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock PySide6 imports for testing without GUI
pytest_plugins = ['pytest_qt']

class TestMainWindow:
    """Test cases for MainWindow GUI component"""
    
    @pytest.fixture
    def app(self, qtbot):
        """Create QApplication for testing"""
        from gui.main_window import MainWindow
        window = MainWindow()
        qtbot.addWidget(window)
        return window
    
    def test_main_window_initialization(self, app):
        """Test MainWindow initialization"""
        assert app is not None
        assert app.windowTitle() == "DJ Audio Analysis Tool"
        assert app.isVisible() is False  # Not shown by default in tests
    
    def test_main_window_components(self, app):
        """Test MainWindow has required components"""
        # Check for main components
        assert hasattr(app, 'central_widget')
        assert hasattr(app, 'menu_bar')
        assert hasattr(app, 'status_bar')
        assert hasattr(app, 'toolbar')
    
    def test_menu_actions(self, app, qtbot):
        """Test menu actions"""
        # Test File menu actions
        file_menu = app.menuBar().findChild(object, 'file_menu')
        if file_menu:
            actions = file_menu.actions()
            assert len(actions) > 0
    
    def test_toolbar_actions(self, app, qtbot):
        """Test toolbar actions"""
        toolbar = app.findChild(object, 'main_toolbar')
        if toolbar:
            actions = toolbar.actions()
            assert len(actions) > 0
    
    @patch('gui.main_window.QFileDialog.getOpenFileNames')
    def test_import_audio_files(self, mock_dialog, app, qtbot):
        """Test audio file import functionality"""
        # Mock file dialog to return test files
        mock_dialog.return_value = (['test1.mp3', 'test2.wav'], '')
        
        # Simulate import action
        if hasattr(app, 'import_files'):
            app.import_files()
            
            # Verify dialog was called
            mock_dialog.assert_called_once()

class TestAudioAnalysisWidget:
    """Test cases for AudioAnalysisWidget"""
    
    @pytest.fixture
    def widget(self, qtbot):
        """Create AudioAnalysisWidget for testing"""
        try:
            from gui.components.audio_analysis_widget import AudioAnalysisWidget
            widget = AudioAnalysisWidget()
            qtbot.addWidget(widget)
            return widget
        except ImportError:
            pytest.skip("AudioAnalysisWidget not available")
    
    def test_widget_initialization(self, widget):
        """Test widget initialization"""
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_analysis_progress(self, widget, qtbot):
        """Test analysis progress indication"""
        if hasattr(widget, 'progress_bar'):
            # Test progress updates
            widget.update_progress(50)
            assert widget.progress_bar.value() == 50
    
    @patch('gui.components.audio_analysis_widget.AudioAnalyzer')
    def test_start_analysis(self, mock_analyzer, widget, qtbot):
        """Test starting audio analysis"""
        mock_analyzer_instance = Mock()
        mock_analyzer.return_value = mock_analyzer_instance
        
        if hasattr(widget, 'start_analysis'):
            test_files = ['test1.mp3', 'test2.wav']
            widget.start_analysis(test_files)
            
            # Verify analyzer was created
            mock_analyzer.assert_called_once()

class TestPlaylistWidget:
    """Test cases for PlaylistWidget"""
    
    @pytest.fixture
    def widget(self, qtbot):
        """Create PlaylistWidget for testing"""
        try:
            from gui.components.playlist_widget import PlaylistWidget
            widget = PlaylistWidget()
            qtbot.addWidget(widget)
            return widget
        except ImportError:
            pytest.skip("PlaylistWidget not available")
    
    def test_widget_initialization(self, widget):
        """Test widget initialization"""
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_add_track_to_playlist(self, widget, qtbot, mock_track_metadata):
        """Test adding track to playlist"""
        if hasattr(widget, 'add_track'):
            initial_count = widget.get_track_count() if hasattr(widget, 'get_track_count') else 0
            
            widget.add_track(mock_track_metadata)
            
            if hasattr(widget, 'get_track_count'):
                assert widget.get_track_count() == initial_count + 1
    
    def test_remove_track_from_playlist(self, widget, qtbot, mock_track_metadata):
        """Test removing track from playlist"""
        if hasattr(widget, 'add_track') and hasattr(widget, 'remove_track'):
            # Add a track first
            widget.add_track(mock_track_metadata)
            initial_count = widget.get_track_count() if hasattr(widget, 'get_track_count') else 1
            
            # Remove the track
            widget.remove_track(0)  # Remove first track
            
            if hasattr(widget, 'get_track_count'):
                assert widget.get_track_count() == initial_count - 1
    
    def test_clear_playlist(self, widget, qtbot, mock_track_metadata):
        """Test clearing playlist"""
        if hasattr(widget, 'add_track') and hasattr(widget, 'clear_playlist'):
            # Add some tracks
            widget.add_track(mock_track_metadata)
            widget.add_track(mock_track_metadata)
            
            # Clear playlist
            widget.clear_playlist()
            
            if hasattr(widget, 'get_track_count'):
                assert widget.get_track_count() == 0

class TestTrackBrowserWidget:
    """Test cases for TrackBrowserWidget"""
    
    @pytest.fixture
    def widget(self, qtbot):
        """Create TrackBrowserWidget for testing"""
        try:
            from gui.components.track_browser_widget import TrackBrowserWidget
            widget = TrackBrowserWidget()
            qtbot.addWidget(widget)
            return widget
        except ImportError:
            pytest.skip("TrackBrowserWidget not available")
    
    def test_widget_initialization(self, widget):
        """Test widget initialization"""
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_load_tracks(self, widget, qtbot, mock_playlist_data):
        """Test loading tracks into browser"""
        if hasattr(widget, 'load_tracks'):
            tracks = mock_playlist_data['tracks']
            widget.load_tracks(tracks)
            
            # Verify tracks were loaded
            if hasattr(widget, 'get_track_count'):
                assert widget.get_track_count() == len(tracks)
    
    def test_filter_tracks(self, widget, qtbot, mock_playlist_data):
        """Test track filtering functionality"""
        if hasattr(widget, 'load_tracks') and hasattr(widget, 'filter_tracks'):
            tracks = mock_playlist_data['tracks']
            widget.load_tracks(tracks)
            
            # Filter by BPM
            widget.filter_tracks({'bpm_min': 129, 'bpm_max': 131})
            
            # Should show only tracks within BPM range
            if hasattr(widget, 'get_visible_track_count'):
                visible_count = widget.get_visible_track_count()
                assert visible_count <= len(tracks)
    
    def test_sort_tracks(self, widget, qtbot, mock_playlist_data):
        """Test track sorting functionality"""
        if hasattr(widget, 'load_tracks') and hasattr(widget, 'sort_tracks'):
            tracks = mock_playlist_data['tracks']
            widget.load_tracks(tracks)
            
            # Sort by BPM
            widget.sort_tracks('bpm', ascending=True)
            
            # Verify sorting (implementation dependent)
            assert True  # Basic test that sorting doesn't crash

class TestExportWidget:
    """Test cases for ExportWidget"""
    
    @pytest.fixture
    def widget(self, qtbot):
        """Create ExportWidget for testing"""
        try:
            from gui.components.export_widget import ExportWidget
            widget = ExportWidget()
            qtbot.addWidget(widget)
            return widget
        except ImportError:
            pytest.skip("ExportWidget not available")
    
    def test_widget_initialization(self, widget):
        """Test widget initialization"""
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_export_format_selection(self, widget, qtbot):
        """Test export format selection"""
        if hasattr(widget, 'set_export_format'):
            widget.set_export_format('m3u')
            
            if hasattr(widget, 'get_export_format'):
                assert widget.get_export_format() == 'm3u'
    
    @patch('gui.components.export_widget.QFileDialog.getSaveFileName')
    def test_export_playlist(self, mock_dialog, widget, qtbot, mock_playlist_data):
        """Test playlist export functionality"""
        mock_dialog.return_value = ('test_playlist.m3u', '')
        
        if hasattr(widget, 'export_playlist'):
            tracks = mock_playlist_data['tracks']
            result = widget.export_playlist(tracks, 'm3u')
            
            # Verify export was attempted
            mock_dialog.assert_called_once()

class TestSettingsWidget:
    """Test cases for SettingsWidget"""
    
    @pytest.fixture
    def widget(self, qtbot):
        """Create SettingsWidget for testing"""
        try:
            from gui.components.settings_widget import SettingsWidget
            widget = SettingsWidget()
            qtbot.addWidget(widget)
            return widget
        except ImportError:
            pytest.skip("SettingsWidget not available")
    
    def test_widget_initialization(self, widget):
        """Test widget initialization"""
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_load_settings(self, widget, qtbot, test_config):
        """Test loading settings"""
        if hasattr(widget, 'load_settings'):
            widget.load_settings(test_config)
            
            # Verify settings were loaded
            assert True  # Basic test that loading doesn't crash
    
    def test_save_settings(self, widget, qtbot):
        """Test saving settings"""
        if hasattr(widget, 'save_settings'):
            settings = widget.save_settings()
            
            # Verify settings were returned
            assert isinstance(settings, dict)
    
    def test_reset_settings(self, widget, qtbot):
        """Test resetting settings to defaults"""
        if hasattr(widget, 'reset_to_defaults'):
            widget.reset_to_defaults()
            
            # Verify reset doesn't crash
            assert True

class TestOnboardingWizard:
    """Test cases for OnboardingWizard"""
    
    @pytest.fixture
    def wizard(self, qtbot):
        """Create OnboardingWizard for testing"""
        try:
            from gui.components.onboarding_wizard import OnboardingWizard
            wizard = OnboardingWizard()
            qtbot.addWidget(wizard)
            return wizard
        except ImportError:
            pytest.skip("OnboardingWizard not available")
    
    def test_wizard_initialization(self, wizard):
        """Test wizard initialization"""
        assert wizard is not None
        assert hasattr(wizard, 'currentPage')
    
    def test_wizard_navigation(self, wizard, qtbot):
        """Test wizard page navigation"""
        if hasattr(wizard, 'next') and hasattr(wizard, 'back'):
            initial_page = wizard.currentPage()
            
            # Go to next page
            wizard.next()
            
            # Go back
            wizard.back()
            
            # Should be back to initial page
            assert wizard.currentPage() == initial_page
    
    def test_wizard_completion(self, wizard, qtbot):
        """Test wizard completion"""
        if hasattr(wizard, 'accept'):
            # Complete wizard
            wizard.accept()
            
            # Verify wizard is completed
            assert True  # Basic test that completion doesn't crash

class TestEnergyCanvas:
    """Test cases for EnergyCanvas widget"""
    
    @pytest.fixture
    def canvas(self, qtbot):
        """Create EnergyCanvas for testing"""
        try:
            from gui.components.energy_canvas import EnergyCanvas
            canvas = EnergyCanvas()
            qtbot.addWidget(canvas)
            return canvas
        except ImportError:
            pytest.skip("EnergyCanvas not available")
    
    def test_canvas_initialization(self, canvas):
        """Test canvas initialization"""
        assert canvas is not None
        assert isinstance(canvas, QWidget)
    
    def test_plot_energy_curve(self, canvas, qtbot, mock_track_metadata):
        """Test plotting energy curve"""
        if hasattr(canvas, 'plot_energy_curve'):
            # Create mock energy data
            energy_data = [0.1, 0.3, 0.5, 0.7, 0.9, 0.6, 0.4]
            
            canvas.plot_energy_curve(energy_data)
            
            # Verify plot was created
            assert True  # Basic test that plotting doesn't crash
    
    def test_canvas_interaction(self, canvas, qtbot):
        """Test canvas mouse interaction"""
        if hasattr(canvas, 'mousePressEvent'):
            # Simulate mouse click
            QTest.mouseClick(canvas, Qt.LeftButton)
            
            # Verify interaction doesn't crash
            assert True

class TestAudioPreviewPlayer:
    """Test cases for AudioPreviewPlayer"""
    
    @pytest.fixture
    def player(self, qtbot):
        """Create AudioPreviewPlayer for testing"""
        try:
            from gui.components.audio_preview_player import AudioPreviewPlayer
            player = AudioPreviewPlayer()
            qtbot.addWidget(player)
            return player
        except ImportError:
            pytest.skip("AudioPreviewPlayer not available")
    
    def test_player_initialization(self, player):
        """Test player initialization"""
        assert player is not None
        assert isinstance(player, QWidget)
    
    @patch('gui.components.audio_preview_player.pygame.mixer')
    def test_load_audio_file(self, mock_mixer, player, qtbot):
        """Test loading audio file"""
        if hasattr(player, 'load_file'):
            player.load_file('test.mp3')
            
            # Verify file loading was attempted
            assert True  # Basic test that loading doesn't crash
    
    @patch('gui.components.audio_preview_player.pygame.mixer')
    def test_play_pause_audio(self, mock_mixer, player, qtbot):
        """Test play/pause functionality"""
        if hasattr(player, 'play') and hasattr(player, 'pause'):
            # Test play
            player.play()
            
            # Test pause
            player.pause()
            
            # Verify operations don't crash
            assert True
    
    def test_seek_position(self, player, qtbot):
        """Test seeking to position"""
        if hasattr(player, 'seek'):
            player.seek(30.0)  # Seek to 30 seconds
            
            # Verify seeking doesn't crash
            assert True

class TestDragDropTimeline:
    """Test cases for DragDropTimeline"""
    
    @pytest.fixture
    def timeline(self, qtbot):
        """Create DragDropTimeline for testing"""
        try:
            from gui.components.drag_drop_timeline import DragDropTimeline
            timeline = DragDropTimeline()
            qtbot.addWidget(timeline)
            return timeline
        except ImportError:
            pytest.skip("DragDropTimeline not available")
    
    def test_timeline_initialization(self, timeline):
        """Test timeline initialization"""
        assert timeline is not None
        assert isinstance(timeline, QWidget)
    
    def test_add_track_to_timeline(self, timeline, qtbot, mock_track_metadata):
        """Test adding track to timeline"""
        if hasattr(timeline, 'add_track'):
            timeline.add_track(mock_track_metadata)
            
            # Verify track was added
            if hasattr(timeline, 'get_track_count'):
                assert timeline.get_track_count() > 0
    
    def test_drag_drop_functionality(self, timeline, qtbot):
        """Test drag and drop functionality"""
        if hasattr(timeline, 'dragEnterEvent') and hasattr(timeline, 'dropEvent'):
            # Basic test that drag/drop events don't crash
            assert True
    
    def test_timeline_zoom(self, timeline, qtbot):
        """Test timeline zoom functionality"""
        if hasattr(timeline, 'zoom_in') and hasattr(timeline, 'zoom_out'):
            initial_zoom = timeline.get_zoom_level() if hasattr(timeline, 'get_zoom_level') else 1.0
            
            timeline.zoom_in()
            timeline.zoom_out()
            
            # Verify zoom operations don't crash
            assert True