from flask import Blueprint, url_for, redirect, request, flash, render_template
from flask_login import login_user, logout_user, current_user

from forms import SignUpForm, LoginForm
from models import User, check_password_hash
from models import db
from .. import login_manager

auth = Blueprint('authorization', __name__,
                 template_folder='auth_templates',
                 static_folder='static',
                 static_url_path='/auth')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('profile.user_profile'))
    
    form = SignUpForm()
    try:
        if request.method == 'POST' and form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            new_user = User(email, password=password)

            db.session.add(new_user)
            db.session.commit()

            flash(f'Profile for {email} created!')
            return redirect(url_for('profile.user_profile', user_id=new_user.id))
    except:
        raise Exception('Something went wrong')
    
    return render_template('sign_up.html',
                           title = 'Sign Up',
                           form = form)

@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('profile.user_profile', user_id=current_user.get_id()))
    
    form = LoginForm()
    try:
        if request.method == 'POST' and form.validate_on_submit():
            email = form.email.data
            password = form.password.data

            existing_user = User.query.filter_by(email=email).first()
            if check_password_hash(existing_user.password, password):
                login_user(existing_user)
                return redirect(url_for('profile.user_profile', user_id=existing_user.id))
            else:
                if existing_user is None:
                    flash('Email is not registered with us')
                flash('Email and password do not match')
    except:
        print(form.errors)
        raise Exception('Form is not valid')
    
    return render_template('/sign_in.html',
                           title='Sign In',
                           form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('site.home'))

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

@login_manager.unauthorized_handler
def unauthorized():
    flash('You must be logged in to view that page.')
    return redirect(url_for('authorization.signin'))