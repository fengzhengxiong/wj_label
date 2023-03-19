# !/usr/bin/env python
# -*- coding: utf-8 -*-


import copy
import sys
import math
import numpy as np
import vtkmodules.all as vtk

from data.label_core_3d import LabelCore3d
from utils.vtk_util import *
from utils.util import *

from config.label_type import traffic_property_dic
from manager.global_manager import global_manager


DEFAULT = 0  # 默认显示
SELECTED = 1  # 选中高亮显示的
VIEWS = 2  # 视图模式


type_map = {}  # 数据类型映射


class CubeLabel(LabelCore3d):

    LINE_WIDTH = 1.0  # 线宽
    SELECT_LINE_WIDTH = 1.5

    # (0.2, 0.2, 0.3)
    SOLID_COLOR = (0.3, 0.6, 0.3)  # 实心颜色 (0.02, 0.01, 0.9)
    SOLID_OPC = 0.2

    EDGE_COLOR = (0.95, 0.1, 0.02)  # 棱颜色
    SELECT_EDGE_COLOR = (0.95, 0.9, 0.9)  # 高亮

    ARROW_COLOR = (0.02, 0.99, 0.1)  # 箭头颜色
    ARROW_OPC = 0.9

    TEXT_FONTSIZE = 20
    TEXT_COLOR = (0.9, 0.9, 0.9)

    TEXT_BOLD_FLAG = 1  # 是否加粗 0 / 1

    dicCubeDisplay = {
        DEFAULT: {
            'line_width': LINE_WIDTH,
            'edge_color': EDGE_COLOR,
            'solid_color': SOLID_COLOR,
            'edge_opacity': 1.0,
            'solid_opacity': 0.2,
        },
        SELECTED: {
            'line_width': SELECT_LINE_WIDTH,
            'edge_color': SELECT_EDGE_COLOR,
            'solid_color': SOLID_COLOR,
            'edge_opacity': 1.0,
            'solid_opacity': 0.4,
        },
    }


    def __init__(self, label=0, id_num=0):
        super(CubeLabel, self).__init__(label=label, id_num=id_num)
        self._line_width = self.LINE_WIDTH
        self._solid_color = self.SOLID_COLOR
        self._solid_opc = self.SOLID_OPC
        self._edge_color = self.EDGE_COLOR
        self._arrow_color = self.ARROW_COLOR
        self._arrow_opc = self.ARROW_OPC

        self._text_fontsize = self.TEXT_FONTSIZE
        self._text_color = self.TEXT_COLOR

        self.identified = True  # 是否显示标签
        self.selected = False  # 选中与否
        self.isInView = False  # 是否在三视图里显示


        # 演员对象
        self.solidActor = vtk.vtkActor()  # 实心立方体，可被点击触发
        self.edgeActor = vtk.vtkActor()  # 边框
        self.arrowActor = vtk.vtkActor()  # 箭头
        self.textActor = vtk.vtkActor2D()  # 文本

        self.buildActors()

    def setCenterPos(self, pos):
        try:
            self.cen_x, self.cen_y, self.cen_z = pos
        except Exception as e:
            print(e)

    def getCenterPos(self):
        return (self.cen_x, self.cen_y, self.cen_z)

    def setScale(self, scale):
        try:
            self.length, self.width, self.height = scale
        except Exception as e:
            print(e)

    def getScale(self):
        return (self.length, self.width, self.height)

    def setRotate(self, rotate):
        try:
            self.angle = rotate[2]
        except Exception as e:
            print(e)

    def getRotate(self):
        return (0.0, 0.0, self.angle)

    def getCubeVertexs(self):
        """
        获取8个顶点坐标
        :return:
        """
        # 定义点序列 ,4567 分别在上
        # 3--------0
        # |   o    |-----  车的方向
        # 2--------1

        x, y, z = self.getCenterPos()
        a, b, c = 0.5 * self.length, 0.5 * self.width, 0.5 * self.height
        ang = self.angle

        # vec_list = [
        #     [-b, a, -c], [b, a, -c], [b, -a, -c], [-b, -a, -c],
        #     [-b, a, c], [b, a, c], [b, -a, c], [-b, -a, c]
        # ]
        vec_list = [
            [a, b, -c], [a, -b, -c], [-a, -b, -c], [-a, b, -c],
            [a, b, c], [a, -b, c], [-a, -b, c], [-a, b, c],
        ]

        points = []
        for vec in vec_list:
            points.append(turnVector(vec, ang))

        for i in range(len(points)):
            points[i][0] += x
            points[i][1] += y
            points[i][2] += z

        return points

    def poseChange(self, delta_pos):
        """
        目标移动 ,
        :param delta_pos:移动向量，xyz 分别是前 左 上
        :return:
        """
        dx, dy, dz = delta_pos
        ang = self.angle

        delta_x1 = dx * np.cos(np.deg2rad(ang))
        delta_y1 = dx * np.sin(np.deg2rad(ang))

        delta_x2 = dy * np.cos(np.deg2rad(ang + 90))
        delta_y2 = dy * np.sin(np.deg2rad(ang + 90))

        self.cen_x += (delta_x1 + delta_x2)
        self.cen_y += (delta_y1 + delta_y2)
        self.cen_z += dz

    def sizeChange(self, delta_size):
        """
        3D框尺寸变化
        :param delta_size:
        :return:
        """
        dl, dw, dh = delta_size
        self.length += dl
        self.width += dw
        self.height += dh


    def updatePose(self):
        """
        更新框位置
        :return:
        """
        for obj in [self.solidActor, self.edgeActor]:
            set_transform_obj(
                obj=obj,
                pos=(self.cen_x, self.cen_y, self.cen_z),
                scale=(self.length, self.width, self.height),
                rot=(0.0, 0.0, self.angle)
            )

        if self.isInView:
            k = 0.7
            thick = 3.5
        else:
            k = 1.0  # 箭头长度与目标长度比例
            thick = 3.0  # 箭头粗细尺度

        arrowLength = self.length * k
        set_transform_obj(
            obj=self.arrowActor,
            pos=(self.cen_x, self.cen_y, self.cen_z),
            scale=(arrowLength, thick, thick),
            rot=(0.0, 0.0, self.angle)
        )
        if not self.isInView:
            # TODO 标签位置的更新暂时没有好方法，只有重新创建一个
            self.buildTextActor()

    def buildSolidActor(self):
        """
        创建实心显示
        :return:
        """
        cube = get_cube_source()
        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(cube.GetOutputPort(0))
        self.solidActor.SetMapper(m)

        transform = get_transform_obj(pos=(self.cen_x, self.cen_y, self.cen_z),
                                      scale=(self.length, self.width, self.height),
                                      rot=(0.0, 0.0, self.angle))

        self.solidActor.SetUserTransform(transform)

        self.solidActor.GetProperty().SetColor(self._solid_color)
        self.solidActor.GetProperty().SetOpacity(self._solid_opc)  # 透明度
        self.solidActor.GetProperty().SetLineWidth(self._line_width)
        # self.solidActor.GetProperty().SetRenderLinesAsTubes(True)
        del cube, m, transform

    def buildEdgeActor(self):
        """
        创建边界棱
        :return:
        """
        cube = get_cube_source()
        outline = vtk.vtkOutlineFilter()  # 这个是框
        outline.SetInputData(cube.GetOutput())
        outline.Update(0)
        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(outline.GetOutputPort(0))
        self.edgeActor.SetMapper(m)

        transform = get_transform_obj(pos=(self.cen_x, self.cen_y, self.cen_z),
                                      scale=(self.length, self.width, self.height),
                                      rot=(0.0, 0.0, self.angle))

        self.edgeActor.SetUserTransform(transform)

        color = self._edge_color
        if self.label in global_manager.traffic_property_dic.keys():
            r, g, b = global_manager.traffic_property_dic[self.label]['color']
            color = (r / 255, g/ 255, b / 255)

        self.edgeActor.GetProperty().SetColor(color)
        self.edgeActor.GetProperty().SetOpacity(1.0)  # 透明度
        self.edgeActor.GetProperty().SetLineWidth(self._line_width)
        # self.solidActor.GetProperty().SetRenderLinesAsTubes(True)
        del cube, outline, m, transform


    def buildArrowActor(self):
        """
        创建箭头方向
        :return:
        """
        ''' 创建方向箭头源 '''
        arrow = get_arrow_source()
        ''' 添加数据集 '''
        point = vtk.vtkPoints()
        point.InsertNextPoint((0.0, 0.0, 0.0))
        polydata = vtk.vtkPolyData()
        polydata.SetPoints(point)
        glyph = vtk.vtkGlyph3D()
        glyph.SetSourceConnection(arrow.GetOutputPort(0))
        glyph.SetInputData(polydata)
        glyph.SetVectorModeToUseNormal()
        glyph.SetScaleFactor(1)
        glyph.OrientOn()
        glyph.Update(0)
        m = vtk.vtkPolyDataMapper()
        m.SetInputData(glyph.GetOutput())

        self.arrowActor.SetMapper(m)

        k = 1.0  # 箭头长度与目标长度比例
        thick = 3.0  # 箭头粗细尺度
        arrowLength = self.length * k
        transform = get_transform_obj(pos=(self.cen_x, self.cen_y, self.cen_z),
                                      scale=(arrowLength, thick, thick),
                                      rot=(0.0, 0.0, self.angle))

        self.arrowActor.SetUserTransform(transform)

        self.arrowActor.GetProperty().SetColor(self._arrow_color)
        self.arrowActor.GetProperty().SetOpacity(self._arrow_opc)  # 透明度
        self.arrowActor.GetProperty().SetLineWidth(self._line_width)

        del arrow, point, polydata, glyph, m, transform


    def buildTextActor(self):
        """
        创建字体
        """
        # 这个方法标签大小有问题，还是用其他
        str_text = self.getText()

        pos = [self.cen_x, self.cen_y, self.cen_z]

        # vtkVectorText 方法
        # self.textActor = get_follower(str_text, pos, self._text_color)

        #  vtkLabelPlacementMapper 方法
        color = self._text_color
        if self.label in global_manager.traffic_property_dic.keys():
            r, g, b = global_manager.traffic_property_dic[self.label]['color']
            color = (r / 255, g / 255, b / 255)

        labelMapper = get_label_mapper(str_text, pos, self._text_fontsize, color)
        if labelMapper is not None:
            self.textActor.SetMapper(labelMapper)

    def buildActors(self):
        self.buildSolidActor()
        self.buildEdgeActor()
        self.buildArrowActor()
        self.buildTextActor()


    def getText(self):
        str_text = "{}-[{}]-{}".format(self.id_num, self.label, self.is_cover)
        if type_map and self.label in type_map.keys():
            str_text = "{}-{}-{}".format(self.id_num, type_map[self.label], self.is_cover)
        return str_text


    #axiong add 20221209
    def setText(self,data):
        pass
        # pos = [self.cen_x, self.cen_y, self.cen_z]
        # color = self._text_color
        # if self.label in global_manager.traffic_property_dic.keys():
        #     r, g, b = global_manager.traffic_property_dic[self.label]['color']
        #     color = (r / 255, g / 255, b / 255)
        # labelMapper = get_label_mapper(str(data), pos, self._text_fontsize, color)
        # if labelMapper is not None:
        #     self.textActor.SetMapper(labelMapper)


    def addByRenderer(self, render):
        """
        标签显示
        :param render:
        :return:
        """
        if not isinstance(render, vtk.vtkRenderer):
            print(type(render))
            return False
        render.AddActor(self.solidActor)
        render.AddActor(self.edgeActor)
        render.AddActor(self.arrowActor)
        if not self.isInView:
            if isinstance(self.textActor, vtk.vtkFollower):
                self.textActor.SetCamera(render.GetActiveCamera())  # 只有follower可以用
            render.AddActor(self.textActor)
        return True

    def removeByRenderer(self, render):
        if not isinstance(render, vtk.vtkRenderer):
            print(type(render))
            return False
        render.RemoveActor(self.solidActor)
        render.RemoveActor(self.edgeActor)
        render.RemoveActor(self.arrowActor)
        render.RemoveActor2D(self.textActor)
        return True


    def updateActorProperty(self):
        """更新显示属性"""
        if self.isInView:

            self.solidActor.GetProperty().SetColor(self._solid_color)
            self.solidActor.GetProperty().SetOpacity(0.05)  # 透明度
            self.solidActor.GetProperty().SetLineWidth(0.5)

            self.edgeActor.GetProperty().SetColor(1, 0.5, 0)
            self.edgeActor.GetProperty().SetOpacity(1.0)  # 透明度
            self.edgeActor.GetProperty().SetLineWidth(1.2)
            return

        color = self._edge_color
        if self.label in global_manager.traffic_property_dic.keys():
            r, g, b = global_manager.traffic_property_dic[self.label]['color']
            color = (r / 255, g / 255, b / 255)

        if self.selected:


            self.solidActor.GetProperty().SetColor((0.8, 0.8, 0.8))
            self.solidActor.GetProperty().SetOpacity(0.2)  # 透明度
            self.solidActor.GetProperty().SetLineWidth(1.0)

            self.edgeActor.GetProperty().SetColor(0.9,0.9,0.9)
            self.edgeActor.GetProperty().SetOpacity(1.0)  # 透明度
            self.edgeActor.GetProperty().SetLineWidth(3.0)

            self.arrowActor.GetProperty().SetColor((0.8, 0.9, 0.9))
        else:

            self.solidActor.GetProperty().SetColor(self._solid_color)
            self.solidActor.GetProperty().SetOpacity(0.15)  # 透明度
            self.solidActor.GetProperty().SetLineWidth(self.SELECT_LINE_WIDTH)

            self.edgeActor.GetProperty().SetColor(color)
            self.edgeActor.GetProperty().SetOpacity(1.0)  # 透明度
            self.edgeActor.GetProperty().SetLineWidth(self.SELECT_LINE_WIDTH)

            self.arrowActor.GetProperty().SetColor(self._arrow_color)


    def updateMode(self, render):

        self.removeByRenderer(render)
        self.addByRenderer(render)

    def isMe(self, actor, all=True):
        """
        判断是否为本cube对象
        :param actor:
        :param all:
        :return:
        """
        if all:
            ret = actor in [self.solidActor, self.edgeActor, self.arrowActor, self.textActor]
        else:
            ret = actor in [self.solidActor, self.edgeActor]
        return ret

    def shadowCopy(self, other):
        """
        从另外对象拷贝过来位置信息
        :param other:
        :return:
        """
        if not isinstance(other, CubeLabel):
            print("shadowCopy  fail ...")
            return False

        self.setCenterPos(other.getCenterPos())
        self.setScale(other.getScale())
        self.setRotate(other.getRotate())
        self.updatePose()


    def copy(self):
        c = CubeLabel()
        for key, val in vars(self).items():
            if not isinstance(val, vtk.vtkActor):
                setattr(c, key, val)

        c.solidActor = vtk.vtkActor()
        c.buildSolidActor()
        c.edgeActor = vtk.vtkActor()
        c.buildEdgeActor()
        c.arrowActor = vtk.vtkActor()
        c.buildArrowActor()
        c.textActor = vtk.vtkActor2D()
        c.buildTextActor()

        return c


if __name__ == "__main__":
    a = CubeLabel()

    a.cen_x, a.cen_y, a.cen_z = 1, 1.5, 0.3
    a.length, a.width, a.height = 3,1,2
    a.angle = 30
    a.label = 2
    a.buildActors()

    axes_actor = vtk.vtkAxesActor()  # 添加坐标轴
    axes_actor.SetTotalLength(3, 3, 3)  # 设置坐标轴长度
    # 渲染器
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.6, 0.5, 0.9)
    ren.SetBackground2(0.8, 0.5, 0.8)
    ren.SetGradientBackground(1)

    a.addByRenderer(ren)
    a.selected = True
    a.updateActorProperty()
    a.updateMode(ren)

    ren.AddActor(axes_actor)
    # 窗口
    ren_window = vtk.vtkRenderWindow()
    ren_window.SetSize(400, 400)
    ren_window.AddRenderer(ren)
    # 交互
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(ren_window)  # 绑定交互作用的窗口
    # 交互模式
    style = vtk.vtkInteractorStyleMultiTouchCamera()  # 移动相机模式
    interactor.SetInteractorStyle(style)
    # 显示
    interactor.Initialize()
    ren_window.Render()
    interactor.Start()
