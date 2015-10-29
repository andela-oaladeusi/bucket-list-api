'''
Test file to test authentication endpoints
'''
import json
import unittest
from base64 import b64encode

from flask import url_for, g

from app import create_app, db
from app.models import User, BucketList, BucketItem


class TestAPI(unittest.TestCase):
    default_username = 'lade'
    default_password = 'password'
    default_bucketlist = 'This is a default bucketlist'
    default_bucketlistitem = 'This is a default bucketlist item'

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        u = User(username=self.default_username)
        u.hash_password(self.default_password)
        u.save()
        g.user = u
        bucketlist = BucketList(name=self.default_bucketlist)
        bucketlist.create()
        bucketlist.save()
        item = BucketItem(
            name=self.default_bucketlistitem, bucketlist_id=bucketlist.id
        )
        item.create()
        item.save()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization':
                'Basic ' + b64encode(
                    (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_token(self):
        # calls the login function and returns the token generated
        response = self.client.post(
            url_for('api_1.login'),
            headers=self.get_api_headers('lade', 'password'),
            data=json.dumps({'username': 'lade', 'password': 'password'}))
        token = json.loads(response.data)['token']
        return token

    def test_no_auth(self):
        response = self.client.get(url_for('api_1.bucketlists'),
                                   content_type='application/json')
        self.assertTrue(response.status_code == 401)

    def test_auth_registration(self):
        # register a user
        response = self.client.post(
            url_for('api_1.new_user'),
            headers=self.get_api_headers('lade', 'password'),
            data=json.dumps({'username': 'dave', 'password': 'password'}))
        self.assertTrue(response.status_code == 200)

    def test_auth_login(self):
        # login a user
        response = self.client.post(
            url_for('api_1.login'),
            headers=self.get_api_headers('lade', 'password'),
            data=json.dumps({'username': 'lade', 'password': 'password'}))
        self.assertTrue(response.status_code == 200)

    def test_auth_logout(self):
        # logout a user
        token = self.get_token()
        response = self.client.post(
            url_for('api_1.logout'),
            headers=self.get_api_headers(token, 'password'))
        self.assertTrue(response.status_code == 200)

    # test errors
    def test_login_error(self):
        # test invalid username or password
        response = self.client.post(
            url_for('api_1.login'),
            headers=self.get_api_headers('lade', 'password'),
            data=json.dumps({'username': 'lad', 'password': 'pass'}))
        self.assertTrue(response.status_code == 200)

    def test_registration_error(self):
        # test double registration
        response = self.client.post(
            url_for('api_1.new_user'),
            headers=self.get_api_headers('lade', 'password'),
            data=json.dumps({'username': 'lade', 'password': 'password'}))
        self.assertTrue(response.status_code == 400)

    def test_empty_registration_error(self):
        # test empty registration
        response = self.client.post(
            url_for('api_1.new_user'),
            headers=self.get_api_headers('lade', 'password'))
        self.assertTrue(response.status_code == 400)
