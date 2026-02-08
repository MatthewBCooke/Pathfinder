"""
Core analysis functions for Morris Water Maze search strategy calculation.

Refactored from SearchStrategyAnalysis/Pathfinder.py to be pure, testable, and modular.
"""

import math
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import scipy.ndimage as sp

from pathfinder.types import TrialMetrics, AnalysisConfig, Parameters, HeatmapData, AutoParameters

# Import entropy - handle if module is unavailable
try:
    from pathfinder.entropy import entropy as calculate_entropy  # type: ignore
    CAN_USE_ENTROPY = True
except ImportError:
    try:
        # Fallback: try importing from original location
        import sys
        sys.path.append('/tmp/Pathfinder/SearchStrategyAnalysis')
        from entropy import entropy as calculate_entropy # type: ignore
        CAN_USE_ENTROPY = True
    except ImportError:
        CAN_USE_ENTROPY = False
        logging.warning("Entropy module unavailable - entropy calculations will be disabled")
        def calculate_entropy(*args, **kwargs):
            raise ImportError("Entropy module unavailable")


def unit_vector(vector: np.ndarray) -> np.ndarray:
    """
    Returns the unit vector of the input vector.
    
    Args:
        vector: Input vector as numpy array
        
    Returns:
        Normalized unit vector, or (0, 0) if norm is zero
    """
    if np.linalg.norm(vector) == 0:
        return np.array([0.0, 0.0])
    try:
        return vector / np.linalg.norm(vector)
    except Exception:
        return np.array([0.0, 0.0])


def angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate the angle in degrees between two vectors.
    
    Args:
        v1: First vector
        v2: Second vector
        
    Returns:
        Angle in degrees between the two vectors
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return float(np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))))


