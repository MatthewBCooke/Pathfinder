#!/usr/bin/env python3
"""
Pathfinder GUI - PyQt6 Modern Interface

Entry point for the Pathfinder analysis tool with a modern PyQt6 interface.
Replaces the legacy tkinter version in Pathfinder.py.

Usage:
    python pathfinder_gui.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Launch the Pathfinder GUI application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Pathfinder")
    app.setApplicationVersion("2.0.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
