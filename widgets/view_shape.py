# !/usr/bin/env python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, QRectF, QLineF
from PyQt5.QtGui import QColor, QPen, QPainterPath

import copy

from utils.qt_math_util import *

DEFAULT_LINE_COLOR = QColor(200, 50, 50, 200)  # bf hovering
DEFAULT_FILL_COLOR = QColor(20, 200, 0, 10)  # hovering 悬浮填充颜色
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)  # selected
DEFAULT_SELECT_FILL_COLOR = QColor(0, 255, 0, 100)  # selected  # 选中后填充颜色

DEFAULT_VERTEX_FILL_COLOR = QColor(20, 255, 0, 50)  # 默认点被填充颜色
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 255, 255, 150)  # hovering 点悬浮时候的颜色


# 默认，悬浮，选中模式
DEFAULT = 0
HOVERING = 1
SELECTED = 2


class ShapeShowMode():
    """ shape显示模式 """
    def __init__(self, index=None, mode=DEFAULT):
        self.index = index
        self.mode = mode


class ViewShape():

    P_SQUARE = 0
    P_ROUND = 1
    MOVE_VERTEX = 0
    NEAR_VERTEX = 1
    L_SOLID = Qt.SolidLine  # 实线
    L_DASH = Qt.DashLine  # 虚线

    # line_color = DEFAULT_LINE_COLOR
    # fill_color = DEFAULT_FILL_COLOR
    # select_line_color = DEFAULT_SELECT_LINE_COLOR
    # select_fill_color = DEFAULT_SELECT_FILL_COLOR
    # vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    # hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    # TODO  yaml文件

    # 顶点模式
    dicVertexMode = {
        DEFAULT: {
            'color': DEFAULT_VERTEX_FILL_COLOR,
            'fillcolor': DEFAULT_VERTEX_FILL_COLOR,
            'style': P_SQUARE,
            'size': 10,
        },
        HOVERING: {
            'color': DEFAULT_HVERTEX_FILL_COLOR,
            'fillcolor': DEFAULT_HVERTEX_FILL_COLOR,
            'style': P_SQUARE,
            'size': 15,
        },
        SELECTED: {
            'color': QColor(255, 0, 0, 200),
            'fillcolor': QColor(255, 0, 0, 200),
            'style': P_SQUARE,
            'size': 18,
        },
    }
    # 矩形框线的模式
    dicPolyMode = {
        DEFAULT: {
            'color': DEFAULT_LINE_COLOR,
            'fillcolor': DEFAULT_FILL_COLOR,
            'width': 1.0,
        },
        HOVERING: {
            'color': DEFAULT_HVERTEX_FILL_COLOR,
            'fillcolor': QColor(150, 10, 10, 15),
            'width': 1.2,
        },
        SELECTED: {
            'color': QColor(255, 0, 0, 200),
            'fillcolor': QColor(100, 200, 30, 20),
            'width': 1.5,
        },
    }
    # 拉伸点
    dicStretchMode = {
        DEFAULT: {
            'color': DEFAULT_VERTEX_FILL_COLOR,
            'fillcolor': QColor(220, 120, 100, 50),
            'style': P_ROUND,
            'size': 10,
        },
        HOVERING: {
            'color': DEFAULT_HVERTEX_FILL_COLOR,
            'fillcolor': QColor(20, 255, 30, 50),
            'style': P_ROUND,
            'size': 18,
        },
        SELECTED: {
            'color': QColor(255, 0, 0, 200),
            'fillcolor': QColor(255, 255, 255, 80),
            'style': P_ROUND,
            'size': 18,
        },
    }

    # 平移线 capstyle , joinstyle
    dicTranslateMode = {
        DEFAULT: {
            'color': QColor(0, 0, 200, 80),
            'width': 0.5,
            'style': L_DASH,
        },
        HOVERING: {
            'color': QColor(0, 200, 200, 150),
            'width': 1.0,
            'style': L_SOLID,
        },
        SELECTED: {
            'color': QColor(0, 200, 200, 230),
            'width': 1.2,
            'style': L_SOLID,
        },
    }

    # 旋转线 capstyle , joinstyle
    dicRotateMode = {
        DEFAULT: {
            'color': QColor(0, 0, 200, 80),
            'width': 1.0,
            'style': L_SOLID,
        },
        HOVERING: {
            'color': QColor(60, 200, 30, 150),
            'width': 3.0,
            'style': L_SOLID,
        },
        SELECTED: {
            'color': QColor(60, 200, 30, 240),
            'width': 3.2,
            'style': L_SOLID,
        },
    }

    line_width = 1.0
    point_size = 5
    scale = 1.0

    min_radius = 40  # 圆辅助线 最小半径

    point_type = P_ROUND

    def __init__(self):
        super().__init__()

        self.coord_points = []
        self.points = []  # 图形顶点Vertex
        # self.points = [
        #     QPointF(100, 100),
        #     QPointF(300, 100),
        #     QPointF(300, 300),
        #     QPointF(100, 300)
        # ]
        self.stretch_points = []  # 边中心点，用于拉伸图形,QPointF*4
        self.translate_lines = []  # 平移线， 沿着X,Y方向移动,QLineF*2
        self.rotate_lines = []  # 旋转线， 存放圆形的矩形,QRectF*1

        self.radius = None  # 旋转圆的半径

        self._highlightVertexIndex = None  # 高亮顶点索引
        self._highlightStretchIndex = None  # 高亮拉伸点索引
        self._highlightDraglineIndex = None  # 高亮平移线
        self._highlightRotlineIndex = None  # 高亮圆，目前圆仅一个，若需，则为0

        self.fill = False  # 是否填充
        self.selected = False  # 是否选中 ,三视图按下左键选中，松开后不选中 ； TODO 图像模式，选中和拖动是一样的样式

        self.rot_enable = True  # 旋转使能

        self._hlShape = None  # 高亮矩形框
        self._hlVertex = None  # 高亮顶点
        self._hlStretch = None  # 高亮拉伸点
        self._hlTrans = None  # 高亮平移线
        self._hlRot = None  # 高亮圆


        self.line_color = DEFAULT_LINE_COLOR
        self._vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR

        # print(self.getCenterPoint())

        # self.setTranslateLine()
        # self.setRotateLine()
        # self.setStretchPoint()

    def coord_to_points(self):
        self.points = [QPointF(x, y) for x, y in self.coord_points]

    def points_to_coord(self):
        self.coord_points = [(p.x(), p.y()) for p in self.points]

    def setStretchPoint(self):
        """ 计算拉伸点"""
        # 边的序号 边0: 3-0 ;边1:0-1 ...；
        # 拉伸点n = 边n中点
        # 0-----|-----1
        # |     |     |
        # ------|-------
        # |     |     |
        # 3-----|-----2

        self.stretch_points = []
        if len(self.points) == 0:
            return
        for i in range(len(self.points)):
            self.stretch_points.append(midPoint(self.points[i - 1], self.points[i]))

    def setTranslateLine(self):
        """ 计算平移线 """
        # 矩形：线0 = 拉伸点0-2 ；线1 = 拉伸点1-3
        # 0-----|-----1
        # |     |     |
        # ------|-------
        # |     |     |
        # 3-----|-----2
        self.translate_lines = []
        if len(self.points) == 0:
            return

        # TODO  对之后其他图形另做设定
        # 矩形情况
        if len(self.points) == 4:
            p1 = midPoint(self.points[0], self.points[3])
            p2 = midPoint(self.points[1], self.points[2])
            new_p1, new_p2 = extendline([p1, p2], ratio=2, minlength=None)
            self.translate_lines.append(QLineF(new_p1, new_p2))

            p1 = midPoint(self.points[0], self.points[1])
            p2 = midPoint(self.points[3], self.points[2])
            new_p1, new_p2 = extendline([p1, p2], ratio=2, minlength=None)
            self.translate_lines.append(QLineF(new_p1, new_p2))

    def setRotateLine(self):
        """添加旋转线"""
        self.rotate_lines = []

        if len(self.points) == 0:
            return
        if len(self.points) == 4 and self.rot_enable:
            w, h = self.getHeightWidth()

            self.radius = min(w, h) * 1.1 / 2
            r = self.radius = max(self.radius, self.min_radius)
            c = self.getCenterPoint()
            self.rotate_lines.append(QRectF(c.x() - r, c.y() - r, 2 * r, 2 * r))

    def getCenterPoint(self):
        if len(self.points) == 0:
            return None
        xl = [p.x() for p in self.points]
        yl = [p.y() for p in self.points]
        return QPointF(sum(xl) / len(xl), sum(yl) / len(yl))

    def getHeightWidth(self):
        try:
            w, h = distance(self.points[0] - self.points[1]), distance(self.points[0] - self.points[3])
            return [w, h]
        except Exception as e:
            print(e)
            return [0, 0]

    def updatePoints(self, qp=True):
        """
        更新点位
        :param qp: True 由points更新 ，False coord_points更新
        :return:
        """
        if qp:
            self.points_to_coord()
        else:
            self.coord_to_points()

        if self.points:
            self.setTranslateLine()
            self.setRotateLine()
            self.setStretchPoint()


    def paint(self, painter):
        if self.points:
            try:
                # 画矩形框
                self.paintPoly(painter)
                # 画顶点
                self.paintVertex(painter)
                # 画拉伸点
                self.paintStretch(painter)
                # 画平移线
                self.paintTranslate(painter)
                # 画选转圆
                self.paintRotate(painter)

            except Exception as e:
                print(e)


    def paintPoly(self, painter):
        line_path = QPainterPath()

        mode = DEFAULT
        if self._hlShape is not None:
            mode = self._hlShape.mode

        mode = SELECTED if self.selected else mode

        linewidth = self.dicPolyMode.get(mode, {}).get('width', 1.0)
        color = self.dicPolyMode.get(mode, {}).get('color', self.line_color)
        fillcolor = self.dicPolyMode.get(mode, {}).get('fillcolor', None)  # 如果为None, 不填充

        line_path.moveTo(self.points[0])
        for i, point in enumerate(self.points):
            line_path.lineTo(point)
        line_path.lineTo(self.points[0])

        pen = QPen(color)
        pen.setWidthF(linewidth)
        painter.setPen(pen)
        painter.drawPath(line_path)
        if fillcolor:
            painter.fillPath(line_path, fillcolor)

    def paintVertex(self, painter):
        """默认均为DEFAULT，某顶点被hover或select ，其他为hover状态"""

        painter.setPen(QPen())
        if self._hlVertex is not None and self._hlVertex.mode == SELECTED:
            index = self._hlVertex.index
            mode = self._hlVertex.mode
            self.drawVertex(painter, [index], mode)
            p_list = list(range(len(self.points)))
            if index in p_list:
                p_list.remove(index)
            # print(p_list)

            self.drawVertex(painter, p_list, HOVERING)

        else:
            mode = DEFAULT if self._hlVertex is None else self._hlVertex.mode
            p_list = list(range(len(self.points)))
            self.drawVertex(painter, p_list, mode)

    def drawVertex(self, painter, indexs, mode):
        """
        绘制顶点
        :param painter: QPainter()
        :param indexs: 索引列表
        :param mode: 点的状态模式
        :return:
        """
        path = QPainterPath()
        d = self.dicVertexMode.get(mode, {}).get('size', 5)
        color = self.dicVertexMode.get(mode, {}).get('fillcolor', self._vertex_fill_color)
        p_type = self.dicVertexMode.get(mode, {}).get('style', self.P_SQUARE)

        for i in indexs:
            point = self.points[i]
            if p_type == self.P_SQUARE:
                path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
            elif p_type == self.P_ROUND:
                path.addEllipse(point, d / 2.0, d / 2.0)

        painter.drawPath(path)
        painter.fillPath(path, color)

    def paintStretch(self, painter):
        """默认均为DEFAULT，某顶点被hover或select ，其他为hover状态"""
        painter.setPen(QPen())
        if self._hlStretch is not None and self._hlStretch.mode == SELECTED:
            index = self._hlStretch.index
            mode = self._hlStretch.mode
            self.drawStretch(painter, [index], mode)
            p_list = list(range(len(self.stretch_points)))
            if index in p_list:
                p_list.remove(index)
            # print(p_list)

            self.drawStretch(painter, p_list, HOVERING)

        else:
            mode = DEFAULT if self._hlStretch is None else self._hlStretch.mode
            p_list = list(range(len(self.stretch_points)))
            self.drawStretch(painter, p_list, mode)

    def drawStretch(self, painter, indexs, mode):
        """
        绘制顶点
        :param painter: QPainter()
        :param indexs: 索引列表
        :param mode: 点的状态模式
        :return:
        """
        path = QPainterPath()
        d = self.dicStretchMode.get(mode, {}).get('size', 5)
        color = self.dicStretchMode.get(mode, {}).get('fillcolor', self._vertex_fill_color)
        p_type = self.dicStretchMode.get(mode, {}).get('style', self.P_ROUND)

        for i in indexs:
            point = self.stretch_points[i]
            if p_type == self.P_SQUARE:
                path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
            elif p_type == self.P_ROUND:
                path.addEllipse(point, d / 2.0, d / 2.0)

        painter.drawPath(path)
        painter.fillPath(path, color)

    def paintTranslate(self, painter):
        """默认为DEFAULT，某线为特殊状态，则另一条为默认"""

        if self._hlTrans is not None and self._hlTrans.mode in [HOVERING, SELECTED]:
            mode = self._hlTrans.mode
            index = self._hlTrans.index
            self.drawTranslate(painter, [index], mode)
            p_list = list(range(len(self.translate_lines)))
            if index in p_list:
                p_list.remove(index)
            self.drawTranslate(painter, p_list, DEFAULT)
        else:
            mode = DEFAULT if self._hlTrans is None else self._hlTrans.mode
            p_list = list(range(len(self.translate_lines)))
            self.drawTranslate(painter, p_list, mode)

    def drawTranslate(self, painter, indexs, mode):
        linewidth = self.dicTranslateMode.get(mode, {}).get('width', 1.0)
        color = self.dicTranslateMode.get(mode, {}).get('color', self.line_color)
        style = self.dicTranslateMode.get(mode, {}).get('style', self.L_SOLID)

        pen = QPen(color, linewidth)
        pen.setStyle(style)
        painter.setPen(pen)

        for i in indexs:
            line = self.translate_lines[i]
            painter.drawLine(line)


    def paintRotate(self, painter):
        """画圆"""

        if self._hlRot is not None and self._hlRot.mode in [HOVERING, SELECTED]:
            mode = self._hlRot.mode
            index = self._hlRot.index if self._hlRot.index is not None else 0
            self.drawRotate(painter, [index], mode)

            # 圆只有一个..
            p_list = list(range(len(self.rotate_lines)))
            if index in p_list:
                p_list.remove(index)
            if p_list:
                self.drawRotate(painter, p_list, DEFAULT)
        else:
            mode = DEFAULT if self._hlRot is None else self._hlRot.mode
            p_list = list(range(len(self.rotate_lines)))
            self.drawRotate(painter, p_list, mode)

    def drawRotate(self, painter, indexs, mode):
        linewidth = self.dicRotateMode.get(mode, {}).get('width', 1.0)
        color = self.dicRotateMode.get(mode, {}).get('color', self.line_color)
        style = self.dicRotateMode.get(mode, {}).get('style', self.L_SOLID)

        rotate_path = QPainterPath()
        for i in indexs:
            rect = self.rotate_lines[i]
            rotate_path.addEllipse(rect)
        pen = QPen(color, linewidth)
        pen.setStyle(style)
        painter.setPen(pen)
        painter.drawPath(rotate_path)


    def nearestVertex(self, point, epsilon):
        """是否临近顶点"""
        min_distance = float("inf")
        min_i = None
        for i, p in enumerate(self.points):
            dist = distance(p - point)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                min_i = i
        return min_i

    def nearestStretch(self, point, epsilon):
        """是否临近拉伸点"""
        min_distance = float("inf")
        min_i = None
        for i, p in enumerate(self.stretch_points):
            dist = distance(p - point)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                min_i = i
        return min_i

    def nearestTranslate(self, point, epsilon):
        """是否临近平移线"""
        min_distance = float("inf")
        post_i = None

        for i in range(len(self.translate_lines)):
            line = [self.translate_lines[i].p1(), self.translate_lines[i].p2()]
            dist = distancetoline(point, line)
            disdrop = disDropPoint(line[0], line[1], point)
            if dist <= epsilon and dist < min_distance and (0 <= disdrop <= distance(line[0] - line[1])):
                min_distance = dist
                post_i = i

        return post_i

    def nearestRotate(self, point, epsilon):
        """是否临近旋转圆"""

        # 只有一个圆，就用下面这个中心和半径即可
        cen = self.getCenterPoint()
        r = self.radius

        min_distance = float("inf")
        post_i = None

        for i in range(len(self.rotate_lines)):
            rect = self.rotate_lines[i]
            # rect = QRectF()
            cen = rect.center()
            r = 0.5 * min(rect.width(), rect.height())
            dist = distance(point - cen)

            if np.fabs(dist - r) <= epsilon and dist < min_distance:
                min_distance = dist
                post_i = i
        return post_i


    def nearestEdge(self, point, epsilon):
        min_distance = float("inf")
        post_i = None
        for i in range(len(self.points)):
            line = [self.points[i - 1], self.points[i]]
            dist = distancetoline(point, line)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                post_i = i
        return post_i

    def containsPoint(self, point):
        """是否包含某个点"""
        return self.makePath().contains(point)

    def makePath(self):
        path = QPainterPath()
        if len(self.points) == 4:
            path.moveTo(self.points[0])
            for p in self.points[1:]:
                path.lineTo(p)

        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def changeByVertex(self, i, offset):
        """
        改变2D框——通过一个顶点
        :param i: 顶点索引
        :param offset: 偏移矢量
        :return:
        """
        def changeRect(i, offset):
            # 设i点为C，变为C1， 对角点=A点不动，根据C1调节B、D
            pc, pd, pa, pb = self.points[i], self.points[(i + 1) % 4], self.points[(i + 2) % 4], self.points[
                (i + 3) % 4]

            pc1 = pc + offset
            pb1 = projectionPoint(pa, pb, pc1)
            pd1 = projectionPoint(pa, pd, pc1)
            if None in [pb1, pd1]:
                return
            # 加异常判定，长度不可以接近0，否则图形坍缩，不能继续编辑了
            dist = min(distance(pb1 - pa), distance(pd1 - pa))
            if dist <= 2:
                return

            new_points = [pc1, pd1, pa, pb1]
            for j in range(4):
                self.points[(i + j) % 4] = new_points[j]
            self.updatePoints()

        def changeQuad(i, offset):
            # i-1 点平移量 delta是 offset在（i-2,i-1）
            v1 = self.points[(i + 3) % 4] - self.points[(i + 2) % 4]
            off1 = projectionVector(v1, offset)

            v2 = self.points[(i + 1) % 4] - self.points[(i + 2) % 4]
            off2 = projectionVector(v2, offset)
            # TODO 需要做防坍缩处理
            self.moveVertexBy(i, offset)
            self.moveVertexBy((i + 3) % 4, off1)
            self.moveVertexBy((i + 1) % 4, off2)
            self.updatePoints()

        if len(self.points) == 4:
            # TODO 目前适用于矩形
            changeRect(i, offset)

    def changeByStretch(self, i, offset):
        """
        改变2D框——通过一个拉伸点, 适用于平行四边形
        :param i: 拉伸点索引
        :param offset: 偏移矢量
        :return:
        """
        if len(self.points) == 4:
            # TODO 目前仅是矩形
            # 第i拉伸点为 i 和 i-1 顶点中点
            # 拉伸点i移动offset == 顶点i移动offset在（i+1,i）投影
            v1 = self.points[i] - self.points[(i + 1) % 4]
            v2 = offset
            new_offset = projectionVector(v1, v2)
            if new_offset:
                self.changeByVertex(i, new_offset)


    def changeByRotate(self, i, pos1, pos2):
        """
        旋转
        :param i: 圆索引，目前只有1个
        :param pos1: 前点
        :param pos2: 后点
        :return:
        """
        ret = None
        if 0 <= i < len(self.rotate_lines):
            rect = self.rotate_lines[i]
            cen = rect.center()  # 圆心

            if min(distance(pos1 - cen), distance(pos2 - cen)) < 0.01:
                return ret
            # 求夹角
            theta = angleVector(pos1 - cen, pos2 - cen)
            # print('theta=',theta)

            for j in range(len(self.points)):
                self.points[j] = turnPoint(cen, self.points[j], theta)
            self.updatePoints()
            ret = theta
        return ret

    def changeByMove(self, i, offset):
        """
        移动2D框
        :param i: 平移线索引，如果为None，按照鼠标平移
        :param offset:
        :return:
        """
        delta = offset
        # print("i = ", i)
        if i is not None and 0 <= i < len(self.translate_lines):
            line = [self.translate_lines[i].p1(), self.translate_lines[i].p2()]
            v1 = line[1] - line[0]
            delta = projectionVector(v1, offset)
            # print('delta', delta)

        if delta:
            self.moveBy(delta)
            self.updatePoints()

    def turn(self, theta):
        """
        绕着几何中心旋转
        :param theta:
        :return:
        """
        cen = self.getCenterPoint()
        for j in range(len(self.points)):
            self.points[j] = turnPoint(cen, self.points[j], theta)
        self.updatePoints()

    def highlightPoly(self, i, action):
        self._hlShape = ShapeShowMode(i, mode=action)

    def highlightVertex(self, i, action):
        self._hlVertex = ShapeShowMode(i, mode=action)

    def highlightStretch(self, i, action):
        self._hlStretch = ShapeShowMode(i, mode=action)

    def highlightTrans(self, i, action):
        self._hlTrans = ShapeShowMode(i, mode=action)

    def highlightRot(self, i, action):
        self._hlRot = ShapeShowMode(i, mode=action)


    def highlightClear(self):
        """Clear the highlighted point"""
        self._highlightVertexIndex = None

        self._hlShape = None
        self._hlVertex = None
        self._hlStretch = None
        self._hlTrans = None
        self._hlRot = None

    def copyPoints(self):
        """深拷贝点位信息"""
        return [QPointF(p.x(), p.y()) for p in self.points]

    def copy(self):
        c_shape = copy.deepcopy(self)
        return c_shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value


if __name__ == "__main__":
    s = ViewShape()