def calculate_trial_metrics(
    trial,  # Trial object with iterable datapoints
    goal_x: float,
    goal_y: float,
    maze_centre_x: float,
    maze_centre_y: float,
    corridor_width: float,
    thigmotaxis_zone_size: float,
    chaining_radius: float,
    full_thigmo_zone: float,
    small_thigmo_zone: float,
    maze_radius: float,
    day_num: int,
    goal_diam: float,
    config: Optional[AnalysisConfig] = None
) -> TrialMetrics:
    """
    Calculate all 19 search strategy metrics for a trial.
    
    This is the core analysis function that computes spatial, kinematic, and strategic
    metrics from a Morris Water Maze trial trajectory.
    
    Args:
        trial: Trial object containing datapoints (must be iterable)
        goal_x, goal_y: Goal/platform position coordinates (must be numeric)
        maze_centre_x, maze_centre_y: Maze centre coordinates (must be numeric)
        corridor_width: Width of corridor toward goal (degrees)
        thigmotaxis_zone_size: Size of thigmotaxis zone
        chaining_radius: Radius for chaining zone around platform
        full_thigmo_zone: Full thigmotaxis zone size
        small_thigmo_zone: Small thigmotaxis zone size
        maze_radius: Radius of the maze/pool
        day_num: Experimental day number
        goal_diam: Diameter of the goal platform
        config: Optional analysis configuration (uses defaults if None)
        
    Returns:
        TrialMetrics object containing all 19 calculated metrics
        
    Raises:
        ValueError: If critical numeric parameters are invalid or None
    """
    # Use default config if not provided
    if config is None:
        config = AnalysisConfig()
    
    # CRITICAL: Input validation
    if trial is None:
        raise ValueError("trial cannot be None")
    
    # Try to get datapoints - handle both legacy and modern Trial objects
    try:
        if hasattr(trial, 'datapointList'):
            datapoints = trial.datapointList
        elif hasattr(trial, 'trajectory'):
            datapoints = trial.trajectory
        else:
            # Assume trial itself is iterable
            datapoints = list(trial)
    except Exception as e:
        raise ValueError(f"Cannot access trial datapoints: {e}")
    
    if len(datapoints) == 0:
        raise ValueError("trial cannot be empty")
    
    # Validate that datapoints have necessary methods/attributes
    first_point = datapoints[0]
    has_getx = hasattr(first_point, 'getx')
    has_x_attr = hasattr(first_point, 'x')
    
    if not (has_getx or has_x_attr):
        raise ValueError("Datapoint missing required coordinate access methods/attributes")
    
    # Helper functions to access datapoint coordinates (handle both legacy and modern formats)
    def get_x(dp):
        if hasattr(dp, 'getx'):
            return dp.getx()
        return dp.x
    
    def get_y(dp):
        if hasattr(dp, 'gety'):
            return dp.gety()
        return dp.y
    
    def get_time(dp):
        if hasattr(dp, 'gettime'):
            return dp.gettime()
        return dp.time
    
    # Validate numeric parameters
    for param_name, param_value in [
        ('goal_x', goal_x), ('goal_y', goal_y),
        ('maze_centre_x', maze_centre_x), ('maze_centre_y', maze_centre_y)
    ]:
        if param_value is None:
            raise ValueError(f"Parameter '{param_name}' cannot be None")
        try:
            float(param_value)
        except (TypeError, ValueError):
            raise ValueError(f"Parameter '{param_name}' must be numeric, got: {param_value}")
    
    # Initialize variables
    i = 0.0
    total_distance = 0.0
    latency = 1.0
    main_latency = 0.0
    x_summed = 0.0
    y_summed = 0.0
    x_av = 0.0
    y_av = 0.0
    current_distance_from_goal = 0.0
    distance_from_goal_summed = 0.0
    distance_average = 0.0
    a_x = 0.0
    a_y = 0.0
    
    missing_data = 0
    
    distance_to_center_of_maze = 0.0
    total_distance_to_center_of_maze = 0.0
    average_distance_to_centre = 0.0
    
    small_thigmo_counter = 0.0
    full_thigmo_counter = 0.0
    annulus_counter = 0.0
    current_heading_error = 0.0
    distance_to_swim_path_centroid = 0.0
    total_distance_to_swim_path_centroid = 0.0
    average_distance_to_swim_path_centroid = 0.0
    
    distance_to_old_goal = 0.0
    total_distance_to_old_goal = 0.0
    average_distance_to_old_goal = 0.0
    
    start_x = 0.0
    start_y = 0.0
    start_time = 0.0
    
    old_item_x = 0.0
    old_item_y = 0.0
    corridor_counter = 0.0
    quadrant_one = 0
    quadrant_two = 0
    quadrant_three = 0
    quadrant_four = 0
    quadrant_total = 0
    x = 0
    old_x = 0.0
    old_y = 0.0
    latency_counter = 0.0
    distance_from_start_to_goal = 0.0
    array_x: List[float] = []
    array_y: List[float] = []
    
    # First pass: calculate basic metrics
    for a_datapoint in datapoints:
        if i == 0:
            start_x = get_x(a_datapoint)
            start_y = get_y(a_datapoint)
            start_time = get_time(a_datapoint)
        
        # Swim Path centroid
        i += 1.0
        x_summed += float(get_x(a_datapoint))
        y_summed += float(get_y(a_datapoint))
        a_x = float(get_x(a_datapoint))
        a_y = float(get_y(a_datapoint))
        
        array_x.append(a_x)
        array_y.append(a_y)
        
        # Average Distance
        current_distance_from_goal = math.sqrt((goal_x - a_x) ** 2 + (goal_y - a_y) ** 2)
        
        # in zones
        distance_center_to_goal = math.sqrt((maze_centre_x - goal_x) ** 2 + (maze_centre_y - goal_y) ** 2)
        annulus_zone_inner = distance_center_to_goal - (chaining_radius / 2)
        annulus_zone_outer = distance_center_to_goal + (chaining_radius / 2)
        distance_to_center_of_maze = math.sqrt((maze_centre_x - a_x) ** 2 + (maze_centre_y - a_y) ** 2)
        total_distance_to_center_of_maze += distance_to_center_of_maze
        distance_from_start_to_goal = math.sqrt((goal_x - start_x) ** 2 + (goal_y - start_y) ** 2)
        
        distance = math.sqrt(abs(old_x - a_x) ** 2 + abs(old_y - a_y) ** 2)
        distance_from_goal_summed += current_distance_from_goal
        total_distance += distance
        old_x = a_x
        old_y = a_y
        
        if distance_to_center_of_maze > small_thigmo_zone:  # calculate if we are in zones
            small_thigmo_counter += 1.0
        if distance_to_center_of_maze > full_thigmo_zone:
            full_thigmo_counter += 1.0
        if (distance_to_center_of_maze >= annulus_zone_inner) and (distance_to_center_of_maze <= annulus_zone_outer):
            annulus_counter += 1.0
        
        # Quadrant tracking
        if get_x(a_datapoint) >= maze_centre_x and get_y(a_datapoint) >= maze_centre_y:
            quadrant_one = 1
        elif get_x(a_datapoint) < maze_centre_x and get_y(a_datapoint) >= maze_centre_y:
            quadrant_two = 1
        elif get_x(a_datapoint) >= maze_centre_x and get_y(a_datapoint) < maze_centre_y:
            quadrant_three = 1
        elif get_x(a_datapoint) < maze_centre_x and get_y(a_datapoint) < maze_centre_y:
            quadrant_four = 1
        
        latency = get_time(a_datapoint) - start_time
        
        # Check if we should truncate at platform
        if config.truncate_at_platform and current_distance_from_goal < float(goal_diam) / 2.0:
            break
    
    quadrant_total = quadrant_one + quadrant_two + quadrant_three + quadrant_four
    
    # Calculate percent traversed using grid normalization
    if len(array_x) == 0 or len(array_y) == 0:
        logging.warning("array_x or array_y is empty, skipping grid normalization")
        percent_traversed = 0.0
        norm_x: List[float] = []
        norm_y: List[float] = []
    else:
        spread_x = abs((maze_centre_x + maze_radius) - (maze_centre_x - maze_radius))
        spread_y = abs((maze_centre_y + maze_radius) - (maze_centre_y - maze_radius))
        norm_x = []
        norm_y = []
        for xx in array_x:
            norm_x.append(
                round((((xx - abs((maze_centre_x - maze_radius))) / spread_x) * config.grid_cell_size), 0) * config.grid_cell_size
            )
        for yy in array_y:
            norm_y.append(
                round((((yy - abs((maze_centre_y - maze_radius))) / spread_y) * config.grid_cell_size), 0) * config.grid_cell_size
            )
    
    # Calculate unique grid cells visited
    xy_pairs = list(zip(norm_x, norm_y))
    xy_unique = list(dict.fromkeys(xy_pairs))
    percent_traversed = float(len(xy_unique))
    
    if percent_traversed > 100:
        percent_traversed = 100.0
    
    # Calculate swim path centroid
    if i == 0:
        i = 1
    try:
        x_av = x_summed / i
        y_av = y_summed / i
        swim_path_centroid = (x_av, y_av)
    except ZeroDivisionError:
        swim_path_centroid = (0.0, 0.0)
    
    # Calculate corridor parameters
    start_point = np.array([start_x, start_y])
    goal_point = np.array([goal_x, goal_y])
    
    start_to_plat_vector = goal_point - start_point
    
    if (goal_x - start_x) != 0:
        a_arc_tangent = math.degrees(math.atan((goal_y - start_y) / (goal_x - start_x)))
    else:
        a_arc_tangent = 0.0
    
    upper_corridor = a_arc_tangent + corridor_width
    lower_corridor = a_arc_tangent - corridor_width
    corridor_width_calc = 0.0
    total_heading_error = 0.0
    initial_heading_error = 0.0
    initial_heading_error_count = 0
    
    # Second pass: calculate heading errors and corridor metrics
    for a_datapoint in datapoints:
        current_distance_from_goal = math.sqrt(
            (goal_x - get_x(a_datapoint)) ** 2 + (goal_y - get_y(a_datapoint)) ** 2
        )
        distance_to_swim_path_centroid = math.sqrt(
            (x_av - get_x(a_datapoint)) ** 2 + (y_av - get_y(a_datapoint)) ** 2
        )
        total_distance_to_swim_path_centroid += distance_to_swim_path_centroid
        distance_from_start_to_current = math.sqrt(
            (get_x(a_datapoint) - start_x) ** 2 + (get_y(a_datapoint) - start_y) ** 2
        )
        
        if (old_item_x != 0 and 
            get_x(a_datapoint) - old_item_x != 0 and 
            get_x(a_datapoint) - start_x != 0):
            
            current_to_plat = np.subtract(
                np.array([goal_x, goal_y]), 
                np.array([get_x(a_datapoint), get_y(a_datapoint)])
            )
            old_to_current = np.subtract(
                np.array([get_x(a_datapoint), get_y(a_datapoint)]),
                np.array([old_item_x, old_item_y])
            )
            current_heading_error = abs(angle_between(current_to_plat, old_to_current))
            within_corridor = math.degrees(
                math.atan((get_y(a_datapoint) - start_y) / (get_x(a_datapoint) - start_x))
            )
            corridor_width_calc = abs(
                a_arc_tangent - abs(
                    math.degrees(
                        math.atan((get_y(a_datapoint) - old_item_y) / (get_x(a_datapoint) - old_item_x))
                    )
                )
            )
            if float(lower_corridor) <= float(within_corridor) <= float(upper_corridor):
                corridor_counter += 1.0
        
        if get_time(a_datapoint) < 1.0:
            initial_heading_error += current_heading_error
            initial_heading_error_count += 1
        
        old_item_x = get_x(a_datapoint)
        old_item_y = get_y(a_datapoint)
        total_heading_error += current_heading_error
        
        if config.truncate_at_platform and current_distance_from_goal < float(goal_diam) / 2.0:
            break
    
    # Calculate averages
    try:
        corridor_average = corridor_counter / i
        distance_average = distance_from_goal_summed / i
        average_distance_to_swim_path_centroid = total_distance_to_swim_path_centroid / i
        average_distance_to_old_goal = total_distance_to_old_goal / i
        average_distance_to_centre = total_distance_to_center_of_maze / i
        average_heading_error = total_heading_error / i
    except ZeroDivisionError:
        logging.warning("Division by zero in average calculations, setting i=1")
        i = 1.0
        corridor_average = corridor_counter / i
        distance_average = distance_from_goal_summed / i
        average_distance_to_swim_path_centroid = total_distance_to_swim_path_centroid / i
        average_distance_to_old_goal = total_distance_to_old_goal / i
        average_distance_to_centre = total_distance_to_center_of_maze / i
        average_heading_error = total_heading_error / i
    
    try:
        average_initial_heading_error = initial_heading_error / initial_heading_error_count
    except ZeroDivisionError:
        logging.warning("Division by zero when calculating average_initial_heading_error, setting to 0")
        average_initial_heading_error = 0.0
    
    # Calculate velocity and IPE (Ideal Path Error)
    velocity = 0.0
    ideal_distance = distance_from_start_to_goal
    if latency != 0:
        try:
            velocity = (total_distance / latency)
        except ZeroDivisionError:
            logging.warning("Division by zero when calculating velocity, setting to 0")
            velocity = 0.0
    
    ideal_cumulative_distance = 0.0
    try:
        sample_rate = (get_time(datapoints[-1]) - start_time) / (len(datapoints) - 1)
    except (ZeroDivisionError, IndexError) as e:
        logging.warning(f"Error with sample rate calculation: {type(e).__name__}, setting sample_rate=1")
        sample_rate = 1.0
    
    # Calculate ideal path with safety limits
    iteration_count = 0
    while (ideal_distance > math.ceil(float(goal_diam) / 2) and 
           iteration_count < config.max_iterations):
        ideal_cumulative_distance += ideal_distance
        ideal_distance = (ideal_distance - velocity * sample_rate)
        iteration_count += 1
        if ideal_cumulative_distance > config.max_cumulative_distance:
            logging.warning(
                f"Max cumulative distance {config.max_cumulative_distance} exceeded, breaking while loop"
            )
            break
    
    if iteration_count >= config.max_iterations:
        logging.warning(
            f"While loop reached MAX_ITERATIONS ({config.max_iterations}), possible infinite loop condition"
        )
    
    ipe = float(distance_from_goal_summed - ideal_cumulative_distance) * sample_rate
    
    if ipe < 0:
        ipe = 0.0
    
    # Calculate entropy if enabled
    if config.use_entropy and CAN_USE_ENTROPY:
        try:
            entropy_result = calculate_entropy(array_x, array_y, goal_x, goal_y)
        except Exception as e:
            logging.warning(f"Entropy calculation failed: {e}")
            entropy_result = None
    else:
        entropy_result = None
    
    # Return results as TrialMetrics dataclass
    return TrialMetrics(
        corridor_average=corridor_average,
        distance_average=distance_average,
        average_distance_to_swim_path_centroid=average_distance_to_swim_path_centroid,
        average_distance_to_centre=average_distance_to_centre,
        average_heading_error=average_heading_error,
        percent_traversed=percent_traversed,
        quadrant_total=quadrant_total,
        total_distance=total_distance,
        latency=latency,
        full_thigmo_counter=full_thigmo_counter,
        small_thigmo_counter=small_thigmo_counter,
        annulus_counter=annulus_counter,
        sample_count=i,
        trajectory_x=array_x,
        trajectory_y=array_y,
        velocity=velocity,
        ipe=ipe,
        average_initial_heading_error=average_initial_heading_error,
        entropy=entropy_result
    )


