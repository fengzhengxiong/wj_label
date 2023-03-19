# -*- coding: utf-8 -*-
# !/usr/bin/env python

import numpy as np
import os
import os.path as osp

# 保留小数位 用round  format(36.924, '6.3f')  ，整数用 format(3, '06d')

def float_to_str(num, w=6):
    if w < 1:
        return str(num)
    format_f = lambda x: str(x + .0).ljust(w, '0')[:w]
    # format(num, '.5f')
    return format_f(num)


def check_float_to_int(n):
    ''' 如果n=1.00 ，返回 1 ，否则为浮点数  '''
    return int(n) if n.is_integer() else n


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_int_number(s):
    """ 判断字符串是否为整数，排除小数点 """
    try:
        return (float(s).is_integer() and s.count('.') == 0)
    except ValueError:
        return False


def calulate_rect(cen_pos, w, h, def_ret=None):
    """
    中心点，宽高 计算矩形四点坐标, 图像坐标轴下
    :param cen_pos:
    :param w:
    :param h:
    :return:
    """
    #  0  1
    #  3  2
    try:
        result = [
            [cen_pos[0] - 0.5 * w, cen_pos[1] - 0.5 * h],
            [cen_pos[0] + 0.5 * w, cen_pos[1] - 0.5 * h],
            [cen_pos[0] + 0.5 * w, cen_pos[1] + 0.5 * h],
            [cen_pos[0] - 0.5 * w, cen_pos[1] + 0.5 * h]
        ]
        return result
    except Exception as e:
        print(e)
        return def_ret


def turnVector(vec, delta_t, def_ret=None):
    """二维向量旋转delta_t"""
    try:
        vz = None
        if len(vec) == 3:
            vx, vy, vz = vec
        else:
            vx, vy = vec
        rho = np.sqrt(vx * vx + vy * vy)
        theta1 = np.arctan2(vy, vx)
        theta2 = theta1 + np.deg2rad(delta_t)
        x = rho * np.cos(theta2)
        y = rho * np.sin(theta2)
        result = [x, y, vz] if vz else [x, y]
        return result
    except Exception as e:
        print(e)
        return def_ret



def get_points_inside(cloud, pos=(0, 0, 0), scale=(0, 0, 0), rot=(0, 0, 0), def_ret=None):
    """
    获取框里的点云数据
    :param cloud: 点云 np数组或者pcd路径，均可
    :param pos:
    :param scale:
    :param rot:
    :return:
    """

    from pclpy import pcl
    import os.path as osp
    cloud_xyz = pcl.PointCloud.PointXYZ()
    filtered = pcl.PointCloud.PointXYZ()

    if isinstance(cloud, str):
        if cloud.endswith('.pcd') and osp.exists(cloud):
            pcl.io.loadPCDFile(cloud, cloud_xyz)
        else:
            print('error', cloud)
            return def_ret
    elif isinstance(cloud, np.ndarray):
        cloud_xyz = pcl.PointCloud.PointXYZ().from_array(cloud)
    else:
        return def_ret

    # print('原始 ', cloud_xyz.size())
    l, w, h = scale
    x, y, z = pos
    rx, ry, rz = rot

    box_filter = pcl.filters.CropBox.PointXYZ()
    box_filter.setMax(np.array([0.5 * l, 0.5 * w, 0.5 * h, 1]))
    box_filter.setMin(np.array([-0.5 * l, -0.5 * w, -0.5 * h, 1]))
    box_filter.setTranslation(np.array([x, y, z]))
    box_filter.setRotation(np.array([np.deg2rad(rx), np.deg2rad(ry), np.deg2rad(rz)]))
    box_filter.setNegative(False)
    box_filter.setInputCloud(cloud_xyz)
    box_filter.filter(filtered)

    # import pcl
    # box = pcl.CropBox()
    # pc = pcl.PointCloud()
    # pc.make_cropbox()
    # box.set_InputCloud()
    # box.filter()

    return np.array(filtered.xyz)

