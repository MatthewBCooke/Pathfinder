# Pathfinder GUI - Quick Troubleshooting Guide

**Version:** 2.0  
**Last Updated:** 2026-02-07

---

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install PyQt5 pandas openpyxl pydantic
   ```

2. **Run the application:**
   ```bash
   python3 pathfinder_gui.py
   ```

3. **Load a file:** Click "📁 Load Experiment File" → Select CSV/Excel file

4. **Run analysis:** Click "▶ Run Analysis"

5. **View results:** Check the Results Table, Summary, and Heatmap tabs

---

## ❗ Common Errors

### Error: "AttributeError: 'AnalysisResult' object has no attribute 'strategy'"

**Symptom:** Analysis crashes when processing trials  
**Cause:** Old code used `result.strategy` instead of `result.detected_strategy`  
**Fix:** This should be fixed in the latest version (line 146 of integration.py)  
**Verify:**
```bash
grep "result.strategy" gui/integration.py
# Should NOT find any matches
grep "result.detected_strategy" gui/integration.py
# Should find: trial.search_strategy = result.detected_strategy
```

---

### Error: "ModuleNotFoundError: No module named 'pathfinder'"

**Symptom:** Import errors when starting the application  
**Cause:** Running from wrong directory or missing __init__.py files  
**Fix:**
```bash
# Make sure you're in the pathfinder_gui directory
cd /path/to/pathfinder_gui

# Check that all __init__.py files exist
find . -name "__init__.py"
# Should show:
#   ./gui/__init__.py
#   ./pathfinder/__init__.py
#   ./pathfinder/core/__init__.py
#   ./pathfinder/io/__init__.py
#   ./pathfinder/analysis/__init__.py

# Run from project root
python3 pathfinder_gui.py
```

---

### Error: "Could not find required columns" when loading CSV

**Symptom:** File load fails with column detection error  
**Cause:** CSV doesn't have expected column names  
**Solution:**
1. CSV must have at minimum: `time`, `x`, `y` columns (case-insensitive)
2. Optional columns: `trial`, `trial number`, `day`
3. Example valid CSV:
   ```csv
   Trial,Time,X,Y
   1,0.0,100.5,200.3
   1,0.1,101.2,201.1
   ```

**Supported column name variations:**
- Time: `time`, `t`, `timestamp`, `trial time`
- X: `x`, `x center`, `x position`, `x_pos`
- Y: `y`, `y center`, `y position`, `y_pos`
- Trial: `trial`, `trial number`, `trial_num`

---

### Error: "No trials found in file"

**Symptom:** File loads but shows 0 trials  
**Cause:** Data format issue or parsing error  
**Troubleshooting:**
1. Check that CSV has data rows (not just headers)
2. Verify columns are properly formatted (numbers, not text)
3. Check for empty rows at the top of the file
4. Look at the terminal/console for warning messages

---

### Error: Settings dialog crashes

**Symptom:** Clicking "⚙ Analysis Settings" causes error  
**Cause:** Missing settings_dialog.py import  
**Fix:** Ensure `gui/settings_dialog.py` exists and is imported in `integration.py`

---

### Error: Export fails

**Symptom:** "Export Error" dialog appears  
**Possible causes:**
1. **Permission denied:** Try saving to a different location
2. **File in use:** Close the file if it's open in Excel
3. **Missing dependencies:** Install openpyxl for Excel export
   ```bash
   pip install openpyxl
   ```

---

## 🔧 Installation Issues

### PyQt5 installation fails on Linux

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5

# Fedora
sudo dnf install python3-qt5

# Or use pip with system packages
pip install --user PyQt5
```

### Pandas/openpyxl installation

```bash
pip install pandas openpyxl
```

---

## 🐛 Debug Mode

**Enable detailed logging:**

Edit `gui/integration.py` (line ~23):
```python
# Change from:
logging.basicConfig(level=logging.INFO)

# To:
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Check logs:**
- Logs appear in the terminal/console where you launched the app
- Look for ERROR or WARNING messages
- Copy the full stack trace when reporting bugs

---

## 📊 Data Format Examples

### Minimal CSV (Generic format)
```csv
time,x,y
0.0,150,200
0.1,151,201
0.2,152,203
```

### CSV with trials
```csv
trial,day,time,x,y
1,1,0.0,150,200
1,1,0.1,151,201
2,1,0.0,160,210
```

### Ethovision Excel format
- Must have columns: `Trial time` or `Recording time`, `X center` or `X`, `Y center` or `Y`
- Optional: `Trial` column for multi-trial files

---

## ⚠️ Known Limitations

1. **Heatmap widget:** Currently placeholder - implementation pending
2. **Large files:** Files with >10,000 data points per trial may be slow
3. **Platform detection:** Pool/platform geometry is auto-detected from trajectory bounds (may be inaccurate if animal doesn't explore full pool)
4. **Strategy confidence:** Confidence scores are estimates based on metric thresholds

---

## 📧 Getting Help

**Before reporting a bug:**
1. Enable debug logging (see above)
2. Try with a minimal test file (10-20 data points)
3. Check this troubleshooting guide
4. Note exact error message and steps to reproduce

**Report bugs with:**
- Python version: `python3 --version`
- PyQt5 version: `pip show PyQt5`
- Operating system
- Sample data file (if possible)
- Full error message/stack trace
- Steps to reproduce

---

## ✅ Verification Checklist

**After installation, test that:**

- [ ] Application launches without errors
- [ ] Can load a CSV file
- [ ] File appears in "File Operations" panel
- [ ] "Run Analysis" button becomes enabled
- [ ] Analysis completes without crashes
- [ ] Results table shows classified trials
- [ ] Can manually reclassify a trial (double-click row)
- [ ] Can export to CSV
- [ ] Can open Settings dialog
- [ ] Settings changes are applied

**Test CSV for verification:**
```csv
trial,day,time,x,y
1,1,0.0,100,100
1,1,1.0,110,110
1,1,2.0,120,120
1,1,3.0,130,130
2,1,0.0,50,50
2,1,1.0,60,55
2,1,2.0,70,60
2,1,3.0,80,65
```

Save this as `test_data.csv` and try loading it.

---

## 🔄 Reset to Clean State

**If everything is broken:**

```bash
# Remove any cached files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Reinstall dependencies
pip install --force-reinstall PyQt5 pandas openpyxl pydantic

# Try running again
python3 pathfinder_gui.py
```

---

## 🆘 Emergency Contact

If nothing works:
1. Check AUDIT_REPORT.md for known issues
2. Review the code architecture in README.md
3. Compare your files against the reference implementation
4. Start with a minimal test case

**Last resort:** Delete and re-clone the repository, start fresh.
