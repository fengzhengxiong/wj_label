#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import numpy as np
import sys
import copy
from PyQt5.QtWidgets import *

from widgets.para_edit_area_view import ParaEditAreaView
from widgets.para_edit_widget_ import EditWidget_

# from config.label_type import label_csv_dic
from manager.global_manager import global_manager
from utils.pub import *


class ParaEditAreaController(object):
    def __init__(self, view=None, model=None, *args, **kwargs):
        super(ParaEditAreaController, self).__init__()
        if view is not None:
            self._view = view
        else:
            self._view = ParaEditAreaView()
        try:
            self.init_view()

            self.reload_widget()
            pass
        except Exception as e:
            print(e)

    def init_view(self):
        """
        在原有视图基础上进行编辑
        :return:
        """
        _map_dic = copy.deepcopy(global_manager.label_csv_dic)

        for k in ["cen_x", "cen_y", "cen_z", "angle", "length", "width", "height"]:
            dic_pop(_map_dic, k)

        # 创建属性列表
        self.wid_list = []

        for k, v in _map_dic.items():
            label = v["ch"]
            if isinstance(v["val"], dict):
                mode = 'QComboBox'
                ew = EditWidget_(label, mode, parent=self._view.wid_)  # 加上parent 按钮显示正常
                strlist = []
                datalist = []
                colorlist = []
                for a, b in v["val"].items():  # 1:  {"des": "普通道路", "rgb": (10, 240, 10)},
                    strlist.append("%d - %s" % (a, b["name"]))
                    datalist.append(a)
                    if "color" in b:
                        colorlist.append(b["color"])
                ew.set_combo_attr(strlist, datalist, colorlist)

            elif isinstance(v["val"], (int, float)):
                mode = "QLineEdit"
                ew = EditWidget_(label, mode, parent=self._view.wid_)  # 加上parent 按钮显示正常
                ew.set_lineedit_number()

            else:
                mode = "QLineEdit"
                ew = EditWidget_(label, mode, parent=self._view.wid_)  # 加上parent 按钮显示正常
                ew.set_lineedit_number()

            ew.set_user_data(k)  # 把当前项在txt所属列号，保存下来。
            self.wid_list.append(ew)

        for wid in self.wid_list:
            self._view.vbox.addWidget(wid)

    def __init_connect(self):

        pass

    def set_view(self, view):
        if isinstance(view, ParaEditAreaView):
            self._view = view

    def get_view(self):
        return self._view

    def set_model(self, model):
        pass

    def set_edit_value(self, name, val):
        for ew in self.wid_list:
            if ew.get_user_data() == name:
                ew.set_value(val)
                break

    def reload_widget(self):
        """
        重新装填控件
        :return:
        """

        for wid in self.wid_list:
            self._view.vbox.removeWidget(wid)
            wid.setParent(None)
            wid.destroy()
        self.init_view()




    def run(self):
        self._app = QApplication(sys.argv)
        self._view.show()
        return self._app.exec_()

    def show(self):
        self._view.show()


# if __name__ == "__main__":
#     v = ParaEditAreaView()
#     c = ParaEditAreaController(v)
#     # c.run()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    _view = ParaEditAreaView()
    c = ParaEditAreaController(_view)
    c.show()
    sys.exit(app.exec_())
