"""
Custom PyQt6 widgets for Pathfinder GUI.

Provides specialized visualization and control widgets for Morris Water Maze analysis.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QProgressBar, QDialog, QMenu,
    QFileDialog, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

from pathfinder.types import HeatmapData, StrategyResult


class HeatmapWidget(QWidget):
    """
    Widget for displaying interactive heatmaps using matplotlib.
    
    Features:
    - Embedded matplotlib canvas with zoom and pan
    - Configurable colormaps
    - Image export functionality
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the HeatmapWidget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = self.figure.add_subplot(111)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # State
        self.current_data: Optional[np.ndarray] = None
        self.current_colormap: str = "viridis"
        self.image_handle = None
        
    def set_data(self, heatmap_data: HeatmapData) -> None:
        """
        Set and display heatmap data.
        
        Args:
            heatmap_data: HeatmapData object containing the numpy array to display
        """
        if heatmap_data is None or heatmap_data.data is None:
            self.clear()
            return
            
        self.current_data = heatmap_data.data
        self._render_heatmap()
        
    def set_colormap(self, name: str) -> None:
        """
        Change the colormap of the displayed heatmap.
        
        Args:
            name: Name of matplotlib colormap (e.g., 'viridis', 'hot', 'plasma')
        """
        self.current_colormap = name
        if self.current_data is not None:
            self._render_heatmap()
            
    def save_image(self, path: str) -> None:
        """
        Save the current heatmap to an image file.
        
        Args:
            path: File path to save the image (format determined by extension)
        """
        if self.current_data is None:
            raise ValueError("No heatmap data to save")
            
        self.figure.savefig(path, dpi=300, bbox_inches='tight')
        
    def clear(self) -> None:
        """Clear the heatmap display."""
        self.ax.clear()
        self.current_data = None
        self.canvas.draw()
        
    def _render_heatmap(self) -> None:
        """Internal method to render the heatmap on the canvas."""
        self.ax.clear()
        
        if self.current_data is None:
            self.canvas.draw()
            return
            
        self.image_handle = self.ax.imshow(
            self.current_data,
            cmap=self.current_colormap,
            interpolation='bilinear',
            aspect='auto'
        )
        
        # Add colorbar
        if self.figure.axes:
            # Remove old colorbar if exists
            if len(self.figure.axes) > 1:
                self.figure.delaxes(self.figure.axes[-1])
        
        self.figure.colorbar(self.image_handle, ax=self.ax)
        
        self.ax.set_title("Occupancy Heatmap")
        self.canvas.draw()


