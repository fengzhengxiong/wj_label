# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
三视图控件，分两页，1页3个vtk 2页3个canvas
"""
import sys

from PyQt5 import QtWidgets, QtCore, QtGui

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
from widgets.vtk_view import VTK_View
from widgets.view_canvas import CanvasView

# ---------------------------------------------------------------
# axiong test  专用
# from utils.file_manage import read_pcd_file_to_np, read_csv_file
# from data.cube_label import CubeLabel
# axiong_path1 = "C:/Users\wanji\Desktop/000000.pcd"
# axiong_path2 = "C:/Users\wanji\Desktop/000000.csv"
# axiong_pcd = read_pcd_file_to_np(axiong_path1)
# axiong_CubeDatas = read_csv_file(axiong_path2)
# axiong_cubes=[]
# for cube in axiong_CubeDatas:
#     a = CubeLabel()
#     a.getDataFromCsv(cube)
#     a.buildActors()
#     axiong_cubes.append(a)
# -----------------------------------------------------------------

class ViewWidget(QStackedWidget):

    def __init__(self, parent=None):
        super(ViewWidget, self).__init__(parent)
        self.parent = parent

        self.setMinimumSize(QtCore.QSize(180, 250))
        self.setMaximumSize(QtCore.QSize(2000, 16777215))
        self.setObjectName("ViewWidget")
        self.page1 = QtWidgets.QWidget()
        self.page1.setObjectName("page1")
        self.page2 = QtWidgets.QWidget()
        self.page2.setObjectName("page2")
        self.addWidget(self.page1)
        self.addWidget(self.page2)


        self.vtk_viewList = []
        dicViewMode = {
            0: VTK_View.V_FRONT,
            1: VTK_View.V_SIDE,
            2: VTK_View.V_BIRD,
        }
        lay = QVBoxLayout(self.page1)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(1)
        for i in range(3):
            tmp_view = VTK_View()
            tmp_view.setViewMode(dicViewMode[i])
            # ---------------------------------------------------
            # axiong  test  专用
            # tmp_view.initShowPcdCubes(axiong_pcd,axiong_cubes)
            # ---------------------------------------------------
            lay.addWidget(tmp_view)
            self.vtk_viewList.append(tmp_view)

        # 三视图qt
        lay = QVBoxLayout(self.page2)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(1)
        self.canvas_viewList = []
        for i in range(3):
            tmp_view = CanvasView()
            tmp_view.setViewMode(dicViewMode[i])
            lay.addWidget(tmp_view)
            self.canvas_viewList.append(tmp_view)

        self.setCurrentIndex(1)

        for i in range(3):
            self.canvas_viewList[i].zoomView.connect(self.adjustViewRatio)

        # self.show()

    def updateVtkView(self, index=None):
        """
        vtk三视图更新
        :param index:
        :return:
        """
        for i in range(len(self.vtk_viewList)):
            self.vtk_viewList[i].updateView(change_view=(i != index))

    def updateCanvasView(self, index=None):
        """
        更新三视图图像
        :param index: index = 0 1 2 时，当前控件只刷新背景图
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        for i in range(3):
            self.canvas_viewList[i].setImage(self.vtk_viewList[i].getScreen())
            if index is None or i != index:
                self.canvas_viewList[i].setPoints(self.vtk_viewList[i].getPixPoints())

    def updateThreeView(self, index=None):
        # 三视图数据变化
        self.updateVtkView(index)
        self.updateCanvasView(index)

    def syncViewSize(self):
        """同步刷新三视图尺寸"""
        self.setCurrentIndex(0)
        self.setCurrentIndex(1)
        self.updateThreeView()

    def adjustViewRatio(self, mode, value):
        """
        调整视图比例， 由滚轮触发
        :param mode: 三视图
        :param value:
        :return:
        """
        modes = [v._view_mode for v in self.vtk_viewList]
        if not mode in modes:
            return

        idx = modes.index(mode)
        wid = self.vtk_viewList[idx]
        if value > 0:
            wid.RATIO += 0.05
        else:
            wid.RATIO -= 0.05
            wid.RATIO = np.clip(wid.RATIO, 0.1, 1.5)
        self.syncViewSize()

    def resizeEvent(self, ev):
        self.syncViewSize()
        super(ViewWidget, self).resizeEvent(ev)

    def closeEvent(self, event):
        for view_wid in self.vtk_viewList:
            view_wid.vtkWidget.Finalize()
        super(ViewWidget, self).closeEvent(event)



if __name__=="__main__":
    app=QApplication(sys.argv)
    win=ViewWidget()
    win.show()
    sys.exit(app.exec_())

