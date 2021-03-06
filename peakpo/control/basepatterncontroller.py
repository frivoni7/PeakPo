import os
from PyQt5 import QtWidgets
from utils import get_sorted_filelist, find_from_filelist, readchi, \
    make_filename, writechi
from utils import undo_button_press
from .mplcontroller import MplController
from .cakecontroller import CakeController


class BasePatternController(object):

    def __init__(self, model, widget):
        self.model = model
        self.widget = widget
        self.plot_ctrl = MplController(self.model, self.widget)
        self.cake_ctrl = CakeController(self.model, self.widget)
        self.connect_channel()

    def connect_channel(self):
        self.widget.pushButton_NewBasePtn.clicked.connect(
            self.select_base_ptn)
        self.widget.pushButton_PrevBasePtn.clicked.connect(
            lambda: self.goto_next_file('previous'))
        self.widget.pushButton_NextBasePtn.clicked.connect(
            lambda: self.goto_next_file('next'))
        self.widget.pushButton_S_PrevBasePtn.clicked.connect(
            lambda: self.goto_next_file('previous'))
        self.widget.pushButton_S_NextBasePtn.clicked.connect(
            lambda: self.goto_next_file('next'))
        self.widget.pushButton_LastBasePtn.clicked.connect(
            lambda: self.goto_next_file('last'))
        self.widget.pushButton_FirstBasePtn.clicked.connect(
            lambda: self.goto_next_file('first'))
        self.widget.lineEdit_DiffractionPatternFileName.editingFinished.\
            connect(self.load_new_base_pattern_from_name)

    def select_base_ptn(self):
        """
        opens a file select dialog
        """
        filen = QtWidgets.QFileDialog.getOpenFileName(
            self.widget, "Open a Chi File", self.model.chi_path,
            "Data files (*.chi)")[0]
        self._setshow_new_base_ptn(str(filen))

    def goto_next_file(self, move):
        """
        quick move to the next base pattern file
        """
        if not self.model.base_ptn_exist():
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning", "Choose a base pattern first.")
            return
        filelist = get_sorted_filelist(
            self.model.chi_path,
            sorted_by_name=self.widget.radioButton_SortbyNme.isChecked())
        idx = find_from_filelist(filelist,
                                 os.path.split(self.model.base_ptn.fname)[1])
        if idx == -1:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning", "Cannot find current file")
        step = self.widget.spinBox_FileStep.value()
        if move == 'next':
            idx_new = idx + step
        elif move == 'previous':
            idx_new = idx - step
        elif move == 'last':
            idx_new = filelist.__len__() - 1
            if idx == idx_new:
                QtWidgets.QMessageBox.warning(
                    self.widget, "Warning", "It is already the last file.")
                return
        elif move == 'first':
            idx_new = 0
            if idx == idx_new:
                QtWidgets.QMessageBox.warning(
                    self.widget, "Warning", "It is already the first file.")
                return
        if idx_new > filelist.__len__() - 1:
            idx_new = filelist.__len__() - 1
            if idx == idx_new:
                QtWidgets.QMessageBox.warning(
                    self.widget, "Warning", "It is already the last file.")
                return
        if idx_new < 0:
            idx_new = 0
            if idx == idx_new:
                QtWidgets.QMessageBox.warning(
                    self.widget, "Warning", "It is already the first file.")
                return
        new_filename = filelist[idx_new]
        if os.path.exists(new_filename):
            self._load_a_new_pattern(new_filename)
            # self.model.set_base_ptn_color(self.obj_color)
            self.plot_ctrl.update()
        else:
            QtWidgets.QMessageBox.warning(self.widget, "Warning",
                                          new_filename + " does not exist.")

    def load_new_base_pattern_from_name(self):
        if self.widget.lineEdit_DiffractionPatternFileName.isModified():
            filen = self.widget.lineEdit_DiffractionPatternFileName.text()
            self._setshow_new_base_ptn(filen)

    def _setshow_new_base_ptn(self, filen):
        """
        load and then send signal to update_graph
        """
        if os.path.exists(filen):
            self.model.set_chi_path(os.path.split(filen)[0])
            if self.model.base_ptn_exist():
                old_filename = self.model.get_base_ptn_filename()
            else:
                old_filename = None
            new_filename = filen
            self._load_a_new_pattern(new_filename)
            if old_filename is None:
                self.plot_new_graph()
            else:
                self.apply_changes_to_graph()
        else:
            QtWidgets.QMessageBox.warning(
                self.widget, 'Warning', 'Cannot find ' + filen)
            # self.widget.lineEdit_DiffractionPatternFileName.setText(
            #    self.model.get_base_ptn_filename())

    def _load_a_new_pattern(self, new_filename):
        """
        load and process base pattern.  does not signal to update_graph
        """
        self.model.set_base_ptn(
            new_filename, self.widget.doubleSpinBox_SetWavelength.value())
        # self.widget.textEdit_DiffractionPatternFileName.setText(
        #    '1D Pattern: ' + self.model.get_base_ptn_filename())
        self.widget.lineEdit_DiffractionPatternFileName.setText(
            str(self.model.get_base_ptn_filename()))
        temp_dir = os.path.join(self.model.chi_path, 'temporary_pkpo')
        if self.widget.checkBox_UseTempBGSub.isChecked():
            if os.path.exists(temp_dir):
                success = self.model.base_ptn.read_bg_from_tempfile(
                    temp_dir=temp_dir)
                if success:
                    self._update_bg_params_in_widget()
                    print('Read temp chi successfully.')
                else:
                    self._update_bgsub_from_current_values()
                    print('No temp chi file found. Force new bgsub fit.')
            else:
                os.makedirs(temp_dir)
                self._update_bgsub_from_current_values()
                print('No temp chi file found. Force new bgsub fit.')
        else:
            self._update_bgsub_from_current_values()
            print('Temp chi ignored. Force new bgsub fit.')
        filen_tif = self.model.make_filename('tif', original=True)
        filen_mar3450 = self.model.make_filename('mar3450', original=True)
        if not (os.path.exists(filen_tif) or os.path.exists(filen_mar3450)):
            self.widget.checkBox_ShowCake.setChecked(False)
            return
        # self._update_bg_params_in_widget()
        if self.widget.checkBox_ShowCake.isChecked() and \
                (self.model.poni is not None):
            self.cake_ctrl.process_temp_cake()
            # not sure this is correct.
            # self.cake_ctrl.addremove_cake(update_plot=False)

    def _update_bg_params_in_widget(self):
        self.widget.spinBox_BGParam0.setValue(self.model.base_ptn.params_chbg[0])
        self.widget.spinBox_BGParam1.setValue(self.model.base_ptn.params_chbg[1])
        self.widget.spinBox_BGParam2.setValue(self.model.base_ptn.params_chbg[2])
        self.widget.doubleSpinBox_Background_ROI_min.setValue(self.model.base_ptn.roi[0])
        self.widget.doubleSpinBox_Background_ROI_max.setValue(self.model.base_ptn.roi[1])

    def _update_bgsub_from_current_values(self):
        x_raw, y_raw = self.model.base_ptn.get_raw()
        if (x_raw.min() >= self.widget.doubleSpinBox_Background_ROI_min.value()) or \
                (x_raw.max() <= self.widget.doubleSpinBox_Background_ROI_min.value()):
            self.widget.doubleSpinBox_Background_ROI_min.setValue(x_raw.min())
        if (x_raw.max() <= self.widget.doubleSpinBox_Background_ROI_max.value()) or \
                (x_raw.min() >= self.widget.doubleSpinBox_Background_ROI_max.value()):
            self.widget.doubleSpinBox_Background_ROI_max.setValue(x_raw.max())
        self.model.base_ptn.subtract_bg(
            [self.widget.doubleSpinBox_Background_ROI_min.value(),
                self.widget.doubleSpinBox_Background_ROI_max.value()],
            [self.widget.spinBox_BGParam0.value(),
                self.widget.spinBox_BGParam1.value(),
                self.widget.spinBox_BGParam2.value()], yshift=0)
        self.model.base_ptn.write_temporary_bgfiles()

    def apply_changes_to_graph(self):
        self.plot_ctrl.update()

    def plot_new_graph(self):
        self.plot_ctrl.zoom_out_graph()
