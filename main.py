import sys
import math
import time
import os

import PyQt5.QtWidgets as QtWidgets
from PyQt5 import Qt


from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkUtils import *
from config import *


class MainWindow(QtWidgets.QMainWindow, QtWidgets.QApplication):
    def __init__(self, app):
        self.app = app
      
        QtWidgets.QMainWindow.__init__(self, None)
        
        # base setup
        self.renderer, self.frame, self.vtk_widget, self.interactor, self.render_window = self.setup()

        # create grid for all widgets
        self.grid = QtWidgets.QGridLayout()

        # add each widget
        self.add_vtk_window_widget()
        self.add_brain_input_widget()

        self.run() 
        
        
    @staticmethod
    def setup():
        
        renderer = vtk.vtkRenderer()
        renderer.GlobalWarningDisplayOff()
        frame = QtWidgets.QFrame()
        vtk_widget = QVTKRenderWindowInteractor()
        interactor = vtk_widget.GetRenderWindow().GetInteractor()
        render_window = vtk_widget.GetRenderWindow()

        frame.setAutoFillBackground(True)
        vtk_widget.GetRenderWindow().AddRenderer(renderer)
        render_window.AddRenderer(renderer)
        interactor.SetRenderWindow(render_window)
        interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())


        return renderer, frame, vtk_widget, interactor, render_window

    def add_brain_input_widget(self): 
        groupBox = QtWidgets.QGroupBox("Inputs") # group box to group controls
        groupBox_layout = QtWidgets.QGridLayout() 
        
        label = QtWidgets.QLabel("Brain File:")
        groupBox_layout.addWidget(label)
        hbox = QtWidgets.QHBoxLayout()
        self.qt_file_name = QtWidgets.QLineEdit()
        hbox.addWidget(self.qt_file_name) 
        self.qt_browser_button = Qt.QPushButton('Browser')
        self.qt_browser_button.clicked.connect(lambda: self.on_file_browser_clicked('BRAIN'))
        self.qt_browser_button.show()
        hbox.addWidget(self.qt_browser_button)
        file_widget = QtWidgets.QWidget()
        file_widget.setLayout(hbox)
        groupBox_layout.addWidget(file_widget)

        label = QtWidgets.QLabel("Mask File:")
        groupBox_layout.addWidget(label)
        hbox = QtWidgets.QHBoxLayout()
        self.qt_file_name1 = QtWidgets.QLineEdit()
        hbox.addWidget(self.qt_file_name1) 
        self.qt_browser_button = Qt.QPushButton('Browser')
        self.qt_browser_button.clicked.connect(lambda: self.on_file_browser_clicked('MASK'))
        self.qt_browser_button.show()
        hbox.addWidget(self.qt_browser_button)
        file_widget = QtWidgets.QWidget()
        file_widget.setLayout(hbox)
        groupBox_layout.addWidget(file_widget)

        self.qt_open_button = QtWidgets.QPushButton('Open')
        self.qt_open_button.clicked.connect(self.load_inputs)
        self.qt_open_button.show()
        groupBox_layout.addWidget(self.qt_open_button)

        groupBox.setLayout(groupBox_layout)
        self.grid.addWidget(groupBox, 0, 0, 1, 2)
    
    def on_file_browser_clicked(self,type):
        dlg = Qt.QFileDialog()
        dlg.setFileMode(Qt.QFileDialog.AnyFile)

        if dlg.exec_():
            filenames = dlg.selectedFiles()
            if not self.verify_type(filenames[0]):
                self.object_group_box.setTitle('Invalid File Uploaded')
                self.object_group_box.setStyleSheet('QGroupBox:title {color: rgb(255, 0, 0);}')
                return
            if type == 'BRAIN':
                self.object_group_box.setTitle('Brain File Uploaded')
                self.object_group_box.setStyleSheet('QGroupBox:title {color: rgb(0, 255, 0);}')
                self.app.BRAIN_FILE = filenames[0]
                self.qt_file_name.setText(filenames[0])
            else:
                self.object_group_box.setTitle('Mask File Uploaded')
                self.object_group_box.setStyleSheet('QGroupBox:title {color: rgb(0, 255, 0);}')
                self.app.MASK_FILE = filenames[0]
                self.qt_file_name1.setText(filenames[0])

            

    def verify_type(self,file):  
        ext = os.path.basename(file).split(os.extsep, 1)
        #print(ext)
        if 'nii.gz' not in ext[-1]:
            return False
        return True

    def load_inputs(self):
        if hasattr(self.app,'BRAIN_FILE') and hasattr(self.app,'MASK_FILE'):
            self.object_group_box.setTitle('Rendering... Please Wait')
            self.object_group_box.setStyleSheet('QGroupBox:title {color: rgb(0, 255, 0);}')
            self.run()
            self.object_group_box.setTitle('Render Completed')
            self.object_group_box.setStyleSheet('QGroupBox:title {color: rgb(0, 255, 0);}')
        else:
            self.object_group_box.setTitle('Load both the Brain and Mask files')
            self.object_group_box.setStyleSheet('QGroupBox:title {color: rgb(255, 0, 0);}')

    
    def run(self):

        if hasattr(self,'w1') and hasattr(self,'w2') and hasattr(self,'w3'):
            self.grid.removeWidget(self.w1)
            del self.w1
            self.grid.removeWidget(self.w2)
            del self.w2
            self.grid.removeWidget(self.w3)
            del self.w3
        

        if not hasattr(self.app,'BRAIN_FILE') or not hasattr(self.app,'MASK_FILE'):
            self.render_window.Render()
            self.setWindowTitle(APPLICATION_TITLE)
            self.frame.setLayout(self.grid)
            self.setCentralWidget(self.frame)
            self.set_axial_view()
            self.interactor.Initialize()
            self.show()
            return

        if hasattr(self,'brain_image_prop') and hasattr(self,'brain_slicer_props') and hasattr(self,'slicer_widgets'):
            del self.brain_image_prop
            del self.brain_slicer_props
            del self.slicer_widgets
            del self.brain_slicer_cb
            del self.brain
            del self.mask
            
        self.render_window.Render()
        
        
        self.brain, self.mask = setup_brain(self.renderer, self.app.BRAIN_FILE,self), setup_mask(self.renderer,
                                                                                            self.app.MASK_FILE,self)

        # setup brain projection and slicer
        self.brain_image_prop = setup_projection(self.brain, self.renderer,self)
        self.brain_slicer_props = setup_slicer(self.renderer, self.brain,self)  # causing issues with rotation
        self.slicer_widgets = []
        
        # brain pickers
        self.brain_threshold_sp = self.create_new_picker(self.brain.scalar_range[1], self.brain.scalar_range[0], 5.0,
                                                         sum(self.brain.scalar_range) / 2, self.brain_threshold_vc)
        self.brain_opacity_sp = self.create_new_picker(1.0, 0.0, 0.1, BRAIN_OPACITY, self.brain_opacity_vc)
        self.brain_smoothness_sp = self.create_new_picker(1000, 100, 100, BRAIN_SMOOTHNESS, self.brain_smoothness_vc)
        self.brain_lut_sp = self.create_new_picker(3.0, 0.0, 0.1, 2.0, self.lut_value_changed)
        self.brain_projection_cb = self.add_brain_projection()
        self.brain_slicer_cb = self.add_brain_slicer()

        # mask pickers
        self.mask_opacity_sp = self.create_new_picker(1.0, 0.0, 0.1, MASK_OPACITY, self.mask_opacity_vc)
        self.mask_smoothness_sp = self.create_new_picker(1000, 100, 100, MASK_SMOOTHNESS, self.mask_smoothness_vc)
        self.mask_label_cbs = []
        
        self.w1 = self.add_brain_settings_widget()
        self.w2 = self.add_mask_settings_widget()
        self.w3 = self.add_views_widget()
        self.show_widgets()

        #  set layout and show
        self.render_window.Render()
        self.setWindowTitle(APPLICATION_TITLE)
        self.frame.setLayout(self.grid)
        self.setCentralWidget(self.frame)
        self.set_axial_view()
        self.interactor.Initialize()
        self.show()

    def show_widgets(self):
        self.grid.addWidget(self.w1, 1, 0, 1, 2)
        self.grid.addWidget(self.w2, 2, 0, 2, 2)
        self.grid.addWidget(self.w3, 4, 0, 2, 2)

    def lut_value_changed(self):
        lut = self.brain.image_mapper.GetLookupTable()
        new_lut_value = self.brain_lut_sp.value()
        lut.SetValueRange(0.0, new_lut_value)
        lut.Build()
        self.brain.image_mapper.SetLookupTable(lut)
        self.brain.image_mapper.Update()
        self.render_window.Render()

    def add_brain_slicer(self):
        slicer_cb = QtWidgets.QCheckBox("Slicer")
        slicer_cb.clicked.connect(self.brain_slicer_vc)
        return slicer_cb

    def add_vtk_window_widget(self):
        object_group_box = QtWidgets.QGroupBox('')
        self.object_group_box = object_group_box
        object_layout = QtWidgets.QVBoxLayout()
        object_layout.addWidget(self.vtk_widget)
        object_group_box.setLayout(object_layout)

        self.grid.addWidget(object_group_box, 0, 2, 5, 5)

        # column width for vtk_widget
        self.grid.setColumnMinimumWidth(2, 700)

    def add_brain_settings_widget(self):
        brain_group_box = QtWidgets.QGroupBox("Brain Settings")
        brain_group_layout = QtWidgets.QGridLayout()
        brain_group_layout.addWidget(QtWidgets.QLabel("Brain Threshold"), 0, 0)
        brain_group_layout.addWidget(QtWidgets.QLabel("Brain Opacity"), 1, 0)
        brain_group_layout.addWidget(QtWidgets.QLabel("Brain Smoothness"), 2, 0)
        brain_group_layout.addWidget(QtWidgets.QLabel("Image Intensity"), 3, 0)
        brain_group_layout.addWidget(self.brain_threshold_sp, 0, 1, 1, 2)
        brain_group_layout.addWidget(self.brain_opacity_sp, 1, 1, 1, 2)
        brain_group_layout.addWidget(self.brain_smoothness_sp, 2, 1, 1, 2)
        brain_group_layout.addWidget(self.brain_lut_sp, 3, 1, 1, 2)
        brain_group_layout.addWidget(self.brain_projection_cb, 4, 0)
        brain_group_layout.addWidget(self.brain_slicer_cb, 4, 1)
        brain_group_layout.addWidget(self.create_new_separator(), 5, 0, 1, 3)
        brain_group_layout.addWidget(QtWidgets.QLabel("Axial Slice"), 6, 0)
        brain_group_layout.addWidget(QtWidgets.QLabel("Coronal Slice"), 7, 0)
        brain_group_layout.addWidget(QtWidgets.QLabel("Sagittal Slice"), 8, 0)

        slicer_funcs = [self.axial_slice_changed, self.coronal_slice_changed, self.sagittal_slice_changed]
        current_label_row = 6
   
        extent_index = 5
        for func in slicer_funcs:
            slice_widget = QtWidgets.QSlider(Qt.Qt.Horizontal)
            slice_widget.setDisabled(True)
            self.slicer_widgets.append(slice_widget)
            brain_group_layout.addWidget(slice_widget, current_label_row, 1, 1, 2)
            slice_widget.valueChanged.connect(func)
            slice_widget.setRange(self.brain.extent[extent_index - 1], self.brain.extent[extent_index])
            slice_widget.setValue(int(self.brain.extent[extent_index] / 2))
            current_label_row += 1
            extent_index -= 2

        brain_group_box.setLayout(brain_group_layout)

        return brain_group_box
    
    def axial_slice_changed(self):
        pos = self.slicer_widgets[0].value()
        self.brain_slicer_props[0].SetDisplayExtent(self.brain.extent[0], self.brain.extent[1], self.brain.extent[2],
                                                    self.brain.extent[3], pos, pos)
        self.render_window.Render()

    def coronal_slice_changed(self):
        pos = self.slicer_widgets[1].value()
        self.brain_slicer_props[1].SetDisplayExtent(self.brain.extent[0], self.brain.extent[1], pos, pos,
                                                    self.brain.extent[4], self.brain.extent[5])
        self.render_window.Render()

    def sagittal_slice_changed(self):
        pos = self.slicer_widgets[2].value()
        self.brain_slicer_props[2].SetDisplayExtent(pos, pos, self.brain.extent[2], self.brain.extent[3],
                                                    self.brain.extent[4], self.brain.extent[5])
        self.render_window.Render()

    def add_mask_settings_widget(self):
        mask_settings_group_box = QtWidgets.QGroupBox("Mask Settings")
        mask_settings_layout = QtWidgets.QGridLayout()
        mask_settings_layout.addWidget(QtWidgets.QLabel("Mask Opacity"), 0, 0)
        mask_settings_layout.addWidget(QtWidgets.QLabel("Mask Smoothness"), 1, 0)
        mask_settings_layout.addWidget(self.mask_opacity_sp, 0, 1)
        mask_settings_layout.addWidget(self.mask_smoothness_sp, 1, 1)
        mask_multi_color_radio = QtWidgets.QRadioButton("Multi Color")
        mask_multi_color_radio.setChecked(True)
        mask_multi_color_radio.clicked.connect(self.mask_multi_color_radio_checked)
        mask_single_color_radio = QtWidgets.QRadioButton("Single Color")
        mask_single_color_radio.clicked.connect(self.mask_single_color_radio_checked)
        mask_settings_layout.addWidget(mask_multi_color_radio, 2, 0)
        mask_settings_layout.addWidget(mask_single_color_radio, 2, 1)
        mask_settings_layout.addWidget(self.create_new_separator(), 3, 0, 1, 2)

        self.mask_label_cbs = []
        c_col, c_row = 0, 4  # c_row must always be (+1) of last row
        for i in range(1, 11):
            self.mask_label_cbs.append(QtWidgets.QCheckBox("Label {}".format(i)))
            mask_settings_layout.addWidget(self.mask_label_cbs[i - 1], c_row, c_col)
            c_row = c_row + 1 if c_col == 1 else c_row
            c_col = 0 if c_col == 1 else 1

        mask_settings_group_box.setLayout(mask_settings_layout)

        for i, cb in enumerate(self.mask_label_cbs):
            if i < len(self.mask.labels) and self.mask.labels[i].actor:
                cb.setChecked(True)
                cb.clicked.connect(self.mask_label_checked)
            else:
                cb.setDisabled(True)
        return mask_settings_group_box

    def add_views_widget(self):
        axial_view = QtWidgets.QPushButton("Axial")
        coronal_view = QtWidgets.QPushButton("Coronal")
        sagittal_view = QtWidgets.QPushButton("Sagittal")
        views_box = QtWidgets.QGroupBox("Views")
        views_box_layout = QtWidgets.QVBoxLayout()
        views_box_layout.addWidget(axial_view)
        views_box_layout.addWidget(coronal_view)
        views_box_layout.addWidget(sagittal_view)
        views_box.setLayout(views_box_layout)

        axial_view.clicked.connect(self.set_axial_view)
        coronal_view.clicked.connect(self.set_coronal_view)
        sagittal_view.clicked.connect(self.set_sagittal_view)
        return views_box

    @staticmethod
    def create_new_picker(max_value, min_value, step, picker_value, value_changed_func):
        if isinstance(max_value, int):
            picker = QtWidgets.QSpinBox()
        else:
            picker = QtWidgets.QDoubleSpinBox()

        picker.setMaximum(max_value)
        picker.setMinimum(min_value)
        picker.setSingleStep(step)
        picker.setValue(picker_value)
        picker.valueChanged.connect(value_changed_func)
        return picker

    def add_brain_projection(self):
        projection_cb = QtWidgets.QCheckBox("Projection")
        projection_cb.clicked.connect(self.brain_projection_vc)
        return projection_cb

    def mask_label_checked(self):
        for i, cb in enumerate(self.mask_label_cbs):
            if cb.isChecked():
                self.mask.labels[i].property.SetOpacity(self.mask_opacity_sp.value())
            elif cb.isEnabled():  # labels without data are disabled
                self.mask.labels[i].property.SetOpacity(0)
        self.render_window.Render()

    def mask_single_color_radio_checked(self):
        for label in self.mask.labels:
            if label.property:
                label.property.SetColor(MASK_COLORS[0])
        self.render_window.Render()

    def mask_multi_color_radio_checked(self):
        for label in self.mask.labels:
            if label.property:
                label.property.SetColor(label.color)
        self.render_window.Render()

    def brain_projection_vc(self):
        projection_checked = self.brain_projection_cb.isChecked()
        self.brain_slicer_cb.setDisabled(projection_checked) 
        self.brain_image_prop.SetOpacity(projection_checked)
        self.render_window.Render()

    def brain_slicer_vc(self):
        slicer_checked = self.brain_slicer_cb.isChecked()

        for widget in self.slicer_widgets:
            widget.setEnabled(slicer_checked)

        self.brain_projection_cb.setDisabled(slicer_checked)  
        for prop in self.brain_slicer_props:
            prop.GetProperty().SetOpacity(slicer_checked)
        self.render_window.Render()

    def brain_opacity_vc(self):
        opacity = round(self.brain_opacity_sp.value(), 2)
        self.brain.labels[0].property.SetOpacity(opacity)
        self.render_window.Render()

    def brain_threshold_vc(self):
        self.process_changes()
        threshold = self.brain_threshold_sp.value()
        self.brain.labels[0].extractor.SetValue(0, threshold)
        self.render_window.Render()

    def brain_smoothness_vc(self):
        self.process_changes()
        smoothness = self.brain_smoothness_sp.value()
        self.brain.labels[0].smoother.SetNumberOfIterations(smoothness)
        self.render_window.Render()

    def mask_opacity_vc(self):
        opacity = round(self.mask_opacity_sp.value(), 2)
        for i, label in enumerate(self.mask.labels):
            if label.property and self.mask_label_cbs[i].isChecked():
                label.property.SetOpacity(opacity)  
        self.render_window.Render()

    def mask_smoothness_vc(self):
        self.process_changes()
        smoothness = self.mask_smoothness_sp.value()
        for label in self.mask.labels:
            if label.smoother:
                label.smoother.SetNumberOfIterations(smoothness)
        self.render_window.Render()

    def set_axial_view(self):
        self.renderer.ResetCamera()
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        p = self.renderer.GetActiveCamera().GetPosition()
        dist = math.sqrt((p[0] - fp[0]) ** 2 + (p[1] - fp[1]) ** 2 + (p[2] - fp[2]) ** 2)
        self.renderer.GetActiveCamera().SetPosition(fp[0], fp[1], fp[2] + dist)
        self.renderer.GetActiveCamera().SetViewUp(0.0, 1.0, 0.0)
        self.renderer.GetActiveCamera().Zoom(1.8)
        self.render_window.Render()

    def set_coronal_view(self):
        self.renderer.ResetCamera()
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        p = self.renderer.GetActiveCamera().GetPosition()
        dist = math.sqrt((p[0] - fp[0]) ** 2 + (p[1] - fp[1]) ** 2 + (p[2] - fp[2]) ** 2)
        self.renderer.GetActiveCamera().SetPosition(fp[0], fp[2] - dist, fp[1])
        self.renderer.GetActiveCamera().SetViewUp(0.0, 0.5, 0.5)
        self.renderer.GetActiveCamera().Zoom(1.8)
        self.render_window.Render()

    def set_sagittal_view(self):
        self.renderer.ResetCamera()
        fp = self.renderer.GetActiveCamera().GetFocalPoint()
        p = self.renderer.GetActiveCamera().GetPosition()
        dist = math.sqrt((p[0] - fp[0]) ** 2 + (p[1] - fp[1]) ** 2 + (p[2] - fp[2]) ** 2)
        self.renderer.GetActiveCamera().SetPosition(fp[2] + dist, fp[0], fp[1])
        self.renderer.GetActiveCamera().SetViewUp(0.0, 0.0, 1.0)
        self.renderer.GetActiveCamera().Zoom(1.6)
        self.render_window.Render()

    @staticmethod
    def create_new_separator():
        horizontal_line = QtWidgets.QWidget()
        horizontal_line.setFixedHeight(1)
        horizontal_line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        horizontal_line.setStyleSheet("background-color: #c8c8c8;")
        return horizontal_line

    def process_changes(self):
        for _ in range(10):
            self.app.processEvents()
            time.sleep(0.1)



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    sys.exit(app.exec_())
