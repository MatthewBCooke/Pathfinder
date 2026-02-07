"""
Type definitions for Pathfinder analysis.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TrialMetrics:
    """
    Complete metrics for a single trial analysis.
    
    All 19 search strategy metrics calculated from trajectory data.
    """
    # Directional metrics
    corridor_average: float
    """Percentage of time swimming in corridor toward platform"""
    
    average_heading_error: float
    """Mean heading error in degrees relative to platform"""
    
    average_initial_heading_error: float
    """Mean heading error during first second of trial"""
    
    # Distance metrics
    distance_average: float
    """Average distance from platform throughout trial"""
    
    average_distance_to_swim_path_centroid: float
    """Average distance from centroid of swim path"""
    
    average_distance_to_centre: float
    """Average distance from pool center"""
    
    # Spatial coverage
    percent_traversed: float
    """Percentage of pool grid cells visited"""
    
    quadrant_total: int
    """Number of quadrants entered (1-4)"""
    
    # Kinematic metrics
    total_distance: float
    """Total path length in cm/pixels"""
    
    latency: float
    """Escape latency (time to reach platform) in seconds"""
    
    velocity: float
    """Average swim speed"""
    
    # Zone metrics
    full_thigmo_counter: float
    """Time/samples in full thigmotaxis zone"""
    
    small_thigmo_counter: float
    """Time/samples in small thigmotaxis zone"""
    
    annulus_counter: float
    """Time/samples in annulus zone around platform"""
    
    # Advanced metrics
    sample_count: float
    """Number of trajectory samples (i)"""
    
    ipe: float
    """Ideal Path Error (IPE) - path efficiency metric"""
    
    entropy: Optional[float]
    """Shannon entropy of spatial distribution (None if disabled)"""
    
    # Raw trajectory data
    trajectory_x: List[float]
    """X coordinates of trajectory"""
    
    trajectory_y: List[float]
    """Y coordinates of trajectory"""


@dataclass
class AnalysisConfig:
    """
    Configuration parameters for trial analysis.
    
    Corresponds to instance variables and configuration flags from original Pathfinder.
    """
    # Grid parameters
    grid_cell_size: float = 10.0
    """Size of grid cells for coverage calculation"""
    
    # Safety limits
    max_iterations: int = 100000
    """Maximum iterations for ideal path calculation"""
    
    max_cumulative_distance: float = 1000000.0
    """Maximum cumulative distance before breaking"""
    
    # Behavior flags
    use_entropy: bool = True
    """Whether to calculate entropy metric"""
    
    truncate_at_platform: bool = False
    """Whether to truncate trajectory when platform is reached"""
