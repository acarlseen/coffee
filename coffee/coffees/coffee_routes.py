from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required

from models import Coffee, Portfolio
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
    
    try:
        if request.method == 'POST' and form.validate_on_submit():
            attributes = {}
            attributes['roaster'] = form.roaster.data
            attributes['bag_name'] = form.bag_name.data
            attributes['origin'] = form.origin.data
            attributes['producer'] = form.producer.data
            attributes['variety'] = form.variety.data
            attributes['process_method'] = form.process_method.data
            attributes['blend'] = form.blend.data
            tasting_notes = form.tasting_notes.data
            print(attributes)
            new_coffee_id = get_coffee_id(attributes)
            print(new_coffee_id)

            portfolio_addition = Portfolio(user=current_user.get_id(), coffee=new_coffee_id, tasting_notes=tasting_notes)
            print("portfolio.id=", portfolio_addition.id)
            db.session.add(portfolio_addition)
            db.session.commit()

            return redirect(url_for('profile.portfolio', user_id=current_user.get_id()))
    except:
        raise Exception('Something went wrong')
    
    return render_template('add_coffee.html',
                           title = 'Add a bag',
                           form = form)



#helper functions
def get_coffee_id(coffee_attributes: dict) -> str:
    new_coffee = True

    coffee_list = Coffee.query.filter_by(roaster=coffee_attributes['roaster'], 
                                         origin=coffee_attributes['origin']).all()
    print("coffee_list=", coffee_list)
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
        coffee = Coffee(roaster=coffee_attributes['roaster'],
                               bag_name=coffee_attributes['bag_name'],
                               origin=coffee_attributes['origin'],
                               producer=coffee_attributes['producer'],
                               variety=coffee_attributes['variety'],
                               process_method=coffee_attributes['process_method'],
                               blend=coffee_attributes['blend'])
        coffee_id = coffee.id
        db.session.add(coffee)
        db.session.commit()
    
    return coffee_id

def update_coffee_table(existing_coffee: Coffee, update_attributes: dict):
    updated_coffee = { 'roaster' : existing_coffee.roaster,
                      'bag_name' : existing_coffee.bag_name,
                      'origin' : existing_coffee.origin,
                      'producer' : existing_coffee.producer,
                      'variety' : existing_coffee.variety,
                      'process' : existing_coffee.process,
                      'blend' : existing_coffee.blend}
    
    for k,v in updated_coffee.items():
        if v == None:
            updated_coffee[k] = update_attributes[k]
    
    existing_coffee.roaster = updated_coffee['roaster']
    existing_coffee.bag_name = updated_coffee['bag_name']
    existing_coffee.origin = updated_coffee['origin']
    existing_coffee.producer = updated_coffee['producer']
    existing_coffee.variety = updated_coffee['variety']
    existing_coffee.process = updated_coffee['process']
    existing_coffee.blend = updated_coffee['blend']

    db.session.commit()