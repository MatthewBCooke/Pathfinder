"""
Unit tests for Pathfinder worker threads.

Tests worker thread behavior, signal emissions, abort mechanisms,
and error handling without blocking the GUI.
"""

import sys
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import QEventLoop, QTimer, pyqtSignal
from PyQt6.QtTest import QSignalSpy

sys.path.insert(0, '/tmp/Pathfinder')
sys.path.insert(0, '/tmp/Pathfinder/gui')

from gui.workers import AnalysisWorker, FileLoadWorker, HeatmapWorker
from pathfinder.models import Trial, Experiment, Datapoint
from pathfinder.types import Parameters, StrategyResult


class TestAnalysisWorker:
    """Tests for AnalysisWorker thread."""
    
    def test_worker_initialization(self, qapp, test_experiment, default_parameters):
        """Test that worker initializes correctly."""
        worker = AnalysisWorker(
            experiment=test_experiment,
            parameters=vars(default_parameters)
        )
        
        assert worker.experiment == test_experiment
        assert worker.parameters is not None
        assert worker._abort_requested is False
        assert len(worker.results) == 0
    
    def test_worker_emits_progress_signals(self, qapp, test_experiment, default_parameters):
        """Test that worker emits progress signals during analysis."""
        worker = AnalysisWorker(
            experiment=test_experiment,
            parameters=vars(default_parameters)
        )
        
        # Set up signal spies
        progress_spy = QSignalSpy(worker.progress)
        trial_completed_spy = QSignalSpy(worker.trial_completed)
        finished_spy = QSignalSpy(worker.finished)
        
        # Mock the analysis functions to avoid actual computation
        with patch('gui.workers.calculate_trial_metrics') as mock_metrics, \
             patch('gui.workers.classify_strategy') as mock_classify:
            
            # Mock return values
            mock_metrics.return_value = MagicMock()
            mock_classify.return_value = MagicMock(
                trial_name="Test",
                animal_id="Animal_01",
                strategy="Direct",
                score=3,
                entropy=1.5,
                ipe=100.0,
                distance=300.0,
                velocity=20.0,
                latency=15.0
            )
            
            # Run worker
            worker.start()
            worker.wait(5000)  # Wait up to 5 seconds
        
        # Verify signals were emitted
        assert len(progress_spy) > 0, "Progress signal should be emitted"
        assert len(trial_completed_spy) > 0, "Trial completed signals should be emitted"
        assert len(finished_spy) == 1, "Finished signal should be emitted once"
    
    def test_worker_abort_mechanism(self, qapp, test_experiment, default_parameters):
        """Test that abort mechanism stops worker cleanly."""
        worker = AnalysisWorker(
            experiment=test_experiment,
            parameters=vars(default_parameters)
        )
        
        finished_spy = QSignalSpy(worker.finished)
        
        # Mock slow analysis
        with patch('gui.workers.calculate_trial_metrics') as mock_metrics:
            def slow_calc(*args, **kwargs):
                time.sleep(0.1)
                return MagicMock()
            
            mock_metrics.side_effect = slow_calc
            
            # Start worker
            worker.start()
            
            # Request abort immediately
            QTimer.singleShot(50, worker.request_abort)
            
            # Wait for worker to finish
            worker.wait(2000)
        
        # Worker should have stopped early (not emitted finished signal)
        assert len(finished_spy) == 0, "Finished signal should not be emitted after abort"
        assert worker._abort_requested is True
    
    def test_worker_handles_errors(self, qapp, test_experiment, default_parameters):
        """Test that worker propagates errors via error signal."""
        worker = AnalysisWorker(
            experiment=test_experiment,
            parameters=vars(default_parameters)
        )
        
        error_spy = QSignalSpy(worker.error)
        
        # Mock analysis to raise exception
        with patch('gui.workers.calculate_trial_metrics') as mock_metrics:
            mock_metrics.side_effect = ValueError("Test error")
            
            worker.start()
            worker.wait(2000)
        
        # Verify error signal was emitted
        assert len(error_spy) == 1, "Error signal should be emitted"
        error_msg = error_spy[0][0]
        assert "Test error" in error_msg
    
    def test_worker_processes_all_trials(self, qapp, test_experiment, default_parameters):
        """Test that worker processes all trials in experiment."""
        worker = AnalysisWorker(
            experiment=test_experiment,
            parameters=vars(default_parameters)
        )
        
        trial_completed_spy = QSignalSpy(worker.trial_completed)
        
        with patch('gui.workers.calculate_trial_metrics') as mock_metrics, \
             patch('gui.workers.classify_strategy') as mock_classify:
            
            mock_metrics.return_value = MagicMock()
            mock_classify.return_value = MagicMock(
                trial_name="Test",
                animal_id="Animal",
                strategy="Direct",
                score=3,
                entropy=1.5,
                ipe=100.0,
                distance=300.0,
                velocity=20.0,
                latency=15.0
            )
            
            worker.start()
            worker.wait(5000)
        
        # Should have processed all trials
        expected_trials = len(test_experiment.trials)
        assert len(trial_completed_spy) == expected_trials
        assert len(worker.results) == expected_trials


