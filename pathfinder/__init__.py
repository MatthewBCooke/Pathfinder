"""
Pathfinder Analysis Engine - Pure Python API

This package provides a clean separation between analysis logic and UI.
All functions are pure (no GUI dependencies) and fully typed.

Main exports:
- Analysis functions: calculate_trial_metrics, classify_strategy, aggregate_heatmap_data, calculate_auto_parameters
- Data models: Trial, Experiment, Datapoint, Parameters
- Type definitions: TrialMetrics, StrategyResult, HeatmapData, AutoParameters, AnalysisConfig
- I/O functions: load_experiment, find_files
"""

from pathfinder.models import Trial, Experiment, Datapoint, Parameters
from pathfinder.types import (
    TrialMetrics,
    StrategyResult,
    HeatmapData,
    AutoParameters,
    AnalysisConfig,
)
from pathfinder.analysis import (
    calculate_trial_metrics,
    classify_strategy,
    aggregate_heatmap_data,
    calculate_auto_parameters,
    unit_vector,
    angle_between,
)
from pathfinder.io import load_experiment, find_files
from pathfinder.entropy import entropy

__version__ = "2.0.0"  # Phase 1 complete

__all__ = [
    # Models
    "Trial",
    "Experiment",
    "Datapoint",
    "Parameters",
    # Type definitions
    "TrialMetrics",
    "StrategyResult",
    "HeatmapData",
    "AutoParameters",
    "AnalysisConfig",
    # Analysis functions
    "calculate_trial_metrics",
    "classify_strategy",
    "aggregate_heatmap_data",
    "calculate_auto_parameters",
    "unit_vector",
    "angle_between",
    # I/O functions
    "load_experiment",
    "find_files",
    # Entropy
    "entropy",
]
