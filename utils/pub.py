# -*- coding: utf-8 -*-
# !/usr/bin/env python


# from math import sqrt

import re
import os
import sys
import numpy as np
import os.path as osp

import collections

from PyQt5.QtCore import QT_VERSION_STR, QRegExp
# from PyQt5.QtGui import QColor, QIcon, QRegExpValidator


class struct(object):
    def __init__(self, **kwargs):
        """

        :rtype:
        """
        self.__dict__.update(kwargs)



def have_qstring():
    '''p3/qt5 get rid of QString wrapper as py3 has native unicode str type'''
    return not (sys.version_info.major >= 3 or QT_VERSION_STR.startswith('5.'))


# def util_qt_strlistclass():
#     return QStringList if have_qstring() else list


def natural_sort(list, key=lambda s:s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
        convert = lambda text: int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    list.sort(key=sort_key)



def search_path_reference(input_path, isfile=False):
    """
    路径的模糊匹配
    :param input_path:
    :param isfile: 是不是文件路径
    :return:
    """
    output_path = None
    if isfile is True:
        if osp.exists(input_path) and osp.isfile(input_path):
            output_path = input_path
            return output_path
    if input_path:
        if osp.exists(input_path) and osp.isdir(input_path):
            output_path = input_path
        else:
            if osp.exists(osp.dirname(input_path)):
                output_path = osp.dirname(input_path)
            else:
                if osp.exists(osp.abspath(osp.join(input_path, ".."))):
                    output_path = osp.abspath(osp.join(input_path, ".."))
    return output_path


def fuzzy_search_file(path, filename, suffix, def_ret=None):
    """
    模糊检索文件夹内的文件, 只获取一个结果就返回，用于点云匹配图像
    :param path: 文件夹路径
    :param filename: 检索的文件字符串，可以的残缺的名称
    :return: 返回完整路径，异常情况返回None
    :param suffix:  文件后缀筛选要求
    """
    # print('fuzzy_search_file', path, filename)
    if path is None or not osp.exists(path):
        return def_ret

    res = []
    for root, dirs, files in os.walk(path):
        for f in files:
            abs_path = osp.join(root, f)
            bare_name = osp.splitext(f)[0]
            if filename in bare_name:
                # print('路径:%s' % (abs_path))
                if abs_path.lower().endswith(tuple(suffix)):
                    res.append([f, abs_path])
                else:
                    pass
    # print('fuzzy_search_file', res)
    if not res:
        return None
    ''' 先准确搜索 '''
    for name, abs_path in res:
        if filename == osp.splitext(name)[0]:
            return abs_path

    ''' 准确搜索没有，则模糊判定 '''
    for name, abs_path in res:
        if filename in osp.splitext(name)[0]:
            return abs_path
        else:
            return def_ret


def dic_getset(dic, key, def_ret):
    if key not in dic:
        dic[key] = def_ret
    return dic.get(key)

def dic_list_push(dic, key, v):
    dic_getset(dic, key, []).append(v)

def dic_list_pop(dic, key):
    dic.get(key, [None]).pop()

def dic_list_get(dic, key, def_ret=None):
    return dic.get(key, [def_ret])[-1]

def lst_append_once(lst, v):
    exist = v in lst
    if not exist:
        lst.append(v)
    return exist

def lst_remove_once(lst, v):
    exist = v in lst
    if exist:
        lst.remove(v)
    return exist

def get_top(lst, def_ret=None):
    return lst[0] if len(lst) > 0 else def_ret


def dict_to_orderdict(data, def_ret=''):
    ret = data
    if isinstance(data, dict):
        ret = collections.OrderedDict()
        for k, v in data.items():
            if isinstance(v, dict):
                v = dict_to_orderdict(v)
            ret[k] = v
    return ret


def dic_pop(dic, key):
    if key in dic.keys():
        dic.pop(key)


def split_list_in_segs(data):
    if len(data) == 0:
        return [[]]

    # 数据必须是整数，按照升序排列，且不能有重复
    _data = np.sort(np.array(data, dtype=int), axis=-1)  # 排序
    _data = _data.tolist()

    result = []
    tmp = []
    for i in range(len(_data)):
        if i == 0:
            tmp.append(_data[i])
        else:
            if _data[i] == tmp[-1] + 1:
                tmp.append(_data[i])
            else:
                result.append(tmp)
                tmp = [_data[i]]
    result.append(tmp)
    return result
