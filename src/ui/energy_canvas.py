"""Interactive Energy Curve Canvas - Interaktives Energie-Kurven-Canvas für DJ-Workflows"""

import sys
import numpy as np
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QSpinBox, QComboBox, QGroupBox, QFrame,
    QToolButton, QButtonGroup, QSplitter, QTextEdit,
    QScrollArea, QGridLayout, QCheckBox, QDoubleSpinBox,
    QProgressBar, QTabWidget, QListWidget, QListWidgetItem,
    QMessageBox, QFileDialog, QColorDialog, QApplication
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QThread, pyqtSignal, QPointF, QRectF,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QLinearGradient, QRadialGradient,
    QPolygonF, QPixmap, QIcon, QCursor, QPalette
)

from ..playlist_engine.enhanced_generator import EnergyPoint, EnhancedPlaylistGenerator
from ..audio_analysis.energy_score_extractor import EnergyScoreExtractor

logger = logging.getLogger(__name__)

@dataclass
class CanvasConfig:
    """Konfiguration für das Energie-Canvas"""
    width: int = 800
    height: int = 400
    margin: int = 50
    grid_enabled: bool = True
    snap_to_grid: bool = True
    grid_spacing: int = 20
    point_radius: int = 8
    line_width: int = 3
    animation_duration: int = 300
    auto_save: bool = True
    show_tooltips: bool = True
    theme: str = 'dark'  # 'dark' oder 'light'

