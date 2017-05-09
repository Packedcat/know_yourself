#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Kitsch'

import wikipedia
import itchat
from itchat.content import *

wikipedia.set_lang('jp')

HELP_MSG = u'''\
找@`placeholder`
开@`placeholder`\
'''
@itchat.msg_register(TEXT)
def wiki_pedia(msg):
    # if msg['FromUserName'] != 'filehelper': return
    print(msg['Text'])
    l = msg['Text'].split('@')
    print(l)
    if l[0] == '找':
        r = wikipedia.search(l[1])
        print(r)
        itchat.send('是不是在找这些\n%s' % '\n'.join(r), msg['FromUserName'])
    elif l[0] == '开':
        page = wikipedia.page(l[1])
        print(page)
        itchat.send('%s\n%s' % (page.content, page.url), msg['FromUserName'])
    else:
        itchat.send('貌似有错误poi', msg['FromUserName'])

itchat.auto_login(hotReload=True)
itchat.send(HELP_MSG, 'filehelper') 
itchat.run()


# wikipedia.search('')
# r = wikipedia.page('')
# r.content
# r.url
# print wikipedia.summary("Wikipedia")
# Wikipedia (/ˌwɪkɨˈpiːdiə/ or /ˌwɪkiˈpiːdiə/ WIK-i-PEE-dee-ə)
# is a collaboratively edited, multilingual, free Internet
# encyclopedia supported by the non-profit Wikimedia Foundation...

# wikipedia.search("Barack")
# [u'Barak (given name)', u'Barack Obama'
# u'Barack (brandy)', u'Presidency of Barack Obama'
# u'Family of Barack Obama', u'First inauguration of Barack Obama'
# u'Barack Obama presidential campaign, 2008'
# u'Barack Obama, Sr.', u'Barack Obama citizenship conspiracy theories'
# u'Presidential transition of Barack Obama']

# ny = wikipedia.page("New York")
# ny.title
# u'New York'

# ny.url
# u'http://en.wikipedia.org/wiki/New_York'

# ny.content
# u'New York is a state in the Northeastern region of the United States.
# New York is the 27th-most exten'...

# ny.links[0]
# u'1790 United States Census'

# wikipedia.set_lang("fr")
# wikipedia.summary("Facebook", sentences=1)
# Facebook est un service de réseautage social en ligne
# sur Internet permettant d'y publier des informations
# (photographies, liens, textes, etc.) en contrôlant
# leur visibilité par différentes catégories de personnes.
