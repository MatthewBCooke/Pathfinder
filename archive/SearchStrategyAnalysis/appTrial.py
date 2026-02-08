# Module: appTrial.py
# Holds data structures


import sys
from sys import platform as _platform
import csv
import math
import logging
import os
import fnmatch
import datetime
import tkinter
from operator import add
from collections import defaultdict
import pkg_resources
import pandas as pd

if sys.version_info<(3,0,0):  # tkinter names for python 2
    print("Update to Python3 for best results... You may encounter errors")
    from Tkinter import *
    import tkMessageBox as messagebox
    import ttk
    import tkFileDialog as filedialog
else:  # tkinter for python 3
    from tkinter import *
    from tkinter import messagebox
    from tkinter import ttk
    from tkinter import filedialog
import traceback
import pandas as pd

class Datapoint(object):
    def __init__(self, time: float, x: float, y: float):
        self.time = time
        self.x = x
        self.y = y

    def __str__(self):
        return("Datapoint object:\n"
               "  Time = {1}\n"
               "  x = {2}\n"
               "  y = {3}"
               .format(self.time, self.x, self.y))
    def getx(self):
        return self.x
    def gety(self):
        return self.y
    def gettime(self):
        return self.time


class Trial(object):  # an object for our row values
    def __init__(self):
        self.datapointList = []
        self.name = None
        self.animal = None
        self.date = None
        self.day = None
        self.trial = None
        self.corruptedData = False

    def setname(self, name):
        self.name = name

    def setanimal(self, animal):
        self.animal = animal

    def setdate(self, date):
        self.date = date

    def settrial(self, trial):
        self.trial = trial

    def setday(self, day):
        self.day = day

    def markDataAsCorrupted(self):
        self.corruptedData = True

    def __str__(self):
        return self.animal if self.animal != None else self.name

    def append(self, adatapoint):
        self.datapointList.append(adatapoint)

    def __iter__(self):
        return iter(self.datapointList)


class Experiment(object):
    def __init__(self, name: str):
        self.name = name
        self.trialList = []
        self.hasAnimalNames = False
        self.hasDateInfo = False
        self.hasTrialNames = False

    def setTrialList(self, trialList):
        self.trialList = trialList

    def setHasAnimalNames(self, hasAnimalNames):
        self.hasAnimalNames = hasAnimalNames

    def setHasDateInfo(self, hasDateInfo):
        self.hasDateInfo = hasDateInfo

    def setHasTrialNames(self, hasTrialNames):
        self.hasTrialNames = hasTrialNames

    def append(self, atrial):
        self.trialList.append(atrial)

    def __str__(self):
        return self.name

    def __len__(self):
        return len(self.trialList)

    def __iter__(self):
        return iter(self.trialList)


