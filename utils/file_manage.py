# Copyright (c) <2022-5> An-Haiyang
# 文件读写管理
# -*- coding: utf-8 -*-
# !/usr/bin/env python

import sys
import os
import os.path as osp
import json
import yaml
import codecs
import re
import csv
import ast
import numpy as np
from collections import OrderedDict

# print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)

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


def save_json_file(filename, dic, indent=2, def_ret=False):
    """
    写json文件
    :return: 成功 True， 失败 def_ret
    """
    try:
        with codecs.open(filename, 'w', encoding='utf-8') as f:
            # json.dump(data, f, ensure_ascii=False, indent=2)
            text = json.dumps(dic, ensure_ascii=False, indent=indent)
            f.write(text)
            f.close()
            del text
            return True
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def read_json_file(filename, def_ret=None):
    """
    读json文件
    :return: 成功 字典， 失败 def_ret
    """
    def check_file(filename):
        extensions = ['json']
        return True if (filename and osp.isfile(filename) and filename.lower().endswith(tuple(extensions))) else False

    try:
        if not check_file(filename):
            return def_ret
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
            ret = json.loads(text) if text else {}
            f.close()
            del text
            return ret
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def read_yaml_file(filename, def_ret=None):
    """
    读yaml文件
    :return: 成功 True， 失败 def_ret
    """
    def check_file(filename):
        extensions = ['.yaml', ',yml']
        return True \
            if (filename and osp.isfile(filename) and filename.lower().endswith(tuple(extensions))) \
            else False
    try:
        if not check_file(filename):
            return def_ret
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            text = f.read()
            ret = yaml.safe_load(text) if text else {}
            f.close()
            del text
            return ret
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def save_yaml_file(filename, data, order=False, def_ret=None):
    """
     写yml文件
    :param filename:
    :param data:
    :param order:  是否按序写入
    :param def_ret:
    :return:  成功 True， 失败 def_ret
    """

    from collections import OrderedDict

    def _dict_to_orderdict(data):
        ret = data
        if isinstance(data, dict):
            ret = OrderedDict()
            for k, v in data.items():
                if isinstance(v, dict):
                    v = _dict_to_orderdict(v)
                ret[k] = v
        return ret
    try:
        if not order:
            with codecs.open(filename, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, canonical=False)
                return True
        else:
            save_ordered_dict_to_yaml(_dict_to_orderdict(data), filename)

    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def save_ordered_dict_to_yaml(data, save_path, stream=None, Dumper=yaml.SafeDumper, object_pairs_hook=OrderedDict, **kwds):
    """
    将有序字典， 按序写入yaml文件中
    :param data: OrderedDict 类型
    :param save_path:
    :param stream:
    :param Dumper:
    :param object_pairs_hook:
    :param kwds:
    :return:
    """

    class OrderedDumper(Dumper):
        pass
    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())
    OrderedDumper.add_representer(object_pairs_hook, _dict_representer)
    with codecs.open(save_path, 'w', encoding='utf-8') as file:
        file.write(yaml.dump(data, stream, OrderedDumper, allow_unicode=True, **kwds))
    return yaml.dump(data, stream, OrderedDumper, **kwds)


