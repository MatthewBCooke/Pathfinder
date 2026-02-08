# Maze Visualization Feature

## Overview

The Pathfinder GUI now includes a **visual maze setup display** that shows the pool, platform, and all analysis zones in real-time. This appears as the first tab ("🔵 Maze Setup") in the main display area.

## What It Shows

### Visual Elements

1. **🔵 Pool Circle** (Blue)
   - Shows the complete pool boundary
   - Size determined by Pool Diameter parameter
   - Centered at Pool Center coordinates

2. **🔴 Platform Circle** (Red)
   - Escape platform location and size
   - Position determined by Platform X/Y parameters
   - Size determined by Platform Diameter parameter

3. **⚫ Thigmotaxis Zone** (Gray Annulus)
   - Ring near the pool wall (default: 20% of radius from wall)
   - Used to detect wall-hugging behavior
   - Semi-transparent gray shading

4. **🟡 Chaining Zone** (Yellow Circle)
   - Area around platform for chaining detection
   - Default: 50% of platform diameter
   - Yellow dashed circle with transparent fill

5. **🟢 Direct Swim Corridor** (Green Wedge)
   - Angular corridor from pool center to platform
   - Default width: ±30° from platform direction
   - Light green transparent wedge
   - Used to detect direct swimming behavior

6. **Labels and Coordinates**
   - Pool diameter display
   - Platform diameter display
   - Zone labels (Thigmotaxis, Chaining, Direct Swim Corridor)
   - Current coordinates shown at bottom

## How to Use

### 1. Set Parameters

In the left control panel, "Maze Geometry" section:
```
Pool Center X:     [250.0] px
Pool Center Y:     [250.0] px
Pool Diameter:     [500.0] px
Platform X:        [350.0] px
Platform Y:        [150.0] px
Platform Diameter: [ 50.0] px
```

### 2. Apply and View

1. Click **"Apply Geometry"** button
2. Switch to **"🔵 Maze Setup"** tab
3. See real-time visual representation
4. Adjust parameters and click Apply again to update

### 3. Verify Setup

Use the visualization to:
- ✅ Confirm platform is within pool bounds
- ✅ Check platform position matches experimental setup
- ✅ Verify zones make sense for your maze configuration
- ✅ Ensure all dimensions are correct

## Visual Diagram Example

```
                    Thigmotaxis Zone
                   ╱                 ╲
          ┌───────●───────────────────●───────┐
          │      ╱                     ╲      │
          │     │    Direct Swim        │     │
          │     │      Corridor         │     │
Pool  ────┤     │    (Green Wedge)      │     ├──── Pool
Boundary  │     │                       │     │     Boundary
(Blue)    │      ╲                     ╱      │     (Blue)
          │   ●───◉────────────────◉───●      │
          │       │   Platform    │           │
          │       │   (Red)       │           │
          │       └───────────────┘           │
          │     Chaining Zone                 │
          │     (Yellow Circle)               │
          └───────────────────────────────────┘

          ● = Pool Center (black dot)
          ◉ = Platform
```

## Auto-Scaling

The visualization automatically scales to fit the widget:
- Maintains aspect ratio
- Centers the pool in the display
- Adds margins for labels
- Scales all zones proportionally

## Real-Time Updates

Changes to spatial parameters update the visualization immediately when you click "Apply Geometry":

```python
# In the integration layer:
control_panel.spatial_params_changed -> maze_viz.update_parameters()
```

## Zone Parameters

### Thigmotaxis Zone
- **Default**: 20% of pool radius from wall
- **Purpose**: Detect wall-hugging behavior
- **Calculation**: Annulus from (radius - 20%) to radius

### Chaining Zone
- **Default**: 50% of platform diameter
- **Purpose**: Detect repeated paths to platform area
- **Calculation**: Circle around platform with radius = 0.5 × platform_diameter

### Direct Swim Corridor
- **Default**: ±30° from platform direction
- **Purpose**: Detect straight swimming to platform
- **Calculation**: Wedge from pool center with angle to platform ± 30°

## Comparison to Original Version

### Original Pathfinder
- Had visual maze display in Tkinter
- Showed pool, platform, zones
- Static display after parameter entry

