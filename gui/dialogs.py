"""
Dialog windows for Pathfinder PyQt6 GUI.

Contains:
- SettingsDialog: Application settings with Analysis, Visualization, and I/O tabs
- FileImportDialog: Import tracking data from various software formats
- ManualStrategyDialog: Manually classify a trial strategy
- ExportDialog: Export analysis results in various formats
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QSlider, QComboBox,
    QFileDialog, QTextEdit, QScrollArea, QWidget, QGroupBox,
    QSpinBox, QDoubleSpinBox, QMessageBox, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QIntValidator

from pathfinder import Parameters


class SettingsDialog(QDialog):
    """
    Settings dialog with tabbed interface for configuring analysis parameters,
    visualization options, and file I/O preferences.
    """
    
    settings_applied = pyqtSignal(object)  # Emits updated Parameters object
    
    def __init__(self, current_params: Parameters, parent: Optional[QWidget] = None):
        """
        Initialize the settings dialog.
        
        Args:
            current_params: Current Parameters object to display/edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.params = current_params
        self.param_widgets: Dict[str, Any] = {}
        
        self.setWindowTitle("Pathfinder Settings")
        self.setMinimumSize(700, 600)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self._create_analysis_tab(), "Analysis Parameters")
        self.tab_widget.addTab(self._create_visualization_tab(), "Visualization")
        self.tab_widget.addTab(self._create_io_tab(), "File I/O")
        
        layout.addWidget(self.tab_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        apply_btn.setDefault(True)
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _create_analysis_tab(self) -> QWidget:
        """Create the Analysis Parameters tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Scrollable area for all parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Strategy enable/disable group
        strategy_group = QGroupBox("Strategy Detection")
        strategy_layout = QGridLayout()
        
        strategies = [
            'direct_enabled', 'focal_enabled', 'directed_enabled',
            'chaining_enabled', 'scanning_enabled', 'thigmotaxis_enabled',
            'random_enabled', 'perseverative_enabled'
        ]
        
        row = 0
        for i, strategy in enumerate(strategies):
            label = strategy.replace('_enabled', '').replace('_', ' ').title()
            checkbox = QCheckBox(label)
            checkbox.setChecked(getattr(self.params, strategy, True))
            self.param_widgets[strategy] = checkbox
            strategy_layout.addWidget(checkbox, row, i % 2)
            if i % 2 == 1:
                row += 1
        
        strategy_group.setLayout(strategy_layout)
        scroll_layout.addWidget(strategy_group)
        
        # Threshold parameters
        threshold_group = QGroupBox("Threshold Parameters")
        threshold_layout = QGridLayout()
        
        # Define all threshold parameters with their labels and default ranges
        thresholds = [
            ('direct_latency_threshold', 'Direct Latency (s)', 0.0, 100.0, 2),
            ('direct_path_efficiency_threshold', 'Direct Path Efficiency', 0.0, 1.0, 2),
            ('focal_time_threshold', 'Focal Time %', 0.0, 100.0, 1),
            ('focal_area_ratio_threshold', 'Focal Area Ratio', 0.0, 1.0, 2),
            ('directed_angle_threshold', 'Directed Angle (deg)', 0.0, 180.0, 1),
            ('directed_efficiency_threshold', 'Directed Efficiency', 0.0, 1.0, 2),
            ('chaining_heading_change_threshold', 'Chaining Heading Change', 0.0, 180.0, 1),
            ('chaining_distance_threshold', 'Chaining Distance (cm)', 0.0, 200.0, 1),
            ('scanning_coverage_threshold', 'Scanning Coverage %', 0.0, 100.0, 1),
            ('scanning_speed_threshold', 'Scanning Speed (cm/s)', 0.0, 100.0, 1),
            ('thigmotaxis_wall_distance_threshold', 'Thigmotaxis Wall Distance (cm)', 0.0, 50.0, 1),
            ('thigmotaxis_time_threshold', 'Thigmotaxis Time %', 0.0, 100.0, 1),
            ('random_turn_angle_threshold', 'Random Turn Angle (deg)', 0.0, 180.0, 1),
            ('random_entropy_threshold', 'Random Entropy', 0.0, 10.0, 2),
            ('perseverative_quadrant_time_threshold', 'Perseverative Quadrant Time %', 0.0, 100.0, 1),
            ('perseverative_return_count_threshold', 'Perseverative Return Count', 0, 50, 0),
            ('velocity_threshold', 'Velocity Threshold (cm/s)', 0.0, 100.0, 1),
            ('immobility_threshold', 'Immobility Threshold (s)', 0.0, 60.0, 1),
            ('platform_radius', 'Platform Radius (cm)', 0.0, 50.0, 1),
            ('pool_radius', 'Pool Radius (cm)', 0.0, 500.0, 1),
            ('zone_radius', 'Zone Radius (cm)', 0.0, 200.0, 1),
            ('min_trial_duration', 'Min Trial Duration (s)', 0.0, 300.0, 1),
            ('max_trial_duration', 'Max Trial Duration (s)', 0.0, 300.0, 1),
        ]
        
        for row, (param_name, label, min_val, max_val, decimals) in enumerate(thresholds):
            param_label = QLabel(label + ":")
            threshold_layout.addWidget(param_label, row, 0)
            
            if decimals == 0:
                spinbox = QSpinBox()
                spinbox.setRange(int(min_val), int(max_val))
                spinbox.setValue(int(getattr(self.params, param_name, 0)))
            else:
                spinbox = QDoubleSpinBox()
                spinbox.setRange(min_val, max_val)
                spinbox.setDecimals(decimals)
                spinbox.setValue(float(getattr(self.params, param_name, 0.0)))
            
            self.param_widgets[param_name] = spinbox
            threshold_layout.addWidget(spinbox, row, 1)
        
        threshold_group.setLayout(threshold_layout)
        scroll_layout.addWidget(threshold_group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        
        layout.addWidget(scroll)
        tab.setLayout(layout)
        return tab
    
    def _create_visualization_tab(self) -> QWidget:
        """Create the Visualization Options tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Heatmap grid size
        grid_size_layout = QHBoxLayout()
        grid_size_layout.addWidget(QLabel("Heatmap Grid Size:"))
        self.grid_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.grid_size_slider.setRange(10, 100)
        self.grid_size_slider.setValue(getattr(self.params, 'heatmap_grid_size', 50))
        self.grid_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.grid_size_slider.setTickInterval(10)
        self.grid_size_value_label = QLabel(str(self.grid_size_slider.value()))
        self.grid_size_slider.valueChanged.connect(
            lambda v: self.grid_size_value_label.setText(str(v))
        )
        grid_size_layout.addWidget(self.grid_size_slider)
        grid_size_layout.addWidget(self.grid_size_value_label)
        layout.addLayout(grid_size_layout)
        
        # Gaussian sigma
        sigma_layout = QHBoxLayout()
        sigma_layout.addWidget(QLabel("Gaussian Sigma:"))
        self.sigma_slider = QSlider(Qt.Orientation.Horizontal)
        self.sigma_slider.setRange(5, 50)  # 0.5 to 5.0, multiplied by 10
        sigma_value = getattr(self.params, 'gaussian_sigma', 2.0)
        self.sigma_slider.setValue(int(sigma_value * 10))
        self.sigma_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sigma_slider.setTickInterval(5)
        self.sigma_value_label = QLabel(f"{sigma_value:.1f}")
        self.sigma_slider.valueChanged.connect(
            lambda v: self.sigma_value_label.setText(f"{v/10:.1f}")
        )
        sigma_layout.addWidget(self.sigma_slider)
        sigma_layout.addWidget(self.sigma_value_label)
        layout.addLayout(sigma_layout)
        
        # Color scheme
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color Scheme:"))
        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.addItems([
            'viridis', 'plasma', 'inferno', 'magma', 'cividis',
            'hot', 'coolwarm', 'jet', 'rainbow'
        ])
        current_scheme = getattr(self.params, 'color_scheme', 'viridis')
        index = self.color_scheme_combo.findText(current_scheme)
        if index >= 0:
            self.color_scheme_combo.setCurrentIndex(index)
        color_layout.addWidget(self.color_scheme_combo)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _create_io_tab(self) -> QWidget:
        """Create the File I/O Options tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Auto-save results
        self.autosave_checkbox = QCheckBox("Auto-save results after analysis")
        self.autosave_checkbox.setChecked(getattr(self.params, 'autosave', False))
        layout.addWidget(self.autosave_checkbox)
        
        # Export format
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Default Export Format:"))
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(['CSV', 'Excel', 'JSON'])
        current_format = getattr(self.params, 'export_format', 'CSV')
        index = self.export_format_combo.findText(current_format)
        if index >= 0:
            self.export_format_combo.setCurrentIndex(index)
        export_layout.addWidget(self.export_format_combo)
        export_layout.addStretch()
        layout.addLayout(export_layout)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def _reset_to_defaults(self) -> None:
        """Reset all parameters to default values."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.params = Parameters()  # Create new default Parameters
            self._update_ui_from_params()
    
    def _update_ui_from_params(self) -> None:
        """Update all UI widgets from current parameters."""
        # Update all param widgets
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, QCheckBox):
                widget.setChecked(getattr(self.params, param_name, False))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(getattr(self.params, param_name, 0))
        
        # Update visualization widgets
        self.grid_size_slider.setValue(getattr(self.params, 'heatmap_grid_size', 50))
        sigma_value = getattr(self.params, 'gaussian_sigma', 2.0)
        self.sigma_slider.setValue(int(sigma_value * 10))
        
        scheme = getattr(self.params, 'color_scheme', 'viridis')
        index = self.color_scheme_combo.findText(scheme)
        if index >= 0:
            self.color_scheme_combo.setCurrentIndex(index)
        
        # Update I/O widgets
        self.autosave_checkbox.setChecked(getattr(self.params, 'autosave', False))
        fmt = getattr(self.params, 'export_format', 'CSV')
        index = self.export_format_combo.findText(fmt)
        if index >= 0:
            self.export_format_combo.setCurrentIndex(index)
    
    def _apply_settings(self) -> None:
        """Apply settings and emit updated Parameters object."""
        # Update params from widgets
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, QCheckBox):
                setattr(self.params, param_name, widget.isChecked())
            elif isinstance(widget, QSpinBox):
                setattr(self.params, param_name, widget.value())
            elif isinstance(widget, QDoubleSpinBox):
                setattr(self.params, param_name, widget.value())
        
        # Update visualization params
        setattr(self.params, 'heatmap_grid_size', self.grid_size_slider.value())
        setattr(self.params, 'gaussian_sigma', self.sigma_slider.value() / 10.0)
        setattr(self.params, 'color_scheme', self.color_scheme_combo.currentText())
        
        # Update I/O params
        setattr(self.params, 'autosave', self.autosave_checkbox.isChecked())
        setattr(self.params, 'export_format', self.export_format_combo.currentText())
        
        self.settings_applied.emit(self.params)
        self.accept()


