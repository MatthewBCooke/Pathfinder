# Pathfinder Analysis Engine Extraction - Architectural Proposal

**Date:** 2026-02-07  
**Purpose:** Blueprint for extracting pure analysis logic from Pathfinder.py into a clean, testable API module (analysis.py)

---

## 1. PURE ANALYSIS FUNCTIONS (No GUI Dependencies)

These functions contain only computational logic and can be moved directly to `analysis.py`:

### 1.1 Core Analysis Functions

| Function | Line Numbers | Description | Dependencies |
|----------|--------------|-------------|--------------|
| `calculateEntropy()` | 1808-1821 | Calculates entropy for a trial's path | `entropy.py` module (optional), numpy |
| `calculateValues()` | 1823-2211 | **PRIMARY ANALYSIS ENGINE** - Calculates all search strategy metrics | numpy, math, scipy |
| `unit_vector()` | 1789-1794 | Normalizes a vector to unit length | numpy |
| `angle_between()` | 1796-1799 | Calculates angle between two vectors | numpy |

### 1.2 Pure Analysis: calculateValues() Details

**Current Signature (line 1823):**
```python
def calculateValues(self, theTrial, goalX, goalY, mazeCentreX, mazeCentreY, 
                   corridorWidth, thigmotaxisZoneSize, chainingRadius, 
                   fullThigmoZone, smallThigmoZone, mazeradius, dayNum, goalDiam)
```

**What it computes:**
- Initial Path Error (IPE)
- Velocity
- Distance metrics (total, average to goal, to swim path centroid, to maze center)
- Heading error (average, initial)
- Zone occupancy (corridor, annulus, thigmotaxis zones)
- Percent of maze traversed
- Quadrant analysis
- Latency

**Returns:** Tuple of 19 values (line 2208-2210)

**Critical Issues:**
- Uses `theStatus.set()` - **GUI dependency on line 1835**
- Uses `self.calculateEntropy()` - needs refactoring to standalone
- Uses `self.angle_between()` and `self.unit_vector()` - needs refactoring
- Has hardcoded constants: `GRID_CELL_SIZE`, `MAX_CUMULATIVE_DISTANCE`, `MAX_ITERATIONS` (lines 237-239)

---

## 2. GUI-ONLY FUNCTIONS (Stay in mainClass)

These functions are pure GUI and should remain in Pathfinder.py:

| Function | Line Numbers | Purpose |
|----------|--------------|---------|
| `buildGUI()` | 260-584 | Constructs tkinter interface |
| `openFile()` | 669-676 | File dialog for single file |
| `openDir()` | 678-685 | Directory picker dialog |
| `plotPoints()` | 1442-1559 | **Manual categorization popup with plot** |
| `guiHeatmap()` | 1561-1597 | Heatmap parameter input dialog |
| `settings()` | 1190-1364 | Custom parameter settings GUI |
| `saveStrat()` | 1561-1571 | Saves manual strategy selection |
| `otherROI()` | 1183-1201 | ROI definition popup |
| `addROI()` | 1203-1217 | Add ROI entry fields |
| `saveROI()` | 1219-1276 | Validate and save ROI data |
| `updateTasks()` | 1776-1781 | Force GUI refresh |
| `on_enter()` / `on_leave()` | 694-700 | Tooltip hover handlers |
| Window management | Various | maximize, minimize, about, getHelp, tryQuit |

---

## 3. MIXED FUNCTIONS (Need Refactoring)

These functions combine analysis logic with GUI/IO and must be split:

### 3.1 getAutoLocations() - Lines 1823-2003

**Analysis Logic:**
- Calculates maze center from data bounds
- Estimates goal position from early trial endpoints
- Estimates maze diameter
- Estimates goal diameter

**GUI Dependencies:**
- `theStatus.set()` - status bar updates (lines 1973, 1993, 1996, 2001)
- `self.updateTasks()` - GUI refresh (lines 1974, 1994, 1997, 2002)
- `messagebox.showwarning()` - error dialogs (lines 1982-2001)
- `logging` calls (throughout)

**Refactoring Strategy:**
- Extract calculation logic to `calculate_auto_locations(experiment_data, manual_overrides)` → returns dict or raises exceptions
- Let GUI code handle exceptions and display warnings
- Remove status updates from core logic

