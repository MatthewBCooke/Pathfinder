# Heatmap and AutoParameters Extraction Summary

## Date: 2026-02-07

## Objective
Extract and split mixed analysis+GUI functions from `SearchStrategyAnalysis/Pathfinder.py` into pure analysis functions in `pathfinder/analysis.py`.

---

## ✅ Completed Extractions

### 1. `aggregate_heatmap_data()` - Heatmap Analysis Function

**Source:** `Pathfinder.py` lines 1557-1689 (heatmap() method)

**Location:** `/tmp/Pathfinder/pathfinder/analysis.py`

**What it does:**
- Filters trials by day and trial number ranges
- Collects x, y position coordinates from matching trials
- Applies Gaussian smoothing (scipy.ndimage.gaussian_filter)
- Computes spatial extent and 2D histogram
- Returns `HeatmapData` object (pure data, no plotting)

**Removed GUI/Matplotlib code:**
- ❌ `plt.figure()`, `plt.hexbin()`, `plt.colorbar()`, `plt.savefig()`, `plt.show()`
- ❌ `theStatus.set()`, `self.updateTasks()`
- ❌ GUI StringVar references (`dayValStringVar`, `trialValStringVar`, etc.)

**Kept analysis logic:**
- ✅ Trial filtering (day/trial ranges)
- ✅ Data collection from experiment trials
- ✅ Gaussian smoothing (`sp.filters.gaussian_filter`)
- ✅ 2D histogram creation (`np.histogram2d`)
- ✅ Spatial extent tracking

**Function signature:**
```python
def aggregate_heatmap_data(
    experiment,  # Experiment object (iterable of trials)
    filters: Dict[str, Any],  # {'day_filter': str, 'trial_filter': str}
    gridsize: int = 50,
    gaussian_sigma: float = 2.0
) -> HeatmapData:
```

**Returns:** `HeatmapData` dataclass with:
- `x_smoothed`, `y_smoothed`: Gaussian-filtered numpy arrays
- `x_raw`, `y_raw`: Original coordinate lists
- `extent`: (xMin, xMax, yMin, yMax) tuple
- `gridsize`: Grid size for visualization
- `histogram`, `xedges`, `yedges`: 2D histogram data

---

### 2. `calculate_auto_parameters()` - Automatic Parameter Estimation

**Source:** `Pathfinder.py` lines 1732-1935 (getAutoLocations() method)

**Location:** `/tmp/Pathfinder/pathfinder/analysis.py`

**What it does:**
- Analyzes trial trajectories to automatically estimate:
  - Maze center position (midpoint of spatial extent)
  - Platform/goal position (average end position within time limit)
  - Maze diameter (full spatial extent)
  - Platform diameter (estimated from position variance)

**Removed GUI code:**
- ❌ `messagebox.showwarning()` - GUI error dialogs
- ❌ `theStatus.set()` - Status bar updates
- ❌ `self.updateTasks()` - GUI refresh
- ❌ Direct GUI variable references (goalPosVar, mazeCentreVar, etc.)

**Kept analysis logic:**
- ✅ Spatial extent tracking (min/max X/Y)
- ✅ Platform position estimation (average of last positions)
- ✅ Maze center calculation (midpoint of extent)
- ✅ Diameter calculations
- ✅ Time-based filtering (maxLengthOfTrial)

**Function signature:**
```python
def calculate_auto_parameters(
    experiment,  # Experiment object (iterable of trials)
    max_trial_length: float = 50.0,
    manual_goal: Optional[Tuple[float, float]] = None,
    manual_maze_centre: Optional[Tuple[float, float]] = None,
    manual_maze_diameter: Optional[float] = None,
    manual_goal_diameter: Optional[float] = None
) -> AutoParameters:
```

**Returns:** `AutoParameters` dataclass with:
- `maze_centre_x`, `maze_centre_y`: Estimated maze center
- `goal_x`, `goal_y`: Estimated platform/goal position
- `maze_diameter`, `maze_radius`: Estimated maze size
- `goal_diameter`: Estimated platform size
- `trial_count`: Number of trials analyzed
- `warnings`: List of calculation warnings (replaces GUI messageboxes)

