from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QWidget, QFileDialog, QLineEdit, QCheckBox,
    QProgressBar, QTextEdit, QGroupBox, QRadioButton, QButtonGroup,
    QSlider, QSpinBox, QComboBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class OnboardingWizard(QDialog):
    """4-Schritt Setup-Prozess für neue Benutzer"""
    
    setup_completed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DJ Audio-Analyse-Tool Pro - Setup")
        self.setFixedSize(800, 600)
        self.setModal(True)
        
        # Setup data
        self.setup_data = {
            'music_library_path': '',
            'cache_location': 'cache',
            'analysis_quality': 'high',
            'enable_multiprocessing': True,
            'auto_analyze': True,
            'export_format': 'm3u',
            'theme': 'dark'
        }
        
        self.current_step = 0
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """Erstellt die Wizard-Oberfläche"""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Content area
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create wizard steps
        self.create_step_1()  # Willkommen
        self.create_step_2()  # Musikbibliothek
        self.create_step_3()  # Analyse-Einstellungen
        self.create_step_4()  # Fertigstellung
        
        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(20, 10, 20, 20)
        
        self.back_btn = QPushButton("← Zurück")
        self.back_btn.setEnabled(False)
        self.back_btn.clicked.connect(self.previous_step)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch()
        
        self.next_btn = QPushButton("Weiter →")
        self.next_btn.clicked.connect(self.next_step)
        
        self.finish_btn = QPushButton("Setup abschließen")
        self.finish_btn.setVisible(False)
        self.finish_btn.clicked.connect(self.finish_setup)
        
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.finish_btn)
        
        layout.addLayout(nav_layout)
        
        # Apply dark theme
        self.apply_dark_theme()
    
    def create_header(self):
        """Erstellt den Header mit Fortschrittsanzeige"""
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1a1a, stop:1 #2d2d2d);
                border-bottom: 2px solid #0066cc;
            }
        """)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Title
        title = QLabel("Setup-Assistent")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 4)
        self.progress_bar.setValue(1)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #2d2d2d;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        return header
    
    def create_step_1(self):
        """Schritt 1: Willkommen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Welcome message
        welcome = QLabel("Willkommen beim DJ Audio-Analyse-Tool Pro!")
        welcome.setFont(QFont("Segoe UI", 24, QFont.Bold))
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("color: #0066cc; margin-bottom: 20px;")
        layout.addWidget(welcome)
        
        # Description
        desc = QLabel("""
        Dieses Tool analysiert Ihre Musikbibliothek und erstellt intelligente Playlists
        basierend auf BPM, Tonart, Energie-Level und Stimmung.
        
        Der Setup-Assistent führt Sie durch die wichtigsten Einstellungen:
        
        • Musikbibliothek auswählen
        • Analyse-Parameter konfigurieren
        • Export-Optionen festlegen
        
        Der gesamte Prozess dauert nur wenige Minuten.
        """)
        desc.setFont(QFont("Segoe UI", 12))
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cccccc; line-height: 1.5;")
        layout.addWidget(desc)
        
        layout.addStretch()
        
        # Features preview
        features = QLabel("🎵 Audio-Analyse  •  🎧 Playlist-Generierung  •  📊 Visualisierung")
        features.setFont(QFont("Segoe UI", 14))
        features.setAlignment(Qt.AlignCenter)
        features.setStyleSheet("color: #4caf50; margin-top: 20px;")
        layout.addWidget(features)
        
        self.stacked_widget.addWidget(widget)
    
    def create_step_2(self):
        """Schritt 2: Musikbibliothek auswählen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Musikbibliothek auswählen")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Wählen Sie den Hauptordner Ihrer Musiksammlung aus. Das Tool wird alle Unterordner nach Audio-Dateien durchsuchen.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cccccc; margin-bottom: 20px;")
        layout.addWidget(desc)
        
        # Path selection
        path_group = QGroupBox("Musikbibliothek-Pfad")
        path_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        path_layout = QVBoxLayout(path_group)
        
        path_input_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Pfad zur Musikbibliothek...")
        self.path_input.textChanged.connect(self.validate_step_2)
        
        browse_btn = QPushButton("Durchsuchen")
        browse_btn.clicked.connect(self.browse_music_folder)
        
        path_input_layout.addWidget(self.path_input)
        path_input_layout.addWidget(browse_btn)
        path_layout.addLayout(path_input_layout)
        
        # Cache location
        cache_layout = QHBoxLayout()
        cache_label = QLabel("Cache-Verzeichnis:")
        self.cache_input = QLineEdit("cache")
        cache_layout.addWidget(cache_label)
        cache_layout.addWidget(self.cache_input)
        path_layout.addLayout(cache_layout)
        
        layout.addWidget(path_group)
        
        # Supported formats info
        formats = QLabel("Unterstützte Formate: MP3, WAV, FLAC, M4A, OGG")
        formats.setStyleSheet("color: #4caf50; font-style: italic;")
        layout.addWidget(formats)
        
        layout.addStretch()
        
        self.stacked_widget.addWidget(widget)
    
    def create_step_3(self):
        """Schritt 3: Analyse-Einstellungen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Analyse-Einstellungen")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Quality settings
        quality_group = QGroupBox("Analyse-Qualität")
        quality_layout = QVBoxLayout(quality_group)
        
        self.quality_group = QButtonGroup()
        
        high_quality = QRadioButton("Hoch (empfohlen) - Beste Genauigkeit, längere Analysezeit")
        high_quality.setChecked(True)
        medium_quality = QRadioButton("Mittel - Gute Balance zwischen Geschwindigkeit und Genauigkeit")
        fast_quality = QRadioButton("Schnell - Für große Bibliotheken, reduzierte Genauigkeit")
        
        self.quality_group.addButton(high_quality, 0)
        self.quality_group.addButton(medium_quality, 1)
        self.quality_group.addButton(fast_quality, 2)
        
        quality_layout.addWidget(high_quality)
        quality_layout.addWidget(medium_quality)
        quality_layout.addWidget(fast_quality)
        
        layout.addWidget(quality_group)
        
        # Performance settings
        perf_group = QGroupBox("Performance-Optionen")
        perf_layout = QVBoxLayout(perf_group)
        
        self.multiprocessing_cb = QCheckBox("Multiprocessing aktivieren (empfohlen für große Bibliotheken)")
        self.multiprocessing_cb.setChecked(True)
        
        self.auto_analyze_cb = QCheckBox("Neue Dateien automatisch analysieren")
        self.auto_analyze_cb.setChecked(True)
        
        perf_layout.addWidget(self.multiprocessing_cb)
        perf_layout.addWidget(self.auto_analyze_cb)
        
        layout.addWidget(perf_group)
        
        # Export settings
        export_group = QGroupBox("Standard-Export-Format")
        export_layout = QVBoxLayout(export_group)
        
        self.export_combo = QComboBox()
        self.export_combo.addItems(["M3U Playlist", "Rekordbox XML", "CSV Export"])
        export_layout.addWidget(self.export_combo)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
        
        self.stacked_widget.addWidget(widget)
    
    def create_step_4(self):
        """Schritt 4: Fertigstellung"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Setup abgeschlossen!")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4caf50; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
                color: #cccccc;
            }
        """)
        layout.addWidget(self.summary_text)
        
        # Next steps
        next_steps = QLabel("""
        Nächste Schritte:
        
        1. Das Tool wird Ihre Musikbibliothek scannen
        2. Audio-Analyse wird automatisch gestartet
        3. Sie können sofort mit der Playlist-Erstellung beginnen
        
        Tipp: Nutzen Sie den Playlist-Wizard für optimale Ergebnisse!
        """)
        next_steps.setWordWrap(True)
        next_steps.setStyleSheet("color: #cccccc; line-height: 1.5;")
        layout.addWidget(next_steps)
        
        layout.addStretch()
        
        self.stacked_widget.addWidget(widget)
    
    def setup_animations(self):
        """Erstellt Übergangsanimationen"""
        self.fade_animation = QPropertyAnimation(self.stacked_widget, b"geometry")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def apply_dark_theme(self):
        """Wendet das dunkle Theme an"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
            }
            QPushButton {
                background-color: #0066cc;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: white;
            }
            QLineEdit:focus {
                border-color: #0066cc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: white;
            }
            QRadioButton, QCheckBox {
                color: white;
                spacing: 8px;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                color: white;
            }
        """)
    
    def browse_music_folder(self):
        """Öffnet Dialog zur Ordnerauswahl"""
        folder = QFileDialog.getExistingDirectory(
            self, "Musikbibliothek auswählen", 
            self.path_input.text() or str(Path.home())
        )
        if folder:
            self.path_input.setText(folder)
    
    def validate_step_2(self):
        """Validiert Schritt 2"""
        path = self.path_input.text().strip()
        self.next_btn.setEnabled(bool(path and Path(path).exists()))
    
    def next_step(self):
        """Geht zum nächsten Schritt"""
        if self.current_step < 3:
            self.current_step += 1
            self.stacked_widget.setCurrentIndex(self.current_step)
            self.progress_bar.setValue(self.current_step + 1)
            
            # Update navigation
            self.back_btn.setEnabled(self.current_step > 0)
            
            if self.current_step == 3:  # Last step
                self.next_btn.setVisible(False)
                self.finish_btn.setVisible(True)
                self.update_summary()
            
            # Validate current step
            if self.current_step == 1:
                self.validate_step_2()
    
    def previous_step(self):
        """Geht zum vorherigen Schritt"""
        if self.current_step > 0:
            self.current_step -= 1
            self.stacked_widget.setCurrentIndex(self.current_step)
            self.progress_bar.setValue(self.current_step + 1)
            
            # Update navigation
            self.back_btn.setEnabled(self.current_step > 0)
            self.next_btn.setVisible(True)
            self.finish_btn.setVisible(False)
            
            if self.current_step == 1:
                self.validate_step_2()
            else:
                self.next_btn.setEnabled(True)
    
    def update_summary(self):
        """Aktualisiert die Zusammenfassung"""
        # Collect settings
        self.setup_data['music_library_path'] = self.path_input.text()
        self.setup_data['cache_location'] = self.cache_input.text()
        
        quality_map = {0: 'high', 1: 'medium', 2: 'fast'}
        self.setup_data['analysis_quality'] = quality_map[self.quality_group.checkedId()]
        
        self.setup_data['enable_multiprocessing'] = self.multiprocessing_cb.isChecked()
        self.setup_data['auto_analyze'] = self.auto_analyze_cb.isChecked()
        
        export_map = {0: 'm3u', 1: 'rekordbox', 2: 'csv'}
        self.setup_data['export_format'] = export_map[self.export_combo.currentIndex()]
        
        # Generate summary
        summary = f"""
        Setup-Konfiguration:
        
        📁 Musikbibliothek: {self.setup_data['music_library_path']}
        💾 Cache-Verzeichnis: {self.setup_data['cache_location']}
        🎯 Analyse-Qualität: {self.setup_data['analysis_quality'].title()}
        ⚡ Multiprocessing: {'Aktiviert' if self.setup_data['enable_multiprocessing'] else 'Deaktiviert'}
        🔄 Auto-Analyse: {'Aktiviert' if self.setup_data['auto_analyze'] else 'Deaktiviert'}
        📤 Export-Format: {self.export_combo.currentText()}
        """
        
        self.summary_text.setPlainText(summary)
    
    def finish_setup(self):
        """Schließt das Setup ab"""
        self.update_summary()
        
        # Save settings
        try:
            config_path = Path("config/user_config.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.setup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Setup-Konfiguration gespeichert: {config_path}")
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
        
        # Emit completion signal
        self.setup_completed.emit(self.setup_data)
        self.accept()