#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import asyncio
import itchat
import orm
import requests
from handlers import api_create_blog
from config import configs
from models import User, Blog, Comment, next_id

loop = asyncio.get_event_loop()
# loop.run_forever()
# user = dict(name='yoite', id='71546', image='nu', admin='1')
class FakeRequest(object):
    def __init__(self, arg):
        self.__user__ = arg

async def odst():
    await orm.create_pool(loop=loop, **configs.db)
    user = await User.find('00149407089444984770ea021e84471a20e9bd0e0f44b54000')
    default_request = FakeRequest(user)
    r = await api_create_blog(default_request, name='name', summary='summary', content='content')
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

@itchat.msg_register(itchat.content.TEXT)
def print_content(msg):
    if msg['ToUserName'] != 'filehelper': return
    defaultReply = 'I received: ' + msg['Text']
    reply = loop.run_until_complete(odst())
    print(reply)
    return reply[:50] or defaultReply
    # reply = get_response(msg['Text'], msg['ToUserName'])
    # return reply[:10] or defaultReply
    # if msg['Text'] == u'add':
        # itchat.send('unid', 'filehelper')

itchat.auto_login(hotReload=True)
itchat.run()
