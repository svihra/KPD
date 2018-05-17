import sys, os, random

import serial

import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from time import sleep

device = "/dev/ttyUSB0"
bps    = 9600

class SliderBox(QGroupBox):
    value_changed = pyqtSignal(int)
    
    @pyqtSlot(int)
    def send_value(self, index):
        self.value_changed.emit(index)
        self.label.setNum(index)
        
    @pyqtSlot(int,int)
    def set_range(self, minVal, maxVal):
        self.slider.setRange(minVal, maxVal)
    
    def set_value(self,val):
        self.slider.setValue(val)
    
    def __init__(self, name, minVal, maxVal, val, parent=None):
        QGroupBox.__init__(self, parent)
        self.setTitle(name)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(minVal, maxVal)
        self.slider.setValue(val)
        
        self.label = QLabel()
        self.label.setNum(val)
        
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        
        self.connect(self.slider, SIGNAL('valueChanged(int)'), self.send_value)
        
class ArduinoThread(QThread):
    value = pyqtSignal('PyQt_PyObject','PyQt_PyObject')
    text = pyqtSignal('QString')
    count = pyqtSignal(int)
    finished = pyqtSignal()
    
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.restart()
        self.arduino = serial.Serial(device,bps)

    
    @pyqtSlot()
    def reset(self):
        self.counter = 0
        
    def isint(self,value):
        try:
            int(value)
            return True
        except:
            return False
        
    def convert(self, arr, res):
        if (len(arr) == 1024):
            self.text.emit("reading data")
            index = 0
            while index < len(arr):
                if self.isint(arr[index]):
                    res[index] = res[index] + int(arr[index])
                index = index + 1
        return res

    @pyqtSlot()
    def stop_thread(self):
        self.active = False
        self.text.emit("stopped")
    
    @pyqtSlot()
    def restart(self):
        self.result = np.zeros(1024)
        self.resultRaw = np.zeros(1024)
        self.counter = 0
        self.active = True
        
    @pyqtSlot()
    def run(self):
        while self.active:
            self.text.emit("reading intro for frame " + str(self.counter))
            self.data = self.arduino.readline()[:-3]
            if (len(self.data) == 0):
                self.data = self.arduino.readline()[:-3]
                self.converted = self.data.split(",")
                self.result = self.convert(self.converted, self.result)
                
                self.data = self.arduino.readline()[:-3]
                self.converted = self.data.split(",")
                self.resultRaw = self.convert(self.converted, self.resultRaw)
                
                self.value.emit(self.result, self.resultRaw)
                self.text.emit("sending all data")
                self.counter = self.counter + 1
                self.count.emit(self.counter)
            
    def finish(self):
        self.finished.emit()

