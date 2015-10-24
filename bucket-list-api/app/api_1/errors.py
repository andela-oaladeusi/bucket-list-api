'''
Error handling for API
'''
from flask import jsonify, make_response

from . import api_1


@api_1.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


@api_1.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify({'error': 'Unauthorized'}), 401)


@api_1.errorhandler(403)
def forbidden(error):
    return make_response(jsonify({'error': 'Forbidden'}), 403)


@api_1.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def internal_server_error(error):
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)
