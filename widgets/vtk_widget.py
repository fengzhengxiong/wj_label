# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本工程 vtk 对象命名规则:vtk_xxx
"""

import os
import copy
from PyQt5.QtCore import pyqtSignal

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from data.cube_label import CubeLabel
from utils.vtk_util import *
from utils.pub import *
from utils.myqueue import MyQueue

from manager.global_manager import global_manager
from config.label_type import traffic_property_dic



from widgets.vtk_interactor_style import InteractorStyle


class VTK_QWidget(QFrame):

    selectionChanged = pyqtSignal(list)
    cubeMoved = pyqtSignal(list)  # 发生移动对外触发
    newCube = pyqtSignal()  # 新增

    NormalCubeColor = (0.95, 0.1, 0.02)
    HighLightCubeColor = (1, 1, 1)
    SolidCubeColor = (0, 0, 0.8)  # 实心框体的颜色

    ThreeViewsColor = (0.0, 0.05, 0.1)
    AxesLineWidth = 15.0
    NormalCubeLineWidth = 1.3
    SelectCubeLineWidth = 1.0
    ArrowNormalScale = 3  # 默认的箭头缩放尺度

    seq = [0, 1, 2, 3, 0, 4, 5, 6, 7, 4, 5, 1, 2, 6, 7, 3]
    UnitMatrix = vtk.vtkMatrix4x4()  # 单位矩阵
    type_map = {}  # 数据类型映射

    num_backups = 30  # 备份队列长度

    # BG_GRADIENT = 1  # 0 一种颜色，1 两种颜色
    # BG_COLOR1 = (0.3, 0.05, 0.1)
    BG_COLOR2 = (0.2, 0.1, 0.5)

    BG_GRADIENT = 0
    BG_COLOR1 = (0.1, 0.1, 0.1)

    AXES_COLOR = (0.1, 0.9, 0.1)
    POINT_SIZE = 1.0
    POINT_COLOR = (0.7, 0.7, 0.72)

    _axes_show = True
    _boundary_show = True
    _bound_radius = 80.0


    def __init__(self, parent=None):
        super(VTK_QWidget, self).__init__(parent=parent)
        self.parent = parent
        self.resize(1000, 800)

        '''PyQt控件'''
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtkWidget)

        '''VTK渲染'''
        self.window = self.vtkWidget.GetRenderWindow()  # renWin = vtk.vtkRenderWindow()
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()  # iren = vtk.vtkRenderWindowInteractor()
        self.renderer = vtk.vtkRenderer()

        # 背景渐变颜色
        self.renderer.SetGradientBackground(self.BG_GRADIENT)
        self.renderer.SetBackground(*self.BG_COLOR1)
        self.renderer.SetBackground2(*self.BG_COLOR2)
        self.renderer.SetViewport(0.0, 0.0, 1, 1)
        self.window.AddRenderer(self.renderer)

        ''' vtk 对象成员  '''
        # 点云中间数据
        self.vtk_points = None  # vtkPoints
        self.vtk_vertices = None  # vtkCellArray
        self.vtk_depth = None  # vtkFloatArray
        self.vtk_polydata = None  # vtkPolyData
        self.vtk_mapper = None  # vtkPolyDataMapper
        self.vtk_pcdActor = None  # vtkActor  点云

        self.vtk_axes = get_axes_actor(color=self.AXES_COLOR)  # 坐标轴
        if self._axes_show and self.vtk_axes:
            self.renderer.AddActor(self.vtk_axes)

        self.vtk_marker = get_axes_marker_widget(self.interactor)  # 坐标轴marker
        self.vtk_marker.SetEnabled(1)

        self.vtk_boundary = get_boundary_obj(r=self._bound_radius)  # 圆边界
        if self._boundary_show and self.vtk_boundary:
            self.renderer.AddActor(self.vtk_boundary)

        self.vtk_boxWidget = None
        self.vtk_boxWidget = get_box_widget(self.interactor)  # 调节3D框

        self.vtk_camera = vtk.vtkCamera()  # 相机
        self.vtk_camera.SetPosition(0, 0, 80)
        self.vtk_camera.SetFocalPoint(0, 0, 0)
        # self.vtk_camera.SetDistance(90)
        # self.vtk_camera.SetClippingRange(0.5, 80.0)
        self.vtk_camera.SetViewUp(0, 1, 0)
        self.renderer.ResetCamera()
        self.renderer.SetActiveCamera(self.vtk_camera)

        '''添加事件'''
        self.style = InteractorStyle(parent=self.parent, brother=self)

        # self.style.createCube.connect(self.addCube)

        # self.style = vtk.vtkInteractorStyleRubberBandPick()
        self.interactor.SetInteractorStyle(self.style)
        # self.style.set_data(self.PolyData)
        # self.style.SetDefaultRenderer(self.renderer)

        ''' 数据  '''
        # 3D框数据
        self.cubes = []  # CubeLabel ...
        self.selectedCubes = []  # 选中的目标， cubeLabels 元素浅拷贝
        self.selectedCubesCopy = []  # 深拷贝

        # self.cubeBackups = []  # 备份
        self.cubeBackups = MyQueue(max_size=self.num_backups)

        self.pcdArray = None  # 点云 np数组
        self.cubeVisible = {}

        self.interactor.Initialize()
        self.window.Render()
        self.interactor.Start()


    def resetData(self, all=True):
        """
        初始化成员数据
        :return:
        """
        self.selectedCubes = []  # 选中的目标， cubeLabels 元素浅拷贝
        self.selectedCubesCopy = []  # 深拷贝
        # self.cubeBackups = []  # 备份
        self.cubeBackups.reset()
        self.cubeVisible = {}

        if all:
            self.cubes = []
            self.pcdArray = None

    def setPcdData(self, data):
        self.pcdArray = data

    def getPcdData(self):
        return self.pcdArray

    def setLabelData(self, data):
        self.cubes = data

    def getLabelData(self):
        return self.cubes

    def buildPcdActor(self):
        result = get_cloud_point_actor(self.pcdArray, size=self.POINT_SIZE, color=self.POINT_COLOR)
        if result is None:
            return False
        self.vtk_points = result[0]
        self.vtk_vertices = result[1]
        self.vtk_depth = result[2]
        self.vtk_polydata = result[3]
        self.vtk_mapper = result[4]
        self.vtk_pcdActor = result[5]
        return True

    def showCloudPoint(self):
        """显示点云"""
        if self.vtk_pcdActor is None:
            return False
        try:
            self.renderer.AddActor(self.vtk_pcdActor)
            self.renderer.Render()
            # self.updatePointSize(2)
            return True
        except Exception as e:
            print(e)
            return False

    def hideCloudPoint(self):
        """隐藏点云"""
        if self.vtk_pcdActor is not None:
            self.renderer.RemoveActor(self.vtk_pcdActor)
            self.renderer.Render()

    def updatePointSize(self, size=1.0):
        """
        更新点云点的大小
        :param size:
        :return:
        """
        if self.vtk_pcdActor is not None:
            self.POINT_SIZE = size
            self.vtk_pcdActor.GetProperty().SetPointSize(size)
            self.renderer.Render()
            self.refreshVTKDisplay()

    def updateBoundary(self, radius=80, show=True):
        """
        更新边界
        :param radius: 半径大小
        :param show: 是否显示
        :return:
        """
        if self.vtk_boundary is not None:
            self._bound_radius = radius
            self.renderer.RemoveActor(self.vtk_boundary)
            self.renderer.Render()
            self.refreshVTKDisplay()
        self._boundary_show = show

        if self._boundary_show:
            self._bound_radius = radius
            self.vtk_boundary = get_boundary_obj(r=self._bound_radius)  # 圆边界
            if self.vtk_boundary:
                self.renderer.AddActor(self.vtk_boundary)
                self.renderer.Render()
                self.refreshVTKDisplay()
            else:
                print('updateBoundary ，创建错误')

    def loadPcdData(self, data):
        """
        首次加载显示点云
        :param data: 点云数据
        :return:
        """
        self.setPcdData(data)
        ret = self.buildPcdActor()
        if not ret:
            print("buildPcdActor 出错")
            return False
        ret = self.showCloudPoint()
        if not ret:
            print("showCloudPoint 出错")
            return False

    def loadCubeLabel(self, cubes, first=True):
        """
        加载显示3d框
        :param cubes: 标签list
        :param first: 首次加载
        :return:
        """
        self.setLabelData(cubes)
        self.redisplay()
        if first:
            self.storeCubes()  # 首次加载作第一个缓存

    def redisplay(self, force=True):
        """更新标签显示,force 刷新VTK渲染"""
        if not self.cubes:
            return
        for cube in self.cubes:
            cube.updateActorProperty()
            if self.isCubeVisible(cube):
                cube.addByRenderer(self.renderer)
            else:
                cube.removeByRenderer(self.renderer)
        self.renderer.Render()
        if force:
            self.refreshVTKDisplay()


    def isCubeVisible(self, cube):
        return self.cubeVisible.get(cube, True)

    def setCubeVisible(self, cube, val=True):
        self.cubeVisible[cube] = val

    def refreshVTKDisplay(self):
        self.interactor.Initialize()
        self.window.Render()
        self.interactor.Start()

    def closeBoxWidget(self):
        if self.vtk_boxWidget:
            self.vtk_boxWidget.Off()

    def initVTKUI(self):
        """
        初始化UI界面显示
        :return:
        """
        renderer_remove_all(self.renderer)
        if self._axes_show and self.vtk_axes:
            self.renderer.AddActor(self.vtk_axes)
        if self._boundary_show and self.vtk_boundary:
            self.renderer.AddActor(self.vtk_boundary)
        self.closeBoxWidget()
        self.refreshVTKDisplay()


    def initShowPcdCubes(self, pcddata, cubes):
        """
        显示点云和3d框
        :param pcddata:
        :param cubes:
        :return:
        """

        # initVTKUI在前面
        self.initVTKUI()
        self.resetData()

        self.loadPcdData(pcddata)
        self.loadCubeLabel(cubes)
        self.refreshVTKDisplay()

    def reset(self):
        """
        重置
        :return:
        """
        # renderer_remove_all(self.renderer)
        self.resetData()

    def isCubeRestorable(self, undo=True):
        """
        能否回退、下一步
        :param undo:True 回退 ，False 下一步
        :return:
        """
        if undo:
            return self.cubeBackups.isGetLast()
        else:
            return self.cubeBackups.isGetNext()
        # if len(self.cubeBackups) >= 2:
        #     return True
        # return False

    def restoreCube(self, undo=True):
        """
        从备份队列里恢复上一步存储
        :return:
        """
        if not self.isCubeRestorable(undo):
            return
        # 清除显示
        for cube in self.cubes:
            cube.removeByRenderer(self.renderer)
        self.closeBoxWidget()
        # 获取堆栈上一个缓存
        if undo:
            cubesBackup = self.cubeBackups.getLast([])
        else:
            cubesBackup = self.cubeBackups.getNext([])
        # self.cubes = cubesBackup  # 这里不可以直接赋值！！！，否则会被改变
        self.cubes = []
        self.selectedCubes = []
        for cube in cubesBackup:
            c = cube.copy()
            c.selected = False
            self.cubes.append(c)

        print("restoreCube,idx={},len={}".format(self.cubeBackups.index, self.cubeBackups.count()))

        # TODO 暂时默认回退后，所有的框都显示，待CubeLabel里加入隐藏属性后，再更新cubeVisible
        self.cubeVisible = {}
        self.redisplay(True)


    def selectCubes(self, cubes):
        """
        设置选中标签
        :param cubes:
        :return:
        """
        for cube in self.cubes:
            cube.selected = True if cube in cubes else False
        self.selectedCubes = cubes
        self.redisplay(True)  # 给True 鼠标选中后可及时刷新
        self.selectionChanged.emit(cubes)  # 列表更新select 注意屏蔽slot


    def addSelectCubes(self, cubes):
        """
        增加, 选中标签
        :param cubes:
        :return:
        """
        for cube in cubes:
            lst_append_once(self.selectedCubes, cube)
        self.selectCubes(self.selectedCubes)

    def subSelectCubes(self, cubes):
        """
        减少, 选中标签
        :param cubes:
        :return:
        """
        for cube in cubes:
            lst_remove_once(self.selectedCubes, cube)
        self.selectCubes(self.selectedCubes)

    def deSelectCube(self):
        """ 非选中状态  """
        if self.selectedCubes:
            for cube in self.selectedCubes:
                cube.selected = False
                cube.updateActorProperty()
            self.redisplay(True)  # 给True 鼠标选中后可及时刷新
            self.selectionChanged.emit([])


    def deleteSelected(self):
        """删除选中标签"""
        deleted_cubes = []
        if self.selectedCubes:
            for cube in self.selectedCubes:
                cube.removeByRenderer(self.renderer)
                self.cubes.remove(cube)
                deleted_cubes.append(cube)
            self.orderCubes()
            self.storeCubes()
            self.selectedCubes = []
            self.redisplay(True)

        return deleted_cubes

    def addCube(self, data):
        """
        新增框，如果是预先设定的框了，就新增该类型框
        :param data:
        :return:
        """
        # print("addCube, ", data)
        assert isinstance(data, list)
        x,y,z,ang,l,w,h = data
        # TODO 预先设定标签名称可加入
        add_cube = CubeLabel()
        add_cube.cen_x = x
        add_cube.cen_y = y
        add_cube.cen_z = z
        add_cube.angle = ang
        add_cube.length = l
        add_cube.width = w
        add_cube.height = h

        add_label = global_manager.add_traffic_type
        if add_label is not None and add_label in global_manager.traffic_property_dic.keys():
            l, w, h = global_manager.traffic_property_dic[add_label]['scale']
            add_cube.length = l
            add_cube.width = w
            add_cube.height = h
            add_cube.label = add_label
            # print("+++++++++", add_cube.label)

        add_cube.buildActors()

        self.cubes.append(add_cube)
        self.orderCubes()
        self.storeCubes()
        self.redisplay(False)
        self.newCube.emit()

    def moveSelectedCube(self, delta_pos):
        """
        选中的框一起移动一个位移
        :param delta_pos:
        :return:
        """
        for cube in self.selectedCubes:
            cube.cen_x += delta_pos[0]
            cube.cen_y += delta_pos[1]
            cube.cen_z += delta_pos[2]

        self.moveingCube(self.selectedCubes)

    def moveingCube(self, cubes):
        """
        移动框，目前默认单次只能移动一个
        :param cubes:
        :return:
        """
        # print('moveingCube', cubes)
        for cube in cubes:
            # print(cube.length, cube.width,cube.height)
            cube.updatePose()
        self.redisplay(False)
        self.cubeMoved.emit(cubes)

    def endEditCube(self):
        """
        操作3D框结束
        :return:
        """
        self.storeCubes()
        self.redisplay(False)
        self.cubeMoved.emit([])  # 仅是为了完成刷新，更新setDirty 中action使能

    def duplicateSelectedCubes(self):
        """拷贝"""
        if self.selectedCubes:
            self.selectedCubesCopy = [c.copy() for c in self.selectedCubes]
            self.boundedShiftCubes(self.selectedCubesCopy)
            self.endMove(copy=True)
        return self.selectedCubes

    def pasteCubes(self, cubes, update_pos=True):
        """
        粘贴标签
        :param cubes:标签浅拷贝
        :param update_pos: 是否更新粘贴标签的位置
        :return:
        """
        try:
            if update_pos:
                camera = self.renderer.GetActiveCamera()
                fp = camera.GetFocalPoint()  # 相机焦点
                xl = [cube.cen_x for cube in cubes]
                yl = [cube.cen_y for cube in cubes]
                center = [sum(xl) / len(xl), sum(yl) / len(yl)]  # 粘贴标签中心
                offset = [fp[0] - center[0], fp[1] - center[1]]  # 偏移
                for cube in cubes:
                    # cube.cen_x += offset[0]
                    # cube.cen_y += offset[1]
                    cube.updatePose()

            self.cubes.extend(cubes)
            self.orderCubes()
            self.storeCubes()
            self.redisplay(False)

        except Exception as e:
            print(e)

    def boundedShiftCubes(self, cubes):
        """
        仅用于拷贝时产生，偏移
        :param cubes:
        :return:
        """
        for cube in cubes:
            cube.cen_x += cube.width
            cube.cen_y += cube.width

    def endMove(self, copy=False):
        """
        标签移动
        :param copy:
        :return:
        """
        if len(self.selectedCubes) == 0:
            return 
        if len(self.selectedCubes) != len(self.selectedCubesCopy):
            return 
        
        if copy:
            for i, cube in enumerate(self.selectedCubesCopy):
                self.cubes.append(cube)
                self.selectedCubes[i].selected = False  # 选中的切换状态
                self.selectedCubes[i] = cube  # 替换为copy的作为选中的
        else:
            pass
        self.selectedCubesCopy = []
        self.orderCubes()
        self.storeCubes()
        self.redisplay(False)

    def findCube(self, actor, all=True):
        """
        判断是哪个框
        :param actor:
        :return:
        """
        ret = None
        for cube in self.cubes:
            if cube.isMe(actor, all):
                return cube
        return ret

    def setLastCube(self, label=None, id_num=None):
        """
        新增标签后，设置标签
        :param label:
        :param id_num:
        :return:
        """
        if len(self.cubes) == 0:
            print("setLastCube 异常")
            return
        cube = self.cubes[-1]
        cube.label = label if label is not None else cube.label
        cube.id_num = id_num if id_num is not None else cube.id_num
        cube.updatePose()
        # self.cubeBackups.pop()
        self.cubeBackups.getLast()
        self.orderCubes()
        self.storeCubes()
        self.redisplay()
        return cube

    def focusThisCube(self, cube):
        """
        视野看该目标
        :param cube:
        :return:
        """
        d = 80  # 焦点和拍照点的距离 max(2*height, 2*length)
        pos = (cube.cen_x, cube.cen_y, cube.cen_z + d)
        camera = self.renderer.GetActiveCamera()
        camera.SetFocalPoint(cube.cen_x, cube.cen_y, cube.cen_z)
        camera.SetPosition(pos)
        camera.SetViewUp(0, 1, 0)
        self.renderer.SetActiveCamera(camera)
        self.refreshVTKDisplay()

    def storeCubes(self):
        """
        备份
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name, ' ', \
              sys._getframe().f_back.f_code.co_name, ' ', sys._getframe().f_back.f_back.f_code.co_name)

        tmp = []
        for cube in self.cubes:
            tmp.append(cube.copy())
        self.cubeBackups.put(tmp)
        print("storeCubes,idx={},len={}".format(self.cubeBackups.index, self.cubeBackups.count()))
        # print('%%%%%%%%%%%%')
        # for d in self.cubeBackups.data:
        #     print(d[0])
        #     print(d[0].length)
        # print('%%%%%%%%%%%%')

    def orderCubes(self):
        """
        序号更新
        :return:
        """
        if self.cubes:
            for cube in self.cubes:
                cube.order_no = self.cubes.index(cube)

    def closeEvent(self, event):
        self.vtkWidget.Finalize()
        super(VTK_QWidget, self).closeEvent(event)

    # def resizeEvent(self, event):
    #     print('vtk  resizeEvent')
    #     super(VTK_QWidget, self).resizeEvent(event)
    def enterEvent(self, event):
        self.setMouseTracking(True)
        self.setFocus()
        super(VTK_QWidget, self).enterEvent(event)

    def leaveEvent(self, event):
        super(VTK_QWidget, self).leaveEvent(event)
        self.clearFocus()
        self.setMouseTracking(False)


import time


def main():
    from utils.file_manage import read_pcd_file_to_np, read_csv_file

    aa = time.time()
    app = QApplication(sys.argv)
    window = VTK_QWidget()
    #
    # path1 = "../20200809193718_000000.pcd"
    # path2 = "../000002.csv"
    path1 = "C:/Users\wanji\Desktop/000000.pcd"
    path2 = "C:/Users\wanji\Desktop/000000.csv"

    pcd = read_pcd_file_to_np(path1)
    CubeDatas = read_csv_file(path2)

    cubes = []
    for cube in CubeDatas:
        a = CubeLabel()
        a.getDataFromCsv(cube)
        a.buildActors()
        # a.selected = True
        cubes.append(a)
        print(a)

    print(len(cubes))
    b = cubes[0].copy()
    b.cen_x += 5
    b.buildActors()
    cubes.append(b)
    window.initShowPcdCubes(pcd, cubes)

    window.show()
    bb = time.time()
    print('time = ', bb - aa)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
