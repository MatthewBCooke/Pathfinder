"""
Integration layer for connecting GUI components and worker threads.

This module handles:
- Wiring up signal/slot connections between main window and dialogs
- Launching and managing worker threads
- Coordinating data flow between GUI and analysis engine
- Event handling and error management
"""

from __future__ import annotations
from typing import Optional, Callable
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from pathfinder import load_experiment
from pathfinder.models import Experiment, Parameters
from pathfinder.types import StrategyResult

from gui.main_window import PathfinderMainWindow
from gui.dialogs import SettingsDialog, FileImportDialog, ManualStrategyDialog, ExportDialog
from gui.workers import AnalysisWorker, HeatmapWorker, FileLoadWorker


class PathfinderIntegration:
    """
    Orchestrates the Pathfinder GUI application.
    
    Manages:
    - Dialog creation and event handling
    - Worker thread lifecycle
    - Data flow from file loading → analysis → results display
    - Error handling and user feedback
    """

    def __init__(self, main_window: PathfinderMainWindow) -> None:
        """
        Initialize integration layer.

        Args:
            main_window: The main application window
        """
        self.main_window = main_window
        self.current_experiment: Optional[Experiment] = None
        self.current_parameters: Optional[Parameters] = None
        self.current_results: list[StrategyResult] = []
        
        self.analysis_worker: Optional[AnalysisWorker] = None
        self.heatmap_worker: Optional[HeatmapWorker] = None
        self.file_load_worker: Optional[FileLoadWorker] = None

        self._setup_signal_connections()

    def _setup_signal_connections(self) -> None:
        """Wire up all signal/slot connections between GUI components."""
        # Main window menu actions
        self.main_window.action_load.triggered.connect(self.on_load_file)
        self.main_window.action_exit.triggered.connect(self.main_window.close)
        self.main_window.action_settings.triggered.connect(self.on_settings)
        self.main_window.action_about.triggered.connect(self.on_about)

        # Control panel signals
        # (These would be wired from control_panel widget signals)

    @pyqtSlot()
    def on_load_file(self) -> None:
        """Handle file loading trigger."""
        dialog = FileImportDialog(self.main_window)
        result = dialog.exec()
        
        if result == FileImportDialog.DialogCode.Accepted:
            software_type = dialog.get_software_type()
            path = dialog.get_path()
            
            # Launch file load worker
            self._load_experiment_file(software_type, path)

    def _load_experiment_file(self, software_type: str, path: str) -> None:
        """
        Load experiment file in background thread.

        Args:
            software_type: Type of file (ethovision, anymaze, etc.)
            path: Path to file or directory
        """
        self.file_load_worker = FileLoadWorker(software_type, path)
        self.file_load_worker.progress.connect(self._on_file_load_progress)
        self.file_load_worker.finished.connect(self._on_file_load_finished)
        self.file_load_worker.error.connect(self._on_file_load_error)
        
        # Update UI to show loading
        self.main_window.statusbar.showMessage("Loading experiment...")
        self.file_load_worker.start()

    @pyqtSlot(str)
    def _on_file_load_progress(self, status: str) -> None:
        """Update progress during file loading."""
        self.main_window.statusbar.showMessage(f"Loading: {status}")

    @pyqtSlot(object)
    def _on_file_load_finished(self, experiment: Experiment) -> None:
        """Handle successful file load."""
        self.current_experiment = experiment
        
        # Update UI
        self.main_window.statusbar.showMessage(
            f"Loaded: {len(experiment)} trials"
        )
        
        # Enable analysis button
        # (Connect to control panel's analyze_clicked signal)

    @pyqtSlot(str)
    def _on_file_load_error(self, error_msg: str) -> None:
        """Handle file load error."""
        QMessageBox.critical(self.main_window, "Load Error", error_msg)
        self.main_window.statusbar.showMessage("Load failed")

    @pyqtSlot()
    def on_settings(self) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(self.main_window, self.current_parameters)
        result = dialog.exec()
        
        if result == SettingsDialog.DialogCode.Accepted:
            self.current_parameters = dialog.get_parameters()
            self.main_window.statusbar.showMessage("Settings updated")

    @pyqtSlot()
    def on_about(self) -> None:
        """Show about dialog."""
        QMessageBox.information(
            self.main_window,
            "About Pathfinder",
            "Pathfinder 2.0 - Behavioral Analysis Tool\n"
            "Using clean PyQt6 interface with modular analysis engine\n"
            "© 2026 UBC Snyder Lab"
        )

    def run_analysis(self) -> None:
        """Start analysis of loaded experiment."""
        if not self.current_experiment:
            QMessageBox.warning(self.main_window, "No Data", "Load an experiment first")
            return

        if not self.current_parameters:
            QMessageBox.warning(self.main_window, "No Parameters", "Set analysis parameters first")
            return

        # Launch analysis worker
        self.analysis_worker = AnalysisWorker(
            self.current_experiment,
            self.current_parameters
        )
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.trial_completed.connect(self._on_trial_completed)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.error.connect(self._on_analysis_error)

        self.main_window.statusbar.showMessage("Starting analysis...")
        self.analysis_worker.start()

    @pyqtSlot(int, int)
    def _on_analysis_progress(self, current: int, total: int) -> None:
        """Update progress bar during analysis."""
        # Update main window progress bar
        percent = int((current / total) * 100) if total > 0 else 0
        self.main_window.statusbar.showMessage(
            f"Analyzing: {current}/{total} trials ({percent}%)"
        )

    @pyqtSlot(object)
    def _on_trial_completed(self, result: StrategyResult) -> None:
        """Handle completion of individual trial analysis."""
        self.current_results.append(result)
        # Could update UI in real-time here

    @pyqtSlot(list)
    def _on_analysis_finished(self, results: list[StrategyResult]) -> None:
        """Handle analysis completion."""
        self.current_results = results
        
        # Update results display in main window
        # self.main_window.results_table.load_results(results)
        # self.main_window.summary_widget.set_results(results)
        
        self.main_window.statusbar.showMessage(
            f"Analysis complete: {len(results)} trials analyzed"
        )

    @pyqtSlot(str)
    def _on_analysis_error(self, error_msg: str) -> None:
        """Handle analysis error."""
        QMessageBox.critical(self.main_window, "Analysis Error", error_msg)
        self.main_window.statusbar.showMessage("Analysis failed")

    def shutdown(self) -> None:
        """Clean up worker threads on application exit."""
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.request_abort()
            self.analysis_worker.wait()
        
        if self.heatmap_worker and self.heatmap_worker.isRunning():
            self.heatmap_worker.wait()
        
        if self.file_load_worker and self.file_load_worker.isRunning():
            self.file_load_worker.wait()
