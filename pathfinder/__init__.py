"""
Pathfinder: Morris Water Maze Search Strategy Analysis

Refactored modular package for calculating search strategy metrics.
"""

from pathfinder.analysis import (
    calculate_trial_metrics,
    unit_vector,
    angle_between,
)

from pathfinder.types import (
    TrialMetrics,
    AnalysisConfig,
)

__version__ = "2.0.0-refactored"

__all__ = [
    "calculate_trial_metrics",
    "unit_vector",
    "angle_between",
    "TrialMetrics",
    "AnalysisConfig",
]
