from tkinter import Tk, Canvas, Frame, BOTH

class Diagram(object):  # an object for our row values
    def __init__(self):
        self.goalPos = (374,244)
        self.goalDia = 5
        self.mazeDia = 20
        self.mazeCen = (0,0)
        self.corridorAngle = 40
        self.chainingWidth = 35
        self.thigmoSize = 15
        self.scale = 1.0

    # def drawDiagram(self):
