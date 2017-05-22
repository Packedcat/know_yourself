#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import asyncio
import itchat
import orm
import requests
import wikipedia
import hashlib
import json

from itchat.content import *
from handlers import api_create_blog, api_create_record, authenticate
from config import configs
from models import User, Blog, Comment, next_id

# 获取事件循环
loop = asyncio.get_event_loop()

# 设置搜索语言
wikipedia.set_lang('jp')

# 帮助信息
HELP_MSG = u'''
使用以下命令搜寻关键词
search@"placeholder"
使用以下命令开启页面
open@"placeholder"
'''

# 登录用户
USER = None

# 伪造中间件添加的user信息
class FakeRequest(object):
    def __init__(self, arg):
        self.__user__ = arg

# 登录绑定
async def login(email, passwd):
    global USER
    await orm.create_pool(loop=loop, **configs.db)
    s = '%s:%s' % (email, passwd)
    sha1 = hashlib.sha1(s.encode('utf-8'))
    response = await authenticate(email=email, passwd=sha1.hexdigest())
    USER = json.loads(response.body.decode('utf-8'))

# 创建记事
async def create(content, title, genres):
    await orm.create_pool(loop=loop, **configs.db)
    user = await User.find(USER['id'])
    default_request = FakeRequest(user)
    r = await api_create_record(default_request, content=content, title=title, genres=genres)
    return str(r)

# 直接发起请求调用API
def get_response(msg, user):
    apiUrl = 'http://127.0.0.1:9000/api/blogs'
    payload = {
        'name': user,
        'summary': msg,
        'content': msg,
    }
    try:
        r = requests.post(apiUrl, data=payload).json()
        return str(r)
    except:
        return

# 注册下载资源方法
@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files(msg):
    if msg['ToUserName'] != 'filehelper': return
    path = './static/%s/%s' % (msg['Type'].lower(), msg['FileName'])
    result = msg['Text'](path)
    content = path[1:]
    genres = msg['Type']
    title = msg['FileName']
    r = loop.run_until_complete(create(content, title, genres))
    itchat.send('%s received\nPath: %s' % (msg['Type'], content), 'filehelper')

# @itchat.msg_register([TEXT, SHARING])
# def text_reply(msg):
#     # if msg['ToUserName'] != 'filehelper': return
#     l = msg['Text'].split('@')
#     if l[0] == 'search':
#         r = wikipedia.search(l[1], results=5)
#         if len(r) == 0:
#             itchat.send('无查询结果', 'filehelper')
#         else:
#             itchat.send('是不是在找这些\n%s' % '\n'.join(r), 'filehelper')
#     elif l[0] == 'open':
#         page = wikipedia.page(l[1].encode('utf-8'))
#         itchat.send('%s\n%s' % (page.content, page.url), 'filehelper')
#     else:
#         genres = msg['Type']
#         title = msg['ToUserName']
#         content = msg['Text']
#         if msg['Type'] == SHARING:
#             title = msg['Text']
#             content = msg['Url']
#         r = loop.run_until_complete(odst(content, title, genres))
#         itchat.send('%s: %s' % (msg['Type'], content), 'filehelper')

@itchat.msg_register(TEXT)
def text_reply(msg):
    if msg['ToUserName'] != 'filehelper': return
    auth = msg['Text'].split(';')
    if len(auth) != 2:
        itchat.send('请输入邮箱密码，中间用分号隔开', 'filehelper')
    else:
        email, passwd = auth
    loop.run_until_complete(login(email, passwd))
    itchat.send('ようこそ：%s' % USER['name'], 'filehelper')

itchat.auto_login(hotReload=True)
itchat.run()

# send方法
# itchat.send('Hello world!', toUserName)
# itchat.send('@img@%s' % 'path', toUserName)
# itchat.send('@fil@%s' % 'path', toUserName)
# itchat.send('@vid@%s' % 'path', toUserName)