class EnergyCanvasWidget(QWidget):
    """Interaktives Canvas für Energie-Kurven-Erstellung"""
    
    # Signals
    curve_changed = Signal(list)  # Emitted when curve is modified
    point_selected = Signal(int)  # Emitted when point is selected
    curve_exported = Signal(str)  # Emitted when curve is exported
    
    def __init__(self, config: Optional[CanvasConfig] = None, parent=None):
        super().__init__(parent)
        
        self.config = config or CanvasConfig()
        self.energy_points = []
        self.selected_point_index = -1
        self.dragging_point = False
        self.hover_point_index = -1
        
        # Canvas-Zustand
        self.canvas_rect = QRectF()
        self.energy_rect = QRectF(0, 0, 1, 10)  # Position: 0-1, Energy: 0-10
        
        # Interaktions-Modi
        self.interaction_mode = 'edit'  # 'edit', 'add', 'delete', 'view'
        self.snap_enabled = True
        self.grid_visible = True
        
        # Undo/Redo
        self.history = []
        self.history_index = -1
        self.max_history = 50
        
        # Animationen
        self.animations = QParallelAnimationGroup()
        
        # Themes
        self.themes = {
            'dark': {
                'background': QColor(30, 30, 30),
                'grid': QColor(60, 60, 60),
                'curve': QColor(0, 150, 255),
                'point': QColor(255, 100, 100),
                'selected': QColor(255, 255, 100),
                'hover': QColor(150, 255, 150),
                'text': QColor(255, 255, 255)
            },
            'light': {
                'background': QColor(250, 250, 250),
                'grid': QColor(200, 200, 200),
                'curve': QColor(0, 100, 200),
                'point': QColor(200, 50, 50),
                'selected': QColor(200, 200, 50),
                'hover': QColor(100, 200, 100),
                'text': QColor(50, 50, 50)
            }
        }
        
        self.current_theme = self.themes[self.config.theme]
        
        # Setup UI
        self._setup_ui()
        self._setup_default_curve()
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        logger.info("EnergyCanvasWidget initialisiert")
    
    def _setup_ui(self):
        """Setup der Benutzeroberfläche"""
        self.setMinimumSize(self.config.width, self.config.height)
        self.setStyleSheet(self._get_stylesheet())
        
        # Tooltip-Setup
        if self.config.show_tooltips:
            self.setToolTip("Klicken und ziehen um Punkte zu bewegen\nDoppelklick um Punkte hinzuzufügen")
    
    def _setup_default_curve(self):
        """Erstellt Standard-Energie-Kurve"""
        default_points = [
            EnergyPoint(0.0, 4.0, 1.0, 0.5),
            EnergyPoint(0.25, 6.0, 1.2, 0.4),
            EnergyPoint(0.5, 8.0, 1.5, 0.3),
            EnergyPoint(0.75, 7.0, 1.3, 0.4),
            EnergyPoint(1.0, 5.0, 1.0, 0.5)
        ]
        
        self.set_energy_curve(default_points)
    
    def _get_stylesheet(self) -> str:
        """Gibt Stylesheet für das Widget zurück"""
        bg_color = self.current_theme['background']
        text_color = self.current_theme['text']
        
        return f"""
        EnergyCanvasWidget {{
            background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});
            color: rgb({text_color.red()}, {text_color.green()}, {text_color.blue()});
            border: 1px solid #555;
            border-radius: 5px;
        }}
        """
    
    def set_energy_curve(self, energy_points: List[EnergyPoint]):
        """Setzt neue Energie-Kurve"""
        self.energy_points = energy_points.copy()
        self._save_to_history()
        self.update()
        self.curve_changed.emit(self.energy_points)
    
    def get_energy_curve(self) -> List[EnergyPoint]:
        """Gibt aktuelle Energie-Kurve zurück"""
        return self.energy_points.copy()
    
    def add_energy_point(self, position: float, energy: float) -> int:
        """Fügt neuen Energie-Punkt hinzu"""
        # Validierung
        position = max(0.0, min(1.0, position))
        energy = max(0.0, min(10.0, energy))
        
        # Finde Einfügeposition
        insert_index = 0
        for i, point in enumerate(self.energy_points):
            if point.position > position:
                break
            insert_index = i + 1
        
        # Erstelle neuen Punkt
        new_point = EnergyPoint(
            position=position,
            energy=energy,
            weight=1.0,
            tolerance=0.5
        )
        
        # Füge Punkt ein
        self.energy_points.insert(insert_index, new_point)
        self._save_to_history()
        self.update()
        self.curve_changed.emit(self.energy_points)
        
        return insert_index
    
    def remove_energy_point(self, index: int) -> bool:
        """Entfernt Energie-Punkt"""
        if 0 <= index < len(self.energy_points) and len(self.energy_points) > 2:
            self.energy_points.pop(index)
            self.selected_point_index = -1
            self._save_to_history()
            self.update()
            self.curve_changed.emit(self.energy_points)
            return True
        return False
    
    def update_energy_point(self, index: int, position: float, energy: float):
        """Aktualisiert Energie-Punkt"""
        if 0 <= index < len(self.energy_points):
            # Validierung
            position = max(0.0, min(1.0, position))
            energy = max(0.0, min(10.0, energy))
            
            # Update Punkt
            self.energy_points[index].position = position
            self.energy_points[index].energy = energy
            
            # Sortiere Punkte nach Position
            self.energy_points.sort(key=lambda p: p.position)
            
            self.update()
            self.curve_changed.emit(self.energy_points)
    
    def set_interaction_mode(self, mode: str):
        """Setzt Interaktions-Modus"""
        if mode in ['edit', 'add', 'delete', 'view']:
            self.interaction_mode = mode
            self._update_cursor()
    
    def set_snap_enabled(self, enabled: bool):
        """Aktiviert/Deaktiviert Snap-to-Grid"""
        self.snap_enabled = enabled
    
    def set_grid_visible(self, visible: bool):
        """Zeigt/Versteckt Grid"""
        self.grid_visible = visible
        self.update()
    
    def set_theme(self, theme_name: str):
        """Setzt Theme"""
        if theme_name in self.themes:
            self.current_theme = self.themes[theme_name]
            self.setStyleSheet(self._get_stylesheet())
            self.update()
    
    def paintEvent(self, event):
        """Paint-Event für Canvas-Rendering"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Update Canvas-Rechteck
        self.canvas_rect = QRectF(
            self.config.margin,
            self.config.margin,
            self.width() - 2 * self.config.margin,
            self.height() - 2 * self.config.margin
        )
        
        # Zeichne Komponenten
        self._draw_background(painter)
        if self.grid_visible:
            self._draw_grid(painter)
        self._draw_axes(painter)
        self._draw_curve(painter)
        self._draw_points(painter)
        self._draw_labels(painter)
    
    def _draw_background(self, painter: QPainter):
        """Zeichnet Hintergrund"""
        painter.fillRect(self.rect(), self.current_theme['background'])
    
    def _draw_grid(self, painter: QPainter):
        """Zeichnet Grid"""
        painter.setPen(QPen(self.current_theme['grid'], 1, Qt.DotLine))
        
        # Vertikale Linien
        for i in range(0, int(self.canvas_rect.width()), self.config.grid_spacing):
            x = self.canvas_rect.left() + i
            painter.drawLine(x, self.canvas_rect.top(), x, self.canvas_rect.bottom())
        
        # Horizontale Linien
        for i in range(0, int(self.canvas_rect.height()), self.config.grid_spacing):
            y = self.canvas_rect.top() + i
            painter.drawLine(self.canvas_rect.left(), y, self.canvas_rect.right(), y)
    
    def _draw_axes(self, painter: QPainter):
        """Zeichnet Achsen"""
        painter.setPen(QPen(self.current_theme['text'], 2))
        
        # X-Achse (Position)
        painter.drawLine(
            self.canvas_rect.bottomLeft(),
            self.canvas_rect.bottomRight()
        )
        
        # Y-Achse (Energy)
        painter.drawLine(
            self.canvas_rect.bottomLeft(),
            self.canvas_rect.topLeft()
        )
        
        # Achsen-Beschriftungen
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        # X-Achse Ticks
        for i in range(11):  # 0% bis 100%
            x = self.canvas_rect.left() + (i / 10.0) * self.canvas_rect.width()
            y = self.canvas_rect.bottom() + 15
            painter.drawText(x - 10, y, f"{i*10}%")
        
        # Y-Achse Ticks
        for i in range(11):  # 0 bis 10 Energy
            x = self.canvas_rect.left() - 25
            y = self.canvas_rect.bottom() - (i / 10.0) * self.canvas_rect.height() + 5
            painter.drawText(x, y, str(i))
    
    def _draw_curve(self, painter: QPainter):
        """Zeichnet Energie-Kurve"""
        if len(self.energy_points) < 2:
            return
        
        # Erstelle Kurven-Pfad
        path = QPainterPath()
        
        # Erster Punkt
        first_point = self._energy_to_canvas(self.energy_points[0])
        path.moveTo(first_point)
        
        # Interpolierte Kurve
        for i in range(1, len(self.energy_points)):
            canvas_point = self._energy_to_canvas(self.energy_points[i])
            
            if i == 1:
                # Erste Linie
                path.lineTo(canvas_point)
            else:
                # Smooth curve mit Bezier
                prev_point = self._energy_to_canvas(self.energy_points[i-1])
                control_offset = (canvas_point.x() - prev_point.x()) * 0.3
                
                control1 = QPointF(prev_point.x() + control_offset, prev_point.y())
                control2 = QPointF(canvas_point.x() - control_offset, canvas_point.y())
                
                path.cubicTo(control1, control2, canvas_point)
        
        # Zeichne Kurve
        painter.setPen(QPen(self.current_theme['curve'], self.config.line_width))
        painter.drawPath(path)
        
        # Zeichne Füllung unter der Kurve
        fill_path = QPainterPath(path)
        fill_path.lineTo(self.canvas_rect.bottomRight())
        fill_path.lineTo(self.canvas_rect.bottomLeft())
        fill_path.closeSubpath()
        
        gradient = QLinearGradient(0, self.canvas_rect.top(), 0, self.canvas_rect.bottom())
        curve_color = self.current_theme['curve']
        gradient.setColorAt(0, QColor(curve_color.red(), curve_color.green(), curve_color.blue(), 100))
        gradient.setColorAt(1, QColor(curve_color.red(), curve_color.green(), curve_color.blue(), 20))
        
        painter.fillPath(fill_path, QBrush(gradient))
    
    def _draw_points(self, painter: QPainter):
        """Zeichnet Energie-Punkte"""
        for i, point in enumerate(self.energy_points):
            canvas_point = self._energy_to_canvas(point)
            
            # Wähle Farbe basierend auf Zustand
            if i == self.selected_point_index:
                color = self.current_theme['selected']
                radius = self.config.point_radius + 2
            elif i == self.hover_point_index:
                color = self.current_theme['hover']
                radius = self.config.point_radius + 1
            else:
                color = self.current_theme['point']
                radius = self.config.point_radius
            
            # Zeichne Punkt
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(canvas_point, radius, radius)
            
            # Zeichne Toleranz-Ring
            if i == self.selected_point_index:
                tolerance_radius = radius + point.tolerance * 20
                painter.setPen(QPen(color, 1, Qt.DashLine))
                painter.setBrush(QBrush())
                painter.drawEllipse(canvas_point, tolerance_radius, tolerance_radius)
    
    def _draw_labels(self, painter: QPainter):
        """Zeichnet Beschriftungen"""
        painter.setPen(QPen(self.current_theme['text'], 1))
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        
        # Titel
        title_rect = QRectF(0, 0, self.width(), 30)
        painter.drawText(title_rect, Qt.AlignCenter, "Energy Curve Editor")
        
        # Achsen-Titel
        painter.save()
        painter.translate(15, self.height() / 2)
        painter.rotate(-90)
        painter.drawText(0, 0, "Energy Level")
        painter.restore()
        
        painter.drawText(
            self.width() / 2 - 50, self.height() - 10,
            "Playlist Position"
        )
    
    def _energy_to_canvas(self, energy_point: EnergyPoint) -> QPointF:
        """Konvertiert Energie-Punkt zu Canvas-Koordinaten"""
        x = self.canvas_rect.left() + energy_point.position * self.canvas_rect.width()
        y = self.canvas_rect.bottom() - (energy_point.energy / 10.0) * self.canvas_rect.height()
        return QPointF(x, y)
    
    def _canvas_to_energy(self, canvas_point: QPointF) -> Tuple[float, float]:
        """Konvertiert Canvas-Koordinaten zu Energie-Werten"""
        position = (canvas_point.x() - self.canvas_rect.left()) / self.canvas_rect.width()
        energy = (self.canvas_rect.bottom() - canvas_point.y()) / self.canvas_rect.height() * 10.0
        
        # Snap to grid wenn aktiviert
        if self.snap_enabled:
            position = round(position * 20) / 20.0  # Snap to 5% grid
            energy = round(energy * 2) / 2.0  # Snap to 0.5 energy grid
        
        return max(0.0, min(1.0, position)), max(0.0, min(10.0, energy))
    
    def _find_point_at_position(self, canvas_point: QPointF) -> int:
        """Findet Punkt an gegebener Canvas-Position"""
        for i, energy_point in enumerate(self.energy_points):
            point_canvas = self._energy_to_canvas(energy_point)
            distance = ((canvas_point.x() - point_canvas.x()) ** 2 + 
                       (canvas_point.y() - point_canvas.y()) ** 2) ** 0.5
            
            if distance <= self.config.point_radius + 5:
                return i
        
        return -1
    
    def _update_cursor(self):
        """Aktualisiert Cursor basierend auf Modus"""
        if self.interaction_mode == 'add':
            self.setCursor(QCursor(Qt.CrossCursor))
        elif self.interaction_mode == 'delete':
            self.setCursor(QCursor(Qt.PointingHandCursor))
        elif self.interaction_mode == 'view':
            self.setCursor(QCursor(Qt.ArrowCursor))
        else:  # edit
            self.setCursor(QCursor(Qt.ArrowCursor))
    
    def _save_to_history(self):
        """Speichert aktuellen Zustand in History"""
        # Entferne zukünftige History wenn wir nicht am Ende sind
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # Füge neuen Zustand hinzu
        state = [point.__dict__.copy() for point in self.energy_points]
        self.history.append(state)
        self.history_index += 1
        
        # Begrenze History-Größe
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1
    
    def undo(self) -> bool:
        """Macht letzte Aktion rückgängig"""
        if self.history_index > 0:
            self.history_index -= 1
            state = self.history[self.history_index]
            
            self.energy_points = [
                EnergyPoint(**point_data) for point_data in state
            ]
            
            self.update()
            self.curve_changed.emit(self.energy_points)
            return True
        return False
    
    def redo(self) -> bool:
        """Wiederholt rückgängig gemachte Aktion"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            state = self.history[self.history_index]
            
            self.energy_points = [
                EnergyPoint(**point_data) for point_data in state
            ]
            
            self.update()
            self.curve_changed.emit(self.energy_points)
            return True
        return False
    
    # Mouse Events
    def mousePressEvent(self, event):
        """Mouse Press Event"""
        if event.button() == Qt.LeftButton:
            canvas_point = QPointF(event.position())
            point_index = self._find_point_at_position(canvas_point)
            
            if self.interaction_mode == 'edit':
                if point_index >= 0:
                    self.selected_point_index = point_index
                    self.dragging_point = True
                    self.point_selected.emit(point_index)
                else:
                    self.selected_point_index = -1
                
            elif self.interaction_mode == 'add':
                if point_index < 0:  # Nur hinzufügen wenn kein Punkt getroffen
                    position, energy = self._canvas_to_energy(canvas_point)
                    new_index = self.add_energy_point(position, energy)
                    self.selected_point_index = new_index
                    self.point_selected.emit(new_index)
                
            elif self.interaction_mode == 'delete':
                if point_index >= 0:
                    self.remove_energy_point(point_index)
            
            self.update()
    
    def mouseMoveEvent(self, event):
        """Mouse Move Event"""
        canvas_point = QPointF(event.position())
        
        # Update Hover-Zustand
        old_hover = self.hover_point_index
        self.hover_point_index = self._find_point_at_position(canvas_point)
        
        if old_hover != self.hover_point_index:
            self.update()
        
        # Dragging
        if self.dragging_point and self.selected_point_index >= 0:
            position, energy = self._canvas_to_energy(canvas_point)
            self.update_energy_point(self.selected_point_index, position, energy)
    
    def mouseReleaseEvent(self, event):
        """Mouse Release Event"""
        if event.button() == Qt.LeftButton:
            if self.dragging_point:
                self._save_to_history()
            self.dragging_point = False
    
    def mouseDoubleClickEvent(self, event):
        """Mouse Double Click Event"""
        if event.button() == Qt.LeftButton and self.interaction_mode == 'edit':
            canvas_point = QPointF(event.position())
            point_index = self._find_point_at_position(canvas_point)
            
            if point_index < 0:  # Füge Punkt hinzu wenn keiner getroffen
                position, energy = self._canvas_to_energy(canvas_point)
                new_index = self.add_energy_point(position, energy)
                self.selected_point_index = new_index
                self.point_selected.emit(new_index)
                self.update()
    
    def wheelEvent(self, event):
        """Wheel Event für Zoom/Scroll"""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom mit Ctrl+Wheel
            delta = event.angleDelta().y()
            if delta > 0:
                self.config.point_radius = min(15, self.config.point_radius + 1)
            else:
                self.config.point_radius = max(5, self.config.point_radius - 1)
            self.update()
    
    def keyPressEvent(self, event):
        """Key Press Event"""
        if event.key() == Qt.Key_Delete and self.selected_point_index >= 0:
            self.remove_energy_point(self.selected_point_index)
        elif event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if event.modifiers() & Qt.ShiftModifier:
                self.redo()
            else:
                self.undo()
        elif event.key() == Qt.Key_Escape:
            self.selected_point_index = -1
            self.update()
    
    # Export/Import
    def export_curve_json(self, file_path: str) -> bool:
        """Exportiert Kurve als JSON"""
        try:
            curve_data = {
                'name': 'custom_curve',
                'created': time.time(),
                'points': [
                    {
                        'position': point.position,
                        'energy': point.energy,
                        'weight': point.weight,
                        'tolerance': point.tolerance
                    }
                    for point in self.energy_points
                ]
            }
            
            with open(file_path, 'w') as f:
                json.dump(curve_data, f, indent=2)
            
            self.curve_exported.emit(file_path)
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Kurve: {e}")
            return False
    
    def import_curve_json(self, file_path: str) -> bool:
        """Importiert Kurve aus JSON"""
        try:
            with open(file_path, 'r') as f:
                curve_data = json.load(f)
            
            points = []
            for point_data in curve_data['points']:
                point = EnergyPoint(
                    position=point_data['position'],
                    energy=point_data['energy'],
                    weight=point_data.get('weight', 1.0),
                    tolerance=point_data.get('tolerance', 0.5)
                )
                points.append(point)
            
            self.set_energy_curve(points)
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Importieren der Kurve: {e}")
            return False
    
    def get_curve_preview_image(self, width: int = 200, height: int = 100) -> QPixmap:
        """Erstellt Vorschau-Bild der Kurve"""
        pixmap = QPixmap(width, height)
        pixmap.fill(self.current_theme['background'])
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Temporäre Canvas-Größe
        old_rect = self.canvas_rect
        self.canvas_rect = QRectF(10, 10, width - 20, height - 20)
        
        # Zeichne nur Kurve
        self._draw_curve(painter)
        
        # Restore
        self.canvas_rect = old_rect
        painter.end()
        
        return pixmap

