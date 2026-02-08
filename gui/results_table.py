"""
Results table widget for displaying trial analysis results.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QHBoxLayout,
    QMenu, QAction
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QBrush
from typing import List, Optional
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
    trial_selected = pyqtSignal(str)  # trial_id
    manual_classification_requested = pyqtSignal(str)  # trial_id
    export_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._experiment: Optional[Experiment] = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Table widget
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Day",
            "Trial #",
            "Strategy",
            "Confidence",
            "Latency (s)",
            "Path (cm)",
            "Speed (cm/s)",
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
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        
        self.table.setColumnWidth(0, 50)   # Day
        self.table.setColumnWidth(1, 60)   # Trial #
        self.table.setColumnWidth(3, 80)   # Confidence
        self.table.setColumnWidth(4, 90)   # Latency
        self.table.setColumnWidth(5, 90)   # Path
        self.table.setColumnWidth(6, 90)   # Speed
        self.table.setColumnWidth(7, 60)   # Manual
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        
        layout.addWidget(self.table)
        
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
        
        layout.addLayout(button_layout)
    
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
        """Add a single trial to the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
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
        
        # Confidence (placeholder - would come from AnalysisResult)
        confidence_item = QTableWidgetItem("—")
        confidence_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, confidence_item)
        
        # Escape latency
        latency_item = QTableWidgetItem()
        if trial.escape_latency is not None:
            latency_item.setData(Qt.DisplayRole, f"{trial.escape_latency:.2f}")
        else:
            latency_item.setData(Qt.DisplayRole, "—")
        latency_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 4, latency_item)
        
        # Path length
        path_item = QTableWidgetItem()
        if trial.path_length is not None:
            path_item.setData(Qt.DisplayRole, f"{trial.path_length:.1f}")
        else:
            path_item.setData(Qt.DisplayRole, "—")
        path_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 5, path_item)
        
        # Swim speed
        speed_item = QTableWidgetItem()
        if trial.swim_speed is not None:
            speed_item.setData(Qt.DisplayRole, f"{trial.swim_speed:.1f}")
        else:
            speed_item.setData(Qt.DisplayRole, "—")
        speed_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.setItem(row, 6, speed_item)
        
        # Manual classification flag
        manual_item = QTableWidgetItem("✓" if trial.manual_categorization else "")
        manual_item.setTextAlignment(Qt.AlignCenter)
        if trial.manual_categorization:
            manual_item.setForeground(QBrush(QColor("#FF9800")))
        self.table.setItem(row, 7, manual_item)
        
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
        }
        return colors.get(strategy, QColor("#FFFFFF"))
    
    def _on_selection_changed(self):
        """Handle row selection change"""
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            trial_id = self.table.item(row, 0).data(Qt.UserRole)
            self.trial_selected.emit(trial_id)
            self.classify_btn.setEnabled(True)
        else:
            self.classify_btn.setEnabled(False)
    
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
