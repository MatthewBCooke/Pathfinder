# Parameter Verification Report

## Summary

✅ **All parameters from old code have been verified and added to the new Pathfinder system**

✅ **NOT_RECOGNIZED strategy added as fallback instead of Random Search**

## Strategy Classification Order

Both old and new code use the same hierarchical decision tree:

1. **Direct Path** (score=3) - Most efficient
2. **Focal Search** (score=2) - Concentrated near platform
3. **Directed Search** (score=2) - Swimming in corridor toward platform
4. **Indirect Search** (score=2) - Near miss with good heading
5. **Semi-Focal Search** (score=2) - Broader focused search
6. **Chaining** (score=1) - Repeated similar paths
7. **Scanning** (score=1) - Systematic pool coverage
8. **Thigmotaxis** (score=0) - Wall-hugging
9. **Random Search** (score=0) - High coverage, no pattern
10. **NOT_RECOGNIZED** (score=0) - **NEW**: No strategy fits (instead of defaulting to Random)

## Parameter Comparison

### Direct Path
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| ipeMaxVal | 125 | 125 | ✅ Match |
| headingMaxVal | 40 | 40 | ✅ Match |
| useDirect | True | True | ✅ Match |

### Focal Search
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| distanceToSwimMaxVal | 30 | 30 | ✅ Match |
| distanceToPlatMaxVal | 30 | 30 | ✅ Match |
| focalMinDistance | 100 | 100 | ✅ Match |
| focalMaxDistance | 400 | 400 | ✅ Match |
| useFocal | True | True | ✅ Match |

### Directed Search
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| corridorAverageMinVal | 70 | 70 | ✅ Match |
| corridoripeMaxVal | 1500 | 1500 | ✅ Match |
| directedSearchMaxDistance | 400 | 400 | ✅ Match |
| useDirected | True | True | ✅ Match |

### Indirect Search
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| ipeIndirectMaxVal | 300 | 300 | ✅ Match |
| headingIndirectMaxVal | 70 | 70 | ✅ Match |
| useIndirect | True | True | ✅ Match |

### Semi-Focal Search
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| distanceToSwimMaxVal2 | 50 | 50 | ✅ Match |
| distanceToPlatMaxVal2 | 50 | 50 | ✅ Match |
| semiFocalMinDistance | 0 | 0 | ✅ Match |
| semiFocalMaxDistance | 500 | 500 | ✅ Match |
| useSemiFocal | False | False | ✅ Match |

### Chaining
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| annulusCounterMaxVal | 90 | 90 | ✅ Match |
| quadrantTotalMaxVal | 4 | 4 | ✅ Match |
| chainingMaxCoverage | 40 | 40 | ✅ Match |
| useChaining | True | True | ✅ Match |

### Scanning
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| percentTraversedMinVal | 5 | 5 | ✅ Match |
| percentTraversedMaxVal | 20 | 20 | ✅ Match |
| distanceToCentreMaxVal | 60 | 60 | ✅ Match |
| useScanning | True | True | ✅ Match |

### Thigmotaxis
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| fullThigmoMinVal | 65 | 65 | ✅ Match |
| smallThigmoMinVal | 35 | 35 | ✅ Match |
| thigmoMinDistance | 400 | 400 | ✅ Match |
| useThigmotaxis | True | True | ✅ Match |

### Random Search
| Parameter | Old Code | New Code | Status |
|-----------|----------|----------|--------|
| percentTraversedRandomMaxVal | 10 | 10 | ✅ Match |
| useRandom | True | True | ✅ Match |

## Files Modified

### 1. `pathfinder/core/models.py`
- ✅ Added `NOT_RECOGNIZED` to `SearchStrategy` enum
- ✅ Added all missing parameters to `Parameters` class:
  - `ipe_indirect_max_val` (300)
  - `heading_indirect_max_val` (70)
  - `percent_traversed_min_val` (5)
  - `distance_to_centre_max_val` (60)
  - `full_thigmo_min_val` (65)
  - `small_thigmo_min_val` (35)
  - `thigmo_min_distance` (400)
  - `percent_traversed_random_max_val` (10)
  - All `use_*` enable/disable flags

### 2. `gui/results_table.py`
- ✅ Added `NOT_RECOGNIZED` to color mapping (dark gray #757575)

### 3. `gui/summary_widget.py`
- ✅ Added `NOT_RECOGNIZED` to color mapping (dark gray #757575)

### 4. `gui/settings_dialog_v2.py`
- ✅ Moved corridor width parameter from Direct Swim to Directed Search tab
- ✅ Updated corridor label to "Directed Search Corridor"

### 5. `gui/maze_visualization.py`
- ✅ Updated corridor label from "Direct Corridor" to "Directed Search Corridor"

## Verification Tests

```bash
# Test 1: Parameters model loads with all fields
✓ Parameters model loads successfully
✓ use_direct=True
✓ ipe_indirect_max_val=300
✓ full_thigmo_min_val=65

# Test 2: NOT_RECOGNIZED enum exists
✓ SearchStrategy imports
✓ NOT_RECOGNIZED: not_recognized
```

## Classification Logic Comparison

### Old Code (from user-provided snippet)
```python
if ipe <= params.ipeMaxVal and averageHeadingError <= params.headingMaxVal and params.useDirect:
    strategyType = "Direct Path"
elif averageDistanceToSwimPathCentroid < (mazeRadius * params.distanceToSwimMaxVal / 100) and ...
    strategyType = "Focal Search"
# ... (continues through all strategies)
else:
    strategyType = "Not Recognized"  # ✓ PRESENT
```

### New Code (`pathfinder/analysis.py`, lines 539-602)
```python
if (ipe <= parameters.ipeMaxVal and
    average_heading_error <= parameters.headingMaxVal and
    parameters.useDirect):
    return ("Direct Path", 3)
elif (average_distance_to_swim_path_centroid < (maze_radius * parameters.distanceToSwimMaxVal / 100) and ...
    return ("Focal Search", 2)
# ... (continues through all strategies)
else:
    return ("Not Recognized", 0)  # ✓ ADDED
```

## Next Steps (Optional)

Task #3 is still pending: **Update settings dialog with all missing parameters**

Currently the settings dialog (`gui/settings_dialog_v2.py`) exposes:
- ✅ Direct Swim parameters (IPE, heading, corridor min)
- ✅ Directed Search parameters (distance, corridor IPE, corridor min, corridor width)
- ✅ Focal Search parameters (min/max distance, distance to platform/swim)
- ✅ Chaining parameters (max coverage, radius)
- ✅ Spatial Indirect parameters (partially)
- ✅ Thigmotaxis parameters (zone size, min time)
- ❌ **Missing**: Indirect Search parameters (IPE indirect, heading indirect)
- ❌ **Missing**: Semi-Focal Search parameters
- ❌ **Missing**: Scanning parameters (percent traversed min/max, distance to centre)
- ❌ **Missing**: Random Search parameters
- ❌ **Missing**: Enable/disable checkboxes for all strategies

**Question**: Do you want me to add all missing parameters to the settings dialog, or are the current exposed parameters sufficient?

## Conclusion

✅ **All strategy classification parameters match your old code exactly**

✅ **NOT_RECOGNIZED strategy added as proper fallback instead of defaulting to Random Search**

✅ **GUI components updated to handle NOT_RECOGNIZED strategy**

✅ **Corridor parameters moved to correct location (Directed Search) and properly labeled**
