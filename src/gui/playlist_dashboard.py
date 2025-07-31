"""Playlist Dashboard Widget - Konfiguration und Verwaltung von Playlist-Regeln"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QSlider, QTextEdit, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import json
import os


class PlaylistDashboard(QWidget):
    """Widget für Playlist-Konfiguration und -Verwaltung"""
    
    generate_playlist = pyqtSignal(dict)  # Signal für Playlist-Generierung
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_rules = {}
        self.setup_ui()
        self.load_default_rules()
        
    def setup_ui(self):
        """Setup der Benutzeroberfläche"""
        layout = QHBoxLayout(self)
        
        # Linke Seite - Regel-Konfiguration
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Preset-Auswahl
        preset_group = QGroupBox("Presets")
        preset_layout = QHBoxLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom", "Push-Push", "Dark", "Euphoric", "Experimental", "Driving"
        ])
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        preset_layout.addWidget(QLabel("Preset:"))
        preset_layout.addWidget(self.preset_combo)
        
        save_preset_btn = QPushButton("Save Preset")
        save_preset_btn.clicked.connect(self.save_custom_preset)
        preset_layout.addWidget(save_preset_btn)
        
        left_layout.addWidget(preset_group)
        
        # BPM-Regeln
        bpm_group = QGroupBox("BPM Rules")
        bpm_layout = QGridLayout(bpm_group)
        
        bpm_layout.addWidget(QLabel("Min BPM:"), 0, 0)
        self.min_bpm_spin = QSpinBox()
        self.min_bpm_spin.setRange(60, 200)
        self.min_bpm_spin.setValue(120)
        self.min_bpm_spin.valueChanged.connect(self.update_rules)
        bpm_layout.addWidget(self.min_bpm_spin, 0, 1)
        
        bpm_layout.addWidget(QLabel("Max BPM:"), 0, 2)
        self.max_bpm_spin = QSpinBox()
        self.max_bpm_spin.setRange(60, 200)
        self.max_bpm_spin.setValue(140)
        self.max_bpm_spin.valueChanged.connect(self.update_rules)
        bpm_layout.addWidget(self.max_bpm_spin, 0, 3)
        
        bpm_layout.addWidget(QLabel("BPM Tolerance:"), 1, 0)
        self.bpm_tolerance_spin = QSpinBox()
        self.bpm_tolerance_spin.setRange(1, 20)
        self.bpm_tolerance_spin.setValue(5)
        self.bpm_tolerance_spin.valueChanged.connect(self.update_rules)
        bpm_layout.addWidget(self.bpm_tolerance_spin, 1, 1)
        
        left_layout.addWidget(bpm_group)
        
        # Energie-Regeln
        energy_group = QGroupBox("Energy Rules")
        energy_layout = QGridLayout(energy_group)
        
        energy_layout.addWidget(QLabel("Min Energy:"), 0, 0)
        self.min_energy_spin = QDoubleSpinBox()
        self.min_energy_spin.setRange(0.0, 1.0)
        self.min_energy_spin.setSingleStep(0.1)
        self.min_energy_spin.setValue(0.3)
        self.min_energy_spin.valueChanged.connect(self.update_rules)
        energy_layout.addWidget(self.min_energy_spin, 0, 1)
        
        energy_layout.addWidget(QLabel("Energy Flow:"), 1, 0)
        self.energy_flow_combo = QComboBox()
        self.energy_flow_combo.addItems(["Any", "Ascending", "Descending", "Stable"])
        self.energy_flow_combo.currentTextChanged.connect(self.update_rules)
        energy_layout.addWidget(self.energy_flow_combo, 1, 1)
        
        left_layout.addWidget(energy_group)
        
        # Stimmungs-Regeln
        mood_group = QGroupBox("Mood Rules")
        mood_layout = QVBoxLayout(mood_group)
        
        self.mood_checkboxes = {}
        moods = ["Euphoric", "Dark", "Driving", "Experimental"]
        
        for mood in moods:
            checkbox = QCheckBox(mood)
            checkbox.stateChanged.connect(self.update_rules)
            self.mood_checkboxes[mood] = checkbox
            mood_layout.addWidget(checkbox)
        
        left_layout.addWidget(mood_group)
        
        # Tonart-Regeln
        key_group = QGroupBox("Key Rules")
        key_layout = QGridLayout(key_group)
        
        key_layout.addWidget(QLabel("Key Compatibility:"), 0, 0)
        self.key_compat_combo = QComboBox()
        self.key_compat_combo.addItems(["Any", "Camelot Compatible", "Same Key"])
        self.key_compat_combo.currentTextChanged.connect(self.update_rules)
        key_layout.addWidget(self.key_compat_combo, 0, 1)
        
        key_layout.addWidget(QLabel("Start Key:"), 1, 0)
        self.start_key_combo = QComboBox()
        self.start_key_combo.addItem("Auto")
        self.start_key_combo.currentTextChanged.connect(self.update_rules)
        key_layout.addWidget(self.start_key_combo, 1, 1)
        
        left_layout.addWidget(key_group)
        
        # Sortier-Regeln
        sort_group = QGroupBox("Sorting Rules")
        sort_layout = QGridLayout(sort_group)
        
        sort_layout.addWidget(QLabel("Sort By:"), 0, 0)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["BPM", "Energy", "Mood", "Harmonic Flow", "Random"])
        self.sort_combo.currentTextChanged.connect(self.update_rules)
        sort_layout.addWidget(self.sort_combo, 0, 1)
        
        sort_layout.addWidget(QLabel("Max Tracks:"), 1, 0)
        self.max_tracks_spin = QSpinBox()
        self.max_tracks_spin.setRange(5, 100)
        self.max_tracks_spin.setValue(20)
        self.max_tracks_spin.valueChanged.connect(self.update_rules)
        sort_layout.addWidget(self.max_tracks_spin, 1, 1)
        
        left_layout.addWidget(sort_group)
        
        # Generate Button
        generate_btn = QPushButton("Generate Playlist")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        generate_btn.clicked.connect(self.on_generate_playlist)
        left_layout.addWidget(generate_btn)
        
        left_layout.addStretch()
        
        # Rechte Seite - Regel-Vorschau
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Regel-Vorschau
        preview_group = QGroupBox("Current Rules Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.rules_preview = QTextEdit()
        self.rules_preview.setReadOnly(True)
        self.rules_preview.setMaximumHeight(200)
        self.rules_preview.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        preview_layout.addWidget(self.rules_preview)
        
        right_layout.addWidget(preview_group)
        
        # Statistiken
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("No tracks loaded")
        self.stats_label.setStyleSheet("color: #888; font-style: italic;")
        stats_layout.addWidget(self.stats_label)
        
        right_layout.addWidget(stats_group)
        
        right_layout.addStretch()
        
        # Splitter für Layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 300])
        
        layout.addWidget(splitter)
        
    def load_default_rules(self):
        """Lädt Standard-Regeln"""
        self.update_rules()
        
    def update_rules(self):
        """Aktualisiert die aktuellen Regeln"""
        # Stimmungen sammeln
        selected_moods = []
        for mood, checkbox in self.mood_checkboxes.items():
            if checkbox.isChecked():
                selected_moods.append(mood)
        
        self.current_rules = {
            'bpm_min': self.min_bpm_spin.value(),
            'bpm_max': self.max_bpm_spin.value(),
            'bpm_tolerance': self.bpm_tolerance_spin.value(),
            'energy_min': self.min_energy_spin.value(),
            'energy_flow': self.energy_flow_combo.currentText(),
            'moods': selected_moods,
            'key_compatibility': self.key_compat_combo.currentText(),
            'start_key': self.start_key_combo.currentText(),
            'sort_by': self.sort_combo.currentText(),
            'max_tracks': self.max_tracks_spin.value()
        }
        
        self.update_preview()
        
    def update_preview(self):
        """Aktualisiert die Regel-Vorschau"""
        preview_text = "Current Playlist Rules:\n\n"
        
        preview_text += f"BPM Range: {self.current_rules['bpm_min']} - {self.current_rules['bpm_max']}\n"
        preview_text += f"BPM Tolerance: ±{self.current_rules['bpm_tolerance']}\n"
        preview_text += f"Min Energy: {self.current_rules['energy_min']:.1f}\n"
        preview_text += f"Energy Flow: {self.current_rules['energy_flow']}\n"
        
        if self.current_rules['moods']:
            preview_text += f"Moods: {', '.join(self.current_rules['moods'])}\n"
        else:
            preview_text += "Moods: Any\n"
        
        preview_text += f"Key Compatibility: {self.current_rules['key_compatibility']}\n"
        preview_text += f"Start Key: {self.current_rules['start_key']}\n"
        preview_text += f"Sort By: {self.current_rules['sort_by']}\n"
        preview_text += f"Max Tracks: {self.current_rules['max_tracks']}"
        
        self.rules_preview.setPlainText(preview_text)
        
    def load_preset(self, preset_name):
        """Lädt ein Preset"""
        if preset_name == "Custom":
            return
            
        presets = {
            "Push-Push": {
                'bpm_min': 128, 'bpm_max': 135, 'bpm_tolerance': 3,
                'energy_min': 0.7, 'energy_flow': 'Ascending',
                'moods': ['Driving', 'Euphoric'], 'key_compatibility': 'Camelot Compatible',
                'start_key': 'Auto', 'sort_by': 'Harmonic Flow', 'max_tracks': 15
            },
            "Dark": {
                'bpm_min': 120, 'bpm_max': 130, 'bpm_tolerance': 5,
                'energy_min': 0.4, 'energy_flow': 'Stable',
                'moods': ['Dark', 'Experimental'], 'key_compatibility': 'Same Key',
                'start_key': 'Auto', 'sort_by': 'Mood', 'max_tracks': 25
            },
            "Euphoric": {
                'bpm_min': 130, 'bpm_max': 140, 'bpm_tolerance': 4,
                'energy_min': 0.8, 'energy_flow': 'Ascending',
                'moods': ['Euphoric', 'Driving'], 'key_compatibility': 'Camelot Compatible',
                'start_key': 'Auto', 'sort_by': 'Energy', 'max_tracks': 20
            },
            "Experimental": {
                'bpm_min': 110, 'bpm_max': 150, 'bpm_tolerance': 10,
                'energy_min': 0.2, 'energy_flow': 'Any',
                'moods': ['Experimental', 'Dark'], 'key_compatibility': 'Any',
                'start_key': 'Auto', 'sort_by': 'Random', 'max_tracks': 30
            },
            "Driving": {
                'bpm_min': 125, 'bpm_max': 135, 'bpm_tolerance': 3,
                'energy_min': 0.6, 'energy_flow': 'Stable',
                'moods': ['Driving'], 'key_compatibility': 'Camelot Compatible',
                'start_key': 'Auto', 'sort_by': 'BPM', 'max_tracks': 20
            }
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            
            # UI aktualisieren
            self.min_bpm_spin.setValue(preset['bpm_min'])
            self.max_bpm_spin.setValue(preset['bpm_max'])
            self.bpm_tolerance_spin.setValue(preset['bpm_tolerance'])
            self.min_energy_spin.setValue(preset['energy_min'])
            self.energy_flow_combo.setCurrentText(preset['energy_flow'])
            
            # Stimmungen setzen
            for mood, checkbox in self.mood_checkboxes.items():
                checkbox.setChecked(mood in preset['moods'])
            
            self.key_compat_combo.setCurrentText(preset['key_compatibility'])
            self.start_key_combo.setCurrentText(preset['start_key'])
            self.sort_combo.setCurrentText(preset['sort_by'])
            self.max_tracks_spin.setValue(preset['max_tracks'])
            
            self.update_rules()
    
    def save_custom_preset(self):
        """Speichert ein benutzerdefiniertes Preset"""
        # Hier könnte ein Dialog zum Eingeben des Preset-Namens geöffnet werden
        # Für jetzt speichern wir als "Custom_1"
        preset_name = "Custom_1"
        
        presets_file = "config/custom_presets.json"
        os.makedirs(os.path.dirname(presets_file), exist_ok=True)
        
        try:
            if os.path.exists(presets_file):
                with open(presets_file, 'r') as f:
                    presets = json.load(f)
            else:
                presets = {}
            
            presets[preset_name] = self.current_rules.copy()
            
            with open(presets_file, 'w') as f:
                json.dump(presets, f, indent=2)
                
        except Exception as e:
            print(f"Error saving preset: {e}")
    
    def on_generate_playlist(self):
        """Handler für Playlist-Generierung"""
        self.generate_playlist.emit(self.current_rules.copy())
    
    def update_statistics(self, total_tracks, matching_tracks):
        """Aktualisiert die Statistiken"""
        if total_tracks == 0:
            self.stats_label.setText("No tracks loaded")
        else:
            percentage = (matching_tracks / total_tracks) * 100
            self.stats_label.setText(
                f"Total tracks: {total_tracks}\n"
                f"Matching current rules: {matching_tracks} ({percentage:.1f}%)"
            )
    
    def update_available_keys(self, keys):
        """Aktualisiert die verfügbaren Tonarten"""
        current_key = self.start_key_combo.currentText()
        self.start_key_combo.clear()
        self.start_key_combo.addItem("Auto")
        
        for key in sorted(keys):
            self.start_key_combo.addItem(key)
        
        # Vorherige Auswahl wiederherstellen
        index = self.start_key_combo.findText(current_key)
        if index >= 0:
            self.start_key_combo.setCurrentIndex(index)
    
    def get_current_rules(self):
        """Gibt die aktuellen Regeln zurück"""
        return self.current_rules.copy()