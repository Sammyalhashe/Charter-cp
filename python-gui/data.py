###############################################################################
from random import random
from rx.subjects import Subject
import nidaqmx as nida
import time
from math import sin
import numpy as np

# from PyQt5.QtWidgets import QMessageBox

###############################################################################

daq_chnl_names = ["Dev1/ai0", "Dev1/ai1", "Dev1/ai2", "Dev1/ai3"]

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

    def getData_s(self, channels, x_axis, time_sim=True):
        """getData_s
        This function is a test function that mimics observing the data
        stream from the larry box.

        :param channels: string => How many channel you want to observe
        """
        n = 1

        if not self.stream:
            self.activateStream()
        stream_arr = [[np.random.normal(0, 30)] * n for i in range(sum(channels))]
        if (x_axis != 0):
            stream_arr.append(random()-0.5)
        elif (time_sim):
            stream_arr.append(time.time())
        self.stream.on_next(stream_arr)

    def getData_test(self, on=False, prod=False, channels=[True,True,True,True], x_axis=0):
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
                self.getData_s(channels,x_axis=x_axis)
            else:
                self.getData_larrybox(channels,x_axis=x_axis)
            # time.sleep(0.25)

    def getData_larrybox(self, channels, x_axis, sampling_rate=10000):

        if not self.stream:
            self.activateStream()

        stream_arr = []
        timeline = None

        # append one list for each active channel
        for i in range(sum(channels)):
            stream_arr.append([])

        with nida.Task() as task:
            # initialize all channels based on frontend input of boolean array
            # if (channels[0]):
            #     task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            # if (channels[1]):
            #     task.ai_channels.add_ai_voltage_chan("Dev1/ai1")
            # if (channels[2]):
            #     task.ai_channels.add_ai_voltage_chan("Dev1/ai2")
            # if (channels[3]):
            #     task.ai_channels.add_ai_voltage_chan("Dev1/ai3")

            for i in range(4):
                if (channels[i] and x_axis != i):
                    task.ai_channels.add_ai_voltage_chan(daq_chnl_names[i])
            if (x_axis != -1):
                task.ai_channels.add_ai_voltage_chan(daq_chnl_names[x_axis - 1])

            task.timing.cfg_samp_clk_timing(rate=sampling_rate) #can change sampling rate default 10000
            reading = task.read(1) # read one sample from each channel at a time
            end = time.time()

            # for each active channel, add data to separate lists in stream_arr
            if sum(channels)==1:
                stream_arr[0].extend(reading)
            else:
                for i in range(sum(channels)):
                    stream_arr[i].extend(reading[i])

            # append time period of the data readings to stream_arr
            if (x_axis == -1):
                stream_arr.append(end)
            else:
                stream_arr[len(stream_arr)-1] = stream_arr[len(stream_arr)-1][0]
            self.stream.on_next(stream_arr)

    def toggleListening(self, on=False):
        """toggleListening
        Easy way to toggle listening on or off

        :param on: the boolean described above
        """
        self.plottingOn = on
        self.getData_test(on=self.plottingOn)
