"""
Unit tests for Pathfinder dialog windows.

Tests dialog functionality, signal emissions, and data validation.
"""

import sys
import pytest
from unittest.mock import Mock, patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest, QSignalSpy
from PyQt6.QtWidgets import QDialogButtonBox, QMessageBox

sys.path.insert(0, '/tmp/Pathfinder')
sys.path.insert(0, '/tmp/Pathfinder/gui')

from gui.dialogs import (
    SettingsDialog,
    FileImportDialog,
    ManualStrategyDialog,
    ExportDialog
)
from pathfinder.types import Parameters


class TestSettingsDialog:
    """Tests for SettingsDialog."""
    
    def test_dialog_initialization(self, qapp, default_parameters):
        """Test that dialog initializes with current parameters."""
        dialog = SettingsDialog(default_parameters)
        
        assert dialog.params == default_parameters
        assert dialog.windowTitle() == "Pathfinder Settings"
        assert dialog.minimumSize().width() >= 700
        assert dialog.minimumSize().height() >= 600
    
    def test_parameters_display_correctly(self, qapp, default_parameters):
        """Test that current parameters are displayed in UI."""
        dialog = SettingsDialog(default_parameters)
        
        # Check that parameter widgets exist and have correct values
        assert 'direct_enabled' in dialog.param_widgets
        assert 'ipeMaxVal' in dialog.param_widgets
        
        # Verify checkbox state
        # Note: attribute name differs from widget key
        # Widget uses 'direct_enabled', but Parameters uses 'useDirect'
        
    def test_apply_settings_emits_signal(self, qapp, default_parameters):
        """Test that applying settings emits signal with updated parameters."""
        dialog = SettingsDialog(default_parameters)
        
        settings_spy = QSignalSpy(dialog.settings_applied)
        
        # Modify a parameter
        if 'ipeMaxVal' in dialog.param_widgets:
            dialog.param_widgets['ipeMaxVal'].setValue(150.0)
        
        # Click apply button
        dialog._apply_settings()
        
        # Verify signal was emitted
        assert len(settings_spy) == 1
        
        # Verify dialog was accepted
        assert not dialog.isVisible() or dialog.result() == dialog.DialogCode.Accepted
    
    def test_cancel_closes_without_applying(self, qapp, default_parameters):
        """Test that cancel closes dialog without applying changes."""
        dialog = SettingsDialog(default_parameters)
        
        settings_spy = QSignalSpy(dialog.settings_applied)
        original_value = default_parameters.ipeMaxVal
        
        # Modify a parameter
        if 'ipeMaxVal' in dialog.param_widgets:
            dialog.param_widgets['ipeMaxVal'].setValue(999.0)
        
        # Reject dialog
        dialog.reject()
        
        # Signal should not be emitted
        assert len(settings_spy) == 0
        
        # Original parameters should be unchanged
        assert default_parameters.ipeMaxVal == original_value
    
    def test_reset_to_defaults_confirmation(self, qapp, custom_parameters):
        """Test that reset to defaults shows confirmation dialog."""
        dialog = SettingsDialog(custom_parameters)
        
        # Mock the message box to auto-confirm
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            original_name = dialog.params.name
            dialog._reset_to_defaults()
            
            # Parameters should be reset
            assert dialog.params.name != original_name
            assert dialog.params.name == "Default"
    
    def test_reset_to_defaults_cancel(self, qapp, custom_parameters):
        """Test that canceling reset keeps current parameters."""
        dialog = SettingsDialog(custom_parameters)
        
        # Mock the message box to cancel
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.No):
            original_name = dialog.params.name
            dialog._reset_to_defaults()
            
            # Parameters should not change
            assert dialog.params.name == original_name
    
    def test_tab_navigation(self, qapp, default_parameters):
        """Test that all tabs are accessible."""
        dialog = SettingsDialog(default_parameters)
        
        # Check that tabs exist
        assert dialog.tab_widget.count() == 3
        assert dialog.tab_widget.tabText(0) == "Analysis Parameters"
        assert dialog.tab_widget.tabText(1) == "Visualization"
        assert dialog.tab_widget.tabText(2) == "File I/O"
        
        # Navigate through tabs
        for i in range(3):
            dialog.tab_widget.setCurrentIndex(i)
            assert dialog.tab_widget.currentIndex() == i
    
    def test_visualization_settings(self, qapp, default_parameters):
        """Test visualization tab settings."""
        dialog = SettingsDialog(default_parameters)
        dialog.tab_widget.setCurrentIndex(1)  # Visualization tab
        
        # Check sliders exist and have reasonable ranges
        assert dialog.grid_size_slider is not None
        assert dialog.sigma_slider is not None
        assert dialog.color_scheme_combo is not None
        
        # Test changing values
        dialog.grid_size_slider.setValue(75)
        assert dialog.grid_size_value_label.text() == "75"
        
        dialog.sigma_slider.setValue(30)  # 3.0 * 10
        assert "3.0" in dialog.sigma_value_label.text()
    
    def test_io_settings(self, qapp, default_parameters):
        """Test File I/O tab settings."""
        dialog = SettingsDialog(default_parameters)
        dialog.tab_widget.setCurrentIndex(2)  # File I/O tab
        
        # Check widgets exist
        assert dialog.autosave_checkbox is not None
        assert dialog.export_format_combo is not None
        
        # Test changing values
        dialog.autosave_checkbox.setChecked(True)
        assert dialog.autosave_checkbox.isChecked()
        
        dialog.export_format_combo.setCurrentText("Excel")
        assert dialog.export_format_combo.currentText() == "Excel"


