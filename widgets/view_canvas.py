# !/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import copy
from utils.qt_math_util import *
from utils.image_util import *
from widgets.view_shape import ViewShape, HOVERING, SELECTED

from PyQt5.QtCore import Qt

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor
CURSOR_MOVE_IMG = Qt.SizeAllCursor


DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)  # bf hovering
DEFAULT_FILL_COLOR = QColor(0, 255, 0, 60)  # hovering 悬浮填充颜色
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)  # selected
DEFAULT_SELECT_FILL_COLOR = QColor(0, 255, 0, 100)  # selected  # 选中后填充颜色
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 255, 0, 255)  # 默认点被填充颜色
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 255, 255, 200)  # hovering 点悬浮时候的颜色
MIN_Y_LABEL = 10


class CanvasView(QWidget):

    V_BIRD = 0
    V_FRONT = 1
    V_SIDE = 2
    # 键盘触发步距
    MOVE_SPEED = 1
    ROT_SPEED = 1.0

    epsilon = 8.0
    mode = 1  # 显示辅助线模式0,1，0不显示旋转线，不能旋转
    moveShape = pyqtSignal(int, list)
    rotShape = pyqtSignal(int, float)
    finishShape = pyqtSignal()  # 完成调整
    zoomView = pyqtSignal(int, float)  # 缩放视野
    rightpressShape = pyqtSignal(int,int)  # axiong add 用于发送鼠标右键点击

    def __init__(self, parent=None, view=V_BIRD):
        super(CanvasView, self).__init__(parent=parent)
        self.resize(200, 200)

        self._view_mode = view
        self._painter = QPainter()
        self.pixmap = None

        self.shape = ViewShape()
        self.shape.rot_enable = True if self._view_mode == self.V_BIRD else False  # 俯视图可旋转

        # self.shape.points = [
        #     QPointF(100, 100),
        #     QPointF(300, 100),
        #     QPointF(300, 300),
        #     QPointF(100, 300)
        # ]
        # self.shape.points_to_coord()
        # print(self.shape.coord_points)
        self.old_shape = ViewShape()  # 为计算框变化建立的对象

        self.hShape = None  # 光标悬浮到2D框，hShape为this Shape——设定为只要鼠标有接触
        self.hVertex = None  # 光标悬浮在顶点， 序号0,1...
        self.hStretch = None  # 光标悬浮拉伸点，序号0,1...
        self.hTransline = None  # 光标悬浮在平移线 , 序号0,1...
        self.hRotline = None  # 光标悬浮在旋转圆 , 序号0,1...

        self.selectedShape = None  # 点击选中对象
        self.prevPoint = QPointF()  # 记录拖动时候上一个点位置

        self._is_moving = False  # 是否在移动中
        self._is_key_moving = False  # 是否键盘控制移动

        # self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)  # 在进入离开事件设置了焦点，这里不用也行

    def setViewMode(self, view):
        self._view_mode = view
        self.shape.rot_enable = True if self._view_mode == self.V_BIRD else False

    def getViewMode(self):
        return self._view_mode

    def setPoints(self, points, flg=True):
        """
        设置长方形点
        :param points: [(x,y) * 4]
        :param flg:
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        # print(type(self.shape))
        try:
            self.shape.coord_points = points
            self.shape.updatePoints(False)
            if flg:
                self.update()
        except Exception as e:
            print(e)

    def setImage(self, img):
        self.pixmap = array_qpixmap(img, False)
        if self.pixmap:
            # print('setImage=', self.pixmap.width(), self.pixmap.height())
            pass
        self.update()


    def handleMoveEventHovering(self, ev):
        """鼠标划过"""
        # pos = self.transformPos(ev.pos())
        pos = ev.pos()
        # print("handleMoveEventHovering== ", pos)
        try:

            # 是否在顶点
            index = self.shape.nearestVertex(pos, self.epsilon)
            if index is not None:
                if self.hShape is not None:
                    self.hShape.highlightClear()
                self.resetHover()
                self.hVertex = index
                self.hShape = self.shape
                self.shape.highlightVertex(index, HOVERING)
                self.overrideCursor(CURSOR_POINT)
                # self.setToolTip(self.tr("Click & drag to move point"))
                # self.setStatusTip(self.toolTip())
                self.update()
                return

            # 是否在拉伸点
            index = self.shape.nearestStretch(pos, self.epsilon)
            if index is not None:
                if self.hShape is not None:
                    self.hShape.highlightClear()
                self.resetHover()
                self.hStretch = index
                self.hShape = self.shape
                self.shape.highlightStretch(index, HOVERING)
                self.overrideCursor(CURSOR_POINT)
                self.update()
                return

            # 是否在平移线
            index = self.shape.nearestTranslate(pos, self.epsilon)
            if index is not None:
                if self.hShape is not None:
                    self.hShape.highlightClear()
                self.resetHover()
                self.hTransline = index
                self.hShape = self.shape
                self.shape.highlightTrans(index, HOVERING)
                self.overrideCursor(CURSOR_MOVE_IMG)
                self.update()
                return

            # 是否在内部
            if self.shape.containsPoint(pos):
                if self.hShape is not None:
                    self.hShape.highlightClear()
                self.resetHover()
                self.hShape = self.shape
                self.shape.highlightPoly(0, HOVERING)
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                return

            # 是否旋转圆
            index = self.shape.nearestRotate(pos, self.epsilon)
            if index is not None:
                if self.hShape is not None:
                    self.hShape.highlightClear()
                self.resetHover()
                self.hRotline = index
                self.hShape = self.shape
                self.shape.highlightRot(index, HOVERING)
                self.overrideCursor(CURSOR_MOVE_IMG)
                self.update()
                return

            self.overrideCursor(CURSOR_DEFAULT)
            self.unHighlight()

        except Exception as e:
            print(e)
            return


    def handleMoveEventPressing(self, ev):
        # pos = self.transformPos(ev.pos())
        pos = ev.pos()
        ''' 处理左键拖动框或者顶点 '''
        if Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self._is_moving = True
                self.repaint()
                # self.movingShape = True
            elif self.selectedStretch():
                self.boundedMoveStretch(pos)
                self._is_moving = True
                self.repaint()
            elif self.selectedTransline():
                self.boundedMovePoly(pos)
                self._is_moving = True
                self.repaint()
            elif self.selectedRotline():
                self.boundedMoveRot(pos)
                self._is_moving = True
                self.repaint()
            elif self.hShape is not None:
                self.boundedMovePoly(pos)
                self._is_moving = True
                self.repaint()

            return True

    def mouseMoveEvent(self, ev):
        # print('mouseMoveEvent')
        """Update line with last point and current coordinates."""

        if len(self.shape) != 4:
            return

        if Qt.LeftButton & ev.buttons():
            self.handleMoveEventPressing(ev)

        else:
            self._is_moving = False
            self.handleMoveEventHovering(ev)

    def mousePressEvent(self, ev):
        pos = ev.pos()
        if ev.button() == Qt.LeftButton:
            self.prevPoint = pos

        # 用于记录，右击三视图长方体四条边自动贴合点云 axiong add 20221109
        if ev.button() == Qt.RightButton:
            if self.selectedStretch():
                self.rightpressShape.emit(self._view_mode,self.hStretch)

    def mouseReleaseEvent(self, ev):
        if self._is_moving:
            self._is_moving = False
            self.finishShape.emit()

    def keyPressEvent(self, ev):
        modifiers = ev.modifiers()
        key = ev.key()
        # print('keyPressEvent')
        if len(self.shape) != 4:
            return

        step = self.MOVE_SPEED
        turn_step = self.ROT_SPEED

        if modifiers == Qt.ShiftModifier:
            step *= 5
            turn_step *= 3

        move_dic = {
            Qt.Key_A: (QPointF(-step, 0.0), False),
            Qt.Key_D: (QPointF(step, 0.0), False),
            Qt.Key_W: (QPointF(0.0, -step), False),
            Qt.Key_S: (QPointF(0.0, step), False),
            Qt.Key_Q: (-turn_step, True),
            Qt.Key_E: (turn_step, True),
        }
        if key in move_dic.keys():
            self.moveByKeyboard(move_dic[key])
            self._is_key_moving = True

        if self._is_key_moving:
            self.repaint()
            ev.ignore()

    def keyReleaseEvent(self, ev):
        # modifiers = ev.modifiers()
        if self._is_key_moving:
            self._is_key_moving = False
            self.finishShape.emit()

    def wheelEvent(self, ev):
        if not hasattr(ev, "angleDelta"):
            return
        delta = ev.angleDelta()
        h_delta = delta.x()
        v_delta = delta.y()
        mods = ev.modifiers()
        self.zoomView.emit(self._view_mode, v_delta)
        ev.accept()  # 将事件接收不再上传，用ignore 图片平移不准

    def moveByKeyboard(self, *args):
        # print('moveByKeyboard ', offset)
        offset, rot = args[0]
        shape = self.shape
        self.old_shape.points = shape.copyPoints()
        if not rot:
            shape.changeByMove(None, offset)
            self.getShapeMoved(self.old_shape, shape)  # 计算变化量
        else:
            if self.shape.rot_enable:
                shape.turn(offset)
                self.sendShapeChange(True, offset)

    def selectedVertex(self):
        return self.hVertex is not None

    def selectedStretch(self):
        return self.hStretch is not None

    def selectedTransline(self):
        return self.hTransline is not None

    def selectedRotline(self):
        return self.hRotline is not None

    def resetHover(self):
        self.hShape = self.hVertex = self.hStretch = self.hTransline = self.hRotline = None

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
            self.update()
        self.resetHover()

    def boundedMoveVertex(self, pos):
        """处理顶点移动"""
        index, shape = self.hVertex, self.hShape

        self.old_shape.points = shape.copyPoints()
        delta_pos = pos - self.prevPoint
        shape.changeByVertex(index, delta_pos)
        self.prevPoint = pos
        self.getShapeMoved(self.old_shape, shape)  # 计算变化量

    def boundedMoveStretch(self, pos):
        """处理拉伸点移动"""
        index, shape = self.hStretch, self.hShape
        self.old_shape.points = shape.copyPoints()
        delta_pos = pos - self.prevPoint
        shape.changeByStretch(index, delta_pos)
        self.prevPoint = pos
        self.getShapeMoved(self.old_shape, shape)  # 计算变化量

    def boundedMovePoly(self, pos):
        """平移，如果在平移线上，仅在平移线方向平移"""
        shape = self.hShape
        index = None
        self.old_shape.points = shape.copyPoints()
        if self.selectedTransline():
            index = self.hTransline
        delta_pos = pos - self.prevPoint
        shape.changeByMove(index, delta_pos)
        self.prevPoint = pos
        self.getShapeMoved(self.old_shape, shape)  # 计算变化量

    def boundedMoveRot(self, pos):
        """ 旋转 """
        index, shape = self.hRotline, self.hShape

        # delta_pos = pos - self.prevPoint
        delta_ang = shape.changeByRotate(index, self.prevPoint, pos)
        self.prevPoint = pos
        if delta_ang is not None:
            self.sendShapeChange(True, delta_ang)

    def getShapeMoved(self, old, new):
        """
        计算shape变化量
        :param old:
        :param new:
        :return:
        """
        try:
            old_center = old.getCenterPoint()
            new_center = new.getCenterPoint()

            delta_cen = [new_center.x() - old_center.x(), new_center.y() - old_center.y()]

            old_wh = old.getHeightWidth()
            new_wh = new.getHeightWidth()
            delta_wh = [new_wh[0] - old_wh[0], new_wh[1] - old_wh[1]]

            self.sendShapeChange(False, [delta_cen, delta_wh])
        except Exception as e:
            print(e)

    def sendShapeChange(self, isRot=False, *args):
        """
        发送框变化数据
        :param isRot: 是否旋转
        :param args: 参数
        :return:
        """
        if isRot:
            delta_ang = args[0]
            # print("delta_ang=", delta_ang)
            self.rotShape.emit(self._view_mode, delta_ang)
        else:
            # print("args=", args)
            delta_cen, delta_wh = args[0]
            self.moveShape.emit(self._view_mode, [delta_cen, delta_wh])

    def paintEvent(self, event):
        # if not self.pixmap:
        #     return super(CanvasView, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.scale(1.0, 1.0)
        # 清理一次
        p.eraseRect(QRectF(0, 0, self.size().width(), self.size().height()))
        if self.pixmap:
            p.drawPixmap(0, 0, self.pixmap)

        # 多个shape情况
        # for shape in self.shapes:
        #     if (shape.selected or not self._hideBackround) and self.isVisible(shape):
        #         shape.fill = shape.selected or shape == self.hShape
        #         shape.paint(p)

        # 仅点在内部时高亮框，其他位置不高亮
        # if self.shape == self.hShape:
        #     self.shape.highlightPoly(0, HOVERING)
        if self.shape.selected:
            self.shape.highlightPoly(0, SELECTED)
        self.shape.paint(p)

        p.end()
        pass

    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def overrideCursor(self, cursor):
        # self.restoreCursor()
        self._cursor = cursor
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def reset(self):
        self.restoreCursor()
        self.setPoints([])
        self.setImage(None)
        self.update()


    # 定义点序列
    # 3--------0
    # |        |-----  车的方向
    # 2--------1

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        # if self.pixmap:
        #     return self.scale * self.pixmap.size()
        return super(CanvasView, self).minimumSizeHint()
    
    def resizeEvent(self, event):
        super(CanvasView, self).resizeEvent(event)

    def enterEvent(self, event):
        self.setMouseTracking(True)
        self.setFocus()
        super(CanvasView, self).enterEvent(event)

    def leaveEvent(self, event):

        self.restoreCursor()
        super(CanvasView, self).leaveEvent(event)
        self.clearFocus()
        self.setMouseTracking(False)


import sys
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = QWidget()
    mainwin.resize(600, 500)
    win = CanvasView(view=0)
    # win = CanvasView(view=1)
    # win = CanvasView(view=2)
    btn = QPushButton('按钮')

    vbox = QVBoxLayout(mainwin)
    vbox.setContentsMargins(0,0,0,0)
    vbox.addWidget(win)
    # vbox.addWidget(btn)

    ps = [
        (100, 100),
        (300, 100),
        (300, 300),
        (100, 300)
    ]
    win.setPoints(ps)

    mainwin.show()
    sys.exit(app.exec_())

