#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, Qt, QRegExp
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QRegExpValidator, QColor

from widgets.custom_combobox import CustomComboBox


class EditWidget_(QtWidgets.QWidget):
    """
    自定义组合控件
    """

    " 按钮触发 ，LINE 字符串  COMBO 发当前index  SPIN 发出值"
    click_signal = pyqtSignal(list)


    def __init__(self, label='title', mode='QSpinBox', parent=None, user_data=None):
        super(EditWidget_, self).__init__()

        if parent:
            self._parent = parent
            self.setParent(self._parent)

        self.data = user_data  # 控件存储的数据

        wid_dic = {
            'QLineEdit': QLineEdit(),
            'QComboBox': CustomComboBox(),
            'QSpinBox': QSpinBox(),
            'QDoubleSpinBox': QDoubleSpinBox(),
        }
        self._mode = mode

        self.label = QLabel(self)
        self.label.setText(label)
        self.edit = wid_dic.get(self._mode, QLineEdit())
        self.edit.setParent(self)

        # if isinstance(self.edit, QComboBox):
        #     self.edit.(False)

        self.button = QPushButton(self)
        self.button.setText('确认')

        # self.edit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        self.__init_ui()
        self.__init_connect()

        # self.set_lineedit_attr(False, (1, 12.0))
        # self.set_spin_attr(0.1, (-5, 10))

    def __init_ui(self):
        # 布局
        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(2, 2, 2, 2)
        self.lay.setSpacing(6)

        self.lay.addWidget(self.label)
        self.lay.addWidget(self.edit)
        self.lay.addWidget(self.button)
        self.lay.setStretch(0, 3)
        self.lay.setStretch(1, 10)
        self.lay.setStretch(2, 1)

    def __init_connect(self):
        self.button.clicked.connect(self.button_click)

    def button_click(self):
        """
        按钮触发
        :return:
        """
        res = []
        if isinstance(self.edit, QLineEdit):
            res = [self.edit.text()]
        elif isinstance(self.edit, QComboBox):
            res = [self.edit.currentData(Qt.UserRole)]
        elif isinstance(self.edit, (QSpinBox, QDoubleSpinBox)):
            res = [self.edit.value()]

        res = [self] + res
        # print('res = ', res)
        self.click_signal.emit(res)

    def get_mode(self):
        return self._mode

    def set_label(self, text):
        self.label.setText(str(text))

    def get_label(self):
        return self.label.text()

    def set_user_data(self, user_data):
        self.data = user_data

    def get_user_data(self):
        return self.data

    def set_lineedit_number(self):
        """
        只允许输入数字
        :return:
        """
        # self.edit.setValidator(QRegExpValidator(QRegExp("[A-Za-z][1-9][0-9]{0,2}"),self))#设置验证器
        # self.edit.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9]+${5}"),self))#设置验证器
        # self.edit.setValidator(QRegExpValidator(QRegExp("[0-9]*$"),self))#输入数字，没有限制位数
        # self.edit.setValidator(QRegExpValidator(QRegExp("[0-9]{12}"),self))#最多只能输入12位数字
        # self.edit.setValidator(QRegExpValidator(QRegExp("^[\u4e00-\u9fa5]{0,}$"),self))#输入汉字
        # self.edit.setValidator(QRegExpValidator(QRegExp("^[\u4e00-\u9fa5]{6}"),self))#输入汉字，限制6
        if not isinstance(self.edit, QLineEdit):
            return

        self.edit.setValidator(QRegExpValidator(QRegExp("^(-?[0]|-?[1-9][0-9]{0,8})(?:\\.\\d{1,4})?$|(^\\t?$)"), self))

    def set_lineedit_attr(self, isInt, range=(0, 99)):
        """ 设置输入控件 输入项"""
        if not isinstance(self.edit, QLineEdit):
            return

        if isInt:
            intValidator = QIntValidator()
            intValidator.setRange(range[0], range[1])
            self.edit.setValidator(intValidator)

        else:
            doubleValidator = QDoubleValidator()
            doubleValidator.setRange(range[0], range[1])
            doubleValidator.setDecimals(3)
            doubleValidator.setNotation(QDoubleValidator.StandardNotation)

            self.edit.setValidator(doubleValidator)

        self.edit.update()

    def set_spin_attr(self, step=1, range=(0, 99)):
        """设置spin 输入属性"""
        if isinstance(self.edit, QDoubleSpinBox):
            self.edit.setDecimals(2)
            self.edit.setSingleStep(step)
            self.edit.setRange(range[0], range[1])

        elif isinstance(self.edit, QSpinBox):
            try:
                _step = max(1, int(step))
            except Exception:
                _step = 1

            self.edit.setSingleStep(_step)
            self.edit.setRange(range[0], range[1])

    def set_combo_attr(self, strlist, datalist=None, colorlist=None):
        """
        设置下拉框内容
        :param strlist:
        :return:
        """
        # if isinstance(self.edit, QComboBox):
        #     self.edit.clear()
        #     self.edit.addItems(strlist)

        if isinstance(self.edit, QComboBox):
            model = QtGui.QStandardItemModel()
            self.edit.setModel(model)
            for i in range(len(strlist)):
                self.edit.addItem(strlist[i])
                if datalist:
                    model.item(i).setData(datalist[i], Qt.UserRole)
                if colorlist:
                    c = colorlist[i]
                    model.item(i).setBackground(QColor(c[0], c[1], c[2]))


    def set_value(self, val):
        if isinstance(self.edit, QComboBox):
            for i in range(self.edit.count()):
                if val == self.edit.itemData(i, Qt.UserRole):
                    self.edit.setCurrentIndex(i)
                    # print('11111111111111')
                    break
        elif isinstance(self.edit, (QSpinBox, QDoubleSpinBox)):
            self.edit.setValue(val)
        elif isinstance(self.edit, QLineEdit):
            # print('2222222222222')
            self.edit.setText(str(val))
        else:
            pass


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    _view = EditWidget_(label='axiong',mode='QSpinBox')
    _view.set_combo_attr(strlist=['a', 'b', 'c'])
    _view.show()
    sys.exit(app.exec_())