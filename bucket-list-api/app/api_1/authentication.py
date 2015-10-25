'''
Handles all authentication for API
'''
from . import api_1
from ..models import User
from flask import request, url_for, g, abort, jsonify, session

from flask.ext.httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()


# registration endpoint
@api_1.route('/auth/register/', methods=['POST'])
def new_user():
    '''Register a new user'''
    username = request.json.get('username')
    password = request.json.get('password')

    if username is None or password is None:
        abort(400)  # missing arguments
    if User.query.filter_by(username=username).first() is not None:
        abort(400)  # existing user
    user = User(username=username)
    user.hash_password(password)
    user.save()
    return jsonify({
        'username': user.username,
        'Location': url_for('api_1.get_user', username=user.username,
                            _external=True)
    })


# login endpoint
@api_1.route('/auth/login/', methods=['POST'])
def login():
    '''Logins a user'''
    username = request.json.get('username')
    password = request.json.get('password')

    if verify_password(username, password):
        session['logged_in'] = True
        status = "Logged in successfully"
    else:
        status = "Invalid username or password"

    return jsonify({'status': status})


# logout endpoint
@api_1.route('/auth/logout/', methods=['POST'])
@auth.login_required
def logout():
    '''loguts a user'''
    session.pop('logged_in', None)
    return jsonify({'status': 'Logged Out'})


# verify users
@auth.verify_password
def verify_password(username_or_token, password):
    '''verifies user based on login credentials or generated token'''
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


# request for token
@api_1.route('/token/')
@auth.login_required
def get_auth_token():
    '''End point for users to request for token'''
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})
