from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
import re



from config import Config
from models import Coffee, Portfolio, Flavor, FlavorProfile
from models import db
from forms import CoffeeForm
from .. import login_manager

coffee = Blueprint('coffee', __name__,
                   static_folder='static',
                   static_url_path='/coffees',
                   template_folder='coffee_templates')

@coffee.route('/addcoffee', methods=['GET', 'POST'])
@login_required
def add_coffee():

    form = CoffeeForm()
    print("form loaded")
    try:
        print(form.validate_on_submit())
        if request.method == 'POST' and form.validate_on_submit():
            print("processing")
            attributes = {}
            attributes['roaster'] = form.roaster.data
            attributes['bag_name'] = form.bag_name.data
            attributes['origin'] = form.origin.data
            attributes['producer'] = form.producer.data
            if form.variety.data:
                attributes['variety'] = str(form.variety.data).lower()
            else:
                attributes['variety'] = None
            if form.process_method.data:
                attributes['process_method'] = str(form.process_method.data).lower()
            else:
                attributes['process_method'] = None
            attributes['blend'] = form.blend.data
            # get coffee_id, and check if coffee is new or exists in db
            new_coffee_id, coffee_is_new = get_coffee_id(attributes)
            print("new_coffee_id: ", new_coffee_id)
            
            # these go to a separate table
            acidity = form.acidity.data
            flavors = str(form.flavors.data).lower()
            tasting_notes = form.tasting_notes.data
            
            
            if flavors == 'none':   #honestly, it works to avoid NoneType errors above.
                flavors = None      # change back to None

            print('flavors: ', flavors)
            create_flavor_profile(flavors, new_coffee_id, acidity)
            
            #check if already in portfolio (unless coffee is new to db):
            # This was causing a query problem with commits vs. rendering speed
            existing_portfolio = None

            if coffee_is_new == False:
                existing_portfolio = Portfolio.query.filter_by(user=current_user.get_id(), coffee=new_coffee_id).first()
            
            if existing_portfolio == None:
                portfolio_addition = Portfolio(user=current_user.get_id(), coffee=new_coffee_id, tasting_notes=tasting_notes, flavors=flavors)
                db.session.add(portfolio_addition)

            else:
                print('existing_portfolio.user = ', existing_portfolio.user)
                print('existing_portfolio.coffee: ', existing_portfolio.coffee)
                existing_portfolio.tasting_notes=tasting_notes
                existing_portfolio.flavors=flavors

            print(f'coffee_id: {new_coffee_id} \n tasting_notes: {tasting_notes} \n flavors: {flavors})')
            db.session.commit()

            return redirect(url_for('profile.portfolio', user_id=current_user.get_id()))
    except:
        raise Exception('Something went wrong')
    
    return render_template('add_coffee.html',
                           title = 'Add a bag',
                           form = form)

@coffee.route('/coffee', methods=['GET'])
def all_coffees():
    ''' this page displays all of the coffees in the database'''
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
                           prev_page=prev_url)

@coffee.route('/coffee/<coffee_id>', methods=['GET'])
def coffee_profile(coffee_id):
    '''
        Displays a single coffee's page
    '''
    entry_id = notes = flavors = None
    coffee = Coffee.query.filter_by(id=coffee_id).first()
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        portfolio_entry = Portfolio.query.filter_by(user=user_id, coffee=coffee_id).first()
        
        if portfolio_entry:
            entry_id = portfolio_entry.id
            if portfolio_entry.flavors:
                flavors = portfolio_entry.flavors.capitalize()
            if portfolio_entry.tasting_notes:
                notes = portfolio_entry.tasting_notes

    flavor_profile = FlavorProfile.query.filter_by(coffee_id=coffee_id).join(Flavor, Flavor.id == FlavorProfile.adjective_id).add_columns(Flavor.adjective).all()
    tester = FlavorProfile.query.filter_by(coffee_id=coffee_id).join(Flavor, Flavor.id == FlavorProfile.adjective_id).add_entity(Flavor).all()

    return render_template('coffee_profile.html',
                           title=coffee.roaster +' '+coffee.bag_name,
                           coffee=coffee,
                           tasting_notes=notes,
                           flavors=flavors,
                           more_from_roaster=coffee.roaster,
                           more_by_flavor = flavor_profile,
                           entry_id = entry_id)


