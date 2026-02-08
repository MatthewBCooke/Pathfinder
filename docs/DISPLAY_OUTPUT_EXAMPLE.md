# Spatial Parameters Display Output

## Overview

The Pathfinder GUI now includes a real-time display of spatial parameters in the control panel, similar to the original version. This display shows current maze geometry settings and validates the configuration.

## Display Features

### Real-Time Updates
- Display updates automatically as you adjust spinbox values
- No need to click "Apply" to see the changes in the display
- Instant validation feedback

### Formatted Display Example

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POOL CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Center:     (250.0, 250.0) px
  Diameter:   500.0 px
  Radius:     250.0 px

PLATFORM CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Position:   (350.0, 150.0) px
  Diameter:   50.0 px
  Radius:     25.0 px

STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Platform within pool bounds
  ✓ Valid configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Validation Indicators

The display shows automatic validation:

**✓ Valid Configuration**
- Pool diameter > platform diameter
- Platform within pool bounds
- All positive values

**⚠ Warnings**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠ Platform may be outside pool!
  ✓ Valid configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**✗ Errors**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Platform within pool bounds
  ✗ Pool must be larger than platform!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Display Location

The display appears in the **"Maze Geometry"** group box in the left control panel:

```
┌─────────────────────────────────┐
│  Maze Geometry                  │
├─────────────────────────────────┤
│ Pool Center X:     [250.0] px   │
│ Pool Center Y:     [250.0] px   │
│ Pool Diameter:     [500.0] px   │
│ Platform X:        [350.0] px   │
│ Platform Y:        [150.0] px   │
│ Platform Diameter: [ 50.0] px   │
│ [Apply Geometry]                │
│                                 │
│ Current Settings:               │
│ ┌─────────────────────────────┐ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│ │ POOL CONFIGURATION          │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│ │   Center:   (250.0, 250.0)  │ │
│ │   Diameter: 500.0 px        │ │
│ │   Radius:   250.0 px        │ │
│ │                             │ │
│ │ PLATFORM CONFIGURATION      │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│ │   Position: (350.0, 150.0)  │ │
│ │   Diameter: 50.0 px         │ │
│ │   Radius:   25.0 px         │ │
│ │                             │ │
│ │ STATUS                      │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│ │   ✓ Platform within pool    │ │
│ │   ✓ Valid configuration     │ │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

## Calculated Values

The display automatically calculates and shows:

1. **Pool Radius**: Calculated as `diameter / 2`
2. **Platform Radius**: Calculated as `diameter / 2`
3. **Platform Distance from Center**: Distance between pool center and platform position
4. **Bounds Validation**: Whether platform fits within pool boundary

## Comparison to Original

### Original Pathfinder (Tkinter)
- Had separate entry fields for each parameter
- Settings displayed in various places
- Manual validation required

### New Pathfinder (PyQt5)
- Organized spinbox inputs with live constraints
- **Centralized display panel** showing all current settings
- **Real-time validation** with visual indicators
- **Calculated values** (radii, distances) shown automatically

## Interactive Behavior

1. **User adjusts spinbox** → Display updates immediately
2. **User clicks "Apply Geometry"** → Display updates + signal emitted to backend
3. **Invalid configuration** → Display shows error indicators (✗, ⚠)
4. **Valid configuration** → Display shows checkmarks (✓)

## Testing the Display

Run the test script to see the display in action:

```bash
cd "/Users/matthewcooke/Documents/UBC/Pathfinder/Pathfinder 2/Pathfinder"
source .venv/bin/activate
python3 test_spatial_display.py
```

Or run the full application:

```bash
python3 pathfinder_gui.py
```

Then look at the left control panel, "Maze Geometry" section.

## Styling

The display uses:
- **Monospace font** for aligned columns
- **Gray background** (#f0f0f0) for read-only area
- **Unicode box characters** (━) for section dividers
- **Emoji indicators** (✓, ✗, ⚠) for validation status
- **9pt font size** for compact display

## Accessibility

- Read-only text area prevents accidental editing
- High contrast text for readability
- Clear section headers
- Visual indicators supplement text

## Future Enhancements

Potential additions to the display:
- **Distance from platform to pool edge**: Show clearance
- **Quadrant indicator**: Show which quadrant contains platform
- **Units conversion**: Display values in both px and cm
- **Visual diagram**: ASCII art representation of pool/platform layout

## Related Files

- **Implementation**: `gui/control_panel.py:167-234` - Display creation and update logic
- **Styling**: Inline CSS in `_create_spatial_params_group()`
- **Update Method**: `_update_spatial_display()` - Formatting and validation
- **Signal Connection**: Each spinbox connected to `valueChanged` signal

## See Also

- `docs/SPATIAL_PARAMETERS_GUIDE.md` - User guide for spatial parameters
- `docs/SPATIAL_PARAMS_IMPLEMENTATION.md` - Technical implementation details
- `test_spatial_display.py` - Standalone test of the display
