#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交通目标配置文件信息
"""
import copy

from utils.file_manage import *


traffic_property_dic = {
    0: {'name': 'person', 'ch': '行人', 'color': (255, 0, 0), 'scale': (0.7, 0.7, 2), 'descript': 'person'},
    1: {'name': 'bicycle', 'ch': '两轮车', 'color': (200, 180, 0), 'scale': (1.7, 0.7, 1.5), 'descript': 'bicycle'},
    6: {'name': 'electric_bicycle', 'ch': '电动车', 'color': (255, 120, 0), 'scale': (2.9, 1.2, 1.8), 'descript': None},
    5: {'name': 'tricycle', 'ch': '三轮车', 'color': (120, 120, 0), 'scale': (2.9, 1.2, 1.5), 'descript': None},
}

default_traffic_property_dic = copy.deepcopy(traffic_property_dic)


# 遮挡
tar_cover_dic = {
    0:  {"name": "未遮挡"},
    1:  {"name": "遮挡"},
}

# 遮挡等级
tar_coverlevel_dict = {
    0: {"name": "0~30分"},
    1: {"name": "31~60分"},
    2: {"name": "61~90分"},
    3: {"name": "90分以上"},
}

# 置信度
tar_conf_dict = {
    0: {"name": "默认"},
    1: {"name": "十分可疑"},
    2: {"name": "比较可疑"},
    3: {"name": "一般可信"},
    4: {"name": "十分可信"},
}

# 信息来源
tar_source_dict = {
    0: {"name": "激光"},
    1: {"name": "视频"},
    2: {"name": "激光视频融合"},
}


# 标签属性编辑
KEYS = [
        'label',
        'id_num',
        'cen_x',
        'cen_y',
        'cen_z',
        'speed',
        'angle',
        'length',
        'width',
        'height',
        'is_cover',
        'cover_level',
        'conf',
        'source',
        'attr_value',
        'order_no'
    ]

import numpy as np
label_csv_dic = {
    # key 名称    val: 中文名称      列数      描述   值(供参考选择)
    "label":        {"ch": "类别", "No": 0, "describe": "", "val": traffic_property_dic},
    "id_num":       {"ch": "ID", "No": 1, "describe": "", "val": int()},
    "cen_x":        {"ch": "中心点X", "No": 2, "describe": "", "val": float()},
    "cen_y":        {"ch": "中心点Y", "No": 3, "describe": "", "val": float()},
    "cen_z":        {"ch": "中心点Z", "No": 4, "describe": "", "val": float()},
    "speed":        {"ch": "速度", "No": 5, "describe": "", "val": float()},
    "angle":        {"ch": "航向角", "No": 6, "describe": "", "val": float()},
    "length":       {"ch": "长", "No": 7, "describe": "", "val": float()},
    "width":        {"ch": "宽", "No": 8, "describe": "", "val": float()},
    "height":       {"ch": "高", "No": 9, "describe": "", "val": float()},
    "is_cover":     {"ch": "是否遮挡", "No": 10, "describe": "", "val": tar_cover_dic},
    "cover_level":  {"ch": "遮挡程度", "No": 11, "describe": "", "val": tar_coverlevel_dict},
    "conf":         {"ch": "置信度", "No": 12, "describe": "", "val": tar_conf_dict},
    "source":       {"ch": "信息来源", "No": 13, "describe": "", "val": tar_source_dict},
    "attr_value":   {"ch": "异常属性", "No": 14, "describe": "", "val": int()},
}

#
# fn = r'C:\Users\wanji\Desktop\标注测试\car_type.yaml'
# save_yaml_file(fn, traffic_property_dic, order=True)
# hh = read_yaml_file(fn)
# print(hh)
# save_json_file(r'C:\Users\wanji\Desktop\标注测试\car_type.json', hh)
