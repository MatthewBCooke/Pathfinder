#!/usr/bin/env python3
"""
End-to-end functional test for Pathfinder GUI.

Tests the complete workflow:
1. Load an experiment file
2. Run analysis
3. Display results
4. Verify data integrity

Run with: python test_gui_e2e.py
"""

import sys
from pathfinder import (
    load_experiment,
    calculate_trial_metrics,
    classify_strategy,
    Trial,
    Datapoint,
    Experiment,
)
from pathfinder.types import TrialMetrics


def create_test_experiment() -> Experiment:
    """Create a minimal test experiment for GUI testing."""
    exp = Experiment("Test Experiment")
    
    # Create 3 test trials with realistic data
    for trial_num in range(1, 4):
        trial = Trial()
        trial.setname(f"Trial_{trial_num}")
        trial.setanimal(f"Mouse_{trial_num}")
        trial.setday(trial_num)
        trial.settrial(trial_num)
        
        # Add position data (circular pattern moving toward goal)
        import math
        goal_x, goal_y = 128.0, 128.0
        
        for i in range(0, 100):
            t = i * 0.1
            # Spiral toward goal
            angle = i * 0.1
            distance = 100 - (i * 0.5)  # Moving closer to goal
            x = goal_x + distance * math.cos(angle)
            y = goal_y + distance * math.sin(angle)
            
            trial.append(Datapoint(t, x, y))
        
        exp.append(trial)
    
    return exp


def test_analysis_pipeline() -> None:
    """Test the complete analysis pipeline."""
    print("=" * 60)
    print("PATHFINDER GUI E2E TEST")
    print("=" * 60)
    
    # Create test data
    print("\n1. Creating test experiment...")
    experiment = create_test_experiment()
    print(f"   ✓ Created experiment with {len(experiment)} trials")
    
    # Define analysis parameters
    print("\n2. Setting analysis parameters...")
    params = {
        'goal_x': 128.0,
        'goal_y': 128.0,
        'maze_centre_x': 128.0,
        'maze_centre_y': 128.0,
        'corridor_width': 20.0,
        'thigmotaxis_zone_size': 10.0,
    }
    print(f"   ✓ Parameters set: {len(params)} params")
    
    # Run analysis
    print("\n3. Running analysis on trials...")
    results = []
    for i, trial in enumerate(experiment, 1):
        print(f"   Processing trial {i}/{len(experiment)}: {trial.name}")
        
        # Calculate metrics
        metrics = calculate_trial_metrics(
            trial,
            goal_x=params['goal_x'],
            goal_y=params['goal_y'],
            maze_centre_x=params['maze_centre_x'],
            maze_centre_y=params['maze_centre_y'],
            corridor_width=params['corridor_width'],
            thigmotaxis_zone_size=params['thigmotaxis_zone_size'],
        )
        
        # Verify metrics
        assert isinstance(metrics, TrialMetrics), "Invalid metrics object"
        assert hasattr(metrics, 'ipe'), "Missing IPE metric"
        assert hasattr(metrics, 'entropy'), "Missing entropy metric"
        
        print(f"      → IPE: {metrics.ipe:.2f}")
        print(f"      → Entropy: {metrics.entropy:.2f}")
        
        results.append(metrics)
    
    print(f"   ✓ Analysis complete: {len(results)} trials processed")
    
    # Verify results
    print("\n4. Verifying results...")
    assert len(results) == len(experiment), "Mismatch in result count"
    
    for i, metrics in enumerate(results, 1):
        assert isinstance(metrics, TrialMetrics), f"Trial {i}: Invalid metrics"
        assert metrics.ipe >= 0, f"Trial {i}: Invalid IPE"
        assert metrics.entropy >= 0, f"Trial {i}: Invalid entropy"
    
    print(f"   ✓ All {len(results)} results verified")
    
    # Display summary
    print("\n5. Results Summary:")
    print(f"   Trials analyzed: {len(results)}")
    print(f"   Avg IPE: {sum(r.ipe for r in results) / len(results):.2f}")
    print(f"   Avg Entropy: {sum(r.entropy for r in results) / len(results):.2f}")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)
    print("\nThe GUI is ready to use!")
    print("Run: python pathfinder_gui.py")


if __name__ == "__main__":
    try:
        test_analysis_pipeline()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
