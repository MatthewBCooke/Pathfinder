# Phase 1: Analysis Engine Extraction Plan

## Current State
- **Pathfinder.py** (2563 lines): Monolithic tkinter GUI class with embedded analysis logic
- **appTrial.py** (545 lines): Data structures (Trial, Experiment, Datapoint) + file parsers
- **entropy.py** (pure): Clean entropy calculation function
- **Pathfinder.py root**: File I/O helpers, tkinter setup

## Extraction Strategy

### Target Structure

```
SearchStrategyAnalysis/
├── pathfinder/                    # NEW: Analysis package
│   ├── __init__.py
│   ├── analysis.py               # NEW: Core analysis API
│   ├── models.py                 # MOVE from appTrial.py: Trial, Experiment, Datapoint
│   ├── entropy.py                # EXISTING: Keep as-is
│   ├── io.py                     # MOVE: File parsers (CSV, Excel, etc.)
│   └── types.py                  # NEW: Type definitions
├── ui/                           # NEW: GUI package
│   ├── __init__.py
│   ├── gui.py                    # MOVE: mainClass → PyQt6 version
│   ├── dialogs.py                # MOVE: Dialog windows (column mapping, settings, etc.)
│   └── widgets.py                # NEW: Reusable PyQt6 widgets
├── appTrial.py                   # LEGACY: Keep for backwards compat, import from models.py
├── Pathfinder.py                 # LEGACY: Keep minimal for backwards compat
├── entropy.py                    # EXISTING
└── requirements.txt              # NEW: dependencies

```

### Phase 1 Deliverables (In Order)

#### Step 1: Create `pathfinder/models.py` (Data Structures)
Extract from **appTrial.py**:
- `Datapoint` class (no changes needed)
- `Trial` class (no changes needed)
- `Experiment` class (no changes needed)
- `Parameters` class (no changes needed)

**Why first?** These are pure data structures with no GUI/analysis dependencies. Everything else depends on them.

#### Step 2: Create `pathfinder/io.py` (File Parsers)
Extract from **appTrial.py** + **Pathfinder.py**:
- `find_files(directory, pattern)` → `file_utils.find_files()`
- `saveFileAsExperiment(software, filename, filedirectory)` → `load.load_experiment()`
- `defineOwnSoftware(root, filename)` → `load.define_column_mapping()` (remove tkinter)
- Software-specific parsers:
  - `parse_ethovision(filename) → Experiment`
  - `parse_anymaze(filename) → Experiment`
  - `parse_watermaze(filename) → Experiment`
  - `parse_eztrack(filename) → Experiment`
  - `parse_custom(filename, column_mapping) → Experiment`

**Note:** `defineOwnSoftware` currently uses `tkinter.Toplevel()` — we'll create a non-GUI version that returns column mapping, then let PyQt6 UI handle the dialog.

#### Step 3: Create `pathfinder/analysis.py` (Core Analysis API)
Extract from **Pathfinder.mainClass**:
- `calculate_entropy(trial, goal_x, goal_y) → float`
- `calculate_values(trial, goal_x, goal_y, maze_centre_x, ...) → dict`
- `get_auto_locations(experiment, ...) → dict`
- `generate_heatmap(experiment, strategy_data) → array`
- `angle_between(v1, v2) → float` (utility)
- `unit_vector(vector) → array` (utility)

**Input/Output Examples:**
```python
# calculate_values() signature
result = calculate_values(
    trial=Trial,           # From models.Trial
    goal_x=100.0,
    goal_y=100.0,
    maze_centre_x=128.0,
    maze_centre_y=128.0,
    corridor_width=20.0,
    thigmotaxis_zone_size=10.0,
    ipe_max_val=50.0,
    ...26 more parameters...
)
# Returns: dict with calculated strategy metrics
```

#### Step 4: Create `pathfinder/types.py` (Type Definitions)
Define TypedDicts for complex return types:
```python
StrategyMetrics = TypedDict({
    'direct': float,
    'focal': float,
    'directed': float,
    'indirect': float,
    'scanning': float,
    'thigmotaxis': float,
    'chaining': float,
    'random': float,
})

AutoLocationResult = TypedDict({
    'goal_x': float,
    'goal_y': float,
    'maze_centre_x': float,
    'maze_centre_y': float,
    'confidence': float,
})
```

#### Step 5: Create `pathfinder/__init__.py`
Export the public API:
```python
from pathfinder.models import Trial, Experiment, Datapoint, Parameters
from pathfinder.io import load_experiment, parse_custom, define_column_mapping
from pathfinder.analysis import (
    calculate_entropy,
    calculate_values,
    get_auto_locations,
    generate_heatmap,
)
from pathfinder.entropy import entropy

__all__ = [
    # Models
    'Trial', 'Experiment', 'Datapoint', 'Parameters',
    # I/O
    'load_experiment', 'parse_custom',
    # Analysis
    'calculate_entropy', 'calculate_values', 'get_auto_locations', 'generate_heatmap',
    'entropy',
]
```

