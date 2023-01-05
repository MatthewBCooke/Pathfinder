# Module: appTrial.py
# Holds data structures
#__requires__= 'xlrd==1.2.0'

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
#pkg_resources.require("xlrd==1.2.0")
import pandas as pd

#from xlrd import open_workbook
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

global customxyt
customxyt = []


def defineOwnSoftware(root, filename):
    file_extension = os.path.splitext(filename)[1]
    top = Toplevel(root)
    canvas = Canvas(top, borderwidth=0, width=800, height=600, bg="white")  # we create the canvas
    frame = Frame(canvas)  # we place a frame in the canvas
    frame.configure(bg="white")
    xscrollbar = Scrollbar(top, orient=HORIZONTAL, command=canvas.xview)  # we add a horizontal scroll bar
    yscrollbar = Scrollbar(top, orient="vertical", command=canvas.yview)  # vertical scroll bar
    xscrollbar.pack(side=BOTTOM, fill=X)  # we put the horizontal scroll bar on the bottom
    yscrollbar.pack(side="right", fill="y")  # put on right

    canvas.pack(side="left", fill="both", expand=True)  # we pack in the canvas
    canvas.create_window((4, 4), window=frame, anchor="nw")  # we create the window for the results
    canvas.configure(xscrollcommand=xscrollbar.set)
    canvas.configure(yscrollcommand=yscrollbar.set)  # we set the commands for the scroll bars
    frame.bind("<Configure>", lambda event, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))
    top.attributes('-topmost', True)

    # display selected XYT columns using a status bar
    theStatus = StringVar()
    theStatus.set("[First X, Y, time values]: ")
    status = Label(frame, textvariable=theStatus, width=50, height=2, relief=SUNKEN, anchor=W, bg="white")
    status.grid(row=0, column=0, columnspan=4)
    global customxyt
    def okButton():
        if (len(customxyt) == 3):
            top.attributes('-topmost', False)
            messagebox.showinfo(None, "First X value: " + str(list(map(add, list(customxyt[0]),[1,1])))
                                + "\nFirst Y value: " + str(list(map(add, list(customxyt[1]),[1,1])))
                                + "\nFirst time value: " + str(list(map(add, list(customxyt[2]),[1,1]))))
            top.quit()
            top.destroy()
        else:
            top.attributes('-topmost', False)
            messagebox.showinfo(None, "Please select three columns!")
            top.attributes('-topmost', True)

    def resetButton():
        global customxyt
        customxyt = []
        theStatus.set("[First X, Y, time values]: ")

    def displayTable(data):
        r = 0
        for col in data:
            c = 0
            for row in col:
                coord = (r, c)
                if (r < 45) and (c < 11):
                    cell = Label(frame, width=12, height=1, text=row, borderwidth=2, relief="groove")
                    cell.grid(row=r + 1, column=c)
                    cell.bind("<Button-1>", lambda event: getXYT(event))
                c += 1
            r += 1

    # gets column number from clicked column
    def getXYT(event):
        info = event.widget.grid_info()
        coord = (int(info["column"]), int(info["row"])-1)
        customxyt.append(coord)
        theStatus.set("[First X, Y, time values]: " + str(customxyt))

    # display table
    if (file_extension == '.csv'):
        with open(filename, newline="") as file:
            try:
                dialect = csv.Sniffer().sniff(file.readline())
                file.seek(0)
                data = csv.reader(file, dialect)
                displayTable(data)

                okbutton = Button(frame, text="Save", width=12, height=2, command=okButton)
                okbutton.grid(row=0, column=4)
                resetbutton = Button(frame, text="Reset", width=12, height=2, command=resetButton)
                resetbutton.grid(row=0, column=5)

                top.attributes('-topmost', False)
                messagebox.showinfo(None, "Please select the first X value (e.g. 23.45), then the first Y value, and finally the starting Time value.")
                top.attributes('-topmost', True)
                top.mainloop()
            except:
                top.attributes('-topmost', False)
                messagebox.showinfo(None, "Invalid CSV format.")
                top.destroy()
                top.mainloop()
    elif (file_extension == '.xlsx'):
        try:
            data = pd.read_excel(filename)
            displayTable(data.values)

            okbutton = Button(frame, text="Save", width=12, height=2, command=okButton)
            okbutton.grid(row=0, column=4)
            resetbutton = Button(frame, text="Reset", width=12, height=2, command=resetButton)
            resetbutton.grid(row=0, column=5)

            top.attributes('-topmost', False)
            messagebox.showinfo(None, "Please select the first X value (e.g. 23.45), then the first Y value, and finally the starting Time value.")
            top.attributes('-topmost', True)
            top.mainloop()
        except:
            top.attributes('-topmost', False)
            messagebox.showinfo(None, "Error opening Excel table.")


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
                print("TIME: ",time)
                if (sum(map(lambda x : 1 if ':' in x else 0, time))>0):
                    try:
                        if (sum(map(lambda x : 1 if ':' in x else 0, time)) == 2):
                            hours = float(time.split(':')[0])
                            minutes = float(time.split(':')[1])
                            seconds = float(time.split(':')[2])
                        else:
                            minutes = float(time.split(':')[0])
                            seconds = float(time.split(':')[1])
                            hours = 0
                        time = seconds + minutes*60 + hours*3600
                    except:
                        aTrial.markDataAsCorrupted()
                else:
                    time = float(time)
 
                x = float(x)
                y = float(y)
                aTrial.append(Datapoint(time, x, y))
                
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
            except:
                logging.info("Could not open " + filename)
                return

            file_extension = os.path.splitext(filename)[1]
            if (file_extension == '.csv'):
                # reader = csv.reader(f, dialect)
                reader = pd.read_csv(filename, sep=";|,", header=None, engine='python')
            elif (file_extension == '.xlsx'):
                reader = pd.read_excel(filename, header=None)


            # listReader = list(reader)
            aTrial = Trial()
            aTrial.setname(filename.split("/")[-1])
            aIndex = 0
            xCol = customxyt[0][0]
            yCol = customxyt[1][0]
            tCol = customxyt[2][0]
            dataStartRow = customxyt[0][1]
            for index, row in reader.iloc[dataStartRow:].iterrows():
                try:
                    x = float(row[xCol])
                    y = float(row[yCol])
                    t = row[tCol]
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
                    # print(time, x, y)
                    if not math.isnan(x) and not math.isnan(y):
                        aTrial.append(Datapoint(time, x, y))
                except:
                    aTrial.markDataAsCorrupted()
            trialList.append(aTrial)
        else:
            logging.critical("Could not determine trial, saveFileAsTrial")
            return
    
    if experiment.hasDateInfo:
        trialList.sort(key=lambda t:t.date)
    
    experiment.setTrialList(trialList)
    return experiment
