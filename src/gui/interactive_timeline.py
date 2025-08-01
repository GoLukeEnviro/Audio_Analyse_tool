"""Interactive Timeline - Drag & Drop Playlist-Editor mit Live-Vorschau"""

import sys
import math
from typing import Dict, List, Any, Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QSlider, QFrame, QSplitter,
    QGroupBox, QProgressBar, QToolTip
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QPoint, QSize, QMimeData, QByteArray
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap,
    QDrag, QLinearGradient, QFontMetrics
)


class TrackBlock(QWidget):
    """Einzelner Track-Block in der Timeline"""
    
    track_selected = Signal(dict)  # track_data
    track_moved = Signal(int, int)  # from_index, to_index
    track_removed = Signal(int)  # track_index
    
    def __init__(self, track_data: Dict[str, Any], index: int, parent=None):
        super().__init__(parent)
        self.track_data = track_data
        self.index = index
        self.is_selected = False
        self.is_dragging = False
        self.drag_start_position = QPoint()
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        # Berechne Block-Breite basierend auf Track-Dauer
        duration = self.track_data.get('duration', 240)  # Sekunden
        self.block_width = max(120, min(300, duration // 2))  # 2 Sekunden = 1 Pixel
        self.setFixedSize(self.block_width, 80)
        
        # Tooltip mit Track-Info
        tooltip_text = self.create_tooltip_text()
        self.setToolTip(tooltip_text)
    
    def create_tooltip_text(self) -> str:
        """Erstellt Tooltip-Text mit Track-Informationen"""
        track = self.track_data
        
        title = track.get('title', 'Unbekannt')
        artist = track.get('artist', 'Unbekannt')
        bpm = track.get('bpm', 0)
        key = track.get('key', 'Unbekannt')
        energy = track.get('energy_score', 0)
        duration = track.get('duration', 0)
        
        duration_str = f"{duration // 60}:{duration % 60:02d}"
        
        return f"""
        <b>{title}</b><br>
        <i>{artist}</i><br><br>
        <b>BPM:</b> {bpm}<br>
        <b>Key:</b> {key}<br>
        <b>Energy:</b> {energy:.1f}/10<br>
        <b>Dauer:</b> {duration_str}
        """
    
    def setup_style(self):
        self.setStyleSheet("""
            TrackBlock {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
            }
            TrackBlock:hover {
                border-color: #007bff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
            }
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Hintergrund (wird durch Stylesheet gehandhabt)
        
        # Energy-Indikator (linker Rand)
        energy = self.track_data.get('energy_score', 5)
        energy_color = self.get_energy_color(energy)
        
        painter.fillRect(0, 0, 4, self.height(), QBrush(energy_color))
        
        # Track-Info Text
        self.draw_track_info(painter)
        
        # Waveform-Simulation (vereinfacht)
        self.draw_mini_waveform(painter)
        
        # Selection Overlay
        if self.is_selected:
            painter.setPen(QPen(QColor("#007bff"), 3))
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
    
    def get_energy_color(self, energy: float) -> QColor:
        """Gibt Farbe basierend auf Energy-Level zurück"""
        if energy >= 8:
            return QColor("#dc3545")  # Rot - Hoch
        elif energy >= 6:
            return QColor("#fd7e14")  # Orange - Mittel-Hoch
        elif energy >= 4:
            return QColor("#ffc107")  # Gelb - Mittel
        else:
            return QColor("#28a745")  # Grün - Niedrig
    
    def draw_track_info(self, painter: QPainter):
        """Zeichnet Track-Informationen"""
        painter.setPen(QPen(QColor("#343a40"), 1))
        
        # Title (gekürzt)
        title = self.track_data.get('title', 'Unbekannt')
        if len(title) > 15:
            title = title[:12] + "..."
        
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        
        painter.drawText(8, 15, title)
        
        # Artist (gekürzt)
        artist = self.track_data.get('artist', 'Unbekannt')
        if len(artist) > 18:
            artist = artist[:15] + "..."
        
        font.setBold(False)
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QPen(QColor("#6c757d"), 1))
        
        painter.drawText(8, 30, artist)
        
        # BPM & Key
        bpm = self.track_data.get('bpm', 0)
        key = self.track_data.get('key', '')
        
        info_text = f"{bpm} BPM"
        if key:
            info_text += f" • {key}"
        
        painter.drawText(8, 45, info_text)
        
        # Duration
        duration = self.track_data.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}"
        
        painter.drawText(8, 60, duration_str)
    
    def draw_mini_waveform(self, painter: QPainter):
        """Zeichnet vereinfachte Waveform-Darstellung"""
        waveform_rect = QRect(self.width() - 60, 10, 50, 30)
        
        painter.setPen(QPen(QColor("#007bff"), 1))
        
        # Simuliere Waveform mit zufälligen Balken
        import random
        random.seed(hash(self.track_data.get('file_path', '')))
        
        bar_width = 2
        bar_count = waveform_rect.width() // (bar_width + 1)
        
        for i in range(bar_count):
            x = waveform_rect.x() + i * (bar_width + 1)
            height = random.randint(5, waveform_rect.height())
            y = waveform_rect.y() + (waveform_rect.height() - height) // 2
            
            painter.fillRect(x, y, bar_width, height, QBrush(QColor("#007bff")))
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
            self.track_selected.emit(self.track_data)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Starte Drag & Drop
        self.start_drag()
    
    def start_drag(self):
        """Startet Drag & Drop Operation"""
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Speichere Track-Index für Drop-Operation
        mime_data.setData("application/x-track-index", QByteArray(str(self.index).encode()))
        drag.setMimeData(mime_data)
        
        # Erstelle Drag-Pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)
        
        # Führe Drag aus
        self.is_dragging = True
        drop_action = drag.exec(Qt.MoveAction)
        self.is_dragging = False
    
    def set_selected(self, selected: bool):
        """Setzt Auswahl-Status"""
        self.is_selected = selected
        self.update()


class TimelineRuler(QWidget):
    """Zeitlineal für Timeline"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.total_duration = 0
        self.track_positions = []  # [(start_time, duration), ...]
    
    def set_tracks(self, tracks: List[Dict[str, Any]]):
        """Setzt Tracks für Zeitberechnung"""
        self.track_positions = []
        current_time = 0
        
        for track in tracks:
            duration = track.get('duration', 240)
            self.track_positions.append((current_time, duration))
            current_time += duration
        
        self.total_duration = current_time
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Hintergrund
        painter.fillRect(self.rect(), QColor("#f8f9fa"))
        
        if self.total_duration == 0:
            return
        
        # Zeitmarkierungen
        painter.setPen(QPen(QColor("#6c757d"), 1))
        
        # Berechne Zeitintervalle
        width = self.width()
        time_per_pixel = self.total_duration / width
        
        # Zeichne Hauptmarkierungen (jede Minute)
        minute_interval = 60  # Sekunden
        pixel_per_minute = minute_interval / time_per_pixel
        
        if pixel_per_minute > 20:  # Nur wenn genug Platz
            for minute in range(0, int(self.total_duration // 60) + 1):
                x = (minute * 60) / time_per_pixel
                
                if x <= width:
                    painter.drawLine(int(x), 0, int(x), self.height())
                    
                    # Zeit-Label
                    time_str = f"{minute}:00"
                    painter.drawText(int(x + 2), 15, time_str)
        
        # Zeichne Track-Grenzen
        painter.setPen(QPen(QColor("#007bff"), 2))
        
        for start_time, duration in self.track_positions:
            x = start_time / time_per_pixel
            painter.drawLine(int(x), 0, int(x), self.height())


class EnergyGraph(QWidget):
    """Energy-Verlauf-Graph für Timeline"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.tracks = []
    
    def set_tracks(self, tracks: List[Dict[str, Any]]):
        """Setzt Tracks für Energy-Graph"""
        self.tracks = tracks
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Hintergrund
        painter.fillRect(self.rect(), QColor("#f8f9fa"))
        
        if not self.tracks:
            return
        
        # Berechne Gesamtdauer
        total_duration = sum(track.get('duration', 240) for track in self.tracks)
        
        if total_duration == 0:
            return
        
        # Zeichne Grid
        self.draw_grid(painter, total_duration)
        
        # Zeichne Energy-Kurve
        self.draw_energy_curve(painter, total_duration)
    
    def draw_grid(self, painter: QPainter, total_duration: float):
        """Zeichnet Hintergrund-Grid"""
        painter.setPen(QPen(QColor("#e9ecef"), 1))
        
        # Horizontale Linien (Energy-Level)
        for i in range(11):  # 0-10 Energy
            y = self.height() - (i / 10) * (self.height() - 20) - 10
            painter.drawLine(0, int(y), self.width(), int(y))
            
            # Energy-Labels
            if i % 2 == 0:
                painter.setPen(QPen(QColor("#6c757d"), 1))
                painter.drawText(5, int(y - 2), str(i))
                painter.setPen(QPen(QColor("#e9ecef"), 1))
    
    def draw_energy_curve(self, painter: QPainter, total_duration: float):
        """Zeichnet Energy-Verlaufskurve"""
        if len(self.tracks) < 2:
            return
        
        width = self.width()
        height = self.height() - 20
        
        # Berechne Punkte
        points = []
        current_time = 0
        
        for track in self.tracks:
            energy = track.get('energy_score', 5)
            duration = track.get('duration', 240)
            
            # Start-Punkt des Tracks
            x = (current_time / total_duration) * width
            y = height - ((energy - 1) / 9) * height + 10
            points.append((x, y))
            
            # End-Punkt des Tracks
            current_time += duration
            x = (current_time / total_duration) * width
            points.append((x, y))
        
        # Zeichne Kurve
        painter.setPen(QPen(QColor("#007bff"), 3))
        
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))
        
        # Zeichne Punkte
        painter.setBrush(QBrush(QColor("#007bff")))
        painter.setPen(QPen(QColor("white"), 2))
        
        for i in range(0, len(points), 2):  # Nur Track-Start-Punkte
            x, y = points[i]
            painter.drawEllipse(int(x - 4), int(y - 4), 8, 8)


class DropZone(QWidget):
    """Drop-Zone für Track-Einfügung"""
    
    track_dropped = Signal(int, int)  # from_index, to_index
    
    def __init__(self, insert_index: int, parent=None):
        super().__init__(parent)
        self.insert_index = insert_index
        self.is_drag_over = False
        
        self.setFixedSize(20, 80)
        self.setAcceptDrops(True)
        
        self.setStyleSheet("""
            DropZone {
                border: 2px dashed #dee2e6;
                border-radius: 4px;
                background: transparent;
            }
        """)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-track-index"):
            event.acceptProposedAction()
            self.is_drag_over = True
            self.setStyleSheet("""
                DropZone {
                    border: 2px dashed #007bff;
                    border-radius: 4px;
                    background: rgba(0, 123, 255, 0.1);
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.is_drag_over = False
        self.setStyleSheet("""
            DropZone {
                border: 2px dashed #dee2e6;
                border-radius: 4px;
                background: transparent;
            }
        """)
    
    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-track-index"):
            from_index_data = event.mimeData().data("application/x-track-index")
            from_index = int(from_index_data.data().decode())
            
            self.track_dropped.emit(from_index, self.insert_index)
            event.acceptProposedAction()
        
        self.is_drag_over = False
        self.setStyleSheet("""
            DropZone {
                border: 2px dashed #dee2e6;
                border-radius: 4px;
                background: transparent;
            }
        """)


class InteractiveTimeline(QWidget):
    """Hauptkomponente der interaktiven Timeline"""
    
    playlist_changed = Signal(list)  # updated_playlist
    track_selected = Signal(dict)  # selected_track
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.playlist = []
        self.track_blocks = []
        self.selected_track_index = -1
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Playlist Timeline")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #343a40;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Zoom Controls
        zoom_label = QLabel("Zoom:")
        header_layout.addWidget(zoom_label)
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        header_layout.addWidget(self.zoom_slider)
        
        layout.addLayout(header_layout)
        
        # Timeline Ruler
        self.ruler = TimelineRuler()
        layout.addWidget(self.ruler)
        
        # Tracks Container
        self.tracks_scroll = QScrollArea()
        self.tracks_scroll.setWidgetResizable(True)
        self.tracks_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tracks_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.tracks_container = QWidget()
        self.tracks_layout = QHBoxLayout(self.tracks_container)
        self.tracks_layout.setSpacing(5)
        self.tracks_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tracks_scroll.setWidget(self.tracks_container)
        layout.addWidget(self.tracks_scroll)
        
        # Energy Graph
        self.energy_graph = EnergyGraph()
        layout.addWidget(self.energy_graph)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶️ Play")
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        self.clear_button = QPushButton("🗑️ Clear")
        self.clear_button.clicked.connect(self.clear_playlist)
        controls_layout.addWidget(self.clear_button)
        
        controls_layout.addStretch()
        
        # Playlist Stats
        self.stats_label = QLabel("Keine Tracks")
        self.stats_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        controls_layout.addWidget(self.stats_label)
        
        layout.addLayout(controls_layout)
    
    def setup_connections(self):
        pass
    
    def set_playlist(self, playlist: List[Dict[str, Any]]):
        """Setzt neue Playlist"""
        self.playlist = playlist.copy()
        self.rebuild_timeline()
        self.update_stats()
    
    def rebuild_timeline(self):
        """Baut Timeline neu auf"""
        # Lösche alte Blocks
        for block in self.track_blocks:
            block.deleteLater()
        self.track_blocks.clear()
        
        # Lösche Layout-Items
        while self.tracks_layout.count():
            child = self.tracks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Erstelle neue Blocks
        for i, track in enumerate(self.playlist):
            # Drop-Zone vor Track
            drop_zone = DropZone(i)
            drop_zone.track_dropped.connect(self.move_track)
            self.tracks_layout.addWidget(drop_zone)
            
            # Track-Block
            block = TrackBlock(track, i)
            block.track_selected.connect(self.on_track_selected)
            block.track_moved.connect(self.move_track)
            
            self.track_blocks.append(block)
            self.tracks_layout.addWidget(block)
        
        # Drop-Zone nach letztem Track
        if self.playlist:
            drop_zone = DropZone(len(self.playlist))
            drop_zone.track_dropped.connect(self.move_track)
            self.tracks_layout.addWidget(drop_zone)
        
        self.tracks_layout.addStretch()
        
        # Update andere Komponenten
        self.ruler.set_tracks(self.playlist)
        self.energy_graph.set_tracks(self.playlist)
    
    def move_track(self, from_index: int, to_index: int):
        """Verschiebt Track in Playlist"""
        if from_index == to_index or from_index < 0 or from_index >= len(self.playlist):
            return
        
        # Korrigiere to_index wenn nötig
        if to_index > from_index:
            to_index -= 1
        
        to_index = max(0, min(to_index, len(self.playlist) - 1))
        
        # Verschiebe Track
        track = self.playlist.pop(from_index)
        self.playlist.insert(to_index, track)
        
        # Rebuild Timeline
        self.rebuild_timeline()
        self.update_stats()
        
        # Emit Signal
        self.playlist_changed.emit(self.playlist.copy())
    
    def remove_track(self, index: int):
        """Entfernt Track aus Playlist"""
        if 0 <= index < len(self.playlist):
            self.playlist.pop(index)
            self.rebuild_timeline()
            self.update_stats()
            self.playlist_changed.emit(self.playlist.copy())
    
    def add_track(self, track: Dict[str, Any], index: Optional[int] = None):
        """Fügt Track zur Playlist hinzu"""
        if index is None:
            self.playlist.append(track)
        else:
            self.playlist.insert(index, track)
        
        self.rebuild_timeline()
        self.update_stats()
        self.playlist_changed.emit(self.playlist.copy())
    
    def on_track_selected(self, track_data: Dict[str, Any]):
        """Callback für Track-Auswahl"""
        # Finde Index
        for i, track in enumerate(self.playlist):
            if track.get('file_path') == track_data.get('file_path'):
                self.selected_track_index = i
                break
        
        # Update Selection
        for i, block in enumerate(self.track_blocks):
            block.set_selected(i == self.selected_track_index)
        
        self.track_selected.emit(track_data)
    
    def on_zoom_changed(self, value: int):
        """Callback für Zoom-Änderung"""
        zoom_factor = value / 100.0
        
        # Skaliere Track-Blocks
        for block in self.track_blocks:
            duration = block.track_data.get('duration', 240)
            new_width = max(80, min(400, int((duration // 2) * zoom_factor)))
            block.setFixedWidth(new_width)
    
    def update_stats(self):
        """Aktualisiert Playlist-Statistiken"""
        if not self.playlist:
            self.stats_label.setText("Keine Tracks")
            return
        
        total_tracks = len(self.playlist)
        total_duration = sum(track.get('duration', 0) for track in self.playlist)
        avg_bpm = sum(track.get('bpm', 0) for track in self.playlist) / total_tracks
        
        duration_str = f"{total_duration // 3600:02d}:{(total_duration % 3600) // 60:02d}:{total_duration % 60:02d}"
        
        self.stats_label.setText(
            f"{total_tracks} Tracks • {duration_str} • ⌀ {avg_bpm:.0f} BPM"
        )
    
    def toggle_playback(self):
        """Toggle Playback (Placeholder)"""
        if self.play_button.text().startswith("▶️"):
            self.play_button.setText("⏸️ Pause")
            # TODO: Start playback
        else:
            self.play_button.setText("▶️ Play")
            # TODO: Pause playback
    
    def clear_playlist(self):
        """Leert Playlist"""
        self.playlist.clear()
        self.rebuild_timeline()
        self.update_stats()
        self.playlist_changed.emit(self.playlist.copy())
    
    def get_playlist(self) -> List[Dict[str, Any]]:
        """Gibt aktuelle Playlist zurück"""
        return self.playlist.copy()
    
    def load_playlist(self, playlist: List[Dict[str, Any]]):
        """Lädt eine Playlist in die Timeline"""
        self.set_playlist(playlist)