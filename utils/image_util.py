# -*- coding: utf-8 -*-
# !/usr/bin/env python


from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import cv2
import PIL
import PIL.Image
import os.path as osp
import sys


def img_to_pix(path, def_ret=None):
    """
    图像转为QPixmap
    :param path:
    :return:
    """
    if not osp.exists(path):
        print(f'error in fun[{sys._getframe().f_code.co_name}]')
        return None
    cvimg = cv2.imdecode(np.fromfile(path, dtype=np.uint8), 1)

    h, w, d = cvimg.shape
    cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    image = QImage(cvimg.data, w, h, w * d, QImage.Format_RGB888)
    if image.isNull():
        return def_ret
    pix = QPixmap.fromImage(image)
    return pix


def array_qpixmap(arr_img, isBGR=True, def_ret=None):
    """
    np数据转qpixmap
    :param arr_img:
    :param def_ret:
    :return:
    """
    try:
        if arr_img is None:
            return def_ret
        h, w, d = arr_img.shape
        if isBGR:
            img = cv2.cvtColor(arr_img, cv2.COLOR_BGR2RGB)
        else:
            img = arr_img.copy()
        image = QImage(img.data, w, h, w * d, QImage.Format_RGB888)
        if image.isNull():
            return def_ret
        pix = QPixmap.fromImage(image)
        return pix
    except Exception as e:
        print(e)
        return def_ret



def cv2_load(path):
    """
    cv2读取图片信息，为数组
    :param path: 路径
    :return: np数组,BGR格式
    """
    cvimg = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    # cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    return cvimg


def array2qimage(arr_img, isBGR=True, def_ret=None):
    """
    np - QImage
    :param arr_img:
    :param isBGR:
    :param def_ret:
    :return:
    """
    try:
        if arr_img is None:
            return def_ret
        h, w, d = arr_img.shape
        if isBGR:
            img = cv2.cvtColor(arr_img, cv2.COLOR_BGR2RGB)
        else:
            img = arr_img.copy()
        image = QImage(img.data, w, h, w * d, QImage.Format_RGB888)
        return image
    except Exception as e:
        print(e)
        return def_ret


def qimage2qpixmap(image, def_ret=None):
    """
    QImage - QPixmap
    :param image:
    :param def_ret:
    :return:
    """
    # QPixmap.fromImage() 必须有qt界面显示，才不会报错
    try:
        if image.isNull():
            return def_ret
        return QPixmap.fromImage(image)
    except Exception as e:
        return def_ret

def qpixmap2qimage(pix: QPixmap, def_ret=None):
    return pix.toImage()


def qimage2array(qimg: QImage):
    temp_shape = (qimg.height(), qimg.bytesPerLine() * 8 // qimg.depth())
    temp_shape += (4,)
    # print(temp_shape)
    ptr = qimg.bits()
    ptr.setsize(qimg.byteCount())
    result = np.array(ptr, dtype=np.uint8).reshape(temp_shape)
    result = result[..., :3]
    return result


def file2qpixmap(path, def_ret=None):
    """
    图像转为QPixmap
    :param path:
    :return:
    """
    if not osp.exists(path):
        print('In Func [{}], 路径不存在: {}'.format(sys._getframe().f_code.co_name, path))
        return None
    try:
        cvimg = cv2_load(path)
        qimg = array2qimage(cvimg)
        qpix = qimage2qpixmap(qimg)
        return qpix
    except Exception as e:
        print('In Func [{}], err: {}'.format(sys._getframe().f_code.co_name, e))
        return def_ret


def array2qpixmap(arr_img, isBGR=True, def_ret=None):
    """
    np数据转qpixmap
    :param arr_img:
    :param def_ret:
    :return:
    """
    try:
        if arr_img is None:
            return def_ret
        qimg = array2qimage(arr_img, isBGR)
        qpix = qimage2qpixmap(qimg)
        return qpix
    except Exception as e:
        print(e)
        return def_ret