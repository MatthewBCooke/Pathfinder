# Pathfinder Maze Visualization Guide

**Last Updated**: 2026-02-08

## Overview

The Pathfinder maze visualization provides a real-time, interactive display of the Morris Water Maze geometry and analysis zones. All zone sizes are controlled via settings and update automatically.

## Features

### ✅ Unit-Agnostic System
- All spatial values (pool size, platform position, etc.) are **unit-agnostic**
- Works with any tracking software units (pixels, cm, mm, etc.)
- Values are treated as relative measurements in whatever unit the tracking software recorded
- Use `pixels_per_cm` setting for real-world conversions when needed

### ✅ Live Updates
- Adjust spatial parameters → visualization updates **immediately**
- No need to click "Apply" to see changes
- Smooth, responsive interface
- All zones scale automatically

### ✅ Settings Integration
- All zone sizes read from Settings dialog
- Change settings → visualization reflects new values instantly
- Accurate representation of both maze geometry AND classification parameters

##Visualization Zones

### Zone Display (in draw order)

| Zone | Color | Description | Controlled By |
|------|-------|-------------|---------------|
| **Thigmotaxis** | Gray annulus | Wall-hugging zone near edge | Settings → Thigmotaxis → Width % (default 20%) |
| **Chaining** | Yellow annulus | Circular search pattern zone | Settings → Chaining → Radius (default 30cm) |
| **Direct Corridor** | Green wedge | Optimal swim path from center to platform | Internal parameter (default ±15°) |
| **Focal Search** | Pink/magenta circle | Tight concentrated search zone | Internal multiplier (default 1.5× platform) |
| **Pool** | Blue circle | Main pool boundary | From spatial parameters |
| **Platform** | Red circle | Target escape platform | From spatial parameters |

### Zone Calculations

**Thigmotaxis Zone**:
- Annulus near wall
- Width = pool_radius × (thigmotaxis_percent / 100)
- Default: 20% from wall
- Centered on pool center

**Chaining Zone**:
- Annulus centered on pool center
- **Midpoint positioned at platform's distance from center**
- Width converted from cm to tracking units: `chaining_radius × pixels_per_cm`
- Default width: 30cm
- Dynamically resizes based on platform position

**Direct Swim Corridor**:
- Wedge from pool center toward platform
- Angular width: ±corridor_width_degrees (default ±15°)
- **Drawn AFTER annulus zones** to avoid being obscured
- Points directly at platform, updates as platform moves

**Focal Search Zone**:
- Circle centered on platform
- Radius = platform_diameter × focal_multiplier
- Default multiplier: 1.5
- Represents tight, concentrated search behavior

## Settings Parameters

### General Settings Tab
- **Parameter Set Name**: Name for this configuration
- **Auto-scale values**: Whether to scale values based on pool size
- **Pixels per cm**: Conversion factor for real-world measurements

### Zone-Specific Settings

**Chaining Tab**:
- `chaining_radius` (default 30cm) - Controls chaining annulus width
- `chaining_max_coverage` (default 40%) - Max pool coverage for classification

**Thigmotaxis Tab**:
- `thigmotaxis_zone_percent` (default 20%) - Zone width as % of pool radius

**Internal Parameters** (in Parameters model, not exposed in UI):
- `focal_search_radius_multiplier` (default 1.5)
- `corridor_width_degrees` (default 15)

## Usage Guide

### Basic Workflow

1. **Open Pathfinder**
   ```bash
   source .venv/bin/activate
   python3 pathfinder_gui.py
   ```

2. **Go to "🔵 Maze Setup" tab**
   - See current maze geometry visualization

3. **Adjust Spatial Parameters** (left sidebar)
   - Pool Center X/Y
   - Pool Diameter
   - Platform X/Y
   - Platform Diameter
   - **Visualization updates in real-time!**

4. **Click "Apply Geometry"**
   - Applies parameters to all loaded trials
   - Required before running analysis

5. **Adjust Zone Settings** (Settings button)
   - Go to relevant strategy tab
   - Modify zone parameters
   - **Visualization updates immediately!**

### Testing Changes

**Test Spatial Parameters**:
1. Adjust "Platform X" spinbox → watch platform move
2. Adjust "Pool Diameter" → watch all zones scale
3. Move platform near wall → chaining zone contracts
4. Move platform to center → chaining zone expands

**Test Settings Integration**:
1. Click ⚙️ Settings
2. Go to "Chaining" tab
3. Change "Chaining Zone Radius" from 30 to 50
4. Click OK
5. Return to Maze Setup tab
6. ✅ Yellow ring should be wider
7. ✅ Label shows "Chaining Zone (50cm width)"

## Technical Details

### Drawing Order (Critical!)

Zones must be drawn in this order to avoid visual occlusion:

1. **Thigmotaxis annulus** (with white inner circle)
2. **Chaining annulus** (with white inner circle)
3. **Direct Swim Corridor** ⚠️ **Must be after annuli!**
4. **Focal Search zone**
5. **Pool boundary**
6. **Platform**