def classify_strategy(
    metrics: TrialMetrics,
    parameters: Parameters,
    maze_radius: float
) -> Tuple[str, int]:
    """
    Classify a trial's search strategy based on its metrics and thresholds.
    
    This is a pure decision tree that classifies Morris Water Maze trials into
    one of 9 search strategy types based on spatial, kinematic, and coverage metrics.
    
    Extracted from SearchStrategyAnalysis/Pathfinder.py lines 2420-2475 (mainCalculate method).
    
    Strategy Types (in order of evaluation):
    1. Direct Path (score=3) - Most efficient, straight to platform
    2. Focal Search (score=2) - Focused searching near platform
    3. Directed Search (score=2) - Swimming in corridor toward platform
    4. Indirect Search (score=2) - Near miss, good heading but misses platform
    5. Semi-Focal Search (score=2) - Broader focused search
    6. Chaining (score=1) - Circling annulus zone
    7. Scanning (score=1) - Systematic coverage of pool
    8. Thigmotaxis (score=0) - Wall-hugging behavior
    9. Random Search (score=0) - High coverage, no spatial strategy
    10. Not Recognized (score=0) - Doesn't fit any category
    
    Args:
        metrics: TrialMetrics object containing all 19 calculated metrics
        parameters: Parameters object with classification thresholds
        maze_radius: Radius of the maze/pool (needed for percentage calculations)
        
    Returns:
        Tuple of (strategy_name: str, score: int) where score is 0-3 (higher = better)
        
    Example:
        >>> metrics = calculate_trial_metrics(trial, ...)
        >>> params = Parameters()  # Use defaults
        >>> strategy, score = classify_strategy(metrics, params, maze_radius=150)
        >>> print(f"Strategy: {strategy} (score: {score})")
        Strategy: Direct Path (score: 3)
    """
    # Extract metrics for readability
    ipe = metrics.ipe
    average_heading_error = metrics.average_heading_error
    average_distance_to_swim_path_centroid = metrics.average_distance_to_swim_path_centroid
    distance_average = metrics.distance_average
    total_distance = metrics.total_distance
    corridor_average = metrics.corridor_average
    percent_traversed = metrics.percent_traversed
    annulus_counter = metrics.annulus_counter
    quadrant_total = metrics.quadrant_total
    average_distance_to_centre = metrics.average_distance_to_centre
    full_thigmo_counter = metrics.full_thigmo_counter
    small_thigmo_counter = metrics.small_thigmo_counter
    sample_count = metrics.sample_count
    
    # DIRECT PATH
    if (ipe <= parameters.ipeMaxVal and 
        average_heading_error <= parameters.headingMaxVal and 
        parameters.useDirect):
        return ("Direct Path", 3)
    
    # FOCAL SEARCH
    elif (average_distance_to_swim_path_centroid < (maze_radius * parameters.distanceToSwimMaxVal / 100) and 
          distance_average < (parameters.distanceToPlatMaxVal / 100 * maze_radius) and 
          total_distance < parameters.focalMaxDistance and 
          total_distance > parameters.focalMinDistance and 
          parameters.useFocal):
        return ("Focal Search", 2)
    
    # DIRECTED SEARCH
    elif (corridor_average >= parameters.corridorAverageMinVal / 100 and 
          ipe <= parameters.corridoripeMaxVal and 
          total_distance < parameters.directedSearchMaxDistance and 
          parameters.useDirected):
        return ("Directed Search", 2)
    
    # INDIRECT SEARCH
    elif (ipe < parameters.ipeIndirectMaxVal and 
          average_heading_error < parameters.headingIndirectMaxVal and 
          parameters.useIndirect):
        return ("Indirect Search", 2)
    
    # SEMI-FOCAL SEARCH
    elif (average_distance_to_swim_path_centroid < (maze_radius * parameters.distanceToSwimMaxVal2 / 100) and 
          distance_average < (parameters.distanceToPlatMaxVal2 / 100 * maze_radius) and 
          total_distance < parameters.semiFocalMaxDistance and 
          total_distance > parameters.semiFocalMinDistance and 
          parameters.useSemiFocal):
        return ("Semi-focal Search", 2)
    
    # CHAINING
    elif (float(annulus_counter / sample_count) > parameters.annulusCounterMaxVal / 100 and 
          quadrant_total >= parameters.quadrantTotalMaxVal and 
          percent_traversed < parameters.chainingMaxCoverage and 
          parameters.useChaining):
        return ("Chaining", 1)
    
    # SCANNING
    elif (parameters.percentTraversedMinVal <= percent_traversed and 
          parameters.percentTraversedMaxVal > percent_traversed and 
          average_distance_to_centre <= (parameters.distanceToCentreMaxVal / 100 * maze_radius) and 
          parameters.useScanning):
        return ("Scanning", 1)
    
    # THIGMOTAXIS
    elif (full_thigmo_counter / sample_count >= parameters.fullThigmoMinVal / 100 and 
          small_thigmo_counter / sample_count >= parameters.smallThigmoMinVal / 100 and 
          total_distance > parameters.thigmoMinDistance and 
          parameters.useThigmotaxis):
        return ("Thigmotaxis", 0)
    
    # RANDOM SEARCH
    elif (percent_traversed >= parameters.percentTraversedRandomMaxVal and 
          parameters.useRandom):
        return ("Random Search", 0)
    
    # NOT RECOGNIZED
    else:
        return ("Not Recognized", 0)


