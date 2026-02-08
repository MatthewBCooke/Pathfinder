"""
Pathfinder - Main Window Module

This module contains the MainWindow class for the Pathfinder PyQt6 GUI.
The main window provides a clean, modern interface for loading experiments,
configuring parameters, running analysis, and viewing results.

Architecture:
    - Left panel: Control panel (file loading, parameters, run button)
    - Right panel: Results display (table, heatmap, summary)
    - Menu bar: File, View, Tools, Help
    - Status bar: Operation status, trial count, progress

Author: OpenClaw Agent
Date: 2026-02-07
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QProgressBar, QTabWidget,
    QGroupBox, QFileDialog, QMessageBox, QStatusBar, QTableWidget,
    QTableWidgetItem, QMenuBar, QMenu, QFrame, QTextEdit
)
from PyQt6.QtGui import QAction, QFont, QColor

# Import from pathfinder package
try:
    from pathfinder import load_experiment, calculate_trial_metrics, classify_strategy
except ImportError:
    # Placeholder for development - will be replaced with actual imports
    def load_experiment(*args, **kwargs):
        raise NotImplementedError("pathfinder.load_experiment not yet implemented")
    
    def calculate_trial_metrics(*args, **kwargs):
        raise NotImplementedError("pathfinder.calculate_trial_metrics not yet implemented")
    
    def classify_strategy(*args, **kwargs):
        raise NotImplementedError("pathfinder.classify_strategy not yet implemented")


class MainWindow(QMainWindow):
    """
    Main application window for Pathfinder Morris Water Maze Analysis.
    
    This window provides a split-panel interface with controls on the left
    and results display on the right. All analysis logic is delegated to
    the pathfinder package - this class only handles UI interactions.
    
    Signals:
        loaded_experiment: Emitted when an experiment is successfully loaded.
            Args: experiment (Any): The loaded experiment object
        
        analysis_started: Emitted when analysis execution begins.
        
        analysis_complete: Emitted when analysis finishes successfully.
            Args: results (Dict[str, Any]): Analysis results dictionary
        
        error: Emitted when an error occurs.
            Args: message (str): Error message to display
    
    Attributes:
        current_experiment: Currently loaded experiment object
        current_results: Most recent analysis results
        current_parameters: Current analysis parameters
    """
    
    # Custom signals
    loaded_experiment = pyqtSignal(object)  # experiment object
    analysis_started = pyqtSignal()
    analysis_complete = pyqtSignal(dict)  # results dictionary
    error = pyqtSignal(str)  # error message
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the main window.
        
        Args:
            parent: Parent widget (typically None for main window)
        """
        super().__init__(parent)
        
        # State variables
        self.current_experiment: Optional[Any] = None
        self.current_results: Optional[Dict[str, Any]] = None
        self.current_parameters: Dict[str, Any] = {}
        self.experiment_file_path: Optional[str] = None
        
        # Setup UI
        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._connect_signals()
        
        # Window properties
        self.setWindowTitle("Pathfinder - Morris Water Maze Analysis")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
    
    def _init_ui(self) -> None:
        """Initialize the user interface components."""
        # Central widget with horizontal splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for left/right panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # Left panel: Control panel
        left_panel = self._create_control_panel()
        self.splitter.addWidget(left_panel)
        
        # Right panel: Results display
        right_panel = self._create_results_panel()
        self.splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% left, 70% right)
        self.splitter.setSizes([400, 1000])
    
    def _create_control_panel(self) -> QWidget:
        """
        Create the left control panel with file loading, parameters, and run button.
        
        Returns:
            QWidget: Configured control panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- File Loading Section ---
        file_group = QGroupBox("Experiment File")
        file_layout = QVBoxLayout()
        
        # Load Experiment button
        self.load_button = QPushButton("📂 Load Experiment")
        self.load_button.setMinimumHeight(40)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        file_layout.addWidget(self.load_button)
        
        # Current experiment display
        self.experiment_label = QLabel("No experiment loaded")
        self.experiment_label.setWordWrap(True)
        self.experiment_label.setStyleSheet("color: #666; font-style: italic;")
        file_layout.addWidget(self.experiment_label)
        
        # Trial count display
        self.trial_count_label = QLabel("Trials: 0")
        self.trial_count_label.setStyleSheet("font-weight: bold; color: #333;")
        file_layout.addWidget(self.trial_count_label)
        
        # Software type dropdown
        software_layout = QHBoxLayout()
        software_label = QLabel("Software Type:")
        self.software_combo = QComboBox()
        self.software_combo.addItems([
            "Auto-detect",
            "Ethovision",
            "AnyMaze",
            "WaterMaze",
            "EZTrack",
            "Custom"
        ])
        software_layout.addWidget(software_label)
        software_layout.addWidget(self.software_combo)
        file_layout.addLayout(software_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # --- Parameter Section ---
        param_group = QGroupBox("Analysis Parameters")
        param_layout = QVBoxLayout()
        
        # Settings button
        self.settings_button = QPushButton("⚙️ Settings")
        self.settings_button.setMinimumHeight(35)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                font-size: 13px;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        param_layout.addWidget(self.settings_button)
        
        # Current parameters display (read-only summary)
        self.params_display = QLabel("Using default parameters")
        self.params_display.setWordWrap(True)
        self.params_display.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                color: #444;
            }
        """)
        param_layout.addWidget(self.params_display)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
        
        # --- Analysis Execution Section ---
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout()
        
        # Analyze button
        self.analyze_button = QPushButton("▶️ Analyze")
        self.analyze_button.setMinimumHeight(50)
        self.analyze_button.setEnabled(False)  # Disabled until experiment loaded
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #888;
            }
        """)
        analysis_layout.addWidget(self.analyze_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
            }
        """)
        analysis_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 12px;
                padding: 5px;
            }
        """)
        analysis_layout.addWidget(self.status_label)
        
        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
    
    def _create_results_panel(self) -> QWidget:
        """
        Create the right results panel with tabbed views.
        
        Returns:
            QWidget: Configured results panel with tabs
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Tab widget for different result views
        self.results_tabs = QTabWidget()
        self.results_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555;
            }
            QTabBar::tab {
                background: #333;
                color: #fff;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #555;
                border-bottom: none;
            }
        """)
        
        # Tab 1: Results Table
        self.results_table = self._create_results_table()
        self.results_tabs.addTab(self.results_table, "📊 Results Table")
        
        # Tab 2: Heatmap (placeholder for matplotlib canvas)
        self.heatmap_widget = self._create_heatmap_widget()
        self.results_tabs.addTab(self.heatmap_widget, "🔥 Heatmap")
        
        # Tab 3: Summary (statistics and charts)
        self.summary_widget = self._create_summary_widget()
        self.results_tabs.addTab(self.summary_widget, "📈 Summary")
        
        layout.addWidget(self.results_tabs)
        
        return panel
    
    def _create_results_table(self) -> QTableWidget:
        """
        Create the results table widget.
        
        Returns:
            QTableWidget: Configured table for displaying trial results
        """
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Trial",
            "Strategy",
            "Latency (s)",
            "Distance (cm)",
            "Efficiency",
            "Score"
        ])
        
        # Configure table properties
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                gridline-color: #555;
                background-color: #2b2b2b;
                color: #fff;
                alternate-background-color: #333;
                selection-background-color: #0d47a1;
            }
            QTableWidget::item {
                padding: 5px;
                background-color: #2b2b2b;
                color: #fff;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #fff;
                padding: 8px;
                border: 1px solid #555;
                font-weight: bold;
            }
        """)
        
        # Resize columns
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        
        return table
    
    def _create_heatmap_widget(self) -> QWidget:
        """
        Create the heatmap display widget.
        
        Note: This is a placeholder. In the full implementation, this will
        contain an embedded matplotlib FigureCanvas.
        
        Returns:
            QWidget: Container for heatmap visualization
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Placeholder label
        placeholder = QLabel("Heatmap visualization will appear here\n\n"
                           "Generate a heatmap after running analysis")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 14px;
                font-style: italic;
            }
        """)
        layout.addWidget(placeholder)
        
        # TODO: Add matplotlib FigureCanvas
        # from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        # from matplotlib.figure import Figure
        # self.figure = Figure(figsize=(8, 6))
        # self.canvas = FigureCanvasQTAgg(self.figure)
        # layout.addWidget(self.canvas)
        
        return widget
    
    def _create_summary_widget(self) -> QWidget:
        """
        Create the summary statistics widget.
        
        Returns:
            QWidget: Container for summary statistics and charts
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Summary text display
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #fff;
                border: 1px solid #555;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        self.summary_text.setPlaceholderText(
            "Summary statistics will appear here after analysis"
        )
        layout.addWidget(self.summary_text)
        
        return widget
    
    def _create_menu_bar(self) -> None:
        """Create the main menu bar with File, View, Tools, and Help menus."""
        menubar = self.menuBar()
        
        # --- File Menu ---
        file_menu = menubar.addMenu("&File")
        
        # Load action
        load_action = QAction("&Load Experiment...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.setStatusTip("Load an experiment file or directory")
        load_action.triggered.connect(self._on_load_experiment)
        file_menu.addAction(load_action)
        
        # Load directory action
        load_dir_action = QAction("Load &Directory...", self)
        load_dir_action.setShortcut("Ctrl+D")
        load_dir_action.setStatusTip("Load all files from a directory")
        load_dir_action.triggered.connect(self._on_load_directory)
        file_menu.addAction(load_dir_action)
        
        file_menu.addSeparator()
        
        # Save results action
        self.save_results_action = QAction("&Save Results...", self)
        self.save_results_action.setShortcut("Ctrl+S")
        self.save_results_action.setStatusTip("Save analysis results to CSV")
        self.save_results_action.setEnabled(False)
        self.save_results_action.triggered.connect(self._on_save_results)
        file_menu.addAction(self.save_results_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # --- View Menu ---
        view_menu = menubar.addMenu("&View")
        
        # Zoom actions (placeholder for future implementation)
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.setEnabled(False)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.setEnabled(False)
        view_menu.addAction(zoom_out_action)
        
        view_menu.addSeparator()
        
        # Dark mode toggle (placeholder)
        self.dark_mode_action = QAction("&Dark Mode", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(False)
        self.dark_mode_action.setEnabled(False)
        self.dark_mode_action.triggered.connect(self._on_toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        
        # --- Tools Menu ---
        tools_menu = menubar.addMenu("&Tools")
        
        # Settings action
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Open settings dialog")
        settings_action.triggered.connect(self._on_open_settings)
        tools_menu.addAction(settings_action)
        
        # ROI Manager action
        roi_action = QAction("&ROI Manager...", self)
        roi_action.setStatusTip("Manage regions of interest")
        roi_action.setEnabled(False)
        roi_action.triggered.connect(self._on_open_roi_manager)
        tools_menu.addAction(roi_action)
        
        # --- Help Menu ---
        help_menu = menubar.addMenu("&Help")
        
        # Documentation action
        docs_action = QAction("&Documentation", self)
        docs_action.setShortcut("F1")
        docs_action.triggered.connect(self._on_show_documentation)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&About Pathfinder", self)
        about_action.triggered.connect(self._on_show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self) -> None:
        """Create the status bar with operation status and metadata."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Main status message
        self.status_bar.showMessage("Ready")
        
        # Trial count (permanent widget on right)
        self.status_trial_label = QLabel("Trials: 0")
        self.status_trial_label.setStyleSheet("padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.status_trial_label)
        
        # Last update time
        self.status_time_label = QLabel("Last update: Never")
        self.status_time_label.setStyleSheet("padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.status_time_label)
    
    def _connect_signals(self) -> None:
        """Connect internal signals to slots."""
        # Button connections
        self.load_button.clicked.connect(self._on_load_experiment)
        self.settings_button.clicked.connect(self._on_open_settings)
        self.analyze_button.clicked.connect(self._on_run_analysis)
        
        # Custom signal connections
        self.loaded_experiment.connect(self._on_experiment_loaded)
        self.analysis_complete.connect(self._on_analysis_finished)
        self.error.connect(self._on_error_occurred)
    
    # --- Event Handlers (Menu Actions) ---
    
    def _on_load_experiment(self) -> None:
        """Handle Load Experiment action - delegated to integration layer."""
        # This will be handled by the integration layer
        pass
    
    def _on_load_directory(self) -> None:
        """Handle Load Directory action."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Experiment Directory"
        )
        
        if dir_path:
            self._load_experiment_directory(dir_path)
    
    def _on_save_results(self) -> None:
        """Handle Save Results action."""
        if not self.current_results:
            QMessageBox.warning(
                self,
                "No Results",
                "No analysis results available to save."
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            "pathfinder_results.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self._save_results_to_file(file_path)
    
    def _on_open_settings(self) -> None:
        """Handle Settings action - delegated to integration layer."""
        # This will be handled by the integration layer
        pass
    
    def _on_open_roi_manager(self) -> None:
        """Handle ROI Manager action."""
        # TODO: Open ROIManagerDialog
        QMessageBox.information(
            self,
            "ROI Manager",
            "ROI Manager dialog will be implemented in the next phase.\n\n"
            "This will allow you to manage multiple regions of interest."
        )
    
    def _on_toggle_dark_mode(self, checked: bool) -> None:
        """
        Handle Dark Mode toggle action.
        
        Args:
            checked: Whether dark mode is enabled
        """
        # TODO: Implement dark mode styling
        mode = "dark" if checked else "light"
        self.status_bar.showMessage(f"Switched to {mode} mode")
    
    def _on_show_documentation(self) -> None:
        """Handle Documentation action."""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation will open in your default browser.\n\n"
            "For now, please refer to the README.md file."
        )
    
    def _on_show_about(self) -> None:
        """Handle About action."""
        QMessageBox.about(
            self,
            "About Pathfinder",
            "<h2>Pathfinder</h2>"
            "<p><b>Morris Water Maze Analysis Tool</b></p>"
            "<p>Version: 2.0 (PyQt6 Edition)</p>"
            "<p>Automated classification of search strategies in spatial navigation tasks.</p>"
            "<p>Built with PyQt6 and Python</p>"
            "<p>© 2026 OpenClaw Agent</p>"
        )
    
    # --- Event Handlers (Button Actions) ---
    
    def _on_run_analysis(self) -> None:
        """Handle Analyze button click - delegated to integration layer."""
        # This will be handled by the integration layer
        pass
    
    # --- Slot Handlers (Custom Signals) ---
    
    def _on_experiment_loaded(self, experiment: Any) -> None:
        """
        Handle experiment loaded signal.
        
        Args:
            experiment: The loaded experiment object
        """
        self.current_experiment = experiment
        
        # Enable analyze button
        self.analyze_button.setEnabled(True)
        
        # Update status
        self._update_status("Experiment loaded successfully")
        self._update_last_update_time()
    
    def _on_analysis_finished(self, results: Dict[str, Any]) -> None:
        """
        Handle analysis complete signal.
        
        Args:
            results: Analysis results dictionary
        """
        self.current_results = results
        
        # Update results table
        self._populate_results_table(results)
        
        # Enable save action
        self.save_results_action.setEnabled(True)
        
        # Update status
        trial_count = len(results.get('trials', []))
        self._update_status(f"Analysis complete: {trial_count} trials processed")
        self._update_last_update_time()
        
        # Reset progress bar
        self.progress_bar.setValue(100)
        
        # Re-enable analyze button
        self.analyze_button.setEnabled(True)
    
    def _on_error_occurred(self, message: str) -> None:
        """
        Handle error signal.
        
        Args:
            message: Error message to display
        """
        QMessageBox.critical(
            self,
            "Error",
            f"An error occurred:\n\n{message}"
        )
        
        self._update_status(f"Error: {message}")
        self.analyze_button.setEnabled(True)
        self.progress_bar.setValue(0)
    
    # --- Helper Methods ---
    
    def _load_experiment_file(self, file_path: str) -> None:
        """
        Load an experiment from a single file.
        
        This method is kept for compatibility but actual loading
        is handled by the integration layer.
        
        Args:
            file_path: Path to the experiment file
        """
        # Deprecated - handled by integration layer
        pass
    
    def _load_experiment_directory(self, dir_path: str) -> None:
        """
        Load experiments from a directory.
        
        Args:
            dir_path: Path to the directory containing experiment files
        """
        # TODO: Implement directory loading (Phase 2)
        self._update_status(f"Loading experiments from {Path(dir_path).name}...")
        QMessageBox.information(
            self,
            "Directory Loading",
            "Directory loading will be implemented in Phase 2.\n\n"
            "For now, please load individual files."
        )
    
    def _save_results_to_file(self, file_path: str) -> None:
        """
        Save analysis results to a CSV file.
        
        Args:
            file_path: Path where results should be saved
        """
        if not self.current_results:
            return
        
        try:
            import csv
            
            self._update_status(f"Saving results to {Path(file_path).name}...")
            
            # Get trials from results dict
            trials = self.current_results.get('trials', [])
            
            if not trials:
                QMessageBox.warning(self, "No Results", "No trial results to save")
                return
            
            # Write to CSV
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Trial', 'Strategy', 'Latency (s)', 
                    'Distance (cm)', 'Efficiency', 'Score'
                ])
                
                # Data rows
                for trial in trials:
                    writer.writerow([
                        trial.get('trial_id', ''),
                        trial.get('strategy', ''),
                        f"{trial.get('latency', 0.0):.2f}",
                        f"{trial.get('distance', 0.0):.2f}",
                        f"{trial.get('efficiency', 0.0):.3f}",
                        f"{trial.get('score', 0.0):.1f}",
                    ])
            
            self._update_status(f"Results saved to {Path(file_path).name}")
            QMessageBox.information(
                self,
                "Saved",
                f"Results successfully saved to:\n{file_path}"
            )
            
        except Exception as e:
            self.error.emit(f"Failed to save results: {str(e)}")
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save results:\n{str(e)}"
            )
    
    def _populate_results_table(self, results: Dict[str, Any]) -> None:
        """
        Populate the results table with analysis data.
        
        Args:
            results: Analysis results dictionary
        """
        trials = results.get('trials', [])
        
        self.results_table.setRowCount(len(trials))
        
        for row, trial in enumerate(trials):
            # Trial ID
            self.results_table.setItem(
                row, 0, QTableWidgetItem(str(trial.get('trial_id', '')))
            )
            
            # Strategy
            self.results_table.setItem(
                row, 1, QTableWidgetItem(trial.get('strategy', ''))
            )
            
            # Latency
            latency = trial.get('latency', 0.0)
            self.results_table.setItem(
                row, 2, QTableWidgetItem(f"{latency:.2f}")
            )
            
            # Distance
            distance = trial.get('distance', 0.0)
            self.results_table.setItem(
                row, 3, QTableWidgetItem(f"{distance:.2f}")
            )
            
            # Efficiency
            efficiency = trial.get('efficiency', 0.0)
            self.results_table.setItem(
                row, 4, QTableWidgetItem(f"{efficiency:.3f}")
            )
            
            # Score
            score = trial.get('score', 0.0)
            self.results_table.setItem(
                row, 5, QTableWidgetItem(f"{score:.1f}")
            )
        
        # Update trial count in status bar
        self.status_trial_label.setText(f"Trials: {len(trials)}")
    
    def _update_status(self, message: str) -> None:
        """
        Update the status bar message.
        
        Args:
            message: Status message to display
        """
        self.status_bar.showMessage(message)
        self.status_label.setText(message)
    
    def _update_last_update_time(self) -> None:
        """Update the last update time in the status bar."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.status_time_label.setText(f"Last update: {current_time}")
    
    def update_progress(self, current: int, total: int) -> None:
        """
        Update the progress bar.
        
        This method is designed to be called by worker threads.
        
        Args:
            current: Current progress value
            total: Total progress value (maximum)
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{current}/{total} trials ({percentage}%)")
