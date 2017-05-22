#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import time, _thread

import itchat
from itchat.content import *

itchat.auto_login(hotReload=True)

replyToGroupChat = True
functionStatus = False

def change_function():
    global replyToGroupChat
    global functionStatus
    if replyToGroupChat != functionStatus:
        if replyToGroupChat:
            @itchat.msg_register(TEXT, isGroupChat = True)
            def group_text_reply(msg):
                if u'关闭' in msg['Text']:
                    replyToGroupChat = False
                    return u'已关闭'
                elif u'开启' in msg['Text']:
                    return u'已经在运行'
                return u'输入"关闭"或者"开启"测试功能'
        else:
            @itchat.msg_register(TEXT, isGroupChat = True)
            def group_text_reply(msg):
                if u'开启' in msg['Text']:
                    replyToGroupChat = True
                    return u'重新开启成功'
        functionStatus = replyToGroupChat

_thread.start_new_thread(itchat.run, ())

while 1:
    change_function()
    time.sleep(.1)
