"""Playlist Wizard - Interaktive UI für erweiterte Playlist-Generierung"""

import sys
import json
import numpy as np
from typing import Dict, List, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSlider, QSpinBox, QComboBox,
    QProgressBar, QScrollArea, QFrame, QButtonGroup,
    QCheckBox, QTextEdit, QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis

from ..playlist_engine.generator import PlaylistGenerator


class MoodPresetCard(QFrame):
    """Interaktive Mood-Preset-Karte"""
    
    selected = Signal(str)  # preset_id
    
    def __init__(self, preset_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.preset_data = preset_data
        self.preset_id = preset_data['id']
        self.is_selected = False
        
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header mit Emoji und Name
        header_layout = QHBoxLayout()
        
        emoji_label = QLabel(self.preset_data.get('emoji', '🎵'))
        emoji_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(emoji_label)
        
        name_label = QLabel(self.preset_data['name'])
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(name_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Beschreibung
        desc_label = QLabel(self.preset_data['description'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(desc_label)
        
        # Mini Energy-Kurve
        energy_widget = self.create_mini_energy_curve()
        layout.addWidget(energy_widget)
        
        # Details
        details_layout = QGridLayout()
        
        duration_label = QLabel(f"⏱️ {self.preset_data['duration_minutes']}min")
        duration_label.setStyleSheet("font-size: 11px; color: #888;")
        details_layout.addWidget(duration_label, 0, 0)
        
        bpm_range = self.preset_data['bpm_range']
        bpm_label = QLabel(f"🎵 {bpm_range[0]}-{bpm_range[1]} BPM")
        bpm_label.setStyleSheet("font-size: 11px; color: #888;")
        details_layout.addWidget(bpm_label, 0, 1)
        
        layout.addLayout(details_layout)
    
    def create_mini_energy_curve(self) -> QWidget:
        """Erstellt Mini-Visualisierung der Energy-Kurve"""
        widget = QWidget()
        widget.setFixedHeight(40)
        widget.setStyleSheet("background: #f8f9fa; border-radius: 4px;")
        
        # Zeichne Kurve als einfache Linie
        def paintEvent(event):
            painter = QPainter(widget)
            painter.setRenderHint(QPainter.Antialiasing)
            
            energy_curve = self.preset_data.get('energy_curve', [5, 6, 7, 6, 5])
            
            if len(energy_curve) < 2:
                return
            
            # Berechne Punkte
            width = widget.width() - 20
            height = widget.height() - 10
            
            points = []
            for i, energy in enumerate(energy_curve):
                x = 10 + (i / (len(energy_curve) - 1)) * width
                y = height - ((energy - 1) / 9) * (height - 10) + 5
                points.append((x, y))
            
            # Zeichne Linie
            pen = QPen(QColor("#007bff"), 2)
            painter.setPen(pen)
            
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                               int(points[i+1][0]), int(points[i+1][1]))
            
            # Zeichne Punkte
            brush = QBrush(QColor("#007bff"))
            painter.setBrush(brush)
            painter.setPen(QPen(QColor("white"), 1))
            
            for x, y in points:
                painter.drawEllipse(int(x-3), int(y-3), 6, 6)
        
        widget.paintEvent = paintEvent
        return widget
    
    def setup_style(self):
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            MoodPresetCard {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background: white;
                padding: 8px;
            }
            MoodPresetCard:hover {
                border-color: #007bff;
                background: #f8f9ff;
            }
        """)
        
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_selected(True)
            self.selected.emit(self.preset_id)
    
    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                MoodPresetCard {
                    border: 2px solid #007bff;
                    border-radius: 8px;
                    background: #e3f2fd;
                    padding: 8px;
                }
            """)
        else:
            self.setup_style()


class EnergyCanvas(QWidget):
    """Interaktives Canvas für Energy-Kurven-Bearbeitung"""
    
    curve_changed = Signal(list)  # energy_curve
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.energy_curve = [5, 6, 7, 6, 5]
        self.dragging_point = -1
        self.point_radius = 8
        
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
    
    def set_curve(self, curve: List[float]):
        """Setzt neue Energy-Kurve"""
        self.energy_curve = curve.copy()
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Hintergrund
        painter.fillRect(self.rect(), QColor("#f8f9fa"))
        
        # Grid
        self.draw_grid(painter)
        
        # Energy-Kurve
        self.draw_energy_curve(painter)
        
        # Kontrollpunkte
        self.draw_control_points(painter)
    
    def draw_grid(self, painter: QPainter):
        """Zeichnet Hintergrund-Grid"""
        painter.setPen(QPen(QColor("#e9ecef"), 1))
        
        width = self.width() - 40
        height = self.height() - 40
        
        # Horizontale Linien (Energy-Level)
        for i in range(11):  # 0-10 Energy
            y = 20 + (i / 10) * height
            painter.drawLine(20, int(y), width + 20, int(y))
            
            # Labels
            painter.setPen(QPen(QColor("#666"), 1))
            painter.drawText(5, int(y + 5), str(10 - i))
            painter.setPen(QPen(QColor("#e9ecef"), 1))
        
        # Vertikale Linien (Zeit)
        for i in range(len(self.energy_curve)):
            x = 20 + (i / (len(self.energy_curve) - 1)) * width
            painter.drawLine(int(x), 20, int(x), height + 20)
    
    def draw_energy_curve(self, painter: QPainter):
        """Zeichnet Energy-Kurve"""
        if len(self.energy_curve) < 2:
            return
        
        width = self.width() - 40
        height = self.height() - 40
        
        # Berechne Punkte
        points = []
        for i, energy in enumerate(self.energy_curve):
            x = 20 + (i / (len(self.energy_curve) - 1)) * width
            y = 20 + ((10 - energy) / 10) * height
            points.append((x, y))
        
        # Zeichne Kurve
        painter.setPen(QPen(QColor("#007bff"), 3))
        
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))
    
    def draw_control_points(self, painter: QPainter):
        """Zeichnet Kontrollpunkte"""
        width = self.width() - 40
        height = self.height() - 40
        
        for i, energy in enumerate(self.energy_curve):
            x = 20 + (i / (len(self.energy_curve) - 1)) * width
            y = 20 + ((10 - energy) / 10) * height
            
            # Punkt-Hintergrund
            painter.setBrush(QBrush(QColor("white")))
            painter.setPen(QPen(QColor("#007bff"), 2))
            painter.drawEllipse(int(x - self.point_radius), int(y - self.point_radius),
                              self.point_radius * 2, self.point_radius * 2)
            
            # Punkt-Zentrum
            painter.setBrush(QBrush(QColor("#007bff")))
            painter.setPen(QPen(QColor("#007bff"), 1))
            painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            point_index = self.get_point_at_position(event.position().x(), event.position().y())
            if point_index >= 0:
                self.dragging_point = point_index
                self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event):
        if self.dragging_point >= 0:
            # Berechne neue Energy basierend auf Y-Position
            height = self.height() - 40
            y = event.position().y() - 20
            energy = 10 - (y / height) * 10
            energy = max(1, min(10, energy))  # Clamp 1-10
            
            self.energy_curve[self.dragging_point] = energy
            self.update()
            self.curve_changed.emit(self.energy_curve.copy())
        else:
            # Hover-Effekt
            point_index = self.get_point_at_position(event.position().x(), event.position().y())
            if point_index >= 0:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.CrossCursor)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_point = -1
            self.setCursor(Qt.CrossCursor)
    
    def get_point_at_position(self, x: float, y: float) -> int:
        """Findet Kontrollpunkt an Position"""
        width = self.width() - 40
        height = self.height() - 40
        
        for i, energy in enumerate(self.energy_curve):
            point_x = 20 + (i / (len(self.energy_curve) - 1)) * width
            point_y = 20 + ((10 - energy) / 10) * height
            
            distance = ((x - point_x) ** 2 + (y - point_y) ** 2) ** 0.5
            if distance <= self.point_radius:
                return i
        
        return -1


