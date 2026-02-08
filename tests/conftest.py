"""
Pytest fixtures for Pathfinder GUI tests.

Provides mock data, test experiments, and PyQt6 application setup.
"""

import sys
import math
from typing import List
import numpy as np
import pytest

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add pathfinder to path
sys.path.insert(0, '/tmp/Pathfinder')

from pathfinder.models import Trial, Experiment, Datapoint, Parameters
from pathfinder.types import (
    TrialMetrics, StrategyResult, HeatmapData, AnalysisConfig
)


@pytest.fixture(scope='session')
def qapp():
    """
    Create QApplication instance for GUI tests.
    
    Session-scoped to avoid creating multiple QApplication instances.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    # Don't quit the app here to avoid segfaults


@pytest.fixture
def simple_trial() -> Trial:
    """
    Create a simple circular trial for testing.
    
    Returns:
        Trial with 100 datapoints in a circular path
    """
    trial = Trial()
    trial.setname("TestTrial001")
    trial.setanimal("Animal_01")
    trial.settrial(1)
    trial.setday(1)
    
    # Create circular path
    num_points = 100
    radius = 80.0
    center_x, center_y = 100.0, 100.0
    
    for i in range(num_points):
        angle = (i / num_points) * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        time = i * 0.1  # 10 Hz sampling
        
        trial.append(Datapoint(time, x, y))
    
    return trial


@pytest.fixture
def direct_path_trial() -> Trial:
    """
    Create a trial with direct path to platform.
    
    Returns:
        Trial with straight-line trajectory toward platform
    """
    trial = Trial()
    trial.setname("DirectTrial001")
    trial.setanimal("Animal_02")
    trial.settrial(1)
    trial.setday(1)
    
    # Straight line from start to platform
    start_x, start_y = 50.0, 150.0
    platform_x, platform_y = 100.0, 100.0
    num_points = 50
    
    for i in range(num_points):
        t = i / (num_points - 1)
        x = start_x + t * (platform_x - start_x)
        y = start_y + t * (platform_y - start_y)
        time = i * 0.1
        
        trial.append(Datapoint(time, x, y))
    
    return trial


@pytest.fixture
def thigmotaxis_trial() -> Trial:
    """
    Create a trial showing wall-hugging behavior.
    
    Returns:
        Trial circling near the pool edge (thigmotaxis)
    """
    trial = Trial()
    trial.setname("ThigmoTrial001")
    trial.setanimal("Animal_03")
    trial.settrial(1)
    trial.setday(1)
    
    # Circle near the wall
    num_points = 200
    radius = 95.0  # Close to edge (pool radius ~100)
    center_x, center_y = 100.0, 100.0
    
    for i in range(num_points):
        angle = (i / num_points) * 4 * math.pi  # Two full circles
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        time = i * 0.1
        
        trial.append(Datapoint(time, x, y))
    
    return trial


@pytest.fixture
def empty_trial() -> Trial:
    """
    Create an empty trial (edge case).
    
    Returns:
        Trial with no datapoints
    """
    trial = Trial()
    trial.setname("EmptyTrial")
    trial.setanimal("Animal_Empty")
    trial.settrial(1)
    trial.setday(1)
    return trial


@pytest.fixture
def corrupted_trial() -> Trial:
    """
    Create a trial marked as corrupted.
    
    Returns:
        Trial with corrupted data flag set
    """
    trial = Trial()
    trial.setname("CorruptedTrial")
    trial.setanimal("Animal_Corrupt")
    trial.settrial(1)
    trial.setday(1)
    trial.markDataAsCorrupted()
    
    # Add some invalid data
    trial.append(Datapoint(0.0, float('nan'), float('nan')))
    trial.append(Datapoint(0.1, float('inf'), 100.0))
    
    return trial


@pytest.fixture
def test_experiment(simple_trial, direct_path_trial, thigmotaxis_trial) -> Experiment:
    """
    Create a test experiment with multiple trials.
    
    Returns:
        Experiment containing 3 different trial types
    """
    experiment = Experiment("TestExperiment")
    experiment.setHasAnimalNames(True)
    experiment.setHasTrialNames(True)
    experiment.setHasDateInfo(False)
    
    experiment.append(simple_trial)
    experiment.append(direct_path_trial)
    experiment.append(thigmotaxis_trial)
    
    return experiment


@pytest.fixture
def empty_experiment() -> Experiment:
    """
    Create an empty experiment (edge case).
    
    Returns:
        Experiment with no trials
    """
    return Experiment("EmptyExperiment")


@pytest.fixture
def default_parameters() -> Parameters:
    """
    Create default analysis parameters.
    
    Returns:
        Parameters object with default thresholds
    """
    return Parameters()


@pytest.fixture
def custom_parameters() -> Parameters:
    """
    Create custom analysis parameters for testing.
    
    Returns:
        Parameters object with modified thresholds
    """
    params = Parameters()
    params.name = "Custom Test Parameters"
    params.ipeMaxVal = 100.0
    params.headingMaxVal = 30.0
    params.useSemiFocal = True
    return params


@pytest.fixture
def sample_trial_metrics() -> TrialMetrics:
    """
    Create sample trial metrics for testing.
    
    Returns:
        TrialMetrics object with realistic values
    """
    return TrialMetrics(
        corridor_average=75.5,
        average_heading_error=25.3,
        average_initial_heading_error=35.2,
        distance_average=45.8,
        average_distance_to_swim_path_centroid=22.1,
        average_distance_to_centre=55.0,
        percent_traversed=15.2,
        quadrant_total=3,
        total_distance=450.5,
        latency=25.3,
        velocity=18.5,
        full_thigmo_counter=10.0,
        small_thigmo_counter=25.0,
        annulus_counter=40.0,
        sample_count=253.0,
        ipe=145.8,
        entropy=2.35,
        trajectory_x=[100.0, 105.0, 110.0],
        trajectory_y=[100.0, 102.0, 105.0]
    )


@pytest.fixture
def sample_strategy_results() -> List[StrategyResult]:
    """
    Create sample strategy results for testing.
    
    Returns:
        List of StrategyResult objects with different strategies
    """
    return [
        StrategyResult(
            trial_name="Trial_01",
            animal_id="Animal_01",
            strategy="Direct",
            score=3,
            entropy=1.85,
            ipe=95.2,
            distance=280.5,
            velocity=22.3,
            latency=12.5
        ),
        StrategyResult(
            trial_name="Trial_02",
            animal_id="Animal_01",
            strategy="Focal",
            score=2,
            entropy=2.15,
            ipe=145.8,
            distance=380.2,
            velocity=19.1,
            latency=19.9
        ),
        StrategyResult(
            trial_name="Trial_03",
            animal_id="Animal_02",
            strategy="Random",
            score=0,
            entropy=3.45,
            ipe=450.3,
            distance=850.7,
            velocity=17.5,
            latency=48.6
        ),
        StrategyResult(
            trial_name="Trial_04",
            animal_id="Animal_02",
            strategy="Thigmotaxis",
            score=0,
            entropy=2.85,
            ipe=380.1,
            distance=920.4,
            velocity=15.3,
            latency=60.1
        ),
    ]


@pytest.fixture
def sample_heatmap_data() -> HeatmapData:
    """
    Create sample heatmap data for testing.
    
    Returns:
        HeatmapData object with synthetic heatmap array
    """
    # Create a Gaussian-like heatmap centered at (25, 25)
    size = 50
    x, y = np.meshgrid(np.arange(size), np.arange(size))
    center_x, center_y = 25, 25
    sigma = 5.0
    
    data = np.exp(-((x - center_x)**2 + (y - center_y)**2) / (2 * sigma**2))
    
    return HeatmapData(
        data=data,
        x_smoothed=np.linspace(0, 200, size),
        y_smoothed=np.linspace(0, 200, size),
        x_raw=[100.0] * 100,
        y_raw=[100.0] * 100,
        extent=(0, 200, 0, 200),
        gridsize=50
    )


@pytest.fixture
def analysis_config() -> AnalysisConfig:
    """
    Create default analysis configuration.
    
    Returns:
        AnalysisConfig object with default settings
    """
    return AnalysisConfig(
        grid_cell_size=10.0,
        max_iterations=100000,
        max_cumulative_distance=1000000.0,
        use_entropy=True,
        truncate_at_platform=False
    )


# Helper functions for tests

def wait_for_signal(signal, timeout=1000):
    """
    Wait for a Qt signal to be emitted.
    
    Args:
        signal: PyQt signal to wait for
        timeout: Maximum wait time in milliseconds
        
    Returns:
        True if signal was emitted, False if timeout
    """
    from PyQt6.QtCore import QEventLoop, QTimer
    
    loop = QEventLoop()
    signal.connect(loop.quit)
    
    QTimer.singleShot(timeout, loop.quit)
    loop.exec()
    
    return True


def click_button(button):
    """
    Simulate clicking a QPushButton.
    
    Args:
        button: QPushButton to click
    """
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)


def set_combo_box_value(combo, text):
    """
    Set QComboBox to specific text value.
    
    Args:
        combo: QComboBox widget
        text: Text value to select
    """
    index = combo.findText(text)
    if index >= 0:
        combo.setCurrentIndex(index)
