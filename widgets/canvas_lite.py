
# !/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QApplication, QMenu, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QPointF, QRectF, QLineF
from PyQt5.QtGui import QPainter, QColor, QCursor, QPixmap, QBrush

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_MOVE_IMG = Qt.SizeAllCursor

MOVE_SPEED = 2.0
# class Canvas(QGLWidget):
MOVE_IMG_STEP = 50


class Canvas(QWidget):
    zoomRequest = pyqtSignal(int, QPointF)
    scrollRequest = pyqtSignal(int, int, bool)
    coordChanged = pyqtSignal(float, float)

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)

        self.pixmap = QPixmap()
        self.scale = 1.0
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT

        self.setFocusPolicy(Qt.StrongFocus)

        self.panStartPos = QPointF()  # 移动图片用的，起始点位

    def setScale(self, value):
        self.scale = value

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def transformPos(self, point: QPointF):
        return QPointF(point.x() / self.scale, point.y() / self.scale) - self.offsetToCenter()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def reset(self):
        self.pixmap = QPixmap()
        self.scale = 1.0
        self.update()

    def resetState(self):
        self.restoreCursor()
        self.pixmap = QPixmap()
        self.scale = 1.0
        self.update()

    def paintEvent(self, event):
        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())
        # 清理一次
        p.eraseRect(QRectF(0, 0, self.size().width(), self.size().height()))
        if self.pixmap:
            p.drawPixmap(0, 0, self.pixmap)

        p.end()

    def mouseMoveEvent(self, ev):
        # print('mouseMoveEvent')
        pos = self.transformPos(ev.pos())
        self.coordChanged.emit(pos.x(), pos.y())

        ''' 中键按下拖动，移动图片，无论何种模式下'''
        if Qt.MiddleButton & ev.buttons():
            # 平移图片
            self.overrideCursor(CURSOR_MOVE_IMG)
            # self.setCursor(CURSOR_MOVE_IMG)
            delta_x = pos.x() - self.panStartPos.x()
            delta_y = pos.y() - self.panStartPos.y()
            self.scrollRequest.emit(delta_x, Qt.Horizontal, True)
            self.scrollRequest.emit(delta_y, Qt.Vertical, True)
            self.update()
            return

    def mousePressEvent(self, ev):
        pos = self.transformPos(ev.pos())

        if ev.button() == Qt.MiddleButton:
            self.overrideCursor(CURSOR_MOVE_IMG)
            self.panStartPos = pos

    def mouseReleaseEvent(self, ev):
        pos = self.transformPos(ev.pos())
        self.restoreCursor()

    def wheelEvent(self, ev):
        if not hasattr(ev, "angleDelta"):
            return
        delta = ev.angleDelta()
        h_delta = delta.x()
        v_delta = delta.y()
        mods = ev.modifiers()
        if v_delta:
            self.zoomRequest.emit(v_delta, ev.pos())
        ev.accept()  # 将事件接收不再上传，用ignore 图片平移不准

    def keyPressEvent(self, ev):
        modifiers = ev.modifiers()
        key = ev.key()
        # print(ev.type())

        move_dic = {
            Qt.Key_A: (MOVE_IMG_STEP, Qt.Horizontal, False),
            Qt.Key_D: (-MOVE_IMG_STEP, Qt.Horizontal, False),
            Qt.Key_W: (MOVE_IMG_STEP, Qt.Vertical, False),
            Qt.Key_S: (-MOVE_IMG_STEP, Qt.Vertical, False),

        }
        if key in move_dic.keys():
            dis, direct, flg = move_dic[key]
            self.scrollRequest.emit(dis, direct, flg)

        # ev.ignore()
        super(Canvas, self).keyPressEvent(ev)

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def resizeEvent(self, event):
        # print('canview resizeEvent')
        super(Canvas, self).resizeEvent(event)

    def enterEvent(self, event):
        self.setMouseTracking(True)
        self.setFocus()
        self.overrideCursor(self._cursor)
        super(Canvas, self).enterEvent(event)

    def leaveEvent(self, event):
        self.restoreCursor()
        super(Canvas, self).leaveEvent(event)
        self.clearFocus()
        self.setMouseTracking(False)

    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def overrideCursor(self, cursor):
        self._cursor = cursor
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()