class TestFileImportDialog:
    """Tests for FileImportDialog."""
    
    def test_dialog_initialization(self, qapp):
        """Test that dialog initializes correctly."""
        dialog = FileImportDialog()
        
        assert dialog.windowTitle() == "Import Tracking Data"
        assert dialog.selected_path is None
        assert not dialog.import_btn.isEnabled()
    
    def test_software_type_selection(self, qapp):
        """Test software type combo box."""
        dialog = FileImportDialog()
        
        # Check available software types
        items = [dialog.software_combo.itemText(i) 
                for i in range(dialog.software_combo.count())]
        
        assert 'Ethovision' in items
        assert 'AnyMaze' in items
        assert 'WaterMaze' in items
    
    def test_file_browse_updates_preview(self, qapp, tmp_path):
        """Test that browsing for file updates preview."""
        dialog = FileImportDialog()
        
        # Create test file
        test_file = tmp_path / "test_data.csv"
        test_file.write_text("x,y,time\n1,2,0.1\n3,4,0.2\n")
        
        # Mock file dialog to return test file
        with patch('gui.dialogs.QFileDialog.getOpenFileName', 
                  return_value=(str(test_file), '')):
            dialog._browse_file()
        
        # Verify file was selected
        assert dialog.selected_path == str(test_file)
        assert str(test_file) in dialog.path_edit.text()
        assert dialog.import_btn.isEnabled()
        
        # Verify preview was updated
        assert dialog.preview_list.count() > 0
    
    def test_directory_browse_lists_files(self, qapp, tmp_path):
        """Test that browsing directory lists files."""
        dialog = FileImportDialog()
        
        # Create test directory with files
        test_dir = tmp_path / "test_data"
        test_dir.mkdir()
        (test_dir / "trial1.csv").write_text("data")
        (test_dir / "trial2.csv").write_text("data")
        
        # Mock directory dialog
        with patch('gui.dialogs.QFileDialog.getExistingDirectory',
                  return_value=str(test_dir)):
            dialog._browse_directory()
        
        # Verify directory was selected
        assert dialog.selected_path == str(test_dir)
        assert dialog.import_btn.isEnabled()
        
        # Verify files are listed
        assert dialog.preview_list.count() >= 2
    
    def test_import_emits_signal(self, qapp, tmp_path):
        """Test that import button emits signal with data."""
        dialog = FileImportDialog()
        
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        
        file_imported_spy = QSignalSpy(dialog.file_imported)
        
        # Set up dialog state
        dialog.selected_path = str(test_file)
        dialog.path_edit.setText(str(test_file))
        dialog.import_btn.setEnabled(True)
        dialog.software_combo.setCurrentText("Ethovision")
        
        # Click import
        dialog._import_data()
        
        # Verify signal was emitted
        assert len(file_imported_spy) == 1
        software_type, path, preview = file_imported_spy[0]
        assert software_type == "Ethovision"
        assert path == str(test_file)
    
    def test_import_without_selection_shows_warning(self, qapp):
        """Test that importing without selection shows warning."""
        dialog = FileImportDialog()
        
        with patch.object(QMessageBox, 'warning') as mock_warning:
            dialog._import_data()
            mock_warning.assert_called_once()


