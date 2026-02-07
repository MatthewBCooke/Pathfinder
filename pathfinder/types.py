"""
Type definitions for Pathfinder analysis.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


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


@dataclass
class Parameters:
    """
    Strategy classification threshold parameters.
    
    Defines thresholds for classifying search strategies and which strategies to use.
    Corresponds to the Parameters class from SearchStrategyAnalysis/appTrial.py.
    """
    name: str = "Default"
    
    # Direct Path thresholds
    ipeMaxVal: float = 125
    """Maximum IPE for Direct Path classification"""
    
    headingMaxVal: float = 40
    """Maximum heading error for Direct Path classification"""
    
    # Focal Search thresholds
    distanceToSwimMaxVal: float = 30
    """Distance to swim path centroid threshold (% of maze radius)"""
    
    distanceToPlatMaxVal: float = 30
    """Distance to platform threshold (% of maze radius)"""
    
    focalMinDistance: float = 100
    """Minimum total distance for Focal Search"""
    
    focalMaxDistance: float = 400
    """Maximum total distance for Focal Search"""
    
    # Semi-Focal Search thresholds
    distanceToSwimMaxVal2: float = 50
    """Distance to swim path centroid for Semi-Focal (% of maze radius)"""
    
    distanceToPlatMaxVal2: float = 50
    """Distance to platform for Semi-Focal (% of maze radius)"""
    
    semiFocalMinDistance: float = 0
    """Minimum total distance for Semi-Focal Search"""
    
    semiFocalMaxDistance: float = 500
    """Maximum total distance for Semi-Focal Search"""
    
    # Directed Search thresholds
    corridorAverageMinVal: float = 70
    """Minimum corridor percentage for Directed Search"""
    
    corridoripeMaxVal: float = 1500
    """Maximum IPE for Directed Search"""
    
    directedSearchMaxDistance: float = 400
    """Maximum total distance for Directed Search"""
    
    # Indirect Search thresholds
    ipeIndirectMaxVal: float = 300
    """Maximum IPE for Indirect Search"""
    
    headingIndirectMaxVal: float = 70
    """Maximum heading error for Indirect Search"""
    
    # Chaining thresholds
    annulusCounterMaxVal: float = 90
    """Minimum annulus time percentage for Chaining"""
    
    quadrantTotalMaxVal: int = 4
    """Minimum quadrants visited for Chaining"""
    
    chainingMaxCoverage: float = 40
    """Maximum percent traversed for Chaining"""
    
    # Scanning thresholds
    percentTraversedMinVal: float = 5
    """Minimum percent traversed for Scanning"""
    
    percentTraversedMaxVal: float = 20
    """Maximum percent traversed for Scanning"""
    
    distanceToCentreMaxVal: float = 60
    """Maximum distance to centre (% of maze radius) for Scanning"""
    
    # Thigmotaxis thresholds
    fullThigmoMinVal: float = 65
    """Minimum full thigmotaxis percentage"""
    
    smallThigmoMinVal: float = 35
    """Minimum small thigmotaxis percentage"""
    
    thigmoMinDistance: float = 400
    """Minimum total distance for Thigmotaxis"""
    
    # Random Search thresholds
    percentTraversedRandomMaxVal: float = 10
    """Minimum percent traversed for Random Search"""
    
    # Strategy enable flags
    useDirect: bool = True
    """Enable Direct Path classification"""
    
    useFocal: bool = True
    """Enable Focal Search classification"""
    
    useDirected: bool = True
    """Enable Directed Search classification"""
    
    useIndirect: bool = True
    """Enable Indirect Search classification"""
    
    useSemiFocal: bool = False
    """Enable Semi-Focal Search classification"""
    
    useChaining: bool = True
    """Enable Chaining classification"""
    
    useScanning: bool = True
    """Enable Scanning classification"""
    
    useRandom: bool = True
    """Enable Random Search classification"""
    
    useThigmotaxis: bool = True
    """Enable Thigmotaxis classification"""


@dataclass
class AutoParameters:
    """
    Automatically calculated experimental parameters from trial data.
    
    Extracted from getAutoLocations() method to separate analysis from GUI.
    """
    maze_centre_x: float
    """Estimated X coordinate of maze center"""
    
    maze_centre_y: float
    """Estimated Y coordinate of maze center"""
    
    goal_x: float
    """Estimated X coordinate of platform/goal"""
    
    goal_y: float
    """Estimated Y coordinate of platform/goal"""
    
    maze_diameter: float
    """Estimated maze diameter"""
    
    maze_radius: float
    """Estimated maze radius (diameter / 2)"""
    
    goal_diameter: float
    """Estimated platform/goal diameter"""
    
    trial_count: int
    """Number of trials used in estimation"""
    
    warnings: List[str]
    """List of warnings generated during calculation"""


@dataclass
class HeatmapData:
    """
    Aggregated heatmap data ready for visualization.
    
    Contains position data aggregated and smoothed from trials, 
    without any plotting/GUI dependencies.
    """
    x_smoothed: np.ndarray
    """Gaussian-smoothed X coordinates"""
    
    y_smoothed: np.ndarray
    """Gaussian-smoothed Y coordinates"""
    
    x_raw: List[float]
    """Raw X coordinates before smoothing"""
    
    y_raw: List[float]
    """Raw Y coordinates before smoothing"""
    
    extent: Tuple[float, float, float, float]
    """Spatial extent (xMin, xMax, yMin, yMax) of the data"""
    
    gridsize: int
    """Grid size for hexbin/heatmap visualization"""
    
    histogram: Optional[np.ndarray] = None
    """2D histogram array (optional, can be computed from x/y)"""
    
    xedges: Optional[np.ndarray] = None
    """Histogram bin edges for X axis"""
    
    yedges: Optional[np.ndarray] = None
    """Histogram bin edges for Y axis"""
