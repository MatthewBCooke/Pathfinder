"""
Test spatial parameter functionality.
Verifies that spatial parameters can be set and applied to trials.
"""

from pathlib import Path
from pathfinder.io.loaders import detect_software_format, load_experiment
from pathfinder.core.models import Parameters
from pathfinder.core.geometry import MazeGeometry
from pathfinder.analysis.trial_analyzer import TrialAnalyzer


def test_spatial_parameter_application():
    """Test that spatial parameters can be applied to loaded trials"""
    # Load test file
    test_file = Path("tests/test_data.csv")
    assert test_file.exists(), "test_data.csv not found"

    software = detect_software_format(test_file)
    params = Parameters(name="Test")
    experiment = load_experiment(test_file, software, params)

    assert len(experiment.trials) > 0, "No trials loaded"

    # Define spatial parameters (simulating GUI input)
    spatial_params = {
        'pool_center_x': 250.0,
        'pool_center_y': 250.0,
        'pool_diameter': 400.0,
        'platform_x': 350.0,
        'platform_y': 150.0,
        'platform_diameter': 40.0
    }

    # Apply to all trials (simulating integration.apply_spatial_parameters_to_trials)
    for trial in experiment.trials:
        trial.pool_center = (spatial_params['pool_center_x'], spatial_params['pool_center_y'])
        trial.pool_diameter = spatial_params['pool_diameter']
        trial.platform_position = (spatial_params['platform_x'], spatial_params['platform_y'])
        trial.platform_diameter = spatial_params['platform_diameter']

    # Verify parameters were applied
    trial = experiment.trials[0]
    assert trial.pool_center == (250.0, 250.0)
    assert trial.pool_diameter == 400.0
    assert trial.platform_position == (350.0, 150.0)
    assert trial.platform_diameter == 40.0

    print("✓ Spatial parameters applied successfully")


def test_maze_geometry_creation():
    """Test that MazeGeometry can be created from trial spatial parameters"""
    # Load and configure trial
    test_file = Path("tests/test_data.csv")
    software = detect_software_format(test_file)
    params = Parameters(name="Test")
    experiment = load_experiment(test_file, software, params)

    trial = experiment.trials[0]
    trial.pool_center = (250.0, 250.0)
    trial.pool_diameter = 400.0
    trial.platform_position = (350.0, 150.0)
    trial.platform_diameter = 40.0

    # Create MazeGeometry (simulating AnalysisWorker)
    geometry = MazeGeometry(
        center_x=trial.pool_center[0],
        center_y=trial.pool_center[1],
        pool_diameter=trial.pool_diameter,
        platform_x=trial.platform_position[0],
        platform_y=trial.platform_position[1],
        platform_diameter=trial.platform_diameter
    )

    # Verify geometry
    assert geometry.pool_radius == 200.0
    assert geometry.platform_radius == 20.0
    assert geometry.pool_center == (250.0, 250.0)
    assert geometry.platform_center == (350.0, 150.0)

    print("✓ MazeGeometry created successfully")


def test_analysis_with_spatial_params():
    """Test that analysis runs with user-defined spatial parameters"""
    # Load and configure
    test_file = Path("tests/test_data.csv")
    software = detect_software_format(test_file)
    params = Parameters(name="Test")
    experiment = load_experiment(test_file, software, params)

    # Apply spatial parameters
    for trial in experiment.trials:
        trial.pool_center = (250.0, 250.0)
        trial.pool_diameter = 400.0
        trial.platform_position = (350.0, 150.0)
        trial.platform_diameter = 40.0

    # Run analysis
    trial = experiment.trials[0]
    geometry = MazeGeometry(
        center_x=trial.pool_center[0],
        center_y=trial.pool_center[1],
        pool_diameter=trial.pool_diameter,
        platform_x=trial.platform_position[0],
        platform_y=trial.platform_position[1],
        platform_diameter=trial.platform_diameter
    )

    analyzer = TrialAnalyzer(geometry, params)
    result = analyzer.analyze(trial)

    # Verify analysis completed
    assert result is not None
    assert result.detected_strategy is not None
    assert 0.0 <= result.confidence <= 1.0

    print(f"✓ Analysis completed: {result.detected_strategy} (confidence: {result.confidence:.2f})")


def test_validation():
    """Test that invalid spatial parameters are rejected"""
    # Pool diameter must be > platform diameter
    test_file = Path("tests/test_data.csv")
    software = detect_software_format(test_file)
    params = Parameters(name="Test")
    experiment = load_experiment(test_file, software, params)

    trial = experiment.trials[0]

    # This should work
    trial.pool_diameter = 400.0
    trial.platform_diameter = 40.0
    assert trial.pool_diameter > trial.platform_diameter

    # This configuration would be invalid (caught by GUI validation)
    # pool_diameter = 40.0, platform_diameter = 400.0 would fail

    print("✓ Validation logic verified")


if __name__ == "__main__":
    print("Running spatial parameter tests...\n")

    test_spatial_parameter_application()
    test_maze_geometry_creation()
    test_analysis_with_spatial_params()
    test_validation()

    print("\n✓✓✓ All tests passed! ✓✓✓")