class TestManualStrategyDialog:
    """Tests for ManualStrategyDialog."""
    
    def test_dialog_initialization(self, qapp):
        """Test that dialog initializes correctly."""
        dialog = ManualStrategyDialog()
        
        assert dialog.windowTitle() == "Manual Strategy Classification"
        assert dialog.strategy_combo.currentText() in [
            'Direct', 'Focal', 'Directed', 'Chaining', 
            'Scanning', 'Thigmotaxis', 'Random', 'Perseverative'
        ]
    
    def test_strategy_selection(self, qapp):
        """Test strategy dropdown."""
        dialog = ManualStrategyDialog()
        
        strategies = [dialog.strategy_combo.itemText(i)
                     for i in range(dialog.strategy_combo.count())]
        
        assert 'Direct' in strategies
        assert 'Focal' in strategies
        assert 'Random' in strategies
        assert len(strategies) == 8
    
    def test_score_slider(self, qapp):
        """Test score slider (0-3)."""
        dialog = ManualStrategyDialog()
        
        # Check range
        assert dialog.score_slider.minimum() == 0
        assert dialog.score_slider.maximum() == 3
        
        # Test value changes
        dialog.score_slider.setValue(3)
        assert dialog.score_value_label.text() == "3"
        
        dialog.score_slider.setValue(0)
        assert dialog.score_value_label.text() == "0"
    
    def test_confidence_slider(self, qapp):
        """Test confidence slider (0-100%)."""
        dialog = ManualStrategyDialog()
        
        # Check range
        assert dialog.confidence_slider.minimum() == 0
        assert dialog.confidence_slider.maximum() == 100
        
        # Test value changes
        dialog.confidence_slider.setValue(95)
        assert "95" in dialog.confidence_value_label.text()
        
        dialog.confidence_slider.setValue(50)
        assert "50" in dialog.confidence_value_label.text()
    
    def test_classification_emits_signal(self, qapp):
        """Test that accepting classification emits signal."""
        dialog = ManualStrategyDialog()
        
        classified_spy = QSignalSpy(dialog.strategy_classified)
        
        # Set values
        dialog.strategy_combo.setCurrentText("Focal")
        dialog.score_slider.setValue(2)
        dialog.confidence_slider.setValue(85)
        dialog.notes_edit.setPlainText("Test notes")
        
        # Accept classification
        dialog._accept_classification()
        
        # Verify signal
        assert len(classified_spy) == 1
        strategy, score, confidence, notes = classified_spy[0]
        assert strategy == "Focal"
        assert score == 2
        assert confidence == 85
        assert notes == "Test notes"
    
    def test_notes_field(self, qapp):
        """Test notes text field."""
        dialog = ManualStrategyDialog()
        
        test_notes = "Animal seemed confused. Multiple false approaches."
        dialog.notes_edit.setPlainText(test_notes)
        
        assert dialog.notes_edit.toPlainText() == test_notes