### 3.2 heatmap() - Lines 1599-1774

**Analysis Logic:**
- Filters trials by day/trial range
- Aggregates position data across trials
- Applies Gaussian filtering
- Calculates 2D histogram

**GUI Dependencies:**
- `theStatus.set()` / `self.updateTasks()` - status updates
- `plt.figure()`, `plt.hexbin()`, `plt.show()` - matplotlib visualization
- `messagebox` for error handling
- File I/O (saves PNG)

**Refactoring Strategy:**
- Extract to `aggregate_heatmap_data(experiment, day_filter, trial_filter, grid_size)` → returns (X, Y, heatmap_array)
- Separate visualization: `render_heatmap(data, output_path)` in GUI or plotting module
- Let caller handle matplotlib rendering

### 3.3 mainCalculate() - Lines 2213-2551

**Analysis Logic:**
- Loads parameters
- Calls `getAutoLocations()`
- Iterates through trials calling `calculateValues()`
- Applies strategy classification rules
- Aggregates strategy counts

**GUI Dependencies:**
- `self.updateTasks()` - GUI refresh (multiple locations)
- `theStatus.set()` - status bar (lines 2225, 2318, 2548)
- `show_message()` - error popup (line 2252)
- `self.plotPoints()` - manual classification dialog (lines 2464, 2495)
- `root.wait_window()` - blocking GUI wait (lines 2473, 2503)
- CSV file writing (throughout)
- `open_file()` - opens CSV in system viewer (line 2542)

**Refactoring Strategy:**
- Extract `analyze_experiment(experiment, params, goal_config)` → returns list of TrialResult objects
- Extract `classify_strategy(trial_metrics, params)` → returns strategy name + score
- GUI code handles CSV writing, plotting, status updates, manual overrides

---

## 4. PROPOSED CLEAN API (analysis.py)

### 4.1 Module Structure

```
analysis.py
│
├─ Data Structures
│  ├─ AnalysisConfig (dataclass)
│  ├─ TrialMetrics (dataclass)
│  └─ StrategyResult (dataclass)
│
├─ Helper Functions
│  ├─ unit_vector(vector)
│  ├─ angle_between(v1, v2)
│  └─ calculate_entropy(x_list, y_list, goal_x, goal_y)
│
├─ Core Analysis
│  ├─ calculate_trial_metrics(trial, config)
│  ├─ calculate_auto_locations(experiment, overrides)
│  └─ aggregate_heatmap_data(experiment, filters)
│
└─ Strategy Classification
   ├─ classify_strategy(metrics, params)
   └─ analyze_experiment(experiment, config, params)
```

### 4.2 Proposed Function Signatures

