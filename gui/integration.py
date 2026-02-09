"""
Integration layer for Pathfinder GUI.
Connects UI widgets to analysis backend via signal/slot pattern.
Manages worker threads for long-running operations.
"""

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QDialogButtonBox, QComboBox, QLabel
from pathlib import Path
from typing import Optional, List
import logging
import math

from pathfinder.core.models import (
    Experiment, Trial, SearchStrategy, Parameters
)
from pathfinder.io.loaders import load_experiment, detect_software_format
from pathfinder.io.writers import export_to_csv, export_to_excel, export_trajectory_data
from pathfinder.analysis import calculate_trial_metrics, classify_strategy
from pathfinder.types import Parameters as LegacyParameters
from pathfinder.core.geometry import MazeGeometry

from .main_window import PathfinderMainWindow
from .defaults import DEFAULT_PARAMETERS, get_default_parameters
from .settings_dialog_v2 import SettingsDialogV2


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileLoadWorker(QThread):
    """
    Worker thread for loading experiment files.
    Emits progress updates and results.
    """
    progress = pyqtSignal(int, str)  # (percentage, message)
    finished = pyqtSignal(object)    # Experiment object
    error = pyqtSignal(str)          # Error message
    
    def __init__(self, file_path: Path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._is_cancelled = False
    
    def run(self):
        """Load experiment file in background thread"""
        try:
            self.progress.emit(10, "Detecting file format...")
            
            # Detect software type
            software = detect_software_format(self.file_path)
            
            if self._is_cancelled:
                return
            
            self.progress.emit(30, f"Loading {software.value} data...")
            
            # Load experiment
            experiment = load_experiment(self.file_path, software)
            
            if self._is_cancelled:
                return
            
            self.progress.emit(90, "Processing trials...")
            
            # Validate
            if not experiment or not experiment.trials:
                self.error.emit("No trials found in file")
                return
            
            self.progress.emit(100, f"Loaded {len(experiment.trials)} trials")
            self.finished.emit(experiment)
            
        except Exception as e:
            logger.exception("Error loading file")
            self.error.emit(f"Failed to load file: {str(e)}")
    
    def cancel(self):
        """Cancel the operation"""
        self._is_cancelled = True


class AnalysisWorker(QThread):
    """
    Worker thread for running analysis on experiment.
    Processes trials and emits progress updates.
    """
    progress = pyqtSignal(int, str)         # (percentage, message)
    trial_completed = pyqtSignal(str, object)  # (trial_id, AnalysisResult)
    finished = pyqtSignal(object)           # Updated Experiment
    error = pyqtSignal(str)                 # Error message
    
    def __init__(self, experiment: Experiment, parameters: Parameters, parent=None):
        super().__init__(parent)
        self.experiment = experiment
        self.parameters = parameters
        self._is_cancelled = False
    
    def run(self):
        """Run analysis in background thread using proper classification logic"""
        try:
            total_trials = len(self.experiment.trials)

            self.progress.emit(0, "Initializing analysis...")

            # Get pool geometry from first trial
            first_trial = self.experiment.trials[0]
            pool_radius = first_trial.pool_diameter / 2

            # Convert Pydantic Parameters to legacy Parameters format for analysis functions
            legacy_params = LegacyParameters(
                name=self.parameters.name,
                ipeMaxVal=self.parameters.ipe_max_val,
                headingMaxVal=self.parameters.heading_max_val,
                distanceToSwimMaxVal=self.parameters.distance_to_swim_max_val,
                distanceToPlatMaxVal=self.parameters.distance_to_plat_max_val,
                distanceToSwimMaxVal2=self.parameters.distance_to_swim_max_val2,
                distanceToPlatMaxVal2=self.parameters.distance_to_plat_max_val2,
                focalMinDistance=self.parameters.focal_min_distance,
                focalMaxDistance=self.parameters.focal_max_distance,
                semiFocalMinDistance=self.parameters.semi_focal_min_distance,
                semiFocalMaxDistance=self.parameters.semi_focal_max_distance,
                corridorAverageMinVal=self.parameters.corridor_average_min_val,
                corridoripeMaxVal=self.parameters.corridor_ipe_max_val,
                directedSearchMaxDistance=self.parameters.directed_search_max_distance,
                ipeIndirectMaxVal=self.parameters.ipe_indirect_max_val,
                headingIndirectMaxVal=self.parameters.heading_indirect_max_val,
                annulusCounterMaxVal=self.parameters.annulus_counter_max_val,
                quadrantTotalMaxVal=int(self.parameters.quadrant_total_max_val),
                chainingMaxCoverage=self.parameters.chaining_max_coverage,
                percentTraversedMinVal=self.parameters.percent_traversed_min_val,
                percentTraversedMaxVal=self.parameters.percent_traversed_max_val,
                distanceToCentreMaxVal=self.parameters.distance_to_centre_max_val,
                fullThigmoMinVal=self.parameters.full_thigmo_min_val,
                smallThigmoMinVal=self.parameters.small_thigmo_min_val,
                thigmoMinDistance=self.parameters.thigmo_min_distance,
                percentTraversedRandomMaxVal=self.parameters.percent_traversed_random_max_val,
                useDirect=self.parameters.use_direct,
                useFocal=self.parameters.use_focal,
                useDirected=self.parameters.use_directed,
                useIndirect=self.parameters.use_indirect,
                useSemiFocal=self.parameters.use_semi_focal,
                useChaining=self.parameters.use_chaining,
                useScanning=self.parameters.use_scanning,
                useThigmotaxis=self.parameters.use_thigmotaxis,
                useRandom=self.parameters.use_random
            )

            # Process each trial
            for i, trial in enumerate(self.experiment.trials):
                if self._is_cancelled:
                    return

                # Update progress
                try:
                    percent = int((i / total_trials) * 100) if total_trials > 0 else 0
                except Exception:
                    percent = 0

                self.progress.emit(
                    percent,
                    f"Analyzing trial {i+1}/{total_trials} (Day {trial.day}, Trial {trial.trial_number})"
                )

                # Run analysis using proper functions
                try:
                    # Calculate metrics
                    metrics = calculate_trial_metrics(
                        trial=trial,
                        goal_x=trial.platform_position[0],
                        goal_y=trial.platform_position[1],
                        maze_centre_x=trial.pool_center[0],
                        maze_centre_y=trial.pool_center[1],
                        corridor_width=self.parameters.corridor_width_degrees,
                        thigmotaxis_zone_size=self.parameters.thigmotaxis_zone_percent,
                        chaining_radius=self.parameters.chaining_radius,
                        full_thigmo_zone=pool_radius * (1 - self.parameters.thigmotaxis_zone_percent / 100),
                        small_thigmo_zone=pool_radius * 0.8,  # 80% of radius
                        maze_radius=pool_radius,
                        day_num=trial.day,
                        goal_diam=trial.platform_diameter
                    )

                    # Classify strategy
                    strategy_name, score = classify_strategy(
                        metrics=metrics,
                        parameters=legacy_params,
                        maze_radius=pool_radius
                    )

                    # Map strategy name to enum
                    strategy_map = {
                        "Direct Path": SearchStrategy.DIRECT_SWIM,
                        "Directed Search": SearchStrategy.DIRECTED_SEARCH,
                        "Focal Search": SearchStrategy.FOCAL_SEARCH,
                        "Indirect Search": SearchStrategy.SPATIAL_INDIRECT,
                        "Semi-focal Search": SearchStrategy.SPATIAL_INDIRECT,  # Map to spatial indirect
                        "Chaining": SearchStrategy.CHAINING,
                        "Scanning": SearchStrategy.SCANNING,
                        "Thigmotaxis": SearchStrategy.THIGMOTAXIS,
                        "Random Search": SearchStrategy.RANDOM_SEARCH,
                        "Not Recognized": SearchStrategy.NOT_RECOGNIZED
                    }

                    strategy = strategy_map.get(strategy_name, SearchStrategy.NOT_RECOGNIZED)

                    # Update trial
                    trial.search_strategy = strategy
                    trial.path_length = metrics.total_distance
                    trial.escape_latency = metrics.latency
                    trial.swim_speed = metrics.velocity

                    # Store metrics in trial for display (will add this field)
                    if not hasattr(trial, '_metrics'):
                        trial._metrics = metrics
                    else:
                        trial._metrics = metrics

                    self.trial_completed.emit(trial.trial_id, None)

                except Exception as e:
                    logger.error(f"Error analyzing trial {trial.trial_id}: {e}")
                    logger.exception(e)
                    # Continue with other trials

            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(self.experiment)

        except Exception as e:
            logger.exception("Error during analysis")
            self.error.emit(f"Analysis failed: {str(e)}")
    
    def cancel(self):
        """Cancel the operation"""
        self._is_cancelled = True


class ManualClassificationDialog(QDialog):
    """
    Dialog for manually classifying a trial's search strategy.
    """
    
    def __init__(self, trial: Trial, parent=None):
        super().__init__(parent)
        self.trial = trial
        self.selected_strategy = trial.search_strategy
        self._init_ui()
    
    def _init_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle(f"Manual Classification - Trial {self.trial.trial_number}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info = QLabel(
            f"<b>Day {self.trial.day}, Trial {self.trial.trial_number}</b><br>"
            f"Escape Latency: {self.trial.escape_latency:.2f}s<br>"
            f"Current: {self.trial.search_strategy.value if self.trial.search_strategy else 'None'}"
        )
        layout.addWidget(info)
        
        # Strategy selector
        layout.addWidget(QLabel("\nSelect Strategy:"))
        self.strategy_combo = QComboBox()
        for strategy in SearchStrategy:
            self.strategy_combo.addItem(strategy.value, strategy)
        
        # Set current selection
        if self.trial.search_strategy:
            index = self.strategy_combo.findData(self.trial.search_strategy)
            if index >= 0:
                self.strategy_combo.setCurrentIndex(index)
        
        layout.addWidget(self.strategy_combo)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_strategy(self) -> SearchStrategy:
        """Get the selected strategy"""
        return self.strategy_combo.currentData()


def auto_calculate_geometry(trials: List[Trial]) -> dict:
    """
    Auto-calculate pool and platform geometry from trajectory data.

    Returns dict with:
        - pool_center_x, pool_center_y: Center of bounding circle
        - pool_diameter: Diameter that encompasses all trajectories
        - platform_x, platform_y: Estimated platform location from trial endpoints
    """
    import numpy as np
    import math

    # Collect all trajectory points
    all_x = []
    all_y = []

    for trial in trials:
        for point in trial.trajectory:
            if (point.x is not None and point.y is not None and
                not np.isnan(point.x) and not np.isnan(point.y) and
                not np.isinf(point.x) and not np.isinf(point.y)):
                all_x.append(point.x)
                all_y.append(point.y)

    if not all_x:
        logger.warning("No valid trajectory points found for auto-calculation")
        return {
            'pool_center_x': 250.0,
            'pool_center_y': 250.0,
            'pool_diameter': 500.0,
            'platform_x': 350.0,
            'platform_y': 150.0
        }

    # Use percentiles instead of min/max to exclude outliers
    # This handles tracking errors (e.g., one trial with points outside the pool)
    percentile_low = 1   # Exclude bottom 1%
    percentile_high = 99  # Exclude top 1%

    min_x = np.percentile(all_x, percentile_low)
    max_x = np.percentile(all_x, percentile_high)
    min_y = np.percentile(all_y, percentile_low)
    max_y = np.percentile(all_y, percentile_high)

    logger.info(f"Using {percentile_low}th-{percentile_high}th percentile for outlier-resistant bounds")

    # Pool center is center of bounding box
    pool_center_x = (min_x + max_x) / 2
    pool_center_y = (min_y + max_y) / 2

    # Pool diameter: use 99th percentile of distances to exclude outliers
    # Calculate distances from center for all points
    distances = []
    for x, y in zip(all_x, all_y):
        dist = math.sqrt((x - pool_center_x)**2 + (y - pool_center_y)**2)
        distances.append(dist)

    # Use 99th percentile instead of max to exclude outliers
    max_dist = np.percentile(distances, 99)

    pool_diameter = max_dist * 2 * 1.1  # Add 10% margin

    logger.info(f"Pool diameter calculated from 99th percentile distance: {pool_diameter:.1f}")

    # Estimate platform location from endpoints of successful trials
    # (trials that didn't take maximum time)
    endpoint_x = []
    endpoint_y = []

    # Find maximum trial duration
    durations = []
    for trial in trials:
        if trial.trajectory:
            duration = trial.trajectory[-1].time - trial.trajectory[0].time
            durations.append(duration)

    if durations:
        max_duration = max(durations)
        # Consider trials that finished in less than 95% of max time as "successful"
        threshold = max_duration * 0.95

        for trial in trials:
            if trial.trajectory and len(trial.trajectory) > 1:
                duration = trial.trajectory[-1].time - trial.trajectory[0].time
                if duration < threshold:  # Successful trial
                    last_point = trial.trajectory[-1]
                    if (last_point.x is not None and last_point.y is not None and
                        not np.isnan(last_point.x) and not np.isnan(last_point.y)):
                        endpoint_x.append(last_point.x)
                        endpoint_y.append(last_point.y)

    # Platform location is mean of successful trial endpoints
    if endpoint_x and endpoint_y:
        platform_x = np.mean(endpoint_x)
        platform_y = np.mean(endpoint_y)
    else:
        # Fallback: use center of pool
        platform_x = pool_center_x
        platform_y = pool_center_y
        logger.warning("Could not estimate platform location, using pool center")

    logger.info(f"Auto-calculated geometry: Pool center ({pool_center_x:.1f}, {pool_center_y:.1f}), "
                f"diameter {pool_diameter:.1f}, platform ({platform_x:.1f}, {platform_y:.1f})")

    return {
        'pool_center_x': pool_center_x,
        'pool_center_y': pool_center_y,
        'pool_diameter': pool_diameter,
        'platform_x': platform_x,
        'platform_y': platform_y
    }


class PathfinderIntegration(QObject):
    @pyqtSlot()
    def on_load_folder(self):
        """Handle load folder request"""
        dir_path = QFileDialog.getExistingDirectory(
            self.window,
            "Select Folder Containing Trials",
            str(Path.home())
        )
        if not dir_path:
            return
        dir_path = Path(dir_path)
        logger.info(f"Loading all supported files from folder: {dir_path}")

        # Find all supported files recursively
        exts = (".csv", ".xlsx", ".xls")
        files = [f for f in dir_path.rglob("*") if f.suffix.lower() in exts]
        if not files:
            logger.error("No supported files found in folder.")
            return

        # Load and combine all trials
        all_trials = []
        experiment_name = f"Batch import: {dir_path.name}"
        for file in files:
            try:
                software = detect_software_format(file)
                exp = load_experiment(file, software)
                all_trials.extend(exp.trials)
            except Exception as e:
                logger.warning(f"Failed to load {file}: {e}")
        if not all_trials:
            logger.error("No valid trials loaded from folder.")
            return

        # Auto-calculate pool and platform geometry
        auto_geom = auto_calculate_geometry(all_trials)

        # Apply auto-calculated geometry to all trials
        for trial in all_trials:
            trial.pool_center = (auto_geom['pool_center_x'], auto_geom['pool_center_y'])
            trial.pool_diameter = auto_geom['pool_diameter']
            trial.platform_position = (auto_geom['platform_x'], auto_geom['platform_y'])
            # Note: platform_diameter is NOT auto-calculated, requires manual input

        # Update spatial parameters in integration
        self.spatial_params['pool_center_x'] = auto_geom['pool_center_x']
        self.spatial_params['pool_center_y'] = auto_geom['pool_center_y']
        self.spatial_params['pool_diameter'] = auto_geom['pool_diameter']
        self.spatial_params['platform_x'] = auto_geom['platform_x']
        self.spatial_params['platform_y'] = auto_geom['platform_y']
        # platform_diameter remains at default, user must set manually

        # Update GUI spinboxes
        cp = self.window.get_control_panel()
        cp.pool_center_x_spin.setValue(auto_geom['pool_center_x'])
        cp.pool_center_y_spin.setValue(auto_geom['pool_center_y'])
        cp.pool_diameter_spin.setValue(auto_geom['pool_diameter'])
        cp.platform_x_spin.setValue(auto_geom['platform_x'])
        cp.platform_y_spin.setValue(auto_geom['platform_y'])

        # Notify user
        self.window.show_info(
            "Auto-Calculated Geometry",
            f"Pool geometry and platform location have been estimated from trajectory data.\n\n"
            f"Pool Center: ({auto_geom['pool_center_x']:.1f}, {auto_geom['pool_center_y']:.1f})\n"
            f"Pool Diameter: {auto_geom['pool_diameter']:.1f}\n"
            f"Platform Position: ({auto_geom['platform_x']:.1f}, {auto_geom['platform_y']:.1f})\n\n"
            f"⚠️ Platform diameter NOT estimated - please set manually!\n\n"
            f"Review the Maze Setup tab and adjust if needed."
        )

        # Create a combined Experiment object
        from pathfinder.core.models import Experiment
        experiment = Experiment(
            experiment_id="batch_import",
            experiment_name=experiment_name,
            researcher="",
            notes="",
            parameters=get_default_parameters(),
            tracking_software="Unknown",
            trials=all_trials
        )
        # Set current_file to the folder path for batch import
        self.current_file = dir_path
        self._on_file_load_finished(experiment)

    
    def __init__(self, main_window: PathfinderMainWindow):
        super().__init__()
        self.window = main_window

        # State
        self.current_file: Optional[Path] = None
        self.current_experiment: Optional[Experiment] = None
        self.current_parameters: Parameters = get_default_parameters()

        # Spatial parameters for maze geometry
        self.spatial_params = {
            'pool_center_x': 250.0,
            'pool_center_y': 250.0,
            'pool_diameter': 500.0,
            'platform_x': 350.0,
            'platform_y': 150.0,
            'platform_diameter': 50.0
        }

        # Workers
        self.file_worker: Optional[FileLoadWorker] = None
        self.analysis_worker: Optional[AnalysisWorker] = None

        # Connect all signals
        self._connect_signals()
        
        # Initialize UI with defaults
        self._initialize_defaults()
        
        logger.info("Pathfinder integration initialized")
    
    def _connect_signals(self):
        """Connect all UI signals to handlers"""
        # Control panel signals
        cp = self.window.get_control_panel()
        cp.load_clicked.connect(self.on_load_file)
        cp.analyze_clicked.connect(self.run_analysis)
        cp.settings_clicked.connect(self.on_settings)
        cp.export_clicked.connect(self.on_export)
        cp.stop_btn.clicked.connect(self.on_stop_analysis)
        cp.spatial_params_changed.connect(self.on_spatial_params_changed)

        # Maze visualization signals
        maze_viz = self.window.get_maze_viz()
        cp.spatial_params_changed.connect(maze_viz.update_parameters)

        # Initialize maze visualization with default parameters
        initial_params = {
            'pool_center_x': self.spatial_params['pool_center_x'],
            'pool_center_y': self.spatial_params['pool_center_y'],
            'pool_diameter': self.spatial_params['pool_diameter'],
            'platform_x': self.spatial_params['platform_x'],
            'platform_y': self.spatial_params['platform_y'],
            'platform_diameter': self.spatial_params['platform_diameter']
        }
        maze_viz.update_parameters(initial_params)

        # Pass parameters object to visualization for zone sizing
        maze_viz.set_parameters(self.current_parameters)

        # Results table signals
        rt = self.window.get_results_table()
        rt.manual_classification_requested.connect(self.on_manual_classification)
        rt.trial_selected.connect(self.on_trial_selected)
        rt.export_requested.connect(self.on_export)
        
        # Heatmap signals
        hm = self.window.get_heatmap_widget()
        hm.export_requested.connect(self.on_export_heatmap)
        
        # Window signals
        self.window.exit_requested.connect(self.on_exit)
        
        logger.info("All signals connected")
    
    def _initialize_defaults(self):
        """Initialize UI with default parameter values"""
        cp = self.window.get_control_panel()
        cp.set_parameters_summary(f"Using: {self.current_parameters.name}")
        self.window.set_status_message("Ready - Load an experiment file to begin")

    def apply_spatial_parameters_to_trials(self):
        """Apply current spatial parameters to all trials in the experiment"""
        if not self.current_experiment:
            logger.warning("No experiment loaded - cannot apply spatial parameters")
            return

        # Validate parameters
        if self.spatial_params['pool_diameter'] <= self.spatial_params['platform_diameter']:
            logger.error("Pool diameter must be greater than platform diameter")
            self.window.set_status_message("ERROR: Invalid spatial parameters - pool must be larger than platform")
            return

        # Apply to all trials
        count = 0
        for trial in self.current_experiment.trials:
            trial.pool_center = (
                self.spatial_params['pool_center_x'],
                self.spatial_params['pool_center_y']
            )
            trial.pool_diameter = self.spatial_params['pool_diameter']
            trial.platform_position = (
                self.spatial_params['platform_x'],
                self.spatial_params['platform_y']
            )
            trial.platform_diameter = self.spatial_params['platform_diameter']
            count += 1

        logger.info(f"Applied spatial parameters to {count} trials")
        self.window.set_status_message(f"Applied maze geometry to {count} trials")

    @pyqtSlot(dict)
    def on_spatial_params_changed(self, params: dict):
        """Handle spatial parameter changes from GUI"""
        self.spatial_params.update(params)
        logger.info(f"Spatial parameters updated: {params}")

        # Apply to current experiment if loaded
        if self.current_experiment:
            self.apply_spatial_parameters_to_trials()
        else:
            self.window.set_status_message("Spatial parameters updated - will apply when file is loaded")

    # File operations
    
    @pyqtSlot()
    def on_load_file(self):
        """Handle load file request"""
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Open Experiment File",
            str(Path.home()),
            "All Supported (*.xlsx *.xls *.csv);;Excel Files (*.xlsx *.xls);;CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        file_path = Path(file_path)
        logger.info(f"Loading file: {file_path}")
        
        # Create and start worker thread
        self.file_worker = FileLoadWorker(file_path)
        self.file_worker.progress.connect(self._on_file_load_progress)
        self.file_worker.finished.connect(self._on_file_load_finished)
        self.file_worker.error.connect(self._on_file_load_error)
        
        # Update UI
        cp = self.window.get_control_panel()
        cp.set_progress(0, "Starting...")
        self.window.set_status_message("Loading file...")
        
        # Start loading
        self.file_worker.start()
    
    @pyqtSlot(int, str)
    def _on_file_load_progress(self, percent: int, message: str):
        """Handle file load progress update"""
        cp = self.window.get_control_panel()
        cp.set_progress(percent, message)
    
    @pyqtSlot(object)
    def _on_file_load_finished(self, experiment: Experiment):
        """Handle successful file load"""
        self.current_experiment = experiment
        # Only set current_file from file_worker if it exists (single file load)
        if self.file_worker is not None:
            self.current_file = self.file_worker.file_path
        # Otherwise, current_file is already set (e.g., by folder load)

        logger.info(f"File loaded: {len(experiment.trials)} trials")

        # Apply spatial parameters to all trials
        self.apply_spatial_parameters_to_trials()

        # Update UI
        cp = self.window.get_control_panel()
        if self.current_file is not None:
            cp.set_file_loaded(self.current_file)
        cp.set_progress(min(100, 100), "File loaded successfully")

        # Clear previous results
        self.window.get_results_table().clear()
        self.window.get_summary_widget()._clear()

        self.window.set_status_message(
            f"Loaded: {experiment.experiment_name} ({len(experiment.trials)} trials)"
        )

        # Clean up worker
        self.file_worker = None
    
    @pyqtSlot(str)
    def _on_file_load_error(self, error_message: str):
        """Handle file load error"""
        logger.error(f"File load error: {error_message}")
        
        self.window.show_error("Load Error", error_message)
        self.window.set_status_message("Error loading file")
        
        cp = self.window.get_control_panel()
        cp.set_progress(0, "Error")
        
        # Clean up worker
        self.file_worker = None
    
    # Analysis operations
    
    @pyqtSlot()
    def run_analysis(self):
        """Start analysis on current experiment"""
        if not self.current_experiment:
            self.window.show_warning("No Data", "Please load an experiment file first")
            return
        
        logger.info("Starting analysis...")
        
        # Create and start worker
        self.analysis_worker = AnalysisWorker(
            self.current_experiment,
            self.current_parameters
        )
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.trial_completed.connect(self._on_trial_completed)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.error.connect(self._on_analysis_error)
        
        # Update UI
        cp = self.window.get_control_panel()
        cp.set_analyzing(True)
        cp.set_progress(0, "Starting analysis...")
        self.window.set_status_message("Analysis running...")
        
        # Start analysis
        self.analysis_worker.start()
    
    @pyqtSlot()
    def on_stop_analysis(self):
        """Stop running analysis"""
        if self.analysis_worker and self.analysis_worker.isRunning():
            logger.info("Stopping analysis...")
            self.analysis_worker.cancel()
            self.analysis_worker.wait()
            
            cp = self.window.get_control_panel()
            cp.set_analyzing(False)
            cp.set_progress(0, "Analysis stopped")
            self.window.set_status_message("Analysis stopped by user")
    
    @pyqtSlot(int, str)
    def _on_analysis_progress(self, percent: int, message: str):
        """Handle analysis progress update"""
        cp = self.window.get_control_panel()
        cp.set_progress(percent, message)
    
    @pyqtSlot(str, object)
    def _on_trial_completed(self, trial_id: str, result: object):
        """Handle individual trial completion"""
        # Could update UI incrementally here if desired
        pass
    
    @pyqtSlot(object)
    def _on_analysis_finished(self, experiment: Experiment):
        """Handle analysis completion"""
        logger.info("Analysis complete")
        
        # Update state
        self.current_experiment = experiment
        
        # Update UI
        cp = self.window.get_control_panel()
        cp.set_analyzing(False)
        cp.set_progress(100, "Analysis complete!")
        
        # Display results
        rt = self.window.get_results_table()
        rt.load_results(experiment)
        
        sw = self.window.get_summary_widget()
        sw.set_results(experiment)
        
        hm = self.window.get_heatmap_widget()
        hm.set_experiment(experiment)
        
        self.window.set_status_message(
            f"Analysis complete: {len(experiment.trials)} trials classified"
        )
        
        # Switch to results tab
        self.window.results_tabs.setCurrentIndex(0)
        
        # Clean up worker
        self.analysis_worker = None
    
    @pyqtSlot(str)
    def _on_analysis_error(self, error_message: str):
        """Handle analysis error"""
        logger.error(f"Analysis error: {error_message}")
        
        self.window.show_error("Analysis Error", error_message)
        
        cp = self.window.get_control_panel()
        cp.set_analyzing(False)
        cp.set_progress(0, "Error")
        self.window.set_status_message("Analysis failed")
        
        # Clean up worker
        self.analysis_worker = None
    
    # Manual classification
    
    @pyqtSlot(str)
    def on_manual_classification(self, trial_id: str):
        """Handle manual classification request"""
        if not self.current_experiment:
            return
        
        # Find trial
        trial = next((t for t in self.current_experiment.trials if t.trial_id == trial_id), None)
        if not trial:
            logger.error(f"Trial not found: {trial_id}")
            return
        
        # Show dialog
        dialog = ManualClassificationDialog(trial, self.window)
        if dialog.exec_() == QDialog.Accepted:
            # Update trial
            new_strategy = dialog.get_selected_strategy()
            trial.search_strategy = new_strategy
            trial.manual_categorization = True
            
            logger.info(f"Trial {trial_id} manually classified as {new_strategy.value}")
            
            # Update results table
            rt = self.window.get_results_table()
            rt.update_trial(trial_id, new_strategy, manual=True)
            
            # Refresh summary
            sw = self.window.get_summary_widget()
            sw.set_results(self.current_experiment)
            
            self.window.set_status_message(f"Trial {trial.trial_number} classified as {new_strategy.value}")
    
    @pyqtSlot(int)
    def on_trial_selected(self, row_index: int):
        """Handle trial selection in results table - show trial path in heatmap by row index"""
        if row_index < 0:
            return

        # Show the selected trial's path in the heatmap (using row index)
        hm = self.window.get_heatmap_widget()
        hm.show_trial_by_index(row_index)
    
    # Settings
    
    @pyqtSlot()
    def on_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialogV2(self.current_parameters, self.window)
        
        if dialog.exec_() == QDialog.Accepted:
            # Update parameters
            new_params = dialog.get_parameters()
            self.current_parameters = new_params
            
            logger.info(f"Parameters updated: {new_params.name}")
            
            # Update UI
            cp = self.window.get_control_panel()
            cp.set_parameters_summary(f"Using: {new_params.name}")

            # Update maze visualization with new parameters
            maze_viz = self.window.get_maze_viz()
            maze_viz.set_parameters(new_params)

            self.window.set_status_message(f"Parameters updated: {new_params.name}")

            # If experiment is loaded, suggest re-analysis
            if self.current_experiment:
                if self.window.ask_yes_no(
                    "Re-run Analysis?",
                    "Parameters have been changed. Would you like to re-run the analysis with the new parameters?"
                ):
                    self.run_analysis()
    
    # Export
    
    @pyqtSlot()
    def on_export(self):
        """Export results to file"""
        if not self.current_experiment:
            self.window.show_warning("No Data", "No results to export")
            return
        
        # Show save dialog
        file_path, file_filter = QFileDialog.getSaveFileName(
            self.window,
            "Export Results",
            str(Path.home() / "pathfinder_results.csv"),
            "CSV Files (*.csv);;Excel Files (*.xlsx);;Trajectory Data (*.csv)"
        )
        
        if file_path:
            try:
                file_path = Path(file_path)
                logger.info(f"Exporting to: {file_path}")
                
                # Determine export format from filter or extension
                if 'Trajectory' in file_filter or '_trajectory' in file_path.stem:
                    export_trajectory_data(self.current_experiment, file_path)
                    export_type = "trajectory data"
                elif file_path.suffix.lower() in ['.xlsx', '.xls'] or 'Excel' in file_filter:
                    # Ensure .xlsx extension
                    if file_path.suffix.lower() != '.xlsx':
                        file_path = file_path.with_suffix('.xlsx')
                    export_to_excel(self.current_experiment, file_path)
                    export_type = "Excel file"
                else:
                    # Default to CSV
                    if not file_path.suffix:
                        file_path = file_path.with_suffix('.csv')
                    export_to_csv(self.current_experiment, file_path)
                    export_type = "CSV file"
                
                self.window.show_info(
                    "Export Successful", 
                    f"Results exported as {export_type}:\n{file_path}"
                )
                self.window.set_status_message(f"Exported to {file_path.name}")
                
            except Exception as e:
                logger.exception("Export error")
                self.window.show_error("Export Error", f"Failed to export: {str(e)}")
    
    @pyqtSlot()
    def on_export_heatmap(self):
        """Export heatmap image"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Export Heatmap",
            str(Path.home() / "heatmap.png"),
            "PNG Files (*.png);;JPEG Files (*.jpg)"
        )
        
        if file_path:
            try:
                hm = self.window.get_heatmap_widget()
                hm.export_image(file_path)
                self.window.show_info("Export", f"Heatmap saved to:\n{file_path}")
            except Exception as e:
                logger.exception("Heatmap export error")
                self.window.show_error("Export Error", f"Failed to export: {str(e)}")
    
    # Application lifecycle
    
    @pyqtSlot()
    def on_exit(self):
        """Handle application exit"""
        # Check if analysis is running
        if self.analysis_worker and self.analysis_worker.isRunning():
            if self.window.ask_yes_no(
                "Analysis Running",
                "Analysis is still running. Are you sure you want to exit?"
            ):
                self.analysis_worker.cancel()
                self.analysis_worker.wait()
            else:
                return
        
        logger.info("Application exiting")
    
    def cleanup(self):
        """Clean up resources"""
        # Cancel any running workers
        if self.file_worker and self.file_worker.isRunning():
            self.file_worker.cancel()
            self.file_worker.wait()
        
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.cancel()
            self.analysis_worker.wait()
        
        logger.info("Integration cleanup complete")
