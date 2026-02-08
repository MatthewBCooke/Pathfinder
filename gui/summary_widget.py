"""
Summary statistics widget for displaying experiment-level analysis results.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QGridLayout, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Optional, Dict
from pathfinder.core.models import Experiment, SearchStrategy
from collections import Counter


class SummaryWidget(QWidget):
    """
    Display experiment-level summary statistics:
    - Strategy distribution
    - Average performance metrics
    - Learning curve indicators
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._experiment: Optional[Experiment] = None
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Experiment Summary")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Overview section
        overview_group = self._create_overview_section()
        layout.addWidget(overview_group)
        
        # Performance metrics section
        metrics_group = self._create_metrics_section()
        layout.addWidget(metrics_group)
        
        # Strategy distribution section
        strategy_group = self._create_strategy_section()
        layout.addWidget(strategy_group)
        
        layout.addStretch()
    
    def _create_overview_section(self):
        """Create experiment overview section"""
        group = QGroupBox("Overview")
        layout = QGridLayout()
        
        # Experiment name
        layout.addWidget(QLabel("Experiment:"), 0, 0, Qt.AlignRight)
        self.exp_name_label = QLabel("—")
        self.exp_name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.exp_name_label, 0, 1)
        
        # Total trials
        layout.addWidget(QLabel("Total Trials:"), 1, 0, Qt.AlignRight)
        self.total_trials_label = QLabel("0")
        layout.addWidget(self.total_trials_label, 1, 1)
        
        # Days
        layout.addWidget(QLabel("Training Days:"), 2, 0, Qt.AlignRight)
        self.days_label = QLabel("0")
        layout.addWidget(self.days_label, 2, 1)
        
        # Tracking software
        layout.addWidget(QLabel("Software:"), 3, 0, Qt.AlignRight)
        self.software_label = QLabel("—")
        layout.addWidget(self.software_label, 3, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_metrics_section(self):
        """Create performance metrics section"""
        group = QGroupBox("Performance Metrics")
        layout = QGridLayout()
        
        # Average escape latency
        layout.addWidget(QLabel("Avg Escape Latency:"), 0, 0, Qt.AlignRight)
        self.avg_latency_label = QLabel("—")
        self.avg_latency_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #2196F3;")
        layout.addWidget(self.avg_latency_label, 0, 1)
        
        # Average path length
        layout.addWidget(QLabel("Avg Path Length:"), 1, 0, Qt.AlignRight)
        self.avg_path_label = QLabel("—")
        layout.addWidget(self.avg_path_label, 1, 1)
        
        # Average swim speed
        layout.addWidget(QLabel("Avg Swim Speed:"), 2, 0, Qt.AlignRight)
        self.avg_speed_label = QLabel("—")
        layout.addWidget(self.avg_speed_label, 2, 1)
        
        # Learning indicator
        layout.addWidget(QLabel("Learning Trend:"), 3, 0, Qt.AlignRight)
        self.learning_label = QLabel("—")
        layout.addWidget(self.learning_label, 3, 1)
        
        group.setLayout(layout)
        return group
    
    def _create_strategy_section(self):
        """Create strategy distribution section"""
        group = QGroupBox("Strategy Distribution")
        layout = QVBoxLayout()
        
        # Strategy counts container
        self.strategy_container = QWidget()
        self.strategy_layout = QVBoxLayout(self.strategy_container)
        self.strategy_layout.setContentsMargins(0, 0, 0, 0)
        self.strategy_layout.setSpacing(5)
        
        layout.addWidget(self.strategy_container)
        
        group.setLayout(layout)
        return group
    
    def set_results(self, experiment: Experiment):
        """Update summary with experiment results"""
        self._experiment = experiment
        
        if not experiment:
            self._clear()
            return
        
        # Update overview
        self.exp_name_label.setText(experiment.experiment_name)
        self.total_trials_label.setText(str(len(experiment.trials)))
        
        days = set(t.day for t in experiment.trials)
        self.days_label.setText(str(len(days)))
        self.software_label.setText(experiment.tracking_software)
        
        # Update metrics
        self._update_metrics(experiment)
        
        # Update strategy distribution
        self._update_strategy_distribution(experiment)
    
    def _update_metrics(self, experiment: Experiment):
        """Calculate and display performance metrics"""
        trials = experiment.trials
        
        if not trials:
            return
        
        # Average escape latency
        latencies = [t.escape_latency for t in trials if t.escape_latency is not None]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            self.avg_latency_label.setText(f"{avg_latency:.2f} s")
        else:
            self.avg_latency_label.setText("—")
        
        # Average path length
        paths = [t.path_length for t in trials if t.path_length is not None]
        if paths:
            avg_path = sum(paths) / len(paths)
            self.avg_path_label.setText(f"{avg_path:.1f} cm")
        else:
            self.avg_path_label.setText("—")
        
        # Average swim speed
        speeds = [t.swim_speed for t in trials if t.swim_speed is not None]
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            self.avg_speed_label.setText(f"{avg_speed:.1f} cm/s")
        else:
            self.avg_speed_label.setText("—")
        
        # Learning trend (simple: compare first vs last day)
        days = sorted(set(t.day for t in trials))
        if len(days) >= 2 and latencies:
            first_day_latencies = [t.escape_latency for t in trials 
                                   if t.day == days[0] and t.escape_latency is not None]
            last_day_latencies = [t.escape_latency for t in trials 
                                  if t.day == days[-1] and t.escape_latency is not None]
            
            if first_day_latencies and last_day_latencies:
                first_avg = sum(first_day_latencies) / len(first_day_latencies)
                last_avg = sum(last_day_latencies) / len(last_day_latencies)
                improvement = ((first_avg - last_avg) / first_avg) * 100
                
                if improvement > 10:
                    self.learning_label.setText(f"✓ Improving ({improvement:.1f}%)")
                    self.learning_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                elif improvement < -10:
                    self.learning_label.setText(f"✗ Declining ({abs(improvement):.1f}%)")
                    self.learning_label.setStyleSheet("color: #F44336; font-weight: bold;")
                else:
                    self.learning_label.setText("→ Stable")
                    self.learning_label.setStyleSheet("color: #FF9800;")
            else:
                self.learning_label.setText("—")
        else:
            self.learning_label.setText("—")
    
    def _update_strategy_distribution(self, experiment: Experiment):
        """Display strategy distribution chart"""
        # Clear existing
        while self.strategy_layout.count():
            item = self.strategy_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Count strategies
        strategies = [t.search_strategy for t in experiment.trials if t.search_strategy]
        if not strategies:
            no_data = QLabel("No strategies detected yet")
            no_data.setAlignment(Qt.AlignCenter)
            no_data.setStyleSheet("color: gray; font-style: italic;")
            self.strategy_layout.addWidget(no_data)
            return
        
        strategy_counts = Counter(strategies)
        total = len(strategies)
        
        # Create bars for each strategy
        for strategy, count in strategy_counts.most_common():
            bar = self._create_strategy_bar(strategy, count, total)
            self.strategy_layout.addWidget(bar)
    
    def _create_strategy_bar(self, strategy: SearchStrategy, count: int, total: int) -> QWidget:
        """Create a horizontal bar for strategy distribution"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Strategy name
        name_label = QLabel(strategy.value)
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label)
        
        # Progress bar (visual representation)
        percentage = (count / total) * 100
        bar_widget = QFrame()
        bar_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self._get_strategy_color_hex(strategy)};
                border-radius: 3px;
            }}
        """)
        bar_widget.setFixedHeight(20)
        bar_widget.setMinimumWidth(int(percentage * 2))  # Scale for visualization
        layout.addWidget(bar_widget)
        
        # Count and percentage
        count_label = QLabel(f"{count} ({percentage:.1f}%)")
        count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(count_label)
        
        layout.addStretch()
        
        return widget
    
    def _get_strategy_color_hex(self, strategy: SearchStrategy) -> str:
        """Return hex color for strategy"""
        colors = {
            SearchStrategy.DIRECT_SWIM: "#4CAF50",
            SearchStrategy.DIRECTED_SEARCH: "#8BC34A",
            SearchStrategy.FOCAL_SEARCH: "#FFEB3B",
            SearchStrategy.SPATIAL_INDIRECT: "#FFC107",
            SearchStrategy.CHAINING: "#FF9800",
            SearchStrategy.SCANNING: "#FF5722",
            SearchStrategy.THIGMOTAXIS: "#F44336",
            SearchStrategy.RANDOM_SEARCH: "#9E9E9E",
        }
        return colors.get(strategy, "#CCCCCC")
    
    def _clear(self):
        """Clear all displayed data"""
        self.exp_name_label.setText("—")
        self.total_trials_label.setText("0")
        self.days_label.setText("0")
        self.software_label.setText("—")
        self.avg_latency_label.setText("—")
        self.avg_path_label.setText("—")
        self.avg_speed_label.setText("—")
        self.learning_label.setText("—")
        
        # Clear strategy distribution
        while self.strategy_layout.count():
            item = self.strategy_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
