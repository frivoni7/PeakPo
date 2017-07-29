import os
import dill
import zipfile
from PyQt5 import QtWidgets
from .mplcontroller import MplController
from .waterfalltablecontroller import WaterfallTableController
from .jcpdstablecontroller import JcpdsTableController
from .peakfittablecontroller import PeakfitTableController
from utils import dialog_savefile


class SessionController(object):

    def __init__(self, model, widget):
        self.model = model
        self.widget = widget
        self.plot_ctrl = MplController(self.model, self.widget)
        self.waterfalltable_ctrl = \
            WaterfallTableController(self.model, self.widget)
        self.jcpdstable_ctrl = JcpdsTableController(self.model, self.widget)
        self.peakfit_table_ctrl = PeakfitTableController(
            self.model, self.widget)
        self.connect_channel()

    def connect_channel(self):
        self.widget.pushButton_SaveDPP.clicked.connect(self.save_dpp)
        self.widget.pushButton_LoadPPSS.clicked.connect(self.load_ppss)
        self.widget.pushButton_LoadDPP.clicked.connect(self.load_dpp)
        self.widget.pushButton_ZipSession.clicked.connect(self.zip_ppss)
        self.widget.pushButton_SaveJlist.clicked.connect(self.save_dpp)
        self.widget.pushButton_PkFtSectionSavetoDPP.clicked.connect(
            self.save_dpp)
        self.widget.pushButton_SaveDPPandPPSS.clicked.connect(
            self.save_dpp_ppss)

    def load_ppss(self):
        """
        get existing jlist file from data folder
        """
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self.widget, "Choose A Session File",
            self.model.chi_path, "(*.ppss)")[0]
#       replaceing chi_path with '' does not work
        if fn == '':
            return
        self._load_ppss(fn, jlistonly=False)
        self.plot_ctrl.zoom_out_graph()
        self.update_inputs()

    def load_dpp(self):
        """
        get existing jlist file from data folder
        """
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self.widget, "Choose A Session File",
            self.model.chi_path, "(*.dpp)")[0]