def aggregate_heatmap_data(
    experiment,  # Experiment object (iterable of trials)
    filters: Dict[str, Any],
    gridsize: int = 50,
    gaussian_sigma: float = 2.0
) -> HeatmapData:
    """
    Aggregate position data from trials into heatmap array for visualization.
    
    Pure analysis function - NO plotting or GUI dependencies.
    Extracted from SearchStrategyAnalysis/Pathfinder.py heatmap() method (lines 1557-1689).
    
    This function:
    1. Filters trials by day and trial number ranges
    2. Collects x, y position coordinates from matching trials
    3. Applies Gaussian smoothing to reduce noise
    4. Computes spatial extent and 2D histogram
    5. Returns HeatmapData ready for visualization
    
    Args:
        experiment: Experiment object containing trials (iterable)
        filters: Dictionary with filter parameters:
            - 'day_filter': str - "All", "1", "1-3", etc.
            - 'trial_filter': str - "All", "1", "1-5", etc.
        gridsize: Grid size for hexbin/heatmap (default: 50)
        gaussian_sigma: Sigma parameter for Gaussian smoothing (default: 2.0)
        
    Returns:
        HeatmapData object containing:
            - x_smoothed, y_smoothed: Gaussian-filtered coordinates
            - x_raw, y_raw: Original coordinates
            - extent: (xMin, xMax, yMin, yMax)
            - gridsize: Grid size for visualization
            - histogram, xedges, yedges: Optional 2D histogram data
            
    Example:
        >>> filters = {'day_filter': 'All', 'trial_filter': '1-3'}
        >>> heatmap_data = aggregate_heatmap_data(experiment, filters, gridsize=50)
        >>> # Now pass heatmap_data to visualization function
    """
    # Parse filters
    day_filter = filters.get('day_filter', 'All')
    trial_filter = filters.get('trial_filter', 'All')
    
    # Parse day range
    day_start_stop: List[float] = []
    if day_filter == "All" or day_filter == "all" or day_filter == "":
        day_start_stop = [1, float(math.inf)]
    elif "-" in day_filter:
        parts = day_filter.split("-", 1)
        day_start_stop = [int(parts[0]), int(parts[1])]
    else:
        day_start_stop = [int(day_filter), int(day_filter)]
    
    # Parse trial range
    trial_start_stop: List[float] = []
    if trial_filter == "All" or trial_filter == "all" or trial_filter == "":
        trial_start_stop = [1, float(math.inf)]
    elif "-" in trial_filter:
        parts = trial_filter.split("-", 1)
        trial_start_stop = [int(parts[0]), int(parts[1])]
    else:
        trial_start_stop = [int(trial_filter), int(trial_filter)]
    
    # Initialize data collection
    x: List[float] = []
    y: List[float] = []
    x_min = float('inf')
    y_min = float('inf')
    x_max = float('-inf')
    y_max = float('-inf')
    
    day_num = 0
    trial_num: Dict[str, int] = {}
    cur_date = None
    
    # Iterate through trials and collect position data
    for a_trial in experiment:
        # Track animal identifier
        animal = ""
        if hasattr(experiment, 'hasAnimalNames') and experiment.hasAnimalNames:
            if hasattr(a_trial, 'animal'):
                animal = a_trial.animal.replace("*", "")
        
        # Track day number
        if hasattr(experiment, 'hasDateInfo') and experiment.hasDateInfo:
            if hasattr(a_trial, 'date'):
                trial_date = a_trial.date.date() if hasattr(a_trial.date, 'date') else a_trial.date
                if trial_date != cur_date:
                    day_num += 1
                    cur_date = trial_date
                    trial_num = {}
                    trial_num[animal] = 1
                elif animal in trial_num:
                    trial_num[animal] += 1
                else:
                    trial_num[animal] = 1
            else:
                if animal in trial_num:
                    trial_num[animal] += 1
                else:
                    trial_num[animal] = 1
        else:
            if animal in trial_num:
                trial_num[animal] += 1
            else:
                trial_num[animal] = 1
        
        # Get datapoints from trial
        if hasattr(a_trial, 'datapointList'):
            datapoints = a_trial.datapointList
        elif hasattr(a_trial, 'trajectory'):
            datapoints = a_trial.trajectory
        else:
            try:
                datapoints = list(a_trial)
            except TypeError:
                logging.warning(f"Could not iterate trial: {a_trial}")
                continue
        
        # Helper functions to access datapoint coordinates
        def get_x(dp):
            if hasattr(dp, 'getx'):
                return dp.getx()
            return dp.x
        
        def get_y(dp):
            if hasattr(dp, 'gety'):
                return dp.gety()
            return dp.y
        
        # Collect coordinates from datapoints that pass filters
        for a_datapoint in datapoints:
            # Apply day and trial filters
            passes_filter = True
            
            if day_num != 0 and trial_num:
                if not (day_num >= day_start_stop[0] and day_num <= day_start_stop[1]):
                    passes_filter = False
                if animal in trial_num:
                    if not (trial_num[animal] >= trial_start_stop[0] and 
                           trial_num[animal] <= trial_start_stop[1]):
                        passes_filter = False
            
            if not passes_filter:
                continue
            
            # Skip missing data points
            x_val = get_x(a_datapoint)
            y_val = get_y(a_datapoint)
            
            if x_val == "-" or y_val == "-":
                continue
            
            # Convert to float and collect
            try:
                x_float = float(x_val)
                y_float = float(y_val)
            except (TypeError, ValueError):
                logging.warning(f"Could not convert coordinates to float: x={x_val}, y={y_val}")
                continue
            
            x.append(x_float)
            y.append(y_float)
            
            # Track extent
            if x_float < x_min:
                x_min = x_float
            if y_float < y_min:
                y_min = y_float
            if x_float > x_max:
                x_max = x_float
            if y_float > y_max:
                y_max = y_float
    
    # Handle empty data case
    if len(x) == 0 or len(y) == 0:
        logging.warning("No data points collected after filtering")
        return HeatmapData(
            x_smoothed=np.array([]),
            y_smoothed=np.array([]),
            x_raw=[],
            y_raw=[],
            extent=(0.0, 0.0, 0.0, 0.0),
            gridsize=gridsize,
            histogram=None,
            xedges=None,
            yedges=None
        )
    
    # Apply Gaussian smoothing to reduce noise
    # Uses scipy.ndimage.gaussian_filter (pure analysis, no plotting)
    x_smoothed = sp.gaussian_filter(x, sigma=gaussian_sigma, order=0)
    y_smoothed = sp.gaussian_filter(y, sigma=gaussian_sigma, order=0)
    
    # Create 2D histogram (optional - can also be computed by visualization layer)
    histogram, xedges, yedges = np.histogram2d(x_smoothed, y_smoothed)
    
    # Return aggregated data
    return HeatmapData(
        x_smoothed=x_smoothed,
        y_smoothed=y_smoothed,
        x_raw=x,
        y_raw=y,
        extent=(x_min, x_max, y_min, y_max),
        gridsize=gridsize,
        histogram=histogram,
        xedges=xedges,
        yedges=yedges
    )


