# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    目标ID	 跟踪数据需要准确标注，同一目标ID需保持不变，范围1~100000	    0
    类型	     见目标类型sheet表	                                        1
    中心（重心）X轴坐标	        单位cm，≥0	                            2
    中心（重心）Y轴坐标	        单位cm，≥0	                            3
    中心（重心）Z轴坐标	        单位cm，≥0	                            4
    速度	cm/s            （标记0cm/s）	                                5
    运动方向	            Y轴正方向顺时针夹角，0~360度	                    6
    长度	沿物体运动方向为长，单位cm，≥0	                                7
    宽度	单位cm，≥0	                                                    8
    高度	单位cm，≥0	                                                    9
    是否被遮挡	0 — 未遮挡；1 — 遮挡	                                10
    遮挡程度	等级分为0/1/2/3，越大遮挡越严重	                            11
    置信度	此字段为本交通参与者的置信度，等级分为1/2/3/4，越大越可信	    12
    信息来源	0 — 激光；1 — 视频；2 — 视频激光融合	                    13
    异常属性                                                            14

    """


class LabelCore3d(object):
    """
    标签核心数据，与json文件项对应
    """
    # json文件里的item对应key在这里更新
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

    def __init__(self, label=0, id_num=0):

        self.label = label  # 类型 int
        self.id_num = id_num  # id  int
        self.cen_x = 0.0
        self.cen_y = 0.0
        self.cen_z = 0.0
        self.speed = 0.0
        # TODO angle 后续改为rot_z
        self.angle = 0.0
        self.length = 0.0
        self.width = 0.0
        self.height = 0.0
        self.is_cover = 0
        self.cover_level = 0
        self.conf = 0  # 置信度
        self.source = 0  # 来源
        self.attr_value = 0
        self.order_no = 0

        self.other_data = {}

        # print(vars(self))
        # for k, v in vars(self).items():
        #     print("'{}',".format(k))

    def getDataFromDict(self, dicData):
        if not isinstance(dicData, dict):
            print("LabelCore3d.getDataFromDict 输入不是字典")
            return

        self.label = dicData.get("label", 0)
        self.id_num = dicData.get("id_num", 0)
        self.cen_x = dicData.get("cen_x", 0.0)
        self.cen_y = dicData.get("cen_y", 0.0)
        self.cen_z = dicData.get("cen_z", 0.0)

        self.speed = dicData.get("speed", 0.0)
        self.angle = dicData.get("angle", 0.0)
        self.length = dicData.get("length", 0.0)
        self.width = dicData.get("width", 0.0)
        self.height = dicData.get("height", 0.0)

        self.is_cover = dicData.get("is_cover", 0)
        self.cover_level = dicData.get("cover_level", None)
        self.conf = dicData.get("conf", 0)
        self.source = dicData.get("source", 0)
        self.attr_value = dicData.get("attr_value", 0)
        self.order_no = dicData.get("order_no", 0)

        self.other_data = {
            k: v for k, v in dicData.items() if k not in LabelCore3d.KEYS
        }

    def convertToDict(self):
        data = {}
        try:
            data = dict(
                label=self.label,
                id_num=self.id_num,
                cen_x=self.cen_x,
                cen_y=self.cen_y,
                cen_z=self.cen_z,
                speed=self.speed,
                angle=self.angle,
                length=self.length,
                width=self.width,
                height=self.height,
                is_cover=self.is_cover,
                cover_level=self.cover_level,
                conf=self.conf,
                source=self.source,
                attr_value=self.attr_value,
                order_no=self.order_no,

            )
            for key, value in self.other_data.items():
                assert key not in data
                data[key] = value
        except Exception as e:
            print("LabelCore3d.convertToDict ", e)

        return data

    def getDataFromCsv(self, data):
        if isinstance(data, (list, tuple)) and len(data) == 15:
            self.id_num, self.label, self.cen_x, self.cen_y, self.cen_z,\
            self.speed, self.angle, self.length, self.width, self.height,\
            self.is_cover, self.cover_level, self.conf, self.source, self.attr_value = data

            self.cen_x, self.cen_y, self.cen_z = 0.01*self.cen_x, 0.01*self.cen_y, 0.01*self.cen_z
            self.length, self.width, self.height = 0.01 * self.length, 0.01 * self.width, 0.01 * self.height
            return True
        else:
            print("getDataFromCsv failed : data={}".format(data))
            return False


    def convertToCsv(self):
        result = [
            self.id_num, self.label, 100*self.cen_x, 100*self.cen_y, 100*self.cen_z,
            self.speed, self.angle, 100*self.length, 100*self.width, 100*self.height,
            self.is_cover, self.cover_level, self.conf, self.source, self.attr_value
        ]
        return result



if __name__ == "__main__":
    a = LabelCore3d()

    # print(vars(a))
    try:
        mm = getattr(a, 'angle')
        print(mm)
    except AttributeError:
        print('---')


