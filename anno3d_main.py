# Copyright (c) <2021-6> An-Haiyang
# 点云标注软件
#
# !/usr/bin/env python
# -*- coding: utf-8 -*-

# import argparse
# import codecs
# import subprocess
# from collections import defaultdict
import os
import pdb
import sys

import cv2
import numpy as np

sys.setrecursionlimit(1000000)
import os.path as osp
from functools import partial

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time
import json
import copy
import math
from interval import Interval
#  --------本地包----------
# 主界面UI
# 图像显示控件
from widgets.ImgWidget import ImgWidget
from widgets.drawboard import DrawBoard

from utils.qt_util import *
from utils.pub import *
from utils.camera_map import CameraMap
from utils.image_data import *


from widgets.vtk_widget import VTK_QWidget
from widgets.vtk_view import VTK_View
from widgets.view_canvas import CanvasView
from widgets.view_widget import ViewWidget
from widgets.gui_main import Ui_MainWindow
from widgets.file_list_widget import FileListWidgetItem
from widgets.para_edit_area_view import ParaEditAreaView
from widgets.panel_area_view import PanelAreaView
from widgets.traffic_tool_view import TrafficToolView

from utils.file_manage import *
from data.pcd_file_info import PcdFileInfo
from data.anno_info_3d import AnnoInfo3d
from utils.image_util import *

from config import __appname__, __version__

from data.cube_label import CubeLabel

from control.para_edit_area_controller import ParaEditAreaController

from config.label_type import label_csv_dic, traffic_property_dic
from manager.global_manager import global_manager


_title = __appname__ + ' v' + __version__

#  2021.07.26 提供一个对照字典
tar_type_dict = {
    "car": 0,
    "bicycle": 1,
    "bus": 2,
    "tricycle": 3,
    "pedestrian": 4,
    "semitrailer": 5,
    "truck": 6,
}

# 2023.01.31 axiong add 提供一个误差范围
Error_Scale=0.3

# 遮挡
tar_cover_dict = {
    "未遮挡": 0,
    "遮挡": 1
}
# 遮挡等级
tar_coverlevel_dict = {
    "0~30分": 0,
    "31~60分": 1,
    "61~90分": 2,
    "90分以上": 3
}
# 置信度
tar_conf_dict = {
    "默认": 0,
    "十分可疑": 1,
    "比较可疑": 2,
    "一般可信": 3,
    "十分可信": 4
}
# 信息来源
tar_source_dict = {
    "激光": 0,
    "视频": 1,
    "激光视频融合": 2
}
# 灵敏度 ：移动 拉伸 旋转
SensitivityDict = {
    'move': 18,
    'stretch': 12,
    'turn': 1,
    'fast_move': 50,
    'fast_stretch': 50,
    'fast_turn': 5
}

TEST_PATH = None
TEST_PATH = r'C:\Users\wanji\Desktop\标注测试\cloud\test4'


