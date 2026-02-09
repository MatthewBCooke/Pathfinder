# Row Index Fix for Trial Selection

## Problem Identified

Multiple animals can have the same Day/Trial numbers:
- Animal 1: Day 1, Trial 1
- Animal 2: Day 1, Trial 1
- Animal 3: Day 1, Trial 1

This caused all trials to show the same path when selected, because they had identical Day/Trial identifiers but were different animals.

## Solution: Row-Based Indexing

Changed from using `trial_id` (ambiguous) to using **row index** (unique).

### What Changed

**Row index = position in the results table (0-based internally, 1-based for display)**

This is guaranteed unique and matches exactly what the user sees in the table.

## Implementation Details

### 1. Results Table Signal Change

**Before:**
```python
trial_selected = pyqtSignal(str)  # trial_id
self.trial_selected.emit(trial_id)
```

**After:**
```python
trial_selected = pyqtSignal(int)  # row index
self.trial_selected.emit(row)  # 0-based row index
```

### 2. Integration Layer Update

**Before:**
```python
def on_trial_selected(self, trial_id: str):
    hm.show_trial(trial_id)
```

**After:**
```python
def on_trial_selected(self, row_index: int):
    hm.show_trial_by_index(row_index)
```

### 3. Heatmap Trial Selector

**Before:**
```
Trial 1 (Day 1) - Focal Search
Trial 1 (Day 1) - Direct Swim  ← AMBIGUOUS!
```

**After:**
```
Row 1: Day 1 Trial 1 - Focal Search
Row 2: Day 1 Trial 1 - Direct Swim  ← CLEAR!
Row 3: Day 2 Trial 1 - Chaining
```

The dropdown now shows:
- **Row number** (matches table)
- Day
- Trial number
- Strategy

### 4. Trial Lookup Logic

The heatmap uses row index to find the correct trial:

```python
# Get trial from experiment by row index
target_trial = self._experiment.trials[row_index]

# Handle day filtering:
# If day filter is active, find trial in filtered list
# Otherwise, use row index directly
```

## Key Benefits

✅ **Unique identification** - Row index is always unique
✅ **Visual consistency** - Row 5 in table = Row 5 in heatmap dropdown
✅ **Multi-animal support** - Works with any number of animals/subjects
✅ **No confusion** - Each trial has a distinct identifier

## How It Works Now

### Workflow Example

**Experiment with 3 animals:**
```
Row 1: Day 1 Trial 1 - Animal 1 - Thigmotaxis
Row 2: Day 1 Trial 1 - Animal 2 - Direct Swim
Row 3: Day 1 Trial 1 - Animal 3 - Focal Search
Row 4: Day 2 Trial 1 - Animal 1 - Scanning
...
```

**User clicks Row 2:**
1. Results table emits `trial_selected(1)`  # 0-based
2. Integration receives row index 1
3. Heatmap gets trial from `experiment.trials[1]`
4. Shows Animal 2's path (not Animal 1's!)

### Day Filtering

When day filter is active:
- Dropdown shows only trials from that day
- Internal mapping: filtered_index → original row_index
- Clicking a row still shows correct trial

Example with "Day 1" filter:
```
Row 1: Day 1 Trial 1 - Animal 1
Row 2: Day 1 Trial 1 - Animal 2
Row 3: Day 1 Trial 1 - Animal 3
(Day 2 trials hidden)
```

Clicking Row 2 shows Animal 2's Day 1 Trial 1 path ✓

## Testing

```bash
python3 pathfinder_gui.py

# Test with multi-animal data:
1. Load experiment with multiple animals
2. Note identical Day/Trial numbers across animals
3. Click different rows in Results Table
4. ✓ Each row shows different trajectory path
5. ✓ Heatmap dropdown shows "Row X:" labels
```

## Files Modified

1. **`gui/results_table.py`**
   - Changed signal: `trial_selected = pyqtSignal(int)`
   - Emit row index: `self.trial_selected.emit(row)`

2. **`gui/integration.py`**
   - Updated slot: `def on_trial_selected(self, row_index: int)`
   - Call new method: `hm.show_trial_by_index(row_index)`

3. **`gui/heatmap_widget.py`**
   - New method: `show_trial_by_index(row_index)`
   - Updated dropdown labels: `"Row X: Day Y Trial Z - Strategy"`
   - Store row indices as data (not trial_id)
   - Handle filtering correctly

## Edge Cases Handled

✅ **Sorted table** - Row index follows sort order
✅ **Filtered by day** - Finds trial in filtered list, then maps to original
✅ **Empty selection** - Gracefully handles no selection
✅ **Invalid index** - Bounds checking prevents crashes

## Backward Compatibility

The `manual_classification_requested` signal still uses `trial_id` since it needs to modify a specific trial's data. Only the visualization/display uses row indices.

## Result

**Problem FIXED**: Each row now correctly maps to its unique trial, regardless of how many animals share the same Day/Trial numbers.
