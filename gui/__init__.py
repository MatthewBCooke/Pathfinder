"""
Pathfinder GUI package.
Modern PyQt5-based interface for Morris Water Maze analysis.
"""

from .main_window import PathfinderMainWindow
from .integration import PathfinderIntegration
from .control_panel import ControlPanelWidget
from .results_table import ResultsTableWidget
from .summary_widget import SummaryWidget
from .heatmap_widget import HeatmapWidget
from .defaults import DEFAULT_PARAMETERS, get_default_parameters

__all__ = [
    "PathfinderMainWindow",
    "PathfinderIntegration",
    "ControlPanelWidget",
    "ResultsTableWidget",
    "SummaryWidget",
    "HeatmapWidget",
    "DEFAULT_PARAMETERS",
    "get_default_parameters",
]

__version__ = "2.0.0"