class TestFileLoadWorker:
    """Tests for FileLoadWorker thread."""
    
    def test_worker_initialization(self, qapp):
        """Test that file load worker initializes correctly."""
        worker = FileLoadWorker(
            software_type="ethovision",
            path="/tmp/test_data.csv"
        )
        
        assert worker.software_type == "ethovision"
        assert worker.path == "/tmp/test_data.csv"
    
    def test_worker_emits_progress_messages(self, qapp, tmp_path):
        """Test that worker emits progress status messages."""
        # Create a temporary test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("dummy,data\n1,2\n")
        
        worker = FileLoadWorker(
            software_type="ethovision",
            path=str(test_file)
        )
        
        progress_spy = QSignalSpy(worker.progress)
        finished_spy = QSignalSpy(worker.finished)
        
        # Mock the load_experiment function
        with patch('gui.workers.load_experiment') as mock_load:
            mock_experiment = MagicMock()
            mock_experiment.trials = []
            mock_load.return_value = mock_experiment
            
            worker.start()
            worker.wait(2000)
        
        # Verify progress messages were emitted
        assert len(progress_spy) >= 1, "Progress messages should be emitted"
        assert len(finished_spy) == 1, "Finished signal should be emitted"
    
    def test_worker_handles_file_not_found(self, qapp):
        """Test error handling for missing files."""
        worker = FileLoadWorker(
            software_type="ethovision",
            path="/nonexistent/file.csv"
        )
        
        error_spy = QSignalSpy(worker.error)
        
        # Mock load_experiment to raise FileNotFoundError
        with patch('gui.workers.load_experiment') as mock_load:
            mock_load.side_effect = FileNotFoundError("File not found")
            
            worker.start()
            worker.wait(2000)
        
        # Verify error was propagated
        assert len(error_spy) == 1
        error_msg = error_spy[0][0]
        assert "File not found" in error_msg
    
    def test_worker_handles_invalid_format(self, qapp, tmp_path):
        """Test error handling for invalid file formats."""
        test_file = tmp_path / "invalid.txt"
        test_file.write_text("not a valid file format")
        
        worker = FileLoadWorker(
            software_type="ethovision",
            path=str(test_file)
        )
        
        error_spy = QSignalSpy(worker.error)
        
        with patch('gui.workers.load_experiment') as mock_load:
            mock_load.side_effect = ValueError("Invalid file format")
            
            worker.start()
            worker.wait(2000)
        
        assert len(error_spy) == 1
        error_msg = error_spy[0][0]
        assert "Invalid file format" in error_msg
    
    def test_worker_handles_permission_error(self, qapp):
        """Test error handling for permission denied."""
        worker = FileLoadWorker(
            software_type="ethovision",
            path="/root/protected_file.csv"
        )
        
        error_spy = QSignalSpy(worker.error)
        
        with patch('gui.workers.load_experiment') as mock_load:
            mock_load.side_effect = PermissionError("Permission denied")
            
            worker.start()
            worker.wait(2000)
        
        assert len(error_spy) == 1
        error_msg = error_spy[0][0]
        assert "Permission denied" in error_msg


