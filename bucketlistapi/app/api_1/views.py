'''
Views for the API
'''
from flask import jsonify, request, g, current_app, url_for

from . import api_1
from . import errors
from .authentication import auth
from ..models import User, BucketList, BucketItem
from datetime import datetime


# user endpoints
@api_1.route('/users/')
@auth.login_required
def get_users():
    '''Returns all users'''

    users = User.query.all()
    return jsonify({
        'users': [{'user': user.to_json()} for user in users]
    })


@api_1.route('/users/<username>/')
@auth.login_required
def get_user(username):
    '''Returns a user'''

    user = User.query.filter_by(username=username).first()
    if not user:
        return errors.bad_request(400)
    return jsonify({'user': user.to_json()})


# bucketlist endpoints
@api_1.route('/bucketlists/', methods=['GET', 'POST'])
@auth.login_required
def bucketlists():
    '''Returns all bucketlists or adds a new bucketlist'''

    if request.method == 'POST':
        # create a bucketlist
        name = request.json.get('name')
        if not name:
            return errors.bad_request(400)  # empty name field
        bucketlist = BucketList(name=name)
        bucketlist.create()
        bucketlist.save()

        return jsonify({'bucketlist': bucketlist.to_json()})

    else:
        # list all created bucketlists

        # gets page to display or sets it to page 1 by default
        page = request.args.get('page', 1, type=int)

        # gets the number of posts the user desires to see per page
        limit = request.args.get(
            'limit', current_app.config['DEFAULT_PER_PAGE'], type=int)

        # checks if limit is greater than allowed maximum
        if limit > current_app.config['MAX_PER_PAGE']:
            limit = current_app.config['MAX_PER_PAGE']

        # gets the bucketname the user desires to see
        q = request.args.get('q', "", type=str)

        # paginate bucketlist
        # query the BucketList table and apply query parameters set
        pagination = BucketList.query.filter_by(
            creator_id=g.user.id
        ).filter(
            BucketList.name.contains(q)
        ).paginate(
            page, per_page=limit, error_out=False
        )

        bucketlists = pagination.items

        # get url of prev page if any
        prev_page = url_for(
            'api_1.bucketlists', page=page - 1, _external=True
        ) if pagination.has_prev else None

        # get url for next page if any
        next_page = url_for(
            'api_1.bucketlists', page=page + 1, _external=True
        ) if pagination.has_next else None

        return jsonify({
            'bucketlists': [
                bucketlist.to_json() for bucketlist in bucketlists
            ],
            'prev': prev_page,
            'next': next_page,
            'count': pagination.total
        })


@api_1.route('/bucketlists/<int:bucketlist_id>/',
             methods=['GET', 'PUT', 'DELETE'])
@auth.login_required
def bucketlist(bucketlist_id):
    '''Modifies, deletes or returns a bucketlist'''

    # gets the bucketlist created by the user
    bucketlist = BucketList.query.filter_by(
        id=bucketlist_id, creator_id=g.user.id).first()

    if bucketlist is None:
        return errors.not_found(404)

    if request.method == 'PUT':
        # update this bucketlist
        name = request.json.get('name')
        bucketlist.rename(name)
    elif request.method == 'DELETE':
        # delete this bucketlist
        bucketlist.delete()
        return jsonify({"status": "successfully deleted!"})

    return jsonify({'bucketlist': bucketlist.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/items/', methods=['POST'])
@auth.login_required
def add_bucketitem(bucketlist_id):
    '''Create a new bucketlist item'''

    # gets the bucketlist created by the user
    bucketlist = BucketList.query.filter_by(
        id=bucketlist_id, creator_id=g.user.id).first()

    if bucketlist is None:
        return errors.not_found(404)

    bucketitem = BucketItem(
        name=request.json.get('name'),
        bucketlist_id=bucketlist.id
    )
    bucketitem.create()
    bucketitem.save()

    return jsonify({'item': bucketitem.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/items/<int:bucketitem_id>/',
             methods=['PUT', 'DELETE'])
@auth.login_required
def bucketitem(bucketlist_id, bucketitem_id):
    '''Update or delete a bucketitem'''

    # gets the bucketlist created by the user
    bucketlist = BucketList.query.filter_by(
        id=bucketlist_id, creator_id=g.user.id).first()

    if bucketlist is None:
        return errors.not_found(404)

    # get the bucketitem belonging to the bucketlist
    bucketitem = BucketItem.query.filter_by(
        id=bucketitem_id, bucketlist_id=bucketlist.id).first()

    if bucketitem is None:
        return errors.not_found(404)

    if request.method == 'PUT':
        bucketitem.done = request.json.get('done')
        new_name = request.json.get('name')
        if new_name is not None:
            bucketitem.name = new_name
        bucketitem.date_modified = datetime.now()
        return jsonify({'item': bucketitem.to_json()})
    else:
        bucketitem.delete()
        return jsonify({"status": "successfully deleted!"})