```python
# --- Data Structures ---

@dataclass
class AnalysisConfig:
    """Configuration for analysis calculations"""
    goal_x: float
    goal_y: float
    goal_diameter: float
    maze_centre_x: float
    maze_centre_y: float
    maze_radius: float
    corridor_width: float  # degrees
    chaining_radius: float
    thigmotaxis_zone_size: float
    full_thigmo_zone: float
    small_thigmo_zone: float
    truncate_at_goal: bool = False
    calculate_entropy_flag: bool = False
    
@dataclass
class TrialMetrics:
    """Results from calculateValues()"""
    corridor_average: float
    distance_average: float
    avg_distance_to_swim_path_centroid: float
    avg_distance_to_centre: float
    avg_heading_error: float
    percent_traversed: float
    quadrant_total: int
    total_distance: float
    latency: float
    full_thigmo_counter: float
    small_thigmo_counter: float
    annulus_counter: float
    sample_count: float
    path_x: List[float]
    path_y: List[float]
    velocity: float
    ipe: float  # Ideal Path Error
    initial_heading_error: float
    entropy: Optional[float] = None

@dataclass
class StrategyResult:
    """Strategy classification result"""
    strategy_type: str
    score: int  # 0-3
    metrics: TrialMetrics
    trial_info: dict  # animal, day, trial number, etc.


# --- Helper Functions ---

def unit_vector(vector: np.ndarray) -> np.ndarray:
    """Returns the unit vector of the input vector"""
    # Current implementation from lines 1789-1794
    
def angle_between(v1: np.ndarray, v2: np.ndarray) -> float:
    """Returns angle in degrees between two vectors"""
    # Current implementation from lines 1796-1799

def calculate_entropy(x_list: List[float], y_list: List[float], 
                     goal_x: float, goal_y: float) -> Optional[float]:
    """
    Calculates path entropy if entropy module is available.
    
    Returns:
        float: Entropy value, or None if entropy module unavailable
    """
    # Current implementation from lines 1808-1821


# --- Core Analysis ---

def calculate_trial_metrics(trial, config: AnalysisConfig) -> TrialMetrics:
    """
    Calculates all search strategy metrics for a single trial.
    
    This is the refactored calculateValues() without GUI dependencies.
    
    Args:
        trial: Trial object with datapointList
        config: AnalysisConfig with all analysis parameters
        
    Returns:
        TrialMetrics containing all calculated values
        
    Raises:
        ValueError: If trial or config parameters are invalid
    """
    # Refactored calculateValues() (lines 1823-2211)
    # Remove: theStatus.set() calls
    # Remove: self references (make standalone)
    # Remove: global useEntropyFlag (use config.calculate_entropy_flag)
    

def calculate_auto_locations(experiment, 
                            manual_overrides: dict) -> dict:
    """
    Auto-calculates maze parameters from experiment data.
    
    Args:
        experiment: Experiment object with trials
        manual_overrides: dict with keys:
            - goal_pos: "x,y" or None
            - goal_diam: float or None
            - maze_centre: "x,y" or None
            - maze_diam: float or None
            
    Returns:
        dict with calculated parameters:
            {
                'maze_centre_x': float,
                'maze_centre_y': float,
                'goal_x': float,
                'goal_y': float,
                'maze_diameter': float,
                'maze_radius': float,
                'goal_diameter': float
            }
            
    Raises:
        ValueError: If insufficient data to calculate parameters
    """
    # Refactored getAutoLocations() (lines 1823-2003)
    # Remove: GUI status updates
    # Remove: messagebox warnings (raise exceptions instead)
    # Remove: logging (let caller handle)


def aggregate_heatmap_data(experiment, 
                           day_filter: Tuple[int, int],
                           trial_filter: Tuple[int, int],
                           grid_size: int = 70,
                           gaussian_sigma: float = 2.0) -> dict:
    """
    Aggregates position data for heatmap generation.
    
    Args:
        experiment: Experiment object
        day_filter: (start_day, end_day) inclusive, use inf for no limit
        trial_filter: (start_trial, end_trial) inclusive
        grid_size: Grid resolution for binning
        gaussian_sigma: Sigma for Gaussian filtering
        
    Returns:
        dict containing:
            {
                'x': List[float],  # filtered X positions
                'y': List[float],  # filtered Y positions
                'x_bounds': (min, max),
                'y_bounds': (min, max),
                'grid_size': int
            }
    """
    # Extracted from heatmap() (lines 1599-1774)
    # Remove: matplotlib plotting
    # Remove: GUI updates
    # Return raw data for visualization elsewhere


# --- Strategy Classification ---

def classify_strategy(metrics: TrialMetrics, 
                     params: Parameters) -> Tuple[str, int]:
    """
    Classifies search strategy based on trial metrics.
    
    Args:
        metrics: TrialMetrics from calculate_trial_metrics()
        params: Parameters object with classification thresholds
        
    Returns:
        (strategy_name, score) where score is 0-3:
            3 = Direct Path
            2 = Focal/Directed/Indirect/Semi-focal Search
            1 = Chaining/Scanning
            0 = Thigmotaxis/Random Search
            
    Note: Returns ("Not Recognized", None) if no strategy matches
    """
    # Extracted from mainCalculate() (lines 2428-2461)
    # Pure classification logic without GUI


def analyze_experiment(experiment, 
                      config: AnalysisConfig,
                      params: Parameters,
                      progress_callback: Optional[Callable] = None) -> List[StrategyResult]:
    """
    Analyzes all trials in an experiment.
    
    Args:
        experiment: Experiment object
        config: AnalysisConfig with analysis parameters
        params: Parameters with classification thresholds
        progress_callback: Optional function(trial_num, total, trial_name)
                          for progress reporting
        
    Returns:
        List[StrategyResult] with one entry per trial
    """
    # Refactored mainCalculate() orchestration logic
    # Remove: CSV writing
    # Remove: GUI plotting
    # Remove: Status bar updates
    # Keep: Pure analysis pipeline
```

