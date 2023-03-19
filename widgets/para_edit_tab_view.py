#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal

from widgets.panel_area_view import PanelAreaView
from widgets.para_edit_area_view import ParaEditAreaView

from control.para_edit_area_controller import ParaEditAreaController

from utils.qt_util import *



class ParaEditTabView(QtWidgets.QTabWidget):
    """
    编辑区
    """

    def __init__(self, parent=None):
        super(ParaEditTabView, self).__init__()
        self._parent = parent
        self.__init_ui()

    def __init_ui(self):
        if self._parent:
            self.setParent(self._parent)
        self.para_edit_view = ParaEditAreaView(self)
        self.panel_area_view = PanelAreaView(self)

        self.addTab(self.para_edit_view, "a")
        self.addTab(self.panel_area_view, "b")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    _view = ParaEditTabView()
    _view.show()
    sys.exit(app.exec_())