#### Step 6: Update `appTrial.py` (Backwards Compatibility)
```python
# appTrial.py becomes a compatibility shim
from pathfinder.models import *
from pathfinder.io import *

# Legacy functions for backwards compat
def saveFileAsExperiment(software, filename, filedirectory):
    return load_experiment(software, filename, filedirectory)
```

#### Step 7: Update `Pathfinder.py` (Minimal Legacy Wrapper)
Keep only:
- tkinter app startup
- Import and call the new API
- WARNING: "Use pathfinder package for new code"

---

## Key Refactoring Notes

### `defineOwnSoftware()` — GUI Removal
**Current:** Uses `tkinter.Toplevel()` to show dialog
**New:** Return pure function `define_column_mapping(file_data: FilePreview) -> dict`
```python
# OLD (in Pathfinder.py):
dialog = defineOwnSoftware(root, filename)  # Creates window

# NEW (in pathfinder/io.py):
preview = FilePreview(filename)  # Just analyze the file
mapping = preview.detect_columns()  # Get column types
# PyQt6 UI calls this and displays its own dialog
```

### `calculateValues()` — Dependency Analysis
Currently calls:
- `unit_vector()` — Move to `analysis.py`
- `angle_between()` — Move to `analysis.py`
- Directly accesses `self.parameters` (GUI state)
- Builds GUI updates into return values

**Refactor:** Extract pure calculation, separate from GUI updates
```python
# BEFORE (mixed):
def calculateValues(self, trial, ...):
    result = {...} # calculations
    self.updateTasks()  # GUI update!
    return result

# AFTER (pure):
def calculate_values(trial, parameters, ...):
    result = {...} # same calculations
    return result  # nothing else
```

### `calculateEntropy()` — Already Simple
Calls `entropy()` from entropy.py — can move to analysis.py as-is.

### `getAutoLocations()` — Image Processing
Depends on `heatmap()` output. Keep together in analysis.py.

### `generateHeatmap()` — Plotting
**Current:** Uses matplotlib + tkinter canvas
**Refactor:** 
- Pure function returns numpy array (no plotting)
- Return data + metadata separately
- Let PyQt6 UI handle visualization

```python
# BEFORE (plotting inside function):
def generateHeatmap(self, trial_list):
    # ... calculations ...
    plt.plot(...)
    return figure

# AFTER (pure):
def generate_heatmap(trial_list) -> HeatmapData:
    return HeatmapData(
        array=...,
        extent=...,
        levels=...,
    )
```

---

## Dependency Graph

```
entropy.py (pure, no deps)
  ↑
analysis.py (depends on entropy, models, numpy/scipy)
  ↑
io.py (depends on models, pandas, numpy)
  ↑
pathfinder/__init__.py (aggregates public API)

models.py (pure, no external deps)
  ↑
(used by: analysis.py, io.py, future UI)

types.py (pure type definitions, no deps)
  ↑
(imported by: analysis.py, io.py)
```

---

## Migration Path for GUI (Phase 2)

Once Phase 1 is done, PyQt6 UI will:
1. Import from `pathfinder` package
2. Call analysis functions with pure data (Trial, Experiment)
3. Handle all GUI concerns (dialogs, plots, threading, events)
4. Never mix GUI logic with analysis

Example:
```python
# PyQt6 GUI code
from pathfinder import load_experiment, calculate_values

class PathfinderMainWindow(QMainWindow):
    def analyze_trial(self, trial_path):
        experiment = load_experiment('custom', trial_path, column_mapping=self.mapping)
        for trial in experiment:
            metrics = calculate_values(trial, self.parameters)
            self.update_results_table(metrics)
```

---

## Estimated Effort

| Step | File | Lines | Effort |
|------|------|-------|--------|
| 1 | models.py (create) | ~300 | 15 min (copy) |
| 2 | io.py (create) | ~800 | 45 min (refactor parsers) |
| 3 | analysis.py (create) | ~1000 | 90 min (extract + clean) |
| 4 | types.py (create) | ~50 | 10 min |
| 5 | __init__.py (create) | ~30 | 5 min |
| 6 | appTrial.py (update) | ~50 | 5 min |
| 7 | Pathfinder.py (update) | minimal | 5 min |
| **TOTAL** | | | **~2.5 hours** |

---

## Testing Strategy

Once Phase 1 is extracted:
```python
# test_analysis.py
from pathfinder import load_experiment, calculate_values

def test_calculate_values():
    exp = load_experiment('ethovision', 'test_data.xlsx')
    trial = exp[0]
    result = calculate_values(trial, parameters=DEFAULT_PARAMS)
    assert result['direct'] > 0
    assert result['entropy'] < 100

def test_load_custom_csv():
    mapping = {'x_col': 0, 'y_col': 1, 't_col': 2}
    exp = load_experiment('custom', 'test.csv', column_mapping=mapping)
    assert len(exp) > 0
```

No GUI needed — pure functions are testable.

---

## Next: Await Subagent Analysis

Subagent will provide:
- Complete list of all methods with line numbers
- Mixed function identification
- Exact parameter lists for core functions
- Import dependency map

Use this document + subagent output as the complete Phase 1 spec.
