"""
Reorganized settings dialog with per-strategy configuration.
Each strategy has its own tab with enable/disable and specific parameters.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox,
    QDialogButtonBox, QLabel, QGroupBox, QLineEdit, QPushButton,
    QScrollArea
)
from PyQt5.QtCore import Qt
from pathfinder.core.models import Parameters
from gui.defaults import DEFAULT_PARAMETERS


class StrategySettingsWidget(QWidget):
    """Widget for configuring a single strategy's parameters"""

    def __init__(self, strategy_name, strategy_description, parent=None):
        super().__init__(parent)
        self.strategy_name = strategy_name
        self.strategy_description = strategy_description
        self.parameter_spinboxes = {}
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)

        # Enable/Disable checkbox
        self.enable_checkbox = QCheckBox(f"Enable {self.strategy_name} Detection")
        self.enable_checkbox.setChecked(True)
        self.enable_checkbox.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.enable_checkbox)

        # Description
        desc_label = QLabel(self.strategy_description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-style: italic; padding: 5px 0px 10px 20px;")
        layout.addWidget(desc_label)

        # Parameters form
        self.param_form = QFormLayout()
        self.param_form.setContentsMargins(20, 10, 20, 10)
        layout.addLayout(self.param_form)

        layout.addStretch()

    def add_parameter(self, param_name, label_text, min_val, max_val, default_val, suffix="", tooltip=""):
        """Add a parameter spinbox"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        spinbox.setDecimals(1)
        if suffix:
            spinbox.setSuffix(f" {suffix}")
        spinbox.setMinimumWidth(150)
        if tooltip:
            spinbox.setToolTip(tooltip)

        label = QLabel(label_text)
        if tooltip:
            label.setToolTip(tooltip)

        self.param_form.addRow(label, spinbox)
        self.parameter_spinboxes[param_name] = spinbox
        return spinbox

    def is_enabled(self):
        """Check if strategy is enabled"""
        return self.enable_checkbox.isChecked()

    def set_enabled(self, enabled):
        """Set strategy enabled state"""
        self.enable_checkbox.setChecked(enabled)

    def get_parameter_value(self, param_name):
        """Get parameter value"""
        if param_name in self.parameter_spinboxes:
            return self.parameter_spinboxes[param_name].value()
        return None

    def set_parameter_value(self, param_name, value):
        """Set parameter value"""
        if param_name in self.parameter_spinboxes:
            self.parameter_spinboxes[param_name].setValue(value)


class SettingsDialogV2(QDialog):
    """
    Reorganized settings dialog with per-strategy configuration.
    Much clearer organization than the previous flat threshold list.
    """

    def __init__(self, current_parameters: Parameters, parent=None):
        super().__init__(parent)
        self.current_parameters = current_parameters.copy(deep=True)
        self.edited_parameters = current_parameters.copy(deep=True)
        self.strategy_widgets = {}
        self._init_ui()
        self._load_values()

    def _init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Strategy Analysis Settings")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<h2>⚙ Strategy Detection Configuration</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Info label
        info = QLabel(
            "Configure detection parameters for each search strategy. "
            "Uncheck 'Enable' to disable classification for that strategy."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(info)

        # Tabs for each strategy
        tabs = QTabWidget()

        # Create strategy tabs
        self._create_direct_swim_tab(tabs)
        self._create_directed_search_tab(tabs)
        self._create_focal_search_tab(tabs)
        self._create_spatial_indirect_tab(tabs)
        self._create_chaining_tab(tabs)
        self._create_scanning_tab(tabs)
        self._create_thigmotaxis_tab(tabs)
        self._create_random_tab(tabs)
        self._create_general_tab(tabs)

        layout.addWidget(tabs)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        layout.addWidget(button_box)

    def _create_direct_swim_tab(self, tabs):
        """Create Direct Swim strategy tab"""
        widget = StrategySettingsWidget(
            "Direct Swim",
            "Animal swims directly to the platform with minimal deviation. "
            "Indicates strong spatial memory."
        )

        widget.add_parameter(
            "ipe_max", "Maximum IPE (Ideal Path Error):",
            0, 500, 125, "",
            "Maximum deviation from ideal path. Lower = more direct."
        )

        widget.add_parameter(
            "heading_max", "Maximum Heading Error:",
            0, 90, 40, "degrees",
            "Maximum angular deviation from platform direction."
        )

        widget.add_parameter(
            "corridor_min", "Minimum Time in Corridor:",
            0, 100, 70, "%",
            "Minimum percentage of trial spent in angular corridor toward platform."
        )

        self.strategy_widgets['direct_swim'] = widget
        tabs.addTab(widget, "🎯 Direct Swim")

    def _create_directed_search_tab(self, tabs):
        """Create Directed Search strategy tab"""
        widget = StrategySettingsWidget(
            "Directed Search",
            "Animal searches in the general platform area but doesn't swim directly to it. "
            "Shows some spatial knowledge."
        )

        widget.add_parameter(
            "directed_max_distance", "Maximum Path Length:",
            0, 1000, 400, "cm",
            "Maximum total distance traveled for directed search."
        )

        widget.add_parameter(
            "corridor_ipe_max", "Maximum Corridor IPE:",
            0, 3000, 1500, "",
            "Maximum IPE while in corridor (more lenient than direct swim)."
        )

        widget.add_parameter(
            "corridor_min_directed", "Minimum Time in Corridor:",
            0, 100, 70, "%",
            "Minimum time in angular corridor for directed search."
        )

        widget.add_parameter(
            "corridor_width", "Corridor Angular Width:",
            5, 45, 15, "degrees",
            "Angular width of directed search corridor on each side of platform direction (for visualization and analysis)."
        )

        self.strategy_widgets['directed_search'] = widget
        tabs.addTab(widget, "🔍 Directed Search")

    def _create_focal_search_tab(self, tabs):
        """Create Focal Search strategy tab"""
        widget = StrategySettingsWidget(
            "Focal Search",
            "Animal searches intensively in a small area, typically near the platform location. "
            "Shows partial spatial memory."
        )

        widget.add_parameter(
            "focal_min_distance", "Minimum Path Length:",
            0, 500, 100, "cm",
            "Minimum distance for focal search (to distinguish from direct)."
        )

        widget.add_parameter(
            "focal_max_distance", "Maximum Path Length:",
            100, 1000, 400, "cm",
            "Maximum distance for focal search."
        )

        widget.add_parameter(
            "distance_to_plat_max", "Maximum Distance to Platform:",
            0, 100, 30, "% of radius",
            "Maximum average distance from platform."
        )

        widget.add_parameter(
            "distance_to_swim_max", "Maximum Distance to Swim Path:",
            0, 100, 30, "% of radius",
            "Maximum distance from swim path centroid."
        )

        self.strategy_widgets['focal_search'] = widget
        tabs.addTab(widget, "🎪 Focal Search")

    def _create_spatial_indirect_tab(self, tabs):
        """Create Spatial Indirect (Semi-Focal) strategy tab"""
        widget = StrategySettingsWidget(
            "Spatial Indirect",
            "Animal has some spatial knowledge but uses an indirect approach. "
            "Between focal search and random search."
        )

        widget.add_parameter(
            "semi_focal_min_distance", "Minimum Path Length:",
            0, 500, 0, "cm",
            "Minimum distance for spatial indirect."
        )

        widget.add_parameter(
            "semi_focal_max_distance", "Maximum Path Length:",
            0, 1500, 500, "cm",
            "Maximum distance for spatial indirect."
        )

        widget.add_parameter(
            "ipe_indirect_max", "Maximum IPE:",
            0, 1000, 200, "",
            "Maximum IPE for spatial indirect (higher than direct)."
        )

        widget.add_parameter(
            "heading_indirect_max", "Maximum Heading Error:",
            0, 180, 60, "degrees",
            "Maximum heading error for spatial indirect."
        )

        self.strategy_widgets['spatial_indirect'] = widget
        tabs.addTab(widget, "🔄 Spatial Indirect")

    def _create_chaining_tab(self, tabs):
        """Create Chaining strategy tab"""
        widget = StrategySettingsWidget(
            "Chaining",
            "Animal repeatedly follows similar path from start location to platform. "
            "Response learning rather than spatial learning."
        )

        widget.add_parameter(
            "chaining_max_coverage", "Maximum Pool Coverage:",
            0, 100, 40, "% traversed",
            "Maximum percentage of pool visited (low = repeated path)."
        )

        widget.add_parameter(
            "chaining_radius", "Chaining Zone Radius:",
            10, 200, 30, "cm",
            "Radius of zone around platform for chaining detection."
        )

        self.strategy_widgets['chaining'] = widget
        tabs.addTab(widget, "🔗 Chaining")

    def _create_scanning_tab(self, tabs):
        """Create Scanning strategy tab"""
        widget = StrategySettingsWidget(
            "Scanning",
            "Animal systematically covers the pool, visiting multiple quadrants. "
            "Organized search without spatial knowledge."
        )

        widget.add_parameter(
            "quadrant_total_max", "Minimum Quadrants Visited:",
            1, 4, 4, "quadrants",
            "Number of quadrants animal must visit for scanning."
        )

        widget.add_parameter(
            "annulus_max", "Maximum Annulus Counter:",
            0, 100, 90, "%",
            "Maximum time in annulus zone."
        )

        self.strategy_widgets['scanning'] = widget
        tabs.addTab(widget, "📊 Scanning")

    def _create_thigmotaxis_tab(self, tabs):
        """Create Thigmotaxis strategy tab"""
        widget = StrategySettingsWidget(
            "Thigmotaxis",
            "Animal stays near the pool wall (wall-hugging behavior). "
            "Indicates stress or lack of spatial learning."
        )

        widget.add_parameter(
            "percent_traversed_max", "Maximum Pool Coverage:",
            0, 100, 20, "% traversed",
            "Maximum coverage of pool (low = stays near wall)."
        )

        widget.add_parameter(
            "thigmo_zone_size", "Thigmotaxis Zone Width (Visual):",
            5, 50, 20, "% of radius",
            "Width of wall zone for visualization (affects thigmotaxis_zone_percent)."
        )

        widget.add_parameter(
            "full_thigmo_min", "Minimum Time in Full Zone:",
            0, 100, 65, "%",
            "Minimum time in outer/full thigmotaxis zone for classification."
        )

        widget.add_parameter(
            "small_thigmo_min", "Minimum Time in Small Zone:",
            0, 100, 35, "%",
            "Minimum time in inner/small thigmotaxis zone for classification."
        )

        widget.add_parameter(
            "thigmo_min_distance", "Minimum Path Distance:",
            0, 1000, 400, "cm",
            "Minimum total distance traveled for thigmotaxis classification."
        )

        self.strategy_widgets['thigmotaxis'] = widget
        tabs.addTab(widget, "⭕ Thigmotaxis")

    def _create_random_tab(self, tabs):
        """Create Random Search strategy tab"""
        widget = StrategySettingsWidget(
            "Random Search",
            "Animal searches with no apparent strategy or pattern. "
            "Default classification when no other strategy fits."
        )

        widget.add_parameter(
            "percent_traversed_random_max", "Minimum Pool Coverage:",
            0, 100, 30, "% traversed",
            "Minimum coverage for random search."
        )

        # Random search is typically the fallback, so minimal parameters
        note = QLabel(
            "Note: Random Search is the default classification when no other strategy matches. "
            "It has minimal parameters since it's defined by the absence of pattern."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-style: italic; padding: 10px;")
        widget.layout().addWidget(note)

        self.strategy_widgets['random'] = widget
        tabs.addTab(widget, "❓ Random Search")

    def _create_general_tab(self, tabs):
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

        tabs.addTab(widget, "⚙️ General")

    def _load_values(self):
        """Load current parameter values into widgets"""
        # Load general settings
        self.name_edit.setText(self.current_parameters.name)
        self.scale_values_check.setChecked(self.current_parameters.scale_values)
        self.pixels_per_cm_spin.setValue(self.current_parameters.pixels_per_cm)

        # Load strategy-specific values from current_parameters
        # Direct Swim
        if 'direct_swim' in self.strategy_widgets:
            w = self.strategy_widgets['direct_swim']
            w.set_parameter_value('ipe_max', self.current_parameters.ipe_max_val)
            w.set_parameter_value('heading_max', self.current_parameters.heading_max_val)
            w.set_parameter_value('corridor_min', self.current_parameters.corridor_average_min_val)

        # Directed Search
        if 'directed_search' in self.strategy_widgets:
            w = self.strategy_widgets['directed_search']
            w.set_parameter_value('directed_max_distance', self.current_parameters.directed_search_max_distance)
            w.set_parameter_value('corridor_ipe_max', self.current_parameters.corridor_ipe_max_val)
            w.set_parameter_value('corridor_min_directed', self.current_parameters.corridor_average_min_val)
            w.set_parameter_value('corridor_width', self.current_parameters.corridor_width_degrees)

        # Focal Search
        if 'focal_search' in self.strategy_widgets:
            w = self.strategy_widgets['focal_search']
            w.set_parameter_value('focal_min_distance', self.current_parameters.focal_min_distance)
            w.set_parameter_value('focal_max_distance', self.current_parameters.focal_max_distance)
            w.set_parameter_value('distance_to_plat_max', self.current_parameters.distance_to_plat_max_val)
            w.set_parameter_value('distance_to_swim_max', self.current_parameters.distance_to_swim_max_val)

        # Chaining
        if 'chaining' in self.strategy_widgets:
            w = self.strategy_widgets['chaining']
            w.set_parameter_value('chaining_max_coverage', self.current_parameters.chaining_max_coverage)
            w.set_parameter_value('chaining_radius', self.current_parameters.chaining_radius)

        # Thigmotaxis
        if 'thigmotaxis' in self.strategy_widgets:
            w = self.strategy_widgets['thigmotaxis']
            w.set_parameter_value('percent_traversed_max', self.current_parameters.percent_traversed_max_val)
            w.set_parameter_value('thigmo_zone_size', self.current_parameters.thigmotaxis_zone_percent)
            w.set_parameter_value('full_thigmo_min', self.current_parameters.full_thigmo_min_val)
            w.set_parameter_value('small_thigmo_min', self.current_parameters.small_thigmo_min_val)
            w.set_parameter_value('thigmo_min_distance', self.current_parameters.thigmo_min_distance)

    def _on_accept(self):
        """Save changes and close"""
        # Save general settings
        self.edited_parameters.name = self.name_edit.text()
        self.edited_parameters.scale_values = self.scale_values_check.isChecked()
        self.edited_parameters.pixels_per_cm = self.pixels_per_cm_spin.value()

        # Save strategy parameters
        # Direct Swim
        if 'direct_swim' in self.strategy_widgets:
            w = self.strategy_widgets['direct_swim']
            self.edited_parameters.ipe_max_val = w.get_parameter_value('ipe_max')
            self.edited_parameters.heading_max_val = w.get_parameter_value('heading_max')
            self.edited_parameters.corridor_average_min_val = w.get_parameter_value('corridor_min')

        # Directed Search
        if 'directed_search' in self.strategy_widgets:
            w = self.strategy_widgets['directed_search']
            self.edited_parameters.directed_search_max_distance = w.get_parameter_value('directed_max_distance')
            self.edited_parameters.corridor_ipe_max_val = w.get_parameter_value('corridor_ipe_max')
            self.edited_parameters.corridor_width_degrees = w.get_parameter_value('corridor_width')

        # Focal Search
        if 'focal_search' in self.strategy_widgets:
            w = self.strategy_widgets['focal_search']
            self.edited_parameters.focal_min_distance = w.get_parameter_value('focal_min_distance')
            self.edited_parameters.focal_max_distance = w.get_parameter_value('focal_max_distance')
            self.edited_parameters.distance_to_plat_max_val = w.get_parameter_value('distance_to_plat_max')
            self.edited_parameters.distance_to_swim_max_val = w.get_parameter_value('distance_to_swim_max')

        # Chaining
        if 'chaining' in self.strategy_widgets:
            w = self.strategy_widgets['chaining']
            self.edited_parameters.chaining_max_coverage = w.get_parameter_value('chaining_max_coverage')
            self.edited_parameters.chaining_radius = w.get_parameter_value('chaining_radius')

        # Thigmotaxis
        if 'thigmotaxis' in self.strategy_widgets:
            w = self.strategy_widgets['thigmotaxis']
            self.edited_parameters.percent_traversed_max_val = w.get_parameter_value('percent_traversed_max')
            self.edited_parameters.thigmotaxis_zone_percent = w.get_parameter_value('thigmo_zone_size')
            self.edited_parameters.full_thigmo_min_val = w.get_parameter_value('full_thigmo_min')
            self.edited_parameters.small_thigmo_min_val = w.get_parameter_value('small_thigmo_min')
            self.edited_parameters.thigmo_min_distance = w.get_parameter_value('thigmo_min_distance')

        # Store enable/disable state (would need to add these to Parameters model)
        # For now, just log them
        for strategy_name, widget in self.strategy_widgets.items():
            enabled = widget.is_enabled()
            print(f"Strategy '{strategy_name}' enabled: {enabled}")

        self.accept()

    def _restore_defaults(self):
        """Restore default parameter values"""
        self.current_parameters = DEFAULT_PARAMETERS.copy(deep=True)
        self._load_values()

    def get_parameters(self) -> Parameters:
        """Get edited parameters"""
        return self.edited_parameters
