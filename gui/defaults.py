"""
Default parameter values for Pathfinder analysis.
These are the reference values from the original Pathfinder.py
"""

from pathfinder.core.models import Parameters


# Default parameters based on original Pathfinder.py implementation
DEFAULT_PARAMETERS = Parameters(
    name="Standard Morris Water Maze",
    
    # IPE (Initial Path Error) parameters
    ipe_max_val=125.0,
    heading_max_val=40.0,
    
    # Distance thresholds (first pass)
    distance_to_swim_max_val=30.0,
    distance_to_plat_max_val=30.0,
    
    # Distance thresholds (second pass)
    distance_to_swim_max_val2=50.0,
    distance_to_plat_max_val2=50.0,
    
    # Corridor (Direct Swim) parameters
    corridor_average_min_val=70.0,
    corridor_ipe_max_val=1500.0,
    directed_search_max_distance=400.0,
    
    # Focal search parameters
    focal_min_distance=100.0,
    focal_max_distance=400.0,
    
    # Semi-focal (Spatial Indirect) parameters
    semi_focal_min_distance=0.0,
    semi_focal_max_distance=500.0,
    
    # Annulus parameters
    annulus_counter_max_val=90.0,
    
    # Quadrant parameters
    quadrant_total_max_val=4.0,
    
    # Chaining parameters
    chaining_max_coverage=40.0,
    
    # Thigmotaxis parameters
    percent_traversed_max_val=20.0,
    
    # Scaling
    scale_values=True,
    pixels_per_cm=1.0,
)


# Additional parameters not in the base Parameters model
# These control analysis behavior and UI preferences
ANALYSIS_DEFAULTS = {
    # Strategy detection sensitivity
    "confidence_threshold": 0.70,  # Minimum confidence to auto-classify
    "require_manual_review": False,  # Flag uncertain trials for review
    
    # Performance thresholds
    "max_escape_latency": 120.0,  # seconds
    "min_swim_speed": 5.0,  # cm/s
    "max_swim_speed": 50.0,  # cm/s
    
    # Pool geometry (typical values)
    "default_pool_diameter": 120.0,  # cm
    "default_platform_diameter": 10.0,  # cm
    
    # Trajectory smoothing
    "enable_smoothing": True,
    "smoothing_window": 5,  # points
    
    # Heatmap generation
    "heatmap_resolution": 100,  # grid size
    "heatmap_gaussian_sigma": 2.0,
    
    # Export options
    "export_format": "csv",  # csv, excel, json
    "include_trajectory_data": False,
    "include_raw_metrics": True,
}


# UI defaults
UI_DEFAULTS = {
    "window_width": 1400,
    "window_height": 900,
    "control_panel_width": 350,
    "results_table_font_size": 10,
    "auto_save_interval": 300,  # seconds (5 minutes)
    "recent_files_max": 10,
}


def get_default_parameters():
    """Return a copy of default parameters"""
    return DEFAULT_PARAMETERS.copy(deep=True)


def reset_to_defaults():
    """Factory reset - return fresh defaults"""
    return {
        "parameters": get_default_parameters(),
        "analysis": ANALYSIS_DEFAULTS.copy(),
        "ui": UI_DEFAULTS.copy(),
    }
