from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, RadioField, TextAreaField
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
    blend = RadioField('Is this a blend?', choices=[('Blend', 'Blend'),('Single Origin', 'Single Origin')])
    acidity = RadioField('Acidity', choices=[('high', 'High'), 
                                             ('medium', 'Medium'), 
                                             ('low', 'Low')])
    flavors = StringField('Tastes like... (separate by commas)', validators=[Length(max=200), Optional()])
    tasting_notes = TextAreaField('Other tasting notes (brew process, etc.)', validators=[Length(min=3, max=200), Optional()])
    '''rating = RadioField('Love it or hate it? How many stars?', choices=[('1', '1'),
                                                                        ('2', '2'),
                                                                        ('3', '3'),
                                                                        ('4', '4'),
                                                                        ('5', '5')])'''
    submit_button = SubmitField('Add beans')