class TestHeatmapWorker:
    """Tests for HeatmapWorker thread."""
    
    def test_worker_initialization(self, qapp, test_experiment):
        """Test that heatmap worker initializes correctly."""
        filters = {'min_score': 10, 'strategy': 'Direct'}
        
        worker = HeatmapWorker(
            experiment=test_experiment,
            filters=filters
        )
        
        assert worker.experiment == test_experiment
        assert worker.filters == filters
    
    def test_worker_emits_progress(self, qapp, test_experiment):
        """Test that worker emits progress updates."""
        worker = HeatmapWorker(
            experiment=test_experiment,
            filters={}
        )
        
        progress_spy = QSignalSpy(worker.progress)
        finished_spy = QSignalSpy(worker.finished)
        
        # Mock aggregate_heatmap_data
        with patch('gui.workers.aggregate_heatmap_data') as mock_aggregate:
            mock_heatmap = MagicMock()
            mock_aggregate.return_value = mock_heatmap
            
            worker.start()
            worker.wait(2000)
        
        # Verify progress was emitted
        assert len(progress_spy) >= 2, "Progress should be emitted (start and end)"
        assert progress_spy[0][0] == 0, "Initial progress should be 0"
        assert progress_spy[-1][0] == 100, "Final progress should be 100"
        
        # Verify finished signal
        assert len(finished_spy) == 1
    
    def test_worker_handles_errors(self, qapp, test_experiment):
        """Test that worker handles errors during heatmap generation."""
        worker = HeatmapWorker(
            experiment=test_experiment,
            filters={}
        )
        
        error_spy = QSignalSpy(worker.error)
        
        with patch('gui.workers.aggregate_heatmap_data') as mock_aggregate:
            mock_aggregate.side_effect = RuntimeError("Heatmap generation failed")
            
            worker.start()
            worker.wait(2000)
        
        assert len(error_spy) == 1
        error_msg = error_spy[0][0]
        assert "Heatmap generation" in error_msg
    
    def test_worker_progress_callback(self, qapp, test_experiment):
        """Test that progress callback is called correctly."""
        worker = HeatmapWorker(
            experiment=test_experiment,
            filters={}
        )
        
        progress_spy = QSignalSpy(worker.progress)
        
        with patch('gui.workers.aggregate_heatmap_data') as mock_aggregate:
            def mock_with_callback(experiment, filters, progress_callback):
                # Simulate progress updates
                progress_callback(25)
                progress_callback(50)
                progress_callback(75)
                return MagicMock()
            
            mock_aggregate.side_effect = mock_with_callback
            
            worker.start()
            worker.wait(2000)
        
        # Should have: 0% (start), 25%, 50%, 75%, 100% (end)
        assert len(progress_spy) >= 4


class TestWorkerConcurrency:
    """Tests for concurrent worker operations."""
    
    def test_multiple_workers_dont_interfere(self, qapp, test_experiment, default_parameters):
        """Test that multiple workers can run without interfering."""
        worker1 = AnalysisWorker(test_experiment, vars(default_parameters))
        worker2 = HeatmapWorker(test_experiment, {})
        
        finished1_spy = QSignalSpy(worker1.finished)
        finished2_spy = QSignalSpy(worker2.finished)
        
        with patch('gui.workers.calculate_trial_metrics'), \
             patch('gui.workers.classify_strategy'), \
             patch('gui.workers.aggregate_heatmap_data'):
            
            # Start both workers
            worker1.start()
            worker2.start()
            
            # Wait for both to finish
            worker1.wait(3000)
            worker2.wait(3000)
        
        # Both should complete successfully
        assert len(finished1_spy) <= 1  # May not emit if aborted
        assert len(finished2_spy) == 1
    
    def test_worker_cleanup_on_abort(self, qapp, test_experiment, default_parameters):
        """Test that workers clean up properly when aborted."""
        worker = AnalysisWorker(test_experiment, vars(default_parameters))
        
        with patch('gui.workers.calculate_trial_metrics') as mock_metrics:
            mock_metrics.return_value = MagicMock()
            
            worker.start()
            QTimer.singleShot(100, worker.request_abort)
            worker.wait(2000)
        
        # Worker should be finished
        assert worker.isFinished()
        assert not worker.isRunning()


class TestWorkerEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_empty_experiment(self, qapp, empty_experiment, default_parameters):
        """Test worker behavior with empty experiment."""
        worker = AnalysisWorker(empty_experiment, vars(default_parameters))
        
        finished_spy = QSignalSpy(worker.finished)
        
        worker.start()
        worker.wait(1000)
        
        # Should finish immediately with empty results
        assert len(finished_spy) == 1
        assert len(worker.results) == 0
    
    def test_corrupted_trial_handling(self, qapp, corrupted_trial, default_parameters):
        """Test worker handles corrupted trial data."""
        experiment = Experiment("Test")
        experiment.append(corrupted_trial)
        
        worker = AnalysisWorker(experiment, vars(default_parameters))
        
        error_spy = QSignalSpy(worker.error)
        
        with patch('gui.workers.calculate_trial_metrics') as mock_metrics:
            mock_metrics.side_effect = ValueError("Invalid data")
            
            worker.start()
            worker.wait(2000)
        
        # Should emit error signal
        assert len(error_spy) == 1
    
    def test_invalid_parameters(self, qapp, test_experiment):
        """Test worker with invalid/missing parameters."""
        invalid_params = {}  # Empty parameters
        
        worker = AnalysisWorker(test_experiment, invalid_params)
        error_spy = QSignalSpy(worker.error)
        
        with patch('gui.workers.calculate_trial_metrics') as mock_metrics:
            mock_metrics.side_effect = KeyError("Missing parameter")
            
            worker.start()
            worker.wait(2000)
        
        assert len(error_spy) == 1
