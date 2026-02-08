"""
Control panel widget for Pathfinder GUI.
Provides file loading, analysis controls, and settings access.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QGroupBox, QFileDialog,
    QDoubleSpinBox, QFormLayout
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
    load_folder_requested = pyqtSignal()
    spatial_params_changed = pyqtSignal(dict)
    
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

        # Spatial Parameters Group
        spatial_group = self._create_spatial_params_group()
        layout.addWidget(spatial_group)

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

        # Initial state (call after all widgets are created)
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

    def _on_load_folder_clicked(self):
        self.load_folder_requested.emit()

    def _create_spatial_params_group(self):
        """Create spatial parameters group"""
        group = QGroupBox("Maze Geometry")
        layout = QFormLayout()

        # Pool center X
        self.pool_center_x_spin = QDoubleSpinBox()
        self.pool_center_x_spin.setRange(0, 10000)
        self.pool_center_x_spin.setValue(250.0)
        self.pool_center_x_spin.setSuffix(" px")
        self.pool_center_x_spin.setDecimals(1)
        self.pool_center_x_spin.valueChanged.connect(self._on_spatial_param_changed)
        layout.addRow("Pool Center X:", self.pool_center_x_spin)

        # Pool center Y
        self.pool_center_y_spin = QDoubleSpinBox()
        self.pool_center_y_spin.setRange(0, 10000)
        self.pool_center_y_spin.setValue(250.0)
        self.pool_center_y_spin.setSuffix(" px")
        self.pool_center_y_spin.setDecimals(1)
        self.pool_center_y_spin.valueChanged.connect(self._on_spatial_param_changed)
        layout.addRow("Pool Center Y:", self.pool_center_y_spin)

        # Pool diameter
        self.pool_diameter_spin = QDoubleSpinBox()
        self.pool_diameter_spin.setRange(10, 10000)
        self.pool_diameter_spin.setValue(500.0)
        self.pool_diameter_spin.setSuffix(" px")
        self.pool_diameter_spin.setDecimals(1)
        self.pool_diameter_spin.valueChanged.connect(self._on_spatial_param_changed)
        layout.addRow("Pool Diameter:", self.pool_diameter_spin)

        # Platform X
        self.platform_x_spin = QDoubleSpinBox()
        self.platform_x_spin.setRange(0, 10000)
        self.platform_x_spin.setValue(350.0)
        self.platform_x_spin.setSuffix(" px")
        self.platform_x_spin.setDecimals(1)
        self.platform_x_spin.valueChanged.connect(self._on_spatial_param_changed)
        layout.addRow("Platform X:", self.platform_x_spin)

        # Platform Y
        self.platform_y_spin = QDoubleSpinBox()
        self.platform_y_spin.setRange(0, 10000)
        self.platform_y_spin.setValue(150.0)
        self.platform_y_spin.setSuffix(" px")
        self.platform_y_spin.setDecimals(1)
        self.platform_y_spin.valueChanged.connect(self._on_spatial_param_changed)
        layout.addRow("Platform Y:", self.platform_y_spin)

        # Platform diameter
        self.platform_diameter_spin = QDoubleSpinBox()
        self.platform_diameter_spin.setRange(1, 1000)
        self.platform_diameter_spin.setValue(50.0)
        self.platform_diameter_spin.setSuffix(" px")
        self.platform_diameter_spin.setDecimals(1)
        self.platform_diameter_spin.valueChanged.connect(self._on_spatial_param_changed)
        layout.addRow("Platform Diameter:", self.platform_diameter_spin)

        # Apply button
        apply_btn = QPushButton("Apply Geometry")
        apply_btn.setMinimumHeight(30)
        apply_btn.clicked.connect(self._on_spatial_params_apply)
        layout.addRow(apply_btn)

        # Info labels
        info_label = QLabel("💡 Visualization updates automatically as you adjust values")
        info_label.setStyleSheet("color: #0066cc; font-size: 9pt; font-style: italic;")
        info_label.setWordWrap(True)
        layout.addRow(info_label)

        info_label2 = QLabel("Click 'Apply Geometry' to update loaded trials")
        info_label2.setStyleSheet("color: #666; font-size: 9pt; font-style: italic;")
        info_label2.setWordWrap(True)
        layout.addRow(info_label2)

        group.setLayout(layout)
        return group

    def _get_current_spatial_params(self):
        """Get current spatial parameter values as dict"""
        return {
            'pool_center_x': self.pool_center_x_spin.value(),
            'pool_center_y': self.pool_center_y_spin.value(),
            'pool_diameter': self.pool_diameter_spin.value(),
            'platform_x': self.platform_x_spin.value(),
            'platform_y': self.platform_y_spin.value(),
            'platform_diameter': self.platform_diameter_spin.value()
        }

    def _on_spatial_param_changed(self):
        """Handle individual spinbox value change - update visualization only"""
        # Emit signal for live visualization update
        # Note: This does NOT apply to trials, only updates the display
        params = self._get_current_spatial_params()
        self.spatial_params_changed.emit(params)

    def _on_spatial_params_apply(self):
        """Emit signal to apply spatial parameters to loaded trials"""
        # This applies parameters to all trials in the experiment
        params = self._get_current_spatial_params()
        self.spatial_params_changed.emit(params)

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
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
