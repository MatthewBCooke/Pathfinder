# Module: appTrial.py
# Holds data structures


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