@coffee.route('/delete/<entry_id>')
@login_required
def delete_coffee(entry_id: str):
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        '''deletes a coffee from a user's portfolio'''
        del_coffee = Portfolio.query.filter_by(id=entry_id).first()
        del_coffee_bag = Coffee.query.filter_by(id=del_coffee.coffee).first()
        
        db.session.delete(del_coffee)
        db.session.commit()

        more_entries = Portfolio.query.filter_by(coffee=del_coffee.coffee).first()
        
        if not more_entries:
            FlavorProfile.query.filter_by(coffee_id=del_coffee.coffee).delete()
            db.session.delete(del_coffee_bag)
            db.session.commit()
    
    return redirect(url_for('profile.portfolio', user_id=user_id))

@coffee.route('/coffee/roaster/<roaster_name>', methods=['GET'])
def by_roaster(roaster_name):

    page = request.args.get('page', 1, type=int)
    beans = Coffee.query.filter_by(roaster=roaster_name).paginate( 
                        page=page, 
                        per_page = Config.ITEMS_PER_PAGE,
                        error_out= False)
    
    next_url = prev_url = None
    
    if beans.has_next:
        next_url = url_for('coffee.by_roaster', page=beans.next_num)
    if beans.has_prev:
        prev_url = url_for('coffee.by_roaster', page=beans.prev_num)
    
    return render_template('coffee_database.html',
                           title=roaster_name,
                           beans = beans.items,
                           next_page=next_url,
                           prev_page=prev_url)



@coffee.route('/coffee/by_flavor/<flavor>', methods=['GET'])
def by_flavor(flavor):
    flavor_id = Flavor.query.filter_by(adjective=flavor).first()
    print('flavor_id: ', flavor_id)
    # the following query needs a group_by(coffee.id) statement
    # becasue there will be many of the same adjective pointing at
    # each coffee with this ORM design
    if flavor_id != None:
        flavor_id = flavor_id.id
        flavor_profile = FlavorProfile.query.filter_by(adjective_id=flavor_id).all()

        coffee_id_list = [entry.coffee_id for entry in flavor_profile]

        coffees_with_flavor = Coffee.query.filter(Coffee.id.in_(coffee_id_list)).all()

        page = request.args.get('page', 1, type=int)
        beans = Coffee.query.filter(Coffee.id.in_(coffee_id_list)).paginate( 
                            page=page, 
                            per_page = Config.ITEMS_PER_PAGE,
                            error_out= False)
        
        next_url = prev_url = None
        
        if beans.has_next:
            next_url = url_for('coffee.by_roaster', page=beans.next_num)
        if beans.has_prev:
            prev_url = url_for('coffee.by_roaster', page=beans.prev_num)

        return render_template('coffee_database.html',
                        title='Coffees by flavor',
                        beans = beans.items,
                        next_page=next_url,
                        prev_page=prev_url)

    else:
        return redirect(url_for('site.home'))

#helper functions
def get_coffee_id(coffee_attributes: dict) -> str:
    ''' Function takes a dictionary of attributes and determines if the record
    already exists, creating a new record if necessary. Returns coffee UUID and 
    bool is_new value.
    coffee id: UUID str
    is_new : True = new entry; False = existing'''
    new_coffee = True

    coffee_list = Coffee.query.filter_by(roaster=coffee_attributes['roaster'], 
                                         bag_name=coffee_attributes['bag_name']).all()
    if coffee_list:
        for coffee_obj in coffee_list:

            print("coffee_obj= ", coffee_obj)
            if coffee_obj.matches(coffee_attributes):
                new_coffee= False
                coffee = coffee_obj
                update_coffee_table(coffee, coffee_attributes)
                coffee_id = coffee.id
                break
    
    if new_coffee == True:
        coffee_id = create_new_coffee(coffee_attributes)
    
    return coffee_id, new_coffee

