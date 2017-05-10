#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, time, json, logging, hashlib, base64, asyncio
import markdown2

from aiohttp import web

from config import configs
from coreweb import get, post
from models import User, Blog, Comment, Record, Tags, Relationship, next_id
from apis import Page, APIError, APIValueError, APIResourceNotFoundError

# cookie键值
COOKIE_NAME = 'awesession'
# 加密盐值
_COOKIE_KEY = configs.session.secret
# 邮箱检验正则式
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
# 密码检验正则式
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

# 检查登录
def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

# 文本转换
def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

# 转成int
def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

# 用户对象计算cookie
def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

# 在cookie中获取uid, expires, sha1
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
        # 通过uid查找用户对象
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

@get('/')
async def index(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    page = Page(num)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs
    }

@get('/blog/{id}')
async def get_blog(id):
    blog = await Blog.find(id)
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }

@get('/manage')
def manage():
    return 'redirect:/manage/comments'

@get('/manage/comments')
def manage_comments(*, page='1'):
    return {
        '__template__': 'manage_comments.html',
        'page_index': get_page_index(page)
    }

@get('/manage/blogs')
def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }

@get('/manage/blogs/create')
def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }

@get('/manage/blogs/edit')
def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % id
    }

@get('/manage/users')
def manage_users(*, page='1'):
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }

@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }

@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

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
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
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
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@get('/api/users')
async def api_get_users(*, page='1'):
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)

@get('/api/comments')
async def api_comments(*, page='1'):
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)

@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, content):
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name, user_image=user.image, content=content.strip())
    await comment.save()
    return comment

@post('/api/comments/{id}/delete')
async def api_delete_comments(id, request):
    check_admin(request)
    c = await Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    await c.remove()
    return dict(id=id)

@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

@get('/api/blogs/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id)
    return blog

@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog

@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content):
    check_admin(request)
    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog

@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)
    blog = await Blog.find(id)
    await blog.remove()
    return dict(id=id)

# Record part

# 获取标签
@get('/api/tags')
async def api_get_tags(request):
    check_admin(request)
    tags = await Tags.findAll('user_id=?', [request.__user__.id])
    return dict(tags=tags)

# 创建标签
@post('/api/tags')
async def api_create_tags(request, *, tag):
    check_admin(request)
    if not tag or not tag.strip():
        raise APIValueError('tag', 'tag cannot be empty.')
    tag = Tags(user_id=request.__user__.id, tag=tag.strip())
    await tag.save()
    return tag

# 更新标签
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

# 删除标签
@post('/api/tags/delete')
async def api_delete_tags(request, *, id):
    check_admin(request)
    tag = await Tags.find(id)
    await tag.remove()
    return dict(id=id)

# 链接标签
@post('/api/tags/link')
async def api_link_tag(request, * , tag_ids, record_id):
    if not tag_ids or not tag_ids.strip():
        raise APIValueError('tag_ids', 'tag_ids cannot be empty.')
    if not record_id or not record_id.strip():
        raise APIValueError('record_id', 'record_id cannot be empty.')
    idList = tag_ids.split(',')
    links = []
    for tag_id in idList:
        tag = await Tags.find(tag_id)
        link = Relationship(tag=tag.tag, tag_id=tag_id.strip(), record_id=record_id.strip())
        await link.save()
        links.append(link)
    return dict(links=links)

# 获取记事
@get('/api/record')
async def api_get_record(*, page='1'):
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        # 去重
        r.tags = tags
    return dict(page=p, record=record)

@get('/api/record/bytag')
async def api_record_bytag(*, tag_id):
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

# 获取文字
@get('/api/text')
async def api_get_text(*, page='1'):
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Text'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll('genres=?', ['Text'], orderBy='created_at desc', limit=(p.offset, p.limit))
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)

# 获取链接
@get('/api/sharing')
async def api_get_link(*, page='1'):
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Sharing'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll('genres=?', ['Sharing'], orderBy='created_at desc', limit=(p.offset, p.limit))
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)

# 获取图片
@get('/api/picture')
async def api_get_image(*, page='1'):
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Picture'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll('genres=?', ['Picture'], orderBy='created_at desc', limit=(p.offset, p.limit))
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)

# 获取音频
@get('/api/recording')
async def api_get_audio(*, page='1'):
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Recording'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll('genres=?', ['Recording'], orderBy='created_at desc', limit=(p.offset, p.limit))
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)

# 获取文件
@get('/api/attachment')
async def api_get_file(*, page='1'):
    page_index = get_page_index(page)
    num = await Record.findNumber('count(id)', 'genres=?', ['Attachment'])
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, record=())
    record = await Record.findAll('genres=?', ['Attachment'], orderBy='created_at desc', limit=(p.offset, p.limit))
    for r in record:
        tags = await Relationship.findAll('record_id=?', [r.id])
        r.tags = tags
    return dict(page=p, record=record)

# 创建记事
@post('/api/record')
async def api_create_record(request, *, content, title='自分', genres='Text'):
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    record = Record(user_id=request.__user__.id, title=title.strip(), genres=genres.strip(), content=content.strip())
    await record.save()
    return record

# 更新记事
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

# 记事归档
@post('/api/record/archive')
async def api_archive_record(request, *, id):
    check_admin(request)
    record = await Record.find(id)
    record.archive = 1
    await record.update()
    return record

# 记事删除
@post('/api/record/trash')
async def api_delete_record(request, *, id):
    check_admin(request)
    record = await Record.find(id)
    record.trash = 1
    await record.update()
    return record

# 记事移除
@post('/api/record/remove')
async def api_remove_record(request, *, id):
    check_admin(request)
    record = await Record.find(id)
    await record.remove()
    return dict(id=id)
