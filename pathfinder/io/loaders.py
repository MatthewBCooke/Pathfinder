"""
File loaders for different tracking software formats.
Detects format and parses experiment data.
"""

from pathlib import Path
from typing import Union
from enum import Enum
import pandas as pd
import logging
import math

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
        # Try to detect Ethovision by scanning the worksheet rows (handles metadata header rows)
        try:
            engine = 'openpyxl' if suffix == '.xlsx' else None
            preview = pd.read_excel(file_path, header=None, nrows=200, engine=engine)
            header_line_count = None
            header_row_index = None
            for idx, row in preview.iterrows():
                row_strs = [str(val).lower() for val in row.values if pd.notna(val)]
                for c in row_strs:
                    if 'number of header lines' in c:
                        parts = c.split(',')
                        if len(parts) > 1:
                            try:
                                header_line_count = int(parts[1].strip())
                            except Exception:
                                pass
                if any('trial time' in c or 'recording time' in c for c in row_strs):
                    header_row_index = idx
                    break
            if header_line_count is not None:
                return SoftwareType.ETHOVISION
            if header_row_index is not None:
                # Confirm by reading with header located at found index
                df = pd.read_excel(file_path, header=header_row_index, nrows=5, engine=engine)
                if any(h in df.columns for h in ['Trial time', 'Recording time', 'X center', 'Y center']):
                    return SoftwareType.ETHOVISION
        except Exception as e:
            logger.warning(f"Error reading Excel file for Ethovision markers: {e}")
        # Not recognized as Ethovision; treat as generic Excel data
        return SoftwareType.GENERIC_CSV
    elif suffix == '.csv':
        # Try to detect CSV format by scanning lines for Ethovision header markers
        try:
            header_line_count = None
            header_row_index = None
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i in range(0, 200):
                    line = f.readline()
                    if not line:
                        break
                    low = line.lower()
                    if low.startswith('number of header lines'):
                        try:
                            header_line_count = int(line.split(',')[1].strip())
                        except Exception:
                            pass
                    if any(h in low for h in ['trial time', 'recording time', 'x center', 'y center']):
                        header_row_index = i
                        break
            if header_line_count is not None or header_row_index is not None:
                return SoftwareType.ETHOVISION
        except Exception as e:
            logger.warning(f"Error scanning CSV for Ethovision markers: {e}")

        # Fallback to quick CSV sniffing for AnyMaze/Generic
        try:
            df = pd.read_csv(file_path, nrows=10)
            if 'Time' in df.columns and 'X' in df.columns:
                return SoftwareType.ANYMAZE
            return SoftwareType.GENERIC_CSV
        except Exception as e:
            logger.warning(f"Error reading CSV file: {e}")
        return SoftwareType.GENERIC_CSV
    
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
        # If file is Excel but not identified as Ethovision, try Ethovision loader first
        if Path(file_path).suffix.lower() in ['.xlsx', '.xls']:
            logger.info(f"Excel file with unknown format: {file_path}, attempting Ethovision loader")
            try:
                return _load_ethovision(file_path, parameters)
            except Exception as e:
                logger.exception("Failed to load Excel file as Ethovision")
                raise ValueError(f"Attempted to load Excel file as CSV: {file_path}") from e
        return _load_generic_csv(file_path, parameters)
    else:
        raise ValueError(f"Unsupported software type: {software}")


