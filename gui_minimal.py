#!/usr/bin/env python3
"""
Minimal working Pathfinder GUI - stripped down to essentials.
No complex dependencies, just load CSV and display.
"""

import sys
import csv
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class PathfinderMinimal(QMainWindow):
    """Minimal Pathfinder GUI - just load CSV and display."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pathfinder - Minimal GUI")
        self.setGeometry(100, 100, 1200, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Top: Load button
        top_layout = QHBoxLayout()
        self.load_btn = QPushButton("📂 Load CSV File")
        self.load_btn.setMinimumHeight(40)
        self.load_btn.clicked.connect(self.load_file)
        top_layout.addWidget(self.load_btn)
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setMinimumHeight(40)
        top_layout.addWidget(self.file_label)
        
        layout.addLayout(top_layout)
        
        # Bottom: Results table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Row #", "Time", "X", "Y", "Notes"])
        layout.addWidget(self.table)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #fff; }
            QPushButton { background-color: #0d47a1; color: white; border: none; border-radius: 4px; padding: 8px; }
            QPushButton:hover { background-color: #1565c0; }
            QTableWidget { background-color: #2b2b2b; color: #fff; gridline-color: #555; }
            QHeaderView::section { background-color: #404040; color: #fff; padding: 5px; }
            QTableWidget::item { padding: 5px; }
        """)
    
    def load_file(self):
        """Load CSV file and display in table."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Read CSV
            rows = []
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    rows.append(row)
            
            if not rows:
                QMessageBox.warning(self, "Error", "CSV file is empty")
                return
            
            # Detect header
            has_header = self._looks_like_header(rows[0])
            start_idx = 1 if has_header else 0
            data_rows = rows[start_idx:]
            
            if not data_rows:
                QMessageBox.warning(self, "Error", "No data rows in CSV")
                return
            
            # Display in table
            self.table.setRowCount(len(data_rows))
            
            for row_idx, row in enumerate(data_rows):
                # Row number
                item = QTableWidgetItem(str(row_idx + 1))
                self.table.setItem(row_idx, 0, item)
                
                # First 4 columns (time, x, y, other)
                for col_idx in range(1, min(5, len(row) + 1)):
                    try:
                        val = row[col_idx - 1] if col_idx - 1 < len(row) else ""
                        # Try to convert to float for display
                        if val:
                            try:
                                fval = float(val)
                                val = f"{fval:.2f}"
                            except:
                                pass
                        item = QTableWidgetItem(str(val))
                        self.table.setItem(row_idx, col_idx, item)
                    except:
                        pass
            
            # Update label
            file_name = Path(file_path).name
            self.file_label.setText(f"✓ Loaded: {file_name} ({len(data_rows)} rows)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
    
    def _looks_like_header(self, row):
        """Check if first row looks like a header (contains non-numeric values)."""
        if not row or len(row) < 3:
            return False
        
        # Count numeric values
        numeric_count = 0
        for val in row[:3]:
            try:
                float(val)
                numeric_count += 1
            except:
                pass
        
        # If all first 3 are numeric, probably data not header
        return numeric_count < 3


def main():
    app = QApplication(sys.argv)
    window = PathfinderMinimal()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
