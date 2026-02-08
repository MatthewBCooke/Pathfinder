# Zone Geometry Fixes

**Date**: 2026-02-08
**Status**: ✅ Complete

## Overview

Critical fixes to maze visualization zone geometry based on Morris Water Maze behavioral analysis requirements.

## Issues Fixed

### 1. ✅ Chaining Zone - Corrected to Annulus

**Previous Implementation (INCORRECT)**:
- Circle centered on platform
- Extended from platform toward wall
- Variable radius based on platform position

**Current Implementation (CORRECT)**:
- **Annulus** (ring shape) centered on **pool center**
- Platform is **inside** the annulus
- Fixed percentage of pool radius (30-70%)
- Similar structure to thigmotaxis zone

**Why This Matters**:
- Chaining behavior: Animal swims in circular pattern at consistent distance from center
- Not centered on platform - platform happens to be within the chaining path
- Annulus represents the ring where chaining behavior occurs

**Code Location**: `gui/maze_visualization.py` lines 165-203

**Parameters**:
```python
self.chaining_zone_inner_percent = 30  # Inner radius: 30% of pool radius
self.chaining_zone_outer_percent = 70  # Outer radius: 70% of pool radius
```

**Drawing Logic**:
```python
# Calculate radii
chaining_inner_radius = pool_radius * (self.chaining_zone_inner_percent / 100.0)
chaining_outer_radius = pool_radius * (self.chaining_zone_outer_percent / 100.0)

# Draw outer circle (filled yellow semi-transparent)
painter.drawEllipse(pool_center, outer_radius, outer_radius)

# Draw inner circle (white fill to create ring/annulus)
painter.drawEllipse(pool_center, inner_radius, inner_radius)

# Draw boundary lines (yellow dashed)
painter.drawEllipse(pool_center, inner_radius, inner_radius)  # Inner boundary
painter.drawEllipse(pool_center, outer_radius, outer_radius)  # Outer boundary
```

### 2. ✅ Focal Search vs Directed Search - Both Now Visible

**Previous Implementation**:
- Only one zone labeled "directed search" (2.5× platform diameter)
- Ambiguous which strategy it represented

**Current Implementation**:
- **Two distinct zones** with different sizes and colors
- Clear distinction between focal and directed search behaviors

#### Focal Search Zone
- **Color**: Pink/Magenta dashed circle (🟣)
- **Size**: 1.5× platform diameter
- **Center**: Platform position
- **Behavior**: Tight, concentrated search immediately around platform location
- **Characteristics**: High turning rate, very localized, animal "knows" platform is nearby

#### Directed Search Zone
- **Color**: Cyan dashed circle (🔵)
- **Size**: 3.5× platform diameter
- **Center**: Platform position
- **Behavior**: Broader systematic search in general platform area
- **Characteristics**: Moderate path length, searching in correct quadrant/region

**Code Location**: `gui/maze_visualization.py` lines 204-224

**Visual Hierarchy** (centered on platform, smallest to largest):
1. Platform (red, solid)
2. Focal Search (pink dashed, 1.5×)
3. Directed Search (cyan dashed, 3.5×)

## Complete Zone Visualization

### All Zones (in order of appearance):

1. **Thigmotaxis Zone** (Gray annulus)
   - 20% from pool wall
   - Centered on pool center
   - Wall-hugging behavior

2. **Direct Swim Corridor** (Green wedge)
   - From pool center toward platform
   - ±15° angular width
   - Optimal swim path

3. **Chaining Zone** (Yellow annulus) ⭐ FIXED
   - 30-70% of pool radius
   - Centered on pool center
   - Circular search pattern

4. **Focal Search Zone** (Pink/Magenta circle) ⭐ NEW
   - 1.5× platform diameter
   - Centered on platform
   - Tight concentrated search

5. **Directed Search Zone** (Cyan circle) ⭐ UPDATED
   - 3.5× platform diameter
   - Centered on platform
   - Broad systematic search

6. **Pool Boundary** (Blue circle)
   - Main pool perimeter

7. **Platform** (Red circle)
   - Target location

## Behavioral Context

### Chaining Strategy
- **Definition**: Swimming in a circular pattern at a consistent distance from pool center
- **Zone**: Annulus at 30-70% of pool radius
- **Key**: Distance from center is relatively constant, NOT centered on platform
- **Example**: Animal swims in circles, occasionally crossing through platform area

### Focal Search Strategy
- **Definition**: Very tight, concentrated search in small area where platform should be
- **Zone**: Small circle (1.5× platform diameter) around platform
- **Key**: High turning rate, repeated coverage of same small area
- **Example**: Animal "knows" platform is here, searching intensely in tight loops

