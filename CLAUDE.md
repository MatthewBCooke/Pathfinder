# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Pathfinder** is a Morris Water Maze search strategy analysis tool with a modern PyQt5 GUI. It analyzes rodent navigation trajectories to classify search strategies (Direct Swim, Directed Search, Focal Search, Spatial Indirect, Chaining, Scanning, Thigmotaxis, Random Search).

**Main Branch**: `dev`
**Python Version**: 3.10+
**GUI Framework**: PyQt5 (note: tests use PyQt6 fixtures but runtime uses PyQt5)

## Recent Updates

**v2.1 (2026-02-08)**: Added spatial parameter GUI controls for setting maze geometry (pool center, pool diameter, platform position, platform diameter). These parameters are critical for accurate strategy classification. See `docs/SPATIAL_PARAMETERS_GUIDE.md` for details.

## Quick Start Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (includes pytest, PyQt6 for tests)
pip install -r requirements-dev.txt
```

### Running the Application
```bash
# Run GUI application
python pathfinder_gui.py

# Or using executable mode
./pathfinder_gui.py
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_workers.py -v

# Run with coverage
pytest tests/ --cov=pathfinder --cov=gui --cov-report=html

# Run tests from project root (important for imports)
cd /Users/matthewcooke/Documents/UBC/Pathfinder/Pathfinder\ 2/Pathfinder
pytest tests/
```

### Development Tools
```bash
# Type checking
mypy pathfinder gui

# Code formatting
black pathfinder gui tests

