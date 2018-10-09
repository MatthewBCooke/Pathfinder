#!/usr/bin/env python

"""searchStrategyAnalysis.py: GUI + analyses ethovision exported xlsx files to determine which search strategy animals follow during
Morris Water Maze trials."""

from __future__ import print_function
import csv
import fnmatch
import logging
import math
import os
import sys
import threading
import webbrowser
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
from appTrial import Trial, Experiment, Parameters


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
__copyright__ = "Copyright 2017, Jason Snyder Lab, The University of British Columbia"
__credits__ = ["Matthew Cooke", "Tim O'Leary"]
__email__ = "mbcooke@mail.ubc.ca"

logfilename = "logfile " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime())) + ".log"  # name of the log file for the run
logging.basicConfig(filename=logfilename,level=logging.INFO)  # set the default log type to INFO, can be set to DEBUG for more detailed information
csvfilename = "results " + str(
    strftime("%Y_%m_%d %I_%M_%S_%p", localtime())) + ".csv"  # name of the default results file
theFile = ""
fileDirectory = ""
platformPosVar = "Auto"  # -21,31
poolDiamVar = "Auto"  # 180.0
corridorWidthVar = "40"
poolCentreVar = "Auto"  # 14.43,-4.409
oldPlatformPosVar = ""
chainingRadiusVar = "40.0"
thigmotaxisZoneSizeVar = "20"
outputFile = csvfilename
fileFlag = 0

snyderParams = Parameters(name="snyder", cseMaxVal=300/24, headingMaxVal=25, distanceToSwimMaxVal=0.45,
                  distanceToPlatMaxVal=0.35, corridorAverageMinVal=0.5, corridorCseMaxVal=100000,
                  annulusCounterMaxVal=0.70, quadrantTotalMaxVal=3, percentTraversedMaxVal=60,
                  percentTraversedMinVal=10, distanceToCentreMaxVal=0.7, innerWallMaxVal=0.65,
                  outerWallMaxVal=0.3, cseIndirectMaxVal=7000/24, percentTraversedRandomMaxVal=30)

ruedigerParams = Parameters(name="ruediger", cseMaxVal=300/24, headingMaxVal=35, distanceToSwimMaxVal=0.45,
                  distanceToPlatMaxVal=0.5, corridorAverageMinVal=0.8, corridorCseMaxVal=999999999,
                  annulusCounterMaxVal=0.65, quadrantTotalMaxVal=0, percentTraversedMaxVal=70,
                  percentTraversedMinVal=15, distanceToCentreMaxVal=0.7, innerWallMaxVal=0.65,
                  outerWallMaxVal=0.35, cseIndirectMaxVal=0, percentTraversedRandomMaxVal=70)

gartheParams = Parameters(name="garthe", cseMaxVal=300/24, headingMaxVal=20, distanceToSwimMaxVal=0.35,
                  distanceToPlatMaxVal=0.3, corridorAverageMinVal=0.8, corridorCseMaxVal=999999999,
                  annulusCounterMaxVal=0.8, quadrantTotalMaxVal=0, percentTraversedMaxVal=60,
                  percentTraversedMinVal=10, distanceToCentreMaxVal=0.7, innerWallMaxVal=0.65,
                  outerWallMaxVal=0.35, cseIndirectMaxVal=0, percentTraversedRandomMaxVal=60)

params = snyderParams

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
usePerseveranceV = False

root = Tk()  # set up the root
theStatus = StringVar()  # create the status bar text
theStatus.set('Waiting for user input...')  # set status bar text
platformPosStringVar = StringVar()  # setup all the gui variables (different from normal variables)
platformPosStringVar.set(platformPosVar)
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
useScaling = BooleanVar()
useScaling.set(True)
scale = True

def show_error(text):  # popup box with error text
    logging.debug("Displaying Error")
    try:
        top = Toplevel(root)  # show as toplevel
        Label(top, text=text).pack()   # label set to text
        Button(top, text="OK", command=top.destroy).pack(pady=5)   # add ok button
    except:
        logging.info("Couldn't Display error "+text)