#       replaceing chi_path with '' does not work
        if fn == '':
            return
        success = self._load_dpp(fn, jlistonly=False)
        print(success)
        if success:
            self.plot_ctrl.zoom_out_graph()
            self.update_inputs()

    def _update_ppss(self):
        if not self.model.base_ptn_exist():
            return
        fn = self.model.make_filename('ppss')
        if not os.path.exists(fn):
            return
        self._load_ppss(fn, jlistonly=False)
        self.update_inputs()

    def _load_ppss(self, fsession, jlistonly=False):
        '''
        internal method for reading pickled ppss file
        '''
        self.model.read_ppss(fsession)
        success = self._load_jcpds_from_ppss()
        if not success:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning",
                "The JCPDS in the PPSS cannot be found.")
        else:
            self.widget.textEdit_Jlist.setText('Jlist: ' + str(fsession))
        if jlistonly:
            return
        success = self._load_base_ptn_from_ppss(fsession)
        if not success:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning",
                "The base pattern file in the PPSS cannot be found.")
        else:
            self.widget.textEdit_DiffractionPatternFileName.setText(
                '1D pattern: ' + str(self.model.base_ptn.fname))
            self.widget.lineEdit_DiffractionPatternFileName.setText(
                str(self.model.base_ptn.fname))
            self.widget.textEdit_SessionFileName.setText(
                'Session: ' + str(fsession))
        success = self._load_waterfall_ptn_from_ppss()
        if not success:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning",
                "The waterfall pattern files in the PPSS cannot be found.")

    def _load_dpp(self, filen_dpp, jlistonly=False):
        '''
        internal method for reading dilled dpp file
        '''
        try:
            with open(filen_dpp, 'rb') as f:
                model_dpp = dill.load(f)
        except Exception as inst:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning", str(inst))
            return False
        self.model.set_from(model_dpp)
        self.widget.textEdit_Jlist.setText('Jlist: ' + str(filen_dpp))
        self.widget.textEdit_DiffractionPatternFileName.setText(
            '1D pattern: ' + str(self.model.base_ptn.fname))
        self.widget.lineEdit_DiffractionPatternFileName.setText(
            str(self.model.base_ptn.fname))
        self.widget.textEdit_SessionFileName.setText(
            'Session: ' + str(filen_dpp))
        self.widget.doubleSpinBox_Pressure.setValue(
            self.model.get_saved_pressure())
        self.widget.doubleSpinBox_Temperature.setValue(
            self.model.get_saved_temperature())
        return True

        """
        success = self._load_jcpds_from_session()
        if not success:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning",
                "The JCPDS in the PPSS cannot be found.")
        else:
            self.widget.textEdit_Jlist.setText('Jlist: ' + str(fsession))
        if jlistonly:
            return
        success = self._load_base_ptn_from_session(fsession)
        if not success:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning",
                "The base pattern file in the PPSS cannot be found.")
        else:
            self.widget.textEdit_DiffractionPatternFileName.setText(
                '1D pattern: ' + str(self.model.base_ptn.fname))
            self.widget.lineEdit_DiffractionPatternFileName.setText(
                str(self.model.base_ptn.fname))
            self.widget.textEdit_SessionFileName.setText(
                'Session: ' + str(fsession))
        success = self._load_waterfall_ptn_from_session()
        if not success:
            QtWidgets.QMessageBox.warning(
                self.widget, "Warning",
                "The waterfall pattern files in the PPSS cannot be found.")
        """

    def _load_base_ptn_from_ppss(self, fsession):
        if self.model.session.chi_path == '':
            return False
        if not os.path.exists(self.model.session.chi_path):
            chi_path_from_fsession = os.path.dirname(str(fsession))
            chi_basefilen = os.path.basename(self.model.session.pattern.fname)
            chi_filen_at_fsession_dir = os.path.join(
                chi_path_from_fsession, chi_basefilen)
            if os.path.exists(chi_filen_at_fsession_dir):
                new_chi_filen = chi_filen_at_fsession_dir
                new_chi_path = chi_path_from_fsession
            else:
                return False
        else:
            new_chi_filen = self.model.session.pattern.fname
        self.model.set_base_ptn(new_chi_filen, self.model.session.wavelength)
        self.model.base_ptn.get_chbg(self.model.session.bg_roi,
                                     self.model.session.bg_params, yshift=0)
        self.widget.doubleSpinBox_SetWavelength.setValue(
            self.model.session.wavelength)
        self.widget.doubleSpinBox_Pressure.setValue(
            self.model.session.pressure)
        self.widget.doubleSpinBox_Temperature.setValue(
            self.model.session.temperature)
        self.widget.doubleSpinBox_Background_ROI_min.setValue(
            self.model.session.bg_roi[0])
        self.widget.doubleSpinBox_Background_ROI_max.setValue(
            self.model.session.bg_roi[1])
        self.widget.spinBox_BGParam0.setValue(
            self.model.session.bg_params[0])
        self.widget.spinBox_BGParam1.setValue(
            self.model.session.bg_params[1])
        self.widget.spinBox_BGParam2.setValue(
            self.model.session.bg_params[2])
        return True

    def _load_waterfall_ptn_from_ppss(self):
        if self.model.session.chi_path == '':
            return False
        if self.model.session.waterfallpatterns == []:
            return True
        else:
            new_wf_ptn_names = []
            new_wf_wavelength = []
            new_wf_display = []
            for ptn in self.model.session.waterfallpatterns:
                if os.path.exists(ptn.fname):
                    new_wf_ptn_names.append(ptn.fname)
                elif os.path.exists(os.path.join(
                        self.model.chi_path, os.path.basename(ptn.fname))):
                    new_wf_ptn_names.append(
                        os.path.join(
                            self.model.chi_path, os.path.basename(ptn.fname)))
                    new_wf_wavelengh.append(ptn.wavelength)
                    new_wf_display.append(ptn.display)
                else:
                    QtWidgets.QMessageBox.warning(
                        self.widget, "Warning",
                        "Some waterfall paterns in PPSS do not exist.")
            if new_wf_ptn_name == []:
                return False
            else:
                self.model.set_waterfall_ptn(
                    new_wf_ptn_names, new_wf_wavelength, new_wf_display,
                    self.model.session.bg_roi, self.model.session.bg_params)
                return True

    def _load_jcpds_from_ppss(self):
        if (self.model.session.jcpds_path == ''):
            return False
        if os.path.exists(self.model.session.jcpds_path):
            self.model.set_jcpds_path(self.model.session.jcpds_path)
            self.model.set_jcpds_from_ppss()
            return True
        else:
            reply = QtWidgets.QMessageBox.question(
                self.widget, "Question",
                "The JCPDS path in the PPSS does not exist.  \
                Do you want to update the JCPDS path?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes)
            if reply == QtWidgets.QMessageBox.Yes:
                jcpds_path = \
                    QtWidgets.QFileDialog.getExistingDirectory(
                        self.widget, "Open Directory", self.model.jcpds_path,
                        QtWidgets.QFileDialog.ShowDirsOnly)
                self.model.set_jcpds_path(jcpds_path)
                self.model.set_jcpds_from_ppss()
                return True
            else:
                QtWidgets.QMessageBox.warning(
                    self.widget, "Warning", "JCPDS path does not match.")
                return False

    def _dump_dpp(self, filen_dpp):
        with open(filen_dpp, 'wb') as f:
            dill.dump(self.model, f)

    def _dump_ppss(self, fsession):
        """
        session = *.ppss
        """
        self.model.write_as_ppss(
            fsession, self.widget.doubleSpinBox_Pressure.value(),
            self.widget.doubleSpinBox_Temperature.value())

    def update_inputs(self):
        self.reset_bgsub()
        self.waterfalltable_ctrl.update()
        self.jcpdstable_ctrl.update()
        self.peakfit_table_ctrl.update_sections()
        self.peakfit_table_ctrl.update_pkparams()

    def zip_ppss(self):
        """
        session = *.ppss
        """
        if not self.model.base_ptn_exist():
            fzip = os.path.join(self.model.chi_path, 'default.zip')
        else:
            fzip = self.model.make_filename('zip')
        reply = QtWidgets.QMessageBox.question(
            self.widget, 'Question',
            'Do you want to save in default filename, %s ?' % fzip,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes)
        if reply == QtWidgets.QMessageBox.No:
            fzip = QtWidgets.QFileDialog.getSaveFileName(
                self.widget, "Save A Zip File",
                fzip, "(*.zip)", None)[0]
        else:
            if os.path.exists(fzip):
                reply = QtWidgets.QMessageBox.question(
                    self.widget, 'Question',
                    'The file already exist.  Do you want to overwrite?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.No:
                    return
        if str(fzip) != '':
            path, filen = os.path.split(str(fzip))
            fsession_name = '%s.forzip.ppss' % filen
            fsession = os.path.join(path, fsession_name)
            self._dump_ppss(str(fsession))
            self.widget.textEdit_Jlist.setText('Jlist : ' + str(fsession))
            zf = zipfile.ZipFile(str(fzip), 'w', zipfile.ZIP_DEFLATED)
            zf.write(fsession, arcname=fsession_name)
            if self.model.base_ptn_exist():
                dum, filen = os.path.split(self.model.base_ptn.fname)
                zf.write(self.model.base_ptn.fname, arcname=filen)
            if self.model.waterfall_exist():
                for wf in self.model.waterfall_ptn:
                    dum, filen = os.path.split(wf.fname)
                    zf.write(wf.fname, arcname=filen)
            zf.close()

    def save_dpp_ppss(self):
        self.save_dpp()
        self.save_ppss()

    def save_dpp(self):
        if not self.model.base_ptn_exist():
            fsession = os.path.join(self.model.chi_path, 'default.dpp')
        else:
            fsession = self.model.make_filename('dpp')
        new_filename = dialog_savefile(self.widget, fsession)
        if new_filename != '':
            self.model.save_pressure(self.widget.doubleSpinBox_Pressure.value())
            self.model.save_temperature(
                self.widget.doubleSpinBox_Temperature.value())
            self._dump_dpp(new_filename)
            self.widget.textEdit_SessionFileName.setText('Session: ' +
                                                         str(new_filename))
            self.widget.tableWidget_PkFtSections.setStyleSheet(
                "Background-color:None;color:rgb(0,0,0);")

    def save_ppss(self):
        """
        session = *.ppss
        """
        if not self.model.base_ptn_exist():
            fsession = os.path.join(self.model.chi_path, 'dum.ppss')
        else:
            fsession = self.model.make_filename('ppss')
        new_filename = dialog_savefile(self.widget, fsession)
        if new_filename != '':
            self._dump_ppss(new_filename)
            self.widget.textEdit_SessionFileName.setText('Session: ' +
                                                         str(new_filename))

    def save_ppss_with_default_name(self):
        if not self.model.base_ptn_exist():
            fsession = os.path.join(self.model.chi_path, 'dum.ppss')
        else:
            fsession = self.model.make_filename('ppss')
        if os.path.exists(fsession):
            reply = QtWidgets.QMessageBox.question(
                self.widget, 'Question',
                'The file already exist.  Do you want to overwrite?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes)
            if reply == QtWidgets.QMessageBox.No:
                return
        if str(fsession) != '':
            self._dump_ppss(str(fsession))
            self.widget.textEdit_SessionFileName.setText(
                'Session: ' + str(fsession))

    def reset_bgsub(self):
        '''
        this is to read from session file and put to the table
        '''
        bg_params = [self.widget.spinBox_BGParam0.value(),
                     self.widget.spinBox_BGParam1.value(),
                     self.widget.spinBox_BGParam2.value()]
        bg_roi = [self.widget.doubleSpinBox_Background_ROI_min.value(),
                  self.widget.doubleSpinBox_Background_ROI_max.value()]
        self.model.base_ptn.subtract_bg(bg_roi, bg_params, yshift=0)
        if self.model.waterfall_exist():
            for pattern in self.model.waterfall_ptn:
                pattern.get_chbg(bg_roi, bg_params, yshift=0)