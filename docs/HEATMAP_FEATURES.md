# Interactive Heatmap Features

## New Features Implemented ✅

### 1. **Trial Selector in Individual Paths Mode**

When you select "Individual Paths" visualization type, a new **"Trial:"** dropdown appears:

- **"All Trials (max 10)"** - Shows up to 10 trial paths overlaid (previous behavior)
- **Individual trial selection** - Select any specific trial to view just that path

**Trial dropdown shows:**
- Trial number
- Day number
- Classified strategy
- Example: `Trial 5 (Day 2) - Focal Search`

### 2. **Click-to-View from Results Table**

**NEW BEHAVIOR**: When you click on any row in the Results Table, the heatmap automatically:

1. ✅ Switches to "Individual Paths" mode (if not already)
2. ✅ Selects that specific trial in the dropdown
3. ✅ Displays that trial's complete trajectory path

**This creates a seamless workflow:**
```
Results Table → Click trial → Heatmap shows that exact path
```

### 3. **Enhanced Path Visualization**

When viewing a **single trial**, the display now shows:

- **Blue trajectory line** (thicker, more visible than multi-trial view)
- **Green circle** - Start point (with dark green border)
- **Red square** - End point (with dark red border)
- **Red circle** - Platform location (semi-transparent)
- **Black circle** - Pool boundary
- **Legend** - Shows strategy classification

**Title shows:** `Trial X Trajectory (Day Y)`

### 4. **Multi-Trial View** (when "All Trials" selected)

When viewing multiple trials:
- **Color-coded paths** - Each trial gets a different color from viridis colormap
- **Thinner lines** - Better visibility with overlapping paths
- **Green dots** - Start points for all trials
- **Red squares** - End points for all trials
- **Title shows:** `Individual Trajectories (showing X of Y trials)`

## How to Use

### Method 1: Heatmap Dropdown Selection

1. Go to the **Heatmap** tab
2. Select **"Individual Paths"** from Type dropdown
3. Use the **"Trial:"** dropdown to select specific trial
4. Click **"🔄 Regenerate"** if needed

### Method 2: Click from Results Table (Recommended!)

1. Go to **Results Table** tab
2. Click on any trial row
3. **Automatically switches** to Heatmap tab and shows that trial's path

## Filtering Capabilities

The trial selector respects day filters:
- Select **"Day: 2"** → Trial dropdown only shows Day 2 trials
- Select **"Day: All Days"** → Trial dropdown shows all trials

## Visual Markers Legend

| Marker | Meaning |
|--------|---------|
| 🟢 Green Circle | Start position of trial |
| 🔴 Red Square | End position of trial |
| 🔴 Red Circle (filled) | Platform location |
| ⚫ Black Circle (outline) | Pool boundary |
| 🔵 Blue Line (single) | Single trial trajectory |
| 🌈 Colored Lines (multiple) | Multi-trial overlay |

## Technical Details

### Data Validation
- Automatically filters out NaN and Inf values from trajectories
- Handles missing data gracefully
- Validates coordinates before plotting

### Signal Flow
```
ResultsTableWidget.trial_selected(trial_id)
    ↓
PathfinderIntegration.on_trial_selected(trial_id)
    ↓
HeatmapWidget.show_trial(trial_id)
    ↓
  • Switches to "Individual Paths" mode
  • Selects trial in dropdown
  • Triggers regenerate plot
```

### Files Modified

1. **`gui/heatmap_widget.py`**
   - Added trial selector combo box
   - Added `show_trial(trial_id)` public method
   - Enhanced `_plot_individual_paths()` for single/multi trial modes
   - Added `_update_trial_selector()` to populate dropdown
   - Added `_on_trial_changed()` event handler

2. **`gui/integration.py`**
   - Implemented `on_trial_selected()` to connect table to heatmap
   - Wires up ResultsTable signal to HeatmapWidget

## Example Workflow

### Analyzing a Specific Trial

1. **Load experiment** → File loaded with 50 trials
2. **Run analysis** → All trials classified
3. **Browse results table** → Notice Trial 23 has "Thigmotaxis" strategy
4. **Click on Trial 23 row** → Heatmap instantly shows Trial 23's wall-hugging path
5. **Compare with another** → Click Trial 5 row → See "Direct Swim" straight path

### Comparing Multiple Trials from Same Day

1. **Select "Day: 3"** in heatmap controls
2. **Select "Individual Paths"** mode
3. **Keep "All Trials (max 10)"** selected
4. **Click Regenerate** → See up to 10 Day 3 trials overlaid
5. **Notice one stands out** → Use dropdown to select that specific trial

## Benefits

✅ **No more manual searching** - Click to view instantly
✅ **Visual strategy verification** - See why each strategy was classified
✅ **Quick comparisons** - Switch between trials with one click
✅ **Context preserved** - Trial metadata shown in dropdown
✅ **Seamless workflow** - Results table and heatmap work together

## Testing

```bash
python3 pathfinder_gui.py

# Then:
1. Load an experiment file
2. Run analysis
3. Go to Results Table
4. Click any trial row
5. ✓ Heatmap should show that trial's path automatically
```

## Next Steps (Future Enhancements)

Possible future additions:
- [ ] Side-by-side comparison of two trials
- [ ] Animation of trajectory playback over time
- [ ] Overlay analysis zones (thigmotaxis, chaining, etc.) on individual paths
- [ ] Export individual trial paths to image files
- [ ] Add velocity/speed color gradient along path
