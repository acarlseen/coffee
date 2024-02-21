from flask import Blueprint, url_for, redirect, render_template
from flask_login import login_required

from models import User, Portfolio, Coffee

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
    portfolio= None
    try:
        portfolio = Portfolio.query.filter_by(user=user_id).all()
    except:
        print(portfolio)

    print('portfolio = ', portfolio)
    coffee_list = [coffee.coffee for coffee in portfolio]
    print('coffee_list = ', coffee_list)
    list_o_beans = Coffee.query.filter(Coffee.id.in_(coffee_list))
    for coffee in list_o_beans:
        print(coffee.roaster, coffee.bag_name)
    return render_template('coffee_database.html',
                           title='User Portfolio',
                           beans=list_o_beans)

