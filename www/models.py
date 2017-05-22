#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from utils import next_id
from orm import Model, StringField, BooleanField, FloatField, TextField


class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField(default=True)
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(default=time.time)


class Record(Model):
    __table__ = 'record'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    genres = StringField(default='Text', ddl='varchar(50)')
    title = StringField(ddl='varchar(50)')
    content = TextField()
    trash = BooleanField()
    archive = BooleanField()
    is_delete = BooleanField()
    created_at = FloatField(default=time.time)


class Tags(Model):
    __table__ = 'tags'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    tag = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)


class Relationship(Model):
    __table__ = 'relationship'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    tag = StringField(ddl='varchar(50)')
    tag_id = StringField(ddl='varchar(50)')
    record_id = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)
