# !/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5.QtWidgets import QFrame, QHBoxLayout, QApplication
import vtkmodules.all as vtk
# from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
# import vtkmodules
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk

import numpy as np
import sys


def get_cube_source():
    s = vtk.vtkCubeSource()
    s.SetCenter(0, 0, 0)
    s.SetXLength(1)
    s.SetYLength(1)
    s.SetZLength(1)
    s.Update(0)
    return s


def get_arrow_source():
    """创建方向箭头源 """
    arrow = vtk.vtkArrowSource()
    arrow.SetTipResolution(10)
    arrow.SetTipLength(0.3)
    arrow.SetTipRadius(0.05)
    arrow.SetShaftRadius(0.01)
    arrow.SetShaftResolution(10)
    arrow.SetInvert(0)
    arrow.Update(0)
    return arrow


def get_transform_obj(pos=(0, 0, 0), scale=(0, 0, 0), rot=(0, 0, 0)):
    try:
        transform = vtk.vtkTransform()
        transform.PostMultiply()  # PreMultiply
        transform.Scale(*scale)
        transform.RotateZ(rot[2])
        transform.RotateY(rot[1])
        transform.RotateX(rot[0])
        transform.Translate(*pos)
        transform.Update()
        return transform
    except Exception as e:
        print(e)
        return vtk.vtkTransform()


def set_transform_obj(obj, pos=(0, 0, 0), scale=(0, 0, 0), rot=(0, 0, 0)):
    """
    actor 设置位置
    :param obj: vtkActor
    :param pos:
    :param scale:
    :param rot:
    :return:
    """
    if not isinstance(obj, vtk.vtkActor):
        print(type(obj))
        return False
    transform = obj.GetUserTransform()
    transform = transform if transform is not None else vtk.vtkTransform()
    # transform = vtk.vtkTransform()
    transform.SetMatrix(vtk.vtkMatrix4x4())  # 清除
    transform.PostMultiply()  # PreMultiply
    transform.Scale(*scale)
    transform.RotateZ(rot[2])
    transform.RotateY(rot[1])
    transform.RotateX(rot[0])
    transform.Translate(*pos)
    transform.Update()
    obj.SetUserTransform(transform)
    return True



def get_box_widget(iren, size=3.0, color=(0.8, 0.5, 0.1), def_ret=None):
    """
    添加3D操作框控件
    # https://www.freesion.com/article/6280422237/#3_vtkBoxWidget__15
    :param iren: vtk.vtkRenderWindowInteractor()
    :param def_ret:
    :return:
    """
    # https://www.freesion.com/article/6280422237/#3_vtkBoxWidget__15
    try:
        # print(type(iren))
        bw = vtk.vtkBoxWidget()
        bw.SetInteractor(iren)
        bw.SetPlaceFactor(1.0)
        bw.PlaceWidget(-0.5, 0.5, -0.5, 0.5, -0.5, 0.5)
        bw.SetTranslationEnabled(1)
        bw.SetScalingEnabled(1)
        bw.SetRotationEnabled(1)
        bw.SetOutlineFaceWires(0)
        bw.SetOutlineCursorWires(1)
        bw.SetInsideOut(0)
        bw.HandlesOn()
        # bw.SetHandleSize(0.01)
        bw.GetHandleProperty().SetPointSize(size)
        bw.GetHandleProperty().SetColor(*color)
        # bw.On()


        return bw
    except Exception as e:
        print(e)
        return def_ret