### Directed Search Strategy
- **Definition**: Systematic searching in the general platform region/quadrant
- **Zone**: Larger circle (3.5× platform diameter) around platform
- **Key**: Moderate path length, searching correct area but not as focused as focal
- **Example**: Animal knows general area, searching methodically in broader region

## Testing

### Visual Verification

```bash
source .venv/bin/activate
python3 pathfinder_gui.py
```

**Check these items**:
1. Go to "🔵 Maze Setup" tab
2. Verify **chaining zone is a ring** (not solid circle)
3. Verify chaining zone is **centered on pool center** (not platform)
4. Verify **two search zones** around platform (pink and cyan)
5. Verify focal (pink) is **smaller** than directed (cyan)
6. Adjust platform position - search zones move, chaining stays centered on pool
7. Adjust pool diameter - chaining scales, search zones stay relative to platform

### Expected Appearance

```
         Pool (blue circle)
    ┌──────────────────────────┐
    │   Thigmo (gray ring)     │
    │  ┌────────────────────┐  │
    │  │  Chaining (yellow) │  │
    │  │    ┌──────────┐    │  │
    │  │    │          │    │  │
    │  │    │  Platform│    │  │
    │  │    │   (red)  │    │  │
    │  │    │  Focal   │    │  │
    │  │    │  Directed│    │  │
    │  │    └──────────┘    │  │
    │  └────────────────────┘  │
    └──────────────────────────┘
```

### Legend Verification

Updated legend should show:
```
🔵 Pool  |  🔴 Platform  |  ⚫ Thigmotaxis  |  🟡 Chaining  |
🟣 Focal Search  |  🔵 Directed Search  |  🟢 Direct Corridor
```

## Code Changes Summary

### File: `gui/maze_visualization.py`

**Lines 29-31** - Updated parameters:
```python
self.thigmotaxis_zone_percent = 20
self.chaining_zone_inner_percent = 30  # New
self.chaining_zone_outer_percent = 70  # New
```

**Lines 165-203** - Chaining zone as annulus:
```python
# Draw chaining zone (annulus centered on pool center)
chaining_inner_radius = pool_radius * (self.chaining_zone_inner_percent / 100.0)
chaining_outer_radius = pool_radius * (self.chaining_zone_outer_percent / 100.0)
# ... drawing code creates ring shape
```

**Lines 204-224** - Focal and Directed search zones:
```python
# Focal search (small, tight)
focal_search_radius = self.platform_diameter * 1.5

# Directed search (broader)
directed_search_radius = self.platform_diameter * 3.5
```

**Lines 47-51** - Updated legend:
```python
legend = QLabel(
    "🔵 Pool  |  🔴 Platform  |  "
    "⚫ Thigmotaxis  |  🟡 Chaining  |  "
    "🟣 Focal Search  |  🔵 Directed Search  |  🟢 Direct Corridor"
)
```

## Impact on Analysis

### Strategy Classification
These zone fixes ensure accurate classification:

1. **Chaining**: Animal must swim within the 30-70% annulus ring
2. **Focal Search**: Animal must stay within 1.5× platform diameter
3. **Directed Search**: Animal must stay within 3.5× platform diameter but not focal

### Previously Ambiguous Cases
- Animals swimming in circles are now correctly identified as chaining
- Tight platform search is focal, not directed
- Broader platform area search is directed, not focal

## Future Enhancements

### Potential Improvements
- [ ] Make zone percentages/radii configurable in settings
- [ ] Add visual indicators for which zones animal entered during trial
- [ ] Show zone statistics (time spent in each zone)
- [ ] Export zone definitions with analysis results
- [ ] Add quadrant division lines for scanning strategy

## References

### Morris Water Maze Literature
- Chaining: Circular swimming pattern at consistent distance from center
- Focal: Tight concentrated search at platform location
- Directed: Systematic search in platform quadrant/area

### Similar Analysis Software
- **Ethovision**: Defines zones similarly but less granular
- **AnyMaze**: Static zone definitions, no visual preview
- **Pathfinder**: Now has accurate, visualized zone definitions ✅

## Summary

✅ **Chaining zone**: Now correctly implemented as annulus centered on pool center
✅ **Focal search**: New zone at 1.5× platform diameter (tight search)
✅ **Directed search**: Updated zone at 3.5× platform diameter (broad search)
✅ **Visual distinction**: Clear color coding and sizing for all zones
✅ **Behavioral accuracy**: Zones now match Morris Water Maze literature definitions

The maze visualization now accurately represents all search strategy zones according to established behavioral analysis protocols! 🎉
