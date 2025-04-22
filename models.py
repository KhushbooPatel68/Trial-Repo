from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    locale = db.Column(db.String(10), default='en')  # en, es, hi, kn, ta, te, mr, gu
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    meals = db.relationship('Meal', backref='user', lazy='dynamic')
    achievements = db.relationship('UserAchievement', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    height = db.Column(db.Float)  # in centimeters
    weight = db.Column(db.Float)  # in kilograms
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    activity_level = db.Column(db.String(20))
    target_calories = db.Column(db.Integer)
    target_protein = db.Column(db.Integer)
    target_carbs = db.Column(db.Integer)
    target_fat = db.Column(db.Integer)
    
    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate"""
        if not self.height or not self.weight or not self.age or not self.gender:
            return None
            
        if self.gender.lower() == 'male':
            return 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
        else:
            return 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
    
    def calculate_daily_needs(self):
        """Calculate daily caloric needs based on activity level"""
        bmr = self.calculate_bmr()
        if not bmr:
            return None
            
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }
        
        multiplier = activity_multipliers.get(self.activity_level.lower(), 1.2)
        return bmr * multiplier


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    name_es = db.Column(db.String(128))  # Spanish name
    name_hi = db.Column(db.String(128))  # Hindi name
    name_kn = db.Column(db.String(128))  # Kannada name
    name_ta = db.Column(db.String(128))  # Tamil name
    name_te = db.Column(db.String(128))  # Telugu name
    name_mr = db.Column(db.String(128))  # Marathi name
    name_gu = db.Column(db.String(128))  # Gujarati name
    calories = db.Column(db.Integer)  # per 100g or standard portion
    protein = db.Column(db.Float)  # in grams
    carbs = db.Column(db.Float)  # in grams
    fat = db.Column(db.Float)  # in grams
    fiber = db.Column(db.Float, default=0.0)  # in grams
    category = db.Column(db.String(50))  # e.g., protein, carbs, vegetables
    is_custom = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def get_name(self, locale='en'):
        """Return the name based on locale"""
        if locale == 'en' or not locale:
            return self.name
        locale_attr = f'name_{locale}'
        if hasattr(self, locale_attr) and getattr(self, locale_attr):
            return getattr(self, locale_attr)
        return self.name
        
    def get_nutrition_for_portion(self, portion_size):
        """Calculate nutrition based on portion size"""
        multiplier = {
            'small': 0.75,
            'medium': 1.0,
            'large': 1.5
        }.get(portion_size.lower(), 1.0)
        
        return {
            'calories': int(self.calories * multiplier),
            'protein': round(self.protein * multiplier, 1),
            'carbs': round(self.carbs * multiplier, 1),
            'fat': round(self.fat * multiplier, 1),
            'fiber': round(self.fiber * multiplier, 1)
        }


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    time = db.Column(db.Time, default=datetime.utcnow().time)
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    
    # Relationships
    items = db.relationship('MealItem', backref='meal', lazy='dynamic')
    
    @property
    def total_nutrition(self):
        """Calculate total nutrition for all items in the meal"""
        totals = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
        
        for item in self.items:
            food_nutrition = item.food.get_nutrition_for_portion(item.portion_size)
            totals['calories'] += food_nutrition['calories']
            totals['protein'] += food_nutrition['protein']
            totals['carbs'] += food_nutrition['carbs']
            totals['fat'] += food_nutrition['fat']
            totals['fiber'] += food_nutrition['fiber']
            
        return totals


class MealItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    portion_size = db.Column(db.String(10), default='medium')  # small, medium, large
    
    # Relationships
    food = db.relationship('Food')


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))  # Icon reference
    requirement_type = db.Column(db.String(50))  # e.g., meals_logged, days_streak
    requirement_value = db.Column(db.Integer)  # The value needed to earn this achievement
    
    # Relationship with users who have earned this achievement
    users = db.relationship('UserAchievement', backref='achievement')


class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_date = db.Column(db.DateTime, default=datetime.utcnow)