class Parameters:
    def __init__(self, name, ipeMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, distanceToSwimMaxVal2, distanceToPlatMaxVal2, corridorAverageMinVal, directedSearchMaxDistance, focalMinDistance, focalMaxDistance, semiFocalMinDistance, semiFocalMaxDistance, corridoripeMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, chainingMaxCoverage, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, thigmoMinDistance, fullThigmoMinVal, smallThigmoMinVal, ipeIndirectMaxVal, percentTraversedRandomMaxVal, headingIndirectMaxVal, useDirect, useFocal, useDirected, useIndirect, useSemiFocal, useChaining, useScanning, useRandom, useThigmogaxis):

        self.name = name
        self.ipeMaxVal = ipeMaxVal
        self.headingMaxVal = headingMaxVal
        self.distanceToSwimMaxVal = distanceToSwimMaxVal
        self.distanceToPlatMaxVal = distanceToPlatMaxVal
        self.distanceToSwimMaxVal2 = distanceToSwimMaxVal2
        self.distanceToPlatMaxVal2 = distanceToPlatMaxVal2
        self.corridorAverageMinVal = corridorAverageMinVal
        self.directedSearchMaxDistance = directedSearchMaxDistance
        self.focalMinDistance = focalMinDistance
        self.focalMaxDistance = focalMaxDistance
        self.semiFocalMinDistance = semiFocalMinDistance
        self.semiFocalMaxDistance = semiFocalMaxDistance
        self.corridoripeMaxVal = corridoripeMaxVal
        self.annulusCounterMaxVal = annulusCounterMaxVal
        self.quadrantTotalMaxVal = quadrantTotalMaxVal
        self.chainingMaxCoverage = chainingMaxCoverage
        self.percentTraversedMaxVal = percentTraversedMaxVal
        self.percentTraversedMinVal = percentTraversedMinVal
        self.distanceToCentreMaxVal = distanceToCentreMaxVal
        self.thigmoMinDistance = thigmoMinDistance
        self.fullThigmoMinVal = fullThigmoMinVal
        self.smallThigmoMinVal = smallThigmoMinVal
        self.ipeIndirectMaxVal = ipeIndirectMaxVal
        self.percentTraversedRandomMaxVal = percentTraversedRandomMaxVal
        self.headingIndirectMaxVal = headingIndirectMaxVal
        self.useDirect = useDirect
        self.useFocal = useFocal
        self.useDirected = useDirected
        self.useIndirect = useIndirect
        self.useSemiFocal = useSemiFocal
        self.useChaining = useChaining
        self.useScanning = useScanning
        self.useRandom = useRandom
        self.useThigmotaxis = useThigmogaxis

    def __str__(self):
        return self.name

def find_files(directory, pattern):  # searches for our files in the directory
        logging.debug("Finding files in the directory")
        for root, dirs, files in os.walk(directory):
            for basename in sorted(files):
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename

def openFile():  # opens a dialog to get a single file
    logging.debug("Open File...")
    theFile = filedialog.askopenfilename()
    return theFile