def get_axes_actor(length=(80, 80, 30), color=(0.1, 0.9, 0.1), linewidth=15.0):
    """
    创建坐标轴

    """
    axesActor = vtk.vtkAxesActor()
    axesActor.SetXAxisLabelText('x')
    axesActor.SetYAxisLabelText('y')
    axesActor.SetZAxisLabelText('z')
    axesActor.SetTotalLength(*length)
    axesActor.SetShaftTypeToLine()
    axesActor.SetNormalizedShaftLength(1.0, 1.0, 1.0)  # 设置末端箭头在轴上比例
    axesActor.SetNormalizedTipLength(0.08, 0.08, 0.08)
    # axesActor.SetShaftType(1)
    axesActor.SetCylinderRadius(6.0)
    axesActor.SetConeRadius(0.3)

    axesActor.GetXAxisCaptionActor2D().GetProperty().SetColor(*color)
    axesActor.GetYAxisCaptionActor2D().GetProperty().SetColor(*color)
    axesActor.GetZAxisCaptionActor2D().GetProperty().SetColor(*color)
    axesActor.GetXAxisCaptionActor2D().GetProperty().SetLineWidth(linewidth)
    axesActor.GetYAxisCaptionActor2D().GetProperty().SetLineWidth(linewidth)
    axesActor.GetZAxisCaptionActor2D().GetProperty().SetLineWidth(linewidth)
    bFlag = False
    if bFlag:
        # colors = vtk.vtkNamedColors()
        # xAxisLabel = axesActor.GetXAxisCaptionActor2D()
        # xAxisLabel.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        # xAxisLabel.SetWidth(5.0)
        # # xAxisLabel.GetPositionCoordinate().SetValue(0, 0)
        # xAxisLabel.GetCaptionTextProperty().SetFontSize(6)
        # xAxisLabel.GetCaptionTextProperty().SetColor(colors.GetColor3d("white"))
        # yAxisLabel = axesActor.GetYAxisCaptionActor2D()
        # yAxisLabel.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        # yAxisLabel.SetWidth(5.0)
        # # yAxisLabel.GetPositionCoordinate().SetValue(0, 0)
        # yAxisLabel.GetCaptionTextProperty().SetFontSize(6)
        # zAxisLabel = axesActor.GetZAxisCaptionActor2D()
        # zAxisLabel.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        # zAxisLabel.SetWidth(5.0)
        # # zAxisLabel.GetPositionCoordinate().SetValue(0, 0)
        # zAxisLabel.GetCaptionTextProperty().SetFontSize(6)
        # del xAxisLabel, yAxisLabel, zAxisLabel, colors
        pass

    return axesActor


def get_boundary_obj(r=80.0, color=(0.9, 0.8, 1), linewidth=2.0, def_ret=None):
    """
    建立边界圆
    :param r: 半径
    :param color: 颜色
    :param linewidth: 线宽
    :return:vtkActor
    """
    try:
        lineSource = vtk.vtkLineSource()
        points = vtk.vtkPoints()
        for i in range(0, 361):
            p = (r * np.cos(np.deg2rad(i)), r * np.sin(np.deg2rad(i)), 0.0)
            points.InsertNextPoint(*p)
        lineSource.SetPoints(points)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(lineSource.GetOutputPort(0))
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetLineWidth(linewidth)
        actor.GetProperty().SetColor(*color)
        # colors = vtk.vtkNamedColors()
        # actor.GetProperty().SetColor(colors.GetColor3d("Peacock"))
        return actor
    except Exception as e:
        print(e)
        return def_ret


def get_text_actor(text, size=18, pos=(10, 2), color=(1, 1, 1)):
    """
    创建二维静态文本标签
    :param text: 内容
    :param size: 字体大小
    :param pos: 位置
    :return: vtkActor2D
    """
    flag = 1
    if flag == 0:
        tp = vtk.vtkTextProperty()
        tp.SetFontSize(size)
        tp.SetJustificationToLeft()
        tm = vtk.vtkTextMapper()
        tm.SetInput(text)
        tm.SetTextProperty(tp)

        a2d = vtk.vtkActor2D()
        a2d.SetMapper(tm)
        a2d.SetPosition(pos)
        return a2d
    else:
        t = vtk.vtkTextActor()
        t.SetInput(text)
        t.GetTextProperty().SetFontSize(size)
        t.GetTextProperty().SetColor(color)
        t.GetTextProperty().SetJustificationToLeft()
        # t.GetTextProperty().SetVerticalJustificationToTop()
        t.GetTextProperty().SetFontFamilyToTimes()
        t.SetPosition(pos)
        return t



