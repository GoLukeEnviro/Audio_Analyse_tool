"""GUI Module - Desktop Interface mit PyQt5"""

from .main_window import AudioAnalyseApp
from .track_browser import TrackBrowser
from .playlist_dashboard import PlaylistDashboard
from .settings_dialog import SettingsDialog

__all__ = ['AudioAnalyseApp', 'TrackBrowser', 'PlaylistDashboard', '