def defineOwnSoftware(root, filename):
    """Modernized dialog for defining custom file column mappings using ttk.Treeview.
    
    Args:
        root: Parent window
        filename: Path to the CSV or XLSX file to analyze
        
    Returns:
        dict: Column mapping with keys 'x_col', 'y_col', 't_col', 'data_start_row'
    """
    file_extension = os.path.splitext(filename)[1]
    
    # Initialize return value
    column_mapping = {'x_col': None, 'y_col': None, 't_col': None, 'data_start_row': 0}
    
    # Create dialog window
    top = Toplevel(root)
    top.title("Define Column Mapping")
    top.geometry("900x600")
    top.attributes('-topmost', True)
    
    # Main container with 10px margins
    main_frame = ttk.Frame(top, padding=10)
    main_frame.pack(fill=BOTH, expand=True)
    
    # Header label
    header_label = ttk.Label(
        main_frame,
        text="Select which column to use for each data type:",
        font=("TkDefaultFont", 10, "bold")
    )
    header_label.pack(pady=(0, 10), fill=X)
    
    # Instructions label
    instructions = ttk.Label(
        main_frame,
        text="Use the dropdown menus to assign each column to X axis, Y axis, Time, or Skip",
        font=("TkDefaultFont", 9),
        foreground="gray40"
    )
    instructions.pack(pady=(0, 10), fill=X)
    
    # Status message frame
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(pady=(0, 10), fill=X)
    
    status_var = StringVar()
    status_var.set("Status: Waiting for column selection...")
    status_label = ttk.Label(status_frame, textvariable=status_var, foreground="blue")
    status_label.pack(side=LEFT)
    
    error_var = StringVar()
    error_label = ttk.Label(status_frame, textvariable=error_var, foreground="red")
    error_label.pack(side=LEFT, padx=(20, 0))
    
    # Treeview frame with scrollbar
    treeview_frame = ttk.Frame(main_frame)
    treeview_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
    
    # Create treeview with 3 columns
    columns = ("Column Name", "Data Type", "Use as X/Y/Time")
    tree = ttk.Treeview(
        treeview_frame,
        columns=columns,
        height=15,
        show='headings'
    )
    
    # Configure column headings and widths
    tree.heading("Column Name", text="Column Name")
    tree.heading("Data Type", text="Data Type")
    tree.heading("Use as X/Y/Time", text="Use as X/Y/Time")
    
    tree.column("Column Name", width=150, anchor=W)
    tree.column("Data Type", width=150, anchor=W)
    tree.column("Use as X/Y/Time", width=200, anchor=W)
    
    # Add vertical scrollbar
    yscrollbar = ttk.Scrollbar(treeview_frame, orient=VERTICAL, command=tree.yview)
    tree.configure(yscroll=yscrollbar.set)
    
    tree.grid(row=0, column=0, sticky=(N, S, E, W))
    yscrollbar.grid(row=0, column=1, sticky=(N, S))
    
    treeview_frame.columnconfigure(0, weight=1)
    treeview_frame.rowconfigure(0, weight=1)
    
    # Dictionary to track combobox values: item_id -> combobox widget
    combobox_map = {}
    
    def populate_treeview(data_rows, column_names):
        """Populate treeview with file preview data (first 5 rows).
        
        Args:
            data_rows: List of row data from file
            column_names: List of column headers
        """
        for idx, col_name in enumerate(column_names[:10]):  # Limit to first 10 columns
            # Detect data type from first row of data
            data_type = "Unknown"
            if data_rows and idx < len(data_rows[0]):
                try:
                    float(data_rows[0][idx])
                    data_type = "Numeric"
                except (ValueError, TypeError):
                    data_type = "Text"
            
            # Insert row
            item_id = tree.insert('', END, values=(col_name, data_type, "Skip"))
            
            # Create combobox for dropdown selection
            combo = ttk.Combobox(
                tree,
                values=["X axis", "Y axis", "Time", "Skip"],
                state="readonly",
                width=15
            )
            combo.set("Skip")
            
            # Bind combobox change event
            def on_combo_change(event, iid=item_id, cb=combo):
                value = cb.get()
                tree.item(iid, values=(tree.item(iid)['values'][0], tree.item(iid)['values'][1], value))
                update_status()
            
            combo.bind("<<ComboboxSelected>>", on_combo_change)
            combobox_map[item_id] = combo
    
    def update_status():
        """Update status message based on current selections."""
        x_selected = False
        y_selected = False
        t_selected = False
        
        for item_id in tree.get_children():
            values = tree.item(item_id)['values']
            selection = values[2] if len(values) > 2 else "Skip"
            
            if selection == "X axis":
                x_selected = True
            elif selection == "Y axis":
                y_selected = True
            elif selection == "Time":
                t_selected = True
        
        if x_selected and y_selected and t_selected:
            status_var.set("Status: All required columns selected ✓")
            error_var.set("")
            return True
        else:
            missing = []
            if not x_selected:
                missing.append("X")
            if not y_selected:
                missing.append("Y")
            if not t_selected:
                missing.append("Time")
            status_var.set(f"Status: Waiting for selection...")
            error_var.set(f"Missing: {', '.join(missing)}")
            return False
    
    def get_column_mapping():
        """Extract column mapping from treeview selections."""
        mapping = {'x_col': None, 'y_col': None, 't_col': None}
        
        for item_id in tree.get_children():
            values = tree.item(item_id)['values']
            col_name = values[0]
            selection = values[2] if len(values) > 2 else "Skip"
            col_index = list(column_names).index(col_name) if col_name in column_names else None
            
            if col_index is not None:
                if selection == "X axis":
                    mapping['x_col'] = col_index
                elif selection == "Y axis":
                    mapping['y_col'] = col_index
                elif selection == "Time":
                    mapping['t_col'] = col_index
        
        return mapping
    
    def ok_button_click():
        """Validate selection and close dialog."""
        if update_status():
            nonlocal column_mapping
            column_mapping = get_column_mapping()
            column_mapping['data_start_row'] = 0
            top.attributes('-topmost', False)
            top.quit()
            top.destroy()
        else:
            error_var.set("Error: Please select X, Y, and Time columns")
    
    def reset_button_click():
        """Reset all selections to 'Skip'."""
        for item_id in tree.get_children():
            tree.item(item_id, values=(tree.item(item_id)['values'][0], tree.item(item_id)['values'][1], "Skip"))
        status_var.set("Status: Selections cleared")
        error_var.set("")
    
    # Load file and populate treeview
    try:
        if file_extension == '.csv':
            with open(filename, newline="") as file:
                try:
                    dialect = csv.Sniffer().sniff(file.readline())
                    file.seek(0)
                    reader = csv.reader(file, dialect)
                    all_rows = list(reader)
                    
                    if len(all_rows) < 2:
                        raise ValueError("CSV file must have at least header row and one data row")
                    
                    headers = all_rows[0]
                    data_rows = all_rows[1:6]  # First 5 data rows for preview
                    column_names = headers
                    
                except csv.Error as e:
                    error_var.set(f"CSV parsing error: {str(e)}")
                    logging.error(f"CSV parsing error: {e}")
                    top.destroy()
                    return column_mapping
        
        elif file_extension == '.xlsx':
            try:
                df = pd.read_excel(filename)
                headers = list(df.columns)
                data_rows = df.iloc[:5].values.tolist()  # First 5 rows
                column_names = headers
            except Exception as e:
                error_var.set(f"Excel parsing error: {str(e)}")
                logging.error(f"Excel parsing error: {e}")
                top.destroy()
                return column_mapping
        else:
            error_var.set(f"Unsupported file type: {file_extension}")
            logging.error(f"Unsupported file type: {file_extension}")
            top.destroy()
            return column_mapping
        
        # Populate treeview
        populate_treeview(data_rows, column_names)
        
    except IOError as e:
        error_var.set(f"File I/O error: {str(e)}")
        logging.error(f"File I/O error: {e}")
        top.destroy()
        return column_mapping
    
    # Button frame
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=10, fill=X)
    
    ok_button = ttk.Button(button_frame, text="Save Mapping", command=ok_button_click)
    ok_button.pack(side=LEFT, padx=(0, 5))
    
    reset_button = ttk.Button(button_frame, text="Reset", command=reset_button_click)
    reset_button.pack(side=LEFT)
    
    cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda: top.destroy())
    cancel_button.pack(side=LEFT, padx=(5, 0))
    
    # Show initial instruction message in status
    status_var.set("Status: Select column roles using dropdowns")
    
    # Center window on parent
    top.transient(root)
    top.grab_set()
    
    # Start event loop
    top.mainloop()
    
    return column_mapping


