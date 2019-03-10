# Thought Process when designing the UI

This is a cool article that discusses usefull points about
the size of widgets and UI components [https://blog.prototypr.io/smart-ui-dimensions-for-any-screen-size-cc532f92c2f8](https://blog.prototypr.io/smart-ui-dimensions-for-any-screen-size-cc532f92c2f8). It takes what it has learned from Google's Material Design Philosophy.

## Exporter Code
```python
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from Exporter import Exporter
from pyqtgraph.parametertree import Parameter


__all__ = ['CSVExporter']
    
    
class CSVExporter(Exporter):
    Name = "CSV from plot data"
    windows = []
    def __init__(self, item):
        Exporter.__init__(self, item)
        self.params = Parameter(name='params', type='group', children=[
            {'name': 'separator', 'type': 'list', 'value': 'comma', 'values': ['comma', 'tab']},
        ])
        
    def parameters(self):
        return self.params
    
    def export(self, fileName=None):
        
        if not isinstance(self.item, pg.PlotItem):
            raise Exception("Matplotlib export currently only works with plot items")
        
        if fileName is None:
            self.fileSaveDialog(filter=["*.csv", "*.tsv"])
            return

        fd = open(fileName, 'w')
        data = []
        header = []
        for c in self.item.curves:
            data.append(c.getData())
            header.extend(['x', 'y'])

        if self.params['separator'] == 'comma':
            sep = ','
        else:
            sep = '\t'
            
        fd.write(sep.join(header) + '\n')
        i = 0
        while True:
            done = True
            for d in data:
                if i < len(d[0]):
                    fd.write('%g%s%g%s'%(d[0][i], sep, d[1][i], sep))
                    done = False
                else:
                    fd.write(' %s %s' % (sep, sep))
            fd.write('\n')
            if done:
                break
            i += 1
        fd.close()
```

## Scrolling Plot Example

```python
# -*- coding: utf-8 -*-
"""
Various methods of drawing scrolling plots.
"""
import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

win = pg.GraphicsWindow()
win.setWindowTitle('pyqtgraph example: Scrolling Plots')


# 1) Simplest approach -- update data in the array such that plot appears to scroll
#    In these examples, the array size is fixed.
p1 = win.addPlot()
p2 = win.addPlot()
data1 = np.random.normal(size=300)
curve1 = p1.plot(data1)
curve2 = p2.plot(data1)
ptr1 = 0
def update1():
    global data1, curve1, ptr1
    data1[:-1] = data1[1:]  # shift data in the array one sample left
                            # (see also: np.roll)
    data1[-1] = np.random.normal()
    curve1.setData(data1)
    
    ptr1 += 1
    curve2.setData(data1)
    curve2.setPos(ptr1, 0)
    

# 2) Allow data to accumulate. In these examples, the array doubles in length
#    whenever it is full. 
win.nextRow()
p3 = win.addPlot()
p4 = win.addPlot()
# Use automatic downsampling and clipping to reduce the drawing load
p3.setDownsampling(mode='peak')
p4.setDownsampling(mode='peak')
p3.setClipToView(True)
p4.setClipToView(True)
p3.setRange(xRange=[-100, 0])
p3.setLimits(xMax=0)
curve3 = p3.plot()
curve4 = p4.plot()

data3 = np.empty(100)
ptr3 = 0

def update2():
    global data3, ptr3
    data3[ptr3] = np.random.normal()
    ptr3 += 1
    if ptr3 >= data3.shape[0]:
        tmp = data3
        data3 = np.empty(data3.shape[0] * 2)
        data3[:tmp.shape[0]] = tmp
    curve3.setData(data3[:ptr3])
    curve3.setPos(-ptr3, 0)
    curve4.setData(data3[:ptr3])


# 3) Plot in chunks, adding one new plot curve for every 100 samples
chunkSize = 100
# Remove chunks after we have 10
maxChunks = 10
startTime = pg.ptime.time()
win.nextRow()
p5 = win.addPlot(colspan=2)
p5.setLabel('bottom', 'Time', 's')
p5.setXRange(-10, 0)
curves = []
data5 = np.empty((chunkSize+1,2))
ptr5 = 0

def update3():
    global p5, data5, ptr5, curves
    now = pg.ptime.time()
    for c in curves:
        c.setPos(-(now-startTime), 0)
    
    i = ptr5 % chunkSize
    if i == 0:
        curve = p5.plot()
        curves.append(curve)
        last = data5[-1]
        data5 = np.empty((chunkSize+1,2))        
        data5[0] = last
        while len(curves) > maxChunks:
            c = curves.pop(0)
            p5.removeItem(c)
    else:
        curve = curves[-1]
    data5[i+1,0] = now - startTime
    data5[i+1,1] = np.random.normal()
    curve.setData(x=data5[:i+2, 0], y=data5[:i+2, 1])
    ptr5 += 1


# update all plots
def update():
    update1()
    update2()
    update3()
timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)



# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
```

## Setting text and styles for widgets
```python
button = QtGui.QPushButton()
button.setStyleSheet('QPushButton {background-color: #A3C1DA; color: red;}')
button.setText('Press Me')
```

Check out this link for supposed real-time plotting [https://github.com/guillaumegenthial/streamplot/blob/master/streamplot.py](https://github.com/guillaumegenthial/streamplot/blob/master/streamplot.py).

NIDAQMX driver in Larry Box
DAQMX python google
