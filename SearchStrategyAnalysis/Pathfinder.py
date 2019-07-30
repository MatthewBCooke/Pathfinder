#!/usr/bin/env python

"""Pathfinder.py"""

from __future__ import print_function
import csv
import fnmatch
import logging
import math
import os, subprocess
import sys
import threading
import webbrowser
import statistics
from collections import defaultdict
from sys import platform as _platform
from time import localtime, strftime
import PIL.Image
from PIL import ImageTk
from xlrd import open_workbook
from functools import partial
import numpy as np
import pickle
import datetime
import scipy.ndimage as sp
try:
    from SearchStrategyAnalysis.appTrial import Trial, Experiment, Parameters, saveFileAsExperiment, Datapoint
    import SearchStrategyAnalysis.heatmap
except:
    from appTrial import Trial, Experiment, Parameters, saveFileAsExperiment, Datapoint
    import heatmap
from scipy.stats import norm
import re
import traceback



try:
    import matlab.engine
    canUseMatlab = True
except:
    print("MATLAB Engine Unavailable")
    canUseMatlab = False


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
if _platform == "darwin":
    import matplotlib
    matplotlib.use('TkAgg')  # prevent bugs on Mac
import matplotlib.pyplot as plt
from matplotlib import cm as CM

__author__ = "Matthew Cooke"
__copyright__ = "Copyright 2019, Jason Snyder Lab, The University of British Columbia"
__credits__ = ["Matthew Cooke", "Tim O'Leary", "Phelan Harris"]
__email__ = "mbcooke@mail.ubc.ca"

if not os.path.exists("output"):
    os.makedirs("output")
if not os.path.exists("output/logs"):
    os.makedirs("output/logs")
if not os.path.exists("output/results"):
    os.makedirs("output/results")
if not os.path.exists("output/plots"):
    os.makedirs("output/plots")
if not os.path.exists("output/heatmaps"):
    os.makedirs("output/heatmaps")

