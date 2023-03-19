#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal

from widgets.panel_button import PanelButton
from utils.qt_util import *


def set_slid_attr(obj):
    if not isinstance(obj, QSlider):
        return
    obj.setStyleSheet("")
    obj.setSliderPosition(0)
    obj.setOrientation(QtCore.Qt.Horizontal)
    obj.setInvertedControls(False)
    obj.setTickPosition(QtWidgets.QSlider.NoTicks)
    obj.setTickInterval(0)



class PanelAreaView(QtWidgets.QWidget):
    """
    编辑区
    """

    move_change_signal = pyqtSignal(int)
    stretch_change_signal = pyqtSignal(int)

    moving_signal = pyqtSignal(str, int, str)

    def __init__(self, parent=None):
        super(PanelAreaView, self).__init__()
        self._parent = parent
        self.__init_ui()
        self.__init_connect()

    def __init_ui(self):
        if self._parent:
            self.setParent(self._parent)

        self.btns = QWidget(self)
        self.gbx_sen = QGroupBox(self)
        self.gbx_sen.setTitle("灵敏度调节")

        fill_widget(self, 2, [self.btns,  self.gbx_sen])

        # 布局 ------------------
        self.btn_lr = PanelButton(text='左右', parent=self)
        self.btn_fb = PanelButton(text='前后', parent=self)
        self.btn_ud = PanelButton(text='上下', parent=self)
        self.btn_turn = PanelButton(text='90', parent=self)

        tip = '鼠标左右键拉伸，滚轮移动，Ctrl+ 快速，Shift + 迟缓'
        self.btn_lr.setToolTip(tip)
        self.btn_fb.setToolTip(tip)
        self.btn_ud.setToolTip(tip)
        self.btn_turn.setToolTip(tip)

        gridLayout = QGridLayout(self.btns)
        gridLayout.setContentsMargins(1, 1, 1, 1)
        gridLayout.setHorizontalSpacing(1)
        gridLayout.setVerticalSpacing(1)
        gridLayout.setObjectName("gridLayout")
        #
        # 控件网格布局设置  控件，占用行列
        grid_wids = [
            [(self.btn_fb, 1, 1), (self.btn_lr, 1, 1)],
            [(self.btn_ud, 1, 1), (self.btn_turn, 1, 1)],
        ]
        fill_grid_layout(gridLayout, grid_wids)

        self.lbl_move = QLabel("移动", self.gbx_sen)
        self.lbl_stretch = QLabel("拉伸", self.gbx_sen)

        self.slid_move = QSlider(self.gbx_sen)
        self.slid_stretch = QSlider(self.gbx_sen)

        set_slid_attr(self.slid_move)
        set_slid_attr(self.slid_stretch)

        grid2 = QGridLayout(self.gbx_sen)
        grid2.setContentsMargins(5, 1, 5, 1)
        grid2.setHorizontalSpacing(10)
        grid2.setVerticalSpacing(8)

        grid2.setColumnStretch(0, 3)
        grid2.setColumnStretch(1, 5)
        grid_wids = [
            [(self.lbl_move, 1, 1), (self.slid_move, 1, 1)],
            [(self.lbl_stretch, 1, 1), (self.slid_stretch, 1, 1)],
        ]

        fill_grid_layout(grid2, grid_wids)

    def __init_connect(self):
        self.slid_move.valueChanged.connect(self.change_move)
        self.slid_stretch.valueChanged.connect(self.change_stretch)
        self.btn_fb.signal.connect(self.moving_signal.emit)
        self.btn_lr.signal.connect(self.moving_signal.emit)
        self.btn_ud.signal.connect(self.moving_signal.emit)
        self.btn_turn.signal.connect(self.moving_signal.emit)



    def change_move(self, val):
        self.lbl_move.setText("移动 %s" % val)
        self.move_change_signal.emit(val)

    def change_stretch(self, val):
        self.lbl_stretch.setText("拉伸 %s" % val)
        self.stretch_change_signal.emit(val)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    _view = PanelAreaView()
    _view.show()
    sys.exit(app.exec_())
