"""
Core analysis module for Morris Water Maze search strategy detection.
Modernized from original Pathfinder.py with type hints and modular design.
"""

from typing import List, Tuple, Optional, Dict
import math
from pathfinder_modernized_models import (
    Trial, Parameters, SearchStrategy, Datapoint, AnalysisResult
)
from datetime import datetime


class StrategyAnalyzer:
    """
    Analyzes trial trajectories to determine search strategy.
    Encapsulates the core analysis algorithms.
    """
    
    def __init__(self, parameters: Parameters):
        """
        Initialize analyzer with parameters.
        
        Args:
            parameters: Configuration parameters for analysis
        """
        self.parameters = parameters
    
    def analyze_trial(self, trial: Trial) -> Tuple[SearchStrategy, float]:
        """
        Determine the search strategy for a trial.
        
        Args:
            trial: Trial data to analyze
            
        Returns:
            Tuple of (detected_strategy, confidence_score)
        """
        if not trial.trajectory or len(trial.trajectory) < 2:
            return SearchStrategy.RANDOM_SEARCH, 0.0
        
        # Calculate key metrics
        metrics = self._calculate_metrics(trial)
        
        # Apply strategy detection rules
        strategy = self._detect_strategy(metrics, trial)
        confidence = self._calculate_confidence(metrics, strategy)
        
        return strategy, confidence
    
    def _calculate_metrics(self, trial: Trial) -> Dict[str, float]:
        """
        Calculate key metrics from trajectory.
        
        Args:
            trial: Trial to analyze
            
        Returns:
            Dictionary of computed metrics
        """
        trajectory = trial.trajectory
        
        # Total distance
        total_distance = sum(
            self._euclidean_distance(
                trajectory[i], trajectory[i + 1]
            )
            for i in range(len(trajectory) - 1)
        )
        
        # Average speed
        total_time = trajectory[-1].time - trajectory[0].time
        avg_speed = total_distance / total_time if total_time > 0 else 0
        
        # Distance to platform trend
        platform_pos = trial.platform_position
        distances_to_platform = [
            self._euclidean_distance_to_point(
                (dp.x, dp.y), platform_pos
            )
            for dp in trajectory
        ]
        
        distance_trend = distances_to_platform[-1] - distances_to_platform[0]
        
        # Thigmotaxis (wall-following) measure
        pool_center = trial.pool_center
        pool_radius = trial.pool_diameter / 2
        distance_from_center = [
            self._euclidean_distance_to_point(
                (dp.x, dp.y), pool_center
            )
            for dp in trajectory
        ]
        wall_proximity = sum(
            1 for d in distance_from_center 
            if d > pool_radius * 0.8
        ) / len(distance_from_center) * 100
        
        return {
            'total_distance': total_distance,
            'avg_speed': avg_speed,
            'distance_trend': distance_trend,
            'wall_proximity': wall_proximity,
            'path_length': total_distance,
            'escape_latency': total_time,
        }
    
    def _detect_strategy(self, metrics: Dict[str, float], trial: Trial) -> SearchStrategy:
        """
        Determine strategy based on metrics and rules.
        
        Args:
            metrics: Calculated metrics
            trial: Original trial data
            
        Returns:
            Detected search strategy
        """
        # Simplified decision rules (expand based on original algorithm)
        
        if metrics['wall_proximity'] > 80:
            return SearchStrategy.THIGMOTAXIS
        
        if metrics['distance_trend'] < -50:  # Strong trend toward platform
            return SearchStrategy.DIRECTED_SEARCH
        
        if metrics['path_length'] < 100:
            return SearchStrategy.DIRECT_SWIM
        
        if metrics['avg_speed'] > 30:
            return SearchStrategy.SCANNING
        
        return SearchStrategy.RANDOM_SEARCH
    
    def _calculate_confidence(self, metrics: Dict[str, float], strategy: SearchStrategy) -> float:
        """
        Calculate confidence in detected strategy.
        
        Args:
            metrics: Calculated metrics
            strategy: Detected strategy
            
        Returns:
            Confidence score 0-1
        """
        # Simple confidence model (expand based on domain knowledge)
        base_confidence = 0.7
        
        if strategy == SearchStrategy.RANDOM_SEARCH:
            base_confidence = 0.5
        
        return min(1.0, max(0.0, base_confidence))
    
    @staticmethod
    def _euclidean_distance(p1: Datapoint, p2: Datapoint) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
    
    @staticmethod
    def _euclidean_distance_to_point(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two coordinate tuples"""
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


class FileParser:
    """
    Handles parsing trial data from various formats.
    Supports: Ethovision (Excel), Anymaze (CSV), WaterMaze (CSV), ezTrack (CSV)
    """
    
    def __init__(self, software: str):
        """
        Initialize parser for specific tracking software.
        
        Args:
            software: Name of tracking software (e.g., 'Ethovision', 'Anymaze')
        """
        self.software = software
    
    def parse_file(self, filepath: str) -> List[Trial]:
        """
        Parse a data file into Trial objects.
        
        Args:
            filepath: Path to file
            
        Returns:
            List of parsed trials
        """
        if self.software.lower() == 'ethovision':
            return self._parse_ethovision(filepath)
        elif self.software.lower() == 'anymaze':
            return self._parse_anymaze(filepath)
        else:
            raise ValueError(f"Unsupported software: {self.software}")
    
    def _parse_ethovision(self, filepath: str) -> List[Trial]:
        """Parse Ethovision Excel format"""
        # Placeholder implementation
        trials: List[Trial] = []
        # TODO: Implement Excel parsing with openpyxl
        return trials
    
    def _parse_anymaze(self, filepath: str) -> List[Trial]:
        """Parse Anymaze CSV format"""
        # Placeholder implementation
        trials: List[Trial] = []
        # TODO: Implement CSV parsing
        return trials


def analyze_experiment(
    experiment_data: Dict,
    parameters: Parameters
) -> List[AnalysisResult]:
    """
    Analyze all trials in an experiment.
    
    Args:
        experiment_data: Experiment with trials
        parameters: Analysis parameters
        
    Returns:
        List of analysis results
    """
    analyzer = StrategyAnalyzer(parameters)
    results: List[AnalysisResult] = []
    
    for trial in experiment_data.get('trials', []):
        strategy, confidence = analyzer.analyze_trial(trial)
        
        result = AnalysisResult(
            experiment_id=experiment_data.get('experiment_id', ''),
            trial_id=trial.trial_id,
            detected_strategy=strategy,
            confidence=confidence,
            metrics=analyzer._calculate_metrics(trial)
        )
        results.append(result)
    
    return results
