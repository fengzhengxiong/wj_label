# Copyright (c) <2021-8> An-Haiyang
# 定制pyqt控件
#
# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time : 2021/08
@Author : 咖啡凉了_hy
@File : ImgWidget.py
@Function :
@History :
@Version : V1.0
"""

import sys
import os
import os.path as osp
import cv2

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np


class ImgWidget(QWidget):
    """
    自定义图像显示控件
    图像放大缩小：ctrl+滚轮
    图像平移：左键拖动，键盘方向键
    图像适合窗口：左键双击
    图像原图大小：右键双击
    图像全屏显示：中键双击
    控件大小改变：全屏模式将保持，若非，则为适应窗口模式
    接口说明：

    load_image 显示图像
    clean 清空图像
    catpoint_enable 图像选点
    catpoint_disable 取消选点
    img_zoom 图像缩放
    img_move 图像移动

    """
    signal_pixpos = pyqtSignal(float, float)  # 鼠标像素坐标 x y
    signal_pos = pyqtSignal(float, float)  # 鼠标窗口坐标 x y
    signal_img = pyqtSignal(float, float, float, float)  # 输出图像位置 x y w h
    signal_outpoint = pyqtSignal(float, float, int)  # 输出get到点位 x y index=第几个点
    signal_imgobjname = pyqtSignal(str)

    def __init__(self, parent=None, pixmap=None, path=None):
        super().__init__(parent)
        self.parent = parent
        # self.resize(520, 520)
        self.img = pixmap  # QPixmap类型，原始图像
        self.scaled_img = self.img  # 显示的图像
        self.img_path = path  # 图像路径
        self.img_size = [0, 0]  # 图像尺寸
        if self.img is not None:
            self.img_size = [self.img.size().width(), self.img.size().height()]

        self.img_position = QPointF(0, 0)  # 图像起点坐标
        self.coord_pix = QPointF(0.0, 0.0)  # 鼠标实时像素坐标
        self.scale = [1, 1]  # 图像缩放比例

        self.left_pressing = False  # 左键按下状态
        self.right_pressing = False  # 右键按下状态
        self.mid_pressing = False  # 中键按下状态

        self.scale_mode = 0  # 0:不缩放，1 控件缩放 ，2 按照宽度调整 ，3 按照高度调整 ， 4 全屏
        self.cat_point_flag = False  # 获取点位标志位
        self.cat_count = 0  # 获取点的个数，最多获取30个
        self.cat_cur_num = 0  # 当前获取第几个
        # print('size', self.width(), self.height())

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)

    def load_image(self, picture, path=None):
        """
        加载图像
        :param picture: 可以是路径，也可以是QPixmap对象
        :param path:
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        # qt显示图像支持的文件格式
        extensions = ['.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        # extensions[
        #     '.bmp', '.cur', '.gif', '.icns', '.ico', '.jpeg', '.jpg', '.pbm', '.pgm', '.png', '.ppm', '.svg', '.svgz',
        #  '.tga', '.tif', '.tiff', '.wbmp', '.webp', '.xbm', '.xpm']
        if isinstance(picture, str):
            ''' 输入为路径 '''
            if os.path.exists(picture) and os.path.splitext(picture)[1] in extensions:
                if os.path.splitext(picture)[1] in ['.ico', '.svg', '.tif', '.tiff']:
                    # 也不知道具体区别，QPixmap 对各种格式图像都可以转换，不用cv2 也行吧
                    pixmap = QPixmap(picture)
                else:
                    cvimg = cv2.imdecode(np.fromfile(picture, dtype=np.uint8), 1)
                    print(type(cvimg))
                    QImg = self.cvimg_to_QImage(cvimg)
                    pixmap = QPixmap.fromImage(QImg)
                self.img = pixmap
                self.img_path = picture
                self.img_size = [self.img.size().width(), self.img.size().height()]
        elif isinstance(picture, QPixmap):
            self.img = picture
            self.img_path = path
            self.img_size = [self.img.size().width(), self.img.size().height()]
        else:
            return
        # 适合窗口，载入图片
        self.adapt_window()

    def cvimg_to_QImage(self, cvimg):
        """
        转化cv图像到Qt图像
        :param cvimg:
        :return:
        """
        height, width, depth = cvimg.shape
        cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB, cvimg)
        QImg = QImage(cvimg.data, width, height, width * depth, QImage.Format_RGB888)
        return QImg

    def qtpixmap_to_cvimg(self, qt_pixmap):
        """
        qt pixmap转化cvimg
        :param qt_pixmap:
        :return:
        """
        qimg = qt_pixmap.toImage()
        temp_shape = (qimg.height(), qimg.bytesPerLine() * 8 // qimg.depth())
        temp_shape += (4,)
        ptr = qimg.bits()
        ptr.setsize(qimg.byteCount())
        result = np.array(ptr, dtype=np.uint8).reshape(temp_shape)
        result = result[..., :3]
        return result

    def adapt_window(self):
        """
        自适应窗口，图像..
        :return:
        """
        if self.img:
            w1, h1 = self.img.width(), self.img.height()
            w2, h2 = self.size().width(), self.size().height()
            k1 = float(w1) / h1
            k2 = float(w2) / h2
            if k1 > k2:
                self.adapt_width()
            else:
                self.adapt_height()
            self.repaint()

    def adapt_width(self):
        """
        适应宽度
        :return:
        """
        if self.img:
            w1, h1 = self.img.width(), self.img.height()
            w2, h2 = self.size().width(), self.size().height()
            # print(w1, h1, w2, h2)
            self.scaled_img = self.img.scaledToWidth(w2)
            # self.scaled_img.scaled()
            cur_h = float(w2) / w1 * h1
            self.img_position.setX(0.0)
            self.img_position.setY(float(0.5 * (h2 - cur_h)))
            self.scale_mode = 2
            self.repaint()

    def adapt_height(self):
        """
        适应高度
        :return:
        """
        if self.img:
            w1, h1 = self.img.width(), self.img.height()
            w2, h2 = self.size().width(), self.size().height()
            self.scaled_img = self.img.scaledToHeight(h2)
            cur_w = float(h2) / h1 * w1
            self.img_position.setX(float(0.5 * (w2 - cur_w)))
            self.img_position.setY(0.0)
            self.scale_mode = 3
            self.repaint()

    def adape_orignal(self):
        """
        原始尺寸
        :return:
        """
        if self.img:
            self.scaled_img = self.img.scaledToWidth(self.img.width())
            self.img_position.setX(0)
            self.img_position.setY(0)
            self.scale_mode = 0
            self.repaint()

    def adape_screen(self):
        """
        全屏显示
        :return:
        """
        if self.img:
            self.scaled_img = self.img.scaled(self.width(), self.height())
            self.img_position.setX(0)
            self.img_position.setY(0)
            self.scale_mode = 4
            self.repaint()

    def reset_position(self):
        """
        重置尺寸，如果是全屏模式，就一直保持全屏模式
        :return:
        """
        if self.img:
            if self.scale_mode == 4:
                self.adape_screen()
            else:
                self.adapt_window()

    def clean(self):
        """
        清空画布
        :return:
        """
        self.img = None
        self.scaled_img = None
        if self.cat_point_flag:
            self.catpoint_disable()
        self.repaint()
        self.signal_pixpos.emit(0.0, 0.0)

    def catpoint_enable(self, count=1):
        """
        设置获取点使能，及个数
        :param count: 连续获取点个数，限制在30个
        :return:
        """
        # print('catpoint_enable')
        if self.img and 1 <= count <= 30:
            self.cat_count = count
            self.cat_point_flag = True
            self.cat_cur_num = 0

    def catpoint_disable(self):
        """
        取消获取点
        :return:
        """
        self.cat_count = 0
        self.cat_point_flag = False
        self.cat_cur_num = 0
        QApplication.restoreOverrideCursor()

    def map_to_image(self, pos):
        """
        坐标转化到像素坐标
        :param pos: 控件坐标
        :return:
        """
        delta = pos - self.img_position
        ret = QPointF(delta.x() / self.scale[0], delta.y() / self.scale[1])
        return ret

    def img_zoom(self, event=None, ratio=1.0):
        """
        缩放
        :param event: 鼠标事件
        :param ratio: 比例
        :return:
        """
        if self.img is None:
            return

        old_w = self.scaled_img.width()
        old_h = self.scaled_img.height()
        # 新宽度
        new_w = old_w * ratio
        if new_w < 10 or new_w > 10000:
            return

        # 新高度
        # 不用下面这里，因为缩放次数多了出现尺寸精度误差，导致图像比例失衡
        # new_h = new_w * self.scaled_img.height() / self.scaled_img.width()
        if self.scale_mode == 4:
            new_h = new_w * self.size().height() / self.size().width()
        else:
            new_h = new_w * self.img.height() / self.img.width()

        # 计算图像位置，默认以图像中心缩放
        px = self.img_position.x() - self.scaled_img.width() * (ratio - 1) / 2
        py = self.img_position.y() - self.scaled_img.height() * (ratio - 1) / 2
        # 以鼠标位置缩放
        if event:
            e = event
            if 0 <= e.x() <= self.width() and 0 <= e.y() <= self.height():
                dis_w = (e.x() - self.img_position.x()) * ratio
                dis_h = (e.y() - self.img_position.y()) * ratio
                px = e.x() - dis_w
                py = e.y() - dis_h
        self.img_position.setX(px)
        self.img_position.setY(py)
        del self.scaled_img
        self.scaled_img = self.img.scaled(new_w, new_h)
        self.repaint()

    def img_move(self, dis=QPointF(0.0, 0.0)):
        """
        移动
        :param dis:
        :return:
        """
        self.img_position += dis
        self.repaint()

    def enterEvent(self, ev):
        """
        如果拾取点位功能开启，光标变为十字
        :param ev:
        :return:
        """
        if self.cat_point_flag:
            self.overrideCursor(Qt.CrossCursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    def currentCursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def overrideCursor(self, cursor):
        if self.currentCursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restoreCursor(self):
        QApplication.restoreOverrideCursor()

    def mouseMoveEvent(self, e):  # 重写移动事件
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        self.signal_pos.emit(e.pos().x(), e.pos().y())
        if self.img:
            res = self.map_to_image(e.pos())
            self.coord_pix.setX(round(res.x(), 2))
            self.coord_pix.setY(round(res.y(), 2))
            self.signal_pixpos.emit(self.coord_pix.x(), self.coord_pix.y())
        else:
            self.coord_pix.setX(0)
            self.coord_pix.setY(0)

        # 鼠标按下，移动过程拖动图像
        if self.left_pressing:
            self.img_move(e.pos() - self.start_pos)
            self.start_pos = e.pos()

    def mousePressEvent(self, e):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if e.button() == Qt.LeftButton:
            if self.cat_point_flag:  # 如果拾取点位，则不能让平移
                self.cat_cur_num += 1
                self.signal_outpoint.emit(self.coord_pix.x(), self.coord_pix.y(), self.cat_cur_num)
                print('cat= ', self.coord_pix.x(), self.coord_pix.y(), self.cat_cur_num)
                if self.cat_cur_num >= self.cat_count:
                    self.catpoint_disable()
            else:
                self.left_pressing = True
                self.start_pos = e.pos()
                self.setCursor(QCursor(Qt.OpenHandCursor))
        elif e.button() == Qt.RightButton:
            self.right_pressing = True
        elif e.button() == Qt.MiddleButton:
            self.mid_pressing = True

    def mouseReleaseEvent(self, e):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if e.button() == Qt.LeftButton:
            self.left_pressing = False
            self.setCursor(QCursor(Qt.ArrowCursor))
        elif e.button() == Qt.RightButton:
            self.right_pressing = False
        elif e.button() == Qt.MiddleButton:
            self.mid_pressing = False

    def wheelEvent(self, e):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if self.img is None:
            return
        h_delta = e.angleDelta().x()
        v_delta = e.angleDelta().y()
        mods = e.modifiers()
        # if Qt.ControlModifier == int(mods) and v_delta:
        if v_delta:
            if e.angleDelta().y() < 0:
                self.img_zoom(event=e, ratio=0.9)
            elif e.angleDelta().y() > 0:
                self.img_zoom(event=e, ratio=1.1)

    def mouseDoubleClickEvent(self, e):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if self.img:
            if e.button() == Qt.LeftButton:
                # print('------  ', self.objectName())
                self.adapt_window()
                # self.signal_imgobjname.emit(self.objectName())
            elif e.button() == Qt.RightButton:
                self.adape_orignal()
            elif e.button() == Qt.MiddleButton:
                self.adape_screen()

        if e.button() == Qt.LeftButton:
            self.signal_imgobjname.emit(str(self.objectName()))


    def keyPressEvent(self, e):
        key = e.key()
        if key == Qt.Key_Left:
            self.img_move(dis=QPointF(-5.0, 0))
        elif key == Qt.Key_Right:
            self.img_move(dis=QPointF(+5.0, 0))
        elif key == Qt.Key_Up:
            self.img_move(dis=QPointF(0.0, -5.0))
        elif key == Qt.Key_Down:
            self.img_move(dis=QPointF(0.0, 5.0))
        elif key == Qt.Key_Escape:
            if self.cat_point_flag:
                self.catpoint_disable()

    def resizeEvent(self, e):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if self.img:
            self.reset_position()

    def paintEvent(self, e):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if self.img:
            self.signal_img.emit(self.img_position.x(), self.img_position.y(), self.scaled_img.width(),
                                 self.scaled_img.height())
            painter.drawPixmap(self.img_position, self.scaled_img)
            #  更新缩放比例
            self.scale[0] = self.scaled_img.width() / self.img.width()
            self.scale[1] = self.scaled_img.height() / self.img.height()

        else:
            rect = QRect(0, 0, self.size().width(), self.size().height())
            painter.eraseRect(rect)
        painter.end()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    a = ImgWidget()
    a.load_image('./7_0.png')
    a.show()
    sys.exit(app.exec_())