def get_cloud_point_actor(data, color=(1, 1, 1), size=1.0, def_ret=None):
    """
    点云
    :param data: pcd数据， np数组
    :param color:
    :param size: 点大小
    :param def_ret:
    :return:
    """
    try:
        if data is None or data.shape[0] == 0:
            return def_ret
    except Exception as e:
        print('In Func [{}], ERR:{}'.format(sys._getframe().f_code.co_name, e))
        return def_ret
    points = vtk.vtkPoints()
    vertices = vtk.vtkCellArray()
    depth = vtk.vtkFloatArray()
    for i in range(data.shape[0]):
        p = (data[i, 0], data[i, 1], data[i, 2])
        point_id = points.InsertNextPoint(*p)
        vertices.InsertNextCell(1)
        vertices.InsertCellPoint(point_id)
        depth.InsertNextValue(p[2])  # 按照Z颜色渐变

    # 设置颜色表
    ColorTable = vtk.vtkLookupTable()
    ColorTable.SetNumberOfColors(4)
    ColorTable.SetTableValue(0, (0.0, 0.0, 0.0, 3.0))
    ColorTable.SetTableValue(1, (0.0, 0.3, 0.0, 1.0))
    ColorTable.SetTableValue(2, (1.0, 0.4, 0.3, 1.0))
    ColorTable.SetTableValue(3, (0.5, 0.5, 1.0, 2.0))
    ColorTable.SetTableRange((-25, 5))
    ColorTable.Build()
    array = ColorTable.MapScalars(depth, vtk.VTK_COLOR_MODE_DEFAULT, -1)
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetVerts(vertices)
    # polydata.GetPointData().SetScalars(depth)  # 颜色渐变
    # polydata.GetPointData().SetScalars(array)

    glyphFilter = vtk.vtkVertexGlyphFilter()
    glyphFilter.SetInputData(polydata)
    glyphFilter.Update(0)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(glyphFilter.GetOutputPort(0))
    mapper.SetColorModeToDefault()
    mapper.SetScalarRange(-7, 5)
    # mapper.SetLookupTable(ColorTable)
    mapper.SetScalarVisibility(1)

    act = vtk.vtkActor()
    act.SetMapper(mapper)
    act.GetProperty().SetColor(color)
    act.GetProperty().SetPointSize(size)
    # act.GetProperty().SetAmbient(0.5)

    return (points, vertices, depth, polydata, mapper, act)


def get_axes_marker_widget(iren, def_ret=None):
    try:
        axes = vtk.vtkAxesActor()
        axesWidget = vtk.vtkOrientationMarkerWidget()
        axesWidget.SetOutlineColor(1, 1, 1)  # (0.93, 0.57, 0.13) # 外边框颜色
        axesWidget.SetOrientationMarker(axes)
        axesWidget.SetInteractor(iren)
        axesWidget.SetEnabled(1)  # EnabledOn()
        axesWidget.InteractiveOn()  # 坐标系是否可移动
        return axesWidget
    except Exception as e:
        print(e)
        return def_ret

def renderer_remove_all(ren, def_ret=None):
    """
    清除render里所有的演员
    :param ren:
    :return:
    """
    try:
        actorCollection = ren.GetActors()
        num = actorCollection.GetNumberOfItems()
        actorCollection.InitTraversal()
        # print('num=', num)
        for i in range(num):
            a = actorCollection.GetNextActor()
            ren.RemoveActor(a)

        actorCollection = ren.GetActors2D()
        num = actorCollection.GetNumberOfItems()
        actorCollection.InitTraversal()
        for i in range(num):
            a = actorCollection.GetNextProp()
            ren.RemoveActor2D(a)

        del actorCollection
        del num
    except Exception as e:
        print(e)
        return def_ret


def actor_in_renderer_ornot(act, ren, def_ret=False):
    """
    actor 是否显示在renderer里
    :param act:
    :param ren:
    :param def_ret:
    :return:
    """
    try:
        actorCollection = ren.GetActors()
        num = actorCollection.GetNumberOfItems()
        actorCollection.InitTraversal()
        # print('num=', num)
        for i in range(num):
            a = actorCollection.GetNextActor()
            if act == a:
                return True

        actorCollection = ren.GetActors2D()
        num = actorCollection.GetNumberOfItems()
        actorCollection.InitTraversal()
        for i in range(num):
            a = actorCollection.GetNextProp()
            if act == a:
                return True

        del actorCollection
        del num
        return False
    except Exception as e:
        print(e)
        return def_ret


