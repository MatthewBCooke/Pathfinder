# Spatial Parameters Guide

## Overview

The Pathfinder GUI now includes controls for setting critical spatial parameters needed for accurate search strategy analysis. These parameters define the maze geometry and platform location.

## Required Parameters

### Pool/Maze Parameters
- **Pool Center X**: X-coordinate of the pool center (in pixels)
- **Pool Center Y**: Y-coordinate of the pool center (in pixels)
- **Pool Diameter**: Diameter of the pool (in pixels)

### Platform Parameters
- **Platform X**: X-coordinate of the platform center (in pixels)
- **Platform Y**: Y-coordinate of the platform center (in pixels)
- **Platform Diameter**: Diameter of the escape platform (in pixels)

## How to Use

### 1. Before Loading Data

You can set spatial parameters before loading your experiment file:

1. Launch Pathfinder GUI
2. Locate the **"Maze Geometry"** group in the left control panel
3. Enter your maze parameters:
   - Pool center coordinates (e.g., 250, 250 for center of 500x500 video)
   - Pool diameter (e.g., 400 pixels)
   - Platform position (e.g., 350, 150)
   - Platform diameter (e.g., 40 pixels)
4. Click **"Apply Geometry"**
5. Load your experiment file (CSV or Excel)
6. Run analysis

### 2. After Loading Data

You can also adjust parameters after loading:

1. Load your experiment file
2. Adjust the spatial parameters in the "Maze Geometry" group
3. Click **"Apply Geometry"** to update all trials
4. Run analysis with the new parameters

## Finding Your Values

### Determining Pool Center and Diameter

1. **Video Tracking Software**: Check your tracking software settings for pool configuration
2. **Video Frame**: Open a video frame in an image editor, measure the pool dimensions
3. **Trajectory Bounds**: The loader estimates these from trajectory data, but manual values are more accurate

### Determining Platform Location

1. **Experimental Protocol**: Refer to your experimental notes for platform coordinates
2. **Quadrant Information**: If using standard quadrant positions (NE, SE, SW, NW), calculate based on pool center
3. **Trajectory Endpoint**: Look at where animals successfully escape

### Example Values

For a typical Morris Water Maze video (500x500 pixels):

```
Pool Center X: 250 px
Pool Center Y: 250 px
Pool Diameter: 400 px
Platform X: 350 px (NE quadrant)
Platform Y: 150 px (NE quadrant)
Platform Diameter: 40 px
```

## Validation

The GUI validates your inputs:

- ✅ Pool diameter must be greater than platform diameter
- ✅ All values must be positive
- ⚠️ Warning if platform appears outside pool bounds

## Impact on Analysis

Accurate spatial parameters are **critical** for:

1. **Strategy Classification**: Determines thigmotaxis, focal search, directed search detection
2. **Metrics Calculation**: Affects distance metrics, heading errors, IPE calculations
3. **Quadrant Analysis**: Defines which quadrant contains the platform

### Metrics Affected

- Initial Path Error (IPE)
- Heading error
- Distance to platform
- Thigmotaxis detection
- Corridor analysis
- Quadrant transitions

## Supported File Formats

The spatial parameter system works with:

- ✅ **CSV files** (AnyMaze, Generic CSV)
- ✅ **Excel files** (.xlsx, .xls - Ethovision, custom formats)

## Troubleshooting

### "Invalid spatial parameters" error

**Problem**: Pool diameter is smaller than platform diameter

**Solution**: Ensure pool diameter > platform diameter (typically pool is 10x platform size)

### Analysis results seem incorrect

**Problem**: Spatial parameters don't match actual experimental setup

**Solution**:
1. Verify pool center matches video center
2. Check platform coordinates match experimental protocol
3. Ensure units are consistent (all in pixels or all in cm)

### Platform appears outside pool

**Warning**: Platform coordinates place it outside the pool boundary

**Solution**: Check platform X/Y coordinates are within pool radius from center

## Technical Details

### How It Works

1. User enters spatial parameters in GUI
2. Parameters stored in integration layer
3. When file is loaded, parameters applied to all trials
4. Analysis worker creates `MazeGeometry` from trial parameters
5. `TrialAnalyzer` uses geometry for metric calculations
6. Strategy classification uses geometry-based metrics

### Default Values

If you don't set spatial parameters, the system uses defaults:
- Pool center: 250, 250
- Pool diameter: 500
- Platform: 350, 150
- Platform diameter: 50

These may not match your setup - **always set parameters explicitly** for accurate analysis.

### Code Reference

- GUI Controls: `gui/control_panel.py` - `_create_spatial_params_group()`
- Parameter Storage: `gui/integration.py` - `spatial_params` dict
- Application Logic: `gui/integration.py` - `apply_spatial_parameters_to_trials()`
- Geometry Model: `pathfinder/core/geometry.py` - `MazeGeometry` class
- Analysis Usage: `pathfinder/analysis/trial_analyzer.py` - `TrialAnalyzer`

## Best Practices

1. **Record Parameters**: Keep a lab notebook with pool dimensions and platform positions
2. **Consistency**: Use the same parameters for all trials in an experiment
3. **Calibration**: Measure pool/platform in actual units, convert to pixels
4. **Validation**: Run a test trial and verify metrics look reasonable
5. **Documentation**: Save parameter values with your analysis results

## Example Workflow

```
1. Open Pathfinder GUI
2. Set Maze Geometry:
   - Pool Center X: 250
   - Pool Center Y: 250
   - Pool Diameter: 400
   - Platform X: 350
   - Platform Y: 150
   - Platform Diameter: 40
3. Click "Apply Geometry"
4. Load experiment file (test_data.csv)
5. Verify in log: "Applied maze geometry to N trials"
6. Run Analysis
7. Check results for accurate strategy classification
```

## Version History

- **v2.1** (2026-02-08): Added spatial parameter GUI controls
- **v2.0**: Initial GUI release with estimated parameters from trajectory

## See Also

- `pathfinder/core/geometry.py` - MazeGeometry class documentation
- `docs/IMPLEMENTATION_COMPLETE.md` - Full GUI implementation details
- `README.md` - General Pathfinder usage guide
