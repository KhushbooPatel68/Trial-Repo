from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    meal_logs = db.relationship('MealLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    weight = db.Column(db.Float)  # in kg
    height = db.Column(db.Float)  # in cm
    activity_level = db.Column(db.String(20))  # sedentary, light, moderate, active, very active
    health_goal = db.Column(db.String(20))  # weight loss, maintenance, gain
    bmi = db.Column(db.Float)
    daily_calorie_needs = db.Column(db.Float)
    preferred_language = db.Column(db.String(10), default='en')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'

    def calculate_bmi(self):
        if self.weight and self.height:
            # BMI = weight(kg) / (height(m))²
            height_m = self.height / 100  # convert cm to m
            self.bmi = round(self.weight / (height_m * height_m), 1)
            return self.bmi
        return None

    def calculate_daily_calorie_needs(self):
        if self.weight and self.height and self.age and self.gender:
            # Mifflin-St Jeor Equation
            if self.gender.lower() == 'male':
                bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
            else:
                bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

            # Apply activity level multiplier
            activity_multipliers = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'active': 1.725,
                'very active': 1.9
            }
            
            multiplier = activity_multipliers.get(self.activity_level.lower(), 1.2)
            self.daily_calorie_needs = round(bmr * multiplier)
            
            # Adjust based on health goal
            if self.health_goal.lower() == 'weight loss':
                self.daily_calorie_needs = round(self.daily_calorie_needs * 0.8)
            elif self.health_goal.lower() == 'gain':
                self.daily_calorie_needs = round(self.daily_calorie_needs * 1.15)
                
            return self.daily_calorie_needs
        return None

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(128), nullable=False)
    name_hi = db.Column(db.String(128))
    name_kn = db.Column(db.String(128))
    name_ta = db.Column(db.String(128))
    name_te = db.Column(db.String(128))
    name_mr = db.Column(db.String(128))
    name_gu = db.Column(db.String(128))
    image_path = db.Column(db.String(256))
    is_cafeteria_item = db.Column(db.Boolean, default=False)
    
    # Nutritional info per 100g
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fats = db.Column(db.Float)
    fiber = db.Column(db.Float)
    
    # Portion sizes in grams
    portion_small = db.Column(db.Float)
    portion_medium = db.Column(db.Float)
    portion_large = db.Column(db.Float)
    
    tags = db.Column(db.String(256))  # Comma-separated tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who created

    def __repr__(self):
        return f'<Meal {self.name_en}>'
    
    def get_name(self, lang='en'):
        if lang == 'hi' and self.name_hi:
            return self.name_hi
        elif lang == 'kn' and self.name_kn:
            return self.name_kn
        elif lang == 'ta' and self.name_ta:
            return self.name_ta
        elif lang == 'te' and self.name_te:
            return self.name_te
        elif lang == 'mr' and self.name_mr:
            return self.name_mr
        elif lang == 'gu' and self.name_gu:
            return self.name_gu
        return self.name_en
    
    def calculate_nutrition(self, portion_size='medium'):
        if portion_size == 'small' and self.portion_small:
            multiplier = self.portion_small / 100
        elif portion_size == 'large' and self.portion_large:
            multiplier = self.portion_large / 100
        else:  # Default to medium
            multiplier = self.portion_medium / 100 if self.portion_medium else 1
            
        return {
            'calories': round(self.calories * multiplier),
            'proteins': round(self.proteins * multiplier, 1) if self.proteins else None,
            'carbs': round(self.carbs * multiplier, 1) if self.carbs else None,
            'fats': round(self.fats * multiplier, 1) if self.fats else None,
            'fiber': round(self.fiber * multiplier, 1) if self.fiber else None
        }

class MealLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'))
    # If it's a custom meal not in the database
    custom_meal_name = db.Column(db.String(128))
    custom_meal_calories = db.Column(db.Float)
    custom_meal_proteins = db.Column(db.Float)
    custom_meal_carbs = db.Column(db.Float)
    custom_meal_fats = db.Column(db.Float)
    
    portion_size = db.Column(db.String(20), default='medium')  # small, medium, large
    meal_time = db.Column(db.DateTime, default=datetime.utcnow)
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    notes = db.Column(db.Text)
    meal = db.relationship('Meal', backref='logs')

    def __repr__(self):
        meal_name = self.meal.name_en if self.meal else self.custom_meal_name
        return f'<MealLog {meal_name} on {self.meal_time}>'
    
    def get_calories(self):
        if self.meal:
            return self.meal.calculate_nutrition(self.portion_size)['calories']
        return self.custom_meal_calories
    
    def get_macros(self):
        if self.meal:
            return {
                'proteins': self.meal.calculate_nutrition(self.portion_size)['proteins'],
                'carbs': self.meal.calculate_nutrition(self.portion_size)['carbs'],
                'fats': self.meal.calculate_nutrition(self.portion_size)['fats']
            }
        return {
            'proteins': self.custom_meal_proteins,
            'carbs': self.custom_meal_carbs,
            'fats': self.custom_meal_fats
        }