class FileImportDialog(QDialog):
    """
    Dialog for importing tracking data from various software formats.
    """
    
    file_imported = pyqtSignal(str, str, list)  # software_type, path, preview_data
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the file import dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_path: Optional[str] = None
        
        self.setWindowTitle("Import Tracking Data")
        self.setMinimumSize(600, 400)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Software type selector
        software_layout = QHBoxLayout()
        software_layout.addWidget(QLabel("Software Type:"))
        self.software_combo = QComboBox()
        self.software_combo.addItems([
            'Ethovision',
            'AnyMaze',
            'WaterMaze',
            'EZTrack',
            'Custom'
        ])
        software_layout.addWidget(self.software_combo)
        software_layout.addStretch()
        layout.addLayout(software_layout)
        
        # File/Directory browser
        browser_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select file or directory...")
        self.path_edit.setReadOnly(True)
        browser_layout.addWidget(self.path_edit)
        
        browse_file_btn = QPushButton("Browse File")
        browse_file_btn.clicked.connect(self._browse_file)
        browser_layout.addWidget(browse_file_btn)
        
        browse_dir_btn = QPushButton("Browse Directory")
        browse_dir_btn.clicked.connect(self._browse_directory)
        browser_layout.addWidget(browse_dir_btn)
        
        layout.addLayout(browser_layout)
        
        # Preview area
        preview_label = QLabel("Preview (first few trials):")
        layout.addWidget(preview_label)
        
        self.preview_list = QListWidget()
        layout.addWidget(self.preview_list)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self._import_data)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _browse_file(self) -> None:
        """Open file browser dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tracking Data File",
            "",
            "Data Files (*.csv *.xlsx *.txt *.dat);;All Files (*.*)"
        )
        
        if file_path:
            self.selected_path = file_path
            self.path_edit.setText(file_path)
            self._update_preview()
    
    def _browse_directory(self) -> None:
        """Open directory browser dialog."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory Containing Tracking Data"
        )
        
        if dir_path:
            self.selected_path = dir_path
            self.path_edit.setText(dir_path)
            self._update_preview()
    
    def _update_preview(self) -> None:
        """Update preview list with sample data."""
        self.preview_list.clear()
        
        if not self.selected_path:
            return
        
        path = Path(self.selected_path)
        
        if path.is_file():
            # Preview single file
            try:
                with open(path, 'r') as f:
                    lines = [f.readline().strip() for _ in range(10)]
                self.preview_list.addItems(lines)
            except Exception as e:
                self.preview_list.addItem(f"Error reading file: {e}")
        elif path.is_dir():
            # List files in directory
            files = list(path.glob('*.csv')) + list(path.glob('*.xlsx'))
            files = files[:20]  # Limit to first 20 files
            self.preview_list.addItems([f.name for f in files])
        
        self.import_btn.setEnabled(True)
    
    def _import_data(self) -> None:
        """Import the selected data."""
        if not self.selected_path:
            QMessageBox.warning(self, "No Selection", "Please select a file or directory first.")
            return
        
        software_type = self.software_combo.currentText()
        preview_data = [
            self.preview_list.item(i).text()
            for i in range(self.preview_list.count())
        ]
        
        self.file_imported.emit(software_type, self.selected_path, preview_data)
        self.accept()