class ResultsTableWidget(QTableWidget):
    """
    Table widget for displaying analysis results with sorting and context menu.
    
    Signals:
        trial_selected: Emitted when a trial is selected (trial_name: str)
    """
    
    trial_selected = pyqtSignal(str)
    
    COLUMNS = [
        "Trial Name",
        "Animal",
        "Strategy",
        "Score",
        "Entropy",
        "IPE",
        "Distance",
        "Velocity"
    ]
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the ResultsTableWidget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Configure table
        self.setColumnCount(len(self.COLUMNS))
        self.setHorizontalHeaderLabels(self.COLUMNS)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        
        # Resize columns
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)
        
        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Selection signal
        self.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Data storage
        self.results_data: List[StrategyResult] = []
        
    def load_results(self, results: List[StrategyResult]) -> None:
        """
        Load analysis results into the table.
        
        Args:
            results: List of StrategyResult objects to display
        """
        self.results_data = results
        self.setRowCount(len(results))
        
        for row, result in enumerate(results):
            self._populate_row(row, result)
            
    def get_selected_trial(self) -> Optional[str]:
        """
        Get the trial name of the currently selected row.
        
        Returns:
            Trial name or None if no selection
        """
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return None
            
        row = selected_rows[0].row()
        trial_item = self.item(row, 0)
        return trial_item.text() if trial_item else None
        
    def highlight_trial(self, trial_name: str) -> None:
        """
        Highlight and scroll to a specific trial.
        
        Args:
            trial_name: Name of the trial to highlight
        """
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.text() == trial_name:
                self.selectRow(row)
                self.scrollToItem(item)
                break
                
    def _populate_row(self, row: int, result: StrategyResult) -> None:
        """Populate a table row with result data."""
        # Trial Name
        self.setItem(row, 0, QTableWidgetItem(result.trial_name))
        
        # Animal
        self.setItem(row, 1, QTableWidgetItem(result.animal_id))
        
        # Strategy
        strategy_item = QTableWidgetItem(result.strategy)
        strategy_item.setBackground(QColor(self._get_strategy_color(result.strategy)))
        self.setItem(row, 2, strategy_item)
        
        # Score
        self.setItem(row, 3, self._create_numeric_item(result.score, "%.2f"))
        
        # Entropy
        self.setItem(row, 4, self._create_numeric_item(result.entropy, "%.3f"))
        
        # IPE
        self.setItem(row, 5, self._create_numeric_item(result.ipe, "%.3f"))
        
        # Distance
        self.setItem(row, 6, self._create_numeric_item(result.distance, "%.1f"))
        
        # Velocity
        self.setItem(row, 7, self._create_numeric_item(result.velocity, "%.2f"))
        
    def _create_numeric_item(self, value: Optional[float], fmt: str) -> QTableWidgetItem:
        """Create a table item for numeric values with proper formatting and sorting."""
        if value is None:
            item = QTableWidgetItem("N/A")
        else:
            item = QTableWidgetItem(fmt % value)
            item.setData(Qt.ItemDataRole.UserRole, value)  # For proper numeric sorting
            
        return item
        
    def _get_strategy_color(self, strategy: str) -> str:
        """Get background color for strategy cell."""
        colors = {
            "Direct": "#90EE90",      # Light green
            "Focal": "#87CEEB",       # Sky blue
            "Directed": "#FFD700",    # Gold
            "Chaining": "#FFA500",    # Orange
            "Scanning": "#DDA0DD",    # Plum
            "Random": "#F08080",      # Light coral
            "Thigmotaxis": "#CD5C5C", # Indian red
        }
        return colors.get(strategy, "#FFFFFF")
        
    def _show_context_menu(self, position) -> None:
        """Show right-click context menu."""
        menu = QMenu(self)
        
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self._copy_selected)
        menu.addAction(copy_action)
        
        export_action = QAction("Export to CSV", self)
        export_action.triggered.connect(self._export_to_csv)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        manual_classify_action = QAction("Manual Classification", self)
        manual_classify_action.triggered.connect(self._manual_classification)
        menu.addAction(manual_classify_action)
        
        menu.exec(self.viewport().mapToGlobal(position))
        
    def _copy_selected(self) -> None:
        """Copy selected row to clipboard."""
        trial_name = self.get_selected_trial()
        if trial_name:
            # Find the result
            for result in self.results_data:
                if result.trial_name == trial_name:
                    text = f"{result.trial_name}\t{result.animal_id}\t{result.strategy}\t{result.score}"
                    from PyQt6.QtGui import QGuiApplication
                    QGuiApplication.clipboard().setText(text)
                    break
                    
    def _export_to_csv(self) -> None:
        """Export all results to CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.COLUMNS)
                
                for result in self.results_data:
                    writer.writerow([
                        result.trial_name,
                        result.animal_id,
                        result.strategy,
                        result.score,
                        result.entropy,
                        result.ipe,
                        result.distance,
                        result.velocity
                    ])
                    
    def _manual_classification(self) -> None:
        """Open manual classification dialog (placeholder)."""
        QMessageBox.information(
            self,
            "Manual Classification",
            "Manual classification dialog will be implemented."
        )
        
    def _on_selection_changed(self) -> None:
        """Handle selection changes."""
        trial_name = self.get_selected_trial()
        if trial_name:
            self.trial_selected.emit(trial_name)


class ControlPanelWidget(QWidget):
    """
    Control panel widget for experiment loading and analysis control.
    
    Signals:
        load_clicked: Emitted when Load Experiment is clicked
        analyze_clicked: Emitted when Analyze is clicked
        settings_clicked: Emitted when Settings is clicked
    """
    
    load_clicked = pyqtSignal()
    analyze_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the ControlPanelWidget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Load Experiment section
        self.load_button = QPushButton("Load Experiment")
        self.load_button.clicked.connect(self.load_clicked.emit)
        layout.addWidget(self.load_button)
        
        self.status_label = QLabel("No experiment loaded")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addSpacing(10)
        
        # Software type selector
        software_layout = QVBoxLayout()
        software_label = QLabel("Software Type:")
        software_layout.addWidget(software_label)
        
        self.software_combo = QComboBox()
        self.software_combo.addItems(["EthoVision", "ANY-maze", "WaterMaze"])
        software_layout.addWidget(self.software_combo)
        layout.addLayout(software_layout)
        
        layout.addSpacing(10)
        
        # Parameter summary
        param_label = QLabel("<b>Current Parameters:</b>")
        layout.addWidget(param_label)
        
        self.param_summary = QLabel("Pool radius: 60 cm\nPlatform radius: 5 cm\nFPS: 30")
        self.param_summary.setWordWrap(True)
        self.param_summary.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        layout.addWidget(self.param_summary)
        
        layout.addSpacing(10)
        
        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_button)
        
        layout.addSpacing(10)
        
        # Analyze button
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.analyze_clicked.emit)
        layout.addWidget(self.analyze_button)
        
        layout.addSpacing(20)
        
        # Progress section
        progress_label = QLabel("Progress:")
        layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.progress_status = QLabel("Ready")
        self.progress_status.setWordWrap(True)
        layout.addWidget(self.progress_status)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
    def set_experiment_loaded(self, loaded: bool, experiment_name: str = "") -> None:
        """
        Update the UI state based on whether an experiment is loaded.
        
        Args:
            loaded: True if experiment is loaded
            experiment_name: Name of the loaded experiment
        """
        if loaded:
            self.status_label.setText(f"Loaded: {experiment_name}")
            self.analyze_button.setEnabled(True)
        else:
            self.status_label.setText("No experiment loaded")
            self.analyze_button.setEnabled(False)
            
    def set_progress(self, value: int, message: str = "") -> None:
        """
        Update the progress bar and status message.
        
        Args:
            value: Progress percentage (0-100)
            message: Status message to display
        """
        self.progress_bar.setValue(value)
        if message:
            self.progress_status.setText(message)
            
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """
        Update the parameter summary display.
        
        Args:
            params: Dictionary of parameter names and values
        """
        summary_lines = [f"{key}: {value}" for key, value in params.items()]
        self.param_summary.setText("\n".join(summary_lines))
        
    def get_software_type(self) -> str:
        """
        Get the currently selected software type.
        
        Returns:
            Software type name
        """
        return self.software_combo.currentText()


class SummaryWidget(QWidget):
    """
    Widget for displaying statistical summaries with charts and tables.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the SummaryWidget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create matplotlib figures
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Create subplots
        self.ax_pie = self.figure.add_subplot(221)      # Strategy distribution
        self.ax_hist = self.figure.add_subplot(222)     # Score distribution
        self.ax_metrics = self.figure.add_subplot(212)  # Metrics table
        
        self.results: List[StrategyResult] = []
        
    def set_results(self, results: List[StrategyResult]) -> None:
        """
        Display summary statistics for the given results.
        
        Args:
            results: List of StrategyResult objects to summarize
        """
        self.results = results
        self._render_summary()
        
    def clear(self) -> None:
        """Clear all charts and data."""
        for ax in [self.ax_pie, self.ax_hist, self.ax_metrics]:
            ax.clear()
        self.canvas.draw()
        
    def _render_summary(self) -> None:
        """Render all summary visualizations."""
        if not self.results:
            self.clear()
            return
            
        # Clear axes
        for ax in [self.ax_pie, self.ax_hist, self.ax_metrics]:
            ax.clear()
            
        # Strategy distribution (pie chart)
        self._render_strategy_distribution()
        
        # Score distribution (histogram)
        self._render_score_distribution()
        
        # Average metrics table
        self._render_metrics_table()
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _render_strategy_distribution(self) -> None:
        """Render pie chart of strategy distribution."""
        strategies = [r.strategy for r in self.results]
        strategy_counts = {}
        
        for strategy in strategies:
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
        labels = list(strategy_counts.keys())
        sizes = list(strategy_counts.values())
        
        self.ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        self.ax_pie.set_title("Strategy Distribution")
        
    def _render_score_distribution(self) -> None:
        """Render histogram of score distribution."""
        scores = [r.score for r in self.results if r.score is not None]
        
        if scores:
            self.ax_hist.hist(scores, bins=20, edgecolor='black', alpha=0.7)
            self.ax_hist.set_xlabel("Score")
            self.ax_hist.set_ylabel("Frequency")
            self.ax_hist.set_title("Score Distribution")
            self.ax_hist.grid(True, alpha=0.3)
        
    def _render_metrics_table(self) -> None:
        """Render table of average metrics."""
        # Calculate success metrics (percentage of each strategy)
        strategies = [r.strategy for r in self.results]
        total = len(strategies)
        
        strategy_percentages = {}
        for strategy in set(strategies):
            count = strategies.count(strategy)
            strategy_percentages[strategy] = (count / total) * 100
            
        # Calculate average metrics
        scores = [r.score for r in self.results if r.score is not None]
        entropies = [r.entropy for r in self.results if r.entropy is not None]
        ipes = [r.ipe for r in self.results if r.ipe is not None]
        distances = [r.distance for r in self.results if r.distance is not None]
        velocities = [r.velocity for r in self.results if r.velocity is not None]
        
        # Create table data
        table_data = [
            ["Metric", "Value"],
            ["Total Trials", str(total)],
            ["Average Score", f"{np.mean(scores):.2f}" if scores else "N/A"],
            ["Average Entropy", f"{np.mean(entropies):.3f}" if entropies else "N/A"],
            ["Average IPE", f"{np.mean(ipes):.3f}" if ipes else "N/A"],
            ["Average Distance", f"{np.mean(distances):.1f}" if distances else "N/A"],
            ["Average Velocity", f"{np.mean(velocities):.2f}" if velocities else "N/A"],
        ]
        
        # Add strategy percentages
        for strategy, pct in sorted(strategy_percentages.items()):
            table_data.append([f"% {strategy}", f"{pct:.1f}%"])
        
        # Render table
        self.ax_metrics.axis('tight')
        self.ax_metrics.axis('off')
        
        table = self.ax_metrics.table(
            cellText=table_data,
            cellLoc='left',
            loc='center',
            colWidths=[0.4, 0.3]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)
        
        # Header styling
        for i in range(2):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        self.ax_metrics.set_title("Average Metrics", fontweight='bold', pad=20)


