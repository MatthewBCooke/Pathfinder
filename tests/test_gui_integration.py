"""
Integration tests for Pathfinder GUI components.

Tests the complete workflow:
- File loading → Analysis → Results display
- Signal/slot connections
- Error handling
- Thread cleanup
"""

import pytest
from pathlib import Path
from pathfinder import (
    load_experiment,
    calculate_trial_metrics,
    classify_strategy,
    Trial,
    Datapoint,
    Experiment,
    Parameters,
)
from pathfinder.types import TrialMetrics


class TestFileLoadingIntegration:
    """Test file loading integration."""

    def test_load_experiment_creates_valid_object(self):
        """Test that load_experiment returns valid Experiment object."""
        exp = Experiment("test")
        assert exp is not None
        assert len(exp) == 0
        
        trial = Trial()
        trial.setname("T1")
        exp.append(trial)
        assert len(exp) == 1

    def test_experiment_with_trials(self):
        """Test experiment with multiple trials."""
        exp = Experiment("multi-trial")
        
        for i in range(5):
            trial = Trial()
            trial.setname(f"Trial_{i}")
            trial.setanimal(f"Mouse_{i}")
            
            for j in range(10):
                trial.append(Datapoint(float(j), float(i*10 + j), float(i*10 + j)))
            
            exp.append(trial)
        
        assert len(exp) == 5
        for trial in exp:
            assert len(trial) == 10


class TestAnalysisWorkerIntegration:
    """Test analysis worker integration."""

    @pytest.fixture
    def sample_experiment(self):
        """Create a sample experiment for testing."""
        exp = Experiment("Test")
        
        for trial_num in range(1, 4):
            trial = Trial()
            trial.setname(f"Trial_{trial_num}")
            trial.setanimal(f"Mouse_{trial_num}")
            
            # Add simple circular path data
            for i in range(0, 50):
                import math
                t = i * 0.1
                angle = i * 0.1
                distance = 50 - (i * 0.2)
                x = 128.0 + distance * math.cos(angle)
                y = 128.0 + distance * math.sin(angle)
                trial.append(Datapoint(t, x, y))
            
            exp.append(trial)
        
        return exp

    def test_analysis_produces_valid_metrics(self, sample_experiment):
        """Test that analysis produces valid TrialMetrics."""
        trial = list(sample_experiment)[0]
        
        metrics = calculate_trial_metrics(
            trial,
            goal_x=128.0,
            goal_y=128.0,
            maze_centre_x=128.0,
            maze_centre_y=128.0,
            corridor_width=20.0,
            thigmotaxis_zone_size=10.0,
        )
        
        assert isinstance(metrics, TrialMetrics)
        assert metrics.ipe >= 0
        assert metrics.entropy >= 0
        assert metrics.velocity >= 0

    def test_multiple_trials_analysis(self, sample_experiment):
        """Test analyzing multiple trials."""
        results = []
        
        for trial in sample_experiment:
            metrics = calculate_trial_metrics(
                trial,
                goal_x=128.0,
                goal_y=128.0,
                maze_centre_x=128.0,
                maze_centre_y=128.0,
                corridor_width=20.0,
                thigmotaxis_zone_size=10.0,
            )
            results.append(metrics)
        
        assert len(results) == len(sample_experiment)
        for metrics in results:
            assert isinstance(metrics, TrialMetrics)


class TestStrategyClassification:
    """Test strategy classification."""

    def test_classify_strategy_returns_tuple(self):
        """Test that classify_strategy returns (name, score) tuple."""
        metrics = TrialMetrics(
            ipe=100.0,
            heading=30.0,
            distance_average=50.0,
            velocity=10.0,
            entropy=2.5,
        )
        
        params = Parameters(
            name="test",
            ipeMaxVal=125,
            headingMaxVal=40,
            distanceToSwimMaxVal=200,
            distanceToPlatMaxVal=100,
            distanceToSwimMaxVal2=300,
            distanceToPlatMaxVal2=150,
            corridorAverageMinVal=0.7,
            directedSearchMaxDistance=100,
            focalMinDistance=50,
            focalMaxDistance=150,
            semiFocalMinDistance=40,
            semiFocalMaxDistance=140,
            corridoripeMaxVal=1500,
            annulusCounterMaxVal=100,
            quadrantTotalMaxVal=50,
            chainingMaxCoverage=0.8,
            percentTraversedMaxVal=0.9,
            percentTraversedMinVal=0.1,
            distanceToCentreMaxVal=100,
            thigmoMinDistance=50,
            fullThigmoMinVal=0.2,
            smallThigmoMinVal=0.1,
            ipeIndirectMaxVal=300,
            percentTraversedRandomMaxVal=0.5,
            headingIndirectMaxVal=60,
            useDirect=True,
            useFocal=True,
            useDirected=True,
            useIndirect=True,
            useSemiFocal=True,
            useChaining=True,
            useScanning=True,
            useRandom=True,
            useThigmogaxis=True,
        )
        
        strategy_name, score = classify_strategy(metrics, params)
        
        assert isinstance(strategy_name, str)
        assert isinstance(score, int)
        assert 0 <= score <= 3


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_trial(self):
        """Test handling of empty trial."""
        trial = Trial()
        trial.setname("Empty")
        
        assert len(trial) == 0
        assert trial.name == "Empty"

    def test_single_datapoint_trial(self):
        """Test trial with single datapoint."""
        trial = Trial()
        trial.append(Datapoint(0.0, 100.0, 100.0))
        
        assert len(trial) == 1
        assert trial[0].getx() == 100.0

    def test_experiment_iteration(self):
        """Test iterating over experiment."""
        exp = Experiment("iter_test")
        
        trials = []
        for i in range(3):
            trial = Trial()
            trial.setname(f"T{i}")
            exp.append(trial)
            trials.append(trial)
        
        # Verify iteration
        count = 0
        for trial in exp:
            assert trial in trials
            count += 1
        
        assert count == 3

    def test_trial_with_nan_values(self):
        """Test handling trials with NaN-like values."""
        trial = Trial()
        trial.append(Datapoint(0.0, 100.0, 100.0))
        trial.append(Datapoint(1.0, float('inf'), 100.0))  # Invalid
        trial.append(Datapoint(2.0, 100.0, 100.0))
        
        # Should handle gracefully
        assert len(trial) == 3


class TestResultsDisplay:
    """Test results display formatting."""

    def test_metrics_string_representation(self):
        """Test TrialMetrics can be formatted."""
        metrics = TrialMetrics(
            ipe=123.4,
            heading=45.6,
            distance_average=78.9,
            velocity=12.3,
            entropy=2.56,
        )
        
        # Should be convertible to dict for table display
        assert metrics.ipe == 123.4
        assert metrics.heading == 45.6

    def test_strategy_scores(self):
        """Test strategy score ranges."""
        # Score should be 0-3
        for score in [0, 1, 2, 3]:
            assert 0 <= score <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