---

## 5. DEPENDENCY MAP

### 5.1 External Dependencies (analysis.py)

```
analysis.py
├── Python Standard Library
│   ├── math
│   ├── typing (List, Tuple, Optional, Callable)
│   └── dataclasses
│
├── Third-Party (Required)
│   ├── numpy (vector operations, array math)
│   └── scipy.ndimage (Gaussian filtering for heatmaps)
│
└── Project Internal
    ├── appTrial.py
    │   ├── Trial (data structure)
    │   ├── Experiment (data structure)
    │   ├── Parameters (thresholds)
    │   └── Datapoint (position/time data)
    │
    └── entropy.py (OPTIONAL)
        └── entropy() function
```

### 5.2 Removed Dependencies (from current code)

**Will NOT be needed in analysis.py:**
- ❌ `tkinter` (all variants)
- ❌ `matplotlib.pyplot` (visualization - stays in GUI)
- ❌ `PIL` / `ImageTk` (image handling - GUI only)
- ❌ `csv` (file I/O - let caller handle)
- ❌ `logging` (let caller handle or use exceptions)
- ❌ `pickle` (state persistence - GUI concern)
- ❌ `subprocess`, `webbrowser` (system interaction)
- ❌ `filedialog`, `messagebox` (tkinter dialogs)

### 5.3 Shared Dependencies (used by both)

**Both Pathfinder.py (GUI) and analysis.py will use:**
- ✅ `appTrial.py` (data structures)
- ✅ `numpy`
- ✅ `Parameters` (threshold configurations)

---

## 6. REFACTORING NOTES FOR MIXED FUNCTIONS

### 6.1 calculateValues() → calculate_trial_metrics()

**Changes required:**
1. **Remove `self` references** - make standalone function
2. **Replace `self.angle_between()` with `angle_between()`**
3. **Replace `self.calculateEntropy()` with `calculate_entropy()`**
4. **Remove `theStatus.set()`** on line 1835
5. **Replace global `useEntropyFlag`** with `config.calculate_entropy_flag`
6. **Replace global `truncateFlag`** with `config.truncate_at_goal`
7. **Extract constants** to AnalysisConfig or module-level:
   - `GRID_CELL_SIZE = 10` (line 237)
   - `MAX_CUMULATIVE_DISTANCE = 1000000` (line 238)
   - `MAX_ITERATIONS = 100000` (line 239)
8. **Input validation** - add checks for None/invalid values (lines 1827-1843 are good start, expand)
9. **Return TrialMetrics dataclass** instead of 19-element tuple

### 6.2 getAutoLocations() → calculate_auto_locations()

**Changes required:**
1. **Remove all GUI calls:**
   - `theStatus.set()` → delete
   - `self.updateTasks()` → delete
   - `messagebox.showwarning()` → raise ValueError with message
2. **Remove logging** - raise exceptions instead
3. **Accept structured input** - dict of manual overrides instead of string parsing
4. **Return dict** instead of tuple for clarity
5. **Let caller handle:**
   - String parsing ("Auto" vs "x,y")
   - User notifications
   - Status updates

### 6.3 heatmap() → aggregate_heatmap_data()

**Changes required:**
1. **Split into two functions:**
   - `aggregate_heatmap_data()` - data processing only
   - `render_heatmap()` - visualization (stays in GUI)
2. **Remove from analysis.py:**
   - All matplotlib calls
   - File I/O (saving PNG)
   - `theStatus.set()` / `updateTasks()`
