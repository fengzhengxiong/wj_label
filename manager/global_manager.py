#!/usr/bin/env python
# -*- encoding: utf-8 -*-


"""
软件的一些全局变量，统一管理
"""

from config.label_type import *
import copy

class GlobalManger():
    def __init__(self):
        self.add_traffic_type = None  # 预先新增box 的类别

        self.traffic_property_dic = copy.deepcopy(traffic_property_dic)
        self.label_csv_dic = copy.deepcopy(label_csv_dic)



class Singleton(GlobalManger):
    def foo(self):
        pass

global_manager = Singleton()