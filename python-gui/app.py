###############################################################################
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, \
    QVBoxLayout, QPushButton, QLineEdit, QComboBox, QMessageBox
from PyQt5.QtCore import QRect  # pyqtSlot
import pyqtgraph as pg
import pyqtgraph.exporters as pg_e
from pyqtgraph.Qt import QtGui
import numpy as np
from styles import styles
from data import dataRPC

###############################################################################

# mapping created for string to pyqt widget class
# used in a creator function below -> widgetCreator
mapping = {
    'button': QPushButton,
    'dropdown': QComboBox,
    'text': QLineEdit,
    'plot': pg.PlotWidget
}


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

        self.Xtext = QLineEdit("Label for x-axis", self)
        self.Ytext = QLineEdit("Label for y-axis", self)

        # combobox init: For choosing the channels
        self.YcomboBox = QComboBox(self)
        self.YcomboBox.setGeometry(QRect(40, 40, 491, 31))
        self.YcomboBox.setObjectName(("Pick Y Axis"))
        self.initComboBox(self.YcomboBox)
        self.XcomboBox = QComboBox(self)
        self.XcomboBox.setGeometry(QRect(40, 40, 491, 31))
        self.XcomboBox.setObjectName(("Pick X Axis"))
        self.initComboBox(self.XcomboBox)

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

        # pyqt graph init
        self.plotWidget = pg.PlotWidget()

        # layout init
        self.vbox = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)

        # adding the widgets to the layout
        self.grid_layout.addWidget(self.YcomboBox, 0, 0)
        self.grid_layout.addWidget(self.XcomboBox, 0, 1)
        self.grid_layout.addWidget(self.btn, 0, 2)
        self.grid_layout.addWidget(self.stop, 0, 3)
        self.grid_layout.addWidget(self.Ytext, 1, 0)
        self.grid_layout.addWidget(self.Xtext, 1, 1)
        self.grid_layout.addWidget(self.clear, 1, 2)
        self.grid_layout.addWidget(self.save, 1, 3)

        self.vbox.addLayout(self.grid_layout)
        self.vbox.addWidget(self.plotWidget)

        # plotting variables
        self.subscription = None
        self.currentlyPlotting = False
        self.data = np.array([])
        self.traces = []
        # self.ptr = 0

        # application showing
        self.setLayout(self.vbox)
        self.setGeometry(300, 300, 1468, 1468)
        self.windowWidth = 768
        self.setWindowTitle("Plotter")
        self.setTitle()
        self.setXLabel()
        self.setYLabel()
        self.show()

    def initComboBox(self, box):
        """initComboBox

        :param box: box reference to give values to
        """
        items = ["channel {}".format(i + 1) for i in range(4)]
        for name in items:
            box.addItem(name)

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
        if self.currentlyPlotting:
            self.messageBox("Already Plotting")
            return
        # If not plotting, but there is already data on the plot,
        # first clear, and then starting plotting again
        if self.data is not None and self.data.size != 0:
            self.clearData()
        # I need to figure out how to not make the legend mess up the data
        # saving. So removed for now
        # self.legend = self.plotWidget.addLegend()

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
        self.data_rpc.getData_test(on=True, prod=False)

    def addData(self, newData):
        """addData
        Adds a single data point to a trace
        :param newData: single new data point to add
        """
        # refactor the new incoming data
        fixedNewData = np.array([i for i in newData])
        # if we are at the start of plotting
        if self.data.size == 0:
            self.data = np.zeros_like(fixedNewData)
            self.data += fixedNewData

            # this is the first time adding data
            starting = True
        # data already exists, concatenate it
        else:
            # self.ptr += 1
            self.data = np.concatenate((self.data, fixedNewData), axis=1)

            # there is already data
            starting = False
        # Since we are just starting, we create new traces for each channel
        # and add the first set of datapoints to those traces
        if starting:
            for i in range(len(self.data)):
                plot = self.plotWidget.plot(
                    self.data[i], pen=(i, self.data.size),
                    name=str(i))  # name=i
                self.traces.append(plot)
        # The traces already exist. Add the new data to each of the already
        # existing traces
        else:
            for i in range(len(self.data)):
                self.traces[i].setData(self.data[i])
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
            # self.legend.scene().removeItem(self.legend)
            for i in range(len(self.data)):
                print(self.traces[i])
                self.traces[i].clear()
            self.traces = []
            # self.plotWidget.clear()
            self.data = np.array([])

    def saveData(self):
        """saveData
        Saves the data in csv format
        """
        self.exportToCSV()
        if not self.currentlyPlotting and self.data.size != 0:
            exporter = pg_e.CSVExporter(self.plotWidget.plotItem)
            exporter.export(fileName='data.csv')
            self.messageBox('Data saved to data.csv')
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
