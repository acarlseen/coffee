import secrets
import json
from functools import wraps
import decimal
from flask import jsonify, request
from flask_jwt_extended import decode_token

from models import User

def token_required(flask_function):
    @wraps(flask_function)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token'].split(' ')[1]
        if not token:
            return jsonify({"message" : "Token missing"})
        
        try:
            current_user_token = User.query.filter_by(token=token).first().token
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
    
def update_dict(existing_dict: dict, update_dict: dict):
    for k, v in existing_dict.items():
        if v == None or v == '':
            continue
        update_dict[k] = existing_dict[k]
    return update_dict

def get_user_id_from_JWT(auth: str):
    token = auth.split(' ')[1]
    print(f'INCOMING TOKEN: {token}')
    decoded_token = decode_token(token)
    print(decoded_token)
    user_id = decoded_token['sub'].split('|')
    if len(user_id) == 1:
        return user_id[0]
    return user_id[1]

    