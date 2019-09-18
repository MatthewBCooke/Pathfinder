# Module: appTrial.py
# Holds data structures

import csv
import math
import logging
import os
import fnmatch
import datetime
from collections import defaultdict
from xlrd import open_workbook
from tkinter import filedialog

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


def defineOwnSoftware():
    filename = ""
    file_extension = ""
    filename = openFile()
    if filename == "":
        logging.error("Please select a file")
        print("Please select a file")
        return
    else:
        print("TODO")
        pass
        filename, file_extension = os.path.splitext(filename)



'''
def heatmapSettings(self, top3):
	        global softwareStringVar
	        software = softwareStringVar.get()
	        if software != "ethovision":
	            return
	        global canvas
	        global xscrollbar
	        global vsb
	        global frame
	        global fileDirectory
	        global heatValues
	        global flags
	        global labels
	
	        heatValues = []
	        flags = []
	        labels = []
	
	        extensionType = r"*.xlsx"
	        try:  # we try to delete a canvas (if one exists this will execute)
	            deleteCanvas()
	            logging.info("Canvas destroyed")
	        except:
	            logging.debug("Didn't kill canvas, could be first call")
	
	        logging.debug("heatmapSettings")
	
	        try:
	
	            canvas = Canvas(top3, borderwidth=0, width=350, height=800, bg="white")  # we create the canvas
	            frame = Frame(canvas)  # we place a frame in the canvas
	            frame.configure(bg="white")
	            xscrollbar = Scrollbar(top3, orient=HORIZONTAL, command=canvas.xview)  # we add a horizontal scroll bar
	            xscrollbar.pack(side=BOTTOM, fill=X)  # we put the horizontal scroll bar on the bottom
	            vsb = Scrollbar(top3, orient="vertical", command=canvas.yview)  # vertical scroll bar
	            vsb.pack(side="right", fill="y")  # put on right
	
	            canvas.pack(side="left", fill="both", expand=True)  # we pack in the canvas
	            canvas.create_window((4, 4), window=frame, anchor="nw")  # we create the window for the results
	
	            canvas.configure(yscrollcommand=vsb.set)  # we set the commands for the scroll bars
	            canvas.configure(xscrollcommand=xscrollbar.set)
	            frame.bind("<Configure>", lambda event, canvas=canvas: self.onFrameConfigure(canvas))   # we bind on frame configure
	        except:
	            logging.critical("Couldn't create the CSV canvas")
	
	        try:  # we try and fill the canvas
	            logging.debug("Populating the canvas")
	            for aFile in self.find_files(fileDirectory, extensionType):
	                try:
	                    wb = open_workbook(aFile)
	                    logging.debug("Opened" + aFile)
	                except:
	                    logging.error("Could not open excel file: " + aFile)
	                    continue
	
	                for sheet in wb.sheets():  # for all sheets in the workbook
	                    for row in range(38):  # GET CONDITION TREATMENT AND DAY VALUES
	                        for col in range(2):
	                            if str(sheet.cell(row, 0).value) != "":
	                                if col == 0:
	                                    labels.append(str(sheet.cell(row, 0).value))
	                                    heatmapValueFlag = BooleanVar()
	                                    heatmapValueFlag.set(False)
	                                    button = Checkbutton(frame, width=30, height=1, \
	                                                    text=str(sheet.cell(row, col).value), relief=RAISED, bg="white", variable=heatmapValueFlag)
	                                    button.grid(row=row, column=col)
	                                    flags.append(heatmapValueFlag)
	                                else:
	                                    value = StringVar()
	                                    value.set(str(sheet.cell(row, col).value))
	                                    label = Entry(frame, width=30, textvariable=value)
	                                    label.grid(row=row, column=col)
	                                    heatValues.append(value)
	                return
	
	        except Exception:  # if we can't fill
	            logging.critical("Fatal error in populate")
	

'''






def saveFileAsExperiment(software, filename, filedirectory):
    trialList = []
    filenameList = []
    experiment = Experiment(filename)
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

        if software == "ethovision":
            logging.info("Reading file ethovision")
            experiment.setHasAnimalNames(True)
            experiment.setHasDateInfo(True)
            experiment.setHasTrialNames(True)

            try:
                wb = open_workbook(filename)
                logging.debug("Opened" + filename)
            except Exception:
                traceback.print_exc()
                logging.error("Unable to open excel file " + filename)
                return

            for sheet in wb.sheets():  # for all sheets in the workbook
                number_of_rows = sheet.nrows
                headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet
                aTrial = Trial()

                for row in range(1, headerLines):
                    if sheet.cell(row, 0).value.upper() == 'TRIAL NAME':
                        aTrial.setname(sheet.cell(row, 1).value)
                    elif sheet.cell(row, 0).value.upper() == 'TRIAL ID':
                        aTrial.settrial(int(sheet.cell(row, 1).value))
                    elif sheet.cell(row, 0).value.upper() == 'START TIME':
                        aTrial.setdate(datetime.datetime.strptime(sheet.cell(row, 1).value, "%d/%m/%Y %H:%M:%S"))
                    elif sheet.cell(row, 0).value.upper() == 'ANIMAL ID':
                        aTrial.setanimal(sheet.cell(row, 1).value)
                    elif sheet.cell(row, 0).value.upper() == 'DAY':
                        aTrial.setday(sheet.cell(row, 1).value)
                    elif sheet.cell(row, 0).value.upper() == 'TRIAL':
                        try:
                            aTrial.settrial(int(sheet.cell(row, 1).value))
                        except:
                            pass

                for row in range(headerLines, number_of_rows):  # for each row
                    time = sheet.cell(row, 1).value
                    x = sheet.cell(row, 2).value
                    y = sheet.cell(row, 3).value

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
            reader = csv.reader(f, delimiter=",")
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

            reader = csv.reader(f, delimiter=",")
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

            reader = csv.reader(f, delimiter=",")
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

        else:
            logging.critical("Could not determine trial, saveFileAsTrial")
            return
    
    if experiment.hasDateInfo:
        trialList.sort(key=lambda t:t.date)
    
    experiment.setTrialList(trialList)
    return experiment
