from models import User
import secrets
import json
from functools import wraps
import decimal
from flask import jsonify, json, request


def token_required(flask_function):
    @wraps(flask_function)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token'].split(' ')[1]
        if not token:
            return jsonify({"message" : "Token missing"})
        
        try:
            current_user_token = User.query.filter_by(token=token).first()
        except:
            owner = User.query.filter_by(token=token).first()
            if owner.token != token and secrets.compare_digest():
                return jsonify({"message" : "Token is invalid"})


        return flask_function(current_user_token, *args, **kwargs)
    return decorated

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(JSONEncoder, self).default(obj)