class AppEntry(QMainWindow, Ui_MainWindow):
    CACHE = "cache"  # 软件缓存目录
    LABEL_CACHE = "label_cache"  # 子目录，标签文件
    LABEL_CHECK = "label_check"  # 子目录，标签check出来的文件，受到改变时，将删除这里的问题
    ANNO_STATE_NAME = "anno_state.json"  # 标注状态文件名称
    RECYCLE = "recycle"  # 子目录，回收站
    OUTPUT = "output"  # 子目录,输出结果

    DEFAULT_FONT = getFont(0)
    CHECK_FONT = getFont(1)
    ABANDON_FONT = getFont(2)

    imgdisp_tab1 = 4  # 图像显示四个， 如果为1 ，表示只显示1个
    imgdisp_tab2 = 4

    def __init__(self, *args, **kwargs):
        super(AppEntry, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle(__appname__ + __version__)

        self._tar_type_dict = tar_type_dict

        # TODO 调节面板要移植出去为独立模块，输入：灵敏度，输出cube移动量，
        # 灵敏度 : 移动 拉伸 旋转
        self.SensitivityDict = {
            'move': 18,
            'stretch': 12,
            'turn': 1,
            'fast_move': 50,
            'fast_stretch': 50,
            'fast_turn': 5
        }

        self.initQtUi()

        self.initQtAction()
        self.initQtMenu()
        self.initQtToolbar()

        self.initQtSlot()

        # 类内成员变量
        self.fileName = None  # 名称
        self.fileBaseName = None  # 点云名称
        self.fileDir = None

        self.pcdList = []  # self.fileName * n
        self.lastOpenDir = None  # 上一次打开的文件夹
        self.lastOpenFile = None  # 上一次打开文件路径

        self.lastFileState = None  # 当前文件上一个文件状态
        self.labelCubes = []  # 当前图像文件标签列表 CubeLabel() * n

        self.pointsData = None  # pcd np数组
        self.pcdDict = {}  # 点云数据，key ：filename  ，val ： np数组
        self.labelDict = {}  # key: basename value: self.labelCubes  ，打开文件夹统一读取标签时记录。

        self.annoInfo = None  # 当前标注信息

        self.fileInfoDict = {}  # 记录文件标注状态,k : xx.pcd  v: PcdFileInfo()

        self.fileUpdateTimeDict = {}  # 标签文件更新时间戳，key: xx.png ,val: 时间
        self.fileAnnoDelayDict = {}  # 图标标注耗时，以打开到保存截止

        self._copied_cubes = None  # 粘贴板存储

        self.dirty = False  # 当前文件是否被修改过
        self._noSelectionSlot = False  # 标签列表选中触发标志位
        self._noLabelEditSlot = False  # 标签值变化触发标志位
        self._noFileSelectionSlot = False  # 文件删除，添加槽函数屏蔽

        self._noSyncEditSlot = False

        self.beginTime = None
        self.endTime = None

        VTK_QWidget.type_map = {v: k for k, v in self._tar_type_dict.items()}

        self.img={}  #  当前的图像和opencv读出来的字典

    def initQtUi(self):
        """
        初始化QT控件
        多vtk控件手动关闭，否则报错wglMakeCurrent failed in Clean()
        :return:
        """
        self.splitter.setStretchFactor(1, 10)
        self.splitter.setStretchFactor(2, 6)
        self.splitter.setHandleWidth(5)
        lay = QHBoxLayout(self.wid_labellist)
        self.BoxList = QListWidget(self.wid_labellist)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.BoxList)
        self.BoxList.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # VTK 三维控件显示
        self.vtk_widget = VTK_QWidget(parent=self)
        lay = QVBoxLayout(self.frame_pcd)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.vtk_widget)

        # 三视图
        self.view = ViewWidget()
        lay = QHBoxLayout(self.frmView)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.view)
        self.vtk_viewList = self.view.vtk_viewList
        self.canvas_viewList = self.view.canvas_viewList

        # 图像控件
        frame_list = [self.frame_1, self.frame_2, self.frame_3, self.frame_4, self.frame_5, self.frame_6, self.frame_7,
                      self.frame_8]
        self.imgWgtList = []
        for i in range(8):
            imgwid = DrawBoard(frame_list[i])
            lay = QVBoxLayout(frame_list[i])
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(imgwid)
            imgwid.setObjectName('imgwid{}'.format(i + 1))
            self.imgWgtList.append(imgwid)

        self.fileListWidget.setIconSize(QSize(20, 20))

        # 操作区 .............

        self.tab_edit_widget = QTabWidget(self)
        self.para_edit_view = ParaEditAreaView(self.tab_edit_widget)
        self.panel_area_view = PanelAreaView(self.tab_edit_widget)

        self.tab_edit_widget.addTab(self.para_edit_view, "参数编辑")
        self.tab_edit_widget.addTab(self.panel_area_view, "调节面板")

        self.con_para_edit = ParaEditAreaController(self.para_edit_view)
        setSliderPara(self.panel_area_view.slid_move, self.SensitivityDict['move'])
        setSliderPara(self.panel_area_view.slid_stretch, self.SensitivityDict['stretch'])


        self.verticalLayout_4.addWidget(self.tab_edit_widget)



    def initQtSlot(self):

        self.fileListWidget.itemSelectionChanged.connect(self.fileSelectionChanged)
        self.BoxList.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.BoxList.itemDoubleClicked.connect(self.labelDoubleClick)
        self.BoxList.itemChanged.connect(self.labelItemChanged)

        self.BoxList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.BoxList.customContextMenuRequested.connect(self.boxlist_right_menu)

        self.vtk_widget.selectionChanged.connect(self.cubeSelectionChanged)
        self.vtk_widget.newCube.connect(self.newCube)
        self.vtk_widget.cubeMoved.connect(self.moveCube)

        for can in self.canvas_viewList:
            can.moveShape.connect(self.viewShapeMove)
            can.rotShape.connect(self.viewShapeRot)
            can.finishShape.connect(self.viewShapeDone)
            can.rightpressShape.connect(self.viewShapeRightPress)

        for i in range(len(self.imgWgtList)):
            self.imgWgtList[i].signal_imgobjname.connect(self.slot_togg_img_display)
        self.splitter.splitterMoved.connect(self.view.syncViewSize)

        # 圆圈范围 、 点大小
        self.spin_circle_radius.valueChanged.connect(self.slot_set_boundary_radio)
        self.spin_point_size.valueChanged.connect(self.slot_update_size)

        self.panel_area_view.move_change_signal.connect(self.slot_slider_sens)
        self.panel_area_view.stretch_change_signal.connect(self.slot_slider_sens)

        # 参数编辑
        # TODO  self.slot_cube_pose_adjustment 面板
        # TODO self.slot_label_para_edit 参数触发

        for ew in self.con_para_edit.wid_list:
            #  ew is  EditWidget_
            ew.click_signal.connect(self.edit_para_property)

        self.panel_area_view.moving_signal.connect(self.slot_cube_pose_adjustment)

        self.traffic_tool_view.traffic_add_signal.connect(self.set_add_traffic_type)



    def initQtAction(self):
        action = partial(newAction, self)
        quit = action(
            text=self.tr("退出"),
            slot=self.close,
            shortcut="Ctrl+Shift+Q",
            tip="quit",
            icon="quit",
        )

        opendir = action(text='打开文件夹',
                         slot=self.openDirDialog,
                         shortcut='Ctrl+U',
                         icon='opendir',
                         tip='选择点云文件',
                         )
        opendir.setToolTip(opendir.toolTip() + ' ' + opendir.shortcut().toString())

        openPrevPcd = action(
            text=self.tr("上一个"),
            slot=self.openPrevPcd,
            shortcut="PgUp",
        )
        openNextPcd = action(
            text=self.tr("下一个"),
            slot=self.openNextPcd,
            shortcut="PgDown",
        )
        save = action(
            text='保存',
            slot=self.saveFile,
            shortcut="Ctrl+S",
            icon='save_all',
            enabled=False,
            tip='保存标签json文件',
        )
        saveAs = action(
            text=self.tr("另存为"),
            slot=None,
            shortcut=None,
        )
        export = action(
            text=self.tr("输出标注结果"),
            slot=self.exportCheckedLabel,
            shortcut="Ctrl+W",
        )

        check = action(
            text=self.tr("完成√"),
            slot=self.checkFile,
            shortcut="C",
            icon='finish'
        )

        normal = action(
            text=self.tr("待编辑"),
            slot=self.normalFile,
            shortcut=None,
            icon='unfinish',
        )
        abandon = action(
            text=self.tr("待丢弃"),
            slot=self.abandonFile,
            shortcut=None,
            icon='discard',
        )
        checkAll = action(
            text=self.tr("check所有文件"),
            slot=None,
            shortcut=None,
            enabled=False,
        )
        normalAll = action(
            text=self.tr("待编辑所有文件"),
            slot=None,
            shortcut=None,
            enabled=False,
        )
        deleteAbandon = action(
            text=self.tr("移除丢弃文件"),
            slot=None,
            shortcut=None,
            enabled=False,
            icon='remove',
            tip='移除丢弃的文件',
        )

        recovery = action(
            text=self.tr("回收站还原文件"),
            slot=None,
            shortcut=None,
            enabled=False,
        )

        duplicate = action(
            text=self.tr("拷贝"),
            slot=self.duplicateSelectedCube,
            shortcut="Ctrl+D",
            enabled=False,
        )

        copy = action(
            text=self.tr("复制"),
            slot=self.copySelectedCube,
            shortcut="Ctrl+C",
            enabled=False,
            icon='copy',
        )
        paste = action(
            text=self.tr("粘贴"),
            slot=self.pasteSelectedCube,
            shortcut="Ctrl+V",
            enabled=False,
        )
        delete = action(
            text=self.tr("删除"),
            slot=self.deleteSelectedCube,
            shortcut="Del",
            enabled=False,
            icon='del_box',
        )
        undo = action(
            text=self.tr("撤回"),
            slot=lambda: self.undoCubeEdit(True),
            shortcut="Ctrl+Z",
            enabled=False,
            icon='revoke',
            tip='返回上一步'
        )

        redo = action(
            text=self.tr("redo"),
            slot=lambda: self.undoCubeEdit(False),
            shortcut='Ctrl+Shift+Z',
            enabled=False,
            tip='恢复下一步'
        )
        hideAll = action(
            text=self.tr("隐藏所有标签"),
            # slot=partial(self.togglePolygons, False),
            shortcut=None,
            enabled=False,
        )

        showAll = action(
            text=self.tr("显示所有标签"),
            # slot=partial(self.togglePolygons, True),
            shortcut=None,
            enabled=False,
        )


        readclass = action(
            text=self.tr("读取标签类别"),
            slot=self.openClassDialog,
            shortcut=None,
            enabled=True,
        )

        syncTargetType = action(
            text=self.tr("同步目标类别"),
            slot=self.sync_target_type,
            shortcut=None,
            enabled=True,
            tip='根据当前帧id向后同步类别'
        )

        # axiong add 20230104
        image_label_show = action(
            text=self.tr("图片中显示标签label"),
            slot=self.Load_Image_Label,
            shortcut='Ctrl+X',
            enabled=True,
            tip='加载图片的时候把标签信息也显示出来'
        )

        # axiong add 20230209
        save_current_pic = action(
            text=self.tr("保存当前的图片"),
            slot=self.Save_Current_Pic,
            shortcut='Ctrl+N',
            enabled=True,
            tip='把当前的图片标注框图片保存'
        )

        # axiong add20230131
        check_label_size=action(
            text=self.tr("label尺寸错误检查"),
            slot=self.Check_Label_Size,
            shortcut='Ctrl+M',
            enabled=True,
            tip='对当前帧的label进行一个尺寸检查，不符合的高亮显示'
        )

        # axiong add 20230316
        check_label_overlap = action(
            text=self.tr("label重叠检查"),
            slot=self.Check_Label_Overlap,
            shortcut='Ctrl+L',
            enabled=True,
            tip='对当前帧的label进行遍历，重叠部分高亮显示'
        )


        self.actions = struct(opendir=opendir, quit=quit, openPrevPcd=openPrevPcd, openNextPcd=openNextPcd,
                              save=save, saveAs=saveAs, export=export, check=check, normal=normal, abandon=abandon,
                              checkAll=checkAll, normalAll=normalAll, deleteAbandon=deleteAbandon, recovery=recovery,
                              duplicate=duplicate, copy=copy, paste=paste, delete=delete, undo=undo, redo=redo,
                              hideAll=hideAll, showAll=showAll, readclass=readclass, syncTargetType=syncTargetType,
                              image_label_show=image_label_show, save_current_pic=save_current_pic,
                              check_label_size=check_label_size,check_label_overlap=check_label_overlap)



        self.labelMenu = QMenu()
        addActions(self.labelMenu, (delete, copy, paste, duplicate, syncTargetType))

        # TODO 封装...
        # 删除框
        self.del_cube_btn.setDefaultAction(self.actions.delete)
        self.del_cube_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.del_cube_btn.setIconSize(QtCore.QSize(16, 16))
        # 完成按钮
        self.checkButton.setDefaultAction(self.actions.check)
        self.checkButton.setIconSize(QtCore.QSize(16, 16))
        self.checkButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        # 撤销按钮
        self.revoke_btn.setDefaultAction(self.actions.undo)
        self.revoke_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.revoke_btn.setIconSize(QtCore.QSize(16, 16))
        # 待编辑
        self.editingButton.setDefaultAction(self.actions.normal)
        self.editingButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.editingButton.setIconSize(QtCore.QSize(16, 16))
        # 待删除
        self.wait_remove_Button.setDefaultAction(self.actions.abandon)
        self.wait_remove_Button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.wait_remove_Button.setIconSize(QtCore.QSize(16, 16))
        # 复制框
        self.copy_cube_btn.setDefaultAction(self.actions.duplicate)
        self.copy_cube_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.copy_cube_btn.setIconSize(QtCore.QSize(16, 16))

    def initQtMenu(self):
        self.menus = struct(
            file=self.menu('&文件'),
            edit=self.menu('&编辑'),
            view=self.menu('&视图'),
            autolabel=self.menu('&模型'),
            help=self.menu('&帮助'),
            labelList=self.labelMenu
        )

        addActions(self.menus.file, (self.actions.opendir, self.actions.openPrevPcd, self.actions.openNextPcd,
                                     self.actions.save, self.actions.saveAs, self.actions.export,
                                     self.actions.readclass))

        addActions(self.menus.edit, (self.actions.check, self.actions.normal, self.actions.abandon,
                                     self.actions.checkAll, self.actions.normalAll, self.actions.deleteAbandon,
                                     self.actions.recovery, self.actions.duplicate, self.actions.copy,
                                     self.actions.paste, self.actions.delete, self.actions.undo, self.actions.redo))

        addActions(self.menus.view, (self.actions.hideAll, self.actions.showAll, self.actions.image_label_show,
                                     self.actions.save_current_pic,self.actions.check_label_size,self.actions.check_label_overlap))

    def initQtToolbar(self):
        """
        工具栏初始化
        :return:
        """
        self.toolbar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.insertToolBarBreak(self.toolbar)
        self.toolbar.addAction(self.actions.opendir)
        self.toolbar.addAction(self.actions.save)
        self.toolbar.addAction(self.actions.readclass)
        self.toolbar.addSeparator()

        self.lbl_circle = QLabel("范围")
        self.spin_circle_radius = QDoubleSpinBox(self.toolbar)
        self.spin_circle_radius.setMinimum(1)
        self.spin_circle_radius.setMaximum(200)
        self.spin_circle_radius.setDecimals(1)
        self.spin_circle_radius.setSingleStep(1)
        self.spin_circle_radius.setValue(75)

        self.toolbar.addWidget(self.lbl_circle)
        self.toolbar.addWidget(self.spin_circle_radius)
        self.toolbar.addSeparator()

        self.lbl_point_size = QLabel("size")
        self.spin_point_size = QDoubleSpinBox(self.toolbar)
        self.spin_point_size.setDecimals(1)
        self.spin_point_size.setMinimum(0.1)
        self.spin_point_size.setMaximum(5.0)
        self.spin_point_size.setSingleStep(0.1)
        self.spin_point_size.setValue(1.0)

        self.toolbar.addWidget(self.lbl_point_size)
        self.toolbar.addWidget(self.spin_point_size)

        self.toolbar.addSeparator()
        # 设置向后搜索最大文件数量。
        self.lbl_search_back_file = QLabel("同步最大文件数")
        self.spin_search_back_file = QSpinBox(self.toolbar)
        self.spin_search_back_file.setMinimum(1)
        self.spin_search_back_file.setMaximum(1000)
        self.spin_search_back_file.setSingleStep(10)
        self.spin_search_back_file.setValue(10)
        self.toolbar.addWidget(self.lbl_search_back_file)
        self.toolbar.addWidget(self.spin_search_back_file)

        self.lbl_max_cube_id_nums = QLabel("当前Max_Cube_ID:")
        self.lbl_max_cube_id_nums_ = QLabel("0")
        self.toolbar.addWidget(self.lbl_max_cube_id_nums)
        self.toolbar.addWidget(self.lbl_max_cube_id_nums_)
        #  工具栏2 ...

        self.toolbar2 = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar2)
        self.insertToolBarBreak(self.toolbar2)
        self.traffic_tool_view = TrafficToolView(self.toolbar2)
        self.toolbar2.addWidget(self.traffic_tool_view)
        # self.toolbar2.addAction(self.actions.opendir)


    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            addActions(menu, actions)
        return menu


    def openDirDialog(self, _value=False, dirpath=None):
        if not self.mayContinue():
            return

        defaultOpenDirPath = dirpath if dirpath else "."
        if self.lastOpenDir and osp.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = (osp.dirname(self.fileName) if self.fileName else ".")

        if TEST_PATH is not None:
            defaultOpenDirPath = TEST_PATH

        targetDirPath = str(
            QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self.tr("%s - Open Directory") % _title,
                defaultOpenDirPath,
                QtWidgets.QFileDialog.ShowDirsOnly
                | QtWidgets.QFileDialog.DontResolveSymlinks,
            )
        )
        print('targetDirPath=', targetDirPath)
        self.importDirPcds(targetDirPath)

    def checkFile(self):
        """
        check 完成标注
        :return:
        """
        # import pdb;pdb.set_trace()
        if self.lastFileState is not None and self.lastFileState == PcdFileInfo.CHECK:
            # 标签没有做任何改变，自动打开下一个pcd文件
            self.openNextPcd()
            return
        if self.dirty:
            self.saveFile()  # 保存文件
        # 保存到check文件夹
        check_path = self.getCheckLabelPath(self.fileName)
        self._saveFile(check_path)

        # 更新文件状态
        try:
            self.updateFileInfo(state=PcdFileInfo.CHECK)
            self.openNextPcd()
        except Exception as e:
            print(e)

    def normalFile(self):
        """
        待编辑模式触发
        :return:
        """
        if self.lastFileState is not None and self.lastFileState == PcdFileInfo.NORMAL:
            return

        if self.lastFileState == PcdFileInfo.CHECK:
            self.deleteCheck(self.fileName)

        # 更新文件状态
        try:
            self.updateFileInfo(PcdFileInfo.NORMAL)
        except Exception as e:
            print(e)

    def abandonFile(self):
        if self.lastFileState is not None and self.lastFileState == PcdFileInfo.ABANDON:
            return
        if self.lastFileState == PcdFileInfo.CHECK:
            self.deleteCheck(self.fileName)

        # 更新文件状态
        try:
            self.updateFileInfo(PcdFileInfo.ABANDON)
        except Exception as e:
            print(e)

    def updateFileInfo(self, state=PcdFileInfo.NORMAL):
        """
        更新文件状态显示，更新文件
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        # pdb.set_trace()
        f_info = self.fileInfoDict[self.fileBaseName]
        f_info.state = state
        # 更新文件列表, TODO 字典与文件列表item.data 对应一致
        currIndex = self.pcdList.index(self.fileName)
        print("currIndex=", currIndex)
        item = self.fileListWidget.item(currIndex)
        item.setFileMode(state=f_info.state)
        print('字典与item一致性验证: ', item.file() == f_info)

        # 更新时间戳、时长保存到文件状态数据
        f_info.update_timestamp = self.annoInfo.updateTime
        f_info.anno_delay = self.annoInfo.annoDelay
        # 保存文件状态信息
        self.saveAnnoInfo()
        self.lastFileState = state
        # TODO 更新显示文件个数reportFileState

    def fileSelectionChanged(self):
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if self._noFileSelectionSlot:
            return
        items = self.fileListWidget.selectedItems()

        if not items:
            return
        item = items[0]
        if not self.mayContinue():
            return
        try:
            currIndex = self.fileListWidget.indexFromItem(item).row()


            if currIndex is not None and currIndex < len(self.pcdList):
                filename = self.pcdList[currIndex]
                if filename:
                    self.loadFile(filename)
        except Exception as e:
            print(sys._getframe().f_lineno, " ", e)

    def cubeSelectionChanged(self, selected_cubes):
        """
        3D框选中变化触发
        :param selected_cubes:
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        self._noSelectionSlot = True
        for cube in self.vtk_widget.cubes:
            cube.selected = False
        self.BoxList.clearSelection()
        self.vtk_widget.selectedCubes = selected_cubes
        for cube in selected_cubes:
            cube.selected = True
            item = self.findItemByCube(cube)
            index = self.BoxList.indexFromItem(item)
            self.BoxList.selectionModel().select(index, QtCore.QItemSelectionModel.Select)
            self.BoxList.scrollToItem(item)

        for vv in self.vtk_viewList:
            vv.loadCubeLabel(selected_cubes)
            # print('AAAA: ', vv.getWindowSize())
        self.updateCanvasView()

        self._noSelectionSlot = False
        # print('shapeSelectionChanged=', self.labelList.currentIndex().row())
        # 刷新显示标签编辑区
        self._noLabelEditSlot = True
        self.updateLabelEdit()  # 编辑区刷新
        self._noLabelEditSlot = False
        n_selected = len(selected_cubes)
        self.actions.delete.setEnabled(n_selected)
        self.actions.duplicate.setEnabled(n_selected)
        self.actions.copy.setEnabled(n_selected)
        # self.actions.edit.setEnabled(n_selected == 1)


    def labelSelectionChanged(self):
        """
        标签列表选中变化触发
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if self._noSelectionSlot:
            return
        selected_cubes = []

        for item in self.BoxList.selectedItems():
            selected_cubes.append(item.data(Qt.UserRole))
        if selected_cubes:
            self.vtk_widget.selectCubes(selected_cubes)
        else:
            self.vtk_widget.deSelectCube()

    def boxlist_right_menu(self, pos):
        self.menus.labelList.exec_(self.BoxList.mapToGlobal(pos))

    def updateVtkView(self, index=None):
        """
        vtk三视图更新
        :param index:
        :return:
        """
        for i in range(len(self.vtk_viewList)):
            self.vtk_viewList[i].updateView(change_view=(i != index))  # index视图不改变相机位置

    def updateCanvasView(self, index=None):
        """
        更新三视图图像
        :param index: index = 0 1 2 时，当前控件只刷新背景图
        :return:
        """
        for i in range(3):
            self.canvas_viewList[i].setImage(self.vtk_viewList[i].getScreen())
            if index is None or i != index:
                self.canvas_viewList[i].setPoints(self.vtk_viewList[i].getPixPoints())
    
    def updateThreeView(self, index=None):
        # 三视图数据变化
        self.updateVtkView(index)
        self.updateCanvasView(index)

    def updatePointSize(self, size=None, view_size=None):
        """
        更新点云点的大小显示
        :param size: 主控件点云大小
        :param size_view: 三视图点云的大小
        :return:
        """
        # 更新主界面点大小
        if size is not None:
            self.vtk_widget.updatePointSize(size)
        # 更新三视图点大小
        if view_size is not None:
            for i in range(len(self.vtk_viewList)):
                self.vtk_viewList[i].updatePointSize(view_size)

            self.updateThreeView()
    
    def labelDoubleClick(self, item):
        """
        双击， 定位这个视角
        :param item:
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        cube = item.data(Qt.UserRole)
        self.vtk_widget.focusThisCube(cube)

    def labelItemChanged(self, item):
        """
        item内容变化 ， 或勾选变化，触发此函数
        :param item:
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        cube = item.data(Qt.UserRole)
        self.vtk_widget.setCubeVisible(cube, item.checkState() == Qt.Checked)
        self.vtk_widget.redisplay()

    def updateLabelEdit(self):
        """
        更新数据编辑区控件显示
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        # TODO gaigai
        if self._noSyncEditSlot:
            return
        if len(self.vtk_widget.selectedCubes) == 1:
            try:
                cube = self.vtk_widget.selectedCubes[0]
                data = [cube.cen_x, cube.cen_y, cube.cen_z, cube.angle, cube.length, cube.width, cube.height]
                for name in ['label','id_num','speed','is_cover','cover_level','conf','source','attr_value']:
                    if hasattr(cube, name):
                        self.con_para_edit.set_edit_value(name, getattr(cube, name, 0))

            except Exception as e:
                print(e)


    def newCube(self):
        """
        新增标签，by鼠标绘制
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)

        try:
            # TODO 设置新增标签的名称、id --setLastCube
            added_cube = self.vtk_widget.setLastCube()
            self.addLabel(added_cube)

            self.setDirty()
        except Exception as e:
            print(e)

    def moveCube(self, cubes):
        """
        移动标签3D框，刷新标签列表数据
        :param cubes:
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        self._noLabelEditSlot = True  # 屏蔽编辑框槽触发
        self.refreshLabels(cubes)
        # TODO 编辑区数据变化..
        self.updateLabelEdit()

        # 三视图数据变化
        self.updateThreeView()

        # 图像变化
        self.Image_Label_Show()

        self._noLabelEditSlot = False
        self.setDirty()

    #axiong add 20221109
    def viewShapeRightPress(self,view_mode,ids):
        """
        鼠标右键点击三视图中的四个拉伸点（点击单次），四个拉伸点对应四条边边，三视图中会直接将图拉到最边缘的点云边边
        """
        data=self.pointsData
        for i in range(len(self.vtk_widget.selectedCubes)):
            newdata = []
            cube=self.vtk_widget.selectedCubes[i]
            min_x,max_x = cube.cen_x - cube.length / 2, cube.cen_x + cube.length / 2
            min_y,max_y = cube.cen_y - cube.width / 2, cube.cen_y + cube.width / 2
            min_z,max_z = cube.cen_z - cube.height / 2, cube.cen_z + cube.height / 2
            for j in range(data.shape[0]):
                if min_x <= data[j][0] <= max_x and  min_y <= data[j][1] <= max_y and  min_z <= data[j][2] <= max_z :
                    newdata.append(data[j])
            newdata = np.array(newdata)
            newdata_x = newdata[:, 0]
            newdata_y = newdata[:, 1]
            newdata_z = newdata[:, 2]
            min_newdata_x, max_newdata_x = min(newdata_x), max(newdata_x)
            min_newdata_y, max_newdata_y = min(newdata_y), max(newdata_y)
            min_newdata_z, max_newdata_z = min(newdata_z), max(newdata_z)
            cube.length=max_newdata_x-min_newdata_x
            cube.width=max_newdata_y-min_newdata_y
            cube.height=max_newdata_z-min_newdata_z
            cube.cen_x = (max_newdata_x + min_newdata_x) / 2
            cube.cen_y = (max_newdata_y + min_newdata_y) / 2
            cube.cen_z = (max_newdata_z + min_newdata_z) / 2
            cube.updatePose()
            self.moveCubeByView(view_mode)


    def moveCubeByView(self, view_mode):
        """
        三视图改变框，刷新显示
        :param view_mode:
        :return:
        """
        index = self.getViewIndex(view_mode)
        cube = self.vtk_viewList[index].cube

        self._noLabelEditSlot = True  # 屏蔽编辑框槽触发
        self.refreshLabels([cube])
        self.updateLabelEdit()
        # 三视图数据变化
        self.updateThreeView(index)

        self._noLabelEditSlot = False
        self.setDirty()


    def viewShapeMove(self, view_mode, delta):
        """
        三视图2D框移动触发
        :param view_mode: which view
        :param delta: 变化量
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        try:
            delta_cen, delta_wh = delta
            index = self.getViewIndex(view_mode)
            k = self.vtk_viewList[index].getPixRatio()  # 比例 pix/m
            cube = self.vtk_viewList[index].cube  # 被调整的cube
            dx = dy = dz = 0  # 目标移动距离，xyz为前、左、上 方向
            dl = dw = dh = 0

            # TODO 三视图二维向三维变化映射字典
            # 视图移动换算三维移动
            if view_mode == CanvasView.V_BIRD:
                dy = -delta_cen[0] / k
                dx = -delta_cen[1] / k
                dw = delta_wh[0] / k
                dl = delta_wh[1] / k
            elif view_mode == CanvasView.V_SIDE:
                dx = delta_cen[0] / k
                dz = -delta_cen[1] / k
                dl = delta_wh[0] / k
                dh = delta_wh[1] / k

            elif view_mode == CanvasView.V_FRONT:
                dy = delta_cen[0] / k
                dz = -delta_cen[1] / k
                dw = delta_wh[0] / k
                dh = delta_wh[1] / k

            cube.poseChange(delta_pos=(dx, dy, dz))
            cube.sizeChange(delta_size=(dl, dw, dh))
            cube.updatePose()
            self.moveCubeByView(view_mode)
        except Exception as e:
            print(e)

    def viewShapeRot(self, view_mode, delta):
        """
        三视图旋转
        :param view_mode:
        :param delta: 角度
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        try:
            index = self.getViewIndex(view_mode)
            cube = self.vtk_viewList[index].cube  # 被调整的cube
            dtheta = 0
            # print("dtheta = ", dtheta)

            # TODO 三视图二维向三维变化映射字典
            # 旋转只能在俯视图下发生。
            if view_mode == CanvasView.V_BIRD:
                dtheta = -delta  # 负数以为图像坐标系与三视图，Z反的
            elif view_mode == CanvasView.V_SIDE:
                pass
            elif view_mode == CanvasView.V_FRONT:
                pass

            cube.angle += dtheta
            cube.updatePose()
            self.moveCubeByView(view_mode)
        except Exception as e:
            print(e)

    def viewShapeDone(self):
        """
        三视图调整完毕
        :return:
        """
        self.updateThreeView(None)
        self.vtk_widget.endEditCube()


    def getViewIndex(self, view_mode, def_ret=0):
        """
        根据视图模式，获取视图编号, vtk和图像列表对应
        :param view_mode:uu
        :param def_ret:
        :return:
        """

        for i in range(len(self.canvas_viewList)):
            if self.canvas_viewList[i].getViewMode() == view_mode:
                return i
        return def_ret

    def importDirPcds(self, dirpath, pattern=None, load=True):
        """
        载入pcd文件夹
        :param dirpath:
        :param pattern:
        :param load:
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        self.actions.openNextPcd.setEnabled(True)
        self.actions.openPrevPcd.setEnabled(True)
        if not self.mayContinue() or not dirpath:
            return
        if not osp.exists(dirpath):
            return
            # TODO 数据初始化操作

        self.lastOpenDir = dirpath
        self.fileName = None
        self.fileListWidget.clear()
        self.pcdList = scan_files(dirpath, [".pcd", ".bin"])
        self.fileDir = dirpath
        self.resetImgWidget()
        self.resetVtkWidget(True)
        self.filedock.setWindowTitle("文件列表")
        # 查看加载class.json文件
        # self.loadTypeMap(osp.join(self.fileDir, "class.json"))
        self.loadTypeMap(osp.join(self.fileDir, "car_type.yaml"))

        # 读算法标注文件----
        # self.labelDict = {}

        # 读状态---
        self.fileInfoDict = {}
        anno_state_file = self.getFileInfoPath()
        # print("anno_state_file:",anno_state_file)
        self.fileInfoDict = self.loadFileInfo(anno_state_file)
        # print("self.fileInfoDict:",self.fileInfoDict)
        # print("self.getFileStateCnt():",self.getFileStateCnt())
        # 汇报状态---
        fs = self.getFileStateCnt()
        # self.reportFileState()

        # 加载文件目录
        # print(self.pcdList)
        for filename in self.pcdList:
            if pattern and pattern not in filename:
                continue
            bn = osp.basename(filename)
            f_info = PcdFileInfo(bn)
            f_info = dic_getset(self.fileInfoDict, bn, f_info)
            item = FileListWidgetItem(text=str(bn), file=f_info)

            # TODO 看是否检查有没有独立json。打√
            self.fileListWidget.addItem(item)

        self.openNextPcd(load=load)
        self.setClean()

    def openPrevPcd(self, _value=False):
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if not self.mayContinue():
            return
        if len(self.pcdList) <= 0:
            return
        if self.fileName is None:
            return

        currIndex = self.pcdList.index(self.fileName)
        if currIndex - 1 >= 0:
            filename = self.pcdList[currIndex - 1]
            self.fileName = filename
            self.loadFile(filename)

    def openNextPcd(self, _value=False, load=True):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        # pdb.set_trace()
        if not self.mayContinue():
            return

        if len(self.pcdList) <= 0:
            return
        if self.fileName is None:
            filename = self.pcdList[0]
        else:
            currIndex = self.pcdList.index(self.fileName)
            if currIndex + 1 < len(self.pcdList):
                filename = self.pcdList[currIndex + 1]
            else:
                filename = self.pcdList[-1]
        self.fileName = filename
        if self.fileName and load:
            self.loadFile(self.fileName)

    def loadFile(self, filename=None):
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name, ' ', \
              sys._getframe().f_back.f_code.co_name, ' ', sys._getframe().f_back.f_back.f_code.co_name)
        # 预防重复进入,
        if filename in self.pcdList and (
                self.fileListWidget.currentRow() != self.pcdList.index(filename)
        ):
            print('loadFile=', self.fileListWidget.currentRow(), '  ', self.pcdList.index(filename))
            self.fileListWidget.setCurrentRow(self.pcdList.index(filename))
            self.fileListWidget.update()
            return

        print('loadFile 进入', filename)
        idx = self.pcdList.index(filename)
        self.filedock.setWindowTitle("文件列表 {}/{}".format(idx + 1, len(self.pcdList)))
        self.resetState()

        # 判断filename是否存在
        if not QtCore.QFile.exists(str(filename)):
            self.errorMessage(self.tr("Error opening file"), self.tr("No such file: <b>%s</b>") % filename)
            return False
        self.status(str(self.tr("Loading %s...")) % osp.basename(str(filename)))

        self.beginTime = time.time()

        # 判断基站id名，取消了暂时
        self.fileName = filename
        self.fileBaseName = osp.basename(filename)

        # 加载点云
        ret = self.loadPoints(filename)
        if not ret:
            # TODO 加载点云失败，退出
            print('加载点云失败，退出')
            return

        # 加载标签
        ret = self.loadLabelInfo(filename)
        self.vtk_widget.initShowPcdCubes(self.pointsData, self.labelCubes)
        for vv in self.vtk_viewList:
            vv.initShowPcd(self.pointsData)


        self.slot_update_size() # axiong add 20221108 需求是切换帧的时候要先检索spin_point_size.value()的值
        self.updateCanvasView()

        # 显示标签列表
        self.loadLabels(self.labelCubes)

        # 加载当前文件状态详细信息 TODO 显示文件状态信息  pcd_info ...
        f_info = dic_getset(self.fileInfoDict, self.fileBaseName, PcdFileInfo(self.fileBaseName))
        f_info.update_timestamp = self.annoInfo.updateTime if f_info.update_timestamp is None else f_info.update_timestamp
        f_info.anno_delay = self.annoInfo.annoDelay if f_info.anno_delay is None else f_info.anno_delay
        self.fileInfoDict[self.fileBaseName] = f_info

        self.lastFileState = self.fileInfoDict[self.fileBaseName].state

        # 加载显示图像
        self.loadImages(self.fileDir)

        self.setClean()
        self.vtk_widget.setFocus()
        self.setWindowTitle(__appname__ + __version__ + '   ' + filename)
        # 根据文件状态使能action  check

    def loadPoints(self, filename, def_ret=False):
        """
        加载点云
        :param filename:
        :param def_ret:
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        self.pointsData = self.pcdDict.get(filename, None)
        if self.pointsData is not None:
            return True
        self.pointsData = load_points_cloud(filename)
        if self.pointsData is not None:
            self.pcdDict[filename] = self.pointsData
            return True
        return def_ret

    def loadLabelInfo(self, filename, def_ret=False):
        """
        加载标签数据 json
        :param filename: 当前pcd文件名
        :return:
        """
        try:
            path = self.getLabelPath(filename)
            self.annoInfo = AnnoInfo3d()
            data = {}
            if osp.exists(path):
                data = read_json_file(path, def_ret=data)
                self.annoInfo.getDataFromDict(data)
                # 标签列表  []
                self.labelCubes = self.annoInfo.cubes

            else:
                # json文件不存在
                self.labelCubes = self.labelDict.get(self.fileBaseName, [])
                self.annoInfo.cubes = self.labelCubes

            return True
        except Exception as e:
            print('In Func [{}], err is {}'.format(sys._getframe().f_code.co_name, e))
            return def_ret

    def loadFileInfo(self, filename):
        """
        读取pcd状态文件json
        :param filename:
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        result = {}
        if not osp.exists(filename):
            return {}

        dic_data = read_json_file(filename)

        # import pdb
        # pdb.set_trace()

        if bool(dic_data):
            for k, v in dic_data.items():
                f_info = PcdFileInfo(k)
                f_info.getDataFromDict(v)
                result[k] = f_info
        return result

    def loadLabels(self, cubes):
        """
        加载标签列表
        :param cubes:
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        temp_cubes={}   # axiong add 20230309 加载标签数据的时候按照 cube.id_num 升序的顺序 additem
        for cube in cubes:
            temp_cubes[cube]=cube.id_num
        temp_cubes=dict(sorted(temp_cubes.items(),key=lambda x:x[1]))
        temp_cubes_key=list(temp_cubes.keys())
        max_cube_id_num=int(self.lbl_max_cube_id_nums_.text())
        if temp_cubes[temp_cubes_key[-1]] > max_cube_id_num:
            self.lbl_max_cube_id_nums_.setText(str(temp_cubes[temp_cubes_key[-1]]))

        self._noSelectionSlot = True
        # TODO 这里addLabel 暂时默认都是显示状态，待cube含有隐藏属性，再在addLabel加入判定勾选
        for cube in temp_cubes_key:
            self.addLabel(cube)
        self.BoxList.clearSelection()
        self._noSelectionSlot = False
        self.refreshLabels(temp_cubes_key)

    def addLabel(self, cube):
        """
        添加标签
        :param cube:
        :return:
        """

        item = QListWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        text = self.dispLabelText(cube)
        item.setText(text)
        item.setData(Qt.UserRole, cube)

        # TODO 暂时默认都是显示状态，待cube含有隐藏属性，在此更新，设置三维显示字典setCubeVisible
        item.setCheckState(Qt.Checked)
        # self.vtk_widget.setCubeVisible(cube, item.checkState() == Qt.Checked)
        self.BoxList.addItem(item)

    def dispLabelText(self, cube):
        """
        标签显示
        :param cube:
        :return:
        """
        # TODO yaml配置化、 增加颜色显示

        if isinstance(cube, CubeLabel):
            pos = np.array([cube.cen_x, cube.cen_y, cube.cen_z])
            pos = np.round(pos, 3)
            scale = np.array([cube.length, cube.width, cube.height])
            scale = np.round(scale, 3)
            rz = np.round(cube.angle, 3)

            disp_str = 'NO.{0} : '.format(cube.order_no + 1) + \
                       '目标ID = {0}, 类型 = {1}, 属性 = {2}\n'.format(cube.id_num, cube.label, cube.attr_value) + \
                       '        Pos = {0},θ = {1},'.format(pos, rz) + \
                       'Size = {0}'.format(scale)
            return disp_str
        else:
            err_msg = '输入对象错误 ,cube= ', type(cube)
            print(err_msg)
            return '——'

    def refreshLabels(self, cubes):
        """
        刷新标签列表显示
        :param cubes:
        :return:
        """
        try:
            for cube in cubes:
                item = self.findItemByCube(cube)
                text = self.dispLabelText(cube)
                item.setText(text)
        except Exception as e:
            print("refreshLabels  ", e)

    def remLabels(self, cubes):
        """
        删除标签
        :param cubes:
        :return:
        """
        for cube in cubes:
            item = self.findItemByCube(cube)
            # row = self.BoxList.indexFromItem(item).row()
            # self.BoxList.takeItem(row)
            index = self.BoxList.indexFromItem(item)
            self.BoxList.model().removeRows(index.row(), 1)

    def findItemByCube(self, cube):
        for row in range(self.BoxList.count()):
            item = self.BoxList.item(row)
            if item.data(Qt.UserRole) == cube:
                return item
        raise ValueError("cannot find cube: {}".format(cube))

    def loadImages(self, fileDir):
        """
        加载图像
        :return:
        """
        self.Map_Config_path=fileDir+'/Image_Map_Config.json'
        extensions = ['png', 'jpg', 'jpeg', 'bmp']
        #  点云和图像索引的方式是点云名称基站_后的名称寻找图像包含这个字符串的
        search_node = str(osp.splitext(self.fileBaseName)[0])
        search_node = search_node.split('_')[1] if '_' in search_node else search_node
        # print("search_node", search_node)

        # 目前支持8路照片显示，TODO
        self.picpath = []
        for i in range(8):
            child_dir = 'pic_%d' % (i + 1)
            imgpath = fuzzy_search_file(path=osp.join(fileDir, child_dir),
                                        filename=search_node,
                                        suffix=extensions)

            self.picpath.append(imgpath)

        for i in range(len(self.picpath)):
            if self.picpath[i] is not None and osp.exists(self.picpath[i]):
                # self.Image_is_ok = True
                self.imgWgtList[i].load_image(img_to_pix(self.picpath[i]), self.picpath[i])
                self.imgWgtList[i].setToolTip(str(self.picpath[i]))
            else:
                # self.Image_is_ok = False
                self.imgWgtList[i].clean()
                self.imgWgtList[i].setToolTip('')

    def errorMessage(self, title, message):
        return QtWidgets.QMessageBox.critical(
            self, title, "<p><b>%s</b></p>%s" % (title, message)
        )

    def infoMessage(self, title, message):
        return QtWidgets.QMessageBox.information(
            self, title, "<p><b>%s</b></p>%s" % (title, message)
        )

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def duplicateSelectedCube(self):
        """
        拷贝 ctrl+d
        :return:
        """
        added_cubes = self.vtk_widget.duplicateSelectedCubes()
        self.BoxList.clearSelection()

        for cube in added_cubes:
            self.addLabel(cube)
        self.refreshLabels(self.vtk_widget.cubes)  # 刷新标签序号和列表显示
        self.setSelectCube(added_cubes)
        self.setDirty()

    def pasteSelectedCube(self):
        """
        粘贴 ctrl+v
        :return:
        """
        if self._copied_cubes is None:
            return
        add_cubes = [cube.copy() for cube in self._copied_cubes]
        self.vtk_widget.pasteCubes(add_cubes)
        self.loadLabels(add_cubes)  # 添加标签
        self.setSelectCube(add_cubes)  # 选中被粘贴的标签
        self.setDirty()

    def copySelectedCube(self):
        """
        复制 ctrl+c
        :return:
        """
        self._copied_cubes = [c.copy() for c in self.vtk_widget.selectedCubes]
        self.actions.paste.setEnabled(len(self._copied_cubes) > 0)

    def deleteSelectedCube(self):
        """
        删除选中3D框
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)

        del_cubes = self.vtk_widget.deleteSelected()
        self.remLabels(del_cubes)
        self.refreshLabels(self.vtk_widget.cubes)

        for vv in self.vtk_viewList:
            if vv.cube in del_cubes:
                vv.cube = None

        self.updateThreeView()
        self.setDirty()
        if self.noCubes():
            pass
            # TODO  使能一些action

    def setSelectCube(self, cubes):
        """
        选中3D框, 标签列表、粘贴、拷贝用到此函数
        :param cubes:
        :return:
        """
        self.vtk_widget.selectCubes(cubes)
        # self.vtk_widget.redisplay()


    def undoCubeEdit(self, undo=True):
        """
        撤回 功能
        :return:
        """
        # 清除三视图显示，--如果有的显示的话
        for vv in self.vtk_viewList:
                vv.cube = None
        self.updateThreeView()
        # 缓存取数据
        self.vtk_widget.restoreCube(undo)
        # 刷新标签列表
        self.BoxList.clear()
        self.loadLabels(self.vtk_widget.cubes)

        # 刷新编辑区

        self.actions.undo.setEnabled(self.vtk_widget.isCubeRestorable(True))
        self.actions.redo.setEnabled(self.vtk_widget.isCubeRestorable(False))



    def resetImgWidget(self):
        """
        清空图像显示
        :return:
        """
        try:
            for imgwid in self.imgWgtList:
                imgwid.clean()
                imgwid.setToolTip('')
        except Exception as e:
            print(e)

    def resetVtkWidget(self, force=False):
        """
        清空vtk
        :return:
        """
        self.vtk_widget.initVTKUI()

        if force:  # 三视图的也清理
            for i in range(3):
                self.vtk_viewList[i].initVTKUI()
                self.canvas_viewList[i].reset()

    def resetState(self):

        self.BoxList.clear()
        self.fileName = None
        self.fileBaseName = None
        self.pointsData = None
        self.labelCubes = []

        self.resetImgWidget()
        self.resetVtkWidget()
        self.setWindowTitle(__appname__ + __version__)

    def getFileStateCnt(self, def_ret=None):
        """
        获取文件状态个数
        :return:
        """
        try:
            check_cnt = 0
            abandon_cnt = 0
            # normal_cnt = 0
            for k, v in self.fileInfoDict.items():
                if v.state == PcdFileInfo.CHECK:
                    check_cnt += 1
                elif v.state == PcdFileInfo.ABANDON:
                    abandon_cnt += 1

            all_cnt = len(self.pcdList)
            if all_cnt == 0:
                return def_ret
            normal_cnt = all_cnt - check_cnt - abandon_cnt

            return (normal_cnt, check_cnt, abandon_cnt)
        except Exception as e:
            print(e)
            return def_ret

    def mayContinue(self):
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if not self.dirty:
            return True
        mb = QtWidgets.QMessageBox
        msg = self.tr('Save annotations to "{}" before closing?').format(self.fileName)
        answer = mb.question(self, self.tr("Save annotations?"), msg, mb.Save | mb.Discard | mb.Cancel, mb.Save)
        if answer == mb.Discard:
            return True
        elif answer == mb.Save:
            self.saveFile()
            return True
        else:  # answer == mb.Cancel
            return False

    def noCubes(self):
        return (self.BoxList.count() == 0)

    def setDirty(self):
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        self.dirty = True
        self.actions.save.setEnabled(True)
        self.actions.undo.setEnabled(self.vtk_widget.isCubeRestorable(True))
        self.actions.redo.setEnabled(self.vtk_widget.isCubeRestorable(False))
        title = _title
        if self.fileName is not None:
            title = "{} - {}*".format(title, self.fileName)
        self.setWindowTitle(title)
        self.normalFile()

    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        title = _title
        if self.fileName is not None:
            title = "{} - {}".format(title, self.fileName)
        self.setWindowTitle(title)

    def saveFile(self):
        """
        ctrl+s 默认保存到cache
        :return:
        """
        # pdb.set_trace()
        if not self.fileName:
            return
        # TODO 另存为功能可借鉴saveFileDialog

        target_path = self.getLabelPath(self.fileName)
        self._saveFile(target_path)

    def _saveFile(self, filename=None):
        """
        当前文件标签保存起来
        :param filename: 标签路径json
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        # print(filename)
        # pdb.set_trace()

        self.endTime = time.time()
        self.labelCubes = self.vtk_widget.cubes
        self.annoInfo.cubes = self.labelCubes
        self.annoInfo.version = __version__
        self.annoInfo.updateTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.annoInfo.annoDelay = round(self.endTime - self.beginTime, 1)
        self.annoInfo.pcdPath = self.fileBaseName
        self.annoInfo.datasetName = "test pcd"

        dic_data = self.annoInfo.convertToDict()
        # print("dic_data = ", json.dumps(dic_data, indent=2))
        if not osp.exists(osp.dirname(filename)):
            os.makedirs(osp.dirname(filename))
        ret = save_json_file(filename, dic_data, indent=2)
        if not ret:
            print("保存_saveFile 出错")

        self.setClean()

    def saveAnnoInfo(self):
        """
        保存状态信息json
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        anno_state_file = self.getFileInfoPath()
        if not osp.exists(osp.dirname(anno_state_file)):
            os.makedirs(osp.dirname(anno_state_file))

        dic_data = {}
        for k, v in self.fileInfoDict.items():
            dic_data[k] = v.convertToDict()

        # print("self.fileInfoDict = ", json.dumps(dic_data, indent=2))

        ret = save_json_file(anno_state_file, dic_data, indent=2)
        if not ret:
            print("保存saveAnnoInfo 出错")

    def deleteCheck(self, filename):
        """
        删除check文件夹json文件
        :param filename: pcd文件名称
        :return:
        """
        check_path = self.getCheckLabelPath(filename)
        if osp.exists(check_path):
            os.remove(check_path)

    def getLabelPath(self, filename):
        """
        根据pcd路径获取它的标签json路径
        :param filename:
        :return:
        """
        label_dir = osp.join(self.fileDir, self.CACHE, self.LABEL_CACHE)
        label_json_name = osp.splitext(osp.basename(filename))[0] + ".json"
        label_file = osp.join(label_dir, label_json_name)
        return label_file

    def getCheckLabelPath(self, filename):
        """
        根据pcd路径获取 check 标签路径
        :param filename: pcd文件名
        :return:
        """
        label_dir = osp.join(self.fileDir, self.CACHE, self.LABEL_CHECK)
        label_json_name = osp.splitext(osp.basename(filename))[0] + ".json"
        label_file = osp.join(label_dir, label_json_name)
        return label_file

    def getFileInfoPath(self, filename=''):
        anno_state_file = osp.join(self.fileDir, self.CACHE, self.ANNO_STATE_NAME)
        return anno_state_file

    def getExportLabelFolder(self):
        """ 导出文件夹位置 csv """
        return osp.join(self.fileDir, self.OUTPUT)

    def getExportCsvPath(self, filename):
        """导出csv 路径"""
        folder = self.getExportLabelFolder()
        if not osp.exists(folder):
            os.makedirs(folder)
        label_csv_name = osp.splitext(osp.basename(filename))[0] + ".csv"
        return osp.join(folder, label_csv_name)

    def getCheckedFileList(self):
        result = []
        for k, v in self.fileInfoDict.items():
            if v.state == PcdFileInfo.CHECK:
                result.append(v.name)

        return result

    def exportCheckedLabel(self):
        """ check 的文件json导出csv """
        if self.fileName is None:
            return
        pcd_files = self.getCheckedFileList()
        for filename in pcd_files:
            check_label_file = self.getCheckLabelPath(osp.join(self.fileDir, filename))
            if osp.exists(check_label_file):
                data = read_json_file(check_label_file)
                anno_info = AnnoInfo3d()
                anno_info.getDataFromDict(data)
                csv_data = anno_info.convertToCsvData()

                save_csv_file(self.getExportCsvPath(osp.join(self.fileDir, filename)), csv_data)

    def loadTypeMap(self, classfile):
        """
        加载映射关系class.json  , 改为 读取yaml文件
        :param classfile:
        :return:
        """

        if not osp.exists(classfile):
            return
        # outputdict = read_json_file(classfile)
        # if outputdict:
        #     self._tar_type_dict.clear()
        #     self._tar_type_dict = outputdict
        #     VTK_QWidget.type_map = {v: k for k, v in self._tar_type_dict.items()}

        # global traffic_property_dic, label_csv_dic
        tmp_dic = copy.deepcopy(global_manager.traffic_property_dic)
        tmp_dic = read_yaml_file(classfile, tmp_dic)

        global_manager.traffic_property_dic = copy.deepcopy(tmp_dic)
        global_manager.add_traffic_type = None

        self.traffic_tool_view.add_buttons()
        global_manager.label_csv_dic['label']['val'] = global_manager.traffic_property_dic

        self.con_para_edit.reload_widget()

        for ew in self.con_para_edit.wid_list:
            #  ew is  EditWidget_
            ew.click_signal.connect(self.edit_para_property)

    # axiong add 20230104

    def Load_Image_Label(self):
        for i in range(len(self.picpath)):
            if self.picpath[i] is None:
                continue
            else:
                if 'pic_1' in self.picpath[i]:
                    img = cv2.imread(self.picpath[i])
                    # img = cv2.resize(img, (1980, 1080))
                    self.img['left']=img
                if 'pic_2' in self.picpath[i]:
                    img = cv2.imread(self.picpath[i])
                    # img = cv2.resize(img, (1980, 1080))
                    self.img['mid']=img
                if 'pic_3' in self.picpath[i]:
                    img = cv2.imread(self.picpath[i])
                    # img = cv2.resize(img, (1980, 1080))
                    self.img['right']=img
        self.Image_Label_Show()

    def Image_Label_Show(self):
        pcdpoints=copy.deepcopy(self.pointsData)
        config_data = Load_Image_Map_Config(self.Map_Config_path)
        csv_path = osp.join(self.fileDir, "output")
        for key ,value in self.img.items():
            Img=copy.deepcopy(value)

            if key is 'left':
                map_=Map_left(config_data[0],config_data[1],config_data[2],config_data[3])
                # map_ = Map(config_data[0], config_data[1], config_data[2], config_data[3])
                Img_count=0
            if key is 'mid':
                map_=Map_mid(config_data[4],config_data[5],config_data[6],config_data[7])
                # map_ = Map(config_data[4], config_data[5], config_data[6], config_data[7])
                Img_count = 1
            if key is 'right':
                map_=Map_right(config_data[8],config_data[9],config_data[10],config_data[11])
                # map_ = Map(config_data[8], config_data[9], config_data[10], config_data[11])
                Img_count = 2

            label_data=[]
            selectedcubes = self.vtk_widget.selectedCubes
            cubes=self.labelCubes

            if selectedcubes == []:
                for cube in cubes:
                    temp = [float(cube.cen_x),
                            float(cube.cen_y),
                            float(cube.cen_z),
                            float(cube.width),
                            float(cube.length),
                            float(cube.height),
                            float(cube.angle) * math.pi / 180.0]
                    label_data.append(temp)
                label_data = np.array(label_data)
                boxes_corners = center_to_corner_box3d_(label_data)

            else:
                for cube in selectedcubes:
                    temp = [float(cube.cen_x),
                            float(cube.cen_y),
                            float(cube.cen_z),
                            float(cube.width),
                            float(cube.length),
                            float(cube.height),
                            float(cube.angle) * math.pi / 180.0]
                    label_data.append(temp)
                label_data = np.array(label_data)
                boxes_corners = center_to_corner_box3d_(label_data)
            outimg = cv2.undistort(Img, np.array(map_.in_param), np.array(map_.dist_vec))
            for po in range(boxes_corners.shape[0]):
                label_data = boxes_corners[po]
                xyz_cam = map_.lidar_to_cam(label_data)
                filter_cam = np.where(xyz_cam[:, 2] > 0, True, False)
                label_data = np.mat(label_data)

                # 图像去畸变
                translation_repeat = np.expand_dims(map_.translation_vec, axis=1)

                translation_repeat = np.repeat(translation_repeat, label_data.shape[0], axis=1)

                pc_in_camera_coordinate = np.matmul(map_.rotate_mat, label_data.T) +translation_repeat
                uv_loc = np.array(np.matmul(map_.in_param, pc_in_camera_coordinate))

                u, v = uv_loc[0, :] / uv_loc[2, :], uv_loc[1, :] / uv_loc[2, :]

                point_draw = []
                for i in range(u.shape[0]):
                    r = np.sqrt(label_data[i, 0] ** 2 + label_data[i, 1] ** 2)
                    height = label_data[i, 2]
                    if filter_cam[i] == False:
                        continue

                    if u[i] < outimg.shape[1] and u[i] > 0 and v[i] < outimg.shape[0] and v[i] > 0:
                        cv2.circle(outimg, (int(u[i]), int(v[i])), 1, (0, 0, 255), thickness=4)
                        point_2d=np.array([u[i],v[i]])
                        point_draw.append(point_2d)

                if len(point_draw) == 8:
                    lines_box = np.array(
                        [[0, 1], [1, 2], [0, 3], [2, 3], [4, 5], [4, 7], [5, 6], [6, 7], [0, 4], [1, 5], [2, 6],
                         [3, 7]])
                    point_draw = np.array(point_draw)
                    for j in range(len(lines_box)):
                        start = (int(point_draw[lines_box[j][0]][0]), int(point_draw[lines_box[j][0]][1]))
                        end = (int(point_draw[lines_box[j][1]][0]), int(point_draw[lines_box[j][1]][1]))
                        cv2.line(outimg, start, end, (0, 255, 0), thickness=2, lineType=1)

            h, w, d = outimg.shape
            img = cv2.cvtColor(outimg, cv2.COLOR_BGR2RGB)
            img = QImage(img.data, w, h, w * d, QImage.Format_RGB888)
            pix = QPixmap.fromImage(img)

            self.imgWgtList[Img_count].no_window_fit_load_image(pix)
            self.imgWgtList[Img_count].setToolTip(str(self.picpath[Img_count]))

    # axiong add 20230209
    def Save_Current_Pic(self):
        """
        把当前标注框投影到图片，的图片输出保存
        """
        for i in range(len(self.imgWgtList)):
            pix=self.imgWgtList[i].pixmap
            if pix is not None:
                child_dir = 'save_pic_%d' % (i + 1)
                save_path = osp.join(self.fileDir,child_dir)
                if not osp.exists(save_path):
                    os.makedirs(save_path)
                csv_name=self.fileName.split('\\')[-1]
                csv_name=csv_name.replace('pcd','png')
                save_path=osp.join(save_path,csv_name)
                img=pix.toImage()
                size = img.size()
                s = img.bits().asstring(size.width() * size.height() * img.depth() // 8)  # format 0xffRRGGBB
                arr = np.fromstring(s, dtype=np.uint8).reshape((size.height(), size.width(), img.depth() // 8))
                cv2.imwrite(save_path,arr)


    # axiong add 20230131
    def Check_Label_Size(self):
        cubes=[]
        for cube in self.labelCubes:
            l=cube.length
            w=cube.width
            h=cube.height
            scale=global_manager.traffic_property_dic[cube.label]['scale']
            scale_l=Interval(scale[0]-Error_Scale,scale[0]+Error_Scale)
            scale_w=Interval(scale[1]-Error_Scale,scale[1]+Error_Scale)
            scale_h=Interval(scale[2]-Error_Scale,scale[2]+Error_Scale)
            if l in scale_l and w in scale_w and h in scale_h:
                pass
            else:
                cubes.append(cube)
        if cubes:
            self.cubeSelectionChanged(cubes)
            self.vtk_widget.selectCubes(cubes)


    # axiong add 20230316
    def Check_Label_Overlap(self):
        cubes_data=[]
        cubes=[]
        for cube in self.labelCubes:
            temp = []
            temp.append(cube.cen_x-cube.length/2)
            temp.append(cube.cen_x+cube.length/2)
            temp.append(cube.cen_y-cube.width/2)
            temp.append(cube.cen_y+cube.width/2)
            cubes_data.append(temp)
        for i in range(len(cubes_data)):
            for j in range(i+1,len(cubes_data)):
                ret=self.Check_Overlap(cubes_data[i],cubes_data[j])
                if ret:
                    cubes.append(self.labelCubes[i])
                    cubes.append(self.labelCubes[j])
                else:
                    pass
        if cubes:
            self.cubeSelectionChanged(cubes)
            self.vtk_widget.selectCubes(cubes)

    def Check_Overlap(self,cubes_data1,cubes_data2):
        cubes_data1_points = [(cubes_data1[0], cubes_data1[2]), (cubes_data1[0], cubes_data1[3]),
                              (cubes_data1[1], cubes_data1[2]), (cubes_data1[1], cubes_data1[3])]
        cubes_data2_points = [(cubes_data2[0], cubes_data2[2]), (cubes_data2[0], cubes_data2[3]),
                              (cubes_data2[1], cubes_data2[2]), (cubes_data2[1], cubes_data2[3])]

        for point in cubes_data1_points:
            point_x,point_y=point
            scale_x = Interval(cubes_data2[0], cubes_data2[1])
            scale_y = Interval(cubes_data2[2], cubes_data2[3])
            if point_x in scale_x and point_y in scale_y:
                return True
            else:
                pass

        for point in cubes_data2_points:
            point_x,point_y=point
            scale_x = Interval(cubes_data1[0], cubes_data1[1])
            scale_y = Interval(cubes_data1[2], cubes_data1[3])
            if point_x in scale_x and point_y in scale_y:
                return True
            else:
                pass

    def openClassDialog(self):
        print('openClassDialog')
        default_path = '.'
        # save_path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择json配置类别文件", default_path)
        ret = QtWidgets.QFileDialog.getOpenFileName(self, '选择', default_path, '')
        if ret[0] == "":
            return
        print(ret[0])
        path = ret[0]
        try:
            self.loadTypeMap(path)

        except Exception as e:
            print('读取目标类别json文件失败，请检查')
            msg_box = QMessageBox(QMessageBox.Warning, 'Warning', '读取目标类别yaml文件失败 ,{0}'.format(str(e)))
            msg_box.exec_()
            pass

    def currentItem(self):
        items = self.BoxList.selectedItems()
        if items:
            return items[0]
        return None

    def edit_para_property(self, data):
        """
        编辑参数属性
        :param data:(控件id， 值)
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        items = self.BoxList.selectedItems()
        if not items or len(items) == 0:
            return
        wid, val = data

        member = wid.get_user_data()  # cube成员名称

        cubes = []
        for item in items:
            cube = item.data(Qt.UserRole)
            cubes.append(cube)
            if hasattr(cube, member):
                if isinstance(label_csv_dic.get(member, {}).get('val', None), float):
                    setattr(cube, member, float(val))
                else:
                    setattr(cube, member, int(float(val)))

        self.vtk_widget.moveingCube(cubes)
        self.vtk_widget.storeCubes()


    def slot_cube_pose_adjustment(self, text, flag, fast_flag='mid'):
        """
        点击控件操作按钮的槽函数
        :param text: 点击的按钮 。包括：前后 左右 上下 90
        :param flag: -1，向后滚轮；1，向前滚轮；2，点击左键；3，点击右键
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)

        # item = self.currentItem()
        items = self.BoxList.selectedItems()
        if not items or len(items) == 0:
            return
        cubes = []
        for item in items:
            cube = item.data(Qt.UserRole)
            cubes.append(cube)
            move_delta = self.cal_move_distance(text, flag, fast_flag, direct=cube.angle)  # 计算移动量
            delta_x, delta_y, delta_z, delta_ang, delta_a, delta_b, delta_c = move_delta
            cube.length += delta_a
            cube.width += delta_b
            cube.height += delta_c

            #  右键点击情况，只变更箭头方向
            if delta_ang == -90:
                cube.length, cube.width = cube.width, cube.length

            if delta_a < 0 or delta_b < 0 or delta_c < 0:
                #  判断车辆不能无限制缩小
                if cube.length < 0.05 or \
                        cube.width < 0.05 or \
                        cube.height < 0.05:
                    cube.length -= delta_a
                    cube.width -= delta_b
                    cube.height -= delta_c
                    return

            cube.cen_x += delta_x
            cube.cen_y += delta_y
            cube.cen_z += delta_z
            cube.angle = (cube.angle + delta_ang) % 360.0

        self.vtk_widget.closeBoxWidget()
        self.vtk_widget.moveingCube(cubes)
        # TODO 标签值的改变特别频繁0606
        # self.vtk_widget.storeCubes()


    def cal_move_distance(self, text, flag, fast_flag, direct=0.0):
        """
        计算移动、拉伸距离
        :param text:  按钮上的文字
        :param flag: 1 -1 2 3 滚轮前、后、左键、右键
        :param fast_flag: 速度-灵敏度 fast mid slow
        :return:
        """
        step_dis = self.SensitivityDict['move']
        step_stretch = self.SensitivityDict['stretch']
        step_angle = self.SensitivityDict['turn']
        if fast_flag == 'fast':
            step_dis = self.SensitivityDict['move'] * 10
            step_stretch = self.SensitivityDict['stretch'] * 10
            step_angle = self.SensitivityDict['turn'] * 8
        elif fast_flag == 'slow':
            step_dis = self.SensitivityDict['move'] * 0.2
            step_stretch = self.SensitivityDict['stretch'] * 0.5
            step_angle = self.SensitivityDict['turn'] * 0.4
        elif fast_flag == 'mid':
            step_dis = self.SensitivityDict['move']
            step_stretch = self.SensitivityDict['stretch']
            step_angle = self.SensitivityDict['turn']
        else:
            pass

        #  框在前后、左右、上下、旋转方向上的移动量
        delta_x = 0.0
        delta_y = 0.0
        delta_z = 0.0
        delta_ang = 0.0
        delta_a = 0.0
        delta_b = 0.0
        delta_c = 0.0

        if text == '前后':
            if flag == 1:  # 上滚轮
                delta_x = step_dis * np.cos(np.deg2rad(direct))
                delta_y = step_dis * np.sin(np.deg2rad(direct))
            elif flag == -1:  # 下滚轮
                delta_x = -step_dis * np.cos(np.deg2rad(direct))
                delta_y = -step_dis * np.sin(np.deg2rad(direct))
            elif flag == 2:  # 左键点击
                delta_a = step_stretch
            elif flag == 3:  # 右键点击
                delta_a = -1 * step_stretch

        if text == '左右':
            if flag == 1:  # 上滚轮
                delta_x = step_dis * np.cos(np.deg2rad(direct + 90))
                delta_y = step_dis * np.sin(np.deg2rad(direct + 90))
            elif flag == -1:  # 下滚轮
                delta_x = -step_dis * np.cos(np.deg2rad(direct + 90))
                delta_y = -step_dis * np.sin(np.deg2rad(direct + 90))
            elif flag == 2:  # 左键点击
                delta_b = step_stretch
            elif flag == 3:  # 右键点击
                delta_b = -step_stretch

        if text == '上下':
            if flag == 1:  # 上滚轮
                delta_z = step_dis
            elif flag == -1:  # 下滚轮
                delta_z = -step_dis
            elif flag == 2:  # 左键点击
                delta_c = step_stretch
            elif flag == 3:  # 右键点击
                delta_c = -step_stretch

        if text == '90':
            if flag == 1:  # 上滚轮
                delta_ang = step_angle
            elif flag == -1:  # 下滚轮
                delta_ang = -step_angle
            elif flag == 2:  # 左键点击
                delta_ang = 90
            elif flag == 3:  # 右键点击，调整了箭头方向，长宽互换
                delta_ang = -90

        # 旧版用的是cm ，新版用m
        return [0.01*delta_x, 0.01*delta_y, 0.01*delta_z, delta_ang, 0.01*delta_a, 0.01*delta_b, 0.01*delta_c]

    def slot_slider_sens(self):
        """
        滑块触发槽函数，改变灵敏度
        :return:
        """
        self.SensitivityDict['move'] = self.panel_area_view.slid_move.value()
        self.SensitivityDict['stretch'] = self.panel_area_view.slid_stretch.value()

    def set_add_traffic_type(self, val):
        """
        设置要添加框的类型
        :param val:
        :return:
        """
        global_manager.add_traffic_type = val if val >= 0 else None

    def reset_add_traffic_type(self):
        """
        重置工具栏内，添加框预类别设定
        :return:
        """
        global_manager.add_traffic_type = None
        self.traffic_tool_view.clear_checked()


    def slot_togg_img_display(self, objname=''):
        """
        双击图像控件，全屏显示图像
        :param objname:
        :return:
        """
        # print('slot_togg_img_display==  ', objname)
        idx = None
        for i in range(len(self.imgWgtList)):
            if self.imgWgtList[i].objectName() == objname:
                idx = i
                break

        if idx is None:
            return

        if 0 <= idx < 4:
            if self.imgdisp_tab1 == 4:
                self.imgdisp_tab1 = 1
                for i in range(0, 4):
                    self.imgWgtList[i].parent.hide()
                self.imgWgtList[idx].parent.show()
            else:
                for i in range(0, 4):
                    self.imgWgtList[i].parent.show()
                    self.imgdisp_tab1 = 4
        else:
            if self.imgdisp_tab2 == 4:
                self.imgdisp_tab2 = 1
                for i in range(4, 8):
                    self.imgWgtList[i].parent.hide()
                self.imgWgtList[idx].parent.show()
            else:
                for i in range(4, 8):
                    self.imgWgtList[i].parent.show()
                    self.imgdisp_tab2 = 4

        self.imgWgtList[idx].setFitWindow()


    def slot_set_boundary_radio(self):
        """
        更新圆形边界半径长度
        :return:
        """
        self.vtk_widget.updateBoundary(self.spin_circle_radius.value(), True)

    def slot_update_size(self):
        """
        修改点云点大小
        :return:
        """
        size = self.spin_point_size.value()
        self.vtk_widget.updatePointSize(size)
        for i in range(len(self.vtk_viewList)):
            self.vtk_viewList[i].updatePointSize(size)
        self.view.syncViewSize()

    def sync_target_type(self):
        print('sync_target_type')
        pass

        count = self.spin_search_back_file.value()

        st = self.pcdList.index(self.fileName)

        if st == len(self.pcdList) - 1:
            return

        files = self.pcdList[(st + 1):]

        if len(files) > count:
            files = files[: count]

        # print(files)
        items = self.BoxList.selectedItems()

        if not items or len(items) == 0:
            return
        t1 = time.time()

        edit_list = []
        for item in items:
            cube = item.data(Qt.UserRole)
            _id = cube.id_num
            _label = cube.label
            edit_list.append([_id, _label])

        for file in files:
            path = self.getLabelPath(file)
            data = {}
            if osp.exists(path):
                data = read_json_file(path, def_ret=data)
                cubes = data.get("cubes", [])
                for cube in cubes:
                    for _id, _label in edit_list:
                        if cube["id_num"] == _id:
                            cube["label"] = _label

                data["cubes"] = cubes
                save_json_file(path, data)

            path = self.getCheckLabelPath(file)
            data = {}
            if osp.exists(path):
                data = read_json_file(path, def_ret=data)
                cubes = data.get("cubes", [])
                for cube in cubes:
                    for _id, _label in edit_list:
                        if cube["id_num"] == _id:
                            cube["label"] = _label

                data["cubes"] = cubes
                save_json_file(path, data)
        t2 = time.time()

        print("sync_target_type 时间={}ms".format(1000*(t2-t1)))



    def closeEvent(self, event):
        self.vtk_widget.vtkWidget.Finalize()
        for view_wid in self.vtk_viewList:
            view_wid.vtkWidget.Finalize()
        super(AppEntry, self).closeEvent(event)

        pass

    def resizeEvent(self, event):
        self.view.syncViewSize()
        super(AppEntry, self).resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(__appname__ + __version__)
    app.setWindowIcon(newIcon('wanji64'))
    win = AppEntry()
    win.show()
    sys.exit(app.exec_())