from scipy import linalg

def cal_obb_2d(coord_xy, def_ret=None):
    """
    计算二维点，obb盒子
    :param coord_xy:
    :return: 中心点，长宽，方向
    """
    try:
        # 求协方差矩阵
        covMatrix = np.cov(coord_xy)
        # print('covMatrix= ', covMatrix)
        # 求协方差矩阵的特征向量
        la, eigVector = linalg.eig(covMatrix)
        # print('eigVector = ',eigVector)
        # print('角度= ', np.rad2deg(np.arccos(eigVector[0, 0])))
        ori = np.rad2deg(np.arccos(eigVector[0, 0]))

        # 将数据点从 xy 空间转到 uv 空间
        coord_uv = np.matmul(eigVector.transpose(1, 0), coord_xy)
        # 求 uv 空间的 AABB，依次保存：左下角、左上角、右下角、右上角
        uMin = min(coord_uv[0])
        uMax = max(coord_uv[0])
        vMin = min(coord_uv[1])
        vMax = max(coord_uv[1])
        AABB_uv = np.array([[uMin, uMin, uMax, uMax], [vMin, vMax, vMin, vMax]])
        # uv 空间的 AABB 转回 xy 空间，即得到 OBB
        OBB_xy = np.matmul(eigVector, AABB_uv)

        scale = [uMax-uMin, vMax - vMin]
        # print(scale)
        # print('\nOBB_xy = ', OBB_xy)
        # print(np.average(OBB_xy, axis=1))
        # print(np.average(OBB_xy, axis=1).tolist())
        center = np.average(OBB_xy, axis=1).tolist()

        return (center, scale, ori)

    except Exception as e:
        print(e)
        return def_ret



def get_bound_3dbox(points, direc=None):
    """
    :param points: 点云集合
    :return: 返回3D框， 位置、尺寸、角度
    """
    area = np.array(points)
    coordxy = area[:, 0:2]
    coordxy = coordxy.transpose()
    # print('coordxy == ', coordxy.shape)
    # print('direc = ', direc)

    # OBB包围盒贴合
    result = cal_obb_2d(coordxy)
    if result is not None:
        center, scale, ori = result
        cenX = center[0]
        cenY = center[1]
        length = scale[0]
        width = scale[1]
        # print('++++++', length, width, ori)
        ang = direc if direc else ori
        if length < width:
            length, width = width, length
            ang = direc if direc else (ori - 90)
        # print('++++++22', length, width, ori)
    else:
        # AABB包围盒
        cenX = (max(area[:, 0]) + min(area[:, 0])) / 2
        cenY = (max(area[:, 1]) + min(area[:, 1])) / 2
        length = (max(area[:, 0]) - min(area[:, 0]))
        width = (max(area[:, 1]) - min(area[:, 1]))
        ang = direc if direc else 0
        if length < width:
            length, width = width, length
            ang = direc if direc else 90

    cenZ = (max(area[:, 2]) + min(area[:, 2])) / 2
    height = (max(area[:, 2]) - min(area[:, 2]))

    length = max(length, 0.3)
    width = max(width, 0.3)
    height = max(height, 0.3)

    ret = [cenX, cenY, cenZ, ang, length, width, height]
    return ret


if __name__ == "__main__":
    # 是生成文件路径，全称
    # data是映射字典
    # test_main_json()
    # test_main_yaml()
    path = r"C:\Users\wanji\Desktop\test"


    print(float_to_str(3.5600, 6))

    a = 1.000
    print(a.is_integer())

    b = '556.3695'
    # print(b.isdigit())
    # print(int(float(b)))

    # print(format(float(b), "6.9f"))
    # print(format(3, '06d'))
    print(is_int_number('-589.0000'))

    print("dfdfdffd".count('.'))
# import pcl
#
# pcl.PointCloud