3. **Return raw data** - let caller decide what to do with it
4. **Day/trial filtering** - keep this logic (it's data processing)

### 6.4 mainCalculate() → analyze_experiment()

**Changes required:**
1. **Remove orchestration** that belongs in GUI:
   - CSV file writing (lines 2327-2540)
   - `open_file()` call (line 2542)
   - Status bar updates
2. **Remove user interaction:**
   - `self.plotPoints()` for manual classification
   - `root.wait_window()` blocking
   - Manual strategy override logic
3. **Keep pure pipeline:**
   - Iterate trials
   - Call calculate_trial_metrics()
   - Call classify_strategy()
   - Aggregate results
4. **Add progress callback** - let caller handle progress UI
5. **Return structured data** - List[StrategyResult] instead of writing CSV

---

## 7. MIGRATION STRATEGY

### Phase 1: Create analysis.py skeleton
- Define data structures (AnalysisConfig, TrialMetrics, StrategyResult)
- Copy helper functions (unit_vector, angle_between, calculate_entropy)
- Add tests for helpers

### Phase 2: Extract calculateValues()
- Copy to calculate_trial_metrics()
- Remove GUI dependencies
- Replace globals with config parameters
- Add input validation
- Return TrialMetrics dataclass
- Add unit tests

### Phase 3: Extract classification logic
- Implement classify_strategy()
- Extract strategy decision tree from mainCalculate()
- Add tests for all strategy types

### Phase 4: Extract auto-location logic
- Implement calculate_auto_locations()
- Remove GUI dependencies
- Convert exceptions properly
- Add tests

### Phase 5: Extract heatmap data aggregation
- Implement aggregate_heatmap_data()
- Test filtering and aggregation

### Phase 6: Create orchestration function
- Implement analyze_experiment()
- Integrate all pieces
- Add progress callback support

### Phase 7: Refactor Pathfinder.py
- Import analysis module
- Replace inline logic with API calls
- Handle exceptions and display GUI feedback
- Maintain backward compatibility

---

## 8. TESTING STRATEGY

### Unit Tests Needed (analysis.py)

1. **Helper functions:**
   - `test_unit_vector_normalization()`
   - `test_angle_between_orthogonal()`
   - `test_angle_between_parallel()`

2. **calculate_trial_metrics():**
   - `test_calculate_metrics_simple_trial()`
   - `test_calculate_metrics_with_truncation()`
   - `test_calculate_metrics_invalid_input()`
   - `test_calculate_metrics_empty_trial()`

3. **calculate_auto_locations():**
   - `test_auto_locations_full_auto()`
   - `test_auto_locations_manual_overrides()`
   - `test_auto_locations_insufficient_data()`

4. **classify_strategy():**
   - `test_classify_direct_path()`
   - `test_classify_focal_search()`
   - `test_classify_thigmotaxis()`
   - `test_classify_not_recognized()`

5. **analyze_experiment():**
   - `test_analyze_multi_trial_experiment()`
   - `test_analyze_with_progress_callback()`

---

## 9. BENEFITS OF EXTRACTION

### Testability
- Pure functions can be unit tested without GUI
- Mock Trial/Experiment objects easily
- Test edge cases without user interaction

### Reusability
- Use analysis engine in:
  - Command-line tools
  - Batch processing scripts
  - Web APIs
  - Jupyter notebooks
  - Other GUIs (PyQt, web frontend)

### Maintainability
- Clear separation of concerns
- Analysis logic documented independently
- Easier to modify strategy classification rules
- No accidental GUI breakage when changing analysis

### Performance
- Analysis can run headless (no GUI overhead)
- Parallel processing of multiple experiments
- Integration with HPC/cluster environments

---

## 10. OPEN QUESTIONS / DESIGN DECISIONS

1. **Should Parameters be part of analysis.py or stay external?**
   - Current: Lives in appTrial.py
   - Recommendation: Keep in appTrial.py (it's a data structure, not logic)

2. **How to handle entropy.py optional dependency?**
   - Current: Try/except import with global flag
   - Recommendation: Keep optional, return None if unavailable
   - Add explicit `entropy_available()` function

3. **Should AnalysisConfig merge with Parameters?**
   - AnalysisConfig: Per-trial spatial configuration (goal, maze)
   - Parameters: Classification thresholds
   - Recommendation: Keep separate (different concerns)

4. **Logging in analysis.py?**
   - Current: Extensive logging throughout
   - Recommendation: Minimal logging, use exceptions
   - Let caller decide what to log

5. **Should we keep the 19-element tuple return or use dataclass?**
   - Recommendation: **Use TrialMetrics dataclass**
   - Much clearer, self-documenting
   - Easier to extend without breaking callers

---

## SUMMARY

This extraction will create a clean, testable analysis engine while preserving all existing functionality in the GUI. The key insight is recognizing that most "mixed" functions can be split cleanly:
- **Data processing → analysis.py**
- **User interaction + visualization → Pathfinder.py**

The proposed API provides clear boundaries and makes the analysis logic portable to any environment.
