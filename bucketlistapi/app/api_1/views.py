'''
Views for the API
'''
from flask import jsonify, request, g, current_app, url_for


from . import api_1
from . import errors
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
        return errors.bad_request(400)
    return jsonify({'user': user.to_json()})


# bucketlist endpoints
@api_1.route('/bucketlists/')
@auth.login_required
def get_bucketlists():
    '''Lists all created bucketlists'''
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

    # Query the BucketList table and apply query parameters set
    pagination = BucketList.query.filter_by(
        created_by=g.user.username
    ).filter(
        BucketList.name.contains(q)
    ).paginate(
        page, per_page=limit, error_out=False
    )

    # variable for all bucketlist returned after query
    bucketlists = pagination.items

    # get url of prev page
    prev_pg = url_for(
        'api_1.get_bucketlists', page=page - 1, _external=True
    ) if pagination.has_prev else None

    # get url of next page
    next_pg = url_for(
        'api_1.get_bucketlists', page=page + 1, _external=True
    ) if pagination.has_next else None

    return jsonify({
        'bucketlists': [bucketlist.to_json() for bucketlist in bucketlists],
        'prev': prev_pg,
        'next': next_pg,
        'count': pagination.total
    })


@api_1.route('/bucketlists/', methods=['POST'])
@auth.login_required
def add_bucketlist():
    '''Creates a new bucketlist'''
    name = request.json.get('name')
    if not name:
        return errors.bad_request(400)  # empty name field
    bucketlist = BucketList(name=name)
    bucketlist.creation()
    bucketlist.save()

    return jsonify({'bucketlist': bucketlist.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/')
@auth.login_required
def get_bucketlist(bucketlist_id):
    '''Returns a single bucketlist'''
    bucketlist = BucketList.query.get_or_404(bucketlist_id)

    # Allows authenticated users view only  their bucketlist
    if bucketlist.created_by != g.user.username:
        return errors.unauthorized(401)
    return jsonify({'bucketlist': bucketlist.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/', methods=['PUT'])
@auth.login_required
def change_bucketlist_name(bucketlist_id):
    '''Update this bucketlist name'''
    bucketlist = BucketList.query.get(bucketlist_id)

    # Allows authenticated users update only their bucketlist
    if bucketlist.created_by == g.user.username:
        name = request.json.get('name')
        bucketlist.rename(name)
    else:
        return errors.unauthorized(401)

    return jsonify({'bucketlist': bucketlist.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/', methods=['DELETE'])
@auth.login_required
def delete_bucketlist(bucketlist_id):
    '''Delete this single bucketlist'''
    bucketlist = BucketList.query.get(bucketlist_id)

    # Allows authenticated users delete only their bucketlist
    if bucketlist.created_by == g.user.username:
        bucketlist.delete()
        return jsonify({"status": "successfully deleted"})
    else:
        return errors.unauthorized(401)


@api_1.route('/bucketlists/<int:bucketlist_id>/items/', methods=['POST'])
@auth.login_required
def add_bucketlist_item(bucketlist_id):
    '''Create a new bucketlist item'''
    bucketlist = BucketList.query.get(bucketlist_id)

    # Allows authenticated users create bucketitems only in their bucketlist
    if bucketlist.created_by == g.user.username:
        bucketitems = BucketItems(
            name=request.json.get('name'),
            bucketlist_id=bucketlist.id
        )
        bucketitems.creation()
        bucketitems.save()
    else:
        return errors.unauthorized(401)

    return jsonify({'item': bucketitems.to_json()})


@api_1.route('/bucketlists/<int:bucketlist_id>/items/<int:bucketitem_id>/', methods=['PUT'])
@auth.login_required
def update_bucketitem_status(bucketlist_id, bucketitem_id):
    '''Update a bucketlist item status'''
    bucketlist = BucketList.query.get(bucketlist_id)

    # Allows authenticated users update only their bucketitem
    if bucketlist.created_by != g.user.username:
        return errors.unauthorized(401)
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

    # Allows authenticated users delete only their bucketitem
    if bucketlist.created_by != g.user.username:
        return errors.unauthorized(401)
    items = BucketItems.query.filter_by(bucketlist_id=bucketlist_id).all()
    for bucketitem in items:
        if bucketitem.id == bucketitem_id:
            bucketitem.delete()
            break
    return jsonify({"status": "successfully deleted"})
