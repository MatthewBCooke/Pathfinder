#!/usr/bin/env python3
"""
Quick test of the spatial parameters display.
Shows what the settings display looks like.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.control_panel import ControlPanelWidget


def main():
    """Show the control panel with spatial parameters display"""
    app = QApplication(sys.argv)

    # Create control panel
    panel = ControlPanelWidget()
    panel.setWindowTitle("Pathfinder - Maze Geometry Settings")
    panel.resize(400, 800)
    panel.show()

    print("=" * 60)
    print("SPATIAL PARAMETERS DISPLAY TEST")
    print("=" * 60)
    print("\nThe control panel should show:")
    print("  1. Input fields for all 6 spatial parameters")
    print("  2. A formatted display showing current settings")
    print("  3. Real-time validation (platform within pool, etc.)")
    print("\nTry:")
    print("  - Adjusting the spinbox values")
    print("  - The display updates automatically")
    print("  - Watch for validation warnings")
    print("  - Click 'Apply Geometry' to emit the signal")
    print("=" * 60)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
