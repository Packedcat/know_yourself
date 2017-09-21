#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
import json
import logging
import hashlib
import base64
import asyncio
from utils import next_id
from config import configs
from aiohttp import web
from coreweb import get, post
from models import User, Record, Tags, Relationship
from apis import Page, APIError, APIValueError, APIPermissionError

COOKIE_NAME = 'know_yourself'

_COOKIE_KEY = configs.session.secret

_RE_EMAIL = re.compile(
    r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')

_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


def check_admin(request):
    if request.__user__ is None:
        raise APIPermissionError()


def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p


def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    build cookie string by: id-expires-sha1
    '''
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None


@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r


@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', '邮箱不存在')
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', '密码错误')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(
        user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(
        id=uid,
        name=name.strip(),
        email=email,
        passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
        image='/static/img/user.png'
    )
    await user.save()
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(
        user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/api/user')
async def api_get_user(request):
    user = request.__user__
    return dict(user=user)


@get('/api/users')
async def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderBy='created_at desc',
                               limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)


@get('/api/tags')
async def api_get_tags(request):
    check_admin(request)
    tags = await Tags.findAll('user_id=?', [request.__user__.id])
    return dict(tags=tags)


@post('/api/tags')
async def api_create_tags(request, *, tag):
    check_admin(request)
    if not tag or not tag.strip():
        raise APIValueError('tag', 'tag cannot be empty.')
    tag = Tags(user_id=request.__user__.id, tag=tag.strip())
    await tag.save()
    return tag


@post('/api/tags/update')
async def api_update_tags(request, *, id, tag):
    check_admin(request)
    t = await Tags.find(id)
    if not id or not id.strip():
        raise APIValueError('id', 'id cannot be empty.')
    if not tag or not tag.strip():
        raise APIValueError('tag', 'tag cannot be empty.')
    t.tag = tag.strip()
    await t.update()
    return t


@post('/api/tags/delete')
async def api_delete_tags(request, *, id):
    check_admin(request)
    tag = await Tags.find(id)
    await tag.remove()
    return dict(id=id)


@post('/api/tags/link')
async def api_link_tag(request, *, record_id, tag_ids):
    check_admin(request)
    if not record_id or not record_id.strip():
        raise APIValueError('record_id', 'record_id cannot be empty.')
    rl = await Relationship.findAll('record_id=?', [record_id])
    for r in rl:
        print(r)
        await r.remove()
    if not tag_ids:
        return dict(links=[])
    idList = tag_ids.split(',')
    links = []
    for tag_id in idList:
        tag = await Tags.find(tag_id)
        link = Relationship(tag=tag.tag, tag_id=tag_id.strip(),
                            record_id=record_id.strip())
        await link.save()
        links.append(link)
    return dict(links=links)


@get('/api/record')
async def api_get_record(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'trash=? and archive=? and user_id=?',
        [False, False, id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@get('/api/record/bytag')
async def api_record_bytag(request, *, tag_id):
    check_admin(request)
    if not tag_id or not tag_id.strip():
        raise APIValueError('tag_id', 'tag_id cannot be empty.')
    record = []
    relation = await Relationship.findAll('tag_id=?', [tag_id])
    for r in relation:
        rc = await Record.find(r.record_id)
        record.append(rc)
    l = []
    result = []
    for d in record:
        if d.id not in l:
            result.append(d)
        l.append(d.id)
    for r in result:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(record=result)


@get('/api/text')
async def api_get_text(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Text'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'genres=? and user_id=?',
        ['Text', id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@get('/api/sharing')
async def api_get_link(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Sharing'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'genres=? and user_id=?',
        ['Sharing', id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@get('/api/picture')
async def api_get_image(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Picture'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'genres=? and user_id=?',
        ['Picture', id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@get('/api/recording')
async def api_get_audio(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Recording'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'genres=? and user_id=?',
        ['Recording', id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@get('/api/attachment')
async def api_get_file(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Attachment'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'genres=? and user_id=?',
        ['Attachment', id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@post('/api/record')
async def api_create_record(request, *, content, title='自分', genres='Text'):
    check_admin(request)
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    record = Record(user_id=request.__user__.id, title=title.strip(),
                    genres=genres.strip(), content=content.strip())
    await record.save()
    return record


@post('/api/record/update')
async def api_update_blog(request, *, id, content, title=None):
    check_admin(request)
    record = await Record.find(id)
    if content:
        record.content = content.strip()
    if title:
        record.title = title.strip()
    await record.update()
    return record


@get('/api/archive')
async def api_get_archive(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber(
        'count(id)',
        'archive=? and trash=?',
        [True, False]
    )
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'archive=? and trash=? and user_id=?',
        [True, False, id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@get('/api/trash')
async def api_get_trash(request, *, page='1'):
    check_admin(request)
    id = request.__user__.id
    page_index = get_page_index(page)
    num = await Record.findNumber(
        'count(id)',
        'trash=? and archive=?',
        [True, False]
    )
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(
        'trash=? and archive=? and user_id=?',
        [True, False, id],
        orderBy='created_at desc',
        limit=(p.offset, p.limit)
    )
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)


@post('/api/record/archive')
async def api_archive_record(request, *, id):
    check_admin(request)
    record = await Record.find(id)
    record.archive = not record.archive
    await record.update()
    return record


@post('/api/record/trash')
async def api_delete_record(request, *, id):
    check_admin(request)
    record = await Record.find(id)
    record.trash = not record.trash
    await record.update()
    return record


@post('/api/record/remove')
async def api_remove_record(request, *, id):
    check_admin(request)
    record = await Record.find(id)
    await record.remove()
    return dict(id=id)
