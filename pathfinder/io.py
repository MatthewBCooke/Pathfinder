"""
File I/O and data parsing for Pathfinder.

Handles loading trial data from various formats:
- Ethovision (Excel .xlsx)
- AnyMaze (CSV)
- WaterMaze (CSV)
- EZTrack (CSV)
- Custom CSV/Excel with user-defined column mapping
"""

from __future__ import annotations
import os
import csv
import fnmatch
import datetime
import logging
from typing import Iterator, Optional
from collections import defaultdict

import pandas as pd

from pathfinder.models import Trial, Experiment, Datapoint


def find_files(directory: str, pattern: str) -> Iterator[str]:
    """
    Find files matching a pattern in a directory.

    Args:
        directory: Path to search
        pattern: File pattern (e.g., "*.csv", "*.xlsx")

    Yields:
        Full paths to matching files
    """
    logging.debug(f"Finding files in {directory} matching {pattern}")
    for root, dirs, files in os.walk(directory):
        for basename in sorted(files):
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def load_experiment(
    software: str, filename: str = "", filedirectory: str = ""
) -> Optional[Experiment]:
    """
    Load trial data from files and create an Experiment object.

    Supports multiple file formats:
    - ethovision: Excel files
    - anymaze: CSV files
    - watermaze: CSV files
    - eztrack: CSV files
    - custom: CSV or Excel with user-defined columns

    Args:
        software: Type of software/format ("ethovision", "anymaze", "watermaze", "eztrack", "custom")
        filename: Single file to load (if provided)
        filedirectory: Directory to search for files (if provided)

    Returns:
        Experiment object with loaded trials, or None if loading failed
    """
    trialList = []
    filenameList = []
    experiment = Experiment(filename or filedirectory)
    dialect = ""

    if filename == "":
        if filedirectory == "":
            logging.error("No files selected")
            return None
        else:
            if software == "ethovision":
                extensionType = r"*.xlsx"
            else:
                extensionType = r"*.csv"
            for aFile in find_files(filedirectory, extensionType):
                filenameList.append(aFile)
    else:
        filenameList.append(filename)

    for fname in filenameList:
        file_extension = os.path.splitext(fname)[1]

        if software != "ethovision" and file_extension == ".csv":
            try:
                with open(fname, newline="") as file:
                    dialect = csv.Sniffer().sniff(file.readline())
                    file.seek(0)
            except csv.Error:
                dialect = "excel"

        if software == "ethovision":
            _load_ethovision(fname, experiment, trialList)
        elif software == "anymaze":
            _load_anymaze(fname, experiment, trialList, dialect)
        elif software == "watermaze":
            _load_watermaze(fname, experiment, trialList, dialect)
        elif software == "eztrack":
            _load_eztrack(fname, experiment, trialList, dialect)
        elif software == "custom":
            # For custom, need column mapping - this would come from defineOwnSoftware()
            # For now, return None to indicate custom needs more setup
            logging.info("Custom format requires column mapping")
            return None
        else:
            logging.critical(f"Unknown software type: {software}")
            return None

    if experiment.hasDateInfo:
        trialList.sort(key=lambda t: t.date if t.date else datetime.datetime.min)

    experiment.setTrialList(trialList)
    return experiment


def _load_ethovision(fname: str, experiment: Experiment, trialList: list) -> None:
    """Load Ethovision format (Excel with header metadata)."""
    logging.info("Loading Ethovision format")
    experiment.setHasAnimalNames(True)
    experiment.setHasDateInfo(False)
    experiment.setHasTrialNames(True)

    try:
        sheet = pd.read_excel(fname, header=None)
        logging.debug(f"Opened {fname}")
    except Exception as e:
        logging.error(f"Unable to open excel file {fname}: {e}")
        return

    number_of_rows = len(sheet)
    headerLines = int(sheet.iloc[0, 1])

    aTrial = Trial()

    for row in range(1, headerLines):
        if str(sheet.iloc[row, 0]).upper() == "TRIAL NAME":
            aTrial.setname(sheet.iloc[row, 1])
        elif str(sheet.iloc[row, 0]).upper() == "ANIMAL ID":
            aTrial.setanimal(sheet.iloc[row, 1])
        elif str(sheet.iloc[row, 0]).upper() == "TRIAL":
            aTrial.settrial(sheet.iloc[row, 1])

    for row in range(headerLines, number_of_rows):
        try:
            time = float(sheet.iloc[row, 1])
            x = float(sheet.iloc[row, 2])
            y = float(sheet.iloc[row, 3])

            if pd.isna(time) or pd.isna(x) or pd.isna(y):
                aTrial.markDataAsCorrupted()
                continue

            aTrial.append(Datapoint(time, x, y))
        except (ValueError, TypeError):
            aTrial.markDataAsCorrupted()

    if len(aTrial.datapointList) > 0:
        trialList.append(aTrial)


