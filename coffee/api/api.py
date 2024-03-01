from flask import Blueprint, json, jsonify, request

from models import db, Portfolio, User, Coffee, user_schema, users_schema, coffee_schema, coffees_schema, portfolios_schema, portfolio_schema 
from helpers import token_required
from ..coffees.coffee_routes import get_coffee_id, update_coffee_table, create_flavor_profile, coffee_as_dict, create_new_coffee
from helpers import update_dict

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/')

def tester():
    return jsonify({"message" : "Successful"})


@api.route('/<user_id>', methods=["POST"])
@token_required
def add_coffee(current_user_token, user_id):
    ''' adds a coffee to a user's portfolio and (if new) to the database '''
    roaster = request.json['roaster']
    bag_name = request.json['bag_name']
    origin = request.json['origin']
    producer = request.json['producer']
    variety = request.json['variety']
    process_method = request.json['process_method']
    blend = request.json['blend']
    flavors = request.json['flavors']
    tasting_notes = request.json['tasting_notes']
    acidity = request.json['acidity']

    incoming_coffee = {"roaster" : roaster,
                         "bag_name" : bag_name,
                         "origin" : origin,
                         "producer" : producer,
                         "variety" : variety,
                         "process_method" : process_method,
                         "blend" : blend}
    
    coffee_id, _ = get_coffee_id(incoming_coffee)

    portfolio_add = Portfolio(user_id, coffee_id, tasting_notes, flavors)
    db.session.add(portfolio_add)
    db.session.commit()
    create_flavor_profile(flavors, coffee_id, acidity)
    db.session.commit()

    response = portfolio_schema.dump(portfolio_add)
    return jsonify(response)



@api.route('/<user_id>', methods=['GET'])
@token_required
def get_coffees(current_user_token, user_id):
    '''
        Returns a json object of all coffees in one User's Portfolio
    '''
    coffees_in_portfolio = Portfolio.query.filter_by(user=user_id).all()
    print(coffees_in_portfolio)
    coffee_list = []
    for coffee in coffees_in_portfolio:
        beans = Coffee.query.filter_by(id = coffee.coffee).first()
        coffee_list.append(coffee_schema.dump(beans))
    portfolio_list = portfolios_schema.dump(coffees_in_portfolio)

    for i, v in enumerate(coffee_list):
        v.update(portfolio_list[i])
    return jsonify(coffee_list)

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
    # load relevant variables for use
    # load entered attributes into a dictionary
    update_attributes = {}
    update_attributes['roaster'] = request.json['roaster']
    update_attributes['bag_name'] = request.json['bag_name']
    update_attributes['origin'] = request.json['origin']
    update_attributes['producer'] = request.json['producer']
    update_attributes['variety'] = request.json['variety']
    update_attributes['process_method'] = request.json['process_method']
    update_attributes['blend'] = request.json['blend']
    update_tasting_notes = request.json['tasting_notes']
    update_flavors = request.json['flavors']

    # load existing_coffee attributes into a dictionary
    coffee_to_update = Coffee.query.filter_by(id=coffee_id).first()
    existing_coffee_dict = coffee_as_dict(coffee_to_update)

    # load existing porfolio entry for this user/coffee combo
    existing_portfolio_entry = Portfolio.query.filter_by(user=user_id, coffee=coffee_id).first()

    # user may not be updating 'roaster' and/or 'bag_name'
    # necessary for lookup (because these are required on the entry form)
    if update_attributes['roaster'] == None or update_attributes['roaster'] == '':
        update_attributes['roaster'] = existing_coffee_dict['roaster']
    if update_attributes['bag_name'] == None or update_attributes['bag_name'] == '':
        update_attributes['bag_name'] = existing_coffee_dict['bag_name']
    
    ###### End necessary loading ######

    
    # check if the coffee is only in this portfolio, if so it is safe to alter all attributes.
    affected_portfolios = Portfolio.query.filter_by(coffee=coffee_id).all()
    
    unique_entry = False
    if len(affected_portfolios==1):
        unique_entry=True

    # check if user is correcting entering the wrong bag of beans
    update_bag = Coffee.query.filter_by(roaster=update_attributes['roaster'], bag_name=update_attributes['bag_name']).first()
    same_bag = False
    if update_bag and update_bag.id == coffee_id:
        same_bag = True

    
    if same_bag == True:
        ''' user has initially entered correct roaster and bag_name, has additional updates '''
        # create an updated dict
        updated_coffee_dict = update_dict(existing_coffee_dict, update_attributes)

    else:
        ''' user entered wrong bag to db '''
        # correct bag exists
        if update_bag:
            correct_bag_dict = coffee_as_dict(update_bag)
            updated_coffee_dict = update_dict(correct_bag_dict, update_attributes)
        # correct bag does not exist
        else:
            new_coffee_id = create_new_coffee(update_attributes)

        db.session.delete(existing_portfolio_entry)
        corrected_portfolio = Portfolio(user_id, update_bag.id, tasting_notes, flavors)
        db.session.add(corrected_portfolio)


    


        '''
    ##### old code, some snippets might be useful
        
        
        db.session.delete(affected_portfolios[0])
        coffee_to_delete = Coffee.query.filter_by(id=affected_portfolios[0].coffee).first()
        db.session.delete(coffee_to_delete)

    else:
        db.session.delete(existing_portfolio_entry)


    fetched_coffee_id = get_coffee_id(update_attributes)

    # case: bag update, user added wrong bag to portfolio
    # get correct bag, then evaluate tasting note updates and apply
    if fetched_coffee_id != coffee_id:
        coffee = Coffee.query.filter_by(id=fetched_coffee_id).first()
        if update_tasting_notes == None:
            portfolio_add = Portfolio(user_id, fetched_coffee_id, existing_portfolio_entry.tasting_notes)
        else:
            portfolio_add = Portfolio(user_id, fetched_coffee_id, update_tasting_notes)
        db.session.delete(existing_portfolio_entry)
        db.session.add(portfolio_add)
        portfolio = portfolio_add
    
    # case: correct bag, updating bag info and/or tasting notes
    else:
        portfolio = existing_portfolio_entry
        coffee = Coffee.query.filter_by(id=coffee_id)
        update_coffee_table(coffee, update_attributes)
        if update_tasting_notes != None:
            existing_portfolio_entry.tasting_notes = update_tasting_notes
    
    db.session.commit()

    response1 = coffee_schema.dump(coffee)
    response2 = portfolio_schema(portfolio)
    
    return jsonify(response1), jsonify(response2)'''

@api.route('/<user_id>/<coffee_id>', methods=['DELETE'])
@token_required
def delete_coffee(current_user_token, user_id, coffee_id):
    '''deletes a coffee from a user's portfolio'''
    del_coffee = Portfolio.query.filter_by(user=user_id, coffee=coffee_id).first()
    db.session.delete(del_coffee)
    db.session.commit()

    response = coffee_schema.dump(del_coffee)
    return jsonify(response)

@api.route('/coffee/<coffee_id>', methods=['GET'])
@token_required
def get_coffee_profile(current_user_token, coffee_id: str):
    ''' returns the profile for a single coffee'''
    coffee = Coffee.query.filter_by(id=coffee_id).first()
    response = coffee_schema.dump(coffee)
    return jsonify(response)