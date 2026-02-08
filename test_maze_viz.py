#!/usr/bin/env python3
"""
Test the maze visualization widget standalone.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.maze_visualization import MazeVisualizationWidget


def main():
    """Test maze visualization"""
    app = QApplication(sys.argv)

    # Create widget
    viz = MazeVisualizationWidget()
    viz.setWindowTitle("Pathfinder - Maze Visualization Test")
    viz.resize(800, 800)

    print("=" * 60)
    print("MAZE VISUALIZATION TEST")
    print("=" * 60)
    print("\nThe visualization should show:")
    print("  🔵 Pool circle (blue)")
    print("  🔴 Platform circle (red)")
    print("  ⚫ Thigmotaxis zone (gray annulus near wall)")
    print("  🟡 Chaining zone (yellow circle around platform)")
    print("  🟢 Direct swim corridor (green wedge to platform)")
    print("\nTry updating parameters:")
    print("  viz.update_parameters({")
    print("      'pool_diameter': 400,")
    print("      'platform_x': 300,")
    print("      'platform_y': 200,")
    print("  })")
    print("=" * 60)

    viz.show()

    # Test parameter update after 2 seconds
    from PyQt5.QtCore import QTimer
    def test_update():
        print("\nUpdating visualization parameters...")
        viz.update_parameters({
            'pool_diameter': 400,
            'platform_x': 300,
            'platform_y': 100,
            'platform_diameter': 40
        })

    QTimer.singleShot(2000, test_update)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
