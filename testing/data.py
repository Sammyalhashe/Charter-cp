import zerorpc
from random import random
from rx.subjects import Subject
import time
from math import sin


class dataRPC():
    """dataRPC"""

    def __init__(self):
        self.stream = None
        self.plottingOn = False

    def getData(self, channels="1"):
        """getData

        :param channels: channels connected to
        """
        channels = channels.split(' ')
        return [random() for i in channels], [i for i in channels]

    def getStream(self):
        if not self.stream:
            print("Activate the Data Stream first")
            return None
        return self.stream

    def activateStream(self):
        if not self.stream:
            self.stream = Subject()

    def getData_s(self, channels="1 2"):
        if not self.stream:
            self.activateStream()
        channels = channels.split(' ')
        self.stream.on_next([sin(random()) for i in channels])

    def getData_test(self, on=False):
        self.plottingOn = on
        while self.plottingOn:
            self.getData_s()
            time.sleep(0.25)

    def toggleListening(self, on=False):
        self.plottingOn = on
        self.getData_test(on=self.plottingOn)

    @zerorpc.stream
    def dataStream(self, channels="1"):
        channels = channels.split(' ')
        return [random() for i in channels]
