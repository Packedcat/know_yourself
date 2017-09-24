#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import asyncio
import itchat
import orm
import requests
import hashlib
import json

from itchat.content import *
from handlers import api_create_record, authenticate
from config import configs
from models import User, next_id
from apis import APIValueError

# 获取事件循环
loop = asyncio.get_event_loop()

# 帮助信息
HELP_MSG = u'''\
暂未绑定账号
请输入邮箱密码
中间用分号隔开
'''

# 登录用户
USER_MAP = {}

# 伪造中间件添加的user信息
class FakeRequest(object):
    def __init__(self, arg):
        self.__user__ = arg

# 登录绑定
async def login(email, passwd, user_key):
    global USER_MAP
    await orm.create_pool(loop=loop, **configs.db)
    s = '%s:%s' % (email, passwd)
    sha1 = hashlib.sha1(s.encode('utf-8'))
    try:
        response = await authenticate(email=email, passwd=sha1.hexdigest())
        user = json.loads(response.body.decode('utf-8'))
        if user_key in USER_MAP:
            USER_MAP[user_key] = None
            del USER_MAP[user_key]
        USER_MAP[user_key] = user
        return ('success', user['name'])
    except APIValueError as e:
        return (e.data, e.message)

# 创建记事
async def create(content, title, genres, user_key):
    user = USER_MAP.get(user_key)
    if user == None:
        return
    await orm.create_pool(loop=loop, **configs.db)
    user = await User.find(user['id'])
    default_request = FakeRequest(user)
    r = await api_create_record(default_request, content=content,
        title=title, genres=genres)
    return str(r)

# 注册下载资源方法
@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files(msg):
    if msg['User']['RemarkName'] == 'bypass':
        return
    user_key = msg['FromUserName']
    if user_key not in USER_MAP:
        itchat.send(HELP_MSG, msg['FromUserName'])
        return
    path = './static/%s/%s' % (msg['Type'].lower(), msg['FileName'])
    result = msg['Text'](path)
    content = path[1:]
    genres = msg['Type']
    title = msg['FileName']
    r = loop.run_until_complete(create(content, title, genres, user_key))
    itchat.send('%s received\nPath: %s' % (msg['Type'], content), msg['FromUserName'])

# 注册信息与分享方法
@itchat.msg_register([TEXT, SHARING])
def text_reply(msg):
    if msg['User']['RemarkName'] == 'bypass':
        return
    user_key = msg['FromUserName']
    if user_key not in USER_MAP:
        auth = msg['Text'].split(';')
        if len(auth) < 2:
            itchat.send(HELP_MSG, msg['FromUserName'])
        else:
            email, passwd = auth[:2]
            status, message = loop.run_until_complete(
                login(email, passwd, user_key))
            itchat.send(u'%s: %s' % (status, message), msg['FromUserName'])
    else:
        genres = msg['Type']
        title = u'文字备忘'
        content = msg['Text']
        if msg['Type'] == SHARING:
            title = msg['Text']
            content = msg['Url']
        r = loop.run_until_complete(create(content, title, genres, user_key))
        itchat.send('%s: %s' % (msg['Type'], content), msg['FromUserName'])

itchat.auto_login(hotReload=True, enableCmdQR=2)
itchat.run()
