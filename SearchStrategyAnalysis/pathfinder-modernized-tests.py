"""
Pytest test suite for modernized Pathfinder.
Demonstrates testing strategy for refactored codebase.
"""

import pytest
from datetime import datetime
from pathfinder_modernized_models import (
    Datapoint, Parameters, Trial, Experiment, SearchStrategy, AnalysisResult
)
from pathfinder_modernized_analysis import StrategyAnalyzer


class TestDatapoint:
    """Tests for Datapoint model validation"""
    
    def test_valid_datapoint(self):
        """Should create valid datapoint"""
        dp = Datapoint(x=100, y=150, time=1.5)
        assert dp.x == 100
        assert dp.y == 150
        assert dp.time == 1.5
    
    def test_negative_coordinates_rejected(self):
        """Should reject negative coordinates"""
        with pytest.raises(ValueError):
            Datapoint(x=-10, y=100, time=1.0)
    
    def test_negative_time_rejected(self):
        """Should reject negative time"""
        with pytest.raises(ValueError):
            Datapoint(x=100, y=100, time=-1.0)


class TestParameters:
    """Tests for Parameters model"""
    
    def test_default_parameters(self):
        """Should create with default values"""
        params = Parameters(name="Test")
        assert params.ipe_max_val == 125
        assert params.scale_values is True
    
    def test_custom_parameters(self):
        """Should accept custom parameter values"""
        params = Parameters(
            name="Custom",
            ipe_max_val=150,
            scale_values=False
        )
        assert params.ipe_max_val == 150
        assert params.scale_values is False


@pytest.fixture
def sample_trajectory() -> list[Datapoint]:
    """Create a sample trajectory for testing"""
    return [
        Datapoint(x=100, y=100, time=0.0),
        Datapoint(x=110, y=105, time=0.5),
        Datapoint(x=120, y=110, time=1.0),
        Datapoint(x=130, y=115, time=1.5),
    ]


@pytest.fixture
def sample_trial(sample_trajectory) -> Trial:
    """Create a sample trial for testing"""
    return Trial(
        trial_id="trial_001",
        trial_number=1,
        day=1,
        trajectory=sample_trajectory,
        platform_position=(200, 200),
        platform_diameter=20,
        pool_center=(150, 150),
        pool_diameter=300,
        search_strategy=SearchStrategy.DIRECT_SWIM,
        escape_latency=10.5,
        path_length=50.0,
        swim_speed=4.76
    )


class TestTrial:
    """Tests for Trial model"""
    
    def test_trial_creation(self, sample_trial):
        """Should create valid trial"""
        assert sample_trial.trial_id == "trial_001"
        assert sample_trial.trial_number == 1
        assert len(sample_trial.trajectory) == 4
    
    def test_negative_metrics_rejected(self):
        """Should reject negative metrics"""
        with pytest.raises(ValueError):
            Trial(
                trial_id="test",
                trial_number=1,
                day=1,
                trajectory=[],
                platform_position=(0, 0),
                platform_diameter=10,
                pool_center=(0, 0),
                pool_diameter=100,
                escape_latency=-1.0  # Invalid
            )
    
    def test_trajectory_access(self, sample_trial):
        """Should access trajectory data"""
        assert sample_trial.trajectory[0].time == 0.0
        assert sample_trial.trajectory[-1].time == 1.5


class TestExperiment:
    """Tests for Experiment model"""
    
    @pytest.fixture
    def sample_experiment(self, sample_trial) -> Experiment:
        """Create a sample experiment"""
        return Experiment(
            experiment_id="exp_001",
            experiment_name="Test Experiment",
            parameters=Parameters(name="Test"),
            trials=[sample_trial],
            tracking_software="Ethovision"
        )
    
    def test_experiment_creation(self, sample_experiment):
        """Should create valid experiment"""
        assert sample_experiment.experiment_id == "exp_001"
        assert len(sample_experiment.trials) == 1
    
    def test_get_trials_by_day(self, sample_experiment):
        """Should filter trials by day"""
        trials = sample_experiment.get_trials_by_day(1)
        assert len(trials) == 1
        assert trials[0].trial_id == "trial_001"
    
    def test_get_trials_by_strategy(self, sample_experiment):
        """Should filter trials by strategy"""
        trials = sample_experiment.get_trials_by_strategy(SearchStrategy.DIRECT_SWIM)
        assert len(trials) == 1
    
    def test_average_escape_latency(self, sample_experiment):
        """Should calculate average escape latency"""
        avg = sample_experiment.average_escape_latency()
        assert avg == 10.5


class TestStrategyAnalyzer:
    """Tests for core analysis engine"""
    
    @pytest.fixture
    def analyzer(self) -> StrategyAnalyzer:
        """Create analyzer with default parameters"""
        return StrategyAnalyzer(Parameters(name="Test"))
    
    def test_metric_calculation(self, analyzer, sample_trial):
        """Should calculate trajectory metrics"""
        metrics = analyzer._calculate_metrics(sample_trial)
        assert 'total_distance' in metrics
        assert 'avg_speed' in metrics
        assert 'wall_proximity' in metrics
        assert metrics['total_distance'] > 0
    
    def test_strategy_detection(self, analyzer, sample_trial):
        """Should detect search strategy"""
        strategy, confidence = analyzer.analyze_trial(sample_trial)
        assert strategy in SearchStrategy
        assert 0 <= confidence <= 1
    
    def test_empty_trajectory_handling(self, analyzer):
        """Should handle empty trajectory gracefully"""
        empty_trial = Trial(
            trial_id="empty",
            trial_number=1,
            day=1,
            trajectory=[],
            platform_position=(0, 0),
            platform_diameter=10,
            pool_center=(0, 0),
            pool_diameter=100
        )
        strategy, confidence = analyzer.analyze_trial(empty_trial)
        assert strategy == SearchStrategy.RANDOM_SEARCH
        assert confidence == 0.0


class TestAnalysisResult:
    """Tests for analysis results"""
    
    def test_result_creation(self):
        """Should create valid analysis result"""
        result = AnalysisResult(
            experiment_id="exp_001",
            trial_id="trial_001",
            detected_strategy=SearchStrategy.DIRECT_SWIM,
            confidence=0.85
        )
        assert result.detected_strategy == SearchStrategy.DIRECT_SWIM
        assert result.confidence == 0.85
    
    def test_invalid_confidence(self):
        """Should reject invalid confidence"""
        with pytest.raises(ValueError):
            AnalysisResult(
                experiment_id="exp_001",
                trial_id="trial_001",
                detected_strategy=SearchStrategy.DIRECT_SWIM,
                confidence=1.5  # Invalid: > 1.0
            )


# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_experiment_analysis_workflow(self, sample_trial):
        """Should run complete analysis on experiment"""
        experiment = Experiment(
            experiment_id="exp_001",
            experiment_name="Integration Test",
            parameters=Parameters(name="Test"),
            trials=[sample_trial],
            tracking_software="Ethovision"
        )
        
        analyzer = StrategyAnalyzer(experiment.parameters)
        results = []
        
        for trial in experiment.trials:
            strategy, confidence = analyzer.analyze_trial(trial)
            result = AnalysisResult(
                experiment_id=experiment.experiment_id,
                trial_id=trial.trial_id,
                detected_strategy=strategy,
                confidence=confidence
            )
            results.append(result)
        
        assert len(results) == 1
        assert results[0].detected_strategy in SearchStrategy
