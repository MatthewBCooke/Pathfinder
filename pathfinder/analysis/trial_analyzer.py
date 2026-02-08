"""
Trial analyzer for search strategy detection.
"""

import math
import logging
from typing import Tuple
from pathfinder.core.models import Trial, SearchStrategy, AnalysisResult, Parameters
from pathfinder.core.geometry import MazeGeometry

logger = logging.getLogger(__name__)


class TrialAnalyzer:
    """
    Analyzes individual trials to detect search strategies.
    Uses rule-based classification based on trajectory metrics.
    """
    
    def __init__(self, geometry: MazeGeometry, parameters: Parameters):
        """
        Initialize analyzer.
        
        Args:
            geometry: Maze geometry configuration
            parameters: Analysis parameters
        """
        self.geometry = geometry
        self.params = parameters
    
    def analyze(self, trial: Trial) -> AnalysisResult:
        """
        Analyze a trial and detect search strategy.
        
        Args:
            trial: Trial to analyze
            
        Returns:
            AnalysisResult with detected strategy and confidence
        """
        logger.debug(f"Analyzing trial {trial.trial_id}")
        
        # Calculate metrics
        metrics = self._calculate_metrics(trial)
        
        # Detect strategy using rule-based classification
        strategy, confidence = self._detect_strategy(metrics)
        
        # Create result
        result = AnalysisResult(
            experiment_id="",  # Will be set by caller
            trial_id=trial.trial_id,
            detected_strategy=strategy,
            confidence=confidence,
            metrics=metrics
        )
        
        logger.debug(f"Trial {trial.trial_id}: {strategy.value} (confidence: {confidence:.2f})")
        
        return result
    
    def _calculate_metrics(self, trial: Trial) -> dict:
        """
        Calculate trajectory metrics for strategy detection.
        
        Args:
            trial: Trial to analyze
            
        Returns:
            Dictionary of metrics
        """
        metrics = {}
        
        if not trial.trajectory:
            return metrics
        
        trajectory = trial.trajectory
        
        # Basic metrics
        metrics['num_points'] = len(trajectory)
        metrics['duration'] = trajectory[-1].time - trajectory[0].time if len(trajectory) > 1 else 0
        
        # Path length (already calculated in trial)
        metrics['path_length'] = trial.path_length or 0.0
        
        # Swim speed
        metrics['swim_speed'] = trial.swim_speed or 0.0
        
        # Distance metrics
        first_point = trajectory[0]
        dist_to_platform_start = self.geometry.distance_to_platform(first_point.x, first_point.y)
        metrics['initial_distance_to_platform'] = dist_to_platform_start
        
        # Wall hugging (thigmotaxis) detection
        wall_time = 0
        wall_threshold = self.geometry.pool_radius * 0.2  # Within 20% of radius from wall

        valid_wall_points = 0
        for point in trajectory:
            x, y = point.x, point.y
            if (
                x is None or y is None or
                (hasattr(x, '__float__') and (math.isnan(x) or math.isinf(x))) or
                (hasattr(y, '__float__') and (math.isnan(y) or math.isinf(y)))
            ):
                continue  # Skip invalid points
            dist_to_wall = self.geometry.distance_to_wall(x, y)
            if dist_to_wall < wall_threshold:
                wall_time += 1
            valid_wall_points += 1

        metrics['percent_near_wall'] = (wall_time / valid_wall_points) * 100 if valid_wall_points else 0

        # Platform region visits
        platform_time = 0
        platform_zone = self.geometry.platform_radius * 2.5  # Zone around platform

        valid_platform_points = 0
        for point in trajectory:
            x, y = point.x, point.y
            if (
                x is None or y is None or
                (hasattr(x, '__float__') and (math.isnan(x) or math.isinf(x))) or
                (hasattr(y, '__float__') and (math.isnan(y) or math.isinf(y)))
            ):
                continue  # Skip invalid points
            dist_to_platform = self.geometry.distance_to_platform(x, y)
            if dist_to_platform < platform_zone:
                platform_time += 1
            valid_platform_points += 1

        metrics['percent_in_platform_zone'] = (platform_time / valid_platform_points) * 100 if valid_platform_points else 0
        
        # Initial heading error (IPE)
        if len(trajectory) >= 2:
            ipe = self._calculate_ipe(trajectory[0], trajectory[1])
            metrics['initial_path_error'] = ipe
        else:
            metrics['initial_path_error'] = 0
        
        # Path efficiency (straight line distance / actual path length)
        straight_line_dist = self.geometry.distance_to_platform(first_point.x, first_point.y)
        if metrics['path_length'] > 0:
            metrics['path_efficiency'] = (straight_line_dist / metrics['path_length']) * 100
        else:
            metrics['path_efficiency'] = 0
        
        # Coverage (simplified - percentage of pool quadrants visited)
        quadrants_visited = set()
        for point in trajectory:
            x, y = point.x, point.y
            if (
                x is None or y is None or
                (hasattr(x, '__float__') and (math.isnan(x) or math.isinf(x))) or
                (hasattr(y, '__float__') and (math.isnan(y) or math.isinf(y)))
            ):
                continue  # Skip invalid points
            q = self.geometry.get_quadrant(x, y)
            quadrants_visited.add(q)

        metrics['quadrant_coverage'] = len(quadrants_visited)
        
        return metrics
    
    def _calculate_ipe(self, start_point, second_point) -> float:
        """
        Calculate Initial Path Error (heading error).
        
        Args:
            start_point: First trajectory point
            second_point: Second trajectory point
            
        Returns:
            IPE in degrees
        """
        # Vector from start to platform
        dx_platform = self.geometry.platform_x - start_point.x
        dy_platform = self.geometry.platform_y - start_point.y
        angle_to_platform = math.atan2(dy_platform, dx_platform)
        
        # Vector from start to second point (actual heading)
        dx_actual = second_point.x - start_point.x
        dy_actual = second_point.y - start_point.y
        actual_heading = math.atan2(dy_actual, dx_actual)
        
        # Angular difference
        diff = abs(angle_to_platform - actual_heading)
        
        # Normalize to 0-180°
        if diff > math.pi:
            diff = 2 * math.pi - diff
        
        return math.degrees(diff)
    
    def _detect_strategy(self, metrics: dict) -> Tuple[SearchStrategy, float]:
        """
        Detect search strategy based on metrics.
        Uses rule-based classification.
        
        Args:
            metrics: Calculated trajectory metrics
            
        Returns:
            Tuple of (strategy, confidence)
        """
        # Direct Swim: low IPE, high efficiency, straight to platform
        if (metrics.get('initial_path_error', 999) < self.params.ipe_max_val and
            metrics.get('path_efficiency', 0) > 50 and
            metrics.get('initial_distance_to_platform', 0) < self.params.distance_to_swim_max_val):
            return SearchStrategy.DIRECT_SWIM, 0.9
        
        # Directed Search: reasonable heading, focused on platform area
        if (metrics.get('percent_in_platform_zone', 0) > 30 and
            metrics.get('path_efficiency', 0) > 30):
            return SearchStrategy.DIRECTED_SEARCH, 0.8
        
        # Focal Search: concentrated search in platform region
        if (metrics.get('percent_in_platform_zone', 0) > 40 and
            metrics.get('quadrant_coverage', 0) <= 2):
            return SearchStrategy.FOCAL_SEARCH, 0.85
        
        # Thigmotaxis: hugging the wall
        if metrics.get('percent_near_wall', 0) > self.params.percent_traversed_max_val:
            return SearchStrategy.THIGMOTAXIS, 0.9
        
        # Scanning: systematic coverage of pool
        if (metrics.get('quadrant_coverage', 0) >= 3 and
            metrics.get('percent_near_wall', 0) < 30):
            return SearchStrategy.SCANNING, 0.7
        
        # Chaining: repeated similar path (would need trial-to-trial comparison)
        # Simplified detection based on moderate efficiency
        if (metrics.get('path_efficiency', 0) > 20 and
            metrics.get('path_efficiency', 0) < 40):
            return SearchStrategy.CHAINING, 0.6
        
        # Spatial Indirect: some spatial knowledge but indirect approach
        if (metrics.get('percent_in_platform_zone', 0) > 15 and
            metrics.get('quadrant_coverage', 0) >= 2):
            return SearchStrategy.SPATIAL_INDIRECT, 0.7
        
        # Default: Random Search
        return SearchStrategy.RANDOM_SEARCH, 0.5