# Linting
flake8 pathfinder gui tests
```

## Architecture

### Three-Layer Design

1. **Analysis Layer** (`pathfinder/`)
   - Pure Python, no GUI dependencies
   - Core domain models with Pydantic validation
   - Strategy detection algorithms
   - File I/O for Ethovision, AnyMaze, Generic CSV formats

2. **GUI Layer** (`gui/`)
   - PyQt5 widgets and UI components
   - Signal/slot connections for user interactions
   - No direct analysis logic

3. **Integration Layer** (`gui/integration.py`)
   - Bridges GUI and analysis layers
   - Manages worker threads for long-running operations
   - Handles state management and error propagation

### Key Principle: Separation of Concerns
The analysis layer (`pathfinder/`) must remain independent of PyQt. This enables:
- Headless/CLI usage of analysis functions
- Easier testing of analysis logic
- Potential future Qt version migrations

## Critical File Locations

### Entry Point
- `pathfinder_gui.py` - Main application entry point, creates QApplication and wires PathfinderIntegration

### Core Analysis
- `pathfinder/analysis/trial_analyzer.py` - Strategy detection engine
- `pathfinder/core/models.py` - Pydantic data models (Trial, Experiment, Parameters, SearchStrategy enum)
- `pathfinder/core/geometry.py` - Maze geometry utilities
- `pathfinder/io/loaders.py` - File format detection and parsing
- `pathfinder/analysis.py` - Legacy analysis functions (calculate_trial_metrics)
- `pathfinder/types.py` - Type definitions (TrialMetrics, AnalysisConfig, StrategyResult)

### GUI Components
- `gui/main_window.py` - Main application window and tab structure
- `gui/integration.py` - Signal/slot wiring and business logic coordination
- `gui/control_panel.py` - Left sidebar (Load File, Run Analysis, Export buttons)
- `gui/results_table.py` - Trial-by-trial results display
- `gui/summary_widget.py` - Experiment-level statistics
- `gui/heatmap_widget.py` - Trajectory visualization
- `gui/workers.py` - Background worker threads (FileLoadWorker, AnalysisWorker, HeatmapWorker)
- `gui/defaults.py` - Default parameter values (35+ thresholds)

### Testing
- `tests/conftest.py` - Pytest fixtures (sample trials, experiments, parameters)
- `tests/test_workers.py` - Worker thread signal emission tests
- `tests/test_dialogs.py` - Dialog functionality tests
- `tests/test_gui_integration.py` - End-to-end GUI integration tests

## Data Flow

### File Loading
1. User clicks "Load Experiment File" → `ControlPanel.load_clicked` signal
2. `Integration.on_load_file()` spawns `FileLoadWorker`
3. Worker calls `pathfinder.io.loaders.load_experiment(file_path, parameters)`
4. Loader detects format (Ethovision/AnyMaze/Generic), parses to `Experiment` object
5. Worker emits `finished(Experiment)` signal
6. Integration stores experiment, applies spatial parameters to all trials, and enables "Run Analysis" button

### Spatial Parameters
1. User sets maze geometry in "Maze Geometry" group (pool center, pool/platform diameter, platform position)
2. User clicks "Apply Geometry" → `ControlPanel.spatial_params_changed` signal with dict
3. `Integration.on_spatial_params_changed(params)` updates `self.spatial_params`
4. `Integration.apply_spatial_parameters_to_trials()` applies to all trials in current experiment
5. Analysis worker uses trial spatial parameters to create `MazeGeometry` for accurate calculations

### Analysis Pipeline
1. User clicks "Run Analysis" → `ControlPanel.analyze_clicked` signal
2. `Integration.run_analysis()` spawns `AnalysisWorker`
3. Worker iterates trials, calls `trial_analyzer.analyze_trial(trial, params)`
4. Analyzer computes 19 metrics via `calculate_trial_metrics()` (IPE, heading error, distance metrics, etc.)
5. Analyzer classifies strategy using hierarchical decision tree (Direct → Directed → Focal → Spatial Indirect → Chaining → Scanning → Thigmotaxis → Random)
6. Worker emits `progress(int, str)` for each trial
7. Worker emits `finished(List[StrategyResult])` on completion
8. Integration populates ResultsTable, SummaryWidget, and HeatmapWidget

### Manual Classification Override
1. User double-clicks trial row → `ResultsTable.manual_classification_requested` signal
2. `Integration.on_manual_classification()` shows strategy selection dialog
3. User selects strategy, Integration updates in-memory results
4. ResultsTable refreshes to show manually classified strategy

## Strategy Detection Algorithm

Located in `pathfinder/analysis/trial_analyzer.py`, the classifier uses a hierarchical decision tree:

1. **Direct Swim**: Low IPE (<125), low heading error (<40°), straight path to platform
2. **Directed Search**: Moderate IPE, high corridor average (>70%), focused near platform
3. **Focal Search**: Search concentrated in platform quadrant, moderate distance metrics
4. **Spatial Indirect**: Some spatial knowledge, indirect approach, moderate coverage
5. **Chaining**: Repeated similar paths from start location, low coverage (<40%)
6. **Scanning**: Systematic pool coverage, multiple quadrants (4), moderate distance
7. **Thigmotaxis**: Wall-hugging, high time in thigmotaxis zones (>70%)
8. **Random Search**: Default fallback, high entropy, no apparent strategy

Metrics are computed in `pathfinder/analysis.py:calculate_trial_metrics()` and include IPE, heading error, distance to platform, corridor average, percent traversed, thigmotaxis counters, entropy.

## Important Constraints

### PyQt Version Mismatch
- **Runtime**: Uses PyQt5 (requirements.txt)
- **Tests**: Use PyQt6 fixtures (requirements-dev.txt, conftest.py imports PyQt6)
- When modifying GUI code, ensure PyQt5 compatibility
- When modifying tests, maintain PyQt6 test fixtures

### Data Validation
All trajectory data undergoes NaN/Inf validation. If you see validation errors, check:
1. `pathfinder/io/loaders.py` - NaN/Inf replacement with 0
2. `gui/integration.py` - Error handling for corrupted data
3. Analysis functions replace invalid values rather than raising exceptions

### Threading Model
Long operations (file loading, analysis, heatmap generation) run in QThreads via worker classes. Workers emit signals to communicate with the main thread. Never call GUI methods from worker threads directly - always use signals.

## Adding New Features

### Adding a New Search Strategy
1. Add enum value to `pathfinder/core/models.py:SearchStrategy`
2. Implement detection logic in `pathfinder/analysis/trial_analyzer.py:_classify_strategy()`
3. Add strategy color to `gui/results_table.py:_get_strategy_color()`
4. Add strategy display name to `gui/summary_widget.py` if needed
5. Update tests in `tests/` to include new strategy

### Adding a New File Format
1. Add enum to `pathfinder/io/loaders.py:SoftwareType`
2. Implement `_load_<format>(file_path, parameters)` function
3. Update `load_experiment()` dispatcher to call new loader
4. Add test data file to `tests/` directory
5. Add test case to `tests/test_gui_integration.py`

### Adding a New Analysis Metric
1. Add field to `pathfinder/types.py:TrialMetrics` dataclass
2. Implement calculation in `pathfinder/analysis.py:calculate_trial_metrics()`
3. If metric influences strategy, update `trial_analyzer.py:_classify_strategy()`
4. Add column to `gui/results_table.py` if displaying in table
5. Add to `gui/summary_widget.py` if aggregating across trials

## Common Pitfalls

1. **Import Errors**: Always run tests from project root, not from `tests/` directory
2. **Signal/Slot Disconnects**: Ensure signals are connected in `integration.py`, not scattered across widgets
3. **Thread Safety**: Never modify GUI widgets from worker threads - use signals
4. **Coordinate Systems**: Some legacy code mixes pixels and cm - check `Parameters.pixels_per_cm` scaling
5. **Empty Trials**: Analysis functions must handle trials with zero datapoints gracefully
6. **Platform Coordinates**: Platform position is in absolute coordinates, not relative to pool center

## File Format Notes

### Ethovision (Excel)
- Required columns: `Trial time`, `X center`, `Y center`
- Optional: `Trial` column for multi-trial files
- Auto-detects based on column headers

### AnyMaze (CSV)
- Required columns: `Time`, `X`, `Y`
- Optional: `Trial` column for multi-trial files
- Auto-detects based on column headers

### Generic CSV
- Auto-detects columns matching: time/t, x/x_pos, y/y_pos (case-insensitive)
- If detection fails, edit `pathfinder/io/loaders.py:_find_column()` to add synonyms

## Logging

Application logs to both console and `pathfinder.log`. Log levels:
- INFO: Normal operations (file loaded, analysis started)
- WARNING: Recoverable issues (NaN values replaced, missing columns)
- ERROR: Failures (file not found, analysis crash)

Configure in `pathfinder_gui.py` logging setup.

## Package Structure

```
pathfinder/
├── core/           # Domain models (Trial, Experiment, Parameters)
├── io/             # File loaders and writers
├── analysis/       # Strategy detection (trial_analyzer.py)
├── analysis.py     # Legacy metric calculations
├── models.py       # Legacy model definitions
├── types.py        # Type definitions (dataclasses, enums)
└── entropy.py      # Entropy calculation

gui/
├── main_window.py      # Main window container
├── integration.py      # Signal/slot wiring (KEY FILE)
├── control_panel.py    # Left sidebar buttons
├── results_table.py    # Trial results display
├── summary_widget.py   # Experiment summary
├── heatmap_widget.py   # Trajectory visualization
├── workers.py          # Background thread workers
├── defaults.py         # Default parameters
└── dialogs.py          # Settings and manual classification dialogs

tests/
├── conftest.py                 # Pytest fixtures
├── test_workers.py             # Worker thread tests
├── test_dialogs.py             # Dialog tests
└── test_gui_integration.py     # E2E integration tests
```

## Performance Considerations

- Analysis is CPU-bound - runs in background thread to avoid GUI freezing
- Heatmap generation can be slow for trials with >10k datapoints - consider downsampling
- Large experiments (>100 trials) may take 30+ seconds to analyze
- File loading is I/O-bound - background thread prevents blocking
- Results table rendering can slow with >500 trials - consider pagination if needed
