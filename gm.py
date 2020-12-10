"""This scripts wraps-up the GMYC commandline codes in the form of pyQt5-GUI application"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import re
import sys, os
from PyQt5.uic import loadUiType
from GMYC import *
import GMYC
import pyr8s.parse
from pyr8s.qt.utility import UProcess, URunnable
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import *

import multiprocessing
import timeit

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

FORM_CLASS, _= loadUiType(resource_path("GM.ui"))  # use ui reference to load the widgets

class Main(QMainWindow, FORM_CLASS):    # create class instance
    def __init__(self):
        super(Main, self).__init__()
        self.setWindowIcon(QIcon(resource_path('icons/GMYC_icon.ico')))
        self.setupUi(self)
        self.Handel_Buttons()  # connect widget to method when triggered (clicked)
        quit = QAction("Quit", self)

        # quit.setIconVisibleInMenu(True)
        quit.triggered.connect(self.closeEvent)
        self.launcher = None
        self.time_init = timeit.default_timer()
        self.time_start = 0
        self.time_end = 0
        self.time_diff = 0

    # These are required for pickling when spawning a new process.
    # Note that no information is saved and the new Main that spawns will be clean.
    def __getstate__(self):
        return {}
    def __setstate__(self, data):
        return

    def closeEvent(self, event):

         close = QMessageBox.question(self, "QUIT", "Are you sure want to stop process?",QMessageBox.Yes | QMessageBox.No)
         if close == QMessageBox.Yes:

            if self.launcher is not None:
                self.launcher.quit()
            event.accept()
            #import sys
            sys.exit(0)
         else:

             event.ignore()
        # import sys
        # sys.exit(0)


    def Handel_Buttons(self):  # call back functions
        self.pushButton_7.clicked.connect(self.browse_file1)
        self.pushButton_2.clicked.connect(self.browse_file3)
        self.pushButton_3.clicked.connect(self.download)
        self.pushButton_4.clicked.connect(self.view)
        self.pushButton_5.clicked.connect(self.clear)
        self.pushButton_6.clicked.connect(self.takeinputs)
        #self.radioButton_2.toggled.connect(self.onClicked)


    def browse_file1(self):
        self.browse_file = QFileDialog.getOpenFileName(self, "browse file", directory=".",filter="All Files (*.*)")
        self.lineEdit_3.setText(QDir.toNativeSeparators(str(self.browse_file[0])))
        return self.browse_file[0]


    def browse_file3(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        if dlg.exec_():
            filenames = dlg.selectedFiles()
            self.lineEdit_2.setText(QDir.toNativeSeparators(str(filenames[0])))

    def download(self, tree = None, show_tree = False, show_llh = True, show_lineages = True, print_species = True, print_species_spart = True):

        self.time_start = timeit.default_timer()
        
        open_file= self.lineEdit_3.text()
        save_file = self.lineEdit_2.text()
        is_ultrametric = self.radioButton_2.isChecked()

        def fail(exception):
            print(str(exception))
            QMessageBox.warning(self, "Warning", "The species demitation output not obtained, please check input file type")
            pass

        def done(result):
            self.time_end = timeit.default_timer()
            self.time_diff = self.time_end - self.time_start
            print("GMYC returned: " +  repr(len(result)))
            print("TIME taken: ", self.time_diff)
            QMessageBox.information(self, "Information", "The species delimitation output data generated successfully")

        def started():
            self.pushButton_3.setEnabled(False)
            self.pushButton_3.setText('Please wait analysis is going on')
            pass

        def finished():
            self.pushButton_3.setEnabled(True)
            self.pushButton_3.setText('Run analysis and save GMYC output')
            pass

        if not len(open_file) > 0:
            fail(Exception('File not found.'))
            return

        self.launcher = UProcess(self.download_work, open_file=open_file, save_file=save_file, is_ultrametric=is_ultrametric)
        self.launcher.started.connect(started)
        self.launcher.finished.connect(finished)
        self.launcher.done.connect(done)
        self.launcher.fail.connect(fail)
        self.launcher.start()

    def download_work(self, open_file=None, save_file=None, is_ultrametric=None):

        treetest = open(open_file)
        l1 = treetest.readline()
        is_nexus = (l1.strip() == "#NEXUS")
        treetest.close()

        if is_ultrametric:
            if is_nexus:
                nexus = NexusReader(open_file)
                nexus.blocks['trees'].detranslate()
                newick_tree = nexus.trees.trees[0]
                stree = newick_tree
                stree = newick_tree
            if not is_nexus:
                stree = open_file
        else:
            print('time to parse')
            newick_tree = pyr8s.parse.quick(file=open_file)
            stree = newick_tree

        sp = gmyc(tree = stree, print_detail = True, show_tree = False, show_llh = True, show_lineages = True, print_species = True, print_species_spart = True, pv = 0.01, save_file= save_file)
        print("Final number of estimated species by GMYC: " +  repr(len(sp)))

        return sp


    def takeinputs(self):
        comment1, done1 = QInputDialog.getText(
             self, 'Input Dialog', 'Enter your first comment:')
        comment2, done2 = QInputDialog.getText(
           self, 'Input Dialog', 'Enter your second comment:')
        save_file= self.lineEdit_2.text()
        if done1 and done2:

            try:
                fin = open(resource_path(os.path.join(save_file, "partition.spart")), "rt")
                data = fin.read()
                data = data.replace("this is my first comment", str(comment1))
                data = data.replace("this is my second comment", str(comment2))
                fin.close()
                fin = open(resource_path(os.path.join(save_file,  "partition.spart")), "wt")
                fin.write(data)
                fin.close()

            except Exception:
                QMessageBox.warning(self, "Warning", "The spart file is not generated, please generate the output files")
                return
            QMessageBox.information(self, "Information", "The spart file is updated successfully")


    def view(self):
        try:
            save_file = self.lineEdit_2.text()
            pixmap = QPixmap(resource_path(os.path.join(save_file,  "myoutput.png")))
            f = open(resource_path(os.path.join(save_file, "partition.txt")), "rt")
            self.scene = QGraphicsScene()
            self.scene.addPixmap(QPixmap(pixmap))
            self.graphicsView_2.setScene(self.scene)
            self.scene_1 = QGraphicsScene()
            mytext1 = QGraphicsSimpleTextItem(f.read())
            self.scene_1.addItem(mytext1)
            self.graphicsView.setScene(self.scene_1)
            f.close()
        except Exception:
            QMessageBox.warning(self, "Warning", "The species delimitation view is not obtained, please genetrate the analysis output first")
            return
        QMessageBox.information(self, "Information", "The species delimitation result image and partition generated successfully")


    def clear(self):
        try:
            self.lineEdit_3.setText("")
            self.lineEdit_2.setText("")
            self.graphicsView_2.setScene(QGraphicsScene())
            self.graphicsView.setScene(QGraphicsScene())
        except Exception:
            QMessageBox.warning(self, "Warning", "The input data is not cleared, Please do manually")
            return
        QMessageBox.information(self, "Information", "Please start a new analysis")



def main1():

    app=QApplication(sys.argv)

    window=Main()
    window.show()
    app.exec_()

def show():
    """Entry point"""
    app = QApplication(sys.argv)
    main = Main()
    main.setWindowFlags(Qt.Window)
    main.show()
    sys.exit(app.exec_())


if __name__=='__main__':
    multiprocessing.freeze_support()
    show()
    