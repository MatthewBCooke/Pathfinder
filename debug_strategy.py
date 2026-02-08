#!/usr/bin/env python3
"""
Debug script to diagnose strategy classification issues.
Loads test data and prints detailed metrics for each trial.
"""

import sys
import logging
from pathlib import Path

# Add pathfinder to path
sys.path.insert(0, str(Path(__file__).parent))

from pathfinder.core.models import Experiment, Trial
from pathfinder.io.loaders import load_experiment, detect_software_format
from pathfinder.analysis.trial_analyzer import TrialAnalyzer
from pathfinder.core.geometry import MazeGeometry
from gui.defaults import get_default_parameters

# Configure verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)


def analyze_trial_debug(trial: Trial, analyzer: TrialAnalyzer):
    """Analyze a trial and print detailed debug info"""
    print(f"\n{'='*80}")
    print(f"Trial {trial.trial_number} (Day {trial.day})")
    print(f"{'='*80}")
    
    # Calculate metrics
    metrics = analyzer._calculate_metrics(trial)
    
    print(f"\n📊 Calculated Metrics:")
    for key, value in metrics.items():
        print(f"  {key:35s}: {value}")
    
    # Run detection
    strategy, confidence = analyzer._detect_strategy(metrics)
    
    print(f"\n🎯 Strategy Detection:")
    print(f"  Detected Strategy: {strategy.value}")
    print(f"  Confidence:        {confidence:.2f}")
    
    # Show which rules were checked
    params = analyzer.params
    print(f"\n🔍 Rule Evaluation:")
    
    # Direct Swim
    direct_swim_check = (
        metrics.get('initial_path_error', 999) < params.ipe_max_val and
        metrics.get('path_efficiency', 0) > 50 and
        metrics.get('initial_distance_to_platform', 0) < params.distance_to_swim_max_val
    )
    print(f"  Direct Swim:       {'✅ PASS' if direct_swim_check else '❌ FAIL'}")
    print(f"    - IPE < {params.ipe_max_val}: {metrics.get('initial_path_error', 999):.1f} < {params.ipe_max_val} = {metrics.get('initial_path_error', 999) < params.ipe_max_val}")
    print(f"    - Efficiency > 50: {metrics.get('path_efficiency', 0):.1f}% > 50% = {metrics.get('path_efficiency', 0) > 50}")
    print(f"    - Initial dist < {params.distance_to_swim_max_val}: {metrics.get('initial_distance_to_platform', 0):.1f} < {params.distance_to_swim_max_val} = {metrics.get('initial_distance_to_platform', 0) < params.distance_to_swim_max_val}")
    
    # Directed Search
    directed_check = (
        metrics.get('percent_in_platform_zone', 0) > 30 and
        metrics.get('path_efficiency', 0) > 30
    )
    print(f"  Directed Search:   {'✅ PASS' if directed_check else '❌ FAIL'}")
    print(f"    - Platform zone > 30%: {metrics.get('percent_in_platform_zone', 0):.1f}% > 30% = {metrics.get('percent_in_platform_zone', 0) > 30}")
    print(f"    - Efficiency > 30%: {metrics.get('path_efficiency', 0):.1f}% > 30% = {metrics.get('path_efficiency', 0) > 30}")
    
    # Focal Search
    focal_check = (
        metrics.get('percent_in_platform_zone', 0) > 40 and
        metrics.get('quadrant_coverage', 0) <= 2
    )
    print(f"  Focal Search:      {'✅ PASS' if focal_check else '❌ FAIL'}")
    print(f"    - Platform zone > 40%: {metrics.get('percent_in_platform_zone', 0):.1f}% > 40% = {metrics.get('percent_in_platform_zone', 0) > 40}")
    print(f"    - Quadrants <= 2: {metrics.get('quadrant_coverage', 0)} <= 2 = {metrics.get('quadrant_coverage', 0) <= 2}")
    
    # Thigmotaxis
    thigmo_check = metrics.get('percent_near_wall', 0) > params.percent_traversed_max_val
    print(f"  Thigmotaxis:       {'✅ PASS' if thigmo_check else '❌ FAIL'}")
    print(f"    - Near wall > {params.percent_traversed_max_val}%: {metrics.get('percent_near_wall', 0):.1f}% > {params.percent_traversed_max_val}% = {thigmo_check}")
    
    # Scanning
    scanning_check = (
        metrics.get('quadrant_coverage', 0) >= 3 and
        metrics.get('percent_near_wall', 0) < 30
    )
    print(f"  Scanning:          {'✅ PASS' if scanning_check else '❌ FAIL'}")
    print(f"    - Quadrants >= 3: {metrics.get('quadrant_coverage', 0)} >= 3 = {metrics.get('quadrant_coverage', 0) >= 3}")
    print(f"    - Near wall < 30%: {metrics.get('percent_near_wall', 0):.1f}% < 30% = {metrics.get('percent_near_wall', 0) < 30}")
    
    print(f"\n")
    return metrics, strategy, confidence


def main():
    """Main debug entry point"""
    # Load test data
    test_file = Path(__file__).parent / "tests" / "test_data.csv"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    
    print(f"📁 Loading test data from: {test_file}")
    
    try:
        # Detect format and load
        software = detect_software_format(test_file)
        experiment = load_experiment(test_file, software)
        
        print(f"✅ Loaded experiment: {experiment.experiment_name}")
        print(f"   Trials: {len(experiment.trials)}")
        print(f"   Software: {software.value}")
        
        # Create analyzer with defaults
        params = get_default_parameters()
        
        # Use first trial to get geometry
        first_trial = experiment.trials[0]
        geometry = MazeGeometry(
            center_x=first_trial.pool_center[0],
            center_y=first_trial.pool_center[1],
            pool_diameter=first_trial.pool_diameter,
            platform_x=first_trial.platform_position[0],
            platform_y=first_trial.platform_position[1],
            platform_diameter=first_trial.platform_diameter
        )
        
        print(f"\n🎯 Maze Geometry:")
        print(f"   Pool center: {geometry.pool_center}")
        print(f"   Pool radius: {geometry.pool_radius:.1f}")
        print(f"   Platform: {geometry.platform_center}")
        print(f"   Platform radius: {geometry.platform_radius:.1f}")
        
        analyzer = TrialAnalyzer(geometry, params)
        
        # Analyze each trial with debug output
        for trial in experiment.trials:
            analyze_trial_debug(trial, analyzer)
        
        print(f"\n{'='*80}")
        print("DEBUG COMPLETE")
        print(f"{'='*80}\n")
        
    except Exception as e:
        logger.exception("Error during debug")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
