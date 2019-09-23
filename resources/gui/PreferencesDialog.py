from PyQt5 import QtWidgets as gui
from PyQt5LayoutGeneration import AutoVBoxLayout


class PreferencesDialog(gui.QDialog):
    def __init__(self):
        super().__init__()

        self.init_gui()

    def init_gui(self):
        # create preferences form
        self.setLayout()
