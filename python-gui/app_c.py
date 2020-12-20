###############################################################################
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, \
    QVBoxLayout, QPushButton, QLineEdit, QComboBox, QMessageBox, \
    QInputDialog, QCheckBox, QLabel
from PyQt5.QtCore import QRect  # pyqtSlot
import pyqtgraph as pg
import pyqtgraph.exporters as pg_e
from pyqtgraph.Qt import QtGui
import numpy as np
from styles import styles
from data import dataRPC
import time
import datetime
from copy import deepcopy
from serial_ard import query_serial_ports

###############################################################################

# mapping created for string to pyqt widget class
# used in a creator function below -> widgetCreator
mapping = {
    'button': QPushButton,
    'dropdown': QComboBox,
    'text': QLineEdit,
    'plot': pg.PlotWidget
}

# channel names
channel_names = ["Channel 1", "Channel 2", "Channel 3", "Channel 4"]

# dict table for default colours of plot display
# permitted colours in pyqt for Qpen constructor is (b, g, r, c, m, y, k, w)
colours = {0: 'c', 1: 'w', 2: 'g', 3: 'm', 4: 'r'}


##############################################################################################
# There's a bug with the pyqtgraph library that interferes with image exports.
# One workaround is to edit the library directly. Search for ImageExporter.py and
# replace line 70 with the following:
# bg = np.empty((int(self.params['width']), int(self.params['height']), 4),dtype=np.ubyte)
# another non-intrusive way is to override the default params, which is done in saveData below.
# second method is however just a workaround until pyqt gets their shit together.
##############################################################################################

class CustomPopup(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.parent = parent
        self.ports = Plotter.configurePorts()
        self.selectedPorts = self.parent.data_rpc.portNames
        self.init_UI()

    def selectionChanged(self, i, idx):
        if idx == 0:
            self.selectedPorts[i] = None
        else:
            # ignore the "None" option
            self.selectedPorts[i] = self.ports[idx - 1]
        self.parent.setPorts(self.selectedPorts)

    def init_UI(self):
        # TODO add a refresh ports button
        # creating GUI elements
        self.ch1_textLabel = QLabel("Channel 1")  # text label
        self.ch2_textLabel = QLabel("Channel 2")  # text label
        self.ch3_textLabel = QLabel("Channel 3")  # text label
        self.ch4_textLabel = QLabel("Channel 4")  # text label
        # combo boxes to hold serial port options
        self.ch2_combo = QComboBox()
        self.ch1_combo = QComboBox()
        self.ch3_combo = QComboBox()
        self.ch4_combo = QComboBox()
        # add the selection options
        self.ch1_combo.addItem("None")
        self.ch2_combo.addItem("None")
        self.ch3_combo.addItem("None")
        self.ch4_combo.addItem("None")

        self.ch1_combo.addItems(self.ports)
        self.ch2_combo.addItems(self.ports)
        self.ch3_combo.addItems(self.ports)
        self.ch4_combo.addItems(self.ports)

        # add change callbacks
        self.ch1_combo.currentIndexChanged.connect(
            lambda idx: self.selectionChanged(0, idx))
        self.ch2_combo.currentIndexChanged.connect(
            lambda idx: self.selectionChanged(1, idx))
        self.ch3_combo.currentIndexChanged.connect(
            lambda idx: self.selectionChanged(2, idx))
        self.ch4_combo.currentIndexChanged.connect(
            lambda idx: self.selectionChanged(3, idx))

        # layout init
        self.vbox = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)

        # adding the widgets to the layout
        # layout, 1st row
        self.grid_layout.addWidget(self.ch1_textLabel, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.ch1_combo, 0, 2, 1, 10)
        self.grid_layout.addWidget(self.ch2_textLabel, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.ch2_combo, 1, 2, 1, 10)
        self.grid_layout.addWidget(self.ch3_textLabel, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.ch3_combo, 2, 2, 1, 10)
        self.grid_layout.addWidget(self.ch4_textLabel, 3, 0, 1, 2)
        self.grid_layout.addWidget(self.ch4_combo, 3, 2, 1, 10)
        # initialize grid layout and plotwidget display
        self.vbox.addLayout(self.grid_layout)

        self.setLayout(self.vbox)
        self.setWindowTitle("Configure Channel Input")