def create_new_coffee(coffee_attributes: dict) -> str:
    ''' Creates a new coffee entry and returns the UUID for the new entry'''
    coffee = Coffee(roaster=coffee_attributes['roaster'],
                               bag_name=coffee_attributes['bag_name'],
                               origin=coffee_attributes['origin'],
                               producer=coffee_attributes['producer'],
                               variety=coffee_attributes['variety'],
                               process_method=coffee_attributes['process_method'],
                               blend=coffee_attributes['blend'])
    db.session.add(coffee)
    db.session.commit()
    return coffee.id

def coffee_as_dict(coffee):
    ''' Expects an SQLAlchemy or Coffee object, returns a dictionary with relevant fields for comparison 
    excludes UUID because it is not used in context of this function'''
    
    coffee_dict = {
        'roaster': coffee.roaster,
        'bag_name': coffee.bag_name,
        'origin': coffee.origin,
        'producer': coffee.producer,
        'variety': coffee.variety,
        'process_method': coffee.process_method,
        'blend': coffee.blend
    }
    return coffee_dict


def update_coffee_table(existing_coffee: Coffee, update_attributes: dict):
    updated_coffee = {'roaster' : existing_coffee.roaster,
                      'bag_name' : existing_coffee.bag_name,
                      'origin' : existing_coffee.origin,
                      'producer' : existing_coffee.producer,
                      'variety' : existing_coffee.variety,
                      'process_method' : existing_coffee.process_method,
                      'blend' : existing_coffee.blend}
    
    for k,v in updated_coffee.items():
        if v == None:
            updated_coffee[k] = update_attributes[k]
    
    existing_coffee.roaster = updated_coffee['roaster']
    existing_coffee.bag_name = updated_coffee['bag_name']
    existing_coffee.origin = updated_coffee['origin']
    existing_coffee.producer = updated_coffee['producer']
    existing_coffee.variety = updated_coffee['variety']
    existing_coffee.process_method = updated_coffee['process_method']
    existing_coffee.blend = updated_coffee['blend']

    db.session.commit()


def create_flavor_profile(flavor_str: str, coffee_id: str, acidity: str =''):
    ''' Takes in arguments, creates flavor profile for user's portfolio'''
    print('flavor_str: ', flavor_str)
    
    # break string into words
    flavor_list=[]
    delimiters = re.compile('[;,.?!\/|]')
    delimeter_re = delimiters.finditer(flavor_str)

    first=0
    for i in delimeter_re:
        flavor_list.append(flavor_str[first:i.start()].strip(' '))
        first = i.start()+1

    if first < len(flavor_str):
        flavor_list.append(flavor_str[first:].strip(' '))

    print('flavor_list: ', flavor_list)
    for flavor in flavor_list:
        flavor_id = get_flavor_id(flavor)
        flavor_profile = FlavorProfile(coffee_id, flavor_id, acidity)
        db.session.add(flavor_profile)
    db.session.commit()

def get_flavor_id(flavor: str) -> str:
    ''' Checks table Flavor for existing descriptors
        calls add_flavor if no entry matches
        returns flavor descriptor ID
    '''
    existing_flavor = Flavor.query.filter_by(adjective=flavor).first()
    print('existing_flavor: ', existing_flavor)
    print('flavor: ', flavor)
    if existing_flavor == None:
        return add_flavor(flavor)
    
    else:
        return existing_flavor.id

def add_flavor(flavor: str) -> str:
        ''' creates a new entry in table Flavor, returns id'''
        new_flavor = Flavor(flavor)
        db.session.add(new_flavor)
        db.session.commit()
        print(new_flavor.id, new_flavor.adjective)
        return new_flavor.id

