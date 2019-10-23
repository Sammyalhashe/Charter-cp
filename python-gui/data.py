###############################################################################
from random import random, randint
from rx.subject import Subject
import nidaqmx as nida
import time
from math import sin, cos, pi
import numpy as np
from serial_ard import read_ard

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

    def fourier_example(self, x, A, w, p, num=1):
        funcs = [sin, cos]
        total = 0
        for i in range(num):
            rand_amp = A * random()
            func_i = randint(0, 1)
            total += rand_amp * funcs[func_i](w * x + p)
        return total

    def getData_s(self, channels, x_axis, time_sim=True):
        """getData_s
        This function is a test function that mimics observing the data
        stream from the larry box.

        :param channels: list of booleans => which channels you want to observe
        """
        n = 1
        if not self.stream:
            self.activateStream()
        stream_arr = [[
            # sin(4 * (time.time() + i)) * n for i in range(sum(channels))
            self.fourier_example(time.time() + i, 4 / (3 * pi), 3 * pi / 4, 0)
            if i != 0 else read_ard() for i in range(sum(channels))
            # read_ard() for i in range(sum(channels))
        ]]
        if (x_axis != 0):
            stream_arr.append(cos(4 * (time.time())))
        elif (time_sim):
            stream_arr.append(time.time())

        end = time.time()
        # append time period of the data readings to stream_arr
        # if (x_axis == 0):
        #     if sum(channels) == 1:
        #         stream_arr = [stream_arr]
        #     stream_arr.append(end)
        # else:
        #     stream_arr[len(stream_arr) - 1] = stream_arr[len(stream_arr)
        #                                                  - 1][0]
        self.stream.on_next(stream_arr)

    def getData_test(self,
                     on=False,
                     prod=False,
                     channels=[True, False, False, False],
                     x_axis=0):
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
                self.getData_s(channels, x_axis=x_axis)
            else:
                self.getData_larrybox(channels, x_axis=x_axis)
            # time.sleep(0.25)

    def getData_larrybox(self, channels, x_axis, sampling_rate=10000):
        """getData_larrybox
        fetch data from larrybox

        :param channels: list of 4 booleans to indicate which channels are being used
        :param x_axis: integer indicating which channel is selected. reorders the output.
        :param sampling rate: set sampling rate for fetching data from nidaqmx
        """
        if not self.stream:
            self.activateStream()

        with nida.Task() as task:
            try:
                for i in range(4):
                    if (channels[i] and x_axis != i + 1):
                        task.ai_channels.add_ai_voltage_chan(daq_chnl_names[i])
                if (x_axis != 0):
                    task.ai_channels.add_ai_voltage_chan(
                        daq_chnl_names[x_axis - 1])
                stream_arr = task.read(
                    1)  # read one sample from each channel at a time
            except:
                task.stop()
                for i in range(4):
                    if (channels[i] and x_axis != i + 1):
                        task.ai_channels.add_ai_voltage_chan(daq_chnl_names[i])
                if (x_axis != 0):
                    task.ai_channels.add_ai_voltage_chan(
                        daq_chnl_names[x_axis - 1])
                stream_arr = task.read(
                    1)  # read one sample from each channel at a time
            end = time.time()

            # append time period of the data readings to stream_arr
            if (x_axis == 0):
                if sum(channels) == 1:
                    stream_arr = [stream_arr]
                stream_arr.append(end)
            else:
                stream_arr[len(stream_arr) - 1] = stream_arr[len(stream_arr)
                                                             - 1][0]

            self.stream.on_next(stream_arr)

    def toggleListening(self, on=False):
        """toggleListening
        Easy way to toggle listening on or off

        :param on: the boolean described above
        """
        self.plottingOn = on
        self.getData_test(on=self.plottingOn)
