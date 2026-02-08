"""
File loaders for different tracking software formats.
Detects format and parses experiment data.
"""

from pathlib import Path
from typing import Union
from enum import Enum
import pandas as pd
import logging

from pathfinder.core.models import Experiment, Trial, Datapoint, Parameters

logger = logging.getLogger(__name__)


class SoftwareType(str, Enum):
    """Supported tracking software types"""
    ETHOVISION = "Ethovision"
    ANYMAZE = "AnyMaze"
    WATERMAZE = "WaterMaze"
    EZTRACK = "EZTrack"
    GENERIC_CSV = "Generic CSV"


def detect_software_format(file_path: Path) -> SoftwareType:
    """
    Detect tracking software format from file.
    
    Args:
        file_path: Path to data file
        
    Returns:
        SoftwareType enum value
    """
    file_path = Path(file_path)
    
    # Check file extension
    suffix = file_path.suffix.lower()
    
    if suffix in ['.xlsx', '.xls']:
        # Try to detect Ethovision format
        try:
            df = pd.read_excel(file_path, nrows=10)
            
            # Ethovision has specific column patterns
            if 'Trial time' in df.columns or 'Recording time' in df.columns:
                return SoftwareType.ETHOVISION
            
        except Exception as e:
            logger.warning(f"Error reading Excel file: {e}")
    
    elif suffix == '.csv':
        # Try to detect CSV format
        try:
            df = pd.read_csv(file_path, nrows=10)
            
            # AnyMaze detection
            if 'Time' in df.columns and 'X' in df.columns:
                return SoftwareType.ANYMAZE
            
            # Generic CSV
            return SoftwareType.GENERIC_CSV
            
        except Exception as e:
            logger.warning(f"Error reading CSV file: {e}")
    
    # Default fallback
    return SoftwareType.GENERIC_CSV


def load_experiment(
    file_path: Union[str, Path],
    software: SoftwareType,
    parameters: Parameters = None
) -> Experiment:
    """
    Load experiment data from file.
    
    Args:
        file_path: Path to data file
        software: Software type (from detect_software_format)
        parameters: Optional analysis parameters
        
    Returns:
        Experiment object with trials loaded
    """
    file_path = Path(file_path)
    
    logger.info(f"Loading {software.value} file: {file_path}")
    
    if software == SoftwareType.ETHOVISION:
        return _load_ethovision(file_path, parameters)
    elif software == SoftwareType.ANYMAZE:
        return _load_anymaze(file_path, parameters)
    elif software == SoftwareType.GENERIC_CSV:
        return _load_generic_csv(file_path, parameters)
    else:
        raise ValueError(f"Unsupported software type: {software}")


def _load_ethovision(file_path: Path, parameters: Parameters = None) -> Experiment:
    """Load Ethovision Excel file"""
    
    # Read Excel file
    df = pd.read_excel(file_path)
    
    # Parse trials
    trials = []
    
    # Simplified parsing - assumes standard Ethovision format
    # Column mapping (adjust based on actual file)
    time_col = 'Trial time' if 'Trial time' in df.columns else 'Recording time'
    x_col = 'X center' if 'X center' in df.columns else 'X'
    y_col = 'Y center' if 'Y center' in df.columns else 'Y'
    
    # Group by trial (assumes 'Trial' column exists)
    if 'Trial' in df.columns:
        for trial_num, trial_df in df.groupby('Trial'):
            trial = _parse_trial_dataframe(
                trial_df, trial_num, 
                time_col, x_col, y_col
            )
            trials.append(trial)
    else:
        # Single trial file
        trial = _parse_trial_dataframe(df, 1, time_col, x_col, y_col)
        trials.append(trial)
    
    # Create experiment
    experiment = Experiment(
        experiment_id=file_path.stem,
        experiment_name=file_path.stem,
        tracking_software=SoftwareType.ETHOVISION.value,
        parameters=parameters or Parameters(name="Default"),
        trials=trials
    )
    
    logger.info(f"Loaded {len(trials)} trials from Ethovision file")
    
    return experiment


def _load_anymaze(file_path: Path, parameters: Parameters = None) -> Experiment:
    """Load AnyMaze CSV file"""
    
    df = pd.read_csv(file_path)
    
    # Parse trials
    trials = []
    
    # AnyMaze column mapping
    time_col = 'Time'
    x_col = 'X'
    y_col = 'Y'
    
    # Group by trial if column exists
    if 'Trial' in df.columns:
        for trial_num, trial_df in df.groupby('Trial'):
            trial = _parse_trial_dataframe(
                trial_df, trial_num,
                time_col, x_col, y_col
            )
            trials.append(trial)
    else:
        trial = _parse_trial_dataframe(df, 1, time_col, x_col, y_col)
        trials.append(trial)
    
    experiment = Experiment(
        experiment_id=file_path.stem,
        experiment_name=file_path.stem,
        tracking_software=SoftwareType.ANYMAZE.value,
        parameters=parameters or Parameters(name="Default"),
        trials=trials
    )
    
    logger.info(f"Loaded {len(trials)} trials from AnyMaze file")
    
    return experiment


