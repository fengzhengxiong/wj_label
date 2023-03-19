# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 标签标注信息，json文件对应数据结构

from data.cube_label import CubeLabel


class AnnoInfo3d(object):
    """
    标注信息内容
    """
    KEYS = [
        "version",
        "updateTime",
        "annoDelay",
        "datasetName",
        "pcdPath",
        "flags",
        "cubes",
    ]

    def __init__(self):
        self.version = None
        self.updateTime = ""
        self.annoDelay = 0
        self.datasetName = None
        self.pcdPath = None
        self.flags = {}
        self.cubes = []

        self.otherData = {}  # 读取文件有未知数据时暂存这里。

    def getDataFromDict(self, dicData):
        if not isinstance(dicData, dict):
            print("AnnoInfo3d 输入不是字典")
            return
        self.version = dicData.get("version", None)
        self.updateTime = dicData.get("updateTime", "")
        self.annoDelay = dicData.get("annoDelay", 0)
        self.datasetName = dicData.get("datasetName", None)
        self.pcdPath = dicData.get("pcdPath", None)
        self.flags = dicData.get("flags", {})

        self.cubes = []
        cubes_data = dicData.get("cubes", [])
        if cubes_data:
            for data in cubes_data:
                cube = CubeLabel()
                cube.getDataFromDict(data)
                cube.buildActors()
                self.cubes.append(cube)

        self.otherData = {
            k: v for k, v in dicData.items() if k not in self.KEYS
        }

    def convertToDict(self):
        cubes = []
        if self.cubes:
            for c in self.cubes:
                if isinstance(c, CubeLabel):
                    cubes.append(c.convertToDict())
                else:
                    print("AnnoMsg  convertToDict error")
                    continue

        data = dict(
            version=self.version,
            updateTime=self.updateTime,
            annoDelay=self.annoDelay,
            datasetName=self.datasetName,
            pcdPath=self.pcdPath,
            flags=self.flags,
            cubes=cubes,
        )
        # print("self.otherData = ", self.otherData)
        for key, value in self.otherData.items():
            assert key not in data
            data[key] = value

        return data


    def convertToCsvData(self):
        """
        转化为csv数据格式
        :return:
        """
        res = [cube.convertToCsv() for cube in self.cubes]
        print('convertToCsvData = ', res)
        return res

    def getDataFromCsv(self, datas):
        cubes = []
        try:
            for data in datas:
                cube = CubeLabel()
                ret = cube.getDataFromCsv(data)
                if ret:
                    cubes.append(cube)

            self.cubes = cubes
        except Exception as e:
            print(e)

    def reset(self):
        self.version = None
        self.updateTime = ''
        self.annoDelay = 0
        self.datasetName = None
        self.pcdPath = None
        self.flags = {}
        self.cubes = []
        self.otherData = {}

