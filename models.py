from datetime import datetime
from flask_login import UserMixin
from flask_marshmallow import Marshmallow
from sqlalchemy import ForeignKey, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from coffee import db

ma = Marshmallow()

class User(UserMixin, db.Model):
    id : Mapped[str] = mapped_column('id', String, primary_key=True)
    first_name : Mapped[str] = mapped_column('first_name', String, nullable=True, default='')
    last_name : Mapped[str] = mapped_column('last_name', String, nullable=True, default='')
    email : Mapped[str] = mapped_column('email', String, nullable=False)
    street1 : Mapped[str] = mapped_column('street', String, nullable=True)
    street2 : Mapped[str] = mapped_column('unit', String, nullable=True)
    city : Mapped[str] = mapped_column('city', String, nullable=True)
    state : Mapped[str] = mapped_column('state', String, nullable=True)
    _zip : Mapped[str] = mapped_column('zip', Integer, nullable=True)
    website : Mapped[str] = mapped_column('website', String, nullable=True)
    password : Mapped[str] = mapped_column('password', String, nullable=False, default='')
    g_auth_verify : Mapped[bool] = mapped_column('g_auth_verify', Boolean, default=False)
    token : Mapped[str] = mapped_column('token', String, unique=True, default='')
    date_joined : Mapped[str] = mapped_column('date_joined', String, nullable=False, default = datetime.now())

    def __init__(self, email, first_name='', last_name='', password=''):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.id = self.set_id()
        self.password = self.set_password(password)
        self.token = self.generate_token()
    
    def set_id(self):
        return str(uuid.uuid4())
    
    def set_password(self, password):
        return generate_password_hash(password)
    
    def generate_token(self, tok_len=24):
        return secrets.token_hex(tok_len)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def __repr__(self): # this will reprint (confirm) the information just entered
        return f'User {self.email} has been added to the database'
    

class UserSchema(ma.Schema):
    class Meta:
        fields = ('email', 'first_name', 'last_name', 'date_joined', 'website')

user_schema = UserSchema()
users_schema = UserSchema(many=True)


#consider making one-to-many for brew methods to hone tasting notes
class Coffee(db.Model):
    id: Mapped[str] = mapped_column('id', String, primary_key=True)
    roaster : Mapped[str] = mapped_column('roaster', String, nullable=False, default='')
    bag_name : Mapped[str] = mapped_column('bag_name', String, nullable=True)
    origin : Mapped[str] = mapped_column('origin', String, nullable=False, default='')
    producer : Mapped[str] = mapped_column('producer', String, nullable=True)
    variety : Mapped[str] = mapped_column('variety', String, nullable=True)
    process_method : Mapped[str] = mapped_column('process_method', String, nullable=True)
    blend : Mapped[str] = mapped_column('blend', String, nullable=False, default=False)

    def __init__(self, roaster, bag_name='', origin='', producer='', variety='', process_method='', blend=''):
        self.id = self.set_id()
        self.roaster = roaster
        self.bag_name = bag_name
        self.origin = origin
        self.producer = producer
        self.variety = variety
        self. process_method = process_method
        self.blend = blend

    def set_id(self):
        return uuid.uuid4()
    
    def matches(self, new_coffee_attributes: dict) -> bool:
        my_attributes = {"roaster" : self.roaster,
                         "bag_name" : self.bag_name,
                         "origin" : self.origin,
                         "producer" : self.producer,
                         "variety" : self.variety,
                         "process_method" : self.process_method,
                         "blend" : self.blend}
        
        same_data = True
        for key,value in my_attributes.items():
            if value.lower() == new_coffee_attributes[key].lower() or new_coffee_attributes[key] == None or value == None:
                continue
            else:
                same_data = False
                break
        return same_data
        

class CoffeeSchema(ma.Schema):
    class Meta:
        fields = ('roaster', 'bag_name', 'origin', 'producer', 'variety', 'process_method', 'blend')

coffee_schema = CoffeeSchema()
coffees_schema = CoffeeSchema(many=True)

class Flavor(db.Model):
    id : Mapped[int] = mapped_column('id', Integer, primary_key=True, autoincrement=True)
    adjective : Mapped[int] = mapped_column('adjective', String, nullable=False)

    def __init__(self, adjective):
        self.adjective = adjective
        self.id


class FlavorProfile(db.Model):
    id: Mapped[int] = mapped_column('id', Integer, primary_key=True, autoincrement=True)
    adjective_id : Mapped[int] = mapped_column('adjective_id', Integer, ForeignKey(Flavor.id), nullable=False)
    coffee_id : Mapped[str] = mapped_column('coffee_id', String, ForeignKey(Coffee.id), nullable=False)
    acidity : Mapped[str] = mapped_column('acidity', String)

    def __init__(self, coffee_id, adjective_id, acidity):
        self.adjective_id = adjective_id
        self.coffee_id = coffee_id
        self.acidity = acidity

class Portfolio(db.Model):
    id : Mapped[str] = mapped_column('id', String, primary_key=True)
    user : Mapped[str] = mapped_column('user', String, ForeignKey(User.id))
    coffee : Mapped[str] = mapped_column('coffee', String, ForeignKey(Coffee.id))
    tasting_notes : Mapped[str] = mapped_column('tasting_notes', String, nullable=True)
    flavors: Mapped[str] = mapped_column('flavors', String, nullable=True)
    rating : Mapped[str] = mapped_column('rating', String, nullable=True)
    timestamp : Mapped[str] = mapped_column('added_on', String, default= datetime.now())


    def __init__(self, user, coffee, tasting_notes='', flavors='', rating=''):
        self.user = user
        self.coffee = coffee
        self.tasting_notes = tasting_notes
        self.flavors = flavors
        self.rating = rating
        self.id = self.set_id()

    def get_flavors(self):
        ''' revisit this, just want to return flavor_id data'''
        return FlavorProfile.query.select(FlavorProfile.adjective_id).filter_by(user_id=self.user, coffee_id=self.coffee).all()

    def set_id(self):
        return uuid.uuid4()

class PortfolioSchema(ma.Schema):
    class Meta:
        fields = ('flavors', 'tasting_notes', 'timestamp')

portfolio_schema = PortfolioSchema()
portfolios_schema = PortfolioSchema(many=True)