def natural_sort(list, key=lambda s:s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
        convert = lambda text: int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    list.sort(key=sort_key)


def scan_files(dirpath, ext=None, def_ret=None):
    """
    扫描当前文件夹文件
    """
    dirpath = dirpath if osp.isdir(dirpath) else osp.dirname(dirpath)
    if not osp.exists(dirpath):
        return def_ret
    result = []
    try:
        if ext is None:
            for file in os.listdir(dirpath):
                result.append(osp.join(dirpath, file))
        else:
            extensions = [ext] if type(ext) == str else ext
            for file in os.listdir(dirpath):
                result += [osp.join(dirpath, file)] if file.lower().endswith(tuple(extensions)) else []

        natural_sort(result, key=lambda x: x.lower())
        return result
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def scan_all_files(dirpath, ext=None, def_ret=None):
    """
    扫描当前文件夹下所有文件，包含子文件夹
    """
    dirpath = dirpath if osp.isdir(dirpath) else osp.dirname(dirpath)
    if not osp.exists(dirpath):
        return def_ret
    result = []
    try:
        if ext is None:
            for root, dirs, files in os.walk(dirpath):
                # root 表示当前正在访问的文件夹路径
                # dirs 表示该文件夹下的子目录名list
                # files 表示该文件夹下的文件list
                for f in files:
                    result.append(osp.join(root, f))
        else:
            extensions = [ext] if type(ext) == str else ext
            for root, dirs, files in os.walk(dirpath):
                for f in files:
                    if f.lower().endswith(tuple(extensions)):
                        result.append(osp.join(root, f))
        # natural_sort(result, key=lambda x: x.lower())
        return result
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def scan_images(dirpath):
    """ 扫描QT支持的图像格式文件 """
    from PyQt5 import QtGui
    extensions = [
        ".%s" % fmt.data().decode().lower()
        for fmt in QtGui.QImageReader.supportedImageFormats()
    ]
    return scan_files(dirpath=dirpath, ext=extensions)


def read_file(path, def_ret=None):
    if not (osp.exists(path) and osp.isfile(path)):
        return def_ret

    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
            return text
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def write_file(path, text, def_ret=None):
    if not osp.exists(osp.dirname(path)):
        os.makedirs(osp.dirname(path))
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
            f.close()
            return True
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def read_yolo_txt(file, def_ret=None):
    """
    txt:
    0 8 0.094596 0.087841 0.135026 0.119921 0 0
    0 10 0.558333 0.408764 0.591666 0.736083 0 粤JR0800
    :return:
    [0, 8, 0.094596, 0.087841, 0.135026, 0.119921, 0, 0]
    [0, 10, 0.558333, 0.408764, 0.591666, 0.736083, 0, '粤JR0800']
    """
    if not osp.exists(file):
        return def_ret
    result = []
    try:
        with codecs.open(file, 'r', encoding='utf-8') as f:
            line = f.readline()
            while line:
                # print("line= ",line)
                row_data = [data for data in line.strip('\n\r').split(' ')]
                for i in range(len(row_data)):
                    a = row_data[i]
                    if is_int_number(a):
                        row_data[i] = int(a)
                    elif is_number(a):
                        row_data[i] = float(a)
                    else:
                        pass

                result.append(row_data)
                line = f.readline()
            return result
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def read_csv_file(filename, def_ret=None):
    def check_file(filename):
        extensions = ['.csv']
        return True \
            if (filename and osp.isfile(filename) and filename.lower().endswith(tuple(extensions))) \
            else False

    result = []
    try:
        if not check_file(filename):
            return def_ret
        with open(filename, 'r', encoding='utf-8') as f:
            datas = csv.reader(f)
            for data in datas:
                # tmp = [ast.literal_eval(a) for a in data]  # 对于中文会报错
                tmp = data[:]
                for i in range(len(tmp)):
                    a = tmp[i]
                    if is_int_number(a):
                        tmp[i] = int(a)
                    elif is_number(a):
                        tmp[i] = float(a)
                    else:
                        pass
                # print(tmp)
                result.append(tmp)
            f.close()
            del datas
            return result
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def save_csv_file(filename, data, def_ret=None):
    """
    写csv文件, data是list 二维格式
    :return: 成功 True， 失败 def_ret
    """
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            for d in data:
                w.writerow(d)
            f.close()
            return True
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret

    # 用下面方法也是可以的
    # res = []
    # for d in data:
    #     for a in d:
    #         d[d.index(a)] = str(a)
    #     res.append(','.join(d))
    # text = '\n'.join(res)
    # write_file(filename, text)


def read_pcd_file_to_np(filename, def_ret=None):
    """ 读pcd 到数组 """
    def check_file(filename):
        extensions = ['.pcd']
        return True \
            if (filename and osp.isfile(filename) and filename.lower().endswith(tuple(extensions))) \
            else False
    cnt = 0
    try:
        if not check_file(filename):
            return def_ret
        with open(filename) as f:
            while True:
                cnt += 1
                if cnt > 50:
                    print('pcd文件一直未能找到DATA标识')
                    f.close()
                    return def_ret
                ln = f.readline().strip()
                if ln.startswith('DATA'):
                    break
            points = np.loadtxt(f)
            points = points[:, 0:4]
            f.close()
            return points
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def read_bin_file_to_np(filename, def_ret=None):
    """ 读pcd 到数组 """
    def check_file(filename):
        extensions = ['.bin']
        return True \
            if (filename and osp.isfile(filename) and filename.lower().endswith(tuple(extensions))) \
            else False
    cnt = 0
    try:
        if not check_file(filename):
            return def_ret
        pointcloud = np.fromfile(filename, dtype=np.float32, count=-1).reshape([-1, 4])
        x = pointcloud[:, 0]  # x position of point
        y = pointcloud[:, 1]  # y position of point
        z = pointcloud[:, 2]  # z position of point

        r = pointcloud[:, 3]  # reflectance value of point
        d = np.sqrt(x ** 2 + y ** 2)  # Map Distance from sensor
        points = pointcloud[:, 0:4]
        return points
    except Exception as e:
        err_msg = 'In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e)
        print(err_msg)
        return def_ret


def load_points_cloud(path, def_ret=None):
    """
    加载点云文件
    :param path:
    :return:
    """
    # print('load_points_to_ndarray', path)
    if os.path.exists(path) and os.path.isfile(path):
        pass
    else:
        print("文件不存在！！")
        return def_ret

    result = def_ret
    try:
        if path.lower().endswith('.pcd'):
            result = read_pcd_file_to_np(path)
        elif path.lower().endswith('.bin'):
            result = read_bin_file_to_np(path)
        else:
            print(f'error in fun[{sys._getframe().f_code.co_name},格式非点云:{path}]')
        return result
    except Exception as e:
        print(e)
        return def_ret


def save_pcd_file(points, p_path):

    if not osp.exists(osp.dirname(p_path)):
        os.makedirs(osp.dirname(p_path))

    # print('点的个数', point_num)
    try:
        point_num = points.shape[0]
        dim = points.shape[1]

        headstring4 = \
"""# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z intensity
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH {}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {}
DATA ascii""".format(point_num, point_num)
        headstring3 = \
"""# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z
SIZE 4 4 4
TYPE F F F
COUNT 1 1 1
WIDTH {}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {}
DATA ascii""".format(point_num, point_num)

        with open(p_path, 'w') as f:
            if dim == 3:
                f.write(headstring3)
            elif dim == 4:
                f.write(headstring4)

            # 依次写入点
            for i in range(point_num):
                polist = []
                for j in range(dim):
                    polist.append(str(points[i][j]))
                string = '\n' + ' '.join(polist)
                f.write(string)
            f.close()
    except Exception as e:
        print(e)


def save_pcd_file_with_pcl(pc_data, filename):
    from pclpy import pcl
    obj_new = pcl.PointCloud.PointXYZ()
    obj_new = obj_new.from_array(pc_data)
    pcl.io.savePCDFile(filename, obj_new)










def test_main_json():
    path = r"C:\Users\wanji\Desktop\test\cd.json"
    data = dict(
        car=1,
        # bus=[2,78,'yd'],
        truck='粤G5696',
        bike='来 ，,我GKH89',
        per={"df": '答复的', 89: ['kkg']},
    )
    data['59'] = (3.69, ['是的的', 6.985, ['手动阀', 'dfs交通']])

    ret = save_json_file(path, data, indent=2)
    print(ret)

    dd = read_json_file(path)
    print(dd)

def test_main_yaml():
    data = dict(
        car=1,
        # bus=[2,78,'yd'],
        truck='粤G5696',
        bike='来 ，,我GKH89',
        per={"df": '答复的', 89: ['kkg']},
    )
    data['59'] = (3.69, ['是的的', 6.985, ['手动阀', 'dfs交通']])

    path = r"C:\Users\wanji\Desktop\test\cdd.yaml"
    # data = list(range(0,30))
    save_yaml_file(path, data)
    dd = read_yaml_file(path)
    print(dd)


    # path = r"C:\Users\wanji\Desktop\test"
    # ss = scan_all_files(path, 'json')
    # for s in ss:
    #     print(s)

def test_yolo_txt():
    path = r'C:\Users\wanji\Desktop\1\test\output\yolo2\2021-05-17-154932_00145.txt'
    dd = read_yolo_txt(path)
    for s in dd:
        print(s)


def test_read_csv():
    path = r'C:\Users\wanji\Desktop\测试\test点云\cube\gate8.csv'
    dd = read_csv_file(path)
    # print(dd)
    for s in dd:
        print(s)

    path2 = r'C:\Users\wanji\Desktop\测试\test点云\cube\gate8666.csv'
    save_csv_file(path2, dd)


if __name__ == "__main__":
    # test_main_json()
    # test_main_yaml()

    test_read_csv()

    pass