---

## 📦 New Type Definitions

Added to `/tmp/Pathfinder/pathfinder/types.py`:

### `HeatmapData` dataclass
Pure data structure for heatmap visualization - no matplotlib dependencies.

### `AutoParameters` dataclass
Container for automatically calculated experimental parameters.

---

## 🔧 Dependencies

### Added imports to `analysis.py`:
```python
import scipy.ndimage as sp  # For Gaussian filtering
from typing import Dict, Any  # For filters parameter
from pathfinder.types import HeatmapData, AutoParameters
```

### Added imports to `types.py`:
```python
from typing import Tuple  # For coordinate tuples
import numpy as np  # For array types
```

---

## ✨ Benefits

1. **Separation of Concerns**
   - Analysis logic is now testable without GUI
   - Can be used in headless/batch processing
   - No tkinter/matplotlib imports required for analysis

2. **Type Safety**
   - Full type hints on all new functions
   - Dataclasses with documented fields
   - Clear input/output contracts

3. **Maintainability**
   - Pure functions with no side effects
   - Single Responsibility Principle
   - Easier to test and debug

4. **Reusability**
   - Analysis functions can be called from CLI tools
   - Can be used in notebooks/scripts
   - No GUI coupling

---

## 🔄 Next Steps (Future Work)

The visualization code remains in `Pathfinder.py`:
- The GUI `heatmap()` method should be refactored to:
  1. Call `aggregate_heatmap_data()` to get data
  2. Use the returned `HeatmapData` for plotting
  
- The GUI `getAutoLocations()` method should be refactored to:
  1. Call `calculate_auto_parameters()` to get estimates
  2. Handle warnings/errors in GUI layer
  3. Update GUI fields with results

---

## 📝 Usage Examples

### Example 1: Generate heatmap data
```python
from pathfinder.analysis import aggregate_heatmap_data

# Define filters
filters = {
    'day_filter': 'All',      # or '1-3' for range, or '2' for single day
    'trial_filter': '1-5'     # or 'All', or '3' for single trial
}

# Aggregate data (no GUI required!)
heatmap_data = aggregate_heatmap_data(
    experiment=my_experiment,
    filters=filters,
    gridsize=50,
    gaussian_sigma=2.0
)

# Now pass to visualization layer
# plot_heatmap(heatmap_data)  # GUI code stays in Pathfinder.py
```

### Example 2: Auto-calculate parameters
```python
from pathfinder.analysis import calculate_auto_parameters

# Fully automatic
params = calculate_auto_parameters(experiment)
print(f"Goal: ({params.goal_x}, {params.goal_y})")
print(f"Maze centre: ({params.maze_centre_x}, {params.maze_centre_y})")

# Partial manual override
params = calculate_auto_parameters(
    experiment,
    manual_goal=(100.0, 150.0),  # Manual goal position
    # Other params auto-calculated
)

# Check warnings (replaces GUI messageboxes)
if params.warnings:
    for warning in params.warnings:
        print(f"WARNING: {warning}")
```

---

## ✅ Validation Checklist

- [x] No matplotlib imports in extracted functions
- [x] No GUI code (messagebox, status updates, updateTasks)
- [x] Type hints added to all parameters and returns
- [x] Docstrings with clear descriptions
- [x] Analysis logic preserved exactly
- [x] Dataclasses created for return types
- [x] Error handling converted to exceptions (not GUI dialogs)
- [x] Warnings collected in list (not messageboxes)

---

## 🎯 Summary

Successfully extracted **2 major analysis functions** from GUI code:

1. ✅ `aggregate_heatmap_data()` - Heatmap data aggregation (176 lines → pure analysis)
2. ✅ `calculate_auto_parameters()` - Automatic parameter estimation (204 lines → pure analysis)

**Total lines of analysis code separated from GUI:** ~380 lines

**Result:** Clean, testable, reusable analysis functions with no GUI dependencies.
