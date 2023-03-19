# !/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2, csv
import numpy as np
import math
import os
from scipy.spatial.transform import Rotation as R
import json
import codecs

class Map(object):
    def __init__(self,in_param,rotate_mat,translation_vec,dist_vec):
        self.in_param = np.mat(in_param).reshape(-1,3)
        self.rotate_mat = np.mat(rotate_mat)
        self.translation_vec = np.asarray(translation_vec)
        self.dist_vec = np.mat(dist_vec)
        self.get_tf_lidar_to_cam()
        quateranion = R.from_matrix(self.rotate_mat)
        euler = R.as_euler(quateranion,"XYZ")

    def get_tf_lidar_to_cam(self):
        tf_lidar_to_cam = np.zeros((4, 4))
        tf_lidar_to_cam[:3, :3] = self.rotate_mat
        tf_lidar_to_cam[:3, 3] = self.translation_vec
        tf_lidar_to_cam[3, 3] = 1
        self.tf_lidar_to_cam = tf_lidar_to_cam#4×4

    def lidar_to_cam(self, xyz_lidar):
        xyz_lidar = xyz_lidar
        xyz_lidar = np.hstack([xyz_lidar, np.ones(xyz_lidar.shape[0]).reshape(-1, 1)])
        return self.tf_lidar_to_cam.dot(xyz_lidar.T)[:3].T

class Map_left(object):
    def __init__(self,in_param_left,rotate_mat_left,translation_vec_left,dist_vec_left):
        self.in_param = np.mat(in_param_left).reshape(-1,3)
        self.rotate_mat = np.mat(rotate_mat_left)
        self.translation_vec = np.mat(translation_vec_left)
        self.dist_vec = np.mat(dist_vec_left)
        self.get_tf_lidar_to_cam()
        quateranion = R.from_matrix(self.rotate_mat)
        euler = R.as_euler(quateranion,"XYZ")

    def get_tf_lidar_to_cam(self):
        tf_lidar_to_cam = np.zeros((4, 4))
        tf_lidar_to_cam[:3, :3] = self.rotate_mat
        tf_lidar_to_cam[:3, 3] = self.translation_vec
        tf_lidar_to_cam[3, 3] = 1
        self.tf_lidar_to_cam = tf_lidar_to_cam

    def lidar_to_cam(self, xyz_lidar):
        xyz_lidar = xyz_lidar
        xyz_lidar = np.hstack([xyz_lidar, np.ones(xyz_lidar.shape[0]).reshape(-1, 1)])
        return self.tf_lidar_to_cam.dot(xyz_lidar.T)[:3].T

class Map_mid(object):
    def __init__(self,in_param_mid,rotate_mat_mid,translation_vec_mid,dist_vec_mid):
        self.in_param = np.mat(in_param_mid).reshape(-1,3)
        self.rotate_mat = np.mat(rotate_mat_mid)
        self.translation_vec = np.asarray(translation_vec_mid)
        self.dist_vec = np.mat(dist_vec_mid)
        self.get_tf_lidar_to_cam()
        quateranion = R.from_matrix(self.rotate_mat)
        euler = R.as_euler(quateranion,"XYZ")

    def get_tf_lidar_to_cam(self):
        tf_lidar_to_cam = np.zeros((4, 4))
        tf_lidar_to_cam[:3, :3] = self.rotate_mat
        tf_lidar_to_cam[:3, 3] = self.translation_vec
        tf_lidar_to_cam[3, 3] = 1
        self.tf_lidar_to_cam = tf_lidar_to_cam#4×4

    def lidar_to_cam(self, xyz_lidar):
        xyz_lidar = xyz_lidar
        xyz_lidar = np.hstack([xyz_lidar, np.ones(xyz_lidar.shape[0]).reshape(-1, 1)])
        return self.tf_lidar_to_cam.dot(xyz_lidar.T)[:3].T

class Map_right(object):
    def __init__(self,in_param_right,rotate_mat_right,translation_vec_right,dist_vec_right):
        self.in_param = np.mat(in_param_right).reshape(-1,3)
        self.rotate_mat = np.mat(rotate_mat_right)
        self.translation_vec = np.mat(translation_vec_right)
        self.dist_vec = np.mat(dist_vec_right)
        self.get_tf_lidar_to_cam()
        quateranion = R.from_matrix(self.rotate_mat)
        euler = R.as_euler(quateranion,"XYZ")

    def get_tf_lidar_to_cam(self):
        tf_lidar_to_cam = np.zeros((4, 4))
        tf_lidar_to_cam[:3, :3] = self.rotate_mat
        tf_lidar_to_cam[:3, 3] = self.translation_vec
        tf_lidar_to_cam[3, 3] = 1
        self.tf_lidar_to_cam = tf_lidar_to_cam#4×4

    def lidar_to_cam(self, xyz_lidar):
        xyz_lidar = xyz_lidar
        xyz_lidar = np.hstack([xyz_lidar, np.ones(xyz_lidar.shape[0]).reshape(-1, 1)])
        return self.tf_lidar_to_cam.dot(xyz_lidar.T)[:3].T


def img_file_name(file_dir):
    img_time = []
    for root, dirs, files in os.walk(file_dir):
        for i in range(len(files)):
            file_name = os.path.splitext(files[i])[0]
            img_time.append(file_name)
    return img_time

