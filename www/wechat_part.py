#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import asyncio
import itchat
import orm
import requests

from itchat.content import *
from handlers import api_create_blog, api_create_record
from config import configs
from models import User, Blog, Comment, next_id

loop = asyncio.get_event_loop()

class FakeRequest(object):
    def __init__(self, arg):
        self.__user__ = arg

async def odst(content, title, genres):
    await orm.create_pool(loop=loop, **configs.db)

    user = await User.find('00149407089444984770ea021e84471a20e9bd0e0f44b54000')
    print(user)
    default_request = FakeRequest(user)
    r = await api_create_record(default_request, content=content, title=title, genres=genres)
    return str(r)

def get_response(msg, user):
    apiUrl = 'http://127.0.0.1:9000/api/blogs'
    payload = {
        'name': user,
        'summary': msg,
        'content': msg,
    }
    try:
        r = requests.post(apiUrl, data=payload).json()
        print(r)
        return str(r)
    except:
        return

# send方法
# itchat.send('Hello world!', toUserName)
# itchat.send('@img@%s' % 'path', toUserName)
# itchat.send('@fil@%s' % 'path', toUserName)
# itchat.send('@vid@%s' % 'path', toUserName)
@itchat.msg_register([PICTURE, RECORDING, ATTACHMENT, VIDEO])
def download_files(msg):
    # if msg['ToUserName'] != 'filehelper': return
    path = './static/%s/%s' % (msg['Type'].lower(), msg['FileName'])
    result = msg['Text'](path)
    content = path[1:]
    genres = msg['Type']
    title = msg['FileName']
    r = loop.run_until_complete(odst(content, title, genres))
    print(r)
    itchat.send('%s received\nPath: %s' % (msg['Type'], content), 'filehelper')

@itchat.msg_register([TEXT, SHARING])
def text_reply(msg):
    # if msg['ToUserName'] != 'filehelper': return
    print(msg)
    genres = msg['Type']
    title = msg['ToUserName']
    content = msg['Text']
    if msg['Type'] == SHARING:
        title = msg['Text']
        content = msg['Url']
    r = loop.run_until_complete(odst(content, title, genres))
    print(r)
    itchat.send('%s: %s' % (msg['Type'], content), 'filehelper')

# @itchat.msg_register(itchat.content.TEXT)
# def print_content(msg):
#     if msg['ToUserName'] != 'filehelper': return
#     defaultReply = 'I received: ' + msg['Text']
#     reply = loop.run_until_complete(odst())
#     reply = get_response(msg['Text'], msg['ToUserName'])
#     print(reply)
#     return reply[:50] or defaultReply

itchat.auto_login(hotReload=True)
itchat.run()
