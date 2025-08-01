import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
    QFileDialog, QProgressBar, QLabel, QTextEdit, QComboBox,
    QSpinBox, QCheckBox, QGroupBox, QSplitter, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QLineEdit, QSlider,
    QFrame, QScrollArea, QGridLayout, QButtonGroup, QRadioButton
)
from PySide6.QtCore import (
    Qt, QThread, QTimer, Signal, QSettings, QSize, QPoint,
    QPropertyAnimation, QEasingCurve, QRect
)
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont, QAction,
    QPalette, QLinearGradient, QBrush
)

# Import core modules
try:
    from core.mood_classifier import HybridClassifier
except ImportError:
    class HybridClassifier:
        def __init__(self): pass
        def classify(self, features): return {'mood': 'unknown'}

try:
    from core.cache_manager import CacheManager
except ImportError:
    class CacheManager:
        def __init__(self): pass
        def get(self, key): return None
        def set(self, key, value): pass

try:
    from core.playlist_engine import PlaylistEngine, PlaylistPreset, PlaylistRule, SortingAlgorithm
except ImportError:
    from enum import Enum
    class SortingAlgorithm(Enum):
        HARMONIC = "harmonic"
    class PlaylistRule:
        def __init__(self, *args, **kwargs): pass
    class PlaylistPreset:
        def __init__(self, *args, **kwargs): pass
    class PlaylistEngine:
        def __init__(self): pass
        def generate_playlist(self, tracks, preset=None): return tracks[:10]

from audio_analysis.analyzer import AudioAnalyzer

try:
    from export.playlist_exporter import PlaylistExporter
except ImportError:
    class PlaylistExporter:
        def __init__(self): pass
        def export_m3u(self, tracks, path): return True
# Import GUI modules
try:
    from playlist_dashboard import PlaylistDashboard
    from track_browser import TrackBrowser
    from settings_dialog import SettingsDialog
    from playlist_wizard import PlaylistWizard
    from interactive_timeline import InteractiveTimeline
    from onboarding_wizard import OnboardingWizard
    from audio_preview_player import AudioPreviewPlayer
except ImportError:
    # Fallback: Create dummy classes if modules don't exist
    from PySide6.QtWidgets import QWidget, QDialog
    
    class PlaylistDashboard(QWidget):
        def __init__(self, parent=None): super().__init__(parent)
    
    class TrackBrowser(QWidget):
        def __init__(self, parent=None): super().__init__(parent)
    
    class SettingsDialog(QDialog):
        def __init__(self, parent=None): 
            super().__init__(parent)
            self.setWindowTitle("Einstellungen")
        def exec(self): return 0
    
    class PlaylistWizard(QDialog):
        def __init__(self, parent=None): 
            super().__init__(parent)
            self.setWindowTitle("Playlist Wizard")
        def exec(self): return 0
    
    class InteractiveTimeline(QWidget):
        def __init__(self, parent=None): super().__init__(parent)
    
    class OnboardingWizard(QDialog):
        def __init__(self, parent=None): 
            super().__init__(parent)
            self.setWindowTitle("Willkommen")
        def exec(self): return 0
    
    class AudioPreviewPlayer(QWidget):
        def __init__(self, parent=None): super().__init__(parent)

logger = logging.getLogger(__name__)

class AnalysisWorker(QThread):
    """Worker-Thread für Audio-Analyse"""
    progress_updated = Signal(int, str)
    analysis_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, file_paths: List[str], analyzer: AudioAnalyzer):
        super().__init__()
        self.file_paths = file_paths
        self.analyzer = analyzer
        self.is_cancelled = False
    
    def run(self):
        try:
            total_files = len(self.file_paths)
            results = []
            
            for i, file_path in enumerate(self.file_paths):
                if self.is_cancelled:
                    break
                
                self.progress_updated.emit(
                    int((i / total_files) * 100),
                    f"Analysiere: {os.path.basename(file_path)}"
                )
                
                result = self.analyzer.analyze_track(file_path)
                results.append(result)
            
            if not self.is_cancelled:
                self.progress_updated.emit(100, "Analyse abgeschlossen")
                self.analysis_completed.emit({'results': results})
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def cancel(self):
        self.is_cancelled = True

