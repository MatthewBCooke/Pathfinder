"""
Control panel widget for Pathfinder GUI.
Provides file loading, analysis controls, and settings access.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QGroupBox, QFileDialog
)
from PyQt5.QtCore import pyqtSignal, Qt
from pathlib import Path


class ControlPanelWidget(QWidget):
    """
    Left sidebar control panel with:
    - File loading
    - Analysis controls
    - Settings access
    - Progress display
    """
    
    # Signals
    load_clicked = pyqtSignal()
    analyze_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file = None
        self._is_analyzing = False
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # File Operations Group
        file_group = self._create_file_group()
        layout.addWidget(file_group)
        
        # Analysis Controls Group
        analysis_group = self._create_analysis_group()
        layout.addWidget(analysis_group)
        
        # Progress Section
        progress_group = self._create_progress_group()
        layout.addWidget(progress_group)
        
        # Settings Group
        settings_group = self._create_settings_group()
        layout.addWidget(settings_group)
        
        # Stretch to push everything to the top
        layout.addStretch()
        
        # Initial state
        self._update_button_states()
    
    def _create_file_group(self):
        """Create file operations group"""
        group = QGroupBox("File Operations")
        layout = QVBoxLayout()
        

        # Load File button
        self.load_btn = QPushButton("📁 Load Experiment File")
        self.load_btn.setMinimumHeight(40)
        self.load_btn.clicked.connect(self._on_load_clicked)
        layout.addWidget(self.load_btn)

        # Load Folder button
        self.load_folder_btn = QPushButton("📂 Load Folder of Trials")
        self.load_folder_btn.setMinimumHeight(40)
        self.load_folder_btn.clicked.connect(self._on_load_folder_clicked)
        layout.addWidget(self.load_folder_btn)
            def _on_load_folder_clicked(self):
                self.parent().load_folder_requested.emit()

            # Add a new signal for folder loading
            load_folder_requested = pyqtSignal()
        
        # Current file label
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.file_label)
        
        # Export button
        self.export_btn = QPushButton("💾 Export Results")
        self.export_btn.clicked.connect(self.export_clicked.emit)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_analysis_group(self):
        """Create analysis controls group"""
        group = QGroupBox("Analysis")
        layout = QVBoxLayout()
        
        # Analyze button
        self.analyze_btn = QPushButton("▶ Run Analysis")
        self.analyze_btn.setMinimumHeight(50)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)
        
        # Stop button (hidden initially)
        self.stop_btn = QPushButton("⏹ Stop Analysis")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_btn.setVisible(False)
        layout.addWidget(self.stop_btn)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 11px; color: #555;")
        layout.addWidget(self.status_label)
        
        group.setLayout(layout)
        return group
    
    def _create_progress_group(self):
        """Create progress display group"""
        group = QGroupBox("Progress")
        layout = QVBoxLayout()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Progress label (detail)
        self.progress_label = QLabel("Waiting...")
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.progress_label)
        
        group.setLayout(layout)
        return group
    
    def _create_settings_group(self):
        """Create settings group"""
        group = QGroupBox("Configuration")
        layout = QVBoxLayout()
        
        # Settings button
        self.settings_btn = QPushButton("⚙ Analysis Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)
        
        # Parameters summary
        self.params_label = QLabel("Using default parameters")
        self.params_label.setWordWrap(True)
        self.params_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(self.params_label)
        
        group.setLayout(layout)
        return group
    
    def _on_load_clicked(self):
        """Handle load button click"""
        self.load_clicked.emit()
    
    def _on_analyze_clicked(self):
        """Handle analyze button click"""
        if not self._is_analyzing:
            self.analyze_clicked.emit()
    
    def _update_button_states(self):
        """Update button enabled states based on current state"""
        has_file = self._current_file is not None
        
        self.analyze_btn.setEnabled(has_file and not self._is_analyzing)
        self.export_btn.setEnabled(has_file)
        self.load_btn.setEnabled(not self._is_analyzing)
        self.settings_btn.setEnabled(not self._is_analyzing)
    
    # Public methods for external control
    
    def set_file_loaded(self, file_path: Path):
        """Update UI when a file is loaded"""
        self._current_file = file_path
        self.file_label.setText(f"📄 {file_path.name}")
        self.file_label.setStyleSheet("color: black; font-size: 10px;")
        self.status_label.setText("File loaded - Ready to analyze")
        self._update_button_states()
    
    def set_analyzing(self, is_analyzing: bool):
        """Update UI when analysis state changes"""
        self._is_analyzing = is_analyzing
        
        if is_analyzing:
            self.analyze_btn.setVisible(False)
            self.stop_btn.setVisible(True)
            self.status_label.setText("⏳ Analyzing...")
            self.status_label.setStyleSheet("font-size: 11px; color: #FF9800; font-weight: bold;")
        else:
            self.analyze_btn.setVisible(True)
            self.stop_btn.setVisible(False)
            self.status_label.setText("✓ Analysis complete")
            self.status_label.setStyleSheet("font-size: 11px; color: #4CAF50; font-weight: bold;")
        
        self._update_button_states()
    
    def set_progress(self, value: int, text: str = ""):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        if text:
            self.progress_label.setText(text)
    
    def set_parameters_summary(self, text: str):
        """Update parameters summary label"""
        self.params_label.setText(text)
    
    def reset(self):
        """Reset to initial state"""
        self._current_file = None
        self._is_analyzing = False
        self.file_label.setText("No file loaded")
        self.file_label.setStyleSheet("color: gray; font-size: 10px;")
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("font-size: 11px; color: #555;")
        self.progress_bar.setValue(0)
        self.progress_label.setText("Waiting...")
        self._update_button_states()
