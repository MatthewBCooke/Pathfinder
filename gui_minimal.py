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
        self.table.setColumnCount(20)  # Will be resized based on CSV
        self.table.setHorizontalHeaderLabels(["Row #"] + [f"Col {i}" for i in range(19)])
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
            
            # Determine number of columns
            max_cols = max(len(row) for row in data_rows) if data_rows else 0
            total_cols = max_cols + 1  # +1 for row number column
            
            # Set table size
            self.table.setColumnCount(total_cols)
            self.table.setRowCount(len(data_rows))
            
            # Set table headers from first row if it has header
            if has_header and rows[0]:
                headers = ["Row #"] + rows[0]
                self.table.setHorizontalHeaderLabels(headers[:total_cols])
            else:
                headers = ["Row #"] + [f"Col {i}" for i in range(max_cols)]
                self.table.setHorizontalHeaderLabels(headers[:total_cols])
            
            for row_idx, row in enumerate(data_rows):
                # Row number (sequential from 1)
                item = QTableWidgetItem(str(row_idx + 1))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                self.table.setItem(row_idx, 0, item)
                
                # All columns from CSV
                for col_idx in range(len(row)):
                    try:
                        val = row[col_idx]
                        # Try to convert to float for display
                        if val:
                            try:
                                fval = float(val)
                                val = f"{fval:.2f}"
                            except:
                                pass
                        item = QTableWidgetItem(str(val))
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                        self.table.setItem(row_idx, col_idx + 1, item)  # +1 for row number column
                    except:
                        pass
            
            # Update label with column info
            file_name = Path(file_path).name
            cols = total_cols - 1  # Exclude row number column
            col_names = ", ".join(rows[0][:3]) + ("..." if len(rows[0]) > 3 else "") if has_header else f"{cols} columns"
            self.file_label.setText(f"✓ Loaded: {file_name} ({len(data_rows)} rows, {cols} cols: {col_names})")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
    
    def _looks_like_header(self, row):
        """Check if first row looks like a header (contains non-numeric values)."""
        if not row or len(row) < 1:
            return False
        
        # Check first column - if it's not numeric, likely a header
        first_val = str(row[0]).strip().lower()
        
        # Common header names
        header_keywords = ['time', 'x', 'y', 't', 'col', 'column', 'frame', 'id', 'name', 'label']
        
        # If first value is a known header keyword or non-numeric, treat as header
        is_keyword = any(kw in first_val for kw in header_keywords)
        
        try:
            float(row[0])
            is_numeric = True
        except:
            is_numeric = False
        
        # It's a header if it's NOT numeric OR contains header keywords
        return (not is_numeric) or is_keyword


def main():
    app = QApplication(sys.argv)
    window = PathfinderMinimal()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
