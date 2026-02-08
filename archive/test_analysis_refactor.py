#!/usr/bin/env python3
"""
Quick test to verify the refactored calculate_trial_metrics() function works.
"""

import sys
sys.path.insert(0, '/tmp/Pathfinder')
sys.path.insert(0, '/tmp/Pathfinder/SearchStrategyAnalysis')

from pathfinder.analysis import calculate_trial_metrics
from pathfinder.types import AnalysisConfig, TrialMetrics


# Mock datapoint class that matches the legacy interface
class MockDatapoint:
    def __init__(self, x, y, time):
        self._x = x
        self._y = y
        self._time = time
    
    def getx(self):
        return self._x
    
    def gety(self):
        return self._y
    
    def gettime(self):
        return self._time


# Mock trial class
class MockTrial:
    def __init__(self, datapoints):
        self.datapointList = datapoints
    
    def __iter__(self):
        return iter(self.datapointList)
    
    def __str__(self):
        return f"MockTrial({len(self.datapointList)} points)"


def test_basic_trial():
    """Test with a simple circular path"""
    print("=" * 60)
    print("TEST: Basic circular trial")
    print("=" * 60)
    
    # Create a simple circular path
    import math
    datapoints = []
    num_points = 100
    radius = 80.0
    center_x, center_y = 100.0, 100.0
    
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        time = i * 0.1  # 0.1 second intervals
        datapoints.append(MockDatapoint(x, y, time))
    
    trial = MockTrial(datapoints)
    
    # Test parameters
    goal_x = 100.0
    goal_y = 100.0
    maze_centre_x = 100.0
    maze_centre_y = 100.0
    corridor_width = 15.0
    thigmotaxis_zone_size = 20.0
    chaining_radius = 30.0
    full_thigmo_zone = 70.0
    small_thigmo_zone = 85.0
    maze_radius = 100.0
    day_num = 1
    goal_diam = 10.0
    
    config = AnalysisConfig(
        grid_cell_size=10.0,
        max_iterations=100000,
        max_cumulative_distance=1000000.0,
        use_entropy=True,
        truncate_at_platform=False
    )
    
    try:
        metrics = calculate_trial_metrics(
            trial=trial,
            goal_x=goal_x,
            goal_y=goal_y,
            maze_centre_x=maze_centre_x,
            maze_centre_y=maze_centre_y,
            corridor_width=corridor_width,
            thigmotaxis_zone_size=thigmotaxis_zone_size,
            chaining_radius=chaining_radius,
            full_thigmo_zone=full_thigmo_zone,
            small_thigmo_zone=small_thigmo_zone,
            maze_radius=maze_radius,
            day_num=day_num,
            goal_diam=goal_diam,
            config=config
        )
        
        print("✅ SUCCESS: Function executed without errors")
        print("\nMetrics returned:")
        print(f"  Latency: {metrics.latency:.2f} seconds")
        print(f"  Total Distance: {metrics.total_distance:.2f}")
        print(f"  Velocity: {metrics.velocity:.2f}")
        print(f"  Average Distance to Goal: {metrics.distance_average:.2f}")
        print(f"  Corridor Average: {metrics.corridor_average:.2%}")
        print(f"  Percent Traversed: {metrics.percent_traversed:.1f}%")
        print(f"  Quadrants Visited: {metrics.quadrant_total}")
        print(f"  Sample Count: {int(metrics.sample_count)}")
        print(f"  IPE (Ideal Path Error): {metrics.ipe:.2f}")
        print(f"  Average Heading Error: {metrics.average_heading_error:.2f}°")
        print(f"  Entropy: {metrics.entropy}")
        print(f"  Trajectory Length: {len(metrics.trajectory_x)} points")
        
        # Verify return type
        assert isinstance(metrics, TrialMetrics), "Return type should be TrialMetrics"
        
        # Verify all 19 metrics exist
        assert hasattr(metrics, 'corridor_average')
        assert hasattr(metrics, 'distance_average')
        assert hasattr(metrics, 'average_distance_to_swim_path_centroid')
        assert hasattr(metrics, 'average_distance_to_centre')
        assert hasattr(metrics, 'average_heading_error')
        assert hasattr(metrics, 'percent_traversed')
        assert hasattr(metrics, 'quadrant_total')
        assert hasattr(metrics, 'total_distance')
        assert hasattr(metrics, 'latency')
        assert hasattr(metrics, 'full_thigmo_counter')
        assert hasattr(metrics, 'small_thigmo_counter')
        assert hasattr(metrics, 'annulus_counter')
        assert hasattr(metrics, 'sample_count')
        assert hasattr(metrics, 'trajectory_x')
        assert hasattr(metrics, 'trajectory_y')
        assert hasattr(metrics, 'velocity')
        assert hasattr(metrics, 'ipe')
        assert hasattr(metrics, 'average_initial_heading_error')
        assert hasattr(metrics, 'entropy')
        
        print("\n✅ All 19 metrics present in TrialMetrics")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_straight_path_to_goal():
    """Test with a straight path directly to the goal"""
    print("\n" + "=" * 60)
    print("TEST: Straight path to goal (should have low IPE)")
    print("=" * 60)
    
    datapoints = []
    start_x, start_y = 50.0, 50.0
    goal_x, goal_y = 150.0, 150.0
    
    num_points = 50
    for i in range(num_points):
        t = i / (num_points - 1)
        x = start_x + t * (goal_x - start_x)
        y = start_y + t * (goal_y - start_y)
        time = i * 0.1
        datapoints.append(MockDatapoint(x, y, time))
    
    trial = MockTrial(datapoints)
    
    config = AnalysisConfig(use_entropy=True, truncate_at_platform=False)
    
    try:
        metrics = calculate_trial_metrics(
            trial=trial,
            goal_x=goal_x,
            goal_y=goal_y,
            maze_centre_x=100.0,
            maze_centre_y=100.0,
            corridor_width=15.0,
            thigmotaxis_zone_size=20.0,
            chaining_radius=30.0,
            full_thigmo_zone=70.0,
            small_thigmo_zone=85.0,
            maze_radius=100.0,
            day_num=1,
            goal_diam=10.0,
            config=config
        )
        
        print("✅ SUCCESS")
        print(f"  IPE (should be low for direct path): {metrics.ipe:.2f}")
        print(f"  Corridor Average (should be high): {metrics.corridor_average:.2%}")
        print(f"  Average Heading Error: {metrics.average_heading_error:.2f}°")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        return False


def main():
    print("\n" + "🧪 " * 20)
    print("REFACTORED ANALYSIS FUNCTION TEST SUITE")
    print("🧪 " * 20 + "\n")
    
    tests = [
        test_basic_trial,
        test_straight_path_to_goal,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
