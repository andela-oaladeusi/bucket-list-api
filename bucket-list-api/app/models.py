'''
Models for bucketlist API
'''
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    BadSignature, SignatureExpired
)
from flask import url_for, current_app, g

from . import db

from datetime import datetime
import json


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    bucketlists = db.relationship('BucketList', backref=db.backref(
        'bucketlist', lazy='joined'), lazy='dynamic', uselist=True)

    def __repr__(self):
        return '<User: {0}>'.format(self.name)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user

    def to_json(self):
        bucketlists = [item.to_json() for item in self.bucketlists]
        json_user = {
            'username': self.username,
            'user_url': url_for(
                'api_1.get_user', username=self.username, _external=True
            ),
            'bucketlists': bucketlists
        }
        return json_user

    @staticmethod
    def from_json(json_user):
        User(json.loads(json_user)).save()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class BucketList(db.Model):
    __tablename__ = 'bucketlist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    date_created = db.Column(db.DateTime)
    date_modified = db.Column(db.DateTime)
    created_by = db.Column(db.String(64))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bucketitem = db.relationship('BucketItems', backref=db.backref(
        'bucketitems', lazy='joined'), lazy='dynamic', uselist=True)

    def __repr__(self):
        return '<Bucket List: {0}>'.format(self.name)

    def creation(self):
        self.created_by = g.user.username
        self.creator_id = g.user.id
        self.date_created = datetime.utcnow()
        self.date_modified = datetime.utcnow()

    def rename(self, new_name):
        self.name = new_name
        self.date_modified = datetime.utcnow()
        self.save()

    def to_json(self):
        items = [item.to_json() for item in self.bucketitem]

        json_bucketlist = {
            'id': self.id,
            'name': self.name,
            'created_by': self.created_by,
            'date_created': self.date_created,
            'last_modified': self.date_modified,
            'items': items,
            'bucketlist_url': url_for(
                'api_1.get_bucketlist',
                bucketlist_id=self.id,
                _external=True
            ),
        }
        return json_bucketlist

    @staticmethod
    def from_json(json_bucketlist):
        BucketList(json.loads(json_bucketlist)).save()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class BucketItems(db.Model):
    __tablename__ = 'bucketitems'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    date_created = db.Column(db.DateTime)
    date_modified = db.Column(db.DateTime)
    done = db.Column(db.Boolean)
    bucketlist_id = db.Column(db.Integer, db.ForeignKey('bucketlist.id'))

    def __repr__(self):
        return '<Bucket Item: {0}>'.format(self.name)

    def creation(self):
        self.date_created = datetime.utcnow()
        self.date_modified = datetime.utcnow()
        self.done = False

    def to_json(self):
        json_items = {
            'id': self.id,
            'name': self.name,
            'date_created': self.date_created,
            'last_modified': self.date_modified,
            'done': self.done
        }
        return json_items

    @staticmethod
    def from_json(json_items):
        BucketItems(json.loads(json_items)).save()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
