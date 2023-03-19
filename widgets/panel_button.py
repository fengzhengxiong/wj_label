#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal


class PanelButton(QToolButton):
    """
    触摸板， 鼠标滑动
    """
    signal = pyqtSignal(str, int, str)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._parent = parent
        if self._parent:
            self.setParent(self._parent)

        self.setText(text)

        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(30, 30))
        # self.setMaximumSize(QtCore.QSize(60, 60))

    def mousePressEvent(self, e):
        mods = e.modifiers()
        if Qt.ControlModifier == int(mods):
            fast_flag = 'fast'
        elif Qt.ShiftModifier == int(mods):
            fast_flag = 'slow'
        else:
            fast_flag = 'mid'

        if e.button() == Qt.LeftButton:
            # print(self.text(), 2, fast_flag)
            self.signal.emit(self.text(), 2, fast_flag)
        elif e.button() == Qt.RightButton:
            # print(self.text(), 3, fast_flag)
            self.signal.emit(self.text(), 3, fast_flag)

    def wheelEvent(self, e):
        mods = e.modifiers()
        if Qt.ControlModifier == int(mods):
            fast_flag = 'fast'
        elif Qt.ShiftModifier == int(mods):
            fast_flag = 'slow'
        else:
            fast_flag = 'mid'

        v_delta = e.angleDelta().y()
        if v_delta < 0:
            # print(self.text(), -1, fast_flag)
            self.signal.emit(self.text(), -1, fast_flag)
        else:
            # print(self.text(), 1, fast_flag)
            self.signal.emit(self.text(), 1, fast_flag)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = PanelButton('axiong')
    win.show()
    sys.exit(app.exec_())