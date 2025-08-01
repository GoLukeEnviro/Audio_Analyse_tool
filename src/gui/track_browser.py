"""Track Browser Widget - Anzeige und Verwaltung der analysierten Tracks"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QLineEdit, QComboBox, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import os


class TrackBrowser(QWidget):
    """Widget für die Anzeige und Verwaltung der analysierten Tracks"""
    
    track_selected = Signal(dict)  # Signal wenn Track ausgewählt wird
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tracks_data = []
        self.filtered_tracks = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup der Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Filter-Bereich
        filter_layout = QHBoxLayout()
        
        # Such-Filter
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Track name, artist, key...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        # BPM Filter
        filter_layout.addWidget(QLabel("BPM:"))
        self.bpm_filter = QComboBox()
        self.bpm_filter.addItems(["All", "< 120", "120-130", "130-140", "> 140"])
        self.bpm_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.bpm_filter)
        
        # Key Filter
        filter_layout.addWidget(QLabel("Key:"))
        self.key_filter = QComboBox()
        self.key_filter.addItem("All")
        self.key_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.key_filter)
        
        # Clear Filter Button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Track-Tabelle
        self.track_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.track_table)
        
        # Status-Label
        self.status_label = QLabel("No tracks loaded")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.status_label)
        
    def setup_table(self):
        """Setup der Track-Tabelle"""
        headers = [
            "Track", "Artist", "BPM", "Key", "Camelot", 
            "Energy", "Mood", "Duration", "Path"
        ]
        
        self.track_table.setColumnCount(len(headers))
        self.track_table.setHorizontalHeaderLabels(headers)
        
        # Header-Styling
        header = self.track_table.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #3a3a3a;
                color: white;
                padding: 8px;
                border: 1px solid #555;
                font-weight: bold;
            }
        """)
        
        # Spalten-Größen
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Track
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Artist
        header.resizeSection(2, 80)   # BPM
        header.resizeSection(3, 80)   # Key
        header.resizeSection(4, 80)   # Camelot
        header.resizeSection(5, 80)   # Energy
        header.resizeSection(6, 100)  # Mood
        header.resizeSection(7, 80)   # Duration
        header.setSectionResizeMode(8, QHeaderView.Stretch)  # Path
        
        # Tabellen-Styling
        self.track_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: white;
                gridline-color: #555;
                selection-background-color: #0078d4;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
        """)
        
        # Selection-Handler
        self.track_table.itemSelectionChanged.connect(self.on_track_selected)
        
    def load_tracks(self, tracks_data):
        """Lädt Track-Daten in den Browser"""
        self.tracks_data = tracks_data
        self.filtered_tracks = tracks_data.copy()
        
        # Key-Filter aktualisieren
        keys = set()
        for track in tracks_data:
            if track.get('key'):
                keys.add(track['key'])
        
        self.key_filter.clear()
        self.key_filter.addItem("All")
        for key in sorted(keys):
            self.key_filter.addItem(key)
        
        self.update_table()
        
    def update_table(self):
        """Aktualisiert die Tabellen-Anzeige"""
        self.track_table.setRowCount(len(self.filtered_tracks))
        
        for row, track in enumerate(self.filtered_tracks):
            # Track Name
            track_name = os.path.splitext(os.path.basename(track['file_path']))[0]
            self.track_table.setItem(row, 0, QTableWidgetItem(track_name))
            
            # Artist (falls verfügbar)
            artist = track.get('artist', 'Unknown')
            self.track_table.setItem(row, 1, QTableWidgetItem(artist))
            
            # BPM
            bpm = f"{track.get('bpm', 0):.0f}" if track.get('bpm') else "N/A"
            self.track_table.setItem(row, 2, QTableWidgetItem(bpm))
            
            # Key
            key = track.get('key', 'N/A')
            self.track_table.setItem(row, 3, QTableWidgetItem(key))
            
            # Camelot
            camelot = track.get('camelot', 'N/A')
            self.track_table.setItem(row, 4, QTableWidgetItem(camelot))
            
            # Energy
            energy = f"{track.get('energy', 0):.2f}" if track.get('energy') else "N/A"
            self.track_table.setItem(row, 5, QTableWidgetItem(energy))
            
            # Mood
            mood = track.get('mood', 'Unknown')
            self.track_table.setItem(row, 6, QTableWidgetItem(mood))
            
            # Duration
            duration = track.get('duration', 0)
            duration_str = f"{int(duration//60)}:{int(duration%60):02d}" if duration else "N/A"
            self.track_table.setItem(row, 7, QTableWidgetItem(duration_str))
            
            # Path
            path = track.get('file_path', '')
            self.track_table.setItem(row, 8, QTableWidgetItem(path))
        
        # Status aktualisieren
        total = len(self.tracks_data)
        filtered = len(self.filtered_tracks)
        if total == 0:
            self.status_label.setText("No tracks loaded")
        elif filtered == total:
            self.status_label.setText(f"Showing {total} tracks")
        else:
            self.status_label.setText(f"Showing {filtered} of {total} tracks")
    
    def apply_filters(self):
        """Wendet die aktuellen Filter an"""
        search_text = self.search_input.text().lower()
        bpm_filter = self.bpm_filter.currentText()
        key_filter = self.key_filter.currentText()
        
        self.filtered_tracks = []
        
        for track in self.tracks_data:
            # Such-Filter
            if search_text:
                track_name = os.path.splitext(os.path.basename(track['file_path']))[0].lower()
                artist = track.get('artist', '').lower()
                key = track.get('key', '').lower()
                
                if not (search_text in track_name or search_text in artist or search_text in key):
                    continue
            
            # BPM-Filter
            if bpm_filter != "All":
                bpm = track.get('bpm', 0)
                if bpm_filter == "< 120" and bpm >= 120:
                    continue
                elif bpm_filter == "120-130" and not (120 <= bpm <= 130):
                    continue
                elif bpm_filter == "130-140" and not (130 <= bpm <= 140):
                    continue
                elif bpm_filter == "> 140" and bpm <= 140:
                    continue
            
            # Key-Filter
            if key_filter != "All":
                if track.get('key') != key_filter:
                    continue
            
            self.filtered_tracks.append(track)
        
        self.update_table()
    
    def clear_filters(self):
        """Löscht alle Filter"""
        self.search_input.clear()
        self.bpm_filter.setCurrentText("All")
        self.key_filter.setCurrentText("All")
        self.apply_filters()
    
    def on_track_selected(self):
        """Handler für Track-Auswahl"""
        current_row = self.track_table.currentRow()
        if 0 <= current_row < len(self.filtered_tracks):
            selected_track = self.filtered_tracks[current_row]
            self.track_selected.emit(selected_track)
    
    def get_selected_track(self):
        """Gibt den aktuell ausgewählten Track zurück"""
        current_row = self.track_table.currentRow()
        if 0 <= current_row < len(self.filtered_tracks):
            return self.filtered_tracks[current_row]
        return None
    
    def get_all_tracks(self):
        """Gibt alle geladenen Tracks zurück"""
        return self.tracks_data.copy()
    
    def get_filtered_tracks(self):
        """Gibt die aktuell gefilterten Tracks zurück"""
        return self.filtered_tracks.copy()