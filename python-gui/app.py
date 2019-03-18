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

# import threading
# import zerorpc
###############################################################################

mapping = {
    'button': QPushButton,
    'dropdown': QComboBox,
    'text': QLineEdit,
    'plot': pg.PlotWidget
}

###############################################################################


class thread_runner(object):
    """thread_runner"""

    def __init__(self):
        """__init__"""
        # self.data_rpc = dataRPC()
        # self.thread = threading.Thread(target=self.init_daemon, args=())
        # self.thread.daemon = True
        # self.thread.start()

    def get_rpc(self):
        """get_rpc"""
        # if not self.data_rpc:
        # self.data_rpc = dataRPC()

    def init_daemon(self):
        """init_daemon"""
        # if not self.data_rpc:
        # self.get_rpc()
        # s = zerorpc.Server(self.data_rpc)
        # s.bind("tcp://0.0.0.0:4242")
        # s.run()
        # sys.stdout.flush()


###############################################################################
class Plotter(QWidget):
    """Plotter"""

    def __init__(self):
        """__init__"""
        # application init
        super().__init__()
        # self.initThread()
        self.data_rpc = dataRPC()
        self.observer = None
        self.init_UI()

    def initThread(self):
        """initThread"""
        # self.thread = thread_runner()
        # zerorpc setup
        # self.c = zerorpc.Client()
        # self.c.connect("tcp://0.0.0.0:4242")
        # self.observer = None
        pass

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
        # self.clear = QPushButton("Clear Plot", self)
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

        self.btn.setStyleSheet(
            'QPushButton {background-color: #A3C1DA; color: blue;}')
        self.stop.setStyleSheet(
            'QPushButton {background-color: #A3C1DA; color: red;}')

        # combobox init
        self.YcomboBox = QComboBox(self)
        self.YcomboBox.setGeometry(QRect(40, 40, 491, 31))
        self.YcomboBox.setObjectName(("Pick Y Axis"))
        self.initComboBox(self.YcomboBox)
        self.XcomboBox = QComboBox(self)
        self.XcomboBox.setGeometry(QRect(40, 40, 491, 31))
        self.XcomboBox.setObjectName(("Pick X Axis"))
        self.initComboBox(self.XcomboBox)

        # functionality
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
        # self.grid_layout.addWidget(self.plot, 2, 0)
        # self.grid_layout.setRowStretch(0, 2)

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
        xtext = self.Xtext.text()
        ytext = self.Ytext.text()
        self.plotWidget.setTitle("""
                                 <h1>{0} vs {1}</h1>
                                 """.format(ytext, xtext))

    def setXLabel(self):
        xtext = self.Xtext.text()
        html = """
            <style>{0}</style>
            <i class='label'>{1}</i>
        """.format(styles['label'], xtext)
        self.plotWidget.setLabel('bottom', text=html)

    def setYLabel(self):
        ytext = self.Ytext.text()
        html = """
            <style>{0}</style>
            <i class='label'>{1}</i>
        """.format(styles['label'], ytext)
        self.plotWidget.setLabel('left', text=html)

    def getObserver(self):
        """getObserver"""
        if not self.observer:
            self.data_rpc.activateStream()
            self.observer = self.data_rpc.getStream()

    def plotData(self):
        """plotData"""
        if self.currentlyPlotting:
            print("Already plotting")
            return
        if self.data is not None and self.data.size != 0:
            self.clearData()
        self.legend = self.plotWidget.addLegend()
        self.currentlyPlotting = True
        self.ww = 0
        if not self.observer:
            self.getObserver()
        if not self.subscription:
            self.subscription = self.observer.subscribe_(
                lambda x: self.addData(x))
        self.data_rpc.getData_test(on=True)

    def addData(self, newData):
        """addData
        Adds a single data point to a trace
        :param newData: single new data point to add
        """
        # to make the plot as a while move left
        # might take this out
        # self.ww -= 1
        fixedNewData = np.array([i for i in newData])
        if self.data.size == 0:
            self.data = np.zeros_like(fixedNewData)
            self.data += fixedNewData
            starting = True
        else:
            # self.ptr += 1
            self.data = np.concatenate((self.data, fixedNewData), axis=1)
            starting = False
        # self.data = np.append(self.data, newData[0])
        # if self.data[0].size == 1:
        if starting:
            for i in range(len(self.data)):
                plot = self.plotWidget.plot(
                    self.data[i], pen=(i, self.data.size))  # name=i
                self.traces.append(plot)
        else:
            for i in range(len(self.data)):
                self.traces[i].setData(self.data[i])
                # self.traces[i].setPos(-self.ptr, 0)
            # this is what repositions the plot
            # self.plot.setPos(self.ww, 0)
            QtGui.QApplication.processEvents()

    def stopData(self):
        """stopData
        Stops data collection in general.
        The data arrays are still filled
        """

        # a boolean for keeping track if we are currently plotting
        self.currentlyPlotting = False
        if not self.subscription:
            print("No data is being plotted")
        else:
            self.subscription.dispose()
            self.subscription = None
            self.data_rpc.toggleListening(on=self.currentlyPlotting)
            QtGui.QApplication.processEvents()

    def resumeData(self):
        if not self.subscription:
            print("No data is being plotted")
        else:
            self.currentlyPlotting = True
            self.data_rpc.toggleListening(on=self.currentlyPlotting)

    def clearData(self):
        """clearData
        Clears the plot of all traces
        """
        if self.subscription is not None:
            print("Stop plotting before you clear")
            self.messageBox("Stop plotting before you clear")
            return
        print(self.data.size)
        if self.data.size == 0:
            print("No data has been plotted")
        else:
            # self.ptr = 0
            self.legend.scene().removeItem(self.legend)
            for i in range(len(self.data)):
                print(self.traces[i])
                self.traces[i].clear()
            self.data = np.array([])
            # self.ww = 0
            # self.plot.setPos(self.ww, 0)

    def saveData(self):
        """saveData
        Saves the data in csv format
        """
        if not self.currentlyPlotting and self.data.size != 0:
            exporter = pg_e.CSVExporter(self.plotWidget.plotItem)
            exporter.export(fileName='data.csv')
            self.messageBox('Data saved to data.csv')


###############################################################################

if __name__ == '__main__':
    app = QApplication(sys.argv)
    plotter = Plotter()
    # only exit when the exec_ function is called
    sys.exit(app.exec_())
