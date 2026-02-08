# Pathfinder GUI - Quick Start Guide

## What Was Delivered

A **working Pathfinder GUI** with:
- ✅ Auto-detecting CSV loader (tries 4 formats)
- ✅ All buttons wired up and functional
- ✅ Background workers (GUI stays responsive)
- ✅ Real error messages (no more "Loading..." hang)
- ✅ Results display and CSV export

## Installation

```bash
cd /tmp/Pathfinder

# Install dependencies
pip install PyQt6 numpy scipy pandas openpyxl

# Or if using conda:
conda install pyqt numpy scipy pandas openpyxl
```

## Running the GUI

```bash
python test_gui_simple.py
```

This launches the working GUI application.

## Usage

### 1. Load an Experiment
- Click **"📂 Load Experiment"** button
- Select any CSV or Excel file
- Format is auto-detected:
  - AnyMaze (Time as HH:MM:SS, X, Y)
  - WaterMaze (Interleaved columns)
  - Ethovision (Excel with metadata)
  - Basic (any time/x/y columns)
- Success: Shows trial count, enables Analyze button
- Failure: Shows clear error with tried formats

### 2. Configure Settings (Optional)
- Click **"⚙️ Settings"** button
- Adjust parameters:
  - Pool diameter
  - Platform diameter
  - Platform position (x, y)
- Click OK to save

### 3. Run Analysis
- Click **"▶️ Analyze"** button
- Watch progress bar update
- Wait for completion
- View results in:
  - **Results Table** tab: Trial-by-trial data
  - **Summary** tab: Statistics & strategy distribution

### 4. Export Results
- Menu: **File → Save Results**
- Choose location
- Saves CSV with all metrics

## Test Data

### Sample File Included
```bash
# Already created for you:
test_data_simple.csv
```

Load this to test the system.

### Create Your Own Test Data

**AnyMaze format:**
```csv
Time,X,Y
0:00:00,10.5,20.3
0:00:01,15.2,25.8
0:00:02,20.1,30.5
```

**Basic format (any column names with time/x/y keywords):**
```csv
time,x,y
0.0,10.5,20.3
1.0,15.2,25.8
2.0,20.1,30.5
```

**WaterMaze format:**
```csv
Animal1,Date,Time,Animal2,Date,Time
Mouse1,01/01/2026,10:00 AM,,,
,,,,,
10.5,20.3,0.0,15.2,25.8,0.0
15.2,25.8,1.0,20.1,30.5,1.0
```

All formats auto-detect!

## Files You Need to Know About

### Entry Point:
- **`test_gui_simple.py`** - Launch this to run the GUI

### Core Implementation:
- **`gui/simple_loader.py`** - Auto-detecting CSV loader
- **`gui/integration.py`** - Orchestration (wires everything up)
- **`gui/main_window.py`** - UI definition (buttons, tables, displays)

### Documentation:
- **`QUICK_START.md`** - This file (how to run it)
- **`GUI_WORKING_IMPLEMENTATION.md`** - Detailed technical docs
- **`IMPLEMENTATION_COMPLETE.md`** - Task completion summary

### Analysis Engine:
- **`pathfinder/`** - Core analysis package (unchanged)
- **`pathfinder/analysis.py`** - Metrics and classification
- **`pathfinder/io.py`** - Original file loaders
- **`pathfinder/models.py`** - Data structures

## Troubleshooting

### "No module named 'PyQt6'"
```bash
pip install PyQt6
```

### "No module named 'numpy'"
```bash
pip install numpy scipy
```

### "No module named 'pandas'"
- **For CSV files:** Not required! CSV loading works without pandas.
- **For Excel files:** Install with `pip install pandas openpyxl`

### "No valid trials found in file"
- Check CSV has columns with time, x, y data
- Ensure data rows contain valid numbers (not empty/NaN)
- Open file in text editor to verify structure

### "Could not parse file"
- Error message shows which formats were tried
- Verify file is CSV or Excel (.csv, .xlsx)
- Check for encoding issues (should be UTF-8)

### GUI freezes
- This is fixed! Long operations run in worker threads.
- If it still happens, check terminal for error messages.

### Analysis fails
- Verify parameters are valid:
  - Platform must be inside pool
  - Coordinates should be positive
- Check trials have enough datapoints (need >2 points)
- Look for NaN or infinite values

## What's Different from Before

### ❌ Before (Placeholder):
- Buttons showed "will be implemented in Phase 2"
- Loading got stuck on "Loading..." with no feedback
- Required exact CSV format
- No error messages

### ✅ Now (Working):
- All buttons functional
- Auto-detects CSV format (tries 4 types)
- Clear error messages
- Background workers keep GUI responsive
- Results display in table
- CSV export works

## Next Steps (Optional Enhancements)

The core functionality works. Future improvements could include:

- [ ] Heatmap visualization (matplotlib integration)
- [ ] Directory loading (batch process multiple files)
- [ ] Advanced settings dialog (all parameters)
- [ ] ROI (Region of Interest) manager
- [ ] Custom format definition wizard
- [ ] Parallel processing for multiple trials

But for now: **Everything you asked for works!**

## Getting Help

**Check the docs:**
- `GUI_WORKING_IMPLEMENTATION.md` - Technical details
- `IMPLEMENTATION_COMPLETE.md` - What was built

**Test with sample data:**
```bash
python test_gui_simple.py
# Then load: test_data_simple.csv
```

**Verify installation:**
```bash
python -c "import PyQt6; import numpy; import pathfinder; print('✓ All imports work')"
```

## Summary

You now have a **fully functional** Pathfinder GUI that:
- Loads CSV files with auto-detection
- Runs analysis in background (responsive UI)
- Displays results in table
- Exports to CSV
- Shows real error messages

**Just run:** `python test_gui_simple.py`

Enjoy! 🎉
