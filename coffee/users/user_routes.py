from flask import Blueprint, url_for, redirect, render_template, request
from flask_login import login_required

from models import User, Portfolio, Coffee
from config import Config


profile = Blueprint('profile', __name__,
                    template_folder='user_templates',
                    static_folder='static',
                    static_url_path='/profile')

@profile.route('/profile/<user_id>', methods=['GET'])
@login_required
def user_profile(user_id):
    user = User.query.filter_by(id=user_id).first()
    return render_template('profile.html',
                           title='User Profile',
                           user_id=user_id,
                           token=user.token)

@profile.route('/portfolio/<user_id>', methods=['GET'])
@login_required
def portfolio(user_id):
 
    page = request.args.get('page', 1, type=int)
    beans = Portfolio.query.filter_by(user=user_id)\
        .join(Coffee, Coffee.id == Portfolio.coffee)\
            .add_entity(Coffee)\
            .order_by(Coffee.roaster)\
            .paginate(page=page,
                      per_page= Config.ITEMS_PER_PAGE,
                      error_out= False)

    next_url = prev_url = None
    
    if beans.has_next:
        next_url = url_for('coffee.all_coffees', page=beans.next_num)
    if beans.has_prev:
        prev_url = url_for('coffee.all_coffees', page=beans.prev_num)
    
    beans2 = [item[1] for item in beans.items]

    return render_template('coffee_database.html',
                           title='User Portfolio',
                           beans = beans2,
                           next_page=next_url,
                           prev_page=prev_url)