class MainWindow(QMainWindow):
    """Hauptfenster der DJ Audio-Analyse-Tool Pro Anwendung"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ Audio-Analyse-Tool Pro v2.0")
        self.setMinimumSize(1200, 800)
        
        # Initialize core components
        self.cache_manager = CacheManager()
        self.mood_classifier = HybridClassifier()
        self.playlist_engine = PlaylistEngine()
        self.analyzer = AudioAnalyzer(
            cache_dir="cache",
            enable_multiprocessing=True
        )
        self.exporter = PlaylistExporter()
        
        # Erstelle zentrale Widgets
        self.playlist_dashboard = PlaylistDashboard()
        self.track_browser = TrackBrowser()
        self.playlist_wizard = PlaylistWizard()
        self.interactive_timeline = InteractiveTimeline()
        self.onboarding_wizard = OnboardingWizard()
        self.audio_preview = AudioPreviewPlayer()
        
        # Data
        self.analyzed_tracks = []
        self.current_playlist = []
        
        # Worker thread
        self.analysis_worker = None
        
        # Settings
        self.settings = QSettings("DJTool", "AudioAnalyzer")
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        
        # Prüfe ob Onboarding nötig ist
        self.check_first_run()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - File browser and controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center panel - Main content tabs
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Toolbar Actions
        self.create_actions()
        self.create_toolbar()
        
        # Verbinde Signale
        self.connect_signals()
    
    def create_left_panel(self) -> QWidget:
        """Erstellt das linke Panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # File operations
        file_group = QGroupBox("Dateien")
        file_layout = QVBoxLayout(file_group)
        
        self.add_files_btn = QPushButton("Dateien hinzufügen")
        self.add_folder_btn = QPushButton("Ordner hinzufügen")
        self.clear_files_btn = QPushButton("Liste leeren")
        
        file_layout.addWidget(self.add_files_btn)
        file_layout.addWidget(self.add_folder_btn)
        file_layout.addWidget(self.clear_files_btn)
        
        layout.addWidget(file_group)
        
        # Analysis controls
        analysis_group = QGroupBox("Analyse")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.analyze_btn = QPushButton("Analyse starten")
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Bereit")
        
        analysis_layout.addWidget(self.analyze_btn)
        analysis_layout.addWidget(self.cancel_btn)
        analysis_layout.addWidget(self.progress_bar)
        analysis_layout.addWidget(self.progress_label)
        
        layout.addWidget(analysis_group)
        
        # Export controls
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        self.export_m3u_btn = QPushButton("M3U exportieren")
        self.export_json_btn = QPushButton("JSON exportieren")
        
        export_layout.addWidget(self.export_m3u_btn)
        export_layout.addWidget(self.export_json_btn)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """Erstellt das zentrale Panel mit Tabs"""
        self.tab_widget = QTabWidget()
        
        # Erweiterte Tabs
        self.tab_widget.addTab(self.playlist_dashboard, "Playlist Dashboard")
        self.tab_widget.addTab(self.playlist_wizard, "Playlist Wizard")
        
        # Timeline Tab mit Audio-Preview
        timeline_widget = QWidget()
        timeline_layout = QVBoxLayout(timeline_widget)
        
        # Splitter für Timeline und Audio-Preview
        timeline_splitter = QSplitter(Qt.Vertical)
        
        timeline_splitter.addWidget(self.interactive_timeline)
        timeline_splitter.addWidget(self.audio_preview)
        
        # Setze Splitter-Verhältnis (Timeline größer)
        timeline_splitter.setSizes([400, 200])
        
        timeline_layout.addWidget(timeline_splitter)
        
        self.tab_widget.addTab(timeline_widget, "Interactive Timeline")
        self.tab_widget.addTab(self.track_browser, "Track Browser")
        
        # Tracks tab
        self.tracks_tab = self.create_tracks_tab()
        self.tab_widget.addTab(self.tracks_tab, "Tracks")
        
        # Analysis tab
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "Analyse")
        
        return self.tab_widget
    
    def create_tracks_tab(self) -> QWidget:
        """Erstellt den Tracks-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Tracks table
        self.tracks_table = QTableWidget()
        self.tracks_table.setColumnCount(8)
        self.tracks_table.setHorizontalHeaderLabels([
            "Dateiname", "BPM", "Key", "Camelot", "Energie", "Stimmung", "Dauer", "Status"
        ])
        
        header = self.tracks_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        
        self.tracks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tracks_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.tracks_table)
        
        return widget
    
    def create_analysis_tab(self) -> QWidget:
        """Erstellt den Analyse-Tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Analysis details
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlainText("Wählen Sie einen Track aus der Tracks-Tabelle aus, um Details zu sehen.")
        
        layout.addWidget(QLabel("Analyse-Details:"))
        layout.addWidget(self.analysis_text)
        
        return widget
    
    def create_menu_bar(self):
        """Erstellt die Menüleiste"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("Datei")
        
        open_action = QAction("Dateien öffnen", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.add_files)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Beenden", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Hilfe")
        
        about_action = QAction("Über", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_actions(self):
        """Erstellt Actions für Menü und Toolbar"""
        # Datei-Actions
        self.open_action = QAction("Öffnen", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)
        
        self.save_action = QAction("Speichern", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_file)
        
        self.exit_action = QAction("Beenden", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        
        # Playlist-Actions
        self.new_wizard_action = QAction("Neuer Playlist Wizard", self)
        self.new_wizard_action.setShortcut("Ctrl+N")
        self.new_wizard_action.triggered.connect(self.start_new_wizard)
        
        self.export_action = QAction("Playlist Exportieren", self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self.export_playlist)
        
        # Einstellungen
        self.settings_action = QAction("Einstellungen", self)
        self.settings_action.triggered.connect(self.show_settings)
    
    def create_toolbar(self):
        """Erstellt Toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.new_wizard_action)
        toolbar.addAction(self.export_action)
        toolbar.addSeparator()
        toolbar.addAction(self.settings_action)
    
    def create_status_bar(self):
        """Erstellt die Statusleiste"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Bereit")
    
    def setup_connections(self):
        """Verbindet Signale und Slots"""
        # File operations
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.clear_files_btn.clicked.connect(self.clear_files)
        
        # Analysis
        self.analyze_btn.clicked.connect(self.start_analysis)
        self.cancel_btn.clicked.connect(self.cancel_analysis)
        
        # Export
        self.export_m3u_btn.clicked.connect(self.export_m3u)
        self.export_json_btn.clicked.connect(self.export_json)
        
        # Table selections
        self.tracks_table.itemSelectionChanged.connect(self.on_track_selected)
        
        # Timeline und Audio-Preview Verbindungen
        if hasattr(self.interactive_timeline, 'track_selected'):
            self.interactive_timeline.track_selected.connect(self.on_timeline_track_selected)
        if hasattr(self.interactive_timeline, 'playlist_changed'):
            self.interactive_timeline.playlist_changed.connect(self.on_timeline_playlist_changed)
        
        # Track Browser zu Timeline
        if hasattr(self.track_browser, 'track_double_clicked'):
            self.track_browser.track_double_clicked.connect(self.add_track_to_timeline)
    
    def add_files(self):
        """Fügt Audio-Dateien hinzu"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(
            "Audio Files (*.mp3 *.wav *.flac *.aac *.ogg *.m4a);;All Files (*)"
        )
        
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            self.add_files_to_table(files)
    
    def add_folder(self):
        """Fügt alle Audio-Dateien aus einem Ordner hinzu"""
        folder = QFileDialog.getExistingDirectory(self, "Ordner auswählen")
        
        if folder:
            audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
            files = []
            
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in audio_extensions):
                        files.append(os.path.join(root, filename))
            
            if files:
                self.add_files_to_table(files)
            else:
                QMessageBox.information(self, "Keine Dateien", "Keine Audio-Dateien im ausgewählten Ordner gefunden.")
    
    def add_files_to_table(self, files: List[str]):
        """Fügt Dateien zur Tracks-Tabelle hinzu"""
        current_row = self.tracks_table.rowCount()
        
        for file_path in files:
            # Prüfe ob Datei bereits vorhanden
            already_exists = False
            for row in range(self.tracks_table.rowCount()):
                if self.tracks_table.item(row, 0).data(Qt.UserRole) == file_path:
                    already_exists = True
                    break
            
            if already_exists:
                continue
            
            self.tracks_table.insertRow(current_row)
            
            filename_item = QTableWidgetItem(os.path.basename(file_path))
            filename_item.setData(Qt.UserRole, file_path)
            self.tracks_table.setItem(current_row, 0, filename_item)
            
            # Placeholder values
            for col in range(1, 8):
                self.tracks_table.setItem(current_row, col, QTableWidgetItem("-"))
            
            self.tracks_table.setItem(current_row, 7, QTableWidgetItem("Nicht analysiert"))
            
            current_row += 1
        
        self.update_status(f"{self.tracks_table.rowCount()} Dateien geladen")
    
    def clear_files(self):
        """Leert die Dateiliste"""
        self.tracks_table.setRowCount(0)
        self.analyzed_tracks.clear()
        self.update_status("Dateiliste geleert")
    
    def start_analysis(self):
        """Startet die Audio-Analyse"""
        if self.tracks_table.rowCount() == 0:
            QMessageBox.warning(self, "Keine Dateien", "Bitte fügen Sie zuerst Audio-Dateien hinzu.")
            return
        
        # Sammle Dateipfade
        file_paths = []
        for row in range(self.tracks_table.rowCount()):
            file_path = self.tracks_table.item(row, 0).data(Qt.UserRole)
            file_paths.append(file_path)
        
        # Starte Worker-Thread
        self.analysis_worker = AnalysisWorker(file_paths, self.analyzer)
        self.analysis_worker.progress_updated.connect(self.update_progress)
        self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
        self.analysis_worker.error_occurred.connect(self.on_analysis_error)
        
        self.analysis_worker.start()
        
        # UI-Status aktualisieren
        self.analyze_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.update_status("Analyse läuft...")
    
    def cancel_analysis(self):
        """Bricht die laufende Analyse ab"""
        if self.analysis_worker:
            self.analysis_worker.cancel()
            self.analysis_worker.wait()
        
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Analyse abgebrochen")
        self.update_status("Analyse abgebrochen")
    
    def connect_signals(self):
        """Verbindet Signale zwischen Komponenten"""
        # Playlist Wizard -> Timeline
        if hasattr(self.playlist_wizard, 'playlist_generated'):
            self.playlist_wizard.playlist_generated.connect(
                self.interactive_timeline.load_playlist
            )
        
        # Timeline -> Dashboard
        if hasattr(self.interactive_timeline, 'playlist_updated'):
            self.interactive_timeline.playlist_updated.connect(
                self.playlist_dashboard.update_playlist
            )
    
    def start_new_wizard(self):
        """Startet neuen Playlist Wizard"""
        self.tab_widget.setCurrentWidget(self.playlist_wizard)
        if hasattr(self.playlist_wizard, 'start_wizard'):
            self.playlist_wizard.start_wizard()
    
    def export_playlist(self):
        """Exportiert aktuelle Playlist"""
        current_widget = self.tab_widget.currentWidget()
        
        if current_widget == self.interactive_timeline:
            if hasattr(self.interactive_timeline, 'export_playlist'):
                self.interactive_timeline.export_playlist()
        elif current_widget == self.playlist_dashboard:
            if hasattr(self.playlist_dashboard, 'export_current_playlist'):
                self.playlist_dashboard.export_current_playlist()
    
    def open_file(self):
        """Öffnet Datei"""
        self.add_files()
    
    def save_file(self):
        """Speichert Datei"""
        self.export_json()
    
    def show_settings(self):
        """Zeigt Einstellungen-Dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def update_progress(self, value: int, message: str):
        """Aktualisiert den Fortschrittsbalken"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def on_analysis_completed(self, data: Dict):
        """Wird aufgerufen wenn die Analyse abgeschlossen ist"""
        results = data.get('results', [])
        self.analyzed_tracks = results
        
        # Aktualisiere Tracks-Tabelle
        for i, result in enumerate(results):
            if i < self.tracks_table.rowCount():
                self.update_track_row(i, result)
        
        # UI-Status zurücksetzen
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Analyse abgeschlossen")
        
        self.update_status(f"Analyse von {len(results)} Tracks abgeschlossen")
    
    def on_analysis_error(self, error_message: str):
        """Wird bei Analyse-Fehlern aufgerufen"""
        QMessageBox.critical(self, "Analyse-Fehler", f"Fehler bei der Analyse:\n{error_message}")
        
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Fehler")
        self.update_status("Analyse-Fehler")
    
    def update_track_row(self, row: int, result: Dict):
        """Aktualisiert eine Zeile in der Tracks-Tabelle"""
        features = result.get('features', {})
        metadata = result.get('metadata', {})
        mood = result.get('mood', {})
        camelot = result.get('camelot', {})
        
        # BPM
        bpm = features.get('tempo', 0.0) * 200  # Rückkonvertierung
        self.tracks_table.setItem(row, 1, QTableWidgetItem(f"{bpm:.0f}"))
        
        # Key
        key = camelot.get('key', 'Unknown')
        self.tracks_table.setItem(row, 2, QTableWidgetItem(key))
        
        # Camelot
        camelot_key = camelot.get('camelot', '-')
        self.tracks_table.setItem(row, 3, QTableWidgetItem(camelot_key))
        
        # Energy
        energy = features.get('energy', 0.0)
        self.tracks_table.setItem(row, 4, QTableWidgetItem(f"{energy:.2f}"))
        
        # Mood
        primary_mood = mood.get('primary_mood', 'Unknown')
        self.tracks_table.setItem(row, 5, QTableWidgetItem(primary_mood))
        
        # Duration
        duration = metadata.get('duration', 0)
        duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
        self.tracks_table.setItem(row, 6, QTableWidgetItem(duration_str))
        
        # Status
        status = "Analysiert" if not result.get('errors') else "Fehler"
        self.tracks_table.setItem(row, 7, QTableWidgetItem(status))
    
    def on_track_selected(self):
        """Wird aufgerufen wenn ein Track ausgewählt wird"""
        current_row = self.tracks_table.currentRow()
        
        if current_row >= 0 and current_row < len(self.analyzed_tracks):
            result = self.analyzed_tracks[current_row]
            self.show_track_details(result)
    
    def show_track_details(self, result: Dict):
        """Zeigt Track-Details im Analyse-Tab"""
        details = []
        details.append(f"Datei: {result.get('filename', 'Unknown')}")
        details.append(f"Analysiert: {result.get('analysis_timestamp', 'Unknown')}")
        details.append("")
        
        # Features
        features = result.get('features', {})
        details.append("Audio-Features:")
        for key, value in features.items():
            if isinstance(value, float):
                details.append(f"  {key}: {value:.3f}")
            else:
                details.append(f"  {key}: {value}")
        
        details.append("")
        
        # Mood
        mood = result.get('mood', {})
        if mood:
            details.append("Stimmungs-Analyse:")
            details.append(f"  Primäre Stimmung: {mood.get('primary_mood', 'Unknown')}")
            details.append(f"  Konfidenz: {mood.get('confidence', 0.0):.2f}")
            details.append(f"  Energie-Level: {mood.get('energy_level', 0.0):.2f}")
            details.append(f"  Valence: {mood.get('valence', 0.0):.2f}")
            details.append(f"  Danceability: {mood.get('danceability', 0.0):.2f}")
        
        details.append("")
        
        # Camelot
        camelot = result.get('camelot', {})
        if camelot:
            details.append("Harmonische Analyse:")
            details.append(f"  Key: {camelot.get('key', 'Unknown')}")
            details.append(f"  Camelot: {camelot.get('camelot', 'Unknown')}")
            details.append(f"  Kompatible Keys: {', '.join(camelot.get('compatible_keys', []))}")
        
        # Errors
        errors = result.get('errors', [])
        if errors:
            details.append("")
            details.append("Fehler:")
            for error in errors:
                details.append(f"  {error}")
        
        self.analysis_text.setPlainText("\n".join(details))
    
    def export_m3u(self):
        """Exportiert die Playlist als M3U"""
        if not self.analyzed_tracks:
            QMessageBox.warning(self, "Keine Daten", "Bitte analysieren Sie zuerst einige Tracks.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "M3U Playlist speichern", "", "M3U Files (*.m3u);;All Files (*)"
        )
        
        if file_path:
            try:
                success = self.exporter.export_m3u(self.analyzed_tracks, file_path)
                if success:
                    QMessageBox.information(self, "Export erfolgreich", f"Playlist wurde als M3U exportiert:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Export-Fehler", "Playlist konnte nicht exportiert werden.")
            except Exception as e:
                QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Export:\n{str(e)}")
    
    def export_json(self):
        """Exportiert die Analyse-Daten als JSON"""
        if not self.analyzed_tracks:
            QMessageBox.warning(self, "Keine Daten", "Bitte analysieren Sie zuerst einige Tracks.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSON Daten speichern", "", "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                export_data = {
                    'version': '2.0',
                    'exported_at': datetime.now().isoformat(),
                    'tracks': self.analyzed_tracks
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "Export erfolgreich", f"Daten wurden als JSON exportiert:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export-Fehler", f"Fehler beim Export:\n{str(e)}")
    
    def show_about(self):
        """Zeigt den Über-Dialog"""
        QMessageBox.about(
            self,
            "Über DJ Audio-Analyse-Tool Pro",
            "DJ Audio-Analyse-Tool Pro v2.0\n\n"
            "Professionelle Audio-Analyse für DJs\n\n"
            "Features:\n"
            "• Erweiterte Audio-Analyse mit Essentia\n"
            "• Hybrid Mood-Classifier\n"
            "• Intelligente Playlist-Engine\n"
            "• Interaktive Camelot Wheel\n"
            "• Rekordbox-Integration\n\n"
            "© 2024 DJ Audio-Analyse-Tool"
        )
    
    def update_status(self, message: str):
        """Aktualisiert die Statusleiste"""
        self.status_bar.showMessage(message)
    
    def load_settings(self):
        """Lädt die Anwendungseinstellungen"""
        # Fenstergeometrie
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Fensterstatus
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def save_settings(self):
        """Speichert die Anwendungseinstellungen"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def check_first_run(self):
        """Prüft ob dies der erste Start ist und zeigt Onboarding"""
        first_run = self.settings.value("first_run", True, type=bool)
        
        if first_run:
            # Zeige Onboarding-Wizard
            if self.onboarding_wizard.exec() == QDialog.Accepted:
                self.settings.setValue("first_run", False)
    
    def on_timeline_track_selected(self, track_data):
        """Wird aufgerufen wenn ein Track in der Timeline ausgewählt wird"""
        if hasattr(self.audio_preview, 'load_track'):
            self.audio_preview.load_track(track_data)
    
    def on_timeline_playlist_changed(self, playlist_data):
        """Wird aufgerufen wenn sich die Timeline-Playlist ändert"""
        if hasattr(self.playlist_dashboard, 'update_playlist'):
            self.playlist_dashboard.update_playlist(playlist_data)
    
    def add_track_to_timeline(self, track_data):
        """Fügt einen Track zur Timeline hinzu"""
        if hasattr(self.interactive_timeline, 'add_track'):
            self.interactive_timeline.add_track(track_data)
    
    def closeEvent(self, event):
        """Wird beim Schließen der Anwendung aufgerufen"""
        # Stoppe laufende Analyse
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.cancel()
            self.analysis_worker.wait()
        
        # Speichere Einstellungen
        self.save_settings()
        
        event.accept()

def main():
    """Hauptfunktion"""
    app = QApplication(sys.argv)
    
    # Setze Anwendungsmetadaten
    app.setApplicationName("DJ Audio-Analyse-Tool Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("DJTool")
    app.setOrganizationDomain("djtool.com")
    
    # Setze Anwendungsstil
    app.setStyle("Fusion")
    
    # Erstelle und zeige Hauptfenster
    window = MainWindow()
    window.show()
    
    # Starte Event-Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()