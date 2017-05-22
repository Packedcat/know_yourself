#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, platform
import requests, time, re, subprocess
import json, xml.dom.minidom

# 基础URL
BASE_URL = 'https://login.weixin.qq.com'
OS = platform.system()
INTERACT_URL = None

session = requests.Session()
uuid = None
baseRequest = {}

# 获取QRcode的uuid
def get_QRuuid():
    # 格式化url
    url = '%s/jslogin'%BASE_URL
    # 请求参数为固定值
    params = {
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
    }
    r = session.get(url, params = params)
    # 使用正则提取返回结果中的QRcode的uuid
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)";'
    data = re.search(regx, r.text)
    # 请求成功且获取得到uuid返回
    if data and data.group(1) == '200': return data.group(2)

def get_QR():
    # 格式化获取QRcode的url
    url = '%s/qrcode/%s'%(BASE_URL, uuid)
    # 以二进制数据流的形式获取服务器返回的数据包
    r = session.get(url, stream = True)
    # 保存图片
    with open('QR.jpg', 'wb') as f: f.write(r.content)
    # 判断系统使用命令打开图片
    if OS == 'Darwin':
        subprocess.call(['open', 'QR.jpg'])
    elif OS == 'Linux':
        subprocess.call(['xdg-open', 'QR.jpg'])
    else:
        os.startfile('QR.jpg')

def check_login(uuid):
    # 格式化检查登录状态的url
    url = '%s/cgi-bin/mmwebwx-bin/login'%BASE_URL
    # 提交uuid与时间的载荷
    payloads = 'tip=1&uuid=%s&_=%s'%(uuid, int(time.time()))
    r = session.get(url, params = payloads)
    # 获取请求返回的状态码
    regx = r'window.code=(\d+)'
    data = re.search(regx, r.text)
    if not data: return False

    def one_line_print(msg):
        sys.stdout.write('%s\r'%msg)
        sys.stdout.flush()
    if data.group(1) == '200':
        # 若登录成功则匹配重定向的地址
        regx = r'window.redirect_uri="(\S+)";'
        global INTERACT_URL
        INTERACT_URL = re.search(regx, r.text).group(1)
        r = session.get(INTERACT_URL, allow_redirects=False)
        # 获取重定向URL的域名用以后续接口调用
        INTERACT_URL = INTERACT_URL[:INTERACT_URL.rfind('/')]
        # 获取登录信息
        get_login_info(r.text)
        return True
    elif data.group(1) == '201':
        one_line_print('Please press confirm')
    elif data.group(1) == '408':
        one_line_print('Please reload QR Code')
    return False

def get_login_info(s):
    global baseRequest
    for node in xml.dom.minidom.parseString(s).documentElement.childNodes:
        if node.nodeName == 'skey':
            baseRequest['Skey'] = node.childNodes[0].data.encode('utf8')
        elif node.nodeName == 'wxsid':
            baseRequest['Sid'] = node.childNodes[0].data.encode('utf8')
        elif node.nodeName == 'wxuin':
            baseRequest['Uin'] = node.childNodes[0].data.encode('utf8')
        elif node.nodeName == 'pass_ticket':
            baseRequest['DeviceID'] = node.childNodes[0].data.encode('utf8')

def web_init():
    url = '%s/webwxinit?r=%s' % (INTERACT_URL, int(time.time()))
    # 登录信息的载荷
    payloads = {
        'BaseRequest': baseRequest,
    }
    # 改变请求头信息
    headers = { 'ContentType': 'application/json; charset=UTF-8' }
    r = session.post(url, data = json.dumps(payloads), headers = headers)
    dic = json.loads(r.content.decode('utf-8', 'replace'))
    return dic['User']['UserName']

def send_msg(toUserName = None, msg = 'Test Message'):
    url = '%s/webwxsendmsg'%INTERACT_URL
    # baseRequest为用户与登录信息对象
    # Msg为发送信息对象
    payloads = {
            'BaseRequest': baseRequest,
            'Msg': {
                'Type': 1,
                'Content': msg.encode('utf8') if isinstance(msg, unicode) else msg,
                'FromUserName': myUserName.encode('utf8'),
                'ToUserName': (toUserName if toUserName else myUserName).encode('utf8'),
                'LocalID': int(time.time()),
                'ClientMsgId': int(time.time()),
                },
            }
    headers = { 'ContentType': 'application/json; charset=UTF-8' }
    session.post(url, data = json.dumps(payloads, ensure_ascii = False), headers = headers)

if __name__ == '__main__':
    while uuid is None: uuid = get_QRuuid()
    get_QR()
    print 'QR is shown'
    while not check_login(uuid): pass
    myUserName = web_init()
    print 'Login successfully you can send messages now, input q to exit'
    msg = None
    while msg != 'q':
        if msg: send_msg(myUserName, msg)
        msg = raw_input('>').decode(sys.stdin.encoding)
    print 'Have fun:)'