def get_label_mapper(text, pos, fontsize=20, color=(1, 1, 1), def_ret=None):
    """
    获取文本 mapper
    :param text:
    :param pos: 位置
    :param fontsize: 字体大小
    :param color: 颜色
    :param def_ret:
    :return:
    """
    try:
        labels = vtk.vtkStringArray()
        labels.SetName("label")
        points = vtk.vtkPoints()
        points.InsertNextPoint(*pos)
        labels.InsertNextValue(text)

        vertices = vtk.vtkCellArray()
        vertices.InsertNextCell(1)
        vertices.InsertCellPoint(0)

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetVerts(vertices)
        polydata.GetPointData().AddArray(labels)
        # print('GetPoint = ',polydata.GetPoint(0))

        textProperty = vtk.vtkTextProperty()
        textProperty.SetFontSize(fontsize)  # 字体
        textProperty.SetColor(*color)  # 颜色
        # textProperty.SetJustificationToCentered()  # 居中
        textProperty.SetJustificationToLeft()  # 靠左 ,SetJustificationToRight 右
        textProperty.SetFontFamilyToArial()
        # textProperty.SetFontFamily(0)
        textProperty.SetBold(1)  # 加粗

        hie = vtk.vtkPointSetToLabelHierarchy()
        hie.SetInputData(polydata)
        hie.SetMaximumDepth(8)
        hie.SetLabelArrayName(labels.GetName())
        hie.SetTargetLabelCount(60)
        hie.SetTextProperty(textProperty)
        strategy = vtk.vtkFreeTypeLabelRenderStrategy()
        labelMapper = vtk.vtkLabelPlacementMapper()
        labelMapper.SetInputConnection(hie.GetOutputPort(0))
        labelMapper.SetRenderStrategy(strategy)
        labelMapper.UseDepthBufferOff()
        labelMapper.SetShapeToNone()  # 设置不显示边框, SetShapeToRect, SetShapeToRoundedRect
        labelMapper.SetStyleToOutline()
        labelMapper.UseUnicodeStringsOff()  # 表示不使用Unicode字符串
        return labelMapper

    except Exception as e:
        print(e)
        return def_ret


def get_follower(text, pos, color=(1, 1, 1), def_ret=None):
    """
    获取字体 actor
    :param text:
    :param pos:
    :param color:
    :param def_ret:
    :return:
    """
    try:
        vec_text = vtk.vtkVectorText()
        vec_text.SetText(text)
        textMapper = vtk.vtkPolyDataMapper()
        textMapper.SetInputConnection(vec_text.GetOutputPort(0))
        textActor = vtk.vtkFollower()
        # textActor = vtk.vtkActor()
        textActor.SetMapper(textMapper)
        textActor.SetScale(0.6, 0.6, 0.6)
        textActor.AddPosition(*pos)
        textActor.GetProperty().SetColor(*color)
        return textActor
    except Exception as e:
        print(e)
        return def_ret


def get_cube_axes_actor(ren, def_ret=None):
    """
    https://www.cnblogs.com/ybqjymy/p/14042172.html
    暂时不启用
    :param ren:
    :param def_ret:
    :return:
    """
    # TODO 未进行调试过
    if not isinstance(ren, vtk.vtkRenderer):
        return def_ret

    caa = vtk.vtkCubeAxesActor()
    caa.SetXAxisRange(0, 80)
    caa.SetYAxisRange(0, 80)
    caa.SetZAxisRange(0, 40)

    caa.GetXAxesLinesProperty().SetLineWidth(0.5)
    caa.GetYAxesLinesProperty().SetLineWidth(0.5)
    caa.GetZAxesLinesProperty().SetLineWidth(0.5)

    # 设置标题和标签文本的屏幕大小。默认值为10
    caa.SetScreenSize(6)
    # 指定标签与轴之间的距离。默认值为20
    caa.SetLabelOffset(5)
    # 显示坐标轴
    caa.SetVisibility(1)
    # 指定一种模式来控制轴的绘制方式
    caa.SetFlyMode(vtk.vtkCubeAxesActor.VTK_FLY_OUTER_EDGES)

    caa.SetXAxisMinorTickVisibility(1)
    caa.SetYAxisMinorTickVisibility(1)
    caa.SetZAxisMinorTickVisibility(1)
    caa.SetTickLocation(vtk.vtkCubeAxesActor.VTK_TICKS_INSIDE)
    caa.SetGridLineLocation(vtk.vtkCubeAxesActor.VTK_GRID_LINES_CLOSEST)
    caa.SetCamera(ren.GetActiveCamera())

    return caa


