from flask import Blueprint, json, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token
from sqlalchemy import text

from models import db, Portfolio, User, Coffee, FlavorProfile, user_schema, users_schema, coffee_schema, coffees_schema, portfolios_schema, portfolio_schema, Flavor
from helpers import token_required
from ..coffees.coffee_routes import get_coffee_id, update_coffee_table, create_flavor_profile, coffee_as_dict, create_new_coffee
from helpers import update_dict, get_user_id_from_JWT

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/', methods=['GET'])
@jwt_required()
def tester():
    response = {"message" : "Successful"}
    print(request.headers.get('Authorization'))
    get_user_id_from_JWT(request.headers.get('Authorization'))
    thing = create_access_token(identity=response)
    return jsonify(response)


@api.route('/<user_id>', methods=["POST"])
@jwt_required()
def add_coffee(user_id):
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
@jwt_required()
def get_coffees(user_id):
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
        v['coffeeID'] = v['id']
        v.update(portfolio_list[i])
    return jsonify(coffee_list)

@api.route('/<user_id>/<coffee_id>', methods=["GET"])
@jwt_required()
def get_coffee(user_id, coffee_id):
    '''
        Returns a single coffee from a User's Portfolio
        with tasting
    '''
    bean_response = Coffee.query.filter_by(id = coffee_id).first()
    single_coffee = coffee_schema.dump(bean_response)
    single_coffee.pop('id')
    single_coffee.update({'coffeeID' : coffee_id})
    print(single_coffee)
    response = Portfolio.query.filter_by(user=user_id, coffee=coffee_id).first()
    single_coffee.update(portfolio_schema.dump(response))
    print(single_coffee)
    return jsonify(single_coffee)

@api.route('/<user_id>/<coffee_id>', methods=['POST', 'PUT'])
@token_required
def update_coffee(current_user_token, user_id, coffee_id):
    ''' 
        Update a previous entry in coffee
    '''
    # before all else, check token against user_id on record
    token_user = get_user_id_from_JWT(request.headers.get('Authorization'))
    if token_user != user_id:
        return jsonify({"error message": "token does not match user id"})


    # load relevant variables for use
    # load entered attributes into a dictionary
    final_coffee_id = coffee_id
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
    update_acidity = request.json['acidity']

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
    if len(affected_portfolios)==1:
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
            final_coffee_id = existing_portfolio_entry.coffee = update_bag.id
        # correct bag does not exist
        else:
            new_coffee_id = create_new_coffee(update_attributes)
            coffee_to_update = Coffee.query.filter_by(id=new_coffee_id)
            final_coffee_id = existing_portfolio_entry.coffee = new_coffee_id

    coffee_to_update.roaster = updated_coffee_dict['roaster']
    coffee_to_update.bag_name = updated_coffee_dict['bag_name']
    coffee_to_update.origin = updated_coffee_dict['origin']
    coffee_to_update.producer = updated_coffee_dict['producer']
    coffee_to_update.variety = updated_coffee_dict['variety']
    coffee_to_update.process_method = updated_coffee_dict['process_method']
    coffee_to_update.blend = updated_coffee_dict['blend']

    if update_tasting_notes:
        existing_portfolio_entry.tasting_notes = update_tasting_notes
    if update_flavors and update_flavors.lower() != existing_portfolio_entry.flavors.lower():
        existing_portfolio_entry.flavors = update_flavors
        create_flavor_profile(update_flavors, final_coffee_id)
    
    db.session.commit()
    

    updated = Coffee.query.filter_by(id=final_coffee_id).first()
    response = coffee_schema.dump(updated)
    response.update(portfolio_schema.dump(existing_portfolio_entry))
    return jsonify(response)


@api.route('/<user_id>/<coffee_id>', methods=['DELETE'])
@jwt_required()
def delete_coffee(user_id, coffee_id):
    '''deletes a coffee from a user's portfolio'''

    token_user = get_user_id_from_JWT(request.headers.get('Authorization'))
    if token_user != user_id:
        return jsonify({"error message": "token does not match user id"})

    del_coffee = Portfolio.query.filter_by(user=user_id, coffee=coffee_id).first()
    del_coffee_bag = Coffee.query.filter_by(id=coffee_id).first()
    
    db.session.delete(del_coffee)
    db.session.commit()

    more_entries = Portfolio.query.filter_by(coffee=coffee_id).first()
    
    if not more_entries:
        FlavorProfile.query.filter_by(coffee_id=coffee_id).delete()
        db.session.delete(del_coffee_bag)
        db.session.commit()

    response = portfolio_schema.dump(del_coffee)
    response.update(coffee_schema.dump(del_coffee_bag))
    return jsonify(response)

