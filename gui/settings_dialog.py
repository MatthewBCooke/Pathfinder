"""
Settings dialog for configuring analysis parameters.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox,
    QDialogButtonBox, QLabel, QGroupBox, QLineEdit, QPushButton
)
from PyQt5.QtCore import Qt
from pathfinder.core.models import Parameters
from gui.defaults import DEFAULT_PARAMETERS


class SettingsDialog(QDialog):
    """
    Dialog for editing analysis parameters.
    Organized into tabs for different parameter categories.
    """
    
    def __init__(self, current_parameters: Parameters, parent=None):
        super().__init__(parent)
        self.current_parameters = current_parameters.copy(deep=True)
        self.edited_parameters = current_parameters.copy(deep=True)
        self._init_ui()
        self._load_values()
    
    def _init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Analysis Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("<h2>⚙ Analysis Parameters</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Tabs for different parameter categories
        tabs = QTabWidget()
        
        # General tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Strategy Detection tab
        strategy_tab = self._create_strategy_tab()
        tabs.addTab(strategy_tab, "Strategy Detection")
        
        # Thresholds tab
        thresholds_tab = self._create_thresholds_tab()
        tabs.addTab(thresholds_tab, "Thresholds")
        
        # Advanced tab
        advanced_tab = self._create_advanced_tab()
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Parameter set name
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        form.addRow("Parameter Set Name:", self.name_edit)
        
        self.scale_values_check = QCheckBox("Auto-scale values based on pool size")
        form.addRow("Scaling:", self.scale_values_check)
        
        self.pixels_per_cm_spin = QDoubleSpinBox()
        self.pixels_per_cm_spin.setRange(0.1, 100.0)
        self.pixels_per_cm_spin.setDecimals(2)
        self.pixels_per_cm_spin.setSuffix(" px/cm")
        form.addRow("Pixels per cm:", self.pixels_per_cm_spin)
        
        layout.addLayout(form)
        layout.addStretch()
        
        return widget
    
    def _create_strategy_tab(self) -> QWidget:
        """Create strategy detection parameters tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Direct Swim group
        direct_group = QGroupBox("Direct Swim Detection")
        direct_layout = QFormLayout()
        
        self.ipe_max_spin = QDoubleSpinBox()
        self.ipe_max_spin.setRange(0, 360)
        self.ipe_max_spin.setDecimals(1)
        self.ipe_max_spin.setSuffix("°")
        direct_layout.addRow("IPE Maximum (Initial Path Error):", self.ipe_max_spin)
        
        self.heading_max_spin = QDoubleSpinBox()
        self.heading_max_spin.setRange(0, 180)
        self.heading_max_spin.setDecimals(1)
        self.heading_max_spin.setSuffix("°")
        direct_layout.addRow("Heading Error Maximum:", self.heading_max_spin)
        
        self.corridor_avg_min_spin = QDoubleSpinBox()
        self.corridor_avg_min_spin.setRange(0, 100)
        self.corridor_avg_min_spin.setDecimals(1)
        self.corridor_avg_min_spin.setSuffix("%")
        direct_layout.addRow("Corridor Coverage Minimum:", self.corridor_avg_min_spin)
        
        self.corridor_ipe_max_spin = QDoubleSpinBox()
        self.corridor_ipe_max_spin.setRange(0, 5000)
        self.corridor_ipe_max_spin.setDecimals(0)
        direct_layout.addRow("Corridor IPE Maximum:", self.corridor_ipe_max_spin)
        
        direct_group.setLayout(direct_layout)
        layout.addWidget(direct_group)
        
        # Focal Search group
        focal_group = QGroupBox("Focal Search Detection")
        focal_layout = QFormLayout()
        
        self.focal_min_spin = QDoubleSpinBox()
        self.focal_min_spin.setRange(0, 1000)
        self.focal_min_spin.setDecimals(0)
        self.focal_min_spin.setSuffix(" cm")
        focal_layout.addRow("Minimum Distance:", self.focal_min_spin)
        
        self.focal_max_spin = QDoubleSpinBox()
        self.focal_max_spin.setRange(0, 1000)
        self.focal_max_spin.setDecimals(0)
        self.focal_max_spin.setSuffix(" cm")
        focal_layout.addRow("Maximum Distance:", self.focal_max_spin)
        
        focal_group.setLayout(focal_layout)
        layout.addWidget(focal_group)
        
        # Thigmotaxis group
        thigmo_group = QGroupBox("Thigmotaxis Detection")
        thigmo_layout = QFormLayout()
        
        self.percent_traversed_max_spin = QDoubleSpinBox()
        self.percent_traversed_max_spin.setRange(0, 100)
        self.percent_traversed_max_spin.setDecimals(1)
        self.percent_traversed_max_spin.setSuffix("%")
        thigmo_layout.addRow("Max Wall Proximity %:", self.percent_traversed_max_spin)
        
        thigmo_group.setLayout(thigmo_layout)
        layout.addWidget(thigmo_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_thresholds_tab(self) -> QWidget:
        """Create thresholds tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Distance thresholds group
        dist_group = QGroupBox("Distance Thresholds")
        dist_layout = QFormLayout()
        
        self.dist_swim_max_spin = QDoubleSpinBox()
        self.dist_swim_max_spin.setRange(0, 500)
        self.dist_swim_max_spin.setDecimals(0)
        self.dist_swim_max_spin.setSuffix(" cm")
        dist_layout.addRow("Distance to Swim Max (1st):", self.dist_swim_max_spin)
        
        self.dist_plat_max_spin = QDoubleSpinBox()
        self.dist_plat_max_spin.setRange(0, 500)
        self.dist_plat_max_spin.setDecimals(0)
        self.dist_plat_max_spin.setSuffix(" cm")
        dist_layout.addRow("Distance to Platform Max (1st):", self.dist_plat_max_spin)
        
        self.dist_swim_max2_spin = QDoubleSpinBox()
        self.dist_swim_max2_spin.setRange(0, 500)
        self.dist_swim_max2_spin.setDecimals(0)
        self.dist_swim_max2_spin.setSuffix(" cm")
        dist_layout.addRow("Distance to Swim Max (2nd):", self.dist_swim_max2_spin)
        
        self.dist_plat_max2_spin = QDoubleSpinBox()
        self.dist_plat_max2_spin.setRange(0, 500)
        self.dist_plat_max2_spin.setDecimals(0)
        self.dist_plat_max2_spin.setSuffix(" cm")
        dist_layout.addRow("Distance to Platform Max (2nd):", self.dist_plat_max2_spin)
        
        dist_group.setLayout(dist_layout)
        layout.addWidget(dist_group)
        
        # Other thresholds group
        other_group = QGroupBox("Other Thresholds")
        other_layout = QFormLayout()
        
        self.directed_search_max_spin = QDoubleSpinBox()
        self.directed_search_max_spin.setRange(0, 1000)
        self.directed_search_max_spin.setDecimals(0)
        self.directed_search_max_spin.setSuffix(" cm")
        other_layout.addRow("Directed Search Max Distance:", self.directed_search_max_spin)
        
        self.annulus_max_spin = QDoubleSpinBox()
        self.annulus_max_spin.setRange(0, 100)
        self.annulus_max_spin.setDecimals(0)
        other_layout.addRow("Annulus Counter Maximum:", self.annulus_max_spin)
        
        self.quadrant_max_spin = QDoubleSpinBox()
        self.quadrant_max_spin.setRange(1, 4)
        self.quadrant_max_spin.setDecimals(0)
        other_layout.addRow("Quadrant Total Maximum:", self.quadrant_max_spin)
        
        self.chaining_max_spin = QDoubleSpinBox()
        self.chaining_max_spin.setRange(0, 100)
        self.chaining_max_spin.setDecimals(1)
        self.chaining_max_spin.setSuffix("%")
        other_layout.addRow("Chaining Max Coverage:", self.chaining_max_spin)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced parameters tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Semi-focal (Spatial Indirect) group
        semi_group = QGroupBox("Spatial Indirect (Semi-Focal)")
        semi_layout = QFormLayout()
        
        self.semi_focal_min_spin = QDoubleSpinBox()
        self.semi_focal_min_spin.setRange(0, 1000)
        self.semi_focal_min_spin.setDecimals(0)
        self.semi_focal_min_spin.setSuffix(" cm")
        semi_layout.addRow("Minimum Distance:", self.semi_focal_min_spin)
        
        self.semi_focal_max_spin = QDoubleSpinBox()
        self.semi_focal_max_spin.setRange(0, 1000)
        self.semi_focal_max_spin.setDecimals(0)
        self.semi_focal_max_spin.setSuffix(" cm")
        semi_layout.addRow("Maximum Distance:", self.semi_focal_max_spin)
        
        semi_group.setLayout(semi_layout)
        layout.addWidget(semi_group)
        
        # Info label
        info = QLabel(
            "<i>Advanced parameters control fine-tuning of strategy detection. "
            "Modify with caution - incorrect values may lead to misclassification.</i>"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        return widget
    
    def _load_values(self):
        """Load current parameter values into UI"""
        p = self.edited_parameters
        
        # General
        self.name_edit.setText(p.name)
        self.scale_values_check.setChecked(p.scale_values)
        self.pixels_per_cm_spin.setValue(p.pixels_per_cm)
        
        # Strategy Detection
        self.ipe_max_spin.setValue(p.ipe_max_val)
        self.heading_max_spin.setValue(p.heading_max_val)
        self.corridor_avg_min_spin.setValue(p.corridor_average_min_val)
        self.corridor_ipe_max_spin.setValue(p.corridor_ipe_max_val)
        self.focal_min_spin.setValue(p.focal_min_distance)
        self.focal_max_spin.setValue(p.focal_max_distance)
        self.percent_traversed_max_spin.setValue(p.percent_traversed_max_val)
        
        # Thresholds
        self.dist_swim_max_spin.setValue(p.distance_to_swim_max_val)
        self.dist_plat_max_spin.setValue(p.distance_to_plat_max_val)
        self.dist_swim_max2_spin.setValue(p.distance_to_swim_max_val2)
        self.dist_plat_max2_spin.setValue(p.distance_to_plat_max_val2)
        self.directed_search_max_spin.setValue(p.directed_search_max_distance)
        self.annulus_max_spin.setValue(p.annulus_counter_max_val)
        self.quadrant_max_spin.setValue(p.quadrant_total_max_val)
        self.chaining_max_spin.setValue(p.chaining_max_coverage)
        
        # Advanced
        self.semi_focal_min_spin.setValue(p.semi_focal_min_distance)
        self.semi_focal_max_spin.setValue(p.semi_focal_max_distance)
    
    def _save_values(self):
        """Save UI values to edited_parameters"""
        # General
        self.edited_parameters.name = self.name_edit.text()
        self.edited_parameters.scale_values = self.scale_values_check.isChecked()
        self.edited_parameters.pixels_per_cm = self.pixels_per_cm_spin.value()
        
        # Strategy Detection
        self.edited_parameters.ipe_max_val = self.ipe_max_spin.value()
        self.edited_parameters.heading_max_val = self.heading_max_spin.value()
        self.edited_parameters.corridor_average_min_val = self.corridor_avg_min_spin.value()
        self.edited_parameters.corridor_ipe_max_val = self.corridor_ipe_max_spin.value()
        self.edited_parameters.focal_min_distance = self.focal_min_spin.value()
        self.edited_parameters.focal_max_distance = self.focal_max_spin.value()
        self.edited_parameters.percent_traversed_max_val = self.percent_traversed_max_spin.value()
        
        # Thresholds
        self.edited_parameters.distance_to_swim_max_val = self.dist_swim_max_spin.value()
        self.edited_parameters.distance_to_plat_max_val = self.dist_plat_max_spin.value()
        self.edited_parameters.distance_to_swim_max_val2 = self.dist_swim_max2_spin.value()
        self.edited_parameters.distance_to_plat_max_val2 = self.dist_plat_max2_spin.value()
        self.edited_parameters.directed_search_max_distance = self.directed_search_max_spin.value()
        self.edited_parameters.annulus_counter_max_val = self.annulus_max_spin.value()
        self.edited_parameters.quadrant_total_max_val = self.quadrant_max_spin.value()
        self.edited_parameters.chaining_max_coverage = self.chaining_max_spin.value()
        
        # Advanced
        self.edited_parameters.semi_focal_min_distance = self.semi_focal_min_spin.value()
        self.edited_parameters.semi_focal_max_distance = self.semi_focal_max_spin.value()
    
    def _on_accept(self):
        """Handle OK button"""
        self._save_values()
        self.accept()
    
    def _restore_defaults(self):
        """Restore default parameters"""
        self.edited_parameters = DEFAULT_PARAMETERS.copy(deep=True)
        self._load_values()
    
    def get_parameters(self) -> Parameters:
        """Get the edited parameters"""
        return self.edited_parameters
