"""
Main window for Pathfinder GUI application.
Handles layout and widget composition.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QMenuBar, QMenu, QAction,
    QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from pathlib import Path

from .control_panel import ControlPanelWidget
from .results_table import ResultsTableWidget
from .summary_widget import SummaryWidget
from .heatmap_widget import HeatmapWidget


class PathfinderMainWindow(QMainWindow):
    """
    Main application window with:
    - Control panel (left sidebar)
    - Results tabs (right side): table, summary, heatmap
    - Menu bar and status bar
    """
    
    # Signals for high-level events
    exit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
    
    def _init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Pathfinder - Morris Water Maze Analysis")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Control panel
        self.control_panel = ControlPanelWidget()
        self.control_panel.setMinimumWidth(300)
        self.control_panel.setMaximumWidth(500)
        splitter.addWidget(self.control_panel)
        
        # Right panel: Results tabs
        self.results_tabs = QTabWidget()
        self.results_tabs.setTabPosition(QTabWidget.North)
        
        # Create tab widgets
        self.results_table = ResultsTableWidget()
        self.summary_widget = SummaryWidget()
        self.heatmap_widget = HeatmapWidget()
        
        # Add tabs
        self.results_tabs.addTab(self.results_table, "📊 Results Table")
        self.results_tabs.addTab(self.summary_widget, "📈 Summary")
        self.results_tabs.addTab(self.heatmap_widget, "🗺️ Heatmap")
        
        splitter.addWidget(self.results_tabs)
        
        # Set initial splitter sizes (30% control, 70% results)
        splitter.setSizes([350, 1050])
        
        main_layout.addWidget(splitter)
    
    def _create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Experiment...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.control_panel.load_clicked.emit)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("&Export Results...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.control_panel.export_clicked.emit)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Analysis menu
        analysis_menu = menubar.addMenu("&Analysis")
        
        run_action = QAction("&Run Analysis", self)
        run_action.setShortcut("Ctrl+R")
        run_action.triggered.connect(self.control_panel.analyze_clicked.emit)
        analysis_menu.addAction(run_action)
        
        analysis_menu.addSeparator()
        
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.control_panel.settings_clicked.emit)
        analysis_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        table_action = QAction("Results &Table", self)
        table_action.triggered.connect(lambda: self.results_tabs.setCurrentIndex(0))
        view_menu.addAction(table_action)
        
        summary_action = QAction("&Summary", self)
        summary_action.triggered.connect(lambda: self.results_tabs.setCurrentIndex(1))
        view_menu.addAction(summary_action)
        
        heatmap_action = QAction("&Heatmap", self)
        heatmap_action.triggered.connect(lambda: self.results_tabs.setCurrentIndex(2))
        view_menu.addAction(heatmap_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About Pathfinder", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("&Documentation", self)
        help_menu.addAction(docs_action)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Pathfinder",
            "<h3>Pathfinder v2.0</h3>"
            "<p>Morris Water Maze Search Strategy Analysis</p>"
            "<p>Modernized GUI with PyQt5</p>"
            "<p>© 2026 Johns Lab</p>"
            "<p><a href='https://github.com/MatthewBCooke/Pathfinder'>GitHub Repository</a></p>"
        )
    
    # Public accessors for integration layer
    
    def get_control_panel(self) -> ControlPanelWidget:
        """Get control panel widget for signal connections"""
        return self.control_panel
    
    def get_results_table(self) -> ResultsTableWidget:
        """Get results table widget"""
        return self.results_table
    
    def get_summary_widget(self) -> SummaryWidget:
        """Get summary widget"""
        return self.summary_widget
    
    def get_heatmap_widget(self) -> HeatmapWidget:
        """Get heatmap widget"""
        return self.heatmap_widget
    
    def set_status_message(self, message: str):
        """Update status bar message"""
        self.status_bar.showMessage(message)
    
    def show_error(self, title: str, message: str):
        """Show error dialog"""
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title: str, message: str):
        """Show warning dialog"""
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title: str, message: str):
        """Show info dialog"""
        QMessageBox.information(self, title, message)
    
    def ask_yes_no(self, title: str, question: str) -> bool:
        """Show yes/no question dialog"""
        reply = QMessageBox.question(
            self, title, question,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Ask for confirmation if analysis is running
        # (This will be connected by integration layer)
        self.exit_requested.emit()
        
        # Accept by default (integration layer can reject if needed)
        event.accept()
