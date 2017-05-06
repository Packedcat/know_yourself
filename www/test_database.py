#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import asyncio

import orm
from models import User

loop = asyncio.get_event_loop()

# 插入
async def insert():
    await orm.create_pool(loop,user='yoite', password='71546', db='awesome')
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

loop.run_until_complete(insert())
loop.close()
