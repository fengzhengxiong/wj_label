#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal

# from config.label_type import traffic_property_dic
from utils.qt_util import *

from manager.global_manager import global_manager


class TrafficToolView(QtWidgets.QWidget):
    """
    工具添加组件
    """
    traffic_add_signal = pyqtSignal(int)  # 默认添加哪个模式的框

    def __init__(self, parent=None):
        super(TrafficToolView, self).__init__()
        self._parent = parent

        self.button_list = []
        self.btn_val_dic = {}

        self.__init_ui()

    def __init_ui(self):
        if self._parent:
            self.setParent(self._parent)

        self.hbox = QHBoxLayout(self)
        self.hbox.setContentsMargins(1, 1, 1, 1)
        self.hbox.setSpacing(2)

        self.lbl_traffic = QLabel('目标类别预选:')
        self.hbox.addWidget(self.lbl_traffic)
        self.add_buttons()

    def add_buttons(self):
        self.remove_buttons()

        print("traffic_property_dic=  \n",  global_manager.traffic_property_dic)

        for k, v in global_manager.traffic_property_dic.items():
            scale = v.get('scale', None)
            if isinstance(scale, (list, tuple)) and len(scale) == 3:
                btn_ = QToolButton(self)
                btn_.setCheckable(True)
                # btn_.setText("%s-%s" % (str(k), v['name']))
                btn_.setText("%s" % (str(k)))
                btn_.setToolTip("%s-%s %s" % (v['name'], v['ch'], v['scale']))
                self.button_list.append(btn_)
                self.btn_val_dic[btn_] = k

        for b in self.button_list:
            self.hbox.addWidget(b)
            b.clicked.connect(self.button_click_event)


    def remove_buttons(self):
        lay = self.layout()

        for b in self.button_list:
            lay.removeWidget(b)
            b.setParent(None)
            b.clicked.disconnect()
            b.destroy()

        self.button_list = []
        self.btn_val_dic = {}


    def button_click_event(self):
        this_btn = self.sender()
        if this_btn.isChecked():
            self.clear_checked(this_btn)
            self.traffic_add_signal.emit(int(self.btn_val_dic[this_btn]))
        else:
            self.traffic_add_signal.emit(-99)


    def clear_checked(self, without=None):
        for btn in self.button_list:
            if btn != without:
                btn.setChecked(False)





if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    _view = TrafficToolView()
    _view.show()
    sys.exit(app.exec_())