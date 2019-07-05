#!/usr/bin/env python

"""searchStrategyAnalysis.py: GUI + analyses ethovision exported xlsx files to determine which search strategy animals follow during
Morris Water Maze trials."""

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
from SearchStrategyAnalysis.appTrial import Trial, Experiment, Parameters, saveFileAsExperiment, Datapoint
import SearchStrategyAnalysis.heatmap
from scipy.stats import norm

try:
    import matlab.engine
except:
    print("matlab engine unavailable")

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
__copyright__ = "Copyright 2018, Jason Snyder Lab, The University of British Columbia"
__credits__ = ["Matthew Cooke", "Tim O'Leary", "Phelan Harris"]
__email__ = "mbcooke@mail.ubc.ca"

if not os.path.exists("logs"):
    os.makedirs("logs")
if not os.path.exists("results"):
    os.makedirs("results")
if not os.path.exists("plots"):
    os.makedirs("plots")
if not os.path.exists("heatmaps"):
    os.makedirs("heatmaps")

logfilename = "logs/logfile " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime())) + ".log"  # name of the log file for the run
logging.basicConfig(filename=logfilename,level=logging.INFO)  # set the default log type to INFO, can be set to DEBUG for more detailed information
csvfilename = "results/results " + str(
    strftime("%Y_%m_%d %I_%M_%S_%p", localtime())) + ".csv"  # name of the default results file
theFile = ""
fileDirectory = ""
platformPosVar = "Auto"
poolDiamVar = "Auto"
platformPosVar = "Auto"  # -21,31
platformDiamVar = "Auto"
poolDiamVar = "Auto"  # 180.0
corridorWidthVar = "40"
poolCentreVar = "Auto"
oldPlatformPosVar = ""
chainingRadiusVar = "35"
thigmotaxisZoneSizeVar = "15"
outputFile = csvfilename
fileFlag = 0

defaultParams = Parameters(name="Default", cseMaxVal=125, headingMaxVal=40, distanceToSwimMaxVal=0.3,
                           distanceToPlatMaxVal=0.3, corridorAverageMinVal=0.7, directedSearchMaxDistance=400, focalMinDistance=100, focalMaxDistance=400, corridorCseMaxVal=1500,
                           annulusCounterMaxVal=0.90, quadrantTotalMaxVal=4, chainingMaxCoverage=40, percentTraversedMaxVal=35,
                           percentTraversedMinVal=5, distanceToCentreMaxVal=0.7, thigmoMinDistance=400, innerWallMaxVal=0.65,
                           outerWallMaxVal=0.35, cseIndirectMaxVal=300, percentTraversedRandomMaxVal=10)

relaxedParams = Parameters(name="Relaxed", cseMaxVal=150, headingMaxVal=45, distanceToSwimMaxVal=0.4,
                           distanceToPlatMaxVal=0.4, corridorAverageMinVal=0.65, directedSearchMaxDistance=500, focalMinDistance=100, focalMaxDistance=500, corridorCseMaxVal=1500,
                           annulusCounterMaxVal=0.85, quadrantTotalMaxVal=3, chainingMaxCoverage=40, percentTraversedMaxVal=35,
                           percentTraversedMinVal=5, distanceToCentreMaxVal=0.7, thigmoMinDistance=400, innerWallMaxVal=0.65,
                           outerWallMaxVal=0.35, cseIndirectMaxVal=350, percentTraversedRandomMaxVal=10)

strictParams = Parameters(name="Strict", cseMaxVal=100, headingMaxVal=35, distanceToSwimMaxVal=0.3,
                           distanceToPlatMaxVal=0.3, corridorAverageMinVal=0.7, directedSearchMaxDistance=400, focalMinDistance=100, focalMaxDistance=400, corridorCseMaxVal=1500,
                           annulusCounterMaxVal=0.90, quadrantTotalMaxVal=4, chainingMaxCoverage=40, percentTraversedMaxVal=35,
                           percentTraversedMinVal=5, distanceToCentreMaxVal=0.7, thigmoMinDistance=400, innerWallMaxVal=0.65,
                           outerWallMaxVal=0.35, cseIndirectMaxVal=250, percentTraversedRandomMaxVal=15)

params = defaultParams

cseMaxVal = params.cseMaxVal
headingMaxVal = params.headingMaxVal
distanceToSwimMaxVal = params.distanceToSwimMaxVal
distanceToPlatMaxVal = params.distanceToPlatMaxVal
corridorAverageMinVal = params.corridorAverageMinVal
corridorCseMaxVal = params.corridorCseMaxVal
annulusCounterMaxVal = params.annulusCounterMaxVal
quadrantTotalMaxVal = params.quadrantTotalMaxVal
percentTraversedMaxVal = params.percentTraversedMaxVal
percentTraversedMinVal = params.percentTraversedMinVal
distanceToCentreMaxVal = params.distanceToCentreMaxVal
innerWallMaxVal = params.innerWallMaxVal
outerWallMaxVal = params.outerWallMaxVal
cseIndirectMaxVal = params.cseIndirectMaxVal
percentTraversedRandomMaxVal = params.percentTraversedRandomMaxVal
directedSearchMaxDistance = params.directedSearchMaxDistance
focalMinDistance = params.focalMinDistance
focalMaxDistance = params.focalMaxDistance
chainingMaxCoverage = params.chainingMaxCoverage
thigmoMinDistanceCustom = params.thigmoMinDistance


isRuediger = False
customFlag = False
useDirectSwimV = True
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
platformPosStringVar = StringVar()  # setup all the gui variables (different from normal variables)
platformPosStringVar.set(platformPosVar)
platformDiamStringVar = StringVar()
platformDiamStringVar.set(platformDiamVar)
poolDiamStringVar = StringVar()
poolDiamStringVar.set(poolDiamVar)
corridorWidthStringVar = StringVar()
corridorWidthStringVar.set(corridorWidthVar)
poolCentreStringVar = StringVar()
poolCentreStringVar.set(poolCentreVar)
oldPlatformPosStringVar = StringVar()
oldPlatformPosStringVar.set(oldPlatformPosVar)
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
gridSizeStringVar = StringVar()
gridSizeStringVar.set("70")
useManual = BooleanVar()
useManual.set(False)
useManualForAll = BooleanVar()
useManualForAll.set(False)
useEntropy = BooleanVar()
useEntropy.set(False)
useScaling = BooleanVar()
useScaling.set(False)
scale = False

def show_error(text):  # popup box with error text
    logging.debug("Displaying Error")
    try:
        top = Toplevel(root)  # show as toplevel
        Label(top, text=text).pack()   # label set to text
        Button(top, text="OK", command=top.destroy).pack(pady=5)   # add ok button
    except:
        logging.info("Couldn't Display error "+text)

