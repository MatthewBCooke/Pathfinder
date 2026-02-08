"""
Simplified CSV loader with auto-format detection for Pathfinder.

Tries multiple formats in order:
1. AnyMaze (Time:Min:Sec, X, Y)
2. WaterMaze (interleaved X/Y/Time columns)
3. Basic fallback (any CSV with time/x/y columns)

Provides clear error messages when loading fails.
"""

from __future__ import annotations
import csv
import os
import logging
from typing import Optional, Tuple, List
from collections import defaultdict
from datetime import datetime

# Make pandas optional (only needed for Excel and some fallback parsing)
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

from pathfinder.models import Trial, Experiment, Datapoint


def auto_detect_and_load(file_path: str) -> Tuple[Optional[Experiment], Optional[str]]:
    """
    Auto-detect CSV format and load experiment.
    
    Tries formats in order:
    1. AnyMaze
    2. WaterMaze  
    3. Ethovision (if Excel)
    4. Basic fallback (time, x, y columns)
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (Experiment object or None, error message or None)
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Try Excel (Ethovision) first if it's an xlsx file
    if file_ext in ['.xlsx', '.xls']:
        if not HAS_PANDAS:
            return None, (
                f"Excel files require pandas library.\n"
                f"Install with: pip install pandas openpyxl\n\n"
                f"For CSV files, pandas is not required."
            )
        try:
            exp = _try_ethovision(file_path)
            if exp and len(exp.trials) > 0:
                logging.info("Successfully loaded as Ethovision format")
                return exp, None
        except Exception as e:
            logging.debug(f"Ethovision load failed: {e}")
    
    # For CSV files, try different formats
    if file_ext == '.csv':
        # Try AnyMaze first (most common)
        try:
            exp = _try_anymaze(file_path)
            if exp and len(exp.trials) > 0:
                logging.info("Successfully loaded as AnyMaze format")
                return exp, None
        except Exception as e:
            logging.debug(f"AnyMaze load failed: {e}")
        
        # Try WaterMaze format
        try:
            exp = _try_watermaze(file_path)
            if exp and len(exp.trials) > 0:
                logging.info("Successfully loaded as WaterMaze format")
                return exp, None
        except Exception as e:
            logging.debug(f"WaterMaze load failed: {e}")
        
        # Try basic fallback (any time/x/y columns)
        try:
            exp = _try_basic_csv(file_path)
            if exp and len(exp.trials) > 0:
                logging.info("Successfully loaded as basic CSV format")
                return exp, None
        except Exception as e:
            logging.debug(f"Basic CSV load failed: {e}")
    
    # All formats failed
    return None, (
        f"Could not parse file: {os.path.basename(file_path)}\n\n"
        f"Tried formats: AnyMaze, WaterMaze, Ethovision, Basic CSV\n\n"
        f"Expected columns:\n"
        f"- AnyMaze: Time (HH:MM:SS), X, Y\n"
        f"- WaterMaze: Interleaved X/Y/Time columns\n"
        f"- Basic: Any columns with time/x/y values\n"
        f"- Ethovision: Excel with header metadata"
    )


def _try_anymaze(file_path: str) -> Optional[Experiment]:
    """
    Try loading as AnyMaze format.
    
    Expected format:
    - CSV file
    - Column 0: Time in HH:MM:SS format
    - Column 1: X coordinate
    - Column 2: Y coordinate
    """
    experiment = Experiment(file_path)
    experiment.setHasAnimalNames(False)
    experiment.setHasDateInfo(False)
    experiment.setHasTrialNames(True)
    
    columns = defaultdict(list)
    
    with open(file_path, 'r') as f:
        # Try to detect CSV dialect
        try:
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
        except:
            dialect = 'excel'
        
        reader = csv.reader(f, dialect)
        next(reader, None)  # Skip header
        
        for row in reader:
            for i, v in enumerate(row):
                columns[i].append(v)
    
    trial = Trial()
    trial.setname(os.path.basename(file_path))
    
    # Parse AnyMaze time format (HH:MM:SS)
    for time_str, x_str, y_str in zip(columns[0], columns[1], columns[2]):
        try:
            # Skip empty rows
            if not time_str or not x_str or not y_str:
                continue
                
            # Parse time
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                time = seconds + minutes * 60 + hours * 3600
            else:
                # Maybe it's just seconds
                time = float(time_str)
            
            x = float(x_str)
            y = float(y_str)
            trial.append(Datapoint(time, x, y))
            
        except (ValueError, IndexError, AttributeError):
            continue
    
    if len(trial.datapointList) > 0:
        experiment.setTrialList([trial])
        return experiment
    
    return None


def _try_watermaze(file_path: str) -> Optional[Experiment]:
    """
    Try loading as WaterMaze format.
    
    Expected format:
    - Interleaved columns: X1, Y1, Time1, X2, Y2, Time2, ...
    - First row contains animal/date info
    """
    experiment = Experiment(file_path)
    experiment.setHasAnimalNames(True)
    experiment.setHasDateInfo(True)
    experiment.setHasTrialNames(False)
    
    columns = defaultdict(list)
    
    with open(file_path, 'r') as f:
        try:
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
        except:
            dialect = 'excel'
        
        reader = csv.reader(f, dialect)
        for row in reader:
            for i, v in enumerate(row):
                columns[i].append(v)
    
    if not columns:
        return None
    
    num_columns = max(columns.keys()) + 1
    trials = []
    
    # Each set of 3 columns is one trial
    for i in range(0, num_columns, 3):
        if i + 2 >= num_columns:
            break
            
        col_x = columns.get(i, [])
        col_y = columns.get(i + 1, [])
        col_time = columns.get(i + 2, [])
        
        if not col_x or not col_y or not col_time:
            continue
        
        trial = Trial()
        trial.setanimal(col_x[0] if col_x else None)
        
        # Parse data rows (skip first 2 rows - header/metadata)
        for x_str, y_str, time_str in zip(col_x[2:], col_y[2:], col_time[2:]):
            if not x_str or not y_str or not time_str:
                break
            try:
                x = float(x_str)
                y = float(y_str)
                time = float(time_str)
                trial.append(Datapoint(time, x, y))
            except ValueError:
                continue
        
        if len(trial.datapointList) > 0:
            trials.append(trial)
    
    if trials:
        experiment.setTrialList(trials)
        return experiment
    
    return None


def _try_ethovision(file_path: str) -> Optional[Experiment]:
    """
    Try loading as Ethovision format (Excel with metadata header).
    Requires pandas and openpyxl.
    """
    if not HAS_PANDAS:
        return None
    
    experiment = Experiment(file_path)
    experiment.setHasAnimalNames(True)
    experiment.setHasDateInfo(False)
    experiment.setHasTrialNames(True)
    
    try:
        sheet = pd.read_excel(file_path, header=None)
    except Exception as e:
        logging.error(f"Failed to read Excel file: {e}")
        return None
    
    if sheet.empty:
        return None
    
    # Get header lines count
    try:
        header_lines = int(sheet.iloc[0, 1])
    except:
        return None
    
    trial = Trial()
    
    # Parse metadata from header
    for row in range(1, min(header_lines, len(sheet))):
        try:
            key = str(sheet.iloc[row, 0]).upper()
            value = sheet.iloc[row, 1]
            
            if "TRIAL NAME" in key:
                trial.setname(value)
            elif "ANIMAL" in key:
                trial.setanimal(value)
            elif "TRIAL" in key:
                trial.settrial(value)
        except:
            continue
    
    # Parse data rows
    for row in range(header_lines, len(sheet)):
        try:
            time = float(sheet.iloc[row, 1])
            x = float(sheet.iloc[row, 2])
            y = float(sheet.iloc[row, 3])
            
            if pd.isna(time) or pd.isna(x) or pd.isna(y):
                continue
            
            trial.append(Datapoint(time, x, y))
        except (ValueError, TypeError, IndexError):
            continue
    
    if len(trial.datapointList) > 0:
        experiment.setTrialList([trial])
        return experiment
    
    return None


def _try_basic_csv(file_path: str) -> Optional[Experiment]:
    """
    Fallback: Try loading as basic CSV with time/x/y columns (any names).
    
    Looks for columns containing:
    - time, t, frame, sec
    - x, xpos, x_pos
    - y, ypos, y_pos
    """
    # Try pandas version if available (more robust)
    if HAS_PANDAS:
        return _try_basic_csv_pandas(file_path)
    else:
        return _try_basic_csv_simple(file_path)


def _try_basic_csv_pandas(file_path: str) -> Optional[Experiment]:
    """Pandas-based basic CSV loader (preferred)."""
    try:
        df = pd.read_csv(file_path)
        
        if df.empty:
            return None
        
        # Normalize column names
        df.columns = [str(col).lower().strip() for col in df.columns]
        
        # Find time column
        time_col = None
        for col in df.columns:
            if any(keyword in col for keyword in ['time', 't', 'frame', 'sec']):
                time_col = col
                break
        
        # Find X column
        x_col = None
        for col in df.columns:
            if any(keyword in col for keyword in ['x', 'xpos', 'x_pos']):
                x_col = col
                break
        
        # Find Y column
        y_col = None
        for col in df.columns:
            if any(keyword in col for keyword in ['y', 'ypos', 'y_pos']):
                y_col = col
                break
        
        if not (time_col and x_col and y_col):
            return None
        
        # Create experiment
        experiment = Experiment(file_path)
        experiment.setHasAnimalNames(False)
        experiment.setHasDateInfo(False)
        experiment.setHasTrialNames(True)
        
        trial = Trial()
        trial.setname(os.path.basename(file_path))
        
        # Parse data
        for _, row in df.iterrows():
            try:
                time = float(row[time_col])
                x = float(row[x_col])
                y = float(row[y_col])
                trial.append(Datapoint(time, x, y))
            except (ValueError, TypeError):
                continue
        
        if len(trial.datapointList) > 0:
            experiment.setTrialList([trial])
            return experiment
        
        return None
        
    except Exception as e:
        logging.debug(f"Basic CSV (pandas) parse failed: {e}")
        return None


def _try_basic_csv_simple(file_path: str) -> Optional[Experiment]:
    """Simple CSV loader without pandas (fallback)."""
    try:
        with open(file_path, 'r') as f:
            # Detect dialect
            try:
                sample = f.read(1024)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample)
            except:
                dialect = 'excel'
            
            reader = csv.reader(f, dialect)
            
            # Read header
            header = next(reader, None)
            if not header:
                return None
            
            # Normalize headers
            header = [str(col).lower().strip() for col in header]
            
            # Find column indices
            time_idx = None
            x_idx = None
            y_idx = None
            
            for i, col in enumerate(header):
                if not time_idx and any(kw in col for kw in ['time', 't', 'frame', 'sec']):
                    time_idx = i
                if not x_idx and any(kw in col for kw in ['x', 'xpos', 'x_pos']):
                    x_idx = i
                if not y_idx and any(kw in col for kw in ['y', 'ypos', 'y_pos']):
                    y_idx = i
            
            if time_idx is None or x_idx is None or y_idx is None:
                return None
            
            # Create experiment
            experiment = Experiment(file_path)
            experiment.setHasAnimalNames(False)
            experiment.setHasDateInfo(False)
            experiment.setHasTrialNames(True)
            
            trial = Trial()
            trial.setname(os.path.basename(file_path))
            
            # Read data rows
            for row in reader:
                try:
                    if len(row) <= max(time_idx, x_idx, y_idx):
                        continue
                    
                    time = float(row[time_idx])
                    x = float(row[x_idx])
                    y = float(row[y_idx])
                    trial.append(Datapoint(time, x, y))
                except (ValueError, TypeError, IndexError):
                    continue
            
            if len(trial.datapointList) > 0:
                experiment.setTrialList([trial])
                return experiment
            
            return None
            
    except Exception as e:
        logging.debug(f"Basic CSV (simple) parse failed: {e}")
        return None