logfilename = "output/logs/logfile " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime())) + ".log"  # name of the log file for the run
logging.basicConfig(filename=logfilename,level=logging.DEBUG)  # set the default log type to INFO, can be set to DEBUG for more detailed information
csvfilename = "output/results/results " + str(
    strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # name of the default results file
theFile = ""
fileDirectory = ""
goalPosVar = "Auto"
mazeDiamVar = "Auto"
goalPosVar = "Auto"
goalDiamVar = "Auto"
mazeDiamVar = "Auto"
corridorWidthVar = "40"
mazeCentreVar = "Auto"
chainingRadiusVar = "35"
thigmotaxisZoneSizeVar = "15"
outputFile = csvfilename
fileFlag = 0
probeCutVar = math.inf #stop probe trials at X seconds, inf = no cutoff

defaultParams = Parameters(name="Default", ipeMaxVal=125, headingMaxVal=40, distanceToSwimMaxVal=0.3,
                           distanceToPlatMaxVal=0.3, corridorAverageMinVal=0.7, directedSearchMaxDistance=400, focalMinDistance=100, focalMaxDistance=400, corridoripeMaxVal=1500,
                           annulusCounterMaxVal=0.90, quadrantTotalMaxVal=4, chainingMaxCoverage=40, percentTraversedMaxVal=20,
                           percentTraversedMinVal=5, distanceToCentreMaxVal=0.6, thigmoMinDistance=400, innerWallMaxVal=0.65,
                           outerWallMaxVal=0.35, ipeIndirectMaxVal=300, percentTraversedRandomMaxVal=10, headingIndirectMaxVal=70)

params = defaultParams

ipeMaxVal = params.ipeMaxVal
headingMaxVal = params.headingMaxVal
distanceToSwimMaxVal = params.distanceToSwimMaxVal
distanceToPlatMaxVal = params.distanceToPlatMaxVal
corridorAverageMinVal = params.corridorAverageMinVal
corridoripeMaxVal = params.corridoripeMaxVal
annulusCounterMaxVal = params.annulusCounterMaxVal
quadrantTotalMaxVal = params.quadrantTotalMaxVal
percentTraversedMaxVal = params.percentTraversedMaxVal
percentTraversedMinVal = params.percentTraversedMinVal
distanceToCentreMaxVal = params.distanceToCentreMaxVal
innerWallMaxVal = params.innerWallMaxVal
outerWallMaxVal = params.outerWallMaxVal
ipeIndirectMaxVal = params.ipeIndirectMaxVal
percentTraversedRandomMaxVal = params.percentTraversedRandomMaxVal
directedSearchMaxDistance = params.directedSearchMaxDistance
focalMinDistance = params.focalMinDistance
focalMaxDistance = params.focalMaxDistance
chainingMaxCoverage = params.chainingMaxCoverage
thigmoMinDistanceCustom = params.thigmoMinDistance
headingIndirectMaxVal = params.headingIndirectMaxVal

customFlag = False
useDirectPathV = True
useFocalSearchV = True
useDirectedSearchV = True
useScanningV = True
useChainingV = True
useRandomV = True
useIndirectV = True
useThigmoV = True

root = Tk()  # set up the root
theStatus = StringVar()  # create the status bar text
theStatus.set('Waiting for user input...')  # set status bar text
goalPosStringVar = StringVar()  # setup all the gui variables (different from normal variables)
goalPosStringVar.set(goalPosVar)
goalDiamStringVar = StringVar()
goalDiamStringVar.set(goalDiamVar)
mazeDiamStringVar = StringVar()
mazeDiamStringVar.set(mazeDiamVar)
corridorWidthStringVar = StringVar()
corridorWidthStringVar.set(corridorWidthVar)
mazeCentreStringVar = StringVar()
mazeCentreStringVar.set(mazeCentreVar)
chainingRadiusStringVar = StringVar()
chainingRadiusStringVar.set(chainingRadiusVar)
thigmotaxisZoneSizeStringVar = StringVar()
thigmotaxisZoneSizeStringVar.set(thigmotaxisZoneSizeVar)
softwareScalingFactorStringVar = StringVar()
softwareScalingFactorStringVar.set("1.0")
outputFileStringVar = StringVar()
outputFileStringVar.set(outputFile)
maxValStringVar = StringVar()
maxValStringVar.set("Auto")
dayValStringVar = StringVar()
dayValStringVar.set("All")
trialValStringVar = StringVar()
trialValStringVar.set("All")
gridSizeStringVar = StringVar()
gridSizeStringVar.set("70")
useManual = BooleanVar()
useManual.set(False)
useManualForAll = BooleanVar()
useManualForAll.set(False)
useEntropy = BooleanVar()
useEntropy.set(False)
truncate = BooleanVar()
truncate.set(False)
useScaling = BooleanVar()
useScaling.set(False)
scale = False
rois = []

def show_error(text):  # popup box with error text
    logging.debug("Displaying Error")
    try:
        top = Toplevel(root)  # show as toplevel
        Label(top, text=text).pack()   # label set to text
        Button(top, text="OK", command=top.destroy).pack(pady=5)   # add ok button
    except:
        logging.info("Couldn't Display error "+text)

class EntryWithPlaceholder(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey'):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()

class mainClass:
    def __init__(self, root):  # init is called on runtime
        logging.debug("Initiating Main program")
        try:
            self.buildGUI(root)
        except Exception:
            traceback.print_exc()
            logging.fatal("Couldn't build GUI")
            self.tryQuit()
            return
        logging.debug("GUI is built")

    def buildGUI(self, root):  # Called in the __init__ to build the GUI window
        root.wm_title("Pathfinder")

        global goalPosVar
        global goalDiamVar
        global mazeDiamVar
        global corridorWidthVar
        global mazeCentreVar
        global chainingRadiusVar
        global thigmotaxisZoneSizeVar
        global outputFile
        global manualFlag
        global useManualForAllFlag
        global useEntropyFlag
        global truncateFlag
        global softwareStringVar
        global softwareScalingFactorStringVar

        softwareStringVar = StringVar()
        softwareStringVar.set("ethovision")


        if _platform == "darwin":
            accelF = "CMD+F"
            accelD = "CMD+D"
            accelX = "CMD+X"
            accelC = "CMD+C"
            accelV = "CMD+V"
        else:
            accelF = "Ctrl+F"
            accelD = "Ctrl+D"
            accelX = "Ctrl+X"
            accelC = "Ctrl+C"
            accelV = "Ctrl+V"

        root.geometry('{}x{}'.format( 700, 500 ))

        self.menu = Menu(root)  # create a menu
        root.config(menu=self.menu, bg="white")  # set up the config
        self.fileMenu = Menu(self.menu, tearoff=False)  # create file menu
        self.menu.add_cascade(label="File", menu=self.fileMenu)  # add cascading menus
        self.fileMenu.add_command(label="Open File...", accelerator=accelF,
                                  command=self.openFile)  # add buttons in the menus
        self.fileMenu.add_command(label="Open Directory...", accelerator=accelD, command=self.openDir)
        self.fileMenu.add_separator()  # adds a seperator
        self.fileMenu.add_command(label="Generate Heatmap", command=lambda: self.generateHeatmap(root))
        self.fileMenu.add_separator()  # adds a seperator
        self.fileMenu.add_command(label="Exit", command=self.tryQuit)  # exit button quits

        self.editMenu = Menu(self.menu, tearoff=False)  # create edit menu
        self.menu.add_cascade(label="Edit", menu=self.editMenu)
        self.editMenu.add_command(label="Cut", \
                                  accelerator=accelX, \
                                  command=lambda: \
                                      root.focus_get().event_generate('<<Cut>>'))
        self.editMenu.add_command(label="Copy", \
                                  accelerator=accelC, \
                                  command=lambda: \
                                      root.focus_get().event_generate('<<Copy>>'))
        self.editMenu.add_command(label="Paste", \
                                  accelerator=accelV, \
                                  command=lambda: \
                                      root.focus_get().event_generate('<<Paste>>'))

        self.windowMenu = Menu(self.menu, tearoff=False)  # create window menu
        self.menu.add_cascade(label="Window", menu=self.windowMenu)
        self.windowMenu.add_command(label="Maximize", command=self.maximize)
        self.windowMenu.add_command(label="Minimize", command=self.minimize)

        self.helpMenu = Menu(self.menu, tearoff=False)  # create help menu
        self.menu.add_cascade(label="Help", menu=self.helpMenu)
        self.helpMenu.add_command(label="Help", command=self.getHelp)
        self.helpMenu.add_command(label="About", command=self.about)

        rowCount = 0
        # ******* Software Type *******
        self.softwareBar = Frame(root)  # add a toolbar to the frame
        self.softwareBar.config(bg="white")
        self.ethovisionRadio = Radiobutton(self.softwareBar, text="Ethovision", variable=softwareStringVar,
                                           value="ethovision",
                                           indicatoron=1, width=15, bg="white")
        self.ethovisionRadio.grid(row=rowCount, column=0, padx=5, sticky='NW')  # add the radiobuttons for selection

        self.anymazeRadio = Radiobutton(self.softwareBar, text="Anymaze", variable=softwareStringVar,
                                        value="anymaze",
                                        indicatoron=1, width=15, bg="white")
        self.anymazeRadio.grid(row=rowCount, column=1, padx=5, sticky='NW')
        self.watermazeRadio = Radiobutton(self.softwareBar, text="Watermaze", variable=softwareStringVar,
                                          value="watermaze", indicatoron=1, width=15, bg="white")
        self.watermazeRadio.grid(row=rowCount, column=2, padx=5, sticky='NW')
        self.eztrackRadio = Radiobutton(self.softwareBar, text="ezTrack", variable=softwareStringVar,
                                          value="eztrack", indicatoron=1, width=15, bg="white")
        self.eztrackRadio.grid(row=rowCount, column=3, padx=5, sticky='NW')
        self.softwareBar.pack(side=TOP, fill=X, pady =5)

        self.ethovisionRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Ethovision to generate your data"))
        self.ethovisionRadio.bind("<Leave>", self.on_leave)
        self.anymazeRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Anymaze to generate your data"))
        self.anymazeRadio.bind("<Leave>", self.on_leave)
        self.watermazeRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Watermaze to generate your data"))
        self.watermazeRadio.bind("<Leave>", self.on_leave)
        self.eztrackRadio.bind("<Enter>", partial(self.on_enter, "Click if you used ezTrack to generate your data"))
        self.eztrackRadio.bind("<Leave>", self.on_leave)

        # ******* STATUS BAR *******
        self.status = Label(root, textvariable=theStatus, bd=1, relief=SUNKEN, anchor=W, bg="white")  # setup the status bar
        self.status.pack(side=BOTTOM, anchor=W, fill=X)  # place the status bar

        # ****** PARAMETERS SIDE ******
        self.paramFrame = Frame(root, bd=1, bg="white")  # create a frame for the parameters
        self.paramFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)  # place this on the left

        try:
            with open('mainobjs.pickle', 'rb') as f:
                goalPosVar, goalDiamVar, mazeDiamVar, mazeCentreVar, corridorWidthVar, chainingRadiusVar, thigmotaxisZoneSizeVar, softwareScalingFactorVar = pickle.load(f)
                goalPosStringVar.set(goalPosVar)
                goalDiamStringVar.set(goalDiamVar)
                mazeDiamStringVar.set(mazeDiamVar)
                mazeCentreStringVar.set(mazeCentreVar)
                corridorWidthStringVar.set(corridorWidthVar)
                chainingRadiusStringVar.set(chainingRadiusVar)
                thigmotaxisZoneSizeStringVar.set(thigmotaxisZoneSizeVar)
                softwareScalingFactorStringVar.set(softwareScalingFactorVar)
        except:
            pass

        rowCount = rowCount+1
        self.goalPos = Label(self.paramFrame, text="Goal Position (x,y):", bg="white")  # add different items (Position)
        self.goalPos.grid(row=rowCount, column=0, sticky=E)  # place this in row 0 column 0
        self.goalPosE = Entry(self.paramFrame, textvariable=goalPosStringVar)  # add an entry text box
        self.goalPosE.grid(row=rowCount, column=1)  # place this in row 0 column 1
        self.goalPos.bind("<Enter>", partial(self.on_enter, "Goal position. Example: 2.5,-3.72 or Auto"))
        self.goalPos.bind("<Leave>", self.on_leave)
        self.otherROIButton = Button(self.paramFrame, text="Add Goal...", command=self.otherROI, fg="black")
        self.otherROIButton.grid(row=rowCount, column=2)  # add custom button
        self.otherROIButton.bind("<Enter>", partial(self.on_enter, "Add more Regions of Interest to be considered in strategy calculation"))
        self.otherROIButton.bind("<Leave>", self.on_leave)
        self.otherROIButton.config(width = 10)
        rowCount = rowCount+1
        self.goalDiam = Label(self.paramFrame, text="Goal Diameter (cm):", bg="white")
        self.goalDiam.grid(row=rowCount, column=0, sticky=E)
        self.goalDiamE = Entry(self.paramFrame, textvariable=goalDiamStringVar)
        self.goalDiamE.grid(row=rowCount, column=1)
        self.goalDiam.bind("<Enter>", partial(self.on_enter, "Goal diameter. Use the same unit as the data"))
        self.goalDiam.bind("<Leave>", self.on_leave)
        rowCount = rowCount+1
        self.mazeDiam = Label(self.paramFrame, text="Maze Diameter (cm):", bg="white")
        self.mazeDiam.grid(row=rowCount, column=0, sticky=E)
        self.mazeDiamE = Entry(self.paramFrame, textvariable=mazeDiamStringVar)
        self.mazeDiamE.grid(row=rowCount, column=1)
        self.mazeDiam.bind("<Enter>", partial(self.on_enter, "The diameter of the maze. Use the same unit as the data"))
        self.mazeDiam.bind("<Leave>", self.on_leave)
        rowCount = rowCount+1
        self.mazeCentre = Label(self.paramFrame, text="Maze Centre (x,y):", bg="white")
        self.mazeCentre.grid(row=rowCount, column=0, sticky=E)
        self.mazeCentreE = Entry(self.paramFrame, textvariable=mazeCentreStringVar)
        self.mazeCentreE.grid(row=rowCount, column=1)
        self.mazeCentre.bind("<Enter>", partial(self.on_enter, "Maze Centre. Example: 0.0,0.0 or Auto"))
        self.mazeCentre.bind("<Leave>", self.on_leave)
        rowCount = rowCount+1

        self.headingError = Label(self.paramFrame, text="Angular Corridor Width (degrees):", bg="white")
        self.headingError.grid(row=rowCount, column=0, sticky=E)
        self.headingErrorE = Entry(self.paramFrame, textvariable=corridorWidthStringVar)
        self.headingErrorE.grid(row=rowCount, column=1)
        self.headingError.bind("<Enter>", partial(self.on_enter, "This is an angular corridor (in degrees) in which the animal must face"))
        self.headingError.bind("<Leave>", self.on_leave)
        rowCount = rowCount+1

        self.chainingRadius = Label(self.paramFrame, text="Chaining Annulus Width (cm):", bg="white")
        self.chainingRadius.grid(row=rowCount, column=0, sticky=E)
        self.chainingRadiusE = Entry(self.paramFrame, textvariable=chainingRadiusStringVar)
        self.chainingRadiusE.grid(row=rowCount, column=1)
        self.chainingRadius.bind("<Enter>", partial(self.on_enter, "The diameter of the ring in which chaining is considered (centered on goal)"))
        self.chainingRadius.bind("<Leave>", self.on_leave)

        rowCount = rowCount+1
        self.thigmotaxisZoneSize = Label(self.paramFrame, text="Thigmotaxis Zone Size (cm):", bg="white")
        self.thigmotaxisZoneSize.grid(row=rowCount, column=0, sticky=E)
        self.thigmotaxisZoneSizeE = Entry(self.paramFrame, textvariable=thigmotaxisZoneSizeStringVar)
        self.thigmotaxisZoneSizeE.grid(row=rowCount, column=1)
        self.thigmotaxisZoneSize.bind("<Enter>", partial(self.on_enter, "Size of the zone in which thigmotaxis is considered (from the outer wall)"))
        self.thigmotaxisZoneSize.bind("<Leave>", self.on_leave)
        rowCount = rowCount+1

        self.softwareScalingFactor = Label(self.paramFrame, text="Pixels/cm for scaling:", bg="white")
        self.softwareScalingFactor.grid(row=rowCount, column=0, sticky=E)
        self.softwareScalingFactorE = Entry(self.paramFrame, textvariable=softwareScalingFactorStringVar)
        self.softwareScalingFactorE.grid(row=rowCount, column=1)
        self.softwareScalingFactor.bind("<Enter>", partial(self.on_enter, "This is used to convert Anymaze and Watermaze from Pixels to cm"))
        self.softwareScalingFactor.bind("<Leave>", self.on_leave)

        rowCount = rowCount+1
        self.saveDirectory = Label(self.paramFrame, text="Output File (.csv):", bg="white")
        self.saveDirectory.grid(row=rowCount, column=0, sticky=E)
        self.saveDirectoryE = Entry(self.paramFrame, textvariable=outputFileStringVar)
        self.saveDirectoryE.grid(row=rowCount, column=1)
        self.saveDirectory.bind("<Enter>", partial(self.on_enter, "The csv file to store the results"))
        self.saveDirectory.bind("<Leave>", self.on_leave)


        global outputFile  # allow outputFile to be accessed from anywhere (not secure)
        outputFile = outputFileStringVar.get()  # get the value entered for the ouput file

        manualFlag = False  # a flag that lets us know if we want to use manual categorization
        useManualForAllFlag = False
        useEntropyFlag = False
        truncateFlag = False
        rowCount = rowCount+1
        self.scalingTickL = Label(self.paramFrame, text="Scale values (convert pixels to cm): ", bg="white")  # label for the tickbox
        self.scalingTickL.grid(row=rowCount, column=0, sticky=E)  # placed here
        self.scalingTickC = Checkbutton(self.paramFrame, variable=useScaling, bg="white")  # the actual tickbox
        self.scalingTickC.grid(row=rowCount, column=1)
        self.scalingTickL.bind("<Enter>", partial(self.on_enter, "Check if you want to scale the values to fit your maze"))
        self.scalingTickL.bind("<Leave>", self.on_leave)


        scale = useScaling.get()
        rowCount = rowCount+1
        self.manualTickL = Label(self.paramFrame, text="Manual categorization for uncategorized trials: ", bg="white")  # label for the tickbox
        self.manualTickL.grid(row=rowCount, column=0, sticky=E)  # placed here
        self.manualTickC = Checkbutton(self.paramFrame, variable=useManual, bg="white")  # the actual tickbox
        self.manualTickC.grid(row=rowCount, column=1)
        self.manualTickL.bind("<Enter>", partial(self.on_enter, "Unrecognized strategies will popup so you can manually categorize them"))
        self.manualTickL.bind("<Leave>", self.on_leave)
        rowCount = rowCount+1
        self.manualForAllL = Label(self.paramFrame, text="Manual categorization for all trials: ", bg="white")  # label for the tickbox
        self.manualForAllL.grid(row=rowCount, column=0, sticky=E)  # placed here
        self.manualForAllC = Checkbutton(self.paramFrame, variable=useManualForAll, bg="white")  # the actual tickbox
        self.manualForAllC.grid(row=rowCount, column=1)
        self.manualForAllL.bind("<Enter>", partial(self.on_enter, "All trials will popup so you can manually categorize them"))
        self.manualForAllL.bind("<Leave>", self.on_leave)
        rowCount = rowCount+1

        if canUseMatlab:
            self.entropyL = Label(self.paramFrame, text="Run entropy calculation: ", bg="white")  # label for the tickbox
            self.entropyL.grid(row=rowCount, column=0, sticky=E)  # placed here
            self.entropyC = Checkbutton(self.paramFrame, variable=useEntropy, bg="white")  # the actual tickbox
            self.entropyC.grid(row=rowCount, column=1)
            self.entropyL.bind("<Enter>", partial(self.on_enter, "Calculates the entropy of the trial (slow)"))
            self.entropyL.bind("<Leave>", self.on_leave)
            rowCount = rowCount+1

        self.truncateL = Label(self.paramFrame, text="Truncate trials when animal reaches goal location: ", bg="white")  # label for the tickbox
        self.truncateL.grid(row=rowCount, column=0, sticky=E)  # placed here
        self.truncateC = Checkbutton(self.paramFrame, variable=truncate, bg="white")  # the actual tickbox
        self.truncateC.grid(row=rowCount, column=1)
        self.truncateL.bind("<Enter>", partial(self.on_enter, "Will end the trial onces the animal reaches the goal location."))
        self.truncateL.bind("<Leave>", self.on_leave)

        useManualForAllFlag = useManualForAll.get()
        useEntropyFlag = useEntropy.get()
        manualFlag = useManual.get()  # get the value of the tickbox
        trunacteFlag = truncate.get()
        rowCount = rowCount+1
        self.calculateButton = Button(self.paramFrame, text="Calculate", fg="black",
                                      command=self.mainHelper)  # add a button that says calculate
        self.calculateButton.grid(row=rowCount, column=1, columnspan=1)
        self.settingsButton = Button(self.paramFrame, text="Settings", command=self.settings, fg="black")
        self.settingsButton.grid(row=rowCount, column=0, columnspan=1)  # add custom button
        self.calculateButton.config(width = 10)
        self.settingsButton.config(width = 10)

        if _platform == "darwin":
            root.bind('<Command-d>', self.ctrlDir)
            root.bind('<Command-f>', self.ctrlFile)
        else:
            root.bind('<Control-d>', self.ctrlDir)
            root.bind('<Control-f>', self.ctrlFile)

        root.bind('<Shift-Return>', self.enterManual)

    def onFrameConfigure(self, canvas):  # configure the frame
        canvas.configure(scrollregion=canvas.bbox("all"))

    def openFile(self):  # opens a dialog to get a single file
        logging.debug("Open File...")
        global theFile
        global fileDirectory
        global fileFlag
        fileFlag = 1
        fileDirectory = ""
        theFile = filedialog.askopenfilename()  # look for xlsx and xls files

    def openDir(self):  # open dialog to get multiple files
        logging.debug("Open Dir...")
        global fileDirectory
        global theFile
        global fileFlag
        fileFlag = 0
        theFile = ""
        fileDirectory = filedialog.askdirectory(mustexist=TRUE)

    def generateHeatmap(self, root):
        global softwareStringVar
        global fileDirectory
        global theFile
        software = softwareStringVar.get()

        experiment = saveFileAsExperiment(software, theFile, fileDirectory)
        self.guiHeatmap(experiment)

    def on_enter(self, text, event):
        global oldStatus
        oldStatus=theStatus.get()
        theStatus.set(text)

    def on_leave(self, enter):
        global oldStatus
        theStatus.set(oldStatus)

    def maximize(self):  # maximize the window
        logging.debug("Window maximized")
        root.attributes('-fullscreen', True)

    def minimize(self):  # minimize the window
        logging.debug("Window minimized")
        root.attributes('-fullscreen', False)

    def about(self):  # go to README
        logging.debug("Called about")
        webbrowser.open('https://github.com/MatthewBCooke/Pathfinder')

    def getHelp(self):  # go to readme
        logging.debug("Called help")
        webbrowser.open('https://github.com/MatthewBCooke/Pathfinder/wiki')

    def tryQuit(self):  # tries to stop threads
        logging.debug("trying to quit")
        try:
            t1.join()
            t2.join()
            print("success")
        except:
            root.destroy()
            return

        root.destroy()

    def enterManual(self, event):  # called when shift enter is pressed in the GUI
        self.mainHelper()

    def ctrlDir(self, event):  # called when CTRL D is pressed
        self.openDir()

    def ctrlFile(self, event):
        self.openFile()

    def select1(self, event):
        self.directRadio.select()

    def select2(self, event):
        self.focalRadio.select()

    def select3(self, event):
        self.directedRadio.select()

    def select4(self, event):
        self.spatialRadio.select()

    def select5(self, event):
        self.chainingRadio.select()

    def select6(self, event):
        self.scanningRadio.select()

    def select7(self, event):
        self.randomRadio.select()

    def select8(self, event):
        self.thigmoRadio.select()

    def select9(self, event):
        self.notRecognizedRadio.select()

    def enterSave(self, event):
        self.saveStrat()

    def mainHelper(self):  # function that checks for the manual flag and runs the program
        global manualFlag
        global useManualForAllFlag
        global useEntropyFlag
        global truncateFlag
        manualFlag = useManual.get()
        useManualForAllFlag = useManualForAll.get()
        useEntropyFlag = useEntropy.get()
        truncateFlag = truncate.get()
        goalPosVar = goalPosStringVar.get()
        goalDiamVar = goalDiamStringVar.get()
        mazeDiamVar = mazeDiamStringVar.get()
        mazeCentreVar = mazeCentreStringVar.get()
        corridorWidthVar = corridorWidthStringVar.get()
        chainingRadiusVar = chainingRadiusStringVar.get()
        thigmotaxisZoneSizeVar = thigmotaxisZoneSizeStringVar.get()  # get important values
        softwareScalingFactorVar = softwareScalingFactorStringVar.get()

        try:
            with open('mainobjs.pickle', 'wb') as f:
                pickle.dump([goalPosVar, goalDiamVar, mazeDiamVar, mazeCentreVar, corridorWidthVar, chainingRadiusVar, thigmotaxisZoneSizeVar, softwareScalingFactorVar], f)
        except:
            pass

        self.mainCalculate(goalPosVar,goalDiamVar)

        for roi in rois:
            print("Running for ROI: " + roi[0])
            self.mainCalculate(roi[0],roi[1])


    def otherROI(self):
        logging.debug("Opening ROI menu")
        self.entries = []
        number = 0
        self.top4 = Toplevel(root)  # we set this to be the top
        self.canvas = Canvas(self.top4, width=500, height=200)
        self.vsb = Scrollbar(self.top4, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(bg="white", yscrollcommand=self.vsb.set)
        self.add_button = Button(self.top4, text="Add Goal", command=self.addROI)
        self.saveButton = Button(self.top4, text="Save", command=self.saveROI)
        self.saveButton.config(width = 10)
        self.add_button.config(width = 10)
        self.container = Frame(self.top4)
        self.canvas.create_window(0,0,anchor="nw",window=self.container)
        Label(self.top4, text="Settings", bg="white", fg="red").pack(side="top") # we title it
        self.add_button.pack(side="top")
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.saveButton.pack(side="bottom")

    def addROI(self):
        labelText = "ROI #" + str(int((len(self.entries))/2+2))
        label = Label(self.container,text=labelText)
        label.grid(row=int(((len(self.entries))/2)),column=0)
        entry1 = EntryWithPlaceholder(self.container, "Location (x,y)")
        entry1.grid(row=int(((len(self.entries))/2)),column=1)
        entry2 = EntryWithPlaceholder(self.container, "Diameter (cm)")
        entry2.grid(row=int(((len(self.entries))/2)),column=2)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.entries.append(entry1)
        self.entries.append(entry2)

    def saveROI(self):
        roiError = False
        roiList = []
        sizeList = []
        try:
            rois.clear()
            sizeList.clear()
            roiList.clear()
        except:
            pass

        count = 0
        for entry in self.entries:
            if count % 2 == 0:
                roiList.append(entry.get())
            else:
                sizeList.append(entry.get())
            count = count + 1

        tempRois = zip(roiList,sizeList)

        patternROI = re.compile("^[0-9]{1,9}([.][0-9]{1,9}){0,1}[,][0-9]{1,9}([.][0-9]{1,9}){0,1}$")
        patternSize = re.compile("^[0-9]{1,9}([.][0-9]{1,9}){0,1}$")

        for aTuple in tempRois:
            if aTuple[0] == 'Location (x,y)' or aTuple[1] == 'Diameter (cm)':
                continue
            if patternROI.match(aTuple[0]) == None:
                messagebox.showwarning('Input Error',
                                   'Please verify your ROI input')
                rois.clear()
                roiError = True
            elif patternSize.match(aTuple[1]) == None:
                messagebox.showwarning('Input Error',
                                   'Please verify your size input')
                rois.clear()
                roiError = True
            else:
                rois.append(aTuple)

        for aTuple in rois:
            print("Goal set at " + aTuple[0] + " and size set at " + aTuple[1])
        if roiError == False:
            try:
                self.top4.destroy()
            except:
                pass

    def settings(self):
        logging.debug("Getting custom values")

        global useDirectPathV
        global useFocalSearchV
        global useDirectedSearchV
        global useScanningV
        global useChainingV
        global useRandomV
        global useIndirectV
        global useThigmoV

        self.useDirectPath = BooleanVar()
        self.useFocalSearch = BooleanVar()
        self.useDirectedSearch = BooleanVar()
        self.useScanning = BooleanVar()
        self.useChaining = BooleanVar()
        self.useRandom = BooleanVar()
        self.useIndirect = BooleanVar()
        self.useThigmo = BooleanVar()

        self.jslsMaxCustom = StringVar()
        self.headingErrorCustom = StringVar()
        self.distanceToSwimCustom = StringVar()
        self.distanceToPlatCustom = StringVar()
        self.corridorAverageCustom = StringVar()
        self.corridorJslsCustom = StringVar()
        self.annulusCustom = StringVar()
        self.quadrantTotalCustom = StringVar()
        self.percentTraversedCustom = StringVar()
        self.percentTraversedMinCustom = StringVar()
        self.distanceToCentreCustom = StringVar()
        self.innerWallCustom = StringVar()
        self.outerWallCustom = StringVar()
        self.jslsIndirectCustom = StringVar()
        self.percentTraversedRandomCustom = StringVar()
        self.directedSearchMaxDistanceCustom = StringVar()
        self.focalMinDistanceCustom = StringVar()
        self.focalMaxDistanceCustom = StringVar()
        self.chainingMaxCoverageCustom = StringVar()
        self.thigmoMinDistanceCustom = StringVar()
        self.headingIndirectCustom = StringVar()

        try:
            with open('customobjs.pickle', 'rb') as f:
                ipeMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, corridorAverageMinVal, directedSearchMaxDistance, focalMinDistance, focalMaxDistance, corridoripeMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, chainingMaxCoverage, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, thigmoMinDistance, innerWallMaxVal, outerWallMaxVal, ipeIndirectMaxVal, percentTraversedRandomMaxVal, headingIndirectMaxVal, useDirectPathV, useFocalSearchV, useDirectedSearchV, useScanningV, useChainingV, useRandomV, useIndirectV, useThigmoV = pickle.load(f)
                self.useDirectPath.set(useDirectPathV)
                self.useFocalSearch.set(useFocalSearchV)
                self.useDirectedSearch.set(useDirectedSearchV)
                self.useScanning.set(useScanningV)
                self.useChaining.set(useChainingV)
                self.useRandom.set(useRandomV)
                self.useIndirect.set(useIndirectV)
                self.useThigmo.set(useThigmoV)

        except:
            params = defaultParams
            ipeMaxVal = params.ipeMaxVal
            headingMaxVal = params.headingMaxVal
            distanceToSwimMaxVal = params.distanceToSwimMaxVal
            distanceToPlatMaxVal = params.distanceToPlatMaxVal
            corridorAverageMinVal = params.corridorAverageMinVal
            corridoripeMaxVal = params.corridoripeMaxVal
            annulusCounterMaxVal = params.annulusCounterMaxVal
            quadrantTotalMaxVal = params.quadrantTotalMaxVal
            percentTraversedMaxVal = params.percentTraversedMaxVal
            percentTraversedMinVal = params.percentTraversedMinVal
            distanceToCentreMaxVal = params.distanceToCentreMaxVal
            innerWallMaxVal = params.innerWallMaxVal
            outerWallMaxVal = params.outerWallMaxVal
            ipeIndirectMaxVal = params.ipeIndirectMaxVal
            percentTraversedRandomMaxVal = params.percentTraversedRandomMaxVal
            directedSearchMaxDistance = params.directedSearchMaxDistance
            focalMinDistance = params.focalMinDistance
            focalMaxDistance = params.focalMaxDistance
            chainingMaxCoverage = params.chainingMaxCoverage
            thigmoMinDistance = params.thigmoMinDistance
            headingIndirectMaxVal = params.headingIndirectMaxVal

            self.useDirectPath.set(True)
            self.useFocalSearch.set(True)
            self.useDirectedSearch.set(True)
            self.useScanning.set(True)
            self.useChaining.set(True)
            self.useRandom.set(True)
            self.useIndirect.set(True)
            self.useThigmo.set(True)



        self.jslsMaxCustom.set(ipeMaxVal)
        self.headingErrorCustom.set(headingMaxVal)
        self.distanceToSwimCustom.set(distanceToSwimMaxVal * 100)
        self.distanceToPlatCustom.set(distanceToPlatMaxVal * 100)
        self.corridorAverageCustom.set(corridorAverageMinVal * 100)
        self.corridorJslsCustom.set(corridoripeMaxVal)
        self.annulusCustom.set(annulusCounterMaxVal * 100)
        self.quadrantTotalCustom.set(quadrantTotalMaxVal)
        self.percentTraversedCustom.set(percentTraversedMaxVal)
        self.percentTraversedMinCustom.set(percentTraversedMinVal)
        self.distanceToCentreCustom.set(distanceToCentreMaxVal * 100)
        self.innerWallCustom.set(innerWallMaxVal * 100)
        self.outerWallCustom.set(outerWallMaxVal * 100)
        self.jslsIndirectCustom.set(ipeIndirectMaxVal)
        self.percentTraversedRandomCustom.set(percentTraversedRandomMaxVal)
        self.directedSearchMaxDistanceCustom.set(directedSearchMaxDistance)
        self.focalMinDistanceCustom.set(focalMinDistance)
        self.focalMaxDistanceCustom.set(focalMaxDistance)
        self.chainingMaxCoverageCustom.set(chainingMaxCoverage)
        self.thigmoMinDistanceCustom.set(thigmoMinDistance)
        self.headingIndirectCustom.set(headingIndirectMaxVal)
        # all of the above is the same as in snyder, plus the creation of variables to hold values from the custom menu

        self.top = Toplevel(root)  # we set this to be the top
        self.top.configure(bg="white")
        Label(self.top, text="Settings", bg="white", fg="red").grid(row=0, column=0, columnspan=2)  # we title it

        rowCount = 1

        useDirectPathL = Label(self.top, text="Direct Path: ", bg="white")  # we add a direct path label
        useDirectPathL.grid(row=rowCount, column=0, sticky=E)  # stick it to row 1
        useDirectPathC = Checkbutton(self.top, variable=self.useDirectPath, bg="white")  # we add a direct path checkbox
        useDirectPathC.grid(row=rowCount, column=1)  # put it beside the label

        rowCount+=1

        jslsMaxCustomL = Label(self.top, text="Ideal Path Error [maximum]: ", bg="white")  # label for JSLs
        jslsMaxCustomL.grid(row=rowCount, column=0, sticky=E)  # row 2
        jslsMaxCustomE = Entry(self.top, textvariable=self.jslsMaxCustom)  # entry field
        jslsMaxCustomE.grid(row=rowCount, column=1)  # right beside

        rowCount+=1

        headingErrorCustomL = Label(self.top, text="Heading error [maximum, degrees]: ", bg="white")
        headingErrorCustomL.grid(row=rowCount, column=0, sticky=E)
        headingErrorCustomE = Entry(self.top, textvariable=self.headingErrorCustom)
        headingErrorCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useFocalSearchL = Label(self.top, text="Focal Search: ", bg="white")
        useFocalSearchL.grid(row=rowCount, column=0, sticky=E)
        useFocalSearchC = Checkbutton(self.top, variable=self.useFocalSearch, bg="white")
        useFocalSearchC.grid(row=rowCount, column=1)

        rowCount+=1

        distanceToSwimCustomL = Label(self.top, text="Distance to swim path centroid [maximum, % of radius]: ", bg="white")
        distanceToSwimCustomL.grid(row=rowCount, column=0, sticky=E)
        distanceToSwimCustomE = Entry(self.top, textvariable=self.distanceToSwimCustom)
        distanceToSwimCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        distanceToPlatCustomL = Label(self.top, text="Distance to goal [maximum, % of radius]: ", bg="white")
        distanceToPlatCustomL.grid(row=rowCount, column=0, sticky=E)
        distanceToPlatCustomE = Entry(self.top, textvariable=self.distanceToPlatCustom)
        distanceToPlatCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        focalMinDistanceCustomL = Label(self.top, text="Distance covered (minimum, cm): ", bg="white")
        focalMinDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        focalMinDistanceCustomE = Entry(self.top, textvariable=self.focalMinDistanceCustom)
        focalMinDistanceCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        focalMaxDistanceCustomL = Label(self.top, text="Distance covered (maximum, cm): ", bg="white")
        focalMaxDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        focalMaxDistanceCustomE = Entry(self.top, textvariable=self.focalMaxDistanceCustom)
        focalMaxDistanceCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useDirectedSearchL = Label(self.top, text="Directed Search: ", bg="white")
        useDirectedSearchL.grid(row=rowCount, column=0, sticky=E)
        useDirectedSearchC = Checkbutton(self.top, variable=self.useDirectedSearch, bg="white", onvalue=1)
        useDirectedSearchC.grid(row=rowCount, column=1)

        rowCount+=1

        corridorAverageCustomL = Label(self.top, text="Time in angular corridor [minimum, % of trial]: ", bg="white")
        corridorAverageCustomL.grid(row=rowCount, column=0, sticky=E)
        corridorAverageCustomE = Entry(self.top, textvariable=self.corridorAverageCustom)
        corridorAverageCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        directedSearchMaxDistanceCustomL = Label(self.top, text="Distance covered (maximum, cm): ", bg="white")
        directedSearchMaxDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        directedSearchMaxDistanceCustomE = Entry(self.top, textvariable=self.directedSearchMaxDistanceCustom)
        directedSearchMaxDistanceCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        corridorJslsCustomL = Label(self.top, text="Ideal Path Error [maximum]: ", bg="white")
        corridorJslsCustomL.grid(row=rowCount, column=0, sticky=E)
        corridorJslsCustomE = Entry(self.top, textvariable=self.corridorJslsCustom)
        corridorJslsCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useIndirectL = Label(self.top, text="Indirect Search: ", bg="white")
        useIndirectL.grid(row=rowCount, column=0, sticky=E)
        useIndirectC = Checkbutton(self.top, variable=self.useIndirect, bg="white")
        useIndirectC.grid(row=rowCount, column=1)

        rowCount+=1

        jslsIndirectCustomL = Label(self.top, text="Ideal Path Error [maximum]: ", bg="white")
        jslsIndirectCustomL.grid(row=rowCount, column=0, sticky=E)
        jslsIndirectCustomE = Entry(self.top, textvariable=self.jslsIndirectCustom)
        jslsIndirectCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        headingIndirectCustomL = Label(self.top, text="Heading error [maximum]: ", bg="white")
        headingIndirectCustomL.grid(row=rowCount, column=0, sticky=E)
        headingIndirectCustomE = Entry(self.top, textvariable=self.headingIndirectCustom, bg="white")
        headingIndirectCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useChainingL = Label(self.top, text="Chaining: ", bg="white")
        useChainingL.grid(row=rowCount, column=0, sticky=E)
        useChainingC = Checkbutton(self.top, variable=self.useChaining, bg="white")
        useChainingC.grid(row=rowCount, column=1)

        rowCount+=1

        annulusCustomL = Label(self.top, text="Time in annulus zone [minimum, % of trial]: ", bg="white")
        annulusCustomL.grid(row=rowCount, column=0, sticky=E)
        annulusCustomE = Entry(self.top, textvariable=self.annulusCustom)
        annulusCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        quadrantTotalCustomL = Label(self.top, text="Quadrants visited [minimum]: ", bg="white")
        quadrantTotalCustomL.grid(row=rowCount, column=0, sticky=E)
        quadrantTotalCustomE = Entry(self.top, textvariable=self.quadrantTotalCustom)
        quadrantTotalCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        chainingMaxCoverageCustomL = Label(self.top, text="Area of maze traversed (maximum, % of maze): ", bg="white")
        chainingMaxCoverageCustomL.grid(row=rowCount, column=0, sticky=E)
        chainingMaxCoverageCustomE = Entry(self.top, textvariable=self.chainingMaxCoverageCustom)
        chainingMaxCoverageCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useScanningL = Label(self.top, text="Scanning: ", bg="white")
        useScanningL.grid(row=rowCount, column=0, sticky=E)
        useScanningC = Checkbutton(self.top, variable=self.useScanning, bg="white")
        useScanningC.grid(row=rowCount, column=1)

        rowCount+=1

        percentTraversedCustomL = Label(self.top, text="Area of maze traversed [maximum, % of maze]: ", bg="white")
        percentTraversedCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedCustomE = Entry(self.top, textvariable=self.percentTraversedCustom)
        percentTraversedCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        percentTraversedMinCustomL = Label(self.top, text="Area of maze traversed [minimum, % of maze]: ", bg="white")
        percentTraversedMinCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedMinCustomE = Entry(self.top, textvariable=self.percentTraversedMinCustom)
        percentTraversedMinCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        distanceToCentreCustomL = Label(self.top, text="Average distance to maze centre [maximum, % of radius]: ", bg="white")
        distanceToCentreCustomL.grid(row=rowCount, column=0, sticky=E)
        distanceToCentreCustomE = Entry(self.top, textvariable=self.distanceToCentreCustom)
        distanceToCentreCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useThigmoL = Label(self.top, text="Thigmotaxis: ", bg="white")
        useThigmoL.grid(row=rowCount, column=0, sticky=E)
        useThigmoC = Checkbutton(self.top, variable=self.useThigmo, bg="white")
        useThigmoC.grid(row=rowCount, column=1)

        rowCount+=1

        innerWallCustomL = Label(self.top, text="Time in larger thigmotaxis zone [minimum, % of trial]: ", bg="white")
        innerWallCustomL.grid(row=rowCount, column=0, sticky=E)
        innerWallCustomE = Entry(self.top, textvariable=self.innerWallCustom)
        innerWallCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        outerWallCustomL = Label(self.top, text="Time in smaller thigmotaxis zone [minimum, % of trial]: ", bg="white")
        outerWallCustomL.grid(row=rowCount, column=0, sticky=E)
        outerWallCustomE = Entry(self.top, textvariable=self.outerWallCustom, bg="white")
        outerWallCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        thigmoMinDistanceCustomL = Label(self.top, text="Total distance covered (minimum, cm): ", bg="white")
        thigmoMinDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        thigmoMinDistanceCustomE = Entry(self.top, textvariable=self.thigmoMinDistanceCustom, bg="white")
        thigmoMinDistanceCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useRandomL = Label(self.top, text="Random Search: ", bg="white")
        useRandomL.grid(row=rowCount, column=0, sticky=E)
        useRandomC = Checkbutton(self.top, variable=self.useRandom, bg="white")
        useRandomC.grid(row=rowCount, column=1)

        rowCount+=1

        percentTraversedRandomCustomL = Label(self.top, text="Area of maze traversed [minimum, % of maze]: ", bg="white")
        percentTraversedRandomCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedRandomCustomE = Entry(self.top, textvariable=self.percentTraversedRandomCustom)
        percentTraversedRandomCustomE.grid(row=rowCount, column=1)

        # we save the values from the fields and scale them appropriately

        rowCount+=1

        Button(self.top, text="Save", command=self.saveCuston).grid(row=rowCount, column=0, columnspan=2)  # button to save
        rowCount+=1
        Button(self.top, text="Reset", command=self.resetCustom).grid(row=rowCount, column=0, columnspan=2)  # button to save

    def saveCuston(self):  # save the custom values
        logging.debug("Saving custom parameters")
        global useDirectPath
        global useFocalSearch
        global useDirectedSearch
        global useScanning
        global useChaining
        global useRandom
        global useIndirect
        global useThigmo

        global useDirectPathV
        global useFocalSearchV
        global useDirectedSearchV
        global useScanningV
        global useChainingV
        global useRandomV
        global useIndirectV
        global useThigmoV

        ipeMaxVal = float(self.jslsMaxCustom.get())
        headingMaxVal = float(self.headingErrorCustom.get())
        distanceToSwimMaxVal = float(self.distanceToSwimCustom.get())/100
        distanceToPlatMaxVal = float(self.distanceToPlatCustom.get())/100
        corridorAverageMinVal = float(self.corridorAverageCustom.get()) / 100
        corridoripeMaxVal = float(self.corridorJslsCustom.get())
        annulusCounterMaxVal = float(self.annulusCustom.get())/100
        quadrantTotalMaxVal = float(self.quadrantTotalCustom.get())
        percentTraversedMaxVal = float(self.percentTraversedCustom.get())
        percentTraversedMinVal = float(self.percentTraversedMinCustom.get())
        distanceToCentreMaxVal = float(self.distanceToCentreCustom.get())/100
        innerWallMaxVal = float(self.innerWallCustom.get())/100
        outerWallMaxVal = float(self.outerWallCustom.get())/100
        ipeIndirectMaxVal = float(self.jslsIndirectCustom.get())
        percentTraversedRandomMaxVal = float(self.percentTraversedRandomCustom.get())
        directedSearchMaxDistance = float(self.directedSearchMaxDistanceCustom.get())
        focalMinDistance = float(self.focalMinDistanceCustom.get())
        focalMaxDistance = float(self.focalMaxDistanceCustom.get())
        chainingMaxCoverage = float(self.chainingMaxCoverageCustom.get())
        thigmoMinDistance = float(self.thigmoMinDistanceCustom.get())
        headingIndirectMaxVal = float(self.headingIndirectCustom.get())

        params = Parameters(name="Custom", ipeMaxVal=float(self.jslsMaxCustom.get()), headingMaxVal=float(self.headingErrorCustom.get()), distanceToSwimMaxVal=float(self.distanceToSwimCustom.get())/100,
                            distanceToPlatMaxVal=float(self.distanceToPlatCustom.get())/100, corridorAverageMinVal=float(self.corridorAverageCustom.get()) / 100, directedSearchMaxDistance=float(self.directedSearchMaxDistanceCustom.get()), focalMinDistance=float(self.focalMinDistanceCustom.get()), focalMaxDistance=float(self.focalMaxDistanceCustom.get()), corridoripeMaxVal=float(self.corridorJslsCustom.get()),
                            annulusCounterMaxVal=float(self.annulusCustom.get())/100, quadrantTotalMaxVal=float(self.quadrantTotalCustom.get()), chainingMaxCoverage=float(self.chainingMaxCoverageCustom.get()), percentTraversedMaxVal=float(self.percentTraversedCustom.get()),
                            percentTraversedMinVal=float(self.percentTraversedMinCustom.get()), distanceToCentreMaxVal=float(self.distanceToCentreCustom.get())/100, thigmoMinDistance = float(self.thigmoMinDistanceCustom.get()), innerWallMaxVal=float(self.innerWallCustom.get())/100,
                            outerWallMaxVal=float(self.outerWallCustom.get())/100, ipeIndirectMaxVal=float(self.jslsIndirectCustom.get()), percentTraversedRandomMaxVal=float(self.percentTraversedRandomCustom.get(), headingIndirectMaxVal=float(self.headingIndirectCustom.get())))

        useDirectPathV = self.useDirectPath.get()
        useFocalSearchV = self.useFocalSearch.get()
        useDirectedSearchV = self.useDirectedSearch.get()
        useScanningV = self.useScanning.get()
        useChainingV = self.useChaining.get()
        useRandomV = self.useRandom.get()
        useIndirectV = self.useIndirect.get()
        useThigmoV = self.useThigmo.get()
        try:
            with open('customobjs.pickle', 'wb') as f:
                pickle.dump([ipeMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, corridorAverageMinVal, directedSearchMaxDistance, focalMinDistance, focalMaxDistance, corridoripeMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, chainingMaxCoverage, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, thigmoMinDistance, innerWallMaxVal, outerWallMaxVal, ipeIndirectMaxVal, percentTraversedRandomMaxVal, headingIndirectMaxVal, useDirectPathV, useFocalSearchV, useDirectedSearchV, useScanningV, useChainingV, useRandomV, useIndirectV, useThigmoV], f)
        except:
            pass
        try:
            self.top.destroy()
        except:
            pass

    def resetCustom(self):
        result = messagebox.askquestion("Reset", "Are You Sure?", icon='warning')
        if result == 'yes':
            logging.debug("Resetting custom parameters")
            params = defaultParams
            useDirectPathV = True
            useFocalSearchV = True
            useDirectedSearchV = True
            useScanningV = True
            useChainingV = True
            useRandomV = True
            useIndirectV = True
            useThigmoV = True
            try:
                with open('customobjs.pickle', 'wb') as f:
                    pickle.dump([params.ipeMaxVal, params.headingMaxVal, params.distanceToSwimMaxVal, params.distanceToPlatMaxVal, params.corridorAverageMinVal, params.directedSearchMaxDistance, params.focalMinDistance, params.focalMaxDistance, params.corridoripeMaxVal, params.annulusCounterMaxVal, params.quadrantTotalMaxVal, params.chainingMaxCoverage, params.percentTraversedMaxVal, params.percentTraversedMinVal, params.distanceToCentreMaxVal, params.thigmoMinDistance, params.innerWallMaxVal, params.outerWallMaxVal, params.ipeIndirectMaxVal, params.percentTraversedRandomMaxVal, params.headingIndirectMaxVal, useDirectPathV, useFocalSearchV, useDirectedSearchV, useScanningV, useChainingV, useRandomV, useIndirectV, useThigmoV], f)
            except:
                pass
            try:
                self.top.destroy()
            except:
                pass

    def find_files(self, directory, pattern):  # searches for our files in the directory
        logging.debug("Finding files in the directory")
        for root, dirs, files in os.walk(directory):
            for basename in sorted(files):
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename

    def plotPoints(self, x, y, mazeDiam, centreX, centreY, platX, platY, scalingFactor, name, title, platEstDiam):  # function to graph the data for the not recognized trials
        wallsX = []
        wallsY = []
        platWallsX = []
        platWallsY = []
        for theta in range(0,360):
            wallsX.append(centreX + ((math.ceil(mazeDiam) / 2)) * math.cos(math.radians(theta)))
            wallsY.append(centreY + ((math.ceil(mazeDiam) / 2)) * math.sin(math.radians(theta)))

        for theta in range(0,360):
            platWallsX.append(platX + ((math.ceil(platEstDiam) / 2)+1) * math.cos(math.radians(theta)))
            platWallsY.append(platY + ((math.ceil(platEstDiam) / 2)+1) * math.sin(math.radians(theta)))

        plotName = "output/plots/" + name + " " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # the name will be Animal id followed by the date and time
        plt.scatter(x, y, s=15, c='r', alpha=1.0)  # we plot the XY position of animal
        plt.scatter(x[0],y[0], s=100, c='b', alpha=1, marker='s')  # we plot the start point
        plt.scatter(platWallsX, platWallsY, s=1, c='black', alpha=1.0)  # we plot the goal
        plt.scatter(centreX, centreY, s=100, c='g', alpha=1.0)  # we plot the centre
        plt.scatter(wallsX, wallsY, s=15, c='black', alpha=0.3)
        plt.title(title)  # add the title
        plt.xlim(centreX-mazeDiam/2-15, centreX+mazeDiam/2+15)  # set the size to be the center + radius + 30
        plt.ylim(centreY-mazeDiam/2-15, centreY+mazeDiam/2+15)

        try:
            plt.gca().set_aspect('equal')
        except:
            pass
        photoName = plotName + ".png"  # image name the same as plotname
        plt.savefig(photoName, dpi=100, figsize=(2,2))  # save the file
        plt.clf()  # clear the plot

        image = PIL.Image.open(photoName)  # open the saved image
        photo = ImageTk.PhotoImage(image)  # convert it to something the GUI can read
        global searchStrategyV
        global searchStrategyStringVar

        searchStrategyStringVar = StringVar()  # temporary variable for the selection of strategies
        searchStrategyStringVar.set("Not Recognized")

        self.top2 = Toplevel(root)  # create a new toplevel window
        self.top2.configure(bg="white")

        Label(self.top2, text=name, bg="white", fg="black", width=40).grid(row=0, column=0, columnspan = 7)  # add a title
        photoimg = Label(self.top2, image=photo)  # add the photo
        photoimg.image = photo  # keep a reference
        photoimg.grid(row=1, column=0, columnspan=7)  # place the photo in the window

        Label(self.top2, text="Start position", bg="blue", fg="white", width=15).grid(row=2, column=1, padx=3)
        Label(self.top2, text="Goal and Walls", bg="black", fg="white", width=15).grid(row=2, column=2, padx=3)
        Label(self.top2, text="Maze centre", bg="green", fg="white", width=15).grid(row=2, column=3, padx=3)
        Label(self.top2, text="Path", bg="red", fg="white", width=15).grid(row=2, column=4, padx=3)

        self.directRadio = Radiobutton(self.top2, text="(1) Direct Path", variable=searchStrategyStringVar, value="Direct path",
                                       indicatoron=0, width=15, bg="white")
        self.directRadio.grid(row=3, column=0, columnspan = 7, pady=3)  # add the radiobuttons for selection

        self.focalRadio = Radiobutton(self.top2, text="(2) Focal Search", variable=searchStrategyStringVar, value="Focal Search",
                                      indicatoron=0, width=15, bg="white")
        self.focalRadio.grid(row=4, column=0, columnspan = 7, pady=3)
        self.directedRadio = Radiobutton(self.top2, text="(3) Directed Search", variable=searchStrategyStringVar,
                                         value="Directed Search (m)", indicatoron=0, width=15, bg="white")
        self.directedRadio.grid(row=5, column=0, columnspan = 7, pady=3)
        self.spatialRadio = Radiobutton(self.top2, text="(4) Indirect Search", variable=searchStrategyStringVar,
                                        value="Indirect Search", indicatoron=0, width=15, bg="white")
        self.spatialRadio.grid(row=6, column=0, columnspan = 7, pady=3)
        self.chainingRadio = Radiobutton(self.top2, text="(5) Chaining", variable=searchStrategyStringVar, value="Chaining",
                                         indicatoron=0, width=15, bg="white")
        self.chainingRadio.grid(row=7, column=0, columnspan = 7, pady=3)
        self.scanningRadio = Radiobutton(self.top2, text="(6) Scanning", variable=searchStrategyStringVar, value="Scanning",
                                         indicatoron=0, width=15, bg="white")
        self.scanningRadio.grid(row=8, column=0, columnspan = 7, pady=3)
        self.randomRadio = Radiobutton(self.top2, text="(7) Random Search", variable=searchStrategyStringVar, value="Random Search",
                                       indicatoron=0, width=15, bg="white")
        self.randomRadio.grid(row=9, column=0, columnspan = 7, pady=3)
        self.thigmoRadio = Radiobutton(self.top2, text="(8) Thigmotaxis", variable=searchStrategyStringVar, value="Thigmotaxis",
                                       indicatoron=0, width=15, bg="white")
        self.thigmoRadio.grid(row=10, column=0, columnspan=7, pady=3)
        self.notRecognizedRadio = Radiobutton(self.top2, text="(9) Not Recognized", variable=searchStrategyStringVar, value="Not Recognized",
                                              indicatoron=0, width=15, bg="white")
        self.notRecognizedRadio.grid(row=11, column=0, columnspan = 7, pady=3)

        Button(self.top2, text="(Return) Save", command=self.saveStrat, fg="black", bg="white", width=15).grid(row=12,
                                                                                                               column=0,
                                                                                                               columnspan=7,
                                                                                                               pady=5)  # save button not mac

        self.top2.bind('1', self.select1)
        self.top2.bind('2', self.select2)
        self.top2.bind('3', self.select3)
        self.top2.bind('4', self.select4)
        self.top2.bind('5', self.select5)
        self.top2.bind('6', self.select6)
        self.top2.bind('7', self.select7)
        self.top2.bind('8', self.select8)
        self.top2.bind('9', self.select9)



        self.top2.bind('<Return>', self.enterSave)

        self.top2.focus_force()  # once built, show the window in front



        searchStrategyV = searchStrategyStringVar.get()  # get the solution

        logging.info("Plotted " + plotName)

    def saveStrat(self):  # save the manual strategy
        global searchStrategyV
        global searchStrategyStringVar

        searchStrategyV = searchStrategyStringVar.get()  # get the value to be saved
        try:  # try and destroy the window
            self.top2.destroy()
        except:
            pass

    def guiHeatmap(self, aExperiment):

        self.top3 = Toplevel(root)  # create a new toplevel window
        self.top3.configure(bg="white")
        self.top3.geometry('{}x{}'.format( 500, 500 ))
        Label(self.top3, text="Heatmap Parameters", bg="white", fg="black", width=15).pack()  # add a title

        self.gridSizeL = Label(self.top3, text="Grid Size:", bg="white")
        self.gridSizeL.pack(side=TOP)
        self.gridSizeE = Entry(self.top3, textvariable=gridSizeStringVar)
        self.gridSizeE.pack(side=TOP)

        self.maxValL = Label(self.top3, text="Maximum Value:", bg="white")
        self.maxValL.pack(side=TOP)
        self.maxValE = Entry(self.top3, textvariable=maxValStringVar)
        self.maxValE.pack(side=TOP)

        self.dayValL = Label(self.top3, text="Day(s) to consider:", bg="white")
        self.dayValL.pack(side=TOP)
        self.dayValE = Entry(self.top3, textvariable=dayValStringVar)
        self.dayValE.pack(side=TOP)

        self.trialValL = Label(self.top3, text="Trial(s) to consider:", bg="white")
        self.trialValL.pack(side=TOP)
        self.trialValE = Entry(self.top3, textvariable=trialValStringVar)
        self.trialValE.pack(side=TOP)

        Button(self.top3, text="Generate", command=lambda: self.heatmap(aExperiment), fg="black", bg="white").pack()


    def heatmap(self, aExperiment):
        logging.debug("Heatmap Called")
        theStatus.set("Generating Heatmap...")
        self.updateTasks()
        n = 0
        i = 0
        x = []
        y = []
        xMin = 0.0
        yMin = 0.0
        xMax = 0.0
        yMax = 0.0
        dayStartStop = []
        trialStartStop = []
        dayVal = dayValStringVar.get()
        trialVal = trialValStringVar.get()
        dayNum = 0
        trialNum = {}
        curDate = None

        if dayVal == "All" or dayVal == "all" or dayVal == "":
            dayStartStop = [1,float(math.inf)]
        elif "-" in dayVal:
            dayStartStop = dayVal.split("-",1)
            dayStartStop = [int(dayStartStop[0]),int(dayStartStop[1])]
        else:
            dayStartStop = [int(dayVal),int(dayVal)]

        if trialVal == "All" or trialVal == "all" or trialVal == "":
            trialStartStop = [1,float(math.inf)]
        elif "-" in trialVal:
            trialStartStop = trialVal.split("-",1)
            trialStartStop = [int(trialStartStop[0]),int(trialStartStop[1])]
        else:
            trialStartStop = [int(trialVal),int(trialVal)]

        for aTrial in aExperiment:  # for all the files we find
            theStatus.set("Running " + theFile)
            animal = ""
            if aExperiment.hasAnimalNames:
                animal = aTrial.animal.replace("*", "")
            if aExperiment.hasDateInfo and aTrial.date.date() != curDate:
                dayNum += 1
                curDate = aTrial.date.date()
                trialNum = {}
                trialNum[animal] = 1
            elif animal in trialNum:
                trialNum[animal] += 1
            else:
                trialNum[animal] = 1

            for aDatapoint in aTrial:
                # Create data
                if dayNum >= dayStartStop[0] and dayNum <= dayStartStop[1]:
                    if trialNum[animal] >= trialStartStop[0] and trialNum[animal] <= trialStartStop[1]:
                        if aDatapoint.getx() == "-" or aDatapoint.gety() == "-":
                            continue
                        x.append(float(aDatapoint.getx()))
                        y.append(float(aDatapoint.gety()))

                        if aDatapoint.getx() < xMin:
                            xMin = aDatapoint.getx()
                        if aDatapoint.gety() < yMin:
                            yMin = aDatapoint.gety()
                        if aDatapoint.getx() > xMax:
                            xMax = aDatapoint.getx()
                        if aDatapoint.gety() > yMax:
                            yMax = aDatapoint.gety()

        # x = np.zeros(math.ceil(xMax-xMin+1))
        # y = np.zeros(math.ceil(yMax-yMin+1))

        # for aTrial in experiment:  # for all the files we find
        #     for row in aTrial:
        #         # Create data
        #         if row.x == "-" or row.y == "-":
        #             continue
        #         x[math.floor(row.x)] += 1/len(experiment)
        #         y[math.floor(row.y)] += 1/len(experiment)

        aFileName = "output/heatmaps/ " + "Day "+ dayValStringVar.get() + " Trial " + trialValStringVar.get() + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # name of the log file for the run
        aTitle = fileDirectory
        """
        mu = 0
        variance = 0.01
        sigma = math.sqrt(variance)
        x = np.random.normal(mu,sigma,50000)
        y = np.random.normal(mu,sigma,50000)
        """
        try:
            gridSize = int(math.floor(float(gridSizeStringVar.get())))
        except:
            logging.error("Couldn't read grid size for heatmap")
            theStatus.set("Waiting for user input...")
            return

        X = sp.filters.gaussian_filter(x, sigma=2, order=0)
        Y = sp.filters.gaussian_filter(y, sigma=2, order=0)
        heatmap, xedges, yedges = np.histogram2d(X, Y)

        # Plot heatmap
        maxVal = maxValStringVar.get()
        if maxVal == "Auto" or maxVal == "auto" or maxVal == "automatic" or maxVal == "Automatic" or maxVal == "":
            hb = plt.hexbin(X, Y, gridsize=gridSize, cmap=CM.jet, vmin=0, bins=None)
        else:
            try:
                maxVal = int(math.floor(float(maxValStringVar.get())))
                hb = plt.hexbin(X, Y, gridsize=gridSize, cmap=CM.jet, vmin=0, vmax=maxVal, bins=None, linewidths=0.25)
            except:
                logging.error("Couldn't read Max Value")
                theStatus.set("Waiting for user input...")
                return

        try:
            plt.gca().set_aspect('equal')
        except:
            pass
        logging.debug("Heatmap generated")
        theStatus.set("Waiting for user input...")
        self.updateTasks()

        plt.title("Day: " + dayValStringVar.get() + " Trial: "+ trialValStringVar.get())
        cb = plt.colorbar()
        photoName = aFileName + ".png"  # image name the same as plotname
        plt.savefig(photoName, dpi=300, figsize=(4,4))  # save the file
        plt.show()


    def updateTasks(self):  # called when we want to push an update to the GUI
        try:
            root.update_idletasks()
            root.update()  # update the gui
        except:
            logging.info("Couldn't update the GUI")

    def unit_vector(self, vector):
        """ Returns the unit vector of the vector.  """
        if np.linalg.norm(vector) == 0:
            return (0,0)
        try:
           return vector / np.linalg.norm(vector)
        except:
            return (0,0)

    def angle_between(self, v1, v2):
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))

    def calculateEntropy(self, theTrial, goalX, goalY):
        xList = []
        yList = []
        try:
            eng = matlab.engine.start_matlab()
            logging.info("Matlab Engine Started")
        except:
            logging.info("Matlab Engine Running")
        for aDatapoint in theTrial:
            xList.append(float(aDatapoint.getx()))
            yList.append(float(aDatapoint.gety()))

        entropyResult = eng.Entropy(xList,yList,goalX,goalY)
        return entropyResult

    def getAutoLocations(self, theExperiment, goalX, goalY, goalPosVar, mazeCentreX, mazeCentreY, mazeCentreVar, mazeDiamVar, software, goalDiamVar):
        platEstX = 0.0
        platEstY = 0.0
        maxX = 0.0
        minX = 0.0
        maxY = 0.0
        minY = 0.0
        avMaxY = 0.0
        avMinY = 0.0
        avMaxX = 0.0
        avMinX = 0.0
        absMaxX = 0.0
        absMaxY = 0.0
        absMinX = 0.0
        absMinY = 0.0
        mazeCentreEstX = 0.0
        mazeCentreEstY = 0.0
        mazeRadius = 0.0
        count = 0.0
        centreCount = 0.0
        lastX = 0.0
        lastY = 0.0
        platMaxX = -100.0
        platMinX = 100.0
        platMaxY = -100.0
        platMinY = 100.0
        platEstDiam = 0.0
        maxLengthOfTrial = 50.0
        centreFlag = False
        platFlag = False
        platDiamFlag = False
        diamFlag = False
        autoParams = []


        if goalPosVar != "Auto" and goalPosVar != "auto" and goalPosVar != "automatic" and goalPosVar != "Automatic" and goalPosVar != "":  # if we want manual goal
            goalX, goalY = goalPosVar.split(",")
            goalX = float(goalX)
            goalY = float(goalY)
            logging.debug("Goal position set manually: "+str(goalPosVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get goal position from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:  # automatic goal calculation
            platFlag = True
            autoParams.append("goal position")

        if goalDiamVar != "Auto" and goalDiamVar != "auto" and goalDiamVar != "automatic" and goalDiamVar != "Automatic" and goalDiamVar != "":  # if we want manual goal diameter
            platEstDiam = goalDiamVar
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get goal position from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:
            platDiamFlag = True
            autoParams.append("goal diameter")


        if mazeCentreVar != "Auto" and mazeCentreVar != "auto" and mazeCentreVar != "automatic" and mazeCentreVar != "Automatic" and mazeCentreVar != "":  # manual maze center
            mazeCentreX, mazeCentreY = mazeCentreVar.split(",")
            mazeCentreX = float(mazeCentreX)
            mazeCentreY = float(mazeCentreY)
            logging.debug("Maze centre set manually: "+str(mazeCentreVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get maze centre from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:  # automatic maze centre
            centreFlag = True
            autoParams.append("centre position")

        if mazeDiamVar != "Auto" and mazeDiamVar != "auto" and mazeDiamVar != "automatic" and mazeDiamVar != "Automatic" and mazeDiamVar != "":  # manual diameter
            mazeRadius = float(mazeDiamVar) / 2.0
            logging.debug("Maze diameter set manually: " + str(mazeDiamVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Tried to get diameter from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:  # automatic diameter
            diamFlag = True
            autoParams.append("maze diameter")

        if len(autoParams) > 0:  # update the status bar depending on choice
            loggingText = "Getting " + " and ".join(autoParams)
            theStatus.set(loggingText + "...")
            logging.debug(loggingText)
            self.updateTasks()
            for aTrial in theExperiment:
                for aDatapoint in aTrial:
                    if aDatapoint.getx() == "-" or aDatapoint.getx() == "":  # throw out missing data
                        continue
                    if aDatapoint.gety() == "-" or aDatapoint.gety() == "":
                        continue
                    if aDatapoint.gettime() < maxLengthOfTrial:
                        lastX = aDatapoint.getx()
                        lastY = aDatapoint.gety()
                        skipFlag = False
                    else:
                        skipFlag = True

                    if aDatapoint.getx() > maxX:
                        maxX = aDatapoint.getx()
                    if aDatapoint.getx() < minX:
                        minX = aDatapoint.getx()
                    if aDatapoint.gety() > maxY:
                        maxY = aDatapoint.gety()
                    if aDatapoint.gety() < minY:
                        minY = aDatapoint.gety()

                    if maxX > absMaxX:
                        absMaxX = maxX
                    if minX < absMinX:
                        absMinX = minX
                    if maxY > absMaxY:
                        absMaxY = maxY
                    if minY < absMinY:
                        absMinY = minY

                    avMaxX += maxX
                    avMaxY += maxY
                    avMinX += minX
                    avMinY += minY
                    centreCount += 1.0

                    if skipFlag == False:
                        count += 1.0
                        platEstX += lastX
                        platEstY += lastY



            if centreCount < 1:  # we couldnt get the position
                if centreFlag:
                    logging.error("Unable to determine a centre position. Compatible trials: 0" )
                    messagebox.showwarning('Centre Error',
                                           'Unable to determine a centre position. Compatible trials')
                elif centreFlag and diamFlag:
                    logging.error(
                        "Unable to determine a centre position and maze diameter. Compatible trials: 0")
                    messagebox.showwarning('Centre and Diameter Error',
                                           'We were unable to determine a centre position or maze diameter from the trials')
                elif diamFlag:
                    logging.error("Unable to determine the maze diameter. Compatible trials: 0")
                    messagebox.showwarning('Diameter Error',
                                           'We were unable to determine a diameter from the trials')
                theStatus.set('Waiting for user input...')
                self.updateTasks()
                return

        if count < 1 and platFlag:
            logging.error("Unable to determine a goal posititon. Compatible trials: " + str(count))
            messagebox.showwarning('Goal Error',
                                   'We were unable to determine a goal position from the trials')
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            return

        if centreFlag:  # if we want an automatic centre position
            avMaxX = avMaxX / centreCount  # get the average of the max X
            avMaxY = avMaxY / centreCount  # max Y
            avMinX = avMinX / centreCount  # min X
            avMinY = avMinY / centreCount  # min Y
            mazeCentreEstX = (avMaxX + avMinX) / 2  # estmiate the centre
            mazeCentreEstY = (avMaxY + avMinY) / 2
            mazeCentreX = mazeCentreEstX
            mazeCentreY = mazeCentreEstY
            logging.info("Automatic maze centre calculated as: " + str(mazeCentreEstX) + ", " + str(mazeCentreEstY))
            print("Automatic maze centre calculated as: " + str(mazeCentreEstX) + ", " + str(mazeCentreEstY))

        if platFlag:  # automatic goal
            platEstX = platEstX / count
            platEstY = platEstY / count
            goalX = platEstX
            goalY = platEstY
            logging.info("Automatic goal position calculated as: " + str(platEstX) + ", " + str(platEstY))
            print("Automatic goal position calculated as: " + str(platEstX) + ", " + str(platEstY))
        if platDiamFlag:
            platEstDiam = ((platMaxX-platMinX) + (platMaxY-platMinY))/2
            if platEstDiam > 50 or platEstDiam < 1:
                platEstDiam = 10
            logging.info("Automatic goal diameter calculated as: " + str((math.ceil(float(platEstDiam)))))
            print("Automatic goal diameter calculated as: " + str((math.ceil(float(platEstDiam)))))
        if diamFlag:  # automatic diameter
            mazeDiamEst = ((abs(absMaxX) + abs(absMinX)) + (abs(absMaxY) + abs(absMinY))) / 2
            logging.info("Automatic maze diameter calculated as: " + str(mazeDiamEst))
            print("Automatic maze diameter calculated as: " + str(mazeDiamEst))
            mazeDiamVar = mazeDiamEst
            mazeRadius = float(mazeDiamVar) / 2
        return (mazeCentreX,mazeCentreY,goalX,goalY,mazeDiamVar,mazeRadius,platEstDiam)


    def calculateValues(self, theTrial, goalX, goalY, mazeCentreX, mazeCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone, biggerWallZone, scalingFactor, mazeradius, dayNum, goalDiam):
        global mazeCentreVar
        global useEntropyFlag
        global truncateFlag
        theStatus.set("Calculating Search Strategies: " + str(theTrial))

        i = 0
        totalDistance = 0.0
        latency = 1
        mainLatency = 0.0
        xSummed = 0.0
        ySummed = 0.0
        xAv = 0.0
        yAv = 0.0
        currentDistanceFromGoal = 0.0
        distanceFromGoalSummed = 0.0
        distanceAverage = 0.0
        aX = 0.0
        aY = 0.0

        missingData = 0

        distanceToCenterOfMaze = 0.0
        totalDistanceToCenterOfMaze = 0.0
        averageDistanceToCentre = 0.0

        innerWallCounter = 0.0
        outerWallCounter = 0.0
        annulusCounter = 0.0
        currentHeadingError = 0.0
        distanceToSwimPathCentroid = 0.0
        totalDistanceToSwimPathCentroid = 0.0
        averageDistanceToSwimPathCentroid = 0.0

        distanceToOldGoal = 0.0
        totalDistanceToOldGoal = 0.0
        averageDistanceToOldGoal = 0.0

        startX = 0.0
        startY = 0.0

        oldItemX = 0.0
        oldItemY = 0.0
        corridorCounter = 0.0
        quadrantOne = 0
        quadrantTwo = 0
        quadrantThree = 0
        quadrantFour = 0
        quadrantTotal = 0
        x = 0
        oldX = 0.0
        oldY = 0.0
        latencyCounter = 0.0
        arrayX = []
        arrayY = []
        gridCellSize = float(mazeradius*2)/10.0
        Matrix = [[0 for x in range(0, math.ceil(gridCellSize)+1)] for y in range(0, math.ceil(gridCellSize)+1)]

        for aDatapoint in theTrial:  # for each row in our sheet

            if dayNum == 9 or dayNum == 14:
                if aDatapoint.gettime() > probeCutVar:
                    continue
            if i == 0:
                startX = aDatapoint.getx()
                startY = aDatapoint.gety()
                startTime = aDatapoint.gettime()


            # Swim Path centroid
            i += 1.0
            xSummed += float(aDatapoint.getx())
            ySummed += float(aDatapoint.gety())
            aX = float(aDatapoint.getx())
            aY = float(aDatapoint.gety())

            arrayX.append(aX)
            arrayY.append(aY)

            # Average Distance
            currentDistanceFromGoal = math.sqrt((goalX - aX) ** 2 + (goalY - aY) ** 2)*scalingFactor



            # in zones
            distanceCenterToGoal = math.sqrt((mazeCentreX - goalX) ** 2 + (mazeCentreY - goalY) ** 2)*scalingFactor
            annulusZoneInner = distanceCenterToGoal - (chainingRadius / 2)
            annulusZoneOuter = distanceCenterToGoal + (chainingRadius / 2)
            distanceToCenterOfMaze = math.sqrt((mazeCentreX - aX) ** 2 + (mazeCentreY - aY) ** 2)*scalingFactor
            totalDistanceToCenterOfMaze += distanceToCenterOfMaze
            distanceFromStartToGoal = math.sqrt((goalX - startX) ** 2 + (goalY - startY) ** 2)*scalingFactor

            distance = math.sqrt(abs(oldX - aX) ** 2 + abs(oldY - aY) ** 2)*scalingFactor
            distanceFromGoalSummed += currentDistanceFromGoal
            totalDistance += distance
            oldX = aX
            oldY = aY

            if distanceToCenterOfMaze > biggerWallZone:  # calculate if we are in zones
                innerWallCounter += 1.0
            if distanceToCenterOfMaze > smallerWallZone:
                outerWallCounter += 1.0
            if (distanceToCenterOfMaze >= annulusZoneInner) and (distanceToCenterOfMaze <= annulusZoneOuter):
                annulusCounter += 1.0

            a, b = 0, 0

            Matrix[int(aDatapoint.getx()/gridCellSize)][int(aDatapoint.gety()/gridCellSize)] = 1  # set matrix cells to 1 if we have visited them

            if (mazeCentreX - aX) != 0:
                centerArcTangent = math.degrees(math.atan((mazeCentreY - aY) / (mazeCentreX - aX)))


            if aDatapoint.getx() >= mazeCentreX and aDatapoint.gety() >= mazeCentreY:
                quadrantOne = 1
            elif aDatapoint.getx() < mazeCentreX and aDatapoint.gety() >= mazeCentreY:
                quadrantTwo = 1
            elif aDatapoint.getx() >= mazeCentreX and aDatapoint.gety() < mazeCentreY:
                quadrantThree = 1
            elif aDatapoint.getx() < mazeCentreX and aDatapoint.gety() < mazeCentreY:
                quadrantFour = 1

            latency = aDatapoint.gettime() - startTime
            if truncateFlag and currentDistanceFromGoal < float(goalDiam)/2.0:
                break

        quadrantTotal = quadrantOne + quadrantTwo + quadrantThree + quadrantFour

        xAv = xSummed / i  # get our average positions for the centroid
        yAv = ySummed / i
        swimPathCentroid = (xAv, yAv)


        startPoint = np.array([startX,startY])
        goalPoint = np.array([goalX,goalY])

        startToPlatVector = goalPoint-startPoint


        aArcTangent = math.degrees(math.atan((goalY - startY) / (goalX - startX)))
        upperCorridor = aArcTangent + corridorWidth
        lowerCorridor = aArcTangent - corridorWidth
        corridorWidth = 0.0
        totalHeadingError = 0.0
        initialHeadingError = 0.0
        initialHeadingErrorCount = 0
        for aDatapoint in theTrial:  # go back through all values and calculate distance to the centroid
            if dayNum == 9 or dayNum == 14:
                if aDatapoint.gettime() > probeCutVar:
                    continue
            currentDistanceFromGoal = math.sqrt((goalX - aDatapoint.getx()) ** 2 + (goalY - aDatapoint.gety()) ** 2)*scalingFactor
            distanceToSwimPathCentroid = math.sqrt((xAv - aDatapoint.getx()) ** 2 + (yAv - aDatapoint.gety()) ** 2)*scalingFactor
            totalDistanceToSwimPathCentroid += distanceToSwimPathCentroid
            distanceFromStartToCurrent = math.sqrt((aDatapoint.getx() - startX) **2 + (aDatapoint.gety() - startY)**2)*scalingFactor

            if oldItemX!=0 and aDatapoint.getx() - oldItemX != 0 and aDatapoint.getx() - startX != 0:
                currentToPlat = np.subtract(np.array([goalX, goalY]),np.array([aDatapoint.getx(), aDatapoint.gety()]))
                oldToCurrent = np.subtract(np.array([aDatapoint.getx(), aDatapoint.gety()]),np.array([oldItemX,oldItemY]))
                currentHeadingError = abs(self.angle_between(currentToPlat,oldToCurrent))
                withinCorridor = math.degrees(math.atan((aDatapoint.gety() - startY) / (aDatapoint.getx() - startX)))
                corridorWidth = abs(
                    aArcTangent - abs(math.degrees(math.atan((aDatapoint.gety() - oldItemY) / (aDatapoint.getx() - oldItemX)))))
                if float(lowerCorridor) <= float(withinCorridor) <= float(upperCorridor):
                    corridorCounter += 1.0
            if(aDatapoint.gettime() < 1.0):
                initialHeadingError += currentHeadingError
                initialHeadingErrorCount += 1

            oldItemX = aDatapoint.getx()
            oldItemY = aDatapoint.gety()
            totalHeadingError += currentHeadingError
            if truncateFlag and currentDistanceFromGoal < float(goalDiam)/2.0:
                break

        corridorAverage = corridorCounter / i
        distanceAverage = distanceFromGoalSummed / i  # calculate our average distances to landmarks
        averageDistanceToSwimPathCentroid = totalDistanceToSwimPathCentroid / i
        averageDistanceToOldGoal = totalDistanceToOldGoal / i
        averageDistanceToCentre = totalDistanceToCenterOfMaze / i
        averageHeadingError = totalHeadingError / i
        try:
            averageInitialHeadingError = initialHeadingError/initialHeadingErrorCount
        except:
            averageInitialHeadingError = 0
        cellCounter = 0.0  # initialize our cell counter

        percentTraversed = (((sum(sum(Matrix,[]))) / len(Matrix[0])**2) * scalingFactor) * 100.0  # turn our count into a percentage over how many cells we can visit

        velocity = 0
        idealDistance = distanceFromStartToGoal
        if latency != 0:
            try:
                velocity = (totalDistance/latency)
            except:
                velocity = 0
                pass
        idealCumulativeDistance = 0.0
        try:
            sampleRate = (theTrial.datapointList[-1].gettime() - startTime)/(len(theTrial.datapointList) - 1)
        except:
            print("Error with sample rate calculation")
            logging.info("Error with sample rate calculation")
            sampleRate = 1
        while idealDistance > math.ceil(float(goalDiam)/2):
            idealCumulativeDistance += idealDistance
            idealDistance = (idealDistance - velocity*sampleRate)
            if(idealCumulativeDistance > 10000):
                break

        ipe = float(distanceFromGoalSummed - idealCumulativeDistance)*sampleRate

        if ipe<0:
            ipe = 0

        if useEntropyFlag:
            entropyResult = self.calculateEntropy(theTrial,goalX,goalY)
        else:
            entropyResult = False
        return corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToCentre, averageHeadingError, percentTraversed, quadrantTotal, totalDistance, latency, innerWallCounter, outerWallCounter, annulusCounter, i, arrayX, arrayY, velocity, ipe, averageInitialHeadingError, entropyResult

    def mainCalculate(self, goalPosVar=goalPosVar, goalDiamVar=goalDiamVar):
        global softwareStringVar
        logging.debug("Calculate Called")
        self.updateTasks()
        theStatus.set("Initializing")

        print("Running: " + str(goalPosVar) + " with diamater " + str(goalDiamVar))

        mazeDiamVar = mazeDiamStringVar.get()
        mazeCentreVar = mazeCentreStringVar.get()
        corridorWidthVar = corridorWidthStringVar.get()
        chainingRadiusVar = chainingRadiusStringVar.get()
        thigmotaxisZoneSizeVar = thigmotaxisZoneSizeStringVar.get()  # get important values
        softwareScalingFactorVar = softwareScalingFactorStringVar.get()
        # basic setup


        ipeMaxVal = params.ipeMaxVal
        headingMaxVal = params.headingMaxVal
        distanceToSwimMaxVal = params.distanceToSwimMaxVal
        distanceToPlatMaxVal = params.distanceToPlatMaxVal
        corridorAverageMinVal = params.corridorAverageMinVal
        corridoripeMaxVal = params.corridoripeMaxVal
        annulusCounterMaxVal = params.annulusCounterMaxVal
        quadrantTotalMaxVal = params.quadrantTotalMaxVal
        percentTraversedMaxVal = params.percentTraversedMaxVal
        percentTraversedMinVal = params.percentTraversedMinVal
        distanceToCentreMaxVal = params.distanceToCentreMaxVal
        innerWallMaxVal = params.innerWallMaxVal
        outerWallMaxVal = params.outerWallMaxVal
        ipeIndirectMaxVal = params.ipeIndirectMaxVal
        percentTraversedRandomMaxVal = params.percentTraversedRandomMaxVal
        focalMinDistance = params.focalMinDistance
        focalMaxDistance = params.focalMaxDistance
        chainingMaxCoverage = params.chainingMaxCoverage
        thigmoMinDistance = params.thigmoMinDistance
        directedSearchMaxDistance = params.directedSearchMaxDistance
        headingIndirectMaxVal = params.headingIndirectMaxVal


        mazeRadius = 0.0
        thigmotaxisZoneSize = 0.0
        corridorWidth = 0.0
        goalX = 0.0
        goalY = 0.0
        oldDay = ""
        chainingRadius = 0.0
        mazeCentre = (0.0, 0.0)
        mazeRadius = 0.0
        smallerWallZone = 0.0
        biggerWallZone = 0.0
        distanceCenterToGoal = 0.0
        totalTrialCount = 0.0
        thigmotaxisCount = 0.0
        randomCount = 0.0
        scanningCount = 0.0
        chainingCount = 0.0
        directSearchCount = 0.0
        focalSearchCount = 0.0
        directPathCount = 0.0
        indirectSearchCount = 0.0
        notRecognizedCount = 0.0
        n = 0
        numOfRows = 0
        mazeCentreX, mazeCentreY = mazeCentre
        flag = False
        dayFlag = False
        autoFlag = False
        skipFlag = False
        software = softwareStringVar.get()

        try:
            aExperiment = saveFileAsExperiment(software, theFile, fileDirectory)
        except Exception:
            show_error("No Input")
            print("Unexpected Error loading experiment")
            traceback.print_exc()
            return

        mazeCentreX, mazeCentreY, goalX, goalY, mazeDiamVar, mazeRadius, goalDiamVar = self.getAutoLocations(aExperiment, goalX, goalY, goalPosVar, mazeCentreX, mazeCentreY, mazeCentreVar, mazeDiamVar, software, goalDiamVar)
        if scale:
            scalingFactor = softwareScalingFactorVar
        else:
            scalingFactor = 1.0

        thigmotaxisZoneSize = float(thigmotaxisZoneSizeVar) * scalingFactor # update the thigmotaxis zone
        chainingRadius = float(chainingRadiusVar) * scalingFactor # update the chaining radius
        corridorWidth = (int(corridorWidthVar) / 2) * scalingFactor # update the corridor width

        smallerWallZone = mazeRadius - math.ceil(thigmotaxisZoneSize / 2)  # update the smaller wall zone
        biggerWallZone = mazeRadius - thigmotaxisZoneSize  # and bigger wall zone

        theStatus.set('Calculating Search Strategies...')  # update status bar
        self.updateTasks()
        currentOutputFile = outputFile+str(goalPosVar)+".csv"
        logging.debug("Calculating search strategies")
        try:  # try to open a csv file for output
            f = open(currentOutputFile, 'wt')
            writer = csv.writer(f, delimiter=',', quotechar='"')
        except Exception:
            traceback.print_exc()
            logging.error("Cannot write to " + str(currentOutputFile))
            return

        headersToWrite = []
        if aExperiment.hasDateInfo:
            headersToWrite.extend(["Date", "Time", "Day"])
        
        headersToWrite.append("Trial")
        if aExperiment.hasTrialNames:
            headersToWrite.append("Name")
        if aExperiment.hasAnimalNames:
            headersToWrite.append("Animal")

        headersToWrite.extend(["Trial Code", "Strategy Type", "ipe", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage", "score", "initial heading error", "entropy", "Strategy (manual)"])
        writer.writerow(headersToWrite) # write to the csv

        dayNum = 0
        trialNum = {}
        curDate = None
        for aTrial in aExperiment:
            animal = aTrial.animal
            if aExperiment.hasAnimalNames:
                animal = aTrial.animal.replace("*", "")
                animal = animal.replace("Jan","1")
                animal = animal.replace("Feb","2")
                animal = animal.replace("Mar","3")
                animal = animal.replace("Apr","4")
                animal = animal.replace("May","5")
                animal = animal.replace("Jun","6")
                animal = animal.replace("Jul","7")
                animal = animal.replace("Aug","8")
                animal = animal.replace("Sep","9")
                animal = animal.replace("Oct","10")
                animal = animal.replace("Nov","11")
                animal = animal.replace("Dec","12")

            if aExperiment.hasDateInfo and aTrial.date.date() != curDate:
                dayNum += 1
                curDate = aTrial.date.date()
                trialNum = {}
                trialNum[animal] = 1
            elif animal in trialNum:
                trialNum[animal] += 1
            else:
                trialNum[animal] = 1

            xSummed = 0.0
            ySummed = 0.0
            xAv = 0.0
            yAv = 0.0

            currentDistanceFromGoal = 0.0
            distanceAverage = 0.0
            aX = 0.0
            aY = 0.0

            distanceToCenterOfMaze = 0.0
            totalDistanceToCenterOfMaze = 0.0
            averageDistanceToCentre = 0.0

            innerWallCounter = 0.0
            outerWallCounter = 0.0
            annulusCounter = 0.0

            distanceToSwimPathCentroid = 0.0
            totalDistanceToSwimPathCentroid = 0.0
            averageDistanceToSwimPathCentroid = 0.0

            distanceToOldGoal = 0.0
            totalDistanceToOldGoal = 0.0
            averageDistanceToOldGoal = 0.0

            ipe = 0.0

            startX = 0.0
            startY = 0.0

            areaCoverageGridSize = 19

            corridorCounter = 0.0
            quadrantOne = 0
            quadrantTwo = 0
            quadrantThree = 0
            quadrantFour = 0
            quadrantTotal = 0
            # </editor-fold>
            score = 0
            # Analyze the data ----------------------------------------------------------------------------------------------


            corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToCentre, averageHeadingError, percentTraversed, quadrantTotal, totalDistance, latency, innerWallCounter, outerWallCounter, annulusCounter, i, arrayX, arrayY, velocity, ipe, initialHeadingError, entropyResult = self.calculateValues(
                aTrial, goalX, goalY, mazeCentreX,
                mazeCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone,
                biggerWallZone, scalingFactor, mazeRadius, dayNum, goalDiamVar)

            strategyType = ""
            strategyManual = ""
            # DIRECT SWIM
            if ipe <= ipeMaxVal and averageHeadingError <= headingMaxVal and useDirectPathV:  # direct path
                directPathCount += 1.0
                score = 3
                strategyType = "Direct Path"
            # FOCAL SEARCH
            elif averageDistanceToSwimPathCentroid < (
                    mazeRadius * distanceToSwimMaxVal) and distanceAverage < (
                    distanceToPlatMaxVal * mazeRadius) and totalDistance < focalMaxDistance and totalDistance > focalMinDistance and useFocalSearchV:  # Focal Search
                focalSearchCount += 1.0
                score = 2
                strategyType = "Focal Search"
            # DIRECTED SEARCH
            elif corridorAverage >= corridorAverageMinVal and ipe <= corridoripeMaxVal and totalDistance < directedSearchMaxDistance and useDirectedSearchV:  # directed search
                directSearchCount += 1.0
                score = 2
                strategyType = "Directed Search"
            # Indirect Search
            elif ipe < ipeIndirectMaxVal and averageHeadingError < headingIndirectMaxVal and useIndirectV:  # Near miss
                strategyType = "Indirect Search"
                score = 2
                indirectSearchCount += 1.0
            # CHAINING
            elif float(
                    annulusCounter / i) > annulusCounterMaxVal and quadrantTotal >= quadrantTotalMaxVal and percentTraversed < chainingMaxCoverage and useChainingV:  # or 4 chaining
                chainingCount += 1.0
                score = 1
                strategyType = "Chaining"
            # SCANNING
            elif percentTraversedMinVal <= percentTraversed >= percentTraversedMaxVal and averageDistanceToCentre <= (
                    distanceToCentreMaxVal * mazeRadius) and useScanningV:  # scanning
                scanningCount += 1.0
                score = 1
                strategyType = "Scanning"
            # THIGMOTAXIS
            elif innerWallCounter >= innerWallMaxVal * i and outerWallCounter >= i * outerWallMaxVal and totalDistance > thigmoMinDistance and useThigmoV:  # thigmotaxis
                thigmotaxisCount += 1.0
                score = 0
                strategyType = "Thigmotaxis"
            # RANDOM SEARCH
            elif percentTraversed >= percentTraversedRandomMaxVal and useRandomV:  # random search
                randomCount += 1.0
                score = 0
                strategyType = "Random Search"
            # NOT RECOGNIZED
            else:  # cannot categorize
                strategyType = "Not Recognized"
                notRecognizedCount += 1.0
                if manualFlag and not useManualForAllFlag:
                    print("Day #", "Trial #", "Name", "Date", "Trial", "Strategy Type", "ipe", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage")
                    print(dayNum, trialNum, aTrial.name, aTrial.date, aTrial.trial, strategyType, round(ipe,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2))
                    #print("ipe: ", ipe, " Distance to centroid: ", averageDistanceToSwimPathCentroid, " Distance to plat: ", distanceAverage)
                    plotName = "Strategy " + str(strategyType) + " Animal " + str(animal) + "  Day " + str(dayNum) + " Trial " + str(trialNum[animal])
                    self.plotPoints(arrayX, arrayY, float(mazeDiamVar), float(mazeCentreX), float(mazeCentreY),
                                float(goalX), float(goalY), float(scalingFactor), plotName,
                                ("Animal: " + str(animal) + "  Day/Trial: " + str(dayNum) + "/" + str(trialNum[animal])), float(goalDiamVar))  # ask user for answer
                    root.wait_window(self.top2)  # we wait until the user responds
                    strategyManual = searchStrategyV  # update the strategyType to that of the user
                    try:  # try and kill the popup window
                        self.top2.destroy()
                    except:
                        pass

            totalTrialCount += 1.0

            n += 1
            print("ipe: ", ipe, "    Heading: ",averageHeadingError, " Entropy: ", entropyResult)

            if useManualForAllFlag:
                print("Day #", "Trial #", "Name", "Date", "Trial", "Strategy Type", "ipe", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage")
                print(dayNum, trialNum[animal], aTrial.name, aTrial.date, aTrial.trial, strategyType, round(ipe,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2))
                plotName = "Strategy " + str(strategyType) + " Animal " + str(animal) + "  Day " + str(dayNum) + " Trial " + str(trialNum[animal])
                self.plotPoints(arrayX, arrayY, float(mazeDiamVar), float(mazeCentreX), float(mazeCentreY),
                                float(goalX), float(goalY), float(scalingFactor), plotName,
                                ("Animal: " + str(animal) + "  Day/Trial: " + str(dayNum) + "/" + str(trialNum[animal])), float(goalDiamVar))  # ask user for answer
                root.wait_window(self.top2)  # we wait until the user responds
                strategyManual = searchStrategyV  # update the strategyType to that of the user

            dataToWrite = []
            if aExperiment.hasDateInfo:
                formattedDate = aTrial.date.strftime("%Y-%m-%d")
                formattedTime = aTrial.date.strftime("%I:%M %p")
                dataToWrite.append(formattedDate)
                dataToWrite.append(formattedTime)
                dataToWrite.append(dayNum)
            
            dataToWrite.append(trialNum[animal])
            if aExperiment.hasTrialNames:
                dataToWrite.append(aTrial.name)
            if aExperiment.hasAnimalNames:
                dataToWrite.append(aTrial.animal)

            dataToWrite.extend(
                [(str(animal) + " " + str(dayNum) + " " + str(trialNum[animal])), strategyType, round(ipe, 2), round(velocity, 2), round(totalDistance, 2), round(distanceAverage, 2),
                 round(averageHeadingError, 2), round(percentTraversed, 2), round(latency, 2),
                 round(corridorAverage, 2), score, initialHeadingError, round(entropyResult, 2), str(strategyManual)])
            writer.writerow(dataToWrite)  # writing to csv file

            f.flush()

        print("Direct Path: ", directPathCount, "| Directed Search: ", directSearchCount, "| Focal Search: ", focalSearchCount, "| Indirect Search: ", indirectSearchCount, "| Chaining: ", chainingCount, "| Scanning: ", scanningCount, "| Random Search: ", randomCount, "| Thigmotaxis: ", thigmotaxisCount, "| Not Recognized: ", notRecognizedCount)
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', currentOutputFile))
        elif os.name == 'nt': # For Windows
            os.startfile(currentOutputFile)
        elif os.name == 'posix': # For Linux, Mac, etc.
            subprocess.call(('xdg-open', currentOutputFile))
        self.updateTasks()
        theStatus.set('')
        self.updateTasks()
        csvfilename = "output/results/results " + str(strftime("%Y_%m_%d %I_%M_%S_%p",
                                            localtime()))  # update the csv file name for the next run
        outputFileStringVar.set(csvfilename)

        return

def main():
    b = mainClass(root)  # start the main class (main program)
    root.mainloop()  # loop so the gui stays

if __name__ == "__main__":  # main part of the program -- this is called at runtime
    main()
