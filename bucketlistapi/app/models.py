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


class Base(db.Model):

    '''Base Model'''
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime)

    # saves
    def save(self):
        db.session.add(self)
        db.session.commit()

    # deletes
    def delete(self):
        db.session.delete(self)
        db.session.commit()


class User(Base):

    '''User Table'''
    __tablename__ = 'user'
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    bucketlists = db.relationship('BucketList', backref=db.backref(
        'bucketlist', lazy='joined'), lazy='dynamic', uselist=True)

    # perform hashing on password
    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    # verify hashed password
    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    # generate timed authentication token
    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    # verify authentication token
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

    # json format
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


class BucketList(Base):

    '''BucketList Table'''
    __tablename__ = 'bucketlist'
    name = db.Column(db.String(64), unique=True, index=True)
    date_modified = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bucketitems = db.relationship('BucketItem', backref=db.backref(
        'bucketitem', lazy='joined'), lazy='dynamic', uselist=True)

    # instantiate bucketlist fields at creation
    def create(self):
        self.creator_id = g.user.id
        self.date_created = datetime.now()
        self.date_modified = datetime.now()

    # rename bucketlist
    def rename(self, new_name):
        self.name = new_name
        self.date_modified = datetime.now()
        self.save()

    # json format
    def to_json(self):
        items = [item.to_json() for item in self.bucketitems]
        json_bucketlist = {
            'id': self.id,
            'name': self.name,
            'created_by': User.query.get(self.creator_id).username,
            'date_created': self.date_created,
            'last_modified': self.date_modified,
            'items': items,
            'bucketlist_url': url_for(
                'api_1.bucketlist',
                bucketlist_id=self.id,
                _external=True
            ),
        }
        return json_bucketlist


class BucketItem(Base):

    '''BucketItem Table'''
    __tablename__ = 'bucketitem'
    name = db.Column(db.String(64), unique=True, index=True)
    date_modified = db.Column(db.DateTime)
    done = db.Column(db.Boolean)
    bucketlist_id = db.Column(db.Integer, db.ForeignKey('bucketlist.id'))

    # intantiate bucketitems fields at creation
    def create(self):
        self.date_created = datetime.now()
        self.date_modified = datetime.now()
        self.done = False

    # json format
    def to_json(self):
        json_items = {
            'id': self.id,
            'name': self.name,
            'date_created': self.date_created,
            'last_modified': self.date_modified,
            'done': self.done
        }
        return json_items
