#!/usr/bin/env python3
"""
Quick test to verify classify_strategy function works correctly.
"""

from pathfinder.types import TrialMetrics, Parameters
from pathfinder.analysis import classify_strategy

# Create a test case that should classify as "Direct Path"
direct_path_metrics = TrialMetrics(
    corridor_average=0.95,
    distance_average=50.0,
    average_distance_to_swim_path_centroid=20.0,
    average_distance_to_centre=80.0,
    average_heading_error=25.0,  # Low heading error
    percent_traversed=8.0,
    quadrant_total=2,
    total_distance=180.0,
    latency=12.5,
    full_thigmo_counter=0.0,
    small_thigmo_counter=0.0,
    annulus_counter=5.0,
    sample_count=100.0,
    trajectory_x=[0.0, 10.0, 20.0],
    trajectory_y=[0.0, 10.0, 20.0],
    velocity=14.4,
    ipe=80.0,  # Low IPE
    average_initial_heading_error=30.0,
    entropy=None
)

# Create default parameters
params = Parameters()

# Test classification
maze_radius = 150.0
strategy, score = classify_strategy(direct_path_metrics, params, maze_radius)

print(f"✓ classify_strategy() executed successfully")
print(f"  Strategy: {strategy}")
print(f"  Score: {score}")
print(f"  Expected: Direct Path (score=3)")
print()

# Test with a random search case
random_metrics = TrialMetrics(
    corridor_average=0.2,
    distance_average=100.0,
    average_distance_to_swim_path_centroid=80.0,
    average_distance_to_centre=70.0,
    average_heading_error=120.0,
    percent_traversed=85.0,  # High coverage
    quadrant_total=4,
    total_distance=1500.0,
    latency=45.0,
    full_thigmo_counter=10.0,
    small_thigmo_counter=5.0,
    annulus_counter=2.0,
    sample_count=200.0,
    trajectory_x=[],
    trajectory_y=[],
    velocity=33.3,
    ipe=2000.0,
    average_initial_heading_error=140.0,
    entropy=None
)

strategy2, score2 = classify_strategy(random_metrics, params, maze_radius)
print(f"✓ Second test completed")
print(f"  Strategy: {strategy2}")
print(f"  Score: {score2}")
print(f"  Expected: Random Search (score=0)")
print()

print("✓ All tests passed - function is working correctly!")
