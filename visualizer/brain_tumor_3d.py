import sys
import os

from MainWindow import *
from PyQt5 import QtCore

def redirect_vtk_messages():
    """ Redirect VTK related error messages to a file."""
    import tempfile
    tempfile.template = 'vtk-err'
    f = tempfile.mktemp('.log')
    log = vtk.vtkFileOutputWindow()
    log.SetFlush(1)
    log.SetFileName(f)
    log.SetInstance(log)


def verify_type(file):  
    ext = os.path.basename(file).split(os.extsep, 1)
    if ext[1] != 'nii.gz':
        print('Invalid File')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    sys.exit(app.exec_())
