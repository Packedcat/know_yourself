#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
import time
import datetime
import functools


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


def log(prefix='call'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            print('%s begin: %s' % (prefix, func.__name__))
            func(*args, **kw)
            print('%s end: %s' % (prefix, func.__name__))
            return
        return wrapper
    return decorator
