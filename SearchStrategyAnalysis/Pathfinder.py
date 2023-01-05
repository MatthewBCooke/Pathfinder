#!/usr/bin/env python

"""Pathfinder.py"""

from __future__ import print_function
import csv
import fnmatch
import logging
import math
import os, subprocess, sys
import webbrowser
import statistics
from collections import defaultdict
from sys import platform as _platform
from time import localtime, strftime
import PIL.Image
from PIL import ImageTk
#from xlrd import open_workbook
from functools import partial
import numpy as np
import pickle
import datetime
import scipy.ndimage as sp
import pandas as pd


try:  # Tries to import local dependencies
    from SearchStrategyAnalysis.appTrial import Trial, Experiment, Parameters, saveFileAsExperiment, Datapoint, defineOwnSoftware
    import SearchStrategyAnalysis.heatmap
    
except:
    from appTrial import Trial, Experiment, Parameters, saveFileAsExperiment, Datapoint, \
        defineOwnSoftware
    import heatmap
from scipy.stats import norm
import re
import traceback

try:  # Imports MATLAB engine if available
    import matlab.engine

    canUseMatlab = True
except:  # Notify user that MATLAB is unavailable
    print("MATLAB Engine Unavailable")
    canUseMatlab = False

if sys.version_info < (3, 0, 0):  # tkinter names for python 2
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
logging.basicConfig(filename=logfilename, level=logging.DEBUG)  # set the default log type to INFO, can be set to DEBUG for more detailed information
csvfilename = "output/results/results " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # name of the default results file
theFile = ""
fileDirectory = ""
goalPosVar = "0,0"
mazeDiamVar = "300"
goalDiamVar = "10"
corridorWidthVar = "40"
mazeCentreVar = "0,0"
chainingRadiusVar = "25"
thigmotaxisZoneSizeVar = "15"
outputFile = csvfilename
fileFlag = 0
probeCutVar = math.inf  # stop probe trials at X seconds, inf = no cutoff

defaultParams = Parameters(name="Default", ipeMaxVal=125, headingMaxVal=40, distanceToSwimMaxVal=30,
                           distanceToPlatMaxVal=30, distanceToSwimMaxVal2=50, distanceToPlatMaxVal2=50,
                           corridorAverageMinVal=70, directedSearchMaxDistance=400,
                           focalMinDistance=100, focalMaxDistance=400, semiFocalMinDistance=0, semiFocalMaxDistance=500,
                           corridoripeMaxVal=1500,
                           annulusCounterMaxVal=90, quadrantTotalMaxVal=4, chainingMaxCoverage=40,
                           percentTraversedMaxVal=20,
                           percentTraversedMinVal=5, distanceToCentreMaxVal=60, thigmoMinDistance=400,
                           fullThigmoMinVal=65,
                           smallThigmoMinVal=35, ipeIndirectMaxVal=300, percentTraversedRandomMaxVal=10,
                           headingIndirectMaxVal=70,
                           useDirect=True, useFocal=True, useDirected=True, useIndirect=True,
                           useSemiFocal=False, useChaining=True, useScanning=True, useRandom=True, useThigmogaxis=True)

global params
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
smallThigmoMinVal = params.smallThigmoMinVal
fullThigmoMinVal = params.fullThigmoMinVal
ipeIndirectMaxVal = params.ipeIndirectMaxVal
percentTraversedRandomMaxVal = params.percentTraversedRandomMaxVal
directedSearchMaxDistance = params.directedSearchMaxDistance
focalMinDistance = params.focalMinDistance
focalMaxDistance = params.focalMaxDistance
semiFocalMinDistance = params.semiFocalMinDistance
semiFocalMaxDistance = params.semiFocalMaxDistance
chainingMaxCoverage = params.chainingMaxCoverage
thigmoMinDistanceCustom = params.thigmoMinDistance
headingIndirectMaxVal = params.headingIndirectMaxVal

customFlag = False
useDirectPathV = params.useDirect
useFocalSearchV = params.useFocal
useDirectedSearchV = params.useDirected
useScanningV = params.useScanning
useChainingV = params.useChaining
useRandomV = params.useRandom
useIndirectV = params.useIndirect
useSemiFocalSearchV = params.useSemiFocal
useThigmoV = params.useThigmotaxis

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
softwareStringVar = StringVar()
softwareStringVar.set("")
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
rois = []
destroyedroot = False

