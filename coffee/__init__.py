from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=False, template_folder='./base/templates', static_folder='./base/static')
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.sign_in'

    with app.app_context():
        # Import blueprints
        from .site.routes import site
        from .auth.auth import auth
        from .users.user_routes import profile
        from .coffees.coffee_routes import coffee

        # Register blueprints
        app.register_blueprint(site)
        app.register_blueprint(auth)
        app.register_blueprint(profile)
        app.register_blueprint(coffee)
    
        # create database models
        db.create_all()

        return app