from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms import IntegerField, FloatField, TextAreaField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange
from flask_babel import lazy_gettext as _l

# User Authentication Forms
class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(_l('Confirm Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))

# User Profile Form
class UserProfileForm(FlaskForm):
    age = IntegerField(_l('Age'), validators=[DataRequired(), NumberRange(min=15, max=120)])
    gender = SelectField(_l('Gender'), choices=[
        ('male', _l('Male')), 
        ('female', _l('Female')), 
        ('other', _l('Other'))
    ])
    weight = FloatField(_l('Weight (kg)'), validators=[DataRequired(), NumberRange(min=30, max=300)])
    height = FloatField(_l('Height (cm)'), validators=[DataRequired(), NumberRange(min=100, max=250)])
    activity_level = SelectField(_l('Activity Level'), choices=[
        ('sedentary', _l('Sedentary (little or no exercise)')),
        ('light', _l('Light (exercise 1-3 days/week)')),
        ('moderate', _l('Moderate (exercise 3-5 days/week)')),
        ('active', _l('Active (exercise 6-7 days/week)')),
        ('very active', _l('Very Active (hard exercise & physical job)'))
    ])
    health_goal = SelectField(_l('Health Goal'), choices=[
        ('weight loss', _l('Weight Loss')),
        ('maintenance', _l('Maintenance')),
        ('gain', _l('Weight Gain'))
    ])
    preferred_language = SelectField(_l('Preferred Language'), choices=[
        ('en', _l('English')),
        ('hi', _l('Hindi')),
        ('kn', _l('Kannada')),
        ('ta', _l('Tamil')),
        ('te', _l('Telugu')),
        ('mr', _l('Marathi')),
        ('gu', _l('Gujarati'))
    ])
    submit = SubmitField(_l('Save Profile'))

# Meal Logging Forms
class LogMealForm(FlaskForm):
    meal_id = HiddenField()
    custom_meal_name = StringField(_l('Meal Name'), validators=[Optional(), Length(max=128)])
    custom_meal_calories = FloatField(_l('Calories'), validators=[Optional(), NumberRange(min=0)])
    custom_meal_proteins = FloatField(_l('Proteins (g)'), validators=[Optional(), NumberRange(min=0)])
    custom_meal_carbs = FloatField(_l('Carbohydrates (g)'), validators=[Optional(), NumberRange(min=0)])
    custom_meal_fats = FloatField(_l('Fats (g)'), validators=[Optional(), NumberRange(min=0)])
    portion_size = SelectField(_l('Portion Size'), choices=[
        ('small', _l('Small')),
        ('medium', _l('Medium')),
        ('large', _l('Large'))
    ], default='medium')
    meal_type = SelectField(_l('Meal Type'), choices=[
        ('breakfast', _l('Breakfast')),
        ('lunch', _l('Lunch')),
        ('dinner', _l('Dinner')),
        ('snack', _l('Snack'))
    ])
    notes = TextAreaField(_l('Notes'), validators=[Optional(), Length(max=500)])
    meal_image = FileField(_l('Upload Meal Image'))
    submit = SubmitField(_l('Log Meal'))

class MealSearchForm(FlaskForm):
    search_term = StringField(_l('Search for a meal'), validators=[Optional()])
    submit = SubmitField(_l('Search'))

# Admin Forms
class AdminMealForm(FlaskForm):
    name_en = StringField(_l('Name (English)'), validators=[DataRequired()])
    name_hi = StringField(_l('Name (Hindi)'), validators=[Optional()])
    name_kn = StringField(_l('Name (Kannada)'), validators=[Optional()])
    name_ta = StringField(_l('Name (Tamil)'), validators=[Optional()])
    name_te = StringField(_l('Name (Telugu)'), validators=[Optional()])
    name_mr = StringField(_l('Name (Marathi)'), validators=[Optional()])
    name_gu = StringField(_l('Name (Gujarati)'), validators=[Optional()])
    
    calories = FloatField(_l('Calories (per 100g)'), validators=[DataRequired(), NumberRange(min=0)])
    proteins = FloatField(_l('Proteins (g per 100g)'), validators=[Optional(), NumberRange(min=0)])
    carbs = FloatField(_l('Carbohydrates (g per 100g)'), validators=[Optional(), NumberRange(min=0)])
    fats = FloatField(_l('Fats (g per 100g)'), validators=[Optional(), NumberRange(min=0)])
    fiber = FloatField(_l('Fiber (g per 100g)'), validators=[Optional(), NumberRange(min=0)])
    
    portion_small = FloatField(_l('Small Portion (g)'), validators=[Optional(), NumberRange(min=0)])
    portion_medium = FloatField(_l('Medium Portion (g)'), validators=[Optional(), NumberRange(min=0)])
    portion_large = FloatField(_l('Large Portion (g)'), validators=[Optional(), NumberRange(min=0)])
    
    is_cafeteria_item = BooleanField(_l('Available in Cafeteria'))
    tags = StringField(_l('Tags (comma separated)'), validators=[Optional()])
    image_path = StringField(_l('Image URL'), validators=[Optional()])
    
    submit = SubmitField(_l('Save Meal'))