### New Pathfinder
- Full PyQt5 visualization with anti-aliasing
- First tab in main display area
- Real-time updates when parameters change
- High-quality rendering with transparency
- Labeled zones and dimensions
- Color-coded elements

## Testing the Visualization

### Standalone Test
```bash
cd "/Users/matthewcooke/Documents/UBC/Pathfinder/Pathfinder 2/Pathfinder"
source .venv/bin/activate
python3 test_maze_viz.py
```

### Full Application
```bash
python3 pathfinder_gui.py
```

Then:
1. Look at the "🔵 Maze Setup" tab (first tab)
2. Adjust parameters in left control panel
3. Click "Apply Geometry"
4. Watch visualization update

## Implementation Details

### File Location
`gui/maze_visualization.py` - Complete visualization widget

### Key Methods
- `update_parameters(params)` - Update and redraw with new parameters
- `paintEvent(event)` - QPainter rendering logic
- Coordinate transformation: maze coords → widget coords
- Automatic scaling to fit available space

### Drawing Order
1. Thigmotaxis zone (gray annulus)
2. Direct swim corridor (green wedge)
3. Chaining zone (yellow circle)
4. Pool boundary (blue circle)
5. Platform (red circle)
6. Pool center marker (black dot)
7. Labels and text

### Coordinate System
- **Maze coordinates**: Origin at pool center, X right, Y down (typical tracking software)
- **Widget coordinates**: Origin at top-left, X right, Y down (PyQt convention)
- Transformation handles scaling and translation automatically

## Customization

### Adjusting Zone Sizes

Edit `gui/maze_visualization.py`:

```python
class MazeVisualizationWidget(QWidget):
    def __init__(self, parent=None):
        # ...
        self.thigmotaxis_zone_percent = 20  # Change this (0-100)
        self.chaining_radius_percent = 50    # Change this (0-100)
```

### Changing Colors

In `paintEvent()` method:

```python
# Pool
QColor(0, 100, 200)  # Blue - change RGB values

# Platform
QColor(200, 0, 0)     # Red - change RGB values

# Thigmotaxis zone
QColor(200, 200, 200, 100)  # Gray with transparency

# Chaining zone
QColor(255, 200, 0)   # Yellow - change RGB values

# Corridor
QColor(100, 255, 100, 80)  # Green with transparency
```

### Adding More Zones

To add additional zones:
1. Calculate zone dimensions in `paintEvent()`
2. Use `QPainter` to draw (circles, arcs, polygons)
3. Add to drawing order before labels
4. Update legend in `_init_ui()`

## Troubleshooting

### Visualization doesn't show
- Check that you're on the "🔵 Maze Setup" tab
- Verify parameters have been set and "Apply Geometry" clicked
- Check console for errors

### Platform appears outside pool
- Adjust Platform X/Y to be closer to Pool Center
- Ensure distance from center < (pool_radius - platform_radius)
- Red circle should be fully inside blue circle

### Zones look wrong
- Verify pool diameter is correct (not too small/large)
- Check platform diameter is reasonable (typically 1/10 pool size)
- Adjust thigmotaxis_zone_percent if needed

### Display is too small/large
- Resize the main window - visualization auto-scales
- Make window larger for better detail
- Visualization maintains proper proportions

## Future Enhancements

Potential additions:
- **Trajectory overlay**: Show trial paths on the maze
- **Quadrant lines**: Draw 4 quadrants
- **Start position markers**: Show typical start locations
- **Annulus-40 visualization**: Show annulus scoring zones
- **Export image**: Save visualization as PNG
- **Interactive editing**: Click to set platform position
- **3D view**: Perspective visualization

## Related Files

- `gui/maze_visualization.py` - Main visualization widget
- `gui/main_window.py:66-74` - Tab integration
- `gui/integration.py:322-324` - Signal connections
- `test_maze_viz.py` - Standalone test script

## See Also

- `docs/SPATIAL_PARAMETERS_GUIDE.md` - How to set parameters
- `docs/SPATIAL_PARAMS_IMPLEMENTATION.md` - Technical implementation
- `README.md` - General Pathfinder usage
