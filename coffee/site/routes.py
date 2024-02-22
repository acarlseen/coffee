from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required

from models import User, Coffee, Portfolio

site = Blueprint('site', __name__,
                 template_folder='site_temps',
                 static_url_path='/site',
                 static_folder='static')

@site.route('/')
def home():
    return render_template('index.html',
                           title='')