class csvDisplay:
    def __init__(self, root):
        global canvas
        global xscrollbar
        global vsb
        global frame
        try:  # we try to delete a canvas (if one exists this will execute)
            deleteCanvas()
            logging.info("Canvas destroyed")
        except:
            logging.debug("Didn't kill canvas, could be first call")

        logging.debug("CSV Display is called")

        try:
            canvas = Canvas(root, borderwidth=0, width=500, height=400, bg="white")  # we create the canvas
            frame = Frame(canvas)   # we place a frame in the canvas
            xscrollbar = Scrollbar(root, orient=HORIZONTAL, command=canvas.xview)   # we add a horizontal scroll bar
            xscrollbar.pack(side=BOTTOM, fill=X)   # we put the horizontal scroll bar on the bottom
            vsb = Scrollbar(root, orient="vertical", command=canvas.yview)   # vertical scroll bar
            vsb.pack(side="right", fill="y")  # put on right

            canvas.pack(side="left", fill="both", expand=True)   # we pack in the canvas
            canvas.create_window((4, 4), window=frame, anchor="nw")   # we create the window for the results

            canvas.configure(yscrollcommand=vsb.set)   # we set the commands for the scroll bars
            canvas.configure(xscrollcommand=xscrollbar.set)
            frame.bind("<Configure>", lambda event, canvas=canvas: self.onFrameConfigure(canvas))   # we bind on frame configure
        except:
            logging.critical("Couldn't create the CSV canvas") # not able to create canvas for the output

        try:   # we try and fill the canvas
            self.populate(frame)
        except Exception:   # if we can't fill
            logging.critical("Fatal error in populate") # cannot populate the CSV canvas

    def populate(self, frame):  # function to populate the canvas
        logging.debug("Populating the CSV canvas")
        with open(outputFile, newline="") as file:   # we open the file with the results
            reader = csv.reader(file)   # read the file
            # r and c tell us where to grid the labels
            r = 0
            for col in reader:
                c = 0
                for row in col:   # for all columns and rows we place a label
                    # i've added some styling
                    label = Label(frame, width=20, height=1, \
                                  text=row, relief=RIDGE)
                    label.grid(row=r, column=c)
                    c += 1
                r += 1

    def onFrameConfigure(self, canvas):  # configure the frame
        canvas.configure(scrollregion=canvas.bbox("all"))

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
        root.wm_title("Search-O-Matic 2000")

        global platformPosVar
        global poolDiamVar
        global corridorWidthVar
        global poolCentreVar
        global oldPlatformPosVar
        global chainingRadiusVar
        global thigmotaxisZoneSizeVar
        global outputFile
        global manualFlag
        global useManualForAllFlag
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
        self.fileMenu.add_command(label="Generate Heatmap", command=self.guiHeatmap)
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

        self.snyderButton = ttk.Button(self.toolbar, text="Default", command=self.snyder,
                                       style='selected.TButton')  # add snyder button
        self.snyderButton.grid(row=0, ipadx=2, pady=2, padx=2)
        self.ruedigerButton = ttk.Button(self.toolbar, text="Ruediger et al., 2012", command=self.ruediger,
                                         style='default.TButton')  # add reudiger button
        self.ruedigerButton.grid(row=0, column=1, ipadx=2, pady=2, padx=2)
        self.gartheButton = ttk.Button(self.toolbar, text="Garthe et al., 2009", command=self.garthe,
                                       style='default.TButton')  # add garthe button
        self.gartheButton.grid(row=0, column=2, ipadx=2, pady=2, padx=2)
        self.customButton = ttk.Button(self.toolbar, text="Custom...", command=self.custom, style='default.TButton')
        self.customButton.grid(row=0, column=3, ipadx=2, pady=2, padx=2)  # add custom button
        self.toolbar.pack(side=TOP, fill=X)  # place the toolbar
        self.snyderButton.bind("<Enter>", partial(self.on_enter, "Use preset values from our paper"))
        self.snyderButton.bind("<Leave>", self.on_leave)
        self.ruedigerButton.bind("<Enter>", partial(self.on_enter, "Use preset values from Ruediger et al., 2012"))
        self.ruedigerButton.bind("<Leave>", self.on_leave)
        self.gartheButton.bind("<Enter>", partial(self.on_enter, "Use preset values from Garthe et al., 2009"))
        self.gartheButton.bind("<Leave>", self.on_leave)
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
        self.softwareBar.pack(side=TOP, fill=X, pady =5)

        self.ethovisionRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Ethovision to generate your data"))
        self.ethovisionRadio.bind("<Leave>", self.on_leave)
        self.anymazeRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Anymaze to generate your data"))
        self.anymazeRadio.bind("<Leave>", self.on_leave)
        self.watermazeRadio.bind("<Enter>", partial(self.on_enter, "Click if you used Watermaze to generate your data"))
        self.watermazeRadio.bind("<Leave>", self.on_leave)

        # ******* STATUS BAR *******
        self.status = Label(root, textvariable=theStatus, bd=1, relief=SUNKEN, anchor=W, bg="white")  # setup the status bar
        self.status.pack(side=BOTTOM, anchor=W, fill=X)  # place the status bar

        # ****** PARAMETERS SIDE ******
        self.paramFrame = Frame(root, bd=1, bg="white")  # create a frame for the parameters
        self.paramFrame.pack(side=LEFT, fill=BOTH, padx=5, pady=5)  # place this on the left

        try:
            with open('mainobjs.pickle', 'rb') as f:
                platformPosVar, poolDiamVar, poolCentreVar, oldPlatformPosVar, corridorWidthVar, chainingRadiusVar, thigmotaxisZoneSizeVar, softwareScalingFactorVar = pickle.load(f)
                platformPosStringVar.set(platformPosVar)
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

        self.poolDiam = Label(self.paramFrame, text="Pool Diameter (cm):", bg="white")
        self.poolDiam.grid(row=1, column=0, sticky=E)
        self.poolDiamE = Entry(self.paramFrame, textvariable=poolDiamStringVar)
        self.poolDiamE.grid(row=1, column=1)
        self.poolDiam.bind("<Enter>", partial(self.on_enter, "The diameter of the MWM. Use the same unit as the data"))
        self.poolDiam.bind("<Leave>", self.on_leave)

        self.poolCentre = Label(self.paramFrame, text="Pool Centre (x,y):", bg="white")
        self.poolCentre.grid(row=2, column=0, sticky=E)
        self.poolCentreE = Entry(self.paramFrame, textvariable=poolCentreStringVar)
        self.poolCentreE.grid(row=2, column=1)
        self.poolCentre.bind("<Enter>", partial(self.on_enter, "Pool Centre. Example: 0.0,0.0 or Auto"))
        self.poolCentre.bind("<Leave>", self.on_leave)

        self.oldPlatformPos = Label(self.paramFrame, text="Old Platform Position (x,y):", bg="white")
        self.oldPlatformPos.grid(row=3, column=0, sticky=E)
        self.oldPlatformPosE = Entry(self.paramFrame, textvariable=oldPlatformPosStringVar)
        self.oldPlatformPosE.grid(row=3, column=1)
        self.oldPlatformPos.bind("<Enter>", partial(self.on_enter, "Used only if you want to calculate a perseverance measure"))
        self.oldPlatformPos.bind("<Leave>", self.on_leave)

        self.headingError = Label(self.paramFrame, text="Corridor Width (degrees):", bg="white")
        self.headingError.grid(row=4, column=0, sticky=E)
        self.headingErrorE = Entry(self.paramFrame, textvariable=corridorWidthStringVar)
        self.headingErrorE.grid(row=4, column=1)
        self.headingError.bind("<Enter>", partial(self.on_enter, "This is an angular corridor (in degrees) in which the animal must face"))
        self.headingError.bind("<Leave>", self.on_leave)


        self.chainingRadius = Label(self.paramFrame, text="Chaining Width (cm):", bg="white")
        self.chainingRadius.grid(row=5, column=0, sticky=E)
        self.chainingRadiusE = Entry(self.paramFrame, textvariable=chainingRadiusStringVar)
        self.chainingRadiusE.grid(row=5, column=1)
        self.chainingRadius.bind("<Enter>", partial(self.on_enter, "The diameter of the ring in which chaining is considered (centered on platform)"))
        self.chainingRadius.bind("<Leave>", self.on_leave)


        self.thigmotaxisZoneSize = Label(self.paramFrame, text="Thigmotaxis Zone Size (cm):", bg="white")
        self.thigmotaxisZoneSize.grid(row=6, column=0, sticky=E)
        self.thigmotaxisZoneSizeE = Entry(self.paramFrame, textvariable=thigmotaxisZoneSizeStringVar)
        self.thigmotaxisZoneSizeE.grid(row=6, column=1)
        self.thigmotaxisZoneSize.bind("<Enter>", partial(self.on_enter, "Size of the zone in which thigmotaxis is considered (from the outer wall)"))
        self.thigmotaxisZoneSize.bind("<Leave>", self.on_leave)


        self.softwareScalingFactor = Label(self.paramFrame, text="Pixels/cm (for Anymaze and Watermaze):", bg="white")
        self.softwareScalingFactor.grid(row=7, column=0, sticky=E)
        self.softwareScalingFactorE = Entry(self.paramFrame, textvariable=softwareScalingFactorStringVar)
        self.softwareScalingFactorE.grid(row=7, column=1)
        self.softwareScalingFactor.bind("<Enter>", partial(self.on_enter, "This is used to convert Anymaze and Watermaze from Pixels to cm"))
        self.softwareScalingFactor.bind("<Leave>", self.on_leave)


        self.saveDirectory = Label(self.paramFrame, text="Output File (.csv):", bg="white")
        self.saveDirectory.grid(row=8, column=0, sticky=E)
        self.saveDirectoryE = Entry(self.paramFrame, textvariable=outputFileStringVar)
        self.saveDirectoryE.grid(row=8, column=1)
        self.saveDirectory.bind("<Enter>", partial(self.on_enter, "The csv file to store the results"))
        self.saveDirectory.bind("<Leave>", self.on_leave)


        global outputFile  # allow outputFile to be accessed from anywhere (not secure)
        outputFile = outputFileStringVar.get()  # get the value entered for the ouput file

        manualFlag = False  # a flag that lets us know if we want to use manual categorization
        useManualForAllFlag = False

        self.scalingTickL = Label(self.paramFrame, text="Scale Values: ", bg="white")  # label for the tickbox
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

        useManualForAllFlag = useManualForAll.get()


        manualFlag = useManual.get()  # get the value of the tickbox

        self.calculateButton = Button(self.paramFrame, text="Calculate", fg="black",
                                      command=self.manual)  # add a button that says calculate
        self.calculateButton.grid(row=17, column=0, columnspan=3)



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
        theFile = filedialog.askopenfilename(filetypes = (("Excel Files","*.xlsx;*.xls"),("CSV Files","*.csv")))  # look for xlsx and xls files

    def openDir(self):  # open dialog to get multiple files
        logging.debug("Open Dir...")
        global fileDirectory
        global theFile
        global fileFlag
        fileFlag = 0
        theFile = ""
        fileDirectory = filedialog.askdirectory(mustexist=TRUE)

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
        manualFlag = useManual.get()
        useManualForAllFlag = useManualForAll.get()
        if manualFlag or useManualForAllFlag:  # if we want manual we can't use threading
            self.mainCalculate()
        else:  # else start the threads
            self.mainThreader()

    def snyder(self):  # actions on button press (snyder button)
        logging.debug("Snyder selected")
        self.snyderButton.configure(style='selected.TButton')  # change the style of the selected
        self.gartheButton.configure(style='default.TButton')  # and non-selected buttons
        self.ruedigerButton.configure(style='default.TButton')
        self.customButton.configure(style='default.TButton')
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
        # # values we need access to
        # # what these values should be
        # cseMaxVal = snyderCseMaxVal
        # headingMaxVal = snyderHeadingMaxVal
        # distanceToSwimMaxVal = snyderDistanceToSwimMaxVal
        # distanceToPlatMaxVal = snyderDistanceToPlatMaxVal
        # corridorAverageMinVal = snyderCorridorAverageMinVal
        # corridorCseMaxVal = snyderCorridorCseMaxVal
        # annulusCounterMaxVal = snyderAnnulusCounterMaxVal
        # quadrantTotalMaxVal = snyderQuadrantTotalMaxVal
        # percentTraversedMaxVal = snyderPercentTraversedMaxVal
        # percentTraversedMinVal = snyderPercentTraversedMinVal
        # distanceToCentreMaxVal = snyderDistanceToCentreMaxVal
        # innerWallMaxVal = snyderInnerWallMaxVal
        # outerWallMaxVal = snyderOuterWallMaxVal
        # cseIndirectMaxVal = snyderCseIndirectMaxVal
        # percentTraversedRandomMaxVal = snyderPercentTraversedRandomMaxVal
        params = snyderParams

    def ruediger(self):  # see snyder
        logging.debug("Ruediger selected")
        self.snyderButton.configure(style='default.TButton')
        self.gartheButton.configure(style='default.TButton')
        self.ruedigerButton.configure(style='selected.TButton')
        self.customButton.configure(style='default.TButton')

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
        # global isRuediger
        #
        # cseMaxVal = 300/24
        # headingMaxVal = 35
        # distanceToSwimMaxVal = 0.45
        # distanceToPlatMaxVal = 0.5
        # corridorAverageMinVal = 0.8
        # corridorCseMaxVal = 999999999  # inf
        # annulusCounterMaxVal = 0.65
        # quadrantTotalMaxVal = 0
        # percentTraversedMaxVal = 70
        # percentTraversedMinVal = 15
        # distanceToCentreMaxVal = 0.7
        # innerWallMaxVal = 0.65
        # outerWallMaxVal = 0.35
        # cseIndirectMaxVal = 0
        # percentTraversedRandomMaxVal = 70
        # isRuediger = True
        params = ruedigerParams

    def garthe(self):  # see snyder
        logging.debug("Garthe selected")
        self.snyderButton.configure(style='default.TButton')
        self.gartheButton.configure(style='selected.TButton')
        self.ruedigerButton.configure(style='default.TButton')
        self.customButton.configure(style='default.TButton')


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

        # cseMaxVal = 300/24
        # headingMaxVal = 20
        # distanceToSwimMaxVal = 0.35
        # distanceToPlatMaxVal = 0.3
        # corridorAverageMinVal = 0.8
        # corridorCseMaxVal = 999999999  # inf
        # annulusCounterMaxVal = 0.8
        # quadrantTotalMaxVal = 0
        # percentTraversedMaxVal = 60
        # percentTraversedMinVal = 10
        # distanceToCentreMaxVal = 0.7
        # innerWallMaxVal = 0.65
        # outerWallMaxVal = 0.35
        # cseIndirectMaxVal = 0
        # percentTraversedRandomMaxVal = 60
        params = gartheParams

    def custom(self):
        logging.debug("Getting custom values")
        global cseMaxVal
        global headingMaxVal
        global distanceToSwimMaxVal
        global distanceToPlatMaxVal
        global corridorAverageMinVal
        global annulusCounterMaxVal
        global quadrantTotalMaxVal
        global corridorCseMaxVal
        global percentTraversedMaxVal
        global percentTraversedMinVal
        global distanceToCentreMaxVal
        global innerWallMaxVal
        global outerWallMaxVal
        global cseIndirectMaxVal
        global percentTraversedRandomMaxVal

        global useDirectSwimV
        global useFocalSearchV
        global useDirectedSearchV
        global useScanningV
        global useChainingV
        global useRandomV
        global useIndirectV
        global useThigmoV
        global usePerseveranceV

        self.useDirectSwim = BooleanVar()
        self.useFocalSearch = BooleanVar()
        self.useDirectedSearch = BooleanVar()
        self.useScanning = BooleanVar()
        self.useChaining = BooleanVar()
        self.useRandom = BooleanVar()
        self.useIndirect = BooleanVar()
        self.useThigmo = BooleanVar()
        self.usePerseverance = BooleanVar()

        self.snyderButton.configure(style='default.TButton')
        self.gartheButton.configure(style='default.TButton')
        self.ruedigerButton.configure(style='default.TButton')
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

        try:
            with open('customobjs.pickle', 'rb') as f:
                cseMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, corridorAverageMinVal, corridorCseMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, innerWallMaxVal, outerWallMaxVal, cseIndirectMaxVal, percentTraversedRandomMaxVal, useDirectSwimV, useFocalSearchV, useDirectedSearchV, useScanningV, useChainingV, useRandomV, useIndirectV, useThigmoV, usePerseveranceV = pickle.load(f)
                self.useDirectSwim.set(useDirectSwimV)
                self.useFocalSearch.set(useFocalSearchV)
                self.useDirectedSearch.set(useDirectedSearchV)
                self.useScanning.set(useScanningV)
                self.useChaining.set(useChainingV)
                self.useRandom.set(useRandomV)
                self.useIndirect.set(useIndirectV)
                self.useThigmo.set(useThigmoV)
                self.usePerseverance.set(usePerseveranceV)
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

            self.useDirectSwim.set(True)
            self.useFocalSearch.set(True)
            self.useDirectedSearch.set(True)
            self.useScanning.set(True)
            self.useChaining.set(True)
            self.useRandom.set(True)
            self.useIndirect.set(True)
            self.useThigmo.set(True)
            self.usePerseverance.set(False)


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
        # all of the above is the same as in snyder, plus the creation of variables to hold values from the custom menu

        self.top = Toplevel(root)  # we set this to be the top
        self.top.configure(bg="white")
        Label(self.top, text="Custom Values", bg="white", fg="red").grid(row=0, column=0, columnspan=2)  # we title it



        useDirectSwimL = Label(self.top, text="Direct Swim: ", bg="white")  # we add a direct swim label
        useDirectSwimL.grid(row=1, column=0, sticky=E)  # stick it to row 1
        useDirectSwimC = Checkbutton(self.top, variable=self.useDirectSwim, bg="white")  # we add a direct swim checkbox
        useDirectSwimC.grid(row=1, column=1)  # put it beside the label

        jslsMaxCustomL = Label(self.top, text="Cumulative Search Error [maximum]: ", bg="white")  # label for JSLs
        jslsMaxCustomL.grid(row=2, column=0, sticky=E)  # row 2
        jslsMaxCustomE = Entry(self.top, textvariable=self.jslsMaxCustom)  # entry field
        jslsMaxCustomE.grid(row=2, column=1)  # right beside

        headingErrorCustomL = Label(self.top, text="Heading degree error [maximum]: ", bg="white")
        headingErrorCustomL.grid(row=3, column=0, sticky=E)
        headingErrorCustomE = Entry(self.top, textvariable=self.headingErrorCustom)
        headingErrorCustomE.grid(row=3, column=1)


        useFocalSearchL = Label(self.top, text="Focal Search: ", bg="white")
        useFocalSearchL.grid(row=4, column=0, sticky=E)
        useFocalSearchC = Checkbutton(self.top, variable=self.useFocalSearch, bg="white")
        useFocalSearchC.grid(row=4, column=1)

        usePerseveranceL = Label(self.top, text="Perseverance: ", bg="white")
        usePerseveranceL.grid(row=5, column=0, sticky=E)
        usePerseveranceC = Checkbutton(self.top, variable=self.usePerseverance, bg="white")
        usePerseveranceC.grid(row=5, column=1)

        distanceToSwimCustomL = Label(self.top, text="Distance to swim path centroid [% of radius]: ", bg="white")
        distanceToSwimCustomL.grid(row=6, column=0, sticky=E)
        distanceToSwimCustomE = Entry(self.top, textvariable=self.distanceToSwimCustom)
        distanceToSwimCustomE.grid(row=6, column=1)

        distanceToPlatCustomL = Label(self.top, text="Distance to platform [% of radius]: ", bg="white")
        distanceToPlatCustomL.grid(row=7, column=0, sticky=E)
        distanceToPlatCustomL = Entry(self.top, textvariable=self.distanceToPlatCustom)
        distanceToPlatCustomL.grid(row=7, column=1)


        useDirectedSearchL = Label(self.top, text="Directed Search: ", bg="white")
        useDirectedSearchL.grid(row=8, column=0, sticky=E)
        useDirectedSearchC = Checkbutton(self.top, variable=self.useDirectedSearch, bg="white", onvalue=1)
        useDirectedSearchC.grid(row=8, column=1)

        corridorAverageCustomL = Label(self.top, text="Angular corridor minimum [% of time]: ", bg="white")
        corridorAverageCustomL.grid(row=9, column=0, sticky=E)
        corridorAverageCustomE = Entry(self.top, textvariable=self.corridorAverageCustom)
        corridorAverageCustomE.grid(row=9, column=1)

        corridorJslsCustomL = Label(self.top, text="Cumulative Search Error [maximum]: ", bg="white")
        corridorJslsCustomL.grid(row=10, column=0, sticky=E)
        corridorJslsCustomE = Entry(self.top, textvariable=self.corridorJslsCustom)
        corridorJslsCustomE.grid(row=10, column=1)


        useIndirectL = Label(self.top, text="Spatial Indirect: ", bg="white")
        useIndirectL.grid(row=11, column=0, sticky=E)
        useIndirectC = Checkbutton(self.top, variable=self.useIndirect, bg="white")
        useIndirectC.grid(row=11, column=1)

        jslsIndirectCustomL = Label(self.top, text="Cumulative Search Error [maximum]: ", bg="white")
        jslsIndirectCustomL.grid(row=12, column=0, sticky=E)
        jslsIndirectCustomE = Entry(self.top, textvariable=self.jslsIndirectCustom)
        jslsIndirectCustomE.grid(row=12, column=1)


        useChainingL = Label(self.top, text="Chaining: ", bg="white")
        useChainingL.grid(row=13, column=0, sticky=E)
        useChainingC = Checkbutton(self.top, variable=self.useChaining, bg="white")
        useChainingC.grid(row=13, column=1)

        annulusCustomL = Label(self.top, text="Time in annulus zone [% of time]: ", bg="white")
        annulusCustomL.grid(row=14, column=0, sticky=E)
        annulusCustomE = Entry(self.top, textvariable=self.annulusCustom)
        annulusCustomE.grid(row=14, column=1)

        quadrantTotalCustomL = Label(self.top, text="Quadrants visited [minimum]: ", bg="white")
        quadrantTotalCustomL.grid(row=15, column=0, sticky=E)
        quadrantTotalCustomE = Entry(self.top, textvariable=self.quadrantTotalCustom)
        quadrantTotalCustomE.grid(row=15, column=1)


        useScanningL = Label(self.top, text="Scanning: ", bg="white")
        useScanningL.grid(row=16, column=0, sticky=E)
        useScanningC = Checkbutton(self.top, variable=self.useScanning, bg="white")
        useScanningC.grid(row=16, column=1)

        percentTraversedCustomL = Label(self.top, text="Area traversed [maximum]: ", bg="white")
        percentTraversedCustomL.grid(row=17, column=0, sticky=E)
        percentTraversedCustomE = Entry(self.top, textvariable=self.percentTraversedCustom)
        percentTraversedCustomE.grid(row=17, column=1)

        percentTraversedMinCustomL = Label(self.top, text="Area traversed [minimum]: ", bg="white")
        percentTraversedMinCustomL.grid(row=18, column=0, sticky=E)
        percentTraversedMinCustomE = Entry(self.top, textvariable=self.percentTraversedMinCustom)
        percentTraversedMinCustomE.grid(row=18, column=1)

        distanceToCentreCustomL = Label(self.top, text="Average distance to center [% of radius]: ", bg="white")
        distanceToCentreCustomL.grid(row=19, column=0, sticky=E)
        distanceToCentreCustomE = Entry(self.top, textvariable=self.distanceToCentreCustom)
        distanceToCentreCustomE.grid(row=19, column=1)


        useThigmoL = Label(self.top, text="Thigmotaxis: ", bg="white")
        useThigmoL.grid(row=20, column=0, sticky=E)
        useThigmoC = Checkbutton(self.top, variable=self.useThigmo, bg="white")
        useThigmoC.grid(row=20, column=1)

        innerWallCustomL = Label(self.top, text="Inner wall zone [% of time]: ", bg="white")
        innerWallCustomL.grid(row=21, column=0, sticky=E)
        innerWallCustomE = Entry(self.top, textvariable=self.innerWallCustom)
        innerWallCustomE.grid(row=21, column=1)

        outerWallCustomL = Label(self.top, text="Outer wall zone [% of time]: ", bg="white")
        outerWallCustomL.grid(row=22, column=0, sticky=E)
        outerWallCustomE = Entry(self.top, textvariable=self.outerWallCustom, bg="white")
        outerWallCustomE.grid(row=22, column=1)


        useRandomL = Label(self.top, text="Random Search: ", bg="white")
        useRandomL.grid(row=23, column=0, sticky=E)
        useRandomC = Checkbutton(self.top, variable=self.useRandom, bg="white")
        useRandomC.grid(row=23, column=1)

        percentTraversedRandomCustomL = Label(self.top, text="Area traversed [% minimum]: ", bg="white")
        percentTraversedRandomCustomL.grid(row=24, column=0, sticky=E)
        percentTraversedRandomCustomE = Entry(self.top, textvariable=self.percentTraversedRandomCustom)
        percentTraversedRandomCustomE.grid(row=24, column=1)

        # we save the values from the fields and scale them appropriately

        Button(self.top, text="Save", command=self.saveCuston).grid(row=25, column=0, columnspan=2)  # button to save

    def saveCuston(self):  # save the custom values
        logging.debug("Saving custom parameters")
        global cseMaxVal
        global headingMaxVal
        global distanceToSwimMaxVal
        global distanceToPlatMaxVal
        global corridorAverageMinVal
        global annulusCounterMaxVal
        global quadrantTotalMaxVal
        global corridorCseMaxVal
        global percentTraversedMaxVal
        global percentTraversedMinVal
        global distanceToCentreMaxVal
        global innerWallMaxVal
        global outerWallMaxVal
        global cseIndirectMaxVal
        global percentTraversedRandomMaxVal

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

        params = Parameters(name="custom", cseMaxVal=float(self.jslsMaxCustom.get()), headingMaxVal=float(self.headingErrorCustom.get()), distanceToSwimMaxVal=float(self.distanceToSwimCustom.get())/100,
                          distanceToPlatMaxVal=float(self.distanceToPlatCustom.get())/100, corridorAverageMinVal=float(self.corridorAverageCustom.get()) / 100, corridorCseMaxVal=float(self.corridorJslsCustom.get()),
                          annulusCounterMaxVal=float(self.annulusCustom.get())/100, quadrantTotalMaxVal=float(self.quadrantTotalCustom.get()), percentTraversedMaxVal=float(self.percentTraversedCustom.get()),
                          percentTraversedMinVal=float(self.percentTraversedMinCustom.get()), distanceToCentreMaxVal=float(self.distanceToCentreCustom.get())/100, innerWallMaxVal=float(self.innerWallCustom.get())/100,
                          outerWallMaxVal=float(self.outerWallCustom.get())/100, cseIndirectMaxVal=float(self.jslsIndirectCustom.get()), percentTraversedRandomMaxVal=float(self.percentTraversedRandomCustom.get()))

        useDirectSwimV = self.useDirectSwim.get()
        useFocalSearchV = self.useFocalSearch.get()
        useDirectedSearchV = self.useDirectedSearch.get()
        useScanningV = self.useScanning.get()
        useChainingV = self.useChaining.get()
        useRandomV = self.useRandom.get()
        useIndirectV = self.useIndirect.get()
        useThigmoV = self.useThigmo.get()
        usePerseveranceV = self.usePerseverance.get()
        try:
            with open('customobjs.pickle', 'wb') as f:
                pickle.dump([cseMaxVal, headingMaxVal, distanceToSwimMaxVal, distanceToPlatMaxVal, corridorAverageMinVal, corridorCseMaxVal, annulusCounterMaxVal, quadrantTotalMaxVal, percentTraversedMaxVal, percentTraversedMinVal, distanceToCentreMaxVal, innerWallMaxVal, outerWallMaxVal, cseIndirectMaxVal, percentTraversedRandomMaxVal, useDirectSwimV, useFocalSearchV, useDirectedSearchV, useScanningV, useChainingV, useRandomV, useIndirectV, useThigmoV, usePerseveranceV], f)
        except:
            pass
        try:
            self.top.destroy()
        except:
            pass

    def saveFileAsTrial(self,software,aFile,fileDirectory,theFile):
        trialList = []
        if fileDirectory == "":  # if we didnt select a directory
            if theFile == "":  # or a file
                experimentName= theFile
                messagebox.showwarning('No file or directory selected', 'Please select a directory or file under the File menu')
                self.killBar()
                logging.error("Unable to find trials")
                return  # stop
        else:
            experimentName = fileDirectory

        if software == "ethovision":
            logging.info("Extension set to xlsx")
            extensionType = r'*.xlsx'
            softwareScalingFactorVar = 1.0
            logging.info("Reading file ethovision")
            i = 0.0
            try:
                wb = open_workbook(aFile)
                logging.debug("Opened" + aFile)
            except:
                # print("Corrupted excel file", aFile)
                logging.error("Unable to open excel file" + aFile)
                try:
                    show_error("Corrupted Excel File " + aFile)
                except:
                    pass
                return

            for sheet in wb.sheets():  # for all sheets in the workbook
                number_of_rows = sheet.nrows
                headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet
                numOfRows = sheet.nrows - headerLines
                number_of_columns = sheet.ncols
                fullTrial = []
                rows = []
                k = 0
                cCondition = ""
                cTreatment = ""
                cDay = ""
                cTemp = ""
                cGen = ""
                cAnimalID = ""
                cTrName = ""
                cTrID = ""
                cTr = ""

                for k in range(0, 39):  # GET CONDITION TREATMENT AND DAY VALUES
                    if str(sheet.cell(k, 0).value) == "Condition" or str(sheet.cell(k, 0).value) == "Restraint":
                        cCondition = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Treatment":
                        cTreatment = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Day":
                        cDay = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Temperature":
                        cTemp = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Genotype":
                        cGen = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Animal ID":
                        cAnimalID = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Trial name":
                        cTrName = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Trial ID":
                        cTrID = str(sheet.cell(k, 1).value)
                    elif str(sheet.cell(k, 0).value) == "Trial":
                        cTr = str(sheet.cell(k, 1).value)


                for row in range(headerLines, number_of_rows):  # for each row

                    values = []
                    values.append(aFile)
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
            extensionType = r'*.csv'
            logging.info("Extension set to csv")
            softwareScalingFactorVar = 1.0/float(softwareScalingFactorVar)
        elif software == "watermaze":
            extensionType = r'*.csv'
            logging.info("Extension set to csv")
            softwareScalingFactorVar = 1.0/float(softwareScalingFactorVar)
        else:
            logging.critical("Could not determine trial, saveFileAsTrial")

        return Experiment(experimentName, trialList)

    def mainThreader(self):  # start the threaded execution
        logging.debug("Threading")

        try:
            t1 = threading.Thread(target=self.mainCalculate)  # create a thread for the main function
            t1.start()  # start that thread
            logging.debug("Threading mainCalculate thread started")
        except Exception:
            logging.critical("Fatal error in mainCalculate")  # couldnt be started
        try:
            t2 = threading.Thread(target=self.progressBar)  # create a thread for the progressBar
            t2.start()  # start that thread
            logging.debug("Threading progressBar thread started")
        except Exception:
            logging.critical("Fatal error in progressBar")  # couldn't be started

    def progressBar(self):  # create a progressbar
        logging.debug("ProgressBar")
        try:
            self.progress = ttk.Progressbar(orient="vertical", length=200, mode="determinate")  # create the bar
            self.progress.pack(side=LEFT)  # pack it left
            self.progress.start()  # start the bar
        except:
            logging.info("Couldn't generate a progressBar")

    def find_files(self, directory, pattern):  # searches for our files in the directory
        logging.debug("Finding files in the directory")
        for root, dirs, files in os.walk(directory):
            for basename in sorted(files):
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename

    def plotPoints(self, x, y, poolDiam, centreX, centreY, platX, platY, scalingFactor, name, platEstDiam):  # function to graph the data for the not recognized trials
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

        plotName = name + " " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # the name will be Animal id followed by the date and time
        plt.scatter(x, y, s=15, c='r', alpha=1.0)  # we plot the XY position of animal
        plt.scatter(x[0],y[0], s=100, c='b', alpha=1, marker='s')  # we plot the start point
        plt.scatter(platWallsX, platWallsY, s=1, c='black', alpha=1.0)  # we plot the platform
        plt.scatter(centreX, centreY, s=100, c='g', alpha=1.0)  # we plot the centre
        plt.scatter(wallsX, wallsY, s=15, c='black', alpha=0.3)
        plt.title(name)  # add the title
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
        Label(self.top2, text=name, bg="white", fg="black", width=15).grid(row=0, column=0, columnspan = 7)  # add a title
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

    def guiHeatmap(self):

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

        self.heatmapSettings(self.top3)

        Button(self.top3, text="Generate", command=self.heatmap, fg="black", bg="white").pack()

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

    def updateTasks(self):  # called when we want to push an update to the GUI
        try:
            root.update_idletasks()
            root.update()  # update the gui
        except:
            logging.info("Couldn't update the GUI")

    def killBar(self):  # called when we want to kill the progressBar
        try:
            self.progress.stop()
            self.progress.destroy()
        except:
            logging.info("Couldn't destroy the progressBar")

    def csvDestroy(self):
        try:  # try to remove the csv display (for second run)
            theStatus.set('Removing CSV display...')
            self.updateTasks()
            frame.grid_forget()
            canvas.grid_forget()
            frame.destroy()
            canvas.destroy()
            vsb.destroy()
            xscrollbar.destroy()
            logging.info("CSV display destroyed")
        except:
            logging.debug("Couldn't remove CSV display")

    def heatmap(self):
        global values
        global flags


        if fileDirectory == "":  # if we didnt select a directory
            messagebox.showwarning('No file or directory selected', 'Please select a directory or file under the File menu')
            logging.error("Unable to find trials")
            return  # stop
        software = softwareStringVar.get()
        if software == "ethovision":
            logging.info("Extension set to xlsx")
            extensionType = r'*.xlsx'
        elif software == "anymaze":
            extensionType = r'*.csv'
            logging.info("Extension set to csv")
        elif software == "watermaze":
            extensionType = r'*.csv'
            logging.info("Extension set to csv")
        logging.debug("Heatmap Called")
        theStatus.set("Generating Heatmap...")
        self.updateTasks()

        n = 0
        condition = ""
        genotype = ""
        n += 1
        x = []
        y = []
        i = 0
        xMin = 0.0
        yMin = 0.0
        xMax = 0.0
        yMax = 0.0
        finalTemp = ""
        finalGeno = ""



        for aFile in self.find_files(fileDirectory, extensionType):  # for all the files we find
            theStatus.set("Running " + aFile)
            if software == "ethovision":
                i = 0.0
                try:
                    wb = open_workbook(aFile)
                    logging.debug("Opened" + aFile)
                except:
                    logging.error("Could not open excel file: " + aFile)
                    continue

                for sheet in wb.sheets():  # for all sheets in the workbook
                    arrayX = []
                    arrayY = []
                    number_of_rows = sheet.nrows
                    headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet
                    numOfRows = sheet.nrows - headerLines
                    number_of_columns = sheet.ncols
                    fullTrial = []
                    rows = []
                    k = 0

                    continueVar=False

                    variableFlagsCounter = 0
                    for flag in flags:
                        if flags[variableFlagsCounter].get():
                            for row in range(headerLines):
                                if labels[variableFlagsCounter] == str(sheet.cell(row, 0).value):
                                    if heatValues[variableFlagsCounter].get() != str(sheet.cell(row, 1).value):
                                        continueVar = True
                        variableFlagsCounter += 1

                    if continueVar:
                        continue

                    for row in range(headerLines, number_of_rows):  # for each row

                        values = []

                        for col in range(1, 4):  # for columns 1 through 4, get all the values
                            value = sheet.cell(row, col).value
                            try:
                                value = float(value)
                            except ValueError:
                                pass
                            finally:
                                values.append(value)

                        item = Trial(*values)
                        fullTrial.append(item)


            elif software == "anymaze":
                columns = defaultdict(list)  # each value in each column is appended to a list
                arrayX = []
                arrayY = []
                oldItemX = 0.0
                oldItemY = 0.0
                try:
                    f = open(aFile)
                    logging.debug("Opened" + aFile)
                except:
                    logging.info("Could not open " + aFile)
                    continue
                reader = csv.reader(f, delimiter=",")
                next(reader)
                number_of_columns = 3
                number_of_rows = 0
                for row in reader:
                    number_of_rows += 1
                    for (i, v) in enumerate(row):
                        columns[i].append(v)

                headerLines = 0  # gets number of header lines in the spreadsheet
                numOfRows = number_of_rows

                fullTrial = []
                rows = []
                k = 0
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
                    item = Trial(*values)
                    fullTrial.append(item)
                cTrName = aFile


            elif software == "watermaze":
                columns = defaultdict(list)  # each value in each column is appended to a list

                oldItemX = 0.0
                oldItemY = 0.0
                number_of_columns = 0
                number_of_rows = 0
                try:
                    f = open(aFile)
                except:
                    logging.info("Could not open " + aFile)
                    continue
                reader = csv.reader(f, delimiter=",")
                for row in reader:
                    number_of_rows += 1
                    for (i, v) in enumerate(row):
                        columns[i].append(v)
                        number_of_columns = i

                headerLines = 0  # gets number of header lines in the spreadsheet
                numOfRows = number_of_rows
                rows = []
                k = 0
                firstFlag = True
                secondFlag = False
                for i in range(0, math.floor(number_of_columns / 3)):
                    firstFlag = True
                    secondFlag = False
                    arrayX = []
                    arrayY = []
                    fullTrial = []
                    for a, b, c in zip(columns[i * 3], columns[1 + i * 3], columns[2 + i * 3]):
                        values = []
                        if firstFlag == True:
                            if a == "" or b == "" or c == "":
                                continue
                            cTr = a
                            cTrID = b
                            cTrName = c  # round((math.floor(cTrName) + (((cTrName) % math.floor(cTrName)) * 60) / 100), 2)
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
                            fullTrial.append(item)

                    for item in fullTrial:
                        # Create data
                        if item.x == "-" or item.y == "-":
                            continue
                        if item.time > 60.0:
                            continue
                        x.append(float(item.x))
                        y.append(float(item.y))

                        if item.x < xMin:
                            xMin = item.x
                        if item.y < yMin:
                            yMin = item.y
                        if item.x > xMax:
                            xMax = item.x
                        if item.y > yMax:
                            yMax = item.y

            for item in fullTrial:
                # Create data
                if item.x == "-" or item.y == "-":
                    continue
                if item.time > 60.0:
                    continue
                x.append(float(item.x))
                y.append(float(item.y))

                if item.x < xMin:
                    xMin = item.x
                if item.y < yMin:
                    yMin = item.y
                if item.x > xMax:
                    xMax = item.x
                if item.y > yMax:
                    yMax = item.y



        aFileName = "heatmap " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime()))  # name of the log file for the run
        aTitle = fileDirectory

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

    def getAutoLocations(self, software, platformX, platformY, platformPosVar, poolCentreX, poolCentreY, poolCentreVar, poolDiamVar, fileDirectory, extensionType, theFile):
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
        centreFlag = False
        platFlag = False
        diamFlag = False
        logginText = ""
        if platformPosVar != "Auto" and platformPosVar != "auto" and platformPosVar != "automatic" and platformPosVar != "Automatic" and platformPosVar != "":  # if we want manual platform
            platformX, platformY = platformPosVar.split(",")
            platformX = float(platformX)
            platformY = float(platformY)
            platEstDiam = 12.0
            logging.debug("Platform position set manually: "+str(platformPosVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get platform position from single trial")
            self.killBar()
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter concrete positions for a single trial')
            return
        else:  # automatic platform calculation
            platFlag = True

        if poolCentreVar != "Auto" and poolCentreVar != "auto" and poolCentreVar != "automatic" and poolCentreVar != "Automatic" and poolCentreVar != "":  # manual pool center
            poolCentreX, poolCentreY = poolCentreVar.split(",")
            poolCentreX = float(poolCentreX)
            poolCentreY = float(poolCentreY)
            logging.debug("Pool centre set manually: "+str(poolCentreVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Cannot get pool centre from single trial")
            self.killBar()
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter concrete positions for a single trial')
            return
        else:  # automatic pool centre
            centreFlag = True

        if poolDiamVar != "Auto" and poolDiamVar != "auto" and poolDiamVar != "automatic" and poolDiamVar != "Automatic" and poolDiamVar != "":  # manual diameter
            poolRadius = float(poolDiamVar) / 2.0
            logging.debug("Pool diameter set manually: " + str(poolDiamVar))
        elif fileFlag == 1 and software != "watermaze":  # if we only chose 1 trial
            logging.error("Tried to get diameter from single trial")
            self.killBar()
            theStatus.set('Waiting for user input...')
            self.updateTasks()
            messagebox.showwarning('File Error',
                                   'You must enter concrete positions for a single trial')
            return
        else:  # automatic diameter
            diamFlag = True

        if platFlag == True or centreFlag == True or diamFlag == True:  # update the status bar depending on choice
            #           if software == "watermaze":
            #               self.killBar()
            #               theStatus.set('Waiting for user input...')
            #               self.updateTasks()
            #               messagebox.showwarning('Watermaze Error',
            #                                      'You cannot use any Auto Calculations for Watermaze')
            #               return

            if platFlag == True and diamFlag == False:
                theStatus.set('Getting platform position...')
                loggingText = "Getting platform position"
                if centreFlag == True:
                    loggingText = "Getting platform and pool centre positions"
                    theStatus.set('Getting platform and pool centre positions...')
            elif platFlag == True and diamFlag == True:
                theStatus.set('Getting platform position and pool diameter...')
                loggingText = "Getting platform position and pool diameter"
                if centreFlag == True:
                    loggingText = "Getting platform and pool centre positions and pool diameter"
                    theStatus.set('Getting platform and pool centre positions and pool diameter...')
            elif centreFlag == True and diamFlag == True:
                loggingText = "Getting pool centre position and pool diameter"
                theStatus.set("Getting pool centre position and pool diameter")
            elif diamFlag == True and platFlag == False:
                theStatus.set('Getting pool diameter...')
                loggingText = "Getting pool diameter"
            else:
                loggingText = "Getting pool centre position"
                theStatus.set('Getting pool centre position...')
            logging.debug(loggingText)
            self.updateTasks()
            if software == "watermaze" and theFile != "":
                for aFile in self.find_files(fileDirectory, extensionType):
                    columns = defaultdict(list)  # each value in each column is appended to a list

                    oldItemX = 0.0
                    oldItemY = 0.0
                    number_of_columns = 0
                    number_of_rows = 0
                    try:

                        f = open(aFile)
                    except:
                        logging.info("Could not open " + aFile)
                        return
                    reader = csv.reader(f, delimiter=",")
                    for row in reader:
                        number_of_rows += 1
                        for (i, v) in enumerate(row):
                            columns[i].append(v)
                            number_of_columns = i

                    headerLines = 0  # gets number of header lines in the spreadsheet
                    numOfRows = number_of_rows
                    rows = []
                    k = 0
                    firstFlag = True
                    secondFlag = False
                    for i in range(0, math.floor(number_of_columns / 3)):
                        firstFlag = True
                        secondFlag = False
                        arrayX = []
                        arrayY = []
                        fullTrial = []
                        for a, b, c in zip(columns[i * 3], columns[1 + i * 3], columns[2 + i * 3]):
                            values = []
                            if firstFlag == True:
                                if a == "" or b == "" or c == "":
                                    continue
                                cTr = a
                                cTrID = b
                                cTrName = c  # round((math.floor(cTrName) + (((cTrName) % math.floor(cTrName)) * 60) / 100), 2)
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
                                fullTrial.append(item)

                        for item0 in fullTrial:  # for each row in our sheet
                            if item0.x == "-" or item0.x == "":  # throw out missing data
                                continue
                            if item0.y == "-" or item0.y == "":
                                continue
                            if item0.time < 1.0:
                                continue
                            if item0.time > (((number_of_rows - 39) * 0.04) - 1):
                                continue
                            if item0.time < 50.0:
                                lastX = item0.x
                                lastY = item0.y
                                skipFlag = False
                            else:
                                skipFlag = True

                            if item0.x > maxX:
                                maxX = item0.x
                            if item0.x < minX:
                                minX = item0.x
                            if item0.y > maxY:
                                maxY = item0.y
                            if item0.y < minY:
                                minY = item0.y

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

            else:
                for aFile in self.find_files(fileDirectory, extensionType):
                    i = 0.0
                    if software == "ethovision":
                        try:
                            wb = open_workbook(aFile)
                        except:
                            continue
                        for sheet in wb.sheets():  # for all sheets in the workbook
                            number_of_rows = sheet.nrows
                            headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet
                            numOfRows = sheet.nrows - headerLines
                            number_of_columns = sheet.ncols
                            fullTrial = []
                            rows = []
                            k = 0
                            for row in range(headerLines, number_of_rows):  # for each row

                                values = []

                                for col in range(1, 4):  # for columns 1 through 4, get all the values
                                    value = sheet.cell(row, col).value
                                    try:
                                        value = float(value)
                                    except ValueError:
                                        pass
                                    finally:
                                        values.append(value)

                                item = Trial(*values)
                                fullTrial.append(item)

                        for item0 in fullTrial:  # for each row in our sheet
                            if item0.x == "-" or item0.x == "":  # throw out missing data
                                continue
                            if item0.y == "-" or item0.y == "":
                                continue
                            if item0.time < 1.0:
                                continue
                            if item0.time > (((number_of_rows - 39) * 0.04) - 1):
                                continue
                            if item0.time < 50.0:
                                lastX = item0.x
                                lastY = item0.y
                                skipFlag = False
                            else:
                                skipFlag = True



                            if item0.x > maxX:
                                maxX = item0.x
                            if item0.x < minX:
                                minX = item0.x
                            if item0.y > maxY:
                                maxY = item0.y
                            if item0.y < minY:
                                minY = item0.y
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
                            if lastX > platMaxX:
                                platMaxX = lastX
                            if lastX < platMinX:
                                platMinX = lastX
                            if lastY > platMaxY:
                                platMaxY = lastY
                            if lastY < platMinY:
                                platMinY = lastY
                            platEstX += lastX
                            platEstY += lastY

                    elif software == "anymaze":
                        columns = defaultdict(list)  # each value in each column is appended to a list
                        try:
                            f = open(aFile)
                            logging.debug("Opened" +aFile)
                        except:
                            logging.info("Could not open " + aFile)
                            continue
                        reader = csv.reader(f, delimiter=",")
                        next(reader)
                        number_of_columns = 3
                        number_of_rows = 0
                        for row in reader:
                            number_of_rows += 1
                            for (i, v) in enumerate(row):
                                if i == 0 or i == 1 or i == 2:
                                    columns[i].append(v)

                        headerLines = 0  # gets number of header lines in the spreadsheet
                        numOfRows = number_of_rows

                        fullTrial = []
                        rows = []
                        k = 0
                        cTrName = ""


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
                            item = Trial(*values)
                            fullTrial.append(item)
                        cTrName = aFile

                        for item0 in fullTrial:  # for each row in our sheet
                            if item0.x == "-" or item0.x == "":  # throw out missing data
                                continue
                            if item0.y == "-" or item0.y == "":
                                continue
                            if item0.time < 1.0:
                                continue
                            if item0.time > (((number_of_rows - 39) * 0.04) - 1):
                                continue
                            if item0.time < 50.0:
                                lastX = item0.x
                                lastY = item0.y
                                skipFlag = False
                            else:
                                skipFlag = True

                            if item0.x > maxX:
                                maxX = item0.x
                            if item0.x < minX:
                                minX = item0.x
                            if item0.y > maxY:
                                maxY = item0.y
                            if item0.y < minY:
                                minY = item0.y

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
                            if lastX > maxX:
                                platMaxX = lastX
                            if lastX < minX:
                                platMinX = lastX
                            if lastY > maxY:
                                platMaxY = lastY
                            if lastY < minY:
                                platMinY = lastY
                            platEstX += lastX
                            platEstY += lastY

                    elif software == "watermaze":
                        columns = defaultdict(list)  # each value in each column is appended to a list

                        oldItemX = 0.0
                        oldItemY = 0.0
                        number_of_columns = 0
                        number_of_rows = 0
                        try:
                            f = open(aFile)
                        except:
                            logging.info("Could not open " + aFile)
                            continue
                        reader = csv.reader(f, delimiter=",")
                        for row in reader:
                            number_of_rows += 1
                            for (i, v) in enumerate(row):
                                columns[i].append(v)
                                number_of_columns = i

                        headerLines = 0  # gets number of header lines in the spreadsheet
                        numOfRows = number_of_rows
                        rows = []
                        k = 0
                        firstFlag = True
                        secondFlag = False
                        for i in range(0, math.floor(number_of_columns / 3)):
                            firstFlag = True
                            secondFlag = False
                            arrayX = []
                            arrayY = []
                            fullTrial = []
                            for a, b, c in zip(columns[i * 3], columns[1 + i * 3], columns[2 + i * 3]):
                                values = []
                                if firstFlag == True:
                                    if a == "" or b == "" or c == "":
                                        continue
                                    cTr = a
                                    cTrID = b
                                    cTrName = c  # round((math.floor(cTrName) + (((cTrName) % math.floor(cTrName)) * 60) / 100), 2)
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
                                    fullTrial.append(item)

                            for item0 in fullTrial:  # for each row in our sheet
                                if item0.x == "-" or item0.x == "":  # throw out missing data
                                    continue
                                if item0.y == "-" or item0.y == "":
                                    continue
                                if item0.time < 1.0:
                                    continue
                                if item0.time > (((number_of_rows - 39) * 0.04) - 1):
                                    continue
                                if item0.time < 50.0:
                                    lastX = item0.x
                                    lastY = item0.y
                                    skipFlag = False
                                else:
                                    skipFlag = True

                                if item0.x > maxX:
                                    maxX = item0.x
                                if item0.x < minX:
                                    minX = item0.x
                                if item0.y > maxY:
                                    maxY = item0.y
                                if item0.y < minY:
                                    minY = item0.y

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
                                if lastX > maxX:
                                    platMaxX = lastX
                                if lastX < minX:
                                    platMinX = lastX
                                if lastY > maxY:
                                    platMaxY = lastY
                                if lastY < minY:
                                    platMinY = lastY
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
                self.killBar()
                return

            if count < 1 and platFlag:
                logging.error("Unable to determine a platform posititon. Compatible trials: " + str(count))
                messagebox.showwarning('Platform Error',
                                       'We were unable to determine a platform position from the trials')
                theStatus.set('Waiting for user input...')
                self.updateTasks()
                self.killBar()
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
            if platFlag:  # automatic platform
                platEstX = platEstX / count
                platEstY = platEstY / count
                platformX = platEstX
                platformY = platEstY
                platEstDiam = ((platMaxX-platMinX) + (platMaxY-platMinY))/2
                logging.info("Automatic platform position calculated as: " + str(platEstX) + ", " + str(platEstY))
                logging.info("Automatic platform diameter calculated as: " + str((math.ceil(float(platEstDiam)))))
            if diamFlag:  # automatic diameter
                poolDiamEst = ((abs(absMaxX) + abs(absMinX)) + (abs(absMaxY) + abs(absMinY))) / 2
                logging.info("Automatic pool diameter calculated as: " + str(poolDiamEst))
                poolDiamVar = poolDiamEst
                poolRadius = float(poolDiamVar) / 2

            return (poolCentreX,poolCentreY,platformX,platformY,poolDiamVar,poolRadius, platEstDiam)

    def calculateValues(self, fullTrial, i, number_of_rows, headerLines, Matrix, platformX, platformY, poolCentreX, poolCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone, biggerWallZone, scalingFactor):
        global usePerseveranceV
        global oldPlatformPosVar
        global poolCentreVar

        if usePerseveranceV:
            oldPlatformPosVar = oldPlatformPosVar
            oldPlatfromX, oldPlatformY = oldPlatformPosVar
            oldPlatfromX = float(oldPlatfromX)
            oldPlatformY = float(oldPlatfromY)

        totalDistance = 0.0
        sampleRate = 0.0
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

        distanceToSwimPathCentroid = 0.0
        totalDistanceToSwimPathCentroid = 0.0
        averageDistanceToSwimPathCentroid = 0.0

        distanceToOldPlatform = 0.0
        totalDistanceToOldPlatform = 0.0
        averageDistanceToOldPlatform = 0.0

        jsls = 0.0

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


        for item in fullTrial:
            if item.x == "-" or item.x == "":  # throw out missing data
                continue
            if item.y == "-" or item.y == "":
                continue
            if x == 0:
                startTime = item.time
            if x == 1:
                sampleRate = item.time - startTime
            x += 1

        for item in fullTrial:  # for each row in our sheet
            if item.x == "-" or item.x == "":  # throw out missing data
                missingData += 1  # keep track of how much we throw out
                continue
            if item.y == "-" or item.y == "":
                missingData += 1
                continue
            if item.time < 1.0:
                if ((number_of_rows - headerLines) * (sampleRate)) > 5:
                    continue
            if i == 0:
                startX = item.x
                startY = item.y
            if item.time > (((number_of_rows - headerLines) * (sampleRate)) - 1):
                if ((number_of_rows-headerLines) * (sampleRate)) > 5:
                    continue
            # Swim Path centroid
            i += 1.0
            mainLatency += sampleRate
            xSummed += float(item.x)
            ySummed += float(item.y)
            aX = float(item.x)
            aY = float(item.y)
            arrayX.append(aX)
            arrayY.append(aY)
            # Average Distance
            currentDistanceFromPlatform = math.sqrt((platformX - aX) ** 2 + (platformY - aY) ** 2)

            #print(currentDistanceFromPlatform)

            if usePerseveranceV:
                distanceToOldPlatform = math.sqrt((oldPlatformX - aX) ** 2 + (oldPlatformY - aY) ** 2)
                totalDistanceToOldPlatform += distanceToOldPlatform

            # in zones
            distanceCenterToPlatform = math.sqrt((poolCentreX - platformX) ** 2 + (poolCentreY - platformY) ** 2)
            annulusZoneInner = distanceCenterToPlatform - (chainingRadius / 2)
            annulusZoneOuter = distanceCenterToPlatform + (chainingRadius / 2)
            distanceToCenterOfPool = math.sqrt((poolCentreX - aX) ** 2 + (poolCentreY - aY) ** 2)
            totalDistanceToCenterOfPool += distanceToCenterOfPool
            distanceFromStartToPlatform = math.sqrt((platformX - startX) ** 2 + (platformY - startY) ** 2)

            jsls += -(distanceFromStartToPlatform - distanceFromPlatformSummed) / 1000
            distance = math.sqrt(abs(oldX - aX) ** 2 + abs(oldY - aY) ** 2)
            if currentDistanceFromPlatform > 5:
                latencyCounter += 1.0
                distanceFromPlatformSummed += currentDistanceFromPlatform
                if distance < 5:
                    totalDistance += distance
            oldX = aX
            oldY = aY

            if distanceToCenterOfPool > biggerWallZone:  # calculate if we are in zones
                innerWallCounter += 1.0
            if distanceToCenterOfPool > smallerWallZone:
                outerWallCounter += 1.0
            if (distanceToCenterOfPool >= annulusZoneInner) and (distanceToCenterOfPool <= annulusZoneOuter):
                annulusCounter += 1

            a, b = 0, 0
            # grid creation
            # x values
            # <editor-fold desc="Grid">
            if item.x >= -100.0 and item.x <= -90:
                a = -9
            elif item.x > -90 and item.x <= -80:
                a = -8
            elif item.x > -80 and item.x <= -70:
                a = -7
            elif item.x > -70 and item.x <= -60:
                a = -6
            elif item.x > -60 and item.x <= -50:
                a = -5
            elif item.x > -50 and item.x <= -40:
                a = -4
            elif item.x > -40 and item.x <= -30:
                a = -3
            elif item.x > -30 and item.x <= -20:
                a = -2
            elif item.x > -20 and item.x <= -10:
                a = -1
            elif item.x > -10 and item.x <= 0:
                a = 0
            elif item.x > 0 and item.x <= 10:
                a = 1
            elif item.x > 10 and item.x <= 20:
                a = 2
            elif item.x > 20 and item.x <= 30:
                a = 3
            elif item.x > 30 and item.x <= 40:
                a = 4
            elif item.x > 40 and item.x <= 50:
                a = 5
            elif item.x > 50 and item.x <= 60:
                a = 6
            elif item.x > 60 and item.x <= 70:
                a = 7
            elif item.x > 70 and item.x <= 80:
                a = 8
            elif item.x > 80 and item.x <= 90:
                a = 9

            # y value categorization
            if item.y >= -100.0 and item.y <= -90:
                b = -9
            elif item.y > -90 and item.y <= -80:
                b = -8
            elif item.y > -80 and item.y <= -70:
                b = -7
            elif item.y > -70 and item.y <= -60:
                b = -6
            elif item.y > -60 and item.y <= -50:
                b = -5
            elif item.y > -50 and item.y <= -40:
                b = -4
            elif item.y > -40 and item.y <= -30:
                b = -3
            elif item.y > -30 and item.y <= -20:
                b = -2
            elif item.y > -20 and item.y <= -10:
                b = -1
            elif item.y > -10 and item.y <= 0:
                b = 0
            elif item.y > 0 and item.y <= 10:
                b = 1
            elif item.y > 10 and item.y <= 20:
                b = 2
            elif item.y > 20 and item.y <= 30:
                b = 3
            elif item.y > 30 and item.y <= 40:
                b = 4
            elif item.y > 40 and item.y <= 50:
                b = 5
            elif item.y > 50 and item.y <= 60:
                b = 6
            elif item.y > 60 and item.y <= 70:
                b = 7
            elif item.y > 70 and item.y <= 80:
                b = 8
            elif item.y > 80 and item.y <= 90:
                b = 9
            # </editor-fold>
            Matrix[a][b] = 1  # set matrix cells to 1 if we have visited them
            if (poolCentreX - aX) != 0:
                centerArcTangent = math.degrees(math.atan((poolCentreY - aY) / (poolCentreX - aX)))

            # print centerArcTangent
            if item.x >= 0 and item.y >= 0:
                quadrantOne = 1
            elif item.x < 0 and item.y >= 0:
                quadrantTwo = 1
            elif item.x >= 0 and item.y < 0:
                quadrantThree = 1
            elif item.x < 0 and item.y < 0:
                quadrantFour = 1

        latency = latencyCounter * sampleRate
        quadrantTotal = quadrantOne + quadrantTwo + quadrantThree + quadrantFour
        # <editor-fold desc="Swim Path centroid">
        if i <= 0:  # make sure we don't divide by 0
            i = 1

        xAv = xSummed / i  # get our average positions for the centroid
        yAv = ySummed / i
        swimPathCentroid = (xAv, yAv)

        if (platformX - startX) == 0:
            pass

        aArcTangent = math.degrees(math.atan((platformY - startY) / (platformX - startX)))
        upperCorridor = aArcTangent + corridorWidth
        lowerCorridor = aArcTangent - corridorWidth
        corridorWidth = 0.0
        totalHeadingError = 0.0

        for item2 in fullTrial:  # go back through all values and calculate distance to the centroid
            if item2.x == "-" or item2.x == "":
                continue
            if item2.y == "-" or item2.y == "":
                continue
            if item2.time < 1.0:
                continue
            if item2.time > (((number_of_rows - headerLines) * (sampleRate)) - 1):
                continue

            distanceToSwimPathCentroid = math.sqrt((xAv - item2.x) ** 2 + (yAv - item2.y) ** 2)
            totalDistanceToSwimPathCentroid += distanceToSwimPathCentroid
            distanceFromStartToCurrent = math.sqrt((item2.x - startX) **2 + (item2.y - startY)**2)

            if (item2.x - startX) != 0 and (item2.x - oldItemX) != 0:
                currentArcTangent = math.degrees(math.atan((item2.y - startY) / (item2.x - startX)))
                corridorWidth = abs(
                    aArcTangent - abs(math.degrees(math.atan((item2.y - oldItemY) / (item2.x - oldItemX)))))
                if float(lowerCorridor) <= float(currentArcTangent) <= float(upperCorridor) and distanceFromStartToCurrent < (distanceFromStartToPlatform+5):
                    corridorCounter += 1.0

            oldItemX = item2.x
            oldItemY = item2.y
            if item2.time < (((number_of_rows - 39) * sampleRate) - 1):
                totalHeadingError += corridorWidth
        # </editor-fold>
        # <editor-fold desc="Take Averages">
        corridorAverage = corridorCounter / i
        distanceAverage = distanceFromPlatformSummed / i  # calculate our average distances to landmarks
        averageDistanceToSwimPathCentroid = totalDistanceToSwimPathCentroid / i
        averageDistanceToOldPlatform = totalDistanceToOldPlatform / i
        averageDistanceToCentre = totalDistanceToCenterOfPool / i
        averageHeadingError = totalHeadingError / i

        missingDataFlag = 0
        if missingData > (i / 10):  # if we are missing more than 10% data, notify
            missingDataFlag = 1

        cellCounter = 0.0  # initialize our cell counter

        for k in range(0, 19):  # count how many cells we have visited
            for j in range(0, 19):
                if Matrix[k][j] == 1:
                    cellCounter += 1.0

        # print distanceTotal/(i/25), avHeadingError
        percentTraversed = (
                               cellCounter / (
                                   252.0 * scalingFactor)) * 100.0  # turn our count into a percentage over how many cells we can visit


        idealDistance = distanceFromStartToPlatform-5
        if latency != 0:
            try:
                velocity = (totalDistance/latency)
            except:
                pass
        else:
            latency = 0.04
        cumulativeDistanceError = 0.0

        while idealDistance > 5.0:
            cumulativeDistanceError += idealDistance
            idealDistance = (idealDistance - velocity*sampleRate)

        return jsls, corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToOldPlatform, averageDistanceToCentre, averageHeadingError, percentTraversed, missingDataFlag, quadrantTotal, totalDistance, mainLatency, innerWallCounter, outerWallCounter, annulusCounter, i, cumulativeDistanceError, distanceFromPlatformSummed, arrayX, arrayY

    def mainCalculate(self):
        global softwareStringVar
        logging.debug("Calculate Called")
        self.updateTasks()
        self.csvDestroy()

        platformPosVar = platformPosStringVar.get()
        poolDiamVar = poolDiamStringVar.get()
        poolCentreVar = poolCentreStringVar.get()
        oldPlatformPosVar = oldPlatformPosStringVar.get()
        corridorWidthVar = corridorWidthStringVar.get()
        chainingRadiusVar = chainingRadiusStringVar.get()
        thigmotaxisZoneSizeVar = thigmotaxisZoneSizeStringVar.get()  # get important values
        softwareScalingFactorVar = softwareScalingFactorStringVar.get()

        try:
            with open('mainobjs.pickle', 'wb') as f:
                pickle.dump([platformPosVar, poolDiamVar, poolCentreVar, oldPlatformPosVar, corridorWidthVar, chainingRadiusVar, thigmotaxisZoneSizeVar, softwareScalingFactorVar], f)
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
        perseveranceCount = 0.0
        spatialIndirectCount = 0.0
        notRecognizedCount = 0.0
        oldTotalCount = 0.0
        oldThigmotaxisCount = 0.0
        oldRandomCount = 0.0
        oldScanningCount = 0.0
        oldChainingCount = 0.0
        oldDirectSearchCount = 0.0
        oldFocalSearchCount = 0.0
        oldDirectSwimCount = 0.0
        oldPerseveranceCount = 0.0
        oldspatialIndirectCount = 0.0
        oldNotRecognizedCount = 0.0
        n = 0
        numOfRows = 0
        poolCentreX, poolCentreY = poolCentre
        flag = False
        dayFlag = False
        autoFlag = False
        skipFlag = False
        software = softwareStringVar.get()

        if fileDirectory == "":  # if we didnt select a directory
            if theFile == "":  # or a file
                messagebox.showwarning('No file or directory selected', 'Please select a directory or file under the File menu')
                self.killBar()
                logging.error("Unable to find trials")
                return  # stop

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

        poolCentreX, poolCentreY, platformX, platformY, poolDiamVar, poolRadius, platEstDiam = self.getAutoLocations(software, platformX, platformY, platformPosVar, poolCentreX, poolCentreY, poolCentreVar, poolDiamVar, fileDirectory, extensionType, theFile)
        scalingFactor = float(poolDiamVar) / 180.0  # set scaling factor for different pool sizes
        if scale:
            scalingFactor = scalingFactor * softwareScalingFactorVar
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
            self.killBar()
            return

        if software == "ethovision":
            writer.writerow(
                ("Day", "Trial", "Trial ID", "Trial Name", "Strategy Type", "Animal ID", "Missing Data",
                 "File", "CSE", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage"))  # write to the csv
            logging.debug("Using Ethovision")

        elif software == "anymaze":
            writer.writerow(
                ("File", "Strategy Type", "CSE", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage"))  # write to the csv
            logging.debug("Using Anymaze")
        elif software == "watermaze":
            logging.debug("Using Watermaze")
            writer.writerow(
                ("Trial", "Date", "Time", "Strategy Type", "File", "CSE", "velocity", "totalDistance", "distanceAverage", "averageHeadingError", "percentTraversed", "latency", "corridorAverage"))  # write to the csv


        if fileFlag == 1:  # called when 1 file selected
            logging.debug("Single file selected")
            aFile = theFile
            theStatus.set("Running "+aFile)
            if software == "ethovision":
                logging.info("Reading file ethovision")
                i = 0.0
                try:
                    wb = open_workbook(aFile)
                    logging.debug("Opened" + aFile)
                except:
                    # print("Corrupted excel file", aFile)
                    logging.error("Unable to open excel file" + aFile)
                    try:
                        show_error("Corrupted Excel File " + aFile)
                    except:
                        pass
                    return


                for sheet in wb.sheets():  # for all sheets in the workbook
                    number_of_rows = sheet.nrows
                    headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet
                    numOfRows = sheet.nrows - headerLines
                    number_of_columns = sheet.ncols
                    fullTrial = []
                    rows = []
                    k = 0
                    cCondition = ""
                    cTreatment = ""
                    cDay = ""
                    cTemp = ""
                    cGen = ""
                    cAnimalID = ""
                    cTrName = ""
                    cTrID = ""
                    cTr = ""

                    for k in range(0, 39):  # GET CONDITION TREATMENT AND DAY VALUES
                        if str(sheet.cell(k, 0).value) == "Condition" or str(sheet.cell(k, 0).value) == "Restraint":
                            cCondition = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Treatment":
                            cTreatment = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Day":
                            cDay = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Temperature":
                            cTemp = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Genotype":
                            cGen = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Animal ID":
                            cAnimalID = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Trial name":
                            cTrName = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Trial ID":
                            cTrID = str(sheet.cell(k, 1).value)
                        elif str(sheet.cell(k, 0).value) == "Trial":
                            cTr = str(sheet.cell(k, 1).value)


                    for row in range(headerLines, number_of_rows):  # for each row

                        values = []

                        for col in range(1, 4):  # for columns 1 through 4, get all the values
                            value = sheet.cell(row, col).value
                            try:
                                value = float(value)
                            except ValueError:
                                pass
                            finally:
                                values.append(value)

                        item = Trial(*values)
                        fullTrial.append(item)

            elif software == "anymaze":
                logging.info("Reading anymaze")
                i = 0.0
                columns = defaultdict(list)  # each value in each column is appended to a list
                try:
                    f = open(aFile)
                    logging.debug("Opened" + aFile)
                except:
                    logging.info("Could not open " + aFile)
                    return
                reader = csv.reader(f, delimiter=",")
                next(reader)
                number_of_columns = 3
                number_of_rows = 0
                for row in reader:
                    number_of_rows += 1
                    for (i, v) in enumerate(row):
                        columns[i].append(v)

                headerLines = 0  # gets number of header lines in the spreadsheet
                numOfRows = number_of_rows
                fullTrial = []
                rows = []
                k = 0
                cCondition = ""
                cTreatment = ""
                cDay = ""
                cTemp = ""
                cGen = ""
                cAnimalID = ""
                cTrName = ""
                cTrID = ""
                cTr = ""

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
                    item = Trial(*values)
                    fullTrial.append(item)
                cTrName = aFile
            elif software == "watermaze":
                logging.info("Reading watermaze")
                columns = defaultdict(list)  # each value in each column is appended to a list

                oldItemX = 0.0
                oldItemY = 0.0
                number_of_columns = 0
                number_of_rows = 0
                try:
                    f = open(aFile)
                except:
                    logging.info("Could not open " + aFile)
                    return
                reader = csv.reader(f, delimiter=",")
                for row in reader:
                    number_of_rows += 1
                    for (i, v) in enumerate(row):
                        columns[i].append(v)
                        number_of_columns = i

                headerLines = 0  # gets number of header lines in the spreadsheet
                numOfRows = number_of_rows


                rows = []
                k = 0

                for i in range(0, math.floor(number_of_columns / 3)):
                    i = 0.0
                    firstFlag = True
                    secondFlag = False
                    fullTrial = []
                    arrayX = []
                    arrayY = []
                    for a, b, c in zip(columns[i * 3], columns[1 + i * 3], columns[2 + i * 3]):
                        logging.debug("Running through columns: " + str(a) + str(b) + str(c))
                        values = []
                        if firstFlag == True:
                            if a == "" or b == "" or c == "":
                                continue
                            cTr = a
                            cTrID = b
                            cTrName = c  # round((math.floor(cTrName) + (((cTrName) % math.floor(cTrName)) * 60) / 100), 2)
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
                            fullTrial.append(item)

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

                    distanceToSwimPathCentroid = 0.0
                    totalDistanceToSwimPathCentroid = 0.0
                    averageDistanceToSwimPathCentroid = 0.0

                    distanceToOldPlatform = 0.0
                    totalDistanceToOldPlatform = 0.0
                    averageDistanceToOldPlatform = 0.0

                    cse = 0.0

                    startX = 0.0
                    startY = 0.0

                    areaCoverageGridSize = 18

                    corridorCounter = 0.0
                    quadrantOne = 0
                    quadrantTwo = 0
                    quadrantThree = 0
                    quadrantFour = 0
                    quadrantTotal = 0
                    # </editor-fold>
                    # initialize our cell matrix
                    Matrix = [[0 for x in range(0, areaCoverageGridSize)] for y in range(0, areaCoverageGridSize)]
                    # Analyze the data ----------------------------------------------------------------------------------------------
                    jsls, corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToOldPlatform, averageDistanceToCentre, averageHeadingError, percentTraversed, missingDataFlag, quadrantTotal, totalDistance, latency, innerWallCounter, outerWallCounter, annulusCounter, i, cumulativeDistanceError, distanceFromPlatformSummed, arrayX, arrayY = self.calculateValues(
                        fullTrial, i, number_of_rows, headerLines, Matrix, platformX, platformY, poolCentreX,
                        poolCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone,
                        biggerWallZone, scalingFactor)
                    velocity = totalDistance / latency
                    cse = float(distanceFromPlatformSummed - cumulativeDistanceError)*sampleRate
                    # OLD VALUE cse = float(distanceFromPlatformSummed - cumulativeDistanceError)


                    strategyType = ""
                    # DIRECT SWIM
                    if cse <= cseMaxVal and averageHeadingError <= headingMaxVal and isRuediger == False and useDirectSwimV:  # direct swim
                        directSwimCount += 1.0
                        strategyType = "Direct Swim"
                    elif isRuediger == True and corridorAverage >= 0.98 and useDirectSwimV:
                        directSwimCount += 1.0
                        strategyType = "Direct Swim"
                    # FOCAL SEARCH
                    elif averageDistanceToSwimPathCentroid < (
                                poolRadius * distanceToSwimMaxVal) and distanceAverage < (
                                distanceToPlatMaxVal * poolRadius) and useFocalSearchV:  # Focal Search
                        focalSearchCount += 1.0
                        strategyType = "Focal Search"
                    # DIRECTED SEARCH
                    elif corridorAverage >= corridorAverageMinVal and cse <= corridorCseMaxVal and useDirectedSearchV:  # directed search
                        directSearchCount += 1.0
                        strategyType = "Directed Search"
                    # spatial INDIRECT
                    elif cse < cseIndirectMaxVal and useIndirectV:  # Near miss
                        strategyType = "Spatial Indirect"
                        spatialIndirectCount += 1.0
                    # PERSEVERANCE
                    elif averageDistanceToSwimPathCentroid < (
                                distanceToSwimMaxVal * poolRadius) and averageDistanceToOldPlatform < (
                                distanceToPlatMaxVal * poolRadius) and usePerseveranceV:
                        perseveranceCount += 1.0
                        print("Perseverance")
                    # CHAINING
                    elif float(
                                    annulusCounter / i) > annulusCounterMaxVal and quadrantTotal >= quadrantTotalMaxVal and useChainingV:  # or 4 chaining
                        chainingCount += 1.0
                        strategyType = "Chaining"
                    # SCANNING
                    elif percentTraversedMinVal <= percentTraversed >= percentTraversedMaxVal and averageDistanceToCentre <= (
                                distanceToCentreMaxVal * poolRadius) and useScanningV:  # scanning
                        scanningCount += 1.0
                        strategyType = "Scanning"
                    # THIGMOTAXIS
                    elif innerWallCounter >= innerWallMaxVal * i and outerWallCounter >= i * outerWallMaxVal and useThigmoV:  # thigmotaxis
                        thigmotaxisCount += 1.0
                        strategyType = "Thigmotaxis"
                    # RANDOM SEARCH
                    elif percentTraversed >= percentTraversedRandomMaxVal and useRandomV:  # random search
                        randomCount += 1.0
                        strategyType = "Random Search"
                    # NOT RECOGNIZED
                    else:  # cannot categorize
                        strategyType = "Not Recognized"
                        notRecognizedCount += 1.0
                        if manualFlag and not useManualForAllFlag:
                            self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX),
                                            float(poolCentreY),
                                            float(platformX), float(platformY), float(scalingFactor),
                                            str(cAnimalID), float(platEstDiam))  # ask user for answer
                            root.wait_window(self.top2)  # we wait until the user responds
                            strategyType = searchStrategyV  # update the strategyType to that of the user
                            try:  # try and kill the popup window
                                self.top2.destroy()
                            except:
                                pass

                    totalTrialCount += 1.0

                    n += 1

                    if useManualForAllFlag:
                        self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY),
                                        float(platformX), float(platformY), float(scalingFactor),
                                        str(strategyType), float(platEstDiam))  # ask user for answer
                        root.wait_window(self.top2)  # we wait until the user responds
                        strategyType = searchStrategyV  # update the strategyType to that of the user

                    writer.writerow((cTr, cTrID, cTrName, strategyType, aFile), round(cse,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2))  # writing to csv file
                    f.flush()
                theStatus.set('Updating CSV...')
                self.updateTasks()
                try:
                    csvDisplay(root)
                except:
                    pass
                theStatus.set('')
                self.updateTasks()
                self.killBar()
                csvfilename = "results " + str(strftime("%Y_%m_%d %I_%M_%S_%p",
                                                        localtime())) + ".csv"  # update the csv file name for the next run
                outputFileStringVar.set(csvfilename)
                return

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

            distanceToSwimPathCentroid = 0.0
            totalDistanceToSwimPathCentroid = 0.0
            averageDistanceToSwimPathCentroid = 0.0

            distanceToOldPlatform = 0.0
            totalDistanceToOldPlatform = 0.0
            averageDistanceToOldPlatform = 0.0

            cse = 0.0

            startX = 0.0
            startY = 0.0
            oldX = 0.0
            oldY = 0.0
            areaCoverageGridSize = 18

            corridorCounter = 0.0
            quadrantOne = 0
            quadrantTwo = 0
            quadrantThree = 0
            quadrantFour = 0
            quadrantTotal = 0
            # </editor-fold>
            # initialize our cell matrix
            Matrix = [[0 for x in range(0, areaCoverageGridSize)] for y in range(0, areaCoverageGridSize)]
            # Analyze the data ----------------------------------------------------------------------------------------------

            jsls, corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToOldPlatform, averageDistanceToCentre, averageHeadingError, percentTraversed, missingDataFlag, quadrantTotal, totalDistance, latency, innerWallCounter, outerWallCounter, annulusCounter, i, cumulativeDistanceError, distanceFromPlatformSummed, arrayX, arrayY = self.calculateValues(
                fullTrial, i, number_of_rows, headerLines, Matrix, platformX, platformY, poolCentreX, poolCentreY,
                corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone, biggerWallZone, scalingFactor)
            velocity = totalDistance / latency
            cse = float(distanceFromPlatformSummed - cumulativeDistanceError)*sampleRate

            strategyType = ""
            # DIRECT SWIM
            if cse <= cseMaxVal and averageHeadingError <= headingMaxVal and isRuediger == False and useDirectSwimV:  # direct swim
                directSwimCount += 1.0
                strategyType = "Direct Swim"
            elif isRuediger == True and corridorAverage >= 0.98 and useDirectSwimV:
                directSwimCount += 1.0
                strategyType = "Direct Swim"
            # FOCAL SEARCH
            elif averageDistanceToSwimPathCentroid < (poolRadius * distanceToSwimMaxVal) and distanceAverage < (
                        distanceToPlatMaxVal * poolRadius) and useFocalSearchV:  # Focal Search
                focalSearchCount += 1.0
                strategyType = "Focal Search"
            # DIRECTED SEARCH
            elif corridorAverage >= corridorAverageMinVal and cse <= corridorCseMaxVal and useDirectedSearchV:  # directed search
                directSearchCount += 1.0
                strategyType = "Directed Search"
            # spatial INDIRECT
            elif cse < cseIndirectMaxVal and useIndirectV:  # Near miss
                strategyType = "Spatial Indirect"
                spatialIndirectCount += 1.0
            # PERSEVERANCE
            elif averageDistanceToSwimPathCentroid < (distanceToSwimMaxVal * poolRadius) and averageDistanceToOldPlatform < (distanceToPlatMaxVal * poolRadius) and usePerseveranceV:
                perseveranceCount += 1.0
                print("Perseverance")
            # CHAINING
            elif float(
                            annulusCounter / i) > annulusCounterMaxVal and quadrantTotal >= quadrantTotalMaxVal and useChainingV:  # or 4 chaining
                chainingCount += 1.0
                strategyType = "Chaining"
            # SCANNING
            elif percentTraversedMinVal <= percentTraversed >= percentTraversedMaxVal and averageDistanceToCentre <= (
                        distanceToCentreMaxVal * poolRadius) and useScanningV:  # scanning
                scanningCount += 1.0
                strategyType = "Scanning"
            # THIGMOTAXIS
            elif innerWallCounter >= innerWallMaxVal * i and outerWallCounter >= i * outerWallMaxVal and useThigmoV:  # thigmotaxis
                thigmotaxisCount += 1.0
                strategyType = "Thigmotaxis"
            # RANDOM SEARCH
            elif percentTraversed >= percentTraversedRandomMaxVal and useRandomV:  # random search
                randomCount += 1.0
                strategyType = "Random Search"
            # NOT RECOGNIZED
            else:  # cannot categorize
                strategyType = "Not Recognized"
                notRecognizedCount += 1.0
                if manualFlag and not useManualForAllFlag:
                    self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY),
                                    float(platformX), float(platformY), float(scalingFactor),
                                    str(cAnimalID), float(platEstDiam))  # ask user for answer
                    root.wait_window(self.top2)  # we wait until the user responds
                    strategyType = searchStrategyV  # update the strategyType to that of the user
                    try:  # try and kill the popup window
                        self.top2.destroy()
                    except:
                        pass

            totalTrialCount += 1.0

            n += 1
            if useManualForAllFlag:
                self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY),
                                float(platformX), float(platformY), float(scalingFactor),
                                str(strategyType), float(platEstDiam))  # ask user for answer
                root.wait_window(self.top2)  # we wait until the user responds
                strategyType = searchStrategyV  # update the strategyType to that of the user

            if software == "ethovision":
                writer.writerow((cDay, cTr, item.tid, item.name, strategyType, item.animalID, missingDataFlag,
                                 aFile, round(cse,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2)))  #   writing to csv file

            elif software == "anymaze":
                writer.writerow(
                    ("File", "Strategy Type"))  # write to the csv

                writer.writerow((aFile, strategyType, round(cse,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2)))  # , aFile  writing to csv file
            f.flush()

        else:  # called on directory of files
            logging.debug("Going through directory: " + str(fileDirectory))
            for aFile in self.find_files(fileDirectory, extensionType):  # for all the files we find
                theStatus.set("Running " + aFile)
                if software == "ethovision":
                    i = 0.0
                    try:
                        wb = open_workbook(aFile)
                        logging.debug("Opened" +aFile)
                    except:
                        logging.error("Could not open excel file: "+aFile)
                        continue

                    for sheet in wb.sheets():  # for all sheets in the workbook
                        arrayX = []
                        arrayY = []
                        number_of_rows = sheet.nrows
                        headerLines = int(sheet.cell(0, 1).value)  # gets number of header lines in the spreadsheet
                        numOfRows = sheet.nrows - headerLines
                        number_of_columns = sheet.ncols
                        fullTrial = []
                        rows = []
                        k = 0
                        cCondition = ""
                        cTreatment = ""
                        cDay = ""
                        cTemp = ""
                        cGen = ""
                        cAnimalID = ""
                        cTrName = ""
                        cTrID = ""
                        cTr = ""

                        for k in range(0, 39):  # GET CONDITION TREATMENT AND DAY VALUES
                            if str(sheet.cell(k, 0).value) == "Condition" or str(sheet.cell(k, 0).value) == "Restraint":
                                cCondition = str(sheet.cell(k, 1).value)
                            elif str(sheet.cell(k, 0).value) == "Treatment":
                                cTreatment = str(sheet.cell(k, 1).value)
                            elif str(sheet.cell(k, 0).value) == "Day":
                                cDay = str(sheet.cell(k, 1).value)
                                if dayFlag == False:
                                    oldDay = cDay
                                    dayFlag = True
                            elif str(sheet.cell(k, 0).value) == "Temperature":
                                cTemp = str(sheet.cell(k, 1).value)
                            elif str(sheet.cell(k, 0).value) == "Genotype":
                                cGen = str(sheet.cell(k, 1).value)
                            elif str(sheet.cell(k, 0).value) == "Animal ID":
                                cAnimalID = str(sheet.cell(k, 1).value)
                            elif str(sheet.cell(k, 0).value) == "Trial name":
                                cTrName = str(sheet.cell(k, 1).value)
                            elif str(sheet.cell(k, 0).value) == "Trial ID":
                                cTrID = str(sheet.cell(k, 1).value)
                            elif str(sheet.cell(k, 0).value) == "Trial":
                                cTr = str(sheet.cell(k, 1).value)


                        for row in range(headerLines, number_of_rows):  # for each row

                            values = []

                            for col in range(1, 4):  # for columns 1 through 4, get all the values
                                value = sheet.cell(row, col).value
                                try:
                                    value = float(value)
                                except ValueError:
                                    pass
                                finally:
                                    values.append(value)

                            item = Trial(*values)
                            fullTrial.append(item)



                        if cDay != str(oldDay) and flag:  # this is what we use to output totals for each day in the CSV file
                            if (totalTrialCount - oldTotalCount) != 0:
                                writer.writerow(())
                                writer.writerow(("Summary of day " + str(oldDay), ""))
                                writer.writerow(("Direct Swim", "Focal Search", "Directed Search", "Spatial Indirect", "Chaining",
                                                 "Scanning", "Thigmotaxis", "Random Search", "Not Recognized", "Total Categorized",
                                                 "Spatial Strategy Categorization", "Non-Spatial"))
                                writer.writerow((directSwimCount - oldDirectSwimCount, focalSearchCount - oldFocalSearchCount,
                                                 directSearchCount - oldDirectSearchCount,
                                                 spatialIndirectCount - oldspatialIndirectCount, chainingCount - oldChainingCount,
                                                 scanningCount - oldScanningCount, thigmotaxisCount - oldThigmotaxisCount,
                                                 randomCount - oldRandomCount, notRecognizedCount - oldNotRecognizedCount, round((((
                                                                                                                                       (
                                                                                                                                           totalTrialCount - oldTotalCount) - (
                                                                                                                                           notRecognizedCount - oldNotRecognizedCount)) / (
                                                                                                                                       totalTrialCount - oldTotalCount)) * 100),
                                                                                                                                 2),
                                                 directSwimCount - oldDirectSwimCount + directSearchCount - oldDirectSearchCount + focalSearchCount - oldFocalSearchCount + spatialIndirectCount - oldspatialIndirectCount,
                                                 chainingCount - oldChainingCount + scanningCount - oldScanningCount + thigmotaxisCount - oldThigmotaxisCount + randomCount - oldRandomCount))
                                writer.writerow(())
                                oldDay = cDay
                                oldTotalCount = totalTrialCount
                                oldThigmotaxisCount = thigmotaxisCount
                                oldRandomCount = randomCount
                                oldScanningCount = scanningCount
                                oldChainingCount = chainingCount
                                oldDirectSearchCount = directSearchCount
                                oldFocalSearchCount = focalSearchCount
                                oldDirectSwimCount = directSwimCount
                                oldPerseveranceCount = perseveranceCount
                                oldspatialIndirectCount = spatialIndirectCount
                                oldNotRecognizedCount = notRecognizedCount
                                writer.writerow(())
                                f.flush()

                elif software == "anymaze":
                    columns = defaultdict(list)  # each value in each column is appended to a list
                    arrayX = []
                    arrayY = []
                    oldItemX = 0.0
                    oldItemY = 0.0
                    try:
                        f = open(aFile)
                        logging.debug("Opened" +aFile)
                    except:
                        logging.info("Could not open " + aFile)
                        continue
                    reader = csv.reader(f, delimiter=",")
                    next(reader)
                    number_of_columns = 3
                    number_of_rows = 0
                    for row in reader:
                        number_of_rows += 1
                        for (i, v) in enumerate(row):
                            columns[i].append(v)

                    headerLines = 0  # gets number of header lines in the spreadsheet
                    numOfRows = number_of_rows

                    fullTrial = []
                    rows = []
                    k = 0
                    cCondition = ""
                    cTreatment = ""
                    cDay = ""
                    cTemp = ""
                    cGen = ""
                    cAnimalID = ""
                    cTrName = ""
                    cTrID = ""
                    cTr = ""
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
                        item = Trial(*values)
                        fullTrial.append(item)
                    cTrName = aFile


                elif software == "watermaze":
                    columns = defaultdict(list)  # each value in each column is appended to a list

                    oldItemX = 0.0
                    oldItemY = 0.0
                    number_of_columns = 0
                    number_of_rows = 0
                    try:
                        f = open(aFile)
                    except:
                        logging.info("Could not open " + aFile)
                        continue
                    reader = csv.reader(f, delimiter=",")
                    for row in reader:
                        number_of_rows += 1
                        for (i, v) in enumerate(row):
                            columns[i].append(v)
                            number_of_columns = i

                    headerLines = 0  # gets number of header lines in the spreadsheet
                    numOfRows = number_of_rows
                    rows = []
                    k = 0
                    firstFlag = True
                    secondFlag = False
                    for i in range(0, math.floor(number_of_columns / 3)):
                        firstFlag = True
                        secondFlag = False
                        arrayX = []
                        arrayY = []
                        fullTrial = []
                        for a, b, c in zip(columns[i * 3], columns[1 + i * 3], columns[2 + i * 3]):
                            values = []
                            if firstFlag == True:
                                if a == "" or b == "" or c == "":
                                    continue
                                cTr = a
                                cTrID = b
                                cTrName = c  # round((math.floor(cTrName) + (((cTrName) % math.floor(cTrName)) * 60) / 100), 2)
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
                                fullTrial.append(item)


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

                        distanceToSwimPathCentroid = 0.0
                        totalDistanceToSwimPathCentroid = 0.0
                        averageDistanceToSwimPathCentroid = 0.0

                        distanceToOldPlatform = 0.0
                        totalDistanceToOldPlatform = 0.0
                        averageDistanceToOldPlatform = 0.0

                        cse = 0.0

                        startX = 0.0
                        startY = 0.0

                        areaCoverageGridSize = 18

                        corridorCounter = 0.0
                        quadrantOne = 0
                        quadrantTwo = 0
                        quadrantThree = 0
                        quadrantFour = 0
                        quadrantTotal = 0
                        # </editor-fold>
                        # initialize our cell matrix
                        Matrix = [[0 for x in range(0, areaCoverageGridSize)] for y in
                                  range(0, areaCoverageGridSize)]
                        # Analyze the data ----------------------------------------------------------------------------------------------
                        jsls, corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToOldPlatform, averageDistanceToCentre, averageHeadingError, percentTraversed, missingDataFlag, quadrantTotal, totalDistance, latency, innerWallCounter, outerWallCounter, annulusCounter, i, cumulativeDistanceError, distanceFromPlatformSummed, arrayX, arrayY = self.calculateValues(
                            fullTrial, i, number_of_rows, headerLines, Matrix, platformX, platformY, poolCentreX,
                            poolCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone,
                            biggerWallZone, scalingFactor)
                        velocity = totalDistance / latency
                        cse = float(distanceFromPlatformSummed - cumulativeDistanceError)*sampleRate

                        strategyType = ""
                        # DIRECT SWIM
                        if cse <= cseMaxVal and averageHeadingError <= headingMaxVal and isRuediger == False and useDirectSwimV:  # direct swim
                            directSwimCount += 1.0
                            strategyType = "Direct Swim"
                        elif isRuediger == True and corridorAverage >= 0.98 and useDirectSwimV:
                            directSwimCount += 1.0
                            strategyType = "Direct Swim"
                        # FOCAL SEARCH
                        elif averageDistanceToSwimPathCentroid < (
                                    poolRadius * distanceToSwimMaxVal) and distanceAverage < (
                                    distanceToPlatMaxVal * poolRadius) and useFocalSearchV:  # Focal Search
                            focalSearchCount += 1.0
                            strategyType = "Focal Search"
                        # DIRECTED SEARCH
                        elif corridorAverage >= corridorAverageMinVal and cse <= corridorCseMaxVal and useDirectedSearchV:  # directed search
                            directSearchCount += 1.0
                            strategyType = "Directed Search"
                        # spatial INDIRECT
                        elif cse < cseIndirectMaxVal and useIndirectV:  # Near miss
                            strategyType = "Spatial Indirect"
                            spatialIndirectCount += 1.0
                        # PERSEVERANCE
                        elif averageDistanceToSwimPathCentroid < (
                                    distanceToSwimMaxVal * poolRadius) and averageDistanceToOldPlatform < (
                                    distanceToPlatMaxVal * poolRadius) and usePerseveranceV:
                            perseveranceCount += 1.0
                            print("Perseverance")
                        # CHAINING
                        elif float(
                                        annulusCounter / i) > annulusCounterMaxVal and quadrantTotal >= quadrantTotalMaxVal and useChainingV:  # or 4 chaining
                            chainingCount += 1.0
                            strategyType = "Chaining"
                        # SCANNING
                        elif percentTraversedMinVal <= percentTraversed >= percentTraversedMaxVal and averageDistanceToCentre <= (
                                    distanceToCentreMaxVal * poolRadius) and useScanningV:  # scanning
                            scanningCount += 1.0
                            strategyType = "Scanning"
                        # THIGMOTAXIS
                        elif innerWallCounter >= innerWallMaxVal * i and outerWallCounter >= i * outerWallMaxVal and useThigmoV:  # thigmotaxis
                            thigmotaxisCount += 1.0
                            strategyType = "Thigmotaxis"
                        # RANDOM SEARCH
                        elif percentTraversed >= percentTraversedRandomMaxVal and useRandomV:  # random search
                            randomCount += 1.0
                            strategyType = "Random Search"
                        # NOT RECOGNIZED
                        else:  # cannot categorize
                            strategyType = "Not Recognized"
                            notRecognizedCount += 1.0
                            if manualFlag and not useManualForAllFlag:
                                self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX),
                                                float(poolCentreY),
                                                float(platformX), float(platformY), float(scalingFactor),
                                                str(cAnimalID), float(platEstDiam))  # ask user for answer
                                root.wait_window(self.top2)  # we wait until the user responds
                                strategyType = searchStrategyV  # update the strategyType to that of the user
                                try:  # try and kill the popup window
                                    self.top2.destroy()
                                except:
                                    pass

                        totalTrialCount += 1.0

                        n += 1
                        if useManualForAllFlag:
                            self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY),
                                            float(platformX), float(platformY), float(scalingFactor),
                                            str(strategyType), float(platEstDiam))  # ask user for answer
                            root.wait_window(self.top2)  # we wait until the user responds
                            strategyType = searchStrategyV  # update the strategyType to that of the user

                        writer.writerow((cTr, cTrID, cTrName, strategyType, aFile, cse, velocity, totalDistance, distanceAverage, averageHeadingError, percentTraversed, latency), corridorAverage)  # writing to csv file
                        f.flush()
                    theStatus.set('Updating CSV...')
                    self.updateTasks()
                    try:
                        csvDisplay(root)
                    except:
                        pass
                    theStatus.set('')
                    self.updateTasks()
                    self.killBar()
                    csvfilename = "results " + str(strftime("%Y_%m_%d %I_%M_%S_%p",
                                                            localtime())) + ".csv"  # update the csv file name for the next run
                    outputFileStringVar.set(csvfilename)
                    return

                flag = True

                # </editor-fold>
                # initialize our cell matrix

                areaCoverageGridSize = 18

                Matrix = [[0 for x in range(0, areaCoverageGridSize+1)] for y in range(0, areaCoverageGridSize+1)]
                # Analyze the data ----------------------------------------------------------------------------------------------

                jsls, corridorAverage, distanceAverage, averageDistanceToSwimPathCentroid, averageDistanceToOldPlatform, averageDistanceToCentre, averageHeadingError, percentTraversed, missingDataFlag, quadrantTotal, totalDistance, latency, innerWallCounter, outerWallCounter, annulusCounter, i, cumulativeDistanceError, distanceFromPlatformSummed, arrayX, arrayY = self.calculateValues(fullTrial, i, number_of_rows, headerLines, Matrix, platformX, platformY, poolCentreX, poolCentreY, corridorWidth, thigmotaxisZoneSize, chainingRadius, smallerWallZone, biggerWallZone, scalingFactor)
                velocity = totalDistance/latency
                cse = float(distanceFromPlatformSummed - cumulativeDistanceError)


                strategyType = ""
                # DIRECT SWIM
                if cse <= cseMaxVal and averageHeadingError <= headingMaxVal and isRuediger == False and useDirectSwimV:  # direct swim
                    directSwimCount += 1.0
                    strategyType = "Direct Swim"
                elif isRuediger == True and corridorAverage >= 0.99 and useDirectSwimV:
                    directSwimCount += 1.0
                    strategyType = "Direct Swim"
                # FOCAL SEARCH
                elif averageDistanceToSwimPathCentroid < (poolRadius * distanceToSwimMaxVal) and distanceAverage < (
                            distanceToPlatMaxVal * poolRadius) and useFocalSearchV:  # Focal Search
                    focalSearchCount += 1.0
                    strategyType = "Focal Search"
                # DIRECTED SEARCH
                elif corridorAverage >= corridorAverageMinVal and cse <= corridorCseMaxVal and useDirectedSearchV:  # directed search
                    directSearchCount += 1.0
                    strategyType = "Directed Search"
                # spatial INDIRECT
                elif cse < cseIndirectMaxVal and useIndirectV:
                    strategyType = "Spatial Indirect"
                    spatialIndirectCount += 1.0
                #  PERSEVERANCE
                elif averageDistanceToSwimPathCentroid < (distanceToSwimMaxVal*poolRadius) and averageDistanceToOldPlatform < (distanceToPlatMaxVal*poolRadius) and usePerseveranceV:
                    perseveranceCount += 1.0
                    print("Perseverance")
                # CHAINING
                elif float(annulusCounter / i) > annulusCounterMaxVal and quadrantTotal >= quadrantTotalMaxVal and useChainingV:  # or 4 chaining
                    chainingCount += 1.0
                    strategyType = "Chaining"
                # SCANNING
                elif percentTraversedMinVal <= percentTraversed >= percentTraversedMaxVal and averageDistanceToCentre <= (distanceToCentreMaxVal * poolRadius) and useScanningV:  # scanning
                    scanningCount += 1.0
                    strategyType = "Scanning"
                # THIGMOTAXIS
                elif innerWallCounter >= innerWallMaxVal * i and outerWallCounter >= i * outerWallMaxVal and useThigmoV:  # thigmotaxis
                    thigmotaxisCount += 1.0
                    strategyType = "Thigmotaxis"
                # RANDOM SEARCH
                elif percentTraversed >= percentTraversedRandomMaxVal and useRandomV:  # random search
                    randomCount += 1.0
                    strategyType = "Random Search"
                # NOT RECOGNIZED
                else:  # cannot categorize
                    strategyType = "Not Recognized"
                    notRecognizedCount += 1.0
                    if manualFlag and not useManualForAllFlag:
                        self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY), float(platformX), float(platformY), float(scalingFactor), str(cAnimalID), float(platEstDiam))  # ask user for answer
                        root.wait_window(self.top2)  # we wait until the user responds
                        strategyType = searchStrategyV  # update the strategyType to that of the user
                        try:  # try and kill the popup window
                            self.top2.destroy()
                        except:
                            pass

                totalTrialCount += 1.0
                n += 1

                if useManualForAllFlag:
                    self.plotPoints(arrayX, arrayY, float(poolDiamVar), float(poolCentreX), float(poolCentreY),
                                    float(platformX), float(platformY), float(scalingFactor),
                                    str(strategyType), float(platEstDiam))  # ask user for answer
                    root.wait_window(self.top2)  # we wait until the user responds
                    strategyType = searchStrategyV  # update the strategyType to that of the user


                #round(math.log(cse,math.e),2) <= 5 for direct swim and round(math.log(cse,math.e),2) <= 9

                if software == "ethovision":
                    writer.writerow((cDay, cTr, cTrID, cTrName, strategyType, cAnimalID, missingDataFlag,
                                     aFile, round(cse,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2)))  # writing to csv file

                elif software == "anymaze":
                    writer.writerow((aFile, strategyType, round(cse,2), round(velocity,2), round(totalDistance,2), round(distanceAverage,2), round(averageHeadingError,2), round(percentTraversed,2), round(latency,2), round(corridorAverage,2)))  # , aFile  writing to csv file

                f.flush()
                logging.info("For " + str(aFile) + "... Day " + str(cDay) + " Trial " + str(cTr)+" ID " + str(cTrID) + " Trial Name " + str(cTrName) + " Strategy type " + str(strategyType) + " Animal ID " + str(cAnimalID) + " Missing Data 1/0? " + str(missingDataFlag))


            if (totalTrialCount - oldTotalCount) != 0 and software == "ethovision":

                writer.writerow(())
                writer.writerow(("Summary of day " + str(oldDay), ""))
                writer.writerow(("Direct Swim", "Focal Search", "Directed Search", "Spatial Indirect", "Chaining", "Scanning",
                                 "Thigmotaxis", "Random Search", "Not Recognized", "Total Categorized",
                                 "Spatial Strategy Categorization", "Non-Spatial"))
                writer.writerow((directSwimCount - oldDirectSwimCount, focalSearchCount - oldFocalSearchCount,
                                 directSearchCount - oldDirectSearchCount, spatialIndirectCount - oldspatialIndirectCount,
                                 chainingCount - oldChainingCount, scanningCount - oldScanningCount,
                                 thigmotaxisCount - oldThigmotaxisCount, randomCount - oldRandomCount,
                                 notRecognizedCount - oldNotRecognizedCount, round(((((totalTrialCount - oldTotalCount) - (
                    notRecognizedCount - oldNotRecognizedCount)) / (totalTrialCount - oldTotalCount)) * 100), 2),
                                 directSwimCount - oldDirectSwimCount + directSearchCount - oldDirectSearchCount + focalSearchCount - oldFocalSearchCount + spatialIndirectCount - oldspatialIndirectCount,
                                 chainingCount - oldChainingCount + scanningCount - oldScanningCount + thigmotaxisCount - oldThigmotaxisCount + randomCount - oldRandomCount))
                writer.writerow(())
                writer.writerow(("Direct Swim", "Focal Search", "Directed Search", "Spatial Indirect", "Chaining", "Scanning",
                                 "Thigmotaxis", "Random Search", "Not Recognized", "Total Categorized",
                                 "Spatial Strategy Categorization", "Non-Spatial"))
                writer.writerow((directSwimCount, focalSearchCount, directSearchCount, spatialIndirectCount, chainingCount,
                                 scanningCount, thigmotaxisCount, randomCount, notRecognizedCount,
                                 round((((totalTrialCount - notRecognizedCount) / totalTrialCount) * 100), 2),
                                 directSwimCount + directSearchCount + focalSearchCount + spatialIndirectCount,
                                 chainingCount + scanningCount + thigmotaxisCount + randomCount))
                f.flush()

                logging.info("Final results: Direct Swim: "+ str(directSwimCount) + "  Focal Search: " + str(focalSearchCount)+ "  Directed Search: "+
                             str(directSearchCount) + "  spatial Indirect: "+ str(spatialIndirectCount) + "  Chaining: " + str(chainingCount) +
                             "  Scanning: " + str(scanningCount))
        theStatus.set('Updating CSV...')
        self.updateTasks()
        try:
            csvDisplay(root)
        except:
            logging.error("Failed to display CSV")
            pass
        theStatus.set('Waiting for user input...')
        self.updateTasks()
        self.killBar()
        csvfilename = "results " + str(strftime("%Y_%m_%d %I_%M_%S_%p", localtime())) + ".csv"  # update the csv file name for the next run
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
