"""
Pathfinder core data models with type hints and validation.
Modernized from the original monolithic Pathfinder.py
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Tuple
from enum import Enum
from datetime import datetime


class SearchStrategy(str, Enum):
    """Available search strategies in Morris Water Maze analysis"""
    DIRECT_SWIM = "direct_swim"
    DIRECTED_SEARCH = "directed_search"
    FOCAL_SEARCH = "focal_search"
    SPATIAL_INDIRECT = "spatial_indirect"
    CHAINING = "chaining"
    SCANNING = "scanning"
    THIGMOTAXIS = "thigmotaxis"
    RANDOM_SEARCH = "random_search"
    NOT_RECOGNIZED = "not_recognized"


class Datapoint(BaseModel):
    """Single X-Y coordinate from tracking data"""
    x: float = Field(..., description="X coordinate in tracking software units")
    y: float = Field(..., description="Y coordinate in tracking software units")
    time: float = Field(..., description="Time in seconds")
    
    @validator('x', 'y', 'time')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError('Coordinates and time must be non-negative')
        return v


class Parameters(BaseModel):
    """Configuration parameters for search strategy analysis"""
    name: str = Field("Default", description="Parameter preset name")
    
    # IPE parameters
    ipe_max_val: float = Field(125, description="IPE maximum value")
    heading_max_val: float = Field(40, description="Heading maximum value")
    
    # Distance parameters
    distance_to_swim_max_val: float = Field(30, description="Distance to swim max (1st)")
    distance_to_plat_max_val: float = Field(30, description="Distance to platform max (1st)")
    distance_to_swim_max_val2: float = Field(50, description="Distance to swim max (2nd)")
    distance_to_plat_max_val2: float = Field(50, description="Distance to platform max (2nd)")
    
    # Corridor parameters
    corridor_average_min_val: float = Field(70, description="Corridor average minimum")
    corridor_ipe_max_val: float = Field(1500, description="Corridor IPE maximum")
    directed_search_max_distance_multiplier: float = Field(0.8, description="Directed search max distance (× pool diameter)")

    # Focal search parameters
    focal_min_distance_multiplier: float = Field(0.2, description="Focal search minimum distance (× pool diameter)")
    focal_max_distance_multiplier: float = Field(0.8, description="Focal search maximum distance (× pool diameter)")

    # Semi-focal parameters
    semi_focal_min_distance_multiplier: float = Field(0.0, description="Semi-focal minimum distance (× pool diameter)")
    semi_focal_max_distance_multiplier: float = Field(1.0, description="Semi-focal maximum distance (× pool diameter)")

    # Indirect Search parameters
    ipe_indirect_max_val: float = Field(300, description="Maximum IPE for Indirect Search")
    heading_indirect_max_val: float = Field(70, description="Maximum heading error for Indirect Search")

    # Chaining parameters
    annulus_counter_max_val: float = Field(90, description="Annulus counter maximum")
    quadrant_total_max_val: float = Field(4, description="Quadrant total maximum")
    chaining_max_coverage: float = Field(40, description="Chaining max coverage")

    # Scanning parameters
    percent_traversed_min_val: float = Field(5, description="Minimum percent traversed for Scanning")
    percent_traversed_max_val: float = Field(20, description="Maximum percent traversed for Scanning")
    distance_to_centre_max_val: float = Field(60, description="Maximum distance to centre (% of radius) for Scanning")

    # Thigmotaxis parameters
    full_thigmo_min_val: float = Field(65, description="Minimum full thigmotaxis percentage")
    small_thigmo_min_val: float = Field(35, description="Minimum small thigmotaxis percentage")
    thigmo_min_distance_multiplier: float = Field(0.8, description="Minimum total distance for Thigmotaxis (× pool diameter)")

    # Random Search parameters
    percent_traversed_random_max_val: float = Field(10, description="Minimum percent traversed for Random Search")

    # Strategy enable/disable flags
    use_direct: bool = Field(True, description="Enable Direct Path classification")
    use_focal: bool = Field(True, description="Enable Focal Search classification")
    use_directed: bool = Field(True, description="Enable Directed Search classification")
    use_indirect: bool = Field(True, description="Enable Indirect Search classification")
    use_semi_focal: bool = Field(False, description="Enable Semi-Focal Search classification")
    use_chaining: bool = Field(True, description="Enable Chaining classification")
    use_scanning: bool = Field(True, description="Enable Scanning classification")
    use_thigmotaxis: bool = Field(True, description="Enable Thigmotaxis classification")
    use_random: bool = Field(True, description="Enable Random Search classification")

    # Advanced parameters
    scale_values: bool = Field(True, description="Auto-scale values based on pool size")
    pixels_per_cm: float = Field(1.0, description="Conversion factor: pixels per cm")

    # Visualization zone parameters
    chaining_radius_percent: float = Field(6, description="Chaining zone radius as % of pool diameter")
    thigmotaxis_zone_percent: float = Field(20, description="Thigmotaxis zone width as % of pool radius")
    focal_search_radius_multiplier: float = Field(1.5, description="Focal search radius as multiple of platform diameter")
    directed_search_radius_multiplier: float = Field(3.5, description="Directed search radius as multiple of platform diameter")
    corridor_width_degrees: float = Field(15, description="Direct swim corridor width in degrees (each side)")

    class Config:
        use_enum_values = True


class Trial(BaseModel):
    """Single Morris Water Maze trial with trajectory and analysis results"""
    trial_id: str = Field(..., description="Unique trial identifier")
    trial_number: int = Field(..., description="Sequential trial number")
    day: int = Field(..., description="Experimental day")
    
    # Trajectory data
    trajectory: List[Datapoint] = Field(..., description="X-Y-T coordinates for trial")
    
    # Spatial parameters
    platform_position: Tuple[float, float] = Field(
        ..., 
        description="Platform location (x, y)"
    )
    platform_diameter: float = Field(..., description="Platform diameter in tracking software units")
    pool_center: Tuple[float, float] = Field(..., description="Pool center (x, y)")
    pool_diameter: float = Field(..., description="Pool diameter in tracking software units")
    
    # Analysis results
    search_strategy: Optional[SearchStrategy] = Field(
        None, 
        description="Detected search strategy"
    )
    escape_latency: Optional[float] = Field(None, description="Time to reach platform (seconds)")
    path_length: Optional[float] = Field(None, description="Total distance traveled")
    swim_speed: Optional[float] = Field(None, description="Average swim speed")
    
    # Quality flags
    manual_categorization: bool = Field(False, description="Was strategy manually assigned?")
    notes: Optional[str] = Field(None, description="Analyst notes")
    
    @validator('escape_latency', 'path_length', 'swim_speed', pre=True, always=True)
    def validate_metrics(cls, v):
        if v is not None and v < 0:
            raise ValueError('Metrics must be non-negative')
        return v


class Experiment(BaseModel):
    """Complete Morris Water Maze experiment with all trials and metadata"""
    experiment_id: str = Field(..., description="Unique experiment identifier")
    experiment_name: str = Field(..., description="Descriptive name")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    researcher: Optional[str] = Field(None, description="Researcher name")
    notes: Optional[str] = Field(None, description="Experiment notes")
    
    # Parameters used
    parameters: Parameters = Field(..., description="Analysis parameters")
    
    # Data
    trials: List[Trial] = Field(default_factory=list, description="All trials in experiment")
    
    # Tracking software
    tracking_software: str = Field(..., description="Software used (Ethovision, Anymaze, etc.)")
    
    class Config:
        use_enum_values = True
    
    def get_trials_by_day(self, day: int) -> List[Trial]:
        """Get all trials from a specific day"""
        return [t for t in self.trials if t.day == day]
    
    def get_trials_by_strategy(self, strategy: SearchStrategy) -> List[Trial]:
        """Get all trials with a specific search strategy"""
        return [t for t in self.trials if t.search_strategy == strategy]
    
    def average_escape_latency(self, day: Optional[int] = None) -> Optional[float]:
        """Calculate average escape latency"""
        trials = self.get_trials_by_day(day) if day else self.trials
        latencies = [t.escape_latency for t in trials if t.escape_latency is not None]
        return sum(latencies) / len(latencies) if latencies else None


class AnalysisResult(BaseModel):
    """Results of search strategy analysis"""
    experiment_id: str
    trial_id: str
    detected_strategy: SearchStrategy
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
