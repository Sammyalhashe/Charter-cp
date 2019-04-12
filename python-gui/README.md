# Data Charter APL
This document will talk about the process in creating this charter.

## Project Objective
* The main stakeholders already have a data recorder that is written in LABVIEW
* The requirements according to the stakeholders were to reproduce the basic functionality of the LABVIEW recorder, but written in python.
* The reason for this is because the LABVIEW code is very hard to read, so they wanted it ported to python3 for readability and flexibility.
* For example, say they wanted to add more channels, they could esaily do so by slightly modifying the code.

## Backend Construction
* The backend is written as a class that has several class methods for communication with the frontend.
* The goal of the backend is to communicate with the NI (National Instruments) DAQmx board that is present in a device called the "Larrybox", which is a common interface used throughout University of Toronto's Advanced Physics Lab. (It is named after the man who created it).
* To communicate with the board, the [NI-DAQmx python package](https://nidaqmx-python.readthedocs.io/en/latest/) was used.
* This package would written arrays for each channel of data recorded.
* RxPy Subjects were then used to establish connections between backend and frontend.
* Upon recording the data from the Larrybox, the Observer side of the subject would be fed the new data; which would then be recieved from the Observer side in the frontend.

## Frontend Construction
* Upon consultation of public forum and stack overflow, Pyqt5 was decided over tkinter.
* The reason in public consultation was that as the project grows in complexity, pyqt5 is a lot more flexible.
* In addition, pyqt5 actually has a plotting widget, pyqtgraph, which was used to actually plot the data recieved from the backend.
* There are several additional features implemented in the application. For example, there are responsive plot titles, and the ability to export the data as a csv file as well as a picture of the plot.
* Another implementation that I want to do is the ability to switch between different channels after the plotting has stopped.
* So far, the charter replicates everything the LABVIEW recorder can do, such as plotting channels vs. time, and channel vs. channels.