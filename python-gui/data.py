###############################################################################
from random import random
from rx.subjects import Subject
import nidaqmx as nida
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

    def getData_s(self, channels="1 2", time_sim=True):
        """getData_s
        This function is a test function that mimics observing the data
        stream from the larry box.

        :param channels: string => How many channel you want to observe
        """
        if not self.stream:
            self.activateStream()
        channels = channels.split(' ')
        stream_arr = [[sin(random())] * 10 for i in channels]
        if (time_sim):
            stream_arr.append(random()*5)
        self.stream.on_next(stream_arr)

    def getData_test(self, on=False, prod=False, channels=[True,True,True,True]):
        """getData_test
        Function that starts the test data observation

        :param on: a boolean that keeps track if the program should be
        listening to the larry box.
        :param prod: a boolean that determines whether data is simulated
        or fetched from larry box. True: fetch from larrybox. False: simulate
        :param channels: a list of booleans (size 4) that indicate which channels
        on the larry box to collect data from. only applicable when prod=True
        """
        self.plottingOn = on
        while self.plottingOn:
            if not prod:
                self.getData_s()
            else:
                self.getData_larrybox(channels)
            time.sleep(0.25)

    def getData_larrybox(self, channels):

        if not self.stream:
            self.activateStream()

        n = 256
        start = time.time()
        end = start

        # values1 = []
        # values2 = []
        # values3 = []
        # values4 = []
        # timeline = []

        # for i in range(n):
        #     values1.append(0)
        #     values2.append(0)
        #     values3.append(0)
        #     values4.append(0)
        #     timeline.append(0)

        stream_arr = []
        timeline = None

        # append one list for each active channel
        for i in range(sum(channels)):
            stream_arr.append([])

        with nida.Task() as task:
            # initialize all channels based on frontend input of boolean array
            if (channels[0]):
                task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            if (channels[1]):
                task.ai_channels.add_ai_voltage_chan("Dev1/ai1")
            if (channels[2]):
                task.ai_channels.add_ai_voltage_chan("Dev1/ai2")
            if (channels[3]):
                task.ai_channels.add_ai_voltage_chan("Dev1/ai3")
            reading = task.read(n)

            end = time.time()

            # for each active channel, add data to separate lists in stream_arr
            for i in range(sum(channels)):
                stream_arr[i].extend(reading[i])

            # append time period of the data readings to stream_arr
            stream_arr.append(end-start)

            # values1.extend(reading[0])
            # values2.extend(reading[1])
            # values3.extend(reading[2])
            # values4.extend(reading[3])
            # timeline.extend(end - start)

            # del (values1[:n])
            # del (values2[:n])
            # del (values3[:n])
            # del (values4[:n])
            # del (timeline[:-1])

            # stream_arr = []
            # stream_arr.append(values1)
            # stream_arr.append(values2)
            # stream_arr.append(values3)
            # stream_arr.append(values4)
            self.stream.on_next(stream_arr)

    def toggleListening(self, on=False):
        """toggleListening
        Easy way to toggle listening on or off

        :param on: the boolean described above
        """
        self.plottingOn = on
        self.getData_test(on=self.plottingOn)
