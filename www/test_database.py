#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import asyncio

import orm
from models import User, Record, Tags
from handlers import api_create_record, api_get_tags

loop = asyncio.get_event_loop()

# fakeData
class FakeRequest(object):
    def __init__(self, arg):
        self.__user__ = arg

# 插入
async def insert():
    await orm.create_pool(loop,user='yoite', password='71546', db='test')
    u = User(name='test', email='test@example.com', passwd='1234567890', image='about:blank')
    await u.save()
    r = await User.findAll()
    print('kc data\n',r)
    await orm.destory_pool()

# 删除
async def remove():
    await orm.create_pool(loop, user='yoite', password='71546', db='awesome')
    # r = await User.find('001492757565916ec72f6eeb731405ab07ee37911a3ae79000')
    await r.remove()
    print('remove\n',r)
    await orm.destory_pool()

# 更新
async def update():
    await orm.create_pool(loop, user='yoite', password='71546', db='awesome')
    # r = await User.find('00149276202953187d8d3176f894f1fa82d9caa7d36775a000')
    r.passwd = '765'
    await r.update()
    print('update\n',r)
    await orm.destory_pool()

# 查找
async def find():
    await orm.create_pool(loop, user='yoite', password='71546', db='awesome')
    # all = await User.findAll()
    # print(all)
    # pk = await User.find('00149276202953187d8d3176f894f1fa82d9caa7d36775a000')
    # print(pk)
    num = await User.findNumber('email')
    print(num)
    await orm.destory_pool()

# API测试
async def testAPI():
    await orm.create_pool(loop, user='yoite', password='71546', db='awesome')
    user = await User.find('0015060907967599013c99ccea04eb0b33b4348c45c4702000')
    default_request = FakeRequest(user)
    r = await api_create_record(default_request, content='content')
    return str(r)

reply = loop.run_until_complete(testAPI())
print(reply)
loop.close()