def corners_nd(dims, origin=0.5):
    ndim = int(dims.shape[1])
    corners_norm = np.stack(
        np.unravel_index(np.arange(2 ** ndim), [2] * ndim),
        axis=1).astype(dims.dtype)

    if ndim == 2:
        corners_norm = corners_norm[[0, 1, 3, 2]]
    elif ndim == 3:
        corners_norm = corners_norm[[0, 1, 3, 2, 4, 5, 7, 6]]
    corners_norm = corners_norm - np.array(origin, dtype=dims.dtype)
    corners = dims.reshape([-1, 1, ndim]) * corners_norm.reshape([1, 2 ** ndim, ndim])
    return corners


def rotation_3d_in_axis(points, angles, axis=0):
    rot_sin = np.sin(angles)
    rot_cos = np.cos(angles)
    ones = np.ones_like(rot_cos)
    zeros = np.zeros_like(rot_cos)
    if axis == 1:
        rot_mat_T = np.stack([[rot_cos, zeros, -rot_sin], [zeros, ones, zeros], [rot_sin, zeros, rot_cos]])
    elif axis == 2 or axis == -1:
        rot_mat_T = np.stack([[rot_cos, -rot_sin, zeros], [rot_sin, rot_cos, zeros], [zeros, zeros, ones]])
    elif axis == 0:
        rot_mat_T = np.stack([[zeros, rot_cos, -rot_sin], [zeros, rot_sin, rot_cos], [ones, zeros, zeros]])
    else:
        raise ValueError("axis should in range")
    return np.einsum('aij,jka->aik', points, rot_mat_T)


def center_to_corner_box3d_(bbox,origin=(0.5, 0.5, 0.5), axis=2):
    centers = bbox[:, :3]#中心点 x,y,z [ -3.94672347, -62.38768339,  -3.1443063 ]
    dims = bbox[:, 3:6]#宽、长、高 [0.74305974, 1.5765898 , 1.57541666]

    angles = 3/2 * np.pi - bbox[:, 6]#角度 3/2×pi [4.68024822]
    corners = corners_nd(dims, origin=origin)

    if angles is not None:
        corners = rotation_3d_in_axis(corners, angles, axis=axis)

    corners += centers.reshape([-1, 1, 3])
    return corners

def mat_to_vec(transfromation_matrix):
    temp=np.array(transfromation_matrix)
    rot_mat = temp[:3, :3]
    if(np.any(rot_mat)==0):
        return [0,0,0]
    else:
        rotate_vec_mat, _ = cv2.Rodrigues(rot_mat)
        rotate_vec = np.array([rotate_vec_mat[0, 0], rotate_vec_mat[1, 0], rotate_vec_mat[2, 0]])
        return list(rotate_vec)

def Load_Image_Map_Config(Map_Config_path):
    # print(Map_Config_path)
    with codecs.open(Map_Config_path, 'r', encoding='utf-8') as f:
        text = f.read()
        ret = json.loads(text) if text else {}
        f.close()
        del text

    if 'in_param_left' in ret:
        in_param_left = ret['in_param_left']
        transfromation_matrix_left=ret['transfromation_matrix_left']
        translation_vec_left = ret['translation_vec_left']
        dist_vec_left = ret['dist_vec_left']
        # print([in_param_left,transfromation_matrix_left,translation_vec_left,dist_vec_left])
    else:
        in_param_left=[[0,0,0],[0,0,0],[0,0,0]]
        transfromation_matrix_left = [[0,0,0],[0,0,0],[0,0,0]]
        translation_vec_left = [0,0,0]
        dist_vec_left = [0,0,0,0,0]

    if 'in_param_mid' in ret:
        in_param_mid = ret['in_param_mid']
        transfromation_matrix_mid = ret['transfromation_matrix_mid']
        translation_vec_mid = ret['translation_vec_mid']
        dist_vec_mid = ret['dist_vec_mid']
        # print([in_param_mid, transfromation_matrix_mid, translation_vec_mid, dist_vec_mid])
    else:
        in_param_mid=[[0,0,0],[0,0,0],[0,0,0]]
        transfromation_matrix_mid = [[0,0,0],[0,0,0],[0,0,0]]
        translation_vec_mid = [0,0,0]
        dist_vec_mid = [0,0,0,0,0]

    if 'in_param_right' in ret:
        in_param_right = ret['in_param_right']
        transfromation_matrix_right = ret['transfromation_matrix_right']
        translation_vec_right = ret['translation_vec_right']
        dist_vec_right = ret['dist_vec_right']
        # print([in_param_right, rotate_vec_right, translation_vec_right, dist_vec_right])
    else:
        in_param_right=[[0,0,0],[0,0,0],[0,0,0]]
        transfromation_matrix_right = [[0,0,0],[0,0,0],[0,0,0]]
        translation_vec_right = [0,0,0]
        dist_vec_right = [0,0,0,0,0]

    return [in_param_left,transfromation_matrix_left,translation_vec_left,dist_vec_left,
            in_param_mid,transfromation_matrix_mid,translation_vec_mid,dist_vec_mid,
            in_param_right,transfromation_matrix_right,translation_vec_right,dist_vec_right]



