"""Settings Dialog - Anwendungseinstellungen und Konfiguration"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QLineEdit, QFileDialog, QTabWidget, QWidget,
    QSlider, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import json
import os


class SettingsDialog(QDialog):
    """Dialog für Anwendungseinstellungen"""
    
    settings_changed = pyqtSignal(dict)  # Signal wenn Einstellungen geändert werden
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings - Audio Analysis Tool")
        self.setModal(True)
        self.resize(600, 500)
        
        self.settings = {}
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup der Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        
        # Audio-Einstellungen Tab
        self.setup_audio_tab()
        
        # Analyse-Einstellungen Tab
        self.setup_analysis_tab()
        
        # GUI-Einstellungen Tab
        self.setup_gui_tab()
        
        # Export-Einstellungen Tab
        self.setup_export_tab()
        
        # Cache-Einstellungen Tab
        self.setup_cache_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Button Box
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        
        layout.addWidget(button_box)
        
    def setup_audio_tab(self):
        """Setup Audio-Einstellungen Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Audio-Parameter
        audio_group = QGroupBox("Audio Processing")
        audio_layout = QGridLayout(audio_group)
        
        audio_layout.addWidget(QLabel("Sample Rate:"), 0, 0)
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["22050", "44100", "48000"])
        self.sample_rate_combo.setCurrentText("22050")
        audio_layout.addWidget(self.sample_rate_combo, 0, 1)
        
        audio_layout.addWidget(QLabel("Hop Length:"), 1, 0)
        self.hop_length_spin = QSpinBox()
        self.hop_length_spin.setRange(256, 2048)
        self.hop_length_spin.setValue(512)
        audio_layout.addWidget(self.hop_length_spin, 1, 1)
        
        audio_layout.addWidget(QLabel("Analysis Duration (sec):"), 2, 0)
        self.analysis_duration_spin = QSpinBox()
        self.analysis_duration_spin.setRange(30, 300)
        self.analysis_duration_spin.setValue(120)
        audio_layout.addWidget(self.analysis_duration_spin, 2, 1)
        
        layout.addWidget(audio_group)
        
        # Unterstützte Formate
        formats_group = QGroupBox("Supported Formats")
        formats_layout = QVBoxLayout(formats_group)
        
        self.format_checkboxes = {}
        formats = ["mp3", "wav", "flac", "m4a", "aac", "ogg"]
        
        for fmt in formats:
            checkbox = QCheckBox(fmt.upper())
            checkbox.setChecked(fmt in ["mp3", "wav", "flac"])  # Default
            self.format_checkboxes[fmt] = checkbox
            formats_layout.addWidget(checkbox)
        
        layout.addWidget(formats_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Audio")
        
    def setup_analysis_tab(self):
        """Setup Analyse-Einstellungen Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Feature-Extraktion
        features_group = QGroupBox("Feature Extraction")
        features_layout = QVBoxLayout(features_group)
        
        self.feature_checkboxes = {}
        features = [
            ("chroma", "Chroma Features (Key Detection)"),
            ("mfcc", "MFCC (Timbre Analysis)"),
            ("spectral_centroid", "Spectral Centroid (Brightness)"),
            ("rms", "RMS Energy"),
            ("zero_crossing_rate", "Zero Crossing Rate"),
            ("tempo", "Tempo/BPM Detection")
        ]
        
        for key, label in features:
            checkbox = QCheckBox(label)
            checkbox.setChecked(True)  # Alle standardmäßig aktiviert
            self.feature_checkboxes[key] = checkbox
            features_layout.addWidget(checkbox)
        
        layout.addWidget(features_group)
        
        # Analyse-Parameter
        params_group = QGroupBox("Analysis Parameters")
        params_layout = QGridLayout(params_group)
        
        params_layout.addWidget(QLabel("BPM Range Min:"), 0, 0)
        self.bpm_min_spin = QSpinBox()
        self.bpm_min_spin.setRange(60, 200)
        self.bpm_min_spin.setValue(80)
        params_layout.addWidget(self.bpm_min_spin, 0, 1)
        
        params_layout.addWidget(QLabel("BPM Range Max:"), 0, 2)
        self.bpm_max_spin = QSpinBox()
        self.bpm_max_spin.setRange(60, 200)
        self.bpm_max_spin.setValue(180)
        params_layout.addWidget(self.bpm_max_spin, 0, 3)
        
        params_layout.addWidget(QLabel("Key Detection Threshold:"), 1, 0)
        self.key_threshold_spin = QDoubleSpinBox()
        self.key_threshold_spin.setRange(0.1, 1.0)
        self.key_threshold_spin.setSingleStep(0.1)
        self.key_threshold_spin.setValue(0.3)
        params_layout.addWidget(self.key_threshold_spin, 1, 1)
        
        layout.addWidget(params_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Analysis")
        
    def setup_gui_tab(self):
        """Setup GUI-Einstellungen Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme-Einstellungen
        theme_group = QGroupBox("Theme & Appearance")
        theme_layout = QGridLayout(theme_group)
        
        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        self.theme_combo.setCurrentText("Dark")
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        theme_layout.addWidget(QLabel("Font Size:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(10)
        theme_layout.addWidget(self.font_size_spin, 1, 1)
        
        layout.addWidget(theme_group)
        
        # Tabellen-Einstellungen
        table_group = QGroupBox("Table Settings")
        table_layout = QVBoxLayout(table_group)
        
        self.show_spectogram_check = QCheckBox("Show Spectogram Preview")
        self.show_spectogram_check.setChecked(False)
        table_layout.addWidget(self.show_spectogram_check)
        
        self.auto_refresh_check = QCheckBox("Auto-refresh Track List")
        self.auto_refresh_check.setChecked(True)
        table_layout.addWidget(self.auto_refresh_check)
        
        layout.addWidget(table_group)
        
        # Performance-Einstellungen
        perf_group = QGroupBox("Performance")
        perf_layout = QGridLayout(perf_group)
        
        perf_layout.addWidget(QLabel("Max Parallel Analysis:"), 0, 0)
        self.max_workers_spin = QSpinBox()
        self.max_workers_spin.setRange(1, 8)
        self.max_workers_spin.setValue(2)
        perf_layout.addWidget(self.max_workers_spin, 0, 1)
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "GUI")
        
    def setup_export_tab(self):
        """Setup Export-Einstellungen Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Export-Pfade
        paths_group = QGroupBox("Export Paths")
        paths_layout = QGridLayout(paths_group)
        
        paths_layout.addWidget(QLabel("Default Export Directory:"), 0, 0)
        self.export_dir_edit = QLineEdit()
        self.export_dir_edit.setText(os.path.expanduser("~/Music/Playlists"))
        paths_layout.addWidget(self.export_dir_edit, 0, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_export_dir)
        paths_layout.addWidget(browse_btn, 0, 2)
        
        layout.addWidget(paths_group)
        
        # Export-Formate
        formats_group = QGroupBox("Export Formats")
        formats_layout = QVBoxLayout(formats_group)
        
        self.export_format_checkboxes = {}
        export_formats = [
            ("m3u", "M3U Playlist"),
            ("m3u8", "M3U8 Playlist (UTF-8)"),
            ("xml", "Rekordbox XML"),
            ("json", "JSON Metadata")
        ]
        
        for key, label in export_formats:
            checkbox = QCheckBox(label)
            checkbox.setChecked(key in ["m3u", "xml"])  # Default
            self.export_format_checkboxes[key] = checkbox
            formats_layout.addWidget(checkbox)
        
        layout.addWidget(formats_group)
        
        # Export-Optionen
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        self.relative_paths_check = QCheckBox("Use Relative Paths")
        self.relative_paths_check.setChecked(True)
        options_layout.addWidget(self.relative_paths_check)
        
        self.include_metadata_check = QCheckBox("Include Extended Metadata")
        self.include_metadata_check.setChecked(True)
        options_layout.addWidget(self.include_metadata_check)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Export")
        
    def setup_cache_tab(self):
        """Setup Cache-Einstellungen Tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cache-Einstellungen
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QGridLayout(cache_group)
        
        cache_layout.addWidget(QLabel("Cache Directory:"), 0, 0)
        self.cache_dir_edit = QLineEdit()
        self.cache_dir_edit.setText("data/cache")
        cache_layout.addWidget(self.cache_dir_edit, 0, 1)
        
        cache_browse_btn = QPushButton("Browse...")
        cache_browse_btn.clicked.connect(self.browse_cache_dir)
        cache_layout.addWidget(cache_browse_btn, 0, 2)
        
        cache_layout.addWidget(QLabel("Max Cache Size (MB):"), 1, 0)
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 10000)
        self.cache_size_spin.setValue(1000)
        cache_layout.addWidget(self.cache_size_spin, 1, 1)
        
        cache_layout.addWidget(QLabel("Cache Cleanup Days:"), 2, 0)
        self.cache_cleanup_spin = QSpinBox()
        self.cache_cleanup_spin.setRange(1, 365)
        self.cache_cleanup_spin.setValue(30)
        cache_layout.addWidget(self.cache_cleanup_spin, 2, 1)
        
        layout.addWidget(cache_group)
        
        # Cache-Aktionen
        actions_group = QGroupBox("Cache Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        clear_cache_btn = QPushButton("Clear All Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        actions_layout.addWidget(clear_cache_btn)
        
        optimize_cache_btn = QPushButton("Optimize Cache")
        optimize_cache_btn.clicked.connect(self.optimize_cache)
        actions_layout.addWidget(optimize_cache_btn)
        
        layout.addWidget(actions_group)
        
        # Cache-Info
        info_group = QGroupBox("Cache Information")
        info_layout = QVBoxLayout(info_group)
        
        self.cache_info_label = QLabel("Loading cache information...")
        self.cache_info_label.setStyleSheet("color: #888; font-style: italic;")
        info_layout.addWidget(self.cache_info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Cache")
        
    def browse_export_dir(self):
        """Öffnet Dialog zur Auswahl des Export-Verzeichnisses"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", self.export_dir_edit.text()
        )
        if directory:
            self.export_dir_edit.setText(directory)
    
    def browse_cache_dir(self):
        """Öffnet Dialog zur Auswahl des Cache-Verzeichnisses"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Cache Directory", self.cache_dir_edit.text()
        )
        if directory:
            self.cache_dir_edit.setText(directory)
    
    def clear_cache(self):
        """Löscht den gesamten Cache"""
        # Hier würde die Cache-Löschung implementiert
        print("Cache cleared")
        self.update_cache_info()
    
    def optimize_cache(self):
        """Optimiert den Cache"""
        # Hier würde die Cache-Optimierung implementiert
        print("Cache optimized")
        self.update_cache_info()
    
    def update_cache_info(self):
        """Aktualisiert die Cache-Informationen"""
        # Hier würden echte Cache-Statistiken geladen
        self.cache_info_label.setText(
            "Cache Size: 245 MB\n"
            "Cached Files: 1,234\n"
            "Last Cleanup: 5 days ago"
        )
    
    def load_settings(self):
        """Lädt die Einstellungen aus der Datei"""
        settings_file = "config/settings.json"
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    self.settings = json.load(f)
                self.apply_settings_to_ui()
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        self.update_cache_info()
    
    def apply_settings_to_ui(self):
        """Wendet geladene Einstellungen auf die UI an"""
        # Hier würden die Einstellungen auf die UI-Elemente angewendet
        pass
    
    def collect_settings(self):
        """Sammelt alle Einstellungen aus der UI"""
        # Audio-Einstellungen
        audio_settings = {
            'sample_rate': int(self.sample_rate_combo.currentText()),
            'hop_length': self.hop_length_spin.value(),
            'analysis_duration': self.analysis_duration_spin.value(),
            'supported_formats': [fmt for fmt, cb in self.format_checkboxes.items() if cb.isChecked()]
        }
        
        # Analyse-Einstellungen
        analysis_settings = {
            'features': [feat for feat, cb in self.feature_checkboxes.items() if cb.isChecked()],
            'bpm_range': [self.bpm_min_spin.value(), self.bpm_max_spin.value()],
            'key_threshold': self.key_threshold_spin.value()
        }
        
        # GUI-Einstellungen
        gui_settings = {
            'theme': self.theme_combo.currentText(),
            'font_size': self.font_size_spin.value(),
            'show_spectogram': self.show_spectogram_check.isChecked(),
            'auto_refresh': self.auto_refresh_check.isChecked(),
            'max_workers': self.max_workers_spin.value()
        }
        
        # Export-Einstellungen
        export_settings = {
            'default_directory': self.export_dir_edit.text(),
            'formats': [fmt for fmt, cb in self.export_format_checkboxes.items() if cb.isChecked()],
            'relative_paths': self.relative_paths_check.isChecked(),
            'include_metadata': self.include_metadata_check.isChecked()
        }
        
        # Cache-Einstellungen
        cache_settings = {
            'directory': self.cache_dir_edit.text(),
            'max_size_mb': self.cache_size_spin.value(),
            'cleanup_days': self.cache_cleanup_spin.value()
        }
        
        return {
            'audio': audio_settings,
            'analysis': analysis_settings,
            'gui': gui_settings,
            'export': export_settings,
            'cache': cache_settings
        }
    
    def save_settings(self):
        """Speichert die Einstellungen in eine Datei"""
        settings_file = "config/settings.json"
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def apply_settings(self):
        """Wendet die Einstellungen an ohne Dialog zu schließen"""
        self.settings = self.collect_settings()
        self.save_settings()
        self.settings_changed.emit(self.settings)
    
    def accept_settings(self):
        """Akzeptiert und speichert die Einstellungen"""
        self.apply_settings()
        self.accept()
    
    def get_settings(self):
        """Gibt die aktuellen Einstellungen zurück"""
        return self.settings.copy()