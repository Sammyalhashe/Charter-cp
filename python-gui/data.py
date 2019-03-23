###############################################################################
from random import random
from rx.subjects import Subject
import time
from math import sin

# from PyQt5.QtWidgets import QMessageBox

###############################################################################


class dataRPC():
    """dataRPC"""

    def __init__(self):
        self.stream = None
        self.plottingOn = False

    def getStream(self):
        if not self.stream:
            print("Activate the Data Stream first")
            # msg = QMessageBox()
            # msg.setIcon(QMessageBox.Information)
            # msg.setInformativeText("Activate the Data Stream first")
            # msg.setStandardButtons(QMessageBox.Ok)
            # msg.buttonClicked.connect(lambda _: print("Ok"))
            # msg.exec_()
            return None
        return self.stream

    def activateStream(self):
        """activateStream
        Creates an RxPy Subject if one hasn't already been created.
        This subject serves as the data bridge between frontend and backend
        """
        if not self.stream:
            self.stream = Subject()

    def getData_s(self, channels="1 2"):
        """getData_s
        This function is a test function that mimics observing the data
        stream from the larry box.

        :param channels: string => How many channel you want to observe
        """
        if not self.stream:
            self.activateStream()
        channels = channels.split(' ')
        self.stream.on_next([[sin(random())] * 10 for i in channels])

    def getData_test(self, on=False):
        """getData_test
        Function that starts the test data observation

        :param on: a boolean that keeps track if the program should be
        listening to the larry box.
        """
        self.plottingOn = on
        while self.plottingOn:
            self.getData_s()
            time.sleep(0.25)

    def toggleListening(self, on=False):
        """toggleListening
        Easy way to toggle listening on or off

        :param on: the boolean described above
        """
        self.plottingOn = on
        self.getData_test(on=self.plottingOn)
