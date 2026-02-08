# Pathfinder GUI v2.0

Modern PyQt5-based interface for Morris Water Maze search strategy analysis.

## Features

✨ **Modern GUI** - Clean PyQt5 interface with resizable panels  
📊 **Results Table** - Trial-by-trial analysis with sortable columns  
📈 **Summary Statistics** - Experiment-level metrics and learning curves  
🗺️ **Heatmap Visualization** - Trajectory plots and occupancy maps  
⚙️ **Configurable Parameters** - 35+ analysis parameters with defaults  
🔄 **Background Processing** - Non-blocking file loading and analysis  
💾 **Export Capability** - CSV/Excel export of results  
✏️ **Manual Classification** - Override strategy detection when needed  

## Installation

### Requirements

- Python 3.10+
- PyQt5
- pandas
- numpy
- scipy
- matplotlib
- pydantic

### Setup

```bash
# Clone repository
cd pathfinder_gui

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python pathfinder_gui.py
```

## Usage

### Quick Start

1. **Load Experiment File**
   - Click "📁 Load Experiment File" button
   - Select your tracking data (Excel/CSV)
   - Supported formats: Ethovision, AnyMaze, Generic CSV

2. **Run Analysis**
   - Click "▶ Run Analysis" button
   - Progress updates will show trial-by-trial processing
   - Results appear in the Results Table tab

3. **Review Results**
   - **Results Table**: View all trials with detected strategies
   - **Summary**: See experiment-level statistics and learning trends
   - **Heatmap**: Visualize trajectory patterns

4. **Manual Adjustments** (optional)
   - Double-click a trial row to manually classify
   - Or right-click → "Manual Classification"

5. **Export**
   - Click "💾 Export Results" to save as CSV/Excel

### File Formats

#### Ethovision (Excel)
- Must contain columns: `Trial time`, `X center`, `Y center`
- Optional: `Trial` column for multi-trial files

#### AnyMaze (CSV)
- Must contain columns: `Time`, `X`, `Y`
- Optional: `Trial` column for multi-trial files

#### Generic CSV
- Auto-detects columns matching: time/t, x/x_pos, y/y_pos
- Case-insensitive matching

## Project Structure

```
pathfinder_gui/
├── gui/                           # GUI layer (PyQt5)
│   ├── __init__.py
│   ├── main_window.py            # Main application window
│   ├── integration.py            # Business logic & signal/slot wiring
│   ├── control_panel.py          # Left sidebar controls
│   ├── results_table.py          # Results table widget
│   ├── summary_widget.py         # Summary statistics widget
│   ├── heatmap_widget.py         # Trajectory visualization widget
│   └── defaults.py               # Default parameter values
│
├── pathfinder/                    # Analysis backend (pure Python)
│   ├── core/                      # Domain models
│   │   ├── models.py              # Pydantic data models
│   │   └── geometry.py            # Maze geometry utilities
│   ├── io/                        # File I/O
│   │   └── loaders.py             # Format detection & loading
│   └── analysis/                  # Analysis logic
│       └── trial_analyzer.py      # Strategy detection engine
│
├── pathfinder_gui.py             # Main entry point
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Architecture

### Separation of Concerns

**GUI Layer** (`gui/`)
- PyQt5 widgets
- Signal/slot connections
- User interaction handling
- No analysis logic

**Analysis Layer** (`pathfinder/`)
- Pure Python models
- Strategy detection algorithms
- File parsing
- No GUI dependencies

**Integration Layer** (`gui/integration.py`)
- Connects GUI to analysis backend
- Worker threads for long operations
- State management
- Error handling

### Signal/Slot Connections

All UI interactions use Qt's signal/slot pattern:

- `ControlPanel.load_clicked` → `Integration.on_load_file()`
- `ControlPanel.analyze_clicked` → `Integration.run_analysis()`
- `ResultsTable.manual_classification_requested` → `Integration.on_manual_classification()`
- `FileLoadWorker.finished` → `Integration._on_file_load_finished()`
- `AnalysisWorker.progress` → `ControlPanel.set_progress()`

## Configuration

### Analysis Parameters

Edit `gui/defaults.py` to change default parameters:

```python
DEFAULT_PARAMETERS = Parameters(
    name="Standard Morris Water Maze",
    ipe_max_val=125.0,                # Initial path error threshold
    heading_max_val=40.0,             # Heading error threshold
    distance_to_swim_max_val=30.0,   # Direct swim distance threshold
    # ... 30+ more parameters
)
```

### UI Customization

Adjust window sizes, colors, fonts in respective widget files:

- `main_window.py` - Window dimensions, menu layout
- `control_panel.py` - Button styles, panel width
- `results_table.py` - Column widths, colors
- `heatmap_widget.py` - Visualization settings

## Search Strategies

The analyzer detects 8 search strategies:

1. **Direct Swim** - Straight path to platform (spatial memory)
2. **Directed Search** - Focused search near platform area
3. **Focal Search** - Concentrated search in platform region
4. **Spatial Indirect** - Some spatial knowledge, indirect approach
5. **Chaining** - Repeated similar path from start location
6. **Scanning** - Systematic coverage of pool
7. **Thigmotaxis** - Wall-hugging behavior
8. **Random Search** - No apparent strategy

## Development

### Adding a New Strategy

1. Add enum to `pathfinder/core/models.py`:
   ```python
   class SearchStrategy(str, Enum):
       NEW_STRATEGY = "new_strategy"
   ```

2. Add detection logic to `pathfinder/analysis/trial_analyzer.py`:
   ```python
   def _detect_strategy(self, metrics):
       if meets_new_strategy_criteria:
           return SearchStrategy.NEW_STRATEGY, confidence
   ```

3. Add color to `gui/results_table.py` and `gui/summary_widget.py`

### Adding a New File Format

1. Add enum to `pathfinder/io/loaders.py`:
   ```python
   class SoftwareType(str, Enum):
       NEW_SOFTWARE = "NewSoftware"
   ```

2. Implement loader function:
   ```python
   def _load_new_software(file_path, parameters):
       # Parse file
       # Return Experiment object
   ```

3. Update `load_experiment()` dispatcher

## Troubleshooting

### "No module named 'PyQt5'"
```bash
pip install PyQt5
```

### "Could not find required columns"
Your CSV doesn't have standard column names. Edit `pathfinder/io/loaders.py` `_find_column()` to add your column names to the candidates list.

### Analysis hangs
Check `pathfinder.log` for errors. Ensure your data file has valid numeric X/Y/Time values.

### Import errors
Make sure you're running from the `pathfinder_gui` directory:
```bash
cd pathfinder_gui
python pathfinder_gui.py
```

## Credits

**Original Pathfinder**: Johns Lab  
**Modernization**: 2026 refactoring with PyQt5  
**License**: [Original license terms apply]  

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Full settings dialog for all 35 parameters
- [ ] Database persistence (replace in-memory storage)
- [ ] Advanced heatmap options (kernel density, multiple trials overlay)
- [ ] Export to additional formats (JSON, MATLAB .mat)
- [ ] Batch processing mode for multiple experiments
- [ ] Plugin system for custom strategies
- [ ] Integration with statistical analysis tools

## Support

For issues, questions, or feature requests:
- GitHub Issues: [MatthewBCooke/Pathfinder](https://github.com/MatthewBCooke/Pathfinder)
- Email: [Contact through GitHub]

---

**Version**: 2.0.0  
**Last Updated**: February 2026
