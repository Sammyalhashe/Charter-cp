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
from time import time
import datetime

###############################################################################

# mapping created for string to pyqt widget class
# used in a creator function below -> widgetCreator
mapping = {
    'button': QPushButton,
    'dropdown': QComboBox,
    'text': QLineEdit,
    'plot': pg.PlotWidget
}

channel_names = ["Channel 1",
                 "Channel 2",
                 "Channel 3",
                 "Channel 4"]

# permitted colours in pyqt for Qpen constructor is (b, g, r, c, m, y, k, w)
colours = {
    0: 'm', 
    1: 'w', 
    2: 'g', 
    3: 'r',
    4: 'c'  
}

# Custom textbox that inherits from QLineEdit.
# Added functionality: Will highlight all text upon mouseclick
class CustomLineEdit(QLineEdit):
    def __init__(self, name):
        super().__init__(name)
        self.readyToEdit = True

    def mousePressEvent(self, e, Parent=None):
        super().mousePressEvent(e) #required to deselect on 2e click
        if self.readyToEdit:
            self.selectAll()
            self.readyToEdit = False

    def focusOutEvent(self, e):
        super().focusOutEvent(e) #required to remove cursor on focusOut
        # self.deselect()
        self.readyToEdit = True


###############################################################################
class Plotter(QWidget):
    """Plotter"""

    def __init__(self):
        """__init__"""
        # application init
        super().__init__()
        self.data_rpc = dataRPC()
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
                                   """.format(
                mapping[widget].__name__, kwargs.get('name', widget),
                kwargs.get('backColor', 'transparent'),
                kwargs.get('color', 'black')))
            return instance

    def messageBox(self, message):
        """messageBox

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
        self.stop = QPushButton("Stop", self)
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

        self.windowRange = 5.  #### CHANGED_HERE default window of 10
        self.Y_lower = None # CHANGED_HERE user-set y-axis lower limit
        self.Y_upper = None # CHANGED_HERE user-set y-axis upper limit
        #self.X_autoscale = False # CHANGED_HERE boolean to switch on and off Y-autoscaling
        self.plotSegments = 100 # CHANGED_HERE segment the plot into smaller plotItems for memory management
        self.maxSegments = 20 # CHANGED_HERE only allow this number of 
                              # segments on the plot at a time. After this, 
                              # start deleting segments in FIFO order.

        # creating GUI elements
        self.Ytext_QLabel = QLabel("Y-Axis Title: ")
        self.Xtext_QLabel = QLabel("X-Axis Title: ")
        self.Xtext = CustomLineEdit("Label for x-axis")
        self.Ytext = CustomLineEdit("Label for y-axis")
        self.YLimits_QLabel = QLabel("Range (y-axis): ")
        self.Y_lower_text = CustomLineEdit("Lower Limit for y-axis")
        self.Y_upper_text = CustomLineEdit("Upper Limit for y-axis")
        self.XLimits_QLabel = QLabel("Range (x-axis): ")
        self.X_lower_text = CustomLineEdit("Lower Limit for x-axis")
        self.X_upper_text = CustomLineEdit("Upper Limit for x-axis")
        self.XLimits_QLabel.setVisible(False)
        self.X_lower_text.setVisible(False)
        self.X_upper_text.setVisible(False)
        self.windowRange_QLabel = QLabel("Window Range: ")
        self.windowRange_text = CustomLineEdit(str(self.windowRange) + " (default)") # CHANGED_HERE QLine for window range. allow dude to change window size from gui. TODO: fit it nicely somewhere into gui.
        self.autoscale_Y = QPushButton("AutoY", self) # CHANGED_HERE turn on and off autoscaling of Y axis
        self.autoscale_X = QPushButton("AutoX", self) # CHANGED_HERE turn on and off autoscaling of X axis
        self.autoscale_X.setCheckable(True)
        self.autoscale_Y.setCheckable(True)
        self.autoscale_Y.setChecked(True)
        self.chnl1_button = QPushButton("Channel 1", self)
        self.chnl2_button = QPushButton("Channel 2", self)
        self.chnl3_button = QPushButton("Channel 3", self)
        self.chnl4_button = QPushButton("Channel 4", self)
        self.chnl1_button.setCheckable(True)
        self.chnl2_button.setCheckable(True)
        self.chnl3_button.setCheckable(True)
        self.chnl4_button.setCheckable(True)
        self.chnl1_button.setChecked(True) # Channel 1 is selected by default
        self.scatter_chkbox = QCheckBox("Scatter", self)
        self.line_chkbox = QCheckBox("Line", self)
        self.line_chkbox.setChecked(True)

        self.x_axis_ComboBox_QLabel = QLabel("X-Axis: ")
        self.x_axis_ComboBox = QComboBox(self)
        self.x_axis_ComboBox.addItem('Time (Default)')
        # WARNING: channels are referenced by their indices in combobox list
        #          if you change the ordering, you will need to change the behaviour
        #          in self.change_x_axis()
        items = ["Channel {}".format(i + 1) for i in range(4)]
        for name in items:
            self.x_axis_ComboBox.addItem(name)

        # combobox init: For choosing the channels
        # self.YcomboBox = QComboBox(self)
        # self.YcomboBox.setGeometry(QRect(40, 40, 491, 31))
        # self.YcomboBox.setObjectName(("Pick Y Axis"))
        # self.initComboBox(self.YcomboBox)
        # self.XcomboBox = QComboBox(self)
        # self.XcomboBox.setGeometry(QRect(40, 40, 491, 31))
        # self.XcomboBox.setObjectName(("Pick X Axis"))
        # self.initComboBox(self.XcomboBox)

        # functionality
        # connects all the buttons/labels to their associated functions
        self.btn.clicked.connect(lambda _: self.plotData())
        self.stop.clicked.connect(lambda _: self.stopData())
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
        self.autoscale_X.clicked.connect(lambda _: self.setAutoscale(0)) # CHANGED_HERE, TODO should we change this to a toggle?
        self.autoscale_Y.clicked.connect(lambda _: self.setAutoscale(1)) # CHANGED_HERE, TODO should we change this to a toggle?
        self.windowRange_text.textEdited.connect(self.setWindowRange) # CHANGED_HERE connects Qline to function call
        self.chnl1_button.clicked.connect(lambda _: self.toggleChannels())
        self.chnl2_button.clicked.connect(lambda _: self.toggleChannels())
        self.chnl3_button.clicked.connect(lambda _: self.toggleChannels())
        self.chnl4_button.clicked.connect(lambda _: self.toggleChannels())
        self.channel_buttons = { 1:self.chnl1_button, # put all chnl buttons in a dict table for easier looping and access
                                 2:self.chnl2_button,
                                 3:self.chnl3_button,
                                 4:self.chnl4_button  }
        self.x_axis_ComboBox.activated.connect(lambda _: self.change_x_axis())
        self.scatter_chkbox.stateChanged.connect(lambda _: self.togglePlotStyle())
        self.line_chkbox.stateChanged.connect(lambda _: self.togglePlotStyle())

        # pyqt graph init
        self.plotWidget = pg.PlotWidget() # create the widget for viewing

        # layout init
        self.vbox = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)

        # adding the widgets to the layout
        #self.grid_layout.addWidget(CustomLineEdit("hwllo"),4,0,1,8)
        #self.grid_layout.addWidget(self.YcomboBox, 0, 0, -1, 2)
        #self.grid_layout.addWidget(self.XcomboBox, 0, 1, -1, 2)
        self.grid_layout.addWidget(self.Ytext_QLabel, 0, 0, 1, 2)
        self.grid_layout.addWidget(self.Ytext, 0, 2, 1, 10)
        self.grid_layout.addWidget(self.Xtext_QLabel, 0, 12, 1, 2)
        self.grid_layout.addWidget(self.Xtext, 0, 14, 1, 10)
        self.grid_layout.addWidget(self.btn, 0, 24)
        self.grid_layout.addWidget(self.stop, 0, 25)

        self.grid_layout.addWidget(self.YLimits_QLabel, 1, 0, 1, 2)
        self.grid_layout.addWidget(self.Y_lower_text, 1, 2, 1, 5)
        self.grid_layout.addWidget(self.Y_upper_text, 1, 7, 1, 5)
        self.grid_layout.addWidget(self.x_axis_ComboBox_QLabel, 1, 12, 1, 2)
        self.grid_layout.addWidget(self.x_axis_ComboBox, 1, 14, 1, 10)
        self.grid_layout.addWidget(self.clear, 1, 24)
        self.grid_layout.addWidget(self.save, 1, 25)

        self.grid_layout.addWidget(self.windowRange_QLabel, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.windowRange_text, 2, 2, 1, 10)
        self.grid_layout.addWidget(self.XLimits_QLabel, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.X_lower_text, 2, 2, 1, 5)
        self.grid_layout.addWidget(self.X_upper_text, 2, 7, 1, 5)
        self.grid_layout.addWidget(self.autoscale_Y, 2, 24) #
        self.grid_layout.addWidget(self.autoscale_X, 2, 25) #

        self.grid_layout.addWidget(self.chnl1_button,3,0,1,6)
        self.grid_layout.addWidget(self.chnl2_button,3,6,1,6)
        self.grid_layout.addWidget(self.chnl3_button,3,12,1,6)
        self.grid_layout.addWidget(self.chnl4_button,3,18,1,6)
        self.grid_layout.addWidget(self.line_chkbox, 3, 24)
        self.grid_layout.addWidget(self.scatter_chkbox, 3, 25)

        self.vbox.addLayout(self.grid_layout)
        self.vbox.addWidget(self.plotWidget)

        # plotting variables
        self.subscription = None
        self.currentlyPlotting = False
        self.data = np.array([])
        self.x_axis_data = np.array([])
        self.current_time = None
        self.traces = []
        self.channels = [True, False, False, False] # default channel selection
        self.x_axis_selection = 0 # indicates which channel {1,2,3,4} is x-axis. 0 indicates time.
        self.legend = None
        # self.ptr = 0

        # application showing
        self.setLayout(self.vbox)
        self.setGeometry(300, 300, 1468, 1468)
        self.windowWidth = 768
        self.setWindowTitle("Plotter")
        self.setTitle()
        self.setXLabel()
        self.setYLabel()
        self.plotWidget.setXRange(0,self.windowRange) # CHANGED_HERE : initial window from 0 to XRange.
        self.show()

    def togglePlotStyle(self, line=None, scatter=None):
        if (line == None and scatter == None): # if this was called through user checkbox, fetch values
            line = self.line_chkbox.isChecked()
            scatter = self.scatter_chkbox.isChecked()
        if (self.currentlyPlotting):
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

    def change_x_axis(self):
        self.x_axis_selection = self.x_axis_ComboBox.currentIndex()
        if (self.x_axis_selection != 0):
            self.autoscale_X.setChecked(True)
            self.autoscale_Y.setChecked(True)
            self.setAutoscale() # update autoscaling
            self.windowRange_QLabel.setVisible(False)
            self.windowRange_text.setVisible(False)
            self.XLimits_QLabel.setVisible(True)
            self.X_lower_text.setVisible(True)
            self.X_upper_text.setVisible(True)
        else:
            self.autoscale_X.setChecked(False)
            self.autoscale_Y.setChecked(True)
            self.setAutoscale() # update autoscaling
            self.XLimits_QLabel.setVisible(False)
            self.X_lower_text.setVisible(False)
            self.X_upper_text.setVisible(False)
            self.windowRange_QLabel.setVisible(True)
            self.windowRange_text.setVisible(True)
        if (self.currentlyPlotting):
            self.stopData()
            self.clearData()
            self.plotData()

    def toggleChannels(self):
        self.channels = [self.chnl1_button.isChecked(),
                         self.chnl2_button.isChecked(),
                         self.chnl3_button.isChecked(),
                         self.chnl4_button.isChecked()]
        if (self.currentlyPlotting):
            self.stopData()
            self.clearData()
            if (sum(self.channels) > 0):
                self.plotData()
            else:
                self.messageBox("No channels selected. Plotting has been stopped.")

    def setYRange(self): #CHANGED_HERE
        try:
            self.Y_lower = float(self.Y_lower_text.text())
            self.Y_upper = float(self.Y_upper_text.text())
            self.plotWidget.setYRange(self.Y_lower, self.Y_upper)
            self.plotWidget.enableAutoRange(axis=1, enable=False)
            self.autoscale_Y.setChecked(False)
        except:
            self.Y_lower = None
            self.Y_upper = None

    def setXRange(self): #CHANGED_HERE
        try:
            self.X_lower = float(self.X_lower_text.text())
            self.X_upper = float(self.X_upper_text.text())
            self.plotWidget.setXRange(self.X_lower, self.X_upper)
            self.plotWidget.enableAutoRange(axis=0, enable=False)
            self.autoscale_X.setChecked(False)
        except:
            self.Y_lower = None
            self.Y_upper = None


    def setWindowRange(self): ## CHANGED_HERE : function to connect to GUI. allows user to change window size
        try:
            self.windowRange = float(self.windowRange_text.text()) # CHANGED_HERE: retrieves value from user box. TODO: proof against invalid values eg. letters
            print("Setting window range to " + str(self.windowRange))
            self.plotWidget.setXRange(0, self.windowRange)
            #self.X_autoscale = False
        except:
            pass

    def setAutoscale(self, axis=None): #CHANGED_HERE
        if (axis == 0 or axis == 1): # if axis is specified, change only for that
            if (axis == 0):
                enable = self.autoscale_X.isChecked()
            else:
                enable = self.autoscale_Y.isChecked()
            self.plotWidget.enableAutoRange(axis=axis, enable=enable)
            if (enable == False and axis == 0):
                self.plotWidget.setXRange(0, self.windowRange)
        else: # else, change for both based on button status
            self.plotWidget.enableAutoRange(axis=0, enable=self.autoscale_X.isChecked())
            if (not self.autoscale_X.isChecked()):
                self.plotWidget.setXRange(0, self.windowRange)
            self.plotWidget.enableAutoRange(axis=1, enable=self.autoscale_Y.isChecked())
        #self.X_autoscale = True if axis==0 else self.X_autoscale


    # obsolete function, can be taken out
    # def initComboBox(self, box):
    #     """initComboBox

    #     :param box: box reference to give values to
    #     """
    #     items = ["channel {}".format(i + 1) for i in range(4)]
    #     for name in items:
    #         box.addItem(name)

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
        # If not plotting, but there is already data on the plot,
        # first clear, and then starting plotting again
        if self.data is not None and self.data.size != 0:
            self.clearData()
        # if more than 1 channel is selected, add a legend
        if (sum(self.channels) > 0) :
            self.legend = self.plotWidget.addLegend()
        # set that we are plotting
        self.currentlyPlotting = True
        # if we have not yet grabbed the observer from the backend, get it
        if not self.observer:
            self.getObserver()
        # if we have not yet subscribed to the observer, or if we stopped
        # subscribing to the observer, subscribe to it
        if not self.subscription:
            # depending on the current rx version, try different versions 
            # of subscribe since the older versions use subscribe_()
            try:
                self.subscription = self.observer.subscribe_(lambda x: self.
                                                            addData(x))
            except:
                self.subscription = self.observer.subscribe(lambda x: self.
                                                            addData(x))
        # this is the function that starts the data collection in the backend
        # the on variable starts and stops data observation in the backend
        # prod=boolean is a variable that sets whether we retrieve test/actual
        # values
        self.data_rpc.getData_test(on=True, prod=False, channels=self.channels, x_axis=self.x_axis_selection)

    def addData(self, newData):
        """addData
        Adds a single data point to a trace
        :param newData: single new data point to add
        """
        # get the time window of the incoming data
        new_x_data = newData.pop()
        # refactor the new incoming data
        fixedNewData = np.array([i for i in newData])
        # if we are at the start of plotting
        if self.data.size == 0:
            self.data = np.zeros_like(fixedNewData)
            self.data += fixedNewData
            self.x_axis_data = np.zeros(1)
            if (self.x_axis_selection == 0): # if time is the x_axis
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
            if (self.x_axis_selection == 0): # if time is the x_axis
                self.current_time = new_x_data - self.start # update time position of next incoming data
                self.x_axis_data = np.append(self.x_axis_data, self.current_time)
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
                        x=self.x_axis_data,
                        y=self.data[index],
                        pen= colours[index] if self.line_chkbox.isChecked() else None,
                        symbol='o' if self.scatter_chkbox.isChecked() else None,
                        symbolBrush= colours[index] if self.scatter_chkbox.isChecked() else None,
                        symbolSize=5,
                        name=channel_names[i])  # name=i
                    index += 1
                    self.traces.append(plot)
        # The traces already exist. Add the new data to each of the already
        # existing traces
        else:
            for i in range(len(self.data)):
                self.traces[i].setData(x=self.x_axis_data,
                                       y=self.data[i])
                if (self.x_axis_selection != 0       # if plotting against channel instead of time
                        or self.current_time < self.windowRange # or if plotting against time and it still fits witin window
                        or self.autoscale_X.isChecked()):  # or if autoscaling is on
                    self.traces[i].setPos(0,0)           # set position of plot to 0
                else : # CHANGED_HERE. else, we just clip the plotItem accordingly
                    self.traces[i].setPos(-self.current_time+self.windowRange,0) # CHANGED_HERE setPos of each plotItem
            # this is necessary for data smoothly being added/removed from plot
            QtGui.QApplication.processEvents()

    def stopData(self):
        """stopData
        Stops data collection in general.
        The data arrays are still filled
        """

        # a boolean for keeping track if we are currently plotting
        # we set it false as we are stopping plotting
        self.currentlyPlotting = False

        # if there is not a subscription, data wasn't being plotted anyways
        if not self.subscription:
            self.messageBox("No data is being plotted")
        # there is a subscription that we mean to stop.
        # The subscription is destroyed and we tell the backend to stop
        # plotting by using the toggleListening(on=boolean) function
        else:
            self.subscription.dispose()
            self.subscription = None
            self.data_rpc.toggleListening(on=self.currentlyPlotting)
            QtGui.QApplication.processEvents()

    def clearData(self):
        """clearData
        Clears the plot of all traces
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
        Saves the data in csv format
        """
        self.exportToCSV()
        if not self.currentlyPlotting and self.data.size != 0:
            currentDT = datetime.datetime.now()
            defaultname = currentDT.strftime("plot_%Y-%m-%d_%H-%M-%S")
            (filename,ok)=QInputDialog.getText(self,"Export to CSV","Filename (without .csv):                  ",
                                                QLineEdit.Normal,defaultname)
            if (not ok): # if user clicked cancel, stop saving
                return
            filename += '.csv'
            exporter = pg_e.CSVExporter(self.plotWidget.plotItem)
            exporter.export(fileName=filename)
            self.messageBox('Data saved to ' + filename)
        else:
            self.messageBox(
                "Make sure you aren't plotting, or there is no data")

    def exportToCSV(self):
        print(self.data.shape)
        num_channels, n = self.data.shape

        # data_csv = ""
        print(self.data[0])
        for i in range(n):
            pass


###############################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    plotter = Plotter()
    # only exit when the exec_ function is called
    sys.exit(app.exec_())
