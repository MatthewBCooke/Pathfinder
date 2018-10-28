# Module: appTrial.py
# Holds data structures

import csv
import math
import logging
import os
import fnmatch
from collections import defaultdict
from xlrd import open_workbook

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
        self.name = "DefaultName"
        self.date = "DefaultDate"
        self.trial = "DefaultTrial"

    def setname(self, name):
        self.name = name

    def setdate(self, date):
        self.date = date

    def settrial(self, trial):
        self.trial = trial

    def __str__(self):
        return self.name

    def append(self, adatapoint):
        self.datapointList.append(adatapoint)

    def __iter__(self):
        return iter(self.datapointList)


class Experiment(object):
    def __init__(self, name: str,trialList: list):
        self.name = name
        self.trialList = trialList

    def __str__(self):
        return self.name

    def append(self, atrial):
        self.trialList.append(atrial)

    def __iter__(self):
        return iter(self.trialList)


class Parameters:
    def __init__(self, name, cseMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, corridorAverageMinVal,
                 corridorCseMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, percentTraversedMaxVal,
                 percentTraversedMinVal, distanceToCentreMaxVal, innerWallMaxVal, outerWallMaxVal, cseIndirectMaxVal,
                 percentTraversedRandomMaxVal):

        self.name = name
        self.cseMaxVal = cseMaxVal
        self.headingMaxVal = headingMaxVal
        self.distanceToSwimMaxVal = distanceToSwimMaxVal
        self.distanceToPlatMaxVal = distanceToPlatMaxVal
        self.corridorAverageMinVal = corridorAverageMinVal
        self.corridorCseMaxVal = corridorCseMaxVal
        self.annulusCounterMaxVal = annulusCounterMaxVal
        self.quadrantTotalMaxVal = quadrantTotalMaxVal
        self.percentTraversedMaxVal = percentTraversedMaxVal
        self.percentTraversedMinVal = percentTraversedMinVal
        self.distanceToCentreMaxVal = distanceToCentreMaxVal
        self.innerWallMaxVal = innerWallMaxVal
        self.outerWallMaxVal = outerWallMaxVal
        self.cseIndirectMaxVal = cseIndirectMaxVal
        self.percentTraversedRandomMaxVal = percentTraversedRandomMaxVal

    def __str__(self):
        return self.name


def find_files(directory, pattern):  # searches for our files in the directory
        logging.debug("Finding files in the directory")
        for root, dirs, files in os.walk(directory):
            for basename in sorted(files):
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename

def saveFileAsExperiment(software, filename, filedirectory):
    trialList = []
    filenameList = []
    if filename == "":
        if filedirectory == "":
            logging.error("No files selected")
            return
        else:
            if software == "ethovision":
                extensionType = r"*.xlsx"
            elif software == "anymaze" or software == "watermaze":
                extensionType = r"*.csv"
            for aFile in find_files(filedirectory, extensionType):
                filenameList.append(aFile)
    else:
        filenameList.append(filename)

    for filename in filenameList:

        if software == "ethovision":
            logging.info("Reading file ethovision")
            try:
                wb = open_workbook(filename)
                logging.debug("Opened" + filename)
            except:
                logging.error("Unable to open excel file " + filename)
                return

            for sheet in wb.sheets():  # for all sheets in the workbook
                number_of_rows = sheet.nrows
                headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet

                for row in range(headerLines, number_of_rows):  # for each row

                    values = []
                    values.append(filename)
                    for col in range(1, 4):  # for columns 1 through 4, get all the values
                        value = sheet.cell(row, col).value
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                        finally:
                            values.append(value)

                    trialList.append(Trial(*values))

        elif software == "anymaze":
            logging.info("Reading anymaze")
            columns = defaultdict(list)  # each value in each column is appended to a list
            try:
                f = open(filename)
                logging.debug("Opened " + filename)
            except:
                logging.info("Could not open " + filename)
                return
            reader = csv.reader(f, delimiter=",")
            next(reader)
            for row in reader:
                for (i, v) in enumerate(row):
                    columns[i].append(v)

            for a, b, c in zip(columns[0], columns[1], columns[2]):
                values = []
                a = a.replace(":", "")
                values.append(float(a))
                try:
                    values.append(float(b))
                except:
                    values.append(b)
                try:
                    values.append(float(c))
                except:
                    values.append(c)
                trialList.append(Trial(*values))

        elif software == "watermaze":
            logging.info("Reading watermaze")
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

            for i in range(0, math.floor(number_of_columns / 3)):
                col1 = columns[i * 3]
                col2 = columns[1 + i * 3]
                col3 = columns[2 + i * 3]

                aTrial = Trial()
                aTrial.setname(col1[0])
                aTrial.setdate(col2[0])
                aTrial.settrial(col3[0])

                for a, b, c in zip(col1[2:], col2[2:], col3[2:]):
                    logging.debug("Running through columns: " + str(a) + str(b) + str(c))
                    values = []
                    if a == "" and b == "" and c == "":
                        break
                    elif a == "NaN" or b == "NaN" or c == "NaN":
                        continue
                    else:
                        try:
                            aTrial.append(Datapoint(float(c),float(a),float(b)))
                        except ValueError:
                            continue

                if len(aTrial.datapointList) > 0:
                    trialList.append(aTrial)

        else:
            logging.critical("Could not determine trial, saveFileAsTrial")
            return
    
    # sort by date then by time. Assumes time in 12-hour format
    trialList.sort(key=lambda t: (t.date, 0 if t.trial[-2:] == "AM" or t.trial[-2:] == "am" else 1, int(t.trial.split(":")[0]) % 12, int(t.trial.split(":")[1][:2])))
    return Experiment(filename, trialList)