def world_to_display(ren, world_point, def_ret=None, flg=1):
    """
    vtk 世界坐标转换到像素坐标 , 2个算法
    :param ren: renderer
    :param world_point: 空间坐标xyz
    :return: (x,y) 或 (x, y, z)
    """
    try:
        flg = flg
        if flg == 1:
            ren.SetWorldPoint(world_point[0], world_point[1], world_point[2], 1)
            ren.WorldToDisplay()
            result = ren.GetDisplayPoint()[:2]
            return result
        else:
            vtk_coord = vtk.vtkCoordinate()
            vtk_coord.SetCoordinateSystemToWorld()
            vtk_coord.SetValue(world_point[0], world_point[1], world_point[2])
            result = vtk_coord.GetComputedDoubleViewportValue(ren)[:2]
            return result
    except Exception as e:
        print(e)
        return def_ret



def display_to_world(ren, coord, def_ret=None, flg=1):
    """
    vtk 像素坐标转换到世界坐标 , 2个算法
    :param ren: renderer
    :param coord: 像素x y
    :return: (x,y,z)
    """
    try:
        flg = flg
        if flg == 1:
            ren.SetDisplayPoint(coord[0], coord[1], 0)
            ren.DisplayToWorld()
            result = ren.GetWorldPoint()
            # print(result)
            return result[:3]
        else:
            vtk_coord = vtk.vtkCoordinate()
            vtk_coord.SetCoordinateSystemToDisplay()
            vtk_coord.SetValue(coord[0], coord[1], 0)
            result = vtk_coord.GetComputedWorldValue(ren)
            # print('==== ',result)
            return result[:3]
    except Exception as e:
        print(e)
        return def_ret


def getVtkWindowScreen(window, def_ret=None):
    """
    获取vtk窗口图像
    :param window:
    :param def_ret:
    :return:
    """
    try:
        converter = vtk.vtkWindowToImageFilter()
        converter.SetInput(window)
        converter.SetInputBufferTypeToRGB()
        converter.ReadFrontBufferOff()
        converter.Update(0)
        im = vtk_to_numpy(converter.GetOutput().GetPointData().GetScalars())
        # print('getVtkWindowScreen=', window.GetSize())
        return np.flipud(im.reshape(window.GetSize()[1], window.GetSize()[0], im.shape[-1]))
    except Exception as e:
        print(e)
        return def_ret


def get_mouse_direction(ren, pos1, pos2, def_ret=None):
    """
    计算方向，鼠标框选过程中的方向
    :param ren: renderer
    :param pos1: 起点
    :param pos2: 终点
    :return:
    """
    if not isinstance(ren, vtk.vtkRenderer):
        return def_ret

    width = np.abs(pos2[0] - pos1[0])
    height = np.abs(pos2[1] - pos1[1])

    if width >= height:  # 横向
        pa = [pos1[0], 0.5 * (pos1[1] + pos2[1])]
        pb = [pos2[0], 0.5 * (pos1[1] + pos2[1])]
    else:
        pa = [0.5 * (pos1[0] + pos2[0]), pos1[1]]
        pb = [0.5 * (pos1[0] + pos2[0]), pos2[1]]

    point1 = display_to_world(ren, pa)
    point2 = display_to_world(ren, pb)
    # 三维点，只看xy向量
    vx = point2[0] - point1[0]
    vy = point2[1] - point1[1]
    result = np.rad2deg(np.arctan2(vy, vx))
    return result