@api.route('/coffee/<coffee_id>', methods=['GET'])
def get_coffee_profile( coffee_id: str):
    ''' returns the profile for a single coffee'''
    coffee = Coffee.query.filter_by(id=coffee_id).first()
    flavor_list = FlavorProfile.query.filter_by(coffee_id = coffee_id)\
        .join(Flavor, FlavorProfile.adjective_id == Flavor.id)\
            .add_entity(Flavor).limit(5).all()
    
    compiled_flavors = ''
    
    for flavor in flavor_list:
        print(flavor[1].adjective)
        compiled_flavors += flavor[1].adjective + ", "
    
    compiled_flavors = compiled_flavors[:-2:]
    print(compiled_flavors)
    
    
    response = coffee_schema.dump(coffee)
    response.update({'flavors': compiled_flavors})
    print(f'response: {response}')
    return jsonify(response)

@api.route('/coffee')
@jwt_required(optional=True)
def get_public_coffee ():
    '''Returns all coffees in DB
    
    page = request.args.get('page', 1, type=int)
    beans = Coffee.query.order_by(Coffee.roaster).paginate( 
                        page=page, 
                        per_page = Config.ITEMS_PER_PAGE,
                        error_out= False)
    
    next_url = prev_url = None
    
    if beans.has_next:
        next_url = url_for('coffee.all_coffees', page=beans.next_num)
    if beans.has_prev:
        prev_url = url_for('coffee.all_coffees', page=beans.prev_num)
    
    return render_template('coffee_database.html',
                           title='Coffee Database',
                           beans = beans.items,
                           next_page=next_url,
                           prev_page=prev_url)'''
    page = request.args.get('page', 1, type=int)
    items = request.args.get('items', 12, type=int)
    all_beans = Coffee.query.order_by(Coffee.roaster).paginate(
                    page=page,
                    per_page = items,
                    error_out = False)
    response ={'coffees' :  coffees_schema.dump(all_beans)}
    response.update({'tot_pages': all_beans.pages})
    return jsonify(response)

@api.route('/filter')
@jwt_required(optional=True)
def filter_results():
    roaster = request.args.get('roaster', '%%', type=str)
    bag_name = request.args.get('bag_name', '%%', type=str)
    origin = request.args.get('origin', '%%', type=str)
    producer = request.args.get('producer', '%%', type=str)
    variety = request.args.get('variety', '%%', type=str)
    flavors = request.args.get('flavors', '%%', type=str)
    process_method = request.args.get('process_method', '%%', type=str)
    
    query_filters = {
    'roaster' : request.args.get('roaster', '%%', type=str),
    'bag_name' : request.args.get('bag_name', '%%', type=str),
    'origin' : request.args.get('origin', '%%', type=str),
    'producer' : request.args.get('producer', '%%', type=str),
    'variety' : request.args.get('variety', '%%', type=str),
    'process_method' : request.args.get('process_method', '%%', type=str)
    }
    flavor = request.args.get('flavor', '%%', type=str)
    
    # filtered_beans = Coffee.query.filter_by(text(filter_test)).all()
    filtered_beans = Coffee.query.filter(Coffee.roaster.ilike(roaster), 
                                         Coffee.bag_name.ilike(bag_name),
                                         Coffee.origin.ilike(origin),
                                         Coffee.producer.ilike(producer),
                                         Coffee.variety.ilike(variety),
                                         Coffee.process_method.ilike(process_method)).all()
    
    
    test_filtered_beans = Coffee.query
    for attr, val in query_filters.items():
        test_filtered_beans = test_filtered_beans.filter( getattr(Coffee, attr).ilike(val))
    test_filtered_beans = test_filtered_beans.join(FlavorProfile, Coffee.id == FlavorProfile.coffee_id)\
        .join(Flavor, FlavorProfile.adjective_id == Flavor.id).filter(Flavor.adjective.ilike(flavor))

    
    filtered = test_filtered_beans.all()
    result = coffees_schema.dump(filtered)
    print(result)
    return jsonify(result)
    
    # response = coffees_schema.dump(filtered_beans)
    # return jsonify(response)
    
    
# def by_flavor(flavor):
#     flavor_id = Flavor.query.filter_by(adjective=flavor).first()
#     print('flavor_id: ', flavor_id)
#     # the following query needs a group_by(coffee.id) statement
#     # becasue there will be many of the same adjective pointing at
#     # each coffee with this ORM design
#     if flavor_id != None:
#         flavor_id = flavor_id.id
#         flavor_profile = FlavorProfile.query.filter_by(adjective_id=flavor_id).all()

#         coffee_id_list = [entry.coffee_id for entry in flavor_profile]

#         coffees_with_flavor = Coffee.query.filter(Coffee.id.in_(coffee_id_list)).all()

#         page = request.args.get('page', 1, type=int)
#         beans = Coffee.query.filter(Coffee.id.in_(coffee_id_list)).paginate( 
#                             page=page, 
#                             per_page = Config.ITEMS_PER_PAGE,
#                             error_out= False)
        
#         next_url = prev_url = None
        
#         if beans.has_next:
#             next_url = url_for('coffee.by_roaster', page=beans.next_num)
#         if beans.has_prev:
#             prev_url = url_for('coffee.by_roaster', page=beans.prev_num)

#         return render_template('coffee_database.html',
#                         title='Coffees by flavor',
#                         beans = beans.items,
#                         next_page=next_url,
#                         prev_page=prev_url)

#     else:
#         return redirect(url_for('site.home'))