class mainClass:
    def __init__(self, root):  # init is called on runtime
        logging.debug("Initiating Main program")
        try:
            self.buildGUI(root)
        except:
            logging.fatal("Couldn't build GUI")
            self.tryQuit()
            return
        logging.debug("GUI is built")

    def buildGUI(self, root):  # Called in the __init__ to build the GUI window
        root.wm_title("Pathfinder")

        global platformPosVar
        global platformDiamVar
        global poolDiamVar
        global corridorWidthVar
        global poolCentreVar
        global oldPlatformPosVar
        global chainingRadiusVar
        global thigmotaxisZoneSizeVar
        global outputFile
        global manualFlag
        global useManualForAllFlag
        global useEntropyFlag
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

        # ****** TOOLBAR ******
        self.toolbar = Frame(root)  # add a toolbar to the frame
        self.toolbar.config(bg="white")

        ttk.Style().configure('selected.TButton', foreground='red', background='white')  # have two button styles
        ttk.Style().configure('default.TButton', foreground='black',
                              background='white')  # note: we are using TKK buttons not tk buttons because tk buttons don't support style changes on mac

        self.defaultButton = ttk.Button(self.toolbar, text="Default", command=self.defaultButtonFunc,
                                        style='selected.TButton')  # add snyder button
        self.defaultButton.grid(row=0, ipadx=2, pady=2, padx=2)
        self.strictButton = ttk.Button(self.toolbar, text="Relaxed", command=self.strictButtonFunc,
                                        style='default.TButton')  # add reudiger button
        self.strictButton.grid(row=0, column=1, ipadx=2, pady=2, padx=2)
        self.relaxedButton = ttk.Button(self.toolbar, text="Strict", command=self.relaxedButtonFunc,
                                       style='default.TButton')  # add garthe button
        self.relaxedButton.grid(row=0, column=2, ipadx=2, pady=2, padx=2)
        self.customButton = ttk.Button(self.toolbar, text="Custom...", command=self.custom, style='default.TButton')
        self.customButton.grid(row=0, column=3, ipadx=2, pady=2, padx=2)  # add custom button
        self.toolbar.pack(side=TOP, fill=X)  # place the toolbar
        self.defaultButton.bind("<Enter>", partial(self.on_enter, "Use preset values from our paper"))
        self.defaultButton.bind("<Leave>", self.on_leave)
        self.relaxedButton.bind("<Enter>", partial(self.on_enter, "Use preset values relaxed"))
        self.relaxedButton.bind("<Leave>", self.on_leave)
        self.strictButton.bind("<Enter>", partial(self.on_enter, "Use preset values strict"))
        self.strictButton.bind("<Leave>", self.on_leave)
        self.customButton.bind("<Enter>", partial(self.on_enter, "Choose your own values (please disable scaling)"))
        self.customButton.bind("<Leave>", self.on_leave)

        # ******* Software Type *******
        self.softwareBar = Frame(root)  # add a toolbar to the frame
        self.softwareBar.config(bg="white")
        self.ethovisionRadio = Radiobutton(self.softwareBar, text="Ethovision", variable=softwareStringVar,
                                           value="ethovision",
                                           indicatoron=1, width=15, bg="white")
        self.ethovisionRadio.grid(row=0, column=0, padx=5, sticky='NW')  # add the radiobuttons for selection

        self.anymazeRadio = Radiobutton(self.softwareBar, text="Anymaze", variable=softwareStringVar,
                                        value="anymaze",
                                        indicatoron=1, width=15, bg="white")
        self.anymazeRadio.grid(row=0, column=1, padx=5, sticky='NW')
        self.watermazeRadio = Radiobutton(self.softwareBar, text="Watermaze", variable=softwareStringVar,
                                          value="watermaze", indicatoron=1, width=15, bg="white")
        self.watermazeRadio.grid(row=0, column=2, padx=5, sticky='NW')
        self.eztrackRadio = Radiobutton(self.softwareBar, text="ezTrack", variable=softwareStringVar,
                                          value="eztrack", indicatoron=1, width=15, bg="white")
        self.eztrackRadio.grid(row=0, column=3, padx=5, sticky='NW')
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
                platformPosVar, platformDiamVar, poolDiamVar, poolCentreVar, oldPlatformPosVar, corridorWidthVar, chainingRadiusVar, thigmotaxisZoneSizeVar, softwareScalingFactorVar = pickle.load(f)
                platformPosStringVar.set(platformPosVar)
                platformDiamStringVar.set(platformDiamVar)
                poolDiamStringVar.set(poolDiamVar)
                poolCentreStringVar.set(poolCentreVar)
                oldPlatformPosStringVar.set(oldPlatformPosVar)
                corridorWidthStringVar.set(corridorWidthVar)
                chainingRadiusStringVar.set(chainingRadiusVar)
                thigmotaxisZoneSizeStringVar.set(thigmotaxisZoneSizeVar)
                softwareScalingFactorStringVar.set(softwareScalingFactorVar)
        except:
            pass


        self.platformPos = Label(self.paramFrame, text="Platform Position (x,y):", bg="white")  # add different items (Position)
        self.platformPos.grid(row=0, column=0, sticky=E)  # place this in row 0 column 0
        self.platformPosE = Entry(self.paramFrame, textvariable=platformPosStringVar)  # add an entry text box
        self.platformPosE.grid(row=0, column=1)  # place this in row 0 column 1
        self.platformPos.bind("<Enter>", partial(self.on_enter, "Platform position. Example: 2.5,-3.72 or Auto"))
        self.platformPos.bind("<Leave>", self.on_leave)

        self.platformDiam = Label(self.paramFrame, text="Platform Diameter (cm):", bg="white")
        self.platformDiam.grid(row=1, column=0, sticky=E)
        self.platformDiamE = Entry(self.paramFrame, textvariable=platformDiamStringVar)
        self.platformDiamE.grid(row=1, column=1)
        self.platformDiam.bind("<Enter>", partial(self.on_enter, "Platform diameter. Use the same unit as the data"))
        self.platformDiam.bind("<Leave>", self.on_leave)

        self.poolDiam = Label(self.paramFrame, text="Pool Diameter (cm):", bg="white")
        self.poolDiam.grid(row=2, column=0, sticky=E)
        self.poolDiamE = Entry(self.paramFrame, textvariable=poolDiamStringVar)
        self.poolDiamE.grid(row=2, column=1)
        self.poolDiam.bind("<Enter>", partial(self.on_enter, "The diameter of the MWM. Use the same unit as the data"))
        self.poolDiam.bind("<Leave>", self.on_leave)

        self.poolCentre = Label(self.paramFrame, text="Pool Centre (x,y):", bg="white")
        self.poolCentre.grid(row=3, column=0, sticky=E)
        self.poolCentreE = Entry(self.paramFrame, textvariable=poolCentreStringVar)
        self.poolCentreE.grid(row=3, column=1)
        self.poolCentre.bind("<Enter>", partial(self.on_enter, "Pool Centre. Example: 0.0,0.0 or Auto"))
        self.poolCentre.bind("<Leave>", self.on_leave)

        self.oldPlatformPos = Label(self.paramFrame, text="Old Platform Position (x,y):", bg="white")
        self.oldPlatformPos.grid(row=4, column=0, sticky=E)
        self.oldPlatformPosE = Entry(self.paramFrame, textvariable=oldPlatformPosStringVar)
        self.oldPlatformPosE.grid(row=4, column=1)
        self.oldPlatformPos.bind("<Enter>", partial(self.on_enter, "Not currently used"))
        self.oldPlatformPos.bind("<Leave>", self.on_leave)

        self.headingError = Label(self.paramFrame, text="Corridor Width (degrees):", bg="white")
        self.headingError.grid(row=5, column=0, sticky=E)
        self.headingErrorE = Entry(self.paramFrame, textvariable=corridorWidthStringVar)
        self.headingErrorE.grid(row=5, column=1)
        self.headingError.bind("<Enter>", partial(self.on_enter, "This is an angular corridor (in degrees) in which the animal must face"))
        self.headingError.bind("<Leave>", self.on_leave)


        self.chainingRadius = Label(self.paramFrame, text="Chaining Width (cm):", bg="white")
        self.chainingRadius.grid(row=6, column=0, sticky=E)
        self.chainingRadiusE = Entry(self.paramFrame, textvariable=chainingRadiusStringVar)
        self.chainingRadiusE.grid(row=6, column=1)
        self.chainingRadius.bind("<Enter>", partial(self.on_enter, "The diameter of the ring in which chaining is considered (centered on platform)"))
        self.chainingRadius.bind("<Leave>", self.on_leave)


        self.thigmotaxisZoneSize = Label(self.paramFrame, text="Thigmotaxis Zone Size (cm):", bg="white")
        self.thigmotaxisZoneSize.grid(row=7, column=0, sticky=E)
        self.thigmotaxisZoneSizeE = Entry(self.paramFrame, textvariable=thigmotaxisZoneSizeStringVar)
        self.thigmotaxisZoneSizeE.grid(row=7, column=1)
        self.thigmotaxisZoneSize.bind("<Enter>", partial(self.on_enter, "Size of the zone in which thigmotaxis is considered (from the outer wall)"))
        self.thigmotaxisZoneSize.bind("<Leave>", self.on_leave)


        self.softwareScalingFactor = Label(self.paramFrame, text="Pixels/cm (for Anymaze and Watermaze):", bg="white")
        self.softwareScalingFactor.grid(row=8, column=0, sticky=E)
        self.softwareScalingFactorE = Entry(self.paramFrame, textvariable=softwareScalingFactorStringVar)
        self.softwareScalingFactorE.grid(row=8, column=1)
        self.softwareScalingFactor.bind("<Enter>", partial(self.on_enter, "This is used to convert Anymaze and Watermaze from Pixels to cm"))
        self.softwareScalingFactor.bind("<Leave>", self.on_leave)


        self.saveDirectory = Label(self.paramFrame, text="Output File (.csv):", bg="white")
        self.saveDirectory.grid(row=9, column=0, sticky=E)
        self.saveDirectoryE = Entry(self.paramFrame, textvariable=outputFileStringVar)
        self.saveDirectoryE.grid(row=9, column=1)
        self.saveDirectory.bind("<Enter>", partial(self.on_enter, "The csv file to store the results"))
        self.saveDirectory.bind("<Leave>", self.on_leave)


        global outputFile  # allow outputFile to be accessed from anywhere (not secure)
        outputFile = outputFileStringVar.get()  # get the value entered for the ouput file

        manualFlag = False  # a flag that lets us know if we want to use manual categorization
        useManualForAllFlag = False
        useEntropyFlag = False

        self.scalingTickL = Label(self.paramFrame, text="Scale values: ", bg="white")  # label for the tickbox
        self.scalingTickL.grid(row=14, column=0, sticky=E)  # placed here
        self.scalingTickC = Checkbutton(self.paramFrame, variable=useScaling, bg="white")  # the actual tickbox
        self.scalingTickC.grid(row=14, column=1)
        self.scalingTickL.bind("<Enter>", partial(self.on_enter, "Check if you want to scale the values to fit your pool"))
        self.scalingTickL.bind("<Leave>", self.on_leave)


        scale = useScaling.get()

        self.manualTickL = Label(self.paramFrame, text="Manual categorization for uncategorized trials: ", bg="white")  # label for the tickbox
        self.manualTickL.grid(row=15, column=0, sticky=E)  # placed here
        self.manualTickC = Checkbutton(self.paramFrame, variable=useManual, bg="white")  # the actual tickbox
        self.manualTickC.grid(row=15, column=1)
        self.manualTickL.bind("<Enter>", partial(self.on_enter, "Unrecognized strategies will popup so you can manually categorize them"))
        self.manualTickL.bind("<Leave>", self.on_leave)
        self.manualForAllL = Label(self.paramFrame, text="Manual categorization for all trials: ", bg="white")  # label for the tickbox
        self.manualForAllL.grid(row=16, column=0, sticky=E)  # placed here
        self.manualForAllC = Checkbutton(self.paramFrame, variable=useManualForAll, bg="white")  # the actual tickbox
        self.manualForAllC.grid(row=16, column=1)
        self.manualForAllL.bind("<Enter>", partial(self.on_enter, "All trials will popup so you can manually categorize them"))
        self.manualForAllL.bind("<Leave>", self.on_leave)
        self.entropyL = Label(self.paramFrame, text="Run entropy calculation (requires matlab): ", bg="white")  # label for the tickbox
        self.entropyL.grid(row=17, column=0, sticky=E)  # placed here
        self.entropyC = Checkbutton(self.paramFrame, variable=useEntropy, bg="white")  # the actual tickbox
        self.entropyC.grid(row=17, column=1)
        self.entropyL.bind("<Enter>", partial(self.on_enter, "Calculates the entropy of the trial (slow)"))
        self.entropyL.bind("<Leave>", self.on_leave)

        useManualForAllFlag = useManualForAll.get()
        useEntropyFlag = useEntropy.get()
        manualFlag = useManual.get()  # get the value of the tickbox

        self.calculateButton = Button(self.paramFrame, text="Calculate", fg="black",
                                      command=self.manual)  # add a button that says calculate
        self.calculateButton.grid(row=18, column=0, columnspan=3)



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
        webbrowser.open('https://github.com/Norton50/JSL/blob/master/README.md')

    def getHelp(self):  # go to readme
        logging.debug("Called help")
        webbrowser.open('https://github.com/Norton50/JSL/blob/master/README.md')

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
        self.manual()

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

    def manual(self):  # function that checks for the manual flag and runs the program
        global manualFlag
        global useManualForAllFlag
        global useEntropyFlag
        manualFlag = useManual.get()
        useManualForAllFlag = useManualForAll.get()
        useEntropyFlag = useEntropy.get()
        if manualFlag or useManualForAllFlag:  # if we want manual we can't use threading
            self.mainCalculate()
        else:  # else start the threads
            self.mainThreader()

    def defaultButtonFunc(self):  # actions on button press (snyder button)
        logging.debug("Default selected")
        self.defaultButton.configure(style='selected.TButton')  # change the style of the selected
        self.strictButton.configure(style='default.TButton')  # and non-selected buttons
        self.relaxedButton.configure(style='default.TButton')
        self.customButton.configure(style='default.TButton')
        params = defaultParams

    def strictButtonFunc(self):  # see snyder
        logging.debug("Strict selected")
        self.defaultButton.configure(style='default.TButton')
        self.strictButton.configure(style='selected.TButton')
        self.relaxedButton.configure(style='default.TButton')
        self.customButton.configure(style='default.TButton')
        params = strictParams

    def relaxedButtonFunc(self):  # see snyder
        logging.debug("Relaxed selected")
        self.defaultButton.configure(style='default.TButton')
        self.strictButton.configure(style='default.TButton')
        self.relaxedButton.configure(style='selected.TButton')
        self.customButton.configure(style='default.TButton')
        params = relaxedParams

    def custom(self):
        logging.debug("Getting custom values")
        # global cseMaxVal
        # global headingMaxVal
        # global distanceToSwimMaxVal
        # global distanceToPlatMaxVal
        # global corridorAverageMinVal
        # global annulusCounterMaxVal
        # global quadrantTotalMaxVal
        # global corridorCseMaxVal
        # global percentTraversedMaxVal
        # global percentTraversedMinVal
        # global distanceToCentreMaxVal
        # global innerWallMaxVal
        # global outerWallMaxVal
        # global cseIndirectMaxVal
        # global percentTraversedRandomMaxVal
        # global directedSearchMaxDistance
        # global focalMinDistance
        # global focalMaxDistance
        # global chainingMaxCoverage
        # global thigmoMinDistance

        global useDirectSwimV
        global useFocalSearchV
        global useDirectedSearchV
        global useScanningV
        global useChainingV
        global useRandomV
        global useIndirectV
        global useThigmoV

        self.useDirectSwim = BooleanVar()
        self.useFocalSearch = BooleanVar()
        self.useDirectedSearch = BooleanVar()
        self.useScanning = BooleanVar()
        self.useChaining = BooleanVar()
        self.useRandom = BooleanVar()
        self.useIndirect = BooleanVar()
        self.useThigmo = BooleanVar()

        self.defaultButton.configure(style='default.TButton')
        self.strictButton.configure(style='default.TButton')
        self.relaxedButton.configure(style='default.TButton')
        self.customButton.configure(style='selected.TButton')

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

        try:
            with open('customobjs.pickle', 'rb') as f:
                cseMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, corridorAverageMinVal, directedSearchMaxDistance, focalMinDistance, focalMaxDistance, corridorCseMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, chainingMaxCoverage, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, thigmoMinDistance, innerWallMaxVal, outerWallMaxVal, cseIndirectMaxVal, percentTraversedRandomMaxVal, useDirectSwimV, useFocalSearchV, useDirectedSearchV, useScanningV, useChainingV, useRandomV, useIndirectV, useThigmoV = pickle.load(f)
                self.useDirectSwim.set(useDirectSwimV)
                self.useFocalSearch.set(useFocalSearchV)
                self.useDirectedSearch.set(useDirectedSearchV)
                self.useScanning.set(useScanningV)
                self.useChaining.set(useChainingV)
                self.useRandom.set(useRandomV)
                self.useIndirect.set(useIndirectV)
                self.useThigmo.set(useThigmoV)

        except:
            cseMaxVal = params.cseMaxVal
            headingMaxVal = params.headingMaxVal
            distanceToSwimMaxVal = params.distanceToSwimMaxVal
            distanceToPlatMaxVal = params.distanceToPlatMaxVal
            corridorAverageMinVal = params.corridorAverageMinVal
            corridorCseMaxVal = params.corridorCseMaxVal
            annulusCounterMaxVal = params.annulusCounterMaxVal
            quadrantTotalMaxVal = params.quadrantTotalMaxVal
            percentTraversedMaxVal = params.percentTraversedMaxVal
            percentTraversedMinVal = params.percentTraversedMinVal
            distanceToCentreMaxVal = params.distanceToCentreMaxVal
            innerWallMaxVal = params.innerWallMaxVal
            outerWallMaxVal = params.outerWallMaxVal
            cseIndirectMaxVal = params.cseIndirectMaxVal
            percentTraversedRandomMaxVal = params.percentTraversedRandomMaxVal
            directedSearchMaxDistance = params.directedSearchMaxDistance
            focalMinDistance = params.focalMinDistance
            focalMaxDistance = params.focalMaxDistance
            chainingMaxCoverage = params.chainingMaxCoverage
            thigmoMinDistance = params.thigmoMinDistance

            self.useDirectSwim.set(True)
            self.useFocalSearch.set(True)
            self.useDirectedSearch.set(True)
            self.useScanning.set(True)
            self.useChaining.set(True)
            self.useRandom.set(True)
            self.useIndirect.set(True)
            self.useThigmo.set(True)



        self.jslsMaxCustom.set(cseMaxVal)
        self.headingErrorCustom.set(headingMaxVal)
        self.distanceToSwimCustom.set(distanceToSwimMaxVal * 100)
        self.distanceToPlatCustom.set(distanceToPlatMaxVal * 100)
        self.corridorAverageCustom.set(corridorAverageMinVal * 100)
        self.corridorJslsCustom.set(corridorCseMaxVal)
        self.annulusCustom.set(annulusCounterMaxVal * 100)
        self.quadrantTotalCustom.set(quadrantTotalMaxVal)
        self.percentTraversedCustom.set(percentTraversedMaxVal)
        self.percentTraversedMinCustom.set(percentTraversedMinVal)
        self.distanceToCentreCustom.set(distanceToCentreMaxVal * 100)
        self.innerWallCustom.set(innerWallMaxVal * 100)
        self.outerWallCustom.set(outerWallMaxVal * 100)
        self.jslsIndirectCustom.set(cseIndirectMaxVal)
        self.percentTraversedRandomCustom.set(percentTraversedRandomMaxVal)
        self.directedSearchMaxDistanceCustom.set(directedSearchMaxDistance)
        self.focalMinDistanceCustom.set(focalMinDistance)
        self.focalMaxDistanceCustom.set(focalMaxDistance)
        self.chainingMaxCoverageCustom.set(chainingMaxCoverage)
        self.thigmoMinDistanceCustom.set(thigmoMinDistance)
        # all of the above is the same as in snyder, plus the creation of variables to hold values from the custom menu

        self.top = Toplevel(root)  # we set this to be the top
        self.top.configure(bg="white")
        Label(self.top, text="Custom Values", bg="white", fg="red").grid(row=0, column=0, columnspan=2)  # we title it

        rowCount = 1

        useDirectSwimL = Label(self.top, text="Direct Swim: ", bg="white")  # we add a direct swim label
        useDirectSwimL.grid(row=rowCount, column=0, sticky=E)  # stick it to row 1
        useDirectSwimC = Checkbutton(self.top, variable=self.useDirectSwim, bg="white")  # we add a direct swim checkbox
        useDirectSwimC.grid(row=rowCount, column=1)  # put it beside the label

        rowCount+=1

        jslsMaxCustomL = Label(self.top, text="Cumulative Search Error [maximum]: ", bg="white")  # label for JSLs
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

        distanceToPlatCustomL = Label(self.top, text="Distance to platform [maximum, % of radius]: ", bg="white")
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

        corridorJslsCustomL = Label(self.top, text="Cumulative Search Error [maximum]: ", bg="white")
        corridorJslsCustomL.grid(row=rowCount, column=0, sticky=E)
        corridorJslsCustomE = Entry(self.top, textvariable=self.corridorJslsCustom)
        corridorJslsCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useIndirectL = Label(self.top, text="Spatial Indirect: ", bg="white")
        useIndirectL.grid(row=rowCount, column=0, sticky=E)
        useIndirectC = Checkbutton(self.top, variable=self.useIndirect, bg="white")
        useIndirectC.grid(row=rowCount, column=1)

        rowCount+=1

        jslsIndirectCustomL = Label(self.top, text="Cumulative Search Error [maximum]: ", bg="white")
        jslsIndirectCustomL.grid(row=rowCount, column=0, sticky=E)
        jslsIndirectCustomE = Entry(self.top, textvariable=self.jslsIndirectCustom)
        jslsIndirectCustomE.grid(row=rowCount, column=1)

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

        chainingMaxCoverageCustomL = Label(self.top, text="Area of pool traversed (maximum, % of pool): ", bg="white")
        chainingMaxCoverageCustomL.grid(row=rowCount, column=0, sticky=E)
        chainingMaxCoverageCustomE = Entry(self.top, textvariable=self.chainingMaxCoverageCustom)
        chainingMaxCoverageCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useScanningL = Label(self.top, text="Scanning: ", bg="white")
        useScanningL.grid(row=rowCount, column=0, sticky=E)
        useScanningC = Checkbutton(self.top, variable=self.useScanning, bg="white")
        useScanningC.grid(row=rowCount, column=1)

        rowCount+=1

        percentTraversedCustomL = Label(self.top, text="Area of pool traversed [maximum, % of pool]: ", bg="white")
        percentTraversedCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedCustomE = Entry(self.top, textvariable=self.percentTraversedCustom)
        percentTraversedCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        percentTraversedMinCustomL = Label(self.top, text="Area of pool traversed [minimum, % of pool]: ", bg="white")
        percentTraversedMinCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedMinCustomE = Entry(self.top, textvariable=self.percentTraversedMinCustom)
        percentTraversedMinCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        distanceToCentreCustomL = Label(self.top, text="Average distance to pool centre [maximum, % of radius]: ", bg="white")
        distanceToCentreCustomL.grid(row=rowCount, column=0, sticky=E)
        distanceToCentreCustomE = Entry(self.top, textvariable=self.distanceToCentreCustom)
        distanceToCentreCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        useThigmoL = Label(self.top, text="Thigmotaxis: ", bg="white")
        useThigmoL.grid(row=rowCount, column=0, sticky=E)
        useThigmoC = Checkbutton(self.top, variable=self.useThigmo, bg="white")
        useThigmoC.grid(row=rowCount, column=1)

        rowCount+=1

        innerWallCustomL = Label(self.top, text="Time in inner wall zone [minimum, % of trial]: ", bg="white")
        innerWallCustomL.grid(row=rowCount, column=0, sticky=E)
        innerWallCustomE = Entry(self.top, textvariable=self.innerWallCustom)
        innerWallCustomE.grid(row=rowCount, column=1)

        rowCount+=1

        outerWallCustomL = Label(self.top, text="Time in outer wall zone [minimum, % of trial]: ", bg="white")
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

        percentTraversedRandomCustomL = Label(self.top, text="Area of pool traversed [minimum, % of pool]: ", bg="white")
        percentTraversedRandomCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedRandomCustomE = Entry(self.top, textvariable=self.percentTraversedRandomCustom)
        percentTraversedRandomCustomE.grid(row=rowCount, column=1)

        # we save the values from the fields and scale them appropriately

        rowCount+=1

        Button(self.top, text="Save", command=self.saveCuston).grid(row=rowCount, column=0, columnspan=2)  # button to save

    def saveCuston(self):  # save the custom values
        logging.debug("Saving custom parameters")
        # global cseMaxVal
        # global headingMaxVal
        # global distanceToSwimMaxVal
        # global distanceToPlatMaxVal
        # global corridorAverageMinVal
        # global annulusCounterMaxVal
        # global quadrantTotalMaxVal
        # global corridorCseMaxVal
        # global percentTraversedMaxVal
        # global percentTraversedMinVal
        # global distanceToCentreMaxVal
        # global innerWallMaxVal
        # global outerWallMaxVal
        # global cseIndirectMaxVal
        # global percentTraversedRandomMaxVal

        global useDirectSwim
        global useFocalSearch
        global useDirectedSearch
        global useScanning
        global useChaining
        global useRandom
        global useIndirect
        global useThigmo

        global useDirectSwimV
        global useFocalSearchV
        global useDirectedSearchV
        global useScanningV
        global useChainingV
        global useRandomV
        global useIndirectV
        global useThigmoV

        cseMaxVal = float(self.jslsMaxCustom.get())
        headingMaxVal = float(self.headingErrorCustom.get())
        distanceToSwimMaxVal = float(self.distanceToSwimCustom.get())/100
        distanceToPlatMaxVal = float(self.distanceToPlatCustom.get())/100
        corridorAverageMinVal = float(self.corridorAverageCustom.get()) / 100
        corridorCseMaxVal = float(self.corridorJslsCustom.get())
        annulusCounterMaxVal = float(self.annulusCustom.get())/100
        quadrantTotalMaxVal = float(self.quadrantTotalCustom.get())
        percentTraversedMaxVal = float(self.percentTraversedCustom.get())
        percentTraversedMinVal = float(self.percentTraversedMinCustom.get())
        distanceToCentreMaxVal = float(self.distanceToCentreCustom.get())/100
        innerWallMaxVal = float(self.innerWallCustom.get())/100
        outerWallMaxVal = float(self.outerWallCustom.get())/100
        cseIndirectMaxVal = float(self.jslsIndirectCustom.get())
        percentTraversedRandomMaxVal = float(self.percentTraversedRandomCustom.get())
        directedSearchMaxDistance = float(self.directedSearchMaxDistanceCustom.get())
        focalMinDistance = float(self.focalMinDistanceCustom.get())
        focalMaxDistance = float(self.focalMaxDistanceCustom.get())
        chainingMaxCoverage = float(self.chainingMaxCoverageCustom.get())
        thigmoMinDistance = float(self.thigmoMinDistanceCustom.get())

        params = Parameters(name="custom", cseMaxVal=float(self.jslsMaxCustom.get()), headingMaxVal=float(self.headingErrorCustom.get()), distanceToSwimMaxVal=float(self.distanceToSwimCustom.get())/100,
                            distanceToPlatMaxVal=float(self.distanceToPlatCustom.get())/100, corridorAverageMinVal=float(self.corridorAverageCustom.get()) / 100, directedSearchMaxDistance=float(self.directedSearchMaxDistanceCustom.get()), focalMinDistance=float(self.focalMinDistanceCustom.get()), focalMaxDistance=float(self.focalMaxDistanceCustom.get()), corridorCseMaxVal=float(self.corridorJslsCustom.get()),
                            annulusCounterMaxVal=float(self.annulusCustom.get())/100, quadrantTotalMaxVal=float(self.quadrantTotalCustom.get()), chainingMaxCoverage=float(self.chainingMaxCoverageCustom.get()), percentTraversedMaxVal=float(self.percentTraversedCustom.get()),
                            percentTraversedMinVal=float(self.percentTraversedMinCustom.get()), distanceToCentreMaxVal=float(self.distanceToCentreCustom.get())/100, thigmoMinDistance = float(self.thigmoMinDistanceCustom.get()), innerWallMaxVal=float(self.innerWallCustom.get())/100,
                            outerWallMaxVal=float(self.outerWallCustom.get())/100, cseIndirectMaxVal=float(self.jslsIndirectCustom.get()), percentTraversedRandomMaxVal=float(self.percentTraversedRandomCustom.get()))

        useDirectSwimV = self.useDirectSwim.get()
        useFocalSearchV = self.useFocalSearch.get()
        useDirectedSearchV = self.useDirectedSearch.get()
        useScanningV = self.useScanning.get()
        useChainingV = self.useChaining.get()
        useRandomV = self.useRandom.get()
        useIndirectV = self.useIndirect.get()
        useThigmoV = self.useThigmo.get()
        try:
            with open('customobjs.pickle', 'wb') as f:
                pickle.dump([cseMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, corridorAverageMinVal, directedSearchMaxDistance, focalMinDistance, focalMaxDistance, corridorCseMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, chainingMaxCoverage, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, thigmoMinDistance, innerWallMaxVal, outerWallMaxVal, cseIndirectMaxVal, percentTraversedRandomMaxVal, useDirectSwimV, useFocalSearchV, useDirectedSearchV, useScanningV, useChainingV, useRandomV, useIndirectV, useThigmoV], f)
        except:
            pass
        try:
            self.top.destroy()
        except:
            pass

    def mainThreader(self):  # start the threaded execution
        logging.debug("Threading")

        try:
            t1 = threading.Thread(target=self.mainCalculate)  # create a thread for the main function
            t1.start()  # start that thread
            logging.debug("Threading mainCalculate thread started")
        except Exception:
            logging.critical("Fatal error in mainCalculate")  # couldnt be started

    def find_files(self, directory, pattern):  # searches for our files in the directory
        logging.debug("Finding files in the directory")
        for root, dirs, files in os.walk(directory):
            for basename in sorted(files):
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename

    def plotPoints(self, x, y, poolDiam, centreX, centreY, platX, platY, scalingFactor, name, title, platEstDiam):  # function to graph the data for the not recognized trials
        wallsX = []
        wallsY = []
        platWallsX = []
        platWallsY = []
        for theta in range(0,360):
            wallsX.append(centreX + ((math.ceil(poolDiam) / 2)) * math.cos(math.radians(theta)))
            wallsY.append(centreY + ((math.ceil(poolDiam) / 2)) * math.sin(math.radians(theta)))

        for theta in range(0,360):
            platWallsX.append(platX + ((math.ceil(platEstDiam) / 2)+1) * math.cos(math.radians(theta)))
            platWallsY.append(platY + ((math.ceil(platEstDiam) / 2)+1) * math.sin(math.radians(theta)))

        plotName = "plots/" + name + " " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # the name will be Animal id followed by the date and time
        plt.scatter(x, y, s=15, c='r', alpha=1.0)  # we plot the XY position of animal
        plt.scatter(x[0],y[0], s=100, c='b', alpha=1, marker='s')  # we plot the start point
        plt.scatter(platWallsX, platWallsY, s=1, c='black', alpha=1.0)  # we plot the platform
        plt.scatter(centreX, centreY, s=100, c='g', alpha=1.0)  # we plot the centre
        plt.scatter(wallsX, wallsY, s=15, c='black', alpha=0.3)
        plt.title(title)  # add the title
        plt.xlim(centreX-poolDiam/2-15, centreX+poolDiam/2+15)  # set the size to be the center + radius + 30
        plt.ylim(centreY-poolDiam/2-15, centreY+poolDiam/2+15)

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
        Label(self.top2, text="Platform and Walls", bg="black", fg="white", width=15).grid(row=2, column=2, padx=3)
        Label(self.top2, text="Pool centre", bg="green", fg="white", width=15).grid(row=2, column=3, padx=3)
        Label(self.top2, text="Path", bg="red", fg="white", width=15).grid(row=2, column=4, padx=3)

        self.directRadio = Radiobutton(self.top2, text="(1) Direct Swim", variable=searchStrategyStringVar, value="Direct swim (m)",
                                       indicatoron=0, width=15, bg="white")
        self.directRadio.grid(row=3, column=0, columnspan = 7, pady=3)  # add the radiobuttons for selection

        self.focalRadio = Radiobutton(self.top2, text="(2) Focal Search", variable=searchStrategyStringVar, value="Focal Search (m)",
                                      indicatoron=0, width=15, bg="white")
        self.focalRadio.grid(row=4, column=0, columnspan = 7, pady=3)
        self.directedRadio = Radiobutton(self.top2, text="(3) Directed Search", variable=searchStrategyStringVar,
                                         value="Directed Search (m)", indicatoron=0, width=15, bg="white")
        self.directedRadio.grid(row=5, column=0, columnspan = 7, pady=3)
        self.spatialRadio = Radiobutton(self.top2, text="(4) Spatial Indirect", variable=searchStrategyStringVar,
                                        value="Spatial Indirect (m)", indicatoron=0, width=15, bg="white")
        self.spatialRadio.grid(row=6, column=0, columnspan = 7, pady=3)
        self.chainingRadio = Radiobutton(self.top2, text="(5) Chaining", variable=searchStrategyStringVar, value="Chaining (m)",
                                         indicatoron=0, width=15, bg="white")
        self.chainingRadio.grid(row=7, column=0, columnspan = 7, pady=3)
        self.scanningRadio = Radiobutton(self.top2, text="(6) Scanning", variable=searchStrategyStringVar, value="Scanning (m)",
                                         indicatoron=0, width=15, bg="white")
        self.scanningRadio.grid(row=8, column=0, columnspan = 7, pady=3)
        self.randomRadio = Radiobutton(self.top2, text="(7) Random Search", variable=searchStrategyStringVar, value="Random Search (m)",
                                       indicatoron=0, width=15, bg="white")
        self.randomRadio.grid(row=9, column=0, columnspan = 7, pady=3)
        self.thigmoRadio = Radiobutton(self.top2, text="(8) Thigmotaxis", variable=searchStrategyStringVar, value="Thigmotaxis (m)",
                                       indicatoron=0, width=15, bg="white")
        self.thigmoRadio.grid(row=10, column=0, columnspan=7, pady=3)
        self.notRecognizedRadio = Radiobutton(self.top2, text="(9) Not Recognized", variable=searchStrategyStringVar, value="Not Recognized (m)",
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

    def guiHeatmap(self, experiment):

        self.top3 = Toplevel(root)  # create a new toplevel window
        self.top3.configure(bg="white")
        self.top3.geometry('{}x{}'.format( 500, 1000 ))
        Label(self.top3, text="Heatmap Parameters", bg="white", fg="black", width=15).pack()  # add a title

        self.gridSizeL = Label(self.top3, text="Grid Size:", bg="white")
        self.gridSizeL.pack(side=TOP)
        self.gridSizeE = Entry(self.top3, textvariable=gridSizeStringVar)
        self.gridSizeE.pack(side=TOP)

        self.maxValL = Label(self.top3, text="Maximum Value:", bg="white")
        self.maxValL.pack(side=TOP)
        self.maxValE = Entry(self.top3, textvariable=maxValStringVar)
        self.maxValE.pack(side=TOP)

        Button(self.top3, text="Generate", command=lambda: self.heatmap(experiment), fg="black", bg="white").pack()


    def heatmap(self, experiment):
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

        for aTrial in experiment:  # for all the files we find
            theStatus.set("Running " + theFile)
            for row in aTrial:
                # Create data
                if row.x == "-" or row.y == "-":
                    continue
                x.append(float(row.x))
                y.append(float(row.y))

                if row.x < xMin:
                    xMin = row.x
                if row.y < yMin:
                    yMin = row.y
                if row.x > xMax:
                    xMax = row.x
                if row.y > yMax:
                    yMax = row.y

        # x = np.zeros(math.ceil(xMax-xMin+1))
        # y = np.zeros(math.ceil(yMax-yMin+1))

        # for aTrial in experiment:  # for all the files we find
        #     for row in aTrial:
        #         # Create data
        #         if row.x == "-" or row.y == "-":
        #             continue
        #         x[math.floor(row.x)] += 1/len(experiment)
        #         y[math.floor(row.y)] += 1/len(experiment)

        aFileName = "heatmaps/heatmap " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # name of the log file for the run
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
        heatmap, xedges, yedges = np.histogram2d(X, Y, bins=(30, 30))
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

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


        plt.axis([xMin, xMax, yMin, yMax])
        try:
            plt.gca().set_aspect('equal')
        except:
            pass
        logging.debug("Heatmap generated")
        theStatus.set("Waiting for user input...")
        self.updateTasks()

        plt.title(aTitle)
        cb = plt.colorbar()
        photoName = aFileName + ".png"  # image name the same as plotname
        plt.savefig(photoName, dpi=300, figsize=(3,3))  # save the file
        plt.show()


    def updateTasks(self):  # called when we want to push an update to the GUI
        try:
            root.update_idletasks()
            root.update()  # update the gui
        except:
            logging.info("Couldn't update the GUI")


    def csvDestroy(self):
        try:  # try to remove the csv display (for second run)
            theStatus.set('Loading...')
            self.updateTasks()
            frame.grid_forget()
            canvas.grid_forget()
            frame.destroy()
            canvas.destroy()
            vsb.destroy()
            xscrollbar.destroy()
            logging.info("Loaded")
        except:
            logging.debug("Failed to load")

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

    def calculateEntropy(self, theTrial, platformX, platformY):
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

        entropyResult = eng.Entropy(xList,yList,platformX,platformY)
        return entropyResult

    def getAutoLocations(self, theExperiment, platformX, platformY, platformPosVar, poolCentreX, poolCentreY, poolCentreVar, poolDiamVar, software):
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
        poolCentreEstX = 0.0
        poolCentreEstY = 0.0
        poolRadius = 0.0
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

        if platformPosVar != "Auto" and platformPosVar != "auto" and platformPosVar != "automatic" and platformPosVar != "Automatic" and platformPosVar != "":  # if we want manual platform
            platformX, platformY = platformPosVar.split(",")
            platformX = float(platformX)
            platformY = float(platformY)
            logging.debug("Platform position set manually: "+str(platformPosVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get platform position from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:  # automatic platform calculation
            platFlag = True
            autoParams.append("platform position")

        if platformDiamVar != "Auto" and platformDiamVar != "auto" and platformDiamVar != "automatic" and platformDiamVar != "Automatic" and platformDiamVar != "":  # if we want manual platform diameter
            platEstDiam = platformDiamVar
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get platform position from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:
            platDiamFlag = True
            autoParams.append("platform diameter")


        if poolCentreVar != "Auto" and poolCentreVar != "auto" and poolCentreVar != "automatic" and poolCentreVar != "Automatic" and poolCentreVar != "":  # manual pool center
            poolCentreX, poolCentreY = poolCentreVar.split(",")
            poolCentreX = float(poolCentreX)
            poolCentreY = float(poolCentreY)
            logging.debug("Pool centre set manually: "+str(poolCentreVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get pool centre from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:  # automatic pool centre
            centreFlag = True
            autoParams.append("centre position")

        if poolDiamVar != "Auto" and poolDiamVar != "auto" and poolDiamVar != "automatic" and poolDiamVar != "Automatic" and poolDiamVar != "":  # manual diameter
            poolRadius = float(poolDiamVar) / 2.0
            logging.debug("Pool diameter set manually: " + str(poolDiamVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Tried to get diameter from single trial")
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter values for a single trial')
            return
        else:  # automatic diameter
            diamFlag = True
            autoParams.append("pool diameter")

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
                        "Unable to determine a centre position and pool diameter. Compatible trials: 0")
                    messagebox.showwarning('Centre and Diameter Error',
                                           'We were unable to determine a centre position or pool diameter from the trials')
                elif diamFlag:
                    logging.error("Unable to determine the pool diameter. Compatible trials: 0")
                    messagebox.showwarning('Diameter Error',
                                           'We were unable to determine a diameter from the trials')
                theStatus.set('Waiting for user input...')
                self.updateTasks()
                return

        if count < 1 and platFlag:
            logging.error("Unable to determine a platform posititon. Compatible trials: " + str(count))
            messagebox.showwarning('Platform Error',
                                   'We were unable to determine a platform position from the trials')
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            return

        if centreFlag:  # if we want an automatic centre position
            avMaxX = avMaxX / centreCount  # get the average of the max X
            avMaxY = avMaxY / centreCount  # max Y
            avMinX = avMinX / centreCount  # min X
            avMinY = avMinY / centreCount  # min Y
            poolCentreEstX = (avMaxX + avMinX) / 2  # estmiate the centre
            poolCentreEstY = (avMaxY + avMinY) / 2
            poolCentreX = poolCentreEstX
            poolCentreY = poolCentreEstY
            logging.info("Automatic pool centre calculated as: " + str(poolCentreEstX) + ", " + str(poolCentreEstY))
            print("Automatic pool centre calculated as: " + str(poolCentreEstX) + ", " + str(poolCentreEstY))

        if platFlag:  # automatic platform
            platEstX = platEstX / count
            platEstY = platEstY / count
            platformX = platEstX
            platformY = platEstY
            logging.info("Automatic platform position calculated as: " + str(platEstX) + ", " + str(platEstY))
            print("Automatic platform position calculated as: " + str(platEstX) + ", " + str(platEstY))
        if platDiamFlag:
            platEstDiam = ((platMaxX-platMinX) + (platMaxY-platMinY))/2
            if platEstDiam > 15 or platEstDiam < 5:
                platEstDiam = 10
            logging.info("Automatic platform diameter calculated as: " + str((math.ceil(float(platEstDiam)))))
            print("Automatic platform diameter calculated as: " + str((math.ceil(float(platEstDiam)))))
        if diamFlag:  # automatic diameter
            poolDiamEst = ((abs(absMaxX) + abs(absMinX)) + (abs(absMaxY) + abs(absMinY))) / 2
            logging.info("Automatic pool diameter calculated as: " + str(poolDiamEst))
            print("Automatic pool diameter calculated as: " + str(poolDiamEst))
            poolDiamVar = poolDiamEst
            poolRadius = float(poolDiamVar) / 2
        print("Pool Centre calculated as: ",poolCentreX,poolCentreY)
        return (poolCentreX,poolCentreY,platformX,platformY,poolDiamVar,poolRadius, platEstDiam)


    def calculateValues(self, theTrial, platformX, platformY, poolCentreX, poolCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone, biggerWallZone, scalingFactor, poolradius):
        global oldPlatformPosVar
        global poolCentreVar
        global useEntropyFlag
        theStatus.set("Calculating Search Strategies: " + str(theTrial))

        i = 0
        totalDistance = 0.0
        latency = 0.0
        mainLatency = 0.0
        xSummed = 0.0
        ySummed = 0.0
        xAv = 0.0
        yAv = 0.0
        currentDistanceFromPlatform = 0.0
        distanceFromPlatformSummed = 0.0
        distanceAverage = 0.0
        aX = 0.0
        aY = 0.0

        missingData = 0

        distanceToCenterOfPool = 0.0
        totalDistanceToCenterOfPool = 0.0
        averageDistanceToCentre = 0.0

        innerWallCounter = 0.0
        outerWallCounter = 0.0
        annulusCounter = 0.0
        currentHeadingError = 0.0
        distanceToSwimPathCentroid = 0.0
        totalDistanceToSwimPathCentroid = 0.0
        averageDistanceToSwimPathCentroid = 0.0

        distanceToOldPlatform = 0.0
        totalDistanceToOldPlatform = 0.0
        averageDistanceToOldPlatform = 0.0

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
        theGridSize = float(poolradius*2)/10.0
        Matrix = [[0 for x in range(0, math.ceil(theGridSize)+1)] for y in range(0, math.ceil(theGridSize)+1)]

        for aDatapoint in theTrial:  # for each row in our sheet
            if i == 0:
                startX = aDatapoint.getx()
                startY = aDatapoint.gety()
                startTime = aDatapoint.gettime()

            # Swim Path centroid
            i += 1.0
            mainLatency = aDatapoint.gettime()
            xSummed += float(aDatapoint.getx())
            ySummed += float(aDatapoint.gety())
            aX = float(aDatapoint.getx())
            aY = float(aDatapoint.gety())
            arrayX.append(aX)
            arrayY.append(aY)
            # Average Distance
            currentDistanceFromPlatform = math.sqrt((platformX - aX) ** 2 + (platformY - aY) ** 2)*scalingFactor

            #print(currentDistanceFromPlatform)


            # in zones
            distanceCenterToPlatform = math.sqrt((poolCentreX - platformX) ** 2 + (poolCentreY - platformY) ** 2)*scalingFactor
            annulusZoneInner = distanceCenterToPlatform - (chainingRadius / 2)
            annulusZoneOuter = distanceCenterToPlatform + (chainingRadius / 2)
            distanceToCenterOfPool = math.sqrt((poolCentreX - aX) ** 2 + (poolCentreY - aY) ** 2)*scalingFactor
            totalDistanceToCenterOfPool += distanceToCenterOfPool
            distanceFromStartToPlatform = math.sqrt((platformX - startX) ** 2 + (platformY - startY) ** 2)*scalingFactor

            distance = math.sqrt(abs(oldX - aX) ** 2 + abs(oldY - aY) ** 2)*scalingFactor
            distanceFromPlatformSummed += currentDistanceFromPlatform
            totalDistance += distance
            oldX = aX
            oldY = aY

            if distanceToCenterOfPool > biggerWallZone:  # calculate if we are in zones
                innerWallCounter += 1.0
            if distanceToCenterOfPool > smallerWallZone:
                outerWallCounter += 1.0
            if (distanceToCenterOfPool >= annulusZoneInner) and (distanceToCenterOfPool <= annulusZoneOuter):
                annulusCounter += 1.0

            a, b = 0, 0

            # grid creation
            # x values
            # <editor-fold desc="Grid">
            gridCounter = 0
            storeX = aDatapoint.getx()
            storeY = aDatapoint.gety()

            for step in range(-math.ceil(theGridSize/2),math.ceil(theGridSize/2)):
                if storeX >= poolCentreX+(step*theGridSize/2) and storeX <= poolCentreX+((step+1)*theGridSize/2):
                    a = gridCounter
                if storeY >= poolCentreY+(step*theGridSize/2) and storeY <= poolCentreY+((step+1)*theGridSize/2):
                    b = gridCounter
                gridCounter += 1

            Matrix[a][b] = 1  # set matrix cells to 1 if we have visited them
            if (poolCentreX - aX) != 0:
                centerArcTangent = math.degrees(math.atan((poolCentreY - aY) / (poolCentreX - aX)))

            # print centerArcTangent
            if aDatapoint.getx() >= poolCentreX and aDatapoint.gety() >= poolCentreY:
                quadrantOne = 1
            elif aDatapoint.getx() < poolCentreX and aDatapoint.gety() >= poolCentreY:
                quadrantTwo = 1
            elif aDatapoint.getx() >= poolCentreX and aDatapoint.gety() < poolCentreY:
                quadrantThree = 1
            elif aDatapoint.getx() < poolCentreX and aDatapoint.gety() < poolCentreY:
                quadrantFour = 1

            latency = aDatapoint.gettime()

        quadrantTotal = quadrantOne + quadrantTwo + quadrantThree + quadrantFour

        xAv = xSummed / i  # get our average positions for the centroid
        yAv = ySummed / i
        swimPathCentroid = (xAv, yAv)


        startPoint = np.array([startX,startY])
        platformPoint = np.array([platformX,platformY])

        startToPlatVector = platformPoint-startPoint


        aArcTangent = math.degrees(math.atan((platformY - startY) / (platformX - startX)))
        upperCorridor = aArcTangent + corridorWidth
        lowerCorridor = aArcTangent - corridorWidth
        corridorWidth = 0.0
        totalHeadingError = 0.0
        initialHeadingError = 0.0
        initialHeadingErrorCount = 0
        for aDatapoint in theTrial:  # go back through all values and calculate distance to the centroid
            distanceToSwimPathCentroid = math.sqrt((xAv - aDatapoint.getx()) ** 2 + (yAv - aDatapoint.gety()) ** 2)*scalingFactor
            totalDistanceToSwimPathCentroid += distanceToSwimPathCentroid
            distanceFromStartToCurrent = math.sqrt((aDatapoint.getx() - startX) **2 + (aDatapoint.gety() - startY)**2)*scalingFactor

            if oldItemX!=0 and aDatapoint.getx() - oldItemX != 0 and aDatapoint.getx() - startX != 0:
                currentToPlat = np.subtract(np.array([platformX, platformY]),np.array([aDatapoint.getx(), aDatapoint.gety()]))
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
        # </editor-fold>
        # <editor-fold desc="Take Averages">
        corridorAverage = corridorCounter / i
        distanceAverage = distanceFromPlatformSummed / i  # calculate our average distances to landmarks
        averageDistanceToSwimPathCentroid = totalDistanceToSwimPathCentroid / i
        averageDistanceToOldPlatform = totalDistanceToOldPlatform / i
        averageDistanceToCentre = totalDistanceToCenterOfPool / i
        averageHeadingError = totalHeadingError / i
        try:
            averageInitialHeadingError = initialHeadingError/initialHeadingErrorCount
        except:
            averageInitialHeadingError = 0
        ''' for the next 3 weeks work harder, be impressive, you're good at this and can make it work
        
        corridorAverage = corridorCounter /i
        distance Average - distance From PlatformSummed/i
        averageDistanceToSwimPathCentroid = totalDistanceToSwimPathCentroid/i
        averageInitialHeadingError'''
        cellCounter = 0.0  # initialize our cell counter

        for k in range(0, math.ceil(theGridSize)+1):  # count how many cells we have visited
            for j in range(0, math.ceil(theGridSize)+1):
                try:
                    if Matrix[k][j] == 1:
                        cellCounter += 1.0
                except:
                    continue

        # print distanceTotal/(i/25), avHeadingError
        percentTraversed = (cellCounter / (math.ceil(gridCounter**2) * scalingFactor)) * 100.0  # turn our count into a percentage over how many cells we can visit


        idealDistance = distanceFromStartToPlatform
        if latency != 0:
            try:
                velocity = (totalDistance/latency)
            except:
                velocity = 0
                pass
        idealCumulativeDistance = 0.0

        sampleRate = (theTrial.datapointList[-1].gettime() - startTime)/(len(theTrial.datapointList) - 1)
        while idealDistance > 10.0:
            idealCumulativeDistance += idealDistance
            idealDistance = (idealDistance - velocity*sampleRate)
            if(idealCumulativeDistance > 10000):
                break
        cse = float(distanceFromPlatformSummed - idealCumulativeDistance)*sampleRate

        if useEntropyFlag:
            entropyResult = self.calculateEntropy(theTrial,platformX,platformY)
        else:
            entropyResult = False
        return corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToOldPlatform, averageDistanceToCentre, averageHeadingError, percentTraversed, quadrantTotal, totalDistance, mainLatency, innerWallCounter, outerWallCounter, annulusCounter, i, arrayX, arrayY, velocity, cse, averageInitialHeadingError, entropyResult
    def mainCalculate(self):
        global softwareStringVar
        logging.debug("Calculate Called")
        self.updateTasks()
        self.csvDestroy()
        theStatus.set("Initializing")

        platformPosVar = platformPosStringVar.get()
        platformDiamVar = platformDiamStringVar.get()
        poolDiamVar = poolDiamStringVar.get()
        poolCentreVar = poolCentreStringVar.get()
        oldPlatformPosVar = oldPlatformPosStringVar.get()
        corridorWidthVar = corridorWidthStringVar.get()
        chainingRadiusVar = chainingRadiusStringVar.get()
        thigmotaxisZoneSizeVar = thigmotaxisZoneSizeStringVar.get()  # get important values
        softwareScalingFactorVar = softwareScalingFactorStringVar.get()

        try:
            with open('mainobjs.pickle', 'wb') as f:
                pickle.dump([platformPosVar, platformDiamVar, poolDiamVar, poolCentreVar, oldPlatformPosVar, corridorWidthVar, chainingRadiusVar, thigmotaxisZoneSizeVar, softwareScalingFactorVar], f)
        except:
            pass

        # basic setup

        cseMaxVal = params.cseMaxVal
        headingMaxVal = params.headingMaxVal
        distanceToSwimMaxVal = params.distanceToSwimMaxVal
        distanceToPlatMaxVal = params.distanceToPlatMaxVal
        corridorAverageMinVal = params.corridorAverageMinVal
        corridorCseMaxVal = params.corridorCseMaxVal
        annulusCounterMaxVal = params.annulusCounterMaxVal
        quadrantTotalMaxVal = params.quadrantTotalMaxVal
        percentTraversedMaxVal = params.percentTraversedMaxVal
        percentTraversedMinVal = params.percentTraversedMinVal
        distanceToCentreMaxVal = params.distanceToCentreMaxVal
        innerWallMaxVal = params.innerWallMaxVal
        outerWallMaxVal = params.outerWallMaxVal
        cseIndirectMaxVal = params.cseIndirectMaxVal
        percentTraversedRandomMaxVal = params.percentTraversedRandomMaxVal
        focalMinDistance = params.focalMinDistance
        focalMaxDistance = params.focalMaxDistance
        chainingMaxCoverage = params.chainingMaxCoverage
        thigmoMinDistance = params.thigmoMinDistance
        directedSearchMaxDistance = params.directedSearchMaxDistance


        poolRadius = 0.0
        thigmotaxisZoneSize = 0.0
        corridorWidth = 0.0
        platformX = 0.0
        platformY = 0.0
        oldDay = ""
        oldPlatformX = platformX
        oldPlatformY = platformY
        chainingRadius = 0.0
        poolCentre = (0.0, 0.0)
        poolRadius = 0.0
        smallerWallZone = 0.0
        biggerWallZone = 0.0
        distanceCenterToPlatform = 0.0
        totalTrialCount = 0.0
        thigmotaxisCount = 0.0
        randomCount = 0.0
        scanningCount = 0.0
        chainingCount = 0.0
        directSearchCount = 0.0
        focalSearchCount = 0.0
        directSwimCount = 0.0
        spatialIndirectCount = 0.0
        notRecognizedCount = 0.0
        n = 0
        numOfRows = 0
        poolCentreX, poolCentreY = poolCentre
        flag = False
        dayFlag = False
        autoFlag = False
        skipFlag = False
        software = softwareStringVar.get()

        try:
            aExperiment = saveFileAsExperiment(software, theFile, fileDirectory)
        except Exception as e:
            show_error("No Input")
            print("Unexpected Error: " + str(e))
            return
        if software == "ethovision":
            logging.info("Extension set to xlsx")
            extensionType = r'*.xlsx'
            softwareScalingFactorVar = 1.0
        elif software == "anymaze":
            extensionType = r'*.csv'
            logging.info("Extension set to csv")
            softwareScalingFactorVar = 1.0/float(softwareScalingFactorVar)
        elif software == "watermaze":
            extensionType = r'*.csv'
            logging.info("Extension set to csv")
            softwareScalingFactorVar = 1.0/float(softwareScalingFactorVar)

        poolCentreX, poolCentreY, platformX, platformY, poolDiamVar, poolRadius, platEstDiam = self.getAutoLocations(aExperiment, platformX, platformY, platformPosVar, poolCentreX, poolCentreY, poolCentreVar, poolDiamVar, software)
        if scale:
            scalingFactor = softwareScalingFactorVar
        else:
            scalingFactor = 1.0

        thigmotaxisZoneSize = float(thigmotaxisZoneSizeVar) * scalingFactor # update the thigmotaxis zone
        chainingRadius = float(chainingRadiusVar) * scalingFactor # update the chaining radius
        corridorWidth = (int(corridorWidthVar) / 2) * scalingFactor # update the corridor width

        smallerWallZone = poolRadius - math.ceil(thigmotaxisZoneSize / 2)  # update the smaller wall zone
        biggerWallZone = poolRadius - thigmotaxisZoneSize  # and bigger wall zone

        theStatus.set('Calculating Search Strategies...')  # update status bar
        self.updateTasks()

        logging.debug("Calculating search strategies")
        try:  # try to open a csv file for output
            f = open(outputFile, 'wt')
            writer = csv.writer(f, delimiter=',', quotechar='"')
        except:
            logging.error("Cannot write to " + str(outputFile))
            return

        headersToWrite = []
        if aExperiment.hasDateInfo:
            headersToWrite.extend(["Date", "Time", "Day"])
        
        headersToWrite.append("Trial")
        if aExperiment.hasTrialNames:
            headersToWrite.append("Name")
        if aExperiment.hasAnimalNames:
            headersToWrite.append("Animal")

        headersToWrite.extend(["Trial Code", "Strategy Type", "CSE", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage", "score", "initial heading error", "entropy"])
        writer.writerow(headersToWrite) # write to the csv

        dayNum = 0
        trialNum = {}
        curDate = None 
        for aTrial in aExperiment:
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

            xSummed = 0.0
            ySummed = 0.0
            xAv = 0.0
            yAv = 0.0

            currentDistanceFromPlatform = 0.0
            distanceAverage = 0.0
            aX = 0.0
            aY = 0.0

            distanceToCenterOfPool = 0.0
            totalDistanceToCenterOfPool = 0.0
            averageDistanceToCentre = 0.0

            innerWallCounter = 0.0
            outerWallCounter = 0.0
            annulusCounter = 0.0

            distanceToSwimPathCentroid = 0.0
            totalDistanceToSwimPathCentroid = 0.0
            averageDistanceToSwimPathCentroid = 0.0

            distanceToOldPlatform = 0.0
            totalDistanceToOldPlatform = 0.0
            averageDistanceToOldPlatform = 0.0

            cse = 0.0

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
            corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToOldPlatform, averageDistanceToCentre, averageHeadingError, percentTraversed, quadrantTotal, totalDistance, latency, innerWallCounter, outerWallCounter, annulusCounter, i, arrayX, arrayY, velocity, cse, initialHeadingError, entropyResult = self.calculateValues(
                aTrial, platformX, platformY, poolCentreX,
                poolCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone,
                biggerWallZone, scalingFactor, poolRadius)

            strategyType = ""
            # DIRECT SWIM
            if cse <= cseMaxVal and averageHeadingError <= headingMaxVal and isRuediger == False and useDirectSwimV:  # direct swim
                directSwimCount += 1.0
                score = 3
                strategyType = "Direct Swim"
            # FOCAL SEARCH
            elif averageDistanceToSwimPathCentroid < (
                    poolRadius * distanceToSwimMaxVal) and distanceAverage < (
                    distanceToPlatMaxVal * poolRadius) and totalDistance < focalMaxDistance and totalDistance > focalMinDistance and useFocalSearchV:  # Focal Search
                focalSearchCount += 1.0
                score = 2
                strategyType = "Focal Search"
            # DIRECTED SEARCH
            elif corridorAverage >= corridorAverageMinVal and cse <= corridorCseMaxVal and totalDistance < directedSearchMaxDistance and useDirectedSearchV:  # directed search
                directSearchCount += 1.0
                score = 2
                strategyType = "Directed Search"
            # spatial INDIRECT
            elif cse < cseIndirectMaxVal and useIndirectV:  # Near miss
                strategyType = "Spatial Indirect"
                score = 2
                spatialIndirectCount += 1.0
            # CHAINING
            elif float(
                    annulusCounter / i) > annulusCounterMaxVal and quadrantTotal >= quadrantTotalMaxVal and percentTraversed < chainingMaxCoverage and useChainingV:  # or 4 chaining
                chainingCount += 1.0
                score = 1
                strategyType = "Chaining"
            # SCANNING
            elif percentTraversedMinVal <= percentTraversed >= percentTraversedMaxVal and averageDistanceToCentre <= (
                    distanceToCentreMaxVal * poolRadius) and useScanningV:  # scanning
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
                    print("Day #", "Trial #", "Name", "Date", "Trial", "Strategy Type", "CSE", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage")
                    print(dayNum, trialNum, aTrial.name, aTrial.date, aTrial.trial, strategyType, round(cse,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2))
                    #print("CSE: ", cse, " Distance to centroid: ", averageDistanceToSwimPathCentroid, " Distance to plat: ", distanceAverage)
                    plotName = "Strategy " + str(strategyType) + " Animal " + str(animal) + "  Day " + str(dayNum) + " Trial " + str(trialNum[animal])
                    self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY),
                                float(platformX), float(platformY), float(scalingFactor), plotName,
                                    ("Animal: " + str(animal) + "  Day/Trial: " + str(dayNum) + "/" + str(trialNum[animal])), float(platEstDiam))  # ask user for answer
                    root.wait_window(self.top2)  # we wait until the user responds
                    strategyType = searchStrategyV  # update the strategyType to that of the user
                    try:  # try and kill the popup window
                        self.top2.destroy()
                    except:
                        pass

            totalTrialCount += 1.0

            n += 1
            print("CSE: ", cse, "    Heading: ",averageHeadingError, " Entropy: ", entropyResult)

            if useManualForAllFlag:
                print("Day #", "Trial #", "Name", "Date", "Trial", "Strategy Type", "CSE", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage")
                print(dayNum, trialNum[animal], aTrial.name, aTrial.date, aTrial.trial, strategyType, round(cse,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2))
                plotName = "Strategy " + str(strategyType) + " Animal " + str(animal) + "  Day " + str(dayNum) + " Trial " + str(trialNum[animal])
                self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY),
                                float(platformX), float(platformY), float(scalingFactor), plotName,
                                ("Animal: " + str(animal) + "  Day/Trial: " + str(dayNum) + "/" + str(trialNum[animal])), float(platEstDiam))  # ask user for answer
                root.wait_window(self.top2)  # we wait until the user responds
                strategyType = searchStrategyV  # update the strategyType to that of the user

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
                [(str(aTrial.animal) + " " + str(dayNum) + " " + str(trialNum[animal])), strategyType, round(cse, 2), round(velocity, 2), round(totalDistance, 2), round(distanceAverage, 2),
                 round(averageHeadingError, 2), round(percentTraversed, 2), round(latency, 2),
                 round(corridorAverage, 2), score, initialHeadingError, round(entropyResult, 2)])
            writer.writerow(dataToWrite)  # writing to csv file

            f.flush()

        print("Direct Swim: ", directSwimCount, "| Directed Search: ", directSearchCount, "| Focal Search: ", focalSearchCount, "| Spatial Indirect: ", spatialIndirectCount, "| Chaining: ", chainingCount, "| Scanning: ", scanningCount, "| Random Search: ", randomCount, "| Thigmotaxis: ", thigmotaxisCount, "| Not Recognized: ", notRecognizedCount)
        theStatus.set('Updating CSV...')
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', outputFile))
        elif os.name == 'nt': # For Windows
            os.startfile(outputFile)
        elif os.name == 'posix': # For Linux, Mac, etc.
            subprocess.call(('xdg-open', outputFile))
        self.updateTasks()
        theStatus.set('')
        self.updateTasks()
        csvfilename = "results/results " + str(strftime("%Y_%m_%d %I_%M_%S_%p",
                                            localtime())) + ".csv"  # update the csv file name for the next run
        outputFileStringVar.set(csvfilename)

        try:
            t1.join()
            t2.join()
        except:
            return

def main():
    b = mainClass(root)  # start the main class (main program)
    root.mainloop()  # loop so the gui stays

if __name__ == "__main__":  # main part of the program -- this is called at runtime
    main()
