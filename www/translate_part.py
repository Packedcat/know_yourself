#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
import hashlib
import urllib
import random
import http.client

appid = '20170509000046718'
secretKey = 'v8SvEBXD8edZuLeRw23Q'

 
httpClient = None
myurl = '/api/trans/vip/translate'
q = 'apple'
fromLang = 'en'
toLang = 'zh'
salt = random.randint(32768, 65536)

sign = appid+q+str(salt)+secretKey
m1 = hashlib.md5(sign.encode(encoding='gb2312'))
sign = m1.hexdigest()
myurl = myurl+'?appid='+appid+'&q='+urllib.parse.quote(q)+'&from='+fromLang+'&to='+toLang+'&salt='+str(salt)+'&sign='+sign

try:
    httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
    httpClient.request('GET', myurl)
    response = httpClient.getresponse()
    print(response.read())
except Exception as e:
    print(e)
finally:
    if httpClient:
        httpClient.close()