def _load_generic_csv(file_path: Path, parameters: Parameters = None) -> Experiment:
    """Load generic CSV file with X, Y, Time columns"""
    
    df = pd.read_csv(file_path)
    
    # Try to auto-detect column names
    time_col = _find_column(df, ['time', 't', 'timestamp', 'trial time'])
    x_col = _find_column(df, ['x', 'x center', 'x position', 'x_pos'])
    y_col = _find_column(df, ['y', 'y center', 'y position', 'y_pos'])
    
    if not all([time_col, x_col, y_col]):
        raise ValueError(
            f"Could not find required columns. Found: {df.columns.tolist()}\n"
            "Need columns for: time, x, y"
        )
    
    trials = []
    
    # Check for trial grouping
    trial_col = _find_column(df, ['trial', 'trial number', 'trial_num'])
    
    if trial_col:
        for trial_num, trial_df in df.groupby(trial_col):
            trial = _parse_trial_dataframe(
                trial_df, trial_num,
                time_col, x_col, y_col
            )
            trials.append(trial)
    else:
        trial = _parse_trial_dataframe(df, 1, time_col, x_col, y_col)
        trials.append(trial)
    
    experiment = Experiment(
        experiment_id=file_path.stem,
        experiment_name=file_path.stem,
        tracking_software=SoftwareType.GENERIC_CSV.value,
        parameters=parameters or Parameters(name="Default"),
        trials=trials
    )
    
    logger.info(f"Loaded {len(trials)} trials from generic CSV")
    
    return experiment


def _parse_trial_dataframe(
    df: pd.DataFrame,
    trial_num: int,
    time_col: str,
    x_col: str,
    y_col: str
) -> Trial:
    """
    Parse a trial from a dataframe.
    
    Args:
        df: DataFrame with trial data
        trial_num: Trial number
        time_col: Name of time column
        x_col: Name of X column
        y_col: Name of Y column
        
    Returns:
        Trial object
    """
    # Extract trajectory
    trajectory = []
    
    for _, row in df.iterrows():
        try:
            time = float(row[time_col])
            x = float(row[x_col])
            y = float(row[y_col])
            
            point = Datapoint(x=x, y=y, time=time)
            trajectory.append(point)
            
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid data point: {e}")
            continue
    
    if not trajectory:
        raise ValueError(f"No valid data points in trial {trial_num}")
    
    # Calculate basic metrics
    total_time = trajectory[-1].time - trajectory[0].time if len(trajectory) > 1 else 0
    
    # Calculate path length
    path_length = 0.0
    for i in range(1, len(trajectory)):
        dx = trajectory[i].x - trajectory[i-1].x
        dy = trajectory[i].y - trajectory[i-1].y
        path_length += (dx**2 + dy**2) ** 0.5
    
    # Calculate swim speed
    swim_speed = path_length / total_time if total_time > 0 else 0.0
    
    # Estimate pool geometry (simplified - should be provided externally)
    xs = [p.x for p in trajectory]
    ys = [p.y for p in trajectory]
    
    pool_center_x = (max(xs) + min(xs)) / 2
    pool_center_y = (max(ys) + min(ys)) / 2
    pool_diameter = max(max(xs) - min(xs), max(ys) - min(ys))
    
    # Platform location (placeholder - should be provided)
    platform_x = pool_center_x
    platform_y = pool_center_y
    platform_diameter = pool_diameter * 0.1  # Typical 10% of pool
    
    # Create trial
    trial = Trial(
        trial_id=f"trial_{trial_num}",
        trial_number=trial_num,
        day=1,  # Default - should be extracted from data
        trajectory=trajectory,
        platform_position=(platform_x, platform_y),
        platform_diameter=platform_diameter,
        pool_center=(pool_center_x, pool_center_y),
        pool_diameter=pool_diameter,
        escape_latency=total_time,
        path_length=path_length,
        swim_speed=swim_speed
    )
    
    return trial


def _find_column(df: pd.DataFrame, candidates: list) -> str:
    """
    Find column name from list of candidates (case-insensitive).
    
    Args:
        df: DataFrame to search
        candidates: List of possible column names
        
    Returns:
        Matching column name or None
    """
    df_cols_lower = {col.lower(): col for col in df.columns}
    
    for candidate in candidates:
        if candidate.lower() in df_cols_lower:
            return df_cols_lower[candidate.lower()]
    
    return None
