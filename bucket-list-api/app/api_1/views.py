'''
Views for the API
'''
from flask import jsonify, request, abort, g


from . import api_1
from .authentication import auth
from ..models import User, BucketList, BucketItems
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
    '''Return a user'''
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(400)
    return jsonify({'user': user.to_json()})


# bucketlist endpoints
@api_1.route('/bucketlists/')
@auth.login_required
def get_bucketlists():
    '''Lists all created bucketlists'''
    limit = request.args.get('limit')
    q = request.args.get('q')
    if limit:
        limit = int(limit)
        if limit > 0 or limit <= 100:
            bucketlists = BucketList.query.limit(limit).all()
    elif q:
        bucketlists = BucketList.query.filter(
            BucketList.name.contains(q)).all()
    else:
        bucketlists = BucketList.query.limit(20).all()

    return jsonify({
        'bucketlists': [bucketlist.to_json() for bucketlist in bucketlists]
    })


@api_1.route('/bucketlists/', methods=['POST'])
@auth.login_required
def add_bucketlist():
    '''Creates a new bucketlist'''
    name = request.json.get('name')
    if not name:
        abort(400)
    bucketlist = BucketList(name=name)
    bucketlist.creation()
    bucketlist.save()

    return jsonify({'bucketlist': bucketlist.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/')
@auth.login_required
def get_bucketlist(bucketlist_id):
    '''Returns a single bucketlist'''
    bucketlist = BucketList.query.get_or_404(bucketlist_id)
    return jsonify({'bucketlist': bucketlist.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/', methods=['PUT'])
@auth.login_required
def change_bucketlist_name(bucketlist_id):
    '''Update this bucketlist name'''
    bucketlist = BucketList.query.get(bucketlist_id)
    if bucketlist.created_by == g.user.username:
        name = request.json.get('name')
        bucketlist.rename(name)
    else:
        abort(401)

    return jsonify({'bucketlist': bucketlist.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/', methods=['DELETE'])
@auth.login_required
def delete_bucketlist(bucketlist_id):
    '''Delete this single bucketlist'''
    bucketlist = BucketList.query.get(bucketlist_id)
    if bucketlist.created_by == g.user.username:
        bucketlist.delete()
        return jsonify({"status": "successfully deleted"})
    else:
        abort(401)


@api_1.route('/bucketlists/<int:bucketlist_id>/items/', methods=['POST'])
@auth.login_required
def add_bucketlist_item(bucketlist_id):
    '''Create a new bucketlist item'''
    bucketlist = BucketList.query.get(bucketlist_id)
    if bucketlist.created_by == g.user.username:
        bucketitems = BucketItems(
            name=request.json.get('name'),
            bucketlist_id=bucketlist.id
        )
        bucketitems.creation()
        bucketitems.save()
    else:
        abort(401)

    return jsonify({'item': bucketitems.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/items/<int:bucketitem_id>/', methods=['PUT'])
@auth.login_required
def update_bucketitem_status(bucketlist_id, bucketitem_id):
    '''Update a bucketlist item status'''
    bucketlist = BucketList.query.get(bucketlist_id)
    if bucketlist.created_by != g.user.username:
        abort(403)
    items = BucketItems.query.filter_by(bucketlist_id=bucketlist_id).all()
    for bucketitem in items:
        if bucketitem.id == bucketitem_id:
            bucketitem.done = request.json.get('done')
            bucketitem.date_modified = datetime.utcnow()
            break
    bucketitem = BucketItems.query.get(bucketitem_id)

    return jsonify({'item': bucketitem.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/items/<int:bucketitem_id>/', methods=['DELETE'])
@auth.login_required
def delete_item(bucketlist_id, bucketitem_id):
    '''Delete a bucketlist item'''
    bucketlist = BucketList.query.get(bucketlist_id)
    if bucketlist.created_by != g.user.username:
        abort(401)
    items = BucketItems.query.filter_by(bucketlist_id=bucketlist_id).all()
    for bucketitem in items:
        if bucketitem.id == bucketitem_id:
            bucketitem.delete()
            break
    return jsonify({"status": "successfully deleted"})
