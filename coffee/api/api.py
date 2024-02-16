from flask import Blueprint, json, jsonify, request

from models import db, Portfolio, User, Coffee, user_schema, users_schema, coffee_schema, coffees_schema, portfolios_schema, portfolio_schema 
from helpers import token_required
from ..coffees.coffee_routes import get_coffee_id, update_coffee_table

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/')
@token_required
def tester(current_user_token):
    return jsonify({"message" : "Successful"})


@api.route('/<user_id>', methods=["POST"])
@token_required
def add_coffee(current_user_token, user_id):
    roaster = request.json['roaster']
    bag_name = request.json['bag_name']
    origin = request.json['origin']
    producer = request.json['producer']
    variety = request.json['variety']
    process = request.json['process']
    blend = request.json['blend']
    tasting_notes = request.json['tasting_notes']

    incoming_coffee = {"roaster" : roaster,
                         "bag_name" : bag_name,
                         "origin" : origin,
                         "producer" : producer,
                         "variety" : variety,
                         "process" : process,
                         "blend" : blend}
    
    coffee_id = get_coffee_id(incoming_coffee)

    portfolio_add = Portfolio(user_id, coffee_id, tasting_notes)
    db.session.add(portfolio_add)
    db.session.commit()

    response = portfolio_schema.dump(portfolio_add)
    return jsonify(response)



@api.route('/<user_id>', methods=['GET'])
@token_required
def get_coffees(current_user_token, user_id):
    '''
        Returns a json object of all coffees in one User's Portfolio
    '''
    response = Portfolio.query.filter_by(user=user_id).all()
    return jsonify(response)

@api.route('/<user_id>/<coffee_id>', methods=["GET"])
@token_required
def get_coffee(current_user_token, user_id, coffee_id):
    '''
        Returns a single coffee from a User's Portfolio
    '''
    response = Portfolio.query.filter_by(user=user_id, coffee=coffee_id)
    return jsonify(response)

@api.route('/<user_id>/<coffee_id>', methods=['POST', 'PUT'])
@token_required
def update_coffee(current_user_token, user_id, coffee_id):
    ''' 
        Update a previous entry in coffee
    '''

    existing_portfolio_entry = Portfolio.query.filter_by(user=user_id, coffee=coffee_id).first()

    attributes = {}
    attributes['roaster'] = request.json['roaster']
    attributes['bag_name'] = request.json['bag_name']
    attributes['origin'] = request.json['origin']
    attributes['producer'] = request.json['producer']
    attributes['variety'] = request.json['variety']
    attributes['process'] = request.json['process']
    attributes['blend'] = request.json['blend']
    tasting_notes = request.json['tasting_notes']

    fetched_coffee_id = get_coffee_id(attributes)

    # case: bag update, user added wrong bag to portfolio
    # get correct bag, then evaluate tasting note updates and apply
    if fetched_coffee_id != coffee_id:
        coffee = Coffee.query.filter_by(id=fetched_coffee_id).first()
        if tasting_notes == None:
            portfolio_add = Portfolio(user_id, fetched_coffee_id, existing_portfolio_entry.tasting_notes)
        else:
            portfolio_add = Portfolio(user_id, fetched_coffee_id, tasting_notes)
        db.session.delete(existing_portfolio_entry)
        db.session.add(portfolio_add)
        portfolio = portfolio_add
    
    # case: correct bag, updating bag info and/or tasting notes
    else:
        portfolio = existing_portfolio_entry
        coffee = Coffee.query.filter_by(id=coffee_id)
        update_coffee_table(coffee, attributes)
        if tasting_notes != None:
            existing_portfolio_entry.tasting_notes = tasting_notes
    
    db.session.commit()

    response1 = coffee_schema.dump(coffee)
    response2 = portfolio_schema(portfolio)
    
    return jsonify(response1), jsonify(response2)

@api.route('/<user_id>/<coffee_id>', methods=['DELETE'])
@token_required
def delete_coffee(current_user_token, user_id, coffee_id):
    del_coffee = Portfolio.query.filter_by(user=user_id, coffee=coffee_id).first()
    db.session.delete(del_coffee)
    db.session.commit()

    response = coffee_schema.dump(del_coffee)
    return jsonify(response)



