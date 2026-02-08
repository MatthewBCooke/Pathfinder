# Strategy Classification Usage Examples

This document shows how to use the new `classify_strategy()` function in various scenarios.

---

## Basic Usage

```python
from pathfinder.types import Parameters
from pathfinder.analysis import calculate_trial_metrics, classify_strategy

# Step 1: Calculate metrics from trial data
metrics = calculate_trial_metrics(
    trial=my_trial,
    goal_x=100.0,
    goal_y=100.0,
    maze_centre_x=0.0,
    maze_centre_y=0.0,
    corridor_width=40.0,
    thigmotaxis_zone_size=15.0,
    chaining_radius=25.0,
    full_thigmo_zone=120.0,
    small_thigmo_zone=135.0,
    maze_radius=150.0,
    day_num=1,
    goal_diam=10.0
)

# Step 2: Classify strategy using default parameters
params = Parameters()
strategy_name, confidence_score = classify_strategy(metrics, params, maze_radius=150.0)

print(f"Strategy: {strategy_name}")
print(f"Confidence: {confidence_score}/3")
```

---

## Using Custom Thresholds

```python
from pathfinder.types import Parameters

# Create custom parameters (stricter thresholds for Direct Path)
custom_params = Parameters(
    name="Strict",
    ipeMaxVal=100,      # More strict (default: 125)
    headingMaxVal=30,   # More strict (default: 40)
    useSemiFocal=True   # Enable Semi-Focal (disabled by default)
)

# Classify with custom thresholds
strategy, score = classify_strategy(metrics, custom_params, maze_radius=150.0)
```

---

## Batch Processing Multiple Trials

```python
from pathfinder.types import Parameters
from pathfinder.analysis import calculate_trial_metrics, classify_strategy

def analyze_experiment(trials, experiment_config):
    """Analyze all trials in an experiment."""
    params = Parameters()  # Use default thresholds
    results = []
    
    for trial in trials:
        # Calculate metrics
        metrics = calculate_trial_metrics(
            trial=trial,
            goal_x=experiment_config['goal_x'],
            goal_y=experiment_config['goal_y'],
            maze_centre_x=experiment_config['maze_centre_x'],
            maze_centre_y=experiment_config['maze_centre_y'],
            corridor_width=experiment_config['corridor_width'],
            thigmotaxis_zone_size=experiment_config['thigmo_zone'],
            chaining_radius=experiment_config['chaining_radius'],
            full_thigmo_zone=experiment_config['full_thigmo_zone'],
            small_thigmo_zone=experiment_config['small_thigmo_zone'],
            maze_radius=experiment_config['maze_radius'],
            day_num=trial.day,
            goal_diam=experiment_config['goal_diam']
        )
        
        # Classify strategy
        strategy, score = classify_strategy(
            metrics, 
            params, 
            maze_radius=experiment_config['maze_radius']
        )
        
        results.append({
            'trial_id': trial.id,
            'day': trial.day,
            'strategy': strategy,
            'confidence': score,
            'ipe': metrics.ipe,
            'latency': metrics.latency,
            'velocity': metrics.velocity
        })
    
    return results
```

---

## Integration with DataFrame

