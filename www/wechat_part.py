#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import asyncio
import itchat
import orm
import requests
from handlers import api_create_blog
from config import configs

# loop = asyncio.get_event_loop()
# loop.run_until_complete(init(loop))
# loop.run_forever()

# default_request = {'__user__': {'name': 'yoite', 'id': '71546', 'image': 'nu'}}

# async def odst():
    # await orm.create_pool(loop=loop, **configs.db)
    # r = api_create_blog(default_request, name='name', summary='summary', content='content')

def get_response(msg, user):
    apiUrl = 'http://127.0.0.1:9000/api/users'
    # data = {
    #     'name': user,
    #     'summary': msg,
    #     'content': msg,
    # }
    try:
        r = requests.get(apiUrl).json()
        print(r)
        return str(r)
    except:
        return

@itchat.msg_register(itchat.content.TEXT)
def print_content(msg):
    if msg['ToUserName'] != 'filehelper': return
    defaultReply = 'I received: ' + msg['Text']
    reply = get_response(msg['Text'], msg['ToUserName'])
    return reply[:10] or defaultReply
    # if msg['Text'] == u'add':
        # itchat.send('unid', 'filehelper')

itchat.auto_login()
itchat.run()
