# Pathfinder Test Suite

Comprehensive tests for the Pathfinder GUI and analysis engine.

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-qt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_workers.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=pathfinder --cov=gui --cov-report=html
```

## Test Organization

### `conftest.py`
Pytest configuration and fixtures:
- Sample experiment creation
- Mock parameters
- Test data utilities

### `test_workers.py`
Unit tests for background worker threads:
- AnalysisWorker signal emission
- FileLoadWorker file operations
- HeatmapWorker data aggregation
- Error handling and abort mechanisms

### `test_dialogs.py`
Dialog window functionality:
- SettingsDialog parameter updates
- FileImportDialog file selection
- ManualStrategyDialog classification
- ExportDialog format selection

### `test_gui_integration.py`
End-to-end integration tests:
- File loading → Analysis → Display pipeline
- Signal/slot connections
- Results accuracy
- Edge cases (empty data, errors, etc.)

## Test Coverage

Current coverage targets:
- **pathfinder/** (analysis engine): 85%+
- **gui/** (GUI components): 70%+
- **workers.py** (threading): 90%+
- **integration.py** (signal/slots): 75%+

## Example Tests

### Test File Loading
```python
def test_load_experiment():
    exp = Experiment("test")
    assert len(exp) == 0
    
    trial = Trial()
    trial.setname("T1")
    exp.append(trial)
    assert len(exp) == 1
```

### Test Analysis Worker
```python
def test_analysis_worker_signals(qtbot):
    worker = AnalysisWorker(experiment, parameters)
    
    with qtbot.waitSignal(worker.finished):
        worker.start()
    
    assert len(worker.results) > 0
```

### Test Results Display
```python
def test_results_table_loads_data(qtbot):
    widget = ResultsTableWidget()
    widget.load_results(test_results)
    
    assert widget.rowCount() == len(test_results)
```

## Continuous Integration

### Local CI Check
```bash
#!/bin/bash
echo "Running tests..."
pytest tests/ -v || exit 1

echo "Checking coverage..."
pytest tests/ --cov=pathfinder --cov=gui || exit 1

echo "Type checking..."
mypy pathfinder gui

echo "Code style..."
flake8 pathfinder gui tests

echo "✓ All checks passed"
```

### GitHub Actions
See `.github/workflows/test.yml` for automated testing on each commit.

## Troubleshooting

### "ImportError: No module named 'pathfinder'"
Run tests from project root:
```bash
cd /path/to/Pathfinder
pytest tests/
```

### "ModuleNotFoundError: No module named 'PyQt6'"
Install GUI dependencies:
```bash
pip install -r requirements-dev.txt
```

### "assertion error" in worker tests
Worker threads may need time assertions. Use `qtbot.waitSignal()`:
```python
with qtbot.waitSignal(worker.finished, timeout=5000):
    worker.start()
```

### Tests pass locally but fail in CI
- Check Python version (should be 3.8+)
- Ensure all dependencies in requirements.txt
- Use same test command locally and in CI

## Adding New Tests

1. Create test file in `tests/` directory
2. Name it `test_*.py` (pytest discovers automatically)
3. Use fixtures from `conftest.py`
4. Run: `pytest tests/test_yourfile.py -v`

Example template:
```python
import pytest
from pathfinder import Trial, Experiment

class TestMyFeature:
    """Test description."""
    
    @pytest.fixture
    def sample_trial(self):
        """Create test trial."""
        trial = Trial()
        trial.setname("test")
        return trial
    
    def test_something(self, sample_trial):
        """Test specific behavior."""
        assert sample_trial.name == "test"
```

## Performance Tests

For long-running analyses:
```bash
pytest tests/ -v -k "performance" --durations=10
```

## Benchmarking

Profile analysis speed:
```bash
pip install pytest-benchmark
pytest tests/ --benchmark-only
```

## Coverage Reports

Generate HTML coverage report:
```bash
pytest tests/ --cov=pathfinder --cov=gui --cov-report=html
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## CI/CD Integration

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest tests/ --tb=short || exit 1
```

### Pre-push Hook
```bash
#!/bin/bash
pytest tests/ -v || exit 1
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [PyQt6 Testing Guide](https://doc.qt.io/qt-6/qtestlib-manual.html)