def show_message(text):  # popup box with message text
    logging.debug("Displaying message")
    try:
        top = Toplevel(root)  # show as toplevel
        Label(top, text=text).pack()  # label set to text
        Button(top, text="OK", command=top.destroy).pack(pady=5)  # add ok button
    except:
        logging.info("Couldn't Display message " + text)

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])

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

    # Helper for callDefineOwnSoftware, tracks if root has been destroyed
    def root_tracker():
        destroyedroot = True
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", root_tracker)

    def buildGUI(self, root):  # Called in the __init__ to build the GUI window
        for widget in root.winfo_children():
            widget.destroy()

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

        softwareStringVar = StringVar()
        softwareStringVar.set("auto")

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
        self.helpMenu.add_command(label="Update with PIP", command=self.updatePathfinder)

        rowCount = 0
        # ******* Software Type *******
        self.softwareBar = Frame(root)  # add a toolbar to the frame
        self.softwareBar.config(bg="white")
        #self.autoRadio = Radiobutton(self.softwareBar, text="Auto", variable=softwareStringVar, value="auto", indicatoron=1, width=15, bg="white")
        #self.autoRadio.grid(row=rowCount, column=0, padx=5, sticky='NW')  # add the radiobuttons for selection

        self.ethovisionRadio = Radiobutton(self.softwareBar, text="Ethovision", variable=softwareStringVar,
                                           value="ethovision", indicatoron=1, width=15, bg="white")
        self.ethovisionRadio.grid(row=rowCount, column=1, padx=5, sticky='NW')

        self.anymazeRadio = Radiobutton(self.softwareBar, text="Anymaze", variable=softwareStringVar,
                                        value="anymaze", indicatoron=1, width=15, bg="white")
        self.anymazeRadio.grid(row=rowCount, column=2, padx=5, sticky='NW')

        self.watermazeRadio = Radiobutton(self.softwareBar, text="Watermaze", variable=softwareStringVar,
                                          value="watermaze", indicatoron=1, width=15, bg="white")
        self.watermazeRadio.grid(row=rowCount, column=3, padx=5, sticky='NW')

        self.eztrackRadio = Radiobutton(self.softwareBar, text="ezTrack", variable=softwareStringVar,
                                        value="eztrack", indicatoron=1, width=15, bg="white")
        self.eztrackRadio.grid(row=rowCount, column=4, padx=5, sticky='NW')

        self.defineRadio = Radiobutton(self.softwareBar, text="Define", variable=softwareStringVar, value="custom",
                                       indicatoron=0, width=15, bg="white", command=self.callDefineOwnSoftware)
        self.defineRadio.grid(row=rowCount, column=5, padx=5, sticky='NW')
        self.softwareBar.pack(side=TOP, fill=X, pady=5)

        #self.autoRadio.bind("<Enter>", partial(self.on_enter, "Click for automatic detection of data-type"))
        #self.autoRadio.bind("<Leave>", self.on_leave)
        self.ethovisionRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Ethovision to generate your data"))
        self.ethovisionRadio.bind("<Leave>", self.on_leave)
        self.anymazeRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Anymaze to generate your data"))
        self.anymazeRadio.bind("<Leave>", self.on_leave)
        self.watermazeRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Watermaze to generate your data"))
        self.watermazeRadio.bind("<Leave>", self.on_leave)
        self.eztrackRadio.bind("<Enter>", partial(self.on_enter, "Click if you used ezTrack to generate your data"))
        self.eztrackRadio.bind("<Leave>", self.on_leave)
        self.defineRadio.bind("<Enter>", partial(self.on_enter, "Click if your software does not match a preset"))
        self.defineRadio.bind("<Leave>", self.on_leave)

        # ******* STATUS BAR *******
        self.status = Label(root, textvariable=theStatus, bd=1, relief=SUNKEN, anchor=W,
                            bg="white")  # setup the status bar
        self.status.pack(side=BOTTOM, anchor=W, fill=X)  # place the status bar

        # ****** PARAMETERS SIDE ******
        self.paramFrame = Frame(root, bd=1, bg="white")  # create a frame for the parameters
        self.paramFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)  # place this on the left

        try:
            with open('mainobjs.pickle', 'rb') as f:
                # goalPosVar, goalDiamVar, mazeDiamVar, mazeCentreVar, corridorWidthVar, chainingRadiusVar, thigmotaxisZoneSizeVar = pickle.load(f)
                goalPosStringVar.set(goalPosVar)
                goalDiamStringVar.set(goalDiamVar)
                mazeDiamStringVar.set(mazeDiamVar)
                mazeCentreStringVar.set(mazeCentreVar)
                corridorWidthStringVar.set(corridorWidthVar)
                chainingRadiusStringVar.set(chainingRadiusVar)
                thigmotaxisZoneSizeStringVar.set(thigmotaxisZoneSizeVar)
        except:
            pass

        rowCount = rowCount + 1
        self.goalPos = Label(self.paramFrame, text="Goal Position (x,y):", bg="white")  # add different items (Position)
        self.goalPos.grid(row=rowCount, column=0, sticky=E)  # place this in row 0 column 0
        self.goalPosE = Entry(self.paramFrame, textvariable=goalPosStringVar)  # add an entry text box
        self.goalPosE.grid(row=rowCount, column=1)  # place this in row 0 column 1
        self.goalPos.bind("<Enter>", partial(self.on_enter, "Goal position. Example: 2.5,-3.72 or Auto"))
        self.goalPos.bind("<Leave>", self.on_leave)
        self.otherROIButton = Button(self.paramFrame, text="Add Goal...", command=self.otherROI, fg="black")
        self.otherROIButton.grid(row=rowCount, column=2)  # add custom button
        self.otherROIButton.bind("<Enter>", partial(self.on_enter,
                                                    "Add more Regions of Interest to be considered in strategy calculation"))
        self.otherROIButton.bind("<Leave>", self.on_leave)
        self.otherROIButton.config(width=10)
        rowCount = rowCount + 1
        self.goalDiam = Label(self.paramFrame, text="Goal Diameter (cm):", bg="white")
        self.goalDiam.grid(row=rowCount, column=0, sticky=E)
        self.goalDiamE = Entry(self.paramFrame, textvariable=goalDiamStringVar)
        self.goalDiamE.grid(row=rowCount, column=1)
        self.goalDiam.bind("<Enter>", partial(self.on_enter, "Goal diameter. Use the same unit as the data"))
        self.goalDiam.bind("<Leave>", self.on_leave)
        rowCount = rowCount + 1
        self.mazeDiam = Label(self.paramFrame, text="Maze Diameter (cm):", bg="white")
        self.mazeDiam.grid(row=rowCount, column=0, sticky=E)
        self.mazeDiamE = Entry(self.paramFrame, textvariable=mazeDiamStringVar)
        self.mazeDiamE.grid(row=rowCount, column=1)
        self.mazeDiam.bind("<Enter>", partial(self.on_enter, "The diameter of the maze. Use the same unit as the data"))
        self.mazeDiam.bind("<Leave>", self.on_leave)
        rowCount = rowCount + 1
        self.mazeCentre = Label(self.paramFrame, text="Maze Centre (x,y):", bg="white")
        self.mazeCentre.grid(row=rowCount, column=0, sticky=E)
        self.mazeCentreE = Entry(self.paramFrame, textvariable=mazeCentreStringVar)
        self.mazeCentreE.grid(row=rowCount, column=1)
        self.mazeCentre.bind("<Enter>", partial(self.on_enter, "Maze Centre. Example: 0.0,0.0 or Auto"))
        self.mazeCentre.bind("<Leave>", self.on_leave)
        rowCount = rowCount + 1

        self.headingError = Label(self.paramFrame, text="Angular Corridor Width (degrees):", bg="white")
        self.headingError.grid(row=rowCount, column=0, sticky=E)
        self.headingErrorE = Entry(self.paramFrame, textvariable=corridorWidthStringVar)
        self.headingErrorE.grid(row=rowCount, column=1)
        self.headingError.bind("<Enter>", partial(self.on_enter,
                                                  "This is an angular corridor (in degrees) in which the animal must face"))
        self.headingError.bind("<Leave>", self.on_leave)
        rowCount = rowCount + 1

        self.chainingRadius = Label(self.paramFrame, text="Chaining Annulus Width (cm):", bg="white")
        self.chainingRadius.grid(row=rowCount, column=0, sticky=E)
        self.chainingRadiusE = Entry(self.paramFrame, textvariable=chainingRadiusStringVar)
        self.chainingRadiusE.grid(row=rowCount, column=1)
        self.chainingRadius.bind("<Enter>", partial(self.on_enter,
                                                    "The diameter of the ring in which chaining is considered (centered on goal)"))
        self.chainingRadius.bind("<Leave>", self.on_leave)

        rowCount = rowCount + 1
        self.thigmotaxisZoneSize = Label(self.paramFrame, text="Thigmotaxis Zone Size (cm):", bg="white")
        self.thigmotaxisZoneSize.grid(row=rowCount, column=0, sticky=E)
        self.thigmotaxisZoneSizeE = Entry(self.paramFrame, textvariable=thigmotaxisZoneSizeStringVar)
        self.thigmotaxisZoneSizeE.grid(row=rowCount, column=1)
        self.thigmotaxisZoneSize.bind("<Enter>", partial(self.on_enter,
                                                         "Size of the zone in which thigmotaxis is considered (from the outer wall)"))
        self.thigmotaxisZoneSize.bind("<Leave>", self.on_leave)

        rowCount = rowCount + 1
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

        rowCount = rowCount + 1
        self.manualTickL = Label(self.paramFrame, text="Manual categorization for uncategorized trials: ",
                                 bg="white")  # label for the tickbox
        self.manualTickL.grid(row=rowCount, column=0, sticky=E)  # placed here
        self.manualTickC = Checkbutton(self.paramFrame, variable=useManual, bg="white")  # the actual tickbox
        self.manualTickC.grid(row=rowCount, column=1)
        self.manualTickL.bind("<Enter>", partial(self.on_enter,
                                                 "Unrecognized strategies will popup so you can manually categorize them"))
        self.manualTickL.bind("<Leave>", self.on_leave)
        rowCount = rowCount + 1
        self.manualForAllL = Label(self.paramFrame, text="Manual categorization for all trials: ",
                                   bg="white")  # label for the tickbox
        self.manualForAllL.grid(row=rowCount, column=0, sticky=E)  # placed here
        self.manualForAllC = Checkbutton(self.paramFrame, variable=useManualForAll, bg="white")  # the actual tickbox
        self.manualForAllC.grid(row=rowCount, column=1)
        self.manualForAllL.bind("<Enter>",
                                partial(self.on_enter, "All trials will popup so you can manually categorize them"))
        self.manualForAllL.bind("<Leave>", self.on_leave)
        rowCount = rowCount + 1

        if canUseMatlab:
            self.entropyL = Label(self.paramFrame, text="Run entropy calculation: ",
                                  bg="white")  # label for the tickbox
            self.entropyL.grid(row=rowCount, column=0, sticky=E)  # placed here
            self.entropyC = Checkbutton(self.paramFrame, variable=useEntropy, bg="white")  # the actual tickbox
            self.entropyC.grid(row=rowCount, column=1)
            self.entropyL.bind("<Enter>", partial(self.on_enter, "Calculates the entropy of the trial (slow)"))
            self.entropyL.bind("<Leave>", self.on_leave)
            rowCount = rowCount + 1

        self.truncateL = Label(self.paramFrame, text="Truncate trials when animal reaches goal location: ",
                               bg="white")  # label for the tickbox
        self.truncateL.grid(row=rowCount, column=0, sticky=E)  # placed here
        self.truncateC = Checkbutton(self.paramFrame, variable=truncate, bg="white")  # the actual tickbox
        self.truncateC.grid(row=rowCount, column=1)
        self.truncateL.bind("<Enter>",
                            partial(self.on_enter, "Will end the trial onces the animal reaches the goal location."))
        self.truncateL.bind("<Leave>", self.on_leave)

        useManualForAllFlag = useManualForAll.get()
        useEntropyFlag = useEntropy.get()
        manualFlag = useManual.get()  # get the value of the tickbox
        trunacteFlag = truncate.get()
        rowCount = rowCount + 1
        self.calculateButton = Button(self.paramFrame, text="Calculate", fg="black",
                                      command=self.mainHelper, state='disabled')  # add a button that says calculate
        self.calculateButton.grid(row=rowCount, column=1, columnspan=1)
        self.settingsButton = Button(self.paramFrame, text="Settings", command=self.settings, fg="black", bg="white")
        self.settingsButton.grid(row=rowCount, column=0, columnspan=1)  # add custom button
        self.calculateButton.config(width=10)
        self.settingsButton.config(width=10)

        if _platform == "darwin":
            root.bind('<Command-d>', self.ctrlDir)
            root.bind('<Command-f>', self.ctrlFile)
        else:
            root.bind('<Control-d>', self.ctrlDir)
            root.bind('<Control-f>', self.ctrlFile)

        root.bind('<Shift-Return>', self.enterManual)

        # ****** DIAGRAM SIDE ******
        # initialize frame
        self.graphFrame = Frame(root, bd=1, bg="white")  # create a frame for the diagram
        self.graphFrame.pack(side=RIGHT, fill=BOTH, padx=5, pady=5)  # place this on the right
        canvas = Canvas(self.graphFrame, width=400, height=400)
        canvas.pack()
        def redraw(*args):
            try:
                try:
                    canvas.delete("all")
                except:
                    pass

                radius = float(mazeDiamStringVar.get()) / 2
                scale = 1 / float(2*radius/300)
                self.circle = canvas.create_oval(200 - scale * radius, 200 - scale * radius,
                                                 200 + scale * radius, 200 + scale * radius, fill="white", width=3)

                mazeX, mazeY = mazeCentreStringVar.get().split(",")
                mazeCentre = [float(mazeX) * scale, float(mazeY) * scale]

                startX, startY = 200, 200 + scale * radius
                goalX, goalY = goalPosStringVar.get().split(",")
                goalCentre = [200 + (float(goalX) * scale) - mazeCentre[0],
                              200 - (float(goalY) * scale) + mazeCentre[1]]
                goalLBorder = goalCentre[0] - scale * (float(goalDiamStringVar.get()) / 2)
                goalRBorder = goalCentre[0] + scale * (float(goalDiamStringVar.get()) / 2)
                goalTopBorder = goalCentre[1] - scale * (float(goalDiamStringVar.get()) / 2)
                goalBottomBorder = goalCentre[1] + scale * (float(goalDiamStringVar.get()) / 2)

                smallChainLBorder = 200 - math.sqrt(
                    ((goalCentre[0] - 200) ** 2) + ((goalCentre[1] - 200) ** 2)) + scale * float(
                    chainingRadiusStringVar.get()) / 2
                smallChainRBorder = 200 + math.sqrt(
                    ((goalCentre[0] - 200) ** 2) + ((goalCentre[1] - 200) ** 2)) - scale * float(
                    chainingRadiusStringVar.get()) / 2
                bigChainLBorder = 200 - math.sqrt(
                    ((goalCentre[0] - 200) ** 2) + ((goalCentre[1] - 200) ** 2)) - scale * float(
                    chainingRadiusStringVar.get()) / 2
                bigChainRBorder = 200 + math.sqrt(
                    ((goalCentre[0] - 200) ** 2) + ((goalCentre[1] - 200) ** 2)) + scale * float(
                    chainingRadiusStringVar.get()) / 2
                self.bigChain = canvas.create_oval(bigChainLBorder, bigChainLBorder, bigChainRBorder, bigChainRBorder,
                                                   fill="#c7c7c7", width=1)
                self.smallChain = canvas.create_oval(smallChainLBorder, smallChainLBorder,
                                                     smallChainRBorder, smallChainRBorder, fill="white", width=1)

                bigThigmoRadius = 200 - scale * radius + scale * int(thigmotaxisZoneSizeStringVar.get())
                smallThigmoRadius = 200 - scale * radius + scale * (int(thigmotaxisZoneSizeStringVar.get()) / 2)
                self.bigThigmo = canvas.create_oval(bigThigmoRadius, bigThigmoRadius,
                                                    400 - bigThigmoRadius, 400 - bigThigmoRadius, dash=(2, 1))
                self.smallThigmo = canvas.create_oval(smallThigmoRadius, smallThigmoRadius,
                                                      400 - smallThigmoRadius, 400 - smallThigmoRadius, dash=(2, 1))

                self.centerLine = canvas.create_line(200, 200 + scale * radius, 200, 200 - scale * radius, dash=(1, 1))
                self.centerLine = canvas.create_line(200 - scale * radius, 200, 200 + scale * radius, 200, dash=(1, 1))
                self.centerToGoalLine = canvas.create_line(200, 200 + scale * radius, goalCentre[0], goalCentre[1],
                                                           fill="red")
                self.start = canvas.create_oval(195, 195 + scale * radius, 205, 205 + scale * radius, fill="green",
                                                width=1)
                self.goal = canvas.create_oval(goalLBorder, goalTopBorder, goalRBorder, goalBottomBorder, fill="red",
                                               width=1)

                # calculation of angular cooridor, updates to user input and renders blue lines on user interface
                # to represent outer bounds of cooridor
                if((goalCentre[0] - 200) == 0):
                    rightCorridorSideAngle = math.radians(float(corridorWidthStringVar.get()) / 2)
                else:
                    rightCorridorSideAngle = math.radians(float(corridorWidthStringVar.get()) / 2) + math.atan((goalCentre[0] - 200)/ abs(goalCentre[1] -(200 + scale * radius)))
                rightCorridorLeftDiameterChordSection = radius + radius * math.tan(rightCorridorSideAngle)
                rightCorridorRightDiameterChordSection = radius - radius * math.tan(rightCorridorSideAngle)
                rightCorridorBottomChordSection = radius / math.cos(rightCorridorSideAngle)
                rightCorridorTopChordSection = (
                                                           rightCorridorLeftDiameterChordSection * rightCorridorRightDiameterChordSection) / rightCorridorBottomChordSection
                rightCorridorOnCircleX = radius * math.tan(
                    rightCorridorSideAngle) + rightCorridorTopChordSection * math.sin(rightCorridorSideAngle)
                rightCorridorOnCircleY = rightCorridorTopChordSection * math.cos(rightCorridorSideAngle)
                self.rightAngularCooridorLine = canvas.create_line(200, 200 + scale * radius,
                                                                   200 + scale * (rightCorridorOnCircleX),
                                                                   200 - (scale * rightCorridorOnCircleY), fill="blue",
                                                                   width=2)

                leftCorridorSideAngle = rightCorridorSideAngle - math.radians(float(corridorWidthStringVar.get()))
                leftCorridorLeftDiameterChordSection = radius + radius * math.tan(leftCorridorSideAngle)
                leftCorridorRightDiameterChordSection = radius - radius * math.tan(leftCorridorSideAngle)
                leftCorridorBottomChordSection = radius / math.cos(leftCorridorSideAngle)
                leftCorridorTopChordSection = (
                                                          leftCorridorLeftDiameterChordSection * leftCorridorRightDiameterChordSection) / leftCorridorBottomChordSection
                leftCorridorOnCircleX = radius * math.tan(
                    leftCorridorSideAngle) + leftCorridorTopChordSection * math.sin(leftCorridorSideAngle)
                leftCorridorOnCircleY = leftCorridorTopChordSection * math.cos(leftCorridorSideAngle)
                self.leftAngularCooridorLine = canvas.create_line(200, 200 + scale * radius,
                                                                  200 + scale * (leftCorridorOnCircleX),
                                                                  200 - (scale * leftCorridorOnCircleY), fill="blue",
                                                                  width=2)

                # draw all rois
                for aTuple in rois:
                    roiX, roiY = aTuple[0].split(",")
                    roiCentre = [200 + scale * float(roiX), 200 - scale * float(roiY)]
                    roiLBorder = roiCentre[0] - scale * float(aTuple[1]) / 2
                    roiRBorder = roiCentre[0] + scale * float(aTuple[1]) / 2
                    roiTopBorder = roiCentre[1] - scale * float(aTuple[1]) / 2
                    roiBottomBorder = roiCentre[1] + scale * float(aTuple[1]) / 2
                    self.roi = canvas.create_oval(roiLBorder, roiTopBorder, roiRBorder, roiBottomBorder, fill="red", width=1)
            except:
                pass

        goalDiamStringVar.trace_variable("w", redraw)
        goalPosStringVar.trace_variable("w", redraw)
        chainingRadiusStringVar.trace_variable("w", redraw)
        corridorWidthStringVar.trace_variable("w", redraw)
        thigmotaxisZoneSizeStringVar.trace_variable("w", redraw)
        mazeDiamStringVar.trace_variable("w", redraw)
        mazeCentreStringVar.trace_variable("w", redraw)

    def onFrameConfigure(self, canvas):  # configure the frame
        canvas.configure(scrollregion=canvas.bbox("all"))

    def detectSoftwareType(self):
        anymaze = ['Time', 'Centre posn X', 'Centre posn Y', 'In Quadrant 1', 'In Quadrant 2', 'In Quadrant 3', 'In Quadrant 4']
        eztrack = ['', 'File', 'FPS', 'Location_Thresh', 'Use_Window', 'Window_Weight', 'Window_Size', 'Start_Frame',
                      'Frame', 'X', 'Y', 'Distance', 'dark', 'light']
        ethovision = ['Number of header lines:']
        file_extension = os.path.splitext(theFile)[1]
        if (file_extension == '.csv'):
            with open(filename, newline="") as file:
                dialect = csv.Sniffer().sniff(file.read(1024), delimiters=";,")
                file.seek(0)
                data = csv.reader(file, dialect)
                twoRows = [row for idx, row in enumerate(data) if idx in (0, 1)]
                if (set(anymaze).issubset(twoRows[0])):
                    softwareStringVar.set("anymaze")
                if (set(['x', 'y', 't']).issubset(twoRows[1])):
                    softwareStringVar.set("watermaze")
                if (set(eztrack).issubset(twoRows[0])):
                    softwareStringVar.set("eztrack")
                else:
                    softwareStringVar.set("custom")
        elif (file_extension == '.xlsx'):
            softwareStringVar.set("ethovision")


    def openFile(self):  # opens a dialog to get a single file
        logging.debug("Open File...")
        global theFile
        global fileDirectory
        global fileFlag
        fileFlag = 1
        fileDirectory = ""
        theFile = filedialog.askopenfilename()  # look for xlsx and xls files
        self.calculateButton['state'] = 'normal'

    def openDir(self):  # open dialog to get multiple files
        logging.debug("Open Dir...")
        global fileDirectory
        global theFile
        global fileFlag
        fileFlag = 0
        theFile = ""
        self.calculateButton['state'] = 'normal'
        fileDirectory = filedialog.askdirectory(mustexist=TRUE)

    def generateHeatmap(self, root):
        global softwareStringVar
        global fileDirectory
        global theFile
        software = softwareStringVar.get()
        if theFile == "" and fileDirectory == "":
            messagebox.showwarning('No file or directory', 'Please upload a file or directory before attempting to generate heatmap.')
        else:
            experiment = saveFileAsExperiment(software, theFile, fileDirectory)
            self.guiHeatmap(experiment)

    def on_enter(self, text, event):
        global oldStatus
        oldStatus = theStatus.get()
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

    def updatePathfinder(self):
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U',
                               'jsl-pathfinder'])
        exit(0)

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
        self.semiFocalRadio.select()

    def select6(self, event):
        self.chainingRadio.select()

    def select7(self, event):
        self.scanningRadio.select()

    def select8(self, event):
        self.randomRadio.select()

    def select9(self, event):
        self.thigmoRadio.select()

    def select0(self, event):
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

        try:
            with open('mainobjs.pickle', 'wb') as f:
                pickle.dump([goalPosVar, goalDiamVar, mazeDiamVar, mazeCentreVar, corridorWidthVar, chainingRadiusVar,
                             thigmotaxisZoneSizeVar], f)
        except:
            pass
        theStatus.set("Loading Files...")
        self.mainCalculate(goalPosVar, goalDiamVar)

        for roi in rois:
            print("Running for ROI: " + roi[0])
            self.mainCalculate(roi[0], roi[1])

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
        self.saveButton.config(width=10)
        self.add_button.config(width=10)
        self.container = Frame(self.top4)
        self.canvas.create_window(0, 0, anchor="nw", window=self.container)  # we title it
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.saveButton.pack(side="bottom")
        self.add_button.pack(side="bottom")

    def addROI(self):
        labelText = "ROI #" + str(int((len(self.entries)) / 2 + 2))
        label = Label(self.container, text=labelText)
        label.grid(row=int(((len(self.entries)) / 2)), column=0)
        entry1 = EntryWithPlaceholder(self.container, "Location (x,y)")
        entry1.grid(row=int(((len(self.entries)) / 2)), column=1)
        entry2 = EntryWithPlaceholder(self.container, "Diameter (cm)")
        entry2.grid(row=int(((len(self.entries)) / 2)), column=2)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.entries.append(entry1)
        self.entries.append(entry2)

    def saveROI(self):
        roiError = False
        roiList = []
        sizeList = []

        count = 0
        for entry in self.entries:
            if count % 2 == 0:
                roiList.append(entry.get())
            else:
                sizeList.append(entry.get())
            count = count + 1

        tempRois = zip(roiList, sizeList)

        patternROI = re.compile("^-?[0-9]{1,9}([.][0-9]{1,9})?[,]-?[0-9]{1,9}([.][0-9]{1,9})?$")
        patternSize = re.compile("^[0-9]{1,9}([.][0-9]{1,9})?$")

        for aTuple in tempRois:
            if aTuple[0] == 'Location (x,y)' or aTuple[1] == 'Diameter (cm)':
                continue
            if patternROI.match(aTuple[0]) == None:
                messagebox.showwarning('Input Error', 'Please verify your ROI input')
                rois.clear()
                roiError = True
            elif patternSize.match(aTuple[1]) == None:
                messagebox.showwarning('Input Error', 'Please verify your size input')
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

        global goalPosVar
        global goalDiamVar
        global mazeDiamVar
        global mazeCentreVar
        global corridorWidthVar
        global chainingRadiusVar
        global thigmotaxisZoneSizeVar

        goalPosVar = goalPosStringVar.get()
        goalDiamVar = goalDiamStringVar.get()
        mazeDiamVar = mazeDiamStringVar.get()
        mazeCentreVar = mazeCentreStringVar.get()
        corridorWidthVar = corridorWidthStringVar.get()
        chainingRadiusVar = chainingRadiusStringVar.get()
        thigmotaxisZoneSizeVar = thigmotaxisZoneSizeStringVar.get()

        self.buildGUI(root)


    def settings(self):
        logging.debug("Getting custom values")

        self.useDirectPath = BooleanVar()
        self.useFocalSearch = BooleanVar()
        self.useSemiFocalSearch = BooleanVar()
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
        self.distanceToSwimCustom2 = StringVar()
        self.distanceToPlatCustom2 = StringVar()
        self.corridorAverageCustom = StringVar()
        self.corridorJslsCustom = StringVar()
        self.annulusCustom = StringVar()
        self.quadrantTotalCustom = StringVar()
        self.percentTraversedCustom = StringVar()
        self.percentTraversedMinCustom = StringVar()
        self.distanceToCentreCustom = StringVar()
        self.smallThigmoCustom = StringVar()
        self.fullThigmoCustom = StringVar()
        self.jslsIndirectCustom = StringVar()
        self.percentTraversedRandomCustom = StringVar()
        self.directedSearchMaxDistanceCustom = StringVar()
        self.focalMinDistanceCustom = StringVar()
        self.focalMaxDistanceCustom = StringVar()
        self.semiFocalMinDistanceCustom = StringVar()
        self.semiFocalMaxDistanceCustom = StringVar()
        self.chainingMaxCoverageCustom = StringVar()
        self.thigmoMinDistanceCustom = StringVar()
        self.headingIndirectCustom = StringVar()

        try:
            with open('customobjs.pickle', 'rb') as f:
                ipeMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, distanceToSwimMaxVal2, \
                distanceToPlatMaxVal2, corridorAverageMinVal, directedSearchMaxDistance, focalMinDistance, \
                focalMaxDistance, semiFocalMinDistance, semiFocalMaxDistance, corridoripeMaxVal, annulusCounterMaxVal, \
                quadrantTotalMaxVal, chainingMaxCoverage, percentTraversedMaxVal, percentTraversedMinVal, \
                distanceToCentreMaxVal, thigmoMinDistance, smallThigmoMinVal, fullThigmoMinVal, ipeIndirectMaxVal, \
                percentTraversedRandomMaxVal, headingIndirectMaxVal, useDirectPathV, useFocalSearchV, useDirectedSearchV, \
                useIndirectV, useSemiFocalSearchV, useScanningV, useChainingV, useRandomV, useThigmoV = pickle.load(f)
            params = Parameters(name="Custom", ipeMaxVal=float(ipeMaxVal), headingMaxVal=float(headingMaxVal),
                                distanceToSwimMaxVal=float(distanceToSwimMaxVal),
                                distanceToPlatMaxVal=float(distanceToPlatMaxVal),
                                distanceToSwimMaxVal2=float(distanceToSwimMaxVal2),
                                distanceToPlatMaxVal2=float(distanceToPlatMaxVal2),
                                corridorAverageMinVal=float(corridorAverageMinVal),
                                directedSearchMaxDistance=float(directedSearchMaxDistance),
                                focalMinDistance=float(focalMinDistance), focalMaxDistance=float(focalMaxDistance),
                                semiFocalMinDistance=float(semiFocalMinDistance),
                                semiFocalMaxDistance=float(semiFocalMaxDistance),
                                corridoripeMaxVal=float(corridoripeMaxVal),
                                annulusCounterMaxVal=float(annulusCounterMaxVal),
                                quadrantTotalMaxVal=int(quadrantTotalMaxVal),
                                chainingMaxCoverage=float(chainingMaxCoverage),
                                percentTraversedMaxVal=float(percentTraversedMaxVal),
                                percentTraversedMinVal=float(percentTraversedMinVal),
                                distanceToCentreMaxVal=float(distanceToCentreMaxVal),
                                thigmoMinDistance=float(thigmoMinDistance), fullThigmoMinVal=float(fullThigmoMinVal),
                                smallThigmoMinVal=float(smallThigmoMinVal), ipeIndirectMaxVal=float(ipeIndirectMaxVal),
                                percentTraversedRandomMaxVal=float(percentTraversedRandomMaxVal),
                                headingIndirectMaxVal=float(headingIndirectMaxVal),
                                useDirect=useDirectPathV, useFocal=useFocalSearchV, useDirected=useDirectedSearchV,
                                useIndirect=useIndirectV, useSemiFocal=useSemiFocalSearchV, useChaining=useChainingV,
                                useScanning=useScanningV, useRandom=useRandomV, useThigmogaxis=useThigmoV)
        except:
            params = defaultParams

        self.jslsMaxCustom.set(params.ipeMaxVal)
        self.headingErrorCustom.set(params.headingMaxVal)
        self.distanceToSwimCustom.set(params.distanceToSwimMaxVal)
        self.distanceToPlatCustom.set(params.distanceToPlatMaxVal)
        self.distanceToSwimCustom2.set(params.distanceToSwimMaxVal2)
        self.distanceToPlatCustom2.set(params.distanceToPlatMaxVal2)
        self.corridorAverageCustom.set(params.corridorAverageMinVal)
        self.corridorJslsCustom.set(params.corridoripeMaxVal)
        self.annulusCustom.set(params.annulusCounterMaxVal)
        self.quadrantTotalCustom.set(params.quadrantTotalMaxVal)
        self.percentTraversedCustom.set(params.percentTraversedMaxVal)
        self.percentTraversedMinCustom.set(params.percentTraversedMinVal)
        self.distanceToCentreCustom.set(params.distanceToCentreMaxVal)
        self.smallThigmoCustom.set(params.smallThigmoMinVal)
        self.fullThigmoCustom.set(params.fullThigmoMinVal)
        self.jslsIndirectCustom.set(params.ipeIndirectMaxVal)
        self.percentTraversedRandomCustom.set(params.percentTraversedRandomMaxVal)
        self.directedSearchMaxDistanceCustom.set(params.directedSearchMaxDistance)
        self.focalMinDistanceCustom.set(params.focalMinDistance)
        self.focalMaxDistanceCustom.set(params.focalMaxDistance)
        self.semiFocalMinDistanceCustom.set(params.semiFocalMinDistance)
        self.semiFocalMaxDistanceCustom.set(params.semiFocalMaxDistance)
        self.chainingMaxCoverageCustom.set(params.chainingMaxCoverage)
        self.thigmoMinDistanceCustom.set(params.thigmoMinDistance)
        self.headingIndirectCustom.set(params.headingIndirectMaxVal)
        self.useDirectPath.set(params.useDirect)
        self.useFocalSearch.set(params.useFocal)
        self.useDirectedSearch.set(params.useDirected)
        self.useIndirect.set(params.useIndirect)
        self.useSemiFocalSearch.set(params.useSemiFocal)
        self.useChaining.set(params.useChaining)
        self.useScanning.set(params.useScanning)
        self.useRandom.set(params.useRandom)
        self.useThigmo.set(params.useThigmotaxis)
        # all of the above is the same as in snyder, plus the creation of variables to hold values from the custom menu

        self.top = Toplevel(root)  # we set this to be the top
        self.top.configure(bg="white")

        canvas = Canvas(self.top, borderwidth=0, width=600, height=600, bg="white")  # we create the canvas
        frame = Frame(canvas)  # we place a frame in the canvas
        frame.configure(bg="white")
        yscrollbar = Scrollbar(self.top, orient=VERTICAL, command=canvas.yview)  # vertical scroll bar
        yscrollbar.grid(row=0, column=2, sticky='ns')

        canvas.grid(row=0, column=0) # we pack in the canvas
        canvas.create_window((4, 4), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=yscrollbar.set)  # we set the commands for the scroll bars
        frame.bind("<Configure>", lambda event, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))



        Label(frame, text="Settings", bg="white", fg="black").grid(row=0, column=0, columnspan=2, padx=100, pady=20)  # we title it

        rowCount = 1

        useDirectPathL = Label(frame, text="Direct Path: ", bg="white")  # we add a direct path label
        useDirectPathL.grid(row=rowCount, column=0, sticky=E)  # stick it to row 1
        useDirectPathC = Checkbutton(frame, variable=self.useDirectPath, bg="white")  # we add a direct path checkbox
        useDirectPathC.grid(row=rowCount, column=1)  # put it beside the label

        rowCount += 1

        jslsMaxCustomL = Label(frame, text="Ideal Path Error [maximum]: ", bg="white")  # label for JSLs
        jslsMaxCustomL.grid(row=rowCount, column=0, sticky=E)  # row 2
        jslsMaxCustomE = Entry(frame, textvariable=self.jslsMaxCustom)  # entry field
        jslsMaxCustomE.grid(row=rowCount, column=1)  # right beside

        rowCount += 1

        headingErrorCustomL = Label(frame, text="Heading error [maximum, degrees]: ", bg="white")
        headingErrorCustomL.grid(row=rowCount, column=0, sticky=E)
        headingErrorCustomE = Entry(frame, textvariable=self.headingErrorCustom)
        headingErrorCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useFocalSearchL = Label(frame, text="Focal Search: ", bg="white")
        useFocalSearchL.grid(row=rowCount, column=0, sticky=E)
        useFocalSearchC = Checkbutton(frame, variable=self.useFocalSearch, bg="white")
        useFocalSearchC.grid(row=rowCount, column=1)

        rowCount += 1

        distanceToSwimCustomL = Label(frame, text="Distance to swim path centroid [maximum, % of radius]: ",
                                      bg="white")
        distanceToSwimCustomL.grid(row=rowCount, column=0, sticky=E)
        distanceToSwimCustomE = Entry(frame, textvariable=self.distanceToSwimCustom)
        distanceToSwimCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        distanceToPlatCustomL = Label(frame, text="Distance to goal [maximum, % of radius]: ", bg="white")
        distanceToPlatCustomL.grid(row=rowCount, column=0, sticky=E)
        distanceToPlatCustomE = Entry(frame, textvariable=self.distanceToPlatCustom)
        distanceToPlatCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        focalMinDistanceCustomL = Label(frame, text="Distance covered (minimum, cm): ", bg="white")
        focalMinDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        focalMinDistanceCustomE = Entry(frame, textvariable=self.focalMinDistanceCustom)
        focalMinDistanceCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        focalMaxDistanceCustomL = Label(frame, text="Distance covered (maximum, cm): ", bg="white")
        focalMaxDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        focalMaxDistanceCustomE = Entry(frame, textvariable=self.focalMaxDistanceCustom)
        focalMaxDistanceCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useDirectedSearchL = Label(frame, text="Directed Search: ", bg="white")
        useDirectedSearchL.grid(row=rowCount, column=0, sticky=E)
        useDirectedSearchC = Checkbutton(frame, variable=self.useDirectedSearch, bg="white", onvalue=1)
        useDirectedSearchC.grid(row=rowCount, column=1)

        rowCount += 1

        corridorAverageCustomL = Label(frame, text="Time in angular corridor [minimum, % of trial]: ", bg="white")
        corridorAverageCustomL.grid(row=rowCount, column=0, sticky=E)
        corridorAverageCustomE = Entry(frame, textvariable=self.corridorAverageCustom)
        corridorAverageCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        directedSearchMaxDistanceCustomL = Label(frame, text="Distance covered (maximum, cm): ", bg="white")
        directedSearchMaxDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        directedSearchMaxDistanceCustomE = Entry(frame, textvariable=self.directedSearchMaxDistanceCustom)
        directedSearchMaxDistanceCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        corridorJslsCustomL = Label(frame, text="Ideal Path Error [maximum]: ", bg="white")
        corridorJslsCustomL.grid(row=rowCount, column=0, sticky=E)
        corridorJslsCustomE = Entry(frame, textvariable=self.corridorJslsCustom)
        corridorJslsCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useIndirectL = Label(frame, text="Indirect Search: ", bg="white")
        useIndirectL.grid(row=rowCount, column=0, sticky=E)
        useIndirectC = Checkbutton(frame, variable=self.useIndirect, bg="white")
        useIndirectC.grid(row=rowCount, column=1)

        rowCount += 1

        jslsIndirectCustomL = Label(frame, text="Ideal Path Error [maximum]: ", bg="white")
        jslsIndirectCustomL.grid(row=rowCount, column=0, sticky=E)
        jslsIndirectCustomE = Entry(frame, textvariable=self.jslsIndirectCustom)
        jslsIndirectCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        headingIndirectCustomL = Label(frame, text="Average Heading error [maximum]: ", bg="white")
        headingIndirectCustomL.grid(row=rowCount, column=0, sticky=E)
        headingIndirectCustomE = Entry(frame, textvariable=self.headingIndirectCustom, bg="white")
        headingIndirectCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useSemiFocalSearchL = Label(frame, text="Semi-focal Search: ", bg="white")
        useSemiFocalSearchL.grid(row=rowCount, column=0, sticky=E)
        useSemiFocalSearchC = Checkbutton(frame, variable=self.useSemiFocalSearch, bg="white")
        useSemiFocalSearchC.grid(row=rowCount, column=1)

        rowCount += 1

        distanceToSwimCustomL2 = Label(frame, text="Distance to swim path centroid [maximum, % of radius]: ",
                                       bg="white")
        distanceToSwimCustomL2.grid(row=rowCount, column=0, sticky=E)
        distanceToSwimCustomE2 = Entry(frame, textvariable=self.distanceToSwimCustom2)
        distanceToSwimCustomE2.grid(row=rowCount, column=1)

        rowCount += 1

        distanceToPlatCustomL2 = Label(frame, text="Distance to goal [maximum, % of radius]: ", bg="white")
        distanceToPlatCustomL2.grid(row=rowCount, column=0, sticky=E)
        distanceToPlatCustomE2 = Entry(frame, textvariable=self.distanceToPlatCustom2)
        distanceToPlatCustomE2.grid(row=rowCount, column=1)

        rowCount += 1

        semiFocalMinDistanceCustomL = Label(frame, text="Distance covered (minimum, cm): ", bg="white")
        semiFocalMinDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        semiFocalMinDistanceCustomE = Entry(frame, textvariable=self.semiFocalMinDistanceCustom)
        semiFocalMinDistanceCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        semiFocalMaxDistanceCustomL = Label(frame, text="Distance covered (maximum, cm): ", bg="white")
        semiFocalMaxDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        semiFocalMaxDistanceCustomE = Entry(frame, textvariable=self.semiFocalMaxDistanceCustom)
        semiFocalMaxDistanceCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useChainingL = Label(frame, text="Chaining: ", bg="white")
        useChainingL.grid(row=rowCount, column=0, sticky=E)
        useChainingC = Checkbutton(frame, variable=self.useChaining, bg="white")
        useChainingC.grid(row=rowCount, column=1)

        rowCount += 1

        annulusCustomL = Label(frame, text="Time in annulus zone [minimum, % of trial]: ", bg="white")
        annulusCustomL.grid(row=rowCount, column=0, sticky=E)
        annulusCustomE = Entry(frame, textvariable=self.annulusCustom)
        annulusCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        quadrantTotalCustomL = Label(frame, text="Quadrants visited [minimum]: ", bg="white")
        quadrantTotalCustomL.grid(row=rowCount, column=0, sticky=E)
        quadrantTotalCustomE = Entry(frame, textvariable=self.quadrantTotalCustom)
        quadrantTotalCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        chainingMaxCoverageCustomL = Label(frame, text="Area of maze traversed (maximum, % of maze): ", bg="white")
        chainingMaxCoverageCustomL.grid(row=rowCount, column=0, sticky=E)
        chainingMaxCoverageCustomE = Entry(frame, textvariable=self.chainingMaxCoverageCustom)
        chainingMaxCoverageCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useScanningL = Label(frame, text="Scanning: ", bg="white")
        useScanningL.grid(row=rowCount, column=0, sticky=E)
        useScanningC = Checkbutton(frame, variable=self.useScanning, bg="white")
        useScanningC.grid(row=rowCount, column=1)

        rowCount += 1

        percentTraversedCustomL = Label(frame, text="Area of maze traversed [maximum, % of maze]: ", bg="white")
        percentTraversedCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedCustomE = Entry(frame, textvariable=self.percentTraversedCustom)
        percentTraversedCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        percentTraversedMinCustomL = Label(frame, text="Area of maze traversed [minimum, % of maze]: ", bg="white")
        percentTraversedMinCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedMinCustomE = Entry(frame, textvariable=self.percentTraversedMinCustom)
        percentTraversedMinCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        distanceToCentreCustomL = Label(frame, text="Average distance to maze centre [maximum, % of radius]: ",
                                        bg="white")
        distanceToCentreCustomL.grid(row=rowCount, column=0, sticky=E)
        distanceToCentreCustomE = Entry(frame, textvariable=self.distanceToCentreCustom)
        distanceToCentreCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useThigmoL = Label(frame, text="Thigmotaxis: ", bg="white")
        useThigmoL.grid(row=rowCount, column=0, sticky=E)
        useThigmoC = Checkbutton(frame, variable=self.useThigmo, bg="white")
        useThigmoC.grid(row=rowCount, column=1)

        rowCount += 1

        fullThigmoCustomL = Label(frame, text="Time in full thigmotaxis zone [minimum, % of trial]: ", bg="white")
        fullThigmoCustomL.grid(row=rowCount, column=0, sticky=E)
        fullThigmoCustomE = Entry(frame, textvariable=self.fullThigmoCustom, bg="white")
        fullThigmoCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        smallThigmoCustomL = Label(frame, text="Time in smaller thigmotaxis zone [minimum, % of trial]: ", bg="white")
        smallThigmoCustomL.grid(row=rowCount, column=0, sticky=E)
        smallThigmoCustomE = Entry(frame, textvariable=self.smallThigmoCustom)
        smallThigmoCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        thigmoMinDistanceCustomL = Label(frame, text="Total distance covered (minimum, cm): ", bg="white")
        thigmoMinDistanceCustomL.grid(row=rowCount, column=0, sticky=E)
        thigmoMinDistanceCustomE = Entry(frame, textvariable=self.thigmoMinDistanceCustom, bg="white")
        thigmoMinDistanceCustomE.grid(row=rowCount, column=1)

        rowCount += 1

        useRandomL = Label(frame, text="Random Search: ", bg="white")
        useRandomL.grid(row=rowCount, column=0, sticky=E)
        useRandomC = Checkbutton(frame, variable=self.useRandom, bg="white")
        useRandomC.grid(row=rowCount, column=1)

        rowCount += 1

        percentTraversedRandomCustomL = Label(frame, text="Area of maze traversed [minimum, % of maze]: ", bg="white")
        percentTraversedRandomCustomL.grid(row=rowCount, column=0, sticky=E)
        percentTraversedRandomCustomE = Entry(frame, textvariable=self.percentTraversedRandomCustom)
        percentTraversedRandomCustomE.grid(row=rowCount, column=1)

        rowCount += 1
        Button(frame, text="Save", command=self.saveCuston).grid(row=rowCount, column=0, columnspan=2)
        rowCount += 1
        Button(frame, text="Reset", command=self.resetCustom).grid(row=rowCount, column=0, columnspan=2)



    def saveCuston(self):  # save the custom values
        logging.debug("Saving custom parameters")
        global params
        params = Parameters(name="Custom", ipeMaxVal=float(self.jslsMaxCustom.get()),
                            headingMaxVal=float(self.headingErrorCustom.get()),
                            distanceToSwimMaxVal=float(self.distanceToSwimCustom.get()),
                            distanceToPlatMaxVal=float(self.distanceToPlatCustom.get()),
                            distanceToSwimMaxVal2=float(self.distanceToSwimCustom2.get()),
                            distanceToPlatMaxVal2=float(self.distanceToPlatCustom2.get()),
                            corridorAverageMinVal=float(self.corridorAverageCustom.get()),
                            directedSearchMaxDistance=float(self.directedSearchMaxDistanceCustom.get()),
                            focalMinDistance=float(self.focalMinDistanceCustom.get()),
                            focalMaxDistance=float(self.focalMaxDistanceCustom.get()),
                            semiFocalMinDistance=float(self.semiFocalMinDistanceCustom.get()),
                            semiFocalMaxDistance=float(self.semiFocalMaxDistanceCustom.get()),
                            corridoripeMaxVal=float(self.corridorJslsCustom.get()),
                            annulusCounterMaxVal=float(self.annulusCustom.get()),
                            quadrantTotalMaxVal=int(self.quadrantTotalCustom.get()),
                            chainingMaxCoverage=float(self.chainingMaxCoverageCustom.get()),
                            percentTraversedMaxVal=float(self.percentTraversedCustom.get()),
                            percentTraversedMinVal=float(self.percentTraversedMinCustom.get()),
                            distanceToCentreMaxVal=float(self.distanceToCentreCustom.get()),
                            thigmoMinDistance=float(self.thigmoMinDistanceCustom.get()),
                            fullThigmoMinVal=float(self.fullThigmoCustom.get()),
                            smallThigmoMinVal=float(self.smallThigmoCustom.get()),
                            ipeIndirectMaxVal=float(self.jslsIndirectCustom.get()),
                            percentTraversedRandomMaxVal=float(self.percentTraversedRandomCustom.get()),
                            headingIndirectMaxVal=float(self.headingIndirectCustom.get()),
                            useDirect=self.useDirectPath.get(), useFocal=self.useFocalSearch.get(),
                            useDirected=self.useDirectedSearch.get(), useIndirect=self.useIndirect.get(),
                            useSemiFocal=self.useSemiFocalSearch.get(), useChaining=self.useChaining.get(),
                            useScanning=self.useScanning.get(), useRandom=self.useRandom.get(),
                            useThigmogaxis=self.useThigmo.get())

        try:
            with open('customobjs.pickle', 'wb') as f:
                pickle.dump(
                    [params.ipeMaxVal, params.headingMaxVal, params.distanceToSwimMaxVal, params.distanceToPlatMaxVal,
                     params.distanceToSwimMaxVal2, params.distanceToPlatMaxVal2, params.corridorAverageMinVal,
                     params.directedSearchMaxDistance, params.focalMinDistance, params.focalMaxDistance,
                     params.semiFocalMinDistance, params.semiFocalMaxDistance, params.corridoripeMaxVal,
                     params.annulusCounterMaxVal, params.quadrantTotalMaxVal, params.chainingMaxCoverage,
                     params.percentTraversedMaxVal, params.percentTraversedMinVal, params.distanceToCentreMaxVal,
                     params.thigmoMinDistance, params.smallThigmoMinVal, params.fullThigmoMinVal,
                     params.ipeIndirectMaxVal, params.percentTraversedRandomMaxVal, params.headingIndirectMaxVal,
                     params.useDirect, params.useFocal, params.useDirected, params.useIndirect, params.useSemiFocal,
                     params.useChaining, params.useScanning, params.useRandom, params.useThigmotaxis], f)
        except:
            pass
        try:
            self.top.destroy()
        except:
            pass

    def resetCustom(self):
        result = messagebox.askquestion("Reset", "Are You Sure?", icon='warning')
        global params
        if result == 'yes':
            logging.debug("Resetting custom parameters")
            params = defaultParams
            try:
                with open('customobjs.pickle', 'wb') as f:
                    pickle.dump([params.ipeMaxVal, params.headingMaxVal, params.distanceToSwimMaxVal,
                                 params.distanceToPlatMaxVal, params.distanceToSwimMaxVal2,
                                 params.distanceToPlatMaxVal2, params.corridorAverageMinVal,
                                 params.directedSearchMaxDistance, params.focalMinDistance, params.focalMaxDistance,
                                 params.semiFocalMinDistance, params.semiFocalMaxDistance, params.corridoripeMaxVal,
                                 params.annulusCounterMaxVal, params.quadrantTotalMaxVal, params.chainingMaxCoverage,
                                 params.percentTraversedMaxVal, params.percentTraversedMinVal,
                                 params.distanceToCentreMaxVal, params.thigmoMinDistance, params.smallThigmoMinVal,
                                 params.fullThigmoMinVal, params.ipeIndirectMaxVal, params.percentTraversedRandomMaxVal,
                                 params.headingIndirectMaxVal, params.useDirect, params.useFocal, params.useDirected,
                                 params.useIndirect, params.useSemiFocal, params.useChaining, params.useScanning,
                                 params.useRandom, params.useThigmotaxis], f)
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

    def callDefineOwnSoftware(self):
        global theFile
        if theFile == "":
            logging.debug("Open File...")
            theFile = filedialog.askopenfilename()
        if theFile != "":
            defineOwnSoftware(root, theFile)
        if destroyedroot==True:
            softwareStringVar.set('custom')
            self.defineRadio['state'] = 'active'
            self.calculateButton['state'] = 'normal'

    def plotPoints(self, x, y, mazeDiam, centreX, centreY, platX, platY, name, title, platEstDiam):  # function to graph the data for the not recognized trials
        wallsX = []
        wallsY = []
        platWallsX = []
        platWallsY = []
        for theta in range(0, 360):
            wallsX.append(centreX + ((math.ceil(mazeDiam) / 2)) * math.cos(math.radians(theta)))
            wallsY.append(centreY + ((math.ceil(mazeDiam) / 2)) * math.sin(math.radians(theta)))

        for theta in range(0, 360):
            platWallsX.append(platX + ((math.ceil(platEstDiam) / 2) + 1) * math.cos(math.radians(theta)))
            platWallsY.append(platY + ((math.ceil(platEstDiam) / 2) + 1) * math.sin(math.radians(theta)))

        plotName = "output/plots/" + name + " " + str(
            strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # the name will be Animal id followed by the date and time
        plt.scatter(x, y, s=15, c='r', alpha=1.0)  # we plot the XY position of animal
        plt.scatter(x[0], y[0], s=100, c='b', alpha=1, marker='s')  # we plot the start point
        plt.scatter(platWallsX, platWallsY, s=1, c='black', alpha=1.0)  # we plot the goal
        plt.scatter(centreX, centreY, s=100, c='g', alpha=1.0)  # we plot the centre
        plt.scatter(wallsX, wallsY, s=15, c='black', alpha=0.3)
        plt.title(title)  # add the title
        plt.xlim(centreX - mazeDiam / 2 - 15,
                 centreX + mazeDiam / 2 + 15)  # set the size to be the center + radius + 30
        plt.ylim(centreY - mazeDiam / 2 - 15, centreY + mazeDiam / 2 + 15)

        try:
            plt.gca().set_aspect('equal')
        except:
            pass
        photoName = plotName + ".png"  # image name the same as plotname
        plt.savefig(photoName, dpi=100)  # save the file
        plt.clf()  # clear the plot

        image = PIL.Image.open(photoName)  # open the saved image
        photo = ImageTk.PhotoImage(image)  # convert it to something the GUI can read
        global searchStrategyV
        global searchStrategyStringVar

        searchStrategyStringVar = StringVar()  # temporary variable for the selection of strategies
        searchStrategyStringVar.set("Not Recognized")

        self.top2 = Toplevel(root)  # create a new toplevel window
        self.top2.configure(bg="white")

        Label(self.top2, text=name, bg="white", fg="black", width=40).grid(row=0, column=0, columnspan=7)  # add a title
        photoimg = Label(self.top2, image=photo)  # add the photo
        photoimg.image = photo  # keep a reference
        photoimg.grid(row=1, column=0, columnspan=7)  # place the photo in the window

        Label(self.top2, text="Start position", bg="blue", fg="white", width=15).grid(row=2, column=1, padx=3)
        Label(self.top2, text="Goal and Walls", bg="black", fg="white", width=15).grid(row=2, column=2, padx=3)
        Label(self.top2, text="Maze centre", bg="green", fg="white", width=15).grid(row=2, column=3, padx=3)
        Label(self.top2, text="Path", bg="red", fg="white", width=15).grid(row=2, column=4, padx=3)

        self.directRadio = Radiobutton(self.top2, text="(1) Direct Path", variable=searchStrategyStringVar,
                                       value="Direct path",
                                       indicatoron=0, width=15, bg="white")
        self.directRadio.grid(row=3, column=0, columnspan=7, pady=3)  # add the radiobuttons for selection

        self.focalRadio = Radiobutton(self.top2, text="(2) Focal Search", variable=searchStrategyStringVar,
                                      value="Focal Search",
                                      indicatoron=0, width=15, bg="white")
        self.focalRadio.grid(row=4, column=0, columnspan=7, pady=3)
        self.directedRadio = Radiobutton(self.top2, text="(3) Directed Search", variable=searchStrategyStringVar,
                                         value="Directed Search (m)", indicatoron=0, width=15, bg="white")
        self.directedRadio.grid(row=5, column=0, columnspan=7, pady=3)
        self.spatialRadio = Radiobutton(self.top2, text="(4) Indirect Search", variable=searchStrategyStringVar,
                                        value="Indirect Search", indicatoron=0, width=15, bg="white")
        self.spatialRadio.grid(row=6, column=0, columnspan=7, pady=3)
        self.semiFocalRadio = Radiobutton(self.top2, text="(5) Semi-focal Search", variable=searchStrategyStringVar,
                                       value="Semi-focal Search",
                                       indicatoron=0, width=15, bg="white")
        self.semiFocalRadio.grid(row=7, column=0, columnspan=7, pady=3)
        self.chainingRadio = Radiobutton(self.top2, text="(6) Chaining", variable=searchStrategyStringVar,
                                         value="Chaining",
                                         indicatoron=0, width=15, bg="white")
        self.chainingRadio.grid(row=8, column=0, columnspan=7, pady=3)
        self.scanningRadio = Radiobutton(self.top2, text="(7) Scanning", variable=searchStrategyStringVar,
                                         value="Scanning",
                                         indicatoron=0, width=15, bg="white")
        self.scanningRadio.grid(row=9, column=0, columnspan=7, pady=3)
        self.randomRadio = Radiobutton(self.top2, text="(8) Random Search", variable=searchStrategyStringVar,
                                       value="Random Search",
                                       indicatoron=0, width=15, bg="white")
        self.randomRadio.grid(row=10, column=0, columnspan=7, pady=3)
        self.thigmoRadio = Radiobutton(self.top2, text="(9) Thigmotaxis", variable=searchStrategyStringVar,
                                       value="Thigmotaxis",
                                       indicatoron=0, width=15, bg="white")
        self.thigmoRadio.grid(row=11, column=0, columnspan=7, pady=3)
        self.notRecognizedRadio = Radiobutton(self.top2, text="(0) Not Recognized", variable=searchStrategyStringVar,
                                              value="Not Recognized",
                                              indicatoron=0, width=15, bg="white")
        self.notRecognizedRadio.grid(row=12, column=0, columnspan=7, pady=3)

        Button(self.top2, text="(Return) Save", command=self.saveStrat, fg="black", bg="white", width=15).grid(row=13,
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
        self.top2.bind('0', self.select0)

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
        self.top3.geometry('{}x{}'.format(200, 300))
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

    def heatmap(self, aExperiment):  # Generates heatmaps for inputted trial data
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
            dayStartStop = [1, float(math.inf)]
        elif "-" in dayVal:
            dayStartStop = dayVal.split("-", 1)
            dayStartStop = [int(dayStartStop[0]), int(dayStartStop[1])]
        else:
            dayStartStop = [int(dayVal), int(dayVal)]

        if trialVal == "All" or trialVal == "all" or trialVal == "":
            trialStartStop = [1, float(math.inf)]
        elif "-" in trialVal:
            trialStartStop = trialVal.split("-", 1)
            trialStartStop = [int(trialStartStop[0]), int(trialStartStop[1])]
        else:
            trialStartStop = [int(trialVal), int(trialVal)]

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
                if dayNum != 0 and trialNum != 0:
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
                else:
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

        aFileName = "output/heatmaps/ " + "Day " + dayValStringVar.get() + " Trial " + trialValStringVar.get() + str(
            strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # name of the log file for the run
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

        plt.title("Day: " + dayValStringVar.get() + " Trial: " + trialValStringVar.get())
        cb = plt.colorbar()
        photoName = aFileName + ".png"  # image name the same as plotname
        plt.savefig(photoName, dpi=300, figsize=(4, 4))  # save the file
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
            return (0, 0)
        try:
            return vector / np.linalg.norm(vector)
        except:
            return (0, 0)

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

        entropyResult = eng.Entropy(xList, yList, goalX, goalY)
        return entropyResult

    def getAutoLocations(self, theExperiment, goalX, goalY, goalPosVar, mazeCentreX, mazeCentreY, mazeCentreVar,
                         mazeDiamVar, software, goalDiamVar):
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
            logging.debug("Goal position set manually: " + str(goalPosVar))
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
            logging.debug("Maze centre set manually: " + str(mazeCentreVar))
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
                    logging.error("Unable to determine a centre position. Compatible trials: 0")
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
            platEstDiam = ((platMaxX - platMinX) + (platMaxY - platMinY)) / 2
            if platEstDiam > 50 or platEstDiam < 1:
                platEstDiam = 10.0
                print(
                    "Automatic goal diameter calculation failed. Defaulted to: " + str((math.ceil(float(platEstDiam)))))
            else:
                print("Automatic goal diameter calculated as: " + str((math.ceil(float(platEstDiam)))))
            logging.info("Automatic goal diameter calculated as: " + str((math.ceil(float(platEstDiam)))))
        if diamFlag:  # automatic diameter
            mazeDiamEst = ((abs(absMaxX) + abs(absMinX)) + (abs(absMaxY) + abs(absMinY))) / 2
            logging.info("Automatic maze diameter calculated as: " + str(mazeDiamEst))
            print("Automatic maze diameter calculated as: " + str(mazeDiamEst))
            mazeDiamVar = mazeDiamEst
            mazeRadius = float(mazeDiamVar) / 2
        return (mazeCentreX, mazeCentreY, goalX, goalY, mazeDiamVar, mazeRadius, platEstDiam)

    def calculateValues(self, theTrial, goalX, goalY, mazeCentreX, mazeCentreY, corridorWidth, thigmotaxisZoneSize,
                        chainingRadius, fullThigmoZone, smallThigmoZone, mazeradius, dayNum, goalDiam):
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

        smallThigmoCounter = 0.0
        fullThigmoCounter = 0.0
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
        distanceFromStartToGoal = 0
        arrayX = []
        arrayY = []


        for aDatapoint in theTrial:  # for each row in our sheet
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
            print(aX)
            arrayX.append(aX)
            arrayY.append(aY)

            # Average Distance
            currentDistanceFromGoal = math.sqrt((goalX - aX) ** 2 + (goalY - aY) ** 2)

            # in zones
            distanceCenterToGoal = math.sqrt((mazeCentreX - goalX) ** 2 + (mazeCentreY - goalY) ** 2)
            annulusZoneInner = distanceCenterToGoal - (chainingRadius / 2)
            annulusZoneOuter = distanceCenterToGoal + (chainingRadius / 2)
            distanceToCenterOfMaze = math.sqrt((mazeCentreX - aX) ** 2 + (mazeCentreY - aY) ** 2)
            totalDistanceToCenterOfMaze += distanceToCenterOfMaze
            distanceFromStartToGoal = math.sqrt((goalX - startX) ** 2 + (goalY - startY) ** 2)

            distance = math.sqrt(abs(oldX - aX) ** 2 + abs(oldY - aY) ** 2)
            distanceFromGoalSummed += currentDistanceFromGoal
            totalDistance += distance
            oldX = aX
            oldY = aY

            if distanceToCenterOfMaze > smallThigmoZone:  # calculate if we are in zones
                smallThigmoCounter += 1.0
            if distanceToCenterOfMaze > fullThigmoZone:
                fullThigmoCounter += 1.0
            if (distanceToCenterOfMaze >= annulusZoneInner) and (distanceToCenterOfMaze <= annulusZoneOuter):
                annulusCounter += 1.0

            a, b = 0, 0


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
            if truncateFlag and currentDistanceFromGoal < float(goalDiam) / 2.0:
                break

        quadrantTotal = quadrantOne + quadrantTwo + quadrantThree + quadrantFour


        spreadX = abs((mazeCentreX+mazeradius) - (mazeCentreX-mazeradius))
        spreadY = abs((mazeCentreY+mazeradius) - (mazeCentreY-mazeradius))
        normX = []
        normY = []
        for xx in arrayX:
            normX.append(round((((xx - abs((mazeCentreX - mazeradius))) / spreadX)*10),0)*10)
        for yy in arrayY:
            normY.append(round((((yy - abs((mazeCentreY - mazeradius))) / spreadY)*10),0)*10)
        XY = list(zip(normX,normY))
        XY = list(dict.fromkeys(XY))
        print(XY)
        percentTraversed = len(XY)# turn our count into a percentage over how many cells we can visit
        print(percentTraversed)
        if percentTraversed > 100:
            percentTraversed = 100

        if i == 0:
            i = 1
        try:
            xAv = xSummed / i  # get our average positions for the centroid
            yAv = ySummed / i
            swimPathCentroid = (xAv, yAv)
        except:
            swimPathCentroid = (0, 0)

        startPoint = np.array([startX, startY])
        goalPoint = np.array([goalX, goalY])

        startToPlatVector = goalPoint - startPoint

        if(goalX-startX != 0):
            aArcTangent = math.degrees(math.atan((goalY - startY) / (goalX - startX)))
        else:
            aArcTangent = 0;

        upperCorridor = aArcTangent + corridorWidth
        lowerCorridor = aArcTangent - corridorWidth
        corridorWidth = 0.0
        totalHeadingError = 0.0
        initialHeadingError = 0.0
        initialHeadingErrorCount = 0

        for aDatapoint in theTrial:  # go back through all values and calculate distance to the centroid

            currentDistanceFromGoal = math.sqrt(
                (goalX - aDatapoint.getx()) ** 2 + (goalY - aDatapoint.gety()) ** 2)
            distanceToSwimPathCentroid = math.sqrt(
                (xAv - aDatapoint.getx()) ** 2 + (yAv - aDatapoint.gety()) ** 2)
            totalDistanceToSwimPathCentroid += distanceToSwimPathCentroid
            distanceFromStartToCurrent = math.sqrt(
                (aDatapoint.getx() - startX) ** 2 + (aDatapoint.gety() - startY) ** 2)

            if oldItemX != 0 and aDatapoint.getx() - oldItemX != 0 and aDatapoint.getx() - startX != 0:
                currentToPlat = np.subtract(np.array([goalX, goalY]), np.array([aDatapoint.getx(), aDatapoint.gety()]))
                oldToCurrent = np.subtract(np.array([aDatapoint.getx(), aDatapoint.gety()]),
                                           np.array([oldItemX, oldItemY]))
                currentHeadingError = abs(self.angle_between(currentToPlat, oldToCurrent))
                withinCorridor = math.degrees(math.atan((aDatapoint.gety() - startY) / (aDatapoint.getx() - startX)))
                corridorWidth = abs(
                    aArcTangent - abs(
                        math.degrees(math.atan((aDatapoint.gety() - oldItemY) / (aDatapoint.getx() - oldItemX)))))
                if float(lowerCorridor) <= float(withinCorridor) <= float(upperCorridor):
                    corridorCounter += 1.0
            if (aDatapoint.gettime() < 1.0):
                initialHeadingError += currentHeadingError
                initialHeadingErrorCount += 1

            oldItemX = aDatapoint.getx()
            oldItemY = aDatapoint.gety()
            totalHeadingError += currentHeadingError
            if truncateFlag and currentDistanceFromGoal < float(goalDiam) / 2.0:
                break
        try:
            corridorAverage = corridorCounter / i
            distanceAverage = distanceFromGoalSummed / i  # calculate our average distances to landmarks
            averageDistanceToSwimPathCentroid = totalDistanceToSwimPathCentroid / i
            averageDistanceToOldGoal = totalDistanceToOldGoal / i
            averageDistanceToCentre = totalDistanceToCenterOfMaze / i
            averageHeadingError = totalHeadingError / i
        except:
            i = 1
            corridorAverage = corridorCounter / i
            distanceAverage = distanceFromGoalSummed / i  # calculate our average distances to landmarks
            averageDistanceToSwimPathCentroid = totalDistanceToSwimPathCentroid / i
            averageDistanceToOldGoal = totalDistanceToOldGoal / i
            averageDistanceToCentre = totalDistanceToCenterOfMaze / i
            averageHeadingError = totalHeadingError / i

        try:
            averageInitialHeadingError = initialHeadingError / initialHeadingErrorCount
        except:
            averageInitialHeadingError = 0
        cellCounter = 0.0  # initialize our cell counter

        velocity = 0
        idealDistance = distanceFromStartToGoal
        if latency != 0:
            try:
                velocity = (totalDistance / latency)
            except:
                velocity = 0
                pass
        idealCumulativeDistance = 0.0
        try:
            sampleRate = (theTrial.datapointList[-1].gettime() - startTime) / (len(theTrial.datapointList) - 1)
        except:
            logging.info("Error with sample rate calculation")
            sampleRate = 1
        while idealDistance > math.ceil(float(goalDiam) / 2):
            idealCumulativeDistance += idealDistance
            idealDistance = (idealDistance - velocity * sampleRate)
            if (idealCumulativeDistance > 1000000):
                break

        ipe = float(distanceFromGoalSummed - idealCumulativeDistance) * sampleRate

        if ipe < 0:
            ipe = 0

        if useEntropyFlag:
            entropyResult = self.calculateEntropy(theTrial, goalX, goalY)
        else:
            entropyResult = False
        return corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToCentre, averageHeadingError, percentTraversed, quadrantTotal, totalDistance, latency, fullThigmoCounter, smallThigmoCounter, annulusCounter, i, arrayX, arrayY, velocity, ipe, averageInitialHeadingError, entropyResult

    def mainCalculate(self, goalPosVar=goalPosVar, goalDiamVar=goalDiamVar):
        global softwareStringVar
        global params
        logging.debug("Calculate Called")
        self.updateTasks()
        theStatus.set("Initializing")

        try:
            with open('customobjs.pickle', 'rb') as f:
                ipeMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, distanceToSwimMaxVal2, distanceToPlatMaxVal2, corridorAverageMinVal, directedSearchMaxDistance, focalMinDistance, focalMaxDistance, semiFocalMinDistance, semiFocalMaxDistance, corridoripeMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, chainingMaxCoverage, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, thigmoMinDistance, smallThigmoMinVal, fullThigmoMinVal, ipeIndirectMaxVal, percentTraversedRandomMaxVal, headingIndirectMaxVal, useDirectPathV, useFocalSearchV, useDirectedSearchV, useIndirectV, useSemiFocalSearchV, useScanningV, useChainingV, useRandomV, useThigmoV = pickle.load(
                    f)
            params = Parameters(name="Custom", ipeMaxVal=float(ipeMaxVal), headingMaxVal=float(headingMaxVal),
                                distanceToSwimMaxVal=float(distanceToSwimMaxVal),
                                distanceToPlatMaxVal=float(distanceToPlatMaxVal),
                                distanceToSwimMaxVal2=float(distanceToSwimMaxVal2),
                                distanceToPlatMaxVal2=float(distanceToPlatMaxVal2),
                                corridorAverageMinVal=float(corridorAverageMinVal),
                                directedSearchMaxDistance=float(directedSearchMaxDistance),
                                focalMinDistance=float(focalMinDistance), 
                                focalMaxDistance=float(focalMaxDistance),
                                semiFocalMinDistance=float(semiFocalMinDistance),
                                semiFocalMaxDistance=float(semiFocalMaxDistance),
                                corridoripeMaxVal=float(corridoripeMaxVal),
                                annulusCounterMaxVal=float(annulusCounterMaxVal),
                                quadrantTotalMaxVal=int(quadrantTotalMaxVal),
                                chainingMaxCoverage=float(chainingMaxCoverage),
                                percentTraversedMaxVal=float(percentTraversedMaxVal),
                                percentTraversedMinVal=float(percentTraversedMinVal),
                                distanceToCentreMaxVal=float(distanceToCentreMaxVal),
                                thigmoMinDistance=float(thigmoMinDistance), fullThigmoMinVal=float(fullThigmoMinVal),
                                smallThigmoMinVal=float(smallThigmoMinVal), ipeIndirectMaxVal=float(ipeIndirectMaxVal),
                                percentTraversedRandomMaxVal=float(percentTraversedRandomMaxVal),
                                headingIndirectMaxVal=float(headingIndirectMaxVal),
                                useDirect=useDirectPathV, useFocal=useFocalSearchV, useDirected=useDirectedSearchV,
                                useIndirect=useIndirectV, useSemiFocal=useSemiFocalSearchV, useChaining=useChainingV,
                                useScanning=useScanningV, useRandom=useRandomV, useThigmogaxis=useThigmoV)
        except:
            params = defaultParams

        print("Running: " + str(goalPosVar) + " with diamater " + str(goalDiamVar))

        mazeDiamVar = mazeDiamStringVar.get()
        mazeCentreVar = mazeCentreStringVar.get()
        corridorWidthVar = corridorWidthStringVar.get()
        chainingRadiusVar = chainingRadiusStringVar.get()
        thigmotaxisZoneSizeVar = thigmotaxisZoneSizeStringVar.get()  # get important values
        # basic setup

        mazeRadius = 0.0
        thigmotaxisZoneSize = 0.0
        corridorWidth = 0.0
        goalX = 0.0
        goalY = 0.0
        oldDay = ""
        chainingRadius = 0.0
        mazeCentre = (0.0, 0.0)
        mazeRadius = 0.0
        fullThigmoZone = 0.0
        smallThigmoZone = 0.0
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
        semiFocalSearchCount = 0.0
        n = 0
        numOfRows = 0
        mazeCentreX, mazeCentreY = mazeCentre
        flag = False
        dayFlag = False
        autoFlag = False
        skipFlag = False
        software = softwareStringVar.get()
        if (software == "auto"):
            self.detectSoftwareType()
        software = softwareStringVar.get()

        try:
            aExperiment = saveFileAsExperiment(software, theFile, fileDirectory)
        except Exception:
            show_message("No Input")
            print("Unexpected Error loading experiment")
            traceback.print_exc()
            return

        mazeCentreX, mazeCentreY, goalX, goalY, mazeDiamVar, mazeRadius, goalDiamVar = self.getAutoLocations(
            aExperiment, goalX, goalY, goalPosVar, mazeCentreX, mazeCentreY, mazeCentreVar, mazeDiamVar, software,
            goalDiamVar)

        thigmotaxisZoneSize = float(thigmotaxisZoneSizeVar)  # update the thigmotaxis zone
        chainingRadius = float(chainingRadiusVar)  # update the chaining radius
        corridorWidth = (int(corridorWidthVar) / 2)  # update the corridor width

        smallThigmoZone = mazeRadius - math.ceil(thigmotaxisZoneSize / 2)  # update the smaller wall zone
        fullThigmoZone = mazeRadius - thigmotaxisZoneSize  # and bigger wall zone

        theStatus.set('Calculating Search Strategies...')  # update status bar
        self.updateTasks()
        currentOutputFile = outputFileStringVar.get() + str(goalPosVar) + ".csv"
        logging.debug("Calculating search strategies")
        try:  # try to open a csv file for output
            f = open(currentOutputFile, 'wt')
            writer = csv.writer(f, delimiter=',', quotechar='"')
        except Exception:
            traceback.print_exc()
            logging.error("Cannot write to " + str(currentOutputFile))
            return

        headersToWrite = []
        try:
            if aExperiment.hasDateInfo:
                headersToWrite.extend(["Date", "Time", "Day"])

            headersToWrite.append("Trial")
            if aExperiment.hasTrialNames:
                headersToWrite.append("Name")
            if aExperiment.hasAnimalNames:
                headersToWrite.append("Animal")
        except:
            pass
        headersToWrite.extend(
            ["Trial Code", "Strategy", "IPE", "Velocity", "Distance covered", "Average distance to goal",
             "Average heading error", "Percent of maze traversed", "Latency", "Score", "Initial heading error",
             "Entropy", "Distance to swim path centroid", "Average distance to centre of maze",
             "Percent in angular corridor", "Percent in annulus zone", "Percent in smaller thigmotaxis zone",
             "Percent in full thigmotaxis zone", "Strategy (manual)"])
        writer.writerow(headersToWrite)  # write to the csv

        dayNum = 0
        trialNum = {}
        curDate = None
        for aTrial in aExperiment:
            animal = aTrial.animal
            if animal in trialNum:
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

            fullThigmoCounter = 0.0
            smallThigmoCounter = 0.0
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
            score = 0
            # Analyze the data ----------------------------------------------------------------------------------------------
            corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToCentre, averageHeadingError, \
            percentTraversed, quadrantTotal, totalDistance, latency, fullThigmoCounter, smallThigmoCounter, annulusCounter, i, \
            arrayX, arrayY, velocity, ipe, initialHeadingError, entropyResult = self.calculateValues(
                aTrial, goalX, goalY, mazeCentreX,
                mazeCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, fullThigmoZone,
                smallThigmoZone, mazeRadius, dayNum, goalDiamVar)

            strategyType = ""
            strategyManual = ""
            # print(fullThigmoMinVal, smallThigmoMinVal, fullThigmoCounter/i, smallThigmoCounter/i)
            # DIRECT SWIM
            if ipe <= params.ipeMaxVal and averageHeadingError <= params.headingMaxVal and params.useDirect:  # direct path
                directPathCount += 1.0
                score = 3
                strategyType = "Direct Path"
            # FOCAL SEARCH
            elif averageDistanceToSwimPathCentroid < (
                    mazeRadius * params.distanceToSwimMaxVal / 100) and distanceAverage < (
                    params.distanceToPlatMaxVal / 100 * mazeRadius) and totalDistance < params.focalMaxDistance and totalDistance > params.focalMinDistance and params.useFocal:  # Focal Search
                focalSearchCount += 1.0
                score = 2
                strategyType = "Focal Search"
            # DIRECTED SEARCH
            elif corridorAverage >= params.corridorAverageMinVal / 100 and ipe <= params.corridoripeMaxVal and totalDistance < params.directedSearchMaxDistance and params.useDirected:  # directed search
                directSearchCount += 1.0
                score = 2
                strategyType = "Directed Search"
            # INDIRECT SEARCH
            elif ipe < params.ipeIndirectMaxVal and averageHeadingError < params.headingIndirectMaxVal and params.useIndirect:  # Near miss
                strategyType = "Indirect Search"
                score = 2
                indirectSearchCount += 1.0
            # SEMI FOCAL SEARCH
            elif averageDistanceToSwimPathCentroid < (
                    mazeRadius * params.distanceToSwimMaxVal2 / 100) and distanceAverage < (
                    params.distanceToPlatMaxVal2 / 100 * mazeRadius) and totalDistance < params.semiFocalMaxDistance and totalDistance > params.semiFocalMinDistance and params.useSemiFocal:  # Semi-Focal Search
                semiFocalSearchCount += 1.0
                score = 2
                strategyType = "Semi-focal Search"
            # CHAINING
            elif float(
                    annulusCounter / i) > params.annulusCounterMaxVal / 100 and quadrantTotal >= params.quadrantTotalMaxVal and percentTraversed < params.chainingMaxCoverage and params.useChaining:  # or 4 chaining
                chainingCount += 1.0
                score = 1
                strategyType = "Chaining"
            # SCANNING
            elif params.percentTraversedMinVal <= percentTraversed and params.percentTraversedMaxVal > percentTraversed and averageDistanceToCentre <= (
                    params.distanceToCentreMaxVal / 100 * mazeRadius) and params.useScanning:  # scanning
                scanningCount += 1.0
                score = 1
                strategyType = "Scanning"
            # THIGMOTAXIS
            elif fullThigmoCounter / i >= params.fullThigmoMinVal / 100 and smallThigmoCounter / i >= params.smallThigmoMinVal / 100 and totalDistance > params.thigmoMinDistance and params.useThigmotaxis:  # thigmotaxis
                thigmotaxisCount += 1.0
                score = 0
                strategyType = "Thigmotaxis"
            # RANDOM SEARCH
            elif percentTraversed >= params.percentTraversedRandomMaxVal and params.useRandom:  # random search
                randomCount += 1.0
                score = 0
                strategyType = "Random Search"
            # NOT RECOGNIZED
            else:  # cannot categorize
                strategyType = "Not Recognized"
                notRecognizedCount += 1.0
                if manualFlag and not useManualForAllFlag:
                    print("Day #", "Trial #", "Name", "Date", "Trial", "Strategy Type", "ipe", "velocity",
                          "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency",
                          "corridorAverage")
                    print(dayNum, trialNum, aTrial.name, aTrial.date, aTrial.trial, strategyType, round(ipe, 2),
                          round(velocity, 2), round(totalDistance, 2), round(distanceAverage, 2),
                          round(averageHeadingError, 2), round(percentTraversed, 2), round(latency, 2),
                          round(corridorAverage, 2))
                    # print("ipe: ", ipe, " Distance to centroid: ", averageDistanceToSwimPathCentroid, " Distance to plat: ", distanceAverage)
                    plotName = "Strategy " + str(strategyType) + " Animal " + str(animal) + "  Day " + str(
                        dayNum) + " Trial " + str(trialNum[animal])
                    self.plotPoints(arrayX, arrayY, float(mazeDiamVar), float(mazeCentreX), float(mazeCentreY),
                                    float(goalX), float(goalY), plotName,
                                    ("Animal: " + str(animal) + "  Day/Trial: " + str(dayNum) + "/" + str(
                                        trialNum[animal])), float(goalDiamVar))  # ask user for answer
                    root.wait_window(self.top2)  # we wait until the user responds
                    strategyManual = searchStrategyV  # update the strategyType to that of the user
                    try:  # try and kill the popup window
                        self.top2.destroy()
                    except:
                        pass

            totalTrialCount += 1.0

            n += 1
            print(animal)
            print("strategy: ", strategyType, "    ipe: ", round(ipe, 2), "    Heading: ",
                  round(averageHeadingError, 2), "    Entropy: ", entropyResult)

            if useManualForAllFlag:
                print("Day #", "Trial #", "Name", "Date", "Trial", "Strategy Type", "ipe", "velocity", "totalDistance",
                      "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage")
                print(dayNum, trialNum[animal], aTrial.name, aTrial.date, aTrial.trial, strategyType, round(ipe, 2),
                      round(velocity, 2), round(totalDistance, 2), round(distanceAverage, 2),
                      round(averageHeadingError, 2), round(percentTraversed, 2), round(latency, 2),
                      round(corridorAverage, 2))
                plotName = "Strategy " + str(strategyType) + " Animal " + str(animal) + "  Day " + str(
                    dayNum) + " Trial " + str(trialNum[animal])
                self.plotPoints(arrayX, arrayY, float(mazeDiamVar), float(mazeCentreX), float(mazeCentreY),
                                float(goalX), float(goalY), plotName,
                                ("Animal: " + str(animal) + "  Day/Trial: " + str(dayNum) + "/" + str(
                                    trialNum[animal])), float(goalDiamVar))  # ask user for answer
                root.wait_window(self.top2)  # we wait until the user responds
                strategyManual = searchStrategyV  # update the strategyType to that of the user

            dataToWrite = []


            dataToWrite.append(trialNum[animal])
            if aExperiment.hasTrialNames:
                dataToWrite.append(aTrial.name)
            if aExperiment.hasAnimalNames:
                dataToWrite.append(aTrial.animal)

            dataToWrite.extend(
                [(str(animal) + " " + str(dayNum) + " " + str(trialNum[animal])), strategyType, round(ipe, 2),
                 round(velocity, 2), round(totalDistance, 2), round(distanceAverage, 2),
                 round(averageHeadingError, 2), round(percentTraversed, 2), round(latency, 2), score,
                 initialHeadingError, round(entropyResult, 2), round(averageDistanceToSwimPathCentroid, 2),
                 round(averageDistanceToCentre, 2), round(corridorAverage, 2), round(annulusCounter / i, 2),
                 round(smallThigmoCounter / i, 2), round(fullThigmoCounter / i, 2), str(strategyManual)])
            writer.writerow(dataToWrite)  # writing to csv file

            f.flush()

        print("Direct Path: ", directPathCount, "| Directed Search: ", directSearchCount, "| Focal Search: ",
              focalSearchCount, "| Indirect Search: ", indirectSearchCount, "| Semi-focal Search: ",
              semiFocalSearchCount, "| Chaining: ", chainingCount, "| Scanning: ", scanningCount, "| Random Search: ",
              randomCount, "| Thigmotaxis: ", thigmotaxisCount, "| Not Recognized: ", notRecognizedCount)
        try:
            open_file(currentOutputFile)
        except:
            print("The system couldn't find ", currentOutputFile, " please check your output folder.")

        self.updateTasks()
        theStatus.set('')
        self.updateTasks()
        csvfilename = "output/results/results " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # update the csv file name for the next run
        outputFileStringVar.set(csvfilename)
        return


def main():
    b = mainClass(root)  # start the main class (main program)
    root.mainloop()  # loop so the gui stays


if __name__ == "__main__":  # main part of the program -- this is called at runtime
    main()
