# Pathfinder

Jason Snyder Lab Watermaze Search strategy and entropy analysis.
Created by **Matthew Cooke** at **The University of British Columbia**, **Jason Snyder Lab**

## Synopsis

The Pathfinder package is a animal search strategy analysis tool for the Morris Water Maze. The program analyses X-Y coordinate data exported from tracking software (currently supports Ethovision, Anymazy, WaterMaze, and ezTrack). We then calculate the best-fit search strategy for the trial. We analyse the data and fit it into one of 9 search strategies: Direct Swim, Directed Search, Focal Search, Spatial indirect, Chaining, Scanning, Thigmotaxis, and Random Search.

## Usage Example

1. The program can be opened by calling `pathfinder`. See [**Installation**](https://github.com/MatthewBCooke/Pathfinder/blob/master/README.md#installation) for install instructions.

2. This will open up the GUI window.

![Window Preview](https://i.gyazo.com/869e96f19fee12d94d442535607f884e.png)

3. You can then select an inividual file or a directory containing files from the **File** dropdown menu. These files must be Excel files if you are using Ethovision tracking software, and CSV files if you are using Anymaze or Watermaze software. *Note: For directory selection, you must enter **into** the directory and not just highlight it for it to be selected*

4. From here you can choose to either [(**A**)](https://github.com/MatthewBCooke/Pathfinder/blob/master/README.md#a-generating-heatmaps) generate heatmaps for the chosen trials, or to [(**B**)](https://github.com/MatthewBCooke/Pathfinder/blob/master/README.md#b-search-strategy-analysis) calculate search strategies.

### (A) Generating Heatmaps

The Pathfinder package allows for the efficient generation of heatmaps. To do so, follow these steps.

1. Click on **File** -> **Generate Heatmaps**

2. A parameters panel will appear:

![Heatmap parameters](https://i.gyazo.com/e4dfcb87078433f276d785431af3bf96.png)

3. The parameters panel lets you tailor the output to your needs:

    1. Grid size. This roughly translates into how many bins to put the data in. For more information on grid size see matplotlib documentation: http://matplotlib.org/devdocs/api/_as_gen/matplotlib.axes.Axes.hexbin.html

    2. Maximum Value. This will allow you to change at which value the points in the heatmap will become their most saturated (dark red). Setting 'Auto' will dynamically assign the maximum value to be equal to the value of the maximum grid.

    3. Dynamic Parameters. Our dynamic parameter display will appear if you are using Ethovision. This display allows you to tick the boxes of which labels you would like to consider. Example: `(X) Genotype | WT` will only calculate heatmaps from trials with WT genotype animals.

4. You can then click generate, and our software will plot a heatmap of your trial data.

![heatmap display](https://i.gyazo.com/38211dd9a8add907ffa6b955adf3058e.png)

### (B) Search Strategy Analysis

1. For search strategy analysis we have multiple options. To use predefined values from either Snyder et el., 2017, Ruediger et al., 2012, or Gathe et al., 2009 click their respecive buttons. To set your own strategy parameters, click custom.

2. (Custom) The custom button will spawn a parameters panel

![custom parameters](https://i.gyazo.com/f7a34522b4d4bcab1bc1746c0218767b.png)

3. In the custom parameters pane, you can select and deselect any of the search strategies. Deselecting Strategies will remove them from consideration. You can also define the cutoff values for each strategy. For definitions of these values see Snyder et al., 2017.

4. Once you have chosen your parameters, be sure to select your tracking software. Ethovision, Anymaze, and Watermaze are currently supported. (*Note: Anymaze and Watermaze are currently in beta -- not all features are available*)

5. You may then alter the main values to suit your data. Platform position, pool centre, and pool diameter can be automatically calculated for groups of non-probe trials tracked in Ethovision. For all other data you must manually define these values (Example: `Platform Position (x,y) | 6.53,-17.3`). Old platform position is only used when Perseverance is chosen in the Custom parameters pane. For more in-depth explanations of these values, see Snyder et al., 2017.

6. There are 3 checkboxes above the **Calculate** button. The first, *Scale Values* is used to automatically scale the default values in an attempt to better match your data. This uses the Pixels/cm and the pool diameter to determine a constant C with which to multiply some parameters. (*Note: If you are using custom values, it is best to disable scaling*) The two other checkboxes enable manual categorization. Manual categorization can be used for trials in which our algorithm was unable to make a determination (**Manual categorization for uncategorized trials**) or for all trials (**Manual categorization for all trials**). 

![manual categorization](https://i.gyazo.com/a394b4f18e693cb26f996cca27feac16.png)

7. Once you are satisfied with your parameters, click calculate. This will begin the process of determining search strategies for the trials. Once calculation is complete you will be shown a display of the results.

![csv display](https://i.gyazo.com/d3c918f27785d3a8b910fd870fd18387.png)

8. Your results will be saved as a `.csv` file with whatever name was chosen in the *Output File* field. You will also receive a log file of the excecution, and any generated paths saved in your present working directory.


## Motivation

This program was developed in order to simplify as well as remove inconsistencies in Morris Water Maze search strategy analysis. 

## Installation

This package is hosted on PyPi, and is therefore easy to install with PIP.
To install simply call: `pip install pathfinder`

## References

>Ruediger S, Spirig D, Donato F, Caroni P. Goal-oriented searching mediated by ventral hippocampus early in trial-and-error learning. Nat Neurosci. 2012 Nov;15(11):1563-71. doi: 10.1038/nn.3224. Epub 2012 Sep 23. PubMed PMID: 23001061.

>Adult-Generated Hippocampal Neurons Allow the Flexible Use of Spatially Precise Learning Strategies 
Garthe A, Behr J, Kempermann G (2009) Adult-Generated Hippocampal Neurons Allow the Flexible Use of Spatially Precise Learning Strategies. PLOS ONE 4(5): e5464. https://doi.org/10.1371/journal.pone.0005464

>Garthe A, Huang Z, Kaczmarek L, Filipkowski RK, Kempermann G. Not all water mazes are created equal: cyclin D2 knockout mice with constitutively suppressed adult hippocampal neurogenesis do show specific spatial learning deficits. Genes, Brain, and Behavior. 2014;13(4):357-364. doi:10.1111/gbb.12130.

>Graziano A, Petrosini L, Bartoletti A. Automatic recognition of explorative strategies in the Morris water maze. J Neurosci Methods. 2003 Nov 30;130(1):33-44. PubMed PMID: 14583402.

## License

GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.
