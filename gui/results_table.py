"""
Results table widget for displaying trial analysis results.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QHBoxLayout,
    QMenu, QAction, QSplitter, QFrame, QLabel
)
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QColor, QBrush
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Dict
from pathfinder.core.models import Trial, SearchStrategy, Experiment


class ResultsTableWidget(QWidget):
    """
    Table displaying trial-by-trial analysis results with:
    - Trial metadata (ID, day, trial #)
    - Detected strategy
    - Key metrics (latency, path length, speed)
    - Manual override capability
    """
    
    # Signals
    trial_selected = pyqtSignal(int)  # row index (0-based)
    manual_classification_requested = pyqtSignal(str)  # trial_id
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._experiment: Optional[Experiment] = None
        self._expanded_row: Optional[int] = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for table and path view
        self.splitter = QSplitter(Qt.Vertical)

        # Table widget container
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Table widget
        self.table = QTableWidget()
        self.table.setColumnCount(16)
        self.table.setHorizontalHeaderLabels([
            "Day",
            "Trial #",
            "Strategy",
            "Latency (s)",
            "Path (cm)",
            "Speed (cm/s)",
            "IPE",
            "Heading Avg (°)",
            "Heading Max (°)",
            "Corridor (%)",
            "Coverage (%)",
            "Chaining (%)",
            "Quadrants",
            "Thigmo Full (%)",
            "Thigmo Small (%)",
            "Manual"
        ])
        
        # Table configuration
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)   # Day
        header.setSectionResizeMode(1, QHeaderView.Fixed)   # Trial #
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Strategy
        for i in range(3, 16):
            header.setSectionResizeMode(i, QHeaderView.Fixed)

        self.table.setColumnWidth(0, 50)    # Day
        self.table.setColumnWidth(1, 60)    # Trial #
        self.table.setColumnWidth(3, 90)    # Latency
        self.table.setColumnWidth(4, 90)    # Path
        self.table.setColumnWidth(5, 90)    # Speed
        self.table.setColumnWidth(6, 80)    # IPE
        self.table.setColumnWidth(7, 110)   # Heading Avg
        self.table.setColumnWidth(8, 110)   # Heading Max
        self.table.setColumnWidth(9, 90)    # Corridor
        self.table.setColumnWidth(10, 90)   # Coverage
        self.table.setColumnWidth(11, 90)   # Chaining
        self.table.setColumnWidth(12, 80)   # Quadrants
        self.table.setColumnWidth(13, 110)  # Thigmo Full
        self.table.setColumnWidth(14, 110)  # Thigmo Small
        self.table.setColumnWidth(15, 60)   # Manual
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.cellClicked.connect(self._on_cell_clicked)

        table_layout.addWidget(self.table)
        
        # Button bar
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 Export to CSV")
        self.export_btn.clicked.connect(self.export_requested.emit)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()

        self.classify_btn = QPushButton("✏ Manual Classification")
        self.classify_btn.clicked.connect(self._on_manual_classify)
        self.classify_btn.setEnabled(False)
        button_layout.addWidget(self.classify_btn)

        table_layout.addLayout(button_layout)

        # Add table container to splitter
        self.splitter.addWidget(table_container)

        # Path visualization panel (initially hidden)
        self.path_panel = QFrame()
        self.path_panel.setFrameShape(QFrame.StyledPanel)
        self.path_panel_layout = QVBoxLayout(self.path_panel)
        self.path_panel_layout.setContentsMargins(5, 5, 5, 5)

        # Path title label
        self.path_title = QLabel("Click a trial to view its path")
        self.path_title.setStyleSheet("font-weight: bold; font-size: 11pt; padding: 5px;")
        self.path_panel_layout.addWidget(self.path_title)

        # Matplotlib canvas for path
        self.path_figure = Figure(figsize=(8, 6))
        self.path_canvas = FigureCanvas(self.path_figure)
        self.path_canvas.setMinimumHeight(300)
        self.path_panel_layout.addWidget(self.path_canvas)

        # Close button
        close_btn = QPushButton("✕ Close Path View")
        close_btn.clicked.connect(self._close_path_view)
        self.path_panel_layout.addWidget(close_btn)

        # Add path panel to splitter
        self.splitter.addWidget(self.path_panel)

        # Initially hide path panel
        self.path_panel.setVisible(False)
        self.splitter.setSizes([1000, 0])  # All space to table

        layout.addWidget(self.splitter)
    
    def load_results(self, experiment: Experiment):
        """Load experiment results into the table"""
        self._experiment = experiment
        self.table.setRowCount(0)  # Clear existing
        
        if not experiment or not experiment.trials:
            return
        
        self.table.setSortingEnabled(False)  # Disable during population
        
        for trial in experiment.trials:
            self._add_trial_row(trial)
        
        self.table.setSortingEnabled(True)
        self.table.sortItems(0, Qt.AscendingOrder)  # Sort by day
    
    def _add_trial_row(self, trial: Trial):
        """Add a single trial to the table with all metrics"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Get metrics if available
        metrics = getattr(trial, '_metrics', None)

        # Helper to create numeric item
        def make_numeric_item(value, fmt=".1f"):
            item = QTableWidgetItem()
            if value is not None:
                try:
                    item.setData(Qt.DisplayRole, f"{value:{fmt}}")
                except:
                    item.setData(Qt.DisplayRole, "—")
            else:
                item.setData(Qt.DisplayRole, "—")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return item

        # Day
        day_item = QTableWidgetItem()
        day_item.setData(Qt.DisplayRole, trial.day)
        day_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, day_item)

        # Trial number
        trial_num_item = QTableWidgetItem()
        trial_num_item.setData(Qt.DisplayRole, trial.trial_number)
        trial_num_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 1, trial_num_item)

        # Strategy
        strategy_text = trial.search_strategy.value if trial.search_strategy else "Not analyzed"
        strategy_item = QTableWidgetItem(strategy_text)

        # Color-code by strategy
        if trial.search_strategy:
            color = self._get_strategy_color(trial.search_strategy)
            strategy_item.setBackground(QBrush(color))

        self.table.setItem(row, 2, strategy_item)

        # Escape latency
        self.table.setItem(row, 3, make_numeric_item(trial.escape_latency, ".2f"))

        # Path length
        self.table.setItem(row, 4, make_numeric_item(trial.path_length, ".1f"))

        # Swim speed
        self.table.setItem(row, 5, make_numeric_item(trial.swim_speed, ".1f"))

        # IPE (Ideal Path Error)
        ipe = metrics.ipe if metrics else None
        self.table.setItem(row, 6, make_numeric_item(ipe, ".1f"))

        # Heading Error Average
        heading_avg = metrics.average_heading_error if metrics else None
        self.table.setItem(row, 7, make_numeric_item(heading_avg, ".1f"))

        # Heading Error Max (use initial heading error as proxy for max)
        heading_max = metrics.average_initial_heading_error if metrics else None
        self.table.setItem(row, 8, make_numeric_item(heading_max, ".1f"))

        # Time in Corridor (%)
        corridor_pct = (metrics.corridor_average * 100) if metrics else None
        self.table.setItem(row, 9, make_numeric_item(corridor_pct, ".1f"))

        # Pool Coverage (%)
        coverage = metrics.percent_traversed if metrics else None
        self.table.setItem(row, 10, make_numeric_item(coverage, ".1f"))

        # Time in Chaining Zone (%)
        if metrics:
            chaining_pct = (metrics.annulus_counter / metrics.sample_count * 100) if metrics.sample_count > 0 else None
        else:
            chaining_pct = None
        self.table.setItem(row, 11, make_numeric_item(chaining_pct, ".1f"))

        # Quadrants Visited
        quadrants = metrics.quadrant_total if metrics else None
        quadrants_item = QTableWidgetItem()
        if quadrants is not None:
            quadrants_item.setData(Qt.DisplayRole, str(int(quadrants)))
        else:
            quadrants_item.setData(Qt.DisplayRole, "—")
        quadrants_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 12, quadrants_item)

        # Thigmotaxis Full Zone (%)
        if metrics:
            thigmo_full_pct = (metrics.full_thigmo_counter / metrics.sample_count * 100) if metrics.sample_count > 0 else None
        else:
            thigmo_full_pct = None
        self.table.setItem(row, 13, make_numeric_item(thigmo_full_pct, ".1f"))

        # Thigmotaxis Small Zone (%)
        if metrics:
            thigmo_small_pct = (metrics.small_thigmo_counter / metrics.sample_count * 100) if metrics.sample_count > 0 else None
        else:
            thigmo_small_pct = None
        self.table.setItem(row, 14, make_numeric_item(thigmo_small_pct, ".1f"))

        # Manual classification flag
        manual_item = QTableWidgetItem("✓" if trial.manual_categorization else "")
        manual_item.setTextAlignment(Qt.AlignCenter)
        if trial.manual_categorization:
            manual_item.setForeground(QBrush(QColor("#FF9800")))
        self.table.setItem(row, 15, manual_item)

        # Store trial_id in row data
        day_item.setData(Qt.UserRole, trial.trial_id)
    
    def _get_strategy_color(self, strategy: SearchStrategy) -> QColor:
        """Return color for strategy visualization"""
        colors = {
            SearchStrategy.DIRECT_SWIM: QColor("#4CAF50"),        # Green
            SearchStrategy.DIRECTED_SEARCH: QColor("#8BC34A"),    # Light green
            SearchStrategy.FOCAL_SEARCH: QColor("#FFEB3B"),       # Yellow
            SearchStrategy.SPATIAL_INDIRECT: QColor("#FFC107"),   # Amber
            SearchStrategy.CHAINING: QColor("#FF9800"),           # Orange
            SearchStrategy.SCANNING: QColor("#FF5722"),           # Deep orange
            SearchStrategy.THIGMOTAXIS: QColor("#F44336"),        # Red
            SearchStrategy.RANDOM_SEARCH: QColor("#9E9E9E"),      # Gray
            SearchStrategy.NOT_RECOGNIZED: QColor("#757575"),     # Dark gray
        }
        return colors.get(strategy, QColor("#FFFFFF"))
    
    def _on_selection_changed(self):
        """Handle row selection change - emit row index for unique identification"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            # Don't emit signal - we'll handle click event instead
            # self.trial_selected.emit(row)  # Disabled - use inline view instead
            self.classify_btn.setEnabled(True)
        else:
            self.classify_btn.setEnabled(False)

    def _on_cell_clicked(self, row: int, column: int):
        """Handle cell click - show trial path inline"""
        if not self._experiment or row < 0:
            return

        # Toggle if clicking same row
        if self._expanded_row == row:
            self._close_path_view()
        else:
            self._show_trial_path(row)

    def _show_trial_path(self, row: int):
        """Display trial path in the expandable panel"""
        if not self._experiment or row >= len(self._experiment.trials):
            return

        trial = self._experiment.trials[row]
        self._expanded_row = row

        # Update title
        strategy_text = trial.search_strategy.value if trial.search_strategy else "Unclassified"
        self.path_title.setText(
            f"Row {row + 1}: Day {trial.day}, Trial {trial.trial_number} - {strategy_text}"
        )

        # Plot the path
        self._plot_trial_path(trial)

        # Show panel
        self.path_panel.setVisible(True)
        self.splitter.setSizes([600, 400])  # Give space to both

    def _plot_trial_path(self, trial: Trial):
        """Plot the trial's trajectory path"""
        self.path_figure.clear()
        ax = self.path_figure.add_subplot(111)

        # Get trajectory data
        x_coords = [p.x for p in trial.trajectory if p.x is not None and not np.isnan(p.x)]
        y_coords = [p.y for p in trial.trajectory if p.y is not None and not np.isnan(p.y)]

        if not x_coords or not y_coords:
            ax.text(0.5, 0.5, "No valid trajectory data",
                   ha='center', va='center', fontsize=14, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            self.path_canvas.draw()
            return

        # Pool geometry
        pool_center = trial.pool_center
        pool_radius = trial.pool_diameter / 2

        # Plot pool boundary
        circle = plt.Circle(pool_center, pool_radius, color='black',
                           fill=False, linewidth=2)
        ax.add_patch(circle)

        # Plot platform
        platform = plt.Circle(trial.platform_position, trial.platform_diameter / 2,
                             color='red', fill=True, alpha=0.5, label='Platform')
        ax.add_patch(platform)

        # Plot trajectory
        strategy_color = self._get_strategy_color_hex(trial.search_strategy) if trial.search_strategy else '#666666'
        ax.plot(x_coords, y_coords, color=strategy_color, linewidth=2, alpha=0.8, label='Path')

        # Mark start and end
        ax.plot(x_coords[0], y_coords[0], 'go', markersize=12, alpha=0.9,
               markeredgecolor='darkgreen', markeredgewidth=2, label='Start', zorder=5)
        ax.plot(x_coords[-1], y_coords[-1], 'rs', markersize=12, alpha=0.9,
               markeredgecolor='darkred', markeredgewidth=2, label='End', zorder=5)

        # Set equal aspect and limits
        ax.set_aspect('equal')
        margin = pool_radius * 0.1
        ax.set_xlim(pool_center[0] - pool_radius - margin, pool_center[0] + pool_radius + margin)
        ax.set_ylim(pool_center[1] - pool_radius - margin, pool_center[1] + pool_radius + margin)

        # Labels and legend
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title(f'Trajectory - Latency: {trial.escape_latency:.2f}s, Path: {trial.path_length:.1f}cm',
                    fontsize=10, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)

        ax.grid(True, alpha=0.3)
        self.path_figure.tight_layout()
        self.path_canvas.draw()

    def _get_strategy_color_hex(self, strategy: SearchStrategy) -> str:
        """Get hex color for strategy"""
        color_map = {
            SearchStrategy.DIRECT_SWIM: "#4CAF50",
            SearchStrategy.DIRECTED_SEARCH: "#8BC34A",
            SearchStrategy.FOCAL_SEARCH: "#FFEB3B",
            SearchStrategy.SPATIAL_INDIRECT: "#FFC107",
            SearchStrategy.CHAINING: "#FF9800",
            SearchStrategy.SCANNING: "#FF5722",
            SearchStrategy.THIGMOTAXIS: "#F44336",
            SearchStrategy.RANDOM_SEARCH: "#9E9E9E",
            SearchStrategy.NOT_RECOGNIZED: "#757575",
        }
        return color_map.get(strategy, "#666666")

    def _close_path_view(self):
        """Close the path visualization panel"""
        self.path_panel.setVisible(False)
        self.splitter.setSizes([1000, 0])
        self._expanded_row = None
        self.path_title.setText("Click a trial to view its path")
    
    def _on_cell_double_clicked(self, row: int, column: int):
        """Handle double-click on cell"""
        trial_id = self.table.item(row, 0).data(Qt.UserRole)
        self.manual_classification_requested.emit(trial_id)
    
    def _on_manual_classify(self):
        """Handle manual classification button click"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            trial_id = self.table.item(row, 0).data(Qt.UserRole)
            self.manual_classification_requested.emit(trial_id)
    
    def _show_context_menu(self, position):
        """Show context menu on right-click"""
        menu = QMenu()
        
        classify_action = QAction("Manual Classification", self)
        classify_action.triggered.connect(self._on_manual_classify)
        menu.addAction(classify_action)
        
        menu.addSeparator()
        
        export_action = QAction("Export Results", self)
        export_action.triggered.connect(self.export_requested.emit)
        menu.addAction(export_action)
        
        menu.exec_(self.table.mapToGlobal(position))
    
    def update_trial(self, trial_id: str, strategy: SearchStrategy, manual: bool = True):
        """Update a trial's strategy after manual classification"""
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).data(Qt.UserRole) == trial_id:
                # Update strategy
                strategy_item = self.table.item(row, 2)
                strategy_item.setText(strategy.value)
                strategy_item.setBackground(QBrush(self._get_strategy_color(strategy)))
                
                # Update manual flag
                manual_item = self.table.item(row, 7)
                manual_item.setText("✓" if manual else "")
                if manual:
                    manual_item.setForeground(QBrush(QColor("#FF9800")))
                
                break
    
    def get_selected_trial_id(self) -> Optional[str]:
        """Get currently selected trial ID"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            return self.table.item(row, 0).data(Qt.UserRole)
        return None
    
    def clear(self):
        """Clear all results"""
        self.table.setRowCount(0)
        self._experiment = None
        self.classify_btn.setEnabled(False)
        self._close_path_view()
