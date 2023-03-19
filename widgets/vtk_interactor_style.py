# !/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSignal
from utils.vtk_util import *
from utils.pub import lst_append_once, lst_remove_once
from utils.util import cal_obb_2d, get_bound_3dbox


class InteractorStyle(vtk.vtkInteractorStyleRubberBandPick):
    """
    # 参考C++  vtkInteractorStyleRubberBandPick.h
    https://vtk.org/doc/nightly/html/vtkInteractorStyleRubberBandPick_8h_source.html
    """

    # 0 默认数据， 1: r触发框选点云 2: u 触发多选目标
    NO_PICK = 0
    PICK_POINTS = 1
    PICK_CUBES = 2

    UnitMatrix = vtk.vtkMatrix4x4()  # 单位矩阵

    def __init__(self, parent=None, brother=None):
        super(InteractorStyle, self).__init__()
        #  鼠标按键绑定
        self.AddObserver("LeftButtonPressEvent", self.left_button_press_event)
        self.AddObserver("RightButtonPressEvent", self.right_button_press_event)
        self.AddObserver("LeftButtonReleaseEvent", self.left_button_release_event)
        self.AddObserver("RightButtonReleaseEvent", self.right_button_release_event)
        #  键盘按键事件绑定
        self.AddObserver("KeyReleaseEvent", self.KeyReleaseEvent)
        self.AddObserver("KeyPressEvent", self.KeyPressEvent)
        self.AddObserver(vtk.vtkCommand.LeaveEvent, self.leave_event)
        self.AddObserver(vtk.vtkCommand.EnterEvent, self.enter_event)

        self.Parent = parent  # 主界面程序的对象
        self.brother = brother  # vtk对象

        self.ren = self.brother.renderer
        self.renWin = self.brother.window
        self.SetInteractor(self.renWin.GetInteractor())  # 这个要加，防止GetInteractor返回NoneType

        self.areaPicker = vtk.vtkAreaPicker()  # 选区域用的
        self.renWin.GetInteractor().SetPicker(self.areaPicker)
        self.areaPicker.AddObserver('StartPickEvent', self.area_start_pick)
        self.areaPicker.AddObserver('PickEvent', self.area_pick_event)
        self.areaPicker.AddObserver('EndPickEvent', self.area_end_pick)

        self.cubePicker = vtk.vtkPropPicker()  # 选择框体用的
        self.cubePicker.AddObserver('StartPickEvent', self.box_start_pick)
        self.cubePicker.AddObserver('PickEvent', self.box_pick_event)
        self.cubePicker.AddObserver('EndPickEvent', self.box_end_pick)

        self.boxWidget = self.brother.vtk_boxWidget  # 拉伸移动交互控件
        # self.boxWidget = get_box_widget(self.GetInteractor())
        self.boxwidget_attr_setup()

        # 创建一些临时变量，供回调函数使用，避免频繁申请局部变量，多线程引发数据冲突？
        self.pick_T = vtk.vtkTransform()  # 框被pick时，换算所用的矩阵
        self.move_T1 = vtk.vtkTransform()  # 当前的wid位置
        self.move_T2 = vtk.vtkTransform()  # 实时被移动，换算所用的矩阵

        # C++中含有CurrentMode变量，py中未找到 https://vtk.org/doc/nightly/html/classvtkInteractorStyleRubberBandPick.html
        self.currentmode = self.NO_PICK
        self._ctrlModify = False  # ctrl键是否按下
        self._edit_valid = False  # 调整框是否有效

        # 记录坐标 变量参照C++命名
        self.StartPosition = None
        self.EndPosition = None

        self.select_cubes=[]  # axiong add 20221209 框选多选不消除



    def boxwidget_attr_setup(self):
        """
        3D boxwidget 控件属性设置
        https://www.freesion.com/article/6280422237/#3_vtkBoxWidget__15
        :return:
        """
        self.boxWidget.AddObserver('InteractionEvent', self.boxwidget_callback)
        self.boxWidget.AddObserver('EndInteractionEvent', self.boxwidget_end_callback)
        self.boxWidget.SetInteractor(self.GetInteractor())

        if self.boxWidget.GetEnabled() > 0:
            self.boxWidget.Off()

    def left_button_press_event(self, obj, event):
        click_pos = self.GetInteractor().GetEventPosition()
        if self.currentmode == self.PICK_POINTS:
            self.StartPosition = [click_pos[0], click_pos[1]]
        else:
            self.StartPosition = None

        self.OnLeftButtonDown()

    def left_button_release_event(self, obj, event):
        click_pos = self.GetInteractor().GetEventPosition()
        if self.currentmode == self.PICK_POINTS:
            self.EndPosition = [click_pos[0], click_pos[1]]
        else:
            self.EndPosition = None
        self.OnLeftButtonUp()

    def right_button_press_event(self, obj, event):
        click_pos = self.GetInteractor().GetEventPosition()
        self.cubePicker.Pick(click_pos[0], click_pos[1], 0, self.ren)  # pick函数触发事件pick event
        picked = self.cubePicker.GetActor()
        picked2d = self.cubePicker.GetActor2D()
        if picked is None and picked2d is None:
            self.OnRightButtonDown()

    def right_button_release_event(self, obj, event):

        self.OnRightButtonUp()

    def leave_event(self, obj, event):
        # print('leave_event  ', event)
        self._ctrlModify = False
        self.OnLeave()

    def enter_event(self, obj, event):
        # print('enter_event  ', event)
        self.OnEnter()

    def box_start_pick(self, obj, event):
        """
        vtkPropPicker StartPickEvent 响应
        :param obj:
        :param event:
        :return:
        """
        # print(f'{sys._getframe().f_code.co_name}', event)
        pass

    def box_pick_event(self, obj, event):
        """
        vtkPropPicker PickEvent 响应， pick函数 如果没有拾取到actor， 这个函数应该不会被进入
        :param obj:
        :param event:
        :return:
        """
        # print(f'{sys._getframe().f_code.co_name}', event)
        pass

    def box_end_pick(self, obj, event):
        """
        vtkPropPicker EndPickEvent 响应 ,拾取到后进行处理
        :param obj:
        :param event:
        :return:
        """
        # print(f'In Fun:{sys._getframe().f_code.co_name}', event)
        picked = self.cubePicker.GetActor()
        picked2d = self.cubePicker.GetActor2D()
        self.boxWidget.SetInteractor(self.GetInteractor())  # 必须先加上这句，要不就报错提示
        self.boxWidget.Off()

        # 如果拾取到，判断其属于哪个cubelabel成员，设为选中状态
        if picked or picked2d:
            picked_cube = self.brother.findCube(picked)
            if not picked_cube:
                picked_cube = self.brother.findCube(picked2d)
                if not picked_cube:
                    # print("没有匹配到是哪个框，有错误")
                    return

            if self._ctrlModify:
                # ctrl 多选
                if picked_cube.selected:
                    self.brother.subSelectCubes([picked_cube])
                else:
                    self.brother.addSelectCubes([picked_cube])
            else:
                # 单选
                if picked_cube.selected:
                    self.boxWidget.SetProp3D(picked_cube.solidActor)
                    self.pick_T.SetMatrix(self.UnitMatrix)  # 清除
                    self.pick_T.DeepCopy(picked_cube.solidActor.GetUserTransform())
                    self.boxWidget.SetTransform(self.pick_T)
                    self.boxWidget.On()
                # self.brother.selectCubes([picked_cube])
                self.brother.addSelectCubes([picked_cube])  # 改为这个目的是支持多个目标一起移动
        else:
            if not self._ctrlModify:
                self.brother.selectCubes([])

        del picked

    def area_start_pick(self, obj, event):
        """
        vtkAreaPicker 选取事件
        """
        pass

    def area_pick_event(self, obj, event):
        """
        vtkAreaPicker 选取事件
        """
        pass

    def area_end_pick(self, obj, event):
        """
        鼠标选中区域，选择的部分生成包围框
        :param obj:
        :param event:
        :return:
        """
        if self.currentmode == self.PICK_POINTS:
            self.areaPickPoints(obj, event)
        elif self.currentmode == self.PICK_CUBES:
            self.areaPickCubes(obj, event)

            # self.KeyPressEvent(obj, event)
            # self.KeyReleaseEvent(obj, event)


    def areaPickPoints(self, obj, event):
        """
        areaPicker 触发，框选点云
        :param obj:
        :param event:
        :return:
        """
        print(self.StartPosition, self.EndPosition)

        frustum = self.areaPicker.GetFrustum()  # vtk.vtkPlanes()
        geo = vtk.vtkExtractPolyDataGeometry()
        geo.SetInputData(self.brother.vtk_polydata)
        geo.SetImplicitFunction(frustum)
        geo.Update(0)
        select_polydata = geo.GetOutput()
        nums = select_polydata.GetNumberOfPoints()
        print('pick num  =', nums)
        if nums < 3:
            return

        direct = None
        if self.StartPosition and self.EndPosition:
            direct = get_mouse_direction(self.ren, self.StartPosition, self.EndPosition)
            # print('direct = ', direct)

        selected = []
        for i in range(nums):
            selected.append(select_polydata.GetPoint(i))

        box = get_bound_3dbox(selected, direc=direct)  # 选中的点生成框体
        self.brother.addCube(box)

        ''' 下面的是将选中的点，标红，可以不用要 '''
        # TODO 下面的取消，存在不可控bug，虽不影响使用。会影响到areaPickCubes函数，导致其也会高亮显示选中的点
        # m = vtk.vtkDataSetMapper()  # 选择区域映射数据
        # a = vtk.vtkActor()  # 演员
        # m.SetInputData(geo.GetOutput())
        # # m.SetInputConnection(geo.GetOutputPort(0))
        #
        # m.ScalarVisibilityOff()
        # a.SetMapper(m)
        # a.GetProperty().SetColor(0.3, 0.8, 0.7)
        # a.GetProperty().SetRepresentationToWireframe()
        # a.GetProperty().SetPointSize(2)
        # self.ren.AddActor(a)
        # self.renWin.Render()

    def areaPickCubes(self, obj, event):
        """
        areaPicker 触发，框选目标
        :return:
        # vtkProp3DCollection * props = areaPicker->GetProp3Ds();
        # props->InitTraversal();
        # props = vtk.vtkProp3DCollection()
        # props.InitTraversal()
        # props.GetNextProp3D()
        """
        props = self.areaPicker.GetProp3Ds()
        props.InitTraversal()  # 指向第一个prop
        nums = props.GetNumberOfItems()
        print("GetNumberOfItems=", nums)
        for i in range(nums):
            prop = props.GetNextProp3D()
            picked_cube = self.brother.findCube(prop, False)
            if picked_cube:
                lst_append_once(self.select_cubes, picked_cube)
        self.brother.selectCubes(self.select_cubes)



    def boxwidget_callback(self, obj, event):
        """
        鼠标操作boxwidget回调函数
        :param obj: 当前widget对象
        :param event:
        :return:
        """
        print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        obj_trans = vtk.vtkTransform()
        obj.GetTransform(obj_trans)  # 获得box控件位姿矩阵

        current = obj.GetProp3D()  # 当前被控制的

        edit_cube = self.brother.findCube(current)
        if not edit_cube:
            print("发送错误", current)
            return

        current_trans = vtk.vtkTransform()
        if hasattr(current, 'GetUserTransform'):
            current_trans = current.GetUserTransform()

        #  当前3D框位姿矩阵
        cur_scale = current_trans.GetScale()
        cur_pos = current_trans.GetPosition()
        cur_rot = current_trans.GetOrientation()

        self._edit_valid = True
        # 缩放
        s1, s2, s3 = obj_trans.GetScale()
        s1 = max(s1, 0.3)
        s2 = max(s2, 0.3)
        s3 = max(s3, 0.3)
        scale = (s1, s2, s3)
        # 三个维度同时拉伸功能禁用，防止误触
        if (
                np.fabs(scale[0] - cur_scale[0]) > 0.01 and
                np.fabs(scale[1] - cur_scale[1]) > 0.01 and
                np.fabs(scale[2] - cur_scale[2]) > 0.01
        ):
            scale = cur_scale
            self._edit_valid = False  # 调整是无效的

        rotation = list(obj_trans.GetOrientation())
        rotation[0], rotation[1] = cur_rot[0], cur_rot[1]  # rx ry 保持不变，为0
        rotation[2] %= 360.0

        pos = list(obj_trans.GetPosition())
        # 处理平移过程中，高度不变
        if np.fabs(pos[0] - cur_pos[0]) > 0.01 or np.fabs(pos[1] - cur_pos[1]) > 0.01:
            pos[2] = cur_pos[2]

        obj_trans.SetMatrix(self.UnitMatrix)  # 清除
        obj_trans.PostMultiply()
        obj_trans.Scale(*scale)
        obj_trans.RotateZ(rotation[2])
        obj_trans.RotateY(rotation[1])
        obj_trans.RotateX(rotation[0])
        obj_trans.Translate(pos[0], pos[1], pos[2])
        obj_trans.Update()
        obj.SetTransform(obj_trans)  # 这句加不加都行

        # 如果仅仅是移动，则一起动作，否则仅自己动
        if (
                np.fabs(scale[0] - cur_scale[0]) < 0.01 and
                np.fabs(scale[1] - cur_scale[1]) < 0.01 and
                np.fabs(scale[2] - cur_scale[2]) < 0.01 and
                np.fabs(rotation[2] - cur_rot[2] % 360.0 < 0.01)
        ):
            # print('==================')
            delta_pos = np.array(pos) - np.array(cur_pos)
            self.brother.moveSelectedCube(delta_pos)

        else:
            # print('++++++++++++++++++')
            edit_cube.setCenterPos(pos)
            edit_cube.setScale(scale)
            edit_cube.setRotate(rotation)
            self.brother.moveingCube([edit_cube])

        del obj_trans

    def boxwidget_end_callback(self, obj, event):
        """
        鼠标操作boxwidget回调函数,操作结束时触发，可以做backup使用
        :param obj:
        :param event:
        :return:
        """
        # print('行:', sys._getframe().f_lineno, ' ', sys._getframe().f_code.co_name)
        if self._edit_valid:
            self.brother.endEditCube()
            self._edit_valid = False

    def KeyReleaseEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        print('releaseevent-key: ',key)
        if key == 'Control_L':
            self._ctrlModify = False

        self.OnKeyRelease()  # self.OnKeyUp()


    def KeyPressEvent(self, obj, event):
        """
        键盘按键事件
        :param obj:
        :param event:
        :return:
        """
        '''
        r: 默认r按下触发选取
        u: 按下u键，触发r键按下功能，areapicker触发
        '''

        key = self.GetInteractor().GetKeySym()
        print('pressevent-key:', key)
        accept_flag = True  # 是否键盘事件推送

        if key == 'r':
            if self.currentmode == self.NO_PICK:
                self.currentmode = self.PICK_POINTS
                self.renWin.SetCurrentCursor(vtk.VTK_CURSOR_CROSSHAIR)
            else:
                self.currentmode = self.NO_PICK
                self.renWin.SetCurrentCursor(vtk.VTK_CURSOR_DEFAULT)

        elif key == 'u':
            self.select_cubes.clear()
            self.GetInteractor().SetKeyCode('r')
            if self.currentmode == self.NO_PICK:
                self.currentmode = self.PICK_CUBES
                self.renWin.SetCurrentCursor(vtk.VTK_CURSOR_SIZENW)
            else:
                self.currentmode = self.NO_PICK
                self.renWin.SetCurrentCursor(vtk.VTK_CURSOR_DEFAULT)
            print('pressevent-key-u: ',self.GetInteractor().GetKeySym())

        elif key == 'Control_L':
            self._ctrlModify = True

        # if self.currentmode == 0:
        #     self.areaPicker.InitializePickList()

        if accept_flag:
            self.OnKeyPress()  # self.OnKeyDown()

