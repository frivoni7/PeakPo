import pickle
import os
import copy
from ds_cake import DiffImg
# do not change the module structure for ds_jcpds and ds_powdiff for
# retro compatibility
from ds_jcpds import JCPDSplt, Session
from ds_powdiff import PatternPeakPo, get_DataSection
from ds_section import Section
from utils import samefilename, make_filename


class PeakPoModel(object):
    """
    session is only for reading/writing/referencing.
    components of the models are not part of session.
    session is a reference object
    """

    def __init__(self):
        self.base_ptn = None
        self.waterfall_ptn = []
        self.jcpds_lst = []
        self.ucfit_lst = []
        self.diff_img = None
        self.poni = None
        self.session = None
        self.jcpds_path = ''
        self.chi_path = ''
        self.current_section = None
        self.section_lst = []
        self.saved_pressure = 10.
        self.saved_temperature = 300.

    def get_saved_pressure(self):
        return self.saved_pressure

    def get_saved_temperature(self):
        return self.saved_temperature

    def save_pressure(self, pressure):
        self.saved_pressure = pressure

    def save_temperature(self, temperature):
        self.saved_temperature = temperature

    def set_this_section_current(self, index):
        self.current_section = None
        self.current_section = copy.deepcopy(self.section_lst[index])

    def clear_section_list(self):
        self.section_list[:] = []

    def get_number_of_section(self):
        return self.section_lst.__len__()

    def set_current_section(self, roi):
        x_section_bg, y_section_bg = get_DataSection(
            self.base_ptn.x_bg, self.base_ptn.y_bg, roi)
        __, y_section_bgsub = get_DataSection(
            self.base_ptn.x_bgsub, self.base_ptn.y_bgsub, roi)
        self.current_section.set(x_section_bg, y_section_bgsub, y_section_bg)

    def current_section_exists_in_list(self):
        for section in self.section_lst:
            if self.current_section.get_timestamp() == section.get_timestamp():
                return True
        return False

    def current_section_saved(self):
        if self.get_number_of_section() == 0:
            return False
        if self.current_section.timestamp is None:
            return False
        if self.current_section_exists_in_list():
            return True
        else:
            return False

    def initialize_current_section(self):
        if self.current_section_exist():
            self.current_section = None
        self.current_section = Section()

    def save_current_section(self):
        new_section = copy.deepcopy(self.current_section)
        self.section_lst.append(new_section)
        self.current_section = None

    def current_section_exist(self):
        if self.current_section is None:
            return False
        if self.current_section.x is None:
            return False
        else:
            return True

    def set_from(self, model_r):
        self.base_ptn = model_r.base_ptn
        self.waterfall_ptn = model_r.waterfall_ptn
        self.jcpds_lst = model_r.jcpds_lst
        self.ucfit_lst = model_r.ucfit_lst
        self.diff_img = model_r.diff_img
        self.poni = model_r.poni
        self.session = model_r.session
        self.jcpds_path = model_r.jcpds_path
        self.chi_path = model_r.chi_path
        self.section_lst = model_r.section_lst
        self.saved_pressure = model_r.get_saved_pressure()
        self.saved_temperature = model_r.get_saved_temperature()

    def reset_base_ptn(self):
        self.base_ptn = PatternPeakPo()

    def reset_waterfall_ptn(self):
        self.waterfall_patterns[:] = []

    def reset_jcpds_lst(self):
        self.jcpds_lst[:] = []

    def reset_ucfit_lst(self):
        self.ucfit_lst[:] = []

    def reset_diff_img(self):
        self.diff_img = DiffImg()

    def reset_poni(self):
        self.poni = None

    def base_ptn_exist(self):
        if self.base_ptn is None:
            return False
        else:
            if self.base_ptn.fname is None:
                return False
            else:
                return True

    def waterfall_exist(self):
        if self.waterfall_ptn == []:
            return False
        else:
            return True

    def jcpds_exist(self):
        if self.jcpds_lst == []:
            return False
        else:
            return True

    def ucfit_exist(self):
        if self.ucfit_lst == []:
            return False
        else:
            return True

    def diff_img_exist(self):
        if self.diff_img is None:
            return False
        else:
            return True

    def poni_exist(self):
        if self.poni is None:
            return False
        else:
            return True

    def make_filename(self, extension, original=False):
        """
        :param extension: extension without a dot
        """
        return make_filename(self.base_ptn.fname, extension, original=original)

    def same_filename_as_base_ptn(self, filename):
        return samefilename(self.base_ptn.fname, filename)

    def set_base_ptn(self, new_base_ptn, wavelength):
        """
        :param new_base_ptn: PatternPeakPo object
        """
        self.reset_base_ptn()
        self.base_ptn.read_file(new_base_ptn)
        self.set_chi_path(os.path.split(new_base_ptn)[0])
        self.set_base_ptn_wavelength(wavelength)
        self.base_ptn.display = True

    def get_base_ptn(self):
        return self.base_ptn

    def append_a_waterfall_ptn(self, filename, wavelength,
                               bg_roi, bg_params, temp_dir=None):
        pattern = PatternPeakPo()
        pattern.read_file(filename)
        pattern.wavelength = wavelength
        pattern.display = False
        if temp_dir is None:
            pattern.get_chbg(bg_roi, params=bg_params, yshift=0)
        else:
            success = pattern.read_bg_from_tempfile(temp_dir=temp_dir)
            if not success:
                pattern.get_chbg(bg_roi, params=bg_params, yshift=0)
        self.waterfall_ptn.append(pattern)

    def set_waterfall_ptn(
            self, filenames, wavelength, display, bg_roi, bg_params,
            temp_dir=None):
        new_waterfall_ptn = []
        for f, wl, dp in zip(filenames, wavelength, display):
            pattern = PatternPeakPo()
            pattern.read_file(f)
            pattern.wavelength = wl
            pattern.display = dp
            if temp_dir is None:
                pattern.get_chbg(bg_roi, params=bg_params, yshift=0)
            else:
                success = pattern.read_bg_from_tempfile(temp_dir=temp_dir)
                if not success:
                    pattern.get_chbg(bg_roi, params=bg_params, yshift=0)
            new_waterfall_ptn.append(pattern)
        self.waterfall_ptn = new_waterfall_ptn

    def append_a_jcpds(self, filen, color):
        phase = JCPDSplt()
        phase.read_file(filen)  # phase.file = f
        phase.color = color
        self.jcpds_lst.append(phase)

    def write_as_ppss(self,
                      fname, pressure, temperature):
        session = Session()
        session.pattern = self.get_base_ptn()
        session.waterfallpatterns = self.waterfall_ptn
        session.wavelength = self.base_ptn.wavelength
        session.pressure = pressure
        session.temperature = temperature
        session.jlist = self.jcpds_lst
        session.bg_roi = self.base_ptn.roi
        session.bg_params = self.base_ptn.params_chbg
        session.jcpds_path = self.jcpds_path
        session.chi_path = self.chi_path
        f = open(fname, 'wb')
        pickle.dump(session, f)
        f.close()

    def read_ppss(self, fname):
        f = open(fname, 'rb')
        session = pickle.load(f, encoding='latin1')
        f.close()
        self.session = session

    def set_jcpds_from_ppss(self):
        if self.session is not None:
            self.jcpds_lst = self.session.jlist
        else:
            self.set_jcpds_path('')

    def set_chi_path(self, chi_path):
        self.chi_path = chi_path

    def set_jcpds_path(self, jcpds_path):
        self.jcpds_path = jcpds_path

    def get_base_ptn_wavelength(self):
        return self.base_ptn.wavelength

    def set_base_ptn_wavelength(self, wavelength):
        self.base_ptn.wavelength = wavelength

    def get_base_ptn_filename(self):
        return self.base_ptn.fname

    def set_base_ptn_color(self, color):
        self.base_ptn.color = color

    def associated_image_exists(self):
        filen_tif = self.make_filename('tif', original=True)
        if os.path.exists(filen_tif):
            return True
        else:
            return False

    def load_associated_img(self):
        filen_tif = self.make_filename('tif', original=True)
        self.reset_diff_img()
        self.diff_img.load(filen_tif)
