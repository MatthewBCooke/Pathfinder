# Phase 2: PyQt6 GUI Architecture Design

**Project:** Pathfinder - Morris Water Maze Analysis  
**Phase:** GUI Modernization (tkinter → PyQt6)  
**Author:** OpenClaw Agent  
**Date:** 2026-02-07  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Module Structure](#module-structure)
4. [Class Hierarchy](#class-hierarchy)
5. [Window Hierarchy](#window-hierarchy)
6. [Signal/Slot Workflow](#signalslot-workflow)
7. [Widget Mapping (tkinter → PyQt6)](#widget-mapping-tkinter--pyqt6)
8. [Threading Strategy](#threading-strategy)
9. [Migration Checklist](#migration-checklist)
10. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

### Current State
- **Pathfinder.py**: ~2563 lines of tkinter GUI mixed with analysis logic
- **mainClass**: Handles file loading, parameter entry, analysis execution, result display, heatmap visualization
- **Analysis logic**: Successfully extracted to `pathfinder/` package (models, io, analysis, entropy)

### Target State
- **Clean separation**: GUI code completely separate from analysis logic
- **Modern UI**: PyQt6 with responsive layouts, themes, and better UX
- **Maintainability**: Modular structure with clear responsibilities
- **Extensibility**: Easy to add new features (plugins, custom visualizations)

### Key Benefits of PyQt6
- **Rich widget library**: QTableView, QGraphicsView, QDockWidget, QSplitter
- **Model/View architecture**: Separation between data and presentation
- **Signal/Slot system**: Type-safe, declarative event handling
- **Built-in threading**: QThread, QRunnable for non-blocking operations
- **Styling**: CSS-like stylesheets, dark mode, themes
- **Cross-platform**: Consistent look across Windows, macOS, Linux

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                  (Application Entry Point)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 gui/main_window.py                          │
│                  (MainWindow: QMainWindow)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Menu Bar  │  Tool Bar  │  Status Bar               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Central Widget (QSplitter)               │  │
│  │  ┌────────────────────┬──────────────────────────┐   │  │
│  │  │  Control Panel     │  Results/Visualization   │   │  │
│  │  │  (QDockWidget)     │  (QTabWidget)            │   │  │
│  │  │  - File Selection  │  - Table View            │   │  │
│  │  │  - Parameters      │  - Heatmap Canvas        │   │  │
│  │  │  - ROI Management  │  - Plots                 │   │  │
│  │  │  - Run Button      │  - Log Output            │   │  │
│  │  └────────────────────┴──────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────┬──────────────────┬───────────────┬──────────┘
               │                  │               │
               ▼                  ▼               ▼
    ┌──────────────────┐  ┌─────────────┐  ┌────────────────┐
    │  gui/dialogs.py  │  │gui/widgets  │  │ gui/workers.py │
    │  - Settings      │  │- Heatmap    │  │ - QThread for  │
    │  - File Import   │  │- ROI Editor │  │   Analysis     │
    │  - Manual Strat  │  │- Plot Canvas│  │ - Progress     │
    │  - ROI Manager   │  │- Results Tbl│  │   Reporting    │
    └──────────────────┘  └─────────────┘  └────────────────┘
                                  │
                                  ▼
                        ┌──────────────────────┐
                        │  pathfinder package  │
                        │  (Pure Python API)   │
                        │  - analysis.py       │
                        │  - models.py         │
                        │  - io.py             │
                        │  - entropy.py        │
                        └──────────────────────┘
```

### Design Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Dependency Inversion**: GUI depends on pathfinder API, not vice versa
3. **Event-Driven**: Signal/slot pattern for all user interactions
4. **Non-Blocking**: Long operations run in QThread
5. **Testable**: Business logic in pathfinder, GUI code minimal and testable
6. **Themeable**: Centralized styling in `gui/styles.py`

---

## Module Structure

```
pathfinder/
├── main.py                      # Application entry point
├── gui/
│   ├── __init__.py
│   ├── main_window.py          # MainWindow (QMainWindow)
│   ├── dialogs.py              # All dialog windows
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── heatmap_widget.py   # Custom heatmap visualization
│   │   ├── results_table.py    # Results table with model/view
│   │   ├── roi_editor.py       # ROI (Region of Interest) editor
│   │   ├── plot_canvas.py      # Matplotlib integration
│   │   └── control_panel.py    # Left-side parameter controls
│   ├── workers.py              # QThread workers for background tasks
│   ├── models.py               # Qt data models (QAbstractTableModel)
│   ├── styles.py               # Centralized styling/themes
│   └── resources/
│       ├── icons/              # Application icons
│       └── qss/                # Qt Style Sheets
├── pathfinder/                 # Pure analysis package (already exists)
│   ├── __init__.py
│   ├── analysis.py
│   ├── models.py
│   ├── io.py
│   ├── types.py
│   └── entropy.py
└── tests/
    ├── test_gui/
    │   ├── test_main_window.py
    │   └── test_widgets.py
    └── test_pathfinder/        # Already exists
```

### Module Responsibilities

#### `main.py`
- Initialize QApplication
- Set application metadata (name, version, organization)
- Apply global styles/theme
- Create and show MainWindow
- Handle command-line arguments (optional: file path)

#### `gui/main_window.py`
- **MainWindow** class (inherits QMainWindow)
- Menu bar setup (File, Edit, Window, Help)
- Toolbar with common actions
- Status bar with progress indicator
- Central widget layout (splitter, dock widgets)
- Coordinate between control panel and results display
- Handle file open/save actions
- Manage application state

#### `gui/dialogs.py`
- **SettingsDialog**: Parameter configuration
- **FileImportDialog**: Advanced file selection with preview
- **ManualStrategyDialog**: Manual strategy classification UI
- **ROIManagerDialog**: Manage multiple regions of interest
- **AboutDialog**: Application info, version, credits
- **HeatmapConfigDialog**: Heatmap generation settings

#### `gui/widgets/`
- **HeatmapWidget** (QWidget + matplotlib): Interactive heatmap display
- **ResultsTableWidget** (QTableView): Display analysis results with sorting/filtering
- **ROIEditorWidget** (QGraphicsView): Visual editor for ROI placement
- **PlotCanvasWidget** (QWidget): Embedded matplotlib plots
- **ControlPanelWidget** (QWidget): Left-side parameter controls

#### `gui/workers.py`
- **AnalysisWorker** (QThread): Run analysis in background
- **HeatmapWorker** (QThread): Generate heatmaps without blocking UI
- **FileLoaderWorker** (QThread): Load large files asynchronously
- Progress reporting via signals

#### `gui/models.py`
- **ResultsTableModel** (QAbstractTableModel): Data model for results table
- **ROIListModel** (QAbstractListModel): Model for ROI list
- Clean separation between data and presentation

#### `gui/styles.py`
- Centralized theme definitions
- Dark mode detection and application
- Platform-specific styling
- Common color palettes, fonts, spacing

---

## Class Hierarchy

### Main Window

```python
class MainWindow(QMainWindow):
    """
    Main application window for Pathfinder.
    
    Signals:
        file_loaded: Emitted when files are loaded (str: directory path)
        analysis_started: Emitted when analysis begins
        analysis_completed: Emitted with results (dict)
        parameters_changed: Emitted when parameters are modified (Parameters)
    """
    
    # Signals
    file_loaded = pyqtSignal(str)
    analysis_started = pyqtSignal()
    analysis_completed = pyqtSignal(dict)
    parameters_changed = pyqtSignal(object)  # Parameters object
    
    def __init__(self):
        # Initialize UI components
        # Setup menu bar
        # Setup toolbar
        # Setup central widget
        # Setup dock widgets
        # Connect signals/slots
        
    # Menu actions
    def open_file(self)
    def open_directory(self)
    def generate_heatmap(self)
    def show_settings(self)
    def quit_application(self)
    
    # Analysis workflow
    def start_analysis(self)
    def on_analysis_complete(self, results: dict)
    def on_analysis_error(self, error: str)
    
    # UI updates
    def update_status(self, message: str)
    def update_progress(self, value: int, maximum: int)
```

### Dialogs

```python
class SettingsDialog(QDialog):
    """Parameter configuration dialog."""
    
    parameters_updated = pyqtSignal(object)  # Parameters object
    
    def __init__(self, current_params: Parameters):
        # Load current parameters
        # Build form UI
        # Validation
        
    def get_parameters(self) -> Parameters
    def validate_inputs(self) -> bool
    def restore_defaults(self)


class ManualStrategyDialog(QDialog):
    """Manual strategy classification for individual trials."""
    
    strategy_classified = pyqtSignal(str, str)  # (trial_id, strategy)
    
    def __init__(self, trial_data):
        # Display trial visualization
        # Radio buttons for strategy selection
        # Navigation (prev/next trial)
        
    def get_classification(self) -> str
    def show_next_trial(self)
    def show_previous_trial(self)


class ROIManagerDialog(QDialog):
    """Manage multiple regions of interest."""
    
    rois_updated = pyqtSignal(list)  # List of (position, diameter) tuples
    
    def __init__(self, current_rois: list):
        # ROI list view
        # Add/remove/edit controls
        # Visual editor preview
        
    def add_roi(self)
    def remove_roi(self, index: int)
    def get_rois(self) -> list


class HeatmapConfigDialog(QDialog):
    """Configure heatmap generation settings."""
    
    config_confirmed = pyqtSignal(dict)
    
    def __init__(self, defaults: dict):
        # Grid size
        # Color map selection
        # Day/trial filters
        # Max value (auto/manual)
        
    def get_config(self) -> dict
```

### Custom Widgets

```python
class HeatmapWidget(QWidget):
    """Interactive heatmap visualization using matplotlib."""
    
    point_clicked = pyqtSignal(float, float)  # (x, y) coordinates
    
    def __init__(self):
        # Matplotlib FigureCanvas
        # Navigation toolbar
        # Color bar
        
    def set_data(self, heatmap_data: HeatmapData)
    def update_colormap(self, cmap: str)
    def save_to_file(self, filename: str)


class ResultsTableWidget(QTableView):
    """Results table with sorting, filtering, and export."""
    
    row_selected = pyqtSignal(int)
    
    def __init__(self):
        # Set up table model
        # Configure columns
        # Enable sorting/filtering
        
    def set_results(self, results: list)
    def export_to_csv(self, filename: str)
    def get_selected_trials(self) -> list


class ROIEditorWidget(QGraphicsView):
    """Visual editor for placing ROIs on maze diagram."""
    
    roi_added = pyqtSignal(float, float, float)  # (x, y, diameter)
    roi_moved = pyqtSignal(int, float, float)    # (index, x, y)
    
    def __init__(self, maze_params: dict):
        # QGraphicsScene with maze outline
        # Draggable ROI circles
        # Grid overlay
        
    def add_roi(self, x: float, y: float, diameter: float)
    def clear_rois(self)
    def get_rois(self) -> list


class ControlPanelWidget(QWidget):
    """Left-side control panel for parameters and actions."""
    
    run_clicked = pyqtSignal()
    parameters_changed = pyqtSignal(object)
    
    def __init__(self):
        # Software type selection (radio buttons)
        # File path display
        # Quick parameters (goal pos, maze diam, etc.)
        # Run analysis button
        # Advanced settings button
        
    def set_file_path(self, path: str)
    def get_quick_params(self) -> dict
    def enable_run_button(self, enabled: bool)
```

### Workers (Threading)

```python
class AnalysisWorker(QThread):
    """Background thread for running analysis."""
    
    progress = pyqtSignal(int, int)  # (current, total)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)  # Results
    error = pyqtSignal(str)
    
    def __init__(self, file_path: str, parameters: Parameters):
        self.file_path = file_path
        self.parameters = parameters
        
    def run(self):
        """Execute analysis in background thread."""
        try:
            # Load experiment
            # Calculate metrics
            # Classify strategies
            # Emit progress updates
            # Return results
        except Exception as e:
            self.error.emit(str(e))


class HeatmapWorker(QThread):
    """Background thread for generating heatmaps."""
    
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(object)  # HeatmapData
    error = pyqtSignal(str)
    
    def __init__(self, experiment, config: dict):
        self.experiment = experiment
        self.config = config
        
    def run(self):
        """Generate heatmap in background."""
        # Call pathfinder.aggregate_heatmap_data()
        # Emit progress
        # Return HeatmapData
```

### Data Models

```python
class ResultsTableModel(QAbstractTableModel):
    """Qt model for displaying analysis results."""
    
    def __init__(self, results: list):
        self.results = results
        self.headers = ["Trial", "Strategy", "Latency", "Distance", "Efficiency"]
        
    def rowCount(self, parent=QModelIndex()) -> int
    def columnCount(self, parent=QModelIndex()) -> int
    def data(self, index, role=Qt.DisplayRole)
    def headerData(self, section, orientation, role=Qt.DisplayRole)
    def sort(self, column, order=Qt.AscendingOrder)


class ROIListModel(QAbstractListModel):
    """Qt model for ROI list."""
    
    def __init__(self, rois: list):
        self.rois = rois  # List of (position, diameter)
        
    def rowCount(self, parent=QModelIndex()) -> int
    def data(self, index, role=Qt.DisplayRole)
    def add_roi(self, position: tuple, diameter: float)
    def remove_roi(self, index: int)
```

---

## Window Hierarchy

### Main Window Layout

```
┌────────────────────────────────────────────────────────────┐
│ File  Edit  Window  Help                      [_] [□] [X]  │ ← Menu Bar
├────────────────────────────────────────────────────────────┤
│ [Open] [Dir] [Heatmap] [Settings]             [Run]        │ ← Tool Bar
├─────────────────┬──────────────────────────────────────────┤
│ Control Panel   │  Results Display                         │
│ ┌─────────────┐ │  ┌──────────────────────────────────┐   │
│ │ Software:   │ │  │ [Table] [Heatmap] [Plots] [Log]  │   │
│ │ ○ Ethovision│ │  ├──────────────────────────────────┤   │
│ │ ○ Anymaze   │ │  │                                  │   │
│ │ ○ MATLAB    │ │  │  Trial│Strategy │Latency│Dist    │   │
│ │             │ │  │  001  │ Direct  │ 12.3  │ 145.2  │   │
│ │ File:       │ │  │  002  │ Focal   │ 18.7  │ 234.1  │   │
│ │ /path/to... │ │  │  003  │ Random  │ 45.2  │ 512.8  │   │
│ │             │ │  │  ...  │         │       │        │   │
│ │ Goal Pos:   │ │  │                                  │   │
│ │ [0,0     ]  │ │  │                                  │   │
│ │ Goal Diam:  │ │  │                                  │   │
│ │ [10      ]  │ │  └──────────────────────────────────┘   │
│ │ Maze Diam:  │ │                                          │
│ │ [300     ]  │ │                                          │
│ │             │ │                                          │
│ │ [Advanced…] │ │                                          │
│ │             │ │                                          │
│ └─────────────┘ │                                          │
│                 │                                          │
├─────────────────┴──────────────────────────────────────────┤
│ Ready  │  Analysis completed: 45 trials processed         │ ← Status Bar
└────────────────────────────────────────────────────────────┘
```

### Dialog Windows

#### Settings Dialog
```
┌─────────────────────────────────────────┐
│ Pathfinder Settings              [X]    │
├─────────────────────────────────────────┤
│ ┌───────────────────────────────────┐   │
│ │ [Direct] [Focal] [Indirect] [...] │   │ ← Tabs
│ ├───────────────────────────────────┤   │
│ │ Direct Search Parameters:         │   │
│ │                                   │   │
│ │ IPE Max Value:        [125     ]  │   │
│ │ Heading Max Value:    [40      ]  │   │
│ │ Distance to Swim Max: [30      ]  │   │
│ │ Distance to Plat Max: [30      ]  │   │
│ │                                   │   │
│ │ ☑ Enable Direct Search            │   │
│ │                                   │   │
│ └───────────────────────────────────┘   │
│                                         │
│         [Restore Defaults] [OK] [Cancel]│
└─────────────────────────────────────────┘
```

#### Manual Strategy Dialog
```
┌─────────────────────────────────────────┐
│ Manual Strategy Classification   [X]    │
├─────────────────────────────────────────┤
│ Trial: 001 / 045                        │
│                                         │
│ ┌───────────────────────────────────┐   │
│ │                                   │   │
│ │     [Swim path visualization]     │   │
│ │                                   │   │
│ │         ○                         │   │
│ │       ╱│╲                         │   │
│ │     ╱  │  ╲                       │   │
│ │   ╱    │    ╲    ●               │   │
│ │  ────────────────                 │   │
│ │                                   │   │
│ └───────────────────────────────────┘   │
│                                         │
│ Select Strategy:                        │
│ ○ Direct      ○ Focal      ○ Directed   │
│ ○ Indirect    ○ Scanning   ○ Random     │
│ ○ Chaining    ○ Thigmotaxis             │
│                                         │
│   [< Previous]        [Next >]  [Save]  │
└─────────────────────────────────────────┘
```

#### ROI Manager Dialog
```
┌─────────────────────────────────────────┐
│ ROI Manager                      [X]    │
├─────────────────────────────────────────┤
│ Regions of Interest:                    │
│ ┌───────────────────────────────────┐   │
│ │ ☑ ROI 1: (0,0) - Ø 10cm          │   │
│ │ ☑ ROI 2: (50,50) - Ø 15cm        │   │
│ │ ☐ ROI 3: (-30,20) - Ø 12cm       │   │
│ └───────────────────────────────────┘   │
│                                         │
│ ┌─────────Visual Editor──────────┐      │
│ │        ┌─────────┐             │      │
│ │        │    ①    │             │      │
│ │        │       ② │             │      │
│ │        │  ③      │             │      │
│ │        └─────────┘             │      │
│ └───────────────────────────────┘       │
│                                         │
│ [Add] [Remove] [Edit]      [OK] [Cancel]│
└─────────────────────────────────────────┘
```

---

## Signal/Slot Workflow

### User Opens File

```
User clicks "Open File"
         │
         ▼
MainWindow.open_file()
         │
         ├─> QFileDialog.getOpenFileName()
         │
         ▼
MainWindow.file_loaded signal emitted (str: path)
         │
         ├─> ControlPanel.set_file_path(path)
         │
         └─> StatusBar.showMessage("File loaded: ...")
```

### User Runs Analysis

```
User clicks "Run Analysis"
         │
         ▼
ControlPanel.run_clicked signal
         │
         ▼
MainWindow.start_analysis()
         │
         ├─> Validate parameters
         ├─> Disable UI controls
         ├─> Create AnalysisWorker
         │
         ▼
AnalysisWorker.start()
         │
         ├─> Worker.progress signal → ProgressBar.setValue()
         ├─> Worker.status signal → StatusBar.showMessage()
         │
         ▼
Worker completes → Worker.finished signal (dict: results)
         │
         ▼
MainWindow.on_analysis_complete(results)
         │
         ├─> ResultsTableModel.set_results(results)
         ├─> ResultsTable.update()
         ├─> Enable UI controls
         └─> StatusBar.showMessage("Analysis complete")
```

### User Generates Heatmap

```
User clicks "Generate Heatmap"
         │
         ▼
MainWindow.generate_heatmap()
         │
         ├─> HeatmapConfigDialog.exec_()
         │
         ▼
User configures settings → Dialog.config_confirmed signal (dict)
         │
         ▼
MainWindow receives config
         │
         ├─> Create HeatmapWorker(experiment, config)
         ├─> Worker.start()
         │
         ▼
Worker.finished signal (HeatmapData)
         │
         ▼
HeatmapWidget.set_data(heatmap_data)
         │
         └─> Switch to Heatmap tab
```

### Parameter Changes

```
User edits parameter field
         │
         ▼
QLineEdit.textChanged signal
         │
         ▼
ControlPanel validates input
         │
         ├─> Valid: Enable run button
         └─> Invalid: Show error, disable run button
         
User clicks "Advanced Settings"
         │
         ▼
SettingsDialog.exec_()
         │
         ├─> User modifies parameters
         │
         ▼
Dialog.parameters_updated signal (Parameters)
         │
         ▼
MainWindow.parameters_changed signal
         │
         └─> ControlPanel updates display
```

### Signal/Slot Connections (Code Example)

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Connect control panel signals
        self.control_panel.run_clicked.connect(self.start_analysis)
        self.control_panel.parameters_changed.connect(self.on_parameters_changed)
        
        # Connect menu actions
        self.action_open_file.triggered.connect(self.open_file)
        self.action_generate_heatmap.triggered.connect(self.generate_heatmap)
        
        # Connect file loaded signal to multiple slots
        self.file_loaded.connect(self.control_panel.set_file_path)
        self.file_loaded.connect(lambda path: self.statusBar().showMessage(f"Loaded: {path}"))
        
        # Connect results table selection
        self.results_table.row_selected.connect(self.show_trial_details)
        
    def start_analysis(self):
        # Create worker
        worker = AnalysisWorker(self.file_path, self.parameters)
        
        # Connect worker signals
        worker.progress.connect(self.update_progress)
        worker.status.connect(self.update_status)
        worker.finished.connect(self.on_analysis_complete)
        worker.error.connect(self.on_analysis_error)
        
        # Start worker
        worker.start()
        self.current_worker = worker  # Keep reference
```

---

## Widget Mapping (tkinter → PyQt6)

### Basic Widgets

| tkinter | PyQt6 | Notes |
|---------|-------|-------|
| `Tk()` | `QApplication` | Application instance |
| `Toplevel()` | `QDialog` or `QMainWindow` | Top-level windows |
| `Frame()` | `QWidget` or `QFrame` | Container widget |
| `Label()` | `QLabel` | Text/image display |
| `Button()` | `QPushButton` | Clickable button |
| `Entry()` | `QLineEdit` | Single-line text input |
| `Text()` | `QTextEdit` or `QPlainTextEdit` | Multi-line text |
| `Checkbutton()` | `QCheckBox` | Checkbox |
| `Radiobutton()` | `QRadioButton` | Radio button |
| `Listbox()` | `QListWidget` or `QListView` | List selection |
| `Scrollbar()` | `QScrollBar` | Scrollbar (often automatic in Qt) |
| `Canvas()` | `QGraphicsView` + `QGraphicsScene` | Drawing canvas |
| `Menu()` | `QMenu` | Menu |
| `Menubutton()` | `QMenuBar` | Menu bar |
| `Scale()` | `QSlider` | Slider widget |
| `Spinbox()` | `QSpinBox` or `QDoubleSpinBox` | Numeric spinner |
| `OptionMenu()` | `QComboBox` | Dropdown selection |
| `messagebox` | `QMessageBox` | Message dialogs |
| `filedialog` | `QFileDialog` | File selection dialogs |

### Layout Management

| tkinter | PyQt6 | Notes |
|---------|-------|-------|
| `.grid()` | `QGridLayout` | Grid-based layout |
| `.pack()` | `QVBoxLayout` / `QHBoxLayout` | Linear layouts |
| `.place()` | Absolute positioning (discouraged) | Use layouts instead |
| `PanedWindow()` | `QSplitter` | Resizable panes |
| - | `QDockWidget` | Dockable panels (NEW!) |
| - | `QTabWidget` | Tabbed interface (NEW!) |

### Advanced Widgets (New in PyQt6)

| Purpose | PyQt6 Widget | Advantage |
|---------|--------------|-----------|
| Table view | `QTableView` + `QAbstractTableModel` | Model/View separation, sorting, filtering |
| Tree view | `QTreeView` + `QAbstractItemModel` | Hierarchical data |
| Status bar | `QStatusBar` | Built-in progress, messages |
| Toolbar | `QToolBar` | Icon-based actions, draggable |
| Dock widgets | `QDockWidget` | Floating/dockable panels |
| Splitters | `QSplitter` | Resizable panes |
| Tab widget | `QTabWidget` | Multi-page interface |
| Stacked widget | `QStackedWidget` | Multiple pages, one visible |
| Graphics view | `QGraphicsView` + `QGraphicsScene` | 2D graphics, zooming, panning |

### Pathfinder-Specific Mappings

#### Current tkinter Implementation → New PyQt6 Implementation

**File Selection**
```python
# tkinter (Pathfinder.py line ~689)
def openFile(self):
    filename = filedialog.askopenfilename(title="Select file")
    
# PyQt6
def open_file(self):
    filename, _ = QFileDialog.getOpenFileName(
        self, 
        "Select Experiment File",
        "",
        "CSV Files (*.csv);;All Files (*)"
    )
```

**Directory Selection**
```python
# tkinter (Pathfinder.py line ~699)
def openDir(self):
    directory = filedialog.askdirectory(title="Select directory")
    
# PyQt6
def open_directory(self):
    directory = QFileDialog.getExistingDirectory(
        self,
        "Select Experiment Directory"
    )
```

**Software Type Selection (Radio Buttons)**
```python
# tkinter (Pathfinder.py line ~357)
softwareStringVar = StringVar()
softwareStringVar.set("auto")
ethovisionRadio = Radiobutton(frame, text="Ethovision", 
                              variable=softwareStringVar, value="ethovision")
anymazeRadio = Radiobutton(frame, text="Anymaze",
                          variable=softwareStringVar, value="anymaze")

# PyQt6
class ControlPanel(QWidget):
    def __init__(self):
        self.software_group = QButtonGroup()
        self.ethovision_radio = QRadioButton("Ethovision")
        self.anymaze_radio = QRadioButton("Anymaze")
        self.matlab_radio = QRadioButton("MATLAB")
        
        self.software_group.addButton(self.ethovision_radio, 1)
        self.software_group.addButton(self.anymaze_radio, 2)
        self.software_group.addButton(self.matlab_radio, 3)
        
        # Connect signal
        self.software_group.idClicked.connect(self.on_software_changed)
```

**Parameter Entry Fields**
```python
# tkinter (Pathfinder.py line ~410+)
goalPosEntry = Entry(frame, textvariable=goalPosStringVar, width=20)
goalDiamEntry = Entry(frame, textvariable=goalDiamStringVar, width=20)

# PyQt6
class ControlPanel(QWidget):
    def __init__(self):
        self.goal_pos_edit = QLineEdit()
        self.goal_pos_edit.setPlaceholderText("0,0")
        self.goal_pos_edit.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^-?\d+,-?\d+$"))
        )
        
        self.goal_diam_edit = QDoubleSpinBox()
        self.goal_diam_edit.setRange(1.0, 100.0)
        self.goal_diam_edit.setValue(10.0)
        self.goal_diam_edit.setSuffix(" cm")
```

**Results Display (Table)**
```python
# tkinter - Uses Text widget or custom table
# (Pathfinder.py saves to CSV, no built-in table view)

# PyQt6 - Proper table with model/view
class ResultsTableWidget(QTableView):
    def __init__(self):
        super().__init__()
        self.model = ResultsTableModel([])
        self.setModel(self.model)
        
        # Enable sorting
        self.setSortingEnabled(True)
        
        # Configure columns
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        
    def set_results(self, results: list):
        self.model = ResultsTableModel(results)
        self.setModel(self.model)
```

**Heatmap Display**
```python
# tkinter - Uses matplotlib popup window or PIL/ImageTk
# (Pathfinder.py line ~709)

# PyQt6 - Embedded matplotlib canvas
class HeatmapWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
    def set_data(self, heatmap_data: HeatmapData):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Plot heatmap
        im = ax.imshow(heatmap_data.grid, cmap='hot', origin='lower')
        self.figure.colorbar(im, ax=ax)
        
        self.canvas.draw()
```

**Progress Indication**
```python
# tkinter - Uses status bar text updates
theStatus.set("Loading Files...")

# PyQt6 - Progress bar in status bar
class MainWindow(QMainWindow):
    def __init__(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
    def update_progress(self, value: int, maximum: int):
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        
    def update_status(self, message: str):
        self.statusBar().showMessage(message)
```

**Manual Strategy Classification Window**
```python
# tkinter - Toplevel with Canvas for visualization
# (Pathfinder.py line ~1517+)

# PyQt6 - Dialog with graphics view
class ManualStrategyDialog(QDialog):
    def __init__(self, trial_data):
        super().__init__()
        
        # Graphics view for swim path
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        
        # Draw maze boundary
        self.scene.addEllipse(-150, -150, 300, 300, QPen(Qt.black))
        
        # Draw swim path
        for i in range(len(trial_data) - 1):
            self.scene.addLine(
                trial_data[i].x, trial_data[i].y,
                trial_data[i+1].x, trial_data[i+1].y,
                QPen(Qt.blue)
            )
        
        # Strategy selection (radio buttons)
        self.strategy_group = QButtonGroup()
        # ... add radio buttons for each strategy
```

---

## Threading Strategy

### Why Threading?

Analysis operations can take significant time:
- Loading large experiment files (thousands of trials)
- Calculating metrics for each trial
- Generating heatmaps with high-resolution grids
- Computing entropy values

Without threading, the GUI would freeze during these operations.

### QThread vs QRunnable

**QThread** (Recommended for Pathfinder):
- Full-featured thread with event loop
- Can emit signals (progress updates, status messages)
- Easy to stop/pause
- Best for long-running operations with user feedback

**QRunnable** (Alternative):
- Lightweight, managed by QThreadPool
- No built-in signal support (need QObject wrapper)
- Better for many short tasks
- Automatic thread management

### Implementation Pattern

```python
class AnalysisWorker(QThread):
    """
    Worker thread for running analysis.
    
    Emits progress updates and results via signals.
    """
    
    # Signals (can only be class attributes)
    progress = pyqtSignal(int, int)  # (current, total)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, file_path: str, parameters: Parameters):
        super().__init__()
        self.file_path = file_path
        self.parameters = parameters
        self._is_running = True
        
    def run(self):
        """
        Main execution method (runs in separate thread).
        """
        try:
            # Load experiment
            self.status.emit("Loading experiment...")
            experiment = load_experiment(self.file_path)
            
            total_trials = len(experiment.trials)
            results = []
            
            # Process each trial
            for i, trial in enumerate(experiment.trials):
                if not self._is_running:
                    break
                    
                self.status.emit(f"Analyzing trial {i+1}/{total_trials}...")
                self.progress.emit(i+1, total_trials)
                
                # Call pathfinder API
                metrics = calculate_trial_metrics(trial, self.parameters)
                strategy = classify_strategy(metrics, self.parameters)
                
                results.append({
                    'trial_id': trial.id,
                    'strategy': strategy.strategy,
                    'latency': metrics.latency,
                    'distance': metrics.total_distance,
                    # ... more fields
                })
            
            # Emit results
            self.finished.emit({'trials': results, 'experiment': experiment})
            
        except Exception as e:
            self.error.emit(str(e))
            logging.error(f"Analysis error: {e}", exc_info=True)
    
    def stop(self):
        """Stop the worker gracefully."""
        self._is_running = False
```

### Usage in MainWindow

```python
class MainWindow(QMainWindow):
    def start_analysis(self):
        """Start analysis in background thread."""
        
        # Validate inputs
        if not self.file_path:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return
        
        # Disable UI during analysis
        self.control_panel.setEnabled(False)
        self.action_run.setEnabled(False)
        
        # Create and configure worker
        self.worker = AnalysisWorker(self.file_path, self.parameters)
        
        # Connect signals
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.error.connect(self.on_analysis_error)
        
        # Clean up when finished
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        
        # Start worker
        self.worker.start()
        
    def on_analysis_complete(self, results: dict):
        """Handle analysis completion."""
        # Re-enable UI
        self.control_panel.setEnabled(True)
        self.action_run.setEnabled(True)
        
        # Update results display
        self.results_table.set_results(results['trials'])
        
        # Switch to results tab
        self.tab_widget.setCurrentIndex(0)
        
        # Update status
        trial_count = len(results['trials'])
        self.statusBar().showMessage(f"Analysis complete: {trial_count} trials processed")
        
        # Store experiment for heatmap generation
        self.current_experiment = results['experiment']
        
    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.control_panel.setEnabled(True)
        self.action_run.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"An error occurred during analysis:\n\n{error}"
        )
```

### Thread Safety Considerations

1. **Signal/Slot is thread-safe**: Qt automatically handles cross-thread signal/slot connections
2. **Don't access GUI from worker**: Only emit signals, never call GUI methods directly
3. **Immutable data**: Pass immutable parameters to workers (or deep copy)
4. **Keep worker reference**: Store worker as instance variable to prevent garbage collection
5. **Clean up**: Use `deleteLater()` to clean up workers after completion

### Progress Reporting Best Practices

```python
def run(self):
    total_steps = 100
    
    for i in range(total_steps):
        # Do work...
        
        # Update progress (every step)
        self.progress.emit(i+1, total_steps)
        
        # Update status (occasionally, not every iteration)
        if i % 10 == 0:
            self.status.emit(f"Processing step {i+1}/{total_steps}")
```

---

## Migration Checklist from tkinter → PyQt6

### Phase 1: Setup & Infrastructure ✓ (Already Complete)

- [x] Extract all analysis logic to `pathfinder/` package
- [x] Create pure Python API (analysis.py, models.py, io.py)
- [x] Define type hints (TrialMetrics, StrategyResult, etc.)
- [x] Write unit tests for analysis functions
- [x] Verify API works independently of GUI

### Phase 2: PyQt6 Project Structure

- [ ] Create `gui/` directory structure
- [ ] Set up `main.py` entry point
- [ ] Configure `requirements.txt` with PyQt6 dependencies
- [ ] Create `setup.py` for installation
- [ ] Set up `gui/__init__.py` with version info

### Phase 3: Main Window

- [ ] Create `MainWindow` class (QMainWindow)
- [ ] Implement menu bar (File, Edit, Window, Help)
- [ ] Add toolbar with common actions
- [ ] Create status bar with progress indicator
- [ ] Set up central widget with QSplitter
- [ ] Define signals (file_loaded, analysis_started, etc.)

### Phase 4: Control Panel

- [ ] Create `ControlPanelWidget`
- [ ] Add software type selection (radio buttons)
- [ ] Implement file path display
- [ ] Add quick parameter inputs (goal pos, maze diam, etc.)
- [ ] Create "Advanced Settings" button
- [ ] Add "Run Analysis" button
- [ ] Implement input validation
- [ ] Define signals (run_clicked, parameters_changed)

### Phase 5: Dialogs

- [ ] **SettingsDialog**: Full parameter configuration
  - [ ] Create tabbed interface (Direct, Focal, Indirect, etc.)
  - [ ] Add input fields for all parameters
  - [ ] Implement "Restore Defaults" functionality
  - [ ] Add validation
  - [ ] Emit parameters_updated signal

- [ ] **FileImportDialog**: Advanced file selection
  - [ ] File browser with preview
  - [ ] Software type auto-detection
  - [ ] Batch file selection

- [ ] **ManualStrategyDialog**: Manual classification
  - [ ] Graphics view for swim path visualization
  - [ ] Radio buttons for strategy selection
  - [ ] Navigation (prev/next trial)
  - [ ] Save classifications

- [ ] **ROIManagerDialog**: Multiple ROIs
  - [ ] List view of current ROIs
  - [ ] Add/remove/edit controls
  - [ ] Visual editor preview
  - [ ] Validation

- [ ] **HeatmapConfigDialog**: Heatmap settings
  - [ ] Grid size input
  - [ ] Color map selection
  - [ ] Day/trial filters
  - [ ] Max value (auto/manual)

- [ ] **AboutDialog**: App info and credits

### Phase 6: Custom Widgets

- [ ] **ResultsTableWidget**
  - [ ] Create ResultsTableModel (QAbstractTableModel)
  - [ ] Implement data(), headerData(), rowCount(), columnCount()
  - [ ] Add sorting functionality
  - [ ] Implement row selection signal
  - [ ] Add context menu (copy, export)

- [ ] **HeatmapWidget**
  - [ ] Embed matplotlib FigureCanvas
  - [ ] Add navigation toolbar
  - [ ] Implement set_data() method
  - [ ] Add colormap customization
  - [ ] Add export functionality

- [ ] **ROIEditorWidget**
  - [ ] Create QGraphicsScene with maze outline
  - [ ] Add draggable ROI circles (QGraphicsEllipseItem)
  - [ ] Implement grid overlay
  - [ ] Add zoom/pan controls
  - [ ] Emit roi_added, roi_moved signals

- [ ] **PlotCanvasWidget**
  - [ ] Embed matplotlib for strategy plots
  - [ ] Add plot type selection (bar, pie, line)
  - [ ] Implement export functionality

### Phase 7: Workers (Threading)

- [ ] **AnalysisWorker** (QThread)
  - [ ] Implement run() method
  - [ ] Call pathfinder API functions
  - [ ] Emit progress updates (every trial)
  - [ ] Emit status messages (every 10 trials)
  - [ ] Handle errors gracefully
  - [ ] Implement stop() method

- [ ] **HeatmapWorker** (QThread)
  - [ ] Call aggregate_heatmap_data()
  - [ ] Emit progress updates
  - [ ] Return HeatmapData object

- [ ] **FileLoaderWorker** (QThread)
  - [ ] Load large experiment files asynchronously
  - [ ] Emit progress for multi-file directories
  - [ ] Return loaded Experiment object

### Phase 8: Styling & Themes

- [ ] Create `styles.py` with theme definitions
- [ ] Implement dark mode detection (cross-platform)
- [ ] Define color palettes (light/dark)
- [ ] Create QSS (Qt Style Sheets) for custom styling
- [ ] Add font definitions
- [ ] Implement theme switching functionality

### Phase 9: Integration & Workflow

- [ ] Connect MainWindow to ControlPanel signals
- [ ] Connect file selection to file loading workflow
- [ ] Implement run analysis workflow
  - [ ] Validate inputs
  - [ ] Create AnalysisWorker
  - [ ] Connect signals
  - [ ] Update UI on completion

- [ ] Implement heatmap generation workflow
  - [ ] Open HeatmapConfigDialog
  - [ ] Create HeatmapWorker
  - [ ] Display results in HeatmapWidget

- [ ] Implement manual classification workflow
  - [ ] Open ManualStrategyDialog for each trial
  - [ ] Save classifications
  - [ ] Update results table

- [ ] Add keyboard shortcuts
  - [ ] Ctrl+O: Open File
  - [ ] Ctrl+D: Open Directory
  - [ ] Ctrl+R: Run Analysis
  - [ ] Ctrl+H: Generate Heatmap
  - [ ] Ctrl+S: Save Results

### Phase 10: Testing

- [ ] Unit tests for GUI components
  - [ ] Test signal/slot connections
  - [ ] Test worker thread logic
  - [ ] Test data models

- [ ] Integration tests
  - [ ] Test full analysis workflow
  - [ ] Test heatmap generation
  - [ ] Test file loading

- [ ] Manual testing
  - [ ] Test on Windows
  - [ ] Test on macOS
  - [ ] Test on Linux
  - [ ] Test with large datasets
  - [ ] Test error handling

### Phase 11: Documentation

- [ ] Update README with PyQt6 requirements
- [ ] Add screenshots of new GUI
- [ ] Document new features
- [ ] Create user guide
- [ ] Add developer documentation

### Phase 12: Deployment

- [ ] Create installer for Windows (PyInstaller or cx_Freeze)
- [ ] Create .app bundle for macOS
- [ ] Create .deb package for Linux
- [ ] Update pip package
- [ ] Tag release on GitHub

### Phase 13: Deprecation of Old GUI

- [ ] Keep `SearchStrategyAnalysis/Pathfinder.py` for reference
- [ ] Add deprecation notice
- [ ] Update documentation to point to new GUI
- [ ] Eventually remove old GUI (future release)

---

## Implementation Roadmap

### Sprint 1: Foundation (Week 1)

**Goal**: Basic PyQt6 skeleton with main window

- Set up project structure (`gui/` directory)
- Create `main.py` entry point
- Implement `MainWindow` with menu bar
- Add toolbar and status bar
- Create basic control panel (file selection only)
- Test: Open a file and display path

**Deliverables**:
- Working PyQt6 application that launches
- Can select files (but doesn't process them yet)

### Sprint 2: Control Panel & Settings (Week 2)

**Goal**: Full parameter configuration UI

- Complete `ControlPanelWidget` with all quick parameters
- Implement `SettingsDialog` with tabbed interface
- Add input validation
- Connect parameter signals
- Test: Change parameters and verify signals emitted

**Deliverables**:
- Functional control panel
- Settings dialog with all parameters
- Validation working

### Sprint 3: Analysis Integration (Week 3)

**Goal**: Run analysis and display results

- Create `AnalysisWorker` thread
- Implement `ResultsTableModel` and `ResultsTableWidget`
- Connect run analysis workflow
- Add progress bar and status updates
- Test: Run full analysis on sample data

**Deliverables**:
- Working analysis execution
- Results displayed in table
- Progress indication

### Sprint 4: Heatmap Visualization (Week 4)

**Goal**: Generate and display heatmaps

- Implement `HeatmapWidget` with matplotlib
- Create `HeatmapConfigDialog`
- Implement `HeatmapWorker` thread
- Connect heatmap generation workflow
- Test: Generate heatmap from analysis results

**Deliverables**:
- Functional heatmap generation
- Interactive heatmap display
- Export to image file

### Sprint 5: Advanced Features (Week 5)

**Goal**: ROI management and manual classification

- Implement `ROIEditorWidget` with graphics scene
- Create `ROIManagerDialog`
- Implement `ManualStrategyDialog` with visualization
- Test: Add ROIs, classify strategies manually

**Deliverables**:
- ROI editor with visual feedback
- Manual classification workflow
- Multiple ROIs supported

### Sprint 6: Polish & Testing (Week 6)

**Goal**: Production-ready application

- Implement theming (dark/light mode)
- Add keyboard shortcuts
- Write unit tests
- Fix bugs
- Optimize performance
- Test on all platforms

**Deliverables**:
- Polished, bug-free application
- Comprehensive test coverage
- Cross-platform verified

### Sprint 7: Documentation & Deployment (Week 7)

**Goal**: Release to users

- Write user documentation
- Create installers (Windows, macOS, Linux)
- Update README and guides
- Create demo videos/screenshots
- Tag release

**Deliverables**:
- Packaged application for all platforms
- Complete documentation
- Public release

---

## Key Design Decisions

### 1. Model/View Separation

**Why**: Qt's Model/View architecture separates data from presentation, enabling:
- Multiple views of the same data
- Easy sorting and filtering
- Automatic updates when data changes
- Better testability

**Example**: `ResultsTableModel` (data) + `ResultsTableWidget` (view)

### 2. Signal/Slot for All Communication

**Why**: Declarative, type-safe, and decoupled
- No tight coupling between components
- Easy to add new listeners
- Thread-safe cross-thread communication
- Self-documenting (signals describe what can happen)

**Example**: `ControlPanel.run_clicked` → `MainWindow.start_analysis()`

### 3. Threading for Long Operations

**Why**: Keep UI responsive
- Analysis can take minutes for large datasets
- User needs feedback (progress, status)
- Ability to cancel long operations

**Example**: `AnalysisWorker` runs in background, emits progress signals

### 4. Centralized Styling

**Why**: Consistent look, easy theming
- Single source of truth for colors, fonts
- Easy to implement dark mode
- Platform-specific adaptations
- Maintainable

**Example**: `styles.py` with theme dictionaries, applied globally

### 5. Pure Analysis API

**Why**: Already done in Phase 1, but critical for GUI independence
- GUI can be completely replaced without touching analysis code
- Analysis logic testable without GUI
- CLI and GUI use same API
- Future: web interface, API server

**Example**: `pathfinder.calculate_trial_metrics()` has no GUI dependencies

---

## What Stays, What's New, What's Removed

### KEEP (Preserved Functionality)

✅ **File loading workflow**: Single file or directory selection  
✅ **Software type detection**: Ethovision, Anymaze, MATLAB  
✅ **Parameter configuration**: All analysis parameters customizable  
✅ **Analysis execution**: Call pathfinder API functions  
✅ **Result display**: Table of trials with strategies  
✅ **Heatmap visualization**: Grid-based heatmap generation  
✅ **Manual classification**: Override automatic strategy detection  
✅ **ROI management**: Multiple regions of interest  
✅ **Export functionality**: Save results to CSV  
✅ **Entropy calculations**: Optional entropy metrics  

### NEW (Modern Features)

🆕 **Responsive layout**: Resizable splitters, dockable panels  
🆕 **Dark mode**: System theme detection and switching  
🆕 **Progress indication**: Real-time progress bar and status  
🆕 **Interactive tables**: Sorting, filtering, row selection  
🆕 **Embedded heatmaps**: In-app display with zoom/pan  
🆕 **Keyboard shortcuts**: Fast navigation and actions  
🆕 **Tooltips**: Contextual help for all parameters  
🆕 **Input validation**: Real-time validation with visual feedback  
🆕 **Themes**: Customizable color schemes  
🆕 **Better error handling**: Clear error messages, recovery options  
🆕 **Undo/Redo**: For parameter changes (future)  
🆕 **Batch processing**: Multiple experiments at once (future)  
🆕 **Plugin system**: Extensible for custom analyses (future)  

### REMOVE (GUI/Analysis Coupling)

❌ **Analysis logic in GUI**: All moved to `pathfinder/`  
❌ **Global variables**: Replaced with proper state management  
❌ **Tight coupling**: GUI now uses pathfinder API only  
❌ **tkinter-specific hacks**: Platform detection, color handling  
❌ **Mixed responsibilities**: Clear separation of concerns  
❌ **Hardcoded paths**: User-configurable output directories  
❌ **Manual layout calculations**: Use Qt layouts  

---

## Technical Specifications

### Dependencies

```txt
# Core
PyQt6>=6.4.0
PyQt6-Charts>=6.4.0

# Visualization
matplotlib>=3.5.0
numpy>=1.21.0
scipy>=1.7.0
Pillow>=9.0.0

# Data handling
pandas>=1.3.0

# Analysis (already have)
pathfinder>=2.0.0  # Local package

# Optional
seaborn>=0.11.0  # Enhanced plotting
```

### Python Version

- **Minimum**: Python 3.8
- **Recommended**: Python 3.10+
- **Tested**: Python 3.8, 3.9, 3.10, 3.11

### Platform Support

- **Windows**: 10, 11
- **macOS**: 10.14+
- **Linux**: Ubuntu 20.04+, Fedora 34+, Debian 11+

### Performance Targets

- **Startup time**: < 2 seconds
- **File loading**: < 1 second for 100 trials
- **Analysis execution**: Real-time progress updates (at least every 100ms)
- **Heatmap rendering**: < 5 seconds for 100x100 grid
- **UI responsiveness**: Never freeze, always responsive

---

## Future Enhancements (Post-Migration)

### Short-term (Next Release)

- **Export plots**: Save heatmaps and plots to various formats
- **Batch processing**: Analyze multiple experiments in sequence
- **Report generation**: PDF reports with results and visualizations
- **Recent files**: Quick access to recently opened experiments

### Medium-term

- **Project files**: Save analysis configuration as .pathfinder project
- **Comparison mode**: Compare results across experiments
- **Statistical tests**: Built-in ANOVA, t-tests for group comparisons
- **Custom strategies**: User-defined strategy classification rules
- **Scripting**: Python console for custom analyses

### Long-term

- **Web interface**: Browser-based GUI (same pathfinder API)
- **Cloud integration**: Save results to cloud storage
- **Collaborative features**: Share analyses with team
- **Machine learning**: Train custom strategy classifiers
- **Real-time analysis**: Analyze during experiment recording

---

## Conclusion

This PyQt6 architecture provides a **modern, maintainable, and extensible** foundation for Pathfinder. By separating GUI from analysis logic (already achieved in Phase 1), we can now build a superior user experience while keeping the powerful analysis engine intact.

### Key Advantages

1. **Clean separation**: GUI and analysis completely decoupled
2. **Modern UI**: Responsive, themeable, professional
3. **Better UX**: Progress indication, validation, error handling
4. **Maintainable**: Modular structure, clear responsibilities
5. **Testable**: Unit tests for both GUI and analysis
6. **Extensible**: Easy to add new features, visualizations, plugins
7. **Cross-platform**: Consistent experience on Windows, macOS, Linux

### Next Steps

1. ✅ **Review this design** with stakeholders
2. **Set up development environment** (PyQt6, dependencies)
3. **Create project structure** (`gui/` directory)
4. **Implement Sprint 1** (main window skeleton)
5. **Iterate through sprints** following the roadmap

### Success Criteria

- [ ] All original functionality preserved
- [ ] No analysis logic in GUI code
- [ ] Non-blocking UI during long operations
- [ ] Dark mode support
- [ ] Cross-platform compatibility
- [ ] Unit test coverage > 80%
- [ ] User documentation complete
- [ ] Packaged installers for all platforms

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-07  
**Status**: Ready for Implementation  
**Estimated Timeline**: 7 weeks (7 sprints)

---

## Appendix: Code Examples

### Example: main.py

```python
#!/usr/bin/env python3
"""
Pathfinder - Morris Water Maze Analysis Tool

Main entry point for the PyQt6 GUI application.
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from gui.main_window import MainWindow
from gui.styles import apply_theme

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pathfinder.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Pathfinder")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("UBC Snyder Lab")
    app.setOrganizationDomain("snyderlab.ubc.ca")
    
    # Set application icon
    icon_path = Path(__file__).parent / "gui" / "resources" / "icons" / "pathfinder.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Apply theme
    apply_theme(app, dark_mode='auto')
    
    # Enable high DPI scaling
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Handle command-line arguments (optional file path)
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        logger.info(f"Opening file from command line: {file_path}")
        window.load_file(file_path)
    
    # Run event loop
    logger.info("Application started")
    exit_code = app.exec()
    logger.info("Application exiting")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
```

### Example: gui/main_window.py (Skeleton)

```python
"""
Main window for Pathfinder GUI.
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QFileDialog, QMessageBox,
    QProgressBar, QLabel, QStatusBar, QMenuBar, QMenu,
    QToolBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QKeySequence

from pathfinder import Parameters

from gui.widgets.control_panel import ControlPanelWidget
from gui.widgets.results_table import ResultsTableWidget
from gui.widgets.heatmap_widget import HeatmapWidget
from gui.dialogs import (
    SettingsDialog, HeatmapConfigDialog, 
    ManualStrategyDialog, AboutDialog
)
from gui.workers import AnalysisWorker, HeatmapWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for Pathfinder.
    """
    
    # Signals
    file_loaded = pyqtSignal(str)
    analysis_started = pyqtSignal()
    analysis_completed = pyqtSignal(dict)
    parameters_changed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        
        # State
        self.file_path = None
        self.current_experiment = None
        self.parameters = Parameters()  # Default parameters
        self.worker = None
        
        # Setup UI
        self.setWindowTitle("Pathfinder - Morris Water Maze Analysis")
        self.setGeometry(100, 100, 1200, 800)
        
        self._setup_ui()
        self._connect_signals()
        
        logger.info("MainWindow initialized")
    
    def _setup_ui(self):
        """Initialize all UI components."""
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_status_bar()
    
    def _create_menu_bar(self):
        """Create menu bar with File, Edit, Window, Help menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        self.action_open_file = QAction("&Open File...", self)
        self.action_open_file.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open_file.triggered.connect(self.open_file)
        file_menu.addAction(self.action_open_file)
        
        self.action_open_dir = QAction("Open &Directory...", self)
        self.action_open_dir.setShortcut(QKeySequence("Ctrl+D"))
        self.action_open_dir.triggered.connect(self.open_directory)
        file_menu.addAction(self.action_open_dir)
        
        file_menu.addSeparator()
        
        self.action_generate_heatmap = QAction("Generate &Heatmap...", self)
        self.action_generate_heatmap.setShortcut(QKeySequence("Ctrl+H"))
        self.action_generate_heatmap.triggered.connect(self.generate_heatmap)
        file_menu.addAction(self.action_generate_heatmap)
        
        file_menu.addSeparator()
        
        self.action_quit = QAction("&Quit", self)
        self.action_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_quit.triggered.connect(self.close)
        file_menu.addAction(self.action_quit)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        self.action_settings = QAction("&Settings...", self)
        self.action_settings.setShortcut(QKeySequence.StandardKey.Preferences)
        self.action_settings.triggered.connect(self.show_settings)
        edit_menu.addAction(self.action_settings)
        
        # Window menu
        window_menu = menubar.addMenu("&Window")
        
        self.action_maximize = QAction("Maximize", self)
        self.action_maximize.triggered.connect(self.showMaximized)
        window_menu.addAction(self.action_maximize)
        
        self.action_minimize = QAction("Minimize", self)
        self.action_minimize.triggered.connect(self.showMinimized)
        window_menu.addAction(self.action_minimize)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        self.action_about = QAction("&About Pathfinder", self)
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)
    
    def _create_toolbar(self):
        """Create toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.action_open_file)
        toolbar.addAction(self.action_open_dir)
        toolbar.addSeparator()
        toolbar.addAction(self.action_generate_heatmap)
        toolbar.addSeparator()
        
        self.action_run = QAction("Run Analysis", self)
        self.action_run.setShortcut(QKeySequence("Ctrl+R"))
        self.action_run.triggered.connect(self.start_analysis)
        self.action_run.setEnabled(False)
        toolbar.addAction(self.action_run)
    
    def _create_central_widget(self):
        """Create central widget with splitter layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Control panel
        self.control_panel = ControlPanelWidget()
        splitter.addWidget(self.control_panel)
        
        # Right panel: Tab widget for results
        self.tab_widget = QTabWidget()
        
        self.results_table = ResultsTableWidget()
        self.tab_widget.addTab(self.results_table, "Results Table")
        
        self.heatmap_widget = HeatmapWidget()
        self.tab_widget.addTab(self.heatmap_widget, "Heatmap")
        
        # TODO: Add more tabs (Plots, Log)
        
        splitter.addWidget(self.tab_widget)
        
        # Set initial sizes (30% control panel, 70% results)
        splitter.setSizes([300, 900])
        
        layout.addWidget(splitter)
    
    def _create_status_bar(self):
        """Create status bar with message and progress indicator."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_bar.showMessage("Ready")
    
    def _connect_signals(self):
        """Connect signals and slots."""
        # Control panel signals
        self.control_panel.run_clicked.connect(self.start_analysis)
        self.control_panel.parameters_changed.connect(self.on_parameters_changed)
        
        # File loaded signal
        self.file_loaded.connect(self.control_panel.set_file_path)
        self.file_loaded.connect(lambda path: self.action_run.setEnabled(True))
    
    # Menu action handlers
    def open_file(self):
        """Open file dialog and load single experiment file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Experiment File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.load_file(file_path)
    
    def open_directory(self):
        """Open directory dialog and load all experiment files."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Experiment Directory"
        )
        
        if dir_path:
            self.load_file(dir_path)
    
    def load_file(self, path: str):
        """Load experiment file or directory."""
        self.file_path = path
        self.file_loaded.emit(path)
        self.status_bar.showMessage(f"Loaded: {path}")
        logger.info(f"File loaded: {path}")
    
    def start_analysis(self):
        """Start analysis in background thread."""
        if not self.file_path:
            QMessageBox.warning(self, "No File", "Please select a file first.")
            return
        
        # Disable UI
        self.control_panel.setEnabled(False)
        self.action_run.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create worker
        self.worker = AnalysisWorker(self.file_path, self.parameters)
        
        # Connect signals
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.error.connect(self.on_analysis_error)
        
        # Cleanup
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        
        # Start
        self.worker.start()
        self.analysis_started.emit()
        logger.info("Analysis started")
    
    def on_analysis_complete(self, results: dict):
        """Handle analysis completion."""
        # Re-enable UI
        self.control_panel.setEnabled(True)
        self.action_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Update results
        self.results_table.set_results(results.get('trials', []))
        self.current_experiment = results.get('experiment')
        
        # Switch to results tab
        self.tab_widget.setCurrentIndex(0)
        
        # Update status
        trial_count = len(results.get('trials', []))
        self.status_bar.showMessage(f"Analysis complete: {trial_count} trials processed")
        
        self.analysis_completed.emit(results)
        logger.info(f"Analysis completed: {trial_count} trials")
    
    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        self.control_panel.setEnabled(True)
        self.action_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"An error occurred during analysis:\n\n{error}"
        )
        
        self.status_bar.showMessage("Analysis failed")
        logger.error(f"Analysis error: {error}")
    
    def update_progress(self, value: int, maximum: int):
        """Update progress bar."""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
    
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_bar.showMessage(message)
    
    def generate_heatmap(self):
        """Open heatmap configuration dialog and generate heatmap."""
        if not self.current_experiment:
            QMessageBox.warning(
                self,
                "No Data",
                "Please run analysis first before generating heatmap."
            )
            return
        
        # Open config dialog
        dialog = HeatmapConfigDialog()
        if dialog.exec():
            config = dialog.get_config()
            
            # Create worker
            worker = HeatmapWorker(self.current_experiment, config)
            worker.finished.connect(self.on_heatmap_complete)
            worker.error.connect(lambda err: QMessageBox.critical(self, "Error", err))
            worker.start()
            
            self.status_bar.showMessage("Generating heatmap...")
    
    def on_heatmap_complete(self, heatmap_data):
        """Handle heatmap generation completion."""
        self.heatmap_widget.set_data(heatmap_data)
        self.tab_widget.setCurrentWidget(self.heatmap_widget)
        self.status_bar.showMessage("Heatmap generated")
    
    def show_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self.parameters)
        if dialog.exec():
            self.parameters = dialog.get_parameters()
            self.parameters_changed.emit(self.parameters)
            logger.info("Parameters updated")
    
    def on_parameters_changed(self, parameters):
        """Handle parameter changes from control panel."""
        self.parameters = parameters
        self.parameters_changed.emit(parameters)
    
    def show_about(self):
        """Show about dialog."""
        dialog = AboutDialog()
        dialog.exec()
```

---

**End of Design Document**
