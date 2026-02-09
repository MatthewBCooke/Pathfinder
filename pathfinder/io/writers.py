"""
Data export writers for different formats.
"""

from pathlib import Path
from typing import Union
import pandas as pd
import logging
from datetime import datetime

from pathfinder.core.models import Experiment, Trial

logger = logging.getLogger(__name__)


def export_to_csv(experiment: Experiment, output_path: Union[str, Path]) -> None:
    """
    Export experiment results to CSV file.
    
    Args:
        experiment: Experiment object with analyzed trials
        output_path: Path to output CSV file
    """
    output_path = Path(output_path)
    
    logger.info(f"Exporting {len(experiment.trials)} trials to CSV: {output_path}")
    
    # Build data rows
    rows = []
    for trial in experiment.trials:
        # Calculate path length as multiple of pool diameter
        path_multiplier = None
        if trial.path_length is not None and trial.pool_diameter > 0:
            path_multiplier = trial.path_length / trial.pool_diameter

        row = {
            'experiment_id': experiment.experiment_id,
            'experiment_name': experiment.experiment_name,
            'trial_id': trial.trial_id,
            'day': trial.day,
            'trial_number': trial.trial_number,
            'search_strategy': trial.search_strategy.value if trial.search_strategy else 'Not analyzed',
            'escape_latency_s': trial.escape_latency,
            'path_length_x_diameter': path_multiplier,
            'manual_classification': trial.manual_categorization,
            'platform_x': trial.platform_position[0],
            'platform_y': trial.platform_position[1],
            'pool_center_x': trial.pool_center[0],
            'pool_center_y': trial.pool_center[1],
            'pool_diameter': trial.pool_diameter,
            'platform_diameter': trial.platform_diameter,
            'notes': trial.notes or '',
        }
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Export to CSV
    df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully exported {len(rows)} trials to {output_path}")


def export_to_excel(experiment: Experiment, output_path: Union[str, Path]) -> None:
    """
    Export experiment results to Excel file with multiple sheets.
    
    Args:
        experiment: Experiment object with analyzed trials
        output_path: Path to output Excel file
    """
    output_path = Path(output_path)
    
    logger.info(f"Exporting {len(experiment.trials)} trials to Excel: {output_path}")
    
    # Build data rows
    rows = []
    for trial in experiment.trials:
        # Calculate path length as multiple of pool diameter
        path_multiplier = None
        if trial.path_length is not None and trial.pool_diameter > 0:
            path_multiplier = trial.path_length / trial.pool_diameter

        row = {
            'Experiment ID': experiment.experiment_id,
            'Experiment Name': experiment.experiment_name,
            'Trial ID': trial.trial_id,
            'Day': trial.day,
            'Trial Number': trial.trial_number,
            'Search Strategy': trial.search_strategy.value if trial.search_strategy else 'Not analyzed',
            'Escape Latency (s)': trial.escape_latency,
            'Path Length (× diameter)': path_multiplier,
            'Manual Classification': 'Yes' if trial.manual_categorization else 'No',
            'Platform X': trial.platform_position[0],
            'Platform Y': trial.platform_position[1],
            'Pool Center X': trial.pool_center[0],
            'Pool Center Y': trial.pool_center[1],
            'Pool Diameter': trial.pool_diameter,
            'Platform Diameter': trial.platform_diameter,
            'Notes': trial.notes or '',
        }
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Create Excel writer
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Main results sheet
        df.to_excel(writer, sheet_name='Trial Results', index=False)
        
        # Summary by day sheet
        summary_by_day = df.groupby('Day').agg({
            'Trial Number': 'count',
            'Escape Latency (s)': ['mean', 'std'],
            'Path Length (× diameter)': ['mean', 'std'],
        })
        summary_by_day.columns = ['_'.join(col).strip() for col in summary_by_day.columns.values]
        summary_by_day.to_excel(writer, sheet_name='Summary by Day')
        
        # Strategy counts sheet
        strategy_counts = df.groupby(['Day', 'Search Strategy']).size().unstack(fill_value=0)
        strategy_counts.to_excel(writer, sheet_name='Strategy Counts')
        
        # Metadata sheet
        metadata = pd.DataFrame({
            'Property': ['Experiment ID', 'Experiment Name', 'Researcher', 'Created At', 'Tracking Software', 'Parameters', 'Total Trials'],
            'Value': [
                experiment.experiment_id,
                experiment.experiment_name,
                experiment.researcher or 'N/A',
                experiment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                experiment.tracking_software,
                experiment.parameters.name,
                len(experiment.trials)
            ]
        })
        metadata.to_excel(writer, sheet_name='Metadata', index=False)
    
    logger.info(f"Successfully exported to Excel: {output_path}")


def export_trajectory_data(experiment: Experiment, output_path: Union[str, Path]) -> None:
    """
    Export full trajectory data for all trials.
    
    Args:
        experiment: Experiment object with trajectory data
        output_path: Path to output CSV file
    """
    output_path = Path(output_path)
    
    logger.info(f"Exporting trajectory data to CSV: {output_path}")
    
    # Build data rows with all trajectory points
    rows = []
    for trial in experiment.trials:
        for point in trial.trajectory:
            row = {
                'experiment_id': experiment.experiment_id,
                'trial_id': trial.trial_id,
                'day': trial.day,
                'trial_number': trial.trial_number,
                'time_s': point.time,
                'x': point.x,
                'y': point.y,
            }
            rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Export to CSV
    df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully exported {len(rows)} trajectory points to {output_path}")
