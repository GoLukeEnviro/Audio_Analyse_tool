from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QProgressBar, QGroupBox, QFrame, QSpinBox,
    QComboBox, QCheckBox, QToolButton, QButtonGroup,
    QSizePolicy, QApplication
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QThread, QUrl, QPropertyAnimation,
    QEasingCurve, QRect, QSize
)
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import logging
from pathlib import Path
from typing import Optional, Dict, List
import time

logger = logging.getLogger(__name__)

class WaveformWidget(QWidget):
    """Waveform-Visualisierung für Audio-Preview"""
    
    position_changed = Signal(float)  # 0.0 - 1.0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)
        
        # Waveform data
        self.waveform_data = []
        self.current_position = 0.0
        self.duration = 0.0
        
        # Cue points
        self.cue_points = {}  # {name: position}
        self.active_cue = None
        
        # Visual settings
        self.background_color = QColor(30, 30, 30)
        self.waveform_color = QColor(0, 150, 255)
        self.progress_color = QColor(255, 100, 100)
        self.cue_color = QColor(255, 255, 100)
        
        self.setMouseTracking(True)
    
    def set_waveform_data(self, data: List[float]):
        """Setzt Waveform-Daten"""
        self.waveform_data = data
        self.update()
    
    def set_position(self, position: float):
        """Setzt aktuelle Position (0.0 - 1.0)"""
        self.current_position = max(0.0, min(1.0, position))
        self.update()
    
    def add_cue_point(self, name: str, position: float):
        """Fügt Cue-Point hinzu"""
        self.cue_points[name] = max(0.0, min(1.0, position))
        self.update()
    
    def remove_cue_point(self, name: str):
        """Entfernt Cue-Point"""
        if name in self.cue_points:
            del self.cue_points[name]
            self.update()
    
    def paintEvent(self, event):
        """Zeichnet Waveform"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        painter.fillRect(rect, self.background_color)
        
        if not self.waveform_data:
            return
        
        # Zeichne Waveform
        width = rect.width()
        height = rect.height()
        center_y = height // 2
        
        painter.setPen(self.waveform_color)
        
        for i, amplitude in enumerate(self.waveform_data):
            x = int((i / len(self.waveform_data)) * width)
            y_offset = int(amplitude * center_y * 0.8)
            
            painter.drawLine(x, center_y - y_offset, x, center_y + y_offset)
        
        # Zeichne Progress
        progress_x = int(self.current_position * width)
        painter.setPen(self.progress_color)
        painter.drawLine(progress_x, 0, progress_x, height)
        
        # Zeichne Cue-Points
        painter.setPen(self.cue_color)
        for name, position in self.cue_points.items():
            cue_x = int(position * width)
            painter.drawLine(cue_x, 0, cue_x, height)
            
            # Cue-Point Label
            painter.drawText(cue_x + 2, 15, name)
    
    def mousePressEvent(self, event):
        """Maus-Klick für Position-Änderung"""
        if event.button() == Qt.LeftButton:
            position = event.x() / self.width()
            self.position_changed.emit(position)

class AudioPreviewPlayer(QWidget):
    """Audio-Preview-Player mit Cue-Point-Funktionalität"""
    
    # Signals
    track_loaded = Signal(str)
    position_changed = Signal(float)
    cue_point_set = Signal(str, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # State
        self.current_track = None
        self.duration = 0
        self.is_playing = False
        self.loop_enabled = False
        self.loop_start = 0.0
        self.loop_end = 1.0
        
        # Cue points (A, B, C, etc.)
        self.cue_points = {}
        self.active_cue = None
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_position)
        self.update_timer.start(50)  # 20 FPS
        
        self.setup_ui()
        self.setup_connections()
        
        logger.info("AudioPreviewPlayer initialisiert")
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Track info
        info_group = QGroupBox("Track-Info")
        info_layout = QVBoxLayout(info_group)
        
        self.track_label = QLabel("Kein Track geladen")
        self.track_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        info_layout.addWidget(self.track_label)
        
        self.duration_label = QLabel("00:00 / 00:00")
        self.duration_label.setFont(QFont("Segoe UI", 9))
        info_layout.addWidget(self.duration_label)
        
        layout.addWidget(info_group)
        
        # Waveform
        self.waveform = WaveformWidget()
        self.waveform.position_changed.connect(self.seek_to_position)
        layout.addWidget(self.waveform)
        
        # Transport controls
        transport_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self.toggle_playback)
        
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.clicked.connect(self.stop)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.valueChanged.connect(self._on_slider_changed)
        
        transport_layout.addWidget(self.play_btn)
        transport_layout.addWidget(self.stop_btn)
        transport_layout.addWidget(self.position_slider)
        
        layout.addLayout(transport_layout)
        
        # Cue points
        cue_group = QGroupBox("Cue-Points")
        cue_layout = QHBoxLayout(cue_group)
        
        # Cue buttons (A, B, C)
        self.cue_buttons = {}
        for cue_name in ['A', 'B', 'C']:
            btn = QPushButton(cue_name)
            btn.setFixedSize(30, 30)
            btn.clicked.connect(lambda checked, name=cue_name: self.set_cue_point(name))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, name=cue_name: self.goto_cue_point(name)
            )
            self.cue_buttons[cue_name] = btn
            cue_layout.addWidget(btn)
        
        cue_layout.addStretch()
        
        # Loop controls
        self.loop_cb = QCheckBox("Loop")
        self.loop_cb.toggled.connect(self.toggle_loop)
        cue_layout.addWidget(self.loop_cb)
        
        layout.addWidget(cue_group)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)
        
        # Apply dark theme
        self.apply_dark_theme()
    
    def setup_connections(self):
        """Verbindet Media Player Signals"""
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
    
    def apply_dark_theme(self):
        """Wendet dunkles Theme an"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: white;
                background-color: #2d2d2d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #0066cc;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:pressed {
                background-color: #003d7a;
            }
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 8px;
                background: #2d2d2d;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0066cc;
                border: 1px solid #0066cc;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QLabel {
                color: white;
            }
            QCheckBox {
                color: white;
            }
        """)
    
    def load_track(self, file_path: str):
        """Lädt Audio-Track"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Audio-Datei nicht gefunden: {file_path}")
                return False
            
            self.current_track = file_path
            self.media_player.setSource(QUrl.fromLocalFile(str(path.absolute())))
            
            # Update UI
            self.track_label.setText(path.name)
            
            # Reset cue points
            self.cue_points.clear()
            self.waveform.cue_points.clear()
            
            # Generate dummy waveform (in real implementation, use librosa)
            self._generate_dummy_waveform()
            
            self.track_loaded.emit(file_path)
            logger.info(f"Track geladen: {path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des Tracks: {e}")
            return False
    
    def _generate_dummy_waveform(self):
        """Generiert Dummy-Waveform (Platzhalter)"""
        import random
        waveform_data = [random.uniform(0.1, 1.0) for _ in range(200)]
        self.waveform.set_waveform_data(waveform_data)
    
    def toggle_playback(self):
        """Startet/Pausiert Wiedergabe"""
        if self.is_playing:
            self.media_player.pause()
            self.play_btn.setText("▶")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸")
    
    def stop(self):
        """Stoppt Wiedergabe"""
        self.media_player.stop()
        self.play_btn.setText("▶")
        self.position_slider.setValue(0)
    
    def seek_to_position(self, position: float):
        """Springt zu Position (0.0 - 1.0)"""
        if self.duration > 0:
            ms_position = int(position * self.duration)
            self.media_player.setPosition(ms_position)
    
    def set_cue_point(self, name: str):
        """Setzt Cue-Point an aktueller Position"""
        if self.duration > 0:
            position = self.media_player.position() / self.duration
            self.cue_points[name] = position
            self.waveform.add_cue_point(name, position)
            
            # Update button style
            self.cue_buttons[name].setStyleSheet("""
                QPushButton {
                    background-color: #ff6b35;
                    border: 2px solid #ff6b35;
                }
            """)
            
            self.cue_point_set.emit(name, position)
            logger.info(f"Cue-Point {name} gesetzt bei {position:.2f}")
    
    def goto_cue_point(self, name: str):
        """Springt zu Cue-Point"""
        if name in self.cue_points:
            self.seek_to_position(self.cue_points[name])
            logger.info(f"Springe zu Cue-Point {name}")
    
    def toggle_loop(self, enabled: bool):
        """Aktiviert/Deaktiviert Loop"""
        self.loop_enabled = enabled
        if enabled and 'A' in self.cue_points and 'B' in self.cue_points:
            self.loop_start = self.cue_points['A']
            self.loop_end = self.cue_points['B']
            logger.info(f"Loop aktiviert: {self.loop_start:.2f} - {self.loop_end:.2f}")
    
    def _update_position(self):
        """Aktualisiert Position (Timer-Callback)"""
        if self.duration > 0:
            position = self.media_player.position() / self.duration
            self.waveform.set_position(position)
            
            # Loop-Logik
            if self.loop_enabled and self.is_playing:
                if position >= self.loop_end:
                    self.seek_to_position(self.loop_start)
    
    def _on_duration_changed(self, duration: int):
        """Duration geändert"""
        self.duration = duration
        self._update_duration_label()
    
    def _on_position_changed(self, position: int):
        """Position geändert"""
        if self.duration > 0:
            progress = int((position / self.duration) * 1000)
            self.position_slider.setValue(progress)
            self._update_duration_label()
            
            # Emit position signal
            self.position_changed.emit(position / self.duration)
    
    def _on_playback_state_changed(self, state):
        """Playback-Status geändert"""
        self.is_playing = (state == QMediaPlayer.PlayingState)
        
        if self.is_playing:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
    
    def _on_slider_changed(self, value: int):
        """Position-Slider geändert"""
        if self.duration > 0:
            position = int((value / 1000) * self.duration)
            self.media_player.setPosition(position)
    
    def _on_volume_changed(self, value: int):
        """Volume geändert"""
        self.audio_output.setVolume(value / 100.0)
    
    def _update_duration_label(self):
        """Aktualisiert Duration-Label"""
        if self.duration > 0:
            current_ms = self.media_player.position()
            current_time = self._format_time(current_ms)
            total_time = self._format_time(self.duration)
            self.duration_label.setText(f"{current_time} / {total_time}")
    
    def _format_time(self, ms: int) -> str:
        """Formatiert Zeit in MM:SS"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_current_position(self) -> float:
        """Gibt aktuelle Position zurück (0.0 - 1.0)"""
        if self.duration > 0:
            return self.media_player.position() / self.duration
        return 0.0
    
    def get_cue_points(self) -> Dict[str, float]:
        """Gibt alle Cue-Points zurück"""
        return self.cue_points.copy()