**Why**: Annulus zones use white inner circles to create the ring effect. The corridor must be drawn AFTER these to avoid being covered.

### Signal Flow

```
User adjusts spatial spinbox
  ↓
QDoubleSpinBox.valueChanged signal
  ↓
ControlPanel._on_spatial_param_changed()
  ↓
ControlPanel.spatial_params_changed.emit(params)
  ↓
MazeVisualization.update_parameters(params)
  ↓
Visualization redraws immediately
```

```
User changes settings
  ↓
SettingsDialogV2 saves to Parameters
  ↓
Integration.on_settings() receives new parameters
  ↓
maze_viz.set_parameters(new_params)
  ↓
Zones read new sizes from parameters
  ↓
Visualization redraws with new zone sizes
```

### Code Locations

**Visualization**:
- `gui/maze_visualization.py` - QPainter-based rendering
- Lines 128-260: Zone drawing code
- Lines 70-100: Helper methods for parameters

**Control Panel**:
- `gui/control_panel.py` - Spatial parameter spinboxes
- Lines 110-162: Spinbox definitions (no unit suffixes)
- Lines 195-206: Live update handlers

**Integration**:
- `gui/integration.py` - Connects signals and parameters
- Lines 317-332: Maze viz initialization with parameters
- Lines 638-645: Settings update handler

**Settings**:
- `gui/settings_dialog_v2.py` - Per-strategy configuration
- Lines 280-301: Chaining zone settings
- Lines 326-358: Thigmotaxis zone settings

**Parameters Model**:
- `pathfinder/core/models.py` - Data model
- Lines 73-78: Visualization parameters

## Common Issues & Solutions

### Issue: Corridor Not Fully Visible
**Symptom**: Green corridor wedge starts partway from center, not at pool center
**Cause**: Corridor drawn before annulus zones, covered by white inner circles
**Solution**: Corridor is now drawn AFTER annuli (fixed)

### Issue: Changing Settings Doesn't Update Visualization
**Symptom**: Modified chaining radius in settings, but yellow ring stays same size
**Cause**: Visualization not reading from Parameters object
**Solution**: Integration layer now passes parameters to visualization (fixed)

### Issue: Labels Show "px" But Data is in cm
**Symptom**: Misleading unit labels
**Cause**: Hardcoded "px" suffix
**Solution**: All unit suffixes removed, system is now unit-agnostic (fixed)

### Issue: AttributeError on Startup
**Symptom**: `'PathfinderIntegration' object has no attribute 'parameters'`
**Cause**: Using `self.parameters` instead of `self.current_parameters`
**Solution**: Use correct attribute name `self.current_parameters` (fixed)

## Best Practices

### For Users
- **Always check Maze Setup tab** before running analysis
- **Verify zones look correct** for your experimental setup
- **Adjust settings** to match your specific protocol
- **Use Apply Geometry** when spatial parameters change

### For Developers
- **Never assume units** - keep system unit-agnostic
- **Read from Parameters** - don't hardcode zone sizes
- **Respect drawing order** - corridor after annuli!
- **Test both live updates** - spinbox changes AND settings changes
- **Use `self.current_parameters`** in integration layer

## Changelog

### 2026-02-08: Unit-Agnostic Update
- ✅ Removed all "px" unit suffixes from GUI
- ✅ Updated model descriptions to "tracking software units"
- ✅ Spatial parameters now unit-agnostic

### 2026-02-08: Directed Search Removed
- ✅ Removed directed search ring (cyan circle)
- ✅ Updated legend
- ✅ Cleaner visualization with essential zones

### 2026-02-08: Settings Integration Complete
- ✅ All zone sizes read from Parameters model
- ✅ Added visualization parameters to core model
- ✅ Settings dialog saves/loads zone parameters
- ✅ Visualization updates when settings change

### 2026-02-08: Drawing Order Fixed
- ✅ Corridor moved to after annulus zones
- ✅ Full corridor now visible from pool center

### 2026-02-08: Chaining Zone Corrected
- ✅ Changed from circle to annulus (ring)
- ✅ Centered on pool center (not platform)
- ✅ Midpoint positioned at platform distance
- ✅ Dynamic width based on settings

### 2026-02-08: Focal Search Added
- ✅ Added focal search zone (pink/magenta circle)
- ✅ Smaller than directed search
- ✅ Represents tight concentrated search behavior

### 2026-02-08: Live Updates Implemented
- ✅ Spinbox changes update visualization immediately
- ✅ No need to click "Apply" for visual feedback
- ✅ Separate "Apply" button for trial data updates

## References

- **Morris Water Maze Literature**: Chaining, focal search, and directed search behavioral patterns
- **Qt Documentation**: QPainter, coordinate systems, signal/slot pattern
- **Pathfinder Core**: `pathfinder/core/models.py` for data structures
