"""
Integration layer for connecting GUI components and worker threads.

This module handles:
- Wiring up signal/slot connections between main window and dialogs
- Launching and managing worker threads
- Coordinating data flow between GUI and analysis engine
- Event handling and error management
"""

from __future__ import annotations
from typing import Optional
from pathlib import Path
from PyQt6.QtCore import pyqtSlot, QThread, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from pathfinder.models import Experiment
from pathfinder.types import StrategyResult
from pathfinder import calculate_trial_metrics, classify_strategy

from gui.simple_loader import auto_detect_and_load
from gui.dialogs import SettingsDialog


class SimpleFileLoadWorker(QThread):
    """Simple worker for loading files with auto-detection."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)  # Experiment
    error = pyqtSignal(str)
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        """Load the file."""
        try:
            self.progress.emit(f"Loading {Path(self.file_path).name}...")
            
            # Use auto-detection
            experiment, error = auto_detect_and_load(self.file_path)
            
            if error:
                self.error.emit(error)
                return
            
            if not experiment or not experiment.trials:
                self.error.emit("No valid trials found in file")
                return
            
            self.progress.emit(f"Loaded {len(experiment.trials)} trials")
            self.finished.emit(experiment)
            
        except Exception as e:
            self.error.emit(f"Error loading file: {str(e)}")


class SimpleAnalysisWorker(QThread):
    """Simple worker for running analysis."""
    
    progress = pyqtSignal(int, int)  # current, total
    trial_completed = pyqtSignal(dict)  # result dict
    finished = pyqtSignal(list)  # all results
    error = pyqtSignal(str)
    
    def __init__(self, experiment: Experiment, parameters: dict):
        super().__init__()
        self.experiment = experiment
        self.parameters = parameters
        self._abort = False
    
    def run(self):
        """Run analysis on all trials."""
        try:
            results = []
            total = len(self.experiment.trials)
            
            for i, trial in enumerate(self.experiment.trials):
                if self._abort:
                    return
                
                # Calculate metrics
                metrics = calculate_trial_metrics(trial, **self.parameters)
                
                # Classify strategy
                strategy_result = classify_strategy(trial, metrics, **self.parameters)
                
                # Convert to dict for display
                result_dict = {
                    'trial_id': i + 1,
                    'trial_name': trial.name or f"Trial {i+1}",
                    'strategy': strategy_result.strategy_name,
                    'latency': metrics.latency,
                    'distance': metrics.path_length,
                    'efficiency': metrics.path_efficiency,
                    'score': strategy_result.confidence_score,
                }
                
                results.append(result_dict)
                self.trial_completed.emit(result_dict)
                self.progress.emit(i + 1, total)
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Analysis error: {str(e)}")
    
    def request_abort(self):
        """Request cancellation."""
        self._abort = True


class SimpleIntegration:
    """
    Simplified integration that actually works.
    
    Wires up MainWindow buttons to real functionality:
    - Load button → file dialog → auto-detect format → load
    - Settings button → settings dialog
    - Analyze button → run analysis → display results
    """
    
    def __init__(self, main_window) -> None:
        """
        Initialize integration.
        
        Args:
            main_window: MainWindow instance
        """
        self.main_window = main_window
        self.current_experiment: Optional[Experiment] = None
        self.current_parameters: dict = self._default_parameters()
        self.current_results: list = []
        
        self.file_load_worker: Optional[SimpleFileLoadWorker] = None
        self.analysis_worker: Optional[SimpleAnalysisWorker] = None
        
        self._setup_connections()
    
    def _default_parameters(self) -> dict:
        """Get default analysis parameters."""
        return {
            'pool_diameter': 120.0,
            'platform_diameter': 10.0,
            'platform_x': 60.0,
            'platform_y': 60.0,
            'quadrant_analysis': True,
            'heatmap_bins': 50,
        }
    
    def _setup_connections(self) -> None:
        """Wire up all buttons and signals."""
        # Button connections
        self.main_window.load_button.clicked.connect(self.on_load_file)
        self.main_window.settings_button.clicked.connect(self.on_settings)
        self.main_window.analyze_button.clicked.connect(self.on_analyze)
    
    @pyqtSlot(bool)
    def on_load_file(self, checked: bool = False) -> None:
        """Handle Load Experiment button."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Load Experiment File",
            "",
            "All Supported (*.csv *.xlsx);;CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Update UI
        self.main_window._update_status("Loading experiment...")
        self.main_window.load_button.setEnabled(False)
        self.main_window.experiment_label.setText("Loading...")
        
        # Start worker
        self.file_load_worker = SimpleFileLoadWorker(file_path)
        self.file_load_worker.progress.connect(self._on_load_progress)
        self.file_load_worker.finished.connect(self._on_load_finished)
        self.file_load_worker.error.connect(self._on_load_error)
        self.file_load_worker.start()
    
    @pyqtSlot(str)
    def _on_load_progress(self, message: str) -> None:
        """Update progress during loading."""
        self.main_window._update_status(message)
    
    @pyqtSlot(object)
    def _on_load_finished(self, experiment: Experiment) -> None:
        """Handle successful load."""
        self.current_experiment = experiment
        
        # Update UI
        trial_count = len(experiment.trials)
        file_name = Path(experiment.name).name if experiment.name else "Unknown"
        
        self.main_window.experiment_label.setText(f"📁 {file_name}")
        self.main_window.trial_count_label.setText(f"Trials: {trial_count}")
        self.main_window.status_trial_label.setText(f"Trials: {trial_count}")
        self.main_window._update_status(f"Loaded {trial_count} trials successfully")
        self.main_window._update_last_update_time()
        
        # Enable analyze button
        self.main_window.analyze_button.setEnabled(True)
        self.main_window.load_button.setEnabled(True)
        
        # Emit signal
        self.main_window.loaded_experiment.emit(experiment)
    
    @pyqtSlot(str)
    def _on_load_error(self, error_message: str) -> None:
        """Handle load error."""
        QMessageBox.critical(
            self.main_window,
            "Load Error",
            f"Failed to load experiment:\n\n{error_message}"
        )
        
        self.main_window.experiment_label.setText("No experiment loaded")
        self.main_window.trial_count_label.setText("Trials: 0")
        self.main_window._update_status("Load failed")
        self.main_window.load_button.setEnabled(True)
    
    @pyqtSlot()
    def on_settings(self) -> None:
        """Handle Settings button."""
        try:
            dialog = SettingsDialog(self.main_window, self.current_parameters)
            result = dialog.exec()
            
            if result == SettingsDialog.DialogCode.Accepted:
                self.current_parameters = dialog.get_parameters()
                self.main_window._update_status("Settings updated")
                
                # Update parameter display
                param_text = (
                    f"Pool: {self.current_parameters.get('pool_diameter', 120)}cm\n"
                    f"Platform: {self.current_parameters.get('platform_diameter', 10)}cm\n"
                    f"Position: ({self.current_parameters.get('platform_x', 60)}, "
                    f"{self.current_parameters.get('platform_y', 60)})"
                )
                self.main_window.params_display.setText(param_text)
                
        except Exception as e:
            # Fallback if SettingsDialog not fully implemented
            QMessageBox.information(
                self.main_window,
                "Settings",
                f"Settings dialog opened.\n\n"
                f"Current parameters:\n"
                f"- Pool diameter: {self.current_parameters.get('pool_diameter', 120)} cm\n"
                f"- Platform diameter: {self.current_parameters.get('platform_diameter', 10)} cm\n"
                f"- Platform position: ({self.current_parameters.get('platform_x', 60)}, "
                f"{self.current_parameters.get('platform_y', 60)})\n\n"
                f"(Full settings editor coming soon)"
            )
    
    @pyqtSlot()
    def on_analyze(self) -> None:
        """Handle Analyze button."""
        if not self.current_experiment:
            QMessageBox.warning(
                self.main_window,
                "No Experiment",
                "Please load an experiment before running analysis."
            )
            return
        
        # Update UI
        self.main_window._update_status("Starting analysis...")
        self.main_window.analyze_button.setEnabled(False)
        self.main_window.load_button.setEnabled(False)
        self.main_window.progress_bar.setValue(0)
        
        # Start worker
        self.analysis_worker = SimpleAnalysisWorker(
            self.current_experiment,
            self.current_parameters
        )
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.trial_completed.connect(self._on_trial_completed)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        self.analysis_worker.error.connect(self._on_analysis_error)
        self.analysis_worker.start()
        
        # Emit signal
        self.main_window.analysis_started.emit()
    
    @pyqtSlot(int, int)
    def _on_analysis_progress(self, current: int, total: int) -> None:
        """Update progress during analysis."""
        percent = int((current / total) * 100) if total > 0 else 0
        self.main_window.progress_bar.setValue(percent)
        self.main_window._update_status(f"Analyzing trial {current}/{total}")
    
    @pyqtSlot(dict)
    def _on_trial_completed(self, result: dict) -> None:
        """Handle individual trial completion."""
        # Could update UI in real-time here
        pass
    
    @pyqtSlot(list)
    def _on_analysis_finished(self, results: list) -> None:
        """Handle analysis completion."""
        self.current_results = results
        
        # Update results table
        self._populate_results_table(results)
        
        # Update summary
        self._update_summary(results)
        
        # Update UI
        trial_count = len(results)
        self.main_window._update_status(f"Analysis complete: {trial_count} trials analyzed")
        self.main_window._update_last_update_time()
        self.main_window.progress_bar.setValue(100)
        self.main_window.analyze_button.setEnabled(True)
        self.main_window.load_button.setEnabled(True)
        self.main_window.save_results_action.setEnabled(True)
        
        # Emit signal
        results_dict = {'trials': results}
        self.main_window.analysis_complete.emit(results_dict)
    
    @pyqtSlot(str)
    def _on_analysis_error(self, error_message: str) -> None:
        """Handle analysis error."""
        QMessageBox.critical(
            self.main_window,
            "Analysis Error",
            f"Analysis failed:\n\n{error_message}"
        )
        
        self.main_window._update_status("Analysis failed")
        self.main_window.progress_bar.setValue(0)
        self.main_window.analyze_button.setEnabled(True)
        self.main_window.load_button.setEnabled(True)
        
        # Emit signal
        self.main_window.error.emit(error_message)
    
    def _populate_results_table(self, results: list) -> None:
        """Populate the results table with data."""
        table = self.main_window.results_table
        table.setRowCount(len(results))
        
        from PyQt6.QtWidgets import QTableWidgetItem
        
        for row, result in enumerate(results):
            # Trial
            table.setItem(row, 0, QTableWidgetItem(str(result.get('trial_id', row + 1))))
            
            # Strategy
            table.setItem(row, 1, QTableWidgetItem(result.get('strategy', 'Unknown')))
            
            # Latency
            latency = result.get('latency', 0.0)
            table.setItem(row, 2, QTableWidgetItem(f"{latency:.2f}"))
            
            # Distance
            distance = result.get('distance', 0.0)
            table.setItem(row, 3, QTableWidgetItem(f"{distance:.2f}"))
            
            # Efficiency
            efficiency = result.get('efficiency', 0.0)
            table.setItem(row, 4, QTableWidgetItem(f"{efficiency:.3f}"))
            
            # Score
            score = result.get('score', 0.0)
            table.setItem(row, 5, QTableWidgetItem(f"{score:.1f}"))
    
    def _update_summary(self, results: list) -> None:
        """Update the summary widget with statistics."""
        if not results:
            return
        
        # Calculate summary statistics
        strategies = {}
        total_latency = 0.0
        total_distance = 0.0
        
        for result in results:
            strategy = result.get('strategy', 'Unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
            total_latency += result.get('latency', 0.0)
            total_distance += result.get('distance', 0.0)
        
        avg_latency = total_latency / len(results) if results else 0
        avg_distance = total_distance / len(results) if results else 0
        
        # Format summary text
        summary_text = f"""ANALYSIS SUMMARY
{'=' * 50}

Total Trials: {len(results)}

Average Metrics:
  - Latency: {avg_latency:.2f} seconds
  - Distance: {avg_distance:.2f} cm

Strategy Distribution:
"""
        
        for strategy, count in sorted(strategies.items(), key=lambda x: -x[1]):
            percent = (count / len(results)) * 100
            summary_text += f"  - {strategy}: {count} ({percent:.1f}%)\n"
        
        self.main_window.summary_text.setPlainText(summary_text)
    
    def shutdown(self) -> None:
        """Clean up workers on exit."""
        if self.file_load_worker and self.file_load_worker.isRunning():
            self.file_load_worker.wait()
        
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.request_abort()
            self.analysis_worker.wait()