def _load_ethovision(file_path: Path, parameters: Parameters = None) -> Experiment:
    """Load Ethovision Excel or CSV file with metadata header rows"""
    header_line_count = None
    header_row_index = None
    if file_path.suffix.lower() in ['.xlsx', '.xls']:
        # Inspect Excel rows to find header row / header line count
        try:
            engine = 'openpyxl' if file_path.suffix.lower() == '.xlsx' else None
            preview = pd.read_excel(file_path, header=None, nrows=200, engine=engine)
            for idx, row in preview.iterrows():
                row_strs = [str(val).lower() for val in row.values if pd.notna(val)]
                for c in row_strs:
                    if 'number of header lines' in c:
                        parts = c.split(',')
                        if len(parts) > 1:
                            try:
                                header_line_count = int(parts[1].strip())
                            except Exception:
                                pass
                if any('trial time' in c or 'recording time' in c for c in row_strs):
                    header_row_index = idx
                    break
        except Exception as e:
            logger.warning(f"Error inspecting Excel for header rows: {e}")

        # Determine header parameter priority: header_line_count > header_row_index > 0
        header_param = None
        if header_line_count is not None:
            header_param = header_line_count
        elif header_row_index is not None:
            header_param = header_row_index
        else:
            header_param = 0

        engine = 'openpyxl' if file_path.suffix.lower() == '.xlsx' else None
        df = pd.read_excel(file_path, header=header_param, engine=engine)
    else:
        # CSV: scan first 200 lines for Number of header lines or header row
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i in range(0, 200):
                    line = f.readline()
                    if not line:
                        break
                    low = line.lower()
                    if low.startswith('number of header lines'):
                        try:
                            header_line_count = int(line.split(',')[1].strip())
                        except Exception:
                            pass
                    if any(h in low for h in ['trial time', 'recording time', 'x center', 'y center']):
                        header_row_index = i
                        break
        except Exception as e:
            logger.warning(f"Error scanning CSV for header rows: {e}")

        header_param = header_line_count if header_line_count is not None else (header_row_index if header_row_index is not None else 0)
        df = pd.read_csv(file_path, header=header_param)

    # Parse trials
    trials = []
    # More flexible column detection for EthoVision files
    time_col = None
    x_col = None
    y_col = None
    
    # Priority order for time columns
    for col in ['Trial time', 'Recording time', 'Time']:
        if col in df.columns:
            time_col = col
            break
    
    # Priority order for position columns
    for col in ['X center', 'X', 'Centre posn X']:
        if col in df.columns:
            x_col = col
            break
            
    for col in ['Y center', 'Y', 'Centre posn Y']:
        if col in df.columns:
            y_col = col
            break
    
    if not all([time_col, x_col, y_col]):
        raise ValueError(f"Could not find required columns in EthoVision file. Found columns: {list(df.columns)}")

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
    
    # Try to read as CSV, fallback to latin1 encoding if utf-8 fails
    try:
        df = pd.read_csv(file_path)
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decode failed for {file_path}, trying latin1 encoding.")
        df = pd.read_csv(file_path, encoding='latin1')
    
    # Try to auto-detect column names (order matters - specific to general)
    time_col = _find_column(df, ['time', 't', 'timestamp', 'trial time', 'recording time'])
    x_col = _find_column(df, ['x center', 'x centre', 'centre posn x', 'center posn x', 'x position', 'x_pos', 'x'])
    y_col = _find_column(df, ['y center', 'y centre', 'centre posn y', 'center posn y', 'y position', 'y_pos', 'y'])
    
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


def _parse_time_value(time_val) -> float:
    """
    Parse time value from various formats to seconds.
    
    Handles:
    - Numeric seconds (float/int)
    - HH:MM:SS.ss format
    - H:MM:SS.ss format
    
    Args:
        time_val: Time value (string or numeric)
        
    Returns:
        Time in seconds as float
    """
    # Handle numeric values directly
    if isinstance(time_val, (int, float)):
        return float(time_val)
    
    # Handle string time formats
    time_str = str(time_val).strip()
    
    # Try HH:MM:SS.ss or H:MM:SS.ss format
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
    
    # Fall back to direct float conversion
    return float(time_str)


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
    
    prev_time = prev_x = prev_y = None
    for _, row in df.iterrows():
        try:
            # Parse values
            time_val = row[time_col]
            x_val = row[x_col]
            y_val = row[y_col]

            # Check for missing or NaN/Inf
            missing = False
            for v in (time_val, x_val, y_val):
                if v is None:
                    missing = True
                try:
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        missing = True
                except Exception:
                    pass
            if missing:
                # Option 1: skip row entirely
                logger.warning(f"Skipping row with missing/invalid time/x/y in trial {trial_num}")
                continue
                # Option 2: use previous value instead (uncomment to enable)
                # if prev_time is not None and prev_x is not None and prev_y is not None:
                #     time, x, y = prev_time, prev_x, prev_y
                # else:
                #     logger.warning(f"Skipping row with missing/invalid time/x/y in trial {trial_num}")
                #     continue
            else:
                time = _parse_time_value(time_val)
                x = float(x_val)
                y = float(y_val)
                prev_time, prev_x, prev_y = time, x, y

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
    Find column name from list of candidates (case-insensitive, partial match).
    
    Args:
        df: DataFrame to search
        candidates: List of possible column names or keywords
        
    Returns:
        Matching column name or None
    """
    df_cols_lower = {col.lower(): col for col in df.columns}
    
    # First try exact matches
    for candidate in candidates:
        if candidate.lower() in df_cols_lower:
            return df_cols_lower[candidate.lower()]
    
    # Then try partial matches (candidate keyword in column name)
    for candidate in candidates:
        for col_lower, col_original in df_cols_lower.items():
            if candidate.lower() in col_lower:
                return col_original
    
    return None
