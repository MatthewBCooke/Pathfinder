"""
Data models for Pathfinder analysis engine.

These are the core data structures that represent trials, experiments, and parameters.
All classes are pure data containers (no GUI dependencies).
"""

from __future__ import annotations
from typing import List, Optional
from datetime import datetime


class Datapoint:
    """A single position measurement from a trial."""

    def __init__(self, time: float, x: float, y: float) -> None:
        """
        Initialize a datapoint.

        Args:
            time: Time in seconds since trial start
            x: X coordinate of animal position
            y: Y coordinate of animal position
        """
        self.time: float = time
        self.x: float = x
        self.y: float = y

    def __str__(self) -> str:
        return (
            f"Datapoint(time={self.time:.2f}s, x={self.x:.1f}, y={self.y:.1f})"
        )

    def getx(self) -> float:
        """Get X coordinate."""
        return self.x

    def gety(self) -> float:
        """Get Y coordinate."""
        return self.y

    def gettime(self) -> float:
        """Get time value."""
        return self.time


class Trial:
    """Represents a single trial of behavioral data."""

    def __init__(self) -> None:
        """Initialize an empty trial."""
        self.datapointList: List[Datapoint] = []
        self.name: Optional[str] = None
        self.animal: Optional[str] = None
        self.date: Optional[datetime] = None
        self.day: Optional[int] = None
        self.trial: Optional[int] = None
        self.corruptedData: bool = False

    def setname(self, name: str) -> None:
        """Set trial name."""
        self.name = name

    def setanimal(self, animal: str) -> None:
        """Set animal identifier."""
        self.animal = animal

    def setdate(self, date: datetime) -> None:
        """Set trial date."""
        self.date = date

    def settrial(self, trial: int) -> None:
        """Set trial number."""
        self.trial = trial

    def setday(self, day: int) -> None:
        """Set trial day."""
        self.day = day

    def markDataAsCorrupted(self) -> None:
        """Mark this trial's data as corrupted/invalid."""
        self.corruptedData = True

    def __str__(self) -> str:
        return self.animal if self.animal is not None else self.name or "Unknown"

    def append(self, datapoint: Datapoint) -> None:
        """Add a datapoint to this trial."""
        self.datapointList.append(datapoint)

    def __iter__(self):
        """Iterate over datapoints in this trial."""
        return iter(self.datapointList)

    def __len__(self) -> int:
        """Get number of datapoints."""
        return len(self.datapointList)


class Experiment:
    """Represents a collection of trials from an experiment."""

    def __init__(self, name: str) -> None:
        """
        Initialize an experiment.

        Args:
            name: Name of the experiment
        """
        self.name: str = name
        self.trialList: List[Trial] = []
        self.hasAnimalNames: bool = False
        self.hasDateInfo: bool = False
        self.hasTrialNames: bool = False

    def setTrialList(self, trialList: List[Trial]) -> None:
        """Set the trial list."""
        self.trialList = trialList

    def setHasAnimalNames(self, hasAnimalNames: bool) -> None:
        """Mark whether this experiment has animal names."""
        self.hasAnimalNames = hasAnimalNames

    def setHasDateInfo(self, hasDateInfo: bool) -> None:
        """Mark whether this experiment has date information."""
        self.hasDateInfo = hasDateInfo

    def setHasTrialNames(self, hasTrialNames: bool) -> None:
        """Mark whether this experiment has trial names."""
        self.hasTrialNames = hasTrialNames

    def append(self, trial: Trial) -> None:
        """Add a trial to this experiment."""
        self.trialList.append(trial)

    def __str__(self) -> str:
        return self.name

    def __len__(self) -> int:
        """Get number of trials."""
        return len(self.trialList)

    def __iter__(self):
        """Iterate over trials in this experiment."""
        return iter(self.trialList)


class Parameters:
    """Configuration parameters for analysis thresholds and decision criteria."""

    def __init__(
        self,
        name: str,
        ipeMaxVal: float,
        headingMaxVal: float,
        distanceToSwimMaxVal: float,
        distanceToPlatMaxVal: float,
        distanceToSwimMaxVal2: float,
        distanceToPlatMaxVal2: float,
        corridorAverageMinVal: float,
        directedSearchMaxDistance: float,
        focalMinDistance: float,
        focalMaxDistance: float,
        semiFocalMinDistance: float,
        semiFocalMaxDistance: float,
        corridoripeMaxVal: float,
        annulusCounterMaxVal: float,
        quadrantTotalMaxVal: float,
        chainingMaxCoverage: float,
        percentTraversedMaxVal: float,
        percentTraversedMinVal: float,
        distanceToCentreMaxVal: float,
        thigmoMinDistance: float,
        fullThigmoMinVal: float,
        smallThigmoMinVal: float,
        ipeIndirectMaxVal: float,
        percentTraversedRandomMaxVal: float,
        headingIndirectMaxVal: float,
        useDirect: bool,
        useFocal: bool,
        useDirected: bool,
        useIndirect: bool,
        useSemiFocal: bool,
        useChaining: bool,
        useScanning: bool,
        useRandom: bool,
        useThigmogaxis: bool,
    ) -> None:
        """
        Initialize analysis parameters.

        All parameters are analysis thresholds that determine strategy classification.
        """
        self.name: str = name
        self.ipeMaxVal: float = ipeMaxVal
        self.headingMaxVal: float = headingMaxVal
        self.distanceToSwimMaxVal: float = distanceToSwimMaxVal
        self.distanceToPlatMaxVal: float = distanceToPlatMaxVal
        self.distanceToSwimMaxVal2: float = distanceToSwimMaxVal2
        self.distanceToPlatMaxVal2: float = distanceToPlatMaxVal2
        self.corridorAverageMinVal: float = corridorAverageMinVal
        self.directedSearchMaxDistance: float = directedSearchMaxDistance
        self.focalMinDistance: float = focalMinDistance
        self.focalMaxDistance: float = focalMaxDistance
        self.semiFocalMinDistance: float = semiFocalMinDistance
        self.semiFocalMaxDistance: float = semiFocalMaxDistance
        self.corridoripeMaxVal: float = corridoripeMaxVal
        self.annulusCounterMaxVal: float = annulusCounterMaxVal
        self.quadrantTotalMaxVal: float = quadrantTotalMaxVal
        self.chainingMaxCoverage: float = chainingMaxCoverage
        self.percentTraversedMaxVal: float = percentTraversedMaxVal
        self.percentTraversedMinVal: float = percentTraversedMinVal
        self.distanceToCentreMaxVal: float = distanceToCentreMaxVal
        self.thigmoMinDistance: float = thigmoMinDistance
        self.fullThigmoMinVal: float = fullThigmoMinVal
        self.smallThigmoMinVal: float = smallThigmoMinVal
        self.ipeIndirectMaxVal: float = ipeIndirectMaxVal
        self.percentTraversedRandomMaxVal: float = percentTraversedRandomMaxVal
        self.headingIndirectMaxVal: float = headingIndirectMaxVal
        self.useDirect: bool = useDirect
        self.useFocal: bool = useFocal
        self.useDirected: bool = useDirected
        self.useIndirect: bool = useIndirect
        self.useSemiFocal: bool = useSemiFocal
        self.useChaining: bool = useChaining
        self.useScanning: bool = useScanning
        self.useRandom: bool = useRandom
        self.useThigmotaxis: bool = useThigmogaxis

    def __str__(self) -> str:
        return self.name