class ProgressDialog(QDialog):
    """
    Dialog for showing analysis progress with cancel capability.
    
    Signals:
        cancelled: Emitted when the user clicks Cancel
    """
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the ProgressDialog.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Analysis Progress")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Current trial label
        self.trial_label = QLabel("Preparing analysis...")
        layout.addWidget(self.trial_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("0 / 0 trials completed")
        layout.addWidget(self.status_label)
        
        layout.addSpacing(10)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)
        
        # State
        self.total_trials: int = 0
        self.completed_trials: int = 0
        self.auto_close_enabled: bool = True
        
    def start_analysis(self, total_trials: int) -> None:
        """
        Start the analysis progress tracking.
        
        Args:
            total_trials: Total number of trials to analyze
        """
        self.total_trials = total_trials
        self.completed_trials = 0
        self.progress_bar.setValue(0)
        self.status_label.setText(f"0 / {total_trials} trials completed")
        self.show()
        
    def update_progress(self, trial_name: str, completed: int) -> None:
        """
        Update the progress display.
        
        Args:
            trial_name: Name of the trial currently being analyzed
            completed: Number of trials completed so far
        """
        self.completed_trials = completed
        self.trial_label.setText(f"Analyzing: {trial_name}")
        
        if self.total_trials > 0:
            try:
                pct = (completed / self.total_trials) * 100
                if isinstance(pct, float) and (math.isnan(pct) or math.isinf(pct)):
                    progress_pct = 0
                else:
                    progress_pct = int(pct)
            except Exception:
                progress_pct = 0
            self.progress_bar.setValue(progress_pct)
            
        self.status_label.setText(f"{completed} / {self.total_trials} trials completed")
        
        # Auto-close when complete
        if completed >= self.total_trials and self.auto_close_enabled:
            self.accept()
            
    def set_auto_close(self, enabled: bool) -> None:
        """
        Enable or disable auto-close on completion.
        
        Args:
            enabled: True to auto-close, False to stay open
        """
        self.auto_close_enabled = enabled
        
    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.cancelled.emit()
        self.reject()
