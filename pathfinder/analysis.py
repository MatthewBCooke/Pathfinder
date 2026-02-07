"""
Core analysis functions for Morris Water Maze search strategy calculation.

Refactored from SearchStrategyAnalysis/Pathfinder.py to be pure, testable, and modular.
"""

import math
import logging
from typing import List, Tuple, Optional
import numpy as np

from pathfinder.types import TrialMetrics, AnalysisConfig

# Import entropy - handle if module is unavailable
try:
    from pathfinder.entropy import entropy as calculate_entropy
    CAN_USE_ENTROPY = True
except ImportError:
    try:
        # Fallback: try importing from original location
        import sys
        sys.path.append('/tmp/Pathfinder/SearchStrategyAnalysis')
        from entropy import entropy as calculate_entropy
        CAN_USE_ENTROPY = True
    except ImportError:
        CAN_USE_ENTROPY = False
        logging.warning("Entropy module unavailable - entropy calculations will be disabled")


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