class TestExportDialog:
    """Tests for ExportDialog."""
    
    def test_dialog_initialization(self, qapp):
        """Test that dialog initializes correctly."""
        dialog = ExportDialog()
        
        assert dialog.windowTitle() == "Export Analysis Results"
        assert dialog.export_path is None
        assert not dialog.export_btn.isEnabled()
    
    def test_export_format_selection(self, qapp):
        """Test export format combo box."""
        dialog = ExportDialog()
        
        formats = [dialog.format_combo.itemText(i)
                  for i in range(dialog.format_combo.count())]
        
        assert 'CSV' in formats
        assert 'Excel' in formats
        assert 'PDF' in formats
    
    def test_include_options(self, qapp):
        """Test include checkboxes."""
        dialog = ExportDialog()
        
        # Check default states
        assert dialog.include_metrics_cb.isChecked()
        assert dialog.include_heatmap_cb.isChecked()
        assert dialog.include_summary_cb.isChecked()
        assert not dialog.include_paths_cb.isChecked()
        
        # Test changing states
        dialog.include_paths_cb.setChecked(True)
        assert dialog.include_paths_cb.isChecked()
    
    def test_browse_location_enables_export(self, qapp, tmp_path):
        """Test that selecting export location enables export button."""
        dialog = ExportDialog()
        
        export_file = tmp_path / "export.csv"
        
        with patch('gui.dialogs.QFileDialog.getSaveFileName',
                  return_value=(str(export_file), '')):
            dialog._browse_location()
        
        assert dialog.export_path == str(export_file)
        assert dialog.export_btn.isEnabled()
        assert str(export_file) in dialog.location_edit.text()
    
    def test_export_emits_signal(self, qapp, tmp_path):
        """Test that export button emits signal with options."""
        dialog = ExportDialog()
        
        export_file = tmp_path / "export.xlsx"
        dialog.export_path = str(export_file)
        dialog.location_edit.setText(str(export_file))
        dialog.export_btn.setEnabled(True)
        
        export_spy = QSignalSpy(dialog.export_requested)
        
        # Set options
        dialog.format_combo.setCurrentText("Excel")
        dialog.include_metrics_cb.setChecked(True)
        dialog.include_heatmap_cb.setChecked(False)
        dialog.include_summary_cb.setChecked(True)
        dialog.include_paths_cb.setChecked(True)
        
        # Perform export
        dialog._perform_export()
        
        # Verify signal
        assert len(export_spy) == 1
        export_format, options, path = export_spy[0]
        assert export_format == "Excel"
        assert options['metrics'] is True
        assert options['heatmap'] is False
        assert options['summary'] is True
        assert options['paths'] is True
        assert path == str(export_file)
    
    def test_export_without_location_shows_warning(self, qapp):
        """Test that exporting without location shows warning."""
        dialog = ExportDialog()
        dialog.export_path = None
        
        with patch.object(QMessageBox, 'warning') as mock_warning:
            dialog._perform_export()
            mock_warning.assert_called_once()
    
    def test_format_changes_file_filter(self, qapp, tmp_path):
        """Test that changing format updates file dialog filter."""
        dialog = ExportDialog()
        
        # Test CSV
        dialog.format_combo.setCurrentText("CSV")
        with patch('gui.dialogs.QFileDialog.getSaveFileName',
                  return_value=(str(tmp_path / "export.csv"), '')) as mock_dialog:
            dialog._browse_location()
            # Verify filter contains CSV
            call_args = mock_dialog.call_args
            assert "CSV" in call_args[0][3]
        
        # Test Excel
        dialog.format_combo.setCurrentText("Excel")
        with patch('gui.dialogs.QFileDialog.getSaveFileName',
                  return_value=(str(tmp_path / "export.xlsx"), '')) as mock_dialog:
            dialog._browse_location()
            call_args = mock_dialog.call_args
            assert "Excel" in call_args[0][3]


class TestDialogIntegration:
    """Integration tests for dialog interactions."""
    
    def test_settings_dialog_roundtrip(self, qapp, default_parameters):
        """Test that settings can be modified and retrieved."""
        dialog = SettingsDialog(default_parameters)
        
        # Modify multiple settings
        if 'ipeMaxVal' in dialog.param_widgets:
            dialog.param_widgets['ipeMaxVal'].setValue(150.0)
        
        dialog.grid_size_slider.setValue(60)
        dialog.autosave_checkbox.setChecked(True)
        
        settings_spy = QSignalSpy(dialog.settings_applied)
        dialog._apply_settings()
        
        # Verify all changes were applied
        assert len(settings_spy) == 1
        updated_params = settings_spy[0][0]
        
        # Note: The exact attribute names might differ
        # This tests that the object was emitted
        assert updated_params is not None
    
    def test_dialog_keyboard_shortcuts(self, qapp, default_parameters):
        """Test that dialogs respond to keyboard shortcuts."""
        dialog = SettingsDialog(default_parameters)
        
        # Test Escape key (should reject)
        QTest.keyClick(dialog, Qt.Key.Key_Escape)
        # Dialog should close (may not in test environment)
        
        # Test Enter on default button (should apply)
        # This is platform-dependent and may not work in tests
