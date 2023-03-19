# !/usr/bin/env python
# -*- coding: utf-8 -*-
# 点云文件信息


class PcdFileInfo(object):
    """  点云文件信息类,标注相关  """

    # 文件状态 待编辑、已完成、待丢弃
    NORMAL = 0
    CHECK = 1
    ABANDON = 2

    KEYS = [
        "name",
        "state",
        "update_timestamp",
        "anno_delay",
    ]

    def __init__(self, filename=None, dicdata=None):
        self.name = filename
        self.state = self.NORMAL
        self.update_timestamp = None
        self.anno_delay = None

        self.other_data = {}

        if dicdata:
            self.getDataFromDict(dicdata)

    def getDataFromDict(self, dicData):
        if not isinstance(dicData, dict):
            print("dicData 输入不是字典")
            return

        _translate = {
            "NORMAL": 0,
            "CHECK": 1,
            "ABANDON": 2,
        }

        self.name = dicData.get("name", None)
        self.state = dicData.get("state", "NORMAL")
        self.update_timestamp = dicData.get("update_timestamp", None)
        self.anno_delay = dicData.get("anno_delay", None)

        self.state = _translate[self.state]

        self.other_data = {
            k: v for k, v in dicData.items() if k not in PcdFileInfo.KEYS
        }

    def convertToDict(self):
        data = {}
        _translate = {
            0: "NORMAL",
            1: "CHECK",
            2: "ABANDON",
        }
        try:
            data = dict(
                name=self.name,
                state=_translate[self.state],
                update_timestamp=self.update_timestamp,
                anno_delay=self.anno_delay,
            )

            if bool(self.other_data):
                for key, value in self.other_data.items():
                    assert key not in data
                    data[key] = value
        except Exception as e:
            print("convertToDict ", e)

        return data