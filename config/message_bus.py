# -*- coding: utf-8 -*-
import queue
import threading
from threading import Lock
from PyQt5.QtCore import *

##################

# 消息分发总线模块，使用到Qt的QEvent机制
class MessageBus(QObject):
    def __init__(self):
        super(MessageBus, self).__init__()
        self.__subscriptions = {}
        self.__event_queue = queue.Queue()
        self.__message_queue = queue.Queue()
        self.__thread_running = False
        self.__mutex = Lock()
        
    def subscribe(self, subject, owner, func):
        self.__mutex.acquire()
        if owner not in self.__subscriptions:
            self.__subscriptions[owner] = {}
        self.__subscriptions[owner][subject] = func
        self.__mutex.release()
    
    def unsubscribe(self, subject, owner, func):
        self.__mutex.acquire()
        if self.__has_subscription(owner,subject):
            self.__subscriptions[owner].pop(subject)
        self.__mutex.release()
        
    def __publish(self, subject, *args, **kwargs):
        self.__mutex.acquire()
        for owner in list(self.__subscriptions.keys()):
            if self.__has_subscription(owner, subject):
                self.__subscriptions[owner][subject](*args, **kwargs)
        self.__mutex.release()

    def start(self):
        """
        start a thread to check message existed in 
        """
        self.__thread_running = True
        cmd_thread = threading.Thread(target=self.__event_handle_thread)
        cmd_thread.setDaemon(True)
        cmd_thread.start()
    
    def stop(self):
        self.__thread_running = False

    def post(self, message):
        self.__event_queue.put(message)
    
    def __has_subscription(self, owner, subject):
        return owner in self.__subscriptions  and subject in self.__subscriptions[owner]

    def __event_handle_thread(self):
        """
        handler the mssage from other module
        """
        while self.__thread_running:
            #采用阻塞方式，超时时间为5s
            cmd = None
            try:
                cmd = self.__event_queue.get(True, 5)
            except:
                continue
            if cmd == None:
                continue
            self.__message_queue.put(cmd)
            # postEvent是异步方法，所以需要将当前的消息进行队列管理
            # 1000是用户自定义的的QCoreApplication.postEvent
            # 在事件生成时会自动调用customEvent函数
            QCoreApplication.postEvent(self, QEvent(1000))

    def customEvent(self, e):
        message = self.__message_queue.get(True)
        if message:
            self.__publish(message['key'], message)
        

class Singleton(MessageBus):
    def foo(self):
        pass

bus_handler = Singleton()