class CamelotWheel(QWidget):
    """Interaktives Camelot Wheel für Key-Auswahl"""
    
    key_selected = Signal(str)  # camelot_key
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wheel_data = []
        self.selected_keys = set()
        self.setMinimumSize(300, 300)
    
    def set_wheel_data(self, wheel_data: Dict[str, Any]):
        """Setzt Camelot Wheel-Daten"""
        self.wheel_data = wheel_data.get('keys', [])
        self.update()
    
    def set_selected_keys(self, keys: List[str]):
        """Setzt ausgewählte Keys"""
        self.selected_keys = set(keys)
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Zeichne Wheel-Segmente
        for key_data in self.wheel_data:
            self.draw_key_segment(painter, key_data, center_x, center_y)
        
        # Zeichne Zentrum
        painter.setBrush(QBrush(QColor("#343a40")))
        painter.setPen(QPen(QColor("#343a40"), 1))
        painter.drawEllipse(center_x - 20, center_y - 20, 40, 40)
        
        painter.setPen(QPen(QColor("white"), 1))
        painter.drawText(center_x - 15, center_y + 5, "KEY")
    
    def draw_key_segment(self, painter: QPainter, key_data: Dict[str, Any], 
                        center_x: int, center_y: int):
        """Zeichnet einzelnes Key-Segment"""
        camelot = key_data['camelot']
        angle = key_data['position']['angle']
        radius = key_data['position']['radius']
        
        # Berechne Position
        angle_rad = np.radians(angle - 90)  # -90 für 12-Uhr-Position
        x = center_x + radius * np.cos(angle_rad)
        y = center_y + radius * np.sin(angle_rad)
        
        # Segment-Farbe
        if camelot in self.selected_keys:
            color = QColor("#007bff")
            text_color = QColor("white")
        elif key_data['type'] == 'A':  # Minor
            color = QColor("#6c757d")
            text_color = QColor("white")
        else:  # Major
            color = QColor("#28a745")
            text_color = QColor("white")
        
        # Zeichne Kreis
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor("white"), 2))
        painter.drawEllipse(int(x - 15), int(y - 15), 30, 30)
        
        # Zeichne Text
        painter.setPen(QPen(text_color, 1))
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        
        text_rect = painter.fontMetrics().boundingRect(camelot)
        text_x = int(x - text_rect.width() // 2)
        text_y = int(y + text_rect.height() // 2 - 2)
        
        painter.drawText(text_x, text_y, camelot)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            camelot = self.get_key_at_position(event.position().x(), event.position().y())
            if camelot:
                if camelot in self.selected_keys:
                    self.selected_keys.remove(camelot)
                else:
                    self.selected_keys.add(camelot)
                
                self.update()
                self.key_selected.emit(camelot)
    
    def get_key_at_position(self, x: float, y: float) -> Optional[str]:
        """Findet Key an Position"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        for key_data in self.wheel_data:
            angle = key_data['position']['angle']
            radius = key_data['position']['radius']
            
            angle_rad = np.radians(angle - 90)
            key_x = center_x + radius * np.cos(angle_rad)
            key_y = center_y + radius * np.sin(angle_rad)
            
            distance = ((x - key_x) ** 2 + (y - key_y) ** 2) ** 0.5
            if distance <= 15:
                return key_data['camelot']
        
        return None


class PlaylistWizard(QWidget):
    """Hauptkomponente des Playlist-Wizards"""
    
    playlist_generated = Signal(dict)  # playlist_result
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = PlaylistGenerator()
        self.available_tracks = []
        
        self.setup_ui()
        self.setup_connections()
        
        # Starte Wizard
        self.start_wizard()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.header_label = QLabel("Playlist Wizard")
        self.header_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #343a40;
            margin-bottom: 10px;
        """)
        layout.addWidget(self.header_label)
        
        self.description_label = QLabel("Erstelle deine perfekte Playlist in 4 einfachen Schritten")
        self.description_label.setStyleSheet("color: #6c757d; font-size: 14px;")
        layout.addWidget(self.description_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 4)
        self.progress_bar.setValue(1)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Content Area
        self.content_area = QScrollArea()
        self.content_area.setWidgetResizable(True)
        self.content_area.setStyleSheet("border: none;")
        layout.addWidget(self.content_area)
        
        # Navigation Buttons
        nav_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Zurück")
        self.back_button.setEnabled(False)
        self.back_button.clicked.connect(self.go_back)
        nav_layout.addWidget(self.back_button)
        
        nav_layout.addStretch()
        
        self.next_button = QPushButton("Weiter →")
        self.next_button.clicked.connect(self.go_next)
        nav_layout.addWidget(self.next_button)
        
        self.generate_button = QPushButton("🎵 Playlist generieren")
        self.generate_button.setVisible(False)
        self.generate_button.clicked.connect(self.generate_playlist)
        nav_layout.addWidget(self.generate_button)
        
        layout.addLayout(nav_layout)
    
    def setup_connections(self):
        pass
    
    def start_wizard(self):
        """Startet den Wizard"""
        wizard_data = self.generator.start_wizard()
        self.show_step_1(wizard_data)
    
    def show_step_1(self, wizard_data: Dict[str, Any]):
        """Zeigt Schritt 1: Mood-Auswahl"""
        self.current_step = 1
        self.progress_bar.setValue(1)
        self.header_label.setText(wizard_data['title'])
        self.description_label.setText(wizard_data['description'])
        
        # Content Widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(16)
        
        # Mood Presets Grid
        presets_layout = QGridLayout()
        presets_layout.setSpacing(16)
        
        self.preset_cards = []
        self.preset_group = QButtonGroup()
        
        for i, preset in enumerate(wizard_data['presets']):
            card = MoodPresetCard(preset)
            card.selected.connect(self.on_preset_selected)
            
            row = i // 3
            col = i % 3
            presets_layout.addWidget(card, row, col)
            
            self.preset_cards.append(card)
        
        layout.addLayout(presets_layout)
        layout.addStretch()
        
        self.content_area.setWidget(content_widget)
        
        # Navigation
        self.back_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.generate_button.setVisible(False)
    
    def show_step_2(self, wizard_data: Dict[str, Any]):
        """Zeigt Schritt 2: Energy-Kurve"""
        self.current_step = 2
        self.progress_bar.setValue(2)
        self.header_label.setText(wizard_data['title'])
        self.description_label.setText(wizard_data['description'])
        
        # Content Widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        
        # Preset Info
        preset_info = QLabel(f"Preset: {wizard_data['preset_name']}")
        preset_info.setStyleSheet("font-weight: bold; font-size: 16px; color: #007bff;")
        layout.addWidget(preset_info)
        
        # Duration Control
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Dauer:"))
        
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(15, 180)
        self.duration_spinbox.setValue(wizard_data['duration_minutes'])
        self.duration_spinbox.setSuffix(" min")
        duration_layout.addWidget(self.duration_spinbox)
        
        duration_layout.addStretch()
        layout.addLayout(duration_layout)
        
        # Energy Canvas
        canvas_group = QGroupBox("Energy-Verlauf")
        canvas_layout = QVBoxLayout(canvas_group)
        
        self.energy_canvas = EnergyCanvas()
        self.energy_canvas.set_curve(wizard_data['default_curve'])
        self.energy_canvas.curve_changed.connect(self.on_curve_changed)
        canvas_layout.addWidget(self.energy_canvas)
        
        layout.addWidget(canvas_group)
        
        # Curve Templates
        templates_group = QGroupBox("Vorlagen")
        templates_layout = QHBoxLayout(templates_group)
        
        for template in wizard_data['curve_templates']:
            btn = QPushButton(f"{template['emoji']} {template['name']}")
            btn.setToolTip(template['description'])
            btn.clicked.connect(lambda checked, curve=template['curve']: self.apply_curve_template(curve))
            templates_layout.addWidget(btn)
        
        layout.addWidget(templates_group)
        layout.addStretch()
        
        self.content_area.setWidget(content_widget)
        
        # Navigation
        self.back_button.setEnabled(True)
        self.next_button.setEnabled(True)
    
    def show_step_3(self, wizard_data: Dict[str, Any]):
        """Zeigt Schritt 3: Key-Präferenzen"""
        self.current_step = 3
        self.progress_bar.setValue(3)
        self.header_label.setText(wizard_data['title'])
        self.description_label.setText(wizard_data['description'])
        
        # Content Widget
        content_widget = QWidget()
        layout = QHBoxLayout(content_widget)
        layout.setSpacing(30)
        
        # Linke Seite: Camelot Wheel
        left_layout = QVBoxLayout()
        
        wheel_label = QLabel("Bevorzugte Tonarten auswählen:")
        wheel_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(wheel_label)
        
        self.camelot_wheel = CamelotWheel()
        self.camelot_wheel.set_wheel_data(wizard_data['camelot_wheel'])
        self.camelot_wheel.set_selected_keys(wizard_data.get('key_suggestions', []))
        self.camelot_wheel.key_selected.connect(self.on_key_selected)
        left_layout.addWidget(self.camelot_wheel)
        
        layout.addLayout(left_layout)
        
        # Rechte Seite: Optionen
        right_layout = QVBoxLayout()
        
        # Transition Style
        style_group = QGroupBox("Übergangsstil")
        style_layout = QVBoxLayout(style_group)
        
        self.transition_group = QButtonGroup()
        
        for style in wizard_data['transition_styles']:
            radio = QCheckBox(f"{style['name']} - {style['description']}")
            if style['id'] == 'smooth':  # Default
                radio.setChecked(True)
            
            style_layout.addWidget(radio)
            self.transition_group.addButton(radio)
        
        right_layout.addWidget(style_group)
        
        # Selected Keys Display
        keys_group = QGroupBox("Ausgewählte Tonarten")
        keys_layout = QVBoxLayout(keys_group)
        
        self.selected_keys_label = QLabel("Keine Tonarten ausgewählt")
        self.selected_keys_label.setWordWrap(True)
        keys_layout.addWidget(self.selected_keys_label)
        
        right_layout.addWidget(keys_group)
        right_layout.addStretch()
        
        layout.addLayout(right_layout)
        
        self.content_area.setWidget(content_widget)
        
        # Navigation
        self.back_button.setEnabled(True)
        self.next_button.setEnabled(True)
    
    def show_step_4(self, wizard_data: Dict[str, Any]):
        """Zeigt Schritt 4: Vorschau & Export"""
        self.current_step = 4
        self.progress_bar.setValue(4)
        self.header_label.setText(wizard_data['title'])
        self.description_label.setText(wizard_data['description'])
        
        # Content Widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        
        # Zusammenfassung
        summary_group = QGroupBox("Playlist-Zusammenfassung")
        summary_layout = QVBoxLayout(summary_group)
        
        wizard_state = wizard_data['wizard_state']
        
        summary_text = f"""
        <b>Mood-Preset:</b> {wizard_state.get('mood_preset', 'Unbekannt')}<br>
        <b>Dauer:</b> {wizard_state.get('duration_minutes', 60)} Minuten<br>
        <b>Energy-Kurve:</b> {len(wizard_state.get('energy_curve', []))} Punkte<br>
        <b>Tonarten:</b> {len(wizard_state.get('key_preferences', []))} ausgewählt<br>
        <b>Übergangsstil:</b> {wizard_state.get('transition_style', 'smooth')}
        """
        
        summary_label = QLabel(summary_text)
        summary_label.setWordWrap(True)
        summary_layout.addWidget(summary_label)
        
        layout.addWidget(summary_group)
        
        # Export-Optionen
        export_group = QGroupBox("Export-Optionen")
        export_layout = QVBoxLayout(export_group)
        
        self.export_rekordbox = QCheckBox("Rekordbox XML exportieren")
        self.export_rekordbox.setChecked(True)
        export_layout.addWidget(self.export_rekordbox)
        
        self.export_m3u = QCheckBox("M3U Playlist exportieren")
        self.export_m3u.setChecked(True)
        export_layout.addWidget(self.export_m3u)
        
        self.export_json = QCheckBox("JSON Metadaten exportieren")
        self.export_json.setChecked(False)
        export_layout.addWidget(self.export_json)
        
        layout.addWidget(export_group)
        layout.addStretch()
        
        self.content_area.setWidget(content_widget)
        
        # Navigation
        self.back_button.setEnabled(True)
        self.next_button.setVisible(False)
        self.generate_button.setVisible(True)
    
    def on_preset_selected(self, preset_id: str):
        """Callback für Preset-Auswahl"""
        # Deselektiere andere Cards
        for card in self.preset_cards:
            card.set_selected(card.preset_id == preset_id)
        
        self.selected_preset = preset_id
        self.next_button.setEnabled(True)
    
    def on_curve_changed(self, curve: List[float]):
        """Callback für Energy-Kurve-Änderung"""
        self.current_energy_curve = curve
    
    def apply_curve_template(self, curve: List[float]):
        """Wendet Kurven-Template an"""
        self.energy_canvas.set_curve(curve)
        self.current_energy_curve = curve
    
    def on_key_selected(self, camelot: str):
        """Callback für Key-Auswahl"""
        selected_keys = list(self.camelot_wheel.selected_keys)
        if selected_keys:
            self.selected_keys_label.setText(f"Ausgewählt: {', '.join(selected_keys)}")
        else:
            self.selected_keys_label.setText("Keine Tonarten ausgewählt")
    
    def go_back(self):
        """Geht zum vorherigen Schritt"""
        if self.current_step > 1:
            if self.current_step == 2:
                self.start_wizard()
            elif self.current_step == 3:
                wizard_data = self.generator.wizard_step_2(self.selected_preset)
                self.show_step_2(wizard_data)
            elif self.current_step == 4:
                wizard_data = self.generator.wizard_step_3(
                    getattr(self, 'current_energy_curve', [5, 6, 7, 6, 5]),
                    self.duration_spinbox.value() if hasattr(self, 'duration_spinbox') else 60
                )
                self.show_step_3(wizard_data)
    
    def go_next(self):
        """Geht zum nächsten Schritt"""
        if self.current_step == 1 and hasattr(self, 'selected_preset'):
            wizard_data = self.generator.wizard_step_2(self.selected_preset)
            self.show_step_2(wizard_data)
        
        elif self.current_step == 2:
            energy_curve = getattr(self, 'current_energy_curve', [5, 6, 7, 6, 5])
            duration = self.duration_spinbox.value()
            wizard_data = self.generator.wizard_step_3(energy_curve, duration)
            self.show_step_3(wizard_data)
        
        elif self.current_step == 3:
            selected_keys = list(self.camelot_wheel.selected_keys)
            transition_style = 'smooth'  # TODO: Get from UI
            wizard_data = self.generator.wizard_step_4(selected_keys, transition_style)
            self.show_step_4(wizard_data)
    
    def set_available_tracks(self, tracks: List[Dict[str, Any]]):
        """Setzt verfügbare Tracks für Playlist-Generierung"""
        self.available_tracks = tracks
    
    def generate_playlist(self):
        """Generiert finale Playlist"""
        if not self.available_tracks:
            # TODO: Show error message
            return
        
        try:
            result = self.generator.generate_from_wizard(self.available_tracks)
            self.playlist_generated.emit(result)
        except Exception as e:
            # TODO: Show error message
            print(f"Fehler bei Playlist-Generierung: {e}")