def calculate_auto_parameters(
    experiment,  # Experiment object (iterable of trials)
    max_trial_length: float = 50.0,
    manual_goal: Optional[Tuple[float, float]] = None,
    manual_maze_centre: Optional[Tuple[float, float]] = None,
    manual_maze_diameter: Optional[float] = None,
    manual_goal_diameter: Optional[float] = None
) -> AutoParameters:
    """
    Automatically calculate experimental parameters from trial data.
    
    Pure analysis function - NO GUI dependencies (messagebox, status updates, etc.).
    Extracted from SearchStrategyAnalysis/Pathfinder.py getAutoLocations() method (lines 1732-1935).
    
    This function analyzes trial trajectories to estimate:
    1. Maze center position (midpoint of spatial extent)
    2. Platform/goal position (average end position within time limit)
    3. Maze diameter (full spatial extent)
    4. Platform diameter (estimated from position variance)
    
    Args:
        experiment: Experiment object containing trials (iterable)
        max_trial_length: Maximum time (seconds) to consider for platform estimation (default: 50.0)
        manual_goal: Optional manual goal position (x, y) - skips auto-calculation
        manual_maze_centre: Optional manual maze centre (x, y) - skips auto-calculation
        manual_maze_diameter: Optional manual maze diameter - skips auto-calculation
        manual_goal_diameter: Optional manual goal diameter - skips auto-calculation
        
    Returns:
        AutoParameters object containing estimated or manual parameters
        
    Raises:
        ValueError: If insufficient data to calculate parameters
        
    Example:
        >>> params = calculate_auto_parameters(experiment)
        >>> print(f"Goal: ({params.goal_x}, {params.goal_y})")
        >>> print(f"Maze centre: ({params.maze_centre_x}, {params.maze_centre_y})")
    """
    # Initialize variables
    plat_est_x = 0.0
    plat_est_y = 0.0
    max_x = 0.0
    min_x = 0.0
    max_y = 0.0
    min_y = 0.0
    av_max_y = 0.0
    av_min_y = 0.0
    av_max_x = 0.0
    av_min_x = 0.0
    abs_max_x = 0.0
    abs_max_y = 0.0
    abs_min_x = 0.0
    abs_min_y = 0.0
    maze_centre_est_x = 0.0
    maze_centre_est_y = 0.0
    maze_radius = 0.0
    count = 0.0
    centre_count = 0.0
    last_x = 0.0
    last_y = 0.0
    plat_max_x = -100.0
    plat_min_x = 100.0
    plat_max_y = -100.0
    plat_min_y = 100.0
    plat_est_diam = 0.0
    
    warnings: List[str] = []
    
    # Determine which parameters need calculation
    need_goal = manual_goal is None
    need_maze_centre = manual_maze_centre is None
    need_maze_diameter = manual_maze_diameter is None
    need_goal_diameter = manual_goal_diameter is None
    
    # Set manual values if provided
    goal_x = manual_goal[0] if manual_goal else 0.0
    goal_y = manual_goal[1] if manual_goal else 0.0
    maze_centre_x = manual_maze_centre[0] if manual_maze_centre else 0.0
    maze_centre_y = manual_maze_centre[1] if manual_maze_centre else 0.0
    maze_diameter = manual_maze_diameter if manual_maze_diameter else 0.0
    goal_diameter = manual_goal_diameter if manual_goal_diameter else 0.0
    
    # If all values are manual, return immediately
    if not (need_goal or need_maze_centre or need_maze_diameter or need_goal_diameter):
        return AutoParameters(
            maze_centre_x=maze_centre_x,
            maze_centre_y=maze_centre_y,
            goal_x=goal_x,
            goal_y=goal_y,
            maze_diameter=maze_diameter,
            maze_radius=maze_diameter / 2.0,
            goal_diameter=goal_diameter,
            trial_count=0,
            warnings=["All parameters set manually"]
        )
    
    # Iterate through trials to collect data
    for a_trial in experiment:
        # Get datapoints from trial
        if hasattr(a_trial, 'datapointList'):
            datapoints = a_trial.datapointList
        elif hasattr(a_trial, 'trajectory'):
            datapoints = a_trial.trajectory
        else:
            try:
                datapoints = list(a_trial)
            except TypeError:
                logging.warning(f"Could not iterate trial: {a_trial}")
                continue
        
        # Helper functions to access datapoint attributes
        def get_x(dp):
            if hasattr(dp, 'getx'):
                return dp.getx()
            return dp.x
        
        def get_y(dp):
            if hasattr(dp, 'gety'):
                return dp.gety()
            return dp.y
        
        def get_time(dp):
            if hasattr(dp, 'gettime'):
                return dp.gettime()
            return dp.time
        
        # Reset trial-level tracking
        max_x = 0.0
        min_x = 0.0
        max_y = 0.0
        min_y = 0.0
        
        # Process datapoints
        for a_datapoint in datapoints:
            x_val = get_x(a_datapoint)
            y_val = get_y(a_datapoint)
            
            # Skip missing data
            if x_val == "-" or x_val == "":
                continue
            if y_val == "-" or y_val == "":
                continue
            
            try:
                x_float = float(x_val)
                y_float = float(y_val)
                time_val = float(get_time(a_datapoint))
            except (TypeError, ValueError):
                continue
            
            # Track last position within time limit (for platform estimation)
            skip_flag = False
            if time_val < max_trial_length:
                last_x = x_float
                last_y = y_float
                skip_flag = False
            else:
                skip_flag = True
            
            # Track spatial extent for this trial
            if x_float > max_x:
                max_x = x_float
            if x_float < min_x:
                min_x = x_float
            if y_float > max_y:
                max_y = y_float
            if y_float < min_y:
                min_y = y_float
            
            # Track absolute spatial extent across all trials
            if max_x > abs_max_x:
                abs_max_x = max_x
            if min_x < abs_min_x:
                abs_min_x = min_x
            if max_y > abs_max_y:
                abs_max_y = max_y
            if min_y < abs_min_y:
                abs_min_y = min_y
            
            # Accumulate for averaging
            av_max_x += max_x
            av_max_y += max_y
            av_min_x += min_x
            av_min_y += min_y
            centre_count += 1.0
            
            # Track platform position estimates
            if not skip_flag:
                count += 1.0
                plat_est_x += last_x
                plat_est_y += last_y
                
                # Track platform extent for diameter estimation
                if last_x > plat_max_x:
                    plat_max_x = last_x
                if last_x < plat_min_x:
                    plat_min_x = last_x
                if last_y > plat_max_y:
                    plat_max_y = last_y
                if last_y < plat_min_y:
                    plat_min_y = last_y
    
    # Validate we have enough data
    if centre_count < 1 and (need_maze_centre or need_maze_diameter):
        raise ValueError("Unable to determine maze parameters - no valid datapoints found")
    
    if count < 1 and need_goal:
        raise ValueError("Unable to determine goal position - no valid datapoints within time limit")
    
    # Calculate maze centre if needed
    if need_maze_centre:
        av_max_x = av_max_x / centre_count
        av_max_y = av_max_y / centre_count
        av_min_x = av_min_x / centre_count
        av_min_y = av_min_y / centre_count
        maze_centre_est_x = (av_max_x + av_min_x) / 2
        maze_centre_est_y = (av_max_y + av_min_y) / 2
        maze_centre_x = maze_centre_est_x
        maze_centre_y = maze_centre_est_y
        logging.info(f"Automatic maze centre calculated as: {maze_centre_est_x}, {maze_centre_est_y}")
    
    # Calculate goal position if needed
    if need_goal:
        plat_est_x = plat_est_x / count
        plat_est_y = plat_est_y / count
        goal_x = plat_est_x
        goal_y = plat_est_y
        logging.info(f"Automatic goal position calculated as: {plat_est_x}, {plat_est_y}")
    
    # Calculate goal diameter if needed
    if need_goal_diameter:
        plat_est_diam = ((plat_max_x - plat_min_x) + (plat_max_y - plat_min_y)) / 2
        if plat_est_diam > 50 or plat_est_diam < 1:
            plat_est_diam = 10.0
            warnings.append(f"Goal diameter estimation unreliable (range: {plat_est_diam}), defaulted to 10.0")
            logging.warning(f"Automatic goal diameter calculation failed. Defaulted to: {math.ceil(plat_est_diam)}")
        else:
            logging.info(f"Automatic goal diameter calculated as: {math.ceil(plat_est_diam)}")
        goal_diameter = plat_est_diam
    
    # Calculate maze diameter if needed
    if need_maze_diameter:
        maze_diam_est = ((abs(abs_max_x) + abs(abs_min_x)) + (abs(abs_max_y) + abs(abs_min_y))) / 2
        logging.info(f"Automatic maze diameter calculated as: {maze_diam_est}")
        maze_diameter = maze_diam_est
        maze_radius = maze_diameter / 2.0
    else:
        maze_radius = maze_diameter / 2.0
    
    # Return results
    return AutoParameters(
        maze_centre_x=maze_centre_x,
        maze_centre_y=maze_centre_y,
        goal_x=goal_x,
        goal_y=goal_y,
        maze_diameter=maze_diameter,
        maze_radius=maze_radius,
        goal_diameter=goal_diameter,
        trial_count=int(count if need_goal else centre_count),
        warnings=warnings
    )
