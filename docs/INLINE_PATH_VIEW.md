# Inline Path Visualization

## Summary

✅ **Expandable trial paths in results table** - Click any row to view path inline
✅ **Better UX** - No need to switch tabs or use dropdowns
✅ **Toggle view** - Click same row again to collapse

## How It Works

### Click to Expand

1. **Click any trial row** in the results table
2. Panel expands below the table showing:
   - Trial information (Row #, Day, Trial, Strategy)
   - Full trajectory path visualization
   - Start point (green circle)
   - End point (red square)
   - Platform location (red circle)
   - Pool boundary
   - Path metrics in title

### Click to Collapse

- Click the **same row again** to close the path view
- Click **"✕ Close Path View"** button to close
- View collapses back to just the table

### Switch Between Trials

- Click **different rows** to see different trial paths
- View updates immediately
- No need to close first

## Visualization Features

### Path Display

- **Color-coded by strategy**:
  - Direct Swim: Green
  - Directed Search: Light Green
  - Focal Search: Yellow
  - Spatial Indirect: Amber
  - Chaining: Orange
  - Scanning: Deep Orange
  - Thigmotaxis: Red
  - Random Search: Gray
  - Not Recognized: Dark Gray

- **Trajectory line**: Thick (2px), semi-transparent
- **Start marker**: Green circle with dark border
- **End marker**: Red square with dark border
- **Platform**: Red semi-transparent circle
- **Pool boundary**: Black circle outline

### Title Bar Shows

```
Row 5: Day 2, Trial 3 - Focal Search
```

```
Trajectory - Latency: 15.23s, Path: 380.5cm
```

- Row number (matches table)
- Day and trial numbers
- Strategy classification
- Escape latency
- Total path length

### Layout

```
┌────────────────────────────────────────┐
│  Results Table (16 columns)           │
│  [All trials listed]                   │
│                                        │
│  > Row 5 clicked                       │
├────────────────────────────────────────┤
│  Row 5: Day 2, Trial 3 - Focal Search │
│  ┌──────────────────────────────────┐ │
│  │                                  │ │
│  │    [Trajectory Visualization]   │ │
│  │         with pool, platform,    │ │
│  │         start/end markers       │ │
│  │                                  │ │
│  └──────────────────────────────────┘ │
│  [✕ Close Path View]                  │
└────────────────────────────────────────┘
```

## Technical Implementation

### Splitter Layout

Uses `QSplitter` with vertical orientation:
- **Top pane**: Results table (always visible)
- **Bottom pane**: Path visualization (shown on demand)

### Splitter Sizes

- **Collapsed**: `[1000, 0]` - All space to table
- **Expanded**: `[600, 400]` - 60% table, 40% path view

### State Management

```python
self._expanded_row: Optional[int]  # Currently expanded row (None if collapsed)
```

### Event Flow

```
User clicks row 5
    ↓
_on_cell_clicked(row=5, column=X)
    ↓
Check if row == _expanded_row
    ↓
If same: _close_path_view()
If different: _show_trial_path(row)
    ↓
Plot trajectory
    ↓
Show path_panel
    ↓
Adjust splitter sizes [600, 400]
```

### Plotting

Uses matplotlib embedded canvas (`FigureCanvas`):
- Pool boundary (circle)
- Platform (filled circle)
- Trajectory (line plot)
- Start/end markers (scatter plot)
- Grid and labels
- Strategy-based coloring

### Data Validation

- Filters out NaN and None values from trajectory
- Handles empty trajectories gracefully
- Shows "No valid trajectory data" if needed

## Benefits

### UX Improvements

✅ **No tab switching** - View path right where you clicked
✅ **Context preserved** - See table and path at same time
✅ **Quick comparison** - Click different rows to compare paths
✅ **Toggle easily** - Click same row to close
✅ **Visual feedback** - Clear what row you're viewing

### Performance

✅ **On-demand rendering** - Only plots when clicked
✅ **Reuses canvas** - Same Figure object updated
✅ **Fast switching** - Immediate path updates

## Removed Old Behavior

The old click-to-heatmap behavior is **disabled**:

```python
def _on_selection_changed(self):
    # self.trial_selected.emit(row)  # Disabled - use inline view instead
```

The `trial_selected` signal is no longer emitted, so the heatmap won't switch when clicking rows.

## Files Modified

**`gui/results_table.py`**:
- Added `QSplitter` for expandable layout
- Added `path_panel` with matplotlib canvas
- Added `_on_cell_clicked()` handler
- Added `_show_trial_path()` method
- Added `_plot_trial_path()` method
- Added `_close_path_view()` method
- Added `_get_strategy_color_hex()` helper
- Updated imports for matplotlib

## Testing

```bash
python3 pathfinder_gui.py

# Test:
1. Load experiment
2. Run analysis
3. Click any row in results table
4. ✓ Path panel expands below with trajectory
5. ✓ Title shows correct row/day/trial/strategy
6. ✓ Path matches strategy color
7. Click same row
8. ✓ Panel collapses
9. Click different row
10. ✓ New path appears immediately
11. Click "✕ Close Path View"
12. ✓ Panel closes
```

## Example Workflow

### Analyzing Thigmotaxis Trial

1. Sort by Strategy column
2. Click a "thigmotaxis" trial row
3. ✓ Path expands showing wall-hugging behavior
4. Red trajectory line hugs pool boundary
5. Long path length visible
6. Compare with Direct Swim trial
7. Click Direct Swim row
8. ✓ Green straight line to platform appears

### Quality Control

1. Notice unusual latency value (e.g., 0.5s)
2. Click that trial row
3. ✓ View path to see if data is valid
4. Check if start point is near platform (explains short latency)
5. Or identify bad tracking data

## Future Enhancements

Possible additions:
- [ ] Add velocity color gradient along path
- [ ] Overlay analysis zones (thigmotaxis, chaining, corridor)
- [ ] Show datapoint timestamps on hover
- [ ] Export individual path to image
- [ ] Side-by-side comparison of two trials
- [ ] Animation playback of trajectory over time