```python
import pandas as pd
from pathfinder.types import Parameters
from pathfinder.analysis import classify_strategy

def add_strategy_classification(df_metrics, params=None, maze_radius=150.0):
    """
    Add strategy classification to a DataFrame of trial metrics.
    
    Args:
        df_metrics: DataFrame with columns matching TrialMetrics fields
        params: Parameters object (None = use defaults)
        maze_radius: Maze radius in cm
        
    Returns:
        DataFrame with added 'strategy' and 'strategy_score' columns
    """
    from pathfinder.types import TrialMetrics
    
    if params is None:
        params = Parameters()
    
    strategies = []
    scores = []
    
    for _, row in df_metrics.iterrows():
        # Convert row to TrialMetrics
        metrics = TrialMetrics(
            corridor_average=row['corridor_average'],
            distance_average=row['distance_average'],
            average_distance_to_swim_path_centroid=row['avg_dist_centroid'],
            average_distance_to_centre=row['avg_dist_centre'],
            average_heading_error=row['avg_heading_error'],
            percent_traversed=row['percent_traversed'],
            quadrant_total=row['quadrant_total'],
            total_distance=row['total_distance'],
            latency=row['latency'],
            full_thigmo_counter=row['full_thigmo_counter'],
            small_thigmo_counter=row['small_thigmo_counter'],
            annulus_counter=row['annulus_counter'],
            sample_count=row['sample_count'],
            trajectory_x=[],  # Not needed for classification
            trajectory_y=[],
            velocity=row['velocity'],
            ipe=row['ipe'],
            average_initial_heading_error=row['initial_heading_error'],
            entropy=row.get('entropy', None)
        )
        
        # Classify
        strategy, score = classify_strategy(metrics, params, maze_radius)
        strategies.append(strategy)
        scores.append(score)
    
    df_metrics['strategy'] = strategies
    df_metrics['strategy_score'] = scores
    return df_metrics
```

---

## Analyzing Strategy Distribution

```python
from collections import Counter
import matplotlib.pyplot as plt

def analyze_strategy_distribution(trials, params=None):
    """Analyze and visualize strategy distribution across trials."""
    if params is None:
        params = Parameters()
    
    strategies = []
    scores = []
    
    for trial in trials:
        metrics = calculate_trial_metrics(trial, ...)  # Your config here
        strategy, score = classify_strategy(metrics, params, maze_radius=150.0)
        strategies.append(strategy)
        scores.append(score)
    
    # Count strategies
    strategy_counts = Counter(strategies)
    
    # Plot distribution
    plt.figure(figsize=(12, 6))
    plt.bar(strategy_counts.keys(), strategy_counts.values())
    plt.xlabel('Strategy Type')
    plt.ylabel('Count')
    plt.title('Search Strategy Distribution')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
    
    # Summary statistics
    print("\nStrategy Distribution:")
    for strategy, count in strategy_counts.most_common():
        pct = 100 * count / len(trials)
        print(f"  {strategy:20s}: {count:3d} ({pct:5.1f}%)")
    
    avg_score = sum(scores) / len(scores)
    print(f"\nAverage Confidence Score: {avg_score:.2f}/3")
```

---

## Filtering by Strategy Quality

```python
def filter_high_quality_trials(trials, min_score=2):
    """
    Filter trials to only include high-quality search strategies.
    
    Args:
        trials: List of trials to analyze
        min_score: Minimum strategy score (0-3)
        
    Returns:
        List of (trial, strategy, score) tuples for high-quality trials
    """
    params = Parameters()
    high_quality = []
    
    for trial in trials:
        metrics = calculate_trial_metrics(trial, ...)
        strategy, score = classify_strategy(metrics, params, maze_radius=150.0)
        
        if score >= min_score:
            high_quality.append((trial, strategy, score))
    
    print(f"Found {len(high_quality)}/{len(trials)} high-quality trials")
    return high_quality

# Example usage
good_trials = filter_high_quality_trials(all_trials, min_score=2)
for trial, strategy, score in good_trials:
    print(f"Trial {trial.id}: {strategy} (score: {score})")
```

---

## Comparing Parameter Sets

```python
def compare_parameter_sets(trials, param_sets):
    """
    Compare how different parameter sets classify the same trials.
    
    Args:
        trials: List of trials to analyze
        param_sets: Dict of {name: Parameters} objects
        
    Returns:
        DataFrame comparing classifications
    """
    import pandas as pd
    
    results = []
    
    for trial in trials:
        metrics = calculate_trial_metrics(trial, ...)
        row = {'trial_id': trial.id}
        
        for param_name, params in param_sets.items():
            strategy, score = classify_strategy(metrics, params, maze_radius=150.0)
            row[f'{param_name}_strategy'] = strategy
            row[f'{param_name}_score'] = score
        
        results.append(row)
    
    return pd.DataFrame(results)

# Example
param_sets = {
    'default': Parameters(),
    'strict': Parameters(ipeMaxVal=100, headingMaxVal=30),
    'lenient': Parameters(ipeMaxVal=150, headingMaxVal=50)
}

comparison = compare_parameter_sets(my_trials, param_sets)
print(comparison)
```

