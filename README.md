# Pathfinder

Morris Water Maze search strategy and entropy analysis.

Created by **Matthew Cooke** at **The University of British Columbia**, **Jason Snyder Lab**

Visit us at [https://matthewbcooke.github.io/Pathfinder/](https://matthewbcooke.github.io/Pathfinder/)

## Synopsis

The Pathfinder package is a search strategy analysis tool for the Morris Water Maze, and can be expanded for other spatial navigation tasks. The program analyses X-Y coordinate data exported from commercially available tracking software. Pathfinder currently supports outputs from: Ethovision, Anymazy, WaterMaze, and ezTrack. We then calculate the best-fit search strategy for the trial. Trials are fit into one of: Direct Swim, Directed Search, Focal Search, Spatial indirect, Chaining, Scanning, Thigmotaxis, and Random Search.

## Usage Example

1. The program can be opened by calling `pathfinder` if installed through PyPi or by navigating to your install location and calling `python pathfinder.py` in a terminal window. See [**Installation**](https://github.com/MatthewBCooke/Pathfinder/wiki/Installation) for install instructions.

2. This will open up the main GUI window.

    ![Window Preview](http://snyderlab.com/pathfinder/main.jpg)

3. You can select an inividual file or a directory containing export files from the **File** drop-down menu.

4. From here you can choose to either [(**A**)](https://github.com/MatthewBCooke/Pathfinder/blob/master/README.md#a-generating-heatmaps) generate heatmaps for the chosen trials, or to [(**B**)](https://github.com/MatthewBCooke/Pathfinder/blob/master/README.md#b-search-strategy-analysis) calculate search strategies.

### (A) Generating Heatmaps

The Pathfinder package allows for the efficient generation of heatmaps. To do so, follow these steps.

1. Once a directory or file has been imported, select **File** -> **Generate Heatmaps**

2. A parameters panel will appear:

    ![Heatmap parameters](http://snyderlab.com/pathfinder/heatmapparams.jpg)

3. The parameters panel lets you tailor the output to your needs:

    1. Grid size. This roughly translates into how many bins to put the data in. For more information on grid size see matplotlib documentation [(here)](http://matplotlib.org/devdocs/api/_as_gen/matplotlib.axes.Axes.hexbin.html).

    2. Maximum Value. This will allow you to change at which value the points in the heatmap will become their most saturated (dark red). Setting 'Auto' will dynamically assign the maximum value to be equal to the value of the maximum grid.


    3. Day: A day or range of days to use for calculating the heatmaps. (E.g. 1 or 3-6 or All)

    4. Trial: A trial or range of trials on the above selected days. (E.g. All or 1-4 or 2)

4. You can then click generate, and our software will plot a heatmap of your trial data.

    ![heatmap display](http://snyderlab.com/pathfinder/heatmap.jpg)

### (B) Search Strategy Analysis

1. For search strategy analysis we have multiple options. To set your own strategy parameters, click settings.

2. The settings button will spawn a parameters panel:

    ![settings parameters](http://snyderlab.com/pathfinder/settings.jpg)


3. In the settings parameters pane, you can select and deselect any of the search strategies. Deselecting Strategies will remove them from consideration. You can also define the cutoff values for each strategy. For definitions of these values see Cooke et al., 2019, in preparation.

4. Once you have chosen your parameters, be sure to select your tracking software. Ethovision, Anymaze, WaterMaze, and ezTrack are currently supported. 

5. You may then alter the main values to suit your data. Platform position, pool centre, and pool diameter can be automatically calculated for groups of trials with a consistent single platform location. For all other data, you must manually define these values (Example: `Platform Position (x,y) | 6.53,-17.3`). For more in-depth explanations of these values, see Cooke et al., 2019, in preparation.

6. There are 4 checkboxes above the **Calculate** button. The first, *Scale Values* is used to automatically scale the default values in an attempt to better match your data. This uses the Pixels/cm and the pool diameter to determine a constant C with which to multiply some parameters. (*Note: If you are using custom values, it is best to disable scaling*) The two following checkboxes enable manual categorization. Manual categorization can be used for trials in which our algorithm was unable to make a determination (**Manual categorization for uncategorized trials**) or for all trials (**Manual categorization for all trials**). The last checkbox enables the calculation of entropy for the trial. This requires MATLAB.

    ![manual categorization](http://snyderlab.com/pathfinder/manual.jpg)


7. Once you are satisfied with your parameters, click calculate. This will begin the process of determining search strategies for the trials. Once calculation is complete, you will be shown a display of the results.

    ![display](http://snyderlab.com/pathfinder/output.jpg)


8. Your results will be saved as a `.csv` file with whatever name was chosen in the *Output File* field. You will also receive a log file of the excecution, and any generated paths saved in your present working directory. The CSV file will automatically open with whatever default CSV software you use.


## Motivation

This program was developed in order to simplify as well as remove inconsistencies in Morris Water Maze search strategy analysis. 

## Installation

Installing the program is easy for both macOS and Windows users.

Pathfinder requires you to have Python 3.6 or later. We highly recommend installing Conda for python via the Anaconda 🐍 package https://www.anaconda.com/distribution/. Once installed, the installation of Pathfinder is easy.

For the most recent stable version, cloning the GitHub repository or installing via PyPi is possible. For the most recent beta version of the software, the develop branch of the GitHub repository will host the version currently being worked on.

Installation Instructions:

Windows:

Installing from the Python Package Index:
Launch a CMD window by launching `run` from the start menu, and typing `CMD` in Run.

Once the CMD shell has opened, type `pip install jsl-pathfinder`

Press enter

Installing from GitHub

Download and install Git here: https://git-scm.com

Open Git Bash.

Change the current working directory to the location where you want the cloned directory to be made.

Type `git clone https://github.com/MatthewBCooke/Pathfinder`

Press enter

***

Mac:

Installing from the Python Package Index:

Open a terminal window (located in your utilities folder under the Applications directory.

Type `pip install jsl-pathfinder`

Press return

Installing from GitHub

Open a terminal window Navigate to the folder you wish to install Pathfinder into

Type `git clone https://github.com/MatthewBCooke/Pathfinder/`

press return


## License

GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
