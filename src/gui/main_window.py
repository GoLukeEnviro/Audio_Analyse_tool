import sys
import os
import json
from typing import List, Dict, Optional
from pathlib import Path
import threading
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QFileDialog, QProgressBar, QTextEdit, QSlider, QComboBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout, QSplitter,
    QHeaderView, QAbstractItemView, QMessageBox, QCheckBox,
    QLineEdit, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

# Import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.audio_analysis.analyzer import AudioAnalyzer
from src.playlist_engine.generator import PlaylistGenerator
from src.export.exporter import PlaylistExporter

class AnalysisWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, directory: str):
        super().__init__()
        self.directory = directory
        self.analyzer = AudioAnalyzer()
    
    def run(self):
        try:
            def progress_callback(message):
                self.progress.emit(message)
            
            results = self.analyzer.analyze_directory(self.directory, progress_callback)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tracks = []
        self.current_playlist = None
        self.analyzer = AudioAnalyzer()
        self.playlist_generator = PlaylistGenerator()
        self.exporter = PlaylistExporter()
        
        self.init_ui()
        self.apply_dark_theme()
        self.load_cached_tracks()
    
    def init_ui(self):
        self.setWindowTitle('Audio Analysis Tool - DJ Playlist Generator')
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_analysis_tab()
        self.create_playlist_tab()
        self.create_export_tab()
        self.create_settings_tab()
    
    def create_dashboard_tab(self):
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)
        
        # Statistics section
        stats_group = QGroupBox("Library Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.total_tracks_label = QLabel("Total Tracks: 0")
        self.avg_bpm_label = QLabel("Average BPM: 0")
        self.total_duration_label = QLabel("Total Duration: 0:00")
        
        stats_layout.addWidget(self.total_tracks_label, 0, 0)
        stats_layout.addWidget(self.avg_bpm_label, 0, 1)
        stats_layout.addWidget(self.total_duration_label, 0, 2)
        
        layout.addWidget(stats_group)
        
        # Track table
        self.track_table = QTableWidget()
        self.track_table.setColumnCount(8)
        self.track_table.setHorizontalHeaderLabels([
            'Filename', 'BPM', 'Key', 'Camelot', 'Energy', 'Duration', 'Mood', 'Path'
        ])
        
        # Configure table
        header = self.track_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        self.track_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.track_table.setAlternatingRowColors(True)
        self.track_table.setSortingEnabled(True)
        
        layout.addWidget(self.track_table)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Library")
        self.refresh_btn.clicked.connect(self.refresh_library)
        
        self.analyze_folder_btn = QPushButton("Analyze Folder")
        self.analyze_folder_btn.clicked.connect(self.select_analysis_folder)
        
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.analyze_folder_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(dashboard, "Dashboard")
    
    def create_analysis_tab(self):
        analysis = QWidget()
        layout = QVBoxLayout(analysis)
        
        # Analysis controls
        controls_group = QGroupBox("Analysis Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.select_folder_btn = QPushButton("Select Music Folder")
        self.select_folder_btn.clicked.connect(self.select_analysis_folder)
        
        self.start_analysis_btn = QPushButton("Start Analysis")
        self.start_analysis_btn.clicked.connect(self.start_analysis)
        self.start_analysis_btn.setEnabled(False)
        
        controls_layout.addWidget(self.select_folder_btn)
        controls_layout.addWidget(self.start_analysis_btn)
        controls_layout.addStretch()
        
        layout.addWidget(controls_group)
        
        # Progress section
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(200)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_text)
        
        layout.addWidget(progress_group)
        
        # Results section
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            'Filename', 'Status', 'BPM', 'Key', 'Energy', 'Error'
        ])
        
        results_layout.addWidget(self.results_table)
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(analysis, "Analysis Center")
    
    def create_playlist_tab(self):
        playlist = QWidget()
        layout = QHBoxLayout(playlist)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(350)
        
        # Preset selection
        preset_group = QGroupBox("Presets")
        preset_layout = QVBoxLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['Custom', 'Push-Push', 'Dark', 'Euphoric', 'Experimental', 'Driving'])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        
        self.load_preset_btn = QPushButton("Load Preset")
        self.load_preset_btn.clicked.connect(self.load_preset)
        
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(self.load_preset_btn)
        
        left_layout.addWidget(preset_group)
        
        # BPM Range
        bpm_group = QGroupBox("BPM Range")
        bpm_layout = QGridLayout(bpm_group)
        
        bpm_layout.addWidget(QLabel("Min BPM:"), 0, 0)
        self.bpm_min_spin = QSpinBox()
        self.bpm_min_spin.setRange(60, 200)
        self.bpm_min_spin.setValue(120)
        bpm_layout.addWidget(self.bpm_min_spin, 0, 1)
        
        bpm_layout.addWidget(QLabel("Max BPM:"), 1, 0)
        self.bpm_max_spin = QSpinBox()
        self.bpm_max_spin.setRange(60, 200)
        self.bpm_max_spin.setValue(140)
        bpm_layout.addWidget(self.bpm_max_spin, 1, 1)
        
        left_layout.addWidget(bpm_group)
        
        # Energy and Mood
        mood_group = QGroupBox("Mood & Energy")
        mood_layout = QGridLayout(mood_group)
        
        mood_layout.addWidget(QLabel("Min Energy:"), 0, 0)
        self.energy_slider = QSlider(Qt.Horizontal)
        self.energy_slider.setRange(0, 100)
        self.energy_slider.setValue(50)
        self.energy_label = QLabel("0.5")
        mood_layout.addWidget(self.energy_slider, 0, 1)
        mood_layout.addWidget(self.energy_label, 0, 2)
        
        self.energy_slider.valueChanged.connect(
            lambda v: self.energy_label.setText(f"{v/100:.1f}")
        )
        
        # Mood checkboxes
        self.euphoric_check = QCheckBox("Euphoric")
        self.dark_check = QCheckBox("Dark")
        self.driving_check = QCheckBox("Driving")
        self.experimental_check = QCheckBox("Experimental")
        
        mood_layout.addWidget(self.euphoric_check, 1, 0)
        mood_layout.addWidget(self.dark_check, 1, 1)
        mood_layout.addWidget(self.driving_check, 2, 0)
        mood_layout.addWidget(self.experimental_check, 2, 1)
        
        left_layout.addWidget(mood_group)
        
        # Sorting options
        sort_group = QGroupBox("Sorting")
        sort_layout = QVBoxLayout(sort_group)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            'BPM Ascending', 'BPM Descending', 'Energy Ascending', 
            'Energy Descending', 'Harmonic Flow', 'Dark Mood', 'Euphoric Mood'
        ])
        
        sort_layout.addWidget(self.sort_combo)
        left_layout.addWidget(sort_group)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Playlist")
        self.generate_btn.clicked.connect(self.generate_playlist)
        left_layout.addWidget(self.generate_btn)
        
        left_layout.addStretch()
        
        # Right panel - Playlist preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Playlist info
        info_group = QGroupBox("Playlist Information")
        info_layout = QGridLayout(info_group)
        
        self.playlist_tracks_label = QLabel("Tracks: 0")
        self.playlist_duration_label = QLabel("Duration: 0:00")
        self.playlist_bpm_label = QLabel("Avg BPM: 0")
        
        info_layout.addWidget(self.playlist_tracks_label, 0, 0)
        info_layout.addWidget(self.playlist_duration_label, 0, 1)
        info_layout.addWidget(self.playlist_bpm_label, 0, 2)
        
        right_layout.addWidget(info_group)
        
        # Playlist table
        self.playlist_table = QTableWidget()
        self.playlist_table.setColumnCount(7)
        self.playlist_table.setHorizontalHeaderLabels([
            'Track', 'BPM', 'Key', 'Camelot', 'Energy', 'Duration', 'Mood Score'
        ])
        
        playlist_header = self.playlist_table.horizontalHeader()
        playlist_header.setSectionResizeMode(0, QHeaderView.Stretch)
        
        right_layout.addWidget(self.playlist_table)
        
        # Add panels to splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 1050])
        
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(playlist, "Playlist Generator")
    
    def create_export_tab(self):
        export = QWidget()
        layout = QVBoxLayout(export)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QGridLayout(options_group)
        
        options_layout.addWidget(QLabel("Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(['M3U Playlist', 'Rekordbox XML'])
        options_layout.addWidget(self.format_combo, 0, 1)
        
        options_layout.addWidget(QLabel("Output Directory:"), 1, 0)
        self.output_path_edit = QLineEdit()
        self.browse_output_btn = QPushButton("Browse")
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        
        options_layout.addWidget(self.output_path_edit, 1, 1)
        options_layout.addWidget(self.browse_output_btn, 1, 2)
        
        options_layout.addWidget(QLabel("Playlist Name:"), 2, 0)
        self.playlist_name_edit = QLineEdit("Generated Playlist")
        options_layout.addWidget(self.playlist_name_edit, 2, 1)
        
        layout.addWidget(options_group)
        
        # Export buttons
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export Current Playlist")
        self.export_btn.clicked.connect(self.export_playlist)
        self.export_btn.setEnabled(False)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Export log
        log_group = QGroupBox("Export Log")
        log_layout = QVBoxLayout(log_group)
        
        self.export_log = QTextEdit()
        self.export_log.setMaximumHeight(200)
        log_layout.addWidget(self.export_log)
        
        layout.addWidget(log_group)
        layout.addStretch()
        
        self.tab_widget.addTab(export, "Export Manager")
    
    def create_settings_tab(self):
        settings = QWidget()
        layout = QVBoxLayout(settings)
        
        # Cache settings
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QVBoxLayout(cache_group)
        
        cache_info = QLabel(f"Cache Directory: {self.analyzer.cache_dir}")
        cache_layout.addWidget(cache_info)
        
        clear_cache_btn = QPushButton("Clear Analysis Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        cache_layout.addWidget(clear_cache_btn)
        
        layout.addWidget(cache_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(settings, "Settings")
    
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #2d2d2d;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0066cc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2d2d2d;
                border-radius: 4px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0080ff;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #333333;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #0066cc;
                color: white;
                padding: 4px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QComboBox, QSpinBox, QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 2px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 8px;
                background: #2d2d2d;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0066cc;
                border: 1px solid #555555;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 4px;
            }
        """)
    
    def select_analysis_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            self.analysis_folder = folder
            self.start_analysis_btn.setEnabled(True)
            self.progress_text.append(f"Selected folder: {folder}")
    
    def start_analysis(self):
        if not hasattr(self, 'analysis_folder'):
            return
        
        self.start_analysis_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_text.clear()
        
        self.analysis_worker = AnalysisWorker(self.analysis_folder)
        self.analysis_worker.progress.connect(self.update_analysis_progress)
        self.analysis_worker.finished.connect(self.analysis_finished)
        self.analysis_worker.error.connect(self.analysis_error)
        self.analysis_worker.start()
    
    def update_analysis_progress(self, message):
        self.progress_text.append(message)
        # Scroll to bottom
        cursor = self.progress_text.textCursor()
        cursor.movePosition(cursor.End)
        self.progress_text.setTextCursor(cursor)
    
    def analysis_finished(self, results):
        self.tracks.extend(results)
        self.update_track_table()
        self.update_results_table(results)
        self.update_statistics()
        self.start_analysis_btn.setEnabled(True)
        self.progress_text.append(f"\nAnalysis completed! Processed {len(results)} files.")
        
        # Save tracks to cache
        self.save_tracks_cache()
    
    def analysis_error(self, error_message):
        self.progress_text.append(f"Error: {error_message}")
        self.start_analysis_btn.setEnabled(True)
    
    def update_track_table(self):
        self.track_table.setRowCount(len(self.tracks))
        
        for row, track in enumerate(self.tracks):
            if 'error' in track:
                continue
            
            self.track_table.setItem(row, 0, QTableWidgetItem(track.get('filename', '')))
            self.track_table.setItem(row, 1, QTableWidgetItem(f"{track.get('bpm', 0):.1f}"))
            self.track_table.setItem(row, 2, QTableWidgetItem(track.get('key', '')))
            self.track_table.setItem(row, 3, QTableWidgetItem(track.get('camelot', '')))
            self.track_table.setItem(row, 4, QTableWidgetItem(f"{track.get('energy', 0):.2f}"))
            
            duration = track.get('duration', 0)
            duration_str = f"{int(duration//60)}:{int(duration%60):02d}"
            self.track_table.setItem(row, 5, QTableWidgetItem(duration_str))
            
            mood = track.get('mood', {})
            dominant_mood = max(mood.items(), key=lambda x: x[1])[0] if mood else 'Unknown'
            self.track_table.setItem(row, 6, QTableWidgetItem(dominant_mood))
            
            self.track_table.setItem(row, 7, QTableWidgetItem(track.get('file_path', '')))
    
    def update_results_table(self, results):
        self.results_table.setRowCount(len(results))
        
        for row, track in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(track.get('filename', '')))
            
            if 'error' in track:
                self.results_table.setItem(row, 1, QTableWidgetItem('Error'))
                self.results_table.setItem(row, 5, QTableWidgetItem(track['error']))
            else:
                self.results_table.setItem(row, 1, QTableWidgetItem('Success'))
                self.results_table.setItem(row, 2, QTableWidgetItem(f"{track.get('bpm', 0):.1f}"))
                self.results_table.setItem(row, 3, QTableWidgetItem(track.get('key', '')))
                self.results_table.setItem(row, 4, QTableWidgetItem(f"{track.get('energy', 0):.2f}"))
    
    def update_statistics(self):
        valid_tracks = [t for t in self.tracks if 'error' not in t]
        
        total_tracks = len(valid_tracks)
        avg_bpm = sum(t.get('bpm', 0) for t in valid_tracks) / total_tracks if total_tracks > 0 else 0
        total_duration = sum(t.get('duration', 0) for t in valid_tracks)
        
        self.total_tracks_label.setText(f"Total Tracks: {total_tracks}")
        self.avg_bpm_label.setText(f"Average BPM: {avg_bpm:.1f}")
        
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        self.total_duration_label.setText(f"Total Duration: {hours}:{minutes:02d}")
    
    def on_preset_changed(self, preset_name):
        if preset_name == 'Custom':
            return
        
        presets = self.playlist_generator.presets
        if preset_name.lower().replace('-', '_') in presets:
            self.load_preset()
    
    def load_preset(self):
        preset_name = self.preset_combo.currentText()
        if preset_name == 'Custom':
            return
        
        preset_key = preset_name.lower().replace('-', '_')
        presets = self.playlist_generator.presets
        
        if preset_key in presets:
            preset = presets[preset_key]
            
            # Update UI with preset values
            self.bpm_min_spin.setValue(preset['bpm_range'][0])
            self.bpm_max_spin.setValue(preset['bpm_range'][1])
            self.energy_slider.setValue(int(preset['energy_min'] * 100))
            
            # Update mood checkboxes
            mood_weights = preset['mood_weights']
            self.euphoric_check.setChecked(mood_weights.get('euphoric', 0) > 0.5)
            self.dark_check.setChecked(mood_weights.get('dark', 0) > 0.5)
            self.driving_check.setChecked(mood_weights.get('driving', 0) > 0.5)
            self.experimental_check.setChecked(mood_weights.get('experimental', 0) > 0.5)
            
            # Update sort method
            sort_mapping = {
                'bpm_ascending': 'BPM Ascending',
                'energy_ascending': 'Energy Ascending',
                'mood_dark': 'Dark Mood',
                'experimental': 'Experimental'
            }
            sort_text = sort_mapping.get(preset['sort_by'], 'BPM Ascending')
            index = self.sort_combo.findText(sort_text)
            if index >= 0:
                self.sort_combo.setCurrentIndex(index)
    
    def generate_playlist(self):
        if not self.tracks:
            QMessageBox.warning(self, "Warning", "No tracks available. Please analyze some music first.")
            return
        
        # Build rules from UI
        rules = {
            'bpm_min': self.bpm_min_spin.value(),
            'bpm_max': self.bpm_max_spin.value(),
            'energy_min': self.energy_slider.value() / 100.0,
            'mood_weights': {},
            'mood_threshold': 0.3
        }
        
        # Add mood weights based on checkboxes
        if self.euphoric_check.isChecked():
            rules['mood_weights']['euphoric'] = 0.8
        if self.dark_check.isChecked():
            rules['mood_weights']['dark'] = 0.8
        if self.driving_check.isChecked():
            rules['mood_weights']['driving'] = 0.8
        if self.experimental_check.isChecked():
            rules['mood_weights']['experimental'] = 0.8
        
        # Map sort method
        sort_mapping = {
            'BPM Ascending': 'bpm_ascending',
            'BPM Descending': 'bpm_descending',
            'Energy Ascending': 'energy_ascending',
            'Energy Descending': 'energy_descending',
            'Harmonic Flow': 'harmonic_flow',
            'Dark Mood': 'mood_dark',
            'Euphoric Mood': 'mood_euphoric'
        }
        rules['sort_by'] = sort_mapping.get(self.sort_combo.currentText(), 'bpm_ascending')
        
        # Generate playlist
        self.current_playlist = self.playlist_generator.generate_playlist(self.tracks, rules)
        
        if 'error' in self.current_playlist:
            QMessageBox.warning(self, "Warning", self.current_playlist['error'])
            return
        
        # Update playlist table
        self.update_playlist_table()
        self.export_btn.setEnabled(True)
    
    def update_playlist_table(self):
        if not self.current_playlist:
            return
        
        tracks = self.current_playlist['tracks']
        self.playlist_table.setRowCount(len(tracks))
        
        for row, track in enumerate(tracks):
            filename = os.path.splitext(track.get('filename', ''))[0]
            self.playlist_table.setItem(row, 0, QTableWidgetItem(filename))
            self.playlist_table.setItem(row, 1, QTableWidgetItem(f"{track.get('bpm', 0):.1f}"))
            self.playlist_table.setItem(row, 2, QTableWidgetItem(track.get('key', '')))
            self.playlist_table.setItem(row, 3, QTableWidgetItem(track.get('camelot', '')))
            self.playlist_table.setItem(row, 4, QTableWidgetItem(f"{track.get('energy', 0):.2f}"))
            
            duration = track.get('duration', 0)
            duration_str = f"{int(duration//60)}:{int(duration%60):02d}"
            self.playlist_table.setItem(row, 5, QTableWidgetItem(duration_str))
            
            # Calculate mood score
            mood = track.get('mood', {})
            mood_score = sum(mood.values()) / len(mood) if mood else 0
            self.playlist_table.setItem(row, 6, QTableWidgetItem(f"{mood_score:.2f}"))
        
        # Update playlist info
        total_tracks = self.current_playlist['total_tracks']
        total_duration = self.current_playlist['total_duration']
        avg_bpm = self.current_playlist['avg_bpm']
        
        self.playlist_tracks_label.setText(f"Tracks: {total_tracks}")
        
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        self.playlist_duration_label.setText(f"Duration: {hours}:{minutes:02d}")
        
        self.playlist_bpm_label.setText(f"Avg BPM: {avg_bpm:.1f}")
    
    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_path_edit.setText(directory)
    
    def export_playlist(self):
        if not self.current_playlist:
            QMessageBox.warning(self, "Warning", "No playlist to export. Please generate a playlist first.")
            return
        
        output_dir = self.output_path_edit.text()
        if not output_dir:
            QMessageBox.warning(self, "Warning", "Please select an output directory.")
            return
        
        playlist_name = self.playlist_name_edit.text() or "Generated Playlist"
        format_type = 'm3u' if 'M3U' in self.format_combo.currentText() else 'rekordbox_xml'
        
        # Prepare playlist data
        export_playlist = self.current_playlist.copy()
        export_playlist['name'] = playlist_name
        
        # Generate filename
        safe_name = self.exporter._sanitize_filename(playlist_name)
        if format_type == 'm3u':
            output_file = os.path.join(output_dir, f"{safe_name}.m3u")
        else:
            output_file = os.path.join(output_dir, f"{safe_name}.xml")
        
        # Export
        success = self.exporter.export_playlist(export_playlist, output_file, format_type)
        
        if success:
            self.export_log.append(f"Successfully exported '{playlist_name}' to {output_file}")
            QMessageBox.information(self, "Success", f"Playlist exported successfully to:\n{output_file}")
        else:
            self.export_log.append(f"Failed to export '{playlist_name}'")
            QMessageBox.critical(self, "Error", "Failed to export playlist.")
    
    def refresh_library(self):
        self.load_cached_tracks()
        self.update_track_table()
        self.update_statistics()
    
    def clear_cache(self):
        reply = QMessageBox.question(self, "Clear Cache", 
                                   "Are you sure you want to clear the analysis cache?\n"
                                   "This will remove all cached analysis results.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                import shutil
                if self.analyzer.cache_dir.exists():
                    shutil.rmtree(self.analyzer.cache_dir)
                    self.analyzer.cache_dir.mkdir(parents=True, exist_ok=True)
                
                self.tracks.clear()
                self.update_track_table()
                self.update_statistics()
                
                QMessageBox.information(self, "Success", "Cache cleared successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache: {e}")
    
    def save_tracks_cache(self):
        try:
            cache_file = Path("data/tracks_cache.json")
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(cache_file, 'w') as f:
                json.dump(self.tracks, f, indent=2)
        except Exception:
            pass
    
    def load_cached_tracks(self):
        try:
            cache_file = Path("data/tracks_cache.json")
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    self.tracks = json.load(f)
        except Exception:
            self.tracks = []

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better dark theme support
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()