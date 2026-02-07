"""
Worker threads for Pathfinder GUI non-blocking operations.

This module implements QThread workers for CPU-intensive and I/O operations
to keep the GUI responsive. All workers follow these threading patterns:
- Signals for communication (never direct GUI calls)
- Clean abort mechanisms
- Proper error handling and propagation
- Thread-safe operations only
"""

from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from pathfinder import (
    load_experiment,
    calculate_trial_metrics,
    classify_strategy,
    aggregate_heatmap_data,
)
from pathfinder.types import StrategyResult, HeatmapData
from pathfinder.models import Experiment, Trial


class AnalysisWorker(QThread):
    """
    Background worker for analyzing experiment trials.
    
    Iterates through all trials in an experiment, calculates metrics,
    and classifies search strategies. Emits progress updates and results
    via Qt signals for thread-safe GUI updates.
    
    Threading Model:
    - Runs in background thread (do not call run() directly)
    - Use start() to begin processing
    - Use request_abort() to cancel cleanly
    - Connect to signals for progress/results
    - Never accesses GUI elements directly
    
    Example:
        worker = AnalysisWorker(experiment, params)
        worker.progress.connect(update_progress_bar)
        worker.finished.connect(display_results)
        worker.error.connect(show_error_dialog)
        worker.start()
    """
    
    # Signals for thread-safe communication
    progress = pyqtSignal(int, int)  # current_trial, total_trials
    trial_completed = pyqtSignal(object)  # StrategyResult
    finished = pyqtSignal(list)  # List[StrategyResult]
    error = pyqtSignal(str)  # error_message
    
    def __init__(
        self,
        experiment: Experiment,
        parameters: Dict[str, Any],
        cancel_flag: Optional[Any] = None
    ):
        """
        Initialize the analysis worker.
        
        Args:
            experiment: Experiment object containing trials to analyze
            parameters: Analysis parameters (thresholds, filters, etc.)
            cancel_flag: Optional external cancellation flag (thread-safe)
        """
        super().__init__()
        self.experiment = experiment
        self.parameters = parameters
        self.cancel_flag = cancel_flag
        self._abort_requested = False
        self.results: List[StrategyResult] = []
    
    def run(self) -> None:
        """
        Main worker loop - analyzes all trials in the experiment.
        
        Called automatically by QThread.start(). Do not call directly.
        Emits progress after each trial and finished signal with all results.
        Respects abort requests for clean cancellation.
        """
        try:
            trials = self.experiment.trials
            total_trials = len(trials)
            self.results = []
            
            for i, trial in enumerate(trials):
                # Check for cancellation
                if self._should_abort():
                    return
                
                # Calculate metrics for this trial
                metrics = calculate_trial_metrics(
                    trial=trial,
                    **self.parameters
                )
                
                # Classify the search strategy
                strategy_result = classify_strategy(
                    trial=trial,
                    metrics=metrics,
                    **self.parameters
                )
                
                # Store and emit result
                self.results.append(strategy_result)
                self.trial_completed.emit(strategy_result)
                
                # Emit progress (1-indexed for display)
                self.progress.emit(i + 1, total_trials)
            
            # All trials processed successfully
            self.finished.emit(self.results)
            
        except Exception as e:
            # Propagate errors to GUI thread
            self.error.emit(f"Analysis error: {str(e)}")
    
    def request_abort(self) -> None:
        """
        Request clean cancellation of the analysis.
        
        Sets internal flag to stop processing after current trial.
        Thread-safe and can be called from any thread.
        """
        self._abort_requested = True
    
    def _should_abort(self) -> bool:
        """
        Check if abort has been requested.
        
        Returns:
            True if cancellation requested, False otherwise
        """
        # Check internal flag
        if self._abort_requested:
            return True
        
        # Check external cancel flag if provided
        if self.cancel_flag is not None:
            if callable(self.cancel_flag):
                return self.cancel_flag()
            elif hasattr(self.cancel_flag, 'is_set'):
                return self.cancel_flag.is_set()
            else:
                return bool(self.cancel_flag)
        
        return False


