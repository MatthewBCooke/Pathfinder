from tkinter import Tk, Canvas, Frame, BOTH


class Diagram(object):  # an object for our row values
    def __init__(self):
        self.goalPos = (0,0)
        self.goalDia = 10
        self.mazeDia = 300
        self.mazeCen = (0,0)
        self.corridorAngle = 40
        self.chainingWidth = 25
        self.thigmoSize = 15
        self.scale = 1.0

    # def drawDiagram(self):
