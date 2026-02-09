# Metrics & Settings Update

## Summary

✅ **Fixed Direct Swim classification** - Now uses proper classify_strategy function
✅ **Added 9 new metrics columns** to results table
✅ **Added thigmotaxis zone width settings** to settings dialog

## New Results Table Columns

The results table now shows **16 columns** (was 8):

| Column | Description | Format |
|--------|-------------|--------|
| Day | Experimental day | Integer |
| Trial # | Trial number | Integer |
| Strategy | Classified strategy | Color-coded |
| Latency (s) | Escape latency | Decimal (2 places) |
| Path (cm) | Total path length | Decimal (1 place) |
| Speed (cm/s) | Average swim speed | Decimal (1 place) |
| **IPE** | **Ideal Path Error** | **Decimal (1 place)** |
| **Heading Avg (°)** | **Average heading error** | **Decimal (1 place)** |
| **Heading Max (°)** | **Initial heading error** | **Decimal (1 place)** |
| **Corridor (%)** | **Time in corridor toward platform** | **Decimal (1 place)** |
| **Coverage (%)** | **Pool coverage (percent traversed)** | **Decimal (1 place)** |
| **Chaining (%)** | **Time in chaining zone (annulus)** | **Decimal (1 place)** |
| **Quadrants** | **Number of quadrants visited (1-4)** | **Integer** |
| **Thigmo Full (%)** | **Time in full thigmotaxis zone** | **Decimal (1 place)** |
| **Thigmo Small (%)** | **Time in small thigmotaxis zone** | **Decimal (1 place)** |
| Manual | Manual classification flag | Checkmark |

**Bold** = New columns added

## Metrics Calculations

All metrics are calculated using `calculate_trial_metrics()` from `pathfinder/analysis.py` and stored in `trial._metrics`.

### IPE (Ideal Path Error)
- Difference between actual path distance and ideal straight-line path
- Lower = more efficient/direct
- Direct Swim threshold: IPE ≤ 125

### Heading Error Average
- Average angular deviation from platform direction throughout trial
- Lower = better orientation
- Direct Swim threshold: ≤ 40°

### Heading Error Max
- Uses initial heading error (first second of trial)
- Indicates starting orientation accuracy

### Time in Corridor (%)
- Percentage of time swimming in angular corridor toward platform
- Corridor width configurable in settings (default: ±15°)
- Direct Swim threshold: ≥ 70%

### Pool Coverage (%)
- Percentage of pool grid cells visited
- Based on grid normalization
- High = exploration, Low = focused search

### Time in Chaining Zone (%)
- Percentage of samples in annulus around platform
- Annulus = ring at platform distance from pool center
- Width configurable in settings (default: 30cm)

### Quadrants Visited
- Number of pool quadrants entered (1-4)
- 4 = systematic coverage (Scanning strategy)
- 1-2 = localized search

### Thigmotaxis Zones (%)
- **Full Zone**: Outer ring near wall (default: 20% of radius from wall)
- **Small Zone**: Inner ring (default: 80% of radius from center)
- Thigmotaxis threshold: ≥65% in full, ≥35% in small

## New Thigmotaxis Settings

Added to **Settings → ⭕ Thigmotaxis** tab:

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Maximum Pool Coverage | 0-100% | 20% | Max coverage for thigmotaxis (low = wall-hugging) |
| Thigmotaxis Zone Width (Visual) | 5-50% of radius | 20% | Width of visualization zone |
| Minimum Time in Full Zone | 0-100% | 65% | Min time in outer zone for classification |
| Minimum Time in Small Zone | 0-100% | 35% | Min time in inner zone for classification |
| Minimum Path Distance | 0-1000 cm | 400cm | Min total distance for classification |

## UI Layout

The table is now **wider** to accommodate all metrics. Columns are sized appropriately:
- Fixed width for numeric columns
- Strategy column stretches to fill remaining space
- All numeric values right-aligned
- Missing data shows "—"

## Data Flow

```
AnalysisWorker.run()
    ↓
calculate_trial_metrics() → TrialMetrics object
    ↓
classify_strategy() → Strategy name + score
    ↓
Store metrics: trial._metrics = metrics
    ↓
ResultsTableWidget._add_trial_row()
    ↓
Read from trial._metrics
    ↓
Display all 16 columns
```

## Example Output

```
Day | Trial# | Strategy        | Latency | Path  | Speed | IPE   | Heading | Corridor | Coverage | ...
--- | ------ | --------------- | ------- | ----- | ----- | ----- | ------- | -------- | -------- | ...
1   | 1      | Direct Swim     | 8.5     | 245.3 | 28.9  | 98.2  | 25.3    | 85.6     | 12.3     | ...
1   | 2      | Focal Search    | 15.2    | 380.5 | 25.0  | 195.7 | 45.2    | 45.3     | 25.8     | ...
1   | 3      | Thigmotaxis     | 58.3    | 890.2 | 15.3  | 750.3 | 78.5    | 15.2     | 8.5      | ...
```

## Testing

```bash
python3 pathfinder_gui.py

# Test:
1. Load experiment
2. Run analysis
3. ✓ Results table shows all 16 columns
4. ✓ Metrics populated with calculated values
5. ✓ Direct Swim trials properly classified
6. ✓ Settings → Thigmotaxis shows new zone parameters
```

## Files Modified

1. **`gui/results_table.py`**
   - Increased column count from 8 to 16
   - Updated `_add_trial_row()` to populate all metrics
   - Added helper function `make_numeric_item()` for formatting
   - Adjusted column widths for all new columns

2. **`gui/settings_dialog_v2.py`**
   - Updated `_create_thigmotaxis_tab()` with 5 parameters
   - Added loading in `_load_values()` for thigmotaxis settings
   - Added saving in `_on_accept()` for thigmotaxis settings

3. **`gui/integration.py`** (from classification fix)
   - Updated AnalysisWorker to store metrics in `trial._metrics`
   - Makes metrics available for results table display

## Benefits

✅ **Complete visibility** - See all metrics that inform classification
✅ **Easy debugging** - Understand why each trial was classified
✅ **Quality control** - Spot outliers or bad data quickly
✅ **Research insights** - Export detailed metrics for analysis
✅ **Configurable zones** - Adjust thigmotaxis detection sensitivity

## Note on Table Width

The table is now significantly wider due to 16 columns. Consider:
- Maximizing window for full view
- Horizontal scrolling is enabled
- Most important columns (Day, Trial, Strategy, Latency) are on the left
- Less frequently viewed metrics (thigmotaxis zones) are on the right
