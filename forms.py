from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField, RadioField
from wtforms.validators import Email, Length, Optional, DataRequired, EqualTo


class SignUpForm(FlaskForm):
    email = StringField('Email', validators= [DataRequired(), Email(message='Enter a valid email')])
    password = PasswordField('Password', validators= [DataRequired(), 
                                                      Length(min=8, message='Select a stronger password'), 
                                                      EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm your password', validators=[DataRequired()])
    submit_button = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message='Enter a valid email')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit_button = SubmitField('Log In')


class CoffeeForm(FlaskForm):
    roaster = StringField('Roaster', validators=[Length(max=50, message='50 character max'), DataRequired()])
    bag_name = StringField('Name on bag', validators=[Length(max=50, message='50 character max'), DataRequired()])
    origin = StringField('Origin', validators=[Length(max=50), Optional()])
    producer = StringField('Producer/Farm', validators=[Length(max=50), Optional()])
    variety = StringField('Variety', validators=[Length(max=50), Optional()])
    process_method = StringField('Process Method', validators=[Length(max=50), Optional()])
    blend = RadioField('Is this a blend?', choices=[('blend', 'Blend'),('single origin', 'Single Origin')])
    tasting_notes = StringField('Tasting Notes', validators=[Length(min=3, max=200), Optional()])
    submit_button = SubmitField('Add beans')
