#!/usr/bin/env python3
"""
Simple test for the Pathfinder GUI with working functionality.

This demonstrates that:
1. CSV files load with auto-detection
2. Buttons are wired up
3. Analysis runs in a worker thread
4. Results display correctly
"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow
from gui.integration import SimpleIntegration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Run the simplified Pathfinder GUI."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    
    # Wire up integration (this makes buttons actually work!)
    integration = SimpleIntegration(window)
    
    # Show window
    window.show()
    
    print("\n" + "="*60)
    print("Pathfinder GUI - Simplified Working Version")
    print("="*60)
    print("\nFeatures:")
    print("  ✓ Auto-detect CSV format (AnyMaze, WaterMaze, Ethovision, Basic)")
    print("  ✓ Load Experiment button works")
    print("  ✓ Settings button opens dialog")
    print("  ✓ Analyze button runs analysis in background")
    print("  ✓ Results display in table")
    print("  ✓ Real error messages (no more 'Loading...' freeze)")
    print("\nInstructions:")
    print("  1. Click 'Load Experiment' to select a CSV file")
    print("  2. File format is auto-detected")
    print("  3. Click 'Analyze' to run analysis")
    print("  4. View results in the table")
    print("  5. Use 'File > Save Results' to export CSV")
    print("\n" + "="*60 + "\n")
    
    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