class ManualStrategyDialog(QDialog):
    """
    Dialog for manually classifying a trial's strategy.
    """
    
    strategy_classified = pyqtSignal(str, int, int, str)  # strategy, score, confidence, notes
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the manual strategy classification dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Manual Strategy Classification")
        self.setMinimumSize(400, 350)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Strategy dropdown
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("Strategy:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            'Direct',
            'Focal',
            'Directed',
            'Chaining',
            'Scanning',
            'Thigmotaxis',
            'Random',
            'Perseverative'
        ])
        strategy_layout.addWidget(self.strategy_combo)
        layout.addLayout(strategy_layout)
        
        # Score slider (0-3)
        score_label = QLabel("Score (0-3):")
        layout.addWidget(score_label)
        
        score_layout = QHBoxLayout()
        self.score_slider = QSlider(Qt.Orientation.Horizontal)
        self.score_slider.setRange(0, 3)
        self.score_slider.setValue(2)
        self.score_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.score_slider.setTickInterval(1)
        self.score_value_label = QLabel("2")
        self.score_slider.valueChanged.connect(
            lambda v: self.score_value_label.setText(str(v))
        )
        score_layout.addWidget(self.score_slider)
        score_layout.addWidget(self.score_value_label)
        layout.addLayout(score_layout)
        
        # Confidence slider (0-100%)
        confidence_label = QLabel("Confidence (0-100%):")
        layout.addWidget(confidence_label)
        
        confidence_layout = QHBoxLayout()
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(0, 100)
        self.confidence_slider.setValue(80)
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        self.confidence_value_label = QLabel("80%")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_value_label.setText(f"{v}%")
        )
        confidence_layout.addWidget(self.confidence_slider)
        confidence_layout.addWidget(self.confidence_value_label)
        layout.addLayout(confidence_layout)
        
        # Notes text field
        notes_label = QLabel("Notes:")
        layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Optional notes about this classification...")
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._accept_classification)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _accept_classification(self) -> None:
        """Accept and emit the classification."""
        strategy = self.strategy_combo.currentText()
        score = self.score_slider.value()
        confidence = self.confidence_slider.value()
        notes = self.notes_edit.toPlainText()
        
        self.strategy_classified.emit(strategy, score, confidence, notes)
        self.accept()