class EnergyCanvasControlPanel(QWidget):
    """Kontroll-Panel für das Energie-Canvas"""
    
    # Signals
    mode_changed = Signal(str)
    curve_preset_selected = Signal(str)
    export_requested = Signal()
    import_requested = Signal()
    
    def __init__(self, canvas: EnergyCanvasWidget, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup der Kontroll-UI"""
        layout = QVBoxLayout(self)
        
        # Interaktions-Modi
        mode_group = QGroupBox("Interaction Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_buttons = QButtonGroup()
        modes = [
            ('edit', 'Edit Points'),
            ('add', 'Add Points'),
            ('delete', 'Delete Points'),
            ('view', 'View Only')
        ]
        
        for mode, label in modes:
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, m=mode: self._on_mode_changed(m))
            self.mode_buttons.addButton(button)
            mode_layout.addWidget(button)
        
        # Standard: Edit-Modus
        self.mode_buttons.buttons()[0].setChecked(True)
        
        layout.addWidget(mode_group)
        
        # Curve Presets
        preset_group = QGroupBox("Curve Presets")
        preset_layout = QVBoxLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            'Progressive Build',
            'Peak Time',
            'Cool Down',
            'Wave Pattern',
            'Custom'
        ])
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        layout.addWidget(preset_group)
        
        # Canvas-Einstellungen
        settings_group = QGroupBox("Canvas Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Grid
        self.grid_checkbox = QCheckBox("Show Grid")
        self.grid_checkbox.setChecked(True)
        self.grid_checkbox.toggled.connect(self.canvas.set_grid_visible)
        settings_layout.addWidget(self.grid_checkbox, 0, 0)
        
        # Snap
        self.snap_checkbox = QCheckBox("Snap to Grid")
        self.snap_checkbox.setChecked(True)
        self.snap_checkbox.toggled.connect(self.canvas.set_snap_enabled)
        settings_layout.addWidget(self.snap_checkbox, 0, 1)
        
        # Theme
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['dark', 'light'])
        self.theme_combo.currentTextChanged.connect(self.canvas.set_theme)
        settings_layout.addWidget(theme_label, 1, 0)
        settings_layout.addWidget(self.theme_combo, 1, 1)
        
        layout.addWidget(settings_group)
        
        # Point-Details
        point_group = QGroupBox("Selected Point")
        point_layout = QGridLayout(point_group)
        
        # Position
        point_layout.addWidget(QLabel("Position:"), 0, 0)
        self.position_spinbox = QDoubleSpinBox()
        self.position_spinbox.setRange(0.0, 1.0)
        self.position_spinbox.setSingleStep(0.05)
        self.position_spinbox.setDecimals(2)
        self.position_spinbox.valueChanged.connect(self._on_point_position_changed)
        point_layout.addWidget(self.position_spinbox, 0, 1)
        
        # Energy
        point_layout.addWidget(QLabel("Energy:"), 1, 0)
        self.energy_spinbox = QDoubleSpinBox()
        self.energy_spinbox.setRange(0.0, 10.0)
        self.energy_spinbox.setSingleStep(0.5)
        self.energy_spinbox.setDecimals(1)
        self.energy_spinbox.valueChanged.connect(self._on_point_energy_changed)
        point_layout.addWidget(self.energy_spinbox, 1, 1)
        
        # Tolerance
        point_layout.addWidget(QLabel("Tolerance:"), 2, 0)
        self.tolerance_spinbox = QDoubleSpinBox()
        self.tolerance_spinbox.setRange(0.1, 2.0)
        self.tolerance_spinbox.setSingleStep(0.1)
        self.tolerance_spinbox.setDecimals(1)
        self.tolerance_spinbox.valueChanged.connect(self._on_point_tolerance_changed)
        point_layout.addWidget(self.tolerance_spinbox, 2, 1)
        
        layout.addWidget(point_group)
        
        # Actions
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout(action_group)
        
        # Undo/Redo
        undo_redo_layout = QHBoxLayout()
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self.canvas.undo)
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self.canvas.redo)
        undo_redo_layout.addWidget(self.undo_button)
        undo_redo_layout.addWidget(self.redo_button)
        action_layout.addLayout(undo_redo_layout)
        
        # Export/Import
        export_import_layout = QHBoxLayout()
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self._on_export_clicked)
        self.import_button = QPushButton("Import")
        self.import_button.clicked.connect(self._on_import_clicked)
        export_import_layout.addWidget(self.export_button)
        export_import_layout.addWidget(self.import_button)
        action_layout.addLayout(export_import_layout)
        
        layout.addWidget(action_group)
        
        # Stretch
        layout.addStretch()
    
    def _connect_signals(self):
        """Verbindet Signals"""
        self.canvas.point_selected.connect(self._on_point_selected)
        self.canvas.curve_changed.connect(self._on_curve_changed)
    
    def _on_mode_changed(self, mode: str):
        """Mode-Änderung"""
        self.canvas.set_interaction_mode(mode)
        self.mode_changed.emit(mode)
    
    def _on_preset_changed(self, preset_name: str):
        """Preset-Änderung"""
        preset_curves = {
            'Progressive Build': [
                EnergyPoint(0.0, 3.0, 1.0, 0.5),
                EnergyPoint(0.3, 5.0, 1.2, 0.4),
                EnergyPoint(0.6, 7.0, 1.4, 0.3),
                EnergyPoint(1.0, 9.0, 1.8, 0.2)
            ],
            'Peak Time': [
                EnergyPoint(0.0, 8.0, 1.5, 0.3),
                EnergyPoint(0.25, 9.0, 2.0, 0.2),
                EnergyPoint(0.75, 9.0, 2.0, 0.2),
                EnergyPoint(1.0, 8.5, 1.5, 0.3)
            ],
            'Cool Down': [
                EnergyPoint(0.0, 8.0, 1.5, 0.3),
                EnergyPoint(0.4, 6.0, 1.2, 0.4),
                EnergyPoint(0.8, 4.0, 0.8, 0.6),
                EnergyPoint(1.0, 2.0, 0.5, 0.8)
            ],
            'Wave Pattern': [
                EnergyPoint(0.0, 5.0, 1.0, 0.5),
                EnergyPoint(0.2, 7.5, 1.5, 0.3),
                EnergyPoint(0.4, 5.5, 1.0, 0.4),
                EnergyPoint(0.6, 8.0, 1.8, 0.2),
                EnergyPoint(0.8, 6.0, 1.2, 0.4),
                EnergyPoint(1.0, 7.0, 1.4, 0.3)
            ]
        }
        
        if preset_name in preset_curves:
            self.canvas.set_energy_curve(preset_curves[preset_name])
            self.curve_preset_selected.emit(preset_name)
    
    def _on_point_selected(self, index: int):
        """Point-Selektion"""
        if 0 <= index < len(self.canvas.energy_points):
            point = self.canvas.energy_points[index]
            
            # Update Spinboxes
            self.position_spinbox.blockSignals(True)
            self.energy_spinbox.blockSignals(True)
            self.tolerance_spinbox.blockSignals(True)
            
            self.position_spinbox.setValue(point.position)
            self.energy_spinbox.setValue(point.energy)
            self.tolerance_spinbox.setValue(point.tolerance)
            
            self.position_spinbox.blockSignals(False)
            self.energy_spinbox.blockSignals(False)
            self.tolerance_spinbox.blockSignals(False)
    
    def _on_curve_changed(self, energy_points: List[EnergyPoint]):
        """Kurven-Änderung"""
        # Update UI wenn nötig
        pass
    
    def _on_point_position_changed(self, value: float):
        """Position-Änderung"""
        if self.canvas.selected_point_index >= 0:
            point = self.canvas.energy_points[self.canvas.selected_point_index]
            self.canvas.update_energy_point(
                self.canvas.selected_point_index,
                value,
                point.energy
            )
    
    def _on_point_energy_changed(self, value: float):
        """Energie-Änderung"""
        if self.canvas.selected_point_index >= 0:
            point = self.canvas.energy_points[self.canvas.selected_point_index]
            self.canvas.update_energy_point(
                self.canvas.selected_point_index,
                point.position,
                value
            )
    
    def _on_point_tolerance_changed(self, value: float):
        """Toleranz-Änderung"""
        if self.canvas.selected_point_index >= 0:
            self.canvas.energy_points[self.canvas.selected_point_index].tolerance = value
            self.canvas.update()
    
    def _on_export_clicked(self):
        """Export-Button geklickt"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Energy Curve",
            "energy_curve.json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.canvas.export_curve_json(file_path):
                QMessageBox.information(self, "Export", "Curve exported successfully!")
            else:
                QMessageBox.warning(self, "Export", "Failed to export curve!")
    
    def _on_import_clicked(self):
        """Import-Button geklickt"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Energy Curve",
            "",
            "JSON Files (*.json)"
        )
        
        if file_path:
            if self.canvas.import_curve_json(file_path):
                QMessageBox.information(self, "Import", "Curve imported successfully!")
            else:
                QMessageBox.warning(self, "Import", "Failed to import curve!")

class EnergyCanvasMainWidget(QWidget):
    """Haupt-Widget das Canvas und Kontroll-Panel kombiniert"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup der Haupt-UI"""
        layout = QHBoxLayout(self)
        
        # Canvas
        self.canvas = EnergyCanvasWidget()
        
        # Kontroll-Panel
        self.control_panel = EnergyCanvasControlPanel(self.canvas)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.control_panel)
        splitter.setStretchFactor(0, 3)  # Canvas bekommt mehr Platz
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
    
    def get_energy_curve(self) -> List[EnergyPoint]:
        """Gibt aktuelle Energie-Kurve zurück"""
        return self.canvas.get_energy_curve()
    
    def set_energy_curve(self, energy_points: List[EnergyPoint]):
        """Setzt Energie-Kurve"""
        self.canvas.set_energy_curve(energy_points)

# Demo/Test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = EnergyCanvasMainWidget()
    window.setWindowTitle("Energy Curve Canvas - Demo")
    window.resize(1200, 600)
    window.show()
    
    sys.exit(app.exec())