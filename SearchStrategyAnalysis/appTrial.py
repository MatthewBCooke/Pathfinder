# Module: appTrial.py
# Holds data structures

import csv
import math
import logging
from collections import defaultdict
from xlrd import open_workbook


class Trial(object):  # an object for our row values
    def __init__(self, name, time, x, y):
        self.name = name
        self.time = time
        self.x = x
        self.y = y

    def __str__(self):
        return("Trial object:\n"
               "  Name = {0}\n"
               "  Time = {1}\n"
               "  x = {2}\n"
               "  y = {3}"
               .format(self.name, self.time, self.x, self.y))


class Experiment(object):
    def __init__(self, name: str, trialList: list):
        self.name = name
        self.trialList = trialList

    def __str__(self):
        return self.name

    def append(self, atrial):
        self.trialList.append(atrial)


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



def saveFileAsExperiment(software, fileName):
    trialList = []
    if fileName == "":
        logging.error("fileName is empty")
        return

    if software == "ethovision":
        logging.info("Extension set to xlsx")
        logging.info("Reading file ethovision")
        try:
            wb = open_workbook(fileName)
            logging.debug("Opened" + fileName)
        except:
            logging.error("Unable to open excel file " + fileName)
            return

        for sheet in wb.sheets():  # for all sheets in the workbook
            number_of_rows = sheet.nrows
            headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet

            for row in range(headerLines, number_of_rows):  # for each row

                values = []
                values.append(fileName)
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
        logging.info("Extension set to csv")
        logging.info("Reading anymaze")
        columns = defaultdict(list)  # each value in each column is appended to a list
        try:
            f = open(fileName)
            logging.debug("Opened " + fileName)
        except:
            logging.info("Could not open " + fileName)
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
        logging.info("Extension set to csv")
        logging.info("Reading watermaze")
        columns = defaultdict(list)  # each value in each column is appended to a list

        number_of_columns = 0
        try:
            f = open(fileName)
        except:
            logging.info("Could not open " + fileName)
            return

        reader = csv.reader(f, delimiter=",")
        for row in reader:
            for (i, v) in enumerate(row):
                columns[i].append(v)
                number_of_columns = i

        for i in range(0, math.floor(number_of_columns / 3)):
            i = 0.0
            firstFlag = True
            secondFlag = False
            for a, b, c in zip(columns[i * 3], columns[1 + i * 3], columns[2 + i * 3]):
                logging.debug("Running through columns: " + str(a) + str(b) + str(c))
                values = []
                if firstFlag == True:
                    if a == "" or b == "" or c == "":
                        continue
                    firstFlag = False
                    secondFlag = True
                elif secondFlag == True:
                    secondFlag = False
                    continue
                else:
                    if a == "" or b == "" or c == "":
                        continue
                    values.append(float(c))
                    values.append(float(a))
                    values.append(float(b))
                    item = Trial(*values)
                    trialList.append(item)
    else:
        logging.critical("Could not determine trial, saveFileAsTrial")
        return

    return Experiment(fileName, trialList)