def saveFileAsExperiment(software, filename, filedirectory):
    trialList = []
    filenameList = []
    experiment = Experiment(filename)
    dialect = ""
    if filename == "":
        if filedirectory == "":
            logging.error("No files selected")
            print("Please select a file or directory first")
            return
        else:
            if software == "ethovision":
                extensionType = r"*.xlsx"
            else:
                extensionType = r"*.csv"
            for aFile in find_files(filedirectory, extensionType):
                filenameList.append(aFile)
    else:
        filenameList.append(filename)

    for filename in filenameList:
        file_extension = os.path.splitext(filename)[1]
        if software != "ethovision" and file_extension == '.csv':
            with open(filename, newline="") as file:
                dialect = csv.Sniffer().sniff(file.readline())
                file.seek(0)
        if software == "ethovision":
            logging.info("Reading file ethovision")
            experiment.setHasAnimalNames(True)
            experiment.setHasDateInfo(False)
            experiment.setHasTrialNames(True)

            try:
                sheet = pd.read_excel(filename, header = None)
                logging.debug("Opened" + filename)
            except Exception:
                traceback.print_exc()
                logging.error("Unable to open excel file " + filename)
                return

            number_of_rows = len(sheet)
            headerLines = int(sheet.iloc[0,1])  # gets number of header lines in the spreadsheet
            aTrial = Trial()

            for row in range(1, headerLines):
                if str(sheet.iloc[row, 0]).upper() == 'TRIAL NAME':
                    aTrial.setname(sheet.iloc[row,1])
                elif str(sheet.iloc[row, 0]).upper() == 'ANIMAL ID':
                    aTrial.setanimal(sheet.iloc[row,1])
                elif str(sheet.iloc[row, 0]).upper() == 'TRIAL':
                    aTrial.settrial(sheet.iloc[row,1])

            for row in range(headerLines, number_of_rows):  # for each row
                time = sheet.iloc[row,1]
                x = sheet.iloc[row,2]
                y = sheet.iloc[row,3]

                if time == "NaN" or x == "NaN" or y == "NaN":
                    aTrial.markDataAsCorrupted()
                    continue

                try:
                    aTrial.append(Datapoint(float(time), float(x), float(y)))
                except ValueError:
                    aTrial.markDataAsCorrupted()
                    pass

            trialList.append(aTrial)

        elif software == "anymaze":
            logging.info("Reading anymaze")
            experiment.setHasAnimalNames(False)
            experiment.setHasDateInfo(False)
            experiment.setHasTrialNames(True)

            columns = defaultdict(list)  # each value in each column is appended to a list
            try:
                f = open(filename)
                logging.debug("Opened " + filename)
            except Exception:
                traceback.print_exc()
                logging.info("Could not open " + filename)
                return
            reader = csv.reader(f, dialect)
            next(reader)
            for row in reader:
                for (i, v) in enumerate(row):
                    columns[i].append(v)

            aTrial = Trial()
            aTrial.setname(filename.split("/")[-1])

            for time, x, y in zip(columns[0][1:], columns[1][1:], columns[2][1:]):
                try:
                    hours = float(time.split(':')[0])
                    minutes = float(time.split(':')[1])
                    seconds = float(time.split(':')[2])
                    time = seconds + minutes*60 + hours*3600
                    x = float(x)
                    y = float(y)
                    aTrial.append(Datapoint(time, x, y))
                except:
                    aTrial.markDataAsCorrupted()

            trialList.append(aTrial)

        elif software == "watermaze":
            logging.info("Reading watermaze")
            experiment.setHasAnimalNames(True)
            experiment.setHasDateInfo(True)
            experiment.setHasTrialNames(False)

            columns = defaultdict(list)  # each value in each column is appended to a list

            number_of_columns = 0
            try:
                f = open(filename)
            except:
                logging.info("Could not open " + filename)
                return

            reader = csv.reader(f, dialect)
            for row in reader:
                for (i, v) in enumerate(row):
                    columns[i].append(v)
                    number_of_columns = i

            for i in range(0, int(round((number_of_columns / 3)))):
                col1 = columns[i * 3]
                col2 = columns[1 + i * 3]
                col3 = columns[2 + i * 3]

                aTrial = Trial()
                aTrial.setanimal(col1[0])
                try:
                    aTrial.setdate(datetime.datetime.strptime(col2[0] + " " + col3[0], "%m/%d/%Y %H:%M %p"))
                except Exception as e:
                    aTrial.setdate(0)
                    print(e)

                for xVal, yVal, timeVal in zip(col1[2:], col2[2:], col3[2:]):
                    logging.debug("Running through columns: " + str(timeVal) + str(xVal) + str(yVal))
                    values = []
                    if timeVal == "" and xVal == "" and yVal == "":
                        break
                    elif timeVal == "NaN" or xVal == "NaN" or yVal == "NaN":
                        aTrial.markDataAsCorrupted()
                        continue
                    else:
                        try:
                            aTrial.append(Datapoint(float(timeVal),float(xVal),float(yVal)))
                        except ValueError:
                            aTrial.markDataAsCorrupted()
                            continue

                if len(aTrial.datapointList) > 0:
                    trialList.append(aTrial)

        elif software == "eztrack":
            logging.info("Reading file ezTrack")
            experiment.setHasAnimalNames(False)
            experiment.setHasDateInfo(False)
            experiment.setHasTrialNames(True)
            try:
                f = open(filename)
            except:
                logging.info("Could not open " + filename)
                return

            reader = csv.reader(f, dialect)
            listReader = list(reader)
            aTrial = Trial()
            aTrial.setname(filename.split("/")[-1])
            columns = defaultdict(list)  # each value in each column is appended to a list
            aIndex = 0
            for aColumn in listReader[0]:
                if aColumn == "FPS":
                    fpsCol = aIndex
                elif aColumn == "Frame":
                    frameCol = aIndex
                elif aColumn == "X":
                    xCol = aIndex
                elif aColumn == "Y":
                    yCol = aIndex
                aIndex = aIndex +1
            for row in listReader:
                for (i, v) in enumerate(row):
                    columns[i].append(v)

            for fps, frame, x, y in zip(columns[fpsCol][1:], columns[frameCol][1:], columns[xCol][1:], columns[yCol][1:]):
                try:
                    time = float(frame)/float(fps)
                    x = float(x)
                    y = float(y)
                    print(time,x,y)
                    aTrial.append(Datapoint(time, x, y))
                except:
                    aTrial.markDataAsCorrupted()

            trialList.append(aTrial)

        elif software == "custom":
            logging.info("Reading file custom")
            experiment.setHasAnimalNames(False)
            experiment.setHasDateInfo(False)
            experiment.setHasTrialNames(False)
            try:
                f = open(filename)
            except IOError as e:
                logging.info(f"Could not open {filename}: {e}")
                return

            file_extension = os.path.splitext(filename)[1]
            
            # Get column mapping from modernized dialog
            column_mapping = defineOwnSoftware(None, filename)
            
            if column_mapping['x_col'] is None or column_mapping['y_col'] is None or column_mapping['t_col'] is None:
                logging.warning("Column mapping incomplete, skipping file")
                return
            
            if file_extension == '.csv':
                reader = pd.read_csv(filename, sep=";|,", header=None, engine='python')
            elif file_extension == '.xlsx':
                reader = pd.read_excel(filename, header=None)
            else:
                logging.error(f"Unsupported file type: {file_extension}")
                return

            aTrial = Trial()
            aTrial.setname(filename.split("/")[-1])
            
            xCol = column_mapping['x_col']
            yCol = column_mapping['y_col']
            tCol = column_mapping['t_col']
            dataStartRow = column_mapping['data_start_row']
            
            for index, row in reader.iloc[dataStartRow:].iterrows():
                try:
                    x = float(row[xCol])
                    y = float(row[yCol])
                    t = row[tCol]
                    
                    # Parse time value (supports HH:MM:SS, MM:SS, or numeric formats)
                    if isinstance(t, str) and t.count(':') == 2:
                        hours = float(t.split(':')[0])
                        minutes = float(t.split(':')[1])
                        seconds = float(t.split(':')[2])
                        time = seconds + minutes * 60 + hours * 3600
                    elif isinstance(t, str) and t.count(':') == 1:
                        minutes = float(t.split(':')[0])
                        seconds = float(t.split(':')[1])
                        time = seconds + minutes * 60
                    else:
                        time = float(t)
                    
                    if not math.isnan(x) and not math.isnan(y):
                        aTrial.append(Datapoint(time, x, y))
                except (ValueError, TypeError) as e:
                    logging.debug(f"Skipping row due to value error: {e}")
                    aTrial.markDataAsCorrupted()
            
            trialList.append(aTrial)
        else:
            logging.critical("Could not determine trial, saveFileAsTrial")
            return
    
    if experiment.hasDateInfo:
        trialList.sort(key=lambda t:t.date)
    
    experiment.setTrialList(trialList)
    return experiment
