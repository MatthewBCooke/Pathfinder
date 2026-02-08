#!/usr/bin/env python3
"""
Pathfinder GUI - Main entry point.
Morris Water Maze Search Strategy Analysis Tool.
"""

import sys
import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from gui.main_window import PathfinderMainWindow
from gui.integration import PathfinderIntegration


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pathfinder.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    logger.info("Starting Pathfinder GUI v2.0")
    
    # Enable high DPI scaling (must be set before creating QApplication)
    from PyQt5.QtCore import Qt
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Pathfinder")
    app.setOrganizationName("Johns Lab")
    app.setOrganizationDomain("github.com/MatthewBCooke")
    
    # Create main window
    main_window = PathfinderMainWindow()
    
    # Create integration layer (wires everything together)
    integration = PathfinderIntegration(main_window)
    # Connect folder load signal
    main_window.get_control_panel().load_folder_requested.connect(integration.on_load_folder)
    
    # Show window
    main_window.show()
    
    logger.info("Application window shown")
    
    # Run event loop
    exit_code = app.exec_()
    
    # Cleanup
    integration.cleanup()
    
    logger.info(f"Application exiting with code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
