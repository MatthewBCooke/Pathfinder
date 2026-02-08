"""
Heatmap widget for visualizing trajectory patterns and occupancy.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QGroupBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List
from pathfinder.core.models import Experiment, Trial
from scipy.ndimage import gaussian_filter


class HeatmapWidget(QWidget):
    """
    Trajectory visualization widget with:
    - Heatmap of spatial occupancy
    - Individual trial paths
    - Day/strategy filtering
    - Export capability
    """
    
    # Signals
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._experiment: Optional[Experiment] = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Controls
        controls = self._create_controls()
        layout.addWidget(controls)
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(8, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        
        # Canvas
        layout.addWidget(self.canvas)
        
        # Initial empty plot
        self._plot_empty()
    
    def _create_controls(self):
        """Create control panel"""
        group = QGroupBox("Visualization Controls")
        layout = QHBoxLayout()
        
        # Visualization type
        layout.addWidget(QLabel("Type:"))
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItems([
            "Heatmap (All Trials)",
            "Heatmap (By Day)",
            "Individual Paths",
            "Strategy Comparison"
        ])
        self.viz_type_combo.currentIndexChanged.connect(self._on_viz_type_changed)
        layout.addWidget(self.viz_type_combo)
        
        # Day filter
        layout.addWidget(QLabel("Day:"))
        self.day_combo = QComboBox()
        self.day_combo.addItem("All Days", None)
        self.day_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.day_combo)
        
        layout.addStretch()
        
        # Generate button
        self.generate_btn = QPushButton("🔄 Regenerate")
        self.generate_btn.clicked.connect(self._generate_plot)
        layout.addWidget(self.generate_btn)
        
        # Export button
        self.export_btn = QPushButton("💾 Export Image")
        self.export_btn.clicked.connect(self.export_requested.emit)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
    
    def set_experiment(self, experiment: Experiment):
        """Load experiment data for visualization"""
        self._experiment = experiment
        
        if not experiment:
            self._plot_empty()
            return
        
        # Update day filter
        self.day_combo.clear()
        self.day_combo.addItem("All Days", None)
        
        days = sorted(set(t.day for t in experiment.trials))
        for day in days:
            self.day_combo.addItem(f"Day {day}", day)
        
        # Generate initial plot
        self._generate_plot()
    
    def _on_viz_type_changed(self, index: int):
        """Handle visualization type change"""
        self._generate_plot()
    
    def _on_filter_changed(self, index: int):
        """Handle filter change"""
        self._generate_plot()
    
    def _generate_plot(self):
        """Generate the selected visualization"""
        if not self._experiment or not self._experiment.trials:
            self._plot_empty()
            return
        
        viz_type = self.viz_type_combo.currentText()
        
        if "Heatmap" in viz_type:
            self._plot_heatmap()
        elif "Individual Paths" in viz_type:
            self._plot_individual_paths()
        elif "Strategy Comparison" in viz_type:
            self._plot_strategy_comparison()
    
    def _plot_empty(self):
        """Show empty placeholder"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, "No data to visualize\nLoad an experiment and run analysis",
                    ha='center', va='center', fontsize=14, color='gray')
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        self.canvas.draw()
    
    def _plot_heatmap(self):
        """Generate occupancy heatmap with NaN/Inf checks"""
        self.ax.clear()
        # Clear all colorbars to prevent multiple legend bars
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        # Get filtered trials
        trials = self._get_filtered_trials()
        if not trials:
            self._plot_empty()
            return

        # Get pool geometry from first trial
        trial = trials[0]
        pool_center = trial.pool_center
        pool_radius = trial.pool_diameter / 2

        # Create occupancy grid
        grid_size = 100
        x_bins = np.linspace(pool_center[0] - pool_radius,
                             pool_center[0] + pool_radius, grid_size)
        y_bins = np.linspace(pool_center[1] - pool_radius,
                             pool_center[1] + pool_radius, grid_size)

        occupancy = np.zeros((grid_size - 1, grid_size - 1))

        # Accumulate trajectory points, skipping NaN/Inf
        for trial in trials:
            for point in trial.trajectory:
                x, y = point.x, point.y
                if (
                    x is None or y is None or
                    np.isnan(x) or np.isnan(y) or
                    np.isinf(x) or np.isinf(y)
                ):
                    continue  # Skip invalid points
                x_idx = np.digitize(x, x_bins) - 1
                y_idx = np.digitize(y, y_bins) - 1
                if 0 <= x_idx < grid_size - 1 and 0 <= y_idx < grid_size - 1:
                    occupancy[y_idx, x_idx] += 1

        # Smooth the heatmap
        occupancy_smooth = gaussian_filter(occupancy, sigma=2.0)

        # Replace any NaN/Inf in bins and occupancy with 0
        if np.any(np.isnan(x_bins)) or np.any(np.isinf(x_bins)):
            x_bins = np.nan_to_num(x_bins, nan=0.0, posinf=0.0, neginf=0.0)
        if np.any(np.isnan(y_bins)) or np.any(np.isinf(y_bins)):
            y_bins = np.nan_to_num(y_bins, nan=0.0, posinf=0.0, neginf=0.0)
        if np.any(np.isnan(occupancy_smooth)) or np.any(np.isinf(occupancy_smooth)):
            occupancy_smooth = np.nan_to_num(occupancy_smooth, nan=0.0, posinf=0.0, neginf=0.0)

        # Plot heatmap
        im = self.ax.imshow(occupancy_smooth, cmap='hot', origin='lower',
                            extent=[x_bins[0], x_bins[-1], y_bins[0], y_bins[-1]],
                            interpolation='bilinear')

        # Add pool boundary
        circle = plt.Circle(pool_center, pool_radius, color='cyan',
                            fill=False, linewidth=2, linestyle='--')
        self.ax.add_patch(circle)

        # Add platform location
        platform = plt.Circle(trial.platform_position, trial.platform_diameter / 2,
                              color='lime', fill=True, alpha=0.5, label='Platform')
        self.ax.add_patch(platform)

        # Formatting
        self.ax.set_aspect('equal')
        self.ax.set_title(f'Occupancy Heatmap ({len(trials)} trials)', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('X Position')
        self.ax.set_ylabel('Y Position')

        # Colorbar
        cbar = self.figure.colorbar(im, ax=self.ax)
        cbar.set_label('Occupancy', rotation=270, labelpad=15)

        self.ax.legend(loc='upper right')

        self.canvas.draw()
    
    def _plot_individual_paths(self):
        """Plot individual trial trajectories"""
        self.ax.clear()
        
        trials = self._get_filtered_trials()
        if not trials:
            self._plot_empty()
            return
        
        # Get pool geometry
        trial = trials[0]
        pool_center = trial.pool_center
        pool_radius = trial.pool_diameter / 2
        
        # Plot pool boundary
        circle = plt.Circle(pool_center, pool_radius, color='black', 
                           fill=False, linewidth=2)
        self.ax.add_patch(circle)
        
        # Plot platform
        platform = plt.Circle(trial.platform_position, trial.platform_diameter / 2,
                             color='red', fill=True, alpha=0.5, label='Platform')
        self.ax.add_patch(platform)
        
        # Plot each trial path
        for i, trial in enumerate(trials[:10]):  # Limit to first 10 for clarity
            x = [p.x for p in trial.trajectory]
            y = [p.y for p in trial.trajectory]
            
            # Color by trial number
            color = plt.cm.viridis(i / len(trials[:10]))
            self.ax.plot(x, y, color=color, alpha=0.6, linewidth=1, 
                        label=f'Trial {trial.trial_number}')
            
            # Mark start point
            if x and y:
                self.ax.plot(x[0], y[0], 'go', markersize=6, alpha=0.7)
        
        self.ax.set_aspect('equal')
        self.ax.set_title(f'Individual Trajectories (showing {min(len(trials), 10)} trials)', 
                         fontsize=12, fontweight='bold')
        self.ax.set_xlabel('X Position')
        self.ax.set_ylabel('Y Position')
        self.ax.legend(loc='upper right', fontsize=8)
        
        self.canvas.draw()
    
    def _plot_strategy_comparison(self):
        """Compare trajectories by strategy"""
        self.ax.clear()
        
        trials = self._get_filtered_trials()
        if not trials:
            self._plot_empty()
            return
        
        # Group by strategy
        from collections import defaultdict
        strategy_trials = defaultdict(list)
        
        for trial in trials:
            if trial.search_strategy:
                strategy_trials[trial.search_strategy].append(trial)
        
        if not strategy_trials:
            self.ax.text(0.5, 0.5, "No strategies classified yet",
                        ha='center', va='center', fontsize=14, color='gray',
                        transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        # Get pool geometry
        trial = trials[0]
        pool_center = trial.pool_center
        pool_radius = trial.pool_diameter / 2
        
        # Plot pool
        circle = plt.Circle(pool_center, pool_radius, color='black', 
                           fill=False, linewidth=2)
        self.ax.add_patch(circle)
        
        # Plot platform
        platform = plt.Circle(trial.platform_position, trial.platform_diameter / 2,
                             color='red', fill=True, alpha=0.5)
        self.ax.add_patch(platform)
        
        # Plot one example per strategy
        colors = plt.cm.tab10.colors
        for i, (strategy, trials_list) in enumerate(strategy_trials.items()):
            if trials_list:
                example = trials_list[0]
                x = [p.x for p in example.trajectory]
                y = [p.y for p in example.trajectory]
                
                self.ax.plot(x, y, color=colors[i % len(colors)], 
                           linewidth=2, alpha=0.8, label=strategy.value)
        
        self.ax.set_aspect('equal')
        self.ax.set_title('Strategy Examples', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('X Position')
        self.ax.set_ylabel('Y Position')
        self.ax.legend(loc='upper right', fontsize=9)
        
        self.canvas.draw()
    
    def _get_filtered_trials(self) -> List[Trial]:
        """Get trials based on current filter settings"""
        if not self._experiment:
            return []
        
        trials = self._experiment.trials
        
        # Filter by day
        selected_day = self.day_combo.currentData()
        if selected_day is not None:
            trials = [t for t in trials if t.day == selected_day]
        
        return trials
    
    def export_image(self, filename: str):
        """Export current plot to file"""
        self.figure.savefig(filename, dpi=300, bbox_inches='tight')
    
    def clear(self):
        """Clear visualization"""
        self._experiment = None
        self.day_combo.clear()
        self.day_combo.addItem("All Days", None)
        self._plot_empty()