class HeatmapWorker(QThread):
    """
    Background worker for generating heatmap data.
    
    Aggregates spatial data from experiment trials to create heatmaps.
    Designed to handle large datasets efficiently without blocking the GUI.
    
    Threading Model:
    - Runs in background thread
    - Use start() to begin processing
    - Connect to signals for progress/results
    - Never accesses GUI elements directly
    
    Example:
        filters = {'min_score': 10, 'strategy': 'systematic'}
        worker = HeatmapWorker(experiment, filters)
        worker.progress.connect(update_progress_bar)
        worker.finished.connect(render_heatmap)
        worker.error.connect(show_error_dialog)
        worker.start()
    """
    
    # Signals for thread-safe communication
    progress = pyqtSignal(int)  # percent_complete (0-100)
    finished = pyqtSignal(object)  # HeatmapData
    error = pyqtSignal(str)  # error_message
    
    def __init__(
        self,
        experiment: Experiment,
        filters: Dict[str, Any]
    ):
        """
        Initialize the heatmap worker.
        
        Args:
            experiment: Experiment object containing trial data
            filters: Filter criteria for heatmap generation
                    (e.g., trial selection, time ranges, strategies)
        """
        super().__init__()
        self.experiment = experiment
        self.filters = filters
    
    def run(self) -> None:
        """
        Main worker loop - generates heatmap data.
        
        Called automatically by QThread.start(). Do not call directly.
        Emits progress updates and finished signal with HeatmapData.
        """
        try:
            # Emit initial progress
            self.progress.emit(0)
            
            # Generate heatmap data with progress callback
            heatmap_data = aggregate_heatmap_data(
                experiment=self.experiment,
                filters=self.filters,
                progress_callback=self._emit_progress
            )
            
            # Emit completion
            self.progress.emit(100)
            self.finished.emit(heatmap_data)
            
        except Exception as e:
            # Propagate errors to GUI thread
            self.error.emit(f"Heatmap generation error: {str(e)}")
    
    def _emit_progress(self, percent: int) -> None:
        """
        Internal progress callback for aggregate_heatmap_data.
        
        Args:
            percent: Completion percentage (0-100)
        """
        self.progress.emit(percent)


class FileLoadWorker(QThread):
    """
    Background worker for loading experiment files.
    
    Handles potentially slow file I/O operations without freezing the GUI.
    Supports various software formats and provides progress updates.
    
    Threading Model:
    - Runs in background thread
    - Use start() to begin loading
    - Connect to signals for progress/results
    - Never accesses GUI elements directly
    
    Example:
        worker = FileLoadWorker('ethovision', '/path/to/data.xlsx')
        worker.progress.connect(update_status_label)
        worker.finished.connect(display_experiment)
        worker.error.connect(show_error_dialog)
        worker.start()
    """
    
    # Signals for thread-safe communication
    progress = pyqtSignal(str)  # status_message
    finished = pyqtSignal(object)  # Experiment
    error = pyqtSignal(str)  # error_message
    
    def __init__(
        self,
        software_type: str,
        path: str
    ):
        """
        Initialize the file loading worker.
        
        Args:
            software_type: Type of software that generated the data
                          (e.g., 'ethovision', 'anymaze', 'topscan')
            path: File path or directory path to load from
        """
        super().__init__()
        self.software_type = software_type
        self.path = path
    
    def run(self) -> None:
        """
        Main worker loop - loads experiment from file(s).
        
        Called automatically by QThread.start(). Do not call directly.
        Emits progress status updates and finished signal with Experiment.
        """
        try:
            # Emit initial status
            self.progress.emit(f"Loading {self.software_type} data from {self.path}...")
            
            # Load the experiment
            experiment = load_experiment(
                software_type=self.software_type,
                path=self.path,
                progress_callback=self._emit_progress
            )
            
            # Emit completion status
            trial_count = len(experiment.trials) if experiment.trials else 0
            self.progress.emit(f"Loaded {trial_count} trials successfully")
            
            # Emit the loaded experiment
            self.finished.emit(experiment)
            
        except FileNotFoundError as e:
            self.error.emit(f"File not found: {str(e)}")
        except PermissionError as e:
            self.error.emit(f"Permission denied: {str(e)}")
        except ValueError as e:
            self.error.emit(f"Invalid file format: {str(e)}")
        except Exception as e:
            # Catch-all for unexpected errors
            self.error.emit(f"Error loading experiment: {str(e)}")
    
    def _emit_progress(self, status: str) -> None:
        """
        Internal progress callback for load_experiment.
        
        Args:
            status: Status message describing current operation
        """
        self.progress.emit(status)