---

## Export to CSV

```python
import csv

def export_strategy_analysis(trials, output_path, params=None):
    """
    Analyze trials and export results to CSV.
    
    Args:
        trials: List of trials to analyze
        output_path: Path to output CSV file
        params: Parameters object (None = use defaults)
    """
    if params is None:
        params = Parameters()
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = [
            'trial_id', 'day', 'animal_id',
            'strategy', 'confidence_score',
            'ipe', 'latency', 'velocity', 'total_distance',
            'percent_traversed', 'avg_heading_error'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for trial in trials:
            metrics = calculate_trial_metrics(trial, ...)
            strategy, score = classify_strategy(metrics, params, maze_radius=150.0)
            
            writer.writerow({
                'trial_id': trial.id,
                'day': trial.day,
                'animal_id': trial.animal_id,
                'strategy': strategy,
                'confidence_score': score,
                'ipe': metrics.ipe,
                'latency': metrics.latency,
                'velocity': metrics.velocity,
                'total_distance': metrics.total_distance,
                'percent_traversed': metrics.percent_traversed,
                'avg_heading_error': metrics.average_heading_error
            })
    
    print(f"Exported {len(trials)} trials to {output_path}")
```

---

## Unit Testing Example

```python
import unittest
from pathfinder.types import TrialMetrics, Parameters
from pathfinder.analysis import classify_strategy

class TestStrategyClassification(unittest.TestCase):
    
    def setUp(self):
        """Create default parameters for tests."""
        self.params = Parameters()
        self.maze_radius = 150.0
    
    def test_direct_path_classification(self):
        """Test that direct path is correctly identified."""
        metrics = TrialMetrics(
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
            trajectory_x=[],
            trajectory_y=[],
            velocity=14.4,
            ipe=80.0,  # Low IPE
            average_initial_heading_error=30.0,
            entropy=None
        )
        
        strategy, score = classify_strategy(metrics, self.params, self.maze_radius)
        self.assertEqual(strategy, "Direct Path")
        self.assertEqual(score, 3)
    
    def test_random_search_classification(self):
        """Test that random search is correctly identified."""
        metrics = TrialMetrics(
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
        
        strategy, score = classify_strategy(metrics, self.params, self.maze_radius)
        self.assertEqual(strategy, "Random Search")
        self.assertEqual(score, 0)

if __name__ == '__main__':
    unittest.main()
```

---

## Best Practices

1. **Always use the same Parameters object** when comparing trials within an experiment
2. **Store the maze_radius** with your experimental configuration
3. **Validate metrics** before classification (check for NaN/Inf values)
4. **Log parameter settings** when exporting results for reproducibility
5. **Consider confidence scores** when analyzing borderline cases
6. **Use batch processing** for large datasets to avoid memory issues

---

## Troubleshooting

### Issue: Getting "Not Recognized" for most trials
- Check that your threshold parameters are appropriate for your setup
- Verify that maze_radius is correct (affects percentage calculations)
- Check that metrics are calculated correctly (especially IPE)

### Issue: Division by zero errors
- Ensure sample_count > 0 in your metrics
- Check that trials aren't empty before processing

### Issue: Inconsistent results vs legacy code
- Verify maze_radius is the same value
- Check that Parameters match the legacy defaultParams
- Ensure metric calculations match legacy implementation

---

## See Also

- `pathfinder/types.py` - Type definitions
- `pathfinder/analysis.py` - Core analysis functions
- `EXTRACTION_SUMMARY.md` - Technical details of the extraction
- `LOGIC_COMPARISON.md` - Proof of logic preservation
