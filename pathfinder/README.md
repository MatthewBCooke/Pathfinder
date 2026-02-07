# Pathfinder Analysis Module

Clean, testable analysis functions for Morris Water Maze search strategy calculation.

## Quick Start

```python
from pathfinder.analysis import calculate_trial_metrics
from pathfinder.types import TrialMetrics, AnalysisConfig

# Configure analysis (optional - uses defaults if omitted)
config = AnalysisConfig(
    grid_cell_size=10.0,
    use_entropy=True,
    truncate_at_platform=False
)

# Calculate metrics for a trial
metrics: TrialMetrics = calculate_trial_metrics(
    trial=my_trial,
    goal_x=150.0,
    goal_y=150.0,
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

# Access metrics (type-safe)
print(f"Escape Latency: {metrics.latency:.2f} seconds")
print(f"Path Length: {metrics.total_distance:.2f}")
print(f"Average Speed: {metrics.velocity:.2f}")
print(f"IPE (Ideal Path Error): {metrics.ipe:.2f}")
print(f"Heading Error: {metrics.average_heading_error:.2f}°")
print(f"Percent Traversed: {metrics.percent_traversed:.1f}%")
```

## Features

✅ **Pure Functions** - No GUI dependencies, no hidden state  
✅ **Type-Safe** - Full type hints with dataclass returns  
✅ **Documented** - Comprehensive docstrings  
✅ **Tested** - Unit test suite included  
✅ **Backward Compatible** - Supports legacy datapoint formats  
✅ **Validated** - Input validation and error handling  

## The 19 Metrics

`TrialMetrics` contains:

1. **corridor_average** - Time spent in corridor toward platform
2. **distance_average** - Average distance from platform
3. **average_distance_to_swim_path_centroid** - Distance from path centroid
4. **average_distance_to_centre** - Distance from pool center
5. **average_heading_error** - Mean heading error (degrees)
6. **percent_traversed** - Percentage of grid cells visited
7. **quadrant_total** - Number of quadrants entered (1-4)
8. **total_distance** - Total path length
9. **latency** - Escape latency (seconds)
10. **full_thigmo_counter** - Samples in full thigmotaxis zone
11. **small_thigmo_counter** - Samples in small thigmotaxis zone
12. **annulus_counter** - Samples in annulus zone
13. **sample_count** - Number of trajectory samples
14. **trajectory_x** - List of X coordinates
15. **trajectory_y** - List of Y coordinates
16. **velocity** - Average swim speed
17. **ipe** - Ideal Path Error
18. **average_initial_heading_error** - Initial heading error
19. **entropy** - Shannon entropy (optional)

## Dependencies

- **numpy** - Vector operations
- **math** - Basic math functions
- **logging** - Warning messages
- **entropy** (optional) - Entropy calculation from SearchStrategyAnalysis/

## Testing

Run the test suite:

```bash
python3 test_analysis_refactor.py
```

Verify installation:

```bash
./verify_refactoring.sh
```

## Migration from Legacy Code

### Old API (tuple return):
```python
result = self.calculateValues(theTrial, goalX, goalY, ...)
corridorAvg, distAvg, distToSwim, distToCentre, headingErr, \
    pctTraversed, quadTotal, totalDist, latency, fullThigmo, \
    smallThigmo, annulusCount, sampleCount, arrayX, arrayY, \
    velocity, ipe, initHeadingErr, entropy = result
```

### New API (dataclass return):
```python
from pathfinder import calculate_trial_metrics, AnalysisConfig

metrics = calculate_trial_metrics(
    trial=theTrial,
    goal_x=goalX,
    goal_y=goalY,
    maze_centre_x=mazeCentreX,
    maze_centre_y=mazeCentreY,
    corridor_width=corridorWidth,
    thigmotaxis_zone_size=thigmoSize,
    chaining_radius=chainingRadius,
    full_thigmo_zone=fullThigmoZone,
    small_thigmo_zone=smallThigmoZone,
    maze_radius=mazeRadius,
    day_num=dayNum,
    goal_diam=goalDiam,
    config=AnalysisConfig()
)

# Access by name:
latency = metrics.latency
ipe = metrics.ipe
entropy = metrics.entropy
```

## Configuration

Customize analysis behavior with `AnalysisConfig`:

```python
config = AnalysisConfig(
    grid_cell_size=10.0,           # Grid resolution for coverage
    max_iterations=100000,         # Safety limit for ideal path
    max_cumulative_distance=1e6,   # Max distance before breaking
    use_entropy=True,              # Enable entropy calculation
    truncate_at_platform=False     # Stop at platform arrival
)
```

## Files

- **analysis.py** - Main analysis functions
- **types.py** - Type definitions (TrialMetrics, AnalysisConfig)
- **__init__.py** - Package exports

## License

Part of the Pathfinder project (GNU GPL v3+)

## Author

Refactored from original Pathfinder by Matthew Cooke  
Modernization: OpenClaw Subagent (2026-02-07)
