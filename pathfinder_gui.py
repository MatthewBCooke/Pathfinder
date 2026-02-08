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
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Pathfinder")
    app.setOrganizationName("Johns Lab")
    app.setOrganizationDomain("github.com/MatthewBCooke")
    
    # Enable high DPI scaling
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create main window
    main_window = PathfinderMainWindow()
    
    # Create integration layer (wires everything together)
    integration = PathfinderIntegration(main_window)
    
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