class AppForm(QMainWindow):
    change_bins = pyqtSignal(int,int)
    reset = pyqtSignal()
    stop_run = pyqtSignal()
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Spectrogram')
        
        #self.mu, self.sigma = 100, 15
        self.bins = 100
        self.disc = 0
        self.maxCount = 100000
        self.count = 0
        self.process_data = True
        self.counter = 0
        
        self.data = np.zeros(1024)
        self.dataRaw = np.zeros(1024)
        self.channels = np.arange(1024)
        
        self.minVal = 250
        self.maxVal = 320

        # init window
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
        # init data taking
        self.arduino = ArduinoThread(self)
        self.connect(self.arduino,SIGNAL('value(PyQt_PyObject,PyQt_PyObject)'),self.get_data)
        self.connect(self.arduino,SIGNAL('text(QString)'),self.printer)
        self.connect(self.arduino,SIGNAL('count(int)'),self.set_title)
        self.connect(self,SIGNAL('stop_run()'),self.arduino.stop_thread)
        
        self.on_draw()
        
    def __exit__(self, exc_type, exc_value, traceback):
        print("exiting")
        
    def save_plot(self):
        file_choices = "TXT (*.txt);;PNG (*.png)|*.png"
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path.endswith('.png'):
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 1023)
        else:
            np.savetxt(path,np.c_[self.data, self.dataRaw], fmt='%d')

    def load_plot(self):
        file_choices = "TXT (*.txt)"
        
        path = unicode(QFileDialog.getOpenFileName(self, 
                        'Load file', '', 
                        file_choices))
        self.data, self.dataRaw = np.loadtxt(path, delimiter=' ',dtype = int, unpack=True)
        self.on_draw()
            
    @pyqtSlot('QString')
    def printer(self,text):
        print(text)
        
    @pyqtSlot(int)
    def set_title(self,value):
        self.counter = value
    
    @pyqtSlot('PyQt_PyObject','PyQt_PyObject')
    def get_data(self,data,dataRaw):
        self.data = data
        self.dataRaw = dataRaw
        
        self.on_draw()
    
    def on_draw(self):
        """ Redraws the figure """        
        self.axes.clear()
        self.axes.grid(self.grid_cb.isChecked())
        
        ymin = 0
        if self.logy_cb.isChecked():
            self.axes.semilogy(self.channels,self.data, label='filtered')
            if self.raw_cb.isChecked():
                self.axes.semilogy(self.channels,self.dataRaw, label='raw')
            ymin = 1
        else:
            self.axes.plot(self.channels,self.data, label='filtered')
            if self.raw_cb.isChecked():
                self.axes.plot(self.channels,self.dataRaw, label='raw')
            
        self.axes.set_xlim(self.minVal, self.maxVal)
        if self.raw_cb.isChecked():
            self.axes.set_ylim(ymin,np.amax(self.dataRaw[self.minVal:self.maxVal]))
        else:
            self.axes.set_ylim(ymin,np.amax(self.data[self.minVal:self.maxVal]))
            
        self.legend = self.axes.legend(loc='upper right')
        self.axes.set_title("Run " + str(self.counter))
        
        self.canvas.draw()
        
    def set_range_min(self, minVal):
        if minVal > self.maxVal:
            self.slider_min.set_value(self.maxVal)
        else:
            self.slider_max.set_range(minVal,1023)
            self.minVal = minVal
            
        self.on_draw()
        
    def set_range_max(self, maxVal):
        if maxVal < self.minVal:
            self.slider_max.set_value(self.minVal)
        else:
            self.slider_min.set_range(0,maxVal)
            self.maxVal = maxVal
            
        self.on_draw()
        
    def restart_acqui(self):
        print("Restarting the run")
        self.status_text.setText("Continually receiving data")

        self.button_acqui.setText("Restart")
        self.arduino.restart()
        self.arduino.start()

    @pyqtSlot()
    def stop_acqui(self):
        print("Stopping the run")
        self.status_text.setText("Waiting for start")

        self.button_acqui.setText("Start")
        self.stop_run.emit()

    @pyqtSlot()
    def exit(self):
        print("Exitting")
        self.stop_acqui()
        self.close()
    
    def create_main_frame(self):
        self.main_frame = QWidget()
        
        self.dpi = 100
        self.fig = Figure((10.0, 10.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        self.axes = self.fig.add_subplot(111)
                
        # GUI controls
        #         
        self.button_acqui = QPushButton("&Start")
        start_shortcut = QShortcut(self)
        start_shortcut.setKey("Ctrl+R")
        self.connect(start_shortcut, SIGNAL("activated()"), self.restart_acqui)
        self.connect(self.button_acqui, SIGNAL('clicked()'), self.restart_acqui)
        
        self.button_stop = QPushButton("&Stop")
        stop_shortcut = QShortcut(self)
        stop_shortcut.setKey("Ctrl+D")
        self.connect(stop_shortcut, SIGNAL("activated()"), self.stop_acqui)
        self.connect(self.button_stop, SIGNAL('clicked()'), self.stop_acqui)

        self.raw_cb = QCheckBox("Toggle raw")
        self.raw_cb.setChecked(True)
        self.connect(self.raw_cb, SIGNAL('stateChanged(int)'), self.on_draw)

        self.grid_cb = QCheckBox("Toggle grid")
        self.grid_cb.setChecked(False)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.on_draw)

        self.logy_cb = QCheckBox("Toggle logy")
        self.logy_cb.setChecked(False)
        self.connect(self.logy_cb, SIGNAL('stateChanged(int)'), self.on_draw)

        self.slider_min = SliderBox("Min Value", 0, 1023, self.minVal)
        self.connect(self.slider_min, SIGNAL('value_changed(int)'), self.set_range_min)

        self.slider_max = SliderBox("Max Value", 0, 1023, self.maxVal)
        self.connect(self.slider_max, SIGNAL('value_changed(int)'), self.set_range_max)

        #
        # Layout with box sizers
        # 
        hbox = QHBoxLayout()
        acqbox = QHBoxLayout()
        
        for w in [ self.slider_min, self.slider_max, self.logy_cb, self.raw_cb, self.grid_cb]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)

        for w in [ self.button_acqui, self.button_stop]:
            acqbox.addWidget(w)
            acqbox.setAlignment(w, Qt.AlignVCenter)
        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addLayout(acqbox)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
    
    def create_status_bar(self):
        self.status_text = QLabel("Waiting for start")
        self.statusBar().addWidget(self.status_text, 1)
        
    def create_menu(self):        
        self.file_menu = self.menuBar().addMenu("&File")
        
        save_file_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot, 
            tip="Save the plot")
        load_file_action = self.create_action("&Load plot",
            shortcut="Ctrl+L", slot=self.load_plot, 
            tip="Load the plot")

        quit_action = self.create_action("&Quit", slot=self.exit, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, 
            (save_file_action, load_file_action, None, quit_action))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


def main():
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance() 
    form = AppForm()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()