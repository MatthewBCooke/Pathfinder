import math
import os
import sys
from appTrial import Trial, Experiment, Parameters
from time import localtime, strftime

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


def guiHeatmap(self, root, experiment, gridSizeStringVar, maxValStringVar):

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

        Button(self.top3, text="Generate", command=lambda: heatmap(self, experiment), fg="black", bg="white").pack()


def heatmap(self, experiment):
    logging.debug("Heatmap Called")
    theStatus.set("Generating Heatmap...")
    self.updateTasks()

    n = 0
    x = []
    y = []
    i = 0
    xMin = 0.0
    yMin = 0.0
    xMax = 0.0
    yMax = 0.0

    for aTrial in experiment:  # for all the files we find
        theStatus.set("Running " + aFile)
        i = 0.0
        for row in aTrial:
            # Create data
            if row.x == "-" or row.y == "-":
                continue
            x.append(float(item.x))
            y.append(float(item.y))

            if row.x < xMin:
                xMin = row.x
            if row.y < yMin:
                yMin = row.y
            if row.x > xMax:
                xMax = row.x
            if row.y > yMax:
                yMax = row.y



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
