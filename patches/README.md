# Pathfinder Diagnostic Patches

Quick fixes for common issues identified during diagnostic analysis.

## How to Apply Patches

```bash
cd /home/administrator/.openclaw/workspace/pathfinder-work

# Apply all patches at once
git apply patches/*.patch

# Or apply individually
git apply patches/01-add-debug-logging.patch
git apply patches/02-relax-thresholds.patch
git apply patches/03-heatmap-debug.patch

# If git apply fails, use patch directly
patch -p1 < patches/01-add-debug-logging.patch
```

## What Each Patch Does

### 01-add-debug-logging.patch
**Purpose:** Add detailed metric output to strategy classification

**Changes:**
- Adds debug prints to `trial_analyzer.py`
- Shows IPE, efficiency, platform zone %, wall %, quadrants, path length
- Prints to stderr so it doesn't interfere with normal output

**When to use:** When you want to see why trials are classified as they are

**Revert:** Just remove the debug block (marked with BEGIN/END comments)

---

### 02-relax-thresholds.patch
**Purpose:** Make strategy classification less strict

**Changes:**
- **Direct Swim:**
  - Removes strict distance constraint (was <30cm from platform)
  - Lowers efficiency threshold: 45% (was 50%)
- **Directed Search:**
  - Platform zone: 20% (was 30%)
  - Efficiency: 25% (was 30%)
- **Focal Search:**
  - Platform zone: 30% (was 40%)
- **Default parameters:**
  - distance_to_swim_max_val: 60 (was 30)
  - distance_to_plat_max_val: 60 (was 30)

**When to use:** When most trials are classified as "random search"

**Impact:** More trials will match Direct Swim, Directed Search, and Focal Search categories

**Revert:** Use `git checkout` on the modified files

---

### 03-heatmap-debug.patch  
**Purpose:** Diagnose why heatmap might show nothing

**Changes:**
- Adds debug output to `_plot_heatmap()`
- Shows trial counts, trajectory points, pool geometry
- Helps identify if problem is data filtering or rendering

**When to use:** When heatmap appears blank or empty

**Output shows:**
- Total trials in experiment
- Trials after filtering (day filter, etc.)
- First trial's trajectory point count
- Pool and platform geometry

**Revert:** Remove debug block (marked with BEGIN/END comments)

---

## Testing After Applying Patches

### Test Debug Logging
```bash
source venv/bin/activate
python3 pathfinder_gui.py 2>&1 | tee debug_output.log
# Load your data and run analysis
# Check debug_output.log for metric values
```

### Test Relaxed Thresholds
```bash
# After applying patch 02, run analysis again
# Compare classifications before and after
# Manually verify that new classifications match visual inspection
```

### Test Heatmap Debug
```bash
# After applying patch 03, load data and generate heatmap
# Check terminal for debug output
# Verify trial counts and geometry values
```

---

## Rollback Instructions

### Rollback Individual Patch
```bash
# If patch was applied with git apply
git checkout pathfinder/analysis/trial_analyzer.py  # Revert patch 01 or 02
git checkout gui/heatmap_widget.py                  # Revert patch 03
git checkout gui/defaults.py                        # Revert patch 02
```

### Rollback All Changes
```bash
# Discard all working directory changes
git reset --hard HEAD
```

### Create Backup First (Recommended)
```bash
# Before applying patches
git stash push -m "Before applying diagnostic patches"

# If you want to rollback
git stash pop
```

---

## Permanent Integration

If patches work well, commit them:

```bash
git add -A
git commit -m "Apply diagnostic patches: relaxed thresholds and debug logging

- Relaxed classification thresholds for better real-world data matching
- Added debug output for strategy classification metrics
- Added heatmap diagnostic logging
  
Based on diagnostic analysis 2026-02-08"

git push origin dev
```

Or create a separate diagnostic branch:

```bash
git checkout -b diagnostic-fixes
git add -A
git commit -m "Diagnostic fixes and debug logging"
git push origin diagnostic-fixes
```

---

## Support

If patches don't apply cleanly:
1. Check you're on the `dev` branch
2. Ensure working directory is clean (`git status`)
3. Try applying patches one at a time
4. Check line numbers if files have been modified
5. Manually apply the changes (see original files for context)

Created by Jerry (OpenClaw AI) - 2026-02-08