class CustomLineEdit(QLineEdit):
    """CustomLineEdit
    Custom textbox that inherits from QLineEdit.
    Added functionality: Will highlight all text upon mouseclick
    """

    def __init__(self, name):
        """__init__"""
        super().__init__(name)
        self.readyToEdit = True  # decides whether to highlight all text on press

    def mousePressEvent(self, e, Parent=None):
        """mousePressEvent
        on first mouse click, select and highlight all text
        for easy overwriting.
        upon second press, deselect all text.
        """
        super().mousePressEvent(e)  #required to deselect on 2e click
        if self.readyToEdit:
            self.selectAll()
            self.readyToEdit = False

    def focusOutEvent(self, e):
        """focusOutEvent
        on focusOut, refreshes self.readyToEdit
        """
        super().focusOutEvent(e)  #required to remove text cursor on focusOut
        self.readyToEdit = True


###############################################################################
class Plotter(QWidget):
    """Plotter"""

    def __init__(self):
        """__init__"""
        # application init
        super().__init__()
        self.data_rpc = dataRPC()
        self.popup = CustomPopup(self)
        self.observer = None
        self.init_UI()

    def widgetCreator(self, widget, **kwargs):
        """widgetCreator

        :param widget: widget to create; see mappings above for names
        :param **kwargs: depending on the widget being created
        """
        if widget == 'plot':
            return mapping[widget]()
        else:
            instance = mapping[widget](
                kwargs.get('text', widget),
                objectName=kwargs.get('name', widget))
            instance.setStyleSheet("""
                                   {0}#{1} {{
                                    background-color: {2};
                                    color: {3};
                                   }}
                                   """.format(mapping[widget].__name__,
                                              kwargs.get('name', widget),
                                              kwargs.get(
                                                  'backColor', 'transparent'),
                                              kwargs.get('color', 'black')))
            return instance

    def messageBox(self, message):
        """messageBox
        creates a popup notication with custom text

        :param message: message to display on message box
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setInformativeText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(lambda _: print("Ok"))
        msg.exec_()

    def init_UI(self):
        """init_UI"""
        # common component init
        self.btn = QPushButton("Start", self)
        self.stop = QPushButton("Configure", self)
        self.btn.setStyleSheet(
            'QPushButton {background-color: #A3C1DA; color: blue;}')
        self.stop.setStyleSheet(
            'QPushButton {background-color: #A3C1DA; color: red;}')

        # example usages of widgetCreator in case you wanted to make use of it
        # as you can see, it gives you some flexibility
        self.clear = self.widgetCreator(
            'button',
            text='Clear',
            name='clearButton',
            backColor='green',
            color='red')
        self.save = self.widgetCreator(
            'button',
            text='Save',
            name='saveButton',
            backColor='teal',
            color='orange')

        # plotting variables
        self.subscription = None  # indicate if subscription is present
        self.currentlyPlotting = False  # boolean to indicate plotter status
        self.data = np.array([])  # y_axis numpy data
        self.x_axis_data = np.array([])  # x_axis numpy data
        self.current_time = None  # current unix timestamp. used to normalize time-axis
        self.traces = []  # list of all PlotDataItems currently on plotter
        self.channels = [True, False, False,
                         False]  # default channel selection
        self.previousChannels = None  # store previous channel state when plotting is stopped
        self.x_axis_selection = 0  # indicates which channel {1,2,3,4} is x-axis. 0 indicates time.
        self.legend = None  # stores a reference to the plot legend for subsequent deletion
        self.traceSegment = 1000  # each trace should only hold 1000 datapoints max
        self.maxSegments = 20  # max number of traces allowed
        self.windowRange = 5.  # default window of 10
        self.Y_lower = None  # user-set y-axis lower limit
        self.Y_upper = None  # user-set y-axis upper limit

        # creating GUI elements
        self.Ytext_QLabel = QLabel("Y-Axis Title: ")  # text label
        self.Xtext_QLabel = QLabel("X-Axis Title: ")  # text label
        self.Xtext = CustomLineEdit(
            "Label for x-axis")  # textbox for x-axis title
        self.Ytext = CustomLineEdit(
            "Label for y-axis")  # textbox for y-axis title
        self.YLimits_QLabel = QLabel("Range (y-axis): ")  # text label
        self.Y_lower_text = CustomLineEdit(
            "Lower Limit for y-axis")  # textbox for y-lower scale
        self.Y_upper_text = CustomLineEdit(
            "Upper Limit for y-axis")  # textbox for y-upper scale
        self.XLimits_QLabel = QLabel(
            "Range (x-axis): "
        )  # text label for x-window scaling. hidden in chnl vs chnl plotting.
        self.X_lower_text = CustomLineEdit(
            "Lower Limit for x-axis"
        )  # textbox for x-lower scale. hidden in time plotting.
        self.X_upper_text = CustomLineEdit(
            "Upper Limit for x-axis"
        )  # textbox for x-upper scale. hidden in time plotting.
        self.XLimits_QLabel.setVisible(
            False
        )  # plotter starts up with time-plotting selected, so hidden by default
        self.X_lower_text.setVisible(
            False
        )  # plotter starts up with time-plotting selected, so hidden by default
        self.X_upper_text.setVisible(
            False
        )  # plotter starts up with time-plotting selected, so hidden by default
        self.windowRange_QLabel = QLabel(
            "Window Range: ")  # textbox for x-window size
        self.windowRange_text = CustomLineEdit(
            str(self.windowRange) +
            " (default)")  # default text for x-window size
        self.autoscale_Y = QPushButton(
            "AutoY", self)  # turn on and off autoscaling of Y axis
        self.autoscale_X = QPushButton(
            "AutoX", self)  # turn on and off autoscaling of X axis
        self.autoscale_X.setCheckable(True)  # enable toggling of button
        self.autoscale_Y.setCheckable(True)  # enable toggling of button
        self.autoscale_Y.setChecked(
            True)  # set autoscaling of Y to true by default
        # buttons for selecting channels
        self.chnl1_button = QPushButton("Channel 1", self)
        self.chnl2_button = QPushButton("Channel 2", self)
        self.chnl3_button = QPushButton("Channel 3", self)
        self.chnl4_button = QPushButton("Channel 4", self)
        self.chnl1_button.setCheckable(True)
        self.chnl2_button.setCheckable(True)
        self.chnl3_button.setCheckable(True)
        self.chnl4_button.setCheckable(True)
        # put all chnl buttons in a dict table to facilitate referencing in loops
        self.channel_buttons = {
            1: self.chnl1_button,
            2: self.chnl2_button,
            3: self.chnl3_button,
            4: self.chnl4_button
        }
        self.chnl1_button.setChecked(True)  # Channel 1 is selected by default
        # plot-display checkboxes. toggles scatter or line plot display
        self.scatter_chkbox = QCheckBox("Scatter", self)
        self.line_chkbox = QCheckBox("Line", self)
        self.line_chkbox.setChecked(True)
        # combobox for x-axis channel selection
        self.x_axis_ComboBox_QLabel = QLabel("X-Axis: ")
        self.x_axis_ComboBox = QComboBox(self)
        self.x_axis_ComboBox.addItem('Time (Default)')
        # WARNING: channels are referenced by their indices in combobox list.
        #          if you change the ordering, you will need to change the behaviour
        #          in self.change_x_axis()
        items = ["Channel {}".format(i + 1) for i in range(4)]
        for name in items:
            self.x_axis_ComboBox.addItem(name)

        # functionality for all created GUI elements
        # connects all the buttons/labels to their associated functions
        self.btn.clicked.connect(lambda _: self.StartClicked())
        self.stop.clicked.connect(lambda _: self.ConfigurePorts())
        self.clear.clicked.connect(lambda _: self.clearData())
        self.save.clicked.connect(lambda _: self.saveData())
        self.Xtext.textEdited.connect(self.setTitle)
        self.Ytext.textEdited.connect(self.setTitle)
        self.Xtext.textEdited.connect(self.setXLabel)
        self.Ytext.textEdited.connect(self.setYLabel)
        self.Y_lower_text.textEdited.connect(self.setYRange)
        self.Y_upper_text.textEdited.connect(self.setYRange)
        self.X_lower_text.textEdited.connect(self.setXRange)
        self.X_upper_text.textEdited.connect(self.setXRange)
        self.autoscale_X.clicked.connect(lambda _: self.setAutoscale(0))
        self.autoscale_Y.clicked.connect(lambda _: self.setAutoscale(1))
        self.windowRange_text.textEdited.connect(self.setWindowRange)
        self.chnl1_button.clicked.connect(lambda _: self.toggleChannels())
        self.chnl2_button.clicked.connect(lambda _: self.toggleChannels())
        self.chnl3_button.clicked.connect(lambda _: self.toggleChannels())
        self.chnl4_button.clicked.connect(lambda _: self.toggleChannels())
        self.x_axis_ComboBox.activated.connect(lambda _: self.change_x_axis())
        self.scatter_chkbox.stateChanged.connect(
            lambda _: self.togglePlotStyle())
        self.line_chkbox.stateChanged.connect(lambda _: self.togglePlotStyle())

        # pyqt graph init
        self.plotWidget = pg.PlotWidget()  # create the widget for viewing

        # layout init
        self.vbox = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)

        # adding the widgets to the layout
        # layout, 1st row
        self.grid_layout.addWidget(self.Ytext_QLabel, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.Ytext, 0, 2, 1, 10)
        self.grid_layout.addWidget(self.Xtext_QLabel, 0, 12, 1, 2)
        self.grid_layout.addWidget(self.Xtext, 0, 14, 1, 10)
        self.grid_layout.addWidget(self.btn, 0, 24)
        self.grid_layout.addWidget(self.stop, 0, 25)
        # layout, 2nd row
        self.grid_layout.addWidget(self.YLimits_QLabel, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.Y_lower_text, 1, 2, 1, 5)
        self.grid_layout.addWidget(self.Y_upper_text, 1, 7, 1, 5)
        self.grid_layout.addWidget(self.x_axis_ComboBox_QLabel, 1, 12, 1, 2)
        self.grid_layout.addWidget(self.x_axis_ComboBox, 1, 14, 1, 10)
        self.grid_layout.addWidget(self.clear, 1, 24)
        self.grid_layout.addWidget(self.save, 1, 25)
        # layout, 3rd row
        self.grid_layout.addWidget(self.windowRange_QLabel, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.windowRange_text, 2, 2, 1, 10)
        self.grid_layout.addWidget(self.XLimits_QLabel, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.X_lower_text, 2, 2, 1, 5)
        self.grid_layout.addWidget(self.X_upper_text, 2, 7, 1, 5)
        self.grid_layout.addWidget(self.autoscale_Y, 2, 24)  #
        self.grid_layout.addWidget(self.autoscale_X, 2, 25)  #
        # layout, 4th row
        self.grid_layout.addWidget(self.chnl1_button, 3, 0, 1, 6)
        self.grid_layout.addWidget(self.chnl2_button, 3, 6, 1, 6)
        self.grid_layout.addWidget(self.chnl3_button, 3, 12, 1, 6)
        self.grid_layout.addWidget(self.chnl4_button, 3, 18, 1, 6)
        self.grid_layout.addWidget(self.line_chkbox, 3, 24)
        self.grid_layout.addWidget(self.scatter_chkbox, 3, 25)

        # initialize grid layout and plotwidget display
        self.vbox.addLayout(self.grid_layout)
        self.vbox.addWidget(self.plotWidget)

        # application showing
        self.setLayout(self.vbox)
        self.setGeometry(300, 300, 1468, 1468)
        self.windowWidth = 768
        self.setWindowTitle("Plotter")
        self.setTitle()
        self.setXLabel()
        self.setYLabel()
        self.plotWidget.setXRange(
            0, self.windowRange)  #  : initial window from 0 to XRange.
        self.show()

    def StartClicked(self):
        if not self.currentlyPlotting:
            self.plotData()
        else:
            self.stopData()

    # toggles whether to represent data by connected lines, scatterpoints (symbols), or both

    def togglePlotStyle(self, hide_non_selected=False):
        """togglePlotStyle
        toggles whether to represent data by connected lines, scatterpoints (symbols), or both
        :param hide_non_selected: if this parameter is True,
                                    and if plotting is stopped but not cleared,
                                    hide all user-deselected channels.
        """
        # first, retrieve checked status from the user buttons
        line = self.line_chkbox.isChecked()
        scatter = self.scatter_chkbox.isChecked()
        # if plot elements exist and hide_non_selected is false, toggle as usual.
        # this conditional is usually activated during live plotting.
        if (len(self.traces) > 0 and hide_non_selected == False):
            for i in range(len(self.traces)):
                if (scatter == True):
                    self.traces[i].setSymbol('o')
                    self.traces[i].setSymbolBrush(colours[i])
                elif (scatter == False):
                    self.traces[i].setSymbol(None)
                    self.traces[i].setSymbolBrush(None)
                if (line == True):
                    self.traces[i].setPen(colours[i])
                elif (line == False):
                    self.traces[i].setPen(None)
        # if plot elements exist and hide_non_selected is True,
        # this conditional was activated when plotting has already stopped
        # we need to toggle the display based on the saved states
        # from self.previousChannels since self.channels would already be cleared.
        elif (len(self.traces) > 0 and hide_non_selected):
            trace_index = 0
            for i in range(4):
                if (self.previousChannels[i]):
                    if (scatter):
                        self.traces[trace_index].setSymbol(
                            'o' if self.channel_buttons[i + 1].isChecked() else
                            None)
                        self.traces[trace_index].setSymbolBrush(
                            colours[trace_index] if self.channel_buttons[i + 1]
                            .isChecked() else None)
                    if (line):
                        self.traces[trace_index].setPen(
                            colours[trace_index] if self.channel_buttons[i + 1]
                            .isChecked() else None)
                    trace_index += 1  # move on to next trace in self.trace

    def change_x_axis(self):
        """change_x_axis
        changes the x_axis selection. the selection will be fetched from
        the gui combobox in self.x_axis_Combobox, and subsequently
        stored in self.x_axis_selection as an integer. Below are the integer
        representations of all possible selections. They are selected to be the
        same as their indices in the GUI combobox.
        0: Time
        1: Channel 1
        2: Channel 2
        3: Channel 3
        4: Channel 4
        """
        self.x_axis_selection = self.x_axis_ComboBox.currentIndex(
        )  # fetch from GUI
        # if x-axis is a channel, we set turn on autoscale,
        # then hide self.windowRange_text and enable user to set
        # both upper and lower limits of x range
        if (self.x_axis_selection != 0):
            self.autoscale_X.setChecked(True)
            self.autoscale_Y.setChecked(True)
            self.setAutoscale()  # update autoscaling
            self.windowRange_QLabel.setVisible(False)
            self.windowRange_text.setVisible(False)
            self.XLimits_QLabel.setVisible(True)
            self.X_lower_text.setVisible(True)
            self.X_upper_text.setVisible(True)
        # else, the x-axis is time, so we restrict the user and only
        # allow one QLineEdit for size adjustment of current window.
        else:
            self.autoscale_X.setChecked(False)
            self.autoscale_Y.setChecked(True)
            self.setAutoscale()  # update autoscaling
            self.XLimits_QLabel.setVisible(False)
            self.X_lower_text.setVisible(False)
            self.X_upper_text.setVisible(False)
            self.windowRange_QLabel.setVisible(True)
            self.windowRange_text.setVisible(True)
        # if x-axis channel selection was toggled while plotter was plotting
        # stop plotting, clear, then toggle channels accordingly and restart the plot
        if (self.currentlyPlotting):
            self.stopData()
            self.clearData()
            self.toggleChannels()
            self.plotData()
        # else, simply make a call to toggleChannels to set channels appriopriately
        else:
            self.toggleChannels()

    def toggleChannels(self):
        """toggleChannels
        this function toggles the channels being plotted. if plotting is currently ongoing
        it is equivalent to stopping, reseting, and then restarting the plot with the selected channels
        if plotting is stopped but not reset, it simply hides or displays the existing plots
        if no plots are on display and plotting is stopped, it only edits self.channels for the next
        time that the plot is started
        """
        # if user is trying to plot channel against itself, block the attempt.
        if (self.x_axis_selection != 0
                and self.channel_buttons[self.x_axis_selection].isChecked()):
            self.channel_buttons[self.x_axis_selection].setChecked(False)
            if (self.channels[self.x_axis_selection - 1] == False
                ):  # if it was already plotting normally before, just return
                return  # otherwise, proceed and reset the plot to stop
                # channel from being plotted against itself.
        # proceed to fetch button selection status from GUI
        self.channels = [
            self.chnl1_button.isChecked(),
            self.chnl2_button.isChecked(),
            self.chnl3_button.isChecked(),
            self.chnl4_button.isChecked()
        ]
        # if function was called while live plotting was ongoing, reset the plot
        if (self.currentlyPlotting):
            self.stopData()
            self.clearData()
            if (sum(self.channels) > 0):
                self.plotData()
            else:
                self.messageBox(
                    "No channels selected. Plotting has been stopped.")
        # when plot is stopped but there are previous graphs, we just toggle visibility of previous graphs
        # by calling self.togglePlotStyle() programatically with hide_non_selected as True.
        elif (self.previousChannels != None and len(self.traces) > 0):
            self.togglePlotStyle(hide_non_selected=True)

    def setYRange(self):
        """setYRange
        changes the display range of y-axis
        """
        try:
            # fetches data from GUI elements and checks if they are valid values
            # note that we don't check for if self.Y_lower > self.Y_upper.
            # this is already handled by the pyqt library, so we just pass the values
            # on.
            self.Y_lower = float(self.Y_lower_text.text())
            self.Y_upper = float(self.Y_upper_text.text())
            self.plotWidget.setYRange(self.Y_lower, self.Y_upper)
            self.plotWidget.enableAutoRange(axis=1, enable=False)
            self.autoscale_Y.setChecked(False)
        except:
            self.Y_lower = None
            self.Y_upper = None

    def setXRange(self):
        """setXRange
        changes the display range of x-axis. only applicable in
        multichannel vs channel plotting mode
        """
        try:
            self.X_lower = float(self.X_lower_text.text())
            self.X_upper = float(self.X_upper_text.text())
            self.plotWidget.setXRange(self.X_lower, self.X_upper)
            self.plotWidget.enableAutoRange(axis=0, enable=False)
            self.autoscale_X.setChecked(False)
        except:
            self.X_lower = None
            self.X_upper = None

    def setWindowRange(self):
        """setWindowRange
        changes the x-axis window size to display, only applicable
        in time-plotting mode
        """
        try:
            self.windowRange = float(
                self.windowRange_text.text()
            )  # : retrieves value from user box. TODO: proof against invalid values eg. letters
            print("Setting window range to " + str(self.windowRange))
            self.plotWidget.setXRange(0, self.windowRange)
            #self.X_autoscale = False
        except:
            pass

    def setAutoscale(self, axis=None):
        """setAutoscale
        toggles autoscaling for axes
        :param axis: optional integer (0 or 1) to select which axis to toggleAutoscale
        0 : x-axis
        1 : y-axis
        """
        if (axis == 0
                or axis == 1):  # if axis is specified, change only for that
            if (axis == 0):
                enable = self.autoscale_X.isChecked()
            else:
                enable = self.autoscale_Y.isChecked()
            self.plotWidget.enableAutoRange(axis=axis, enable=enable)
            if (enable == False and axis == 0):
                self.plotWidget.setXRange(0, self.windowRange)
        else:  # else, change for both based on button status
            self.plotWidget.enableAutoRange(
                axis=0, enable=self.autoscale_X.isChecked())
            if (not self.autoscale_X.isChecked()):
                self.plotWidget.setXRange(0, self.windowRange)
            self.plotWidget.enableAutoRange(
                axis=1, enable=self.autoscale_Y.isChecked())

    def setTitle(self):
        """
        setTitle

        Sets the title of the plot based on the QLineEdits for the
        x/y label
        """
        xtext = self.Xtext.text()
        ytext = self.Ytext.text()
        self.plotWidget.setTitle("""
                                 <h1>{0} vs {1}</h1>
                                 """.format(ytext, xtext))

    def setXLabel(self):
        """
        setXLabel
        Same as set title but for the xlabel
        """
        xtext = self.Xtext.text()
        html = """
            <style>{0}</style>
            <i class='label'>{1}</i>
        """.format(styles['label'], xtext)
        self.plotWidget.setLabel('bottom', text=html)

    def setYLabel(self):
        """
        setYLabel
        Same as set title but for the ylabel
        """
        ytext = self.Ytext.text()
        html = """
            <style>{0}</style>
            <i class='label'>{1}</i>
        """.format(styles['label'], ytext)
        self.plotWidget.setLabel('left', text=html)

    def togglePlottingStatus(self):
        if self.currentlyPlotting:
            self.btn.setText("Stop")
        else:
            self.btn.setText("Start")

    @staticmethod
    def configurePorts():
        ports = query_serial_ports()
        return ports

    def ConfigurePorts(self):
        self.popup.setGeometry(QRect(100, 100, 400, 200))
        self.popup.show()
        # ports = Plotter.configurePorts()
        # items = ports
        # item, ok = QInputDialog.getItem(self, "Get item", "Color:", items, 0,
        #                                 False)
        # if ok and item:
        #     print(item)

    def setPorts(self, ports):
        self.data_rpc.setPorts(ports)

    def getObserver(self):
        """
        getObserver
        Frontend and backend communicate with an RxPy Subject.
        This function grabs the observer from the backend for communication
        to occur
        """
        if not self.observer:
            # tells the backend to activate (instantiate) the Subject
            self.data_rpc.activateStream()
            # grab the subject; I call it observer as a Subject can act as
            # both an observer and observable, but in the frontend it only
            # acts as the observer.
            self.observer = self.data_rpc.getStream()

    def plotData(self):
        """plotData"""
        # if plotting is already happening
        if (sum(self.channels) == 0):
            self.messageBox("Please select at least one channel")
            return
        if self.currentlyPlotting:
            self.messageBox("Already Plotting")
            return
        # self.data_rpc.togglePortConnections()
        # If not plotting, but there is already data on the plot,
        # first clear, and then starting plotting again
        if self.data is not None and self.data.size != 0:
            self.clearData()
        # if more than 1 channel is selected, add a legend
        if (sum(self.channels) > 0):
            self.legend = self.plotWidget.addLegend()
        # set that we are plotting
        self.currentlyPlotting = True
        self.togglePlottingStatus()
        # if we have not yet grabbed the observer from the backend, get it
        if not self.observer:
            self.getObserver()
        # if we have not yet subscribed to the observer, or if we stopped
        # subscribing to the observer, subscribe to it
        if not self.subscription:
            # depending on the current rx version, try different versions
            # of subscribe since the older versions use subscribe_()
            try:
                self.subscription = self.observer.subscribe_(
                    lambda x: self.addData(x))
            except:
                self.subscription = self.observer.subscribe(
                    lambda x: self.addData(x))
        # this is the function that starts the data collection in the backend
        # the on variable starts and stops data observation in the backend
        # prod=boolean is a variable that sets whether we retrieve test/actual
        # values
        self.data_rpc.getData_test(
            on=True,
            prod=False,
            larrybox=False,
            channels=self.channels,
            x_axis=self.x_axis_selection)

    def addData(self, newData):
        """addData
        Adds a single data point to a trace
        :param newData: single new data point to add
        """
        # get the time window of the incoming data
        new_x_data = newData.pop()
        # refactor the new incoming data
        # TODO
        # fixedNewData = np.array([i for i in newData])
        # TODO
        newData = newData.pop()
        fnd = [[i] for i in newData]
        fixedNewData = np.array(fnd)
        # if we are at the start of plotting
        if self.data.size == 0:
            self.data = np.zeros_like(fixedNewData)
            self.data += np.array(fixedNewData)
            # self.data += fixedNewData
            self.x_axis_data = np.zeros(1)
            if (self.x_axis_selection == 0):  # if time is the x_axis
                self.current_time = 0
                self.start = new_x_data
            else:
                self.x_axis_data += new_x_data
            # this is the first time adding data
            starting = True
        # data already exists, concatenate it
        else:
            # self.ptr += 1
            self.data = np.concatenate((self.data, fixedNewData), axis=1)
            if (self.x_axis_selection == 0):  # if time is the x_axis
                self.current_time = new_x_data - self.start  # update time position of next incoming data
                self.x_axis_data = np.append(self.x_axis_data,
                                             self.current_time)
            else:
                self.x_axis_data = np.append(self.x_axis_data, new_x_data)

            # there is already data
            starting = False
        # Since we are just starting, we create new traces for each channel
        # and add the first set of datapoints to those traces
        if starting:
            index = 0
            for i in range(4):
                if (self.channels[i]):
                    plot = self.plotWidget.plot(
                        x=self.x_axis_data,  # underlying numpy x-axis data
                        y=self.data[index],  # underlying numpy y-axis
                        pen=colours[index] if self.line_chkbox.isChecked() else
                        None,  # line display, if selected by user
                        symbol='o' if self.scatter_chkbox.isChecked() else
                        None,  # scatter display, if selected by user
                        symbolBrush=colours[index]
                        if self.scatter_chkbox.isChecked() else
                        None,  # scatter display, if selected by user
                        symbolSize=5,  # scatter display size
                        name=channel_names[
                            i])  # fetch channel names from global dict table
                    index += 1
                    self.traces.append(
                        plot
                    )  # consolidate all created PlotDataItems in self.traces
        # The traces already exist. Add the new data to each of the already
        # existing traces
        else:
            for i in range(len(self.data)):
                self.traces[i].setData(x=self.x_axis_data, y=self.data[i])
                if (self.x_axis_selection !=
                        0  # if plotting against channel instead of time
                        or self.current_time < self.
                        windowRange  # or if plotting against time and it still fits witin window
                        or self.autoscale_X.isChecked()
                    ):  # or if autoscaling is on
                    self.traces[i].setPos(0, 0)  # set position of plot to 0
                else:  # . else, we just clip the plotItem accordingly
                    self.traces[i].setPos(
                        -self.current_time + self.windowRange,
                        0)  #  setPos of each plotItem
            # this is necessary for data smoothly being added/removed from plot
            QtGui.QApplication.processEvents()

    def stopData(self):
        """stopData
        Stops data collection in general.
        The data arrays are still filled,
        and the plotting variables are still
        not yet reset.
        """

        # a boolean for keeping track if we are currently plotting
        # we set it false as we are stopping plotting
        self.currentlyPlotting = False
        self.togglePlottingStatus()

        # if subscription does not exist, data wasn't being plotted in the first place
        # returns
        if not self.subscription:
            self.messageBox("No data is being plotted")
            return
        # there is a subscription that we mean to stop.
        # The subscription is destroyed and we tell the backend to stop
        # plotting by using the toggleListening(on=boolean) function
        else:
            # keep a deep copy of the channel selection state so
            # that the program can continue to make changes to display if needed
            self.previousChannels = deepcopy(self.channels)
            self.subscription.dispose()  # remove subscription
            self.subscription = None
            self.data_rpc.toggleListening(on=False)
            QtGui.QApplication.processEvents()

    def clearData(self):
        """clearData
        Clears the plot of all traces, and
        resets all relevant plotting variables
        """
        # If there is a subscription, plotting hasn't been stopped
        # remind the user to stop plotting before trying to clear
        if self.subscription is not None:
            self.messageBox("Stop plotting before you clear")
            return

        # if the data is empty, there is no data to clear
        if self.data.size == 0:
            self.messageBox("No data has been plotted")
        # remove all data from traces and clear data
        else:
            self.legend.scene().removeItem(self.legend)
            for i in range(len(self.data)):
                #print(self.traces[i])
                self.traces[i].clear()
            self.traces = []
            # self.plotWidget.clear()
            self.data = np.array([])
            self.x_axis_data = np.array([])
            self.current_time = None

    def saveData(self):
        """saveData
        Saves the data in .csv format and/or .PNG image format
        """
        #self.exportToCSV()
        if not self.currentlyPlotting and self.data.size != 0:
            # fetch date and time to use as default filename
            currentDT = datetime.datetime.now()
            defaultnameCSV = currentDT.strftime("data_%Y-%m-%d_%H-%M-%S")
            defaultnamePNG = currentDT.strftime("plot_%Y-%m-%d_%H-%M-%S")

            # first, prompt user if they want to save as .csv
            (filename, ok) = QInputDialog.getText(
                self, "Data Export to CSV",
                "Filename (without .csv):                  ", QLineEdit.Normal,
                defaultnameCSV)
            if (ok):  # if user clicked okay, start saving .csv. else pass.
                filename += '.csv'  # append correct file format
                exporter = pg_e.CSVExporter(self.plotWidget.plotItem)
                exporter.export(fileName=filename)
                self.messageBox('Data saved to ' + filename)

            # then, prompt user if they want to save as .png
            (filename, ok) = QInputDialog.getText(
                self, "Image Export to PNG",
                "Filename (without .png):                  ", QLineEdit.Normal,
                defaultnamePNG)
            if (
                    ok
            ):  # if user clicked okay on second popup, save as png. else pass.
                filename += '.png'
                exporter = pg_e.ImageExporter(self.plotWidget.plotItem)
                # these following two lines circumvent the bug in pyqt library.
                # once the pyqt authors have fixed it in future updates, they shouldn't
                # be needed.
                exporter.params.param('width').setValue(
                    1920, blockSignal=exporter.widthChanged)
                exporter.params.param('height').setValue(
                    1080, blockSignal=exporter.heightChanged)
                exporter.export(fileName=filename)
                self.messageBox('Data saved to ' + filename)
        else:
            self.messageBox(
                "Make sure you aren't plotting, or there is no data")


###############################################################################


def app():
    app = QApplication(sys.argv)
    plotter = Plotter()
    # only exit when the exec_ function is called
    sys.exit(app.exec_())


if __name__ == '__main__':
    app()
# app = QApplication(sys.argv)
# plotter = Plotter()
# # only exit when the exec_ function is called
# sys.exit(app.exec_())
