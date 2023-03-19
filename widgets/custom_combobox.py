#!/usr/bin/env python
# -*- coding: utf-8 -*-



from PyQt5 import QtWidgets, QtCore


class CustomComboBox(QtWidgets.QComboBox):
    """
    忽略滚轮
    """
    def __init__(self, parent=None):
        super(CustomComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()
        pass