class ExportDialog(QDialog):
    """
    Dialog for exporting analysis results in various formats.
    """
    
    export_requested = pyqtSignal(str, dict, str)  # format, options, file_path
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the export dialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.export_path: Optional[str] = None
        
        self.setWindowTitle("Export Analysis Results")
        self.setMinimumSize(450, 300)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Export format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Export Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['CSV', 'Excel', 'PDF'])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        # Include options
        options_group = QGroupBox("Include in Export")
        options_layout = QVBoxLayout()
        
        self.include_metrics_cb = QCheckBox("Strategy Metrics")
        self.include_metrics_cb.setChecked(True)
        options_layout.addWidget(self.include_metrics_cb)
        
        self.include_heatmap_cb = QCheckBox("Heatmap Images")
        self.include_heatmap_cb.setChecked(True)
        options_layout.addWidget(self.include_heatmap_cb)
        
        self.include_summary_cb = QCheckBox("Summary Statistics")
        self.include_summary_cb.setChecked(True)
        options_layout.addWidget(self.include_summary_cb)
        
        self.include_paths_cb = QCheckBox("Path Trajectories")
        self.include_paths_cb.setChecked(False)
        options_layout.addWidget(self.include_paths_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # File location browser
        location_layout = QHBoxLayout()
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Select export location...")
        self.location_edit.setReadOnly(True)
        location_layout.addWidget(self.location_edit)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_location)
        location_layout.addWidget(browse_btn)
        
        layout.addLayout(location_layout)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._perform_export)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _browse_location(self) -> None:
        """Open file browser to select export location."""
        format_text = self.format_combo.currentText()
        
        if format_text == 'CSV':
            filter_str = "CSV Files (*.csv)"
            default_ext = ".csv"
        elif format_text == 'Excel':
            filter_str = "Excel Files (*.xlsx)"
            default_ext = ".xlsx"
        else:  # PDF
            filter_str = "PDF Files (*.pdf)"
            default_ext = ".pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Export Location",
            f"pathfinder_export{default_ext}",
            filter_str
        )
        
        if file_path:
            self.export_path = file_path
            self.location_edit.setText(file_path)
            self.export_btn.setEnabled(True)
    
    def _perform_export(self) -> None:
        """Perform the export operation."""
        if not self.export_path:
            QMessageBox.warning(self, "No Location", "Please select an export location first.")
            return
        
        export_format = self.format_combo.currentText()
        
        options = {
            'metrics': self.include_metrics_cb.isChecked(),
            'heatmap': self.include_heatmap_cb.isChecked(),
            'summary': self.include_summary_cb.isChecked(),
            'paths': self.include_paths_cb.isChecked()
        }
        
        self.export_requested.emit(export_format, options, self.export_path)
        self.accept()
