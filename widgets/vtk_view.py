# !/usr/bin/env python
# -*- coding: utf-8 -*-
# VTK视图控件

import os
import copy
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPushButton

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


from data.cube_label import CubeLabel
from utils.vtk_util import *
from utils.pub import *
from utils.util import *

# import cv2


class VTK_View(QFrame):


    V_BIRD = 0
    V_FRONT = 1
    V_SIDE = 2

    BG_GRADIENT = 0  # 0 一种颜色，1 两种颜色
    BG_COLOR1 = (0.1, 0.1, 0.1)
    BG_COLOR2 = (0.2, 0.1, 0.5)
    POINT_SIZE = 1.1
    POINT_COLOR = (0.9, 0.8, 0.7)

    CLIP_EPS = 0.01  # 相机截面冗余
    RATIO = 0.6  # 框在视图中的占比，初步设置为60%

    # 三维向二维映射
    dicWorldToPixMap = {
        V_BIRD: {
            'width': 'width',
            'height': 'length',
        },
        V_FRONT: {
            'width': 'width',
            'height': 'height',
        },
        V_SIDE: {
            'width': 'length',
            'height': 'height',
        }
    }


    def __init__(self, parent=None):
        super(VTK_View, self).__init__(parent=parent)
        self.parent = parent
        if not self.parent:
            self.resize(400, 400)

        '''PyQt控件'''
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtkWidget)

        # self.show()

        '''VTK渲染'''
        self.window = self.vtkWidget.GetRenderWindow()  # renWin = vtk.vtkRenderWindow()
        # self.window.SetSize(self.size().width(), self.size().height())
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()  # iren = vtk.vtkRenderWindowInteractor()
        self.renderer = vtk.vtkRenderer()

        # 背景渐变颜色
        self.renderer.SetGradientBackground(self.BG_GRADIENT)
        self.renderer.SetBackground(*self.BG_COLOR1)
        if self.BG_GRADIENT:
            self.renderer.SetBackground2(*self.BG_COLOR2)
        self.renderer.SetViewport(0.0, 0.0, 1, 1)
        self.window.AddRenderer(self.renderer)

        ''' vtk 对象成员  '''
        # 点云中间数据

        self.vtk_pcdActor = None  # vtkActor  点云

        self.vtk_camera = vtk.vtkCamera()  # 相机
        self.vtk_camera.SetParallelProjection(1)
        self.renderer.ResetCamera()
        self.renderer.SetActiveCamera(self.vtk_camera)

        self.vtk_textActor = get_text_actor(text='bird view')

        '''添加事件'''
        # self.style = InteractorStyle(parent=self.parent, brother=self)
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.style)

        self.cube = None  # 3D框对象， 用于接收外部对象
        self.cubeDisp = CubeLabel()  # 显示对象

        self.pcdArray = None  # 点云 np数组
        self._view_mode = 0  # 视图模式，俯视、侧视、前视

        self.screenImg = None  # 截屏数组
        self.points = []  # 框，2D数据

        self.interactor.Initialize()
        self.window.Render()
        self.interactor.Start()

    def getWindowSize(self):
        """
        尺寸
        window 默认尺寸是100，30 ，执行show()后刷新
        布局边距设置为0
        :return:
        """
        # print('getWindowSize', self.window.GetSize())
        return (self.size().width(), self.size().height())
        # return self.window.GetSize()

    def setViewMode(self, mode=V_BIRD):
        """
        设置视图模式
        :param mode:
        :return:
        """
        self._view_mode = mode

    def setPcdSize(self, size=1.0):
        """
        调整点云大小
        :param size:
        :return:
        """
        # TODO 改变点云大小，能默认大小
        # TODO 修改视野占比，能默认回占比
        pass

    def setCameraView(self):
        """
        设置相机视角
        :return:
        """

        if self.cube is None or not isinstance(self.cube, CubeLabel):
            # print("setCameraView  ---no cube")
            return False

        (focal, dis, pos, vec, clip, scale) = self.getCameraPara(self._view_mode)

        self.renderer.ResetCamera()
        cam = self.vtk_camera
        cam.SetFocalPoint(*focal)
        cam.SetPosition(*pos)
        cam.SetViewUp(*vec)
        cam.SetParallelProjection(1)
        cam.SetDistance(dis)
        cam.SetClippingRange(*clip)
        cam.SetParallelScale(scale)
        self.renderer.SetActiveCamera(cam)
        self.renderer.Render()

    def getCameraPara(self, view_mode=V_BIRD):
        """
        三视图计算相机参数
        :param view_mode:
        :return:
        """
        x, y, z = self.cubeDisp.cen_x, self.cubeDisp.cen_y, self.cubeDisp.cen_z
        theta = self.cubeDisp.angle
        le, w, h = self.cubeDisp.length, self.cubeDisp.width, self.cubeDisp.height
        if view_mode == self.V_BIRD:
            focal = (x, y, z + 0.5 * h)  # 焦点
            dis = 10.0
            pos = (x, y, z + 0.5 * h + dis)  # 光心
            vec = (np.cos(np.deg2rad(theta)), np.sin(np.deg2rad(theta)), 0)  # 相机方向
            clip = (dis - self.CLIP_EPS, dis + h + self.CLIP_EPS)  # 截面
            scale = self.calScale()
        elif view_mode == self.V_FRONT:
            dirflag = 1  # 前视图
            if dirflag:
                vx = np.cos(np.deg2rad(theta))
                vy = np.sin(np.deg2rad(theta))
            else:
                vx = np.cos(np.deg2rad(theta - 180.0))
                vy = np.sin(np.deg2rad(theta - 180.0))
            r = le / 2
            focal = (x + r * vx, y + r * vy, z)
            dis = 10
            pos = (focal[0] + dis * vx, focal[1] + dis * vy, focal[2])
            vec = (0, 0, 1.0)  # 相机方向
            clip = (dis - self.CLIP_EPS, dis + le + self.CLIP_EPS)  # 截面
            scale = self.calScale()

        else:
            dirflag = 0  # 右视图
            if dirflag:
                vx = np.cos(np.deg2rad(theta + 90.0))
                vy = np.sin(np.deg2rad(theta + 90.0))
            else:
                vx = np.cos(np.deg2rad(theta - 90.0))
                vy = np.sin(np.deg2rad(theta - 90.0))
            r = w / 2
            focal = (x + r * vx, y + r * vy, z)
            dis = 10
            pos = (focal[0] + dis * vx, focal[1] + dis * vy, focal[2])
            vec = (0, 0, 1.0)  # 相机方向
            clip = (dis - self.CLIP_EPS, dis + w + self.CLIP_EPS)  # 截面
            scale = self.calScale()

        return (focal, dis, pos, vec, clip, scale)



    def calScale(self):
        """
        计算相机视野比例
        :return:
        """
        scale = 0.8 * self.cube.height
        win_w, win_h = self.getWindowSize()
        # print(win_w, win_h)
        if self._view_mode == self.V_BIRD:
            # 宽度对应比例求解
            k = win_w * self.RATIO / self.cube.width  # 像素与实际尺度比例，单位  pix/m
            scal_w = 0.5 * win_h / k

            # 高度对应比例求解
            k = win_h * self.RATIO / self.cube.length  # 像素与实际尺度比例，单位  pix/m
            scal_h = 0.5 * win_h / k
            # print('V_BIRD   ', scal_w, scal_h)
            scale = max(scal_w, scal_h)  # scale 越大，画面显示的框越小

        elif self._view_mode == self.V_FRONT:
            # 宽度对应比例求解
            k = win_w * self.RATIO / self.cube.width  # 像素与实际尺度比例，单位  pix/m
            scal_w = 0.5 * win_h / k

            # 高度对应比例求解
            k = win_h * self.RATIO / self.cube.height  # 像素与实际尺度比例，单位  pix/m
            scal_h = 0.5 * win_h / k
            scale = max(scal_w, scal_h)

        elif self._view_mode == self.V_SIDE:
            # 宽度对应比例求解
            k = win_w * self.RATIO / self.cube.length  # 像素与实际尺度比例，单位  pix/m
            scal_w = 0.5 * win_h / k

            # 高度对应比例求解
            k = win_h * self.RATIO / self.cube.height  # 像素与实际尺度比例，单位  pix/m
            scal_h = 0.5 * win_h / k
            # print(scal_w, scal_h)
            scale = max(scal_w, scal_h)

        return scale

    def resetData(self, all=True):
        """
        初始化成员数据
        :return:
        """
        self.cube = None
        if all:
            self.vtk_pcdActor = None
            self.pcdArray = None

    def setPcdData(self, data):
        self.pcdArray = data

    def getPcdData(self):
        return self.pcdArray

    def setLabelData(self, data):
        """
        设置深拷贝，单独建立对象
        显示用cubeDisp
        :param data:
        :return:
        """
        if isinstance(data, list):
            if len(data) == 0:
                self.cube = None
            else:
                self.cube = data[0]
        elif isinstance(data, CubeLabel):
            self.cube = data
        else:
            self.cube = None
            # print("setLabelData error", data)

        if self.cube is not None:
            self.cubeDisp.shadowCopy(self.cube)
            self.cubeDisp.isInView = True
            self.cubeDisp.updateActorProperty()

    def getLabelData(self):
        return self.cube


    def buildPcdActor(self):
        result = get_cloud_point_actor(self.pcdArray, size=self.POINT_SIZE, color=self.POINT_COLOR)
        if result is None:
            return False
        self.vtk_pcdActor = result[5]
        return True

    def showCloudPoint(self):
        """显示点云"""
        if self.vtk_pcdActor is None:
            return False
        try:
            self.renderer.AddActor(self.vtk_pcdActor)
            self.renderer.Render()
            self.refreshVTKDisplay()
            return True
        except Exception as e:
            print(e)
            return False

    def hideCloudPoint(self):
        """隐藏点云"""
        if self.vtk_pcdActor is not None:
            self.renderer.RemoveActor(self.vtk_pcdActor)
            self.renderer.Render()

    def updatePointSize(self, size=5.0):
        """
        更新点云点的大小
        :param size:
        :return:
        """
        if self.vtk_pcdActor is not None:
            self.vtk_pcdActor.GetProperty().SetPointSize(size)
            self.renderer.Render()
            self.refreshVTKDisplay()

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
        self.screenImg = getVtkWindowScreen(self.window)
        if not ret:
            print("showCloudPoint 出错")
            return False

    def loadCubeLabel(self, cubes):
        """加载显示3d框"""
        self.setLabelData(cubes)
        self.setCameraView()
        self.redisplay()

        # 发送图像信息
        self.screenImg = getVtkWindowScreen(self.window)
        # if self.cube:
        #     self.screenImg = getVtkWindowScreen(self.window)


    def redisplay(self, force=True):
        """更新标签显示,force 刷新VTK渲染"""
        if self.cube is None:
            # 如果self.cube为None ，不予显示框
            self.cubeDisp.removeByRenderer(self.renderer)
        else:
            self.cubeDisp.addByRenderer(self.renderer)

        self.renderer.Render()
        if force:
            self.refreshVTKDisplay()

    def refreshVTKDisplay(self):
        self.interactor.Initialize()
        self.window.Render()
        self.interactor.Start()

    def initVTKUI(self):
        """
        初始化UI界面显示
        :return:
        """
        renderer_remove_all(self.renderer)
        self.refreshVTKDisplay()

    def initShowPcdCubes(self, pcddata, cubes):
        """
        显示点云和3d框
        :param pcddata:
        :param cubes: 暂时以列表传入，实际只有一个
        :return:
        """

        # initVTKUI在前面
        self.initVTKUI()
        self.resetData()

        self.loadPcdData(pcddata)
        self.loadCubeLabel(cubes)
        self.refreshVTKDisplay()

    def initShowPcd(self, pcd):
        """
        初始化显示点云
        :param pcd:
        :return:
        """
        # initVTKUI在前面，先将actor从renderer移除
        self.initVTKUI()
        self.resetData()
        self.loadPcdData(pcd)


    def updateView(self, cube=None, change_view=False):
        """
        更新显示:切换cube，调整cube，切换视角
        :param cube: None 不变更框
        :param change_view: 是否刷新相机视角
        :return:
        """
        if cube and cube != self.cube:
            self.setLabelData(cube)
        else:
            if self.cube is not None:
                self.cubeDisp.shadowCopy(self.cube)  # 依然显示当前框视图，未切换

        if change_view:
            self.setCameraView()
            self.redisplay(True)
        else:
            self.redisplay(True)
        self.screenImg = getVtkWindowScreen(self.window)

    def changeScale(self, scale=10.0):
        """
        改变图像放大缩小
        :return:
        """
        # self.RATIO

        # self.vtk_camera.GetParallelScale()
        # pass
        self.updateView(change_view=True)


    def getScreen(self):
        """
        获得图像信息
        :return:
        """
        return self.screenImg

    def getPixPoints(self):
        """
        获得图像框，四个顶点像素坐标
        :return:
        """
        if self.cube is None:
            return []
        self.window.SetSize(self.size().width(), self.size().height())
        # print('===================================================================')
        # print(self.size().width(),self.size().height())
        pos = self.cubeDisp.getCenterPos()
        # print('axiong ::: test::: pos: ',pos)
        pix_cen = world_to_display(self.renderer, pos, flg=0)
        # print('axiong ::: test :::   pix_cen1=', pix_cen)

        k = self.getPixRatio()
        trans_map = self.dicWorldToPixMap[self._view_mode]
        # print('axiong   ::: trans_map:  ',trans_map)
        box_w = getattr(self.cubeDisp, trans_map['width'])
        # print('axiong ::: box_w ::: ',box_w)
        box_w = k * box_w
        box_h = getattr(self.cubeDisp, trans_map['height'])
        # print('axiong ::: box_h ::: ',box_h)
        box_h = k * box_h

        self.points = calulate_rect(pix_cen, box_w, box_h, [])
        # print('axiong ::: test ::: four_points: ',self.points)
        return self.points

    # 20221110 axiong add
    # def getNewPixPointsPcd(self):
    #     """
    #     用来把像素坐标转换为世界坐标系下的立方体
    #     """
    #     result=[]
    #     for i in range(len(self.points)):
    #         point=self.points[i]
    #         newpoint=display_to_world(self.renderer, point, flg=0)
    #         result.append(newpoint)
    #     return result

    # def getNewPixPoints(self,view_mode,ids,min_x,max_x,min_y,max_y,min_z,max_z):
    #     """
    #     获得图像框，右键点击拉伸点，后新的四个顶点像素坐标
    #     view_mode:三视图的模式索引,区分主视图左视图俯视图
    #     ids:用来记录点击的是那一个点，以便矩形做相应的调整
    #     #  ------1------
    #     # |     |     |
    #     # 0-----|-----2
    #     # |     |     |
    #     # ------3------
    #     min_x,max_x,min_y,max_y,min_z,max_z:pcd文件中点云的边界，在相应三视图中用相应的两组即可
    #     :return:
    #     """
    #     # 先获取8个边缘点对应的像素坐标
    #     point1 = world_to_display(self.renderer, (min_x, min_y, min_z), flg=0)
    #     point2 = world_to_display(self.renderer, (min_x, min_y, max_z), flg=0)
    #     point3 = world_to_display(self.renderer, (min_x, max_y, min_z), flg=0)
    #     point4 = world_to_display(self.renderer, (min_x, max_y, max_z), flg=0)
    #     point5 = world_to_display(self.renderer, (max_x, min_y, min_z), flg=0)
    #     point6 = world_to_display(self.renderer, (max_x, min_y, max_z), flg=0)
    #     point7 = world_to_display(self.renderer, (max_x, max_y, min_z), flg=0)
    #     point8 = world_to_display(self.renderer, (max_x, max_y, max_z), flg=0)
    #     point_1 = []
    #     point_1.append(point1[0])
    #     point_1.append(point2[0])
    #     point_1.append(point3[0])
    #     point_1.append(point4[0])
    #     point_1.append(point5[0])
    #     point_1.append(point6[0])
    #     point_1.append(point7[0])
    #     point_1.append(point8[0])
    #     point_2 = []
    #     point_2.append(point1[1])
    #     point_2.append(point2[1])
    #     point_2.append(point3[1])
    #     point_2.append(point4[1])
    #     point_2.append(point5[1])
    #     point_2.append(point6[1])
    #     point_2.append(point7[1])
    #     point_2.append(point8[1])
    #     min_point_1,max_point_1=min(point_1),max(point_1)
    #     min_point_2,max_point_2=min(point_2),max(point_2)
    #
    #     if ids==0:
    #         point=self.points[0]
    #         nextpoint=self.points[3]
    #         if abs(point[0] - min_point_1) < 1000:
    #             point[0]=min_point_1
    #             nextpoint[0]=min_point_1
    #             self.points[0]=point
    #             self.points[3]=nextpoint
    #         else:
    #             print('距离太大了，我整不了')
    #     if ids==3:
    #         point = self.points[3]
    #         nextpoint=self.points[2]
    #         if abs(point[0] - max_point_2) < 1000:
    #             point[1] = max_point_2
    #             nextpoint[1]=max_point_2
    #             self.points[3] = point
    #             self.points[2]=nextpoint
    #         else:
    #             print('距离太大了，我整不了')
    #     if ids==2:
    #         point = self.points[2]
    #         nextpoint=self.points[1]
    #         if abs(point[0] - max_point_1) < 1000:
    #             point[0] = max_point_1
    #             nextpoint[0]=max_point_1
    #             self.points[2] = point
    #             self.points[1]=nextpoint
    #         else:
    #            print('距离太大了，我整不了')
    #     if ids==1:
    #         point = self.points[1]
    #         nextpoint=self.points[0]
    #         if abs(point[0] - min_point_2) < 1000:
    #             point[1] = min_point_2
    #             nextpoint[1]=min_point_2
    #             self.points[1] = point
    #             self.points[0]=nextpoint
    #         else:
    #             print('距离太大了，我整不了')
    #     return self.points



    def getImgPosition(self):
        """
        获得图像框，中心坐标，长宽像素值, 暂时测试用
        :return:
        """
        pass
        self.window.SetSize(self.size().width(), self.size().height())
        pos = self.cubeDisp.getCenterPos()
        # print('==================================================================================')
        # print(pos)
        pix_cen = world_to_display(self.renderer, pos, flg=0)
        # print('pix_cen1=', pix_cen)
        pix_cen = world_to_display(self.renderer, pos)
        # print('pix_cen2=', pix_cen)

        display_to_world(self.renderer, pix_cen, flg=1)
        display_to_world(self.renderer, pix_cen, flg=0)

    def getPixRatio(self):
        """
        获得比例尺度= 像素对应实际距离i  pix/m
        :return:
        """
        try:
            win_w, win_h = self.getWindowSize()
            # print('----------------------------------------')
            # print(win_w,win_h)
            scale = self.vtk_camera.GetParallelScale()
            k = 0.5 * win_h / scale
            return k
        except ZeroDivisionError:
            return None

    def reset(self):
        """
        重置
        :return:
        """
        # renderer_remove_all(self.renderer)
        self.resetData()

    def closeEvent(self, event):
        self.vtkWidget.Finalize()
        super(VTK_View, self).closeEvent(event)

    def resizeEvent(self, event):
        # print('vtkview resizeEvent')
        super(VTK_View, self).resizeEvent(event)

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        # if self.pixmap:
        #     return self.scale * self.pixmap.size()
        return super(VTK_View, self).minimumSizeHint()



import time

def main():
    from utils.file_manage import read_pcd_file_to_np, read_csv_file

    aa = time.time()
    app = QApplication(sys.argv)
    window = VTK_View()
    # window.resize(400, 800)

    path1 = "C:/Users\wanji\Desktop/000000.pcd"
    path2 = "C:/Users\wanji\Desktop/000000.csv"

    pcd = read_pcd_file_to_np(path1)
    CubeDatas = read_csv_file(path2)

    cubes = []
    for cube in CubeDatas:
        a = CubeLabel()
        a.getDataFromCsv(cube)
        a.buildActors()
        a.selected = True
        cubes.append(a)
        print(a)

    print(len(cubes))
    b = cubes[0].copy()
    b.cen_x += 5
    b.buildActors()
    cubes.append(b)
    cu = cubes[0]
    print(cu.length, cu.width, cu.height)
    window.RATIO = 0.5
    # window.setViewMode(0)
    window.setViewMode(1)
    window.initShowPcdCubes(pcd, cubes)
    window.getImgPosition()
    print(window.window.GetSize())
    # cv2.imwrite('C:/Users\wanji\Desktop/1.jpg', window.getScreen())
    window.show()
    bb = time.time()
    print('time = ', bb - aa)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
