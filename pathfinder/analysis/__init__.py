"""
Pathfinder analysis module.
Strategy detection and classification.
"""

from .trial_analyzer import TrialAnalyzer

# Import legacy analysis functions from parent module's analysis.py file
# This works around the package/module naming conflict
import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
try:
    # Import from the analysis.py FILE (not this analysis/ package)
    import importlib.util
    spec = importlib.util.spec_from_file_location("analysis_file", parent_dir / "analysis.py")
    analysis_file = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analysis_file)

    calculate_trial_metrics = analysis_file.calculate_trial_metrics
    classify_strategy = analysis_file.classify_strategy
finally:
    sys.path.pop(0)

__all__ = [
    "TrialAnalyzer",
    "calculate_trial_metrics",
    "classify_strategy",
]