def _load_anymaze(fname: str, experiment: Experiment, trialList: list, dialect) -> None:
    """Load AnyMaze format (CSV)."""
    logging.info("Loading AnyMaze format")
    experiment.setHasAnimalNames(False)
    experiment.setHasDateInfo(False)
    experiment.setHasTrialNames(True)

    columns = defaultdict(list)

    try:
        f = open(fname)
        logging.debug(f"Opened {fname}")
    except Exception as e:
        logging.error(f"Could not open {fname}: {e}")
        return

    reader = csv.reader(f, dialect)
    next(reader)
    for row in reader:
        for i, v in enumerate(row):
            columns[i].append(v)

    aTrial = Trial()
    aTrial.setname(os.path.basename(fname))

    for time_str, x_str, y_str in zip(columns[0][1:], columns[1][1:], columns[2][1:]):
        try:
            hours = float(time_str.split(":")[0])
            minutes = float(time_str.split(":")[1])
            seconds = float(time_str.split(":")[2])
            time = seconds + minutes * 60 + hours * 3600
            x = float(x_str)
            y = float(y_str)
            aTrial.append(Datapoint(time, x, y))
        except (ValueError, IndexError):
            aTrial.markDataAsCorrupted()

    if len(aTrial.datapointList) > 0:
        trialList.append(aTrial)


def _load_watermaze(fname: str, experiment: Experiment, trialList: list, dialect) -> None:
    """Load WaterMaze format (CSV with interleaved x/y/time columns)."""
    logging.info("Loading WaterMaze format")
    experiment.setHasAnimalNames(True)
    experiment.setHasDateInfo(True)
    experiment.setHasTrialNames(False)

    columns = defaultdict(list)

    try:
        f = open(fname)
    except Exception as e:
        logging.error(f"Could not open {fname}: {e}")
        return

    reader = csv.reader(f, dialect)
    for row in reader:
        for i, v in enumerate(row):
            columns[i].append(v)

    number_of_columns = 0
    if columns:
        number_of_columns = max(columns.keys())

    for i in range(0, int((number_of_columns + 1) / 3)):
        col1 = columns[i * 3]
        col2 = columns[1 + i * 3]
        col3 = columns[2 + i * 3]

        aTrial = Trial()
        aTrial.setanimal(col1[0] if col1 else None)
        try:
            if col2 and col3:
                date_str = col2[0] + " " + col3[0]
                aTrial.setdate(
                    datetime.datetime.strptime(date_str, "%m/%d/%Y %H:%M %p")
                )
        except Exception:
            aTrial.setdate(None)

        for xVal, yVal, timeVal in zip(col1[2:], col2[2:], col3[2:]):
            if timeVal == "" and xVal == "" and yVal == "":
                break
            try:
                aTrial.append(Datapoint(float(timeVal), float(xVal), float(yVal)))
            except ValueError:
                aTrial.markDataAsCorrupted()

        if len(aTrial.datapointList) > 0:
            trialList.append(aTrial)


def _load_eztrack(fname: str, experiment: Experiment, trialList: list, dialect) -> None:
    """Load EZTrack format (CSV with FPS and Frame columns)."""
    logging.info("Loading EZTrack format")
    experiment.setHasAnimalNames(False)
    experiment.setHasDateInfo(False)
    experiment.setHasTrialNames(True)

    try:
        f = open(fname)
    except Exception as e:
        logging.error(f"Could not open {fname}: {e}")
        return

    reader = csv.reader(f, dialect)
    listReader = list(reader)

    aTrial = Trial()
    aTrial.setname(os.path.basename(fname))

    columns = defaultdict(list)

    fpsCol = xCol = yCol = frameCol = None
    for aIndex, aColumn in enumerate(listReader[0]):
        if aColumn == "FPS":
            fpsCol = aIndex
        elif aColumn == "Frame":
            frameCol = aIndex
        elif aColumn == "X":
            xCol = aIndex
        elif aColumn == "Y":
            yCol = aIndex

    if fpsCol is None or frameCol is None or xCol is None or yCol is None:
        logging.error("Missing required columns in EZTrack file")
        return

    for row in listReader[1:]:
        for i, v in enumerate(row):
            columns[i].append(v)

    for fps_str, frame_str, x_str, y_str in zip(
        columns[fpsCol], columns[frameCol], columns[xCol], columns[yCol]
    ):
        try:
            time = float(frame_str) / float(fps_str)
            x = float(x_str)
            y = float(y_str)
            aTrial.append(Datapoint(time, x, y))
        except (ValueError, ZeroDivisionError):
            aTrial.markDataAsCorrupted()

    if len(aTrial.datapointList) > 0:
        trialList.append(aTrial)
