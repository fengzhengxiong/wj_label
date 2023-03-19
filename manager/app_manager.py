
from manager import *

class AppManager():
    def __init__(self):
        self.__app_mode = AppMode.EDIT_MODE

    def set_app_mode(self, mode):
        self.__app_mode = mode

    def get_app_mode(self):
        return self.__app_mode

class Singleton(AppManager):
    def foo(self):
        pass

app_manager = Singleton()